"""
asi.narrative.schema — the shape of a country's narrative record.

Every country gets the same structure, so the interface can render any country
without special cases and the audit pass can check any country against one
specification.

Why this is a schema and not a convention: the narrative layer is written by a
language model across many sessions. Left to convention it drifts — sections get
renamed, citations become optional, a country ends up with prose no one can
trace to a source. Validation is the only thing that makes an iterative,
model-written corpus auditable.

The rules encoded here come from the failure modes this project is specifically
exposed to (ASI v2 plan §9.3):

  - every factual claim carries a citation, because models produce plausible,
    well-formatted, nonexistent sources
  - recent items require a publication date, because training-cutoff knowledge
    otherwise masquerades as current news
  - each country records a framing balance count, because the training
    distribution over-represents conflict and failure in African coverage
  - narrative may not be written for a pillar the index itself greys out, or
    fluent prose would assert what the data refused to
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from asi.core.constants import PILLAR_DEFS


class Mode(str, Enum):
    """What a research run is allowed to do."""

    CREATE = "create"   # build the baseline record
    EXPAND = "expand"   # add depth, periods, sources
    AUDIT  = "audit"    # add nothing; verify and remove what does not hold


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED    = "mixed"


class SourceType(str, Enum):
    WIKIPEDIA = "wikipedia"
    NEWS      = "news"
    ACADEMIC  = "academic"
    OFFICIAL  = "official"     # government, UN, AU, World Bank


class EventType(str, Enum):
    COUP           = "coup"
    ELECTION       = "election"
    CONFLICT       = "conflict"
    PEACE_DEAL     = "peace_deal"
    CONSTITUTIONAL = "constitutional"
    ECONOMIC       = "economic"
    DISASTER       = "disaster"
    INDEPENDENCE   = "independence"


class Direction(str, Enum):
    IMPROVE     = "improve"
    DETERIORATE = "deteriorate"
    MIXED       = "mixed"


# ── Word budgets ───────────────────────────────────────────────────────────────
# Upper bounds matter more than lower ones: an unbounded model writes essays that
# nobody reads and that take an audit pass an hour per country to check.

LIMITS = {
    "historical_overview": (150, 300),
    "colonial_legacy":     (100, 250),
    "key_period_summary":  (40, 150),
    "pillar_summary":      (80, 160),
    "recent_summary":      (40, 120),
}

#: Recent-developments block: three shown by default, six more behind a control.
N_RECENT_PRIMARY  = 3
N_RECENT_EXTENDED = 6

#: An AUDIT run is forced when a single run inflates citations by more than this,
#: regardless of where the rotation sits. Rapid growth is when fabrication is
#: most likely and least visible.
AUDIT_CITATION_GROWTH_TRIGGER = 0.50

#: Rotation: create, expand, expand, then audit — and audit every fourth run
#: after that. An instruction document that updates itself trends toward "add
#: more detail" indefinitely; a scheduled adversarial pass is the counterweight.
AUDIT_EVERY = 4


def mode_for_iteration(n: int) -> Mode:
    """
    Which mode iteration `n` runs in (1-based).

        1 create · 2 expand · 3 expand · 4 audit · 5-7 expand · 8 audit · ...
    """
    if n <= 0:
        raise ValueError("iterations are 1-based")
    if n == 1:
        return Mode.CREATE
    if n % AUDIT_EVERY == 0:
        return Mode.AUDIT
    return Mode.EXPAND


# ── Validation ─────────────────────────────────────────────────────────────────

@dataclass(slots=True)
class Problem:
    """One validation failure, addressed to whoever must fix it."""

    country: str
    where: str
    message: str
    severity: str = "error"   # error | warning

    def __str__(self) -> str:
        return f"[{self.severity}] {self.country} · {self.where}: {self.message}"


def _words(text: str | None) -> int:
    return len((text or "").split())


def _check_length(country: str, where: str, text: str | None,
                  key: str, problems: list[Problem]) -> None:
    lo, hi = LIMITS[key]
    n = _words(text)
    if n == 0:
        problems.append(Problem(country, where, "empty"))
    elif n < lo:
        problems.append(Problem(country, where, f"{n} words, expected at least {lo}",
                                "warning"))
    elif n > hi:
        problems.append(Problem(country, where, f"{n} words, limit {hi}"))


def validate(record: dict[str, Any], *,
             greyed_pillars: set[str] | None = None) -> list[Problem]:
    """
    Check one country record against the blueprint.

    `greyed_pillars` are pillars the index itself will not show for this country
    at the reference year. Writing a confident paragraph about a pillar the data
    refused to score is the single most damaging thing this layer can do, so it
    is an error rather than a style note.
    """
    problems: list[Problem] = []
    iso3 = (record.get("meta") or {}).get("iso3", "???")
    greyed = greyed_pillars or set()

    # meta
    meta = record.get("meta") or {}
    for key in ("iso3", "name", "last_updated", "iteration_count", "next_action"):
        if not meta.get(key):
            problems.append(Problem(iso3, "meta", f"missing {key}"))

    # citations, indexed for lookup
    citations = {c.get("id"): c for c in (record.get("citations") or [])}
    if not citations:
        problems.append(Problem(iso3, "citations", "no citations at all"))
    for cid, c in citations.items():
        if not c.get("url"):
            problems.append(Problem(iso3, f"citation {cid}", "no url"))
        if c.get("source_type") not in {s.value for s in SourceType}:
            problems.append(Problem(iso3, f"citation {cid}",
                                    f"unknown source_type {c.get('source_type')!r}"))

    def check_refs(where: str, refs: list[str] | None) -> None:
        if not refs:
            problems.append(Problem(iso3, where, "no citation referenced"))
            return
        for r in refs:
            if r not in citations:
                problems.append(Problem(iso3, where, f"cites unknown id {r!r}"))

    # historical
    hist = record.get("historical") or {}
    _check_length(iso3, "historical.overview", hist.get("overview"),
                  "historical_overview", problems)
    _check_length(iso3, "historical.colonial_legacy", hist.get("colonial_legacy"),
                  "colonial_legacy", problems)
    check_refs("historical.overview", hist.get("overview_citations"))
    for i, period in enumerate(hist.get("key_periods") or []):
        where = f"historical.key_periods[{i}]"
        if not period.get("title"):
            problems.append(Problem(iso3, where, "no title"))
        _check_length(iso3, where, period.get("summary"), "key_period_summary", problems)
        check_refs(where, period.get("citations"))

    # pillars
    pillars = record.get("pillars") or {}
    for pid in PILLAR_DEFS:
        entry = pillars.get(pid)
        if pid in greyed:
            if entry and (entry.get("summary") or "").strip():
                problems.append(Problem(
                    iso3, f"pillars.{pid}",
                    "narrative written for a pillar the index greys out — the data "
                    "was judged too inferred to score, so prose about it asserts "
                    "more than the evidence supports"))
            continue
        if not entry:
            problems.append(Problem(iso3, f"pillars.{pid}", "missing", "warning"))
            continue
        _check_length(iso3, f"pillars.{pid}", entry.get("summary"),
                      "pillar_summary", problems)
        check_refs(f"pillars.{pid}", entry.get("citations"))

    # recent developments
    recent = record.get("recent") or {}
    primary = recent.get("primary") or []
    extended = recent.get("extended") or []
    if len(primary) != N_RECENT_PRIMARY:
        problems.append(Problem(iso3, "recent.primary",
                                f"{len(primary)} items, expected {N_RECENT_PRIMARY}"))
    if len(extended) > N_RECENT_EXTENDED:
        problems.append(Problem(iso3, "recent.extended",
                                f"{len(extended)} items, limit {N_RECENT_EXTENDED}"))
    for i, item in enumerate(primary + extended):
        where = f"recent[{i}]"
        if not item.get("headline"):
            problems.append(Problem(iso3, where, "no headline"))
        if not item.get("date"):
            problems.append(Problem(
                iso3, where,
                "no publication date — without one, model training data is "
                "indistinguishable from current reporting"))
        _check_length(iso3, where, item.get("summary"), "recent_summary", problems)
        if not item.get("news_url") and not item.get("wikipedia_url"):
            problems.append(Problem(iso3, where, "no source url"))
        if item.get("sentiment") not in {s.value for s in Sentiment}:
            problems.append(Problem(iso3, where,
                                    f"unknown sentiment {item.get('sentiment')!r}"))

    # events feeding the time slider
    for i, ev in enumerate(record.get("events") or []):
        where = f"events[{i}]"
        year = ev.get("year")
        if not isinstance(year, int):
            problems.append(Problem(iso3, where, "year must be an integer"))
        if ev.get("type") not in {t.value for t in EventType}:
            problems.append(Problem(iso3, where, f"unknown type {ev.get('type')!r}"))
        if ev.get("direction") not in {d.value for d in Direction}:
            problems.append(Problem(iso3, where, f"unknown direction {ev.get('direction')!r}"))
        if not ev.get("url"):
            problems.append(Problem(iso3, where, "no source url"))

    # framing balance
    balance = record.get("balance") or {}
    for key in ("n_positive", "n_negative", "n_mixed"):
        if key not in balance:
            problems.append(Problem(iso3, "balance", f"missing {key}"))
    if all(k in balance for k in ("n_positive", "n_negative")):
        pos, neg = balance["n_positive"], balance["n_negative"]
        if neg > 0 and pos == 0:
            problems.append(Problem(
                iso3, "balance",
                f"{neg} negative items and no positive ones. Where the evidence "
                f"supports it, documented gains belong alongside documented "
                f"failures; an all-negative record reproduces the framing bias "
                f"this project exists to avoid", "warning"))

    return problems


def blank_record(iso3: str, name: str) -> dict[str, Any]:
    """The empty shape a CREATE run fills in."""
    return {
        "meta": {
            "iso3": iso3, "name": name, "last_updated": None,
            "iteration_count": 0, "next_action": "create baseline from blueprint",
            "model_used": None,
        },
        "historical": {"overview": "", "overview_citations": [],
                       "colonial_legacy": "", "key_periods": []},
        "pillars": {p: {"summary": "", "drivers": [], "citations": []}
                    for p in PILLAR_DEFS},
        "recent": {"primary": [], "extended": []},
        "events": [],
        "citations": [],
        "balance": {"n_positive": 0, "n_negative": 0, "n_mixed": 0, "note": ""},
    }


__all__ = [
    "Mode", "Sentiment", "SourceType", "EventType", "Direction",
    "LIMITS", "N_RECENT_PRIMARY", "N_RECENT_EXTENDED",
    "AUDIT_EVERY", "AUDIT_CITATION_GROWTH_TRIGGER",
    "mode_for_iteration", "Problem", "validate", "blank_record",
]
