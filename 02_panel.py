"""
02_panel.py — build the yearly panel and score it.

Replaces the old 02_clean -> 03_normalize -> 04_score chain for the panel era.
Those three stages each collapsed or re-anchored the data in ways that made a
time series impossible; this runs the whole sequence once, on every year.

    inputs (data/inputs.csv, from Athena's datasets)
      -> panel        one value per country/indicator/year, with provenance
      -> derived      GPI parity folding, IDP per capita
      -> missing      a gap stays a gap (edition 2; --missing-at-regional-quantile for the sensitivity run)
      -> goalposts    fixed bounds (frozen; --freeze-goalposts to regenerate)
      -> normalize    log -> winsorize -> goalpost min-max, clamping flagged
      -> score        pillar + composite scores, each with a reliability tier

Usage
    python 02_panel.py --freeze-goalposts   # first run, or a deliberate re-anchor
    python 02_panel.py                      # normal run, loads frozen bounds

Outputs (data/panel/)
    observations.csv    the panel: value, provenance, score per country-year
    pillar_scores.csv   pillar scores with coverage and reliability
    composites.csv      composite scores per method per year
    weights.yaml        frozen PCA/entropy weights
"""

import argparse
import logging
import sys
import time as _time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from asi.core.constants import (
    PANEL_START, DEFAULT_MAX_CARRY_FORWARD, IQR_MULTIPLIER, MIN_REGIONAL_SAMPLE,
    PILLAR_DEFS, WEIGHT_PRESETS, ACTIVE_PRESET, SMALL,
    RELIABILITY_RELIABLE_AT, RELIABILITY_THIN_AT, RELIABILITY_MAX_IMPUTED,
    MIN_PILLARS_FOR_COMPOSITE, DISPLAY_DECIMALS, REFERENCE_YEAR_MIN_COVERAGE,
)
from asi.core.countries import COUNTRIES
from asi.core.registry import PillarRegistry, IndicatorRegistry
from asi.core.schema import Reliability
from asi.pipeline import panel as panel_mod
from asi.pipeline import goalposts as gp_mod
from asi.pipeline import normalize as norm_mod
from asi.pipeline import score as score_mod

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s",
                    stream=sys.stdout)
logger = logging.getLogger(__name__)


INPUTS         = Path("data/inputs.csv")
OUT_DIR        = Path("data/panel")
GOALPOSTS_FILE = Path("registry/goalposts.yaml")
WEIGHTS_FILE   = OUT_DIR / "weights.yaml"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--freeze-goalposts", action="store_true",
                    help="recompute and overwrite the frozen goalposts "
                         "(re-anchors every historical score — do this deliberately)")
    ap.add_argument("--freeze-new-goalposts", action="store_true",
                    help="freeze goalposts for indicators the file lacks, leaving every existing one as it is (N1)")
    ap.add_argument("--missing-at-regional-quantile", type=float, metavar="Q",
                    help="sensitivity run only: fill every gap with its region's Q quantile that year "
                         "(plan 4.5 asks for 0.25); needs --out, so the published outputs are untouched")
    ap.add_argument("--out", help="write the outputs here instead of data/panel")
    args = ap.parse_args()
    if args.missing_at_regional_quantile is not None and not args.out:
        ap.error("a sensitivity run must write elsewhere: add --out")

    global OUT_DIR, WEIGHTS_FILE
    if args.out:
        OUT_DIR, WEIGHTS_FILE = Path(args.out), Path(args.out) / "weights.yaml"
    t0 = _time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── registry ──────────────────────────────────────────────────────────────
    ir = IndicatorRegistry(PillarRegistry())
    if not ir.validate_all():
        logger.error("Registry validation failed.")
        return 1
    specs = {i["variable_name"]: i for i in ir.list_indicators()}
    scoring = {v: s for v, s in specs.items() if s.get("role", "scoring") == "scoring"}
    logger.info("Registry: %d indicators (%d scoring)", len(specs), len(scoring))

    # ── raw ───────────────────────────────────────────────────────────────────
    # data/inputs.csv is Athena's common format, written by 01_inputs.py from the
    # edition's datasets; each World Bank series maps to its registry variable.
    if not INPUTS.exists():
        logger.error("%s not found — run 01_inputs.py first.", INPUTS)
        return 1
    inputs = pd.read_csv(INPUTS, dtype={"TIME_PERIOD": str}, float_precision="round_trip")
    # A series may feed more than one variable: growth is read as its 3-year mean and as its 10-year volatility.
    variables = pd.DataFrame([(s["series_code"], v) for v, s in specs.items()], columns=["SERIES", "variable_name"])
    inputs = inputs.merge(variables, on="SERIES", how="inner", validate="many_to_many")
    raw = pd.DataFrame({"iso3": inputs["REF_AREA"], "variable_name": inputs["variable_name"],
                        "year": inputs["TIME_PERIOD"].astype(int), "value": inputs["OBS_VALUE"]})
    # The bundle is dated by its data, not by the day it was built, so the same
    # inputs always give the same bytes: the newest edition among the datasets.
    # Only names that end in a date count: UCDP's datasets are named by version (ucdp-cy-26.1).
    as_of = max(name[-10:] for name in inputs["DATASET"].unique()
                if pd.notna(pd.to_datetime(name[-10:], format="%Y-%m-%d", errors="coerce")))
    panel_end = int(raw["year"].max())
    years = range(PANEL_START, panel_end + 1)
    logger.info("Raw: %d observations | panel %d-%d", len(raw), PANEL_START, panel_end)

    # ── 1. panel ──────────────────────────────────────────────────────────────
    logger.info("Step 1 - build panel")
    pnl = panel_mod.build_panel(
        raw, specs, list(COUNTRIES), years, DEFAULT_MAX_CARRY_FORWARD
    )
    counts = pnl["provenance"].value_counts()
    logger.info("  %d cells | observed=%d carried_forward=%d absent=%d",
                len(pnl), counts.get("observed", 0),
                counts.get("carried_forward", 0), counts.get("absent", 0))

    # ── 2. derived transforms ─────────────────────────────────────────────────
    logger.info("Step 2 - derived transforms")
    pnl, notes = panel_mod.apply_derived(pnl, specs)
    for n in notes:
        logger.info("  %s", n)

    # ── 3. missing data ───────────────────────────────────────────────────────
    # Edition 2, step 2 (plan 4.5): no regional fill. A value is observed, or carried forward up to
    # DEFAULT_MAX_CARRY_FORWARD years, or missing; a pillar scores on what is present, with its tier. The states
    # least able to report are the least stable, so a regional mean flattered them.
    q = args.missing_at_regional_quantile
    if q is None:
        logger.info("Step 3 - no regional fill: a gap stays a gap (edition 2, plan 4.5)")
    else:
        logger.info("Step 3 - SENSITIVITY: gaps set to the region's %.2f quantile (min %d peers, same year)",
                    q, MIN_REGIONAL_SAMPLE)
        iso3_to_region = {k: v["region"] for k, v in COUNTRIES.items()}
        pnl, n_filled = panel_mod.regional_fill(pnl, iso3_to_region, MIN_REGIONAL_SAMPLE, statistic=q)
        logger.info("  filled %d cells from regional peers", n_filled)
    still_missing = int(pnl["raw_value"].isna().sum())
    logger.info("  %d cells remain empty (left empty on purpose)", still_missing)

    # ── 4. goalposts ──────────────────────────────────────────────────────────
    # `--freeze-goalposts` and nothing else. The condition here used to read
    # `or not GOALPOSTS_FILE.exists()`, which quietly undid the rule the
    # goalposts module states in its own docstring: a deleted, gitignored or
    # never-committed registry/goalposts.yaml re-anchored every historical score
    # against the current panel, and the run logged it as an ordinary step. The
    # scores that came out would look entirely normal and would not be
    # comparable with any previously published edition.
    if args.freeze_goalposts:
        logger.info("Step 4 - computing and FREEZING goalposts (re-anchors every historical score)")
        gps = gp_mod.compute(pnl, scoring, IQR_MULTIPLIER)
        gp_mod.freeze(gps, GOALPOSTS_FILE, panel_years=(PANEL_START, panel_end))
        theory = sorted(v for v, b in gps.items() if b["goalpost_source"] == "theoretical")
        logger.info("  froze %d indicators -> %s; theoretical bounds for %d: %s", len(gps), GOALPOSTS_FILE,
                    len(theory), theory)
        capped = {v: b["n_capped_low"] + b["n_capped_high"] for v, b in gps.items()
                  if b["n_capped_low"] + b["n_capped_high"]}
        logger.info("  observed values beyond 3 trimmed SDs, replaced at 3.1: %s", capped)
    elif args.freeze_new_goalposts:
        # N1: an added indicator gets goalposts; every existing indicator keeps its own, so history stays put
        merged, added = gp_mod.add_new(gp_mod.load(GOALPOSTS_FILE), gp_mod.compute(pnl, scoring, IQR_MULTIPLIER))
        gp_mod.freeze(merged, GOALPOSTS_FILE, panel_years=(PANEL_START, panel_end))
        logger.info("Step 4 - goalposts added for new indicators only: %s", added or "none")
    else:
        logger.info("Step 4 - loading frozen goalposts")
    gps = gp_mod.load(GOALPOSTS_FILE)

    # ── 5. normalize ──────────────────────────────────────────────────────────
    logger.info("Step 5 - normalize against fixed goalposts")
    pnl, notes = norm_mod.normalize_panel(pnl, gps)
    for n in notes:
        logger.info("  %s", n)

    # ── 6. pillar scores ──────────────────────────────────────────────────────
    logger.info("Step 6 - pillar scores with reliability")
    pillar_map: dict[str, list[str]] = {p: [] for p in PILLAR_DEFS}
    for var, spec in scoring.items():
        for p in spec.get("pillars", []):
            if p in pillar_map:
                pillar_map[p].append(var)

    pil = score_mod.pillar_scores(
        pnl, pillar_map,
        reliable_at=RELIABILITY_RELIABLE_AT,
        thin_at=RELIABILITY_THIN_AT,
        max_imputed_share=RELIABILITY_MAX_IMPUTED,
    )
    tiers = pil[pil["score"].notna()]["reliability"].value_counts()
    logger.info("  %d pillar-years | reliable=%d thin=%d unreliable=%d",
                int(pil["score"].notna().sum()), tiers.get("reliable", 0),
                tiers.get("thin", 0), tiers.get("unreliable", 0))

    # ── 7. composites ─────────────────────────────────────────────────────────
    logger.info("Step 7 - composite scores")
    # Edition 2, step 7 (plan 4.1): an unreliable pillar does not enter any composite; the rest are averaged, and
    # each composite reports how many pillars it used (k) and an INFORM-style lack-of-reliability index.
    wide = score_mod.composite_inputs(pil)
    pillars = [p for p in PILLAR_DEFS if p in wide.columns]
    n_pillars = wide.notna().sum(axis=1)
    lri = score_mod.lack_of_reliability(pnl, list(scoring), DEFAULT_MAX_CARRY_FORWARD)
    left_out = int((pil["score"].notna() & ~pil["reliability"].isin(score_mod.COMPOSABLE)).sum())
    logger.info("  %d unreliable pillar-years left out of the composites", left_out)

    # data-driven weights fitted ONCE on the pooled panel, then reused every year
    pca_w = score_mod.fit_pca_weights(wide, pillars, SMALL)
    ent_w = score_mod.fit_entropy_weights(wide, pillars, SMALL)
    equal_w = {p: WEIGHT_PRESETS[ACTIVE_PRESET][p] for p in pillars}
    with open(WEIGHTS_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump({
            "note": ("Fitted once on the pooled panel and reused for every year. "
                     "Refitting per year would move a country's score because the "
                     "weighting changed rather than because the country did."),
            "equal": {k: float(v) for k, v in equal_w.items()},
            "pca": {k: round(float(v), 6) for k, v in pca_w.items()},
            "entropy": {k: round(float(v), 6) for k, v in ent_w.items()},
        }, f, sort_keys=False)
    logger.info("  PCA weights:     %s", {k: round(v, 3) for k, v in pca_w.items()})
    logger.info("  Entropy weights: %s", {k: round(v, 3) for k, v in ent_w.items()})

    comps = {
        "equal":     score_mod.weighted_composite(wide, equal_w),
        "pca":       score_mod.weighted_composite(wide, pca_w),
        "entropy":   score_mod.weighted_composite(wide, ent_w),
        "geometric": score_mod.geometric_composite(wide, pillars, SMALL),
    }

    rel_by_key = {
        key: score_mod.composite_reliability(grp, MIN_PILLARS_FOR_COMPOSITE)
        for key, grp in pil.groupby(["iso3", "year"], sort=False)
    }

    rows = []
    for method, series in comps.items():
        for (iso3, year), value in series.items():
            rel = rel_by_key.get((iso3, year), Reliability.ABSENT)
            rows.append({
                "iso3": iso3, "year": int(year), "method": method,
                "score": None if pd.isna(value) else round(float(value), DISPLAY_DECIMALS),
                "reliability": rel.value,
                "n_pillars": int(n_pillars.get((iso3, year), 0)),
                "lack_of_reliability": round(float(lri.get((iso3, year), 10.0)), DISPLAY_DECIMALS),
            })
    comp_df = pd.DataFrame(rows)

    # ranks within each year and method, best = 1, computed only over displayable rows
    comp_df["rank"] = pd.NA
    for (year, method), grp in comp_df.groupby(["year", "method"], sort=False):
        usable = grp[grp["score"].notna() &
                     grp["reliability"].isin(["reliable", "thin"])]
        ranks = usable["score"].rank(ascending=False, method="min")
        comp_df.loc[ranks.index, "rank"] = ranks.astype("Int64")

    # ── 8. reference year ─────────────────────────────────────────────────────
    # The newest year is not automatically the year to show. World Bank series
    # report with a lag, so the final panel year is typically near-empty: the
    # dashboard must not open on a year where nothing is scoreable. The
    # reference year is the latest year in which most countries have a
    # displayable composite — computed, never hardcoded.
    eq = comp_df[comp_df["method"] == "equal"]
    n_countries = len(COUNTRIES)
    coverage_by_year = (
        eq[eq["rank"].notna()].groupby("year").size() / n_countries
    )
    eligible = coverage_by_year[coverage_by_year >= REFERENCE_YEAR_MIN_COVERAGE]
    reference_year = int(eligible.index.max()) if not eligible.empty else panel_end
    logger.info("Step 8 - reference year: %d "
                "(latest year with >=%.0f%% of countries scoreable; panel ends %d)",
                reference_year, REFERENCE_YEAR_MIN_COVERAGE * 100, panel_end)
    if reference_year != panel_end:
        logger.info("  %d-%d are present but too sparse to score and will display greyed",
                    reference_year + 1, panel_end)

    with open(OUT_DIR / "panel_meta.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump({
            "panel_start": PANEL_START,
            "panel_end": panel_end,
            "reference_year": reference_year,
            "note": ("reference_year is the latest year with at least 80% of "
                     "countries scoreable. Later years exist in the panel but are "
                     "too sparse to score and must render greyed, not blank."),
            "coverage_by_year": {
                int(y): round(float(v), 3) for y, v in coverage_by_year.items()
            },
        }, f, sort_keys=False)

    # ── 9. write ──────────────────────────────────────────────────────────────
    # Identity columns travel with every value. The dashboard must be able to
    # render a row without consulting the registry: a row IS the Observation.
    # Denormalised on purpose — the alternative is a UI-side lookup, which is
    # exactly where the frontend and backend drift apart.
    logger.info("Step 9 - write")
    identity = pd.DataFrame([
        {
            "variable_name": v,
            "display_name":  s.get("display_name", v),
            "series_code":   s.get("series_code", ""),
            "database":      s.get("database", ""),
            "polarity":      s.get("polarity", "positive"),
            "role":          s.get("role", "scoring"),
        }
        for v, s in specs.items()
    ])
    pnl = pnl.merge(identity, on="variable_name", how="left")
    ordered = [
        "iso3", "variable_name", "display_name", "series_code", "database",
        "year", "raw_value", "transformed_value", "score",
        "provenance", "source_year", "polarity", "role", "clamped",
    ]
    pnl = pnl[[c for c in ordered if c in pnl.columns]]
    pnl.to_csv(OUT_DIR / "observations.csv", index=False)
    pil.to_csv(OUT_DIR / "pillar_scores.csv", index=False)
    comp_df.to_csv(OUT_DIR / "composites.csv", index=False)
    logger.info("  %s", OUT_DIR / "observations.csv")
    logger.info("  %s", OUT_DIR / "pillar_scores.csv")
    logger.info("  %s", OUT_DIR / "composites.csv")

    # ── 10. UI metadata bundle ────────────────────────────────────────────────
    # Deliberately small: it carries identity and structure, not values. The
    # values live in the panel tables, already computed, and the UI filters them
    # rather than deriving anything. A single JSON holding 44,550 indicator-years
    # would be tens of megabytes and would tempt the UI into recomputation.
    import json
    bundle = {
        "run": {
            "generated": as_of,
            "panel_start": PANEL_START,
            "panel_end": panel_end,
            "reference_year": reference_year,
        },
        "pillars": {
            p: {"name": name, "indicators": pillar_map.get(p, [])}
            for p, name in PILLAR_DEFS.items()
        },
        "indicators": {
            v: {
                "display_name": s.get("display_name", v),
                "series_code":  s.get("series_code", ""),
                "database":     s.get("database", ""),
                "polarity":     s.get("polarity", "positive"),
                "role":         s.get("role", "scoring"),
                "pillars":      s.get("pillars", []),
                "log_transform": bool(s.get("log_transform", False)),
                "transform":    s.get("transform"),
                "justification": s.get("justification", ""),
            }
            for v, s in specs.items()
        },
        "countries": {
            iso3: {
                "name":   meta["name"],
                "region": meta["region"],
                "recs":   meta["rec"],
                "island_state": iso3 in __import__(
                    "asi.core.constants", fromlist=["ISLAND_SET"]
                ).ISLAND_SET,
            }
            for iso3, meta in COUNTRIES.items()
        },
        "methods": sorted(comp_df["method"].unique().tolist()),
        "weights": {"equal": equal_w, "pca": pca_w, "entropy": ent_w},
        "coverage_by_year": {
            int(y): round(float(v), 3) for y, v in coverage_by_year.items()
        },
    }
    with open(OUT_DIR / "bundle.json", "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=1, ensure_ascii=False)
    logger.info("  %s (metadata only; values stay in the panel tables)",
                OUT_DIR / "bundle.json")

    latest = comp_df[(comp_df["year"] == reference_year) & (comp_df["method"] == "equal")]
    shown = latest[latest["rank"].notna()].sort_values("rank")
    logger.info("")
    logger.info("Equal-weight top 5 in %d (reference year):", reference_year)
    for _, r in shown.head(5).iterrows():
        logger.info("  #%-2s %-4s %5.1f  (%s)", r["rank"], r["iso3"],
                    r["score"], r["reliability"])
    logger.info("Bottom 3:")
    for _, r in shown.tail(3).iterrows():
        logger.info("  #%-2s %-4s %5.1f  (%s)", r["rank"], r["iso3"],
                    r["score"], r["reliability"])

    logger.info("Done in %.1fs", _time.time() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
