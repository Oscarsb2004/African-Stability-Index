"""
06_backtests.py — run the pre-registered backtests on the published panel (the vault's `ASI Backtests`).

    python 06_backtests.py wdi-2026-10-08 wgi-2026-09-25

Outcomes come from the WDI's copies of their publishers' data until those datasets are ingested:
- conflict: battle-related deaths (UCDP via WDI). WDI lists conflict years only, so a year without a value is read
  as below UCDP's 25-death threshold;
- displacement: new displacement by conflict (IDMC via WDI), 2009 onward, a missing year read as none;
- inflation crisis: inflation above 20% (Reinhart and Rogoff 2011);
- currency crash: a depreciation against the dollar of 15% or more (Reinhart and Rogoff 2011).

Writes data/backtests.json and prints a summary. BT3 (coups) waits on its dataset's terms; BT7 on WDI archives.

v2 (edition 2, 2026-10-20): the same tests on edition 2's eight pillars, mapped by meaning before the run (the
vault's `ASI Backtest Protocol`, athena-data e6e9b22): the ASI without SEC; MAC as the economic predictor; BT6
expects SEC, GOV or VOI for conflict and MAC for monetary crises. Edition 1's results are in
data/backtests_edition1.json.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))  # athena-core, for the `athena` package

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import backtests as bt  # noqa: E402
from asi.core.countries import COUNTRIES  # noqa: E402

OUTPUT = ROOT / "data" / "backtests.json"
PANEL = ROOT / "data" / "panel"
SERIES = ["VC.BTL.DETH", "VC.IDP.NWCV", "FP.CPI.TOTL.ZG", "PA.NUS.FCRF", "NY.GDP.PCAP.PP.KD", "GOV_WGI_PV.EST"]
AREAS = sorted(COUNTRIES)


def wide(values: pd.DataFrame, series: str) -> pd.DataFrame:
    v = values[values["SERIES"] == series]
    w = v.pivot_table(index="REF_AREA", columns="TIME_PERIOD", values="OBS_VALUE", aggfunc="first")
    w.columns = w.columns.astype(int)
    return w.reindex(AREAS)


def recorded(w: pd.DataFrame, first: int, last: int, above: float = 0.0) -> pd.DataFrame:
    """1 where a value above `above` is recorded, 0 otherwise: for series that list event years only."""
    years = list(range(first, last + 1))
    return (w.reindex(columns=years) > above).astype(float)


def threshold(w: pd.DataFrame, limit: float, inclusive: bool) -> pd.DataFrame:
    """1 beyond the limit, 0 within it, NaN where unknown."""
    hit = (w >= limit) if inclusive else (w > limit)
    return hit.astype(float).where(w.notna())


def latest_at(w: pd.DataFrame, iso3: str, t: int) -> float:
    """The value at t, or the latest before it (the WGI skips some early years)."""
    row = w.loc[iso3, [y for y in w.columns if y <= t]].dropna()
    return float(row.iloc[-1]) if len(row) else float("nan")


def main(names: list[str]) -> int:
    if not names:
        print(__doc__)
        return 2
    from athena import dataset

    values = pd.concat([dataset.load(n) for n in names], ignore_index=True)
    values = values[values["SERIES"].isin(SERIES) & values["REF_AREA"].isin(AREAS)]
    deaths, displaced = wide(values, "VC.BTL.DETH"), wide(values, "VC.IDP.NWCV")
    inflation, rate = wide(values, "FP.CPI.TOTL.ZG"), wide(values, "PA.NUS.FCRF")
    gdp, pv = wide(values, "NY.GDP.PCAP.PP.KD"), wide(values, "GOV_WGI_PV.EST")
    depreciation = rate / rate.shift(1, axis=1) - 1

    comp = pd.read_csv(PANEL / "composites.csv")
    comp = comp[comp["method"] == "equal"].set_index(["iso3", "year"])["score"]
    pillars = pd.read_csv(PANEL / "pillar_scores.csv").pivot_table(index=["iso3", "year"], columns="pillar_id",
                                                                     values="score")
    without_sec = pillars.drop(columns="SEC").mean(axis=1)
    fifth = comp.groupby(level="year").transform(lambda s: s <= s.quantile(0.2))

    flags = {
        "conflict": recorded(deaths, 1989, 2024),
        "displacement": recorded(displaced, 2009, 2023),
        "inflation_crisis": threshold(inflation, 20, inclusive=False),
        "currency_crash": threshold(depreciation, 0.15, inclusive=True),
    }

    def rows_for(event: str, first: int, last: int, h: int, extra=()) -> pd.DataFrame:
        r = bt.windows(flags[event], first, last, h)
        key = list(zip(r["iso3"], r["year"]))
        r["asi"] = [-comp.get(k, np.nan) for k in key]
        r["asi_without_SEC"] = [-without_sec.get(k, np.nan) for k in key]
        r["gdp"] = [-np.log(gdp.loc[i, t]) if t in gdp.columns and gdp.loc[i, t] > 0 else np.nan for i, t in key]
        r["history"] = [bt.history(flags[event], i, t) for i, t in key]
        for p in pillars.columns:
            r[f"pillar_{p}"] = [-pillars[p].get(k, np.nan) for k in key]
        if "wgi_pv" in extra:
            r["wgi_pv"] = [-latest_at(pv, i, t) for i, t in key]
        if "inflation_now" in extra:
            r["inflation_now"] = [inflation.loc[i, t] if t in inflation.columns else np.nan for i, t in key]
        return r

    def run(event, first, last, h, predictors, extra=()):
        r = rows_for(event, first, last, h, extra)
        result = bt.compare(r, predictors, "gdp")
        return {"window": f"t = {first} to {last}, event in t+1 to t+{h}",
                "n": {"state_years": len(r), "events": int(r["event"].sum()), "states": int(r["iso3"].nunique())},
                "auc": result, "verdict": bt.verdict(result, "asi", "gdp"),
                "hit_rate": bt.hit_rate(r, fifth)}, r

    out, rows = {}, {}
    out["BT1 conflict onset"], rows["conflict"] = run(
        "conflict", 2000, 2021, 3, ["asi", "asi_without_SEC", "gdp", "history", "wgi_pv"], ("wgi_pv",))
    out["BT1 sensitivity, t+1"], _ = run("conflict", 2000, 2023, 1, ["asi", "gdp"])
    out["BT1 sensitivity, t+1 to t+5"], _ = run("conflict", 2000, 2019, 5, ["asi", "gdp"])
    out["BT2 conflict displacement"], _ = run(
        "displacement", 2009, 2020, 3, ["asi", "asi_without_SEC", "gdp", "history"])
    out["BT4 inflation crisis"], rows["inflation_crisis"] = run(
        "inflation_crisis", 2000, 2021, 3, ["asi", "pillar_MAC", "gdp", "history", "inflation_now"],
        ("inflation_now",))
    out["BT4 currency crash"], rows["currency_crash"] = run(
        "currency_crash", 2000, 2021, 3, ["asi", "pillar_MAC", "gdp", "history"])
    for h, last in ((1, 2023), (5, 2019)):
        for e in ("inflation_crisis", "currency_crash"):
            out[f"BT4 {e.replace('_', ' ')} sensitivity, h={h}"], _ = run(e, 2000, last, h, ["asi", "gdp"])

    # BT6: every pillar's AUC on BT1's and BT4's rows
    expected = {"conflict": {"SEC", "GOV", "VOI"}, "inflation_crisis": {"MAC"}, "currency_crash": {"MAC"}}
    for event, r in rows.items():
        cols = [f"pillar_{p}" for p in pillars.columns]
        res = bt.compare(r, cols, None)
        lead = max(cols, key=lambda c: res[c]["value"]).removeprefix("pillar_")
        out[f"BT6 pillars, {event.replace('_', ' ')}"] = {
            "auc": res, "leading_pillar": lead, "expected": sorted(expected[event]),
            "expectation_held": lead in expected[event]}

    # BT5: war onsets by rule
    war = recorded(deaths, 1989, 2024, above=999)
    pct = comp.groupby(level="year").rank(pct=True)
    events = []
    for iso3 in AREAS:
        for t in range(2003, 2025):
            if war.loc[iso3, t] == 1 and (war.loc[iso3, [t - 3, t - 2, t - 1]] == 0).all():
                path = {f"t-{k}": pct.get((iso3, t - k), np.nan) for k in (3, 2, 1, 0)}
                events.append({"state": iso3, "year": t, **{k: round(float(v) * 100, 1) for k, v in path.items()}})
    ev = pd.DataFrame(events)
    out["BT5 war onsets"] = {
        "events": events, "n": len(events),
        "share_bottom_fifth_at_t-1": float((ev["t-1"] <= 20).mean()) if len(ev) else None,
        "median_change_t-3_to_t-1_percentile_points": float((ev["t-1"] - ev["t-3"]).median()) if len(ev) else None}

    OUTPUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    for name, res in out.items():
        if "auc" in res and "n" in res:
            a = res["auc"]
            line = ", ".join(f"{k} {v['value']:.3f} [{v['low']:.3f}, {v['high']:.3f}]" for k, v in a.items())
            print(f"{name}: n {res['n']}; {line}; verdict {res['verdict']}; hits {res['hit_rate']}")
        elif "leading_pillar" in res:
            line = ", ".join(f"{k.removeprefix('pillar_')} {v['value']:.3f} [{v['low']:.3f}, {v['high']:.3f}]"
                             for k, v in res["auc"].items())
            print(f"{name}: {line}; leading {res['leading_pillar']}, expected {res['expected']}, "
                  f"held {res['expectation_held']}")
    print("BT5:", {k: v for k, v in out["BT5 war onsets"].items() if k != "events"})
    for e in out["BT5 war onsets"]["events"]:
        print("  ", e)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
