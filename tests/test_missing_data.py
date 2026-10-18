"""Edition 2, step 2 (plan 4.5): no regional fill in the published scores; a quantile fill only as the sensitivity
run. Invented panel; each rule has a negative control."""

import pandas as pd

from asi.pipeline import panel as panel_mod


def toy():
    rows = [("A1", "x", 2020, 10.0), ("A2", "x", 2020, 20.0), ("A3", "x", 2020, 30.0), ("A4", "x", 2020, 40.0),
            ("A5", "x", 2020, None), ("B1", "x", 2020, None)]
    p = pd.DataFrame(rows, columns=["iso3", "variable_name", "year", "raw_value"])
    p["provenance"] = ["observed"] * 4 + ["absent"] * 2
    p["source_year"] = None
    return p, {"A1": "A", "A2": "A", "A3": "A", "A4": "A", "A5": "A", "B1": "B"}


def test_a_quantile_fill_uses_the_regions_quantile_and_says_so():
    p, regions = toy()
    out, n = panel_mod.regional_fill(p, regions, min_sample=3, statistic=0.25)
    a5 = out[out["iso3"] == "A5"].iloc[0]
    assert n == 1 and a5["raw_value"] == 17.5  # the 25th percentile of 10, 20, 30, 40
    assert a5["provenance"] == "regional_quantile"
    assert pd.isna(out[out["iso3"] == "B1"].iloc[0]["raw_value"])  # a region without enough peers stays empty


def test_the_mean_fill_of_edition_1_is_still_available_and_labelled():
    p, regions = toy()
    out, _ = panel_mod.regional_fill(p, regions, min_sample=3)
    a5 = out[out["iso3"] == "A5"].iloc[0]
    assert (a5["raw_value"], a5["provenance"]) == (25.0, "regional_mean")  # negative control: not the quantile


def test_the_published_panel_has_no_regional_fill():
    panel = pd.read_csv("data/panel/observations.csv", usecols=["provenance"])
    assert not panel["provenance"].isin(["regional_mean", "regional_quantile"]).any()
