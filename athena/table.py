"""The common format (P31): one long table with SDMX column names, checked by pandera.

Every output has this shape, so any template can show any dataset. Values stay in full precision here; rounding
happens once, at the output (P33).
"""

from __future__ import annotations

import hashlib
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd
import pandera.pandas as pa

COLUMNS = ["INDICATOR", "REF_AREA", "TIME_PERIOD", "OBS_VALUE", "UNIT_MEASURE", "OBS_STATUS", "SOURCE", "EDITION",
           "DERIVED"]
KEYS = ["INDICATOR", "REF_AREA", "TIME_PERIOD"]

SCHEMA = pa.DataFrameSchema(
    {"INDICATOR": pa.Column(str), "REF_AREA": pa.Column(str), "TIME_PERIOD": pa.Column(int),
     "OBS_VALUE": pa.Column(float, pa.Check(lambda s: np.isfinite(s).all(), error="finite values only")),
     "UNIT_MEASURE": pa.Column(str), "OBS_STATUS": pa.Column(str), "SOURCE": pa.Column(str),
     "EDITION": pa.Column(str), "DERIVED": pa.Column(bool)},
    unique=KEYS, strict=True, coerce=True,
)


def table(rows: list[dict]) -> pd.DataFrame:
    """Rows to a validated common-format table, sorted by its keys. An unknown column is refused, not dropped."""
    frame = pd.DataFrame(rows) if rows else pd.DataFrame(columns=COLUMNS)
    return SCHEMA.validate(frame)[COLUMNS].sort_values(KEYS, ignore_index=True)


def round_half_up(value: float, decimals: int) -> float:
    """Half-up, away from zero, on the number as written (P14): 2.25 -> 2.3, -2.25 -> -2.3."""
    return float(Decimal(repr(value)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP))


def canonical_hash(frame: pd.DataFrame) -> str:
    """SHA-256 of the table as sorted CSV, with every value written in its shortest exact form. The same values give
    the same hash whatever the row order; -0.0 is written as 0.0."""
    ordered = frame.sort_values(KEYS, ignore_index=True)
    lines = [",".join(COLUMNS)]
    for row in ordered.itertuples(index=False):
        cells = [repr(abs(v) if v == 0 else v) if isinstance(v, float) else str(v) for v in row]
        lines.append(",".join(cells))
    return "sha256:" + hashlib.sha256("\n".join(lines).encode()).hexdigest()
