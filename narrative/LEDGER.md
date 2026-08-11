# Narrative Ledger

The document future runs read before doing anything. Machine-readable twin:
`narrative/state.yaml`.

*Seeded 2026-08-09. Research runs so far: Mauritius, Ghana, Algeria, DR Congo, Somalia, Botswana, Nigeria, Rwanda, Chad, Angola, South Africa, Kenya, Egypt, Ethiopia, Sudan, Mali, Burkina Faso (all CREATE). First pass complete; backlog underway.*

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

**26 of 54 countries have a record (Mauritius, Ghana, Algeria, DR Congo, Somalia, Botswana, Nigeria, Rwanda, Chad, Angola, South Africa, Kenya, Egypt, Ethiopia, Sudan, Mali, Burkina Faso, Niger, Morocco, Madagascar, Namibia, Liberia, Eritrea, Central African Republic, Mauritania, Zimbabwe). The first pass is complete; Angola, South Africa, Kenya, Egypt, Ethiopia, Sudan, Mali, Burkina Faso, Niger, Morocco, Madagascar, Namibia, Liberia, Eritrea, Central African Republic, Mauritania and Zimbabwe are the first seventeen backlog countries.**

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

### Backlog countries done so far

| ISO3 | Country | Why this one | Status |
|---|---|---|---|
| AGO | Angola | fills the corpus's clearest gap (Lusophone Africa, previously unrepresented); third resource-economy (oil) case alongside DZA and TCD | **done — iteration 1** |
| ZAF | South Africa | anchors the Southern Africa/anchor-economy gap; first reliable-tier (not thin) composite score in the corpus; sharpest test yet of framing balance in the positive direction | **done — iteration 1** |
| KEN | Kenya | East Africa's anchor economy; only prior East African records (SOM, RWA) were atypical crisis/authoritarian cases; a multiparty democracy under real, recurring strain | **done — iteration 1** |
| EGY | Egypt | North Africa's second major economy (DZA was the region's only prior record); lowest, but reliably-measured, Pillar F score in the corpus, driven by a still-unfolding colonial-legacy water dispute | **done — iteration 1** |
| ETH | Ethiopia | one of only two never-colonised African states, requiring a genuinely different colonial_legacy framing; the GERD story's other side, cross-referenced against EGY | **done — iteration 1** |
| SDN | Sudan | the single most severe remaining gap; the SAF-RSF war since April 2023 is the world's largest displacement crisis, with a formal US genocide determination (Jan 2025); closes the refugee-outflow thread already opened in TCD | **done — iteration 1** |
| MLI | Mali | opens the Sahel coup-belt/ECOWAS-exit category entirely new to this corpus; a fourth distinct resource-governance pattern (coercive renegotiation, Barrick Gold); a case where searching again after an all-negative draft found a genuine positive | **done — iteration 1** |
| BFA | Burkina Faso | completes the AES/ECOWAS-exit pair with MLI (NER remains); accounted for ~1/4 of world extremist attacks in 2024; sharpest disconnect yet between aggregate governance scores and documented atrocities (HRW: own forces killed more civilians than jihadists) | **done — iteration 1** |
| NER | Niger | completes the AES/ECOWAS-exit trio with MLI and BFA; Niger's own first-ever civilian-to-civilian democratic transfer (Bazoum, 2021) makes the 2023 coup a sharper rupture than in its AES partners; most precisely quantified extraction-imbalance case yet (Orano: 63% stake, 86.3% of production, 1971-2024) resolved by nationalisation | **done — iteration 1** |
| MAR | Morocco | the corpus's first stable monarchy; a genuine framing-balance counterweight after a run of negative-leaning Sahel records; Western Sahara documented as the one African decolonisation case still legally open (Morocco left the OAU 1984-2017 over exactly this dispute); a genuine positive (AMO health coverage 42%->88%) placed deliberately alongside the Gen Z 212 protesters' own healthcare grievances | **done — iteration 1** |
| MDG | Madagascar | fills the Islands gap (only MUS previously represented of 5 island backlog states); distinct colonial history (an independent Merina monarchy conquered militarily in 1895-96, not a protectorate); a live current-events thread -- the October 2025 CAPSAT-backed coup that ousted Rajoelina, the same unit that installed him in 2009 -- and a genuine positive (Jan 2026 mining-moratorium lift) found deliberately rather than manufactured | **done — iteration 1** |
| NAM | Namibia | fills Southern Africa's biggest gap (only ZAF and BWA previously done of 5 in the region); colonized by two different powers in sequence (Germany, then South Africa), including the Herero and Nama genocide (1904-1908), formally recognised by Germany only in 2021; strongest governance pillar recorded in this corpus so far, deliberately paired against a genuinely unresolved current fact (a 2023 reparations lawsuit still undecided as of mid-2026) rather than treating 2021 recognition as closure | **done — iteration 1** |
| LBR | Liberia | fills West Africa's biggest absolute gap (5 of 16 done); the only country in the corpus never formally colonized by a foreign state, yet the Americo-Liberian settler elite (freed American slaves, from 1822) held internal-colonial dominance over the indigenous majority for 133 years, and Firestone's 1926 rubber lease shows the same extractive pattern operating without any formal colonizer at all; a 20+-year-overdue War and Economic Crimes Court coded mixed, not positive, since no prosecution has yet followed | **done — iteration 1** |
| ERI | Eritrea | fills East Africa's biggest gap (4 of 14 done); the only country in the corpus with zero national elections since independence (1993); most extreme data-sparsity case yet -- 3 of 6 non-C pillars greyed entirely, directly tied to the same closed-state pattern behind the corpus's lowest-ever single indicator score (Voice and Accountability, 4.9); opens a new cross-referenced pair with ETH (GERD, Tigray War, Pretoria Agreement, 2025 Red Sea tension); a genuine positive (UN-verified 2025 health/nutrition gains) credited at full weight, not treated as suspect by association | **done — iteration 1** |
| CAF | Central African Republic | fills Central Africa's biggest gap (3 of 8 done); Bokassa's 1976-1979 self-declared Empire; the corpus's first major Russian paramilitary presence (Wagner, since 2018), argued as structurally continuous with the colonial-era concessionary companies that produced the 1928-1931 Kongo-Wara Rebellion; two new corpus superlatives (56.3% severe food insecurity, 99.37/1,000 directly-measured IDPs); a genuine positive (2024 Kimberley Process reintegration) credited alongside, not instead of, Wagner-atrocity findings in the same mining sector | **done — iteration 1** |
| MRT | Mauritania | fills West Africa's biggest gap (6 of 16 done); the last country in the world to formally abolish slavery (1981, criminalized 2007), with France's own colonial administration having declared abolition in 1905 and knowingly declined to enforce it -- a distinct colonial-complicity mechanism new to this corpus; left ECOWAS entirely in 2000, decades before the AES trio's 2025 exit; a genuine positive (Greater Tortue Ahmeyim gas field reaching full production) placed alongside a genuinely unresolved current negative (2025 State Dept trafficking report on persistent hereditary slavery) | **done — iteration 1** |
| ZWE | Zimbabwe | fills East Africa's biggest gap (5 of 14 done); the only country in the corpus whose settler minority unilaterally declared independence FROM the colonizer to avoid majority rule (Rhodesia's 1965 UDI), inverting every other decolonization pattern here; the 2000-2002 land reform read as a catastrophically-executed response to a genuine, unresolved colonial grievance rather than dismissed outright; a genuine positive (ZiG currency's first single-digit inflation in ~30 years) credited independent of a severe, escalating political record (July 2026 term-limit extension, sidelined VP/General Chiwenga) | **done — iteration 1** |

### Backlog — the remaining 28

Listed in full in `narrative/state.yaml` under `backlog`. They are recorded
explicitly rather than left implicit: a country with no record should be visibly
absent, not quietly missing.

Libya, Tunisia, Benin, Cabo Verde, The Gambia, Guinea, Guinea-Bissau, Cote d'Ivoire, Senegal, Sierra Leone, Togo, Cameroon, Republic of Congo, Equatorial Guinea, Gabon, Burundi, Djibouti, Malawi, Mozambique, South Sudan, Tanzania, Uganda, Zambia, Lesotho, Eswatini, Comoros, Seychelles, Sao Tome & Principe

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

- **2026-08-10 — AGO — CREATE. First backlog country.** Full baseline
  built: historical overview, colonial legacy (expands
  context/colonial_history.yaml with the 1885 Treaty of Simulambuco —
  Cabinda's separate colonial-protectorate status, which is the exact
  legal basis FLEC has invoked for a five-decade insurgency, most recently
  a February 2026 independence declaration from exile in Brussels), 4
  key_periods, 6 pillar summaries (Pillar C left empty — greyed at 2/8
  measured), 3 primary + 1 extended recent items, 4 events, rec_membership
  (SADC 1980, ECCAS 1999). 14 sources opened and verified. `--links`
  passes 0 errors, 2 warnings (FurtherAfrica, IMF — the familiar 403
  bot-detection pattern). Chosen specifically to fill the corpus's
  clearest gap (Lusophone Africa, previously fully unrepresented) and to
  add a third resource-economy case alongside DZA (hydrocarbon, geometric
  vs PCA rank swing) and TCD (failed World Bank anti-resource-curse
  pipeline): Angola's China oil-backed-debt model (once $40B+, being paid
  down toward $7.5-8B by end-2025) is a third distinct pattern, neither a
  sovereign-wealth-fund success nor an escrow-account failure but a
  bilateral resource-backed borrowing relationship now being actively
  unwound. Pillar F is also genuinely distinct from every prior wealth-proxy
  case: Angola's low per-capita CO2 is partly real hydro investment (only
  27% fossil-fuel electricity) rather than pure energy poverty, even
  though electricity access is still only ~51% — a mixed, not purely
  artefactual, story. One drafting error caught before commit: initially
  assumed Angola was a 1983 ECCAS founding member by pattern-matching to
  COD/TCD's founding-member status; a direct Wikipedia fetch showed Angola
  was actually an ECCAS observer until January 1999. Balance: 1 positive
  (the 2022 election, closest in Angola's history, placed in extended
  since it is now three years old), 2 negative, 1 mixed.

- **2026-08-10 — ZAF — CREATE. Second backlog country.** Full baseline
  built: historical overview, colonial legacy (expands
  context/colonial_history.yaml with the 2017 land-audit figures — white
  South Africans, ~8% of the population, held ~72% of private farmland
  against Black South Africans' 4% — and traces the January 2025
  Expropriation Act to the February 2025-onward Trump administration
  rupture: an executive order, 30% tariffs, and South Africa's
  unprecedented exclusion from the 2026 G20), 4 key_periods, 6 pillar
  summaries (Pillar C left empty — greyed at 1/8 measured), 3 primary + 1
  extended recent items, 4 events, rec_membership (SADC, April 1994). 10
  sources opened and verified. `--links`: one genuine dead link caught (a
  feeds.bbci.co.uk URL returning a real HTTP 404, not a 403) — the second
  confirmed genuine dead link in the corpus after COD's — replaced with a
  working citation (Corruption Watch) covering the same claim before
  commit; 1 warning remains (IMF, the familiar 403 bot-detection pattern).
  South Africa is the first country in the corpus with a genuinely
  reliable-tier (not thin) composite score, and the sharpest test yet of
  framing balance in the opposite direction from most prior countries:
  the recent record skews positive (2 of 4 items), and both positives —
  the 2024 ANC/GNU transition and Eskom's 441-day loadshedding streak —
  are real, substantial, independently verified developments, not
  padding to look balanced. Pillar F is the clearest counter-example yet
  to the wealth-proxy pattern flagged since DZA: South Africa's CO2 per
  capita (6.76 tons, freshly measured) scores at the absolute bottom of
  the scale — a real, substantial emissions cost from a coal-dependent
  industrial economy, the mirror opposite of every "low CO2 scores well"
  case documented so far. The Trump-administration dispute was handled
  as a contested topic requiring evidence, not stance: the real costs
  (tariffs, G20 exclusion) are documented alongside the well-corroborated
  fact-check (two independent South African official inquiries, ISS
  Africa, multiple international outlets) that farm murders are roughly
  0.2% of the national homicide total and no coordinated racial campaign
  has been found — while South Africa's genuinely severe general
  homicide rate (43.72/100k, carried forward, the worst possible score)
  is reported as exactly that, a real crisis, not a targeted one.
  Balance: 2 positive, 1 negative, 1 mixed.

- **2026-08-10 — KEN — CREATE. Third backlog country.** Full baseline
  built: historical overview, colonial legacy (expands
  context/colonial_history.yaml with the Hanslope Park disclosure — the
  8,800 secretly retained colonial files that forced Britain's 2013
  "sincere regret" and GBP19.9m settlement after fifty years of denial,
  and the narrowness of that settlement: GBP3,000 per surviving claimant,
  no collective compensation for land), 4 key_periods, 6 pillar summaries
  (Pillar C left empty — greyed at 2/8 measured), 3 primary + 1 extended
  recent items, 4 events, rec_membership (COMESA 1994; EAC twice — 1967
  founding through its 1977 collapse, then 2000 refounding; IGAD 1986
  founding). 14 sources opened and verified. `--links` passes 0 errors, 0
  warnings — 14/14 resolved, the cleanest link check in the corpus so
  far. A striking documented throughline: two of Kenya's last four
  presidents (Uhuru Kenyatta, William Ruto) were once named among the
  "Ocampo Six" ICC crimes-against-humanity suspects from the 2007-08
  post-election violence, before charges were dropped or dismissed by
  2014-2016 — Ruto then presided over his own deadly protest crackdown in
  2024-2025. Pillar F is a second genuine (not wealth-proxy-artefact)
  clean-energy case after Angola's partial-hydro story: Kenya's grid is
  ~92% renewable (43% geothermal via Olkaria, Africa's largest geothermal
  field; 14% wind via Lake Turkana, Africa's largest wind farm), up from
  ~50% in 2000 — real, substantial infrastructure investment. Balance: 2
  positive (the renewable grid, Major Non-NATO Ally status), 1 negative
  (2025's protest recurrence, people still missing), 1 mixed (the 2024
  parliament storming itself, genuinely both democratic responsiveness
  and deadly state violence at once).

- **2026-08-10 — EGY — CREATE. Fourth backlog country.** Full baseline
  built: historical overview, colonial legacy (expands
  context/colonial_history.yaml with the 1929 Anglo-Egyptian Nile Waters
  Agreement — 48 bcm/year to Egypt plus veto power over upstream
  projects — and the 1959 Egypt-Sudan treaty, both negotiated by Britain
  without Ethiopia, which contributes over 85% of the Nile's flow but was
  never colonised and never a party; this is the specific legal root of
  the GERD dispute), 4 key_periods, 6 pillar summaries (Pillar C left
  empty — greyed at 1/8 measured), 3 primary + 1 extended recent items, 4
  events, rec_membership (COMESA 1998, CEN-SAD 2001). 12 sources opened
  and verified. One validator catch: historical.overview ran 301 words
  against the 300 limit, trimmed to pass. `--links` passes 0 errors, 1
  warning (France24, the familiar 403 bot-detection pattern) — 11/12
  resolved. Pillar F (8.7) is the lowest score recorded anywhere in this
  corpus, and unlike most extreme-low-F cases it is reliably measured
  (3/4 fresh), not thin — annual freshwater withdrawal runs roughly
  7,750% of internal renewable resources, possible only because Egypt
  depends on the external Nile for about 90% of its freshwater, now
  acutely exposed by Ethiopia's September 2025 GERD inauguration without
  a binding agreement. First genuinely all-negative recent-primary record
  since DR Congo's: the GERD dispute, the currency/debt crisis, and the
  uncompetitive December 2023 election are each independently severe and
  current, and this record does not manufacture a counterweight it did
  not find. Also checked rather than assumed: Sisi's 2023 result (89.65%)
  was numerically smaller than his 2018 landslide (97%), but multiple
  sources confirm this reflects reduced state mobilisation, not increased
  competition — his strongest potential challenger was blocked from the
  ballot via harassment and spyware targeting before voting even began.
  Balance: 0 positive, 3 negative, 1 mixed.

- **2026-08-10 — ETH — CREATE. Fifth backlog country.** Full baseline
  built: historical overview, colonial legacy (a genuinely different
  approach for a genuinely different case — Ethiopia is one of only two
  African states never colonised, so this expands on Menelik II's own
  1878-1904 imperial expansion, which historians including Oxford's
  Richard Reid directly compare to European colonial methods: the
  neftenya-gabbar settler system, forced Amharic imposition, violent
  suppression of the Oromo, Somali and other southern peoples — the
  direct root of today's ethnic-federal fault lines), 4 key_periods, 6
  pillar summaries (Pillar C left empty — greyed at 1/8 measured), 3
  primary + 1 extended recent items, 4 events, rec_membership (COMESA
  1994, IGAD 1986 founding — both verified directly rather than
  pattern-matched to Kenya's identical REC list). 14 sources opened and
  verified. `--links` passes 0 errors, 1 warning (AllAfrica, familiar 403
  pattern) — 13/14 resolved. GERD is the standout cross-reference: the
  same dam is Ethiopia's primary environmental achievement (near-ceiling
  Pillar F score, largely self-financed by ordinary Ethiopians —
  teachers, students, diaspora — rather than external debt) and Egypt's
  primary environmental catastrophe (documented in EGY's record), giving
  both records a shared factual anchor rather than treating the dispute
  as two separate stories. Balance: 1 positive (GERD, documented at full
  weight rather than folded only into the international dispute), 2
  negative (Amhara/Fano insurgency and the disputed April 2025 Gedeb
  drone strike, the July 2024 currency crisis), 1 mixed (the TPLF
  factional split, showing the Pretoria peace stopped a war but did not
  resolve Tigray's internal politics).

- **2026-08-10 — SDN — CREATE. Sixth backlog country.** Full baseline
  built: historical overview, colonial legacy (traces a precise
  institutional lineage from the Condominium's pre-colonial
  slave-raiding-frontier hierarchy through the 2003 Janjaweed to the
  2013-formalised Rapid Support Forces — the same commander, Hemedti,
  who led the Janjaweed now commands the RSF the US formally determined
  in January 2025 to be committing genocide; the 2023 war is fought BY
  an institution built directly on colonial-era divisions, not merely a
  general consequence of them), 4 key_periods, 6 pillar summaries
  (Pillar C left empty — greyed at 1/8 measured), 3 primary + 1 extended
  recent items, 4 events, rec_membership (COMESA 1994, CEN-SAD 1998
  founding). 15 sources opened and verified. One validator catch:
  pillars.D ran 162 words against the 160 limit, trimmed to pass.
  `--links` passes 0 errors, 0 warnings — 15/15 resolved, including an
  archived state.gov page that could not be opened directly but resolves
  for the automated checker. Pillar E's IDP figure (180.91/1,000,
  directly measured, not an estimate) is the starkest single number in
  the corpus — roughly 1 in 5.5 Sudanese displaced, confirming Sudan as
  the world's largest displacement crisis. Before accepting an
  all-negative primary record, found and verified a genuine, substantial
  positive: Sudan's Emergency Response Rooms, grown from the 2019
  revolution's resistance committees, have assisted 11.5 million people
  and won the Right Livelihood Award, Rafto Prize, Chatham House Prize,
  and two Nobel Peace Prize nominations — documented honestly, including
  that volunteers face real risk from both warring parties. Also flagged
  an index-data-lag issue worth checking in any fast-moving crisis
  country: Pillar D's regional-mean food-insecurity indicator (~11%)
  badly understates the independently-confirmed famine (Zamzam camp,
  declared August 2024; ~25.6 million facing severe hunger by 2025).
  Balance: 1 positive, 3 negative, 0 mixed.

- **2026-08-10 — MLI — CREATE. Seventh backlog country.** Full baseline
  built: historical overview, colonial legacy (traces the north's
  colonial-era military-territorial administration and southern
  investment concentration to four Tuareg rebellions since independence
  and the weakly-governed geography JNIM and ISGS now operate from,
  including the 2025-2026 fuel blockade on Bamako), 4 key_periods, 6
  pillar summaries (Pillar C left empty — greyed at 1/8 measured), 3
  primary + 1 extended recent items, 4 events, rec_membership (CEN-SAD
  1998 founding; ECOWAS recorded as withdrawn — joined 1975 founding,
  left 2025 — matching the index's own current registry). 11 sources
  opened and verified. `--links` passes 0 errors, 1 warning (France24,
  familiar 403 pattern) — 10/11 resolved. Mali opens the Sahel
  coup-belt/ECOWAS-exit category entirely new to this corpus: the
  January 2025 Alliance of Sahel States withdrawal alongside Burkina
  Faso and Niger, and the France-to-Russia (Wagner, then Africa Corps)
  security realignment. The Barrick Gold dispute ($430M settlement,
  November 2025, following employee detentions and a CEO arrest
  warrant) is a fourth distinct resource-governance pattern in this
  corpus, after Botswana's sovereign-wealth success, Chad's failed
  pipeline, and Angola's bilateral debt model. Process note worth
  repeating: the first full draft landed at 0 positive / 2 negative / 1
  mixed, matching COD/EGY's pattern — but a further search specifically
  for a counterweight found Goulamina, Mali's first lithium mine (first
  exports June 2025), which also resolved an internal puzzle the draft
  had flagged rather than explained away (Pillar D's near-ceiling
  food-insecurity score, plausibly a genuine strong-harvest effect
  rather than an anomaly). Balance: 1 positive, 2 negative, 1 mixed.

- **2026-08-10 — BFA — CREATE. Eighth backlog country.** Full baseline
  built: historical overview, colonial legacy (documents the 1932
  dissolution of Upper Volta — France abolished the colony outright for
  15 years because Depression-era cash-crop collapse meant it failed
  France's own profitability requirement, partitioning its population
  among three neighbours partly to formalise them as captive labour for
  Côte d'Ivoire's plantations; reconstituted only in 1947 after Mossi
  political pressure), 4 key_periods, 6 pillar summaries (Pillar C left
  empty — greyed at 1/8 measured), 3 primary + 1 extended recent items,
  4 events, rec_membership (CEN-SAD 1998 founding; ECOWAS withdrawn —
  founding 1975, left 2025 — matching the index's own current registry).
  12 sources opened and verified. `--links` passes 0 errors, 1 warning
  (APAnews, familiar 403 pattern) — 11/12 resolved. This is the sharpest
  disconnect yet in this corpus between aggregate WGI-style governance
  scores (moderate: Voice and Accountability 50.0, Regulatory Quality
  56.6) and specific documented atrocities: an April 2026 HRW report
  found Burkina Faso's own military and allied VDP militias killed more
  civilians than jihadist groups did between 2023 and 2025 — including
  400+ killed near Djibo in December 2023 — characterised as ethnic
  cleansing against Fulani communities. Confirmed Burkina Faso accounted
  for roughly a quarter of all extremist attacks worldwide in 2024 (Global
  Terrorism Index) and 9 of that year's 20 deadliest single attacks.
  Caught a genuine dead link before it shipped: africanewsdesk.net,
  cited for the "94-tonne gold record" figure, returned a real 404, not
  a 403 — the third confirmed genuine dead link in the corpus after
  COD's and ZAF's — replaced with a directly corroborated source
  (APAnews) before committing. A separate YAML syntax error was caught
  and fixed in state.yaml itself during this run: an unquoted colon
  inside a plain-scalar `reason` field ("(HRW: government/VDP...")
  broke the parser; fixed by rewording rather than adding quotes, since
  the file's existing convention uses single-quoted scalars with doubled
  apostrophes throughout, not bare colons in unquoted text. Following the
  SDN/MLI pattern, found a genuine positive: gold production hit a record
  94 tonnes in 2025 (up 30+ tonnes from 2024), driven by the junta's
  SOPAMIB state mining vehicle and 2024 mine nationalisations — a
  distinct-but-related resource-governance pattern from MLI's Barrick
  Gold coercion. Balance: 1 positive, 2 negative, 1 mixed.

- **2026-08-10 — NER — CREATE. Ninth backlog country, completes the
  nine-country first-pass backlog entirely.** Full baseline built:
  historical overview, colonial legacy (documents the precise
  extraction-imbalance figure behind the 2025 uranium nationalisation —
  Orano held a 63% stake in the Somair mine but took 86.3% of its
  production between 1971 and 2024, a number Niger's own government
  cited to justify nationalising outright), 4 key_periods, 6 pillar
  summaries (Pillar C left empty — greyed at 1/8 measured), 3 primary +
  1 extended recent items, 4 events, rec_membership (CEN-SAD 1998
  founding; ECOWAS withdrawn — founding 1975, left 2025 — matching the
  index's own current registry). 9 sources opened and verified: 2
  Wikipedia, 6 news, 1 official (World Bank). `narrative_check.py
  --country NER` passes 0 errors, 0 warnings on the first pass. `--links`
  passes 0 errors, 1 warning (Bloomberg, familiar 403 bot-detection
  pattern, independently corroborated by AJOT's syndication of the same
  story) — 8/9 resolved. Full pytest suite: 106 passed. Niger's own
  record sharpens the "democratic rupture" framing already used for MLI
  and BFA: Mohamed Bazoum's 2021 election was Niger's first-ever transfer
  of power between two democratically elected civilian presidents —
  unlike its AES partners, whose pre-coup governments were themselves
  less firmly democratic — which the July 2023 coup ended outright.
  Bazoum remains detained without trial more than three years later,
  never brought before a judge, his presidential term having lapsed in
  April 2026 without resignation; both the ECOWAS Court of Justice and
  the UN Working Group on Arbitrary Detention have ruled the detention
  unlawful. A sixth resource-governance sub-pattern for the corpus's
  running typology (after BWA, TCD, AGO, MLI, BFA): Niger's June 2025
  Somair nationalisation is the most precisely quantified extraction-
  imbalance case yet, and Pillar F is confirmed as the corpus's clearest
  pure wealth-proxy case — the lowest CO2-per-capita reading recorded
  anywhere in this project, paired with ~97% fossil-fuel electricity
  generation and only ~20% electricity access, with no clean-energy
  achievement to credit (unlike KEN's genuine renewable grid or the
  AGO/ETH blend cases). Following the SDN/MLI/BFA discipline, found a
  genuine positive before finalizing — the Somair nationalisation itself,
  coded positive on the same standard applied to BFA's SOPAMIB and MLI's
  Barrick Gold cases — plus a genuinely mixed item (the Chinese-financed
  Niger-Benin oil pipeline, whose real new revenue was inseparable from
  real fragility: shut by a cross-border dispute and damaged by a rebel
  attack within its first four months, only resuming in August 2024).
  Balance: 1 positive, 2 negative, 1 mixed.

- **2026-08-10 — MAR — CREATE. Tenth backlog country, first stable
  monarchy in the corpus.** Full baseline built: historical overview,
  colonial legacy (the dual French/Spanish protectorate, and Western
  Sahara documented precisely as the one African decolonisation case
  still legally open — the 1975 Madrid Accords transferred
  administration, not sovereignty, exactly as the ICJ's own October 1975
  advisory opinion required, and no referendum has ever been held), 4
  key_periods, 6 pillar summaries (Pillar C left empty — greyed at 2/8
  measured), 3 primary + 1 extended recent items, 4 events,
  rec_membership (UMA 1989 founding member, reused cleanly from DZA;
  CEN-SAD 2001 — verified fresh rather than assumed founding-member
  status from TCD/BFA's 1998 precedent). 15 sources opened and verified:
  5 Wikipedia, 6 news, 1 ICJ, 1 Climate Investment Funds, 2 more
  Wikipedia for rec_membership. `--links` passes 0 errors, 1 warning
  (france24, familiar 403 pattern already confirmed on DZA) — 14/15
  resolved. Deliberately chosen for framing balance after nine
  consecutive negative-to-mixed Sahel/Horn/Southern Africa records:
  Morocco's aggregate indicators are genuinely strong (highest
  non-island GDP per capita in the corpus, 100% electricity access,
  strongest health pillar recorded so far), and a real, current,
  substantial positive was found and placed deliberately alongside a
  real, current negative rather than either one crowding out the other —
  the AMO health-insurance reform reaching 88% coverage (up from 42%) by
  December 2025 sits in recent.primary next to the Gen Z 212 youth
  protests over exactly that same healthcare system, both true and
  current at once. Also found and verified a striking colonial-legacy-
  adjacent fact new to this corpus: Morocco withdrew from the OAU in
  November 1984 rather than sit alongside the Polisario Front's SADR as
  a fellow member, and remained outside the AU entirely for 33 years,
  unique among every AU member recorded so far, rejoining only in
  January 2017. The UN Security Council's October 2025 endorsement of
  Morocco's Western Sahara autonomy plan (Resolution 2797) and the July
  2024 pardon of jailed journalists Radi, Raissouni and Bouachrine were
  both coded mixed rather than positive: neither delivers the referendum
  or full exoneration their respective stories would need to cross that
  line. Balance: 1 positive, 1 negative, 2 mixed.

- **2026-08-10 — MDG — CREATE. Eleventh backlog country, first
  Islands record since MUS.** Full baseline built: historical overview,
  colonial legacy (the 1895-1903 Menalamba rebellion documented as
  directed as much at the retained Merina administrative elite as at
  France itself, tied explicitly to a recurring extraction-grievance
  pattern the record traces through 1972, 1991, 2002, 2009 and 2025), 4
  key_periods, 6 pillar summaries (Pillar C left empty — greyed at 1/8
  measured), 3 primary + 1 extended recent items, 4 events,
  rec_membership (COMESA 1994, SADC 2005 — verified individually, not
  assumed). 14 sources opened and verified: 3 Wikipedia, 8 news, 1
  academic/Britannica, 1 official/SADC, 1 more Wikipedia for
  rec_membership. One citation swap during the run: a Washington Post
  URL returned a persistent `TimeoutError` under `--links` rather than
  the usual 403 bot-detection pattern; rather than accept an ambiguous
  signal, swapped it for an AP-syndicated OPB piece covering the same
  event, after which all 15 citation URLs resolved cleanly — zero link
  warnings, a first for this corpus. Colonial history here is genuinely
  distinct from every prior record: an independent, internationally
  recognised Merina monarchy under Radama I and Queen Ranavalona I
  resisted European control through most of the 19th century before
  France conquered it militarily in 1895-96, not a gradual
  protectorate-to-colony transition like MAR or most of the corpus. The
  October 2025 coup that ousted President Andry Rajoelina — via the same
  CAPSAT military unit that had installed him in a 2009 coup — is an
  unusually sharp case of this corpus's "reference year predates the
  crisis" caveat: the underlying index data is dated 2023, so Pillars A,
  E and G all describe a Madagascar that, as written, no longer exists,
  flagged explicitly in each pillar's own prose. Followed the SDN/MLI/
  BFA/NER discipline and found a genuine positive rather than defaulting
  to coup-only coverage: the January 2026 mining-moratorium lift
  (Ambatovy alone repatriated $3.9B in 2023), coded positive on the same
  standard already applied to other unelected transitional governments'
  policy actions in this corpus (BFA's SOPAMIB, NER's Somair). Balance:
  1 positive, 1 negative, 2 mixed. Also raised a new pending format
  proposal: `RECStatus` has no SUSPENDED value, and Madagascar's
  2009-2013 SADC/AU suspension (distinct from the AES trio's actual
  ECOWAS withdrawals) doesn't cleanly fit CURRENT or WITHDRAWN — logged,
  not self-applied, per the self-modifying-format rule.

- **2026-08-10 — NAM — CREATE. Twelfth backlog country, fills
  Southern Africa's biggest proportional gap.** Full baseline built:
  historical overview, colonial legacy (the Herero and Nama genocide's
  2021 German recognition documented alongside its contested
  aftermath — the agreement avoids the word "reparation," Herero and
  Nama leaders were excluded from negotiating it, and a 2023 High Court
  lawsuit challenging it remained unresolved as of mid-2026), 4
  key_periods, 6 pillar summaries (Pillar C left empty — greyed at 2/8
  measured), 3 primary + 1 extended recent items, 4 events,
  rec_membership (SADC 1990 — Namibia joined SADCC within months of its
  own independence, the only REC it belongs to). 12 sources opened and
  verified: 4 Wikipedia, 5 news, 1 EBSCO, 1 UN Namibia, 1 SADC. `--links`
  passes 0 errors, 1 warning (allafrica, familiar 403 pattern) — 11/12
  resolved. Namibia is the only backlog country colonized by two
  different powers in sequence — Germany (1884-1915), then South Africa
  (1915-1990) — rather than one throughout, and the Herero and Nama
  genocide (1904-1908, an estimated 80% of Herero and 50% of Nama
  killed) is the first genocide of the 20th century. Found a genuinely
  unexpected cross-thread connection worth the colonial_legacy space it
  took: in September 2025, German utility RWE withdrew from Namibia's
  flagship $10B green-hydrogen project after Nama groups objected the
  concession sat on ancestral Nama land inside a national park — the
  same land the 1904-1908 genocide was fought over resurfacing in a
  2020s green-energy investment dispute. This record has the strongest
  governance pillar recorded in this corpus so far (all 6 WGI indicators
  positive-signed, Voice and Accountability the highest single indicator
  score seen in this pillar to date), and deliberately does not leave
  that uncomplicated: it is paired directly against the unresolved
  reparations lawsuit as a real, current counterweight — the MAR "place
  a positive and negative on the same subject side by side" discipline,
  but applied in reverse (pairing a strong CURRENT governance picture
  against an unresolved HISTORICAL-legal thread, rather than two current
  events on one subject). Balance: 1 positive, 1 negative, 2 mixed. One
  word-count fix: recent.extended was 3 words under the 40-word floor,
  fixed by adding a real fact (the Vision 2030 / sixth National
  Development Plan framing) rather than padding.

- **2026-08-10 — LBR — CREATE. Thirteenth backlog country, fills
  West Africa's biggest absolute gap.** Full baseline built: historical
  overview, colonial legacy (Firestone's 1926 rubber lease — 99 years,
  ~10% of Liberia's arable land, workers paid as little as 18
  cents/day, below Liberia's own minimum wage — documented as
  functionally the same extractive pattern this corpus records for
  formally colonized countries, operating through an American
  corporation instead of a European state), 4 key_periods, 6 pillar
  summaries (Pillar C left empty — greyed at 1/8 measured; two
  word-count fixes on Pillars D and G, both fixed by adding a real fact
  rather than padding), 3 primary + 1 extended recent items, 4 events,
  rec_membership (ECOWAS 1975 founding member, ratified 30 May 1975,
  one of the earliest ratifiers). 16 sources opened and verified: 6
  Wikipedia, 7 news, 1 Princeton, 1 Nobel Prize, 1 more Wikipedia for
  rec_membership. Liberia is genuinely unique in this corpus: never
  formally colonized by any foreign state, founded in 1822 by the
  American Colonization Society as a settlement for freed American
  slaves, yet the resulting Americo-Liberian settler elite held
  internal-colonial dominance over the indigenous majority for 133
  years — a mechanism this record argues belongs in the same category
  as this project's other extraction stories, not a genuine exception
  to them. One genuine dead link caught: a PressReader URL for the 2023
  Weah-concedes-to-Boakai citation returned a real HTTP 404 — the
  fourth confirmed genuine dead link in this corpus (after COD, ZAF,
  BFA) — replaced with a VOA News piece covering the same event before
  committing; all 16 citations resolved cleanly afterward. The War and
  Economic Crimes Court thread (Boakai's May 2024 executive order, May
  2025 renewal, a more consultative director appointment after
  civil-society pushback) is coded mixed rather than positive
  specifically because institutional progress and actual delivered
  justice are not the same thing: more than two decades after Liberia's
  civil wars ended, no one has ever been domestically prosecuted, and
  the office's own timeline doesn't expect a functioning court before
  November 2027. Balance: 1 positive, 1 negative, 2 mixed — the
  revenue-growth claim (positive) and the corruption protests
  (negative) both concern the same period, deliberately not left to
  cancel each other out.

- **2026-08-10 — ERI — CREATE. Fourteenth backlog country, most
  extreme data-sparsity case yet.** Full baseline built: historical
  overview, colonial legacy (Italy/Britain/Ethiopia's sequential
  control, then a genuinely domestic PFDJ one-party construction
  reproducing a forced-labour extraction pattern via the national
  service system and Segen Construction's alleged use of conscript
  labour at the PFDJ-owned Bisha mine subcontractor), 4 key_periods, 4
  pillar summaries only (A, E, F, G — Pillars B, C and D are ALL greyed
  out entirely, 0/5, 1/8 and 2/5 measured respectively, the first
  record in this corpus where more than just C is unwritten), 3
  primary + 1 extended recent items, 4 events, rec_membership (COMESA
  1994, CEN-SAD 1999 — verified individually; Eritrea also suspended
  and then formally withdrew from IGAD as of December 2025, correctly
  absent from the index's own current registry and therefore not
  included here). 12 sources opened and verified: 1 EBSCO, 6 news, 2
  official (Nobel, UN Eritrea), 1 Business & Human Rights Centre, 2
  more Wikipedia for rec_membership. Eritrea has held zero national
  elections since 1993, and Voice and Accountability scores 4.9 — the
  single lowest indicator score recorded anywhere in this project to
  date — directly connected, not coincidental, to why three other
  pillars couldn't be scored at all: the same closed-state pattern that
  produces the governance score is why the country publishes too little
  verifiable data for the rest of the index. Opens a new cross-
  referenced pair with ETH: the GERD dispute, the 2018 Nobel-winning
  peace deal, Eritrea's uncredited role in the 2020-2022 Tigray War, its
  refusal to sign the Pretoria Agreement, and the sharply renewed
  November 2025 Red Sea tension are all told from Eritrea's side here
  and must stay consistent with ETH's own account in any future
  EXPAND/AUDIT pass, alongside the existing EGY/ETH, TCD/SDN and
  MLI/BFA/NER threads. Following the SDN/MLI/BFA/NER/MDG discipline,
  found a genuine positive despite Eritrea's severity: UN Eritrea's own
  2025 Annual Results Report documents real, verified immunisation,
  nutrition and water-access gains, credited at full weight
  specifically to avoid treating a repressive state's documented
  humanitarian achievements as inherently suspect. Balance: 1 positive,
  2 negative, 1 mixed. One word-count fix: recent.extended was 2 words
  under the 40-word floor, fixed by adding a real fact rather than
  padding. `--links` passes 0 errors, 0 warnings — the second
  zero-warning `--links` run in this corpus after MDG.

- **2026-08-10 — CAF — CREATE. Fifteenth backlog country, fills
  Central Africa's biggest gap.** Full baseline built: historical
  overview, colonial legacy (the Ubangi-Shari concessionary company
  system's rubber/ivory extraction, compared directly to the Belgian
  Congo, exposed by André Gide's 1927 Voyage au Congo, and resisted by
  an estimated 350,000 people in the 1928-1931 Kongo-Wara Rebellion —
  perhaps the largest anti-colonial uprising in interwar Africa), 4
  key_periods, 6 pillar summaries (Pillar C left empty — greyed at
  1/8 measured), 3 primary + 1 extended recent items, 4 events,
  rec_membership (ECCAS 1983 founding member via UDEAC, CEN-SAD 1999).
  18 sources opened and verified: 9 Wikipedia, 6 news, 1 State
  Department, 2 more Wikipedia for rec_membership. This is the corpus's
  first record with a major Russian paramilitary presence: the
  colonial_legacy section argues, with specific 2024 State Department
  and UN Panel of Experts findings, that Wagner's since-2018 role —
  foreign armed actor granted mineral extraction rights in exchange for
  providing the state's own security, operating outside ordinary
  accountability — is structurally continuous with, not merely
  analogous to, the colonial-era concessionary company template. Two
  new corpus superlatives: severe food insecurity at 56.3% is the
  single worst reading recorded anywhere in this project to date, and
  displaced persons at 99.37/1,000 is both the most severe AND,
  unusually, directly fresh-measured rather than a regional-mean
  estimate — roughly 1 in 10 Central Africans displaced, stated as a
  direct finding rather than softened as an estimate. Following the
  established discipline, found a genuine positive despite the
  severity: the 2024 Kimberley Process embargo lift and 2025
  mining-code reforms are real and credited at full weight in Pillar B,
  explicitly placed alongside — not instead of — the Wagner-entanglement
  finding in the same sector, applying the MAR/NAM "positive and
  negative on the same subject side by side" discipline within a single
  pillar rather than across two recent-development items. Balance: 1
  positive, 3 negative, 0 mixed — comparable in severity distribution
  to SDN's record, not forced toward a nicer ratio. One word-count fix:
  recent.extended was 1 word under the 40-word floor, fixed by adding a
  real fact rather than padding. `--links` passes 0 errors, 0 warnings
  — the third zero-warning run in this corpus after MDG and ERI.

- **2026-08-10 — MRT — CREATE. Sixteenth backlog country, fills
  West Africa's biggest gap.** Full baseline built: historical
  overview, colonial legacy (France declared slavery abolished in
  Mauritania in 1905, only three years into its occupation, then
  documentedly declined to enforce that decision for the remaining 55
  years of colonial rule — a distinct kind of colonial complicity, new
  to this corpus: not imposing exploitation, but formally banning it
  while knowingly declining to stop it), 4 key_periods, 6 pillar
  summaries (Pillar C left empty — greyed at 1/8 measured), 3 primary
  + 1 extended recent items, 4 events, rec_membership (UMA 1989
  founding member, reused cleanly from DZA/MAR; CEN-SAD 2008 — verified
  fresh, a later joiner, not a founder). 13 sources opened and
  verified: 4 Wikipedia, 6 news, 1 Britannica, 1 State Department, 2
  more Wikipedia for rec_membership. Mauritania became independent in
  1960 with slavery still embedded from that unenforced abolition;
  full legal abolition took until 1981 (the last country in the world
  to do so) and criminal enforcement until 2007. Verified precisely
  rather than assumed: Mauritania withdrew from ECOWAS entirely in
  December 2000 (for UMA instead) — a genuinely different case from the
  AES trio's 2025 exit, two decades earlier and over currency-union
  disagreements rather than a coup-driven realignment. Pillar F logs
  what may be the starkest single hydrological figure in this corpus:
  freshwater withdrawal at over 337% of internal renewable resources,
  explicitly read as a genuine severe reality for one of the world's
  most arid countries rather than the ambiguous wealth-proxy pattern
  used for similar-looking low-withdrawal figures elsewhere. Following
  the established discipline, found a genuine positive: the Greater
  Tortue Ahmeyim gas field (shared with Senegal) reached full
  production by end of 2025, flagged explicitly as a real revenue
  stream this record's 2023-reference-year pillars cannot yet reflect,
  rather than left as an implicit gap. The July 2024 election
  (Ghazouani re-elected, anti-slavery activist Biram Dah Abeid's strong
  22.1% second-place finish, Abeid's fraud allegations) is coded mixed
  rather than adjudicated either way. Balance: 1 positive, 2 negative,
  1 mixed. One word-count fix: Pillar D was 5 words under the 80-word
  floor, fixed by adding a real cross-corpus comparison rather than
  padding. `--links` passes 0 errors, 1 warning (Britannica, familiar
  403 pattern already confirmed on multiple prior runs) — 13/14
  resolved.

- **2026-08-10 — ZWE — CREATE. Seventeenth backlog country, fills
  East Africa's biggest gap.** Full baseline built: historical
  overview, colonial legacy (Ian Smith's 1965 UDI documented as the
  only inverted decolonization pattern in this corpus -- the settler
  minority, not the colonial power, resisting majority rule -- used to
  reframe the 2000-2002 fast-track land reform as a catastrophically-
  executed response to a genuine, unresolved colonial-era grievance
  rather than dismissed outright), 4 key_periods, 6 pillar summaries
  (Pillar C left empty — greyed at 1/8 measured; Pillar D fully
  measured, 5/5, unusually complete), 3 primary + 1 extended recent
  items, 4 events, rec_membership (SADC 1980 founding member, COMESA
  1994). 13 sources opened and verified: 3 Wikipedia, 8 news, 1
  Britannica, 1 HRW PDF, 2 more for rec_membership. This is the fourth
  "reference year predates the current reality" case in this corpus
  (after MDG, ERI, MRT): Pillar B's carried-forward 253.94% inflation
  figure is genuinely severe for 2023, but is now superseded by the
  April 2024 gold-backed ZiG currency, which reached single-digit
  inflation (4.1%) by January 2026 — the first time in roughly 30
  years — credited as a genuine positive independent of, not despite,
  a severe and currently escalating political story: Mnangagwa's July
  2026 constitutional amendment extending his own term to 2030,
  sidelining Vice President Constantino Chiwenga, the same general who
  led the 2017 coup that installed him. Balance: 1 positive, 2
  negative, 1 mixed. One word-count fix: Pillar E was 3 words under the
  80-word floor, fixed by adding a real fact rather than padding.
  `--links` passes 0 errors, 2 warnings (Britannica and WEF, both
  familiar 403 bot-detection patterns) — 13/15 resolved.

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
- **2026-08-10** — AGO opens the 45-country backlog and confirms the
  meta-note above holds outside the first pass too: check the underlying
  mechanism every time rather than pattern-matching to a similar-looking
  prior case. Caught in this run specifically: assumed Angola was an
  ECCAS founding member (1983) because COD and TCD both were, via
  UDEAC/CEPGL groupings Angola was never part of — a direct source check
  showed Angola was actually an ECCAS observer until 1999. This applies
  to REC data exactly as much as it does to pillar narrative or
  methodology patterns (co2_pc wealth-proxy, IDP regional-mean caveats,
  etc.) — verify, don't infer from a similar-looking neighbour. Also
  worth carrying forward: Angola's oil-debt-to-China model is a third,
  genuinely distinct resource-governance pattern (bilateral resource-backed
  borrowing, being actively unwound) alongside BWA's sovereign-wealth-fund
  success and TCD's escrow-account failure — future oil/mineral-economy
  countries (Republic of Congo, Equatorial Guinea, Gabon, Zambia are all
  still in backlog) should be checked against all three patterns rather
  than assumed to fit whichever was used most recently.
- **2026-08-10** — ZAF surfaced the corpus's second genuine dead link
  (after COD's): a `feeds.bbci.co.uk` URL that returned a real HTTP 404,
  not the usual 403 bot-detection block. Both genuine dead links found so
  far have come from URLs that look canonical but aren't (a World Bank
  PDF path for COD, a BBC RSS-feed-style URL here) — worth treating
  feed-style or deeply-pathed URLs with slightly more scepticism at
  citation time, and always confirming a replacement resolves before
  swapping it in, same as this run did with Corruption Watch. ZAF also
  confirms a pattern worth stating explicitly for the backlog going
  forward: framing-balance discipline cuts both ways. Every country so
  far has required resisting the pull toward an unearned negative
  (COD's balance warning, TCD's severity) or an unearned positive
  (BWA's, RWA's need for real counterweights). ZAF required resisting the
  pull toward *false* balance — inventing or overweighting a negative to
  avoid a record that reads as too good, when the two genuine positives
  (the 2024 political transition, the Eskom turnaround) were simply real
  and substantial. The rule is the same in both directions: count what
  actually happened, don't average toward a target ratio.
- **2026-08-10** — KEN's rec_membership entry is worth citing as a model
  for future runs handling any REC with a discontinuous history: rather
  than flattening Kenya's EAC membership to a single "joined" date, it
  recorded two entries (founding 1967 through the 1977 collapse, then
  founding again in 2000) because the schema supports multiple entries
  per org and the two-entry version is more accurate, not just more
  detailed. Check other RECs' histories for similar discontinuities
  before defaulting to one entry — CEN-SAD and IGAD both have named
  predecessor organisations (IGADD, 1986) that could have similar cases
  worth surfacing rather than assuming continuity. Also worth noting: KEN
  is the first run with a completely clean link check (14/14, zero 403s,
  zero 404s) since SOM in the first pass — a reminder that most citation
  friction in this corpus comes from specific domains (IMF, UNDP, Crisis
  Group, AllAfrica, CDC) rather than being evenly distributed, so a
  citation set that happens to avoid those domains will simply run clean.
- **2026-08-10** — EGY confirms an important discipline point from a
  different angle than ZAF: where ZAF required resisting false balance
  when the record was genuinely positive, EGY required accepting a
  genuinely all-negative primary record (0/3/1) without straining to
  invent a fourth "positive" item just to avoid looking like COD's
  all-negative case again. The temptation with EGY specifically would
  have been to promote a structural strength (Pillar D's health outcomes,
  Pillar G's near-universal infrastructure access) into `recent.primary`
  just to balance the sentiment count — resisted, because neither is a
  recent development the primary/extended format is built to track, and
  forcing one in would blur the distinction between "this country has
  real strengths" (true, and documented in the pillars) and "something
  positive happened recently" (not true for this record, checked
  honestly). Also worth flagging for future North African / water-stressed
  countries (Libya, Tunisia, Morocco, Sudan all remain in backlog):
  Egypt's Nile-dependency mechanism is a template for checking whether a
  country's F-pillar extremity is a genuine geographic/geopolitical
  vulnerability (Egypt, ZAF's coal economy) versus a wealth-proxy scoring
  artifact (NGA, TCD, most of the corpus) versus a real clean-energy
  achievement (AGO, KEN) — three now-distinct categories worth checking
  against explicitly rather than defaulting to whichever explanation was
  used most recently.
- **2026-08-10** — ETH adds a fourth category to that F-pillar typology,
  and it doesn't fit cleanly into any of the three from the EGY note:
  Ethiopia's near-ceiling score is neither a pure wealth-proxy artifact
  nor a pure achievement like Kenya's — it's genuinely both at once (real
  GERD/hydro investment) AND still partly poverty-driven (electricity
  access only ~55%), and the record says so explicitly rather than
  forcing a single explanation. General lesson: don't assume a country
  will cleanly fit one of the categories logged from prior countries —
  check whether it's actually a blend before writing the pillar as though
  it must be one or the other. Also worth flagging structurally: EGY and
  ETH are the first pair of records in this corpus that share a single
  live event (GERD) from opposite sides. Any future EXPAND/AUDIT pass on
  either record should check the other for continued factual consistency
  — if GERD's status changes (a binding agreement, further escalation),
  both records need updating together, not just whichever one a future
  run happens to be working on.
- **2026-08-10** — SDN is the corpus's clearest demonstration yet that
  "search harder before accepting an all-negative record" actually works
  even in the most severe cases: Sudan's situation is genuinely as bad as
  any country covered so far, and the search for a real counterweight
  still surfaced one (the Emergency Response Rooms) that meets the same
  evidentiary bar as everything else in the record — internationally
  audited award recognition, a specific verified headcount, not a vague
  claim. Don't let a country's severity become a reason to skip the
  search; COD, EGY and now SDN all show that sometimes the search
  genuinely comes up short (COD, EGY) and sometimes it doesn't (SDN,
  ETH), and the only way to know which is true for a given country is to
  actually look, not to predict from how bad the rest of the record
  reads. Also worth flagging for TCD's future EXPAND pass: SDN's record
  documents the war driving Sudanese refugees into Chad from the source
  side, giving a second cross-referenced pair (after EGY/ETH's GERD) that
  a future audit should keep factually consistent across both files.
- **2026-08-10** — MLI sharpens the SDN lesson into an actionable
  checkpoint rather than a general principle: when a first full draft
  lands at 0 positive, treat that specific moment — not "this country
  seems severe" in the abstract, but the concrete fact of an empty
  positive slot — as the trigger to run one more targeted search before
  accepting it. MLI's positive (Goulamina lithium) also did double duty,
  resolving a data puzzle (Pillar D's food-insecurity figure) the record
  would otherwise have left as an unexplained flag — a reminder that a
  genuine counterweight search sometimes pays for itself twice, not just
  once. Also worth carrying forward: Mali is the first of what will
  likely be three closely related records (Burkina Faso and Niger remain
  in backlog) sharing the same AES/ECOWAS-exit institutional facts —
  future runs on either should reuse MLI's verified ECOWAS-founding-year
  (1975) and CEN-SAD (1998) research rather than re-deriving it, and all
  three records should stay consistent on shared AES developments the
  way EGY/ETH and TCD/SDN already do on their shared events.
- **2026-08-10** — BFA confirms MLI's ECOWAS (1975) and CEN-SAD (1998)
  research reused cleanly with zero re-verification needed — the "reuse
  shared REC facts across AES records" plan from the MLI note works in
  practice. When Niger is eventually written, its ECOWAS/CEN-SAD entries
  should follow the same pattern. Also: a genuine YAML syntax bug was
  introduced and caught in this run — an unquoted colon inside a
  plain-scalar block in state.yaml broke the parser. Every meta_notes
  entry and every `reason`/`next_action` field in this file uses
  single-quoted scalars specifically so colons, apostrophes and other
  punctuation don't need special handling beyond doubling apostrophes —
  a future run drafting one of these fields as an unquoted plain scalar
  (easy to do by accident when appending via a script rather than the
  Edit tool) should quote it from the start rather than debugging a
  parse failure after the fact. Finally: this is the third run to log a
  genuine (not bot-detection) dead link mid-session rather than only
  during a scheduled AUDIT pass (after COD's World Bank PDF and ZAF's
  BBC feed URL) — dead links are being caught reliably by the existing
  workflow without needing to wait for the 4th-iteration audit rotation
  to find them.
- **2026-08-10** — NER confirms the ECOWAS (1975) and CEN-SAD (1998)
  research reused cleanly a third time across all three AES records
  (MLI, BFA, NER) with zero re-verification needed. This closes the
  nine-country first-pass backlog (AGO through NER) and, with it, the
  three-way MLI/BFA/NER cross-reference thread flagged since the MLI
  run: a future EXPAND or AUDIT pass touching any one of these three
  should check the shared ECOWAS-exit (Jan 2025) and resource-
  nationalisation facts stay consistent across all three files, the same
  discipline already applied to the EGY/ETH GERD pair and the TCD/SDN
  refugee-outflow pair. The resource-governance typology is now six
  entries deep (BWA sovereign-wealth success, TCD's failed pipeline,
  AGO's bilateral debt model, MLI's coercive Barrick renegotiation, BFA's
  SOPAMIB nationalisation, NER's Somair nationalisation) and the Pillar F
  wealth-proxy-vs-genuine-achievement-vs-blend typology now has its
  cleanest pure-artefact case in NER itself (lowest CO2 pc in the corpus,
  paired with almost no actual clean generation or access) — worth citing
  as the reference example if a future country's Pillar F story needs a
  clear contrast to argue against.
- **2026-08-10** — MAR is a useful test of the framing-balance discipline
  from the opposite direction than usual: instead of searching for a
  positive to avoid an all-negative record (the SDN/MLI/BFA/NER pattern),
  this run deliberately picked a country likely to *supply* a strong
  positive after nine records in a row skewed negative-to-mixed, and then
  had to resist the opposite failure mode — letting a genuine achievement
  (AMO health coverage) quietly cancel out a genuine, current grievance
  about the same system (Gen Z 212) instead of stating both at full
  weight side by side. Worth carrying forward as its own checkpoint,
  distinct from the "search again at 0 positive" rule: when a positive
  and a negative item share the same underlying subject, place them next
  to each other rather than letting either one soften the other. Also
  confirms the REC "verify, don't pattern-match" discipline generalises
  past the AES trio: MAR's UMA membership reused DZA's 1989 founding-year
  research cleanly, but CEN-SAD needed its own fresh search rather than
  assuming TCD/BFA's 1998 founding-member pattern — Morocco joined in
  2001, a genuinely different case (a later joiner, not a founder), and
  would have been wrong if assumed by analogy.
- **2026-08-10** — MDG confirms the citation-swap discipline should
  extend beyond the known 403 bot-detection pattern: a `TimeoutError`
  from `--links` is a different signal (the request never got a response
  at all, not a blocked-but-live response) and this run treated it the
  same cautious way as a genuine dead link — swap to a corroborating
  source rather than assume it's "probably fine like the 403 cases."
  That produced this corpus's first zero-warning `--links` run. Also
  worth carrying forward: MDG's Pillars A, E and G all describe a
  pre-coup Madagascar because the underlying index data's reference year
  (2023) predates the October 2025 crisis entirely — this is a sharper,
  more literal version of a caveat this corpus has made before (e.g.
  BFA's true IDP figure vs. the measured one) and should be checked for
  every future country whose most consequential recent event postdates
  its own data's reference year, not just ones already known to have a
  data-lag problem.
- **2026-08-10** — NAM introduces a variant of the balance discipline
  worth naming explicitly: MAR paired a positive and negative item that
  shared the same CURRENT subject (AMO coverage vs. Gen Z 212 protests,
  both 2025); NAM instead pairs its strongest-ever governance PILLAR
  score against an unresolved HISTORICAL-legal thread (the Herero/Nama
  reparations lawsuit) that is still open only because of ongoing
  present-day inaction. Different shape, same principle: a genuine
  strength should not be left to imply a completeness it doesn't have
  when a real, current, related weakness exists — check for this
  pairing opportunity at the pillar level, not just within
  recent.primary. Also worth flagging for a future EXPAND pass: this is
  the first record where a Pillar F/G explanation depended on ruling OUT
  the usual wealth-proxy reading (Namibia's low-fossil generation is
  argued as a genuine achievement specifically because electricity
  access, unlike NER/BFA/MDG, is only moderately constrained rather than
  severe) — a useful worked contrast if a future country's Pillar F
  needs the same kind of judgment call.
- **2026-08-10** — LBR is a genuine test of the "never colonized"
  category this corpus has only used once before (ETH). Worth stating
  the distinction plainly for future runs: Ethiopia's non-colonization
  meant the record needed a genuinely different colonial_legacy
  framing built around Menelik II's own imperial expansion. Liberia's
  non-colonization means something else entirely — a settler project
  by formerly enslaved people that reproduced the same extractive
  and stratifying dynamics as European colonialism, just without a
  foreign sovereign ever holding the territory. Do not assume "never
  colonized" is a single pattern; check what actually filled the
  space where colonization would otherwise have been. Also: this is
  the fourth genuine (non-403) dead link caught in this corpus, and
  the first from PressReader specifically — PressReader URLs may be
  worth treating with extra suspicion in future citation checks, since
  their content can rotate or expire independent of the underlying
  story still existing elsewhere.
- **2026-08-10** — ERI adds a fourth distinct "how do we frame this
  country's relationship to colonization" pattern to the three already
  logged (MDG's conquered independent monarchy, ETH's own imperial
  expansion, LBR's settler-project-by-the-formerly-enslaved): Eritrea
  WAS formally colonized in the ordinary sense, but the record's most
  important extraction story — the national service system — is a
  purely post-independence, domestically-generated institution with no
  colonial-era antecedent at all. The lesson for future runs generalizes
  further than "check what filled the space where colonization would
  otherwise have been" (the LBR lesson): sometimes the most damaging
  extraction pattern in a country's history isn't colonial at all, and
  forcing every record's colonial_legacy section to be the single place
  a country's worst governance story lives would be a mistake. Also
  worth carrying forward as a genuine methodological finding, not just
  a caveat: greyed pillars are not independent of the pillars that DO
  get written. ERI's Pillar A finding (worst Voice and Accountability
  score in the project) and its three greyed pillars (B, C, D) are the
  same underlying fact — a state that suppresses information about
  itself — observed from two different angles. A future EXPAND pass on
  any heavily-greyed record should check for this connection explicitly
  rather than treating "why is this pillar greyed" as a separate
  question from "what does the written pillar say."
- **2026-08-10** — CAF confirms a pattern worth naming: this is the
  third record in a row (after MDG and ERI) to pass `--links` with zero
  warnings. That is not evidence the citation-quality bar has loosened —
  if anything the opposite, since this run also swapped out a
  Washington Post link for MDG and caught a genuine PressReader 404 for
  LBR. It more likely reflects that Wikipedia and major wire services
  now make up a larger share of citations than in the earliest runs
  (MUS/GHA/DZA), which leaned more on official/NGO/think-tank PDFs that
  are more prone to bot-detection blocking. Worth watching whether this
  holds as an emerging pattern or is coincidence across a few runs.
  Also: CAF's Wagner-as-concessionary-company argument is the most
  structurally direct colonial-legacy claim made in this corpus so far
  — not "this rhymes with colonialism" but "this occupies the literal
  same institutional position colonialism did, with a different foreign
  power." Worth checking in a future AUDIT pass whether the specific
  claim (extraction rights traded for security provision, operating
  outside ordinary state accountability) holds up as precisely as
  written, since it is doing real argumentative work rather than
  serving as background color.
- **2026-08-10** — MRT adds a fifth distinct colonial-complicity
  mechanism to the running typology (after MDG's conquered monarchy,
  ETH's own imperial expansion, LBR's settler-project-by-the-formerly-
  enslaved, CAF/ERI's post-colonial domestic institutions echoing
  colonial structure): France's 1905 declared-but-unenforced abolition
  of slavery is neither "colonizer imposed X" nor "colonizer's
  successor state reproduced X" — it is "colonizer formally banned X,
  then chose for 55 years not to enforce that ban." That is a
  meaningfully different kind of complicity (a documented act of
  omission, not commission) and worth its own category when a future
  country's colonial history turns on what the colonial power declined
  to do rather than what it did. Also worth flagging as a genuinely
  new pattern: MRT is the first record where a single Pillar (F)
  contains a data point this record is confident reads as GENUINELY,
  not ambiguously, severe (freshwater withdrawal >337% of renewable
  resources) specifically because the country's known aridity rules out
  the abundance-explanation used for MDG's and LBR's similarly
  low-scoring freshwater figures — a reminder that the same numeric
  pattern (near-zero or, here, wildly-over-100% withdrawal) can mean
  opposite things depending on the country's actual hydrology, and
  should be checked against that context each time rather than
  defaulted to one reading.
- **2026-08-10** — ZWE confirms the "reference year predates the
  current reality" pattern first flagged on MDG is now recurring
  reliably enough to actively search for on every run, not just notice
  when stumbled on: this is the fourth instance (MDG's coup, ERI's Red
  Sea tension, MRT's gas field, ZWE's currency reset) in eight runs.
  Worth naming the check explicitly for future CREATE passes: after
  drafting the pillar summaries from country_facts.py's reference year,
  search specifically for "what changed in this country after [year]"
  before finalizing recent.primary, rather than only surfacing whatever
  turns up in the course of researching historical events. Also: ZWE's
  UDI is the sixth distinct colonial/decolonization-relationship
  pattern logged in this corpus (after MDG's conquered monarchy, ETH's
  own imperial expansion, LBR's settler-project-by-the-formerly-
  enslaved, CAF/ERI's post-colonial domestic institutions echoing
  colonial structure, MRT's declared-but-unenforced abolition) — and
  the first where the settler population itself, rather than the
  metropole or a successor state, is the party resisting decolonization.
  The typology is now diverse enough that future country picks should
  actively ask "which pattern would this add" rather than defaulting to
  the most obvious reading of a country's colonial history.

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
- **2026-08-10 (from MDG CREATE run):** `asi/narrative/schema.py`'s
  `RECStatus` enum has only `CURRENT` and `WITHDRAWN`, with no way to
  represent a temporary suspension. Madagascar's SADC and AU membership was
  suspended for four years (2009-2013) following the 2009 coup but was never
  withdrawn and is current again today — a genuinely different case from the
  AES trio's (MLI/BFA/NER) actual ECOWAS withdrawals. Represented in the MDG
  record with a current status and the suspension mentioned only in
  `historical.key_periods` prose, since the schema has no structured field
  for it. Suggest adding a `SUSPENDED` status value if another
  suspended-not-withdrawn case comes up. Not applied — awaiting a human
  decision, per the self-modifying-format rule above.
