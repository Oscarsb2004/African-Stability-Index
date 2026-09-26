"""Method: the recipe as written, kept apart from the code that carries it out (decision P4).

A published method card numbers the publisher's steps and quotes the paragraph behind each one. Wherever the
text is unclear, the reading adopted is logged with its reason, and the owner rules on it; a reading is never
chosen because it matches the answer key. The card also lists every value the publisher releases along the way,
because those values decide where checkpoints can go.

An own method states a formula in the owner's words. It needs no citations, and everything it produces is
labelled derived.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import model_validator

from athena.base import Definition, Record
from athena.ids import Id
from athena.vocab import Origin


class Citation(Record):
    """Where in a stored document a statement comes from. The quote must be found verbatim at the locator."""

    document: Id
    locator: str
    quote: str


class MethodStep(Record):
    number: int
    name: str
    action: str
    citation: Citation | None = None
    shell: Id | None = None


class Reading(Record):
    """A sentence that can be read more than one way, the reading taken, and why."""

    step: int
    sentence: Citation
    options: tuple[str, ...]
    adopted: str
    reason: str
    owner_ruled: bool = False

    @model_validator(mode="after")
    def _adopted_is_an_option(self) -> Reading:
        if len(self.options) < 2:
            raise ValueError("a reading needs at least two options; otherwise the text is not ambiguous")
        if self.adopted not in self.options:
            raise ValueError("the adopted reading must be one of the options")
        return self


class PublishedValue(Record):
    """A value the publisher releases part-way through the method: a country table, a group list, a count."""

    name: str
    after_step: int
    description: str
    citation: Citation


class MethodCard(Definition):
    KIND: ClassVar[str] = "method"

    subject: Id
    origin: Origin
    steps: tuple[MethodStep, ...]
    readings: tuple[Reading, ...] = ()
    published_values: tuple[PublishedValue, ...] = ()
    formula: str | None = None

    @model_validator(mode="after")
    def _well_formed(self) -> MethodCard:
        numbers = [s.number for s in self.steps]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError(f"steps are numbered 1..n in order, got {numbers}")
        if self.origin is Origin.PUBLISHED:
            uncited = [s.number for s in self.steps if s.citation is None]
            if uncited:
                raise ValueError(f"a published method cites the text behind every step; uncited: {uncited}")
        elif not self.formula:
            raise ValueError("an own method states its formula")
        for n in [r.step for r in self.readings] + [v.after_step for v in self.published_values]:
            if n not in numbers:
                raise ValueError(f"step {n} is referred to but does not exist")
        return self

    @property
    def unruled_readings(self) -> tuple[Reading, ...]:
        return tuple(r for r in self.readings if not r.owner_ruled)

    def checkpoint_steps(self) -> tuple[int, ...]:
        """The steps after which the publisher gives us something to compare against."""
        return tuple(sorted({v.after_step for v in self.published_values}))
