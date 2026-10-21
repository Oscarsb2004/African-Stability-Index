"""The publication list (`registry/layers.yaml`): every layer the site publishes, with its licence and attribution,
and every layer withheld, with its reason. A layer not listed is not published.

`load` refuses a list with any problem, and names every problem together, so nothing is built from a half-stated
layer.
"""

from __future__ import annotations

from pathlib import Path

import yaml

FORMAT = "asi.layers/1"
EVERY = ("id", "title", "dataset", "layer", "note", "licence", "attribution", "link")
LINES = ("archive", "keep", "first_zoom")
SUMMARIES = ("count", "count_by", "each")


def problems(reg: dict) -> list[str]:
    """What is wrong with a publication list; empty when nothing is."""
    out = [] if reg.get("format") == FORMAT else [f"format must be {FORMAT}"]
    ids = []
    for kind in ("points", "lines"):
        for spec in reg.get(kind) or []:
            who = spec.get("id", "?")
            ids.append(who)
            out += [f"{kind} {who}: no {k}" for k in EVERY + (LINES if kind == "lines" else ()) if not spec.get(k)]
            summary = spec.get("summary", {"count": True})
            if kind == "points" and (len(summary) != 1 or next(iter(summary)) not in SUMMARIES):
                out.append(f"points {who}: summary must be one of {SUMMARIES}")
    out += [f"{i}: listed twice" for i in sorted({i for i in ids if ids.count(i) > 1})]
    out += [f"withheld {w.get('layer', '?')}: no reason" for w in reg.get("withheld") or [] if not w.get("reason")]
    return out


def load(path: Path) -> dict:
    reg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    found = problems(reg)
    if found:
        raise ValueError(f"{Path(path).name}: " + "; ".join(found))
    return reg
