---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# ASI Method Goalposts and Normalisation

> [!abstract] Goal
> Put every indicator on a 0–100 scale between fixed goalposts set from observed values or theoretical bounds, so scores are comparable across years.

## Why it exists

19 of edition 1's 32 goalposts rest on imputed extremes; moving goalposts would also re-anchor history every time an indicator is added.

## Precise objectives

1. Goalposts from observed values only, or theoretical bounds (0 to 100%) where they exist.
2. Cap outliers beyond 3 trimmed standard deviations first (the Ibrahim Index's rule).
3. Freeze a new indicator's goalposts without re-anchoring history (N1).

## Inputs and outputs

- **In:** observed values per indicator
- **Out:** goalposts per indicator, committed in the registry

## Where it stands

Built (edition 2, step 3, athena-core #14). Goalposts from observed values only; outliers beyond 3 trimmed SDs replaced at 3.1 (the IIAG's 2024 rule: trimmed mean and SD from the central 95%); theoretical bounds for 15 indicators; `--freeze-new-goalposts` for N1. Clamped values fell from 45 to 1. Composites moved 1.21 points on average; rank correlation .989.

## Related

ASI next edition plan (athena-data)
