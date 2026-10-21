---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-20"
updated: "2026-10-20"
---

# ASI Data Section

> [!abstract] Goal
> A statistical workspace beside the map: any series of the whole databases, for any states and groups of states, in many kinds of chart, with the statistics that describe them (P105).

## Why it exists

The owner asked for the Data sub-tab of Stability to become its own heading, linked with every other tab but built
around statistical analysis: remove any state, choose a whole REC, average any set of states and compare it with
another, more kinds of chart, and categories for continent-wide bar charts.

## Precise objectives

1. Every series covering at least 20 member states since 2000, found by search: 1,759 at the first build (WDI
   1,435, ASI 134, UCDP 58, HDR 40, WEO 39, WGI 36, CPI 15, Glottolog 2), one small file each, loaded on demand.
2. A selection of states and whole groups: the owner's eight RECs (P106), 17 organisations, every category value,
   and groups the reader makes. Any item can be removed, the first included.
3. A group shown as its members, or as its average (mean of states by default; median, or weighted by population or
   GDP), drawn where at least half the members have a value. Comparisons with an interval; shared members named.
4. Fourteen views: lines, small multiples, slope, dumbbell, distribution, every state in order with intervals (tiers,
   never ranks), heatmap, scatter, trajectory, pillar profile, composition, categories, REC overlaps (UpSet), table.
5. Statistics by stated formulas, read as descriptions: change and volatility, σ- and β-convergence, the measure
   against income, neighbours and Moran's I, the states most alike on the pillars.
6. The map shows the workspace's measure; a click adds or removes a state; the view lives in the address.

## Inputs and outputs

- **In:** athena-core `09_explore.py`: `explore/catalogue.json`, `explore/s/<dataset>/<code>.json`,
  `groups.json`, `states.json`, `languages.json`
- **Out:** the Data tab

## Where it stands

Built in athena-core #35. Each state counts once and none is treated differently for being small, an island or
data-poor (P105). Not yet built: a diverging map palette for measures with both signs (it needs its own validated
ramp), and membership by year (the charts use members as they stand today, and say so).

## Related

[ASI Stability Section](<ASI Stability Section.md>) · [ASI Appraisals](<ASI Appraisals.md>) · [ASI Wonders Section](<ASI Wonders Section.md>)
