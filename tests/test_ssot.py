"""
Single-source-of-truth enforcement.

The project has repeatedly drifted by re-declaring a canonical constant next to
where it is used: ISLAND_SET was defined in both constants.py and the dashboard,
and PillarRegistry kept a second copy of the pillar names. Comments saying
"never redefine this" did not prevent either.

These tests scan the source tree for redefinition, so the rule is enforced
mechanically instead of by good intentions.
"""

import ast
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent

#: Constants that may be assigned in exactly one place.
CANONICAL = {
    "PILLAR_DEFS":    "asi/core/constants.py",
    "WEIGHT_PRESETS": "asi/core/constants.py",
    "ISLAND_SET":     "asi/core/constants.py",
    "WEIGHT_MIN":     "asi/core/constants.py",
    "WEIGHT_MAX":     "asi/core/constants.py",
    "SMALL":          "asi/core/constants.py",
    "IQR_MULTIPLIER": "asi/core/constants.py",
    "COUNTRIES":      "asi/core/countries.py",
}

SKIP_DIRS = {".venv", ".git", "__pycache__", "node_modules", "data"}


def _python_files():
    for p in REPO.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def _module_level_assignments(path: pathlib.Path) -> set[str]:
    """Names bound by a top-level assignment in this file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in tree.body:                      # module level only
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


@pytest.mark.parametrize("const,owner", sorted(CANONICAL.items()))
def test_constant_defined_exactly_once(const, owner):
    owner_path = (REPO / owner).resolve()
    offenders = []
    for path in _python_files():
        if path.resolve() == owner_path:
            continue
        if const in _module_level_assignments(path):
            offenders.append(str(path.relative_to(REPO)))
    assert not offenders, (
        f"{const} is owned by {owner} but is also assigned in: {offenders}. "
        f"Import it instead of redefining it."
    )


def test_canonical_constants_actually_live_where_claimed():
    """Guard against the map above going stale."""
    for const, owner in CANONICAL.items():
        path = REPO / owner
        assert path.exists(), f"{owner} does not exist"
        assert const in _module_level_assignments(path), (
            f"{const} is not assigned at module level in {owner}"
        )


def test_no_module_shadows_the_package():
    """
    Root-level modules named `constants.py`/`config.py`/`models/` shadowed the
    package during the Phase A migration and silently won on sys.path. Ensure
    they are gone.
    """
    for stale in ("constants.py", "config.py", "run_config.py"):
        assert not (REPO / stale).exists(), (
            f"{stale} still exists at the repo root and will shadow asi.core"
        )
    assert not (REPO / "models" / "__init__.py").exists(), (
        "models/ package still exists; it moved into asi/core/"
    )
