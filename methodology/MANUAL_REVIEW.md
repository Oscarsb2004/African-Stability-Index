# Manual Review Queue

**Living document.** Items a human must judge — machines can flag these, but not
decide them. Nothing here is a bug report; each is a decision the index needs a
person to make.

Assume issues exist. Verification passing does not mean these are settled: the
verifiers check that the arithmetic is faithful, not that the choices are right.

Status key: `[ ]` open · `[x]` reviewed and accepted · `[!]` reviewed, change needed

*Last updated: 2026-08-08 (Phase B)*

---

## Tier 1 — affects published scores

### [ ] 1. Goalposts anchored on imputed values (19 of 32 indicators)

**Why it matters:** goalposts are frozen permanently. An extreme set by a
regional-mean estimate rather than a real measurement fixes the scale for that
indicator for every country and every year, forever. This is the single highest-
leverage review item in the project.

Flagged automatically during freezing (`min_from_imputed` / `max_from_imputed` in
`registry/goalposts.yaml`):

| Indicator | min | max | imputed at |
|---|---:|---:|---|
| gini | 27.600 | 60.200 | **MIN + MAX** |
| intent_homicide | 0.237 | 3.791 | **MIN + MAX** |
| learning_poverty | 44.088 | 98.607 | **MIN + MAX** |
| social_protection_labour_pop | 0.514 | 62.566 | **MIN + MAX** |
| agri_land | 3.261 | 86.476 | MAX |
| domestic_credit_private | 0.383 | 50.115 | MAX |
| femicide | 0.133 | 7.338 | MAX |
| freshwater_withdraw | 0.020 | 63.434 | MAX |
| hand_washing_facil | 0.000 | 74.938 | MAX |
| inflation_5yr_avg | -5.180 | 24.934 | MAX |
| nonrenew_elec | 0.000 | 100.000 | MAX |
| primary_enroll | 26.828 | 99.099 | MAX |
| secondary_enroll | 3.280 | 80.359 | MAX |
| gdp_growth_3yr_avg | -4.420 | 12.548 | MIN |
| primary_gpi | 0.705 | 1.000 | MIN |
| rq_estimate | -2.581 | 1.130 | MIN |
| secondary_gpi | 0.358 | 1.000 | MIN |
| sev_food_insec | 1.281 | 4.196 | MIN |
| youth_literacy | 23.640 | 100.000 | MIN |

The four **MIN + MAX** rows are the priority: both ends of the scale rest on
inference. `gini` and `learning_poverty` are the worst cases, since both are also
sparse indicators.

**Decision needed per indicator:** accept the imputed bound, substitute a
theoretical bound (e.g. GPI parity is 1.0 by definition; literacy is 0–100 by
definition), or restrict the goalpost to observed values only.

*Note: `primary_gpi` / `secondary_gpi` max of exactly 1.000 is correct by
construction — the parity transform caps at 1.0. Only their MIN needs review.*

### [ ] 2. REC membership vs your spreadsheet

`asi/core/countries.py` already carries all 8 AU-recognised communities.
Counts to check: **ECOWAS 12, COMESA 21, CEN-SAD 25, SADC 16, ECCAS 10, EAC 8,
IGAD 6, UMA 5.** ECOWAS at 12 suggests the 2025 Sahel withdrawals are already
reflected — confirm. Also confirm EAC (Somalia and DRC joined recently).

Second question: membership is currently time-invariant, but the time slider
spans 2000–2024 and REC membership changed within that window. Decide whether to
model membership by year or label the control "current membership".

### [ ] 3. Polarity, all 32 indicators

Priority cases: `co2_pc` (correlates −0.91 with GDP per capita — behaves as an
inverted wealth proxy), `agri_land` (positive polarity is argued in the YAML but
contested), `nonrenew_elec` (rewards hydro dependence that Pillar G penalises).

The GPI indicators are resolved as of Phase B (`distance_from_parity`).

### [ ] 4. Log-transform flags

Five indicators are flagged. Seven unflagged ones have comparable skew. The
explicit rule ("log1p iff skew > 1 and min >= 0") has **not** yet been applied —
current flags are inherited. Transform order is now correct (log before
winsorize), so re-deriving the flags is a clean follow-up.

### [ ] 5. Reliability thresholds

Currently `reliable >= 0.60`, `thin >= 0.40`, imputed share > 0.50 vetoes.
Yields 7,043 reliable / 1,225 thin / 1,182 unreliable pillar-years.
Spot-check five countries where a pillar flips to greyed and judge whether the
call is defensible. These three numbers decide what the public sees as a score
versus a grey box.

---

## Tier 2 — Phase B findings needing a judgement call

### [ ] 6. 2001 is 37/54 unreliable (WGI biennial gap)

WGI has no 2001 observation, so Pillar A is carried forward and the composite
degrades. This is honest, but it will show as a visible notch in the time slider.
Decide: leave the notch, suppress 2001 entirely, or annotate it in the UI.

### [ ] 7. Reference year is 2023, panel ends 2024

2024 is 54/54 unreliable because World Bank series report with a lag. The
dashboard opens on 2023. Confirm that is the desired behaviour, and decide what
2024 should look like — greyed, or hidden until it fills in.

### [ ] 8. Pre-independence country-years

South Sudan's pre-2011 years currently come out `unreliable` and unranked, which
produces the right display behaviour by accident rather than by design. Consider
an explicit `panel_start` per country (South Sudan 2011, Eritrea 1993) so the
reason is stated rather than inferred from coverage.

### [ ] 9a. Some countries' ranks swing wildly with the weighting method

From `03_robustness.py` at 2023. The index is *robust* overall (worst-case
Spearman 0.928 across all admissible weightings), but individual countries are
not:

| Country | Rank range across methods |
|---|---|
| Algeria | 9 – 45 |
| Libya | 16 – 52 |
| Mauritania | 21 – 42 |
| Egypt | 6 – 27 |
| Guinea | 13 – 40 |

These are all North African / Sahelian hydrocarbon economies, which is the
signature of item 9 below: entropy gives Pillar F the highest weight while PCA
gives it zero, and oil producers score badly on the environmental indicators. A
reader who picks a different weighting sees Algeria as either top-10 or
bottom-10. Decide whether to surface this uncertainty in the interface (a rank
range rather than a point rank) or resolve it by fixing Pillar F.

### [ ] 9. PCA and entropy disagree sharply on Pillar F

PCA assigns Pillar F weight **0.000**; entropy assigns it the **highest** weight
(0.204). Both are defensible on their own terms and they cannot both be right
about what Pillar F contributes. Feeds directly into the Pillar F redesign.

### [ ] 10. Scores compressed by fixed goalposts

Bottom-end scores rose (SOM 34.3 in 2023 vs 28.2 under the old sample-relative
scoring) because goalposts now span 24 years of history, so present-day values
sit less extreme. This is expected and correct, but it changes how the index
reads. Confirm the interpretation is acceptable before publishing.

---

### [ ] 11. Five indicators were not directly measured anywhere in 2023

From `verify/advisory.py`. At the reference year these carry 0% observed data —
every value is carried forward or estimated from regional peers:

`freshwater_withdraw` · `secondary_gpi` · `primary_enroll` ·
`social_protection_labour_pop` · `secondary_enroll`

Overall the reference year is 57.6% directly measured, 22.2% carried forward,
14.7% regional estimate, 5.4% absent. The five above are the extreme case:
they contribute to scores every year while never being observed in the year
shown. Decide whether carry-forward remains acceptable for them, or whether
they should be restricted to the years they were actually collected.

---

## Tier 3 — structural, lower urgency

- [ ] **Cross-listing effective weights.** Cross-listed WGI indicators carry
  1.68–1.90× a median indicator; Pillar C members carry 0.57×.
- [ ] **Aggregation windows per indicator** — only 2 of 33 use a rolling mean;
  confirm `most_recent` is right for the rest in a panel context.
- [ ] **WGI concentration** — 6 of 32 indicators supply ~29% of composite weight.
- [ ] **Display precision** — 2 decimals accepted (2026-08-08). Consequence:
  countries can display an identical score and rank one apart (e.g. MOZ/ETH
  entropy 44.31). `verify/contract.py` reports these as WARN.

---

## Tier 4 — narrative layer (opens at Phase D)

Not yet actionable; listed so they are not forgotten.

- [ ] Every citation in the first 9 countries: URL resolves **and** supports the claim
- [ ] Framing balance in the first 9 — read for negativity skew
- [ ] Event flags (coup/election dates) against an independent source
- [ ] `context/colonial_history.yaml` — 1,188 lines, never audited
- [ ] Per-pillar AI summaries vs the actual indicator values
