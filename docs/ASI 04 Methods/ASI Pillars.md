---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# ASI Pillars

> [!abstract] Goal
> Divide stability into eight channels that are as independent as theory allows and each reach their own family of sources, so the index can grow without new overlap.

## Why it exists

Edition 1's seven pillars blur together: corrected for reliability, 12 of 21 pairs cannot be told apart, mostly
because development (income, health, education, services) is spread across four of them. The owner asked for pillars
renamed and redefined for least overlap and most reach (P52), and adopted variant B (P57).

**The three rules behind the layout:**
1. What the state does (institutions) is kept apart from what happens to people (outcomes) and from what the
   country is exposed to (forces mostly outside its control), as INFORM and ND-GAIN do.
2. Stocks are kept apart from shocks: capacity built over decades is one channel; volatility, debt and hazards are
   others.
3. Development is one factor, so it gets one pillar.

## Precise objectives

1. Every indicator sits in one pillar only.
2. Every indicator passes its pillar's umbrella test (P58).
3. No pillar pair above an HTMT of .85 (P51's target, kept as a diagnostic).
4. Each pillar reports its measurement model: reflective if its items cohere, formative otherwise.
5. The layout is rerun on edition 2's panel before publication, and the result reported whatever it is.

## The layout test (2026-10-18)

Prototype on WDI and WGI: latest real value per state in 2016–2024, ranked 0–1, equal weights. n is 52 or 53.

| Layout | Pillars | Indicators | Mean \|rho\| between pillars | Largest pair | With GDP per capita held constant |
| --- | --- | --- | --- | --- | --- |
| Edition 1's seven, one home per indicator | 7 | 26 | .456 | .77 | .227 |
| A: eight, demography its own pillar | 8 | 51 | .307 | .77 | .240 |
| **B: eight, demography inside human development (adopted, P57)** | 8 | 54 | .320 | .64 | .251 |
| C: seven, no cohesion pillar | 7 | 50 | .298 | .64 | .246 |

**Reading.** The new layouts cut raw overlap by about a third and double the reach. With GDP held constant there is
no gain: the development factor is gathered into one pillar, not removed. That is the intended trade.

## Inputs and outputs

- **In:** the candidate list (`ASI indicator candidates.csv`, 119 rows) and Athena's datasets
- **Out:** eight pillar definitions with their indicators

## Where it stands

Built at edition 2, step 6 (athena-core #14): keys GOV, VOI, SEC, MAC, EXT, HUM, COH, ENV; 50 scored indicators and 19 descriptive. Rerun on edition 2's panel at 2024: mean between-pillar |rho| .383 and the largest pair GOV–VOI .80 (the prototype gave .320 and .64); parallel analysis keeps one factor, with GDP held constant too.

## Open questions

- Governance and Voice are the closest pair (.64); they stay apart to keep capacity and legitimacy distinct.
- Several pillars are formative (inner |rho| .14 to .22); each must still pass its umbrella test.

## Related

ASI Building Distinct Pillars.pdf (athena-data) · [ASI Method Pillar Distinctness](<ASI Method Pillar Distinctness.md>) · [ASI Definition of Stability](<ASI Definition of Stability.md>)
