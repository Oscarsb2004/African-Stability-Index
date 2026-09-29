"""The M1 build: every catalogue row from its sources to the common format. It never reads a published value.

This is the first replication project (MDG 3.3 and 3.1). Milestone S1 replaces it with a short project script over
the ingested datasets.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from adapters import LOCK, readers, sources
from adapters.codes import Coder, UnmappedNames, load_aliases  # noqa: F401  (UnmappedNames is re-exported)
from athena import aggregate
from athena.fetch import Fetcher
from athena.table import table

HERE = Path(__file__).parent
DATASET = "mdg-m1"


def load(name: str, folder: Path = HERE) -> dict:
    with (folder / name).open("rb") as f:
        return tomllib.load(f)


class MixedEditions(ValueError):
    pass


@dataclass
class Project:
    fetcher: Fetcher
    sources: dict = field(default_factory=sources)
    catalogue: dict = field(default_factory=lambda: load("catalogue.toml"))

    def get(self, key: str, **fields: str) -> bytes:
        return self.fetcher.get(self.sources[key]["url"].format(**fields))


def open_project(lock: Path = LOCK, session=None) -> Project:
    return Project(Fetcher(lock, session))


def membership(project: Project, code: Coder) -> pd.DataFrame:
    """(member, group): the official groupings, with each replacement list swapped in whole for its group."""
    spec = project.catalogue["groups"]
    pairs = readers.groupings(project.get(spec["document"]))
    for key in spec["replace"]:
        source = project.sources[key]
        read = {"ldc-pdf": readers.ldc_names, "lldc-html": readers.lldc_names}[source["kind"]]
        pairs = {p for p in pairs if p[1] != source["group"]} | {(n, source["group"]) for n in read(project.get(key))}
    coded = sorted({(c, group) for name, group in pairs if (c := code(name))})
    return pd.DataFrame(coded, columns=["member", "group"])


def variables(project: Project, row: dict, year: int, code: Coder) -> pd.DataFrame:
    """One column per input variable, one row per country code, for one year."""
    editions = {project.sources[ref.split("/")[0]].get("edition") for ref in row["inputs"].values()}
    if len(editions) != 1:
        raise MixedEditions(f"{row['id']}: inputs come from editions {sorted(map(str, editions))} (P25)")
    columns = {}
    for name, ref in row["inputs"].items():
        key, series = ref.split("/", 1)
        source = project.sources[key]
        if source["kind"] == "ipu-classification":
            at = {"seats": 1, "women": 2}[series]
            found = [(c, r[at]) for r in readers.ipu_classification(project.get(key))
                     if source["year"] == year and (c := code(r[0]))]
        elif source["kind"] == "wdi-archive":
            # In the WDI archive's editions of 2015 the values sit under current ISO codes, not the old World
            # Bank ones (ZAR, ROM, TMP), so they join M49's codes directly. Aggregates such as WLD are dropped.
            years = ";".join(f"YR{y}" for y in row["years"])
            countries = set(code.codes.values())
            found = [(c, v) for c, y, v in readers.wdi_archive(project.get(key, series=series, years=years))
                     if y == year and c in countries]
        else:
            raise ValueError(f"{key}: no reader for kind {source['kind']!r}")
        values = pd.Series(dict(found), dtype=float)
        if len(values) != len(found):
            raise ValueError(f"{row['id']} {name}: a country appears twice")
        columns[name] = values
    return pd.DataFrame(columns)


@dataclass
class Built:
    outputs: pd.DataFrame
    members: pd.DataFrame
    sums: dict[tuple[str, int], pd.DataFrame]
    coder: Coder


def build(project: Project) -> Built:
    code = Coder(readers.m49_codes(project.get("m49")), load_aliases())
    members = membership(project, code)
    rows, sums = [], {}
    for row in project.catalogue["indicator"]:
        edition = project.sources[next(iter(row["inputs"].values())).split("/")[0]]["edition"]
        for year in row["years"]:
            known = aggregate.complete(variables(project, row, year, code), row.get("derive", {}), row["value"])
            groups = aggregate.by_group(known, members, row["value"])
            sums[(row["id"], year)] = groups
            values = pd.concat([known["value"], groups["value"]])
            for area, value in values[np.isfinite(values)].items():
                rows.append({"DATASET": DATASET, "SERIES": row["id"], "REF_AREA": area, "TIME_PERIOD": str(year),
                             "OBS_VALUE": value, "UNIT_MEASURE": row["unit"], "EDITION": edition, "DERIVED": True})
    code.done()
    return Built(table(rows), members, sums, code)
