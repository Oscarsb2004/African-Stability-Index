"""Goal 3, indicators 3.1 and 3.2 (section S43). Pipeline side: it never imports `mdg.answers`.

3.1 is built from current UIS counts through the published method. The regional groupings come unchanged from the
3.3 build, which also yields the name-to-code mapping. 3.2 cannot be built: its weights (each country's 1990
non-agricultural labour force) and its imputations are not available, so it is hosted only.
"""

from __future__ import annotations

from athena.store import Store
from mdg.method import CARD_31
from mdg.pipeline import Build, build
from mdg.readers import UisApiReader
from mdg.sources import LEVELS, UIS_COUNTS
from mdg.steps import GerByCountry, ParityByCountry, ParityByGroup, RoundValues, UisCounts

YEARS = (1991, 2000)


def build_goal3(store: Store, base: Build | None = None) -> Build:
    b = base or build(store)
    for part, (level, ef, em, pf, pm, *_rest) in LEVELS.items():
        recipe = UIS_COUNTS[part]
        snapshot = store.latest_snapshot(recipe.ref)
        b.snapshots[recipe.id] = snapshot.hash
        records = UisApiReader().parse(store.get(snapshot.hash), recipe)
        b.parsed[snapshot.hash] = records.content_hash()
        for year in YEARS:
            name = f"3.1{part}-{year}"
            counts = b.run(f"{name}-counts", UisCounts, {"records": records},
                           {"year": year, "ef": ef, "em": em, "pf": pf, "pm": pm})
            b.run(f"{name}-ger", GerByCountry, {"counts": counts}, {})
            b.run(f"{name}-country", ParityByCountry, {"counts": counts}, {})
            group = b.run(f"{name}-group", ParityByGroup, {"counts": counts, "groups": b.frames["groups"]}, {})
            b.run(f"{name}-group-rounded", RoundValues, {"values": group}, {"rounding": CARD_31.rounding})
    return b
