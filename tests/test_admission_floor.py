"""Edition 2, step 5 (plan 4.12): every scoring indicator has a real value for at least ADMISSION_FLOOR of the 54
states at the reference year; an indicator below it is descriptive. Reads the committed panel."""

import pandas as pd
import yaml

from asi.core.constants import ADMISSION_FLOOR


def coverage():
    year = yaml.safe_load(open("data/panel/panel_meta.yaml", encoding="utf-8"))["reference_year"]
    obs = pd.read_csv("data/panel/observations.csv", usecols=["iso3", "variable_name", "year", "raw_value", "role"])
    now = obs[obs["year"] == year].dropna(subset=["raw_value"])
    return now.groupby(["variable_name", "role"])["iso3"].nunique()


def test_every_scoring_indicator_clears_the_floor():
    c = coverage()
    below = {v: int(n) for (v, role), n in c.items() if role == "scoring" and n < ADMISSION_FLOOR}
    assert below == {}


def test_the_floor_does_bind_some_indicators():
    """Negative control: the rule is doing work, so some descriptive indicator sits below the floor."""
    c = coverage()
    assert any(role == "descriptive" and n < ADMISSION_FLOOR for (v, role), n in c.items())
