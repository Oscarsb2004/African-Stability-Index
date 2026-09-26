"""The build: stored snapshots in, frames and step receipts out. It never sees a published answer."""

from __future__ import annotations

from dataclasses import dataclass, field

from athena.frames import Frame
from athena.steps import StepResult
from athena.store import Store
from mdg.codes import code_map, load_aliases
from mdg.method import CARD
from mdg.readers import GroupingsDocReader, IpuClassificationReader, LdcListReader, LldcProfilesReader, M49Reader
from mdg.sources import GROUPINGS, IPU_CLASSIFICATION, LDC_2014, LLDC_2014, M49_OVERVIEW
from mdg.steps import CodeCountries, CodeMembers, RatioByCountry, ReplaceGroups, RoundValues, SumRatioByGroup

INPUT_RECIPES = (IPU_CLASSIFICATION, GROUPINGS, M49_OVERVIEW, LDC_2014, LLDC_2014)


@dataclass
class Build:
    frames: dict[str, Frame] = field(default_factory=dict)
    results: list[StepResult] = field(default_factory=list)
    parsed: dict[str, str] = field(default_factory=dict)
    snapshots: dict[str, str] = field(default_factory=dict)
    mapping: dict[str, str] = field(default_factory=dict)

    def run(self, name: str, step, inputs: dict[str, Frame], parameters: dict) -> Frame:
        frame, result = step()(inputs, parameters)
        self.frames[name] = frame
        self.results.append(result)
        return frame


def build(store: Store) -> Build:
    b = Build()
    data = {}
    for recipe in INPUT_RECIPES:
        snapshot = store.latest_snapshot(recipe.ref)
        b.snapshots[recipe.id] = snapshot.hash
        data[recipe.id] = store.get(snapshot.hash)

    counts = IpuClassificationReader().parse(data[IPU_CLASSIFICATION.id], IPU_CLASSIFICATION)
    names = GroupingsDocReader().parse(data[GROUPINGS.id], GROUPINGS)
    m49 = M49Reader().parse(data[M49_OVERVIEW.id], M49_OVERVIEW)
    b.parsed[b.snapshots[IPU_CLASSIFICATION.id]] = counts.content_hash()
    b.parsed[b.snapshots[GROUPINGS.id]] = names.content_hash()
    b.frames["counts-by-name"], b.frames["groups-by-name"] = counts, names

    dated = [LdcListReader().parse(data[LDC_2014.id], LDC_2014),
             LldcProfilesReader().parse(data[LLDC_2014.id], LLDC_2014)]
    for recipe, frame in zip((LDC_2014, LLDC_2014), dated):
        b.parsed[b.snapshots[recipe.id]] = frame.content_hash()

    everyone = set(counts.column("name").to_pylist()) | set(names.column("member").to_pylist())
    for frame in dated:
        everyone |= set(frame.column("member").to_pylist())
    b.mapping = code_map(everyone, m49, load_aliases())
    coded = b.run("counts", CodeCountries, {"counts": counts}, {"mapping": b.mapping})
    listed = b.run("groups-listed", CodeMembers, {"groups": names}, {"mapping": b.mapping})
    ldc = b.run("ldc-2015", CodeMembers, {"groups": dated[0]}, {"mapping": b.mapping})
    lldc = b.run("lldc-2015", CodeMembers, {"groups": dated[1]}, {"mapping": b.mapping})
    groups = b.run("groups-ldc", ReplaceGroups, {"groups": listed, "replacement": ldc}, {})
    groups = b.run("groups", ReplaceGroups, {"groups": groups, "replacement": lldc}, {})
    b.run("country-percent", RatioByCountry, {"counts": coded}, {})
    regional = b.run("group-percent", SumRatioByGroup, {"counts": coded, "groups": groups}, {})
    b.run("group-percent-rounded", RoundValues, {"values": regional}, {"rounding": CARD.rounding})
    return b
