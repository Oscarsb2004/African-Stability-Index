"""
05_web.py — the files the new site (web/) reads, written to web/public (P55).

    python 05_web.py

It writes:
    geo/countries.json   Natural Earth 1:50m admin-0 polygons for Africa, for hover and click only.
                         Somaliland is drawn as part of Somalia, and Western Sahara apart and unscored (ISO's view).
    geo/borders.json     Natural Earth's land boundary lines. Lines ISO does not recognise are left out;
                         disputed, indefinite and line-of-control lines are marked to be drawn dashed.
    geo/places.json      Natural Earth 1:10m populated places in the member states, with the zoom each appears at.
    data/stability.json  the published ASI at its reference year: composite, pillars and indicators.
    data/meta.json       every source shown on the site, with its licence and attribution.

data/sections.json is written there by 04_sections.py; this stage reads it for the sources list.

Natural Earth comes through athena.fetch, so every file is hash-locked in athena-core's adapters/sources.lock.
Nothing else is downloaded.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))  # athena-core, for `athena` and `adapters`

import pandas as pd  # noqa: E402

from asi import results  # noqa: E402
from asi.core.countries import COUNTRIES  # noqa: E402

PUBLIC = ROOT / "web" / "public"
PANEL = ROOT / "data" / "panel"
DECIMALS = 3  # about 100 m, finer than 1:50m data needs
ALSO_DRAWN = {"ESH": "Western Sahara"}  # on the map, not in the index
MERGED = {"SOL": "SOM", "SDS": "SSD"}  # Somaliland is drawn as Somalia; Natural Earth codes South Sudan SDS
DASHED = ("Disputed", "Indefinite", "Line of control")
EOX = ("EOxCloudless https://cloudless.eox.at by EOX IT Services GmbH "
       "(Contains modified Copernicus Sentinel data 2025)")


def _round(coords):
    if isinstance(coords[0], (int, float)):
        return [round(c, DECIMALS) for c in coords]
    return [_round(c) for c in coords]


def feature(geometry: dict, properties: dict) -> dict:
    return {"type": "Feature", "properties": properties,
            "geometry": {"type": geometry["type"], "coordinates": _round(geometry["coordinates"])}}


def collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def countries(ne: dict) -> dict:
    out, seen = [], set()
    for f in ne["features"]:
        code = MERGED.get(f["properties"]["ADM0_A3"], f["properties"]["ADM0_A3"])
        if code in COUNTRIES:
            out.append(feature(f["geometry"], {"iso3": code, "name": COUNTRIES[code]["name"], "member": True}))
        elif code in ALSO_DRAWN:
            out.append(feature(f["geometry"], {"iso3": code, "name": ALSO_DRAWN[code], "member": False}))
        else:
            continue
        seen.add(code)
    missing = sorted(set(COUNTRIES) - seen)
    if missing:
        raise ValueError(f"member states with no Natural Earth 1:50m polygon: {missing}")
    return collection(out)


def borders(ne: dict, west=-26, south=-36, east=52, north=38) -> dict:
    out = []
    for f in ne["features"]:
        p = f["properties"]
        if p["FCLASS_ISO"] == "Unrecognized":
            continue
        lines = f["geometry"]["coordinates"]
        points = [q for line in lines for q in line] if f["geometry"]["type"] == "MultiLineString" else lines
        xs, ys = [q[0] for q in points], [q[1] for q in points]
        if max(xs) < west or min(xs) > east or max(ys) < south or min(ys) > north:
            continue
        kind = p["FCLASS_ISO"] or p["FEATURECLA"]
        out.append(feature(f["geometry"], {"dashed": kind.startswith(DASHED)}))
    return collection(out)


def places(ne: dict) -> dict:
    out = []
    for f in ne["features"]:
        p = f["properties"]
        code = MERGED.get(p["adm0_a3"], p["adm0_a3"])
        if code not in COUNTRIES:
            continue
        # Natural Earth's class, not its adm0cap flag, which misses Juba; a capital of a merged area is not one
        capital = p["featurecla"] == "Admin-0 capital" and p["adm0_a3"] not in MERGED
        out.append(feature(f["geometry"], {
            "name": p["name"], "iso3": code, "capital": capital, "population": int(p["pop_max"]),
            "min_zoom": p["min_zoom"]}))
    out.sort(key=lambda f: (not f["properties"]["capital"], -f["properties"]["population"]))
    return collection(out)


def stability() -> dict:
    panel = results.load(PANEL)
    bundle, year = panel.meta, panel.reference_year
    comp, pill, obs = panel.composites, panel.pillar_scores, panel.observations
    equal = comp[comp["method"] == "equal"]
    out = {}
    for iso3 in COUNTRIES:
        c = equal[(equal["iso3"] == iso3)].sort_values("year")
        now = c[c["year"] == year].iloc[0]
        p = pill[(pill["iso3"] == iso3) & (pill["year"] == year)]
        o = obs[(obs["iso3"] == iso3) & (obs["year"] == year) & (obs["role"] == "scoring")]
        out[iso3] = {
            "composite": {"score": float(now["score"]), "reliability": now["reliability"]},
            "history": {"years": c["year"].tolist(), "scores": [None if pd.isna(s) else float(s) for s in c["score"]]},
            "pillars": {r.pillar_id: {"score": None if pd.isna(r.score) else float(r.score),
                                      "reliability": r.reliability, "observed": int(r.n_observed),
                                      "indicators": int(r.n_indicators)} for r in p.itertuples()},
            "indicators": {r.variable_name: {"raw": None if pd.isna(r.raw_value) else float(r.raw_value),
                                             "score": None if pd.isna(r.score) else float(r.score),
                                             "provenance": r.provenance,
                                             "source_year": None if pd.isna(r.source_year) else int(r.source_year)}
                           for r in o.itertuples()},
        }
    scores = pd.Series([c["composite"]["score"] for c in out.values()])
    # the map's classes: fifths of the member states at the reference year, a stated rule, not a judgement
    fifths = [round(float(q), 1) for q in scores.quantile([0.2, 0.4, 0.6, 0.8])]
    return {"reference_year": year, "inputs": f"the frozen pull of {bundle['run']['generated']}",
            "method": "equal weights", "classes": {"rule": "fifths of the member states", "breaks": fifths},
            "pillars": bundle["pillars"],
            "indicators": {k: {f: v[f] for f in ("display_name", "series_code", "polarity")}
                           for k, v in bundle["indicators"].items() if v["role"] == "scoring"},
            "countries": out}


def write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8",
                    newline="\n")
    print(f"{path.relative_to(ROOT)}: {path.stat().st_size / 1e3:,.0f} kB")


def main() -> int:
    from adapters import fetcher, sources

    src, fetch = sources(), fetcher()
    ne = {k: json.loads(fetch.get(src[f"natural-earth-{k}"]["url"])) for k in ("countries-50m", "borders-50m",
                                                                                "places-10m")}
    write(PUBLIC / "geo" / "countries.json", countries(ne["countries-50m"]))
    write(PUBLIC / "geo" / "borders.json", borders(ne["borders-50m"]))
    write(PUBLIC / "geo" / "places.json", places(ne["places-10m"]))
    write(PUBLIC / "data" / "stability.json", stability())
    sections = json.loads((PUBLIC / "data" / "sections.json").read_text(encoding="utf-8"))
    write(PUBLIC / "data" / "meta.json", {
        "sources": [{"name": d["attribution"], "licence": d["licence"], "link": d.get("link", "")}
                    for d in sections["datasets"]]
        + [{"name": "Natural Earth (borders, places)", "licence": "public domain",
            "link": "https://www.naturalearthdata.com"},
           {"name": EOX, "licence": "CC BY-NC-SA 4.0", "link": "https://cloudless.eox.at"}],
        "imagery": {"tiles": "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2025_3857/default/"
                             "GoogleMapsCompatible/{z}/{y}/{x}.jpg", "attribution": EOX, "max_zoom": 15}})
    return 0


if __name__ == "__main__":
    sys.exit(main())
