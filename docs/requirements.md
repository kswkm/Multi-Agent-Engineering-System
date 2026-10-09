# Requirements & Traceability

이 문서는 SPEC(`docs/SPEC.md`)의 요구사항을 가장 작은 검증 단위로 나눈 **추적표**다(WORKING-GUIDELINES 03, SPEC 8). 작업 중 외부 기억으로 쓰며, 구현·검증이 진행될 때마다 갱신한다.

## 읽는 법과 규칙

- **ID**
  - `REQ-F/N/H-NNN`: SPEC 8장의 요구사항 ID 그대로.
  - `REQ-…-NNN.k`: 그 요구사항을 쪼갠 세부 수용 기준.
  - `SPEC-<장>-<n>`: SPEC 8장 밖(5·6·9~19장)에 있는 검증 대상 규칙. 새 요구사항이 아니라 SPEC 문장을 추적 가능하게 만든 것이다.
- **해결할 문제**: 각 요구사항이 막으려는 문제를 한 문장으로 쓰고, 근거가 된 SPEC 절을 괄호로 단다. SPEC에서 근거를 찾을 수 없는 것은 쓰지 않고 [열린 질문](#열린-질문)에 올린다.
- **상태**: `미구현` / `부분 구현` / `구현됨` / `검증됨`. `검증됨`은 증거 칸에 실행 결과가 있을 때만 쓴다.
- **테스트 방법**: 어떤 종류의 테스트로 증명하는지. **검증 방법**: 그 테스트를 어떤 환경·도구로 돌려 무엇을 증거로 남기는지.
- **테스트 연결**: 테스트에 `@pytest.mark.req("REQ-F-003")`를 붙인다. `tests/test_requirements_traceability.py`가 다음을 검사한다.
  - SPEC 8장의 모든 REQ ID가 이 표에 있다.
  - 모든 행에 필수 칸이 채워져 있다.
  - `검증됨` 행에는 증거가 있다.
  - 테스트 마커가 이 표에 있는 ID만 쓴다.
- **엔드포인트 경로**: SPEC이 정한 것(`/todos`, `/healthz`, `/readyz`, `/metrics`)만 쓴다. 나머지 경로는 Phase 2 설계에서 정한다.

## 1. 기능 요구사항 (Target Service, SPEC 8.1)

| ID | 요구사항 | 해결할 문제 | 완료 조건 | 테스트 방법 | 검증 방법 | Phase | 상태 | 구현 위치 | 증거 |
|---|---|---|---|---|---|---|---|---|---|
| REQ-F-001 | 이메일·비밀번호 가입과 로그인 | 하네스가 공격·검증할 실제 인증 경로가 있어야 한다(SPEC 2.1 Target Service) | 하위 .1~.4 전부 | Integration | 실제 PostgreSQL(Testcontainers)에서 pytest | 2 | 미구현 | - | - |
| REQ-F-001.1 | 가입 성공 | 계정을 만들 수 있어야 한다 | 201, users·credentials 행 생성, 비밀번호는 Argon2id 해시(`$argon2id$`)로만 저장 | Integration | 응답 코드 + DB 행 조회 | 2 | 미구현 | - | - |
| REQ-F-001.2 | 중복 가입 거부 | 같은 이메일로 계정이 두 개 생기면 소유권이 모호해진다(SPEC 8.1, 9 CWE-362) | 같은 이메일 재가입 409. 동시 가입 N건 중 201은 정확히 1건, DB unique 제약이 최종 방어 | Integration, Concurrency | 동시 요청 테스트 + 제약 위반 확인 | 2 | 미구현 | - | - |
| REQ-F-001.3 | 로그인 토큰 발급 | 인증된 사용자만 API를 쓰게 한다 | 올바른 자격증명이면 200 + access(JWT EdDSA, 15분, `kid`) + refresh(불투명 256비트) | Integration | 토큰 디코딩·헤더 검사 | 2 | 미구현 | - | - |
| REQ-F-001.4 | 잘못된 자격증명 | 토큰이 잘못 발급되면 안 된다 | 틀린 비밀번호·없는 이메일·빈 값이면 401(또는 입력 오류 4xx)이고 토큰 없음 | Negative | pytest | 2 | 미구현 | - | - |
| REQ-F-002 | refresh 회전과 재사용 탐지 | 탈취된 refresh 토큰을 쓰면 그 계열 전체를 끊어야 한다(SPEC 10 Refresh Token) | 하위 .1~.4 전부 | Integration, Security | 실제 PostgreSQL에서 pytest | 2 | 미구현 | - | - |
| REQ-F-002.1 | 정상 갱신 | 만료된 access를 재로그인 없이 바꾼다 | 유효 refresh → 새 access + 새 refresh, 사용한 refresh는 사용됨으로 기록. DB에는 SHA-256 해시만 저장 | Integration | 응답 + DB 행(원문 토큰 없음) | 2 | 미구현 | - | - |
| REQ-F-002.2 | 재사용 거부 | 이미 쓴 토큰의 재사용은 탈취 신호다 | 사용된 refresh 재사용 → 401 | Security | pytest | 2 | 미구현 | - | - |
| REQ-F-002.3 | 계열 전체 폐기 | 공격자와 정상 사용자 중 누가 최신 토큰을 가졌는지 알 수 없다 | 재사용 탐지 후 같은 계열의 모든 refresh(최신 회전분 포함) → 401. access 포함 여부는 Q-4 | Security | pytest | 2 | 미구현 | - | - |
| REQ-F-002.4 | 변조·만료 토큰 | 위조 토큰으로 갱신하면 안 된다 | 임의 문자열·만료·다른 사용자 계열 refresh → 401 | Security, Negative | pytest | 2–3 | 미구현 | - | - |
| REQ-F-003 | Todo CRUD | 하네스가 검증할 실제 쓰기·읽기 경로가 필요하다(SPEC 2.1) | 하위 .1~.6 전부 | Integration, Contract | 실제 PostgreSQL + OpenAPI | 2 | 미구현 | - | - |
| REQ-F-003.1 | 생성 | Todo를 만들 수 있어야 한다 | POST `/todos` 201, 행 생성, 소유자 = 요청자 | Integration | 응답 + DB | 2 | 미구현 | - | - |
| REQ-F-003.2 | 단건 조회 | 만든 Todo를 읽을 수 있어야 한다 | GET 200, 본문이 DB와 일치 | Integration | pytest | 2 | 미구현 | - | - |
| REQ-F-003.3 | 수정 | Todo를 바꿀 수 있어야 한다 | PATCH 200, DB 반영 | Integration | 응답 + DB | 2 | 미구현 | - | - |
| REQ-F-003.4 | 삭제 | Todo를 지울 수 있어야 한다 | DELETE 204, 이후 GET 404, DB에서 사라짐 | Integration | 응답 + DB | 2 | 미구현 | - | - |
| REQ-F-003.5 | 계약 | 응답이 문서와 다르면 클라이언트가 깨진다(SPEC 5.3 API Contract) | 모든 응답이 OpenAPI 스키마와 일치 | Contract | Schemathesis + OpenAPI 스냅샷 | 2–3 | 미구현 | - | - |
| REQ-F-003.6 | 입력 오류 | 잘못된 입력이 저장되거나 500이 되면 안 된다(SPEC 9 CWE-20) | 빈 값·null·타입 오류·길이 초과·malformed JSON → 4xx, RFC 9457 Problem Details, 스택트레이스 없음 | Negative, Property | pytest + Hypothesis(SPEC 18.2 체크리스트) | 2–3 | 미구현 | - | - |
| REQ-F-004 | 커서 페이지네이션 목록 | 목록 조회가 데이터 수에 비례해 느려지면 안 된다(SPEC 11.1 N+1, 19.3 예) | 하위 .1~.4 전부 | Query count, Property | 쿼리 카운터 픽스처 | 2–4 | 미구현 | - | - |
| REQ-F-004.1 | 커서 이동 | 큰 목록을 끊어서 받는다 | next cursor로 끝까지 순회하면 전체 집합과 같고 중복·누락 없음 | Property | Hypothesis(삽입 순서·개수 무작위) | 2 | 미구현 | - | - |
| REQ-F-004.2 | limit 상한 | 한 요청이 무제한 데이터를 읽으면 자원이 고갈된다(SPEC 9 CWE-770) | limit 1~100 허용, 0·-1·101·비정수 → 4xx | Negative | 경계값 테스트 | 2 | 미구현 | - | - |
| REQ-F-004.3 | 태그·소유자 포함 | 목록 화면이 항목마다 추가 요청을 하게 하면 안 된다 | 각 항목에 태그 목록과 소유자 정보 포함 | Integration | 응답 스키마 검사 | 2 | 미구현 | - | - |
| REQ-F-004.4 | 쿼리 수 고정 | N+1은 데이터가 늘면 장애가 된다 | 요청당 SQL ≤ 3, N=10/100/1000(태그 3개씩)에서 동일 | Query count | `before_cursor_execute` 카운터(SPEC 11.1) | 2, 4 | 미구현 | - | - |
| REQ-F-005 | read/write 공유 | 공유 기능은 IDOR(타인 리소스 접근)의 대표 경로다(SPEC 9 CWE-639) | 하위 .1~.4 전부 | Authorization | 다중 사용자 통합 테스트 | 2 | 미구현 | - | - |
| REQ-F-005.1 | read 공유 | 공유받은 사람이 읽을 수 있어야 한다 | read 공유 대상 GET 200 | Authorization | pytest | 2 | 미구현 | - | - |
| REQ-F-005.2 | write 공유 | 공유받은 사람이 수정할 수 있어야 한다 | write 공유 대상 PATCH 200. read 공유 대상의 쓰기 시도 응답은 Q-3 | Authorization | pytest | 2 | 미구현 | - | - |
| REQ-F-005.3 | 존재 은닉 | 권한 없는 사용자가 Todo ID의 존재를 알아내면 안 된다 | 권한 없는 사용자의 모든 Todo 엔드포인트 접근 → 404, 없는 ID와 응답이 구별되지 않음 | Authorization, Security | 응답 본문·헤더 비교 | 2 | 미구현 | - | - |
| REQ-F-005.4 | IDOR 전수 검사 | 엔드포인트 하나만 빠져도 우회된다(SPEC 9 "전 엔드포인트 자동 생성") | 라우트 목록에서 타 사용자 접근 테스트를 자동 생성해 모든 Todo 관련 엔드포인트 통과 | Security | 라우트 순회 파라미터화 테스트 | 2 | 미구현 | - | - |
| REQ-F-006 | Idempotency-Key | 재시도·중복 클릭으로 같은 리소스가 두 번 생기면 안 된다(SPEC 9 CWE-362) | 하위 .1~.4 전부. 저장소는 Q-1 | Concurrency | 동시 요청 테스트 | 2 | 미구현 | - | - |
| REQ-F-006.1 | 같은 키 재요청 | 클라이언트 재시도가 안전해야 한다 | 같은 키·같은 본문 재요청 → 첫 응답과 같은 상태 코드·본문, 리소스 1개 | Integration | 응답 비교 + DB 행 수 | 2 | 미구현 | - | - |
| REQ-F-006.2 | 동시 같은 키 | 경쟁 상태로 중복 생성되면 안 된다 | 같은 키 동시 N건 → 리소스 1개. 나머지 응답은 Q-5 | Concurrency | asyncio 동시 요청, 반복 실행 | 2 | 미구현 | - | - |
| REQ-F-006.3 | 키 없는 요청 | 헤더는 선택 사항이다("지원한다") | 키 없는 POST는 정상 처리 | Integration | pytest | 2 | 미구현 | - | - |
| REQ-F-006.4 | 같은 키 다른 본문 | 키 재사용으로 다른 요청이 옛 응답을 받으면 안 된다 | 응답 코드는 Q-5. 새 리소스를 만들지 않음 | Negative | pytest | 2 | 미구현 | - | - |

## 2. 비기능 요구사항 (SPEC 8.2)

측정 환경: api 컨테이너 2 vCPU / 512MB 제한(SPEC 8.2), 로컬 Docker Compose. 로컬 수치를 운영 성능으로 주장하지 않는다(SPEC 11.6).

| ID | 요구사항 | 해결할 문제 | 완료 조건 | 테스트 방법 | 검증 방법 | Phase | 상태 | 구현 위치 | 증거 |
|---|---|---|---|---|---|---|---|---|---|
| REQ-N-001 | 지연 시간 | 무중단 운영에서 느린 응답은 장애다(SPEC 1.1) | 200 RPS 5분(읽기 70/쓰기 30)에서 p95 < 200ms, p99 < 500ms | Load | k6 load, thresholds, JSON → `reports/<run_id>/load/` | 4 | 미구현 | - | - |
| REQ-N-002 | 오류율 | 부하에서 오류가 나면 사용자 요청이 실패한다 | 같은 부하에서 5xx 비율 < 0.1% | Load | k6 threshold(http 5xx 비율) | 4 | 미구현 | - | - |
| REQ-N-003 | 한계점 식별 | 한계를 모르면 용량 계획을 할 수 없다(SPEC 11.6) | stress(50 RPS씩 증가)에서 p95 > 1s가 되는 RPS와 병목 원인을 README에 기록. PASS/FAIL 판정 없이 측정 | Stress | k6 stress + CPU·DB 커넥션 관찰 | 4 | 미구현 | - | - |
| REQ-N-004 | 메모리 안정성 | 메모리 누수는 시간이 지나 OOM으로 터진다(SPEC 11.5) | 100 RPS 30분 soak, 워밍업(5분) 이후 RSS 증가 < 10%, OOM 0회. 10초 간격 RSS 선형 회귀 기울기가 양수로 유지되면 누수 의심 | Soak | k6 soak + `docker stats` + memray | 4 | 미구현 | - | - |
| REQ-N-005 | DB 효율 | 인덱스 없는 쿼리와 풀 고갈은 규모가 커지면 장애가 된다(SPEC 11.2) | 하위 .1~.2 | DB | EXPLAIN, chaos | 4–5 | 미구현 | - | - |
| REQ-N-005.1 | Seq Scan 없음 | 큰 테이블 전체 스캔은 지연을 키운다 | 사용자 1만·Todo 10만 행에서 주요 조회 쿼리 `EXPLAIN (ANALYZE, BUFFERS)`에 큰 테이블 Seq Scan 없음. 인덱스 추가 전후 기록 | DB | 시드 스크립트 + EXPLAIN 결과 저장 | 4 | 미구현 | - | - |
| REQ-N-005.2 | 풀 고갈 시 503 | 풀이 고갈되면 요청이 무한 대기하면 안 된다 | 풀 크기를 줄여 고갈을 재현하면 대기 타임아웃 후 503 + `Retry-After` | Chaos | 풀 축소 설정 + 동시 요청 | 4–5 | 미구현 | - | - |
| REQ-N-006 | Redis 장애 격리 | 부가 기능(rate limit) 장애가 핵심 CRUD를 멈추면 안 된다(SPEC 12) | Redis 중단·지연 중 CRUD 성공률 100%, 5xx 0, rate limit은 프로세스 로컬 토큰 버킷으로 폴백 | Chaos | Toxiproxy + `make chaos SCENARIO=redis_down` | 5 | 미구현 | - | - |
| REQ-N-007 | 무중단 | 배포·재시작 중 요청 실패는 장애다(SPEC 12.1) | 하위 .1~.2 | Chaos | restart under load | 5 | 미구현 | - | - |
| REQ-N-007.1 | 정상 종료 | 종료 신호에 진행 중 요청이 끊기면 안 된다 | SIGTERM 시 진행 중 요청 완료 후 종료, 최대 20s | Chaos | 긴 요청 중 SIGTERM, 응답·종료 시간 측정 | 5 | 미구현 | - | - |
| REQ-N-007.2 | 롤링 재시작 | 인스턴스 교체 중에도 서비스가 계속되어야 한다 | load 부하 중 api 2개 인스턴스 순차 재시작 → 실패 요청 0 | Chaos | k6 + 재시작 스크립트 | 5 | 미구현 | - | - |
| REQ-N-008 | 보안 | 배포 후 책임질 근거가 있어야 한다(SPEC 1.1, 9) | 하위 .1~.3 | Security | 9장 | 3 | 미구현 | - | - |
| REQ-N-008.1 | 스캔 결과 | 알려진 취약점을 안고 배포하면 안 된다 | semgrep·bandit·pip-audit·gitleaks·trivy CRITICAL/HIGH 0 | Security | `make security` + CI | 0, 3 | 부분 구현 | Makefile `security`, `.github/workflows/ci.yml` | Phase 0: semgrep 0 findings, bandit 0, pip-audit 0, gitleaks no leaks (CI run 37932537279). trivy 미구성 |
| REQ-N-008.2 | CWE 매트릭스 | 검사하지 않은 항목을 안전하다고 할 수 없다(SPEC R2) | `docs/cwe-matrix.md` 전 항목이 적용·검증됨 / 해당 없음(사유) / 미검증(사유) 중 하나 | Review | 매트릭스 + 각 항목 Evidence 경로 | 3 | 미구현 | - | - |
| REQ-N-008.3 | 인증 누락 탐지 | 인증 없는 엔드포인트 하나가 전체를 뚫는다(SPEC 9 CWE-306) | 라우트 목록 순회 시 공개 허용 목록(A-3) 밖의 모든 라우트에 인증 의존성 존재 | Security | 라우트 순회 테스트 | 2–3 | 미구현 | - | - |

## 3. 하네스 요구사항 (SPEC 8.3)

| ID | 요구사항 | 해결할 문제 | 완료 조건 | 테스트 방법 | 검증 방법 | Phase | 상태 | 구현 위치 | 증거 |
|---|---|---|---|---|---|---|---|---|---|
| REQ-H-001 | Issue 하나로 전체 실행 | 검증이 사람 손에 의존하면 재현되지 않는다(SPEC 1.2 G1) | `harness run --issue docs/issues/xxx.md`가 `reports/<run_id>/`에 Verdict(JSON)와 리포트를 생성 | E2E | MockLLM으로 CLI 실행 후 산출물 검사 | 6 | 미구현 | - | - |
| REQ-H-002 | 모든 PASS에 Evidence | 근거 없는 PASS는 자기보고다(SPEC R1, 7) | 7장 불변식 4개를 validator로 강제, 위반 시 파이프라인 ERROR | Unit, Property | 스키마 단위 테스트 + Hypothesis 무작위 입력 | 6 | 미구현 | - | - |
| REQ-H-003 | LLM 장애 격리 | LLM 하나의 장애가 결정론적 검증까지 멈추면 안 된다(SPEC 12 LLM API) | 단일 에이전트 실패 시 재시도(429/5xx만, 3회, 지수 백오프+지터) 후 그 항목만 ERROR, 나머지 검증 계속. 서킷 열림 시 즉시 실패 | Unit, Integration | MockLLM 장애 주입 + Toxiproxy(LLM 경로) | 6 | 미구현 | - | - |
| REQ-H-004 | Self-Healing 제한과 금지 행위 | 자가 수리가 테스트를 약화해 PASS를 만들 수 있다(SPEC 14) | 하위 .1~.3 | Unit, E2E | 가짜 diff 코퍼스 + 버그를 심은 Issue | 7 | 미구현 | - | - |
| REQ-H-004.1 | 최대 3회 | 수리가 무한히 반복되면 비용이 폭주한다 | attempt > 3이면 진단 리포트와 함께 Human 이관 | Unit | 상태 머신 테스트 | 7 | 미구현 | - | - |
| REQ-H-004.2 | 금지 행위 차단 | 테스트 삭제·완화로 만든 PASS는 거짓이다 | SPEC 14.1의 6개 범주 각각을 담은 가짜 diff가 모두 차단됨 | Unit | Forbidden-Action Guard 테스트 | 7 | 미구현 | - | - |
| REQ-H-004.3 | 동일 FixPlan 반복 | 같은 수리를 반복하는 것은 무한 루프다(SPEC 13.3) | 같은 FixPlan이 다시 나오면 즉시 Human 이관 | Unit | 상태 머신 테스트 | 7 | 미구현 | - | - |
| REQ-H-005 | 결정론적 재현 | 같은 입력에 판정이 달라지면 증거가 되지 못한다(SPEC 13.2) | MockLLM + 같은 seed로 두 번 실행한 Verdict가 run_id·시각 필드를 제외하고 동일(A-4) | E2E | 두 번 실행 후 정규화된 Verdict 비교 | 6 | 미구현 | - | - |
| REQ-H-006 | 실행 비용 제한 | 예산 없는 에이전트 루프는 비용이 폭주한다(SPEC 13.3) | run당 토큰·시간·에이전트별 호출 수 예산 초과 시 상태 저장 후 `BUDGET_EXCEEDED`로 보고 | Unit | 예산을 작게 둔 MockLLM run | 6 | 미구현 | - | - |

## 4. SPEC 기타 장의 검증 대상

SPEC 8장 밖에 있지만 Verification Matrix(SPEC 18)에서 판정해야 하는 규칙이다. 각 항목의 원문은 괄호의 SPEC 절에 있다.

| ID | 요구사항 | 해결할 문제 | 완료 조건 | 테스트 방법 | 검증 방법 | Phase | 상태 | 구현 위치 | 증거 |
|---|---|---|---|---|---|---|---|---|---|
| SPEC-5-1 | 도메인 경계 import 규칙 (5) | 도메인이 서로의 내부를 직접 쓰면 변경이 전파된다 | 5.1 허용 의존성 표와 "서비스 인터페이스 경유"가 import-linter로 강제되고, 규칙 위반이 실제로 BROKEN 됨 | Static, Unit | `make importlint` + `tests/test_domain_boundaries.py`(합성 트리에 위반 주입) | 1 | 검증됨 | `pyproject.toml` `[tool.importlinter]`, `tests/test_domain_boundaries.py` | 13 contracts kept, 0 broken. 경계 테스트 32 passed. 계약 완화 변이 시 2 failed (progress.md Phase 1 Evidence) |
| SPEC-5.3-1 | API 계약 diff (5.3) | 파괴적 API 변경이 클라이언트를 깬다 | main OpenAPI 스냅샷과 diff, 필드 삭제·타입 변경·필수화는 BLOCK | Contract | CI `contract` job | 3 | 미구현 | - | - |
| SPEC-5.3-2 | 마이그레이션 왕복 (5.3, 12.1) | 되돌릴 수 없는 스키마 변경은 롤백을 막는다 | 모든 Alembic 리비전 up/down 왕복 성공, 파괴적 DDL 탐지, expand→migrate→contract | Integration | 실제 PostgreSQL | 2, 5 | 미구현 | - | - |
| SPEC-5.3-3 | 요구사항↔테스트 매핑 (5.3) | 규칙과 테스트의 연결이 끊기면 회귀를 못 잡는다 | 이 표의 ID와 테스트 `req` 마커가 서로 맞음 | Unit | `tests/test_requirements_traceability.py` | 1 | 검증됨 | `tests/test_requirements_traceability.py` | traceability 테스트 통과(progress.md Phase 1 Evidence) |
| SPEC-5.3-4 | 설정·의존성 충돌 (5.3) | 새 환경변수가 문서에 없으면 배포가 깨진다 | 코드가 읽는 환경변수가 모두 `.env.example`에 있음, lockfile diff 리뷰 | Static | 설정 스캔 테스트 | 2 | 미구현 | - | - |
| SPEC-6-1 | 에이전트 I/O 스키마 (6) | 자유 텍스트 출력은 실행할 수 없다 | 출력 스키마 불일치 시 1회 재요청, 다시 실패하면 그 단계 ERROR | Unit | MockLLM 잘못된 출력 | 6–7 | 미구현 | - | - |
| SPEC-6-2 | 검증 에이전트 독립성 (6.1) | 구현자의 설명은 검증자를 편향시킨다 | 검증 에이전트 입력에 구현 에이전트 설명이 없고 diff와 실행 결과만 있음 | Unit | 컨텍스트 팩 내용 검사 | 7 | 미구현 | - | - |
| SPEC-6-3 | 판정은 LLM 없이 (2.1, 6) | LLM 판정은 근거가 될 수 없다 | Validation이 LLM 코드에 의존하지 않음(import 계약) + Checker 결과만으로 Verdict | Static, Unit | import-linter + Validation 단위 테스트 | 0, 6 | 부분 구현 | `pyproject.toml` 첫 번째 계약 | import 계약 KEPT, 위반 주입 시 BROKEN(`tests/test_domain_boundaries.py`). Validation 로직은 Phase 6 |
| SPEC-9-1 | CWE별 방어와 검증 (9) | 대표 CWE 각각에 방어와 테스트가 있어야 한다 | `docs/cwe-matrix.md`에서 9장 표 15개 행 전부 판정 | Security | REQ-N-008.2와 같음 | 3 | 미구현 | - | - |
| SPEC-9.1-1 | Prompt injection 방어 (9.1) | 코드·이슈 속 지시문이 에이전트를 조종할 수 있다 | 외부 텍스트는 `<untrusted>` 구획, 행동은 Tool Gateway 권한으로 제한, 코퍼스 회귀 테스트 통과 | Security | `verification/security/prompt_injection/` | 7 | 미구현 | - | - |
| SPEC-9.1-2 | LLM 송신 비밀 차단 (9.1) | 컨텍스트에 비밀이 섞이면 외부로 유출된다 | `.env`·키 파일 제외, 송신 전 secret 패턴 스캔으로 차단 | Unit | 비밀이 든 컨텍스트 송신 시도 | 6 | 미구현 | - | - |
| SPEC-10-1 | 비밀번호 해시 (10) | 유출된 해시가 쉽게 깨지면 안 된다 | Argon2id, ADR-0003 파라미터, 로그인 시 `check_needs_rehash`로 상향 | Unit, Integration | 해시 문자열 파라미터 검사 + 벤치마크 | 2 | 미구현 | - | - |
| SPEC-10-2 | JWT 서명 고정 (10) | `alg: none`·알고리즘 혼동으로 토큰을 위조할 수 있다 | EdDSA만 허용, `kid` 필수, 만료 15분. none·HS256·변조 토큰 401 | Security | 토큰 공격 테스트 | 2–3 | 미구현 | - | - |
| SPEC-10-3 | 난수 (10) | 예측 가능한 난수로 토큰을 추측할 수 있다 | 보안 용도 난수는 `secrets`만, `random` 금지 Semgrep 규칙 | Static | Semgrep 프로젝트 규칙 | 3 | 미구현 | - | - |
| SPEC-10-4 | 키 교체 (10) | 키를 바꿀 수 없으면 유출 시 대응할 수 없다 | JWKS에 현재+이전 키, 이전 키 토큰은 수명 동안 검증, RUNBOOK 절차 + 테스트 | Integration | 키 교체 시나리오 | 5 | 미구현 | - | - |
| SPEC-10-5 | 금지 암호 (10) | 약한 암호는 보호가 아니다 | MD5·SHA-1(보안 목적), ECB, 고정 IV, HS256 짧은 키 사용 0 | Static | Semgrep 규칙 | 3 | 미구현 | - | - |
| SPEC-11-1 | 동시 수정 락 (11.2) | 락 경합과 데드락은 부하에서만 드러난다 | 동시 수정에서 데드락 0, 락 대기 시간 기록 | Concurrency | 동시 PATCH 테스트 | 4 | 미구현 | - | - |
| SPEC-11-2 | 알고리즘 복잡도 (11.3) | 작은 N에서 숨은 O(N²)가 운영에서 터진다 | 의심 코드는 N=10²·10⁴·10⁶ 실행 시간 곡선 기록 | Performance | 벤치 스크립트 | 4 | 미구현 | - | - |
| SPEC-11-3 | 대용량 요청 OOM (11.5) | 큰 본문·동시 요청이 컨테이너를 죽일 수 있다(CWE-400) | 본문 크기 제한, 512MB 제한에서 대용량·동시 요청 시 OOM 재시작 0 | Chaos | 대용량 페이로드 + `docker inspect` | 4 | 미구현 | - | - |
| SPEC-12-1 | DB 장애 동작 (12) | DB가 끊기면 트래픽을 받지 말아야 한다 | 쿼리 타임아웃 2s, DB 끊김 시 `/readyz` 503, 복구 후 자동 정상화, 쓰기 실패는 재시도하지 않음 | Chaos | Toxiproxy `db_down` | 5 | 미구현 | - | - |
| SPEC-12-2 | 도구 실행 격리 (12) | hang 도구가 run 전체를 멈춘다 | 도구별 타임아웃·출력 크기 제한, hang 강제 종료 후 그 Check만 ERROR | Unit | sleep 도구 주입 | 6 | 미구현 | - | - |
| SPEC-12-3 | 파일 시스템 장애 (12) | 쓰기 실패 후 계속 진행하면 증거가 오염된다 | 쓰기 실패 시 run 중단, 부분 결과 보존 | Unit | 쓰기 불가 디렉터리 주입 | 6 | 미구현 | - | - |
| SPEC-12-4 | 헬스체크 분리 (12.1) | liveness와 readiness가 섞이면 잘못 재시작된다 | `/healthz`는 프로세스 생존, `/readyz`는 DB 연결 + 마이그레이션 버전 | Integration | pytest + compose | 2 | 미구현 | - | - |
| SPEC-12-5 | 롤백 (12.1) | 깨진 배포를 되돌릴 수 없으면 장애가 길어진다 | `make rollback`을 의도적으로 깨진 이미지에 실행해 이전 이미지로 복구 | Chaos | 롤백 시나리오 기록 | 5 | 미구현 | - | - |
| SPEC-13-1 | 도구 권한 매트릭스 (13.1) | 에이전트의 과도한 권한은 사고로 이어진다(Excessive Agency) | `permissions.yaml`대로 Tool Gateway가 허용·차단하고 감사 로그 기록, 보호 경로 쓰기 차단 | Unit | 권한 밖 요청 테스트 | 6 | 미구현 | - | - |
| SPEC-13-2 | 반복 실행 일치율 (13.2) | 단일 LLM 실행은 비결정적이다 | 판정에 영향 주는 LLM 단계는 N=3회 실행, Finding 합집합 + 일치율 기록 | Unit | MockLLM 다른 응답 3개 | 7 | 미구현 | - | - |
| SPEC-14-1 | TEST_REVIEW 이관 (14) | 테스트가 틀렸다는 판단을 AI가 혼자 하면 안 된다 | Self-Healing이 테스트 오류를 의심하면 수정하지 않고 TEST_REVIEW Finding 생성 | Unit | 상태 머신 테스트 | 7 | 미구현 | - | - |
| SPEC-15-1 | 서비스 관측성 (15) | 원인을 볼 수 없으면 복구할 수 없다 | JSON 로그(request_id·trace_id), Prometheus(요청 수·지연·오류율·DB 풀·쿼리 수), OTel HTTP→DB | Integration | `/metrics` 스크랩 + 로그 파싱 | 2–5 | 미구현 | - | - |
| SPEC-15-2 | 하네스 실행 이력 (15) | 어떤 판단이 어떤 근거로 나왔는지 남아야 한다 | run_id별 JSONL(에이전트, 프롬프트 버전, 도구, 결정, 실패, 수리), 토큰·지연·호출·재시도 수, 감사 로그 | Unit | run 후 JSONL 검사 | 6 | 미구현 | - | - |
| SPEC-15-3 | 로그 마스킹 (15) | 로그에 비밀이 남으면 그 자체가 유출이다(CWE-532) | 비밀번호·토큰·API 키·개인정보가 로그에 원문으로 남지 않음 | Security | 마스킹 테스트 | 3 | 미구현 | - | - |
| SPEC-16-1 | CI job (16.3) | 사람이 잊는 검사는 실행되지 않는다 | verify, security, contract, guard, ai-review, load-nightly job이 존재하고 동작 | CI | GitHub Actions run | 0, 3, 7, 8 | 부분 구현 | `.github/workflows/ci.yml` | verify·security job 녹색(run 37932537279). 나머지 job은 이후 Phase |
| SPEC-16-2 | AI PR Reviewer (16.2) | 사람 리뷰만으로는 일관성이 없다 | 판정 규칙 = 7장 불변식, CI 실패 시 BLOCK, PR 코멘트 + status check, fork PR 미실행. 외부 API 키가 필요하므로 오너 승인 후 도입(WORKING-GUIDELINES 14.3, 20) | CI | 테스트 PR | 8 | 미구현 | - | - |
| SPEC-16-3 | main 보호 (16) | main 직접 변경은 검증을 우회한다 | PR + 필수 체크(verify, security) + 승인 1 | CI | GitHub API로 설정 확인 + PR 머지 차단 확인 | 0 | 검증됨 | GitHub 저장소 설정 | 보호 규칙 GET 재확인, PR #1 `BLOCKED`/`REVIEW_REQUIRED` (progress.md Phase 0 Evidence) |
| SPEC-18-1 | 엣지 케이스 체크리스트 (18.2) | 경계값 하나가 장애가 된다 | 모든 입력 엔드포인트에 18.2의 13개 범주 테스트 존재 | Negative | 엔드포인트×범주 표 | 2–3 | 미구현 | - | - |
| SPEC-18-2 | Verification Matrix (18) | 판정이 흩어져 있으면 완료를 증명할 수 없다 | `make report`가 18장 11개 Category 전부를 Evidence와 함께 출력 | E2E | 리포트 검사 | 6, 8 | 미구현 | - | - |
| SPEC-19-1 | README 규격 (19.1) | 결정과 한계가 기록되지 않으면 책임질 수 없다 | README가 19.1의 10개 절을 모두 가짐 | Review | 절 존재 검사 | 8 | 미구현 | - | - |

## 열린 질문

SPEC만으로 답이 정해지지 않는 것들이다. 오너 답변 전까지 아래 **기본안**으로 Phase 2를 설계하고, 답이 다르면 해당 행과 ADR을 갱신한다.

| # | 질문 | 왜 정해지지 않는가 | 기본안 |
|---|---|---|---|
| Q-1 | Idempotency-Key를 어디에 저장하나? | SPEC 3은 Redis에 멱등성 키를 저장한다고 한다. REQ-N-006은 Redis 장애 중에도 CRUD가 계속되어야 하고, REQ-F-006은 중복 생성이 없어야 한다. Redis에만 두면 Redis 장애 시 둘 중 하나를 어기게 된다. | **PostgreSQL**에 `(user_id, key)` unique 테이블을 두고 리소스 생성과 같은 트랜잭션에서 기록한다. Redis는 rate limit에만 쓴다. SPEC 3 표와 다르므로 채택 시 ADR로 기록한다. |
| Q-2 | Todo 목록(REQ-F-004)에 공유받은 Todo도 포함하나? | REQ-F-004는 "Todo 목록"이라고만 한다. | 소유한 Todo만 포함한다. 공유받은 Todo는 단건 접근만 한다. |
| Q-3 | read 공유 대상이 수정·삭제를 시도하면 403인가 404인가? | REQ-F-005는 "권한 없는 사용자 접근 시 404"라고 하지만, read 사용자는 이미 존재를 안다. | 403. 존재를 모르는 사용자에게는 404(존재 은닉)를 유지한다. |
| Q-4 | refresh 재사용 탐지 시 같은 계열의 **access 토큰**도 즉시 무효화하나? | REQ-F-002의 "같은 계열 토큰"이 refresh만인지 access도인지 불명확하다. access까지 막으면 매 요청 폐기 목록 조회가 필요해 REQ-F-004의 쿼리 예산에도 영향을 준다. | refresh 계열만 폐기한다. access는 최대 15분 뒤 만료된다(SPEC 10). |
| Q-5 | 같은 Idempotency-Key로 (a) 다른 본문 재요청, (b) 처리 중 동시 요청이 오면 응답은? | SPEC은 "같은 키 재요청 시 같은 응답"만 정한다. | (a) 422, (b) 409(처리 중). 어느 경우에도 새 리소스를 만들지 않는다. |

## 가정

SPEC 문장을 구현 가능한 형태로 읽은 것이다. 새 기능을 추가하지 않는다.

| # | 가정 | 근거 |
|---|---|---|
| A-1 | 이메일 중복은 대소문자를 구분하지 않고 판단한다(저장 시 소문자 정규화). | REQ-F-001 "중복 409"의 일반적 의미. 다르면 같은 사람의 계정이 둘 생긴다. |
| A-2 | 회원 가입·로그인·갱신은 인증 없이 호출한다. | 인증 전 단계라서 인증을 요구할 수 없다. |
| A-3 | 공개 라우트 허용 목록: 가입, 로그인, 갱신, `/healthz`, `/readyz`, `/metrics`. 그 외는 인증 필수. | A-2와 SPEC 12.1(헬스체크), SPEC 15(Prometheus 스크랩). `/metrics`에는 개인정보를 넣지 않는다. |
| A-4 | REQ-H-005의 "Verdict가 동일"은 `run_id`와 시각 필드를 제외한 비교다. | run_id는 실행마다 달라야 Evidence 경로가 섞이지 않는다(SPEC 2.1 Evidence Store). |
| A-5 | Todo 삭제는 행 삭제(hard delete)다. | REQ-F-003 "DELETE 204, DB에 반영". soft delete 요구가 없다. |
