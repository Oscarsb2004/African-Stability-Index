---
type: "project-page"
project: "African Stability Index"
section: "05 Verification"
status: "built"
created: "2026-10-18"
updated: "2026-10-20"
---

# BT6 Pillar Attribution

> [!abstract] Goal
> Find which pillars carry the predictive signal for each kind of event.

## Why it exists

A composite can predict for the wrong reason; attribution shows whether the security content predicts conflict and the economic content predicts monetary crises, as it should.

## Precise objectives

1. Report every pillar's AUC for every event type, with intervals.
2. Report whether each expectation held.

## Pre-registered design (v1, 2026-10-18)

- **For the events of BT1 and BT4:** the AUC of each pillar at t, with intervals.
- **Expectations, stated now:** for conflict, the security and political pillars lead; for monetary crises, the
  economic pillar leads.

## Results (v1, run 2026-10-18)

AUC of each edition-1 pillar; the intervals are in `data/backtests.json`.

| Pillar | Conflict onset | Inflation crisis | Currency crash |
| --- | --- | --- | --- |
| A Political / Governance | .712 | **.627** | .510 |
| B Economic | .535 | .622 | **.565** |
| C Social / Human capital | .678 | .478 | .462 |
| D Health | .600 | .491 | .521 |
| E Security / Conflict | .682 | .609 | .543 |
| F Environmental | .442 | .407 | .400 |
| G Structural / Infrastructure | **.713** | .603 | .544 |

**Expectations, as pre-registered:** conflict led by A or E: not held (G .713, A .712). Inflation crises led by B:
not held (A .627, B .622). Currency crashes led by B: held.

**Reading.** The conflict signal sits in the governance-laden pillars: A, G (which carries two WGI items) and E.
Edition 1's Pillar F runs the wrong way for every event (.400 to .442), as a pillar that measures wealth inversely
would: evidence for replacing it with [Pillar 8 Environment and Climate Exposure](<../../ASI 04 Methods/Pillar 8 Environment and Climate Exposure.md>).

## Results (v2, edition 2, run 2026-10-20)

The same design on edition 2's panel, with the pillar mapping stated before the run ([ASI Backtest Protocol](<ASI Backtest Protocol.md>); athena-data e6e9b22). Edition 1's results are above.

AUC of each edition-2 pillar on BT1's and BT4's rows; the intervals are in `data/backtests.json`.

- **Conflict:** leading SEC, expected GOV, SEC, VOI: held. SEC .785; ENV .704; EXT .689; COH .671; GOV .663; HUM .647; VOI .617; MAC .415.
- **Inflation crisis:** leading MAC, expected MAC: held. MAC .749; SEC .637; GOV .589; ENV .569; EXT .561; COH .538; HUM .533; VOI .515.
- **Currency crash:** leading MAC, expected MAC: held. MAC .560; EXT .542; SEC .518; HUM .509; GOV .497; ENV .495; VOI .465; COH .446.

**Reading.** Every pre-registered expectation holds, against one of three in edition 1.

## Inputs and outputs

- **In:** the pillar scores and BT1's and BT4's events
- **Out:** AUC with its 95% interval, the difference against each baseline, the hit rate, and n; written into this note under Results

## Where it stands

Run on 2026-10-18 on edition 1's panel, with the WDI's copies of the outcome data (athena-core `projects/asi/06_backtests.py`; results in `data/backtests.json`). The design above was committed before the run (athena-data 90fb6a8).

## Related

[ASI Pillars](<../../ASI 04 Methods/ASI Pillars.md>) · [ASI Backtest Protocol](<ASI Backtest Protocol.md>)
