"""Rounding: done once, in a declared step, by a declared rule.

The owner's default (2026-09-25) is round half up: .5 and above rounds up, anything below rounds down, with ties
going away from zero so that -2.5 becomes -3. A publisher that states a different rule is followed instead, and
the method card cites where it says so.

Numbers are rounded as they are written, not as binary floats store them: 2.675 rounds to 2.68, although the float
nearest 2.675 is slightly below it and Python's built-in round gives 2.67.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal
from enum import StrEnum

from pydantic import Field

from athena.base import Record
from athena.citations import Citation


class RoundingRule(StrEnum):
    HALF_UP = "half-up"
    HALF_EVEN = "half-even"


_DECIMAL_MODES = {RoundingRule.HALF_UP: ROUND_HALF_UP, RoundingRule.HALF_EVEN: ROUND_HALF_EVEN}


class Rounding(Record):
    decimals: int = Field(ge=0)
    rule: RoundingRule = RoundingRule.HALF_UP
    stated_by_publisher: Citation | None = None

    @property
    def is_default(self) -> bool:
        """True when the rule is ours, not one the publisher stated."""
        return self.stated_by_publisher is None

    def apply(self, value: float | None) -> float | None:
        if value is None:
            return None
        quantum = Decimal(1).scaleb(-self.decimals)
        return float(Decimal(repr(value)).quantize(quantum, rounding=_DECIMAL_MODES[self.rule]))
