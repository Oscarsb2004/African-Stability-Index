"""
The scoring arithmetic, under test for the first time.

Until now no test imported `asi.pipeline.score`. The only thing standing behind
these functions was `verify/panel.py`, which re-derives against real data — so
every branch that real data never takes was unexercised. The NaN-renormalisation
path in `weighted_composite` has never fired on the panel: every country-year
that reaches a composite has all seven pillars present. It will fire the first
time an indicator is added mid-panel or a country is admitted with a gap, and
the difference between renormalising and not renormalising is silent.

Each test below states the rule the docstring claims, then checks the function
obeys it — including the cases where an easier-looking implementation would give
a plausible but wrong answer.
"""

import numpy as np
import pandas as pd
import pytest

from asi.core.constants import SMALL
from asi.core.schema import Reliability
from asi.pipeline.score import (
    composite_reliability,
    fit_entropy_weights,
    fit_pca_weights,
    geometric_composite,
    weighted_composite,
)


def _wide(**cols) -> pd.DataFrame:
    """A pillar-wide frame indexed the way 02_panel.py builds it."""
    n = len(next(iter(cols.values())))
    idx = pd.MultiIndex.from_tuples([("KEN", 2000 + i) for i in range(n)],
                                    names=["iso3", "year"])
    return pd.DataFrame(cols, index=idx)


# ── weighted_composite ─────────────────────────────────────────────────────────

def test_weights_renormalise_over_the_pillars_present():
    """
    The path real data has never taken.

    With C missing, A and B must be rescaled to sum to 1 (0.5/0.75 and 0.25/0.75),
    giving 80(2/3) + 40(1/3) = 66.67. An implementation that merely skipped the
    NaN and applied the raw weights would return 50 — a plausible number, and
    wrong by sixteen points.
    """
    wide = _wide(A=[80.0], B=[40.0], C=[np.nan])
    out = weighted_composite(wide, {"A": 0.5, "B": 0.25, "C": 0.25})
    assert out.iloc[0] == pytest.approx(80 * 2 / 3 + 40 * 1 / 3)
    assert out.iloc[0] != pytest.approx(50.0)


def test_a_row_with_no_pillars_at_all_is_nan_not_zero():
    """Nothing measured is not the same claim as measured zero."""
    wide = _wide(A=[np.nan], B=[np.nan])
    out = weighted_composite(wide, {"A": 0.5, "B": 0.5})
    assert np.isnan(out.iloc[0])


def test_weights_naming_an_absent_pillar_are_ignored():
    """A weight preset may name pillars this panel does not carry."""
    wide = _wide(A=[60.0], B=[20.0])
    out = weighted_composite(wide, {"A": 0.5, "B": 0.5, "Z": 99.0})
    assert out.iloc[0] == pytest.approx(40.0)


def test_equal_weights_reduce_to_the_arithmetic_mean():
    wide = _wide(A=[10.0], B=[20.0], C=[60.0])
    out = weighted_composite(wide, {"A": 1 / 3, "B": 1 / 3, "C": 1 / 3})
    assert out.iloc[0] == pytest.approx(30.0)


# ── geometric_composite ────────────────────────────────────────────────────────

def test_geometric_floors_at_small_rather_than_returning_zero():
    """
    ln(0) is undefined, so a pillar at zero is floored at SMALL.

    The floored result is tiny but finite: sqrt(1e-8 x 100) = 1e-3. What must not
    happen is a NaN or a hard zero, either of which would look like missing data
    rather than the collapse it represents.
    """
    wide = _wide(A=[0.0], B=[100.0])
    out = geometric_composite(wide, ["A", "B"], SMALL)
    assert np.isfinite(out.iloc[0])
    assert out.iloc[0] == pytest.approx(np.sqrt(SMALL * 100))
    assert out.iloc[0] > 0


def test_geometric_is_non_compensatory():
    """
    The reason this method exists: a collapsed pillar cannot be bought back by a
    strong one. Equal arithmetic means, wildly different geometric means.
    """
    balanced = geometric_composite(_wide(A=[50.0], B=[50.0]), ["A", "B"], SMALL)
    lopsided = geometric_composite(_wide(A=[5.0], B=[95.0]), ["A", "B"], SMALL)
    assert balanced.iloc[0] == pytest.approx(50.0)
    assert lopsided.iloc[0] < balanced.iloc[0]
    assert lopsided.iloc[0] == pytest.approx(np.sqrt(5 * 95))


def test_geometric_ignores_missing_pillars_rather_than_flooring_them():
    """
    A missing pillar is dropped from the mean. Treating it as SMALL instead would
    drive the composite to near-zero for any country with one gap — punishing
    absent data as though it were measured collapse.
    """
    out = geometric_composite(_wide(A=[50.0], B=[50.0], C=[np.nan]),
                              ["A", "B", "C"], SMALL)
    assert out.iloc[0] == pytest.approx(50.0)


def test_geometric_all_missing_is_nan():
    out = geometric_composite(_wide(A=[np.nan], B=[np.nan]), ["A", "B"], SMALL)
    assert np.isnan(out.iloc[0])


# ── fit_pca_weights ────────────────────────────────────────────────────────────

def test_pca_zeroes_a_negative_loading_rather_than_absolute_valuing_it():
    """
    A pillar loading against the stability dimension is excluded, not flipped.

    C here moves opposite to A and B. Taking |loading| would give C a positive
    weight, silently inverting its contribution — a country would gain composite
    points for scoring badly on it. The documented rule is exclusion.
    """
    rng = np.random.default_rng(0)
    base = rng.normal(size=40)
    wide = _wide(A=list(base + rng.normal(scale=0.1, size=40)),
                 B=list(base + rng.normal(scale=0.1, size=40)),
                 C=list(-base + rng.normal(scale=0.1, size=40)))
    w = fit_pca_weights(wide, ["A", "B", "C"], SMALL)
    assert w["C"] == 0.0
    assert w["A"] > 0 and w["B"] > 0
    assert sum(w.values()) == pytest.approx(1.0)


def test_pca_falls_back_to_equal_weights_when_too_few_complete_rows():
    """Fewer complete rows than pillars makes a correlation matrix meaningless."""
    wide = _wide(A=[1.0, 2.0], B=[1.0, 3.0], C=[np.nan, np.nan])
    w = fit_pca_weights(wide, ["A", "B", "C"], SMALL)
    assert w == pytest.approx({"A": 1 / 3, "B": 1 / 3, "C": 1 / 3})


def test_pca_weights_sum_to_one_on_a_positively_correlated_panel():
    rng = np.random.default_rng(1)
    base = rng.normal(size=40)
    wide = _wide(**{p: list(base + rng.normal(scale=0.3, size=40))
                    for p in ("A", "B", "C")})
    w = fit_pca_weights(wide, ["A", "B", "C"], SMALL)
    assert sum(w.values()) == pytest.approx(1.0)
    assert all(v >= 0 for v in w.values())


# ── fit_entropy_weights ────────────────────────────────────────────────────────

def test_entropy_gives_a_pillar_that_separates_nobody_almost_no_weight():
    """
    The premise of entropy weighting: a column with no spread carries no
    information about how countries differ, so it earns ~0 weight.
    """
    rng = np.random.default_rng(2)
    wide = _wide(A=list(rng.uniform(10, 90, size=40)),
                 B=list(rng.uniform(10, 90, size=40)),
                 C=[50.0] * 40)                     # degenerate: identical everywhere
    w = fit_entropy_weights(wide, ["A", "B", "C"], SMALL)
    assert w["C"] < 0.01
    assert w["A"] > w["C"] and w["B"] > w["C"]
    assert sum(w.values()) == pytest.approx(1.0)


def test_entropy_shifts_non_positive_columns_before_taking_logs():
    """
    Pillar scores are 0-100, but the function guards against a column whose
    minimum is <= 0 by shifting it. Without the shift, ln of a negative share is
    undefined and the weights come back NaN.
    """
    rng = np.random.default_rng(3)
    wide = _wide(A=list(rng.uniform(-50, 50, size=30)),
                 B=list(rng.uniform(10, 90, size=30)))
    w = fit_entropy_weights(wide, ["A", "B"], SMALL)
    assert all(np.isfinite(v) for v in w.values())
    assert sum(w.values()) == pytest.approx(1.0)


def test_entropy_on_an_empty_panel_falls_back_to_equal_weights():
    wide = pd.DataFrame({"A": [], "B": []})
    w = fit_entropy_weights(wide, ["A", "B"], SMALL)
    assert w == {"A": pytest.approx(0.5), "B": pytest.approx(0.5)}


# ── composite_reliability ──────────────────────────────────────────────────────

def _tiers(*values) -> pd.DataFrame:
    return pd.DataFrame({"reliability": list(values)})


def test_composite_is_unreliable_below_the_pillar_floor():
    got = composite_reliability(_tiers("reliable", "unreliable", "absent"),
                                min_pillars=2)
    assert got is Reliability.UNRELIABLE


def test_composite_is_reliable_only_when_every_displayable_pillar_is():
    assert composite_reliability(_tiers("reliable", "reliable"),
                                 min_pillars=2) is Reliability.RELIABLE


def test_one_thin_pillar_makes_the_whole_composite_thin():
    """Reliability does not average — the weakest displayable pillar sets it."""
    assert composite_reliability(_tiers("reliable", "reliable", "thin"),
                                 min_pillars=2) is Reliability.THIN


def test_unreliable_pillars_do_not_count_toward_the_floor():
    """
    Six unreliable pillars and one reliable one is one usable pillar, not seven.
    """
    got = composite_reliability(_tiers("reliable", *["unreliable"] * 6),
                                min_pillars=2)
    assert got is Reliability.UNRELIABLE
