# African Stability Index (ASI)

A composite stability index covering all **54 African Union member states**, built on
**7 pillars** and **32 scoring indicators** (33 total incl. one descriptive), scored by
**5 weighting methods**, with an interactive drill-down dashboard.

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
| 1 | `01_pull.py` | Pull WDI + WGI series via wbgapi (retry logic for 502/504) | `data/01_raw_pull.xlsx` |
| 2 | `02_clean.py` | Aggregate to one value per country-indicator (per-YAML window/mode), stage-1 lookback fill, IDP per-capita conversion, stage-2 regional fill, IQR winsorization | `data/02_clean.xlsx` |
| 3 | `03_normalize.py` | Optional log1p, min-max to [0,100] with polarity | `data/03_norm.xlsx` |
| 4 | `04_score.py` | Pillar scores (mean of available) + 5 methods: equal, PCA, BoD, entropy, geometric | `data/04_scores.xlsx`, `data/04_scores_raw.csv` |
| 5 | `05_robustness.py` | Weight perturbation, MaxS adversarial search, fill/island exclusion | `data/05_robustness.xlsx/.json` |
| 6 | `06_qualitative.py` | Bundle everything + qualitative notes into the dashboard payload | `data/06_results.json` |
| 7 | `07_dashboard.py` | Dash app (port 8050; drill-down: continent → country → pillar → indicator) | — |

### Verification (run after any pipeline change)

| Script | Role |
|---|---|
| `00_audit.py` | Rule-based audit: recomputes normalization/pillar/equal/geometric, design advisories, benchmark plausibility, within-pillar correlations. Output: `data/audit_report.json` + console. |
| `00_evaluate.py` | **Independent end-to-end re-derivation** from the frozen raw baseline (`data/baseline/01_raw_pull_BASELINE.xlsx`) through indicators → pillars → all 5 methods, using different solvers than the pipeline (eigendecomposition vs sklearn PCA; scipy HiGHS vs pulp CBC). Exit 0 = all pass. Delete the baseline file to re-freeze after an intentional re-pull. |

Both must be green before committing methodology changes.

---

## Repository map

```
00_audit.py, 00_evaluate.py      verification (see above)
01..07_*.py                      pipeline stages + dashboard
app.py, Procfile                 gunicorn entry point for web deploy (Railway-ready)
constants.py                     ALL tunable parameters (weights bounds, IQR k, thresholds)
config.py                        indicator/pillar registry loader
models/countries.py              54 AU states: names, regions, island flags
indicators_list/pillar_[a-g].yaml  indicator registry — polarity, window, aggregation,
                                   log flag, and written justification per indicator
context/                         colonial history, country facts, pillar justifications
qualitative/countries/*.yaml     per-country analyst notes (rendered in dashboard)
assets/                          dashboard CSS (incl. Dash 4 dropdown fix)
data/                            all pipeline outputs (committed for portability)
data/baseline/                   frozen raw pull used by 00_evaluate.py
methodology/references.md        source → design-decision mapping (keep in sync!)
methodology/METHODOLOGY_REVIEW.md  full OECD 10-step evaluation (2026-07-14)
methodology/ROADMAP.md           phased refinement plan — START HERE for next steps
```

## Documentation rule

Any change that introduces or alters a methodological choice must be logged in
`methodology/references.md` **in the same commit**, and `00_audit.py` + `00_evaluate.py`
must pass. The July 2026 review found doc-drift (see `METHODOLOGY_REVIEW.md` §B) —
Roadmap Phase 0 restores sync.

## Web deployment

`app.py` + `Procfile` + `requirements.txt` are Railway/Heroku-ready
(`gunicorn app:server`, `PORT` env var respected, `server = app.server` exported).

## Known methodological caveats (as of 2026-07-14)

Documented in full in [`methodology/METHODOLOGY_REVIEW.md`](methodology/METHODOLOGY_REVIEW.md);
fix plan in [`methodology/ROADMAP.md`](methodology/ROADMAP.md). Headlines: GPI indicators
scored monotonically (should be distance-from-parity); `co2_pc` acts as an inverted wealth
proxy (Pillar F excluded by PCA); WGI carries 28.9% effective weight; education data is
effectively ~2017 despite "most_recent" labels.

---

*Maintained by Oscar Bailey · Mount Allison University · part of the Athena platform family*
