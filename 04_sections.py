"""
04_sections.py — the economy and appraisal sections for each country, from Athena's datasets (P54).

`sections.toml` binds athena-core's section templates to series; the datasets named on the command line are the
edition, as for 01_inputs.py:

    python 04_sections.py wdi-2026-10-08 wgi-2026-09-25 hdr-2025 cpi-2025

It writes web/public/data/sections.json (the site reads it) in the format `athena.sections/1`, checked before it is written. Publishers' values
pass through as printed; every other figure is computed by a named shell in athena.figures and marked derived.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))  # athena-core, for the `athena` package

from asi.core.countries import COUNTRIES  # noqa: E402

OUTPUT = ROOT / "web" / "public" / "data" / "sections.json"


def main(names: list[str]) -> int:
    if not names:
        print(__doc__)
        return 2
    from athena import dataset, sections

    b = sections.binding(ROOT / "sections.toml")
    wanted = {m["series"] for m in b["measures"].values()}
    areas = sorted(COUNTRIES)
    values = {}
    for name in names:
        v = dataset.load(name)
        values[name] = v[v["SERIES"].isin(wanted) & v["REF_AREA"].isin(areas)]
    doc = sections.build(b, values, areas)
    doc["names"] = {iso3: c["name"] for iso3, c in COUNTRIES.items()}
    sections.check(doc)
    OUTPUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8",
                      newline="\n")
    held = sum(r["value"] is not None for a in doc["areas"].values() for s in a.values() for r in s.values())
    total = sum(len(s) for a in doc["areas"].values() for s in a.values())
    print(f"{OUTPUT.relative_to(ROOT)}: {len(areas)} countries, {len(doc['sections'])} sections, "
          f"{held:,} of {total:,} figures with a value, from {', '.join(names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
