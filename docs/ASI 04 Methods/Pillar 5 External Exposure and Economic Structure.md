---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# Pillar 5 External Exposure and Economic Structure

> [!abstract] Goal
> Measure how exposed the economy is to forces outside the country, through what it sells, what it receives, and how large and diversified it is.

## Why it exists

**Umbrella concept.** Dependence on the outside world: on commodity exports, natural-resource rents, aid and capital flows; and the size and diversity that cushion it.

**How it bears on stability.** Interpeace names connections between communities (trade, aid, investment) as resilience; dependence on a single commodity or donor is the matching exposure.

**Why it is its own pillar.** Exposure is largely set outside the country; it is kept apart from domestic macro management (pillar 4).

## Precise objectives

1. Every indicator passes the umbrella test, with its direction justified in writing.
2. Natural resource rents are refreshed (WDI's latest is 2021).

**The umbrella test (P58).** A pillar may be the sum of separate causes (formative), but only if every indicator is
an instance of the pillar's umbrella concept, stated above. An indicator that fails the test moves or leaves,
whatever its correlations.

## Indicators in the tested layout (variant B, 2026-10-18)

Direction: **+** means a higher value is more stable, **−** the reverse. Latest real value per state in 2016–2024.

| Indicator | Code | Direction |
| --- | --- | --- |
| Fuel exports, % of merchandise exports | TX.VAL.FUEL.ZS.UN | − |
| Ore and metal exports, % of merchandise exports | TX.VAL.MMTL.ZS.UN | − |
| Natural resource rents, % of GDP | NY.GDP.TOTL.RT.ZS | − |
| Development aid received, % of GNI | DT.ODA.ODAT.GN.ZS | − |
| Remittances received, % of GDP | BX.TRF.PWKR.DT.GD.ZS | + |
| Trade, % of GDP | NE.TRD.GNFS.ZS | + |
| FDI inflows, % of GDP | BX.KLT.DINV.WD.GD.ZS | + |
| GDP, current US$ (log; size, P50) | NY.GDP.MKTP.CD | + |

**Measurement model.** Mean inter-item |rho| inside the pillar: **.20** (formative: separate channels of exposure).

## Candidates to widen it

Export concentration (UNCTAD, terms to read); food import dependence (FAOSTAT); economic complexity (terms to read).

## As built at edition 2, step 6 (athena-core #14)

| Indicator | Variable | Direction | Logged |
| --- | --- | --- | --- |
| Fuel exports (% of merchandise exports) | `fuel_exports` | − | yes |
| Ores and metals exports (% of merchandise exports) | `ore_metal_exports` | − | yes |
| Total natural resources rents (% of GDP) | `resource_rents` | − | yes |
| Net ODA received (% of GNI) | `aid_received` | − | yes |
| Personal remittances, received (% of GDP) | `remittances` | + | yes |
| Trade (% of GDP) | `trade_openness` | + | yes |
| Foreign direct investment, net inflows (% of GDP) | `fdi_inflows` | + | yes |
| GDP (current US$) | `gdp_total` | + | yes |

**Descriptive** (shown, not scored): `domestic_credit_private`.

**At 2024:** mean score 55.46; 29 states reliable, 14 thin, 9 unreliable.

## Inputs and outputs

- **In:** the indicators above, from Athena's datasets
- **Out:** one pillar score per state and year, with its n, interval and reliability tier

## Where it stands

Built at edition 2, step 6 (athena-core #14), key `EXT`.

## Open questions

- Trade and remittances: exposure or connection? Their direction (+) is a first position for the owner.
- Total GDP measures size; it barely tracks the rest (rho .03 with edition 1's Pillar B).

## Related

[ASI Economy Section](<../ASI 06 Outputs and Site/ASI Economy Section.md>)
