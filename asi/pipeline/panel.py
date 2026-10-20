"""
asi.pipeline.panel — turn raw observations into a dense yearly panel.

The pre-Phase-B pipeline collapsed each series to one number per country. The
panel keeps the time dimension: for every (country, indicator, year) in the
panel range it produces a value AND a provenance saying how that value came to
exist. Provenance is what later lets the interface grey out a pillar-year that
is mostly inference rather than measurement.

Order of operations, and why:

    1. window        derive each year's value from observations at or before it
    2. derived       transforms that need more than one indicator, or that
                     reshape an indicator's meaning (IDP per capita, GPI parity)

A gap stays a gap: edition 1's regional fill is not carried over (plan 4.5, P105).

Every function here is pure: it takes data and settings and returns data. File
I/O belongs to the stage script that calls them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from asi.core.schema import Provenance, WindowMode, window_for

#: Columns of the panel this module produces.
PANEL_COLUMNS = [
    "iso3", "variable_name", "year",
    "raw_value", "provenance", "source_year",
]


# ── One country-indicator-year ─────────────────────────────────────────────────

def window_value(
    observations: dict[int, float],
    year: int,
    mode: WindowMode,
    window_years: int,
    max_carry_forward: int,
) -> tuple[float | None, Provenance, int | None]:
    """
    Derive the value for `year` from a country's observations of one indicator.

    `observations` maps year -> real measured value (no imputed entries).

    Returns (value, provenance, source_year).

    Rules:
      - a measurement at `year` itself is OBSERVED
      - an older measurement, still within `max_carry_forward` years, is
        CARRIED_FORWARD and records the year it actually came from
      - anything staler than that is ABSENT: a fifteen-year-old number is not
        evidence about this year, and pretending otherwise is what the
        reliability tiers exist to prevent
      - ROLLING_MEAN averages the real measurements inside the trailing window;
        provenance still reflects whether `year` itself was measured
    """
    if not observations:
        return None, Provenance.ABSENT, None

    prior = [y for y in observations if y <= year]
    if not prior:
        return None, Provenance.ABSENT, None

    latest = max(prior)
    staleness = year - latest
    if staleness > max_carry_forward:
        return None, Provenance.ABSENT, None

    provenance = Provenance.OBSERVED if staleness == 0 else Provenance.CARRIED_FORWARD

    if mode is WindowMode.ROLLING_MEAN:
        # window_years == 0 means "every year available up to now"
        start = year - window_years + 1 if window_years > 0 else min(prior)
        in_window = [observations[y] for y in prior if y >= start]
        if in_window:
            return float(np.mean(in_window)), provenance, latest
        # nothing inside the window, but a usable recent value exists
        return float(observations[latest]), Provenance.CARRIED_FORWARD, latest

    if mode is WindowMode.ROLLING_SD:
        # volatility: the sample standard deviation of the real measurements in
        # the trailing window, and only when at least half the window was measured;
        # a spread of two or three numbers says little about a decade
        start = year - window_years + 1
        in_window = [observations[y] for y in prior if y >= start]
        if len(in_window) < max(2, window_years // 2):
            return None, Provenance.ABSENT, None
        return float(np.std(in_window, ddof=1)), provenance, latest

    if mode is WindowMode.POINT:
        if staleness != 0:
            return None, Provenance.ABSENT, None
        return float(observations[year]), Provenance.OBSERVED, year

    # MOST_RECENT
    return float(observations[latest]), provenance, latest


# ── Build the panel ────────────────────────────────────────────────────────────

def build_panel(
    raw: pd.DataFrame,
    specs: dict[str, dict],
    iso3_list: list[str],
    years: range,
    default_max_carry_forward: int,
) -> pd.DataFrame:
    """
    Expand long raw observations into a dense panel.

    `raw` needs columns: iso3, variable_name, year, value.
    `specs` maps variable_name -> registry entry (needs `aggregation`; may carry
    `max_carry_forward`).

    The result has one row per (country, indicator, year) — including rows with
    no value, because "we have nothing here" is information the reliability
    tiers depend on.
    """
    raw = raw.copy()
    raw["year"] = pd.to_numeric(raw["year"], errors="coerce")
    raw = raw.dropna(subset=["year", "value"])
    raw["year"] = raw["year"].astype(int)

    # variable -> iso3 -> {year: value}
    lookup: dict[str, dict[str, dict[int, float]]] = {}
    for (var, iso3), grp in raw.groupby(["variable_name", "iso3"], sort=False):
        lookup.setdefault(var, {})[iso3] = dict(
            zip(grp["year"].tolist(), grp["value"].astype(float).tolist())
        )

    rows = []
    for var, spec in specs.items():
        mode, window_years = window_for(spec["aggregation"])
        max_carry = int(spec.get("max_carry_forward", default_max_carry_forward))
        per_country = lookup.get(var, {})
        for iso3 in iso3_list:
            observations = per_country.get(iso3, {})
            for year in years:
                value, provenance, source_year = window_value(
                    observations, year, mode, window_years, max_carry
                )
                rows.append((iso3, var, year, value, provenance.value, source_year))

    return pd.DataFrame(rows, columns=PANEL_COLUMNS)


# ── Derived transforms ─────────────────────────────────────────────────────────

def distance_from_parity(value: float | None) -> float | None:
    """
    Fold a parity ratio onto "distance from 1.0", keeping higher = better.

        min(x, 2 - x)

    A Gender Parity Index of 1.0 is the ideal; 0.8 (girls behind) and 1.2 (boys
    behind) are both departures from it and must score the same. Scoring GPI
    monotonically — as this index did before 2026 — rewards male disadvantage as
    though it were progress.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    return float(min(value, 2.0 - value))


def apply_derived(
    panel: pd.DataFrame,
    specs: dict[str, dict],
    *,
    population_var: str = "population_total",
) -> tuple[pd.DataFrame, list[str]]:
    """
    Apply transforms that reshape an indicator's meaning.

    Two kinds, both declared in the registry:
      - `transform: distance_from_parity` on the GPI indicators
      - `per_capita: <scale>`, a count divided by the same country-year's
        population and multiplied by the scale (100,000 for deaths and
        displacement). It needs a second indicator as its denominator, so it
        cannot be a single-column transform.

    Returns the panel and a list of human-readable notes for the run log.
    """
    panel = panel.copy()
    notes: list[str] = []

    # 1. single-column transforms declared in the registry
    for var, spec in specs.items():
        transform = spec.get("transform")
        if not transform:
            continue
        mask = panel["variable_name"] == var
        if transform == "distance_from_parity":
            panel.loc[mask, "raw_value"] = panel.loc[mask, "raw_value"].map(
                distance_from_parity
            )
            n = int(mask.sum())
            notes.append(f"{var}: distance_from_parity applied to {n} panel cells")
        else:
            raise ValueError(f"{var}: unknown transform {transform!r}")

    # 2. per capita — needs population as denominator
    rates = {var: float(spec["per_capita"]) for var, spec in specs.items() if spec.get("per_capita")}
    if rates and population_var not in specs:
        raise ValueError(f"{sorted(rates)} are per capita, but {population_var} is not in the registry")
    if rates:
        # dropna=False is load-bearing. pivot_table's default omits any column
        # whose entries are all NaN, so a population series that failed to pull
        # for the entire panel would vanish from `wide`, and the conversion would
        # be skipped in silence — leaving raw head-counts sitting in a per-capita
        # column, orders of magnitude too large, still marked carried_forward.
        # A missing denominator column is therefore an error, not a skip.
        wide = panel.pivot_table(
            index=["iso3", "year"], columns="variable_name",
            values="raw_value", aggfunc="first", dropna=False,
        )
        if population_var not in wide.columns:
            raise ValueError(f"{population_var} has no panel cells to divide by")
        pop = wide[population_var]
        idx = panel.set_index(["iso3", "year"]).index
        for var, scale in rates.items():
            if var not in wide.columns:
                continue
            count = wide[var]
            converted = np.where(count.notna() & pop.notna() & (pop > 0), count / pop * scale, np.nan)
            mapped = pd.Series(converted, index=wide.index).reindex(idx).to_numpy()
            is_var = (panel["variable_name"] == var).to_numpy()
            had = is_var & panel["raw_value"].notna().to_numpy()
            panel.loc[is_var, "raw_value"] = mapped[is_var]

            # a value that needed a denominator we did not have is not "carried
            # forward", it is absent
            lost = is_var & pd.isna(panel["raw_value"]).to_numpy()
            panel.loc[lost, "provenance"] = Provenance.ABSENT.value
            panel.loc[lost, "source_year"] = None

            n_ok = int((is_var & ~pd.isna(panel["raw_value"]).to_numpy()).sum())
            notes.append(f"{var}: converted to per {scale:,.0f} population ({n_ok} cells); "
                         f"{int((had & lost).sum())} counts dropped for want of population")
        # population_total is descriptive: it stays in the panel as a denominator
        # and is filtered out of scoring by role, not by deletion.

    return panel, notes


__all__ = [
    "PANEL_COLUMNS", "window_value", "build_panel",
    "distance_from_parity", "apply_derived",
]
