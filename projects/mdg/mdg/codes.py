"""Country names to codes: exact M49 matches first, then the declared alias table, and nothing else.

There is no fuzzy matching. A name that matches neither stops the run, because a country quietly dropped or put in
the wrong region is exactly the kind of fault this project exists to catch.
"""

from __future__ import annotations

import tomllib
from collections.abc import Iterable
from pathlib import Path

ALIASES_FILE = Path(__file__).with_name("aliases.toml")


class UnmappedNames(ValueError):
    pass


def load_aliases(path: Path = ALIASES_FILE) -> dict[str, str]:
    with path.open("rb") as f:
        return dict(tomllib.load(f)["aliases"])


def code_map(names: Iterable[str], m49: dict[str, str], aliases: dict[str, str]) -> dict[str, str]:
    shadowing = sorted(a for a in aliases if a in m49)
    if shadowing:
        raise UnmappedNames(f"aliases for names M49 already matches: {shadowing}")
    mapping, missing = {}, []
    for name in sorted(set(names)):
        code = m49.get(name) or aliases.get(name)
        if code is None:
            missing.append(name)
        else:
            mapping[name] = code
    if missing:
        raise UnmappedNames(f"{len(missing)} names match neither M49 nor an alias: {missing}")
    return mapping
