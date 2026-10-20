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


# ── Edition 2, step 7: unreliable pillars leave the composite ──────────────────

def _pillars(rows):
    return pd.DataFrame(rows, columns=["iso3", "year", "pillar_id", "score", "reliability"])


def test_an_unreliable_pillar_is_left_out_and_a_thin_one_kept():
    from asi.pipeline.score import composite_inputs
    pil = _pillars([("KEN", 2024, "GOV", 60.0, "reliable"), ("KEN", 2024, "ENV", 10.0, "unreliable"),
                    ("KEN", 2024, "SEC", 40.0, "thin")])
    wide = composite_inputs(pil)
    assert np.isnan(wide.loc[("KEN", 2024), "ENV"])
    assert wide.loc[("KEN", 2024), "SEC"] == 40.0  # negative control: thin still counts
    assert weighted_composite(wide, {"GOV": 1 / 3, "ENV": 1 / 3, "SEC": 1 / 3}).iloc[0] == pytest.approx(50.0)


def test_the_lack_of_reliability_index_follows_its_formula():
    from asi.pipeline.score import lack_of_reliability
    panel = pd.DataFrame({
        "iso3": ["KEN"] * 4, "year": [2024] * 4, "variable_name": ["a", "b", "c", "d"],
        "raw_value": [1.0, 2.0, 3.0, np.nan],
        "provenance": ["observed", "carried_forward", "carried_forward", "absent"],
        "source_year": [2024, 2022, 2021, None]})
    # gap = 3 of 4 not measured; age = mean(0, 2, 3) / 5 = 1/3; LRI = 10 x (0.75 + 1/3) / 2
    assert lack_of_reliability(panel, ["a", "b", "c", "d"], 5).loc[("KEN", 2024)] == pytest.approx(10 * (0.75 + 1 / 3) / 2)
    fresh = panel.assign(provenance="observed", source_year=2024, raw_value=1.0)
    assert lack_of_reliability(fresh, ["a", "b", "c", "d"], 5).loc[("KEN", 2024)] == 0.0  # negative control


# ── Edition 2, step 8: the headline's interval, bands, tiers and effective weights ──

def test_the_interval_follows_its_formula_and_one_pillar_has_none():
    from scipy.stats import t
    from asi.pipeline.score import composite_interval
    wide = _wide(GOV=[50.0, 40.0], SEC=[60.0, np.nan], VOI=[70.0, np.nan])
    got = composite_interval(wide, 0.95)
    se = 10 / np.sqrt(3)  # SD 10 over three pillars
    assert got.iloc[0]["se"] == pytest.approx(se)
    assert got.iloc[0]["high"] - got.iloc[0]["mean"] == pytest.approx(t.ppf(0.975, 2) * se)
    assert np.isnan(got.iloc[1]["low"])  # negative control: one pillar, no spread, no interval


def test_a_band_counts_only_the_significant_states_above_and_below():
    from asi.pipeline.score import rank_bands
    scores, errors = pd.Series({"A": 90.0, "B": 50.0, "C": 51.0}), pd.Series({"A": 1.0, "B": 1.0, "C": 1.0})
    bands = rank_bands(scores, errors, 1.96)
    assert bands.loc["A"].tolist() == [1, 1]
    assert bands.loc["C"].tolist() == [2, 3] and bands.loc["B"].tolist() == [2, 3]  # 1 point apart: no difference


def test_tiers_follow_the_leader_rule_where_overlapping_bands_would_chain():
    from asi.pipeline.score import rank_bands, tiers
    # A-B and B-C are 3 points apart (z 1.77), A-C 6 (z 3.54): every band overlaps the next, so the overlap rule
    # makes one tier; the leader rule opens a second at C, the first state significantly below A (P96)
    scores, errors = pd.Series({"A": 100.0, "B": 97.0, "C": 94.0}), pd.Series(1.2, index=["A", "B", "C"])
    bands = rank_bands(scores, errors, 1.96)
    assert bands["band_best"].tolist() == [1, 1, 2] and bands["band_worst"].tolist() == [2, 3, 3]
    assert tiers(scores, errors, 1.96).tolist() == [1, 1, 2]
    assert tiers(scores, errors * 10, 1.96).tolist() == [1, 1, 1]  # negative control: wide errors, one tier


def test_effective_weights_nominal_cross_listed_and_as_used():
    from asi.pipeline.score import effective_weights
    nominal = effective_weights({"GOV": ["x", "y"], "SEC": ["z"], "ENV": []})
    assert nominal.to_dict() == pytest.approx({"x": 0.25, "y": 0.25, "z": 0.5})  # an empty pillar weighs nothing
    assert effective_weights({"GOV": ["x", "y"], "SEC": ["x"]})["x"] == pytest.approx(0.75)  # cross-listed
    entered = pd.DataFrame({"iso3": ["KEN", "KEN", "TZA"], "pillar_id": ["GOV", "SEC", "GOV"],
                            "contributing": ["x", "z", "x,y"]})
    # KEN: two pillars, x alone in GOV; TZA: GOV only, both members
    assert effective_weights({}, entered).to_dict() == pytest.approx({"x": 0.5, "y": 0.25, "z": 0.25})


def test_the_verifier_catches_a_wrong_tier_and_a_wrong_interval(capsys):
    from verify import panel as V
    pil = _pillars([(s, 2024, p, v, "reliable") for s, vals in
                    {"A": (100, 101, 99), "B": (60, 61, 59), "C": (59, 60, 58)}.items()
                    for p, v in zip(("GOV", "SEC", "VOI"), vals)])
    comp = pd.DataFrame({"iso3": ["A", "B", "C"], "year": 2024, "method": "equal", "rank": [1, 2, 3],
                         "se": 1 / np.sqrt(3), "band_best": [1, 2, 2], "band_worst": [1, 3, 3], "tier": [1, 2, 2]})
    half = 4.302652729911275 / np.sqrt(3)  # t(2) at 97.5%
    comp["ci_low"] = [100 - half, 60 - half, 59 - half]
    comp["ci_high"] = [100 + half, 60 + half, 59 + half]
    comp[["se", "ci_low", "ci_high"]] = comp[["se", "ci_low", "ci_high"]].round(2)
    V.CHECKS.clear()
    V.check_headline_uncertainty(pil, comp)
    assert V.CHECKS[-1]["status"] == "PASS"
    V.check_headline_uncertainty(pil, comp.assign(tier=[1, 1, 2]))  # negative control: a wrong tier
    V.check_headline_uncertainty(pil, comp.assign(ci_high=comp["ci_high"] + 1))  # and a wrong interval
    assert [c["status"] for c in V.CHECKS[-2:]] == ["FAIL", "FAIL"]


# ── P101: overlapping indicators share a slot ──────────────────────────────────

def _cells(rows):
    return pd.DataFrame(rows, columns=["iso3", "year", "variable_name", "score", "provenance"])


def test_overlapping_indicators_share_one_slot_of_their_pillar():
    from asi.pipeline.score import pillar_scores
    cells = _cells([("KEN", 2024, "a", 90.0, "observed"), ("KEN", 2024, "b", 70.0, "observed"),
                    ("KEN", 2024, "c", 20.0, "observed")])
    kw = dict(reliable_at=0.6, thin_at=0.4, max_imputed_share=0.5)
    shared = pillar_scores(cells, {"P": ["a", "b", "c"]}, slots={"a": "P:a+b", "b": "P:a+b"}, **kw)
    assert shared["score"].iloc[0] == pytest.approx((80.0 + 20.0) / 2)       # (a, b) is one slot at 80, then c
    plain = pillar_scores(cells, {"P": ["a", "b", "c"]}, **kw)
    assert plain["score"].iloc[0] == pytest.approx(60.0)                      # negative control: three slots
    lone = pillar_scores(cells[cells["variable_name"] != "b"], {"P": ["a", "b", "c"]},
                         slots={"a": "P:a+b", "b": "P:a+b"}, **kw)
    assert lone["score"].iloc[0] == pytest.approx((90.0 + 20.0) / 2)         # a slot with one member present


def test_the_overlap_screen_clusters_pairs_beyond_the_control_and_chains_them():
    from asi.pipeline.score import overlap_screen
    rng = np.random.default_rng(7)
    gdp = rng.normal(size=60)
    shared = rng.normal(size=60)
    values = pd.DataFrame({"gdp": gdp, "a": gdp + shared, "b": gdp + shared + 0.3 * rng.normal(size=60),
                           "c": gdp + shared + 0.3 * rng.normal(size=60), "d": gdp + rng.normal(size=60)})
    slots, pairs = overlap_screen(values, {"P": ["gdp", "a", "b", "c", "d"]}, "gdp", 0.71, 20)
    assert set(slots) == {"a", "b", "c"} and len(set(slots.values())) == 1  # one cluster
    assert "d" not in slots and "gdp" not in slots   # negative control: d shares only GDP with the others
    assert len(pairs) == 6                           # every pair of the pillar but the control's is measured


def test_effective_weights_split_a_slot_among_its_members():
    from asi.pipeline.score import effective_weights
    w = effective_weights({"P": ["a", "b", "c"], "Q": ["d"]}, slots={"a": "P:a+b", "b": "P:a+b"})
    assert w.to_dict() == pytest.approx({"a": 0.125, "b": 0.125, "c": 0.25, "d": 0.5})
