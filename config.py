

import yaml
import logging
from pathlib import Path

from models.indicator import Indicator
from models.pillar import Pillar
from constants import (
    PILLAR_DEFS, ACTIVE_PRESET, WEIGHT_PRESETS,
    WEIGHT_MIN, WEIGHT_MAX, SMALL,
    IQR_MULTIPLIER, MIN_REGIONAL_SAMPLE,
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
VALID_SOURCES      = {"wb_api", "wb_api_wgi", "manual"}
VALID_AGGREGATIONS = {"average", "most_recent", "average_recent_3", "average_recent_5"}
VALID_DATABASES    = {"wdi", "wgi"}

REQUIRED_FIELDS = {
    "variable_name", "display_name", "source", "series_code",
    "role", "polarity", "pillars", "year_start", "year_end", "aggregation",
    "database", "log_transform",
}
EDITABLE_FIELDS = REQUIRED_FIELDS | {"justification"}




# ─────────────────────────────────────────────────────────────────────────────
# PillarRegistry
# ─────────────────────────────────────────────────────────────────────────────

class PillarRegistry:
    """
    Hardcoded pillar definitions. Editable via methods — never directly.
    Weights must always sum to 1.0.
    """

    def __init__(self):
        self._pillars = {
            "A": {"name": "Political / Governance",      "weight": 1/7, "weight_min": 0.05, "weight_max": 0.25, "justification": ""},
            "B": {"name": "Economic",                    "weight": 1/7, "weight_min": 0.05, "weight_max": 0.25, "justification": ""},
            "C": {"name": "Social / Human Capital",      "weight": 1/7, "weight_min": 0.05, "weight_max": 0.25, "justification": ""},
            "D": {"name": "Health",                      "weight": 1/7, "weight_min": 0.05, "weight_max": 0.25, "justification": ""},
            "E": {"name": "Security / Conflict",         "weight": 1/7, "weight_min": 0.05, "weight_max": 0.25, "justification": ""},
            "F": {"name": "Environmental",               "weight": 1/7, "weight_min": 0.05, "weight_max": 0.25, "justification": ""},
            "G": {"name": "Structural / Infrastructure", "weight": 1/7, "weight_min": 0.05, "weight_max": 0.25, "justification": ""},
        }

    def valid_keys(self) -> set:
        return set(self._pillars.keys())

    def list_pillars(self) -> dict:
        return dict(self._pillars)

    def get_pillar(self, key: str) -> dict:
        if key not in self._pillars:
            raise KeyError(f"Pillar '{key}' not found. Valid keys: {sorted(self.valid_keys())}")
        return self._pillars[key]

    def add_pillar(self, key: str, name: str, justification: str, weight: float | None = None):
        if key in self._pillars:
            raise ValueError(f"Pillar '{key}' already exists.")
        if weight is None:
            n = len(self._pillars) + 1
            weight = 1 / n
            for k in self._pillars:
                self._pillars[k]["weight"] = 1 / n
        test = {**self._pillars, key: {"weight": weight}}
        if not _weights_sum_to_one(test):
            raise ValueError("Pillar weights do not sum to 1.0 after addition.")
        self._pillars[key] = {
            "name": name, "weight": weight,
            "weight_min": WEIGHT_MIN, "weight_max": WEIGHT_MAX,
            "justification": justification,
        }

    def remove_pillar(self, key: str, indicator_registry=None):
        if key not in self._pillars:
            raise KeyError(f"Pillar '{key}' not found.")
        if indicator_registry:
            affected = indicator_registry.list_indicators(pillar=key)
            if affected:
                names = [i["variable_name"] for i in affected]
                logger.warning("Removing pillar '%s' affects indicators: %s", key, names)
        del self._pillars[key]

    def edit_pillar(self, key: str, field: str, new_value):
        if key not in self._pillars:
            raise KeyError(f"Pillar '{key}' not found.")
        if field not in {"name", "weight", "weight_min", "weight_max", "justification"}:
            raise ValueError(f"'{field}' is not an editable pillar field.")
        if field == "weight":
            test = {k: dict(v) for k, v in self._pillars.items()}
            test[key]["weight"] = new_value
            if not _weights_sum_to_one(test):
                raise ValueError("Pillar weights do not sum to 1.0 after edit.")
        self._pillars[key][field] = new_value


# ─────────────────────────────────────────────────────────────────────────────
# IndicatorRegistry
# ─────────────────────────────────────────────────────────────────────────────

class IndicatorRegistry:
    """
    Reads and writes the indicators_list/ folder.
    All pipeline indicator access goes through this class.
    """

    def __init__(self, pillar_registry: PillarRegistry, yaml_dir: Path = INDICATORS_DIR):
        self._yaml_dir        = yaml_dir
        self._pillar_registry = pillar_registry
        self._file_map        = {}   # {variable_name: Path} — tracks which file each indicator came from
        self._indicators      = self._load()

    # ── Internal I/O ─────────────────────────────────────────────────────────

    def _load(self) -> list[dict]:
        """
        Merges all pillar yaml files into one flat list.
        Populates _file_map so every indicator knows its source file.
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
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            if not data:          # guards against None from empty/comment-only files
                continue
            for entry in data:
                indicators.append(entry)
                self._file_map[entry["variable_name"]] = path

        return indicators

    def _resolve_target_file(self, pillars: list[str]) -> Path:
        """
        Determines which pillar file a new indicator should be written to.
        Derives order from PillarRegistry so it stays in sync if pillars are added.
        e.g. pillars: ["E", "A"] still routes to pillar_a.yaml
        """
        pillar_order = list(self._pillar_registry.list_pillars().keys())
        for key in pillar_order:
            if key in pillars:
                return self._yaml_dir / f"pillar_{key.lower()}.yaml"
        raise ValueError(f"No valid pillar key found in {pillars}")

    def _rewrite_file(self, path: Path):
        """
        Rewrites a single pillar yaml file with all indicators currently
        mapped to it. Only touches one file — leaves all others unchanged.
        """
        entries = [
            ind for ind in self._indicators
            if self._file_map.get(ind["variable_name"]) == path
        ]
        with open(path, "r") as f:
            existing = f.read()

        # preserve header comments at the top of the file
        comments = []
        for line in existing.splitlines():
            if line.startswith("#"):
                comments.append(line)
            else:
                break

        with open(path, "w") as f:
            if comments:
                f.write("\n".join(comments) + "\n\n")
            if entries:
                yaml.dump(entries, f, allow_unicode=True, sort_keys=False)

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

    # ── Writing ───────────────────────────────────────────────────────────────

    def add_indicator(
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
        justification: str = "",
    ):
        # duplicate check — O(n)
        for i in self._indicators:
            if i["variable_name"] == variable_name:
                raise ValueError(f"Indicator '{variable_name}' already exists.")

        entry = {
            "variable_name": variable_name,
            "display_name":  display_name,
            "source":        source,
            "series_code":   series_code,
            "role":          role,
            "polarity":      polarity,
            "pillars":       pillars,
            "year_start":    year_start,
            "year_end":      year_end,
            "aggregation":   aggregation,
            "database":      database,
            "log_transform": log_transform,
            "justification": justification,
        }

        errors = self._validate_fields(entry)
        if errors:
            raise ValueError("Validation failed:\n" + "\n".join(errors))

        target = self._resolve_target_file(pillars)
        self._indicators.append(entry)
        self._file_map[variable_name] = target
        self._rewrite_file(target)

    def remove_indicator(self, variable_name: str):
        for i, entry in enumerate(self._indicators):
            if entry["variable_name"] == variable_name:
                confirm = input(f"Delete '{variable_name}'? This cannot be undone. (y/n): ")
                if confirm.lower() != "y":
                    logger.info("Removal of '%s' cancelled.", variable_name)
                    return
                source_file = self._file_map.pop(variable_name)
                self._indicators.pop(i)
                self._rewrite_file(source_file)
                logger.info("Removed indicator '%s'.", variable_name)
                return
        raise KeyError(f"Indicator '{variable_name}' not found.")

    def edit_indicator(self, variable_name: str, field: str, new_value):
        if field not in EDITABLE_FIELDS:
            raise ValueError(
                f"'{field}' is not an editable indicator field. "
                f"Editable fields: {sorted(EDITABLE_FIELDS)}"
            )

        for entry in self._indicators:
            if entry["variable_name"] == variable_name:
                test = {**entry, field: new_value}
                errors = self._validate_fields(test)
                if errors:
                    raise ValueError("Validation failed:\n" + "\n".join(errors))

                old_file = self._file_map[variable_name]
                entry[field] = new_value

                # if pillars changed, the indicator may belong in a different file
                if field == "pillars":
                    new_file = self._resolve_target_file(new_value)
                    if new_file != old_file:
                        self._file_map[variable_name] = new_file
                        self._rewrite_file(old_file)   # remove from old file
                        self._rewrite_file(new_file)   # add to new file
                        return

                self._rewrite_file(old_file)
                return

        raise KeyError(f"Indicator '{variable_name}' not found.")

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate_fields(self, entry: dict, valid_keys: set | None = None) -> list[str]:
        """
        Validates a single entry. Returns list of error strings.
        Called by add and edit — not a full dataset scan.
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

    def build_pillars(self, indicators: dict[str, Indicator] | None = None) -> dict[str, Pillar]:
        """
        Accepts pre-built indicators dict to avoid reloading yaml.
        If not provided, builds indicators internally.
        """
        if indicators is None:
            indicators = self.build_indicators()

        pillars = {
            key: Pillar(
                key           = key,
                name          = meta["name"],
                justification = meta["justification"],
                weight        = meta["weight"],
            )
            for key, meta in self._pillar_registry.list_pillars().items()
        }

        # O(n) — one pass wiring indicators into pillars
        for indicator in indicators.values():
            for key in indicator.pillars:
                if key in pillars:
                    pillars[key].add_indicator(indicator)

        return pillars


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _weights_sum_to_one(pillars: dict, tolerance: float = 1e-9) -> bool:
    total = sum(p["weight"] for p in pillars.values())
    return abs(total - 1.0) < tolerance
