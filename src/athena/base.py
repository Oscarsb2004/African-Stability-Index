"""The two base classes every piece of data in Athena derives from.

A `Record` is an immutable, validated value: unknown fields are refused (std:MOD-03) and nothing changes after
construction. A `Definition` is a record with an identity and a version - something that is written once,
referred to by id, and changed only by publishing a new version.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, model_validator

from athena.ids import Id, Version, canonical_json, hash_bytes, kind_of


class Record(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True, validate_default=True)

    def fingerprint(self) -> str:
        """A content hash of this value. Two records with the same fingerprint are the same record."""
        return hash_bytes(canonical_json(self.model_dump(mode="json")))


class Definition(Record):
    """Something referred to by id: a source, a method, a step, an indicator, an index."""

    KIND: ClassVar[str]

    id: Id
    title: str
    version: Version = "0.1.0"

    @model_validator(mode="after")
    def _id_matches_kind(self) -> Definition:
        if kind_of(self.id) != self.KIND:
            raise ValueError(f"{type(self).__name__} ids start with {self.KIND}:, got {self.id!r}")
        return self

    @property
    def ref(self) -> str:
        """The exact thing a run used: `id@version`."""
        return f"{self.id}@{self.version}"
