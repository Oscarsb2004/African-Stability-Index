"""Vector tiles in one PMTiles archive, for the line layers too large to send whole (roads, rail, the grid).

Each layer is projected to Web Mercator once; at each zoom its features are simplified to about one tile unit
(1/4096 of a tile), clipped to each tile with a small buffer, encoded as Mapbox Vector Tiles (mapbox-vector-tile,
MIT), gzipped, and written in tile order into a PMTiles archive (pmtiles, BSD-3), which a static site serves whole
and the map reads by range requests. A feature enters at its own first zoom (a road's class, a line's voltage), so
the continent view stays light. Attributes are kept as given; nothing is merged, renamed or invented.
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import mapbox_vector_tile
import numpy as np
import shapely
from pmtiles.tile import Compression, TileType, tileid_to_zxy, zxy_to_tileid
from pmtiles.writer import Writer

EXTENT, BUFFER = 4096, 64
WORLD = 20037508.342789244  # half the Web Mercator world, in metres


@dataclass
class Layer:
    name: str
    frame: gpd.GeoDataFrame   # EPSG:4326, with only the attributes to publish
    first_zoom: np.ndarray    # each feature's first zoom


def tile_bounds(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    size = 2 * WORLD / 2 ** z
    minx, maxy = -WORLD + x * size, WORLD - y * size
    return minx, maxy - size, minx + size, maxy


def tiles_over(bounds: tuple[float, float, float, float], z: int) -> list[tuple[int, int]]:
    """The tiles at zoom z that a box in Web Mercator touches."""
    n, size = 2 ** z, 2 * WORLD / 2 ** z
    x0, x1 = (int((b + WORLD) // size) for b in (bounds[0], bounds[2]))
    y0, y1 = (int((WORLD - b) // size) for b in (bounds[3], bounds[1]))
    return [(x, y) for x in range(max(0, x0), min(n - 1, x1) + 1) for y in range(max(0, y0), min(n - 1, y1) + 1)]


def build(layers: list[Layer], min_zoom: int, max_zoom: int, path: Path, metadata: dict) -> dict:
    """Write the archive; return how many tiles and features each zoom holds."""
    projected = [(lay, lay.frame.to_crs(3857)) for lay in layers]
    tiles: dict[int, dict[str, list]] = {}
    stats = {}
    for z in range(min_zoom, max_zoom + 1):
        tolerance = 2 * WORLD / 2 ** z / EXTENT
        pad = 2 * WORLD / 2 ** z * BUFFER / EXTENT
        count = 0
        for lay, frame in projected:
            keep = lay.first_zoom <= z
            if not keep.any():
                continue
            geoms = shapely.simplify(frame.geometry.values[keep], tolerance)
            props = frame.drop(columns="geometry")[keep].to_dict("records")
            ok = ~shapely.is_empty(geoms)
            geoms, props = geoms[ok], [p for p, o in zip(props, ok) if o]
            tree = shapely.STRtree(geoms)
            for x, y in tiles_over(tuple(shapely.total_bounds(geoms)), z):
                b = tile_bounds(z, x, y)
                hit = tree.query(shapely.box(b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad))
                if not len(hit):
                    continue
                clipped = shapely.clip_by_rect(geoms[hit], b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad)
                feats = [{"geometry": g, "properties": {k: v for k, v in props[i].items() if v is not None and v == v}}
                         for g, i in zip(clipped, hit) if not g.is_empty]
                if feats:
                    tiles.setdefault(zxy_to_tileid(z, x, y), {}).setdefault(lay.name, []).extend(feats)
                    count += len(feats)
        stats[z] = count
    lon0, lat0, lon1, lat1 = gpd.GeoSeries(
        [shapely.box(*lay.frame.total_bounds) for lay in layers], crs=4326).total_bounds
    size = 0
    with path.open("wb") as f:
        writer = Writer(f)
        for tid in sorted(tiles):
            b = tile_bounds(*tileid_to_zxy(tid))
            data = mapbox_vector_tile.encode(
                [{"name": name, "features": feats} for name, feats in tiles[tid].items()],
                default_options={"quantize_bounds": b, "extents": EXTENT, "on_invalid_geometry": None})
            blob = gzip.compress(data, mtime=0)
            size += len(blob)
            writer.write_tile(tid, blob)
        writer.finalize({"tile_type": TileType.MVT, "tile_compression": Compression.GZIP,
                         "min_zoom": min_zoom, "max_zoom": max_zoom,
                         "min_lon_e7": int(lon0 * 1e7), "min_lat_e7": int(lat0 * 1e7),
                         "max_lon_e7": int(lon1 * 1e7), "max_lat_e7": int(lat1 * 1e7),
                         "center_zoom": min_zoom, "center_lon_e7": int((lon0 + lon1) / 2 * 1e7),
                         "center_lat_e7": int((lat0 + lat1) / 2 * 1e7)},
                        metadata | {"vector_layers": [{"id": lay.name, "fields": {c: "String" for c in lay.frame.columns
                                                                                 if c != "geometry"}} for lay in layers]})
    return {"tiles": len(tiles), "features_by_zoom": stats, "tile_bytes": size}
