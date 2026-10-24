"""UCDP's georeferenced events for the "Spreading instability" tab: GED (to the end of its year) followed by the
provisional Candidate Events (the months since), each event in the member state UCDP places it in (its country code
through athena-kit's crosswalk). Every figure here is UCDP's best estimate of deaths, summed by a stated rule (derived,
P4); nothing is re-estimated.

- `Months`: each member state's deaths by month.
- `Spread`: for a theatre, the first-level areas (ADM1, as UCDP names them) with a fatal event in the last twelve
  months against the twelve before, and the "new ground": an identified armed group's events in a state where it had
  none since the baseline year (a group UCDP has not identified, written XXX, cannot be followed).
- `Points`: the last twelve months' events, for the map: place, date, type, deaths and sides, never UCDP's quoted news.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from athena.component import Component

TYPES = {1: "state-based", 2: "non-state", 3: "one-sided"}
BASELINE = 2010  # "new ground": no event of that group in that state from this year until the window opens
GOVERNMENT = "Government of"
UNIDENTIFIED = "XXX"  # UCDP's name for a group it has not identified, followed by a country code


def month(dates: pd.Series) -> pd.Series:
    return dates.str.slice(0, 7)


def window(last: str, months: int = 12) -> tuple[str, str]:
    """The first and last month of the `months` ending at `last` (YYYY-MM)."""
    end = pd.Period(last, "M")
    return str(end - (months - 1)), str(end)


class Months(Component):
    """Each member state's deaths by month: the sum of UCDP's best estimates of its events starting that month."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        events: pd.DataFrame        # iso3, date_start (YYYY-MM-DD), best
        states: tuple               # the member states, in order
        first: str                  # the first month, YYYY-MM
        last: str                   # the last month, YYYY-MM

    @dataclass(frozen=True)
    class Output:
        months: list
        deaths: dict                # iso3 -> deaths per month (0 where UCDP records none)

    def run(self, inp: Input) -> Output:
        months = [str(p) for p in pd.period_range(inp.first, inp.last, freq="M")]
        e = inp.events.assign(month=month(inp.events["date_start"]))
        e = e[e["month"].between(inp.first, inp.last) & e["iso3"].isin(inp.states)]
        table = e.groupby(["iso3", "month"])["best"].sum().unstack(fill_value=0).reindex(
            index=list(inp.states), columns=months, fill_value=0)
        return self.Output(months, {k: [int(v) for v in row] for k, row in table.iterrows()})


class Spread(Component):
    """A theatre's spread over the last twelve months, by two stated rules."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        events: pd.DataFrame        # iso3, date_start, best, adm_1, side_a, side_b
        states: tuple               # the theatre's member states
        last: str                   # the window's last month

    @dataclass(frozen=True)
    class Output:
        areas_now: int              # ADM1 areas with a fatal event in the last twelve months
        areas_before: int           # the same in the twelve months before
        new_ground: list            # {"actor", "iso3", "first", "events", "deaths"}, the larger first

    def run(self, inp: Input) -> Output:
        e = inp.events[inp.events["iso3"].isin(inp.states)].assign(month=month(inp.events["date_start"]))
        a, b = window(inp.last)
        pa, pb = window(str(pd.Period(a, "M") - 1))
        fatal = e[(e["best"] > 0) & (e["adm_1"].fillna("") != "")]
        areas = lambda lo, hi: fatal[fatal["month"].between(lo, hi)][["iso3", "adm_1"]].drop_duplicates().shape[0]
        # the armed groups: either side that is not a government
        sides = pd.concat([e.assign(actor=e["side_a"]), e.assign(actor=e["side_b"])])
        sides = sides[~sides["actor"].fillna("").str.startswith(GOVERNMENT) & (sides["actor"].fillna("") != "")]
        sides = sides[(sides["actor"] != "Civilians") & ~sides["actor"].str.startswith(UNIDENTIFIED)]
        now = sides[sides["month"].between(a, b)]
        before = sides[(sides["date_start"].str.slice(0, 4).astype(int) >= BASELINE) & (sides["month"] < a)]
        seen = set(zip(before["actor"], before["iso3"]))
        new = []
        for (actor, iso3), g in now.groupby(["actor", "iso3"]):
            if (actor, iso3) not in seen:
                new.append({"actor": actor, "iso3": iso3, "first": g["date_start"].min(), "events": len(g),
                            "deaths": int(g["best"].sum())})
        new.sort(key=lambda r: (-r["deaths"], r["actor"]))
        return self.Output(areas(a, b), areas(pa, pb), new)


class Points(Component):
    """The window's events for the map, in member states: place, date, type, deaths and sides."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        events: pd.DataFrame        # iso3, date_start, longitude, latitude, type_of_violence, best, side_a, side_b,
                                    # adm_1, code_status, and the release it came from
        states: tuple
        last: str

    @dataclass(frozen=True)
    class Output:
        geojson: dict

    def run(self, inp: Input) -> Output:
        a, b = window(inp.last)
        e = inp.events[inp.events["iso3"].isin(inp.states) & month(inp.events["date_start"]).between(a, b)]
        features = [{"type": "Feature",
                     "geometry": {"type": "Point", "coordinates": [round(float(r.longitude), 3), round(float(r.latitude), 3)]},
                     "properties": {"date": r.date_start, "iso3": r.iso3, "type": TYPES.get(int(r.type_of_violence), ""),
                                    "best": int(r.best), "side_a": r.side_a, "side_b": r.side_b,
                                    "adm_1": r.adm_1 or None, "status": r.code_status, "release": r.release}}
                    for r in e.sort_values("best").itertuples()]
        return self.Output({"type": "FeatureCollection", "features": features})
