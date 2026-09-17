"""
The advisory layer's statistics, checked three ways.

A diagnostic that is wrong is worse than one that is missing: it produces a
number, the number gets quoted, and nothing about it looks broken. The figures
these functions produce are destined for the methodology documentation, so each
one is checked

  1. against a case whose answer was computed by hand and written into the test
     as a literal — the only check that catches an error shared by every
     implementation of the same formula;
  2. against algebraic properties that must hold whatever the input — alpha of
     identical items is 1, correlation-matrix eigenvalues sum to the number of
     variables, and so on;
  3. against an independent third-party implementation — `pingouin` for alpha,
     `factor_analyzer` for KMO and Bartlett, `scikit-learn` for the
     eigenstructure.

The third-party checks skip cleanly where those packages are absent, so the
suite still passes on a machine with only the pipeline requirements installed.
Install them with `pip install -r requirements-dev.txt` to run the full battery.
"""

import numpy as np
import pandas as pd
import pytest

from verify.stats import (
    MIN_COMPLETE_ROWS,
    bartlett_sphericity,
    cronbach_alpha,
    item_rest_correlations,
    kmo,
    pca_dimensionality,
)

# ── Fixtures ───────────────────────────────────────────────────────────────────

#: Four subjects, three items. Every intermediate quantity is small enough to
#: check on paper, which is the point: the expected alpha below was derived by
#: hand, not by running the function it tests.
#:
#:   item variances (ddof=1): 5/3, 35/12, 35/12   -> sum 15/2
#:   row sums: 6, 9, 12, 17   -> variance 22
#:   alpha = 3/2 * (1 - 7.5/22) = 21.75/22
HAND_FRAME = pd.DataFrame({
    "a": [1.0, 2.0, 3.0, 4.0],
    "b": [2.0, 3.0, 4.0, 6.0],
    "c": [3.0, 4.0, 5.0, 7.0],
})
HAND_ALPHA = 21.75 / 22.0


@pytest.fixture
def rng():
    return np.random.default_rng(20260906)


@pytest.fixture
def correlated(rng):
    """Six items sharing one latent factor, with independent noise."""
    latent = rng.normal(size=60)
    data = {f"v{i}": latent * w + rng.normal(scale=0.5, size=60)
            for i, w in enumerate([1.0, 0.9, 1.1, 0.8, 1.2, 0.95])}
    return pd.DataFrame(data)


@pytest.fixture
def independent(rng):
    """Six items with no shared structure."""
    return pd.DataFrame({f"v{i}": rng.normal(size=60) for i in range(6)})


# ── Cronbach's alpha: computed by hand ─────────────────────────────────────────

def test_alpha_matches_hand_computation():
    result = cronbach_alpha(HAND_FRAME)
    assert result.defined
    assert result.alpha == pytest.approx(HAND_ALPHA, abs=1e-12)
    assert (result.k, result.n) == (3, 4)


def test_alpha_reports_the_variances_it_used():
    """The parts must be inspectable, or a wrong total cannot be diagnosed."""
    result = cronbach_alpha(HAND_FRAME)
    assert result.item_variances["a"] == pytest.approx(5 / 3)
    assert result.item_variances["b"] == pytest.approx(35 / 12)
    assert result.total_variance == pytest.approx(22.0)


# ── Cronbach's alpha: properties that must hold for any input ──────────────────

def test_alpha_of_identical_items_is_one(rng):
    column = rng.normal(size=40)
    frame = pd.DataFrame({f"v{i}": column for i in range(4)})
    assert cronbach_alpha(frame).alpha == pytest.approx(1.0, abs=1e-10)


def test_alpha_is_invariant_to_item_order(correlated, rng):
    forward = cronbach_alpha(correlated).alpha
    shuffled = correlated[list(rng.permutation(correlated.columns))]
    assert cronbach_alpha(shuffled).alpha == pytest.approx(forward)


def test_alpha_is_invariant_to_common_rescaling(correlated):
    """Both terms of the ratio scale by c^2, so alpha must not move."""
    base = cronbach_alpha(correlated).alpha
    assert cronbach_alpha(correlated * 7.5).alpha == pytest.approx(base)


def test_alpha_is_not_high_for_independent_items(independent):
    """
    No shared variance means nothing to be internally consistent about.

    One-sided on purpose. Alpha is centred near zero here but has wide sampling
    variance, and it is *unbounded below* — this fixture returns -0.469, which
    `pingouin` reproduces to twelve decimal places. Asserting `abs(alpha)` would
    fail on correct arithmetic, which is how this test was first written.
    """
    assert cronbach_alpha(independent).alpha < 0.3


def test_alpha_can_be_negative(independent):
    """
    Negative alpha is a real result, not an error state, and the function must
    return it rather than clamping to zero. It means the average inter-item
    covariance is negative — the items are not measuring one thing, and for a
    pillar that is a finding rather than a glitch to be tidied away.
    """
    result = cronbach_alpha(independent)
    assert result.defined
    assert result.alpha < 0


def test_alpha_rises_with_shared_variance(correlated, independent):
    assert cronbach_alpha(correlated).alpha > cronbach_alpha(independent).alpha


def test_alpha_rises_when_a_redundant_item_is_added(correlated):
    """
    The property that makes a high alpha weak evidence on its own: duplicating an
    item raises alpha without adding information. Pillar A is the live instance —
    six WGI items correlating up to 0.93.
    """
    before = cronbach_alpha(correlated).alpha
    padded = correlated.assign(duplicate=correlated["v0"])
    assert cronbach_alpha(padded).alpha > before


# ── Cronbach's alpha: undefined cases return, never raise ──────────────────────

def test_alpha_undefined_for_a_single_item():
    result = cronbach_alpha(HAND_FRAME[["a"]])
    assert result.alpha is None and "2 items" in result.note


def test_alpha_undefined_for_too_few_complete_rows():
    result = cronbach_alpha(HAND_FRAME.head(MIN_COMPLETE_ROWS - 1))
    assert result.alpha is None and "complete rows" in result.note


def test_alpha_undefined_when_the_total_does_not_vary():
    """Constant items carry no information; the formula would divide by zero."""
    frame = pd.DataFrame({"a": [2.0] * 8, "b": [5.0] * 8})
    result = cronbach_alpha(frame)
    assert result.alpha is None and "zero variance" in result.note


def test_alpha_uses_listwise_deletion():
    frame = HAND_FRAME.copy()
    frame.loc[0, "b"] = np.nan
    result = cronbach_alpha(frame)
    assert result.n == 3
    assert result.alpha == pytest.approx(cronbach_alpha(HAND_FRAME.iloc[1:]).alpha)


# ── Item-rest correlations ─────────────────────────────────────────────────────

def test_item_rest_of_identical_items_is_one(rng):
    column = rng.normal(size=30)
    frame = pd.DataFrame({f"v{i}": column for i in range(3)})
    for value in item_rest_correlations(frame).values():
        assert value == pytest.approx(1.0, abs=1e-10)


def test_item_rest_is_negative_for_a_reversed_item(correlated):
    """The signature of an indicator whose polarity is coded the wrong way."""
    frame = correlated.assign(reversed_item=-correlated["v0"])
    assert item_rest_correlations(frame)["reversed_item"] < 0


def test_item_rest_excludes_the_item_from_its_own_total():
    """
    Item-*total* would correlate a column against a sum containing it, which is
    inflated by construction. Two independent columns must therefore score near
    zero here, where item-total would not.
    """
    rng = np.random.default_rng(7)
    frame = pd.DataFrame({"a": rng.normal(size=200), "b": rng.normal(size=200)})
    assert abs(item_rest_correlations(frame)["a"]) < 0.2


def test_item_rest_matches_an_explicit_computation(correlated):
    rest = correlated.drop(columns=["v0"]).sum(axis=1)
    expected = np.corrcoef(correlated["v0"], rest)[0, 1]
    assert item_rest_correlations(correlated)["v0"] == pytest.approx(expected)


def test_item_rest_is_none_for_a_constant_item(correlated):
    frame = correlated.assign(flat=1.0)
    assert item_rest_correlations(frame)["flat"] is None


# ── Dimensionality ─────────────────────────────────────────────────────────────

def test_eigenvalues_sum_to_the_number_of_variables(correlated):
    """The trace of a correlation matrix is k, so its eigenvalues sum to k."""
    result = pca_dimensionality(correlated, level="test")
    assert sum(result.eigenvalues) == pytest.approx(result.k)


def test_independent_variables_give_eigenvalues_near_one(independent):
    result = pca_dimensionality(independent, level="test")
    assert result.eigenvalues[0] < 1.9
    assert result.n_kaiser <= 3


def test_perfectly_correlated_variables_collapse_to_one_component(rng):
    column = rng.normal(size=50)
    frame = pd.DataFrame({f"v{i}": column * (i + 1) for i in range(4)})
    result = pca_dimensionality(frame, level="test")
    assert result.eigenvalues[0] == pytest.approx(4.0, abs=1e-8)
    assert result.explained[0] == pytest.approx(1.0, abs=1e-8)
    assert result.n_kaiser == 1


def test_explained_shares_are_ordered_and_sum_to_one(correlated):
    result = pca_dimensionality(correlated, level="test")
    assert result.explained == sorted(result.explained, reverse=True)
    assert sum(result.explained) == pytest.approx(1.0)
    assert result.cumulative[-1] == pytest.approx(1.0)


def test_dimensionality_carries_its_level(correlated):
    """
    The label is load-bearing. Two eigenvalue reports in this repository read as
    contradictory only because neither said which level it described.
    """
    result = pca_dimensionality(correlated, level="7 pillar scores")
    assert result.level == "7 pillar scores"
    assert "7 pillar scores" in result.summary()


# ── Factorability ──────────────────────────────────────────────────────────────

def test_kmo_is_bounded(correlated):
    overall, per_variable = kmo(correlated)
    assert 0.0 <= overall <= 1.0
    assert all(0.0 <= v <= 1.0 for v in per_variable.values())


def test_kmo_is_higher_for_factorable_data(correlated, independent):
    assert kmo(correlated)[0] > kmo(independent)[0]


def test_bartlett_chi2_is_larger_when_variables_are_correlated(correlated, independent):
    chi2_correlated, df = bartlett_sphericity(correlated)
    chi2_independent, _ = bartlett_sphericity(independent)
    assert chi2_correlated > chi2_independent
    assert df == 6 * 5 // 2


def test_bartlett_returns_none_for_a_singular_matrix(rng):
    """Perfectly collinear variables make log-determinant undefined."""
    column = rng.normal(size=30)
    frame = pd.DataFrame({"a": column, "b": column, "c": column})
    chi2, _ = bartlett_sphericity(frame)
    assert chi2 is None


# ── Third-party cross-checks ───────────────────────────────────────────────────

def test_alpha_agrees_with_pingouin(correlated):
    pingouin = pytest.importorskip("pingouin", reason="pip install -r requirements-dev.txt")
    theirs, _ = pingouin.cronbach_alpha(data=correlated)
    assert cronbach_alpha(correlated).alpha == pytest.approx(theirs, abs=1e-9)


def test_alpha_agrees_with_pingouin_on_the_hand_case():
    """Ours, theirs, and the paper computation must all be the same number."""
    pingouin = pytest.importorskip("pingouin", reason="pip install -r requirements-dev.txt")
    theirs, _ = pingouin.cronbach_alpha(data=HAND_FRAME)
    assert theirs == pytest.approx(HAND_ALPHA, abs=1e-9)
    assert cronbach_alpha(HAND_FRAME).alpha == pytest.approx(theirs, abs=1e-9)


def test_kmo_agrees_with_factor_analyzer(correlated):
    fa = pytest.importorskip("factor_analyzer", reason="pip install -r requirements-dev.txt")
    _, their_overall = fa.calculate_kmo(correlated)
    ours, _ = kmo(correlated)
    assert ours == pytest.approx(their_overall, abs=1e-8)


def test_per_variable_kmo_agrees_with_factor_analyzer(correlated):
    fa = pytest.importorskip("factor_analyzer", reason="pip install -r requirements-dev.txt")
    their_per_variable, _ = fa.calculate_kmo(correlated)
    ours = kmo(correlated)[1]
    for theirs, (_, mine) in zip(their_per_variable, ours.items()):
        assert mine == pytest.approx(theirs, abs=1e-8)


def test_bartlett_agrees_with_factor_analyzer(correlated):
    fa = pytest.importorskip("factor_analyzer", reason="pip install -r requirements-dev.txt")
    their_chi2, _ = fa.calculate_bartlett_sphericity(correlated)
    ours, _ = bartlett_sphericity(correlated)
    assert ours == pytest.approx(their_chi2, abs=1e-6)


def test_eigenvalues_agree_with_sklearn(correlated):
    """
    Our SVD route against sklearn's PCA on the same standardised data. The
    pipeline's own weighting uses `np.linalg.eigh`, so agreeing with a third
    route is worth more here than agreeing with the pipeline's.
    """
    decomposition = pytest.importorskip("sklearn.decomposition")
    values = correlated.to_numpy(dtype=float)
    standardised = (values - values.mean(axis=0)) / values.std(axis=0, ddof=1)

    model = decomposition.PCA().fit(standardised)
    ours = pca_dimensionality(correlated, level="test")

    assert ours.eigenvalues == pytest.approx(list(model.explained_variance_), abs=1e-8)
    assert ours.explained == pytest.approx(list(model.explained_variance_ratio_), abs=1e-10)


# ── Varimax rotation ───────────────────────────────────────────────────────────

def test_varimax_preserves_communalities(correlated):
    """
    Rotation is orthogonal, so each variable's total explained variance — the sum
    of its squared loadings — must be unchanged. This is the property that makes
    rotation a change of axes rather than a change of model.
    """
    decomposition = pytest.importorskip("sklearn.decomposition")
    from verify.stats import varimax

    values = correlated.to_numpy(dtype=float)
    standardised = (values - values.mean(axis=0)) / values.std(axis=0, ddof=1)
    loadings = decomposition.FactorAnalysis(n_components=2,
                                            random_state=0).fit(standardised).components_.T

    before = (loadings ** 2).sum(axis=1)
    after = (varimax(loadings) ** 2).sum(axis=1)
    assert after == pytest.approx(before, abs=1e-8)


def test_varimax_increases_loading_simplicity(correlated):
    """The objective it maximises: variance of squared loadings within factors."""
    decomposition = pytest.importorskip("sklearn.decomposition")
    from verify.stats import varimax

    values = correlated.to_numpy(dtype=float)
    standardised = (values - values.mean(axis=0)) / values.std(axis=0, ddof=1)
    loadings = decomposition.FactorAnalysis(n_components=3,
                                            random_state=0).fit(standardised).components_.T

    def simplicity(m):
        return float(((m ** 2) ** 2).sum() - ((m ** 2).sum(axis=0) ** 2 / m.shape[0]).sum())

    assert simplicity(varimax(loadings)) >= simplicity(loadings) - 1e-9


def test_varimax_is_a_noop_for_a_single_factor(correlated):
    from verify.stats import varimax
    single = np.array([[0.8], [0.6], [0.4]])
    assert varimax(single) == pytest.approx(single)


def test_varimax_agrees_with_factor_analyzer(correlated):
    """
    Our rotation against the reference implementation, to machine precision.

    Both must be run to convergence for the comparison to mean anything.
    `factor_analyzer`'s default `tol=1e-5` stops while the loadings are still
    ~5e-3 from the fixed point — enough to look like an algorithmic disagreement
    when it is only an unconverged one, and enough to move a borderline factor
    assignment. Driven to `tol=1e-12`, the two agree to ~1e-15.
    """
    fa = pytest.importorskip("factor_analyzer", reason="pip install -r requirements-dev.txt")
    decomposition = pytest.importorskip("sklearn.decomposition")
    from verify.stats import varimax

    values = correlated.to_numpy(dtype=float)
    standardised = (values - values.mean(axis=0)) / values.std(axis=0, ddof=1)
    loadings = decomposition.FactorAnalysis(n_components=2,
                                            random_state=0).fit(standardised).components_.T

    theirs = fa.Rotator(method="varimax", normalize=True,
                        tol=1e-12, max_iter=5000).fit_transform(loadings)
    ours = varimax(loadings, normalize=True, tol=1e-12, max_iter=5000)

    # Factor axes are sign- and order-arbitrary; compare the loading magnitudes
    # each variable ends up with, which is what the assignment step reads.
    assert np.sort(np.abs(ours), axis=1) == pytest.approx(
        np.sort(np.abs(theirs), axis=1), abs=1e-10)


def test_varimax_kaiser_normalisation_changes_the_answer(correlated):
    """
    Normalised and unnormalised varimax are different rotations, not variants of
    one. Both are called "varimax" in the literature; SPSS, R and
    `factor_analyzer` all default to normalised, so this module does too. The
    test exists so the default cannot be flipped without something failing.
    """
    decomposition = pytest.importorskip("sklearn.decomposition")
    from verify.stats import varimax

    values = correlated.to_numpy(dtype=float)
    standardised = (values - values.mean(axis=0)) / values.std(axis=0, ddof=1)
    loadings = decomposition.FactorAnalysis(n_components=3,
                                            random_state=0).fit(standardised).components_.T

    difference = np.abs(varimax(loadings, normalize=True)
                        - varimax(loadings, normalize=False)).max()
    assert difference > 1e-4


# ── Structure agreement ────────────────────────────────────────────────────────

@pytest.fixture
def two_block(rng):
    """Twelve variables built from two independent latent factors, six each."""
    a, b = rng.normal(size=120), rng.normal(size=120)
    data = {}
    for i in range(6):
        data[f"a{i}"] = a * 1.0 + rng.normal(scale=0.35, size=120)
        data[f"b{i}"] = b * 1.0 + rng.normal(scale=0.35, size=120)
    return pd.DataFrame(data)


def test_structure_agreement_recovers_a_true_grouping(two_block):
    """When the declared groups are the real factors, agreement must be high."""
    from verify.stats import structure_agreement

    declared = {"A": [f"a{i}" for i in range(6)], "B": [f"b{i}" for i in range(6)]}
    result = structure_agreement(two_block, declared, n_factors=2)

    assert result.agreement > 0.9
    assert all(share == pytest.approx(1.0) for share in result.cohesion.values())


def test_structure_agreement_rejects_a_scrambled_grouping(two_block):
    """A grouping that cuts across the real factors must score near zero."""
    from verify.stats import structure_agreement

    scrambled = {
        "X": ["a0", "a1", "a2", "b0", "b1", "b2"],
        "Y": ["a3", "a4", "a5", "b3", "b4", "b5"],
    }
    result = structure_agreement(two_block, scrambled, n_factors=2)
    assert result.agreement < 0.2


def test_structure_agreement_is_chance_corrected(two_block):
    """
    Adjusted Rand, not raw Rand: an arbitrary partition scores ~0, not ~0.5.
    Without the correction a meaningless grouping looks like partial agreement.
    """
    from verify.stats import structure_agreement

    scrambled = {
        "X": ["a0", "b1", "a2", "b3", "a4", "b5"],
        "Y": ["b0", "a1", "b2", "a3", "b4", "a5"],
    }
    assert abs(structure_agreement(two_block, scrambled, n_factors=2).agreement) < 0.25


def test_structure_agreement_reports_cross_listed_variables(two_block):
    """A variable declared in two groups is assigned once, and named."""
    from verify.stats import structure_agreement

    declared = {
        "A": [f"a{i}" for i in range(6)],
        "B": [f"b{i}" for i in range(6)] + ["a0"],
    }
    result = structure_agreement(two_block, declared, n_factors=2)
    assert "a0" in result.cross_listed
    assert result.declared["a0"] == "A"          # first declaration wins


def test_structure_agreement_carries_its_sample_size(two_block):
    from verify.stats import structure_agreement
    declared = {"A": [f"a{i}" for i in range(6)], "B": [f"b{i}" for i in range(6)]}
    result = structure_agreement(two_block, declared, n_factors=2)
    assert result.n == 120 and result.n_factors == 2
    assert result.kmo is not None


def test_structure_agreement_survives_too_little_data():
    from verify.stats import structure_agreement
    frame = pd.DataFrame({"a": [1.0, 2.0], "b": [2.0, 1.0]})
    result = structure_agreement(frame, {"G": ["a", "b"]})
    assert result.note and np.isnan(result.agreement)


# ── Sample adequacy: the gate that stops an unsupportable answer ───────────────

def test_adequate_data_is_reportable(two_block):
    """120 observations across 12 variables is 10 per variable, and full rank."""
    from verify.stats import structure_agreement

    declared = {"A": [f"a{i}" for i in range(6)], "B": [f"b{i}" for i in range(6)]}
    result = structure_agreement(two_block, declared, n_factors=2)

    assert result.reportable
    assert result.inadequacy == ""
    assert result.obs_per_variable == pytest.approx(10.0)
    assert not result.singular


def test_too_few_observations_per_variable_is_not_reportable(two_block):
    """
    The live case. At the 2023 reference year the panel offers 31 complete
    countries across 32 indicators — under one observation per variable. A factor
    routine returns a full solution on that, with loadings and an adjusted Rand
    index that reads exactly like a finding.
    """
    from verify.stats import MIN_OBS_PER_VARIABLE, structure_agreement

    declared = {"A": [f"a{i}" for i in range(6)], "B": [f"b{i}" for i in range(6)]}
    thin = two_block.head(20)                      # 20 rows, 12 variables
    result = structure_agreement(thin, declared, n_factors=2)

    assert result.obs_per_variable < MIN_OBS_PER_VARIABLE
    assert not result.reportable
    assert "per variable" in result.inadequacy
    # The number is still computed and carried, so the caller can disclose what
    # it would have been rather than leaving a reader to wonder.
    assert not np.isnan(result.agreement)


def test_singular_correlation_matrix_is_not_reportable(rng):
    """Fewer observations than variables cannot give a full-rank matrix."""
    from verify.stats import structure_agreement

    frame = pd.DataFrame({f"v{i}": rng.normal(size=6) for i in range(10)})
    declared = {"A": [f"v{i}" for i in range(5)], "B": [f"v{i}" for i in range(5, 10)]}
    result = structure_agreement(frame, declared, n_factors=2)

    assert result.singular
    assert not result.reportable
    assert "singular" in result.inadequacy


def test_reportability_is_independent_of_agreement(two_block):
    """
    A wrong grouping on good data is reportable and scores badly; a right
    grouping on bad data is not reportable at all. The gate answers "can this
    question be asked here", never "do we like the answer".
    """
    from verify.stats import structure_agreement

    scrambled = {
        "X": ["a0", "a1", "a2", "b0", "b1", "b2"],
        "Y": ["a3", "a4", "a5", "b3", "b4", "b5"],
    }
    bad_grouping_good_data = structure_agreement(two_block, scrambled, n_factors=2)
    assert bad_grouping_good_data.reportable
    assert bad_grouping_good_data.agreement < 0.2

    correct = {"A": [f"a{i}" for i in range(6)], "B": [f"b{i}" for i in range(6)]}
    good_grouping_bad_data = structure_agreement(two_block.head(20), correct, n_factors=2)
    assert not good_grouping_bad_data.reportable
