"""
app.py — Web entry point for Railway / Render / gunicorn deployment.

Usage:
    gunicorn app:server --bind 0.0.0.0:$PORT

The dashboard lives in 07_dashboard.py. That file cannot be imported as a
Python module directly (files starting with digits are not valid identifiers),
so this shim uses importlib to load it and re-export the Flask server object.

Environment variables (set in Railway/Render dashboard):
  PORT    — bound port (set automatically by Railway; default 8050)
  DEBUG   — "true" to enable Dash debug mode (default: false)
"""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "dashboard", Path(__file__).parent / "07_dashboard.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

server = _mod.server  # gunicorn binds to this
