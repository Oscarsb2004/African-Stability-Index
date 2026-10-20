"""08_narratives.py and verify/narrative.py (edition 2, step 10) on a synthetic panel: the facts follow their
rules, the sentences say only what is true of the facts, and the verifier catches a number that is not a fact."""

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("narratives_stage", ROOT / "08_narratives.py")
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


def panel():
    """Three states at 2024 and 2014, three pillars; CCC's ENV is unreliable at 2024."""
    comp, pil = [], []
    scores = {"AAA": {"GOV": 80.0, "SEC": 70.0, "ENV": 60.0}, "BBB": {"GOV": 50.0, "SEC": 50.0, "ENV": 50.0},
              "CCC": {"GOV": 20.0, "SEC": 30.0, "ENV": 90.0}}
    for year, shift in ((2024, 0.0), (2014, -5.0)):
        for rank, (iso3, pillars) in enumerate(scores.items(), 1):
            for p, s in pillars.items():
                tier = "unreliable" if (iso3, p, year) == ("CCC", "ENV", 2024) else "reliable"
                pil.append({"iso3": iso3, "year": year, "pillar_id": p, "score": s + shift, "reliability": tier})
            comp.append({"iso3": iso3, "year": year, "method": "equal", "score": 70.0 - 20 * rank + shift,
                         "rank": rank, "ci_low": 1.0, "ci_high": 2.0, "tier": rank, "band_best": rank,
                         "band_worst": rank, "n_pillars": 2 if iso3 == "CCC" else 3, "lack_of_reliability": 1.0})
    return pd.DataFrame(comp), pd.DataFrame(pil)


def test_pillars_above_and_below_the_median_are_only_those_on_that_side():
    comp, pil = panel()
    f = stage.facts(comp, pil, 2024)
    assert [p for p, *_ in f["AAA"]["above"]] == ["GOV", "SEC"] and f["AAA"]["below"] == []
    assert [p for p, *_ in f["CCC"]["below"]] == ["GOV", "SEC"]
    assert f["CCC"]["left_out"] == ["ENV"] and f["CCC"]["above"] == []  # ENV did not enter, so it is not compared
    assert f["BBB"]["above"] == [] and [p for p, *_ in f["BBB"]["below"]] == ["ENV"]  # at the median: not above


def test_the_change_runs_over_ten_years_and_names_the_pillar_that_moved_most():
    comp, pil = panel()
    change = stage.facts(comp, pil, 2024)["AAA"]["change"]
    assert (change["from_year"], change["from"], change["pillar_from"], change["pillar_to"]) == (2014, 45.0, 75.0, 80.0)


def test_the_sentences_say_none_when_no_pillar_is_on_a_side():
    comp, pil = panel()
    f = stage.facts(comp, pil, 2024)
    assert "None of its pillars is above the median state." in " ".join(stage.sentences("Bbb", f["BBB"], 2024, 3, 3,
                                                                                         1.0))
    assert "None is below it." in " ".join(stage.sentences("Aaa", f["AAA"], 2024, 3, 3, 1.0))
    ccc = " ".join(stage.sentences("Ccc", f["CCC"], 2024, 3, 3, 1.0))
    assert "Environment and Climate Exposure was left out" in ccc


def test_the_verifier_finds_every_number_and_refuses_one_that_is_not_a_fact():
    import sys
    sys.path.insert(0, str(ROOT))
    from verify import narrative as V
    comp, pil = panel()
    f = stage.facts(comp, pil, 2024)
    doc = {"year": 2024, "n_ranked": 3, "n_tiers": 3, "lri_median": 1.0}
    text = stage.sentences("Aaa", f["AAA"], 2024, 3, 3, 1.0)
    ok = V.allowed(f["AAA"], doc)
    assert all(n in ok for s in text for n in V.NUMBER.findall(s))
    assert V.same(V.expected(comp, pil, 2024)["AAA"], f["AAA"])  # the verifier's own route agrees
    forged = text[0].replace("50.0", "51.0")                      # negative control: a number edited by hand
    assert any(n not in ok for n in V.NUMBER.findall(forged))
