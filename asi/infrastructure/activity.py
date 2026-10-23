"""The activity behind a point: each complete calendar year's sum of a publisher's daily figures (derived, P4).

PortWatch publishes daily port calls, trade estimates and chokepoint transits. A year is summed for a point only when
the table holds a row for every day of that year at that point, so a year cut short by the file's end, or with days
missing, is left out rather than read as a quiet year. Summing is the only operation: no estimate is adjusted.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass

import pandas as pd

from athena.component import Component

RULE = ("derived: the sum of the publisher's daily figures over each complete calendar year (UTC), counted only where "
        "every day of the year is in the file")


def number(v) -> int | float:
    """A sum as an integer where it is whole (calls, tons), otherwise as it is."""
    return int(v) if float(v).is_integer() else float(v)


class YearlySums(Component):
    """Each id's sums over its complete calendar years, for the named columns."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        daily: pd.DataFrame         # one row per id and day: `date` (YYYY-MM-DD), the id column, the value columns
        id_field: str
        columns: tuple[str, ...]

    @dataclass(frozen=True)
    class Output:
        sums: dict                  # id -> {"years": [...], column: [...]}; an id with no complete year is absent
        last_day: str

    def run(self, inp: Input) -> Output:
        d = inp.daily
        twice = d.duplicated([inp.id_field, "date"])
        if twice.any():
            raise ValueError(f"days listed twice for one id: {d.loc[twice, [inp.id_field, 'date']].head(3).values.tolist()}")
        year = d["date"].str.slice(0, 4).astype(int).rename("year")
        groups = d.groupby([d[inp.id_field], year])
        days = groups.size()
        whole = days[[n == (366 if calendar.isleap(y) else 365) for (_, y), n in days.items()]].index
        sums = groups[list(inp.columns)].sum().loc[whole]
        out: dict[str, dict] = {}
        for key, rows in sums.groupby(level=0):
            rows = rows.droplevel(0).sort_index()
            out[key] = {"years": [int(y) for y in rows.index]} | {c: [number(v) for v in rows[c]] for c in inp.columns}
        return self.Output(out, str(d["date"].max()))
