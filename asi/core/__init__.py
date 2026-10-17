"""
asi.core — constants, canonical schema, registry, and country data.

Import from here rather than reaching into submodules:

    from asi.core import PILLAR_DEFS, COUNTRIES, Observation

The four submodules divide as follows:
    constants   every tunable value; region profile (the GSI seam)
    schema      immutable transport records crossing the backend/frontend line
    models      mutable runtime objects used while a stage runs
    countries   the country registry for this edition
    registry    loads and validates indicators_list/*.yaml
"""

from asi.core.constants import (
    PILLAR_DEFS, ACTIVE_PRESET, WEIGHT_PRESETS,
    WEIGHT_MIN, WEIGHT_MAX, SMALL,
    IQR_MULTIPLIER, MIN_REGIONAL_SAMPLE,
    COVERAGE_WARN_THRESHOLD, COVERAGE_ALERT_THRESHOLD,
    RELIABILITY_RELIABLE_AT, RELIABILITY_THIN_AT,
    RELIABILITY_MAX_IMPUTED, MIN_PILLARS_FOR_COMPOSITE,
    MAX_PILLAR_NAN_RATE, MIN_CRONBACH_ALPHA,
    RegionProfile, AFRICA, ACTIVE_PROFILE, ISLAND_SET,
)
from asi.core.schema import (
    Provenance, Reliability, Polarity, WindowMode,
    IndicatorSpec, Observation, PillarScore, CompositeScore,
    classify_reliability, missing_keys,
    REQUIRED_COUNTRY_KEYS, REQUIRED_INDICATOR_KEYS,
)
from asi.core.models import Indicator, Pillar
from asi.core.countries import COUNTRIES

__all__ = [
    # constants
    "PILLAR_DEFS", "ACTIVE_PRESET", "WEIGHT_PRESETS",
    "WEIGHT_MIN", "WEIGHT_MAX", "SMALL",
    "IQR_MULTIPLIER", "MIN_REGIONAL_SAMPLE",
    "COVERAGE_WARN_THRESHOLD", "COVERAGE_ALERT_THRESHOLD",
    "RELIABILITY_RELIABLE_AT", "RELIABILITY_THIN_AT",
    "RELIABILITY_MAX_IMPUTED", "MIN_PILLARS_FOR_COMPOSITE",
    "MAX_PILLAR_NAN_RATE", "MIN_CRONBACH_ALPHA",
    "RegionProfile", "AFRICA", "ACTIVE_PROFILE", "ISLAND_SET",
    # schema
    "Provenance", "Reliability", "Polarity", "WindowMode",
    "IndicatorSpec", "Observation", "PillarScore", "CompositeScore",
    "classify_reliability", "missing_keys",
    "REQUIRED_COUNTRY_KEYS", "REQUIRED_INDICATOR_KEYS",
    # models / data
    "Indicator", "Pillar", "COUNTRIES",
]
