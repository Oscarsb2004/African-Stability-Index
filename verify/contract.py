"""
verify/contract.py — the backend/frontend object contract. Gates a release.

    A health indicator is the same object on the server and in the interface,
    carrying its own name, series code, year and value. The interface renders
    what the backend emitted and derives nothing.

verify/panel.py already proves the numbers reconcile. This layer proves the
*identity* survives the crossing, and that the interface has not quietly started
computing or hardcoding things the pipeline is supposed to own.

Ported to the panel in Phase C.

Run:  python verify/contract.py
"""

import sys as _sys
from pathlib import Path as _Path

_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_REPO))

import ast
import json
import re

import pandas as pd
import yaml

PANEL_DIR      = _REPO / "data" / "panel"
BUNDLE         = PANEL_DIR / "bundle.json"
OBSERVATIONS   = PANEL_DIR / "observations.csv"
INDICATORS_DIR = _REPO / "indicators_list"
UI_DIR         = _REPO / "asi" / "dashboard"

DETAIL_CAP = 5
CHECKS: list[dict] = []

#: Every observation row must be able to describe itself without a lookup.
REQUIRED_OBS_COLUMNS = {
    "iso3", "variable_name", "display_name", "series_code",
    "year", "score", "provenance",
}


def record(name: str, status: str, summary: str, details=()) -> None:
    CHECKS.append({"name": name, "status": status})
    print(f"[{status}] contract | {name} -- {summary}")
    for line in list(details)[:DETAIL_CAP]:
        print(f"         {line}")
    if len(details) > DETAIL_CAP:
        print(f"         ... and {len(details) - DETAIL_CAP} more")


def load_registry() -> dict[str, dict]:
    reg: dict[str, dict] = {}
    for p in sorted(INDICATORS_DIR.glob("*.yaml")):
        for ind in yaml.safe_load(p.read_text(encoding="utf-8")) or []:
            reg.setdefault(ind["variable_name"], ind)
    return reg


# ── 1. rows describe themselves ────────────────────────────────────────────────

def check_rows_self_describing(obs: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_OBS_COLUMNS - set(obs.columns))
    if missing:
        record("1.1 panel rows carry their own identity", "FAIL",
               f"observations.csv lacks {missing} — the interface would have to "
               f"look these up, which is where the two sides drift apart")
        return
    blank = obs[obs["display_name"].isna() | (obs["display_name"] == "")]
    if not blank.empty:
        record("1.1 panel rows carry their own identity", "FAIL",
               f"{len(blank)} rows have no display_name")
    else:
        record("1.1 panel rows carry their own identity", "PASS",
               f"{len(obs)} rows carry name, series code and value together")


def check_identity_matches_registry(obs: pd.DataFrame, registry: dict) -> None:
    """A row's stated identity must equal the registry's."""
    seen = obs[["variable_name", "display_name", "series_code"]].drop_duplicates()
    bad, unknown = [], []
    for r in seen.itertuples():
        spec = registry.get(r.variable_name)
        if spec is None:
            unknown.append(r.variable_name)
            continue
        if r.display_name != spec.get("display_name"):
            bad.append(f"{r.variable_name}: name '{r.display_name}' != "
                       f"registry '{spec.get('display_name')}'")
        if r.series_code != spec.get("series_code"):
            bad.append(f"{r.variable_name}: series '{r.series_code}' != "
                       f"registry '{spec.get('series_code')}'")
    if unknown:
        record("1.2 no orphan indicators", "FAIL",
               f"{len(unknown)} indicators not in the registry", sorted(set(unknown)))
    else:
        record("1.2 no orphan indicators", "PASS",
               f"all {len(seen)} indicators trace to a registry definition")
    if bad:
        record("1.3 identity matches the registry", "FAIL",
               f"{len(bad)} mismatches", bad)
    else:
        record("1.3 identity matches the registry", "PASS",
               f"{len(seen)} indicators agree on name and series code")


def check_bundle_complete(bundle: dict, registry: dict) -> None:
    required = {"run", "pillars", "indicators", "countries", "methods", "weights"}
    gaps = sorted(required - set(bundle))
    if gaps:
        record("1.4 bundle carries what the interface needs", "FAIL",
               f"missing top-level keys: {gaps}")
        return
    run = bundle["run"]
    for k in ("panel_start", "panel_end", "reference_year"):
        if k not in run:
            record("1.4 bundle carries what the interface needs", "FAIL",
                   f"run block missing {k}")
            return
    scoring_registry = {v for v, s in registry.items()
                        if s.get("role", "scoring") == "scoring"}
    scoring_bundle = {v for v, m in bundle["indicators"].items()
                      if m.get("role") == "scoring"}
    if scoring_registry != scoring_bundle:
        record("1.4 bundle carries what the interface needs", "FAIL",
               f"scoring set differs: only-registry={sorted(scoring_registry - scoring_bundle)}, "
               f"only-bundle={sorted(scoring_bundle - scoring_registry)}")
    else:
        record("1.4 bundle carries what the interface needs", "PASS",
               f"{len(bundle['countries'])} countries, {len(scoring_bundle)} scoring "
               f"indicators, reference year {run['reference_year']}")


# ── 2. the interface derives nothing ───────────────────────────────────────────

def _ui_files():
    """
    Every Python file under the interface, at any depth.

    `glob` rather than `rglob` meant these checks saw only the top level. The
    obvious next refactor is splitting app.py into a `views/` package, which
    would have silently disabled all three of them — a gate that switches itself
    off during the change it exists to police is worse than no gate at all.
    """
    return sorted(UI_DIR.rglob("*.py"))


def check_no_hardcoded_counts() -> None:
    """
    Counts shown to a reader must come from the data.

    The header once claimed "36 Indicators" for weeks after the number changed.
    Only string literals are inspected, so comments may still discuss the old bug.
    """
    # A digit near a domain noun, tolerating connective words in between.
    #
    # The previous pattern demanded two-or-three digits followed immediately by
    # the noun. That caught "36 Indicators" — the bug it was written for — while
    # passing "54 of 55 AU member states" (live in this interface at the time),
    # "7 pillars" (one digit) and "32 scoring indicators" (an intervening word).
    pattern = re.compile(
        # One to three digits only. Every count in this domain is under 1000,
        # and the word boundaries keep "2024 country coverage" — a year, not a
        # count — from matching on its trailing digits.
        r"\b\d{1,3}\b"
        r"(?:[\s,]+(?:of|the|AU|African|Union|scoring|total|all)\b)*"
        r"[\s,]+(indicators?|countries|country|pillars?|member\s+states)\b",
        re.IGNORECASE)
    offenders = []
    for path in _ui_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if pattern.search(node.value):
                    offenders.append(
                        f"{path.relative_to(UI_DIR)}:{node.lineno}: {node.value[:60]!r}")
    if offenders:
        record("2.1 no hardcoded counts in the interface", "FAIL",
               f"{len(offenders)} literal counts — derive these from the data", offenders)
    else:
        record("2.1 no hardcoded counts in the interface", "PASS",
               "no literal indicator/country/pillar counts in UI strings")


def check_ui_does_not_redefine_canonicals() -> None:
    canonical = {"PILLAR_DEFS", "WEIGHT_PRESETS", "ISLAND_SET", "COUNTRIES"}
    offenders = []
    for path in _ui_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # Walk the whole tree, not just module level, and cover annotated and
        # augmented assignment. `PILLAR_DEFS: dict = {}`, a class attribute and
        # a rebind inside a function all passed the module-level-Assign version.
        assigned: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                assigned |= {t.id for t in node.targets if isinstance(t, ast.Name)}
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
                if isinstance(node.target, ast.Name):
                    assigned.add(node.target.id)
        for name in sorted(canonical & assigned):
            offenders.append(f"{path.relative_to(UI_DIR)}: {name}")
    if offenders:
        record("2.2 interface imports canonical constants", "FAIL",
               "canonical values redefined in the UI", offenders)
    else:
        record("2.2 interface imports canonical constants", "PASS",
               "the interface imports every canonical constant")


def check_ui_reads_only_through_the_data_layer() -> None:
    """
    asi/dashboard/data.py is the only door to stored results.

    A view module reading a CSV or the panel directory itself would be deriving
    its own view of the data, outside anything verify/panel.py checks.

    Matched on the syntax tree rather than by substring: a docstring discussing
    `read_csv` is not a read, and a call in a subdirectory is. The scope stays
    the panel — the stored results verify/panel.py re-derives. Reading the
    context YAMLs or the narrative corpus is a different store under a different
    rule, and this check deliberately says nothing about it.
    """
    readers = {"read_csv", "read_excel", "read_parquet", "read_json"}
    offenders = []
    for path in _ui_files():
        if path.name == "data.py":
            continue
        rel = path.relative_to(UI_DIR)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                if name in readers:
                    offenders.append(f"{rel}:{node.lineno}: calls {name}()")
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                for needle in ("data/panel", "06_results"):
                    if needle in node.value:
                        offenders.append(
                            f"{rel}:{node.lineno}: names storage directly ({needle})")
    if offenders:
        record("2.3 interface reads only through the data layer", "FAIL",
               f"{len(offenders)} direct reads", offenders)
    else:
        record("2.3 interface reads only through the data layer", "PASS",
               "all view code goes through asi.dashboard.data")


# ── Entry point ────────────────────────────────────────────────────────────────

def run() -> int:
    print("=" * 78)
    print("CONTRACT -- backend/frontend object identity")
    print("=" * 78)

    missing = [p for p in (BUNDLE, OBSERVATIONS) if not p.exists()]
    if missing:
        record("0 inputs present", "FAIL",
               f"missing {[str(p.relative_to(_REPO)) for p in missing]} "
               f"-- run 02_panel.py first")
        return 1

    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    obs = pd.read_csv(OBSERVATIONS)
    registry = load_registry()

    check_rows_self_describing(obs)
    check_identity_matches_registry(obs, registry)
    check_bundle_complete(bundle, registry)
    check_no_hardcoded_counts()
    check_ui_does_not_redefine_canonicals()
    check_ui_reads_only_through_the_data_layer()

    n_fail = sum(1 for c in CHECKS if c["status"] == "FAIL")
    n_pass = sum(1 for c in CHECKS if c["status"] == "PASS")
    print("-" * 78)
    print(f"contract: {n_pass} PASS  {n_fail} FAIL")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(run())
