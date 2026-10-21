---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# Pillar 8 Environment and Climate Exposure

> [!abstract] Goal
> Measure the pressure the natural environment puts on the country: water stress, polluted air, depleted resources, disasters that displace people, and forest loss.

## Why it exists

**Umbrella concept.** Environmental pressure and degradation: scarce water, unhealthy air, resources run down, hazards that strike, and the land cover that buffers them.

**How it bears on stability.** Interpeace names climate change and environmental factors among the pressures resilience must absorb; the UN's environmental insecurity lists degradation, depletion and disasters.

**Why it is its own pillar.** It replaces edition 1's Pillar F, which measured wealth (CO2 per capita against log GDP per capita, −.87).

## Precise objectives

1. Every indicator passes the umbrella test.
2. No indicator correlates with log GDP per capita above |.80|, the failure that sank edition 1's Pillar F.

**The umbrella test (P58).** A pillar may be the sum of separate causes (formative), but only if every indicator is
an instance of the pillar's umbrella concept, stated above. An indicator that fails the test moves or leaves,
whatever its correlations.

## Indicators in the tested layout (variant B, 2026-10-18)

Direction: **+** means a higher value is more stable, **−** the reverse. Latest real value per state in 2016–2024.

| Indicator | Code | Direction |
| --- | --- | --- |
| Water stress | ER.H2O.FWST.ZS | − |
| PM2.5 exposure | EN.ATM.PM25.MC.M3 | − |
| Natural resources depletion, % of GNI | NY.ADJ.DRES.GN.ZS | − |
| Disaster displacement per 100,000 | VC.IDP.NWDS | − |
| Forest area, % of land | AG.LND.FRST.ZS | + |

**Measurement model.** Mean inter-item |rho| inside the pillar: **.16** (formative: separate hazards, as INFORM's hazard dimension is).

## Candidates to widen it

ND-GAIN exposure and INFORM hazard (both blocked on terms); EM-DAT disasters (registration); forest change rather than level.

## As built at edition 2, step 6 (athena-core #14)

| Indicator | Variable | Direction | Logged |
| --- | --- | --- | --- |
| Level of water stress: freshwater withdrawal as a proportion of available freshwater resources | `water_stress` | − | yes |
| PM2.5 air pollution, mean annual exposure (micrograms per cubic meter) | `pm25` | − | yes |
| Adjusted savings, natural resources depletion (% of GNI) | `resource_depletion` | − | yes |
| Internally displaced persons, new displacement associated with disasters, per 100,000 people | `disaster_displacement` | − | yes |
| Forest area (% of land area) | `forest_area` | + | yes |

**Descriptive** (shown, not scored): `co2_pc`; `freshwater_withdraw`; `nonrenew_elec`; `agri_land`.

**At 2024:** mean score 57.25; 0 states reliable, 0 thin, 54 unreliable.

## Inputs and outputs

- **In:** the indicators above, from Athena's datasets
- **Out:** one pillar score per state and year, with its n, interval and reliability tier

## Where it stands

Built at edition 2, step 6 (athena-core #14), key `ENV`. Unreliable for all 54 states at 2024: four of its five series end in 2021 to 2023, so four values are carried forward and the imputed share passes the 0.50 limit. Step 7 ([ASI Method Reliability Tiers](<ASI Method Reliability Tiers.md>)) decides what that means.

## Open questions

- Forest area as a level rewards forested countries; the change in forest cover tests degradation better.

## Related

[Appraisal ND-GAIN](<../ASI 06 Outputs and Site/ASI Appraisals.md#the-appraisals>) · [Appraisal INFORM Risk](<../ASI 06 Outputs and Site/ASI Appraisals.md#the-appraisals>)
