"""python -m adapters discover | mdg | worldbank

discover   finds the Internet Archive capture of every MDG series page and metadata page after the database's
           final update, and writes adapters/mdg_captures.csv. Run once, then commit the file.
mdg        ingests the MDG groupings, database and annex into datasets in the store, and prints the report.
worldbank  ingests every World Bank bulk download in sources.toml (WDI, WGI) into a dataset named after its edition.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from adapters import fetcher, mdg_annex, mdg_database, mdg_groupings, sources, worldbank
from athena import dataset
from athena.fetch import cached_session


def mdg(session=None, root: Path = dataset.ROOT, captures: Path = mdg_database.CAPTURES,
        lock: Path | None = None) -> list[str]:
    """All three MDG datasets. Nothing is written unless every name maps to a code."""
    listed, get = sources(), (fetcher(session, lock) if lock else fetcher(session)).get
    code, m49_names = mdg_groupings.coder(get, listed)
    areas, membership, groupings_report = mdg_groupings.ingest(get, listed, code, m49_names)
    values, codebook, database_report = mdg_database.ingest(
        get, code, pd.read_csv(captures, dtype=str, keep_default_na=False))
    annex_values, annex_book, annex_report = mdg_annex.ingest(get(listed["annex-2015"]["url"]))
    dataset.write(mdg_groupings.NAME, {"areas": areas, "membership": membership}, groupings_report, root)
    dataset.write(mdg_database.NAME, {"values": values, "codebook": codebook}, database_report, root)
    dataset.write(mdg_annex.NAME, {"values": annex_values, "codebook": annex_book}, annex_report, root)
    return groupings_report + database_report + annex_report


def world_bank(session=None, root: Path = dataset.ROOT, lock: Path | None = None) -> list[str]:
    """One dataset per bulk download, written as each is read."""
    get, report = (fetcher(session, lock) if lock else fetcher(session)).get, []
    for source in sources().values():
        if source.get("kind") == "worldbank-bulk":
            name, tables, lines = worldbank.ingest(get(source["url"]), source["database"])
            dataset.write(name, tables, lines, root)
            report += lines
    return report


def main(argv: list[str]) -> int:
    if argv[:1] == ["discover"]:
        found = mdg_database.discover(cached_session())
        print(f"{len(found)} series pages, {(found['metadata_capture'] != '').sum()} with a metadata page, "
              f"written to {mdg_database.CAPTURES.name}")
        return 0
    if argv[:1] == ["mdg"]:
        print("\n".join(mdg()))
        return 0
    if argv[:1] == ["worldbank"]:
        print("\n".join(world_bank()))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
