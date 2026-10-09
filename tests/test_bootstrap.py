"""Phase 0 exit checks that can be verified from inside the repository (SPEC 4, 17)."""

import importlib
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

SPEC_DIRECTORIES = [
    ".github/workflows",
    "harness/orchestrator",
    "harness/agents",
    "harness/prompts",
    "harness/schemas",
    "harness/llm",
    "harness/tools",
    "harness/checkers",
    "harness/policies",
    "harness/evidence",
    "services/todo-api/app/domains/auth",
    "services/todo-api/app/domains/users",
    "services/todo-api/app/domains/todos",
    "services/todo-api/app/domains/tags",
    "services/todo-api/app/domains/sharing",
    "services/todo-api/app/core",
    "services/todo-api/migrations",
    "services/todo-api/tests/unit",
    "services/todo-api/tests/integration",
    "services/todo-api/tests/contract",
    "services/todo-api/tests/property",
    "verification/load",
    "verification/chaos",
    "verification/security",
    "verification/memory",
    "docs/adr",
]

PHASE_0_FILES = [
    "CLAUDE.md",
    "Makefile",
    "docker-compose.yml",
    ".env.example",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".github/workflows/ci.yml",
    "docs/SPEC.md",
    "docs/progress.md",
    "docs/backlog.md",
    "docs/adr/0001-tech-stack.md",
]

HARNESS_PACKAGES = [
    "harness",
    "harness.orchestrator",
    "harness.agents",
    "harness.schemas",
    "harness.llm",
    "harness.tools",
    "harness.checkers",
    "harness.evidence",
]


@pytest.mark.parametrize("relative", SPEC_DIRECTORIES)
def test_spec_directory_exists(relative: str) -> None:
    assert (ROOT / relative).is_dir(), f"SPEC 4 directory missing: {relative}"


@pytest.mark.parametrize("relative", PHASE_0_FILES)
def test_phase_0_file_exists(relative: str) -> None:
    assert (ROOT / relative).is_file(), f"Phase 0 file missing: {relative}"


@pytest.mark.parametrize("module", HARNESS_PACKAGES)
def test_harness_package_imports(module: str) -> None:
    imported = importlib.import_module(module)
    assert imported.__doc__, f"{module} must state its responsibility"


def test_secrets_and_evidence_are_gitignored() -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in ignored
    assert "reports/" in ignored
    assert "!.env.example" in ignored


def test_env_example_has_no_real_secrets() -> None:
    values = dict(
        line.split("=", 1)
        for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    )
    assert values["ANTHROPIC_API_KEY"] == ""
    assert "change-me" in values["POSTGRES_PASSWORD"]


def test_python_is_pinned_to_312() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["requires-python"] == ">=3.12,<3.13"


def test_compose_does_not_hardcode_postgres_password() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?" in compose
