"""Reference definitions: code lists and groupings that many steps rely on.

A grouping, such as the MDG developing regions, is a definition rather than data: it has an id and a version, and
a publisher can revise it. Region membership is also something publishers release, so a grouping can be checked
against the publisher's own list like any other value.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import model_validator

from athena.base import Definition
from athena.method import Citation


class Grouping(Definition):
    KIND: ClassVar[str] = "grouping"

    publisher: str
    groups: dict[str, tuple[str, ...]]
    disjoint: bool
    citation: Citation | None = None

    @model_validator(mode="after")
    def _members_well_formed(self) -> Grouping:
        for name, members in self.groups.items():
            if not members:
                raise ValueError(f"group {name!r} is empty")
            if len(members) != len(set(members)):
                raise ValueError(f"group {name!r} lists a member twice")
        if self.disjoint:
            seen: dict[str, str] = {}
            for name, members in self.groups.items():
                for member in members:
                    if member in seen:
                        raise ValueError(f"{member} is in both {seen[member]!r} and {name!r}, but the grouping is disjoint")
                    seen[member] = name
        return self

    def group_of(self, member: str) -> tuple[str, ...]:
        return tuple(name for name, members in self.groups.items() if member in members)
