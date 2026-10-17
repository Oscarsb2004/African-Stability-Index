"""verify/rebuild.py's comparison: identical bytes, or numbers that differ only in their last bits.

A different maths library may move the last bit of a logarithm or an eigenvector, and that must pass. Anything
larger must fail, and so must any change to text.
"""

import pandas as pd

from verify.rebuild import _close, _numbers_agree


def test_numbers_may_differ_only_in_their_last_bits():
    assert _close({"w": [0.15812522838559329, 1.0]}, {"w": [0.15812522838559329 * (1 + 3e-16), 1.0]})
    assert not _close({"w": [0.158125]}, {"w": [0.158125 * (1 + 1e-9)]})


def test_text_and_structure_must_match_exactly():
    assert not _close({"note": "A–E"}, {"note": "A-E"})
    assert not _close({"a": 1}, {"a": 1, "b": 2})
    assert not _close([1, 2], [1, 2, 3])
    assert _close({"x": float("nan")}, {"x": float("nan")})


def test_a_csv_passes_on_last_bits_and_fails_on_text(tmp_path):
    committed, rebuilt, renamed = tmp_path / "a.csv", tmp_path / "b.csv", tmp_path / "c.csv"
    pd.DataFrame({"iso3": ["AGO"], "score": [34.26368556914676]}).to_csv(committed, index=False)
    pd.DataFrame({"iso3": ["AGO"], "score": [34.26368556914676 * (1 + 2e-16)]}).to_csv(rebuilt, index=False)
    pd.DataFrame({"iso3": ["BEN"], "score": [34.26368556914676]}).to_csv(renamed, index=False)
    assert _numbers_agree(committed, rebuilt)
    assert not _numbers_agree(committed, renamed)
