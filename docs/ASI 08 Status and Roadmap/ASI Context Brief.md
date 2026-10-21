---
type: project-page
project: "African Stability Index"
section: "08 Status and Roadmap"
status: planned
created: "2026-10-20"
updated: "2026-10-20"
sources: ["the owner's ruling P102 (2026-10-20)", "athena-core projects/asi methodology/EDITION_2.md, step 10", "athena-core tag archive/narrative-2026-10"]
---

# ASI Context Brief

> [!abstract] Goal
> Give each state's data narrative a short, sourced context: its history since independence, its colonial legacy
> and its regional blocs, with every claim cited to a source whose terms allow reuse and checked against it.

**For later, by the owner's ruling (P102, 2026-10-20):** "changing the historical information for each country will
be a significant undertaking and a lot of prompting over a long time horizon ... leave the context to the African
Stability Project ... I will do those later, after Athena has been built". Step 10's recent events (part C) are
skipped. This note holds the instructions until then.

## Why it exists

The data narratives of step 10, part A (athena-core #28) say what each state's scores show, from the panel alone. They
cannot say why. Edition 1's narratives tried to, with 31,477 lines of researched prose that were never verified, and
they were archived at P3 (Trim Ledger C2, P80).

## What each state gets

- **History:** about 150 to 250 words, from independence to the reference year. Name the events that bear on the
  pillars (coups, wars, elections, economic crises, disasters), each with its year.
- **Colonial legacy:** about 100 to 150 words, on the colonial powers and the extraction, borders and institutions
  they left.
- **Regional blocs:** each membership with the year joined (and left), matching the blocs in `asi/core/countries.py`
  (`COUNTRIES[iso3]["rec"]`).
- **Citations:** every claim names its source, the page or section, the URL and the date it was read.

## How to do it

1. **Sources first.**
   - Read and date each source's terms in Sources (athena-data) before using it (AGENTS.md).
   - Prefer publishers whose terms allow reuse: CC BY, public domain, or explicit permission. Examples are the World
     Bank, UN bodies, and the African Union's own pages for bloc membership.
   - **Wikipedia is CC BY-SA 4.0:** text derived from it must carry the same licence. Use it for leads, and cite the
     sources it cites.
   - **Never used:** paywalled sources, sources whose terms are unclear, and model-written text.
2. **Pilot two states before the other 52,** one among the most stable and one among the least. The owner reviews
   the pilot, and the template follows from it.
3. **One claim per sentence where possible,** each with its citation id.
4. **A second pass checks every claim against its source.** This is the owner, or a researcher agent after December
   (P87), one query at a time. A claim that cannot be checked is cut.
5. **Store it in the project:** `projects/asi/narrative/context/<ISO3>.yaml` in athena-core, validated by a schema.
   - `08_narratives.py` merges it into `narratives.json`.
   - `verify/narrative.py` checks that every citation id resolves, and that every year in the text appears in its
     citation's record.
6. **Run the library routine** (the `athena-library` skill): search the Page Library first, and file a page for
   "cited text, claims checked" once a second project needs one.

## What to start from

- **Leads, never sources:**
  - edition 1's country files and their blueprint, in athena-core's tag `archive/narrative-2026-10`
    (`projects/asi/narrative/countries/*.yaml`, `BLUEPRINT.md`);
  - the vault's [ASI Context - Colonial History](<../ASI 04 Methods/ASI Context Texts/ASI Context - Colonial History.md>) and [ASI Context - Country Facts](<../ASI 04 Methods/ASI Context Texts/ASI Context - Country Facts.md>), marked "Research text, not
    verified".
- **The data narrative each context sits beside:** `data/panel/narratives.json` (step 10, part A).

## Where it stands

Planned, for after Athena is built (P102).

## Open questions

- Which two states form the pilot?
- Do the word limits suit the site's country panel?
- Does the colonial legacy stay as its own part, or join the history?
