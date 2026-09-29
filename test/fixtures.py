"""Synthetic sources in each publisher's format, served under the real addresses in sources.toml. They hold
invented figures, never publisher content, so tests run offline and keep third-party material out of git.

The invented world: Alpha is developed; Beta and Gamma are in Northern Africa; Delta in Eastern Asia; Epsilon in
Western Asia. The 2015 lists make Beta and Gamma least developed and Delta landlocked.
"""

from __future__ import annotations

import json

from mdg.build import load, open_project, sources

CODES = {"Alpha": "AAA", "Beta": "BBB", "Gamma": "CCC", "Delta": "DDD", "Epsilon": "EEE"}

# ── MDG 3.3: seats and women; the published values follow from them ──────────────────────────────────────────
SEATS = [("Alpha", 100, 30), ("Beta", 50, 10), ("Gamma", 40, 20), ("Delta", 60, 6), ("Epsilon 1", 20, None)]

# ── MDG 3.1: enrolment and school-age population, female and male, the same for every level and year ──────────
COUNTS = {"AAA": (90, 100, 100, 100), "BBB": (40, 50, 50, 50), "CCC": (60, 60, 60, 60), "DDD": (30, 40, 40, 40)}
PARITY = {"Alpha": 0.90, "Beta": 0.80, "Gamma": 1.00, "Delta": 0.75}

ANNEX_LINES = [
    "Indicator 3.1",
    "Ratios of girls to boys in primary, secondary and tertiary education",
] + [line for part, title in (("a", "Primary"), ("b", "Secondary"), ("c", "Tertiary")) for line in (
    f"({part}) {title} education a",
    "1991 2000 2015 b",
    "World 0.88 0.88 -",
    "Developing regions 0.87 0.87 -",
    "Northern Africa 0.91 0.91 -",
    "Eastern Asia 0.75 0.75 -",
    "Developed regions 0.90 0.90 -",
    "Least developed countries 0.91 0.91 -",
    "Report of the Secretary-General on the work of the Organization",
    "Landlocked developing countries 0.75 0.75 -",
)] + [
    "a Using gross enrolment ratios. b Projections.",
    "Indicator 3.3",
    "Proportion of seats held by women in national parliament a",
    "2014 2015",
    "World 26.0 26.4",
    "Developing regions 20.0 24.0",
    "Northern Africa 30.0 33.3",
    "Eastern Asia 10.0 10.0",
    "Western Asia - -",
    "Developed regions 30.0 30.0",
    "Least developed countries 50.0 33.3",
    "Landlocked developing countries 10.0 10.0",
    "a As at 31 January 2015.",
]


def ipu_html(countries=SEATS) -> bytes:
    body = "".join(
        f"<tr><td>{rank}</td><td>{name}</td><td>1 2014</td><td>{seats}</td><td>{'?' if women is None else women}"
        f"</td><td>{'?' if women is None else f'{100 * women / seats:.1f}%'}</td><td>---</td><td>---</td>"
        f"<td>---</td><td>---</td></tr>" for rank, (name, seats, women) in enumerate(countries, 1))
    return f"<html><body><table><tr><td>Rank</td><td>Country</td></tr>{body}</table></body></html>".encode("latin-1")


def world_html(known=250, women=66, percent=26.4) -> bytes:
    return (f'<html><body><table><tr><td colspan=2><img alt="Single House or lower House"></td></tr>'
            f"<tr><td>Total MPs</td><td>{known + 20}</td></tr><tr><td>Gender breakdown known for</td><td>{known}</td>"
            f"</tr><tr><td>Women</td><td>{women}</td></tr><tr><td>Percentage of women</td><td>{percent}%</td></tr>"
            f"</table></body></html>").encode("latin-1")


def groupings_doc() -> bytes:
    def table(names):
        return "\x07".join(names) + "\x07\x07"
    text = ("preamble\r2. MDG regional groupings: List of countries in each grouping\r\r"
            f"Developed regions \r{table(['Alpha', ''])}\r\rDeveloping regions \r\rNorthern Africa\r"
            f"{table(['Beta', 'Gamma'])}\r\rEastern Asia\r{table(['Delta'])}\rWestern Asia \r{table(['Epsilon'])}\r"
            f"3. Other groupings: Least Developed Countries as of 1 January 2011\r{table(['Gamma'])}\r"
            f"4. Other groupings: Landlocked developing countries\r{table(['Epsilon'])}\r"
            "6. Other groupings: African regions according to ECA\r\r"
            + "".join(f"SRO {region}\r\r{table([name])}\r" for region, name in
                      (("Central Africa", "Gamma"), ("Eastern Africa", "Delta"), ("North Africa", "Beta"),
                       ("West Africa", "Epsilon"), ("Southern Africa", "Alpha"))))
    return b"\xd0\xcf\x11\xe0binary" + text.encode("cp1252") + b"\x00\x00\x00"


def m49_html(codes=CODES) -> bytes:
    head = "<tr><td>Country or Area</td><td>M49 Code</td><td>ISO-alpha3 Code</td></tr>"
    listed = "".join(f"<tr><td>{n}</td><td>{i:03d}</td><td>{c}</td></tr>" for i, (n, c) in enumerate(codes.items()))
    filler = "".join(f"<tr><td>Filler {i}</td><td>{900 + i}</td><td>F{i:02d}</td></tr>" for i in range(200))
    return f'<html><table id = "downloadTableEN">{head}{listed}{filler}</table></html>'.encode()


def pdf(lines: list[str]) -> bytes:
    """A minimal one-page PDF whose text is the given lines."""
    def escape(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = "BT /F1 10 Tf 12 TL 40 800 Td " + " ".join(f"({escape(line)}) Tj T*" for line in lines) + " ET"
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
               "/Resources << /Font << /F1 5 0 R >> >> >>",
               f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
               "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = "%PDF-1.4\n", []
    for i, body in enumerate(objects, 1):
        offsets.append(len(out.encode("latin-1")))
        out += f"{i} 0 obj\n{body}\nendobj\n"
    xref = len(out.encode("latin-1"))
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    return (out + f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n").encode("latin-1")


def ldc_pdf(names=("Gamma", "Beta")) -> bytes:
    return pdf(["LIST OF LEAST DEVELOPED COUNTRIES",
                " ".join(f"{i} {n}{'1' if i == 1 else ''} 1971" for i, n in enumerate(names, 1))])


def lldc_html(regions=(("Asia", ("Delta",)),)) -> bytes:
    rows = []
    for region, names in regions:
        rows.append(f"<tr><td></td><td>{region} ({len(names)})</td></tr>")
        rows += [f"<tr><td>{i}</td><td>{n} #</td></tr>" for i, n in enumerate(names, 1)]
    return f"<html><body><h2>Country Profiles</h2><table>{''.join(rows)}</table></body></html>".encode()


def series_html(values=PARITY, years=(1991, 2000)) -> bytes:
    head = '<tr class="Head"><td>Country</td>' + "".join(f"<td>{y}</td>" for y in years) + "</tr>"
    body = "".join(f'<tr class="Data"><td>{name}</td>' + "".join(
        f'<td class="C">{v:.2f}<sup><span class="Footnotes">1</span></sup></td>' for _ in years) + "</tr>"
        for name, v in values.items())
    return f'<html><body><table><tr class="Head"><td>Series</td></tr>{head}{body}</table></body></html>'.encode()


def html(paragraphs: list[str]) -> bytes:
    return ("<html><body>" + "".join(f"<p>{p}</p>" for p in paragraphs) + "</body></html>").encode()


METADATA = {
    "metadata-557": html(["This indicator covers the single chamber in unicameral parliaments and the lower chamber "
                          "in bicameral parliaments.", "Regional averages are determined by dividing the total "
                          "number of women members by the total number of seats filled in single or lower chambers "
                          "of parliament per region.", "No adjustments are made for missing values."]),
    "metadata-611": html(["To standardise, the Gender Parity Index (GPI) of the Gross Enrolment Ratio (GER) for each "
                          "level of education is used.", "Averages are produced using the appropriate school-age "
                          "populations as weights."]),
}


def wdi_json(values: dict[str, float], years=(1991, 2000)) -> bytes:
    """An archive response; it also carries an aggregate (WLD) and an empty value, as the real one does."""
    def record(code, year, value):
        return {"variable": [{"concept": "Country", "id": code}, {"concept": "Series", "id": "S"},
                             {"concept": "Time", "id": f"YR{year}"}, {"concept": "Version", "id": "201504"}],
                "value": value}
    data = [record(c, y, v) for c, v in (values | {"WLD": 1.0, "EEE": None}).items() for y in years]
    return json.dumps({"page": 1, "pages": 1, "total": len(data), "source": {"id": "57", "data": data}}).encode()


def wdi_values() -> dict[str, dict[str, float]]:
    """The four WDI series of 3.1, by the variable name the catalogue gives them."""
    return {"enrolled": {c: ef + em for c, (ef, em, _, _) in COUNTS.items()},
            "female_share": {c: 100 * ef / (ef + em) for c, (ef, em, _, _) in COUNTS.items()},
            "ger_f": {c: 100 * ef / pf for c, (ef, _, pf, _) in COUNTS.items()},
            "ger_m": {c: 100 * em / pm for c, (_, em, _, pm) in COUNTS.items()}}


class Response:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self) -> None:
        pass


class Session:
    """Serves bytes by address, so tests never touch the network."""

    def __init__(self, files: dict[str, bytes]):
        self.files = files

    def get(self, url: str, timeout: float | None = None) -> Response:
        return Response(self.files[url])


def files(**overrides: bytes) -> dict[str, bytes]:
    """Every address the catalogue reads, mapped to synthetic bytes; keyword overrides replace a source by key."""
    sources_, catalogue = sources(), load("catalogue.toml")
    content = {"ipu-2015-02": ipu_html(), "ipu-world-2015-02": world_html(), "groupings": groupings_doc(),
               "ldc-2014": ldc_pdf(), "lldc-2014": lldc_html(), "m49": m49_html(), "annex-2015": pdf(ANNEX_LINES),
               "series-611": series_html(), "series-613": series_html(), "series-614": series_html()} | METADATA
    content |= overrides
    out = {sources_[key]["url"]: data for key, data in content.items()}
    values = wdi_values()
    for row in catalogue["indicator"]:
        years = ";".join(f"YR{y}" for y in row["years"])
        for name, ref in row["inputs"].items():
            key, series = ref.split("/", 1)
            if sources_[key]["kind"] == "wdi-archive":
                out[sources_[key]["url"].format(series=series, years=years)] = wdi_json(values[name])
    return out


def project(tmp_path, **overrides: bytes):
    return open_project(lock=tmp_path / "sources.lock", session=Session(files(**overrides)))


# ── Ingest fixtures: pages as the archive holds them, and an annex laid out by position ─────────────────────────

def series_page(values: dict[str, str], years=(1990, 1991), name="Invented series", indicator="9.9") -> bytes:
    """A series page with its header, each value a printed cell ("0.90", "<5", or "" for empty)."""
    head = '<tr class="Head"><td>Country</td>' + "".join(f"<td>{y}</td>" for y in years) + "</tr>"
    body = "".join(f'<tr class="Data"><td>{country}</td>' + "".join(
        f'<td class="E">{printed}</td>' for _ in years) + "</tr>" for country, printed in values.items())
    return (f"<html><body><div>Series Name: {name} Goal: Goal 9. Invent Target: Target 9.A: Test "
            f"Indicator: Indicator {indicator} Invented title</div><div>Series Data</div>"
            f"<div>Last updated: 06 Jul 2015</div><table>{head}{body}</table></body></html>").encode()


def metadata_page(sections: dict[str, str]) -> bytes:
    """A metadata page: each heading toggles the section below it, as the archived pages do."""
    parts = "".join(
        f'<div class="SegmentHead FloatWrap"><div class="Left"><a id="{i}" href="javascript:;" '
        f"onclick=\"TogglePanel('Section_{i}')\">{heading}</a></div><div class=\"Right\"><a id=\"Section_{i}Link\" "
        f"href=\"javascript:;\" onclick=\"TogglePanel('Section_{i}')\">Collapse</a></div></div>"
        f'<div id="Section_{i}" class="SideMargin Metadata Show"><p>{text}</p></div>'
        for i, (heading, text) in enumerate(sections.items(), 1))
    return f"<html><body>{parts}</body></html>".encode()


def positioned_pdf(words: list[tuple[float, float, float, str]]) -> bytes:
    """A one-page PDF with each word at (x, top, size): top is measured down from the top of the page."""
    def escape(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = " ".join(f"BT /F1 {size} Tf 1 0 0 1 {x} {800 - top} Tm ({escape(text)}) Tj ET"
                      for x, top, size, text in words)
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
               "/Resources << /Font << /F1 5 0 R >> >> >>",
               f"<< /Length {len(stream.encode('cp1252'))} >>\nstream\n{stream}\nendstream",
               "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    out, offsets = "%PDF-1.4\n", []
    for i, body in enumerate(objects, 1):  # Windows encoding carries the en dash, as the real annex does
        offsets.append(len(out.encode("cp1252")))
        out += f"{i} 0 obj\n{body}\nendobj\n"
    xref = len(out.encode("cp1252"))
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    return (out + f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n").encode("cp1252")


def annex_row(top: float, label: str, values: list[str], xs: list[float], indent: float = 123) -> list:
    """One table row: the label at the left, each value at its column's position, in 8-point type."""
    words, x = [], indent
    for w in label.split():  # each word after the last one's printed width and a space
        words.append((x, top, 8, w))
        x += len(w) * 0.6 * 8 + 3
    for x, value in zip(xs, values):
        for part in value.split():  # "1 774 954" is printed as three words, 2.5 points apart
            words.append((x, top, 8, part))
            x += len(part) * 0.556 * 8 + 2.5  # Helvetica's digits are 0.556 em wide
    return words


YEARS_X = [320, 380, 440]
URBAN_X = [300, 330, 360, 420, 450, 480]
ANNEX = (
    [(123, 40, 8, "Indicator"), (165, 40, 8, "9.1"), (123, 52, 8, "Invented"), (170, 52, 8, "shares"),
     (123, 64, 7, "(Percentage)"), (330, 80, 7, "1990"), (450, 80, 7, "2015"), (470, 80, 5, "b")]
    + [(x, 92, 7, w) for x, w in zip(URBAN_X, ["Total", "Urban", "Rural", "Total", "Urban", "Rural"])]
    + annex_row(106, "World", ["76", "95", "62", "91", "96", "84"], URBAN_X)
    + annex_row(118, "Northern Africa", ["87", "–", "80", "93", "<0.1", "90"], URBAN_X)
    + [(123, 130, 7, "b"), (130, 130, 7, "Projections.")]
    + [(123, 150, 8, "Indicator"), (165, 150, 8, "9.2"), (123, 162, 8, "Invented"), (170, 162, 8, "totals"),
       (123, 174, 7, "(Tons)")] + [(x, 188, 7, y) for x, y in zip(YEARS_X, ["1986", "2000", "2013"])]
    + annex_row(200, "World", ["1 774 954", "12", "9"], YEARS_X)
    + annex_row(212, "Oceania", ["0.09 (0.08:0.10)", "3", "4"], YEARS_X)
    + annex_row(224, "Atlantis", ["1", "2", "3"], YEARS_X)
    + [(123, 244, 8, "Indicator"), (165, 244, 8, "9.3"), (123, 256, 8, "Invented"), (170, 256, 8, "rates"),
       (123, 268, 8, "No"), (140, 268, 8, "global"), (170, 268, 8, "or"), (185, 268, 8, "regional"),
       (225, 268, 8, "data"), (250, 268, 8, "are"), (270, 268, 8, "available.")]
    + [(123, 288, 8, "Indicator"), (165, 288, 8, "9.4"), (123, 300, 8, "Survey"), (160, 300, 8, "coverage,"),
       (205, 300, 8, "2009-2014")]
    + annex_row(312, "Sub-Saharan Africa (30 countries)", ["37"], [330])
)

