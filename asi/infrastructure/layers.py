"""The layers of the publication list, as the site reads them: one point layer's GeoJSON and catalogue entry; one
line layer's tile layers, catalogue entry and lengths; and each member state's summary for the country panel.

USGS writes a missing value as the text "<Null>", or "<null>" in some layers (the mineral facilities); either is read
as missing. Every field shown keeps the publisher's name, with its label (USGS's field aliases). A feature withheld by the list, or outside every member state, is
counted in the catalogue, never silently dropped.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

import geopandas as gpd
import numpy as np
import pandas as pd

from asi.infrastructure.places import LengthByState, PlaceInStates
from asi.infrastructure.tiles import MAX_ZOOM, Layer
from athena.component import Component

NULL, DECIMALS = "<Null>", 5
SHOWN = ("note", "licence", "attribution", "link")


def clean(frame: pd.DataFrame) -> pd.DataFrame:
    """The publisher's "<Null>", in any case, and empty text as missing; every other value is kept as written."""
    out = frame.copy()
    for column in out.columns:
        if column != "geometry" and (pd.api.types.is_string_dtype(out[column]) or out[column].dtype == object):
            text = out[column].astype(str)
            out[column] = out[column].where(~(text.str.fullmatch(r"(?i)<null>") | (text == "")), None)
    return out


def labels_for(fields: pd.DataFrame, layer: str) -> dict[str, str]:
    """Each field's label in a layer, from the dataset's `fields` table (USGS's aliases); the name where none."""
    f = fields[fields["layer"] == layer]
    return {r.field: r.alias or r.field for r in f.itertuples()}


def feature(geom, props: dict) -> dict:
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(geom.x, DECIMALS),
                                                                             round(geom.y, DECIMALS)]},
            "properties": {k: v for k, v in props.items() if v is not None and v == v}}


def first_zooms(spec: dict, frame: pd.DataFrame) -> np.ndarray:
    """Each line's first zoom, by the list's rule: one zoom for all, one per class, or thresholds on a field."""
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


class PointLayer(Component):
    """One point layer: its GeoJSON, and its catalogue entry with what was withheld, unplaced, placed by degrees, in
    a member state's waters, or in waters two states share or claim.

    The list may also say: `place: false` (the points belong to no state, as chokepoints); `only_placed: true` (a
    worldwide layer keeps only the points in a member state, counting the rest); `publisher_iso3: <field>` (a point
    counts for a member state only where its publisher names that state too; the others are listed, with both
    states, and belong to none); `name` (the field that names a point,
    FeatureNam by default); `labels` (each field's label, where the store has none); `id_field` (the field that
    keys `extra`, the values the stage adds to a point, such as its activity)."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        spec: dict                  # its entry in the publication list
        frame: gpd.GeoDataFrame     # the layer as the store holds it
        polygons: gpd.GeoDataFrame  # the member states
        labels: dict = field(default_factory=dict)
        waters: gpd.GeoDataFrame | None = None  # places.member_waters(...), for points at sea
        extra: dict = field(default_factory=dict)  # a point's id -> properties added to it
        others: gpd.GeoDataFrame | None = None  # places.other_polygons(...), every other state's land

    @dataclass(frozen=True)
    class Output:
        geojson: dict
        entry: dict

    def __init__(self, place: PlaceInStates | None = None):
        self.place = place or PlaceInStates()

    def run(self, inp: Input) -> Output:
        spec, frame = inp.spec, clean(inp.frame)
        frame["geometry"] = frame.geometry.force_2d()
        # a row without a geometry is placed by the publisher's own decimal degrees, where it gives them
        empty = frame.geometry.is_empty | frame.geometry.isna()
        if empty.any() and {"Latitude", "Longitude"} <= set(frame.columns):
            lat, lon = (pd.to_numeric(frame.loc[empty, c], errors="coerce") for c in ("Latitude", "Longitude"))
            frame.loc[empty, "geometry"] = gpd.points_from_xy(lon, lat)
        by_degrees = int(empty.sum())
        frame = frame[~(frame.geometry.is_empty | frame.geometry.isna())]
        withheld = pd.Series(False, index=frame.index)
        for column, word in spec.get("withhold_where", {}).items():
            withheld |= frame[column].fillna("").astype(str).str.contains(word, case=False)
        kept = frame[~withheld].copy()
        if spec.get("place", True):
            placed = self.place.run(PlaceInStates.Input(kept, inp.polygons, inp.waters, others=inp.others))
            kept["iso3"], how = placed.iso3, placed.how
        else:
            kept["iso3"], how = None, pd.Series("none", index=kept.index)
        differs = None
        if "publisher_iso3" in spec:   # a point counts for a member state only where its publisher names it too
            pub = spec["publisher_iso3"]
            other = kept["iso3"].notna() & (kept["iso3"] != kept[pub])
            differs = [f"{r[spec.get('name', 'FeatureNam')]}: {r[pub]} by the publisher, {r['iso3']} by the rule"
                       for _, r in kept[other].iterrows()]
            kept.loc[other, "iso3"] = None
        outside = None
        if spec.get("only_placed"):
            outside = int(kept["iso3"].isna().sum())
            kept, how = kept[kept["iso3"].notna()], how[kept["iso3"].notna()]
        shared = how[how.str.startswith("shared waters: ")].str.removeprefix("shared waters: ")
        if "group_by" in spec:
            features = []
            for uid, rows in kept.groupby(spec["group_by"], sort=True):
                first = rows.iloc[0]
                props = {f: first[f] for f in spec["port_fields"]} | {"id": uid, "iso3": first["iso3"],
                         "rows": [{f: r[f] for f in spec["row_fields"] if r[f] is not None and r[f] == r[f]}
                                  for _, r in rows.iterrows()]}
                features.append(feature(first.geometry, props | inp.extra.get(uid, {})))
            fields = spec["port_fields"] + spec["row_fields"]
        else:
            fields = spec["fields"]
            key = spec.get("id_field")
            features = [feature(r.geometry, {f: r[f] for f in fields} | {"iso3": r["iso3"]}
                                | (inp.extra.get(r[key], {}) if key else {})) for _, r in kept.iterrows()]
        labels = inp.labels | spec.get("labels", {})
        entry = {"id": spec["id"], "title": spec["title"], "kind": "points", "file": f"{spec['id']}.json",
                 "count": len(features), "rows": len(kept) if "group_by" in spec else None,
                 "name": spec.get("name", "FeatureNam"),
                 "withheld": int(withheld.sum()), "withheld_reason": "stated source names SNL, a commercial database"
                 if withheld.any() else None,
                 "unplaced": int(kept["iso3"].isna().sum()) if spec.get("place", True) else None,
                 "outside_member_states": outside, "placed_otherwise_than_publisher": differs,
                 "placed_by_degrees": by_degrees or None,
                 "placed_in_waters": int((how == "waters").sum()) or None,
                 "in_shared_waters": {k: int(v) for k, v in sorted(shared.value_counts().items())} or None,
                 "fields": [{"name": f, "label": labels.get(f, f)} for f in fields],
                 "activity": [{"name": c, "label": label} for c, label in spec["activity"]["columns"].items()]
                 if "activity" in spec else None,
                 **{k: spec[k] for k in SHOWN}}
        return self.Output({"type": "FeatureCollection", "features": features},
                           {k: v for k, v in entry.items() if v is not None})


class LineLayer(Component):
    """One line layer: its tile layers by archive (the lines under another licence kept apart), its catalogue entry,
    and its kilometres in each member state."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        spec: dict
        frame: gpd.GeoDataFrame
        polygons: gpd.GeoDataFrame

    @dataclass(frozen=True)
    class Output:
        tiles: list                 # (archive name, tiles.Layer), in the order they are written
        entry: dict
        km: dict                    # iso3 -> class -> kilometres

    def __init__(self, length: LengthByState | None = None):
        self.length = length or LengthByState()

    def run(self, inp: Input) -> Output:
        spec, frame = inp.spec, clean(inp.frame)
        frame["geometry"] = frame.geometry.force_2d()
        cls = spec.get("class") or "status"
        km = self.length.run(LengthByState.Input(frame, inp.polygons, cls)).km
        zooms = first_zooms(spec, frame)
        keep = frame[list(spec["keep"]) + ["geometry"]].rename(columns=spec["keep"])
        split = spec.get("split_source")
        if split:
            other = (frame[split["field"]] == split["value"]).to_numpy()
            tiles = [(split["archive"], Layer(spec["id"], keep[other], zooms[other])),
                     (spec["archive"], Layer(spec["id"], keep[~other], zooms[~other]))]
        else:
            tiles = [(spec["archive"], Layer(spec["id"], keep, zooms))]
        entry = {"id": spec["id"], "title": spec["title"], "kind": "lines", "count": len(frame),
                 "classes": {str(k): int(v) for k, v in frame[cls].value_counts().items()},
                 "class_field": spec["keep"].get(cls, cls), **{k: spec[k] for k in SHOWN}}
        return self.Output(tiles, entry, km)


class CountrySummary(Component):
    """Each member state's figures for the panel, by each point layer's `summary` rule in the list, then the
    kilometres of each line layer by class."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        specs: list                 # the point layers' entries in the list, in its order
        points: dict                # layer id -> its GeoJSON
        km: dict                    # line layer id -> iso3 -> class -> kilometres
        states: tuple               # the member states, in the order written

    @dataclass(frozen=True)
    class Output:
        countries: dict

    def run(self, inp: Input) -> Output:
        out: dict[str, dict] = {s: {} for s in inp.states}
        for spec in inp.specs:
            rule = spec.get("summary", {"count": True})
            for f in inp.points[spec["id"]]["features"]:
                p = f["properties"]
                if not p.get("iso3"):
                    continue
                s = out[p["iso3"]]
                if "each" in rule:   # one entry per feature: some of its properties, and values from its rows
                    each = rule["each"]
                    item = {k: p.get(v) for k, v in each["fields"].items()}
                    item |= {k: sorted({r.get(v) for r in p["rows"] if r.get(v)})
                             for k, v in each.get("from_rows", {}).items()}
                    s.setdefault(spec["id"], []).append(item)
                elif "count_by" in rule:
                    s.setdefault(spec["id"], Counter())[p.get(rule["count_by"]) or "unspecified"] += 1
                else:
                    s[spec["id"]] = s.get(spec["id"], 0) + 1
        for layer, by_state in inp.km.items():
            for iso3, by in by_state.items():
                out[iso3].setdefault("km", {})[layer] = by
        for s in out.values():
            for k, v in s.items():
                if isinstance(v, Counter):
                    s[k] = dict(v.most_common())
        return self.Output(out)
