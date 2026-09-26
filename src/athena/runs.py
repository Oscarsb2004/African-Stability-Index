"""Runs: the receipt of what was executed, so any result can be rebuilt and compared exactly.

A run records the code version, the frame parsed from each snapshot, every step's exact ref, the hash of its
parameters, inputs and output, and the comparisons made. Same inputs and same code give the same hashes; a
different hash is a finding.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import model_validator

from athena.base import Record
from athena.ids import ContentHash
from athena.steps import StepResult
from athena.validation import Comparison


class RunRecord(Record):
    id: str
    project: str
    started_at: datetime
    finished_at: datetime
    code_version: str
    environment: ContentHash
    parsed: dict[ContentHash, ContentHash]
    steps: tuple[StepResult, ...]
    comparisons: tuple[Comparison, ...] = ()

    @model_validator(mode="after")
    def _ordered_and_linked(self) -> RunRecord:
        if self.finished_at < self.started_at:
            raise ValueError("a run cannot finish before it starts")
        known = set(self.parsed.values())
        for step in self.steps:
            unknown = set(step.inputs.values()) - known
            if unknown:
                raise ValueError(f"{step.step} read {sorted(unknown)}, which no parsed snapshot or earlier step produced")
            known.add(step.output)
        return self

    @property
    def final_output(self) -> ContentHash | None:
        return self.steps[-1].output if self.steps else None
