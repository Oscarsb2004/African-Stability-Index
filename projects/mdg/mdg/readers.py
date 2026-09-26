"""Format readers for phase 1. Each fetches through the transport it is given, and parses without the network.

Parsers are strict: a row or heading they do not recognise is an error, not something silently skipped. Formats
drift, and a quiet skip is how a replication goes wrong without anyone noticing.
"""

from __future__ import annotations

import html
import io
import logging
import re

import pyarrow as pa
from pydantic import BaseModel, ConfigDict

from athena.frames import Column, Frame, Manifest
from athena.reference import membership_frame
from athena.sources import FormatReader, Recipe, Transport
from athena.vocab import Concept, DType, Profile, ReproClass, Role


class UrlParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    url: str


class UrlReader(FormatReader):
    VERSION = "0.1.0"
    Parameters = UrlParameters

    @classmethod
    def ref(cls) -> str:
        return f"{cls.ID}@{cls.VERSION}"

    def fetch(self, recipe: Recipe, transport: Transport) -> tuple[bytes, str, str]:
        params = self.check(recipe)
        data, media_type = transport.get(params.url)
        return data, params.url, media_type


class ParseError(ValueError):
    pass


def _cells(row_html: str) -> list[str]:
    raw = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.S | re.I)
    return [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", c))).strip() for c in raw]


def _count(text: str) -> int | None:
    text = text.replace("'", "").strip()
    if text in ("?", "---", ""):
        return None
    if not text.isdigit():
        raise ParseError(f"not a count: {text!r}")
    return int(text)


def html_text(data: bytes, encoding: str = "utf-8") -> str:
    """Visible text of an HTML page, whitespace collapsed. Used to check that cited quotes appear verbatim."""
    text = data.decode(encoding, errors="replace")
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()


class HtmlTextReader(UrlReader):
    ID = "reader:html-text"

    def parse(self, data: bytes, recipe: Recipe) -> str:
        return html_text(data)


# ── IPU world classification ────────────────────────────────────────────────────────────────────────────────

class IpuClassificationReader(UrlReader):
    """Seats and women in each lower or single house. The printed percentage is a published value and is left to
    `mdg.answers`; this reader returns the counts only."""

    ID = "reader:ipu-classification-html"
    PERIOD = "2015-02-01"

    @staticmethod
    def name(cell: str) -> str:
        """Drop a trailing footnote marker: the page prints "South Africa 1" for footnote 1."""
        return re.sub(r"\s+\d+$", "", cell)

    def rows(self, data: bytes) -> list[list[str]]:
        text = data.decode("latin-1")
        rows = [_cells(r) for r in re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S | re.I)]
        countries = [c for c in rows if len(c) == 10 and re.fullmatch(r"\d+", c[3] or "")]
        if not countries:
            raise ParseError("no country rows found; the page layout has changed")
        return countries

    def parse(self, data: bytes, recipe: Recipe) -> Frame:
        rows = self.rows(data)
        names = [self.name(r[1]) for r in rows]
        if len(names) != len(set(names)):
            raise ParseError("a country appears twice")
        manifest = Manifest(
            profile=Profile.CROSS_SECTION,
            columns=(
                Column(name="name", dtype=DType.STRING, role=Role.ENTITY, description="Country as the IPU names it"),
                Column(name="seats", dtype=DType.INT64, role=Role.MEASURE, unit="seats",
                       description="Seats currently filled, lower or single house"),
                Column(name="women", dtype=DType.INT64, role=Role.MEASURE, unit="seats",
                       description="Seats held by women; missing where the IPU prints ?"),
            ),
            keys=("name",), produced_by=self.ref(), repro_class=ReproClass.A, period=self.PERIOD,
        )
        table = pa.table({
            "name": pa.array(names, pa.string()),
            "seats": pa.array([_count(r[3]) for r in rows], pa.int64()),
            "women": pa.array([_count(r[4]) for r in rows], pa.int64()),
        })
        return Frame(table, manifest)


class IpuWorldReader(UrlReader):
    """The IPU's world totals for one chamber: total MPs, those whose gender is known, women, percentage."""

    ID = "reader:ipu-world-html"

    def parse(self, data: bytes, recipe: Recipe, chamber: str = "Single House or lower House") -> dict[str, float]:
        text = data.decode("latin-1")
        start = text.find(f'alt="{chamber}"')
        if start < 0:
            raise ParseError(f"no block labelled {chamber!r}")
        block = text[start:text.find("</table>", start)]
        pairs = dict(zip(*[iter([c for r in re.findall(r"<tr[^>]*>(.*?)</tr>", block, flags=re.S | re.I)
                                 for c in _cells(r)])] * 2))
        try:
            return {
                "total": _count(pairs["Total MPs"]),
                "known": _count(pairs["Gender breakdown known for"]),
                "women": _count(pairs["Women"]),
                "percent": float(pairs["Percentage of women"].rstrip("%")),
            }
        except KeyError as missing:
            raise ParseError(f"{chamber}: no {missing} row") from None


# ── The official MDG regional groupings (Word 97 document) ──────────────────────────────────────────────────

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


class GroupingsDocReader(UrlReader):
    """Reads the lists in "Regional groupings.doc". Word 97 keeps the text as 8-bit characters: a table cell ends
    with \\x07, a table row with \\x07\\x07, and a paragraph with \\r."""

    ID = "reader:mdg-groupings-doc"

    def listed(self, data: bytes) -> list[tuple[str, str, str]]:
        start, end = data.find(LIST_START.encode()), data.find(LIST_END.encode())
        if start < 0 or end < 0:
            raise ParseError("the list section markers are missing; the document has changed")
        text = data[start + len(LIST_START):end].decode("cp1252")
        rows: list[tuple[str, str, str]] = []
        current: tuple[str, str] | None = None
        for paragraph in text.split("\r"):
            if "\x07" in paragraph:
                for cell in paragraph.split("\x07"):
                    name = cell.strip()
                    if not name:
                        continue
                    if name in HEADINGS:
                        current = HEADINGS[name]
                        continue
                    if current is None:
                        raise ParseError(f"{name!r} appears before any known heading")
                    rows.append((name, *current))
                continue
            heading = paragraph.strip()
            if not heading:
                continue
            if heading not in HEADINGS:
                raise ParseError(f"unknown heading {heading!r}")
            current = HEADINGS[heading]
        return rows

    def parse(self, data: bytes, recipe: Recipe) -> Frame:
        listed = self.listed(data)
        rows = set(listed)
        for name, group, level in listed:
            if level in ("region", "subregion"):
                rows.add((name, "developing", "development"))
            if level == "subregion":
                rows.add((name, "latin-america-and-the-caribbean", "region"))
        for name, group, level in list(rows):
            if level == "development":
                rows.add((name, "world", "world"))
            if (group, level) == ("eastern-asia", "region") and name != "China":
                rows.add((name, "eastern-asia-excluding-china", "alternate"))
            if (group, level) == ("southern-asia", "region") and name != "India":
                rows.add((name, "southern-asia-excluding-india", "alternate"))
        return membership_frame(sorted(rows), produced_by=self.ref())


# ── Dated lists of least developed and landlocked developing countries ─────────────────────────────────────

def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    logging.getLogger("pypdf").setLevel(logging.ERROR)
    return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)


class LdcListReader(UrlReader):
    """The numbered list of least developed countries: "1 Afghanistan 1971 25 Madagascar 1991". A footnote digit
    may sit on a name ("Vanuatu1"). The numbers must run 1 to n without a gap."""

    ID = "reader:ldc-list-pdf"
    GROUP = ("least-developed", "special")

    def names(self, data: bytes) -> list[str]:
        found = re.findall(r"(?:^|\s)(\d{1,2})\s+([A-Z][^\d\n]*?)\d?\s+(\d{4})(?=\s|$)", _pdf_text(data))
        numbered = {int(n): name.strip() for n, name, _ in found}
        if not numbered or sorted(numbered) != list(range(1, max(numbered) + 1)):
            raise ParseError(f"the list is not numbered 1 to n: {sorted(numbered)}")
        return [numbered[n] for n in sorted(numbered)]

    def parse(self, data: bytes, recipe: Recipe) -> Frame:
        return membership_frame([(n, *self.GROUP) for n in self.names(data)], produced_by=self.ref())


class LldcProfilesReader(UrlReader):
    """The UN-OHRLLS country-profiles table: region headers such as "Africa (16)", then numbered names; "#" marks
    countries that are also least developed. Each region's count must equal the names listed under it."""

    ID = "reader:lldc-profiles-html"
    GROUP = ("landlocked-developing", "special")

    def names(self, data: bytes) -> list[str]:
        text = data.decode("utf-8", errors="replace")
        start = text.find("Country Profiles", text.find("<body"))
        table = text[start:text.find("</table>", start)]
        names, counts, current = [], {}, None
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", table, flags=re.S | re.I):
            for cell in _cells(row):
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
        wrong = {r: c for r, c in counts.items() if c[0] != c[1]}
        if not names or wrong:
            raise ParseError(f"region counts do not match the names listed: {wrong}")
        return names

    def parse(self, data: bytes, recipe: Recipe) -> Frame:
        return membership_frame([(n, *self.GROUP) for n in self.names(data)], produced_by=self.ref())


# ── UN M49 overview ─────────────────────────────────────────────────────────────────────────────────────────

class M49Reader(UrlReader):
    """Country or area name to ISO-alpha3 code, from the English table on the M49 overview page."""

    ID = "reader:m49-html"

    def parse(self, data: bytes, recipe: Recipe) -> dict[str, str]:
        text = data.decode("utf-8", errors="replace")
        table = re.search(r'<table id\s*=\s*"downloadTableEN"[^>]*>(.*?)</table>', text, flags=re.S)
        if not table:
            raise ParseError("the English M49 table is missing")
        rows = [_cells(r) for r in re.findall(r"<tr[^>]*>(.*?)</tr>", table.group(1), flags=re.S)]
        header, body = rows[0], rows[1:]
        name_at, iso_at = header.index("Country or Area"), header.index("ISO-alpha3 Code")
        codes = {r[name_at]: r[iso_at] for r in body if r[iso_at]}
        if len(codes) < 200:
            raise ParseError(f"only {len(codes)} codes found")
        return codes


# ── Archived MDG series pages (the database's final country values, 6 July 2015) ────────────────────────────

NATURES = {"C": "country data", "CA": "country adjusted", "E": "estimated", "M": "modelled",
           "G": "global monitoring data", "N": "not relevant", "": "unclassified"}


class MdgSeriesReader(UrlReader):
    """One MDG database series: a row per country, a column per year. Each value's cell carries its nature code as
    its class (C, CA, E, M...), and a footnote number may follow the value."""

    ID = "reader:mdg-series-html"

    def parse(self, data: bytes, recipe: Recipe) -> Frame:
        text = data.decode("utf-8", errors="replace")
        heads = [_cells(h) for h in re.findall(r'<tr class="Head">(.*?)</tr>', text, flags=re.S)]
        head = next((h for h in heads if h and h[0] == "Country"), None)
        if head is None:
            raise ParseError("no header row starting with Country")
        years = [int(y) for y in head[1:]]
        rows = []
        for row in re.findall(r'<tr class="Data">(.*?)</tr>', text, flags=re.S):
            cells = re.findall(r'<td([^>]*)>(.*?)</td>', row, flags=re.S)
            name = _cells(f"<td>{cells[0][1]}</td>")[0]
            if len(cells) - 1 != len(years):
                raise ParseError(f"{name}: {len(cells) - 1} cells for {len(years)} years")
            for year, (attrs, body) in zip(years, cells[1:]):
                found = re.search(r'class="([A-Z]*)"', attrs)
                nature = found.group(1) if found else ""
                note = re.search(r">(\d+)</span>", body)
                value = html.unescape(re.sub(r"<sup>.*?</sup>|<[^>]+>", "", body, flags=re.S)).strip()
                if not value:
                    continue
                if nature not in NATURES or not NUMBER.fullmatch(value):
                    raise ParseError(f"{name} {year}: unexpected cell {nature!r} {value!r}")
                rows.append((name, year, float(value), NATURES[nature], note.group(1) if note else ""))
        if not rows:
            raise ParseError("no values")
        manifest = Manifest(
            profile=Profile.PANEL,
            columns=(Column(name="name", dtype=DType.STRING, role=Role.ENTITY),
                     Column(name="year", dtype=DType.INT64, role=Role.TIME, concept=Concept.TIME_PERIOD),
                     Column(name="value", dtype=DType.FLOAT64, role=Role.MEASURE, unit="as published",
                            concept=Concept.OBS_VALUE),
                     Column(name="nature", dtype=DType.STRING, role=Role.STATUS, concept=Concept.OBS_STATUS),
                     Column(name="footnote", dtype=DType.STRING, role=Role.CATEGORY)),
            keys=("name", "year"), produced_by=self.ref(), repro_class=ReproClass.C,
        )
        columns = list(zip(*rows))
        return Frame(pa.table({"name": pa.array(columns[0], pa.string()), "year": pa.array(columns[1], pa.int64()),
                               "value": pa.array(columns[2], pa.float64()),
                               "nature": pa.array(columns[3], pa.string()),
                               "footnote": pa.array(columns[4], pa.string())}), manifest)


# ── UNESCO Institute for Statistics public API ──────────────────────────────────────────────────────────────

class UisApiReader(UrlReader):
    """Records from the UIS public data API: one per indicator, country and year. A value UIS estimated carries
    the qualifier UIS_EST."""

    ID = "reader:uis-api-json"

    def parse(self, data: bytes, recipe: Recipe) -> Frame:
        import json

        payload = json.loads(data)
        records = payload.get("records")
        if not records:
            raise ParseError(f"no records; hints: {payload.get('hints')}")
        manifest = Manifest(
            profile=Profile.PANEL,
            columns=(Column(name="area", dtype=DType.STRING, role=Role.ENTITY, concept=Concept.REF_AREA),
                     Column(name="indicator", dtype=DType.STRING, role=Role.CATEGORY),
                     Column(name="year", dtype=DType.INT64, role=Role.TIME, concept=Concept.TIME_PERIOD),
                     Column(name="value", dtype=DType.FLOAT64, role=Role.MEASURE, unit="as published",
                            concept=Concept.OBS_VALUE),
                     Column(name="qualifier", dtype=DType.STRING, role=Role.STATUS, concept=Concept.OBS_STATUS)),
            keys=("area", "indicator", "year"), produced_by=self.ref(), repro_class=ReproClass.B,
        )
        return Frame(pa.table({
            "area": pa.array([r["geoUnit"] for r in records], pa.string()),
            "indicator": pa.array([r["indicatorId"] for r in records], pa.string()),
            "year": pa.array([r["year"] for r in records], pa.int64()),
            "value": pa.array([None if r["value"] is None else float(r["value"]) for r in records], pa.float64()),
            "qualifier": pa.array([r["qualifier"] or "" for r in records], pa.string()),
        }), manifest)


# ── The 2015 statistical annex (answers only) ───────────────────────────────────────────────────────────────

VALUE = r"(?:\d+\.\d+|\d+|<0\.1|[–\-�])"
NUMBER = re.compile(r"\d+(?:\.\d+)?")
YEARS = re.compile(r"(?:\d{4}(?:\s*[a-e])?\s*)+")
PART = re.compile(r"^\(([a-z])\)\s*(.*)$")
FOOTNOTE = re.compile(r"^[a-e] [A-Z]")
PAGE_HEADERS = ("Report of the Secretary-General on the work of the Organization", "Annex")


class AnnexTableReader(UrlReader):
    """One indicator's table from the annex. Only `mdg.answers` calls this."""

    ID = "reader:mdg-annex-pdf"

    def pages(self, data: bytes) -> list[str]:
        from pypdf import PdfReader

        logging.getLogger("pypdf").setLevel(logging.ERROR)
        return [p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages]

    def parse(self, data: bytes, recipe: Recipe, indicator: str = "3.3") -> list[tuple[str, int, float | None]]:
        return [(label, year, value) for _, label, year, value in self.parts(data, indicator)]

    def parts(self, data: bytes, indicator: str) -> list[tuple[str | None, str, int, float | None]]:
        """Rows of (part, label, year, value). A table may run over several pages and be split into parts."""
        pages = self.pages(data)
        first = next((i for i, p in enumerate(pages) if _marker(indicator).search(p)), None)
        if first is None:
            raise ParseError(f"no table for indicator {indicator}")
        text = pages[first][_marker(indicator).search(pages[first]).start():]
        for page in pages[first + 1:]:
            other = re.search(r"Indicator \d+\.\d+", page)
            if other:
                text += "\n" + page[:other.start()]
                break
            text += "\n" + page
        return parse_annex_parts(text, indicator)


def _marker(indicator: str) -> re.Pattern[str]:
    return re.compile(rf"Indicator {re.escape(indicator)}(?![\d.])")


def parse_annex_text(page: str, indicator: str) -> list[tuple[str, int, float | None]]:
    """Rows of (label, year, value) from the text of one annex table. A dash means no value, never zero."""
    return [(label, year, value) for _, label, year, value in parse_annex_parts(page, indicator)]


def parse_annex_parts(text: str, indicator: str) -> list[tuple[str | None, str, int, float | None]]:
    """Rows of (part, label, year, value). Parts are headed "(a)", "(b)"...; a year line may carry a footnote
    letter ("2015 b"); a page header repeated inside the table is skipped."""
    found = _marker(indicator).search(text)
    if found is None:
        raise ParseError(f"no table for indicator {indicator}")
    years: list[int] = []
    part: str | None = None
    out: list[tuple[str | None, str, int, float | None]] = []
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
        values = re.findall(VALUE, m.group("values"))
        for year, value in zip(years, values):
            out.append((part, m.group("label").strip(), year, float(value) if NUMBER.fullmatch(value) else None))
    if not out:
        raise ParseError(f"indicator {indicator}: no rows parsed")
    return out


READERS = {r.ID: r for r in (HtmlTextReader, IpuClassificationReader, IpuWorldReader, GroupingsDocReader,
                              M49Reader, AnnexTableReader, LdcListReader, LldcProfilesReader, MdgSeriesReader,
                              UisApiReader)}
