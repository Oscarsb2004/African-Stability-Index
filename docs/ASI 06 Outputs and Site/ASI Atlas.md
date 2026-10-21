---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# ASI Atlas

> [!abstract] Goal
> Present the ASI as a satellite atlas of Africa with five sections (Stability, Economy, Finance, Infrastructure, Wonders) and a country panel on the right, replacing the Dash site once it shows everything the old one does (P55, P59).

## Why it exists

The owner asked for a glossier, map-first site: real satellite imagery zoomable deep into a country, borders, the
name only on hover, no highlight colour, and more than the index itself. Python writes static JSON; the site is a
static build, on the same stack as the Canada atlas.

## Precise objectives

1. Stack: React 19, Vite 7, MapLibre GL 5, versions pinned (`projects/asi/web`).
2. Data: `05_web.py` writes `web/public/{geo,data}`; nothing is fetched at run time except imagery.
3. Every source shown in the site's sources list, with its licence.
4. Parity with the Dash site before it replaces it (P59).

## Inputs and outputs

- **In:** `data/sections.json`, the panel, Natural Earth, the imagery provider
- **Out:** the static site

## Where it stands

Built as a prototype (athena-core #15, merged; round 2 in #17).

## Related

[ASI atlas plan](<../ASI 01 Goals and Rulings/ASI atlas plan.md>) · Canada Economic Atlas (athena-data)
