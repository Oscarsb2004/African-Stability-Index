# run_config.py — edit this file before each pipeline run.
#
# WEIGHT_PRESET selects which pillar-weight profile to use.
# Options defined in config.WEIGHT_PRESETS:
#   "equal"           — 1/7 per pillar (default)
#   "security_focus"  — higher weight on Pillar E (Security) and Pillar A (Governance)
#   "governance_focus"— higher weight on Pillar A (Governance)
#   "custom"          — use the CUSTOM_WEIGHTS dict below
#
# All presets must sum to 1.0. Validation runs at startup of each pipeline module.

WEIGHT_PRESET = "equal"

# Only used when WEIGHT_PRESET = "custom". Values must sum to 1.0.
CUSTOM_WEIGHTS = {
    "A": 1/7,   # Political / Governance
    "B": 1/7,   # Economic
    "C": 1/7,   # Social / Human Capital
    "D": 1/7,   # Health
    "E": 1/7,   # Security / Conflict
    "F": 1/7,   # Environmental
    "G": 1/7,   # Structural / Infrastructure
}
