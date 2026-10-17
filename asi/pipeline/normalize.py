"""
asi.pipeline.normalize — map panel values onto 0-100 using frozen goalposts.

    transformed = log1p(raw) if flagged
    capped      = clip(transformed, winsor_lower, winsor_upper)
    score       = 100 * (capped - gmin) / (gmax - gmin)          [positive polarity]
                = 100 * (gmax - capped) / (gmax - gmin)          [negative polarity]

Bounds come from asi.pipeline.goalposts and are read, never recomputed here.
Because they are fixed, a value can legitimately fall outside them — a country
that sets a new low in a later edition, for instance. Such values are clamped
into [0, 100] and flagged `clamped=True` rather than being allowed to push the
scale around, which is exactly what fixed goalposts exist to prevent.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from asi.core.schema import Polarity
from asi.pipeline.goalposts import apply_log


def normalize_value(
    capped: float | None,
    goalpost_min: float,
    goalpost_max: float,
    polarity: str | Polarity,
) -> tuple[float | None, bool]:
    """
    Map one value onto 0-100. Returns (score, clamped).

    A zero-width goalpost range means the indicator never varies across the
    whole panel; every country scores 50 rather than dividing by zero. Such an
    indicator carries no comparative information and should be reviewed.
    """
    if capped is None or (isinstance(capped, float) and np.isnan(capped)):
        return None, False

    span = goalpost_max - goalpost_min
    if span <= 0:
        return 50.0, False

    pol = polarity.value if isinstance(polarity, Polarity) else str(polarity)
    if pol == "negative":
        raw_score = (goalpost_max - capped) / span * 100.0
    else:
        raw_score = (capped - goalpost_min) / span * 100.0

    clamped = raw_score < 0.0 or raw_score > 100.0
    return float(min(100.0, max(0.0, raw_score))), clamped


def normalize_panel(
    panel: pd.DataFrame,
    goalposts: dict[str, dict],
) -> tuple[pd.DataFrame, list[str]]:
    """
    Add `transformed_value`, `score`, and `clamped` columns to the panel.

    Indicators absent from the goalposts file are left unscored: that means
    either a descriptive indicator (correct — it is a denominator, not a score)
    or a registry change made after the goalposts were frozen (a real problem,
    reported in the returned notes).
    """
    panel = panel.copy()
    panel["transformed_value"] = np.nan
    panel["score"] = np.nan
    panel["clamped"] = False

    notes: list[str] = []

    for var, bounds in goalposts.items():
        mask = (panel["variable_name"] == var).to_numpy()
        if not mask.any():
            notes.append(f"{var}: in goalposts file but absent from the panel")
            continue

        values = panel.loc[mask, "raw_value"]
        transformed = apply_log(values, bool(bounds.get("log_transform", False)))

        lo, hi = bounds.get("winsor_lower"), bounds.get("winsor_upper")
        if lo is not None and hi is not None:
            transformed = transformed.clip(lower=lo, upper=hi)

        gmin = float(bounds["goalpost_min"])
        gmax = float(bounds["goalpost_max"])
        polarity = bounds.get("polarity", "positive")

        results = [normalize_value(v, gmin, gmax, polarity) for v in transformed]
        # pandas 3 refuses to place None into a float column, so missing scores
        # are converted to NaN explicitly rather than relying on coercion.
        scores = np.array(
            [np.nan if r[0] is None else r[0] for r in results], dtype=float
        )
        panel.loc[mask, "transformed_value"] = transformed.to_numpy()
        panel.loc[mask, "score"] = scores
        panel.loc[mask, "clamped"] = np.array([bool(r[1]) for r in results])

        n_clamped = sum(1 for r in results if r[1])
        if n_clamped:
            notes.append(
                f"{var}: {n_clamped} values fell outside the frozen goalposts and "
                f"were clamped into [0, 100]"
            )

    scored_vars = set(goalposts)
    panel_vars = set(panel["variable_name"].unique())
    unscored = sorted(panel_vars - scored_vars)
    if unscored:
        notes.append(
            f"not scored (no goalposts): {unscored} — expected for descriptive "
            f"indicators, otherwise the goalposts file is out of date"
        )

    return panel, notes


__all__ = ["normalize_value", "normalize_panel"]
