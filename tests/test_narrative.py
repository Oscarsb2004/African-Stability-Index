"""
Narrative schema: the rotation and the rules that keep a model-written corpus
auditable.
"""

import pytest

from asi.narrative.schema import (
    Mode, mode_for_iteration, validate, blank_record, AUDIT_EVERY,
)


# ── Rotation ───────────────────────────────────────────────────────────────────

def test_first_run_creates():
    assert mode_for_iteration(1) is Mode.CREATE


def test_audit_lands_every_fourth_run():
    assert mode_for_iteration(4) is Mode.AUDIT
    assert mode_for_iteration(8) is Mode.AUDIT
    assert mode_for_iteration(12) is Mode.AUDIT


def test_non_audit_runs_expand():
    for n in (2, 3, 5, 6, 7, 9):
        assert mode_for_iteration(n) is Mode.EXPAND


def test_audit_is_frequent_enough_to_matter():
    """A loop that only ever adds needs the counterweight often enough to bite."""
    assert AUDIT_EVERY <= 4


def test_iterations_are_one_based():
    with pytest.raises(ValueError):
        mode_for_iteration(0)


# ── Validation ─────────────────────────────────────────────────────────────────

def test_blank_record_is_not_valid():
    """The empty shape is a starting point, not a publishable record."""
    problems = validate(blank_record("TCD", "Chad"))
    assert any(p.severity == "error" for p in problems)


def test_greyed_pillar_must_not_be_written_about():
    rec = blank_record("TCD", "Chad")
    rec["pillars"]["C"]["summary"] = "Social outcomes have improved markedly."
    problems = validate(rec, greyed_pillars={"C"})
    assert any("greys out" in p.message for p in problems), \
        "prose about a pillar the index refused to score must be rejected"


def test_greyed_pillar_left_empty_is_accepted():
    rec = blank_record("TCD", "Chad")
    problems = validate(rec, greyed_pillars={"C"})
    assert not any(p.where == "pillars.C" for p in problems)


def test_recent_item_without_a_date_is_an_error():
    rec = blank_record("TCD", "Chad")
    rec["recent"]["primary"] = [
        {"headline": "x", "summary": "y " * 50, "news_url": "http://e.com",
         "sentiment": "mixed"}
    ] * 3
    problems = validate(rec)
    assert any("publication date" in p.message for p in problems)


def test_all_negative_framing_is_flagged():
    rec = blank_record("TCD", "Chad")
    rec["balance"] = {"n_positive": 0, "n_negative": 6, "n_mixed": 0, "note": ""}
    problems = validate(rec)
    assert any("framing bias" in p.message for p in problems)


def test_citation_reference_must_exist():
    rec = blank_record("TCD", "Chad")
    rec["citations"] = [{"id": "c1", "url": "http://e.com", "source_type": "news"}]
    rec["historical"]["overview_citations"] = ["c9"]
    problems = validate(rec)
    assert any("unknown id" in p.message for p in problems)
