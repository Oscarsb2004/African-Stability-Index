---
type: "project-page"
project: "African Stability Index"
section: "05 Verification"
status: "built"
created: "2026-10-18"
updated: "2026-10-20"
---

# BT4 Monetary Crises

> [!abstract] Goal
> Test whether a low ASI score precedes inflation crises and currency crashes.

## Why it exists

Monetary crises are the economic face of instability; they test the economic content of the index the way conflict tests its security content.

## Precise objectives

1. Report each crisis type separately.
2. Report the AUC, both pass rules and the hit rate.

## Pre-registered design (v1, 2026-10-18)

- **Events (Reinhart and Rogoff 2011, *American Economic Review* 101: 1676–1706, Figure 1 notes):**
  - an **inflation crisis**: consumer price inflation above 20% in a year (FP.CPI.TOTL.ZG);
  - a **currency crash**: a depreciation of 15% or more against the US dollar in a year (PA.NUS.FCRF, local
    currency per dollar).
- **At risk:** state-years t from 2000 to 2021 free of the event at t.
- **Predictor:** the composite at t; Pillar B in edition 1, Pillar 4 in edition 2.
- **Baselines:** log GDP per capita; the event in t−5 to t−1; inflation at t (for inflation crises).
- **Note:** 14 states use the CFA franc, pegged to the euro, so their crashes against the dollar follow the
  euro.

## Results (v1, run 2026-10-18)

**Inflation crises** (1,017 state-years, 81 events, 52 states):

| Predictor | AUC | 95% interval | Minus log GDP per capita |
| --- | --- | --- | --- |
| ASI composite | .574 | .448–.704 | +.002 (−.142 to .162) |
| Pillar B (edition 1) | .622 | .501–.744 | +.056 (−.109 to .211) |
| Log GDP per capita | .552 | .418–.685 | — |
| A crisis in t−5 to t−1 | .612 | .556–.672 | +.051 (−.086 to .193) |
| Inflation at t | .748 | .660–.830 | +.220 (.092 to .358) |

Hit rate: 19 of 81 (23.5%). Horizons: t+1 alone, .590 (35 events); t+1 to t+5, .564 (107 events).

**Currency crashes** (957 state-years, 242 events, 54 states):

| Predictor | AUC | 95% interval | Minus log GDP per capita |
| --- | --- | --- | --- |
| ASI composite | .496 | .419–.573 | −.014 (−.082 to .053) |
| Pillar B (edition 1) | .565 | .488–.633 | +.046 (−.015 to .105) |
| Log GDP per capita | .512 | .438–.583 | — |
| A crash in t−5 to t−1 | .486 | .421–.544 | −.034 (−.120 to .051) |

Hit rate: 50 of 242 (20.7%). Horizons: t+1 alone, .499; t+1 to t+5, .485.

**Verdict:** not informative for either.

**Reading.** The composite carries no signal on monetary crises. This year's inflation is by far the best guide to
an inflation crisis in the next three years. Edition 1's economic pillar does slightly better than the composite;
edition 2's Pillar 4 is where this is tested again.

## Results (v2, edition 2, run 2026-10-20)

The same design on edition 2's panel, with the pillar mapping stated before the run ([ASI Backtest Protocol](<ASI Backtest Protocol.md>); athena-data e6e9b22). Edition 1's results are above.

**n:** 1017 state-years, 81 events, 52 states.

| Predictor | AUC | 95% interval | Minus log GDP per capita |
| --- | --- | --- | --- |
| ASI composite | .626 | .494–.759 | +.053 (−.093 to .206) |
| MAC pillar | .749 | .667–.825 | +.203 (.025 to .381) |
| Log GDP per capita | .552 | .418–.685 | — |
| The event in t−5 to t−1 | .612 | .556–.672 | +.051 (−.086 to .193) |
| Inflation at t | .748 | .660–.830 | +.220 (.092 to .358) |

**Hit rate:** 29 of 81 events (35.8%) came from states in the bottom fifth at t; chance is 20%.

**Verdict:** informative, no. Adds to development, no.

**Currency crashes:**

| Predictor | AUC | 95% interval | Minus log GDP per capita |
| --- | --- | --- | --- |
| ASI composite | .493 | .417–.568 | −.017 (−.090 to .057) |
| MAC pillar | .560 | .503–.615 | +.044 (−.040 to .135) |
| Log GDP per capita | .512 | .438–.583 | — |
| The event in t−5 to t−1 | .486 | .421–.544 | −.034 (−.120 to .051) |

**Hit rate:** 47 of 242 events (19.4%) came from states in the bottom fifth at t; chance is 20%.

**Verdict:** informative, no. Adds to development, no.

**Horizons:** inflation, t+1 alone, .638 (.506–.771; 35 events); inflation, t+1 to t+5, .624 (.491–.758; 107 events); currency, t+1 alone, .497 (.425–.567; 98 events); currency, t+1 to t+5, .474 (.383–.561; 341 events).

**Reading.** The headline does not predict inflation crises, but its MAC pillar does, and adds to income per head: averaging MAC with seven other pillars loses the signal. Nothing here predicts currency crashes.

## Inputs and outputs

- **In:** the panel; FP.CPI.TOTL.ZG; PA.NUS.FCRF; NY.GDP.PCAP.PP.KD
- **Out:** AUC with its 95% interval, the difference against each baseline, the hit rate, and n; written into this note under Results

## Where it stands

Run on 2026-10-18 on edition 1's panel, with the WDI's copies of the outcome data (athena-core `projects/asi/06_backtests.py`; results in `data/backtests.json`). The design above was committed before the run (athena-data 90fb6a8).

## Related

[Pillar 4 Macroeconomic and Fiscal Stability](<../../ASI 04 Methods/Pillar 4 Macroeconomic and Fiscal Stability.md>) · [ASI Backtest Protocol](<ASI Backtest Protocol.md>)
