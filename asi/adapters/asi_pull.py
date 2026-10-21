"""The ASI's own pull of WDI and WGI series, frozen in its repository: the inputs of every score published so far.

The ASI's retired pull script wrote this workbook through the World Bank API:
- `raw_data` holds one row per country, variable and year;
- `pull_log` names the World Bank series behind each variable;
- `coverage_report` summarises each series.

The values become a dataset keyed by the World Bank's series codes, so the ASI reads them exactly as it reads WDI
and WGI. The edition is the workbook's creation date, taken from its own document properties.
"""

from __future__ import annotations

import io
import re
import zipfile

import pandas as pd

from athena.table import table


def ingest(data: bytes) -> tuple[str, dict[str, pd.DataFrame], list[str]]:
    """The dataset's name, its tables, and the report. A variable that pull_log cannot place stops the ingest."""
    properties = zipfile.ZipFile(io.BytesIO(data)).read("docProps/core.xml").decode("utf-8")
    created = re.search(r"<dcterms:created[^>]*>(\d{4}-\d{2}-\d{2})", properties).group(1)
    name = f"asi-pull-{created}"
    book = pd.ExcelFile(io.BytesIO(data))
    raw, log = book.parse("raw_data"), book.parse("pull_log", dtype=str)
    codes = log.set_index("variable_name")["series_code"]
    unknown = sorted(set(raw.variable_name) - set(codes.index))
    if unknown:
        raise ValueError(f"variables with no series in pull_log: {unknown}")
    values = table(pd.DataFrame({
        "DATASET": name, "SERIES": raw.variable_name.map(codes), "REF_AREA": raw.iso3,
        "TIME_PERIOD": raw.year.astype(int).astype(str), "OBS_VALUE": raw.value.astype(float),
        "EDITION": f"ASI pull {created}", "DERIVED": False}))
    return name, {"values": values, "codebook": log, "coverage": book.parse("coverage_report", dtype=str)}, [
        f"{name}: {len(values):,} values, {values.SERIES.nunique()} series, {values.REF_AREA.nunique()} areas, "
        f"{values.TIME_PERIOD.min()} to {values.TIME_PERIOD.max()}; edition {created}"]
