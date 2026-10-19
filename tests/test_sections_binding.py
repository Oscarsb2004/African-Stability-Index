"""04_sections.py and sections.toml: the ASI's binding resolves against athena-core's templates, and the committed
data/sections.json meets the output contract. Neither needs Athena's store."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sections_stage", ROOT / "04_sections.py")
sections_stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sections_stage)  # puts athena-core on the path

from athena import sections  # noqa: E402
from asi.core.countries import COUNTRIES  # noqa: E402

NAMES = ["wdi-2026-10-08", "wgi-2026-09-25"]


def test_every_template_measure_is_bound_or_explained():
    b = sections.binding(ROOT / "sections.toml")
    templates, used = sections.resolve(b, NAMES)
    assert [t["id"] for t in templates] == b["sections"]
    assert used == {"wdi": "wdi-2026-10-08", "wgi": "wgi-2026-09-25"}
    # negative control: drop one bound measure and the binding no longer resolves
    broken = copy.deepcopy(b)
    del broken["measures"]["inflation"]
    with pytest.raises(sections.SectionError, match="inflation"):
        sections.resolve(broken, NAMES)


def test_the_committed_document_meets_the_contract_for_every_member_state():
    doc = json.loads((ROOT / "data" / "sections.json").read_text(encoding="utf-8"))
    sections.check(doc)
    assert sorted(doc["areas"]) == sorted(COUNTRIES)
    assert doc["names"]["NGA"] == "Nigeria"
    # negative control: a damaged copy fails
    del doc["areas"]["NGA"]["prices"]
    with pytest.raises(sections.SectionError):
        sections.check(doc)
