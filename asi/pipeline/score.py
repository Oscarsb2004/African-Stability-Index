"""
asi.pipeline.score — pillar and composite scores, each carrying a reliability tier.

Two things changed in Phase B beyond adding a year dimension.

1. Every aggregate reports how much of it was measured
   A pillar score assembled from four regional averages and one real observation
   is not the same claim as one built from five measurements, and the interface
   must be able to tell them apart. `pillar_scores` therefore returns coverage
   counts and a Reliability tier alongside the number.

2. Data-driven weights are frozen, not recomputed per year
   PCA and entropy weights depend on the sample they are fitted to. Refitting
   them each year would mean a country's composite moved because the weighting
   changed, not because the country did — the same defect fixed goalposts remove
   from normalisation. They are therefore fitted once on the pooled panel and
   reused for every year.

   Benefit-of-the-Doubt is the deliberate exception: it is defined as "the
   weighting most favourable to this country relative to its peers", so it is
   solved per year against that year's peers. It is a within-year statement and
   should not be read as a time series.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from asi.core.schema import Reliability, classify_reliability


# ── Pillar level ───────────────────────────────────────────────────────────────

def pillar_scores(
    panel: pd.DataFrame,
    pillar_map: dict[str, list[str]],
    *,
    reliable_at: float,
    thin_at: float,
    max_imputed_share: float,
) -> pd.DataFrame:
    """
    Mean of the available indicator scores in each pillar, per country-year.

    Returns one row per (iso3, pillar_id, year) with:
        score, n_indicators, n_observed, n_imputed, coverage_ratio, reliability

    `n_indicators` is the pillar's full membership, not the number that happened
    to have data — coverage must be measured against what the pillar claims to
    measure, otherwise a pillar with one surviving indicator would report 100%
    coverage.
    """
    rows = []
    scored = panel[panel["score"].notna()]

    by_key = {
        key: grp for key, grp in
        scored.groupby(["iso3", "year", "variable_name"], sort=False)["score"]
    }
    prov_by_key = {
        key: grp for key, grp in
        panel.groupby(["iso3", "year", "variable_name"], sort=False)["provenance"]
    }

    iso3s = sorted(panel["iso3"].unique())
    years = sorted(panel["year"].unique())

    for pillar_id, members in pillar_map.items():
        n_indicators = len(members)
        if n_indicators == 0:
            continue
        for iso3 in iso3s:
            for year in years:
                vals, n_observed, n_imputed, contributing = [], 0, 0, []
                for var in members:
                    key = (iso3, year, var)
                    s = by_key.get(key)
                    if s is None or s.empty:
                        continue
                    value = float(s.iloc[0])
                    if np.isnan(value):
                        continue
                    vals.append(value)
                    contributing.append(var)
                    prov = prov_by_key.get(key)
                    p = prov.iloc[0] if prov is not None and not prov.empty else "absent"
                    if p == "observed":
                        n_observed += 1
                    elif p in ("carried_forward", "regional_mean", "interpolated"):
                        n_imputed += 1
                    elif p == "derived":
                        n_observed += 1   # computed from real data

                reliability = classify_reliability(
                    n_indicators, n_observed, n_imputed,
                    reliable_at=reliable_at, thin_at=thin_at,
                    max_imputed_share=max_imputed_share,
                )
                rows.append({
                    "iso3": iso3, "pillar_id": pillar_id, "year": year,
                    "score": float(np.mean(vals)) if vals else np.nan,
                    "n_indicators": n_indicators,
                    "n_observed": n_observed,
                    "n_imputed": n_imputed,
                    "coverage_ratio": n_observed / n_indicators if n_indicators else 0.0,
                    "reliability": reliability.value,
                    "contributing": ",".join(contributing),
                })

    return pd.DataFrame(rows)


# ── Composite level ────────────────────────────────────────────────────────────

def weighted_composite(
    pillar_wide: pd.DataFrame,
    weights: dict[str, float],
) -> pd.Series:
    """
    Weighted mean over the pillars a country actually has, renormalising the
    weights across those pillars.

    Covers equal, PCA, entropy, and custom weighting — they differ only in where
    the weights come from.
    """
    pillars = [p for p in weights if p in pillar_wide.columns]
    w = np.array([weights[p] for p in pillars], dtype=float)
    out = {}
    for idx, row in pillar_wide[pillars].iterrows():
        vals = row.to_numpy(dtype=float)
        valid = ~np.isnan(vals)
        if not valid.any():
            out[idx] = np.nan
            continue
        wv = w[valid] / w[valid].sum()
        out[idx] = float(np.dot(wv, vals[valid]))
    return pd.Series(out)


def geometric_composite(
    pillar_wide: pd.DataFrame,
    pillars: list[str],
    small: float,
) -> pd.Series:
    """
    exp(sum(w_i * ln(s_i))) with equal weights — partially non-compensatory, so
    a collapsed pillar cannot be fully offset by a strong one. Scores are floored
    at `small` because ln(0) is undefined.
    """
    present = [p for p in pillars if p in pillar_wide.columns]
    out = {}
    for idx, row in pillar_wide[present].iterrows():
        vals = row.to_numpy(dtype=float)
        valid = ~np.isnan(vals)
        if not valid.any():
            out[idx] = np.nan
            continue
        v = np.maximum(vals[valid], small)
        w = np.full(v.shape, 1.0 / v.size)
        out[idx] = float(np.exp(np.dot(w, np.log(v))))
    return pd.Series(out)


def fit_pca_weights(pillar_wide: pd.DataFrame, pillars: list[str], small: float) -> dict[str, float]:
    """
    First principal component of the pooled panel as pillar weights.

    Fitted on complete rows only, then reused for every year. Pillars whose
    loading is negative after orientation load *against* the stability dimension;
    they are excluded (weight 0) rather than absolute-valued, since taking the
    absolute value would silently invert their contribution.
    """
    present = [p for p in pillars if p in pillar_wide.columns]
    complete = pillar_wide[present].dropna()
    if complete.shape[0] < len(present):
        return {p: 1.0 / len(present) for p in present}

    corr = np.corrcoef(complete.to_numpy(dtype=float), rowvar=False)
    evals, evecs = np.linalg.eigh(corr)
    loadings = evecs[:, -1].copy()
    if (loadings < 0).sum() > len(loadings) / 2:
        loadings = -loadings
    loadings = np.where(loadings < 0, 0.0, loadings)
    if loadings.sum() < small:
        return {p: 1.0 / len(present) for p in present}
    weights = loadings / loadings.sum()
    return {p: float(w) for p, w in zip(present, weights)}


def fit_entropy_weights(pillar_wide: pd.DataFrame, pillars: list[str], small: float) -> dict[str, float]:
    """
    Shannon-entropy weights: a pillar that separates countries carries more
    information and earns more weight. Fitted once on the pooled panel.
    """
    present = [p for p in pillars if p in pillar_wide.columns]
    sub = pillar_wide[present].copy()
    n = len(sub)
    if n == 0:
        return {p: 1.0 / len(present) for p in present}

    for col in present:
        mn = sub[col].min(skipna=True)
        if pd.notna(mn) and mn <= 0:
            sub[col] = sub[col] - mn + small

    ent = {}
    for col in present:
        vals = sub[col].fillna(sub[col].mean())
        total = vals.sum()
        if total == 0 or pd.isna(total):
            ent[col] = 0.0
            continue
        p = (vals / total).clip(lower=small)
        ent[col] = float(-np.sum(p * np.log(p)))

    ln_n = np.log(n) if n > 1 else 1.0
    divergence = {c: 1.0 - ent[c] / ln_n for c in present}
    total_div = sum(divergence.values())
    if total_div <= 0:
        return {p: 1.0 / len(present) for p in present}
    return {c: v / total_div for c, v in divergence.items()}


def composite_reliability(
    pillar_year: pd.DataFrame,
    min_pillars: int,
) -> Reliability:
    """
    A composite is only as honest as the pillars under it.

    Unreliable unless at least `min_pillars` pillars are displayable; reliable
    only when every displayable pillar is itself reliable.
    """
    tiers = [Reliability(t) for t in pillar_year["reliability"]]
    usable = [t for t in tiers if t.displayable]
    if len(usable) < min_pillars:
        return Reliability.UNRELIABLE
    if all(t is Reliability.RELIABLE for t in usable):
        return Reliability.RELIABLE
    return Reliability.THIN


__all__ = [
    "pillar_scores", "weighted_composite", "geometric_composite",
    "fit_pca_weights", "fit_entropy_weights", "composite_reliability",
]
