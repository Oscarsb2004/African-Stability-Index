---
type: "project-page"
project: "African Stability Index"
section: "05 Verification"
status: "built"
created: "2026-10-18"
updated: "2026-10-20"
---

# BT2 Conflict Displacement

> [!abstract] Goal
> Test whether a low ASI score precedes new displacement by conflict in a state that had none.

## Why it exists

Displacement is how conflict reaches civilians at scale; Interpeace puts the protection of civilians at the centre.

## Precise objectives

1. Report the AUC and both pass rules.
2. Report n: the window is short, so intervals will be wide.

## Pre-registered design (v1, 2026-10-18)

- **Event:** any new internal displacement by conflict recorded by IDMC (VC.IDP.NWCV), 31 states, 2009–2023.
- **At risk:** state-years t from 2009 to 2020 with none recorded at t (missing read as none; IDMC directly later).
- **Predictor:** the composite at t; the variant without Pillar E (which holds displaced persons).
- **Baselines:** log GDP per capita; displacement in t−5 to t−1.

## Results (v1, run 2026-10-18)

**n:** 469 state-years, 88 events, 49 states.

| Predictor | AUC | 95% interval | Minus log GDP per capita |
| --- | --- | --- | --- |
| ASI composite | .575 | .458–.693 | −.050 (−.191 to .101) |
| ASI without Pillar E | .595 | .479–.711 | −.031 (−.167 to .118) |
| Log GDP per capita | .639 | .517–.756 | — |
| Displacement in t−5 to t−1 | .613 | .562–.663 | −.024 (−.146 to .102) |

**Hit rate:** 7 of 88 events (8.0%) came from the bottom fifth, below the 20% of chance.

**Verdict:** not informative.

**Reading.** New displacement by conflict mostly begins in middle-ranked states, not in the ones the ASI places at
the bottom. The window is short (2009–2023), so the intervals are wide.

## Results (v2, edition 2, run 2026-10-20)

The same design on edition 2's panel, with the pillar mapping stated before the run ([ASI Backtest Protocol](<ASI Backtest Protocol.md>); athena-data e6e9b22). Edition 1's results are above.

**n:** 469 state-years, 88 events, 49 states.

| Predictor | AUC | 95% interval | Minus log GDP per capita |
| --- | --- | --- | --- |
| ASI composite | .643 | .526–.762 | +.019 (−.130 to .186) |
| ASI without SEC | .617 | .498–.738 | −.004 (−.151 to .161) |
| Log GDP per capita | .639 | .517–.756 | — |
| The event in t−5 to t−1 | .613 | .562–.663 | −.024 (−.146 to .102) |

**Hit rate:** 10 of 88 events (11.4%) came from states in the bottom fifth at t; chance is 20%.

**Verdict:** informative, yes. Adds to development, no.

**Reading.** Informative now (edition 1 was not), but no better than income per head.

## Inputs and outputs

- **In:** the panel; VC.IDP.NWCV; NY.GDP.PCAP.PP.KD
- **Out:** AUC with its 95% interval, the difference against each baseline, the hit rate, and n; written into this note under Results

## Where it stands

Run on 2026-10-18 on edition 1's panel, with the WDI's copies of the outcome data (athena-core `projects/asi/06_backtests.py`; results in `data/backtests.json`). The design above was committed before the run (athena-data 90fb6a8).

## Related

[ASI Backtest Protocol](<ASI Backtest Protocol.md>)
