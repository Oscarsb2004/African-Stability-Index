"""
The robustness stage, which reported a reassuring verdict it had not earned.

Two defects, both of the same kind: a diagnostic that looked like it was testing
something and was not.

  - the adversarial-weights search sampled `rng.dirichlet(np.ones(7))` and threw
    away anything outside [WEIGHT_MIN, WEIGHT_MAX]. 23 of 1000 draws survived,
    so "robust" rested on 23 evaluations of a seven-dimensional body — and the
    worst vector it reported was one of the deterministic corners, so the random
    search had contributed nothing at all.
  - `measured_only` filtered *pillar* scores to reliability == "reliable". At
    2023 Pillar C has zero reliable countries, so the filter deleted Pillar C
    for everyone and `weighted_composite` renormalised the rest. Its headline
    finding — `countries_no_longer_scoreable: 0` — was an artifact of that
    renormalisation, not a fact about the data.

Both are now checked by construction rather than by reading the output and
finding it agreeable.
"""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from asi.core.constants import (  # noqa: E402
    MIN_PILLARS_FOR_COMPOSITE, PILLAR_DEFS, WEIGHT_MAX, WEIGHT_MIN,
)

_spec = importlib.util.spec_from_file_location(
    "robustness", ROOT / "03_robustness.py")
robustness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(robustness)


@pytest.fixture(scope="module")
def published():
    path = ROOT / "data" / "panel" / "robustness.json"
    if not path.exists():
        pytest.skip("no robustness.json; run 03_robustness.py")
    return json.loads(path.read_text(encoding="utf-8"))


# ── the sampler ────────────────────────────────────────────────────────────────

def _draw(n, rng):
    """The sampler as the stage implements it, restated from the rule."""
    return WEIGHT_MIN + (1.0 - WEIGHT_MIN * n) * rng.dirichlet(np.ones(n))


def test_the_shifted_simplex_satisfies_the_lower_bound_by_construction():
    """
    Half the point of the shift. Rejecting on both bounds is what made the old
    acceptance rate 2.3%; shifting first means only the cap can reject.
    """
    rng = np.random.default_rng(0)
    n = len(PILLAR_DEFS)
    for _ in range(2000):
        w = _draw(n, rng)
        assert w.min() >= WEIGHT_MIN - 1e-12
        assert abs(w.sum() - 1.0) < 1e-9


def test_the_sampler_accepts_far_more_than_the_one_it_replaced():
    """
    The defect measured rather than asserted. Both samplers are run here so the
    comparison is a fact about this machine, not a number copied from a changelog.
    """
    n = len(PILLAR_DEFS)
    trials = 5000

    rng = np.random.default_rng(1)
    old = sum(1 for _ in range(trials)
              if (w := rng.dirichlet(np.ones(n))).min() >= WEIGHT_MIN
              and w.max() <= WEIGHT_MAX)

    rng = np.random.default_rng(1)
    new = sum(1 for _ in range(trials) if _draw(n, rng).max() <= WEIGHT_MAX)

    assert old / trials < 0.05, "the old sampler was supposed to be the problem"
    assert new / trials > 0.20, f"acceptance {new / trials:.1%} is still too thin"
    assert new > old * 5


def test_accepted_vectors_are_admissible_weightings():
    rng = np.random.default_rng(2)
    n = len(PILLAR_DEFS)
    accepted = [w for _ in range(3000) if (w := _draw(n, rng)).max() <= WEIGHT_MAX]
    assert accepted, "no vector survived the cap"
    for w in accepted:
        assert w.min() >= WEIGHT_MIN - 1e-12
        assert w.max() <= WEIGHT_MAX + 1e-12
        assert abs(w.sum() - 1.0) < 1e-9


# ── quintiles ──────────────────────────────────────────────────────────────────

def test_the_best_ranked_country_is_in_the_first_fifth():
    import pandas as pd

    ranking = pd.Series(range(1, 51), index=[f"C{i:02d}" for i in range(50)],
                        dtype=float)
    q = robustness._quintile(ranking, 5)
    assert q.iloc[0] == 1
    assert q.iloc[-1] == 5
    assert set(q.unique()) == {1, 2, 3, 4, 5}


def test_the_bands_hold_equal_numbers_of_countries():
    """
    Cut on rank position, not on score: a band defined by score would let every
    country change band because one outlier moved.
    """
    import pandas as pd

    ranking = pd.Series(range(1, 51), index=[f"C{i:02d}" for i in range(50)],
                        dtype=float)
    counts = robustness._quintile(ranking, 5).value_counts()
    assert set(counts) == {10}


def test_an_empty_ranking_does_not_raise():
    import pandas as pd

    assert robustness._quintile(pd.Series(dtype=float), 5).empty


# ── the published file ─────────────────────────────────────────────────────────

def test_the_verdict_rests_on_a_real_search(published):
    """
    A verdict is only worth the number of admissible points behind it. 23 was
    not enough to describe a seven-dimensional polytope, and the published file
    said "robust" anyway.
    """
    a = published["adversarial_weights"]
    assert a["n_sampled"] >= 10000
    assert a["n_within_bounds"] >= 1000, (
        f"only {a['n_within_bounds']} admissible vectors — too few to claim "
        f"anything about the whole space")
    assert a["acceptance_rate"] > 0.20


def test_the_worst_case_is_not_merely_a_deterministic_corner(published):
    """
    The tell that the random search was doing nothing: the reported worst
    weights were exactly one pillar at the cap and the rest split evenly, which
    is a corner the loop above enumerates without sampling at all.
    """
    w = published["adversarial_weights"]["worst_weights"]
    assert w, "no worst-case vector recorded"
    values = sorted(w.values())
    at_cap = sum(1 for v in values if abs(v - WEIGHT_MAX) < 1e-3)
    assert not (at_cap == 1 and len(set(round(v, 4) for v in values)) == 2), (
        "the worst case is a deterministic corner; the sampler found nothing better")


def test_every_admissible_weighting_reported_is_admissible(published):
    w = published["adversarial_weights"]["worst_weights"]
    assert abs(sum(w.values()) - 1.0) < 1e-3
    assert min(w.values()) >= WEIGHT_MIN - 1e-3
    assert max(w.values()) <= WEIGHT_MAX + 1e-3


def test_stability_is_reported_per_country_not_only_as_one_verdict(published):
    """
    A reader arrives at one country's page. "Robust" says nothing about whether
    *that* country's position survives re-weighting, and for Nigeria it does not.
    """
    q = published["adversarial_weights"]["quintile_stability"]
    per = q["per_country"]
    assert len(per) >= 50, "a per-country statistic must cover the countries"
    assert all(0.0 <= v <= 1.0 for v in per.values())
    assert q["n_weightings"] == published["adversarial_weights"]["n_within_bounds"]
    assert q["median"] == pytest.approx(float(np.median(list(per.values()))), abs=1e-3)


def test_the_least_stable_countries_are_actually_the_least_stable(published):
    q = published["adversarial_weights"]["quintile_stability"]
    per, least = q["per_country"], q["least_stable"]
    cutoff = max(least.values())
    assert all(v >= cutoff - 1e-9 for k, v in per.items() if k not in least)


# ── measured_only ──────────────────────────────────────────────────────────────

def test_measured_only_works_from_cells_not_from_pillar_tiers(published):
    """
    The rewrite, pinned. Filtering pillar-level reliability deleted whole
    pillars — Pillar C has zero reliable countries at 2023 — and the composite
    silently renormalised over the survivors.
    """
    m = published["measured_only"]
    assert "observed" in m["basis"]
    assert m["n_cells_kept"] < m["n_cells_total"], "the filter excluded nothing"
    assert m["min_pillars_required"] == MIN_PILLARS_FOR_COMPOSITE


def test_the_unscoreable_count_is_reported_with_what_makes_it_readable(published):
    """
    `countries_no_longer_scoreable: 0` was the old headline and it was an
    artifact. Zero is a defensible answer now, but only alongside how thin the
    surviving pillars are — a pillar rebuilt from one indicator of five still
    counts as usable, and without that context the zero reads as reassurance.
    """
    m = published["measured_only"]
    assert m["countries_no_longer_scoreable"] == len(m["unscoreable"])
    assert m["n_pillar_years_rebuilt"] > 0
    assert m["pillar_years_below_half_measured"] <= m["n_pillar_years_rebuilt"]
    assert 0.0 < m["median_indicator_share_per_pillar"] <= 1.0


def test_rank_movement_is_reported(published):
    m = published["measured_only"]
    assert m["median_rank_shift"] is not None
    assert m["max_rank_shift"] >= m["median_rank_shift"]
