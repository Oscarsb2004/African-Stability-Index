"""
09_explore.py — the Data tab's files (P105): every series that covers enough of the member states, each in its own
small file loaded only when chosen, the catalogue that lists them, the groups of states, each state's categories and
neighbours, and each state's languages for the Wonders tab.

    python 09_explore.py wdi-2026-10-08 wgi-2026-09-25 hdr-2025 cpi-2025 weo-2026-10 ucdp-cy-26.1 \
        wikidata-states-2026-10-20 glottolog-5.3

It writes, under web/public/data/explore/:
    catalogue.json            every measure: id, label, unit, topic, states covered, years, source
    s/<dataset>/<code>.json   one series: {"y": [first, last], "v": {iso3: values}} and, where the publisher gives
                              them, the interval ("lo", "hi"), the first projected year ("f") or the ASI's tiers
    groups.json               the RECs (registry/groups.yaml), the organisations (Wikidata), the cross-check
    states.json               each state's categories, with source and kind, its land neighbours, and how much of each
                              dataset covers it since COVERAGE_SINCE
    languages.json            each state's languages (Glottolog) and official languages (Wikidata)

A series is listed when at least FLOOR states have a value in some year since FIRST_YEAR. Values are printed to four
significant figures, as the publisher's or the panel's; nothing is filled, imputed or rescaled. A category the
publisher prints is "as printed"; one computed here says its formula.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent

import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from asi import geography, results  # noqa: E402
from asi.core.countries import COUNTRIES  # noqa: E402

OUT = ROOT / "web" / "public" / "data" / "explore"
PANEL = ROOT / "data" / "panel"
GROUPS = ROOT / "registry" / "groups.yaml"
FLOOR, FIRST_YEAR, MIN_ORG_MEMBERS = 20, 2000, 3
LANGUAGES_YEAR = 2026  # Glottolog 5.3 was released on 2026-03-02
COVERAGE_SINCE = 2015  # the coverage map counts a series as covering a state if it has a value from this year on
SOURCES = {  # credit for each dataset the Data tab shows, as each publisher's terms ask (Sources.md)
    "asi": ("African Stability Index, edition 2 (this project)", "CC BY 4.0", ""),
    "wdi": ("The World Bank: World Development Indicators", "CC BY 4.0",
            "https://datacatalog.worldbank.org/search/dataset/0037712"),
    "wgi": ("The World Bank: Worldwide Governance Indicators", "CC BY 4.0",
            "https://www.worldbank.org/en/publication/worldwide-governance-indicators"),
    "hdr": ("UNDP Human Development Report Office: Human Development Report data, 2025 edition", "CC BY 3.0 IGO",
            "https://hdr.undp.org/data-center"),
    "cpi": ("Corruption Perceptions Index (2025) by Transparency International is licensed under CC BY 4.0",
            "CC BY 4.0", "https://www.transparency.org/en/cpi/2025"),
    "weo": ("Source: International Monetary Fund, World Economic Outlook database, October 2026",
            "IMF terms for data", "https://www.imf.org/en/Publications/SPROLLs/world-economic-outlook-databases"),
    "ucdp": ("UCDP Country-Year Dataset on Organized Violence 26.1: Davies, Pettersson & Öberg (2026), Journal of "
             "Peace Research; Sundberg & Melander (2013), Journal of Peace Research 50(4)", "CC BY 4.0",
             "https://ucdp.uu.se/downloads/"),
    "wikidata": ("Wikidata", "CC0", "https://www.wikidata.org"),
    "glottolog": ("Hammarström, Forkel, Haspelmath & Bank (2026), Glottolog 5.3, Max Planck Institute for "
                  "Evolutionary Anthropology", "CC BY 4.0", "https://glottolog.org"),
    "ne": ("Natural Earth", "public domain", "https://www.naturalearthdata.com"),
}
TOPICS = {"wgi": None, "hdr": "Human development (UNDP)", "cpi": "Corruption Perceptions Index",
          "weo": "World Economic Outlook (IMF)", "ucdp": "Organised violence (UCDP)"}
BOUNDS = {"wgi": (r"\.SC$", "_LB", "_UB", "90%"), "cpi": (r"^cpi_score$", None, None, "90%")}
UCDP_WORDS = {"sb": "State-based conflict", "ns": "Non-state conflict", "os": "One-sided violence",
              "best": "best estimate", "high": "high estimate", "low": "low estimate", "govt": "government",
              "inv": "involved", "nsgroup": "non-state group", "orgvio": "organised violence",
              "incomp": "incompatibility", "exist": "present (1) or not (0)", "dyad": "dyads"}
SPOKEN = {"Spoken L1 Language", "Pidgin", "Mixed Language"}


def key(name: str) -> str:
    """A dataset's short name: wdi-2026-10-08 -> wdi, wikidata-states-2026-10-20 -> wikidata."""
    return name.split("-")[0]


def four(v) -> float | None:
    return None if pd.isna(v) else float(f"{float(v):.4g}")


def file_id(code: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", code)


def ucdp_label(code: str) -> str:
    """UCDP's variable names spelled out by its own abbreviations (the dataset has no label table)."""
    text = " ".join(UCDP_WORDS.get(w, w) for w in code.split("_"))
    return text[0].upper() + text[1:]


def labels(name: str) -> dict[str, tuple[str, str, str]]:
    """Each series code's label, unit and topic, from the dataset's own codebook."""
    from athena import dataset
    k = key(name)
    if k in ("wdi", "wgi"):
        cb = dataset.load(name, "codebook")
        return {r["Series Code"]: (r["Indicator Name"], r["Unit of measure"],
                                   TOPICS.get(k) or r["Topic"].split(":")[0]) for _, r in cb.iterrows()}
    if k == "hdr":
        cb = dataset.load(name, "codebook")
        return {r["Short name"]: (r["Full name"], "", TOPICS[k]) for _, r in cb.iterrows() if r["Short name"]}
    if k == "cpi":
        cb = dataset.load(name, "codebook")
        return {r["series"]: (r["name"], "", TOPICS[k]) for _, r in cb.iterrows()}
    if k == "weo":
        cb = dataset.load(name, "series").drop_duplicates("INDICATOR.ID")
        return {r["INDICATOR.ID"]: (r["INDICATOR"], " ".join(x for x in (r["SCALE"], r["UNIT"]) if x and x != "Units"),
                                    TOPICS[k])
                for _, r in cb.iterrows()}
    return {}


def series_docs(name: str, values: pd.DataFrame) -> tuple[list[dict], dict[str, dict]]:
    """The catalogue entries and series files of one dataset: member states only, from FIRST_YEAR, with FLOOR."""
    k, names = key(name), labels(name)
    v = values[values["REF_AREA"].isin(COUNTRIES) & values["OBS_VALUE"].notna()].copy()
    v["year"] = v["TIME_PERIOD"].str[:4].astype(int)
    v = v[v["year"] >= FIRST_YEAR]
    cover = v.groupby("SERIES")["REF_AREA"].nunique()
    kept = sorted(cover[cover >= FLOOR].index)
    entries, files = [], {}
    by_series = {s: g for s, g in v[v["SERIES"].isin(kept)].groupby("SERIES")}
    for code in kept:
        g = by_series[code]
        y0, y1 = int(g["year"].min()), int(g["year"].max())
        doc = {"y": [y0, y1], "v": grid(g, y0, y1)}
        if (g["OBS_STATUS"] == "F").any():
            doc["f"] = {a: int(r["year"].min()) - y0 for a, r in g[g["OBS_STATUS"] == "F"].groupby("REF_AREA")}
        label, unit, topic = names.get(code, (ucdp_label(code) if k == "ucdp" else code, "", TOPICS.get(k) or k))
        entry = {"id": f"{k}/{code}", "ds": k, "code": code, "label": label, "unit": unit, "topic": topic,
                 "n": int(cover[code]), "y": [y0, y1]}
        if k in BOUNDS and re.search(BOUNDS[k][0], code):
            lo, hi = (code + BOUNDS[k][1], code + BOUNDS[k][2]) if BOUNDS[k][1] else ("lower_ci", "upper_ci")
            if lo in by_series and hi in by_series:
                doc["lo"], doc["hi"] = grid(by_series[lo], y0, y1), grid(by_series[hi], y0, y1)
                entry["interval"] = BOUNDS[k][3]
        entries.append(entry)
        files[f"{k}/{file_id(code)}"] = doc
    return entries, files


def grid(g: pd.DataFrame, y0: int, y1: int, column: str = "OBS_VALUE") -> dict[str, list]:
    """Each state's values from y0 to y1, None where the publisher has none."""
    years = range(y0, y1 + 1)
    return {a: [four(x) for x in r.set_index("year")[column].reindex(years)]
            for a, r in g.groupby("REF_AREA") if r[column].notna().any()}


def asi_docs() -> tuple[list[dict], dict[str, dict]]:
    """The ASI's own measures: the headline with its 95% interval and tier, every pillar, every scored indicator's
    score and every indicator's value as the panel holds it."""
    panel = results.load(PANEL)
    bundle = panel.meta
    head = panel.composites[panel.composites["method"] == bundle["headline"]].rename(columns={"iso3": "REF_AREA"})
    entries, files = [], {}

    def add(mid: str, label: str, topic: str, frame: pd.DataFrame, unit: str = "score 0-100", extra=None):
        frame = frame[frame["OBS_VALUE"].notna()]
        if frame.empty:
            return
        y0, y1 = int(frame["year"].min()), int(frame["year"].max())
        doc = {"y": [y0, y1], "v": grid(frame, y0, y1)} | (extra(frame, y0, y1) if extra else {})
        entries.append({"id": f"asi/{mid}", "ds": "asi", "code": mid, "label": label, "unit": unit, "topic": topic,
                        "n": int(frame["REF_AREA"].nunique()), "y": [y0, y1],
                        "polarity": "higher is more stable" if unit == "score 0-100" else "",
                        "ref": panel.reference_year}
                       | ({"interval": "95%"} if mid == "headline" else {}))
        files[f"asi/{file_id(mid)}"] = doc

    add("headline", "ASI headline score", "African Stability Index", head.rename(columns={"score": "OBS_VALUE"}),
        extra=lambda f, y0, y1: {"lo": grid(f, y0, y1, "ci_low"), "hi": grid(f, y0, y1, "ci_high"),
                                 "tier": {a: [None if pd.isna(t) else int(t) for t in
                                              r.set_index("year")["tier"].reindex(range(y0, y1 + 1))]
                                          for a, r in f.groupby("REF_AREA")}})
    pillars = panel.pillar_scores.rename(columns={"iso3": "REF_AREA", "score": "OBS_VALUE"})
    for pid, p in bundle["pillars"].items():
        add(f"pillar.{pid}", f"ASI pillar: {p['name']}", "African Stability Index", pillars[pillars["pillar_id"] == pid])
    obs = panel.observations.rename(columns={"iso3": "REF_AREA"})
    for var, spec in bundle["indicators"].items():
        o = obs[obs["variable_name"] == var]
        if spec["role"] == "scoring":
            add(f"score.{var}", f"ASI score: {spec['display_name']}", "African Stability Index: indicator scores",
                o.rename(columns={"score": "OBS_VALUE"}))
        add(f"value.{var}", f"ASI input: {spec['display_name']}", "African Stability Index: inputs",
            o.rename(columns={"raw_value": "OBS_VALUE"}), unit="as published")
    return entries, files


def group_docs(wikidata: str) -> dict:
    """The RECs as the owner compiled them, the listed organisations with their members from Wikidata, and the
    cross-check of each REC against Wikidata's current members. The cross-check reports; it never changes a list."""
    from athena import dataset
    reg = yaml.safe_load(GROUPS.read_text(encoding="utf-8"))
    m = dataset.load(wikidata, "membership")
    current = m[(m["end"] == "") & m["iso3"].isin(COUNTRIES)]
    members = current.groupby("org")["iso3"].apply(lambda s: sorted(set(s))).to_dict()
    unknown = sorted({a for g in reg["recs"] for a in g["members"]} - set(COUNTRIES))
    if unknown:
        raise ValueError(f"groups.yaml names states not in the index: {unknown}")
    orgs = []
    for o in reg["organisations"]:
        found = members.get(o["wikidata"], [])
        if len(found) < MIN_ORG_MEMBERS:
            raise ValueError(f"{o['id']}: Wikidata records {len(found)} current members; the rule needs "
                             f"{MIN_ORG_MEMBERS} (remove it from groups.yaml)")
        orgs.append({"id": o["id"], "name": o["name"], "kind": "organisation", "basis": o["basis"],
                     "members": found, "source": "wikidata"})
    recs = [{"id": g["id"], "name": g["name"], "kind": "rec", "members": sorted(g["members"]),
             "source": "the owner's compilation (registry/groups.yaml)"} for g in reg["recs"]]
    return {"note": "Members as they stand today. Each state counts once in a group; no state is excluded, adjusted "
                    "or reweighted for being small, an island or data-poor.",
            "groups": recs + orgs, "history": reg.get("history", []), "crosscheck": crosscheck(reg["recs"], members)}


def crosscheck(recs: list[dict], members: dict[str, list[str]]) -> list[dict]:
    """Each REC beside Wikidata's current members: who is only in the owner's list, who only in Wikidata."""
    out = []
    for g in recs:
        wd = members.get(g["wikidata"], [])
        out.append({"group": g["id"], "wikidata_count": len(wd), "owner_only": sorted(set(g["members"]) - set(wd)),
                    "wikidata_only": sorted(set(wd) - set(g["members"]))})
    return out


def census_year(text: str) -> int | None:
    found = re.search(r"(19|20)\d{2}", text or "")
    return int(found.group(0)) if found else None


def state_docs(names: dict[str, str], ne: dict, groups: dict) -> dict:
    """Each state's categories. As printed where a publisher prints the category; derived ones say how."""
    from athena import dataset
    wdi = dataset.load(names["wdi"], "areas").set_index("Country Code").reindex(sorted(COUNTRIES))
    hdr = dataset.load(names["hdr"], "areas").set_index("iso3").reindex(sorted(COUNTRIES))
    facts = dataset.load(names["wikidata"], "attributes")
    facts = facts[facts["iso3"].isin(COUNTRIES)]
    ucdp = dataset.load(names["ucdp"])
    sb = ucdp[(ucdp["SERIES"] == "sb_total_deaths_best") & ucdp["REF_AREA"].isin(COUNTRIES)].copy()
    sb["year"] = sb["TIME_PERIOD"].astype(int)
    last = int(sb["year"].max())
    panel = results.load(PANEL)
    head = panel.composites[(panel.composites["method"] == panel.meta["headline"])
                            & (panel.composites["year"] == panel.reference_year)].set_index("iso3")
    out: list[dict] = []

    def attribute(aid, label, source, kind, values, order=None, asof=""):
        out.append({"id": aid, "label": label, "source": source, "kind": kind, "asof": asof,
                    "values": {a: v for a, v in values.items() if v not in (None, "", [])}}
                   | ({"order": order} if order else {}))

    printed = "as printed"
    attribute("subregion", "Subregion (Natural Earth)", "ne", printed, geography.subregions(ne),
              order=["Northern Africa", "Western Africa", "Middle Africa", "Eastern Africa", "Southern Africa"])
    attribute("wb_region", "World Bank region", "wdi", printed, wdi["Region"].to_dict())
    attribute("income", "World Bank income group", "wdi", printed, wdi["Income Group"].to_dict(),
              order=["Low income", "Lower middle income", "Upper middle income", "High income"])
    attribute("lending", "World Bank lending category", "wdi", printed, wdi["Lending category"].to_dict(),
              order=["IDA", "Blend", "IBRD"])
    attribute("hipc", "Heavily indebted poor country (HIPC)", "wdi", "derived: 'HIPC' where the WDI's 'Other groups' "
              "says so, otherwise 'not HIPC'", {a: "HIPC" if v == "HIPC" else "not HIPC"
                                                  for a, v in wdi["Other groups"].items()}, order=["HIPC", "not HIPC"])
    attribute("dissemination", "IMF data dissemination standard", "wdi", printed,
              wdi["IMF data dissemination standard"].to_dict())
    years = {a: census_year(v) for a, v in wdi["Latest population census"].items()}
    attribute("census", "Population census in the last 10 years", "wdi",
              f"derived: the latest census year in the WDI's country table is {panel.reference_year - 9} or later",
              {a: "within 10 years" if y and y >= panel.reference_year - 9 else "older or none recorded"
               for a, y in years.items()}, order=["within 10 years", "older or none recorded"],
              asof=str(panel.reference_year))
    attribute("vital_registration", "Vital registration complete", "wdi", "derived: 'yes' where the WDI says so",
              {a: "yes" if v == "Yes" else "not recorded as complete" for a, v in
               wdi["Vital registration complete"].items()})
    attribute("hdi_group", "UNDP human development group", "hdr", printed, hdr["hdicode"].to_dict(),
              order=["Low", "Medium", "High", "Very High"])
    status = {}
    for a in sorted(COUNTRIES):
        d = sb[(sb["REF_AREA"] == a) & (sb["year"] == last)]["OBS_VALUE"]
        n = float(d.iloc[0]) if len(d) else None
        status[a] = None if n is None else ("none" if n < 25 else "25 to 999 deaths" if n < 1000 else "1,000 or more")
    attribute("conflict", f"State-based conflict deaths, {last}", "ucdp",
              "derived: UCDP's best estimate of state-based battle deaths in the state that year, in UCDP's own "
              "thresholds (25 and 1,000), applied to the state's total", status,
              order=["none", "25 to 999 deaths", "1,000 or more"], asof=str(last))
    attribute("asi_tier", f"ASI tier, {panel.reference_year}", "asi", "as computed by the index (leader rule, P96)",
              {a: f"Tier {int(t)}" for a, t in head["tier"].dropna().items()},
              order=[f"Tier {i}" for i in range(1, int(head["tier"].max()) + 1)], asof=str(panel.reference_year))

    def facts_of(prop):
        f = facts[facts["property"] == prop]
        return f.groupby("iso3")["value_label"].apply(lambda s: sorted(set(s))).to_dict()

    attribute("official_languages", "Official languages", "wikidata", printed, facts_of("P37"))
    attribute("currency", "Currency", "wikidata", printed, facts_of("P38"))
    attribute("government", "Basic form of government", "wikidata", printed, facts_of("P122"))
    attribute("driving", "Driving side", "wikidata", printed, {a: v[0] for a, v in facts_of("P1622").items()})
    classes = facts_of("P31")
    attribute("landlocked", "Landlocked", "wikidata", "derived: 'landlocked' where Wikidata classes the state as a "
              "landlocked country", {a: "landlocked" if "landlocked country" in classes.get(a, []) else "coastal"
                                     for a in COUNTRIES}, order=["landlocked", "coastal"])
    attribute("island", "Island state", "wikidata", "derived: 'island state' where Wikidata classes the state as an "
              "island country; a fact like any other, never a reason to treat a state differently (P105)",
              {a: "island state" if "island country" in classes.get(a, []) else "mainland" for a in COUNTRIES},
              order=["mainland", "island state"])
    recs = [g for g in groups["groups"] if g["kind"] == "rec"]
    attribute("rec_count", "Number of REC memberships", "asi", "derived: how many of the eight RECs list the state "
              "(registry/groups.yaml)", {a: str(sum(a in g["members"] for g in recs)) for a in COUNTRIES},
              order=[str(i) for i in range(0, 5)])
    attribute("recs", "Regional Economic Communities", "asi", "as compiled by the owner (registry/groups.yaml)",
              {a: [g["id"] for g in recs if a in g["members"]] for a in COUNTRIES})
    return {"attributes": out, "neighbours": geography.neighbours(ne)}


def language_docs(names: dict[str, str]) -> tuple[dict, list[dict], dict[str, dict]]:
    """Each state's languages still spoken (Glottolog), with family, endangerment and description, and its
    official languages (Wikidata); and two measures, the number of languages and of endangered languages."""
    from athena import dataset
    g = dataset.load(names["glottolog"], "languoids")
    alpha2 = dataset.load(names["wdi"], "areas").set_index("2-alpha code")["Country Code"].to_dict()
    spoken = g[(g["level"] == "language") & g["category"].isin(SPOKEN) & (g["aes"] != "extinct")]
    facts = dataset.load(names["wikidata"], "attributes")
    official = facts[facts["property"] == "P37"].groupby("iso3")["value_label"].apply(lambda s: sorted(set(s)))
    by_state: dict[str, list] = {a: [] for a in sorted(COUNTRIES)}
    for r in spoken.itertuples():
        family = r.family_name or ("Isolate" if r.is_isolate == "True" else "Unclassified")
        for code in filter(None, r.countries.split(";")):
            iso3 = alpha2.get(code)
            if iso3 in by_state:
                by_state[iso3].append([r.name, family, r.aes, r.med, r.glottocode])
    doc = {"source": "glottolog", "rule": "languages Glottolog places in the state, at language level, spoken as a "
           "first language, a pidgin or a mixed language, and not extinct; Glottolog counts languages, not speakers",
           "states": {}}
    endangered = {"threatened", "shifting", "moribund", "nearly extinct"}
    for iso3, langs in by_state.items():
        langs.sort(key=lambda x: x[0])
        doc["states"][iso3] = {"official": list(official.get(iso3, [])), "n": len(langs),
                               "families": dict(Counter(x[1] for x in langs).most_common()),
                               "endangered": sum(x[2] in endangered for x in langs), "languages": langs}
    year = LANGUAGES_YEAR
    entries, files = [], {}
    for mid, label, val in (("languages", "Languages spoken (Glottolog)", lambda s: s["n"]),
                            ("endangered", "Endangered languages (Glottolog AES: threatened to nearly extinct)",
                             lambda s: s["endangered"])):
        entries.append({"id": f"glottolog/{mid}", "ds": "glottolog", "code": mid, "label": label, "unit": "languages",
                        "topic": "Languages (Glottolog)", "n": len(COUNTRIES), "y": [year, year]})
        files[f"glottolog/{mid}"] = {"y": [year, year], "v": {a: [val(s)] for a, s in doc["states"].items()}}
    return doc, entries, files


def coverage(files: dict[str, dict], since: int = COVERAGE_SINCE) -> dict[str, dict[str, float]]:
    """For each dataset, each state's share of its listed series with a value since `since`: how visible each
    state is in each publisher's data, the story behind the ASI's reliability tiers."""
    by_ds: dict[str, list[dict]] = {}
    for fid, doc in files.items():
        by_ds.setdefault(fid.split("/")[0], []).append(doc)
    out = {}
    for ds, docs in sorted(by_ds.items()):
        if ds in ("asi", "glottolog"):
            continue
        counts = Counter(a for d in docs for a, vals in d["v"].items()
                         if any(v is not None for v in vals[max(0, since - d["y"][0]):]))
        out[ds] = {a: round(counts.get(a, 0) / len(docs), 3) for a in sorted(COUNTRIES)}
    return out


def write(path: Path, doc: dict) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return len(text.encode("utf-8"))


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    from asi.sources import fetcher, sources
    from athena import dataset

    names = {key(n): n for n in argv}
    needed = {"wdi", "hdr", "ucdp", "wikidata", "glottolog"}
    if needed - set(names):
        raise SystemExit(f"name the {sorted(needed - set(names))} datasets too")
    entries, files = asi_docs()
    for k in ("wdi", "wgi", "hdr", "cpi", "weo", "ucdp"):
        if k in names:
            e, f = series_docs(names[k], dataset.load(names[k]))
            entries += e
            files |= f
    languages, e, f = language_docs(names)
    entries += e
    files |= f
    ne = json.loads(fetcher().get(sources()["natural-earth-countries-50m"]["url"]))
    groups = group_docs(names["wikidata"])
    states = state_docs(names, ne, groups)
    states["coverage"] = coverage(files)
    for old in (OUT / "s").glob("*/*.json") if (OUT / "s").exists() else []:
        old.unlink()  # a series no longer listed must not linger
    size = sum(write(OUT / "s" / f"{fid}.json", doc) for fid, doc in sorted(files.items()))
    used = sorted({e["ds"] for e in entries} | {"wikidata", "ne"})
    catalogue = {"floor": FLOOR, "first_year": FIRST_YEAR, "names": {a: c["name"] for a, c in COUNTRIES.items()},
                 "sources": {k: dict(zip(("name", "licence", "link"), SOURCES[k])) for k in used},
                 "measures": sorted(entries, key=lambda e: (e["ds"] != "asi", e["ds"], e["topic"], e["label"]))}
    size += sum(write(OUT / f, d) for f, d in (("catalogue.json", catalogue), ("groups.json", groups),
                                               ("states.json", states), ("languages.json", languages)))
    print(f"{OUT.relative_to(ROOT)}: {len(files):,} series files, {len(entries):,} measures, {size / 1e6:,.1f} MB")
    for k, n in Counter(e["ds"] for e in entries).most_common():
        print(f"  {k:10s} {n:5d} measures")
    print(f"  groups: {len(groups['groups'])} ({sum(g['kind'] == 'rec' for g in groups['groups'])} RECs); "
          f"categories: {len(states['attributes'])}")
    print("  the RECs against Wikidata's current members (reported, never applied):")
    for c in groups["crosscheck"]:
        print(f"    {c['group']:8s} Wikidata lists {c['wikidata_count']:2d}; only in the owner's list: "
              f"{','.join(c['owner_only']) or '-'}; only in Wikidata: {','.join(c['wikidata_only']) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
