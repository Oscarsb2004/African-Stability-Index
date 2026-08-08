"""
verify — the independent verification program.

Deliberately NOT part of the `asi` package. Verification that imports the code
it checks inherits that code's bugs; this package re-reads the registry YAML and
re-derives results with different tools (numpy eigendecomposition instead of
sklearn PCA, scipy HiGHS instead of pulp/CBC).

Three layers, run together by `python -m verify.run`:

    replicate   recompute every published number from the frozen raw pull and
                compare against what the pipeline wrote          (pass/fail)
    contract    the backend/frontend object contract: identity, aggregation
                reconciliation, no re-derivation in the UI       (pass/fail)
    advisory    design diagnostics — correlations, effective weights, coverage,
                staleness, benchmark plausibility                (report only)

Only `replicate` and `contract` gate a release. `advisory` is judgement, not
arithmetic, so it reports and never blocks.
"""

__all__ = ["replicate", "contract", "advisory"]
