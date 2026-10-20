"""
Edition 2, step 9 (plan 1.2): organised violence is scored by its three parts (state-based and one-sided in SEC,
non-state in COH) and its total is descriptive, so no death counts twice. Reads the committed inputs.
"""

import numpy as np
import pandas as pd
import yaml

PARTS = {"sb_total_deaths_best": "state_based_deaths", "os_total_deaths_best": "one_sided_deaths",
         "ns_total_deaths_best": "non_state_deaths"}
TOTAL = "cumulative_total_deaths_in_orgvio_best"


def _ucdp() -> pd.DataFrame:
    inputs = pd.read_csv("data/inputs.csv", dtype={"TIME_PERIOD": str})
    sub = inputs[inputs["SERIES"].isin([*PARTS, TOTAL])]
    return sub.pivot_table(index=["REF_AREA", "TIME_PERIOD"], columns="SERIES", values="OBS_VALUE")


def test_the_three_parts_sum_to_the_total_in_every_country_year():
    wide = _ucdp().dropna()
    assert len(wide) > 1000
    assert np.allclose(wide[list(PARTS)].sum(axis=1), wide[TOTAL])
    assert not np.allclose(wide[["sb_total_deaths_best", "os_total_deaths_best"]].sum(axis=1), wide[TOTAL]), \
        "negative control: two parts alone fall short somewhere"


def test_the_parts_are_scored_and_the_total_is_not():
    roles = {i["series_code"]: (i["variable_name"], i["role"])
             for f in ("indicators_list/pillar_sec.yaml", "indicators_list/pillar_coh.yaml")
             for i in yaml.safe_load(open(f, encoding="utf-8"))}
    assert {roles[c] for c in PARTS} == {(v, "scoring") for v in PARTS.values()}
    assert roles[TOTAL] == ("organised_violence_deaths", "descriptive")
