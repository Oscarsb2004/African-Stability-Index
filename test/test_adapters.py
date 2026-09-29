"""The adapters on synthetic sources: each layout family of the annex, the database pages, the groupings, the
datasets they write, and the rule that nothing is dropped silently. Every check has a negative control."""

import numpy as np
import pandas as pd
import pytest

import fixtures
from adapters import mdg_annex, mdg_database, readers, wayback
from adapters.__main__ import mdg
from adapters.codes import Coder, UnmappedNames
from athena import dataset
from athena.table import table

ROW = {"DATASET": "d", "SERIES": "s", "REF_AREA": "AAA", "TIME_PERIOD": "2015", "OBS_VALUE": 1.5,
       "EDITION": "e", "DERIVED": False}


# ── the common format and datasets ──────────────────────────────────────────────────────────────────────────

def test_a_value_printed_only_as_a_bound_keeps_the_bound_and_the_print():
    frame = table([ROW | {"OBS_VALUE": None, "UPPER_BOUND": 0.1, "COMMENT_OBS": "<0.1"}])
    assert np.isnan(frame.OBS_VALUE[0]) and frame.UPPER_BOUND[0] == 0.1


def test_a_row_without_a_value_must_say_what_was_printed():
    with pytest.raises(Exception, match="must say what was printed"):
        table([ROW | {"OBS_VALUE": None}])


def test_a_breakdown_is_part_of_the_key():
    table([ROW | {"SEX": "F"}, ROW | {"SEX": "M"}])
    with pytest.raises(Exception, match="each key appears once"):
        table([ROW | {"SEX": "F"}, ROW | {"SEX": "F"}])


def test_a_dataset_reads_back_exactly_as_written(tmp_path):
    values = table([ROW | {"OBS_VALUE": 1 / 3}, ROW | {"REF_AREA": "BBB", "OBS_VALUE": None, "COMMENT_OBS": "<5",
                                                        "UPPER_BOUND": 5.0}])
    dataset.write("x", {"values": values}, ["report"], tmp_path)
    back = dataset.load("x", root=tmp_path)
    pd.testing.assert_frame_equal(back, values)
    assert (tmp_path / "x" / "report.txt").read_text(encoding="utf-8") == "report\n"


# ── readers of the database pages ───────────────────────────────────────────────────────────────────────────

def test_a_series_page_names_itself():
    head = readers.series_header(fixtures.series_page({"Alpha": "0.90"}))
    assert (head["name"], head["indicator"], head["last_updated"]) == ("Invented series", "9.9", "06 Jul 2015")


def test_a_metadata_page_gives_every_section():
    page = fixtures.metadata_page({"Definition": "A ratio.", "Regional and Global estimates": "Weighted by people."})
    assert readers.metadata_sections(page) == {"Definition": "A ratio.",
                                               "Regional and Global estimates": "Weighted by people."}


def test_an_unreadable_cell_is_listed_and_a_bound_is_kept():
    problems = []
    found = readers.mdg_series(fixtures.series_page({"Alpha": "0.90", "Beta": "<5", "Gamma": "n/a"}), problems)
    assert ("Beta", 1990, None, "estimated", "<5") in found and len(found) == 4
    assert problems == ["Gamma 1990: unreadable value 'n/a'", "Gamma 1991: unreadable value 'n/a'"]
    with pytest.raises(readers.ParseError, match="unreadable"):
        readers.mdg_series(fixtures.series_page({"Gamma": "n/a"}))


def test_the_earliest_capture_is_taken_for_each_page():
    listing = "20160101000000 a?srid=1\n20150801000000 a?srid=1\n20150901000000 a?srid=2\nbroken line x y\n"
    found = wayback.earliest(listing, lambda url: url.split("=")[1] if "srid=" in url else None)
    assert found == {"1": ("20150801000000", "a?srid=1"), "2": ("20150901000000", "a?srid=2")}


def test_the_database_adapter_lists_every_problem_and_stops_on_an_unknown_name():
    pages = {"s1": fixtures.series_page({"Alpha": "0.90", "Beta": "<5"}),
             "m1": fixtures.metadata_page({"Regional and Global estimates": "Weighted."}),
             "s2": b"<html>not a series page</html>"}
    captures = pd.DataFrame({"series": ["1", "2"], "series_capture": ["s1", "s2"], "metadata_capture": ["m1", ""]})
    values, codebook, report = mdg_database.ingest(pages.__getitem__, Coder(fixtures.CODES, {}), captures)
    assert len(values) == 4 and codebook.loc[0, "Regional and Global estimates"] == "Weighted."
    assert any("series 2: page not read" in line for line in report)
    unknown = {**pages, "s1": fixtures.series_page({"Zeta": "1.0"})}
    with pytest.raises(UnmappedNames, match="Zeta"):
        mdg_database.ingest(unknown.__getitem__, Coder(fixtures.CODES, {}), captures.iloc[:1])


# ── the annex, one layout family at a time ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def annex():
    return mdg_annex.ingest(fixtures.positioned_pdf(fixtures.ANNEX))


def value(values, series, area, period, urbanisation="_Z"):
    rows = values[(values.SERIES == series) & (values.REF_AREA == area) & (values.TIME_PERIOD == period)
                  & (values.URBANISATION == urbanisation)]
    assert len(rows) == 1, rows
    return rows.iloc[0]


def test_sub_columns_become_a_breakdown_and_a_header_mark_a_note(annex):
    values, _, _ = annex
    assert value(values, "9.1", "world", "1990", "R").OBS_VALUE == 62
    assert value(values, "9.1", "world", "2015", "_T").COMMENT_OBS == "b"


def test_a_dash_publishes_nothing_and_a_bound_is_kept(annex):
    values, codebook, _ = annex
    assert values[(values.REF_AREA == "northern-africa") & (values.TIME_PERIOD == "1990")].shape[0] == 2
    assert codebook.set_index("indicator").loc["9.1", "dashes"] == 1
    bound = value(values, "9.1", "northern-africa", "2015", "U")
    assert np.isnan(bound.OBS_VALUE) and bound.UPPER_BOUND == 0.1 and "<0.1" in bound.COMMENT_OBS


def test_thousands_join_and_an_interval_belongs_to_its_value(annex):
    values, _, _ = annex
    assert value(values, "9.2", "world", "1986").OBS_VALUE == 1774954
    oceania = value(values, "9.2", "oceania", "1986")
    assert (oceania.OBS_VALUE, oceania.LOWER_BOUND, oceania.UPPER_BOUND) == (0.09, 0.08, 0.10)


def test_every_table_gets_a_status_and_every_loss_a_reason(annex):
    _, codebook, report = annex
    status = codebook.set_index("indicator")["status"].to_dict()
    assert status == {"9.1": "read", "9.2": "read", "9.3": "no regional data", "9.4": "not read"}
    text = "\n".join(report)
    assert "'Atlantis' is not a known group" in text
    assert "9.4: not read: no row of periods heads its columns" in text


def test_a_value_far_from_every_column_is_reported(annex):
    stray = fixtures.ANNEX + fixtures.annex_row(236, "Caribbean", ["5"], [560])
    _, _, report = mdg_annex.ingest(fixtures.positioned_pdf(stray))
    assert any("'5' fits no column" in line for line in report)


# ── all three MDG datasets together ─────────────────────────────────────────────────────────────────────────

def test_the_mdg_ingest_writes_three_datasets(tmp_path):
    captures = tmp_path / "captures.csv"
    pd.DataFrame({"series": ["611"], "series_capture": ["https://example.test/s611"],
                  "metadata_capture": ["https://example.test/m611"]}).to_csv(captures, index=False)
    files = fixtures.files(**{"annex-2015": fixtures.positioned_pdf(fixtures.ANNEX)}) | {
        "https://example.test/s611": fixtures.series_page({"Alpha": "0.90", "Beta": "0.80"}),
        "https://example.test/m611": fixtures.metadata_page({"Definition": "A ratio."})}
    report = mdg(fixtures.Session(files), tmp_path / "datasets", captures, tmp_path / "lock")
    assert any(line.startswith("mdg-db-2015-07: 1 series listed, 1 read") for line in report)
    assert len(dataset.load("mdg-db-2015-07", root=tmp_path / "datasets")) == 4
    membership = dataset.load("mdg-groupings-2015", "membership", tmp_path / "datasets")
    assert set(membership[membership.group == "least-developed"].member) == {"BBB", "CCC"}
    assert set(membership[membership.group == "north-africa-eca"].member) == {"BBB"}
