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
    """Confirm every cited URL resolves. Fabricated sources are the top risk."""
    import urllib.request
    import urllib.error

    problems, seen = [], {}
    for iso3, rec in records.items():
        for c in rec.get("citations") or []:
            url = c.get("url")
            if not url:
                continue
            if url in seen:
                ok = seen[url]
            else:
                req = urllib.request.Request(
                    url, method="HEAD",
                    headers={"User-Agent": "ASI-narrative-check/1.0"})
                try:
                    with urllib.request.urlopen(req, timeout=12) as r:
                        ok = 200 <= r.status < 400
                except Exception:
                    ok = False
                seen[url] = ok
            if not ok:
                problems.append(f"[error] {iso3} · citation {c.get('id')}: "
                                f"url does not resolve — {url}")
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
