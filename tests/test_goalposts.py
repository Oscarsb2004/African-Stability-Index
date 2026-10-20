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


def test_an_imputed_or_carried_value_never_sets_a_goalpost():
    """
    Edition 2 (plan 4.4): goalposts come from observed values only. In edition 1
    an extreme set by a regional mean was flagged for review; now it cannot set
    the extreme at all.
    """
    out = gp.compute(
        _panel([1.0, 50.0, 100.0, 200.0], ["regional_mean", "observed", "observed", "carried_forward"]),
        {"gdp_pc": {}}, 1.5,
    )["gdp_pc"]
    assert (out["goalpost_min"], out["goalpost_max"]) == (50.0, 100.0)
    assert out["goalpost_source"] == "observed"
    # negative control: marked observed, the low value now sets the lower bound
    every = gp.compute(_panel([1.0, 50.0, 100.0, 200.0]), {"gdp_pc": {}}, 1.5)["gdp_pc"]
    assert every["goalpost_min"] == 1.0


def test_theoretical_bounds_are_the_goalposts_where_the_registry_gives_them():
    out = gp.compute(_panel([20.0, 40.0, 60.0]), {"gdp_pc": {"theoretical_bounds": [0, 100]}}, 1.5)["gdp_pc"]
    assert (out["goalpost_min"], out["goalpost_max"], out["goalpost_source"]) == (0.0, 100.0, "theoretical")


def test_the_trimmed_rule_replaces_only_values_beyond_three_trimmed_sds():
    values = pd.Series(list(np.linspace(0.0, 10.0, 99)) + [1000.0])
    lo, hi, lo_to, hi_to = gp.trimmed_outlier_bounds(values)
    capped = gp.cap_outliers(values, lo, hi, lo_to, hi_to)
    assert capped.iloc[-1] == pytest.approx(hi_to)       # the outlier comes in to 3.1 trimmed SDs
    assert (capped.iloc[:-1] == values.iloc[:-1]).all()   # the rest are untouched
    assert hi_to > hi                                     # replaced just beyond the 3-SD threshold, as the IIAG does
    # negative control: no outlier, nothing moves
    plain = pd.Series(np.linspace(0.0, 10.0, 100))
    assert (gp.cap_outliers(plain, *gp.trimmed_outlier_bounds(plain)) == plain).all()


def test_a_zero_heavy_series_is_tested_on_its_non_zero_values_and_its_zeros_are_never_capped():
    """P100: a violent year is compared with other violent years. A series shaped like UCDP's: 70% zeros, small
    counts, a few larger ones and one extreme. The whole series' trimmed rule caps nearly every larger count;
    tested on the counts alone, it caps fewer, still caps the extreme, and leaves every zero alone."""
    raw = pd.Series([0.0] * 140 + list(np.linspace(0.1, 1.0, 50)) + list(np.linspace(2.0, 10.0, 9)) + [500.0])
    logged = np.log(raw + 1)
    whole = gp.cap_outliers(logged, *gp.trimmed_outlier_bounds(logged))
    split = gp.cap_outliers(logged, *gp.outlier_bounds(logged, raw))
    assert (whole < logged).sum() == 9                       # eight of the nine larger counts, and the extreme
    assert 0 < (split < logged).sum() < (whole < logged).sum()
    assert split.iloc[-1] < logged.iloc[-1]                  # the extreme is still capped
    assert (split.iloc[:140] == 0).all()                     # zeros are never capped
    plain = pd.Series(np.linspace(1.0, 10.0, 100))            # negative control: not zero-heavy, the rule as before
    assert gp.outlier_bounds(plain, plain) == gp.trimmed_outlier_bounds(plain)


def test_adding_an_indicator_never_moves_an_existing_goalpost():
    frozen = {"a": {"goalpost_min": 0.0, "goalpost_max": 1.0}}
    computed = {"a": {"goalpost_min": -5.0, "goalpost_max": 9.0}, "b": {"goalpost_min": 2.0, "goalpost_max": 3.0}}
    merged, added = gp.add_new(frozen, computed)
    assert merged["a"] == frozen["a"] and merged["b"] == computed["b"] and added == ["b"]


def test_compute_carries_polarity_and_lets_the_skew_test_decide_the_log():
    """Edition 2 (plan 4.6): the registry's log flag no longer decides; the skew test does."""
    out = gp.compute(_panel([1.0, 2.0, 3.0]),
                     {"gdp_pc": {"log_transform": True, "polarity": "negative"}},
                     1.5)["gdp_pc"]
    assert out["polarity"] == "negative"
    assert out["log_transform"] is False  # three evenly spaced values have no skew, whatever the flag says


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


# ── the pipeline may not re-anchor them by accident ────────────────────────────

def test_the_stage_script_freezes_only_when_told_to():
    """
    `02_panel.py` used to read `if args.freeze_goalposts or not
    GOALPOSTS_FILE.exists()`, which quietly undid the rule this module states in
    its own docstring. A deleted, gitignored or never-committed
    `registry/goalposts.yaml` re-anchored every historical score against the
    current panel, logged as an ordinary step — and the resulting scores would
    look entirely normal while being incomparable with any published edition.

    Read from the syntax tree, not by substring: the comment explaining the fix
    quotes the removed condition, and a grep would trip on the explanation. The
    guard is the shape of the `if` — a bare flag, never a disjunction.
    """
    import ast

    from asi.core.constants import PROJECT_ROOT

    tree = ast.parse((PROJECT_ROOT / "02_panel.py").read_text(encoding="utf-8"))
    guards = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and "freeze_goalposts" in ast.unparse(node.test)
    ]
    assert guards, "02_panel.py no longer guards the freeze step at all"
    for node in guards:
        assert not isinstance(node.test, ast.BoolOp), (
            f"the freeze step runs on `{ast.unparse(node.test)}` — anything beyond "
            f"the explicit flag re-anchors every historical score when the file "
            f"happens to be missing")


def test_the_error_message_names_a_command_that_exists():
    """
    It told the user to run `03_normalize.py`, which was retired. An error whose
    remedy does not exist teaches people to delete the check instead.
    """
    from asi.core.constants import PROJECT_ROOT

    with pytest.raises(FileNotFoundError) as exc:
        gp.load(PROJECT_ROOT / "registry" / "no-such-goalposts.yaml")
    message = str(exc.value)
    assert "03_normalize.py" not in message
    assert "02_panel.py --freeze-goalposts" in message
    assert (PROJECT_ROOT / "02_panel.py").exists()


def test_the_reference_year_threshold_is_a_named_constant():
    """A bare 0.80 inside a stage script decides what year the whole site describes."""
    from asi.core.constants import PROJECT_ROOT, REFERENCE_YEAR_MIN_COVERAGE

    assert 0.0 < REFERENCE_YEAR_MIN_COVERAGE <= 1.0
    src = (PROJECT_ROOT / "02_panel.py").read_text(encoding="utf-8")
    assert "REFERENCE_YEAR_MIN_COVERAGE" in src
    assert ">= 0.80" not in src


# ── the log rule (edition 2, plan 4.6) ─────────────────────────────────────────

def test_the_skew_test_logs_only_a_significant_right_skew():
    rng = np.random.default_rng(3)
    right = pd.Series(rng.lognormal(0.0, 1.0, 54))
    symmetric = pd.Series(rng.normal(0.0, 1.0, 54))
    assert gp.skew_test(right)[3] > gp.SKEW_Z
    assert abs(gp.skew_test(symmetric)[3]) < gp.SKEW_Z  # negative control
    n, skew, se, z = gp.skew_test([1.0, 2.0, 3.0, 10.0])
    assert n == 4 and se == pytest.approx(np.sqrt(6 * 4 * 3 / (2 * 5 * 7))) and z == pytest.approx(skew / se)


def test_osborne_constant_makes_the_minimum_one():
    panel = pd.DataFrame({"iso3": [f"S{i}" for i in range(40)], "year": 2020, "variable_name": "gdp_pc",
                          "provenance": "observed",
                          "raw_value": np.random.default_rng(4).lognormal(3.0, 1.0, 40) + 50.0})
    out = gp.compute(panel, {"gdp_pc": {}}, 1.5)["gdp_pc"]
    assert out["log_transform"] is True
    assert out["log_constant"] == pytest.approx(1.0 - panel["raw_value"].min())
    logged = gp.apply_log(panel["raw_value"], True, out["log_constant"])
    assert logged.min() == pytest.approx(0.0)  # log(1)


def test_the_registry_flags_match_the_frozen_log_rule():
    """The frozen goalposts decide the log; the registry must say the same, so nobody reads a stale flag."""
    import glob
    frozen = yaml.safe_load(open("registry/goalposts.yaml", encoding="utf-8"))["indicators"]
    registry = {e["variable_name"]: e for f in glob.glob("indicators_list/*.yaml")
                for e in yaml.safe_load(open(f, encoding="utf-8")) or []}
    mismatched = [v for v, b in frozen.items() if bool(registry[v].get("log_transform")) != b["log_transform"]]
    assert mismatched == []
