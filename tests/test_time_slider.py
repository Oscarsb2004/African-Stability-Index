"""
The continent-scale time slider.

Putting the year control on the map raises two problems the country-page slider
never had, and both are tested here rather than left to be discovered:

  1. Some years cannot be scored at all. 2024 is inside the panel but has no
     reported data yet, and 2001 predates annual governance reporting. A slider
     that lands on either must say why, or an empty continent reads as a bug.

  2. Regional community membership is stored as current status only. Grouping
     "ECOWAS" at 2010 with 2026's membership list silently compares the wrong
     set of countries, so the mismatch has to be surfaced.
"""

import pytest

from asi.core.constants import PILLAR_DEFS
from asi.dashboard import data as D
from asi.dashboard.app import (
    PANEL, rec_membership_caveat, view_country, view_overview, view_rankings,
    year_coverage_note, year_slider,
)

LENS = D.Lens("composite", "equal")
YEARS = list(range(PANEL.panel_start, PANEL.panel_end + 1))


def _text(node, out=None):
    out = [] if out is None else out
    if isinstance(node, str):
        out.append(node)
        return out
    if isinstance(node, (list, tuple)):
        for n in node:
            _text(n, out)
        return out
    children = getattr(node, "children", None)
    if children is not None:
        _text(children, out)
    return out


def _find_slider_ids(node, found=None):
    found = [] if found is None else found
    cid = getattr(node, "id", None)
    if isinstance(cid, dict) and cid.get("type") == "year-slider":
        found.append(cid)
    children = getattr(node, "children", None)
    if children is not None:
        if not isinstance(children, (list, tuple)):
            children = [children]
        for c in children:
            _find_slider_ids(c, found)
    return found


# ── The control exists where the year is used ──────────────────────────────────

def test_overview_has_a_year_slider():
    ids = _find_slider_ids(view_overview(LENS, "all", None, False, 2015))
    assert [i["index"] for i in ids] == ["overview"]


def test_rankings_has_a_year_slider():
    ids = _find_slider_ids(view_rankings(LENS, "all", None, False, 2015))
    assert [i["index"] for i in ids] == ["rankings"]


def test_country_still_has_its_own_slider():
    ids = _find_slider_ids(view_country("KEN", LENS, 2015))
    assert [i["index"] for i in ids] == ["country"]


def test_slider_ids_are_pattern_matching():
    """A plain id here would break navigation on every page lacking the slider."""
    cid = _find_slider_ids(year_slider("overview", 2010))[0]
    assert set(cid) == {"type", "index"}


def test_only_one_slider_per_view():
    """Two sliders in one view would race to write the same nav.year."""
    for view in (view_overview(LENS, "all", None, False, 2010),
                 view_rankings(LENS, "all", None, False, 2010),
                 view_country("KEN", LENS, 2010)):
        assert len(_find_slider_ids(view)) == 1


# ── Years that cannot be scored ────────────────────────────────────────────────

def test_full_coverage_needs_no_note():
    assert year_coverage_note(2015, 54, 54) is None


def test_a_year_past_the_reference_year_explains_the_lag():
    note = " ".join(_text(year_coverage_note(PANEL.panel_end, 0, 54)))
    assert "0 of 54" in note
    assert str(PANEL.reference_year) in note
    assert "lag" in note


def test_2001_explains_the_biennial_governance_gap():
    note = " ".join(_text(year_coverage_note(2001, 17, 54)))
    assert "biennial" in note


def test_partial_coverage_still_says_something():
    assert year_coverage_note(2008, 53, 54) is not None


# ── Membership is current-status only ──────────────────────────────────────────

def test_no_caveat_when_not_grouping_by_community():
    assert rec_membership_caveat("all", None, 2005) is None
    assert rec_membership_caveat("region", "West", 2005) is None


def test_caveat_names_countries_that_left_since():
    """Mali, Burkina Faso and Niger were in ECOWAS in 2010 and are not now."""
    note = " ".join(_text(rec_membership_caveat("rec", "ECOWAS", 2010)))
    for country in ("Mali", "Burkina Faso", "Niger"):
        assert country in note


def test_caveat_catches_a_community_that_did_not_exist_yet():
    """The EAC collapsed in 1977 and was refounded in 2000."""
    note = " ".join(_text(rec_membership_caveat("rec", "EAC", 1998)))
    assert "had not joined yet" in note
    assert "Kenya" in note and "Tanzania" in note


def test_caveat_is_silent_where_membership_matches(monkeypatch):
    """No warning should fire for a year whose membership is the current one."""
    import asi.dashboard.app as app_module
    monkeypatch.setattr(app_module, "NARRATIVE", {})
    assert app_module.rec_membership_caveat("rec", "ECOWAS", 2010) is None


# ── Every year renders ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("year", YEARS)
def test_overview_renders_for_every_year(year):
    assert view_overview(LENS, "all", None, False, year) is not None


@pytest.mark.parametrize("year", YEARS)
def test_rankings_renders_for_every_year_including_empty_ones(year):
    assert view_rankings(LENS, "rec", "ECOWAS", False, year) is not None


@pytest.mark.parametrize("pillar_id", sorted(PILLAR_DEFS))
def test_pillar_lens_renders_at_an_unscoreable_year(pillar_id):
    assert view_overview(D.Lens("pillar", pillar_id), "all", None, False,
                         PANEL.panel_end) is not None
