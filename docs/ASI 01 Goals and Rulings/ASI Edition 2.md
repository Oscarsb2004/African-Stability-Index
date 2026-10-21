---
type: "project-page"
project: "African Stability Index"
section: "01 Goals and Rulings"
status: "designed"
created: "2026-10-18"
updated: "2026-10-20"
---

# ASI Edition 2

> [!abstract] Goal
> Publish the next edition on current data and corrected methods, each step reported with what it moved and why.

## Why it exists

The experts' feedback and the plan's method issues change scores; doing them one at a time keeps every movement explainable.

## Precise objectives

1. Step 1: inputs from the current WDI and WGI (built, draft athena-core #14).
2. Step 2: [ASI Method Missing Data](<../ASI 04 Methods/ASI Method Missing Data.md>).
3. Step 3: [ASI Method Goalposts and Normalisation](<../ASI 04 Methods/ASI Method Goalposts and Normalisation.md>).
4. Step 4: [ASI Method Transformations](<../ASI 04 Methods/ASI Method Transformations.md>).
5. Step 5: [ASI Method Indicator Admission](<../ASI 04 Methods/ASI Method Indicator Admission.md>).
6. Step 6: the new pillar layout ([ASI Pillars](<../ASI 04 Methods/ASI Pillars.md>), P57), replacing the old steps for Pillar F and WGI de-duplication.
7. Step 7: [ASI Method Reliability Tiers](<../ASI 04 Methods/ASI Method Reliability Tiers.md>) (unreliable pillars).
8. Step 8: [ASI Method Aggregation and Weights](<../ASI 04 Methods/ASI Method Aggregation and Weights.md>) and [ASI Method Uncertainty and Rank Bands](<../ASI 04 Methods/ASI Method Uncertainty and Rank Bands.md>) (headline, tiers and bands).
9. Step 9: realignment to Interpeace's definition, starting with a UCDP adapter.
10. Step 10: the narrative refresh, once, before publication.
11. Before publication: the backtests rerun on the new panel ([ASI Backtests](<../ASI 05 Verification/Backtests/ASI Backtests.md>)).

## Inputs and outputs

- **In:** `wdi-2026-10-08`, `wgi-2026-09-25`, later UCDP
- **Out:** edition 2 scores, tiers and bands; `methodology/EDITION_2.md`

## Where it stands

Steps 1 to 7 are built and merged, each logged in `methodology/EDITION_2.md`:
- current inputs; no regional fill; goalposts on observed values; the log rule; the admission floor;
- the eight pillars of P57, with UCDP for security;
- unreliable pillars leave the composite.

69 indicators, 50 scored. ENV stays out at 2024 for every state (P97).

**Step 8 is built in athena-core #24, and no score moves:**
- the declared headline;
- an interval for every headline;
- rank bands, and tiers by the leader rule (P96);
- the effective weights.

At 2024 the bands are a median of 42 places wide, and the 54 states form four tiers of 18, 24, 10 and 2.

**Step 9 is built in athena-core #25, with the owner's rulings P98 to P100.** It is the realignment to Interpeace's definition:
- organised violence is scored by its UCDP parts, state-based and one-sided in SEC and non-state in COH;
- youth unemployment is shown.

Outliers in the zero-heavy UCDP series are tested against the other violent years (P100). At 2024 the composites moved
2.72 points on average (+2.72 net), with rank correlation 0.997. How to remove overlapping indicators (P98) is settled by P101,
below.

**Since step 9:**
- **Overlapping indicators share a weight** (P101, athena-core #29): 6 clusters of 15 indicators; composites moved
  0.83 points on average.
- **Step 10, part A, the data narratives,** is built (athena-core #28): seven sentences per state, every number
  re-derived by a gating check.
- **Part B, context,** is left to the project, for after Athena is built; its instructions are [ASI Context Brief](<../ASI 08 Status and Roadmap/ASI Context Brief.md>).
  Part C, recent events, is skipped (P102).

**The backtests are rerun on edition 2's panel** ([ASI Backtests](<../ASI 05 Verification/Backtests/ASI Backtests.md>), v2), with the pillar mapping stated before the run.
- **BT1 conflict onset:** .743 (edition 1: .697); informative, but not yet adding to development.
- **BT6:** every expectation held.

**Next:** edition 2 on the site (tiers, bands and the data narratives), then publication, which is the owner's.

## Related

ASI next edition plan (athena-data) · [ASI Edition 1](<ASI Edition 1.md>)
