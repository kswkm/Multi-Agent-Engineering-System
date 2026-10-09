# 0002. 오케스트레이터: 직접 구현한 asyncio 명시적 상태 머신

Status: Accepted (Phase 1 설계). 구현과 검증은 Phase 6.

## Context

하네스는 Requirement → Context → Architecture → Implementation → 병렬 검증 → Validation → (Self-Healing ↺) → Report 흐름을 실행한다(SPEC 2). 이 흐름에는 다음이 **테스트로 증명 가능**해야 한다.

- 상태 전이가 허용된 경로로만 일어난다(Self-Healing은 최대 3회, 같은 FixPlan 반복 시 Human, SPEC 14).
- 단일 에이전트 실패가 다른 검증을 멈추지 않는다(REQ-H-003).
- 같은 seed + MockLLM이면 같은 Verdict가 나온다(REQ-H-005).
- 토큰·시간·호출 예산을 넘으면 상태를 저장하고 `BUDGET_EXCEEDED`로 끝난다(REQ-H-006).
- 모든 전이가 run_id 단위 JSONL에 남는다(SPEC 15).

SPEC 3은 "직접 구현한 asyncio 상태 머신"을 기본으로 정하고, 프레임워크를 도입하려면 ADR을 쓰라고 한다.

## Decision

`harness/orchestrator/`에 **표로 정의된 상태 머신**을 직접 구현한다.

### 상태

```
PENDING → REQUIREMENTS → CONTEXT → ARCHITECTURE → IMPLEMENTATION → VERIFYING → VALIDATING
VALIDATING ─PASS→ REPORTING → DONE
VALIDATING ─FAIL→ HEALING → IMPLEMENTATION          (attempt += 1)
HEALING ─(attempt > 3 | 같은 FixPlan | TEST_REVIEW)→ ESCALATED_TO_HUMAN
* ─(예산 초과)→ BUDGET_EXCEEDED          * ─(불변식 위반·복구 불가 오류)→ ERROR
```

종료 상태: `DONE`, `ESCALATED_TO_HUMAN`, `BUDGET_EXCEEDED`, `ERROR`. 종료 상태에서도 `reports/<run_id>/`에 지금까지의 Evidence와 진단을 남긴다.

### 설계 규칙

1. **전이 표가 유일한 진실**이다. `TRANSITIONS: dict[State, set[State]]`에 없는 전이는 예외를 던진다. 테스트는 이 표를 전수 검사한다(허용 전이는 모두 가능, 그 외는 모두 거부).
2. **상태 핸들러는 순수에 가깝게** 만든다. 핸들러는 `(RunContext) -> Outcome`을 반환하고, 다음 상태 결정은 러너가 표에 따라 한다. 핸들러가 직접 상태를 바꾸지 않는다.
3. **VERIFYING은 `asyncio.TaskGroup`이 아니라 개별 태스크 + 결과 수집**으로 실행한다. TaskGroup은 하나가 실패하면 나머지를 취소하는데, 이것은 REQ-H-003과 반대다. 각 검증 태스크는 자기 예외를 `CheckResult(status=ERROR, reason=...)`로 바꿔 반환한다.
4. **타임아웃·재시도·서킷 브레이커는 LLM 호출 계층(`harness.llm`)에** 둔다. 정책: 60s, 429/5xx만 3회, 지수 백오프+지터(SPEC 12). 상태 머신은 결과만 본다.
5. **예산(`budget.py`)은 전이마다 검사**한다. 토큰은 LLMProvider가 보고한 사용량, 시간은 단조 시계(`time.monotonic`), 호출 수는 에이전트별 카운터로 잰다. 초과하면 다음 핸들러를 시작하지 않는다.
6. **결정론**: 무작위성은 run seed로 만든 `random.Random(seed)` 하나만 쓴다(재시도 지터 포함). 보안 목적이 아니라 재현 목적이므로 SPEC 10의 `random` 금지 대상이 아니다. Semgrep 규칙은 이 모듈만 예외로 둔다(Phase 3). 시각은 주입 가능한 clock으로 받는다. Verdict 비교에서는 run_id·시각을 뺀다(requirements.md A-4).
7. **영속화**: 전이마다 `reports/<run_id>/run.jsonl`에 한 줄씩 append한다(상태, 에이전트, 프롬프트 버전, 도구 호출, 결정, 실패, 수리). 쓰기 실패 시 run을 중단한다(SPEC 12 파일 시스템).

## Alternatives

| 대안 | 고르지 않은 이유 |
|---|---|
| LangGraph | 그래프·체크포인트·재시도가 프레임워크 내부에 있어 "허용 전이만 일어난다"를 우리 테스트로 직접 증명하기 어렵다. 의존성과 업데이트 주기가 커서 결정론 재현(REQ-H-005)의 변수가 늘어난다. |
| CrewAI / AutoGen | 에이전트 간 자유 대화가 기본 모델이다. SPEC 6.1 독립성 규칙(검증자는 diff와 실행 결과만 받는다)과 맞지 않고, 대화 흐름이 비결정적이다. |
| Temporal / Prefect | 내구성 있는 워크플로에는 강하지만 별도 서버(또는 클라우드)가 필요하다. 이 프로젝트의 run은 로컬에서 분 단위로 끝나고, 필요한 영속성은 JSONL로 충분하다(SPEC 1.3 비목표: 범용 프레임워크). |
| `transitions` 같은 FSM 라이브러리 | 상태 수가 적어(13개) 라이브러리 이점이 작다. 비동기 핸들러·예산·이력 기록을 결국 우리가 감싸야 한다. |

## Consequences

- 얻는 것: 전이 표, 예산, 재시도를 모두 우리 단위 테스트로 증명할 수 있다. 외부 서비스 없이 CI에서 E2E를 MockLLM으로 재현할 수 있다.
- 잃는 것: 체크포인트에서의 재개(resume), 시각화 도구를 직접 만들어야 한다. 재개는 SPEC 범위가 아니므로 만들지 않는다(필요하면 backlog).
- 리스크: 상태 머신 코드의 버그가 곧 하네스의 버그다. 이를 막기 위해 전이 표 전수 테스트와 Hypothesis 기반 무작위 Outcome 시퀀스 테스트를 둔다.

## Verification (Phase 6)

- 전이 표 전수 테스트: 허용 전이 성공, 그 외 모든 (상태, 상태) 쌍 거부.
- Hypothesis: 무작위 Outcome 시퀀스에서 항상 종료 상태에 도달하고, HEALING 진입 횟수 ≤ 3, 같은 FixPlan 두 번이면 ESCALATED_TO_HUMAN.
- 장애 주입: 검증 에이전트 하나가 예외·타임아웃이면 그 CheckResult만 ERROR, 나머지는 결과를 냄(REQ-H-003).
- 같은 seed 두 번 실행 → 정규화된 Verdict 동일(REQ-H-005).
- 예산을 아주 작게 둔 run → `BUDGET_EXCEEDED` + run.jsonl에 마지막 상태 기록(REQ-H-006).
