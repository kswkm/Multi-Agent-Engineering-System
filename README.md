# Multi-Agent Engineering System

A multi-agent harness that verifies whether AI-generated code is safe and reliable enough to run, and keeps the evidence for that verdict. A Todo API is built as the verification target.

**Status: Phase 1 (requirements and design).** The repository skeleton, tooling, local dependencies, the requirements traceability table and the domain-boundary import rules exist. Neither the harness nor the target service has any behaviour implemented yet. See:
- [docs/progress.md](docs/progress.md): what has been verified
- [docs/requirements.md](docs/requirements.md): every requirement and how it will be verified
- [ARCHITECTURE.md](ARCHITECTURE.md): design overview
- [docs/SPEC.md](docs/SPEC.md): the full specification (the source of truth)

The full README structure (SPEC 19.1) is a Phase 8 deliverable.

## Quick start (what works today)

Requirements: [uv](https://docs.astral.sh/uv/), GNU make, Docker, [gitleaks](https://github.com/gitleaks/gitleaks).

```sh
uv python install 3.12
make install          # uv sync + pre-commit hooks
make verify           # ruff, mypy --strict, import-linter, pytest
make security         # semgrep, bandit, pip-audit, gitleaks

cp .env.example .env  # then set POSTGRES_PASSWORD
docker compose up -d  # postgres 16, redis 7, toxiproxy (localhost-only ports)
docker compose ps
```

`make load`, `make chaos` and `make report` exit with `NOT_IMPLEMENTED` until their phases (4, 5, 6).
