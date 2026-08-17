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
)
from asi import results as D
from asi.pipeline import score as score_mod

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s",
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

OUT_FILE = Path("data/panel/robustness.json")

N_RANDOM_WEIGHTS = 1000
RNG_SEED = 20260808   # fixed so the reported figures are reproducible


def _ranking(scores: pd.Series) -> pd.Series:
    return scores.dropna().rank(ascending=False, method="min")


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

    for i in range(n):   # deterministic corners: each pillar pushed to its cap
        w = np.full(n, (1.0 - WEIGHT_MAX) / (n - 1))
        w[i] = WEIGHT_MAX
        if w.min() < WEIGHT_MIN - 1e-9:
            continue
        rho = _agreement(base_rank, _ranking(
            score_mod.weighted_composite(wide, dict(zip(pillars, w)))))
        if rho < worst_rho:
            worst_rho, worst_w = rho, w.copy()

    accepted = 0
    for _ in range(N_RANDOM_WEIGHTS):
        w = rng.dirichlet(np.ones(n))
        if w.min() < WEIGHT_MIN or w.max() > WEIGHT_MAX:
            continue
        accepted += 1
        rho = _agreement(base_rank, _ranking(
            score_mod.weighted_composite(wide, dict(zip(pillars, w)))))
        if rho < worst_rho:
            worst_rho, worst_w = rho, w.copy()

    verdict = ("robust" if worst_rho >= 0.90 else
               "moderately sensitive" if worst_rho >= 0.80 else "sensitive")
    results["adversarial_weights"] = {
        "method": "deterministic corners + Dirichlet sampling",
        "n_sampled": N_RANDOM_WEIGHTS,
        "n_within_bounds": accepted,
        "worst_spearman": round(worst_rho, 4),
        "worst_weights": {p: round(float(x), 4) for p, x in zip(pillars, worst_w)}
                         if worst_w is not None else None,
        "verdict": verdict,
    }
    logger.info("   worst rho=%.4f over %d in-bounds vectors -> %s",
                worst_rho, accepted, verdict)

    # ── 3. dropping estimated data ────────────────────────────────────────────
    # If the ranking only holds because gaps were filled, that is worth knowing.
    logger.info("")
    logger.info("3. Excluding pillars that are not fully measured")
    strict = at_year[at_year["reliability"] == "reliable"].pivot_table(
        index="iso3", columns="pillar_id", values="score", aggfunc="first")
    strict = strict.reindex(columns=pillars)
    strict_scores = score_mod.weighted_composite(strict, weights["equal"])
    rho = _agreement(base_rank, _ranking(strict_scores))
    n_lost = int(len(base_rank) - len(_ranking(strict_scores)))
    results["measured_only"] = {
        "spearman_vs_baseline": round(rho, 4) if not np.isnan(rho) else None,
        "countries_no_longer_scoreable": n_lost,
    }
    logger.info("   rho=%.4f  |  %d countries drop out entirely", rho, n_lost)

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
