---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# Pillar 1 Governance and State Capacity

> [!abstract] Goal
> Measure the state's capacity to make and carry out policy: effective administration, binding rules, controlled corruption, revenue and statistics.

## Why it exists

**Umbrella concept.** The state's ability to govern: an effective administration, rules that bind it and others, corruption it controls, revenue it raises, and statistics it keeps.

**How it bears on stability.** Interpeace: what matters is the quality of the state, not its mere presence; stability without an effective state needs coercion to survive.

**Why it is its own pillar.** Capacity is a stock built over decades; it is kept apart from voice (who is represented) and from security (what violence happens).

## Precise objectives

1. Every indicator passes the umbrella test.
2. Each WGI dimension appears at most once in the index, and the WGI's effective weight is published (28.9% in edition 1).
3. Every indicator reaches 33 of 54 states.

**The umbrella test (P58).** A pillar may be the sum of separate causes (formative), but only if every indicator is
an instance of the pillar's umbrella concept, stated above. An indicator that fails the test moves or leaves,
whatever its correlations.

## Indicators in the tested layout (variant B, 2026-10-18)

Direction: **+** means a higher value is more stable, **−** the reverse. Latest real value per state in 2016–2024.

| Indicator | Code | Direction |
| --- | --- | --- |
| Government effectiveness, WGI | GOV_WGI_GE | + |
| Rule of law, WGI | GOV_WGI_RL | + |
| Control of corruption, WGI | GOV_WGI_CC | + |
| CPIA property rights and rule-based governance | IQ.CPA.PROP.XQ | + |
| Statistical performance, overall | IQ.SPI.OVRL | + |
| Tax revenue, % of GDP | GC.TAX.TOTL.GD.ZS | + |

**Measurement model.** Mean inter-item |rho| inside the pillar: **.71** (reflective: its items cohere).

## Candidates to widen it

CPIA transparency (IQ.CPA.TRAN.XQ, 40 states) and public sector (IQ.CPA.PUBS.XQ, 40); WGI regulatory quality; V-Dem state capacity; World Justice Project and Open Budget Survey (terms to read); Afrobarometer trust in institutions (context).

## As built at edition 2, step 6 (athena-core #14)

| Indicator | Variable | Direction | Logged |
| --- | --- | --- | --- |
| Government Effectiveness, WGI estimated score | `ge_estimate` | + | no |
| Rule of Law, WGI estimated score | `rl_estimate` | + | no |
| Control of Corruption, WGI estimated score | `cc_estimate` | + | no |
| CPIA property rights and rule-based governance rating (1=low to 6=high) | `cpia_property_rights` | + | no |
| Statistical performance indicators (SPI): Overall score (scale 0-100) | `statistical_performance` | + | no |
| Tax revenue (% of GDP) | `tax_revenue` | + | yes |

**Descriptive** (shown, not scored): `rq_estimate`.

**At 2024:** mean score 48.18; 54 states reliable, 0 thin, 0 unreliable.

## Inputs and outputs

- **In:** the indicators above, from Athena's datasets
- **Out:** one pillar score per state and year, with its n, interval and reliability tier

## Where it stands

Built at edition 2, step 6 (athena-core #14), key `GOV`. Tax revenue sits at the admission floor (33 states). Regulatory quality is a near-duplicate of government effectiveness and is shown, not scored.

## Open questions

- Does regulatory quality belong here? It passes the umbrella, but adds a fourth WGI item.

## Related

[Appraisal World Bank WGI](<../ASI 06 Outputs and Site/ASI Appraisals.md#the-appraisals>)
