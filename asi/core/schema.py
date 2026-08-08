"""
asi.core.schema — canonical objects shared by the whole project.

The governing principle (ASI v2 plan §3):

    The frontend and the backend are the same object.

An indicator observation is one record carrying BOTH its identity
(variable_name, display_name, series_code, database) and its value for a given
year. Identity travels with the value; the UI renders what it is given and
never re-derives a label, a rank, or a score. `verify/contract.py` enforces
this across the bundle boundary.

Nothing here computes anything. These are transport and validation types only,
so the pipeline, the dashboard, and the independent verifier can agree on
exactly one vocabulary.

Design notes:
  - stdlib dataclasses, no new dependencies
  - every type round-trips through to_dict()/from_dict() for JSON transport
  - `year` is present on every value-bearing record so the Phase B panel
    (country x indicator x year) needs no schema change
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Iterable


# ── Vocabularies ───────────────────────────────────────────────────────────────

class Provenance(str, Enum):
    """How a value came to exist. Drives reliability and UI greying."""

    OBSERVED        = "observed"          # real measurement from the source database
    CARRIED_FORWARD = "carried_forward"   # last real value reused for a later year
    INTERPOLATED    = "interpolated"      # estimated between two real values
    REGIONAL_MEAN   = "regional_mean"     # imputed from regional peers
    DERIVED         = "derived"           # computed from other indicators (e.g. IDP per capita)
    ABSENT          = "absent"            # no value available

    @property
    def is_real(self) -> bool:
        """True only for a genuine measurement of this country-year."""
        return self is Provenance.OBSERVED

    @property
    def is_imputed(self) -> bool:
        """True when the value was inferred rather than measured."""
        return self in (
            Provenance.CARRIED_FORWARD,
            Provenance.INTERPOLATED,
            Provenance.REGIONAL_MEAN,
        )


class Reliability(str, Enum):
    """
    Whether an aggregate is trustworthy enough to display as a number.
    Thresholds live in asi.core.constants (RELIABILITY_*), not here.
    """

    RELIABLE   = "reliable"     # render normally
    THIN       = "thin"         # render muted, with a tooltip
    UNRELIABLE = "unreliable"   # grey out and say why
    ABSENT     = "absent"       # nothing to render

    @property
    def displayable(self) -> bool:
        """Whether a score should be shown as a number at all."""
        return self in (Reliability.RELIABLE, Reliability.THIN)


class Polarity(str, Enum):
    POSITIVE = "positive"   # higher raw value -> higher (better) score
    NEGATIVE = "negative"   # higher raw value -> lower score


class WindowMode(str, Enum):
    """How a year's value is drawn from the underlying series."""

    POINT        = "point"          # the single observation for that year
    MOST_RECENT  = "most_recent"    # latest observation at or before that year
    ROLLING_MEAN = "rolling_mean"   # mean of the trailing `window_years`


# ── Registry definition ────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class IndicatorSpec:
    """
    The definition of an indicator, as declared in registry YAML.

    This is the identity half of an Observation. It is loaded once and attached
    to every value so that no downstream stage ever needs to look a label up.
    """

    variable_name: str
    display_name: str
    series_code: str
    database: str
    role: str                     # "scoring" | "descriptive"
    polarity: Polarity
    pillars: tuple[str, ...]
    log_transform: bool = False

    # windowing (Phase B panel)
    window_mode: WindowMode = WindowMode.MOST_RECENT
    window_years: int = 1
    max_carry_forward: int = 5    # years a value may be reused before going stale

    # fixed goalposts — frozen per edition; None until generated
    goalpost_min: float | None = None
    goalpost_max: float | None = None

    justification: str = ""

    @property
    def is_scoring(self) -> bool:
        return self.role == "scoring"

    @property
    def has_goalposts(self) -> bool:
        return self.goalpost_min is not None and self.goalpost_max is not None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["polarity"] = self.polarity.value
        d["window_mode"] = self.window_mode.value
        d["pillars"] = list(self.pillars)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> IndicatorSpec:
        return cls(
            variable_name=d["variable_name"],
            display_name=d.get("display_name", d["variable_name"]),
            series_code=d.get("series_code", ""),
            database=d.get("database", "wdi"),
            role=d.get("role", "scoring"),
            polarity=Polarity(d.get("polarity", "positive")),
            pillars=tuple(d.get("pillars", ())),
            log_transform=bool(d.get("log_transform", False)),
            window_mode=WindowMode(d.get("window_mode", "most_recent")),
            window_years=int(d.get("window_years", 1)),
            max_carry_forward=int(d.get("max_carry_forward", 5)),
            goalpost_min=d.get("goalpost_min"),
            goalpost_max=d.get("goalpost_max"),
            justification=d.get("justification", ""),
        )


# ── Atomic value record ────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class Observation:
    """
    One indicator, one country, one year — identity and value together.

    This is the object the plan refers to when it says the frontend and backend
    are the same object. The dashboard renders `display_name`, `series_code`,
    and `score` straight off this record.
    """

    iso3: str
    variable_name: str
    display_name: str
    series_code: str
    database: str
    year: int

    raw_value: float | None = None           # as pulled from the source
    transformed_value: float | None = None   # after log / winsorization
    score: float | None = None               # normalized 0-100

    provenance: Provenance = Provenance.ABSENT
    source_year: int | None = None           # year the real measurement came from
    polarity: Polarity = Polarity.POSITIVE
    log_transform: bool = False
    goalpost_min: float | None = None
    goalpost_max: float | None = None
    clamped: bool = False                    # value fell outside frozen goalposts

    @property
    def is_real(self) -> bool:
        return self.provenance.is_real

    @property
    def staleness(self) -> int | None:
        """Years between the requested year and the underlying measurement."""
        if self.source_year is None:
            return None
        return self.year - self.source_year

    @property
    def identity(self) -> tuple[str, str, str, int]:
        """
        The tuple `verify/contract.py` matches on across the UI boundary.
        Deliberately excludes value, which varies by year.
        """
        return (self.iso3, self.variable_name, self.series_code, self.year)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["provenance"] = self.provenance.value
        d["polarity"] = self.polarity.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Observation:
        return cls(
            iso3=d["iso3"],
            variable_name=d["variable_name"],
            display_name=d.get("display_name", d["variable_name"]),
            series_code=d.get("series_code", ""),
            database=d.get("database", "wdi"),
            year=int(d["year"]),
            raw_value=d.get("raw_value"),
            transformed_value=d.get("transformed_value"),
            score=d.get("score"),
            provenance=Provenance(d.get("provenance", "absent")),
            source_year=d.get("source_year"),
            polarity=Polarity(d.get("polarity", "positive")),
            log_transform=bool(d.get("log_transform", False)),
            goalpost_min=d.get("goalpost_min"),
            goalpost_max=d.get("goalpost_max"),
            clamped=bool(d.get("clamped", False)),
        )


# ── Aggregates ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class PillarScore:
    """One pillar, one country, one year — with its own honesty flag."""

    iso3: str
    pillar_id: str
    year: int
    score: float | None
    n_indicators: int = 0
    n_observed: int = 0
    n_imputed: int = 0
    reliability: Reliability = Reliability.ABSENT
    contributing: tuple[str, ...] = ()   # variable_names actually used

    @property
    def coverage_ratio(self) -> float:
        """Share of this pillar's indicators that are real measurements."""
        if self.n_indicators == 0:
            return 0.0
        return self.n_observed / self.n_indicators

    @property
    def imputed_share(self) -> float:
        """Share of contributing values that were inferred."""
        used = self.n_observed + self.n_imputed
        if used == 0:
            return 0.0
        return self.n_imputed / used

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["reliability"] = self.reliability.value
        d["contributing"] = list(self.contributing)
        d["coverage_ratio"] = round(self.coverage_ratio, 4)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PillarScore:
        return cls(
            iso3=d["iso3"],
            pillar_id=d["pillar_id"],
            year=int(d["year"]),
            score=d.get("score"),
            n_indicators=int(d.get("n_indicators", 0)),
            n_observed=int(d.get("n_observed", 0)),
            n_imputed=int(d.get("n_imputed", 0)),
            reliability=Reliability(d.get("reliability", "absent")),
            contributing=tuple(d.get("contributing", ())),
        )


@dataclass(frozen=True, slots=True)
class CompositeScore:
    """One country, one year, one weighting method."""

    iso3: str
    year: int
    method: str                       # equal | pca | bod | entropy | geometric | custom
    score: float | None
    rank: int | None = None
    n_pillars_used: int = 0
    reliability: Reliability = Reliability.ABSENT

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["reliability"] = self.reliability.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CompositeScore:
        return cls(
            iso3=d["iso3"],
            year=int(d["year"]),
            method=d["method"],
            score=d.get("score"),
            rank=d.get("rank"),
            n_pillars_used=int(d.get("n_pillars_used", 0)),
            reliability=Reliability(d.get("reliability", "absent")),
        )


# ── Reliability classification ─────────────────────────────────────────────────

def classify_reliability(
    n_indicators: int,
    n_observed: int,
    n_imputed: int,
    *,
    reliable_at: float,
    thin_at: float,
    max_imputed_share: float,
) -> Reliability:
    """
    Map coverage onto a reliability tier.

    Thresholds are passed in (from asi.core.constants) rather than read here so
    this function stays pure and unit-testable.

    Rules, in order:
      1. nothing usable            -> ABSENT
      2. imputed majority          -> UNRELIABLE  (a regional mean is not a measurement)
      3. coverage >= reliable_at   -> RELIABLE
      4. coverage >= thin_at       -> THIN
      5. otherwise                 -> UNRELIABLE
    """
    if n_indicators <= 0 or (n_observed + n_imputed) == 0:
        return Reliability.ABSENT

    coverage = n_observed / n_indicators
    used = n_observed + n_imputed
    imputed_share = n_imputed / used

    if imputed_share > max_imputed_share:
        return Reliability.UNRELIABLE
    if coverage >= reliable_at:
        return Reliability.RELIABLE
    if coverage >= thin_at:
        return Reliability.THIN
    return Reliability.UNRELIABLE


# ── Bundle contract ────────────────────────────────────────────────────────────

#: Keys every serialized country record must carry. `verify/contract.py`
#: asserts these exist rather than letting the dashboard silently `.get()` a
#: missing field and render a blank.
REQUIRED_COUNTRY_KEYS: frozenset[str] = frozenset({
    "iso3", "name", "region", "scores", "pillar_scores", "indicators",
})

#: Keys every serialized indicator entry must carry inside a country record.
REQUIRED_INDICATOR_KEYS: frozenset[str] = frozenset({
    "variable_name", "display_name", "series_code", "score",
})


def missing_keys(record: dict[str, Any], required: Iterable[str]) -> list[str]:
    """Return the required keys absent from `record`, sorted for stable output."""
    return sorted(k for k in required if k not in record)


__all__ = [
    "Provenance", "Reliability", "Polarity", "WindowMode",
    "IndicatorSpec", "Observation", "PillarScore", "CompositeScore",
    "classify_reliability", "missing_keys",
    "REQUIRED_COUNTRY_KEYS", "REQUIRED_INDICATOR_KEYS",
]
