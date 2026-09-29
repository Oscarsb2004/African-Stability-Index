"""The MDG database, final edition, from its archived pages: dataset mdg-db-2015-07.

`values` holds every country value of every series. `codebook` holds one row per series: its name, goal, target,
indicator and last update from the series page, and every section of its metadata page ("Regional and Global
estimates" among them). A page that cannot be fetched or read, and a cell that cannot be read, are listed in the
report with the reason; nothing is skipped quietly.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from adapters import readers, wayback
from adapters.codes import Coder
from athena.table import table

NAME = "mdg-db-2015-07"
CAPTURES = Path(__file__).with_name("mdg_captures.csv")
FINAL, UNTIL = "20150706", "20171231"  # the database's last update; captures after it show the final edition
SERIES_PAGES = "mdgs.un.org/unsd/mdg/SeriesDetail.aspx"
METADATA_PAGES = "mdgs.un.org/unsd/mdg/Metadata.aspx"


def _key(pattern: str) -> Callable[[str], str | None]:
    def key(url: str) -> str | None:
        m = re.search(pattern, url, re.I)
        return m.group(1) if m else None
    return key


def discover(session, captures: Path = CAPTURES) -> pd.DataFrame:
    """The earliest capture after the final update of every series page and its metadata page. Run once; the
    result is committed."""
    def listing(prefix: str) -> str:
        response = session.get(wayback.CDX.format(prefix=prefix, since=FINAL, until=UNTIL), timeout=600)
        response.raise_for_status()
        return response.text
    pages = wayback.earliest(listing(SERIES_PAGES), _key(r"SeriesDetail\.aspx\?srid=(\d+)$"))
    metadata = wayback.earliest(listing(METADATA_PAGES), _key(r"Metadata\.aspx\?.*SeriesId=(\d+)$"))
    frame = pd.DataFrame([{"series": s, "series_capture": wayback.RAW.format(stamp=stamp, url=url),
                           "metadata_capture": wayback.RAW.format(stamp=metadata[s][0], url=metadata[s][1])
                           if s in metadata else ""}
                          for s, (stamp, url) in sorted(pages.items(), key=lambda kv: int(kv[0]))])
    frame.to_csv(captures, index=False, lineterminator="\n")
    return frame


def ingest(fetch: Callable[[str], bytes], code: Coder,
           captures: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    rows, book, problems, names = [], [], [], {}
    for capture in captures.fillna("").itertuples(index=False):
        series = str(capture.series)
        cell_problems: list[str] = []
        try:
            page = fetch(capture.series_capture)
            head = readers.series_header(page)
            found = readers.mdg_series(page, cell_problems)
        except Exception as error:  # listed in the report with its reason
            problems.append(f"series {series}: page not read: {type(error).__name__}: {error}")
            continue
        problems += [f"series {series}: {p}" for p in cell_problems]
        sections = {}
        if capture.metadata_capture:
            try:
                sections = readers.metadata_sections(fetch(capture.metadata_capture))
            except Exception as error:
                problems.append(f"series {series}: metadata not read: {type(error).__name__}: {error}")
        else:
            problems.append(f"series {series}: no metadata page captured after {FINAL}")
        book.append({"series": series, **head, "values": len(found), "series_capture": capture.series_capture,
                     "metadata_capture": capture.metadata_capture, **sections})
        edition = f"MDG database, last updated {head['last_updated']}"
        for name, year, value, nature, printed in found:
            area = code(name)
            if area is None:
                continue
            key = (series, area, year)
            if key in names:
                problems.append(f"series {series}: {name!r} and {names[key]!r} both code to {area} in {year}")
                continue
            names[key] = name
            bound = readers.BOUND.fullmatch(printed)
            rows.append({"DATASET": NAME, "SERIES": series, "REF_AREA": area, "TIME_PERIOD": str(year),
                         "OBS_VALUE": value, "OBS_STATUS": nature, "EDITION": edition, "DERIVED": False,
                         "UPPER_BOUND": float(bound.group(1)) if bound and printed.startswith("<") else None,
                         "LOWER_BOUND": float(bound.group(1)) if bound and printed.startswith(">") else None,
                         "COMMENT_OBS": printed if value is None else ""})
    code.done()
    values, codebook = table(rows), pd.DataFrame(book)
    editions = codebook["last_updated"].value_counts()
    report = [f"{NAME}: {len(captures)} series listed, {len(codebook)} read, "
              f"{(codebook['values'] > 0).sum()} with values, {len(values)} values",
              f"  editions (last updated): {dict(editions)}",
              f"  problems: {len(problems)}"] + [f"    {p}" for p in problems]
    return values, codebook, report
