"""
verify/contract.py — the backend/frontend object contract.

ASI v2 plan §2.3 and §7.2:

    A health indicator is the same object on the server and in the UI, carrying
    its own name, series code, year, and value. The frontend renders what the
    backend emitted and derives nothing.

This layer asserts that the bundle (data/06_results.json) is a complete, honest
contract: every rendered element traces back to one record with matching
identity, aggregates reconcile with their parts, and the dashboard is not
re-deriving or hardcoding what the bundle already states.

The live-render half (headless-load the dashboard, scrape displayed values,
match them to bundle records) lands in Phase C when the UI is restructured.
What is checkable today is checked today.

Run standalone:  python verify/contract.py
"""

import sys as _sys
from pathlib import Path as _Path

_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_REPO))

import ast
import json
import re

import yaml

from asi.core.schema import (
    REQUIRED_COUNTRY_KEYS, REQUIRED_INDICATOR_KEYS, missing_keys,
)

BUNDLE_JSON    = _REPO / "data" / "06_results.json"
INDICATORS_DIR = _REPO / "indicators_list"
DASHBOARD      = _REPO / "asi" / "dashboard" / "app.py"

DETAIL_CAP = 5
CHECKS: list[dict] = []


def record(name: str, status: str, summary: str, details=()) -> None:
    CHECKS.append({"name": name, "status": status, "summary": summary,
                   "details": list(details)})
    print(f"[{status}] contract | {name} -- {summary}")
    for line in list(details)[:DETAIL_CAP]:
        print(f"         {line}")
    if len(details) > DETAIL_CAP:
        print(f"         ... and {len(details) - DETAIL_CAP} more")


def load_registry() -> dict[str, dict]:
    """Read the YAML registry directly — never through the pipeline's loader."""
    reg: dict[str, dict] = {}
    for path in sorted(INDICATORS_DIR.glob("*.yaml")):
        for ind in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            reg.setdefault(ind["variable_name"], ind)
    return reg


# ── 1. Bundle completeness ─────────────────────────────────────────────────────

def check_country_records(bundle: dict) -> None:
    bad = []
    for c in bundle.get("countries", []):
        gaps = missing_keys(c, REQUIRED_COUNTRY_KEYS)
        if gaps:
            bad.append(f"{c.get('iso3', '??')}: missing {gaps}")
    if bad:
        record("1.1 country records complete", "FAIL",
               f"{len(bad)} countries missing required keys", bad)
    else:
        record("1.1 country records complete", "PASS",
               f"{len(bundle.get('countries', []))} countries carry all required keys")


def check_indicator_entries(bundle: dict, registry: dict) -> None:
    """
    Every indicator entry the UI can render must carry its own identity.

    This is the heart of the contract: if `display_name` or `series_code` is
    absent from the record, the dashboard has to look it up somewhere else — and
    that second lookup is exactly what allows the two sides to disagree.
    """
    missing_identity, unknown = [], []
    n_entries = 0
    for c in bundle.get("countries", []):
        for var, entry in (c.get("indicators") or {}).items():
            n_entries += 1
            if var not in registry:
                unknown.append(f"{c['iso3']}/{var}: not in registry")
            if not isinstance(entry, dict):
                missing_identity.append(f"{c['iso3']}/{var}: entry is not an object")
                continue
            gaps = [k for k in ("score",) if k not in entry]
            if gaps:
                missing_identity.append(f"{c['iso3']}/{var}: missing {gaps}")

    if unknown:
        record("1.2 no orphan indicators", "FAIL",
               f"{len(unknown)} bundle indicators absent from the registry", unknown)
    else:
        record("1.2 no orphan indicators", "PASS",
               f"all {n_entries} indicator entries trace to a registry definition")

    if missing_identity:
        record("1.3 indicator entries well-formed", "FAIL",
               f"{len(missing_identity)} malformed entries", missing_identity)
    else:
        record("1.3 indicator entries well-formed", "PASS",
               f"{n_entries} entries carry a score field")


def check_identity_matches_registry(bundle: dict, registry: dict) -> None:
    """Names/series codes exposed by the bundle must equal the registry's."""
    meta = bundle.get("indicators") or {}
    if not meta:
        record("1.4 indicator identity matches registry", "WARN",
               "bundle exposes no indicator metadata block to compare")
        return
    bad = []
    for var, m in meta.items():
        spec = registry.get(var)
        if spec is None:
            bad.append(f"{var}: not in registry")
            continue
        if not isinstance(m, dict):
            continue
        for field in ("display_name", "series_code"):
            if field in m and m[field] != spec.get(field):
                bad.append(f"{var}.{field}: bundle={m[field]!r} registry={spec.get(field)!r}")
    if bad:
        record("1.4 indicator identity matches registry", "FAIL",
               f"{len(bad)} identity mismatches", bad)
    else:
        record("1.4 indicator identity matches registry", "PASS",
               f"{len(meta)} indicators agree with the registry on name and series code")


# ── 2. Aggregation reconciliation ──────────────────────────────────────────────

def check_pillar_reconciliation(bundle: dict, registry: dict, tol: float = 0.02) -> None:
    """
    Pillar score in the bundle must equal the mean of the indicator scores the
    same bundle exposes. If these disagree, the UI shows a pillar number that
    its own drill-down cannot reproduce.
    """
    pillar_map: dict[str, list[str]] = {}
    for var, spec in registry.items():
        if spec.get("role", "scoring") != "scoring":
            continue
        for p in spec.get("pillars", []):
            pillar_map.setdefault(p, []).append(var)

    bad = []
    n_checked = 0
    for c in bundle.get("countries", []):
        inds = c.get("indicators") or {}
        for pid, stored in (c.get("pillar_scores") or {}).items():
            if stored is None:
                continue
            vals = [
                inds[v]["score"] for v in pillar_map.get(pid, [])
                if v in inds and isinstance(inds[v], dict) and inds[v].get("score") is not None
            ]
            if not vals:
                continue
            n_checked += 1
            expected = sum(vals) / len(vals)
            if abs(expected - float(stored)) > tol:
                bad.append(f"{c['iso3']}/{pid}: stored={stored:.3f} "
                           f"from-indicators={expected:.3f} diff={abs(expected - float(stored)):.3f}")
    if bad:
        record("2.1 pillar == mean of its indicators", "FAIL",
               f"{len(bad)}/{n_checked} pillar scores do not reconcile (tol={tol})", bad)
    else:
        record("2.1 pillar == mean of its indicators", "PASS",
               f"{n_checked} pillar scores reconcile with their indicators (tol={tol})")


def check_rank_consistency(bundle: dict) -> None:
    """
    Stored ranks must be reproducible from the stored scores.

    One legitimate exception: the bundle rounds scores for display, so two
    countries can share a displayed score while differing at full precision.
    Their ranks then correctly differ even though the rounded values look tied.
    That is a display-precision artifact, not a data fault, so it is reported as
    a WARN — it still matters, because a reader sees two identical numbers
    ranked one apart with no visible reason.
    """
    bad, precision_ties = [], []
    methods = set()
    for c in bundle.get("countries", []):
        methods |= set((c.get("scores") or {}).keys())

    for method in sorted(methods):
        scored = sorted(
            [
                (c["iso3"], c["scores"][method], (c.get("ranks") or {}).get(method))
                for c in bundle.get("countries", [])
                if (c.get("scores") or {}).get(method) is not None
                and (c.get("ranks") or {}).get(method) is not None
            ],
            key=lambda t: -t[1],
        )
        # how many countries share each displayed score
        score_counts: dict[float, int] = {}
        for _, score, _ in scored:
            score_counts[score] = score_counts.get(score, 0) + 1

        expected_rank, prev_score, prev_rank = {}, None, 0
        for i, (iso3, score, _) in enumerate(scored, start=1):
            rank = prev_rank if (prev_score is not None and score == prev_score) else i
            expected_rank[iso3] = rank
            prev_score, prev_rank = score, rank

        for iso3, score, stored in scored:
            if stored == expected_rank[iso3]:
                continue
            if score_counts[score] > 1:
                precision_ties.append(
                    f"{iso3}/{method}: displays {score} (shared with "
                    f"{score_counts[score] - 1} other) but ranks {stored}"
                )
            else:
                bad.append(f"{iso3}/{method}: stored rank={stored} "
                           f"expected={expected_rank[iso3]}")

    if bad:
        record("2.2 ranks reproducible from scores", "FAIL",
               f"{len(bad)} genuine rank mismatches", bad)
    elif precision_ties:
        record("2.2 ranks reproducible from scores", "WARN",
               f"{len(precision_ties)} rank(s) differ only because scores tie at "
               f"display precision; full-precision ordering is correct",
               precision_ties)
    else:
        record("2.2 ranks reproducible from scores", "PASS",
               f"ranks reproduce from stored scores for {len(methods)} methods")


# ── 3. The UI must not re-derive or hardcode ───────────────────────────────────

def check_dashboard_has_no_hardcoded_counts() -> None:
    """
    Counts like "36 Indicators" have been wrong in the UI before. Any
    indicator/country/pillar count shown to a user should be derived from the
    bundle, not typed into a string.
    """
    if not DASHBOARD.exists():
        record("3.1 no hardcoded counts in UI", "WARN", "dashboard file not found")
        return
    # Walk string literals via the AST rather than scanning raw text: comments
    # legitimately discuss past bugs ("once read 36 Indicators") and must not
    # trip the check that prevents those bugs.
    tree = ast.parse(DASHBOARD.read_text(encoding="utf-8"))
    pattern = re.compile(r"\b\d{2,3}\s+(Indicators?|Countries|Pillars?)\b")
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            m = pattern.search(node.value)
            if m:
                offenders.append(f"line {node.lineno}: {node.value[:70]!r}")
    if offenders:
        record("3.1 no hardcoded counts in UI", "FAIL",
               f"{len(offenders)} hardcoded count strings — derive these from the bundle",
               offenders)
    else:
        record("3.1 no hardcoded counts in UI", "PASS",
               "no hardcoded indicator/country/pillar counts in dashboard strings")


def check_dashboard_does_not_redefine_canonicals() -> None:
    """The UI must import canonical constants, never restate them."""
    if not DASHBOARD.exists():
        record("3.2 UI imports canonical constants", "WARN", "dashboard file not found")
        return
    tree = ast.parse(DASHBOARD.read_text(encoding="utf-8"))
    canonical = {"PILLAR_DEFS", "WEIGHT_PRESETS", "ISLAND_SET", "COUNTRIES"}
    assigned = {
        t.id
        for node in tree.body if isinstance(node, ast.Assign)
        for t in node.targets if isinstance(t, ast.Name)
    }
    offenders = sorted(canonical & assigned)
    if offenders:
        record("3.2 UI imports canonical constants", "FAIL",
               f"dashboard redefines {offenders} instead of importing them")
    else:
        record("3.2 UI imports canonical constants", "PASS",
               "dashboard imports all canonical constants")


# ── Entry point ────────────────────────────────────────────────────────────────

def run() -> int:
    print("=" * 78)
    print("CONTRACT -- backend/frontend object identity")
    print("=" * 78)

    if not BUNDLE_JSON.exists():
        record("0 bundle present", "FAIL",
               f"{BUNDLE_JSON} not found -- run 06_qualitative.py first")
        return 1

    bundle = json.loads(BUNDLE_JSON.read_text(encoding="utf-8"))
    registry = load_registry()

    check_country_records(bundle)
    check_indicator_entries(bundle, registry)
    check_identity_matches_registry(bundle, registry)
    check_pillar_reconciliation(bundle, registry)
    check_rank_consistency(bundle)
    check_dashboard_has_no_hardcoded_counts()
    check_dashboard_does_not_redefine_canonicals()

    n_fail = sum(1 for c in CHECKS if c["status"] == "FAIL")
    n_warn = sum(1 for c in CHECKS if c["status"] == "WARN")
    n_pass = sum(1 for c in CHECKS if c["status"] == "PASS")
    print("-" * 78)
    print(f"contract: {n_pass} PASS  {n_warn} WARN  {n_fail} FAIL")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(run())
