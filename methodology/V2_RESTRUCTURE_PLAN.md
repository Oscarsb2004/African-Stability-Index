# ASI v2 — Restructure, Panel Rebuild, Narrative System

*Planning document. Supersedes `methodology/ROADMAP.md` Phases 1–6, which fold into the
workstreams below. Written 2026-08-08.*

---

## 1. Context — what this project is

**The African Stability Index is a minimally-biased, multi-domain stability index for
peer-to-peer country comparison and deep single-country analysis.**

The thesis: *numbers alone do not explain stability; history does.* A composite score tells
you Chad ranks 51st. It does not tell you why — that answer lives in colonial extraction
patterns, commodity dependence, Sahel security spillover, and a coup in 2021. The project's
distinctive claim is the **pairing**: rigorous quantitative comparison *plus* cited
qualitative history, so a reader can move from "what" to "why" without leaving the page.

Three commitments follow from that, and every decision below serves them:

1. **Comparability.** Countries must be comparable to each other *and to their own past*.
   This is why normalization moves to fixed goalposts (§4.2) and why the time slider exists.
2. **Honesty about uncertainty.** A score built from regional averages is not a measurement.
   Where data is largely inferred, the interface must say so and grey out (§4.3), rather than
   render a confident number.
3. **Fair framing.** Africa is routinely narrated as a catalogue of failures. This project
   documents conflict and fragility without reducing 54 countries to them — it attributes
   structural causes (extraction, debt architecture, commodity dependence) and gives equal
   evidentiary weight to democratic consolidation, peace agreements, and development gains
   (§6.4). This is a methodological requirement, not a stylistic preference.

**Scope decision:** Africa-only in content; region-agnostic in the data pipeline. Africa-specific
constants (region names, island set, `scope="africa"` map, IIAG benchmarks) move behind a config
boundary so a future Global Stability Index reuses the pipeline. Narrative, colonial history, and
REC logic stay deliberately Africa-specific.

---

## 2. Current-state assessment

### 2.1 What is genuinely good — keep

- Independent verification (`00_evaluate.py`, 31 checks, different solvers) — rare and valuable.
- Per-indicator written justifications in `indicators_list/*.yaml`.
- Documented consolidation decisions (dropped `adult_literacy`, `primary_oos`, etc.).
- `context/colonial_history.yaml` — 1,188 lines, all 54 countries. **The narrative seed.**
- REC membership **already exists** in `models/countries.py`: all 8 AU RECs, 103 memberships.
  ECOWAS shows 12 (consistent with the 2025 Sahel withdrawals). Your Excel becomes a
  *verification source*, not a prerequisite — no scraping needed for v1.
- Drill-down dashboard with formula walkthrough.

### 2.2 Redundancy and structural debt

| Problem | Evidence | Fix |
|---|---|---|
| Two verification programs | `00_audit.py` + `00_evaluate.py` overlap on normalization/pillar/equal/geometric recomputation | Merge into `verify/` (§7) |
| Three config files | `constants.py`, `config.py`, `run_config.py` | Merge to `asi/core/` |
| Stale script | `validate_stage1.py` header says "37 indicators"; actual 32+1 | Delete |
| Numbered modules unimportable | `app.py` needs an `importlib` hack to load `07_dashboard.py` | Rename to real module names |
| SSOT violated in practice | `ISLAND_SET` redefined at `07_dashboard.py:57` despite `constants.py` owning it | Enforce by test, not convention |
| Dashboard re-derives backend work | `_load()` reads 4 files (`02_clean`, `03_norm`, `04_scores`, `06_results`) and recomputes ranks + custom scores | Single bundle contract (§3) |
| Excel as inter-stage transport | 500KB binaries in git; lossy, slow, undiffable | Parquet for interchange; Excel only as human export |
| Tests embedded in pipeline | `sys.exit(1)` gates inside `02_clean.py` | Move to `verify/`; keep only hard safety gates |
| Zero unit tests | Only end-to-end scripts exist | Add pytest for pure functions |
| Magic numbers in UI | "36 Indicators" was hardcoded (fixed); pattern remains | Derive all counts from the bundle |
| Empty narrative layer | **All 54 `qualitative/countries/*.yaml` are empty stubs** | Greenfield build (§6) |

### 2.3 The core architectural principle (your "same object" requirement)

> *"A health indicator should be the same object viewed on the server side, comprised of name,
> value, series code, year… the frontend and backend are the same object."*

Today this is violated: the dashboard reads raw Excel, re-pivots, recomputes ranks, and
re-labels indicators. **Target: the bundle is the sole contract boundary.** The pipeline emits
canonical objects; the dashboard renders them verbatim and derives nothing. Verification then
asserts identity across that boundary (§7.2).

---

## 3. Canonical data model

One atomic record, defined once in `asi/core/schema.py`, flowing unchanged from pull to pixel:

```
Observation:
  iso3, variable_name, display_name, series_code, database   # identity — never re-derived
  year, raw_value, transformed_value, score                  # value — varies by year
  polarity, log_transform, goalpost_min, goalpost_max        # how the score was made
  provenance: observed | carried_forward | interpolated | regional_mean | absent
```

Derived aggregates carry their own reliability:

```
PillarScore:  iso3, pillar_id, year, score,
              n_indicators, n_observed, coverage_ratio,
              reliability: reliable | thin | unreliable
CompositeScore: iso3, year, method, score, rank, n_pillars_used, reliability
```

`display_name`, `series_code`, and `variable_name` are **pulled from the record**, never
reconstructed in the UI — satisfying your requirement that the name is an independent
datapoint travelling with the value.

---

## 4. Workstream A — Panel rebuild (data + time series)

Folds in ROADMAP Phase 1 (per your sequencing decision): the GPI fix, the
`firm_foreign_owned` swap, and the log-rule reorder all land inside this rewrite, so
normalization is rewritten once and scores are invalidated once.

### 4.1 Time-series panel

- Extend the pull to a full panel: country × indicator × **year** (target start 2000; WGI is
  biennial pre-2002 — flag, do not interpolate across that boundary).
- `02_clean` stops collapsing to one value. Per-indicator window config gains:
  `window_mode` (point | rolling_mean), `window_years` (k), `max_carry_forward`.
- Transform order (Phase 1 decision): **raw → log1p (if flagged) → winsorize → goalpost min-max.**
  Log before winsorize removes today's double-compression.

### 4.2 Fixed goalposts (your decision)

- Compute min/max **once** over the full panel (all countries × all years), freeze into
  `registry/goalposts.yaml`, version it.
- Re-running the pipeline **never** silently recomputes goalposts; regeneration is explicit and
  changelogged.
- Values outside frozen bounds clamp to [0,100] and log a warning.
- Consequence: a country's score moves only when *its own* data moves. This is what makes the
  time slider honest. **All currently published scores change** — expected and intended.

### 4.3 Reliability and greying (your requirement)

Per (country, pillar, year): `coverage_ratio = n_observed / n_indicators`.

| Tier | Rule | UI |
|---|---|---|
| reliable | coverage ≥ 0.60 and < 50% of value from regional-mean | normal |
| thin | 0.40 ≤ coverage < 0.60 | muted + tooltip |
| unreliable | coverage < 0.40, or majority regional-mean | **greyed out + explicit message** |

Composite shown only when ≥5 of 7 pillars are at least `thin`. Applies to **recent years too**,
per your instruction — expect several current pillars to flip to greyed (`femicide` is 33% real,
`learning_poverty` 39%, `managed_water` 56%).

**This resolves the earlier femicide/learning_poverty question:** you chose to keep them rather
than drop them. The reliability system *is* the way to use sporadically-reported indicators —
they contribute where observed, and the interface is honest where they are not.

### 4.4 Time-varying edge cases to handle now

- **Country lifespans:** South Sudan pre-2011 did not exist; Sudan's series breaks at the split.
  Add `independence_year` / `panel_start` per country.
- **Series discontinuities:** deprecated codes (`EN.ATM.CO2E.PC` → `EN.GHG.CO2.PC.CE.AR5`)
  need an explicit continuity mapping, not a silent gap.
- **REC membership is itself time-varying** (Sahel exits, 2025). With a time slider, REC grouping
  must be year-aware or explicitly labelled "current membership".

---

## 5. Workstream B — UI

**Governing constraint: clutter is a correctness problem here.** Adding a pillar selector, a REC
selector, and a time slider naively takes the toolbar from 2 controls to 5. Net target: **stay at
two toolbar controls.**

### 5.1 Single "Lens" control (replaces the method dropdown)

One control answers "what is the map coloring?", with two grouped sections:

- **Overall** → Equal / PCA / BoD / Entropy / Geometric / Custom
- **Pillar** → A Governance … G Infrastructure

Selecting a pillar recolors the choropleth, the top/bottom lists, and rankings to that single
dimension — your continent-wide health-score view. Data already exists (`pillar_scores`); this is
a view change, not a computation change.

### 5.2 "Compare" control (replaces the island checkbox)

`All Africa | Region | REC` → choosing REC reveals an inline chip row of the 8 communities.
Non-members grey out on the map; rankings filter to members; a second selection enables
community-vs-community comparison. The island-state exclusion becomes a filter chip here rather
than a permanent checkbox.

### 5.3 Time slider — country pages only (your specification)

- **Not** on the continental overview.
- Lives on the country page, pinned under the header; **persists into pillar and indicator
  drill-down** via `nav-state` so the year survives navigation.
- Event flags rendered as ticks on the slider track (coups, elections, peace deals) sourced from
  the narrative `events` block (§6.1).
- When the selected year is `unreliable`, the panel greys and states why.

### 5.4 Per-pillar AI summaries

Rendered on the country → pillar view, **current data only** (per your instruction), clearly
labelled as AI-generated with a last-reviewed date and citations.

---

## 6. Workstream C — Narrative system

*The real narrative of the project.* All 54 country files are currently empty — this is
greenfield.

### 6.1 Blueprint — what every country receives

Defined once in `narrative/BLUEPRINT.md` + `asi/narrative/schema.py`; every country conforms:

```
narrative/countries/{ISO3}.yaml
  meta:        iso3, name, last_updated, iteration_count, next_action, model_used
  historical:  overview (APA, 150–250w), colonial_legacy (expands colonial_history.yaml),
               key_periods[{period, title, summary, citations[]}]
  pillars:     A..G → {summary (80–150w APA), drivers[], citations[]}
  recent:      primary[3]  (shown by default)
               extended[6] (dropdown → 9 total)
               each: {headline, date, summary, why_it_matters,
                      news_url, wikipedia_url, sentiment}
  events:      [{year, type: coup|election|conflict|peace_deal|constitutional|economic,
                 title, description, url, direction: improve|deteriorate|mixed}]
  citations:   [{claim_id, url, source_type: wikipedia|academic|news, accessed, verified}]
  balance:     {n_positive, n_negative, n_mixed, note}
```

Style: academic APA prose, cited, **not** full APA essay format (that stays a rare, explicitly
approved exception).

### 6.2 Ledger — the document future iterations read

`narrative/LEDGER.md` (human-readable) + `narrative/state.yaml` (machine-readable):

- **Completed:** country, iteration count, date, model, what was done.
- **Backlog (your explicit ask):** every country not yet filled, with a stub entry and reason —
  after the first 9, the other 45 are listed as to-dos so no country is silently forgotten.
- **Per-country `next_action`** written by the agent at the end of each run.
- **Global meta-notes:** what the agent should change about how it works.
- **Pending format proposals** awaiting your approval (never self-applied).

### 6.3 Two research passes and the iteration policy

**Pass 1 — Historical** (`narrative/prompts/historical.md`): background, colonial legacy, key
periods. Wikipedia-primary, every claim cited.

**Pass 2 — Recent developments** (`narrative/prompts/recent.md`): rapidly-developing situations —
3 primary, 6 extended. **Both** a news URL and a relevant Wikipedia URL by default. Conflict
developments *and* democratic wins.

**Rotation policy** (you asked me to clarify this):

| Iteration | Mode | Action |
|---|---|---|
| 1 | CREATE | Build baseline from blueprint |
| 2–3 | EXPAND | Add depth, periods, citations |
| **4** | **AUDIT** | **No new content.** Verify every citation resolves *and* supports its claim; hunt hallucinations; check framing balance; remove unsupported claims |
| 5–7 | EXPAND | … |
| 8 | AUDIT | repeat every 4th run |

Forced early audit trigger: citation count grows >50% in one run. Rationale: a self-updating
instruction document drifts toward "add more" indefinitely; the audit pass is the only
counterweight, so it must be scheduled, not optional.

### 6.4 Framing balance — enforced, not aspirational

- Metaprompt requires: where evidence supports it, document at least as many concrete
  developments/achievements as challenges.
- Structural attribution required — name extraction, debt architecture, commodity dependence
  rather than implying inherent dysfunction.
- `balance` block records counts per country; the AUDIT pass explicitly tests for negativity skew
  and exoticism.
- Conflict is still reported plainly. The target is proportion, not omission.

### 6.5 Model selection (Anthropic only, token-efficient)

| Model | Use | Why |
|---|---|---|
| **Haiku 4.5** | Link liveness checks, citation formatting, schema validation, balance counting | Mechanical, high volume, cheap |
| **Sonnet 5** | Historical synthesis, per-pillar summaries, news gathering | Best cost/quality for web-grounded writing; the workhorse |
| **Opus 5** | Iteration-4 AUDIT, ledger meta-notes, metaprompt revisions | Hallucination detection and self-critique need the strongest reasoning |

Efficiency: **one call per country covering all 7 pillars** (shared country context) instead of 7
calls — roughly 5× context savings. Keep blueprint + style guide in a stable prompt prefix so
caching applies across countries.

### 6.6 First run (your specification)

Blueprint first → generate **9 countries** → log each in the ledger → **write the remaining 45 to
the backlog as explicit to-dos**. Suggested 9 for maximum variance: MUS, GHA, DZA, COD, SOM, BWA,
NGA, RWA, TCD.

---

## 7. Workstream D — Verification restructure

Per your instruction: strip evaluation out of the main program; make it a separate, independent
replicator.

### 7.1 What leaves the pipeline

Remove from `02_clean` etc.: Cronbach gate, coverage warnings, `sys.exit(1)` calls.
**Keep only** hard safety gates: schema validation on load, and catastrophic-data-loss guards.
Delete `validate_stage1.py`.

### 7.2 `verify/` — independent program, three layers

| Layer | File | Job |
|---|---|---|
| **Replication** | `replicate.py` | Recompute the entire panel from frozen raw with independent implementations (extends today's `00_evaluate.py` to the time dimension) |
| **Contract** | `contract.py` | **New — your "same object" requirement.** For every element the UI renders, assert a bundle record exists with identical `variable_name`, `display_name`, `series_code`, `year`, `value`. Headless-render the dashboard, scrape displayed values, match against the bundle. Catches re-derivation, re-labelling, and stale UI strings |
| **Advisory** | `advisory.py` | Design diagnostics as a **report, not pass/fail**: correlations, effective weights, coverage, staleness, framing balance |

Aggregation check (your requirement): indicator scores → pillar scores → composite must
reconcile across backend math, stored bundle, and rendered frontend.

---

## 8. Sections you must manually verify — assume issues exist

**Tier 1 — blocks correctness**
1. **REC membership** in `models/countries.py` against your Excel. Counts to check: ECOWAS 12,
   COMESA 21, CEN-SAD 25, SADC 16, ECCAS 10, EAC 8, IGAD 6, UMA 5.
2. **Fixed goalposts** once generated — flag any indicator whose min or max is set by an
   *imputed* value rather than an observation.
3. **Polarity, all 32 indicators** — priority: both GPI indicators, `co2_pc`, `agri_land`,
   `nonrenew_elec`.
4. **Log-transform flags** after the new rule is applied.
5. **Reliability thresholds** — spot-check 5 countries where a pillar flips to greyed; is the
   call defensible?

**Tier 2 — narrative integrity (highest hallucination risk)**
6. Every citation in the first 9 countries: URL resolves **and** supports the claim.
7. Framing balance in the first 9 — read for negativity skew.
8. Event flags (coup/election dates) against an independent source.
9. `colonial_history.yaml` — 1,188 lines, never audited.
10. Per-pillar AI summaries vs actual indicator values — does the prose match the numbers?

**Tier 3 — structural**
11. Cross-listing effective weights after any registry change.
12. Aggregation windows per indicator.
13. Token/cost actuals after the first 9, extrapolated to 54.

---

## 9. Senior-review critique — vulnerabilities, edge cases, AI tendencies

### 9.1 Code and architecture

1. Numbered modules block imports *and* unit testing — the `importlib` hack in `app.py` is a
   symptom, not the disease.
2. Excel as inter-stage transport: lossy, slow, 500KB binaries in git. Parquet for interchange.
3. `sys.exit(1)` inside pipeline logic is untestable and uncatchable.
4. Dashboard re-derives backend work (4 file reads, recomputes ranks and custom scores) — the
   direct violation of your "same object" principle.
5. `suppress_callback_exceptions=True` plus bare `except Exception: pass` in `_load()` hides real
   failures.
6. No unit tests — a one-line change in `_agg_group` fails nothing until a full pipeline run.
7. Global mutable `ACTIVE_PRESET` (already caused a Python 3.14 `global` SyntaxError).
8. Ad-hoc confidence band (`2.0 + 26.7 × pct_filled`) — undocumented magic constants.
9. PCA on 7 correlated pillars yields a "general development" axis; using it as weights is close
   to circular. Keep as sensitivity, never headline.
10. Entropy weights shift when the country set changes — breaks cross-edition comparison.

### 9.2 Edge cases to design for now

Country lifespans (South Sudan 2011, Eritrea 1993) · Sudan series break at the split ·
deprecated series mid-panel · goalpost clamping when new data exceeds frozen bounds ·
WGI biennial pre-2002 · negative values into `log1p` · REC membership changing mid-panel ·
all-NaN pillar-year silently averaging to a partial composite · Western Sahara/Morocco
territorial ambiguity in map rendering.

### 9.3 AI failure modes this project is specifically exposed to

1. **Hallucinated citations** — plausible, well-formatted, nonexistent URLs. Machine-validate
   every link; never trust a model-supplied source.
2. **Confident prose over thin data** — fluent paragraphs about a pillar that is 60% imputed.
   Gate narrative generation on the same reliability flags as the UI.
3. **Recency illusion** — training-cutoff knowledge presented as current news. Require web
   search plus explicit publication dates.
4. **Homogenization** — 54 structurally identical paragraphs. Test for distinctiveness.
5. **Sycophantic drift in the self-updating ledger** — it will trend toward "add more detail"
   forever. The scheduled AUDIT pass is the designed counterweight.
6. **Negativity and exoticism bias about Africa** — your central concern, and a real property of
   the training distribution. Requires the measured balance audit, not good intentions.
7. **Silent scope creep** — refactoring adjacent code unasked.
8. **Verification overfitting** — tests that encode today's values instead of invariants.
9. **False precision** — two decimals on a regional-mean-derived number.
10. **Additive-only iteration** — never removing content that turns out wrong.

### 9.4 Qualitative reasoning — why polarity, why this value

Extend each indicator record with a **construct rationale**: latent concept · direction claim and
mechanism (why this polarity) · operationalization rationale (why this series, window, transform)
· **falsification condition** (what evidence would change the choice) · `last_reviewed` + reviewer.

**Review cadence** (you left this to my discretion):

- **Automatic trigger** — verification flags any indicator with a negative item-rest correlation,
  |ρ| > 0.85 against another indicator, or coverage below threshold → mandatory review before the
  next publish.
- **Scheduled** — polarity/log/window review each edition (biennial, IIAG model); narrative audit
  every 4th iteration; full methodology review annually.
- **On-change** — any registry edit updates the construct rationale and `references.md` in the
  same commit, enforced by `verify/`.

---

## 10. Phasing

| Phase | Scope | Scores change? |
|---|---|---|
| **A. Foundation** | Package restructure, canonical schema, verification merge, delete dead scripts | No |
| **B. Panel rebuild** | Time-series pull, fixed goalposts, reliability tiers, **Phase 1 construct fixes folded in** | **Yes — re-baseline** |
| **C. UI** | Lens control, Compare/REC control, time slider, greying | No |
| **D. Narrative** | Blueprint, ledger, metaprompts, first 9 countries + 45-country backlog | No |
| **E. Scale** | Remaining 45 countries, external validation vs IIAG/FSI | No |

Phase A is deliberately first and score-neutral: it makes B testable.

---

## 11. Verification of this work

- **Phase A:** `verify/` runs green on unchanged data; dashboard renders identically
  (byte-compare bundle before/after restructure); `pytest` unit tests pass for pure functions.
- **Phase B:** replication layer reproduces every panel cell independently; goalposts file is
  frozen and diffable; manually confirm ~5 greying decisions; re-baseline and record the score
  delta table.
- **Phase C:** headless render checks per view; contract layer confirms every displayed value
  traces to a bundle record; toolbar control count stays at 2.
- **Phase D:** every citation machine-validated (HTTP + claim support); balance counts recorded;
  ledger backlog lists exactly the 45 unfilled countries.
- **Ongoing:** `verify/` is the single gate before any publish; advisory report reviewed, not
  auto-enforced.
