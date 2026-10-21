---
type: "project-page"
project: "African Stability Index"
section: "01 Goals and Rulings"
status: "live"
created: "2026-10-18"
updated: 2026-10-18
---

# ASI Edition 1

> [!abstract] Goal
> Keep the published edition reproducible, exactly, as the baseline every change is measured from.

## Why it exists

It is the edition people have seen; every later change must say how far it moves these scores.

## Precise objectives

1. All seven committed outputs rebuild identically from `asi-pull-2026-08-08` (the rebuild layer).
2. The legacy site stays live until the new atlas reaches parity (P44, P59).

## What it is

- **Inputs:** the ASI's own pull of 8 August 2026: 33 WDI and WGI series, frozen as a workbook.
- **Panel:** 2000–2024, reference year 2023, 54 states.
- **Seven pillars:** A Political / Governance, B Economic, C Social / Human Capital, D Health, E Security / Conflict,
  F Environmental, G Structural / Infrastructure. 32 scoring indicators and one descriptive (population).
- **Four weighting methods:** equal, PCA, entropy, geometric; equal weights are the headline the atlas shows.
- **Known weaknesses** (the plan's section 4): WGI counted six times and cross-listed (28.9% of the weight);
  regional-mean imputation; goalposts on imputed extremes; Pillar F measuring wealth; 54 point ranks without
  intervals.

## Inputs and outputs

- **In:** `asi-pull-2026-08-08`
- **Out:** `data/panel/*` in athena-core's `projects/asi`; the legacy Dash site

## Where it stands

Live. Reproduced exactly from Athena (athena-core #13).

## Related

[ASI Edition 2](<ASI Edition 2.md>) · [ASI Verification Layers](<../ASI 05 Verification/ASI Verification Layers.md>)
