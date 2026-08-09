# Narrative Ledger

The document future runs read before doing anything. Machine-readable twin:
`narrative/state.yaml`.

*Seeded 2026-08-09. No research runs have happened yet.*

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

**0 of 54 countries have a record.**

### First pass — 9 countries

Chosen for variance rather than convenience: if the metaprompt has a flaw, these
nine surface it. Top and bottom of the index, island and landlocked, four
language traditions, active conflict and long stability, and the two countries
whose ranks swing hardest with the weighting method.

| ISO3 | Country | Why this one |
|---|---|---|
| MUS | Mauritius | top of the index; island state; long democratic continuity |
| GHA | Ghana | mid-high; Anglophone West Africa; repeated peaceful transfers of power |
| DZA | Algeria | rank swings 9-45 with weighting method; Arabophone; hydrocarbon economy |
| COD | Democratic Rep. Congo | bottom decile; vast and low-coverage; long conflict history |
| SOM | Somalia | lowest ranks; state reconstitution; sparse data is the hard case |
| BWA | Botswana | high and stable; landlocked; resource governance counter-example |
| NGA | Nigeria | largest population; federal; mixed signals across pillars |
| RWA | Rwanda | strong development indicators alongside contested governance |
| TCD | Chad | Sahel; 2021 coup; the worked example used in the blueprint |

### Backlog — the remaining 45

Listed in full in `narrative/state.yaml` under `backlog`. They are recorded
explicitly rather than left implicit: a country with no record should be visibly
absent, not quietly missing.

Egypt, Libya, Morocco, Sudan, Tunisia, Benin, Burkina Faso, Cabo Verde, The Gambia, Guinea, Guinea-Bissau, Cote d'Ivoire, Liberia, Mali, Mauritania, Niger, Senegal, Sierra Leone, Togo, Angola, Cameroon, Central African Republic, Republic of Congo, Equatorial Guinea, Gabon, Burundi, Djibouti, Eritrea, Ethiopia, Kenya, Malawi, Mozambique, South Sudan, Tanzania, Uganda, Zambia, Zimbabwe, Lesotho, Namibia, Eswatini, South Africa, Comoros, Madagascar, Seychelles, Sao Tome & Principe

---

## Run log

Append one line per run: date, country, mode, what changed, what was removed.

_(empty)_

---

## Meta-notes

Things a future run should know about how to work, not about a specific country.

- **2026-08-09** — System built: blueprint, schema, validator, this ledger. No
  research has run. Start with Mauritius (MUS).

---

## Pending format proposals

A run that believes the blueprint should change writes the proposal here and
stops. It does not edit the blueprint. Self-modifying format is how a corpus
becomes unauditable.

_(none)_
