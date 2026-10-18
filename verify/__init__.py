"""
verify — the independent verification program.

Deliberately NOT part of the `asi` package. Verification that imports the code
it checks inherits that code's bugs; this package re-reads the registry YAML and
re-derives results with different tools (numpy eigendecomposition instead of
sklearn PCA, a merge_asof join instead of the pipeline's dictionary scan).
`tests/test_verify_independence.py` enforces this by AST scan: no module here may
import from `asi` except `asi.core.constants`, which holds declared thresholds
rather than logic.

Five layers, run together by `python -m verify.run`:

    rebuild     rerun the pipeline from data/inputs.csv in a scratch copy; every
                committed output must come back byte for byte    (pass/fail)
    panel       re-derive the panel from its inputs (data/inputs.csv, written
                from Athena's datasets) and compare against what the pipeline
                wrote                                             (pass/fail)
    contract    the backend/frontend object contract: identity, aggregation
                reconciliation, no re-derivation in the UI        (pass/fail)
    narrative   narrative claims against the panel they describe  (pass/fail)
    advisory    design diagnostics — effective weights, source concentration,
                within- and cross-pillar redundancy, reference-year data
                quality, external plausibility                    (report only)

`advisory` is judgement, not arithmetic, so it reports and never blocks: gating a
release on a judgement call trains people to ignore the gate.

Coverage is stated precisely because it was once overstated. In edition 1, `panel`
re-derived 38,276 of 43,200 scoring cells (88.6%); the other 11.4% were
regional-mean estimates, which cannot be predicted from a country's own data.
From edition 2 there is no regional fill, so every cell with a value is
re-derived (78,234 by the as-of join alone at step 6, the rest by the rolling-mean,
volatility, parity and per-capita checks).
"""

__all__ = ["rebuild", "panel", "contract", "narrative", "advisory"]
