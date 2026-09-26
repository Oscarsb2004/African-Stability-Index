"""A frame's table and manifest must agree, and the manifest must fit its profile."""

import pyarrow as pa
import pytest
from pydantic import ValidationError

from athena.frames import Column, Frame, Manifest
from athena.vocab import DType, Origin, Profile, ReproClass, Role, ValidationLevel

from conftest import VALUES, panel

ENTITY = Column(name="area", dtype=DType.STRING, role=Role.ENTITY)
TIME = Column(name="year", dtype=DType.INT64, role=Role.TIME)
MEASURE = Column(name="value", dtype=DType.FLOAT64, role=Role.MEASURE, unit="percent")


def manifest(**changes):
    fields = dict(profile=Profile.PANEL, columns=(ENTITY, TIME, MEASURE), keys=("area", "year"),
                  produced_by="shell:x@0.1.0", repro_class=ReproClass.A)
    return Manifest(**(fields | changes))


def test_a_measure_declares_its_unit():
    with pytest.raises(ValidationError, match="must declare a unit"):
        Column(name="value", dtype=DType.FLOAT64, role=Role.MEASURE)


def test_a_profile_refuses_a_manifest_missing_a_required_role():
    with pytest.raises(ValidationError, match="needs roles"):
        manifest(columns=(ENTITY, MEASURE), keys=("area",))


def test_keys_must_be_declared_columns():
    with pytest.raises(ValidationError, match="keys must be"):
        manifest(keys=("area", "month"))
    with pytest.raises(ValidationError, match="keys must be"):
        manifest(keys=())


def test_a_cross_section_declares_its_period():
    with pytest.raises(ValidationError, match="declares the period"):
        manifest(profile=Profile.CROSS_SECTION, columns=(ENTITY, MEASURE), keys=("area",))
    assert manifest(profile=Profile.CROSS_SECTION, columns=(ENTITY, MEASURE), keys=("area",), period="2015")


def test_own_method_output_cannot_claim_a_publisher_match():
    with pytest.raises(ValidationError, match="cannot be validation level 1"):
        manifest(origin=Origin.OWN, validation_level=ValidationLevel.PUBLISHER_MATCH)
    assert manifest(origin=Origin.OWN, validation_level=ValidationLevel.INTERNAL_ONLY).derived


def test_a_table_that_does_not_match_its_manifest_is_refused():
    table = pa.table({"area": ["AAA"], "year": pa.array([2015], pa.int32()), "value": [1.0]})
    with pytest.raises(ValueError, match="does not match the manifest"):
        Frame(table, manifest())


def test_duplicate_keys_are_refused():
    with pytest.raises(ValueError, match="duplicate keys"):
        panel([("AAA", 2015, 1.0), ("AAA", 2015, 2.0)])


def test_missing_key_values_are_refused():
    table = pa.table({"area": pa.array(["AAA", None]), "year": pa.array([2015, 2015], pa.int64()),
                      "value": [1.0, 2.0]})
    with pytest.raises(ValueError, match="has missing values"):
        Frame(table, manifest())


def test_missing_measure_values_are_kept_as_missing_not_zero():
    frame = panel([("AAA", 2015, 1.0), ("BBB", 2015, None)])
    assert frame.column("value").null_count == 1


def test_the_content_hash_is_stable_and_sees_every_value():
    assert panel(VALUES).content_hash() == panel(VALUES).content_hash()
    changed = [VALUES[0], VALUES[1], ("CCC", 2015, 50.000001)]
    assert panel(changed).content_hash() != panel(VALUES).content_hash()


def test_the_content_hash_sees_the_manifest():
    assert panel(VALUES, unit="persons").content_hash() != panel(VALUES).content_hash()


def test_sorting_by_keys_keeps_the_hash_meaningful():
    shuffled = panel([VALUES[2], VALUES[0], VALUES[1]])
    assert shuffled.sorted_by_keys().content_hash() == panel(VALUES).content_hash()
