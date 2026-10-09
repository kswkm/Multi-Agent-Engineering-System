# 0003. 암호 정책: 알고리즘, 파라미터, 키 저장과 교체

Status: Accepted (Phase 1 설계). Argon2id 파라미터는 **잠정**이며 Phase 2에서 실제 api 이미지로 재측정해 확정한다.

## Context

SPEC 10이 알고리즘의 기본값을 정했다. 공통 지침 v2(12.2)는 보안 기능마다 다음을 기록하라고 요구한다.
- 어떤 알고리즘과 파라미터를 왜 쓰는가
- 키는 어디에 있고 어떻게 교체하는가

SPEC 10은 파라미터를 "구현 시점의 OWASP Cheat Sheet와 대조"하고 비밀번호 해시는 "대상 환경에서 해시 1회 ≈ 0.2–0.5s가 되도록 벤치마크 후 결정"하라고 한다. 대상 환경은 api 컨테이너 2 vCPU / 512MB다(SPEC 8.2).

**OWASP 대조 (2026-10-09)**: Password Storage Cheat Sheet의 Argon2id 최소 권장은 `m=19456 (19 MiB), t=2, p=1`이다. 같은 방어 수준의 다른 조합도 허용하며, "Benchmark the chosen parameters on the target system"을 요구한다.

## Decision

| 대상 | 결정 | 이유 |
|---|---|---|
| 비밀번호 해시 | **Argon2id**, `argon2-cffi`. 잠정 `memory_cost=65536 KiB (64 MiB), time_cost=3, parallelism=1`. salt 16바이트(라이브러리 기본, 해시 문자열에 포함) | OWASP 최소보다 메모리 3.4배, 반복 1.5배. 아래 벤치마크에서 해시 1회가 0.2–0.5s 목표 범위 근처에 든 유일한 후보다. 파라미터가 해시 문자열에 저장되므로 로그인 성공 시 `check_needs_rehash`로 점진 상향한다. |
| 해시 동시 실행 제한 | 프로세스당 동시 해시 **2개**(semaphore, vCPU 수). 대기 한도를 넘으면 503 + `Retry-After` | 64 MiB × 동시 해시 수가 메모리를 쓴다. 제한이 없으면 로그인 폭주가 512MB 컨테이너를 OOM으로 만든다(SPEC 11.5, CWE-400). 공통 지침 5.2의 격벽(Bulkhead). 동시 2개면 해시용 메모리는 최대 128 MiB다. |
| Access Token | **JWT EdDSA(Ed25519)**, `PyJWT` + `cryptography`. 헤더 `kid` 필수. 클레임 `sub`, `iat`, `exp`(15분), `jti`, 고정 `iss`·`aud`. 검증 시 `algorithms=["EdDSA"]`로 고정하고 `kid`가 JWKS에 있어야 함 | 검증 측(core.security)은 공개키만 가진다(domain-boundaries 3.2). 허용 알고리즘을 하나로 고정해 `alg: none`과 HS/RS 혼동 공격을 막는다. `iss`·`aud`를 검증해 다른 용도의 토큰을 거부한다. |
| Refresh Token | `secrets.token_urlsafe(32)`(256비트 CSPRNG) 불투명 토큰. DB에는 **SHA-256 해시**만 저장. `family_id`로 계열을 묶고, 갱신 때마다 회전한다. 사용된 토큰이 다시 오면 계열 전체를 폐기한다 | DB가 유출돼도 원문 토큰을 쓸 수 없다(SPEC 10). 256비트 무작위 값은 사전 공격이 불가능하므로 salt·느린 해시가 필요 없다. SPEC 10의 "salt 없는 SHA-256 금지"는 비밀번호 대상이다. |
| 난수 | `secrets` 모듈만 사용 | `random`은 예측 가능하다. 예외는 하네스 재현용 seed(ADR-0002 규칙 6) 하나이며 보안 용도가 아니다. |
| 저장 데이터 암호화 | **NOT_APPLICABLE** (현 요구사항 기준) | SPEC 10은 "필요 시" AES-256-GCM이라고 한다. SPEC 8의 어떤 요구사항도 필드 단위 암호화를 요구하지 않는다. 필요해지면 AES-256-GCM + 레코드별 96비트 nonce + 봉투 암호화(DEK/KEK)로 이 ADR을 갱신한다. |
| 키 저장 | Ed25519 개인키 PEM은 **파일 경로 환경변수**(`JWT_SIGNING_KEY_FILE`)로 받는다. 로컬은 Docker secret 또는 gitignored 파일, 운영 가정은 KMS. 키를 이미지·저장소·로그에 넣지 않는다 | SPEC R6, 10. 파일 경로 방식은 Docker secret(`/run/secrets/...`)과 그대로 맞물린다. gitleaks가 커밋을 막는다(Phase 0 hook). |
| 키 교체 | JWKS에 **현재 키 + 이전 키** 공존. 아래 절차 | SPEC 10 "kid 기반 교체" |
| 전송 구간 | 로컬은 HTTP. 운영 가정은 리버스 프록시에서 TLS 1.3 우선, 최소 1.2 | SPEC 10. 로컬 검증 범위 밖이므로 README Known Limitations에 적는다. |

### 키 교체 절차 (RUNBOOK에 옮기고 Phase 5에서 테스트, SPEC-10-4)

1. 새 Ed25519 키 쌍을 만들고 새 `kid`를 붙인다.
2. 새 공개키를 검증 키 집합(JWKS)에 **추가**한다. 이 시점에는 서명은 여전히 이전 키로 한다.
3. 모든 인스턴스가 새 JWKS를 읽은 뒤 **서명 키를 새 키로 전환**한다.
4. 최대 access 수명(15분) + 시계 오차 여유가 지나면 이전 공개키를 JWKS에서 **제거**한다.
5. 검증: 전환 직후 이전 키로 서명된 토큰이 수명 내에 통과하는지, 제거 후에는 401인지 확인한다.

## Benchmark (Argon2id, 2026-10-09)

- **환경**: `python:3.12-slim` 컨테이너, `--cpus 2 --memory 512m`, argon2-cffi 25.1.0, Windows 11 호스트의 Docker Desktop.
- **측정**: 후보마다 단일 해시 7회의 중앙값, 동시 4개 해시의 총 시간. 스크립트는 세션 scratchpad에서 실행했다. 재측정 스크립트는 Phase 2에서 `verification/`에 둔다.

| 후보 | 1차 중앙값 | 2차 중앙값 | 1차 동시 4개 | 2차 동시 4개 |
|---|---|---|---|---|
| OWASP 최소 m=19MiB t=2 p=1 | 38.2 ms | 41.9 ms | 210.6 ms | 265.9 ms |
| m=19MiB t=4 p=1 | 57.0 ms | 84.3 ms | 106.0 ms | 193.7 ms |
| m=46MiB t=1 p=1 | 57.1 ms | 105.5 ms | 365.8 ms | 356.3 ms |
| m=46MiB t=2 p=1 | 160.8 ms | 159.1 ms | 369.7 ms | 354.0 ms |
| **m=64MiB t=3 p=1 (선택)** | **291.0 ms** | **191.3 ms** | 956.8 ms | 842.1 ms |
| m=64MiB t=3 p=2 | 136.4 ms | 110.9 ms | 1184.3 ms | 919.7 ms |
| argon2-cffi 기본 m=64MiB t=3 p=4 | 166.8 ms | 182.4 ms | 1186.9 ms | 1363.7 ms |

해석:
- 두 실행 사이 편차가 크다(선택 후보 191–291 ms). 호스트 부하와 Docker Desktop VM 스케줄링 영향으로 보인다. 그래서 이 파라미터는 **잠정**이고, Phase 2에서 실제 api 이미지로 반복 측정해 확정한다.
- p>1은 단일 해시를 빠르게 하지만 2 vCPU에서 동시 요청 처리량을 줄인다(동시 4개 총시간이 더 길다). 로그인 동시성이 있는 서버에는 p=1이 맞다.
- 로그인 처리량 상한은 대략 인스턴스당 초당 7–10회다(2 슬롯 ÷ 0.2–0.3s). 따라서 k6 시나리오(Phase 4)는 VU당 한 번 로그인하고 토큰을 재사용하도록 짠다. 이 상한은 README Performance에 측정값으로 기록한다.

## Alternatives

| 대안 | 고르지 않은 이유 |
|---|---|
| OWASP 최소(19 MiB, t=2) | 해시 1회 약 40 ms로 SPEC 10의 목표(0.2–0.5s)에 한참 못 미친다. |
| bcrypt / scrypt | SPEC 10이 Argon2id를 지정했다. bcrypt는 72바이트 입력 제한도 있다(OWASP). |
| HS256 JWT | 검증 측에 서명 비밀을 줘야 한다. SPEC 10이 짧은 HS256 키를 금지한다. |
| RS256 / ES256 | Ed25519가 키·서명이 짧고 구현 실수 여지(곡선 파라미터, 패딩)가 적다. SPEC 10이 EdDSA를 지정했다. |
| python-jose, authlib(joserfc) | python-jose는 유지보수가 끊겼다. joserfc도 가능하지만 PyJWT가 `algorithms` 인자를 강제해 알고리즘 고정 실수를 줄인다. 설치 버전의 API는 Phase 2에서 소스로 확인한다(지침 B 환각). |
| refresh도 JWT | 폐기·회전·재사용 탐지에 어차피 DB 조회가 필요하다. 불투명 토큰이 유출 시 정보를 덜 흘린다. |

## Consequences

- 얻는 것: 알고리즘·파라미터·키 위치·교체 절차가 모두 명시되어 사고 시 근거를 설명할 수 있다.
- 잃는 것: 로그인이 의도적으로 느리다(~0.2–0.3s). 해시 동시 실행 제한 때문에 로그인 폭주 시 503이 날 수 있다. 이것은 설계 의도다(OOM보다 낫다).
- 리스크: 측정 편차. Phase 2 재측정 전까지 파라미터는 확정이 아니다.

## Verification

- Phase 2
  - 해시 문자열이 `$argon2id$v=19$m=65536,t=3,p=1$`로 시작하는지 테스트한다.
  - `check_needs_rehash` 상향을 테스트한다. 낮은 파라미터로 만든 해시로 로그인하면 재해시되어야 한다.
  - 실제 api 이미지(2 vCPU/512MB)에서 단일 해시 중앙값 0.2–0.5s를 재측정한다.
  - 동시 해시가 2를 넘으면 503 + `Retry-After`인지 확인한다.
- Phase 2–3
  - `alg: none`, HS256, 변조 서명, 만료, 모르는 `kid`, 잘못된 `aud`/`iss` 토큰이 모두 401인지 확인한다(SPEC-10-2).
  - DB에 refresh 원문이 없는지 확인한다(REQ-F-002.1).
- Phase 3: Semgrep 규칙으로 `random`(보안 용도), MD5/SHA-1, ECB, `yaml.load`, `pickle`을 차단한다(SPEC-10-3, 10-5).
- Phase 5: 키 교체 절차 테스트(SPEC-10-4).
