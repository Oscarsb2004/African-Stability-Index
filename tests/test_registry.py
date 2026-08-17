"""
Registry and configuration integrity.

Replaces the former root-level setup.py, which was a hand-rolled smoke-test
script. These are the same checks as real tests, so they run in CI and fail
loudly instead of printing OK/FAIL lines nobody reads.
"""

import pytest

from asi.core import (
    COUNTRIES, PILLAR_DEFS, WEIGHT_PRESETS, WEIGHT_MIN, WEIGHT_MAX,
    ACTIVE_PRESET, ACTIVE_PROFILE,
)
from asi.core.registry import PillarRegistry, IndicatorRegistry


# ── Country registry ───────────────────────────────────────────────────────────

def _bundle() -> dict:
    """
    The panel the pipeline actually published — an independent second source.

    Read as JSON rather than through `asi.results`, so a bug in the loader
    cannot make the registry and the panel agree with each other by agreeing
    with the same mistake.
    """
    import json

    from asi.core.constants import PROJECT_ROOT

    path = PROJECT_ROOT / "data" / "panel" / "bundle.json"
    if not path.exists():
        pytest.skip("no published panel on disk; run 02_panel.py")
    return json.loads(path.read_text(encoding="utf-8"))



def test_the_country_registry_agrees_with_the_published_panel():
    """
    Cross-source agreement rather than a typed number.

    `assert len(COUNTRIES) == 54` pinned a count. Adding a country meant editing
    the test to match the code, which is not a check — it is a second place to
    write the same number. Comparing the registry against the panel the pipeline
    actually published cannot be satisfied that way: a country added to one and
    not the other fails, whichever direction the mistake ran.
    """
    published = set(_bundle()["countries"])
    assert set(COUNTRIES) == published, (
        f"registry-only: {sorted(set(COUNTRIES) - published)}; "
        f"panel-only: {sorted(published - set(COUNTRIES))}")


def test_the_au_total_is_the_included_plus_the_excluded():
    """
    The one count worth stating, derived from both halves.

    54 is not a fact about the African Union — 55 is. 54 is what remains after
    the documented exclusion, and writing 54 anywhere hides the subtraction that
    produced it. `EXCLUDED_AU_MEMBERS` carries the reason alongside the name.
    """
    from asi.dashboard.app import EXCLUDED_AU_MEMBERS

    assert EXCLUDED_AU_MEMBERS, "the exclusion list must say what is left out, and why"
    for name, reason in EXCLUDED_AU_MEMBERS.items():
        assert reason and len(reason) > 20, f"{name}: excluded without a stated reason"
    assert len(COUNTRIES) + len(EXCLUDED_AU_MEMBERS) == 55


def test_every_country_has_required_fields():
    for iso3, meta in COUNTRIES.items():
        assert len(iso3) == 3 and iso3.isupper(), f"bad ISO3 key: {iso3!r}"
        assert meta.get("name"), f"{iso3} missing name"
        assert meta.get("region"), f"{iso3} missing region"
        assert isinstance(meta.get("rec"), list), f"{iso3} rec must be a list"


def test_regions_match_active_profile():
    """Region values must be drawn from the profile's declared subregions."""
    found = {m["region"] for m in COUNTRIES.values()}
    declared = set(ACTIVE_PROFILE.subregions)
    assert found <= declared, f"undeclared regions in registry: {sorted(found - declared)}"


def test_rec_membership_is_known():
    """Every REC code must be one the profile recognises."""
    found = {r for m in COUNTRIES.values() for r in m["rec"]}
    declared = set(ACTIVE_PROFILE.communities)
    assert found <= declared, f"unknown REC codes: {sorted(found - declared)}"


def test_island_states_exist_in_registry():
    missing = ACTIVE_PROFILE.island_states - set(COUNTRIES)
    assert not missing, f"island states not in country registry: {sorted(missing)}"


# ── Weights ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("preset_name", sorted(WEIGHT_PRESETS))
def test_weight_presets_sum_to_one(preset_name):
    total = sum(WEIGHT_PRESETS[preset_name].values())
    assert abs(total - 1.0) < 1e-9, f"preset {preset_name!r} sums to {total}"


@pytest.mark.parametrize("preset_name", sorted(WEIGHT_PRESETS))
def test_weight_presets_cover_every_pillar(preset_name):
    assert set(WEIGHT_PRESETS[preset_name]) == set(PILLAR_DEFS)


def test_active_preset_exists():
    assert ACTIVE_PRESET in WEIGHT_PRESETS


def test_weight_bounds_are_feasible():
    """
    The BoD LP needs sum(w)=1 to be reachable inside [WEIGHT_MIN, WEIGHT_MAX].
    With 7 pillars this requires 7*MIN <= 1 <= 7*MAX.
    """
    n = len(PILLAR_DEFS)
    assert n * WEIGHT_MIN <= 1.0 <= n * WEIGHT_MAX


# ── Pillar registry ────────────────────────────────────────────────────────────

def test_pillar_registry_matches_pillar_defs():
    """PillarRegistry must derive from PILLAR_DEFS, not keep a second copy."""
    pr = PillarRegistry()
    assert pr.valid_keys() == set(PILLAR_DEFS)
    for key, name in PILLAR_DEFS.items():
        assert pr.get_pillar(key)["name"] == name


def test_pillar_registry_carries_weight_bounds():
    pr = PillarRegistry()
    for key, meta in pr.list_pillars().items():
        assert "weight_min" in meta and "weight_max" in meta, f"pillar {key} missing bounds"


# ── Indicator registry ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def registry():
    return IndicatorRegistry(PillarRegistry())


def test_registry_validates(registry):
    assert registry.validate_all() is True


def test_registry_loads_indicators(registry):
    inds = registry.build_indicators()
    scoring = [i for i in inds.values() if i.role == "scoring"]
    descriptive = [i for i in inds.values() if i.role == "descriptive"]
    # Counts are asserted against the published panel, not against numbers typed
    # here. Adding an indicator should make one edit — the registry — and every
    # derived figure should follow; a pinned count turns that into two edits and
    # quietly passes if only the test is updated.
    published = _bundle()["indicators"]
    assert {i.variable_name for i in scoring} == {
        v for v, m in published.items() if m.get("role") == "scoring"}
    assert {i.variable_name for i in descriptive} == {
        v for v, m in published.items() if m.get("role") == "descriptive"}
    assert scoring, "an index with no scoring indicators is not an index"
    assert len(inds) == len(scoring) + len(descriptive), "an indicator has no role"


def test_every_indicator_has_database_and_log_flag(registry):
    for ind in registry.list_indicators():
        assert "database" in ind, f"{ind['variable_name']} missing 'database'"
        assert "log_transform" in ind, f"{ind['variable_name']} missing 'log_transform'"


def test_indicator_pillars_are_valid(registry):
    valid = set(PILLAR_DEFS)
    for ind in registry.list_indicators():
        if ind.get("role", "scoring") != "scoring":
            continue
        bad = set(ind.get("pillars", [])) - valid
        assert not bad, f"{ind['variable_name']} references unknown pillars {sorted(bad)}"


def test_every_pillar_has_at_least_two_scoring_indicators(registry):
    """A one-indicator pillar is not a construct; it is a single measure."""
    counts = {p: 0 for p in PILLAR_DEFS}
    for ind in registry.list_indicators():
        if ind.get("role", "scoring") != "scoring":
            continue
        for p in ind.get("pillars", []):
            if p in counts:
                counts[p] += 1
    thin = {p: n for p, n in counts.items() if n < 2}
    assert not thin, f"pillars with fewer than 2 scoring indicators: {thin}"
