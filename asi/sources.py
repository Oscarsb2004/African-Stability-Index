"""The ASI's sources and their lock, in the project's own folder (athena-kit's `athena.ingest.Project`).

`sources.toml` lists every source the ASI reads, each with its terms as read and dated; `sources.lock` holds the
SHA-256 of every address fetched, so a source whose bytes change is refused. Every stage fetches through `fetcher()`.
"""

from pathlib import Path

from athena.ingest import Project

ROOT = Path(__file__).resolve().parents[1]
PROJECT = Project(ROOT)


def sources() -> dict:
    """Every source, by key, as `sources.toml` lists it."""
    return PROJECT.sources


def fetcher(session=None):
    """A fetcher held to the ASI's own lock."""
    return PROJECT.fetcher(session)
