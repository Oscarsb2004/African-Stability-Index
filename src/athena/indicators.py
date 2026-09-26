"""Indicators, composite indices, and the justifications behind them.

An `Indicator` is one published measure, such as MDG 4.1. A `CompositeIndex` is a tree of components with
declared normalisation, weights and aggregation - the structure every state-of-the-art index shares.

A `Justification` records why a publisher included, weighted or treated an indicator the way it did, quoted from
their methodology. Collected from the first replication onward, these become the evidence base for building
indices of our own (only after replication is proven) and the training data for a stage 4 model.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field, model_validator

from athena.base import Definition, Record
from athena.ids import Id
from athena.method import Citation
from athena.vocab import Criterion, Origin, ReproClass, Stance

WEIGHT_EPSILON = 1e-9


class Indicator(Definition):
    KIND: ClassVar[str] = "indicator"

    framework: str
    code: str
    unit: str
    method: Id
    sources: tuple[Id, ...]
    repro_class: ReproClass


class Component(Record):
    """A node in an index tree: either an indicator (a leaf) or a group of components."""

    name: str
    weight: float = Field(gt=0)
    indicator: Id | None = None
    children: tuple[Component, ...] = ()

    @model_validator(mode="after")
    def _leaf_or_group(self) -> Component:
        if (self.indicator is None) == (not self.children):
            raise ValueError(f"component {self.name!r} is either an indicator or a group, not both or neither")
        if self.children:
            total = sum(c.weight for c in self.children)
            if abs(total - 1.0) > WEIGHT_EPSILON:
                raise ValueError(f"weights under {self.name!r} sum to {total}, not 1")
            names = [c.name for c in self.children]
            if len(names) != len(set(names)):
                raise ValueError(f"component names under {self.name!r} repeat")
        return self

    def leaves(self) -> tuple[Component, ...]:
        if self.indicator is not None:
            return (self,)
        return tuple(leaf for child in self.children for leaf in child.leaves())


class CompositeIndex(Definition):
    KIND: ClassVar[str] = "index"

    publisher: str
    origin: Origin
    method: Id
    normalisation: str
    aggregation: str
    root: Component

    @model_validator(mode="after")
    def _root_is_a_group(self) -> CompositeIndex:
        if self.root.indicator is not None:
            raise ValueError("an index is a group of components, not a single indicator")
        indicators = [leaf.indicator for leaf in self.root.leaves()]
        if len(indicators) != len(set(indicators)):
            raise ValueError("an indicator appears twice in the index tree")
        return self

    @property
    def derived(self) -> bool:
        return self.origin is Origin.OWN

    def effective_weights(self) -> dict[str, float]:
        """Each indicator's share of the final score: the product of the weights on its path."""
        weights: dict[str, float] = {}

        def walk(node: Component, share: float) -> None:
            if node.indicator is not None:
                weights[node.indicator] = share
            for child in node.children:
                walk(child, share * child.weight)

        walk(self.root, 1.0)
        return weights


class Justification(Record):
    """One reason a publisher gives for a construction choice, quoted and filed by criterion."""

    subject: Id
    criterion: Criterion
    stance: Stance
    claim: str
    citation: Citation
