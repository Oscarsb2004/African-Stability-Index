"""Frames: the one output format every stage emits (decision ST7).

A frame is a table plus a manifest. Every column declares its role, so a view or a test can work on a frame it
has never seen. The manifest also carries the frame's validation level and reproducibility class (P5), so those
travel with the numbers instead of living in a separate report.
"""

from __future__ import annotations

import pyarrow as pa
import pyarrow.compute as pc
from pydantic import model_validator

from athena.base import Record
from athena.ids import ContentHash, hash_bytes
from athena.vocab import DType, Origin, Profile, ReproClass, Role, ValidationLevel

ARROW_TYPES: dict[DType, pa.DataType] = {
    DType.STRING: pa.string(),
    DType.INT64: pa.int64(),
    DType.FLOAT64: pa.float64(),
    DType.BOOL: pa.bool_(),
    DType.DATE: pa.date32(),
}


class Column(Record):
    name: str
    dtype: DType
    role: Role
    unit: str | None = None
    description: str = ""

    @model_validator(mode="after")
    def _measures_have_units(self) -> Column:
        if self.role is Role.MEASURE and not self.unit:
            raise ValueError(f"measure column {self.name!r} must declare a unit")
        return self


class Manifest(Record):
    profile: Profile
    columns: tuple[Column, ...]
    keys: tuple[str, ...]
    produced_by: str
    inputs: tuple[ContentHash, ...] = ()
    origin: Origin = Origin.PUBLISHED
    validation_level: ValidationLevel = ValidationLevel.UNVERIFIED
    repro_class: ReproClass
    period: str | None = None

    @model_validator(mode="after")
    def _consistent(self) -> Manifest:
        names = [c.name for c in self.columns]
        if len(names) != len(set(names)):
            raise ValueError("column names must be unique")
        missing = self.profile.required_roles - {c.role for c in self.columns}
        if missing:
            raise ValueError(f"profile {self.profile} needs roles {sorted(missing)}")
        unknown = set(self.keys) - set(names)
        if unknown or not self.keys:
            raise ValueError(f"keys must be a non-empty subset of the columns; unknown: {sorted(unknown)}")
        if self.profile is Profile.CROSS_SECTION and not self.period:
            raise ValueError("a cross-section declares the period it holds")
        if self.origin is Origin.OWN and self.validation_level is ValidationLevel.PUBLISHER_MATCH:
            raise ValueError("an own-method output has no publisher to match; it cannot be validation level 1")
        return self

    @property
    def derived(self) -> bool:
        """P4: everything an own method produces is labelled derived."""
        return self.origin is Origin.OWN

    def columns_with(self, role: Role) -> tuple[Column, ...]:
        return tuple(c for c in self.columns if c.role is role)


class Frame:
    """A table and its manifest, checked against each other when the frame is made."""

    __slots__ = ("table", "manifest")

    def __init__(self, table: pa.Table, manifest: Manifest):
        expected = pa.schema([pa.field(c.name, ARROW_TYPES[c.dtype]) for c in manifest.columns])
        if not table.schema.remove_metadata().equals(expected):
            raise ValueError(f"table schema {table.schema} does not match the manifest {expected}")
        keys = table.select(list(manifest.keys))
        if keys.num_rows and keys.group_by(list(manifest.keys)).aggregate([]).num_rows != keys.num_rows:
            raise ValueError(f"duplicate keys {manifest.keys}; one row per key")
        for name in manifest.keys:
            if table.column(name).null_count:
                raise ValueError(f"key column {name!r} has missing values")
        self.table = table.combine_chunks()
        self.manifest = manifest

    @property
    def num_rows(self) -> int:
        return self.table.num_rows

    def content_hash(self) -> ContentHash:
        """A hash of the numbers and the manifest together; the same frame always gives the same hash."""
        sink = pa.BufferOutputStream()
        with pa.ipc.new_stream(sink, self.table.schema) as writer:
            writer.write_table(self.table)
        return hash_bytes(sink.getvalue().to_pybytes() + self.manifest.fingerprint().encode())

    def column(self, name: str) -> pa.ChunkedArray:
        return self.table.column(name)

    def sorted_by_keys(self) -> Frame:
        order = pc.sort_indices(self.table, [(k, "ascending") for k in self.manifest.keys])
        return Frame(self.table.take(order), self.manifest)
