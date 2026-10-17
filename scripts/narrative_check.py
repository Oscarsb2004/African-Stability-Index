"""
scripts/narrative_check.py — validate narrative records before they ship.

The authoring-time front end. It runs the same checks the release gate runs,
then adds the two things a gate cannot: a network pass over every citation URL,
and a coverage report saying which countries still have no record.

Four things, in increasing cost:

  1. schema      structure, word limits, citation references, framing balance,
                 and the rule that a greyed pillar gets no prose
  2. consistency whether what a record says is true — delegated in full to
                 verify/narrative.py (see below)
  3. links       every citation URL resolves (--links; needs network)
  4. coverage    which countries have records, which are still backlogged

Step 2 used to be implemented here as well as there, and the two copies had
already drifted in both directions: this file had a duplicate-URL check the gate
lacked, the gate had quoted-value, name-drift, future-date and membership-span
checks this file lacked. Two validators means two answers to "does this record
ship" — and the copy with test coverage was this one, the copy that does not
gate. B04 collapsed them. The implementation lives in `verify/narrative.py`
because that is the one a release depends on; this file calls it.

The dependency runs script → verify, never the reverse: `verify/narrative.py`
still imports nothing from `asi`, which is what lets it check the corpus against
the published panel rather than against the loader the interface happens to use.

A record that fails validation does not ship. The narrative layer is written by
a language model across many sessions; convention alone does not survive that.

    python scripts/narrative_check.py                 # all records, schema only
    python scripts/narrative_check.py --country TCD
    python scripts/narrative_check.py --links         # also check URLs resolve
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml  # noqa: E402

from asi.core.countries import COUNTRIES  # noqa: E402
from asi.narrative.schema import validate, mode_for_iteration  # noqa: E402
from asi import results as D  # noqa: E402
from verify import narrative as VN  # noqa: E402

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


def check_consistency(records: dict[str, dict], panel) -> list[str]:
    """
    Whether what the records say is true. A thin caller; see the module docstring.

    The frames handed over are the ones already loaded for the schema pass, so
    the gate's logic runs against exactly the data this script validated. The
    gate reaches the same frames by reading `data/panel/` itself when it runs
    standalone — same rules, and `tests/test_narrative_consistency.py` asserts
    the two routes produce an identical problem list on the shipped corpus.
    """
    names = {iso3: c.get("name", iso3) for iso3, c in panel.countries.items()}
    return VN.all_checks(records, panel.pillar_scores, panel.observations,
                         panel.reference_year, names)


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
        problems = validate(rec, greyed_pillars=greyed_pillars(panel, iso3),
                            reference_year=panel.reference_year)
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
