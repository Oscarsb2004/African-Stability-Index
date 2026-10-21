---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-18"
updated: 2026-10-19
---

# ASI Finance Section

> [!abstract] Goal
> Give each state a macro-financial picture on yearly horizons: money, the currency and reserves, banks, capital markets, debt and capital flows.

## Why it exists

The owner's example of growing one dimension on its own (P64): what to measure for any financial market, on macroeconomic horizons rather than trading ones. Its charter is [Dimension Finance](<Dimension Finance.md>).

## Precise objectives

1. Headline tiles: real interest rate, reserves, bad loans, the currency's change a year.
2. Histories of the real interest rate, reserves and external debt.
3. Every finance section as a table, each figure with its period and source.

## Inputs and outputs

- **In:** `sections.json` (the six finance templates)
- **Out:** the Finance view

## Where it stands

Built (athena-core #17). Across the 54 states the six blocks hold 1,716 of 2,160 figures; capital markets is the thinnest (78 of 270), since few states have an exchange of their own.

## The parts

One row per part of the panel; each was its own note until P5 (P94).

**Every one shares these objectives:**

1. Every figure shows its period; a computed one is marked derived.
2. The same template serves any country (P64); the ASI binds it to the WDI.

**In and out:**

- **In:** the `athena.sections/1` document (ASI binding: WDI)
- **Out:** one block of the Finance panel

**Related to all of them:**

[Dimension Finance](<Dimension Finance.md>) · System Sections and Figure Shells (athena-data)

**Where they stand:**

Built (athena-core #17).

| Part | Status | Goal | Why it exists | Figures |
| --- | --- | --- | --- | --- |
| **Finance Monetary Conditions** | built | Show how tight money is. | Real rates and money growth show whether policy is containing inflation or feeding it. | Real interest rate (and since 2000); lending rate; deposit rate; broad money, % of GDP; broad money growth, latest and 3-year average (derived). |
| **Finance Currency and Reserves** | built | Show how the currency has moved and the cushion behind it. | A weak cushion against a falling currency is how an external shock becomes a crisis. | Local currency per US dollar, average change a year over 5 and 10 years (derived); real effective exchange rate; reserves in months of imports (and since 2000); short-term external debt, % of reserves; current account, latest and 3-year average (derived). |
| **Finance Banks** | built | Show how sound the banks are and how far they reach. | Bad loans and thin capital turn a downturn into a banking crisis; credit depth and accounts show reach. | Non-performing loans, latest and highest on record (derived); bank capital to assets; credit to the private sector and its 10-year change (derived); interest rate spread; adults with an account. |
| **Finance Capital Markets** | built | Show how deep and active the stock market is. | Where markets exist, their depth says how firms raise money; where they do not, that is itself telling. | Market capitalisation, % of GDP; turnover ratio; listed domestic companies; S&P Global equity index, latest and 3-year average change (derived). |
| **Finance Sovereign and External Debt** | built | Show how heavily debt weighs on the state and the country. | Interest that eats revenue and debt service that eats exports are the classic paths to default. | Interest payments, % of revenue, and their 5-year change (derived); external debt, % of GNI (and since 2000); debt service, % of GNI and % of exports; the 5-year change in debt service (derived). |
| **Finance Capital Flows** | built | Show which way money flows across the border. | Sudden stops in portfolio money and swings in aid and remittances test the balance of payments. | FDI inflows, % of GDP, latest and 3-year average (derived); portfolio equity inflows; portfolio investment, net; remittances, % of GDP; aid, % of GNI. |

## Related

[Dimension Finance](<Dimension Finance.md>) · [ASI Economy Section](<ASI Economy Section.md>)
