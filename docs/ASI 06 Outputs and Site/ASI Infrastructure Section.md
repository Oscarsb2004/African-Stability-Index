---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-18"
updated: 2026-10-21
---

# ASI Infrastructure Section

> [!abstract] Goal
> Show how goods, power and people move through each country and out of it: export hubs and the chains that feed them, roads, railways, shipping, the grid and pipelines, and what each country holds and sells.

## Why it exists

The owner asked for the Canada atlas's infrastructure ideas applied to Africa with different emphases, from AID for geolocated infrastructure and the World Bank's Africa Infrastructure national data for descriptive values (P65).

## Precise objectives

1. Each layer appears by zoom, so the continent view stays calm.
2. Every layer's licence is read before use; ODbL layers keep their share-alike in the derived data.
3. Every feature published is reachable on the map, and every figure shows its year.
4. Nothing is drawn or ranked by our own judgement: chains and ratios are declared joins and formulas.

## The owner's direction (P65, 2026-10-18)

- **Sources.** Geolocated infrastructure from the AUDA-NEPAD African Infrastructure Database (AID). Descriptive
  values from the World Bank's *Africa Infrastructure: National Data*.
- **The descriptive values asked for:**
  - connection to services;
  - producer prices (PPI; P66);
  - minimum and median wages;
  - manufacturing costs for industry;
  - the share of the economy that resource exploitation accounts for.
- **The focus:**
  - roads, and highways that carry heavy trucks;
  - railways and shipping routes;
  - the main export hubs, and how materials move out through them;
  - each country's major resources, with how much of each it produces and sells;
  - an overlay of the electricity grid (which areas are connected), and pipelines.
- **The model.** Inspired by the Canada Economic Atlas (athena-data), but with different emphases.

## What the sources hold (read 2026-10-18; terms in Sources (athena-data))

- **AID:**
  - 647 projects (551 mapped) in transport, ICT, water and energy, with PIDA codes, corridors and capital cost.
  - These are **projects**, not the whole network.
  - The site says "All rights reserved" and gives no licence. Its API needs a key from an account.
  - So the layer waits on the publisher's answer and on the owner's account.
- **The World Bank database** (dropped by the owner, P66) is the Africa Infrastructure Country Diagnostic:
  - CC BY 4.0;
  - 895 series for 53 states, **1990 to 2009 only**, through DataBank with no bulk file;
  - strong on access, roads, power, ICT and water;
  - **no series** on wages, PPI, manufacturing costs or the resource economy.
- **The values it lacks, and their first-position sources:**
  - **Producer prices** (P66): the IMF's PPI dataset (16 states) and FAOSTAT's agricultural producer prices.
  - **Wages:** ILOSTAT, minimum and median.
  - **Costs for industry:** the World Bank Enterprise Surveys and the Logistics Performance Index, both through the
    World Bank API.
  - **The resource economy:** the WDI's natural-resource rents (oil, gas, coal, minerals, forest) as a share of GDP.
  - **Current access rates:** the WDI.
- **The networks AID does not hold come from open publishers:**
  - **USGS** 2021 GIS compilation for Africa: mines and plants, exporting ports with their commodities and
    destinations, pipelines, power stations, rail and roads. Public domain, except that rail and roads are
    OpenStreetMap-derived.
  - **World Bank grid map** (2017, CC BY 4.0) and **gridfinder** (CC BY 4.0).
  - **IMF PortWatch:** ports, chokepoints and port activity.
  - **CEPII BACI:** exports by product, Etalab 2.0.

## Like the Canada atlas, and unlike it

| Canada atlas | Here | Why the emphasis differs |
| --- | --- | --- |
| Transport Canada's five trade corridors, joined to their ports | Export chains, from mine or field by rail or road to an exporting port and its destinations | Most African exports are raw commodities leaving by a few corridors; that path is the story |
| Major Projects Office portfolio | AID's PIDA projects, then a megaproject rule | AID is the continent's own register of regional projects |
| NRCan's national rail network, every class kept | USGS rail and AID rail projects, every published class kept | Same rule: the publisher's classes, never our own "important rail" |
| Canadian-flagged vessels by AIS | Port activity and chokepoints (PortWatch) | Where the ships go matters more than whose they are |
| Sector GDP | What each country produces and sells, and resource rents as a share of GDP | The resource economy is the economy for many states |
| — | The grid, which areas are connected, and the power pools | Access to power is the binding constraint the Canada atlas never faced |
| — | Landlocked states' routes to the sea | 16 member states depend on a neighbour's corridor and port |

## The rules carried over

- **Reproduce, never create:**
  - every line, point and number is a publisher's;
  - a chain or a ratio is a stated join or formula, marked derived;
  - no rankings of our own.
- **Rendering a collection is a total function:** every feature published is reachable on the map.
- **Each layer states its year and its limits on screen.** A 2009 AICD value is never shown as current, and a
  modelled grid line is never shown as a surveyed one.
- **Never invent a truck route.** No open source publishes axle-load limits across Africa. The map shows the
  publisher's road class and the Trans-African Highway and PIDA corridors as published. It does not show a
  "heavy-truck network" of our own.

## Implementation, in order (one branch and one pull request per step)

| Step | What | Waits on |
| --- | --- | --- |
| I0 | **Terms and access:** AID's answer and API key; ILOSTAT's terms; GEM's form | the owner |
| I1 | **System Geodata (athena-data):** the geo format in Athena and one adapter for the USGS Africa compilation, whole | — |
| I2 | **Ports, export hubs and mines** as point layers, with their cards | I1 |
| I3 | **The grid, power stations and pipelines;** vector tiles for lines | I1 |
| I4 | **Railways and the trunk road network** (ODbL kept), with the corridors | I1 |
| I5 | **National data:** WDI, IMF producer prices, FAOSTAT producer prices, Enterprise Surveys, LPI and ILOSTAT, as section templates of the Infrastructure dimension | I0 for wages |
| I6 | **What each country holds and sells:** production, exports from BACI by a declared HS crosswalk, and rents | I5 |
| I7 | **AID projects** | I0 |
| I8 | **Export chains and landlocked access,** as derived joins | I2, I4, I6 |
| I9 | **Shipping:** ports' activity and chokepoints | I2 |
| I10 | **A first review** by a logistics or infrastructure professional ([Expert Consultation](<../ASI 08 Status and Roadmap/Expert Consultation.md>)) | I2 to I8 |

## What the store holds (athena-core #19)

- `usgs-africa-gis-2021`: 24 layers, 429,835 features. The stated sources decide what can be published:
  - rail and roads from OpenStreetMap (ODbL);
  - power and pipelines from a commercial publisher (Cross-border Information / African Energy), so held back;
  - boundaries from GADM (no redistribution), so held back;
  - ports mostly from the NGA World Port Index (public domain).
- `wb-africa-grid-2017`: 62,001 lines (CC BY 4.0; 3,229 OpenStreetMap lines keep ODbL).
- **Showing the layers waits for #17,** which rewrites the map; the layers then come from a publication list naming
  each layer's licence and attribution.

## Inputs and outputs

- **In:** the layers below
- **Out:** the Infrastructure view

## Where it stands

Built (2026-10-21):
- **Cities.**
- **The map layers (I2 to I4):** ports, mines and mineral facilities, deposits and exploration sites as points; railways, major roads and the electricity grid as vector tiles; a card for each point; each state's ports, facilities and kilometres of line in its panel (African-Stability-Index #3 and #4).
- **The national figures from the WDI (I5, first part):** connection to services, power for industry, trade logistics and the resource economy, as athena-kit's section templates (v0.1.4).
- **Producer prices (I5, second part; 2026-10-22):** the IMF's producer and wholesale price indices (its PPI dataflow, 12 and 9 member states) and FAO's agricultural producer price index (41), each figure with its year; FAO's 136 series covering 20 or more states are in the Data tab.
- **Offshore features** count for the state whose waters hold them (the owner's ruling of 2026-10-21; Marine Regions' World EEZ v12).
- **Shipping (I9; 2026-10-22):** IMF PortWatch's ports in member states (196, in 38 states) and its chokepoints (all 28 worldwide at first; from 2026-10-23 only the 4 within 100 km of a member state's land: Suez, Gibraltar, Bab el-Mandeb and the Cape of Good Hope, the owner's Africa-only direction), with PortWatch's published vessel counts, industries and shares of each country's maritime trade, and each complete year 2019–2025 of port calls and estimated imports and exports (or transits and trade volume), summed from the daily figures (derived). 80 of USGS's 123 mineral-exporting ports are joined to PortWatch by published keys only: USGS's WPI ID, NGA's World Port Index (index number to UN/LOCODE), PortWatch's LOCODE. Of the rest, 36 have a LOCODE PortWatch does not list, 6 have no WPI ID, and 1 has a WPI number that NGA gives two LOCODEs. PortWatch's ports are rings in the ports' blue, sized by ships per year, and the chokepoints light dots: six point hues fail the palette check, so no hue was added.
- **The placement rule, corrected (2026-10-22):** a point inside another state's land, or nearest to it, is in no member state (Eilat and Aqaba had gone to Egypt), and a PortWatch port counts for a member state only where PortWatch names it too (Ceuta and Melilla, inside Morocco's 1:50m polygon, are left out and listed). No point of the USGS layers moved.

Waiting: ILOSTAT's wages (the owner reads its terms), and AID (its publisher's answer and the owner's account).

## The layers

One row per layer or analysis; each was its own note until P5 (P94). Their open questions are under Open
questions.

| Layer | Status | Goal | Why it exists | Objectives | In and out | Where it stands | Related |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Infrastructure Cities** | built | Show the capital first, then the largest cities as the map zooms in, by population. | Cities orient the reader and carry most of each country's people and economy. | 1. Every member state has its capital marked.<br>2. Labels never overlap; the less populous one gives way.<br>3. The panel lists the capital and largest cities with their populations. | **In:** Natural Earth 1:10m populated places (public domain)<br>**Out:** city markers and the panel's list | Built: 1,292 places in the 54 states, 58 capitals (Côte d'Ivoire and South Africa have more than one, as Natural Earth records). | [ASI Map and Imagery](<ASI Map and Imagery.md>) |
| **Infrastructure AID Projects** | blocked | Show the continent's own register of infrastructure projects (AID): where each is, its sector, corridor, PIDA code, status and capital cost. | The owner chose AID as the geolocated source (P65). It is AUDA-NEPAD's register of the projects that AU member states and regional communities report, so it shows what Africa itself plans and builds. | 1. Ingest every published project whole through the API (`geo-projects.php` with `geometry=1`, paged), points and full routes.<br>2. Keep the publisher's sector, subsector, programme, corridor, status and capital cost as published.<br>3. Show only after AUDA-NEPAD confirms the data may be republished on a public site. | **In:** AID API (key from the owner's account; 500 requests an hour)<br>**Out:** project points and routes, with a card for each | Blocked: the site says "All rights reserved" and states no licence; the API needs a key. Terms read 2026-10-18. | Sources (athena-data) · [Infrastructure Megaprojects](<ASI Infrastructure Section.md#the-layers>) |
| **Infrastructure Roads** | planned | Draw the road network by the publisher's class, the trunk roads that carry freight, and the Trans-African Highway and PIDA corridors as published. | Roads carry most freight in Africa. The owner asked for roads and the highways that carry heavy trucks (P65); no open source publishes axle-load limits, so the publisher's road class and the published corridors stand in, and the map says so. | 1. Major roads from the USGS compilation (OpenStreetMap-derived, ODbL), every published class kept.<br>2. Corridors from AID once its terms allow; Microsoft's AI-detected roads only as density at deep zoom.<br>3. Never a "heavy-truck network" of our own.<br>4. Vector tiles served as static files; ODbL's share-alike kept. | **In:** USGS Africa GIS roads (OSM-derived, ODbL); AID corridors; Microsoft Road Detections (ODbL)<br>**Out:** a roads layer by zoom | Planned (step I4). USGS's rail (47,127 features) and roads (360,852) are in the store (#19), all from OpenStreetMap, so ODbL. |  |
| **Infrastructure Railways** | planned | Draw the railways, every published class kept, with the rail projects AID records. | Rail carries the bulk minerals that many states export; a mine's railway usually ends at its port. | 1. USGS rail (OpenStreetMap-derived, ODbL), every published class kept.<br>2. AID rail projects once its terms allow.<br>3. AICD's rail statistics (1990–2009) in the country panel, dated. | **In:** USGS Africa GIS rail; AID; AICD<br>**Out:** rail lines by class | Planned (step I4). Ports moved to [Infrastructure Ports and Export Hubs](<ASI Infrastructure Section.md#the-layers>). USGS's rail (47,127 features) and roads (360,852) are in the store (#19), all from OpenStreetMap, so ODbL. |  |
| **Infrastructure Ports and Export Hubs** | built | Show the ports that carry each country's exports: what leaves through each, in what form, from where, to where, and how busy the port is. | Export hubs are where a commodity economy meets the world. USGS records, for each mineral-exporting port, the commodities exported, their capacity, source and destination; PortWatch adds port calls. | 1. USGS mineral-exporting ports with every published attribute.<br>2. PortWatch's ports (2,065 worldwide on 2026-10-22) for the full list, and port activity where published.<br>3. Join USGS and PortWatch only on published keys (USGS's WPI ID, through NGA's World Port Index, to PortWatch's UN/LOCODE), never by name or distance.<br>4. Each port's card states its sources and years. | **In:** USGS Africa GIS (2021, public domain); IMF PortWatch (IMF terms); NGA World Port Index (public information)<br>**Out:** port points sized by a published measure, with cards | Built (I2, I9): USGS's 123 ports (318 commodity rows) with their cards; PortWatch's 196 ports in member states as rings sized by ships per year, each with its complete years of activity; 80 USGS ports joined to PortWatch. | [Infrastructure Export Chains](<ASI Infrastructure Section.md#the-layers>) |
| **Infrastructure Shipping Routes** | partly built | Show how goods leave the continent by sea: the chokepoints and the traffic out of African ports. | Shipping routes decide which disruptions (Suez, Bab el-Mandeb, the Cape) reach which economies. | 1. PortWatch chokepoints and their daily transits.<br>2. Traffic density only from a published raster, never lines drawn by us.<br>3. Export destinations from BACI, shown as flows by partner, not as invented sea lanes. | **In:** IMF PortWatch; CEPII BACI<br>**Out:** a chokepoint layer and destination flows | The chokepoints are built (I9): PortWatch's 4 within 100 km of a member state's land (Africa only, 2026-10-23), each with its ships per year and its complete years of transits and trade volume. Traffic density and BACI's flows wait (I6). |  |
| **Infrastructure Mines and Mineral Facilities** | planned | Show where each country's minerals are mined and processed: commodity, capacity, status and operator. | The resource economy has places. A mine's location explains the railway and the port. | 1. USGS mineral facilities, exploration sites and deposits, with every published attribute.<br>2. The World Bank's Power–Mining projects (2014) as a dated second layer.<br>3. The facility's year is always shown; capacity is not output. | **In:** USGS Africa GIS (2021); World Bank Africa Power–Mining Projects Database (2014, CC BY 4.0)<br>**Out:** facility points by commodity | USGS's 2,408 mineral facilities, 1,093 exploration sites and 1,190 deposits are in the store (#19). Display follows #17. |  |
| **Infrastructure Resources Output and Sales** | planned | For each country, list its major resources with how much of each it produces and how much it sells abroad, and what share of the economy resource extraction is. | The owner asked for each country's resources beside the total output and how much is sold (P65). | 1. **Production:** a publisher's commodity tables (USGS Minerals Yearbook country chapters; BGS or World Mining Data once their terms are read).<br>2. **Sales:** exports by value and quantity from CEPII BACI, through a declared commodity-to-HS crosswalk marked derived.<br>3. A ratio of sales to output is shown only where units match, with its formula; otherwise the two stand side by side.<br>4. **Share of the economy:** the WDI's rents by resource (oil, gas, coal, minerals, forest) as a share of GDP.<br>5. "Major" means the publisher's own ordering or a stated rule (for example, every commodity over a stated share of the country's exports), never our judgement. | **In:** USGS; CEPII BACI (202601); WDI<br>**Out:** a country-panel block and commodity filters on the map | Planned (step I6). |  |
| **Infrastructure Electricity Grid** | planned | Show the electricity grid and which areas are connected: lines by voltage, power stations, modelled connected areas, and access rates. | Power is the constraint that most limits industry and households in Africa; the owner asked for the grid as an overlay (P65). | 1. The World Bank 2017 grid map, existing and planned lines, by voltage.<br>2. Gridfinder's modelled lines and electrified areas, labelled as a model (about 70% accurate within 1 km).<br>3. USGS power stations.<br>4. National, urban and rural access rates from the WDI.<br>5. The four power pools as AICD records them. | **In:** World Bank grid map (2017); gridfinder; USGS; WDI<br>**Out:** grid lines as vector tiles; a connected-areas layer | The World Bank grid map is in the store (#19): 62,001 lines, 56,863 existing and 4,923 planned; 3,229 lines are OpenStreetMap's and keep ODbL. USGS's power layers come from a commercial publisher (Cross-border Information / African Energy) and stay unpublished until its terms are read. Display follows #17. |  |
| **Infrastructure Pipelines** | planned | Show oil and gas pipelines and LNG terminals: product, origin, destination, length and status. | Pipelines carry the hydrocarbons that dominate several economies, often across borders. | 1. Global Energy Monitor's oil and gas trackers (CC BY 4.0), once the owner has downloaded them.<br>2. USGS's pipelines (661) and LNG terminals are in the store, but the pipelines' stated source is a commercial publisher (Cross-border Information / African Energy): unpublished until its terms are read.<br>3. Planned and existing pipelines kept apart, as published. | **In:** USGS Africa GIS (2021); Global Energy Monitor (CC BY 4.0, by form)<br>**Out:** pipeline lines and terminal points | Planned (step I3); waits on the owner's GEM download. |  |
| **Infrastructure National Data** | planned | Give each country's descriptive infrastructure values: connection to services, costs, PPI, wages and the resource economy, each with its year. | The owner asked for descriptive values beside the maps: connection to services, producer prices, wages, costs for industry and the resource economy (P65, P66). Each comes from a current publisher and shows its own year. | 1. Every series ingested whole through its database's adapter (P38).<br>2. Section templates of the Infrastructure dimension, bound by the ASI, rendered by the figure shells (System Sections and Figure Shells (athena-data)).<br>3. Every figure shows its year and source; a state the publisher does not cover is shown as not covered, never filled. | **In:** WDI; IMF PPI; FAOSTAT producer prices; ILOSTAT; Enterprise Surveys; LPI<br>**Out:** Infrastructure blocks in the country panel | Planned (step I5). The AICD is dropped (P66). |  |
| **Infrastructure Export Chains** | planned | Show how materials move out: each chain from a mine or field, by rail, road or pipeline, to the port that exports it and on to its destinations. | This is the Africa counterpart of the Canada atlas's trade corridors, and the story the owner asked for: how materials move out of the export hubs. | 1. A chain is a declared list of published segments (a USGS port's stated commodity source, the rail or road line, the port), marked derived, never a route we draw.<br>2. Landlocked states: their published corridors to the sea through neighbours.<br>3. Every chain names the sources of each of its segments. | **In:** the layers above<br>**Out:** chains highlighted on the map, with a card each | Planned (step I8). | Canada Economic Atlas (athena-data) · [Infrastructure Ports and Export Hubs](<ASI Infrastructure Section.md#the-layers>) |
| **Infrastructure Megaprojects** | planned | Show the great projects each country is proud of, such as dams, by a stated rule rather than by hand. | National-pride projects say where a state invests its future, and readers look for them first. | 1. A selection rule written before selecting, for example AID projects above a stated capital cost, and dams and power plants above a stated capacity.<br>2. Dams from GRanD and power plants from Global Energy Monitor, once their terms are read.<br>3. Each project with its source and article (Wikidata, CC0). | **In:** AID; Global Energy Monitor; GRanD; Wikidata<br>**Out:** project points with a short card | Planned; the terms of GEM and GRanD are not yet read. |  |

### Infrastructure National Data: its sources (P66)

- **Dropped:** the World Bank's *Africa Infrastructure: National Data* (the AICD). Its years stop in 2009 and it
  holds none of the values asked for, so the owner ruled it out (P66).
- **Connection to services:** the WDI (electricity, water, sanitation, internet, mobile), national, urban and rural.
- **Producer prices** (P66: PPI means producer prices):
  - the IMF's Producer Price Index dataset (`PPI`, SDMX, monthly vintages). It covers 16 of the 54 states: AGO, CAF,
    COG, DZA, EGY, ETH, GAB, GHA, GMB, KEN, MUS, SDN, SLE, TUN, ZAF, ZMB.
  - FAOSTAT's agricultural producer prices (CC BY 4.0) for the rest of the continent.
- **Wages:** ILOSTAT's minimum and median wages, once the owner has read its terms.
- **Costs for industry:** the World Bank Enterprise Surveys and the Logistics Performance Index (World Bank API).
- **The resource economy:** the WDI's rents by resource (oil, gas, coal, minerals, forest) as a share of GDP.

## Open questions

- AID's terms: may its data be shown and redistributed on a public site?
- **Infrastructure AID Projects:** The owner writes to aid@auda-nepad.org: may the data be shown and redistributed on a public site, with attribution?
- **Infrastructure AID Projects:** The owner creates the account; the key goes in `web/.env.local` or the adapter's environment, never in git.
- **Infrastructure Roads:** The tile tool: tippecanoe (BSD-2) or another; its licence is read before use.
- **Infrastructure Resources Output and Sales:** Which production source: USGS's yearbook tables (public domain), BGS World Mineral Statistics or World Mining Data? Terms first.
- **Infrastructure National Data:** ILOSTAT's terms (the owner reads them; the page has a bot check).

## Related

Canada Economic Atlas (athena-data)
