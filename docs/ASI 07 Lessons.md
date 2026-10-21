---
type: project-section
project: "African Stability Index"
section: "07 Lessons"
status: live
created: "2026-10-19"
updated: "2026-10-19"
pairs: ["overlapping-bands-chain-into-one-tier (athena-data)"]
---

# ASI 07 Lessons

The ASI's lessons, one per finding, each paired with a note in the Page Library where it is new.

## Lessons

- **A grouping rule can collapse on real data** (edition 2, step 8, 2026-10-19).
  - **What happened:** the plan's tier rule, "countries whose bands overlap form a tier", put all 54 states in one
    tier at 2024, 2023 and 2015. The bands were a median of 42 places wide, so every band overlapped its neighbour's.
  - **Evidence:** a probe on the committed panel, before any code was written (`methodology/EDITION_2.md`, step 8).
  - **Rule:** run a grouping rule on the data before it enters the plan; prefer a rule with an anchor. The owner
    chose the leader rule (P96), which gives three or four tiers in every year.

## Paired concept pages

- overlapping-bands-chain-into-one-tier (athena-data)

## Next time

- Test every presentation rule of the plan (tiers, classes, thresholds) on the committed panel when it is written,
  not when its step is built.
