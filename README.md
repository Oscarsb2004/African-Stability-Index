# athena-core

**Athena** ingests published statistical databases into one common format, runs reusable operations ("shells") on
that format, and checks what it rebuilds against the values the publishers printed. The first proof is the
Millennium Development Goals.

## Layout

| Path | What it is |
| --- | --- |
| `athena/` | The generic parts: fetch once and keep forever (`fetch`), the common format (`table`), formula aggregation (`aggregate`) and comparison at the publisher's decimals (`check`) |
| `mdg/` | The MDG replication: its sources, readers, the sealed answer key, build and check. In the next milestone it splits into database adapters and a project configuration |
| `test/` | Tests on synthetic fixtures only; no publisher material is committed |

## Commands

```bash
.venv/Scripts/python -m pip install -r requirements.lock
.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m mdg fetch    # download every source once; hashes go to mdg/sources.lock
.venv/Scripts/python -m mdg check    # build, compare with the publishers, write the scoreboard to the store
```

The store is `C:\AthenaStore` unless `ATHENA_STORE` says otherwise. The build never imports `mdg.answers`, and a
test fails if it does. Work built on UN and IPU material stays private (decision P24).

## Licence

**Source-available, all rights reserved.** You may read the code to evaluate the work. You may not use, copy, modify
or distribute it without written permission. See [LICENSE](LICENSE).

The plan and the decisions live in the private umbrella repository, `athena-data`.
