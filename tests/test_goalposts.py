"""
The frozen-bounds module, under test for the first time.

`asi.pipeline.goalposts` decides what every normalised score is measured
against. Nothing imported it from a test until now, which meant the two rules it
exists to enforce — bounds round *outward*, and a version mismatch is an error
rather than a shrug — were held up by their docstrings alone.

The outward-rounding rule has a history. Rounding to nearest pushed the very
countries that defined an extreme a fraction outside their own goalpost and set
`clamped` on roughly 35 cells whose true deviation was under 5e-07. That would
have made the flag useless for the case it exists to catch: a genuinely new
extreme in a later edition.
"""

import numpy as np
import pandas as pd
import pytest
import yaml

from asi.pipeline import goalposts as gp


# ── _round_outward ─────────────────────────────────────────────────────────────

def test_a_minimum_rounds_down_and_a_maximum_rounds_up():
    assert gp._round_outward(1.23456749, up=False) == pytest.approx(1.234567)
    assert gp._round_outward(1.23456741, up=True) == pytest.approx(1.234568)


def test_the_value_that_defined_an_extreme_stays_inside_its_own_bound():
    """
    The regression the rule was written for. Round-to-nearest would move the
    bound *past* the defining value and mark it clamped.
    """
    for value in (0.0000004, 3.14159265, 99.9999996, -2.7182818):
        assert gp._round_outward(value, up=False) <= value
        assert gp._round_outward(value, up=True) >= value


def test_round_outward_returns_a_plain_float_for_yaml():
    """PyYAML cannot serialise numpy scalars, and these values are written out."""
    out = gp._round_outward(np.float64(1.5), up=True)
    assert type(out) is float


def test_non_finite_bounds_pass_through():
    assert np.isnan(gp._round_outward(float("nan"), up=True))
    assert np.isinf(gp._round_outward(float("inf"), up=False))


# ── apply_log ──────────────────────────────────────────────────────────────────

def test_log_transform_is_a_no_op_when_not_flagged():
    s = pd.Series([1.0, 10.0, 100.0])
    pd.testing.assert_series_equal(gp.apply_log(s, False), s)


def test_negatives_are_clipped_before_log1p():
    """log1p is undefined below -1; a flagged indicator's range is non-negative."""
    out = gp.apply_log(pd.Series([-5.0, 0.0, 9.0]), True)
    assert out.tolist() == pytest.approx([0.0, 0.0, np.log(10)])


def test_log_preserves_missingness():
    out = gp.apply_log(pd.Series([1.0, np.nan]), True)
    assert np.isnan(out.iloc[1])


# ── winsorize_bounds ───────────────────────────────────────────────────────────

def test_tukey_fences_sit_at_the_stated_multiple_of_the_iqr():
    s = pd.Series(range(1, 101), dtype=float)
    q1, q3 = np.quantile(s, [0.25, 0.75])
    lo, hi = gp.winsorize_bounds(s, 1.5)
    assert lo == pytest.approx(q1 - 1.5 * (q3 - q1))
    assert hi == pytest.approx(q3 + 1.5 * (q3 - q1))


def test_an_empty_series_yields_nan_bounds_not_an_exception():
    """`compute` guards on `np.isfinite(lo)`, so NaN is the contract here."""
    lo, hi = gp.winsorize_bounds(pd.Series([], dtype=float), 1.5)
    assert np.isnan(lo) and np.isnan(hi)


# ── compute ────────────────────────────────────────────────────────────────────

def _panel(values, provenance=None):
    return pd.DataFrame({
        "variable_name": ["gdp_pc"] * len(values),
        "raw_value": values,
        "provenance": provenance or ["observed"] * len(values),
    })


def test_compute_skips_non_scoring_indicators():
    out = gp.compute(_panel([1.0, 2.0]), {"gdp_pc": {"role": "context"}}, 1.5)
    assert out == {}


def test_goalposts_contain_every_value_they_were_derived_from():
    """The property the whole module exists for."""
    values = [0.137, 12.5, 88.812345, 99.9999991]
    out = gp.compute(_panel(values), {"gdp_pc": {}}, 1.5)["gdp_pc"]
    assert out["goalpost_min"] <= min(values)
    assert out["goalpost_max"] >= max(values)


def test_an_extreme_set_by_imputed_data_is_recorded_not_hidden():
    """
    A goalpost anchored on a regional-mean estimate is a manual-review item.
    Recording it is the difference between a known weakness and an unknown one.
    """
    out = gp.compute(
        _panel([1.0, 50.0, 100.0], ["regional_mean", "observed", "observed"]),
        {"gdp_pc": {}}, 1.5,
    )["gdp_pc"]
    assert out["min_from_imputed"] is True
    assert out["max_from_imputed"] is False


def test_compute_carries_the_spec_flags_through():
    out = gp.compute(_panel([1.0, 2.0, 3.0]),
                     {"gdp_pc": {"log_transform": True, "polarity": "negative"}},
                     1.5)["gdp_pc"]
    assert out["log_transform"] is True
    assert out["polarity"] == "negative"


# ── freeze / load ──────────────────────────────────────────────────────────────

def test_freeze_then_load_round_trips(tmp_path):
    path = tmp_path / "goalposts.yaml"
    gp.freeze({"gdp_pc": {"goalpost_min": 1.0, "goalpost_max": 9.0}},
              path, panel_years=(2000, 2024))
    assert gp.load(path) == {"gdp_pc": {"goalpost_min": 1.0, "goalpost_max": 9.0}}


def test_freeze_stamps_the_version_and_the_panel_it_came_from(tmp_path):
    path = tmp_path / "goalposts.yaml"
    gp.freeze({"gdp_pc": {}}, path, panel_years=(2000, 2024))
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert payload["version"] == gp.GOALPOSTS_VERSION
    assert payload["panel_years"] == [2000, 2024]
    assert "Regenerate deliberately" in payload["note"]


def test_a_version_mismatch_raises_rather_than_loading_stale_bounds(tmp_path):
    """
    Bounds from an older schema would normalise every score against the wrong
    range. Loading them quietly is the failure mode worth preventing: the numbers
    would look entirely ordinary.
    """
    path = tmp_path / "goalposts.yaml"
    path.write_text(yaml.safe_dump({
        "version": gp.GOALPOSTS_VERSION - 1,
        "indicators": {"gdp_pc": {"goalpost_min": 0.0, "goalpost_max": 1.0}},
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match"):
        gp.load(path)


def test_a_file_with_no_version_at_all_is_a_mismatch(tmp_path):
    path = tmp_path / "goalposts.yaml"
    path.write_text(yaml.safe_dump({"indicators": {}}), encoding="utf-8")
    with pytest.raises(ValueError):
        gp.load(path)


def test_a_missing_file_raises_rather_than_recomputing(tmp_path):
    """Silently recomputing would re-anchor every historical score."""
    with pytest.raises(FileNotFoundError, match="Generate them once"):
        gp.load(tmp_path / "absent.yaml")


# ── the frozen file this repository actually ships ─────────────────────────────

def test_the_committed_goalposts_load_and_are_self_consistent():
    from asi.core.constants import PROJECT_ROOT

    bounds = gp.load(PROJECT_ROOT / "registry" / "goalposts.yaml")
    assert bounds, "the shipped goalposts file is empty"
    for var, spec in bounds.items():
        assert spec["goalpost_min"] < spec["goalpost_max"], f"{var}: inverted goalposts"
        if spec.get("winsor_lower") is not None:
            assert spec["winsor_lower"] <= spec["winsor_upper"], f"{var}: inverted fences"
