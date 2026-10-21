"""asi.infrastructure: the publication list, the placement rule, the point and line layers, the country summary and
the vector tiles, each on synthetic geometry with a negative control. Two invented states sit side by side on the
equator: AAA from 0° to 1° east, BBB from 1° to 2° east."""

import gzip
from pathlib import Path

import geopandas as gpd
import mapbox_vector_tile
import numpy as np
import pytest
import shapely
from pmtiles.reader import MemorySource, Reader, all_tiles
from pyproj import Geod

from asi.infrastructure import registry
from asi.infrastructure.layers import CountrySummary, LineLayer, PointLayer, first_zooms
from asi.infrastructure.places import LengthByState, PlaceInStates
from asi.infrastructure.tiles import Layer, VectorTiles

ROOT = Path(__file__).resolve().parents[1]
POLYGONS = gpd.GeoDataFrame({"iso3": ["AAA", "BBB"]}, geometry=[shapely.box(0, 0, 1, 1), shapely.box(1, 0, 2, 1)],
                            crs=4326)
SHOWN = {"note": "n", "licence": "l", "attribution": "a", "link": "k"}


def points(*xy, **columns) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(columns, geometry=[shapely.Point(x, y) if x is not None else shapely.Point()
                                               for x, y in xy], crs=4326)


def test_a_point_is_in_the_state_that_holds_it_or_the_nearest_within_reach():
    got = PlaceInStates().run(PlaceInStates.Input(points((0.5, 0.5), (2.05, 0.5), (2.5, 0.5)), POLYGONS)).iso3
    # inside AAA; about 5.6 km east of BBB's coast; about 56 km east of it, beyond reach
    assert got.tolist()[:2] == ["AAA", "BBB"] and got.isna().tolist() == [False, False, True]


@pytest.mark.parametrize("lat", [0.5, 34.5])
def test_the_reach_is_ten_kilometres_on_the_ellipsoid_at_any_latitude(lat):
    # a state whose east coast is at 2° E; points due east of it at exact distances on the WGS84 ellipsoid
    state = gpd.GeoDataFrame({"iso3": ["CCC"]}, geometry=[shapely.box(1, lat - 0.5, 2, lat + 0.5)], crs=4326)
    geod = Geod(ellps="WGS84")
    east = [geod.fwd(2, lat, 90, metres)[:2] for metres in (9_500, 10_500, 13_400)]
    got = PlaceInStates().run(PlaceInStates.Input(points(*east), state)).iso3
    assert got.tolist()[0] == "CCC" and got.isna().tolist() == [False, True, True]  # beyond 10 km, in none


def test_a_lines_length_counts_toward_each_state_by_the_part_inside_it():
    lines = gpd.GeoDataFrame({"cls": ["Road", "Road"]}, geometry=[shapely.LineString([(0.5, 0.5), (1.5, 0.5)]),
                                                                  shapely.LineString([(5, 5), (6, 5)])], crs=4326)
    km = LengthByState().run(LengthByState.Input(lines, POLYGONS, "cls")).km
    half = Geod(ellps="WGS84").line_length([0.5, 1.0], [0.5, 0.5]) / 1000
    assert km == {"AAA": {"Road": round(half, 1)}, "BBB": {"Road": round(half, 1)}}  # the line outside counts nowhere


def test_a_point_layer_reads_nulls_places_by_degrees_and_counts_what_it_withholds():
    frame = points((0.5, 0.5), (0.6, 0.6), (None, None), (1.5, 0.5),
                   FeatureNam=["Alpha", "<Null>", "Gamma", "Delta"], InfSource1=["USGS", "USGS", "USGS", "SNL Metals"],
                   Owner=["<null>", "NA", "", "X"],  # either spelling of the marker is missing; "NA" is text
                   Latitude=[None, None, "0.4", None], Longitude=[None, None, "1.4", None])
    spec = {"id": "mines", "title": "Mines", "fields": ["FeatureNam", "Owner"], "withhold_where": {"InfSource1": "SNL"}} | SHOWN
    out = PointLayer().run(PointLayer.Input(spec, frame, POLYGONS, {"FeatureNam": "Name"}))
    names = [f["properties"].get("FeatureNam") for f in out.geojson["features"]]
    assert names == ["Alpha", None, "Gamma"] and "Delta" not in names  # the withheld row never appears
    assert [f["properties"].get("Owner") for f in out.geojson["features"]] == [None, "NA", None]
    assert [f["properties"]["iso3"] for f in out.geojson["features"]] == ["AAA", "AAA", "BBB"]
    assert {k: out.entry[k] for k in ("count", "withheld", "placed_by_degrees", "unplaced")} == \
        {"count": 3, "withheld": 1, "placed_by_degrees": 1, "unplaced": 0}
    assert out.entry["fields"][0] == {"name": "FeatureNam", "label": "Name"} and out.entry["licence"] == "l"


def test_ports_are_one_point_each_with_a_row_per_commodity():
    frame = points((0.5, 0.5), (0.5, 0.5), (1.5, 0.5), FeatureUID=["p1", "p1", "p2"], FeatureNam=["Port A"] * 2 + ["B"],
                   DsgAttr03=["Copper", "Cobalt", "<Null>"])
    spec = {"id": "ports", "title": "Ports", "group_by": "FeatureUID", "port_fields": ["FeatureNam"],
            "row_fields": ["DsgAttr03"]} | SHOWN
    out = PointLayer().run(PointLayer.Input(spec, frame, POLYGONS))
    rows = {f["properties"]["id"]: f["properties"]["rows"] for f in out.geojson["features"]}
    assert rows == {"p1": [{"DsgAttr03": "Copper"}, {"DsgAttr03": "Cobalt"}], "p2": [{}]}
    assert (out.entry["count"], out.entry["rows"]) == (2, 3)


def test_first_zooms_follow_the_rule_and_an_unlisted_class_stops_the_build():
    frame = gpd.GeoDataFrame({"cls": ["Trunk", "Minor"], "kv": [330, 11]})
    assert first_zooms({"id": "r", "class": "cls", "first_zoom": {"Trunk": 4, "Minor": 8}}, frame).tolist() == [4, 8]
    assert first_zooms({"id": "g", "first_zoom": {"field": "kv", "at_least": [[220, 3], [0, 7]]}}, frame).tolist() == [3, 7]
    with pytest.raises(ValueError, match=r"classes without a first zoom: \['Minor'\]"):
        first_zooms({"id": "r", "class": "cls", "first_zoom": {"Trunk": 4}}, frame)


def test_a_line_layer_keeps_the_lines_under_another_licence_in_their_own_archive():
    frame = gpd.GeoDataFrame({"status": ["Existing", "Planned", "Existing"], "source": ["OSM", "Utility", "Utility"]},
                             geometry=[shapely.LineString([(0.2, 0.2), (0.8, 0.2)])] * 3, crs=4326)
    spec = {"id": "grid", "title": "Grid", "archive": "grid", "keep": {"status": "status"},
            "split_source": {"field": "source", "value": "OSM", "archive": "osm"}, "first_zoom": {"default": 3}} | SHOWN
    out = LineLayer().run(LineLayer.Input(spec, frame, POLYGONS))
    assert [(a, len(layer.frame)) for a, layer in out.tiles] == [("osm", 1), ("grid", 2)]
    assert out.entry["classes"] == {"Existing": 2, "Planned": 1} and set(out.km) == {"AAA"}


def test_the_country_summary_follows_each_layers_rule():
    def fc(*props):
        return {"features": [{"properties": p} for p in props]}
    specs = [{"id": "ports", "summary": {"each": {"fields": {"name": "FeatureNam"}, "from_rows": {"exports": "Com"}}}},
             {"id": "facilities", "summary": {"count_by": "Type"}}, {"id": "deposits"}]
    docs = {"ports": fc({"iso3": "AAA", "FeatureNam": "P", "rows": [{"Com": "Zinc"}, {"Com": "Iron"}, {}]}),
            "facilities": fc({"iso3": "AAA", "Type": "Mine"}, {"iso3": "AAA"}, {"iso3": "AAA", "Type": "Mine"}),
            "deposits": fc({"iso3": "BBB"}, {"iso3": None})}  # a feature outside every state is not counted
    out = CountrySummary().run(CountrySummary.Input(specs, docs, {"rail": {"BBB": {"railway": 12.5}}},
                                                    ("AAA", "BBB", "CCC"))).countries
    assert out == {"AAA": {"ports": [{"name": "P", "exports": ["Iron", "Zinc"]}],
                           "facilities": {"Mine": 2, "unspecified": 1}},
                   "BBB": {"deposits": 1, "km": {"rail": {"railway": 12.5}}}, "CCC": {}}


def test_the_publication_list_states_every_licence_and_reason():
    reg = registry.load(ROOT / "registry" / "layers.yaml")  # the project's own list passes
    assert reg["points"] and reg["lines"] and all(w["reason"] for w in reg["withheld"])
    broken = {"format": "asi.layers/1", "points": [dict(reg["points"][0], licence=None),
                                                   dict(reg["points"][1], summary={"median": "x"})],
              "lines": [reg["lines"][0], reg["lines"][0]], "withheld": [{"layer": "X"}]}
    found = "; ".join(registry.problems(broken))
    for problem in ("points ports: no licence", "points facilities: summary must be one of", "rail: listed twice",
                    "withheld X: no reason"):
        assert problem in found


def test_vector_tiles_hold_each_line_from_its_first_zoom(tmp_path):
    lines = gpd.GeoDataFrame({"class": ["trunk", "minor"]}, geometry=[shapely.LineString([(0.1, 0.5), (0.9, 0.5)]),
                                                                      shapely.LineString([(0.1, 0.6), (0.9, 0.6)])],
                             crs=4326)
    path = tmp_path / "t.pmtiles"
    stats = VectorTiles().run(VectorTiles.Input([Layer("roads", lines, np.array([3, 5]))], path, {"name": "t"}, 3, 5))
    by_zoom: dict[int, set] = {}
    for (z, _, _), data in all_tiles(MemorySource(path.read_bytes())):
        decoded = mapbox_vector_tile.decode(gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data)
        by_zoom.setdefault(z, set()).update(f["properties"]["class"] for f in decoded["roads"]["features"])
    assert by_zoom == {3: {"trunk"}, 4: {"trunk"}, 5: {"trunk", "minor"}}  # the minor road enters at zoom 5
    assert stats.tiles == sum(1 for _ in all_tiles(MemorySource(path.read_bytes())))
    assert Reader(MemorySource(path.read_bytes())).header()["max_zoom"] == 5
