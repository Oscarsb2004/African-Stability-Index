"""Edition 2, step 2 (plan 4.5): no regional fill. Edition 1's fill is not carried over (P105), so a gap in the
published panel stays a gap."""

import pandas as pd


def test_the_published_panel_has_no_regional_fill():
    panel = pd.read_csv("data/panel/observations.csv", usecols=["provenance"])
    assert not panel["provenance"].isin(["regional_mean", "regional_quantile"]).any()
