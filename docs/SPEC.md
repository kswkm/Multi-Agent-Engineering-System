# Multi-Agent Engineering System — 개발 기획서 v1.0

> Enterprise Harness Engineering 개발 기획서 — Claude Code 실행용
>
> **코딩 10% / 검증 90%**
> 생성 → 이해 → 검증 → 공격 → 부하 → 장애 → 복구 → 재검증 → 운영 가능성 증명

| 항목 | 내용 |
|---|---|
| 문서 목적 | Claude Code가 이 문서만 읽고 바로 저장소를 만들고, 단계별로 구현·검증할 수 있도록 한다. |
| 독자 | Claude Code(구현 주체), 프로젝트 오너(사람, 최종 승인자) |
| 작성일 | 2026-10-08 |
| 상태 | Draft for implementation. 이 문서가 Source of Truth이며, 변경 시 버전을 올린다. |

> AI가 코드를 생성하는 것은 시작일 뿐이다. Harness는 그 코드가 실제 환경에서 안전하고 신뢰할 수 있는지 **증명**해야 한다.

_원본: `Multi-Agent-Engineering-System_개발기획서.pdf` (28쪽). 이 파일은 PDF 내용을 Markdown으로 옮긴 것이다._

## 목차

- 00 Claude Code 작업 규칙 (먼저 읽을 것)
- 01 프로젝트 개요와 목표
- 02 시스템 구성
- 03 기술 스택과 선택 이유
- 04 저장소 구조
- 05 도메인 경계
- 06 에이전트 명세
- 07 공통 데이터 계약
- 08 요구사항과 수용 기준
- 09 보안 엔지니어링 (CWE Top 25)
- 10 암호 정책
- 11 성능·DB·메모리 검증
- 12 장애 격리와 복원력
- 13 AI 출력 통제와 가드레일
- 14 Self-Healing 루프
- 15 관측성
- 16 GitFlow와 AI PR 리뷰
- 17 마일스톤 (Phase 0–8)
- 18 Verification Matrix와 완료 조건
- 19 README·PR 문서화 규격
- A 부록 A. CLAUDE.md 초안
- B 부록 B. Claude Code 첫 실행 프롬프트
- C 부록 C. 템플릿 모음

> **이 문서를 읽는 법**
> 0장의 작업 규칙은 모든 단계에 적용된다. 17장의 마일스톤 순서대로 진행하고, 각 Phase의 **Exit Criteria**를 Evidence와 함께 충족한 뒤에만 다음 Phase로 넘어간다. 부록 B의 프롬프트를 Claude Code 첫 메시지로 그대로 사용할 수 있다.

---

## 00 Claude Code 작업 규칙

너는 단순한 Coding Agent가 아니라 **Enterprise AI Engineering Verification System**을 구현하는 엔지니어다. 아래 규칙은 모든 Phase에 우선한다.

### 0.1 절대 규칙

| # | 규칙 | 의미 |
|---|---|---|
| R1 | **실행 결과가 자기보고보다 우선한다** | "해결했습니다"는 PASS가 아니다. 명령을 실행하고 출력(숫자, 로그, 리포트 경로)을 Evidence로 남긴다. |
| R2 | **검사하지 않은 것은 안전하지 않다** | 미검증 항목은 `NOT_VERIFIED`, 해당 없음은 근거와 함께 `NOT_APPLICABLE`로 명시한다. |
| R3 | **테스트를 약화시키지 않는다** | 테스트 삭제, assertion 제거, skip 추가, 임계값 완화, 요구사항 변경으로 PASS를 만드는 행위를 금지한다. 테스트가 틀렸다고 판단되면 `TEST_REVIEW` 이슈를 만들고 사람에게 묻는다. |
| R4 | **기존 구조를 먼저 읽는다** | 작업 전 README, CLAUDE.md, ARCHITECTURE.md, SECURITY.md, TESTING.md, docker-compose, CI, 스키마, 기존 테스트를 확인한다. 확인 없이 새 구조를 만들지 않는다. |
| R5 | **main에 직접 커밋하지 않는다** | 모든 변경은 `feature/*`, `fix/*`, `security/*`, `perf/*` 브랜치와 PR로 진행한다. |
| R6 | **비밀 정보는 저장소와 로그에 남기지 않는다** | API 키, 토큰, 비밀번호는 환경변수나 secret store로만 다룬다. `.env`는 커밋하지 않고 `.env.example`만 둔다. |
| R7 | **범위를 지킨다** | 현재 Phase의 범위를 넘는 기능은 만들지 않고 `docs/backlog.md`에 기록한다. |
| R8 | **불확실하면 멈추고 묻는다** | 되돌릴 수 없는 결정(스키마 파괴적 변경, 데이터 삭제, 배포)이나 요구사항 충돌은 사람에게 확인받는다. |

### 0.2 매 작업 시작 시 루틴 (Context Pollution 방지)

1. 현재 Phase와 해당 Exit Criteria를 이 문서에서 다시 읽는다.
2. `docs/progress.md`에서 직전 상태, 미해결 Finding, 다음 할 일을 확인한다.
3. 관련 코드와 테스트만 열람한다. 무관한 파일을 대량으로 읽지 않는다.
4. 이전 단계의 추론을 사실로 간주하지 않는다. 필요한 것은 다시 실행해서 확인한다.

### 0.3 매 작업 종료 시 루틴

1. `make verify` (lint, type, test, security)를 실행하고 결과를 확인한다.
2. `docs/progress.md`를 갱신한다: 한 일, Evidence 경로, 남은 Finding, 다음 할 일.
3. 의미 있는 결정은 `docs/adr/NNNN-*.md` (Architecture Decision Record)로 남긴다.
4. 커밋 메시지는 Conventional Commits(`feat:`, `fix:`, `perf:`, `security:`, `test:`, `docs:`)를 따른다.

> **금지 문장**
> "아마 동작할 것입니다", "문제없어 보입니다", "테스트는 생략했지만 정상입니다". 이런 문장 대신 실행한 명령, 결과 수치, 남은 리스크를 쓴다.

---

## 01 프로젝트 개요와 목표

### 1.1 문제 정의

AI가 생성하는 코드는 빠르고 저렴하지만, 배포 후 책임을 질 근거가 없다. 엔터프라이즈 환경은 규제, 기밀(외부 학습 불가), 무중단 운영이라는 제약을 갖고 있어 "돌아가는 코드"로는 부족하다. 이 프로젝트는 **AI가 만든 코드를 어디까지 신뢰할 수 있는지 자동으로 검증하고, 그 근거를 남기는 하네스**를 만든다.

### 1.2 목표

| ID | 목표 | 증명 방법 |
|---|---|---|
| G1 | 요구사항 → 구현 → 다단계 검증 → 자가 수리 → 재검증을 자동화하는 멀티 에이전트 파이프라인 | E2E 파이프라인 실행 로그와 최종 Verification Report |
| G2 | 검증 대상 서비스(Todo API)를 보안·성능·장애 관점에서 운영 가능한 수준으로 증명 | Verification Matrix 전 항목 PASS + Evidence |
| G3 | 정상·비정상·악성 흐름 모두에 대한 방어 | CWE 매핑 테스트, fuzzing, prompt injection 테스트 |
| G4 | 로컬 환경에서 규모 차이를 극복하는 부하·메모리·DB 병목 검증 | k6 리포트, memray 리포트, 쿼리 카운트 Before/After |
| G5 | 모든 결정을 "문제 → 원인 → 결정 → 대안 → 검증 → 결과"로 기록 | README, ADR, PR 본문 |

### 1.3 비목표 (이번 버전에서 하지 않는 것)

- 실제 클라우드 운영 배포. 대신 로컬 Docker Compose에서 롤링 배포·헬스체크·롤백 경로를 시뮬레이션한다.
- 웹 프론트엔드 UI. API와 CLI, 리포트(HTML/Markdown)만 제공한다.
- 범용 에이전트 프레임워크 제작. 이 프로젝트의 검증 파이프라인에 필요한 만큼만 만든다.

### 1.4 최종 산출물

**코드**
- `harness/` 멀티 에이전트 검증 파이프라인
- `services/todo-api/` 검증 대상 서비스
- `verification/` 부하·장애·보안 시나리오
- CI 워크플로와 AI PR Reviewer

**문서와 증거**
- README (문제·설계·트레이드오프·한계)
- ARCHITECTURE, SECURITY, TESTING, RUNBOOK
- ADR 모음, PR 기록
- `reports/` Verification Matrix와 Evidence

---

## 02 시스템 구성

시스템은 두 부분으로 나뉜다. **Harness**는 검증하는 쪽이고, **Target Service**는 검증받는 쪽이다. 하네스가 실제 서비스를 상대로 일한다는 점을 보여주기 위해 둘을 같은 저장소에 두되 의존 방향은 Harness → Target 단방향으로 고정한다.

```
                         USER (Requirement / Issue)
                                    │
                                    ▼
┌───────────────────────────── HARNESS ──────────────────────────────┐
│  Requirement Agent ─▶ Context Builder ─▶ Architecture Agent        │
│                                                │                   │
│                                                ▼                   │
│                                     Implementation Agent           │
│                                                │ feature branch    │
│                                                ▼                   │
│  ┌───────── Verification Stage (parallel, independent) ─────────┐  │
│  │ Code Review │ Security │ Perf/DB │ Reliability │ Test        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                │                                   │
│                                ▼                                   │
│               Validation Agent ──FAIL──▶ Self-Healing              │
│                                │ PASS          (max 3 → Human)     │
│                                ▼                                   │
│                   Verification Report + Evidence                   │
└────────────────────────────────────────────────────────────────────┘
                                 │ execute · measure · attack
                                 ▼
┌────────────────────────── TARGET SERVICE ──────────────────────────┐
│  todo-api (FastAPI) ──▶ PostgreSQL 16 ──▶ Redis (rate limit)       │
│     │                                                              │
│     └─ /healthz /readyz /metrics   (fault injection: toxiproxy)    │
└────────────────────────────────────────────────────────────────────┘
```

### 2.1 구성 요소 요약

| 구성 요소 | 책임 |
|---|---|
| Orchestrator | 에이전트 실행 순서, 상태 전이, 재시도·타임아웃·예산 제한, 실행 이력 저장. 명시적 상태 머신으로 구현한다. |
| Agents | 역할별로 분리된 LLM 호출 단위. 각자 입력 스키마, 출력 스키마, 도구 권한을 가진다. |
| Tool Gateway | 에이전트의 모든 도구 호출이 지나가는 관문. 권한 검사, 경로 샌드박스, 감사 로그를 담당한다. |
| Deterministic Checkers | LLM이 아닌 실제 도구(pytest, semgrep, k6, memray 등)를 실행하고 결과를 파싱한다. **판정의 근거는 여기서 나온다.** |
| Evidence Store | 실행 결과, 리포트, 로그를 `reports/<run_id>/`에 저장하고 Matrix와 연결한다. |
| Target Service | 인증, 사용자, Todo, 태그, 공유 기능을 가진 API. N+1, 권한, 입력 검증 등 실제로 문제가 생길 수 있는 지점을 일부러 포함한다. |

> **핵심 설계 원칙: LLM은 제안하고, 도구가 판정한다**
> 에이전트의 출력(예: "보안 문제 없음")은 판정 근거가 될 수 없다. Validation Agent는 Deterministic Checker의 실행 결과만으로 PASS/FAIL을 결정하고, LLM 리뷰 결과는 *추가 Finding의 출처*로만 사용한다.

---

## 03 기술 스택과 선택 이유

저장소가 비어 있다면 아래 스택으로 시작한다. 이미 저장소가 있다면 기존 스택을 우선하고, 차이를 ADR로 기록한다.

| 영역 | 선택 | 이유 |
|---|---|---|
| 언어/런타임 | Python 3.12, `uv` | AI 생태계와 검증 도구 호환성이 가장 높고, uv로 재현 가능한 lockfile을 빠르게 관리한다. |
| Target API | FastAPI, Pydantic v2 | 스키마 기반 입력 검증과 OpenAPI 자동 생성으로 contract 테스트와 fuzzing(Schemathesis)이 쉽다. |
| DB / ORM | PostgreSQL 16, SQLAlchemy 2.0(async), Alembic | N+1, 인덱스, 락, 커넥션 풀 고갈 같은 실제 병목을 재현하고 `EXPLAIN`으로 증명할 수 있다. |
| 캐시/제한 | Redis 7 | rate limit, 멱등성 키 저장. 장애 시 graceful degradation 검증 대상. |
| LLM | Anthropic SDK, 모델명은 환경변수 | 모델 교체 가능하게 `LLMProvider` 인터페이스 뒤에 둔다. 테스트에서는 `MockLLMProvider`로 결정론을 확보한다. |
| 오케스트레이션 | 직접 구현한 asyncio 상태 머신 | 프레임워크 블랙박스 없이 상태 전이, 재시도, 예산을 테스트로 증명하기 위해서다. (도입 시 ADR 필수) |
| 테스트 | pytest, pytest-asyncio, Hypothesis, Testcontainers, Schemathesis | 단위·통합(실제 Postgres)·속성 기반·API fuzzing을 한 체계에서 실행한다. |
| 정적 분석 | ruff, mypy `--strict` | 스타일과 타입 오류를 결정론적으로 차단한다. |
| 보안 스캔 | Semgrep, Bandit, pip-audit, gitleaks, Trivy | SAST, 의존성 CVE, 비밀 유출, 컨테이너 이미지 취약점을 각각 다룬다. |
| 부하 | k6 | 단계적 부하, 임계값(threshold) 기반 PASS/FAIL, JSON 결과 출력이 가능하다. |
| 메모리 | memray, tracemalloc, `docker stats` | 힙 증가와 객체 보존을 관찰하고, 컨테이너 메모리 제한으로 OOM을 재현한다. |
| 장애 주입 | Toxiproxy | DB·Redis·LLM 경로에 지연, 끊김, 대역폭 제한을 주입한다. |
| 관측성 | structlog(JSON), OpenTelemetry, Prometheus (+Grafana 선택) | 에이전트 실행 추적과 서비스 메트릭을 같은 trace id로 연결한다. |
| CI | GitHub Actions | PR마다 verify, 보안 스캔, AI PR Review를 자동 실행한다. |

---

## 04 저장소 구조

```
multi-agent-engineering-system/
├── CLAUDE.md                  # Claude Code 작업 규칙 (부록 A)
├── AGENTS.md                  # 에이전트 역할·권한 요약 (6장)
├── README.md                  # 19장 규격
├── ARCHITECTURE.md  SECURITY.md  TESTING.md  RUNBOOK.md
├── Makefile                   # verify, test, security, load, chaos, report
├── docker-compose.yml         # api, postgres, redis, toxiproxy, prometheus
├── .env.example               # 비밀값 없는 템플릿
├── .github/
│   ├── workflows/ci.yml  security.yml  ai-pr-review.yml  load-nightly.yml
│   ├── pull_request_template.md
│   └── CODEOWNERS             # tests/, verification/, harness/policies/ 보호
├── harness/
│   ├── orchestrator/          # state_machine.py, runner.py, budget.py
│   ├── agents/                # requirement, architecture, implementation,
│   │                          # code_review, security, performance, reliability,
│   │                          # test_engineer, validation, self_healing
│   ├── prompts/               # 에이전트별 시스템 프롬프트 (버전 관리)
│   ├── schemas/               # Finding, Verdict, Evidence, AgentIO (Pydantic)
│   ├── llm/                   # provider.py, anthropic_provider.py, mock_provider.py
│   ├── tools/                 # gateway.py, permissions.py, sandbox.py
│   ├── checkers/              # pytest_, semgrep_, k6_, memray_, query_count_ ...
│   ├── policies/              # permissions.yaml, forbidden_actions.yaml
│   ├── evidence/              # store.py, matrix.py, report_renderer.py
│   └── cli.py                 # `harness run --issue ...`
├── services/todo-api/
│   ├── app/
│   │   ├── domains/           # auth/, users/, todos/, tags/, sharing/
│   │   ├── core/              # config, security, db, logging, errors
│   │   └── main.py
│   ├── migrations/            # Alembic
│   └── tests/                 # unit/, integration/, contract/, property/
├── verification/
│   ├── load/                  # k6 시나리오 (smoke, load, stress, soak)
│   ├── chaos/                 # toxiproxy 시나리오
│   ├── security/              # 공격 페이로드, prompt injection 코퍼스
│   └── memory/                # soak + memray 스크립트
├── docs/
│   ├── adr/  requirements.md  domain-boundaries.md
│   ├── progress.md  backlog.md  cwe-matrix.md
└── reports/                   # (gitignore) run별 Evidence
```

---

## 05 도메인 경계

각 도메인은 자신이 소유한 데이터만 직접 쓴다. 다른 도메인의 데이터가 필요하면 해당 도메인의 서비스 인터페이스를 거친다. 경계를 넘는 import는 정적 검사(import-linter)로 차단한다.

### 5.1 Target Service

| 도메인 | 책임 | 데이터 소유권 | 허용 의존성 |
|---|---|---|---|
| Auth | 로그인, 토큰 발급·갱신·폐기, 비밀번호 해시 | credentials, refresh_tokens | Users(조회만) |
| Users | 사용자 프로필, 계정 상태 | users | 없음 |
| Todos | Todo CRUD, 상태 전이, 페이지네이션 | todos | Users(소유자 확인), Tags(연결) |
| Tags | 태그 생성, Todo-태그 연결 | tags, todo_tags | 없음 |
| Sharing | Todo 공유 권한(read/write) | todo_shares | Todos, Users |

### 5.2 Harness

| 도메인 | 책임 | 입력 → 출력 | 권한 |
|---|---|---|---|
| Agent | 역할별 판단과 제안 | AgentInput → AgentOutput(스키마 검증) | Tool Gateway를 통해서만 행동 |
| Tool | 파일·셸·git·네트워크 실행 | ToolCall → ToolResult | permissions.yaml에 정의된 범위 |
| Validation | 결정론적 판정, Matrix 생성 | CheckerResult[] → Verdict | Read + Execute(검사 도구) |
| Evidence | 증거 저장과 리포트 렌더링 | Evidence → reports/ | reports/ 쓰기만 |

### 5.3 기존 시스템 충돌 검증 항목

새 코드는 다음 항목에서 기존 시스템과 충돌하지 않아야 한다. 각 항목은 자동 검사 또는 리뷰 체크리스트로 확인한다.

| 항목 | 검증 방법 |
|---|---|
| API Contract | main 브랜치 OpenAPI 스냅샷과 diff. 파괴적 변경(필드 삭제, 타입 변경, 필수화)은 BLOCK. |
| Schema | Alembic 마이그레이션의 up/down 왕복 테스트, 파괴적 DDL 탐지. |
| Business Rule | `docs/requirements.md`의 규칙 ID와 테스트 매핑이 끊기지 않는지 확인. |
| AuthN / AuthZ | 모든 엔드포인트가 인증 의존성을 갖는지 라우트 목록으로 검사, 소유권 테스트 실행. |
| Transaction / Dependency / Config | 트랜잭션 경계 리뷰, lockfile diff, 신규 환경변수의 `.env.example` 반영 여부. |

---

## 06 에이전트 명세

모든 에이전트는 **입력 스키마, 출력 스키마, 도구 권한, 최대 토큰, 타임아웃**을 가진다. 출력이 스키마에 맞지 않으면 한 번 재요청하고, 다시 실패하면 해당 단계를 `ERROR`로 기록한다. 권한 표기: R=읽기, W=쓰기, X=실행, N=네트워크, G=git.

| Agent | 책임 | 주요 출력 | 권한 |
|---|---|---|---|
| Requirement | 요청을 기능·비기능 요구사항, 제약, 수용 기준, 검증 방법으로 분해한다. 모호하면 질문 목록을 만든다. | Requirement[] (REQ-ID, acceptance, verification) | R |
| Context Builder | 작업에 필요한 규칙, 아키텍처, 관련 코드·테스트, 기존 Finding만 골라 컨텍스트 팩을 만든다. (결정론적 코드 + 검색) | ContextPack (파일 목록, 토큰 수, 근거) | R |
| Architecture | 도메인 경계, 의존 방향, 장애 격리, 확장성 관점에서 설계와 변경 계획을 낸다. | DesignPlan, 영향 범위, ADR 초안 | R |
| Implementation | 계획에 따라 feature 브랜치에서 코드와 테스트를 작성한다. | Patch, 테스트, 변경 요약 | R W G |
| Code Reviewer | diff 기준으로 정확성, 가독성, 회귀 위험을 리뷰한다. | Finding[] | R |
| Security Reviewer | CWE 기준 리뷰와 보안 스캐너 결과 해석. 악성 흐름 테스트 케이스를 제안한다. | Finding[] (CWE ID 포함) | R X |
| Performance Reviewer | 복잡도, 쿼리 수, 인덱스, 메모리 패턴을 검토하고 부하 결과를 해석한다. | Finding[], 측정 계획 | R X |
| Reliability Reviewer | 타임아웃, 재시도, 서킷 브레이커, 폴백, 그레이스풀 셧다운을 검토하고 장애 시나리오를 실행한다. | Finding[], chaos 결과 | R X |
| Test Engineer | 엣지 케이스, 속성 기반, 회귀 테스트를 추가한다. 기존 테스트 수정은 금지(추가만). | 신규 테스트 파일 | R W(tests/ 신규만) X |
| Validation | **LLM 없이** 모든 Checker 결과를 모아 Matrix와 Verdict를 만든다. | Verdict, VerificationMatrix | R X |
| Self-Healing | FAIL의 원인을 분석하고 수정 계획을 세워 Implementation Agent에게 넘긴다. 직접 테스트를 수정하지 않는다. | RootCause, FixPlan | R |

### 6.1 독립성 규칙

- Implementation Agent와 검증 에이전트는 서로 다른 시스템 프롬프트와 컨텍스트 팩을 사용한다. 검증 에이전트는 구현 에이전트의 "설명"을 받지 않고 **diff와 실행 결과**만 받는다.
- 최종 판정자는 Validation Agent(결정론적 코드)이며, 구현 에이전트는 자기 코드를 PASS시킬 수 없다.
- 프로덕션 배포, 데이터 삭제, 보호 경로 수정은 Human Approval이 필요하다.

---

## 07 공통 데이터 계약

모든 에이전트와 Checker는 아래 스키마로 결과를 주고받는다. `harness/schemas/`에 Pydantic 모델로 구현하고, 스키마 자체에 대한 단위 테스트를 둔다.

```python
from enum import StrEnum
from pydantic import BaseModel, Field

class Status(StrEnum):
    PASS = "PASS"; FAIL = "FAIL"; ERROR = "ERROR"
    NOT_APPLICABLE = "NOT_APPLICABLE"; NOT_VERIFIED = "NOT_VERIFIED"

class Severity(StrEnum):
    CRITICAL = "CRITICAL"; HIGH = "HIGH"; MEDIUM = "MEDIUM"; LOW = "LOW"; INFO = "INFO"

class Evidence(BaseModel):
    kind: str                       # "command" | "report" | "metric" | "log"
    command: str | None = None      # 실제 실행한 명령
    exit_code: int | None = None
    artifact_path: str | None = None   # reports/<run_id>/...
    metrics: dict[str, float] = Field(default_factory=dict)  # p95_ms, queries, rss_mb ...
    summary: str                    # 사람이 읽는 한 줄

class Finding(BaseModel):
    id: str                         # F-SEC-0001
    category: str                   # security | performance | database | reliability | ...
    severity: Severity
    title: str
    location: str | None = None     # path:line
    cwe: str | None = None          # "CWE-89"
    source: str                     # "semgrep" | "llm:security_reviewer" | ...
    evidence: list[Evidence]
    recommendation: str | None = None

class CheckResult(BaseModel):
    category: str
    status: Status
    evidence: list[Evidence]        # PASS인데 evidence가 비어 있으면 검증 오류
    findings: list[Finding] = []
    reason: str | None = None       # NOT_APPLICABLE / NOT_VERIFIED 사유 (필수)

class Verdict(BaseModel):
    run_id: str
    overall: Status
    pr_decision: str                # PASS | REQUEST_CHANGES | BLOCK
    matrix: list[CheckResult]
    repair_attempts: int
```

> **스키마 수준 불변식 (validator로 강제)**
> - `status == PASS`이면 `evidence`가 1개 이상이어야 한다.
> - `NOT_APPLICABLE`, `NOT_VERIFIED`는 `reason`이 필수다.
> - CRITICAL 또는 HIGH Finding이 하나라도 열려 있으면 `overall`은 PASS가 될 수 없고 `pr_decision`은 BLOCK이다.
> - MEDIUM Finding이 남아 있으면 `REQUEST_CHANGES`다.

---

## 08 요구사항과 수용 기준

모든 요구사항은 검증 방법을 가진다. `docs/requirements.md`에 아래 형식으로 관리하고, 테스트 이름이나 마커에 REQ-ID를 붙여 추적한다(`@pytest.mark.req("REQ-F-003")`).

### 8.1 기능 요구사항 (Target Service)

| ID | 요구사항 | 수용 기준 | 검증 |
|---|---|---|---|
| REQ-F-001 | 사용자는 이메일·비밀번호로 가입하고 로그인한다. | 가입 201, 중복 409, 로그인 성공 시 access/refresh 토큰 발급 | Integration |
| REQ-F-002 | refresh 토큰으로 access 토큰을 갱신하며, 이미 사용된 refresh 토큰 재사용 시 해당 토큰 계열 전체를 폐기한다. | 재사용 시 401, 이후 같은 계열 토큰 모두 401 | Integration, Security |
| REQ-F-003 | Todo를 생성·조회·수정·삭제한다. | POST 201, GET 200, PATCH 200, DELETE 204, DB에 반영 | Integration, Contract |
| REQ-F-004 | Todo 목록을 커서 기반으로 페이지네이션하며 태그·소유자 정보를 포함한다. | limit 최대 100, 요청당 SQL 쿼리 3개 이하(N 무관) | Query count test |
| REQ-F-005 | Todo를 다른 사용자에게 read/write 권한으로 공유한다. | 권한 없는 사용자 접근 시 404(존재 은닉) | Authorization test |
| REQ-F-006 | POST 요청은 `Idempotency-Key` 헤더를 지원한다. | 같은 키 재요청 시 같은 응답, 중복 생성 없음 | Concurrency test |

### 8.2 비기능 요구사항

| ID | 요구사항 | 측정 기준 (로컬, api 2 vCPU / 512MB 제한) | 검증 |
|---|---|---|---|
| REQ-N-001 | 지연 시간 | 200 RPS 5분 지속 시 p95 < 200ms, p99 < 500ms | k6 load |
| REQ-N-002 | 오류율 | 위 부하에서 5xx 비율 < 0.1% | k6 load |
| REQ-N-003 | 한계점 식별 | stress로 p95가 1s를 넘는 지점(RPS)을 찾아 README에 기록 | k6 stress |
| REQ-N-004 | 메모리 안정성 | 30분 soak에서 워밍업 이후 RSS 증가 < 10%, OOM 0회 | soak + memray |
| REQ-N-005 | DB 효율 | 주요 조회 쿼리에 Seq Scan 없음(10만 행 기준), 커넥션 풀 고갈 시 503 + Retry-After | EXPLAIN, chaos |
| REQ-N-006 | 장애 격리 | Redis 장애 시 핵심 CRUD는 계속 동작(rate limit만 로컬 폴백) | toxiproxy |
| REQ-N-007 | 무중단 | SIGTERM 시 진행 중 요청 완료 후 종료(최대 20s), 롤링 재시작 중 실패 요청 0 | restart under load |
| REQ-N-008 | 보안 | CRITICAL/HIGH 스캔 결과 0, CWE 매트릭스 전 항목 판정 완료 | 9장 |

### 8.3 하네스 요구사항

| ID | 요구사항 | 수용 기준 |
|---|---|---|
| REQ-H-001 | Issue 하나로 전체 파이프라인을 실행한다. | `harness run --issue docs/issues/xxx.md`가 Verdict와 리포트를 생성 |
| REQ-H-002 | 모든 PASS에 Evidence가 있다. | 스키마 불변식 위반 시 파이프라인 ERROR |
| REQ-H-003 | LLM 장애가 파이프라인 전체를 멈추지 않는다. | 단일 에이전트 실패 시 재시도 후 해당 항목 ERROR, 나머지 검증은 계속 |
| REQ-H-004 | Self-Healing은 최대 3회, 금지 행위를 하지 않는다. | 금지 행위 탐지 테스트 통과, 3회 초과 시 Human 이관 |
| REQ-H-005 | MockLLM으로 전체 파이프라인을 결정론적으로 재현한다. | 같은 seed에서 Verdict가 동일 |
| REQ-H-006 | 실행 비용을 제한한다. | run당 토큰·시간 예산 초과 시 안전하게 중단하고 보고 |

---

## 09 보안 엔지니어링 (CWE Top 25)

정상 흐름, 비정상 흐름, 악성 흐름을 모두 검증한다. `docs/cwe-matrix.md`에 CWE별 판정을 관리하고, 해당 없음도 근거와 함께 명시한다. 최신 CWE Top 25 목록을 확인해 매트릭스를 갱신한다.

| CWE (대표) | 이 프로젝트 적용 | 방어 + 검증 |
|---|---|---|
| CWE-89 SQL Injection | 적용 | ORM 바인딩만 사용, raw SQL 금지 규칙(Semgrep). 페이로드 코퍼스로 모든 문자열 파라미터 공격 테스트. |
| CWE-79 XSS | 부분 적용 | API는 JSON만 반환, `Content-Type` 고정, 리포트 HTML 렌더링 시 이스케이프 테스트. |
| CWE-78 / 77 Command Injection | 적용 (Harness) | Tool Gateway는 `shell=False`, 명령 allowlist, 인자 배열 전달. 주입 시도 테스트. |
| CWE-22 Path Traversal | 적용 (Harness) | 모든 파일 접근을 작업 루트 기준 `resolve()` 후 prefix 검사, 심볼릭 링크 거부. |
| CWE-862 / 863 / 639 접근 제어, IDOR | 적용 | 모든 Todo 쿼리에 소유자/공유 조건 강제, 타 사용자 ID로 접근하는 테스트 전 엔드포인트 자동 생성. |
| CWE-287 / 306 인증 실패, 인증 누락 | 적용 | 라우트 목록을 순회해 인증 의존성 누락 탐지, 토큰 변조·만료·alg 혼동 테스트. |
| CWE-20 입력 검증 | 적용 | Pydantic 엄격 모드, 길이·범위 제한, Schemathesis fuzzing, Hypothesis 속성 테스트. |
| CWE-352 CSRF | N/A 후보 | 쿠키 인증을 쓰지 않고 Bearer 토큰만 쓰는 경우 N/A. 근거를 기록한다. |
| CWE-918 SSRF | 적용 (Harness) | 네트워크 도구는 도메인 allowlist, 사설 IP 대역 차단. |
| CWE-362 Race Condition | 적용 | Idempotency-Key 동시 요청, 공유 권한 동시 변경 테스트. DB 제약(unique)으로 최종 방어. |
| CWE-400 / 770 자원 고갈 | 적용 | 요청 본문 크기 제한, rate limit, 페이지 크기 상한, 대용량 페이로드 테스트. |
| CWE-502 역직렬화 | 적용 | pickle·yaml.load 금지(Semgrep), JSON만 사용. |
| CWE-798 하드코딩 자격증명 | 적용 | gitleaks pre-commit + CI. |
| CWE-209 / 532 오류·로그 정보 노출 | 적용 | 표준 오류 응답(RFC 9457 Problem Details), 스택트레이스 비노출, 로그 마스킹 테스트. |
| CWE-416 / 787 / 125 메모리 안전성 | N/A | 메모리 안전 언어(Python) 사용. 네이티브 확장 추가 시 재평가. |

### 9.1 LLM 고유 위협

| 위협 | 방어 + 검증 |
|---|---|
| Prompt Injection (코드·이슈·도구 출력 안의 지시문) | 외부 텍스트는 `<untrusted>` 구획으로 감싸 데이터로만 취급하도록 시스템 프롬프트에 명시. 행동 결정은 Tool Gateway 권한으로 최종 제한. `verification/security/prompt_injection/` 코퍼스로 회귀 테스트. |
| Invalid Agent Output | 스키마 검증 실패 시 1회 재요청 후 ERROR. 자유 텍스트를 실행하지 않는다. |
| Excessive Agency | 권한 매트릭스(13장), 보호 경로, 위험 작업 Human Approval. |
| Secret 유출 | LLM에 보내는 컨텍스트에서 `.env`, 키 파일 제외. 송신 전 secret 패턴 스캔. |

---

## 10 암호 정책

보안 기능에서 알고리즘을 임의로 고르지 않는다. 아래는 기본값이며, 변경하려면 ADR에 **왜 이 알고리즘·파라미터인지, 키가 어디 있는지, 어떻게 교체하는지**를 쓴다. 파라미터 값은 구현 시점의 OWASP Cheat Sheet와 대조해 확인한다.

| 대상 | 선택 | 이유와 운영 방법 |
|---|---|---|
| 비밀번호 해시 | Argon2id (`argon2-cffi`). OWASP 최소 권장(m=19 MiB, t=2, p=1) 이상으로 설정하고, 대상 환경에서 해시 1회 ≈ 0.2–0.5s가 되도록 벤치마크 후 결정 | 메모리 하드 함수로 GPU/ASIC 공격 비용이 높다. 파라미터는 해시 문자열에 저장되므로 로그인 시 `check_needs_rehash`로 점진적 상향. |
| Access Token | JWT, EdDSA(Ed25519), 만료 15분, `kid` 헤더 포함 | 비대칭 서명으로 검증 측에 서명키를 줄 필요가 없다. 허용 알고리즘을 고정해 `alg: none`/알고리즘 혼동을 차단한다. |
| Refresh Token | 256비트 CSPRNG 불투명 토큰, DB에는 SHA-256 해시만 저장, 회전 + 재사용 탐지 | DB 유출 시에도 원문 토큰을 쓸 수 없다. 재사용이 탐지되면 계열 전체 폐기(REQ-F-002). |
| 난수 | Python `secrets` 모듈 | `random` 사용 금지(Semgrep 규칙). |
| 저장 데이터 암호화 (필요 시) | AES-256-GCM, 레코드별 96비트 nonce, 봉투 암호화(DEK/KEK) | 인증 암호화로 변조를 탐지한다. KEK는 secret store에 두고 DEK만 데이터 옆에 암호화 상태로 저장한다. |
| 키 관리와 교체 | 로컬은 환경변수/Docker secret, 운영 가정은 KMS. JWKS에 현재+이전 키 공존 | `kid` 기반으로 새 키로 서명하고, 이전 키는 최대 토큰 수명 동안 검증용으로만 유지한 뒤 제거한다. 교체 절차를 RUNBOOK에 기록하고 테스트한다. |
| 전송 구간 | TLS 1.3 우선, 최소 1.2. 리버스 프록시에서 종료 | 로컬은 HTTP, 운영 가정 설정은 문서화한다. |

> **금지**
> MD5·SHA-1을 보안 목적으로 사용, ECB 모드, 고정 IV/nonce, 자체 제작 암호, 비밀번호 단순 해시(salt 없는 SHA-256 포함), HS256에 짧은 비밀키.

---

## 11 성능·DB·메모리 검증

### 11.1 N+1 쿼리 탐지

SQLAlchemy의 `before_cursor_execute` 이벤트로 요청별 쿼리 수를 세는 테스트 픽스처를 만든다. 데이터 개수 N을 바꿔도 쿼리 수가 일정해야 통과한다.

```python
@pytest.mark.req("REQ-F-004")
@pytest.mark.parametrize("n", [10, 100, 1000])
async def test_list_todos_query_count_is_constant(client, seed_todos, query_counter, n):
    await seed_todos(n, tags_per_todo=3)
    with query_counter() as qc:
        r = await client.get("/todos?limit=100")
    assert r.status_code == 200
    assert qc.count <= 3, qc.statements   # N과 무관해야 한다
```

개선 우선순위: `selectinload`/JOIN → 배치 조회 → 캐시. 캐시를 먼저 쓰지 않는 이유는 정합성 문제를 새로 만들기 때문이며, 선택 이유는 PR에 기록한다.

### 11.2 DB 병목

- 시드 스크립트로 사용자 1만, Todo 10만 행을 만들고 주요 쿼리를 `EXPLAIN (ANALYZE, BUFFERS)`로 확인한다. Seq Scan이면 인덱스를 추가하고 Before/After를 기록한다.
- `pg_stat_statements`로 부하 테스트 중 상위 쿼리를 수집한다.
- 커넥션 풀 크기를 의도적으로 줄여 고갈을 재현하고, 대기 타임아웃 후 503 + `Retry-After`를 반환하는지 확인한다.
- 동시 수정 시 락 대기와 데드락 여부를 테스트한다.

### 11.3 알고리즘 복잡도

Performance Reviewer는 루프 안 쿼리, 중첩 루프, 전체 로드 후 필터링 같은 패턴을 찾는다. 의심 코드는 N = 10², 10⁴, 10⁶에서 실행 시간을 측정해 증가 곡선으로 판단한다.

### 11.4 부하 테스트 단계 (k6)

| 단계 | 시나리오 | PASS 기준 (k6 thresholds) |
|---|---|---|
| smoke | 1 VU, 1분. 기능 경로 확인 | 오류 0 |
| load | 200 RPS, 5분. 읽기 70 / 쓰기 30 | p95<200ms, p99<500ms, 오류<0.1% |
| stress | 50 RPS씩 증가하며 한계 탐색 | 한계 RPS와 병목 원인 기록 (PASS/FAIL 대신 측정) |
| soak | 100 RPS, 30분 + 메모리 관찰 | REQ-N-004 |

측정 항목: throughput, p50/p95/p99, CPU, 메모리, DB 커넥션 수, 오류율. 결과 JSON은 `reports/<run_id>/load/`에 저장한다.

### 11.5 메모리와 OOM

- api 컨테이너에 `mem_limit: 512m`을 걸어 운영 제약을 흉내 낸다.
- soak 동안 10초 간격으로 RSS를 기록하고, 워밍업(5분) 이후 선형 회귀 기울기가 양수로 유지되면 **Potential Memory Leak**으로 판정한다.
- 의심 시 memray로 할당 위치를 찾고, 무제한 캐시·전역 리스트·닫히지 않은 세션을 우선 확인한다.
- 대용량 요청 본문, 대량 동시 요청에서 OOM 재시작이 없는지 확인한다.

### 11.6 규모 차이 극복

로컬 결과를 운영 성능으로 주장하지 않는다. 대신 **자원 제약(CPU·메모리·풀 크기)을 걸고 한계점과 병목 원인을 찾는 것**을 목표로 하며, README의 Known Limitations에 측정 환경과 외삽의 한계를 명시한다.

---

## 12 장애 격리와 복원력

모든 외부 의존성은 실패한다고 가정한다. 각 의존성에 대해 아래 정책을 코드로 구현하고 Toxiproxy 시나리오로 증명한다.

| 의존성 | 정책 | 장애 시 기대 동작 (테스트로 증명) |
|---|---|---|
| LLM API | 타임아웃 60s, 지수 백오프+지터 재시도 3회(429/5xx만), 서킷 브레이커 | 해당 에이전트만 ERROR, 나머지 결정론적 검증은 계속. 회로 열림 시 즉시 실패로 비용 낭비 방지. |
| PostgreSQL | 쿼리 타임아웃 2s, 풀 대기 타임아웃, readiness 연동 | DB 끊김 시 `/readyz` 503, 복구 후 자동 정상화. 쓰기 실패는 재시도하지 않고 오류 반환(멱등 아님). |
| Redis | 타임아웃 100ms, 실패 시 우회 | rate limit은 프로세스 로컬 토큰 버킷으로 폴백, CRUD는 정상(REQ-N-006). |
| Tool 실행 | 도구별 타임아웃, 출력 크기 제한 | hang 도구 강제 종료, 해당 Check는 ERROR로 기록. |
| 파일 시스템 | 작업 디렉터리 격리 | 쓰기 실패 시 run 중단, 부분 결과 보존. |

### 12.1 무중단 운영 시뮬레이션

```
배포(새 이미지) ─▶ readiness 통과 전 트래픽 없음 ─▶ readiness OK ─▶ 구 인스턴스 SIGTERM
                                                                      │
                    연결 drain, 진행 중 요청 완료(≤20s) ◀──────────────┘
헬스체크 FAIL ─▶ 트래픽 차단 ─▶ 이전 이미지로 롤백 ─▶ 재검증
```

- `/healthz` (liveness: 프로세스 생존), `/readyz` (readiness: DB 연결과 마이그레이션 버전 확인)를 분리한다.
- load 부하를 거는 동안 api 2개 인스턴스를 순차 재시작하고 실패 요청 수를 측정한다(REQ-N-007).
- 마이그레이션은 expand → migrate → contract 순서의 하위 호환 방식으로 작성한다.
- 롤백 스크립트(`make rollback`)를 만들고 의도적으로 깨진 이미지로 실행해 본다.

---

## 13 AI 출력 통제와 가드레일

### 13.1 도구 권한 매트릭스 (`harness/policies/permissions.yaml`)

| Agent | Read | Write | Execute | Delete | Network | Git | Deploy |
|---|---|---|---|---|---|---|---|
| Requirement / Architecture / Reviewers | ✔ | ✘ | ✘ (보안·성능·신뢰성은 검사 도구만) | ✘ | ✘ | ✘ | ✘ |
| Implementation | ✔ | ✔ (보호 경로 제외) | ✔ 테스트·린트 | ✘ | ✘ | branch/commit | ✘ |
| Test Engineer | ✔ | tests/ 신규 파일만 | ✔ 테스트 | ✘ | ✘ | commit | ✘ |
| Validation | ✔ | reports/만 | ✔ 검사 도구 | ✘ | ✘ | ✘ | ✘ |
| Self-Healing | ✔ | ✘ (계획만) | ✘ | ✘ | ✘ | ✘ | ✘ |
| Production Deploy | **Human Approval 필수** | | | | | | |

보호 경로: `services/*/tests/`의 기존 파일, `verification/`, `harness/policies/`, `.github/workflows/`, k6 thresholds. 권한 밖 요청은 Tool Gateway가 차단하고 감사 로그에 남긴다. 차단 동작 자체를 테스트한다.

### 13.2 비결정론 통제

- 모든 LLM 출력은 Pydantic 스키마로 검증한다. 자유 텍스트를 코드 경로에 그대로 쓰지 않는다.
- 판정에 영향을 주는 LLM 단계(예: Security Reviewer)는 N=3회 반복 실행해 Finding을 합집합으로 모으고 반복 간 일치율을 기록한다.
- MockLLMProvider에 녹화된 응답(golden)을 두고, 파이프라인 회귀 테스트는 실제 API 없이 실행한다.
- 불변식 검사: "PASS면 evidence 존재", "HIGH Finding이 있으면 BLOCK" 같은 규칙을 Hypothesis로 무작위 입력에 대해 검증한다.

### 13.3 예산과 중단

run마다 최대 토큰, 최대 시간, 에이전트별 최대 호출 수를 설정한다. 예산을 넘으면 현재 상태를 저장하고 `BUDGET_EXCEEDED`로 보고한다. 무한 루프를 막기 위해 같은 FixPlan이 반복되면 즉시 Human으로 이관한다.

---

## 14 Self-Healing 루프

```
Validation ─▶ PASS ─▶ Report
    │
   FAIL
    ▼
Failure Analysis (Self-Healing Agent: 로그·diff·Evidence만 입력)
    ▼
Root Cause + FixPlan ──(동일 FixPlan 반복?)──▶ Human
    ▼
Implementation Agent (수정) ─▶ Forbidden-Action Guard ─▶ Test ─▶ Validation
    ▼
FAIL이면 attempt += 1 ─▶ attempt > 3 이면 Human 이관 (진단 리포트 첨부)
```

### 14.1 금지 행위와 기계적 차단

| 금지 행위 | 탐지 방법 (Forbidden-Action Guard) |
|---|---|
| 테스트 삭제·이름 변경 | 수정 전후 수집된 테스트 ID 집합 비교. 줄어들면 차단. |
| assertion 제거·완화 | 테스트 파일 diff에서 `assert` 삭제, 비교 연산 완화, 숫자 임계값 증가 탐지. |
| skip/xfail 추가 | diff에서 `pytest.mark.skip`, `xfail`, `pytest.skip(` 추가 탐지. |
| 검증·보안 우회 | 보호 경로 변경 탐지, `# nosec`, `# noqa`, `# type: ignore`, `nosemgrep` 추가 탐지. |
| 오류 무시 | `except Exception: pass` 등 Semgrep 규칙. |
| 요구사항 변경으로 PASS | `docs/requirements.md`, thresholds 파일 변경 탐지. |

테스트가 잘못됐다고 판단되면 Self-Healing은 수정하지 않고 `TEST_REVIEW` Finding을 만들어 사람에게 넘긴다. Guard 자체도 "금지 행위를 담은 가짜 diff"로 테스트한다.

---

## 15 관측성

**Target Service**
- JSON 구조 로그(structlog), request_id·trace_id 포함
- Prometheus 메트릭: 요청 수, 지연 히스토그램, 오류율, DB 풀 사용량, 쿼리 수
- OpenTelemetry trace: HTTP → DB 구간
- 헬스체크 `/healthz`, `/readyz`

**Harness**
- run_id 단위 실행 이력(JSONL): 어떤 Agent, 어떤 프롬프트 버전, 어떤 Tool, 어떤 결정, 어떤 실패, 어떤 수리
- 토큰 사용량, 지연, 도구 호출 수, 재시도 수, 수리 횟수
- Tool Gateway 감사 로그(허용·차단)

> **로그 금지 항목**
> 비밀번호, 토큰, API 키, 개인정보 원문, LLM에 보낸 전체 소스 코드. 마스킹 필터를 두고, 마스킹이 동작하는지 테스트한다.

---

## 16 GitFlow와 AI PR 리뷰

```
main ─────────────●──────────────●────────────  (보호 브랜치: PR + CI 통과 + 사람 승인 1)
                  ▲              ▲
feature/REQ-F-003 ┘  perf/n-plus-one-todos ┘   fix/...   security/...
```

### 16.1 흐름

Issue → feature 브랜치 → 구현 + 테스트 → `make verify` → PR 생성 → CI(lint, type, test, security) → AI PR Review → Security Review → Human Review → squash merge.

### 16.2 AI PR Reviewer (`.github/workflows/ai-pr-review.yml`)

- 입력: 변경 파일, diff, CI 결과, 관련 요구사항. 출력: Finding 목록과 판정 `PASS` / `REQUEST_CHANGES` / `BLOCK`.
- 판정 규칙은 7장의 불변식을 그대로 사용한다. CI가 실패하면 LLM 판정과 무관하게 BLOCK이다.
- 리뷰 결과를 PR 코멘트로 남기고, BLOCK이면 status check를 실패로 설정한다.
- API 키는 GitHub Secrets에 두고, fork에서 온 PR에는 실행하지 않는다(비밀 유출 방지).

### 16.3 CI 파이프라인

| Job | 내용 | 실행 시점 |
|---|---|---|
| verify | ruff, mypy --strict, import-linter, pytest(unit+integration, 커버리지 ≥ 85%) | 모든 PR |
| security | semgrep, bandit, pip-audit, gitleaks, trivy | 모든 PR |
| contract | OpenAPI diff, Schemathesis fuzz | 모든 PR |
| guard | Forbidden-Action Guard (테스트 수, assertion, skip, 보호 경로) | 모든 PR |
| ai-review | AI PR Reviewer | 모든 PR |
| load-nightly | k6 smoke + load, 결과 아티팩트 업로드 | 야간 / 수동 |

---

## 17 마일스톤 (Phase 0–8)

각 Phase는 별도 브랜치와 PR로 진행한다. Exit Criteria를 Evidence와 함께 충족해야 다음 Phase로 넘어간다.

| Phase | 작업 | Exit Criteria |
|---|---|---|
| **0** 분석·부트스트랩 | 저장소 분석(R4). 비어 있으면 4장 구조 생성, uv 프로젝트, Makefile, docker-compose, pre-commit, CLAUDE.md, CI 골격, `docs/progress.md` | `make verify`가 빈 프로젝트에서 성공, `docker compose up`으로 postgres·redis 기동, CI 녹색 |
| **1** 요구사항·설계 | `docs/requirements.md`(8장), `docs/domain-boundaries.md`, ARCHITECTURE.md, ADR-0001(스택), ADR-0002(오케스트레이터), ADR-0003(암호 정책) | 모든 REQ에 검증 방법 존재, 도메인 경계 import 규칙 설정 |
| **2** Target Service | Auth, Users, Todos, Tags, Sharing 구현. Alembic, 표준 오류 응답, 헬스체크, 구조 로그. 단위·통합·계약 테스트 | REQ-F-001~006 테스트 통과, 커버리지 ≥ 85%, IDOR 테스트 전 엔드포인트 통과 |
| **3** 보안 하네스 | 보안 스캐너 CI, CWE 매트릭스, 공격 페이로드 테스트, Schemathesis, 토큰 공격 테스트, 로그 마스킹 | CRITICAL/HIGH 0, CWE 매트릭스 전 항목 판정, Evidence 경로 기록 |
| **4** 성능·DB·메모리 | 쿼리 카운터 픽스처, 시드 스크립트, EXPLAIN 점검, k6 4단계, soak + memray. **일부러 N+1을 남긴 상태에서 측정 → 수정 → 재측정** | REQ-N-001~005 충족, N+1 Before/After 수치와 PR 기록 |
| **5** 장애 격리·무중단 | 타임아웃·재시도·서킷 브레이커, Redis 폴백, graceful shutdown, 롤링 재시작 스크립트, 롤백, Toxiproxy 시나리오 | REQ-N-006, 007 충족, chaos 리포트, RUNBOOK 작성 |
| **6** Harness 코어 | 스키마(7장), LLMProvider(Anthropic + Mock), Tool Gateway와 권한, Checkers, Orchestrator 상태 머신, Evidence Store, 리포트 렌더러, CLI | REQ-H-001, 002, 003, 005, 006 충족. MockLLM으로 E2E run 재현 가능 |
| **7** 에이전트·Self-Healing | 6장의 에이전트와 프롬프트, Forbidden-Action Guard, Self-Healing 루프, prompt injection 코퍼스 | REQ-H-004 충족. 버그를 심은 Issue로 run 시 탐지 → 수리 → 재검증 성공 사례 1개 이상, 수리 실패 → Human 이관 사례 1개 이상 |
| **8** PR 리뷰어·문서화 | AI PR Review 워크플로, PR 템플릿, README(19장), 최종 Verification Matrix 리포트 | 18장 완료 조건 전부 충족, 최종 리포트 생성 |

> **포트폴리오 관점의 핵심 장면**
> Phase 4와 7의 "문제를 일부러 재현하고, 측정하고, 고치고, 다시 측정한" 기록이 이 프로젝트에서 가장 설득력 있는 증거다. Before/After 수치와 선택하지 않은 대안을 반드시 남긴다.

---

## 18 Verification Matrix와 완료 조건

| Category | Evidence (필수) | 판정 기준 |
|---|---|---|
| Requirement | REQ-ID ↔ 테스트 추적표, pytest 결과 | 모든 REQ에 통과한 테스트 존재 |
| Architecture | import-linter 결과, ADR, Architecture Review Finding | 경계 위반 0 |
| Code Quality | ruff, mypy 출력 | 오류 0 |
| Security | semgrep, bandit, pip-audit, gitleaks, trivy, 공격 테스트, CWE 매트릭스 | CRITICAL/HIGH 0 |
| Performance | k6 JSON, p50/p95/p99 | REQ-N-001~003 |
| Memory | RSS 시계열, memray 리포트 | REQ-N-004 |
| Database | 쿼리 카운트 테스트, EXPLAIN 결과, pg_stat_statements | REQ-F-004, REQ-N-005 |
| Reliability | chaos 시나리오 결과, 롤링 재시작 결과 | REQ-N-006, 007 |
| AI Control | 스키마 검증 테스트, 반복 일치율, prompt injection 결과, 권한 차단 테스트 | REQ-H-002~006 |
| Regression / E2E | CI 실행 링크, E2E 테스트 | 전부 통과 |
| Documentation | README, RUNBOOK, ADR, PR 기록 | 19장 항목 모두 존재 |

### 18.1 최종 완료 조건 (하나라도 실패하면 COMPLETE ❌)

- [ ] Requirement 검증
- [ ] Domain Boundary 검증
- [ ] Architecture 검증
- [ ] Existing System 충돌 검증
- [ ] Code Review
- [ ] Security Review
- [ ] CWE 기반 검증
- [ ] Edge Case 검증
- [ ] Unit Test
- [ ] Integration Test
- [ ] E2E Test
- [ ] Regression Test
- [ ] Load Test
- [ ] Performance 검증
- [ ] Memory 검증
- [ ] Database 병목 검증
- [ ] 장애 격리 검증
- [ ] Recovery 검증
- [ ] Observability 검증
- [ ] AI Output Schema 검증
- [ ] Prompt Injection 검증
- [ ] Tool 권한 검증
- [ ] Self-Healing 검증
- [ ] Git/PR 검증
- [ ] README 문서화

### 18.2 엣지 케이스 체크리스트 (모든 입력 엔드포인트)

Empty · Null · Huge · Malformed JSON · Unexpected Type · Boundary Value(0, -1, max, max+1) · Unicode/이모지 · Concurrent Request · Duplicate Request · Timeout · Partial Failure · Network Failure · Database Failure

---

## 19 README·PR 문서화 규격

### 19.1 README 목차 (고정)

1. **Problem**: 어떤 문제를 풀고, 왜 중요한가
2. **Architecture**: 다이어그램과 구성 요소, 도메인 경계
3. **Design Decisions & Trade-offs**: ADR 요약, 선택하지 않은 대안
4. **Security**: 위협 모델, CWE 매트릭스 요약, 암호 정책
5. **Performance**: 측정 환경, 부하 결과, 한계 RPS, 병목과 개선 Before/After
6. **Failure Scenarios**: LLM 장애, DB 장애, 네트워크 타임아웃, 메모리 고갈, 고부하, 잘못된 에이전트 출력, prompt injection, 도구 실패, 인증 실패, 배포 실패 각각의 탐지 → 격리 → 복구 → 검증
7. **Testing**: 테스트 계층, 실행 방법, 커버리지
8. **Verification Report**: 최신 Matrix와 Evidence 링크
9. **Known Limitations**: 로컬 측정의 한계, 미검증 항목
10. **Quick Start / Recovery**: 실행, 롤백, 키 교체 절차

### 19.2 PR 본문 템플릿 (`.github/pull_request_template.md`)

```markdown
## Problem
## Root Cause
## Decision
## Alternatives Considered (and why not)
## Risk / Impact (API·Schema·Auth·Config 영향)
## Verification
- 실행한 명령:
- Before:
- After:
## Requirements
- REQ-...
## Checklist
- [ ] make verify 통과   - [ ] 테스트 삭제·완화 없음   - [ ] 비밀 정보 없음
```

### 19.3 작성 예

```
Problem:     GET /todos 지연 p95 840ms (1000 Todo, 태그 3개씩)
Root Cause:  Todo마다 태그·소유자를 개별 조회 → 요청당 2001 쿼리
Decision:    selectinload로 태그·소유자 일괄 로딩
Alternative: Redis 캐시 → 쓰기 시 무효화 정합성 문제가 새로 생겨 보류
Verification: test_list_todos_query_count_is_constant, k6 load
Before: 2001 queries / p95 840ms    After: 3 queries / p95 61ms
```

---

## A 부록 A. CLAUDE.md 초안

저장소 루트에 그대로 저장한다. Claude Code는 이 파일을 매 세션 자동으로 읽는다. (저장소 루트의 `CLAUDE.md` 참조)

## B 부록 B. Claude Code 첫 실행 프롬프트

이 PDF 내용을 `docs/SPEC.md`로 저장소에 넣은 뒤, Claude Code 첫 메시지로 아래를 붙여 넣는다.

```
docs/SPEC.md는 이 프로젝트의 개발 기획서이고 Source of Truth다.
00장(작업 규칙)과 17장(마일스톤)을 먼저 읽어라.

이번 작업은 Phase 0만 수행한다.

1. 저장소 분석
   - 현재 파일 구조, 기존 README/CLAUDE.md/CI/docker-compose/스키마/테스트를 확인하고
     발견한 내용을 docs/progress.md의 "Phase 0 분석"에 요약하라.
   - 기존 규칙이 SPEC과 충돌하면 구현하지 말고 충돌 목록을 먼저 보고하라.

2. 부트스트랩 (저장소가 비어 있거나 골격이 없을 때)
   - SPEC 4장 디렉터리 구조 생성
   - uv 프로젝트, ruff/mypy/pytest/import-linter 설정, pre-commit(gitleaks 포함)
   - Makefile: verify, security, test, load, chaos, report 타깃 (아직 없는 것은 TODO로 명확히 실패)
   - docker-compose.yml: postgres 16, redis 7, toxiproxy (api는 Phase 2에서 추가)
   - .env.example, .gitignore(reports/, .env)
   - 부록 A의 CLAUDE.md 저장
   - .github/workflows/ci.yml 골격 (verify + security)
   - docs/progress.md, docs/backlog.md, docs/adr/0001-tech-stack.md

3. 검증 (Exit Criteria)
   - make verify 실행 결과
   - docker compose up -d 후 postgres/redis 헬스 확인 결과
   - 실행한 명령과 출력 요약을 progress.md에 Evidence로 남겨라.

4. 브랜치 feature/phase-0-bootstrap에서 작업하고 커밋하라. main에 직접 커밋하지 마라.

완료 후 다음 형식으로 보고하라:
- 한 일 / Evidence(명령, 결과) / NOT_VERIFIED 항목과 이유 / Phase 1에서 할 일
Phase 1은 내가 승인한 뒤에 시작한다.
```

### B.1 이후 Phase 진행 프롬프트 형식

```
docs/SPEC.md와 docs/progress.md를 다시 읽어라.
Phase N을 시작한다. 범위는 SPEC 17장의 Phase N 행이다.
Exit Criteria를 모두 Evidence와 함께 충족한 뒤 PR을 만들고,
PR 본문은 SPEC 19.2 템플릿을 따르라. 범위 밖 아이디어는 backlog.md로.
```

## C 부록 C. 템플릿 모음

### C.1 ADR (`docs/adr/NNNN-title.md`)

```
# NNNN. 제목
Status: Proposed | Accepted | Superseded by NNNN
Context: 어떤 문제와 제약이 있었나
Decision: 무엇을 선택했나
Alternatives: 무엇을 검토했고 왜 선택하지 않았나
Consequences: 얻는 것, 잃는 것, 새로 생기는 리스크
Verification: 이 결정이 맞았는지 무엇으로 확인하나
```

### C.2 Issue (하네스 입력, `docs/issues/*.md`)

```
# 제목
## 요청
## 관련 REQ
## 제약 (성능 기준, 보안 요구, 호환성)
## 완료 정의
```

### C.3 docs/progress.md

```
# Progress
## 현재 Phase: N  (브랜치: ...)
## 완료
- [날짜] 작업 — Evidence: reports/..., 명령: ...
## 열린 Finding
- F-XXX-0001 (severity) 제목 — 상태
## NOT_VERIFIED
- 항목 — 이유
## 다음 할 일
```

### C.4 Failure Scenario 기록 (README 6장 각 항목)

```
### 시나리오: Redis 장애
Detection:    redis 호출 타임아웃(100ms), 메트릭 redis_errors_total 증가
Isolation:    rate limit만 로컬 토큰 버킷으로 폴백, CRUD 영향 없음
Recovery:     연결 재시도(백오프), 복구 시 자동 원복
Verification: make chaos SCENARIO=redis_down → CRUD 성공률 100%, 5xx 0
Evidence:     reports/<run_id>/chaos/redis_down.json
```

> **최종 철학**
> AI가 코드를 만든다 → Harness가 의심한다 → Validator가 검증한다 → Security가 공격한다 → Load Test가 압박한다 → Failure Test가 깨뜨린다 → Self-Healing이 수정한다 → 다시 검증한다 → Evidence를 남긴다 → **사람이 책임질 수 있는 결과가 된다.**
