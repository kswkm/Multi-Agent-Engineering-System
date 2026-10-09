# Multi-Agent Engineering System — task runner (SPEC 4, Appendix A).
# Recipes avoid shell-specific syntax so they run under sh (CI, Git Bash) and cmd (Windows).
# Targets whose phase has not started fail loudly with NOT_IMPLEMENTED instead of passing silently.

UV ?= uv
STAGE ?=
SCENARIO ?=

.PHONY: help install verify lint format typecheck importlint test security semgrep bandit pip-audit gitleaks load chaos report

help:
	@echo "make install    - sync dev dependencies and install pre-commit hooks"
	@echo "make verify     - ruff + mypy --strict + import-linter + pytest (coverage >= 85%)"
	@echo "make security   - semgrep, bandit, pip-audit, gitleaks"
	@echo "make test       - pytest only"
	@echo "make load STAGE=smoke|load|stress|soak     (Phase 4)"
	@echo "make chaos SCENARIO=db_down|redis_down|llm_timeout   (Phase 5)"
	@echo "make report     - Verification Matrix under reports/<run_id>/ (Phase 6)"

install:
	$(UV) sync --frozen
	$(UV) run pre-commit install

verify: lint typecheck importlint test

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format:
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

typecheck:
	$(UV) run mypy

importlint:
	$(UV) run lint-imports

test:
	$(UV) run pytest --cov --cov-report=term-missing

security: semgrep bandit pip-audit gitleaks

semgrep:
	$(UV) tool run semgrep scan --config p/python --error --metrics=off --exclude reports --exclude .venv

bandit:
	$(UV) run bandit -c pyproject.toml -r harness

pip-audit:
	$(UV) export --frozen --format requirements-txt --no-emit-project --output-file reports/audit/requirements.txt
	$(UV) run pip-audit --strict --require-hashes --requirement reports/audit/requirements.txt

gitleaks:
	gitleaks git --redact --no-banner --verbose .

load:
	$(error NOT_IMPLEMENTED: 'make load STAGE=$(STAGE)' arrives in Phase 4 (SPEC 11.4))

chaos:
	$(error NOT_IMPLEMENTED: 'make chaos SCENARIO=$(SCENARIO)' arrives in Phase 5 (SPEC 12))

report:
	$(error NOT_IMPLEMENTED: 'make report' arrives in Phase 6 (SPEC 7, 18))
