---
type: "project-page"
project: "African Stability Index"
section: "05 Verification"
status: "live"
created: "2026-10-18"
updated: 2026-10-18
---

# ASI Backtest Protocol

> [!abstract] Goal
> Fix the rules every backtest follows, so no result can be improved by choosing how to measure it after the fact.

## Why it exists

With 54 states and a few hundred events, a flexible analysis can find a signal in noise. Fixed rules make a reported AUC mean what it says.

## Precise objectives

1. **Panel:** the ASI's published panel, equal weights, 2000–2024, 54 states (`data/panel/composites.csv`, `pillar_scores.csv`).
2. **Unit:** a state in year t. **Horizon:** an event in t+1 to t+3; t+1 alone and t+1 to t+5 as sensitivity.
3. **At risk:** a state is scored only in years when it is free of the event at t.
4. **Orientation:** a lower score means higher predicted risk.
5. **Metric:** ROC AUC, with a 95% interval from 2,000 bootstrap resamples of states (clustered by state), seed 20261018.
6. **Baselines:** (1) log GDP per capita, PPP, constant prices (NY.GDP.PCAP.PP.KD); (2) recent history: the event in any of t−5 to t−1; (3) for conflict tests, the WGI political stability estimate.
7. **Hit rate:** the share of events whose state was in the bottom fifth of ASI scores in year t; chance is 20%.
8. **Pass rules, stated now:** the ASI is *informative* if its AUC interval lies above .50; it *adds to development* if the interval of its AUC minus the GDP baseline's lies above 0.
9. **Leakage:** scores at t use data up to t only (carry-forward looks back; regional means use the same year). Goalposts are fixed over 2000–2024, a mild look-ahead that [BT7 Real-Time Replay](<BT7 Real-Time Replay.md>) measures.
10. **Reporting:** n of state-years, events and states with every figure; every variant reported.

## Inputs and outputs

- **In:** the panel; outcomes from WDI until their publishers' datasets are ingested
- **Out:** the rules the backtests cite

## Where it stands

Live: applied in the v1 run of 2026-10-18. Details fixed in the code before the run: each predictor is scored on the rows where it has a value; a non-event needs every window year observed; displacement before 2009 counts as none, since IDMC's series starts then.

## The v2 rerun on edition 2's panel (stated 2026-10-20, before the run)

Edition 2 replaces edition 1's seven lettered pillars with eight (P57). The tests, the windows, the baselines, the
pass rules and the outcomes (the WDI's copies, as in v1) stay as they are, so only the panel changes. The
pre-registered words map to the new pillars by meaning:
- **"The ASI without its security pillar"** (BT1, BT2) is the ASI without **SEC**.
- **"The economic pillar"** as a predictor (BT4) is **MAC**, Macroeconomic and Fiscal Stability. Its indicators
  (inflation, growth, debt, reserves, the current account) are the macro-financial half of edition 1's B.
- **BT6's expectations:**
  - for conflict, "the security and political pillars": **SEC**, and **GOV** and **VOI**, the two halves of edition
    1's political pillar;
  - for monetary crises, "the economic pillar": **MAC**. EXT, the external half of edition 1's B, is reported but not
    expected.
- **Leakage:** edition 2's SEC holds UCDP's state-based and one-sided deaths, the same events behind the conflict
  outcome. A state is at risk only in years free of conflict, when its state-based deaths are a measured zero, so SEC
  at t carries no outcome. The ASI without SEC is reported beside it, as in v1.
- **Edition 1's results** stay in `data/backtests_edition1.json`, and v2's are written to `data/backtests.json`.

## Related

[ASI Method Uncertainty and Rank Bands](<../../ASI 04 Methods/ASI Method Uncertainty and Rank Bands.md>)
