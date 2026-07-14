# ASI Methodology Review & Refinement Plan

*Review date: 2026-07-14 · Reviewer: pipeline evaluation session (with Oscar Bailey)*
*Prerequisite: computational correctness verified — `00_evaluate.py` 31/31 PASS (independent
re-derivation from frozen raw pull through all five scoring methods).*

This review evaluates the **design** of the ASI against the OECD/JRC Handbook on Constructing
Composite Indicators (2008), the JRC 10-Step Pocket Guide (2019), and two peer indices
(IIAG 2024, ND-GAIN). It covers three layers: (A) OECD step-by-step scorecard,
(B) documentation-vs-implementation drift, (C) construct-level weak spots with empirical
evidence, followed by (D) a phased refinement roadmap.

---

## A. OECD Handbook 10-step scorecard

| # | OECD step | Status | Assessment |
|---|-----------|--------|------------|
| 1 | Theoretical framework | 🟠 PARTIAL | Pillar definitions and per-indicator justifications exist (strong provenance discipline in `indicators_list/*.yaml`), but "stability" itself is never formally defined: no documented statement of what the index measures, for whom, or whether pillars are *formative* (they define stability) or *reflective* (they measure it). Pillar F's incoherence (§C2) traces directly to this gap — no framework decision was made on whether environment enters as *current stress*, *future vulnerability*, or *sustainability counterweight*. |
| 2 | Data selection | 🟠 PARTIAL | Selection criteria are argued per indicator but never codified as rules. No minimum real-coverage floor (femicide entered with 18/54 real observations), no recency requirement (firm_foreign_owned uses 2006 surveys), no documented candidate-pool from which indicators were selected. IIAG 2024 codifies exactly these standards ("quality, periodicity and country coverage") as explicit gates. |
| 3 | Imputation | 🟡 ADEQUATE | Two-stage hierarchy (5-yr lookback → regional mean) is transparent and fully logged; fills flagged per country and reflected in confidence bands. Caveats: regional-mean is *single* imputation (shrinks within-region variance, creates artificial ties among filled countries); fills are included in the min-max normalization sample (verified, `00_evaluate` check 1.5) which lets imputed values set score anchors; no sensitivity analysis of the imputation choice itself. |
| 4 | Multivariate analysis | 🟠 PARTIAL | Within-pillar Spearman matrices and Cronbach's alpha are computed, but alpha runs on **raw, mixed-polarity values** — negative items deflate alpha mechanically, making the B/C/D/E/F warnings uninterpretable. No analysis validates the 7-pillar grouping itself (e.g., exploratory factor analysis); the PCA stage *found* structure (Pillar F loads inversely) but this is treated as a scoring quirk rather than a Step-4 diagnostic. |
| 5 | Normalization | 🟡 ADEQUATE | Min-max to [0,100] with polarity handling is Handbook-standard and correctly implemented. Two design caveats: (i) **sample-dependent bounds** — every re-pull re-anchors all scores to the current sample's min/max, so scores are not comparable across index editions (HDI and ND-GAIN both use fixed goalposts for this reason); (ii) **double outlier treatment** — IQR winsorization (02) *and* log1p (03) both compress tails; post-winsorization skew of mort_infant is 0.15, which log1p then over-corrects to −0.93. |
| 6 | Weighting & aggregation | 🟢 STRONG* | Five methods (equal, PCA, BoD, entropy, geometric) exceed typical practice and are correctly sourced (Cherchye 2007, Munda & Nardo 2009, Zhou 2007). *Caveat: cross-listing creates undisclosed implicit weights — WGI variables carry 1.68–1.90× a median indicator's weight while Pillar C members carry 0.57×. Equal-across-pillars ≠ equal-across-indicators; the dashboard does not surface effective weights. |
| 7 | Uncertainty & sensitivity | 🟡 ADEQUATE | 05_robustness covers weight perturbation, MaxS adversarial search (rho=0.9245, Robust), fill-exclusion, island-exclusion. Missing: a *joint* Monte Carlo over all assumptions (imputation × winsorization × normalization × weighting) per Saisana/Saltelli/Tarantola 2005 — currently each assumption is tested in isolation. Confidence band uses ad-hoc constants (`half_width = 2.0 + pct_filled × 26.7`) with no documented derivation. |
| 8 | Back to the data | 🟢 STRONG | The drill-down dashboard (country → pillar → indicator → formula walkthrough with raw values and continental ranks) is a model implementation of this step. |
| 9 | Links to other indicators | 🟠 PARTIAL | Audit checks top/bottom-10 overlap with IIAG 2023 only. No full-sample rank correlation against IIAG overall score, Fragile States Index, or V-Dem; no divergence analysis (countries where ASI disagrees with peers are the most informative cases). |
| 10 | Visualisation & communication | 🟢 STRONG | Dashboard is complete and now verified working; methodology tab explains all five methods with strengths/limitations. Gaps are content, not presentation: stale claims (§B) and missing staleness/effective-weight disclosures. |

---

## B. Documentation-vs-implementation drift

`methodology/references.md` (last updated 2026-06-18) has fallen behind the code. Its own
footer rule — "any addition … must be logged here before the change is committed" — has been
broken by every change since mid-June. Specific mismatches:

| Documented claim | Actual behavior | Severity |
|---|---|---|
| `IQR_MULTIPLIER = 1.5` (Tukey fences, cited twice) | `constants.py: IQR_MULTIPLIER = 2.0` | **High** — a cited methodological parameter is wrong in the doc; either the doc or the constant is the intended design |
| Cronbach threshold α ≥ 0.70 ("values below 0.70 should trigger review") | `constants.py: MIN_CRONBACH_ALPHA = 0.60` | Medium — inconsistent standard |
| "Stage 05 — not yet implemented"; "MaxS **SLSQP** worst-case search" | 05_robustness fully implemented; SLSQP was *replaced* by random-restart grid search (July 2026) precisely because SLSQP was invalid on a rank-based objective | Medium — describes a method that was rejected |
| PCA: "loadings taken as raw weights; sign flipped if majority negative" | Negative post-orientation loadings are now **excluded** (zeroed) with warning — a material methodological addition | Medium |
| BoD: no mention of the n_valid < 4 equal-weight fallback | Fallback exists and fires for countries with < 4 valid pillars | Low |
| Title: "African **Instability** Index (AII)" | Project renamed African **Stability** Index | Low |
| "Pillar C with 10 indicators … Pillar E with 4" | C has 8 (incl. cross-listed va), E has 4 (incl. 2 cross-listed) | Low |
| Winsorisation sheet "logged with pre/post values" | Sheet logs bounds + cap counts only | Low |

Dashboard (07) carries its own stale claims:

| UI claim | Reality |
|---|---|
| Header + stat card: "**36 Indicators**" | 32 scoring + 1 descriptive = 33 in the registry |
| Audit panel: "rq_estimate is in pillars A, B, and G — effective weight 2.4x" | rq_estimate was consolidated to Pillar A only (the YAML documents this consolidation) |
| Audit panel: "Displaced persons is an absolute count — large countries are penalized" | Converted to per-1,000-population in 02_clean Step 1b (July 2026); audit itself now PASSes this |

---

## C. Construct-level weak spots (empirical evidence from current data)

Ranked by severity. Items 1–2 change scores in the wrong direction; 3–5 dilute signal;
6–10 are transparency/rigor gaps.

1. **Gender parity indices scored monotonically.** `primary_gpi` / `secondary_gpi` use
   positive polarity, but GPI's ideal is 1.0 — deviation *either way* is dysfunction
   (UNESCO convention: |GPI−1|). In current data 17/54 (primary) and 25/54 (secondary)
   countries exceed 1.0, so over-parity (often boys dropping out — a conflict/child-labour
   signal) outscores perfect parity. **Fix: distance-from-parity transform
   (`min(GPI, 2−GPI)`) before normalization.**

2. **`co2_pc` inverts development; Pillar F is incoherent.** ρ(gdp_pc_ppp, co2_pc) = **−0.908**:
   in Africa CO₂/capita is a wealth proxy, so negative polarity makes Pillar F reward energy
   poverty — the demonstrated reason PCA excludes Pillar F (inverse PC1 loading). The YAML
   justification conflates own-emissions with climate *exposure*. Item-rest correlations for
   all four F members are 0.21–0.44 (weakest pillar), and `nonrenew_elec` rewards
   hydro-dependence that `elec_access_tot` (G) simultaneously penalizes. ND-GAIN's
   vulnerability/readiness architecture is the reference model: measure *exposure, sensitivity
   and adaptive capacity*, not emissions.

3. **`firm_foreign_owned`**: only indicator with negative item-rest (−0.103), data as old as
   2006 (20/49 countries pre-2021), conceptually confounded (extractive FDI concentrates in
   less-stable states). Removal/replacement candidate (e.g., domestic credit to private
   sector % GDP, FS.AST.PRVT.GD.ZS).

4. **`femicide`**: 18/54 real observations; 26 stage-2 regional fills make the column two-thirds
   regional averages (item-rest 0.101). Motivates a codified coverage floor (Step-2 rule).

5. **Staleness hidden by "most_recent".** Median observation year actually used:
   primary_enroll **2017** (49/49 countries pre-2021), secondary_enroll 2017,
   social_protection 2017 (oldest 2005), gini 2020 (28 pre-2021), learning_poverty 2019.
   The composite silently mixes 2024 and ~2006–2017 measurements.

6. **WGI concentration**: 6/32 indicators → **28.9%** of effective composite weight
   (Pillar A 100% WGI, E 50%, G 40%) — one perception-based source family. IIAG's answer is
   source diversification (49 sources for 96 indicators); at minimum this needs prominent
   disclosure.

7. **Cross-pillar redundancy invisible to the audit** (which checks within-pillar only):
   gdp_pc_ppp(B) × co2_pc(F) = −0.91 (wealth counted +B and −F, silently self-cancelling);
   gdp_pc_ppp(B) × elec_access_tot(G) = +0.81 (wealth double-counted).

8. **Log-transform rule inconsistent**: five indicators are log-flagged, but seven non-flagged
   indicators have comparable skew (firm_foreign 1.45, inflation 1.34, social_protection 1.33,
   co2_pc 1.31, hand_washing 1.26, freshwater 1.23, managed_water 1.02). No explicit rule
   exists; combined with §A5's double-treatment issue.

9. **Cronbach's alpha on raw mixed-polarity values** renders the diagnostic uninterpretable
   (a pillar with negative-polarity items *should* show low raw alpha). Compute on
   polarity-corrected normalized scores.

10. **Ad-hoc confidence band** (`2.0 + pct_filled × 26.7`): magic numbers with no derivation;
    should fall out of the Phase-3 Monte Carlo instead.

### What held up (do not touch)

Verification infrastructure (00_audit + 00_evaluate — the latter re-derives everything from the
frozen raw pull with independent solvers); the five-method suite with correct sourcing; the
robustness stage; per-indicator YAML justification discipline; the documented consolidation
decisions (adult_literacy, primary_oos, modsev_food_insec, social_safetynet, rq de-cross-listing);
the IDP per-capita conversion; polarity on the other 28 indicators (all empirically consistent);
dashboard drill-down.

---

## D. Refinement roadmap

Each phase ends with `python 00_evaluate.py` (after deleting/re-freezing the baseline if raw
inputs changed) + `python 00_audit.py` + a references.md entry. Phases are ordered so cheap
truth-restoring work lands before score-changing work.

**Phase 0 — Documentation truth (½ session, no score changes).**
Fix every §B mismatch: references.md (IQR k, alpha threshold, MaxS description, PCA exclusion,
BoD fallback, title, pillar sizes, Stage-05 status) and dashboard (indicator count 36→32,
rq_estimate claim, IDP claim). Decide the *intended* IQR multiplier (1.5 Tukey vs 2.0 current)
— this is a real methodological decision currently made by accident.

**Phase 1 — Construct fixes (1 session; scores change, re-baseline).**
(a) GPI distance-from-parity transform (in 02_clean as a derived step, like the IDP conversion);
(b) drop or replace firm_foreign_owned; (c) adopt a codified selection rule — e.g. "≥ 50% real
observations and median data year ≥ 2018 required for scoring role" — and apply it (femicide is
the test case: drop, or demote to descriptive); (d) adopt an explicit log rule ("log1p iff
post-fill skew > 1 and min ≥ 0, applied **before** winsorization") and re-derive flags.

**Phase 2 — Pillar F redesign (1–2 sessions; the big one).**
Reframe F as *climate/resource vulnerability* following ND-GAIN's exposure–sensitivity–capacity
model. Replace co2_pc with vulnerability-side series available in WDI (candidates to screen:
droughts/floods/extreme-temp exposure EN.CLC.MDAT.ZS, water stress ER.H2O.FWST.ZS as upgrade to
current withdrawal share, renewable energy share EG.FEC.RNEW.ZS reframed positively, arable land
per capita, food import dependence). Resolve the nonrenew_elec ↔ elec_access contradiction
(likely: drop nonrenew_elec, keep energy access in G only). Success criterion: all F item-rest
correlations > 0.3 and PCA no longer excludes the pillar.

**Phase 3 — Statistical rigor (1 session).**
(a) Cronbach's alpha on polarity-corrected normalized values (02 diagnostics);
(b) joint Monte Carlo uncertainty analysis in 05_robustness (sample: imputation on/off ×
winsorization on/off × 5 methods × weight perturbation) reporting per-country rank intervals
per Saisana et al. 2005; (c) replace the ad-hoc confidence band with the MC rank interval;
(d) add cross-pillar redundancy check (|ρ| > 0.8 across pillars) to 00_audit.

**Phase 4 — Transparency (½ session, dashboard only).**
(a) Per-country *median data year* + oldest-observation stat in the data-quality panel;
(b) effective-weights table (the §C6 numbers) in the Methodology tab; (c) WGI-reliance
disclosure box; (d) surface fill provenance (stage-1 vs stage-2) in indicator drill-down.

**Phase 5 — External validation (½–1 session).**
Full 54-country Spearman of ASI (equal + geometric) against IIAG 2024 overall score, FSI 2025,
and WGI PV directly; report in audit with a divergence table (countries ranked >10 places apart)
and written interpretation of *why* ASI diverges (it should — it measures more than governance —
but the divergences must be explainable).

**Phase 6 — Future architecture (design decision, then 1 session).**
(a) **Fixed goalposts**: decide whether editions should be comparable over time; if yes, freeze
per-indicator normalization bounds (HDI/ND-GAIN precedent) instead of sample min-max, and store
them in the registry; (b) adopt IIAG's *biennial refinement* discipline — indicator changes
batched to editions, entire back-series recomputed on change; (c) optional third-party
cross-check: run the dataset through JRC's COIN Tool / COINr for an external methodological
audit of the same numbers.

---

## Sources

- OECD/JRC (2008), *Handbook on Constructing Composite Indicators* — primary framework (already in references.md)
- [JRC 10-Step Pocket Guide to Composite Indicators & Scoreboards](https://knowledge4policy.ec.europa.eu/sites/default/files/10-step-pocket-guide-to-composite-indicators-and-scoreboards.pdf)
- [JRC Competence Centre on Composite Indicators (COIN) toolkit](https://knowledge4policy.ec.europa.eu/composite-indicators/toolkit_en) · [COINr R package](https://bluefoxr.github.io/COINr/)
- [IIAG Methodology (Mo Ibrahim Foundation, 2024)](https://iiag.online/methodology.html) · [2024 methodology PDF](https://assets.iiag.online/2024/2024-IIAG-methodology_EN.pdf)
- [ND-GAIN Country Index Methodology](https://gain.nd.edu/our-work/country-index/methodology/) · [Technical report](https://gain.nd.edu/assets/522870/nd_gain_countryindextechreport_2023_01.pdf)
- Saisana, Saltelli & Tarantola (2005), *JRSS-A* 168(2) — joint uncertainty/sensitivity analysis (already cited in references.md as "planned")
- Internal evidence: `00_evaluate.py` run 2026-07-14 (31/31), design diagnostics (skewness, item-rest correlations, effective weights, staleness, cross-pillar redundancy) on the frozen 2026-07 baseline
