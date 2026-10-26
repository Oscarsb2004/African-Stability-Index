"""asi.instability: the links registry's checks and the great-circle lines, on invented states; then the project's
own registry. Each rule has a negative control."""

import copy
from pathlib import Path

import yaml
from pyproj import Geod

from asi.core.countries import COUNTRIES
from asi.instability import links

ROOT = Path(__file__).resolve().parents[1]
SOURCE = {"tier": "un-panel", "publisher": "P", "title": "T", "url": "https://example.org", "date": "2024-01-01",
          "read": "2026-10-23"}
LINK = {"id": "x-aaa", "from": "XXX", "to": "AAA", "conflict": "C", "kind": "arms", "status": "reported",
        "since": "2023", "summary": "One sentence. Two sentences.", "sources": [SOURCE]}
TIERS = {"un-panel": "Panel", "government": "Government", "un-rights": "Rights", "context": "Context"}
REG = {"format": "asi.links/2", "kinds": {"arms": "Arms", "forces": "Forces"}, "tiers": TIERS,
       "coverage": [{"regime": "Aland", "report": "S/2099/1", "date": "2099-01-01", "read": "not yet"}],
       "links": [LINK]}


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


def test_a_link_needs_a_qualifying_source_and_coverage_says_what_is_read():
    news = copy.deepcopy(REG)
    news["links"][0]["sources"] = [SOURCE | {"tier": "context"}]  # negative control: news alone
    news["coverage"][0]["read"] = "skimmed"
    news["links"][0]["sources"].append(SOURCE | {"tier": "rumour"})
    found = "; ".join(links.problems(news, {"XXX", "AAA"}, {"AAA"}))
    assert "x-aaa: no source qualifies it" in found and "read must be one of" in found
    assert "source 2's tier must be one of" in found
    for tier in links.QUALIFYING:  # each qualifying tier is enough on its own
        ok = copy.deepcopy(REG)
        ok["links"][0]["sources"] = [SOURCE | {"tier": "context"}, SOURCE | {"tier": tier}]
        assert links.problems(ok, {"XXX", "AAA"}, {"AAA"}) == []


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
    assert len(reg["coverage"]) == 7  # the six regimes in force and Mali's, ended in 2023
