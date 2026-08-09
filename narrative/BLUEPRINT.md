# Narrative Blueprint

**What every country receives.** One structure, 54 times, so the interface can
render any country without special cases and the audit pass can check any country
against one specification.

Enforced by `asi/narrative/schema.py`. Run `python scripts/narrative_check.py`
before committing narrative work — a record that fails validation does not ship.

---

## Why the narrative layer exists

The quantitative index says Chad ranks 51st. It cannot say why. The answer lives
in colonial extraction patterns, commodity dependence, Sahel security spillover,
and a coup in 2021 — and without it the index is a league table, which is the
least interesting thing it could be.

So this layer is not decoration. It is the half of the project that turns a
ranking into an explanation.

---

## File

`narrative/countries/{ISO3}.yaml` — one per country.

```yaml
meta:
  iso3: TCD
  name: Chad
  last_updated: 2026-08-09        # ISO date
  iteration_count: 1              # how many research runs have touched this file
  next_action: "expand key_periods; 1990s civil war is thin"
  model_used: claude-sonnet-5

historical:
  overview: |                     # 150-300 words, APA-style academic prose
    ...
  overview_citations: [c1, c3]
  colonial_legacy: |              # 100-250 words; expands context/colonial_history.yaml
    ...
  key_periods:
    - title: "Independence and the first civil war"
      period: "1960-1979"
      summary: "..."              # 40-150 words
      citations: [c2]

pillars:                          # one entry per pillar A-G
  A:
    summary: "..."                # 80-160 words, tied to what the indicators show
    drivers: ["weak central authority outside N'Djamena", "..."]
    citations: [c4]
  # ... B through G

recent:
  primary:                        # exactly 3 — shown by default
    - headline: "..."
      date: 2026-05-14            # publication date, required
      summary: "..."              # 40-120 words
      why_it_matters: "..."       # one sentence linking it to a pillar
      news_url: "https://..."
      wikipedia_url: "https://en.wikipedia.org/wiki/..."
      sentiment: negative         # positive | negative | mixed
  extended: []                    # up to 6 more, behind a control

events:                           # ticks on the country time slider
  - year: 2021
    type: coup                    # coup|election|conflict|peace_deal|
                                  # constitutional|economic|disaster|independence
    title: "Death of Idriss Déby; military council takes power"
    description: "..."
    url: "https://..."
    direction: deteriorate        # improve | deteriorate | mixed

citations:
  - id: c1
    url: "https://en.wikipedia.org/wiki/History_of_Chad"
    source_type: wikipedia        # wikipedia|news|academic|official
    title: "History of Chad"
    accessed: 2026-08-09
    verified: false               # set true only by an AUDIT run that opened it

balance:
  n_positive: 2
  n_negative: 4
  n_mixed: 1
  note: "Conflict dominates the recent record; 2024 census and power-grid
         expansion documented as counterweights."
```

---

## Rules that are enforced, not suggested

**Every factual claim carries a citation.** Models produce plausible,
well-formatted, nonexistent sources. An uncited sentence is treated as
unsupported and removed by the next audit.

**Recent items require a publication date.** Without one, a model's training
data is indistinguishable from current reporting. This is the single most
common way an AI-written news section goes quietly stale and wrong.

**Both a news link and a Wikipedia link where both exist.** The news item is the
event; the encyclopedia entry is the context. Readers need the second to judge
the first.

**No narrative for a greyed pillar.** If the index refused to score a pillar
because the data was too inferred, writing a confident paragraph about it
asserts more than the evidence supports. The validator treats this as an error,
not a style note.

**Word limits are upper bounds.** An unbounded model writes essays nobody reads
and that take an hour per country to audit.

**Framing balance is counted, not asserted.** Every record records how many
positive, negative and mixed items it contains. Where the evidence supports it,
documented gains belong alongside documented failures.

---

## On framing

Africa is routinely narrated as a catalogue of failures. This project documents
conflict and fragility without reducing 54 countries to them.

That is a methodological requirement, not a stylistic preference, and it cuts
both ways:

- **Do not** soften or omit coups, wars, famines, or repression. They are real,
  they matter, and the index measures them.
- **Do** attribute structural causes where the evidence supports it — extraction,
  debt architecture, commodity dependence, externally imposed borders — rather
  than implying inherent dysfunction.
- **Do** document democratic consolidation, peace agreements, and development
  gains with the same evidentiary standard applied to failures.
- **Do not** manufacture balance. If a country's decade was genuinely bad, say
  so and let `balance.note` explain the asymmetry.

The target is proportion, not omission.

---

## Style

Academic APA prose: measured, cited, no rhetorical flourish. **Not** full APA
essay format — no abstract, no reference list layout, no headings inside a
summary. Citations live in the structured `citations` block, not in the prose.

Write for a reader who is checking the index rather than being sold it.
