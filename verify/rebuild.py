"""
verify/rebuild.py — the committed outputs are exactly what the committed inputs and code produce.

Copies the project without its outputs to a scratch folder, runs 02_panel.py and 03_robustness.py there from
data/inputs.csv, and compares every file in data/panel/ with the committed one. A stale output, or one edited by
hand, fails here. It is also the proof that the ASI, reading its inputs from Athena's datasets, reproduces what it
has published.

Files must be identical byte for byte, line endings aside (git normalises them). One allowance: a machine with a
different maths library can differ in the last bit of a logarithm, so where the bytes differ, a CSV still passes if
every text cell is identical and every number agrees to a relative 1e-12. The report says which held.

Run:  python verify/rebuild.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
PANEL = Path("data") / "panel"
STAGES = ("02_panel.py", "03_robustness.py")
RELATIVE = 1e-12


def _bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def _numbers_agree(committed: Path, rebuilt: Path) -> bool:
    if committed.suffix != ".csv":
        return False
    a, b = pd.read_csv(committed, float_precision="round_trip"), pd.read_csv(rebuilt, float_precision="round_trip")
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        return False
    for column in a.columns:
        x, y = a[column], b[column]
        if pd.api.types.is_float_dtype(x) and pd.api.types.is_float_dtype(y):
            if not np.allclose(x, y, rtol=RELATIVE, atol=0.0, equal_nan=True):
                return False
        elif not x.astype(str).equals(y.astype(str)):
            return False
    return True


def run() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / "asi"
        shutil.copytree(REPO, copy, ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache"))
        shutil.rmtree(copy / PANEL)
        for stage in STAGES:
            done = subprocess.run([sys.executable, stage], cwd=copy, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
            if done.returncode:
                print(f"[FAIL] rebuild | {stage} exited with {done.returncode}")
                print(done.stdout[-1500:] + done.stderr[-1500:])
                return 1
        committed = sorted(p.name for p in (REPO / PANEL).iterdir())
        rebuilt = sorted(p.name for p in (copy / PANEL).iterdir())
        if committed != rebuilt:
            print(f"[FAIL] rebuild | outputs differ in name: committed {committed}, rebuilt {rebuilt}")
            failures += 1
        for name in sorted(set(committed) & set(rebuilt)):
            ours, theirs = REPO / PANEL / name, copy / PANEL / name
            if _bytes(ours) == _bytes(theirs):
                print(f"[PASS] rebuild | {name}: identical")
            elif _numbers_agree(ours, theirs):
                print(f"[PASS] rebuild | {name}: every number within {RELATIVE:g} relative, every text cell identical")
            else:
                print(f"[FAIL] rebuild | {name}: differs from what the inputs and code produce; rebuild and commit")
                failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
