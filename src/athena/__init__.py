"""athena-core: the contracts every Athena project is built on.

Definitions are data (immutable, validated records); behaviour lives in a few small base classes
(`FormatReader`, `Step`). Read the modules in pipeline order: sources, method, steps, frames, validation, runs.
"""

__version__ = "0.1.0.dev0"
