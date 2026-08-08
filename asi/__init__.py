"""
asi — African Stability Index.

A composite stability index for peer-to-peer country comparison and
single-country analysis, pairing quantitative indicators with cited
qualitative history.

Layout:
    asi.core        constants, canonical schema, registry, country/region data
    asi.pipeline    data stages (added in Phase B; today's stages are the
                    numbered scripts at the repo root)
    asi.dashboard   UI (moved in Phase C)
    asi.narrative   research/narrative system (added in Phase D)

Verification lives OUTSIDE this package, in `verify/`, so that it can never
import the code it is meant to check independently.
"""

__version__ = "2.0.0-dev"
