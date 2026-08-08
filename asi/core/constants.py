"""
asi.core.constants — every tunable value in the project, in one place.

Consolidates the former root-level `constants.py` and `run_config.py`.
(`run_config.py` was dead configuration: it declared WEIGHT_PRESET but no
pipeline stage ever read it — only `setup.py` inspected it. The live switch has
always been ACTIVE_PRESET below.)

Region-specific values live in a RegionProfile rather than as module globals, so
the pipeline itself contains no hardcoded Africa. Content (narrative, colonial
history, RECs) stays deliberately Africa-specific; the *machinery* does not.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ── Pillar definitions — the single source of truth ────────────────────────────
# Never redefine these anywhere else. asi.core.registry derives its pillar
# objects from this dict; verify/ asserts no module shadows it.

PILLAR_DEFS: dict[str, str] = {
    "A": "Political / Governance",
    "B": "Economic",
    "C": "Social / Human Capital",
    "D": "Health",
    "E": "Security / Conflict",
    "F": "Environmental",
    "G": "Structural / Infrastructure",
}


# ── Weight presets ─────────────────────────────────────────────────────────────
# ACTIVE_PRESET selects which profile drives the arithmetic "equal weights"
# column. All presets must sum to 1.0 and stay within [WEIGHT_MIN, WEIGHT_MAX].

ACTIVE_PRESET = "equal"

WEIGHT_PRESETS: dict[str, dict[str, float]] = {
    "equal": {k: 1 / 7 for k in PILLAR_DEFS},
    "security_focus": {
        "A": 0.20, "B": 0.10, "C": 0.10, "D": 0.10,
        "E": 0.30, "F": 0.10, "G": 0.10,
    },
    "governance_focus": {
        "A": 0.25, "B": 0.15, "C": 0.10, "D": 0.10,
        "E": 0.20, "F": 0.10, "G": 0.10,
    },
    "my_weights": {
        "A": 0.20, "B": 0.10, "C": 0.15, "D": 0.20,
        "E": 0.15, "F": 0.10, "G": 0.10,
    },
}


# ── Scoring bounds (Benefit-of-the-Doubt LP) ───────────────────────────────────

WEIGHT_MIN = 0.05   # lower bound per pillar in the BoD LP
WEIGHT_MAX = 0.25   # upper bound per pillar in the BoD LP
SMALL      = 1e-8   # numerical floor for log/division operations


# ── Panel window (Phase B) ─────────────────────────────────────────────────────
# The index is a panel: country x indicator x year.
#
# PANEL_START is 2000 because that is where the data actually begins, not a
# preference. Probed against the World Bank API (2026-08):
#   WGI (all six series, 100% of Pillar A): 0 countries before 2000, 53 in 2000
#   Electricity access (Pillar G):          4 countries in 1990, 25 in 1995, 51 in 2000
# Starting earlier would leave two of seven pillars empty and make the composite
# meaningless for those years.
#
# WGI was biennial before 2002 (1996, 1998, 2000, 2002), so 2001 has no WGI
# observation. It is carried forward from 2000 and flagged as such — never
# silently interpolated.

PANEL_START        = 2000
PANEL_PULL_BUFFER  = 5   # extra years pulled before PANEL_START to feed rolling
                         # means and carry-forward at the panel's left edge

# How many years a real observation may be reused for later years before the
# value stops counting as a measurement. Uniform by default: tuning this
# per indicator without evidence would be arbitrary, and the reliability tiers
# already expose the consequence of staleness.
DEFAULT_MAX_CARRY_FORWARD = 5

# Displayed score precision. Two decimals is the accepted presentation: it keeps
# the interface readable, at the cost of occasional visible near-ties (two
# countries can display the same score and rank one apart, which is correct at
# full precision). verify/contract.py reports those as WARN so they stay visible.
DISPLAY_DECIMALS = 2


# ── Cleaning parameters ────────────────────────────────────────────────────────

# Deliberately widened from Tukey's conventional 1.5. At n=54, 1.5x IQR clips
# too aggressively and compresses cross-country differentiation in the middle of
# the distribution; 2.0x still caps genuine outliers (Somalia, Mauritius)
# without truncating moderate variation. Documented in methodology/references.md.
IQR_MULTIPLIER = 2.0

MIN_REGIONAL_SAMPLE      = 3     # minimum peer countries required for a regional-mean fill
COVERAGE_WARN_THRESHOLD  = 0.75  # below this -> SPARSE flag
COVERAGE_ALERT_THRESHOLD = 0.50  # below this -> VERY SPARSE flag


# ── Reliability tiers (Phase B) ────────────────────────────────────────────────
# A score assembled mostly from regional averages is not a measurement. These
# thresholds decide when the interface shows a number, mutes it, or greys it out.
# Consumed by asi.core.schema.classify_reliability().

RELIABILITY_RELIABLE_AT   = 0.60  # coverage at or above this -> reliable
RELIABILITY_THIN_AT       = 0.40  # coverage at or above this -> thin (muted)
RELIABILITY_MAX_IMPUTED   = 0.50  # imputed share above this -> unreliable regardless
MIN_PILLARS_FOR_COMPOSITE = 5     # composite needs this many usable pillars


# ── Quality gates ──────────────────────────────────────────────────────────────
# Kept as advisory thresholds. Phase A moved enforcement out of the pipeline and
# into verify/; nothing here calls sys.exit().

MAX_PILLAR_NAN_RATE = 0.30  # flag if >30% of countries have no data in a pillar
MIN_CRONBACH_ALPHA  = 0.60  # flag if pillar internal consistency falls below this


# ── Region profile — the GSI seam ──────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RegionProfile:
    """
    Everything that makes an edition specific to one part of the world.

    A future Global Stability Index supplies a different profile; the pipeline
    code needs no change. Narrative content remains Africa-specific by design.
    """

    key: str
    display_name: str
    map_scope: str                       # plotly choropleth scope
    subregions: tuple[str, ...]          # internal grouping used for regional fills
    island_states: frozenset[str]        # structurally advantaged small islands
    community_label: str                 # what a country grouping is called
    communities: tuple[str, ...]         # the groupings themselves

    def is_island(self, iso3: str) -> bool:
        return iso3 in self.island_states


AFRICA = RegionProfile(
    key="africa",
    display_name="Africa",
    map_scope="africa",
    # Grouping used for regional-mean imputation. Note "Islands" holds only 5
    # countries, so a regional fill there rests on a very thin peer pool
    # (MIN_REGIONAL_SAMPLE is 3) — verify/advisory.py flags this.
    subregions=("North", "West", "East", "Central", "South", "Islands"),
    # Small island states rank structurally high across every method: small
    # populations depress absolute conflict counts, sea borders remove land-border
    # security concerns, and concentrated economies are easier to administer.
    # Cabo Verde is deliberately an island state in the *West* region: it is
    # politically and economically West African. Island membership and region
    # membership are independent flags, not a hierarchy.
    island_states=frozenset({"SYC", "MUS", "COM", "CPV", "STP", "MDG"}),
    community_label="Regional Economic Community",
    # The eight RECs recognised by the African Union.
    communities=("UMA", "COMESA", "CEN-SAD", "EAC", "ECCAS", "ECOWAS", "IGAD", "SADC"),
)

#: The profile this edition runs against.
ACTIVE_PROFILE = AFRICA

#: Backwards-compatible alias. Prefer ACTIVE_PROFILE.island_states in new code.
ISLAND_SET = ACTIVE_PROFILE.island_states


__all__ = [
    "PILLAR_DEFS", "ACTIVE_PRESET", "WEIGHT_PRESETS",
    "WEIGHT_MIN", "WEIGHT_MAX", "SMALL",
    "IQR_MULTIPLIER", "MIN_REGIONAL_SAMPLE",
    "COVERAGE_WARN_THRESHOLD", "COVERAGE_ALERT_THRESHOLD",
    "RELIABILITY_RELIABLE_AT", "RELIABILITY_THIN_AT",
    "RELIABILITY_MAX_IMPUTED", "MIN_PILLARS_FOR_COMPOSITE",
    "MAX_PILLAR_NAN_RATE", "MIN_CRONBACH_ALPHA",
    "PANEL_START", "PANEL_PULL_BUFFER", "DEFAULT_MAX_CARRY_FORWARD",
    "DISPLAY_DECIMALS",
    "RegionProfile", "AFRICA", "ACTIVE_PROFILE", "ISLAND_SET",
]
