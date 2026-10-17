"""01_inputs.py: the ASI's inputs selected from Athena datasets, all of them or none.

Synthetic rows in Athena's common format stand in for the datasets. The selection keeps the registry's series, the
member states and the pull window; a series no dataset holds, or two hold, stops the run rather than being guessed.
"""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location("inputs_stage", Path(__file__).resolve().parents[1] / "01_inputs.py")
inputs_stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inputs_stage)


def rows(dataset, series, area, year, value=1.0):
    return {"DATASET": dataset, "SERIES": series, "REF_AREA": area, "TIME_PERIOD": str(year), "OBS_VALUE": value}


VALUES = pd.DataFrame([
    rows("d1", "A.1", "AGO", 2000), rows("d1", "A.1", "AGO", 1990),        # 1990 falls before the window
    rows("d1", "A.1", "FRA", 2000),                                         # not a member state
    rows("d1", "B.2", "BEN", 2001), rows("d1", "B.2", "BEN", 2002, None),  # a cell with no value
    rows("d1", "C.3", "BEN", 2001),                                         # not in the registry
])


def test_only_registry_series_member_states_and_window_years_with_values():
    chosen = inputs_stage.select(VALUES, {"A.1", "B.2"}, {"AGO", "BEN"}, 1995, 2024)
    assert chosen[["SERIES", "REF_AREA", "TIME_PERIOD"]].values.tolist() == [["A.1", "AGO", "2000"],
                                                                             ["B.2", "BEN", "2001"]]


def test_a_series_no_dataset_holds_stops_the_run():
    with pytest.raises(ValueError, match=r"series no dataset holds: \['Z.9'\]"):
        inputs_stage.select(VALUES, {"A.1", "Z.9"}, {"AGO", "BEN"}, 1995, 2024)


def test_a_series_two_datasets_hold_stops_the_run():
    both = pd.concat([VALUES, pd.DataFrame([rows("d2", "A.1", "AGO", 2001)])], ignore_index=True)
    with pytest.raises(ValueError, match=r"series two datasets hold: \['A.1'\]"):
        inputs_stage.select(both, {"A.1"}, {"AGO"}, 1995, 2024)
