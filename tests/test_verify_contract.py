"""
The contract checks, checked.

verify/contract.py section 2 polices the interface: no hardcoded counts, no
redefined canonical constants, no reading storage behind the data layer. All
three passed a clean run for months while being unable to catch most of what
they describe:

  * `_ui_files()` used `glob("*.py")`, so nothing in a subdirectory was read at
    all. Splitting app.py into a `views/` package — the obvious next refactor —
    would have silently switched off the entire layer.
  * 2.1's pattern required two-or-three digits followed *immediately* by one of
    four exact nouns. It caught "36 Indicators", the bug it was written for, and
    passed "54 of 55 AU member states" (live in the header), "7 pillars" and
    "32 scoring indicators".
  * 2.2 inspected only module-level `ast.Assign`, so an annotated assignment or
    a class attribute redefined a canonical constant unnoticed.

A gate that has never been shown to fail is indistinguishable from no gate. Each
test below feeds a check something it is supposed to reject and asserts it does,
so a future loosening of any pattern shows up here rather than in production.
"""

import pytest

from verify import contract


@pytest.fixture
def ui(tmp_path, monkeypatch):
    """Point the checks at a scratch interface tree and reset their ledger."""
    monkeypatch.setattr(contract, "UI_DIR", tmp_path)
    contract.CHECKS.clear()
    return tmp_path


def _write(root, relpath: str, source: str):
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def _verdict(prefix: str) -> str:
    for check in contract.CHECKS:
        if check["name"].startswith(prefix):
            return check["status"]
    raise AssertionError(f"no check recorded for {prefix!r}")


# ── 2.1 hardcoded counts ───────────────────────────────────────────────────────

MUST_FAIL_COUNTS = [
    '"36 Indicators"',                      # the original bug
    '"54 of 55 AU member states"',          # was live in the header
    '"7 pillars"',                          # single digit
    '"32 scoring indicators"',              # intervening word
    '"all 54 countries"',
    '"covering 54 African countries"',
    '"the 7 pillars of the index"',
    '"55 member states"',
]

MUST_PASS_COUNTS = [
    '"0 = most fragile · 100 = most stable"',
    '"2000–2024"',
    '"2024 country coverage"',              # a year, not a count
    '"Pillar C · rule of law"',
    'f"{n} of {m} AU member states"',       # the derived form, the whole point
    '"Scores are 0–100."',
]


@pytest.mark.parametrize("literal", MUST_FAIL_COUNTS)
def test_hardcoded_counts_are_caught(ui, literal):
    _write(ui, "app.py", f"x = {literal}\n")
    contract.check_no_hardcoded_counts()
    assert _verdict("2.1") == "FAIL", f"{literal} slipped through"


@pytest.mark.parametrize("literal", MUST_PASS_COUNTS)
def test_legitimate_strings_are_not_flagged(ui, literal):
    _write(ui, "app.py", f"x = {literal}\n")
    contract.check_no_hardcoded_counts()
    assert _verdict("2.1") == "PASS", f"{literal} is a false positive"


def test_counts_are_caught_in_subdirectories(ui):
    _write(ui, "app.py", "x = 1\n")
    _write(ui, "views/country.py", 'x = "36 Indicators"\n')
    contract.check_no_hardcoded_counts()
    assert _verdict("2.1") == "FAIL"


# ── 2.2 redefined canonical constants ──────────────────────────────────────────

MUST_FAIL_REDEFINITIONS = [
    "PILLAR_DEFS = {}",                            # plain assignment
    "PILLAR_DEFS: dict = {}",                      # annotated
    "WEIGHT_PRESETS: dict[str, float] = {}",
    "class Config:\n    COUNTRIES = []",           # class attribute
    "def build():\n    ISLAND_SET = set()",        # rebound in a function
]


@pytest.mark.parametrize("source", MUST_FAIL_REDEFINITIONS)
def test_canonical_redefinition_is_caught(ui, source):
    _write(ui, "app.py", source + "\n")
    contract.check_ui_does_not_redefine_canonicals()
    assert _verdict("2.2") == "FAIL", f"{source!r} slipped through"


def test_importing_canonicals_is_fine(ui):
    _write(ui, "app.py", "from asi.core.constants import PILLAR_DEFS, ISLAND_SET\n")
    contract.check_ui_does_not_redefine_canonicals()
    assert _verdict("2.2") == "PASS"


def test_redefinition_is_caught_in_subdirectories(ui):
    _write(ui, "app.py", "x = 1\n")
    _write(ui, "views/overview.py", "PILLAR_DEFS = {}\n")
    contract.check_ui_does_not_redefine_canonicals()
    assert _verdict("2.2") == "FAIL"


# ── 2.3 reads behind the data layer ────────────────────────────────────────────

MUST_FAIL_READS = [
    'import pandas as pd\ndf = pd.read_csv("scores.csv")',
    'from pandas import read_excel\ndf = read_excel("x.xlsx")',
    'PATH = "data/panel/observations.csv"',
    'OUT = "06_results/scores.csv"',
]


@pytest.mark.parametrize("source", MUST_FAIL_READS)
def test_direct_reads_are_caught(ui, source):
    _write(ui, "app.py", source + "\n")
    contract.check_ui_reads_only_through_the_data_layer()
    assert _verdict("2.3") == "FAIL", f"{source!r} slipped through"


def test_direct_reads_are_caught_in_subdirectories(ui):
    _write(ui, "app.py", "x = 1\n")
    _write(ui, "views/detail.py", 'import pandas as pd\ndf = pd.read_csv("x.csv")\n')
    contract.check_ui_reads_only_through_the_data_layer()
    assert _verdict("2.3") == "FAIL"


def test_prose_about_reading_is_not_a_read(ui):
    """
    The substring version flagged its own documentation. Matching the syntax
    tree means a docstring may name `read_csv` without being one.
    """
    _write(ui, "app.py", '"""Everything goes through data.py, never read_csv."""\n')
    contract.check_ui_reads_only_through_the_data_layer()
    assert _verdict("2.3") == "PASS"


def test_the_data_layer_itself_is_exempt(ui):
    _write(ui, "data.py", 'import pandas as pd\ndf = pd.read_csv("data/panel/x.csv")\n')
    contract.check_ui_reads_only_through_the_data_layer()
    assert _verdict("2.3") == "PASS"


def test_loading_context_yaml_is_not_a_panel_read(ui):
    """
    2.3 is about the stored panel that verify/panel.py re-derives. The context
    files and the narrative corpus are separate stores under separate rules, and
    the interface is allowed to open them.
    """
    _write(ui, "app.py", 'import yaml\nd = yaml.safe_load(open("context/KEN.yaml"))\n')
    contract.check_ui_reads_only_through_the_data_layer()
    assert _verdict("2.3") == "PASS"


# ── the failure that would have disabled everything ────────────────────────────

def test_ui_files_recurses(ui):
    _write(ui, "app.py", "x = 1\n")
    _write(ui, "views/country.py", "y = 2\n")
    _write(ui, "views/parts/table.py", "z = 3\n")
    found = {p.relative_to(ui).as_posix() for p in contract._ui_files()}
    assert found == {"app.py", "views/country.py", "views/parts/table.py"}
