"""Identity, immutability and the refusal of unknown fields: the base every definition stands on."""

from datetime import date

import pytest
from pydantic import ValidationError

from athena.ids import hash_bytes, kind_of
from athena.reference import Grouping
from athena.sources import SourceCard, Terms
from athena.vocab import Access

TERMS = Terms(url="https://example.org/terms", summary="Not yet read.")


def card(**changes):
    fields = dict(id="source:un-mdg-database", title="MDG database", publisher="UN", access=Access.BULK, terms=TERMS)
    return SourceCard(**(fields | changes))


def test_a_definition_takes_its_kind_from_its_class():
    assert card().ref == "source:un-mdg-database@0.1.0"


def test_a_definition_refuses_an_id_of_another_kind():
    with pytest.raises(ValidationError, match="ids start with source:"):
        card(id="recipe:un-mdg-database")


def test_malformed_ids_and_versions_are_refused():
    with pytest.raises(ValidationError):
        card(id="Source:UN MDG")
    with pytest.raises(ValidationError):
        card(version="1.0")
    with pytest.raises(ValueError):
        kind_of("no-colon")


def test_unknown_fields_are_refused():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        card(owner="someone")


def test_definitions_cannot_be_changed_after_construction():
    with pytest.raises(ValidationError):
        card().title = "changed"


def test_fingerprints_are_stable_and_change_with_content():
    assert card().fingerprint() == card().fingerprint()
    assert card().fingerprint() != card(title="Another title").fingerprint()
    assert card().fingerprint().startswith("sha256:")


def test_hash_bytes_is_sha256():
    assert hash_bytes(b"") == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_a_disjoint_grouping_refuses_a_member_in_two_groups():
    with pytest.raises(ValidationError, match="is in both"):
        Grouping(id="grouping:g", title="g", publisher="p", disjoint=True, groups={"N": ("A",), "S": ("A",)})
    overlapping = Grouping(id="grouping:g", title="g", publisher="p", disjoint=False, groups={"N": ("A",), "S": ("A",)})
    assert overlapping.group_of("A") == ("N", "S")


def test_terms_cannot_be_judged_before_they_are_read():
    with pytest.raises(ValidationError, match="once the terms have been read"):
        Terms(url="https://example.org", summary="s", redistribution="allowed")
    read = Terms(url="https://example.org", summary="s", read_on=date(2026, 9, 25), redistribution="allowed")
    assert card(terms=read).publishable
    assert not card().usable
