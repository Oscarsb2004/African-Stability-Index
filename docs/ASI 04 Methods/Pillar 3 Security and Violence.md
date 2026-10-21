---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: "2026-10-19"
---

# Pillar 3 Security and Violence

> [!abstract] Goal
> Measure how safe people are from organised and everyday violence, and from being forced from home by it.

## Why it exists

**Umbrella concept.** The physical safety of people: from armed conflict, from violence against civilians, from crime, and from displacement by violence.

**How it bears on stability.** Interpeace: a state must provide security and justice for all without discrimination, and protecting civilians produces more lasting outcomes.

**Why it is its own pillar.** Violence is an outcome, not a capacity: it is kept apart from governance so the two can be compared.

## Precise objectives

1. Every indicator passes the umbrella test.
2. WDI's battle deaths list only conflict years; until UCDP is ingested, an absent year is read as below UCDP's 25-death threshold, and this is stated wherever used.

**The umbrella test (P58).** A pillar may be the sum of separate causes (formative), but only if every indicator is
an instance of the pillar's umbrella concept, stated above. An indicator that fails the test moves or leaves,
whatever its correlations.

## Indicators in the tested layout (variant B, 2026-10-18)

Direction: **+** means a higher value is more stable, **−** the reverse. Latest real value per state in 2016–2024.

| Indicator | Code | Direction |
| --- | --- | --- |
| Political stability and absence of violence, WGI | GOV_WGI_PV | + |
| Battle-related deaths per 100,000 (UCDP via WDI) | VC.BTL.DETH | − |
| New conflict displacement per 100,000 (IDMC via WDI) | VC.IDP.NWCV | − |
| Internally displaced people per 100,000 | SM.POP.IDPC | − |
| Intentional homicide per 100,000 | VC.IHR.PSRC.P5 | − |

**Measurement model.** Mean inter-item |rho| inside the pillar: **.48** (between: partly coherent).

## Candidates to widen it

UCDP directly (CC BY 4.0): state-based deaths, one-sided violence against civilians, non-state conflict; UNHCR refugees by origin.

## As built at edition 2, step 6 (athena-core #14)

| Indicator | Variable | Direction | Logged |
| --- | --- | --- | --- |
| Political Stability and Absence of Violence / Terrorism, WGI estimated score | `pv_estimate` | + | no |
| Deaths in organised violence (state-based, non-state and one-sided), per 100,000 people | `organised_violence_deaths` | − | yes |

**Descriptive** (shown, not scored): `intent_homicide`; `femicide`; `displaced_persons`; `conflict_displacement`.

**At 2024:** mean score 68.01; 54 states reliable, 0 thin, 0 unreliable.

## At edition 2, step 9 (athena-core #25; P98 to P100)

Organised violence is scored by its UCDP parts (plan 1.2), per 100,000 people:

| Indicator | Key | Direction | Scored |
| --- | --- | --- | --- |
| Deaths in state-based armed conflict | `state_based_deaths` | − | yes |
| Deaths in one-sided violence against civilians (the protection of civilians) | `one_sided_deaths` | − | yes |
| Deaths in organised violence, the sum of the parts | `organised_violence_deaths` | − | shown |

The third part, non-state conflict, counts in [Pillar 7 Social Cohesion and Equity](<Pillar 7 Social Cohesion and Equity.md>).

- **At 2024:** the pillar's mean rises from 68.01 to 77.93.
  - Each part is zero in more states than the total (31 and 32 states, against 25), and a measured zero scores 100.
  - The outlier test now runs on the non-zero values (P100), so the goalposts sit at the true extremes, and a
    violent year that is not extreme no longer scores 0.
- **The largest move:** SSD, +44.24, since much of its violence is non-state.
- **The overlap (P98):** state-based and one-sided deaths have partial r +0.78 [+0.64, +0.87] at 2024, holding GDP
  per capita constant. That is below N2's .90; how to remove overlap is open.

## Inputs and outputs

- **In:** the indicators above, from Athena's datasets
- **Out:** one pillar score per state and year, with its n, interval and reliability tier

## Where it stands

Built at edition 2, step 6 (athena-core #14), key `SEC`. Two indicators. Homicide (20 states), conflict displacement (27) and the stock of displaced people (32) fall below the floor and are shown, not scored. UCDP's deaths in organised violence replace the WDI's battle deaths, which leave 27 states blank; UCDP records a zero for a year without violence.

## Open questions

- The conflict backtests share this pillar's concept, so they report a variant without it.

## Related

[BT1 Conflict Onset](<../ASI 05 Verification/Backtests/BT1 Conflict Onset.md>) · [BT5 War Onset Event Study](<../ASI 05 Verification/Backtests/BT5 War Onset Event Study.md>)
