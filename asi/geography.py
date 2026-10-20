"""Where each member state is, from Natural Earth's 1:50m countries (public domain): its subregion, and which member
states it borders.

Natural Earth's `SUBREGION` (Northern, Western, Middle, Eastern and Southern Africa) is the only regional division the
site uses. Edition 1's own six regions, with islands as a region of their own, are not carried over (P105); an
island state sits in its geographic subregion like any other state.

Two states are neighbours when their 1:50m polygons meet: they intersect once each is widened by NEIGHBOUR_TOLERANCE
degrees, which absorbs the generalisation of shared boundaries at that scale. Island states have no land neighbours.
"""

from __future__ import annotations

from asi.core.countries import COUNTRIES

MERGED = {"SOL": "SOM", "SDS": "SSD"}  # Somaliland is drawn as Somalia; Natural Earth codes South Sudan SDS
NEIGHBOUR_TOLERANCE = 0.01  # degrees, about 1 km


def code(properties: dict) -> str:
    """A Natural Earth feature's state, in the index's codes."""
    return MERGED.get(properties["ADM0_A3"], properties["ADM0_A3"])


def subregions(ne_countries: dict) -> dict[str, str]:
    """Each member state's Natural Earth subregion. A state with no polygon, or two polygons that disagree, stops."""
    out: dict[str, str] = {}
    for f in ne_countries["features"]:
        iso3, sub = code(f["properties"]), f["properties"]["SUBREGION"]
        if iso3 in COUNTRIES:
            if out.get(iso3, sub) != sub:
                raise ValueError(f"{iso3}: Natural Earth gives two subregions, {out[iso3]} and {sub}")
            out[iso3] = sub
    missing = sorted(set(COUNTRIES) - set(out))
    if missing:
        raise ValueError(f"member states with no Natural Earth polygon: {missing}")
    return dict(sorted(out.items()))


def neighbours(ne_countries: dict) -> dict[str, list[str]]:
    """Each member state's member neighbours on land, from the polygons (needs the [geo] extra's shapely)."""
    from shapely.geometry import shape
    from shapely.ops import unary_union

    parts: dict[str, list] = {}
    for f in ne_countries["features"]:
        iso3 = code(f["properties"])
        if iso3 in COUNTRIES:
            parts.setdefault(iso3, []).append(shape(f["geometry"]))
    widened = {k: unary_union(v).buffer(NEIGHBOUR_TOLERANCE) for k, v in parts.items()}
    out = {k: [] for k in sorted(widened)}
    keys = sorted(widened)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if widened[a].intersects(widened[b]):
                out[a].append(b)
                out[b].append(a)
    return {k: sorted(v) for k, v in out.items()}
