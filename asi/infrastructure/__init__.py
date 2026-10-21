"""The Infrastructure section's data stage (P65), as components (P112): `10_infrastructure.py` reads the store and
the publication list, runs these, and writes what they return.

- registry: the publication list (`registry/layers.yaml`), checked before anything is built;
- places: which member state a point or a line belongs to, by a stated rule;
- layers: one point layer's GeoJSON and catalogue entry; one line layer's tile layers, entry and lengths; each
  state's summary for the country panel;
- tiles: the vector tiles, written to one PMTiles archive (the only component here that writes).
"""
