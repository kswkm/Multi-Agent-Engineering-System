# Backlog

현재 Phase 범위 밖이라 하지 않은 일(SPEC R7). 각 항목에 해당 Phase를 적는다.

| 항목 | 이유 / 출처 | Phase |
|---|---|---|
| Trivy 이미지 스캔을 `make security`와 CI에 추가 | 스캔할 컨테이너 이미지(api)가 Phase 2에 생긴다. SPEC 16.3 | 2–3 |
| semgrep 버전 고정 + 프로젝트 규칙(raw SQL, `random`, `pickle`/`yaml.load`, `except Exception: pass`) | 지금은 `uv tool run semgrep` 최신판 + `p/python`. SPEC 9, 10, 14.1 | 3 |
| docker-compose에 api(mem_limit 512m, 2 vCPU) 추가 | SPEC 8.2, 11.5. Phase 0 프롬프트가 api를 Phase 2로 지정 | 2 |
| docker-compose에 prometheus(+Grafana 선택) 추가 | SPEC 4, 15 | 관측성 작업 시 |
| toxiproxy 프록시 정의(postgres, redis, LLM 경로) | SPEC 12 chaos 시나리오 | 5 |
| CI job: contract, guard, ai-review, load-nightly, security.yml 분리 | SPEC 16.3. Phase 0은 verify + security 골격만 | 3, 7, 8 |
| AGENTS.md, ARCHITECTURE.md, SECURITY.md, TESTING.md, RUNBOOK.md | 내용이 생기는 Phase에 쓴다(빈 껍데기 문서를 만들지 않음) | 1, 3, 5, 8 |
| services/todo-api를 import-linter 대상에 추가하고 도메인 경계 계약 작성 | SPEC 5. 패키지가 생겨야 계약을 검사할 수 있다 | 1–2 |
| main 브랜치 보호 규칙(PR + CI 통과 + 승인 1) | SPEC 16. GitHub 저장소 설정 작업이라 사람 권한 필요 | 첫 PR 전 |
