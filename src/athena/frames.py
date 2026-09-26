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
from athena.ids import ContentHash, canonical_json, hash_bytes
from athena.vocab import Concept, DType, Origin, Profile, ReproClass, Role, ValidationLevel

HASH_SCHEME = "athena-frame/1"

CONCEPT_ROLES: dict[Concept, Role] = {
    Concept.REF_AREA: Role.ENTITY,
    Concept.TIME_PERIOD: Role.TIME,
    Concept.OBS_VALUE: Role.MEASURE,
    Concept.OBS_STATUS: Role.STATUS,
    Concept.UNIT_MEASURE: Role.CATEGORY,
    Concept.UNIT_MULT: Role.CATEGORY,
    Concept.FREQ: Role.CATEGORY,
    Concept.SERIES: Role.ENTITY,
}

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
    concept: Concept | None = None
    description: str = ""

    @model_validator(mode="after")
    def _measures_have_units(self) -> Column:
        if self.role is Role.MEASURE and not self.unit:
            raise ValueError(f"measure column {self.name!r} must declare a unit")
        if self.concept is not None and CONCEPT_ROLES[self.concept] is not self.role:
            raise ValueError(f"column {self.name!r} is {self.concept}, which is a {CONCEPT_ROLES[self.concept]}, "
                             f"not a {self.role}")
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
        """A hash of the values and the manifest, in a byte form Athena defines itself (decision 2).

        Rows are ordered by their keys and every value is written in canonical JSON, so the hash does not
        depend on row order, on how the table is chunked in memory, or on the version of any library.
        Floats are written in their shortest round-trip form, and -0.0 is written as 0.0.
        """
        return hash_bytes(canonical_json({
            "scheme": HASH_SCHEME,
            "manifest": self.manifest.model_dump(mode="json"),
            "rows": [[_canonical(v) for v in row.values()] for row in self.sorted_by_keys().table.to_pylist()],
        }))

    def column(self, name: str) -> pa.ChunkedArray:
        return self.table.column(name)

    def sorted_by_keys(self) -> Frame:
        order = pc.sort_indices(self.table, [(k, "ascending") for k in self.manifest.keys])
        return Frame(self.table.take(order), self.manifest)


def _canonical(value):
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("frames hold no NaN or infinite values; missing is null")
        return 0.0 if value == 0 else value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
