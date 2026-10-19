"""
verify/contract.py — the backend/frontend object contract. Gates a release.

    A health indicator is the same object on the server and in the interface,
    carrying its own name, series code, year and value. The interface renders
    what the backend emitted and derives nothing.

verify/panel.py already proves the numbers reconcile. This layer proves the
*identity* survives the crossing.

Its second section, which scanned the Dash interface for hardcoded counts,
redefined canonicals and direct panel reads, was retired with Dash (P73,
2026-10-19); the code is at the tag `archive/dash-2026-10`.

Ported to the panel in Phase C.

Run:  python verify/contract.py
"""

import sys as _sys
from pathlib import Path as _Path

_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_REPO))

import json

import pandas as pd
import yaml

PANEL_DIR      = _REPO / "data" / "panel"
BUNDLE         = PANEL_DIR / "bundle.json"
OBSERVATIONS   = PANEL_DIR / "observations.csv"
INDICATORS_DIR = _REPO / "indicators_list"

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
    obs = pd.read_csv(OBSERVATIONS, float_precision="round_trip")
    registry = load_registry()

    check_rows_self_describing(obs)
    check_identity_matches_registry(obs, registry)
    check_bundle_complete(bundle, registry)

    n_fail = sum(1 for c in CHECKS if c["status"] == "FAIL")
    n_pass = sum(1 for c in CHECKS if c["status"] == "PASS")
    print("-" * 78)
    print(f"contract: {n_pass} PASS  {n_fail} FAIL")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(run())
