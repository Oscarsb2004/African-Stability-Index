"""
08_narratives.py — each country's data narrative: what its scores say, in sentences (edition 2, step 10).

Every sentence comes from a stated template filled with numbers from the panel; nothing is written by hand or by a
model, so `verify/narrative.py` can re-derive every number in the text. The researched texts that gave context
(history, colonial legacy, recent events) were archived at P3 (C2); what replaces them is the owner's to rule.

    python 08_narratives.py        # reads data/panel, writes data/panel/narratives.json

At the reference year, for a state with a headline:
- its score, the 95% interval, its tier and its rank band;
- its two strongest and two weakest pillars, as distance from the median state's score on that pillar;
- the change since ten years before, and the pillar that changed most;
- how many pillars entered, which were left out, and the lack-of-reliability index against the median.
A state without a headline gets one sentence saying why.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from asi.core.constants import HEADLINE_METHOD, MIN_PILLARS_FOR_COMPOSITE, PILLAR_DEFS

PANEL = Path("data/panel")
SPAN = 10                      # the change is measured over this many years
COMPOSABLE = ("reliable", "thin")


def one(x: float) -> str:
    """Every number in the text has one decimal."""
    return f"{x:.1f}"


def facts(comp: pd.DataFrame, pil: pd.DataFrame, year: int) -> dict[str, dict]:
    """The facts each country's sentences are made from, keyed by ISO3."""
    head = comp[comp["method"] == HEADLINE_METHOD]
    now = head[head["year"] == year].set_index("iso3")
    ranked = now[now["rank"].notna()]
    then = head[(head["year"] == year - SPAN) & head["rank"].notna()].set_index("iso3")
    used = pil[pil["reliability"].isin(COMPOSABLE) & pil["score"].notna()]
    used_now = used[used["year"] == year]
    median = used_now[used_now["iso3"].isin(ranked.index)].groupby("pillar_id")["score"].median()
    out = {}
    for iso3, row in now.iterrows():
        if pd.isna(row["rank"]):
            out[iso3] = {"headline": False, "n_pillars": int(row["n_pillars"])}
            continue
        mine = used_now[used_now["iso3"] == iso3].set_index("pillar_id")["score"]
        gap = (mine - median.reindex(mine.index)).sort_values(kind="mergesort")
        f = {"headline": True, "score": float(row["score"]), "ci_low": float(row["ci_low"]),
             "ci_high": float(row["ci_high"]), "tier": int(row["tier"]), "band_best": int(row["band_best"]),
             "band_worst": int(row["band_worst"]), "n_pillars": int(row["n_pillars"]),
             "lack_of_reliability": float(row["lack_of_reliability"]),
             "above": [[p, float(mine[p]), float(median[p])] for p in gap[gap > 0].index[::-1][:2]],
             "below": [[p, float(mine[p]), float(median[p])] for p in gap[gap < 0].index[:2]],
             "left_out": sorted(set(pil[(pil["iso3"] == iso3) & (pil["year"] == year) & pil["score"].notna()
                                       & ~pil["reliability"].isin(COMPOSABLE)]["pillar_id"]))}
        if iso3 in then.index:
            before = used[(used["iso3"] == iso3) & (used["year"] == year - SPAN)].set_index("pillar_id")["score"]
            both = mine.index.intersection(before.index)
            moved = (mine[both] - before[both]).abs().sort_values(ascending=False, kind="mergesort")
            f["change"] = {"from_year": year - SPAN, "from": float(then.loc[iso3, "score"]),
                           "pillar": moved.index[0], "pillar_from": float(before[moved.index[0]]),
                           "pillar_to": float(mine[moved.index[0]])} if len(moved) else None
        out[iso3] = f
    return out


def sentences(name: str, f: dict, year: int, n: int, n_tiers: int, lri_median: float) -> list[str]:
    if not f["headline"]:
        return [f"{name} has no headline score in {year}: fewer than {MIN_PILLARS_FOR_COMPOSITE} of its pillars "
                f"were measured well enough to show ({f['n_pillars']} were)."]
    def pillars(found: list) -> str:
        return " and ".join(f"{PILLAR_DEFS[p]} ({one(s)}, against {one(m)})" for p, s, m in found)

    above, below = f["above"], f["below"]
    out = [f"{name} scores {one(f['score'])} of 100 in {year}, with a 95% interval of {one(f['ci_low'])} to "
           f"{one(f['ci_high'])}.",
           f"That puts it in tier {f['tier']} of {n_tiers}: its rank could be anywhere from {f['band_best']} to "
           f"{f['band_worst']} of {n}.",
           (f"Its {'pillars' if len(above) > 1 else 'pillar'} furthest above the median state "
            f"{'are' if len(above) > 1 else 'is'} {pillars(above)}." if above
            else "None of its pillars is above the median state."),
           (f"Furthest below {'are' if len(below) > 1 else 'is'} {pillars(below)}." if below
            else "None is below it.")]
    change = f.get("change")
    if change:
        out.append(f"Since {change['from_year']} its score has moved from {one(change['from'])} to "
                   f"{one(f['score'])}; the pillar that moved most is {PILLAR_DEFS[change['pillar']]}, from "
                   f"{one(change['pillar_from'])} to {one(change['pillar_to'])}.")
    left = [PILLAR_DEFS[p] for p in f["left_out"]]
    out.append(f"The score uses {f['n_pillars']} of the {len(PILLAR_DEFS)} pillars"
               + (f"; {' and '.join(left)} {'was' if len(left) == 1 else 'were'} left out, measured too thinly "
                  f"that year to show." if left else "."))
    out.append(f"Its lack-of-reliability index is {one(f['lack_of_reliability'])} of 10, where 0 means every value "
               f"was measured that year, against a median of {one(lri_median)}.")
    return out


def build(panel: Path = PANEL) -> dict:
    comp = pd.read_csv(panel / "composites.csv")
    pil = pd.read_csv(panel / "pillar_scores.csv")
    year = int(yaml.safe_load((panel / "panel_meta.yaml").read_text(encoding="utf-8"))["reference_year"])
    names = {k: v["name"] for k, v in json.loads((panel / "bundle.json").read_text(encoding="utf-8"))
             ["countries"].items()}
    found = facts(comp, pil, year)
    ranked = {k: f for k, f in found.items() if f["headline"]}
    n, n_tiers = len(ranked), max(f["tier"] for f in ranked.values())
    lri_median = float(np.median([f["lack_of_reliability"] for f in ranked.values()]))
    return {"year": year, "n_ranked": n, "n_tiers": n_tiers, "lri_median": lri_median,
            "note": "Each sentence is a stated template filled with numbers from the panel (08_narratives.py); "
                    "verify/narrative.py re-derives every number.",
            "countries": {k: {"name": names[k], "facts": found[k],
                              "text": sentences(names[k], found[k], year, n, n_tiers, lri_median)}
                          for k in sorted(found)}}


def main() -> int:
    doc = build()
    (PANEL / "narratives.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                           newline="\n")
    print(f"{PANEL / 'narratives.json'}: {len(doc['countries'])} countries at {doc['year']}, "
          f"{doc['n_ranked']} with a headline, {doc['n_tiers']} tiers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
