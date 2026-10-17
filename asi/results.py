"""
asi.results — the only door to stored results.

It lived at `asi.dashboard.data` and was described as the *interface's* only
door, which turned out to be a misreading of its own job. Four callers outside
the interface already used it: `03_robustness.py`, `scripts/country_facts.py`,
`scripts/narrative_check.py` and `verify/advisory.py`. The last one mattered —
a verification layer importing the code it checks inherits that code's bugs,
which is the rule `README` and `verify/__init__.py` both state. The name was
describing one caller rather than the boundary, so the boundary kept leaking.
`verify/advisory.py` now reads `data/panel/` directly and imports nothing from
here; the other three are ordinary consumers and belong at this address.

Rules this module exists to enforce:

  1. It filters and formats. It never computes a score, a rank, or a label.
     Every number it returns was produced by the pipeline and checked by
     verify/panel.py. If the UI needed to derive something, that derivation
     would belong in the pipeline instead, where it can be verified.

  2. Identity travels with values. Panel rows already carry display_name,
     series_code and database, so nothing here looks a name up.

  3. Unreliable results are never silently dropped. They are returned with
     their tier attached so the interface can grey them out and say why — a
     blank cell and an untrustworthy cell are different claims.

The "Lens" concept below is the single control that answers "what is the map
showing?" — either a composite method or one pillar. Keeping it as one
vocabulary is what stops the toolbar from growing a control per feature.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from asi.core.constants import PILLAR_DEFS, PROJECT_ROOT

PANEL_DIR = PROJECT_ROOT / "data" / "panel"

#: Tiers whose numbers may be shown. Anything else renders greyed.
DISPLAYABLE = ("reliable", "thin")


# ── Lens ───────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class Lens:
    """
    What the map is coloured by: one composite method, or one pillar.

    kind is "composite" or "pillar"; key is the method name or the pillar id.
    """

    kind: str
    key: str

    @property
    def value(self) -> str:
        return f"{self.kind}:{self.key}"

    @classmethod
    def parse(cls, value: str | None) -> "Lens":
        if not value or ":" not in value:
            return cls("composite", "equal")
        kind, key = value.split(":", 1)
        if kind not in ("composite", "pillar"):
            return cls("composite", "equal")
        return cls(kind, key)

    def label(self, method_labels: dict[str, str]) -> str:
        if self.kind == "pillar":
            return f"Pillar {self.key} — {PILLAR_DEFS.get(self.key, self.key)}"
        return method_labels.get(self.key, self.key)


# ── Loading ────────────────────────────────────────────────────────────────────

@dataclass(slots=True)
class PanelData:
    """Everything the interface reads, loaded once at start-up."""

    meta: dict
    countries: dict
    indicators: dict
    pillars: dict
    observations: pd.DataFrame
    pillar_scores: pd.DataFrame
    composites: pd.DataFrame

    @property
    def reference_year(self) -> int:
        return int(self.meta["run"]["reference_year"])

    @property
    def panel_start(self) -> int:
        return int(self.meta["run"]["panel_start"])

    @property
    def panel_end(self) -> int:
        return int(self.meta["run"]["panel_end"])

    @property
    def years(self) -> list[int]:
        return list(range(self.panel_start, self.panel_end + 1))

    @property
    def methods(self) -> list[str]:
        return list(self.meta.get("methods", []))


def load(panel_dir: Path | None = None) -> PanelData:
    """Load the panel. Raises clearly if the pipeline has not been run."""
    d = Path(panel_dir or PANEL_DIR)
    required = ["bundle.json", "observations.csv", "pillar_scores.csv", "composites.csv"]
    missing = [f for f in required if not (d / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Panel incomplete in {d}: missing {missing}. Run: python 02_panel.py"
        )

    meta = json.loads((d / "bundle.json").read_text(encoding="utf-8"))
    return PanelData(
        meta=meta,
        countries=meta["countries"],
        indicators=meta["indicators"],
        pillars=meta["pillars"],
        observations=pd.read_csv(d / "observations.csv"),
        pillar_scores=pd.read_csv(d / "pillar_scores.csv"),
        composites=pd.read_csv(d / "composites.csv"),
    )


# ── Map / rankings view ────────────────────────────────────────────────────────

def choropleth_frame(data: PanelData, lens: Lens, year: int) -> pd.DataFrame:
    """
    One row per country for a given lens and year.

    Columns: iso3, name, region, island_state, score, rank, reliability,
             displayable, coverage_ratio (pillar lens only).

    Countries with an untrustworthy result keep their row — with
    `displayable=False` — so the map can grey them rather than leaving a hole
    the reader cannot distinguish from "no such country".
    """
    if lens.kind == "pillar":
        src = data.pillar_scores
        sub = src[(src["pillar_id"] == lens.key) & (src["year"] == year)].copy()
        sub = sub.rename(columns={"score": "score"})
        sub["rank"] = pd.NA
        keep = ["iso3", "score", "reliability", "coverage_ratio", "rank"]
        sub = sub[[c for c in keep if c in sub.columns]]
        # rank within the displayable subset only: ranking an untrustworthy
        # number states a comparison the data does not support
        mask = sub["reliability"].isin(DISPLAYABLE) & sub["score"].notna()
        sub.loc[mask, "rank"] = (
            sub.loc[mask, "score"].rank(ascending=False, method="min").astype("Int64")
        )
    else:
        src = data.composites
        sub = src[(src["method"] == lens.key) & (src["year"] == year)].copy()
        sub = sub[["iso3", "score", "rank", "reliability"]]
        sub["coverage_ratio"] = pd.NA

    sub["displayable"] = sub["reliability"].isin(DISPLAYABLE) & sub["score"].notna()
    sub["name"] = sub["iso3"].map(lambda i: data.countries.get(i, {}).get("name", i))
    sub["region"] = sub["iso3"].map(lambda i: data.countries.get(i, {}).get("region", ""))
    sub["island_state"] = sub["iso3"].map(
        lambda i: bool(data.countries.get(i, {}).get("island_state", False))
    )
    sub["recs"] = sub["iso3"].map(lambda i: data.countries.get(i, {}).get("recs", []))
    return sub.reset_index(drop=True)


# ── Grouping (the "Compare" control) ───────────────────────────────────────────

def apply_grouping(
    frame: pd.DataFrame,
    mode: str,
    key: str | None,
    *,
    exclude_islands: bool = False,
) -> pd.DataFrame:
    """
    Mark which countries are in scope for the current comparison.

    Adds `in_scope`. Rows are never removed: a country outside the selected
    Regional Economic Community still exists and still renders — greyed — so
    the map keeps its shape and the reader can see what was excluded.
    """
    frame = frame.copy()
    if mode == "rec" and key:
        frame["in_scope"] = frame["recs"].map(lambda rs: key in (rs or []))
    elif mode == "region" and key:
        frame["in_scope"] = frame["region"] == key
    else:
        frame["in_scope"] = True

    if exclude_islands:
        frame.loc[frame["island_state"], "in_scope"] = False
    return frame


def rankings(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Ordered, in-scope, displayable rows, re-ranked within the current scope.

    Re-ranking matters: inside a Regional Economic Community the reader wants
    "3rd in ECOWAS", not the country's continental position.
    """
    sub = frame[frame["in_scope"] & frame["displayable"]].copy()
    if sub.empty:
        # Always return the promised shape. A year where nothing is rankable is
        # a real state — 2024 is entirely unreliable because World Bank series
        # report late — and callers merge on `scope_rank`, so an empty frame
        # without that column turns an honest "nothing to show" into a crash.
        sub["scope_rank"] = pd.Series(dtype="Int64")
        return sub
    sub = sub.sort_values("score", ascending=False)
    sub["scope_rank"] = sub["score"].rank(ascending=False, method="min").astype("Int64")
    return sub


# ── Country detail ─────────────────────────────────────────────────────────────

def country_composite_series(data: PanelData, iso3: str, method: str) -> pd.DataFrame:
    """A country's composite over the whole panel, tiers included."""
    c = data.composites
    sub = c[(c["iso3"] == iso3) & (c["method"] == method)].copy()
    sub["displayable"] = sub["reliability"].isin(DISPLAYABLE) & sub["score"].notna()
    return sub.sort_values("year").reset_index(drop=True)


def country_pillar_series(data: PanelData, iso3: str) -> pd.DataFrame:
    """Every pillar for one country across the panel."""
    p = data.pillar_scores
    sub = p[p["iso3"] == iso3].copy()
    sub["displayable"] = sub["reliability"].isin(DISPLAYABLE) & sub["score"].notna()
    return sub.sort_values(["pillar_id", "year"]).reset_index(drop=True)


def country_indicators(data: PanelData, iso3: str, year: int,
                       pillar_id: str | None = None) -> pd.DataFrame:
    """
    Indicator rows for one country-year, already carrying their own identity.

    The interface renders display_name and series_code straight off these rows;
    it does not consult the registry.
    """
    o = data.observations
    sub = o[(o["iso3"] == iso3) & (o["year"] == year)].copy()
    if "role" in sub.columns:
        sub = sub[sub["role"] == "scoring"]
    if pillar_id:
        members = data.pillars.get(pillar_id, {}).get("indicators", [])
        sub = sub[sub["variable_name"].isin(members)]
    return sub.sort_values("display_name").reset_index(drop=True)


def reliability_note(reliability: str, coverage_ratio: float | None = None) -> str:
    """Plain-language explanation of why something is greyed."""
    if reliability == "reliable":
        return "Based mostly on direct measurements."
    if reliability == "thin":
        note = "Partly estimated — read with caution."
        if coverage_ratio is not None and pd.notna(coverage_ratio):
            note += f" {coverage_ratio * 100:.0f}% of indicators measured directly."
        return note
    if reliability == "unreliable":
        note = "Not shown: too much of this is inferred rather than measured."
        if coverage_ratio is not None and pd.notna(coverage_ratio):
            note += f" Only {coverage_ratio * 100:.0f}% of indicators were measured."
        return note
    return "No data available for this year."


__all__ = [
    "Lens", "PanelData", "load", "choropleth_frame", "apply_grouping",
    "rankings", "country_composite_series", "country_pillar_series",
    "country_indicators", "reliability_note", "DISPLAYABLE",
]
