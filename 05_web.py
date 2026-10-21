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
    data/method.json     the "How the index is built" page: the rules, pillars, weights, clusters and checks.
    data/meta.json       every source shown on the site, with its licence and attribution.

data/sections.json is written there by 04_sections.py; this stage reads it for the sources list.

Natural Earth comes through athena.fetch, so every file is hash-locked in the project's sources.lock.
Nothing else is downloaded.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

import pandas as pd  # noqa: E402

from asi import results  # noqa: E402
from asi.geography import MERGED  # noqa: E402
from asi.core.countries import COUNTRIES  # noqa: E402

PUBLIC = ROOT / "web" / "public"
PANEL = ROOT / "data" / "panel"
DECIMALS = 3  # about 100 m, finer than 1:50m data needs
ALSO_DRAWN = {"ESH": "Western Sahara"}  # on the map, not in the index
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
    equal = comp[comp["method"] == bundle.get("headline", "equal")]
    narratives = json.loads((PANEL / "narratives.json").read_text(encoding="utf-8"))
    datasets = sorted(pd.read_csv(ROOT / "data" / "inputs.csv", usecols=["DATASET"])["DATASET"].unique())

    def num(x, kind=float):
        return None if pd.isna(x) else kind(x)

    out = {}
    for iso3 in COUNTRIES:
        c = equal[(equal["iso3"] == iso3)].sort_values("year")
        now = c[c["year"] == year].iloc[0]
        p = pill[(pill["iso3"] == iso3) & (pill["year"] == year)]
        o = obs[(obs["iso3"] == iso3) & (obs["year"] == year) & (obs["role"] == "scoring")]
        out[iso3] = {
            # the headline with its 95% interval, tier and rank band (edition 2, step 8); the point rank stays out
            "composite": {"score": float(now["score"]), "reliability": now["reliability"],
                          "ci_low": num(now.get("ci_low")), "ci_high": num(now.get("ci_high")),
                          "tier": num(now.get("tier"), int), "band_best": num(now.get("band_best"), int),
                          "band_worst": num(now.get("band_worst"), int)},
            "narrative": narratives["countries"][iso3]["text"],
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
    return {"reference_year": year, "inputs": ", ".join(datasets), "n_ranked": narratives["n_ranked"],
            "n_tiers": narratives["n_tiers"],
            "method": "equal weights over the pillars that entered",
            "classes": {"rule": "fifths of the member states", "breaks": fifths},
            "pillars": bundle["pillars"],
            "indicators": {k: {f: v[f] for f in ("display_name", "series_code", "polarity")}
                           for k, v in bundle["indicators"].items() if v["role"] == "scoring"},
            "countries": out}


def method() -> dict:
    """The facts the site's "How the index is built" page shows: the rules with their values, every pillar with
    its indicators and their effective weights, the overlap clusters, the uncertainty and the robustness checks.
    Read from the panel's outputs, the registry and the constants; the page computes nothing."""
    import yaml
    from asi.core import constants as k
    panel = results.load(PANEL)
    bundle, year = panel.meta, panel.reference_year
    head = panel.composites[(panel.composites["method"] == bundle["headline"]) & (panel.composites["year"] == year)
                            & panel.composites["rank"].notna()]
    goalposts = yaml.safe_load((ROOT / "registry" / "goalposts.yaml").read_text(encoding="utf-8"))["indicators"]
    overlap = yaml.safe_load((ROOT / "registry" / "overlap.yaml").read_text(encoding="utf-8"))
    slot = {v: s for s, members in overlap["slots"].items() for v in members}
    nominal = bundle["effective_weights"]["nominal"]
    robust = json.loads((PANEL / "robustness.json").read_text(encoding="utf-8"))
    indicators = bundle["indicators"]
    pillars = []
    for pid, p in bundle["pillars"].items():
        members = [v for v, m in indicators.items() if pid in m["pillars"]]
        pillars.append({"id": pid, "name": p["name"], "indicators": [
            {"id": v, "name": indicators[v]["display_name"], "database": indicators[v]["database"],
             "polarity": indicators[v]["polarity"], "role": indicators[v]["role"],
             "log": bool(goalposts.get(v, {}).get("log_transform", False)),
             "goalposts": goalposts.get(v, {}).get("goalpost_source"),
             "weight": nominal.get(v), "cluster": slot.get(v)} for v in members]})
    width = head["band_worst"] - head["band_best"] + 1
    return {
        "reference_year": year, "n_states": len(COUNTRIES), "n_ranked": int(len(head)),
        "n_scored": sum(m["role"] == "scoring" for m in indicators.values()),
        "n_descriptive": sum(m["role"] != "scoring" for m in indicators.values()),
        "tiers": [int(n) for n in head.groupby("tier").size()],
        "band_median_width": float(width.median()), "se_median": round(float(head["se"].median()), 2),
        "rules": {"admission_floor": k.ADMISSION_FLOOR, "carry_forward_years": k.DEFAULT_MAX_CARRY_FORWARD,
                  "reference_coverage": k.REFERENCE_YEAR_MIN_COVERAGE, "outlier_sd": 3.0, "outlier_replace_sd": 3.1,
                  "outlier_trim": 0.025, "zero_heavy": 0.5, "overlap_bar": overlap["bar"],
                  "overlap_year": overlap["year"], "interval_level": k.INTERVAL_LEVEL, "band_z": k.BAND_Z,
                  "min_pillars": k.MIN_PILLARS_FOR_COMPOSITE, "reliable_at": k.RELIABILITY_RELIABLE_AT,
                  "thin_at": k.RELIABILITY_THIN_AT, "max_imputed": k.RELIABILITY_MAX_IMPUTED},
        "method_roles": bundle["method_roles"], "uncertainty": bundle["uncertainty"],
        "pillars": pillars,
        "clusters": [{"slot": s, "members": [indicators[v]["display_name"] for v in members],
                      "pairs": [q for q in overlap["pairs"] if slot.get(q["a"]) == s and slot.get(q["b"]) == s
                                and abs(q["partial_r"]) >= overlap["bar"]]}
                     for s, members in overlap["slots"].items()],
        "wgi_share": round(sum(w for v, w in nominal.items() if indicators[v]["database"] == "wgi"), 4),
        "robustness": {"agreement": {m: robust["methods"][m]["spearman_vs_equal"] for m in robust["methods"]},
                       "worst_weighting": robust["adversarial_weights"]["worst_spearman"],
                       "verdict": robust["adversarial_weights"]["verdict"],
                       "measured_only": robust["measured_only"]["spearman_vs_baseline"]},
    }


def write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8",
                    newline="\n")
    print(f"{path.relative_to(ROOT)}: {path.stat().st_size / 1e3:,.0f} kB")


def main() -> int:
    from asi.sources import fetcher, sources

    src, fetch = sources(), fetcher()
    ne = {k: json.loads(fetch.get(src[f"natural-earth-{k}"]["url"])) for k in ("countries-50m", "borders-50m",
                                                                                "places-10m")}
    write(PUBLIC / "geo" / "countries.json", countries(ne["countries-50m"]))
    write(PUBLIC / "geo" / "borders.json", borders(ne["borders-50m"]))
    write(PUBLIC / "geo" / "places.json", places(ne["places-10m"]))
    write(PUBLIC / "data" / "stability.json", stability())
    write(PUBLIC / "data" / "method.json", method())
    sections = json.loads((PUBLIC / "data" / "sections.json").read_text(encoding="utf-8"))
    write(PUBLIC / "data" / "meta.json", {
        "sources": [{"name": d["attribution"], "licence": d["licence"], "link": d.get("link", "")}
                    for d in sections["datasets"]]
        + [{"name": "UCDP Country-Year Dataset on Organized Violence 26.1: Davies, Pettersson & Öberg (2026), "
                    "Journal of Peace Research; Sundberg & Melander (2013), Journal of Peace Research 50(4)",
            "licence": "CC BY 4.0", "link": "https://ucdp.uu.se/downloads/"},
           {"name": "Wikidata (memberships, official languages, wonders)", "licence": "CC0",
            "link": "https://www.wikidata.org"},
           {"name": "Hammarström, Forkel, Haspelmath & Bank (2026), Glottolog 5.3, Max Planck Institute for "
                    "Evolutionary Anthropology", "licence": "CC BY 4.0", "link": "https://glottolog.org"},
           {"name": "Natural Earth (borders, places, subregions)", "licence": "public domain",
            "link": "https://www.naturalearthdata.com"},
           {"name": EOX, "licence": "CC BY-NC-SA 4.0", "link": "https://cloudless.eox.at"}],
        "imagery": {"tiles": "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2025_3857/default/"
                             "GoogleMapsCompatible/{z}/{y}/{x}.jpg", "attribution": EOX, "max_zoom": 15}})
    return 0


if __name__ == "__main__":
    sys.exit(main())
