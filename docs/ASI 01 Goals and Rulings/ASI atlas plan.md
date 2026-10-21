---
type: "reference"
project: "African Stability Index"
section: "01 Goals and Rulings"
status: "live"
note: "ruled 2026-10-18 (P57 to P62). Goal: Plan the atlas: renamed pillars, many appraisals, four sections and one economic backend (ruled, P57–P62)."
created: 2026-10-18
updated: 2026-10-18
size_justification: "A dated record of the atlas plan as ruled (P57 to P62), kept whole."
---

# ASI atlas plan: renamed pillars, many appraisals, four sections, one economic backend

The owner asked on 2026-10-18 for six things. This plan gives a first position on each, the evidence behind it, and
the order of work.
1. **Rename and redefine the pillars.** They should overlap as little as theory allows and reach as many sources as
   possible.
2. **Stop presenting the ASI as the only score.** Appraise each country the way an NGO consultant would, with every
   index whose finished values we may use.
3. **Redo the country view.** An economic outlook sits on the right: GDP, three-year average inflation, historical
   inflation highs with their years, growth, and the stressors. Analyses weigh a little more than history.
4. **A glossier site.** It has:
   - a satellite map of Africa, zoomable deep into a country;
   - country borders drawn;
   - the name only on hover, with no bright-blue highlight;
   - no monochrome layout.
5. **One economic backend for the ASI and the Canada atlas.** It is built from section files with preset input and
   output formats. Sections can be added or removed.
6. **Four sections:**
   - Stability, with drill-down;
   - Economy;
   - Infrastructure: roads, cities, rail, ports and megaprojects;
   - a natural-features section with a fullscreen photo viewer.

## 1. The pillars, renamed and redefined

### 1.1 The logic

A pillar should be one **channel** through which a country becomes more or less stable. Three rules separate the
channels, as INFORM and ND-GAIN do:
1. **What the state does** (institutions) is kept apart from **what happens to people** (outcomes) and from **what
   the country is exposed to** (forces mostly outside its control).
2. **Stocks are kept apart from shocks.** Capacity built over decades is one channel. Volatility, debt and climate
   hazards are others.
3. **Development is one factor, so it gets one pillar.** Income, health, education, services and the demographic
   transition move together in every African dataset. Today the seven pillars spread that one factor across Social,
   Health, Infrastructure and Economic, which is where most of the overlap comes from (*ASI Building Distinct
   Pillars*, section 5).

Each pillar is also fed by its own family of publishers, so the index can grow without new overlap. Each family is
listed in the table below.

### 1.2 Proposed eight pillars (first position: variant B)

| # | Pillar | What it covers | Families of sources that can feed it |
|---|---|---|---|
| 1 | Governance and state capacity | Making and carrying out policy, collecting revenue, rule of law, control of corruption, statistics | WGI (GE, RL, CC, RQ), CPIA, SPI, tax revenue, V-Dem state capacity, Open Budget Survey, WJP |
| 2 | Political voice and representation | Participation, freedoms, who holds seats | WGI VA, IPU women in parliament, V-Dem, Freedom House, Afrobarometer |
| 3 | Security and violence | Conflict deaths, displacement by conflict, homicide, political violence | WGI PV, UCDP, IDMC, UNHCR (by origin), UNODC |
| 4 | Macroeconomic and fiscal stability | Inflation, growth and its volatility, public and external debt, reserves, current account | WDI, IMF WEO, IMF debt sustainability ratings, IDS |
| 5 | External exposure and economic structure | Commodity and aid dependence, remittances, trade, FDI, size of the economy | WDI, UNCTAD, OECD DAC, total GDP (P50) |
| 6 | Human development and demography | Income per person, health, nutrition, education, basic services, connectivity, the demographic transition | WDI, WHO, UNICEF, JMP, UIS, ITU, UN WPP, HDI |
| 7 | Social cohesion and equity | Inequality, refugees hosted, slums, women's work, urban strain | PIP (Gini), UNHCR (by asylum), UN-Habitat, ILO; later EPR and Afrobarometer |
| 8 | Environment and climate exposure | Water stress, air pollution, resource depletion, disaster displacement, forest | FAO AQUASTAT, WHO, IDMC (disasters), FAO forests; later INFORM hazard, ND-GAIN exposure |

Interpeace's definition (P47) maps onto it as follows:
- a legitimate state that represents and protects everyone: pillars 1, 2 and 3;
- the peace conditions people need: pillars 6 and 7;
- the forces that test both: pillars 4, 5 and 8.

### 1.3 What the data say

This is a prototype on the data already in Athena:
- WDI and WGI;
- the latest real value per AU state in 2016–2024;
- each indicator ranked 0–1 with higher meaning more stable;
- equal weights inside a pillar.

It is not the ASI method (no goalposts or missing-data rule), so it compares layouts with each other, not with the
published .515. Both layouts below were measured the same way.

| Layout | Pillars | Indicators | Mean \|rho\| between pillars | Largest pair | Mean with GDP per capita held constant | Largest, GDP held constant |
|---|---|---|---|---|---|---|
| Current seven, one home per indicator | 7 | 26 | .456 | .77 (Social, Infrastructure) | .227 | .50 |
| A: eight, demography its own pillar | 8 | 51 | .307 | .77 (Human development, Demography) | .240 | .65 |
| **B: eight, demography inside human development, cohesion separate** | 8 | 54 | .320 | .64 (Governance, Voice) | .251 | .65 |
| C: seven, no cohesion pillar | 7 | 50 | .298 | .64 (Governance, Voice) | .246 | .65 |

n is 52 or 53 countries in each layout. Script: `scratchpad/asi_stats/taxonomy.py`, run 2026-10-18.

**Reading:**
1. **Every new layout cuts the overlap by about a third** (.456 to about .31) while doubling the indicators (26 to
   50–54). That is the "minimum overlap, maximum reach" the owner asked for.
2. **With GDP held constant, the gain disappears** (.227 against .240–.251). The new layout does not remove what is
   left of the overlap. It gathers the development factor into one pillar instead of spreading it across four.
3. **Demography is part of the development factor.** In A it correlates .77 with human development, so B and C fold
   it in.
4. **Governance and Voice (.64) are the closest pair left.** Merging them would lose reach and the Interpeace
   distinction between capacity and legitimacy, so the first position keeps both.

**A cost the owner must weigh (conflicts with P48).** Several new pillars hang together weakly inside. Their mean
inter-item |rho| is:
- Voice: .14;
- Macro: .15;
- Environment: .16;
- External: .20;
- Cohesion: .22.

Under a reflective model (P48), a pillar's indicators should correlate because they share a cause. These pillars are
formative instead: their indicators are separate causes of instability that add up. INFORM and ND-GAIN build their
exposure pillars this way. The choice is ruling 7.2.

**Not tested:** variant D, which merges Voice into Cohesion as "Inclusion and social cohesion" (seven pillars). It is
listed so the owner can ask for it. Per the rules, no further variants are tried in search of a better number.

## 2. Many appraisals, the ASI one among them

### 2.1 How a country is shown

The appraisal panel lists each index as its publisher prints it:
- the name and publisher;
- what it measures, in one line;
- the edition year;
- the country's value on the publisher's own scale;
- the publisher's own category where one is printed (for example HDI "Low", FSI "Alert");
- a link.

The ASI is one row, marked as ours. Nothing is re-scaled into a combined score. One derived view is allowed: how far
the indices agree across the 54 countries (rank correlation, with n and an interval, P46).

### 2.2 Indices and their terms (read 2026-10-18 unless stated)

| Index | Publisher | Terms | Can we use it? |
|---|---|---|---|
| WGI (6 dimensions), CPIA, SPI, LPI, HCI | World Bank | CC BY 4.0 (read 2026-10-17) | Yes. WGI and the WDI series are already in Athena |
| Human Development Index and companions | UNDP HDRO | CC BY 3.0 IGO. Commercial use allowed. Must keep to the latest data and print the HDI recalculation note | Yes. Needs an adapter |
| World Economic Outlook | IMF | Data may be downloaded, derived and published, citing "Source: International Monetary Fund, World Economic Outlook database". Commercial reuse needs permission | Yes, non-commercial. Needs an adapter |
| Corruption Perceptions Index | Transparency International | CC BY 4.0. Changes must be indicated | Yes. Needs an adapter |
| V-Dem v16 (March 2026) | V-Dem Institute | CC BY-SA 4.0 | Yes. Share-alike applies to derivatives |
| Global Peace Index | IEP | CC BY-NC-SA 4.0 after a request form. Commercial use needs a licence | Non-commercial only. The owner submits the form |
| INFORM Risk, Mid 2026 (v073) | EC JRC | No licence on the download page. JRC reports are CC BY 4.0 | Ask JRC, or read the EC legal notice |
| ND-GAIN 2026 | Notre Dame | No licence stated; "free and open-access tool" | Ask before use |
| Fragile States Index | Fund for Peace | Values free to download. No licence stated | Ask before use |
| Ibrahim Index of African Governance | Mo Ibrahim Foundation | The portal refused our reader (403) | Read in a browser |
| Freedom in the World | Freedom House | Data by request. A permissions FAQ exists | Read the FAQ |

**First step:** WGI, CPIA, SPI and HCI from the World Bank datasets already in the store, then HDI, CPI and the IMF
WEO.

## 3. The site: four sections

### 3.1 Frontend: React and MapLibre, as in the Canada atlas (first position)

- **The current site** is Dash running in the browser through Pyodide. It is slow to start, and Plotly's map cannot
  draw satellite tiles, photo viewers or zoom-dependent layers well.
- **The Canada atlas already runs this stack** (React 19, Vite, MapLibre GL, Observable Plot). The proposal is to
  build `projects/asi/web` on it.
- **Python writes static JSON,** and the site is a static GitHub Pages build.
- **The Dash site stays live** until the new one shows everything the old one does.

### 3.2 The map

- **Basemap.** First position: EOX Sentinel-2 cloudless 2025.
  - It is open, needs no key, and allows any origin (`access-control-allow-origin: *`).
  - It is sharp to about zoom 14–15 (10 m pixels). A tile over central Nairobi shows city blocks.
  - It is CC BY-NC-SA 4.0, so it is free for a non-commercial site only.
- **The other options:**

  | Option | Deepest useful zoom | Key or cost | Licence |
  |---|---|---|---|
  | EOX cloudless 2025 | ~14–15 | none | CC BY-NC-SA 4.0 |
  | EOX cloudless 2016 | ~13, blurrier | none | CC BY 4.0, any use |
  | Esri World Imagery (ArcGIS Location Platform) | ~18–19 in cities | account and API key; free tier | Esri terms, not yet read through |
  | MapTiler Satellite | ~18–19 | key; the free plan is non-commercial | MapTiler terms |
  | Mapbox or Google satellite | ~19–20 | key and billing account | their terms |

  **Google-level depth needs a keyed provider.** The site will have a provider slot, so a key can be added later
  without code changes.
- **Borders.** Natural Earth admin-0 (public domain), drawn as thin light lines over the imagery.
  - Somaliland is drawn as part of Somalia, which is the UN's depiction (P45).
  - The alternative is the World Bank Official Boundaries (CC BY, version to confirm).
- **Interaction.**
  - Hovering shows the country's name only.
  - A selected country gets a thin outline, with no fill colour.
  - In the Stability section, the tiers are a translucent fill that can be switched off.

### 3.3 The sections

1. **Stability.**
   - The map shows tiers.
   - Clicking a country opens a drill-down: composite, then pillar, then indicator, each with n and an interval
     (P46).
   - Below sits the appraisal panel (section 2).
2. **Economy.**
   - The right-hand panel shows, in order: outlook (IMF WEO projections), stressors, output and growth, prices,
     public finances, the external position, the financial sector and structure.
   - It is filled from the section files (section 4).
3. **Infrastructure.** Its layers appear by zoom.

   | Layer | Source | Licence | Notes |
   |---|---|---|---|
   | Roads | Microsoft Road Detections, drop 2025-04-28 | ODbL (read 2026-10-18) | 5 African files: 1,407 MB, 5,918 thousand km. Built into vector tiles. ODbL share-alike applies to the derived database |
   | Cities | GeoNames cities dump | CC BY 4.0 (about page, read 2026-10-18) | Capital first; others appear by population as you zoom |
   | Rail, ports | OpenStreetMap; NGA World Port Index | ODbL; terms not yet read | |
   | Megaprojects and dams | Global Energy Monitor, GRanD, Wikidata | terms not yet read (Wikidata is CC0) | National-pride projects come from Wikidata, with their articles |

4. **Natural features.** A proposed name is "Heritage", UNESCO's own term for natural and cultural sites.
   - **Content:** mountains, rainforests, reserves and historic sites, drawn from Wikidata (CC0) and the World
     Heritage List (terms not yet read; the page refused our reader).
   - **Photos:** from Wikimedia Commons. Each file carries its own licence. A file without a stated licence is
     refused. This reuses the Canada atlas's `commons_media` shell.
   - **Viewer:**
     - one click opens a photo fullscreen;
     - swiping right (or the arrow keys) moves through a few photos;
     - one more click closes it.

## 4. One economic backend: section files with preset input and output

Two projects now need this, so it is shared under P42. The design separates three things:
1. **Figure shells (`athena/figures.py`)** never name a subject (P38).
   - **Input:** one series from the common format (periods and values).
   - **Output:** one figure record (`value`, `period`, `n`, and for a list, `values`).
   - **The shells:**
     - `latest`;
     - `mean` over the last k periods;
     - `extremes` (the k highest or lowest, at least g periods apart, with their periods);
     - `change` and `growth` over k periods;
     - `spread` (standard deviation over k periods);
     - `trend` (the series since a year);
     - `threshold` (a flag against a stated limit, with its source).
2. **Section templates (`athena-core/sections/*.toml`)** are shared by every project. A template names a section's
   figures:
   - each figure's id;
   - its label;
   - its unit;
   - the shell that computes it, with the shell's arguments.

   Adding or removing a section means adding or removing one file.
3. **Bindings (one file per project)** say which series fill each figure in that project:
   - **ASI:** WDI codes;
   - **Canada atlas:** StatCan tables and the Bank of Canada's Valet series. This needs a StatCan adapter in
     athena-core, which the atlas's `statcan_table` shell already half is.

**The output is one JSON document,** format `athena.sections/1`:
- the templates used;
- every dataset with its publisher, licence and attribution;
- for each area, each section's figures with their periods and n.

The same React panel renders it for an African state or a Canadian province.

**First templates:**
- outlook;
- output and growth;
- prices and inflation;
- public finances and debt;
- external position;
- financial sector;
- structure;
- stressors;
- appraisals (the World Bank indices of section 2).

**The stressor thresholds are first positions.** Each cites the publisher of its limit; one without a published limit is not used. The first example is reserves below three months of imports, the IMF's traditional rule of thumb.

The owner rules on the list (7.5).

## 5. The order of work

1. **This session (done 2026-10-18, athena-core #15):**
   - this plan;
   - the figure shells, the section runner and the first templates in athena-core, with tests and negative controls;
   - the ASI binding and `04_sections.py`, writing the economy payload for the 54 states from WDI;
   - a first `projects/asi/web` with the satellite map, borders, hover names, the four section tabs and the economy
     panel.
2. **Next:**
   - the IMF WEO adapter (the outlook);
   - HDI, CPI and V-Dem adapters (appraisals);
   - the stability drill-down;
   - Natural Earth through `athena.fetch` with a locked hash.
3. **Then:**
   - Infrastructure: roads as vector tiles, GeoNames cities, OSM rail and ports, megaprojects;
   - the Heritage section with Commons photos;
   - the StatCan adapter and the Canada atlas binding (M7, "the spine").
4. **The pillar change itself** waits for rulings 7.1 and 7.2. It then joins the edition-2 order after the
   missing-data rule and goalposts, because each pillar's scores depend on both.

## 6. Rules kept

- Publishers' data only. Every figure of ours is computed by a stated shell, labelled derived (P4), and carries its
  n.
- Terms are read and dated before any data is used. Rows marked "ask" or "not yet read" are not used until then.
- Nothing is re-ranked. Publishers' own categories are shown in their words.
- No raw or third-party data in tests. API keys never enter git.

## 7. Rulings (2026-10-18)

The owner answered on 2026-10-18 and asked the agent to choose where the options were unclear; the owner may edit
any of these.

1. **The pillar layout:** variant B (P57).
2. **Formative pillars:** allowed, but only when every indicator falls under the pillar's umbrella concept (P58). Each
   pillar note states its umbrella and flags indicators whose fit is in doubt.
3. **The frontend:** the React and MapLibre atlas replaces Dash once it matches it (P59).
4. **The basemap:** higher quality and deeper zoom are wanted. Esri World Imagery through a free ArcGIS Location
   Platform key, with EOX as the fallback (P62). The key is the owner's to create.
5. **Stressors:** scrapped (P60).
6. **The fourth section:** Wonders (P61).
7. **Requests to publishers:** drafts are ready in [Appraisal Terms Requests](<../ASI 02 Inputs and Sources/Appraisal Terms Requests.md>), for the owner to send.

The plan's parts are now notes of their own under [African Stability Index](<../ASI 00 Overview/African Stability Index.md>); the chart was `Athena Chart.canvas` (retired at P5).
