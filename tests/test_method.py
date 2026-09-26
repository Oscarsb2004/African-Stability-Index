"""A method card cites the text behind every published step and logs every reading."""

import pytest
from pydantic import ValidationError

from athena.method import MethodCard, MethodStep, PublishedValue, Reading
from athena.vocab import Origin

from conftest import citation

STEPS = (
    MethodStep(number=1, name="Acquire", action="Take country values.", citation=citation("Country data are ...")),
    MethodStep(number=2, name="Aggregate", action="Population-weighted mean.", citation=citation()),
)


def card(**changes):
    fields = dict(id="method:synthetic-regional-mean", title="Regional mean", subject="indicator:synthetic",
                  origin=Origin.PUBLISHED, steps=STEPS)
    return MethodCard(**(fields | changes))


def test_steps_are_numbered_in_order():
    with pytest.raises(ValidationError, match="numbered 1..n"):
        card(steps=(STEPS[1], STEPS[0]))


def test_a_published_method_cites_every_step():
    uncited = MethodStep(number=2, name="Aggregate", action="Mean.")
    with pytest.raises(ValidationError, match="uncited: \\[2\\]"):
        card(steps=(STEPS[0], uncited))


def test_an_own_method_states_its_formula_and_needs_no_citations():
    own_steps = (MethodStep(number=1, name="Ratio", action="Divide A by B."),)
    with pytest.raises(ValidationError, match="states its formula"):
        card(origin=Origin.OWN, steps=own_steps)
    assert card(origin=Origin.OWN, steps=own_steps, formula="A / B").formula == "A / B"


def test_a_reading_needs_real_alternatives_and_adopts_one_of_them():
    with pytest.raises(ValidationError, match="at least two options"):
        Reading(step=1, sentence=citation(), options=("only",), adopted="only", reason="r")
    with pytest.raises(ValidationError, match="must be one of the options"):
        Reading(step=1, sentence=citation(), options=("a", "b"), adopted="c", reason="r")


def test_readings_and_published_values_must_point_at_real_steps():
    reading = Reading(step=3, sentence=citation(), options=("a", "b"), adopted="a", reason="r")
    with pytest.raises(ValidationError, match="step 3 is referred to"):
        card(readings=(reading,))


def test_published_values_fix_where_checkpoints_can_go():
    values = (PublishedValue(name="regional table", after_step=2, description="d", citation=citation()),
              PublishedValue(name="country table", after_step=1, description="d", citation=citation()))
    assert card(published_values=values).checkpoint_steps() == (1, 2)


def test_readings_the_owner_has_not_ruled_on_are_listed():
    reading = Reading(step=2, sentence=citation(), options=("a", "b"), adopted="a", reason="r")
    assert card(readings=(reading,)).unruled_readings == (reading,)
