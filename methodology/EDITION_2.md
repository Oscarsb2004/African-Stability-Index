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
