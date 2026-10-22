"""
10_infrastructure.py — the Infrastructure section's map layers and country figures (P65), from the publication list.

    python 10_infrastructure.py

`registry/layers.yaml` names every layer published, with its licence and attribution, and every layer withheld, with
its reason. This stage reads the store and the list, runs the components of `asi.infrastructure`, and writes what
they return under web/public/geo/infra/:
    layers.json        the catalogue: each layer's title, file, count, fields with the publisher's labels, licence
    <point layer>.json GeoJSON: PortWatch's chokepoints and its ports in member states, each with its complete years
                       of activity (derived sums of the daily estimates); USGS's ports (one point per port, each
                       commodity it exports a row, and its PortWatch activity where published keys link the two),
                       mineral facilities, deposits and exploration sites
    osm.pmtiles        vector tiles under ODbL: railways, major roads, and the grid lines the World Bank took from OSM
    grid.pmtiles       vector tiles under CC BY 4.0: the rest of the World Bank's 2017 grid map
    countries.json     each member state's ports and their exports, its facilities by commodity type, and the length
                       of each line layer inside it, by class or status

Which member state a feature belongs to is derived by the rule in `asi.infrastructure.places`, with the member
states' waters from Marine Regions' World EEZ v12 (CC BY 4.0). Needs the [geo] extra.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent

import pandas as pd  # noqa: E402

from asi.core.countries import COUNTRIES  # noqa: E402
from asi.infrastructure import registry  # noqa: E402
from asi.infrastructure.activity import RULE as ACTIVITY, YearlySums  # noqa: E402
from asi.infrastructure.layers import NULL, CountrySummary, LineLayer, PointLayer, labels_for  # noqa: E402
from asi.infrastructure.places import NEAREST_KM, member_polygons, member_waters, other_polygons  # noqa: E402
from asi.infrastructure.ports import PortLinks  # noqa: E402
from asi.infrastructure.tiles import MAX_ZOOM, MIN_ZOOM, VectorTiles  # noqa: E402

OUT = ROOT / "web" / "public" / "geo" / "infra"
REGISTRY = ROOT / "registry" / "layers.yaml"


def write(name: str, doc: dict) -> None:
    (OUT / name).write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8",
                            newline="\n")


def daily(root: Path, name: str, table: str, key: str, columns: list[str]) -> pd.DataFrame:
    """A daily table from the store, only the columns used (PortWatch's daily ports are 600 MB of CSV)."""
    return pd.read_csv(root / name / f"{table}.csv", usecols=["date", key, *columns], dtype={"date": str, key: str},
                       engine="pyarrow")


def main() -> int:
    from asi.sources import fetcher, sources
    from athena import dataset, geo
    from athena.adapters import nga_wpi

    reg = registry.load(REGISTRY)
    ne = json.loads(fetcher().get(sources()["natural-earth-countries-50m"]["url"]))
    polygons, others = member_polygons(ne), other_polygons(ne)
    waters = member_waters(json.loads(fetcher().get(sources()["marine-regions-eez"]["url"])))
    OUT.mkdir(parents=True, exist_ok=True)
    catalogue = {"points": [], "lines": [], "archives": {}, "withheld": reg["withheld"]}

    sums, specs = {}, {s["id"]: s for s in reg["points"]}
    for spec in reg["points"]:
        if "activity" in spec:
            a, key = spec["activity"], spec["id_field"]
            frame = daily(dataset.ROOT, spec["dataset"], a["table"], key, list(a["columns"]))
            out = YearlySums().run(YearlySums.Input(frame, key, tuple(a["columns"])))
            sums[spec["id"]] = out.sums
            print(f"{spec['id']}: complete years summed for {len(out.sums):,} of {frame[key].nunique():,}; the daily "
                  f"file runs to {out.last_day}")

    points, docs = PointLayer(), {}
    for spec in reg["points"]:
        frame = geo.load(spec["dataset"], spec["layer"])
        extra = {k: {"activity": v} for k, v in sums.get(spec["id"], {}).items()}
        link = None
        if "join" in spec:   # USGS's ports to PortWatch's, by published keys only
            to = specs[spec["join"]["to"]]
            codes, ambiguous = nga_wpi.locodes(geo.load(spec["join"]["index"], "ports"))
            link = PortLinks().run(PortLinks.Input(frame, spec["join"]["key"], codes, tuple(ambiguous),
                                                   geo.load(to["dataset"], to["layer"])))
            extra = {uid: pw | ({"activity": sums[to["id"]][pw["portwatch"]]} if pw["portwatch"] in sums[to["id"]]
                                else {}) for uid, pw in link.links.items()}
            spec = spec | {"activity": to["activity"]}
        fields = dataset.load(spec["dataset"], "fields") if spec["dataset"].startswith("usgs") else pd.DataFrame()
        out = points.run(PointLayer.Input(spec, frame, polygons, labels_for(fields, spec["layer"]) if len(fields)
                                          else {}, waters, extra, others))
        entry = out.entry | ({"linked_to_portwatch": link.counts} if link else {})
        write(entry["file"], out.geojson)
        catalogue["points"].append(entry)
        docs[spec["id"]] = out.geojson
        counts = {k: entry[k] for k in ("withheld", "unplaced", "outside_member_states",
                                        "placed_otherwise_than_publisher", "linked_to_portwatch") if k in entry}
        print(f"{entry['file']}: {entry['count']:,} features; {counts}")

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
    catalogue["rules"] = {"null": f"{NULL}, in any case", "nearest_km": NEAREST_KM, "zooms": [MIN_ZOOM, MAX_ZOOM],
                          "place": "a point is in the member state whose Natural Earth 1:50m polygon holds it, and in "
                                   "none when another state's polygon holds it; at sea, in the member state whose "
                                   "waters hold it (an exclusive economic zone with one sovereign, Marine Regions' "
                                   "World EEZ v12), and in none where two or more states claim or share the waters; "
                                   f"otherwise in the state whose land is nearest within {NEAREST_KM} km, when it is a "
                                   "member. Where a publisher names each point's state (PortWatch), a point counts for "
                                   "a member state only where the publisher names it too. A line's length counts "
                                   "toward each state by the part inside its polygon, on the WGS84 ellipsoid "
                                   "(derived). This says whose waters a point is in, not where a boundary lies in law",
                         "activity": ACTIVITY,
                         "join": "a USGS port is a PortWatch port only by published keys: USGS's World Port Index "
                                 "ID, NGA's World Port Index (the index number's UN/LOCODE, the same code with or "
                                 "without its space) and PortWatch's LOCODE, where each step gives exactly one port; "
                                 "never by name or distance"}
    write("layers.json", catalogue)
    write("countries.json", summary.countries)
    print(f"layers.json, countries.json; {len(reg['withheld'])} layers withheld, each with its reason")
    return 0


if __name__ == "__main__":
    sys.exit(main())
