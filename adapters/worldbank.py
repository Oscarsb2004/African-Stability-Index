"""World Bank databank bulk downloads: WDI, WGI, and any other databank database in the same layout.

A bulk download is a zip of CSV tables named after the database ({DB} below):
- {DB}CSV.csv: the values, one row per area and series, with a column per year;
- {DB}Series.csv: one row per series, with its source, aggregation method and licence;
- {DB}Country.csv: one row per area, with its region and income group (aggregates have no region);
- WDI adds {DB}footnote.csv (a note on one value), and notes per area and series and per series and year.

The edition is the date of the values file inside the zip, so it comes from the locked bytes themselves. Every
value is ingested; footnotes become COMMENT_OBS, and a footnote on a cell without a value is kept in a table of its
own. Any other file in the zip is kept verbatim as a table.
"""

from __future__ import annotations

import io
import zipfile
from datetime import date

import pandas as pd

from athena.table import table

ID = ["Country Code", "Indicator Code"]
CELL = ["REF_AREA", "SERIES", "TIME_PERIOD"]


def ingest(data: bytes, db: str) -> tuple[str, dict[str, pd.DataFrame], list[str]]:
    """The dataset's name, its tables, and the report."""
    z = zipfile.ZipFile(io.BytesIO(data))

    def read(file: str, **options) -> pd.DataFrame:
        return pd.read_csv(z.open(file), keep_default_na=False, **options)

    stamp = date(*z.getinfo(f"{db}CSV.csv").date_time[:3]).isoformat()
    name = f"{db.lower()}-{stamp}"
    years = [c for c in read(f"{db}CSV.csv", nrows=0).columns if c.isdigit()]
    wide = read(f"{db}CSV.csv", usecols=ID + years, dtype=dict.fromkeys(ID, str),
                na_values=dict.fromkeys(years, [""]), float_precision="round_trip")
    values = (wide.set_index(ID)[years].stack().dropna().rename_axis(["REF_AREA", "SERIES", "TIME_PERIOD"])
              .rename("OBS_VALUE").reset_index())
    tables = {"codebook": read(f"{db}Series.csv", dtype=str), "areas": read(f"{db}Country.csv", dtype=str)}
    report = []

    footnotes = f"{db}footnote.csv"
    if footnotes in z.namelist():
        notes = read(footnotes, dtype=str).rename(
            columns={"CountryCode": "REF_AREA", "SeriesCode": "SERIES", "DESCRIPTION": "COMMENT_OBS"})
        notes["TIME_PERIOD"] = notes.pop("Year").str.removeprefix("YR")
        values = values.merge(notes, how="left", on=CELL, validate="one_to_one")
        stray = notes.merge(values[CELL], how="left", on=CELL, indicator=True)
        tables["footnotes_without_value"] = stray[stray._merge == "left_only"].drop(columns="_merge")
        report.append(f"  footnotes: {len(notes) - len(tables['footnotes_without_value']):,} on values, "
                      f"{len(tables['footnotes_without_value']):,} on cells without a value (kept in "
                      f"footnotes_without_value)")
    for file in sorted(set(z.namelist()) - {f"{db}CSV.csv", f"{db}Series.csv", f"{db}Country.csv", footnotes}):
        tables[file.removeprefix(db).removesuffix(".csv").strip("-_").lower()] = read(file, dtype=str)

    values = table(values.assign(DATASET=name, EDITION=f"{db} {stamp}", DERIVED=False))
    licences = tables["codebook"]["License Type"].value_counts().to_dict()
    return name, {"values": values} | tables, [
        f"{name}: {len(values):,} values, {values.SERIES.nunique():,} series, {values.REF_AREA.nunique()} areas, "
        f"{years[0]} to {years[-1]}; edition {stamp}",
        *report,
        f"  licences by series: {', '.join(f'{k} {v}' for k, v in licences.items())}",
        f"  tables: {', '.join(tables)}"]
