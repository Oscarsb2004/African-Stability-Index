"""
03_normalize.py — Normalize cleaned indicator values to [0, 100].

Input:  data/02_clean.xlsx  (clean_data sheet)
Output: data/03_norm.xlsx

Steps:
  1. Load cleaned values and indicator metadata (polarity, log_transform)
  2. For log_transform indicators: apply log1p to compress right-skewed distributions
  3. Polarity-aware min-max normalization to [0, 100] per indicator:
       positive polarity: score = (x - min) / (max - min) * 100
       negative polarity: score = (max - x) / (max - min) * 100
  4. Countries with NaN values at this stage receive NaN scores (not imputed)
  5. Write norm_data + norm_bounds (for reproducibility audit)

Methodological note:
  log1p is applied before min-max so that extreme right-tailed distributions
  (e.g. GDP per capita) do not compress the majority of countries into a narrow
  band. This follows OECD Handbook (2008) §6.2 recommendation.
  Polarity inversion at the normalization step (not a sign flip in raw data)
  ensures all final scores are "higher = more stable" throughout the pipeline.

Run from the project root:
    python 03_normalize.py
"""

import sys
import logging
import time as _time

import numpy as np
import pandas as pd
import yaml
from pathlib import Path

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────

INDICATORS_DIR = Path("indicators_list")
INPUT_FILE     = Path("data/02_clean.xlsx")
OUTPUT_DIR     = Path("data")
OUTPUT_FILE    = OUTPUT_DIR / "03_norm.xlsx"


# ── Indicator metadata ─────────────────────────────────────────────────────────

def load_indicator_meta() -> dict[str, dict]:
    """
    Returns {variable_name: {polarity, log_transform, role, pillars}} for all
    indicators defined in indicators_list/*.yaml.
    """
    meta: dict[str, dict] = {}
    for path in sorted(INDICATORS_DIR.glob("*.yaml")):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue
        for ind in data:
            meta[ind["variable_name"]] = {
                "polarity":      ind.get("polarity", "positive"),
                "log_transform": bool(ind.get("log_transform", False)),
                "role":          ind.get("role", "scoring"),
                "pillars":       ind.get("pillars", []),
            }
    return meta


# ── Normalization ──────────────────────────────────────────────────────────────

def normalize_indicator(
    series: pd.Series,
    polarity: str,
    log_transform: bool,
) -> tuple[pd.Series, float, float, float | None, float | None]:
    """
    Normalize one indicator's value series to [0, 100].

    Returns:
        (norm_scores, x_min, x_max, log_x_min, log_x_max)
        log_x_* are None when log_transform is False.
    """
    x = series.copy().astype(float)

    log_x_min = log_x_max = None

    if log_transform:
        # Guard: log1p requires x >= -1; Winsorization in stage 02 should prevent
        # any negative values for log_transform indicators, but clip defensively.
        if (x.dropna() < 0).any():
            logger.warning(
                "Negative values found for a log_transform indicator — clipping to 0."
            )
            x = x.clip(lower=0)
        x = np.log1p(x)
        log_x_min = float(x.min(skipna=True))
        log_x_max = float(x.max(skipna=True))

    x_min = float(x.min(skipna=True))
    x_max = float(x.max(skipna=True))

    if x_max == x_min:
        # Zero-variance indicator: all countries have the same value — score = 50
        logger.warning("Zero variance indicator — assigning score=50 to all countries.")
        norm = x.where(x.isna(), 50.0)
        return norm, x_min, x_max, log_x_min, log_x_max

    if polarity == "negative":
        norm = (x_max - x) / (x_max - x_min) * 100.0
    else:
        norm = (x - x_min) / (x_max - x_min) * 100.0

    return norm, x_min, x_max, log_x_min, log_x_max


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    t0 = _time.time()
    logger.info("Step 1: Load cleaned data from %s", INPUT_FILE)

    if not INPUT_FILE.exists():
        logger.error("Input file not found: %s — run 02_clean.py first.", INPUT_FILE)
        sys.exit(1)

    # clean_data sheet is wide format: iso3 | _region | <var1> | <var2> | ...
    wide_raw = pd.read_excel(INPUT_FILE, sheet_name="clean_data")
    NON_INDICATOR_COLS = {"iso3", "_region"}
    indicator_cols = [c for c in wide_raw.columns if c not in NON_INDICATOR_COLS]
    wide = wide_raw.set_index("iso3")[indicator_cols]
    wide.columns.name = None

    logger.info("  Loaded %d countries, %d indicator columns",
                len(wide), len(indicator_cols))

    logger.info("Step 2: Load indicator metadata from %s", INDICATORS_DIR)
    meta = load_indicator_meta()
    logger.info("  %d indicators defined", len(meta))

    # Only normalize scoring indicators that appear in the cleaned data
    scoring_vars = [
        v for v in indicator_cols
        if meta.get(v, {}).get("role", "scoring") == "scoring"
    ]
    descriptive_vars = [v for v in indicator_cols if v not in scoring_vars]
    if descriptive_vars:
        logger.info("  Skipping %d descriptive (non-scoring) indicators: %s",
                    len(descriptive_vars), descriptive_vars)

    logger.info("Step 3: Normalize %d scoring indicators", len(scoring_vars))

    norm_records: list[dict] = []
    bounds_records: list[dict] = []

    for var in sorted(scoring_vars):
        if var not in wide.columns:
            logger.warning("  %s: no data in clean_data — skipped", var)
            continue

        ind_meta = meta.get(var, {"polarity": "positive", "log_transform": False})
        polarity      = ind_meta["polarity"]
        log_transform = ind_meta["log_transform"]

        n_valid = wide[var].notna().sum()
        n_total = len(wide[var])

        norm_scores, x_min, x_max, log_x_min, log_x_max = normalize_indicator(
            wide[var], polarity, log_transform
        )

        for iso3, score in norm_scores.items():
            norm_records.append({
                "iso3":          iso3,
                "variable_name": var,
                "norm_score":    round(float(score), 4) if pd.notna(score) else float("nan"),
            })

        bounds_records.append({
            "variable_name": var,
            "polarity":      polarity,
            "log_transform": log_transform,
            "raw_min":       round(x_min, 6),
            "raw_max":       round(x_max, 6),
            "log_min":       round(log_x_min, 6) if log_x_min is not None else None,
            "log_max":       round(log_x_max, 6) if log_x_max is not None else None,
            "n_valid":       int(n_valid),
            "n_total":       int(n_total),
            "pct_valid":     round(n_valid / n_total * 100, 1),
        })

        logger.info(
            "  %-40s polarity=%-8s log=%-5s  valid=%d/%d  "
            "score_range=[%.1f, %.1f]",
            var, polarity, str(log_transform),
            n_valid, n_total,
            norm_scores.min(skipna=True) if norm_scores.notna().any() else float("nan"),
            norm_scores.max(skipna=True) if norm_scores.notna().any() else float("nan"),
        )

    norm_df   = pd.DataFrame(norm_records)
    bounds_df = pd.DataFrame(bounds_records)

    logger.info("Step 4: Write output to %s", OUTPUT_FILE)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        norm_df.to_excel(writer, sheet_name="norm_data",   index=False)
        bounds_df.to_excel(writer, sheet_name="norm_bounds", index=False)

    logger.info("Done in %.1fs", _time.time() - t0)
    logger.info(
        "  norm_data:   %d rows (%d countries x %d indicators)",
        len(norm_df),
        norm_df["iso3"].nunique(),
        norm_df["variable_name"].nunique(),
    )

    # Quick sanity check: all norm_scores should be in [0, 100]
    out_of_range = norm_df[
        norm_df["norm_score"].notna() &
        ~norm_df["norm_score"].between(0.0, 100.0)
    ]
    if not out_of_range.empty:
        logger.error(
            "SANITY FAIL: %d scores outside [0, 100]:\n%s",
            len(out_of_range), out_of_range.head(10).to_string()
        )
    else:
        logger.info("  Sanity check passed: all scores in [0, 100].")


if __name__ == "__main__":
    main()
