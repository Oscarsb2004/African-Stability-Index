"""Which PortWatch port a USGS port is, by published keys only: USGS's World Port Index ID, NGA's World Port Index
(index number to UN/LOCODE) and PortWatch's LOCODE. A port is linked only where every step gives exactly one answer;
a port not linked is counted by the step where the chain stops. Never by name or by distance.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from athena.adapters.nga_wpi import locode
from athena.component import Component


class PortLinks(Component):
    """USGS port -> PortWatch port, through the World Port Index, with a count of where each unlinked port stops."""

    section = "06 Outputs and Site"

    @dataclass(frozen=True)
    class Input:
        usgs: pd.DataFrame          # USGS's ports, one row per commodity: `FeatureUID` and the WPI ID column
        key: str                    # the WPI ID column (USGS's DsgAttr10, "World Port Index (WPI) ID")
        codes: dict                 # index number -> LOCODE where the number's rows agree (athena's nga_wpi.locodes)
        ambiguous: tuple            # index numbers whose rows give two LOCODEs
        portwatch: pd.DataFrame     # PortWatch's ports: `portid`, `portname`, `LOCODE`

    @dataclass(frozen=True)
    class Output:
        links: dict                 # FeatureUID -> {"portwatch": portid, "portwatch_name": portname}
        counts: dict                # "linked", and each step where a chain stops

    def run(self, inp: Input) -> Output:
        pw = inp.portwatch.assign(code=inp.portwatch["LOCODE"].fillna("").map(locode))
        pw = pw[pw["code"] != ""]
        by_code = pw.groupby("code")
        counts = dict.fromkeys(["linked", "no WPI ID", "two WPI IDs", "WPI ID gives two LOCODEs",
                                "WPI ID has no LOCODE", "LOCODE not in PortWatch", "LOCODE on two PortWatch ports"], 0)
        links = {}
        for uid, rows in inp.usgs.groupby("FeatureUID", sort=True):
            ids = set(pd.to_numeric(rows[inp.key], errors="coerce").dropna().astype(int))
            if len(ids) != 1:
                counts["two WPI IDs" if ids else "no WPI ID"] += 1
                continue
            n = ids.pop()
            if n in inp.ambiguous:
                counts["WPI ID gives two LOCODEs"] += 1
            elif n not in inp.codes:
                counts["WPI ID has no LOCODE"] += 1
            elif inp.codes[n] not in by_code.groups:
                counts["LOCODE not in PortWatch"] += 1
            elif len(match := by_code.get_group(inp.codes[n])) > 1:
                counts["LOCODE on two PortWatch ports"] += 1
            else:
                links[uid] = {"portwatch": match["portid"].iloc[0], "portwatch_name": match["portname"].iloc[0]}
                counts["linked"] += 1
        return self.Output(links, counts)
