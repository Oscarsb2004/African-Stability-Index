"""Validation: checking our numbers against the publisher's, beside every stage (decision P2).

The answer key is the publisher's own published values. It is sealed: pipeline code never reads it; it can only
be compared against. Tolerances come from the precision the publisher rounds to and are fixed before any
comparison. A checkpoint compares at every point where the publisher releases a value, so the first checkpoint
to fail names the steps at fault. Every difference is recorded, classified and kept - never adjusted away.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

import pyarrow as pa
import pyarrow.compute as pc
from pydantic import Field, model_validator

from athena.base import Record
from athena.frames import Frame
from athena.rounding import Rounding
from athena.vocab import CauseClass, DivergenceStatus

EPSILON = 1e-12


class Tolerance(Record):
    absolute: float = Field(ge=0)
    basis: str
    fixed_on: date

    @classmethod
    def from_decimals(cls, decimals: int, *, fixed_on: date) -> Tolerance:
        """A value published to n decimals cannot be held tighter than half a unit in the last place."""
        return cls(absolute=0.5 * 10.0 ** -decimals, basis=f"published to {decimals} decimal place(s)",
                   fixed_on=fixed_on)

    @classmethod
    def from_rounding(cls, rounding: Rounding, *, fixed_on: date) -> Tolerance:
        return cls.from_decimals(rounding.decimals, fixed_on=fixed_on)

    def admits(self, difference: float) -> bool:
        return abs(difference) <= self.absolute + EPSILON


class Checkpoint(Record):
    id: str
    after_step: int
    published_value: str
    keys: tuple[str, ...]
    measure: str
    tolerance: Tolerance


class Mismatch(Record):
    key: dict[str, str | int | float | bool | None]
    ours: float | None
    theirs: float | None


class Comparison(Record):
    checkpoint: str
    compared: int
    within: int
    missing: int
    extra: int
    max_abs_difference: float
    mismatches: tuple[Mismatch, ...]

    @property
    def passed(self) -> bool:
        return self.within == self.compared and self.missing == 0 and self.compared > 0


class AnswerKey:
    """The publisher's values for one checkpoint. There is no way to read them back out, only to compare."""

    __slots__ = ("_frame", "_source")

    def __init__(self, frame: Frame, source: str):
        self._frame = frame
        self._source = source

    def __repr__(self) -> str:
        return f"AnswerKey(sealed, source={self._source!r})"

    def compare(self, ours: Frame, checkpoint: Checkpoint, *, limit: int = 50) -> Comparison:
        keys, measure = list(checkpoint.keys), checkpoint.measure
        left = ours.table.select(keys + [measure]).rename_columns(keys + ["ours"])
        right = self._frame.table.select(keys + [measure]).rename_columns(keys + ["theirs"])
        joined = left.join(right, keys=keys, join_type="full outer").sort_by([(k, "ascending") for k in keys])
        ours_col, theirs_col = joined.column("ours"), joined.column("theirs")
        both = pc.and_(pc.is_valid(ours_col), pc.is_valid(theirs_col))
        missing = pc.sum(pc.and_(pc.is_null(ours_col), pc.is_valid(theirs_col))).as_py() or 0
        extra = pc.sum(pc.and_(pc.is_valid(ours_col), pc.is_null(theirs_col))).as_py() or 0
        paired = joined.filter(both)
        diffs = pc.abs(pc.subtract(paired.column("ours"), paired.column("theirs")))
        ok = pc.less_equal(diffs, pa.scalar(checkpoint.tolerance.absolute + EPSILON))
        mismatches = []
        for row in joined.to_pylist():
            o, t = row["ours"], row["theirs"]
            if o is None or t is None or not checkpoint.tolerance.admits(o - t):
                mismatches.append(Mismatch(key={k: row[k] for k in keys}, ours=o, theirs=t))
                if len(mismatches) >= limit:
                    break
        return Comparison(
            checkpoint=checkpoint.id,
            compared=paired.num_rows,
            within=pc.sum(ok).as_py() or 0,
            missing=missing,
            extra=extra,
            max_abs_difference=(pc.max(diffs).as_py() if paired.num_rows else None) or 0.0,
            mismatches=tuple(mismatches),
        )


def blame_window(results: Mapping[int, bool], step_count: int) -> tuple[int, ...]:
    """The steps that may hold a fault, given pass or fail at each checkpoint (keyed by the step it follows).

    The fault lies after the last passing checkpoint that precedes the first failing one, and at or before
    that failing checkpoint. No failure means an empty window.
    """
    failing = [step for step, passed in sorted(results.items()) if not passed]
    if not failing:
        return ()
    first = failing[0]
    passing_before = [step for step, passed in results.items() if passed and step < first]
    start = max(passing_before) + 1 if passing_before else 1
    if not 1 <= first <= step_count:
        raise ValueError(f"checkpoint after step {first} is outside a method of {step_count} steps")
    return tuple(range(start, first + 1))


class Divergence(Record):
    id: str
    checkpoint: str
    size: float
    tolerance: float
    suspected_steps: tuple[int, ...]
    status: DivergenceStatus = DivergenceStatus.OPEN
    cause: CauseClass | None = None
    explanation: str = ""
    evidence: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _closed_only_with_a_reason(self) -> Divergence:
        if self.status is not DivergenceStatus.OPEN and (self.cause is None or not self.explanation):
            raise ValueError(f"divergence {self.id} cannot be {self.status} without a cause and an explanation")
        if self.status is DivergenceStatus.CORRECTED and self.cause in (
            CauseClass.PUBLISHER_ERROR, CauseClass.UNPUBLISHED_STEP, CauseClass.VINTAGE_UNOBTAINABLE,
        ):
            raise ValueError(f"a {self.cause} divergence is outside our code; it can be explained or accepted, not corrected")
        if self.status is DivergenceStatus.CORRECTED and not self.evidence:
            raise ValueError("a corrected divergence names the evidence that it is gone")
        return self


class DivergenceRegister:
    """Append-only. A divergence is never deleted; a change of status is a new entry in its history."""

    def __init__(self) -> None:
        self._history: list[Divergence] = []

    def record(self, divergence: Divergence) -> None:
        if divergence.id in self.current():
            raise ValueError(f"divergence {divergence.id} already exists; update its status instead")
        if divergence.status is not DivergenceStatus.OPEN:
            raise ValueError("a divergence enters the register open")
        self._history.append(divergence)

    def update(self, divergence_id: str, **changes: object) -> Divergence:
        current = self.current()
        if divergence_id not in current:
            raise KeyError(divergence_id)
        updated = Divergence.model_validate(current[divergence_id].model_dump() | changes)
        self._history.append(updated)
        return updated

    def current(self) -> dict[str, Divergence]:
        latest: dict[str, Divergence] = {}
        for entry in self._history:
            latest[entry.id] = entry
        return latest

    def history(self, divergence_id: str) -> Sequence[Divergence]:
        return tuple(d for d in self._history if d.id == divergence_id)

    def open(self) -> tuple[Divergence, ...]:
        return tuple(d for d in self.current().values() if d.status is DivergenceStatus.OPEN)
