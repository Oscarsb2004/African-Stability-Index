# ASI Refinement Roadmap

*Created 2026-07-14 from the full methodology review ([`METHODOLOGY_REVIEW.md`](METHODOLOGY_REVIEW.md)
— read that first for the evidence behind every item). Phases are ordered: cheap
truth-restoring work before score-changing work. Every phase ends with a green
`python 00_audit.py` **and** `python 00_evaluate.py`, plus a `references.md` entry.*

**Score-changing phases (1, 2, 3a) require re-freezing the evaluation baseline afterwards:**
delete `data/baseline/01_raw_pull_BASELINE.xlsx` only if the *raw pull* changed; otherwise
just re-run the pipeline and both verifiers.

---

## ✅ Completed (July 2026, for context)

- [x] Pipeline logic fixes: PCA negative-loading exclusion, BoD valid-pillar LP restriction, MaxS SLSQP → random-restart search
- [x] IDP per-capita conversion (`02_clean.py` Step 1b) — resolved size bias
- [x] rq_estimate de-cross-listing (A only, was A+B+G at 2.4×)
- [x] Independent verification script `00_evaluate.py` (31/31 PASS, frozen baseline, independent solvers)
- [x] Dashboard fixes: Dash 4 dropdown clipping (assets/asi.css), assets path pinning, deployment scaffolding
- [x] Full OECD 10-step methodology review + this roadmap

---

## Phase 0 — Documentation truth ✅ DONE 2026-07-14 · no score changes

Restored sync between docs, UI, and code (evidence: `METHODOLOGY_REVIEW.md` §B).

- [x] **IQR multiplier resolved**: `constants.py:57-60` already carries a deliberate,
  statistically-argued rationale for k=2.0 (n=54 → 1.5 over-clips mid-distribution). Not
  accidental — kept 2.0, documented the rationale in references.md/.yaml. No score change.
- [x] references.md: title AII → ASI; Stage-05 implemented; MaxS random-restart (not SLSQP);
  PCA negative-loading exclusion documented; BoD valid-pillar restriction + n<4 fallback;
  alpha threshold reconciled (0.60 gate vs 0.70 convention, mixed-polarity caveat);
  pillar sizes C=8; winsorisation-sheet description; verified-against-code footer
- [x] references.yaml synced (same facts) + corrected its false "consumed by dashboard" header
- [x] Dashboard: "36 Indicators" → 32 (header + stat card); rq_estimate 2.4× claim → accurate
  WGI cross-listing statement; IDP box reframed as resolved (per-capita normalization)
- [x] Verified: dashboard renders (32, no errors), `00_evaluate.py` 31/31 (scores unchanged)

## Phase 1 — Construct fixes 🔴 scores change · ~1 session

- [ ] **GPI distance-from-parity**: transform `primary_gpi`/`secondary_gpi` via `min(GPI, 2−GPI)` in `02_clean.py` (derived step, like IDP conversion); polarity stays positive. Evidence: 17/54 resp. 25/54 countries currently exceed 1.0 and get *rewarded* for over-parity.
- [ ] **Replace `firm_foreign_owned`** (negative item-rest −0.10; data back to 2006). Candidate: domestic credit to private sector, `FS.AST.PRVT.GD.ZS`. Screen coverage first.
- [ ] **Codify a selection rule** in references.md and enforce in `00_audit.py`: scoring role requires ≥ 50% real (unfilled) observations AND median data year ≥ 2018. Test case: `femicide` (18/54 real, 26 regional fills) → drop or demote to descriptive.
- [ ] **Explicit log rule**: "log1p iff post-fill skew > 1 and min ≥ 0, applied *before* winsorization." Re-derive all `log_transform` flags (currently 7 non-flagged indicators exceed skew 1.0; mort_infant is double-treated). Update YAMLs + justifications.

## Phase 2 — Pillar F redesign 🔴 scores change · ~1–2 sessions

Reframe Environmental pillar as *climate/resource vulnerability* (ND-GAIN
exposure–sensitivity–capacity model). Current state: weakest pillar (item-rest 0.21–0.44),
`co2_pc` ρ = −0.91 with GDP/capita (inverted wealth proxy), PCA excludes the pillar.

- [ ] Replace `co2_pc` with vulnerability-side series; screen WDI candidates for coverage: climate-disaster exposure, water stress `ER.H2O.FWST.ZS`, renewable share `EG.FEC.RNEW.ZS` (positive framing), arable land per capita, cereal import dependence
- [ ] Resolve `nonrenew_elec` ↔ `elec_access_tot` contradiction (likely: drop nonrenew_elec)
- [ ] Re-examine `agri_land` positive polarity once the new pillar frame exists
- [ ] **Acceptance criteria**: all Pillar F item-rest correlations > 0.3; PCA no longer excludes F

## Phase 3 — Statistical rigor 🟡 ~1 session

- [ ] Cronbach's alpha on **polarity-corrected normalized** values (02 diagnostics currently uses raw mixed-polarity → uninterpretable warnings)
- [ ] Joint Monte Carlo uncertainty in `05_robustness.py`: sample imputation on/off × winsorization on/off × method × weight noise; report per-country **rank intervals** (Saisana, Saltelli & Tarantola 2005)
- [ ] Replace ad-hoc confidence band (`2.0 + pct_filled × 26.7`) with the MC rank interval
- [ ] Add cross-pillar redundancy check to `00_audit.py` (|ρ| > 0.8 across pillars; currently invisible: gdp_pc_ppp×co2_pc −0.91, gdp_pc_ppp×elec_access +0.81)

## Phase 4 — Transparency (dashboard) 🟢 no score changes · ~½ session

- [ ] Per-country **median data year** + oldest observation in the data-quality panel (education data is effectively 2017)
- [ ] **Effective-weights table** in Methodology tab (cross-listed WGI vars carry 1.68–1.90× a median indicator; Pillar C members 0.57×)
- [ ] WGI-reliance disclosure (6/32 indicators = 28.9% of composite; Pillar A 100%, E 50%, G 40%)
- [ ] Show fill provenance (stage-1 lookback vs stage-2 regional) in indicator drill-down

## Phase 5 — External validation 🟢 ~½–1 session

- [ ] Full 54-country Spearman vs **IIAG 2024** overall score (not just top/bottom-10), **FSI 2025**, and WGI PV; add to audit
- [ ] Divergence table: countries ranked > 10 places apart from peers, with written interpretation (divergence is expected — ASI measures more than governance — but must be explainable)

## Phase 6 — Future architecture 🔵 design decisions first

- [ ] **Fixed goalposts decision**: if editions should be comparable over time, freeze per-indicator normalization bounds in the registry (HDI/ND-GAIN precedent) instead of sample min-max
- [ ] Adopt IIAG-style **edition discipline**: indicator changes batched to editions; recompute full back-series on structural change
- [ ] Optional: run the dataset through JRC **COIN Tool / COINr** as a third-party methodological cross-check

---

### Key references

OECD/JRC Handbook (2008) · [JRC 10-Step Pocket Guide](https://knowledge4policy.ec.europa.eu/sites/default/files/10-step-pocket-guide-to-composite-indicators-and-scoreboards.pdf) · [IIAG 2024 methodology](https://assets.iiag.online/2024/2024-IIAG-methodology_EN.pdf) · [ND-GAIN methodology](https://gain.nd.edu/our-work/country-index/methodology/) · Saisana, Saltelli & Tarantola (2005) *JRSS-A* 168(2)
