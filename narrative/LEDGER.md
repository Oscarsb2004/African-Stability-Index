# Narrative Ledger

The document future runs read before doing anything. Machine-readable twin:
`narrative/state.yaml`.

*Seeded 2026-08-09. Research runs so far: Mauritius, Ghana, Algeria (all CREATE).*

---

## How this works

One country per run. The rotation decides the mode:

| Iteration | Mode | What it does |
|---|---|---|
| 1 | CREATE | Build the baseline record from the blueprint |
| 2, 3 | EXPAND | Add depth, periods, sources; remove what no longer holds |
| **4** | **AUDIT** | **Add nothing.** Open every citation, hunt fabrication, recheck prose against the index, recount framing balance |
| 5-7 | EXPAND | ... |
| 8 | AUDIT | and every 4th run thereafter |

An audit is forced early if a single run inflates the citation count by more than
50%. Rapid growth is when fabrication is most likely and least visible.

---

## Status

**3 of 54 countries have a record (Mauritius, Ghana, Algeria). 6 of the first pass remain.**

### First pass — 9 countries

Chosen for variance rather than convenience: if the metaprompt has a flaw, these
nine surface it. Top and bottom of the index, island and landlocked, four
language traditions, active conflict and long stability, and the two countries
whose ranks swing hardest with the weighting method.

| ISO3 | Country | Why this one | Status |
|---|---|---|---|
| MUS | Mauritius | top of the index; island state; long democratic continuity | **done — iteration 1** |
| GHA | Ghana | mid-high; Anglophone West Africa; repeated peaceful transfers of power | **done — iteration 1** |
| DZA | Algeria | rank swings 9-45 with weighting method; Arabophone; hydrocarbon economy | **done — iteration 1** |
| COD | Democratic Rep. Congo | bottom decile; vast and low-coverage; long conflict history | backlog |
| SOM | Somalia | lowest ranks; state reconstitution; sparse data is the hard case | backlog |
| BWA | Botswana | high and stable; landlocked; resource governance counter-example | backlog |
| NGA | Nigeria | largest population; federal; mixed signals across pillars | backlog |
| RWA | Rwanda | strong development indicators alongside contested governance | backlog |
| TCD | Chad | Sahel; 2021 coup; the worked example used in the blueprint | backlog |

### Backlog — the remaining 45

Listed in full in `narrative/state.yaml` under `backlog`. They are recorded
explicitly rather than left implicit: a country with no record should be visibly
absent, not quietly missing.

Egypt, Libya, Morocco, Sudan, Tunisia, Benin, Burkina Faso, Cabo Verde, The Gambia, Guinea, Guinea-Bissau, Cote d'Ivoire, Liberia, Mali, Mauritania, Niger, Senegal, Sierra Leone, Togo, Angola, Cameroon, Central African Republic, Republic of Congo, Equatorial Guinea, Gabon, Burundi, Djibouti, Eritrea, Ethiopia, Kenya, Malawi, Mozambique, South Sudan, Tanzania, Uganda, Zambia, Zimbabwe, Lesotho, Namibia, Eswatini, South Africa, Comoros, Madagascar, Seychelles, Sao Tome & Principe

---

## Run log

Append one line per run: date, country, mode, what changed, what was removed.

- **2026-08-09 — MUS — CREATE.** Full baseline built: historical overview, colonial
  legacy (expands context/colonial_history.yaml with the political consequence of
  indentured labour and the Chagos detachment/return), 4 key_periods, 6 pillar
  summaries (Pillar C correctly left empty — greyed at 1/8 measured), 3 primary +
  1 extended recent items, 3 events. 11 sources opened and read directly (not
  from memory): 4 Wikipedia, 3 news, 4 official (IMF, WHO, UNDP, UK Parliament).
  `narrative_check.py --country MUS` passes with 0 errors, 0 warnings.
  `--links` passes with 0 errors, 3 warnings (IMF/UNDP/UK-Parliament block
  scripted HTTP requests with 403; confirmed manually that all three resolve in
  a browser and match their cited content). Nothing removed — this is the first
  pass. Balance: 1 positive, 1 negative, 2 mixed, explained in `balance.note`
  rather than forced even.
  **Bug found and fixed in the process:** `scripts/narrative_check.py --links`
  reported all 10 real citations as unreachable. Root cause was local SSL
  certificate verification failing against valid HTTPS sites — the same
  environment issue already documented and worked around in `01_pull.py`
  ("Windows SSL fix"). Fixed the same way, plus added a HEAD→GET fallback and
  now distinguishes a genuine dead link (error) from a site blocking scripted
  requests with HTTP 403 (warning, check manually) — the previous version
  would have reported real news/official citations as fabricated.

- **2026-08-09 — GHA — CREATE.** Full baseline built: historical overview,
  colonial legacy (expands context/colonial_history.yaml by connecting
  colonial-era gold/cocoa extraction directly to the present galamsey
  mining crisis, and adding Nkrumah's OAU/Pan-Africanism role as a positive
  counterweight to his authoritarian domestic turn), 4 key_periods, 6 pillar
  summaries (Pillar C correctly left empty — greyed at 1/8 measured). 11
  sources opened and verified: 5 Wikipedia, 3 news, 2 official/academic
  (IMF, Center for Global Development, Africa Center for Strategic
  Studies). `narrative_check.py --country GHA` passes 0 errors after one
  fix (pillars.G was 8 words under the 80-word floor; fixed by adding a
  real fact -- rural/northern electrification gap -- not padding).
  `--links` passes 0 errors, 2 warnings (allafrica, IMF: same HTTP-403
  bot-detection pattern seen on the MUS run, confirmed manually to be real,
  live sources). Balance: 2 positive, 1 negative, 1 mixed -- the galamsey
  crisis (negative, still unresolved) sits against the December 2024
  election and a December 2025 forest-reserve mining restriction
  (positive), with the Eurobond restructuring coded mixed because it is
  recovery from a 2022 default, not the absence of one.

---

## Meta-notes

Things a future run should know about how to work, not about a specific country.

- **2026-08-09** — System built: blueprint, schema, validator, this ledger.
- **2026-08-09** — First CREATE run (Mauritius) surfaced a real bug in the link
  checker (see run log), fixed before the second run. Second run (Ghana)
  confirmed the fix holds under a different set of blocked domains, and the
  word-count floor caught a genuinely thin section rather than being a false
  positive. Next country: Algeria (DZA), also a CREATE run -- note DZA is one
  of the two countries flagged in methodology/MANUAL_REVIEW.md item 9a for
  wild rank swings across weighting methods (9th-45th), which the research
  should surface and explain rather than smooth over.
- **2026-08-09** — The schema has no `colonial_legacy_citations` check even
  though that field makes citable claims (see pending format proposals below).
  Populate the field anyway on future CREATE runs for consistency; do not treat
  its absence from validation as license to leave it uncited.
- **2026-08-09** — Three CREATE runs in (MUS, GHA, DZA) and the link-checker fix
  keeps holding across new bot-blocked domains without a false negative. Next
  country: DR Congo (COD) — bottom-decile, vast, low-coverage; expect much
  thinner sourcing and more greyed pillars than the first three, which is a
  useful contrast to log rather than something to route around.

---

## Pending format proposals

A run that believes the blueprint should change writes the proposal here and
stops. It does not edit the blueprint. Self-modifying format is how a corpus
becomes unauditable.

- **2026-08-09 (from MUS CREATE run):** `asi/narrative/schema.py validate()`
  checks `historical.overview_citations` and `key_periods[].citations` but has
  no equivalent check for `colonial_legacy_citations`, even though
  `colonial_legacy` is a substantial prose block making citable claims (which
  colonizer, which years, sourced historical facts). Suggest adding the same
  `check_refs()` call used for `overview`. Not applied — awaiting a human
  decision, per the self-modifying-format rule above.
