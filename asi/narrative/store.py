"""
asi.narrative.store — the interface's only door to the narrative corpus.

`schema.py` says what a record must contain and refuses to ship one that does
not. This module is the other half: it reads the validated records off disk and
hands the interface typed objects instead of nested dictionaries.

It follows the same rule `asi.dashboard.data` follows for the panel, for the
same reason:

    It resolves and shapes. It never writes prose, infers a fact, or upgrades a
    claim. Every string it returns was written by a research run and checked by
    scripts/narrative_check.py.

Three specific things it does rather than leave to the renderer:

  1. **Citation ids become citations.** Records store `[c1, c4]`; a reader needs
     titles and URLs. Resolving that in one place means a dangling id surfaces
     as a missing source everywhere at once instead of crashing one view.

  2. **Events are split by whether the panel can show them.** 130 of the
     corpus's 213 events predate the panel's first year. An event the slider
     cannot reach is still real history, so it is kept and labelled — but it is
     not offered as a slider tick, because a tick that cannot be clicked is a
     broken promise rather than a feature.

  3. **Audit status is derived from the rotation, not from the `verified`
     flags.** A citation's `verified` field is only meaningful once an AUDIT run
     has opened it (narrative/prompts/RESEARCH.md), and AUDIT lands on iteration
     4. Reading the flags alone would let a corpus that has never been audited
     present itself as fully verified, which is precisely the overstatement this
     project exists to refuse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml

from asi.core.constants import PROJECT_ROOT
from asi.narrative.schema import Mode, mode_for_iteration

CORPUS_DIR = PROJECT_ROOT / "narrative" / "countries"

#: Sentiment and direction vocabularies, kept here so the renderer never
#: invents a category the schema does not allow.
SENTIMENTS = ("positive", "negative", "mixed")
DIRECTIONS = ("improve", "deteriorate", "mixed")


# ── Pieces ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class Citation:
    id: str
    url: str
    source_type: str
    title: str
    accessed: str
    verified: bool

    @property
    def domain(self) -> str:
        """Host only — what a reader scans to judge a source at a glance."""
        u = self.url.split("://", 1)[-1]
        return u.split("/", 1)[0].removeprefix("www.")


@dataclass(frozen=True, slots=True)
class KeyPeriod:
    title: str
    period: str
    summary: str
    citations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PillarNarrative:
    pillar_id: str
    summary: str
    drivers: tuple[str, ...]
    citations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecentItem:
    headline: str
    date: str
    summary: str
    why_it_matters: str
    news_url: str
    wikipedia_url: str
    sentiment: str

    @property
    def year(self) -> int | None:
        try:
            return int(str(self.date)[:4])
        except (TypeError, ValueError):
            return None


@dataclass(frozen=True, slots=True)
class Event:
    year: int
    type: str
    title: str
    description: str
    url: str
    direction: str


@dataclass(frozen=True, slots=True)
class RECMembership:
    org: str
    joined: int | None
    status: str
    left: int | None
    citations: tuple[str, ...]

    @property
    def span(self) -> str:
        """'1975–' or '1967–1977' — the shape a reader can read without a key."""
        start = str(self.joined) if self.joined else "?"
        if self.status == "withdrawn" and self.left:
            return f"{start}–{self.left}"
        return f"{start}–"


@dataclass(frozen=True, slots=True)
class Balance:
    n_positive: int
    n_negative: int
    n_mixed: int
    note: str

    @property
    def total(self) -> int:
        return self.n_positive + self.n_negative + self.n_mixed


# ── Record ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class NarrativeRecord:
    """One country's validated narrative record, resolved for rendering."""

    iso3: str
    name: str
    last_updated: str
    iteration_count: int
    next_action: str
    model_used: str

    overview: str
    overview_citations: tuple[str, ...]
    colonial_legacy: str
    colonial_legacy_citations: tuple[str, ...]
    key_periods: tuple[KeyPeriod, ...]

    pillars: dict[str, PillarNarrative]
    recent_primary: tuple[RecentItem, ...]
    recent_extended: tuple[RecentItem, ...]
    events: tuple[Event, ...]
    citations: dict[str, Citation]
    rec_membership: tuple[RECMembership, ...]
    balance: Balance | None

    # ── citations ──
    def cite(self, ids: Iterable[str]) -> list[Citation]:
        """
        Resolve citation ids, silently skipping ids with no citation.

        Skipping rather than raising is deliberate: `narrative_check.py` already
        fails a record with a dangling reference, so by the time the interface
        runs, a missing id means the corpus on disk is older than the code. A
        reader is better served by the sources that do resolve than by a stack
        trace.
        """
        out = []
        for cid in ids or ():
            c = self.citations.get(cid)
            if c is not None:
                out.append(c)
        return out

    @property
    def sources_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for c in self.citations.values():
            counts[c.source_type] = counts.get(c.source_type, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: -kv[1]))

    # ── provenance ──
    @property
    def times_audited(self) -> int:
        """How many completed runs were AUDIT runs."""
        return sum(1 for n in range(1, max(self.iteration_count, 0) + 1)
                   if mode_for_iteration(n) is Mode.AUDIT)

    @property
    def audited(self) -> bool:
        return self.times_audited > 0

    @property
    def next_mode(self) -> Mode:
        return mode_for_iteration(self.iteration_count + 1)

    @property
    def provenance_note(self) -> str:
        """
        What the reader is entitled to conclude about these sources.

        A record's citations carry a `verified` flag, but that flag only means
        something once an AUDIT run has actually opened the page. Saying so is
        the difference between reporting provenance and implying an assurance
        nobody has performed.
        """
        n = len(self.citations)
        if self.audited:
            opened = sum(1 for c in self.citations.values() if c.verified)
            return (f"{opened} of {n} sources opened and confirmed by an audit pass "
                    f"({self.times_audited} run{'s' if self.times_audited > 1 else ''}).")
        return (f"{n} sources cited, collected during research and machine-checked "
                f"for reachability. No audit pass has re-opened them yet, so they "
                f"are shown as cited rather than as confirmed.")

    # ── events ──
    def events_in(self, start: int, end: int) -> list[Event]:
        """Events the panel's own year range can actually reach."""
        return [e for e in self.events if start <= e.year <= end]

    def events_outside(self, start: int, end: int) -> list[Event]:
        return [e for e in self.events if not (start <= e.year <= end)]

    def event_years(self, start: int, end: int) -> dict[int, list[Event]]:
        """In-panel events grouped by year — one slider tick may cover several."""
        out: dict[int, list[Event]] = {}
        for e in self.events_in(start, end):
            out.setdefault(e.year, []).append(e)
        return dict(sorted(out.items()))

    def pillar(self, pillar_id: str) -> PillarNarrative | None:
        return self.pillars.get(pillar_id)

    @property
    def all_recent(self) -> tuple[RecentItem, ...]:
        return self.recent_primary + self.recent_extended


# ── Parsing ────────────────────────────────────────────────────────────────────

def _tuple(v) -> tuple[str, ...]:
    if not v:
        return ()
    if isinstance(v, str):
        return (v,)
    return tuple(str(x) for x in v)


def _int_or_none(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def parse(raw: dict) -> NarrativeRecord:
    """Turn one validated YAML mapping into a record. Pure; no I/O."""
    meta = raw.get("meta") or {}
    hist = raw.get("historical") or {}
    recent = raw.get("recent") or {}
    bal = raw.get("balance") or {}

    citations = {}
    for c in raw.get("citations") or []:
        cid = str(c.get("id", ""))
        if not cid:
            continue
        citations[cid] = Citation(
            id=cid,
            url=str(c.get("url", "")),
            source_type=str(c.get("source_type", "")),
            title=str(c.get("title", "")),
            accessed=str(c.get("accessed", "")),
            verified=bool(c.get("verified", False)),
        )

    pillars = {}
    for pid, p in (raw.get("pillars") or {}).items():
        p = p or {}
        pillars[str(pid)] = PillarNarrative(
            pillar_id=str(pid),
            summary=(p.get("summary") or "").strip(),
            drivers=_tuple(p.get("drivers")),
            citations=_tuple(p.get("citations")),
        )

    def _items(key: str) -> tuple[RecentItem, ...]:
        return tuple(
            RecentItem(
                headline=(i.get("headline") or "").strip(),
                date=str(i.get("date", "")),
                summary=(i.get("summary") or "").strip(),
                why_it_matters=(i.get("why_it_matters") or "").strip(),
                news_url=str(i.get("news_url") or ""),
                wikipedia_url=str(i.get("wikipedia_url") or ""),
                sentiment=str(i.get("sentiment") or "mixed"),
            )
            for i in (recent.get(key) or [])
        )

    return NarrativeRecord(
        iso3=str(meta.get("iso3", "")),
        name=str(meta.get("name", "")),
        last_updated=str(meta.get("last_updated", "")),
        iteration_count=int(meta.get("iteration_count", 0) or 0),
        next_action=(meta.get("next_action") or "").strip(),
        model_used=str(meta.get("model_used", "")),
        overview=(hist.get("overview") or "").strip(),
        overview_citations=_tuple(hist.get("overview_citations")),
        colonial_legacy=(hist.get("colonial_legacy") or "").strip(),
        colonial_legacy_citations=_tuple(hist.get("colonial_legacy_citations")),
        key_periods=tuple(
            KeyPeriod(
                title=(k.get("title") or "").strip(),
                period=str(k.get("period", "")),
                summary=(k.get("summary") or "").strip(),
                citations=_tuple(k.get("citations")),
            )
            for k in (hist.get("key_periods") or [])
        ),
        pillars=pillars,
        recent_primary=_items("primary"),
        recent_extended=_items("extended"),
        events=tuple(
            sorted(
                (
                    Event(
                        year=int(e.get("year", 0) or 0),
                        type=str(e.get("type", "")),
                        title=(e.get("title") or "").strip(),
                        description=(e.get("description") or "").strip(),
                        url=str(e.get("url") or ""),
                        direction=str(e.get("direction") or "mixed"),
                    )
                    for e in (raw.get("events") or [])
                ),
                key=lambda e: e.year,
            )
        ),
        citations=citations,
        rec_membership=tuple(
            RECMembership(
                org=str(m.get("org", "")),
                joined=_int_or_none(m.get("joined")),
                status=str(m.get("status") or "current"),
                left=_int_or_none(m.get("left")),
                citations=_tuple(m.get("citations")),
            )
            for m in (raw.get("rec_membership") or [])
        ),
        balance=Balance(
            n_positive=int(bal.get("n_positive", 0) or 0),
            n_negative=int(bal.get("n_negative", 0) or 0),
            n_mixed=int(bal.get("n_mixed", 0) or 0),
            note=(bal.get("note") or "").strip(),
        ) if bal else None,
    )


def load_corpus(corpus_dir: Path | None = None) -> dict[str, NarrativeRecord]:
    """
    Load every record on disk, keyed by ISO3.

    An absent or empty corpus returns `{}` rather than raising. The narrative
    layer enriches the index; it is not required to run it, and a deployment
    without the corpus should still serve the numbers rather than fail to start.
    """
    d = Path(corpus_dir or CORPUS_DIR)
    if not d.exists():
        return {}
    out: dict[str, NarrativeRecord] = {}
    for path in sorted(d.glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            # A record that will not parse is reported by narrative_check.py.
            # Skipping it here keeps one broken file from taking down 53 good ones.
            continue
        rec = parse(raw)
        key = rec.iso3 or path.stem.upper()
        out[key] = rec
    return out


__all__ = [
    "Citation", "KeyPeriod", "PillarNarrative", "RecentItem", "Event",
    "RECMembership", "Balance", "NarrativeRecord",
    "parse", "load_corpus", "CORPUS_DIR", "SENTIMENTS", "DIRECTIONS",
]
