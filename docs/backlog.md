# Backlog

현재 Phase 범위 밖이라 하지 않은 일(SPEC R7). 각 항목에 해당 Phase를 적는다.

| 항목 | 이유 / 출처 | Phase |
|---|---|---|
| Trivy 이미지 스캔을 `make security`와 CI에 추가 | 스캔할 컨테이너 이미지(api)가 Phase 2에 생긴다. SPEC 16.3 | 2–3 |
| semgrep 버전 고정 + 프로젝트 규칙(raw SQL, `random`, `pickle`/`yaml.load`, `except Exception: pass`, 금지 암호) | 지금은 `uv tool run semgrep` 최신판 + `p/python`. SPEC 9, 10, 14.1. `random` 규칙은 하네스 seed 모듈만 예외(ADR-0002 규칙 6) | 3 |
| docker-compose에 api(mem_limit 512m, 2 vCPU) 추가 | SPEC 8.2, 11.5. Phase 0 프롬프트가 api를 Phase 2로 지정 | 2 |
| docker-compose에 prometheus(+Grafana 선택) 추가 | SPEC 4, 15 | 관측성 작업 시 |
| toxiproxy 프록시 정의(postgres, redis, LLM 경로) | SPEC 12 chaos 시나리오 | 5 |
| CI job: contract, guard, ai-review, load-nightly, security.yml 분리 | SPEC 16.3. Phase 0은 verify + security 골격만 | 3, 7, 8 |
| 새 CI job(contract, guard, ai-review)을 main 보호 규칙의 필수 체크에 추가 | 현재 필수 체크는 verify, security뿐. SPEC 16.3 | 3, 7, 8 |
| SECURITY.md, TESTING.md, RUNBOOK.md | 내용이 생기는 Phase에 쓴다(빈 껍데기 문서를 만들지 않음) | 2, 3, 5 |
| AGENTS.md (에이전트 역할·권한 요약) | 에이전트와 `permissions.yaml`이 생기는 Phase에 쓴다. SPEC 4, 6 | 7 |
| `router` 모듈은 `app.main`만 import하는 protected 계약 | router 모듈이 Phase 2에 생긴다. 없는 모듈을 가리키는 계약은 아무것도 검사하지 않는다(domain-boundaries 7) | 2 |
| Argon2id 벤치마크 스크립트를 `verification/`에 두고 실제 api 이미지로 재측정 | ADR-0003 잠정 파라미터 확정. `verification/`은 보호 경로라 추가 시 오너 승인 필요 | 2 |
| api 2개 인스턴스 앞 로드밸런서 선택(ADR) | REQ-N-007.2 롤링 재시작. SPEC 3 스택에 없음 | 5 |
| AI PR Reviewer 도입 | 외부 API 키가 필요하므로 오너 승인 후(WORKING-GUIDELINES v2 14.3, 20) | 8 |
