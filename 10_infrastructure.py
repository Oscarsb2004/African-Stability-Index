"""
10_infrastructure.py — the Infrastructure section's map layers and country figures (P65), from the publication list.

    python 10_infrastructure.py

`registry/layers.yaml` names every layer published, with its licence and attribution, and every layer withheld, with
its reason. This stage reads the store and the list, runs the components of `asi.infrastructure`, and writes what
they return under web/public/geo/infra/:
    layers.json        the catalogue: each layer's title, file, count, fields with the publisher's labels, licence
    <point layer>.json GeoJSON: ports (one point per port, each commodity it exports a row), mineral facilities,
                       deposits and exploration sites
    osm.pmtiles        vector tiles under ODbL: railways, major roads, and the grid lines the World Bank took from OSM
    grid.pmtiles       vector tiles under CC BY 4.0: the rest of the World Bank's 2017 grid map
    countries.json     each member state's ports and their exports, its facilities by commodity type, and the length
                       of each line layer inside it, by class or status

Which member state a feature belongs to is derived by the rule in `asi.infrastructure.places`. Needs the [geo] extra.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent

import pandas as pd  # noqa: E402

from asi.core.countries import COUNTRIES  # noqa: E402
from asi.infrastructure import registry  # noqa: E402
from asi.infrastructure.layers import NULL, CountrySummary, LineLayer, PointLayer, labels_for  # noqa: E402
from asi.infrastructure.places import NEAREST_KM, member_polygons  # noqa: E402
from asi.infrastructure.tiles import MAX_ZOOM, MIN_ZOOM, VectorTiles  # noqa: E402

OUT = ROOT / "web" / "public" / "geo" / "infra"
REGISTRY = ROOT / "registry" / "layers.yaml"


def write(name: str, doc: dict) -> None:
    (OUT / name).write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8",
                            newline="\n")


def main() -> int:
    from asi.sources import fetcher, sources
    from athena import dataset, geo

    reg = registry.load(REGISTRY)
    polygons = member_polygons(json.loads(fetcher().get(sources()["natural-earth-countries-50m"]["url"])))
    OUT.mkdir(parents=True, exist_ok=True)
    catalogue = {"points": [], "lines": [], "archives": {}, "withheld": reg["withheld"]}

    points, docs = PointLayer(), {}
    for spec in reg["points"]:
        fields = dataset.load(spec["dataset"], "fields") if spec["dataset"].startswith("usgs") else pd.DataFrame()
        out = points.run(PointLayer.Input(spec, geo.load(spec["dataset"], spec["layer"]), polygons,
                                          labels_for(fields, spec["layer"]) if len(fields) else {}))
        write(out.entry["file"], out.geojson)
        catalogue["points"].append(out.entry)
        docs[spec["id"]] = out.geojson
        print(f"{out.entry['file']}: {out.entry['count']:,} features ({out.entry.get('withheld', 0)} withheld, "
              f"{out.entry['unplaced']} outside every member state)")

    lines, archives, km = LineLayer(), defaultdict(list), {}
    for spec in reg["lines"]:
        out = lines.run(LineLayer.Input(spec, geo.load(spec["dataset"], spec["layer"]), polygons))
        for archive, layer in out.tiles:
            archives[archive].append((layer, spec))
        catalogue["lines"].append(out.entry)
        km[spec["id"]] = out.km
        print(f"{spec['id']}: {out.entry['count']:,} lines, length by state measured")

    tiler = VectorTiles()
    for name, parts in archives.items():
        meta = {"name": name, "attribution": "; ".join(dict.fromkeys(p[1]["attribution"] for p in parts))}
        stats = tiler.run(VectorTiles.Input([p[0] for p in parts], OUT / f"{name}.pmtiles", meta))
        catalogue["archives"][name] = {"file": f"{name}.pmtiles", "layers": [p[0].name for p in parts],
                                       "licence": "ODbL 1.0" if name == "osm" else "CC BY 4.0",
                                       "attribution": meta["attribution"], "tiles": stats.tiles}
        print(f"{name}.pmtiles: {stats.tiles:,} tiles, {(OUT / f'{name}.pmtiles').stat().st_size / 1e6:.1f} MB")

    summary = CountrySummary().run(CountrySummary.Input(reg["points"], docs, km, tuple(sorted(COUNTRIES))))
    catalogue["rules"] = {"null": NULL, "nearest_km": NEAREST_KM, "zooms": [MIN_ZOOM, MAX_ZOOM],
                          "place": "a point is in the member state whose Natural Earth 1:50m polygon holds it, or the "
                                   f"nearest within {NEAREST_KM} km; a line's length counts toward each state by the "
                                   "part inside its polygon, on the WGS84 ellipsoid (derived)"}
    write("layers.json", catalogue)
    write("countries.json", summary.countries)
    print(f"layers.json, countries.json; {len(reg['withheld'])} layers withheld, each with its reason")
    return 0


if __name__ == "__main__":
    sys.exit(main())
