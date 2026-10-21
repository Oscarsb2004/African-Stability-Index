---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# ASI Method Missing Data

> [!abstract] Goal
> Score only what was observed or recently observed, and make the missing visible instead of filling it with regional means.

## Why it exists

The states least able to report are the least stable, so data are not missing at random; regional means pull them towards their neighbours.

## Precise objectives

1. Stop scoring regional means.
2. Carry a value forward up to 5 years (INFORM's rule), then leave it missing.
3. A pillar scores on what is present, with its reliability tier.
4. Sensitivity check: rerun with missing values set to the regional 25th percentile.

**Evidence.** At 2023, of 1,728 cells: 254 regional means, 384 carried forward, 94 absent.

## Inputs and outputs

- **In:** the panel with provenance per cell
- **Out:** scores without imputation, with tiers and a sensitivity run

## Where it stands

Built (edition 2, step 2, athena-core #14). 9,936 panel cells now stay empty instead of being filled. At 2024 composites moved 1.93 points on average, at most 12.92 (South Sudan, which regional means had flattered); rank correlation .983. The sensitivity run (gaps at the region's 25th percentile, `--missing-at-regional-quantile 0.25`) moves them 1.75 on average, rank correlation .980.

## Related

ASI next edition plan (athena-data)
