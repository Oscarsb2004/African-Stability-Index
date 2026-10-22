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

import pandas as pd

from asi.infrastructure import registry
from asi.infrastructure.activity import YearlySums
from asi.infrastructure.layers import CountrySummary, LineLayer, PointLayer, first_zooms
from asi.infrastructure.places import LengthByState, PlaceInStates
from asi.infrastructure.ports import PortLinks
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


def test_at_sea_a_point_is_in_the_state_whose_waters_hold_it_and_in_none_where_they_are_shared(monkeypatch):
    def zone(box, sovereigns, kind="200NM", name="zone"):
        return {"type": "Feature", "geometry": shapely.geometry.mapping(shapely.box(*box)),
                "properties": {"pol_type": kind, "geoname": name, **{f"iso_sov{i}": s for i, s in
                                                                    enumerate(sovereigns, 1)}}}
    from asi.infrastructure.places import member_waters
    import asi.infrastructure.places as places
    eez = {"features": [zone((2, 0, 4, 0.5), ["AAA"]), zone((2, 0.5, 4, 1), ["AAA", "BBB"], "Overlapping claim",
                                                              "Overlapping claim: A / B")]}
    monkeypatch.setattr(places, "COUNTRIES", {"AAA": {}, "BBB": {}})  # the invented states are members here
    waters = member_waters(eez)
    got = PlaceInStates().run(PlaceInStates.Input(points((3, 0.25), (3, 0.75), (2.05, 0.75), (5, 5), (0.5, 0.5)),
                                                  POLYGONS, waters))
    # in AAA's waters, though BBB's land is nearer; in a claimed zone, none, even 5.6 km from BBB's coast
    assert got.how.tolist() == ["waters", "shared waters: Overlapping claim: A / B",
                                "shared waters: Overlapping claim: A / B", "none", "land"]
    assert got.iso3.tolist()[0] == "AAA" and got.iso3.isna().tolist() == [False, True, True, True, False]
    without = PlaceInStates().run(PlaceInStates.Input(points((2.05, 0.75)), POLYGONS)).iso3  # no waters given
    assert without.tolist() == ["BBB"]


def test_a_point_in_or_nearest_another_states_land_is_in_no_member_state():
    # ZZZ, not a member, lies east of BBB from 2.06° E; it shares no border with BBB
    others = gpd.GeoDataFrame({"iso3": ["ZZZ"]}, geometry=[shapely.box(2.06, 0, 3, 1)], crs=4326)
    pts = points((2.5, 0.5), (2.045, 0.5), (2.02, 0.5))
    got = PlaceInStates().run(PlaceInStates.Input(pts, POLYGONS, others=others))
    # inside ZZZ; at sea 1.7 km from ZZZ and 5 km from BBB; at sea, nearer BBB
    assert got.how.tolist() == ["another state: ZZZ", "another state: ZZZ", "near"]
    assert got.iso3.isna().tolist() == [True, True, False] and got.iso3.tolist()[2] == "BBB"
    without = PlaceInStates().run(PlaceInStates.Input(pts, POLYGONS)).iso3  # negative control: no other land given
    assert without.isna().tolist() == [True, False, False]  # the second point goes to BBB, the nearest member


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
             {"id": "facilities", "summary": {"count_by": "Type"}}, {"id": "deposits"},
             {"id": "pw", "summary": {"each": {"fields": {"name": "portname", "imports": "share"}}}}]
    docs = {"ports": fc({"iso3": "AAA", "FeatureNam": "P", "rows": [{"Com": "Zinc"}, {"Com": "Iron"}, {}]}),
            "facilities": fc({"iso3": "AAA", "Type": "Mine"}, {"iso3": "AAA"}, {"iso3": "AAA", "Type": "Mine"}),
            "deposits": fc({"iso3": "BBB"}, {"iso3": None}),  # a feature outside every state is not counted
            "pw": fc({"iso3": "BBB", "portname": "Q", "share": 61.5})}  # a point without rows
    out = CountrySummary().run(CountrySummary.Input(specs, docs, {"rail": {"BBB": {"railway": 12.5}}},
                                                    ("AAA", "BBB", "CCC"))).countries
    assert out == {"AAA": {"ports": [{"name": "P", "exports": ["Iron", "Zinc"]}],
                           "facilities": {"Mine": 2, "unspecified": 1}},
                   "BBB": {"deposits": 1, "pw": [{"name": "Q", "imports": 61.5}], "km": {"rail": {"railway": 12.5}}},
                   "CCC": {}}


def test_the_publication_list_states_every_licence_and_reason():
    reg = registry.load(ROOT / "registry" / "layers.yaml")  # the project's own list passes
    assert reg["points"] and reg["lines"] and all(w["reason"] for w in reg["withheld"])
    p = {s["id"]: s for s in reg["points"]}
    broken = {"format": "asi.layers/1", "points": [dict(p["ports"], licence=None, join={"to": "facilities"}),
                                                   dict(p["facilities"], summary={"median": "x"}),
                                                   dict(p["portwatch"], id_field=None)],
              "lines": [reg["lines"][0], reg["lines"][0]], "withheld": [{"layer": "X"}]}
    found = "; ".join(registry.problems(broken))
    for problem in ("points ports: no licence", "points facilities: summary must be one of", "rail: listed twice",
                    "withheld X: no reason", "points portwatch: activity needs an id_field",
                    "points ports: join must name a listed layer with activity"):
        assert problem in found


def test_a_worldwide_layer_keeps_the_member_states_points_and_lists_where_the_publisher_differs():
    frame = points((0.5, 0.5), (1.5, 0.5), (5.0, 5.0), portid=["p1", "p2", "p3"], portname=["A", "B", "Far"],
                   ISO3=["AAA", "AAA", "ZZZ"])
    spec = {"id": "pw", "title": "Port activity", "fields": ["portname"], "name": "portname", "id_field": "portid",
            "only_placed": True, "publisher_iso3": "ISO3", "labels": {"portname": "Port"},
            "activity": {"table": "t", "columns": {"calls": "Port calls"}}} | SHOWN
    out = PointLayer().run(PointLayer.Input(spec, frame, POLYGONS, extra={"p1": {"activity": {"years": [2020],
                                                                                              "calls": [3]}}}))
    props = {f["properties"]["portname"]: f["properties"] for f in out.geojson["features"]}
    # B: the rule says BBB, its publisher AAA, so it counts for neither; "Far" is in no member state; both counted
    assert set(props) == {"A"} and out.entry["outside_member_states"] == 2
    assert out.entry["placed_otherwise_than_publisher"] == ["B: AAA by the publisher, BBB by the rule"]
    assert props["A"]["activity"] == {"years": [2020], "calls": [3]} and props["A"]["iso3"] == "AAA"  # A agrees
    assert out.entry["fields"] == [{"name": "portname", "label": "Port"}] and out.entry["name"] == "portname"
    assert out.entry["activity"] == [{"name": "calls", "label": "Port calls"}]
    loose = PointLayer().run(PointLayer.Input({k: v for k, v in spec.items() if k != "publisher_iso3"}, frame,
                                              POLYGONS))
    assert {f["properties"]["portname"] for f in loose.geojson["features"]} == {"A", "B"}  # negative control


def test_points_that_belong_to_no_state_are_not_placed():
    frame = points((0.5, 0.5), portid=["c1"], portname=["Strait"])
    spec = {"id": "ck", "title": "Chokepoints", "fields": ["portname"], "place": False} | SHOWN
    out = PointLayer().run(PointLayer.Input(spec, frame, POLYGONS))
    assert "iso3" not in out.geojson["features"][0]["properties"] and "unplaced" not in out.entry
    placed = PointLayer().run(PointLayer.Input(spec | {"place": True}, frame, POLYGONS))
    assert placed.geojson["features"][0]["properties"]["iso3"] == "AAA"  # negative control: placed, it is in AAA


def test_activity_sums_only_complete_calendar_years():
    days = list(pd.date_range("2019-01-01", "2021-03-01", freq="D").strftime("%Y-%m-%d"))
    d = pd.DataFrame({"date": days * 2, "portid": ["p1"] * len(days) + ["p2"] * len(days), "calls": 1, "t": 2.5})
    d = d[~((d["portid"] == "p2") & (d["date"] == "2020-06-30"))]
    out = YearlySums().run(YearlySums.Input(d, "portid", ("calls", "t")))
    assert out.sums["p1"] == {"years": [2019, 2020], "calls": [365, 366], "t": [912.5, 915]}  # 2021 runs to March
    assert out.sums["p2"]["years"] == [2019]  # negative control: a year with a day missing is not a quiet year
    assert out.last_day == "2021-03-01"
    with pytest.raises(ValueError, match="twice"):
        YearlySums().run(YearlySums.Input(pd.concat([d, d.head(1)]), "portid", ("calls",)))


def test_a_usgs_port_is_linked_to_portwatch_only_by_published_keys():
    usgs = pd.DataFrame({"FeatureUID": ["u1", "u1", "u2", "u3", "u4", "u5", "u6", "u6"],
                         "DsgAttr10": ["100", "100", "<Null>", "200", "300", "500", "700", "701"]})
    codes = {100: "AAONE", 300: "AATHR", 500: "AAFIV"}
    pw = pd.DataFrame({"portid": ["p1", "p2", "p3", "p4"], "portname": ["One", "Five", "Five bis", "Two"],
                       "LOCODE": ["AA ONE", "AA FIV", "AAFIV", ""]})
    out = PortLinks().run(PortLinks.Input(usgs, "DsgAttr10", codes, (200,), pw))
    assert out.links == {"u1": {"portwatch": "p1", "portwatch_name": "One"}}  # "AA ONE" and "AAONE" are one code
    assert out.counts == {"linked": 1, "no WPI ID": 1, "two WPI IDs": 1, "WPI ID gives two LOCODEs": 1,
                          "WPI ID has no LOCODE": 0, "LOCODE not in PortWatch": 1, "LOCODE on two PortWatch ports": 1}
    # negative control: give 200 a single code and the chain reaches a port, but never by the name "Two"
    out = PortLinks().run(PortLinks.Input(usgs, "DsgAttr10", codes | {200: "AAONE"}, (), pw))
    assert out.links["u3"]["portwatch"] == "p1" and out.counts["linked"] == 2


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
