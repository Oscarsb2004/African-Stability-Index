"""Build steps for indicator 3.3. Each carries out one method step and declares the invariants it keeps.

They are project-local under decision P6: a step moves into the shared package only when a second index uses it.
"""

from __future__ import annotations

from collections.abc import Mapping

import pyarrow as pa
from pydantic import BaseModel, ConfigDict, Field

from athena.frames import Column, Frame, Manifest
from athena.reference import GROUP, LEVEL, MEMBER, membership_frame
from athena.rounding import Rounding
from athena.steps import Invariant, Step
from athena.vocab import Concept, DType, Profile, ReproClass, Role

EPSILON = 1e-9


class _Params(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


# ── Codes ────────────────────────────────────────────────────────────────────────────────────────────────────

class CodeParameters(_Params):
    mapping: dict[str, str] = Field(description="Name to code, built by mdg.codes from M49 and the alias table")


class CodeCountries(Step):
    ID = "shell:mdg-code-countries"
    VERSION = "0.1.0"
    TITLE = "Give each country its code"
    SUMMARY = "Replace publisher country names with ISO codes; the name is kept as a label."
    INPUTS = {"counts": Profile.CROSS_SECTION}
    OUTPUT = Profile.CROSS_SECTION
    Parameters = CodeParameters

    def run(self, inputs, params):
        source = inputs["counts"]
        rows = source.table.to_pylist()
        manifest = Manifest(
            profile=Profile.CROSS_SECTION,
            columns=(Column(name="area", dtype=DType.STRING, role=Role.ENTITY, concept=Concept.REF_AREA),
                     Column(name="name", dtype=DType.STRING, role=Role.LABEL),
                     *[c for c in source.manifest.columns if c.name not in ("name",)]),
            keys=("area",), produced_by=self.ref(), repro_class=source.manifest.repro_class,
            period=source.manifest.period, inputs=(source.content_hash(),),
        )
        table = pa.table({"area": [params.mapping[r["name"]] for r in rows], "name": [r["name"] for r in rows],
                          **{c.name: source.table.column(c.name) for c in source.manifest.columns if c.name != "name"}})
        return Frame(table, manifest)

    def invariants(self):
        return (Invariant("row-count-kept", "Coding never adds or drops a country.",
                          lambda i, o, p: o.num_rows == i["counts"].num_rows),)


class CodeMembers(Step):
    ID = "shell:mdg-code-members"
    VERSION = "0.1.0"
    TITLE = "Give each group member its code"
    SUMMARY = "Replace member names in a membership list with ISO codes."
    INPUTS = {"groups": Profile.MEMBERSHIP}
    OUTPUT = Profile.MEMBERSHIP
    Parameters = CodeParameters

    def run(self, inputs, params):
        rows = {(params.mapping[r[MEMBER]], r[GROUP], r[LEVEL]) for r in inputs["groups"].table.to_pylist()}
        return membership_frame(sorted(rows), produced_by=self.ref())

    def invariants(self):
        def same_groups(i, o, p):
            groups = lambda f: {(r[GROUP], r[LEVEL]) for r in f.table.to_pylist()}
            return groups(i["groups"]) == groups(o)
        return (Invariant("groups-kept", "Coding never adds or removes a group.", same_groups),)


# ── Ratios ───────────────────────────────────────────────────────────────────────────────────────────────────

def _percent_frame(rows: list[tuple[str, float, int]], produced_by: str, period: str, entity: str,
                   extra: tuple[Column, ...] = (), extra_values: dict | None = None) -> Frame:
    manifest = Manifest(
        profile=Profile.CROSS_SECTION,
        columns=(Column(name=entity, dtype=DType.STRING, role=Role.ENTITY),
                 Column(name="value", dtype=DType.FLOAT64, role=Role.MEASURE, unit="percent"),
                 Column(name="countries", dtype=DType.INT64, role=Role.MEASURE, unit="countries",
                        description="Countries with both counts known"),
                 *extra),
        keys=(entity,), produced_by=produced_by, repro_class=ReproClass.A, period=period,
    )
    table = {entity: pa.array([r[0] for r in rows], pa.string()),
             "value": pa.array([r[1] for r in rows], pa.float64()),
             "countries": pa.array([r[2] for r in rows], pa.int64())}
    return Frame(pa.table(table | (extra_values or {})), manifest)


class RatioParameters(_Params):
    numerator: str = "women"
    denominator: str = "seats"
    scale: float = 100.0


def _known(rows: list[dict], p: RatioParameters) -> list[dict]:
    """Method step 4: no adjustment for missing values. A country without both counts is left out."""
    return [r for r in rows if r[p.numerator] is not None and r[p.denominator]]


class RatioByCountry(Step):
    ID = "shell:mdg-ratio-by-country"
    VERSION = "0.1.0"
    TITLE = "Seats held by women, per country"
    SUMMARY = "Divide one count by another for each country, as a percentage."
    INPUTS = {"counts": Profile.CROSS_SECTION}
    OUTPUT = Profile.CROSS_SECTION
    Parameters = RatioParameters

    def run(self, inputs, params):
        rows = _known(inputs["counts"].table.to_pylist(), params)
        return _percent_frame([(r["area"], params.scale * r[params.numerator] / r[params.denominator], 1)
                               for r in rows], self.ref(), inputs["counts"].manifest.period, "area")

    def invariants(self):
        return (Invariant("between-0-and-scale", "A share of seats lies between 0 and 100.",
                          lambda i, o, p: all(0 <= v <= p.scale for v in o.column("value").to_pylist())),)


class SumRatioParameters(RatioParameters):
    levels: tuple[str, ...] = ("world", "development", "region", "subregion", "alternate", "special")


class SumRatioByGroup(Step):
    """Method step 3: "Regional averages are determined by dividing the total number of women members by the total
    number of seats filled in single or lower chambers of parliament per region." """

    ID = "shell:mdg-sum-ratio-by-group"
    VERSION = "0.1.0"
    TITLE = "Seats held by women, per group"
    SUMMARY = "Sum a numerator and a denominator over each group's members, then divide."
    INPUTS = {"counts": Profile.CROSS_SECTION, "groups": Profile.MEMBERSHIP}
    OUTPUT = Profile.CROSS_SECTION
    Parameters = SumRatioParameters

    def run(self, inputs, params):
        known = {r["area"]: r for r in _known(inputs["counts"].table.to_pylist(), params)}
        totals: dict[str, list] = {}
        for m in inputs["groups"].table.to_pylist():
            if m[LEVEL] in params.levels and m[MEMBER] in known:
                t = totals.setdefault(m[GROUP], [m[LEVEL], 0, 0, 0])
                t[1] += known[m[MEMBER]][params.numerator]
                t[2] += known[m[MEMBER]][params.denominator]
                t[3] += 1
        rows = sorted(totals.items())
        extra = (Column(name="level", dtype=DType.STRING, role=Role.CATEGORY),
                 Column(name=params.numerator, dtype=DType.INT64, role=Role.MEASURE, unit="seats"),
                 Column(name=params.denominator, dtype=DType.INT64, role=Role.MEASURE, unit="seats"))
        values = {"level": pa.array([t[0] for _, t in rows], pa.string()),
                  params.numerator: pa.array([t[1] for _, t in rows], pa.int64()),
                  params.denominator: pa.array([t[2] for _, t in rows], pa.int64())}
        return _percent_frame([(g, params.scale * t[1] / t[2], t[3]) for g, t in rows], self.ref(),
                              inputs["counts"].manifest.period, "group", extra, values)

    def invariants(self):
        def between_members(i, o, p):
            known = {r["area"]: r for r in _known(i["counts"].table.to_pylist(), p)}
            ratios: dict[str, list[float]] = {}
            for m in i["groups"].table.to_pylist():
                if m[MEMBER] in known:
                    r = known[m[MEMBER]]
                    ratios.setdefault(m[GROUP], []).append(p.scale * r[p.numerator] / r[p.denominator])
            return all(min(ratios[g]) - EPSILON <= v <= max(ratios[g]) + EPSILON
                       for g, v in zip(o.column("group").to_pylist(), o.column("value").to_pylist()))
        return (Invariant("between-member-ratios", "A seat-weighted share lies between its members' shares.",
                          between_members),)


# ── Rounding ─────────────────────────────────────────────────────────────────────────────────────────────────

class RoundParameters(_Params):
    rounding: Rounding


class RoundValues(Step):
    ID = "shell:mdg-round-values"
    VERSION = "0.1.0"
    TITLE = "Round to the published precision"
    SUMMARY = "Round the value column by the method card's rounding rule."
    INPUTS = {"values": Profile.CROSS_SECTION}
    OUTPUT = Profile.CROSS_SECTION
    Parameters = RoundParameters

    def run(self, inputs, params):
        source = inputs["values"]
        rounded = [params.rounding.apply(v) for v in source.column("value").to_pylist()]
        table = source.table.set_column(source.table.schema.get_field_index("value"), "value",
                                        pa.array(rounded, pa.float64()))
        manifest = source.manifest.model_copy(update={"produced_by": self.ref(), "inputs": (source.content_hash(),)})
        return Frame(table, manifest)

    def invariants(self):
        def within_half_unit(i, o, p):
            half = 0.5 * 10.0 ** -p.rounding.decimals + EPSILON
            return all(abs(a - b) <= half for a, b in zip(i["values"].column("value").to_pylist(),
                                                          o.column("value").to_pylist()))
        return (Invariant("within-half-unit", "Rounding moves a value by at most half a unit in the last place.",
                          within_half_unit),)


STEPS = (CodeCountries, CodeMembers, RatioByCountry, SumRatioByGroup, RoundValues)
