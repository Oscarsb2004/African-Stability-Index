"""
verify/narrative.py — independent verification of the narrative corpus.

Gates a release on the claims that are arithmetic, reports on the ones that are
judgement.

Why this exists as a verification layer rather than only as a script:

    `scripts/narrative_check.py` validates records, but it imports
    `asi.narrative.schema` and `asi.dashboard.data` — the exact dependency this
    package was created to avoid. If `asi.dashboard.data` mis-filtered
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
        dangling = sorted(refs - cites)
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

    unlinked = 0
    unlisted = 0
    for iso3, rec in records.items():
        cites = {str(c.get("id")): str(c.get("url", ""))
                 for c in (rec.get("citations") or []) if c.get("id")}
        hist = rec.get("historical") or {}
        used = set(hist.get("overview_citations") or [])
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
        unlinked += sum(1 for cid, url in cites.items()
                        if cid not in used and url not in linked)
        unlisted += sum(1 for u in linked if u and u not in set(cites.values()))
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


def main() -> int:
    print("Narrative corpus verification (independent re-read)")
    records = load_records()
    if not records:
        print("  no records found — nothing to verify")
        return 0
    scores, year = load_pillar_scores()
    names = load_country_names()
    print(f"  {len(records)} records · panel reference year {year}\n")

    problems = check_claims(records, scores, year) + check_internal(records, names)
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
