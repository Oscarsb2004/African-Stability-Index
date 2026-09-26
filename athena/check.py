"""Comparison with what a publisher printed.

Our value, in full precision, is rounded once to the publisher's decimals and must then equal the published value
exactly. Rounding once matters: 22.14951 is 22.1 at one decimal, but 22.2 by way of three decimals.
"""

from __future__ import annotations

import pandas as pd

from athena.table import round_half_up


def compare(ours: pd.Series, published: pd.Series, decimals: int) -> pd.DataFrame:
    """One row per key in either series: ours, ours rounded, published, and whether they match."""
    both = pd.DataFrame({"ours": ours, "published": published})
    both["rounded"] = [None if pd.isna(v) else round_half_up(v, decimals) for v in both["ours"]]
    both["match"] = both["rounded"].notna() & both["published"].notna() & (both["rounded"] == both["published"])
    both["difference"] = both["ours"] - both["published"]
    return both


def summary(compared: pd.DataFrame) -> dict[str, int | float]:
    """Counts for the scoreboard: compared, matched, missing (published, not ours), extra (ours, not published)."""
    has_ours, has_published = compared["ours"].notna(), compared["published"].notna()
    both = has_ours & has_published
    largest = compared.loc[both, "difference"].abs().max() if both.any() else 0.0
    return {"compared": int(both.sum()), "matched": int(compared["match"].sum()),
            "missing": int((has_published & ~has_ours).sum()), "extra": int((has_ours & ~has_published).sum()),
            "largest_difference": float(largest)}
