"""Adapters: one per database (P37). Each reads one publisher's format and writes a dataset in the common format.
Nothing downstream of an adapter knows that format.

`sources.toml` lists every source with its terms; `sources.lock` holds the hash of every address fetched.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from athena.fetch import Fetcher

HERE = Path(__file__).parent
LOCK = HERE / "sources.lock"


def sources() -> dict:
    with (HERE / "sources.toml").open("rb") as f:
        return tomllib.load(f)


def fetcher(session=None, lock: Path = LOCK) -> Fetcher:
    return Fetcher(lock, session)
