---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-18"
updated: 2026-10-19
---

# ASI Economy Section

> [!abstract] Goal
> Give each state an economic outlook on the right: forecasts first, then the headline figures, the record and the detail, all from the shared section files (P54, P56>).

## Why it exists

The owner asked for GDP, three-year average inflation, historical inflation highs with their years, growth, and
analyses weighted ahead of history. Stressors were scrapped (P60>).

## Precise objectives

1. Order: outlook (when built>), headline tiles, inflation's record, charts, then the economy dimension's other blocks (public finances, structure, jobs>).
2. Money, banks, markets and debt are under [ASI Finance Section](<ASI Finance Section.md>) (P64>).
3. Each block is one shared template; adding or removing one is one file.

## Inputs and outputs

- **In:** `sections.json`
- **Out:** the Economy view

## Where it stands

Built. The economy dimension holds five templates (athena-core #17>).

## The parts

One row per part of the panel; each was its own note until P5 (P94>).

**Every one shares these objectives:**

1. Every figure shows its period; a computed one is marked derived.
2. Every measure is bound to a series, or listed as unbound with its reason.

**In and out:**

- **In:** the `athena.sections/1` document (ASI binding: WDI>)
- **Out:** one block of the Economy panel

**Related to all of them:**

System Sections and Figure Shells (athena-data>)

| Part | Status | Goal | Why it exists | Figures | Where it stands |
| --- | --- | --- | --- | --- | --- |
| **Economy Outlook** | built | Lead the panel with the IMF's projections for growth, inflation and government debt. | Analyses weigh more than history (P56>); the IMF WEO is the standard published forecast for every state. | Planned: real GDP growth next year and the five-year projection; inflation projected; general government gross debt, % of GDP. Source: IMF World Economic Outlook database (terms read 2026-10-18; cite "Source: International Monetary Fund, World Economic Outlook database"). | Built (athena-core #34>): the shared template `outlook` and the shell `first`, bound to the WEO's projections only (`where = { OBS_STATUS = "F" }`). 52 of 54 states; the IMF publishes none for Eritrea or Senegal in this edition, and the panel says so. |
| **Economy Output and Growth** | built | Show how large the economy is, how much it produces per person, and how fast and steadily it grows. | Size, income per head and growth are the first three things anyone asks of an economy. | GDP (current US$); GDP per person, PPP; real growth, latest; real growth, 3-year average (derived>); volatility of growth over 10 years (derived>); real growth since 2000 (chart>). | Built (athena-core #15>). |
| **Economy Prices and Inflation** | built | Show how fast prices rise now, on average lately, and at their worst on record. | The owner asked for the 3-year average and historical highs with their years. | Inflation, latest; 3-year average (derived>); the three highest years on record, at least 3 years apart so one episode counts once (derived, shell `extremes`); inflation since 2000 (chart>). Example: Nigeria, 72.8% in 1995, 54.5% in 1988, 44.6% in 1992; 3-year average 27.0% for 2023–2025. | Built (athena-core #15>). |
| **Economy Public Finances** | built | Show what the state collects, how far it borrows, and how much it owes. | Debt and revenue set how much room a state has to absorb a shock. | Tax revenue, % of GDP; government lending or borrowing, % of GDP, latest and 3-year average (derived>); government debt (unbound until the IMF WEO: WDI covers 23 of 54 states>). What the country owes abroad is under [Finance Sovereign and External Debt](<ASI Finance Section.md#the-parts>). | Built (athena-core #15; external debt moved to Finance in #17>). |
| **Economy Economic Structure** | built | Show what the economy is made of and how much it leans on fuel, minerals and natural resources. | Structure explains exposure: a fuel exporter and a services economy meet the same shock differently. | Agriculture, industry, manufacturing and services, % of GDP; fuel exports and ore exports, % of merchandise exports; natural resource rents, % of GDP (WDI's latest is 2021>). | Built (athena-core #15>). |
| **Economy Jobs** | built | Show modelled labour estimates as context. | Where most work is informal, low unemployment can mean people cannot afford to be without work, so these figures inform rather than judge. | Unemployment; youth unemployment (15–24>); labour force participation; vulnerable employment (ILO modelled estimates, via WDI>). | Built (athena-core #15>). |

## Open questions

- **Economy Outlook:** the edition is printed once, under the outlook, and every tile shows its year (first position, athena-core #34>); the owner may ask for the edition on every tile.

## Related

System Sections and Figure Shells (athena-data>) · [Pillar 4 Macroeconomic and Fiscal Stability](<../ASI 04 Methods/Pillar 4 Macroeconomic and Fiscal Stability.md>)
