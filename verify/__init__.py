"""
verify — the independent verification program.

Deliberately NOT part of the `asi` package. Verification that imports the code
it checks inherits that code's bugs; this package re-reads the registry YAML and
re-derives results with different tools (numpy eigendecomposition instead of
sklearn PCA, a merge_asof join instead of the pipeline's dictionary scan).
`tests/test_verify_independence.py` enforces this by AST scan: no module here may
import from `asi` except `asi.core.constants`, which holds declared thresholds
rather than logic.

Four layers, run together by `python -m verify.run`:

    panel       re-derive the panel from the frozen raw baseline and compare
                against what the pipeline wrote                   (pass/fail)
    contract    the backend/frontend object contract: identity, aggregation
                reconciliation, no re-derivation in the UI        (pass/fail)
    narrative   narrative claims against the panel they describe  (pass/fail)
    advisory    design diagnostics — effective weights, source concentration,
                within- and cross-pillar redundancy, reference-year data
                quality, external plausibility                    (report only)

`advisory` is judgement, not arithmetic, so it reports and never blocks: gating a
release on a judgement call trains people to ignore the gate.

Coverage is stated precisely because it was once overstated. `panel` re-derives
38,276 of 43,200 scoring cells (88.6%). The remaining 11.4% are regional-mean
estimates, which by construction cannot be predicted from a country's own data;
the MIN_REGIONAL_SAMPLE rule and the reliability tiers carry those instead.
"""

__all__ = ["panel", "contract", "narrative", "advisory"]
