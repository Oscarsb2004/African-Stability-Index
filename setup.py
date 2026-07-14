"""
setup.py — Level 1 foundation validation.

Verifies that all models, config, and indicator definitions are correctly
wired before any pipeline module is run. Exit code 0 = all checks passed.
Run with: python setup.py
"""
import sys
import logging

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(levelname)-8s %(message)s",
    stream   = sys.stdout,
)
logger = logging.getLogger(__name__)

PASS = []
FAIL = []


def check(label: str, fn):
    try:
        result = fn()
        if result is False:
            FAIL.append(label)
            logger.error("FAIL  %s", label)
        else:
            PASS.append(label)
            logger.info ("OK    %s", label)
        return result
    except Exception as exc:
        FAIL.append(label)
        logger.error("FAIL  %s — %s: %s", label, type(exc).__name__, exc)
        return None


# ── 1. Directory structure ────────────────────────────────────────────────────

from pathlib import Path

def _check_dirs():
    required = [
        Path("indicators_list"),
        Path("models"),
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing directory: {p.resolve()}")
    return True

check("Directory structure", _check_dirs)


# ── 2. Models importable ──────────────────────────────────────────────────────

def _check_models():
    from models import Indicator, Nation, Pillar, COUNTRIES, build_nations
    assert len(COUNTRIES) == 54, f"Expected 54 countries, got {len(COUNTRIES)}"
    nations = build_nations()
    assert len(nations) == 54
    return True

check("models package imports + 54 countries", _check_models)


# ── 3. Config importable ──────────────────────────────────────────────────────

def _check_config():
    from config import (
        PillarRegistry, IndicatorRegistry,
        WEIGHT_PRESETS, MIN_REGIONAL_SAMPLE,
        COVERAGE_WARN_THRESHOLD, COVERAGE_ALERT_THRESHOLD,
        IQR_MULTIPLIER, VALID_DATABASES,
    )
    # weight presets must sum to 1.0
    for name, weights in WEIGHT_PRESETS.items():
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-9, f"Preset '{name}' weights sum to {total}"
    return True

check("config constants and WEIGHT_PRESETS", _check_config)


# ── 4. Pillar registry ────────────────────────────────────────────────────────

def _check_pillars():
    from config import PillarRegistry
    pr = PillarRegistry()
    keys = pr.valid_keys()
    assert keys == {"A", "B", "C", "D", "E", "F", "G"}, f"Unexpected pillar keys: {keys}"
    for key, meta in pr.list_pillars().items():
        assert "weight_min" in meta, f"Pillar {key} missing weight_min"
        assert "weight_max" in meta, f"Pillar {key} missing weight_max"
    return True

check("PillarRegistry: 7 pillars + weight bounds", _check_pillars)


# ── 5. Indicator registry + validate_all ─────────────────────────────────────

pr_global = None
ir_global = None

def _check_indicators():
    global pr_global, ir_global
    from config import PillarRegistry, IndicatorRegistry
    pr_global = PillarRegistry()
    ir_global = IndicatorRegistry(pr_global)
    n = len(ir_global.list_indicators())
    assert n > 0, "No indicators loaded"
    logger.info("      %d indicators loaded from YAML", n)
    return ir_global.validate_all()

check("IndicatorRegistry: load + validate_all", _check_indicators)


# ── 6. Indicator field completeness ──────────────────────────────────────────

def _check_new_fields():
    if ir_global is None:
        raise RuntimeError("IndicatorRegistry not built — prior check failed")
    missing_db  = []
    missing_log = []
    for ind in ir_global.list_indicators():
        if "database" not in ind:
            missing_db.append(ind["variable_name"])
        if "log_transform" not in ind:
            missing_log.append(ind["variable_name"])
    if missing_db:
        raise ValueError(f"Missing 'database' field on: {missing_db}")
    if missing_log:
        raise ValueError(f"Missing 'log_transform' field on: {missing_log}")
    wgi = [i["variable_name"] for i in ir_global.list_indicators() if i.get("database") == "wgi"]
    wdi = [i["variable_name"] for i in ir_global.list_indicators() if i.get("database") == "wdi"]
    log = [i["variable_name"] for i in ir_global.list_indicators() if i.get("log_transform")]
    logger.info("      WGI indicators (%d): %s", len(wgi), wgi)
    logger.info("      log_transform=True (%d): %s", len(log), log)
    return True

check("All indicators have database + log_transform fields", _check_new_fields)


# ── 7. Build Indicator and Pillar objects ─────────────────────────────────────

def _check_build():
    if ir_global is None:
        raise RuntimeError("IndicatorRegistry not built — prior check failed")
    indicators = ir_global.build_indicators()
    pillars    = ir_global.build_pillars(indicators)
    for key, pillar in pillars.items():
        scoring = pillar.get_scoring_indicators()
        logger.info("      Pillar %s — %d scoring indicator(s)", key, len(scoring))
    # spot-check that Indicator objects carry the new fields correctly
    ind = indicators.get("gdp_pc_ppp")
    if ind is None:
        raise ValueError("gdp_pc_ppp missing from built indicators")
    if ind.database != "wdi":
        raise ValueError(f"gdp_pc_ppp.database expected 'wdi', got '{ind.database}'")
    if ind.log_transform is not True:
        raise ValueError(f"gdp_pc_ppp.log_transform expected True, got {ind.log_transform!r}")

    ind_wgi = indicators.get("va_estimate")
    if ind_wgi is None:
        raise ValueError("va_estimate missing from built indicators")
    if ind_wgi.database != "wgi":
        raise ValueError(f"va_estimate.database expected 'wgi', got '{ind_wgi.database}'")
    if ind_wgi.log_transform is not False:
        raise ValueError(f"va_estimate.log_transform expected False, got {ind_wgi.log_transform!r}")
    return True

check("Build Indicator and Pillar objects", _check_build)


# ── 8. run_config.py ─────────────────────────────────────────────────────────

def _check_run_config():
    import run_config
    from config import WEIGHT_PRESETS
    preset = run_config.WEIGHT_PRESET
    if preset == "custom":
        weights = run_config.CUSTOM_WEIGHTS
    elif preset in WEIGHT_PRESETS:
        weights = WEIGHT_PRESETS[preset]
    else:
        raise ValueError(f"Unknown WEIGHT_PRESET '{preset}' — add it to WEIGHT_PRESETS in config.py")
    total = sum(weights.values())
    assert abs(total - 1.0) < 1e-9, f"Weight preset '{preset}' sums to {total}"
    logger.info("      Active preset: '%s'", preset)
    return True

check("run_config.py: valid preset + weights sum to 1.0", _check_run_config)


# ── Summary ───────────────────────────────────────────────────────────────────

print()
print("=" * 56)
print(f"  Level 1 setup: {len(PASS)} passed, {len(FAIL)} failed")
print("=" * 56)

if FAIL:
    print("\nFailed checks:")
    for label in FAIL:
        print(f"  - {label}")
    sys.exit(1)
else:
    print("\nAll checks passed. Foundation is ready.")
    print("Next step: python 01_pull.py")
    sys.exit(0)
