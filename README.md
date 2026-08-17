# African Stability Index (ASI)

A composite stability index covering all **54 African Union member states**, built on
**7 pillars** and **32 scoring indicators** (33 total incl. one descriptive), scored by
**4 weighting methods**, as a 2000-2024 panel with an interactive drill-down dashboard.

Data sources: World Bank **WDI** (db 2) and **WGI** (db 3) via the `wbgapi` API.
Methodology anchored to the OECD/JRC *Handbook on Constructing Composite Indicators* (2008)
— every design choice is source-mapped in [`methodology/references.md`](methodology/references.md).

---

## Quick start (new machine)

```powershell
git clone https://github.com/Oscarsb2004/African-Stability-Index.git
cd African-Stability-Index
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-pipeline.txt   # full pipeline + dashboard deps
python 07_dashboard.py                     # -> http://127.0.0.1:8050
```

All pipeline outputs in `data/` are committed, so the **dashboard and verification run
immediately after cloning** — no API pull required. Re-run the pipeline only when you want
fresh World Bank data.

Requirements files:
- `requirements.txt` — dashboard/web-deploy only (used by Railway/gunicorn)
- `requirements-pipeline.txt` — superset: adds `wbgapi`, `scipy`, `scikit-learn`, `pulp`

---

## Pipeline

Run stages in order from the project root. Each stage reads the previous stage's output
from `data/`.

| Stage | Script | What it does | Output |
|---|---|---|---|
| 1 | `01_pull.py` | Pull WDI + WGI series via wbgapi across the whole panel window | `data/01_raw_pull.xlsx` |
| 2 | `02_panel.py` | Build the country x indicator x **year** panel with provenance, apply derived transforms, fill regional gaps, normalise against **fixed goalposts**, and score pillars and composites with reliability tiers | `data/panel/*` |
| 3 | `03_robustness.py` | Sensitivity analysis at the reference year: weighting methods, adversarial weights, measured-only, islands excluded | `data/panel/robustness.json` |
| 7 | `07_dashboard.py` | Run the interface (port 8050) | — |

Add `--freeze-goalposts` to stage 2 only when deliberately re-anchoring every
historical score.

### Verification (run after any pipeline change)

One entry point runs three layers:

```bash
python -m verify.run
```

| Layer | Gates a release? | Role |
|---|---|---|
| `verify/panel.py` | **yes** | Independent re-derivation of the panel from the frozen raw baseline, using different tools than the pipeline (carry-forward via a `merge_asof` join; rolling means via `.rolling()`; reliability rules re-implemented from the specification). All 32 scoring indicators are covered. Of 43,200 scoring cells, 38,276 (88.6%) are re-derived; the remaining 11.4% are regional-mean estimates, which by definition cannot be predicted from a country's own data and are checked instead by the `MIN_REGIONAL_SAMPLE` rule and the reliability tiers. |
| `verify/contract.py` | **yes** | The backend/frontend object contract: every indicator entry carries its own identity, pillar scores reconcile with the indicators they are built from, ranks reproduce from scores, and the UI neither hardcodes counts nor redefines canonical constants. |
| `verify/advisory.py` | no | Design diagnostics — correlations, effective weights, coverage, staleness, benchmark plausibility. Reports; never blocks. |

`verify/` is deliberately **not** part of the `asi` package: verification that
imports the code it checks inherits that code's bugs. It re-reads the registry
YAML itself.

That was documentation until B03, and `verify/advisory.py` had already broken it
by loading the panel through the same module the interface uses.
`tests/test_verify_independence.py` now AST-scans every file under `verify/` and
fails on any `asi.*` import except `asi.core.constants` — which holds
declarations (pillar names, country list, tunable parameters) and no logic, so
importing it cannot import a bug under test.

Unit tests cover pure functions, registry integrity, and single-source-of-truth
enforcement:

```bash
python -m pytest tests/ -q
```

---

## Repository map

```
asi/                             importable package (the project's own code)
  pipeline/                      panel, goalposts, normalize, score
  results.py                     the only door to stored results (all callers)
  dashboard/app.py               the interface — reads only through results.py
  core/constants.py              ALL tunable parameters + the region profile (GSI seam)
  core/schema.py                 canonical objects: Observation, PillarScore,
                                 CompositeScore, Provenance, Reliability
  core/registry.py               indicator/pillar registry loader + validation
  core/countries.py              54 AU states: names, regions, REC memberships
  core/models.py                 runtime Indicator / Pillar objects
verify/                          independent verification (NOT imported by asi/)
  run.py                         single entry point: python -m verify.run
  panel.py contract.py advisory.py
tests/                           pytest: registry, schema, SSOT enforcement
scripts/                         one-off utilities (stub generation, adding indicators)
01_pull 02_panel 03_robustness   pipeline stages
07_dashboard.py                  thin runner for asi/dashboard/app.py
app.py, Procfile                 gunicorn entry point for web deploy (Railway-ready)
indicators_list/pillar_[a-g].yaml  indicator registry — polarity, window, aggregation,
                                   log flag, and written justification per indicator
context/                         colonial history, country facts, pillar justifications
qualitative/countries/*.yaml     per-country analyst notes (rendered in dashboard)
assets/                          dashboard CSS (incl. Dash 4 dropdown fix)
data/                            all pipeline outputs (committed for portability)
data/panel/                      the panel, scores, frozen weights, UI bundle
data/baseline/                   frozen raw pull used by verify/panel.py
methodology/references.md        source → design-decision mapping (keep in sync!)
methodology/METHODOLOGY_REVIEW.md  full OECD 10-step evaluation
methodology/ROADMAP.md           phased refinement plan
methodology/MANUAL_REVIEW.md     decisions awaiting human judgement
```

The legacy snapshot chain (`02_clean` / `03_normalize` / `04_score` /
`06_qualitative`) was retired in Phase C; `02_panel.py` supersedes all four.

## Documentation rule

Any change that introduces or alters a methodological choice must be logged in
`methodology/references.md` **in the same commit**, and `python -m verify.run` must
pass. Decisions that need human judgement go to
[`methodology/MANUAL_REVIEW.md`](methodology/MANUAL_REVIEW.md) rather than being
settled silently in code.

## Web deployment

`app.py` + `Procfile` + `requirements.txt` are Railway/Heroku-ready
(`gunicorn app:server`, `PORT` env var respected, `server = app.server` exported).

## Known methodological caveats

Open items live in [`methodology/MANUAL_REVIEW.md`](methodology/MANUAL_REVIEW.md);
the full assessment is in [`methodology/METHODOLOGY_REVIEW.md`](methodology/METHODOLOGY_REVIEW.md).
Headlines: 19 indicators have a fixed goalpost anchored on an estimated rather than
measured value; `co2_pc` behaves as an inverted wealth proxy (rho -0.93 with GDP per
capita) and PCA excludes Pillar F entirely while entropy weights it highest; the
governance source family carries roughly a third of the composite weight; and 2024
is present in the panel but too sparse to score.

Resolved in the 2026 revision: the gender parity indicators are now scored as
distance from parity rather than monotonically, and sample-relative normalisation
was replaced with fixed goalposts.

---

*Maintained by Oscar Bailey · Mount Allison University · part of the Athena platform family*
