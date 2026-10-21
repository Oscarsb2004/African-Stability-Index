---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# Dimension Finance

> [!abstract] Goal
> Give a macro-financial picture of any country's money, currency, banks, capital markets, sovereign debt and capital flows, on yearly to quarterly horizons, never trading horizons.

## Why it exists

The owner's example of how a dimension can grow (2026-10-18): advanced insight into what to measure for any
financial market in the world, in a finance tab, with macroeconomic indicators rather than day-trading horizons.
The backtests add a reason: the composite did not anticipate monetary crises, while this year's inflation did
([BT4 Monetary Crises](<../ASI 05 Verification/Backtests/BT4 Monetary Crises.md>)). Financial stress has its own leading signs, and they belong in a dimension of their own.

## Precise objectives

1. Answer these questions for any country: How tight is money, and is inflation under control? How exposed is the currency, and how large is the cushion? How sound and how deep are the banks? How deep are the capital markets? Can the sovereign pay? Which way is money flowing?
2. Move up one maturity level at a time ([Expert Consultation](<../ASI 08 Status and Roadmap/Expert Consultation.md>)), each move earned by a review.
3. Every measure comes from a publisher whose terms are read; nothing is flagged by a threshold of our own (P60).

## What it measures

**Already in Athena (WDI).** The count is how many of the WDI's 217 economies report the series in 2020 or later.

| Block | Measure | Code | Economies |
| --- | --- | --- | --- |
| Monetary conditions | Inflation | FP.CPI.TOTL.ZG | 180 |
| | Real interest rate | FR.INR.RINR | 114 |
| | Lending and deposit rates | FR.INR.LEND, FR.INR.DPST | 114 |
| | Broad money, % of GDP and growth | FM.LBL.BMNY.GD.ZS, FM.LBL.BMNY.ZG | 146 |
| Currency and reserves | Official exchange rate | PA.NUS.FCRF | 210 |
| | Real effective exchange rate | PX.REX.REER | 93 |
| | Reserves, months of imports | FI.RES.TOTL.MO | 165 |
| | Short-term debt, % of reserves | DT.DOD.DSTC.IR.ZS | 106 |
| | Current account, % of GDP | BN.CAB.XOKA.GD.ZS | 185 |
| Banks | Non-performing loans, % of loans | FB.AST.NPER.ZS | 149 |
| | Bank capital to assets | FB.BNK.CAPA.ZS | 148 |
| | Credit to the private sector, % of GDP | FS.AST.PRVT.GD.ZS | 169 |
| | Interest rate spread | FR.INR.LNDP | 107 |
| | Adults with an account | FX.OWN.TOTL.ZS | 145 |
| Capital markets | Market capitalisation, % of GDP | CM.MKT.LCAP.GD.ZS | 79 |
| | Turnover ratio | CM.MKT.TRNR | 77 |
| | Listed domestic companies | CM.MKT.LDOM.NO | 79 |
| | Equity index, annual change | CM.MKT.INDX.ZG | 81 |
| Sovereign | Interest payments, % of revenue | GC.XPN.INTP.RV.ZS | 138 |
| | Government lending or borrowing, % of GDP | GC.NLD.TOTL.GD.ZS | 138 |
| | External debt, % of GNI | DT.DOD.DECT.GN.ZS | 119 |
| | Debt service, % of exports | DT.TDS.DECT.EX.ZS | 117 |
| Capital flows | FDI inflows, % of GDP | BX.KLT.DINV.WD.GD.ZS | 197 |
| | Portfolio equity inflows | BX.PEF.TOTL.CD.WD | 140 |
| | Portfolio investment, net | BN.KLT.PTXL.CD | 180 |

**Beyond the WDI, terms first:**
- **IMF:** World Economic Outlook (government debt, projections), International Financial Statistics (policy and
  market rates, monthly), Financial Soundness Indicators (bank capital, asset quality, profitability), and the
  exchange-rate regime classification (AREAER). The IMF's data terms were read on 2026-10-18.
- **BIS:** central bank policy rates, credit-to-GDP gaps, debt service ratios, property prices. Terms to read.
- **World Federation of Exchanges:** exchange statistics. Terms to read.
- **Not used:** sovereign credit ratings (S&P, Moody's, Fitch) and bond spread indices such as J.P. Morgan's
  EMBI are proprietary; at most a link.

## Maturity

**D1, prototype.** The six templates and the tab are built on the WDI; no professional has reviewed them yet.

## Expert review

**Who to ask.** An emerging-markets macro-finance analyst (sovereign debt; a central bank or IMF background); a bank supervisor; a capital-markets professional.

**Questions to put to them:**
1. Which five numbers would you look at first to judge a country's macro-financial health, and over what horizon?
2. Which of the measures above mislead for frontier and low-income economies (market capitalisation where the
   market is tiny, for instance)?
3. What is missing that matters: the exchange-rate regime, dollarisation, a parallel-market premium, arrears?
4. Which public sources do you trust for policy rates and yields?
5. Do practitioners use published benchmarks (reserve adequacy, bad-loan levels) worth showing as context, and who
   publishes them?
6. How should data of different ages sit side by side?

**Consultations so far:** recorded in `60 Private` (names stay private); see [Expert Consultation](<../ASI 08 Status and Roadmap/Expert Consultation.md>).

## Backlog, in order

1. **A template set** in athena-core: monetary conditions, currency and reserves, banks, capital markets,
   sovereign, capital flows (first position: the Economy dimension's external and financial-sector blocks move
   here).
2. **A Finance tab** on the site, for every state, with each figure's period and source.
3. **The IMF IFS and FSI adapters**, whole databases (P38), for policy rates and bank soundness.
4. **A first review** by a macro-finance professional.
5. **A backtest:** do the finance measures anticipate monetary crises where the composite did not?
   See [BT4 Monetary Crises](<../ASI 05 Verification/Backtests/BT4 Monetary Crises.md>). It is written down before it is run.

## Implemented in

[ASI Finance Section](<ASI Finance Section.md>) and its six blocks.

## Inputs and outputs

- **In:** publishers' databases through Athena's adapters
- **Out:** the dimension's sections, for any country

## Where it stands

Built at D1 (athena-core #17): six templates and the Finance tab; no review yet.

## Related

[BT4 Monetary Crises](<../ASI 05 Verification/Backtests/BT4 Monetary Crises.md>) · [Dimension Economy](<Dimension Economy.md>) · [Expert Consultation](<../ASI 08 Status and Roadmap/Expert Consultation.md>)
