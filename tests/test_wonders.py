"""07_wonders.py and athena.commons on invented records: the selection rule, and the licence check on photographs.
Each has a negative control. No Wikidata or Commons content is used."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("wonders_stage", ROOT / "07_wonders.py")
wonders = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wonders)  # puts athena-core on the path

from athena import commons  # noqa: E402


def item(qid, iso3, links, heritage=False, kind=None, name=None, coord="Point(1 2)"):
    return {"id": qid, "name": name or f"Place {qid}", "description": "", "countries": {iso3}, "links": links,
            "heritage": heritage, "kinds": {kind} if kind else set(), "coord": coord, "image": None, "category": None}


REGION = {"EGY": "Northern Africa", "MAR": "Northern Africa", "TZA": "Eastern Africa", "KEN": "Eastern Africa",
          "ZAF": "Southern Africa", "NGA": "Western Africa", "GHA": "Western Africa"}  # invented for the test


def test_the_rule_takes_the_most_notable_per_quota_and_every_region(monkeypatch):
    monkeypatch.setattr(wonders, "REGION", REGION)
    monkeypatch.setattr(wonders, "HERITAGE", 1)
    monkeypatch.setattr(wonders, "PER_CLASS", 1)
    found = {q["id"]: q for q in [
        item("Q1", "EGY", 300, heritage=True),           # North: the top heritage site
        item("Q2", "EGY", 200, heritage=True),           # second heritage site: beyond the quota of 1
        item("Q3", "TZA", 150, kind="Mountain"),         # East: top mountain
        item("Q4", "KEN", 100, kind="Mountain"),         # second mountain: beyond the quota
        item("Q5", "ZAF", 10, heritage=True),            # Southern Africa: kept only by the subregion rule
        item("Q6", "NGA", 999, kind="Lake", coord=None),  # no coordinates: left out
        item("Q7", "GHA", 500, kind="Lake", name="Q7"),   # no English name: left out
    ]}
    chosen = [c["id"] for c in wonders.select(found)]
    assert chosen == ["Q1", "Q3", "Q5"]


def test_the_owner_can_remove_or_add_a_wonder(monkeypatch):
    monkeypatch.setattr(wonders, "REGION", REGION)
    found = {q["id"]: q for q in [item("Q1", "EGY", 300, heritage=True), item("Q9", "MAR", 5)]}
    monkeypatch.setattr(wonders, "WONDERS_OWNER", {"Q1": "remove: a city, not a site", "Q9": "a local landmark"})
    chosen = [c["id"] for c in wonders.select(found)]
    assert "Q1" not in chosen and "Q9" in chosen


def response(pages, normalized=()):
    return {"query": {"normalized": [{"from": a, "to": b} for a, b in normalized], "pages": pages}}


def info(licence="CC BY-SA 4.0", thumb="https://x/330px-a.jpg"):
    meta = {"LicenseShortName": {"value": licence}, "Artist": {"value": "<a href='u'>A. Person</a>"}}
    return {"imageinfo": [{"thumburl": thumb, "descriptionurl": "https://c/File:A.jpg", "extmetadata": meta}]}


def test_a_photo_without_a_stated_licence_is_refused():
    kept, refused = commons.records(response({
        "1": {"title": "File:A.jpg", **info()},
        "2": {"title": "File:B.jpg", **info(licence="")},
        "3": {"title": "File:C.jpg", "missing": ""},
    }))
    assert list(kept) == ["File:A.jpg"]
    assert kept["File:A.jpg"]["artist"] == "A. Person"  # HTML stripped
    assert refused == {"File:B.jpg": "no stated licence", "File:C.jpg": "no such file"}


def test_commons_normalised_titles_map_back_to_the_requested_ones():
    kept, _ = commons.records(response({"1": {"title": "File:A b.jpg", **info()}}, normalized=[("File:A_b.jpg",
                                                                                                "File:A b.jpg")]))
    assert list(kept) == ["File:A_b.jpg"]
