"""asi.instability: the links registry's checks and the great-circle lines, on invented states; then the project's
own registry. Each rule has a negative control."""

import copy
from pathlib import Path

import yaml
from pyproj import Geod

from asi.core.countries import COUNTRIES
from asi.instability import links

ROOT = Path(__file__).resolve().parents[1]
SOURCE = {"publisher": "P", "title": "T", "url": "https://example.org", "date": "2024-01-01", "read": "2026-10-23"}
LINK = {"id": "x-aaa", "from": "XXX", "to": "AAA", "conflict": "C", "kind": "arms", "status": "reported",
        "since": "2023", "summary": "One sentence. Two sentences.", "sources": [SOURCE]}
REG = {"format": "asi.links/1", "kinds": {"arms": "Arms", "forces": "Forces"}, "links": [LINK]}


def test_a_link_needs_known_states_a_short_card_and_full_sources():
    assert links.problems(REG, {"XXX", "AAA"}, {"AAA"}) == []
    bad = copy.deepcopy(REG)
    bad["links"][0] |= {"from": "QQQ", "to": "XXX", "kind": "gifts", "status": "rumoured",
                        "summary": "One. Two. Three.", "sources": [{k: v for k, v in SOURCE.items() if k != "read"}]}
    bad["links"].append(dict(LINK))
    found = "; ".join(links.problems(bad, {"XXX", "AAA"}, {"AAA"}))
    for problem in ("unknown backer QQQ", "XXX is not a member state", "kind must be one of", "status must be one of",
                    "3 sentences", "source 1 has no read", "x-aaa: listed twice"):
        assert problem in found


def test_a_link_is_a_great_circle_between_label_points_carrying_its_card():
    pts = {"XXX": (0.0, 60.0), "AAA": (90.0, 60.0)}
    out = links.LinkLines().run(links.LinkLines.Input([LINK | {"until": "2024"}], pts, {"XXX": "Xland"},
                                                      npts=9)).geojson
    f = out["features"][0]
    line = f["geometry"]["coordinates"]
    assert len(line) == 11 and line[0] == [0.0, 60.0] and line[-1] == [90.0, 60.0]
    assert max(y for _, y in line) > 65  # the great circle bows toward the pole; a straight line on the map would not
    assert Geod(ellps="WGS84").line_length(*zip(*line)) < Geod(ellps="WGS84").line_length(
        *zip(*[[x, 60.0] for x in range(0, 91, 9)]))  # negative control: shorter than following the parallel
    assert f["properties"]["historical"] is True and f["properties"]["summary"] == "One sentence. Two sentences."
    assert (f["properties"]["from_name"], f["properties"]["to_name"]) == ("Xland", "AAA")  # a code where no name


def test_the_projects_links_pass_their_checks():
    reg = yaml.safe_load((ROOT / "registry" / "links.yaml").read_text(encoding="utf-8"))
    states = {l["from"] for l in reg["links"]} | set(COUNTRIES)
    assert links.problems(reg, states, set(COUNTRIES)) == []
    assert {l["id"] for l in reg["links"]} >= {"are-sdn-rsf", "rwa-cod-m23", "rus-mli", "eri-eth-tigray"}


# ── UCDP's events: months, spread and points, on invented events ──────────────────────────────────────────────
import pandas as pd  # noqa: E402

from asi.instability import theatres  # noqa: E402
from asi.instability.events import Months, Points, Spread, window  # noqa: E402


def events(*rows):
    cols = ["iso3", "date_start", "best", "adm_1", "side_a", "side_b", "longitude", "latitude", "type_of_violence",
            "code_status", "release"]
    return pd.DataFrame([dict(zip(cols, r)) for r in rows])


E = events(
    ("AAA", "2025-03-02", 4, "North", "Government of A", "Group X", 1.0, 2.0, 1, "Clear", "ged 1"),
    ("AAA", "2026-02-10", 6, "South", "Government of A", "Group X", 1.5, 2.5, 1, "Clear", "candidate 2"),
    ("BBB", "2026-03-01", 2, "East", "Group X", "Civilians", 3.0, 4.0, 3, "Check dyad", "candidate 2"),
    ("BBB", "2026-03-05", 0, "West", "Group Y", "XXX999", 3.1, 4.1, 2, "Clear", "candidate 2"),
    ("AAA", "2012-06-01", 1, "South", "Government of A", "Group Y", 1.0, 2.0, 1, "Clear", "ged 1"),
)


def test_deaths_are_summed_by_the_month_an_event_starts():
    out = Months().run(Months.Input(E, ("AAA", "BBB", "CCC"), "2026-01", "2026-03"))
    assert out.months == ["2026-01", "2026-02", "2026-03"]
    assert out.deaths == {"AAA": [0, 6, 0], "BBB": [0, 0, 2], "CCC": [0, 0, 0]}  # a state without events counts 0


def test_spread_counts_areas_and_an_identified_groups_new_ground():
    assert window("2026-03") == ("2025-04", "2026-03")
    out = Spread().run(Spread.Input(E, ("AAA", "BBB"), "2026-03"))
    assert (out.areas_now, out.areas_before) == (2, 1)  # South and East now (West had no deaths); North before
    # Group X and Group Y are new in BBB (Group Y fought only in AAA before), the more deaths first
    assert [(g["actor"], g["iso3"]) for g in out.new_ground] == [("Group X", "BBB"), ("Group Y", "BBB")]
    # negative controls: Group X in AAA is not new (it fought there in 2025, before the window); an unidentified XXX
    # group and the civilians are never listed
    assert ("Group X", "AAA") not in [(g["actor"], g["iso3"]) for g in out.new_ground]
    assert not any(g["actor"].startswith("XXX") or g["actor"] == "Civilians" for g in out.new_ground)


def test_points_keep_the_window_and_never_the_news():
    out = Points().run(Points.Input(E, ("AAA", "BBB"), "2026-03")).geojson
    assert len(out["features"]) == 3  # 2025-03-02 is outside the window
    p = out["features"][-1]["properties"]
    assert p["type"] == "state-based" and p["best"] == 6 and "source_article" not in p


def test_a_theatre_needs_member_states_and_known_links():
    reg = {"format": "asi.theatres/1", "theatres": [{"id": "t", "name": "T", "states": ["AAA", "ZZZ"],
                                                     "summary": "S", "links": ["nope"], "markets": [{"platform": "p"}]}]}
    found = "; ".join(theatres.problems(reg, {"AAA"}, {"x-aaa"}))
    for problem in ("ZZZ is not a member state", "no link nope", "a market has no id"):
        assert problem in found
    project = yaml.safe_load((ROOT / "registry" / "theatres.yaml").read_text(encoding="utf-8"))
    links_ids = {l["id"] for l in yaml.safe_load((ROOT / "registry" / "links.yaml").read_text(encoding="utf-8"))["links"]}
    assert theatres.problems(project, set(COUNTRIES), links_ids) == []  # the project's own list passes
