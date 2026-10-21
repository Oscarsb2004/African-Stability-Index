---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# Pillar 6 Human Development and Demography

> [!abstract] Goal
> Measure what people have to live on and live with: income, health, nutrition, education, basic services, connection, and the demographic transition that moves with them.

## Why it exists

**Umbrella concept.** Living standards and capabilities: income per head, health, nutrition, schooling, water, sanitation, power and connection, and where the country stands in its demographic transition.

**How it bears on stability.** Interpeace: peace rests on the social and economic conditions people say they need; health, food and education are named among them.

**Why it is its own pillar.** Development is one factor in every African dataset; gathering it here is what cut the overlap between pillars. Demography correlated .77 with it when it stood alone (layout A).

## Precise objectives

1. Every indicator passes the umbrella test.
2. Report how much of the composite this pillar carries, since it holds 16 of 54 indicators but one eighth of the weight.

**The umbrella test (P58).** A pillar may be the sum of separate causes (formative), but only if every indicator is
an instance of the pillar's umbrella concept, stated above. An indicator that fails the test moves or leaves,
whatever its correlations.

## Indicators in the tested layout (variant B, 2026-10-18)

Direction: **+** means a higher value is more stable, **−** the reverse. Latest real value per state in 2016–2024.

| Indicator | Code | Direction |
| --- | --- | --- |
| GDP per person, PPP (log) | NY.GDP.PCAP.PP.CD | + |
| Life expectancy | SP.DYN.LE00.IN | + |
| Under-5 mortality | SH.DYN.MORT | − |
| Maternal mortality | SH.STA.MMRT | − |
| Stunting | SH.STA.STNT.ME.ZS | − |
| Undernourishment | SN.ITK.DEFC.ZS | − |
| Youth literacy | SE.ADT.1524.LT.ZS | + |
| Primary completion | SE.PRM.CMPT.ZS | + |
| Electricity access | EG.ELC.ACCS.ZS | + |
| Basic drinking water | SH.H2O.BASW.ZS | + |
| Basic sanitation | SH.STA.BASS.ZS | + |
| Internet users | IT.NET.USER.ZS | + |
| Mobile subscriptions | IT.CEL.SETS.P2 | + |
| Youth share of population (0–14) | SP.POP.0014.TO.ZS | − |
| Population growth | SP.POP.GROW | − |
| Adolescent fertility | SP.ADO.TFRT | − |

**Measurement model.** Mean inter-item |rho| inside the pillar: **.62** (reflective: one development factor).

## Candidates to widen it

DHS and MICS surveys (registration); IHME (non-commercial); the UNDP HDI is an appraisal, not an indicator.

## As built at edition 2, step 6 (athena-core #14)

| Indicator | Variable | Direction | Logged |
| --- | --- | --- | --- |
| GDP per capita, PPP (current international $) | `gdp_pc_ppp` | + | yes |
| Life expectancy at birth, total (years) | `life_expect_tot` | + | no |
| Mortality rate, under-5 (per 1,000 live births) | `under5_mortality` | − | no |
| Maternal mortality ratio (modeled estimate, per 100,000 live births) | `maternal_mortality` | − | yes |
| Prevalence of stunting, height for age (modeled estimate, % of children under 5) | `stunting` | − | no |
| Prevalence of undernourishment (% of population) | `undernourishment` | − | yes |
| Literacy rate, youth total (% of people ages 15-24) | `youth_literacy` | + | no |
| Primary completion rate, total (% of relevant age group) | `primary_completion` | + | no |
| Access to electricity (% of population) | `elec_access_tot` | + | no |
| People using at least basic drinking water services (% of population) | `water_access_pop` | + | no |
| People using at least basic sanitation services (% of population) | `basic_sanitation` | + | no |
| Individuals using the Internet (% of population) | `internet_users` | + | no |
| Mobile cellular subscriptions (per 100 people) | `mobile_subscriptions` | + | no |
| Population ages 0-14 (% of total population) | `youth_share` | − | no |
| Population growth (annual %) | `population_growth` | − | no |
| Adolescent fertility rate (births per 1,000 women ages 15-19) | `adolescent_fertility` | − | no |

**Descriptive** (shown, not scored): `mort_infant`; `hand_washing_facil`; `sev_food_insec`; `managed_water_percent`; `social_protection_labour_pop`; `population_total`.

**At 2024:** mean score 60.09; 52 states reliable, 2 thin, 0 unreliable.

## Inputs and outputs

- **In:** the indicators above, from Athena's datasets
- **Out:** one pillar score per state and year, with its n, interval and reliability tier

## Where it stands

Built at edition 2, step 6 (athena-core #14), key `HUM`.

## Open questions

- GDP per person is scored here (P50); should it instead be the control variable for the others?

## Related

[ASI Method Pillar Distinctness](<ASI Method Pillar Distinctness.md>) · [Appraisal UNDP HDI](<../ASI 06 Outputs and Site/ASI Appraisals.md#the-appraisals>)
