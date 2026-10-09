# Progress

## 현재 Phase: 1 — 요구사항·설계 (브랜치: `feature/phase-1-requirements-design`)

상태: **Exit Criteria 2개 모두 Evidence와 함께 충족**(아래 Phase 1 Evidence). PR 머지와 Phase 2 시작은 오너 승인 대기. Phase 2 설계에 영향을 주는 열린 질문 5개(`docs/requirements.md` Q-1~Q-5)에 대한 오너 답변이 필요하다.

| Exit Criteria (SPEC 17) | 판정 | 근거 |
|---|---|---|
| 모든 REQ에 검증 방법 존재 | 충족 | SPEC 8장 REQ 20개가 모두 `docs/requirements.md`에 있고, 세부 기준을 포함한 모든 행에 테스트·검증 방법이 있다. `tests/test_requirements_traceability.py`가 이를 강제한다. |
| 도메인 경계 import 규칙 설정 | 충족 | import-linter 13개 계약, 13 kept / 0 broken. 위반 10종이 각각 의도한 계약만 BROKEN 됨을 테스트로 증명 |

## 완료 — Phase 1

- [2026-10-09] 오너가 공통 지침을 v2로 교체 → `docs/WORKING-GUIDELINES.md`를 v2로 갱신(커밋 9ccd49c). Phase 1 산출물은 v2 기준(추적표에 "해결할 문제"·"증거" 칸, 문제 정의, 증거 없는 "검증됨" 금지)을 따른다.
- [2026-10-09] `docs/requirements.md`
  - SPEC 8장 REQ 20개를 세부 수용 기준까지 분해했다(REQ-F-001.1 등).
  - SPEC 5·6·9~19장의 검증 대상을 `SPEC-<장>-<n>` ID로 정리했다.
  - 모든 행에 해결할 문제, 완료 조건, 테스트·검증 방법, Phase, 상태, 증거 칸을 둔다.
  - 열린 질문 5개와 가정 5개를 기록했다.
- [2026-10-09] `docs/domain-boundaries.md`
  - 도메인 표, `interface.py`/`internal/` 구조, 교차 도메인 일괄 조회(쿼리 3개)를 정리했다.
  - SPEC 5.1 의존 방향과 생기는 충돌 2건을 설계로 해결했다.
    - 요청 인증은 `app.core.security`에 둔다.
    - 공유 접근은 `TodoAccessPolicy` 포트로 의존성을 역전한다.
- [2026-10-09] Target 패키지 골격: `services/todo-api/app/{core,domains/<5개>/internal}` (책임·소유 데이터·허용 의존성 docstring만)
- [2026-10-09] import-linter 계약 13개(Phase 0의 1개 + 12개)
  - 할 수 없는 import: `app` → `harness`, `app.core` → `app.domains`.
  - 도메인 쌍은 SPEC 5.1 허용 의존성만 허용한다.
  - 도메인 내부 패키지(`internal/`) 5개는 protected 계약으로 묶었다.
  - Makefile `importlint`에 `PYTHONPATH=services/todo-api`, mypy에 `services/todo-api/app` 추가.
- [2026-10-09] `tests/test_domain_boundaries.py`
  - 계약 ↔ SPEC 5.1 표 일치를 검사한다.
  - 계약에 나오는 모듈이 모두 존재하는지 검사한다.
  - 합성 트리에 위반 10종을 넣으면 각각 의도한 계약 하나만 BROKEN, 허용 의존만 넣으면 전부 KEPT인지 검사한다.
- [2026-10-09] `tests/test_requirements_traceability.py`
  - SPEC 8 REQ 전부 추적, 필수 칸, 상태값, 부모 ID를 검사한다.
  - `검증됨`과 `부분 구현`에는 위치와 증거가 있어야 한다.
  - 테스트 `req` 마커는 알려진 ID만 쓸 수 있다.
- [2026-10-09] `ARCHITECTURE.md`, ADR-0002(오케스트레이터 상태 머신), ADR-0003(암호 정책 + Argon2id 벤치마크), ADR-0001 Phase 1 재검토
- [2026-10-09] `make bandit` 범위에 `services/todo-api/app` 추가

## Phase 1 Evidence

모든 명령은 저장소 루트, Windows 11 + Git Bash, uv 관리 CPython 3.12.14에서 실행했다.

| 검사 | 명령 | 결과 |
|---|---|---|
| verify | `make verify` | ruff "All checks passed!", "28 files already formatted"; mypy "no issues found in 24 source files"; import-linter "Contracts: 13 kept, 0 broken."; pytest "362 passed"; exit 0 |
| security | `make security` | semgrep "Findings: 0", 151 rules; bandit High 0 / Medium 0 (harness + app, 33 LOC); pip-audit "No known vulnerabilities found"; gitleaks "no leaks found"; exit 0 |
| 경계 계약 동작 | `uv run pytest tests/test_domain_boundaries.py` | 32 passed. 위반 10종은 각각 의도한 계약 1개만 BROKEN, 허용 의존 조합은 13 kept |
| 경계 테스트 변이 검사 | `pyproject.toml`에서 todos의 금지 목록에서 `app.domains.sharing`을 빼고 테스트 실행 → 원복 | 2 failed(`test_domain_dependency_rules_match_spec_table`, todos→sharing 위반 케이스) → 원복 후 32 passed |
| 추적표 테스트 | `uv run pytest tests/test_requirements_traceability.py` | 281 passed |
| 추적표 변이 검사 1 | `REQ-N-006` 행 삭제 → 원복 | 2 failed(누락 탐지) |
| 추적표 변이 검사 2 | `REQ-F-003.1`을 증거 없이 `검증됨`으로 변경 → 원복 | 1 failed(증거 없는 검증됨 탐지) |
| 추적표 변이 검사 3 | `@pytest.mark.req("REQ-F-999")` 임시 테스트 추가 → 삭제 | 1 failed(알 수 없는 ID 탐지) |
| OWASP 대조 | Password Storage Cheat Sheet 조회(2026-10-09) | Argon2id 최소 `m=19456 (19 MiB), t=2, p=1`, "Benchmark the chosen parameters on the target system" |
| Argon2id 벤치마크 | `python:3.12-slim`, `--cpus 2 --memory 512m`, argon2-cffi 25.1.0, 2회 | 선택 후보 m=64MiB t=3 p=1 중앙값 291.0 ms / 191.3 ms. 전체 표는 ADR-0003 |
| CI | PR [#2](https://github.com/kswkm/Multi-Agent-Engineering-System/pull/2), run 37937066818 | `verify` pass(13s), `security` pass(46s). 로그: mypy "no issues found in 24 source files", "Contracts: 13 kept, 0 broken.", "362 passed", semgrep "Findings: 0", pip-audit "No known vulnerabilities found", gitleaks "no leaks found" |

## 열린 Finding

- 없음.

## 오너 확인 필요

- `docs/requirements.md` 열린 질문 Q-1~Q-5. 답변 전까지 Phase 2는 기본안으로 설계한다. Q-1(멱등성 키 저장소)은 SPEC 3 표와 다른 기본안이라 특히 확인이 필요하다.

## NOT_VERIFIED

- **Argon2id 최종 파라미터**: 측정 편차(191–291 ms)가 커서 잠정 결정이다. 실제 api 이미지가 생기는 Phase 2에서 재측정해 확정한다.
- **main 직접 push 차단**(Phase 0부터 유지): 보호 규칙 설정값과 PR 머지 차단은 확인했지만, 실제로 main에 직접 push해서 거부되는지는 시험하지 않았다.

## 다음 할 일

1. 오너: Q-1~Q-5 답변, Phase 1 PR 검토·머지.
2. Phase 2(오너 승인 후)
   - Auth, Users, Todos, Tags, Sharing을 domain-boundaries 구조대로 구현한다.
   - Alembic, RFC 9457 오류, `/healthz`·`/readyz`, structlog를 붙인다.
   - 단위·통합(Testcontainers)·계약 테스트를 쓴다.
   - api 컨테이너를 추가하고 Argon2id를 재측정한다.
   - router protected 계약을 추가한다.

---

## Phase 0 기록 — 분석·부트스트랩 (PR #1, squash merge `2b99a90`)

상태: Exit Criteria 3개 모두 Evidence와 함께 충족(make verify, compose 기동, CI 녹색).

### Phase 0 분석

- **저장소 상태 (2026-10-09)**: `main` 브랜치에 커밋 0개, 작업 트리에 파일 없음(`.git`만 존재). remote `origin = https://github.com/kswkm/Multi-Agent-Engineering-System.git`.
- **기존 README / CLAUDE.md / ARCHITECTURE / SECURITY / TESTING / CI / docker-compose / 스키마 / 테스트**: 모두 없음.
- **SPEC과 충돌하는 기존 규칙**: 없음(기존 규칙 자체가 없음). 따라서 SPEC 3장 기본 스택으로 부트스트랩했다.
- **개발 환경 (Windows 11)**
  - 시스템 Python 3.13.2만 있음. 3.12는 uv가 프로젝트 단위로 설치(CPython 3.12.14).
  - 없던 도구를 오너 승인 하에 winget(user scope)으로 설치: uv 0.12.24, GNU Make 4.4.1(ezwinports), gitleaks 8.30.1.
  - GitHub CLI(`gh`) winget 설치는 실패(`copy_file: Access is denied`). 이후 오너가 직접 설치·로그인했다.
  - Docker 엔진이 처음에는 `500 Internal Server Error`를 반환했다. 오너가 Docker Desktop을 재시작한 뒤 29.8.2로 정상 동작했다.
  - 로컬에 PostgreSQL 17이 설치되어 있어 5432 충돌 가능 → compose 호스트 포트 기본값을 55432/56379/58474로 정함(ADR-0001).
- **두 지침 문서 사이의 해석**: 부록 B는 미구현 Makefile 타깃을 "TODO로 명확히 실패"하라고 하고, 공통 지침(04)은 TODO/placeholder를 남기지 말라고 한다. 두 요구를 함께 만족하도록 미구현 타깃은 `NOT_IMPLEMENTED: ... arrives in Phase N`으로 **실패**하게 했다.

### 완료 — Phase 0

- SPEC PDF → `docs/SPEC.md`, 공통 지침 PDF → `docs/WORKING-GUIDELINES.md`
- SPEC 4장 디렉터리 구조, `harness` 패키지 골격(하위 패키지 7개, 책임 docstring)
- uv 프로젝트, ruff/mypy/pytest/coverage/import-linter/bandit 설정, import-linter 계약 1개
- Makefile(install, verify, security; load/chaos/report는 NOT_IMPLEMENTED로 실패)
- docker-compose(postgres 16, redis 7, toxiproxy 2.12.0, healthcheck, localhost 바인딩, 비밀번호 미설정 시 기동 거부)
- `.env.example`, `.gitignore`, `.gitattributes`(LF), pre-commit(gitleaks hook은 설치된 바이너리 사용)
- `CLAUDE.md`, CI(verify + security), PR 템플릿, CODEOWNERS, `tests/test_bootstrap.py`, ADR-0001, backlog
- GitHub: 빈 루트 커밋으로 `main` 생성, PR #1, CI 녹색, `main` 보호 규칙, squash merge

### Phase 0 Evidence

| 검사 | 명령 | 결과 |
|---|---|---|
| verify | `make verify` | ruff 통과, mypy 9개 파일 이상 없음, "Contracts: 1 kept, 0 broken.", 49 passed, exit 0 |
| pre-commit | `uv run pre-commit run --all-files` | 10개 hook 전부 Passed |
| security | `make security` | bandit 0, semgrep 151 rules 0 findings, pip-audit 취약점 없음, gitleaks no leaks, exit 0 |
| gitleaks 음성 검사 | 가짜 GitHub 토큰 stage 후 `gitleaks git --pre-commit --staged` | "leaks found: 1", exit 1 → 원복 |
| 미구현 타깃 | `make load STAGE=smoke`, `make chaos SCENARIO=db_down`, `make report` | 각각 `NOT_IMPLEMENTED ...`, exit 2 |
| import 계약 음성 검사 | `harness/checkers/_violation.py`에 `import harness.llm` 임시 추가 | `BROKEN`, exit 1 → 원복 후 kept |
| compose 기동·헬스 | `docker compose up -d` + `docker compose ps` | postgres 16 / redis 7 / toxiproxy 2.12.0 모두 `Up (healthy)` |
| compose 실제 접속 | `psql select version()`, `redis-cli ping`, `curl :58474/version` | "PostgreSQL 16.15", "PONG"(Redis 7.4.11), `{"version": "2.12.0"}` |
| CI 녹색 | PR #1, run 37932537279 | `verify` pass, `security` pass. 로그로 테스트·스캔 실제 실행 확인 |
| main 보호 규칙 | `gh api` PUT 후 GET 재확인 | 필수 체크 verify·security(strict), 승인 1 + CODEOWNERS, linear history, force push·삭제 금지, squash only |
| 보호 규칙 실효성 | `gh pr view 1 --json mergeStateStatus,reviewDecision` | `BLOCKED`, `REVIEW_REQUIRED` |

### 저장소 이력 메모

- `main`의 첫 커밋은 PR base로 쓰려고 만든 빈 루트 커밋(`chore: initialize repository`, 파일 변경 없음)이다. 원격이 비어 있어 base 브랜치 없이는 PR을 만들 수 없었다.
