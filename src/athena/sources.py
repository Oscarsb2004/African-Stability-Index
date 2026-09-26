"""Source: getting data and keeping it exactly as published (decision P3).

A source is three separate things:
  - a `FormatReader`, reusable code for one kind of format or interface;
  - a `SourceCard`, the record of who publishes the data and on what terms;
  - a `Recipe`, one exact selection from one source, read by one reader.
Every retrieval produces a `Snapshot`: the bytes, named by their hash, kept forever.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import ClassVar, Protocol

from pydantic import BaseModel, model_validator

from athena.base import Definition, Record
from athena.ids import ContentHash, Id, Version, hash_bytes
from athena.vocab import Access, Redistribution

Scalar = str | int | float | bool


class Terms(Record):
    url: str
    read_on: date | None = None
    summary: str
    redistribution: Redistribution = Redistribution.UNKNOWN

    @model_validator(mode="after")
    def _read_before_judged(self) -> Terms:
        if self.read_on is None and self.redistribution is not Redistribution.UNKNOWN:
            raise ValueError("redistribution can only be judged once the terms have been read (read_on)")
        return self


class SourceCard(Definition):
    KIND: ClassVar[str] = "source"

    publisher: str
    access: Access
    terms: Terms
    readers: tuple[Id, ...] = ()
    notes: str = ""

    @property
    def usable(self) -> bool:
        """std:DATA-04: no data is used until the terms have been read and dated."""
        return self.terms.read_on is not None

    @property
    def publishable(self) -> bool:
        return self.usable and self.terms.redistribution in (Redistribution.ALLOWED, Redistribution.ATTRIBUTION)


class Recipe(Definition):
    """One exact retrieval, written down so it can be repeated or pointed at a different source."""

    KIND: ClassVar[str] = "recipe"

    source: Id
    reader: Id
    parameters: dict[str, Scalar | tuple[Scalar, ...]]


class Snapshot(Record):
    """Bytes as published. The hash is the name; a snapshot is never edited."""

    hash: ContentHash
    source: Id
    recipe: str
    retrieved_at: datetime
    url: str
    media_type: str
    size_bytes: int

    @classmethod
    def of(cls, data: bytes, *, source: SourceCard, recipe: Recipe, url: str, media_type: str,
           retrieved_at: datetime) -> Snapshot:
        return cls(hash=hash_bytes(data), source=source.id, recipe=recipe.ref, retrieved_at=retrieved_at,
                   url=url, media_type=media_type, size_bytes=len(data))


class Transport(Protocol):
    """The only way a reader reaches the network. Tests pass a transport that serves fixtures."""

    def get(self, url: str) -> tuple[bytes, str]: ...


class FormatReader(ABC):
    """Reusable code for one format or interface, such as an SDMX API or a spreadsheet download.

    `fetch` is the only method allowed to touch the network, and only through the transport it is given.
    `parse` is pure: the same snapshot bytes always give the same frame.
    """

    ID: ClassVar[str]
    VERSION: ClassVar[Version]
    Parameters: ClassVar[type[BaseModel]]

    def check(self, recipe: Recipe) -> BaseModel:
        if recipe.reader != self.ID:
            raise ValueError(f"recipe {recipe.id} names reader {recipe.reader}, not {self.ID}")
        return self.Parameters.model_validate(recipe.parameters)

    @abstractmethod
    def fetch(self, recipe: Recipe, transport: Transport) -> tuple[bytes, str, str]:
        """Return (bytes, url, media type) for the recipe's selection."""

    @abstractmethod
    def parse(self, data: bytes, recipe: Recipe):
        """Turn snapshot bytes into a frame."""
