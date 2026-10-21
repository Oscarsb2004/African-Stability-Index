---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# ASI Method Indicator Admission

> [!abstract] Goal
> Admit an indicator to scoring only if it covers enough states, varies, has a defensible direction, adds new information, and passes its pillar's umbrella test.

## Why it exists

Edition 1 scored indicators reported by as few as 16 states; an r of .50 is not significant at n = 14 but is at n = 20, so thin indicators cannot carry full weight.

## Precise objectives

1. Coverage: a real value for at least 33 of the 54 states in the window (the Ibrahim Index's rule).
2. Variance: not near-constant across states.
3. Direction: written down with its reason before scoring.
4. New information: partial r with the pillar's existing items, GDP held constant, below .90.
5. Umbrella test: the indicator is an instance of its pillar's concept (P58).
6. Below the floor, an indicator is shown as descriptive, not scored.

**Evidence.** At 2023, 8 of edition 1's 32 scoring indicators fall below the floor: femicide, secondary enrolment, learning poverty, homicide, primary enrolment, social protection, displaced persons, managed water.

## Inputs and outputs

- **In:** the candidate list and the panel
- **Out:** the admitted indicator list per edition

## Where it stands

Built (edition 2, step 5, athena-core #14): `ADMISSION_FLOOR = 33`, with a test and a negative control. At 2024, 10 indicators fell below and became descriptive. Composites moved 1.75 points on average; rank correlation .981. At step 6 the floor also decided the new layout: homicide, conflict displacement, the stock of displaced people and the Gini index are shown, not scored.

## Related

ASI next edition plan (athena-data)
