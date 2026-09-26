"""Readers reach the network only through the transport they are given, and parse without it."""

from datetime import datetime, timezone

import pyarrow as pa
import pytest
from pydantic import BaseModel, ConfigDict, ValidationError

from athena.ids import hash_bytes
from athena.sources import FormatReader, Recipe, Snapshot, SourceCard, Terms
from athena.vocab import Access

from conftest import panel

SOURCE = SourceCard(id="source:synthetic", title="Synthetic", publisher="Test", access=Access.BULK,
                    terms=Terms(url="https://example.org/terms", summary="Not yet read."))


class CsvParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    path: str


class CsvReader(FormatReader):
    ID = "reader:csv"
    VERSION = "0.1.0"
    Parameters = CsvParameters

    def fetch(self, recipe, transport):
        params = self.check(recipe)
        url = f"https://example.org/{params.path}"
        data, media_type = transport.get(url)
        return data, url, media_type

    def parse(self, data, recipe):
        rows = [line.split(",") for line in data.decode().strip().splitlines()[1:]]
        return panel([(a, int(y), float(v)) for a, y, v in rows])


class FixtureTransport:
    def __init__(self, files):
        self.files, self.requested = files, []

    def get(self, url):
        self.requested.append(url)
        return self.files[url], "text/csv"


RECIPE = Recipe(id="recipe:synthetic-values", title="Values", source="source:synthetic", reader="reader:csv",
                parameters={"path": "values.csv"})
CSV = b"area,year,value\nAAA,2015,10\nBBB,2015,30\n"


def test_fetch_goes_through_the_transport_and_parse_is_repeatable():
    transport = FixtureTransport({"https://example.org/values.csv": CSV})
    data, url, media_type = CsvReader().fetch(RECIPE, transport)
    assert transport.requested == ["https://example.org/values.csv"]
    first, second = CsvReader().parse(data, RECIPE), CsvReader().parse(data, RECIPE)
    assert first.content_hash() == second.content_hash()
    assert first.num_rows == 2


def test_a_reader_refuses_a_recipe_meant_for_another_reader():
    other = RECIPE.model_copy(update={"reader": "reader:sdmx"})
    with pytest.raises(ValueError, match="names reader reader:sdmx"):
        CsvReader().fetch(other, FixtureTransport({}))


def test_a_reader_refuses_parameters_it_does_not_declare():
    bad = Recipe(id="recipe:bad", title="Bad", source="source:synthetic", reader="reader:csv",
                 parameters={"path": "values.csv", "sheet": "2"})
    with pytest.raises(ValidationError):
        CsvReader().check(bad)


def test_a_snapshot_is_named_by_the_hash_of_its_bytes():
    snap = Snapshot.of(CSV, source=SOURCE, recipe=RECIPE, url="https://example.org/values.csv",
                       media_type="text/csv", retrieved_at=datetime(2026, 9, 25, tzinfo=timezone.utc))
    assert snap.hash == hash_bytes(CSV)
    assert snap.recipe == "recipe:synthetic-values@0.1.0"
    assert snap.size_bytes == len(CSV)
