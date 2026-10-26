"""The links between states (`registry/links.yaml`, the owner's compilation, R5): who backs whom in Africa's conflicts.

`problems` checks the list before anything is drawn: its format; each link's states (the backer any state Natural
Earth names, the state supported a member state); its kind and status; at most two sentences in its card; every
source with its tier, publisher, title, address, date and the day it was read; at least one source of a tier that
qualifies a link (the rule, R7: a UN panel, the government concerned, or a UN human-rights investigation; news is
context only); and each panel report in the coverage list with how much of it has been read. `load` refuses a list
with any problem and names them all.

`LinkLines` draws each link as a great-circle line between the two states' Natural Earth label points (derived, P4:
the shortest path on the WGS84 ellipsoid, a drawing, not a route), carrying the card the site shows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pyproj import Geod

from athena.component import Component

FORMAT = "asi.links/2"
STATUS = ("confirmed", "reported")
SOURCE = ("tier", "publisher", "title", "url", "date", "read")
QUALIFYING = ("un-panel", "government", "un-rights")  # the tiers that qualify a link; "context" does not
COVERAGE = ("regime", "report", "date", "read")
READ = ("in full", "in part", "not yet")
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")
DECIMALS = 3


def sentences(text: str) -> int:
    """How many sentences a card holds: a full stop, question or exclamation mark followed by a capital starts one."""
    return len([s for s in SENTENCE.split(" ".join(str(text).split())) if s])


def problems(reg: dict, states: set[str], members: set[str]) -> list[str]:
    """What is wrong with a links list; empty when nothing is. `states` are the codes a backer may have, `members`
    the codes a supported state may have."""
    out = [] if reg.get("format") == FORMAT else [f"format must be {FORMAT}"]
    kinds = set(reg.get("kinds") or {})
    tiers = set(reg.get("tiers") or {})
    out += [f"tiers must name {t}" for t in (*QUALIFYING, "context") if t not in tiers]
    for i, c in enumerate(reg.get("coverage") or []):
        out += [f"coverage {i + 1} has no {k}" for k in COVERAGE if not c.get(k)]
        if c.get("read") and c["read"] not in READ:
            out.append(f"coverage {c.get('report', i + 1)}: read must be one of {READ}")
    ids: list[str] = []
    for link in reg.get("links") or []:
        who = link.get("id", "?")
        ids.append(who)
        for k in ("id", "from", "to", "conflict", "kind", "status", "since", "summary", "sources"):
            if not link.get(k):
                out.append(f"{who}: no {k}")
        if link.get("from") and link["from"] not in states:
            out.append(f"{who}: unknown backer {link['from']}")
        if link.get("to") and link["to"] not in members:
            out.append(f"{who}: {link['to']} is not a member state")
        if link.get("kind") and link["kind"] not in kinds:
            out.append(f"{who}: kind must be one of {sorted(kinds)}")
        if link.get("status") and link["status"] not in STATUS:
            out.append(f"{who}: status must be one of {STATUS}")
        if link.get("summary") and sentences(link["summary"]) > 2:
            out.append(f"{who}: the card has {sentences(link['summary'])} sentences; at most 2")
        for i, src in enumerate(link.get("sources") or []):
            out += [f"{who}: source {i + 1} has no {k}" for k in SOURCE if not src.get(k)]
            if src.get("tier") and src["tier"] not in tiers:
                out.append(f"{who}: source {i + 1}'s tier must be one of {sorted(tiers)}")
        if link.get("sources") and not any(s.get("tier") in QUALIFYING for s in link["sources"]):
            out.append(f"{who}: no source qualifies it (the rule: a UN panel, the government concerned, or a UN "
                       f"human-rights investigation; news is context only)")
    out += [f"{i}: listed twice" for i in sorted({i for i in ids if ids.count(i) > 1})]
    return out


def load(path: Path, states: set[str], members: set[str]) -> dict:
    """The links list, refused with every problem named when it has any."""
    reg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    found = problems(reg, states, members)
    if found:
        raise ValueError(f"{Path(path).name}: " + "; ".join(found))
    return reg


class LinkLines(Component):
    """Each link as a great-circle line between the two states' label points, with its card."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        links: list                 # the checked entries of registry/links.yaml
        points: dict                # each state's code -> (longitude, latitude), Natural Earth's label point
        names: dict = field(default_factory=dict)  # each state's code -> its name, for the card
        npts: int = 64              # points between the two ends

    @dataclass(frozen=True)
    class Output:
        geojson: dict               # one LineString per link, its card in the properties

    def run(self, inp: Input) -> Output:
        geod = Geod(ellps="WGS84")
        features = []
        for link in inp.links:
            (x1, y1), (x2, y2) = inp.points[link["from"]], inp.points[link["to"]]
            middle = geod.npts(x1, y1, x2, y2, inp.npts)
            line = [[round(x, DECIMALS), round(y, DECIMALS)] for x, y in [(x1, y1), *middle, (x2, y2)]]
            card = {k: link.get(k) for k in ("id", "from", "to", "actor", "conflict", "kind", "status", "since",
                                             "until", "sources")}
            card["summary"] = " ".join(str(link["summary"]).split())
            card["from_name"] = inp.names.get(link["from"], link["from"])
            card["to_name"] = inp.names.get(link["to"], link["to"])
            card["historical"] = bool(link.get("until"))
            features.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": line},
                             "properties": {k: v for k, v in card.items() if v is not None}})
        return self.Output({"type": "FeatureCollection", "features": features})
