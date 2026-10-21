---
type: "project-page"
project: "African Stability Index"
section: "05 Verification"
status: "planned"
created: "2026-10-18"
updated: 2026-10-18
---

# BT7 Real-Time Replay

> [!abstract] Goal
> Measure how much the backtests owe to hindsight: rebuild past scores from the data as published at the time, and compare.

## Why it exists

Today's data include later revisions; an index used in 2015 would have seen the 2016 data, not today's.

## Precise objectives

1. Ingest the needed WDI archive vintages whole (P38).
2. Report the comparison and the rerun.

## Pre-registered design (v1, 2026-10-18)

- **Rebuild** a past year's scores from a WDI archive vintage of the following year, with that vintage's goalposts.
- **Compare** with today's scores for the same year: Spearman's rho and the largest rank movement.
- **Rerun BT1 and BT4** on the vintage scores where the vintage allows.

## Inputs and outputs

- **In:** WDI Database Archives (CC BY 4.0, terms read 2026-09-26)
- **Out:** AUC with its 95% interval, the difference against each baseline, the hit rate, and n; written into this note under Results

## Where it stands

Planned: the archive vintages are not yet ingested.

## Related

[ASI Backtest Protocol](<ASI Backtest Protocol.md>)
