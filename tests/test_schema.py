"""
Canonical schema behaviour.

These types are the contract between the pipeline, the bundle, and the UI, so
their round-tripping and the reliability rules are worth pinning precisely.
Tests assert invariants, not current data values — a test that encodes today's
numbers passes for the wrong reason.
"""

import pytest

from asi.core.schema import (
    Provenance, Reliability, Polarity, WindowMode,
    IndicatorSpec, Observation, PillarScore, CompositeScore,
    classify_reliability, missing_keys,
    REQUIRED_COUNTRY_KEYS, REQUIRED_INDICATOR_KEYS,
)


# ── Provenance semantics ───────────────────────────────────────────────────────

def test_only_observed_counts_as_real():
    assert Provenance.OBSERVED.is_real
    for p in (Provenance.CARRIED_FORWARD, Provenance.INTERPOLATED,
              Provenance.REGIONAL_MEAN, Provenance.DERIVED, Provenance.ABSENT):
        assert not p.is_real, f"{p} must not count as a real measurement"


def test_imputed_set_is_exactly_the_inferred_kinds():
    imputed = {p for p in Provenance if p.is_imputed}
    assert imputed == {Provenance.CARRIED_FORWARD,
                       Provenance.INTERPOLATED,
                       Provenance.REGIONAL_MEAN}


def test_derived_is_not_imputed():
    """A per-capita conversion is computed from real data, not guessed."""
    assert not Provenance.DERIVED.is_imputed
    assert not Provenance.DERIVED.is_real


# ── Reliability rules ──────────────────────────────────────────────────────────

THRESHOLDS = dict(reliable_at=0.60, thin_at=0.40, max_imputed_share=0.50)


def test_full_coverage_is_reliable():
    assert classify_reliability(5, 5, 0, **THRESHOLDS) is Reliability.RELIABLE


def test_no_data_is_absent():
    assert classify_reliability(5, 0, 0, **THRESHOLDS) is Reliability.ABSENT
    assert classify_reliability(0, 0, 0, **THRESHOLDS) is Reliability.ABSENT


def test_thin_band():
    # 2 of 5 observed = 0.40 coverage, no imputation
    assert classify_reliability(5, 2, 0, **THRESHOLDS) is Reliability.THIN


def test_below_thin_is_unreliable():
    # 1 of 5 observed = 0.20
    assert classify_reliability(5, 1, 0, **THRESHOLDS) is Reliability.UNRELIABLE


def test_imputed_majority_overrides_good_coverage():
    """
    The rule that matters most: a pillar can look well-covered while being
    mostly regional averages. Imputation share must veto reliability.
    """
    result = classify_reliability(5, 4, 5, **THRESHOLDS)   # 5/9 used values imputed
    assert result is Reliability.UNRELIABLE


def test_boundaries_are_inclusive():
    assert classify_reliability(10, 6, 0, **THRESHOLDS) is Reliability.RELIABLE   # exactly 0.60
    assert classify_reliability(10, 4, 0, **THRESHOLDS) is Reliability.THIN       # exactly 0.40


def test_only_reliable_and_thin_are_displayable():
    assert Reliability.RELIABLE.displayable
    assert Reliability.THIN.displayable
    assert not Reliability.UNRELIABLE.displayable
    assert not Reliability.ABSENT.displayable


# ── Observation ────────────────────────────────────────────────────────────────

def make_obs(**kw):
    base = dict(
        iso3="GHA", variable_name="life_expect_tot",
        display_name="Life expectancy at birth, total (years)",
        series_code="SP.DYN.LE00.IN", database="wdi", year=2023,
    )
    base.update(kw)
    return Observation(**base)


def test_observation_round_trip():
    obs = make_obs(raw_value=64.1, score=72.5, provenance=Provenance.OBSERVED,
                   source_year=2023, polarity=Polarity.POSITIVE)
    assert Observation.from_dict(obs.to_dict()) == obs


def test_identity_excludes_value():
    """Identity must be stable across value changes — that is the whole point."""
    a = make_obs(score=10.0)
    b = make_obs(score=90.0)
    assert a.identity == b.identity


def test_identity_distinguishes_year():
    assert make_obs(year=2020).identity != make_obs(year=2021).identity


def test_staleness():
    assert make_obs(year=2024, source_year=2019).staleness == 5
    assert make_obs(year=2024, source_year=2024).staleness == 0
    assert make_obs(year=2024).staleness is None   # no underlying measurement


def test_observation_carries_its_own_label():
    """The UI must be able to render without consulting the registry."""
    obs = make_obs()
    assert obs.display_name and obs.series_code and obs.variable_name


# ── Aggregates ─────────────────────────────────────────────────────────────────

def test_pillar_coverage_ratio():
    ps = PillarScore(iso3="KEN", pillar_id="D", year=2023, score=55.0,
                     n_indicators=5, n_observed=3, n_imputed=2)
    assert ps.coverage_ratio == pytest.approx(0.6)
    assert ps.imputed_share == pytest.approx(0.4)


def test_pillar_ratios_safe_when_empty():
    ps = PillarScore(iso3="KEN", pillar_id="D", year=2023, score=None)
    assert ps.coverage_ratio == 0.0
    assert ps.imputed_share == 0.0


def test_pillar_round_trip():
    ps = PillarScore(iso3="KEN", pillar_id="D", year=2023, score=55.0,
                     n_indicators=5, n_observed=3, n_imputed=2,
                     reliability=Reliability.THIN, contributing=("a", "b"))
    assert PillarScore.from_dict(ps.to_dict()) == ps


def test_composite_round_trip():
    cs = CompositeScore(iso3="MUS", year=2024, method="equal", score=73.5,
                        rank=1, n_pillars_used=7, reliability=Reliability.RELIABLE)
    assert CompositeScore.from_dict(cs.to_dict()) == cs


# ── IndicatorSpec ──────────────────────────────────────────────────────────────

def test_indicator_spec_round_trip():
    spec = IndicatorSpec(
        variable_name="gdp_pc_ppp", display_name="GDP per capita, PPP",
        series_code="NY.GDP.PCAP.PP.CD", database="wdi", role="scoring",
        polarity=Polarity.POSITIVE, pillars=("B",), log_transform=True,
        window_mode=WindowMode.MOST_RECENT, goalpost_min=6.0, goalpost_max=11.0,
    )
    assert IndicatorSpec.from_dict(spec.to_dict()) == spec


def test_goalposts_reported_missing_until_set():
    spec = IndicatorSpec(
        variable_name="x", display_name="X", series_code="X.Y", database="wdi",
        role="scoring", polarity=Polarity.POSITIVE, pillars=("A",),
    )
    assert not spec.has_goalposts


# ── Bundle contract ────────────────────────────────────────────────────────────

def test_missing_keys_detects_gaps():
    record = {"iso3": "GHA", "name": "Ghana"}
    gaps = missing_keys(record, REQUIRED_COUNTRY_KEYS)
    assert "scores" in gaps and "pillar_scores" in gaps


def test_missing_keys_empty_when_complete():
    record = {k: None for k in REQUIRED_INDICATOR_KEYS}
    assert missing_keys(record, REQUIRED_INDICATOR_KEYS) == []
