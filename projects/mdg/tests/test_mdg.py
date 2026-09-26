"""Phase 1 (section S42) on synthetic fixtures: every reader, the mapping, the whole loop, a planted fault before each
checkpoint, and the answer-key isolation rule."""

import ast
from pathlib import Path

import pytest

import mdg
from athena.store import Store
from mdg import steps as mdg_steps
from mdg import testing
from mdg.codes import UnmappedNames, code_map, load_aliases
from mdg.method import CARD, verify_quotes
from mdg.pipeline import build
from mdg.readers import (AnnexTableReader, GroupingsDocReader, IpuClassificationReader, IpuWorldReader, M49Reader,
                         ParseError, parse_annex_text)
from mdg.sources import ANNEX, GROUPINGS, IPU_CLASSIFICATION, IPU_WORLD, M49_OVERVIEW
from mdg.validate import validate

PIPELINE_MODULES = ("sources", "readers", "codes", "steps", "method", "pipeline", "goal3")


@pytest.fixture
def store(tmp_path) -> Store:
    return testing.fill(Store(tmp_path / "store"))


def run(store: Store):
    b = build(store)
    return b, validate(b, store)


# ── Readers ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_ipu_reader_keeps_counts_strips_footnote_markers_and_leaves_unknowns_missing():
    frame = IpuClassificationReader().parse(testing.ipu_html(), IPU_CLASSIFICATION)
    rows = {r["name"]: r for r in frame.table.to_pylist()}
    assert set(rows) == {"Alpha", "Beta", "Gamma", "Delta", "Epsilon"}
    assert rows["Epsilon"]["women"] is None and rows["Epsilon"]["seats"] == 20
    assert "value" not in frame.table.column_names, "the printed percentage belongs to the answer key"


def test_the_ipu_reader_refuses_a_page_without_country_rows():
    with pytest.raises(ParseError, match="no country rows"):
        IpuClassificationReader().parse(b"<html><table></table></html>", IPU_CLASSIFICATION)


def test_the_world_reader_reads_the_block_by_its_label():
    assert IpuWorldReader().parse(testing.world_html(), IPU_WORLD) == {
        "total": 270, "known": 250, "women": 66, "percent": 26.4}
    with pytest.raises(ParseError, match="no block labelled"):
        IpuWorldReader().parse(b"<html></html>", IPU_WORLD)


def test_the_groupings_reader_derives_developing_world_and_the_excluding_rows():
    frame = GroupingsDocReader().parse(testing.groupings_doc(), GROUPINGS)
    rows = {(r["member"], r["group"], r["level"]) for r in frame.table.to_pylist()}
    assert ("Beta", "northern-africa", "region") in rows
    assert ("Beta", "developing", "development") in rows and ("Alpha", "developed", "development") in rows
    assert {m for m, g, _ in rows if g == "world"} == {"Alpha", "Beta", "Gamma", "Delta", "Epsilon"}
    assert ("Delta", "eastern-asia-excluding-china", "alternate") in rows
    assert ("Gamma", "least-developed", "special") in rows


def test_the_groupings_reader_refuses_an_unknown_heading():
    doc = testing.groupings_doc().replace(b"Eastern Asia\r", b"Far Eastern Asia\r")
    with pytest.raises(ParseError, match="unknown heading"):
        GroupingsDocReader().parse(doc, GROUPINGS)


def test_the_annex_reader_treats_a_dash_as_missing_and_refuses_an_unrecognised_row():
    rows = AnnexTableReader().parse(testing.annex_pdf(), ANNEX)
    assert ("Western Asia", 2015, None) in rows and ("World", 2015, 26.4) in rows
    with pytest.raises(ParseError, match="unrecognised row"):
        parse_annex_text("Indicator 3.3\n2014 2015\nWorld 26.0\n", "3.3")


def test_the_m49_reader_needs_a_full_table():
    assert M49Reader().parse(testing.m49_html(), M49_OVERVIEW)["Alpha"] == "AAA"
    with pytest.raises(ParseError, match="only"):
        M49Reader().parse(b'<table id = "downloadTableEN"><tr><td>Country or Area</td><td>ISO-alpha3 Code</td>'
                          b"</tr><tr><td>X</td><td>XXX</td></tr></table>", M49_OVERVIEW)


# ── Codes ────────────────────────────────────────────────────────────────────────────────────────────────────

def test_an_unmatched_name_stops_the_run():
    with pytest.raises(UnmappedNames, match="Atlantis"):
        code_map(["Alpha", "Atlantis"], {"Alpha": "AAA"}, {})


def test_an_alias_may_not_hide_an_exact_match():
    with pytest.raises(UnmappedNames, match="already matches"):
        code_map(["Alpha"], {"Alpha": "AAA"}, {"Alpha": "ZZZ"})


def test_the_real_alias_table_loads_and_maps_to_codes():
    aliases = load_aliases()
    assert aliases["Nauru"] == "NRU" and all(v for v in aliases.values())


# ── The loop ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_correct_build_passes_every_checkpoint(store):
    b, v = run(store)
    assert v.passed, v.comparisons
    regional = {r["group"]: r["value"] for r in b.frames["group-percent-rounded"].table.to_pylist()}
    assert regional["world"] == 26.4 and regional["northern-africa"] == 33.3
    assert "western-asia" not in regional, "a group with no known counts is absent, not zero"
    assert v.window == () and v.register.open() == ()


def test_the_same_snapshots_give_the_same_hashes(store):
    first, second = build(store), build(store)
    assert [r.output for r in first.results] == [r.output for r in second.results]


def test_a_fault_before_k1_is_caught_at_k1(store, monkeypatch):
    run_ratio = mdg_steps.RatioByCountry.run

    def faulty(self, inputs, params):
        frame = run_ratio(self, inputs, params)
        import pyarrow as pa
        values = [v * 0.9 for v in frame.column("value").to_pylist()]
        return type(frame)(frame.table.set_column(1, "value", pa.array(values)), frame.manifest)

    monkeypatch.setattr(mdg_steps.RatioByCountry, "run", faulty)
    _, v = run(store)
    assert not v.comparisons["K1"].passed and v.comparisons["K3"].passed
    assert v.window == (1,)


def test_a_wrong_region_is_caught_at_k3_and_blamed_on_steps_2_and_3(tmp_path):
    doc = testing.groupings_doc().replace(b"Beta\x07Gamma\x07\x07", b"Beta\x07\x07").replace(
        b"Delta\x07\x07", b"Delta\x07Gamma\x07\x07")
    _, v = run(testing.fill(Store(tmp_path / "s"), **{"mdg-regional-groupings-doc": doc}))
    assert v.comparisons["K1"].passed and v.comparisons["K2"].passed
    assert not v.comparisons["K3"].passed
    assert v.window == (2, 3) and [d.checkpoint for d in v.register.open()] == ["K3", "K3r"]


def test_imputing_a_missing_count_as_zero_is_caught_at_k2(store, monkeypatch):
    monkeypatch.setattr(mdg_steps, "_known", lambda rows, p: [
        r | {p.numerator: r[p.numerator] or 0} for r in rows if r[p.denominator]])
    _, v = run(store)
    assert not v.comparisons["K2"].passed


def test_a_wrong_rounding_rule_is_caught_only_after_rounding(store, monkeypatch):
    from athena.rounding import Rounding
    monkeypatch.setattr("mdg.pipeline.CARD", CARD.model_copy(update={"rounding": Rounding(decimals=0)}))
    _, v = run(store)
    assert v.comparisons["K3"].passed and not v.comparisons["K3r"].passed


def test_every_quote_on_the_card_is_checked(store):
    b, v = run(store)
    assert v.quote_problems == []
    assert verify_quotes(CARD, {"MDG metadata": "unrelated text"})


# ── Answer-key isolation ─────────────────────────────────────────────────────────────────────────────────────

def imports_answers(source: str) -> bool:
    for node in ast.walk(ast.parse(source)):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""] + [f"{node.module}.{a.name}" for a in node.names]
        if any(n in ("mdg.answers", "mdg.validate") or n.endswith(".answers") for n in names):
            return True
    return False


def test_no_pipeline_module_can_see_the_answer_key():
    folder = Path(mdg.__file__).parent
    leaks = [m for m in PIPELINE_MODULES if imports_answers((folder / f"{m}.py").read_text(encoding="utf-8"))]
    assert leaks == []


def test_the_isolation_scan_catches_a_planted_read():
    assert imports_answers("from mdg import answers\n")
    assert imports_answers("import mdg.answers as a\n")
    assert imports_answers("from mdg.answers import regional\n")
    assert not imports_answers("from mdg import readers\n")


# ── The owner's ruling on least developed and landlocked lists (2026-09-26) ─────────────────────────────────

def test_the_dated_ldc_list_is_numbered_without_gaps_and_drops_footnote_digits():
    from mdg.readers import LdcListReader
    assert LdcListReader().names(testing.ldc_pdf(("Gamma", "Beta"))) == ["Gamma", "Beta"]
    gap = testing.pdf(["LIST", "1 Gamma 1971 3 Beta 1975"])
    with pytest.raises(ParseError, match="not numbered 1 to n"):
        LdcListReader().names(gap)


def test_the_lldc_reader_checks_each_region_count():
    from mdg.readers import LldcProfilesReader
    assert LldcProfilesReader().names(testing.lldc_html()) == ["Delta"]
    wrong = testing.lldc_html().replace(b"Asia (1)", b"Asia (2)")
    with pytest.raises(ParseError, match="region counts"):
        LldcProfilesReader().names(wrong)


def test_the_dated_lists_replace_the_documents_lists_whole(store):
    b, v = run(store)
    groups = {(r["member"], r["group"]) for r in b.frames["groups"].table.to_pylist()}
    assert {m for m, g in groups if g == "least-developed"} == {"BBB", "CCC"}
    assert {m for m, g in groups if g == "landlocked-developing"} == {"DDD"}, "Epsilon, the document's entry, is gone"
    assert v.passed, v.comparisons


def test_the_readings_record_the_owner_ruling():
    assert CARD.unruled_readings == ()
    assert all("2015" in r.adopted for r in CARD.readings)


def test_without_the_replacement_the_least_developed_row_diverges(store, monkeypatch):
    monkeypatch.setattr(mdg_steps.ReplaceGroups, "run",
                        lambda self, inputs, params: type(inputs["groups"])(
                            inputs["groups"].table, inputs["groups"].manifest.model_copy(
                                update={"produced_by": self.ref()})))
    monkeypatch.setattr(mdg_steps.ReplaceGroups, "invariants", lambda self: ())
    _, v = run(store)
    assert not v.comparisons["K3"].passed
    wrong = {m.key["group"] for m in v.comparisons["K3"].mismatches if m.side != "extra"}
    assert wrong == {"least-developed", "landlocked-developing"}
