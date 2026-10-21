---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: "2026-10-19"
---

# Pillar 7 Social Cohesion and Equity

> [!abstract] Goal
> Measure whether society holds together across its groups: how evenly income and opportunity are shared, and how much strain displacement and fast urban growth put on it.

## Why it exists

**Umbrella concept.** The fairness and cohesion of society: inequality of income and opportunity, between women and men and between town and slum, and the strain of hosting the displaced and of rapid urban growth.

**How it bears on stability.** Interpeace: an inclusive peace, communities connected to each other, and attention to emerging pressures (demography, migration).

**Why it is its own pillar.** Cohesion is central to Interpeace's definition and draws on sources (EPR, Afrobarometer, surveys) that no other pillar uses.

## Precise objectives

1. Every indicator passes the umbrella test.
2. Reach at least one direct measure of group exclusion.

**The umbrella test (P58).** A pillar may be the sum of separate causes (formative), but only if every indicator is
an instance of the pillar's umbrella concept, stated above. An indicator that fails the test moves or leaves,
whatever its correlations.

## Indicators in the tested layout (variant B, 2026-10-18)

Direction: **+** means a higher value is more stable, **−** the reverse. Latest real value per state in 2016–2024.

| Indicator | Code | Direction |
| --- | --- | --- |
| Gini index | SI.POV.GINI | − |
| Refugees hosted per 100,000 | SM.POP.RHCR.EA | − |
| Urban population in slums | EN.POP.SLUM.UR.ZS | − |
| Female-to-male labour participation | SL.TLF.CACT.FM.ZS | + |
| Urban population growth | SP.URB.GROW | − |

**Measurement model.** Mean inter-item |rho| inside the pillar: **.22** (formative: separate pressures on cohesion).

## Candidates to widen it

Ethnic Power Relations (terms to read); Afrobarometer social trust (context); subnational inequality in human development (Global Data Lab, terms to read).

## As built at edition 2, step 6 (athena-core #14)

| Indicator | Variable | Direction | Logged |
| --- | --- | --- | --- |
| Refugees under the mandate of the UNHCR by country or territory of asylum, per 100,000 people | `refugees_hosted` | − | yes |
| Population living in slums (% of urban population) | `slum_population` | − | no |
| Ratio of female to male labor force participation rate (%) (modeled ILO estimate) | `female_male_labour` | + | no |
| Urban population growth (annual %) | `urban_growth` | − | no |

**Descriptive** (shown, not scored): `gini`; `primary_gpi`; `secondary_gpi`.

**At 2024:** mean score 53.95; 50 states reliable, 3 thin, 1 unreliable.

## At edition 2, step 9 (athena-core #25; P98 to P100)

Two indicators join, for horizontal cohesion and the inclusion of youth (plan 1.2):

| Indicator | Key | Direction | Scored |
| --- | --- | --- | --- |
| Deaths in non-state conflict, per 100,000 people (UCDP; the plan's communal violence) | `non_state_deaths` | − | yes |
| Youth unemployment, % of the labour force aged 15 to 24 (modelled ILO estimate) | `youth_unemployment` | − | shown |

Youth unemployment is shown and not scored: measured unemployment is higher in Africa's richer states (the candidate
screen of 2026-10-18).

- **At 2024:** the pillar's mean rises from 53.95 to 62.31. Non-state deaths are zero in 39 of 54 states, and a
  measured zero scores 100.
- **Non-state violence is here by P99:** cohesion between communities.
- **The pillar's tiers:** 53 reliable and 1 thin, against 50, 3 and 1 unreliable.

## Inputs and outputs

- **In:** the indicators above, from Athena's datasets
- **Out:** one pillar score per state and year, with its n, interval and reliability tier

## Where it stands

Built at edition 2, step 6 (athena-core #14), key `COH`.

## Open questions

- Refugees hosted and urban growth are pressures on cohesion, not cohesion itself: do they pass the umbrella test? Hosting refugees is also no sign of instability. First position: keep them pending a direct measure.
- The pillar is the thinnest in the WDI; most of its reach comes from new sources.

## Related

[Appraisal V-Dem](<../ASI 06 Outputs and Site/ASI Appraisals.md#the-appraisals>)
