"""The store: bytes kept exactly as published, named by their hash, and a log of everything that happened.

Snapshots are written once and never overwritten or deleted (decisions ST1 and ST4). Every read re-checks the
hash, so a changed file on disk is caught the moment it is used. The catalogue is an append-only list of events,
one JSON object per line.

This is the minimal store section S42 needs. Section S49 adds backup and a verify-everything command.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from athena.ids import hash_bytes
from athena.sources import Snapshot

DEFAULT_ROOT = Path(os.environ.get("ATHENA_STORE", r"C:\AthenaStore"))


class StoreError(RuntimeError):
    pass


class Store:
    def __init__(self, root: Path = DEFAULT_ROOT):
        self.root = Path(root)
        self._catalogue = self.root / "catalogue" / "events.jsonl"

    def _path(self, content_hash: str) -> Path:
        digest = content_hash.removeprefix("sha256:")
        return self.root / "snapshots" / digest[:2] / digest

    def put(self, data: bytes, snapshot: Snapshot) -> Snapshot:
        if hash_bytes(data) != snapshot.hash:
            raise StoreError(f"snapshot {snapshot.hash} does not describe these bytes")
        path = self._path(snapshot.hash)
        if path.exists():
            if hash_bytes(path.read_bytes()) != snapshot.hash:
                raise StoreError(f"{path} is corrupt; refusing to overwrite a snapshot")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".partial")
            tmp.write_bytes(data)
            tmp.replace(path)
        self.log("snapshot", **snapshot.model_dump(mode="json"))
        return snapshot

    def get(self, content_hash: str) -> bytes:
        path = self._path(content_hash)
        if not path.exists():
            raise StoreError(f"no snapshot {content_hash}")
        data = path.read_bytes()
        if hash_bytes(data) != content_hash:
            raise StoreError(f"snapshot {content_hash} changed on disk")
        return data

    def has(self, content_hash: str) -> bool:
        return self._path(content_hash).exists()

    def log(self, event: str, **fields: Any) -> None:
        self._catalogue.parent.mkdir(parents=True, exist_ok=True)
        entry = {"event": event, "at": datetime.now(timezone.utc).isoformat()} | fields
        with self._catalogue.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")

    def events(self, event: str | None = None) -> list[dict[str, Any]]:
        if not self._catalogue.exists():
            return []
        lines = self._catalogue.read_text(encoding="utf-8").splitlines()
        entries = [json.loads(line) for line in lines if line.strip()]
        return [e for e in entries if event is None or e["event"] == event]

    def latest_snapshot(self, recipe_ref: str) -> Snapshot:
        found = [e for e in self.events("snapshot") if e["recipe"] == recipe_ref]
        if not found:
            raise StoreError(f"no snapshot yet for {recipe_ref}; fetch it first")
        entry = {k: v for k, v in found[-1].items() if k not in ("event", "at")}
        return Snapshot.model_validate(entry)
