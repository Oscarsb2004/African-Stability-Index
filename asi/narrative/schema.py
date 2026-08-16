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

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from asi.core.constants import PILLAR_DEFS
from asi.core.countries import COUNTRIES


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


class REC(str, Enum):
    """AU-recognised Regional Economic Communities, matching asi.core.countries."""

    UMA     = "UMA"
    CEN_SAD = "CEN-SAD"
    COMESA  = "COMESA"
    EAC     = "EAC"
    ECCAS   = "ECCAS"
    ECOWAS  = "ECOWAS"
    IGAD    = "IGAD"
    SADC    = "SADC"


class RECStatus(str, Enum):
    CURRENT   = "current"
    WITHDRAWN = "withdrawn"


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

#: Reserved citation id: the index's own panel.
#:
#: Most pillar summaries are index output — a score, a coverage count, a tier —
#: which rest on data/panel and are verified by verify/panel.py, not by any URL.
#: Requiring a URL anyway produced 71 pillars citing the country's general
#: history article as filler, which could not support anything in them.
#:
#: A pillar may therefore cite `panel` for what the index measured. It may not
#: use it to cover anything else: a summary that reaches outside the index —
#: an event, an actor, a year other than the reference year — still needs a real
#: source. Outside context is encouraged; uncited outside context is not.
PANEL_CITATION = "panel"

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


#: Schemes a citation URL may use.
#:
#: These strings are rendered straight into `href` attributes by
#: asi/dashboard/narrative_ui.py, and React renders a `javascript:` href with
#: only a console warning rather than refusing it. The corpus is written by a
#: language model across many sessions, which is exactly the condition under
#: which a convention-only guarantee decays — this file exists because that has
#: already happened once with the `verified` flags.
URL_SCHEMES = ("http://", "https://")


def _check_url(country: str, where: str, url, problems: list["Problem"]) -> None:
    """A URL that will become an href must be http(s) or absent."""
    if not url:
        return
    if not str(url).startswith(URL_SCHEMES):
        problems.append(Problem(
            country, where,
            f"url must start with http:// or https:// — got {str(url)[:40]!r}"))


def validate(record: dict[str, Any], *,
             greyed_pillars: set[str] | None = None,
             reference_year: int | None = None) -> list[Problem]:
    """
    Check one country record against the blueprint.

    `greyed_pillars` are pillars the index itself will not show for this country
    at the reference year. Writing a confident paragraph about a pillar the data
    refused to score is the single most damaging thing this layer can do, so it
    is an error rather than a style note.

    `reference_year` enables the rule that a pillar citing only the index may not
    reach outside the year the index measures. Omit it and that check is skipped,
    so callers without a panel to hand still get every structural check.
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
        _check_url(iso3, f"citation {cid}", c.get("url"), problems)
        if c.get("source_type") not in {s.value for s in SourceType}:
            problems.append(Problem(iso3, f"citation {cid}",
                                    f"unknown source_type {c.get('source_type')!r}"))

    def check_refs(where: str, refs: list[str] | None,
                   *, panel_allowed: bool = False) -> None:
        if not refs:
            problems.append(Problem(iso3, where, "no citation referenced"))
            return
        for r in refs:
            if r == PANEL_CITATION:
                if not panel_allowed:
                    problems.append(Problem(
                        iso3, where,
                        f"cites {PANEL_CITATION!r}, which only pillar summaries may "
                        f"do — prose outside the pillars is not index output"))
                continue
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
        summary = entry.get("summary") or ""
        _check_length(iso3, f"pillars.{pid}", summary, "pillar_summary", problems)
        refs = entry.get("citations")
        check_refs(f"pillars.{pid}", refs, panel_allowed=True)

        # Outside context is encouraged, but it has to be sourced. A summary
        # that cites nothing but the index while discussing a year the index
        # does not cover is asserting something the panel cannot support.
        if reference_year is not None and refs:
            outside = [r for r in refs if r != PANEL_CITATION]
            if not outside:
                years = {int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", summary)}
                beyond = sorted(years - {reference_year})
                if beyond:
                    problems.append(Problem(
                        iso3, f"pillars.{pid}",
                        f"cites only {PANEL_CITATION!r} but refers to "
                        f"{', '.join(str(y) for y in beyond)} — the index measures "
                        f"{reference_year}, so a claim reaching beyond it needs a "
                        f"real source"))

    # REC (Regional Economic Community) membership
    rec_membership = record.get("rec_membership")
    if not rec_membership:
        problems.append(Problem(
            iso3, "rec_membership",
            "missing — every AU member belongs to at least one REC; see "
            "asi.core.countries.COUNTRIES[iso3]['rec'] for current membership",
            "warning"))
    else:
        valid_orgs = {r.value for r in REC}
        valid_status = {s.value for s in RECStatus}
        seen_current: set[str] = set()
        for i, entry in enumerate(rec_membership):
            where = f"rec_membership[{i}]"
            org = entry.get("org")
            if org not in valid_orgs:
                problems.append(Problem(iso3, where, f"unknown org {org!r}"))
            if not isinstance(entry.get("joined"), int):
                problems.append(Problem(iso3, where, "joined must be an integer year"))
            status = entry.get("status", RECStatus.CURRENT.value)
            if status not in valid_status:
                problems.append(Problem(iso3, where, f"unknown status {status!r}"))
            if status == RECStatus.WITHDRAWN.value and not entry.get("left"):
                problems.append(Problem(iso3, where,
                                        "status is withdrawn but no left year given"))
            check_refs(where, entry.get("citations"))
            if status == RECStatus.CURRENT.value and org in valid_orgs:
                seen_current.add(org)
        expected = set((COUNTRIES.get(iso3) or {}).get("rec") or [])
        if expected and seen_current != expected:
            missing = expected - seen_current
            extra = seen_current - expected
            detail = []
            if missing:
                detail.append(f"missing {sorted(missing)}")
            if extra:
                detail.append(f"not in the index's current list: {sorted(extra)}")
            problems.append(Problem(
                iso3, "rec_membership",
                "doesn't match asi.core.countries.COUNTRIES[iso3]['rec'] — "
                + "; ".join(detail), "warning"))

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
        _check_url(iso3, f"{where}.news_url", item.get("news_url"), problems)
        _check_url(iso3, f"{where}.wikipedia_url", item.get("wikipedia_url"), problems)
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
        _check_url(iso3, where, ev.get("url"), problems)

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
        "rec_membership": [],
        "recent": {"primary": [], "extended": []},
        "events": [],
        "citations": [],
        "balance": {"n_positive": 0, "n_negative": 0, "n_mixed": 0, "note": ""},
    }


__all__ = [
    "Mode", "Sentiment", "SourceType", "EventType", "Direction",
    "REC", "RECStatus",
    "LIMITS", "N_RECENT_PRIMARY", "N_RECENT_EXTENDED", "URL_SCHEMES",
    "AUDIT_EVERY", "AUDIT_CITATION_GROWTH_TRIGGER",
    "mode_for_iteration", "Problem", "validate", "blank_record",
]
