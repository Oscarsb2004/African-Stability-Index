"""05_web.py: the map's geometry rules, on invented features. Natural Earth itself never enters the tests."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("web_stage", ROOT / "05_web.py")
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)

SQUARE = {"type": "Polygon", "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]]}
LINE = {"type": "LineString", "coordinates": [[10.0, 5.0], [11.0, 6.0]]}


def polygons(codes):
    return {"features": [{"geometry": SQUARE, "properties": {"ADM0_A3": c}} for c in codes]}


def test_every_member_state_is_drawn_and_merged_codes_take_the_member_code():
    members = [c for c in web.COUNTRIES if c not in ("SOM", "SSD")]
    out = web.countries(polygons(members + ["SOL", "SDS", "ESH", "FRA"]))["features"]
    codes = [f["properties"]["iso3"] for f in out]
    assert codes.count("SOM") == 1 and codes.count("SSD") == 1  # Somaliland as Somalia, SDS as South Sudan
    assert {"ESH"} == {f["properties"]["iso3"] for f in out if not f["properties"]["member"]}
    assert "FRA" not in codes
    # negative control: a member state without a polygon stops the build
    with pytest.raises(ValueError, match="no Natural Earth"):
        web.countries(polygons(members))


def test_lines_iso_does_not_recognise_are_dropped_and_disputed_ones_dashed():
    def line(cla, iso=None):
        return {"geometry": LINE, "properties": {"FEATURECLA": cla, "FCLASS_ISO": iso}}
    ne = {"features": [line("International boundary (verify)"), line("Disputed (please verify)"),
                       line("Line of control (please verify)", "Unrecognized"),
                       {"geometry": {"type": "LineString", "coordinates": [[120.0, 5.0], [121.0, 6.0]]},
                        "properties": {"FEATURECLA": "International boundary (verify)", "FCLASS_ISO": None}}]}
    out = web.borders(ne)["features"]
    assert [f["properties"]["dashed"] for f in out] == [False, True]  # the unrecognised and the Asian line are gone


def test_capitals_follow_the_class_and_a_merged_areas_capital_is_not_one():
    def place(name, code, cla, pop):
        return {"geometry": {"type": "Point", "coordinates": [1.0, 1.0]},
                "properties": {"name": name, "adm0_a3": code, "featurecla": cla, "adm0cap": 0, "pop_max": pop,
                               "min_zoom": 5.0}}
    ne = {"features": [place("Town", "SSD", "Populated place", 900), place("Juba", "SSD", "Admin-0 capital", 300),
                       place("Hargeisa", "SOL", "Admin-0 capital", 700), place("Paris", "FRA", "Admin-0 capital", 1)]}
    out = [f["properties"] for f in web.places(ne)["features"]]
    assert [(p["name"], p["capital"]) for p in out] == [("Juba", True), ("Town", False), ("Hargeisa", False)]
    assert out[2]["iso3"] == "SOM"
