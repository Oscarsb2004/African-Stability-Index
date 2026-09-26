"""Goal 3 (section S43) on synthetic fixtures: the new readers, the 3.1 steps, the checkpoints that separate our
arithmetic from revisions and the publisher's unpublished estimates, and a planted fault."""

import pytest

from athena.store import Store
from mdg import steps as mdg_steps
from mdg import testing
from mdg.goal3 import build_goal3
from mdg.readers import MdgSeriesReader, ParseError, UisApiReader, parse_annex_parts
from mdg.sources import SERIES, UIS_COUNTS
from mdg.validate_goal3 import validate_goal3


@pytest.fixture
def store(tmp_path) -> Store:
    return testing.fill(Store(tmp_path / "store"))


def run(store: Store):
    b = build_goal3(store)
    return b, validate_goal3(b, store)


def test_the_series_reader_keeps_nature_and_footnote():
    frame = MdgSeriesReader().parse(testing.series_html({"Alpha": 0.9}), SERIES[611])
    row = frame.table.to_pylist()[0]
    assert row == {"name": "Alpha", "year": 1991, "value": 0.9, "nature": "country data", "footnote": "1"}


def test_the_series_reader_refuses_a_row_that_does_not_fit_its_header():
    broken = testing.series_html({"Alpha": 0.9}).replace(b"<td>2000</td>", b"")
    with pytest.raises(ParseError, match="cells for"):
        MdgSeriesReader().parse(broken, SERIES[611])


def test_the_uis_reader_refuses_an_empty_answer():
    with pytest.raises(ParseError, match="no records"):
        UisApiReader().parse(b'{"hints": ["bad indicator"], "records": []}', UIS_COUNTS["a"])


def test_an_annex_table_in_parts_across_a_page_header():
    rows = parse_annex_parts("\n".join(testing.GOAL3_ANNEX_LINES), "3.1")
    assert {p for p, *_ in rows} == {"a", "b", "c"}
    assert ("c", "Landlocked developing countries", 2000, 0.75) in rows
    assert ("a", "World", 2015, None) in rows, "a dash is missing, never zero"


def test_a_zero_enrolment_gives_a_zero_ratio_and_no_male_enrolment_is_left_out():
    counts = {"AAA": (0, 100, 100, 100), "BBB": (10, 0, 50, 50)}
    frame = UisApiReader().parse(testing.uis_json(("20063", "40035", "SAP.1.F", "SAP.1.M"), counts), UIS_COUNTS["a"])
    table, _ = mdg_steps.UisCounts()({"records": frame}, {"year": 1991, "ef": "20063", "em": "40035",
                                                           "pf": "SAP.1.F", "pm": "SAP.1.M"})
    parity, _ = mdg_steps.ParityByCountry()({"counts": table}, {})
    assert {r["area"]: r["value"] for r in parity.table.to_pylist()} == {"AAA": 0.0}


def test_on_matching_data_every_goal3_checkpoint_passes(store):
    b, v = run(store)
    assert all(c.passed for c in v.comparisons.values()), [k for k, c in v.comparisons.items() if not c.passed]
    assert v.register.open() == () and v.quote_problems == []
    groups = {r["group"]: round(r["value"], 4) for r in b.frames["3.1a-1991-group"].table.to_pylist()}
    assert groups["world"] == 0.88 and groups["northern-africa"] == 0.9091 and groups["developing"] == 0.8667


def test_a_revised_country_value_fails_k1_only(tmp_path):
    revised = testing.series_html({**testing.PARITY, "Beta": 0.85})
    _, v = run(testing.fill(Store(tmp_path / "s"), **{"mdg-series-611": revised}))
    assert not v.comparisons["K1-a-1991"].passed and v.comparisons["K3-a-1991"].passed
    assert v.comparisons["K0f-a-1991"].passed
    assert v.windows["a-1991"] == (2,)


def test_wrong_weights_fail_k3_but_not_k0_or_k1(store, monkeypatch):
    monkeypatch.setattr(mdg_steps, "_parity", lambda ef, pf, em, pm: (ef / pm) / (em / pf) * 1.05)
    _, v = run(store)
    assert v.comparisons["K0f-a-1991"].passed and not v.comparisons["K3-a-1991"].passed


def test_every_divergence_carries_a_proposed_cause_but_stays_open(tmp_path):
    revised = testing.series_html({**testing.PARITY, "Beta": 0.85})
    _, v = run(testing.fill(Store(tmp_path / "s"), **{"mdg-series-611": revised}))
    opened = v.register.open()
    assert opened and all(d.cause is not None and d.explanation.startswith("Proposed") for d in opened)


def test_32_is_hosted_not_rebuilt(store):
    b, v = run(store)
    assert v.hosted_32["2013"] == {"world": 39.9, "developed": 47.8}
    assert not any(name.startswith("3.2") for name in b.frames)
