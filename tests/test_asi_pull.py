"""The ASI's frozen pull as a dataset, from a synthetic workbook in its layout; and `file:` sources, locked like any
other. Every check has a negative control."""

import io
from datetime import datetime

import pandas as pd
import pytest
from openpyxl import Workbook

from asi.adapters import asi_pull
from athena import fetch


def workbook(rows=(("AAA", "thing", 2000, 1.5), ("AAA", "thing", 2001, 0.00952819999999999),
                   ("BBB", "other", 2000, -2.0)), log=(("thing", "TH.ING"), ("other", "OT.HER"))) -> bytes:
    book = Workbook()
    book.properties.created = datetime(2026, 8, 8, 23, 46, 20)
    sheets = {"coverage_report": [("variable_name", "n_countries"), ("thing", 1)],
              "raw_data": [("iso3", "variable_name", "year", "value"), *rows],
              "pull_log": [("variable_name", "series_code", "database"), *((v, c, "wdi") for v, c in log)]}
    book.remove(book.active)
    for name, lines in sheets.items():
        sheet = book.create_sheet(name)
        for line in lines:
            sheet.append(line)
    out = io.BytesIO()
    book.save(out)
    return out.getvalue()


def test_the_pull_becomes_a_dataset_named_after_its_creation_date():
    name, tables, report = asi_pull.ingest(workbook())
    values = tables["values"].set_index(["SERIES", "REF_AREA", "TIME_PERIOD"]).OBS_VALUE
    assert name == "asi-pull-2026-08-08"
    assert values.to_dict() == {("OT.HER", "BBB", "2000"): -2.0, ("TH.ING", "AAA", "2000"): 1.5,
                                ("TH.ING", "AAA", "2001"): 0.00952819999999999}
    assert set(tables["values"].EDITION) == {"ASI pull 2026-08-08"}
    assert report[0].startswith("asi-pull-2026-08-08: 3 values, 2 series, 2 areas, 2000 to 2001")


def test_a_variable_the_log_cannot_place_stops_the_ingest():
    with pytest.raises(ValueError, match="no series in pull_log: \\['thing'\\]"):
        asi_pull.ingest(workbook(log=(("other", "OT.HER"),)))


def test_a_file_source_is_read_from_the_project_and_locked(tmp_path):
    # athena-kit reads a `file:` address from the project's folder, the one that holds its lock
    (tmp_path / "data.bin").write_bytes(b"first")
    getter = fetch.Fetcher(tmp_path / "lock")
    assert getter.get("file:data.bin") == b"first"
    assert "file:data.bin" in pd.read_json(tmp_path / "lock", typ="series").index
    (tmp_path / "data.bin").write_bytes(b"changed")
    with pytest.raises(fetch.SourceChanged):
        fetch.Fetcher(tmp_path / "lock").get("file:data.bin")
