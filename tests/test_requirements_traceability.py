"""Keeps docs/requirements.md a faithful, complete traceability table (SPEC 8, 5.3).

The table is the project's external memory (WORKING-GUIDELINES B, 03). These tests fail when a
SPEC requirement is dropped, a row loses its verification method, a row claims "검증됨"
without evidence, or a test marker points at a requirement that does not exist.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "SPEC.md"
REQUIREMENTS = ROOT / "docs" / "requirements.md"

COLUMNS = (
    "ID",
    "요구사항",
    "해결할 문제",
    "완료 조건",
    "테스트 방법",
    "검증 방법",
    "Phase",
    "상태",
    "구현 위치",
    "증거",
)
REQUIRED = ("요구사항", "해결할 문제", "완료 조건", "테스트 방법", "검증 방법", "Phase", "상태")
STATUSES = {"미구현", "부분 구현", "구현됨", "검증됨"}
ROW_ID = re.compile(r"^(REQ-[FNH]-\d{3}(\.\d+)?|SPEC-\d+(\.\d+)?-\d+)$")
# A phase cell is "2", a range written with an en dash such as "2-4", or "0, 3, 7".
EN_DASH = chr(0x2013)
PHASES = re.compile(f"^[0-8](([{EN_DASH},] ?)[0-8])*$")
TEST_ROOTS = [ROOT / "tests", ROOT / "services" / "todo-api" / "tests"]


@dataclass(frozen=True)
class Row:
    cells: dict[str, str]

    @property
    def id(self) -> str:
        return self.cells["ID"]


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _rows() -> list[Row]:
    rows = []
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cells = _cells(line)
        if ROW_ID.match(cells[0]):
            assert len(cells) == len(COLUMNS), f"{cells[0]}: expected {len(COLUMNS)} columns"
            rows.append(Row(dict(zip(COLUMNS, cells, strict=True))))
    return rows


def _spec_requirement_ids() -> set[str]:
    text = SPEC.read_text(encoding="utf-8")
    chapter_8 = text.split("## 08 요구사항과 수용 기준", 1)[1].split("\n## 09 ", 1)[0]
    return set(re.findall(r"^\| (REQ-[FNH]-\d{3}) \|", chapter_8, flags=re.MULTILINE))


def _marker_ids() -> list[tuple[Path, str]]:
    found = []
    for root in TEST_ROOTS:
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "req"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    found.append((path, node.args[0].value))
    return found


ROWS = _rows()


def test_spec_chapter_8_has_the_expected_requirements() -> None:
    # 6 functional + 8 non-functional + 6 harness requirements in SPEC v1.0.
    ids = _spec_requirement_ids()
    assert len(ids) == 20, sorted(ids)


def test_every_spec_requirement_is_traced() -> None:
    traced = {row.id for row in ROWS}
    missing = _spec_requirement_ids() - traced
    assert not missing, f"SPEC 8 requirements missing from requirements.md: {sorted(missing)}"


def test_no_unknown_top_level_requirements() -> None:
    top_level = {row.id for row in ROWS if re.fullmatch(r"REQ-[FNH]-\d{3}", row.id)}
    assert top_level == _spec_requirement_ids()


def test_row_ids_are_unique() -> None:
    ids = [row.id for row in ROWS]
    assert len(ids) == len(set(ids)), sorted({i for i in ids if ids.count(i) > 1})


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row.id)
def test_row_is_complete(row: Row) -> None:
    empty = [column for column in REQUIRED if row.cells[column] in ("", "-")]
    assert not empty, f"{row.id}: empty {empty}"
    assert row.cells["상태"] in STATUSES, row.cells["상태"]
    assert PHASES.match(row.cells["Phase"]), row.cells["Phase"]


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row.id)
def test_sub_requirement_has_parent(row: Row) -> None:
    if re.fullmatch(r"REQ-[FNH]-\d{3}\.\d+", row.id):
        assert row.id.rsplit(".", 1)[0] in {r.id for r in ROWS}


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row.id)
def test_progress_beyond_unimplemented_has_location_and_evidence(row: Row) -> None:
    status = row.cells["상태"]
    if status == "미구현":
        return
    assert row.cells["구현 위치"] not in ("", "-"), f"{row.id} is {status} without a location"
    if status in ("검증됨", "부분 구현"):
        assert row.cells["증거"] not in ("", "-"), f"{row.id} is {status} without evidence"


def test_test_markers_reference_known_requirements() -> None:
    known = {row.id for row in ROWS}
    unknown = [
        (str(path.relative_to(ROOT)), rid) for path, rid in _marker_ids() if rid not in known
    ]
    assert not unknown, unknown
