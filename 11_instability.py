"""
11_instability.py — the "Spreading instability" tab's files and the links between states (the owner's rulings of
2026-10-23).

    python 11_instability.py

It writes:
    data/instability.json  the theatres of registry/theatres.yaml (the owner's list), each with its states' deaths by
                     month since 2018 and its spread over the last twelve months (derived, by stated rules), from
                     UCDP's georeferenced events: GED to the end of its year, then the provisional Candidate Events;
                     and each member state's deaths and events in the last twelve months
    geo/events.json  the last twelve months' events in member states, for the map
    geo/links.json   each link of registry/links.yaml (the owner's compilation, R5) as a great-circle line between
                     the two states' Natural Earth label points, with its card: the actor, the kind, the status as
                     its sources put it, its summary and its sources

Natural Earth comes through athena.fetch, hash-locked in the project's sources.lock.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

from asi import geography  # noqa: E402
from asi.core.countries import COUNTRIES  # noqa: E402
from asi.instability import links, theatres  # noqa: E402
from asi.instability.events import BASELINE, Months, Points, Spread, window  # noqa: E402

import pandas as pd  # noqa: E402

GEO = ROOT / "web" / "public" / "geo"
DATA = ROOT / "web" / "public" / "data"
FIRST_MONTH = "2018-01"
COLUMNS = ["country_id", "date_start", "date_end", "best", "low", "high", "adm_1", "side_a", "side_b", "longitude", "latitude",
           "type_of_violence", "code_status"]
CITE = {"ged": "UCDP Georeferenced Event Dataset (GED) Global {edition}: Davies, Pettersson and Öberg (2026), Journal "
               "of Peace Research; Sundberg and Melander (2013). CC BY 4.0",
        "candidate": "UCDP Candidate Events Dataset {edition} (provisional): Hegre, Croicu, Eck and Högbladh (2020), "
                     "Research & Politics. CC BY 4.0"}


def events(store: Path, src: dict) -> pd.DataFrame:
    """GED, then the Candidate Events after GED's last day, with each event's ISO3 code (athena-kit's crosswalk)."""
    import athena.adapters
    codes = pd.read_csv(Path(athena.adapters.__file__).parent / "ucdp_countries.csv", dtype={"country_id": int})
    frames = []
    for kind in ("ged", "candidate"):
        f = pd.read_parquet(store / f"ucdp-{kind}-{src[kind]['edition']}" / "events.parquet", columns=COLUMNS)
        frames.append(f.assign(release=f"{kind} {src[kind]['edition']}"))
    ged, cand = frames
    cand = cand[cand["date_start"] > ged["date_end"].max()]
    e = pd.concat([ged, cand], ignore_index=True)
    return e.merge(codes[["country_id", "iso3"]], on="country_id", how="left")


def last_full_month(dates: pd.Series) -> str:
    """The last month the events cover in full: the month of the latest date, or the one before it if that month is
    not over."""
    latest = pd.Timestamp(dates.max())
    m = pd.Period(latest, "M")
    return str(m if latest == m.end_time.normalize() else m - 1)


def label_points(ne: dict) -> tuple[dict[str, tuple[float, float]], dict[str, str]]:
    """Each state's Natural Earth label point and name; for a merged code (Somaliland in Somalia), the state's own.
    A member state keeps the ASI's name."""
    points: dict[str, tuple[float, float]] = {}
    names: dict[str, str] = {}
    for f in ne["features"]:
        p = f["properties"]
        code = geography.code(p)
        if code in points and p["ADM0_A3"] != code:
            continue
        points[code] = (float(p["LABEL_X"]), float(p["LABEL_Y"]))
        names[code] = COUNTRIES[code]["name"] if code in COUNTRIES else p["NAME"]
    return points, names


def write(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    from asi.sources import fetcher, sources

    ne = json.loads(fetcher().get(sources()["natural-earth-countries-50m"]["url"]))
    points, names = label_points(ne)
    reg = links.load(ROOT / "registry" / "links.yaml", set(points), set(COUNTRIES))
    doc = links.LinkLines().run(links.LinkLines.Input(reg["links"], points, names)).geojson | {"kinds": reg["kinds"]}
    write(GEO / "links.json", doc)

    from athena import dataset
    src = {k: sources()[f"ucdp-{k}"] for k in ("ged", "candidate")}
    e = events(dataset.ROOT, src)
    th = theatres.load(ROOT / "registry" / "theatres.yaml", set(COUNTRIES), {l["id"] for l in reg["links"]})
    last = last_full_month(e["date_end"])
    states = tuple(sorted(COUNTRIES))
    months = Months().run(Months.Input(e, states, FIRST_MONTH, last))
    a, b = window(last)
    recent = e[e["date_start"].str.slice(0, 7).between(a, b) & e["iso3"].isin(states)]
    out = {"last_month": last, "window": [a, b], "months": months.months,
           "sources": [CITE[k].format(edition=src[k]["edition"]) for k in ("ged", "candidate")],
           "rules": {"deaths": "the sum of UCDP's best estimates of deaths in the events that start in the month "
                               "(derived)",
                     "areas": "first-level areas (ADM1, as UCDP names them) with at least one event with deaths in "
                              "the last twelve months, against the twelve before (derived)",
                     "new_ground": f"an armed group UCDP has identified (either side that is not a government; UCDP "
                                   f"writes an unidentified one XXX and its country code) with events in a state "
                                   f"where it had none from {BASELINE} until the window opened (derived)"},
           "states": {k: {"deaths": int(recent[recent["iso3"] == k]["best"].sum()),
                          "low": int(recent[recent["iso3"] == k]["low"].sum()),
                          "high": int(recent[recent["iso3"] == k]["high"].sum()),
                          "events": int((recent["iso3"] == k).sum())} for k in states},
           "theatres": []}
    for t in th["theatres"]:
        sp = Spread().run(Spread.Input(e, tuple(t["states"]), last))
        out["theatres"].append({**{k: t.get(k) for k in ("id", "name", "states", "summary", "links", "markets")},
                                "maps": t.get("maps") or [],
                                "deaths": {k: months.deaths[k] for k in t["states"]},
                                "range": {b: int(recent[recent["iso3"].isin(t["states"])][b].sum())
                                          for b in ("low", "best", "high")},
                                "areas_now": sp.areas_now, "areas_before": sp.areas_before,
                                "new_ground": sp.new_ground})
    write(DATA / "instability.json", out)
    pts = Points().run(Points.Input(e, states, last)).geojson
    write(GEO / "events.json", pts)
    print(f"instability.json: {len(out['theatres'])} theatres, months {months.months[0]} to {last}; "
          f"events.json: {len(pts['features']):,} events in member states, {a} to {b}, "
          f"{int(recent['best'].sum()):,} deaths; events without an ISO3 code: {int(e['iso3'].isna().sum())}")
    for t in out["theatres"]:
        print(f"  {t['id']}: ADM1 areas {t['areas_before']} -> {t['areas_now']}; new ground {len(t['new_ground'])}: "
              f"{[(g['actor'], g['iso3'], g['events']) for g in t['new_ground'][:4]]}")
    by = {s: sum(1 for l in reg["links"] if l["status"] == s) for s in links.STATUS}
    print(f"links.json: {len(doc['features'])} links {by}, "
          f"{sum(1 for l in reg['links'] if l.get('until'))} historical; backers "
          f"{sorted({l['from'] for l in reg['links']})}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
