"""Which member state an infrastructure feature belongs to, by a stated rule (derived, P4).

- A point is in the member state whose Natural Earth 1:50m polygon holds it. Outside every polygon, it is in the
  member state whose waters hold it (an exclusive economic zone with a single sovereign, Marine Regions' World EEZ
  v12; the owner's ruling of 2026-10-21 for offshore facilities), or else the nearest within `nearest_km` (a point
  on land that the generalised polygons miss); otherwise in none, and counted as unplaced. A point in a zone two or
  more states claim, or share in a joint regime, belongs to none of them, and is counted with the zone's name. This
  says whose waters a point is in, not where any boundary lies in law. The distance is measured on the WGS84
  ellipsoid: in an azimuthal equidistant projection centred on the point, where every distance from the centre is
  true, to the polygon densified every DENSIFY degrees.
- A line's length counts toward each state by the part inside its polygon, measured on the WGS84 ellipsoid.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import geopandas as gpd
import numpy as np
import pandas as pd

from asi import geography
from asi.core.countries import COUNTRIES
from athena.component import Component

NEAREST_KM = 10
DENSIFY = 0.01  # degrees, about 1 km: a polygon's edges are curves once projected


def member_polygons(ne_countries: dict) -> gpd.GeoDataFrame:
    """The member states' Natural Earth polygons, one row each (`iso3`, `geometry`; EPSG:4326)."""
    features = [{"type": "Feature", "properties": {"iso3": geography.code(f["properties"])}, "geometry": f["geometry"]}
                for f in ne_countries["features"] if geography.code(f["properties"]) in COUNTRIES]
    return gpd.GeoDataFrame.from_features(features, crs=4326).dissolve("iso3").reset_index()


def member_waters(eez: dict) -> gpd.GeoDataFrame:
    """The zones of a World EEZ GeoJSON (Marine Regions) that involve member states: `iso3` for a zone with a single
    sovereign that is a member state, else none, with the zone's `name` and whether it is `shared` (an overlapping
    claim or a joint regime)."""
    rows = []
    for f in eez["features"]:
        p = f["properties"]
        sovereigns = [p.get(k) for k in ("iso_sov1", "iso_sov2", "iso_sov3") if p.get(k)]
        shared = p.get("pol_type") != "200NM" or len(sovereigns) > 1
        single = None if shared or sovereigns[0] not in COUNTRIES else sovereigns[0]
        rows.append({"type": "Feature", "geometry": f["geometry"],
                     "properties": {"iso3": single, "name": p.get("geoname", ""), "shared": shared}})
    return gpd.GeoDataFrame.from_features(rows, crs=4326)


class PlaceInStates(Component):
    """Each point's member state: the land that holds it, the waters that hold it, or the nearest land within a
    stated distance; and how it was placed."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        points: gpd.GeoDataFrame    # EPSG:4326
        polygons: gpd.GeoDataFrame  # `iso3` and `geometry`, EPSG:4326
        waters: gpd.GeoDataFrame | None = None  # member_waters(...); without it, only land and the nearest
        nearest_km: float = NEAREST_KM

    @dataclass(frozen=True)
    class Output:
        iso3: pd.Series             # on the points' index; missing where no member state holds or is near it
        how: pd.Series              # "land", "waters", "near", "shared waters: <zone>" or "none"

    def run(self, inp: Input) -> Output:
        inside = gpd.sjoin(inp.points[["geometry"]], inp.polygons, how="left", predicate="within")["iso3"]
        inside = inside[~inside.index.duplicated()].astype(object)
        how = pd.Series(np.where(inside.isna(), "none", "land"), index=inside.index, dtype=object)
        if inp.waters is not None and inside.isna().any():
            sea = gpd.sjoin(inp.points.loc[inside.isna(), ["geometry"]], inp.waters, how="inner", predicate="within")
            sea = sea[~sea.index.duplicated()]
            for i, zone in sea.iterrows():
                if zone["shared"]:
                    how.loc[i] = f"shared waters: {zone['name']}"
                elif zone["iso3"]:
                    inside.loc[i], how.loc[i] = zone["iso3"], "waters"
        for i in inside.index[inside.isna() & (how == "none")]:
            inside.loc[i] = nearest_within(inp.points.geometry.loc[i], inp.polygons, inp.nearest_km)
            if inside.loc[i] is not None:
                how.loc[i] = "near"
        return self.Output(inside.reindex(inp.points.index), how.reindex(inp.points.index))


def nearest_within(point, polygons: gpd.GeoDataFrame, km: float) -> str | None:
    """The member state nearest to a point outside every polygon, if one is within `km` on the WGS84 ellipsoid."""
    import shapely
    from pyproj import CRS, Transformer
    reach = km / (111.32 * np.cos(np.radians(min(abs(point.y), 80)))) * 1.5  # a box in degrees that holds `km`
    near = polygons[polygons.intersects(shapely.box(point.x - reach, point.y - reach, point.x + reach, point.y + reach))]
    if near.empty:
        return None
    aeqd = CRS.from_proj4(f"+proj=aeqd +lat_0={point.y} +lon_0={point.x} +datum=WGS84 +units=m")
    move = Transformer.from_crs(4326, aeqd, always_xy=True)
    centre, best = shapely.Point(0, 0), (km * 1000, None)
    for iso3, poly in zip(near["iso3"], near.geometry):
        part = shapely.segmentize(shapely.clip_by_rect(poly, point.x - reach, point.y - reach, point.x + reach,
                                                       point.y + reach), DENSIFY)
        d = shapely.transform(part, lambda xy: np.column_stack(move.transform(xy[:, 0], xy[:, 1]))).distance(centre)
        if d <= best[0]:
            best = (d, iso3)
    return best[1]


class LengthByState(Component):
    """Kilometres of line inside each member state, by a class column, on the WGS84 ellipsoid."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        lines: gpd.GeoDataFrame     # EPSG:4326, with the class column
        polygons: gpd.GeoDataFrame
        by: str

    @dataclass(frozen=True)
    class Output:
        km: dict                    # iso3 -> class -> kilometres, to 0.1 km

    def run(self, inp: Input) -> Output:
        import shapely
        from pyproj import Geod
        geod = Geod(ellps="WGS84")
        pairs = gpd.sjoin(inp.lines[[inp.by, "geometry"]], inp.polygons, how="inner", predicate="intersects")
        out: dict[str, dict[str, float]] = {}
        for iso3, group in pairs.groupby("iso3"):
            poly = inp.polygons.set_index("iso3").geometry[iso3]
            shapely.prepare(poly)
            geoms = inp.lines.geometry.loc[group.index].values
            parts = np.where(shapely.contains(poly, geoms), geoms, shapely.intersection(geoms, poly))
            km = Counter()
            for cls, part in zip(group[inp.by].astype(str), parts):
                km[cls] += geod.geometry_length(part) / 1000
            out[iso3] = {c: round(v, 1) for c, v in sorted(km.items())}
        return self.Output(dict(sorted(out.items())))
