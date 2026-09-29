"""The answer key: what the publishers printed. Sealed: only `mdg.check` imports this module, and a test fails if
any other module does, so the build cannot see a published value."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from mdg import readers

ANNEX_LABELS = {
    "World": "world", "Developing regions": "developing", "Developed regions": "developed",
    "Northern Africa": "northern-africa", "Sub-Saharan Africa": "sub-saharan-africa",
    "Latin America and the Caribbean": "latin-america-and-the-caribbean", "Caribbean": "caribbean",
    "Latin America": "latin-america", "Eastern Asia": "eastern-asia",
    "Eastern Asia excluding China": "eastern-asia-excluding-china", "Southern Asia": "southern-asia",
    "Southern Asia excluding India": "southern-asia-excluding-india", "South-Eastern Asia": "south-eastern-asia",
    "Western Asia": "western-asia", "Oceania": "oceania", "Caucasus and Central Asia": "caucasus-and-central-asia",
    "Least developed countries": "least-developed", "Landlocked developing countries": "landlocked-developing",
    "Small island developing States": "small-island-developing",
}


class UnknownLabel(ValueError):
    pass


def regional(rows: list[tuple[str, str, int, float | None]], part: str, year: int) -> pd.Series:
    """One year of one part of an annex table, by group. A dash is no value, so it is left out."""
    published = {}
    for p, label, y, value in rows:
        if label not in ANNEX_LABELS:
            raise UnknownLabel(f"annex row {label!r} has no group")
        if p == part and y == year and value is not None:
            published[ANNEX_LABELS[label]] = value
    return pd.Series(published, dtype=float)


def ipu_countries(data: bytes, code: Callable[[str], str | None]) -> pd.Series:
    """The share of seats held by women that the IPU prints for each country, by code."""
    printed = {code(name): float(share) for name, _, _, share in readers.ipu_classification(data)
               if share not in ("?", "---", "")}
    return pd.Series(printed, dtype=float)


def ipu_world_totals(data: bytes) -> pd.Series:
    """The world's seats (where gender is known) and women, as the IPU prints them."""
    world = readers.ipu_world(data)
    return pd.Series({"seats": float(world["known"]), "women": float(world["women"])})


def series(data: bytes, code: Callable[[str], str | None], year: int) -> pd.Series:
    """The MDG database's final country values for one year, by code."""
    return pd.Series({code(name): value for name, y, value, _ in readers.mdg_series(data) if y == year}, dtype=float)
