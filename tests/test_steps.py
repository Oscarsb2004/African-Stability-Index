"""Calling a step checks its inputs, its output and its invariants around the work."""

import pytest
from pydantic import ValidationError

from athena.steps import InvariantBroken, ShellRegistry, Step
from athena.vocab import Profile

from conftest import REGIONS, WeightedGroupMean, panel


def test_a_step_aggregates_and_reports_what_it_did(values, weights):
    output, result = WeightedGroupMean()({"values": values, "weights": weights}, {"grouping": REGIONS})
    by_area = {r["area"]: r["value"] for r in output.table.to_pylist()}
    assert by_area == {"North": 25.0, "South": 50.0}
    assert result.step == "shell:weighted-group-mean@0.1.0"
    assert result.invariants_checked == ("between-member-values",)
    assert result.inputs == {"values": values.content_hash(), "weights": weights.content_hash()}
    assert result.output == output.content_hash()


def test_the_same_inputs_give_the_same_receipt(values, weights):
    call = lambda: WeightedGroupMean()({"values": values, "weights": weights}, {"grouping": REGIONS})[1]
    assert call() == call()


def test_a_step_refuses_missing_or_extra_inputs(values):
    with pytest.raises(ValueError, match="takes inputs"):
        WeightedGroupMean()({"values": values}, {"grouping": REGIONS})


def test_a_step_refuses_undeclared_parameters(values, weights):
    with pytest.raises(ValidationError):
        WeightedGroupMean()({"values": values, "weights": weights}, {"grouping": REGIONS, "round": 1})


class Mislabelled(WeightedGroupMean):
    ID = "shell:mislabelled"

    def run(self, inputs, params):
        return panel([("North", 2015, 25.0)])


class Broken(WeightedGroupMean):
    """A planted fault: returns a value outside its members' range."""

    ID = "shell:broken"

    def run(self, inputs, params):
        return panel([("North", 2015, 99.0), ("South", 2015, 50.0)], produced_by=self.ref())


def test_a_step_must_sign_its_output(values, weights):
    with pytest.raises(ValueError, match="must name produced_by"):
        Mislabelled()({"values": values, "weights": weights}, {"grouping": REGIONS})


def test_a_planted_fault_breaks_the_invariant(values, weights):
    with pytest.raises(InvariantBroken, match="between-member-values"):
        Broken()({"values": values, "weights": weights}, {"grouping": REGIONS})


def test_the_registry_holds_each_shell_once_and_only_shell_ids():
    registry = ShellRegistry()
    registry.register(WeightedGroupMean)
    assert "shell:weighted-group-mean" in registry
    with pytest.raises(ValueError, match="already registered"):
        registry.register(WeightedGroupMean)

    class NotAShell(WeightedGroupMean):
        ID = "method:nope"

    with pytest.raises(ValueError, match="must be a shell id"):
        registry.register(NotAShell)
    with pytest.raises(KeyError, match="not a registered shell"):
        registry.get("shell:unknown")


def test_a_card_describes_the_step_for_people_and_programs():
    card = WeightedGroupMean.card()
    assert card.inputs == {"values": Profile.PANEL, "weights": Profile.PANEL}
    assert card.invariants == ("between-member-values",)
    assert "grouping" in card.parameters_schema["properties"]
