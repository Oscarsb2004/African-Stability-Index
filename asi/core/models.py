"""
asi.core.models — runtime objects built from the registry.

These are the mutable, behaviour-carrying objects the registry hands to the
pipeline. They are distinct from `asi.core.schema`, which defines the immutable
transport records that cross the backend/frontend boundary:

    models.Indicator   loaded definition, used while running a stage
    schema.Observation one country-year value, serialized into the bundle

Consolidates the former models/indicator.py and models/pillar.py. The old
models/nation.py was dropped in Phase A: nothing in the pipeline used it, only a
smoke check in setup.py.
"""

from __future__ import annotations


class Indicator:
    """One indicator as declared in the registry YAML."""

    def __init__(
        self,
        variable_name: str,
        display_name: str,
        source: str,
        series_code: str,
        role: str,
        polarity: str,
        pillars: list[str],
        year_start: int,
        year_end: int,
        aggregation: str,
        database: str = "wdi",
        log_transform: bool = False,
    ):
        self.variable_name = variable_name
        self.display_name  = display_name
        self.source        = source
        self.series_code   = series_code
        self.role          = role
        self.polarity      = polarity
        self.pillars       = pillars
        self.year_start    = year_start
        self.year_end      = year_end
        self.aggregation   = aggregation
        self.database      = database        # "wdi" (wbgapi db=2) or "wgi" (db=3)
        self.log_transform = log_transform   # log1p before normalization
        self.justification = ""

    def __repr__(self):
        return (
            f"Indicator(variable_name={self.variable_name}, source={self.source}, "
            f"database={self.database}, role={self.role}, polarity={self.polarity}, "
            f"pillars={self.pillars})"
        )

    def set_justification(self, text: str):
        self.justification = text

    @property
    def is_scoring(self) -> bool:
        return self.role == "scoring"


class Pillar:
    """A pillar and the indicators assigned to it."""

    def __init__(self, key: str, name: str, justification: str, weight: float = 1 / 7):
        self.key           = key    # e.g. "A"
        self.name          = name   # e.g. "Political / Governance"
        self.justification = justification
        self.weight        = weight
        self.indicators: list[Indicator] = []

    def add_indicator(self, indicator: Indicator):
        self.indicators.append(indicator)

    def __repr__(self):
        return f"Pillar(key={self.key}, name={self.name}, indicators={len(self.indicators)})"

    def get_scoring_indicators(self) -> list[Indicator]:
        return [i for i in self.indicators if i.role == "scoring"]

    def get_descriptive_indicators(self) -> list[Indicator]:
        return [i for i in self.indicators if i.role == "descriptive"]


__all__ = ["Indicator", "Pillar"]
