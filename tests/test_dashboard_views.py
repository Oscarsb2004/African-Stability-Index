"""
Every view renders, for every country — and renders the right numbers.

The narrative layer adds a second data source to the country and pillar pages,
and a record is written by a language model across many sessions. A field that
is absent, empty, or a different shape than expected should degrade to a stated
absence — never to a traceback on a page a reader has already opened.

`assert view(...) is not None` was the whole of that guarantee until B06. A Dash
view function returns a component tree or raises; it never returns None. So the
assertion could only fail on an exception, and 54 country-view tests passed
while the country page rendered a continental rank under the label "in scope".
The tests below therefore read the tree the view actually produced and compare
what is on it against `data/panel/*.csv`.
"""

import re

import pytest

from asi.core.constants import PILLAR_DEFS
from asi import results as D
from asi.dashboard.app import (
    PANEL, NARRATIVE, TIER_STYLE, view_country, view_pillar, view_overview,
)

LENS = D.Lens("composite", "equal")
ISO3S = sorted(PANEL.countries)
YEAR = PANEL.reference_year


# ── Reading a rendered Dash tree ───────────────────────────────────────────────

def _walk(node):
    """Every component and string in a rendered tree, depth-first."""
    if node is None:
        return
    if isinstance(node, (list, tuple)):
        for item in node:
            yield from _walk(item)
        return
    yield node
    children = getattr(node, "children", None)
    if children is not None:
        yield from _walk(children)


def _texts(node) -> list[str]:
    """Every string rendered anywhere in the tree, in document order."""
    out = []
    for n in _walk(node):
        if isinstance(n, str):
            out.append(n)
        elif isinstance(n, (int, float)):
            out.append(str(n))
    return out


def _titles(node) -> list[str]:
    """
    Every `title` tooltip in the tree — where the stated reasons live.

    Strings are skipped explicitly: `"x".title` is a builtin method, so a plain
    getattr over the whole tree collects bound methods instead of tooltips.
    """
    out = []
    for n in _walk(node):
        if isinstance(n, str):
            continue
        title = getattr(n, "title", None)
        if isinstance(title, str) and title:
            out.append(title)
    return out


def _rendered(iso3, year=None):
    return view_country(iso3, LENS, year if year is not None else YEAR)


def _published(iso3, year=None):
    """The composite row the page is supposed to be showing."""
    year = YEAR if year is None else year
    c = PANEL.composites
    row = c[(c["iso3"] == iso3) & (c["method"] == "equal") & (c["year"] == year)]
    return None if row.empty else row.iloc[0]


# ── The corpus is wired in ─────────────────────────────────────────────────────

def test_the_corpus_is_actually_wired_in():
    """Guards the failure this work started from: 54 records and nothing reading them."""
    assert NARRATIVE, "no narrative records loaded into the dashboard"
    assert set(NARRATIVE) & set(ISO3S), "narrative records do not match panel countries"


# ── Country page: the numbers on it are the published ones ─────────────────────

@pytest.mark.parametrize("iso3", ISO3S)
def test_country_page_renders_the_country_it_was_asked_for(iso3):
    """
    Falsifiable version of the old render check. A view that returned another
    country's page, or an empty shell, passed `is not None`; it does not pass
    this.
    """
    texts = _texts(_rendered(iso3))
    name = PANEL.countries[iso3].get("name", iso3)
    assert name in texts, f"{iso3}: the page does not carry the country's name"


@pytest.mark.parametrize("iso3", ISO3S)
def test_the_headline_score_is_the_published_composite(iso3):
    """
    The number the page leads with, against composites.csv. An untrustworthy
    composite must render an em dash rather than a figure — showing the number
    anyway is the failure the reliability tiers exist to prevent.
    """
    texts = _texts(_rendered(iso3))
    row = _published(iso3)
    shown = (row is not None and row["reliability"] in D.DISPLAYABLE
             and row["score"] == row["score"])
    if shown:
        assert f"{row['score']:.1f}" in texts, (
            f"{iso3}: expected headline {row['score']:.1f}, not found on the page")
    else:
        assert "—" in texts, f"{iso3}: an unshowable composite must render a dash"


@pytest.mark.parametrize("iso3", ISO3S)
def test_the_rank_on_the_page_is_the_published_rank(iso3):
    """
    Pins what the page actually shows: the continental rank from composites.csv.

    Deliberately not asserted against `D.rankings()`'s `scope_rank`, which is
    what the label claims — see the xfail below. Two separate statements: this
    one is a content assertion that catches a rendering regression today, that
    one records a defect the maintainer has still to rule on.
    """
    texts = _texts(_rendered(iso3))
    row = _published(iso3)
    if row is not None and row["rank"] == row["rank"]:
        assert f"#{int(row['rank'])}" in texts, (
            f"{iso3}: expected rank #{int(row['rank'])} on the page")
    else:
        assert "Rank" in texts, f"{iso3}: the rank stat should still be present"


@pytest.mark.xfail(strict=True, reason="B13: the page renders a continental rank "
                                       "under the label 'in scope'. Needs the "
                                       "maintainer's call on which to change.")
def test_the_rank_label_describes_the_rank_shown():
    """
    The defect the 54 passing render tests never noticed, written down.

    `view_country` takes no grouping argument, so it cannot know what scope the
    reader is comparing within; it shows `composites.csv`'s continental rank and
    labels it "in scope". Inside ECOWAS a country ranked #2 of 12 is shown its
    continental position instead.

    Strict xfail: when B13 lands, this test starts passing and pytest fails on
    the stale marker, which is how the note gets removed rather than forgotten.
    """
    iso3 = "GHA" if "GHA" in ISO3S else ISO3S[0]
    page = _rendered(iso3)
    texts = _texts(page)

    frame = D.choropleth_frame(PANEL, LENS, YEAR)
    scoped = D.rankings(D.apply_grouping(frame, "rec", "ECOWAS"))
    mine = scoped[scoped["iso3"] == iso3]
    if mine.empty:
        pytest.skip(f"{iso3} is not rankable within ECOWAS at {YEAR}")

    assert "in scope" in texts
    assert f"#{int(mine.iloc[0]['scope_rank'])}" in texts


@pytest.mark.parametrize("iso3", ISO3S)
def test_the_pillars_shown_count_matches_the_displayable_tiers(iso3):
    """The page states how many of the seven pillars it is willing to show."""
    page = _rendered(iso3)
    texts = _texts(page)
    pil = PANEL.pillar_scores
    at_year = pil[(pil["iso3"] == iso3) & (pil["year"] == YEAR)]
    expected = int(at_year["reliability"].isin(D.DISPLAYABLE).sum())
    assert str(expected) in texts, f"{iso3}: expected 'Pillars shown' = {expected}"
    assert f"of {len(PILLAR_DEFS)}" in texts


# ── Pillar cards: value, tier badge, and the stated reason ─────────────────────

def _greyed_examples(limit=8):
    """(iso3, pillar_id) pairs the index refuses to score at the reference year."""
    pil = PANEL.pillar_scores
    at_year = pil[(pil["year"] == YEAR) & ~pil["reliability"].isin(D.DISPLAYABLE)]
    return [(r.iso3, r.pillar_id) for r in at_year.head(limit).itertuples()]


def test_there_are_greyed_pillars_to_check():
    """A fixture that silently matched nothing would make the next test vacuous."""
    assert _greyed_examples(), "no greyed pillar-years at the reference year"


@pytest.mark.parametrize("iso3,pillar_id", _greyed_examples())
def test_a_greyed_pillar_card_shows_a_dash_and_states_a_reason(iso3, pillar_id):
    """
    A blank cell and an untrustworthy cell are different claims, and the page
    must not collapse them. The card renders an em dash instead of a figure, and
    a tooltip saying why — an unexplained grey box reads as a bug in the site.
    """
    page = _rendered(iso3)
    assert "—" in _texts(page), f"{iso3}/{pillar_id}: no dash rendered for a greyed pillar"

    reasons = " ".join(_titles(page)).lower()
    assert ("inferred" in reasons or "no data available" in reasons), (
        f"{iso3}/{pillar_id}: no stated reason for the greyed card")


@pytest.mark.parametrize("iso3", ISO3S[:14])
def test_every_tier_badge_matches_pillar_scores_csv(iso3):
    """
    Each of the seven cards carries the tier the panel published for it. A badge
    reading 'Measured' over an inferred number is the most direct way this
    interface could mislead, and nothing checked it.
    """
    texts = _texts(_rendered(iso3))
    pil = PANEL.pillar_scores
    at_year = pil[(pil["iso3"] == iso3) & (pil["year"] == YEAR)].set_index("pillar_id")

    for pid in PILLAR_DEFS:
        tier = at_year.loc[pid, "reliability"] if pid in at_year.index else "absent"
        label = TIER_STYLE.get(tier, TIER_STYLE["absent"])[1]
        assert label in texts, (
            f"{iso3}/{pid}: panel says {tier!r}, badge {label!r} not on the page")


@pytest.mark.parametrize("iso3", ISO3S[:14])
def test_a_displayable_pillar_renders_its_published_score(iso3):
    page_texts = _texts(_rendered(iso3))
    pil = PANEL.pillar_scores
    at_year = pil[(pil["iso3"] == iso3) & (pil["year"] == YEAR)]
    shown = at_year[at_year["reliability"].isin(D.DISPLAYABLE) & at_year["score"].notna()]
    for r in shown.itertuples():
        assert f"{r.score:.1f}" in page_texts, (
            f"{iso3}/{r.pillar_id}: expected {r.score:.1f} on a card")


# ── Pillar page ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("pillar_id", sorted(PILLAR_DEFS))
def test_pillar_view_names_the_pillar_it_was_asked_for(pillar_id):
    """Includes pillar C, which is greyed everywhere and has no prose by design."""
    for iso3 in ISO3S[:12]:
        texts = " ".join(_texts(view_pillar(iso3, pillar_id, YEAR)))
        assert PILLAR_DEFS[pillar_id] in texts, (
            f"{iso3}/{pillar_id}: the pillar's own name is not on its page")


@pytest.mark.parametrize("pillar_id", sorted(PILLAR_DEFS))
def test_pillar_view_lists_the_indicators_the_panel_assigns_to_it(pillar_id):
    """
    The page must show this pillar's indicators and no others. Identity travels
    with the panel rows, so a page listing a neighbouring pillar's series would
    mean the filter, not the registry, is wrong.
    """
    iso3 = ISO3S[0]
    texts = " ".join(_texts(view_pillar(iso3, pillar_id, YEAR)))
    rows = D.country_indicators(PANEL, iso3, YEAR, pillar_id)
    if rows.empty:
        pytest.skip(f"{pillar_id} has no indicator rows for {iso3} at {YEAR}")
    for name in rows["display_name"]:
        assert str(name) in texts, f"{pillar_id}: {name!r} missing from the page"


# ── Degradation ────────────────────────────────────────────────────────────────

def test_country_view_renders_at_both_ends_of_the_panel():
    """Years outside the reference year exercise the event callout and greyed tiers."""
    for year in (PANEL.panel_start, PANEL.panel_end):
        for iso3 in ISO3S[:8]:
            name = PANEL.countries[iso3].get("name", iso3)
            assert name in _texts(view_country(iso3, LENS, year)), (
                f"{iso3} at {year}: page rendered without the country's name")


def test_the_last_panel_year_shows_dashes_rather_than_numbers():
    """
    2024 is entirely unreliable — World Bank series report late — so the final
    year is a real state the interface has to express, not an error. It must
    render the absence rather than a stale figure carried forward.
    """
    texts = _texts(view_country(ISO3S[0], LENS, PANEL.panel_end))
    assert "—" in texts


def test_country_view_survives_a_missing_narrative_record(monkeypatch):
    """A country the research pass has not reached must still render its numbers."""
    import asi.dashboard.app as app_module
    monkeypatch.setattr(app_module, "NARRATIVE", {})
    iso3 = ISO3S[0]
    name = PANEL.countries[iso3].get("name", iso3)

    country = app_module.view_country(iso3, LENS, YEAR)
    assert name in _texts(country), "numbers must survive a missing record"

    pillar = app_module.view_pillar(iso3, "A", YEAR)
    assert PILLAR_DEFS["A"] in " ".join(_texts(pillar))


# ── Overview ───────────────────────────────────────────────────────────────────

def test_overview_states_its_coverage_without_hardcoding_it():
    """
    The header counts must be derived. Contract check 2.1 fails the build on a
    typed one; this asserts the derived numbers are actually correct, which the
    contract check cannot tell.
    """
    texts = _texts(view_overview(LENS, "all", None, False, YEAR))
    joined = " ".join(texts)
    assert str(len(PANEL.countries)) in joined
    assert str(len(PILLAR_DEFS)) in joined


def test_overview_renders_a_year_it_can_rank_nothing_in():
    """The empty-scope path: 2024 is unrankable, and must not crash the map."""
    assert _texts(view_overview(LENS, "all", None, False, PANEL.panel_end))


def test_overview_scoped_to_a_rec_still_renders():
    texts = _texts(view_overview(LENS, "rec", "ECOWAS", False, YEAR))
    assert "ECOWAS" in " ".join(texts)
