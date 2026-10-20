# African Stability Index (ASI)

A composite stability index covering all **54 African Union member states**, scored by **4 weighting methods**, as a
yearly panel. It is published through the React and MapLibre site in `web/`.

- **Edition 1 (published):** 7 pillars, 32 scoring indicators, a 2000–2024 panel, reference year 2023.
- **Edition 2 (in progress, steps 1 to 7 in `methodology/EDITION_2.md`):** the **8 pillars** of ruling P57
  (Governance and State Capacity; Political Voice and Representation; Security and Violence; Macroeconomic and
  Fiscal Stability; External Exposure and Economic Structure; Human Development and Demography; Social Cohesion and
  Equity; Environment and Climate Exposure), 50 scoring indicators and 19 descriptive ones, a 2000–2025 panel,
  reference year 2024.

**Since 2026-10-17 the ASI lives in Athena** (`athena-core/projects/asi`, decision P44), with its full history.
The public repository `Oscarsb2004/African-Stability-Index` and its GitHub Pages site stay as the live legacy
edition until a new edition is published from here.

Data: World Bank **WDI** and **WGI**, and from edition 2 **UCDP**'s country-year deaths in organised violence, read
from Athena's datasets. Every score published so far rests on the ASI's own pull of 8 August 2026, kept as the
dataset `asi-pull-2026-08-08`. Methodology anchored to the OECD/JRC *Handbook on Constructing Composite Indicators*
(2008); every design choice is source-mapped in [`methodology/references.md`](methodology/references.md).

**Trimmed on 2026-10-19** (the Athena Charter's trimming ledger):
- the Dash interface was retired for the React site (P73);
- the AI-written narrative system and its context texts were archived, and edition 2's step 10 rebuilds narratives
  as site content;
- the shadow registry's write side, the empty qualitative stubs and six superseded planning documents were removed.

Each is kept at its tag: `archive/dash-2026-10`, `archive/narrative-2026-10` and `archive/asi-dead-code-2026-10`.

---

## Running it

From this folder, with athena-core's environment (`requirements.lock` at the repository root):

```powershell
..\..\.venv\Scripts\python -m pytest -q                  # the tests
..\..\.venv\Scripts\python -m verify.run                 # the four verification layers
```

Every output in `data/` and `web/public/` is committed, so the tests and verification run without Athena's store.
The store is needed only to make inputs (stage 1 below).

---

## Pipeline

Run stages in order from the project root. Each stage reads the previous stage's output.

| Stage | Script | What it does | Output |
|---|---|---|---|
| 0 | `python -m adapters asi-pull` or `python -m adapters worldbank`, in athena-core | Ingest the inputs' databases into Athena's store, each source hash-locked | datasets in `C:\AthenaStore\datasets` |
| 1 | `01_inputs.py <datasets>` | Select the registry's series for the 54 states over the pull window from the named datasets. The datasets are the edition: `asi-pull-2026-08-08` reproduces every published score exactly; `wdi-2026-10-08 wgi-2026-09-25 ucdp-cy-26.1` makes edition 2 | `data/inputs.csv` |
| 2 | `02_panel.py` | Build the country x indicator x **year** panel with provenance, apply derived transforms, normalise against **fixed goalposts**, and score pillars and composites with reliability tiers | `data/panel/*` |
| 3 | `03_robustness.py` | Sensitivity analysis at the reference year: weighting methods, adversarial weights, measured-only, islands excluded | `data/panel/robustness.json` |
| 4 | `04_sections.py <datasets>` | The sections of three dimensions (P64) for each country: stability (other appraisals), economy and finance. athena-core's shared templates are bound to WDI, WGI, UNDP HDR and TI CPI series in `sections.toml` (P54): `04_sections.py wdi-2026-10-08 wgi-2026-09-25 hdr-2025 cpi-2025` | `web/public/data/sections.json` |
| 5 | `05_web.py` | The other files the site reads: Natural Earth borders, countries and cities (hash-locked through `athena.fetch`), the published ASI at its reference year, and the sources list | `web/public/{geo,data}/*` |
| 6 | `06_backtests.py <datasets>` | The pre-registered backtests (the vault's `ASI Backtests`) on the published panel | `data/backtests.json` |
| 7 | `07_wonders.py` | The continent's wonders by a stated rule (World Heritage Sites and the most notable mountains, falls, lakes and more on Wikidata, CC0), each with licensed Commons photographs | `web/public/data/wonders.json` |
| 8 | `08_narratives.py` | Each country's data narrative at the reference year: stated templates filled with the panel's numbers (score, interval, tier and band, the pillars furthest from the median state, the change over ten years, what was left out), every number re-derived by `verify/narrative.py` | `data/panel/narratives.json` |
| — | `web/`: `npm install`, then `npm run dev` | The site (P55): a satellite globe with five sections (Stability, Economy, Finance, Infrastructure, Wonders) and a country panel on the right. Imagery: EOX by default; Esri World Imagery when `web/.env.local` sets `VITE_ESRI_KEY` | — |

Add `--freeze-goalposts` to stage 2 only when deliberately re-anchoring every historical score.

### Verification (run after any pipeline change)

One entry point runs four layers:

```bash
python -m verify.run
```

| Layer | Gates a release? | Role |
|---|---|---|
| `verify/rebuild.py` | **yes** | Reruns stages 2 and 3 from `data/inputs.csv` in a scratch copy; every committed output must come back identical. A stale or hand-edited output fails, and it is the proof that the ASI reproduces its published scores from Athena's datasets. |
| `verify/panel.py` | **yes** | Independent re-derivation of the panel from its inputs (`data/inputs.csv`), using different tools than the pipeline (carry-forward via a `merge_asof` join; rolling means and volatility via `.rolling()`; per-capita rates from the carried-forward count and population; reliability rules re-implemented from the specification). Every scoring indicator is covered. From edition 2 there is no regional fill, so every cell with a value is re-derived (78,234 by the as-of join alone at step 6); in edition 1, 11.4% of cells were regional means no check could predict. |
| `verify/contract.py` | **yes** | Every observation row and the bundle carry their own identity (name, series code, year, value), and agree with the registry. |
| `verify/advisory.py` | no | Design diagnostics: correlations, effective weights, coverage, staleness, benchmark plausibility. Reports; never blocks. |

`verify/` is deliberately **not** part of the `asi` package: verification that imports the code it checks inherits
that code's bugs. It re-reads the registry YAML itself. `tests/test_verify_independence.py` AST-scans every file
under `verify/` and fails on any `asi.*` import except `asi.core.constants`, which holds declarations (pillar
names, country list, tunable parameters) and no logic.

---

## Repository map

```
asi/                             importable package (the project's own code)
  pipeline/                      panel, goalposts, normalize, score
  results.py                     the only door to the stored panel
  core/constants.py              ALL tunable parameters + the region profile (GSI seam)
  core/schema.py                 canonical objects: Observation, PillarScore,
                                 CompositeScore, Provenance, Reliability
  core/registry.py               indicator/pillar registry loader + validation (read-only)
  core/countries.py              54 AU states: names, regions, REC memberships; the excluded member
  core/models.py                 the runtime Indicator object
verify/                          independent verification (NOT imported by asi/)
  run.py                         single entry point: python -m verify.run
  rebuild.py panel.py contract.py advisory.py stats.py
tests/                           pytest
01_inputs … 08_narratives        pipeline stages; backtests.py holds the backtests' rules
indicators_list/pillar_*.yaml    the indicator registry, edited by hand: polarity, window,
                                 aggregation, log flag, and a written justification per indicator
registry/goalposts.yaml          the frozen goalposts
registry/overlap.yaml            the frozen overlap screen: which indicators share a slot of their pillar (P101)
sections.toml                    the binding of the shared section templates (P54)
data/                            pipeline outputs (committed for portability)
data/panel/                      the panel, scores, frozen weights, the bundle
data/inputs.csv                  the edition's inputs, written by 01_inputs.py from Athena's datasets
data/baseline/                   the frozen pull of 8 August 2026, the source of asi-pull-2026-08-08
web/                             the React and MapLibre site
methodology/references.md        source → design-decision mapping (keep in sync!)
methodology/STATISTICS.md        the statistics and their sources (P46)
methodology/EDITION_2.md         edition 2, step by step
```

## Documentation rule

Any change that introduces or alters a methodological choice is logged in `methodology/references.md` **in the same
commit**, and `python -m verify.run` must pass. A choice that needs human judgement goes to the owner as a proposed
ruling (the vault's `Decisions`), never settled silently in code.

## Known methodological caveats

Edition 1's headlines: 19 indicators have a fixed goalpost anchored on an estimated rather than measured value;
`co2_pc` behaves as an inverted wealth proxy (rho -0.93 with GDP per capita), and PCA excludes Pillar F entirely
while entropy weights it highest; the governance source family carries roughly a third of the composite weight; and
2024 is present in the panel but too sparse to score. Edition 2's open items are in `methodology/EDITION_2.md` and
the ASI's notes in the Athena vault.

Resolved in the 2026 revision: the gender parity indicators are now scored as distance from parity rather than
monotonically, and sample-relative normalisation was replaced with fixed goalposts.

---

*Maintained by Oscar Bailey · Mount Allison University · part of the Athena platform family*
