"""
verify/narrative.py — every number in the data narratives is the panel's (edition 2, step 10).

The narratives (`08_narratives.py`) are templates filled with numbers. This layer re-derives each country's facts
from `composites.csv` and `pillar_scores.csv` by its own code, checks them against the published facts, and checks
that every number in the text is one of them, formatted as the text shows it. A number edited by hand into a
sentence, a fact gone stale, or a template that drops or invents a number fails here.

Only asi.core.constants is imported, for declarations.

Run standalone:  python verify/narrative.py
"""

import json
import re
import sys as _sys
from pathlib import Path as _Path

_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_REPO))

import pandas as pd
import yaml

from asi.core.constants import HEADLINE_METHOD, MIN_PILLARS_FOR_COMPOSITE, PILLAR_DEFS

PANEL = _REPO / "data" / "panel"
NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?")
CHECKS: list[dict] = []


def record(name: str, status: str, summary: str, details=()) -> None:
    CHECKS.append({"name": name, "status": status})
    print(f"[{status}] narrative | {name} -- {summary}")
    for line in list(details)[:5]:
        print(f"         {line}")
    if len(details) > 5:
        print(f"         ... and {len(details) - 5} more")


def expected(comp: pd.DataFrame, pil: pd.DataFrame, year: int) -> dict[str, dict]:
    """Each country's facts, by a route of its own: plain loops and per-pillar lists."""
    rows = comp[(comp["method"] == HEADLINE_METHOD)]
    usable = pil[pil["reliability"].isin(["reliable", "thin"]) & pil["score"].notna()]
    ranked = set(rows[(rows["year"] == year) & rows["rank"].notna()]["iso3"])
    medians = {}
    for p in PILLAR_DEFS:
        vals = sorted(usable[(usable["year"] == year) & (usable["pillar_id"] == p)
                             & usable["iso3"].isin(ranked)]["score"])
        if vals:
            mid = len(vals) // 2
            medians[p] = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2
    out = {}
    for r in rows[rows["year"] == year].itertuples():
        if r.iso3 not in ranked:
            out[r.iso3] = {"headline": False, "n_pillars": int(r.n_pillars)}
            continue
        mine = {q.pillar_id: q.score for q in usable[(usable["iso3"] == r.iso3) & (usable["year"] == year)]
                .itertuples()}
        gaps = sorted(((s - medians[p], p) for p, s in mine.items()), key=lambda t: t[0])
        f = {"headline": True, "above": [[p, mine[p], medians[p]] for g, p in reversed(gaps) if g > 0][:2],
             "below": [[p, mine[p], medians[p]] for g, p in gaps if g < 0][:2],
             "score": r.score, "ci_low": r.ci_low, "ci_high": r.ci_high, "tier": int(r.tier),
             "band_best": int(r.band_best), "band_worst": int(r.band_worst), "n_pillars": int(r.n_pillars),
             "lack_of_reliability": r.lack_of_reliability}
        f["left_out"] = sorted(q.pillar_id for q in pil[(pil["iso3"] == r.iso3) & (pil["year"] == year)].itertuples()
                               if pd.notna(q.score) and q.reliability not in ("reliable", "thin"))
        earlier = rows[(rows["iso3"] == r.iso3) & (rows["year"] == year - 10) & rows["rank"].notna()]
        if len(earlier):
            past = {q.pillar_id: q.score for q in usable[(usable["iso3"] == r.iso3)
                                                         & (usable["year"] == year - 10)].itertuples()}
            moves = sorted(((abs(mine[p] - past[p]), p) for p in mine if p in past), key=lambda t: -t[0])
            f["change"] = {"from_year": year - 10, "from": float(earlier["score"].iloc[0]), "pillar": moves[0][1],
                           "pillar_from": past[moves[0][1]], "pillar_to": mine[moves[0][1]]} if moves else None
        out[r.iso3] = f
    return out


def same(a, b) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        return abs(float(a) - float(b)) <= 1e-9
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    return a == b


def allowed(f: dict, doc: dict) -> set[str]:
    """Every number the country's text may show: its facts as formatted, and the fixed numbers of the templates."""
    nums = {str(doc["year"]), str(doc["n_ranked"]), str(doc["n_tiers"]), f"{doc['lri_median']:.1f}", "100", "95",
            "10", "0", str(len(PILLAR_DEFS)), str(MIN_PILLARS_FOR_COMPOSITE), str(f["n_pillars"])}
    if not f["headline"]:
        return nums
    nums |= {f"{f[k]:.1f}" for k in ("score", "ci_low", "ci_high", "lack_of_reliability")}
    nums |= {str(f[k]) for k in ("tier", "band_best", "band_worst")}
    nums |= {f"{x:.1f}" for p, s, m in f["above"] + f["below"] for x in (s, m)}
    if f.get("change"):
        c = f["change"]
        nums |= {str(c["from_year"]), f"{c['from']:.1f}", f"{c['pillar_from']:.1f}", f"{c['pillar_to']:.1f}"}
    return nums


def run() -> int:
    doc = json.loads((PANEL / "narratives.json").read_text(encoding="utf-8"))
    comp = pd.read_csv(PANEL / "composites.csv", float_precision="round_trip")
    pil = pd.read_csv(PANEL / "pillar_scores.csv", float_precision="round_trip")
    year = int(yaml.safe_load((PANEL / "panel_meta.yaml").read_text(encoding="utf-8"))["reference_year"])
    want = expected(comp, pil, year)
    bad_facts = [k for k in sorted(set(want) | set(doc["countries"]))
                 if k not in doc["countries"] or k not in want or not same(want[k], doc["countries"][k]["facts"])]
    record("1 facts re-derived", "FAIL" if bad_facts or doc["year"] != year else "PASS",
           f"{len(want)} countries at {year}" + (f"; {len(bad_facts)} differ" if bad_facts else ", all agree"),
           bad_facts)
    bad_text, n_numbers = [], 0
    for k, c in sorted(doc["countries"].items()):
        ok = allowed(c["facts"], doc)
        for sentence in c["text"]:
            for n in NUMBER.findall(sentence):
                n_numbers += 1
                if n not in ok:
                    bad_text.append(f"{k}: {n} in {sentence!r}")
        if c["facts"]["headline"] and f"{c['facts']['score']:.1f}" not in " ".join(c["text"]):
            bad_text.append(f"{k}: the score is not in the text")
    record("2 every number in the text is a fact", "FAIL" if bad_text else "PASS",
           f"{n_numbers} numbers in {sum(len(c['text']) for c in doc['countries'].values())} sentences", bad_text)
    failed = sum(c["status"] == "FAIL" for c in CHECKS)
    print(f"narrative: {len(CHECKS) - failed} PASS  {failed} FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
