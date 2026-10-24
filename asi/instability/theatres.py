"""The conflict theatres of the "Spreading instability" tab (`registry/theatres.yaml`, the owner's list): each a name,
its member states, a one-line description, the links (registry/links.yaml) and prediction markets that belong to it,
and links to control maps others publish (never reproduced). `load` refuses a list with any problem and names them
all, as the links list does.
"""

from __future__ import annotations

from pathlib import Path

import yaml

FORMAT = "asi.theatres/1"


def problems(reg: dict, members: set[str], link_ids: set[str]) -> list[str]:
    """What is wrong with a theatres list; empty when nothing is."""
    out = [] if reg.get("format") == FORMAT else [f"format must be {FORMAT}"]
    ids: list[str] = []
    for t in reg.get("theatres") or []:
        who = t.get("id", "?")
        ids.append(who)
        out += [f"{who}: no {k}" for k in ("id", "name", "states", "summary") if not t.get(k)]
        out += [f"{who}: {s} is not a member state" for s in t.get("states") or [] if s not in members]
        out += [f"{who}: no link {i} in registry/links.yaml" for i in t.get("links") or [] if i not in link_ids]
        for m in t.get("markets") or []:
            out += [f"{who}: a market has no {k}" for k in ("platform", "id", "question") if not m.get(k)]
        for m in t.get("maps") or []:
            out += [f"{who}: a map has no {k}" for k in ("title", "publisher", "url", "revised", "read") if not m.get(k)]
    out += [f"{i}: listed twice" for i in sorted({i for i in ids if ids.count(i) > 1})]
    return out


def load(path: Path, members: set[str], link_ids: set[str]) -> dict:
    """The theatres list, refused with every problem named when it has any."""
    reg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    found = problems(reg, members, link_ids)
    if found:
        raise ValueError(f"{Path(path).name}: " + "; ".join(found))
    return reg
