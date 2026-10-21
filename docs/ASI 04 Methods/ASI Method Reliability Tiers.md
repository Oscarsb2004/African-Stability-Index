---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# ASI Method Reliability Tiers

> [!abstract] Goal
> Say beside every score how far it can be trusted, from its coverage, the age of its data and its imputation.

## Why it exists

A score built on old or filled-in data should not look as solid as one built on this year's observations.

## Precise objectives

1. Every pillar and composite carries a tier: reliable, thin or unreliable.
2. An INFORM-style lack-of-reliability index is published beside each score.
3. Unreliable pillars leave the composite ([ASI Method Aggregation and Weights](<ASI Method Aggregation and Weights.md>)).

**Evidence.** 61 unreliable pillar cells at 2023 count at full weight in edition 1.

## Inputs and outputs

- **In:** provenance per cell
- **Out:** a tier and reliability index per score

## Where it stands

Built (edition 2, step 7, athena-core #14). An unreliable pillar leaves every composite; each composite row reports k (pillars used) and an INFORM-style lack-of-reliability index, 0 to 10: 10 x (gap + age) / 2 over the scoring indicators. 358 pillar-years are left out over the panel; at 2024 ENV for all 54 states. Composites moved 1.40 points on average; rank correlation .983. At 2024 the index runs from 1.19 (UGA) to 3.93 (ERI), median 1.69.

## Open questions

- A value carried forward within its publisher's usual lag counts as imputed, so ENV is left out at the latest year: keep the rule, or count publication lag as current? The owner's ruling.

## Related

ASI next edition plan (athena-data)
