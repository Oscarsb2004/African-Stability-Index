"""
verify/stats.py — the statistical primitives behind the advisory layer.

Separated from `advisory.py` so the arithmetic can be unit-tested on data whose
answer is known in advance, rather than only on the panel, where nobody can say
what the right answer is. `tests/test_advisory_stats.py` checks every function
here three ways: against closed-form cases computed by hand, against algebraic
properties that must hold for any input, and against an independent third-party
implementation (`pingouin`, `factor_analyzer`) where one exists.

Everything here is plain numpy. No `asi` import, per the rule
`tests/test_verify_independence.py` enforces: a diagnostic that imported the
pipeline's own scoring code would be checking that code against itself.

**On polarity.** Cronbach's alpha and item-rest correlations are only
interpretable when every item points the same way. They are computed here on the
panel's `score` column, which `asi/pipeline/normalize.py` has already inverted
for negative-polarity indicators — so alignment is a property of the input, not
something this module has to do. The retired pre-panel implementation ran on raw
mixed-polarity values, which mechanically deflates alpha for any pillar holding a
reversed item; that is why its warnings were uninterpretable and why the
threshold was lowered to 0.60 to accommodate them. Passing raw values here would
reintroduce exactly that bug, silently.

**On listwise deletion.** Every function drops rows with any missing item.
Pairwise deletion would compute each covariance on a different subset, which can
produce a correlation matrix that is not positive semi-definite and an alpha with
no coherent interpretation. The number of complete rows is returned alongside
every statistic so a figure resting on eleven countries cannot be quoted as
though it rested on fifty-four.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

#: Below this many complete observations, a statistic is reported as undefined
#: rather than computed. Three is the floor at which a correlation is defined at
#: all; it is not a floor at which one is trustworthy.
MIN_COMPLETE_ROWS = 3


# ── Internal consistency ───────────────────────────────────────────────────────

@dataclass(slots=True)
class AlphaResult:
    """Cronbach's alpha for one group of items, with what it was computed on."""

    alpha: float | None
    k: int                      # items entering the calculation
    n: int                      # complete observations
    item_variances: dict[str, float] = field(default_factory=dict)
    total_variance: float = float("nan")
    note: str = ""

    @property
    def defined(self) -> bool:
        return self.alpha is not None


def cronbach_alpha(frame: pd.DataFrame) -> AlphaResult:
    """
    Cronbach's alpha over the columns of `frame`, rows as observations.

        alpha = k/(k-1) * (1 - sum(var_i) / var_total)

    where `var_total` is the variance of the row sums. Sample variance (ddof=1)
    throughout, which is the convention every reference implementation uses.

    Returns `alpha=None` rather than raising when alpha is undefined: fewer than
    two items (the k/(k-1) term diverges), fewer than MIN_COMPLETE_ROWS complete
    rows, or a zero-variance total (every country scoring identically, which
    carries no information about consistency).

    Alpha is not a measure of unidimensionality, and a high value is not
    self-evidently good: it rises mechanically with the number of items and with
    redundancy among them. A pillar of six near-identical indicators will report
    excellent alpha precisely because it measures one thing six times.
    """
    data = frame.dropna(axis=0, how="any")
    n, k = data.shape

    if k < 2:
        return AlphaResult(None, k, n, note="alpha needs at least 2 items")
    if n < MIN_COMPLETE_ROWS:
        return AlphaResult(None, k, n,
                           note=f"only {n} complete rows; need {MIN_COMPLETE_ROWS}")

    values = data.to_numpy(dtype=float)
    item_var = values.var(axis=0, ddof=1)
    total_var = float(values.sum(axis=1).var(ddof=1))

    if total_var <= 0:
        return AlphaResult(None, k, n, note="zero variance in the summed score")

    alpha = (k / (k - 1)) * (1.0 - item_var.sum() / total_var)
    return AlphaResult(
        alpha=float(alpha),
        k=k,
        n=n,
        item_variances={c: float(v) for c, v in zip(data.columns, item_var)},
        total_variance=total_var,
    )


def item_rest_correlations(frame: pd.DataFrame) -> dict[str, float | None]:
    """
    Correlation of each item with the sum of the *others*, per column.

    Item-total correlation — correlating an item with a total that includes it —
    is inflated by construction, and the inflation is worst for exactly the small
    groups where the diagnostic matters most. Item-rest is the honest form.

    A near-zero or negative value says the item does not belong with the others,
    which is the single most useful signal for whether an indicator sits in the
    right pillar. Interpretation: negative means check polarity first; below
    about 0.30 means the item may belong elsewhere.

    Returns None for an item whose own variance is zero, or whose rest-sum has
    zero variance, since a correlation is undefined there.
    """
    data = frame.dropna(axis=0, how="any")
    out: dict[str, float | None] = {}

    if data.shape[0] < MIN_COMPLETE_ROWS or data.shape[1] < 2:
        return {c: None for c in frame.columns}

    values = data.to_numpy(dtype=float)
    row_totals = values.sum(axis=1)

    for j, column in enumerate(data.columns):
        item = values[:, j]
        rest = row_totals - item
        if item.std(ddof=1) == 0 or rest.std(ddof=1) == 0:
            out[column] = None
            continue
        out[column] = float(np.corrcoef(item, rest)[0, 1])

    return out


# ── Dimensionality ─────────────────────────────────────────────────────────────

@dataclass(slots=True)
class DimensionalityResult:
    """
    Eigenstructure of a correlation matrix, and the level it describes.

    `level` is not decoration. This repository has carried two eigenvalue reports
    that read as contradictory — PC1 explaining 62% and PC1 explaining 33.6% —
    which are simply the same analysis at different levels, one over 7 pillar
    scores and one over 32 indicators. Neither figure stated its level alongside
    the number, so both were quoted in arguments they did not support. Any
    dimensionality figure this module produces carries its level with it.
    """

    level: str
    eigenvalues: list[float]
    explained: list[float]          # share of total variance per component
    cumulative: list[float]
    n_kaiser: int                   # components with eigenvalue > 1
    n_for_90pct: int
    n: int
    k: int

    def summary(self) -> str:
        first = self.explained[0] * 100 if self.explained else float("nan")
        return (f"{self.level}: {self.k} variables, {self.n} observations; "
                f"PC1 explains {first:.1f}%; {self.n_kaiser} components above "
                f"eigenvalue 1; {self.n_for_90pct} needed for 90% of variance")


def pca_dimensionality(frame: pd.DataFrame, level: str) -> DimensionalityResult:
    """
    Eigenvalues of the correlation matrix, with variance explained.

    On the correlation matrix rather than the covariance matrix, so that
    indicators on wildly different raw scales contribute comparably — the
    convention for composite-indicator work and what the pipeline's own PCA
    weighting uses.

    Computed by singular value decomposition of the standardised data, not by
    `np.linalg.eigh` of the correlation matrix. That is deliberate:
    `asi/pipeline/score.py::fit_pca_weights` uses `eigh`, and a diagnostic that
    reproduced its route would agree with it even where both were wrong. SVD of
    the standardised matrix is mathematically equivalent and numerically better
    conditioned, which matters here because Pillar A's items correlate above 0.9.
    """
    data = frame.dropna(axis=0, how="any")
    n, k = data.shape
    if n < MIN_COMPLETE_ROWS or k < 2:
        return DimensionalityResult(level, [], [], [], 0, 0, n, k)

    values = data.to_numpy(dtype=float)
    centred = values - values.mean(axis=0)
    sd = values.std(axis=0, ddof=1)
    sd[sd == 0] = 1.0                      # a constant column contributes nothing
    standardised = centred / sd

    # Singular values of the standardised matrix relate to correlation-matrix
    # eigenvalues by lambda = s^2 / (n - 1).
    singular = np.linalg.svd(standardised, compute_uv=False)
    eigenvalues = (singular ** 2) / (n - 1)
    eigenvalues = np.clip(eigenvalues, 0.0, None)

    total = eigenvalues.sum()
    explained = eigenvalues / total if total > 0 else np.zeros_like(eigenvalues)
    cumulative = np.cumsum(explained)

    n_for_90 = int(np.searchsorted(cumulative, 0.90) + 1) if total > 0 else 0

    return DimensionalityResult(
        level=level,
        eigenvalues=[float(v) for v in eigenvalues],
        explained=[float(v) for v in explained],
        cumulative=[float(v) for v in cumulative],
        n_kaiser=int((eigenvalues > 1.0).sum()),
        n_for_90pct=min(n_for_90, k),
        n=n,
        k=k,
    )


# ── Is the data factorable at all? ─────────────────────────────────────────────

def kmo(frame: pd.DataFrame) -> tuple[float | None, dict[str, float]]:
    """
    Kaiser-Meyer-Olkin measure of sampling adequacy, overall and per variable.

        KMO = sum(r_ij^2) / (sum(r_ij^2) + sum(p_ij^2)),  i != j

    comparing observed correlations against partial correlations. When variables
    share common factors the partials are small and KMO approaches 1; when each
    correlation is a private affair between two variables, factor analysis has
    nothing to find.

    Kaiser's own labels: below 0.50 unacceptable, 0.50-0.60 miserable, 0.60-0.70
    mediocre, 0.70-0.80 middling, 0.80-0.90 meritorious, above 0.90 marvellous.

    This runs *before* extracting factors, because extraction always returns
    something. A factor solution on unfactorable data is noise with loadings.
    """
    data = frame.dropna(axis=0, how="any")
    if data.shape[0] < MIN_COMPLETE_ROWS or data.shape[1] < 2:
        return None, {}

    corr = np.corrcoef(data.to_numpy(dtype=float), rowvar=False)
    if not np.all(np.isfinite(corr)):
        return None, {}

    # Pseudo-inverse: the correlation matrix is near-singular whenever two
    # indicators are near-duplicates, which is a live condition in Pillar A.
    inverse = np.linalg.pinv(corr)
    d = np.sqrt(np.diag(inverse))
    partial = -inverse / np.outer(d, d)
    np.fill_diagonal(partial, 0.0)

    observed = corr.copy()
    np.fill_diagonal(observed, 0.0)

    sum_r2 = float((observed ** 2).sum())
    sum_p2 = float((partial ** 2).sum())
    overall = sum_r2 / (sum_r2 + sum_p2) if (sum_r2 + sum_p2) > 0 else None

    per_variable = {}
    for j, column in enumerate(data.columns):
        r2 = float((observed[j] ** 2).sum())
        p2 = float((partial[j] ** 2).sum())
        per_variable[column] = r2 / (r2 + p2) if (r2 + p2) > 0 else float("nan")

    return overall, per_variable


def bartlett_sphericity(frame: pd.DataFrame) -> tuple[float | None, int]:
    """
    Bartlett's test of sphericity: is the correlation matrix distinguishable
    from the identity?

        chi2 = -((n - 1) - (2k + 5)/6) * ln(det(R)),   df = k(k-1)/2

    Returns (chi-square, degrees of freedom). A p-value needs a chi-square
    distribution, which lives in scipy; the caller converts. A non-significant
    result means the variables are essentially uncorrelated and there is nothing
    for a factor model to explain.

    Nearly always significant at any real sample size, so it is a floor, not
    evidence of a good factor solution. KMO is the more informative of the two.
    """
    data = frame.dropna(axis=0, how="any")
    n, k = data.shape
    if n < MIN_COMPLETE_ROWS or k < 2:
        return None, 0

    corr = np.corrcoef(data.to_numpy(dtype=float), rowvar=False)
    sign, logdet = np.linalg.slogdet(corr)
    if sign <= 0:                   # singular: perfectly collinear variables
        return None, k * (k - 1) // 2

    chi2 = -((n - 1) - (2 * k + 5) / 6.0) * logdet
    return float(chi2), k * (k - 1) // 2


# ── Does the declared structure match the data? ────────────────────────────────

def varimax(
    loadings: np.ndarray,
    *,
    normalize: bool = True,
    tol: float = 1e-6,
    max_iter: int = 500,
) -> np.ndarray:
    """
    Varimax rotation: the orthogonal rotation maximising the variance of squared
    loadings within each factor.

    Extraction fixes the *subspace* the factors span, not the axes chosen inside
    it, so unrotated loadings are arbitrary to that extent and typically spread
    every variable across every factor. Rotation picks axes on which each
    variable loads heavily on few factors, which is what makes "which factor does
    this indicator belong to" a question with an answer.

    Orthogonal, so the rotated factors stay uncorrelated. Oblique rotation
    (promax) would allow correlated factors and is arguably the better fit for
    pillars that plainly do correlate — but it gives up the clean
    variance-partition reading, and this is a diagnostic rather than a model.

    `normalize` applies **Kaiser normalisation**: rows are scaled to unit length
    before rotating and rescaled after, so that a variable with small
    communality pulls on the solution as hard as one with large communality.
    It is on by default because it is the convention SPSS, R's `varimax` and
    `factor_analyzer` all use — the cross-check in
    `tests/test_advisory_stats.py` disagreed with the reference implementation by
    up to 0.048 per loading until this was added, which is small enough to look
    like numerical noise and large enough to move a borderline assignment.
    """
    rotated = np.asarray(loadings, dtype=float)
    k, n_factors = rotated.shape
    if n_factors < 2:
        return rotated.copy()

    if normalize:
        communalities = np.sqrt((rotated ** 2).sum(axis=1))
        communalities[communalities == 0] = 1.0
        rotated = rotated / communalities[:, None]

    base = rotated.copy()
    rotation = np.eye(n_factors)
    previous = 0.0
    for _ in range(max_iter):
        transformed = base @ rotation
        cubed = transformed ** 3
        column_means = transformed * (transformed ** 2).sum(axis=0) / k
        u, s, vt = np.linalg.svd(base.T @ (cubed - column_means))
        rotation = u @ vt
        current = s.sum()
        if previous != 0 and current / previous < 1 + tol:
            break
        previous = current

    result = base @ rotation
    if normalize:
        result = result * communalities[:, None]
    return result


#: Complete observations per variable below which a factor solution is not
#: reportable. Conventional guidance ranges from 5 to 10 per variable; 5 is the
#: lenient end, chosen so the gate flags only cases that are indefensible rather
#: than merely thin.
#:
#: This gate is not decoration. At the 2023 reference year the panel has 31
#: countries with complete data across 32 scoring indicators — 0.97 observations
#: per variable, and a correlation matrix of rank 30 out of 32. A factor routine
#: run on that still returns loadings, an assignment for every indicator, and an
#: adjusted Rand index that looks exactly like a finding. It is not one.
MIN_OBS_PER_VARIABLE = 5.0


@dataclass(slots=True)
class StructureResult:
    """How well a declared grouping of variables matches the data's own."""

    declared: dict[str, str]            # variable -> declared group
    recovered: dict[str, int]           # variable -> factor it loads highest on
    loadings: pd.DataFrame              # variables x factors, rotated
    agreement: float                    # adjusted Rand index, 1.0 = identical
    cohesion: dict[str, float]          # group -> share of members sharing a factor
    n_factors: int
    n: int
    kmo: float | None = None
    cross_listed: tuple[str, ...] = ()
    note: str = ""
    k: int = 0
    obs_per_variable: float = float("nan")
    rank: int = 0
    reportable: bool = False
    inadequacy: str = ""

    @property
    def singular(self) -> bool:
        """A rank-deficient correlation matrix cannot support a factor model."""
        return self.k > 0 and self.rank < self.k


def structure_agreement(
    frame: pd.DataFrame,
    declared: dict[str, list[str]],
    *,
    n_factors: int | None = None,
) -> StructureResult:
    """
    Compare a declared grouping of variables against the factor structure the
    data actually shows.

    `declared` maps group name -> member variables, which is the shape of both a
    pillar map and any other index structure. Nothing here knows what a pillar
    is, so the same function evaluates an SDG tree or any later framework — the
    question "does this structure hold up?" is not specific to this index.

    Method: maximum-likelihood factor extraction (`sklearn.decomposition
    .FactorAnalysis`) with `n_factors` factors, varimax-rotated, then each
    variable assigned to the factor carrying its largest absolute loading. The
    declared partition and the recovered partition are compared by adjusted Rand
    index — chance-corrected, so the score for an arbitrary grouping is ~0 rather
    than the ~0.3 a raw Rand index would give.

    **A low score is not automatically a defect.** A *reflective* structure, in
    which pillars are alternative measurements of one latent construct, should
    recover cleanly. A *formative* one, in which pillars are constituent parts
    that jointly define the construct, need not: GDP and literacy belong in the
    same index without belonging to the same factor. Which of the two this index
    is has never been decided, and that decision governs how this number should
    be read. Reported either way, because "we have not measured it" and "we
    measured it and it disagrees" are different positions to argue from.

    Cross-listed variables are assigned to their first declared group so the
    comparison has a partition to work with; they are listed in the result, since
    a structure with many of them is one this measure describes less well.
    """
    from sklearn.decomposition import FactorAnalysis
    from sklearn.metrics import adjusted_rand_score

    seen: dict[str, str] = {}
    cross_listed: list[str] = []
    for group, members in declared.items():
        for member in members:
            if member in seen:
                cross_listed.append(member)
            else:
                seen[member] = group

    columns = [c for c in frame.columns if c in seen]
    data = frame[columns].dropna(axis=0, how="any")
    n, k = data.shape
    n_factors = n_factors or len(declared)

    if n < MIN_COMPLETE_ROWS or k < 2 or n_factors < 1:
        return StructureResult({}, {}, pd.DataFrame(), float("nan"), {},
                               n_factors, n, note="too little complete data",
                               k=k, obs_per_variable=n / k if k else float("nan"))
    n_factors = min(n_factors, k)

    # Adequacy, established before anything is extracted. A factor routine always
    # returns a solution; whether the data can support one is a separate question
    # and has to be asked first, or the answer to it never gets asked at all.
    per_variable = n / k
    correlation = np.corrcoef(data.to_numpy(dtype=float), rowvar=False)
    rank = int(np.linalg.matrix_rank(correlation))

    reasons = []
    if rank < k:
        reasons.append(f"correlation matrix is singular (rank {rank} of {k})")
    if per_variable < MIN_OBS_PER_VARIABLE:
        reasons.append(f"{per_variable:.2f} complete observations per variable, "
                       f"below the {MIN_OBS_PER_VARIABLE:.0f} minimum")

    values = data.to_numpy(dtype=float)
    standardised = (values - values.mean(axis=0)) / np.where(
        values.std(axis=0, ddof=1) == 0, 1.0, values.std(axis=0, ddof=1)
    )

    model = FactorAnalysis(n_components=n_factors, random_state=0).fit(standardised)
    rotated = varimax(model.components_.T)
    loadings = pd.DataFrame(
        rotated, index=columns, columns=[f"F{i + 1}" for i in range(n_factors)]
    )

    recovered = {v: int(np.argmax(np.abs(loadings.loc[v].to_numpy())))
                 for v in columns}
    declared_for = {v: seen[v] for v in columns}

    group_ids = {g: i for i, g in enumerate(sorted(set(declared_for.values())))}
    agreement = float(adjusted_rand_score(
        [group_ids[declared_for[v]] for v in columns],
        [recovered[v] for v in columns],
    ))

    cohesion: dict[str, float] = {}
    for group in sorted(set(declared_for.values())):
        members = [v for v in columns if declared_for[v] == group]
        if not members:
            continue
        factors = [recovered[v] for v in members]
        most_common = max(set(factors), key=factors.count)
        cohesion[group] = factors.count(most_common) / len(members)

    return StructureResult(
        declared=declared_for,
        recovered=recovered,
        loadings=loadings,
        agreement=agreement,
        cohesion=cohesion,
        n_factors=n_factors,
        n=n,
        kmo=kmo(data)[0],
        cross_listed=tuple(sorted(set(cross_listed))),
        k=k,
        obs_per_variable=per_variable,
        rank=rank,
        reportable=not reasons,
        inadequacy="; ".join(reasons),
    )


__all__ = [
    "MIN_COMPLETE_ROWS",
    "AlphaResult", "cronbach_alpha", "item_rest_correlations",
    "DimensionalityResult", "pca_dimensionality",
    "kmo", "bartlett_sphericity",
    "varimax", "StructureResult", "structure_agreement",
]
