# Backlog

**How to use this.** Pick the topmost item you can start, hand a session its prompt and nothing
else, tick it here when it lands. This file supersedes the scattered queues — `ITERATION_PLAN.md`,
`MANUAL_REVIEW.md`, `ROADMAP.md`, `METHODOLOGY_REVIEW.md` §D, `state.yaml:pending_format_proposals`,
and the `LEDGER.md` meta-notes. Read those for evidence, not for what to do next.

*Built 2026-08-16 by sweeping all eight sources and verifying every status against the code and
`git log`, not against any document's checkbox.*

**Conventions.** The numbered `B` list below is the OPEN work, in order. Items verified complete
are in **Completed** with `D` ids. Older phrasings of a listed item are in **Duplicates resolved**
with the surviving id. Order is: blocking items first, then impact ÷ effort, then items needing a
human decision. Effort is in hours for one maintainer. `Human?` means the item cannot finish
without a decision only you can make.

---

Things that are not defects — what goes stale, what needs a decision from the maintainer, what to update when the project's shape changes — live in [`TODO.md`](TODO.md), not here.

Statistical-method work is planned in [`STATISTICS.md`](STATISTICS.md): the end state, its preconditions, and the near-term items N1–N6 below. Read §3 there before adding indicators — under equal pillar weights, adding one indicator to a four-indicator pillar cuts every existing indicator in it by 20%.

## The list

| ID | Title | Effort | Human? | Depends on | Source |
|---|---|---:|:---:|---|---|
| **N1** | Incremental goalposts: freeze bounds for new indicators only | 4 | no | — | STATISTICS §4 (blocks indicator growth) |
| **N2** | Indicator admission screening script | 5 | no | N1 | STATISTICS §4 |
| **N3** | Publish effective indicator weights (advisory → methodology + UI) | 3 | no | — | STATISTICS §4 |
| **N6** | State which composite is the headline method, and why | 1 | **yes** | B17 | STATISTICS §4 |
| **B07** | Restore TLS verification on the data pull; manifest the baseline | 3 | **yes** | — | ITERATION_PLAN "Out of band" |
| **B11** | Strike the phantom Benefit-of-the-Doubt limb | 2 | **yes** | — | ITERATION_PLAN 1.3 (D8, ASI-04/17) |
| **B12** | Make corpus loading fault-tolerant and imports side-effect-free | 4 | no | — | ITERATION_PLAN 1.6 (ASI-03) |
| **B13** | Stop the country page reporting a continental rank as "in scope" | 3 | **yes** | — | ITERATION_PLAN 1.5 (ASI-02) |
| **B14** | Make documentation describe the code that exists | 4 | no | — | ITERATION_PLAN 1.4 (ASI-16, D8) |
| **B15** | Delete the shadow registry and the dead weight | 3 | **yes** | — | ITERATION_PLAN 1.8 (ASI-11/17) |
| **B16** | Decide what an `unreliable` pillar does to the composite | 6 | **yes** | — (B02 done) | ITERATION_PLAN 2.1 (D1) |
| **B17** | Resolve what Pillar F measures | 3 / 20–30 | **yes** | — (B02 done) | ITERATION_PLAN 2.3 (D3) |
| **B18** | Collapse the WGI family and remove cross-listing | 4 / +15 | **yes** | — (B02 done) | ITERATION_PLAN 2.4 (D4) |
| **B19** | Re-anchor goalposts that rest on imputed extremes | 6 | **yes** | — (B02 done) | ITERATION_PLAN 2.5 (U1) · MANUAL_REVIEW 1 |
| **B20** | Publish rank intervals instead of point ranks | 12 | **yes** | — (B02 done) | ITERATION_PLAN 2.2 (D2) |
| **B21** | State or replace the missing-data assumption | 2 / 10 | **yes** | — (B02 done) | ITERATION_PLAN 2.6 (U3) |
| **B22** | Re-derive the log-transform flags under an explicit rule | 3 | **yes** | — (B02 done) | MANUAL_REVIEW 4 · ROADMAP P1d · METHODOLOGY_REVIEW C8 |
| **B23** | Spot-check the reliability thresholds | 2 | **yes** | B16 | MANUAL_REVIEW 5 |
| **B24** | Add per-pillar Cronbach's α to `verify/advisory.py` | 1 | no | — | ITERATION_PLAN 3.2 · ROADMAP P3a |
| **B25** | Publish a per-pillar imputation table | 2 | no | — | ITERATION_PLAN 3.3 |
| **B26** | Document the winsorisation consequence | 1 | no | — | ITERATION_PLAN 3.4 |
| **B27** | Report PCA dimensionality wherever PCA weights appear | 3 | **yes** | — | ITERATION_PLAN 3.7 · MANUAL_REVIEW 9 |
| **B28** | Document the goalpost revision policy | 2 | **yes** | B19 | ITERATION_PLAN 3.5 |
| **B29** | Rewrite `METHODOLOGY_REVIEW.md` against the code that exists | 4 | no | B14 | ITERATION_PLAN 3.6 · 1.4 note |
| **B30** | Surface the Monte Carlo intervals in the interface | 6 | no | B20 | ITERATION_PLAN 3.1 |
| **B31** | Full-sample external validation against IIAG 2024 and FSI 2025 | 4 | no | — | ROADMAP P5 · METHODOLOGY_REVIEW A9 |
| **B32** | Ship the four transparency disclosures in the dashboard | 5 | no | — | ROADMAP P4 · MANUAL_REVIEW T3 |
| **B33** | Audit REC membership and decide whether it varies by year | 3 | **yes** | — | MANUAL_REVIEW 2 · LEDGER 2026-08-11 (SEN/CEN-SAD) |
| **B34** | Decide what 2001 and 2024 look like | 2 | **yes** | — | MANUAL_REVIEW 6 + 7 |
| **B35** | Give each country an explicit `panel_start` | 2 | no | — | MANUAL_REVIEW 8 |
| **B36** | Decide the carry-forward policy for the five never-measured indicators | 3 | **yes** | — | MANUAL_REVIEW 11 · METHODOLOGY_REVIEW C5 |
| **B37** | Confirm the score-compression interpretation under fixed goalposts | 1 | **yes** | — | MANUAL_REVIEW 10 |
| **B38** | Confirm the aggregation window for each indicator | 2 | **yes** | — | MANUAL_REVIEW T3 |
| **B39** | Pull the AUDIT limb forward for a sample | 4 | **yes** | — | ITERATION_PLAN 4.4 · MANUAL_REVIEW T4 |
| **B40** | Version the narrative schema and build a migration path | 12 | **yes** | — | ITERATION_PLAN 4.2 (ASI-10) · state.yaml proposals 2+3 |
| **B41** | Key every path and singleton on the region profile | 20–30 | **yes** | — (B01 done) | ITERATION_PLAN 4.1 (ASI-06) |
| **B42** | Split the narrative journal from the work queue | 5 | **yes** | — | ITERATION_PLAN 4.3 (ASI-19) |
| **B43** | Surface `robustness.json` in the Methodology tab | 2 | no | B09 | ITERATION_PLAN 5.4 |
| **B44** | Drop `dash_bootstrap_components` | 1 | no | — | ITERATION_PLAN 5.5 |
| **B45** | Add URL routing | 6 | no | — | ITERATION_PLAN 5.3 |
| **B46** | Accessibility and legibility | 14 | **yes** | — | ITERATION_PLAN 5.2 |
| **B47** | Decompose `app.py` | 16 | no | — (B01 done) | ITERATION_PLAN 5.1 |
| **B48** | Work the 54 per-country EXPAND queues | ~1.5 each | no | — | `narrative/countries/*.yaml` `meta.next_action` |
| **B49** | Cross-record consistency sweep of the paired threads | 4 | no | — | LEDGER meta-notes (9 flagged pairs) |
| **B50** | Audit `context/colonial_history.yaml` | 3 | no | — | MANUAL_REVIEW T4 |
| **B51** | Read the first nine records for negativity skew | 1 | **yes** | — | MANUAL_REVIEW T4 |
| **B52** | Panel integrity: manifest and fail-closed loading | 3 | **yes** | — | ITERATION_PLAN 6.2 |
| **B53** | Pre-deploy bundle: pin, CI, vendor the CDN, `--preload` | 4 | no | B52 | ITERATION_PLAN 6.1 / 6.3 / 6.4 / 6.5 |
| **B54** | Quick wins (under 15 minutes each) | 0.5 | no | — | state.yaml · this file |

**Carried dependency logic.** `ITERATION_PLAN` Stage 0 blocks Stages 2, 4 and 5. That is
B01–B06 blocking B16–B23 (Stage 2), B39–B42 (Stage 4) and B43–B47 (Stage 5). The table records
the specific edges the plan states. Both are now released. **B01 is done** (`7ba8cb7`): it
gated B41 and B47, which move code into subdirectories the contract checks could not see, and
those checks now recurse. **B02 is done** (`d6a316d`): it gated every Stage 2 item because
those edit arithmetic that had no tests, and that arithmetic is now covered and
mutation-checked. **B03 is done** (`f3ef6f9`): it gated B39–B42, whose whole subject is
comparing this index against outside benchmarks — a benchmark layer that loads the panel
through the interface's own loader is comparing the index against a filtered view of itself.
**B04 is done** (`8704853`): the narrative corpus now has one validator rather than two disagreeing ones. **B05 is done** (`40e362a`): every scoring indicator now has a re-derivation path, so Stage 2's arithmetic edits land on a panel that is checked rather than assumed. **B06 is done** (`1e7b9f7`, `82495ba`): the view tests can now fail, which is what Stages 4 and 5 need before they start moving view code into subdirectories.

**Stage 0 is complete.** Stages 2, 4 and 5 are unblocked; every remaining dependency edge in the table is released. **Stage 1's autonomous items (B08–B10) are also done** (`e5ae2dc`); B07 remains, and needs the maintainer's own network knowledge.

---

## Prompts

### B01 — Make the contract checks fail on what they were written to catch

> In `F:\Code\African Stability Index`, `verify/contract.py` checks 2.1/2.2/2.3 are
> too weak. Prove it first: point `UI_DIR` at a temp directory and confirm that
> `"54 of 55 AU member states"` passes check 2.1, that `PILLAR_DEFS: dict = {}`
> passes 2.2, and that a file containing all three violations inside a `views/`
> subdirectory passes all three (because `_ui_files()` at line 139 uses
> `glob("*.py")`, not `rglob`). Then fix: recurse into subdirectories; generalise
> the 2.1 regex from four exact nouns to any digit literal adjacent to a domain
> noun; make 2.3 AST-based (detect `Call` to `open`/`read_csv`/`safe_load`) rather
> than a substring grep; extend 2.2 to `AnnAssign` and class bodies, matching the
> stronger implementation already in `tests/test_ssot.py:54`. Add
> `tests/test_verify_contract.py` with a fixture list of must-fail strings for each
> check. Finally fix the live offender at `asi/dashboard/app.py:1019`, which types
> `55` while `app.py:894` derives the same number from `EXCLUDED_AU_MEMBERS`.

### B02 — Unit-test the scoring arithmetic; verify the geometric composite

> In `F:\Code\African Stability Index`, no test imports `asi.pipeline.score` or
> `asi.pipeline.goalposts`, and `verify/panel.py:286` re-derives only
> equal/pca/entropy. Confirm the gap: add 40 to a `geometric` row in a copy of
> `data/panel/composites.csv` and re-run `check_composites` — it passes, so 1,350
> of 5,400 published rows are checked by nothing. Write `tests/test_score.py` and
> `tests/test_goalposts.py` covering weight renormalisation when a pillar is NaN
> (a path that has never fired on real data), geometric flooring at `SMALL`, PCA
> zeroing rather than absolute-valuing a negative loading, entropy on a degenerate
> column, `_round_outward` direction, and `load()` on a version mismatch. Extend
> `verify/panel.py` to re-derive the geometric composite independently. Report —
> do not decide — whether Benefit-of-the-Doubt should be implemented or removed
> from `asi/dashboard/app.py:52`, `requirements-pipeline.txt` and the docstrings.

### N1 — Incremental goalposts: freeze bounds for new indicators only

> In `F:\Code\African Stability Index`, `registry/goalposts.yaml` is frozen at
> `GOALPOSTS_VERSION = 2` and `02_panel.py --freeze-goalposts` recomputes every
> indicator's bounds, so adding one indicator re-anchors every historical score for
> all 32. Add an incremental mode that computes bounds only for indicators absent
> from the frozen file, leaves existing entries byte-identical, and records which
> panel window each entry was derived from. Bump `GOALPOSTS_VERSION` and keep
> `load()`'s version check meaningful. Prove it: freeze, add a synthetic indicator,
> re-freeze incrementally, and assert every pre-existing bound is unchanged and
> every published score is identical.

### N2 — Indicator admission screening script

> In `F:\Code\African Stability Index`, adding an indicator currently has no
> gate. Write `scripts/screen_indicator.py <variable_name>` reporting, for a
> candidate already present in the raw pull: coverage by country and year, share
> observed vs carried-forward vs regional-mean, variance and a degenerate-column
> check, maximum |rho| against every existing scoring indicator (flagging above
> 0.80), and the before/after effective weight of every indicator in the pillar it
> would join. It refuses nothing — it makes the cost visible before the commit.
> Depends on N1, since a screened indicator has to be addable without re-anchoring.

### N3 — Publish effective indicator weights

> In `F:\Code\African Stability Index`, `verify/advisory.py` computes effective
> per-indicator weights and prints them to a log nobody reads. Equal pillar weights
> are not equal indicator weights: `pv_estimate` and `rl_estimate` carry 5.95% of
> the composite, `primary_gpi` 1.79% — a 3.33x spread nobody chose. Surface the
> table in the methodology page and in the interface's methodology panel, derived
> at render time so it cannot go stale. A reader told "pillars are equally
> weighted" currently has no way to learn this.

### N6 — State which composite is the headline method, and why

> In `F:\Code\African Stability Index`, four composites are published (`equal`,
> `geometric`, `pca`, `entropy`) and nothing says which is the index's answer.
> Write the paragraph: which is the headline, what the others are for, and why.
> Depends on B17 — see `STATISTICS.md` §2.1: geometric aggregation currently
> penalises Algeria 29 places, and 6 of the 8 countries it penalises most have
> Pillar F as their worst pillar, so promoting geometric before Pillar F is fixed
> would amplify a known defect rather than reduce compensability.

### B07 — Restore TLS verification on the data pull; manifest the baseline

> In `F:\Code\African Stability Index`, `01_pull.py:26-38` monkeypatches
> `requests.Session.merge_environment_settings` to force `verify=False`
> process-wide. Reproduce the original failure first: unset the patch, run a single
> `wbgapi` fetch, and record the exact certificate error — that identifies which CA
> is intercepting. Then export that CA with `certutil -store Root`, point
> `REQUESTS_CA_BUNDLE` at the PEM, delete the monkeypatch, and confirm the pull
> succeeds with verification on. Re-pull on a clean network and compare the SHA-256
> of the result against `data/baseline/01_raw_pull_BASELINE.xlsx`; record the digest
> whether or not it matches. Also write a manifest beside the baseline — digest,
> pull date, wbgapi version, row count — because `data/01_raw_pull.xlsx` and the
> baseline are currently byte-identical with nothing distinguishing "unchanged"
> from "silently overwritten". Done looks like: `01_pull.py` contains no `verify`
> override, the pull works, and both files carry recorded digests.
>
> This needs the maintainer's own knowledge of the network. `verify/panel.py`
> re-derives the entire published index from that baseline, so a substituted
> baseline would reconcile perfectly through every downstream check.

### B11 — Strike the phantom Benefit-of-the-Doubt limb

> In `F:\Code\African Stability Index`, Benefit-of-the-Doubt is documented in
> `methodology/METHODOLOGY_REVIEW.md`, labelled in `asi/dashboard/app.py:52`
> (`"bod": "Benefit of the doubt"`), justified by `WEIGHT_MIN`/`WEIGHT_MAX` in
> `asi/core/constants.py:60-61` ("bounds per pillar in the BoD LP"), depends on
> `pulp` in `requirements-pipeline.txt`, and is claimed by `verify/__init__.py` to
> be verified with "scipy HiGHS instead of pulp/CBC" — but no LP exists anywhere
> and `data/panel/composites.csv` contains four methods. Confirm the maintainer
> wants it removed rather than implemented, then delete the label, the `pulp`
> dependency and the docstring claims, and rename `WEIGHT_MIN`/`WEIGHT_MAX` to
> reflect their only remaining use (the robustness sampler).

### B12 — Make corpus loading fault-tolerant and imports side-effect-free

> In `F:\Code\African Stability Index`, `asi/narrative/store.py:390` catches only
> `yaml.YAMLError`, so a shape-valid record with a wrong type (e.g.
> `pillars: {A: "a string"}`) raises `AttributeError` from `parse()`. Because
> `asi/dashboard/app.py:96` calls `load_corpus()` at module import, that is a boot
> failure — gunicorn workers crash-loop with no page at all, from one malformed
> field in an LLM-authored file. Separately, an unparseable file is skipped with no
> output at all, and the country page then renders "No narrative record for X yet…
> has not run", which is false. Reproduce both in a temp corpus. Then catch broad
> exceptions per record, log the path at WARNING, distinguish "failed to load" from
> "not yet written" in `no_record_notice`, and make `PANEL`/`NARRATIVE` lazily
> loaded so importing the module performs no I/O.

### B13 — Stop the country page reporting a continental rank as "in scope"

> In `F:\Code\African Stability Index`, `asi/dashboard/app.py:1109` and `:1111`
> drop the Compare grouping when rendering country and pillar pages, so
> `app.py:525` renders the stored continental rank under the label "in scope".
> With Compare = ECOWAS, Ghana's country page shows "#7 · Rank · in scope" while
> its actual rank within ECOWAS is #2 of 12. Reproduce that, then decide with the
> maintainer whether the country page should follow the grouping or say
> "continental", implement it, and add a regression test. Root cause is
> architectural: `asi/results.py:6` states the module never computes a rank, while
> two of its own functions do, so two disagreeing ranks exist. (The module was
> `asi/dashboard/data.py` until B03 moved it.)

### B14 — Make documentation describe the code that exists

> In `F:\Code\African Stability Index`, several documents describe a retired
> architecture. Write a script extracting `*.py`/`*.yaml` references from
> `README.md`, `methodology/*.md`, `verify/__init__.py` and `verify/run.py` and
> reporting those that do not exist — expect ~14 hits including `02_clean.py`,
> `03_normalize.py`, `04_score.py`, `05_robustness.py`, `00_audit.py`,
> `00_evaluate.py`. Correct every reference. Rewrite `verify/__init__.py`'s
> docstring and `__all__`, which describe three layers named replicate/contract/
> advisory when four exist (panel, contract, narrative, advisory). Fix
> `verify/run.py:5`'s `--layer replicate` example, which argparse would reject,
> and `README:51`'s "three layers". Update the `assets/asi.css` comment referring
> to six methods including "Custom Weights". Then turn the script into
> `tests/test_docs_reference_real_files.py`. Note `methodology/METHODOLOGY_REVIEW.md`
> needs a full rewrite against the current pipeline — do that as its own session.

*Also in scope, same class of defect: `methodology/references.md:296-320` cites
`05_robustness.py`, `02_clean.py` and `04_score.py`, none of which exist.*

### B15 — Delete the shadow registry and the dead weight

> In `F:\Code\African Stability Index`, `scripts/add_indicators.py` is a 655-line
> imperative duplicate of `indicators_list/*.yaml` that executes on import with no
> `__main__` guard. Parse its `add_if_missing(...)` calls with `ast` and diff
> against the YAML registry: it defines 5 indicators that no longer exist, misses 2
> that do, and disagrees on 4 fields — including `agri_land.polarity`, where the
> script says `negative` and the registry says `positive`. Confirm nothing imports
> it and delete it. In the same session remove: the empty `models/` directory, the
> root `dash_errors.txt`/`*.log` scratch files, and the unread
> `context/pillar_justifications.yaml` and `methodology/references.yaml` (verify no
> reader first). Ask before deleting `qualitative/` — all 54 files parse to empty
> dicts and `asi/dashboard/app.py:89` is their only reader, but confirm it is
> superseded by `narrative/` rather than aspirational.

### B16 — Decide what an `unreliable` pillar does to the composite

> In `F:\Code\African Stability Index`, `asi/pipeline/score.py:116`
> `weighted_composite` ignores the `reliability` column, so pillars classified
> `unreliable` enter the composite at full weight. Implement an option to exclude
> non-displayable pillars from aggregation, exercise the weight-renormalisation
> path in `weighted_composite` (which has never fired — no country-year currently
> has a missing pillar), report how many pillars backed each composite, and
> quantify the rank change against the published `data/panel/composites.csv`. Do
> not change the reliability thresholds themselves. Present (a) exclude, (b)
> down-weight by coverage, and (c) keep the arithmetic but relabel the tier as
> display-confidence-only, with the rank impact of each.

### B17 — Resolve what Pillar F measures

> In `F:\Code\African Stability Index`, present three costed options for Pillar F
> and compute each one's effect on the 2023 ranking versus the published
> `data/panel/composites.csv`: (a) reframe F as environmental vulnerability and
> exposure on the ND-GAIN model, which loads positively with the rest; (b) replace
> `co2_pc` with emissions intensity per unit GDP, or an income-residualised
> per-capita measure; (c) remove F from the headline composite and publish it as a
> satellite dimension. Removing F entirely is already known to give Spearman 0.942
> against the published ranking with a maximum shift of 25 places (Libya 42→17).
> This is a framework decision about what "stability" means — `METHODOLOGY_REVIEW.md`
> step 1 records that the question was never settled. Do not choose unilaterally.

*Carry into the same session, from `ROADMAP.md` Phase 2 and `MANUAL_REVIEW` item 3:
the `nonrenew_elec` ↔ `elec_access_tot` contradiction (G penalises what F rewards),
and `agri_land`'s contested positive polarity. Both are Pillar F polarity calls and
should be settled with the frame, not before it. Acceptance criterion from the
roadmap: all Pillar F item-rest correlations > 0.3 and PCA no longer excludes F.*

### B18 — Collapse the WGI family and remove cross-listing

> In `F:\Code\African Stability Index`, prototype collapsing the six WGI dimensions
> into a single governance factor placed in Pillar A only, with no cross-listing
> (known result: Spearman 0.945 versus published, max shift 21 places). Report
> which indicators would need to be sourced to refill Pillars E and G, which the
> change substantially empties. Do not commit — present for a decision.

### B19 — Re-anchor goalposts that rest on imputed extremes

> In `F:\Code\African Stability Index`, 19 of 32 frozen goalposts in
> `registry/goalposts.yaml` carry `min_from_imputed` or `max_from_imputed`; four
> (`gini`, `intent_homicide`, `learning_poverty`, `social_protection_labour_pop`)
> have both. Bounds are frozen permanently, so an imputed extreme fixes the scale
> for every country and year, forever. Start by listing the 19 with their bounds
> and the ISO3/year each extreme came from, so the decision is made against real
> rows rather than the table in `MANUAL_REVIEW.md`. Then take the four both-ends
> cases first and, per indicator, choose: accept the imputed bound, substitute a
> theoretical bound where one exists (GPI parity is 1.0 by construction; literacy
> and enrolment are 0–100), or restrict the bound to observed values only. Note
> `primary_gpi`/`secondary_gpi` max of exactly 1.000 is correct by construction —
> only their MIN needs review. Done looks like: a decision recorded per indicator,
> the goalposts file regenerated deliberately, and the rank delta against the
> published `data/panel/composites.csv` reported.

### B20 — Publish rank intervals instead of point ranks

> In `F:\Code\African Stability Index` there is no uncertainty analysis —
> `03_robustness.py` varies one assumption at a time and reports point Spearmans.
> Add a joint Monte Carlo (OECD/JRC Handbook step 7; Saisana, Saltelli & Tarantola
> 2005): sample pillar weights on the simplex subject to `WEIGHT_MIN`/`WEIGHT_MAX`
> using `w = 0.05 + 0.65 * Dirichlet(1^7)`, bootstrap indicator membership within
> each pillar, and optionally toggle imputed cells off. Emit median rank and a 95%
> rank interval per country-year into `data/panel/composites.csv`. A prior 2,000-draw
> run at 2023 gave a median CI width of 22 places and 29.4% pair separability —
> reproduce and confirm those before wiring anything into the dashboard. Then
> propose how the interface should show a rank it cannot resolve to one number.

### B21 — State or replace the missing-data assumption

> In `F:\Code\African Stability Index`, regional-mean fill in
> `asi/pipeline/panel.py:regional_fill` is *single* imputation: variance is
> understated by construction and filled countries within a region receive
> identical values. Missingness is also unlikely to be MAR — the countries failing
> to report homicide, Gini or learning poverty are disproportionately
> conflict-affected, so filling them with a regional mean pulls them toward the
> average and flatters exactly the states the index should discriminate. Run the
> cheap version first (2h): rebuild composites with regional fills excluded, and
> report the rank change for the ten countries with the most filled cells — does a
> conflict state's rank fall when its fills are removed? Present the result with
> two options: state the assumption and its direction of bias in the methodology
> text, or move to multiple imputation (10h). Done looks like: the sensitivity
> number exists and the assumption is written down somewhere a reader sees it.

### B22 — Re-derive the log-transform flags under an explicit rule

> In `F:\Code\African Stability Index`, five indicators carry `log_transform: true`
> in `indicators_list/*.yaml` (`pillar_b.yaml:19`, `pillar_d.yaml:59,131`,
> `pillar_e.yaml:36,62`) but the flags are inherited, not derived — the stated rule
> "log1p iff post-fill skew > 1 and min >= 0" has never been applied. Reproduce
> first: compute post-fill, pre-winsorisation skew for all 32 scoring indicators
> from `data/panel/observations.csv` and list which currently-unflagged indicators
> exceed skew 1.0 (`METHODOLOGY_REVIEW.md` C8 expects seven: firm_foreign,
> inflation, social_protection, co2_pc, hand_washing, freshwater, managed_water —
> note firm_foreign_owned has since been replaced, so confirm against live data).
> Also check `mort_infant`, previously double-treated. Then get a decision on the
> rule, apply it uniformly, update the YAMLs and their justifications, re-freeze
> goalposts, and report the rank delta. Transform order (log before winsorize) is
> already correct.

### B23 — Spot-check the reliability thresholds

> In `F:\Code\African Stability Index`, `asi/core/constants.py` sets
> `reliable >= 0.60`, `thin >= 0.40`, with an imputed share above 0.50 vetoing —
> yielding 7,043 reliable / 1,225 thin / 1,182 unreliable pillar-years. These three
> numbers decide what the public sees as a score versus a grey box. Pull five
> country-pillar-years sitting just either side of each boundary, print their
> underlying coverage and imputed share, and judge whether the call is defensible
> in each case. Done looks like: either the thresholds are confirmed with the five
> worked examples recorded, or new values are chosen and the display consequence
> quantified. Do this after B16, which decides what the tier does to the
> arithmetic — the threshold matters more once it does something.

### B24 — Add per-pillar Cronbach's α to `verify/advisory.py`

> In `F:\Code\African Stability Index`, `verify/advisory.py` reports effective
> weights, source concentration and redundancy but not internal consistency. Add a
> per-pillar Cronbach's α section computed on **polarity-corrected normalised**
> scores, not raw values — computing it on raw mixed-polarity values is what made
> the old diagnostic uninterpretable (`METHODOLOGY_REVIEW.md` C9). Measured at
> 2023 the answers are A 0.958, B 0.507, C 0.589, D 0.809, E 0.472, F 0.608,
> G 0.799; all 32 indicators as one scale give 0.810. Reproduce those numbers
> before reporting them. Print each against the project's own `MIN_CRONBACH_ALPHA`
> gate of 0.60 and note that three pillars fail it while A fails upward
> (redundancy, not reliability). Done looks like: `python -m verify.run --layer
> advisory` prints the table and the numbers match.

### B25 — Publish a per-pillar imputation table

> In `F:\Code\African Stability Index`, only a cell-level imputation figure is
> documented (74.19% observed overall) while the reference year is 39.0% imputed
> and Pillar C is 82.4%. Derive the per-pillar, per-year observed/carried/imputed
> shares from `data/panel/observations.csv`, add them to `verify/advisory.py`, and
> surface the reference-year row in the dashboard's Methodology tab. Done looks
> like: a reader can see that Pillar C is 82.4% imputed without running anything.

### B26 — Document the winsorisation consequence

> In `F:\Code\African Stability Index`, 672 normalised cells sit at exactly 0 and
> 380 at exactly 100, concentrated in `co2_pc`, `freshwater_withdraw` and
> `femicide`. Within those indicators the pinned countries are indistinguishable —
> a genuine loss of resolution the reader is not told about. Reproduce the counts
> from `data/panel/scores.csv`, then write the consequence into the Methodology
> tab beside the existing winsorisation explanation, naming the three indicators.
> Done looks like: the counts are stated in the interface and reproducible from a
> one-line query.

### B27 — Report PCA dimensionality wherever PCA weights appear

> In `F:\Code\African Stability Index`, the PCA weighting reports loadings but
> never dimensionality. The eigenvalues at 2023 are 4.339, 1.244, 0.572, … so
> **two** components clear Kaiser and PC1 explains only 62% of variance — yet the
> method presents itself as a single-factor weighting. Separately, the
> `loadings < 0 → 0` rule in `asi/pipeline/score.py` is not a numerical repair: it
> is the substantive claim "environment is not part of stability", made by an
> algorithm rather than an author. Reproduce the eigenvalues, then decide with the
> maintainer whether to report PC1 variance explained alongside every PCA figure,
> and whether the zeroing rule stays, becomes a documented editorial choice, or is
> replaced. Done looks like: the interface never shows a PCA rank without its
> variance-explained figure, and the zeroing rule is either justified in prose or
> changed.

### B28 — Document the goalpost revision policy

> In `F:\Code\African Stability Index`, the `clamped` provenance flag has never
> fired and cannot, because the bounds in `registry/goalposts.yaml` were derived
> from this same panel. It can only fire in a future edition, where a country
> setting a new extreme becomes indistinguishable from the previous record-holder
> at 0 or 100. Confirm that by checking `data/panel/observations.csv` for any
> `clamped` row. Then decide and write down: when bounds get re-frozen, what
> triggers it, and how the resulting discontinuity in the back-series is
> changelogged for a reader comparing editions. Done looks like: a stated policy in
> `methodology/` and a note beside the `note:` field already in `goalposts.yaml`.

### B29 — Rewrite `METHODOLOGY_REVIEW.md` against the code that exists

> In `F:\Code\African Stability Index`, `methodology/METHODOLOGY_REVIEW.md` dates
> from 2026-07-14 and reviews a pipeline of five numbered stages that no longer
> exists (`02_clean.py`, `04_score.py`, `05_robustness.py`). Several of its
> findings have since been fixed — GPI distance-from-parity, the
> `firm_foreign_owned` replacement, fixed goalposts, cross-pillar redundancy — and
> its §D roadmap is superseded by `methodology/BACKLOG.md`. Rewrite it against the
> current three-stage pipeline: keep the OECD 10-step scorecard structure, re-score
> each step against what the code does now, delete every finding this backlog
> records as done, and replace §D with a pointer to BACKLOG.md. Run B14 first so
> the file-reference checker catches anything missed. Done looks like: every path
> and stage name in the file exists, and no finding in it contradicts a `D`-id in
> BACKLOG.md.

### B30 — Surface the Monte Carlo intervals in the interface

> In `F:\Code\African Stability Index`, once B20 has written median rank and a 95%
> rank interval per country-year into `data/panel/composites.csv`, render them.
> The index cannot resolve 54 distinct ranks — a prior run gave a median interval
> of 22 places and only 29.4% of pairs separable — so a point rank in the interface
> asserts precision the data does not carry. Implement whichever presentation B20
> proposed (bands, interval bars, or rank-with-range), update the country page, the
> ranking table and the map legend consistently, and add view tests asserting the
> interval rendered matches the CSV. Done looks like: no view displays a bare point
> rank without its interval.

### B31 — Full-sample external validation against IIAG 2024 and FSI 2025

> In `F:\Code\African Stability Index`, `verify/advisory.py:141-152` checks only
> whether the IIAG 2023 top-5 and bottom-5 appear in our top-10 and bottom-10 —
> two hardcoded ISO3 sets, not a correlation. Replace it with a full 54-country
> Spearman of the equal-weighted and geometric composites against IIAG 2024
> overall, FSI 2025, and WGI Political Stability directly. Add a divergence table
> listing every country ranked more than 10 places apart from a peer index, with a
> written interpretation — divergence is expected, since ASI measures more than
> governance, but each case must be explainable. Store the external scores in
> `registry/` with their source and retrieval date rather than inline in the code.
> Done looks like: `--layer advisory` prints three Spearmans and a divergence table.

### B32 — Ship the four transparency disclosures in the dashboard

> In `F:\Code\African Stability Index`, four disclosures are computed by
> `verify/advisory.py` or derivable from `data/panel/` but never reach a reader.
> Add to the Methodology tab and the data-quality panel: (1) the effective-weights
> table — cross-listed WGI indicators carry 1.68–1.90× a median indicator while
> Pillar C members carry 0.57×, so equal-across-pillars is not
> equal-across-indicators; (2) the WGI-reliance figure — 6 of 32 indicators supply
> ~28.9% of composite weight, Pillar A 100%, E 50%, G 40%; (3) per-country median
> data year and oldest observation, since education data is effectively 2017;
> (4) fill provenance in the indicator drill-down, distinguishing stage-1 lookback
> from stage-2 regional fill. Reproduce each number from the panel before
> rendering it. Done looks like: all four visible in the interface and asserted by
> a view test. This is disclosure only — it changes no score. The methodology
> decision behind (1) and (2) is B18.

### B33 — Audit REC membership and decide whether it varies by year

> In `F:\Code\African Stability Index`, `asi/core/countries.py` carries all 8
> AU-recognised communities with counts ECOWAS 12, COMESA 21, CEN-SAD 25, SADC 16,
> ECCAS 10, EAC 8, IGAD 6, UMA 5. Check each against a current source: ECOWAS at 12
> implies the 2025 Sahel withdrawals are reflected, and EAC should include Somalia
> and DRC. One known discrepancy to resolve first, logged in `narrative/LEDGER.md`
> during the SEN run (2026-08-11): external sources say Senegal left CEN-SAD in
> 2013 by not signing the revised treaty, while the registry lists it as current —
> the narrative record matched the registry per established practice, so both will
> need updating together if the registry is wrong. Second question, a decision:
> membership is time-invariant but the slider spans 2000–2024 and membership
> changed inside that window. Either model membership by year or relabel the
> control "current membership". Done looks like: eight counts confirmed against
> cited sources, the SEN case resolved in registry and record together, and the
> time-variance question answered one way or the other.

### B34 — Decide what 2001 and 2024 look like

> In `F:\Code\African Stability Index`, two years display badly for opposite
> reasons. 2001 is 37/54 unreliable because WGI has no 2001 observation, so
> Pillar A is carried forward and the composite degrades — honest, but a visible
> notch in the time slider. 2024 is 54/54 unreliable because World Bank series
> report with a lag, which is why the dashboard opens on 2023. Reproduce both from
> `data/panel/pillar_scores.csv`. Then decide, per year: leave it, suppress it,
> or annotate it in the UI — and confirm 2023 as the landing year. Do not
> interpolate WGI 2001; carry-forward with a provenance flag is the correct
> handling and all three reviewers said so. Done looks like: a decision recorded
> and the slider behaving accordingly.

### B35 — Give each country an explicit `panel_start`

> In `F:\Code\African Stability Index`, South Sudan's pre-2011 country-years come
> out `unreliable` and unranked, which produces the right display behaviour by
> accident: coverage happens to be low, not because the state did not exist.
> Eritrea before 1993 is the same case. Add an explicit optional `panel_start` per
> country in the registry, exclude those years from ranking and aggregation
> explicitly, and have the interface state the reason ("South Sudan became
> independent in 2011") rather than showing a grey box that a reader will read as
> missing data. Done looks like: pre-independence years carry a stated reason, and
> a test asserts SSD has no rank before 2011 for that reason rather than by
> coverage.

### B36 — Decide the carry-forward policy for the five never-measured indicators

> In `F:\Code\African Stability Index`, five indicators carry 0% observed data at
> the 2023 reference year — `freshwater_withdraw`, `secondary_gpi`,
> `primary_enroll`, `social_protection_labour_pop`, `secondary_enroll`. Every value
> shown is carried forward or estimated from regional peers, yet they contribute to
> every published score. Confirm the five from `data/panel/observations.csv` and
> add each one's median actual observation year (`METHODOLOGY_REVIEW.md` C5 puts
> enrolment and social protection around 2017). Then decide: accept carry-forward
> with the staleness disclosed per indicator, cap the lookback at N years and let
> the cells go absent beyond it, or demote the worst to descriptive. Quantify the
> composite and rank impact of each option. Done looks like: a decision per
> indicator and, if anything is capped, the rank delta reported.

### B37 — Confirm the score-compression interpretation under fixed goalposts

> In `F:\Code\African Stability Index`, freezing goalposts across 24 years raised
> bottom-end scores — Somalia reads 34.3 at 2023 against 28.2 under the old
> sample-relative scoring — because present-day values sit less extreme against a
> historical range. This is expected and correct, but it changes how the index
> reads: the floor is no longer "worst in the sample". Reproduce the SOM figure,
> then confirm the interpretation is acceptable for publication and, if so, make
> sure the Methodology tab says plainly that 0 and 100 are historical bounds, not
> present-day extremes. Done looks like: a recorded confirmation and one sentence
> in the interface.

### B38 — Confirm the aggregation window for each indicator

> In `F:\Code\African Stability Index`, only 2 of 33 indicators use a rolling mean
> (`gdp_growth_3yr_avg`, `inflation_5yr_avg`); the rest use `most_recent`. In a
> panel context that is a per-indicator judgement, not a default — a volatile
> annual series read at a single year can move a pillar on noise. List the 33 with
> their aggregation setting and their year-on-year volatility from
> `data/panel/observations.csv`, then confirm `most_recent` for each or nominate
> the ones that should smooth. Done looks like: a recorded decision per indicator;
> if any change, re-freeze goalposts and report the rank delta.

### B39 — Pull the AUDIT limb forward for a sample

> In `F:\Code\African Stability Index`, the rotation policy in `narrative/state.yaml`
> is create → expand → expand → AUDIT, and 0 of 54 records have passed iteration 1.
> That puts 162 research runs between today and the first confirmed citation, so
> the anti-fabrication control at the centre of the design has never executed end
> to end. The first citation-support audit (2026-08-16) sampled the check manually
> and found the failure was structural rather than per-record, which is evidence
> the limb works — but it was not the AUDIT run. Confirm the rotation state from
> `state.yaml`, then decide with the maintainer whether to run a real AUDIT pass on
> a sample of 3–5 records now, out of rotation, rather than waiting. If yes, run it
> per `narrative/prompts/RESEARCH.md` and record what the first genuine audit found.
> Done looks like: at least three records at iteration 4 with `verified: true`
> flags that were earned, or a recorded decision to keep waiting and why.

### B40 — Version the narrative schema and build a migration path

> Add `meta.schema_version` to `blank_record()` and all 54 records, make `validate()`
> version-aware (old versions warn, new error), and write `scripts/migrate_narrative.py`
> with `--dry-run` for bulk mechanical migrations. Then discharge the two mechanical
> queued proposals in the same commit: add the missing `check_refs` call for
> `historical.colonial_legacy_citations` (which `verify/narrative.py:365` already
> reads), and add `SUSPENDED` to `RECStatus` for Madagascar's 2009-2013 case.

*Verified 2026-08-16: `asi/narrative/schema.py` has no `colonial_legacy_citations`
check and `RECStatus` (line 89) still has only `CURRENT` and `WITHDRAWN`. Both
proposals are genuinely unapplied. The third proposal in that list — the pillar
citation requirement — was applied today; see D05.*

### B41 — Key every path and singleton on the region profile

> Enumerate every change needed to add a second region, then propose — do not yet
> implement — a layout keyed on `profile.key` (`data/{key}/panel`,
> `narrative/{key}/countries`, `registry/{key}/goalposts.yaml`), moving `COUNTRIES`
> and the community vocabulary into `RegionProfile` and replacing the REC enum with
> profile data. Validate by sketching a two-country throwaway profile and running
> the pipeline end to end.

*Hard blockers recorded by the review: `COUNTRIES` is a module dict outside the
profile; `asi/narrative/schema.py:76` hardcodes the eight AU RECs as an enum and
validates against `COUNTRIES`; twelve unkeyed path constants across `asi/`,
`verify/`, `scripts/` and the root stages; `ACTIVE_PROFILE`/`PANEL`/`NARRATIVE`/`app`
are process-wide singletons. `verify/advisory.py:29-30` hardcodes Africa-only IIAG
benchmark sets — B03 flags it here rather than fixing it there. Do this before a
second region exists, not during it.*

### B42 — Split the narrative journal from the work queue

> In `F:\Code\African Stability Index`, `narrative/state.yaml` is a 2,988-line work
> queue of which `meta_notes` is 122 KB (64%) of pure journal, duplicated by hand
> into a 3,078-line `narrative/LEDGER.md`. Every research run loads, holds and
> rewrites the whole file; at 4 iterations × 54 records that is ~1.5 MB of prose in
> one YAML. Confirm the sizes, then decide where the journal lives — append-only
> per-run files under `narrative/journal/`, LEDGER.md as the single home with
> `meta_notes` removed, or a database — and migrate. The queue keys (`rotation`,
> `models`, `countries`, `backlog`, `pending_format_proposals`) stay in
> `state.yaml`. Done looks like: `state.yaml` under 500 lines, no journal content
> stored twice, and `narrative_check.py` plus `verify/narrative.py` both still
> green.

### B43 — Surface `robustness.json` in the Methodology tab

> In `F:\Code\African Stability Index`, `data/panel/robustness.json` is a finished
> sensitivity analysis — adversarial weights, measured-only, islands-excluded,
> per-country rank spread across methods — that no reader ever sees, and it
> directly answers the question the Methodology tab exists to answer. Render it:
> the worst-case Spearman, the per-country rank-spread table, and what each
> scenario varied. Run B09 first so the numbers being surfaced come from a sampler
> that actually explores the weight space. Done looks like: the tab shows the
> analysis and a view test asserts the rendered figures match the JSON.

### B44 — Drop `dash_bootstrap_components`

> In `F:\Code\African Stability Index`, `dash_bootstrap_components` is imported
> solely for `dbc.themes.FLATLY` at `asi/dashboard/app.py:1079` — one theme URL
> string. No `dbc` component is used anywhere (confirm with a grep for `dbc.`).
> The package ships ~255 KB on every page load. Replace the import with the theme
> stylesheet URL directly, remove the dependency from `requirements.txt`, and
> confirm the interface renders unchanged. Note B53 vendors that stylesheet
> locally, so leave the URL somewhere easy to swap. Done looks like: no `dbc`
> import, the dependency gone, and the 302+ test suite green.

### B45 — Add URL routing

> In `F:\Code\African Stability Index`, every view serves from `/` — the tab,
> country, pillar and year all live in callback state — so "Kenya, Health, 2010"
> cannot be bookmarked, cited or shared. For an index meant to be referenced by
> other people's work, that is the difference between a tool and a demo. Add
> `dcc.Location` routing with readable paths (`/country/KEN/health/2010`), make
> every view render from the URL rather than from component state, and keep the
> existing controls in sync with it. Add tests that a deep link renders the right
> view and that changing a control updates the URL. Done looks like: any view a
> reader can reach has an address they can paste into a citation.

### B46 — Accessibility and legibility

> In `F:\Code\African Stability Index`, measure first with an audit of
> `asi/dashboard/app.py` and `assets/asi.css`: 13 text styles fail WCAG AA, worst
> `#bbb` at 9px (1.82:1) and `#95a5a6` (2.43:1) — and those are the *caveat*
> styles, so the honesty machinery is rendered as the faintest, smallest text on
> the page. Only 7 elements on the page are focusable; the tabs and the map all set
> `tabIndex: -1`, so a keyboard user cannot change tab or open a country. `lang` is
> unset, heading order jumps H1→H4, and the map renders 140×500px at 375px wide.
> Reproduce each, then fix: a type scale that clears AA at every size (needs a
> decision on the scale), focusable tabs and map points with visible focus rings,
> `lang="en"`, corrected heading order, and a responsive map. Done looks like: no
> style below 4.5:1, keyboard-only navigation reaches every view, and the map is
> legible at 375px. This is a complaint about the typography of the honesty
> design, not its substance — do not remove caveats to fix contrast.

### B47 — Decompose `app.py`

> In `F:\Code\African Stability Index`, `asi/dashboard/app.py` is 1,185 lines
> holding theme constants, components, figures, all views and all callbacks. Split
> it into `theme.py`, `components.py`, `figures.py`, `views/` and `callbacks.py`,
> and move `view_methodology`'s ~140 lines of English prose into Markdown files
> the module reads. B01 cleared the way for this: `verify/contract.py` used
> `UI_DIR.glob("*.py")` rather than `rglob`, so moving views into a subdirectory
> would have silently disarmed all three contract checks. It recurses now, and
> `tests/test_verify_contract.py` holds it to that. Done looks like: no module
> over ~300 lines, the contract checks still see every file, and the full test
> suite green with no view behaviour changed.

### B48 — Work the 54 per-country EXPAND queues

> In `F:\Code\African Stability Index`, all 54 records in `narrative/countries/`
> carry a populated `meta.next_action`, each an EXPAND brief of 2–4 numbered
> research follow-ups written by the CREATE run that produced the record. They are
> per-country research work, not defects. Examples: BWA — find a dedicated source
> for the female intentional-homicide rate under Pillar E, which scores 0.0 and the
> record could not explain; AGO — follow the MPLA succession decision and whether
> the Cabinda/FLEC conflict escalated after February 2026; BEN — follow whether the
> December 2025 coup plotters face trial. Work these one country per session per
> `narrative/prompts/RESEARCH.md`, taking the country the rotation in
> `narrative/state.yaml` selects rather than choosing freely. The detail lives in
> each record's own `meta.next_action` and in that country's `LEDGER.md` entry —
> do not copy it here. Done, per country, looks like: the record at iteration 2
> with its next_action rewritten for the following pass.

*Roughly 1.5h per country, 54 of them. This is the long tail of the corpus and
should never block a methodology or code item.*

### B49 — Cross-record consistency sweep of the paired threads

> In `F:\Code\African Stability Index`, the corpus has accumulated cross-referenced
> country pairs where the same event is told from two sides, and `narrative/LEDGER.md`
> flags each as needing to stay consistent through any future EXPAND or AUDIT pass.
> The threads recorded so far: LBR/SLE (Taylor, RUF, the Special Court), EGY/ETH
> (GERD), TCD/SDN (refugee outflow), SDN/SSD (oil pipeline routing), MLI/BFA/NER
> (the January 2025 ECOWAS exit and resource nationalisation), MOZ/ZWE, MOZ/ZAF,
> GNQ/GMB (Jammeh), and ZAF/BWA/LSO (Operation Boleas, 1998 — the LEDGER notes ZAF
> and BWA may not document it from their own side at all). Sweep all of them in one
> pass: for each thread, read the records together and confirm dates, names,
> casualty figures and framing agree. Two standing rules from the same notes, apply
> them here: any superlative claim ("worst", "most severe", "lowest") must be
> checked against the actual prior record-holder's figures rather than asserted
> from memory; and any record written close to an election must have the actual
> result recorded once known. Done looks like: every thread confirmed or reconciled,
> and a LEDGER entry recording the sweep.

### B50 — Audit `context/colonial_history.yaml`

> In `F:\Code\African Stability Index`, `context/colonial_history.yaml` is 1,188
> lines read by `asi/dashboard/app.py:87` and rendered to readers, and it has never
> been audited — it predates the narrative corpus and its citation discipline.
> `asi/dashboard/narrative_ui.py:154` labels the record's colonial-legacy block as
> "expands context/colonial_history.yaml", so the two are shown side by side and
> can contradict each other. Check each country entry against the corresponding
> record's `historical.colonial_legacy` for factual conflicts, then spot-check
> dates and names against sources. Done looks like: contradictions resolved in
> favour of the sourced version, and a decision on whether the file keeps its own
> life or is folded into the corpus.

### B51 — Read the first nine records for negativity skew

> In `F:\Code\African Stability Index`, the first nine records written (the
> `first_pass: true` set in `narrative/state.yaml` — MUS, GHA, DZA, COD, SOM and
> the rest of that run) were produced before the framing-balance discipline had
> settled, and the balance validator only counts sentiment labels on recent items,
> not the tone of the pillar prose. Read all nine end to end as a human and judge:
> does the prose lean negative relative to what the indicators say? Compare against
> a later record written under the settled discipline. Done looks like: a written
> judgement per record and, where skew is found, a next_action set on that record
> rather than an edit made in place.

### B52 — Panel integrity: manifest and fail-closed loading

> In `F:\Code\African Stability Index`, nothing detects a stale or partial
> `data/panel`. Reproduce it: truncate `composites.csv` to 20 countries and load
> the dashboard — it renders a 20-country continental average while the header
> still claims 54, and `year_coverage_note()` helpfully explains the gap to the
> reader as a World Bank publication lag. Then write a `run_id`, per-file row
> counts and a SHA-256 per file into `data/panel/bundle.json` at the end of
> `02_panel.py`, and have `load()` check them. Needs a decision: fail closed and
> refuse to boot, or boot with a prominent banner. Both reviewers who found this
> ranked it above every other deploy item. Done looks like: a truncated panel is
> detected before a single number is rendered.

### B53 — Pre-deploy bundle: pin, CI, vendor the CDN, `--preload`

> In `F:\Code\African Stability Index`, four cheap deploy prerequisites, one
> session, immediately before the first public deploy and not before. (1) Pin every
> dependency in `requirements.txt` and `requirements-pipeline.txt` to exact
> versions captured from a green environment — both files are currently bare
> package names with no lockfile. (2) Add a GitHub Actions workflow running
> `pytest -q` and `python -m verify.run --gate-only` on push. (3) Vendor the
> Bootstrap stylesheet into `assets/` so nothing external loads, then add `nosniff`,
> `X-Frame-Options` and a CSP — trivial once the CDN is gone, and B44 may already
> have moved that URL. (4) Add `--preload` to the `Procfile`; two gunicorn workers
> each load a 24 MB dataframe independently, which is the likeliest reason a first
> deploy fails to boot. Run B52 first so CI has something real to gate on. Done
> looks like: a green CI run, no external requests from the page, and a successful
> local `gunicorn app:server --preload`.

### B54 — Quick wins

Under 15 minutes each; do them together whenever convenient.

1. Remove the applied pillar-citation proposal (the first entry) from
   `pending_format_proposals` in `narrative/state.yaml` — it was implemented today
   as the reserved `panel` citation id (D05) but still reads "not applied".
2. Add a one-line pointer to `methodology/BACKLOG.md` at the top of
   `ITERATION_PLAN.md`, `MANUAL_REVIEW.md` and `ROADMAP.md`, so nobody works from
   a superseded queue.
3. Update the stale `*Last updated: 2026-08-08 (Phase B)*` line in
   `MANUAL_REVIEW.md`, whose checkbox states this file has now replaced.

---

## Duplicates resolved

19 collapses. Each row is the same underlying issue appearing under different
names in two or more sources.

| Issue | Appeared in | Survives as |
|---|---|---|
| Goalposts anchored on imputed values | MANUAL_REVIEW 1 · ITERATION_PLAN 2.5 (U1, which itself cites MANUAL_REVIEW 1) | **B19** |
| Pillar F is incoherent / `co2_pc` inverts wealth | ITERATION_PLAN 2.3 (D3) · ROADMAP Phase 2 · METHODOLOGY_REVIEW C2 · MANUAL_REVIEW 3 (co2_pc as priority polarity case) · MANUAL_REVIEW 9 (PCA 0.000 vs entropy highest) | **B17** |
| `nonrenew_elec` ↔ `elec_access_tot` contradiction; `agri_land` polarity | ROADMAP Phase 2 · MANUAL_REVIEW 3 · METHODOLOGY_REVIEW C2 | **B17** (folded — both are Pillar F frame decisions) |
| Rank instability across weighting methods | MANUAL_REVIEW 9a · ITERATION_PLAN 2.2 (D2) · ROADMAP Phase 3b | **B20** (the *numbers* in 9a were separately wrong; fixed today, see D01) |
| Ad-hoc confidence band `2.0 + pct_filled × 26.7` | ROADMAP Phase 3c · METHODOLOGY_REVIEW C10 | **B20** — the band no longer exists in the code; only its replacement remains open |
| Joint Monte Carlo uncertainty analysis | ROADMAP Phase 3b · METHODOLOGY_REVIEW A7 + D-Phase3 · ITERATION_PLAN 2.2 · references.md:317 | **B20** |
| WGI concentration at ~28.9% of weight | MANUAL_REVIEW T3 (twice: "Cross-listing effective weights" and "WGI concentration") · METHODOLOGY_REVIEW C6 · ITERATION_PLAN 2.4 (D4) | **B18** for the methodology decision, **B32** for the disclosure |
| Cronbach's α on raw mixed-polarity values | METHODOLOGY_REVIEW A4 + C9 · ROADMAP Phase 3a · ITERATION_PLAN 3.2 | **B24** |
| Log-transform flags never derived from the stated rule | MANUAL_REVIEW 4 · ROADMAP Phase 1d · METHODOLOGY_REVIEW C8 + A5 | **B22** |
| Staleness hidden by `most_recent` / never-measured indicators | MANUAL_REVIEW 11 · METHODOLOGY_REVIEW C5 · ROADMAP Phase 4a | **B36**, with the median-data-year display in **B32** |
| Benefit-of-the-Doubt documented but nonexistent | ITERATION_PLAN 1.3 (D8) · ITERATION_PLAN 0.2 (ASI-04, reports on it) · ITERATION_PLAN 5.x docstring claims · METHODOLOGY_REVIEW B | **B11** (B02 reported it in `d6a316d`; B11 decides and removes) |
| Documentation describes a retired architecture | ITERATION_PLAN 1.4 (ASI-16) · METHODOLOGY_REVIEW B · references.md:296-320 (cites three nonexistent stage files) | **B14**, with the full METHODOLOGY_REVIEW rewrite as **B29** |
| External validation against peer indices | ROADMAP Phase 5 · METHODOLOGY_REVIEW A9 · `verify/advisory.py:29` hardcoded IIAG sets (flagged by ITERATION_PLAN 0.4) | **B31** |
| Cross-pillar redundancy check | ROADMAP Phase 3d · METHODOLOGY_REVIEW C7 | **D14** — already implemented at `verify/advisory.py:104` |
| Senegal / CEN-SAD membership discrepancy | LEDGER 2026-08-11 (SEN run) · MANUAL_REVIEW 2 (REC counts to confirm) | **B33** |
| Citations: URL resolves *and* supports the claim | MANUAL_REVIEW T4 item 1 · LEDGER meta-notes · ITERATION_PLAN 4.4 · `state.yaml` proposal 1 | Resolution split: URLs resolve = **D08**; the pillar-citation rule = **D05**; sample audit run = **D07**; the real AUDIT pass = **B39** |
| Per-pillar summaries vs actual indicator values | MANUAL_REVIEW T4 item 5 · LEDGER 2026-08-14 | **D09** — machine-gated, hedge-aware |
| Event flags checked against an independent source | MANUAL_REVIEW T4 item 3 · rotation AUDIT policy in `state.yaml` | **B39** |
| Fixed goalposts decision | ROADMAP Phase 6a · METHODOLOGY_REVIEW A5 + D-Phase6 | **D13** — decided and implemented; `registry/goalposts.yaml` v2 |

Superseded whole documents: `ROADMAP.md` Phases 1–6 and `METHODOLOGY_REVIEW.md` §D
are fully absorbed above. Nothing in either is unrepresented here.

---

## Completed — do not reopen

Every row below was verified against the code or the committed diff on 2026-08-16,
not against a checkbox.

### Today (2026-08-16)

| ID | What | Evidence |
|---|---|---|
| **D01** | Rank-spread aggregation bug: `min()`/`max()` ran across the appended `range` column, so four of eight published minima were the range. GIN 13→27, LSO 13→14, UGA 11→17, GAB 11→20. | `1079e64`; `03_robustness.py:179-186` now aggregates over `methods` only; `data/panel/robustness.json` regenerated; `MANUAL_REVIEW` item 9a corrected in the same commit |
| **D02** | Citation URL scheme allowlist — citation, `news_url`, `wikipedia_url` and event URLs must start with `http://` or `https://`, closing a `javascript:` href path through React. | `ab27fe6`; `URL_SCHEMES` and `_check_url()` at `asi/narrative/schema.py:181-198`, called at four sites |
| **D03** | Request body cap: Flask had no `MAX_CONTENT_LENGTH`, so a 200 MB POST to `/_dash-update-component` was buffered whole. Capped at 1 MB. | `ab27fe6`; `asi/dashboard/app.py:1085` |
| **D04** | Debugger fencing: `main()` bound `0.0.0.0` while reading `DEBUG` from the environment. Now binds loopback by default, takes an explicit `HOST`, and refuses to start with `DEBUG` set on a non-loopback host. | `ab27fe6`; `asi/dashboard/app.py:1184-1200` |
| **D05** | Reserved `panel` citation id — a pillar summary that is pure index output may cite the index itself, valid only inside pillars and only for the measured year. 71 filler citations migrated; general-history-only pillar sourcing fell from 21% to 2%. Closes the first `pending_format_proposals` entry. | `836cfbf`; `PANEL_CITATION` at `asi/narrative/schema.py:120`, enforced in `schema.py` and restated in `verify/narrative.py`, documented in `narrative/BLUEPRINT.md` |
| **D06** | 746 unearned `verified: true` flags reset. `verified` means an AUDIT run opened the source; no record has passed iteration 1, so none had earned it. | `ea52845`; zero `verified: true` remain across all 54 files in `narrative/countries/` |
| **D07** | First citation-support audit — stratified sample of non-Wikipedia citations behind figure-bearing claims. Found the failure is structural (a schema rule), not 76 separate lapses. Reported as an advisory metric, not a gate. | `809b524`; `verify/narrative.py` |
| **D08** | Contract section 2 could not catch most of what it describes. `_ui_files()` used `glob` not `rglob`, so a `views/` package — the next scheduled refactor — would have switched the layer off silently. 2.1's regex missed five of eight probe strings including the live `54 of 55 AU member states`; 2.2 missed four of five; 2.3 grepped substrings and flagged its own docstring. | `7ba8cb7`; `verify/contract.py` sections 2.1–2.3 rewritten, `tests/test_verify_contract.py` (31 fixtures, discriminating against the old logic), live offender at `asi/dashboard/app.py:1019` derived from `EXCLUDED_AU_MEMBERS` |
| **D09** | A quarter of published composites were verified by nothing — `check_composites` looped over equal/pca/entropy while `composites.csv` carries 5,400 rows across four methods. A +40 corruption on a geometric row passed; the same on an equal row failed. Also: no test had ever imported `asi.pipeline.score` or `asi.pipeline.goalposts`. | `d6a316d`; `check_geometric_composite` in `verify/panel.py` re-derives by product-and-root (pipeline uses exp-mean-log), 1,350 rows reconcile; `tests/test_score.py` + `tests/test_goalposts.py` (37 tests); four mutations introduced and all four caught |
| **D10** | `verify/advisory.py` imported `asi.dashboard.data` — the loader the interface uses — breaking the rule `README` and `verify/__init__.py` both state. A filter added to that loader would have narrowed what the diagnostics saw without changing a line of `advisory.py`. The rule was documentation only. | `f3ef6f9`; `asi/dashboard/data.py` → `asi/results.py` with eight importers repointed, `verify/advisory.py` reads `data/panel/` directly (frames verified identical), `tests/test_verify_independence.py` AST-scans `verify/*.py` and permits only `asi.core.constants`; contract 2.3 loses its `data.py` filename exemption; three mutations introduced and all three caught |
| **D12** | `verify/panel.py` re-derived 27 of 32 scoring indicators. The five it skipped — `displaced_persons`, `gdp_growth_3yr_avg`, `inflation_5yr_avg`, `primary_gpi`, `secondary_gpi` — were 15.6% of cells and effectively all of the panel's arithmetic, while the README claimed re-derivation of the whole panel. Found a live bug: `apply_derived` pivots to reach population as a denominator, and `pivot_table` omits an all-NaN column, so a population series that failed to pull for the whole panel would skip the conversion in silence and leave raw head-counts in a per-thousand column. | `40e362a`; checks 1.4 (`.rolling()`, 2,569 cells), 1.5 (`min(x, 2-x)`, 2,346 cells) and 1.6 (IDP/population, 747 cells) in `verify/panel.py`; `dropna=False` fix in `asi/pipeline/panel.py` (published panel unaffected — population is non-null in all 1,350 cells); `tests/test_panel_derived.py` (28 tests); coverage restated as 38,276 of 43,200 cells (88.6%), remainder regional-mean by construction |
| **D13** | 118 test cases asserted only `view(...) is not None`. A Dash view returns a component tree or raises — it never returns None — so they could only fail on an exception, and 54 country-view tests passed while the page rendered a continental rank labelled "in scope". `test_registry.py` pinned counts (54 countries, 32 indicators), which is a second place to write a number rather than a check. | `1e7b9f7` + `82495ba`; view tests now read the rendered tree per pillar card and compare against `data/panel/*.csv`; the rank defect recorded as a strict xfail pointing at B13; count pins replaced by cross-source agreement with `bundle.json` and `COUNTRIES + EXCLUDED_AU_MEMBERS == 55`; `check_indicator_phrases` in `verify/narrative.py` holds all 17 prefixes to exactly one `display_name`; six mutations introduced, two survived the first attempt and were fixed, all six caught |
| **D14** | `02_panel.py` regenerated frozen goalposts whenever the file was missing, re-anchoring every historical score against the current panel and logging it as an ordinary step. The `FileNotFoundError` told the user to run `03_normalize.py`, retired. | `e5ae2dc`; implicit branch removed (AST-guarded by a test, since the explanatory comment quotes the old condition), message names `02_panel.py --freeze-goalposts`, `REFERENCE_YEAR_MIN_COVERAGE` replaces a bare `0.80` |
| **D15** | The adversarial-weights search sampled the plain simplex and rejected outside `[WEIGHT_MIN, WEIGHT_MAX]`: 23 of 1000 draws survived, so the published *robust* verdict rested on 23 evaluations of a 7-dimensional polytope — and its reported worst vector was a deterministic corner, so the random search contributed nothing. **The verdict changes to "moderately sensitive".** | `e5ae2dc`; shifted-simplex sampler (2,993 of 10,000 accepted, worst rho 0.880 at a genuinely interior vector), `N_RANDOM_WEIGHTS` 1000→10000, per-country quintile-stability statistic (median 93%, NGA 26%, LBY 27%); `MANUAL_REVIEW` 9a corrected |
| **D16** | `measured_only` filtered *pillar* reliability, and Pillar C has zero reliable countries at 2023 — so it deleted Pillar C for all 54 and let `weighted_composite` renormalise. `countries_no_longer_scoreable: 0` was an artifact of that renormalisation. | `e5ae2dc`; rebuilt at cell level from `observations.csv` on `provenance == 'observed'` (996 of 1,728 cells, rho 0.952, median shift 2), reported with the pillar thinness that makes the zero readable (median indicator share 75%, 61 of 377 pillar-years under half) |
| **D11** | Two narrative validators, already drifted in both directions. `scripts/narrative_check.py` had a duplicate-URL check the gate lacked; `verify/narrative.py` had quoted-value, name-drift, future-date and membership-span checks the script lacked. The tests covered the script — the copy that does not gate a release — and the gating copy had none. | `8704853`; `all_checks()` in `verify/narrative.py` is the single implementation, `scripts/narrative_check.py` reduced to a thin caller keeping only `--links` and the coverage report, script's duplicate-URL check moved in as `check_citation_linkage`; both routes assert an identical 40-finding set on the shipped corpus; three mutations introduced and all three caught |

*A regex bug found during D05 is worth remembering: a `\b` written through a heredoc
became a literal backspace byte, so the year check silently matched nothing and passed
everything. The tree was swept for stray control characters; none remain.*

### Earlier, verified still true

| ID | What | Evidence |
|---|---|---|
| **D08** | Corpus-wide link scan; the three genuinely dead citations fixed. Closes the "URL resolves" half of MANUAL_REVIEW T4 item 1. | `ee47432` (2026-08-14) |
| **D09** | Quoted indicator values gated, hedge-aware — judges hedge *direction* and refuses to read across a clause naming another indicator. Closes MANUAL_REVIEW T4 item 5. | `b8750d7` (2026-08-14); `check_quoted_values()` at `verify/narrative.py:156` |
| **D10** | Display precision: 2 decimals accepted 2026-08-08, with the tie consequence documented and reported as WARN by `verify/contract.py`. Closes MANUAL_REVIEW T3. | `MANUAL_REVIEW.md` T3 |
| **D11** | GPI distance-from-parity transform — `min(GPI, 2−GPI)`. Closes ROADMAP Phase 1a and METHODOLOGY_REVIEW C1. | `asi/pipeline/panel.py:147,191` |
| **D12** | `firm_foreign_owned` replaced by `domestic_credit_private`. Closes ROADMAP Phase 1b and METHODOLOGY_REVIEW C3. | `indicators_list/pillar_b.yaml:68` with the replacement rationale at `:84` |
| **D13** | Fixed goalposts frozen in the registry with a deliberate-regeneration note. Closes ROADMAP Phase 6a and METHODOLOGY_REVIEW A5(i). | `registry/goalposts.yaml` version 2, generated 2026-08-08 |
| **D14** | Cross-pillar redundancy check (|ρ| > 0.80 across pillars). Closes ROADMAP Phase 3d and METHODOLOGY_REVIEW C7. | `verify/advisory.py:104-122` |
| **D15** | The ad-hoc confidence band (`2.0 + pct_filled × 26.7`) no longer exists in the code — it survives only in the two documents that complain about it. Only its replacement (B20) is open. | No match for `26.7` anywhere under `asi/`, `verify/`, `scripts/` or the root stages |

---

*Sources swept: `methodology/ITERATION_PLAN.md`, `MANUAL_REVIEW.md`, `ROADMAP.md`,
`METHODOLOGY_REVIEW.md`, `references.md`, `narrative/state.yaml`, `narrative/LEDGER.md`,
`narrative/BLUEPRINT.md`, `narrative/prompts/RESEARCH.md`, all 54 `narrative/countries/*.yaml`,
`README.md`, and a `TODO`/`FIXME`/`XXX`/`HACK`/`not applied`/`for now`/`future` grep across
`asi/`, `verify/`, `scripts/` and the root `*.py` stages.*
