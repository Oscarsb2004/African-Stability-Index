"""Build: one step per method step, each a small class with a declared interface.

A step declares its named inputs and their profiles, its output profile, its parameters, and its invariants -
properties that must hold for any input, which become tests. Calling a step checks all of that around `run`, so
a step cannot quietly return the wrong shape or break its own promises.

Steps are pure: they receive frames and parameters and return a frame. They have no network and no clock. The
shell catalogue built from their cards is also the fixed label set that a stage 3 selection model chooses from.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict

from athena.base import Definition, Record
from athena.frames import Frame
from athena.ids import ContentHash, Id, Version, canonical_json, hash_bytes, kind_of
from athena.vocab import Maturity, Profile


@dataclass(frozen=True)
class Invariant:
    """A property that must hold between a step's inputs and its output, whatever the data."""

    name: str
    description: str
    holds: Callable[[Mapping[str, Frame], Frame, BaseModel], bool]


class NoParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class StepResult(Record):
    step: str
    parameters: ContentHash
    inputs: dict[str, ContentHash]
    output: ContentHash
    invariants_checked: tuple[str, ...]


class ShellCard(Definition):
    """What a step is, for people and for programs: the entry in the shell catalogue."""

    KIND: ClassVar[str] = "shell"

    summary: str
    inputs: dict[str, Profile]
    output: Profile
    parameters_schema: dict[str, Any]
    invariants: tuple[str, ...]
    maturity: Maturity = Maturity.IDEA


class InvariantBroken(AssertionError):
    pass


class Step(ABC):
    ID: ClassVar[Id]
    VERSION: ClassVar[Version]
    TITLE: ClassVar[str]
    SUMMARY: ClassVar[str]
    INPUTS: ClassVar[dict[str, Profile]]
    OUTPUT: ClassVar[Profile]
    Parameters: ClassVar[type[BaseModel]] = NoParameters

    @classmethod
    def ref(cls) -> str:
        return f"{cls.ID}@{cls.VERSION}"

    @abstractmethod
    def run(self, inputs: Mapping[str, Frame], params: BaseModel) -> Frame:
        """The work itself. The returned manifest's produced_by must be this step's ref."""

    def invariants(self) -> tuple[Invariant, ...]:
        return ()

    def __call__(self, inputs: Mapping[str, Frame], parameters: Mapping[str, Any] | None = None) -> tuple[Frame, StepResult]:
        params = self.Parameters.model_validate(dict(parameters or {}))
        if set(inputs) != set(self.INPUTS):
            raise ValueError(f"{self.ID} takes inputs {sorted(self.INPUTS)}, got {sorted(inputs)}")
        for name, frame in inputs.items():
            if frame.manifest.profile is not self.INPUTS[name]:
                raise ValueError(f"{self.ID} input {name!r} must be {self.INPUTS[name]}, got {frame.manifest.profile}")
        output = self.run(inputs, params)
        if output.manifest.profile is not self.OUTPUT:
            raise ValueError(f"{self.ID} must return {self.OUTPUT}, returned {output.manifest.profile}")
        if output.manifest.produced_by != self.ref():
            raise ValueError(f"{self.ID} output must name produced_by={self.ref()!r}")
        checked = []
        for invariant in self.invariants():
            if not invariant.holds(inputs, output, params):
                raise InvariantBroken(f"{self.ID}: invariant {invariant.name!r} broken - {invariant.description}")
            checked.append(invariant.name)
        result = StepResult(
            step=self.ref(),
            parameters=hash_bytes(canonical_json(params.model_dump(mode="json"))),
            inputs={name: frame.content_hash() for name, frame in inputs.items()},
            output=output.content_hash(),
            invariants_checked=tuple(checked),
        )
        return output, result

    @classmethod
    def card(cls, maturity: Maturity = Maturity.IDEA) -> ShellCard:
        return ShellCard(
            id=cls.ID, version=cls.VERSION, title=cls.TITLE, summary=cls.SUMMARY, inputs=dict(cls.INPUTS),
            output=cls.OUTPUT, parameters_schema=cls.Parameters.model_json_schema(),
            invariants=tuple(i.name for i in cls().invariants()), maturity=maturity,
        )


class ShellRegistry:
    """The declared list of steps a project may use. Nothing runs that is not registered."""

    def __init__(self) -> None:
        self._steps: dict[str, type[Step]] = {}

    def register(self, step: type[Step]) -> type[Step]:
        if kind_of(step.ID) != "shell":
            raise ValueError(f"{step.__name__}.ID must be a shell id, got {step.ID!r}")
        if step.ID in self._steps:
            raise ValueError(f"{step.ID} is already registered")
        self._steps[step.ID] = step
        return step

    def get(self, step_id: str) -> type[Step]:
        try:
            return self._steps[step_id]
        except KeyError:
            raise KeyError(f"{step_id} is not a registered shell") from None

    def cards(self) -> tuple[ShellCard, ...]:
        return tuple(self._steps[k].card() for k in sorted(self._steps))

    def __contains__(self, step_id: str) -> bool:
        return step_id in self._steps
