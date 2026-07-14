"""
00_audit.py — Pipeline verification and methodology audit.

Checks every quantitative claim the pipeline makes against independent
recomputation from the raw data. Also flags structural design issues.

Outputs:
  data/audit_report.json  — machine-readable (consumed by dashboard Audit tab)
  console                 — human-readable summary

Run from the project root:
    python 00_audit.py
"""

import sys
import json
import math
import logging
import warnings
import time as _time
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import yaml

from constants import PILLAR_DEFS, SMALL

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────

CLEAN_FILE   = Path("data/02_clean.xlsx")
NORM_FILE    = Path("data/03_norm.xlsx")
SCORES_FILE  = Path("data/04_scores.xlsx")
RESULTS_JSON = Path("data/06_results.json")
IND_DIR      = Path("indicators_list")
OUTPUT_JSON  = Path("data/audit_report.json")

METHODS  = ["equal", "pca", "bod", "entropy", "geometric"]
# SCORE_FLOOR must match 04_score.py score_geometric (which uses SMALL as the clip floor).
# Using a larger value (e.g. 0.001) would shift log-scale values for low-scoring countries
# and cause spurious audit failures for countries with near-zero pillar scores.
SCORE_FLOOR = SMALL

# ── Helpers ────────────────────────────────────────────────────────────────────

def _pass(msg): return {"status": "PASS", "msg": msg}
def _warn(msg): return {"status": "WARN", "msg": msg}
def _fail(msg): return {"status": "FAIL", "msg": msg}
def _info(msg): return {"status": "INFO", "msg": msg}

def load_indicator_meta() -> dict:
    meta = {}
    for path in sorted(IND_DIR.glob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue
        for ind in data:
            vn = ind["variable_name"]
            if vn not in meta:
                meta[vn] = dict(ind)
            else:
                # Already defined (cross-listed) — merge pillars
                meta[vn]["pillars"] = list(set(meta[vn]["pillars"]) | set(ind.get("pillars", [])))
    return meta

def load_pillar_map(meta: dict) -> dict:
    pm = {k: [] for k in PILLAR_DEFS}
    for vn, info in meta.items():
        if info.get("role", "scoring") != "scoring":
            continue
        for p in info.get("pillars", []):
            if p in pm and vn not in pm[p]:
                pm[p].append(vn)
    return pm

# ── Check 0: File presence ─────────────────────────────────────────────────────

def check_file_presence() -> list:
    results = []
    files = {
        "02_clean.xlsx": CLEAN_FILE,
        "03_norm.xlsx":  NORM_FILE,
        "04_scores.xlsx": SCORES_FILE,
        "06_results.json": RESULTS_JSON,
    }
    for name, path in files.items():
        if path.exists():
            results.append(_pass(f"{name} exists ({path.stat().st_size // 1024} KB)"))
        else:
            results.append(_fail(f"{name} MISSING — run pipeline stages first"))
    return results

# ── Check 1: Normalization math ───────────────────────────────────────────────

def check_normalization(ind_meta: dict) -> list:
    """
    Independently recompute min-max normalization for all indicators and compare
    to the stored norm_data values. Reports max error across all countries.
    """
    results = []
    try:
        wide_raw = pd.read_excel(CLEAN_FILE, sheet_name="clean_data")
        norm_df  = pd.read_excel(NORM_FILE,  sheet_name="norm_data")
        bounds_df = pd.read_excel(NORM_FILE, sheet_name="norm_bounds")
    except Exception as e:
        return [_fail(f"Could not load data files: {e}")]

    wide = wide_raw.set_index("iso3").drop(columns=["_region"], errors="ignore")
    norm_pivot = norm_df.pivot(index="iso3", columns="variable_name", values="norm_score")

    bounds_map = bounds_df.set_index("variable_name").to_dict("index")

    max_err_overall = 0.0
    n_ok, n_bad = 0, 0
    bad_indicators = []

    for var, info in ind_meta.items():
        if info.get("role", "scoring") != "scoring":
            continue
        if var not in wide.columns or var not in norm_pivot.columns:
            continue

        polarity      = info.get("polarity", "positive")
        log_transform = bool(info.get("log_transform", False))

        x = wide[var].astype(float).copy()
        if log_transform:
            x = np.log1p(x.clip(lower=0))

        x_min = x.min(skipna=True)
        x_max = x.max(skipna=True)

        if x_max == x_min:
            recomp = x.where(x.isna(), 50.0)
        elif polarity == "negative":
            recomp = (x_max - x) / (x_max - x_min) * 100.0
        else:
            recomp = (x - x_min) / (x_max - x_min) * 100.0

        stored = norm_pivot[var]
        common = recomp.index.intersection(stored.index)
        diff = (recomp[common] - stored[common]).abs()
        max_err = diff.max(skipna=True)

        if np.isnan(max_err) or max_err < 0.01:
            n_ok += 1
        else:
            n_bad += 1
            bad_indicators.append((var, round(max_err, 4)))
        max_err_overall = max(max_err_overall, max_err if not np.isnan(max_err) else 0)

    if n_bad == 0:
        results.append(_pass(
            f"Normalization: all {n_ok} indicators match recomputed values (max error < 0.01)"
        ))
    else:
        results.append(_fail(
            f"Normalization: {n_bad} indicators differ from recomputed values. "
            f"Worst offenders: {bad_indicators[:5]}"
        ))

    # Sanity: all stored scores in [0, 100]
    out = norm_df[norm_df["norm_score"].notna() & ~norm_df["norm_score"].between(0, 100)]
    if out.empty:
        results.append(_pass("All normalized scores are within [0, 100]"))
    else:
        results.append(_fail(f"{len(out)} scores outside [0, 100]: {out.head(5).to_dict('records')}"))

    return results

# ── Check 2: Pillar score computation ─────────────────────────────────────────

def check_pillar_scores(ind_meta: dict, pillar_map: dict) -> list:
    results = []
    try:
        norm_df  = pd.read_excel(NORM_FILE, sheet_name="norm_data")

        pillar_raw = pd.read_excel(SCORES_FILE, sheet_name="Pillar Scores")
        pillar_raw.columns = [c.replace("\n", " ").strip() for c in pillar_raw.columns]
        if "ISO3" in pillar_raw.columns:
            pillar_raw = pillar_raw.rename(columns={"ISO3": "iso3"})
        pillar_raw = pillar_raw.set_index("iso3")
        # Map full name columns to letters
        full_to_letter = {f"{v} Score": k for k, v in PILLAR_DEFS.items()}
        pillar_scores_stored = pillar_raw[[c for c in pillar_raw.columns if c in full_to_letter]]
        pillar_scores_stored = pillar_scores_stored.rename(columns=full_to_letter)
    except Exception as e:
        return [_fail(f"Could not load pillar scores: {e}")]

    norm_pivot = norm_df.pivot(index="iso3", columns="variable_name", values="norm_score")

    n_ok, n_bad = 0, 0
    bad = []
    for p, vars_list in pillar_map.items():
        available = [v for v in vars_list if v in norm_pivot.columns]
        if not available or p not in pillar_scores_stored.columns:
            continue
        recomp = norm_pivot[available].mean(axis=1, skipna=True)
        # All-NaN rows → NaN
        all_nan = norm_pivot[available].isna().all(axis=1)
        recomp[all_nan] = float("nan")
        stored = pillar_scores_stored[p]
        common = recomp.index.intersection(stored.index)
        diff = (recomp[common] - stored[common]).abs()
        max_err = diff.max(skipna=True)
        if np.isnan(max_err) or max_err < 0.1:
            n_ok += 1
        else:
            n_bad += 1
            worst = diff.idxmax(skipna=True)
            bad.append(f"Pillar {p}: max_err={max_err:.2f} at {worst}")

    if n_bad == 0:
        results.append(_pass(f"Pillar scores: all {n_ok} pillars match recomputed means (tol 0.1)"))
    else:
        results.append(_fail(f"Pillar score mismatch in {n_bad} pillars: {bad}"))
    return results

# ── Check 3: Overall score methods ────────────────────────────────────────────

def check_overall_scores() -> list:
    results = []
    try:
        overall_raw = pd.read_excel(SCORES_FILE, sheet_name="Overall Rankings")
        overall_raw.columns = [c.replace("\n", " ").strip() for c in overall_raw.columns]
        if "ISO3" in overall_raw.columns:
            overall_raw = overall_raw.rename(columns={"ISO3": "iso3"})
        overall_raw = overall_raw.set_index("iso3")
        col_map = {
            "Equal Weights Score": "equal",
            "PCA Weights Score": "pca",
            "Benefit of Doubt Score": "bod",
            "Entropy Weights Score": "entropy",
            "Geometric Mean Score": "geometric",
        }
        overall = overall_raw.rename(columns=col_map)

        pillar_raw = pd.read_excel(SCORES_FILE, sheet_name="Pillar Scores")
        pillar_raw.columns = [c.replace("\n", " ").strip() for c in pillar_raw.columns]
        if "ISO3" in pillar_raw.columns:
            pillar_raw = pillar_raw.rename(columns={"ISO3": "iso3"})
        pillar_raw = pillar_raw.set_index("iso3")
        full_to_letter = {f"{v} Score": k for k, v in PILLAR_DEFS.items()}
        pillar_cols = [c for c in pillar_raw.columns if c in full_to_letter]
        pillar_scores = pillar_raw[pillar_cols].rename(columns=full_to_letter)
    except Exception as e:
        return [_fail(f"Could not load overall scores: {e}")]

    # 3a. Equal-weight check
    w = 1.0 / 7.0
    recomp_equal = pillar_scores[[p for p in PILLAR_DEFS if p in pillar_scores.columns]].mean(axis=1, skipna=True)
    diff_equal = (recomp_equal - overall["equal"]).abs()
    max_err = diff_equal.max(skipna=True)
    if max_err < 0.5:
        results.append(_pass(f"Equal-weight scores match recomputed pillar means (max err={max_err:.3f})"))
    else:
        worst = diff_equal.idxmax(skipna=True)
        results.append(_warn(
            f"Equal-weight score differs by up to {max_err:.2f} at {worst}. "
            "This may reflect a non-equal preset being active (ACTIVE_PRESET != 'equal')."
        ))

    # 3b. Geometric mean check
    if "geometric" in overall.columns:
        pillars = [p for p in PILLAR_DEFS if p in pillar_scores.columns]
        n = len(pillars)
        w_g = 1.0 / n
        geo_errors = {}
        for iso3, row in pillar_scores[pillars].iterrows():
            vals = row.values.astype(float)
            valid = ~np.isnan(vals)
            if valid.sum() == 0:
                continue
            # Clip to SCORE_FLOOR (= SMALL) before log, matching 04_score.py score_geometric.
            vals_clipped = np.maximum(vals[valid], SCORE_FLOOR)
            recomp_geo = math.exp(float(np.mean(np.log(vals_clipped))))
            stored_geo = overall["geometric"].get(iso3)
            if stored_geo is not None and not np.isnan(stored_geo):
                err = abs(recomp_geo - stored_geo)
                if err > 1.0:
                    geo_errors[iso3] = round(err, 2)
        if not geo_errors:
            results.append(_pass("Geometric mean scores match (log + exp formula, tol 1.0)"))
        else:
            results.append(_warn(
                f"Geometric mean differs for {len(geo_errors)} countries. "
                f"Note: geometric mean rescaling and SCORE_FLOOR choice affect results. "
                f"Worst: {sorted(geo_errors.items(), key=lambda x: -x[1])[:3]}"
            ))

    # 3c. BoD property: BoD scores should be >= equal for most countries
    if "bod" in overall.columns and "equal" in overall.columns:
        common = overall[["bod", "equal"]].dropna()
        n_bod_lower = (common["bod"] < common["equal"] - 1.0).sum()
        pct = n_bod_lower / len(common) * 100
        if pct < 10:
            results.append(_pass(
                f"BoD >= Equal-weight for {len(common) - n_bod_lower}/{len(common)} countries "
                f"(expected: BoD should always be at least as high as equal-weight)"
            ))
        else:
            results.append(_warn(
                f"BoD < Equal-weight for {n_bod_lower} countries ({pct:.0f}%). "
                "BoD maximizes per-country, so it should always be >= equal. "
                "Check LP solver convergence for these countries."
            ))
    return results

# ── Check 4: Confidence bands ─────────────────────────────────────────────────

def check_confidence_bands() -> list:
    results = []
    try:
        with open(RESULTS_JSON) as f:
            bundle = json.load(f)
    except Exception as e:
        return [_fail(f"Could not load results bundle: {e}")]

    errors = []
    for c in bundle["countries"]:
        pct_real = c["data_quality"]["pct_real"]
        pct_filled = 1.0 - pct_real
        eq_score = c["scores"].get("equal")
        band = c.get("confidence_band", {})
        if eq_score is None:
            continue
        # Formula: half_width = 2.0 + pct_filled * 26.7
        expected_hw = 2.0 + pct_filled * 26.7
        expected_low  = max(0.0,   round(eq_score - expected_hw, 1))
        expected_high = min(100.0, round(eq_score + expected_hw, 1))
        stored_low  = band.get("low")
        stored_high = band.get("high")
        if stored_low is None:
            continue
        if abs(stored_low - expected_low) > 0.5 or abs(stored_high - expected_high) > 0.5:
            errors.append(f"{c['iso3']}: expected [{expected_low},{expected_high}], "
                          f"got [{stored_low},{stored_high}]")
    if not errors:
        results.append(_pass("Confidence bands match formula: half_width = 2.0 + pct_filled×26.7"))
    else:
        results.append(_warn(f"Confidence band mismatch for {len(errors)} countries: {errors[:3]}"))
    return results

# ── Check 5: Peer ranks ───────────────────────────────────────────────────────

def check_peer_ranks() -> list:
    results = []
    try:
        with open(RESULTS_JSON) as f:
            bundle = json.load(f)
    except Exception as e:
        return [_fail(f"Could not load results bundle: {e}")]

    # Group by region
    region_groups = defaultdict(list)
    for c in bundle["countries"]:
        eq = c["scores"].get("equal")
        region_groups[c["region"]].append((c["iso3"], eq))

    errors = []
    for c in bundle["countries"]:
        region = c["region"]
        eq_score = c["scores"].get("equal")
        peers = [(iso3, s) for iso3, s in region_groups[region] if s is not None]
        sorted_peers = sorted(peers, key=lambda x: -x[1])
        ranks = {iso3: i + 1 for i, (iso3, _) in enumerate(sorted_peers)}
        expected_rank = ranks.get(c["iso3"])
        stored_rank = c.get("peer_rank", {}).get("rank_in_region")
        if expected_rank and stored_rank and expected_rank != stored_rank:
            errors.append(f"{c['iso3']}: expected rank {expected_rank}, got {stored_rank}")

    if not errors:
        results.append(_pass("All peer ranks match recomputed regional rankings"))
    else:
        results.append(_warn(f"Peer rank mismatch for {len(errors)} countries: {errors[:5]}"))
    return results

# ── Check 6: Structural / design issues ───────────────────────────────────────

def check_design_issues(ind_meta: dict, pillar_map: dict) -> list:
    results = []

    # 6a. Cross-listed indicators (double-counted)
    cross_listed = []
    for vn, info in ind_meta.items():
        if info.get("role", "scoring") != "scoring":
            continue
        pillars = info.get("pillars", [])
        if len(pillars) > 1:
            cross_listed.append((vn, pillars, info.get("display_name", vn)))

    if cross_listed:
        results.append(_warn(
            f"DOUBLE-COUNTING: {len(cross_listed)} indicators appear in multiple pillars. "
            "With equal pillar weights (1/7 each), these indicators receive implicit extra weight. "
            "Examples: " + "; ".join(f"{vn} in {ps}" for vn, ps, _ in cross_listed[:4])
        ))
        # Compute effective weights for each indicator
        eff_weights = {}
        for p, vars_list in pillar_map.items():
            n = len(vars_list)
            for v in vars_list:
                eff_weights[v] = eff_weights.get(v, 0) + (1/7) * (1/n) if n > 0 else 0
        max_var = max(eff_weights.items(), key=lambda x: x[1])
        min_var = min(eff_weights.items(), key=lambda x: x[1])
        results.append(_info(
            f"Effective indicator weights range: max={max_var[0]} at {max_var[1]:.4f}, "
            f"min={min_var[0]} at {min_var[1]:.4f}. "
            f"A perfectly equal indicator weight would be {1/36:.4f}. "
            "Cross-listed indicators can receive up to 3x the weight of unique indicators."
        ))

    # 6b. Pillar size imbalance
    pillar_sizes = {p: len(v) for p, v in pillar_map.items()}
    min_p = min(pillar_sizes, key=pillar_sizes.get)
    max_p = max(pillar_sizes, key=pillar_sizes.get)
    results.append(_info(
        f"Indicators per pillar: " +
        ", ".join(f"{p}={n}" for p, n in sorted(pillar_sizes.items())) +
        f". Smallest: {min_p}={pillar_sizes[min_p]}, Largest: {max_p}={pillar_sizes[max_p]}."
    ))
    if pillar_sizes[min_p] < 3:
        results.append(_warn(
            f"Pillar {min_p} has only {pillar_sizes[min_p]} indicator(s). "
            "Pillars with < 3 indicators are poorly measured — consider expanding or merging."
        ))

    # 6c. IDP size bias — RESOLVED
    # displaced_persons is converted to IDPs per 1,000 population in 02_clean.py Step 1b
    # using SP.POP.TOTL as denominator (UNHCR standard). The raw SM.POP.IDPC count is
    # replaced in-place before any filling or normalization, so the scored value is
    # already per-capita. This check is retained as documentation only.
    if "displaced_persons" in ind_meta:
        disp_display = ind_meta["displaced_persons"].get("display_name", "")
        if "per 1,000" in disp_display or "per capita" in disp_display.lower():
            results.append(_pass(
                "displaced_persons: per-capita normalization confirmed via display_name "
                f"('{disp_display}'). IDP size bias resolved by 02_clean.py Step 1b."
            ))
        else:
            results.append(_warn(
                "SIZE BIAS: 'displaced_persons' display_name does not confirm per-capita "
                "normalization. Check that 02_clean.py Step 1b (IDP / population × 1000) ran "
                "correctly. Expected display_name to contain 'per 1,000 population'."
            ))

    # 6d. Temporal coverage check
    years_start = [info.get("year_start") for info in ind_meta.values() if info.get("year_start")]
    years_end   = [info.get("year_end")   for info in ind_meta.values() if info.get("year_end")]
    if years_start and years_end:
        results.append(_info(
            f"Indicator year ranges: start [{min(years_start)}–{max(years_start)}], "
            f"end [{min(years_end)}–{max(years_end)}]. "
            "Mixed reference years mean the index is not a single-year snapshot."
        ))

    # 6e. Reliance on WGI governance indicators
    wgi_count = sum(1 for info in ind_meta.values() if info.get("database") == "wgi")
    wdi_count = sum(1 for info in ind_meta.values() if info.get("database") == "wdi")
    results.append(_info(
        f"Data sources: {wgi_count} indicators from WGI, {wdi_count} from WDI. "
        f"WGI constitutes {wgi_count/len(ind_meta)*100:.0f}% of indicators. "
        "WGI aggregates many sub-sources, which risks circular dependency if other "
        "sub-indices in the WGI overlap with WDI indicators used here."
    ))

    # 6f. MaxS optimization check
    rob_path = Path("data/05_robustness.json")
    if rob_path.exists():
        with open(rob_path) as f:
            rob = json.load(f)
        maxs = rob.get("maxs", {})
        max_shift = maxs.get("max_rank_shift", None)
        if max_shift == 0:
            results.append(_warn(
                "MaxS optimizer appears stuck at starting weights (max rank shift = 0). "
                "SLSQP cannot differentiate through rank correlation. "
                "Consider switching to a grid search or random-restart approach for MaxS."
            ))
    return results

# ── Check 7: Score distribution sanity ────────────────────────────────────────

def check_score_distribution() -> list:
    results = []
    try:
        with open(RESULTS_JSON) as f:
            bundle = json.load(f)
    except Exception as e:
        return [_fail(f"Could not load results: {e}")]

    scores = {m: [] for m in METHODS}
    for c in bundle["countries"]:
        for m in METHODS:
            s = c["scores"].get(m)
            if s is not None:
                scores[m].append(s)

    for m in METHODS:
        arr = np.array(scores[m])
        if len(arr) == 0:
            results.append(_warn(f"{m}: no scores computed"))
            continue
        results.append(_info(
            f"{m}: n={len(arr)}, mean={arr.mean():.1f}, "
            f"min={arr.min():.1f}, max={arr.max():.1f}, std={arr.std():.1f}"
        ))
        if arr.min() < 0 or arr.max() > 100:
            results.append(_fail(f"{m}: scores outside [0, 100]!"))

    # Check: does BoD tend to score higher than equal?
    eq_arr  = np.array(scores["equal"])
    bod_arr = np.array(scores["bod"])
    if len(eq_arr) and len(bod_arr):
        diff = bod_arr - eq_arr
        results.append(_info(
            f"BoD minus Equal-weight: mean={diff.mean():.1f}, "
            f"min={diff.min():.1f}, max={diff.max():.1f}. "
            "Expect BoD >= equal for most countries (BoD maximizes)."
        ))

    # Data quality distribution
    flags = [c["data_quality"]["fill_flag"] for c in bundle["countries"]]
    from collections import Counter
    flag_counts = Counter(flags)
    results.append(_info(
        "Data quality: " + ", ".join(f"{k}={v}" for k, v in sorted(flag_counts.items()))
    ))
    if flag_counts.get("Caution", 0) > 10:
        results.append(_warn(
            f"{flag_counts['Caution']} countries have 'Caution' data quality (>30% filled). "
            "Scores for these countries are less reliable."
        ))

    return results

# ── Check 8: Known benchmarks ─────────────────────────────────────────────────

def check_benchmark_plausibility() -> list:
    """
    Compare our rankings against IIAG 2023 top/bottom countries.
    IIAG 2023 top African performers: Mauritius, Botswana, Cabo Verde, Seychelles, South Africa.
    IIAG 2023 bottom performers: Somalia, South Sudan, Eritrea, Sudan, DR Congo.
    We expect strong correlation (top-quartile agreement).
    Source: Mo Ibrahim Foundation, IIAG 2023.
    """
    results = []
    try:
        with open(RESULTS_JSON) as f:
            bundle = json.load(f)
    except Exception as e:
        return [_fail(f"Could not load results: {e}")]

    ranked = sorted(
        [(c["iso3"], c["name"], c["ranks"].get("equal", 999)) for c in bundle["countries"]],
        key=lambda x: x[2]
    )
    top10_iso3  = {r[0] for r in ranked[:10]}
    bot10_iso3  = {r[0] for r in ranked[-10:]}

    # IIAG 2023 top-5 and bottom-5
    iiag_top5 = {"MUS", "BWA", "CPV", "SYC", "ZAF"}
    iiag_bot5 = {"SOM", "SSD", "ERI", "SDN", "COD"}

    top_overlap = len(iiag_top5 & top10_iso3)
    bot_overlap = len(iiag_bot5 & bot10_iso3)

    results.append(_info(
        f"IIAG 2023 top-5 in our top-10: {top_overlap}/5 ({iiag_top5 & top10_iso3}). "
        f"IIAG 2023 bottom-5 in our bottom-10: {bot_overlap}/5 ({iiag_bot5 & bot10_iso3}). "
        "(Reference: Mo Ibrahim Foundation IIAG 2023)"
    ))
    if top_overlap >= 3 and bot_overlap >= 3:
        results.append(_pass("Rankings broadly consistent with IIAG 2023 (3+ matches top and bottom)"))
    elif top_overlap + bot_overlap >= 4:
        results.append(_warn(
            "Partial consistency with IIAG 2023. Differences may reflect different indicator "
            "selection, weight choices, or reference year. Review mismatches carefully."
        ))
    else:
        results.append(_warn(
            "Low consistency with IIAG 2023. This may indicate: different conceptual scope "
            "(IIAG is governance-focused, AII includes security/environment), different year, "
            "or a methodological issue. Investigate top/bottom mismatches."
        ))

    # Print top-10 and bottom-10
    results.append(_info(
        "Our top-10: " + ", ".join(f"{iso3}(#{r})" for iso3, _, r in ranked[:10])
    ))
    results.append(_info(
        "Our bottom-10: " + ", ".join(f"{iso3}(#{r})" for iso3, _, r in ranked[-10:])
    ))
    return results

# ── Check 9: Within-pillar correlation (OECD §3) ──────────────────────────────

def check_pillar_correlations(ind_meta: dict, pillar_map: dict) -> list:
    """
    Flag indicator pairs within the same pillar with |Spearman rho| > 0.80.
    High cross-indicator correlation within a pillar indicates double-counting
    of the same latent concept — a parsimony violation per OECD Handbook (2008) §3.
    Reference threshold: OECD §3 recommends removing indicators with r > 0.80
    or that capture logically nested/subset relationships.
    """
    results = []
    try:
        norm_df = pd.read_excel(NORM_FILE, sheet_name="norm_data")
    except Exception as e:
        return [_fail(f"Could not load norm data for correlation check: {e}")]

    norm_pivot = norm_df.pivot(index="iso3", columns="variable_name", values="norm_score")
    HIGH_R_THRESHOLD = 0.80

    all_high = []
    for pillar, inds in pillar_map.items():
        available = [v for v in inds if v in norm_pivot.columns]
        if len(available) < 2:
            continue
        sub = norm_pivot[available].dropna(how="all")
        for i in range(len(available)):
            for j in range(i + 1, len(available)):
                vi, vj = available[i], available[j]
                pair = sub[[vi, vj]].dropna()
                if len(pair) < 5:
                    continue
                try:
                    from scipy.stats import spearmanr as _sr
                    rho, _ = _sr(pair[vi], pair[vj])
                except Exception:
                    continue
                if abs(rho) > HIGH_R_THRESHOLD:
                    all_high.append({
                        "pillar": pillar, "ind_a": vi, "ind_b": vj,
                        "rho": round(float(rho), 3),
                    })

    if not all_high:
        results.append(_pass(
            f"No within-pillar indicator pairs with |rho| > {HIGH_R_THRESHOLD} "
            "(OECD §3 parsimony threshold satisfied)"
        ))
    else:
        for h in all_high:
            results.append(_warn(
                f"Pillar {h['pillar']}: {h['ind_a']} vs {h['ind_b']} — "
                f"|rho|={abs(h['rho']):.3f} > {HIGH_R_THRESHOLD}. "
                "Review for redundancy (OECD Handbook §3 parsimony)."
            ))
    return results


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    t0 = _time.time()
    logger.info("=" * 60)
    logger.info("AII PIPELINE AUDIT")
    logger.info("=" * 60)

    ind_meta  = load_indicator_meta()
    pillar_map = load_pillar_map(ind_meta)

    all_checks = {}

    sections = [
        ("File Presence",          check_file_presence()),
        ("Normalization Math",     check_normalization(ind_meta)),
        ("Pillar Score Computation", check_pillar_scores(ind_meta, pillar_map)),
        ("Overall Score Methods",  check_overall_scores()),
        ("Confidence Bands",       check_confidence_bands()),
        ("Peer Ranks",             check_peer_ranks()),
        ("Design / Methodology",       check_design_issues(ind_meta, pillar_map)),
        ("Score Distributions",        check_score_distribution()),
        ("Benchmark Plausibility",     check_benchmark_plausibility()),
        ("Within-Pillar Correlations", check_pillar_correlations(ind_meta, pillar_map)),
    ]

    n_pass = n_warn = n_fail = 0
    for section_name, checks in sections:
        logger.info("\n--- %s ---", section_name)
        all_checks[section_name] = checks
        for c in checks:
            status = c["status"]
            if status == "PASS": n_pass += 1
            elif status == "WARN": n_warn += 1
            elif status == "FAIL": n_fail += 1
            icon = {"PASS": "[OK]", "WARN": "[!!]", "FAIL": "[XX]", "INFO": "[  ]"}[status]
            logger.info("  %s %s", icon, c["msg"])

    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY: %d PASS  %d WARN  %d FAIL", n_pass, n_warn, n_fail)
    logger.info("Elapsed: %.1fs", _time.time() - t0)
    logger.info("=" * 60)

    # Write JSON report for dashboard consumption
    report = {
        "run_date":  str(pd.Timestamp.now())[:19],
        "n_pass":    n_pass,
        "n_warn":    n_warn,
        "n_fail":    n_fail,
        "sections":  {k: v for k, v in all_checks.items()},
        "indicator_meta_summary": {
            "n_total": len(ind_meta),
            "n_cross_listed": sum(1 for i in ind_meta.values()
                                  if len(i.get("pillars", [])) > 1),
            "pillar_sizes": {p: len(v) for p, v in pillar_map.items()},
        },
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info("Audit report written to %s", OUTPUT_JSON)

if __name__ == "__main__":
    main()
