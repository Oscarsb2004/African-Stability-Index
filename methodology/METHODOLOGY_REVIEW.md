# ASI Methodology Review

*Review date: 2026-09-06 · Reviewed against the panel pipeline (`01_pull.py`, `02_panel.py`,
`03_robustness.py`, `asi/`, `verify/`) at the 2023 reference year.*

*Supersedes the review of 2026-07-14, which graded the five-stage snapshot pipeline
(`02_clean` / `03_normalize` / `04_score` / `05_robustness` / `06_qualitative`). That pipeline
no longer exists. The previous review was stale in **both** directions: it penalised the index
for sample-dependent normalisation bounds that fixed goalposts have since removed, and credited
it with a Cronbach implementation, five scoring methods, and a "Robust / ρ = 0.9245" verdict,
none of which are true now.*

This review evaluates the **design** of the ASI against the OECD/JRC Handbook on Constructing
Composite Indicators (2008) and two peer indices (IIAG 2024, ND-GAIN). Four layers:
(A) OECD step-by-step scorecard, (B) documentation-versus-implementation drift,
(C) construct-level weak spots with empirical evidence, (D) where the work is tracked.

**Every empirical figure below was reproduced from the shipped panel during this review, not
carried forward from a previous document.** Quoting unreproduced numbers is the specific
failure this review exists to correct.

*Revised 2026-09-06, second pass: step 4 was rated WEAK in this document's first version on
the grounds that no internal-consistency or factor diagnostics existed. They were built the
same day (`verify/stats.py`, `tests/test_advisory_stats.py`), so that rating is superseded
below and the findings are recorded in §C0 and §C2. The interval between a document
describing the code and the code moving under it is exactly the failure §B is about; a day
is short enough to catch and long enough to matter.*

---

## A. OECD Handbook 10-step scorecard

| # | OECD step | Status | Assessment |
|---|-----------|--------|------------|
| 1 | Theoretical framework | 🟠 PARTIAL | Pillar definitions and per-indicator written justifications exist, with strong provenance discipline in `indicators_list/*.yaml`. But "stability" itself is never formally defined: no statement of what the index measures, for whom, or whether pillars are *formative* (they define stability) or *reflective* (they measure it). Pillar F's incoherence (§C1) traces directly to this gap. No headline method is declared among the four published composites. |
| 2 | Data selection | 🟠 PARTIAL | Selection is argued per indicator but never codified as gates. No minimum coverage floor, no recency requirement, no documented candidate pool. Five indicators have **0% directly measured cells** at the reference year (§C3). |
| 3 | Imputation | 🟢 GOOD | Two-stage hierarchy — carry-forward within a per-indicator staleness limit, then same-year regional mean requiring `MIN_REGIONAL_SAMPLE` peers. Every cell carries a `provenance` label that propagates through pillar reliability tiers to a greyed cell in the interface. Nothing is filled silently. **This is above standard practice.** Caveats: regional-mean is *single* imputation with no variance correction; the missingness assumption is unstated; an `unreliable` pillar still enters the composite at full 1/7 weight. |
| 4 | Multivariate analysis | 🟡 ADEQUATE | *Upgraded 2026-09-06.* Cronbach's α, item-rest correlations, eigenstructure at both levels, KMO and Bartlett now run in `verify/advisory.py`, backed by `verify/stats.py` and 48 tests that check each statistic against a hand-computed case, against algebraic properties, and against an independent implementation (`pingouin`, `factor_analyzer`, `scikit-learn`). What remains open is not a missing diagnostic but a data limit: **the seven-pillar structure cannot be validated by factor analysis on this panel** (§C0), and the diagnostic now says so rather than returning a number. |
| 5 | Normalisation | 🟢 STRONG | Min-max to [0, 100] against **fixed goalposts frozen across the whole panel**, log1p before winsorisation, polarity declared per indicator, out-of-range values clamped and flagged. This resolves the previous review's principal criticism and puts the index ahead of the 2008 text, following HDI/ND-GAIN practice. Open: 19 of 32 goalposts are anchored on imputed extremes; the stated log rule was never applied to re-derive the flags. |
| 6 | Weighting & aggregation | 🟡 ADEQUATE | Four methods — equal, PCA, entropy, geometric — with PCA and entropy weights fitted once on the pooled panel and frozen to `data/panel/weights.yaml`, so a score moves only when a country moves. That is the correct call and it is well argued in source. Undermined by undisclosed implicit weights: cross-listing gives `pv_estimate` and `rl_estimate` 1.90× an even share while `femicide` carries 0.57×, a **3.3× spread**, and the dashboard does not surface it. |
| 7 | Uncertainty & sensitivity | 🔴 **WEAK** | `03_robustness.py` varies three assumptions **one at a time** — weighting, observed-cells-only, island exclusion — and reports point Spearman correlations. There is no joint Monte Carlo over assumptions and **no published rank interval**. The per-country quintile-stability measure is a genuine strength and unusual in this class of index, but it is one axis, not an interval. Current verdict: **moderately sensitive**, worst-case Spearman **0.880**. |
| 8 | Back to the data | 🟢 STRONG | Drill-down from continent to country to pillar to indicator, with provenance and source year attached to every cell. A model implementation of this step. |
| 9 | Links to other indicators | 🔴 WEAK | A five-in / five-out set-membership check against IIAG 2023 (4/5 top, 3/5 bottom), self-documented as Africa-only by construction and therefore near-uninformative. No full-sample rank correlation against IIAG, FSI or V-Dem; no divergence analysis. |
| 10 | Visualisation | 🟢 STRONG | Two-control design (Lens, Compare), greyed-not-blank for untrustworthy cells, reliability tiers surfaced with stated reasons. Remaining gaps are disclosure content, not presentation. |

**Summary: two weak steps (4 and 7), both statistical rather than structural, both tracked.**
Steps 3, 5, 8 and 10 are at or above the standard of published peer indices.

---

## B. Documentation-versus-implementation drift

The 2026-07-14 review opened this section because `references.md` had fallen behind the code.
It happened again, and more severely, through the Phase B/C rebuild. **This review pass
corrected it.** Recorded here because the failure mode recurs and the pattern is the lesson.

| Documented claim | Reality | Resolution |
|---|---|---|
| `references.md` mapped every OECD decision to `02_clean.py` / `03_normalize.py` / `04_score.py` / `05_robustness.py` | All four deleted in the Phase B/C rebuild | Table repointed at `asi/pipeline/*` and `03_robustness.py` |
| **Benefit-of-the-Doubt documented as a first-class method** — full LP formulation, solver, feasibility fallback, two citations; labelled in `app.py`; `pulp` in requirements | **No BoD implementation exists.** `composites.csv` has held four methods since Phase B | Retired explicitly, with the reasoning recorded (§ *Benefit of Doubt — considered and retired* in `references.md`) |
| Cronbach's α "computed per pillar, logged in the diagnostics sheet" | No implementation anywhere in the tree; the threshold constant gated nothing | **Built** (`verify/stats.py`), reported by `verify/advisory.py`, tested against `pingouin` and a hand-computed case. B24 closed |
| Saltelli 2008 listed under implemented sources | Nothing uses it; the joint Monte Carlo it grounds is unbuilt | Marked *Not yet used*, pointing at B20 |
| `verify/__init__.py` described three layers including a nonexistent `replicate` | Four layers registered: `panel`, `contract`, `narrative`, `advisory` | Corrected |
| `01_pull.py` ended by printing "Next step: python 02_clean.py" | That file does not exist — the pull told the user to run a deleted stage | Repointed at `02_panel.py` |
| OECD `§` section numbers throughout | Never verified against the Handbook; appear offset from its step numbering | Flagged as unverified rather than silently retained |

**The pattern.** Every one of these was a claim that had been *true* and was never revisited
when the code moved. The project's own rule in `references.md` — that any new methodological
choice must be logged before the change is committed — is not enforced by anything, and a rule
enforced by intention alone fails at exactly the moment a large refactor lands. The structural
fix is a verification layer that checks documentation claims against code, in the same spirit
as `tests/test_verify_independence.py`. That does not exist yet.

---

## C. Construct-level weak spots (empirical, reproduced 2026-09-06)

### C0. The pillar structure cannot be tested on this data — a new finding

Factor-analytic validation of the seven pillars was the largest open item under OECD
step 4. Running it produced a result nobody expected: **the question cannot be answered
with the panel as it stands.**

| Sample | Complete cases | Variables | Per variable | Matrix rank |
|---|---|---|---|---|
| Reference year 2023 | 31 | 32 | **0.97** | 30 of 32 — singular |
| Best single year (2019) | 18 | 32 | 0.56 | singular |
| All country-years pooled | 147 | 32 | **4.59** | 32 of 32 |

Conventional guidance wants five to ten complete observations per variable. The reference
year offers **under one**, and its correlation matrix is rank-deficient, so a factor model
is not merely underpowered there — it is undefined. Pooling every country-year is the only
route to a full-rank matrix, and it still falls below the lenient five-per-variable floor
while adding a second problem: the same 54 countries recur for 25 years with highly
autocorrelated series, so 147 rows are nothing like 147 independent observations.

**This is a finding about coverage, not about the pillars.** It is distinct from, and
much more useful than, "the structure fails validation". The index cannot currently claim
its seven-pillar structure is statistically supported, and equally cannot be shown to lack
support. Both would be overstatements.

The danger this created is worth recording. A factor routine returns a complete solution
on this data — loadings for all 32 indicators, an assignment for each, and an adjusted
Rand index of **+0.206** at the reference year, **+0.244** pooled. Those numbers look
exactly like findings. `verify/stats.py` now gates on sample adequacy before extraction
and refuses to report them, while still printing what they would have been, so the refusal
cannot be mistaken for concealment.

Routes to an answer, none free: raise indicator coverage so a single year has complete
cases; reduce the indicator set; or adopt a method that tolerates missingness (full
information maximum likelihood), which is a larger undertaking than the diagnostic it
would serve.

### Resolved since the previous review

- **Gender parity scored monotonically** — fixed. `distance_from_parity()` folds GPI to
  `min(x, 2−x)` in `asi/pipeline/panel.py`, so over-parity no longer outscores parity.
- **Displaced persons as an absolute count** — fixed. Converted to a per-1,000 rate before the
  regional fill, so peer averaging works on the rate rather than on population size.
- **`firm_foreign_owned`** (negative item-rest, data back to 2006) — replaced by
  `domestic_credit_private`.
- **Sample-dependent normalisation bounds** — fixed. Fixed goalposts, frozen and versioned.
- **Cross-pillar redundancy invisible** — fixed. `verify/advisory.py` now checks across pillars
  as well as within.
- **Ad-hoc confidence band** (`2.0 + pct_filled × 26.7`) — deleted. Nothing has replaced it;
  the Monte Carlo interval that should is B20.

### Open, ranked by severity

1. **Pillar F is incoherent, and `co2_pc` inverts development.** ρ(`co2_pc`, `gdp_pc_ppp`) =
   **−0.93** at the reference year: in Africa, CO₂ per capita is a wealth proxy, so negative
   polarity makes Pillar F reward energy poverty. F is the only pillar PCA excludes entirely
   (weight **0.000**), while entropy gives it the **highest** weight of any pillar (0.204).
   Both are defensible on their own terms and they cannot both be right. ND-GAIN's
   exposure–sensitivity–capacity architecture is the reference model. *(B17)*

2. **The WGI family is counted repeatedly.** Six of 32 indicators carry **28.9%** of composite
   weight, and eight indicator pairs inside Pillar A exceed |ρ| = 0.80 — `rl_estimate` ×
   `cc_estimate` at **+0.93**, `ge_estimate` × `rq_estimate` at **+0.91**. Pillar A is
   effectively one measurement taken six times.

   Internal consistency now confirms this directly. Pillar A returns **α = 0.958**, the
   highest of any pillar and above the point where α indicates redundancy rather than
   reliability. A test in `tests/test_advisory_stats.py` encodes the property that makes
   this readable — duplicating an item raises α without adding information — so the figure
   is not mistaken for a quality score. Pillar A's coherence is an artefact of counting one
   thing six times, not evidence of construct validity. *(B18)*

   **Per-pillar α at the reference year**, reproduced from the shipped panel and matching
   the figures previously quoted from the retired pipeline to three decimals:

   | Pillar | α | k | n | Reading |
   |---|---|---|---|---|
   | A Political | **0.958** | 6 | 54 | redundant, not reliable — see above |
   | B Economic | 0.507 | 5 | 46 | below the project's 0.60 threshold |
   | C Human capital | 0.589 | 8 | 31 | below threshold; thinnest sample of any pillar |
   | D Health | 0.809 | 5 | 54 | coherent |
   | E Security | 0.472 | 4 | 38 | **lowest**; `intent_homicide` item-rest is **−0.104** |
   | F Environment | 0.608 | 4 | 54 | marginal, and see §C1 |
   | G Infrastructure | 0.799 | 5 | 42 | coherent |
   | **All 32 as one scale** | **0.810** | 32 | 31 | higher than five of the seven pillars |

   The last row is the uncomfortable one. Treating all 32 indicators as a single
   undifferentiated scale produces better internal consistency than most of the pillars
   achieve individually, which is what would be expected if the index were closer to
   one-dimensional than a seven-pillar structure implies. It is consistent with the
   eigenstructure: at pillar level, **PC1 explains 63.4%** and only two components clear
   Kaiser. It is *not* proof — §C0 explains why the test that could settle it cannot be
   run — and a formative index is under no obligation to be factorially clean. But it is
   the strongest available evidence that the seven-pillar framework is a presentational
   and theoretical choice rather than a structure the data insists on, and it should be
   defended as such rather than assumed.

2a. **Eleven indicators correlate below +0.30 with the rest of their own pillar**, and one
   is negative: `intent_homicide` at **−0.104** in Pillar E. A negative item-rest
   correlation means the indicator moves against everything else in its pillar; the first
   thing to check is polarity coding, before construct. Also flagged: `gdp_growth_3yr_avg`
   (+0.077), `femicide` (+0.147), `gini` (+0.175), `va_estimate` in Pillar C (+0.173) —
   the last being a cross-listed WGI governance measure sitting in a human-capital pillar.
   *(feeds B17, B18, B36)*

3. **Five indicators have no direct measurement at the reference year.** `freshwater_withdraw`,
   `secondary_gpi`, `primary_enroll`, `social_protection_labour_pop` and `secondary_enroll` are
   all **0% observed** in 2023 — every value is carried forward or regionally estimated. The
   reference year overall is 57.6% observed, 22.2% carried forward, 14.7% regional estimate,
   5.4% absent. *(B36)*

4. **Effective indicator weights are undisclosed.** Equal pillar weights are not equal indicator
   weights: `pv_estimate` and `rl_estimate` carry 1.90× an even share, `femicide` 0.57× — a 3.3×
   spread nobody chose and the interface does not show. *(N3, B32)*

5. **Goalposts anchored on imputed extremes.** 19 of 32 indicators have at least one bound set
   by a regional-mean or carried-forward value rather than a real measurement; four have both.
   Recorded in `registry/goalposts.yaml` as a standing review item. *(B19)*

6. **The missing-data assumption is unstated.** Regional-mean fill is single imputation, and
   missingness here is plainly not at random — the states least able to report are the least
   stable. Filling them with a regional mean pulls them toward the average and flatters exactly
   the countries the index should discriminate. *(B21)*

7. **Log-transform flags were never re-derived under the stated rule.** The rule — log1p iff
   post-fill skew > 1 and min ≥ 0 — is written down and has never been applied; five indicators
   are flagged while several unflagged ones have comparable skew. *(B22)*

8. **Unreliable pillars enter the composite at full weight.** A pillar greyed out in the
   interface as too inferred to display still contributes 1/7 of the composite behind it.
   *(B16)*

9. **No published uncertainty interval.** A prior 2,000-draw experiment found a median 95% rank
   interval of **22 places out of 54**, with only 29.4% of country pairs separable — the data
   supports roughly five bands, not 54 ranks. That figure predates the current panel and needs
   reproducing before it is published, but the index currently presents 54 distinct ranks with
   no interval at all. *(B20, B30)*

### What held up

The verification architecture, and specifically its enforced independence — `verify/panel.py`
re-derives 88.6% of scoring cells using different tools, and `tests/test_verify_independence.py`
fails the build on any `asi.*` import into `verify/` beyond declared constants. Provenance
tracking end to end. Fixed goalposts with outward rounding. Per-indicator YAML justification
discipline. Frozen data-driven weights. The reference-year rule. The drill-down interface. The
narrative corpus's refusal to count a citation as verified until an audit run has opened it.

---

## D. Where the work is tracked

**This document does not carry a roadmap.** The previous version did, and it drifted out of
sync with `BACKLOG.md`, `ITERATION_PLAN.md`, `ROADMAP.md` and `STATISTICS.md` — five planning
documents describing overlapping work in different vocabularies was itself a contributor to the
drift in §B.

`methodology/BACKLOG.md` is the live tracker. Every open item in §C above carries its backlog
id. The two OECD weaknesses map to:

- **Step 4** — B24 (Cronbach α) and B27 (PCA dimensionality) are **closed**: both run in
  `verify/advisory.py`, computed on polarity-aligned normalised scores, each figure
  labelled with the level it describes. Factor validation of the pillar structure is
  blocked by sample adequacy rather than unbuilt (§C0) and needs a backlog id of its own,
  framed as a coverage problem.
- **Step 7** — B20 (joint Monte Carlo and rank intervals), B30 (surface them), B43 (surface
  `robustness.json`).
- **Step 9** — B31 (full-sample external validation with a divergence table).

---

## Sources

- OECD/JRC (2008), *Handbook on Constructing Composite Indicators* — primary framework
- [JRC 10-Step Pocket Guide to Composite Indicators & Scoreboards](https://knowledge4policy.ec.europa.eu/sites/default/files/10-step-pocket-guide-to-composite-indicators-and-scoreboards.pdf)
- [JRC COIN toolkit](https://knowledge4policy.ec.europa.eu/composite-indicators/toolkit_en) · [COINr R package](https://bluefoxr.github.io/COINr/)
- [IIAG Methodology (Mo Ibrahim Foundation, 2024)](https://iiag.online/methodology.html)
- [ND-GAIN Country Index Methodology](https://gain.nd.edu/our-work/country-index/methodology/)
- Saisana, Saltelli & Tarantola (2005), *JRSS-A* 168(2) — joint uncertainty and sensitivity
  analysis as quality assessment for composite indicators
- Internal evidence: `python -m verify.run` (all four layers) and `verify/advisory.py`
  diagnostics, run 2026-09-06 against the shipped panel; `data/panel/robustness.json`
