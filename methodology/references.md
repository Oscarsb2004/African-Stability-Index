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
| Min-max normalization to [0, 100] | §6.1 | `03_normalize.py` — `normalize_indicator()` |
| Log transformation before normalization for skewed distributions | §6.2 | `03_normalize.py` — `log_transform: true` indicators (e.g. GDP per capita, homicide rate) |
| Polarity inversion at normalization step | §5.3 | `03_normalize.py` — negative polarity inverts formula to `(max-x)/(max-min)*100` |
| IQR Winsorization to handle outliers (cap, do not delete) | §5.2 | `02_clean.py` — `IQR_MULTIPLIER = 2.0` (widened from Tukey's 1.5; see Winsorization section) |
| Three-stage imputation hierarchy before leaving NaN | §5.4 | `02_clean.py` — Stage1: 5yr lookback; Stage2: regional mean; Stage3: NaN |
| Equal weights as the default / reference case | §7.1 | `04_score.py` — `score_equal()` |
| PCA-derived weights as a data-driven alternative | §7.3 | `04_score.py` — `score_pca()` |
| Sensitivity analysis / robustness testing across methods | §8 | `05_robustness.py` (implemented: weight perturbation, MaxS adversarial search, fill/island exclusion) |
| Transparency: all weights, bounds, and intermediate values published | throughout | All pipeline outputs include bounds sheets and fill logs |

**Known deviations:**
- The Handbook recommends z-score normalization as an alternative to min-max. We use min-max
  because it produces scores in a fixed [0, 100] range that is more interpretable for a
  public-facing index. Z-scores can exceed these bounds and are harder to communicate.
- The Handbook treats the Benefit of Doubt (BoD) method as exploratory. We implement it as a
  first-class scoring method because the ASI user (a researcher) understands its interpretation.

---

## Scoring Methods

### Benefit of Doubt (BoD) Composite Indicator

> Cherchye, L., Moesen, W., Rogge, N., & Van Puyenbroeck, T.
> "An Introduction to 'Benefit of the Doubt' Composite Indicators."
> *Social Indicators Research*, 82(1), 111–145, 2007.
> DOI: [10.1007/s11205-006-9029-7](https://doi.org/10.1007/s11205-006-9029-7)

BoD is a restricted Data Envelopment Analysis (DEA-CCR) formulation that awards each
country the weight vector that maximises its own composite score, subject to global
weight bounds. This gives each country the "benefit of the doubt" regarding its own
strengths.

**Implementation in `04_score.py` — `score_bod()`:**
- Formulation: LP per country, maximise `sum(w_i * s_i)` subject to:
  - `sum(w_i) = 1` — over that country's **valid (non-NaN) pillars only**
  - `WEIGHT_MIN <= w_i <= WEIGHT_MAX` per valid pillar (bounds: 0.05 to 0.25)
  - `sum(w_i * s_j_i) <= 1` for all other countries j (no country can exceed score 1.0),
    restricted to pillars where both countries have data
- Solver: PuLP CBC (open-source LP solver)
- Pillar scores normalised to [0, 1] before LP; results rescaled back to [0, 100]
- **Feasibility fallback:** a country with fewer than 4 valid pillars cannot reach
  `sum(w_i) = 1` under `WEIGHT_MAX = 0.25`, so its score falls back to the equal-weight
  mean of its valid pillars. Restricting the sum-to-1 constraint to valid pillars (rather
  than including missing ones) was a July 2026 correction: the prior formulation forced
  `WEIGHT_MIN` to be "spent" on each missing pillar, artificially capping achievable scores.

**Known deviation from source:**
- The original Cherchye et al. (2007) formulation uses no explicit upper weight bounds.
  We add per-pillar `WEIGHT_MAX = 0.25` to prevent degenerate solutions where one pillar
  receives near-100% weight. This follows the restricted BoD extension discussed in:
  > Rogge, N. (2018). "Composite Indicators as Generalized Benefit-of-the-Doubt Weighted
  > Averages." *European Journal of Operational Research*, 267(1), 381–392.

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

**Implementation in `04_score.py` — `score_geometric()`:**
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

**Implementation in `04_score.py` — `score_entropy()`:**
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

**Implementation in `04_score.py` — `score_pca()`:**
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
(Nunnally, 1978; George & Mallery, 2003). The pipeline gates more leniently at
`MIN_CRONBACH_ALPHA = 0.60` (`constants.py`) — warning, not halting — because it currently
computes alpha on **raw, mixed-polarity values**, which mechanically deflates alpha for
pillars containing negative-polarity indicators. Correcting this to run on polarity-aligned
normalized scores is scheduled as ROADMAP Phase 3; until then the 0.60 warnings for pillars
B/C/D/E/F are expected artifacts, not verdicts on construct validity.

**Implementation in `02_clean.py` — `cronbach_alpha()`:**
- Computed per pillar on the cleaned (pre-winsorisation) values
- Requires at least k ≥ 2 indicators and n ≥ 3 complete country observations
- Logged in the `diagnostics` sheet of `02_clean.xlsx`
- Values below `MIN_CRONBACH_ALPHA` (0.60) are flagged for review of pillar composition

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

**Implementation in `02_clean.py`:**
- Applied per **scoring** indicator across all countries after aggregation and filling
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
cleaning for each pillar and written to the `spearman_*` sheets in `02_clean.xlsx`.

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

Grounds `05_robustness.py`: weight perturbation, fill-exclusion and island-exclusion
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

Will be used for the sensitivity band methodology (Monte Carlo weight perturbation).

---

*Last updated: 2026-07-14 (Roadmap Phase 0 — documentation truth pass)*
*Last verified against code: 2026-07-14 (constants.py, 02_clean.py, 04_score.py, 05_robustness.py)*
*Maintained by: Oscar Bailey*
*Any addition to the pipeline that introduces a new methodological choice must be
logged here before the change is committed. See `METHODOLOGY_REVIEW.md` for the full
OECD 10-step evaluation and `ROADMAP.md` for the phased refinement plan.*
