"""
02_clean.py — Clean and aggregate raw pull data.

Input:  data/01_raw_pull.xlsx   (raw_data sheet)
Output: data/02_clean.xlsx

Steps:
  1.  Aggregate: per-indicator year window + aggregation function
      → one value per (iso3, variable_name)
  1a. Stage-1 fill: for countries missing in target window, apply the same
      aggregation function to the 5-year buffer before year_start.
      Previously (pre-Stage 1 fix) this always took the single most-recent
      value regardless of the indicator's aggregation setting, meaning
      average_recent_3 and average_recent_5 indicators were incorrectly filled
      with a single-year value. Fix: _agg_group is now called on the lookback
      slice with the same aggregation method as the primary window.
  1b. Per-capita derivation: displaced_persons (SM.POP.IDPC) is converted from
      absolute count to IDPs per 1,000 population using population_total
      (SP.POP.TOTL). This step runs after Stage-1 fill but before Stage-2 fill,
      so that Stage-2 regional means are computed on per-capita values.
      Rationale: OECD Handbook (2008) §3 comparability criterion; UNHCR (2023)
      standard metric for cross-country displacement comparison.
  2.  Stage-2 fill: regional mean, requires MIN_REGIONAL_SAMPLE peers with data
  3.  Stage-3: leave remaining NaN; flagged in coverage_report
  3b. IQR Winsorisation on scoring indicators (cap, IQR_MULTIPLIER=2.0)
  4.  Diagnostics: Cronbach's Alpha + Spearman correlation per pillar

Run from the project root:
    python 02_clean.py
"""

import sys
import logging
import time as _time

import numpy as np
import pandas as pd
from pathlib import Path

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── Imports ────────────────────────────────────────────────────────────────────

from config import (
    PillarRegistry, IndicatorRegistry,
    COVERAGE_WARN_THRESHOLD, COVERAGE_ALERT_THRESHOLD,
    MIN_REGIONAL_SAMPLE, IQR_MULTIPLIER,
    MAX_PILLAR_NAN_RATE, MIN_CRONBACH_ALPHA,
)
from models.countries import COUNTRIES

INPUT_FILE  = Path("data/01_raw_pull.xlsx")
OUTPUT_DIR  = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "02_clean.xlsx"

# ── Registry ───────────────────────────────────────────────────────────────────

pr = PillarRegistry()
ir = IndicatorRegistry(pr)

if not ir.validate_all():
    logger.error("Registry validation failed — run python setup.py to diagnose.")
    sys.exit(1)

indicators = ir.build_indicators()
pillars    = ir.build_pillars(indicators)

iso3_list      = list(COUNTRIES.keys())
iso3_to_region = {iso3: meta["region"] for iso3, meta in COUNTRIES.items()}

scoring_vars = {k for k, v in indicators.items() if v.role == "scoring"}

logger.info(
    "Indicators: %d total (%d scoring, %d descriptive)  |  Countries: %d",
    len(indicators), len(scoring_vars), len(indicators) - len(scoring_vars), len(iso3_list),
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _agg_group(sub: pd.DataFrame, agg: str) -> float:
    """
    Reduce a pre-sorted, NaN-free (iso3, var) slice to a single float.
    sub is sorted ascending by year; NaN rows already dropped by caller.
    """
    if sub.empty:
        return float("nan")
    vals = sub["value"].values
    if agg == "most_recent":
        return float(vals[-1])
    elif agg == "average":
        return float(np.mean(vals))
    elif agg == "average_recent_3":
        return float(np.mean(vals[-3:]))
    elif agg == "average_recent_5":
        return float(np.mean(vals[-5:]))
    raise ValueError(f"Unknown aggregation '{agg}'")


def cronbach_alpha(mat: pd.DataFrame) -> float:
    """
    Cronbach's alpha for a country × indicator matrix.
    Uses only rows that are complete (no NaN across all columns).
    """
    complete = mat.dropna()
    k = complete.shape[1]
    if k < 2 or complete.shape[0] < 3:
        return float("nan")
    var_items = complete.var(ddof=1).sum()
    var_total = complete.sum(axis=1).var(ddof=1)
    if var_total == 0:
        return float("nan")
    return float((k / (k - 1)) * (1 - var_items / var_total))


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    t_total = _time.perf_counter()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load raw data ─────────────────────────────────────────────────────────

    logger.info("Reading %s ...", INPUT_FILE)
    raw_df = pd.read_excel(INPUT_FILE, sheet_name="raw_data")
    raw_df["year"] = pd.to_numeric(raw_df["year"], errors="coerce").astype("Int64")
    logger.info("  %d rows loaded", len(raw_df))

    # ── Step 1: Aggregate + Stage-1 extended look-back fill ──────────────────

    logger.info("")
    logger.info("Step 1 — Aggregation + Stage-1 extended look-back fill...")

    agg_vals     = {}   # (iso3, var_name) -> float
    fill_records = []

    for var_name, ind in indicators.items():
        y_start = ind.year_start
        y_end   = ind.year_end
        agg     = ind.aggregation

        sub      = raw_df[raw_df["variable_name"] == var_name].sort_values("year")
        target   = sub[(sub["year"] >= y_start) & (sub["year"] <= y_end)]
        extended = sub[(sub["year"] >= y_start - 5) & (sub["year"] < y_start)]

        for iso3 in iso3_list:
            t_sub = target[target["iso3"] == iso3].dropna(subset=["value"])
            val   = _agg_group(t_sub, agg)

            if np.isnan(val):
                e_sub = extended[extended["iso3"] == iso3].dropna(subset=["value"])
                if not e_sub.empty:
                    val = _agg_group(e_sub, agg)
                    fill_year = int(e_sub.iloc[-1]["year"])
                    fill_records.append({
                        "variable_name": var_name,
                        "iso3":          iso3,
                        "fill_stage":    "stage1_extended",
                        "fill_year":     fill_year,
                        "fill_value":    round(val, 6),
                    })

            agg_vals[(iso3, var_name)] = val

    n_s1 = sum(1 for r in fill_records if r["fill_stage"] == "stage1_extended")
    logger.info("  Stage-1 fills: %d", n_s1)

    # ── Step 1b: Per-capita derivation ────────────────────────────────────────
    # displaced_persons (SM.POP.IDPC) is pulled as an absolute count.
    # Convert to IDPs per 1,000 population using population_total (SP.POP.TOTL).
    # Runs here — after Stage-1 fill on the raw values but before Stage-2 fill —
    # so that Stage-2 regional means are computed on per-capita values, not
    # absolute counts. A regional mean of absolute counts would be biased toward
    # the population sizes of the peer countries, not their displacement rates.

    if "displaced_persons" in indicators and "population_total" in indicators:
        logger.info("")
        logger.info("Step 1b — Per-capita derivation: displaced_persons / population * 1000 ...")
        n_converted = 0
        n_missing_pop = 0
        for iso3 in iso3_list:
            idp = agg_vals.get((iso3, "displaced_persons"), float("nan"))
            pop = agg_vals.get((iso3, "population_total"), float("nan"))
            if np.isnan(idp):
                continue
            if np.isnan(pop) or pop <= 0:
                n_missing_pop += 1
                agg_vals[(iso3, "displaced_persons")] = float("nan")
            else:
                agg_vals[(iso3, "displaced_persons")] = (idp / pop) * 1000.0
                n_converted += 1
        logger.info("  Converted: %d countries.  No population data: %d countries.",
                    n_converted, n_missing_pop)
    else:
        logger.info("Step 1b — Skipping per-capita derivation (displaced_persons or "
                    "population_total not in indicator set).")

    # ── Step 2: Pivot to wide, then Stage-2 regional mean fill ───────────────

    wide_df = pd.DataFrame(
        [{"iso3": iso3, **{vn: agg_vals[(iso3, vn)] for vn in indicators}}
         for iso3 in iso3_list]
    )

    logger.info("")
    logger.info("Step 2 — Stage-2 regional mean fill (min %d countries per region)...",
                MIN_REGIONAL_SAMPLE)

    wide_df["_region"] = wide_df["iso3"].map(iso3_to_region)
    s2_fills = 0

    for var_name in indicators:
        for region, grp in wide_df.groupby("_region"):
            have   = grp[var_name].notna()
            n_have = int(have.sum())
            n_need = int((~have).sum())

            if n_need == 0 or n_have < MIN_REGIONAL_SAMPLE:
                continue

            region_mean = float(grp.loc[have, var_name].mean())
            fill_idx    = grp.index[~have]
            wide_df.loc[fill_idx, var_name] = region_mean
            s2_fills += n_need

            for iso3 in wide_df.loc[fill_idx, "iso3"]:
                fill_records.append({
                    "variable_name": var_name,
                    "iso3":          iso3,
                    "fill_stage":    "stage2_regional",
                    "fill_year":     None,
                    "fill_value":    round(region_mean, 6),
                })

    wide_df = wide_df.drop(columns=["_region"])
    logger.info("  Stage-2 fills: %d", s2_fills)

    ind_cols  = [v for v in indicators if v in wide_df.columns]
    n_nan_rem = int(wide_df[ind_cols].isna().sum().sum())
    logger.info("  Remaining NaN (Stage-3, left as-is): %d cells", n_nan_rem)

    # ── Step 3: Coverage report (post-fill) ──────────────────────────────────

    n_total  = len(iso3_list)
    cov_rows = []

    for var_name, ind in indicators.items():
        n_valid = int(wide_df[var_name].notna().sum()) if var_name in wide_df.columns else 0
        pct     = n_valid / n_total
        flag    = ""
        if pct < COVERAGE_ALERT_THRESHOLD:
            flag = "VERY SPARSE"
        elif pct < COVERAGE_WARN_THRESHOLD:
            flag = "SPARSE"

        cov_rows.append({
            "variable_name": var_name,
            "display_name":  ind.display_name,
            "role":          ind.role,
            "pillars":       ",".join(ind.pillars),
            "n_valid":       n_valid,
            "n_total":       n_total,
            "pct_coverage":  round(pct, 3),
            "flag":          flag,
        })

    coverage_df = pd.DataFrame(cov_rows).sort_values("pct_coverage", ascending=True)

    very_sparse = coverage_df[coverage_df["flag"] == "VERY SPARSE"]
    sparse      = coverage_df[coverage_df["flag"] == "SPARSE"]
    full_cov    = coverage_df[coverage_df["flag"] == ""]

    logger.info("")
    logger.info("[COVERAGE REPORT — post fill]")
    if not very_sparse.empty:
        logger.warning("  VERY SPARSE (< %.0f%%): %d indicator(s)",
                       COVERAGE_ALERT_THRESHOLD * 100, len(very_sparse))
        for _, r in very_sparse.iterrows():
            logger.warning("    %-36s  %3.0f%%  (%d/%d countries)",
                           r["variable_name"], r["pct_coverage"] * 100,
                           r["n_valid"], n_total)
    if not sparse.empty:
        logger.warning("  SPARSE      (< %.0f%%): %d indicator(s)",
                       COVERAGE_WARN_THRESHOLD * 100, len(sparse))
        for _, r in sparse.iterrows():
            logger.warning("    %-36s  %3.0f%%  (%d/%d countries)",
                           r["variable_name"], r["pct_coverage"] * 100,
                           r["n_valid"], n_total)
    logger.info("  Full coverage (>= %.0f%%): %d indicator(s)",
                COVERAGE_WARN_THRESHOLD * 100, len(full_cov))

    # ── Step 4: IQR Winsorisation (scoring indicators only) ──────────────────

    logger.info("")
    logger.info("Step 3 — IQR Winsorisation (multiplier=%.1f, scoring only)...",
                IQR_MULTIPLIER)

    wins_rows = []

    for var_name in scoring_vars:
        if var_name not in wide_df.columns:
            continue
        col = wide_df[var_name].dropna()
        if col.empty:
            continue

        q1, q3 = float(col.quantile(0.25)), float(col.quantile(0.75))
        iqr    = q3 - q1
        lo     = q1 - IQR_MULTIPLIER * iqr
        hi     = q3 + IQR_MULTIPLIER * iqr

        n_lo = int((wide_df[var_name] < lo).sum())
        n_hi = int((wide_df[var_name] > hi).sum())

        wide_df[var_name] = wide_df[var_name].clip(lower=lo, upper=hi)

        if n_lo or n_hi:
            logger.info("  %-36s  lo_cap=%d  hi_cap=%d  bounds=[%.4f, %.4f]",
                        var_name, n_lo, n_hi, lo, hi)

        wins_rows.append({
            "variable_name":  var_name,
            "q1":             round(q1, 4),
            "q3":             round(q3, 4),
            "iqr":            round(iqr, 4),
            "lower_bound":    round(lo, 4),
            "upper_bound":    round(hi, 4),
            "n_capped_low":   n_lo,
            "n_capped_high":  n_hi,
        })

    wins_df = (pd.DataFrame(wins_rows) if wins_rows else
               pd.DataFrame(columns=["variable_name", "q1", "q3", "iqr",
                                     "lower_bound", "upper_bound",
                                     "n_capped_low", "n_capped_high"]))

    # ── Pillar NaN rate gate ──────────────────────────────────────────────────
    # Halt if any pillar has > MAX_PILLAR_NAN_RATE of countries with no data.
    # Missing-data is correlated with fragility: a pillar going blank mid-run
    # indicates a data pull failure, not a real-world signal.

    logger.info("")
    logger.info("Step 3b — Pillar NaN rate gate (threshold=%.0f%%)...",
                MAX_PILLAR_NAN_RATE * 100)
    gate_failures = []
    for key, pillar in sorted(pillars.items()):
        scoring_inds = pillar.get_scoring_indicators()
        cols = [ind.variable_name for ind in scoring_inds
                if ind.variable_name in wide_df.columns]
        if not cols:
            continue
        all_nan_mask = wide_df[cols].isna().all(axis=1)
        nan_rate = float(all_nan_mask.sum()) / n_total
        if nan_rate > MAX_PILLAR_NAN_RATE:
            logger.error(
                "  GATE FAIL: Pillar %s — %.1f%% of countries have no pillar data "
                "(limit %.0f%%). Possible data pull failure for series: %s",
                key, nan_rate * 100, MAX_PILLAR_NAN_RATE * 100, cols,
            )
            gate_failures.append(key)
        elif nan_rate > 0:
            logger.warning("  Pillar %s — %.1f%% of countries lack all indicators",
                           key, nan_rate * 100)
    if gate_failures:
        logger.error(
            "Pipeline halted — pillars %s exceed the NaN rate threshold. "
            "Re-run 01_pull.py or check World Bank series codes.", gate_failures,
        )
        sys.exit(1)
    logger.info("  All pillars within NaN rate threshold.")

    # ── Step 5: Diagnostics (Cronbach + Spearman per pillar) ─────────────────

    logger.info("")
    logger.info("Step 4 — Pillar diagnostics (Cronbach's Alpha + Spearman)...")

    diag_rows    = []
    spearman_dfs = {}

    for key, pillar in sorted(pillars.items()):
        scoring_inds = pillar.get_scoring_indicators()
        cols = [ind.variable_name for ind in scoring_inds
                if ind.variable_name in wide_df.columns]

        if len(cols) < 2:
            logger.warning("  Pillar %s — only %d column(s), skipping", key, len(cols))
            continue

        mat        = wide_df[cols].copy()
        alpha      = cronbach_alpha(mat)
        n_complete = int(mat.dropna().shape[0])

        if not np.isnan(alpha) and alpha < MIN_CRONBACH_ALPHA:
            logger.warning(
                "  Pillar %s — alpha=%.3f is below MIN_CRONBACH_ALPHA=%.2f. "
                "Indicators may not be measuring the same construct.",
                key, alpha, MIN_CRONBACH_ALPHA,
            )
        else:
            logger.info(
                "  Pillar %s — %d indicators  |  %2d complete countries  |  alpha=%.3f",
                key, len(cols), n_complete,
                alpha if not np.isnan(alpha) else float("nan"),
            )

        diag_rows.append({
            "pillar":         key,
            "n_indicators":   len(cols),
            "n_complete_obs": n_complete,
            "cronbach_alpha": round(alpha, 4) if not np.isnan(alpha) else None,
        })

        spearman_dfs[f"spearman_{key}"] = mat.corr(method="spearman").round(3)

    diag_df = pd.DataFrame(diag_rows)

    # ── Write output ──────────────────────────────────────────────────────────

    logger.info("")
    logger.info("Writing %s ...", OUTPUT_FILE)

    fill_log_df = (pd.DataFrame(fill_records) if fill_records else
                   pd.DataFrame(columns=["variable_name", "iso3",
                                         "fill_stage", "fill_year", "fill_value"]))

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        coverage_df.to_excel(writer, sheet_name="coverage_report", index=False)
        wide_df.to_excel(writer,     sheet_name="clean_data",      index=False)
        fill_log_df.to_excel(writer, sheet_name="fill_log",        index=False)
        diag_df.to_excel(writer,     sheet_name="diagnostics",     index=False)
        wins_df.to_excel(writer,     sheet_name="winsorisation",   index=False)
        for sh_name, corr_df in spearman_dfs.items():
            corr_df.to_excel(writer, sheet_name=sh_name[:31])

    elapsed = _time.perf_counter() - t_total
    logger.info("Done in %.1fs.", elapsed)
    logger.info("Output: %s", OUTPUT_FILE.resolve())
    logger.info("Sheets: coverage_report | clean_data | fill_log | diagnostics | winsorisation | spearman_[A-G]")
    logger.info("Next step: python 03_normalize.py")
