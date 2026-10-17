"""
03_robustness.py — how much do the rankings depend on our choices?

OECD Handbook step 7. A composite indicator that only reports one number hides
the fact that the number rests on decisions — which weights, whether to include
estimated data, whether structurally advantaged countries belong in the
comparison. This stage varies those decisions and reports how far the ranking
moves.

Runs at the reference year, on the panel. Ranking stability is a within-year
statement: comparing a 2003 ranking to a 2019 one measures how the continent
changed, not how fragile the method is.

    python 03_robustness.py

Output: data/panel/robustness.json  (and a console summary)
"""

import json
import logging
import sys
import time as _time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from asi.core.constants import (
    PILLAR_DEFS, WEIGHT_MIN, WEIGHT_MAX, SMALL, ACTIVE_PROFILE,
    MIN_PILLARS_FOR_COMPOSITE,
)
from asi import results as D
from asi.pipeline import score as score_mod

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s",
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

OUT_FILE = Path("data/panel/robustness.json")

N_RANDOM_WEIGHTS = 10000
RNG_SEED = 20260808   # fixed so the reported figures are reproducible

#: Quintiles, because that is the granularity the reader is offered.
#: A rank moving 3 places inside the same fifth of the continent is noise; a
#: country crossing from the second fifth to the third is the claim a reader
#: would actually repeat, and it is what a per-country stability figure should
#: be about.
N_QUANTILES = 5


def _ranking(scores: pd.Series) -> pd.Series:
    return scores.dropna().rank(ascending=False, method="min")


def _quintile(ranking: pd.Series, q: int = 5) -> pd.Series:
    """
    Which fifth of the ranked field each country sits in, best fifth = 1.

    Computed from rank position rather than from score, so the bands hold a
    fixed number of countries and a shift between them always means a country
    overtook another. Cutting on score instead would let every country change
    band because one outlier moved.
    """
    if ranking.empty:
        return ranking
    return np.ceil(ranking.rank(method="min") * q / len(ranking)).astype(int)


def _agreement(a: pd.Series, b: pd.Series) -> float:
    """Spearman correlation between two rankings over their shared countries."""
    common = a.index.intersection(b.index)
    if len(common) < 3:
        return float("nan")
    return float(spearmanr(a.loc[common], b.loc[common]).statistic)


def main() -> int:
    t0 = _time.time()
    panel = D.load()
    year = panel.reference_year
    logger.info("Robustness at the reference year: %d", year)

    pil = panel.pillar_scores
    at_year = pil[pil["year"] == year]
    wide = at_year.pivot_table(index="iso3", columns="pillar_id",
                               values="score", aggfunc="first")
    pillars = [p for p in PILLAR_DEFS if p in wide.columns]
    logger.info("  %d countries x %d pillars", len(wide), len(pillars))

    weights = panel.meta.get("weights", {})
    baseline = score_mod.weighted_composite(wide, weights["equal"])
    base_rank = _ranking(baseline)
    results: dict = {"year": year, "n_countries": int(len(wide))}

    # ── 1. across weighting methods ───────────────────────────────────────────
    logger.info("")
    logger.info("1. Agreement between weighting methods")
    method_scores = {
        "equal":     baseline,
        "pca":       score_mod.weighted_composite(wide, weights["pca"]),
        "entropy":   score_mod.weighted_composite(wide, weights["entropy"]),
        "geometric": score_mod.geometric_composite(wide, pillars, SMALL),
    }
    results["methods"] = {}
    for name, s in method_scores.items():
        if name == "equal":
            continue
        rho = _agreement(base_rank, _ranking(s))
        moves = (base_rank - _ranking(s)).abs()
        results["methods"][name] = {
            "spearman_vs_equal": round(rho, 4),
            "max_rank_shift": int(moves.max()) if not moves.empty else None,
            "median_rank_shift": float(moves.median()) if not moves.empty else None,
        }
        logger.info("   %-10s rho=%.4f  median shift=%.1f  max shift=%d",
                    name, rho, moves.median(), int(moves.max()))

    # ── 2. adversarial weights ────────────────────────────────────────────────
    # The worst-case question: within the allowed weight bounds, how badly can a
    # ranking be made to disagree with equal weights? Searched rather than
    # optimised — the objective is a rank correlation, a step function that
    # gradient methods cannot descend.
    logger.info("")
    logger.info("2. Worst-case weighting inside [%.2f, %.2f]", WEIGHT_MIN, WEIGHT_MAX)
    rng = np.random.default_rng(RNG_SEED)
    n = len(pillars)
    worst_rho, worst_w = 1.0, None
    base_quintile = _quintile(base_rank, N_QUANTILES)

    for i in range(n):   # deterministic corners: each pillar pushed to its cap
        w = np.full(n, (1.0 - WEIGHT_MAX) / (n - 1))
        w[i] = WEIGHT_MAX
        if w.min() < WEIGHT_MIN - 1e-9:
            continue
        rho = _agreement(base_rank, _ranking(
            score_mod.weighted_composite(wide, dict(zip(pillars, w)))))
        if rho < worst_rho:
            worst_rho, worst_w = rho, w.copy()

    # Sample inside the polytope rather than sampling the simplex and hoping.
    #
    # A plain `rng.dirichlet(np.ones(7))` puts almost no mass in the admissible
    # region: 23 of 1000 draws survived the [WEIGHT_MIN, WEIGHT_MAX] filter, so
    # the published "robust" verdict rested on ~23 evaluations of a
    # seven-dimensional body — and the worst vector it reported was one of the
    # deterministic corners, meaning the random search contributed nothing at
    # all. Shifting the simplex by WEIGHT_MIN first satisfies the lower bound by
    # construction and leaves only the cap to reject on, which lifts acceptance
    # by more than an order of magnitude for the same number of draws.
    floor = WEIGHT_MIN * n
    accepted, quintile_hits = 0, pd.Series(0, index=base_rank.index, dtype=int)

    for _ in range(N_RANDOM_WEIGHTS):
        w = WEIGHT_MIN + (1.0 - floor) * rng.dirichlet(np.ones(n))
        if w.max() > WEIGHT_MAX:
            continue
        accepted += 1
        ranking = _ranking(score_mod.weighted_composite(wide, dict(zip(pillars, w))))
        rho = _agreement(base_rank, ranking)
        if rho < worst_rho:
            worst_rho, worst_w = rho, w.copy()

        same = _quintile(ranking).reindex(base_rank.index) == base_quintile
        quintile_hits += same.fillna(False).astype(int)

    verdict = ("robust" if worst_rho >= 0.90 else
               "moderately sensitive" if worst_rho >= 0.80 else "sensitive")

    # A single global verdict answers "does the ranking survive re-weighting?"
    # for the continent and for nobody in particular. A reader arrives at one
    # country's page, and "robust" tells them nothing about whether *that*
    # country's position is an artefact of the weights. The per-country share
    # below is the same experiment reported at the granularity it is read at.
    stability = (quintile_hits / accepted) if accepted else quintile_hits.astype(float)
    ranked = stability.sort_values()
    results["adversarial_weights"] = {
        "method": ("deterministic corners + Dirichlet on the shifted simplex "
                   f"(w = {WEIGHT_MIN} + {1 - floor:.2f} x Dir(1), cap {WEIGHT_MAX})"),
        "n_sampled": N_RANDOM_WEIGHTS,
        "n_within_bounds": accepted,
        "acceptance_rate": round(accepted / N_RANDOM_WEIGHTS, 4),
        "worst_spearman": round(worst_rho, 4),
        "worst_weights": {p: round(float(x), 4) for p, x in zip(pillars, worst_w)}
                         if worst_w is not None else None,
        "verdict": verdict,
        "quintile_stability": {
            "definition": (f"share of admissible weightings that leave the country "
                           f"in its published {N_QUANTILES}-quantile"),
            "n_weightings": accepted,
            "median": round(float(stability.median()), 4) if accepted else None,
            "least_stable": {i: round(float(v), 4) for i, v in ranked.head(8).items()},
            "per_country": {i: round(float(v), 4) for i, v in stability.items()},
        },
    }
    logger.info("   worst rho=%.4f over %d in-bounds vectors (%.0f%% accepted) -> %s",
                worst_rho, accepted, 100 * accepted / N_RANDOM_WEIGHTS, verdict)
    if accepted:
        logger.info("   quintile stability: median %.0f%%; least stable: %s",
                    100 * stability.median(),
                    ", ".join(f"{i} {100*v:.0f}%" for i, v in ranked.head(5).items()))

    # ── 3. dropping estimated data ────────────────────────────────────────────
    # If the ranking only holds because gaps were filled, that is worth knowing.
    #
    # This used to filter *pillar* scores to reliability == "reliable" and call
    # the result "measured only". At the 2023 reference year Pillar C has zero
    # reliable countries, so the filter did not exclude estimated data — it
    # deleted Pillar C for all 54 countries and let weighted_composite
    # renormalise the remaining six. That renormalisation is also why it
    # reported countries_no_longer_scoreable: 0: nobody dropped out because
    # every country still had six pillars. The diagnostic answered a question
    # nobody asked, and answered it reassuringly.
    #
    # Rebuilt at cell level from observations.csv. A cell counts only if the
    # pipeline marked it `observed` — not carried forward, not regionally
    # imputed — and pillars are re-formed from whatever survives, so a country
    # can genuinely fall below MIN_PILLARS_FOR_COMPOSITE and be reported as
    # unscoreable rather than quietly reweighted.
    logger.info("")
    logger.info("3. Rebuilding from directly measured cells only")
    obs = panel.observations
    measured = obs[(obs["year"] == year) & (obs["role"] == "scoring")
                   & (obs["provenance"] == "observed")]

    members = {pid: meta["indicators"] for pid, meta in panel.pillars.items()}
    strict_pillars: dict[str, dict[str, float]] = {}
    # How thin each rebuilt pillar is. Without this, "0 countries became
    # unscoreable" reads as reassurance when it may only mean every pillar kept
    # one surviving indicator out of five — which is exactly the kind of
    # comfortable zero the previous version of this check produced.
    shares: list[float] = []
    for pid in pillars:
        rows = measured[measured["variable_name"].isin(members.get(pid, []))]
        if rows.empty:
            continue
        strict_pillars[pid] = rows.groupby("iso3")["score"].mean().to_dict()
        size = len(members.get(pid, [])) or 1
        shares += list(rows.groupby("iso3").size() / size)

    strict = pd.DataFrame(strict_pillars).reindex(index=wide.index,
                                                  columns=pillars)
    usable = strict.notna().sum(axis=1)
    scoreable = usable >= MIN_PILLARS_FOR_COMPOSITE
    strict_scores = score_mod.weighted_composite(strict[scoreable], weights["equal"])

    strict_rank = _ranking(strict_scores)
    rho = _agreement(base_rank, strict_rank)
    shifts = (base_rank.reindex(strict_rank.index) - strict_rank).abs().dropna()

    results["measured_only"] = {
        "basis": ("composites rebuilt from observations.csv cells with "
                  "provenance == 'observed'; pillars re-formed from the "
                  "survivors, not filtered by pillar-level reliability"),
        "n_cells_kept": int(len(measured)),
        "n_cells_total": int(((obs["year"] == year)
                              & (obs["role"] == "scoring")).sum()),
        "spearman_vs_baseline": round(rho, 4) if not np.isnan(rho) else None,
        "min_pillars_required": MIN_PILLARS_FOR_COMPOSITE,
        "countries_no_longer_scoreable": int((~scoreable).sum()),
        "unscoreable": sorted(usable[~scoreable].index),
        "median_usable_pillars": float(usable.median()),
        "median_indicator_share_per_pillar": (round(float(np.median(shares)), 4)
                                              if shares else None),
        "pillar_years_below_half_measured": int(sum(1 for s in shares if s < 0.5)),
        "n_pillar_years_rebuilt": len(shares),
        "median_rank_shift": float(shifts.median()) if not shifts.empty else None,
        "max_rank_shift": int(shifts.max()) if not shifts.empty else None,
    }
    logger.info("   kept %d of %d scoring cells; %d countries fall below %d usable "
                "pillars", len(measured),
                int(((obs["year"] == year) & (obs["role"] == "scoring")).sum()),
                int((~scoreable).sum()), MIN_PILLARS_FOR_COMPOSITE)
    logger.info("   rho=%.4f  |  survivors move a median of %s places", rho,
                f"{shifts.median():.1f}" if not shifts.empty else "n/a")

    # ── 4. excluding island states ────────────────────────────────────────────
    logger.info("")
    logger.info("4. Excluding island states")
    mainland = wide.drop(index=[i for i in ACTIVE_PROFILE.island_states
                                if i in wide.index], errors="ignore")
    m_rank = _ranking(score_mod.weighted_composite(mainland, weights["equal"]))
    shifts = (base_rank.reindex(m_rank.index) - m_rank).abs()
    results["islands_excluded"] = {
        "n_removed": int(len(wide) - len(mainland)),
        "median_rank_shift": float(shifts.median()) if not shifts.empty else None,
        "max_rank_shift": int(shifts.max()) if not shifts.empty else None,
    }
    logger.info("   removed %d; remaining countries move a median of %.1f places",
                len(wide) - len(mainland), shifts.median())

    # ── 5. most and least stable countries ────────────────────────────────────
    spread = pd.DataFrame({k: _ranking(v) for k, v in method_scores.items()})
    spread["range"] = spread.max(axis=1) - spread.min(axis=1)
    volatile = spread.sort_values("range", ascending=False).head(8)
    # Min/max over the method columns only. `range` was appended to this frame
    # two lines up, so a whole-row min() returns the range whenever a country's
    # spread is narrower than its best rank — which silently published four of
    # these eight entries with a min equal to their range.
    methods = list(method_scores)
    results["rank_spread_across_methods"] = {
        iso3: {"min": int(r[methods].min()),
               "max": int(r[methods].max()),
               "range": int(r["range"])}
        for iso3, r in volatile.iterrows()
    }
    logger.info("")
    logger.info("5. Countries whose rank depends most on the method chosen")
    for iso3, r in volatile.head(5).iterrows():
        name = panel.countries.get(iso3, {}).get("name", iso3)
        logger.info("   %-26s ranks %d-%d across methods", name,
                    int(r.min()), int(r.max()))

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(results, indent=1), encoding="utf-8")
    logger.info("")
    logger.info("Wrote %s in %.1fs", OUT_FILE, _time.time() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
