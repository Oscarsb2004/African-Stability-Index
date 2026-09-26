"""The closed vocabularies. Every value here is a decision; adding one is a change to the contract.

They mirror the umbrella repository: roles and profiles from `architecture/frames.yaml`, validation levels and
reproducibility classes from decision P5, method origin from P4, and divergence causes from proposal AD-2026-01.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum


class Role(StrEnum):
    """What a column means, independent of its name. Views and tests select columns by role."""

    ENTITY = "entity"
    TIME = "time"
    MEASURE = "measure"
    CATEGORY = "category"
    SLICE = "slice"
    UNCERTAINTY_LOW = "uncertainty_low"
    UNCERTAINTY_HIGH = "uncertainty_high"
    STATUS = "status"
    LABEL = "label"
    GEOMETRY_REF = "geometry_ref"
    SOURCE_REF = "source_ref"


class Profile(StrEnum):
    """The eight shapes a frame may take. A new profile needs a recorded decision (P6)."""

    PANEL = "panel"
    CROSS_SECTION = "cross-section"
    TREE_SCORES = "tree-scores"
    MATRIX = "matrix"
    POINTS = "points"
    EVENTS = "events"
    PASSAGES = "passages"
    DISTRIBUTION = "distribution"

    @property
    def required_roles(self) -> frozenset[Role]:
        return REQUIRED_ROLES[self]


REQUIRED_ROLES: dict[Profile, frozenset[Role]] = {
    Profile.PANEL: frozenset({Role.ENTITY, Role.TIME, Role.MEASURE}),
    Profile.CROSS_SECTION: frozenset({Role.ENTITY, Role.MEASURE}),
    Profile.TREE_SCORES: frozenset({Role.ENTITY, Role.CATEGORY, Role.MEASURE}),
    Profile.MATRIX: frozenset({Role.ENTITY, Role.CATEGORY, Role.MEASURE}),
    Profile.POINTS: frozenset({Role.ENTITY, Role.GEOMETRY_REF}),
    Profile.EVENTS: frozenset({Role.ENTITY, Role.TIME, Role.CATEGORY}),
    Profile.PASSAGES: frozenset({Role.ENTITY, Role.LABEL, Role.SOURCE_REF}),
    Profile.DISTRIBUTION: frozenset({Role.ENTITY, Role.MEASURE, Role.UNCERTAINTY_LOW, Role.UNCERTAINTY_HIGH}),
}


class DType(StrEnum):
    """Column types a frame may hold. Money and rates are floats with a declared unit; dates are ISO dates."""

    STRING = "string"
    INT64 = "int64"
    FLOAT64 = "float64"
    BOOL = "bool"
    DATE = "date"


class ValidationLevel(IntEnum):
    """How well a value was checked (P5). Lower is stronger."""

    PUBLISHER_MATCH = 1
    INDEPENDENT_MATCH = 2
    INTERNAL_ONLY = 3
    UNVERIFIED = 4


class ReproClass(StrEnum):
    """How much of a value was recreated (P5)."""

    A = "A"  # fully recreated from source data
    B = "B"  # built from the publisher's own inputs, where the publisher ran a model we cannot rerun
    C = "C"  # hosted only


class Origin(StrEnum):
    """Where a method comes from (P4). Everything an own method produces is labelled derived."""

    PUBLISHED = "published"
    OWN = "own"


class Redistribution(StrEnum):
    ALLOWED = "allowed"
    ATTRIBUTION = "attribution"
    FORBIDDEN = "forbidden"
    UNKNOWN = "unknown"


class Access(StrEnum):
    API = "api"
    BULK = "bulk"
    DOCUMENT = "document"
    WEB = "web"


class CauseClass(StrEnum):
    """Why a value differs from the publisher's."""

    VINTAGE_MISMATCH = "vintage-mismatch"
    VINTAGE_UNOBTAINABLE = "vintage-unobtainable"
    GROUPING_ERROR = "grouping-error"
    METHOD_READING = "method-reading"
    INTERNAL_ERROR = "internal-error"
    UNPUBLISHED_STEP = "unpublished-step"
    PUBLISHER_ERROR = "publisher-error"
    ROUNDING = "rounding"


class DivergenceStatus(StrEnum):
    OPEN = "open"
    EXPLAINED = "explained"
    ACCEPTED = "accepted"
    CORRECTED = "corrected"


class Criterion(StrEnum):
    """The grounds on which an indicator is included in an index. Justifications are filed under one of these.

    They follow the usual construction criteria for composite indicators; the list is a draft for the owner.
    """

    RELEVANCE = "relevance"
    COVERAGE = "coverage"
    QUALITY = "quality"
    INDEPENDENCE = "independence"
    TIMELINESS = "timeliness"
    COMPARABILITY = "comparability"
    WEIGHTING = "weighting"
    NORMALISATION = "normalisation"
    AGGREGATION = "aggregation"


class Maturity(StrEnum):
    """How far a shared part has been proven (lifecycle:part-maturity in the umbrella)."""

    IDEA = "idea"
    CANDIDATE = "candidate"
    USED_ONCE = "used-once"
    PROVEN = "proven"
    FROZEN = "frozen"
    DEPRECATED = "deprecated"


class Stance(StrEnum):
    SUPPORTS = "supports"
    QUALIFIES = "qualifies"
    OPPOSES = "opposes"
