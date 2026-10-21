"""Which member state an infrastructure feature belongs to, by a stated rule (derived, P4).

- A point is in the member state whose Natural Earth 1:50m polygon holds it, or the nearest within `nearest_km`
  (ports sit on the coast, which the generalised polygons can miss); otherwise in none, and counted as unplaced.
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
        inside = inside[~inside.index.duplicated()]
        missing = inside.isna()
        if missing.any():
            near = gpd.sjoin_nearest(inp.points.loc[missing, ["geometry"]].to_crs(3857), inp.polygons.to_crs(3857),
                                     how="left", max_distance=inp.nearest_km * 1000 * 1.6)["iso3"]
            inside.loc[near.index] = near[~near.index.duplicated()]  # Web Mercator stretches by up to 1.6
        return self.Output(inside.reindex(inp.points.index))


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
