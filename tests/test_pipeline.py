"""The whole loop in miniature: build, compare at checkpoints, catch a planted fault, record and trace it.

The method has two steps: (1) assign members to regions, (2) take the weighted regional mean. The publisher releases
both the region list and the regional values, so there is a checkpoint after each step.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from athena.runs import RunRecord
from athena.validation import AnswerKey, Checkpoint, Divergence, DivergenceRegister, Tolerance, blame_window
from athena.vocab import CauseClass, DivergenceStatus

from conftest import BY_REGION, FIXED_ON, WRONG_REGION_ROWS, WeightedGroupMean, panel, regions

PUBLISHED_LIST = AnswerKey(regions(), source="source:synthetic")
PUBLISHED_VALUES = AnswerKey(panel([("North", 2015, 25.0), ("South", 2015, 50.0)]), source="source:synthetic")
MEMBERSHIP = Checkpoint(id="K1", after_step=1, published_value="region list", keys=("member", "group", "level"))
REGIONAL = Checkpoint(id="K2", after_step=2, published_value="regional table", keys=("area", "year"),
                      measure="value", tolerance=Tolerance.from_decimals(1, fixed_on=FIXED_ON))
T0 = datetime(2026, 9, 25, 12, tzinfo=timezone.utc)


def build(values, weights, groups):
    return WeightedGroupMean()({"values": values, "weights": weights, "groups": groups}, BY_REGION)


def test_a_correct_build_matches_the_publisher_at_both_checkpoints(values, weights, groups):
    output, _ = build(values, weights, groups)
    assert PUBLISHED_LIST.compare(groups, MEMBERSHIP).passed
    assert PUBLISHED_VALUES.compare(output, REGIONAL).passed


def test_a_planted_grouping_fault_is_caught_at_the_first_checkpoint(values, weights):
    wrong = regions(WRONG_REGION_ROWS)
    list_check = PUBLISHED_LIST.compare(wrong, MEMBERSHIP)
    output, _ = build(values, weights, wrong)
    value_check = PUBLISHED_VALUES.compare(output, REGIONAL)
    assert not list_check.passed and not value_check.passed
    assert {(m.key["member"], m.key["group"], m.side) for m in list_check.mismatches} == {
        ("BBB", "North", "missing"), ("BBB", "South", "extra")}

    window = blame_window({MEMBERSHIP.after_step: list_check.passed, REGIONAL.after_step: value_check.passed},
                          step_count=2)
    assert window == (1,), "the membership checkpoint narrows the fault to the grouping step"

    register = DivergenceRegister()
    register.record(Divergence(id="D1", checkpoint=MEMBERSHIP.id, size=float(list_check.missing + list_check.extra),
                               tolerance=0.0, suspected_steps=window))
    register.update("D1", status=DivergenceStatus.CORRECTED, cause=CauseClass.GROUPING_ERROR,
                    explanation="BBB was placed in South",
                    evidence=("test_a_correct_build_matches_the_publisher_at_both_checkpoints",))
    assert register.open() == ()


def test_a_membership_checkpoint_fails_on_an_extra_member_alone(groups):
    extra = regions([*[("AAA", "North", "region"), ("BBB", "North", "region"), ("CCC", "South", "region")],
                     ("DDD", "South", "region")])
    result = PUBLISHED_LIST.compare(extra, MEMBERSHIP)
    assert result.missing == 0 and result.extra == 1 and not result.passed


def test_a_checkpoint_names_a_measure_and_tolerance_together_or_neither():
    with pytest.raises(ValidationError, match="names neither"):
        Checkpoint(id="K", after_step=1, published_value="v", keys=("area",), measure="value")


def test_a_run_record_links_every_step_to_what_it_read(values, weights, groups):
    _, result = build(values, weights, groups)
    parsed = {"sha256:" + "0" * 64: values.content_hash(), "sha256:" + "1" * 64: weights.content_hash(),
              "sha256:" + "3" * 64: groups.content_hash()}
    run = RunRecord(id="run:1", project="project:index-catalogue", started_at=T0, finished_at=T0,
                    code_version="test", environment="sha256:" + "2" * 64, parsed=parsed, steps=(result,))
    assert run.final_output == result.output
    with pytest.raises(ValidationError, match="which no parsed snapshot"):
        RunRecord(id="run:2", project="project:index-catalogue", started_at=T0, finished_at=T0,
                  code_version="test", environment="sha256:" + "2" * 64, parsed={}, steps=(result,))
