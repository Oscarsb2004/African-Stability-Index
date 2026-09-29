"""The MDG project on synthetic sources: the readers are strict, every check passes on matching data, and each
kind of fault fails the check that should catch it and no other."""

import ast
from pathlib import Path

import pytest

import fixtures
from mdg import readers
from mdg.build import MixedEditions, UnmappedNames, build
from mdg.check import check


def run(tmp_path, **overrides):
    project = fixtures.project(tmp_path, **overrides)
    built = build(project)
    return built, check(project, built)


def result(checked, indicator, check_name, year):
    board = checked.scoreboard
    return board[(board.indicator == indicator) & (board.check == check_name) & (board.year == year)].iloc[0]


# ── readers ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_an_annex_table_in_parts_across_a_page_header():
    rows = readers.annex_rows("\n".join(fixtures.ANNEX_LINES), "3.1")
    assert {p for p, *_ in rows} == {"a", "b", "c"}
    assert ("c", "Landlocked developing countries", 2000, 0.75) in rows
    assert ("a", "World", 2015, None) in rows, "a dash is no value, never zero"


def test_the_groupings_reader_refuses_an_unknown_heading():
    with pytest.raises(readers.ParseError, match="unknown heading"):
        readers.groupings(fixtures.groupings_doc().replace(b"Eastern Asia\r", b"Far East\r"))


def test_the_ldc_list_must_be_numbered_without_a_gap():
    with pytest.raises(readers.ParseError, match="1 to n"):
        readers.ldc_names(fixtures.pdf(["1 Alpha 1971 3 Gamma 1971"]))


def test_the_series_reader_refuses_a_row_that_does_not_fit_its_header():
    with pytest.raises(readers.ParseError, match="cells for"):
        readers.mdg_series(fixtures.series_html().replace(b"<td>2000</td>", b""))


def test_the_ipu_reader_drops_a_footnote_digit_from_a_name():
    assert ("Epsilon", 20, None, "?") in readers.ipu_classification(fixtures.ipu_html())


def test_a_wdi_response_on_more_than_one_page_is_refused():
    with pytest.raises(readers.ParseError, match="one page"):
        readers.wdi_archive(fixtures.wdi_json({"AAA": 1.0}).replace(b'"pages": 1', b'"pages": 2'))


# ── the whole catalogue ─────────────────────────────────────────────────────────────────────────────────────

def test_on_matching_data_every_check_passes(tmp_path):
    built, checked = run(tmp_path)
    board = checked.scoreboard
    assert (board.matched == board.compared).all() and (board.missing == 0).all(), board.to_string()
    assert set(board.indicator) == {"mdg-3.3", "mdg-3.1a", "mdg-3.1b", "mdg-3.1c"}
    assert checked.divergences.empty and checked.quote_problems == []
    assert result(checked, "mdg-3.3", "regions", 2015).compared == 7
    world = built.sums[("mdg-3.1a", 1991)].loc["world"]
    assert (world.countries, round(world.value, 4)) == (4, 0.88)


def test_a_revised_country_value_fails_the_country_check_only(tmp_path):
    _, checked = run(tmp_path, **{"series-611": fixtures.series_html(fixtures.PARITY | {"Beta": 0.85})})
    assert result(checked, "mdg-3.1a", "countries", 1991).matched == 3
    assert result(checked, "mdg-3.1a", "regions", 1991).matched == 7
    assert set(checked.divergences.key) == {"BBB"}


def test_wrong_weights_fail_the_regions_but_not_the_countries(tmp_path):
    project = fixtures.project(tmp_path)
    row = project.catalogue["indicator"][1]
    row["derive"] = {"ef": "ger_f", "pf": "100 + 0 * ger_f", "em": "ger_m", "pm": "100 + 0 * ger_m"}
    checked = check(project, build(project))
    assert result(checked, "mdg-3.1a", "countries", 1991).matched == 4
    assert result(checked, "mdg-3.1a", "regions", 1991).matched < 7


def test_the_2015_lists_replace_the_documents_lists(tmp_path):
    built, _ = run(tmp_path)
    members = built.members
    assert set(members[members.group == "least-developed"].member) == {"BBB", "CCC"}
    assert set(members[members.group == "landlocked-developing"].member) == {"DDD"}


def test_a_missing_seat_count_leaves_the_country_out(tmp_path):
    built, _ = run(tmp_path)
    assert "EEE" not in set(built.outputs.REF_AREA)
    assert "western-asia" not in set(built.outputs.REF_AREA)


def test_a_different_world_total_fails_the_totals_check(tmp_path):
    _, checked = run(tmp_path, **{"ipu-world-2015-02": fixtures.world_html(known=251)})
    assert result(checked, "mdg-3.3", "world totals", 2015).matched == 1


def test_inputs_from_two_editions_are_refused(tmp_path):
    project = fixtures.project(tmp_path)
    project.catalogue["indicator"][0]["inputs"]["seats"] = "wdi-2015-04/SE.PRM.ENRL"
    with pytest.raises(MixedEditions, match="P25"):
        build(project)


def test_a_name_no_table_matches_stops_the_run(tmp_path):
    with pytest.raises(UnmappedNames, match="Zeta"):
        run(tmp_path, **{"ipu-2015-02": fixtures.ipu_html(fixtures.SEATS + [("Zeta", 10, 1)])})


def test_a_quote_not_found_verbatim_is_reported(tmp_path):
    _, checked = run(tmp_path, **{"metadata-557": fixtures.html(["Something else entirely."])})
    assert len(checked.quote_problems) == 3


def test_a_run_with_a_changed_source_is_refused(tmp_path):
    fixtures.project(tmp_path).get("m49")
    changed = fixtures.project(tmp_path, m49=fixtures.m49_html(fixtures.CODES | {"Zeta": "ZZZ"}))
    with pytest.raises(Exception, match="the lock says"):
        build(changed)


# ── the seal ────────────────────────────────────────────────────────────────────────────────────────────────

def test_only_the_check_reads_the_answer_key():
    package = Path(readers.__file__).parent
    for path in package.glob("*.py"):
        if path.name in ("answers.py", "check.py"):
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imported = [a.name for a in node.names] + [getattr(node, "module", None) or ""]
                assert not any("answers" in name for name in imported), f"{path.name} imports the answer key"
