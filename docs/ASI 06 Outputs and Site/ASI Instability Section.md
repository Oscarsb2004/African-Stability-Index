---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "live"
created: "2026-10-23"
updated: "2026-10-23"
---

# ASI Instability Section

> [!abstract] Goal
> Show the continent's worsening conflicts: where organised violence is, how fast it is growing or spreading, which armed groups are reaching new ground, who backs whom, and which states may be drawn in.

## Why it exists

The owner, 2026-10-23: a new tab, "Spreading instability", to look at the worsening conflicts, the Sahel (Mali) and a possible war between Ethiopia and Eritrea first. Each state should have its links to others (who funds whom), and the states that may be drawn into a pure conflict zone should have a likelihood from a prediction market. The rulings of that day are in [ASI 01 Goals and Rulings](<../ASI 01 Goals and Rulings/ASI 01 Goals and Rulings.md>).

## Precise objectives

1. **Theatres:** the owner's list (`registry/theatres.yaml`), each a set of member states shown together.
2. **Events:** UCDP's georeferenced events. GED runs to the end of its last annual release; the provisional Candidate Events follow month by month, each with UCDP's own flag (`code_status`).
3. **Figures, all derived by stated rules (P4):**
   - deaths by month: the sum of UCDP's best estimates, with UCDP's low-to-high range for the last twelve months;
   - spread: first-level areas (ADM1) with a deadly event in the last twelve months, against the twelve before;
   - new ground: an identified armed group with events in a state where it had none since 2010. A group UCDP has not identified (written XXX) cannot be followed.
4. **Links:** `registry/links.yaml`, the owner's compilation; every card is cited and ruled on.
5. **Markets:** a prediction market's price, only by its platform's own id, its terms read first (plan 4.6).
6. **Never drawn by us:** no frontline, no route, no forecast of our own.

## Inputs and outputs

- **In:** `ucdp-ged-26.1`, `ucdp-candidate-26.01.26.09`; `registry/theatres.yaml`, `registry/links.yaml`
- **Out:** `web/public/data/instability.json`, `web/public/geo/events.json` (written by `11_instability.py`)

## Where it stands

Built on 2026-10-23 (plan 4.5), over October 2025 to September 2026:
- 8 theatres: the Sahel and the coastal states, Sudan and its neighbours, Ethiopia and Eritrea, Somalia and the Horn, the eastern DRC and the Great Lakes, the Lake Chad basin, Libya, northern Mozambique.
- 6,554 events in member states over the window, 97,240 deaths (UCDP's best estimates).
- The Sahel: 6,003 deaths against 7,967 the year before, yet 48 first-level areas with a deadly event against 43; JNIM's first event in Ghana since 2010.
- Sudan: 68,222 deaths (UCDP's range 14,402 to 84,233), most of them in two events UCDP records at El Fasher on 25 October 2025 (best estimates 32,505 and 24,173).

Waiting: the prediction markets (4.6, terms first); Sudan's town-by-town control from Wikipedia's map, if its data can be read (CC BY-SA); the owner's rulings on the theatres and links.

## Related

[ASI Infrastructure Section](<ASI Infrastructure Section.md>) · [ASI Project Plan](<../ASI 08 Status and Roadmap/ASI Project Plan.md>)
