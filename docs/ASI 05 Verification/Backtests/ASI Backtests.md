---
type: "project-page"
project: "African Stability Index"
section: "05 Verification"
status: "built"
created: "2026-10-18"
updated: "2026-10-20"
---

# ASI Backtests

> [!abstract] Goal
> Test whether a lower ASI score at year t is followed by more instability in the years after, beyond what income alone or recent history would tell.

## Why it exists

Predictive validity is the hardest test an index can face and the one composite indices most often skip. Each test
below is written down, with its pass rule, before it is run; results are reported whatever they show, and a changed
design becomes a new version with its reason ([ASI Backtest Protocol](<ASI Backtest Protocol.md>)).

## Precise objectives

1. Run every designed backtest on edition 1's panel, then rerun on every new edition.
2. Report AUC, the gain over baselines and the hit rate, each with n and an interval.
3. Never re-specify a backtest after seeing its result without logging a new version.

## Summary of the v1 run (2026-10-18, edition 1, outcomes from the WDI)

| Test | Events | ASI AUC (95% interval) | Informative | Adds to development |
| --- | --- | --- | --- | --- |
| [BT1 Conflict Onset](<BT1 Conflict Onset.md>) | 142 | .697 (.574–.794) | yes | no |
| [BT2 Conflict Displacement](<BT2 Conflict Displacement.md>) | 88 | .575 (.458–.693) | no | no |
| [BT4 Monetary Crises](<BT4 Monetary Crises.md>), inflation | 81 | .574 (.448–.704) | no | no |
| [BT4 Monetary Crises](<BT4 Monetary Crises.md>), currency | 242 | .496 (.419–.573) | no | no |
| [BT5 War Onset Event Study](<BT5 War Onset Event Study.md>) | 16 | 9 of 16 in the bottom fifth a year before | — | — |
| [BT6 Pillar Attribution](<BT6 Pillar Attribution.md>) | — | the conflict signal in A, G and E; F inverted | — | — |

**What it means for edition 2:**
1. **The index anticipates conflict, but no better than income alone, and worse than the WGI's political stability
   estimate alone.** Its strongest content is diluted by pillars that carry no conflict signal.
2. **It does not anticipate displacement or monetary crises.** Edition 2's Pillar 4 is where the economic content
   is tested again.
3. **Edition 1's Pillar F runs the wrong way for every event,** which supports its replacement (P57).
4. **Renewed wars are flagged; new ones mostly are not.** Mid-table states slid into war without a falling score.
5. **Everything is rerun on edition 2, with UCDP ingested directly, before publication.**

## Summary of the v2 run (2026-10-20, edition 2, outcomes from the WDI)

The same tests on edition 2's panel. The pillar mapping was stated before the run ([ASI Backtest Protocol](<ASI Backtest Protocol.md>)).

| Test | ASI's AUC (edition 1) | Informative | Adds to development |
| --- | --- | --- | --- |
| BT1 conflict onset | .743 (.697) | yes | no: +.126, interval −.004 to .265 |
| BT2 conflict displacement | .643 (.575) | yes (was no) | no |
| BT4 inflation crisis | .626 (.574) | no | no; the MAC pillar alone .749, adding .203 |
| BT4 currency crash | .493 (.496) | no | no |

- **BT5:** 68.75% of the 16 war onsets came from states in the bottom fifth at t−1 (edition 1: 56.25%).
- **BT6:** every expectation held: SEC led for conflict, and MAC for both monetary crises.
- **Still waiting:** BT3 (terms) and BT7 (WDI archives).

**Reading.** Edition 2 sees conflict more clearly than edition 1. It does not yet clear the bar of adding to
income per head, and the WGI's political stability alone predicts conflict better. Inflation crises live in MAC,
which the headline dilutes.

## Inputs and outputs

- **In:** the ASI panel (2000–2024) and outcome data (UCDP, IDMC, prices, exchange rates)
- **Out:** results in each backtest note, and a summary here

## Where it stands

Five of seven run on 2026-10-18 (v1, edition 1's panel). BT3 is blocked; BT7 is planned.

## Related

[ASI External Agreement](<../ASI External Agreement.md>)
