---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# Dimension Economy

> [!abstract] Goal
> Describe the real economy of any country: what it produces, how prices move, what the state collects and owes, what the economy is made of, how people work, and where forecasters expect it to go.

## Why it exists

The owner asked for an economic outlook beside the index (P56), built from shared section files (P54).

## Precise objectives

1. Answer these questions for any country: How big is the economy and how fast and steadily does it grow? How fast do prices rise, and how bad has it been? Can the state pay its way? What is the economy made of? What do forecasters expect?
2. Move up one maturity level at a time ([Expert Consultation](<../ASI 08 Status and Roadmap/Expert Consultation.md>)), each move earned by a review.
3. Every measure comes from a publisher whose terms are read; nothing is flagged by a threshold of our own (P60).

## What it measures

The shared templates (System Sections and Figure Shells (athena-data)): output and growth, prices and inflation, public
finances and debt, structure, jobs, and the outlook once the IMF WEO is in Athena. First position: the external
position and the financial sector move to [Dimension Finance](<Dimension Finance.md>).

## Maturity

**D1, prototype.** Built for the 54 states on the WDI (2,314 of 2,430 figures with a value); no outside review yet.

## Expert review

**Who to ask.** A macroeconomist with a central bank, finance ministry or IMF Article IV background; a development economist.

**Questions to put to them:**
1. If you could see five numbers about an economy, which would they be?
2. Which of ours mislead for low-income or commodity economies?
3. How should a forecast be shown beside history, and which forecaster do you trust?
4. Are the three highest inflation years at least three years apart the right way to show the record?
5. What does the panel get wrong in how it reads?

**Consultations so far:** recorded in `60 Private` (names stay private); see [Expert Consultation](<../ASI 08 Status and Roadmap/Expert Consultation.md>).

## Backlog, in order

1. The outlook from the IMF WEO, whose data is now ingested ([Economy Outlook](<ASI Economy Section.md#the-parts>)).
2. A first review by a macroeconomist.
3. The Canada atlas's binding (Canada Economic Atlas (athena-data)).

## Implemented in

[ASI Economy Section](<ASI Economy Section.md>) and its blocks; the templates in athena-core.

## Inputs and outputs

- **In:** publishers' databases through Athena's adapters
- **Out:** the dimension's sections, for any country

## Where it stands

Built as a prototype (athena-core #15).

## Related

[ASI Economy Section](<ASI Economy Section.md>) · [Expert Consultation](<../ASI 08 Status and Roadmap/Expert Consultation.md>)
