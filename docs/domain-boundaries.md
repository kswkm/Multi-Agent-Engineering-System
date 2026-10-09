# Domain Boundaries

SPEC 5장을 코드 구조와 import 규칙으로 옮긴 문서다. 규칙은 `pyproject.toml`의 `[tool.importlinter]`에 있고, `make importlint`(= `make verify`의 일부)로 검사한다. `tests/test_domain_boundaries.py`는 두 가지를 확인한다.
- 계약이 이 문서·SPEC 표와 일치한다.
- 위반을 실제로 잡아낸다.

## 1. 원칙

1. 각 도메인은 **자신이 소유한 테이블만** 직접 읽고 쓴다(SPEC 5).
2. 다른 도메인의 데이터가 필요하면 그 도메인의 **서비스 인터페이스**(`<domain>/interface.py`)를 거친다. 다른 도메인의 `internal` 패키지(모델, 리포지터리, 서비스 로직)는 import할 수 없다.
3. 도메인 간 직접 의존은 SPEC 5.1 "허용 의존성" 표에 있는 것만 허용한다. 허용 그래프는 순환이 없다.
4. 의존 방향은 **Harness → Target** 단방향이다. Target 서비스(`app`)는 `harness`를 import하지 않는다(SPEC 2).

## 2. Target Service 패키지 구조

```
services/todo-api/app/
├── main.py                 # 앱 조립: 각 도메인 router 등록 (Phase 2)
├── core/                   # config, security, db, logging, errors — 도메인을 import하지 않는다
└── domains/
    └── <domain>/
        ├── __init__.py     # 책임·소유 데이터·허용 의존성 docstring
        ├── interface.py    # 공개 인터페이스: 다른 도메인이 import할 수 있는 유일한 모듈 (Phase 2)
        ├── router.py       # HTTP 엔드포인트 (Phase 2)
        └── internal/       # models, repository, service 로직 — 이 도메인만 import 가능
```

`interface.py`는 ORM 객체가 아니라 **불변 DTO**(dataclass 또는 Pydantic 모델)를 주고받는다. ORM 세션과 모델이 도메인 밖으로 새어 나가면 경계가 무너지기 때문이다.

## 3. 도메인 표 (SPEC 5.1)

| 도메인 | 책임 | 소유 데이터 | 허용 의존성 | 인터페이스로 공개할 것 (Phase 2에서 확정) |
|---|---|---|---|---|
| Auth | 로그인, 토큰 발급·갱신·폐기, 비밀번호 해시 | credentials, refresh_tokens | Users(조회만) | 다른 도메인에 공개할 것 없음(요청 인증은 3.2) |
| Users | 사용자 프로필, 계정 상태 | users | 없음 | 조회 전용: id/이메일로 사용자 조회, id 목록 일괄 조회, 계정 상태 |
| Todos | Todo CRUD, 상태 전이, 페이지네이션 | todos | Users(소유자 확인), Tags(연결) | Todo 존재·소유자 조회 |
| Tags | 태그 생성, Todo-태그 연결 | tags, todo_tags | 없음 | Todo id 목록의 태그 일괄 조회, 연결 생성·해제 |
| Sharing | Todo 공유 권한(read/write) | todo_shares | Todos, Users | 사용자의 Todo 접근 권한 판정 |

**"Users(조회만)"를 지키는 방법**: Users의 `interface.py`에는 조회 함수만 둔다. import-linter는 함수 단위를 구분하지 못하므로, 이 규칙은 코드 리뷰 체크리스트와 Users 인터페이스 단위 테스트(쓰기 함수 부재 확인)로 지킨다.

### 3.1 교차 도메인 데이터와 N+1 (REQ-F-004)

목록 응답에는 태그와 소유자 정보가 들어가지만 tags와 users 테이블은 다른 도메인 소유다. 그래서 **도메인을 넘는 ORM relationship을 만들지 않는다**. 대신 Todos가 한 페이지의 id 목록으로 각 인터페이스를 **일괄 호출**한다.

```
GET /todos?limit=100
  1) todos: 페이지 조회 (keyset 커서)                          → 쿼리 1
  2) tags.interface.tags_for_todos([todo ids])               → 쿼리 1 (todo_tags JOIN tags)
  3) users.interface.get_users([owner ids])                  → 쿼리 1
                                                               = 요청당 3 쿼리, N과 무관
```

이것은 SPEC 11.1의 개선 우선순위 중 "배치 조회"에 해당한다. `selectinload`를 쓰려면 도메인 간 relationship이 필요하다. 그러면 경계 규칙과 충돌하므로 쓰지 않는다. Phase 4에서는 일부러 Todo마다 개별 호출하는 N+1 버전으로 측정을 시작한 뒤, 이 일괄 방식으로 고치고 Before/After를 기록한다.

데이터베이스 수준의 외래 키(`todos.owner_id → users.id` 등)는 무결성을 위해 유지한다. 외래 키는 스키마 제약이지 코드 의존이 아니다.

### 3.2 요청 인증은 core에 둔다

Todos, Tags, Sharing의 모든 보호된 엔드포인트는 "요청자가 누구인가"를 알아야 한다. 하지만 SPEC 5.1은 Todos와 Sharing이 Auth에 의존하는 것을 허용하지 않는다. 그래서 일을 둘로 나눈다.

- **access token 검증**(서명·만료·`kid` 확인 → 사용자 id)은 `app.core.security`에 둔다.
  - SPEC 4가 core의 구성 요소로 `security`를 명시한다.
  - access token은 EdDSA 공개키만으로 검증되므로(SPEC 10) DB나 Auth 도메인 데이터가 필요 없다. core는 도메인을 import하지 않는다는 규칙도 지킬 수 있다.
- **토큰 발급·갱신·폐기와 비밀번호 해시**는 Auth 도메인이 소유한다(credentials, refresh_tokens).
- Q-4 기본안(access는 상태 없이 검증, 폐기는 refresh 계열만)을 전제로 한다. 오너가 access 즉시 폐기를 택하면 core가 폐기 목록을 조회해야 한다. 그 경우 이 절을 다시 설계한다.

### 3.3 공유받은 사용자의 Todo 접근: 의존성 역전

`GET /todos/{id}`처럼 Todos의 엔드포인트도 공유받은 사용자를 허용해야 한다(REQ-F-005). 그런데 공유 권한 데이터(todo_shares)는 Sharing 소유이고, SPEC 5.1은 Sharing → Todos 방향만 허용한다. Todos가 Sharing을 import하면 순환이 생긴다.

그래서 **Todos가 포트를 정의하고 Sharing이 구현한다.**

```
todos/interface.py   : class TodoAccessPolicy(Protocol):
                           def can_read(user_id, todo_id) -> bool
                           def can_write(user_id, todo_id) -> bool
sharing/interface.py : class SharingAccessPolicy(TodoAccessPolicy)  # todo_shares 조회로 구현
app/main.py          : Todos 라우터에 SharingAccessPolicy를 주입 (조립 지점, 도메인 아님)
```

- import 방향은 sharing → todos, main → 둘 다로 유지되어 모든 계약을 지킨다.
- Todos는 소유자 판정만 직접 하고, 공유 판정은 주입된 정책에 맡긴다.
- 정책이 판정하지 못하면 거부(404, REQ-F-005.3)로 처리한다(fail closed).
- 목록(REQ-F-004)에 공유 Todo를 넣을지는 Q-2다. 넣는다면 정책이 "사용자가 공유받은 todo id 목록"도 제공해야 하고, 쿼리 예산(≤ 3)을 다시 계산해야 한다.

## 4. Harness 패키지와 SPEC 5.2

| SPEC 5.2 도메인 | 패키지 | 입력 → 출력 | 권한 | 강제 방법 |
|---|---|---|---|---|
| Agent | `harness.agents` (+ `harness.prompts`, `harness.llm`) | AgentInput → AgentOutput(스키마 검증) | Tool Gateway를 통해서만 행동 | Phase 6: Tool Gateway 권한 테스트(SPEC-13-1) |
| Tool | `harness.tools` | ToolCall → ToolResult | `permissions.yaml` 범위 | Phase 6 |
| Validation | `harness.checkers` + Validation(결정론적 코드) | CheckerResult[] → Verdict | Read + Execute(검사 도구) | import 계약: `checkers`·`evidence`는 `llm`·`agents`를 import하지 않는다 |
| Evidence | `harness.evidence` | Evidence → `reports/` | `reports/` 쓰기만 | 같은 import 계약 + Phase 6 쓰기 경로 테스트 |

## 5. import-linter 계약 목록

| 계약 | 종류 | 의미 |
|---|---|---|
| Deterministic judgement layers do not depend on LLM code | forbidden | `harness.checkers`, `harness.evidence` ↛ `harness.llm`, `harness.agents` |
| Target service never imports the harness | forbidden | `app` ↛ `harness` |
| Core infrastructure does not depend on business domains | forbidden | `app.core` ↛ `app.domains` |
| users / tags depends on no other domain | forbidden (직접 import) | SPEC 5.1 "없음" |
| auth may depend only on users | forbidden (직접 import) | SPEC 5.1 |
| todos may depend only on users and tags | forbidden (직접 import) | SPEC 5.1 |
| sharing may depend only on todos and users | forbidden (직접 import) | SPEC 5.1 |
| `<domain>` internals are private to `<domain>` (×5) | protected | `app.domains.<d>.internal`은 `app.domains.<d>` 안에서만 import |

도메인 쌍 계약은 `allow_indirect_imports = true`로 **직접 import만** 본다. 예를 들어 sharing → todos → tags처럼 허용된 의존을 거쳐 생기는 간접 경로는 SPEC 5.1 위반이 아니기 때문이다. 내부 모듈 직접 접근은 protected 계약이 막는다.

## 6. 계약이 실제로 동작한다는 증거

- 실제 저장소: `make importlint` → 13 kept, 0 broken.
- 합성 패키지 트리(`tests/test_domain_boundaries.py`):
  - 위반 10종을 각각 주입하면 의도한 계약 **하나만** BROKEN 된다.
  - 허용된 의존(간접 포함)만 넣으면 모두 KEPT.
- 계약이 없는 모듈을 가리키면 import-linter는 경고 없이 KEPT를 낸다. 그래서 계약에 나오는 모든 모듈이 실제로 존재하는지도 테스트한다.
- 계약을 느슨하게 바꾸는 변이(todos → sharing 허용)를 넣으면 테스트 2개가 실패하는 것을 확인했다(progress.md Phase 1 Evidence).

## 7. 지금 강제하지 못하는 것

| 규칙 | 이유 | 대신 |
|---|---|---|
| "다른 도메인의 테이블을 직접 읽거나 쓰지 않는다"를 SQL 수준에서 강제 | ORM 모델이 `internal`에 있으면 import 계약으로 대부분 막히지만, raw SQL·문자열 테이블 이름은 import로 보이지 않는다 | raw SQL 금지 Semgrep 규칙(SPEC 9 CWE-89, Phase 3) |
| Users 인터페이스의 "조회만" | import-linter는 함수 단위를 모른다 | 리뷰 체크리스트 + 인터페이스 단위 테스트(Phase 2) |
| `router`는 `app.main`만 import | router 모듈이 Phase 2에 생긴다 | Phase 2에서 protected 계약 추가(backlog) |
