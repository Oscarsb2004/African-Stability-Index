"""
07_dashboard.py — African Stability Index · Interactive Dashboard
────────────────────────────────────────────────────────────────────
Hierarchical drill-down:

  Level 0  Continental Overview  ─ choropleth, top/bottom, summary stats
  Level 1  Country Profile       ─ pillar traffic lights, colonial context, qualitative notes
  Level 2  Pillar Detail         ─ indicator breakdown
  Level 3  Indicator Detail      ─ raw data, step-by-step formula walkthrough

Permanent tabs: Rankings · Methodology · Data Sources · Audit / Verification

Run: python 07_dashboard.py  →  http://127.0.0.1:8050
"""

import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yaml

from dash import Dash, dcc, html, Input, Output, State, ALL, callback_context, dash_table, no_update
import dash_bootstrap_components as dbc

from asi.core.constants import PILLAR_DEFS, WEIGHT_PRESETS, ISLAND_SET

# ── Paths ──────────────────────────────────────────────────────────────────────

RESULTS_JSON    = Path("data/06_results.json")
AUDIT_JSON      = Path("data/audit_report.json")
ROBUSTNESS_JSON = Path("data/05_robustness.json")
NORM_FILE       = Path("data/03_norm.xlsx")
CLEAN_FILE      = Path("data/02_clean.xlsx")
IND_DIR         = Path("indicators_list")
COLONIAL_FILE   = Path("context/colonial_history.yaml")
FACTS_FILE      = Path("context/country_facts.yaml")
QUAL_DIR        = Path("qualitative/countries")

# ── Constants ──────────────────────────────────────────────────────────────────

# PILLAR_DEFS and WEIGHT_PRESETS imported from asi.core.constants
METHODS = ["equal", "pca", "bod", "entropy", "geometric", "custom"]
METHOD_LABELS = {
    "equal":     "Equal Weights",
    "pca":       "PCA Weights",
    "bod":       "Benefit of Doubt",
    "entropy":   "Entropy Weights",
    "geometric": "Geometric Mean",
    "custom":    "Custom Weights",
}
# ISLAND_SET imported from asi.core.constants — do not redefine here.

TL_GREEN  = 65
TL_YELLOW = 35

BRAND       = "#1B3A6B"
BRAND_LIGHT = "#2E6DB4"
SCORE_CS    = [[0.0,"#c0392b"],[0.35,"#e67e22"],[0.65,"#f1c40f"],[1.0,"#2ecc71"]]

SLAVE_TRADE_COLORS = {
    "none": "#27ae60", "low": "#95a5a6", "medium": "#e67e22",
    "high": "#c0392b", "very_high": "#8e44ad",
}
COLONIAL_TYPE_COLORS = {
    "settler": "#c0392b", "extractive": "#e67e22", "plantation": "#8e44ad",
    "protectorate": "#3498db", "never_colonized": "#27ae60",
}

EQUAL_WEIGHTS = {p: round(1/7, 6) for p in PILLAR_DEFS}

# ── Data loading ───────────────────────────────────────────────────────────────

def _load():
    if not RESULTS_JSON.exists():
        print("ERROR: run 06_qualitative.py first"); sys.exit(1)
    with open(RESULTS_JSON, encoding="utf-8") as f:
        bundle = json.load(f)
    if ROBUSTNESS_JSON.exists():
        with open(ROBUSTNESS_JSON, encoding="utf-8") as f:
            rob = json.load(f)
    else:
        rob = {}
    if AUDIT_JSON.exists():
        with open(AUDIT_JSON, encoding="utf-8") as f:
            audit = json.load(f)
    else:
        audit = {}

    ind_meta = {}
    for path in sorted(IND_DIR.glob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue
        for ind in data:
            vn = ind["variable_name"]
            if vn not in ind_meta:
                ind_meta[vn] = dict(ind)
            else:
                ind_meta[vn]["pillars"] = list(
                    set(ind_meta[vn]["pillars"]) | set(ind.get("pillars", []))
                )

    raw_wide = norm_pivot = None
    norm_bounds = {}
    if CLEAN_FILE.exists():
        raw_wide = pd.read_excel(CLEAN_FILE, sheet_name="clean_data").set_index("iso3")
    if NORM_FILE.exists():
        ndf = pd.read_excel(NORM_FILE, sheet_name="norm_data")
        norm_pivot = ndf.pivot(index="iso3", columns="variable_name", values="norm_score")
        bdf = pd.read_excel(NORM_FILE, sheet_name="norm_bounds")
        norm_bounds = bdf.set_index("variable_name").to_dict("index")

    colonial = {}
    if COLONIAL_FILE.exists():
        with open(COLONIAL_FILE, encoding="utf-8") as f:
            colonial = yaml.safe_load(f) or {}

    country_facts = {}
    if FACTS_FILE.exists():
        with open(FACTS_FILE, encoding="utf-8") as f:
            country_facts = yaml.safe_load(f) or {}

    qual_notes = {}
    if QUAL_DIR.exists():
        for p in QUAL_DIR.glob("*.yaml"):
            iso3 = p.stem.upper()
            try:
                with open(p, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data:
                    qual_notes[iso3] = data
            except Exception:
                pass

    # Load per-method pillar weights from 04_scores.xlsx "Method Weights" sheet.
    # Used by fig_radar to scale axes when the scoring method changes.
    method_weights = {}
    scores_xlsx = Path("data/04_scores.xlsx")
    if scores_xlsx.exists():
        try:
            mw_df = pd.read_excel(scores_xlsx, sheet_name="Method Weights")
            col_map = {
                "Equal Weights":   "equal",
                "PCA Weights":     "pca",
                "Entropy Weights": "entropy",
                "Geometric Mean":  "geometric",
            }
            for col, method in col_map.items():
                if col in mw_df.columns and "Pillar Code" in mw_df.columns:
                    method_weights[method] = dict(zip(mw_df["Pillar Code"], mw_df[col].astype(float)))
        except Exception:
            pass

    return bundle, rob, audit, ind_meta, raw_wide, norm_pivot, norm_bounds, colonial, country_facts, qual_notes, method_weights


bundle, rob, audit, ind_meta, raw_wide, norm_pivot, norm_bounds, COLONIAL, COUNTRY_FACTS, QUAL_NOTES, METHOD_WEIGHTS = _load()

country_lookup = {c["iso3"]: c for c in bundle["countries"]}

# Displayed counts are derived from the bundle, never typed into a string.
# The header once claimed "36 Indicators" for weeks after the count changed;
# verify/contract.py now fails if a literal count reappears in the UI.
N_COUNTRIES = len(bundle["countries"])
N_PILLARS   = len(PILLAR_DEFS)
N_SCORING_INDICATORS = sum(
    1 for m in ind_meta.values() if m.get("role", "scoring") == "scoring"
)
countries_df = pd.DataFrame([{
    "iso3": c["iso3"], "name": c["name"], "region": c["region"],
    "island": c["island_state"],
    **{f"{m}_score": c["scores"].get(m) for m in ["equal","pca","bod","entropy","geometric"]},
    **{f"{m}_rank":  c["ranks"].get(m)  for m in ["equal","pca","bod","entropy","geometric"]},
    "fill_flag": c["data_quality"]["fill_flag"],
    "pct_real":  round(c["data_quality"]["pct_real"] * 100, 1),
} for c in bundle["countries"]])

# ── Custom score computation ───────────────────────────────────────────────────

def compute_custom_scores(weights: dict) -> dict:
    """Compute composite score for every country using caller-supplied pillar weights.
    weights: {pillar_id: float} — does NOT need to pre-sum to 1 (auto-normalised).
    Returns {iso3: score_or_None}.
    """
    pillars = list(PILLAR_DEFS.keys())
    w_arr   = np.array([weights.get(p, 1/7) for p in pillars], dtype=float)
    total_w = w_arr.sum()
    if total_w == 0:
        w_arr = np.ones(len(pillars)) / len(pillars)
    else:
        w_arr = w_arr / total_w

    scores = {}
    for c in bundle["countries"]:
        ps   = c["pillar_scores"]
        vals = np.array([ps.get(p) for p in pillars], dtype=object)
        mask = np.array([v is not None and not (isinstance(v, float) and math.isnan(v))
                         for v in vals])
        if not mask.any():
            scores[c["iso3"]] = None
        else:
            v_valid = vals[mask].astype(float)
            w_valid = w_arr[mask]
            w_valid = w_valid / w_valid.sum()
            scores[c["iso3"]] = float(np.dot(w_valid, v_valid))
    return scores


def _enrich_df_custom(weights: dict) -> pd.DataFrame:
    """Add custom_score and custom_rank columns to a copy of countries_df."""
    df = countries_df.copy()
    cscores = compute_custom_scores(weights)
    df["custom_score"] = df["iso3"].map(cscores)
    df["custom_rank"]  = df["custom_score"].rank(ascending=False, method="min",
                                                   na_option="bottom").astype("Int64")
    return df

# ── UI helpers ─────────────────────────────────────────────────────────────────

def traffic_light(score, size=16):
    if score is None:
        return html.Span("-", style={"color": "#aaa"})
    color = "#27ae60" if score >= TL_GREEN else "#e67e22" if score >= TL_YELLOW else "#c0392b"
    label = "Stable" if score >= TL_GREEN else "Moderate" if score >= TL_YELLOW else "Fragile"
    return html.Span(title=f"{label} ({score:.1f})", style={
        "display": "inline-block", "width": f"{size}px", "height": f"{size}px",
        "borderRadius": "50%", "background": color,
        "border": "2px solid rgba(0,0,0,0.12)", "flexShrink": "0",
    })


def stat_card(label, value, sub=None, color=BRAND):
    return html.Div([
        html.Div(str(value), style={"fontSize": "24px", "fontWeight": "700",
                                    "color": color, "lineHeight": "1.1"}),
        html.Div(label, style={"fontSize": "10px", "color": "#777", "marginTop": "2px"}),
        html.Div(sub, style={"fontSize": "9px", "color": "#bbb"}) if sub else None,
    ], style={"background": "#f8f9fa", "borderRadius": "8px", "padding": "10px 14px",
              "border": "1px solid #e4e4e4", "textAlign": "center", "minWidth": "80px"})


def fill_badge(flag):
    c = {"Excellent": "#27ae60", "Good": "#2ecc71", "Moderate": "#e67e22", "Caution": "#c0392b"}
    clr = c.get(flag, "#aaa")
    return html.Span(flag, style={"background": clr + "22", "color": clr,
                                   "fontWeight": "700", "fontSize": "10px",
                                   "padding": "2px 8px", "borderRadius": "4px"})


def breadcrumb(steps):
    """
    steps = list of (label, target_level_or_None).
    Last step (or target=None) is the current page — rendered as plain text.
    All other steps are clickable buttons using pattern-matching IDs.
    """
    items = []
    for i, (label, target) in enumerate(steps):
        if i == len(steps) - 1 or target is None:
            items.append(html.Span(label, style={
                "color": BRAND, "fontWeight": "600", "fontSize": "12px"}))
        else:
            items.append(html.Button(label,
                                      id={"type": "breadcrumb", "index": target},
                                      n_clicks=0, style={
                                          "background": "none", "border": "none",
                                          "color": BRAND_LIGHT, "cursor": "pointer",
                                          "fontSize": "12px", "padding": "0",
                                          "textDecoration": "underline",
                                          "fontWeight": "600",
                                      }))
        if i < len(steps) - 1:
            items.append(html.Span(" › ", style={"color": "#bbb", "margin": "0 5px",
                                                   "fontSize": "13px"}))
    return html.Div(items, style={"padding": "4px 0 10px", "userSelect": "none"})

# ── Figures ────────────────────────────────────────────────────────────────────

def fig_choropleth(method="equal", exclude_islands=False, custom_weights=None):
    if method == "custom" and custom_weights:
        df = _enrich_df_custom(custom_weights)
        sc, rc = "custom_score", "custom_rank"
    else:
        df = countries_df.copy()
        sc, rc = f"{method}_score", f"{method}_rank"
    if exclude_islands:
        df = df[~df["iso3"].isin(ISLAND_SET)].copy()
    df["hover"] = df.apply(lambda r: (
        f"<b>{r['name']}{'  [island]' if r['island'] else ''}</b><br>"
        f"Score: {r[sc]:.1f} | Rank #{int(r[rc])}<br>"
        f"Data quality: {r['fill_flag']}"
        if pd.notna(r[sc]) else f"<b>{r['name']}</b><br>Score: N/A"
    ), axis=1)
    fig = px.choropleth(df, locations="iso3", color=sc,
                        color_continuous_scale=SCORE_CS, range_color=[0, 100],
                        scope="africa", custom_data=["hover"],
                        labels={sc: "Score"})
    fig.update_traces(hovertemplate="%{customdata[0]}<extra></extra>")
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title="Score", tickvals=[0, 35, 65, 100],
                                ticktext=["0 Fragile", "35", "65", "100 Stable"], len=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)", showframe=False,
                 showcoastlines=True, coastlinecolor="#ccc",
                 showland=True, landcolor="#f5f5f5",
                 showocean=True, oceancolor="#e8f4f8"),
    )
    return fig


def fig_radar(iso3, method="geometric", custom_weights=None):
    """
    Radar chart of pillar scores.
    Each axis is scaled by (method_weight × n_pillars) so the polygon shape
    reflects both country performance and how the selected method weights
    each pillar. Equal weights → scale=1.0 on every axis (unchanged shape).
    PCA/entropy → high-weight pillars stretch outward, low-weight ones shrink.
    Custom → user's sliders drive the shape in real time.
    BoD → per-country weights are not saved; falls back to unscaled display.
    """
    c       = country_lookup.get(iso3, {})
    ps      = c.get("pillar_scores", {})
    pillars = list(PILLAR_DEFS.keys())
    labels  = [PILLAR_DEFS[p] for p in pillars]
    n       = len(pillars)

    # ── resolve weights for this method ──────────────────────────────────────
    if method == "custom" and custom_weights:
        raw   = {p: float(custom_weights.get(p, 1/n)) for p in pillars}
        total = sum(raw.values()) or 1
        w     = {p: raw[p] / total for p in pillars}
        note  = "axis = score × custom weight (normalised)"
    elif method == "bod":
        w    = {p: 1/n for p in pillars}
        note = "BoD: per-country optimal weights not saved — showing raw pillar scores"
    else:
        fallback = {p: 1/n for p in pillars}
        w        = METHOD_WEIGHTS.get(method, fallback)
        if not w:
            w = fallback
        note = "axis = score × relative method weight  (equal weight → no change)"

    scale = {p: w.get(p, 1/n) * n for p in pillars}

    # ── country values ────────────────────────────────────────────────────────
    vals = [(ps.get(p) or 0) * scale[p] for p in pillars]

    # ── continental average (same weight scaling) ─────────────────────────────
    avgs = []
    for p in pillars:
        all_s = [cc["pillar_scores"].get(p) for cc in bundle["countries"]
                 if cc["pillar_scores"].get(p) is not None]
        raw_avg = float(np.mean(all_s)) if all_s else 0
        avgs.append(raw_avg * scale[p])

    max_scale    = max(scale.values())
    axis_max     = max(100, round(100 * max_scale + 5, -1))
    vc = vals + [vals[0]]; lc = labels + [labels[0]]; ac = avgs + [avgs[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=ac, theta=lc, fill="toself", name="Continental avg",
        line=dict(color="#aaa", dash="dot"),
        fillcolor="rgba(170,170,170,0.08)"))
    fig.add_trace(go.Scatterpolar(
        r=vc, theta=lc, fill="toself", name=c.get("name", iso3),
        line=dict(color=BRAND_LIGHT, width=2),
        fillcolor="rgba(46,109,180,0.15)"))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, axis_max],
                                   tickfont=dict(size=9))),
        showlegend=True, legend=dict(orientation="h", y=-0.20),
        margin=dict(l=30, r=30, t=30, b=55),
        paper_bgcolor="rgba(0,0,0,0)", height=340,
        annotations=[dict(
            text=note, x=0.5, y=-0.18, xref="paper", yref="paper",
            showarrow=False, font=dict(size=9, color="#aaa"),
        )],
    )
    return fig


def fig_method_bars(iso3):
    c = country_lookup.get(iso3, {})
    methods_disp = ["equal", "pca", "bod", "entropy", "geometric"]
    fig = go.Figure(go.Bar(
        x=[METHOD_LABELS[m] for m in methods_disp],
        y=[c["scores"].get(m) for m in methods_disp],
        marker_color=[BRAND_LIGHT, "#8e44ad", "#e67e22", "#27ae60", "#c0392b"],
        text=[f"{c['scores'].get(m):.1f} (#{c['ranks'].get(m)})"
              if c["scores"].get(m) is not None else "N/A" for m in methods_disp],
        textposition="outside",
    ))
    fig.update_layout(yaxis=dict(range=[0, 115], title="Score (0-100)"), height=220,
                      margin=dict(l=10, r=10, t=10, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    fig.add_hline(y=50, line_dash="dot", line_color="#ddd", line_width=1)
    return fig


def fig_indicator_bars(iso3, pillar_id):
    c = country_lookup.get(iso3, {})
    vars_list = bundle["pillars"].get(pillar_id, {}).get("indicators", [])
    names, scores, colors, labels, hovers = [], [], [], [], []
    for var in vars_list:
        idata = c.get("indicators", {}).get(var, {})
        imeta = ind_meta.get(var, {})
        score = idata.get("score")
        polarity = imeta.get("polarity", "positive")

        # Raw value from clean data
        raw = None
        if raw_wide is not None and var in raw_wide.columns and iso3 in raw_wide.index:
            v = raw_wide.loc[iso3, var]
            raw = None if (isinstance(v, float) and math.isnan(v)) else v

        # Format raw for label
        if raw is not None:
            av = abs(raw)
            if av >= 10000:
                raw_str = f"{raw:,.0f}"
            elif av >= 100:
                raw_str = f"{raw:,.1f}"
            elif av >= 1:
                raw_str = f"{raw:.2f}"
            elif av >= 0.001:
                raw_str = f"{raw:.4f}"
            else:
                raw_str = f"{raw:.4g}"
        else:
            raw_str = "—"

        # Goodness rank for this indicator
        rank_str = ""
        if raw_wide is not None and var in raw_wide.columns and raw is not None:
            col_vals = raw_wide[var].dropna()
            if iso3 in col_vals.index:
                asc = (polarity == "negative")
                rv = int(col_vals.rank(ascending=asc, method="min").loc[iso3])
                rank_str = f" | #{rv}/{int(col_vals.shape[0])}"

        names.append((imeta.get("display_name") or var)[:55])
        scores.append(score if score is not None else 0)
        colors.append("#e67e22" if idata.get("filled") else BRAND_LIGHT)
        score_str = f"{score:.1f}" if score is not None else "—"
        rank_clean = rank_str.strip(" | ") if rank_str else "—"
        labels.append(f"{raw_str}{rank_str}")
        hovers.append(
            f"{imeta.get('display_name', var)}"
            f"<br>Raw value: {raw_str}"
            f"<br>Continental rank: {rank_clean}"
            f"<br>Score (0–100): {score_str}"
        )

    if not names:
        return go.Figure()
    fig = go.Figure(go.Bar(
        x=scores, y=names, orientation="h",
        marker_color=colors,
        text=labels, textposition="outside",
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hovers,
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 120], title="Score (0-100) — bar length only; labels show raw value & rank"),
        yaxis=dict(autorange="reversed"),
        height=max(260, len(names) * 65),
        margin=dict(l=10, r=160, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
    )
    fig.add_vline(x=TL_YELLOW, line_dash="dot", line_color="#e67e22", line_width=1)
    fig.add_vline(x=TL_GREEN,  line_dash="dot", line_color="#27ae60", line_width=1)
    return fig


def fig_cross_country(var, highlight_iso3=None):
    if norm_pivot is None or var not in norm_pivot.columns:
        return go.Figure()
    data = norm_pivot[var].dropna().sort_values()
    colors = ["#c0392b" if iso3 == highlight_iso3
              else "#9b59b6" if iso3 in ISLAND_SET
              else "#3498db" for iso3 in data.index]
    names = [country_lookup.get(iso3, {}).get("name", iso3) for iso3 in data.index]
    fig = go.Figure(go.Bar(x=data.values, y=names, orientation="h",
                            marker_color=colors,
                            hovertemplate="%{y}: %{x:.1f}<extra></extra>"))
    fig.update_layout(xaxis=dict(range=[0, 110], title="Score (0-100)"),
                      yaxis=dict(tickfont=dict(size=9)),
                      height=max(380, len(data) * 14),
                      margin=dict(l=10, r=10, t=10, b=20),
                      paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    return fig


def fig_pillar_heatmap():
    """
    Lower-triangle Spearman correlation matrix — best-practice layout.

    Design choices:
    - RdBu_r: industry standard diverging scale (red = positive, blue = negative,
      white = zero). Used by seaborn, R corrplot, OECD publications.
    - Lower triangle only: upper triangle is redundant by symmetry; masking it
      reduces visual noise and lets the reader focus on unique pairs.
    - Signed annotations (+0.82, -0.34): sign is as important as magnitude.
    - xgap/ygap: thin white gutters separate cells, aiding readability.
    - Diagonal shown as 1.00 (confirms the scale) but visually muted via a
      near-white red — a perfect correlation is expected and uninteresting.
    """
    pillars = list(PILLAR_DEFS.keys())
    n       = len(pillars)

    data = {p: [c["pillar_scores"].get(p) for c in bundle["countries"]]
            for p in pillars}
    corr = pd.DataFrame(data).corr(method="spearman").round(2)

    short_labels = {
        "A": "A · Governance",   "B": "B · Economic",
        "C": "C · Social",       "D": "D · Health",
        "E": "E · Security",     "F": "F · Environment",
        "G": "G · Infrastructure",
    }
    axis_labels = [short_labels[p] for p in pillars]

    z_mat   = []
    txt_mat = []
    for i, p in enumerate(pillars):
        z_row, txt_row = [], []
        for j, q in enumerate(pillars):
            if j > i:
                z_row.append(float("nan"))
                txt_row.append("")
            else:
                v = float(corr.loc[p, q])
                z_row.append(v)
                txt_row.append("1.00" if i == j else f"{v:+.2f}")
        z_mat.append(z_row)
        txt_mat.append(txt_row)

    fig = go.Figure(go.Heatmap(
        z=z_mat, x=axis_labels, y=axis_labels,
        colorscale="RdBu_r",
        zmid=0, zmin=-1, zmax=1,
        text=txt_mat,
        texttemplate="%{text}",
        textfont={"size": 13},
        hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>"
                      "Spearman r = %{z:.3f}<extra></extra>",
        colorbar=dict(
            title=dict(text="Spearman r", side="right",
                       font=dict(size=11)),
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=["-1.0<br><i>strong<br>negative</i>",
                      "-0.5", "0", "+0.5",
                      "+1.0<br><i>strong<br>positive</i>"],
            len=0.75, thickness=18,
            outlinewidth=0,
        ),
        xgap=3, ygap=3,
    ))
    fig.update_layout(
        height=480,
        margin=dict(l=20, r=100, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickangle=-30, tickfont=dict(size=11),
                   side="bottom", showgrid=False),
        yaxis=dict(tickfont=dict(size=11), autorange="reversed",
                   showgrid=False),
    )
    return fig

# ── Colonial history panel ─────────────────────────────────────────────────────

def render_colonial_history(iso3):
    ch = COLONIAL.get(iso3)
    if not ch:
        return html.Div()

    years = ch.get("years_colonized", 0)
    start = ch.get("colonial_start")
    end   = ch.get("colonial_end")
    if years == 0:
        period = "Never formally colonized"
    elif start and end:
        period = f"{start}–{end} ({years} years)"
    else:
        period = f"{years} years"

    colonizers = [ch.get("primary_colonizer", "")]
    colonizers += [c for c in (ch.get("other_colonizers") or []) if c]
    colonizers  = [c for c in colonizers if c and c.lower() != "none"]

    resources = ch.get("resources_extracted") or []
    sources   = ch.get("sources") or []
    ctype     = (ch.get("colonial_type") or "").replace("_", " ").title()
    slave     = (ch.get("slave_trade") or "none").replace("_", " ").title()
    note      = (ch.get("colonial_note") or "").strip()
    # Strip YAML comment lines that sneak through
    note = "\n".join(l for l in note.splitlines() if not l.strip().startswith("#")).strip()

    ct_color = COLONIAL_TYPE_COLORS.get(ch.get("colonial_type", ""), "#999")
    st_color = SLAVE_TRADE_COLORS.get(ch.get("slave_trade", "none"), "#999")

    label_s = {"fontWeight": "700", "fontSize": "10px", "color": "#666",
               "minWidth": "130px", "display": "inline-block"}
    val_s   = {"fontSize": "10px", "color": "#333"}
    row_s   = {"marginBottom": "5px", "display": "flex", "alignItems": "flex-start"}

    meta_rows = [
        html.Div([html.Span("Colonizer(s):", style=label_s),
                  html.Span(", ".join(colonizers) if colonizers else "—", style=val_s)],
                 style=row_s),
        html.Div([html.Span("Colonial period:", style=label_s),
                  html.Span(period, style=val_s)], style=row_s),
        html.Div([html.Span("Type:", style=label_s),
                  html.Span(ctype, style={**val_s, "color": ct_color, "fontWeight": "600"})],
                 style=row_s),
        html.Div([html.Span("Slave trade exposure:", style=label_s),
                  html.Span(slave, style={**val_s, "color": st_color, "fontWeight": "600"})],
                 style=row_s),
        html.Div([html.Span("Resources extracted:", style=label_s),
                  html.Span(", ".join(resources) if resources else "—", style=val_s)],
                 style=row_s),
    ]

    return html.Div([
        html.H4("Historical Context",
                style={"fontSize": "11px", "fontWeight": "700", "color": "#666",
                       "margin": "16px 0 4px", "textTransform": "uppercase",
                       "letterSpacing": "0.07em"}),
        html.Div("Historical data only — not included in the stability score.",
                 style={"fontSize": "9px", "color": "#aaa", "marginBottom": "10px"}),
        html.Div([
            html.Div(meta_rows, style={"minWidth": "280px", "flexShrink": "0",
                                        "paddingRight": "20px"}),
            html.Div([
                html.P(note or "—",
                       style={"fontSize": "10px", "color": "#444", "lineHeight": "1.65",
                              "margin": "0 0 10px"}),
                html.Div([
                    html.Span("Further reading:",
                              style={"fontSize": "9px", "fontWeight": "700", "color": "#888"}),
                    html.Ul([html.Li(s, style={"fontSize": "9px", "color": "#888",
                                                "marginBottom": "2px"}) for s in sources],
                            style={"margin": "4px 0 0 12px", "padding": "0",
                                   "listStyleType": "disc"}),
                ]) if sources else None,
            ], style={"flex": "1"}),
        ], style={"display": "flex", "flexWrap": "wrap", "gap": "10px",
                  "padding": "12px 14px", "background": "#fafafa",
                  "border": "1px solid #e0d8f0", "borderRadius": "8px",
                  "borderLeft": f"4px solid {ct_color}"}),
    ])

# ── Qualitative notes panel ────────────────────────────────────────────────────

def render_qualitative_notes(iso3):
    qual = QUAL_NOTES.get(iso3, {})
    overview    = (qual.get("overview") or "").strip()
    recent      = (qual.get("recent_developments") or "").strip()
    hist        = (qual.get("historical_notes") or "").strip()
    strengths   = [s for s in (qual.get("strengths")       or []) if s and str(s).strip()]
    challenges  = [s for s in (qual.get("challenges")      or []) if s and str(s).strip()]
    sources     = [s for s in (qual.get("external_sources") or []) if s and str(s).strip()]
    updated     = qual.get("last_updated", "")
    has_content = any([overview, recent, hist, strengths, challenges])

    header = html.H4("Country Notes",
                     style={"fontSize": "12px", "fontWeight": "700", "color": "#555",
                            "margin": "20px 0 6px", "textTransform": "uppercase",
                            "letterSpacing": "0.07em"})
    edit_path = f"qualitative/countries/{iso3}.yaml"

    if not has_content:
        return html.Div([
            header,
            html.Div([
                html.P("No qualitative notes yet.",
                       style={"fontSize": "12px", "color": "#bbb",
                              "fontStyle": "italic", "margin": "0 0 4px"}),
                html.P(f"Edit: {edit_path}",
                       style={"fontSize": "10px", "color": "#ccc",
                              "fontFamily": "monospace", "margin": "0"}),
            ], style={"padding": "14px 18px", "background": "#fafafa",
                      "border": "1px dashed #e4e4e4", "borderRadius": "6px"}),
        ])

    children = [header]
    if updated:
        children.append(html.Div(f"Last updated: {updated}",
                                  style={"fontSize": "10px", "color": "#bbb",
                                         "marginBottom": "8px"}))
    sections = []
    if overview:
        sections.append(html.P(overview, style={"fontSize": "13px", "color": "#333",
                                                  "lineHeight": "1.7", "margin": "0"}))
    if recent:
        sections.append(html.Div([
            html.Div("Recent Developments",
                     style={"fontSize": "11px", "fontWeight": "700", "color": "#555",
                            "marginBottom": "4px"}),
            html.P(recent, style={"fontSize": "12px", "color": "#333",
                                   "lineHeight": "1.7", "margin": "0"}),
        ], style={"marginTop": "14px"}))
    col_items = []
    if strengths:
        col_items.append(html.Div([
            html.Div("Strengths", style={"fontSize": "11px", "fontWeight": "700",
                                          "color": "#27ae60", "marginBottom": "6px"}),
            html.Ul([html.Li(s, style={"fontSize": "12px", "color": "#333",
                                        "marginBottom": "4px", "lineHeight": "1.5"}) for s in strengths],
                    style={"margin": "0", "paddingLeft": "18px"}),
        ], style={"flex": "1", "minWidth": "200px"}))
    if challenges:
        col_items.append(html.Div([
            html.Div("Challenges", style={"fontSize": "11px", "fontWeight": "700",
                                           "color": "#c0392b", "marginBottom": "6px"}),
            html.Ul([html.Li(s, style={"fontSize": "12px", "color": "#333",
                                        "marginBottom": "4px", "lineHeight": "1.5"}) for s in challenges],
                    style={"margin": "0", "paddingLeft": "18px"}),
        ], style={"flex": "1", "minWidth": "200px"}))
    if col_items:
        sections.append(html.Div(col_items, style={"display": "flex", "gap": "24px",
                                                     "flexWrap": "wrap", "marginTop": "14px"}))
    if hist:
        sections.append(html.Div([
            html.Div("Historical Context",
                     style={"fontSize": "11px", "fontWeight": "700", "color": "#555",
                            "marginBottom": "6px"}),
            html.P(hist, style={"fontSize": "12px", "color": "#555",
                                 "fontStyle": "italic", "lineHeight": "1.75",
                                 "margin": "0", "maxWidth": "900px"}),
        ], style={"marginTop": "14px", "paddingTop": "12px",
                  "borderTop": "1px solid #e8e8e8"}))
    if sources:
        sections.append(html.Div([
            html.Div("Sources",
                     style={"fontSize": "10px", "fontWeight": "700", "color": "#999",
                            "marginBottom": "4px"}),
            html.Ul([html.Li(s, style={"fontSize": "10px", "color": "#999",
                                        "marginBottom": "3px"}) for s in sources],
                    style={"margin": "0", "paddingLeft": "16px",
                           "listStyleType": "disc"}),
        ], style={"marginTop": "12px", "paddingTop": "10px",
                  "borderTop": "1px solid #f0f0f0"}))
    children.append(html.Div(sections, style={
        "padding": "16px 20px", "background": "#fafafa",
        "border": "1px solid #e4e4e4", "borderRadius": "8px",
        "borderLeft": "4px solid #2E6DB4",
    }))
    return html.Div(children)

# ── Level renders ─────────────────────────────────────────────────────────────

def render_overview(method="equal", exclude_islands=False, custom_weights=None):
    if method == "custom" and custom_weights:
        df = _enrich_df_custom(custom_weights)
        sc, rc = "custom_score", "custom_rank"
    else:
        df = countries_df.copy()
        sc, rc = f"{method}_score", f"{method}_rank"

    df_all = df.copy()
    if exclude_islands:
        df_rank = df[~df["iso3"].isin(ISLAND_SET)].copy().sort_values(rc)
    else:
        df_rank = df.copy().sort_values(rc)

    top5 = df_rank.head(5)
    bot5 = df_rank.tail(5)
    n_green = (df_all[sc] >= TL_GREEN).sum()
    n_red   = (df_all[sc] < TL_YELLOW).sum()
    avg_s   = df_all[sc].mean()

    def mini_list(subset):
        return [html.Div([
            html.Span(f"#{int(r[rc])} ",
                      style={"color": "#aaa", "fontSize": "10px",
                             "minWidth": "28px", "display": "inline-block"}),
            html.Span(("[I] " if r["island"] else "") + r["name"],
                      style={"fontSize": "11px", "fontWeight": "600"}),
            html.Span(f"  {r[sc]:.1f}",
                      style={"color": BRAND_LIGHT, "fontSize": "11px",
                             "float": "right"}),
        ], style={"padding": "3px 0", "borderBottom": "1px solid #f5f5f5"})
        for _, r in subset.iterrows()]

    island_note = html.Div(
        "Island states excluded from rankings list. They still appear on the map.",
        style={"fontSize": "9px", "color": "#8e44ad", "padding": "4px 8px",
               "background": "#f5f0ff", "borderRadius": "4px", "marginBottom": "6px"}
    ) if exclude_islands else None

    return html.Div([
        html.Div([
            html.Div(
                f"Showing: {METHOD_LABELS.get(method, method)}  |  "
                f"{'Island states excluded from rankings' if exclude_islands else 'All 54 countries'}",
                style={"fontSize": "10px", "color": "#888", "fontStyle": "italic"},
            ),
            html.Span("[I] = island state  |  Green >= 65  |  Yellow 35-65  |  Red < 35",
                      style={"fontSize": "10px", "color": "#aaa"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "center", "padding": "8px 14px",
                  "background": "#f8f9fa", "borderBottom": "1px solid #e4e4e4"}),

        html.Div([
            stat_card("Continental avg", f"{avg_s:.1f}", sub="0-100 scale"),
            stat_card("Stable", int(n_green), sub="score >= 65", color="#27ae60"),
            stat_card("Moderate", int(54 - n_green - n_red), sub="score 35-65", color="#e67e22"),
            stat_card("Fragile", int(n_red), sub="score < 35", color="#c0392b"),
            stat_card("Pillars", 7),
            stat_card("Indicators", 32),
        ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap",
                  "padding": "10px 14px"}),

        html.Div([
            html.Div([
                island_note,
                html.H4("Most Stable", style={"fontSize": "11px", "color": "#27ae60",
                                               "fontWeight": "700", "margin": "0 0 6px"}),
                *mini_list(top5),
                html.H4("Most Fragile", style={"fontSize": "11px", "color": "#c0392b",
                                                "fontWeight": "700", "margin": "14px 0 6px"}),
                *mini_list(bot5),
                html.P("Click a country on the map to open its profile.",
                       style={"fontSize": "9px", "color": "#bbb", "marginTop": "12px"}),
            ], style={"width": "180px", "flexShrink": "0", "paddingRight": "10px"}),

            dcc.Graph(id="ov-map",
                      figure=fig_choropleth(method, exclude_islands, custom_weights),
                      config={"displayModeBar": False},
                      style={"flex": "1", "height": "490px"}),
        ], style={"display": "flex", "gap": "8px", "padding": "0 14px 12px",
                  "alignItems": "flex-start"}),

        html.Div([
            html.Div([
                html.H4("Pillar Correlation Matrix",
                        style={"fontSize": "13px", "fontWeight": "700",
                               "color": BRAND, "margin": "0 0 2px"}),
                html.P(
                    "Spearman rank correlation across 54 countries — lower triangle shown. "
                    "Red = pillars that move together; blue = inverse relationship; "
                    "white = independent. Strong positive correlations suggest pillar "
                    "overlap; strong negative correlations are rare and indicate "
                    "genuine trade-offs.",
                    style={"fontSize": "10px", "color": "#666", "margin": "0",
                           "maxWidth": "820px", "lineHeight": "1.5"},
                ),
            ], style={"marginBottom": "8px"}),
            dcc.Graph(figure=fig_pillar_heatmap(),
                      config={"displayModeBar": False},
                      style={"height": "500px"}),
        ], style={"padding": "14px 14px 18px",
                  "borderTop": "1px solid #eee",
                  "background": "#fafafa"}),
    ])


def render_country(iso3, method="geometric", custom_weights=None):
    c = country_lookup.get(iso3)
    if not c:
        return html.Div("Country not found.")
    name   = c["name"]
    region = c["region"]
    island = c["island_state"]
    dq     = c["data_quality"]
    band   = c["confidence_band"]
    peer   = c["peer_rank"]
    eq     = c["scores"].get("equal")
    eq_r   = c["ranks"].get("equal")

    # ── Pillar buttons ────────────────────────────────────────────────────────
    pillar_cards = []
    for p, pname in PILLAR_DEFS.items():
        ps = c["pillar_scores"].get(p)
        pr = c["pillar_ranks"].get(p)
        color = ("#27ae60" if (ps or 0) >= TL_GREEN
                 else "#e67e22" if (ps or 0) >= TL_YELLOW else "#c0392b")
        pillar_cards.append(html.Button([
            html.Div([traffic_light(ps, 13),
                      html.Span(f"  {p}", style={"fontWeight": "700", "fontSize": "12px",
                                                   "marginLeft": "3px"})],
                     style={"display": "flex", "alignItems": "center",
                            "marginBottom": "3px"}),
            html.Div(pname, style={"fontSize": "10px", "color": "#666",
                                    "marginBottom": "6px", "lineHeight": "1.3"}),
            html.Span(f"{ps:.1f}" if ps is not None else "—",
                      style={"fontSize": "22px", "fontWeight": "700", "color": color}),
            html.Span(f"  #{pr}" if pr else "",
                      style={"fontSize": "10px", "color": "#aaa", "marginLeft": "4px"}),
            html.Div("→ click to explore",
                     style={"fontSize": "9px", "color": BRAND_LIGHT, "marginTop": "6px",
                            "opacity": "0.7"}),
        ], id={"type": "pillar-btn", "index": p}, n_clicks=0,
            style={"background": "#fafafa", "border": f"2px solid {color}",
                   "borderRadius": "8px", "padding": "10px", "cursor": "pointer",
                   "textAlign": "left", "width": "calc(14.2% - 5px)",
                   "minWidth": "100px", "transition": "box-shadow 0.15s"}))

    # ── Quick facts panel ─────────────────────────────────────────────────────
    facts = COUNTRY_FACTS.get(iso3, {})

    def fact_chip(label, value, unit=""):
        return html.Div([
            html.Div(label, style={"fontSize": "9px", "color": "#999",
                                   "textTransform": "uppercase", "letterSpacing": "0.05em",
                                   "marginBottom": "2px"}),
            html.Div([
                html.Span(str(value), style={"fontSize": "15px", "fontWeight": "700",
                                              "color": "#333"}),
                html.Span(f" {unit}" if unit else "",
                          style={"fontSize": "10px", "color": "#888", "marginLeft": "2px"}),
            ]),
        ], style={"background": "#fff", "border": "1px solid #e8e8e8",
                  "borderRadius": "6px", "padding": "8px 12px",
                  "minWidth": "120px"})

    def raw_val(var):
        if raw_wide is not None and var in raw_wide.columns and iso3 in raw_wide.index:
            v = raw_wide.loc[iso3, var]
            return None if (isinstance(v, float) and math.isnan(v)) else v
        return None

    gdp_pc   = raw_val("gdp_pc_ppp")
    growth   = raw_val("gdp_growth_3yr_avg")
    gini_v   = raw_val("gini")
    literacy = raw_val("adult_literacy") or raw_val("youth_literacy")

    chips = []
    if facts.get("capital"):
        chips.append(fact_chip("Capital", facts["capital"]))
    if facts.get("population_m"):
        pop = facts["population_m"]
        chips.append(fact_chip("Population", f"{pop:,.1f}", "million (2023 est.)"))
    if facts.get("area_km2"):
        area = facts["area_km2"]
        chips.append(fact_chip("Area", f"{area:,.0f}", "km²"))
    if gdp_pc is not None:
        chips.append(fact_chip("GDP per capita (PPP)", f"${gdp_pc:,.0f}", "int'l $"))
    if growth is not None:
        chips.append(fact_chip("GDP growth (3yr avg)", f"{growth:+.1f}", "%"))
    if gini_v is not None:
        chips.append(fact_chip("Gini Index", f"{gini_v:.1f}", "/ 100"))
    if literacy is not None:
        chips.append(fact_chip("Adult Literacy", f"{literacy:.1f}", "%"))
    if facts.get("currency"):
        chips.append(fact_chip("Currency", facts["currency"]))

    resources_block = None
    if facts.get("resources"):
        resources_block = html.Div([
            html.Span("Key resources / exports: ",
                      style={"fontSize": "10px", "fontWeight": "700", "color": "#555"}),
            html.Span(", ".join(facts["resources"]),
                      style={"fontSize": "11px", "color": "#333"}),
        ], style={"marginTop": "8px"})

    languages_block = None
    if facts.get("languages"):
        languages_block = html.Div([
            html.Span("Official / national languages: ",
                      style={"fontSize": "10px", "fontWeight": "700", "color": "#555"}),
            html.Span(", ".join(facts["languages"]),
                      style={"fontSize": "11px", "color": "#333"}),
        ], style={"marginTop": "4px"})

    facts_section = html.Div([
        html.H4("Country Profile",
                style={"fontSize": "12px", "fontWeight": "700", "color": "#555",
                       "margin": "0 0 8px", "textTransform": "uppercase",
                       "letterSpacing": "0.07em"}),
        html.Div(chips, style={"display": "flex", "gap": "8px", "flexWrap": "wrap",
                               "marginBottom": "6px"}),
        resources_block,
        languages_block,
    ], style={"padding": "12px 14px", "background": "#fafafa",
              "border": "1px solid #e4e4e4", "borderRadius": "8px",
              "marginTop": "12px", "marginBottom": "4px"}) if (chips or facts) else None

    return html.Div([
        breadcrumb([("Overview", "overview"), (name, None)]),
        html.Div([
            html.Div([
                html.H2(("[Island State]  " if island else "") + name,
                        style={"margin": "0", "fontSize": "18px", "fontWeight": "700",
                               "color": BRAND}),
                html.Div(f"{region} Africa",
                         style={"fontSize": "11px", "color": "#888", "marginTop": "2px"}),
                html.Div([
                    html.Span("Data coverage: ",
                              style={"fontSize": "10px", "color": "#888"}),
                    fill_badge(dq.get("fill_flag", "Good")),
                    html.Span(f"  {dq.get('pct_real', 0)*100:.0f}% real observations",
                              style={"fontSize": "10px", "color": "#aaa",
                                     "marginLeft": "6px"}),
                ], style={"display": "flex", "alignItems": "center", "gap": "4px",
                          "marginTop": "4px"}),
                html.Div(
                    "Island state — geographic and demographic insularity structurally "
                    "advantage small island states on most indicators. "
                    "Peer comparisons with continental countries should be interpreted "
                    "cautiously.",
                    style={"fontSize": "10px", "color": "#8e44ad", "marginTop": "6px",
                           "padding": "4px 8px", "background": "#f5f0ff",
                           "borderRadius": "4px", "maxWidth": "380px"}
                ) if island else None,
            ]),
            html.Div([
                stat_card("Equal Score", f"{eq:.1f}" if eq else "-"),
                stat_card("Continental Rank", f"#{eq_r}" if eq_r else "-"),
                stat_card(f"Rank in {region}",
                          f"#{peer.get('rank_in_region','-')} of "
                          f"{peer.get('n_in_region','-')}"),
                html.Div([
                    html.Div(f"{band.get('low','-')} to {band.get('high','-')}",
                             style={"fontSize": "18px", "fontWeight": "700",
                                    "color": "#8e44ad", "lineHeight": "1.1"}),
                    html.Div("Confidence band",
                             style={"fontSize": "9px", "color": "#888",
                                    "marginTop": "1px"}),
                    html.Div("Wider = more estimated data",
                             style={"fontSize": "8px", "color": "#bbb"}),
                ], style={"background": "#f8f9fa", "borderRadius": "8px",
                          "padding": "10px 14px", "border": "1px solid #e4e4e4",
                          "textAlign": "center", "minWidth": "110px"}),
            ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "flex-start", "gap": "14px", "flexWrap": "wrap",
                  "marginBottom": "10px", "paddingBottom": "10px",
                  "borderBottom": "1px solid #eee"}),

        html.Div([
            html.P("7 Pillars — click any to drill down into indicator-level data",
                   style={"fontSize": "10px", "color": "#aaa", "margin": "0 0 8px"}),
            html.Div(pillar_cards,
                     style={"display": "flex", "gap": "6px", "flexWrap": "wrap"}),
        ], style={"marginBottom": "12px"}),

        html.Div([
            html.Div([
                html.H4("Pillar Profile vs Continental Average",
                        style={"fontSize": "11px", "fontWeight": "600",
                               "margin": "0 0 4px"}),
                dcc.Graph(id="cp-radar", figure=fig_radar(iso3, method, custom_weights),
                          config={"displayModeBar": False}),
            ], style={"flex": "1", "minWidth": "260px"}),
            html.Div([
                html.H4("Score by Weighting Method",
                        style={"fontSize": "11px", "fontWeight": "600",
                               "margin": "0 0 4px"}),
                html.P("See Methodology tab for method explanations.",
                       style={"fontSize": "9px", "color": "#888", "margin": "0 0 4px"}),
                dcc.Graph(id="cp-methods", figure=fig_method_bars(iso3),
                          config={"displayModeBar": False}),
            ], style={"flex": "1", "minWidth": "260px"}),
        ], style={"display": "flex", "gap": "14px", "flexWrap": "wrap",
                  "borderBottom": "1px solid #eee", "paddingBottom": "12px",
                  "marginBottom": "4px"}),

        facts_section,
        render_colonial_history(iso3),
        render_qualitative_notes(iso3),

    ], style={"padding": "10px 14px", "overflowY": "auto"})


def render_pillar(iso3, pillar_id):
    c      = country_lookup.get(iso3, {})
    pname  = PILLAR_DEFS.get(pillar_id, pillar_id)
    ps     = c.get("pillar_scores", {}).get(pillar_id)
    pr     = c.get("pillar_ranks",  {}).get(pillar_id)
    pb     = bundle["pillars"].get(pillar_id, {})
    justif = (pb.get("justification") or
              f"Aggregates indicators related to {pname.lower()}.")
    vars_list = pb.get("indicators", [])

    ind_rows = []
    raw_table_rows = []
    for var in vars_list:
        idata = c.get("indicators", {}).get(var, {})
        imeta = ind_meta.get(var, {})
        score = idata.get("score")
        raw   = None
        if raw_wide is not None and var in raw_wide.columns and iso3 in raw_wide.index:
            v = raw_wide.loc[iso3, var]
            raw = None if (isinstance(v, float) and math.isnan(v)) else v
        polarity = imeta.get("polarity", "positive")

        # Format raw value for display
        if raw is not None:
            av = abs(raw)
            if av >= 10000:
                raw_display = f"{raw:,.0f}"
            elif av >= 100:
                raw_display = f"{raw:,.1f}"
            elif av >= 1:
                raw_display = f"{raw:.3f}"
            elif av >= 0.001:
                raw_display = f"{raw:.4f}"
            else:
                raw_display = f"{raw:.4g}"
        else:
            raw_display = "—"

        # Goodness rank: #1 = best-performing country regardless of polarity
        # positive polarity → highest raw = best → rank descending
        # negative polarity → lowest raw = best  → rank ascending
        rank_str = "—"
        n_valid  = "—"
        if raw_wide is not None and var in raw_wide.columns:
            col_vals = raw_wide[var].dropna()
            n_valid  = str(int(col_vals.shape[0]))
            if raw is not None and iso3 in col_vals.index:
                asc = (polarity == "negative")
                rank_val = int(col_vals.rank(ascending=asc, method="min").loc[iso3])
                rank_str = f"#{rank_val} / {n_valid}"

        ind_rows.append(dict(var=var, name=imeta.get("display_name", var),
                             score=score, raw=raw, raw_display=raw_display,
                             rank_str=rank_str,
                             polarity=polarity, filled=idata.get("filled", False),
                             justif=imeta.get("justification", "")[:130]))

        raw_table_rows.append({
            "Indicator":      (imeta.get("display_name", var) or var),
            "Raw Value":      raw_display,
            "Rank (best=#1)": rank_str,
            "Valid n":        n_valid,
            "Score (0-100)":  f"{score:.1f}" if score is not None else "—",
            "Direction":      "↑ higher = better" if polarity == "positive" else "↓ lower = better",
            "Data":           "Estimated" if idata.get("filled") else "Real",
        })

    # ── Missing-data banner ────────────────────────────────────────────────────
    missing = [r for r in ind_rows if r["score"] is None and r["raw"] is None]
    estimated = [r for r in ind_rows if r["filled"] and r["score"] is not None]

    missing_banner = None
    if missing or estimated:
        items = []
        for r in missing:
            items.append(html.Li([
                html.Span("✕ No data: ", style={"color": "#c0392b", "fontWeight": "700",
                                                  "fontSize": "10px"}),
                html.Span(r["name"], style={"fontSize": "10px", "color": "#555"}),
                html.Span(" — not available for this country in the source database.",
                          style={"fontSize": "9px", "color": "#999"}),
            ], style={"marginBottom": "3px", "listStyle": "none"}))
        for r in estimated:
            items.append(html.Li([
                html.Span("~ Estimated: ", style={"color": "#e67e22", "fontWeight": "700",
                                                    "fontSize": "10px"}),
                html.Span(r["name"], style={"fontSize": "10px", "color": "#555"}),
                html.Span(" — filled by regional average (5-yr lookback).",
                          style={"fontSize": "9px", "color": "#999"}),
            ], style={"marginBottom": "3px", "listStyle": "none"}))

        missing_banner = html.Div([
            html.Div([
                html.Span("⚠ Data gaps in this pillar for ",
                          style={"fontWeight": "700", "color": "#b07800",
                                 "fontSize": "11px"}),
                html.Span(c.get("name", iso3),
                          style={"fontWeight": "700", "color": "#b07800",
                                 "fontSize": "11px"}),
            ], style={"marginBottom": "6px"}),
            html.Ul(items, style={"margin": "0", "padding": "0"}),
        ], style={"background": "#fffbea", "border": "1px solid #f0d060",
                  "borderLeft": "4px solid #e6ac00", "borderRadius": "6px",
                  "padding": "10px 14px", "marginBottom": "10px"})

    ind_children = []
    for r in ind_rows:
        ind_children.append(html.Div([
            html.Div([
                html.Div([
                    traffic_light(r["score"], 13),
                    html.Span(" " + r["name"][:60],
                              style={"fontSize": "11px", "marginLeft": "4px",
                                     "color": BRAND_LIGHT, "cursor": "pointer"}),
                    html.Span(" (estimated)" if r["filled"] else "",
                              style={"fontSize": "9px", "color": "#e67e22",
                                     "marginLeft": "4px"}),
                    html.Span(" no data" if r["score"] is None else "",
                              style={"fontSize": "9px", "color": "#c0392b",
                                     "marginLeft": "4px", "fontWeight": "700"}),
                ], style={"display": "flex", "alignItems": "center",
                          "marginBottom": "2px"}),
                html.Div(r["justif"],
                         style={"fontSize": "9px", "color": "#888",
                                "paddingLeft": "21px", "lineHeight": "1.3"}),
            ], style={"flex": "1"}),
            html.Div([
                html.Div(r["raw_display"],
                         style={"fontSize": "20px", "fontWeight": "700",
                                "textAlign": "right", "color": "#222",
                                "letterSpacing": "-0.5px", "lineHeight": "1.1"}),
                html.Div("raw value",
                         style={"fontSize": "8px", "color": "#aaa",
                                "textAlign": "right", "marginBottom": "5px"}),
                html.Div(r["rank_str"],
                         style={"fontSize": "11px", "fontWeight": "700",
                                "textAlign": "right", "color": "#555"}),
                html.Div("continental rank",
                         style={"fontSize": "8px", "color": "#aaa",
                                "textAlign": "right"}),
            ], style={"minWidth": "70px", "textAlign": "right", "flexShrink": "0"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "flex-start", "padding": "7px 0",
                  "borderBottom": "1px solid #f5f5f5",
                  "opacity": "0.45" if r["score"] is None else "1"}))
        ind_children.append(html.Button(
            "Drill into this indicator >",
            id={"type": "ind-btn", "index": r["var"]}, n_clicks=0,
            style={"background": "none", "border": "none", "color": BRAND_LIGHT,
                   "fontSize": "9px", "cursor": "pointer",
                   "padding": "2px 0 6px 21px"}))
    ind_panel = html.Div(ind_children)

    # ── Descriptive indicators (role: descriptive in YAML) ─────────────────────
    # These provide additional context but are not used in the scoring pipeline.
    desc_rows = []
    for var, meta in sorted(ind_meta.items()):
        if meta.get("role") != "descriptive":
            continue
        if pillar_id not in meta.get("pillars", []):
            continue
        idata_d = c.get("indicators", {}).get(var, {})
        raw_d = None
        if raw_wide is not None and var in raw_wide.columns and iso3 in raw_wide.index:
            v = raw_wide.loc[iso3, var]
            raw_d = None if (isinstance(v, float) and math.isnan(v)) else v
        if raw_d is not None:
            av = abs(raw_d)
            if av >= 10000:
                disp_d = f"{raw_d:,.0f}"
            elif av >= 100:
                disp_d = f"{raw_d:,.1f}"
            elif av >= 1:
                disp_d = f"{raw_d:.3f}"
            elif av >= 0.001:
                disp_d = f"{raw_d:.4f}"
            else:
                disp_d = f"{raw_d:.4g}"
        else:
            disp_d = "—"
        pol_d = meta.get("polarity", "positive")
        rank_d = "—"
        if raw_wide is not None and var in raw_wide.columns and raw_d is not None:
            col_d = raw_wide[var].dropna()
            if iso3 in col_d.index:
                asc_d = (pol_d == "negative")
                rv_d = int(col_d.rank(ascending=asc_d, method="min").loc[iso3])
                rank_d = f"#{rv_d} / {int(col_d.shape[0])}"
        desc_rows.append(dict(
            name=meta.get("display_name", var),
            raw_display=disp_d, rank_str=rank_d,
            justif=meta.get("justification", "")[:130],
            filled=idata_d.get("filled", False),
        ))

    desc_panel = None
    if desc_rows:
        desc_children = []
        for dr in desc_rows:
            desc_children.append(html.Div([
                html.Div([
                    html.Span(dr["name"][:60],
                              style={"fontSize": "11px", "color": BRAND_LIGHT,
                                     "fontWeight": "600"}),
                    html.Span(" (estimated)" if dr["filled"] else "",
                              style={"fontSize": "9px", "color": "#e67e22",
                                     "marginLeft": "4px"}),
                    html.Div(dr["justif"],
                             style={"fontSize": "9px", "color": "#888",
                                    "marginTop": "2px", "lineHeight": "1.3"}),
                ], style={"flex": "1"}),
                html.Div([
                    html.Div(dr["raw_display"],
                             style={"fontSize": "18px", "fontWeight": "700",
                                    "textAlign": "right", "color": "#444",
                                    "lineHeight": "1.1"}),
                    html.Div("reference value",
                             style={"fontSize": "8px", "color": "#aaa",
                                    "textAlign": "right", "marginBottom": "4px"}),
                    html.Div(dr["rank_str"],
                             style={"fontSize": "11px", "fontWeight": "700",
                                    "textAlign": "right", "color": "#555"}),
                    html.Div("continental rank",
                             style={"fontSize": "8px", "color": "#aaa",
                                    "textAlign": "right"}),
                ], style={"minWidth": "100px", "flexShrink": "0"}),
            ], style={"display": "flex", "justifyContent": "space-between",
                      "alignItems": "flex-start", "padding": "7px 0",
                      "borderBottom": "1px solid #efefef"}))
        desc_panel = html.Div([
            html.H4("Descriptive Context",
                    style={"fontSize": "12px", "fontWeight": "700",
                           "margin": "0 0 4px", "color": BRAND}),
            html.P("Additional reference data — not used in the composite score.",
                   style={"fontSize": "9px", "color": "#888", "margin": "0 0 8px"}),
            html.Div(desc_children),
        ], style={"marginTop": "12px", "padding": "10px 14px",
                  "background": "#f8f9fa", "borderRadius": "6px",
                  "border": "1px solid #e8eaed",
                  "borderLeft": f"4px solid {BRAND_LIGHT}"})

    return html.Div([
        breadcrumb([("Overview", "overview"),
                    (c.get("name", iso3), "country"),
                    (f"{pillar_id}: {pname}", None)]),
        html.Div([
            html.Div([
                html.H2(f"Pillar {pillar_id}: {pname}",
                        style={"margin": "0", "fontSize": "17px",
                               "fontWeight": "700", "color": BRAND}),
                html.P(justif, style={"fontSize": "11px", "color": "#555",
                                      "marginTop": "6px", "maxWidth": "580px",
                                      "lineHeight": "1.5"}),
            ]),
            html.Div([
                stat_card("Pillar Score", f"{ps:.1f}" if ps is not None else "-"),
                stat_card("Global Rank", f"#{pr}" if pr is not None else "-"),
                stat_card("Indicators", len(vars_list)),
            ], style={"display": "flex", "gap": "8px"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "flex-start", "gap": "14px", "flexWrap": "wrap",
                  "marginBottom": "12px", "paddingBottom": "10px",
                  "borderBottom": "1px solid #eee"}),

        missing_banner,

        html.Div([
            html.Div([
                html.H4("Indicator Scores",
                        style={"fontSize": "11px", "fontWeight": "600",
                               "margin": "0 0 4px"}),
                html.P("Blue = real data  ·  Orange = estimated  ·  "
                       "Green/yellow/red lines = thresholds",
                       style={"fontSize": "9px", "color": "#888", "margin": "0 0 6px"}),
                dcc.Graph(figure=fig_indicator_bars(iso3, pillar_id),
                          config={"displayModeBar": False}),
            ], style={"flex": "1", "minWidth": "280px"}),
            html.Div([
                html.H4("Input Indicators — Raw Value & Rank",
                        style={"fontSize": "11px", "fontWeight": "600",
                               "margin": "0 0 2px"}),
                html.P("Traffic light reflects normalized score used in composite.  "
                       "Numbers show actual measurement & continental rank.",
                       style={"fontSize": "9px", "color": "#888",
                              "margin": "0 0 8px", "lineHeight": "1.4"}),
                html.Div(ind_panel, style={"maxHeight": "420px", "overflowY": "auto"}),
            ], style={"flex": "1", "minWidth": "260px"}),
        ], style={"display": "flex", "gap": "14px", "flexWrap": "wrap",
                  "marginBottom": "16px"}),

        desc_panel,

        html.Div([
            html.H4(f"Raw Data — {c.get('name', iso3)} vs {N_COUNTRIES} Countries",
                    style={"fontSize": "13px", "fontWeight": "700",
                           "color": BRAND, "margin": "0 0 4px"}),
            html.P(
                "Raw Value = actual measurement before normalisation (e.g. real GDP, life expectancy in years).  "
                "Rank (best=#1) = goodness rank — #1 always means best-performing country for this indicator "
                "(highest value for positive indicators; lowest value for negative indicators).  "
                "Click column headers to sort.  Type in filter boxes to search.",
                style={"fontSize": "10px", "color": "#666", "margin": "0 0 8px",
                       "lineHeight": "1.5", "maxWidth": "900px"}),
            dash_table.DataTable(
                data=raw_table_rows,
                columns=[{"name": col, "id": col} for col in raw_table_rows[0].keys()]
                        if raw_table_rows else [],
                sort_action="native",
                filter_action="native",
                filter_options={"case": "insensitive", "placeholder_text": "filter…"},
                style_cell={"textAlign": "left", "fontSize": "12px",
                            "padding": "7px 12px", "whiteSpace": "normal"},
                style_cell_conditional=[
                    {"if": {"column_id": "Indicator"},      "minWidth": "260px", "width": "260px"},
                    {"if": {"column_id": "Raw Value"},      "textAlign": "right", "minWidth": "110px"},
                    {"if": {"column_id": "Rank (best=#1)"}, "textAlign": "center", "minWidth": "110px"},
                    {"if": {"column_id": "Valid n"},        "textAlign": "center", "minWidth": "70px"},
                    {"if": {"column_id": "Score (0-100)"},  "textAlign": "center", "minWidth": "100px"},
                    {"if": {"column_id": "Direction"},      "minWidth": "145px", "color": "#777"},
                    {"if": {"column_id": "Data"},           "textAlign": "center", "minWidth": "80px"},
                ],
                style_header={"backgroundColor": BRAND, "color": "white",
                              "fontWeight": "bold", "fontSize": "11px",
                              "cursor": "pointer", "padding": "8px 12px"},
                style_filter={"backgroundColor": "#f0f4f8", "fontSize": "10px",
                              "border": "1px solid #d0d8e4"},
                style_data_conditional=[
                    {"if": {"filter_query": '{Data} = "Estimated"'},
                     "backgroundColor": "#fff8f0", "color": "#9a6700"},
                    {"if": {"filter_query": '{Rank (best=#1)} contains "#1 "'},
                     "fontWeight": "700"},
                ],
                style_table={"overflowX": "auto"},
                page_size=20,
            ),
        ], style={"borderTop": "1px solid #eee", "paddingTop": "14px"}),
    ], style={"padding": "10px 14px"})


def render_indicator(iso3, pillar_id, var):
    c      = country_lookup.get(iso3, {})
    imeta  = ind_meta.get(var, {})
    idata  = c.get("indicators", {}).get(var, {})
    score  = idata.get("score")
    filled = idata.get("filled", False)

    raw = None
    if raw_wide is not None and var in raw_wide.columns and iso3 in raw_wide.index:
        v = raw_wide.loc[iso3, var]
        raw = None if (isinstance(v, float) and math.isnan(v)) else v

    polarity      = imeta.get("polarity", "positive")
    log_transform = bool(imeta.get("log_transform", False))
    bnds          = norm_bounds.get(var, {})

    steps = []
    if raw is not None:
        steps.append(("1  Raw value", f"{raw:.4f}",
                      "Observed value from source database (most recent year available)."))
        sv = raw
        if log_transform:
            sv = math.log1p(max(0, sv))
            steps.append(("2  Log1p transform",
                          f"log(1 + {raw:.4f}) = {sv:.4f}",
                          "Applied to right-skewed indicators to compress outliers. "
                          "(OECD Handbook on Composite Indicators, 2008, sec. 6.2)"))
        else:
            steps.append(("2  Log transform", "Not applied for this indicator", ""))

        x_min = bnds.get("log_min" if log_transform else "raw_min", 0)
        x_max = bnds.get("log_max" if log_transform else "raw_max", 1)
        if x_max != x_min:
            if polarity == "negative":
                norm = (x_max - sv) / (x_max - x_min) * 100
                formula = (f"({x_max:.4f} - {sv:.4f}) / "
                           f"({x_max:.4f} - {x_min:.4f}) x 100 = {norm:.2f}")
            else:
                norm = (sv - x_min) / (x_max - x_min) * 100
                formula = (f"({sv:.4f} - {x_min:.4f}) / "
                           f"({x_max:.4f} - {x_min:.4f}) x 100 = {norm:.2f}")
            steps.append((f"3  Min-max normalization  (polarity = {polarity})",
                          formula,
                          ("Lower = higher score (worse indicator = higher fragility). "
                           if polarity == "negative" else
                           "Higher = higher score (better = more stable). ")
                          + f"Sample bounds: min={x_min:.4f}, max={x_max:.4f}. "
                          "Mapped to [0, 100] within 54 countries."))
        steps.append(("4  Data status",
                      "ESTIMATED — filled by pipeline" if filled else "REAL — observed data",
                      "Fill procedure: (1) 5-year lookback, (2) regional mean. "
                      "Confidence band is widened when data is estimated." if filled else
                      "Actual observed value from the source database."))
    else:
        steps.append(("Data unavailable", "No value found",
                      "Neither real nor estimated data available."))

    step_cards = [html.Div([
        html.Div(s[0], style={"fontSize": "10px", "fontWeight": "700",
                               "color": BRAND, "marginBottom": "3px"}),
        html.Div(s[1], style={"fontSize": "13px", "fontWeight": "600",
                               "color": "#333", "fontFamily": "monospace"}),
        html.Div(s[2], style={"fontSize": "9px", "color": "#888",
                               "marginTop": "3px", "lineHeight": "1.4"}),
    ], style={"background": "#f8f9fa", "borderRadius": "6px", "padding": "9px 12px",
              "borderLeft": f"3px solid {BRAND_LIGHT}"}) for s in steps]

    return html.Div([
        breadcrumb([("Overview", "overview"),
                    (c.get("name", iso3), "country"),
                    (f"{pillar_id}: {PILLAR_DEFS.get(pillar_id, pillar_id)}", "pillar"),
                    ((imeta.get("display_name", var) or var)[:55], None)]),
        html.Div([
            html.Div([
                html.H2(imeta.get("display_name", var),
                        style={"margin": "0", "fontSize": "16px",
                               "fontWeight": "700", "color": BRAND}),
                html.P(imeta.get("justification", ""),
                       style={"fontSize": "11px", "color": "#555", "marginTop": "6px",
                              "maxWidth": "620px", "lineHeight": "1.5"}),
                html.Span(f"Source: {imeta.get('database','').upper()} / "
                          f"{imeta.get('series_code','')} / "
                          f"{imeta.get('year_start','')}–{imeta.get('year_end','')}",
                          style={"fontSize": "9px", "color": "#aaa",
                                 "display": "block", "marginTop": "6px"}),
            ]),
            html.Div([
                stat_card("Score", f"{score:.1f}" if score is not None else "-",
                          sub="0-100, higher = stable"),
                stat_card("Polarity", polarity.title(), sub="direction of scoring"),
                stat_card("Log Transform", "Yes" if log_transform else "No"),
                stat_card("Data", "Estimated" if filled else "Real",
                          color="#e67e22" if filled else "#27ae60"),
            ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "flex-start", "gap": "14px", "flexWrap": "wrap",
                  "marginBottom": "12px", "paddingBottom": "10px",
                  "borderBottom": "1px solid #eee"}),

        html.Div([
            html.Div([
                html.H4("How this score was calculated",
                        style={"fontSize": "11px", "fontWeight": "600",
                               "margin": "0 0 10px"}),
                html.Div(step_cards,
                         style={"display": "flex", "flexDirection": "column",
                                "gap": "7px"}),
            ], style={"flex": "1", "minWidth": "280px"}),
            html.Div([
                html.H4("Cross-Country Comparison — all 54 countries",
                        style={"fontSize": "11px", "fontWeight": "600",
                               "margin": "0 0 4px"}),
                html.P(f"Red = {c.get('name', iso3)}  |  "
                       "Purple = island states  |  Blue = all others",
                       style={"fontSize": "9px", "color": "#888", "margin": "0 0 6px"}),
                html.Div(dcc.Graph(figure=fig_cross_country(var, iso3),
                                   config={"displayModeBar": False}),
                         style={"maxHeight": "500px", "overflowY": "auto"}),
            ], style={"flex": "1", "minWidth": "280px"}),
        ], style={"display": "flex", "gap": "14px", "flexWrap": "wrap"}),
    ], style={"padding": "10px 14px"})

# ── Static tabs ───────────────────────────────────────────────────────────────

def render_rankings(method="equal", exclude_islands=False, custom_weights=None):
    if method == "custom" and custom_weights:
        df = _enrich_df_custom(custom_weights)
        sc, rc = "custom_score", "custom_rank"
    else:
        df = countries_df.copy()
        sc, rc = f"{method}_score", f"{method}_rank"
    if exclude_islands:
        df = df[~df["iso3"].isin(ISLAND_SET)].copy()
    df = df.sort_values(rc)
    rows = [{
        "Rank": int(r[rc]),
        "Country": ("[I] " if r["island"] else "") + r["name"],
        "ISO3": r["iso3"], "Region": r["region"],
        METHOD_LABELS[method]: f"{r[sc]:.1f}" if pd.notna(r.get(sc)) else "-",
        **{METHOD_LABELS[m]: (f"{r.get(f'{m}_score',None):.1f}"
                              if pd.notna(r.get(f"{m}_score")) else "-")
           for m in ["equal","pca","bod","entropy","geometric"]
           if m != method},
        "Coverage": f"{r['pct_real']:.0f}%",
        "Quality":  r["fill_flag"],
    } for _, r in df.iterrows()]
    note = html.Div(
        f"{'Island states excluded.  ' if exclude_islands else ''}"
        f"Showing {len(rows)} of 54 countries.  Purple rows = island states.",
        style={"fontSize": "10px", "color": "#888", "padding": "6px 14px",
               "background": "#f8f9fa", "borderBottom": "1px solid #e4e4e4"}
    )
    return html.Div([
        note,
        html.Div(dash_table.DataTable(
            data=rows,
            columns=[{"name": c, "id": c} for c in rows[0].keys()] if rows else [],
            sort_action="native", filter_action="native", page_size=54,
            style_cell={"textAlign": "center", "fontSize": "10px", "padding": "5px 7px"},
            style_cell_conditional=[{"if": {"column_id": "Country"},
                                      "textAlign": "left", "minWidth": "140px"}],
            style_header={"backgroundColor": BRAND, "color": "white",
                          "fontWeight": "bold", "fontSize": "10px"},
            style_data_conditional=[
                {"if": {"filter_query": '{Country} contains "[I]"'},
                 "backgroundColor": "#f5f0ff"},
                {"if": {"filter_query": '{Quality} = "Caution"', "column_id": "Quality"},
                 "backgroundColor": "#fdecea", "color": "#c0392b"},
            ],
            style_table={"overflowX": "auto"},
        ), style={"padding": "10px 14px"}),
    ])


def render_methodology():
    cards = [html.Div([
        html.H3(desc["label"],
                style={"fontSize": "13px", "fontWeight": "700",
                       "color": BRAND, "marginBottom": "4px"}),
        html.P(desc["short"],
               style={"fontSize": "10px", "color": "#777",
                      "fontStyle": "italic", "marginBottom": "8px"}),
        html.Div([html.Span("How to read: ",
                            style={"fontWeight": "700", "fontSize": "10px"}),
                  html.Span(desc["interpretation"],
                            style={"fontSize": "10px", "color": "#555",
                                   "lineHeight": "1.5"})], style={"marginBottom": "8px"}),
        html.Div([html.Span("Strength: ",
                            style={"fontWeight": "700", "color": "#27ae60",
                                   "fontSize": "9px"}),
                  html.Span(desc["strength"],
                            style={"fontSize": "9px", "color": "#555"})],
                 style={"marginBottom": "3px"}),
        html.Div([html.Span("Limitation: ",
                            style={"fontWeight": "700", "color": "#e67e22",
                                   "fontSize": "9px"}),
                  html.Span(desc["limitation"],
                            style={"fontSize": "9px", "color": "#555"})]),
    ], style={"border": "1px solid #e4e4e4", "borderRadius": "8px",
              "padding": "12px", "background": "#fafafa"})
    for m, desc in bundle["method_guide"].items()]

    extra = [
        html.Div([
            html.H3("Traffic Light Thresholds",
                    style={"fontSize": "13px", "fontWeight": "700",
                           "color": BRAND, "marginBottom": "8px"}),
            html.Div([traffic_light(80),
                      html.Span("  Stable  (score >= 65)",
                                style={"fontSize": "11px", "marginLeft": "6px"})],
                     style={"display": "flex", "alignItems": "center",
                            "marginBottom": "6px"}),
            html.Div([traffic_light(50),
                      html.Span("  Moderate  (score 35-65)",
                                style={"fontSize": "11px", "marginLeft": "6px"})],
                     style={"display": "flex", "alignItems": "center",
                            "marginBottom": "6px"}),
            html.Div([traffic_light(20),
                      html.Span("  Fragile  (score < 35)",
                                style={"fontSize": "11px", "marginLeft": "6px"})],
                     style={"display": "flex", "alignItems": "center",
                            "marginBottom": "6px"}),
            html.P("Thresholds are visual guides, not official classifications.",
                   style={"fontSize": "9px", "color": "#aaa", "marginTop": "8px"}),
        ], style={"border": "1px solid #e4e4e4", "borderRadius": "8px",
                  "padding": "12px", "background": "#fafafa",
                  "gridColumn": "1 / span 2"}),
        html.Div([
            html.H3("Island State Caveat",
                    style={"fontSize": "13px", "fontWeight": "700",
                           "color": "#8e44ad", "marginBottom": "8px"}),
            html.P("Six island states (SYC, MUS, CPV, STP, COM, MDG) consistently "
                   "rank highest across all methods due to structural geographic advantages: "
                   "small populations reduce absolute conflict counts, natural sea borders "
                   "eliminate land-border security concerns, and concentrated economies "
                   "are easier to govern. Use the 'Exclude island states' toggle in the "
                   "toolbar for mainland-only comparisons.",
                   style={"fontSize": "10px", "color": "#555", "lineHeight": "1.5"}),
        ], style={"border": "1px solid #e0d8f0", "borderRadius": "8px",
                  "padding": "12px", "background": "#fafafa",
                  "borderLeft": "4px solid #8e44ad", "gridColumn": "1 / span 2"}),
    ]
    return html.Div(cards + extra,
                    style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                           "gap": "10px", "padding": "14px"})


def render_sources():
    rows = []
    for var, meta in sorted(ind_meta.items()):
        if meta.get("role", "scoring") != "scoring":
            continue
        rows.append({
            "Variable":     var,
            "Display Name": (meta.get("display_name", "") or "")[:70],
            "Pillars":      ", ".join(meta.get("pillars", [])),
            "Database":     meta.get("database", "").upper(),
            "Series Code":  meta.get("series_code", ""),
            "Polarity":     meta.get("polarity", ""),
            "Log":          "Yes" if meta.get("log_transform") else "No",
            "Years":        f"{meta.get('year_start','')} - {meta.get('year_end','')}",
        })
    col_widths = {
        "Variable": 130, "Display Name": 260, "Pillars": 70,
        "Database": 75, "Series Code": 160, "Polarity": 80,
        "Log": 45, "Years": 110,
    }
    return html.Div([
        html.Div([
            html.P(
                "Full indicator provenance. Orange rows = indicator counted in "
                "multiple pillars (receives implicit extra weight).",
                style={"fontSize": "11px", "color": "#555", "margin": "0 0 4px"}),
            html.P(
                "Click any column header to sort  ·  "
                "Type in the grey filter boxes below the header to search within that column  ·  "
                "Drag column edges to resize",
                style={"fontSize": "10px", "color": "#aaa", "margin": "0",
                       "fontStyle": "italic"}),
        ], style={"padding": "8px 14px", "background": "#f8f9fa",
                  "borderBottom": "1px solid #e4e4e4"}),
        html.Div(dash_table.DataTable(
            data=rows,
            columns=[{"name": c, "id": c} for c in rows[0].keys()],
            sort_action="native",
            filter_action="native",
            filter_options={"case": "insensitive", "placeholder_text": "filter…"},
            page_size=40,
            style_cell={"textAlign": "left", "fontSize": "11px", "padding": "6px 10px",
                        "overflow": "hidden", "textOverflow": "ellipsis",
                        "whiteSpace": "normal", "minWidth": "60px"},
            style_cell_conditional=[
                {"if": {"column_id": col}, "width": f"{w}px", "minWidth": f"{w}px"}
                for col, w in col_widths.items()
            ],
            style_header={"backgroundColor": BRAND, "color": "white",
                          "fontWeight": "bold", "fontSize": "11px",
                          "padding": "8px 10px", "cursor": "pointer"},
            style_filter={"backgroundColor": "#f0f4f8", "fontSize": "10px",
                          "border": "1px solid #d0d8e4"},
            style_data={"fontSize": "11px"},
            style_data_conditional=[
                {"if": {"filter_query": '{Pillars} contains ","'},
                 "backgroundColor": "#fff8e1", "color": "#9a6700"},
            ],
            style_table={"overflowX": "auto", "minWidth": "100%"},
            tooltip_delay=0,
            tooltip_duration=None,
        ), style={"padding": "10px 14px"}),
    ])


def render_audit():
    if not audit:
        return html.Div("No audit report found. Run: python 00_audit.py",
                        style={"padding": "20px", "color": "#999"})
    icons = {"PASS": ("v", "#27ae60"), "WARN": ("!", "#e67e22"),
             "FAIL": ("X", "#c0392b"), "INFO": (".", "#aaa")}
    stat_row = html.Div([
        stat_card("PASS", audit.get("n_pass", 0), color="#27ae60"),
        stat_card("WARN", audit.get("n_warn", 0), color="#e67e22"),
        stat_card("FAIL", audit.get("n_fail", 0), color="#c0392b"),
        html.Div([html.Div("Last run:", style={"fontSize": "9px", "color": "#aaa"}),
                  html.Div(audit.get("run_date", "-"),
                           style={"fontSize": "11px", "fontWeight": "600"})],
                 style={"padding": "8px", "textAlign": "center"}),
    ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap",
              "padding": "8px 14px", "borderBottom": "1px solid #e4e4e4"})

    section_divs = []
    for section, checks in audit.get("sections", {}).items():
        items = [html.Div([
            html.Span(icons.get(chk["status"], (".", "#aaa"))[0] + " ",
                      style={"color": icons.get(chk["status"], (".", "#aaa"))[1],
                             "fontWeight": "700", "marginRight": "5px",
                             "fontSize": "13px"}),
            html.Span(f"[{chk['status']}] ",
                      style={"color": icons.get(chk["status"], (".", "#aaa"))[1],
                             "fontWeight": "600", "fontSize": "9px",
                             "marginRight": "4px"}),
            html.Span(chk["msg"],
                      style={"fontSize": "10px", "color": "#444", "lineHeight": "1.4"}),
        ], style={"padding": "4px 0", "borderBottom": "1px solid #f8f8f8",
                  "display": "flex", "alignItems": "flex-start"}) for chk in checks]
        section_divs.append(html.Div([
            html.H4(section,
                    style={"fontSize": "11px", "fontWeight": "700", "color": BRAND,
                           "margin": "10px 0 5px", "background": "#f0f4f8",
                           "padding": "4px 8px", "borderRadius": "4px"}),
            *items,
        ]))

    meta_sum = audit.get("indicator_meta_summary", {})
    notes = html.Div([
        html.H4("Known Structural Issues",
                style={"fontSize": "12px", "fontWeight": "700",
                       "color": BRAND, "marginBottom": "8px"}),
        html.Div([
            html.H5("Double-counting",
                    style={"fontSize": "11px", "fontWeight": "700",
                           "color": "#e67e22", "margin": "0 0 4px"}),
            html.P(f"{meta_sum.get('n_cross_listed',0)} of {meta_sum.get('n_total',0)} "
                   "indicators appear in multiple pillars. The cross-listed WGI "
                   "governance indicators (e.g. pv_estimate and rl_estimate in Pillars "
                   "A+E) carry up to ~1.9x the effective weight of a single-pillar "
                   "indicator.",
                   style={"fontSize": "10px", "color": "#555",
                          "lineHeight": "1.4", "margin": "0"}),
        ], style={"padding": "10px", "background": "#fff8e1", "borderRadius": "6px",
                  "border": "1px solid #f1c40f", "marginBottom": "8px"}),
        html.Div([
            html.H5("IDP size bias — resolved",
                    style={"fontSize": "11px", "fontWeight": "700",
                           "color": "#27ae60", "margin": "0 0 4px"}),
            html.P("Displaced persons is normalized to a per-1,000-population rate in "
                   "02_clean.py (Step 1b), so large countries (DRC, Ethiopia, Sudan) are "
                   "no longer penalized by population size.",
                   style={"fontSize": "10px", "color": "#555",
                          "lineHeight": "1.4", "margin": "0"}),
        ], style={"padding": "10px", "background": "#eafaf1", "borderRadius": "6px",
                  "border": "1px solid #27ae60", "marginBottom": "8px"}),
        html.Div([
            html.H5("Pillar size imbalance",
                    style={"fontSize": "11px", "fontWeight": "700",
                           "color": "#aaa", "margin": "0 0 4px"}),
            html.P("Indicators per pillar: " + ", ".join(
                f"{k}={v}" for k, v in sorted(meta_sum.get("pillar_sizes", {}).items())
            ) + ". Equal pillar weights ≠ equal indicator weights.",
                   style={"fontSize": "10px", "color": "#555",
                          "lineHeight": "1.4", "margin": "0"}),
        ], style={"padding": "10px", "background": "#f8f9fa", "borderRadius": "6px",
                  "border": "1px solid #ddd"}),
    ], style={"padding": "12px", "background": "#fafafa", "borderRadius": "8px",
              "border": "1px solid #e4e4e4"})

    return html.Div([
        stat_row,
        html.Div([
            html.Div(section_divs, style={"flex": "1", "minWidth": "300px"}),
            html.Div(notes, style={"width": "340px", "flexShrink": "0"}),
        ], style={"display": "flex", "gap": "14px", "padding": "10px 14px",
                  "flexWrap": "wrap"}),
    ])

# ── Custom weights panel ───────────────────────────────────────────────────────

def _custom_weights_panel():
    """Permanent DOM panel — shown only when method-select = 'custom'."""
    sliders = []
    for p, pname in PILLAR_DEFS.items():
        sliders.append(html.Div([
            html.Div([
                html.Span(f"{p}:", style={"fontWeight": "700", "fontSize": "10px",
                                           "color": BRAND, "marginRight": "4px"}),
                html.Span(pname, style={"fontSize": "10px", "color": "#555"}),
            ], style={"minWidth": "220px"}),
            html.Div(
                dcc.Slider(
                    id={"type": "weight-slider", "index": p},
                    min=0, max=50, step=1, value=14,
                    marks={0: "0", 10: "10", 20: "20", 30: "30",
                           40: "40", 50: "50"},
                    tooltip={"placement": "top", "always_visible": False},
                ),
                style={"flex": "1", "minWidth": "200px"},
            ),
            html.Span(id={"type": "weight-pct", "index": p}, children="14%",
                      style={"minWidth": "36px", "textAlign": "right",
                             "fontSize": "10px", "color": BRAND_LIGHT,
                             "fontWeight": "700"}),
        ], style={"display": "flex", "alignItems": "center", "gap": "8px",
                  "marginBottom": "6px"}))

    return html.Div(id="custom-weights-panel", children=[
        html.Div([
            html.Span("Custom Pillar Weights",
                      style={"fontWeight": "700", "fontSize": "11px",
                             "color": BRAND, "marginRight": "16px"}),
            html.Span(id="custom-weights-total", children="Total: 98%",
                      style={"fontSize": "10px", "color": "#888",
                             "marginRight": "16px"}),
            html.Button("Normalize to 100%", id="normalize-weights-btn", n_clicks=0,
                        style={"fontSize": "9px", "background": BRAND_LIGHT,
                               "color": "#fff", "border": "none",
                               "borderRadius": "4px", "padding": "3px 8px",
                               "cursor": "pointer", "marginRight": "8px"}),
            html.Button("Reset to Equal", id="reset-weights-btn", n_clicks=0,
                        style={"fontSize": "9px", "background": "#f0f0f0",
                               "color": "#555", "border": "1px solid #ddd",
                               "borderRadius": "4px", "padding": "3px 8px",
                               "cursor": "pointer"}),
        ], style={"display": "flex", "alignItems": "center",
                  "marginBottom": "10px"}),
        html.Div(sliders),
        html.Div("Weights are normalized to sum to 100% automatically when computing scores. "
                 "Total shown above reflects your raw input.",
                 style={"fontSize": "9px", "color": "#aaa", "marginTop": "6px"}),
    ], style={
        "display": "none",
        "padding": "12px 18px",
        "background": "#f0f4f8",
        "borderBottom": "1px solid #dde5ef",
    })

# ── App layout ────────────────────────────────────────────────────────────────

app = Dash(
    __name__,
    # Explicit path: when this file is loaded via importlib (app.py/gunicorn)
    # or runpy, __name__-based asset resolution points at the wrong directory.
    assets_folder=str(Path(__file__).resolve().parent / "assets"),
    external_stylesheets=[dbc.themes.FLATLY],
    title="African Stability Index",
    suppress_callback_exceptions=True,
)

app.layout = html.Div([
    # ── Header ───────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.H1("African Stability Index",
                    style={"color": "#fff", "margin": "0", "fontSize": "19px",
                           "fontWeight": "700"}),
            # Counts derive from the loaded data, never hardcoded: the header
            # previously read "36 Indicators" long after the count changed.
            # verify/contract.py fails the build if a literal count reappears.
            html.Div(f"{N_COUNTRIES} AU Member States  |  {N_PILLARS} Pillars  |  "
                     f"{N_SCORING_INDICATORS} Indicators  |  "
                     "Click map or pillars to drill down",
                     style={"color": "#9bb8d4", "fontSize": "10px",
                            "marginTop": "2px"}),
        ]),
        html.Div("Score: 0 = most fragile  |  100 = most stable",
                 style={"color": "#9bb8d4", "fontSize": "10px"}),
    ], style={"background": BRAND, "padding": "10px 18px", "display": "flex",
              "justifyContent": "space-between", "alignItems": "center"}),

    # ── Permanent toolbar (always in DOM — required for callbacks) ────────────
    html.Div([
        html.Div([
            html.Label("Scoring method:",
                       style={"fontSize": "11px", "fontWeight": "600",
                              "marginRight": "6px", "color": "#555",
                              "whiteSpace": "nowrap"}),
            dcc.Dropdown(
                id="method-select",
                options=[{"label": METHOD_LABELS[m], "value": m} for m in METHODS],
                value="geometric",
                clearable=False,
                style={"width": "220px"},
            ),
        ], style={"display": "flex", "alignItems": "center", "gap": "4px"}),
        dcc.Checklist(
            id="island-toggle",
            options=[{"label": "  Exclude island states from rankings",
                      "value": "exclude"}],
            value=[],
            inputStyle={"marginRight": "4px"},
            labelStyle={"fontSize": "11px", "color": "#555",
                        "display": "flex", "alignItems": "center"},
        ),
        html.Span("Green >= 65  |  Yellow 35-65  |  Red < 35",
                  style={"fontSize": "10px", "color": "#aaa"}),
    ], style={"display": "flex", "alignItems": "center", "gap": "24px",
              "padding": "7px 18px", "background": "#f4f6f8",
              "borderBottom": "1px solid #e4e4e4", "flexWrap": "wrap"}),

    # ── Custom weights panel (hidden until method = "custom") ─────────────────
    _custom_weights_panel(),

    # ── Stores and tabs ───────────────────────────────────────────────────────
    dcc.Store(id="nav-state", data={
        "level": "overview", "iso3": None,
        "pillar": None, "var": None,
        "method": "geometric", "exclude_islands": False,
    }),
    dcc.Store(id="custom-weights", data=EQUAL_WEIGHTS),
    # Permanent relay for map clicks — ov-map only exists on the overview page,
    # so it cannot be a direct Input to navigate(). This Store is always present.
    dcc.Store(id="map-click-store", data=None),
    # Permanent relay for dynamic component clicks (pillar-btn, ind-btn, breadcrumb).
    # Those components exist only in dynamic content, so they can't be direct Inputs
    # to navigate() — same reason as map-click-store.
    dcc.Store(id="nav-event", data=None),

    html.Div([
        dcc.Tabs(id="nav-tabs", value="explore", children=[
            dcc.Tab(label="Explore (Map + Drill-Down)", value="explore"),
            dcc.Tab(label="Full Rankings",              value="rankings"),
            dcc.Tab(label="Methodology",                value="methodology"),
            dcc.Tab(label="Data Sources",               value="sources"),
            dcc.Tab(label="Audit / Verification",       value="audit"),
        ]),
        html.Div(id="tab-content"),
    ], style={"maxWidth": "1500px", "margin": "0 auto", "padding": "0 6px"}),

], style={"fontFamily": "'Segoe UI',system-ui,sans-serif",
          "backgroundColor": "#fff", "minHeight": "100vh"})

# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("tab-content", "children"),
    Input("nav-tabs", "value"),
    Input("nav-state", "data"),
    Input("custom-weights", "data"),
)
def render_tab(tab, nav, custom_weights):
    method = nav.get("method", "equal")
    excl   = nav.get("exclude_islands", False)
    cw     = custom_weights if method == "custom" else None

    if tab == "rankings":    return render_rankings(method, excl, cw)
    if tab == "methodology": return render_methodology()
    if tab == "sources":     return render_sources()
    if tab == "audit":       return render_audit()

    level = nav.get("level", "overview")
    if level == "country":   return render_country(nav.get("iso3"), method, cw)
    if level == "pillar":
        try:
            return render_pillar(nav.get("iso3"), nav.get("pillar"))
        except Exception:
            import traceback
            return html.Pre(traceback.format_exc(),
                            style={"background": "#fff0f0", "color": "#c0392b",
                                   "padding": "16px", "fontSize": "11px",
                                   "whiteSpace": "pre-wrap", "margin": "12px"})
    if level == "indicator": return render_indicator(nav.get("iso3"), nav.get("pillar"), nav.get("var"))
    return render_overview(method, excl, cw)


@app.callback(
    Output("map-click-store", "data"),
    Input("ov-map", "clickData"),
    prevent_initial_call=True,
)
def relay_map_click(click_data):
    """Push map clicks into a permanent Store so navigate() always has stable inputs."""
    return click_data


@app.callback(
    Output("nav-event", "data"),
    Input({"type": "pillar-btn", "index": ALL}, "n_clicks"),
    Input({"type": "ind-btn",    "index": ALL}, "n_clicks"),
    Input({"type": "breadcrumb", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def relay_click(_pb, _ib, _bcs):
    """Relay dynamic-component clicks into the permanent nav-event Store.

    Pattern-matched ALL inputs fire whenever matching components are added or
    removed from the DOM (not only on real clicks).  By isolating that logic
    here and writing to a Store, navigate() can stay free of pattern-matched
    Inputs and will never be triggered by component-mount events.
    """
    tid = callback_context.triggered_id
    if not isinstance(tid, dict):
        return no_update
    # n_clicks == 0 means the component just mounted — not a real click.
    val = (callback_context.triggered or [{}])[0].get("value", 0)
    if not val:
        return no_update
    return {"type": tid.get("type"), "index": tid.get("index"), "ts": val}


@app.callback(
    Output("nav-state", "data"),
    Input("map-click-store", "data"),   # permanent
    Input("nav-event",       "data"),   # permanent relay for dynamic clicks
    Input("method-select",   "value"),  # permanent toolbar
    Input("island-toggle",   "value"),  # permanent toolbar
    State("nav-state", "data"),
    prevent_initial_call=True,
)
def navigate(map_click, nav_event, method, island_val, nav):
    """Update navigation state.  All inputs are permanent (always in DOM)."""
    tid = callback_context.triggered_id

    if tid == "method-select":
        return {**nav, "method": method}

    if tid == "island-toggle":
        return {**nav, "exclude_islands": "exclude" in (island_val or [])}

    if tid == "map-click-store" and map_click:
        iso3 = map_click["points"][0].get("location")
        if iso3 and iso3 in country_lookup:
            return {**nav, "level": "country", "iso3": iso3}

    if tid == "nav-event" and nav_event:
        t   = nav_event.get("type")
        idx = nav_event.get("index")
        if t == "breadcrumb" and idx:
            return {**nav, "level": idx}
        if t == "pillar-btn" and idx:
            return {**nav, "level": "pillar", "pillar": idx}
        if t == "ind-btn" and idx:
            return {**nav, "level": "indicator", "var": idx}

    return no_update


@app.callback(
    Output("custom-weights-panel", "style"),
    Input("method-select", "value"),
)
def toggle_weights_panel(method):
    visible = {
        "display": "block", "padding": "12px 18px",
        "background": "#f0f4f8", "borderBottom": "1px solid #dde5ef",
    }
    hidden  = {"display": "none"}
    return visible if method == "custom" else hidden


@app.callback(
    Output("custom-weights", "data"),
    Output("custom-weights-total", "children"),
    Output({"type": "weight-pct", "index": ALL}, "children"),
    Input({"type": "weight-slider", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def update_custom_weights(slider_values):
    pillars = list(PILLAR_DEFS.keys())
    raw     = {p: float(v or 0) for p, v in zip(pillars, slider_values)}
    total   = sum(raw.values())

    if total == 0:
        weights  = EQUAL_WEIGHTS.copy()
        total_str = "Total: 0% — using equal weights as fallback"
    else:
        weights   = {p: v / total for p, v in raw.items()}
        sign      = " ✓" if abs(total - 100) < 0.5 else " (will normalize)"
        total_str = f"Total: {total:.0f}%{sign}"

    pct_labels = [f"{weights[p]*100:.0f}%" for p in pillars]
    return weights, total_str, pct_labels


@app.callback(
    Output({"type": "weight-slider", "index": ALL}, "value"),
    Input("reset-weights-btn", "n_clicks"),
    Input("normalize-weights-btn", "n_clicks"),
    State({"type": "weight-slider", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def handle_weight_buttons(reset_clicks, norm_clicks, current_values):
    tid = callback_context.triggered_id
    if isinstance(tid, str) and tid == "reset-weights-btn":
        return [14] * len(PILLAR_DEFS)
    # Normalize: scale raw values to sum to 100
    vals  = [float(v or 0) for v in current_values]
    total = sum(vals)
    if total == 0:
        return [14] * len(PILLAR_DEFS)
    factor  = 100.0 / total
    scaled  = [min(50, max(0, round(v * factor))) for v in vals]
    return scaled


# gunicorn entry point: "gunicorn app:server" (see app.py)
server = app.server

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    print(f"\nAfrican Stability Index Dashboard")
    print(f"Open: http://127.0.0.1:{port}\n")
    app.run(debug=debug, host="0.0.0.0", port=port)
