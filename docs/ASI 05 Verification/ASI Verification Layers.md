---
type: "project-page"
project: "African Stability Index"
section: "05 Verification"
status: "live"
created: "2026-10-18"
updated: "2026-10-20"
---

# ASI Verification Layers

> [!abstract] Goal
> Prove before every release that the outputs rebuild from their inputs, that an independent derivation agrees, that the frontend contract holds, and that the narrative's claims match the numbers.

## Why it exists

A pipeline that cannot reproduce itself cannot be trusted with a new edition.

## Precise objectives

1. `rebuild`: rerun stages 2 and 3 from `data/inputs.csv`; every committed output identical (CSV, JSON and YAML within 1e-12).
2. `panel`: an independent re-derivation with different tools.
3. `contract`: identities, reconciliation, ranks from scores, no hard-coded counts.
4. `narrative`: every claim in the text matches the data.
5. `advisory`: diagnostics that report and never block.
6. `verify/` never imports the code it checks (an AST test enforces it).

## Inputs and outputs

- **In:** `data/inputs.csv` and the committed outputs
- **Out:** a gate: all gating layers OK, or the release stops

## Where it stands

Live.
- **2026-10-18:** the panel layer re-derives 38,276 of 43,200 scoring cells (88.6%); the rest are regional means,
  checked by rule. The ASI's tests stand at 763 passed and 1 expected failure.
- **Edition 2:** with no regional fill, every cell with a value is re-derived. Steps 8 and 9 add checks 4.5 (the
  headline's interval, bands and tiers) and 4.6 (the effective weights).
- **The narrative layer is rebuilt at step 10, part A** (athena-core #28). `verify/narrative.py` re-derives every
  state's facts and checks that each of the 1,570 numbers in the 378 sentences of the data narratives is one of
  them. The tests stand at 292 passed, after the P3 trims removed the Dash and narrative code.

## Related

System Checks and Precision (athena-data) · [ASI Edition 1](<../ASI 01 Goals and Rulings/ASI Edition 1.md>)
