"""The generic parts: fetch, the common format, aggregation and comparison. Each check has a negative control."""

import hashlib

import numpy as np
import pandas as pd
import pandera.errors
import pytest

from athena import aggregate
from athena.check import compare, summary
from athena.fetch import Fetcher, SourceChanged
from athena.table import canonical_hash, round_half_up, table
from fixtures import Session

ROW = {"DATASET": "d", "SERIES": "x", "REF_AREA": "AAA", "TIME_PERIOD": "2015", "OBS_VALUE": 1.5,
       "UNIT_MEASURE": "percent", "EDITION": "e", "DERIVED": True}


# ── fetch ───────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_first_fetch_is_locked_and_a_changed_source_is_refused(tmp_path):
    lock = tmp_path / "sources.lock"
    Fetcher(lock, Session({"u": b"one"})).get("u")
    assert Fetcher(lock, Session({"u": b"one"})).get("u") == b"one"
    assert hashlib.sha256(b"one").hexdigest() in lock.read_text()
    with pytest.raises(SourceChanged, match="the lock says"):
        Fetcher(lock, Session({"u": b"two"})).get("u")


# ── the common format ───────────────────────────────────────────────────────────────────────────────────────

def test_the_format_accepts_a_valid_row_and_sorts_by_key():
    frame = table([ROW | {"REF_AREA": "BBB"}, ROW])
    assert list(frame["REF_AREA"]) == ["AAA", "BBB"]


@pytest.mark.parametrize("bad", [ROW | {"EXTRA": 1}, ROW | {"OBS_VALUE": np.inf}])
def test_the_format_refuses_an_unknown_column_and_an_infinite_value(bad):
    with pytest.raises((pandera.errors.SchemaError, pandera.errors.SchemaErrors)):
        table([bad])


def test_the_format_refuses_a_key_twice():
    with pytest.raises(pandera.errors.SchemaError):
        table([ROW, ROW])


def test_the_hash_ignores_row_order_and_the_sign_of_zero():
    a = table([ROW, ROW | {"REF_AREA": "BBB", "OBS_VALUE": 0.0}])
    b = table([ROW | {"REF_AREA": "BBB", "OBS_VALUE": -0.0}, ROW])
    assert canonical_hash(a) == canonical_hash(b)
    assert canonical_hash(a) != canonical_hash(table([ROW | {"OBS_VALUE": 1.5000001}, ROW | {"REF_AREA": "BBB"}]))


# ── rounding and comparison ─────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("value, decimals, expected",
                         [(2.25, 1, 2.3), (-2.25, 1, -2.3), (0.125, 2, 0.13), (22.14951, 1, 22.1), (26.35, 1, 26.4)])
def test_half_up_on_the_number_as_written(value, decimals, expected):
    assert round_half_up(value, decimals) == expected


def test_a_value_is_rounded_once_to_the_publishers_decimals():
    ours = pd.Series({"g": 22.14951})
    assert compare(ours, pd.Series({"g": 22.1}), 1)["match"].all()
    assert not compare(ours, pd.Series({"g": 22.2}), 1)["match"].any(), "rounding via 3 decimals would give 22.2"


def test_the_summary_counts_missing_and_extra():
    compared = compare(pd.Series({"a": 1.0, "b": 2.0}), pd.Series({"a": 1.0, "c": 3.0}), 1)
    assert summary(compared) | {"largest_difference": 0} == {"compared": 1, "matched": 1, "missing": 1, "extra": 1,
                                                             "largest_difference": 0}


# ── aggregation ─────────────────────────────────────────────────────────────────────────────────────────────

MEMBERS = pd.DataFrame({"member": ["A", "B", "C"], "group": ["g", "g", "g"]})


def test_a_group_value_is_the_formula_on_its_members_sums():
    counts = pd.DataFrame({"women": [30.0, 10.0, 5.0], "seats": [100.0, 50.0, 10.0]}, index=["A", "B", "C"])
    known = aggregate.complete(counts, {}, "100 * women / seats")
    groups = aggregate.by_group(known, MEMBERS, "100 * women / seats")
    assert groups.loc["g", "value"] == pytest.approx(100 * 45 / 160)
    assert groups.loc["g", "value"] != pytest.approx(known["value"].mean()), "not the mean of the ratios"


def test_a_country_missing_a_variable_is_left_out_and_counted():
    counts = pd.DataFrame({"women": [30.0, None, 5.0], "seats": [100.0, 50.0, 10.0]}, index=["A", "B", "C"])
    groups = aggregate.by_group(aggregate.complete(counts, {}, "100 * women / seats"), MEMBERS, "100 * women / seats")
    assert groups.loc["g", "countries"] == 2 and groups.loc["g", "value"] == pytest.approx(100 * 35 / 110)


def test_a_weighted_mean_is_a_derived_product_over_the_weights():
    frame = pd.DataFrame({"x": [1.0, 3.0, 5.0], "w": [1.0, 1.0, 2.0]}, index=["A", "B", "C"])
    known = aggregate.complete(frame, {"wx": "w * x"}, "wx / w")
    assert aggregate.by_group(known, MEMBERS, "wx / w").loc["g", "value"] == pytest.approx(14 / 4)


def test_a_country_with_an_infinite_derived_variable_is_left_out():
    frame = pd.DataFrame({"e": [1.0, 0.0], "r": [50.0, 0.0]}, index=["A", "B"])
    known = aggregate.complete(frame, {"p": "100 * e / r"}, "e / p")
    assert list(known.index) == ["A"]
