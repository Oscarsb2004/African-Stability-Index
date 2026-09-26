"""Identity: every definition has an id, and every stored byte has a content hash.

An id is `kind:slug`, is never reused, and is retired by status rather than deleted (decision A15). A content
hash names bytes exactly, so two runs that read the same hash read the same data.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Annotated, Any

from pydantic import StringConstraints

ID_PATTERN = r"^[a-z][a-z0-9-]*:[A-Za-z0-9][A-Za-z0-9._-]*$"
HASH_PATTERN = r"^sha256:[0-9a-f]{64}$"
VERSION_PATTERN = r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"

Id = Annotated[str, StringConstraints(pattern=ID_PATTERN)]
ContentHash = Annotated[str, StringConstraints(pattern=HASH_PATTERN)]
Version = Annotated[str, StringConstraints(pattern=VERSION_PATTERN)]


def kind_of(identifier: str) -> str:
    """The part of an id before the colon: `source` in `source:un-mdg-database`."""
    if not re.match(ID_PATTERN, identifier):
        raise ValueError(f"not an id: {identifier!r}")
    return identifier.split(":", 1)[0]


def hash_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    """One byte form per value: sorted keys, no whitespace, UTF-8. Fingerprints are taken over this."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
