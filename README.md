# athena-core

The contracts every **Athena** project is built on.

Athena recreates published datasets and indices from the publishers' own methods, then checks every step against the values the publishers released. This package defines the pieces that loop is made of.

| Module | What it defines |
| --- | --- |
| `ids` | Ids (`kind:slug`), versions and content hashes |
| `vocab` | The closed vocabularies: SDMX concepts, column roles, frame profiles, validation levels, reproducibility classes, divergence causes |
| `base` | `Record` (immutable, validated, refuses unknown fields) and `Definition` (a record with an id and a version) |
| `sources` | `SourceCard`, `Terms`, `Recipe`, `Snapshot`, and the `FormatReader` base class |
| `citations` | `Citation`: a locator in a stored document, and the quote that must be found verbatim there |
| `method` | `MethodCard`: numbered steps quoting the published text, a readings log, the values published along the way, and the rounding rule |
| `rounding` | `Rounding`: half up by default, or the publisher's cited rule, applied to the number as written |
| `steps` | The `Step` base class, with declared inputs, output, parameters and invariants, plus the shell registry and cards |
| `frames` | `Frame`: an Arrow table plus a `Manifest` whose columns declare their roles |
| `validation` | The sealed `AnswerKey`, `Tolerance`, `Checkpoint`, the blame window, and the append-only `DivergenceRegister` |
| `indicators` | `Indicator`, `CompositeIndex` trees, and `Justification`: a publisher's reasons, quoted and filed by criterion |
| `reference` | `Grouping`: a small versioned definition that points, by hash, at a membership frame of member, group and level. Levels can nest and lists can overlap (decision P19) |
| `runs` | `RunRecord`: the receipt that lets any result be rebuilt and compared exactly |
| `schemas` | JSON Schema export. The Python definitions are the single source of truth; `schemas/` is generated from them |

`tests/test_pipeline.py` runs the whole loop in miniature. It builds a regional figure and checks both the region list and the regional values against the publisher. A planted wrong region is caught at the first checkpoint, which narrows the fault to the grouping step, and the divergence is recorded.

## Licence

Apache-2.0. See [LICENSE](LICENSE).

## Where things are

- **The umbrella, with the Standard, decisions and section briefs:** `Oscarsb2004/athena-data`
- **Agent instructions:** `AGENTS.md`
- **What this repository is, for programs:** `athena-repo.yaml`
