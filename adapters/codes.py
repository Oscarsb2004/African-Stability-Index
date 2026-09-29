"""Country names to codes: an exact M49 match, then the declared alias table, and nothing else.

There is no fuzzy matching. Every name that no table matches is reported together, and the run stops, because a
country quietly dropped or put under the wrong code is exactly the fault this project exists to catch.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

ALIASES = Path(__file__).with_name("aliases.toml")


class UnmappedNames(ValueError):
    pass


def load_aliases(path: Path = ALIASES) -> dict[str, str]:
    with path.open("rb") as f:
        return dict(tomllib.load(f)["aliases"])


class Coder:
    def __init__(self, m49: dict[str, str], aliases: dict[str, str]):
        shadowing = sorted(a for a in aliases if a in m49)
        if shadowing:
            raise UnmappedNames(f"aliases for names M49 already matches: {shadowing}")
        self.codes, self.missing = m49 | aliases, set()

    def __call__(self, name: str) -> str | None:
        code = self.codes.get(name)
        if code is None:
            self.missing.add(name)
        return code

    def done(self) -> None:
        if self.missing:
            raise UnmappedNames(f"{len(self.missing)} names match neither M49 nor an alias: {sorted(self.missing)}")
