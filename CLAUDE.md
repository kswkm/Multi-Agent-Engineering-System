# CLAUDE.md — Multi-Agent Engineering System

## Source of Truth
- 개발 기획서: docs/SPEC.md (이 PDF의 내용). 충돌 시 SPEC이 우선한다.
- 진행 상황: docs/progress.md — 작업 시작 전 반드시 읽고, 끝나면 갱신한다.
- 공통 작업 지침: docs/WORKING-GUIDELINES.md (구현·테스트·최종 검증·보고 방법).

## 절대 규칙
1. 실행 결과만 Evidence다. "해결했다"고 쓰기 전에 명령을 실행하고 수치를 남긴다.
2. 검사하지 않은 것은 NOT_VERIFIED로 적는다. 해당 없음은 NOT_APPLICABLE + 사유.
3. 테스트 삭제/assertion 제거/skip 추가/임계값 완화/요구사항 변경 금지.
   테스트가 틀렸다고 생각되면 멈추고 TEST_REVIEW로 나에게 묻는다.
4. main에 직접 커밋 금지. feature/ fix/ security/ perf/ 브랜치 + PR.
5. 비밀값은 .env(커밋 금지)와 환경변수로만. 로그에 토큰/비밀번호 금지.
6. 현재 Phase 범위 밖 작업은 docs/backlog.md에 적고 하지 않는다.
7. 파괴적 DB 변경, 데이터 삭제, 배포, 보호 경로 수정은 사람 승인 후.

## 명령
- make verify      # ruff + mypy --strict + import-linter + pytest
- make security    # semgrep, bandit, pip-audit, gitleaks
- make load STAGE=smoke|load|stress|soak
- make chaos SCENARIO=db_down|redis_down|llm_timeout
- make report      # reports/<run_id>/ 에 Verification Matrix 생성

## 코드 규칙
- Python 3.12, 타입 힌트 필수, mypy --strict 통과
- 도메인 간 직접 import 금지 (services/todo-api/app/domains/*) — 서비스 인터페이스 경유
- raw SQL 금지, ORM 바인딩만. pickle/yaml.load/random(보안 용도) 금지
- 모든 외부 호출에 timeout 명시
- 오류 응답은 RFC 9457 Problem Details
- 테스트에 REQ-ID 마커: @pytest.mark.req("REQ-F-003")

## 보호 경로 (수정 시 사람 승인)
services/*/tests/ 기존 파일, verification/, harness/policies/,
.github/workflows/, verification/load/thresholds.*

## 작업 종료 체크
- [ ] make verify 결과 첨부   - [ ] progress.md 갱신
- [ ] 중요한 결정은 docs/adr/ 에 기록   - [ ] Conventional Commit
