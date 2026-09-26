# athena-core

The contracts every **Athena** project is built on.

Athena recreates published datasets and indices from the publishers' own methods, then checks every step against the values the publishers released. This package defines the pieces that loop is made of.

| Module | What it defines |
| --- | --- |
| `ids` | Ids (`kind:slug`), versions and content hashes |
| `vocab` | The closed vocabularies: column roles, frame profiles, validation levels, reproducibility classes, divergence causes |
| `base` | `Record` (immutable, validated, refuses unknown fields) and `Definition` (a record with an id and a version) |
| `sources` | `SourceCard`, `Terms`, `Recipe`, `Snapshot`, and the `FormatReader` base class |
| `method` | `MethodCard`: numbered steps quoting the published text, a readings log, and the values published along the way |
| `steps` | The `Step` base class, with declared inputs, output, parameters and invariants, plus the shell registry and cards |
| `frames` | `Frame`: an Arrow table plus a `Manifest` whose columns declare their roles |
| `validation` | The sealed `AnswerKey`, `Tolerance`, `Checkpoint`, the blame window, and the append-only `DivergenceRegister` |
| `indicators` | `Indicator`, `CompositeIndex` trees, and `Justification`: a publisher's reasons, quoted and filed by criterion |
| `reference` | `Grouping`: region lists and other code lists, versioned like any definition |
| `runs` | `RunRecord`: the receipt that lets any result be rebuilt and compared exactly |

`tests/test_pipeline.py` runs the whole loop in miniature. It builds a regional figure, compares it with the answer key, catches a planted grouping fault, names the step at fault, and records the divergence.

## Where things are

- **The umbrella, with the Standard, decisions and section briefs:** `Oscarsb2004/athena-data`
- **Agent instructions:** `AGENTS.md`
- **What this repository is, for programs:** `athena-repo.yaml`
