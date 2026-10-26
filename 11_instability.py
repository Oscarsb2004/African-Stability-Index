"""
11_instability.py — the "Spreading instability" tab's files and the links between states (the owner's rulings of
2026-10-23).

    python 11_instability.py

It writes:
    geo/links.json   each link of registry/links.yaml (the owner's compilation, R5) as a great-circle line between
                     the two states' Natural Earth label points, with its card: the actor, the kind, the status as
                     its sources put it, its summary and its sources, each with its tier under the rule (R7);
                     and the coverage list: each UN panel's latest report and how much of it has been read

Natural Earth comes through athena.fetch, hash-locked in the project's sources.lock.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

from asi import geography  # noqa: E402
from asi.core.countries import COUNTRIES  # noqa: E402
from asi.instability import links  # noqa: E402

GEO = ROOT / "web" / "public" / "geo"


def label_points(ne: dict) -> tuple[dict[str, tuple[float, float]], dict[str, str]]:
    """Each state's Natural Earth label point and name; for a merged code (Somaliland in Somalia), the state's own.
    A member state keeps the ASI's name."""
    points: dict[str, tuple[float, float]] = {}
    names: dict[str, str] = {}
    for f in ne["features"]:
        p = f["properties"]
        code = geography.code(p)
        if code in points and p["ADM0_A3"] != code:
            continue
        points[code] = (float(p["LABEL_X"]), float(p["LABEL_Y"]))
        names[code] = COUNTRIES[code]["name"] if code in COUNTRIES else p["NAME"]
    return points, names


def write(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    from asi.sources import fetcher, sources

    ne = json.loads(fetcher().get(sources()["natural-earth-countries-50m"]["url"]))
    points, names = label_points(ne)
    reg = links.load(ROOT / "registry" / "links.yaml", set(points), set(COUNTRIES))
    doc = (links.LinkLines().run(links.LinkLines.Input(reg["links"], points, names)).geojson
           | {k: reg[k] for k in ("kinds", "tiers", "coverage")})
    write(GEO / "links.json", doc)
    by = {s: sum(1 for l in reg["links"] if l["status"] == s) for s in links.STATUS}
    print(f"links.json: {len(doc['features'])} links {by}, "
          f"{sum(1 for l in reg['links'] if l.get('until'))} historical; backers "
          f"{sorted({l['from'] for l in reg['links']})}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
