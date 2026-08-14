"""
Consistency checks: does a record's prose agree with the record and the panel?

`validate()` enforces shape. These checks enforce truth, and exist because the
corpus shipped with real violations that shape-checking could never see:

  - a framing-balance count that disagreed with the items present (CPV)
  - ten pillar summaries calling themselves the strongest or weakest pillar when
    the panel ranked them elsewhere
  - the same source listed under two citation ids (ERI)

Prose written against one year's numbers also goes silently wrong when the panel
is rebuilt, which is exactly the drift an automated check catches and a human
audit every fourth iteration does not.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location(
    "narrative_check", ROOT / "scripts" / "narrative_check.py")
narrative_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(narrative_check)

from asi.dashboard import data as D  # noqa: E402

check_consistency = narrative_check.check_consistency


@pytest.fixture(scope="module")
def panel():
    return D.load()


@pytest.fixture(scope="module")
def records():
    import yaml
    out = {}
    for p in sorted((ROOT / "narrative" / "countries").glob("*.yaml")):
        out[p.stem.upper()] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not out:
        pytest.skip("no corpus on disk")
    return out


def _errors(problems):
    return [p for p in problems if p.startswith("[error]")]


# ── The corpus itself ──────────────────────────────────────────────────────────

def test_shipped_corpus_has_no_consistency_errors(records, panel):
    """The audit that found ten false claims must stay at zero."""
    errs = _errors(check_consistency(records, panel))
    assert not errs, "consistency errors:\n" + "\n".join(errs)


# ── Framing balance ────────────────────────────────────────────────────────────

BASE = {
    "meta": {"iso3": "KEN"},
    "recent": {
        "primary": [{"sentiment": "positive"}, {"sentiment": "negative"},
                    {"sentiment": "negative"}],
        "extended": [{"sentiment": "mixed"}],
    },
    "balance": {"n_positive": 1, "n_negative": 2, "n_mixed": 1},
}


def test_balance_matching_the_items_passes(panel):
    assert not _errors(check_consistency({"KEN": BASE}, panel))


def test_balance_disagreeing_with_the_items_is_an_error(panel):
    """The exact defect found in the Cabo Verde record."""
    bad = {**BASE, "balance": {"n_positive": 1, "n_negative": 3, "n_mixed": 1}}
    errs = _errors(check_consistency({"KEN": bad}, panel))
    assert any("balance" in e for e in errs)


def test_balance_counts_extended_items_too(panel):
    bad = {**BASE, "balance": {"n_positive": 1, "n_negative": 2, "n_mixed": 0}}
    assert _errors(check_consistency({"KEN": bad}, panel))


# ── Pillar rank claims ─────────────────────────────────────────────────────────

def _with_pillar_summary(iso3, pillar, summary):
    return {iso3: {"meta": {"iso3": iso3},
                   "pillars": {pillar: {"summary": summary}}}}


def test_a_false_strongest_pillar_claim_is_an_error(panel):
    """Kenya's Pillar A is not its strongest; claiming so must fail."""
    order = narrative_check._pillar_ranking(panel, "KEN")
    loser = order[-1]
    rec = _with_pillar_summary("KEN", loser, "This is Kenya's strongest pillar.")
    errs = _errors(check_consistency(rec, panel))
    assert any("strongest" in e for e in errs)


def test_a_true_strongest_pillar_claim_passes(panel):
    order = narrative_check._pillar_ranking(panel, "KEN")
    rec = _with_pillar_summary("KEN", order[0], "This is Kenya's strongest pillar.")
    assert not _errors(check_consistency(rec, panel))


def test_a_true_weakest_pillar_claim_passes(panel):
    order = narrative_check._pillar_ranking(panel, "KEN")
    rec = _with_pillar_summary("KEN", order[-1], "This is Kenya's weakest pillar.")
    assert not _errors(check_consistency(rec, panel))


def test_second_strongest_is_not_read_as_strongest(panel):
    """'second-strongest' contains 'strongest'; the checker must not confuse them."""
    order = narrative_check._pillar_ranking(panel, "KEN")
    rec = _with_pillar_summary("KEN", order[1], "This is Kenya's second-strongest pillar.")
    assert not _errors(check_consistency(rec, panel))


def test_referring_to_another_pillars_score_is_not_a_self_claim(panel):
    """
    Cabo Verde's Pillar G cites Pillar A's score. That is a reference, not a
    claim that G is strongest, and must not be flagged.
    """
    order = narrative_check._pillar_ranking(panel, "KEN")
    rec = _with_pillar_summary(
        "KEN", order[-1],
        "Infrastructure consistent with the corpus's strongest Pillar A score.")
    assert not _errors(check_consistency(rec, panel))


# ── Citation linkage ───────────────────────────────────────────────────────────

def _warnings(problems):
    return [p for p in problems if p.startswith("[warning]")]


def test_duplicate_url_under_two_ids_warns(panel):
    """The exact defect found in the Eritrea record."""
    rec = {"KEN": {"meta": {"iso3": "KEN"}, "citations": [
        {"id": "c1", "url": "https://example.org/a"},
        {"id": "c2", "url": "https://example.org/a"},
    ], "historical": {"overview_citations": ["c1", "c2"]}}}
    assert any("same URL" in w for w in _warnings(check_consistency(rec, panel)))


def test_citation_attached_to_nothing_warns(panel):
    rec = {"KEN": {"meta": {"iso3": "KEN"},
                   "citations": [{"id": "c1", "url": "https://example.org/a"}]}}
    assert any("no claim" in w for w in _warnings(check_consistency(rec, panel)))


def test_url_used_but_not_listed_warns(panel):
    rec = {"KEN": {"meta": {"iso3": "KEN"}, "citations": [],
                   "recent": {"primary": [{"sentiment": "mixed",
                                           "news_url": "https://example.org/x"}]},
                   "balance": {"n_positive": 0, "n_negative": 0, "n_mixed": 1}}}
    assert any("absent from the citations block" in w
               for w in _warnings(check_consistency(rec, panel)))


def test_a_citation_reached_only_through_a_recent_item_is_not_an_orphan(panel):
    """Sources backing a news item are linked by URL, not by id. Still used."""
    rec = {"KEN": {"meta": {"iso3": "KEN"},
                   "citations": [{"id": "c1", "url": "https://example.org/x"}],
                   "recent": {"primary": [{"sentiment": "mixed",
                                           "news_url": "https://example.org/x"}]},
                   "balance": {"n_positive": 0, "n_negative": 0, "n_mixed": 1}}}
    assert not _warnings(check_consistency(rec, panel))
