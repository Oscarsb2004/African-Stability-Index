---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# Pillar 4 Macroeconomic and Fiscal Stability

> [!abstract] Goal
> Measure how steady the macroeconomy is and how much room the state has to absorb a shock.

## Why it exists

**Umbrella concept.** The steadiness of prices, growth and the public and external accounts, and the buffers held against shocks.

**How it bears on stability.** Interpeace: resilience combines social, institutional, environmental and financial factors; high inflation, debt distress and empty reserves leave a state unable to absorb a shock.

**Why it is its own pillar.** Shocks and buffers move on a different clock from development; mixing them with income per head was a source of edition 1's overlap.

## Precise objectives

1. Every indicator passes the umbrella test.
2. Government debt comes from the IMF WEO once ingested (WDI covers 23 of 54 states).

**The umbrella test (P58).** A pillar may be the sum of separate causes (formative), but only if every indicator is
an instance of the pillar's umbrella concept, stated above. An indicator that fails the test moves or leaves,
whatever its correlations.

## Indicators in the tested layout (variant B, 2026-10-18)

Direction: **+** means a higher value is more stable, **−** the reverse. Latest real value per state in 2016–2024.

| Indicator | Code | Direction |
| --- | --- | --- |
| Inflation, % a year | FP.CPI.TOTL.ZG | − |
| Real GDP growth, latest | NY.GDP.MKTP.KD.ZG | + |
| Volatility of growth, 2010–2024 (derived: standard deviation) | NY.GDP.MKTP.KD.ZG | − |
| External debt, % of GNI | DT.DOD.DECT.GN.ZS | − |
| Debt service, % of GNI | DT.TDS.DECT.GN.ZS | − |
| Reserves, months of imports | FI.RES.TOTL.MO | + |
| Current account, % of GDP | BN.CAB.XOKA.GD.ZS | + |

**Measurement model.** Mean inter-item |rho| inside the pillar: **.15** (formative: separate buffers and stresses).

## Candidates to widen it

IMF WEO general government debt and fiscal balance (terms read; adapter planned); IMF debt sustainability ratings; exchange-rate volatility.

## As built at edition 2, step 6 (athena-core #14)

| Indicator | Variable | Direction | Logged |
| --- | --- | --- | --- |
| Inflation, consumer prices, annual % (5-year average) | `inflation_5yr_avg` | − | yes |
| GDP growth, annual % (3-year average) | `gdp_growth_3yr_avg` | + | no |
| Volatility of real GDP growth: standard deviation over the last 10 years (percentage points) | `growth_volatility` | − | yes |
| External debt stocks (% of GNI) | `external_debt` | − | yes |
| Total debt service (% of GNI) | `debt_service` | − | yes |
| Total reserves in months of imports | `reserves_months` | + | no |
| Current account balance (% of GDP) | `current_account` | + | no |

**Descriptive** (shown, not scored): none.

**At 2024:** mean score 47.81; 49 states reliable, 3 thin, 1 unreliable.

## Inputs and outputs

- **In:** the indicators above, from Athena's datasets
- **Out:** one pillar score per state and year, with its n, interval and reliability tier

## Where it stands

Built at edition 2, step 6 (athena-core #14), key `MAC`. Negatively correlated with every other pillar at 2024 (−.07 to −.34), and PCA gives it no weight. Step 8 ([ASI Method Aggregation and Weights](<ASI Method Aggregation and Weights.md>)) weighs that.

## Open questions

- Inflation's direction is monotone here; very low inflation is rare in the panel, but deflation would need a rule.

## Related

[ASI Economy Section](<../ASI 06 Outputs and Site/ASI Economy Section.md>) · [BT4 Monetary Crises](<../ASI 05 Verification/Backtests/BT4 Monetary Crises.md>)
