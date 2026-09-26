"""The store keeps bytes exactly, never overwrites, and catches a changed file the moment it is read."""

from datetime import datetime, timezone

import pytest

from athena.sources import Snapshot
from athena.store import Store, StoreError
from athena.transport import FixtureTransport

from test_sources import RECIPE, SOURCE


def snap(data: bytes) -> Snapshot:
    return Snapshot.of(data, source=SOURCE, recipe=RECIPE, url="https://example.org/x", media_type="text/csv",
                       retrieved_at=datetime(2026, 9, 26, tzinfo=timezone.utc))


def test_a_snapshot_round_trips_and_is_logged(tmp_path):
    store = Store(tmp_path)
    s = store.put(b"a,b\n1,2\n", snap(b"a,b\n1,2\n"))
    assert store.get(s.hash) == b"a,b\n1,2\n"
    assert store.latest_snapshot(RECIPE.ref) == s
    assert [e["event"] for e in store.events()] == ["snapshot"]


def test_bytes_that_do_not_match_their_snapshot_are_refused(tmp_path):
    with pytest.raises(StoreError, match="does not describe"):
        Store(tmp_path).put(b"other", snap(b"a,b\n1,2\n"))


def test_a_changed_file_is_caught_on_read_and_never_overwritten(tmp_path):
    store = Store(tmp_path)
    s = store.put(b"data", snap(b"data"))
    path = [p for p in (tmp_path / "snapshots").rglob("*") if p.is_file()][0]
    path.write_bytes(b"tampered")
    with pytest.raises(StoreError, match="changed on disk"):
        store.get(s.hash)
    with pytest.raises(StoreError, match="refusing to overwrite"):
        store.put(b"data", snap(b"data"))


def test_asking_for_a_recipe_never_fetched_is_an_error(tmp_path):
    with pytest.raises(StoreError, match="fetch it first"):
        Store(tmp_path).latest_snapshot("recipe:none@0.1.0")


def test_the_fixture_transport_serves_only_what_it_holds():
    transport = FixtureTransport({"https://example.org/a": b"x"})
    assert transport.get("https://example.org/a") == (b"x", "application/octet-stream")
    with pytest.raises(KeyError):
        transport.get("https://example.org/b")
