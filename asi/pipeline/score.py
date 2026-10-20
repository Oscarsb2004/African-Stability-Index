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
from scipy.stats import t as t_dist

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
                    elif p in ("carried_forward", "regional_mean", "regional_quantile", "interpolated"):
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

#: Tiers a pillar may have and still enter a composite (edition 2, step 7, plan 4.1).
COMPOSABLE = ("reliable", "thin")


def composite_inputs(pil: pd.DataFrame, index: list[str] | None = None) -> pd.DataFrame:
    """
    Pillar scores, wide, with every pillar that is not displayable left out.

    Edition 1 averaged an unreliable pillar into the composite at full weight:
    61 pillar cells at 2023 that the interface itself greys out still moved the
    headline. From edition 2 such a pillar is blank here, so every composite
    averages only the pillars it can show, and reports how many (k).
    """
    index = index or ["iso3", "year"]
    wide = pil.pivot_table(index=index, columns="pillar_id", values="score", aggfunc="first")
    tiers = pil.pivot_table(index=index, columns="pillar_id", values="reliability", aggfunc="first")
    return wide.where(tiers.reindex(index=wide.index, columns=wide.columns).isin(COMPOSABLE))


def lack_of_reliability(panel: pd.DataFrame, scoring: list[str], max_carry: int) -> pd.Series:
    """
    An INFORM-style lack-of-reliability index per country-year, 0 (reliable) to 10.

        LRI = 10 x (gap + age) / 2, over the scoring indicators, where
        gap = the share not measured that year (absent, carried forward or imputed)
        age = the mean age of the values present, as a share of the carry-forward limit
              (1 when nothing is present)

    INFORM builds its index from missing and imputed data and from the age of
    the data; these are its two components that apply to a national index.
    """
    sub = panel[panel["variable_name"].isin(scoring)]
    keys = [sub["iso3"], sub["year"]]
    gap = (~sub["provenance"].isin(["observed", "derived"])).groupby(keys).mean()
    staleness = sub["year"] - pd.to_numeric(sub["source_year"])
    age = (staleness.where(sub["raw_value"].notna()) / max_carry).groupby(keys).mean()
    return 10 * (gap + age.fillna(1.0)) / 2


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


# ── Uncertainty, bands and tiers (edition 2, step 8) ───────────────────────────

def composite_interval(pillar_wide: pd.DataFrame, level: float) -> pd.DataFrame:
    """
    The headline is the mean of a sample of k pillar scores, so it has a standard
    error and a t interval (plan 2.2):

        SE = SD / sqrt(k),   M ± t(k - 1) x SE

    over the pillars the composite used. One pillar has no spread, so no interval.
    The spread of a state's pillar scores is the standard error the owner ruled
    for the bands (2026-10-17; kept when P58 allowed formative pillars). Where a
    pillar is formative, part of that spread is real rather than error, so the
    interval errs wide (plan 2.3).
    """
    k = pillar_wide.notna().sum(axis=1)
    mean = pillar_wide.mean(axis=1)
    se = pillar_wide.std(axis=1, ddof=1) / np.sqrt(k)
    t = pd.Series(t_dist.ppf((1 + level) / 2, k.where(k > 1) - 1), index=k.index)
    return pd.DataFrame({"mean": mean, "se": se, "low": mean - t * se, "high": mean + t * se})


def _z(scores: pd.Series, errors: pd.Series) -> np.ndarray:
    """z[i, j] = (M_j - M_i) / sqrt(SE_i^2 + SE_j^2): positive when j scores higher than i."""
    m, s = scores.to_numpy(dtype=float), errors.to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (m[None, :] - m[:, None]) / np.sqrt(s[None, :] ** 2 + s[:, None] ** 2)


def rank_bands(scores: pd.Series, errors: pd.Series, z: float) -> pd.DataFrame:
    """
    The ranks a state could hold (plan 2.3). Two states differ only if
    |M1 - M2| / sqrt(SE1^2 + SE2^2) exceeds z, the test for two independent
    estimates. A state's band runs from 1 + the number significantly above it to
    N - the number significantly below it; rank 1 is the highest score.
    """
    stat = _z(scores, errors)
    return pd.DataFrame({"band_best": 1 + (stat > z).sum(axis=1),
                         "band_worst": len(scores) - (stat < -z).sum(axis=1)}, index=scores.index)


def tiers(scores: pd.Series, errors: pd.Series, z: float) -> pd.Series:
    """
    Tiers by the leader rule (P96). From the highest score down, a tier holds
    every state not significantly below the tier's first state, by the same z
    test; the first state significantly below it starts the next tier.

    The plan's rule, "bands that overlap form a tier", chains: with bands a median
    of 42 places wide, every band overlaps its neighbour's, and all 54 states fell
    into one tier at 2024, 2023 and 2015.
    """
    order = scores.sort_values(ascending=False, kind="mergesort").index
    out, lead, tier = {}, None, 0
    for state in order:
        if lead is not None:
            with np.errstate(divide="ignore", invalid="ignore"):
                gap = (scores[lead] - scores[state]) / np.hypot(errors[lead], errors[state])
        if lead is None or gap > z:
            lead, tier = state, tier + 1
        out[state] = tier
    return pd.Series(out, dtype="Int64").reindex(scores.index)


def effective_weights(pillar_map: dict[str, list[str]], present: pd.DataFrame | None = None) -> pd.Series:
    """
    Each indicator's share of the headline (plan 4.10). Edition 1 hid that the
    WGI carried 28.9% of its weight.

    Nominal (no `present`): every pillar with members weighs 1/P, and each of its
    n indicators 1/n of that, summed over the pillars an indicator is in.

    Realised: `present` is the pillar scores of one year (iso3, pillar_id,
    contributing) for the pillars that entered each state's headline. A state
    with k pillars gives each 1/k, and each pillar's m contributing indicators
    1/m of that; the result is the mean over the states.
    """
    if present is None:
        pillars = {p: m for p, m in pillar_map.items() if m}
        rows = [(v, 1 / (len(pillars) * len(m))) for m in pillars.values() for v in m]
        return pd.DataFrame(rows, columns=["variable_name", "w"]).groupby("variable_name")["w"].sum()
    rows = []
    for state, g in present.groupby("iso3"):
        for members in g["contributing"]:
            names = [v for v in str(members).split(",") if v]
            rows += [(state, v, 1 / (len(g) * len(names))) for v in names]
    shares = pd.DataFrame(rows, columns=["iso3", "variable_name", "w"])
    per_state = shares.pivot_table(index="iso3", columns="variable_name", values="w", aggfunc="sum", fill_value=0.0)
    return per_state.mean()


__all__ = [
    "pillar_scores", "weighted_composite", "geometric_composite",
    "fit_pca_weights", "fit_entropy_weights", "composite_reliability",
    "COMPOSABLE", "composite_inputs", "lack_of_reliability",
    "composite_interval", "rank_bands", "tiers", "effective_weights",
]
