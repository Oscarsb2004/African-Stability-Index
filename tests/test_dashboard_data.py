"""
Dashboard data layer.

The point of these tests is that the interface derives nothing. If a value the
UI shows can be produced here but not found in the panel, the frontend and
backend have drifted — which is the failure mode the whole contract exists to
prevent.
"""

import pandas as pd
import pytest

from asi.dashboard.data import (
    Lens, apply_grouping, rankings, reliability_note, DISPLAYABLE,
)


# ── Lens ───────────────────────────────────────────────────────────────────────

def test_lens_round_trip():
    for value in ("composite:equal", "pillar:D", "composite:geometric"):
        assert Lens.parse(value).value == value


def test_lens_defaults_when_absent_or_malformed():
    for bad in (None, "", "nonsense", "unknown:D"):
        lens = Lens.parse(bad)
        assert lens.kind == "composite" and lens.key == "equal"


def test_lens_labels():
    assert "Health" in Lens("pillar", "D").label({})
    assert Lens("composite", "equal").label({"equal": "Equal Weights"}) == "Equal Weights"


# ── Grouping ───────────────────────────────────────────────────────────────────

@pytest.fixture
def frame():
    return pd.DataFrame([
        {"iso3": "GHA", "region": "West",    "island_state": False,
         "recs": ["ECOWAS", "CEN-SAD"], "score": 60.0, "displayable": True},
        {"iso3": "NGA", "region": "West",    "island_state": False,
         "recs": ["ECOWAS", "CEN-SAD"], "score": 50.0, "displayable": True},
        {"iso3": "KEN", "region": "East",    "island_state": False,
         "recs": ["EAC", "COMESA"],     "score": 55.0, "displayable": True},
        {"iso3": "MUS", "region": "Islands", "island_state": True,
         "recs": ["COMESA", "SADC"],    "score": 75.0, "displayable": True},
        {"iso3": "SOM", "region": "East",    "island_state": False,
         "recs": ["IGAD"],              "score": 30.0, "displayable": False},
    ])


def test_grouping_by_rec_marks_members(frame):
    out = apply_grouping(frame, "rec", "ECOWAS")
    assert set(out[out["in_scope"]]["iso3"]) == {"GHA", "NGA"}


def test_grouping_never_removes_rows(frame):
    """Out-of-scope countries must still render, greyed — not vanish."""
    out = apply_grouping(frame, "rec", "EAC")
    assert len(out) == len(frame)


def test_grouping_by_region(frame):
    out = apply_grouping(frame, "region", "East")
    assert set(out[out["in_scope"]]["iso3"]) == {"KEN", "SOM"}


def test_grouping_all_includes_everyone(frame):
    assert apply_grouping(frame, "all", None)["in_scope"].all()


def test_island_exclusion_composes_with_grouping(frame):
    out = apply_grouping(frame, "all", None, exclude_islands=True)
    assert not out.set_index("iso3").loc["MUS", "in_scope"]
    assert out.set_index("iso3").loc["GHA", "in_scope"]


# ── Rankings ───────────────────────────────────────────────────────────────────

def test_rankings_exclude_undisplayable(frame):
    out = rankings(apply_grouping(frame, "all", None))
    assert "SOM" not in set(out["iso3"]), "an unreliable score must not be ranked"


def test_rankings_are_scoped_not_continental(frame):
    """Inside a community the reader wants position within it."""
    out = rankings(apply_grouping(frame, "rec", "ECOWAS"))
    assert list(out["iso3"]) == ["GHA", "NGA"]
    assert list(out["scope_rank"]) == [1, 2]


def test_rankings_sorted_descending(frame):
    out = rankings(apply_grouping(frame, "all", None))
    assert list(out["score"]) == sorted(out["score"], reverse=True)


def test_rankings_empty_scope_is_safe(frame):
    out = rankings(apply_grouping(frame, "rec", "NONEXISTENT"))
    assert out.empty


# ── Reliability messaging ──────────────────────────────────────────────────────

def test_displayable_tiers_are_exactly_reliable_and_thin():
    assert set(DISPLAYABLE) == {"reliable", "thin"}


def test_unreliable_note_explains_rather_than_blames():
    note = reliability_note("unreliable", 0.2)
    assert "inferred" in note and "20%" in note


def test_every_tier_has_a_message():
    for tier in ("reliable", "thin", "unreliable", "absent"):
        assert reliability_note(tier).strip()


# ── Empty-scope regression ─────────────────────────────────────────────────────

def test_rankings_keeps_its_shape_when_nothing_is_rankable(frame):
    """
    2024 is entirely unreliable (World Bank series report late), so a user who
    slides there must get an empty view, not a crash. Callers merge on
    scope_rank, so the column has to exist even with no rows.
    """
    none_displayable = frame.assign(displayable=False)
    out = rankings(apply_grouping(none_displayable, "all", None))
    assert out.empty
    assert "scope_rank" in out.columns
