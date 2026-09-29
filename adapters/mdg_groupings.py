"""Country lists and groupings for the MDGs: dataset mdg-groupings-2015, as `areas` and `membership` tables.

The groups are the official MDG regional groupings, with the lists of least developed and landlocked developing
countries in force in January 2015 swapped in whole for the document's older lists (owner ruling of 2026-09-26).
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from adapters import readers
from adapters.codes import Coder, load_aliases

NAME = "mdg-groupings-2015"
REPLACEMENTS = ("ldc-2014", "lldc-2014")

# Each group's id and its name as the annex prints it.
GROUP_NAMES = {
    "world": "World", "developing": "Developing regions", "developed": "Developed regions",
    "northern-africa": "Northern Africa", "sub-saharan-africa": "Sub-Saharan Africa",
    "latin-america-and-the-caribbean": "Latin America and the Caribbean", "caribbean": "Caribbean",
    "latin-america": "Latin America", "eastern-asia": "Eastern Asia",
    "eastern-asia-excluding-china": "Eastern Asia excluding China", "southern-asia": "Southern Asia",
    "southern-asia-excluding-india": "Southern Asia excluding India", "south-eastern-asia": "South-Eastern Asia",
    "western-asia": "Western Asia", "oceania": "Oceania", "caucasus-and-central-asia": "Caucasus and Central Asia",
    "least-developed": "Least developed countries", "landlocked-developing": "Landlocked developing countries",
    "small-island-developing": "Small island developing States",
    "south-eastern-asia-including-oceania": "South-Eastern Asia (including Oceania)",
    "central-africa-eca": "Central Africa", "eastern-africa-eca": "Eastern Africa", "north-africa-eca": "North Africa",
    "southern-africa-eca": "Southern Africa", "west-africa-eca": "West Africa",
}
# Groups the annex prints but no source available to us lists the members of.
UNLISTED_GROUPS = {"annex-i-countries": "Annex I countries", "all-developing-countries": "All developing countries",
                   "developing-countries": "Developing countries", "european-union": "European Union (EU)"}


def coder(fetch: Callable[[str], bytes], sources: dict) -> tuple[Coder, dict[str, str]]:
    """The name-to-code table, and M49's own names by code."""
    m49 = readers.m49_codes(fetch(sources["m49"]["url"]))
    return Coder(m49, load_aliases()), {c: n for n, c in m49.items()}


def ingest(fetch: Callable[[str], bytes], sources: dict, code: Coder,
           m49_names: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    listed = {(name, group): sources["groupings"]["title"]
              for name, group in readers.groupings(fetch(sources["groupings"]["url"]))}
    for key in REPLACEMENTS:
        source = sources[key]
        read = {"ldc-pdf": readers.ldc_names, "lldc-html": readers.lldc_names}[source["kind"]]
        listed = {p: t for p, t in listed.items() if p[1] != source["group"]}
        listed |= {(name, source["group"]): source["title"] for name in read(fetch(source["url"]))}
    membership = pd.DataFrame(sorted({(c, group, title) for (name, group), title in listed.items()
                                      if (c := code(name))}), columns=["member", "group", "list"])
    alias_names = {c: n for n, c in load_aliases().items()}
    countries = sorted(set(code.codes.values()) - set(GROUP_NAMES) - set(UNLISTED_GROUPS))
    areas = pd.DataFrame(
        [{"REF_AREA": c, "name": m49_names.get(c) or alias_names[c], "kind": "country"} for c in countries]
        + [{"REF_AREA": g, "name": n, "kind": "group"} for g, n in GROUP_NAMES.items()]
        + [{"REF_AREA": g, "name": n, "kind": "group, members not listed"} for g, n in UNLISTED_GROUPS.items()])
    unknown = sorted(set(membership["group"]) - set(GROUP_NAMES))
    if unknown:
        raise ValueError(f"groups with no name: {unknown}")
    report = [f"{NAME}: {len(countries)} country codes, {len(GROUP_NAMES)} groups, {len(membership)} memberships"]
    report += [f"  {g}: {n} members" for g, n in membership.groupby("group").size().items()]
    return areas, membership, report
