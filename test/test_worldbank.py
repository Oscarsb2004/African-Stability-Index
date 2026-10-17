"""The World Bank bulk adapter on synthetic zips in the databank layout: every value, the edition read from the zip
itself, footnotes kept with their values, and nothing dropped. Every check has a negative control."""

import io
import zipfile

import pandas as pd
import pytest

import fixtures
from adapters import sources, worldbank
from adapters.__main__ import world_bank
from athena import dataset

HEADER = ["Country Name", "Country Code", "Indicator Name", "Indicator Code", "2000", "2001", "2002"]
VALUES = [["Alpha", "AAA", "Thing", "TH.ING", "1.5", "", "0.1"],
          ["Beta", "BBB", "Thing", "TH.ING", "", "", ""],
          ["Alpha", "AAA", "Other", "OT.HER", "-2", "1e-05", ""]]


def bulk(db="WDI", footnotes=None, stamp=(2026, 10, 8, 19, 47, 54)) -> bytes:
    """A databank bulk zip with invented values; footnotes add the WDI-only files."""
    files = {f"{db}CSV.csv": [HEADER] + VALUES,
             f"{db}Series.csv": [["Series Code", "Indicator Name", "License Type"], ["TH.ING", "Thing", "CC BY-4.0"],
                                 ["OT.HER", "Other", "SIPRI terms and conditions"]],
             f"{db}Country.csv": [["Country Code", "Short Name", "Region"], ["AAA", "Alpha", "Somewhere"],
                                  ["BBB", "Beta", ""]]}
    if footnotes is not None:
        files[f"{db}footnote.csv"] = [["CountryCode", "SeriesCode", "Year", "DESCRIPTION"]] + footnotes
        files[f"{db}series-time.csv"] = [["SeriesCode", "Year", "DESCRIPTION"], ["TH.ING", "YR2000", "A note."]]
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name, rows in files.items():
            z.writestr(zipfile.ZipInfo(name, stamp), "".join(",".join(f'"{c}"' for c in r) + "\n" for r in rows))
    return out.getvalue()


def test_every_printed_value_is_ingested_with_the_edition_of_the_zip():
    name, tables, report = worldbank.ingest(bulk(), "WDI")
    values = tables["values"].set_index(["SERIES", "REF_AREA", "TIME_PERIOD"]).OBS_VALUE
    assert name == "wdi-2026-10-08" and report[0].startswith("wdi-2026-10-08: 4 values, 2 series, 1 areas")
    assert values.to_dict() == {("OT.HER", "AAA", "2000"): -2.0, ("OT.HER", "AAA", "2001"): 1e-05,
                                ("TH.ING", "AAA", "2000"): 1.5, ("TH.ING", "AAA", "2002"): 0.1}
    assert set(tables["values"].EDITION) == {"WDI 2026-10-08"}
    assert worldbank.ingest(bulk(stamp=(2026, 9, 25, 0, 0, 0)), "WDI")[0] == "wdi-2026-09-25"


def test_a_footnote_goes_to_its_value_and_one_on_an_empty_cell_is_kept():
    _, tables, report = worldbank.ingest(bulk(footnotes=[["AAA", "TH.ING", "YR2000", "Estimate."],
                                                         ["BBB", "TH.ING", "YR2001", "No data."]]), "WDI")
    noted = tables["values"].set_index(["REF_AREA", "SERIES", "TIME_PERIOD"]).COMMENT_OBS
    assert noted[("AAA", "TH.ING", "2000")] == "Estimate." and noted[("AAA", "TH.ING", "2002")] == ""
    assert tables["footnotes_without_value"].to_dict("records") == [
        {"REF_AREA": "BBB", "SERIES": "TH.ING", "COMMENT_OBS": "No data.", "TIME_PERIOD": "2001"}]
    assert "footnotes: 1 on values, 1 on cells without a value" in report[1]
    assert tables["series-time"].DESCRIPTION.tolist() == ["A note."], "any other file is kept verbatim"


def test_two_footnotes_on_one_value_stop_the_ingest():
    with pytest.raises(pd.errors.MergeError):
        worldbank.ingest(bulk(footnotes=[["AAA", "TH.ING", "YR2000", "One."], ["AAA", "TH.ING", "YR2000", "Two."]]),
                         "WDI")


def test_the_command_writes_one_dataset_per_bulk_download(tmp_path):
    listed = {key: s for key, s in sources().items() if s.get("kind") == "worldbank-bulk"}
    served = {s["url"]: bulk(s["database"], stamp=(2026, 9, 25, 0, 0, 0)) for s in listed.values()}
    report = world_bank(fixtures.Session(served), tmp_path / "datasets", tmp_path / "lock")
    assert sorted(p.name for p in (tmp_path / "datasets").iterdir()) == ["wdi-2026-09-25", "wgi-2026-09-25"]
    assert len(dataset.load("wgi-2026-09-25", root=tmp_path / "datasets")) == 4
    assert dataset.load("wdi-2026-09-25", "codebook", tmp_path / "datasets")["License Type"].tolist() == [
        "CC BY-4.0", "SIPRI terms and conditions"]
    assert any(line.startswith("wgi-2026-09-25: 4 values") for line in report)
    assert (tmp_path / "lock").exists(), "both addresses are locked on first use"
