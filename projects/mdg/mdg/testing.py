"""Synthetic fixtures in each source's format. They hold invented figures, never publisher content, so the tests
run offline and keep third-party material out of git (decision ST6)."""

from __future__ import annotations

from datetime import datetime, timezone

from athena.sources import Snapshot
from athena.store import Store
from mdg.sources import (ANNEX, GROUPINGS, IPU_CLASSIFICATION, IPU_WORLD, LDC_2014, LLDC_2014, M49_OVERVIEW,
                         METADATA_557, RECIPES, SOURCES)

# name, seats, women (None prints as ?)
COUNTRIES = [("Alpha", 100, 30), ("Beta", 50, 10), ("Gamma", 40, 20), ("Delta", 60, 6), ("Epsilon 1", 20, None)]
CODES = {"Alpha": "AAA", "Beta": "BBB", "Gamma": "CCC", "Delta": "DDD", "Epsilon": "EEE"}
# developed: Alpha; developing: Northern Africa = Beta, Gamma; Eastern Asia = Delta, China-like none; LDC = Gamma


def ipu_html(countries=COUNTRIES) -> bytes:
    rows = []
    for rank, (name, seats, women) in enumerate(countries, 1):
        pct = "?" if women is None else f"{100 * women / seats:.1f}%"
        rows.append(f"<tr><td>{rank}</td><td>{name}</td><td>1 2014</td><td>{seats}</td>"
                    f"<td>{'?' if women is None else women}</td><td>{pct}</td>"
                    f"<td>---</td><td>---</td><td>---</td><td>---</td></tr>")
    body = "".join(rows)
    return (f"<html><body><table><tr><td>Rank</td><td>Country</td><td>Lower or single House</td>"
            f"<td>Upper House or Senate</td></tr><tr><td>Elections</td><td>Seats*</td><td>Women</td><td>% W</td>"
            f"<td>Elections</td><td>Seats*</td><td>Women</td><td>% W</td></tr>{body}</table>"
            f"<p>* Figures correspond to the number of seats currently filled in Parliament</p></body></html>"
            ).encode("latin-1")


def world_html(known=250, women=66, percent=26.4) -> bytes:
    block = (f'<table><tr><td colspan=2><img alt="Single House or lower House"></td></tr>'
             f"<tr><td>Total MPs</td><td>{known + 20}</td></tr><tr><td>Gender breakdown known for</td>"
             f"<td>{known}</td></tr><tr><td>Men</td><td>{known - women}</td></tr><tr><td>Women</td><td>{women}</td>"
             f"</tr><tr><td>Percentage of women</td><td>{percent}%</td></tr></table>")
    return f"<html><body>{block}</body></html>".encode("latin-1")


def groupings_doc(ldc=("Gamma",)) -> bytes:
    def table(names):
        return "\x07".join(names) + "\x07\x07"
    text = ("preamble\r2. MDG regional groupings: List of countries in each grouping\r\r"
            f"Developed regions \r{table(['Alpha', ''])}\r\rDeveloping regions \r\rNorthern Africa\r"
            f"{table(['Beta', 'Gamma'])}\r\rEastern Asia\r{table(['Delta'])}\r"
            f"Western Asia \r{table(['Epsilon'])}\r"
            f"3. Other groupings: Least Developed Countries as of 1 January 2011\r{table(list(ldc))}\r"
            f"4. Other groupings: Landlocked developing countries\r{table(['Epsilon'])}\r"
            "6. Other groupings: African regions according to ECA\rrest")
    return b"\xd0\xcf\x11\xe0binary" + text.encode("cp1252") + b"\x00\x00\x00"


def m49_html() -> bytes:
    head = ("<tr><td>Country or Area</td><td>M49 Code</td><td>ISO-alpha3 Code</td></tr>")
    rows = "".join(f"<tr><td>{n}</td><td>{i:03d}</td><td>{c}</td></tr>" for i, (n, c) in enumerate(CODES.items()))
    filler = "".join(f"<tr><td>Filler {i}</td><td>{900 + i}</td><td>F{i:02d}</td></tr>" for i in range(200))
    return f'<html><table id = "downloadTableEN">{head}{rows}{filler}</table></html>'.encode()


def metadata_html() -> bytes:
    return ("<html><body><p>This indicator covers the single chamber in unicameral parliaments and the lower chamber "
            "in bicameral parliaments.</p><p>Regional averages are determined by dividing the total number of women "
            "members by the total number of seats filled in single or lower chambers of parliament per region.</p>"
            "<p>No adjustments are made for missing values.</p></body></html>").encode()


def pdf(lines: list[str]) -> bytes:
    """A minimal one-page PDF whose text is the given lines, one per line."""
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = "BT /F1 10 Tf 12 TL 40 800 Td " + " ".join(f"({esc(l)}) Tj T*" for l in lines) + " ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = "%PDF-1.4\n", []
    for i, body in enumerate(objects, 1):
        offsets.append(len(out.encode("latin-1")))
        out += f"{i} 0 obj\n{body}\nendobj\n"
    xref = len(out.encode("latin-1"))
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    return out.encode("latin-1")


GOAL3_ANNEX_LINES = [
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
    "Indicator 3.2",
    "Share of women in wage employment in the non-agri cultural sector",
    "1990 2000 2005 2013",
    "World 35.4 37.6 38.5 39.9",
    "Developed regions 44.7 46.2 47.0 47.8",
]

ANNEX_LINES = GOAL3_ANNEX_LINES + [
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


def annex_pdf(lines=ANNEX_LINES) -> bytes:
    return pdf(lines)


def ldc_pdf(names=("Gamma", "Beta")) -> bytes:
    entries = " ".join(f"{i} {n}1 1971" if i == 1 else f"{i} {n} 1971" for i, n in enumerate(names, 1))
    return pdf(["LIST OF LEAST DEVELOPED COUNTRIES", entries])


def lldc_html(regions=(("Asia", ("Delta",)),)) -> bytes:
    rows = []
    for region, names in regions:
        rows.append(f"<tr><td></td><td>{region} ({len(names)})</td></tr>")
        rows += [f"<tr><td>{i}</td><td>{n} #</td></tr>" for i, n in enumerate(names, 1)]
    return (f"<html><head><title>x</title></head><body><h2>Country Profiles</h2><table>{''.join(rows)}</table>"
            f"</body></html>").encode()


# Goal 3 fixtures. Enrolment (female, male) and school-age population (female, male) per country, the same for
# every level and year. Expected ratios: Alpha 0.90, Beta 0.80, Gamma 1.00, Delta 0.75; Epsilon has no counts.
UIS_COUNTS_BY_AREA = {"AAA": (90, 100, 100, 100), "BBB": (40, 50, 50, 50), "CCC": (60, 60, 60, 60),
                      "DDD": (30, 40, 40, 40)}
PARITY = {"Alpha": 0.90, "Beta": 0.80, "Gamma": 1.00, "Delta": 0.75}


def uis_json(codes: tuple[str, ...], values: dict[str, tuple[float, ...]], years=(1991, 2000)) -> bytes:
    import json
    records = [{"indicatorId": code, "geoUnit": area, "year": year, "value": vals[i], "magnitude": None,
                "qualifier": None}
               for area, vals in values.items() for year in years for i, code in enumerate(codes)]
    return json.dumps({"hints": [], "records": records}).encode()


def series_html(values: dict[str, float], years=(1991, 2000), decimals: int = 2) -> bytes:
    head = "<tr class=\"Head\"><td>Country</td>" + "".join(f"<td>{y}</td>" for y in years) + "</tr>"
    rows = "".join(f"<tr class=\"Data\"><td>{name}</td>" + "".join(
        f"<td class=\"C\">{v:.{decimals}f}<sup><span class=\"Footnotes\">1</span></sup></td>" for _ in years)
        + "</tr>" for name, v in values.items())
    return (f"<html><body><div>Last updated: 06 Jul 2015</div><table><tr class=\"Head\"><td>Series</td></tr>"
            f"{head}{rows}</table></body></html>").encode()


def metadata_31_html() -> bytes:
    return ("<html><body><p>To standardise, the Gender Parity Index (GPI) of the Gross Enrolment Ratio (GER) for "
            "each level of education is used.</p><p>Then, the number enrolled in each level is divided by the "
            "population of official school age for that level of education, and multiplied by 100.</p><p>Averages "
            "are produced using the appropriate school-age populations as weights.</p><p>Regional averages are made "
            "using the best possible non-publishable estimates where no publishable data exist.</p></body></html>").encode()


def metadata_32_html() -> bytes:
    return ("<html><body><p>The indicator is calculated as the number of women in non-agricultural paid employment "
            "divided by the total number of persons in paid employment in the non-agricultural sector.</p><p>Shares "
            "in the benchmark year 1990.</p><p>These imputed values are used solely for the production of the "
            "regional and global estimates of the indicator.</p></body></html>").encode()


def goal3_content() -> dict[str, bytes]:
    from mdg.sources import LEVELS, METADATA, SERIES, UIS_COUNTS, UIS_GER

    ger = {a: (100 * ef / pf, 100 * em / pm) for a, (ef, em, pf, pm) in UIS_COUNTS_BY_AREA.items()}
    content = {SERIES[722].id: series_html({"Alpha": 45.0, "Beta": 30.0}, years=(1990, 2013), decimals=1),
               METADATA[722].id: metadata_32_html()}
    for srid in (611, 613, 614):
        content[SERIES[srid].id] = series_html(PARITY)
        content[METADATA[srid].id] = metadata_31_html()
    for part, (level, ef, em, pf, pm, gf, gm, _s) in LEVELS.items():
        content[UIS_COUNTS[part].id] = uis_json((ef, em, pf, pm), UIS_COUNTS_BY_AREA)
        content[UIS_GER[part].id] = uis_json((gf, gm), ger)
    return content


def fill(store: Store, **overrides: bytes) -> Store:
    """Put one snapshot per recipe into the store; keyword overrides replace a recipe's bytes by recipe slug."""
    content = {
        IPU_CLASSIFICATION.id: ipu_html(), IPU_WORLD.id: world_html(), GROUPINGS.id: groupings_doc(),
        METADATA_557.id: metadata_html(), ANNEX.id: annex_pdf(), M49_OVERVIEW.id: m49_html(),
        LDC_2014.id: ldc_pdf(), LLDC_2014.id: lldc_html(),
    } | goal3_content()
    for slug, data in overrides.items():
        content[f"recipe:{slug}"] = data
    for recipe in RECIPES:
        data = content[recipe.id]
        store.put(data, Snapshot.of(data, source=SOURCES[recipe.source], recipe=recipe,
                                    url=str(recipe.parameters["url"]), media_type="application/octet-stream",
                                    retrieved_at=datetime(2026, 9, 26, tzinfo=timezone.utc)))
    return store
