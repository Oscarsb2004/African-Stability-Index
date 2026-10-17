"""
The rule `verify/` exists under, enforced rather than stated.

`README` and `verify/__init__.py` both say verification never imports the code
it checks — verification that imports the pipeline inherits the pipeline's bugs,
and a re-derivation built from the same functions is not a re-derivation, it is
a second copy of the same arithmetic. The rule was documentation only, and
`verify/advisory.py` had already broken it by importing the results loader.

`asi.core.constants` is the one permitted import, and the distinction is worth
stating precisely: it holds *declarations* — how many pillars there are, what
they are called, which countries are excluded and why. It holds no logic. A
verify module that re-typed the pillar list would not be more independent, only
more likely to drift; a verify module that imported a scoring function would be
checking that function against itself.

These tests read the source with `ast` rather than importing it, so a module
that fails at import time still gets scanned, and a name mentioned in a
docstring is not mistaken for an import.
"""

import ast
from pathlib import Path

import pytest

from asi.core.constants import PROJECT_ROOT

VERIFY_DIR = PROJECT_ROOT / "verify"

#: The only `asi` module verification may import. Declarations, never logic.
ALLOWED = {"asi.core.constants"}

VERIFY_FILES = sorted(VERIFY_DIR.rglob("*.py"))


def _is_module(dotted: str) -> bool:
    """Does this dotted name resolve to a file on disk, rather than to a name?"""
    parts = dotted.split(".")
    base = PROJECT_ROOT.joinpath(*parts)
    return base.with_suffix(".py").is_file() or (base / "__init__.py").is_file()


def _asi_imports(source: str) -> set[str]:
    """
    Every `asi.*` module a source file imports, however the import is spelled.

    Covers `import asi.x`, `import asi.x as y`, `from asi.x import y` and the
    bare `from asi import x` — that last form is how the violation was written
    (`from asi.dashboard import data as D`), and a check that only looked at
    dotted module paths would have missed it entirely.

    `from asi.core.constants import SMALL` and `from asi.dashboard import data`
    are the same syntax with different meanings: one imports a name out of a
    module, the other imports a module out of a package. Only the filesystem
    can tell them apart, so each candidate is resolved against it — otherwise
    importing a constant would look like importing a module named after that
    constant. Relative imports cannot reach `asi` from inside `verify/`, which
    is not a package of it, so `node.level` is skipped.
    """
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "asi" or alias.name.startswith("asi."):
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level or not node.module:
                continue
            if node.module != "asi" and not node.module.startswith("asi."):
                continue
            found.add(node.module)
            for alias in node.names:
                candidate = f"{node.module}.{alias.name}"
                if _is_module(candidate):
                    found.add(candidate)
    return found


def test_there_are_verify_modules_to_check():
    """A glob that silently matches nothing would make every test below pass."""
    names = {p.name for p in VERIFY_FILES}
    assert {"panel.py", "contract.py", "narrative.py", "advisory.py"} <= names


@pytest.mark.parametrize("path", VERIFY_FILES, ids=lambda p: p.name)
def test_a_verify_module_imports_no_asi_code_it_checks(path: Path):
    """
    The gate itself. Adding `from asi.pipeline import score` to any verify
    module fails here, which is the whole point: the rule can no longer be
    broken by someone who has not read the README.
    """
    imported = _asi_imports(path.read_text(encoding="utf-8"))
    forbidden = sorted(m for m in imported if m not in ALLOWED)
    assert not forbidden, (
        f"{path.name} imports {forbidden}. Verification may import only "
        f"{sorted(ALLOWED)} — declarations, not logic. Re-state the rule in "
        f"the verify module instead of importing the code that implements it."
    )


def test_the_results_loader_specifically_is_not_imported():
    """
    Named separately from the general rule because this is the import that was
    actually there. `verify/advisory.py` loaded the panel through the same
    module the interface uses, so a filter added to that loader would have
    narrowed what the diagnostics saw without changing a single line of
    `advisory.py`.
    """
    for path in VERIFY_FILES:
        imported = _asi_imports(path.read_text(encoding="utf-8"))
        assert "asi.results" not in imported, f"{path.name} imports asi.results"
        assert "asi.dashboard" not in imported, f"{path.name} imports the interface"


def test_the_old_module_path_no_longer_resolves():
    """
    A rename that leaves the old path importable leaves the old habit working
    too, and the next `from asi.dashboard import data` would pass every gate.
    """
    assert not _is_module("asi.dashboard.data")
    assert _is_module("asi.results")


def test_nothing_in_the_repository_still_imports_the_old_path():
    """
    Import statements only. The backlog and this module's own docstrings discuss
    the move by name and should keep doing so — a prose mention is a record, not
    a dependency.
    """
    stale = []
    for path in sorted(PROJECT_ROOT.rglob("*.py")):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            imported = _asi_imports(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        if "asi.dashboard.data" in imported:
            stale.append(str(path.relative_to(PROJECT_ROOT)))
    assert not stale, f"stale imports of the old results path: {stale}"


# ── the detector, checked against forms it must and must not catch ─────────────

@pytest.mark.parametrize("source", [
    "from asi.dashboard import data as D",       # the violation as written
    "from asi import results as D",              # the same thing, new address
    "import asi.pipeline.score",
    "import asi.pipeline.score as s",
    "from asi.pipeline.score import weighted_composite",
    "from asi.narrative import schema",
])
def test_the_detector_catches_each_way_of_spelling_an_import(source):
    assert _asi_imports(source) - ALLOWED


@pytest.mark.parametrize("source", [
    "from asi.core.constants import PILLAR_DEFS, SMALL",
    "import asi.core.constants",
    '"""A docstring mentioning asi.results and asi.pipeline.score."""',
    "D = None  # asi.results would go here",
    "import pandas as pd\nfrom scipy.stats import spearmanr",
])
def test_the_detector_does_not_fire_on_the_permitted_or_the_merely_mentioned(source):
    assert not _asi_imports(source) - ALLOWED
