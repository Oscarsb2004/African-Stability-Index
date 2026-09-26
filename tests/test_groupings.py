"""Decision P19: a grouping is a small versioned definition pointing, by hash, at a membership frame."""

from datetime import date

import pytest
from pydantic import ValidationError

from athena.reference import Grouping, membership_frame

from conftest import REGIONS, regions

NESTED = [("AAA", "North", "region"), ("BBB", "North", "region"), ("CCC", "South", "region"),
          ("North", "World", "world"), ("South", "World", "world")]
OVERLAPPING = [("AAA", "Landlocked", "list"), ("AAA", "Least developed", "list"), ("BBB", "Least developed", "list")]


def grouping(frame, **changes):
    fields = dict(id="grouping:g", title="g", publisher="Test", levels=("region", "world"), disjoint=True,
                  members=frame.content_hash())
    return Grouping(**(fields | changes))


def test_a_grouping_binds_only_the_membership_it_names():
    bound = REGIONS.bind(regions())
    assert bound.groups("region") == {"North": ("AAA", "BBB"), "South": ("CCC",)}
    with pytest.raises(ValueError, match="names membership"):
        REGIONS.bind(regions([("AAA", "North", "region")]))


def test_levels_nest_and_each_level_is_read_on_its_own():
    frame = membership_frame(NESTED, produced_by="shell:test-input@0.1.0")
    bound = grouping(frame).bind(frame)
    assert bound.group_of("AAA", "region") == ("North",)
    assert bound.groups("world") == {"World": ("North", "South")}
    with pytest.raises(KeyError, match="no level"):
        bound.groups("continent")


def test_a_disjoint_grouping_refuses_a_member_in_two_groups_at_one_level():
    frame = membership_frame(OVERLAPPING, produced_by="shell:test-input@0.1.0")
    with pytest.raises(ValueError, match="is in both"):
        grouping(frame, levels=("list",)).bind(frame)
    bound = grouping(frame, levels=("list",), disjoint=False).bind(frame)
    assert bound.group_of("AAA", "list") == ("Landlocked", "Least developed")


def test_a_row_at_an_undeclared_level_is_refused():
    frame = membership_frame(NESTED, produced_by="shell:test-input@0.1.0")
    with pytest.raises(ValueError, match="is not one of"):
        grouping(frame, levels=("region",)).bind(frame)


def test_a_grouping_declares_its_levels_and_a_sane_validity_period():
    frame = regions()
    with pytest.raises(ValidationError, match="names its levels"):
        grouping(frame, levels=())
    with pytest.raises(ValidationError, match="before it starts"):
        grouping(frame, valid_from=date(2015, 1, 1), valid_to=date(2010, 1, 1))


def test_a_membership_frame_refuses_a_repeated_row():
    with pytest.raises(ValueError, match="duplicate keys"):
        membership_frame([("AAA", "North", "region")] * 2, produced_by="shell:test-input@0.1.0")
