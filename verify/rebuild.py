"""
verify/rebuild.py — the committed outputs are exactly what the committed inputs and code produce.

Copies the project without its outputs to a scratch folder, runs 02_panel.py and 03_robustness.py there from
data/inputs.csv, and compares every file in data/panel/ with the committed one. A stale output, or one edited by
hand, fails here. It is also the proof that the ASI, reading its inputs from Athena's datasets, reproduces what it
has published.

Files must be identical byte for byte, line endings aside (git normalises them). One allowance: a machine with a
different maths library can differ in the last bit of a logarithm or an eigenvector, so where the bytes differ, a
CSV, JSON or YAML file still passes if every text value is identical and every number agrees to a relative 1e-12.
The report says which held. (Measured on CI's Linux runner: the observations, the pillar scores and the bundle's
fitted weights differ from Windows only in the last bits.)

Run:  python verify/rebuild.py
"""

import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parent.parent
PANEL = Path("data") / "panel"
STAGES = ("02_panel.py", "03_robustness.py")
RELATIVE = 1e-12


def _bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def _close(x, y) -> bool:
    """Equal structures, with numbers allowed a relative RELATIVE apart."""
    if isinstance(x, bool) or isinstance(y, bool):
        return x == y
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        both_nan = isinstance(x, float) and isinstance(y, float) and math.isnan(x) and math.isnan(y)
        return both_nan or x == y or abs(x - y) <= RELATIVE * max(abs(x), abs(y))
    if isinstance(x, dict) and isinstance(y, dict):
        return x.keys() == y.keys() and all(_close(x[k], y[k]) for k in x)
    if isinstance(x, list) and isinstance(y, list):
        return len(x) == len(y) and all(map(_close, x, y))
    return x == y


def _numbers_agree(committed: Path, rebuilt: Path) -> bool:
    if committed.suffix in (".json", ".yaml"):
        read = json.loads if committed.suffix == ".json" else yaml.safe_load
        return _close(read(committed.read_text(encoding="utf-8")), read(rebuilt.read_text(encoding="utf-8")))
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
                print(f"[PASS] rebuild | {name}: every number within {RELATIVE:g} relative, every text value identical")
            else:
                print(f"[FAIL] rebuild | {name}: differs from what the inputs and code produce; rebuild and commit")
                failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
