"""JSON Schema export: the Python definitions are the single source of truth (decision 1).

Other tools - the umbrella's validator, a web front end, a selection model - read the exported schemas instead of
keeping their own copies, so the definitions cannot drift apart.

    python -m athena.schemas <output-folder>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from athena.base import Definition

# Importing the modules registers every Definition subclass.
from athena import indicators, method, reference, sources, steps  # noqa: F401


def definitions() -> dict[str, type[Definition]]:
    found: dict[str, type[Definition]] = {}
    pending = list(Definition.__subclasses__())
    while pending:
        cls = pending.pop()
        pending.extend(cls.__subclasses__())
        if cls.__module__.startswith("athena."):
            if cls.KIND in found and found[cls.KIND] is not cls:
                raise TypeError(f"two definitions claim kind {cls.KIND!r}: {found[cls.KIND]} and {cls}")
            found[cls.KIND] = cls
    return dict(sorted(found.items()))


def render() -> dict[str, str]:
    """File name to file content, for every definition."""
    out = {}
    for kind, cls in definitions().items():
        schema = cls.model_json_schema()
        schema["$id"] = f"athena-core/{kind}.schema.json"
        out[f"{kind}.schema.json"] = json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return out


def export(folder: Path) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for name, content in render().items():
        path = folder / name
        path.write_text(content, encoding="utf-8", newline="\n")
        written.append(path)
    return written


if __name__ == "__main__":
    for path in export(Path(sys.argv[1] if len(sys.argv) > 1 else "schemas")):
        print(path)
