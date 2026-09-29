"""Datasets in the store (P40): a folder of CSV tables and the report of the ingest that wrote them.

A values table is always in the common format; other tables (a codebook, a membership list) are plain CSV.
Values are written in full precision, so reading a dataset back gives exactly what was written.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from athena.fetch import STORE
from athena.table import NUMBERS, table

ROOT = STORE / "datasets"


def write(name: str, tables: dict[str, pd.DataFrame], report: list[str], root: Path = ROOT) -> Path:
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    for file, frame in tables.items():
        frame.to_csv(folder / f"{file}.csv", index=False, lineterminator="\n")
    (folder / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    return folder


def load(name: str, file: str = "values", root: Path = ROOT) -> pd.DataFrame:
    """A table as written. A values table comes back validated, with numbers as floats."""
    frame = pd.read_csv(root / name / f"{file}.csv", dtype=str, keep_default_na=False)
    if file != "values":
        return frame
    for column in NUMBERS:
        frame[column] = pd.to_numeric(frame[column].replace("", np.nan))
    frame["DERIVED"] = frame["DERIVED"] == "True"
    return table(frame)
