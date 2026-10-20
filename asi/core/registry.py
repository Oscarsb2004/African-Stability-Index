"""
asi.core.registry — loads and validates the indicator/pillar registry.

All pipeline access to indicator definitions goes through IndicatorRegistry;
no stage should read indicators_list/*.yaml directly. (verify/ reads the YAML
itself on purpose, so that it never inherits a bug from this loader.)

Moved from the root-level config.py in Phase A. Two changes were made:
  - imports now come from asi.core
  - PillarRegistry derives its pillars from PILLAR_DEFS instead of keeping a
    second hardcoded copy of the pillar names
"""

import yaml
import logging
from pathlib import Path

from asi.core.models import Indicator
from asi.core.constants import (
    PILLAR_DEFS, ACTIVE_PRESET, WEIGHT_PRESETS,
    WEIGHT_MIN, WEIGHT_MAX, SMALL,
    IQR_MULTIPLIER,
    COVERAGE_WARN_THRESHOLD, COVERAGE_ALERT_THRESHOLD,
    MAX_PILLAR_NAN_RATE, MIN_CRONBACH_ALPHA,
)


# ── Path constants ────────────────────────────────────────────────────────────
# Change INDICATORS_DIR to point to a different indicator set if needed.

INDICATORS_DIR = Path("indicators_list")
MANUAL_DIR     = Path("data/manual")
logger = logging.getLogger(__name__)

# ── Field constraints ─────────────────────────────────────────────────────────

VALID_ROLES        = {"scoring", "descriptive"}
VALID_POLARITIES   = {"positive", "negative"}
VALID_SOURCES      = {"wb_api", "wb_api_wgi", "ucdp", "manual"}
VALID_AGGREGATIONS = {"average", "most_recent", "average_recent_3", "average_recent_5", "sd_recent_10"}
VALID_DATABASES    = {"wdi", "wgi", "ucdp"}

REQUIRED_FIELDS = {
    "variable_name", "display_name", "source", "series_code",
    "role", "polarity", "pillars", "year_start", "year_end", "aggregation",
    "database", "log_transform",
}


# ─────────────────────────────────────────────────────────────────────────────
# PillarRegistry
# ─────────────────────────────────────────────────────────────────────────────

class PillarRegistry:
    """
    The pillars, derived from PILLAR_DEFS, with equal starting weights and their bounds.
    Read-only: the pillars are edited in constants.py, never at run time.
    """

    def __init__(self):
        # Derived from PILLAR_DEFS so pillar names exist in exactly one place.
        # The previous version hardcoded a second copy here, which silently
        # allowed the two to drift apart.
        self._pillars = {
            key: {
                "name": name,
                "weight": 1 / len(PILLAR_DEFS),
                "weight_min": WEIGHT_MIN,
                "weight_max": WEIGHT_MAX,
                "justification": "",
            }
            for key, name in PILLAR_DEFS.items()
        }

    def valid_keys(self) -> set:
        return set(self._pillars.keys())

    def list_pillars(self) -> dict:
        return dict(self._pillars)

    def get_pillar(self, key: str) -> dict:
        if key not in self._pillars:
            raise KeyError(f"Pillar '{key}' not found. Valid keys: {sorted(self.valid_keys())}")
        return self._pillars[key]

# ─────────────────────────────────────────────────────────────────────────────
# IndicatorRegistry
# ─────────────────────────────────────────────────────────────────────────────

class IndicatorRegistry:
    """
    Reads and validates the indicators_list/ folder; the YAML files are the registry,
    edited by hand (the write API and scripts/add_indicators.py were retired 2026-10-19).
    All pipeline indicator access goes through this class.
    """

    def __init__(self, pillar_registry: PillarRegistry, yaml_dir: Path = INDICATORS_DIR):
        self._yaml_dir        = yaml_dir
        self._pillar_registry = pillar_registry
        self._indicators      = self._load()

    # ── Internal I/O ─────────────────────────────────────────────────────────

    def _load(self) -> list[dict]:
        """
        Merges all pillar yaml files into one flat list.
        Guards against empty files returning None.
        O(n)
        """
        if not self._yaml_dir.exists():
            raise FileNotFoundError(
                f"Indicators directory not found: {self._yaml_dir}\n"
                f"Expected folder at {self._yaml_dir.resolve()}"
            )

        indicators = []
        for path in sorted(self._yaml_dir.glob("*.yaml")):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:          # guards against None from empty/comment-only files
                continue
            indicators.extend(data)

        return indicators

    # ── Reading ───────────────────────────────────────────────────────────────

    def list_indicators(self, pillar: str | None = None, role: str | None = None) -> list[dict]:
        # O(n) single pass
        result = self._indicators
        if pillar:
            result = [i for i in result if pillar in i.get("pillars", [])]
        if role:
            result = [i for i in result if i.get("role") == role]
        return result

    def get_indicator(self, variable_name: str) -> dict:
        # O(n)
        for indicator in self._indicators:
            if indicator["variable_name"] == variable_name:
                return indicator
        raise KeyError(
            f"Indicator '{variable_name}' not found. "
            f"Use list_indicators() to see all available indicators."
        )

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate_fields(self, entry: dict, valid_keys: set | None = None) -> list[str]:
        """
        Validates a single entry. Returns list of error strings.
        Accepts valid_keys to avoid re-fetching inside validate_all loop.
        """
        errors = []
        name = entry.get("variable_name", "unknown")

        # required fields present
        for field in REQUIRED_FIELDS:
            if field not in entry or entry[field] in (None, ""):
                errors.append(f"[{name}] missing required field: '{field}'")

        if errors:
            return errors   # no point checking further if fields are missing

        # role, polarity, source
        if entry["role"] not in VALID_ROLES:
            errors.append(f"[{name}] invalid role '{entry['role']}' — must be one of {VALID_ROLES}")

        if entry["polarity"] not in VALID_POLARITIES:
            errors.append(f"[{name}] invalid polarity '{entry['polarity']}' — must be one of {VALID_POLARITIES}")

        if entry["source"] not in VALID_SOURCES:
            errors.append(f"[{name}] invalid source '{entry['source']}' — must be one of {VALID_SOURCES}")

        # pillars
        if not isinstance(entry["pillars"], list) or len(entry["pillars"]) == 0:
            errors.append(f"[{name}] 'pillars' must be a non-empty list")
        else:
            resolved_keys: set = valid_keys if valid_keys is not None else self._pillar_registry.valid_keys()
            bad = [p for p in entry["pillars"] if p not in resolved_keys]
            if bad:
                errors.append(
                    f"[{name}] invalid pillar keys: {bad} — "
                    f"valid keys: {sorted(resolved_keys)}"
                )

        # year range
        year_start = entry.get("year_start")
        year_end   = entry.get("year_end")

        if not isinstance(year_start, int):
            errors.append(f"[{name}] year_start must be an integer")
        if not isinstance(year_end, int):
            errors.append(f"[{name}] year_end must be an integer")
        if isinstance(year_start, int) and isinstance(year_end, int):
            if year_start > year_end:
                errors.append(f"[{name}] year_start ({year_start}) cannot be greater than year_end ({year_end})")

        # aggregation
        if entry["aggregation"] not in VALID_AGGREGATIONS:
            errors.append(
                f"[{name}] invalid aggregation '{entry['aggregation']}' — "
                f"must be one of {VALID_AGGREGATIONS}"
            )

        # database
        if entry.get("database") not in VALID_DATABASES:
            errors.append(
                f"[{name}] invalid database '{entry.get('database')}' — "
                f"must be one of {VALID_DATABASES}"
            )

        # log_transform
        if not isinstance(entry.get("log_transform"), bool):
            errors.append(f"[{name}] 'log_transform' must be a boolean (true/false)")

        # theoretical_bounds (optional): the possible extremes, used as goalposts (edition 2, plan 4.4)
        bounds = entry.get("theoretical_bounds")
        if bounds is not None and not (isinstance(bounds, list) and len(bounds) == 2
                                       and all(isinstance(b, (int, float)) for b in bounds) and bounds[0] < bounds[1]):
            errors.append(f"[{name}] 'theoretical_bounds' must be [low, high] with low < high")

        # per_capita (optional): divide by population_total and multiply by this scale (edition 2, P57)
        scale = entry.get("per_capita")
        if scale is not None and not (isinstance(scale, int) and not isinstance(scale, bool) and scale > 0):
            errors.append(f"[{name}] 'per_capita' must be a positive whole number, such as 100000")

        # source format
        errors += self._validate_source(entry["source"], entry["series_code"], name)
        return errors

    def _validate_source(self, source: str, series_code: str, name: str) -> list[str]:
        """
        wb_api     : checks series_code contains at least one dot (loose format check).
        wb_api_wgi : same dot check — pulled via wbgapi db=3 (Worldwide Governance Indicators).
        manual     : checks file exists in data/manual/.
        """
        errors = []
        if source in {"wb_api", "wb_api_wgi"}:
            if "." not in series_code:
                errors.append(
                    f"[{name}] series_code '{series_code}' looks invalid — "
                    f"WB codes contain dots e.g. 'NY.GDP.PCAP.CD'"
                )
        elif source == "manual":
            expected = MANUAL_DIR / series_code
            if not expected.exists():
                errors.append(
                    f"[{name}] manual file '{series_code}' not found in {MANUAL_DIR}/"
                )
        return errors

    def validate_all(self) -> bool:
        """
        Single pass over all indicators. Collects all errors before reporting.
        Call once at pipeline startup — halt pipeline if returns False.
        O(n)
        """
        all_errors = []
        seen_names = set()
        valid_keys = self._pillar_registry.valid_keys()  # pulled once, not per indicator

        for entry in self._indicators:
            name = entry.get("variable_name", "unknown")

            if name in seen_names:
                all_errors.append(f"[{name}] duplicate variable_name")
            seen_names.add(name)

            all_errors += self._validate_fields(entry, valid_keys=valid_keys)

        if all_errors:
            logger.error("validate_all failed — %d error(s) found:", len(all_errors))
            for error in all_errors:
                logger.error("  %s", error)
            return False

        logger.info("validate_all passed — %d indicators OK.", len(self._indicators))
        return True

    # ── Building objects ──────────────────────────────────────────────────────

    def build_indicators(self) -> dict[str, Indicator]:
        # O(n)
        indicators = {}
        for i in self._indicators:
            indicator = Indicator(
                variable_name = i["variable_name"],
                display_name  = i["display_name"],
                source        = i["source"],
                series_code   = i["series_code"],
                role          = i["role"],
                polarity      = i["polarity"],
                pillars       = i["pillars"],
                year_start    = i["year_start"],
                year_end      = i["year_end"],
                aggregation   = i["aggregation"],
                database      = i.get("database", "wdi"),
                log_transform = i.get("log_transform", False),
            )
            if i.get("justification"):
                indicator.set_justification(i["justification"])
            indicators[i["variable_name"]] = indicator
        return indicators
