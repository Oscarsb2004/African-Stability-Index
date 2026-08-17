"""
The five indicator paths `verify/panel.py` cannot re-derive, under test.

`check_panel_values` compares the panel against a `merge_asof` join, which only
works for indicators taken as-is. It therefore skips `displaced_persons`,
`gdp_growth_3yr_avg`, `inflation_5yr_avg`, `primary_gpi` and `secondary_gpi` —
5 of 32 scoring indicators, 6,750 of 43,200 cells. That is 15.6% of the panel
and very close to 100% of its difficulty: everything the re-derivation covers is
carry-forward, and everything it skips is arithmetic that can be wrong quietly.

Two failures are singled out because they produce plausible numbers rather than
errors:

  - a GPI folded monotonically instead of onto distance-from-parity rewards male
    educational disadvantage as though it were progress. This index did that
    until 2026. The panel looks entirely normal either way.
  - an IDP count with no population to divide by is ABSENT, not carried forward.
    Left as CARRIED_FORWARD it would keep a raw head-count in a per-capita
    column — a number roughly six orders of magnitude too large, sitting in a
    field whose units nobody re-reads.
"""

import numpy as np
import pandas as pd
import pytest

from asi.core.constants import MIN_REGIONAL_SAMPLE
from asi.core.schema import Provenance, WindowMode
from asi.pipeline.panel import (
    PANEL_COLUMNS,
    apply_derived,
    distance_from_parity,
    regional_fill,
    window_value,
)


def _panel(rows) -> pd.DataFrame:
    """Rows as (iso3, variable_name, year, raw_value, provenance, source_year)."""
    return pd.DataFrame(rows, columns=PANEL_COLUMNS)


# ── distance_from_parity ───────────────────────────────────────────────────────

def test_equal_departures_from_parity_score_the_same():
    """
    The whole point of the fold. 0.8 (girls behind) and 1.2 (boys behind) are the
    same distance from parity and must produce the same number.
    """
    assert distance_from_parity(0.8) == pytest.approx(distance_from_parity(1.2))
    assert distance_from_parity(0.8) == pytest.approx(0.8)


def test_parity_itself_is_the_maximum():
    assert distance_from_parity(1.0) == pytest.approx(1.0)
    for v in (0.5, 0.9, 1.1, 1.5):
        assert distance_from_parity(v) < distance_from_parity(1.0)


def test_the_fold_is_not_monotonic_in_the_raw_ratio():
    """
    The regression this transform exists for. Scoring GPI monotonically — the
    index's behaviour before 2026 — makes 1.4 outrank 1.0, which reads a country
    where boys are far behind as more equitable than one at parity.
    """
    assert distance_from_parity(1.4) < distance_from_parity(1.0)
    assert distance_from_parity(1.4) == pytest.approx(distance_from_parity(0.6))


def test_missing_stays_missing():
    assert distance_from_parity(None) is None
    assert distance_from_parity(float("nan")) is None


# ── apply_derived: the GPI transform in place ──────────────────────────────────

GPI_SPECS = {"primary_gpi": {"aggregation": "most_recent",
                             "transform": "distance_from_parity"}}


def test_the_registry_flag_is_what_triggers_the_transform():
    panel = _panel([("KEN", "primary_gpi", 2020, 1.2, "observed", 2020)])
    out, notes = apply_derived(panel, GPI_SPECS)
    assert out["raw_value"].iloc[0] == pytest.approx(0.8)
    assert any("distance_from_parity" in n for n in notes)


def test_an_indicator_without_the_flag_is_left_alone():
    panel = _panel([("KEN", "primary_gpi", 2020, 1.2, "observed", 2020)])
    out, _ = apply_derived(panel, {"primary_gpi": {"aggregation": "most_recent"}})
    assert out["raw_value"].iloc[0] == pytest.approx(1.2)


def test_an_unknown_transform_raises_rather_than_passing_the_value_through():
    """
    A typo in the registry must not silently publish untransformed values. The
    quiet version of this failure is indistinguishable from correct output.
    """
    panel = _panel([("KEN", "primary_gpi", 2020, 1.2, "observed", 2020)])
    with pytest.raises(ValueError, match="unknown transform"):
        apply_derived(panel, {"primary_gpi": {"transform": "sqrt"}})


# ── apply_derived: IDP per capita ──────────────────────────────────────────────

IDP_SPECS = {"displaced_persons": {"aggregation": "most_recent"},
             "population_total": {"aggregation": "most_recent"}}


def test_idp_is_converted_to_a_rate_per_thousand():
    panel = _panel([
        ("KEN", "displaced_persons", 2020, 50_000.0, "observed", 2020),
        ("KEN", "population_total", 2020, 50_000_000.0, "observed", 2020),
    ])
    out, _ = apply_derived(panel, IDP_SPECS)
    idp = out[out["variable_name"] == "displaced_persons"].iloc[0]
    assert idp["raw_value"] == pytest.approx(1.0)          # 50k / 50M x 1000


def test_population_is_left_as_it_was_because_it_is_the_denominator():
    panel = _panel([
        ("KEN", "displaced_persons", 2020, 50_000.0, "observed", 2020),
        ("KEN", "population_total", 2020, 50_000_000.0, "observed", 2020),
    ])
    out, _ = apply_derived(panel, IDP_SPECS)
    pop = out[out["variable_name"] == "population_total"].iloc[0]
    assert pop["raw_value"] == pytest.approx(50_000_000.0)


def test_an_idp_count_with_no_population_becomes_absent_and_clears_source_year():
    """
    The case the backlog names. A displacement count that could not be divided is
    not a carried-forward measurement of anything — it is a raw head-count in a
    per-thousand column, off by six orders of magnitude, and `source_year` would
    still point at a real year and make it look sourced.
    """
    panel = _panel([
        ("KEN", "displaced_persons", 2020, 50_000.0, "carried_forward", 2018),
        ("KEN", "population_total", 2020, np.nan, "absent", None),
    ])
    out, _ = apply_derived(panel, IDP_SPECS)
    idp = out[out["variable_name"] == "displaced_persons"].iloc[0]
    assert pd.isna(idp["raw_value"])
    assert idp["provenance"] == Provenance.ABSENT.value
    assert pd.isna(idp["source_year"])


def test_a_population_of_zero_is_refused_rather_than_dividing_by_it():
    panel = _panel([
        ("KEN", "displaced_persons", 2020, 50_000.0, "observed", 2020),
        ("KEN", "population_total", 2020, 0.0, "observed", 2020),
    ])
    out, _ = apply_derived(panel, IDP_SPECS)
    idp = out[out["variable_name"] == "displaced_persons"].iloc[0]
    assert pd.isna(idp["raw_value"])
    assert idp["provenance"] == Provenance.ABSENT.value


def test_each_country_year_uses_its_own_population():
    """A pivot keyed on one column would cross-contaminate countries or years."""
    panel = _panel([
        ("KEN", "displaced_persons", 2020, 10_000.0, "observed", 2020),
        ("KEN", "population_total", 2020, 10_000_000.0, "observed", 2020),
        ("UGA", "displaced_persons", 2020, 10_000.0, "observed", 2020),
        ("UGA", "population_total", 2020, 50_000_000.0, "observed", 2020),
        ("KEN", "displaced_persons", 2021, 10_000.0, "observed", 2021),
        ("KEN", "population_total", 2021, 20_000_000.0, "observed", 2021),
    ])
    out, _ = apply_derived(panel, IDP_SPECS)
    idp = out[out["variable_name"] == "displaced_persons"].set_index(["iso3", "year"])
    assert idp.loc[("KEN", 2020), "raw_value"] == pytest.approx(1.0)
    assert idp.loc[("UGA", 2020), "raw_value"] == pytest.approx(0.2)
    assert idp.loc[("KEN", 2021), "raw_value"] == pytest.approx(0.5)


def test_the_conversion_is_skipped_when_population_is_not_in_the_registry():
    """Without a denominator indicator there is nothing to divide by."""
    panel = _panel([("KEN", "displaced_persons", 2020, 50_000.0, "observed", 2020)])
    out, _ = apply_derived(panel, {"displaced_persons": {"aggregation": "most_recent"}})
    assert out["raw_value"].iloc[0] == pytest.approx(50_000.0)


# ── rolling means (gdp_growth_3yr_avg, inflation_5yr_avg) ──────────────────────

def test_a_rolling_mean_averages_only_the_years_inside_its_window():
    """
    Three-year window at 2020 covers 2018-2020. A 2017 measurement is outside it
    and must not be averaged in, however close to the edge it sits.
    """
    obs = {2017: 100.0, 2018: 1.0, 2019: 2.0, 2020: 3.0}
    value, prov, src = window_value(obs, 2020, WindowMode.ROLLING_MEAN, 3, 5)
    assert value == pytest.approx(2.0)
    assert prov is Provenance.OBSERVED
    assert src == 2020


def test_a_rolling_mean_averages_what_is_there_not_what_is_missing():
    """
    Gaps inside the window shrink the sample; they are not treated as zeros. Two
    of three years present gives their mean, not their sum over three.
    """
    value, _, _ = window_value({2018: 2.0, 2020: 4.0}, 2020,
                               WindowMode.ROLLING_MEAN, 3, 5)
    assert value == pytest.approx(3.0)
    assert value != pytest.approx(6.0 / 3)


def test_a_rolling_mean_over_a_stale_window_carries_the_last_value_forward():
    """
    Nothing inside the window but a usable recent measurement exists: the value
    is that measurement, and the provenance says carried forward rather than
    claiming a mean of years that were never observed.
    """
    value, prov, src = window_value({2016: 7.0}, 2020,
                                    WindowMode.ROLLING_MEAN, 3, 5)
    assert value == pytest.approx(7.0)
    assert prov is Provenance.CARRIED_FORWARD
    assert src == 2016


def test_a_window_of_zero_years_means_everything_up_to_now():
    value, _, _ = window_value({2000: 1.0, 2010: 2.0, 2020: 3.0}, 2020,
                               WindowMode.ROLLING_MEAN, 0, 5)
    assert value == pytest.approx(2.0)


def test_a_rolling_mean_never_looks_forward():
    """A 2021 measurement cannot inform the 2020 cell."""
    value, _, _ = window_value({2019: 1.0, 2020: 2.0, 2021: 100.0}, 2020,
                               WindowMode.ROLLING_MEAN, 3, 5)
    assert value == pytest.approx(1.5)


def test_a_rolling_mean_expires_with_everything_else():
    value, prov, src = window_value({2010: 5.0}, 2020,
                                    WindowMode.ROLLING_MEAN, 3, 5)
    assert value is None
    assert prov is Provenance.ABSENT
    assert src is None


# ── regional_fill ──────────────────────────────────────────────────────────────

REGIONS = {"AAA": "East", "BBB": "East", "CCC": "East", "DDD": "East",
           "ZZZ": "West"}


def _fill_rows(present: dict[str, float], missing: str, year: int = 2020):
    rows = [(iso3, "gdp_pc", year, v, "observed", year)
            for iso3, v in present.items()]
    rows.append((missing, "gdp_pc", year, np.nan, "absent", None))
    return _panel(rows)


def test_a_gap_is_filled_from_the_regional_mean_of_that_year():
    panel = _fill_rows({"AAA": 10.0, "BBB": 20.0, "CCC": 30.0}, "DDD")
    out, n = regional_fill(panel, REGIONS, MIN_REGIONAL_SAMPLE)
    filled = out[out["iso3"] == "DDD"].iloc[0]
    assert n == 1
    assert filled["raw_value"] == pytest.approx(20.0)
    assert filled["provenance"] == Provenance.REGIONAL_MEAN.value


def test_a_filled_cell_carries_no_source_year():
    """An imputed value came from no particular year, and must not claim one."""
    panel = _fill_rows({"AAA": 10.0, "BBB": 20.0, "CCC": 30.0}, "DDD")
    out, _ = regional_fill(panel, REGIONS, MIN_REGIONAL_SAMPLE)
    assert pd.isna(out[out["iso3"] == "DDD"].iloc[0]["source_year"])


def test_too_few_peers_leaves_the_gap_empty():
    """
    One neighbour is not a regional mean. The threshold is the difference between
    an estimate and a guess dressed as one.
    """
    panel = _fill_rows({"AAA": 10.0, "BBB": 20.0}, "DDD")
    out, n = regional_fill(panel, REGIONS, MIN_REGIONAL_SAMPLE)
    assert n == 0
    assert pd.isna(out[out["iso3"] == "DDD"].iloc[0]["raw_value"])
    assert out[out["iso3"] == "DDD"].iloc[0]["provenance"] == "absent"


def test_the_threshold_is_inclusive_at_exactly_min_regional_sample():
    """Boundary pinned: three donors with MIN_REGIONAL_SAMPLE == 3 must fill."""
    donors = {n: 10.0 for n in list(REGIONS)[:MIN_REGIONAL_SAMPLE]}
    panel = _fill_rows(donors, "DDD")
    _, n = regional_fill(panel, REGIONS, MIN_REGIONAL_SAMPLE)
    assert n == 1

    one_short = dict(list(donors.items())[:MIN_REGIONAL_SAMPLE - 1])
    _, n = regional_fill(_fill_rows(one_short, "DDD"), REGIONS, MIN_REGIONAL_SAMPLE)
    assert n == 0


def test_another_region_is_not_a_donor():
    panel = _panel([
        ("ZZZ", "gdp_pc", 2020, 999.0, "observed", 2020),
        ("AAA", "gdp_pc", 2020, 10.0, "observed", 2020),
        ("BBB", "gdp_pc", 2020, 20.0, "observed", 2020),
        ("DDD", "gdp_pc", 2020, np.nan, "absent", None),
    ])
    out, n = regional_fill(panel, REGIONS, MIN_REGIONAL_SAMPLE)
    assert n == 0, "a West-region value must not fill an East-region gap"
    assert pd.isna(out[out["iso3"] == "DDD"].iloc[0]["raw_value"])


def test_another_year_is_not_a_donor():
    """
    Filling is per year, never across years. A region's 2019 values say nothing
    about a country's 2020 gap, and averaging across time would smuggle a second
    kind of carry-forward past the expiry rule.
    """
    panel = _panel([
        ("AAA", "gdp_pc", 2019, 10.0, "observed", 2019),
        ("BBB", "gdp_pc", 2019, 20.0, "observed", 2019),
        ("CCC", "gdp_pc", 2019, 30.0, "observed", 2019),
        ("DDD", "gdp_pc", 2020, np.nan, "absent", None),
    ])
    out, n = regional_fill(panel, REGIONS, MIN_REGIONAL_SAMPLE)
    assert n == 0
    assert pd.isna(out[out["iso3"] == "DDD"].iloc[0]["raw_value"])


def test_a_measured_value_is_never_overwritten():
    panel = _panel([
        ("AAA", "gdp_pc", 2020, 10.0, "observed", 2020),
        ("BBB", "gdp_pc", 2020, 20.0, "observed", 2020),
        ("CCC", "gdp_pc", 2020, 30.0, "observed", 2020),
        ("DDD", "gdp_pc", 2020, 1.0, "observed", 2020),
    ])
    out, n = regional_fill(panel, REGIONS, MIN_REGIONAL_SAMPLE)
    assert n == 0
    assert out[out["iso3"] == "DDD"].iloc[0]["raw_value"] == pytest.approx(1.0)


def test_an_imputed_cell_does_not_become_a_donor_for_another_gap():
    """
    Donors are drawn from cells that already have values when the fill starts, so
    one imputed country cannot prop up the next. Otherwise a region with three
    reporting members could cascade to fill an unlimited number of gaps, each
    inheriting confidence it never had.
    """
    panel = _panel([
        ("AAA", "gdp_pc", 2020, 10.0, "observed", 2020),
        ("BBB", "gdp_pc", 2020, 20.0, "observed", 2020),
        ("CCC", "gdp_pc", 2020, np.nan, "absent", None),
        ("DDD", "gdp_pc", 2020, np.nan, "absent", None),
    ])
    out, n = regional_fill(panel, REGIONS, MIN_REGIONAL_SAMPLE)
    assert n == 0, "two donors is below the threshold; neither gap may fill"
    assert out["raw_value"].isna().sum() == 2


def test_the_helper_column_is_not_left_behind():
    """`_region` is scratch. Leaking it would change the panel's schema."""
    panel = _fill_rows({"AAA": 10.0, "BBB": 20.0, "CCC": 30.0}, "DDD")
    out, _ = regional_fill(panel, REGIONS, MIN_REGIONAL_SAMPLE)
    assert list(out.columns) == PANEL_COLUMNS
