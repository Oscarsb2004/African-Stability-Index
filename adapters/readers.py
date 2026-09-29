"""Readers for the formats no library reads for us. Each takes bytes and returns plain rows.

They are strict: a row or heading they do not recognise is an error, not something silently skipped. Formats
drift, and a quiet skip is how a replication goes wrong without anyone noticing.
"""

from __future__ import annotations

import html
import io
import json
import logging
import re

from pypdf import PdfReader


class ParseError(ValueError):
    pass


# ── Text ────────────────────────────────────────────────────────────────────────────────────────────────────

def cells(row_html: str) -> list[str]:
    raw = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.S | re.I)
    return [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", c))).strip() for c in raw]


def rows(text: str) -> list[str]:
    return re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S | re.I)


def html_text(data: bytes, encoding: str = "utf-8") -> str:
    """Visible text of an HTML page, whitespace collapsed."""
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", data.decode(encoding, errors="replace"),
                  flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()


def pdf_pages(data: bytes) -> list[str]:
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    return [page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages]


def doc_text(data: bytes) -> str:
    """Text of a Word 97 file: 8-bit characters, a table cell ending in \\x07, a paragraph in \\r."""
    return re.sub(r"\s+", " ", data.decode("cp1252", errors="replace").replace("\x07", " ").replace("\r", " "))


def _count(text: str) -> int | None:
    text = text.replace("'", "").strip()
    if text in ("?", "---", ""):
        return None
    if not text.isdigit():
        raise ParseError(f"not a count: {text!r}")
    return int(text)


# ── IPU ─────────────────────────────────────────────────────────────────────────────────────────────────────

def ipu_classification(data: bytes) -> list[tuple[str, int | None, int | None, str]]:
    """(country, seats, women, printed share) for each lower or single house. A trailing footnote digit is dropped
    from the name ("South Africa 1"); "?" means not known."""
    found = [c for c in (cells(r) for r in rows(data.decode("latin-1")))
             if len(c) == 10 and re.fullmatch(r"\d+", c[3] or "")]
    if not found:
        raise ParseError("no country rows found; the page layout has changed")
    out = [(re.sub(r"\s+\d+$", "", c[1]), _count(c[3]), _count(c[4]), c[5].rstrip("%")) for c in found]
    if len({name for name, *_ in out}) != len(out):
        raise ParseError("a country appears twice")
    return out


def ipu_world(data: bytes, chamber: str = "Single House or lower House") -> dict[str, int | float]:
    text = data.decode("latin-1")
    start = text.find(f'alt="{chamber}"')
    if start < 0:
        raise ParseError(f"no block labelled {chamber!r}")
    values = [c for r in rows(text[start:text.find("</table>", start)]) for c in cells(r)]
    pairs = dict(zip(values[::2], values[1::2]))
    try:
        return {"known": _count(pairs["Gender breakdown known for"]), "women": _count(pairs["Women"]),
                "percent": float(pairs["Percentage of women"].rstrip("%"))}
    except KeyError as missing:
        raise ParseError(f"{chamber}: no {missing} row") from None


# ── The official MDG regional groupings (Word 97) ───────────────────────────────────────────────────────────

HEADINGS: dict[str, tuple[str, str] | None] = {
    "Developed regions": ("developed", "development"),
    "Developing regions": None,
    "Northern Africa": ("northern-africa", "region"),
    "Sub-Saharan Africa": ("sub-saharan-africa", "region"),
    "Latin America and the Caribbean": None,
    "Caribbean": ("caribbean", "subregion"),
    "Latin America": ("latin-america", "subregion"),
    "Caucasus and Central Asia": ("caucasus-and-central-asia", "region"),
    "Eastern Asia": ("eastern-asia", "region"),
    "Southern Asia": ("southern-asia", "region"),
    "South-eastern Asia": ("south-eastern-asia", "region"),
    "Western Asia": ("western-asia", "region"),
    "Oceania": ("oceania", "region"),
    "3. Other groupings: Least Developed Countries as of 1 January 2011": ("least-developed", "special"),
    "4. Other groupings: Landlocked developing countries": ("landlocked-developing", "special"),
    "5. Other groupings: Small Islands Developing States": ("small-island-developing", "special"),
}
LIST_START = "2. MDG regional groupings: List of countries in each grouping"
LIST_END = "6. Other groupings: African regions according to ECA"
ECA_HEADINGS = {"SRO Central Africa": "central-africa-eca", "SRO Eastern Africa": "eastern-africa-eca",
                "SRO North Africa": "north-africa-eca", "SRO West Africa": "west-africa-eca",
                "SRO Southern Africa": "southern-africa-eca"}


def groupings(data: bytes) -> set[tuple[str, str]]:
    """(country, group) for every listed group, plus the groups the list implies: developing regions, Latin
    America and the Caribbean, the world, and Eastern and Southern Asia without China and India."""
    start, end = data.find(LIST_START.encode()), data.find(LIST_END.encode())
    if start < 0 or end < 0:
        raise ParseError("the list section markers are missing; the document has changed")
    listed: list[tuple[str, str, str]] = []
    current: tuple[str, str] | None = None
    for paragraph in data[start + len(LIST_START):end].decode("cp1252").split("\r"):
        for cell in paragraph.split("\x07") if "\x07" in paragraph else [paragraph]:
            name = cell.strip()
            if not name:
                continue
            if name in HEADINGS:
                current = HEADINGS[name]
            elif "\x07" not in paragraph:
                raise ParseError(f"unknown heading {name!r}")
            elif current is None:
                raise ParseError(f"{name!r} appears before any known heading")
            else:
                listed.append((name, *current))
    pairs = {(name, group) for name, group, _ in listed}
    for name, group, level in listed:
        if level in ("region", "subregion"):
            pairs.add((name, "developing"))
        if level == "subregion":
            pairs.add((name, "latin-america-and-the-caribbean"))
        if level != "special":
            pairs.add((name, "world"))
        if group == "eastern-asia" and name != "China":
            pairs.add((name, "eastern-asia-excluding-china"))
        if group == "southern-asia" and name != "India":
            pairs.add((name, "southern-asia-excluding-india"))
        if group in ("south-eastern-asia", "oceania"):
            pairs.add((name, "south-eastern-asia-including-oceania"))
    return pairs | eca_subregions(data)


def eca_subregions(data: bytes) -> set[tuple[str, str]]:
    """(country, group) for the five African subregions of the UN Economic Commission for Africa, listed in the
    same document after the MDG groupings."""
    start = data.find(LIST_END.encode())
    if start < 0:
        raise ParseError("the ECA section marker is missing; the document has changed")
    text = data[start + len(LIST_END):].split(b"\x00")[0].decode("cp1252")
    pairs, current = set(), None
    for paragraph in text.split("\r"):
        name = paragraph.strip().strip("\x02\x03\x04\x0c").strip()
        if name in ECA_HEADINGS:
            current = ECA_HEADINGS[name]
        elif "\x07" in paragraph and current:
            pairs |= {(cell.strip(), current) for cell in paragraph.split("\x07") if cell.strip()}
    if {g for _, g in pairs} != set(ECA_HEADINGS.values()):
        raise ParseError(f"ECA subregions found: {sorted({g for _, g in pairs})}")
    return pairs


# ── Dated lists of least developed and landlocked developing countries ─────────────────────────────────────

def ldc_names(data: bytes) -> list[str]:
    """The numbered list "1 Afghanistan 1971 25 Madagascar 1991"; a footnote digit may sit on a name. The numbers
    must run 1 to n without a gap."""
    found = re.findall(r"(?:^|\s)(\d{1,2})\s+([A-Z][^\d\n]*?)\d?\s+(\d{4})(?=\s|$)", "\n".join(pdf_pages(data)))
    numbered = {int(n): name.strip() for n, name, _ in found}
    if not numbered or sorted(numbered) != list(range(1, max(numbered) + 1)):
        raise ParseError(f"the list is not numbered 1 to n: {sorted(numbered)}")
    return [numbered[n] for n in sorted(numbered)]


def lldc_names(data: bytes) -> list[str]:
    """Region headers such as "Africa (16)", then names; "#" marks a country also least developed. Each region's
    count must equal the names listed under it."""
    text = data.decode("utf-8", errors="replace")
    start = text.find("Country Profiles", text.find("<body"))
    names, counts, current = [], {}, None
    for row in rows(text[start:text.find("</table>", start)]):
        for cell in cells(row):
            cell = cell.replace("#", "").strip()
            header = re.fullmatch(r"(.+?) \((\d+)\)", cell)
            if header:
                current = header.group(1)
                counts[current] = [int(header.group(2)), 0]
            elif cell and not cell.isdigit():
                if current is None:
                    raise ParseError(f"{cell!r} appears before any region header")
                names.append(cell)
                counts[current][1] += 1
    wrong = {region: c for region, c in counts.items() if c[0] != c[1]}
    if not names or wrong:
        raise ParseError(f"region counts do not match the names listed: {wrong}")
    return names


# ── UN M49 ──────────────────────────────────────────────────────────────────────────────────────────────────

def m49_codes(data: bytes) -> dict[str, str]:
    """Country or area name to ISO-alpha3 code, from the English table."""
    table = re.search(r'<table id\s*=\s*"downloadTableEN"[^>]*>(.*?)</table>', data.decode("utf-8", "replace"),
                      flags=re.S)
    if not table:
        raise ParseError("the English M49 table is missing")
    header, *body = [cells(r) for r in rows(table.group(1))]
    name_at, iso_at = header.index("Country or Area"), header.index("ISO-alpha3 Code")
    codes = {r[name_at]: r[iso_at] for r in body if r[iso_at]}
    if len(codes) < 200:
        raise ParseError(f"only {len(codes)} codes found")
    return codes


# ── Archived MDG database series pages (the final edition, 6 July 2015) ────────────────────────────────────

NATURES = {"C": "country data", "CA": "country adjusted", "E": "estimated", "M": "modelled",
           "G": "global monitoring data", "N": "not relevant", "": "unclassified"}
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")  # growth rates and balances can be negative
BOUND = re.compile(r"[<>]\s*(\d+(?:\.\d+)?)")


def mdg_series(data: bytes, problems: list[str] | None = None) -> list[tuple[str, int, float | None, str, str]]:
    """(country, year, value, nature, printed) for every value on the page. A value's nature code is its cell's
    class. A value printed only as a bound ("<5") has no value and keeps its printed text.

    With a `problems` list, a cell that cannot be read is listed there and skipped; without one it stops the read.
    """
    def fail(message: str) -> None:
        if problems is None:
            raise ParseError(message)
        problems.append(message)

    text = data.decode("utf-8", errors="replace")
    heads = [cells(h) for h in re.findall(r'<tr class="Head">(.*?)</tr>', text, flags=re.S)]
    head = next((h for h in heads if h and h[0] == "Country"), None)
    if head is None:
        raise ParseError("no header row starting with Country")
    years = [int(y) for y in head[1:]]
    out = []
    for row in re.findall(r'<tr class="Data">(.*?)</tr>', text, flags=re.S):
        found = re.findall(r"<td([^>]*)>(.*?)</td>", row, flags=re.S)
        name = cells(f"<td>{found[0][1]}</td>")[0]
        if len(found) - 1 != len(years):
            fail(f"{name}: {len(found) - 1} cells for {len(years)} years")
            continue
        for year, (attrs, body) in zip(years, found[1:]):
            nature = (re.search(r'class="([A-Z]*)"', attrs) or [None, ""])[1]
            printed = html.unescape(re.sub(r"<sup>.*?</sup>|<[^>]+>", "", body, flags=re.S)).strip()
            if not printed:
                continue
            if nature not in NATURES:
                fail(f"{name} {year}: unknown nature code {nature!r}")
            elif NUMBER.fullmatch(printed):
                out.append((name, year, float(printed), NATURES[nature], printed))
            elif BOUND.fullmatch(printed):
                out.append((name, year, None, NATURES[nature], printed))
            else:
                fail(f"{name} {year}: unreadable value {printed!r}")
    if not out and not problems:
        raise ParseError("no values")
    return out


SERIES_LABELS = ("Series Name:", "Goal:", "Target:", "Indicator:", "Series Data")


def series_header(data: bytes) -> dict[str, str]:
    """The series page's own description: name, goal, target, indicator code and title, and last update."""
    text = html_text(data)
    found = {}
    for label, following in zip(SERIES_LABELS, SERIES_LABELS[1:]):
        m = re.search(re.escape(label) + r"\s*(.*?)\s*" + re.escape(following), text)
        found[label.rstrip(":").lower().replace(" ", "_")] = m.group(1) if m else ""
    indicator = re.match(r"Indicator\s+(\d+\.\d+[a-z]?)\s*(.*)", found.get("indicator", ""))
    updated = re.search(r"Last updated:\s*(\d{1,2} \w{3} \d{4})", text)
    return {"name": found.get("series_name", ""), "goal": found.get("goal", ""), "target": found.get("target", ""),
            "indicator": indicator.group(1) if indicator else "",
            "indicator_title": indicator.group(2) if indicator else found.get("indicator", ""),
            "last_updated": updated.group(1) if updated else ""}


def metadata_sections(data: bytes) -> dict[str, str]:
    """Each section of an archived MDG metadata page, heading to text: definition, method of computation,
    regional and global estimates, treatment of missing values, and so on."""
    text = data.decode("utf-8", errors="replace")
    out = {}
    for m in re.finditer(r"TogglePanel\('Section_(\d+)'\)\s*\">([^<]+)</a>", text):
        heading = html.unescape(m.group(2)).strip()
        if heading == "Collapse":
            continue
        start = text.find(f'<div id="Section_{m.group(1)}"', m.end())
        if start < 0:
            continue
        end = text.find('<div class="SegmentHead', start)
        out[heading] = html_text(text[start:end if end > 0 else len(text)].encode())
    return out


# ── World Bank WDI Database Archives (API source 57) ───────────────────────────────────────────────────────

def wdi_archive(data: bytes) -> list[tuple[str, int, float]]:
    """(economy code, year, value) for every non-empty value. The response must fit on one page."""
    payload = json.loads(data)
    if payload.get("pages") != 1:
        raise ParseError(f"expected one page, got {payload.get('pages')}")
    out = []
    for record in payload["source"]["data"]:
        concepts = {v["concept"]: v["id"] for v in record["variable"]}
        if record["value"] is not None:
            out.append((concepts["Country"], int(concepts["Time"].removeprefix("YR")), float(record["value"])))
    return out


# ── The 2015 statistical annex ──────────────────────────────────────────────────────────────────────────────

VALUE = r"(?:\d+\.\d+|\d+|<0\.1|[–\-�])"
YEARS = re.compile(r"(?:\d{4}(?:\s*[a-e])?\s*)+")
PART = re.compile(r"^\(([a-z])\)\s*(.*)$")
FOOTNOTE = re.compile(r"^[a-e] [A-Z]")
PAGE_HEADERS = ("Report of the Secretary-General on the work of the Organization", "Annex")


def _marker(indicator: str) -> re.Pattern[str]:
    return re.compile(rf"Indicator {re.escape(indicator)}(?![\d.])")


def annex(data: bytes, indicator: str) -> list[tuple[str, str, int, float | None]]:
    """One indicator's table, which may run over several pages: rows of (part, label, year, value)."""
    pages = pdf_pages(data)
    first = next((i for i, p in enumerate(pages) if _marker(indicator).search(p)), None)
    if first is None:
        raise ParseError(f"no table for indicator {indicator}")
    text = pages[first][_marker(indicator).search(pages[first]).start():]
    for page in pages[first + 1:]:
        other = re.search(r"Indicator \d+\.\d+", page)
        text += "\n" + (page[:other.start()] if other else page)
        if other:
            break
    return annex_rows(text, indicator)


def annex_rows(text: str, indicator: str) -> list[tuple[str, str, int, float | None]]:
    """Parts are headed "(a)", "(b)"...; a year line may carry a footnote letter ("2015 b"); a page header repeated
    inside the table is skipped. A dash means no value, never zero."""
    found = _marker(indicator).search(text)
    if found is None:
        raise ParseError(f"no table for indicator {indicator}")
    years: list[int] = []
    part, out = "", []
    for line in text[found.start():].splitlines()[1:]:
        line = line.strip()
        if re.match(r"^Indicator \d", line) or FOOTNOTE.match(line):
            break
        if line and YEARS.fullmatch(line):
            years = [int(y) for y in re.findall(r"\d{4}", line)]
            continue
        heading = PART.match(line)
        if heading:
            part, years = heading.group(1), []
            continue
        if not years or not line or line in PAGE_HEADERS:
            continue
        m = re.fullmatch(rf"(?P<label>.+?)\s+(?P<values>{VALUE}(?:\s+{VALUE}){{{len(years) - 1}}})", line)
        if not m:
            raise ParseError(f"indicator {indicator}: unrecognised row {line!r}")
        for year, value in zip(years, re.findall(VALUE, m.group("values"))):
            out.append((part, m.group("label").strip(), year, float(value) if NUMBER.fullmatch(value) else None))
    if not out:
        raise ParseError(f"indicator {indicator}: no rows parsed")
    return out
