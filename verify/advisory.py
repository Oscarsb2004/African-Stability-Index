"""
verify/advisory.py — design diagnostics. Reports; never blocks.

These are judgement calls, not arithmetic. Whether Pillar A leaning heavily on
one source family is acceptable is a decision for a person; failing a build over
it would only train people to ignore the gate. Everything here therefore prints
and exits 0.

Ported to the panel in Phase C. The previous version read the legacy snapshot
files, which no longer exist.

Run:  python verify/advisory.py
"""

import sys as _sys
from pathlib import Path as _Path

_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_REPO))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from asi.core.constants import PILLAR_DEFS
from asi.dashboard import data as D

# Mo Ibrahim Foundation, IIAG 2023 — an external sanity check, not a target.
IIAG_TOP5    = {"MUS", "CPV", "SYC", "BWA", "ZAF"}
IIAG_BOTTOM5 = {"SSD", "SOM", "ERI", "SDN", "COD"}

NOTES: list[str] = []


def section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def note(text: str) -> None:
    NOTES.append(text)
    print(f"  {text}")


def main() -> int:
    panel = D.load()
    year = panel.reference_year
    print("=" * 78)
    print(f"ADVISORY -- design diagnostics at {year} (report only)")
    print("=" * 78)

    scoring = {v: m for v, m in panel.indicators.items() if m.get("role") == "scoring"}

    # ── effective weights ─────────────────────────────────────────────────────
    section("Effective weight per indicator")
    sizes = {p: len(panel.pillars[p]["indicators"]) for p in PILLAR_DEFS}
    eff = {
        v: sum((1 / len(PILLAR_DEFS)) / sizes[p] for p in m["pillars"] if sizes.get(p))
        for v, m in scoring.items()
    }
    even = 1 / len(scoring)
    ranked = sorted(eff.items(), key=lambda kv: -kv[1])
    note(f"pillar sizes: {sizes}")
    for v, w in ranked[:4]:
        note(f"{v}: {w*100:.2f}% ({w/even:.2f}x an even share) "
             f"pillars={'+'.join(scoring[v]['pillars'])}")
    note(f"lowest: {ranked[-1][0]} at {ranked[-1][1]*100:.2f}% "
         f"({ranked[-1][1]/even:.2f}x)")
    spread = ranked[0][1] / ranked[-1][1]
    note(f"heaviest indicator carries {spread:.1f}x the lightest — equal pillar "
         f"weights are not equal indicator weights")

    # ── source concentration ──────────────────────────────────────────────────
    section("Source concentration")
    by_db: dict[str, float] = {}
    for v, m in scoring.items():
        by_db[m.get("database", "?")] = by_db.get(m.get("database", "?"), 0) + eff[v]
    for db, w in sorted(by_db.items(), key=lambda kv: -kv[1]):
        n = sum(1 for m in scoring.values() if m.get("database") == db)
        note(f"{db.upper()}: {n} indicators carrying {w*100:.1f}% of composite weight")

    # ── within-pillar redundancy ──────────────────────────────────────────────
    section("Within-pillar redundancy (|rho| > 0.80 at the reference year)")
    obs = panel.observations
    at_year = obs[(obs["year"] == year) & (obs["role"] == "scoring")]
    wide = at_year.pivot_table(index="iso3", columns="variable_name",
                               values="score", aggfunc="first")
    found = 0
    for pid, meta in panel.pillars.items():
        members = [v for v in meta["indicators"] if v in wide.columns]
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                pair = wide[[a, b]].dropna()
                if len(pair) < 10:
                    continue
                rho = spearmanr(pair[a], pair[b]).statistic
                if abs(rho) > 0.80:
                    found += 1
                    note(f"{pid}: {a} x {b} rho={rho:+.2f}")
    if not found:
        note("none")

    # ── cross-pillar redundancy ───────────────────────────────────────────────
    section("Cross-pillar redundancy (|rho| > 0.80, different pillars)")
    cols = [c for c in wide.columns if c in scoring]
    found = 0
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            if set(scoring[a]["pillars"]) & set(scoring[b]["pillars"]):
                continue
            pair = wide[[a, b]].dropna()
            if len(pair) < 10:
                continue
            rho = spearmanr(pair[a], pair[b]).statistic
            if abs(rho) > 0.80:
                found += 1
                note(f"{a} ({'+'.join(scoring[a]['pillars'])}) x "
                     f"{b} ({'+'.join(scoring[b]['pillars'])}): rho={rho:+.2f}")
    if not found:
        note("none")

    # ── data quality ──────────────────────────────────────────────────────────
    section("Data quality at the reference year")
    prov = at_year["provenance"].value_counts()
    total = int(prov.sum())
    for kind, n in prov.items():
        note(f"{kind}: {n} cells ({n/total*100:.1f}%)")
    weakest = (
        at_year.assign(real=at_year["provenance"].eq("observed"))
        .groupby("variable_name")["real"].mean().sort_values().head(5)
    )
    note("least directly measured indicators:")
    for v, share in weakest.items():
        note(f"   {v}: {share*100:.0f}% measured")

    pil = panel.pillar_scores
    tiers = pil[pil["year"] == year]["reliability"].value_counts()
    note(f"pillar tiers: {dict(tiers)}")

    # ── external plausibility ─────────────────────────────────────────────────
    section("External plausibility (IIAG 2023)")
    comp = panel.composites
    eq = comp[(comp["year"] == year) & (comp["method"] == "equal")
              & comp["rank"].notna()].sort_values("rank")
    top10 = set(eq.head(10)["iso3"])
    bottom10 = set(eq.tail(10)["iso3"])
    note(f"IIAG top-5 appearing in our top-10:    {len(IIAG_TOP5 & top10)}/5 "
         f"{sorted(IIAG_TOP5 & top10)}")
    note(f"IIAG bottom-5 appearing in our bottom-10: {len(IIAG_BOTTOM5 & bottom10)}/5 "
         f"{sorted(IIAG_BOTTOM5 & bottom10)}")
    missing = IIAG_BOTTOM5 - set(eq["iso3"])
    if missing:
        note(f"not rankable this year (insufficient data): {sorted(missing)}")

    print()
    print("-" * 78)
    print(f"advisory: {len(NOTES)} observations. Judgement, not arithmetic — "
          f"this layer never blocks a release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
