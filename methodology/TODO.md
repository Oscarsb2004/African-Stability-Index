# TODO — what must be updated in future

Things that are correct today but will stop being correct, and things only a
person can do. Separate from `BACKLOG.md`, which is defects and improvements
waiting to be worked. Nothing here is a bug right now.

Last reviewed: 2026-08-17.

---

## 1. Waiting on you (nobody else can do these)

| # | What | Why it needs you | Est. |
|---|---|---|---|
| U1 | **GitHub branch ruleset.** Settings → Rules → Rulesets → New branch ruleset. Tick only "Restrict deletions" and "Block force pushes". Target `phase-a-foundation` as well as `main`. | Requires repository-owner permissions in the web UI. | 2 min |
| U2 | **Decide Benefit-of-the-Doubt** (BACKLOG B11). It is labelled in `asi/dashboard/app.py:52`, justified by `WEIGHT_MIN`/`WEIGHT_MAX`, listed in `asi/core/schema.py:319`, pulls `pulp` as a dependency, and `verify/__init__.py` claims to verify it — but no LP exists anywhere in the tree, and it is unreachable in the UI because the dropdown builds from `PANEL.methods`. Implement it, or remove all five traces. | Changes what the index publishes. | your call |
| U3 | **TLS verification on the data pull** (BACKLOG B07). `01_pull.py:26-38` disables certificate verification process-wide while producing the frozen baseline the whole index is re-derived from. Needs to know whether the failure is a corporate proxy, a stale cert store, or something else. | Depends on your own network, which no agent can inspect. | 15 min |
| U4 | **Four methodology decisions** (BACKLOG B16, B17, B18, B20): what an unreliable pillar does to the composite; what Pillar F actually measures; whether to collapse the WGI family; whether to publish rank intervals. | Each changes the published numbers. | your call |
| U5 | **Country-page rank label** (BACKLOG B13, effort 3). The page renders the continental rank and labels it "in scope"; inside ECOWAS a country ranked #2 of 12 sees its continental position. Either pass the grouping into `view_country` or change the label. A strict xfail is already written and will start failing the build the moment it is fixed, so the note removes itself. | Which of the two the page should do is a product decision. | your call |

---

## 2. Will go stale on a schedule

| # | What | When it breaks | Where |
|---|---|---|---|
| S1 | **Reference year is 2023.** World Bank series report late, so 2024 is entirely unreliable and nothing is rankable in it. | Whenever WDI/WGI publish 2024 in full — re-run `01_pull.py`, then `02_panel.py`. | `data/panel/bundle.json` → `run.reference_year` |
| S2 | **Goalposts are frozen at version 2**, computed once over the whole panel. Re-running the pipeline will not re-anchor them, deliberately. | Only when a genuinely new extreme appears. Regenerating silently re-anchors every historical score, so it must be a decision, not a side effect. | `registry/goalposts.yaml`, `asi/pipeline/goalposts.py` |
| S3 | **PCA and entropy weights are frozen once-fitted.** | Same rule as S2 — refitting changes every published score for every year. | `registry/weights.yaml` |
| S4 | **Narrative recency.** Newest recent-item dates span 2025-05-01 to 2026-08-13. Stalest records: BWA, MUS, SLE, GAB, KEN. | Continuously. `verify/narrative.py`'s advisory pass reports the spread on every run. | `narrative/countries/*.yaml` |
| S5 | **No record has reached an AUDIT run.** 0 of 54; audit lands on iteration 4. 0 of 749 citations are confirmed as opened. | When records reach iteration 4 — until then the interface correctly says "cited", not "confirmed". | `narrative/state.yaml` |
| S6 | **IIAG benchmark is the 2023 edition**, and both sets are Africa-only by construction, so "4 of 5 agree" says nothing about placing an African state against a non-African one. | On each new IIAG release; the Africa-only limitation is Stage 4 work (B39–B42). | `verify/advisory.py:30-40` |

---

## 3. Update whenever the shape of the project changes

| # | Trigger | What must be updated |
|---|---|---|
| C1 | **A country is added or removed** (Western Sahara being the live case — see `EXCLUDED_AU_MEMBERS`) | `asi/core/countries.py`; every count in the UI must stay derived, never typed — contract check 2.1 fails the build on a hardcoded one |
| C2 | **An indicator is added or removed** | `registry/indicators.yaml`; goalposts must be regenerated deliberately (S2); `N_SCORING` flows through automatically |
| C3 | **A pillar is added or removed** | `PILLAR_DEFS` in `asi/core/constants.py` — everything else derives from it, including the geometric composite's weights |
| C4 | **`app.py` is split into a package** (planned: B47) | Nothing — contract checks now recurse with `rglob`. This was a live trap until B01 |
| C5 | **A new `verify/` layer is added** | Register it in `verify/run.py` LAYERS; it may import only `asi.core.constants` — `tests/test_verify_independence.py` fails the build otherwise |
| C6 | **A new consistency rule for the narrative corpus** | Add it to `verify/narrative.py` and wire it into `all_checks()`. `scripts/narrative_check.py` picks it up for free; a test fails if the script grows its own copy |
| C7 | **A new door to stored results is wanted** | There isn't one. `asi/results.py` is it, for every caller including scripts and `03_robustness.py` |

---

## 4. Known-incomplete, deliberately

| # | What | Status |
|---|---|---|
| K1 | `verify/panel.py` re-derives 38,276 of 43,200 scoring cells (88.6%). The remaining 11.4% are regional-mean estimates, which cannot be predicted from a country's own data by construction. | Closed by B05 — kept here because the 11.4% is a permanent property, not a gap to fill |
| K2 | The country page shows a continental rank under the label "in scope". `view_country` takes no grouping argument, so it cannot know the scope. Recorded as a strict xfail in `tests/test_dashboard_views.py`. | BACKLOG B13 — needs your call: follow the grouping, or relabel it "continental" |
| K3 | No LICENSE file — all rights reserved, by your decision. | Intentional |
| K4 | `main` is 89 commits behind `phase-a-foundation` (as of 2026-08-17). | Intentional while the branch is the working line |
| K5 | Local only, no public deployment. Security items in the backlog are written against a future public server, not today's setup. | Intentional |
