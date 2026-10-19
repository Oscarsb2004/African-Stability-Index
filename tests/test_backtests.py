"""backtests.py on invented data: the AUC, the at-risk windows and the interval behave as the protocol says.
Each has a negative control."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backtests as bt  # noqa: E402


def test_auc_is_one_when_risk_separates_events_and_half_when_it_cannot():
    event = [True, True, False, False]
    assert bt.auc([4, 3, 2, 1], event) == 1.0
    assert bt.auc([1, 2, 3, 4], event) == 0.0
    assert bt.auc([1, 1, 1, 1], event) == 0.5  # ties count half
    assert np.isnan(bt.auc([1, 2], [True, True]))  # no non-events: undefined


def test_auc_ignores_missing_risk_and_a_random_score_sits_near_half():
    assert bt.auc([4, np.nan, 2, 1], [True, True, False, False]) == 1.0
    rng = np.random.default_rng(1)
    event = rng.random(4000) < 0.2
    assert abs(bt.auc(rng.random(4000), event) - 0.5) < 0.03  # negative control


def test_windows_keep_only_state_years_free_of_the_event_and_with_known_outcomes():
    flags = pd.DataFrame({2000: [0, 1, 0, 0], 2001: [1, 0, 0, np.nan], 2002: [0, 0, 0, 0]},
                         index=["AAA", "BBB", "CCC", "DDD"], dtype=float)
    rows = bt.windows(flags, 2000, 2000, 2)
    assert rows.set_index("iso3")["event"].to_dict() == {"AAA": True, "CCC": False}
    # BBB had the event at t; DDD's window is unknown, so neither is scored
    assert bt.windows(flags, 2001, 2001, 2).empty  # the window runs past the data


def test_history_counts_the_five_years_before():
    flags = pd.DataFrame({1995: [1.0], 2000: [0.0]}, index=["AAA"])
    assert bt.history(flags, "AAA", 2000) == 1.0
    assert bt.history(flags, "AAA", 2001) == 0.0  # 1995 is outside 1996-2000


def test_the_interval_excludes_half_for_a_real_signal_and_includes_it_for_noise():
    rng = np.random.default_rng(2)
    states = np.repeat([f"S{i}" for i in range(60)], 10)
    event = rng.random(600) < 0.25
    rows = pd.DataFrame({"iso3": states, "event": event, "signal": event + rng.normal(0, 0.6, 600),
                         "noise": rng.random(600)})
    out = bt.compare(rows, ["signal", "noise"], "noise")
    assert out["signal"]["low"] > 0.5 and bt.verdict(out, "signal", "noise")["informative"]
    assert out["noise"]["low"] < 0.5 < out["noise"]["high"]  # negative control
    assert out["signal - noise"]["low"] > 0


def test_the_hit_rate_counts_events_in_the_bottom_fifth():
    rows = pd.DataFrame({"iso3": ["A", "B", "C"], "year": [2000] * 3, "event": [True, True, False]})
    bottom = pd.Series({("A", 2000): True, ("B", 2000): False, ("C", 2000): True})
    assert bt.hit_rate(rows, bottom) == {"events": 2, "in_bottom_fifth": 1, "share": 0.5}
