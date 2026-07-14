"""
constants.py — Single source of truth for all AII shared constants.

Import from here in config.py, 04_score.py, and 07_dashboard.py.
Never define PILLAR_DEFS or WEIGHT_PRESETS anywhere else.
"""

# ── Pillar definitions ─────────────────────────────────────────────────────────

PILLAR_DEFS = {
    "A": "Political / Governance",
    "B": "Economic",
    "C": "Social / Human Capital",
    "D": "Health",
    "E": "Security / Conflict",
    "F": "Environmental",
    "G": "Structural / Infrastructure",
}

# ── Weight presets ─────────────────────────────────────────────────────────────
# ACTIVE_PRESET selects which preset drives the arithmetic "equal weights" column.
# All presets must sum to 1.0; each weight should stay between WEIGHT_MIN and WEIGHT_MAX.
# Add new presets here only — never duplicate in 04_score.py or config.py.

ACTIVE_PRESET = "equal"

WEIGHT_PRESETS = {
    "equal": {k: 1/7 for k in "ABCDEFG"},
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

# ── Scoring bounds (BoD LP) ────────────────────────────────────────────────────

WEIGHT_MIN = 0.05   # lower bound per pillar in BoD LP
WEIGHT_MAX = 0.25   # upper bound per pillar in BoD LP
SMALL      = 1e-8   # numerical floor for log/division operations

# ── Island states ─────────────────────────────────────────────────────────────
# AU island member states that may be excluded from continental ranking displays.
# Add or remove here — never hardcode this set in individual scripts.

ISLAND_SET = {"SYC", "MUS", "COM", "CPV", "STP", "MDG"}

# ── Pipeline constants ─────────────────────────────────────────────────────────

# Raised from 1.5 → 2.0: 1.5× IQR is appropriate for large samples; for n=54
# it clips too aggressively and compresses cross-country differentiation in the
# middle of the distribution. 2.0× retains genuine outliers (Somalia, Mauritius)
# without truncating moderate variation. See 02_clean.py for implementation.
IQR_MULTIPLIER           = 2.0

MIN_REGIONAL_SAMPLE      = 3     # minimum peer countries for regional mean fill
COVERAGE_WARN_THRESHOLD  = 0.75  # below this → SPARSE flag
COVERAGE_ALERT_THRESHOLD = 0.50  # below this → VERY SPARSE flag

# ── Quality gates ──────────────────────────────────────────────────────────────
# Thresholds that halt or warn when data quality degrades beyond acceptable bounds.
# 02_clean.py checks these after fill and after diagnostics.

MAX_PILLAR_NAN_RATE = 0.30  # halt if > 30% of countries have no data in any pillar
MIN_CRONBACH_ALPHA  = 0.60  # warn if pillar internal consistency falls below 0.60
