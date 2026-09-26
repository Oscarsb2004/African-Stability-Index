"""Groupings: region lists, income groups and other classifications (decision P19).

A grouping is two things, the way SDMX keeps code lists apart from data:
  - a `Grouping` definition - small, named and versioned: who publishes it, the period it is valid for, its levels,
    whether a member may sit in more than one group, and the hash of its membership;
  - a membership frame (profile `membership`) - one row per member and group, stored and hashed like any other data,
    so it scales to thousands of places and is checked against the publisher's own list with the same machinery.

Steps receive the membership frame as an input, so every run records exactly which list it used.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import ClassVar

import pyarrow as pa
from pydantic import model_validator

from athena.base import Definition
from athena.citations import Citation
from athena.frames import Column, Frame, Manifest
from athena.ids import ContentHash
from athena.vocab import Concept, DType, Profile, ReproClass, Role

MEMBER, GROUP, LEVEL = "member", "group", "level"


def membership_frame(rows: list[tuple[str, str, str]], *, produced_by: str,
                     repro_class: ReproClass = ReproClass.A) -> Frame:
    """Rows of (member, group, level). A group may itself be a member of a group at a higher level."""
    manifest = Manifest(
        profile=Profile.MEMBERSHIP,
        columns=(
            Column(name=MEMBER, dtype=DType.STRING, role=Role.ENTITY, concept=Concept.REF_AREA),
            Column(name=GROUP, dtype=DType.STRING, role=Role.CATEGORY),
            Column(name=LEVEL, dtype=DType.STRING, role=Role.CATEGORY),
        ),
        keys=(MEMBER, GROUP, LEVEL),
        produced_by=produced_by,
        repro_class=repro_class,
    )
    table = pa.table({name: pa.array([r[i] for r in rows], pa.string()) for i, name in enumerate((MEMBER, GROUP, LEVEL))})
    return Frame(table, manifest)


class Grouping(Definition):
    KIND: ClassVar[str] = "grouping"

    publisher: str
    levels: tuple[str, ...]
    disjoint: bool
    members: ContentHash
    valid_from: date | None = None
    valid_to: date | None = None
    citation: Citation | None = None

    @model_validator(mode="after")
    def _well_formed(self) -> Grouping:
        if not self.levels or len(self.levels) != len(set(self.levels)):
            raise ValueError("a grouping names its levels, each once")
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            raise ValueError("a grouping cannot stop being valid before it starts")
        return self

    def bind(self, frame: Frame) -> BoundGrouping:
        """Pair the definition with its membership, refusing a frame that is not the one the definition names."""
        if frame.manifest.profile is not Profile.MEMBERSHIP:
            raise ValueError(f"{self.id} needs a membership frame, got {frame.manifest.profile}")
        if frame.content_hash() != self.members:
            raise ValueError(f"{self.ref} names membership {self.members}, not {frame.content_hash()}")
        return BoundGrouping(self, frame)


class BoundGrouping:
    """A grouping with its membership loaded and checked against the definition's promises."""

    __slots__ = ("definition", "_groups")

    def __init__(self, definition: Grouping, frame: Frame):
        groups: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        for row in frame.table.to_pylist():
            if row[LEVEL] not in definition.levels:
                raise ValueError(f"{definition.id}: level {row[LEVEL]!r} is not one of {definition.levels}")
            groups[row[LEVEL]][row[GROUP]].append(row[MEMBER])
        if definition.disjoint:
            for level, by_group in groups.items():
                seen: dict[str, str] = {}
                for group, members in by_group.items():
                    for member in members:
                        if member in seen:
                            raise ValueError(f"{definition.id}: {member} is in both {seen[member]!r} and {group!r} "
                                             f"at level {level!r}, but the grouping is disjoint")
                        seen[member] = group
        self.definition = definition
        self._groups = {level: {g: tuple(sorted(m)) for g, m in by.items()} for level, by in groups.items()}

    def groups(self, level: str) -> dict[str, tuple[str, ...]]:
        if level not in self.definition.levels:
            raise KeyError(f"{self.definition.id} has no level {level!r}")
        return dict(self._groups.get(level, {}))

    def group_of(self, member: str, level: str) -> tuple[str, ...]:
        return tuple(g for g, members in self.groups(level).items() if member in members)
