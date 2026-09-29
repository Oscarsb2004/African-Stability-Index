"""The common format (P31): one long table with SDMX column names, checked by pandera.

Every dataset and every result has this shape, so any shell or template can use any of them. Values stay in full
precision; rounding happens once, at the output (P33). A period is text, as SDMX writes it: "2015", or "1990/1992"
for a range. A value the publisher printed only as a bound ("<0.1") has no OBS_VALUE, carries the bound, and keeps
the printed text in COMMENT_OBS.
"""

from __future__ import annotations

import hashlib
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd
import pandera.pandas as pa

COLUMNS = ["DATASET", "SERIES", "REF_AREA", "TIME_PERIOD", "OBS_VALUE", "LOWER_BOUND", "UPPER_BOUND",
           "UNIT_MEASURE", "OBS_STATUS", "COMMENT_OBS", "EDITION", "DERIVED"]
BREAKDOWNS = ["SEX", "AGE", "URBANISATION"]
KEYS = ["DATASET", "SERIES", "REF_AREA", "TIME_PERIOD"]
DEFAULTS = {"LOWER_BOUND": np.nan, "UPPER_BOUND": np.nan, "UNIT_MEASURE": "", "OBS_STATUS": "", "COMMENT_OBS": ""}
NUMBERS = ["OBS_VALUE", "LOWER_BOUND", "UPPER_BOUND"]


def _keys(frame: pd.DataFrame) -> list[str]:
    return KEYS + [b for b in BREAKDOWNS if b in frame.columns]


SCHEMA = pa.DataFrameSchema(
    {"DATASET": pa.Column(str), "SERIES": pa.Column(str), "REF_AREA": pa.Column(str), "TIME_PERIOD": pa.Column(str),
     "OBS_VALUE": pa.Column(float, nullable=True), "LOWER_BOUND": pa.Column(float, nullable=True),
     "UPPER_BOUND": pa.Column(float, nullable=True), "UNIT_MEASURE": pa.Column(str), "OBS_STATUS": pa.Column(str),
     "COMMENT_OBS": pa.Column(str), "EDITION": pa.Column(str), "DERIVED": pa.Column(bool),
     **{b: pa.Column(str, required=False) for b in BREAKDOWNS}},
    checks=[
        pa.Check(lambda f: ~np.isinf(f[NUMBERS].astype(float)).any(axis=1), error="finite values only"),
        pa.Check(lambda f: f["OBS_VALUE"].notna() | (f["COMMENT_OBS"] != ""),
                 error="a row without a value must say what was printed"),
        pa.Check(lambda f: ~f.duplicated(_keys(f), keep=False), error="each key appears once"),
    ],
    strict=True, coerce=True,
)


def table(rows: list[dict] | pd.DataFrame) -> pd.DataFrame:
    """Rows to a validated common-format table, sorted by its keys. Missing optional cells get their defaults; an
    unknown column is refused, not dropped."""
    frame = pd.DataFrame(rows) if len(rows) else pd.DataFrame(columns=COLUMNS)
    for column, default in DEFAULTS.items():
        if column not in frame.columns:
            frame[column] = default
        elif default == "":
            frame[column] = frame[column].fillna("")  # rows that did not set a text cell leave it empty
    frame = SCHEMA.validate(frame)
    order = COLUMNS + [b for b in BREAKDOWNS if b in frame.columns]
    return frame[order].sort_values(_keys(frame), ignore_index=True)


def round_half_up(value: float, decimals: int) -> float:
    """Half-up, away from zero, on the number as written (P14): 2.25 -> 2.3, -2.25 -> -2.3."""
    return float(Decimal(repr(value)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP))


def canonical_hash(frame: pd.DataFrame) -> str:
    """SHA-256 of the table as sorted CSV, every value in its shortest exact form. The same values give the same
    hash whatever the row order; -0.0 is written as 0.0 and a missing number as nothing."""
    ordered = frame.sort_values(_keys(frame), ignore_index=True)
    lines = [",".join(ordered.columns)]
    for row in ordered.itertuples(index=False):
        cells = ["" if isinstance(v, float) and np.isnan(v) else repr(abs(v) if v == 0 else v)
                 if isinstance(v, float) else str(v) for v in row]
        lines.append(",".join(cells))
    return "sha256:" + hashlib.sha256("\n".join(lines).encode()).hexdigest()
