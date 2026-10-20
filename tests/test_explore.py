"""09_explore.py, the Data tab's files: the coverage floor, the projected years, the publisher's intervals, the
groups and their cross-check, on invented values; then the committed files against each other. Each rule has a
negative control."""

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("explore_stage", ROOT / "09_explore.py")
explore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(explore)  # puts athena-core on the path

from asi.core.countries import COUNTRIES  # noqa: E402

STATES = sorted(COUNTRIES)
OUT = ROOT / "web" / "public" / "data" / "explore"


def values(series: str, states: list[str], years=(2005, 2006), status="") -> pd.DataFrame:
    return pd.DataFrame([{"SERIES": series, "REF_AREA": a, "TIME_PERIOD": str(y), "OBS_VALUE": 1.23456 + i,
                          "OBS_STATUS": status} for i, a in enumerate(states) for y in years])


def run(frame: pd.DataFrame, name="wdi-2026-10-08", monkeypatch=None):
    monkeypatch.setattr(explore, "labels", lambda n: {})
    return explore.series_docs(name, frame)


def test_a_series_needs_the_floor_of_states_since_2000(monkeypatch):
    frame = pd.concat([values("WIDE", STATES[:explore.FLOOR]), values("NARROW", STATES[:explore.FLOOR - 1]),
                       values("OLD", STATES, years=(1990, 1999))])  # negative controls: too few, too early
    entries, files = run(frame, monkeypatch=monkeypatch)
    assert [e["code"] for e in entries] == ["WIDE"] and list(files) == ["wdi/WIDE"]
    doc = files["wdi/WIDE"]
    assert doc["y"] == [2005, 2006] and doc["v"][STATES[0]] == [1.235, 1.235]  # four significant figures


def test_states_outside_the_index_never_enter(monkeypatch):
    frame = pd.concat([values("S", STATES[:explore.FLOOR]), values("S", ["XXX"])])
    _, files = run(frame, monkeypatch=monkeypatch)
    assert "XXX" not in files["wdi/S"]["v"]


def test_the_first_projected_year_is_marked(monkeypatch):
    frame = pd.concat([values("G", STATES[:explore.FLOOR], years=(2024, 2025)),
                       values("G", STATES[:explore.FLOOR], years=(2026, 2027), status="F")])
    _, files = run(frame, name="weo-2026-10", monkeypatch=monkeypatch)
    assert files["weo/G"]["f"][STATES[0]] == 2  # 2026 is the third year from 2024
    _, files = run(values("H", STATES[:explore.FLOOR]), name="weo-2026-10", monkeypatch=monkeypatch)
    assert "f" not in files["weo/H"]  # negative control: nothing projected, nothing marked


def test_a_publishers_interval_travels_with_its_score(monkeypatch):
    frame = pd.concat([values("GOV_WGI_CC.SC", STATES[:explore.FLOOR]),
                       values("GOV_WGI_CC.SC_LB", STATES[:explore.FLOOR]),
                       values("GOV_WGI_CC.SC_UB", STATES[:explore.FLOOR])])
    entries, files = run(frame, name="wgi-2026-09-25", monkeypatch=monkeypatch)
    assert {e["code"]: e.get("interval") for e in entries}["GOV_WGI_CC.SC"] == "90%"
    assert "lo" in files["wgi/GOV_WGI_CC.SC"] and "lo" not in files["wgi/GOV_WGI_CC.SC_LB"]


def test_the_crosscheck_reports_each_difference_and_changes_nothing():
    recs = [{"id": "R", "wikidata": "Q1", "members": ["AAA", "BBB"]}]
    out = explore.crosscheck(recs, {"Q1": ["BBB", "CCC"]})
    assert out == [{"group": "R", "wikidata_count": 2, "owner_only": ["AAA"], "wikidata_only": ["CCC"]}]
    assert recs[0]["members"] == ["AAA", "BBB"]
    assert explore.crosscheck(recs, {"Q1": ["AAA", "BBB"]})[0]["owner_only"] == []  # negative control: agreement


def test_the_registry_holds_the_owners_eight_recs_and_only_index_states():
    reg = yaml.safe_load((ROOT / "registry" / "groups.yaml").read_text(encoding="utf-8"))
    counts = {g["id"]: len(g["members"]) for g in reg["recs"]}
    assert counts == {"UMA": 5, "CEN-SAD": 25, "COMESA": 21, "EAC": 8, "ECCAS": 10, "ECOWAS": 12, "IGAD": 6,
                      "SADC": 16}  # the owner's compilation, moved unchanged (P106)
    assert {a for g in reg["recs"] for a in g["members"]} <= set(COUNTRIES)
    assert {"BFA", "MLI", "NER"}.isdisjoint(next(g for g in reg["recs"] if g["id"] == "ECOWAS")["members"])


# ── the committed files, against each other ────────────────────────────────────────────────────────────────────

def test_every_listed_measure_has_its_file_and_every_file_is_listed():
    cat = json.loads((OUT / "catalogue.json").read_text(encoding="utf-8"))
    listed = {f"{e['ds']}/{explore.file_id(e['code'])}" for e in cat["measures"]}
    files = {f"{p.parent.name}/{p.stem}" for p in (OUT / "s").glob("*/*.json")}
    assert listed == files and set(cat["sources"]) >= {e["ds"] for e in cat["measures"]}


def test_the_data_tabs_headline_is_the_stability_panels():
    head = json.loads((OUT / "s" / "asi" / "headline.json").read_text(encoding="utf-8"))
    stab = json.loads((ROOT / "web" / "public" / "data" / "stability.json").read_text(encoding="utf-8"))
    at = stab["reference_year"] - head["y"][0]
    for iso3, c in stab["countries"].items():
        assert head["v"][iso3][at] == pytest.approx(c["composite"]["score"], rel=5e-4), iso3
        assert head["tier"][iso3][at] == c["composite"]["tier"], iso3


def test_no_category_singles_out_a_state_for_being_small_or_an_island():
    states = json.loads((OUT / "states.json").read_text(encoding="utf-8"))
    ids = {a["id"] for a in states["attributes"]}
    assert "island" in ids and not ids & {"region", "islands_excluded", "structurally_advantaged"}
    groups = json.loads((OUT / "groups.json").read_text(encoding="utf-8"))
    assert {g["kind"] for g in groups["groups"]} == {"rec", "organisation"}  # published groupings only
