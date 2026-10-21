---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: "2026-10-19"
---

# ASI Method Uncertainty and Rank Bands

> [!abstract] Goal
> Give every score an interval and group states into tiers whose differences the data can support.

## Why it exists

Rank bands at 2023 have a median width of 42 places: the data support a handful of tiers, not 54 ranks.

## Precise objectives

1. Every statistic carries its n (P46).
2. Intervals: a composite is M ± t(k−1)·SD/√k over its pillar scores; WGI items use the publisher's 90% interval.
3. Two states differ only if z = (M1 − M2)/√(SE1² + SE2²) exceeds 1.96 in absolute value.
4. A state's band runs from 1 + the number significantly above it to N − the number significantly below.
5. Tiers by the leader rule (P96): from the top, a tier holds every state not significantly below its first state;
   the first state significantly below starts the next. The point rank stays in the methodology.

**Evidence (2023, equal weights).** Pillar-spread SE: median band 42 places (13 to 54). Classical test theory with α .683: 44 places. Without Pillar F (α .908): 30 places.

**After P58.** Formative pillars make spread between pillars partly real, not error; the measurement-based error (WGI errors, data age, imputation, a Monte Carlo over method choices) becomes the target once built.

## Inputs and outputs

- **In:** pillar scores with their n
- **Out:** intervals, bands and tiers

## Where it stands

Built at edition 2, step 8 (athena-core #24). The headline's rows in `composites.csv` carry `se`, `ci_low`,
`ci_high`, `band_best`, `band_worst` and `tier`; `verify/panel.py` re-derives all of them (check 4.5).

- **At 2024:** the standard error has a median of 5.79 points (3.02 to 13.56), and the bands are a median of 42
  places wide (8 to 54).
- **Tiers:** four, of 18, 24, 10 and 2 states. Of the 26 years with ranks, 15 have three tiers and 11 have four.
- **The plan's overlap rule** would have put all 54 states in one tier at 2024, 2023 and 2015, since every band
  overlaps its neighbour's. Hence P96.

## Open questions

- Once the measurement-based error is built, does it replace the pillar spread? For now the spread stays, as
  ruled on 2026-10-17 and kept by P58.

## Related

ASI next edition plan (athena-data)
