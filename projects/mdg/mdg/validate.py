"""Validation for indicator 3.3: every checkpoint, the blame window, and the divergence register.

Tolerances were fixed on the date in `mdg.answers.TOLERANCE_FIXED_ON`, before the first comparison, from the
precision the publishers print (one decimal for percentages; exact for counts).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pyarrow as pa

from athena.frames import Column, Frame, Manifest
from athena.store import Store
from athena.validation import (Checkpoint, Comparison, Divergence, DivergenceRegister, Tolerance,
                               blame_window)
from athena.vocab import DType, Profile, ReproClass, Role
from mdg import answers
from mdg.method import CARD, normalise, verify_quotes
from mdg.pipeline import Build
from mdg.readers import html_text
from mdg.sources import ANNEX, GROUPINGS, IPU_CLASSIFICATION, IPU_WORLD, METADATA_557

ONE_DECIMAL = Tolerance.from_decimals(1, fixed_on=answers.TOLERANCE_FIXED_ON)
EXACT = Tolerance(absolute=0.0, basis="counts and rounded values match exactly", fixed_on=answers.TOLERANCE_FIXED_ON)

K1 = Checkpoint(id="K1", after_step=1, published_value="country percentages", keys=("area",), measure="value",
                tolerance=ONE_DECIMAL)
K2 = Checkpoint(id="K2", after_step=3, published_value="world totals", keys=("total",), measure="value",
                tolerance=EXACT)
K3 = Checkpoint(id="K3", after_step=3, published_value="regional table", keys=("group",), measure="value",
                tolerance=ONE_DECIMAL)
K3R = Checkpoint(id="K3r", after_step=3, published_value="regional table, after rounding", keys=("group",),
                 measure="value", tolerance=EXACT)


@dataclass
class Validation:
    comparisons: dict[str, Comparison] = field(default_factory=dict)
    published: dict[str, dict[str, float]] = field(default_factory=dict)
    register: DivergenceRegister = field(default_factory=DivergenceRegister)
    window: tuple[int, ...] = ()
    quote_problems: list[str] = field(default_factory=list)
    snapshots: dict[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.comparisons.values()) and not self.quote_problems


def _totals_frame(build: Build) -> Frame:
    world = [r for r in build.frames["group-percent"].table.to_pylist() if r["group"] == "world"][0]
    manifest = Manifest(
        profile=Profile.CROSS_SECTION,
        columns=(Column(name="total", dtype=DType.STRING, role=Role.ENTITY),
                 Column(name="value", dtype=DType.FLOAT64, role=Role.MEASURE, unit="seats")),
        keys=("total",), produced_by="validate:world-totals", repro_class=ReproClass.A, period="2015-02-01",
    )
    return Frame(pa.table({"total": ["seats", "women"], "value": [float(world["seats"]), float(world["women"])]}),
                 manifest)


def _document_texts(store: Store, snapshots: dict[str, str]) -> dict[str, str]:
    """The text of each cited document, keyed by the name its citation locators use."""
    def get(recipe) -> bytes:
        snapshot = store.latest_snapshot(recipe.ref)
        snapshots[recipe.id] = snapshot.hash
        return store.get(snapshot.hash)

    from pypdf import PdfReader
    import io
    import logging

    logging.getLogger("pypdf").setLevel(logging.ERROR)
    doc = get(GROUPINGS).decode("cp1252", errors="replace").replace("\x07", " ").replace("\r", " ")
    return {
        "MDG metadata": html_text(get(METADATA_557)),
        "Regional groupings.doc": normalise(doc),
        "IPU world classification": html_text(get(IPU_CLASSIFICATION), encoding="latin-1"),
        "IPU world and regional averages": html_text(get(IPU_WORLD), encoding="latin-1"),
        "MDG 2015 statistical annex": " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(get(ANNEX))).pages),
    }


def validate(build: Build, store: Store) -> Validation:
    v = Validation()
    v.quote_problems = verify_quotes(CARD, _document_texts(store, v.snapshots))

    ipu_html = store.get(store.latest_snapshot(IPU_CLASSIFICATION.ref).hash)
    world_html = store.get(store.latest_snapshot(IPU_WORLD.ref).hash)
    annex_pdf = store.get(store.latest_snapshot(ANNEX.ref).hash)

    country_key, v.published["countries"] = answers.countries(ipu_html, build.mapping)
    world_key, v.published["world"] = answers.world_totals(world_html)
    region_key, v.published["regions"] = answers.regional(annex_pdf)

    v.comparisons["K1"] = country_key.compare(build.frames["country-percent"], K1, limit=500)
    v.comparisons["K2"] = world_key.compare(_totals_frame(build), K2)
    v.comparisons["K3"] = region_key.compare(build.frames["group-percent"], K3, limit=500)
    v.comparisons["K3r"] = region_key.compare(build.frames["group-percent-rounded"], K3R, limit=500)

    results = {1: v.comparisons["K1"].passed, 3: v.comparisons["K2"].passed and v.comparisons["K3"].passed}
    v.window = blame_window(results, step_count=len(CARD.steps))
    for checkpoint in (K1, K2, K3, K3R):
        c = v.comparisons[checkpoint.id]
        if not c.passed:
            suspected = v.window or (checkpoint.after_step,)
            v.register.record(Divergence(
                id=f"D-{checkpoint.id}", checkpoint=checkpoint.id, size=c.max_abs_difference,
                tolerance=checkpoint.tolerance.absolute, suspected_steps=suspected,
            ))
    return v
