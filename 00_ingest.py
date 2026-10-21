"""
00_ingest.py — the ASI's inputs, each database whole, into the store (P37, P38), through athena-kit's athena.ingest.

    python 00_ingest.py wdi-bulk wgi-bulk ucdp-organized-violence imf-weo undp-hdr ti-cpi wikidata-states \
        glottolog-cldf usgs-africa-gis wb-africa-grid asi-pull

Each key is a source in `sources.toml`; its bytes are held to `sources.lock`. The kinds are athena-kit's adapters,
plus this project's own: its frozen pull of August 2026 (`asi.adapters.asi_pull`).
"""

import sys
from pathlib import Path

from athena.ingest import Batch, Ingest, Project, Result

ROOT = Path(__file__).resolve().parent


def frozen_pull(src: dict, get) -> Result:
    """The ASI's own kind: its frozen pull, read from the project's folder."""
    from asi.adapters import asi_pull
    return Result(*asi_pull.ingest(get(src["url"])))


KINDS = {"asi-pull": frozen_pull}


def main(keys: list[str]) -> int:
    if not keys:
        print(__doc__)
        return 2
    print("\n".join(Batch(Project(ROOT), keys).run(Ingest(KINDS))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
