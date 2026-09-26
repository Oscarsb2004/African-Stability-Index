"""Index trees have honest weights, and justifications are quoted, not paraphrased."""

import pytest
from pydantic import ValidationError

from athena.indicators import Component, CompositeIndex, Justification
from athena.vocab import Criterion, Origin, Stance

from conftest import citation


def leaf(name, weight, indicator=None):
    return Component(name=name, weight=weight, indicator=indicator or f"indicator:{name}")


def index(root, **changes):
    fields = dict(id="index:synthetic", title="Synthetic index", publisher="Test", origin=Origin.PUBLISHED,
                  method="method:synthetic", normalisation="min-max", aggregation="arithmetic mean", root=root)
    return CompositeIndex(**(fields | changes))


def test_weights_under_a_group_sum_to_one():
    with pytest.raises(ValidationError, match="sum to"):
        Component(name="root", weight=1, children=(leaf("a", 0.5), leaf("b", 0.6)))


def test_a_component_is_a_leaf_or_a_group():
    with pytest.raises(ValidationError, match="either an indicator or a group"):
        Component(name="x", weight=1)
    with pytest.raises(ValidationError, match="either an indicator or a group"):
        Component(name="x", weight=1, indicator="indicator:x", children=(leaf("a", 1.0),))


def test_an_indicator_appears_once_in_an_index():
    root = Component(name="root", weight=1, children=(leaf("a", 0.5), leaf("b", 0.5, "indicator:a")))
    with pytest.raises(ValidationError, match="appears twice"):
        index(root)


def test_effective_weights_multiply_down_the_tree():
    health = Component(name="health", weight=0.5, children=(leaf("a", 0.5), leaf("b", 0.5)))
    root = Component(name="root", weight=1, children=(health, leaf("c", 0.5)))
    assert index(root).effective_weights() == {"indicator:a": 0.25, "indicator:b": 0.25, "indicator:c": 0.5}


def test_an_own_index_is_derived():
    root = Component(name="root", weight=1, children=(leaf("a", 1.0),))
    assert index(root, origin=Origin.OWN).derived and not index(root).derived


def test_a_justification_is_filed_by_criterion_with_its_quote():
    j = Justification(subject="indicator:a", criterion=Criterion.RELEVANCE, stance=Stance.SUPPORTS,
                      claim="Chosen because it tracks outcomes directly.", citation=citation())
    assert j.citation.quote
    with pytest.raises(ValidationError):
        Justification(subject="indicator:a", criterion="popularity", stance=Stance.SUPPORTS, claim="c",
                      citation=citation())
