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
    3. regional fill impute what is still missing from regional peers

Derived transforms run BEFORE the regional fill so that peers are averaged on
the final quantity. Averaging absolute IDP counts across a region would track
the peers' population sizes rather than their displacement rates.

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
    idp_var: str = "displaced_persons",
    population_var: str = "population_total",
    per_capita_scale: float = 1000.0,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Apply transforms that reshape an indicator's meaning.

    Two kinds, both flagged in the registry rather than hardcoded by name where
    possible:
      - `transform: distance_from_parity` on the GPI indicators
      - the IDP per-capita conversion, which needs a second indicator as its
        denominator and so cannot be expressed as a single-column transform

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

    # 2. IDP per capita — needs population as denominator
    if idp_var in specs and population_var in specs:
        # dropna=False is load-bearing. pivot_table's default omits any column
        # whose entries are all NaN, so a population series that failed to pull
        # for the entire panel would vanish from `wide`, the guard below would
        # find no denominator, and the conversion would be skipped in silence —
        # leaving raw head-counts sitting in a per-thousand column, six orders of
        # magnitude too large, still marked carried_forward. Absent for one
        # country-year already behaved correctly; absent for all of them did not.
        wide = panel.pivot_table(
            index=["iso3", "year"], columns="variable_name",
            values="raw_value", aggfunc="first", dropna=False,
        )
        if idp_var in wide.columns and population_var in wide.columns:
            pop = wide[population_var]
            idp = wide[idp_var]
            converted = np.where(
                idp.notna() & pop.notna() & (pop > 0),
                idp / pop * per_capita_scale,
                np.nan,
            )
            new = pd.Series(converted, index=wide.index)

            idx = panel.set_index(["iso3", "year"]).index
            is_idp = (panel["variable_name"] == idp_var).to_numpy()
            mapped = new.reindex(idx).to_numpy()
            panel.loc[is_idp, "raw_value"] = mapped[is_idp]

            # a value that needed a denominator we did not have is not "carried
            # forward", it is absent
            lost = is_idp & pd.isna(panel["raw_value"]).to_numpy()
            panel.loc[lost, "provenance"] = Provenance.ABSENT.value
            panel.loc[lost, "source_year"] = None

            n_ok = int((is_idp & ~pd.isna(panel["raw_value"]).to_numpy()).sum())
            notes.append(
                f"{idp_var}: converted to per {per_capita_scale:.0f} population "
                f"({n_ok} cells); {int(lost.sum())} cells dropped for want of population"
            )
        # population_total is descriptive: it stays in the panel as a denominator
        # and is filtered out of scoring by role, not by deletion.

    return panel, notes


# ── Regional imputation ────────────────────────────────────────────────────────

def regional_fill(
    panel: pd.DataFrame,
    iso3_to_region: dict[str, str],
    min_sample: int,
) -> tuple[pd.DataFrame, int]:
    """
    Fill gaps from regional peers, within the same year.

    Filling is per year, never across years: a country's 2003 gap is estimated
    from its region in 2003, not from the region's whole history. A region with
    fewer than `min_sample` peers reporting that year is left empty rather than
    imputed from one or two neighbours.

    Filled cells are marked REGIONAL_MEAN, which the reliability tiers treat as
    inference, not measurement.
    """
    panel = panel.copy()
    panel["_region"] = panel["iso3"].map(iso3_to_region)

    missing = panel["raw_value"].isna()
    n_filled = 0

    donors = (
        panel.loc[~missing]
        .groupby(["variable_name", "year", "_region"])["raw_value"]
        .agg(["mean", "size"])
    )
    eligible = donors[donors["size"] >= min_sample]["mean"]

    if not eligible.empty:
        keys = pd.MultiIndex.from_arrays([
            panel["variable_name"], panel["year"], panel["_region"],
        ])
        candidate = eligible.reindex(keys).to_numpy()
        fillable = missing.to_numpy() & ~pd.isna(candidate)
        panel.loc[fillable, "raw_value"] = candidate[fillable]
        panel.loc[fillable, "provenance"] = Provenance.REGIONAL_MEAN.value
        panel.loc[fillable, "source_year"] = None
        n_filled = int(fillable.sum())

    return panel.drop(columns=["_region"]), n_filled


__all__ = [
    "PANEL_COLUMNS", "window_value", "build_panel",
    "distance_from_parity", "apply_derived", "regional_fill",
]
