# Iteration plan

Built 2026-08-16 from three independent cold-start reviews (security, statistical
methodology, architecture/product). Each reviewer was told to assume nothing in
the project was correct, to make no edits, and to return findings with evidence.

**How to use this.** Every item below is sized to one working session and carries
a self-contained prompt. Hand a future session the prompt and nothing else — it
does not need this document or any memory of the reviews. Work stages in order;
within a stage, order is mostly free unless a dependency is stated.

**Standing decisions** (set by the maintainer, 2026-08-16):

1. Priority is **credibility → research rigour → public polish**.
2. **The index's meaning may change.** Scores and ranks are allowed to move; the
   current published numbers are edition 1 of a draft.
3. **No public deployment soon.** Security work is staged late; only cheap and
   permanent fixes were taken early.

---

## What the three reviews agreed on

Convergence across independent reviewers is the strongest signal here, because
none of them saw the others' findings.

| Finding | Flagged by |
|---|---|
| Benefit-of-the-Doubt is documented, labelled in the UI, and does not exist | methodology + architecture |
| Dependencies are entirely unpinned; no lockfile, no CI | security + architecture |
| A stale or partial `data/panel` ships wrong numbers with no gate | security + architecture |
| Documentation describes a retired architecture | methodology + architecture |
| The checking machinery is weaker than it reads | all three |

That last one is the theme of this plan. Two reviewers independently demonstrated
a check passing on the exact defect it exists to catch — the contract layer's
hardcoded-count rule, and `verify/panel.py`'s composite re-derivation. A third
found the same pattern in this session's own work (a regex containing a literal
backspace byte, silently matching nothing).

**Consequence for sequencing: Stage 0 is not optional and is not cosmetic.** Every
later stage edits code that these checks are supposed to protect. Fixing the
checks first is the difference between a refactor that is verified and one that
merely appears to be.

---

## Stage 0 — Make the safety net real

*Blocks Stages 2, 4 and 5. Roughly 35h across ~6 sessions. No decisions needed.*

Nothing in this stage changes a published number. It exists so that the stages
which do change numbers are actually checked.

### 0.1 — Make the contract checks fail on what they were written to catch
**6h · source: architecture ASI-01 · autonomous**

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

### 0.2 — Unit-test the scoring arithmetic; verify the geometric composite
**10h · source: architecture ASI-04 · autonomous, except the BoD question**

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

### 0.3 — Test and verify the five hardest indicator paths
**8h · source: architecture ASI-05 · autonomous**

> In `F:\Code\African Stability Index`, `verify/panel.py:88` excludes rolling-mean,
> transformed and derived indicators from re-derivation — 5 of 33
> (`displaced_persons`, `gdp_growth_3yr_avg`, `inflation_5yr_avg`, `primary_gpi`,
> `secondary_gpi`). Those are the only non-trivial logic in `panel.py`, so the
> README's "independent re-derivation of the whole panel" covers 85% of cells and
> 0% of the difficulty. Add unit tests for `asi.pipeline.panel.apply_derived` and
> `regional_fill` on small synthetic frames, covering IDP-present-but-population-
> absent (must become ABSENT with `source_year` cleared) and the
> `MIN_REGIONAL_SAMPLE` threshold. Extend `check_panel_values` to re-derive rolling
> means with `.rolling()` and the parity fold arithmetically. Correct the README
> claim to what is true.

### 0.4 — Enforce verification independence; rename the results layer
**5h · source: architecture ASI-13 · autonomous**

> In `F:\Code\African Stability Index`, `asi/dashboard/data.py` calls itself "the
> interface's only door to stored results" but is imported by `03_robustness.py:32`,
> `scripts/narrative_check.py:30` and `verify/advisory.py:26` — the last violating
> the rule stated in `README:63` and `verify/__init__.py` that verification never
> imports the code it checks. Move the module to `asi/results.py`, update its
> docstring and all importers, and replace `verify/advisory.py`'s use of it with
> direct pandas/json reads of `data/panel/`. Add `tests/test_verify_independence.py`
> that AST-scans `verify/*.py` and fails on any `asi.*` import other than
> `asi.core.constants`. Note `verify/advisory.py:29-30` also hardcodes Africa-only
> IIAG benchmark ISO3 sets; flag that for Stage 4 rather than fixing it here.

### 0.5 — Collapse the two divergent narrative validators into one
**6h · source: architecture ASI-12 · autonomous**

> In `F:\Code\African Stability Index`, `scripts/narrative_check.py` and
> `verify/narrative.py` independently implement the same checks and have already
> diverged: the script has a duplicate-URL check the gate lacks; the gate has
> quoted-value, name-drift, future-date and membership-span checks the script
> lacks. `tests/test_narrative_consistency.py:34` tests the script — the
> non-gating one — while the gating implementation has no tests. Make
> `verify/narrative.py` the single implementation, reduce `scripts/narrative_check.py`
> to a thin caller adding only the network `--links` pass and the coverage report,
> and repoint the tests at the gating code. Confirm both commands agree on the
> shipped corpus afterwards.

### 0.6 — Add content assertions to the view tests; drop the count pins
**8h · source: architecture ASI-18 · autonomous**

> In `F:\Code\African Stability Index`, 118 of 302 tests are parametrized
> `assert view(...) is not None`, which cannot fail unless an exception is raised
> (confirm with `pytest --collect-only -q`). Those 54 country-view tests all pass
> while `view_country` renders a false rank label. Add content assertions in
> `tests/test_dashboard_views.py`: the rank rendered on a country page equals
> `D.rankings()`'s `scope_rank` for the active grouping; a greyed pillar card
> renders "—" plus a stated reason; each tier badge matches `pillar_scores.csv`.
> Replace the hardcoded counts at `tests/test_registry.py:21,108,109` (54 countries,
> 32 indicators) with structural invariants that survive adding a country or an
> indicator. Add a check in `verify/narrative.py` that every prefix in
> `INDICATOR_PHRASES` (line 102) resolves to exactly one `display_name`, so a
> display-name edit cannot silently disable the quoted-value check.

---

## Stage 1 — Correct what is provably wrong

*~23h across ~6 sessions. No design decisions; these are errors, not choices.*

### 1.1 — Repair the robustness stage's sampler and verdict
**2h · source: methodology D6 · autonomous**

> In `F:\Code\African Stability Index`, `03_robustness.py:120-128` samples weights
> via `rng.dirichlet(np.ones(7))` and rejects vectors outside `[WEIGHT_MIN,
> WEIGHT_MAX]`; `data/panel/robustness.json` records that only 23 of 1000 draws
> were accepted, so the published "robust" verdict rests on ~30 evaluations of a
> 7-dimensional polytope. Replace the sampler with `w = 0.05 + 0.65 *
> rng.dirichlet(np.ones(7))` plus a `w.max() <= 0.25` check (~30% acceptance),
> raise `N_RANDOM_WEIGHTS` to 10000, and replace the single global verdict at
> line 130 with a per-country statistic: the share of admissible weightings that
> keep the country in its published quintile. The file currently reports
> `verdict: robust` alongside `max_rank_shift: 29`.

### 1.2 — Fix the `measured_only` diagnostic to test what it claims
**3h · source: methodology D7 · autonomous**

> In `F:\Code\African Stability Index`, the `measured_only` check at
> `03_robustness.py:148` filters pillar scores to `reliability == "reliable"` and
> claims to measure the effect of excluding estimated data. At the 2023 reference
> year that filter leaves Pillar C with zero surviving countries, so it actually
> deletes Pillar C for everyone and silently reweights the other six; its reported
> `countries_no_longer_scoreable: 0` is an artifact of the renormalisation in
> `asi/pipeline/score.py:136`. Rewrite it to work at cell level — rebuild
> composites from `provenance == "observed"` scores only, using
> `data/panel/observations.csv` — and report how many country-years fall below
> `MIN_PILLARS_FOR_COMPOSITE` and how far ranks move.

### 1.3 — Strike the phantom Benefit-of-the-Doubt limb
**2h · source: methodology D8 + architecture ASI-04/ASI-17 · needs a yes/no**

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

### 1.4 — Make documentation describe the code that exists
**4h · source: architecture ASI-16 + methodology D8 · autonomous**

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

### 1.5 — Stop the country page reporting a continental rank as "in scope"
**3h · source: architecture ASI-02 · needs a decision on intended behaviour**

> In `F:\Code\African Stability Index`, `asi/dashboard/app.py:1109` and `:1111`
> drop the Compare grouping when rendering country and pillar pages, so
> `app.py:525` renders the stored continental rank under the label "in scope".
> With Compare = ECOWAS, Ghana's country page shows "#7 · Rank · in scope" while
> its actual rank within ECOWAS is #2 of 12. Reproduce that, then decide with the
> maintainer whether the country page should follow the grouping or say
> "continental", implement it, and add a regression test. Root cause is
> architectural: `asi/dashboard/data.py:6` states the module never computes a rank,
> while `data.py:151` and `:215` both do, so two disagreeing ranks exist.

### 1.6 — Make corpus loading fault-tolerant and imports side-effect-free
**4h · source: architecture ASI-03 · autonomous**

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

### 1.7 — Stop `02_panel.py` silently re-anchoring frozen goalposts
**1h · source: architecture ASI-15 · autonomous**

> In `F:\Code\African Stability Index`, `asi/pipeline/goalposts.py:176` states it
> raises when the goalposts file is absent because "silently recomputing defeats
> the point" — but `02_panel.py:121` reads `if args.freeze_goalposts or not
> GOALPOSTS_FILE.exists():`, so a deleted or gitignored `registry/goalposts.yaml`
> silently re-anchors every historical score with no warning. Remove the implicit
> regeneration branch. Fix the error message at `goalposts.py:180`, which tells the
> user to run the retired `03_normalize.py`. Move the bare `0.80` reference-year
> coverage threshold at `02_panel.py:224` into `asi/core/constants.py` as a named
> constant.

### 1.8 — Delete the shadow registry and the dead weight
**3h · source: architecture ASI-11 + ASI-17 · one deletion needs confirmation**

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

---

## Stage 2 — The methodology decisions

*~45h. **Every item here changes published scores or ranks.** Decision 2 authorises
that in principle, but each option below needs an explicit choice. Do Stage 0.2
first — these edit the arithmetic that stage puts under test.*

Present these as costed options; do not pick unilaterally.

### 2.1 — Decide what an `unreliable` pillar does to the composite
**6h · source: methodology D1 · DECISION REQUIRED · highest substantive priority**

Pillar C is classified `unreliable` — the project's own label for "too inferred to
show" — for all 54 countries at 2023, is 82.4% imputed, and still contributes 1/7
of every published composite. `weighted_composite` never inspects the reliability
column. The UI greys it; the arithmetic uses it in full.

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

### 2.2 — Publish rank intervals instead of point ranks
**12h · source: methodology D2 · DECISION on presentation**

A joint Monte Carlo run during the review gave a **median 95% rank interval of 22
places out of 54**, with only **29.4% of country pairs separable**. The data
supports roughly five bands, not 54 ranks.

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

### 2.3 — Resolve what Pillar F measures
**3h to demote, 20-30h to rebuild · source: methodology D3 · DECISION REQUIRED**

Pillar F correlates **negatively with all six other pillars** (mean r = −0.415;
r = −0.732 with Health) and carries the only negative PC1 loading. `co2_pc`
correlates **−0.908 with GDP per capita** — an inverted wealth proxy. Burundi and
Malawi top the pillar; Seychelles and Libya bottom it. Under equal weights, being
poor and low-emitting raises the stability score.

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

### 2.4 — Collapse the WGI family and remove cross-listing
**4h mechanical, 15h+ to refill E and G · source: methodology D4 · DECISION REQUIRED**

All five cross-listed indicators are WGI, so cross-listing amplifies exactly one
source family to **28.9% of composite weight**. The six WGI dimensions have mean
pairwise r = 0.801 and a first eigenvalue of 5.03/6; Pillar A's Cronbach α is
0.958 — redundancy, not reliability. Removing shared indicators drops the A–E
correlation from **0.822 to 0.239**, so those pillars' apparent coherence is an
artifact of counting the same thing twice.

> In `F:\Code\African Stability Index`, prototype collapsing the six WGI dimensions
> into a single governance factor placed in Pillar A only, with no cross-listing
> (known result: Spearman 0.945 versus published, max shift 21 places). Report
> which indicators would need to be sourced to refill Pillars E and G, which the
> change substantially empties. Do not commit — present for a decision.

### 2.5 — Re-anchor goalposts that rest on imputed extremes
**6h · source: methodology U1 (already `MANUAL_REVIEW` item 1) · DECISION per indicator**

19 of 32 goalposts are anchored on imputed values; four indicators (`gini`,
`intent_homicide`, `learning_poverty`, `social_protection_labour_pop`) have **both**
bounds imputed. Bounds are frozen permanently, so an imputed extreme fixes the
scale for every country and year, forever. Where a theoretical bound exists (GPI
= 1.0 by construction; literacy 0–100), use it.

### 2.6 — State or replace the missing-data assumption
**2h for the sensitivity check, 10h for multiple imputation · source: methodology U3**

Regional-mean fill is *single* imputation, so variance is understated by
construction and filled countries within a region receive identical values.
More seriously, missingness here is unlikely to be MAR: the countries failing to
report homicide, Gini or learning poverty are disproportionately conflict-affected
and low-capacity, so filling them with a regional mean pulls them **toward** the
average and flatters exactly the states the index should discriminate. At minimum
run the sensitivity check: does a conflict state's rank rise when its missing
cells are filled?

---

## Stage 3 — Research rigour

*~15h. Depends on Stage 2 settling. This is what turns a data product into a
citable artifact.*

- **3.1** Surface the Monte Carlo intervals in the interface (6h) — depends on 2.2.
- **3.2** Add per-pillar Cronbach's α to `verify/advisory.py` (1h, autonomous).
  Measured at 2023: A 0.958, B 0.507, C 0.589, D 0.809, E 0.472, F 0.608, G 0.799.
  Three pillars fail the project's own 0.60 gate; A fails upward. All 32 indicators
  as one scale give α = 0.810 — the index is closer to unidimensional than seven
  pillars implies, and that is a finding worth publishing.
- **3.3** Publish a per-pillar imputation table (2h, autonomous). The panel is
  74.19% observed overall, but the reference year is 39.0% imputed and Pillar C is
  82.4%. Only a cell-level figure is currently documented.
- **3.4** Document the winsorisation consequence (1h, autonomous): 672 cells sit at
  exactly 0 and 380 at exactly 100, concentrated in `co2_pc`, `freshwater_withdraw`,
  `femicide` — within those indicators the pinned countries are indistinguishable.
- **3.5** Document the goalpost revision policy (2h, decision): `clamped` has never
  fired and cannot, since bounds derive from this panel. It can only fire in a
  future edition, where a country setting a new extreme becomes indistinguishable
  from the previous record-holder. State when bounds get re-frozen and how the
  discontinuity is changelogged.
- **3.6** Rewrite `methodology/METHODOLOGY_REVIEW.md` against the code that exists (4h).
- **3.7** Report PCA dimensionality wherever PCA weights appear (3h, decision):
  eigenvalues are 4.339, 1.244, 0.572, … so **two** components clear Kaiser and
  PC1 explains only 62%. The `loadings < 0 → 0` rule is not a numerical repair but
  the substantive claim "environment is not part of stability", made by an
  algorithm rather than an author.

---

## Stage 4 — Extensibility, before it gets more expensive

*~35h. **Do this before a second region exists, not during it.** Every indicator
and record added between now and then deepens the single-edition assumption.*

### 4.1 — Key every path and singleton on the region profile
**20-30h · source: architecture ASI-06 · DECISION on layout**

The `RegionProfile` seam is real in `asi/pipeline` and decorative everywhere else:
`display_name`, `community_label` and `key` are declared and never read. Hard
blockers: `COUNTRIES` is a module dict outside the profile; `asi/narrative/schema.py:76`
hardcodes the eight AU RECs as an enum and validates against `COUNTRIES`; twelve
unkeyed path constants across `asi/`, `verify/`, `scripts/` and the root stages;
`ACTIVE_PROFILE`/`PANEL`/`NARRATIVE`/`app` are process-wide singletons.

> Enumerate every change needed to add a second region, then propose — do not yet
> implement — a layout keyed on `profile.key` (`data/{key}/panel`,
> `narrative/{key}/countries`, `registry/{key}/goalposts.yaml`), moving `COUNTRIES`
> and the community vocabulary into `RegionProfile` and replacing the REC enum with
> profile data. Validate by sketching a two-country throwaway profile and running
> the pipeline end to end.

### 4.2 — Version the narrative schema and build a migration path
**12h · source: architecture ASI-10 · DECISION on the citation rule**

No record carries a schema version, `validate()` is unconditional, and three schema
proposals sit in `state.yaml` marked "not applied" with no mechanism to apply them.
Applying any one fails 54 records at once with 54 manual runs as the only remedy —
so the schema cannot evolve, so proposals accumulate.

> Add `meta.schema_version` to `blank_record()` and all 54 records, make `validate()`
> version-aware (old versions warn, new error), and write `scripts/migrate_narrative.py`
> with `--dry-run` for bulk mechanical migrations. Then discharge the two mechanical
> queued proposals in the same commit: add the missing `check_refs` call for
> `historical.colonial_legacy_citations` (which `verify/narrative.py:365` already
> reads), and add `SUSPENDED` to `RECStatus` for Madagascar's 2009-2013 case.

### 4.3 — Split the narrative journal from the work queue
**5h · source: architecture ASI-19 · DECISION on where the journal lives**

`state.yaml` is 2,988 lines of which `meta_notes` is 122 KB (64%), duplicated by
hand in a 3,078-line `LEDGER.md`. Every research run loads, holds and rewrites the
whole thing. At 4 iterations × 54 records that is ~1.5 MB of prose in one YAML.

### 4.4 — Pull the AUDIT limb forward for a sample
**decision · source: architecture ASI-10 + methodology**

The rotation's audit pass has never executed: 0 of 54 records have reached
iteration 4, so 162 research runs stand between today and the first confirmed
citation. The anti-fabrication control at the centre of the design is unproven
end to end. Decide whether to audit a sample of records now rather than waiting.

---

## Stage 5 — The interface

*~40h. Depends on 0.1 (the contract checks must see subdirectories before `app.py`
is split) and benefits from 2.2 landing first.*

- **5.1** Decompose `app.py` (1,185 lines) into `theme.py`, `components.py`,
  `figures.py`, `views/`, `callbacks.py`; move `view_methodology`'s 140 lines of
  English into Markdown (16h). **Requires 0.1 first** — splitting into a
  subdirectory currently disarms all three contract checks.
- **5.2** Accessibility and legibility (14h, decision on the type scale).
  Measured: **13 text styles fail WCAG AA**, worst `#bbb` at 9px (1.82:1) and
  `#95a5a6` (2.43:1) — and those are the *caveat* styles. The honesty machinery is
  rendered as the faintest, smallest text on the page, which works against the
  project's whole thesis. Also: only **7 focusable elements** on the page, tabs and
  the map all `tabIndex: -1`, so a keyboard user cannot change tab or open a
  country; `lang` unset; heading order jumps H1→H4; **the map renders 140×500px at
  375px wide**.
- **5.3** URL routing (6h, autonomous). Nothing is linkable — every view serves
  from `/`, so "Kenya, Health, 2010" cannot be bookmarked, cited or shared. For an
  index meant to be referenced, this is the difference between a tool and a demo.
- **5.4** Surface `data/panel/robustness.json` in the Methodology tab (2h,
  autonomous). It is a finished sensitivity analysis that no reader ever sees, and
  it directly answers the question that tab exists to answer.
- **5.5** Drop `dash_bootstrap_components` (1h, autonomous): 255 KB shipped on
  every page load for a single theme string; no components are used.

---

## Stage 6 — Pre-deployment checklist

*~6h, run once, immediately before the first public deploy. Not before.*

Security review found **no critical issues**: no secrets in git history, no
injection sinks, no path traversal, no XSS, error pages leak nothing, and
`rel="noopener noreferrer"` is on every external link. Already fixed early:
request-body cap, URL scheme allowlist, debugger fencing.

- **6.1** Pin every dependency to exact versions from a green environment (1h).
- **6.2** Panel integrity: write a `run_id`, per-file row counts and SHA-256 into
  `bundle.json`; have `load()` fail closed on mismatch (3h, decision on fail-closed
  vs banner). A truncated `composites.csv` currently renders a 20-country
  continental average while the header still claims 54 — and `year_coverage_note()`
  explains the gap to the reader as a World Bank publication lag.
- **6.3** Add CI (GitHub Actions) running `pytest -q` and `verify.run --gate-only` (1h).
- **6.4** Vendor the Bootstrap CDN stylesheet, then add `nosniff`, `X-Frame-Options`
  and a CSP (1.5h) — trivial once nothing external is loaded.
- **6.5** Add `--preload` to the Procfile (0.5h). Two workers each load a 24 MB
  dataframe independently; this is the likeliest reason a first deploy fails to boot.

---

## Out of band — do this whenever, it is not staged

**TLS verification is disabled on the data acquisition path.** `01_pull.py:26-38`
monkeypatches `requests` to force `verify=False` process-wide. That script produces
`data/baseline/01_raw_pull_BASELINE.xlsx`, which `verify/panel.py` re-derives the
entire published index from — so the trust root of the whole artifact was fetched
over TLS that authenticated nothing, and every downstream check would reconcile
perfectly against an altered baseline.

The stated justification (a TLS-intercepting proxy) is plausible; the remedy is
not. Such a proxy *has* a CA — trust that one specifically, via `REQUESTS_CA_BUNDLE`
pointing at a PEM exported with `certutil -store Root`. Then re-pull on a clean
network and compare the SHA-256 against the committed baseline, recording the digest
either way. **This needs the maintainer's own network knowledge, which is why it is
not scheduled.** It is the single most important thing for the project's integrity.

Related: `data/01_raw_pull.xlsx` and `data/baseline/01_raw_pull_BASELINE.xlsx` are
byte-identical with no manifest, so nothing distinguishes "unchanged" from "silently
overwritten".

---

## What all three reviewers said not to touch

Recorded so it is not churned in a later session.

- **Frozen goalposts and once-fitted PCA/entropy weights** — methodologically
  correct for a time series, and the reasoning is written where the next maintainer
  finds it. The single biggest methodological upgrade in the project's history.
- **Provenance tracking end to end** — every cell in 44,550 rows knows whether it
  was observed, carried forward or imputed. Most published indices cannot do this;
  it is what made all three reviews possible.
- **The reliability tier design** (`classify_reliability`, `composite_reliability`) —
  measuring coverage against full pillar membership rather than surviving indicators
  is exactly right and a trap most people fall into. Stage 2.1 is about connecting
  it, not correcting it.
- **`verify/narrative.py`** — called "the best code in the repository". Five injected
  defects, all caught with actionable messages.
- **`verify/panel.py`** — proven to catch tampering: 12.0 added to Kenya's composite
  and three altered Nigerian scores both failed it correctly.
- **The WGI 2001 biennial gap** — handled correctly. Carry-forward with a provenance
  flag is right; interpolating would fabricate a governance measurement. Annotate,
  do not interpolate, do not suppress.
- **`distance_from_parity`** and **derived-before-fill ordering** — both non-obvious
  and both correct.
- **The honesty design itself** — `year_coverage_note`, `rec_membership_caveat`,
  stated pillar silence, "cited rather than confirmed", the Western Sahara
  explanation. Stage 5.2 is a complaint about its typography, not its substance.
- **No auth** — the correct design for a public read-only dashboard. Do not add a login.
