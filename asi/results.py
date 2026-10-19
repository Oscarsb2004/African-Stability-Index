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
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from asi.core.constants import PROJECT_ROOT

PANEL_DIR = PROJECT_ROOT / "data" / "panel"

#: Tiers whose numbers may be shown. Anything else renders greyed.
DISPLAYABLE = ("reliable", "thin")


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


__all__ = [
    "PanelData", "load", "country_composite_series", "country_pillar_series",
    "country_indicators", "DISPLAYABLE",
]
