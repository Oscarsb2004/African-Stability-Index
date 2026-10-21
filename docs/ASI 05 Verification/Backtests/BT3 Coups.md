---
type: "project-page"
project: "African Stability Index"
section: "05 Verification"
status: "blocked"
created: "2026-10-18"
updated: 2026-10-18
---

# BT3 Coups

> [!abstract] Goal
> Test whether a low ASI score, and low governance and voice, precede coup attempts.

## Why it exists

Africa's 2020–2023 coup wave (Mali, Guinea, Sudan, Burkina Faso, Niger, Gabon) is the most visible instability of the period; an index of stability should not have been blind to it.

## Precise objectives

1. Read and date the dataset's terms before use.
2. Then run as designed.

## Pre-registered design (v1, 2026-10-18)

- **Event:** a successful or failed coup attempt, from Powell and Thyne's global dataset of coups.
- **At risk:** state-years t from 2000 to 2021 with no attempt at t.
- **Predictor:** the composite at t; Pillar A in edition 1, Pillars 1 and 2 in edition 2.
- **Baselines:** log GDP per capita; an attempt in t−5 to t−1.

## Inputs and outputs

- **In:** Powell and Thyne's coup dataset (terms not yet read)
- **Out:** AUC with its 95% interval, the difference against each baseline, the hit rate, and n; written into this note under Results

## Where it stands

Blocked: the coup dataset's terms are not yet read.

## Open questions

- If its terms do not allow use, is there another published coup list?

## Related

[ASI Backtest Protocol](<ASI Backtest Protocol.md>)
