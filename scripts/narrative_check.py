"""
scripts/narrative_check.py — validate narrative records before they ship.

Three things, in increasing cost:

  1. schema      structure, word limits, citation references, framing balance,
                 and the rule that a greyed pillar gets no prose
  2. links       every citation URL resolves (--links; needs network)
  3. coverage    which countries have records, which are still backlogged

A record that fails validation does not ship. The narrative layer is written by
a language model across many sessions; convention alone does not survive that.

    python scripts/narrative_check.py                 # all records, schema only
    python scripts/narrative_check.py --country TCD
    python scripts/narrative_check.py --links         # also check URLs resolve
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml  # noqa: E402

from asi.core.countries import COUNTRIES  # noqa: E402
from asi.narrative.schema import validate, mode_for_iteration  # noqa: E402
from asi.dashboard import data as D  # noqa: E402

NARRATIVE_DIR = Path("narrative/countries")
STATE_FILE = Path("narrative/state.yaml")


def greyed_pillars(panel, iso3: str) -> set[str]:
    """Pillars the index refuses to show for this country at the reference year."""
    pil = D.country_pillar_series(panel, iso3)
    at_year = pil[pil["year"] == panel.reference_year]
    if at_year.empty:
        return set()
    return set(at_year[~at_year["displayable"]]["pillar_id"])


def check_links(records: dict[str, dict]) -> list[str]:
    """
    Confirm every cited URL resolves. Fabricated sources are the top risk this
    task is exposed to, so a citation that cannot be reached is treated as
    unverified — but "cannot be reached by this script" is not the same claim
    as "does not exist", and the two must not be reported identically.

    Two things independent of link validity get in the way here:
      - SSL verification fails on this project's environment against otherwise
        valid HTTPS sites (documented precedent: 01_pull.py's "Windows SSL fix",
        a corporate/system proxy replacing certificates with a CA Python does
        not recognise). Disabled the same way, for the same reason.
      - Some sites (IMF/Akamai observed) return 403 to any scripted request
        regardless of method, which a human browser sails past. That is bot
        detection, not link rot, so it is reported as a warning to check
        manually rather than an error implying fabrication.

    A HEAD request is tried first and a GET is used as a fallback, since some
    servers reject HEAD outright (405) while serving GET normally.
    """
    import ssl
    import urllib.error
    import urllib.request

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    def _try(url: str, method: str) -> tuple[bool, int | None, str | None]:
        req = urllib.request.Request(
            url, method=method,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ASI-narrative-check/1.0)"})
        try:
            with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
                return 200 <= r.status < 400, r.status, None
        except urllib.error.HTTPError as e:
            return False, e.code, None
        except Exception as e:
            return False, None, f"{type(e).__name__}: {e}"

    problems, seen = [], {}
    for iso3, rec in records.items():
        for c in rec.get("citations") or []:
            url = c.get("url")
            if not url:
                continue
            if url not in seen:
                ok, status, err = _try(url, "HEAD")
                if not ok and status in (403, 405, None):
                    ok, status, err = _try(url, "GET")
                seen[url] = (ok, status, err)
            ok, status, err = seen[url]
            cid = c.get("id")
            if ok:
                continue
            if status == 403:
                problems.append(
                    f"[warning] {iso3} · citation {cid}: blocked our request "
                    f"(HTTP 403) — check manually in a browser, this is likely "
                    f"bot detection rather than a dead link — {url}")
            elif status is not None:
                problems.append(f"[error] {iso3} · citation {cid}: "
                                f"HTTP {status} — {url}")
            else:
                problems.append(f"[error] {iso3} · citation {cid}: "
                                f"unreachable ({err}) — {url}")
    return problems


#: Ordered most-specific-first: "second-strongest" also contains "strongest",
#: so testing the shorter phrase first would misread it.
RANK_CLAIMS = [
    ("second-strongest", re.compile(r"second-strongest (?:single )?pillar"), 2),
    ("second-weakest",   re.compile(r"second-weakest (?:single )?pillar"), -2),
    ("strongest",        re.compile(r"(?<!second-)\bstrongest (?:single )?pillar"), 1),
    ("weakest",          re.compile(r"(?<!second-)\bweakest (?:single )?pillar"), -1),
]


def _pillar_ranking(panel, iso3: str) -> list[str]:
    """This country's displayable pillars, best score first."""
    pil = D.country_pillar_series(panel, iso3)
    at_year = pil[(pil["year"] == panel.reference_year) & pil["displayable"]]
    at_year = at_year[at_year["score"].notna()]
    return list(at_year.sort_values("score", ascending=False)["pillar_id"])


def check_consistency(records: dict[str, dict], panel) -> list[str]:
    """
    Claims a record makes about itself, checked against the record and the panel.

    `validate()` enforces that a record has the right *shape*. These checks ask
    whether what it says is true — the part an AUDIT run is supposed to do by
    hand, and therefore the part that silently rots between audits.

    Four failure modes this catches, all observed in the corpus:

      - a framing-balance count that disagrees with the items actually present,
        which quietly defeats the one mechanism guarding against skewed framing
      - a pillar summary calling itself the country's strongest or weakest when
        the panel ranks it elsewhere; prose written against one year's numbers
        goes wrong when the panel is rebuilt, and nothing else notices
      - sources listed but attached to no claim, which inflates an apparent
        evidence base
      - sources used in a recent item or event but missing from the citations
        block, so the record's own source list understates what it relies on
    """
    problems: list[str] = []

    for iso3, rec in sorted(records.items()):
        meta = rec.get("meta") or {}
        recent = rec.get("recent") or {}
        items = list(recent.get("primary") or []) + list(recent.get("extended") or [])

        # ── framing balance must match the items present ──────────────────────
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
                    f"contains {actual}. The framing count is the only guard "
                    f"against skewed coverage; a wrong one is worse than none.")

        # ── "strongest / weakest pillar" claims must match the panel ──────────
        order = _pillar_ranking(panel, iso3)
        if order:
            for pid, p in (rec.get("pillars") or {}).items():
                summary = ((p or {}).get("summary") or "").lower()
                for sentence in re.split(r"(?<=\.)\s+", summary):
                    # a sentence naming another pillar's score is a reference,
                    # not a claim about this pillar
                    if re.search(r"pillar [a-g](?:'s)? (?:score|own)", sentence):
                        continue
                    for label, pattern, target in RANK_CLAIMS:
                        if not pattern.search(sentence):
                            continue
                        if abs(target) > len(order):
                            break
                        want = order[target - 1] if target > 0 else order[target]
                        if pid != want:
                            pos = order.index(pid) + 1 if pid in order else "unscored"
                            problems.append(
                                f"[error] {iso3} · pillars.{pid}: claims to be the "
                                f"{label} pillar, but ranks {pos} of {len(order)} "
                                f"at {panel.reference_year} — {want} is.")
                        break

        # ── citation linkage, both directions ─────────────────────────────────
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

        cited_urls = {str(c.get("url", "")) for c in cites.values()}
        linked_urls = {u for i in items
                       for u in (i.get("news_url"), i.get("wikipedia_url")) if u}
        linked_urls |= {e.get("url") for e in (rec.get("events") or []) if e.get("url")}

        orphans = [cid for cid, c in cites.items()
                   if cid not in used and str(c.get("url", "")) not in linked_urls]
        if orphans:
            problems.append(
                f"[warning] {iso3} · citations: {len(orphans)} listed but attached "
                f"to no claim ({', '.join(sorted(orphans))}).")

        unlisted = sorted(u for u in linked_urls if u and u not in cited_urls)
        if unlisted:
            problems.append(
                f"[warning] {iso3} · citations: {len(unlisted)} URL(s) used in "
                f"recent items or events but absent from the citations block.")

        by_url: dict[str, list[str]] = {}
        for cid, c in cites.items():
            by_url.setdefault(str(c.get("url", "")), []).append(cid)
        for url, ids in by_url.items():
            if len(ids) > 1:
                problems.append(
                    f"[warning] {iso3} · citations: {'/'.join(sorted(ids))} are the "
                    f"same URL under different ids.")

    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", help="check one ISO3 only")
    ap.add_argument("--links", action="store_true",
                    help="also check that every citation URL resolves (network)")
    args = ap.parse_args()

    print("=" * 74)
    print("NARRATIVE CHECK")
    print("=" * 74)

    NARRATIVE_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(NARRATIVE_DIR.glob("*.yaml"))
    if args.country:
        paths = [p for p in paths if p.stem.upper() == args.country.upper()]
        if not paths:
            print(f"No record for {args.country.upper()} yet "
                  f"(expected {NARRATIVE_DIR / (args.country.upper() + '.yaml')}).")
            return 1

    records = {}
    for p in paths:
        try:
            records[p.stem.upper()] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            print(f"[error] {p.name}: not valid YAML — {e}")
            return 1

    # ── coverage ──────────────────────────────────────────────────────────────
    if not args.country:
        state = (yaml.safe_load(STATE_FILE.read_text(encoding="utf-8"))
                 if STATE_FILE.exists() else {})
        backlog = state.get("backlog") or {}
        first_pass = [c for c, e in backlog.items() if e.get("first_pass")]
        print(f"\nCoverage: {len(records)} of {len(COUNTRIES)} countries have a record")
        if first_pass:
            print(f"  first pass still to do ({len(first_pass)}): {', '.join(first_pass)}")
        remaining = len(backlog) - len(first_pass)
        if remaining > 0:
            print(f"  backlog after the first pass: {remaining} countries")
        if not records:
            print("\nNo records yet. Start with:")
            print(f"  python scripts/country_facts.py {first_pass[0] if first_pass else 'MUS'}")
            print("  then follow narrative/prompts/RESEARCH.md")
            return 0

    # ── schema ────────────────────────────────────────────────────────────────
    panel = D.load()
    all_problems: list[str] = []
    print()
    for iso3, rec in records.items():
        problems = validate(rec, greyed_pillars=greyed_pillars(panel, iso3))
        errors = [p for p in problems if p.severity == "error"]
        warnings = [p for p in problems if p.severity == "warning"]
        n = (rec.get("meta") or {}).get("iteration_count", 0)
        mode = mode_for_iteration(n + 1).value
        status = "OK" if not errors else f"{len(errors)} ERRORS"
        print(f"  {iso3}  iteration {n} -> next run is {mode.upper():<7} {status}"
              + (f", {len(warnings)} warnings" if warnings else ""))
        all_problems += [str(p) for p in problems]

    # ── consistency ───────────────────────────────────────────────────────────
    # Structure is checked above; this asks whether what the records say is true.
    all_problems += check_consistency(records, panel)

    # ── links ─────────────────────────────────────────────────────────────────
    if args.links:
        print("\nChecking citation URLs ...")
        link_problems = check_links(records)
        all_problems += link_problems
        print(f"  {len(link_problems)} unresolvable" if link_problems
              else "  all citation URLs resolve")

    errors = [p for p in all_problems if p.startswith("[error]")]
    warnings = [p for p in all_problems if p.startswith("[warning]")]
    if all_problems:
        print()
        for p in errors + warnings:
            print(f"  {p}")

    print()
    print("-" * 74)
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    if errors:
        print("Records with errors must not be committed.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
