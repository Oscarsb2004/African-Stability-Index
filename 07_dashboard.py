"""
07_dashboard.py — run the interface.

    python 07_dashboard.py     ->  http://127.0.0.1:8050

Thin runner. The interface itself lives in asi/dashboard/, which is importable
(this filename starts with a digit and cannot be), so it can be tested and
served by gunicorn without the importlib shim the previous version needed.
"""

from asi.dashboard.app import main

if __name__ == "__main__":
    raise SystemExit(main())
