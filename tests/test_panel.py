"""
Panel construction: windowing, derived transforms, reliability interaction.

These are the functions that decide what counts as a measurement, so they are
tested against stated rules rather than against current data.
"""

import pytest

from asi.core.schema import Provenance, WindowMode, window_for
from asi.pipeline.panel import window_value, distance_from_parity
from asi.pipeline.normalize import normalize_value


# ── aggregation -> window translation ──────────────────────────────────────────

def test_aggregation_maps_to_window():
    assert window_for("most_recent") == (WindowMode.MOST_RECENT, 1)
    assert window_for("average_recent_3") == (WindowMode.ROLLING_MEAN, 3)
    assert window_for("average_recent_5") == (WindowMode.ROLLING_MEAN, 5)


def test_unknown_aggregation_is_rejected():
    with pytest.raises(ValueError, match="Unknown aggregation"):
        window_for("median_of_tuesdays")


# ── window_value: MOST_RECENT ──────────────────────────────────────────────────

OBS = {2010: 10.0, 2015: 15.0, 2020: 20.0}


def test_measurement_in_the_year_is_observed():
    v, p, src = window_value(OBS, 2015, WindowMode.MOST_RECENT, 1, 5)
    assert (v, p, src) == (15.0, Provenance.OBSERVED, 2015)


def test_older_measurement_is_carried_forward_and_records_its_year():
    v, p, src = window_value(OBS, 2017, WindowMode.MOST_RECENT, 1, 5)
    assert v == 15.0
    assert p is Provenance.CARRIED_FORWARD
    assert src == 2015, "must record where the number actually came from"


def test_carry_forward_expires():
    """A value older than max_carry_forward is not evidence about this year."""
    v, p, src = window_value(OBS, 2026, WindowMode.MOST_RECENT, 1, 5)
    assert v is None and p is Provenance.ABSENT


def test_carry_forward_boundary_is_inclusive():
    v, p, _ = window_value(OBS, 2025, WindowMode.MOST_RECENT, 1, 5)   # exactly 5 years
    assert v == 20.0 and p is Provenance.CARRIED_FORWARD


def test_no_lookahead():
    """A year before any measurement must not borrow from the future."""
    v, p, _ = window_value(OBS, 2005, WindowMode.MOST_RECENT, 1, 5)
    assert v is None and p is Provenance.ABSENT


def test_empty_observations():
    v, p, _ = window_value({}, 2015, WindowMode.MOST_RECENT, 1, 5)
    assert v is None and p is Provenance.ABSENT


# ── window_value: ROLLING_MEAN ─────────────────────────────────────────────────

DENSE = {2018: 1.0, 2019: 2.0, 2020: 3.0, 2021: 4.0, 2022: 5.0}


def test_rolling_mean_averages_the_trailing_window():
    v, p, src = window_value(DENSE, 2022, WindowMode.ROLLING_MEAN, 3, 5)
    assert v == pytest.approx((3.0 + 4.0 + 5.0) / 3)
    assert p is Provenance.OBSERVED and src == 2022


def test_rolling_mean_uses_only_what_exists():
    v, _, _ = window_value(DENSE, 2019, WindowMode.ROLLING_MEAN, 3, 5)
    assert v == pytest.approx((1.0 + 2.0) / 2), "must not invent the missing 2017"


def test_rolling_mean_year_not_measured_is_carried_forward():
    v, p, src = window_value(DENSE, 2023, WindowMode.ROLLING_MEAN, 3, 5)
    assert p is Provenance.CARRIED_FORWARD
    assert src == 2022
    assert v == pytest.approx((4.0 + 5.0) / 2)   # window 2021-2023, two real values


def test_rolling_mean_window_zero_uses_all_history():
    v, _, _ = window_value(DENSE, 2022, WindowMode.ROLLING_MEAN, 0, 5)
    assert v == pytest.approx(3.0)               # mean of 1..5


# ── window_value: POINT ────────────────────────────────────────────────────────

def test_point_mode_refuses_to_carry_forward():
    assert window_value(OBS, 2015, WindowMode.POINT, 1, 5)[1] is Provenance.OBSERVED
    assert window_value(OBS, 2016, WindowMode.POINT, 1, 5)[1] is Provenance.ABSENT


# ── GPI parity transform ───────────────────────────────────────────────────────

def test_parity_is_the_maximum():
    assert distance_from_parity(1.0) == 1.0


def test_equal_and_opposite_gaps_score_the_same():
    """The whole point: 0.8 and 1.2 are the same size of inequity."""
    assert distance_from_parity(0.8) == pytest.approx(distance_from_parity(1.2))


def test_over_parity_no_longer_beats_parity():
    """Regression guard for the pre-2026 bug: GPI 1.16 outscoring GPI 1.00."""
    assert distance_from_parity(1.16) < distance_from_parity(1.0)


def test_worse_gaps_score_lower():
    assert distance_from_parity(0.6) < distance_from_parity(0.9) < distance_from_parity(1.0)


def test_parity_handles_missing():
    assert distance_from_parity(None) is None


# ── goalpost normalization ─────────────────────────────────────────────────────

def test_positive_polarity_maps_range_to_0_100():
    assert normalize_value(0.0, 0.0, 10.0, "positive")[0] == pytest.approx(0.0)
    assert normalize_value(10.0, 0.0, 10.0, "positive")[0] == pytest.approx(100.0)
    assert normalize_value(5.0, 0.0, 10.0, "positive")[0] == pytest.approx(50.0)


def test_negative_polarity_inverts():
    assert normalize_value(0.0, 0.0, 10.0, "negative")[0] == pytest.approx(100.0)
    assert normalize_value(10.0, 0.0, 10.0, "negative")[0] == pytest.approx(0.0)


def test_values_outside_frozen_goalposts_are_clamped_and_flagged():
    """
    Fixed goalposts mean later data can exceed them. Clamping keeps the scale
    stable; the flag keeps it visible.
    """
    score, clamped = normalize_value(12.0, 0.0, 10.0, "positive")
    assert score == 100.0 and clamped is True

    score, clamped = normalize_value(-2.0, 0.0, 10.0, "positive")
    assert score == 0.0 and clamped is True


def test_in_range_values_are_not_flagged():
    assert normalize_value(5.0, 0.0, 10.0, "positive")[1] is False


def test_zero_width_goalposts_give_neutral_score():
    assert normalize_value(3.0, 3.0, 3.0, "positive")[0] == 50.0


def test_missing_value_stays_missing():
    assert normalize_value(None, 0.0, 10.0, "positive") == (None, False)
