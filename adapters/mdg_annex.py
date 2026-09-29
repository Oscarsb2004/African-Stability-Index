"""The 2015 MDG statistical annex, read by position: dataset mdg-annex-2015, the answer key.

Shells never read this dataset; only checks do. Words are placed by where they sit on the page:
- a period ("2015", "1990-1992", "around 2011") heads each column, and a sub-column (Urban, Girls) sits under one;
- a value belongs to the column above it; thousands printed with spaces ("1 774 954") are one value;
- an interval "(0.08:0.09)" belongs to the value before it;
- a letter in a smaller font is a footnote mark;
- a label broken over lines is joined.

A table whose columns are not periods, or a row whose label is not a known group, is listed with the reason. Each
layout family is handled once, never table by table.
"""

from __future__ import annotations

import io
import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass, field, replace

import pandas as pd
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar

from adapters.mdg_groupings import GROUP_NAMES, UNLISTED_GROUPS
from athena.table import table

NAME = "mdg-annex-2015"
EDITION = "The MDG Report 2015, statistical annex"
ANNEX_LABELS = {name: group for group, name in (GROUP_NAMES | UNLISTED_GROUPS).items()}
ANNEX_LABELS["South-Eastern Asia including Oceania"] = "south-eastern-asia-including-oceania"  # 6.5's spelling

SMALL = 6.8          # font size below which a letter is a footnote mark
LINE_GAP = 3.0       # words whose tops differ by less than this share a line
WORD_GAP = 1.0       # characters further apart than this start a new word
THOUSANDS_GAP = 5.5  # "1 774 954": groups of three digits closer than this join the number before
MARKER = re.compile(r"^Indicator (\d+\.\d+)$")
PERIOD = re.compile(r"^(\d{4})(?:[-–](\d{4}))?([a-e]{0,2})$")
VALUE = re.compile(r"^([<>]?)([-−]?\d+(?:\.\d+)?)([a-e]{0,2})$")
DASH = re.compile(r"^(?:[–—−-]|…|\.\.\.?)([a-e]{0,2})$")  # a dash or an ellipsis: nothing was published
INTERVAL = re.compile(r"^\(([-−]?\d+(?:\.\d+)?)\s*[:–-]\s*([-−]?\d+(?:\.\d+)?)\)$")
PART = re.compile(r"^\(([a-z])\)\s*(.*)$")
FOOTNOTE = re.compile(r"^[a-e]\s+\S")  # a table's footnotes; no row label starts with a lone lowercase letter
JOINED = re.compile(r"^([<>]?[-−]?\d+(?:\.\d+)?)(\(.+\))$")  # "41(36:46)": a value and its interval, unspaced
END = re.compile(r"^(Goal \d+|Target \d+\.[A-Z]|Sources?:)")  # what follows a table in the annex
PAGE_HEADERS = {"Annex", "Report of the Secretary-General on the work of the Organization"}
# A sub-column's breakdown and code. "Total" takes the breakdown of the other sub-columns beside it.
SUBCOLUMNS = {"Total": ("", "_T"), "Urban": ("URBANISATION", "U"), "Rural": ("URBANISATION", "R"),
              "Boys": ("SEX", "M"), "Girls": ("SEX", "F"), "Men": ("SEX", "M"), "Women": ("SEX", "F"),
              "Male": ("SEX", "M"), "Female": ("SEX", "F"), "Youth": ("AGE", "youth")}
DIMENSIONS = ("SEX", "AGE", "URBANISATION")


@dataclass(frozen=True)
class Word:
    text: str
    x0: float
    x1: float
    top: float
    size: float

    @property
    def centre(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def small(self) -> bool:
        return self.size < SMALL


def _chars(item) -> Iterable[LTChar]:
    if isinstance(item, LTChar):
        yield item
    elif hasattr(item, "__iter__"):
        for child in item:
            yield from _chars(child)


def lines(data: bytes) -> list[list[Word]]:
    """Every line of words on every page, top to bottom, each line left to right."""
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    out = []
    for page in extract_pages(io.BytesIO(data), laparams=None):
        chars = sorted(_chars(page), key=lambda c: (page.height - c.y1, c.x0))
        rows: list[list[LTChar]] = []
        for c in chars:
            top = page.height - c.y1
            if rows and abs(top - (page.height - rows[-1][0].y1)) < LINE_GAP:
                rows[-1].append(c)
            else:
                rows.append([c])
        for row in rows:
            words, current = [], []
            for c in sorted(row, key=lambda c: c.x0):
                breaks = (not c.get_text().strip() or (current and (c.x0 - current[-1].x1 > WORD_GAP
                                                                    or abs(c.size - current[-1].size) > 1.5)))
                if breaks and current:
                    words.append(current)
                    current = []
                if c.get_text().strip():
                    current.append(c)
            if current:
                words.append(current)
            out.append([Word("".join(c.get_text() for c in w), w[0].x0, w[-1].x1,
                             page.height - max(c.y1 for c in w), w[0].size) for w in words])
    return out


@dataclass
class Column:
    period: str
    centre: float
    note: str = ""
    sub: tuple[str, str] = ("", "")  # (breakdown, code), such as ("URBANISATION", "U")


@dataclass
class Table:
    indicator: str
    title: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    parts: list[dict] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def _period(match: re.Match) -> str:
    start, end, _ = match.groups()
    return f"{start}/{end}" if end else start


def _header(words: list[Word]) -> list[Column] | None:
    """The columns, if this line is a row of periods ("1990 2000", "1990-1992a", "around 2011"); else None."""
    columns, around = [], False
    for w in words:
        if w.small:
            if w.text.isalpha() and columns:
                columns[-1].note = " ".join(filter(None, [columns[-1].note, w.text]))
            continue
        m = PERIOD.match(w.text)
        if w.text == "around":
            around = True
        elif m:
            columns.append(Column(_period(m), w.centre, " ".join(filter(None, ["around" if around else "", m[3]]))))
            around = False
        else:
            return None
    return columns or None


def _values(words: list[Word]) -> tuple[list[dict], list[str]]:
    """Value groups, left to right, each with its text, position, bounds and notes; and unreadable tokens."""
    groups, bad = [], []
    split = []
    for w in words:
        joined = JOINED.match(w.text)
        if joined:
            cut = w.x0 + (w.x1 - w.x0) * len(joined[1]) / len(w.text)
            split += [replace(w, text=joined[1], x1=cut), replace(w, text=joined[2], x0=cut)]
        else:
            split.append(w)
    for w in split:
        if w.small and w.text.isalpha():
            if groups:
                groups[-1]["notes"].append(w.text)
            continue
        interval = INTERVAL.match(w.text)
        if interval:
            if groups:
                groups[-1]["lower"], groups[-1]["upper"] = (float(interval[i].replace("−", "-")) for i in (1, 2))
                groups[-1]["x1"] = w.x1  # a value and its interval sit under their column together
            else:
                bad.append(w.text)
            continue
        last = groups[-1] if groups else None
        if (last and re.fullmatch(r"\d{3}", w.text) and re.fullmatch(r"-?\d{1,3}(?: ?\d{3})*", last["text"])
                and w.x0 - last["x1"] < THOUSANDS_GAP and not last["notes"]):
            last["text"] += " " + w.text
            last["x1"] = w.x1
            continue
        if VALUE.match(w.text) or DASH.match(w.text):
            groups.append({"text": w.text, "x0": w.x0, "x1": w.x1, "notes": []})
        else:
            bad.append(w.text)
    return groups, bad


def parse(indicator: str, body: list[list[Word]]) -> Table:
    t = Table(indicator)
    part, part_title, unit, columns, prefix = "", "", "", [], []
    seen_data, ended, unreadable, in_notes = False, False, False, False
    unknown: list[str] = []  # row labels in this part that are not known groups
    read_in_part = 0

    def close_part() -> None:
        """A part whose rows are all unknown labels is a table of measures, listed once; otherwise each is listed."""
        nonlocal unknown, read_in_part
        if unknown and read_in_part:
            t.problems.extend(f"part {part or '-'}: {label!r} is not a known group" for label in unknown)
        elif unknown:
            t.problems.append(f"part {part or '-'}: not read: its rows are measures, not areas "
                              f"({unknown[0]!r} and {len(unknown) - 1} more)")
        unknown, read_in_part = [], 0

    for words in body:
        text = " ".join(w.text for w in words)
        plain = " ".join(w.text for w in words if not w.small)
        if ended or not plain or text in PAGE_HEADERS or re.fullmatch(r"\d{1,3}", text):
            continue  # nothing but footnote marks, a page header, or a page number
        if END.match(text):
            ended = True
            continue
        if FOOTNOTE.match(text) or text.startswith("Note"):  # later parts may follow, so a note ends nothing
            t.notes.append(text)
            in_notes = True
            continue
        if in_notes:
            if not PART.match(plain) and not _header(words):
                t.notes[-1] += " " + text  # a note running onto the next line
                continue
            in_notes = False
        if re.search(r"No (global or regional )?data", text):
            t.notes.append(text)
            continue
        heading = PART.match(plain)
        if heading:  # a part keeps the columns and unit above it unless it prints its own
            close_part()
            part, part_title, prefix = heading[1], heading[2], []
            seen_data, unreadable = False, False
            continue
        if plain.startswith("(") and plain.endswith(")") and not INTERVAL.match(plain):
            unit = plain.strip("()")
            continue
        header = _header(words)
        if header:
            columns, seen_data, unreadable, prefix = header, False, False, []
            entry = {"part": part, "part_title": part_title, "periods": [c.period for c in columns]}
            if not t.parts or {k: t.parts[-1].get(k) for k in entry} != entry:
                t.parts.append(entry)
            continue
        if not columns:
            if not t.parts:
                t.title.append(plain)
            elif not unreadable and any(VALUE.match(w.text) for w in words if not w.small):
                t.problems.append(f"part {part or '-'}: not read: values with no row of periods above them")
                unreadable = True
            continue
        if unreadable:
            continue
        spacing = min((b.centre - a.centre for a, b in zip(columns, columns[1:])), default=60.0)
        edge = min(c.centre for c in columns) - 0.75 * spacing
        under = [w for w in words if not w.small and w.centre >= edge]  # words beneath the column headers
        labelled = [w for w in words if not w.small and w.centre < edge]
        if not seen_data and under and not labelled:  # a line under the headers with no row label: a caption
            nearest = [min(columns, key=lambda c: abs(c.centre - w.centre)) for w in under]
            if all(w.text in SUBCOLUMNS for w in under):
                columns = [replace(c, centre=w.centre, sub=SUBCOLUMNS[w.text]) for c, w in zip(nearest, under)]
                t.parts[-1]["sub_columns"] = [w.text for w in under]
            else:
                captions = {}
                for c, w in zip(nearest, under):
                    captions.setdefault(id(c), []).append(w.text)
                if len(captions) != len(columns) or len({" ".join(v) for v in captions.values()}) != 1:
                    t.problems.append(f"part {part or '-'}: not read: its columns are {plain!r}, not periods")
                    unreadable = True
            continue  # sub-columns, or one caption repeated under every column
        label_words = [w for w in words if w.centre < edge]
        value_words = [w for w in words if w.centre >= edge]
        own = " ".join(w.text for w in label_words if not w.small)
        row_notes = [w.text for w in label_words if w.small]
        if not any(VALUE.match(w.text) or DASH.match(w.text) or INTERVAL.match(w.text) for w in value_words):
            prefix.append(plain)  # a label broken over lines, or a sub-heading
            continue
        groups, bad = _values(value_words)
        if len(groups) > len(columns) and not seen_data:  # the part's first row shows its layout
            t.problems.append(f"part {part or '-'}: not read: its rows carry {len(groups)} values under "
                              f"{len(columns)} columns, sub-columns without a known breakdown")
            unreadable = True
            continue
        if bad:
            t.problems.append(f"part {part or '-'}: unreadable {bad} in {text!r}")
            prefix = []
            continue
        label = " ".join(prefix + [own])
        if label not in ANNEX_LABELS and own in ANNEX_LABELS:
            label = own  # the lines before were a sub-heading, not the start of this label
        prefix, seen_data = [], True
        area = ANNEX_LABELS.get(label)
        if area is None:
            unknown.append(label)
            continue
        taken = {}
        for g in groups:
            centre = (g["x0"] + g["x1"]) / 2
            column = min(columns, key=lambda c: abs(c.centre - centre))
            if abs(column.centre - centre) > 0.6 * spacing or id(column) in taken:
                t.problems.append(f"part {part or '-'}: {g['text']!r} fits no column in {text!r}")
                continue
            taken[id(column)] = (column, g)
        read_in_part += 1
        for column, g in taken.values():
            t.rows.append(_row(indicator, part, unit, area, column, g, row_notes))
    close_part()
    if not t.parts and not any(re.search(r"No (global or regional )?data", n) for n in t.notes):
        t.problems.append("not read: no row of periods heads its columns (a survey table, by countries covered)")
    return t


def _row(indicator: str, part: str, unit: str, area: str, column: Column, g: dict, row_notes: list[str]) -> dict:
    value = VALUE.match(g["text"].replace(" ", ""))
    notes = [column.note] + row_notes + g["notes"] + ([value[3]] if value and value[3] else [])
    row = {"DATASET": NAME, "SERIES": indicator + part, "REF_AREA": area, "TIME_PERIOD": column.period,
           "UNIT_MEASURE": unit, "EDITION": EDITION, "DERIVED": False, "OBS_VALUE": None,
           "LOWER_BOUND": g.get("lower"), "UPPER_BOUND": g.get("upper"), "sub": column.sub}
    if value is None:  # a dash: nothing was published
        row["dash"] = True
    elif value[1] == "<":
        row["UPPER_BOUND"], notes = float(value[2]), notes + [g["text"]]
    elif value[1] == ">":
        row["LOWER_BOUND"], notes = float(value[2]), notes + [g["text"]]
    else:
        row["OBS_VALUE"] = float(value[2].replace("−", "-"))
    row["COMMENT_OBS"] = " ".join(n for n in notes if n)
    return row


def tables(data: bytes) -> list[Table]:
    """Every indicator table in the annex, in order."""
    found, body, indicator = [], [], None
    for words in lines(data):
        texts = [w.text for w in words]
        m = MARKER.match(" ".join(texts[:2])) if len(texts) >= 2 else None
        if m:
            if indicator:
                found.append(parse(indicator, body))
            indicator, body = m[1], []
        elif indicator:
            body.append(words)
    if indicator:
        found.append(parse(indicator, body))
    return found


def ingest(data: bytes) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    rows, book, problems = [], [], []
    for t in tables(data):
        published = [r for r in t.rows if not r.get("dash")]
        by_part = {}
        for r in published:
            by_part.setdefault(r["SERIES"], []).append(r)
        partial = any("not read" in p for p in t.problems)
        no_data = any(re.search(r"No (global or regional )?data", n) for n in t.notes)
        status = ("read in part" if published and partial else "read" if published
                  else "no regional data" if no_data else "not read")
        book.append({"indicator": t.indicator, "title": " ".join(t.title), "status": status,
                     "values": len(published), "dashes": len(t.rows) - len(published),
                     "parts": "; ".join(f"({p['part']}) {p['part_title']}: {', '.join(p['periods'])}"
                                        + (f" [{', '.join(p['sub_columns'])}]" if p.get("sub_columns") else "")
                                        for p in t.parts),
                     "problems": len(t.problems), "notes": " | ".join(t.notes)})
        problems += [f"indicator {t.indicator}: {p}" for p in t.problems]
        for series, part_rows in by_part.items():
            dimensions = {r["sub"][0] for r in part_rows} - {""}
            for r in part_rows:
                dimension, code = r.pop("sub")
                r.update({d: "_Z" for d in DIMENSIONS})
                if dimension:
                    r[dimension] = code
                elif code == "_T" and len(dimensions) == 1:  # "Total" beside Urban and Rural, or Girls and Boys
                    r[next(iter(dimensions))] = "_T"
                rows.append(r)
    seen, unique = set(), []
    for r in rows:
        key = (r["SERIES"], r["REF_AREA"], r["TIME_PERIOD"], r["SEX"], r["AGE"], r["URBANISATION"])
        if key in seen:
            problems.append(f"indicator {r['SERIES']}: {r['REF_AREA']} {r['TIME_PERIOD']} printed twice; first kept")
        else:
            seen.add(key)
            unique.append(r)
    values, codebook = table(unique), pd.DataFrame(book)
    counts = codebook["status"].value_counts()
    report = [f"{NAME}: {len(codebook)} indicator tables; {dict(counts)}; {len(values)} values; "
              f"{int(codebook['dashes'].sum())} dashes (nothing published)",
              f"  problems: {len(problems)}"] + [f"    {p}" for p in problems]
    return values, codebook, report
