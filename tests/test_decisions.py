"""The owner's decisions of 2026-09-25, each held by a test: rounding, hashing, SDMX concepts, one schema truth."""

from pathlib import Path

import pyarrow as pa
import pytest
from pydantic import ValidationError

from athena.frames import Column, Frame
from athena.rounding import Rounding, RoundingRule
from athena.schemas import definitions, render
from athena.validation import Tolerance
from athena.vocab import Concept, DType, Role

from conftest import FIXED_ON, VALUES, citation, panel


@pytest.mark.parametrize("value, decimals, expected", [
    (2.5, 0, 3.0),
    (2.4999, 0, 2.0),
    (-2.5, 0, -3.0),
    (2.675, 2, 2.68),
    (1.45, 1, 1.5),
    (0.125, 2, 0.13),
])
def test_half_up_is_the_default_and_rounds_the_number_as_written(value, decimals, expected):
    assert Rounding(decimals=decimals).apply(value) == expected


def test_builtin_round_would_have_been_wrong():
    assert round(2.675, 2) == 2.67
    assert Rounding(decimals=2).apply(2.675) == 2.68


def test_a_publisher_rule_is_followed_and_cited():
    rule = Rounding(decimals=2, rule=RoundingRule.HALF_EVEN, stated_by_publisher=citation("rounded to even"))
    assert rule.apply(0.125) == 0.12 and not rule.is_default
    assert Rounding(decimals=2).is_default
    assert Rounding(decimals=2).apply(None) is None


def test_tolerance_follows_the_rounding():
    assert Tolerance.from_rounding(Rounding(decimals=1), fixed_on=FIXED_ON).absolute == pytest.approx(0.05)


def test_the_hash_ignores_chunking_and_row_order():
    frame = panel(VALUES)
    rechunked = Frame(pa.concat_tables([frame.table.slice(0, 1), frame.table.slice(1)]), frame.manifest)
    reordered = panel(list(reversed(VALUES)))
    assert frame.content_hash() == rechunked.content_hash() == reordered.content_hash()


def test_negative_zero_hashes_as_zero_and_nan_is_refused():
    assert panel([("AAA", 2015, -0.0)]).content_hash() == panel([("AAA", 2015, 0.0)]).content_hash()
    with pytest.raises(ValueError, match="no NaN"):
        panel([("AAA", 2015, float("nan"))]).content_hash()


def test_a_frame_hash_is_pinned_to_its_scheme():
    """If this value changes, every stored hash changes with it: that needs a new scheme, not an edit."""
    assert panel([("AAA", 2015, 10.0)]).content_hash() == PINNED


def test_a_concept_must_agree_with_the_column_role():
    Column(name="REF_AREA", dtype=DType.STRING, role=Role.ENTITY, concept=Concept.REF_AREA)
    with pytest.raises(ValidationError, match="REF_AREA, which is a entity"):
        Column(name="REF_AREA", dtype=DType.STRING, role=Role.CATEGORY, concept=Concept.REF_AREA)


def test_every_definition_exports_one_schema_and_the_export_is_repeatable():
    kinds = set(definitions())
    assert {"source", "recipe", "method", "shell", "indicator", "index", "grouping"} <= kinds
    assert render() == render()
    assert '"additionalProperties": false' in render()["source.schema.json"]



def test_the_committed_schemas_match_the_definitions():
    """The exported files are generated; edit the Python and run: python -m athena.schemas schemas"""
    folder = Path(__file__).parent.parent / "schemas"
    committed = {p.name: p.read_text(encoding="utf-8") for p in folder.glob("*.schema.json")}
    assert committed == render()


PINNED = "sha256:6d1661fc2f6af093bc85750fe4744e465ee00250037cff4f3ce798cefcfc7ad2"
