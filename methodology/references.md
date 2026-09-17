# Methodological References — African Stability Index (ASI)

Every design choice in this pipeline is grounded in a published source.
This file maps each source to the specific implementation decision it justifies,
including any deviations from or limitations relative to the cited approach.

---

## Primary Methodology Framework

### OECD/JRC Composite Indicators Handbook (2008)
> Nardo, M., Saisana, M., Saltelli, A., Tarantola, S., Hoffmann, A., & Giovannini, E.
> *Handbook on Constructing Composite Indicators: Methodology and User Guide.*
> OECD Publishing, Paris, 2008.
> DOI: [10.1787/9789264043466-en](https://doi.org/10.1787/9789264043466-en)

This is the primary methodological authority for the ASI pipeline. It is the gold standard
for composite index construction and is used by the UN, World Bank, and EU Commission.

**Decisions grounded in this source:**

| Decision | Handbook section | Implementation |
|---|---|---|
| Min-max normalization to [0, 100] | §6.1 | `asi/pipeline/normalize.py` — `normalize_value()` |
| Log transformation before normalization for skewed distributions | §6.2 | `asi/pipeline/goalposts.py` — `apply_log()`, on indicators carrying `log_transform: true` in `indicators_list/*.yaml` |
| Polarity inversion at normalization step | §5.3 | `asi/pipeline/normalize.py` — `normalize_value()` inverts to `(gmax-x)/(gmax-gmin)*100` for negative polarity |
| IQR Winsorization to handle outliers (cap, do not delete) | §5.2 | `asi/pipeline/goalposts.py` — `winsorize_bounds()` at `IQR_MULTIPLIER = 2.0` (widened from Tukey's 1.5; see Winsorization section). Bounds are **frozen** with the goalposts, not recomputed per run |
| Imputation hierarchy before leaving a cell empty | §5.4 | `asi/pipeline/panel.py` — `window_value()` (carry-forward within `max_carry_forward`) then `regional_fill()` (same-year regional mean, `MIN_REGIONAL_SAMPLE` peers required). Every cell carries a `provenance` label; nothing is filled silently |
| Equal weights as the default / reference case | §7.1 | `asi/pipeline/score.py` — `weighted_composite()` with `WEIGHT_PRESETS["equal"]` |
| PCA-derived weights as a data-driven alternative | §7.3 | `asi/pipeline/score.py` — `fit_pca_weights()`, fitted once on the pooled panel and frozen to `data/panel/weights.yaml` |
| Sensitivity analysis / robustness testing across methods | §8 | `03_robustness.py` — method agreement, adversarial weight search, measured-cells-only rebuild, island exclusion |
| Transparency: all weights, bounds, and intermediate values published | throughout | `registry/goalposts.yaml`, `data/panel/weights.yaml`, and per-cell provenance in `data/panel/observations.csv` |

> **Section numbers are unverified.** The `§` references above were carried forward from
> earlier revisions of this document and have not been checked against the 2008 Handbook
> itself. They are internally consistent but appear offset from the Handbook's step
> numbering. Treat them as a pointer, not a citation, until confirmed against the source.

**Where this index departs from the Handbook's own step list**, and knowingly:

| OECD step | State | Detail |
|---|---|---|
| 4 — Multivariate analysis | **Adequate** | Cronbach α, item-rest correlations, eigenstructure at both levels, KMO and Bartlett all run (`verify/stats.py`, reported by `verify/advisory.py`). Factor-analytic validation of the seven-pillar structure is **blocked by coverage, not unbuilt**: the reference year has 31 complete cases across 32 indicators and a singular correlation matrix. The diagnostic refuses to report rather than returning a number. See `METHODOLOGY_REVIEW.md` §C0. |
| 7 — Uncertainty & sensitivity | **Weak** | `03_robustness.py` varies assumptions **one at a time** and reports point Spearman correlations. There is no joint uncertainty analysis and no published rank interval. |
| 9 — Links to other indicators | **Weak** | A five-in / five-out set-membership check against IIAG 2023, Africa-only by construction. No full-sample correlation against any peer index. |

**Known deviations:**
- The Handbook recommends z-score normalization as an alternative to min-max. We use min-max
  because it produces scores in a fixed [0, 100] range that is more interpretable for a
  public-facing index. Z-scores can exceed these bounds and are harder to communicate.
  **Untested:** no sensitivity analysis compares the two. This is a stated choice, not a
  demonstrated one.
- The Handbook's min-max is computed against the observed sample. We normalise against
  **fixed goalposts** frozen across the whole panel instead, so that a score moves only when
  that country's data moves. This follows later practice (HDI, ND-GAIN) rather than the 2008
  text, and is the deviation that makes a time series possible. See
  `asi/pipeline/goalposts.py`.

---

## Scoring Methods

### Benefit of Doubt (BoD) — considered and retired

> Cherchye, L., Moesen, W., Rogge, N., & Van Puyenbroeck, T.
> "An Introduction to 'Benefit of the Doubt' Composite Indicators."
> *Social Indicators Research*, 82(1), 111–145, 2007.
> DOI: [10.1007/s11205-006-9029-7](https://doi.org/10.1007/s11205-006-9029-7)
>
> Rogge, N. (2018). "Composite Indicators as Generalized Benefit-of-the-Doubt Weighted
> Averages." *European Journal of Operational Research*, 267(1), 381–392.

**BoD is not a method of this index.** It was implemented in the pre-panel pipeline as a
restricted DEA-CCR linear program — one LP per country, awarding each the weight vector
that maximised its own composite subject to global weight bounds — and was retired when
the index became a panel. This section records the decision rather than deleting the
history, because the reasoning generalises.

**Why it was retired.** BoD solves for each country's most favourable weighting against
*that year's* peers, so a BoD score is a within-year statement by construction. Every
other method in this index now uses weights fitted once on the pooled panel and reused
for every year, specifically so that a country's score moves only when that country's
data moves (see *PCA Weighting* below and `data/panel/weights.yaml`). A BoD series would
have been the one published method a reader could not read as a time series, sitting
beside three that they can. That is a worse defect than the absence of a fifth method.

**What remains.** `WEIGHT_MIN = 0.05` and `WEIGHT_MAX = 0.25` were introduced as the LP's
bounds and still stand, now as the definition of an admissible weighting in the
adversarial search of `03_robustness.py`. The feasibility requirement they were chosen to
satisfy — `7*MIN <= 1 <= 7*MAX` — is unchanged and is asserted by
`tests/test_registry.py::test_weight_bounds_are_feasible`.

**Correcting the record.** Until this revision, this document described the LP, its
solver, and a July 2026 correction to its feasibility fallback, as though all three were
live; `pulp` remained in `requirements-pipeline.txt`; and `asi/dashboard/app.py` carried a
display label for the method. None of it ran. The published methods have been `equal`,
`pca`, `entropy` and `geometric` since the Phase B rebuild — see
`data/panel/composites.csv`, which is the authority on what the index actually computes.

---

### Geometric Mean Aggregation (Non-Compensatory)

> Munda, G., & Nardo, M.
> "Noncompensatory/nonlinear composite indicators for ranking countries: a defensible setting."
> *Applied Economics*, 41(12), 1513–1523, 2009.
> DOI: [10.1080/00036840601019364](https://doi.org/10.1080/00036840601019364)

> UNDP. *Human Development Report 2010: The Real Wealth of Nations.*
> United Nations Development Programme, New York, 2010.
> (Chapter 2 and Technical Note 1 — geometric mean adoption for HDI from 2010)

The arithmetic mean is fully compensatory: a very high score in one pillar can fully offset
a near-zero score in another. For a stability index, this is methodologically problematic —
a country at war but with a strong economy should not rank highly overall.

The geometric mean `exp(Σ w_i · ln(s_i))` introduces partial compensability: low scores
in any dimension drag the composite down non-linearly, preventing full substitution.

**Implementation in `asi/pipeline/score.py` — `geometric_composite()`:**
- Equal weights (1/7 per pillar) applied in log space
- Scores floored at `1e-8` before `ln()` to avoid `log(0) = -inf`
- Countries missing all pillar scores receive NaN

**Limitation:** Geometric mean penalises uneven development more harshly than arithmetic mean.
This is a feature, not a bug, for a stability index — but users should be aware that
rankings can shift significantly between equal and geometric methods.

---

### Shannon Entropy Weighting

> Zhou, P., Ang, B. W., & Poh, K. L.
> "A mathematical programming approach to constructing composite indicators."
> *Ecological Economics*, 62(2–3), 291–297, 2007.
> DOI: [10.1016/j.ecolecon.2006.12.020](https://doi.org/10.1016/j.ecolecon.2006.12.020)

> Original entropy theory: Shannon, C. E.
> "A mathematical theory of communication."
> *The Bell System Technical Journal*, 27(3), 379–423, 1948.
> DOI: [10.1002/j.1538-7305.1948.tb01338.x](https://doi.org/10.1002/j.1538-7305.1948.tb01338.x)

Entropy weights reward pillars that vary meaningfully across countries (high information
content) and downweight pillars where all countries score similarly (low information).
This is purely data-driven — no expert judgment is required.

**Implementation in `asi/pipeline/score.py` — `fit_entropy_weights()`:**
- Entropy `H_j = -Σ p_ij · ln(p_ij)` computed per pillar j
- `p_ij = s_ij / Σ_i s_ij` (proportion of pillar j's total score attributed to country i)
- Divergence `e_j = 1 - H_j / ln(n)` (lower entropy → more informative → higher weight)
- Weights normalised so `Σ e_j = 1`
- NaN pillar scores filled with column mean before entropy calculation (so NaN does not
  eliminate a country from entropy estimation)

**Limitation:** Entropy weights are sensitive to sample composition. Adding or removing
countries changes the weights. Results are not comparable across AII versions with
different country lists.

---

### Principal Component Analysis (PCA) Weighting

> Nardo, M., Saisana, M., Saltelli, A., & Tarantola, S.
> *Tools for Composite Indicators Building.*
> EUR 21682 EN. European Commission, Joint Research Centre, Ispra, 2005.
> Available: [https://publications.jrc.ec.europa.eu/repository/handle/JRC31473](https://publications.jrc.ec.europa.eu/repository/handle/JRC31473)

> Also: OECD Handbook (2008) §7.3 (above).

The first principal component captures the direction of maximum variance in pillar scores.
Using its loadings as weights assigns more weight to pillars that differentiate countries most.

**Implementation in `asi/pipeline/score.py` — `fit_pca_weights()`:**
- Fit PCA on countries with complete pillar data (StandardScaler applied first)
- First PC loadings taken as raw weights; whole vector sign-flipped if the majority of
  loadings are negative (orient PC1 toward "higher stability = higher score")
- **Negative loadings after orientation are excluded (zeroed), not `abs()`-ed.** A pillar
  that loads inversely on the stability dimension is set to weight 0 and logged. Using
  `abs()` would silently invert its contribution and misrepresent the variance structure
  (OECD §6.2). In the current data this excludes Pillar F (Environmental), which loads
  inversely — a real signal, not a bug (see METHODOLOGY_REVIEW §C2). If all loadings are
  excluded, the method falls back to equal weights.
- Remaining loadings normalised to sum to 1 (used as convex combination weights)
- Weighted mean then computed for all countries, including those with some missing pillars
  (available pillar weights renormalised on the fly)
- Final scores rescaled to [0, 100] via min-max

**Limitation:** If pillars are highly correlated (which they are in stability indices),
PC1 may not capture structure beyond a single "overall development" axis. PCA weights
are descriptive of the sample, not prescriptive. Treat as a sensitivity check, not a
preferred method.

---

## Data Quality and Diagnostics

### Cronbach's Alpha (Internal Consistency)

> Cronbach, L. J.
> "Coefficient alpha and the internal structure of tests."
> *Psychometrika*, 16(3), 297–334, 1951.
> DOI: [10.1007/BF02310555](https://doi.org/10.1007/BF02310555)

Alpha measures whether indicators within a pillar are measuring a common underlying construct.
The conventional minimum for acceptable internal consistency is α ≥ 0.70
(Nunnally, 1978; George & Mallery, 2003).

**Implementation in `verify/stats.py` - `cronbach_alpha()`, reported by
`verify/advisory.py`** (backlog B24, closed 2026-09-06):

- Computed on the panel's `score` column, which normalisation has already inverted for
  negative-polarity indicators, so the items are **polarity-aligned by construction**. The
  retired pre-panel implementation ran on raw mixed-polarity values, which mechanically
  deflates alpha for any pillar holding a reversed item; that is why its warnings were
  uninterpretable and why the threshold sits at 0.60 rather than the conventional 0.70.
- Listwise deletion, sample variance (ddof=1). The number of complete observations is
  reported alongside every figure, so an alpha resting on 31 countries cannot be quoted as
  though it rested on 54.
- Returns undefined rather than a number for fewer than two items, fewer than three
  complete rows, or zero total variance.
- Cross-checked against `pingouin.cronbach_alpha` to twelve decimal places, and against a
  four-subject case computed by hand, in `tests/test_advisory_stats.py`.

**Limitation, and it is the important one here.** Alpha rises mechanically with item count
and with redundancy among items. Pillar A returns 0.958 not because it is the best-measured
pillar but because six of its indicators are the WGI family, correlating up to 0.93 - one
measurement taken six times. A test encodes this property directly (adding a duplicate item
raises alpha) so the figure is not read as a quality score. Alpha is evidence about
redundancy at least as much as about reliability, and it is not a measure of
unidimensionality at all.

**Limitation:** Cronbach's alpha assumes tau-equivalence (all indicators equally measure
the construct) and is sensitive to the number of indicators. A large pillar (e.g. Pillar C
with 8 indicators) will mechanically produce higher alpha than a small pillar (e.g. Pillar E
with 4 indicators), even if coherence is similar. It is also deflated by mixed polarity when
computed on raw values (see above).

---

### IQR Winsorization

> Tukey, J. W.
> *Exploratory Data Analysis.*
> Addison-Wesley, Reading, MA, 1977. ISBN: 978-0201076165.

Tukey's fences cap extreme values to `[Q1 - k·IQR, Q3 + k·IQR]`. Tukey's conventional
k = 1.5 marks "outside values"; k = 3.0 marks "far out" values. Winsorization retains the
observation in the sample (unlike trimming) and prevents outlier countries from compressing
the entire normalization range.

**Implementation in `asi/pipeline/goalposts.py` - `winsorize_bounds()`:**
- Applied per **scoring** indicator across the whole panel, after the log transform and
  before the goalpost min-max. Bounds are frozen into `registry/goalposts.yaml`, so one
  new outlier in a later edition cannot reshape every historical score
- `IQR_MULTIPLIER = 2.0` — **deliberately widened from Tukey's 1.5.** Rationale
  (`constants.py`): 1.5×IQR is calibrated for large samples; at n = 54 it clips too
  aggressively and compresses cross-country differentiation in the middle of the
  distribution. 2.0× still caps genuine outliers (e.g. Somalia, Mauritius) without
  truncating moderate variation. This is a deliberate, documented choice, not the Tukey
  default.
- Cap, do not delete: countries beyond the fence receive the fence value
- Logged in the `winsorisation` sheet: q1, q3, iqr, lower/upper bound, and cap counts
  (`n_capped_low`, `n_capped_high`) per indicator

---

### Spearman Rank Correlation (Pillar Diagnostics)

> Spearman, C.
> "The Proof and Measurement of Association between Two Things."
> *The American Journal of Psychology*, 15(1), 72–101, 1904.
> DOI: [10.2307/1412159](https://doi.org/10.2307/1412159)

Pairwise Spearman correlations between indicators within a pillar reveal redundancy
(very high ρ) and potential misclassification (very low or negative ρ). Computed after
normalisation and reported by `verify/advisory.py`, both within a pillar and across
pillars, at the reference year.

**Interpretation guideline (not from a single source — conventional):**
- ρ > 0.90: likely redundant pair; consider removing one indicator
- ρ < 0.30: indicators may not belong in the same pillar
- Negative ρ: check polarity coding before investigating further

---

## Data Sources

### World Development Indicators (WDI)

> World Bank.
> *World Development Indicators.*
> Washington, DC: World Bank Group, updated annually.
> Available: [https://databank.worldbank.org/source/world-development-indicators](https://databank.worldbank.org/source/world-development-indicators)
> API accessed via: `wbgapi` Python library, `db=2`

**Used for:** GDP per capita (PPP), GDP growth, inflation, Gini, education indicators,
health indicators, environmental indicators, infrastructure access, food insecurity,
homicide rate, displaced persons.

**Known limitations:**
- Survey-based indicators (Gini, enterprise surveys) have irregular update cycles and
  multi-year lags — some countries have no Gini observation since 2015.
- Sub-national data not available.
- Some social indicators (learning poverty, social protection coverage) have limited
  coverage in lower-income African states.

---

### Worldwide Governance Indicators (WGI)

> Kaufmann, D., Kraay, A., & Mastruzzi, M.
> "The Worldwide Governance Indicators: Methodology and Analytical Issues."
> *Hague Journal on the Rule of Law*, 3(2), 220–246, 2010.
> DOI: [10.1017/S1876404511200046](https://doi.org/10.1017/S1876404511200046)

> World Bank.
> *Worldwide Governance Indicators.*
> Washington, DC: World Bank Group, updated annually.
> Available: [https://www.govindicators.org](https://www.govindicators.org)
> API accessed via: `wbgapi` Python library, `db=3`

**Used for:** Six governance dimensions (va_estimate, pv_estimate, ge_estimate,
rq_estimate, rl_estimate, cc_estimate). Estimated score (`.EST`) used throughout,
not percentile rank (`.PER.RNK`), to avoid rank compression artifacts.

**Known limitations:**
- Derived from expert assessments and perception surveys, not direct measurement.
- High inter-correlation between the six WGI dimensions (a structural feature of the
  methodology, not an AII design flaw — acknowledged in Kaufmann et al. 2010).
- WGI is available biennially before 2002 and annually from 2002 onwards.

---

## Planned / Pending Sources (Stages 05–07)

### Robustness Analysis (Stage 05 — implemented)

> Saisana, M., Saltelli, A., & Tarantola, S.
> "Uncertainty and sensitivity analysis techniques as tools for the quality assessment
> of composite indicators."
> *Journal of the Royal Statistical Society: Series A*, 168(2), 307–323, 2005.
> DOI: [10.1111/j.1467-985X.2005.00359.x](https://doi.org/10.1111/j.1467-985X.2005.00359.x)

Grounds `03_robustness.py`: weight perturbation, measured-only rebuild and island-exclusion
sensitivity, and the MaxS adversarial worst-case weight search.

**MaxS implementation note:** the worst-case search uses a **random-restart grid search**
(7 deterministic pillar-corner weight vectors + 1000 Dirichlet samples within the
`[WEIGHT_MIN, WEIGHT_MAX]` bounds), *not* SLSQP. An earlier version used SLSQP, but the
objective — worst-case Spearman rank correlation — is a non-differentiable step function, on
which a gradient optimiser converges trivially to equal weights. The grid search was adopted
in July 2026 to actually explore the weight space. A full *joint* Monte Carlo over all
assumptions (imputation × winsorization × normalization × weighting) is scheduled as
ROADMAP Phase 3.

> Saltelli, A., Ratto, M., Andres, T., Campolongo, F., Cariboni, J., Gatelli, D.,
> Saisana, M., & Tarantola, S.
> *Global Sensitivity Analysis: The Primer.*
> John Wiley & Sons, 2008. ISBN: 978-0-470-05997-5.

**Not yet used.** This is the intended basis for a joint Monte Carlo over all assumptions
and for per-country rank intervals (backlog **B20**). Nothing in the pipeline implements it
today; `03_robustness.py` varies one assumption at a time. Listing it here under
"implemented" was itself part of the drift this revision corrects.

---

*Last updated: 2026-09-06 (documentation truth pass — Phase 0)*
*Last verified against code: 2026-09-06 (`asi/`, `verify/`, `01_pull.py`, `02_panel.py`, `03_robustness.py`)*
*Maintained by: Oscar Bailey*
*Any addition to the pipeline that introduces a new methodological choice must be
logged here before the change is committed. See `METHODOLOGY_REVIEW.md` for the full
OECD 10-step evaluation and `ROADMAP.md` for the phased refinement plan.*
