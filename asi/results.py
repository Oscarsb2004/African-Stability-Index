"""
asi.results — the only door to stored results.

Stages after 02_panel.py read the panel through `load`, never by opening its
files themselves, so the panel's layout is known in one place. It filters and
formats; it never computes a score, a rank or a label. Every number it returns
was produced by the pipeline and checked by verify/panel.py.

`verify/` does not use it: verification that imports the code it checks
inherits that code's bugs, so `verify/advisory.py` reads `data/panel/` itself.

The Dash interface's view helpers and the narrative scripts' country helpers
were retired with them on 2026-10-19 (P73; tags archive/dash-2026-10 and
archive/narrative-2026-10).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from asi.core.constants import PROJECT_ROOT

PANEL_DIR = PROJECT_ROOT / "data" / "panel"


@dataclass(slots=True)
class PanelData:
    """The panel, loaded once: the bundle and its three tables."""

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


__all__ = ["PanelData", "load", "PANEL_DIR"]
