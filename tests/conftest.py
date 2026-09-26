"""Small builders for the tests. The data is synthetic and says nothing about any real country."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

import pyarrow as pa
import pyarrow.compute as pc
import pytest
from pydantic import BaseModel, ConfigDict

from athena.citations import Citation
from athena.frames import Column, Frame, Manifest
from athena.reference import Grouping, membership_frame
from athena.steps import Invariant, Step
from athena.vocab import Concept, DType, Profile, ReproClass, Role

FIXED_ON = date(2026, 9, 25)


def citation(quote: str = "Regional aggregates are population-weighted averages.") -> Citation:
    return Citation(document="source:synthetic-method-note", locator="p. 3, para 2", quote=quote)


def panel(rows: list[tuple[str, int, float]], *, measure: str = "value", unit: str = "percent",
          produced_by: str = "shell:test-input@0.1.0") -> Frame:
    manifest = Manifest(
        profile=Profile.PANEL,
        columns=(
            Column(name="area", dtype=DType.STRING, role=Role.ENTITY, concept=Concept.REF_AREA),
            Column(name="year", dtype=DType.INT64, role=Role.TIME, concept=Concept.TIME_PERIOD),
            Column(name=measure, dtype=DType.FLOAT64, role=Role.MEASURE, unit=unit, concept=Concept.OBS_VALUE),
        ),
        keys=("area", "year"),
        produced_by=produced_by,
        repro_class=ReproClass.A,
    )
    table = pa.table({
        "area": pa.array([r[0] for r in rows], pa.string()),
        "year": pa.array([r[1] for r in rows], pa.int64()),
        measure: pa.array([r[2] for r in rows], pa.float64()),
    })
    return Frame(table, manifest)


REGION_ROWS = [("AAA", "North", "region"), ("BBB", "North", "region"), ("CCC", "South", "region")]
WRONG_REGION_ROWS = [("AAA", "North", "region"), ("BBB", "South", "region"), ("CCC", "South", "region")]


def regions(rows=REGION_ROWS) -> Frame:
    return membership_frame(rows, produced_by="shell:test-input@0.1.0")


REGIONS = Grouping(id="grouping:synthetic-regions", title="Synthetic regions", publisher="Test",
                   levels=("region",), disjoint=True, members=regions().content_hash())

VALUES = [("AAA", 2015, 10.0), ("BBB", 2015, 30.0), ("CCC", 2015, 50.0)]
POPULATION = [("AAA", 2015, 1.0), ("BBB", 2015, 3.0), ("CCC", 2015, 2.0)]


class GroupMeanParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    level: str


def _members(groups: Frame, level: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in groups.table.to_pylist():
        if row["level"] == level:
            out.setdefault(row["group"], []).append(row["member"])
    return out


def _between_member_values(inputs: Mapping[str, Frame], output: Frame, params: BaseModel) -> bool:
    values = inputs["values"].table
    members_of = _members(inputs["groups"], params.level)
    for row in output.table.to_pylist():
        members = members_of[row["area"]]
        member_values = values.filter(pc.is_in(values.column("area"), pa.array(members))).column("value")
        if not pc.min(member_values).as_py() - 1e-9 <= row["value"] <= pc.max(member_values).as_py() + 1e-9:
            return False
    return True


class WeightedGroupMean(Step):
    """A test-only step: the population-weighted mean of member values within each group at one level."""

    ID = "shell:weighted-group-mean"
    VERSION = "0.1.0"
    TITLE = "Weighted group mean"
    SUMMARY = "Aggregate member values to groups, weighting each member by a second measure."
    INPUTS = {"values": Profile.PANEL, "weights": Profile.PANEL, "groups": Profile.MEMBERSHIP}
    OUTPUT = Profile.PANEL
    Parameters = GroupMeanParameters

    def run(self, inputs, params):
        values = {(r["area"], r["year"]): r["value"] for r in inputs["values"].table.to_pylist()}
        weights = {(r["area"], r["year"]): r["value"] for r in inputs["weights"].table.to_pylist()}
        rows = []
        for group, members in sorted(_members(inputs["groups"], params.level).items()):
            for year in sorted({y for (_, y) in values}):
                pairs = [(values[(m, year)], weights[(m, year)]) for m in members if (m, year) in values]
                total = sum(w for _, w in pairs)
                rows.append((group, year, sum(v * w for v, w in pairs) / total))
        return panel(rows, produced_by=self.ref())

    def invariants(self):
        return (Invariant("between-member-values", "A weighted mean lies between its members' values.",
                          _between_member_values),)


BY_REGION = {"level": "region"}


@pytest.fixture
def values() -> Frame:
    return panel(VALUES)


@pytest.fixture
def weights() -> Frame:
    return panel(POPULATION, unit="persons")


@pytest.fixture
def groups() -> Frame:
    return regions()
