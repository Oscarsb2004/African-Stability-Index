"""Country and group values by formula.

A catalogue row names each country's variables, optional derived variables, and one formula for the value. A group's
value is the same formula applied to the sums of its members' variables. That single rule gives a ratio of sums
(women over seats, MDG 3.3), a ratio of ratios weighted by population (MDG 3.1), and a weighted mean (a derived w*x
summed over w).

Nothing is imputed: a country missing any variable the formula needs is left out of every group, and each group
reports how many countries it used.
"""

from __future__ import annotations

import ast

import numpy as np
import pandas as pd


def names(formula: str) -> list[str]:
    """The variable names a formula uses, in order of first use."""
    seen: list[str] = []
    for node in ast.walk(ast.parse(formula, mode="eval")):
        if isinstance(node, ast.Name) and node.id not in seen:
            seen.append(node.id)
    return seen


def complete(variables: pd.DataFrame, derive: dict[str, str], formula: str) -> pd.DataFrame:
    """Countries (the index) with every variable the formula needs, after deriving; each with its own value."""
    frame = variables.copy()
    for name, expression in derive.items():
        frame[name] = frame.eval(expression)
    needed = names(formula)
    known = frame[needed].replace([np.inf, -np.inf], np.nan).dropna()
    known["value"] = known.eval(formula)
    return known


def by_group(known: pd.DataFrame, members: pd.DataFrame, formula: str) -> pd.DataFrame:
    """The formula applied to each group's sums. `members` has columns member and group."""
    needed = names(formula)
    joined = members.merge(known[needed], left_on="member", right_index=True)
    sums = joined.groupby("group")[needed].sum()
    sums["countries"] = joined.groupby("group").size()
    sums["value"] = sums.eval(formula)
    return sums
