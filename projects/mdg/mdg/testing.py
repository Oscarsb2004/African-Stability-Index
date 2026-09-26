"""Synthetic fixtures in each source's format. They hold invented figures, never publisher content, so the tests
run offline and keep third-party material out of git (decision ST6)."""

from __future__ import annotations

from datetime import datetime, timezone

from athena.sources import Snapshot
from athena.store import Store
from mdg.sources import (ANNEX, GROUPINGS, IPU_CLASSIFICATION, IPU_WORLD, M49_OVERVIEW, METADATA_557, RECIPES,
                         SOURCES)

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


ANNEX_LINES = [
    "Indicator 3.3",
    "Proportion of seats held by women in national parliament a",
    "2014 2015",
    "World 26.0 26.4",
    "Developing regions 20.0 24.0",
    "Northern Africa 30.0 33.3",
    "Eastern Asia 10.0 10.0",
    "Western Asia - -",
    "Developed regions 30.0 30.0",
    "Least developed countries 50.0 50.0",
    "a As at 31 January 2015.",
]


def annex_pdf(lines=ANNEX_LINES) -> bytes:
    return pdf(lines)


def fill(store: Store, **overrides: bytes) -> Store:
    """Put one snapshot per recipe into the store; keyword overrides replace a recipe's bytes by recipe slug."""
    content = {
        IPU_CLASSIFICATION.id: ipu_html(), IPU_WORLD.id: world_html(), GROUPINGS.id: groupings_doc(),
        METADATA_557.id: metadata_html(), ANNEX.id: annex_pdf(), M49_OVERVIEW.id: m49_html(),
    }
    for slug, data in overrides.items():
        content[f"recipe:{slug}"] = data
    for recipe in RECIPES:
        data = content[recipe.id]
        store.put(data, Snapshot.of(data, source=SOURCES[recipe.source], recipe=recipe,
                                    url=str(recipe.parameters["url"]), media_type="application/octet-stream",
                                    retrieved_at=datetime(2026, 9, 26, tzinfo=timezone.utc)))
    return store
