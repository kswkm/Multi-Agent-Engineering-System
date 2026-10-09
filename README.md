# Multi-Agent Engineering System

A multi-agent harness that verifies whether AI-generated code is safe and reliable enough to run, and keeps the evidence for that verdict. A Todo API is built as the verification target.

**Status: Phase 0 (bootstrap).** Only the repository skeleton, tooling and local dependencies exist. Nothing below the harness or the target service is implemented yet. See [docs/progress.md](docs/progress.md) for what has been verified, and [docs/SPEC.md](docs/SPEC.md) for the full specification (the source of truth). The full README structure (SPEC 19.1) is a Phase 8 deliverable.

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
