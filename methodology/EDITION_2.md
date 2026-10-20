# Edition 2: the log

Edition 2 changes published scores, one step at a time, in the order the owner approved on 2026-10-17. The plan is
`ASI next edition plan.md` in athena-data. Each step records what it changed, what moved and why, with every number
taken from command output.

**The owner's rulings for this edition (2026-10-17):**
- **Stability follows Interpeace's *Rethinking Stability* (2022):** a positive, inclusive peace, built on the
  social, political and economic conditions people consider necessary for peace. Indicators are realigned to it in
  a later step.
- **The pillars measure stability.** The index is reflective, so rank bands use the spread of a country's pillar
  scores as the standard error.
- **GDP per capita stays scored.** Total GDP is added as a descriptive indicator.
- **Every other first position in the plan is approved.**

## Step 1 — current WDI and WGI as inputs; total GDP descriptive

**What changed**
- **Inputs:** the inputs come from `wdi-2026-10-08` and `wgi-2026-09-25` instead of the frozen pull of 8 August
  2026:

  ```
  python 01_inputs.py wdi-2026-10-08 wgi-2026-09-25
  ```

  `data/inputs.csv` holds 36,768 values: 34 series for 54 countries, 1995 to 2025.
- **Total GDP:** `gdp_total` (GDP, current US$, NY.GDP.MKTP.CD) joins Pillar B as a descriptive indicator. It is
  shown, never scored.
- **Method:** unchanged. The goalposts stay frozen at their 2026-08 values.
- **Window:** the pull window now runs to 2025 (`year_end` was 2024 in 27 registry entries). Seven indicators keep
  their 2023 end. The panel runs 2000 to 2025.

**What moved.** The method is unchanged, so every movement comes from the publishers' revisions.

At 2023, comparing the same year in both editions with equal weights:
- **Scores:** composites moved 0.26 points on average, at most 0.78 (GMB, +0.78).
- **Ranks:** rank correlation between editions is 0.997. No country moved 5 places or more; the largest move was 4
  (BDI, 36th to 40th).
- **Pillars,** mean absolute change in points: A 0.51 (WGI re-estimated its history), B 0.13, C 0.28, D 0.19, E 0.21,
  F 0.84, G 0.33.
- **Reliability improved.** Pillar F was reliable for 7 countries and is now reliable for 36, because the new WDI
  has 30 more observed 2023 values for electricity from fossil sources. Thirteen composites went from thin to
  reliable (BEN, BFA, CMR, COD, ETH, GHA, LBY, MOZ, NER, NGA, TCD, TGO, UGA). South Sudan went from unreliable to
  thin, so it now has a rank.

**The reference year moves from 2023 to 2024.** 2024 now has enough countries scoreable.

Against the published 2023 ranks:
- rank correlation is 0.983 over the 52 countries ranked in both;
- 4 countries moved 5 places or more, at most 8: AGO 43 to 35, COM 27 to 19, DZA 16 to 21, SWZ 22 to 29.

| | Top 5 | Bottom 5 |
| --- | --- | --- |
| Published (2023) | MUS, SYC, NAM, CPV, MAR | SDN, COD, CAF, TCD, SOM |
| Step 1 (2024) | MUS, SYC, CPV, NAM, MAR | COD, CAF, TCD, SSD, SOM |

**Clamped at the frozen goalposts:** 45 values in 10 indicators: agri_land 16, va_estimate 11, ge_estimate 5,
cc_estimate 3, rl_estimate 3, rq_estimate 2, sev_food_insec 2, displaced_persons 1, domestic_credit_private 1,
gdp_pc_ppp 1. Re-anchoring the goalposts is step 3.

**Checks**
- **Passing:** `verify.run` rebuild, panel and contract. Tests: 756 passed, 1 xfailed.
- **Narrative fails, as it should,** in the verification layer and in 4 tests. It finds 68 claims in the country
  texts that the new data contradicts. They
  were written against the 2023 data: counts of current indicators, which pillar is strongest, quoted values.
- **No new edition is published until the narratives are refreshed.** That happens once, after the method steps,
  because the pillars themselves will change.

**Fixed on the way**
- **Exact reading:** the verification layers read the panel CSVs with pandas' default parser, which misreads
  17-digit numbers such as total GDP's. They now read exactly.
- **The weighted-composite check (panel 4.1)** allows one unit in the last displayed decimal, but float subtraction
  made 46.24 − 46.23 exceed 0.01. Two scores on a rounding boundary failed it (SDN pca 2007, DZA entropy 2024). The
  tolerance now has a 1e-9 margin.

## Step 2 — the missing-data rule: a gap stays a gap (plan 4.5)

**What changed**
- **No regional fill.** Edition 1 filled a missing value with the mean of the same region's states that year. The
  states least able to report are the least stable, so data are not missing at random, and the mean flattered them.
  A value is now observed, or carried forward up to 5 years (as INFORM does, and as the panel already did), or
  missing. A pillar scores on the indicators present, and its reliability tier says how many those are.
- **In numbers:** 47,736 panel cells. 32,478 observed, 5,322 carried forward, and 9,936 left empty.
- **The sensitivity run the plan asks for:**

  ```
  python 02_panel.py --missing-at-regional-quantile 0.25 --out <scratch>
  ```

  It fills each gap with its region's 25th percentile that year. It fills 5,147 cells and writes elsewhere, so the
  published outputs are untouched. Those cells are marked `regional_quantile` and count as imputed.

**What moved** (2024, equal weights, step 1 against step 2)
- **Scores:** composites moved 1.93 points on average, at most 12.92 (SSD, −12.92).
- **Ranks:** rank correlation is 0.983 over the 53 states ranked in both. 5 moved 5 places or more:
  - COM 19 to 28;
  - GAB 25 to 17;
  - GIN 34 to 41;
  - SDN 48 to 53;
  - TZA 23 to 18.
- **Pillars,** mean absolute change in points: A 0.00, B 1.56, C 8.09, D 3.83, E 3.60, F 0.58, G 1.43. Pillar C
  moves most because its thin indicators (enrolment, learning poverty, femicide) were the most often filled.
- **Reliability:** composites were 19 reliable, 34 thin and 1 unreliable; now 18 reliable and 36 thin. No composite
  is now mostly imputed.
- **Top 5:** MUS, CPV, SYC, MAR, NAM. **Bottom 5:** TCD, CAF, SOM, SDN, SSD.

**The sensitivity** (step 2 against gaps at the regional 25th percentile)
- **Scores:** composites move 1.75 points on average, at most 11.98 (SSD, +11.98).
- **Ranks:** rank correlation is 0.980. 8 moved 5 places or more:
  - GIN 41 to 31;
  - GAB 17 to 25;
  - COM 28 to 21;
  - GNB 43 to 36;
  - CMR 36 to 42;
  - CIV 19 to 14;
  - ETH 35 to 40;
  - SDN 53 to 48.
- **Reading:** how a gap is treated moves a few states by several places. They are the states the tiers already
  mark thin, which is why the published view is tiers and bands (step 8), not point ranks.

**Checks**
- **Passing:** `verify.run` rebuild, panel and contract. Panel: 14 checks pass. 37,154 cells match the independent
  as-of join, and no regional-mean cell is left to skip.
- **Narrative still fails** in the verification layer and in 4 tests, as in step 1. It is refreshed once, after the
  method steps.
- **Tests:** 759 passed, 1 xfailed, besides those 4. Three new tests cover the quantile fill, the edition-1 mean
  fill as a negative control, and the published panel having no fill.

## Step 3: goalposts re-anchored on observed values, the IIAG's outlier rule, theoretical bounds (plan 4.4)

**What changed.** The goalposts are re-anchored once, deliberately, with `02_panel.py --freeze-goalposts`.
`registry/goalposts.yaml` moves to version 3. Three rules:
- **Observed values only.** A carried-forward value repeats a measurement and an imputed one guesses it, so neither
  sets a bound. In edition 1, 19 of 32 goalposts rested on imputed extremes.
- **Outliers are capped first, by the Ibrahim Index's rule.**
  - **The rule** (2024 IIAG methodology, "Outliers and treatment", read 2026-10-18):
    - the trimmed mean and standard deviation come from the central 95% of the values;
    - a value more than 3 of those standard deviations from the mean is replaced by the mean plus or minus 3.1 of
      them.
  - **It replaces edition 1's Tukey fences** at 2 IQR.
  - **Values replaced** (observed values beyond the threshold):
    - co2_pc 80;
    - domestic_credit_private 66;
    - gdp_growth_3yr_avg 61;
    - inflation_5yr_avg 59;
    - freshwater_withdraw 57;
    - hand_washing_facil 33;
    - primary_gpi 30;
    - mort_infant 19;
    - rq_estimate 15;
    - secondary_gpi 12;
    - cc_estimate 11;
    - life_expect_tot 9;
    - rl_estimate 8;
    - ge_estimate 6;
    - gini 3, primary_enroll 3, femicide 3;
    - youth_literacy 2, learning_poverty 2, social_protection_labour_pop 2;
    - pv_estimate 1, secondary_enroll 1.
- **Theoretical bounds where they exist.** 15 indicators take their possible extremes as goalposts, so a score means
  the same distance from the possible best and worst:
  - 0 to 100 for 13 percentages: agri_land, elec_access_tot, gini, hand_washing_facil, learning_poverty,
    managed_water_percent, nonrenew_elec, primary_enroll, secondary_enroll, sev_food_insec,
    social_protection_labour_pop, water_access_pop, youth_literacy;
  - 0 to 1 for the two parity distances.

  The registry carries them as `theoretical_bounds`.
- **New indicators (N1):** `02_panel.py --freeze-new-goalposts` adds goalposts for indicators the file lacks and
  leaves every existing one alone, so adding an indicator never re-anchors history.

**What moved** (2024, equal weights, against step 2)
- **Scores:** composites moved 1.21 points on average (+0.81 net), at most 3.74 (ERI, +3.74). The composite range
  is 21.92 to 80.98.
- **Ranks:** rank correlation is 0.989 over 54 states. 5 moved 5 places or more:
  - BFA 34 to 40;
  - DZA 20 to 14;
  - CIV 19 to 24;
  - COG 39 to 44;
  - ZWE 44 to 39.
- **Pillars,** mean change in points: A +1.27, B −2.60, C +4.09, D −5.32, E +0.35, F +5.54, G +2.20. Theoretical
  bounds lower scores where the observed range sat high in the scale (D's water and hygiene) and raise them where it
  sat low.
- **Clamping:** only 1 value now falls outside its goalposts (displaced_persons), against 45 under the old frozen
  goalposts.
- **Reliability:** unchanged, 18 reliable and 36 thin.
- **Top 5:** MUS, CPV, SYC, MAR, NAM. **Bottom 5:** LBY, CAF, SOM, SDN, SSD.

**Checks**
- **Passing:** `verify.run` rebuild, panel and contract.
- **Narrative fails** as before, until step 10.
- **Tests:** 762 passed and 1 xfailed, besides the 4 narrative tests.
  - **Replaced:** edition 1's test that recorded an imputed extreme. It is now a test that an imputed or carried
    value never sets a goalpost, with a negative control.
  - **New:** tests for theoretical bounds, the trimmed rule (with a negative control) and N1.

## Step 4: the log rule, a skew test and Osborne's constant (plan 4.6)

**What changed.** Edition 1 flagged 5 indicators for logs by hand and never applied a stated rule. The rule now
(the ADA course):
- **The test:** log an indicator when its skew is positive and significant, z = skew / SE(skew) above 1.96, with
  SE = sqrt(6n(n−1) / ((n−2)(n+1)(n+3))).
- **The sample:** one value per state, its most recent observation, so n is the number of states reporting (19 to
  54). Thousands of panel cells would make every skew "significant". The test runs after the outlier rule of step 3.
- **The transform:** log(x + c), where the frozen constant c makes the indicator's minimum 1 (Osborne). For an
  indicator with theoretical bounds the minimum is the bound, so its goalposts are log(1) and log(101).
- **The record:** the decision, skew, z, n and c are frozen in `registry/goalposts.yaml`. The registry's
  `log_transform` flags were set to match, and a test keeps them so.

**The decisions.** 12 indicators are logged now, against 5 in edition 1.
- **Logged:**
  - freshwater_withdraw, z 9.19;
  - co2_pc, 5.69;
  - displaced_persons, 5.43;
  - intent_homicide, 4.85;
  - domestic_credit_private, 4.66;
  - inflation_5yr_avg, 4.06;
  - hand_washing_facil, 3.80;
  - gdp_pc_ppp, 3.77;
  - social_protection_labour_pop, 3.64;
  - sev_food_insec, 3.30;
  - femicide, 2.50;
  - gini, 2.35.
- **No longer logged:** mort_infant (z 0.47).
- **Significantly left-skewed, so not logged:** primary_gpi (z −4.71), secondary_gpi (−3.79), primary_enroll
  (−3.30), youth_literacy (−2.73), learning_poverty (−2.10). Logging a left skew means reflecting the scale first.
  **The owner rules on whether to.**

**What moved** (2024, equal weights, against step 3)
- **Scores:** composites moved 1.57 points on average (+0.77 net), at most 3.90 (SDN, +3.90).
- **Ranks:** rank correlation 0.988 over 54 states. 3 moved 5 places or more:
  - EGY 19 to 25;
  - UGA 20 to 26;
  - KEN 16 to 21.
- **Pillars,** mean change in points: A 0.00, B +0.38, C −1.14, D +11.00, E −0.22, F −7.21, G +2.58. D rises as
  hand washing and severe food insecurity are logged. F falls as CO2 and freshwater withdrawal are.
- **Reliability:** unchanged.
- **Top 5:** MUS, CPV, SYC, RWA, NAM. **Bottom 5:** LBY, CAF, SOM, SDN, SSD.

**Checks**
- **Passing:** `verify.run` rebuild, panel and contract.
- **Narrative fails** as before, until step 10.
- **Tests:** 765 passed and 1 xfailed, besides the 4 narrative tests.
  - **New:** the skew test (a symmetric sample as negative control), Osborne's constant, and the registry's flags
    matching the frozen rule.
  - **Rewritten:** the test that carried a hand-set log flag through. The skew test decides now.

## Step 5: the admission floor (plan 2.1, 4.12)

**What changed.** An indicator is scored only if at least 33 of the 54 states have a real value for it at the
reference year: observed, or carried forward within 5 years. That is the Ibrahim Index's rule of at least 33 African
countries. Below the floor an indicator is descriptive: shown, not scored. `ADMISSION_FLOOR = 33` is in
`asi/core/constants.py`, and a test checks every scoring indicator against it, with a negative control.

**Below the floor at 2024** (states with a value), now descriptive:
- secondary_enroll 1;
- primary_enroll 2;
- femicide 16;
- social_protection_labour_pop 18;
- learning_poverty 19;
- intent_homicide 20;
- managed_water_percent 30;
- gini 30;
- secondary_gpi 30;
- displaced_persons 32.

The two enrolment series have almost no values in the 5 years up to 2024. 22 indicators remain scored.

**What moved** (2024, equal weights, against step 4)
- **Scores:** composites moved 1.75 points on average (+1.06 net), at most 6.20 (ZAF, +6.20).
- **Ranks:** rank correlation 0.981 over 54 states. 9 moved 5 places or more:
  - DZA 17 to 25;
  - DJI 19 to 26;
  - CIV 20 to 14;
  - KEN 21 to 15;
  - MWI 18 to 24;
  - ZAF 15 to 9;
  - MDG 32 to 27;
  - MLI 37 to 42;
  - NGA 44 to 39.
- **Reliability:** composites are now 29 reliable and 25 thin, against 18 and 36. The thin indicators no longer drag
  coverage down.
- **Pillars,** indicators each: A 6, B 4, C 3, D 4, E 2, F 4, G 4. Mean change: B +3.72, C +3.74, D +3.45,
  E −2.63, G −0.76.
- **The cost, stated plainly:**
  - Pillar C keeps 3 indicators and is unreliable for 47 states.
  - Pillar E is now the WGI's political stability and rule of law alone.

  The eight pillars of P57 rebuild both from new sources: UCDP for security, and education and cohesion data beyond
  the WDI.
- **Top 5:** CPV, MUS, SYC, NAM, BWA. **Bottom 5:** CAF, LBY, SOM, SDN, SSD.

**Checks**
- **Passing:** `verify.run` rebuild, panel and contract.
- **Narrative fails** as before, until step 10.
- **Tests:** 767 passed and 1 xfailed, besides the 4 narrative corpus tests.
  - **New:** two admission-floor tests.
  - **Fixed:** one narrative test assumed Kenya's Pillar D had an indicator not freshly measured. It no longer does,
    so the test now picks a case from the data.

## Step 6: the eight pillars (P57, variant B)

**What changed.** The seven pillars A to G are replaced by the eight of variant B of the layout test (P57). Each
indicator now has one home, and each falls under its pillar's umbrella (P58).
- **Keys** are short names, so a key can never be read as the old pillar it replaced. Edition 1's E was security;
  here SEC is. The order follows the vault's numbering, Pillar 1 to Pillar 8:
  - GOV, Governance and State Capacity;
  - VOI, Political Voice and Representation;
  - SEC, Security and Violence;
  - MAC, Macroeconomic and Fiscal Stability;
  - EXT, External Exposure and Economic Structure;
  - HUM, Human Development and Demography;
  - COH, Social Cohesion and Equity;
  - ENV, Environment and Climate Exposure.
- **The registry** is `indicators_list/pillar_<key>.yaml`, one file per pillar. It holds 69 indicators: 50 scored and
  19 descriptive.

| Pillar | Scored | Descriptive |
| --- | --- | --- |
| GOV | 6 | 1 |
| VOI | 2 | 0 |
| SEC | 2 | 4 |
| MAC | 7 | 0 |
| EXT | 8 | 1 |
| HUM | 16 | 6 |
| COH | 4 | 3 |
| ENV | 5 | 4 |

- **Variant B's 54 indicators, with the admission floor of step 5 applied.**
  - **Below the floor at 2024** (states with a value), so descriptive: homicide 20, conflict displacement 27, the
    stock of displaced people 32, and the Gini index 30.
  - **Battle-related deaths:** the WDI's series leaves 27 of 54 states blank. UCDP's deaths in organised violence
    take its place (below), so it is not carried.
  - **Tax revenue** is at the floor, with 33 states.
- **Security, from UCDP.** Without UCDP the pillar would hold political stability alone, since every WDI violence
  series falls below the floor.
  - **The indicator:** UCDP's country-year deaths in organised violence (dataset `ucdp-cy-26.1`, from athena-core
    #18), per 100,000 people.
  - **What it counts:** state-based, non-state and one-sided violence together. The column
    `cumulative_total_deaths_in_orgvio_best` equals their sum in every row.
  - **Why it passes the floor:** UCDP records every country-year, so a year without organised violence is a measured
    zero, not a gap. All 54 states have a value.
  - **South Sudan** is empty for 2000 to 2010, before it existed.
- **Indicators variant B leaves out stay descriptive.** They are shown, not scored:
  - regulatory quality (a near-duplicate of government effectiveness);
  - private credit;
  - infant mortality;
  - handwashing;
  - severe food insecurity;
  - primary gender parity;
  - CO2 per person;
  - freshwater withdrawal;
  - fossil electricity;
  - agricultural land.
- **Dropped:** primary and secondary enrolment and learning poverty, which have no value for any state since 2020.
- **Total GDP is scored** in EXT, as P50 asks.
- **Two transforms, declared in the registry and re-derived in `verify/panel.py`:**
  - **`per_capita: 100000`** divides a count by the same country-year's population. It replaces the code that
    converted only displaced people, per 1,000. Five indicators use it: organised-violence deaths, refugees hosted,
    disaster displacement, displaced people and conflict displacement. Population missing from the registry is now
    an error, not a skipped conversion.
  - **`aggregation: sd_recent_10`** is the sample standard deviation of the trailing ten years of a series, given
    only when at least five were measured. Growth volatility uses it. One series can now feed two variables: real
    growth is read both as its 3-year mean and as its volatility.
- **Theoretical bounds** follow step 3's rule for every new share of a whole or bounded scale. That makes 15 in all:
  - basic_sanitation, elec_access_tot, forest_area, fuel_exports, internet_users, ore_metal_exports,
    slum_population, stunting, undernourishment, water_access_pop, women_in_parliament, youth_literacy and
    youth_share, 0 to 100;
  - statistical_performance, 0 to 100;
  - cpia_property_rights, 1 to 6.
- **Goalposts** are frozen again for all 50 scored indicators, since the set changed.
- **The log rule (step 4)** logs 23 of them, and the registry's flags were set to match. Three are significantly
  left-skewed and not logged: female_male_labour (z −3.95), youth_share (−2.91) and youth_literacy (−2.73). That
  joins the open ruling on left skew.
- **Weight presets:** edition 1's three presets beyond equal weights weighted the seven pillars, and no stage read
  them, so they are removed. Step 8 sets any others.
- **`MIN_PILLARS_FOR_COMPOSITE`** stays 5, now of 8. Steps 7 and 8 revisit it.
- **Inputs:** `python 01_inputs.py wdi-2026-10-08 wgi-2026-09-25 ucdp-cy-26.1` gives 83,801 values, 68 series, 54
  countries, 1995 to 2025.

**What moved** (2024, equal weights, against step 5)
- **Scores:** composites moved 5.24 points on average (−4.07 net), at most 14.41 (RWA, −14.41).
- **Ranks:** rank correlation 0.936 over 54 states. 18 moved 5 places or more:
  - COM 29 to 14;
  - GNQ 49 to 34;
  - GNB 40 to 30;
  - SLE 31 to 21;
  - LBY 51 to 42;
  - ZWE 44 to 35;
  - LBR 30 to 24;
  - EGY 28 to 23;
  - MRT 33 to 38;
  - TGO 23 to 28;
  - MLI 42 to 47;
  - DJI 26 to 31;
  - ETH 37 to 44;
  - BFA 38 to 46;
  - ZMB 19 to 27;
  - KEN 15 to 25;
  - UGA 22 to 33;
  - RWA 6 to 17.
- **Reliability:** composites are 33 reliable and 21 thin, against 29 and 25.
- **Top 5:** SYC, MUS, CPV, BWA, NAM. **Bottom 5:** TCD, CAF, SOM, SDN, SSD.
- **Pillars at 2024:**

| Pillar | Indicators | Mean score | Reliable | Thin | Unreliable |
| --- | --- | --- | --- | --- | --- |
| GOV | 6 | 48.18 | 54 | 0 | 0 |
| VOI | 2 | 36.15 | 50 | 4 | 0 |
| SEC | 2 | 68.01 | 54 | 0 | 0 |
| MAC | 7 | 47.81 | 49 | 3 | 1 |
| EXT | 8 | 55.46 | 29 | 14 | 9 |
| HUM | 16 | 60.09 | 52 | 2 | 0 |
| COH | 4 | 53.95 | 50 | 3 | 1 |
| ENV | 5 | 57.25 | 0 | 0 | 54 |

- **The cost, stated plainly:**
  - **ENV is unreliable for all 54 states at 2024.** Four of its five series end in 2021 to 2023, so at the
    reference year four values are carried forward, and the imputed share passes the 0.50 limit. Step 7 (unreliable
    pillars) decides what that means; the data are not wrong.
  - **MAC is negatively correlated with every other pillar** (−.07 to −.34 at 2024), and PCA gives it no weight
    (0.0). Steady prices, low debt and reserves do not move with governance or development across these states.
    Step 8 weighs that.
  - **SEC has two indicators.** Homicide and displacement return when sources clear the floor (UNODC, IDMC direct).

**The layout test, rerun on edition 2's panel** (objective 5 of the pillar note; scores at 2024, not the prototype's
ranks)
- **Between-pillar overlap:** mean |rho| .383, largest GOV–VOI .80. The prototype gave .320 and .64.
- **Corrected for attenuation:** the advisory layer finds seven pairs above |.90|, every one involving COH or ENV:
  COH–ENV +2.71, COH–SEC +1.58, ENV–SEC +1.19, ENV–GOV +1.12, COH–HUM +1.11, ENV–MAC −0.99 and COH–GOV +0.95.
  Those two pillars are formative (their items are separate causes, P58), so their alpha is not a reliability and a
  corrected r above 1 says the reflective model does not fit them. It does not say they measure one thing.
- **Factor analysis:** parallel analysis keeps one factor, as scored (eigenvalues 3.93, 1.19, 0.80) and with log GDP
  per capita held constant (3.25, 1.38, 0.92).

**Robustness** (`03_robustness.py`, 2024)
- **Weighting methods agree:** rho .9843 for PCA, .9782 for entropy and .9909 for geometric.
- **Worst in-bounds weighting:** rho .9076.
- **Measured cells only:** rho .8981.
- **Least stable quintiles:** SLE 41%, UGA 42%, LSO 47%, DZA 49%, GNQ 53%.

**Checks**
- **Passing:** `verify.run` rebuild, panel and contract. Panel: 15 checks pass, two of them new:
  - 1.6 now re-derives every per-capita indicator: 5,850 cells of 5 indicators;
  - 1.7 re-derives growth volatility with pandas' rolling standard deviation: 1,404 cells.

  78,234 cells match the as-of join.
- **Narrative fails** as before, until step 10. The narrative checker's phrase "displaced persons" now names its
  series in full, since three series begin "Internally displaced persons".
- **Tests:** 767 passed and 1 xfailed. The same 4 narrative corpus tests fail as at step 5, confirmed on a clean
  checkout of step 5.
  - **New:** four tests, for per capita (an error without population, with a negative control; each indicator's own
    scale) and for volatility (the window, with a negative control).
  - **Moved to the new keys:** the dashboard, narrative and consistency tests that named edition 1's letters.

## Step 7: unreliable pillars leave the composite (plan 4.1)

**What changed.**
- **Exclusion:** a pillar whose tier is unreliable no longer enters any composite (equal, PCA, entropy or
  geometric). The pillars that remain are averaged, with their weights renormalised.
  - Edition 1 averaged such pillars in at full weight, so cells the interface greys out still moved the headline.
  - `score.composite_inputs` leaves them out.
  - The data-driven weights are fitted on the same inputs.
- **Each composite row now reports:**
  - **k (`n_pillars`):** the number of pillars it used;
  - **`lack_of_reliability`:** an INFORM-style index from 0 (reliable) to 10, computed as
    LRI = 10 × (gap + age) / 2 over the scoring indicators, where:
    - gap is the share not measured that year (absent, carried forward or imputed);
    - age is the mean age of the values present, as a share of the 5-year carry-forward limit (1 when nothing is
      present).

  INFORM builds its index from missing and imputed data and from the data's age. Those are its components that
  apply to a national index; its subnational component does not.
- **Composite reliability is unchanged:** a composite still needs `MIN_PILLARS_FOR_COMPOSITE` = 5 displayable pillars.
- **`03_robustness.py`** starts from the same inputs.

**What moved** (2024, equal weights, against step 6)
- **Left out:** 358 unreliable pillar-years in all, over every year. By pillar: ENV 138, EXT 65, GOV 55, HUM 54,
  MAC 26, COH 15, VOI 5. At 2024 ENV is left out for all 54 states.
- **Scores:** composites moved 1.40 points on average (−0.68 net), at most 4.03 (CAF, −4.03).
- **Ranks:** rank correlation 0.983. 7 moved 5 places or more:
  - DZA 22 to 15;
  - DJI 31 to 25;
  - EGY 23 to 17;
  - UGA 33 to 28;
  - SLE 21 to 26;
  - LBR 24 to 31;
  - COM 14 to 22.
- **k at 2024:** 42 states use 7 pillars, 10 use 6 and 2 use 5.
- **Lack of reliability at 2024:** median 1.69, from 1.19 (UGA) to 3.93 (ERI).
- **Reliability:** composites stay 33 reliable and 21 thin.
- **Top 5:** CPV, MUS, SYC, BWA, ZAF. **Bottom 5:** TCD, CAF, SOM, SDN, SSD.

**For the owner.** ENV is left out at 2024 for every state, and at 2023 for 11.
- **Why:** four of its five series end in 2021 to 2023, so their latest values are carried forward. The tier rule
  counts a carried value as imputed, and an imputed share above 0.50 makes a pillar unreliable.
- **What it is not:** the data are not wrong. They are published with a lag.
- **The choice:**
  - keep the rule, so the headline at the latest year has no environment pillar;
  - or count a value carried forward within its publisher's usual lag as current for the tier.

  That is a ruling, not something to tune until ENV comes back.

**Checks**
- **Passing:** `verify.run` rebuild, panel and contract.
  - **4.1 and 4.3** now re-derive the composites from reliable and thin pillars only. They filter the long table,
    where the pipeline masks the wide one.
  - **4.4 (new)** re-derives k and the index for all 5,616 composite rows with numpy, from the written formula.
- **Narrative fails** as before, until step 10.
- **Robustness:** weighting methods agree at rho .9848 (PCA), .9838 (entropy) and .9877 (geometric). The worst
  in-bounds weighting gives .9067, and measured cells only give .8507.
- **Tests:** 769 passed and 1 xfailed, besides the same 4 narrative corpus tests. **New:** two, each with a negative
  control: an unreliable pillar is left out while a thin one is kept, and the index follows its formula.

## Step 8: the headline, its interval, rank bands and tiers (plan 2.2, 2.3, 4.7, 4.8, 4.10)

**The owner's rulings for this step (2026-10-19):**
- **Tiers follow the leader rule (P96).** The plan's rule, "countries whose bands overlap form a tier", chained all
  54 states into one tier at 2024, 2023 and 2015: with bands a median of 42 places wide, every band overlaps its
  neighbour's.
- **ENV stays out at 2024 (P97).** A value carried forward counts as imputed for the tier, as at step 7, so the 2024
  headline has no environment pillar.

**What changed.** No score moves. The rebuild layer finds every output identical to a fresh run, and the old columns
of `composites.csv` are unchanged.
- **One headline, declared:** the equal-weight arithmetic mean of the pillars that entered (`HEADLINE_METHOD`).
  - The geometric mean is the sensitivity check, and PCA and entropy are diagnostics only.
  - `bundle.json` names each method's role.
- **An interval for every headline:** M ± t(k − 1) × SD/√k over its k pillars, at 95%. It is in `se`, `ci_low` and
  `ci_high`, for the 1,404 headline rows with two or more pillars.
- **A rank band** among the states ranked that year, in `band_best` and `band_worst`.
  - Two states differ when |M₁ − M₂| / √(SE₁² + SE₂²) > 1.96.
  - A band runs from 1 + the states significantly above to N − those significantly below.
  - The point rank stays, for the methodology.
- **A tier** by the leader rule, in `tier`. From the top, a tier holds every state not significantly below its first
  state; the first state significantly below starts the next.
- **Effective weights** (plan 4.10) are in `bundle.json`:
  - **nominal:** each pillar 1/P, each indicator 1/n of its pillar;
  - **as used at the reference year:** the pillars that entered each state's headline, over their contributing
    indicators, averaged over the 54 ranked states.
- **The standard error** is the spread of a state's pillar scores, as ruled on 2026-10-17 and kept by P58. Where a
  pillar is formative, part of that spread is real, so the bands err wide.

**What it shows** (2024)
- **Standard error:** median 5.79 points, from 3.02 (CMR) to 13.56 (ERI). The 95% half-width has a median of 14.16,
  from 7.39 to 37.65.
- **Bands:** median 42 places wide, from 8 (SSD) to 54 (ERI).
- **Four tiers:**
  - **Tier 1 (18 states, 72.6 to 57.2):** CPV, MUS, SYC, BWA, ZAF, NAM, MAR, GHA, LSO, TUN, SEN, STP, GMB, RWA, DZA,
    GAB, EGY, SWZ.
  - **Tier 2 (24 states, 57.1 to 46.2):** CIV, BEN, TZA, COM, KEN, MWI, DJI, SLE, TGO, UGA, MDG, ZMB, LBR, GIN, GNB,
    MRT, GNQ, ZWE, AGO, LBY, CMR, NGA, COG, ERI.
  - **Tier 3 (10 states, 45.8 to 32.8):** MOZ, ETH, BDI, BFA, NER, MLI, COD, TCD, CAF, SOM.
  - **Tier 4 (2 states, 29.2 to 26.2):** SDN, SSD.
- **Every year:** of the 26 years with ranks (2000 to 2025), 15 have three tiers and 11 have four.
- **Effective weights, nominal:** from 0.0078 (adolescent_fertility, 0.39× an even share of 1/50) to 0.0625
  (organised_violence_deaths, 3.12×).
  - Every indicator of a two-indicator pillar (VOI, SEC) carries 3.12×.
  - Each of HUM's 16 carries 0.39×.
  - Pillars weigh equally, so a small pillar's members weigh most. That is why the aggregation note asks pillars to
    grow together.
- **Effective weights, as used at 2024:** largest va_estimate 0.0760, pv_estimate 0.0747, organised_violence_deaths
  0.0747 and women_in_parliament 0.0734. With ENV left out, its five series weigh 0.
- **The WGI's share of the headline:** 18.7% nominal and 23.6% as used at 2024, against edition 1's 28.9%.

**Checks**
- **Passing:** `verify.run` rebuild, panel, contract and advisory. Panel adds two checks:
  - **4.5** re-derives all 1,404 intervals, from the sum of squares and scipy's `stdtrit`, and the 1,378 bands and
    tiers, pair by pair with plain loops where the pipeline uses a matrix. It also checks that no other method
    carries an interval, band or tier.
  - **4.6** re-derives the 50 nominal weights from the registry's YAML, and checks that both published sets sum
    to 1.
- **Tests:** 284 passed, against 279 on main after the P3 trims. **New:** five, each with a negative control:
  - the interval's formula, and none for one pillar;
  - a band counting only significant states;
  - the leader rule where overlapping bands would chain (and one tier when the errors are wide);
  - nominal, cross-listed and realised weights;
  - the verifier catching a wrong tier and a wrong interval.

**Not in this step:** showing tiers, bands and intervals on the site. The site still reads edition 1's frozen panel.
It shows them when edition 2 publishes, with the regenerated `stability.json`.

## Step 9: the realignment to Interpeace's definition (plan 1.1, 1.2)

**What changed.** The plan names what the definition adds that the index lacked:
- the protection of civilians;
- horizontal cohesion between communities;
- the inclusion of women and youth;
- the social contract.

Women in parliament and tax revenue were already scored at step 6. This step adds the rest from data already in
Athena. Trust in institutions (Afrobarometer) and section 6's expanded list wait for edition 3.
- **Organised violence is scored by its three parts.** UCDP's dataset `ucdp-cy-26.1` carries each, per 100,000
  people, and a test checks that the three sum to the total in every country-year:
  - **`state_based_deaths`** (SEC): armed conflict with a government as one side.
  - **`one_sided_deaths`** (SEC): civilians killed deliberately, the protection of civilians.
  - **`non_state_deaths`** (COH): fighting between organised groups, the plan's communal violence.
  - **`organised_violence_deaths`,** their sum, becomes descriptive, so no death counts twice.
- **`youth_unemployment`** (COH) is descriptive. The candidate screen of 2026-10-18 found the direction of measured
  unemployment contradicted in Africa: it is higher in the richer states, where informal work is rarer.
- **The registry:** 73 indicators, 52 scored and 21 descriptive.
  - **SEC:** 3 scored, 5 descriptive.
  - **COH:** 5 scored, 4 descriptive.
- **Inputs:** `python 01_inputs.py wdi-2026-10-08 wgi-2026-09-25 ucdp-cy-26.1` gives 90,413 values, 72 series and 54
  countries, from 1995 to 2025.
- **Goalposts:**
  - **N1:** frozen for the three new indicators only (`--freeze-new-goalposts`), so every existing indicator keeps
    its own and history is not re-anchored.
  - **The log rule** logs all three: skew z 7.43 (state-based), 6.97 (one-sided) and 6.20 (non-state), n 54,
    constant 1.0.
  - **The outlier rule** caps 80, 90 and 80 of their 1,393 values at the high end.

**What moved** (2024, equal weights, against step 8)
- **Scores:** composites moved 2.00 points on average (+1.92 net), at most 6.24 (SSD, +6.24).
- **Ranks:** rank correlation 0.997 over 54 states. One state moved 5 places or more: LBY, 38 to 33.
- **Pillars:**
  - **SEC:** mean 68.01 to 73.86; it moved 6.70 points on average, at most 37.39 (SSD).
  - **COH:** mean 53.95 to 61.00; it moved 7.90 on average, at most 13.85 (MRT).
  - **COH's tiers:** 53 reliable and 1 thin, against 50, 3 and 1 unreliable.
  - **Across all years,** 343 unreliable pillar-years are left out, against 358.
- **k at 2024:** 43 states use 7 pillars, 9 use 6 and 2 use 5.
- **Reliability:** composites stay 33 reliable and 21 thin.
- **Top 5:** CPV, MUS, SYC, BWA, ZAF. **Bottom 5:** MLI, SOM, CAF, SSD, SDN. SSD is no longer last: much of its
  violence is non-state, which now counts in COH.
- **Bands and tiers:**
  - **Standard error:** median 6.46, against 5.79.
  - **Bands:** median 44 places wide, from 14 to 54.
  - **Tiers:** 19, 23, 11 and 1 states, against 18, 24, 10 and 2.
- **Violence's share of the headline:**
  - **Nominal:** 10.83%, against 6.25% for the total at step 8.
  - **As used at 2024:** 12.96%, against 7.47%.

**Why the scores rise.** Each part is zero in more states than the total, and a measured zero scores 100.
- **At 2024 the total is zero in 25 states.** State-based deaths are zero in 31, one-sided deaths in 32 and
  non-state deaths in 39.
- **A state free of one kind of violence scores 100 on that part,** even where another kind is severe.
- **So splitting one series into three raises SEC and COH for most states,** and the headline with them.

**For the owner.** Splitting is the plan's position (the candidate screen marked all three parts "Ingest"). Three
questions remain for you to rule on:
- **Is the rise from three mostly zero series acceptable?** The alternatives:
  - score only the total, plus one-sided deaths on its own (the protection of civilians), which counts those deaths
    twice;
  - or score the total in SEC and non-state deaths in COH, which counts communal violence twice.
- **Does non-state violence belong in COH** (horizontal cohesion), or in SEC with the other two?
- **Are the outlier caps right for these zero-heavy series?** They put about 6% of values at the cap. The outlier
  rule was set for continuous series.

**Checks**
- **Passing:** `verify.run` rebuild, panel, contract and advisory.
  - **1.6** re-derives 10,062 per-capita cells of 8 indicators.
  - **4.6** re-derives 52 nominal weights.
- **Robustness:**
  - **Weighting methods agree:** rho .9881 (PCA), .9851 (entropy) and .9867 (geometric).
  - **The worst in-bounds weighting** gives .8962, against .9067 at step 8, and the verdict moves from "robust" to
    "moderately sensitive".
  - **Measured cells only:** .8549.
- **Tests:** 286 passed. **New:** two:
  - the three parts sum to the total in every country-year, with a negative control: two parts fall short;
  - the parts are scored and the total is not.
