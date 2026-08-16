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


# ── URL scheme allowlist ───────────────────────────────────────────────────────

def _record_with_citation_url(url):
    return {"meta": {"iso3": "KEN", "name": "Kenya", "last_updated": "2026-01-01",
                     "iteration_count": 1, "next_action": "x"},
            "citations": [{"id": "c1", "url": url, "source_type": "news"}]}


def test_a_javascript_url_is_rejected():
    """
    Citation URLs are rendered straight into href attributes, and React renders
    a javascript: href with a console warning rather than refusing it. The
    corpus is machine-authored across sessions, so this cannot rest on
    convention.
    """
    problems = validate(_record_with_citation_url("javascript:alert(1)"))
    assert any("must start with http" in p.message for p in problems)


def test_a_data_url_is_rejected():
    problems = validate(_record_with_citation_url("data:text/html,<script>1</script>"))
    assert any("must start with http" in p.message for p in problems)


def test_https_and_http_are_accepted():
    for url in ("https://example.org/a", "http://example.org/a"):
        problems = validate(_record_with_citation_url(url))
        assert not [p for p in problems if "must start with http" in p.message]


def test_event_and_recent_urls_are_checked_too():
    rec = _record_with_citation_url("https://example.org/a")
    rec["events"] = [{"year": 2020, "type": "coup", "direction": "mixed",
                      "url": "javascript:alert(1)"}]
    rec["recent"] = {"primary": [{"headline": "h", "date": "2025-01-01",
                                  "summary": "s", "why_it_matters": "w",
                                  "news_url": "javascript:alert(2)",
                                  "sentiment": "mixed"}]}
    msgs = [p.message for p in validate(rec) if "must start with http" in p.message]
    assert len(msgs) >= 2
