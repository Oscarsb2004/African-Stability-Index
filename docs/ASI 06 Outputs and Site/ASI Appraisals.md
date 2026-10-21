---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-18"
updated: 2026-10-20
---

# ASI Appraisals

> [!abstract] Goal
> Appraise each state the way an NGO consultant would: with every credible index whose finished values the terms allow, each shown as its publisher prints it, the ASI one among them (P53).

## Why it exists

A single index invites false precision. Readers trust a picture that several careful institutions agree on, and
learn the most where they disagree.

## Precise objectives

1. Each index: its name, publisher, what it measures, edition year, value on its own scale, the publisher's own category or interval, a link.
2. Nothing is rescaled or combined into a new score; the only derived view is agreement across states ([ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>)).
3. Terms are read and dated before any index is shown; an index whose terms forbid it is left out.

## Inputs and outputs

- **In:** the publishers' downloads
- **Out:** the appraisal list in [ASI Stability Section](<ASI Stability Section.md>)

## Where it stands

Built and shown on the site for the World Bank's indices (WGI with its 90% intervals, CPIA, SPI, LPI), UNDP's HDI
and Transparency International's CPI with its 90% interval (athena-core #33). V-Dem waits on the owner's download.
Five are blocked on terms, and requests to the publishers are the owner's to send.

## The appraisals

One row per appraisal; each was its own note until P5 (P94). The requests to the publishers whose terms are
unclear are in [Appraisal Terms Requests](<../ASI 02 Inputs and Sources/Appraisal Terms Requests.md>).

**Every one shares these objectives:**

1. Show its latest value on the publisher's own scale, with the publisher's category and interval where printed.
2. Ingest it whole through an adapter (P38).
3. Include it in [ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>).

**In and out:**

- **In:** the publisher's download
- **Out:** one row in the Stability section's appraisal list

| Appraisal | Status | Goal | What it measures | Terms | Where it stands | Related |
| --- | --- | --- | --- | --- | --- | --- |
| **Appraisal World Bank WGI** | built | Show the six Worldwide Governance Indicators as the World Bank publishes them: a 0–100 governance score with its 90% interval. | Voice and accountability, political stability, government effectiveness, regulatory quality, rule of law and control of corruption, from many sources combined by an unobserved-components model. | CC BY 4.0 (World Bank terms, read 2026-10-17). | Built: `wgi-2026-09-25` in the store; all 54 states, latest 2025; shown with intervals on the site. | [Pillar 1 Governance and State Capacity](<../ASI 04 Methods/Pillar 1 Governance and State Capacity.md>) · [Pillar 2 Political Voice and Representation](<../ASI 04 Methods/Pillar 2 Political Voice and Representation.md>) |
| **Appraisal World Bank CPIA SPI and LPI** | built | Show three more World Bank assessments on their own scales: policy and institutions (CPIA), statistical performance (SPI) and logistics (LPI). | CPIA rates IDA countries' policies and institutions from 1 to 6; SPI scores national statistical systems 0–100; LPI scores trade logistics 1–5. | CC BY 4.0, inside the WDI (read 2026-10-17). | Built: CPIA covers 42 states, SPI 53, LPI 50 (latest LPI 2022). | [ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>) |
| **Appraisal UNDP HDI** | built | Show the Human Development Index and its companions as UNDP publishes them, with UNDP's own category. | Health, education and income combined, with inequality- and gender-adjusted companions. | CC BY 3.0 IGO; commercial use allowed; keep to the latest edition; print UNDP's note that the series is recalculated every year (read 2026-10-18). | Built: the adapter (athena-core #18) wrote `hdr-2025`, 200,004 values, 40 indicators, 206 areas, 1990–2023. Shown beside the ASI since athena-core #33: 54 states, latest 2023, with UNDP's note that each edition recalculates the whole series. | [ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>) · [Pillar 6 Human Development and Demography](<../ASI 04 Methods/Pillar 6 Human Development and Demography.md>) |
| **Appraisal TI CPI** | built | Show Transparency International's Corruption Perceptions Index on its 0–100 scale. | Perceived public-sector corruption, from expert and business surveys. | CC BY 4.0 for the CPI and its datasets; every change indicated; nothing made untrue (read 2026-10-18). | Built: the adapter (athena-core #18) wrote `cpi-2025`, 31,882 values: score, rank, standard error, the 90% interval and each source's score, 183 countries, 2012–2025. The workbook is Strict Open XML; the adapter rewrites its namespaces in memory. Shown beside the ASI since athena-core #33: 54 states, 2025, with the 90% interval. | [ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>) |
| **Appraisal V-Dem** | blocked | Show V-Dem's democracy indices, and draw on them for the voice pillar. | Electoral, liberal, participatory, deliberative and egalitarian democracy, from expert coding. | CC BY-SA 4.0, v16 of March 2026; derivatives under the same licence (read 2026-10-18). | Blocked: V-Dem's download page asks for an email address and consent to its privacy policy (seen 2026-10-18), which is the owner's to give. Once the file is downloaded, the adapter can read it from a `file:` address, as the ASI's frozen pull is read. | [ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>) · [Pillar 2 Political Voice and Representation](<../ASI 04 Methods/Pillar 2 Political Voice and Representation.md>) |
| **Appraisal INFORM Risk** | blocked | Show the EC JRC's INFORM risk of humanitarian crisis, with its classes. | Hazard and exposure, vulnerability, and lack of coping capacity; Mid 2026 edition (v073). | No licence on the download page; JRC reports are CC BY 4.0. Not used until confirmed. | Blocked: a request to the JRC is the owner's to send. | [ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>) · [Pillar 8 Environment and Climate Exposure](<../ASI 04 Methods/Pillar 8 Environment and Climate Exposure.md>) |
| **Appraisal ND-GAIN** | blocked | Show Notre Dame's climate vulnerability and readiness index. | Vulnerability (exposure, sensitivity, adaptive capacity) and readiness. | No licence stated; described as a free and open-access tool. Not used until confirmed. | Blocked: a request to Notre Dame is the owner's to send. | [ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>) · [Pillar 8 Environment and Climate Exposure](<../ASI 04 Methods/Pillar 8 Environment and Climate Exposure.md>) |
| **Appraisal Fragile States Index** | blocked | Show the Fund for Peace's Fragile States Index and its categories. | Twelve indicators of cohesion, economic, political and social pressure, from content analysis, data and expert review. | Values are free to download; no licence stated. Not used until confirmed. | Blocked: a request to the Fund for Peace is the owner's to send. | [ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>) |
| **Appraisal Global Peace Index** | blocked | Show the Institute for Economics and Peace's Global Peace Index. | Twenty-three indicators of safety, conflict and militarisation. | CC BY-NC-SA 4.0 after a request form; any user other than a non-profit or research institution is commercial (read 2026-10-18). | Blocked: the request form is the owner's to submit; non-commercial use only. | [ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>) |
| **Appraisal Ibrahim Index** | blocked | Show the Ibrahim Index of African Governance, the closest peer of the ASI. | African governance across security, participation, opportunity and human development; it covers all 54 states. | The data portal refused automated reading on 2026-10-18; terms not yet read. | Blocked: the terms are to be read in a browser, or asked of the Foundation. | [ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>) |
| **Appraisal Freedom House** | blocked | Show Freedom House's Freedom in the World scores and status. | Political rights and civil liberties. | Data by request; a content-permissions FAQ exists, not yet read. | Blocked: the permissions FAQ is to be read. | [ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>) · [Pillar 2 Political Voice and Representation](<../ASI 04 Methods/Pillar 2 Political Voice and Representation.md>) |

## Related

[ASI External Agreement](<../ASI 05 Verification/ASI External Agreement.md>) · Sources (athena-data)
