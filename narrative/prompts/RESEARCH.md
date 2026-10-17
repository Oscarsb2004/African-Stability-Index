# Country Research Metaprompt

Run this manually, one country at a time. It has three modes; which one applies
is decided by the rotation, not by preference — see `narrative/LEDGER.md`.

> Kept as one file rather than three. The historical, recent and audit passes
> share most of their rules, and three files sharing 70% of their content drift
> apart — which is the failure this project has already had once, in
> `references.md`.

---

## How to invoke

This is **not** a terminal command. It is a message you paste into a Claude Code
session, which then does the web research and writes the file.

Paste this, replacing `<ISO3>`:

```
Read narrative/BLUEPRINT.md and narrative/prompts/RESEARCH.md.
Read narrative/state.yaml and find <ISO3>.
Run the mode the rotation gives for its next iteration.
Use web search — do not write from memory.
Write narrative/countries/<ISO3>.yaml, then update state.yaml and LEDGER.md.
```

Two things around it **are** ordinary terminal commands — plain Python reading
local files, no model involved:

```bash
python scripts/country_facts.py <ISO3>          # run BEFORE: what the index says
python scripts/narrative_check.py --country <ISO3>   # run AFTER: does it validate
```

Do not proceed to a second country until the validator passes on the first.

### Which model to run this on

| Mode | Model | Why |
|---|---|---|
| CREATE, EXPAND | **Sonnet** | Web-grounded research and writing is what it is best at, and this is the bulk of the work. Opus is not meaningfully better at summarising a source it has just opened. |
| AUDIT (every 4th) | **the strongest available** | Detecting one's own fabrication is harder than producing it. This is the one pass where reasoning strength changes the outcome. |
| link/format checks | Haiku, or just the validator script | Mechanical. |

Do **not** run CREATE or EXPAND on Haiku. Citation discipline and the
"leave greyed pillars unwritten" rule are precisely where a weaker model slips,
and every slip becomes audit debt later — a false economy.

---

## Rules that apply in every mode

1. **Search the web. Do not write from memory.** Your training data is stale and
   confidently wrong about recent African politics in particular. Every claim
   traces to a source you actually opened in this session.

2. **A citation you did not open does not exist.** Do not reconstruct a URL that
   "should" be right. Wikipedia article titles you half-remember are the most
   common fabrication in this task.

3. **Check what the index says before describing a pillar.** Run:
   ```
   python scripts/country_facts.py <ISO3>
   ```
   It prints each pillar's score, reliability tier and the indicators behind it.
   If a pillar is greyed, leave its summary empty — writing about it asserts more
   than the data supports, and the validator will reject the file.

4. **The prose must match the numbers.** If Pillar D scores 31 and falling, do
   not write that health outcomes are improving. If they diverge, say so and
   explain why — that divergence is often the most interesting thing on the page.

5. **Word limits are upper bounds.** See `LIMITS` in `asi/narrative/schema.py`.

6. **Framing.** Document conflict and fragility plainly. Attribute structural
   causes where the evidence supports it rather than implying inherent
   dysfunction. Give documented gains the same evidentiary standard as documented
   failures. Do not manufacture balance — if a decade was genuinely bad, say so
   and explain the asymmetry in `balance.note`.

7. **Never invent a number.** Quantitative claims come from the index or from a
   cited source, never from your own estimate.

---

## Mode: CREATE (iteration 1)

Build the baseline record from the blueprint.

Sequence:
1. `python scripts/country_facts.py <ISO3>` — know what the index says first.
2. Read `context/colonial_history.yaml` for this country. Your
   `historical.colonial_legacy` **expands** that entry; it does not restate it.
3. Search for: the country's modern political history; its independence and
   post-independence trajectory; the two or three periods that most shape its
   present.
4. Write `historical.overview`, `colonial_legacy`, and 3–5 `key_periods`.
5. Write a summary for each **non-greyed** pillar, tied to what its indicators
   actually show.
6. Search current news. Write exactly 3 `recent.primary` items, each with a
   publication date and both a news and a Wikipedia URL where both exist.
7. Add `events` for anything that would explain a visible turn in the time
   series — coups, elections, peace deals, currency collapses.
8. Fill `balance` by counting what you wrote.

Aim for a record that is complete rather than exhaustive. Later iterations add
depth; this one establishes the skeleton.

---

## Mode: EXPAND (iterations 2, 3, 5, 6, 7, ...)

Read the existing record first. Then improve it. In rough priority order:

- Fill gaps named in `meta.next_action` — that note was written by the last run
  precisely so this one would not have to guess.
- Add depth where a section is thin: another key period, a driver behind a
  pillar score, a second source for a load-bearing claim.
- Refresh `recent`: drop items that are no longer developing, promote from
  `extended` to `primary`, search for what has happened since `last_updated`.
- Improve weak citations — replace a general article with the specific one that
  actually supports the sentence.

**Expanding includes removing.** If a claim no longer holds, or a source turns
out not to support it, delete it. A record that only ever grows is a record that
accumulates errors.

End by writing a specific `meta.next_action`. "Add more detail" is not an
instruction; "the 1990s civil war period is one sentence and uncited" is.

---

## Mode: AUDIT (every 4th iteration)

**Add no new content.** This pass exists because an iterative loop with a
self-updating instruction file trends toward "add more" indefinitely, and
nothing else in the process pushes back.

1. **Open every citation.** For each, confirm the URL resolves and that the page
   actually supports the claim citing it. Set `verified: true` only for those you
   opened in this session. Delete any claim whose source does not support it, and
   say what you removed in the ledger.
2. **Hunt fabrication.** Dates, names, numbers, and institution names are where
   invention concentrates. Verify each against a source.
3. **Check prose against the index.** Re-run `country_facts.py` and confirm every
   pillar summary still matches its score and tier. Scores change when the panel
   is rebuilt; prose written against last year's numbers goes silently wrong.
4. **Check framing balance.** Recount `balance`. If negative items outnumber
   positive ones with no documented positives at all, search specifically for
   developments the record has missed. If there genuinely are none, write that
   finding into `balance.note`.
5. **Check distinctiveness.** Read the record beside another country's. If the
   pillar summaries could be swapped without anyone noticing, they are generic
   and need rewriting against this country's actual data.

Record what the audit changed in `LEDGER.md`. An audit that reports "no issues
found" on a model-written corpus is more likely to be an audit that did not look.

---

## After every run

Update, in this order:

1. `narrative/countries/<ISO3>.yaml` — the record
2. `narrative/state.yaml` — `iteration_count`, `last_updated`, `next_action`,
   move the country out of `backlog` if this was its CREATE run
3. `narrative/LEDGER.md` — one line: date, country, mode, what changed
4. `python scripts/narrative_check.py --country <ISO3>` — must pass

If you believe the blueprint itself should change — a new field, a different word
limit, a section that is not earning its place — **do not change it**. Write the
proposal under `pending_format_proposals` in `state.yaml` and leave it for a
human. Self-modifying format is how a corpus becomes unauditable.
