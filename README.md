# athena-core

**Athena** ingests published statistical databases into one common format, runs reusable operations ("shells") on
that format, and checks what it rebuilds against the values the publishers printed. The first proof is the
Millennium Development Goals.

## Layout

| Path | What it is |
| --- | --- |
| `athena/` | The generic parts: fetch once and keep forever (`fetch`), the common format (`table`), datasets in the store (`dataset`), formula aggregation (`aggregate`) and comparison at the publisher's decimals (`check`) |
| `adapters/` | One adapter per database: each reads one publisher's format and writes a dataset in the common format, with a report of every loss and its reason. `sources.toml` lists every source and its terms; `sources.lock` holds the hash of every address fetched |
| `mdg/` | The first replication project (MDG 3.3 and 3.1). Milestone S1 replaces it with a short project script over the datasets |
| `test/` | Tests on synthetic fixtures only; no publisher material is committed |

## Commands

```bash
.venv/Scripts/python -m pip install -r requirements.lock
.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m adapters mdg        # ingest the MDG database, annex and groupings as datasets in the store
.venv/Scripts/python -m adapters worldbank  # ingest the whole WDI and WGI, each as a dataset named after its edition
.venv/Scripts/python -m mdg check       # the M1 project: build 3.3 and 3.1, compare with the publishers
```

The store is `C:\AthenaStore` unless `ATHENA_STORE` says otherwise. The build never imports `mdg.answers`, and a
test fails if it does. Work built on UN and IPU material stays private (decision P24).

## Licence

**Source-available, all rights reserved.** You may read the code to evaluate the work. You may not use, copy, modify
or distribute it without written permission. See [LICENSE](LICENSE).

The plan and the decisions live in the private umbrella repository, `athena-data`.
