---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# Wonders Selection

> [!abstract] Goal
> Choose the wonders by a rule anyone can rerun, so the list reflects the world's attention rather than one person's taste.

## Why it exists

A hand-picked list is hard to defend and easy to bias; a rule makes every inclusion explainable.

## Precise objectives

1. First position: a candidate is a place in the 54 states that is on UNESCO's World Heritage List, or a Wikidata item of a listed class (mountain, volcano, waterfall, lake, river, desert, rainforest, national park, archaeological site).
2. Rank candidates within each class by the number of Wikipedia language editions with an article on them (Wikidata sitelinks), a reproducible measure of global notability.
3. Take the top of each class to about 40 wonders, at least one in each of Natural Earth's subregions of Africa (from 2026-10-20; edition 1's own six regions are not carried over, P105).
4. The owner may add or remove a wonder; each change is recorded with its reason.

## Applied (2026-10-18, athena-core `07_wonders.py`)

- **Parameters:** 15 World Heritage Sites, 3 per class, at least one per region, items described in at least 10
  Wikipedia languages; classes mountain, volcano, waterfall, lake, river, desert, rainforest, canyon, national park,
  archaeological site (direct instances or one subclass step).
- **Under Natural Earth's subregions (2026-10-20):** the same 42, in the same order, recomputed from the cache.
- **Result:** 42 wonders in all six regions, from 2,572 candidate rows (1,702 items). Among them: Kilimanjaro, the
  Nile, the Sahara, Victoria Falls, the Pyramids of Giza, Timbuktu, the Serengeti, Great Zimbabwe, Leptis Magna,
  the Rainforests of the Atsinanana.
- **For the owner to review:** Cairo and Rabat enter as whole cities, because their Wikidata items carry the World
  Heritage listing; `WONDERS_OWNER` can replace them with specific sites.
- **Query note:** asked state by state; per-class queries across all 54 timed out on Wikidata's public service.

## Inputs and outputs

- **In:** Wikidata (CC0); the World Heritage List (terms to read)
- **Out:** the wonders list

## Where it stands

Built: the rule applied on 2026-10-18; the owner may edit the list.
