---
type: "project-page"
project: "African Stability Index"
section: "08 Status and Roadmap"
status: "live"
created: "2026-10-23"
updated: "2026-10-23"
---

# ASI Project Plan

> [!abstract] Goal
> Finish the ASI as an Africa-only project with the dimensions it has. Bring each dimension to a reviewed state, publish edition 2, and hand the project to the Library. A model of the world comes later, as a project of its own branched from this one.

## Why it exists

The owner, 2026-10-23: "keep this project limited to africa. We can branch this off and create a model of the world later on". The owner also said we don't necessarily need to keep extending the dimensions. Until now each step has added more, so the project has had no edge. This plan draws that edge: what is still to come, what is cut, and when the ASI is done.

## The scope, from now on

> [!note] Amended the same day (2026-10-23)
> The owner added a sixth tab, "Spreading instability", with links between states, recent conflict events and
> prediction-market prices; non-African states appear only as thin outlines and as the far end of a link into Africa.
> The rulings are in [ASI 01 Goals and Rulings](<../ASI 01 Goals and Rulings/ASI 01 Goals and Rulings.md>); the
> build is phase 4 below.

1. **Africa only.**
   - The site shows the 54 member states and their waters. Other states appear only as thin outlines, and as the far end of a link into Africa (amended).
   - A source may still be ingested whole into the store (P38). PortWatch's worldwide ports are one example. What is shown is cut to Africa by a stated rule.
2. **No new dimensions beyond six.** The five below, the Data tab, and "Spreading instability" (amended):
   - Stability (the index);
   - Economy;
   - Finance;
   - Infrastructure;
   - Wonders.

   The work left deepens and finishes these. A new indicator or source is added only when a review asks for it, or to finish a step already planned below.
3. **A world model is a new project.**
   - It is branched from the ASI once the ASI is done, as the Türkiye atlas was forked from the Canada atlas.
   - It reuses athena-kit's adapters, which already read whole databases (PortWatch, the World Port Index, the WDI).
   - Nothing in the ASI is generalised for it in advance.

## Where each part stands (2026-10-23)

| Part | Built | Still to do in this project |
| --- | --- | --- |
| **Stability** | Edition 2 steps 1 to 9, part A of step 10 (the data narratives) and the backtests (v2), shown on the site at 2024 | Publication (the owner's). Step 10 part B (context) is left for Athena. Part C is skipped (P102). BT3 (coups) and BT7 (real-time replay) wait on their data |
| **Economy** | Five section templates (D1) | One review |
| **Finance** | Six section templates (D1) | One review |
| **Infrastructure** | Cities; ports and export hubs; mines, deposits and exploration sites; rail, roads and the grid; national figures (services, power, logistics, resources, producer prices); shipping (PortWatch's 196 ports in member states and its chokepoints) | Africa's chokepoints only (1.1); I6; I8; I10, the review |
| **Wonders** | 42 wonders with photographs; languages (D1) | One review |
| **Data tab** | 1,895 measures, groups, each state's categories and languages | A diverging palette for measures with both signs (1.4) |
| **The site** | Six tabs, the country panel, the method page | The switch from edition 1 to edition 2 on GitHub Pages ([ASI Atlas Publishing](<../ASI 06 Outputs and Site/ASI Atlas Publishing.md>)) |

## The plan

### Phase 1: finish what is started (Africa only)

| # | Work | Size | Depends on |
| --- | --- | --- | --- |
| 1.1 | **Africa's chokepoints only.** Keep the chokepoints within 100 km of a member state's land. Four of PortWatch's 28 qualify: Suez, Gibraltar, Bab el-Mandeb and the Cape of Good Hope. The next nearest, the Bosporus, is 1,076 km away | small | — |
| 1.2 | **I6: what each state produces and sells.** Each state's major resources, its production from a publisher's commodity tables, and its exports from CEPII BACI through a declared HS crosswalk (derived), beside the WDI's rents already shown | large | — |
| 1.3 | **I8: export chains.** From a mine, by rail or road, to its exporting port, as declared joins of published segments (derived), and landlocked states' corridors to the sea | medium | 1.2 |
| 1.4 | **The Data tab's diverging palette,** validated like every ramp on the site | small | — |

### Phase 2: review each dimension (D1 to D2)

Per [Expert Consultation](<Expert Consultation.md>): one professional per dimension reviews what is measured and how it is shown, and every point gets an answer.

| # | Work | Who |
| --- | --- | --- |
| 2.1 | A one-page brief per dimension: scope, measures, a screenshot, the questions | Claude |
| 2.2 | Find a reviewer for each of Economy, Finance, Infrastructure (I10) and Wonders, and a second for Stability (D2 to D3) | the owner |
| 2.3 | Each review's advice becomes items; the owner rules on what is adopted; the changes are made | the owner rules, Claude builds |

### Phase 3: publish and hand over

| # | Work | Who |
| --- | --- | --- |
| 3.1 | A parity checklist against the live edition-1 site, ticked | Claude |
| 3.2 | Switch GitHub Pages to `edition-2` | the owner |
| 3.3 | A yearly refresh, written down: each source's next release and the command that ingests it, with its lock updated | Claude |
| 3.4 | The finished project goes to athena-data's `Library/Projects`, segmented into pages (P107) | the Cleaners, by Athena's brief |

### Phase 4: Spreading instability, links between states, and readers' own indices (added 2026-10-23)

| # | Work | Size |
| --- | --- | --- |
| 4.1 | **Country names always shown** on the map; Western Sahara drawn as a non-member (its Natural Earth code is SAH) | small |
| 4.2 | **Your own index:** a builder in the Stability popup (any indicator, a stated method, a name), kept in the reader's browser, under Stability › Custom indices | medium |
| 4.3 | **UCDP's georeferenced events** in the store: GED 26.1 (1989–2025) and the Candidate Events of 2026, monthly | small |
| 4.4 | **Links between states:** every other state as a thin outline; `registry/links.yaml`, each link cited and ruled on; a link's line and card shown when its state is clicked | medium |
| 4.5 | **The "Spreading instability" tab:** theatres (the Sahel, Sudan, Ethiopia–Eritrea, Somalia, the eastern DRC, Libya, Mozambique, the Lake Chad basin), each with its events, monthly deaths, spread by a stated formula, and its links; Sudan's town-by-town control from Wikipedia's map where it can be read (CC BY-SA) | large |
| 4.6 | **Prediction markets:** Polymarket's price where a market exists, Manifold's labelled as play money where it has none, terms read first | small |

## What is not added

- **No dimension beyond the six** (the five and "Spreading instability"). Health, education, demography and the like are already indicators of a pillar, or measures in the Data tab.
- **Nothing outside the 54 member states but their links:**
  - no worldwide layers other than the thin outlines;
  - no panels or figures for non-members;
  - no comparison with other continents.
- **No new indicator in the index,** unless a review asks for one and the owner rules for it.
- **Step 10 part B (context)** is left for Athena, as its brief says. **Part C (recent events)** is skipped (P102), except UCDP's conflict events in the "Spreading instability" tab (amended 2026-10-23).
- **The archived backlog** ([ASI Backlog](<ASI Backlog.md>), from edition 1) is not worked through. Edition 2's log supersedes it. An item a review raises again comes back as a new item.

## Waiting on others, with a decision point

Each of these waits on someone outside the project. If a source is still not open when phase 2 ends, its step is cut, not carried:

| Step | Waits on | If it never opens |
| --- | --- | --- |
| I7, AID's infrastructure projects | AUDA-NEPAD's answer about republishing, and the owner's account | cut; the map keeps USGS's and the World Bank's layers |
| I3, pipelines and power stations | Global Energy Monitor's download (the owner) | cut; USGS's layers stay withheld for their commercial source |
| Wages (I5) | the owner's reading of ILOSTAT's terms | cut |
| Megaprojects | the terms of GEM and GRanD, and a selection rule | cut |
| BT3 (coups) | its dataset's terms | left as "waiting" in the backtests |

## The project is done when

1. Phase 1 is built and merged.
2. Every dimension is at D2 (reviewed), and Stability at D3.
3. Edition 2 is live on its site.
4. The yearly refresh is written down.

Then the ASI moves to the Library (3.4), and is maintained once a year (D4).

## Inputs and outputs

- **In:** the owner's direction of 2026-10-23; each section's note; edition 2's log
- **Out:** the remaining work, its order, and the point at which the project stops

## Related

[ASI 08 Status and Roadmap](<ASI 08 Status and Roadmap.md>) · [ASI Infrastructure Section](<../ASI 06 Outputs and Site/ASI Infrastructure Section.md>) · [ASI Edition 2](<../ASI 01 Goals and Rulings/ASI Edition 2.md>) · [Athena Dimensions](<../ASI 06 Outputs and Site/Athena Dimensions.md>)
