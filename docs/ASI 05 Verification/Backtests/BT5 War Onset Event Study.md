---
type: "project-page"
project: "African Stability Index"
section: "05 Verification"
status: "built"
created: "2026-10-18"
updated: "2026-10-20"
---

# BT5 War Onset Event Study

> [!abstract] Goal
> Show where each state stood on the ASI in the years before it entered war.

## Why it exists

Averages can hide the cases people remember; an event study shows them one by one.

## Precise objectives

1. List every event with its trajectory.
2. Report both readings with n.

## Pre-registered design (v1, 2026-10-18)

- **Events, by rule, not chosen by hand:** state-years where battle deaths reach 1,000 (UCDP's threshold for war)
  after at least three years below it, from 2003 to 2024.
- **For each:** the state's percentile among the 54 on the composite at t−3, t−2, t−1 and t, and its change from
  t−3 to t−1.
- **Reading, stated now:** the share of events with the state in the bottom fifth at t−1 (chance 20%), and the
  median change from t−3 to t−1.

## Results (v1, run 2026-10-18)

**16 war onsets by the rule.** The percentile is the state's place among the 54 on the composite (100 = most
stable).

| State | Year | t−3 | t−2 | t−1 | t |
| --- | --- | --- | --- | --- | --- |
| LBR | 2003 | 9.3 | 11.1 | 7.4 | 5.6 |
| UGA | 2004 | 50.9 | 53.7 | 51.9 | 64.8 |
| TCD | 2006 | 7.4 | 5.6 | 5.6 | 3.7 |
| SOM | 2007 | 1.9 | 1.9 | 1.9 | 1.9 |
| COD | 2009 | 5.6 | 5.6 | 5.6 | 7.4 |
| SDN | 2010 | 27.8 | 13.0 | 11.1 | 11.1 |
| LBY | 2011 | 68.5 | 63.0 | 48.1 | 27.8 |
| COD | 2013 | 5.6 | 7.4 | 7.4 | 9.3 |
| NGA | 2013 | 25.9 | 33.3 | 31.5 | 27.8 |
| SSD | 2014 | 3.7 | 3.7 | 1.9 | 1.9 |
| LBY | 2016 | 53.7 | 31.5 | 24.1 | 20.4 |
| COD | 2017 | 9.3 | 11.1 | 11.1 | 11.1 |
| ETH | 2020 | 40.7 | 46.3 | 46.3 | 42.6 |
| BFA | 2022 | 55.6 | 55.6 | 55.6 | 44.4 |
| MLI | 2022 | 39.8 | 40.7 | 38.9 | 33.3 |
| SDN | 2023 | 16.7 | 14.8 | 14.8 | 13.0 |

**Readings, as pre-registered:** 9 of 16 events (56%) had the state in the bottom fifth at t−1, against 20% by
chance. The median change from t−3 to t−1 is −0.45 percentile points: no fall on average before a war.

**Reading.** Most war onsets were renewed wars in states already at the bottom. New wars (Uganda 2004, Libya 2011,
Nigeria 2013, Ethiopia 2020, Burkina Faso 2022, Mali 2022) began in mid-table states. Libya's place fell sharply in
the three years before 2011; the others' did not.

## Results (v2, edition 2, run 2026-10-20)

The same design on edition 2's panel, with the pillar mapping stated before the run ([ASI Backtest Protocol](<ASI Backtest Protocol.md>); athena-data e6e9b22). Edition 1's results are above.

**War onsets by rule:** 16. At t−1, 68.75% (11 of 16) were in the ASI's bottom fifth (edition 1: 56.25%, 9 of 16); the median change from t−3 to t−1 was -0.9 percentile points.

| State | Onset | t−3 | t−2 | t−1 | t |
| --- | --- | --- | --- | --- | --- |
| BFA | 2022 | 38.9 | 34.3 | 37.0 | 24.1 |
| COD | 2009 | 9.3 | 9.3 | 11.1 | 7.4 |
| COD | 2013 | 9.3 | 11.1 | 9.3 | 11.1 |
| COD | 2017 | 11.1 | 13.0 | 11.1 | 9.3 |
| ETH | 2020 | 27.8 | 27.8 | 27.8 | 14.8 |
| LBR | 2003 | 18.5 | 13.0 | 7.4 | 3.7 |
| LBY | 2011 | 44.4 | 37.0 | 25.9 | 9.3 |
| LBY | 2016 | 27.8 | 13.0 | 9.3 | 7.4 |
| MLI | 2022 | 24.1 | 24.1 | 24.1 | 13.0 |
| NGA | 2013 | 24.1 | 29.6 | 25.9 | 25.9 |
| SDN | 2010 | 7.4 | 5.6 | 3.7 | 5.6 |
| SDN | 2023 | 5.6 | 3.7 | 5.6 | 1.9 |
| SOM | 2007 | 3.7 | 3.7 | 5.6 | 3.7 |
| SSD | 2014 | 3.7 | 5.6 | 1.9 | 1.9 |
| TCD | 2006 | 14.8 | 11.1 | 5.6 | 1.9 |
| UGA | 2004 | 27.8 | 22.2 | 18.5 | 27.8 |

Percentile ranks of the ASI among the 54 states (0 is the lowest score).

## Inputs and outputs

- **In:** the panel; VC.BTL.DETH
- **Out:** AUC with its 95% interval, the difference against each baseline, the hit rate, and n; written into this note under Results

## Where it stands

Run on 2026-10-18 on edition 1's panel, with the WDI's copies of the outcome data (athena-core `projects/asi/06_backtests.py`; results in `data/backtests.json`). The design above was committed before the run (athena-data 90fb6a8).

## Related

[Pillar 3 Security and Violence](<../../ASI 04 Methods/Pillar 3 Security and Violence.md>) · [ASI Backtest Protocol](<ASI Backtest Protocol.md>)
