"""
asi.dashboard — UI data access and components.

`data.py` is the only place the interface touches stored results. It filters
and formats; it never computes a score, a rank, or a label. Everything it
returns was produced by the pipeline and verified by verify/panel.py, which is
what makes the contract in verify/contract.py checkable.
"""
