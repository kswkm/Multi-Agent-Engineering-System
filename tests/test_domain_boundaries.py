"""Guards the import-linter contracts that enforce docs/domain-boundaries.md (SPEC 5).

A contract that names a missing module is silently KEPT by import-linter, and a contract
that is loosened still reports KEPT. These tests catch both: they pin the contracts to the
SPEC 5.1 table and prove, on a synthetic package tree, that each rule actually breaks.
"""

import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ("auth", "users", "todos", "tags", "sharing")

# SPEC 5.1 "허용 의존성": which other domains each domain may import directly.
SPEC_ALLOWED_DEPENDENCIES: dict[str, set[str]] = {
    "auth": {"users"},
    "users": set(),
    "todos": {"users", "tags"},
    "tags": set(),
    "sharing": {"todos", "users"},
}

PACKAGE_ROOTS = {"harness": ROOT / "harness", "app": ROOT / "services" / "todo-api" / "app"}


def _config() -> dict[str, Any]:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    config: dict[str, Any] = pyproject["tool"]["importlinter"]
    return config


def _contracts() -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = _config()["contracts"]
    return contracts


def _module_path(module: str) -> Path:
    top, *rest = module.split(".")
    return PACKAGE_ROOTS[top].joinpath(*rest)


def _module_exists(module: str) -> bool:
    path = _module_path(module)
    return (path / "__init__.py").is_file() or path.with_suffix(".py").is_file()


def _contract_modules() -> list[str]:
    keys = ("source_modules", "forbidden_modules", "protected_modules", "allowed_importers")
    return sorted({m for c in _contracts() for k in keys for m in c.get(k, [])})


@pytest.mark.parametrize("module", _contract_modules())
def test_every_contract_module_exists(module: str) -> None:
    assert _module_exists(module), f"{module} is named in a contract but does not exist"


def test_domain_dependency_rules_match_spec_table() -> None:
    forbidden_by_domain: dict[str, set[str]] = {}
    for contract in _contracts():
        if contract["type"] != "forbidden":
            continue
        sources = contract["source_modules"]
        if len(sources) == 1 and sources[0].removeprefix("app.domains.") in DOMAINS:
            domain = sources[0].removeprefix("app.domains.")
            assert contract.get("allow_indirect_imports") is True
            forbidden_by_domain[domain] = {
                m.removeprefix("app.domains.") for m in contract["forbidden_modules"]
            }

    assert set(forbidden_by_domain) == set(DOMAINS)
    for domain, forbidden in forbidden_by_domain.items():
        allowed = set(DOMAINS) - {domain} - forbidden
        assert allowed == SPEC_ALLOWED_DEPENDENCIES[domain], domain


def test_every_domain_has_private_internals() -> None:
    protected = {
        (tuple(c["protected_modules"]), tuple(c["allowed_importers"]))
        for c in _contracts()
        if c["type"] == "protected"
    }
    for domain in DOMAINS:
        package = f"app.domains.{domain}"
        assert ((f"{package}.internal",), (package,)) in protected, domain


def test_target_service_never_imports_harness() -> None:
    assert {
        "type": "forbidden",
        "source_modules": ["app"],
        "forbidden_modules": ["harness"],
    }.items() <= next(c for c in _contracts() if c["source_modules"] == ["app"]).items()


# ------------------------------------------------------------- behaviour on a synthetic tree

SYNTHETIC_MODULES = [
    "harness/__init__.py",
    "harness/checkers/__init__.py",
    "harness/evidence/__init__.py",
    "harness/llm/__init__.py",
    "harness/agents/__init__.py",
    "app/__init__.py",
    "app/core/__init__.py",
    "app/domains/__init__.py",
    *[f"app/domains/{d}/{m}" for d in DOMAINS for m in ("__init__.py", "interface.py")],
    *[f"app/domains/{d}/internal/{m}" for d in DOMAINS for m in ("__init__.py", "repo.py")],
]


def _write_ini(path: Path) -> None:
    config = _config()
    lines = ["[importlinter]", "root_packages =", *[f"    {p}" for p in config["root_packages"]]]
    for index, contract in enumerate(config["contracts"]):
        lines.append(f"[importlinter:contract:{index}]")
        for key, value in contract.items():
            if isinstance(value, list):
                lines.append(f"{key} =")
                lines.extend(f"    {item}" for item in value)
            else:
                lines.append(f"{key} = {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _lint_synthetic_tree(
    tmp_path: Path, imports: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    for relative in SYNTHETIC_MODULES:
        file = tmp_path / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("", encoding="utf-8")
    for module, statement in imports.items():
        (tmp_path / (module.replace(".", "/") + ".py")).write_text(
            statement + "\n", encoding="utf-8"
        )
    config = tmp_path / ".importlinter"
    _write_ini(config)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "from importlinter.cli import lint_imports_command; lint_imports_command()",
            "--config",
            str(config),
            "--no-cache",
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


BROKEN_CASES = [
    (
        "app.domains.users.interface",
        "import app.domains.auth.interface",
        "users depends on no other domain",
    ),
    (
        "app.domains.tags.interface",
        "import app.domains.todos.interface",
        "tags depends on no other domain",
    ),
    (
        "app.domains.auth.interface",
        "import app.domains.todos.interface",
        "auth may depend only on users",
    ),
    (
        "app.domains.todos.interface",
        "import app.domains.sharing.interface",
        "todos may depend only on users and tags",
    ),
    (
        "app.domains.sharing.interface",
        "import app.domains.tags.interface",
        "sharing may depend only on todos and users",
    ),
    (
        "app.domains.todos.interface",
        "import app.domains.users.internal.repo",
        "users internals are private to users",
    ),
    (
        "app.domains.sharing.interface",
        "import app.domains.todos.internal.repo",
        "todos internals are private to todos",
    ),
    (
        "app.core.__init__",
        "import app.domains.todos.interface",
        "Core infrastructure does not depend on business domains",
    ),
    ("app.domains.todos.interface", "import harness", "Target service never imports the harness"),
    (
        "harness.checkers.__init__",
        "import harness.llm",
        "Deterministic judgement layers do not depend on LLM code",
    ),
]


@pytest.mark.parametrize(("importer", "statement", "contract"), BROKEN_CASES)
def test_violation_breaks_contract(
    tmp_path: Path, importer: str, statement: str, contract: str
) -> None:
    result = _lint_synthetic_tree(tmp_path, {importer: statement})
    assert result.returncode == 1, result.stdout + result.stderr
    # import-linter wraps long contract names across lines, so compare whitespace-normalised.
    output = " ".join(result.stdout.split())
    name = next(c["name"] for c in _contracts() if c["name"].startswith(contract))
    broken = [c["name"] for c in _contracts() if f"{c['name']} BROKEN" in output]
    assert broken == [name], result.stdout


def test_allowed_dependencies_keep_all_contracts(tmp_path: Path) -> None:
    allowed = {
        "app.domains.auth.interface": "import app.domains.users.interface",
        # todos -> tags directly, and sharing -> todos -> tags indirectly: both allowed.
        "app.domains.todos.interface": (
            "import app.domains.users.interface\n"
            "import app.domains.tags.interface\n"
            "import app.domains.todos.internal.repo"
        ),
        "app.domains.sharing.interface": (
            "import app.domains.todos.interface\nimport app.domains.users.interface"
        ),
        "app.domains.tags.internal.repo": "import app.core",
    }
    result = _lint_synthetic_tree(tmp_path, allowed)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"Contracts: {len(_contracts())} kept, 0 broken." in result.stdout
