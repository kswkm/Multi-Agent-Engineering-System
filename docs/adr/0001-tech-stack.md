# 0001. 기술 스택과 로컬 툴체인

Status: Accepted (Phase 0). Phase 1에서 재검토하며, 바뀌면 이 ADR을 Superseded 처리한다.

## Context

저장소가 비어 있었다(커밋 0개, 파일 없음). SPEC 3장은 빈 저장소일 때 쓸 스택을 정한다. 개발 머신은 Windows 11이고, 시스템 Python은 3.13뿐이며 uv, make, gitleaks가 없었다. CI는 ubuntu-latest GitHub Actions에서 돈다. 같은 Makefile이 두 환경에서 같은 결과를 내야 한다.

## Decision

- **런타임**: Python 3.12. `requires-python = ">=3.12,<3.13"`, `.python-version = 3.12`, uv가 관리하는 CPython(3.12.14)을 쓴다. 시스템 3.13은 쓰지 않는다.
- **패키지·lock**: uv(`uv.lock` 커밋, 모든 타깃은 `--frozen`). 개발 의존성은 `[dependency-groups].dev`에 둔다.
- **정적 분석**: ruff(lint + format), mypy `--strict`(harness, tests), import-linter.
- **테스트**: pytest, pytest-asyncio(`asyncio_mode=auto`), pytest-cov(`fail_under = 85`, SPEC 16.3). `--strict-markers`이고 `req` 마커는 미리 등록해 둔다(SPEC 8).
- **보안 스캔 실행 방식**
  - Semgrep: `uv tool run semgrep`(격리 환경). 프로젝트 의존성 해석에 semgrep의 엄격한 버전 고정이 섞이지 않게 하려는 것이다. Windows에서 실행되는 것을 확인했다(progress.md Evidence).
  - Bandit: dev 의존성.
  - pip-audit: venv가 아니라 `uv.lock`에서 export한 해시 고정 requirements를 감사한다. venv에는 editable 프로젝트가 있어 `--strict`와 함께 쓸 수 없고, 배포될 것은 lock이기 때문이다.
  - gitleaks: 바이너리(로컬은 winget, CI는 릴리스 tarball 8.30.1). pre-commit에서는 설치된 바이너리를 `language: system` hook으로 실행한다. 공식 hook(`language: golang`)은 첫 실행 때 Go 툴체인을 받아 소스에서 빌드하는데, 이 머신에서 15분이 넘도록 끝나지 않았다.
  - Trivy: 컨테이너 이미지가 생기는 Phase 2/3에 추가한다(backlog).
- **로컬 의존성**: docker-compose에 postgres:16-alpine, redis:7-alpine, ghcr.io/shopify/toxiproxy:2.12.0. 포트는 `127.0.0.1`에만 바인딩한다. 기본 호스트 포트는 55432/56379/58474로, 이 머신에 이미 설치된 PostgreSQL 17(5432)과 충돌하지 않게 했다.
- **Makefile 이식성**: 레시피는 sh와 cmd 양쪽에서 동작하는 명령만 쓴다. 아직 구현하지 않은 타깃(load/chaos/report)은 `$(error NOT_IMPLEMENTED: ...)`로 셸과 무관하게 실패한다.
- **줄바꿈**: `.gitattributes`로 `eol=lf`를 고정한다(core.autocrlf=true 환경에서 Makefile과 YAML 보호).

## Alternatives

- **시스템 Python 3.13 사용**: SPEC이 3.12를 지정했고, 일부 검증 도구(memray 등)의 버전 지원 범위가 3.12에서 더 넓다. uv가 3.12를 프로젝트 단위로 받아오므로 비용이 없다.
- **semgrep을 dev 의존성에 추가**: semgrep은 click, opentelemetry 등을 좁게 고정해 Phase 2 이후 FastAPI·OTel 의존성과 충돌할 위험이 있다.
- **Docker로 semgrep 실행**: Docker 엔진 상태에 보안 스캔이 묶인다. Phase 0에서 엔진이 실제로 응답하지 않았다.
- **`pip-audit --skip-editable`**: `--strict`에서 editable 건너뛰기를 오류로 처리한다. strict를 빼면 해석 실패한 의존성도 조용히 통과해 R2(검사 안 한 것은 안전하지 않다)에 어긋난다.
- **just/nox/PowerShell 스크립트**: SPEC과 CLAUDE.md가 `make`를 명령 인터페이스로 고정했다.

## Consequences

- 얻는 것: Windows 로컬과 Linux CI가 같은 `make` 타깃과 같은 lock으로 돈다.
- 잃는 것·리스크: 개발자 머신에 uv, GNU make, gitleaks가 필요하다(README Quick start). `uv tool run semgrep`은 매번 최신 semgrep을 받으므로 규칙 결과가 시간에 따라 변할 수 있다. Phase 3에서 버전을 고정한다(backlog).

## Phase 1 재검토 (2026-10-09)

스택 결정은 바꾸지 않는다. Phase 1에서 확인하거나 추가한 내용은 아래와 같다.

- import-linter 2.15의 `protected` 계약과 `allow_indirect_imports`로 SPEC 5의 "서비스 인터페이스 경유"를 강제할 수 있음을 확인했다(설치된 소스 확인). import-linter는 존재하지 않는 모듈을 가리키는 계약을 경고 없이 통과시킨다. 그래서 계약 모듈 존재 테스트를 추가했다(domain-boundaries 6).
- Target 패키지 `app`은 `services/todo-api` 아래에 있어서, Makefile `importlint` 타깃이 `PYTHONPATH=services/todo-api`를 설정한다. mypy는 `mypy_path`로 같은 경로를 본다.
- JWT 라이브러리는 PyJWT + cryptography(ADR-0003), 비밀번호 해시는 argon2-cffi(ADR-0003)로 정했다. 실제 의존성 추가는 Phase 2에서 한다.
- 열린 항목은 ADR로 남긴다.
  - REQ-N-007.2(api 2개 인스턴스 롤링 재시작)는 인스턴스 앞에 로드밸런서가 필요하다. SPEC 3 스택에는 없으므로 Phase 5에서 선택하고 ADR로 남긴다(backlog).

## Verification

- `make verify` 성공(ruff, mypy --strict, import-linter, pytest + coverage).
- `make security` 성공(semgrep, bandit, pip-audit, gitleaks).
- `docker compose up -d` 후 postgres/redis/toxiproxy healthy.
- 결과 수치와 명령은 `docs/progress.md`의 Evidence에 기록한다.
