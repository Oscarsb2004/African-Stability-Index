"""Internet Archive captures, found through its CDX index.

A discovery runs once and its result is committed, so every later ingest reads exactly the same captures.
"""

from __future__ import annotations

from collections.abc import Callable

CDX = ("https://web.archive.org/cdx/search/cdx?url={prefix}&matchType=prefix&from={since}&to={until}"
       "&filter=statuscode:200&fl=timestamp,original&limit=200000")
RAW = "https://web.archive.org/web/{stamp}id_/{url}"


def earliest(listing: str, key: Callable[[str], str | None]) -> dict[str, tuple[str, str]]:
    """From CDX lines of "timestamp address", the earliest capture for each key. An address that gives no key is
    ignored."""
    found: dict[str, tuple[str, str]] = {}
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        stamp, url = parts
        k = key(url)
        if k is not None and (k not in found or stamp < found[k][0]):
            found[k] = (stamp, url)
    return found
