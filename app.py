"""
app.py — WSGI entry point for gunicorn / Railway.

    gunicorn app:server

The previous version loaded 07_dashboard.py through importlib because a module
name starting with a digit cannot be imported. The interface now lives in a
proper package, so this is a plain import.
"""

from asi.dashboard.app import server  # noqa: F401
