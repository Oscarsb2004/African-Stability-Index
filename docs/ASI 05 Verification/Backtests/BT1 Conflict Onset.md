---
type: "project-page"
project: "African Stability Index"
section: "05 Verification"
status: "built"
created: "2026-10-18"
updated: "2026-10-20"
---

# BT1 Conflict Onset

> [!abstract] Goal
> Test whether a low ASI score precedes the onset of armed conflict in a state at peace.

## Why it exists

Conflict is the instability Interpeace's definition puts first; if the index cannot anticipate it, its security and governance content is decoration.

## Precise objectives

1. Report the AUC and both pass rules for the composite and the variant.
2. Report the hit rate in the bottom fifth.

## Pre-registered design (v1, 2026-10-18)

- **Event:** battle-related deaths recorded for the state (UCDP's threshold is 25 in a year).
- **Interim data:** WDI's copy of UCDP (VC.BTL.DETH), 40 states, 1989–2024. WDI lists conflict years only, so a
  missing year is read as below the threshold. The final run uses UCDP directly.
- **At risk:** state-years t from 2000 to 2021 with no recorded battle deaths at t.
- **Predictor:** the composite at t. **Variant:** the composite without the security pillar (E), because Pillar E and
  the WGI's political stability share the outcome's concept.
- **Baselines:** log GDP per capita; conflict in t−5 to t−1; the WGI political stability estimate.

## Results (v1, run 2026-10-18)

**n:** 893 state-years, 142 events, 54 states.

| Predictor | AUC | 95% interval | Minus log GDP per capita |
| --- | --- | --- | --- |
| ASI composite | .697 | .574–.794 | +.078 (−.065 to .231) |
| ASI without Pillar E | .685 | .563–.788 | +.068 (−.074 to .217) |
| Log GDP per capita | .616 | .475–.752 | — |
| Conflict in t−5 to t−1 | .702 | .633–.763 | +.105 (−.015 to .235) |
| WGI political stability | .779 | .679–.862 | +.166 (.013 to .326) |

**Hit rate:** 36 of 142 events (25.4%) came from states in the bottom fifth at t; chance is 20%.

**Horizons:** t+1 alone, .692 (.586–.782; 69 events); t+1 to t+5, .690 (.566–.795; 183 events).

**Verdict:** informative, yes. Adds to development, no: the gain over income per head has an interval that
includes zero.

**Reading.** The ASI carries real information about conflict onset, steady across horizons, and not only through
its security pillar. But it cannot be shown to add to income per head, and the WGI's political stability estimate
alone predicts better: the composite dilutes its strongest signal.

## Results (v2, edition 2, run 2026-10-20)

The same design on edition 2's panel, with the pillar mapping stated before the run ([ASI Backtest Protocol](<ASI Backtest Protocol.md>); athena-data e6e9b22). Edition 1's results are above.

**n:** 893 state-years, 142 events, 54 states.

| Predictor | AUC | 95% interval | Minus log GDP per capita |
| --- | --- | --- | --- |
| ASI composite | .743 | .644–.822 | +.126 (−.004 to .265) |
| ASI without SEC | .719 | .617–.798 | +.103 (−.028 to .241) |
| Log GDP per capita | .616 | .475–.752 | — |
| The event in t−5 to t−1 | .702 | .633–.763 | +.105 (−.015 to .235) |
| WGI political stability | .779 | .679–.862 | +.166 (.013 to .326) |

**Hit rate:** 34 of 142 events (23.9%) came from states in the bottom fifth at t; chance is 20%.

**Verdict:** informative, yes. Adds to development, no.

**Horizons:** t+1 alone, .732 (.642–.804; 69 events); t+1 to t+5, .741 (.633–.826; 183 events).

**Reading.** Edition 2 predicts conflict onset better than edition 1 (.743 against .697), and still not only through its security pillar. The gain over income per head has an interval just below zero at its lower end, so it does not yet add to development, and the WGI's political stability estimate alone still predicts better.

## Inputs and outputs

- **In:** the panel; VC.BTL.DETH; NY.GDP.PCAP.PP.KD; GOV_WGI_PV.EST
- **Out:** AUC with its 95% interval, the difference against each baseline, the hit rate, and n; written into this note under Results

## Where it stands

Run on 2026-10-18 on edition 1's panel, with the WDI's copies of the outcome data (athena-core `projects/asi/06_backtests.py`; results in `data/backtests.json`). The design above was committed before the run (athena-data 90fb6a8).

## Related

[Pillar 3 Security and Violence](<../../ASI 04 Methods/Pillar 3 Security and Violence.md>) · [ASI Backtest Protocol](<ASI Backtest Protocol.md>)
