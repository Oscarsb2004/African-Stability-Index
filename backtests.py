"""
backtests.py — does a lower ASI score come before instability? The rules are pre-registered in the vault
(`ASI Backtest Protocol` and the notes BT1 to BT7, committed 2026-10-18 before any test was run).

A state-year t is at risk when the state is free of the event at t; its outcome is whether the event happens in
t+1 to t+h. A non-event needs every year of the window observed; unknown windows are left out. Predictors are
oriented as risk, so a higher value means more risk (the ASI enters as minus its score).

AUC is the probability that an at-risk state-year followed by an event ranks riskier than one that is not, ties
counting half (Mann–Whitney). Its 95% interval comes from resampling states with replacement, so a state's years
stay together. Each predictor is scored on the rows where it has a value; a difference uses rows where both do.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SEED, DRAWS = 20261018, 2000


def auc(risk, event) -> float:
    risk, event = np.asarray(risk, float), np.asarray(event, bool)
    keep = ~np.isnan(risk)
    risk, event = risk[keep], event[keep]
    n_pos, n_neg = int(event.sum()), int((~event).sum())
    if not n_pos or not n_neg:
        return float("nan")
    ranks = pd.Series(risk).rank().to_numpy()
    return float((ranks[event].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def windows(flags: pd.DataFrame, first: int, last: int, h: int) -> pd.DataFrame:
    """Rows (iso3, year, event) for every at-risk state-year t in [first, last]. `flags` is states by years:
    1 where the event happened, 0 where the year was observed without it, NaN where it is unknown."""
    rows = []
    for t in range(first, last + 1):
        span = [y for y in range(t + 1, t + h + 1)]
        if t not in flags.columns or any(y not in flags.columns for y in span):
            continue
        for iso3, now in flags[t].items():
            if pd.isna(now) or now == 1:
                continue
            window = flags.loc[iso3, span]
            if (window == 1).any():
                rows.append((iso3, t, True))
            elif window.notna().all():
                rows.append((iso3, t, False))
    return pd.DataFrame(rows, columns=["iso3", "year", "event"])


def history(flags: pd.DataFrame, iso3: str, t: int, k: int = 5) -> float:
    """1 if the event happened in any of t-k to t-1, else 0 (an unknown year counts as none)."""
    years = [y for y in range(t - k, t) if y in flags.columns]
    return float((flags.loc[iso3, years] == 1).any()) if years else 0.0


def compare(rows: pd.DataFrame, predictors: list[str], baseline: str | None) -> dict:
    """Each predictor's AUC with its interval, and (when a baseline is named) its AUC minus the baseline's."""
    rng = np.random.default_rng(SEED)
    states = rows["iso3"].unique()
    index = {s: np.flatnonzero(rows["iso3"].to_numpy() == s) for s in states}
    event = rows["event"].to_numpy(bool)
    columns = {p: rows[p].to_numpy(float) for p in predictors}

    def scores(idx):
        out = {p: auc(columns[p][idx], event[idx]) for p in predictors}
        if baseline:
            for p in predictors:
                if p != baseline:
                    both = ~np.isnan(columns[p][idx]) & ~np.isnan(columns[baseline][idx])
                    out[f"{p} - {baseline}"] = (auc(columns[p][idx][both], event[idx][both])
                                                - auc(columns[baseline][idx][both], event[idx][both]))
        return out

    point = scores(np.arange(len(rows)))
    draws = {k: [] for k in point}
    for _ in range(DRAWS):
        idx = np.concatenate([index[s] for s in rng.choice(states, len(states))])
        for k, v in scores(idx).items():
            draws[k].append(v)
    out = {}
    for k, v in point.items():
        d = np.array(draws[k])
        d = d[~np.isnan(d)]
        out[k] = {"value": v, "low": float(np.percentile(d, 2.5)), "high": float(np.percentile(d, 97.5))}
    return out


def verdict(result: dict, predictor: str, baseline: str) -> dict:
    """The protocol's two pass rules."""
    a, diff = result[predictor], result.get(f"{predictor} - {baseline}")
    return {"informative": a["low"] > 0.5, "adds_to_development": bool(diff and diff["low"] > 0)}


def hit_rate(rows: pd.DataFrame, bottom: pd.Series) -> dict:
    """The share of events whose state was in the bottom fifth of the composite in year t (chance: 20%)."""
    events = rows[rows["event"]]
    flags = [bool(bottom.get((r.iso3, r.year), False)) for r in events.itertuples()]
    return {"events": len(flags), "in_bottom_fifth": int(sum(flags)),
            "share": float(np.mean(flags)) if flags else float("nan")}
