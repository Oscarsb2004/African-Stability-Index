"""
10_infrastructure.py — the Infrastructure section's map layers and country figures (P65), from the publication list.

    python 10_infrastructure.py

`registry/layers.yaml` names every layer published, with its licence and attribution, and every layer withheld, with
its reason. This stage writes, under web/public/geo/infra/:
    layers.json        the catalogue: each layer's title, file, count, fields with the publisher's labels, licence
    <point layer>.json GeoJSON: ports (one point per port, each commodity it exports a row), mineral facilities,
                       deposits and exploration sites
    osm.pmtiles        vector tiles under ODbL: railways, major roads, and the grid lines the World Bank took from OSM
    grid.pmtiles       vector tiles under CC BY 4.0: the rest of the World Bank's 2017 grid map
    countries.json     each member state's ports and their exports, its facilities by commodity type, and the length
                       of each line layer inside it, by class or status

USGS writes a missing value as the text "<Null>"; it is read as missing. Which member state a feature belongs to is
derived, by a stated rule: a point is in the state whose Natural Earth 1:50m polygon holds it, or the nearest within
NEAREST_KM (ports sit on the coast, which the generalised polygons can miss); a line's length counts toward each
state by the part inside its polygon, measured on the WGS84 ellipsoid. Needs the [geo] extra.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))  # athena-core, for `athena` and `adapters`

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from asi import geography  # noqa: E402
from asi.core.countries import COUNTRIES  # noqa: E402

OUT = ROOT / "web" / "public" / "geo" / "infra"
REGISTRY = ROOT / "registry" / "layers.yaml"
NULL = "<Null>"
NEAREST_KM, DECIMALS, MIN_ZOOM, MAX_ZOOM = 10, 5, 3, 10


def clean(frame: pd.DataFrame) -> pd.DataFrame:
    """The publisher's "<Null>" and empty text as missing."""
    return frame.replace({NULL: None, "": None})


def states(ne: dict) -> gpd.GeoDataFrame:
    """The member states' Natural Earth polygons, one row each."""
    rows = [{"iso3": geography.code(f["properties"]), "geometry": f["geometry"]} for f in ne["features"]
            if geography.code(f["properties"]) in COUNTRIES]
    frame = gpd.GeoDataFrame.from_features([{"type": "Feature", "properties": {"iso3": r["iso3"]},
                                             "geometry": r["geometry"]} for r in rows], crs=4326)
    return frame.dissolve("iso3").reset_index()


def locate(points: gpd.GeoDataFrame, polygons: gpd.GeoDataFrame) -> pd.Series:
    """Each point's member state: the polygon holding it, or the nearest within NEAREST_KM; otherwise none."""
    inside = gpd.sjoin(points[["geometry"]], polygons, how="left", predicate="within")["iso3"]
    inside = inside[~inside.index.duplicated()]
    missing = inside.isna()
    if missing.any():
        near = gpd.sjoin_nearest(points.loc[missing, ["geometry"]].to_crs(3857), polygons.to_crs(3857), how="left",
                                 max_distance=NEAREST_KM * 1000 * 1.6)["iso3"]  # Web Mercator stretches by up to 1.6
        inside.loc[near.index] = near[~near.index.duplicated()]
    return inside.reindex(points.index)


def lengths(lines: gpd.GeoDataFrame, polygons: gpd.GeoDataFrame, by: str) -> dict[str, dict[str, float]]:
    """Kilometres of line inside each state, by a class column."""
    import shapely
    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    pairs = gpd.sjoin(lines[[by, "geometry"]], polygons, how="inner", predicate="intersects")
    out: dict[str, dict[str, float]] = {}
    for iso3, group in pairs.groupby("iso3"):
        poly = polygons.set_index("iso3").geometry[iso3]
        shapely.prepare(poly)
        geoms = lines.geometry.loc[group.index].values
        parts = np.where(shapely.contains(poly, geoms), geoms, shapely.intersection(geoms, poly))
        km = Counter()
        for cls, part in zip(group[by].astype(str), parts):
            km[cls] += geod.geometry_length(part) / 1000
        out[iso3] = {c: round(v, 1) for c, v in sorted(km.items())}
    return dict(sorted(out.items()))


def labels_for(fields: pd.DataFrame, layer: str) -> dict[str, str]:
    f = fields[fields["layer"] == layer]
    return {r.field: r.alias or r.field for r in f.itertuples()}


def feature(geom, props: dict) -> dict:
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(geom.x, DECIMALS),
                                                                             round(geom.y, DECIMALS)]},
            "properties": {k: v for k, v in props.items() if v is not None and v == v}}


def point_layer(spec: dict, frame: gpd.GeoDataFrame, polygons: gpd.GeoDataFrame, labels: dict) -> tuple[dict, dict]:
    """One point layer's GeoJSON and its catalogue entry. Withheld features are counted, never silently dropped."""
    frame = clean(frame)
    frame["geometry"] = frame.geometry.force_2d()
    # a row without a geometry is placed by the publisher's own decimal degrees, where it gives them
    empty = frame.geometry.is_empty | frame.geometry.isna()
    if empty.any() and {"Latitude", "Longitude"} <= set(frame.columns):
        lat, lon = (pd.to_numeric(frame.loc[empty, c], errors="coerce") for c in ("Latitude", "Longitude"))
        frame.loc[empty, "geometry"] = gpd.points_from_xy(lon, lat)
    by_degrees = int(empty.sum())
    frame = frame[~(frame.geometry.is_empty | frame.geometry.isna())]
    withheld = pd.Series(False, index=frame.index)
    for field, word in spec.get("withhold_where", {}).items():
        withheld |= frame[field].fillna("").astype(str).str.contains(word, case=False)
    kept = frame[~withheld].copy()
    kept["iso3"] = locate(kept, polygons)
    if "group_by" in spec:
        features = []
        for uid, rows in kept.groupby(spec["group_by"], sort=True):
            first = rows.iloc[0]
            props = {f: first[f] for f in spec["port_fields"]} | {"id": uid, "iso3": first["iso3"],
                     "rows": [{f: r[f] for f in spec["row_fields"] if r[f] is not None and r[f] == r[f]}
                              for _, r in rows.iterrows()]}
            features.append(feature(first.geometry, props))
        fields = spec["port_fields"] + spec["row_fields"]
    else:
        fields = spec["fields"]
        features = [feature(r.geometry, {f: r[f] for f in fields} | {"iso3": r["iso3"]}) for _, r in kept.iterrows()]
    entry = {"id": spec["id"], "title": spec["title"], "kind": "points", "file": f"{spec['id']}.json",
             "count": len(features), "rows": len(kept) if "group_by" in spec else None,
             "withheld": int(withheld.sum()), "withheld_reason": "stated source names SNL, a commercial database"
             if withheld.any() else None, "unplaced": int(kept["iso3"].isna().sum()),
             "placed_by_degrees": by_degrees or None,
             "fields": [{"name": f, "label": labels.get(f, f)} for f in fields],
             **{k: spec[k] for k in ("note", "licence", "attribution", "link")}}
    return {"type": "FeatureCollection", "features": features}, {k: v for k, v in entry.items() if v is not None}


def first_zooms(spec: dict, frame: pd.DataFrame) -> np.ndarray:
    rule = spec["first_zoom"]
    if "field" in rule:
        v = pd.to_numeric(frame[rule["field"]], errors="coerce").fillna(0).to_numpy()
        z = np.full(len(frame), MAX_ZOOM)
        for at_least, zoom in sorted(rule["at_least"], reverse=True):
            z = np.where((v >= at_least) & (z == MAX_ZOOM), zoom, z)
        return z
    if "default" in rule:
        return np.full(len(frame), rule["default"])
    unknown = sorted(set(frame[spec["class"]].dropna()) - set(rule))
    if unknown:
        raise ValueError(f"{spec['id']}: classes without a first zoom: {unknown}")
    return frame[spec["class"]].map(rule).to_numpy()


def main() -> int:
    from adapters import fetcher, sources
    from athena import dataset, geo
    from asi.tiles import Layer, build

    reg = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    ne = json.loads(fetcher().get(sources()["natural-earth-countries-50m"]["url"]))
    polygons = states(ne)
    OUT.mkdir(parents=True, exist_ok=True)
    catalogue = {"points": [], "lines": [], "archives": {}, "withheld": reg["withheld"]}
    summary: dict[str, dict] = {k: {} for k in sorted(COUNTRIES)}

    for spec in reg["points"]:
        fields = dataset.load(spec["dataset"], "fields") if spec["dataset"].startswith("usgs") else pd.DataFrame()
        doc, entry = point_layer(spec, geo.load(spec["dataset"], spec["layer"]), polygons,
                                 labels_for(fields, spec["layer"]) if len(fields) else {})
        (OUT / entry["file"]).write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n",
                                         encoding="utf-8", newline="\n")
        catalogue["points"].append(entry)
        for f in doc["features"]:
            p = f["properties"]
            if not p.get("iso3"):
                continue
            s = summary[p["iso3"]]
            if spec["id"] == "ports":
                s.setdefault("ports", []).append({"name": p.get("FeatureNam"), "type": p.get("FeatureTyp"),
                                                  "exports": sorted({r.get("DsgAttr03") for r in p["rows"]
                                                                     if r.get("DsgAttr03")})})
            elif spec["id"] == "facilities":
                s.setdefault("facilities", Counter())[p.get("DsgAttr01") or "unspecified"] += 1
            else:
                s[spec["id"]] = s.get(spec["id"], 0) + 1
        print(f"{entry['file']}: {entry['count']:,} features ({entry.get('withheld', 0)} withheld, "
              f"{entry['unplaced']} outside every member state)")

    archives: dict[str, list] = defaultdict(list)
    for spec in reg["lines"]:
        frame = clean(geo.load(spec["dataset"], spec["layer"]))
        frame["geometry"] = frame.geometry.force_2d()
        cls = spec.get("class") or "status"
        length = lengths(frame, polygons, cls)
        for iso3, by in length.items():
            summary[iso3].setdefault("km", {})[spec["id"]] = by
        zooms = first_zooms(spec, frame)
        keep = frame[list(spec["keep"]) + ["geometry"]].rename(columns=spec["keep"])
        split = spec.get("split_source")
        if split:
            osm = (frame[split["field"]] == split["value"]).to_numpy()
            archives[split["archive"]].append((Layer(spec["id"], keep[osm], zooms[osm]), spec))
            archives[spec["archive"]].append((Layer(spec["id"], keep[~osm], zooms[~osm]), spec))
        else:
            archives[spec["archive"]].append((Layer(spec["id"], keep, zooms), spec))
        catalogue["lines"].append({"id": spec["id"], "title": spec["title"], "kind": "lines", "count": len(frame),
                                   "classes": {str(k): int(v) for k, v in frame[cls].value_counts().items()},
                                   "class_field": spec["keep"].get(cls, cls),
                                   **{k: spec[k] for k in ("note", "licence", "attribution", "link")}})
        print(f"{spec['id']}: {len(frame):,} lines, length by state measured")
    for name, parts in archives.items():
        meta = {"name": name, "attribution": "; ".join(dict.fromkeys(p[1]["attribution"] for p in parts))}
        stats = build([p[0] for p in parts], MIN_ZOOM, MAX_ZOOM, OUT / f"{name}.pmtiles", meta)
        catalogue["archives"][name] = {"file": f"{name}.pmtiles", "layers": [p[0].name for p in parts],
                                       "licence": "ODbL 1.0" if name == "osm" else "CC BY 4.0",
                                       "attribution": meta["attribution"], "tiles": stats["tiles"]}
        print(f"{name}.pmtiles: {stats['tiles']:,} tiles, {(OUT / f'{name}.pmtiles').stat().st_size / 1e6:.1f} MB")

    for s in summary.values():
        if "facilities" in s:
            s["facilities"] = dict(s["facilities"].most_common())
    catalogue["rules"] = {"null": NULL, "nearest_km": NEAREST_KM, "zooms": [MIN_ZOOM, MAX_ZOOM],
                          "place": "a point is in the member state whose Natural Earth 1:50m polygon holds it, or the "
                                   f"nearest within {NEAREST_KM} km; a line's length counts toward each state by the "
                                   "part inside its polygon, on the WGS84 ellipsoid (derived)"}
    for path, doc in (("layers.json", catalogue), ("countries.json", summary)):
        (OUT / path).write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8",
                                newline="\n")
    print(f"layers.json, countries.json; {len(reg['withheld'])} layers withheld, each with its reason")
    return 0


if __name__ == "__main__":
    sys.exit(main())
