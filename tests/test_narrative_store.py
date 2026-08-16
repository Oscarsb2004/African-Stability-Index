"""
The narrative corpus as the interface consumes it.

These tests guard the three claims the store is responsible for: that a record
round-trips into typed objects, that events are split by whether the panel can
actually reach them, and that the corpus never presents itself as more verified
than it is.
"""

import pytest

from asi.narrative.schema import Mode
from asi.narrative.store import (
    Balance, NarrativeRecord, RECMembership, load_corpus, parse,
)

PANEL_START, PANEL_END = 2000, 2024


@pytest.fixture(scope="module")
def corpus():
    c = load_corpus()
    if not c:
        pytest.skip("no narrative corpus on disk")
    return c


RAW = {
    "meta": {"iso3": "XXX", "name": "Testland", "last_updated": "2026-01-01",
             "iteration_count": 1, "next_action": "expand", "model_used": "m"},
    "historical": {
        "overview": "An overview.", "overview_citations": ["c1"],
        "colonial_legacy": "A legacy.", "colonial_legacy_citations": ["c1"],
        "key_periods": [{"title": "T", "period": "1900-1910", "summary": "S",
                         "citations": ["c1"]}],
    },
    "pillars": {"A": {"summary": "Governance summary.", "drivers": ["d1", "d2"],
                      "citations": ["c1"]}},
    "recent": {
        "primary": [{"headline": "H", "date": "2025-06-01", "summary": "S",
                     "why_it_matters": "W", "news_url": "https://n/x",
                     "wikipedia_url": "", "sentiment": "negative"}],
        "extended": [{"headline": "H2", "date": "2024-01-02", "summary": "S2",
                      "why_it_matters": "W2", "news_url": "", "wikipedia_url": "",
                      "sentiment": "positive"}],
    },
    "events": [
        {"year": 2010, "type": "coup", "title": "In panel", "description": "d",
         "url": "https://e/1", "direction": "deteriorate"},
        {"year": 1960, "type": "independence", "title": "Before panel",
         "description": "d", "url": "", "direction": "improve"},
        {"year": 2030, "type": "election", "title": "After panel", "description": "d",
         "url": "", "direction": "mixed"},
    ],
    "citations": [{"id": "c1", "url": "https://www.example.org/a/b",
                   "source_type": "news", "title": "T", "accessed": "2026-01-01",
                   "verified": True}],
    "rec_membership": [{"org": "ECOWAS", "joined": 1975, "status": "current",
                        "left": None, "citations": ["c1"]}],
    "balance": {"n_positive": 1, "n_negative": 1, "n_mixed": 0, "note": "n"},
}


# ── Parsing ────────────────────────────────────────────────────────────────────

def test_parse_round_trips_the_record():
    r = parse(RAW)
    assert isinstance(r, NarrativeRecord)
    assert (r.iso3, r.name) == ("XXX", "Testland")
    assert r.overview == "An overview."
    assert r.pillar("A").drivers == ("d1", "d2")
    assert len(r.recent_primary) == 1 and len(r.recent_extended) == 1
    assert r.balance == Balance(1, 1, 0, "n")


def test_parse_tolerates_an_empty_mapping():
    """A file that exists but is empty must not take the interface down."""
    r = parse({})
    assert r.iso3 == "" and r.events == () and r.balance is None
    assert r.cite(["c1"]) == []


def test_events_are_sorted_by_year():
    assert [e.year for e in parse(RAW).events] == [1960, 2010, 2030]


def test_citation_domain_strips_scheme_and_www():
    assert parse(RAW).citations["c1"].domain == "example.org"


# ── The panel split ────────────────────────────────────────────────────────────

def test_events_split_by_what_the_panel_can_reach():
    r = parse(RAW)
    assert [e.year for e in r.events_in(PANEL_START, PANEL_END)] == [2010]
    assert sorted(e.year for e in r.events_outside(PANEL_START, PANEL_END)) == [1960, 2030]


def test_event_years_groups_by_year():
    r = parse(RAW)
    assert list(r.event_years(PANEL_START, PANEL_END)) == [2010]


def test_every_event_is_either_inside_or_outside_never_both(corpus):
    for r in corpus.values():
        inside = r.events_in(PANEL_START, PANEL_END)
        outside = r.events_outside(PANEL_START, PANEL_END)
        assert len(inside) + len(outside) == len(r.events)
        assert not (set(inside) & set(outside))


# ── Citations ──────────────────────────────────────────────────────────────────

def test_cite_resolves_ids():
    assert [c.id for c in parse(RAW).cite(["c1"])] == ["c1"]


def test_cite_skips_dangling_ids_rather_than_raising():
    """narrative_check.py already fails a dangling reference; the UI should not
    also crash on a corpus that is merely older than the code."""
    assert parse(RAW).cite(["c1", "c99"]) == parse(RAW).cite(["c1"])


def test_corpus_citations_all_resolve(corpus):
    for r in corpus.values():
        referenced = set(r.overview_citations) | set(r.colonial_legacy_citations)
        for k in r.key_periods:
            referenced |= set(k.citations)
        for p in r.pillars.values():
            referenced |= set(p.citations)
        for m in r.rec_membership:
            referenced |= set(m.citations)
        # `panel` is the reserved id for the index's own output; it has no
        # citations-block entry because what it points at is not a page.
        assert referenced <= set(r.citations) | {"panel"},             f"{r.iso3} references missing citations"


# ── Provenance: the claim the corpus is allowed to make ────────────────────────

def test_audit_status_comes_from_the_rotation_not_the_flags():
    """
    A `verified` flag only means something once an AUDIT run has opened the page.
    A first-iteration record with every flag set to true is still unaudited.
    """
    r = parse(RAW)
    assert r.iteration_count == 1
    assert all(c.verified for c in r.citations.values())
    assert r.times_audited == 0 and r.audited is False


def test_audited_once_the_rotation_has_reached_an_audit_run():
    raw = {**RAW, "meta": {**RAW["meta"], "iteration_count": 4}}
    assert parse(raw).times_audited == 1
    assert parse(raw).audited is True


def test_unaudited_record_does_not_claim_confirmation():
    note = parse(RAW).provenance_note
    assert "No audit pass" in note
    assert "confirmed" not in note.replace("as confirmed", "")


def test_next_mode_follows_the_rotation():
    assert parse(RAW).next_mode is Mode.EXPAND
    assert parse({**RAW, "meta": {**RAW["meta"], "iteration_count": 3}}).next_mode is Mode.AUDIT


def test_whole_corpus_is_currently_unaudited(corpus):
    """
    Documents the corpus's real standing rather than assuming it. If an AUDIT
    pass later runs, this test should be updated deliberately — which is the
    point of asserting it.
    """
    assert all(not r.audited for r in corpus.values())


# ── Small value objects ────────────────────────────────────────────────────────

def test_membership_span_reads_without_a_key():
    assert RECMembership("ECOWAS", 1975, "current", None, ()).span == "1975–"
    assert RECMembership("EAC", 1967, "withdrawn", 1977, ()).span == "1967–1977"


def test_balance_total_counts_every_item():
    assert Balance(2, 3, 1, "").total == 6


# ── The corpus on disk ─────────────────────────────────────────────────────────

def test_corpus_loads_every_country(corpus):
    assert len(corpus) == 54


def test_missing_corpus_directory_is_not_an_error(tmp_path):
    """The index must still serve its numbers where the prose has not been written."""
    assert load_corpus(tmp_path / "nope") == {}


def test_no_narrative_for_a_pillar_the_index_greys_out(corpus):
    """
    Pillar C is greyed for every country in this edition, so no record may carry
    prose for it. This is the schema's rule; asserting it here keeps a future
    corpus edit from quietly reintroducing unsupported prose.
    """
    assert all("C" not in r.pillars for r in corpus.values())
