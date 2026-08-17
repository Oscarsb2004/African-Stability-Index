"""
verify/panel.py — independent re-derivation of the time-series panel.

Gates a release. The pipeline's panel is only trustworthy if a second
implementation, written differently, lands on the same numbers.

Independence measures taken here:
  - carry-forward is re-derived with pandas `merge_asof` (a backward as-of join)
    rather than the pipeline's per-country dictionary scan
  - reliability tiers are re-implemented from the written rules, not imported
  - pillar means and composites are recomputed with plain numpy
  - the registry is read straight from YAML, never through asi.core.registry

Only asi.core.constants is imported, for threshold values — those are
declarations, not logic. Re-typing them here would test nothing except my
ability to copy numbers.

Run standalone:  python verify/panel.py
"""

import sys as _sys
from pathlib import Path as _Path

_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_REPO))

import numpy as np
import pandas as pd
import yaml

from asi.core.constants import (
    PANEL_START, DEFAULT_MAX_CARRY_FORWARD, MIN_REGIONAL_SAMPLE,
    RELIABILITY_RELIABLE_AT, RELIABILITY_THIN_AT, RELIABILITY_MAX_IMPUTED,
    PILLAR_DEFS, DISPLAY_DECIMALS, SMALL,
)

PANEL_DIR      = _REPO / "data" / "panel"
BASELINE       = _REPO / "data" / "baseline" / "01_raw_pull_BASELINE.xlsx"
GOALPOSTS      = _REPO / "registry" / "goalposts.yaml"
INDICATORS_DIR = _REPO / "indicators_list"
COUNTRIES_PY   = _REPO / "asi" / "core" / "countries.py"

DETAIL_CAP = 5
CHECKS: list[dict] = []


def record(name: str, status: str, summary: str, details=()) -> None:
    CHECKS.append({"name": name, "status": status, "summary": summary})
    print(f"[{status}] panel | {name} -- {summary}")
    for line in list(details)[:DETAIL_CAP]:
        print(f"         {line}")
    if len(details) > DETAIL_CAP:
        print(f"         ... and {len(details) - DETAIL_CAP} more")


def load_registry() -> dict[str, dict]:
    reg = {}
    for p in sorted(INDICATORS_DIR.glob("*.yaml")):
        for ind in yaml.safe_load(p.read_text(encoding="utf-8")) or []:
            reg.setdefault(ind["variable_name"], ind)
    return reg


def load_countries() -> dict[str, dict]:
    ns: dict = {}
    exec(compile(COUNTRIES_PY.read_text(encoding="utf-8"), str(COUNTRIES_PY), "exec"), ns)
    return ns["COUNTRIES"]


# ── 1. panel construction, re-derived with merge_asof ──────────────────────────

def check_panel_values(obs: pd.DataFrame, registry: dict, countries: dict) -> None:
    """
    Re-derive every MOST_RECENT panel cell using a backward as-of join.

    `merge_asof` matches each panel year to the nearest earlier observation,
    which is carry-forward expressed as a join instead of a scan — a genuinely
    different route to the same answer.
    """
    raw = pd.read_excel(BASELINE, sheet_name="raw_data")
    raw["year"] = pd.to_numeric(raw["year"], errors="coerce")
    raw = raw.dropna(subset=["year", "value"])
    raw["year"] = raw["year"].astype(int)

    years = sorted(obs["year"].unique())
    # only indicators whose value is taken as-is (no rolling mean, no transform,
    # no per-capita derivation) can be compared directly against the raw series
    simple = [
        v for v, s in registry.items()
        if s.get("aggregation") == "most_recent"
        and not s.get("transform")
        and v != "displaced_persons"
    ]

    mismatches, n_checked = [], 0
    for var in simple:
        src = raw[raw["variable_name"] == var]
        if src.empty:
            continue
        got = obs[obs["variable_name"] == var]
        for iso3 in countries:
            s = src[src["iso3"] == iso3][["year", "value"]].sort_values("year")
            if s.empty:
                continue
            grid = pd.DataFrame({"year": years})
            joined = pd.merge_asof(grid, s, on="year", direction="backward")
            joined["staleness"] = joined["year"] - pd.merge_asof(
                grid, s.assign(src_year=s["year"])[["year", "src_year"]],
                on="year", direction="backward",
            )["src_year"]
            # expire carry-forward exactly as the rules state
            joined.loc[joined["staleness"] > DEFAULT_MAX_CARRY_FORWARD, "value"] = np.nan

            actual = got[got["iso3"] == iso3].set_index("year")["raw_value"]
            for _, row in joined.iterrows():
                yr = int(row["year"])
                if yr not in actual.index:
                    continue
                a = actual.loc[yr]
                # regional fill legitimately supplies values this check cannot
                # predict; compare only where the pipeline used the country's own data
                prov = got[(got["iso3"] == iso3) & (got["year"] == yr)]["provenance"]
                if prov.empty or prov.iloc[0] == "regional_mean":
                    continue
                e = row["value"]
                n_checked += 1
                if pd.isna(e) and pd.isna(a):
                    continue
                if pd.isna(e) != pd.isna(a) or abs(float(e) - float(a)) > 1e-9:
                    mismatches.append(f"{iso3}/{var}/{yr}: expected={e} actual={a}")

    if mismatches:
        record("1.1 panel values (re-derived via merge_asof)", "FAIL",
               f"{len(mismatches)}/{n_checked} cells differ", mismatches)
    else:
        record("1.1 panel values (re-derived via merge_asof)", "PASS",
               f"{n_checked} cells match an independent as-of join")


def check_carry_forward_expiry(obs: pd.DataFrame) -> None:
    """No cell may be carried forward beyond the stated limit."""
    cf = obs[obs["provenance"] == "carried_forward"].dropna(subset=["source_year"])
    stale = cf[(cf["year"] - cf["source_year"]) > DEFAULT_MAX_CARRY_FORWARD]
    if not stale.empty:
        record("1.2 carry-forward expiry honoured", "FAIL",
               f"{len(stale)} cells exceed {DEFAULT_MAX_CARRY_FORWARD} years",
               [f"{r.iso3}/{r.variable_name}/{int(r.year)} from {int(r.source_year)}"
                for r in stale.head(DETAIL_CAP).itertuples()])
    else:
        record("1.2 carry-forward expiry honoured", "PASS",
               f"{len(cf)} carried-forward cells all within {DEFAULT_MAX_CARRY_FORWARD} years")


def check_no_lookahead(obs: pd.DataFrame) -> None:
    """A value must never come from the future."""
    have = obs.dropna(subset=["source_year"])
    future = have[have["source_year"] > have["year"]]
    if not future.empty:
        record("1.3 no lookahead", "FAIL", f"{len(future)} cells sourced from a later year")
    else:
        record("1.3 no lookahead", "PASS", "no cell draws on a future observation")


# ── 2. normalization against frozen goalposts ──────────────────────────────────

def check_scores_within_bounds(obs: pd.DataFrame) -> None:
    scored = obs.dropna(subset=["score"])
    bad = scored[(scored["score"] < 0) | (scored["score"] > 100)]
    if not bad.empty:
        record("2.1 scores within [0,100]", "FAIL", f"{len(bad)} scores out of range")
    else:
        record("2.1 scores within [0,100]", "PASS",
               f"all {len(scored)} scores lie in [0,100]")


def check_clamping_is_real(obs: pd.DataFrame) -> None:
    """
    `clamped` must mean genuinely outside the frozen range, not rounding noise.

    Bounds are stored rounded outward for exactly this reason; if a clamp is
    smaller than the storage precision the flag has lost its meaning.
    """
    gp = yaml.safe_load(GOALPOSTS.read_text(encoding="utf-8"))["indicators"]
    trivial = []
    for var, b in gp.items():
        sub = obs[(obs["variable_name"] == var) & (obs["clamped"] == True)]  # noqa: E712
        for r in sub.itertuples():
            tv = r.transformed_value
            if pd.isna(tv):
                continue
            dev = max(tv - b["goalpost_max"], b["goalpost_min"] - tv)
            if dev < 1e-6:
                trivial.append(f"{r.iso3}/{var}/{int(r.year)}: deviation {dev:.2e}")
    n_clamped = int(obs["clamped"].sum())
    if trivial:
        record("2.2 clamping flags real excursions", "FAIL",
               f"{len(trivial)} of {n_clamped} clamps are within rounding noise",
               trivial)
    else:
        record("2.2 clamping flags real excursions", "PASS",
               f"{n_clamped} clamped cells all exceed storage precision")


# ── 3. pillar scores and reliability, re-implemented ───────────────────────────

def _tier(n_ind: int, n_obs: int, n_imp: int) -> str:
    """Reliability rules restated from the specification, not imported."""
    if n_ind <= 0 or (n_obs + n_imp) == 0:
        return "absent"
    if n_imp / (n_obs + n_imp) > RELIABILITY_MAX_IMPUTED:
        return "unreliable"
    coverage = n_obs / n_ind
    if coverage >= RELIABILITY_RELIABLE_AT:
        return "reliable"
    if coverage >= RELIABILITY_THIN_AT:
        return "thin"
    return "unreliable"


def check_pillar_scores(obs: pd.DataFrame, pil: pd.DataFrame, registry: dict) -> None:
    pillar_map: dict[str, list[str]] = {p: [] for p in PILLAR_DEFS}
    for var, spec in registry.items():
        if spec.get("role", "scoring") != "scoring":
            continue
        for p in spec.get("pillars", []):
            if p in pillar_map:
                pillar_map[p].append(var)

    scores = obs.set_index(["iso3", "year", "variable_name"])["score"]
    provs  = obs.set_index(["iso3", "year", "variable_name"])["provenance"]

    score_bad, tier_bad, n = [], [], 0
    for r in pil.itertuples():
        members = pillar_map.get(r.pillar_id, [])
        vals, n_obs, n_imp = [], 0, 0
        for var in members:
            key = (r.iso3, r.year, var)
            if key not in scores.index:
                continue
            v = scores.loc[key]
            p = provs.loc[key]
            if pd.notna(v):
                vals.append(float(v))
            if p in ("observed", "derived"):
                n_obs += 1
            elif p in ("carried_forward", "regional_mean", "interpolated"):
                n_imp += 1

        n += 1
        expected = float(np.mean(vals)) if vals else np.nan
        actual = r.score
        if pd.isna(expected) != pd.isna(actual) or (
            pd.notna(expected) and abs(expected - float(actual)) > 1e-6
        ):
            score_bad.append(f"{r.iso3}/{r.pillar_id}/{int(r.year)}: "
                             f"expected={expected} actual={actual}")

        expected_tier = _tier(len(members), n_obs, n_imp)
        if expected_tier != r.reliability:
            tier_bad.append(f"{r.iso3}/{r.pillar_id}/{int(r.year)}: "
                            f"expected={expected_tier} actual={r.reliability}")

    if score_bad:
        record("3.1 pillar = mean of its indicator scores", "FAIL",
               f"{len(score_bad)}/{n} mismatches", score_bad)
    else:
        record("3.1 pillar = mean of its indicator scores", "PASS",
               f"{n} pillar-years reconcile")

    if tier_bad:
        record("3.2 reliability tiers", "FAIL",
               f"{len(tier_bad)}/{n} tiers differ from the stated rules", tier_bad)
    else:
        record("3.2 reliability tiers", "PASS",
               f"{n} tiers match the specification")


# ── 4. composites ──────────────────────────────────────────────────────────────

def check_composites(pil: pd.DataFrame, comp: pd.DataFrame) -> None:
    weights = yaml.safe_load((PANEL_DIR / "weights.yaml").read_text(encoding="utf-8"))
    wide = pil.pivot_table(index=["iso3", "year"], columns="pillar_id",
                           values="score", aggfunc="first")

    bad, n = [], 0
    for method in ("equal", "pca", "entropy"):
        w = weights[method]
        sub = comp[comp["method"] == method]
        for r in sub.itertuples():
            key = (r.iso3, r.year)
            if key not in wide.index:
                continue
            row = wide.loc[key]
            pillars = [p for p in w if p in row.index]
            vals = np.array([row[p] for p in pillars], dtype=float)
            wv = np.array([w[p] for p in pillars], dtype=float)
            valid = ~np.isnan(vals)
            if not valid.any():
                continue
            ww = wv[valid] / wv[valid].sum()
            expected = round(float(np.dot(ww, vals[valid])), DISPLAY_DECIMALS)
            n += 1
            if pd.notna(r.score) and abs(expected - float(r.score)) > 10 ** -DISPLAY_DECIMALS:
                bad.append(f"{r.iso3}/{method}/{int(r.year)}: "
                           f"expected={expected} actual={r.score}")

    if bad:
        record("4.1 weighted composites", "FAIL", f"{len(bad)}/{n} mismatches", bad)
    else:
        record("4.1 weighted composites", "PASS",
               f"{n} composite scores reconcile with the frozen weights")


def check_geometric_composite(pil: pd.DataFrame, comp: pd.DataFrame) -> None:
    """
    The fourth published method, previously re-derived by nothing.

    check_composites loops over equal, pca and entropy only, so a quarter of
    every published composite row crossed the gate unexamined. Adding 40 points
    to a geometric score and re-running the suite passed; the same corruption on
    an equal-weight row failed.

    Independence here is arithmetic as well as structural. The pipeline computes
    exp(mean(ln x)); this takes the product and its n-th root. Same definition,
    different path — a transcription slip in either surfaces as disagreement
    rather than as two copies of one mistake. Scores are floored at SMALL for the
    same reason the pipeline floors them: a pillar at zero would otherwise send
    the whole composite to zero via ln(0).
    """
    wide = pil.pivot_table(index=["iso3", "year"], columns="pillar_id",
                           values="score", aggfunc="first")
    pillars = [p for p in PILLAR_DEFS if p in wide.columns]

    bad, n = [], 0
    for r in comp[comp["method"] == "geometric"].itertuples():
        key = (r.iso3, r.year)
        if key not in wide.index:
            continue
        row = wide.loc[key]
        vals = np.array([row[p] for p in pillars], dtype=float)
        vals = vals[~np.isnan(vals)]
        if vals.size == 0:
            continue
        floored = np.maximum(vals, SMALL)
        expected = round(float(np.prod(floored) ** (1.0 / floored.size)),
                         DISPLAY_DECIMALS)
        n += 1
        if pd.notna(r.score) and abs(expected - float(r.score)) > 10 ** -DISPLAY_DECIMALS:
            bad.append(f"{r.iso3}/geometric/{int(r.year)}: "
                       f"expected={expected} actual={r.score}")

    if bad:
        record("4.3 geometric composite", "FAIL", f"{len(bad)}/{n} mismatches", bad)
    else:
        record("4.3 geometric composite", "PASS",
               f"{n} geometric scores reconcile by product-and-root")


def check_ranks_only_where_displayable(comp: pd.DataFrame) -> None:
    """An unreliable score must not carry a rank: ranking implies a claim."""
    ranked_bad = comp[comp["rank"].notna() & ~comp["reliability"].isin(["reliable", "thin"])]
    if not ranked_bad.empty:
        record("4.2 ranks only where displayable", "FAIL",
               f"{len(ranked_bad)} unreliable scores carry a rank")
    else:
        record("4.2 ranks only where displayable", "PASS",
               "no unreliable score is ranked")


# ── Entry point ────────────────────────────────────────────────────────────────

def run() -> int:
    print("=" * 78)
    print("PANEL -- independent re-derivation of the time series")
    print("=" * 78)

    required = [PANEL_DIR / "observations.csv", PANEL_DIR / "pillar_scores.csv",
                PANEL_DIR / "composites.csv", GOALPOSTS, BASELINE]
    missing = [p for p in required if not p.exists()]
    if missing:
        record("0 inputs present", "FAIL",
               f"missing: {[str(p.relative_to(_REPO)) for p in missing]} "
               f"-- run 02_panel.py first")
        return 1

    obs = pd.read_csv(PANEL_DIR / "observations.csv")
    pil = pd.read_csv(PANEL_DIR / "pillar_scores.csv")
    comp = pd.read_csv(PANEL_DIR / "composites.csv")
    registry = load_registry()
    countries = load_countries()

    record("0 inputs present", "PASS",
           f"panel {obs['year'].min()}-{obs['year'].max()}, {len(obs)} cells, "
           f"{len(countries)} countries")

    check_panel_values(obs, registry, countries)
    check_carry_forward_expiry(obs)
    check_no_lookahead(obs)
    check_scores_within_bounds(obs)
    check_clamping_is_real(obs)
    check_pillar_scores(obs, pil, registry)
    check_composites(pil, comp)
    check_ranks_only_where_displayable(comp)
    check_geometric_composite(pil, comp)

    n_fail = sum(1 for c in CHECKS if c["status"] == "FAIL")
    n_warn = sum(1 for c in CHECKS if c["status"] == "WARN")
    n_pass = sum(1 for c in CHECKS if c["status"] == "PASS")
    print("-" * 78)
    print(f"panel: {n_pass} PASS  {n_warn} WARN  {n_fail} FAIL")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(run())
