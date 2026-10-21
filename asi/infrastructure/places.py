"""Which member state an infrastructure feature belongs to, by a stated rule (derived, P4).

- A point is in the member state whose Natural Earth 1:50m polygon holds it, or the nearest within `nearest_km`
  (ports sit on the coast, which the generalised polygons can miss); otherwise in none, and counted as unplaced. The
  distance is measured on the WGS84 ellipsoid: in an azimuthal equidistant projection centred on the point, where every
  distance from the centre is true, to the polygon densified every DENSIFY degrees.
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


class PlaceInStates(Component):
    """Each point's member state: the polygon that holds it, or the nearest within a stated distance."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        points: gpd.GeoDataFrame    # EPSG:4326
        polygons: gpd.GeoDataFrame  # `iso3` and `geometry`, EPSG:4326
        nearest_km: float = NEAREST_KM

    @dataclass(frozen=True)
    class Output:
        iso3: pd.Series             # on the points' index; missing where no member state is within reach

    def run(self, inp: Input) -> Output:
        inside = gpd.sjoin(inp.points[["geometry"]], inp.polygons, how="left", predicate="within")["iso3"]
        inside = inside[~inside.index.duplicated()].astype(object)
        for i in inside.index[inside.isna()]:
            inside.loc[i] = nearest_within(inp.points.geometry.loc[i], inp.polygons, inp.nearest_km)
        return self.Output(inside.reindex(inp.points.index))


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
