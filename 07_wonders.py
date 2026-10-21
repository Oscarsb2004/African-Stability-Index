"""
07_wonders.py — the continent's wonders (P61), chosen by a stated rule, each with a few licensed photographs.

    python 07_wonders.py

The rule (`docs/ASI 06 Outputs and Site/Wonders/Wonders Selection.md`, first position of 2026-10-18; the owner
may add or remove a wonder, with the reason recorded in WONDERS_OWNER below):
1. Candidates are Wikidata items in the 54 member states that are World Heritage Sites, or instances (or instances of
   a direct subclass) of one of CLASSES.
2. Notability is the number of Wikipedia language editions with an article on the item (Wikidata sitelinks); items
   with fewer than MIN_LINKS are not considered, which cannot change the result since only the most notable few of
   each class are taken.
3. Take the HERITAGE most notable World Heritage Sites, and the PER_CLASS most notable of each class.
4. Every Natural Earth subregion of Africa gets at least one wonder: its most notable World Heritage Site if it has
   none yet. (Edition 1's own regions are not carried over, P105.)

Photographs: the item's main image (P18), then the first JPEG files of its Commons category (P373) in the category's
own order, skipping maps, flags, logos and diagrams, up to PHOTOS in all. A file without a stated licence is refused.
The site shows Commons renderings with each file's author and licence.

Writes web/public/data/wonders.json. Every request goes through athena.fetch and is hash-locked.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

from asi.core.countries import COUNTRIES  # noqa: E402
from asi.geography import subregions  # noqa: E402

EDITION = "2026-10-18"
OUTPUT = ROOT / "web" / "public" / "data" / "wonders.json"
CLASSES = {  # Wikidata class: the label shown; QIDs checked against Wikidata's own labels on 2026-10-18
    "Q8502": "Mountain", "Q8072": "Volcano", "Q34038": "Waterfall", "Q23397": "Lake", "Q4022": "River",
    "Q8514": "Desert", "Q9444": "Rainforest", "Q150784": "Canyon", "Q46169": "National park",
    "Q839954": "Archaeological site",
}
HERITAGE, PER_CLASS, PHOTOS, WIDTH, MIN_LINKS = 15, 3, 4, 1280, 10
SKIP = re.compile(r"map|flag|logo|diagram|locator|coat of arms|\.svg$|\.png$|\.tif", re.I)
WONDERS_OWNER: dict[str, str] = {}  # QID -> the owner's reason for adding (or "remove: reason")
REGION: dict[str, str] = {}  # each state's Natural Earth subregion, filled by main()


def query(iso3: str) -> str:
    """One state's candidates, every class at once. Asking per state takes a second or two; asking per class
    across all 54 timed out on the public query service (2026-10-18)."""
    kinds = " ".join(f"wd:{q}" for q in CLASSES)
    return f"""# Athena: ASI Wonders, edition {EDITION}
SELECT ?item ?iso3 ?kind ?heritage ?links WHERE {{
  BIND("{iso3}" AS ?iso3)
  ?country wdt:P298 ?iso3 .
  ?item wdt:P17 ?country .
  {{ ?item wdt:P1435 wd:Q9259 . BIND(true AS ?heritage) }}
  UNION
  {{ VALUES ?kind {{ {kinds} }} ?item wdt:P31/wdt:P279? ?kind . }}
  ?item wikibase:sitelinks ?links . FILTER(?links >= {MIN_LINKS})
}}"""


def get_json(fetch, url: str, tries: int = 4):
    """The public query service fails now and then under load; a failed request is retried, never cached."""
    import time

    import requests
    for attempt in range(tries):
        try:
            return json.loads(fetch.get(url))
        except (requests.RequestException, json.JSONDecodeError):
            if attempt == tries - 1:
                raise
            time.sleep(10 * (attempt + 1))


def details_query(qids: list[str]) -> str:
    """Names, descriptions, coordinates, main image and Commons category, for a shortlist only."""
    items = " ".join(f"wd:{q}" for q in qids)
    return f"""# Athena: ASI Wonders details, edition {EDITION}
SELECT ?item ?itemLabel ?itemDescription ?coord ?image ?category WHERE {{
  VALUES ?item {{ {items} }}
  OPTIONAL {{ ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en") }}
  OPTIONAL {{ ?item schema:description ?itemDescription . FILTER(LANG(?itemDescription) = "en") }}
  OPTIONAL {{ ?item wdt:P625 ?coord . }}
  OPTIONAL {{ ?item wdt:P18 ?image . }}
  OPTIONAL {{ ?item wdt:P373 ?category . }}
}}"""


def shortlist(found: dict[str, dict]) -> list[str]:
    """Every item that could be chosen once names and coordinates are known: four times each quota, and each
    subregion's leading World Heritage Sites. Only these need details."""
    by_links = sorted(found.values(), key=lambda c: (-c["links"], c["id"]))
    keep = [c["id"] for c in by_links if c["heritage"]][:HERITAGE * 4]
    for kind in CLASSES.values():
        keep += [c["id"] for c in by_links if kind in c["kinds"]][:PER_CLASS * 4]
    for region in set(REGION.values()):
        keep += [c["id"] for c in by_links if c["heritage"]
                 and any(REGION[i] == region for i in c["countries"])][:4]
    return sorted(set(keep))


def candidates(rows: list[dict[str, str]]) -> dict[str, dict]:
    """One record per item, gathering its countries, kinds and first coordinate, image and category."""
    out = {}
    for r in rows:
        qid = r["item"].rsplit("/", 1)[1]
        c = out.setdefault(qid, {"id": qid, "name": r.get("itemLabel") or qid, "description": r.get("itemDescription", ""),
                                 "countries": set(), "kinds": set(), "heritage": False, "links": int(r["links"]),
                                 "coord": None, "image": None, "category": None})
        c["countries"].add(r["iso3"])
        if r.get("heritage"):
            c["heritage"] = True
        if r.get("kind"):
            c["kinds"].add(CLASSES[r["kind"].rsplit("/", 1)[1]])
        for key in ("coord", "image", "category"):
            if r.get(key) and not c[key]:
                c[key] = r[key]
    return out


def select(found: dict[str, dict]) -> list[dict]:
    """The rule, steps 3 and 4. An item whose label is its own QID has no English name and is left out."""
    named = [c for c in found.values() if c["name"] != c["id"] and c["coord"]]
    by_links = sorted(named, key=lambda c: (-c["links"], c["id"]))
    chosen = {c["id"]: c for c in [c for c in by_links if c["heritage"]][:HERITAGE]}
    for kind in CLASSES.values():
        for c in [c for c in by_links if kind in c["kinds"]][:PER_CLASS]:
            chosen.setdefault(c["id"], c)
    regions = {REGION[i] for c in chosen.values() for i in c["countries"]}
    for region in sorted(set(REGION.values()) - regions):
        top = next((c for c in by_links if c["heritage"] and any(REGION[i] == region for i in c["countries"])), None)
        if top:
            chosen.setdefault(top["id"], top)
    for qid, reason in WONDERS_OWNER.items():
        if reason.startswith("remove") and qid in chosen:
            del chosen[qid]
        elif qid in found:
            chosen.setdefault(qid, found[qid])
    return sorted(chosen.values(), key=lambda c: (-c["links"], c["id"]))


def file_title(image_url: str) -> str:
    from urllib.parse import unquote
    return "File:" + unquote(image_url.rsplit("/", 1)[1]).replace("_", " ")


def main() -> int:
    from asi.sources import fetcher, sources
    from athena import commons

    fetch = fetcher()
    REGION.update(subregions(json.loads(fetch.get(sources()["natural-earth-countries-50m"]["url"]))))
    rows = []
    for iso3 in sorted(COUNTRIES):
        rows += commons.bindings(get_json(fetch, commons.sparql_url(query(iso3))))
    found = candidates(rows)
    short = shortlist(found)
    for i in range(0, len(short), 100):
        for d in commons.bindings(get_json(fetch, commons.sparql_url(details_query(short[i:i + 100])))):
            c = found[d["item"].rsplit("/", 1)[1]]
            c["name"] = d.get("itemLabel") or c["name"]
            c["description"] = c["description"] or d.get("itemDescription", "")
            for key in ("coord", "image", "category"):
                if d.get(key) and not c[key]:
                    c[key] = d[key]
    chosen = select(found)
    wonders, refused = [], {}
    for c in chosen:
        titles = [file_title(c["image"])] if c["image"] else []
        if c["category"]:
            for t in commons.category_files(get_json(fetch, commons.category_url(c["category"]))):
                if len(titles) >= PHOTOS * 2:
                    break
                if t not in titles and not SKIP.search(t) and t.lower().endswith((".jpg", ".jpeg")):
                    titles.append(t)
        photos = []
        if titles:
            kept, bad = commons.records(get_json(fetch, commons.imageinfo_url(titles, WIDTH)))
            refused.update(bad)
            for t in titles:
                if t in kept and len(photos) < PHOTOS:
                    k = kept[t]
                    photos.append({"src": k["rendering_url"],
                                   "thumb": k["rendering_url"].replace(f"/{WIDTH}px-", "/330px-"),
                                   "page": k["page_url"], "licence": k["licence"], "licence_url": k["licence_url"],
                                   "artist": k["artist"], "credit": k["credit"]})
        lon, lat = re.findall(r"-?\d+\.?\d*", c["coord"])[:2]
        wonders.append({"id": c["id"], "name": c["name"], "description": c["description"],
                        "kinds": sorted(c["kinds"]) + (["World Heritage Site"] if c["heritage"] else []),
                        "countries": sorted(c["countries"]), "lon": float(lon), "lat": float(lat),
                        "notability": c["links"], "photos": photos})
    doc = {"edition": EDITION, "rule": __doc__.split("The rule")[1].split("Photographs:")[0].strip(),
           "sources": [{"name": "Wikidata", "licence": "CC0", "link": "https://www.wikidata.org"},
                       {"name": "Wikimedia Commons (each photo carries its own licence)", "licence": "per file",
                        "link": "https://commons.wikimedia.org"}],
           "refused": refused, "wonders": wonders}
    OUTPUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    regions = sorted({REGION[i] for w in wonders for i in w["countries"]})
    print(f"{len(rows):,} candidate rows, {len(found):,} items; {len(wonders)} wonders in {len(regions)} regions; "
          f"{sum(len(w['photos']) for w in wonders)} photos; {len(refused)} files refused")
    for w in wonders:
        print(f"  {w['notability']:4d}  {w['name'][:40]:40s} {','.join(w['countries'])[:20]:20s} "
              f"{'/'.join(w['kinds'])[:40]:40s} photos {len(w['photos'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
