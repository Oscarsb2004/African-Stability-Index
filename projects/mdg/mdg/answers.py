"""The answer key: what the publishers printed. Sealed from the pipeline.

Only `mdg.validate` may import this module. A test scans every pipeline module and fails if one does. The published
tables are also returned for the report, which is written after every comparison is made.
"""

from __future__ import annotations

from datetime import date

import pyarrow as pa

from athena.frames import Column, Frame, Manifest
from athena.validation import AnswerKey
from athena.vocab import DType, Profile, ReproClass, Role
from mdg.readers import AnnexTableReader, IpuClassificationReader, IpuWorldReader
from mdg.sources import ANNEX, IPU_CLASSIFICATION, IPU_WORLD

YEAR = 2015

ANNEX_LABELS = {
    "World": ("world", "world"),
    "Developing regions": ("developing", "development"),
    "Developed regions": ("developed", "development"),
    "Northern Africa": ("northern-africa", "region"),
    "Sub-Saharan Africa": ("sub-saharan-africa", "region"),
    "Latin America and the Caribbean": ("latin-america-and-the-caribbean", "region"),
    "Caribbean": ("caribbean", "subregion"),
    "Latin America": ("latin-america", "subregion"),
    "Eastern Asia": ("eastern-asia", "region"),
    "Eastern Asia excluding China": ("eastern-asia-excluding-china", "alternate"),
    "Southern Asia": ("southern-asia", "region"),
    "Southern Asia excluding India": ("southern-asia-excluding-india", "alternate"),
    "South-Eastern Asia": ("south-eastern-asia", "region"),
    "Western Asia": ("western-asia", "region"),
    "Oceania": ("oceania", "region"),
    "Caucasus and Central Asia": ("caucasus-and-central-asia", "region"),
    "Least developed countries": ("least-developed", "special"),
    "Landlocked developing countries": ("landlocked-developing", "special"),
    "Small island developing States": ("small-island-developing", "special"),
}


def _frame(entity: str, rows: list[tuple[str, float]], unit: str, source: str) -> Frame:
    manifest = Manifest(
        profile=Profile.CROSS_SECTION,
        columns=(Column(name=entity, dtype=DType.STRING, role=Role.ENTITY),
                 Column(name="value", dtype=DType.FLOAT64, role=Role.MEASURE, unit=unit)),
        keys=(entity,), produced_by=source, repro_class=ReproClass.C, period=str(YEAR),
    )
    return Frame(pa.table({entity: pa.array([r[0] for r in rows], pa.string()),
                           "value": pa.array([r[1] for r in rows], pa.float64())}), manifest)


class UnknownLabel(ValueError):
    pass


def regional(annex_pdf: bytes) -> tuple[AnswerKey, dict[str, float]]:
    rows = AnnexTableReader().parse(annex_pdf, ANNEX, "3.3")
    published = {}
    for label, year, value in rows:
        if label not in ANNEX_LABELS:
            raise UnknownLabel(f"annex row {label!r} has no grouping")
        if year == YEAR and value is not None:
            published[ANNEX_LABELS[label][0]] = value
    frame = _frame("group", sorted(published.items()), "percent", AnnexTableReader.ref())
    return AnswerKey(frame, source=ANNEX.ref), published


def countries(ipu_html: bytes, mapping: dict[str, str]) -> tuple[AnswerKey, dict[str, float]]:
    reader = IpuClassificationReader()
    published = {}
    for row in reader.rows(ipu_html):
        printed = row[5].rstrip("%")
        if printed not in ("?", "---", ""):
            published[mapping[reader.name(row[1])]] = float(printed)
    frame = _frame("area", sorted(published.items()), "percent", reader.ref())
    return AnswerKey(frame, source=IPU_CLASSIFICATION.ref), published


def world_totals(ipu_world_html: bytes) -> tuple[AnswerKey, dict[str, float]]:
    totals = IpuWorldReader().parse(ipu_world_html, IPU_WORLD)
    published = {"seats": float(totals["known"]), "women": float(totals["women"])}
    frame = _frame("total", sorted(published.items()), "seats", IpuWorldReader.ref())
    return AnswerKey(frame, source=IPU_WORLD.ref), published | {"percent": totals["percent"]}


TOLERANCE_FIXED_ON = date(2026, 9, 26)


# ── Goal 3 (section S43) ────────────────────────────────────────────────────────────────────────────────────

def annex_part(annex_pdf: bytes, indicator: str, part: str | None, year: int) -> tuple[AnswerKey, dict[str, float]]:
    """One year of one part of an annex table, keyed by grouping."""
    published = {}
    for p, label, y, value in AnnexTableReader().parts(annex_pdf, indicator):
        if label not in ANNEX_LABELS:
            raise UnknownLabel(f"annex row {label!r} has no grouping")
        if p == part and y == year and value is not None:
            published[ANNEX_LABELS[label][0]] = value
    frame = _frame("group", sorted(published.items()), "as published", AnnexTableReader.ref())
    return AnswerKey(frame, source=ANNEX.ref), published


def mdg_series(series_html: bytes, mapping: dict[str, str], year: int) -> tuple[AnswerKey, dict[str, float]]:
    """The MDG database's final country values (6 July 2015) for one year, keyed by country code."""
    from mdg.readers import MdgSeriesReader

    frame = MdgSeriesReader().parse(series_html, ANNEX)
    published = {mapping[r["name"]]: r["value"] for r in frame.table.to_pylist() if r["year"] == year}
    return AnswerKey(_frame("area", sorted(published.items()), "as published", MdgSeriesReader.ref()),
                     source="recipe:mdg-series"), published


def uis_ger(records_json: bytes, female: str, male: str, year: int) -> dict[str, AnswerKey]:
    """UIS's own gross enrolment ratios by sex for one year: the check on our arithmetic, same edition."""
    from mdg.readers import UisApiReader

    frame = UisApiReader().parse(records_json, ANNEX)
    keys = {}
    for sex, code in (("female", female), ("male", male)):
        rows = sorted((r["area"], r["value"]) for r in frame.table.to_pylist()
                      if r["indicator"] == code and r["year"] == year and r["value"] is not None)
        keys[sex] = AnswerKey(_frame("area", rows, "percent", UisApiReader.ref()), source=f"uis:{code}")
    return keys
