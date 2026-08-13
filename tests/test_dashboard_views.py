"""
Every view renders, for every country.

The narrative layer adds a second data source to the country and pillar pages,
and a record is written by a language model across many sessions. A field that
is absent, empty, or a different shape than expected should degrade to a stated
absence — never to a traceback on a page a reader has already opened.
"""

import pytest

from asi.core.constants import PILLAR_DEFS
from asi.dashboard import data as D
from asi.dashboard.app import PANEL, NARRATIVE, view_country, view_pillar, view_overview

LENS = D.Lens("composite", "equal")
ISO3S = sorted(PANEL.countries)


def test_the_corpus_is_actually_wired_in():
    """Guards the failure this work started from: 54 records and nothing reading them."""
    assert NARRATIVE, "no narrative records loaded into the dashboard"
    assert set(NARRATIVE) & set(ISO3S), "narrative records do not match panel countries"


@pytest.mark.parametrize("iso3", ISO3S)
def test_country_view_renders(iso3):
    assert view_country(iso3, LENS, PANEL.reference_year) is not None


@pytest.mark.parametrize("pillar_id", sorted(PILLAR_DEFS))
def test_pillar_view_renders_for_every_pillar(pillar_id):
    """Includes pillar C, which is greyed everywhere and has no prose by design."""
    for iso3 in ISO3S[:12]:
        assert view_pillar(iso3, pillar_id, PANEL.reference_year) is not None


def test_country_view_renders_at_both_ends_of_the_panel():
    """Years outside the reference year exercise the event callout and greyed tiers."""
    for year in (PANEL.panel_start, PANEL.panel_end):
        for iso3 in ISO3S[:8]:
            assert view_country(iso3, LENS, year) is not None


def test_country_view_survives_a_missing_narrative_record(monkeypatch):
    """A country the research pass has not reached must still render its numbers."""
    import asi.dashboard.app as app_module
    monkeypatch.setattr(app_module, "NARRATIVE", {})
    assert app_module.view_country(ISO3S[0], LENS, PANEL.reference_year) is not None
    assert app_module.view_pillar(ISO3S[0], "A", PANEL.reference_year) is not None


def test_overview_still_renders():
    assert view_overview(LENS, "all", None, False, PANEL.reference_year) is not None
