"""
asi.pipeline — the data stages.

Phase B introduces the panel: every stage works on
(country x indicator x year) rather than collapsing each series to a single
number. The modules are ordered as the data flows:

    panel       raw observations -> a dense yearly panel with provenance
    goalposts   fixed normalization bounds, computed once and frozen
    normalize   transform -> winsorize -> goalpost min-max
    score       pillar and composite scores, each carrying a reliability tier

Nothing here reads or writes files at import time; each module exposes pure
functions that the stage scripts call.
"""
