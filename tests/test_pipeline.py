"""The whole loop in miniature: build, compare at a checkpoint, catch a planted fault, record and trace it."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from athena.reference import Grouping
from athena.runs import RunRecord
from athena.validation import AnswerKey, Checkpoint, Divergence, DivergenceRegister, Tolerance, blame_window
from athena.vocab import CauseClass, DivergenceStatus

from conftest import FIXED_ON, REGIONS, WeightedGroupMean, panel

PUBLISHED = AnswerKey(panel([("North", 2015, 25.0), ("South", 2015, 50.0)]), source="source:synthetic")
REGIONAL = Checkpoint(id="K2", after_step=2, published_value="regional table", keys=("area", "year"),
                      measure="value", tolerance=Tolerance.from_decimals(1, fixed_on=FIXED_ON))
T0 = datetime(2026, 9, 25, 12, tzinfo=timezone.utc)


def build(values, weights, grouping):
    return WeightedGroupMean()({"values": values, "weights": weights}, {"grouping": grouping})


def test_a_correct_build_matches_the_publisher(values, weights):
    output, _ = build(values, weights, REGIONS)
    assert PUBLISHED.compare(output, REGIONAL).passed


def test_a_planted_grouping_fault_is_caught_recorded_and_traced(values, weights):
    wrong = Grouping(id="grouping:synthetic-regions", title="Wrong", publisher="Test", disjoint=True,
                     groups={"North": ("AAA",), "South": ("BBB", "CCC")})
    output, _ = build(values, weights, wrong)
    comparison = PUBLISHED.compare(output, REGIONAL)
    assert not comparison.passed

    window = blame_window({1: True, REGIONAL.after_step: comparison.passed}, step_count=2)
    assert window == (2,)

    register = DivergenceRegister()
    register.record(Divergence(id="D1", checkpoint=REGIONAL.id, size=comparison.max_abs_difference,
                               tolerance=REGIONAL.tolerance.absolute, suspected_steps=window))
    register.update("D1", status=DivergenceStatus.CORRECTED, cause=CauseClass.GROUPING_ERROR,
                    explanation="BBB was placed in South", evidence=("test_a_correct_build_matches_the_publisher",))
    assert register.open() == ()


def test_a_run_record_links_every_step_to_what_it_read(values, weights):
    _, result = build(values, weights, REGIONS)
    parsed = {"sha256:" + "0" * 64: values.content_hash(), "sha256:" + "1" * 64: weights.content_hash()}
    run = RunRecord(id="run:1", project="project:index-catalogue", started_at=T0, finished_at=T0,
                    code_version="test", environment="sha256:" + "2" * 64, parsed=parsed, steps=(result,))
    assert run.final_output == result.output
    with pytest.raises(ValidationError, match="which no parsed snapshot"):
        RunRecord(id="run:2", project="project:index-catalogue", started_at=T0, finished_at=T0,
                  code_version="test", environment="sha256:" + "2" * 64, parsed={}, steps=(result,))
