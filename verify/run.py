"""
verify/run.py — single entry point for verification.

    python -m verify.run              # all layers
    python -m verify.run --layer replicate
    python -m verify.run --layer contract --layer advisory
    python -m verify.run --gate-only  # skip advisory (report-only layer)

Exit code 0 when no gating layer failed. `advisory` never affects the exit code:
it reports design judgement, not arithmetic, and blocking a release on a
judgement call trains people to ignore the gate.

Replaces the former root-level 00_evaluate.py and 00_audit.py, which duplicated
several checks and had no shared entry point. The legacy snapshot replicator was
retired in Phase C along with the chain it verified; verify/panel.py supersedes it.
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

LAYERS = {
    "panel":     ("verify/panel.py",     True,
                  "independent re-derivation of the time-series panel"),
    "contract":  ("verify/contract.py",  True,
                  "backend/frontend object contract"),
    "narrative": ("verify/narrative.py", True,
                  "narrative claims against the panel they describe"),
    "advisory":  ("verify/advisory.py",  False,
                  "design diagnostics (report only)"),
}


def run_layer(name: str) -> int:
    script, _, description = LAYERS[name]
    print()
    print("=" * 78)
    print(f"LAYER: {name} -- {description}")
    print("=" * 78)
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(REPO / script)],
        cwd=REPO,
    )
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="Run ASI verification layers.")
    ap.add_argument("--layer", action="append", choices=sorted(LAYERS),
                    help="run only these layers (repeatable); default is all")
    ap.add_argument("--gate-only", action="store_true",
                    help="run only layers that gate a release (skip advisory)")
    args = ap.parse_args()

    selected = args.layer or list(LAYERS)
    if args.gate_only:
        selected = [n for n in selected if LAYERS[n][1]]

    results: dict[str, int] = {}
    for name in selected:
        results[name] = run_layer(name)

    print()
    print("=" * 78)
    print("VERIFICATION SUMMARY")
    print("=" * 78)
    gating_failed = False
    for name, code in results.items():
        gates = LAYERS[name][1]
        if code == 0:
            status = "OK"
        elif gates:
            status = "FAILED"
            gating_failed = True
        else:
            status = "findings (report only)"
        print(f"  {name:<10} {status}")

    if gating_failed:
        print("\nA gating layer failed. Do not publish until it is resolved.")
    else:
        print("\nAll gating layers passed.")
    return 1 if gating_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
