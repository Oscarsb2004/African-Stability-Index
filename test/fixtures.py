"""Synthetic sources in each publisher's format, served under the real addresses in sources.toml. They hold
invented figures, never publisher content, so tests run offline and keep third-party material out of git.

The invented world: Alpha is developed; Beta and Gamma are in Northern Africa; Delta in Eastern Asia; Epsilon in
Western Asia. The 2015 lists make Beta and Gamma least developed and Delta landlocked.
"""

from __future__ import annotations

import json

from mdg.build import load, open_project

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
            "6. Other groupings: African regions according to ECA\rrest")
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
    sources, catalogue = load("sources.toml"), load("catalogue.toml")
    content = {"ipu-2015-02": ipu_html(), "ipu-world-2015-02": world_html(), "groupings": groupings_doc(),
               "ldc-2014": ldc_pdf(), "lldc-2014": lldc_html(), "m49": m49_html(), "annex-2015": pdf(ANNEX_LINES),
               "series-611": series_html(), "series-613": series_html(), "series-614": series_html()} | METADATA
    content |= overrides
    out = {sources[key]["url"]: data for key, data in content.items()}
    values = wdi_values()
    for row in catalogue["indicator"]:
        years = ";".join(f"YR{y}" for y in row["years"])
        for name, ref in row["inputs"].items():
            key, series = ref.split("/", 1)
            if sources[key]["kind"] == "wdi-archive":
                out[sources[key]["url"].format(series=series, years=years)] = wdi_json(values[name])
    return out


def project(tmp_path, **overrides: bytes):
    return open_project(lock=tmp_path / "sources.lock", session=Session(files(**overrides)))
