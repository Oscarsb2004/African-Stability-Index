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

GOALPOSTS_VERSION = 3  # 3: edition 2 (observed only, trimmed outlier rule, theoretical bounds)

#: Decimal places bounds are stored at. Bounds are rounded OUTWARD (min down,
#: max up) rather than to-nearest, so that the very values which defined an
#: extreme still sit inside the stored range. Rounding to nearest pushed those
#: countries a fraction outside their own goalpost and set `clamped` on ~35
#: cells whose true deviation was under 5e-07 — which would have made the flag
#: meaningless for the case it exists to catch: genuinely new extremes in a
#: later edition.
BOUND_DECIMALS = 6


def _round_outward(value: float, *, up: bool) -> float:
    """
    Round a bound away from the data so no defining value falls outside it.

    Returns a plain Python float: numpy scalars cannot be serialised by
    PyYAML, and these values are written to the frozen goalposts file.
    """
    if not np.isfinite(value):
        return float(value)
    scale = 10 ** BOUND_DECIMALS
    rounded = np.ceil(value * scale) if up else np.floor(value * scale)
    return float(rounded / scale)


# ── Transform steps ────────────────────────────────────────────────────────────

def apply_log(values: pd.Series, log_transform: bool, constant: float | None = None) -> pd.Series:
    """
    Log a right-skewed indicator.

    Edition 2 (plan 4.6, Osborne's rule): log(x + c), where the frozen constant c
    makes the indicator's minimum 1, so its log is 0. A later value below that
    minimum logs below 0 and is clamped by the goalposts; one at or below -c
    cannot be logged and is floored at a tiny positive number first.

    Edition 1 (no constant): log1p, with negative values clipped to 0.
    """
    if not log_transform:
        return values.astype(float)
    x = values.astype(float)
    if constant is not None:
        return np.log((x + constant).clip(lower=1e-9))
    if (x.dropna() < 0).any():
        x = x.clip(lower=0)
    return np.log1p(x)


#: The log rule (plan 4.6, the ADA course): log an indicator when its skew is positive and significant, z = skew /
#: SE(skew) above 1.96. The test runs on one value per state, its most recent observation, so n is the number of
#: states reporting, not the thousands of panel cells that would make every skew "significant".
SKEW_Z = 1.96


def skew_test(values) -> tuple[int, float, float, float]:
    """(n, skew, its standard error, z). Skew is the adjusted Fisher-Pearson G1; SE = sqrt(6n(n-1) /
    ((n-2)(n+1)(n+3)))."""
    x = pd.Series(values, dtype=float).dropna().to_numpy()
    n = x.size
    if n < 3 or np.std(x) == 0:
        return n, float("nan"), float("nan"), float("nan")
    g1 = float(pd.Series(x).skew())  # pandas' skew is the adjusted G1
    se = float(np.sqrt(6.0 * n * (n - 1) / ((n - 2) * (n + 1) * (n + 3))))
    return n, g1, se, g1 / se


def winsorize_bounds(values: pd.Series, iqr_multiplier: float) -> tuple[float, float]:
    """Tukey fences at `iqr_multiplier` x IQR. Returns (lower, upper). Edition 1's rule."""
    clean = values.dropna().astype(float)
    if clean.empty:
        return (float("nan"), float("nan"))
    q1, q3 = np.quantile(clean, [0.25, 0.75])
    iqr = q3 - q1
    return (float(q1 - iqr_multiplier * iqr), float(q3 + iqr_multiplier * iqr))


#: The Ibrahim Index's outlier rule (2024 IIAG methodology, "Outliers and treatment", read 2026-10-18): the trimmed
#: mean and standard deviation come from the central 95% of the values; a value more than 3 of those standard
#: deviations from the mean is replaced by the mean plus or minus 3.1 of them.
TRIM, OUTLIER_SD, REPLACE_SD = 0.025, 3.0, 3.1


def trimmed_outlier_bounds(values: pd.Series) -> tuple[float, float, float, float]:
    """(lower, upper, lower_to, upper_to): a value below `lower` becomes `lower_to`, above `upper` becomes
    `upper_to`. Edition 2's rule (plan 4.4)."""
    clean = np.sort(values.dropna().astype(float).to_numpy())
    if clean.size == 0:
        return (float("nan"),) * 4
    lo_q, hi_q = np.quantile(clean, [TRIM, 1 - TRIM])
    core = clean[(clean >= lo_q) & (clean <= hi_q)]
    mean = float(core.mean())
    sd = float(core.std(ddof=1)) if core.size > 1 else 0.0
    return (mean - OUTLIER_SD * sd, mean + OUTLIER_SD * sd, mean - REPLACE_SD * sd, mean + REPLACE_SD * sd)


def cap_outliers(values: pd.Series, lower, upper, lower_to, upper_to) -> pd.Series:
    """Replace values beyond the outlier bounds; leave the rest alone."""
    x = values.astype(float)
    if lower is None or upper is None or not np.isfinite(lower):
        return x
    return x.mask(x < lower, lower_to).mask(x > upper, upper_to)


# ── Computing the frozen bounds ────────────────────────────────────────────────

def compute(
    panel: pd.DataFrame,
    specs: dict[str, dict],
    iqr_multiplier: float,
) -> dict[str, dict]:
    """
    Derive outlier and goalpost bounds for every scoring indicator (edition 2, plan 4.4).

    Uses the whole panel — all countries, all years — so the bounds describe the
    full historical range the index will ever normalise against. Three rules:

    - **Observed values only.** A carried-forward or imputed value repeats or
      guesses a measurement, so it never sets a bound.
    - **Outliers capped first,** by the Ibrahim Index's trimmed rule
      (`trimmed_outlier_bounds`), on the scale the index normalises (after log).
    - **Theoretical bounds win** where the registry gives them (0 to 100 for a
      percentage, 0 to 1 for a parity distance): the goalposts are then those
      bounds, so a score means the same distance from the possible extremes.

    `iqr_multiplier` is kept for the signature; edition 1's Tukey fences are no
    longer used.
    """
    out: dict[str, dict] = {}

    for var, spec in specs.items():
        if spec.get("role", "scoring") != "scoring":
            continue
        sub = panel[(panel["variable_name"] == var) & panel["provenance"].isin(["observed", "derived"])]
        if sub.empty:
            continue

        # the log rule (plan 4.6): each state's most recent observed value, skew test after outlier treatment
        theory = spec.get("theoretical_bounds")
        latest = sub.dropna(subset=["raw_value"]).sort_values("year").groupby("iso3")["raw_value"].last() \
            if {"iso3", "year"} <= set(sub.columns) else sub["raw_value"].dropna()
        lo0, hi0, lo0_to, hi0_to = trimmed_outlier_bounds(latest)
        n_skew, skew, skew_se, skew_z = skew_test(cap_outliers(latest, lo0, hi0, lo0_to, hi0_to))
        log = bool(np.isfinite(skew_z) and skew_z > SKEW_Z)
        base = float(theory[0]) if theory else float(sub["raw_value"].min())
        constant = 1.0 - base if log else None

        logged = apply_log(sub["raw_value"], log, constant)
        lo, hi, lo_to, hi_to = trimmed_outlier_bounds(logged)
        capped = cap_outliers(logged, lo, hi, lo_to, hi_to)
        valid = capped.dropna()
        if valid.empty:
            continue

        if theory:
            gmin, gmax = (float(v) for v in apply_log(pd.Series(theory, dtype=float), log, constant))
        else:
            gmin, gmax = float(valid.min()), float(valid.max())

        finite = np.isfinite(lo)
        out[var] = {
            "log_transform":     log,
            "log_constant":      constant,
            "skew":              None if not np.isfinite(skew) else round(skew, 4),
            "skew_z":            None if not np.isfinite(skew_z) else round(skew_z, 4),
            "skew_n":            int(n_skew),
            "polarity":          spec.get("polarity", "positive"),
            "winsor_lower":      _round_outward(lo, up=False) if finite else None,
            "winsor_upper":      _round_outward(hi, up=True) if finite else None,
            "winsor_lower_to":   _round_outward(lo_to, up=False) if finite else None,
            "winsor_upper_to":   _round_outward(hi_to, up=True) if finite else None,
            "goalpost_min":      gmin if theory else _round_outward(gmin, up=False),
            "goalpost_max":      gmax if theory else _round_outward(gmax, up=True),
            "goalpost_source":   "theoretical" if theory else "observed",
            "n_values":          int(valid.shape[0]),
            "n_capped_low":      int((logged < lo).sum()) if finite else 0,
            "n_capped_high":     int((logged > hi).sum()) if finite else 0,
        }

    return out


def add_new(frozen: dict[str, dict], computed: dict[str, dict]) -> tuple[dict[str, dict], list[str]]:
    """N1: goalposts for indicators the frozen file lacks, without touching any existing indicator's bounds, so
    adding an indicator never re-anchors history. Returns the merged bounds and the names added."""
    added = sorted(set(computed) - set(frozen))
    return {**frozen, **{v: computed[v] for v in added}}, added


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
            f"`python 02_panel.py --freeze-goalposts`, then keep the file under "
            f"version control. Regenerating re-anchors every historical score, so "
            f"it must be a deliberate act: this is why the file is not recreated "
            f"on demand."
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
    "GOALPOSTS_VERSION", "apply_log", "winsorize_bounds", "trimmed_outlier_bounds", "cap_outliers",
    "compute", "add_new", "freeze", "load",
]
