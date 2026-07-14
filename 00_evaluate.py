"""
00_evaluate.py — Independent end-to-end evaluation of the ASI pipeline
------------------------------------------------------------------------
Re-derives every published number from the frozen raw World Bank pull using an
independent implementation, then compares expected vs actual at three levels:

  Section 1  INDICATOR  raw pull -> aggregation -> fills -> per-capita →
                         winsorization -> log1p -> min-max  vs  02_clean / 03_norm
  Section 2  PILLAR     mean of available indicator scores  vs  04_scores_raw.csv
  Section 3  METHOD     equal / pca / bod / entropy / geometric + ranks
                         vs  04_scores_raw.csv and 06_results.json

Independence contract
  - Indicator definitions are read directly from indicators_list/*.yaml
    (never through config.PillarRegistry).
  - Only declarative values are imported from constants.py / models/countries.py.
  - No computation function from 02_clean / 03_normalize / 04_score is imported.
  - Where practical, different tools are used on purpose:
      PCA  -> np.linalg.eigh on the correlation matrix   (pipeline: sklearn PCA)
      BoD  -> scipy.optimize.linprog(method="highs")      (pipeline: pulp/CBC)

Raw baseline
  data/baseline/01_raw_pull_BASELINE.xlsx is created on first run as a frozen
  copy of data/01_raw_pull.xlsx. All evaluation reads the baseline; the live
  file is only diffed against it so that a re-pull (World Bank revisions)
  surfaces as a WARN instead of silently shifting the evaluation baseline.
  Delete the baseline file to re-freeze from the current live pull.

Run:   python 00_evaluate.py [--data-dir data]
Exit:  0 if no FAIL (WARNs allowed), 1 otherwise.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.optimize import linprog

from constants import (
    PILLAR_DEFS, WEIGHT_PRESETS, ACTIVE_PRESET,
    WEIGHT_MIN, WEIGHT_MAX, SMALL,
    IQR_MULTIPLIER, MIN_REGIONAL_SAMPLE,
)
from models.countries import COUNTRIES

INDICATORS_DIR = Path("indicators_list")
ISO3_LIST      = list(COUNTRIES.keys())
ISO3_TO_REGION = {iso3: m["region"] for iso3, m in COUNTRIES.items()}
DETAIL_CAP     = 5

# ==============================================================================
# SHARED — registry, artifact loading, comparison/reporting helpers
# ==============================================================================

CHECKS: list[dict] = []


def record(section: str, name: str, status: str, summary: str, details=()):
    CHECKS.append({"section": section, "name": name, "status": status,
                   "summary": summary, "details": list(details)})
    print(f"[{status}] {section} | {name} -- {summary}")
    shown = list(details)[:DETAIL_CAP]
    for line in shown:
        print(f"         {line}")
    if len(details) > DETAIL_CAP:
        print(f"         ... and {len(details) - DETAIL_CAP} more")


def compare_series(section: str, name: str,
                   expected: pd.Series, actual: pd.Series,
                   atol: float, warn_atol: float | None = None,
                   label: str = "values"):
    """
    Index-aligned expected-vs-actual comparison. NaN == NaN counts as a match;
    NaN on one side only is a FAIL. diff <= atol PASS; <= warn_atol WARN;
    beyond FAIL. Details show the worst offenders.
    """
    idx  = expected.index.union(actual.index)
    e    = expected.reindex(idx).astype(float)
    a    = actual.reindex(idx).astype(float)
    both_nan = e.isna() & a.isna()
    one_nan  = e.isna() ^ a.isna()
    diff     = (e - a).abs()

    fail_tol  = warn_atol if warn_atol is not None else atol
    fail_mask = one_nan | ((~both_nan) & (diff > fail_tol))
    warn_mask = (~fail_mask) & (~both_nan) & (diff > atol) if warn_atol is not None \
        else pd.Series(False, index=idx)

    def rows(mask):
        d = pd.DataFrame({"expected": e[mask], "actual": a[mask],
                          "diff": diff[mask]}).sort_values("diff", ascending=False,
                                                           na_position="first")
        return [f"{ix}: expected={r['expected']:.6f} actual={r['actual']:.6f} diff={r['diff']:.2e}"
                if pd.notna(r["expected"]) and pd.notna(r["actual"]) else
                f"{ix}: expected={r['expected']} actual={r['actual']} (NaN mismatch)"
                for ix, r in d.iterrows()]

    n = len(idx)
    tol_txt = f"tol={atol:g}" + (f", warn={warn_atol:g}" if warn_atol is not None else "")
    if fail_mask.any():
        record(section, name, "FAIL",
               f"{int(fail_mask.sum())}/{n} {label} beyond tolerance ({tol_txt})",
               rows(fail_mask))
    elif warn_mask.any():
        record(section, name, "WARN",
               f"{int(warn_mask.sum())}/{n} {label} in warn band ({tol_txt})",
               rows(warn_mask))
    else:
        record(section, name, "PASS", f"{n} {label} match ({tol_txt})")


def stack_wide(df: pd.DataFrame) -> pd.Series:
    """Wide (iso3 × var) -> Series indexed by 'iso3/var' (keeps NaN cells)."""
    long = df.stack()  # pandas 3 stack keeps NaN cells by default
    long.index = [f"{i}/{v}" for i, v in long.index]
    return long


def load_registry() -> dict[str, dict]:
    """indicators_list/*.yaml -> {variable_name: meta}. Cross-listed vars merge pillars."""
    reg: dict[str, dict] = {}
    for path in sorted(INDICATORS_DIR.glob("*.yaml")):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for ind in data or []:
            vn = ind["variable_name"]
            if vn in reg:
                reg[vn]["pillars"] = list(dict.fromkeys(reg[vn]["pillars"] + ind.get("pillars", [])))
                continue
            reg[vn] = {
                "role":          ind.get("role", "scoring"),
                "polarity":      ind.get("polarity", "positive"),
                "pillars":       list(ind.get("pillars", [])),
                "year_start":    int(ind["year_start"]),
                "year_end":      int(ind["year_end"]),
                "aggregation":   ind["aggregation"],
                "log_transform": bool(ind.get("log_transform", False)),
            }
    return reg


def ensure_baseline(data_dir: Path) -> pd.DataFrame:
    """Freeze/read the raw baseline; WARN if the live pull has drifted from it."""
    live     = data_dir / "01_raw_pull.xlsx"
    baseline = data_dir / "baseline" / "01_raw_pull_BASELINE.xlsx"

    if not baseline.exists():
        if not live.exists():
            record("0 Baseline", "raw pull present", "FAIL",
                   f"neither {baseline} nor {live} exists -- run 01_pull.py first")
            sys.exit(1)
        baseline.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(live, baseline)
        record("0 Baseline", "freeze", "PASS",
               f"baseline created from live pull -> {baseline}")

    base_df = pd.read_excel(baseline, sheet_name="raw_data")

    if live.exists():
        live_df = pd.read_excel(live, sheet_name="raw_data")
        key = ["variable_name", "iso3", "year"]
        merged = base_df.merge(live_df, on=key, how="outer",
                               suffixes=("_base", "_live"), indicator=True)
        n_only_base = int((merged["_merge"] == "left_only").sum())
        n_only_live = int((merged["_merge"] == "right_only").sum())
        both = merged[merged["_merge"] == "both"]
        n_changed = int((
            (both["value_base"] - both["value_live"]).abs() > 1e-9
        ).sum())
        if n_only_base or n_only_live or n_changed:
            record("0 Baseline", "live vs frozen raw", "WARN",
                   f"live pull differs from frozen baseline: {n_changed} changed values, "
                   f"{n_only_live} new rows, {n_only_base} removed rows "
                   f"(evaluation uses the frozen baseline; delete "
                   f"data/baseline/01_raw_pull_BASELINE.xlsx to re-freeze)")
        else:
            record("0 Baseline", "live vs frozen raw", "PASS",
                   f"live pull identical to frozen baseline ({len(base_df)} rows)")
    return base_df


# ==============================================================================
# SECTION 1 — INDICATOR LEVEL: raw -> clean -> normalized
# ==============================================================================

def _agg_reduce(vals: np.ndarray, agg: str) -> float:
    """Reduce year-ascending values per the registry's aggregation mode."""
    if len(vals) == 0:
        return float("nan")
    if agg == "most_recent":
        return float(vals[-1])
    if agg == "average":
        return float(np.mean(vals))
    if agg == "average_recent_3":
        return float(np.mean(vals[-3:]))
    if agg == "average_recent_5":
        return float(np.mean(vals[-5:]))
    raise ValueError(f"Unknown aggregation '{agg}'")


def recompute_clean(raw_df: pd.DataFrame, registry: dict):
    """
    Independent re-derivation of 02_clean: aggregation, stage-1 extended
    look-back fill, per-capita IDP conversion, stage-2 regional fill,
    IQR winsorization. Returns (clean_wide, fill_records, wins_rows).
    """
    raw = raw_df.copy()
    raw["year"] = pd.to_numeric(raw["year"], errors="coerce").astype("Int64")

    agg_vals: dict[tuple, float] = {}
    fill_records: list[dict] = []

    # Step 1 — aggregation + stage-1 fill over [year_start-5, year_start)
    for var, meta in registry.items():
        sub      = raw[raw["variable_name"] == var].sort_values("year")
        target   = sub[(sub["year"] >= meta["year_start"]) & (sub["year"] <= meta["year_end"])]
        extended = sub[(sub["year"] >= meta["year_start"] - 5) & (sub["year"] < meta["year_start"])]
        for iso3 in ISO3_LIST:
            t   = target[target["iso3"] == iso3].dropna(subset=["value"])
            val = _agg_reduce(t["value"].to_numpy(dtype=float), meta["aggregation"])
            if np.isnan(val):
                e = extended[extended["iso3"] == iso3].dropna(subset=["value"])
                if not e.empty:
                    val = _agg_reduce(e["value"].to_numpy(dtype=float), meta["aggregation"])
                    # NB: for displaced_persons this logs the PRE-conversion
                    # absolute count — conversion happens after stage-1 (02_clean).
                    fill_records.append({
                        "variable_name": var, "iso3": iso3,
                        "fill_stage": "stage1_extended",
                        "fill_year":  int(e.iloc[-1]["year"]),
                        "fill_value": round(val, 6),
                    })
            agg_vals[(iso3, var)] = val

    # Step 1b — per-capita IDP conversion (after stage-1, before stage-2)
    if "displaced_persons" in registry and "population_total" in registry:
        for iso3 in ISO3_LIST:
            idp = agg_vals[(iso3, "displaced_persons")]
            pop = agg_vals[(iso3, "population_total")]
            if np.isnan(idp):
                continue
            if np.isnan(pop) or pop <= 0:
                agg_vals[(iso3, "displaced_persons")] = float("nan")
            else:
                agg_vals[(iso3, "displaced_persons")] = (idp / pop) * 1000.0

    # Step 2 — stage-2 regional mean fill (needs >= MIN_REGIONAL_SAMPLE peers)
    wide = pd.DataFrame(
        [{"iso3": iso3, **{v: agg_vals[(iso3, v)] for v in registry}} for iso3 in ISO3_LIST]
    )
    wide["_region"] = wide["iso3"].map(ISO3_TO_REGION)
    for var in registry:
        for _region, grp in wide.groupby("_region"):
            have   = grp[var].notna()
            n_have = int(have.sum())
            n_need = int((~have).sum())
            if n_need == 0 or n_have < MIN_REGIONAL_SAMPLE:
                continue
            region_mean = float(grp.loc[have, var].mean())
            fill_idx    = grp.index[~have]
            wide.loc[fill_idx, var] = region_mean
            for iso3 in wide.loc[fill_idx, "iso3"]:
                fill_records.append({
                    "variable_name": var, "iso3": iso3,
                    "fill_stage": "stage2_regional",
                    "fill_year":  None,
                    "fill_value": round(region_mean, 6),
                })
    wide = wide.drop(columns=["_region"]).set_index("iso3")

    # Step 3 — IQR winsorization (scoring indicators only)
    wins_rows: list[dict] = []
    for var, meta in registry.items():
        if meta["role"] != "scoring":
            continue
        col = wide[var].dropna().to_numpy(dtype=float)
        if len(col) == 0:
            continue
        q1, q3 = np.quantile(col, [0.25, 0.75])
        iqr    = q3 - q1
        lo, hi = q1 - IQR_MULTIPLIER * iqr, q3 + IQR_MULTIPLIER * iqr
        n_lo   = int((wide[var] < lo).sum())
        n_hi   = int((wide[var] > hi).sum())
        wide[var] = wide[var].clip(lower=lo, upper=hi)
        wins_rows.append({"variable_name": var, "q1": q1, "q3": q3, "iqr": iqr,
                          "lower_bound": lo, "upper_bound": hi,
                          "n_capped_low": n_lo, "n_capped_high": n_hi})

    return wide, fill_records, wins_rows


def recompute_norm(clean_wide: pd.DataFrame, registry: dict):
    """
    Independent re-derivation of 03_normalize: optional log1p (negatives clipped
    to 0 first), min-max over the non-NaN sample, polarity direction,
    zero-variance -> 50. Returns (norm_wide, bounds) where bounds carries the
    exact sample stats used, for the provenance check.
    """
    scoring = sorted(v for v, m in registry.items()
                     if m["role"] == "scoring" and v in clean_wide.columns)
    norm_cols: dict[str, pd.Series] = {}
    bounds: dict[str, dict] = {}
    for var in scoring:
        meta = registry[var]
        x = clean_wide[var].astype(float)
        if meta["log_transform"]:
            if (x.dropna() < 0).any():
                x = x.clip(lower=0)
            x = np.log1p(x)
        x_min = float(x.min(skipna=True))
        x_max = float(x.max(skipna=True))
        if x_max == x_min:
            norm = x.where(x.isna(), 50.0)
        elif meta["polarity"] == "negative":
            norm = (x_max - x) / (x_max - x_min) * 100.0
        else:
            norm = (x - x_min) / (x_max - x_min) * 100.0
        norm_cols[var] = norm
        bounds[var] = {"x_min": x_min, "x_max": x_max,
                       "n_valid": int(x.notna().sum()), "n_total": int(len(x)),
                       "polarity": meta["polarity"],
                       "log_transform": meta["log_transform"]}
    return pd.DataFrame(norm_cols, index=clean_wide.index), bounds


def section_1(raw_df, registry, art):
    S = "1 Indicator"
    clean_exp, fills_exp, wins_exp = recompute_clean(raw_df, registry)

    # 1.1 — clean values vs 02_clean.xlsx / clean_data
    clean_act = art["clean_data"]
    missing = sorted(set(registry) - set(clean_act.columns))
    extra   = sorted(set(clean_act.columns) - set(registry))
    if missing or extra:
        record(S, "1.1 clean_data columns", "FAIL",
               f"column set differs from registry (missing={missing}, extra={extra})")
    common = [v for v in registry if v in clean_act.columns]
    compare_series(S, "1.1 clean values (post-fill, post-winsorization)",
                   stack_wide(clean_exp[common]), stack_wide(clean_act[common]),
                   atol=1e-9, label="cells")

    # 1.2 — fill log agreement (set equality + values)
    fl = art["fill_log"]
    act_keys = {(r.variable_name, r.iso3, r.fill_stage) for r in fl.itertuples()}
    exp_keys = {(r["variable_name"], r["iso3"], r["fill_stage"]) for r in fills_exp}
    details  = [f"expected-only fill: {k}" for k in sorted(exp_keys - act_keys)] + \
               [f"pipeline-only fill: {k}" for k in sorted(act_keys - exp_keys)]
    exp_map = {(r["variable_name"], r["iso3"], r["fill_stage"]): r for r in fills_exp}
    n_val_bad = 0
    for r in fl.itertuples():
        k = (r.variable_name, r.iso3, r.fill_stage)
        if k not in exp_map:
            continue
        ev = exp_map[k]
        if abs(float(r.fill_value) - float(ev["fill_value"])) > 1e-6:
            n_val_bad += 1
            details.append(f"{k}: fill_value expected={ev['fill_value']} actual={r.fill_value}")
        ey, ay = ev["fill_year"], r.fill_year
        if (ey is None) != bool(pd.isna(ay)) or (ey is not None and int(ey) != int(ay)):
            n_val_bad += 1
            details.append(f"{k}: fill_year expected={ey} actual={ay}")
    if details:
        record(S, "1.2 fill log", "FAIL",
               f"{len(exp_keys ^ act_keys)} membership + {n_val_bad} value mismatches "
               f"(expected {len(exp_keys)}, pipeline {len(act_keys)})", details)
    else:
        record(S, "1.2 fill log", "PASS",
               f"{len(act_keys)} fills match exactly (stage, year, value)")

    # 1.3 — winsorization bounds and cap counts
    wins_act = art["winsorisation"].set_index("variable_name")
    wins_exp_df = pd.DataFrame(wins_exp).set_index("variable_name")
    for col, tol in [("q1", 1e-4), ("q3", 1e-4), ("lower_bound", 1e-4),
                     ("upper_bound", 1e-4), ("n_capped_low", 0), ("n_capped_high", 0)]:
        compare_series(S, f"1.3 winsorization {col}",
                       wins_exp_df[col].astype(float), wins_act[col].astype(float),
                       atol=tol if tol else 1e-12, label="indicators")

    # 1.4 — normalized scores, end-to-end from raw
    norm_exp, bounds_exp = recompute_norm(clean_exp, registry)
    norm_act = art["norm_data"].pivot(index="iso3", columns="variable_name",
                                      values="norm_score")
    common_n = [v for v in norm_exp.columns if v in norm_act.columns]
    only_exp = sorted(set(norm_exp.columns) - set(norm_act.columns))
    only_act = sorted(set(norm_act.columns) - set(norm_exp.columns))
    if only_exp or only_act:
        record(S, "1.4 normalized indicator set", "FAIL",
               f"scoring-indicator sets differ (expected-only={only_exp}, pipeline-only={only_act})")
    compare_series(S, "1.4 normalized scores (raw -> clean -> log -> min-max)",
                   stack_wide(norm_exp[common_n]), stack_wide(norm_act[common_n]),
                   atol=1.5e-4, label="cells")

    # 1.5 — norm_bounds provenance: the min/max/count driving each min-max must
    # equal the stats of OUR independently built post-fill post-winsorization
    # (post-log where applicable) sample.
    nb = art["norm_bounds"].set_index("variable_name")
    exp_min = pd.Series({v: b["x_min"] for v, b in bounds_exp.items()})
    exp_max = pd.Series({v: b["x_max"] for v, b in bounds_exp.items()})
    compare_series(S, "1.5 norm_bounds raw_min provenance",
                   exp_min, nb["raw_min"].astype(float), atol=1e-6, label="indicators")
    compare_series(S, "1.5 norm_bounds raw_max provenance",
                   exp_max, nb["raw_max"].astype(float), atol=1e-6, label="indicators")
    compare_series(S, "1.5 norm_bounds n_valid (fills included in sample)",
                   pd.Series({v: b["n_valid"] for v, b in bounds_exp.items()}, dtype=float),
                   nb["n_valid"].astype(float), atol=1e-12, label="indicators")
    meta_bad = []
    for v, b in bounds_exp.items():
        if v not in nb.index:
            continue
        row = nb.loc[v]
        if str(row["polarity"]) != b["polarity"]:
            meta_bad.append(f"{v}: polarity registry={b['polarity']} pipeline={row['polarity']}")
        if bool(row["log_transform"]) != b["log_transform"]:
            meta_bad.append(f"{v}: log_transform registry={b['log_transform']} "
                            f"pipeline={row['log_transform']}")
        if b["log_transform"]:
            # pipeline stores post-log values in raw_min/raw_max; log_* must duplicate
            if not (np.isclose(row["raw_min"], row["log_min"], atol=1e-9) and
                    np.isclose(row["raw_max"], row["log_max"], atol=1e-9)):
                meta_bad.append(f"{v}: raw_min/max != log_min/max in norm_bounds")
    record(S, "1.5 norm_bounds metadata (polarity/log vs registry)",
           "FAIL" if meta_bad else "PASS",
           f"{len(meta_bad)} mismatches" if meta_bad
           else f"{len(bounds_exp)} indicators consistent", meta_bad)

    # 1.6 — dashboard-facing indicator scores in 06_results.json (rounded 2)
    json_scores = {}
    for c in art["results"]["countries"]:
        for var, d in c.get("indicators", {}).items():
            json_scores[f"{c['iso3']}/{var}"] = (float(d["score"])
                                                 if d.get("score") is not None else float("nan"))
    # Transfer-fidelity check: 06 reads norm_data (already independently verified
    # in 1.4) and rounds to 2dp with Python's round(). numpy's .round() disagrees
    # with it on values like 48.085, so mirror the builtin exactly.
    exp_r2 = stack_wide(norm_act[common_n]).map(
        lambda v: round(float(v), 2) if pd.notna(v) else float("nan"))
    compare_series(S, "1.6 results.json indicator scores (norm_data transfer)",
                   exp_r2, pd.Series(json_scores), atol=0.006, label="cells")

    return norm_exp


# ==============================================================================
# SECTION 2 — PILLAR LEVEL
# ==============================================================================

def build_pillar_map(registry: dict) -> dict[str, list[str]]:
    pillar_map: dict[str, list[str]] = {p: [] for p in PILLAR_DEFS}
    for var, meta in registry.items():
        if meta["role"] != "scoring":
            continue
        for p in meta["pillars"]:
            if p in pillar_map and var not in pillar_map[p]:
                pillar_map[p].append(var)
    return pillar_map


def section_2(registry, art):
    S = "2 Pillar"
    # Deliberate input choice: the PIPELINE's norm_data, so a mismatch here is
    # attributable to the pillar-aggregation step alone (the raw→norm chain is
    # already covered by check 1.4).
    norm_wide = art["norm_data"].pivot(index="iso3", columns="variable_name",
                                       values="norm_score")
    pillar_map = build_pillar_map(registry)

    exp = {}
    for p, vars_in in pillar_map.items():
        avail = [v for v in vars_in if v in norm_wide.columns]
        if not avail:
            exp[p] = pd.Series(float("nan"), index=norm_wide.index)
            continue
        sub = norm_wide[avail]
        s = sub.mean(axis=1, skipna=True)
        s[sub.isna().all(axis=1)] = float("nan")
        exp[p] = s
    pillar_exp = pd.DataFrame(exp, index=norm_wide.index)

    csv = art["scores_csv"].set_index("iso3")
    pillar_act = csv[list(PILLAR_DEFS)]
    compare_series(S, "2.1 pillar scores (mean of available indicators)",
                   stack_wide(pillar_exp), stack_wide(pillar_act),
                   atol=1e-6, label="cells")

    json_p = {}
    for c in art["results"]["countries"]:
        for p, v in c.get("pillar_scores", {}).items():
            json_p[f"{c['iso3']}/{p}"] = float(v) if v is not None else float("nan")
    compare_series(S, "2.2 results.json pillar scores",
                   stack_wide(pillar_exp).round(2), pd.Series(json_p),
                   atol=0.006, label="cells")
    return pillar_exp


# ==============================================================================
# SECTION 3 — METHOD LEVEL (custom excluded)
# ==============================================================================

def _weighted_mean_rows(pillar_wide: pd.DataFrame, weights: np.ndarray) -> pd.Series:
    """Per-country dot product over non-NaN pillars with weights renormalized."""
    out = {}
    for iso3, row in pillar_wide.iterrows():
        vals  = row.to_numpy(dtype=float)
        valid = ~np.isnan(vals)
        if not valid.any():
            out[iso3] = float("nan")
        else:
            w = weights[valid] / weights[valid].sum()
            out[iso3] = float(np.dot(w, vals[valid]))
    return pd.Series(out)


def method_equal(pw: pd.DataFrame) -> pd.Series:
    preset = WEIGHT_PRESETS[ACTIVE_PRESET]
    w = np.array([preset[p] for p in pw.columns])
    return _weighted_mean_rows(pw, w / w.sum())


def method_pca(pw: pd.DataFrame) -> tuple[pd.Series, float]:
    """Independent PCA route: eigendecomposition of the correlation matrix
    (identical eigenvectors to StandardScaler+sklearn-PCA, different solver).
    Returns (scores, PC1-PC2 eigenvalue gap)."""
    complete = pw.dropna()
    R = np.corrcoef(complete.to_numpy(dtype=float), rowvar=False)
    evals, evecs = np.linalg.eigh(R)          # ascending eigenvalues
    loadings = evecs[:, -1].copy()
    gap = float(evals[-1] - evals[-2])
    if (loadings < 0).sum() > len(loadings) / 2:
        loadings = -loadings
    loadings = np.where(loadings < 0, 0.0, loadings)
    if loadings.sum() < SMALL:
        weights = np.full(len(pw.columns), 1.0 / len(pw.columns))
    else:
        weights = loadings / loadings.sum()
    raw = _weighted_mean_rows(pw, weights)
    mn, mx = raw.min(skipna=True), raw.max(skipna=True)
    if mx == mn:
        return raw.where(raw.isna(), 50.0), gap
    return (raw - mn) / (mx - mn) * 100.0, gap


def method_bod(pw: pd.DataFrame) -> pd.Series:
    """Independent BoD via scipy HiGHS (pipeline uses pulp/CBC)."""
    V = pw.to_numpy(dtype=float) / 100.0
    n_c, _ = V.shape
    out = {}
    for i, iso3 in enumerate(pw.index):
        v = V[i]
        valid = [k for k in range(V.shape[1]) if not np.isnan(v[k])]
        if not valid:
            out[iso3] = float("nan")
            continue
        if len(valid) * WEIGHT_MAX < 1.0 - 1e-9:
            out[iso3] = float(np.mean(v[valid])) * 100.0
            continue
        c = -v[valid]                                     # maximize v·w
        a_ub, b_ub = [], []
        for j in range(n_c):
            if j == i:
                continue
            common = [k for k in valid if not np.isnan(V[j, k])]
            if not common:
                continue
            row = [V[j, k] if k in common else 0.0 for k in valid]
            a_ub.append(row)
            b_ub.append(1.0)
        res = linprog(c, A_ub=np.array(a_ub) if a_ub else None,
                      b_ub=np.array(b_ub) if b_ub else None,
                      A_eq=np.ones((1, len(valid))), b_eq=[1.0],
                      bounds=[(WEIGHT_MIN, WEIGHT_MAX)] * len(valid),
                      method="highs")
        out[iso3] = float(-res.fun) * 100.0 if res.success else float("nan")
    return pd.Series(out)


def method_entropy(pw: pd.DataFrame) -> pd.Series:
    sub = pw.copy()
    n = len(sub)
    for col in sub.columns:
        mn = sub[col].min(skipna=True)
        if mn <= 0:
            sub[col] = sub[col] - mn + SMALL
    H = {}
    for col in sub.columns:
        col_vals = sub[col].fillna(sub[col].mean())
        total = col_vals.sum()
        if total == 0:
            H[col] = 0.0
            continue
        p = (col_vals / total).clip(lower=SMALL)
        H[col] = float(-np.sum(p * np.log(p)))
    e = {col: 1.0 - H[col] / np.log(n) for col in sub.columns}
    total_e = sum(e.values())
    if total_e == 0:
        w = np.full(len(sub.columns), 1.0 / len(sub.columns))
    else:
        w = np.array([e[col] / total_e for col in sub.columns])
    return _weighted_mean_rows(pw, w)


def method_geometric(pw: pd.DataFrame) -> pd.Series:
    w = np.full(len(pw.columns), 1.0 / len(pw.columns))
    out = {}
    for iso3, row in pw.iterrows():
        vals = row.to_numpy(dtype=float)
        valid = ~np.isnan(vals)
        if not valid.any():
            out[iso3] = float("nan")
            continue
        clipped = np.maximum(vals[valid], SMALL)
        wv = w[valid] / w[valid].sum()
        out[iso3] = float(np.exp(np.dot(wv, np.log(clipped))))
    return pd.Series(out)


def section_3(pillar_exp: pd.DataFrame, art):
    S = "3 Method"
    pw  = pillar_exp[list(PILLAR_DEFS)]
    csv = art["scores_csv"].set_index("iso3")

    pca_scores, pca_gap = method_pca(pw)
    recomputed = {
        "equal":     (method_equal(pw),     1e-6, None),
        "pca":       (pca_scores,           1e-6, 1e-4),
        "bod":       (method_bod(pw),       1e-4, 1e-2),
        "entropy":   (method_entropy(pw),   1e-6, None),
        "geometric": (method_geometric(pw), 1e-6, None),
    }
    for m, (exp, atol, warn) in recomputed.items():
        compare_series(S, f"3.x {m} score", exp, csv[m].astype(float),
                       atol=atol, warn_atol=warn, label="countries")

    if pca_gap < 0.1:
        record(S, "3.2 pca eigenvalue gap", "WARN",
               f"PC1-PC2 eigenvalue gap = {pca_gap:.4f} (< 0.1): PC1 is nearly "
               f"degenerate, PCA weights are unstable across samples")
    else:
        record(S, "3.2 pca eigenvalue gap", "PASS",
               f"PC1-PC2 eigenvalue gap = {pca_gap:.4f} (well-separated)")

    # 3.6 ranks — internal consistency of the CSV, then noise sensitivity
    for m in recomputed:
        exp_rank = csv[m].rank(ascending=False, method="min", na_option="bottom")
        compare_series(S, f"3.6 {m} rank (recomputed from CSV scores)",
                       exp_rank, csv[f"{m}_rank"].astype(float),
                       atol=1e-12, label="countries")
    for m in ("pca", "bod"):
        ours = recomputed[m][0].rank(ascending=False, method="min", na_option="bottom")
        theirs = csv[f"{m}_rank"].astype(float)
        n_flip = int((ours.reindex(theirs.index) != theirs).sum())
        record(S, f"3.6 {m} rank stability under solver noise",
               "WARN" if n_flip else "PASS",
               f"{n_flip} rank difference(s) between our independently solved scores "
               f"and the pipeline's" if n_flip else "identical ranking from the "
               f"independent solver")

    # 3.7 results.json method scores (rounded 2)
    json_s = {}
    for c in art["results"]["countries"]:
        for m in recomputed:
            v = c.get("scores", {}).get(m)
            json_s[f"{c['iso3']}/{m}"] = float(v) if v is not None else float("nan")
    exp_long = pd.concat(
        {m: csv[m].astype(float).round(2) for m in recomputed}
    )
    exp_long.index = [f"{i}/{m}" for m, i in exp_long.index]
    compare_series(S, "3.7 results.json method scores",
                   exp_long, pd.Series(json_s), atol=0.006, label="cells")


# ==============================================================================
# Main
# ==============================================================================

def load_artifacts(data_dir: Path) -> dict:
    art = {}
    clean = pd.read_excel(data_dir / "02_clean.xlsx",
                          sheet_name=["clean_data", "fill_log", "winsorisation"])
    art["clean_data"]    = clean["clean_data"].set_index("iso3").drop(
        columns=["_region"], errors="ignore")
    art["fill_log"]      = clean["fill_log"]
    art["winsorisation"] = clean["winsorisation"]
    norm = pd.read_excel(data_dir / "03_norm.xlsx",
                         sheet_name=["norm_data", "norm_bounds"])
    art["norm_data"]   = norm["norm_data"]
    art["norm_bounds"] = norm["norm_bounds"]
    art["scores_csv"]  = pd.read_csv(data_dir / "04_scores_raw.csv")
    with open(data_dir / "06_results.json", encoding="utf-8") as f:
        art["results"] = json.load(f)
    return art


def main():
    ap = argparse.ArgumentParser(description="Independent ASI pipeline evaluation")
    ap.add_argument("--data-dir", default="data", type=Path,
                    help="pipeline output directory (default: data)")
    args = ap.parse_args()

    print("=" * 78)
    print("ASI INDEPENDENT EVALUATION -- raw pull -> indicators -> pillars -> methods")
    print("=" * 78)

    registry = load_registry()
    raw_df   = ensure_baseline(args.data_dir)
    art      = load_artifacts(args.data_dir)

    print("-" * 78)
    section_1(raw_df, registry, art)
    print("-" * 78)
    pillar_exp = section_2(registry, art)
    print("-" * 78)
    section_3(pillar_exp, art)

    print("=" * 78)
    n = {s: sum(1 for c in CHECKS if c["status"] == s) for s in ("PASS", "WARN", "FAIL")}
    print(f"SUMMARY: {n['PASS']} PASS  {n['WARN']} WARN  {n['FAIL']} FAIL")
    for c in CHECKS:
        if c["status"] != "PASS":
            print(f"  [{c['status']}] {c['section']} | {c['name']}")
    print("=" * 78)
    sys.exit(1 if n["FAIL"] else 0)


if __name__ == "__main__":
    main()
