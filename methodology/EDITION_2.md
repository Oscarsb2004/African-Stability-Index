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
