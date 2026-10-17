"""
01_inputs.py — the ASI's inputs, taken from Athena's datasets.

Every series the registry names, for the 54 AU member states over the pull window, is selected from the datasets
named on the command line and written to data/inputs.csv in Athena's common format. The datasets are the edition:

    python 01_inputs.py asi-pull-2026-08-08             # the legacy edition: the frozen pull of August 2026
    python 01_inputs.py wdi-2026-10-08 wgi-2026-09-25   # a new edition from the current WDI and WGI

The datasets come from athena-core: `python -m adapters asi-pull` or `python -m adapters worldbank`. Nothing is
dropped silently: a series that no dataset holds, or that two hold, stops the run. This replaces 01_pull.py, which
called the World Bank API with TLS verification turned off.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))  # athena-core, for the `athena` package

import pandas as pd  # noqa: E402

from asi.core.constants import PANEL_PULL_BUFFER, PANEL_START  # noqa: E402
from asi.core.countries import COUNTRIES  # noqa: E402
from asi.core.registry import IndicatorRegistry, PillarRegistry  # noqa: E402

OUTPUT = ROOT / "data" / "inputs.csv"


def select(values: pd.DataFrame, codes: set[str], countries: set[str], first: int, last: int) -> pd.DataFrame:
    """The rows of `values` (Athena's common format) for these series, countries and years, as published."""
    years = values["TIME_PERIOD"].astype(int)
    chosen = values[values["SERIES"].isin(codes) & values["REF_AREA"].isin(countries)
                    & years.between(first, last) & values["OBS_VALUE"].notna()]
    held = chosen.groupby("SERIES")["DATASET"].unique()
    missing = sorted(codes - set(held.index))
    twice = sorted(series for series, names in held.items() if len(names) > 1)
    if missing or twice:
        raise ValueError(f"series no dataset holds: {missing}; series two datasets hold: {twice}")
    return chosen.sort_values(["SERIES", "REF_AREA", "TIME_PERIOD"], ignore_index=True)


def main(names: list[str]) -> int:
    if not names:
        print(__doc__)
        return 2
    from athena import dataset

    indicators = IndicatorRegistry(PillarRegistry()).build_indicators()
    codes = {ind.series_code for ind in indicators.values()}
    first, last = PANEL_START - PANEL_PULL_BUFFER, max(ind.year_end for ind in indicators.values())
    values = pd.concat([dataset.load(name) for name in names], ignore_index=True)
    chosen = select(values, codes, set(COUNTRIES), first, last)
    chosen.to_csv(OUTPUT, index=False, lineterminator="\n")
    counts = chosen["SERIES"].value_counts()
    print(f"{OUTPUT.relative_to(ROOT)}: {len(chosen):,} values, {len(counts)} series, "
          f"{chosen['REF_AREA'].nunique()} countries, {first} to {last}, from {', '.join(names)}")
    print(f"  fewest values: {', '.join(f'{s} {n}' for s, n in counts.sort_values().head(5).items())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
