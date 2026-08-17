"""
verify/narrative.py — independent verification of the narrative corpus.

Gates a release on the claims that are arithmetic, reports on the ones that are
judgement.

Why this exists as a verification layer rather than only as a script:

    `scripts/narrative_check.py` validates records, but it imports
    `asi.narrative.schema` and `asi.results` — the exact dependency this
    package was created to avoid. If `asi.results` mis-filtered
    reliability, the rule "no prose for a greyed pillar" would be checked
    against a wrong idea of which pillars are greyed, and the check would agree
    with the bug. Half the project was also outside `verify/run.py` entirely, so
    a release could pass verification with a corpus full of false claims.

Independence measures taken here, matching verify/panel.py's discipline:

  - records are re-read from `narrative/countries/*.yaml` with plain `yaml`
  - pillar scores are re-read from `data/panel/pillar_scores.csv` with plain
    `pandas`, and the reliability rule is re-stated here rather than imported
  - nothing in this file imports the `asi` package

What gates, and why the split matters: a false factual claim is arithmetic —
a summary saying it is the country's strongest pillar when the panel ranks it
fourth is wrong the way a sum is wrong, and it gates. Whether a source list is
tidy, or how current "recent" should be, is judgement; those report and never
block, on the same reasoning verify/advisory.py gives — failing a build over a
judgement call only trains people to ignore the gate.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parent.parent
CORPUS_DIR = REPO / "narrative" / "countries"
PANEL_DIR = REPO / "data" / "panel"

#: Re-stated, not imported: the tiers whose scores the index is willing to show.
DISPLAYABLE = ("reliable", "thin")

#: Re-stated, not imported: AUDIT lands on iteration 4 and every 4th after.
AUDIT_EVERY = 4

#: Re-stated, not imported: the reserved citation id meaning "the index's own
#: panel". A pillar summary that is pure index output rests on data/panel, which
#: verify/panel.py re-derives independently — so it has a verified source, just
#: not a URL. It may not stand in for a claim reaching outside the index.
PANEL_CITATION = "panel"

NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4,
                "five": 5, "six": 6, "seven": 7, "eight": 8}

RANK_CLAIMS = [
    ("second-strongest", re.compile(r"second-strongest (?:single )?pillar"), 2),
    ("second-weakest",   re.compile(r"second-weakest (?:single )?pillar"), -2),
    ("strongest",        re.compile(r"(?<!second-)\bstrongest (?:single )?pillar"), 1),
    ("weakest",          re.compile(r"(?<!second-)\bweakest (?:single )?pillar"), -1),
]

COVERAGE_CLAIM = re.compile(
    r"(?:only\s+)?(?P<n>one|two|three|four|five|six|seven|eight|\d)\s+of\s+"
    r"(?:the\s+pillar's\s+|its\s+|this\s+pillar's\s+)?"
    r"(?P<total>one|two|three|four|five|six|seven|eight|\d)\s+indicators?\s+"
    r"(?:are|is)\s+(?!not\b)(?:current|fresh|freshly measured|directly measured|measured)",
    re.I,
)


def _spelled(token: str) -> int | None:
    token = token.strip().lower()
    return int(token) if token.isdigit() else NUMBER_WORDS.get(token)


# ── Independent reads ──────────────────────────────────────────────────────────

def load_records() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(CORPUS_DIR.glob("*.yaml")):
        out[path.stem.upper()] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return out


def load_pillar_scores() -> tuple[pd.DataFrame, int]:
    """Re-read the panel's pillar scores without going through asi.dashboard."""
    scores = pd.read_csv(PANEL_DIR / "pillar_scores.csv")
    import json
    meta = json.loads((PANEL_DIR / "bundle.json").read_text(encoding="utf-8"))
    return scores, int(meta["run"]["reference_year"])


#: Indicator phrases as prose writes them, mapped to the display-name prefix the
#: panel publishes. Prefixes must be unambiguous: matching "intentional
#: homicide" loosely also hits the female-specific series, which silently
#: compared the wrong number the first time this was attempted.
INDICATOR_PHRASES = {
    "electricity access": "Access to electricity",
    "access to electricity": "Access to electricity",
    "basic drinking water": "People using at least basic drinking water",
    "safely managed drinking water": "People using safely managed drinking water",
    "handwashing-facility access": "People with basic handwashing",
    "handwashing": "People with basic handwashing",
    "social protection": "Coverage of social protection",
    "life expectancy": "Life expectancy at birth",
    "infant mortality": "Mortality rate, infant",
    "severe food insecurity": "Prevalence of severe food insecurity",
    "agricultural land": "Agricultural land",
    "freshwater withdrawal": "Annual freshwater withdrawals",
    "gdp per capita": "GDP per capita",
    "domestic credit": "Domestic credit to private sector",
    "gini": "Gini index",
    "intentional homicide": "Intentional homicides (per",
    "displaced persons": "Internally displaced persons",
}

HEDGE = (r"(just over|just under|slightly over|slightly under|a little over|"
         r"more than|less than|over|under|above|below|nearly|almost|roughly|"
         r"about|around|just|only)")
_QUOTED = re.compile(
    rf"^[^.]{{0,14}}?\b(?:at|of)?\s*(?:{HEDGE}\s+)?([\d][\d,]*\.?\d*)\s?(?:%|per|years)",
    re.I)


def _hedge_holds(hedge: str | None, claimed: float, actual: float) -> bool:
    """
    Whether a rounded, hedged figure is still true of the measured value.

    The corpus rounds constantly and hedges when it does — "just under 60%" for
    59.2, "roughly 21" for 21.3. That is good prose, not error, so comparing the
    numbers directly flags 19 correct sentences. What is checkable is the
    *direction*: "over 40%" is false if the value is 38, and would become false
    silently the next time the panel is rebuilt.
    """
    h = (hedge or "").lower()
    if h in ("over", "above", "more than", "just over", "slightly over", "a little over"):
        return actual > claimed
    if h in ("under", "below", "less than", "just under", "slightly under"):
        return actual < claimed
    if h in ("nearly", "almost"):
        return claimed * 0.90 <= actual < claimed * 1.02
    if h in ("roughly", "about", "around"):
        return abs(actual - claimed) <= max(1.0, claimed * 0.06)
    return abs(round(actual) - claimed) < 0.51


def load_observations() -> pd.DataFrame:
    return pd.read_csv(PANEL_DIR / "observations.csv")


def check_quoted_values(records: dict[str, dict], observations: pd.DataFrame,
                        year: int) -> list[str]:
    """Indicator values quoted in pillar prose, against what the panel measured."""
    problems: list[str] = []
    at_year = observations[observations["year"] == year]

    for iso3, rec in sorted(records.items()):
        rows = at_year[at_year["iso3"] == iso3]
        values = {str(r.display_name): r.raw_value for r in rows.itertuples()}

        def measured(prefix: str):
            hits = [v for k, v in values.items() if k.startswith(prefix)]
            return hits[0] if len(hits) == 1 else None

        for pid, p in (rec.get("pillars") or {}).items():
            text = ((p or {}).get("summary") or "")
            for phrase, prefix in INDICATOR_PHRASES.items():
                for m in re.finditer(re.escape(phrase), text, re.I):
                    tail = text[m.end():m.end() + 34]
                    # a clause naming another indicator carries another number;
                    # reading across one produced 17 false positives
                    if " and " in tail:
                        continue
                    if any(k in tail.lower() for k in INDICATOR_PHRASES if k != phrase):
                        continue
                    nm = _QUOTED.match(tail)
                    if not nm:
                        continue
                    actual = measured(prefix)
                    if actual is None or actual != actual:
                        continue
                    try:
                        claimed = float(nm.group(2).replace(",", ""))
                    except (TypeError, ValueError):
                        continue
                    if not _hedge_holds(nm.group(1), claimed, float(actual)):
                        problems.append(
                            f"[error] {iso3} · pillars.{pid}: says "
                            f"{(nm.group(1) or '').strip()} {claimed:g} for "
                            f"{phrase}, but the panel measured "
                            f"{float(actual):.2f} at {year}.")
    return problems


def load_country_names() -> dict[str, str]:
    """
    Display names straight from the published bundle.

    Read here rather than imported from `asi.core.countries` for the same reason
    as everything else in this file: the point is to check the corpus against
    what the project actually publishes, not against the module the interface
    happens to import.
    """
    import json
    meta = json.loads((PANEL_DIR / "bundle.json").read_text(encoding="utf-8"))
    return {iso3: c.get("name", iso3) for iso3, c in meta["countries"].items()}


# ── Gating checks ──────────────────────────────────────────────────────────────

def check_claims(records: dict[str, dict], scores: pd.DataFrame,
                 year: int) -> list[str]:
    """Factual claims a record makes about itself, against the panel."""
    problems: list[str] = []
    at_year = scores[scores["year"] == year]
    shown = at_year[at_year["reliability"].isin(DISPLAYABLE) & at_year["score"].notna()]

    for iso3, rec in sorted(records.items()):
        pillars = rec.get("pillars") or {}
        mine = shown[shown["iso3"] == iso3].sort_values("score", ascending=False)
        order = list(mine["pillar_id"])
        counts = {r.pillar_id: (int(r.n_observed), int(r.n_indicators))
                  for r in at_year[at_year["iso3"] == iso3].itertuples()}

        # a pillar the index refuses to score must carry no prose
        greyed = set(at_year[(at_year["iso3"] == iso3)]["pillar_id"]) - set(order)
        for pid in sorted(greyed & set(pillars)):
            problems.append(
                f"[error] {iso3} · pillars.{pid}: prose written for a pillar the "
                f"index does not score at {year}.")

        for pid, p in pillars.items():
            summary = ((p or {}).get("summary") or "")

            for sentence in re.split(r"(?<=\.)\s+", summary.lower()):
                if re.search(r"pillar [a-g](?:'s)? (?:score|own)", sentence):
                    continue
                for label, pattern, target in RANK_CLAIMS:
                    if not pattern.search(sentence) or abs(target) > len(order):
                        continue
                    want = order[target - 1] if target > 0 else order[target]
                    if pid != want:
                        pos = order.index(pid) + 1 if pid in order else "unscored"
                        problems.append(
                            f"[error] {iso3} · pillars.{pid}: claims to be the "
                            f"{label} pillar, but ranks {pos} of {len(order)} "
                            f"at {year} — {want} is.")
                    break

            if pid in counts:
                n_obs, n_ind = counts[pid]
                for m in COVERAGE_CLAIM.finditer(summary):
                    claimed, total = _spelled(m.group("n")), _spelled(m.group("total"))
                    if claimed is None or total != n_ind:
                        continue
                    if claimed != n_obs:
                        problems.append(
                            f"[error] {iso3} · pillars.{pid}: says "
                            f"{m.group(0).strip()!r}, but the panel measured "
                            f"{n_obs} of {n_ind} at {year}.")
    return problems


def check_indicator_phrases(observations: pd.DataFrame, year: int) -> list[str]:
    """
    Every prefix in INDICATOR_PHRASES must still match exactly one indicator.

    `check_quoted_values` compares a number in prose against the panel by
    resolving a phrase to a `display_name` prefix, and its `measured()` helper
    returns None whenever a prefix matches zero or more than one series. That is
    the right behaviour for a single lookup and the wrong thing to leave
    unwatched: a display-name edit in the registry silently turns the check off
    for that indicator, and the corpus keeps passing while nothing is comparing
    its figures any more.

    The failure is invisible from the outside — quoted-value checking reports
    "no errors" either way. So the mapping itself is verified rather than
    assumed. Both directions matter: a prefix that matches nothing has gone
    stale, and one that matches several has become ambiguous, which is how
    "intentional homicide" once compared prose against the female-specific
    series instead.
    """
    problems: list[str] = []
    names = set(observations[observations["year"] == year]["display_name"]
                .dropna().astype(str))
    if not names:
        return [f"[warning] no observations at {year}; indicator phrases unchecked"]

    for phrase, prefix in sorted(INDICATOR_PHRASES.items()):
        hits = sorted(n for n in names if n.startswith(prefix))
        if len(hits) == 1:
            continue
        if not hits:
            problems.append(
                f"[error] INDICATOR_PHRASES: {phrase!r} -> {prefix!r} matches no "
                f"published display_name. The quoted-value check is silently "
                f"disabled for this indicator.")
        else:
            problems.append(
                f"[error] INDICATOR_PHRASES: {phrase!r} -> {prefix!r} matches "
                f"{len(hits)} series ({', '.join(hits)}). An ambiguous prefix "
                f"compares prose against whichever one sorts first.")
    return problems


def check_panel_citations(records: dict[str, dict], year: int) -> list[str]:
    """
    The index may stand as a pillar's source, but only for what the index says.

    Outside context is encouraged in a pillar summary; uncited outside context is
    not. A summary citing nothing but `panel` while discussing a year the panel
    does not cover is asserting something its stated source cannot support.
    """
    problems: list[str] = []
    for iso3, rec in sorted(records.items()):
        for pid, p in (rec.get("pillars") or {}).items():
            refs = list(((p or {}).get("citations") or []))
            if not refs or any(r != PANEL_CITATION for r in refs):
                continue
            summary = ((p or {}).get("summary") or "")
            beyond = sorted({int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", summary)}
                            - {year})
            if beyond:
                problems.append(
                    f"[error] {iso3} · pillars.{pid}: cites only the index but "
                    f"refers to {', '.join(str(y) for y in beyond)}; the panel "
                    f"measures {year}, so that claim needs a real source.")
    return problems


def _citation_links(rec: dict) -> tuple[dict[str, dict], set[str], set[str]]:
    """
    A record's citations, the ids its prose refers to, and the URLs it links to.

    Shared by the linkage check and the advisory summary so the two cannot drift
    apart — which is what happened to the two validators this function is part
    of collapsing.
    """
    cites = {str(c.get("id")): c for c in (rec.get("citations") or []) if c.get("id")}

    hist = rec.get("historical") or {}
    used: set[str] = set(hist.get("overview_citations") or [])
    used |= set(hist.get("colonial_legacy_citations") or [])
    for k in hist.get("key_periods") or []:
        used |= set(k.get("citations") or [])
    for p in (rec.get("pillars") or {}).values():
        used |= set((p or {}).get("citations") or [])
    for m in rec.get("rec_membership") or []:
        used |= set(m.get("citations") or [])

    recent = rec.get("recent") or {}
    items = list(recent.get("primary") or []) + list(recent.get("extended") or [])
    linked = {u for i in items
              for u in (i.get("news_url"), i.get("wikipedia_url")) if u}
    linked |= {e.get("url") for e in (rec.get("events") or []) if e.get("url")}
    return cites, used, {u for u in linked if u}


def check_citation_linkage(records: dict[str, dict]) -> list[str]:
    """
    Whether a record's source list matches the sources it actually uses.

    All three findings were `scripts/narrative_check.py`'s alone until B04. The
    duplicate-URL check in particular existed only in the non-gating script and
    fires zero times on the shipped corpus today, which is precisely why it
    needed moving: a check that is currently silent is a check nobody would
    notice losing, and it caught a real duplicate in ERI when it was written.

    Warnings, not errors, and deliberately so. A source attached to no claim
    inflates an apparent evidence base and a URL used but unlisted understates
    it — both are worth seeing, neither is a false statement about a country.
    """
    problems: list[str] = []
    for iso3, rec in sorted(records.items()):
        cites, used, linked = _citation_links(rec)
        cited_urls = {str(c.get("url", "")) for c in cites.values()}

        orphans = [cid for cid, c in cites.items()
                   if cid not in used and str(c.get("url", "")) not in linked]
        if orphans:
            problems.append(
                f"[warning] {iso3} · citations: {len(orphans)} listed but attached "
                f"to no claim ({', '.join(sorted(orphans))}).")

        unlisted = sorted(u for u in linked if u not in cited_urls)
        if unlisted:
            problems.append(
                f"[warning] {iso3} · citations: {len(unlisted)} URL(s) used in "
                f"recent items or events but absent from the citations block.")

        by_url: dict[str, list[str]] = {}
        for cid, c in cites.items():
            by_url.setdefault(str(c.get("url", "")), []).append(cid)
        for url, ids in sorted(by_url.items()):
            if len(ids) > 1:
                problems.append(
                    f"[warning] {iso3} · citations: {'/'.join(sorted(ids))} are the "
                    f"same URL under different ids.")
    return problems


def check_internal(records: dict[str, dict],
                   names: dict[str, str] | None = None) -> list[str]:
    """Claims a record makes that can be checked without the panel at all."""
    problems: list[str] = []
    names = names or {}
    for iso3, rec in sorted(records.items()):
        meta = rec.get("meta") or {}
        recent = rec.get("recent") or {}
        items = list(recent.get("primary") or []) + list(recent.get("extended") or [])

        # the record must not disagree with the index about what a country is called
        published = names.get(iso3)
        recorded = meta.get("name")
        if published and recorded and recorded != published:
            problems.append(
                f"[error] {iso3} · meta.name: record says {recorded!r}, the "
                f"published bundle says {published!r}. The interface renders the "
                f"bundle's name, so the two must agree.")

        # a "recent development" dated after the record was written is a
        # prediction wearing a publication date — the exact failure the date
        # requirement exists to catch. Found in ZMB: an election written up in
        # the past tense two days before it happened.
        updated = str(meta.get("last_updated") or "")
        dated = [str(i.get("date") or "") for i in items]
        ahead = sorted(d for d in dated if len(d) >= 10 and updated and d > updated)
        if ahead:
            problems.append(
                f"[error] {iso3} · recent: {len(ahead)} item(s) dated after the "
                f"record's own last_updated ({updated}): {', '.join(ahead)}. A "
                f"development cannot be reported before it happens.")

        # membership spans must be coherent
        for m in rec.get("rec_membership") or []:
            joined, left = m.get("joined"), m.get("left")
            org = m.get("org", "?")
            if joined and left and int(left) < int(joined):
                problems.append(
                    f"[error] {iso3} · rec_membership {org}: left {left} before "
                    f"joining {joined}.")
            if str(m.get("status")) == "withdrawn" and not left:
                problems.append(
                    f"[error] {iso3} · rec_membership {org}: withdrawn but no "
                    f"year of withdrawal.")

        # the same event recorded twice
        seen: dict[tuple, int] = {}
        for e in rec.get("events") or []:
            key = (e.get("year"), e.get("type"))
            seen[key] = seen.get(key, 0) + 1
        for key, count in seen.items():
            if count > 1:
                problems.append(
                    f"[error] {iso3} · events: {count} entries share year/type "
                    f"{key}.")

        bal = rec.get("balance") or {}
        if bal:
            actual = {"positive": 0, "negative": 0, "mixed": 0}
            for i in items:
                s = str(i.get("sentiment", "")).lower()
                if s in actual:
                    actual[s] += 1
            claimed = {k: int(bal.get(f"n_{k}", 0) or 0) for k in actual}
            if claimed != actual:
                problems.append(
                    f"[error] {iso3} · balance: counts {claimed} but the record "
                    f"contains {actual}.")

        # every referenced citation id must exist
        cites = {str(c.get("id")) for c in (rec.get("citations") or []) if c.get("id")}
        hist = rec.get("historical") or {}
        refs = set(hist.get("overview_citations") or [])
        refs |= set(hist.get("colonial_legacy_citations") or [])
        for k in hist.get("key_periods") or []:
            refs |= set(k.get("citations") or [])
        for p in (rec.get("pillars") or {}).values():
            refs |= set((p or {}).get("citations") or [])
        for m in rec.get("rec_membership") or []:
            refs |= set(m.get("citations") or [])
        dangling = sorted(refs - cites - {PANEL_CITATION})
        if dangling:
            problems.append(
                f"[error] {iso3} · citations: referenced but not defined: "
                f"{', '.join(dangling)}.")

    # A record cannot claim audited sources before an audit run has happened.
    # Reported once for the corpus rather than once per country: it is a single
    # fact about where the rotation has reached, and 54 identical lines would
    # bury the per-record findings above.
    premature = {iso3: sum(1 for c in (rec.get("citations") or []) if c.get("verified"))
                 for iso3, rec in records.items()
                 if int((rec.get("meta") or {}).get("iteration_count", 0) or 0) < AUDIT_EVERY}
    premature = {k: v for k, v in premature.items() if v}
    if premature:
        problems.append(
            f"[warning] {len(premature)} records carry {sum(premature.values())} "
            f"citations marked verified:true while still short of their first "
            f"AUDIT run (iteration {AUDIT_EVERY}). The interface already reports "
            f"these as cited rather than confirmed; the flag in the data is what "
            f"is premature.")
    return problems


# ── Advisory checks ────────────────────────────────────────────────────────────

def check_advisory(records: dict[str, dict]) -> list[str]:
    """Judgement, not arithmetic. Reported, never gating."""
    notes: list[str] = []

    # Audit coverage, reported whether or not anything is wrong. Once the flags
    # were reset to false the premature-flag error went silent, and silence
    # would wrongly read as "the sources are fine" rather than "nobody has
    # checked them yet". State the position explicitly instead.
    total_cites = sum(len(rec.get("citations") or []) for rec in records.values())
    confirmed = sum(1 for rec in records.values()
                    for c in (rec.get("citations") or []) if c.get("verified"))
    audited_records = sum(
        1 for rec in records.values()
        if int((rec.get("meta") or {}).get("iteration_count", 0) or 0) >= AUDIT_EVERY)
    notes.append(
        f"audit coverage: {audited_records} of {len(records)} records have "
        f"reached an AUDIT run (iteration {AUDIT_EVERY}); {confirmed} of "
        f"{total_cites} citations are confirmed as opened and supporting the "
        f"claim that cites them. Reachability is separately machine-checked by "
        f"narrative_check.py --links.")

    latest: dict[str, str] = {}
    for iso3, rec in records.items():
        recent = rec.get("recent") or {}
        dates = [str(i.get("date", "")) for i in
                 (list(recent.get("primary") or []) + list(recent.get("extended") or []))]
        dates = [d for d in dates if len(d) >= 7]
        if dates:
            latest[iso3] = max(dates)
    if latest:
        oldest = sorted(latest.items(), key=lambda kv: kv[1])[:5]
        notes.append(
            "recency spread across the corpus: newest recent-item date ranges "
            f"{min(latest.values())} to {max(latest.values())}. Stalest: "
            + ", ".join(f"{i} ({d})" for i, d in oldest))

    # The corpus-wide totals. The per-record detail is a gating-layer warning in
    # check_citation_linkage; this line is the one-number trend, and it shares
    # _citation_links with that check so the two cannot report different figures.
    unlinked = unlisted = 0
    for rec in records.values():
        cites, used, linked = _citation_links(rec)
        urls = {str(c.get("url", "")) for c in cites.values()}
        unlinked += sum(1 for cid, c in cites.items()
                        if cid not in used and str(c.get("url", "")) not in linked)
        unlisted += sum(1 for u in linked if u not in urls)
    notes.append(f"citation linkage: {unlinked} sources attached to no claim; "
                 f"{unlisted} URLs used but absent from a citations block")

    # How much of a record rests on encyclopedia entries rather than reporting,
    # research or primary sources. Not a rule — Wikipedia is a legitimate source
    # for settled history, and the blueprint asks for it alongside a news link.
    # But a record at 79% is resting on a different quality of evidence than one
    # at 7%, and that difference is invisible in the interface, which shows only
    # a count of sources.
    shares = []
    for iso3, rec in records.items():
        cites = rec.get("citations") or []
        if not cites:
            continue
        wiki = sum(1 for c in cites if str(c.get("source_type")) == "wikipedia")
        shares.append((wiki / len(cites), iso3, wiki, len(cites)))
    if shares:
        shares.sort(reverse=True)
        heaviest = ", ".join(f"{i} ({w}/{t})" for _, i, w, t in shares[:5])
        mean = sum(s for s, _, _, _ in shares) / len(shares)
        notes.append(f"sourcing mix: Wikipedia is {mean:.0%} of citations on "
                     f"average, ranging {shares[-1][0]:.0%} to {shares[0][0]:.0%}. "
                     f"Most encyclopedia-reliant: {heaviest}")

    # Pillars whose only source is a general history article. The schema requires
    # a citation per pillar, but most pillar summaries are index output and have
    # no claim a URL could support, so the requirement gets satisfied with
    # whatever is to hand. Reported, not gated: the fix is a schema decision
    # (logged in pending_format_proposals), not a per-record error.
    generic = re.compile(
        r"^History of|History \(|— History|Colony and Protectorate|"
        r"War of Independence|Unilateral Declaration|genocide|Secedes from|"
        r"French protectorate|Pacification of|Complete History", re.I)
    only_history = 0
    written = 0
    for rec in records.values():
        cites = {str(c.get("id")): str(c.get("title", ""))
                 for c in (rec.get("citations") or []) if c.get("id")}
        for p in (rec.get("pillars") or {}).values():
            ids = [i for i in ((p or {}).get("citations") or []) if i in cites]
            if not ids:
                continue
            written += 1
            if all(generic.search(cites[i]) for i in ids):
                only_history += 1
    if written:
        notes.append(
            f"pillar sourcing: {only_history} of {written} written pillars "
            f"({only_history / written:.0%}) cite only a general history or "
            f"colonial-era article, which cannot support a present-day "
            f"indicator claim. See pending_format_proposals — the schema "
            f"requires a citation per pillar even where the summary is pure "
            f"index output.")

    no_background = [i for i, rec in records.items()
                     if not any((x.get("wikipedia_url") or "")
                                for x in (list((rec.get("recent") or {}).get("primary") or [])
                                          + list((rec.get("recent") or {}).get("extended") or [])))]
    if no_background:
        notes.append(f"{len(no_background)} records have no background link on any "
                     f"recent item, so the interface shows a source row of a "
                     f"different shape for them: {', '.join(sorted(no_background)[:8])}"
                     + (" ..." if len(no_background) > 8 else ""))
    return notes


def all_checks(records: dict[str, dict], scores: pd.DataFrame,
               observations: pd.DataFrame, year: int,
               names: dict[str, str] | None = None) -> list[str]:
    """
    Every consistency check, in one call, in a fixed order.

    The single entry point B04 exists to create. `scripts/narrative_check.py`
    used to carry its own copy of this logic and the two had already drifted in
    both directions: the script had a duplicate-URL check the gate lacked, the
    gate had quoted-value, name-drift, future-date and membership-span checks
    the script lacked. Two validators means two answers to "does this record
    ship", and the one with tests was the one that did not gate.

    The script now calls this. Anything added here is added to both.
    """
    return (check_claims(records, scores, year)
            + check_quoted_values(records, observations, year)
            + check_indicator_phrases(observations, year)
            + check_panel_citations(records, year)
            + check_internal(records, names)
            + check_citation_linkage(records))


def main() -> int:
    print("Narrative corpus verification (independent re-read)")
    records = load_records()
    if not records:
        print("  no records found — nothing to verify")
        return 0
    scores, year = load_pillar_scores()
    names = load_country_names()
    print(f"  {len(records)} records · panel reference year {year}\n")

    problems = all_checks(records, scores, load_observations(), year, names)
    errors = [p for p in problems if p.startswith("[error]")]
    warnings = [p for p in problems if p.startswith("[warning]")]

    for p in errors + warnings:
        print(f"  {p}")
    if not problems:
        print("  every self-claim checked agrees with the panel")

    print("\n  advisory (report only):")
    for note in check_advisory(records):
        print(f"    - {note}")

    print(f"\n  {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
