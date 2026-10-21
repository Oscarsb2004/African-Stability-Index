---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: "2026-10-20"
---

# ASI Method Aggregation and Weights

> [!abstract] Goal
> Combine indicators into pillars and pillars into the composite by one declared headline rule, and publish the effective weight every indicator ends up with.

## Why it exists

Edition 1 computed four composites without declaring one, and hid that the WGI carried 28.9% of the weight.

## Precise objectives

1. Headline: equal-weight arithmetic mean of the pillars.
2. Sensitivity: the geometric mean (INFORM's); PCA and entropy as diagnostics only, since PCA weights follow the development axis.
3. Unreliable pillars leave the composite, which averages the rest and reports k.
4. Effective weights are published.
5. Pillars grow together: adding one indicator to a four-indicator pillar cuts each existing one's influence by 20%.

## Inputs and outputs

- **In:** pillar scores
- **Out:** the composite, its sensitivity variants, effective weights

## Where it stands

Built at edition 2, steps 7 and 8 (athena-core #24 for step 8).

- **The headline is declared:** the equal-weight mean of the pillars that entered. The geometric mean is the
  sensitivity check, and PCA and entropy are diagnostics; `bundle.json` names each method's role.
- **Effective weights are published** in `bundle.json`, nominal and as used at the reference year; `verify/panel.py`
  re-derives the nominal ones (check 4.6).
  - **Nominal:** from 0.39× an even share (each of HUM's 16 indicators) to 3.12× (each member of the
    two-indicator pillars, VOI and SEC).
  - **As used at 2024:** largest va_estimate 0.0760, pv_estimate 0.0747, organised_violence_deaths 0.0747; ENV's
    five series weigh 0 (P97).
  - **The WGI's share:** 18.7% nominal and 23.6% as used at 2024, against edition 1's 28.9%.
- **Overlapping indicators share a weight (P101; athena-core #29).** Within a pillar, a pair whose partial correlation
  holding log GDP per capita is at least .71 shares one slot, and chains form clusters.
  - **At 2024:** 6 clusters of 15 indicators, among them GOV's three WGI items with CPIA property rights, and
    state-based with one-sided deaths.
  - **The WGI's share** falls to 15.6% nominal and 20.0% as used.
  - **Composites** moved 0.83 points on average, with rank correlation 0.994.

## Related

ASI next edition plan (athena-data)
