"""
The inference functions in verify/stats.py, checked on worked problems whose answers were computed by hand.

The problems are the calculation-practice questions of the owner's Advanced Design and Analysis midterm (questions
2, 3 and 7 to 12), worked with the course's formula sheet and its t and Fisher r-to-z tables. Each expected value
below is that hand computation, written in as a literal: the only kind of check that catches an error shared by
every implementation of a formula. Tolerances match table precision.
"""

import numpy as np
import pandas as pd
import pytest

from verify.stats import (
    compare_correlations,
    disattenuated_r,
    mean_interval,
    parallel_analysis,
    partial_r,
    r_interval,
    r_significance,
    rank_bands,
    semipartial_r,
)


# ── Is r significant? ──────────────────────────────────────────────────────────

def test_question_7_r_of_028_with_52_people_is_significant():
    """t = .28 * sqrt(50 / (1 - .0784)) = .28 * 7.3657 = 2.0624 on 50 df; the table's critical t is 2.009."""
    t, p = r_significance(0.28, 52)
    assert t == pytest.approx(2.0624, abs=1e-3)
    assert t > 2.009 and p < 0.05


def test_the_same_r_needs_enough_people():
    """The midterm's lesson: r = .50 gives t = .5 * sqrt(12 / .75) = 2.000 at n = 14 (critical 2.179, not
    significant) and t = .5 * sqrt(18 / .75) = 2.4495 at n = 20 (critical 2.101, significant)."""
    t14, p14 = r_significance(0.50, 14)
    t20, p20 = r_significance(0.50, 20)
    assert t14 == pytest.approx(2.0, abs=1e-9) and p14 > 0.05
    assert t20 == pytest.approx(2.4495, abs=1e-4) and p20 < 0.05


# ── Confidence intervals for r ─────────────────────────────────────────────────

def test_question_8_r_of_034_in_123_adults():
    """t = .34 * sqrt(121 / .8844) = 3.9769. z' = .3541, SE = 1 / sqrt(120) = .0913,
    z' +/- 1.96 * SE = [.1752, .5330], back to r: [.1734, .4877]."""
    t, p = r_significance(0.34, 123)
    assert t == pytest.approx(3.9769, abs=1e-3) and p < 0.001
    assert r_interval(0.34, 123) == pytest.approx((0.1734, 0.4877), abs=1e-3)


def test_question_9_r_of_060_with_40_people():
    """z' = .6931, SE = 1 / sqrt(37) = .1644, z' +/- .3222 = [.3709, 1.0153], back to r: [.3548, .7680].
    Asymmetric around .60, as an interval built on z' must be."""
    low, high = r_interval(0.60, 40)
    assert (low, high) == pytest.approx((0.3548, 0.7680), abs=1e-3)
    assert 0.60 - low > high - 0.60


def test_an_interval_needs_more_than_three_cases():
    assert all(np.isnan(r_interval(0.5, 3)))


# ── Two correlations ───────────────────────────────────────────────────────────

def test_question_10_self_control_and_grades_differ_between_samples():
    """z'1 = .4847 (r = .45, n = 120), z'2 = .2132 (r = .21, n = 103),
    SE = sqrt(1/117 + 1/100) = .1362, Z = .2715 / .1362 = 1.994: just past 1.96."""
    z = compare_correlations(0.45, 120, 0.21, 103)
    assert z == pytest.approx(1.994, abs=1e-3)
    assert z > 1.96


# ── Attenuation ────────────────────────────────────────────────────────────────

def test_question_11_correcting_for_attenuation():
    """.42 / sqrt(.81 * .64) = .42 / .72 = .5833."""
    assert disattenuated_r(0.42, 0.81, 0.64) == pytest.approx(0.5833, abs=1e-4)


# ── Third variables ────────────────────────────────────────────────────────────

def test_question_12_partial_and_semipartial():
    """Effort and score r = .20; anxiety correlates .80 with effort and -.40 with score.
    Numerator .20 - (.80)(-.40) = .52. Partial: .52 / sqrt(.36 * .84) = .52 / .5499 = .9456.
    Semi-partial, anxiety removed from effort only: .52 / sqrt(.36) = .8667. Anxiety was suppressing the
    relationship: held constant, it rises from .20 to .95."""
    assert partial_r(0.20, 0.80, -0.40) == pytest.approx(0.9456, abs=1e-4)
    assert semipartial_r(0.20, 0.80, -0.40) == pytest.approx(0.8667, abs=1e-4)


def test_a_third_variable_unrelated_to_both_changes_nothing():
    """The class question: if Z correlates with neither X nor Y, the partial r is the bivariate r."""
    assert partial_r(0.30, 0.0, 0.0) == pytest.approx(0.30, abs=1e-12)


def test_a_spurious_correlation_vanishes():
    """When Z fully explains both (r_xy = r_xz * r_yz), nothing is left once Z is held constant."""
    assert partial_r(0.8 * 0.7, 0.8, 0.7) == pytest.approx(0.0, abs=1e-12)


# ── Confidence intervals for a mean ────────────────────────────────────────────

def test_question_2_known_sigma_uses_z():
    """M = 74, sigma = 10, n = 25: SE = 2. 95%: 74 +/- 1.96 * 2 = [70.08, 77.92].
    99%: 74 +/- 2.576 * 2 = [68.85, 79.15], wider at the higher confidence level."""
    assert mean_interval(74, 10, 25, known_sd=True) == pytest.approx((2.0, 70.08, 77.92), abs=1e-2)
    assert mean_interval(74, 10, 25, known_sd=True, confidence=0.99) == pytest.approx((2.0, 68.85, 79.15), abs=1e-2)


def test_question_3_estimated_sd_uses_t():
    """M = 74, SD = 8, n = 25, sigma unknown: SE = 1.6, t(24) = 2.064, 74 +/- 3.302 = [70.698, 77.302]."""
    assert mean_interval(74, 8, 25) == pytest.approx((1.6, 70.698, 77.302), abs=1e-3)


# ── Rank bands ─────────────────────────────────────────────────────────────────

def test_precise_scores_give_exact_ranks():
    """80, 70 and 40 with SE 2: the closest pair differs by 10 / sqrt(8) = 3.54 > 1.96, so every rank is certain."""
    bands = rank_bands(pd.Series({"a": 80.0, "b": 70.0, "c": 40.0}), pd.Series({"a": 2.0, "b": 2.0, "c": 2.0}))
    assert bands[["best", "worst"]].to_dict("index") == {"a": {"best": 1, "worst": 1}, "b": {"best": 2, "worst": 2},
                                                         "c": {"best": 3, "worst": 3}}


def test_overlapping_scores_share_a_band():
    """With SE 5, 80 and 70 differ by 10 / sqrt(50) = 1.41 < 1.96: either could be first. 40 is 30 / 7.07 = 4.24
    below both, so it is third whatever happens."""
    bands = rank_bands(pd.Series({"a": 80.0, "b": 70.0, "c": 40.0}), pd.Series({"a": 5.0, "b": 5.0, "c": 5.0}))
    assert bands[["best", "worst"]].to_dict("index") == {"a": {"best": 1, "worst": 2}, "b": {"best": 1, "worst": 2},
                                                         "c": {"best": 3, "worst": 3}}


# ── How many factors? ──────────────────────────────────────────────────────────

def test_parallel_analysis_thresholds_fall_and_straddle_one():
    """Random data's eigenvalues sum to k and fall in order, so the first sits above 1 and the last below."""
    thresholds = parallel_analysis(54, 7, draws=500)
    assert (np.diff(thresholds) < 0).all()
    assert thresholds[0] > 1 > thresholds[-1]


def test_a_real_factor_beats_parallel_analysis():
    rng = np.random.default_rng(7)
    latent = rng.normal(size=200)
    data = np.column_stack([latent + rng.normal(scale=0.6, size=200) for _ in range(5)])
    observed = np.linalg.eigvalsh(np.corrcoef(data, rowvar=False))[::-1]
    thresholds = parallel_analysis(200, 5, draws=300)
    assert observed[0] > thresholds[0] and observed[1] < thresholds[1]
