"""
scripts/country_facts.py — what the index actually says about one country.

Run this before writing narrative for a country. The point is to stop prose
being written against a remembered or assumed picture: it prints each pillar's
score, its reliability tier, and the indicators behind it, and it names the
pillars that are greyed and must therefore be left unwritten.

    python scripts/country_facts.py TCD
    python scripts/country_facts.py TCD --year 2015
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from asi.core.constants import PILLAR_DEFS  # noqa: E402
from asi import results as D  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("iso3", help="ISO3 country code, e.g. TCD")
    ap.add_argument("--year", type=int, default=None,
                    help="defaults to the reference year")
    args = ap.parse_args()

    panel = D.load()
    iso3 = args.iso3.upper()
    if iso3 not in panel.countries:
        print(f"Unknown country {iso3!r}.")
        return 1
    year = args.year or panel.reference_year
    meta = panel.countries[iso3]

    print("=" * 74)
    print(f"{meta['name']} ({iso3})  ·  {year}")
    print("=" * 74)
    print(f"Region: {meta['region']}    Communities: {', '.join(meta['recs']) or '—'}"
          f"    Island state: {'yes' if meta['island_state'] else 'no'}")

    # composites
    print("\nOverall")
    for method in panel.methods:
        s = D.country_composite_series(panel, iso3, method)
        row = s[s["year"] == year]
        if row.empty:
            continue
        r = row.iloc[0]
        shown = r["reliability"] in D.DISPLAYABLE and pd.notna(r["score"])
        rank = f"#{int(r['rank'])}" if pd.notna(r["rank"]) else "unranked"
        print(f"  {method:<10} {(f'{r.score:.1f}' if shown else 'not shown'):>10}"
              f"  {rank:>9}   ({r['reliability']})")

    # pillars
    pil = D.country_pillar_series(panel, iso3)
    at_year = pil[pil["year"] == year].set_index("pillar_id")
    greyed = []
    print("\nPillars")
    for pid, pname in PILLAR_DEFS.items():
        if pid not in at_year.index:
            greyed.append(pid)
            print(f"  {pid} {pname:<28} —        no data")
            continue
        r = at_year.loc[pid]
        shown = r["reliability"] in D.DISPLAYABLE and pd.notna(r["score"])
        if not shown:
            greyed.append(pid)
        value = f"{r['score']:.1f}" if shown else "GREYED"
        print(f"  {pid} {pname:<28} {value:>7}   {r['reliability']:<11}"
              f" {int(r['n_observed'])}/{int(r['n_indicators'])} measured")

    # trend
    print("\nTrend (equal weights)")
    s = D.country_composite_series(panel, iso3, "equal")
    shown = s[s["displayable"]]
    if len(shown) >= 2:
        first, last = shown.iloc[0], shown.iloc[-1]
        delta = last["score"] - first["score"]
        print(f"  {int(first['year'])}: {first['score']:.1f}  ->  "
              f"{int(last['year'])}: {last['score']:.1f}   ({delta:+.1f})")
        missing = s[~s["displayable"]]["year"].tolist()
        if missing:
            print(f"  years not shown: {missing}")
    else:
        print("  too few displayable years to state a trend")

    # indicators
    print(f"\nIndicators at {year}")
    inds = D.country_indicators(panel, iso3, year)
    for r in inds.itertuples():
        prov = str(r.provenance)
        flag = "" if prov == "observed" else f"  <- {prov.replace('_', ' ')}"
        raw = f"{r.raw_value:,.2f}" if pd.notna(r.raw_value) else "—"
        score = f"{r.score:.1f}" if pd.notna(r.score) else "—"
        print(f"  {r.display_name[:44]:<46} {raw:>12}  score {score:>6}{flag}")

    if greyed:
        print("\n" + "!" * 74)
        print(f"LEAVE THESE PILLARS UNWRITTEN: {', '.join(greyed)}")
        print("The index judged the data too inferred to score them. Prose about")
        print("them would assert more than the evidence supports, and")
        print("scripts/narrative_check.py will reject the file.")
        print("!" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
