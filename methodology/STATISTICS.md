# Statistical method — where this is going

Written 2026-08-17, when the index carries 32 scoring indicators across 7
pillars and the indicator count is about to grow substantially.

Three questions, in order: what the statistical layer should eventually look
like, what has to be true before it can, and what is worth doing in the next two
or three iterations. Everything after that is gradual.

Every number below is measured from the shipped panel at the 2023 reference
year, not quoted from a plan.

---

## 0. One correction first, because it changes how the rest reads

**Geometric mean and equal weighting are not alternatives.** They sit on
different axes. This project currently offers four combinations of two separate
choices:

| method | how pillars are weighted | how pillar scores combine |
|---|---|---|
| `equal` | equal (1/7 each) | arithmetic mean |
| `geometric` | **equal (1/7 each)** | geometric mean |
| `pca` | fitted from the correlation structure | arithmetic mean |
| `entropy` | fitted from dispersion | arithmetic mean |

`asi/pipeline/score.py::geometric_composite` builds `w = np.full(v.shape,
1.0/v.size)` — it *is* equally weighted. `registry/weights.yaml` has no
`geometric` key for exactly this reason. So preferring geometric over equal is
really preferring **geometric aggregation at equal weights** over **arithmetic
aggregation at equal weights**. The weighting did not change.

That matters because the two axes have different problems and different fixes,
and because the grid is mostly empty: there is no geometric-PCA or
geometric-entropy composite, and nothing currently says whether there should be.

**The instinct is well founded.** UNDP switched the Human Development Index from
arithmetic to geometric aggregation in the 2010 report, specifically to reduce
compensability between dimensions — a country should not be able to buy its way
out of a collapsed dimension with strength elsewhere. The OECD/JRC *Handbook on
Constructing Composite Indicators* (2008) treats this as the standard reason to
choose a non-compensatory aggregator; Munda's work on non-compensatory
aggregation is the deeper reference. For an index whose subject is *stability*,
non-compensation is arguably the more honest default: a state with excellent
infrastructure and no rule of law is not "average".

**But it is not free, and its precondition is not currently met.** See §2.1.

---

## 1. What the end goal should look like

Seven properties. None is exotic; all are things a reviewer would ask about.

**1. The weighting policy is declared, not emergent.**
Equal *pillar* weights produce unequal *indicator* weights, because pillars hold
different numbers of indicators. Measured today: the heaviest indicator carries
**3.33×** the lightest — `pv_estimate` and `rl_estimate` at 5.95% of the
composite, `primary_gpi` / `secondary_gpi` / `femicide` at 1.79%. Nobody chose
that ratio; it fell out of pillar sizes and cross-listing. The end state is that
someone chose it, wrote down why, and a check enforces it.

**2. Uncertainty is a published output, not an appendix.**
The index should report an interval, not only a point rank. Worst-case Spearman
under adversarial re-weighting is **0.880**, and per-country quintile stability
ranges from 26% (Nigeria) to effectively 100%. B20's earlier finding — median
95% CI of ~22 places out of 54, with only 29.4% of country pairs separable — is
the number that belongs next to a published rank.

**3. All assumptions are varied jointly, not one at a time.**
Each assumption is currently tested in isolation (weights, then imputation, then
islands). Saisana, Saltelli & Tarantola (2005) is the standard argument for a
joint Monte Carlo over imputation × winsorisation × normalisation × aggregation
× weighting, reporting a rank distribution per country. Already on `ROADMAP.md`;
recorded here as the destination.

**4. Aggregation is chosen for a stated purpose and disclosed per view.**
Not "which method is right" but "which method answers which question".
Arithmetic answers *what is the average condition*. Geometric answers *how bad
is the worst dimension, given the rest*. Both are legitimate; publishing one
silently is not. The interface already has a lens control, so the plumbing
exists.

**5. New indicators pass an admission test before entering.**
As the count grows this becomes the load-bearing control. A candidate should
have to demonstrate adequate coverage, non-trivial variance, a defensible
polarity, and that it adds information rather than duplicating a series already
present. Without this, growth degrades the index while making it look more
thorough.

**6. The pillar structure is validated, not asserted.**
Seven pillars is a theoretical claim about the structure of stability, and it
should be checked against the data periodically — factor analysis, or a
clustering of the correlation matrix — with the check allowed to disagree.
Encouragingly it currently holds up: PC1 explains only **33.6%** of variance,
**14** components are needed for 90%, and 8 have eigenvalues above 1. The index
is genuinely multidimensional; it is not a noisy proxy for GDP.

**7. Goalposts and fitted weights are versioned and incrementally extendable.**
Adding an indicator must not force a re-anchoring of every historical score.

---

## 2. What has to be true first

Three preconditions, in dependency order.

### 2.1 Pillar F has to mean something before non-compensation is applied to it

A non-compensatory aggregator faithfully transmits the *worst* dimension into
the headline number. That is its purpose. It follows that a dimension measuring
the wrong thing does disproportionate damage under geometric aggregation — and
that is live right now:

| Country | rank (equal) | rank (geometric) | penalty | worst pillar |
|---|---:|---:|---:|---|
| Algeria | 16 | 45 | **−29** | F (4.4) |
| Egypt | 12 | 27 | −15 | F (8.7) |
| Libya | 42 | 51 | −9 | F (1.6) |
| Tunisia | 11 | 14 | −3 | F (22.8) |
| Cabo Verde | 4 | 6 | −2 | F (25.8) |

**6 of the 8 countries geometric penalises most have Pillar F as their worst
pillar**, and the Spearman correlation between the penalty and a country's worst
pillar score is **−0.417**. Pillar F is the pillar already flagged (backlog B17)
as negatively correlated with all six others, whose `co2_pc` indicator
correlates **−0.908** with GDP per capita — meaning it substantially rewards
poverty.

So the current effect of preferring geometric aggregation is to *amplify* the
one pillar known to be measuring something other than what it claims. The
aggregation instinct is right; the order of operations is wrong. **Fix F first.**

### 2.2 Normalisation and geometric aggregation interact

Geometric means are unstable near zero, and min-max normalisation manufactures
zeros: the worst observed performer lands at or near 0 by construction. Today
this is survivable only because pillars are internally *arithmetic* means, which
average the zeros away — **24 indicator cells are exactly 0** at 2023
(`co2_pc`, `femicide`, `freshwater_withdraw`, `gdp_growth_3yr_avg`,
`inflation_5yr_avg`, `intent_homicide`, `nonrenew_elec`), yet the lowest pillar
score is 1.65 (Libya, F).

Two consequences. If geometric aggregation is ever used *within* pillars, those
24 zeros become cliffs and the `SMALL = 1e-8` floor becomes load-bearing in a
way it is not today. And HDI uses **externally fixed** goalposts rather than
observed extremes partly for this reason, whereas this index derives goalposts
from winsorised observed data. That is a defensible choice, but it is a
different choice, and it should be a stated one rather than an inherited one.

### 2.3 Adding indicators currently re-anchors everything

`registry/goalposts.yaml` is frozen at version 2 and `02_panel.py
--freeze-goalposts` recomputes **all** of it. There is no way to add an
indicator without either re-anchoring every historical score or hand-editing a
frozen artifact. The same applies to the fitted PCA and entropy weights, whose
correlation structure changes the moment the indicator set does.

This is the hard blocker on the stated plan. It needs solving before the
indicator count moves, not after.

---

## 3. The scaling problem — read this before adding indicators

**Equal pillar weights mean each indicator's influence is 1 / (7 × pillar
size).** Adding an indicator to a pillar therefore reduces every existing
indicator in that pillar:

| Pillar | indicators | each carries | at +1 | change |
|---|---:|---:|---:|---:|
| A | 6 | 2.38% | 2.04% | −14% |
| B | 5 | 2.86% | 2.38% | −17% |
| C | 8 | 1.79% | 1.59% | −11% |
| D | 5 | 2.86% | 2.38% | −17% |
| E | 4 | 3.57% | 2.86% | **−20%** |
| F | 4 | 3.57% | 2.86% | **−20%** |
| G | 5 | 2.86% | 2.38% | −17% |

Three things follow.

1. **Uneven growth silently redistributes influence.** Going from 32 to, say, 60
   indicators unevenly will change every published score without any decision
   having been recorded. The change will be invisible in review, because no line
   of methodology text will have been edited.

2. **Cross-listing compounds it.** Five WGI indicators (`va`, `pv`, `ge`, `rl`,
   `cc`) sit in Pillar A *and* one other pillar, which is why they carry 5.95%
   against 1.79% for a singleton in Pillar C. That is backlog B18, and it gets
   worse, not better, as pillars grow at different rates.

3. **Redundancy is low now and will not stay that way.** Only **10 of 496**
   indicator pairs (2.0%) exceed |ρ| = 0.8 today. Adding indicators from the same
   source families is the fastest way to degrade that, and correlated indicators
   inside one pillar act as a hidden weight multiplier on whatever they jointly
   measure.

**The decision to make before growth, not during it:** does an indicator's
influence derive from its pillar's size (the status quo), or does the index
target a stated per-indicator weight and let pillar weights follow? There is no
neutral option — declining to choose is choosing the status quo.

---

## 4. What to do in the next two or three iterations

Ordered by dependency.

**N1 — Incremental goalposts. Blocks everything else.**
Let `--freeze-goalposts` compute bounds for *new* indicators only, leaving
existing bounds untouched, and bump the file version. Without this, no indicator
can be added without re-anchoring history.

**N2 — Indicator admission screening.**
A script that, for a candidate indicator, reports coverage by country and year,
share observed vs imputed, variance and degenerate-column checks, max |ρ|
against every existing indicator, and which effective weights it would change
and by how much. It refuses nothing; it makes the cost visible before the commit.

**N3 — Publish effective indicator weights.**
`verify/advisory.py` already computes them and prints them where nobody looks.
They belong in the methodology page and in the interface: a reader told that
pillars are equally weighted currently has no way to learn that one indicator
carries 3.33× another.

**N4 — Fix Pillar F (B17). Needs a decision from the maintainer.**
The precondition in §2.1. Until it is done, geometric aggregation amplifies a
known defect, and the honest options are to fix F or to keep arithmetic as the
published default and say why.

**N5 — Rank intervals (B20).**
The machinery now exists: the repaired sampler produces ~3,000 admissible
weightings per run and per-country quintile stability is already computed. An
interval per country is a short step from there, and it is the single change
that would most improve how defensible the published numbers are.

**N6 — State the aggregation choice.**
One paragraph in the methodology saying which composite is the headline, why,
and what the others are for. Cheap, and it converts an implicit choice into a
defended one.

---

## 5. Gradual, after that

- Joint Monte Carlo over all assumptions (§1.3) — the largest single item.
- Factor-analytic validation of the 7-pillar structure (§1.6), re-run whenever
  the indicator set changes materially.
- Non-compensatory aggregation *within* pillars, once §2.2's zero-handling is
  solved.
- Collapse or de-duplicate the WGI family (B18) once §3's weighting policy is
  settled — doing it before is fixing a symptom.
- Refit PCA and entropy weights on the grown indicator set, as a versioned,
  deliberate re-anchoring rather than a side effect.
- Sensitivity of the reference-year rule itself
  (`REFERENCE_YEAR_MIN_COVERAGE = 0.80`), which decides what year the entire
  site and the whole narrative corpus describe.

---

## Sources

- UNDP, *Human Development Report 2010* — the arithmetic → geometric switch and
  the compensability argument for it.
- OECD/JRC, *Handbook on Constructing Composite Indicators: Methodology and User
  Guide* (2008) — weighting, aggregation, and uncertainty analysis.
- Saisana, Saltelli & Tarantola (2005), *JRSS-A* 168(2) — uncertainty and
  sensitivity analysis as quality assessment for composite indicators.
- Munda, G. — non-compensatory aggregation in multi-criteria evaluation.
