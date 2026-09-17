"""
run_asi.py — one command to start the African Stability Index interface.

    python run_asi.py            ->  http://127.0.0.1:8050
    python run_asi.py --port 8060
    python run_asi.py --verify   ->  run the verification suite instead

There is nothing to activate first. If `.venv` does not exist this creates it,
installs `requirements-pipeline.txt` into it, and re-executes itself inside it;
if `.venv` is already current it starts immediately. Dependency install is
skipped unless the requirements files have changed since the last run, so the
steady-state cost of the check is one file read.

Production still runs `gunicorn app:server`, which imports the interface
directly and never touches this file.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
REQUIREMENTS = [ROOT / "requirements.txt", ROOT / "requirements-pipeline.txt"]

#: Set on the re-executed child so a failed bootstrap cannot recurse forever.
_GUARD = "ASI_BOOTSTRAPPED"


def venv_python() -> Path:
    """Interpreter inside .venv, per-platform."""
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def requirements_digest() -> str:
    """
    Fingerprint of the requirements files.

    Stored in the venv after a successful install. A mismatch is the signal to
    reinstall — that is what makes `pip install` conditional rather than a cost
    paid on every launch.
    """
    h = hashlib.sha256()
    for path in REQUIREMENTS:
        h.update(path.read_bytes() if path.exists() else b"")
    return h.hexdigest()


def bootstrap() -> Path:
    """Create and populate .venv as needed. Returns its interpreter."""
    python = venv_python()

    if not python.exists():
        print(f"Creating virtual environment in {VENV} ...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
        python = venv_python()

    stamp = VENV / ".asi-requirements"
    digest = requirements_digest()
    if not stamp.exists() or stamp.read_text(encoding="utf-8").strip() != digest:
        print("Installing dependencies (first run, or requirements changed) ...")
        subprocess.check_call(
            [str(python), "-m", "pip", "install", "--quiet", "--upgrade", "pip"]
        )
        subprocess.check_call(
            [str(python), "-m", "pip", "install", "-r",
             str(ROOT / "requirements-pipeline.txt")]
        )
        stamp.write_text(digest, encoding="utf-8")

    return python


def reexec(python: Path, argv: list[str]) -> int:
    """Re-run this script under the venv interpreter."""
    env = dict(os.environ, **{_GUARD: "1"})
    return subprocess.call([str(python), str(Path(__file__).resolve()), *argv], env=env)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="run_asi.py", description="Start the African Stability Index interface."
    )
    parser.add_argument("--port", type=int, help="Port to serve on (default 8050).")
    parser.add_argument("--host", help="Host to bind (default 127.0.0.1).")
    parser.add_argument("--debug", action="store_true",
                        help="Dash debug mode. Loopback only.")
    parser.add_argument("--verify", action="store_true",
                        help="Run the verification suite instead of serving.")
    parser.add_argument("--test", action="store_true",
                        help="Run the test suite instead of serving.")
    parser.add_argument("--no-bootstrap", action="store_true",
                        help="Use the current interpreter; skip the .venv check.")
    # Unrecognised flags are forwarded to whatever --verify or --test delegates
    # to, so `--verify --gate-only` reaches verify.run rather than being rejected
    # here.
    args, passthrough = parser.parse_known_args()

    # The interface reads these from the environment, so translate flags before
    # anything imports it.
    if args.port:
        os.environ["PORT"] = str(args.port)
    if args.host:
        os.environ["HOST"] = args.host
    if args.debug:
        os.environ["DEBUG"] = "true"

    already_bootstrapped = os.environ.get(_GUARD) == "1"
    running_in_venv = Path(sys.prefix).resolve() == VENV.resolve()

    if not (args.no_bootstrap or already_bootstrapped or running_in_venv):
        try:
            python = bootstrap()
        except subprocess.CalledProcessError as exc:
            print(f"Environment setup failed ({exc}).")
            return 1
        return reexec(python, sys.argv[1:])

    # Both delegate as subprocesses rather than by import: verify.run and pytest
    # each parse sys.argv themselves, and would reject this script's own flags.
    if args.verify:
        return subprocess.call([sys.executable, "-m", "verify.run", *passthrough],
                               cwd=str(ROOT))

    if args.test:
        return subprocess.call([sys.executable, "-m", "pytest", "-q",
                                str(ROOT / "tests"), *passthrough])

    from asi.dashboard.app import main as serve
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
