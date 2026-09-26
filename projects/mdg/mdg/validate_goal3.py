"""Validation for Goal 3 (section S43). Tolerances fixed on `mdg.answers.TOLERANCE_FIXED_ON`, before comparing.

For 3.1 there are five checkpoints per level and year, and together they separate three possible faults:
  K0f, K0m  our gross enrolment ratios against UIS's own, same edition   -> our arithmetic
  K1        our country ratios against the MDG database of July 2015      -> revisions since 2015
  K3, K3r   our group ratios against the 2015 annex, before and after rounding -> grouping, weights, and the
            publisher's unpublished estimates
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pyarrow as pa

from athena.frames import Column, Frame, Manifest
from athena.store import Store
from athena.validation import Checkpoint, Comparison, Divergence, DivergenceRegister, Tolerance, blame_window
from athena.vocab import CauseClass, DType, Profile, ReproClass, Role
from mdg import answers
from mdg.codes import code_map, load_aliases
from mdg.goal3 import YEARS
from mdg.method import CARD_31, CARD_32, verify_quotes
from mdg.pipeline import Build
from mdg.readers import AnnexTableReader, M49Reader, MdgSeriesReader, html_text
from mdg.sources import ANNEX, LEVELS, M49_OVERVIEW, METADATA, SERIES, UIS_GER

FIXED = answers.TOLERANCE_FIXED_ON
ARITHMETIC = Tolerance(absolute=0.01, basis="UIS publishes unrounded ratios; 0.01 points allows float noise",
                       fixed_on=FIXED)
TWO_DECIMALS = Tolerance.from_decimals(2, fixed_on=FIXED)
EXACT = Tolerance(absolute=0.0, basis="rounded values match exactly", fixed_on=FIXED)


def checkpoints(part: str, year: int) -> dict[str, Checkpoint]:
    tag = f"{part}-{year}"
    return {
        "K0f": Checkpoint(id=f"K0f-{tag}", after_step=1, published_value="UIS GER female", keys=("area",),
                          measure="value", tolerance=ARITHMETIC),
        "K0m": Checkpoint(id=f"K0m-{tag}", after_step=1, published_value="UIS GER male", keys=("area",),
                          measure="value", tolerance=ARITHMETIC),
        "K1": Checkpoint(id=f"K1-{tag}", after_step=2, published_value="country ratios, 2015 edition",
                         keys=("area",), measure="value", tolerance=TWO_DECIMALS),
        "K3": Checkpoint(id=f"K3-{tag}", after_step=3, published_value="regional table", keys=("group",),
                         measure="value", tolerance=TWO_DECIMALS),
        "K3r": Checkpoint(id=f"K3r-{tag}", after_step=3, published_value="regional table, rounded", keys=("group",),
                          measure="value", tolerance=EXACT),
    }


def _k0(c: Comparison) -> tuple[CauseClass | None, str]:
    values = [m for m in c.mismatches if m.side == "value"]
    if values:
        return None, (f"{len(values)} ratio(s) UIS publishes differ from its own published enrolment over its own "
                      "published population; unexplained, possibly an inconsistency on the publisher's side.")
    return CauseClass.UNPUBLISHED_STEP, ("UIS publishes a ratio for some countries without publishing both counts "
                                         "behind it, so those countries cannot enter our totals.")


PROPOSED = {
    "K0f": _k0,
    "K0m": _k0,
    "K1": lambda c: (CauseClass.VINTAGE_MISMATCH,
                     "today's UIS counts are revised against the July 2015 edition; some 2015 countries have no "
                     "current counts."),
    "K3": lambda c: (CauseClass.VINTAGE_MISMATCH,
                     "revisions since 2015 (see K1), plus the publisher's non-publishable estimates for missing "
                     "countries, which we cannot reproduce."),
    "K3r": lambda c: (CauseClass.VINTAGE_MISMATCH, "follows from K3; rounding is not the cause."),
}


def _as_value(frame: Frame, column: str) -> Frame:
    """The same numbers with one measure column renamed to value, so a checkpoint can read it. No arithmetic."""
    entity = frame.manifest.keys[0]
    manifest = Manifest(
        profile=Profile.CROSS_SECTION,
        columns=(Column(name=entity, dtype=DType.STRING, role=Role.ENTITY),
                 Column(name="value", dtype=DType.FLOAT64, role=Role.MEASURE, unit="percent")),
        keys=(entity,), produced_by=frame.manifest.produced_by, repro_class=ReproClass.B,
        period=frame.manifest.period,
    )
    return Frame(pa.table({entity: frame.column(entity), "value": frame.column(column)}), manifest)


@dataclass
class Goal3:
    comparisons: dict[str, Comparison] = field(default_factory=dict)
    published: dict[str, dict[str, float]] = field(default_factory=dict)
    windows: dict[str, tuple[int, ...]] = field(default_factory=dict)
    register: DivergenceRegister = field(default_factory=DivergenceRegister)
    series_mapping: dict[str, str] = field(default_factory=dict)
    hosted_32: dict[str, dict[str, float]] = field(default_factory=dict)
    coverage_32: dict[int, int] = field(default_factory=dict)
    quote_problems: list[str] = field(default_factory=list)


def validate_goal3(b: Build, store: Store) -> Goal3:
    v = Goal3()
    get = lambda recipe: store.get(store.latest_snapshot(recipe.ref).hash)
    m49 = M49Reader().parse(get(M49_OVERVIEW), M49_OVERVIEW)
    series_names = set()
    for srid in (611, 613, 614, 722):
        series_names |= set(MdgSeriesReader().parse(get(SERIES[srid]), SERIES[srid]).column("name").to_pylist())
    v.series_mapping = code_map(series_names, m49, load_aliases())
    annex = get(ANNEX)
    texts = {"MDG 2015 statistical annex": " ".join(AnnexTableReader().pages(annex))}
    for srid in (611, 722):
        texts[f"MDG metadata series {srid}"] = html_text(get(METADATA[srid]))
        texts[f"MDG database series {srid}"] = html_text(get(SERIES[srid]))
    v.quote_problems = verify_quotes(CARD_31, texts) + verify_quotes(CARD_32, texts)

    for part, (level, *_counts, gf, gm, srid) in LEVELS.items():
        for year in YEARS:
            name, tag, cps = f"3.1{part}-{year}", f"{part}-{year}", checkpoints(part, year)
            ger = answers.uis_ger(get(UIS_GER[part]), gf, gm, year)
            country_key, v.published[f"country-{tag}"] = answers.mdg_series(get(SERIES[srid]), v.series_mapping, year)
            region_key, v.published[f"region-{tag}"] = answers.annex_part(annex, "3.1", part, year)
            ours_ger = b.frames[f"{name}-ger"]
            results = {
                "K0f": ger["female"].compare(_as_value(ours_ger, "female"), cps["K0f"], limit=300),
                "K0m": ger["male"].compare(_as_value(ours_ger, "male"), cps["K0m"], limit=300),
                "K1": country_key.compare(b.frames[f"{name}-country"], cps["K1"], limit=300),
                "K3": region_key.compare(b.frames[f"{name}-group"], cps["K3"], limit=300),
                "K3r": region_key.compare(b.frames[f"{name}-group-rounded"], cps["K3r"], limit=300),
            }
            for k, c in results.items():
                v.comparisons[cps[k].id] = c
            by_step = {1: results["K0f"].passed and results["K0m"].passed, 2: results["K1"].passed,
                       3: results["K3"].passed}
            v.windows[tag] = blame_window(by_step, step_count=len(CARD_31.steps))
            for k in ("K0f", "K0m", "K1", "K3", "K3r"):
                c = results[k]
                if not c.passed:
                    cause, why = PROPOSED[k](c)
                    v.register.record(Divergence(
                        id=f"D-{cps[k].id}", checkpoint=cps[k].id, size=c.max_abs_difference,
                        tolerance=cps[k].tolerance.absolute, suspected_steps=v.windows[tag] or (cps[k].after_step,),
                        cause=cause, explanation=f"Proposed, awaiting the owner: {why}"))

    series_722 = MdgSeriesReader().parse(get(SERIES[722]), SERIES[722])
    for year in (1990, 2000, 2005, 2013):
        _, v.hosted_32[str(year)] = answers.annex_part(annex, "3.2", None, year)
        v.coverage_32[year] = sum(1 for r in series_722.table.to_pylist() if r["year"] == year)
    return v
