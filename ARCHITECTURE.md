# Architecture

이 문서는 시스템의 구조와 핵심 설계 결정을 요약한다.
- 요구사항의 기준: [docs/SPEC.md](docs/SPEC.md)
- 요구사항별 상태: [docs/requirements.md](docs/requirements.md)
- 도메인 규칙의 상세: [docs/domain-boundaries.md](docs/domain-boundaries.md)

> **현재 상태 (Phase 1)**: 저장소 골격, 툴체인, 로컬 의존성(postgres·redis·toxiproxy), 도메인 경계 규칙만 존재한다. 아래에서 "Phase N"이 붙은 구성 요소는 아직 구현되지 않았다.

## 1. 큰 그림

시스템은 **Harness**(검증하는 쪽)와 **Target Service**(검증받는 쪽) 두 부분이다. 같은 저장소에 두지만 의존 방향은 Harness → Target 하나뿐이다. Target 코드는 Harness를 import하지 않는다. 이것은 import-linter 계약으로 강제한다.

```
                         USER (Requirement / Issue)
                                    │
┌───────────────────────────── HARNESS ──────────────────────────────┐
│  Requirement ─▶ Context Builder ─▶ Architecture ─▶ Implementation  │
│                                                       │ feature branch
│  ┌──────── Verification (parallel, independent) ──────▼───────┐    │
│  │ Code Review │ Security │ Perf/DB │ Reliability │ Test      │    │
│  └─────────────────────────────┬──────────────────────────────┘    │
│        Validation (deterministic) ──FAIL──▶ Self-Healing (≤3)      │
│                 │ PASS                                             │
│        Verification Report + Evidence (reports/<run_id>/)          │
└──────────────────────────────────┬─────────────────────────────────┘
                                   │ execute · measure · attack (HTTP, 프로세스, 컨테이너)
┌────────────────────────── TARGET SERVICE ──────────────────────────┐
│  todo-api (FastAPI) ──▶ PostgreSQL 16      Redis 7 (rate limit)    │
│  /healthz /readyz /metrics        Toxiproxy (장애 주입 경로)        │
└────────────────────────────────────────────────────────────────────┘
```

**핵심 원칙: LLM은 제안하고 도구가 판정한다(SPEC 2.1).**
- 최종 판정(Verdict)은 결정론적 Checker의 실행 결과만으로 만든다.
- LLM 리뷰는 추가 Finding의 출처일 뿐이다.
- 코드 구조로도 강제한다: `harness.checkers`와 `harness.evidence`는 `harness.llm`·`harness.agents`를 import할 수 없다.

## 2. Target Service

### 2.1 구성

| 구성 | 기술 | 상태 |
|---|---|---|
| API | FastAPI, Pydantic v2 | Phase 2 |
| DB | PostgreSQL 16, SQLAlchemy 2.0 async, Alembic | 컨테이너 동작 확인(Phase 0), 스키마는 Phase 2 |
| Rate limit | Redis 7, 장애 시 프로세스 로컬 토큰 버킷 폴백 | 컨테이너 동작 확인(Phase 0), 로직은 Phase 2·5 |
| 장애 주입 | Toxiproxy (DB·Redis·LLM 경로) | 컨테이너 동작 확인(Phase 0), 프록시 정의는 Phase 5 |
| 관측성 | structlog JSON, Prometheus, OpenTelemetry | Phase 2–5 |

### 2.2 도메인과 의존 방향

```
             ┌──────────┐
             │  users   │◀─────────────┬──────────────┐
             └──────────┘              │              │
                  ▲ (조회만)            │              │
             ┌──────────┐        ┌──────────┐   ┌──────────┐
             │   auth   │        │  todos   │◀──│ sharing  │
             └──────────┘        └──────────┘   └──────────┘
                                       │
                                       ▼
                                 ┌──────────┐
                                 │   tags   │
                                 └──────────┘
   모든 도메인 ──▶ app.core (config · security · db · logging · errors)
   app.core ──X──▶ 도메인          app ──X──▶ harness
```

- 다른 도메인에는 `<domain>/interface.py`로만 접근한다. `internal/`은 그 도메인 전용이다.
- 이 규칙들은 import-linter 13개 계약으로 강제한다. 위반을 실제로 잡는지는 합성 트리 테스트로 확인한다.

### 2.3 경계 때문에 정해진 설계

| 문제 | 결정 | 근거 |
|---|---|---|
| 모든 보호 라우트에 인증이 필요한데, Todos와 Sharing은 Auth에 의존할 수 없다 | access token **검증**은 `app.core.security`(공개키, 상태 없음). 발급·갱신·폐기는 Auth | domain-boundaries 3.2, ADR-0003 |
| 공유받은 사용자의 Todo 접근을 Todos가 판단해야 하는데, Sharing 데이터를 import할 수 없다 | Todos가 `TodoAccessPolicy` 포트를 정의하고 Sharing이 구현한다. `app.main`이 주입한다 | domain-boundaries 3.3 |
| 목록에 태그·소유자가 필요한데 다른 도메인 테이블이다 | 도메인 간 ORM relationship 금지. 페이지 id로 각 인터페이스를 **일괄 호출**하므로 요청당 3 쿼리 | domain-boundaries 3.1, REQ-F-004.4 |
| Redis 장애 중에도 멱등성이 필요하다 | (기본안) 멱등성 키는 PostgreSQL에, Redis는 rate limit에만 쓴다 | requirements.md Q-1 (오너 확인 대기) |

### 2.4 장애 격리 (SPEC 12, Phase 5 구현)

| 의존성 | 정책 | 장애 시 기대 동작 |
|---|---|---|
| PostgreSQL | 쿼리 타임아웃 2s, 풀 대기 타임아웃 | `/readyz` 503. 풀 고갈 시 503 + `Retry-After`. 쓰기 실패는 재시도하지 않음 |
| Redis | 타임아웃 100ms | rate limit만 로컬 토큰 버킷으로 폴백, CRUD 정상 |
| 비밀번호 해시 | 동시 2개(semaphore) | 초과 대기 시 503. 해시 메모리가 512MB 컨테이너를 넘지 않게 함(ADR-0003) |
| 프로세스 종료 | SIGTERM 후 진행 중 요청 완료(≤ 20s) | 롤링 재시작 중 실패 요청 0 |

## 3. Harness

| 구성 | 패키지 | 설계 | 상태 |
|---|---|---|---|
| Orchestrator | `harness.orchestrator` | 표로 정의된 asyncio 상태 머신. 13개 상태, 전이 표 전수 테스트, 예산, run.jsonl 이력 | ADR-0002, Phase 6 |
| Agents | `harness.agents`, `harness.prompts` | 역할별 입력·출력 스키마. 검증 에이전트는 diff와 실행 결과만 받는다 | Phase 7 |
| LLM | `harness.llm` | `LLMProvider` 인터페이스, Anthropic + Mock 구현. 타임아웃 60s, 429/5xx 재시도 3회, 서킷 브레이커 | Phase 6 |
| Tool Gateway | `harness.tools` | 모든 도구 호출의 관문: 권한(`permissions.yaml`), 경로 샌드박스, `shell=False` + allowlist, 감사 로그 | Phase 6 |
| Checkers | `harness.checkers` | pytest, semgrep, k6, memray, 쿼리 카운트 등 실제 도구 실행·파싱 | Phase 6 |
| Validation | 결정론적 코드 | CheckResult[] → Verdict. SPEC 7 불변식 강제 | Phase 6 |
| Evidence | `harness.evidence` | `reports/<run_id>/`에 저장, Matrix·리포트 렌더링 | Phase 6 |
| Self-Healing | `harness.agents` | 최대 3회, 같은 FixPlan 반복 시 Human, Forbidden-Action Guard | Phase 7 |

## 4. 검증 체계 (지금 동작하는 것)

| 명령 | 내용 | 실행 위치 |
|---|---|---|
| `make verify` | ruff, mypy --strict, import-linter(13 계약), pytest + coverage ≥ 85% | 로컬, CI `verify` job |
| `make security` | semgrep(p/python), bandit, pip-audit(uv.lock), gitleaks | 로컬, CI `security` job |
| pre-commit | ruff, gitleaks(staged), mypy, 기본 hook | 커밋 시 |
| `main` 보호 | 필수 체크 verify·security, 승인 1, CODEOWNERS, squash only | GitHub |

## 5. 결정 기록 (ADR)

| ADR | 제목 |
|---|---|
| [0001](docs/adr/0001-tech-stack.md) | 기술 스택과 로컬 툴체인 |
| [0002](docs/adr/0002-orchestrator.md) | 오케스트레이터: 직접 구현한 asyncio 명시적 상태 머신 |
| [0003](docs/adr/0003-crypto-policy.md) | 암호 정책: 알고리즘, 파라미터, 키 저장과 교체 |
