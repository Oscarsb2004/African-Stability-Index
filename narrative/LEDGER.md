# Narrative Ledger

The document future runs read before doing anything. Machine-readable twin:
`narrative/state.yaml`.

*Seeded 2026-08-09. Research runs so far: Mauritius, Ghana, Algeria, DR Congo, Somalia, Botswana, Nigeria, Rwanda, Chad (all CREATE). First pass complete.*

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

**9 of 54 countries have a record (Mauritius, Ghana, Algeria, DR Congo, Somalia, Botswana, Nigeria, Rwanda, Chad). The first pass is complete.**

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
| COD | Democratic Rep. Congo | bottom decile; vast and low-coverage; long conflict history | **done — iteration 1** |
| SOM | Somalia | lowest ranks; state reconstitution; sparse data is the hard case | **done — iteration 1** |
| BWA | Botswana | high and stable; landlocked; resource governance counter-example | **done — iteration 1** |
| NGA | Nigeria | largest population; federal; mixed signals across pillars | **done — iteration 1** |
| RWA | Rwanda | strong development indicators alongside contested governance | **done — iteration 1** |
| TCD | Chad | Sahel; 2021 coup; the worked example used in the blueprint | **done — iteration 1** |

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

- **2026-08-09 — DZA — CREATE.** Full baseline built: historical overview,
  colonial legacy, 4 key_periods, 6 pillar summaries (Pillar C left empty
  — greyed at 1/8 measured). 13 sources opened and verified: 5 Wikipedia,
  4 news, 3 academic/think-tank, 1 official US State Dept. Confirmed the
  exact mechanism behind the rank 9-45 swing flagged in
  `methodology/MANUAL_REVIEW.md` item 9a: Pillar F scores 4.4/100 with 3/4
  indicators directly measured (not imputed), crushing the non-compensatory
  geometric mean while PCA discounts the same pillar because it loads
  inversely against the general stability factor. Flagged a genuine
  data-provenance issue in `pillars.E`: the displaced-persons figure is a
  regional estimate, not a direct measurement of Algeria. `--links` passes
  0 errors, 2 more bot-blocked domains (france24, bloomberg) confirmed real.

- **2026-08-09 — COD — CREATE.** Full baseline built: historical overview,
  colonial legacy, 4 key_periods, 6 pillar summaries. 14 sources opened and
  verified — the most of any run so far, correcting the prior assumption
  that COD would be sparsely sourced. One genuine dead link caught and
  fixed: a World Bank PDF returned a real HTTP 404 (confirmed via `curl`);
  replaced with a working citation for the same claim (DRC ~70% of global
  cobalt supply) rather than deleting it. First run to trigger the balance
  warning as a true positive: 0 positive / 1 negative / 3 mixed, left as-is
  with `balance.note` naming two real structural counterweights outside the
  recent window (23-year +14.7-point composite gain; the 2019 first
  peaceful transfer of power). Pillar F is COD's highest-scoring pillar
  (78.4) — the mirror image of Algeria's lowest, same co2_pc wealth-proxy
  mechanism in reverse.

- **2026-08-09 — SOM — CREATE.** Full baseline built: historical overview,
  colonial legacy, 4 key_periods, 6 pillar summaries. 13 sources opened and
  verified. Corrected the DZA-run assumption that low-ranked countries mean
  low index-data coverage: like COD, only Pillar C is greyed here too — A,
  B, D, E, G all clear the reliable tier despite catastrophic scores,
  because reliability measures coverage, not severity. Genuine positive
  counterweight used at full weight: Somaliland's free, fair, peaceful
  November 2024 election, placed in `recent.primary` with an honest caveat
  that it isn't reflected in national-level governance indicators. Balance
  1 positive / 3 negative / 0 mixed — did not trigger the all-negative
  warning (that rule targets zero positives specifically). Cleanest link
  check yet: 13/13 resolved first attempt, zero 403s, zero 404s.

- **2026-08-09 — BWA — CREATE.** Full baseline built: historical overview,
  colonial legacy, 4 key_periods, 6 pillar summaries (Pillar C left empty —
  greyed at 1/8 measured). 14 sources opened and verified: 6 Wikipedia, 4
  news, 2 official, 2 academic. `--links` passes 0 errors, 1 warning (CDC
  blocked with HTTP 403, same bot-detection pattern seen on every prior
  run — cross-checked against an independent academic source, a PMC review
  of the same 95-95-95/gold-tier facts, rather than taken on faith). First
  first-pass country with a genuinely positive-skewed recent record: the
  October 2024 election that ended the BDP's 58-year rule, and the May 2025
  WHO gold-tier HIV/AIDS certification, are both real and both used at full
  positive weight. The record avoids hagiography by giving equal weight to
  two real counterweights: the Pula Fund (Botswana's sovereign-wealth
  evidence for avoiding the resource curse) shrank from ~$1.8B (2018) to
  ~$142M (Aug 2024) under budget deficits, and the San/Basarwa land-rights
  dispute remains unresolved since the 1990s despite a 2006 court victory,
  with a December 2022 ruling still denying land access. `colonial_legacy`
  traces the CKGR dispute to a specific, previously-unused mechanism: the
  1899 Native Reserves Proclamation demarcated land for eight recognised
  Tswana polities but never allocated the San a reserve. Pillar F (37.1,
  thin) is explicitly NOT the usual co2_pc wealth-proxy pattern — Botswana's
  near-total coal-fired electricity generation is a real, current
  vulnerability, not a scoring artifact. Balance: 2 positive / 1 negative /
  1 mixed. One item flagged rather than guessed at: Pillar E's female
  intentional-homicide rate (carried forward) scores 0.0 with no source
  found to explain it — logged as `next_action` for the EXPAND pass.

- **2026-08-09 — NGA — CREATE.** Full baseline built: historical overview,
  colonial legacy (expands context/colonial_history.yaml with the divergent
  indirect-rule mechanism — centralised Sokoto Caliphate emirates in the
  north retained real authority, while manufactured "warrant chiefs" with
  no traditional legitimacy in the decentralised southeast provoked the
  1929 Aba Women's Revolt, a plausible structural contributor to the
  region's later marginalisation), 4 key_periods, 6 pillar summaries
  (Pillar C left empty — greyed at 2/8 measured). 12 sources opened and
  verified: 4 Wikipedia, 5 news, 2 academic/think-tank, 1 official.
  `--links` passes 0 errors, 0 warnings — 12/12 resolved on the first
  attempt, the cleanest link check in the corpus so far. Confirms the
  "mixed signals across pillars" selection reason directly in the data:
  Pillars A (38.7), D (39.1), and E (36.6) are all weak and, unlike
  SOM/COD, fully and freshly measured (6/6, 5/5, 4/4) — the severity is a
  directly-evidenced crisis, not a coverage artifact. Pillar F (71.5)
  confirms the co2_pc wealth-proxy pattern flagged after DZA/COD (and
  ruled out for BWA): Nigeria is a major oil producer/exporter with one of
  the index's lowest per-capita emissions, because roughly 45-50% of the
  population has no electricity access at all. Balance: 1 positive, 2
  negative, 1 mixed — genuinely difficult, not manufactured; the one clear
  positive (the Supreme Court's October 2023 unanimous rejection of both
  opposition election challenges) is placed in `extended` rather than
  `primary` since it is a judicial event rather than an ongoing
  development, and `balance.note` states explicitly that it does not
  offset the severity of the other three items.

- **2026-08-09 — RWA — CREATE.** Full baseline built: historical overview,
  colonial legacy (expands context/colonial_history.yaml with the
  kwihutura mechanism — pre-colonial Hutu/Tutsi identity was fluid and
  cattle-based until Belgium's 1933 identity cards fixed it as an
  inherited category, which historians identify as accelerating the 1994
  genocide's killing pace; also traces the "genocide ideology" and
  "sectarianism" laws as the same instrument, repurposed for political
  control), 4 key_periods, 6 pillar summaries (Pillar C left empty —
  greyed at 1/8 measured). 12 sources opened and verified: 3 Wikipedia, 4
  news, 3 academic/think-tank, 2 official. `--links` passes 0 errors, 0
  warnings — 12/12 resolved, tied with NGA for the cleanest link check in
  the corpus. First first-pass country where strong quantitative scores
  and a difficult political record pull in different directions rather
  than the same one: 5 of 6 governance indicators are genuinely strong,
  while Voice and Accountability is a clear outlier (Kagame's 99.18%
  fourth-term win in July 2024, after courts barred his two leading
  challengers). The dominant recent story is Rwanda's documented military
  role in the DRC/M23 conflict — a UN Group of Experts report (April 2025)
  found 6,000+ Rwandan troops in eastern DRC exercising "strategic command
  and control" over M23; Rwanda captured Goma in January 2025 and Uvira in
  December 2025, days after signing the Washington Accords, before US
  sanctions followed in March 2026. Rwanda's own stated justification (the
  FDLR, a remnant of the 1994 genocidal forces, as a genuine security
  concern) is included at full length alongside the accusation. Flagged
  rather than asserted: Pillar E's IDP figure is a regional-mean estimate,
  not measured for Rwanda specifically, and plausibly reflects the
  region's DRC-conflict-driven average rather than Rwanda's own
  displacement. Balance: 1 positive (Rwanda's world-leading 63.8% female
  parliament, a genuinely different axis from the Voice-and-Accountability
  weakness, not a rebuttal of it), 2 negative, 1 mixed.

- **2026-08-09 — TCD — CREATE. First pass complete.** Full baseline built:
  historical overview, colonial legacy (expands context/colonial_history.yaml
  with the Congo-Ocean Railway forced-labour death toll — ~10,000 Sara
  Chadians among 20,000-30,000 total deaths, 1921-1934 — and the
  chief-enforced cotton quota system, tracing both directly onto the
  FROLINAT rebellion's north-south front line), 4 key_periods, 6 pillar
  summaries (Pillar C left empty — greyed at 1/8 measured), 3 primary + 1
  extended recent items, 4 events. 11 sources opened and verified: 1
  Wikipedia, 5 news, 4 academic/think-tank, 1 official. `--links` passes 0
  errors, 0 warnings — 11/11 resolved. One validator catch: pillars.A ran
  177 words against the 160 limit on first draft, trimmed twice to pass.
  Chad is the most uniformly severe first-pass country — unlike Nigeria or
  Rwanda, no single governance dimension stands out as comparatively
  strong. The direct negative counterpart to BWA's Pula Fund: the World
  Bank's 2000 Chad-Cameroon pipeline was an explicit, designed
  anti-resource-curse mechanism, and it failed within three years — Déby
  spent the first oil-revenue installment on arms in 2003, and the Bank
  exited the arrangement by 2007-2008. A genuine positive was still found
  and given real weight: $20.5 billion in financing commitments toward the
  "Chad Connexion 2030" plan (November 2025), placed in extended with an
  explicit caveat that the pipeline was also presented as a solution at
  signing. Balance: 1 positive, 2 negative, 1 mixed.

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
- **2026-08-09** — Four CREATE runs in (MUS, GHA, DZA, COD). Contrary to the
  expectation logged after DZA, COD's sourcing was NOT thinner than the first
  three — 14 sources, the most of any run so far. The "bottom decile, low
  coverage" reasoning referred to the index's own data density (Pillar C
  greyed, several indicators absent or carried forward), not to how much has
  been written about the country's history and current conflict, which is
  extensively documented. Don't conflate index data-sparsity with
  research-source sparsity in future country selection reasoning.
- **2026-08-09** — The link checker has now caught one confirmed dead citation
  (COD, a World Bank PDF) and repeatedly distinguished it correctly from
  bot-detection 403s (MUS, GHA, DZA), then ran clean with zero false positives
  on SOM's 13 citations. Confidence in the checker is earned, not assumed —
  each run should still treat a FAIL from it as meaning what it says.
- **2026-08-09** — Revise the "sparsest data" assumption for future country
  selection: of the four conflict/low-income countries researched so far
  (COD, SOM), only ONE pillar (C) has ever been greyed, not "most of them" as
  the DZA-run note speculated. The index's reliability tiers are more
  forgiving than raw pillar scores suggest — a country can score 16.8 on
  governance while still being classified RELIABLE, because reliability
  measures how much of the pillar was actually measured, not how good the
  measured values are. Don't assume low-ranked countries are low-coverage
  countries; check country_facts.py output directly each time rather than
  inferring from rank. Next country: Botswana (BWA) — high and stable,
  landlocked, a resource-governance counter-example; expect the research to
  look structurally different from the last two (institutional strength
  story rather than conflict/crisis story) and to be a useful check that the
  metaprompt handles a positive-skewed country as carefully as a
  negative-skewed one.
- **2026-08-09** — Found and fixed a gap in this ledger itself: the Run log
  above was missing entries for DZA, COD, and SOM (only MUS and GHA had been
  recorded, despite all five CREATE runs being reflected in `state.yaml`'s
  meta_notes). Backfilled from the session record so the Run log and
  meta_notes stay in sync going forward — a future run should treat any
  mismatch between the two as a signal to check for a similar gap, not
  assume the shorter one is complete.
- **2026-08-09** — BWA confirms the expectation from the note above: the
  research read as a genuinely different shape (institutional-strength
  story, not conflict/crisis), and staying honest about it took real work —
  two counterweights (Pula Fund depletion, the unresolved San/Basarwa
  land-rights case) had to be actively sought out and given full weight,
  not just left as an afterthought to a success narrative. Also worth
  noting for future runs: a country's Pillar F score should NOT be assumed
  to be the co2_pc wealth-proxy artifact (documented for DZA/COD) by
  default — BWA's low F score turned out to be a genuine, current
  vulnerability (near-total coal-fired electricity) once actually checked,
  not the same artifact recurring a third time. Check the mechanism each
  time rather than pattern-matching to the last country that had a similar
  score. Next country: Nigeria (NGA) — largest population, federal, mixed
  signals across pillars; expect a large, heterogeneous federation to
  produce a genuinely different research shape again rather than fitting
  either the crisis-country or stable-country template used so far.
- **2026-08-09** — NGA confirms the lesson from the note above rather than
  contradicting it: this time the co2_pc wealth-proxy pattern (DZA/COD)
  WAS the right explanation for a low-looking-high F score, because a
  major oil-exporting country with near-ceiling per-capita emissions
  scores turns out to have ~45-50% of its population without electricity
  access at all. The pattern is real and recurs — the point standing after
  BWA is not "don't expect it," it's "don't assume it without checking the
  underlying indicator each time," and NGA is the case where checking
  confirmed it. Also notable: NGA is the first first-pass country where
  three separate pillars (A, D, E) are simultaneously weak AND fully,
  freshly measured — a useful contrast with SOM/COD, where weak scores
  often came with thin or carried-forward coverage. Don't assume "severe
  score" implies "sparse data" any more than the reverse. Next country:
  Rwanda (RWA) — strong development indicators alongside contested
  governance. This is a genuinely new kind of challenge for the
  metaprompt: every country so far has had scores and recent framing
  pointing in roughly the same direction (BWA good news/NGA hard news);
  Rwanda's numbers will likely score well while the historical and
  colonial_legacy sections have to document authoritarian governance and
  the 1994 genocide without either softening the numbers to match the
  history or moralising the pillar summaries past what each section's own
  evidence supports.
- **2026-08-09** — RWA confirmed the predicted challenge and the metaprompt
  held: strong quantitative scores (5 of 6 governance indicators, a fast
  growth economy) and a difficult political/historical record (a barred
  opposition, a 99.18% election result, a documented role in a live
  regional conflict) coexisted in the same record without either side
  being softened. The two are genuinely different axes, not a contest —
  the record doesn't need to net them against each other into one verdict.
  Also worth flagging for future runs handling a regional-mean indicator:
  RWA's Pillar E IDP figure (49.87/1,000, regional-mean) is a case where
  the imputation method may be actively misleading rather than just
  imprecise, since Rwanda's neighbourhood average is currently being
  pulled up by a conflict Rwanda's own military is party to — a future
  EXPAND run should try to find a Rwanda-specific figure rather than
  treating the regional estimate as a neutral placeholder. Next and last
  first-pass country: Chad (TCD) — the blueprint's own worked example
  (narrative/BLUEPRINT.md cites it directly). Worth checking whether the
  metaprompt as actually practiced across eight countries still produces
  the kind of record the blueprint's illustration implied it would.
- **2026-08-09 — FIRST PASS COMPLETE.** All nine countries chosen for
  variance (MUS, GHA, DZA, COD, SOM, BWA, NGA, RWA, TCD) now have
  iteration-1 CREATE records, and TCD confirms the metaprompt still
  produces what BLUEPRINT.md's own worked example implied it would: a
  country with no bright-spot pillar, a colonial-legacy section that
  traces two distinct mechanisms (forced-labour/cotton administration and
  the France military relationship) onto present-day events, and a
  genuine — not manufactured — positive counterweight found through actual
  search rather than assumed absent. Patterns worth carrying into the
  45-country backlog: (1) check country_facts.py directly every time,
  never infer coverage or severity from rank (established after DZA,
  reconfirmed by COD/SOM/NGA); (2) the co2_pc wealth-proxy pattern is real
  and recurs (DZA, COD, NGA, TCD) but is not universal (BWA) — check the
  underlying indicator each run, don't pattern-match to the last similar
  score; (3) regional-mean and carried-forward values can be actively
  misleading, not just imprecise, when the region's average is distorted
  by a conflict the country itself is party to (RWA's IDP figure) — flag
  this explicitly rather than treating every imputed value as a neutral
  placeholder; (4) strong quantitative scores and a difficult political
  history can coexist in the same record without the narrative needing to
  net them into one verdict (RWA); (5) a genuine positive is sometimes
  genuinely absent (COD) and the validator's balance warning exists
  precisely to catch a run that gave up searching rather than a run that
  found nothing. Next: begin the 45-country backlog. No single "logical
  next country" argument applies the way it did within the first pass —
  future runs should pick based on the region/variance balance already
  visible in the corpus (the corpus is entirely Anglophone/Francophone
  sub-Saharan plus one Arabophone North African
  country; Lusophone and small-island states remain fully unrepresented).
- **2026-08-10 — schema addition: `rec_membership`, retrofitted across all
  9 first-pass records.** Per the user's explicit direction (a scoped
  decision, not a self-modification of the blueprint), added a new
  structured field recording Regional Economic Community membership —
  `{org, joined, status, left, citations}` per entry — validated against
  `asi.core.countries.COUNTRIES[iso3]["rec"]`, the index's own source of
  truth for current membership, so the narrative layer can add join years
  and citations but not drift from what the index already lists. All 20
  (country, REC) pairs across the 9 records were researched and verified
  this session, not carried over from any existing file — no join-year
  data existed anywhere in the codebase beforehand. One genuinely
  interesting finding worth flagging for any future EXPAND/AUDIT pass:
  Somalia was a 1981 founding signatory of COMESA's predecessor (the PTA)
  but never formally transitioned into COMESA when it was created in 1994,
  because the 1991 state collapse left no government to complete the
  transition — Somalia only became a full COMESA member again on 19 July
  2018, a 24-year gap directly caused by the same state collapse this
  project's SOM record already documents. `--links` passes 0 errors after
  one confirmed-transient timeout (TCD's sciencespo.fr citation, verified
  live and clean on a retry) — 12 warnings remain, all the familiar
  HTTP-403 bot-detection pattern, no new genuine dead links introduced.

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
