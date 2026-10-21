---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# Pillar 2 Political Voice and Representation

> [!abstract] Goal
> Measure whether citizens can choose and hold to account those who govern, and whether every group, women and youth included, is represented.

## Why it exists

**Umbrella concept.** Citizens' ability to take part in choosing and holding to account those who govern, and the representation of all groups in power.

**How it bears on stability.** Interpeace: a state cannot be called stabilised if it cannot represent the political views and rights of all citizens; women and youth are named.

**Why it is its own pillar.** Legitimacy is distinct from capacity: an effective state can exclude, and an inclusive one can be weak.

## Precise objectives

1. Reach at least four indicators from at least two publishers.
2. Every indicator passes the umbrella test.

**The umbrella test (P58).** A pillar may be the sum of separate causes (formative), but only if every indicator is
an instance of the pillar's umbrella concept, stated above. An indicator that fails the test moves or leaves,
whatever its correlations.

## Indicators in the tested layout (variant B, 2026-10-18)

Direction: **+** means a higher value is more stable, **−** the reverse. Latest real value per state in 2016–2024.

| Indicator | Code | Direction |
| --- | --- | --- |
| Voice and accountability, WGI | GOV_WGI_VA | + |
| Women in parliament, % of seats | SG.GEN.PARL.ZS | + |

**Measurement model.** Mean inter-item |rho| inside the pillar: **.14** (formative: two separate facets so far).

## Candidates to widen it

V-Dem electoral, participatory and egalitarian indices (CC BY-SA 4.0); Ethnic Power Relations, share of the population politically excluded (terms to read); Freedom House (blocked); Afrobarometer representation (context).

## As built at edition 2, step 6 (athena-core #14)

| Indicator | Variable | Direction | Logged |
| --- | --- | --- | --- |
| Voice and Accountability, WGI estimated score | `va_estimate` | + | no |
| Proportion of seats held by women in national parliaments (%) | `women_in_parliament` | + | no |

**Descriptive** (shown, not scored): none.

**At 2024:** mean score 36.15; 50 states reliable, 4 thin, 0 unreliable.

## Inputs and outputs

- **In:** the indicators above, from Athena's datasets
- **Out:** one pillar score per state and year, with its n, interval and reliability tier

## Where it stands

Built at edition 2, step 6 (athena-core #14), key `VOI`. The closest pair is Governance and Voice: rho .80 at 2024 on the real panel, against .64 in the prototype.

## Open questions

- With two items the pillar is thin; V-Dem is the first addition.

## Related

[Appraisal V-Dem](<../ASI 06 Outputs and Site/ASI Appraisals.md#the-appraisals>) · [Appraisal Freedom House](<../ASI 06 Outputs and Site/ASI Appraisals.md#the-appraisals>)
