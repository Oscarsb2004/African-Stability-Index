"""The answer key can only be compared against, and every divergence is kept with its reason."""

import pytest
from pydantic import ValidationError

from athena.validation import AnswerKey, Checkpoint, Divergence, DivergenceRegister, Tolerance, blame_window
from athena.vocab import CauseClass, DivergenceStatus

from conftest import FIXED_ON, panel

PUBLISHED = [("North", 2015, 25.0), ("South", 2015, 50.0)]
CHECK = Checkpoint(id="K4", after_step=5, published_value="regional table", keys=("area", "year"), measure="value",
                   tolerance=Tolerance.from_decimals(1, fixed_on=FIXED_ON))


def key():
    return AnswerKey(panel(PUBLISHED), source="source:synthetic")


def test_a_tolerance_comes_from_the_published_precision():
    tolerance = Tolerance.from_decimals(1, fixed_on=FIXED_ON)
    assert tolerance.absolute == pytest.approx(0.05)
    assert tolerance.admits(0.05) and not tolerance.admits(0.0501)


def test_matching_values_pass():
    result = key().compare(panel([("North", 2015, 25.04), ("South", 2015, 49.96)]), CHECK)
    assert result.passed and result.compared == 2 and result.mismatches == ()


def test_a_value_outside_tolerance_fails_and_is_named():
    result = key().compare(panel([("North", 2015, 25.2), ("South", 2015, 50.0)]), CHECK)
    assert not result.passed
    assert result.max_abs_difference == pytest.approx(0.2)
    assert [m.key["area"] for m in result.mismatches] == ["North"]


def test_a_missing_value_fails_and_an_extra_value_is_counted():
    result = key().compare(panel([("North", 2015, 25.0), ("West", 2015, 1.0)]), CHECK)
    assert not result.passed and result.missing == 1 and result.extra == 1


def test_nothing_compared_is_not_a_pass():
    result = key().compare(panel([("West", 2015, 1.0)]), CHECK)
    assert result.compared == 0 and not result.passed


def test_the_answer_key_has_no_way_to_read_its_values():
    sealed = key()
    assert "25.0" not in repr(sealed)
    public = [name for name in dir(sealed) if not name.startswith("_")]
    assert public == ["compare"]


@pytest.mark.parametrize("results, window", [
    ({1: True, 3: True, 5: True}, ()),
    ({1: False, 3: False, 5: False}, (1,)),
    ({1: True, 3: False, 5: False}, (2, 3)),
    ({1: True, 3: True, 5: False}, (4, 5)),
])
def test_the_first_failing_checkpoint_bounds_the_fault(results, window):
    assert blame_window(results, step_count=6) == window


def test_a_divergence_closes_only_with_a_cause_and_an_explanation():
    with pytest.raises(ValidationError, match="without a cause"):
        Divergence(id="D1", checkpoint="K4", size=0.2, tolerance=0.05, suspected_steps=(4, 5),
                   status=DivergenceStatus.EXPLAINED)


def test_a_publisher_side_divergence_cannot_be_corrected():
    with pytest.raises(ValidationError, match="outside our code"):
        Divergence(id="D1", checkpoint="K4", size=0.2, tolerance=0.05, suspected_steps=(4, 5),
                   status=DivergenceStatus.CORRECTED, cause=CauseClass.UNPUBLISHED_STEP,
                   explanation="model step not published", evidence=("run:1",))


def test_the_register_is_append_only_and_keeps_history():
    register = DivergenceRegister()
    register.record(Divergence(id="D1", checkpoint="K4", size=0.2, tolerance=0.05, suspected_steps=(4, 5)))
    with pytest.raises(ValueError, match="already exists"):
        register.record(Divergence(id="D1", checkpoint="K4", size=0.1, tolerance=0.05, suspected_steps=(4,)))
    register.update("D1", status=DivergenceStatus.EXPLAINED, cause=CauseClass.VINTAGE_MISMATCH,
                    explanation="the publisher used the 2015 edition")
    assert register.open() == ()
    assert [d.status for d in register.history("D1")] == [DivergenceStatus.OPEN, DivergenceStatus.EXPLAINED]


def test_a_divergence_enters_the_register_open():
    with pytest.raises(ValueError, match="enters the register open"):
        DivergenceRegister().record(Divergence(
            id="D1", checkpoint="K4", size=0.2, tolerance=0.05, suspected_steps=(4,),
            status=DivergenceStatus.ACCEPTED, cause=CauseClass.ROUNDING, explanation="e"))
