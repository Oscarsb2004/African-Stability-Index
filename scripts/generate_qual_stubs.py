"""
scripts/generate_qual_stubs.py — create qualitative note stubs for every country.

Idempotent: existing files are NEVER overwritten.

    python scripts/generate_qual_stubs.py

Country names come from asi.core.countries. The previous version kept its own
hardcoded list of 54 (iso3, name) pairs, which was a fourth copy of the country
registry and free to drift; tests/test_ssot.py now forbids that.

Note: the Phase D narrative system writes a richer per-country record defined by
narrative/BLUEPRINT.md. These stubs remain the hand-edited layer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from asi.core.countries import COUNTRIES   # noqa: E402

STUB = """\
# Qualitative country notes — {name} ({iso3})
# Edit this file to add your own analysis.
# All fields are optional; leave empty strings or empty lists as placeholders.
# last_updated: use ISO date format YYYY-MM-DD

overview: ""

recent_developments: ""

strengths:
  - ""

challenges:
  - ""

historical_notes: ""

key_figures: []

external_sources: []

last_updated: ""
"""


def main() -> int:
    out_dir = Path("qualitative/countries")
    out_dir.mkdir(parents=True, exist_ok=True)

    created = skipped = 0
    for iso3, meta in COUNTRIES.items():
        path = out_dir / f"{iso3}.yaml"
        if path.exists():
            skipped += 1
            continue
        path.write_text(STUB.format(iso3=iso3, name=meta["name"]), encoding="utf-8")
        created += 1

    print(f"Created {created} stubs, skipped {skipped} existing files.")
    print(f"Edit files in: {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
