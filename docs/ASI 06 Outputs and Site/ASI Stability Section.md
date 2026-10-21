---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-18"
updated: "2026-10-20"
---

# ASI Stability Section

> [!abstract] Goal
> Show where each state stands on stability, with the ASI as one appraisal among several and a drill-down from composite to pillar to indicator.

## Why it exists

It is the index's home on the site, and the place where P53 is kept: the reader sees the ASI beside the World Bank's and others' scores.

## Precise objectives

1. Map: a translucent fill in five classes, fifths of the member states (49.0, 51.7, 55.6, 62.7 at 2023), from a ramp that passes the dataviz validator; switchable.
2. Panel: the ASI marked as this project's, its history, pillars, then indicators with their year or provenance.
3. Then the other appraisals on their own scales, WGI with its 90% intervals.
4. Tiers and bands, and the eight pillars of edition 2.
5. "Compare" links from the headline, every pillar and indicator into the [ASI Data Section](<ASI Data Section.md>).

## Inputs and outputs

- **In:** `stability.json`, `sections.json` (appraisals)
- **Out:** the Stability view

## Where it stands

Built on edition 1 (equal weights, 2023). **Edition 2 is shown from athena-core #31**, at 2024:
- the headline with its 95% interval, and its tier and rank band (step 8);
- the data narrative under "In words" (step 10, part A);
- a "left out" tag on a pillar the score did not use.

The point rank stays off the site. Publication is the owner's.

From athena-core #33: the page "How the index is built" (linked at the bottom and at `#method`), and each indicator's value across every state. From #35 the Data sub-tab became its own tab, the [ASI Data Section](<ASI Data Section.md>).

## Related

[ASI Appraisals](<ASI Appraisals.md>) · [ASI Pillars](<../ASI 04 Methods/ASI Pillars.md>) · [ASI Method Uncertainty and Rank Bands](<../ASI 04 Methods/ASI Method Uncertainty and Rank Bands.md>)
