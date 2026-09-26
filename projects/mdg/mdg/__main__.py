"""Command line for phase 1.

    python -m mdg fetch    retrieve every recipe into the store (network)
    python -m mdg run      build, validate and write the report (no network)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from athena.ids import canonical_json, hash_bytes
from athena.runs import RunRecord
from athena.sources import Snapshot
from athena.store import DEFAULT_ROOT, Store
from athena.transport import HttpTransport
from mdg.pipeline import build
from mdg.readers import READERS
from mdg.sources import RECIPES, SOURCES
from mdg.validate import validate
from mdg.view import render


def fetch(store: Store) -> None:
    transport = HttpTransport()
    for recipe in RECIPES:
        source = SOURCES[recipe.source]
        if not source.usable:
            raise SystemExit(f"{source.id}: terms not read and dated (std:DATA-04)")
        data, url, media_type = READERS[recipe.reader]().fetch(recipe, transport)
        snapshot = store.put(data, Snapshot.of(data, source=source, recipe=recipe, url=url, media_type=media_type,
                                               retrieved_at=datetime.now(timezone.utc)))
        print(f"{recipe.id}: {snapshot.hash} ({snapshot.size_bytes} bytes)")


def code_version() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run(store: Store) -> int:
    started = datetime.now(timezone.utc)
    b = build(store)
    v = validate(b, store)
    lock = Path(__file__).resolve().parents[3] / "requirements.lock"
    environment = hash_bytes(lock.read_bytes()) if lock.exists() else hash_bytes(b"")
    record = RunRecord(
        id=f"run:mdg-3-3-{started:%Y%m%dT%H%M%SZ}", project="project:index-catalogue", started_at=started,
        finished_at=datetime.now(timezone.utc), code_version=code_version(), environment=environment,
        parsed=b.parsed, steps=tuple(b.results), comparisons=tuple(v.comparisons.values()),
    )
    folder = store.root / "runs" / record.id.split(":", 1)[1]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "run.json").write_bytes(canonical_json(record.model_dump(mode="json")))
    (folder / "report.html").write_text(render(b, v, record.id), encoding="utf-8")
    store.log("run", id=record.id, passed=v.passed, report=str(folder / "report.html"),
              checkpoints={k: c.passed for k, c in v.comparisons.items()})
    for k, c in v.comparisons.items():
        print(f"{k}: compared {c.compared}, within {c.within}, missing {c.missing}, extra {c.extra}, "
              f"largest difference {c.max_abs_difference:.4f} -> {'pass' if c.passed else 'FAIL'}")
    print("quotes:", "all found" if not v.quote_problems else v.quote_problems)
    print("report:", folder / "report.html")
    return 0 if v.passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mdg")
    parser.add_argument("command", choices=("fetch", "run"))
    parser.add_argument("--store", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(argv)
    store = Store(args.store)
    if args.command == "fetch":
        fetch(store)
        return 0
    return run(store)


if __name__ == "__main__":
    sys.exit(main())
