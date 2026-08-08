"""
asi.pipeline.goalposts — fixed normalization bounds, computed once and frozen.

Why this module exists
----------------------
Until Phase B the index min-max normalised against the current sample, so a
country's score moved when *other* countries' data changed, and re-running the
pipeline silently re-anchored every score. That is tolerable for a single
snapshot and fatal for a time slider: a country would appear to improve in a
year when its own numbers were flat and its peers simply got worse.

Fixed goalposts remove that. Bounds are computed once across the whole panel
(every country, every year), written to a versioned file, and thereafter loaded
rather than recomputed. A score then moves only when that country's own data
moves. HDI and ND-GAIN fix their goalposts for the same reason.

Regenerating the file is deliberate and changelogged, never a side effect of a
pipeline run.

Pipeline position
-----------------
    raw -> log1p (if flagged) -> winsorize -> goalpost min-max

Winsorisation bounds are frozen here too, and for the same reason: computing
them per run would let one new outlier reshape every historical score. Log runs
before winsorising so that outliers are capped on the scale the index actually
normalises, instead of being compressed twice.
"""

from __future__ import annotations

import datetime as _dt

import numpy as np
import pandas as pd
import yaml

GOALPOSTS_VERSION = 1


# ── Transform steps ────────────────────────────────────────────────────────────

def apply_log(values: pd.Series, log_transform: bool) -> pd.Series:
    """
    log1p a right-skewed indicator.

    Negative values are clipped to 0 first: log1p is undefined below -1, and an
    indicator flagged for log transform is one whose meaningful range is
    non-negative. Clipping is logged by the caller rather than silently applied
    to data that should not have been flagged.
    """
    if not log_transform:
        return values.astype(float)
    x = values.astype(float)
    if (x.dropna() < 0).any():
        x = x.clip(lower=0)
    return np.log1p(x)


def winsorize_bounds(values: pd.Series, iqr_multiplier: float) -> tuple[float, float]:
    """Tukey fences at `iqr_multiplier` x IQR. Returns (lower, upper)."""
    clean = values.dropna().astype(float)
    if clean.empty:
        return (float("nan"), float("nan"))
    q1, q3 = np.quantile(clean, [0.25, 0.75])
    iqr = q3 - q1
    return (float(q1 - iqr_multiplier * iqr), float(q3 + iqr_multiplier * iqr))


# ── Computing the frozen bounds ────────────────────────────────────────────────

def compute(
    panel: pd.DataFrame,
    specs: dict[str, dict],
    iqr_multiplier: float,
) -> dict[str, dict]:
    """
    Derive winsorisation and goalpost bounds for every scoring indicator.

    Uses the whole panel — all countries, all years — so the bounds describe the
    full historical range the index will ever normalise against.

    Records `min_from_imputed` / `max_from_imputed`: whether an extreme was set
    by a regional-mean estimate rather than a real measurement. A goalpost
    anchored on an imputed value is a manual-review item, so it is recorded
    rather than quietly accepted.
    """
    out: dict[str, dict] = {}

    for var, spec in specs.items():
        if spec.get("role", "scoring") != "scoring":
            continue
        sub = panel[panel["variable_name"] == var]
        if sub.empty:
            continue

        logged = apply_log(sub["raw_value"], bool(spec.get("log_transform", False)))
        lo, hi = winsorize_bounds(logged, iqr_multiplier)
        capped = logged.clip(lower=lo, upper=hi) if np.isfinite(lo) else logged

        valid = capped.dropna()
        if valid.empty:
            continue

        gmin, gmax = float(valid.min()), float(valid.max())

        # was an extreme set by imputed data?
        prov = sub["provenance"].to_numpy()
        capped_arr = capped.to_numpy(dtype=float)
        imputed_mask = np.isin(prov, ["regional_mean", "carried_forward"])
        at_min = np.isclose(capped_arr, gmin, equal_nan=False)
        at_max = np.isclose(capped_arr, gmax, equal_nan=False)

        out[var] = {
            "log_transform":     bool(spec.get("log_transform", False)),
            "polarity":          spec.get("polarity", "positive"),
            "winsor_lower":      round(lo, 6) if np.isfinite(lo) else None,
            "winsor_upper":      round(hi, 6) if np.isfinite(hi) else None,
            "goalpost_min":      round(gmin, 6),
            "goalpost_max":      round(gmax, 6),
            "n_values":          int(valid.shape[0]),
            "n_capped_low":      int((logged < lo).sum()) if np.isfinite(lo) else 0,
            "n_capped_high":     int((logged > hi).sum()) if np.isfinite(hi) else 0,
            "min_from_imputed":  bool((at_min & imputed_mask).any()),
            "max_from_imputed":  bool((at_max & imputed_mask).any()),
        }

    return out


# ── Persistence ────────────────────────────────────────────────────────────────

def freeze(goalposts: dict[str, dict], path, *, panel_years: tuple[int, int],
           note: str = "") -> None:
    """Write the frozen bounds, with the provenance of the run that made them."""
    payload = {
        "version": GOALPOSTS_VERSION,
        "generated": _dt.date.today().isoformat(),
        "panel_years": list(panel_years),
        "note": note or (
            "Fixed goalposts. Regenerate deliberately only: recomputing these "
            "re-anchors every historical score and breaks comparability with "
            "previously published editions."
        ),
        "indicators": dict(sorted(goalposts.items())),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True, width=100)


def load(path) -> dict[str, dict]:
    """Read frozen bounds. Raises if absent — silently recomputing defeats the point."""
    if not path.exists():
        raise FileNotFoundError(
            f"No frozen goalposts at {path}. Generate them once with "
            f"03_normalize.py --freeze-goalposts, then keep the file under version control."
        )
    with open(path, encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}
    if payload.get("version") != GOALPOSTS_VERSION:
        raise ValueError(
            f"Goalposts file version {payload.get('version')} does not match "
            f"expected {GOALPOSTS_VERSION}."
        )
    return payload.get("indicators", {})


__all__ = [
    "GOALPOSTS_VERSION", "apply_log", "winsorize_bounds",
    "compute", "freeze", "load",
]
