"""
asi.dashboard.app — the panel-driven interface.

Replaces the single-snapshot dashboard. Three things drove the design:

1. Two controls, not five.
   Adding a pillar view, community grouping and a time slider naively means five
   toolbar controls. Instead there are two: a Lens ("what is the map showing?" —
   a composite method or one pillar) and Compare ("who is being compared?" —
   everyone, a region, or a Regional Economic Community). The year lives on
   country pages only, where it belongs.

2. Greyed, not blank.
   A country whose data is mostly inferred is drawn in grey with a stated
   reason. Blank would be indistinguishable from "no such country", and a plain
   number would be a claim the data cannot support.

3. The interface derives nothing.
   Every value comes from asi.dashboard.data, which reads results the pipeline
   computed and verify/panel.py checked. No score, rank or label is calculated
   here.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import yaml
from dash import Dash, dcc, html, Input, Output, State, ALL, callback_context, no_update
import dash_bootstrap_components as dbc

from asi.core.constants import PILLAR_DEFS, ACTIVE_PROFILE, PROJECT_ROOT
from asi.dashboard import data as D
from asi.dashboard import narrative_ui as N
from asi.narrative.store import load_corpus

# ── Presentation constants ─────────────────────────────────────────────────────

BRAND       = "#1B3A6B"
BRAND_LIGHT = "#2E6DB4"
GREY        = "#d8dbe0"
SCORE_CS    = [[0.0, "#c0392b"], [0.35, "#e67e22"], [0.65, "#f1c40f"], [1.0, "#2ecc71"]]

METHOD_LABELS = {
    "equal":     "Equal weights",
    "pca":       "PCA weights",
    "entropy":   "Entropy weights",
    "geometric": "Geometric mean",
    "bod":       "Benefit of the doubt",
}

TIER_STYLE = {
    "reliable":   ("#27ae60", "Measured"),
    "thin":       ("#e67e22", "Partly estimated"),
    "unreliable": ("#95a5a6", "Too inferred to show"),
    "absent":     ("#bdc3c7", "No data"),
}

CONTEXT_DIR = PROJECT_ROOT / "context"
QUAL_DIR    = PROJECT_ROOT / "qualitative" / "countries"

#: AU member states this edition does not score, and why. Kept as data rather
#: than prose so the union total shown to a reader stays derived: the AU count
#: is the scored set plus these, and neither number is ever typed into a string.
EXCLUDED_AU_MEMBERS = {
    "Western Sahara": (
        "the Sahrawi Arab Democratic Republic, an AU member since 1984 — the "
        "admission that caused Morocco to leave the OAU until 2017"
    ),
}


# ── Data ───────────────────────────────────────────────────────────────────────

PANEL = D.load()


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


COLONIAL      = _load_yaml(CONTEXT_DIR / "colonial_history.yaml")
COUNTRY_FACTS = _load_yaml(CONTEXT_DIR / "country_facts.yaml")
QUAL_NOTES = {
    p.stem.upper(): _load_yaml(p) for p in QUAL_DIR.glob("*.yaml")
} if QUAL_DIR.exists() else {}

#: The narrative corpus: one validated record per country, or {} if the research
#: pass has not run. Absent records degrade to a stated absence rather than an
#: error — the index is meant to serve its numbers with or without the prose.
NARRATIVE = load_corpus()

#: Derived once. Every count a reader sees comes from the data: the header
#: claimed "36 Indicators" for weeks after the number changed, which is why
#: verify/contract.py refuses literal counts in interface strings.
N_SCORING = sum(1 for m in PANEL.indicators.values() if m.get("role") == "scoring")


# ── Small components ───────────────────────────────────────────────────────────

def tier_badge(reliability: str, coverage: float | None = None):
    colour, label = TIER_STYLE.get(reliability, TIER_STYLE["absent"])
    return html.Span(
        label,
        title=D.reliability_note(reliability, coverage),
        style={"background": colour + "22", "color": colour, "fontWeight": "700",
               "fontSize": "9px", "padding": "2px 7px", "borderRadius": "4px",
               "whiteSpace": "nowrap"},
    )


def stat(label, value, sub=None, colour=BRAND):
    return html.Div([
        html.Div(str(value), style={"fontSize": "23px", "fontWeight": "700",
                                    "color": colour, "lineHeight": "1.1"}),
        html.Div(label, style={"fontSize": "10px", "color": "#777", "marginTop": "2px"}),
        html.Div(sub, style={"fontSize": "9px", "color": "#bbb"}) if sub else None,
    ], style={"background": "#f8f9fa", "borderRadius": "8px", "padding": "9px 13px",
              "border": "1px solid #e4e4e4", "textAlign": "center", "minWidth": "84px"})


def breadcrumb(steps):
    items = []
    for i, (label, target) in enumerate(steps):
        last = i == len(steps) - 1 or target is None
        if last:
            items.append(html.Span(label, style={"color": BRAND, "fontWeight": "600",
                                                 "fontSize": "12px"}))
        else:
            items.append(html.Button(
                label, id={"type": "crumb", "index": target}, n_clicks=0,
                style={"background": "none", "border": "none", "color": BRAND_LIGHT,
                       "cursor": "pointer", "fontSize": "12px", "padding": 0,
                       "textDecoration": "underline", "fontWeight": "600"}))
        if i < len(steps) - 1:
            items.append(html.Span(" › ", style={"color": "#bbb", "margin": "0 5px"}))
    return html.Div(items, style={"padding": "4px 0 10px"})


def year_slider(index: str, year: int, *, marks=None, caption: str | None = None,
                trailing=None):
    """
    The year control, shared by the continent views and the country page.

    `index` distinguishes instances; the id is pattern-matching because these
    live inside `content` and only one exists at a time. A plain id would stop
    Dash running the navigation callback on every page that lacks the slider.
    """
    return html.Div([
        html.Div([
            html.Span("Year", style={"fontSize": "11px", "fontWeight": "700",
                                     "color": "#555", "marginRight": "10px"}),
            html.Span(str(year), style={"fontSize": "13px", "fontWeight": "700",
                                        "color": BRAND}),
            html.Span(caption, style={"fontSize": "10px", "color": "#aaa",
                                      "marginLeft": "8px"}) if caption else None,
            trailing,
        ], style={"marginBottom": "2px", "display": "flex", "alignItems": "center",
                  "flexWrap": "wrap"}),
        dcc.Slider(
            id={"type": "year-slider", "index": index},
            min=PANEL.panel_start, max=PANEL.panel_end, step=1, value=year,
            marks=marks or {y: {"label": str(y), "style": {"fontSize": "9px",
                                                           "color": "#888"}}
                            for y in range(PANEL.panel_start, PANEL.panel_end + 1, 4)},
            tooltip={"placement": "bottom", "always_visible": False},
        ),
    ], style={"padding": "10px 14px 4px", "background": "#f8f9fa",
              "border": "1px solid #e8e8e8", "borderRadius": "8px",
              "margin": "10px 0"})


def year_coverage_note(year: int, n_shown: int, n_total: int):
    """
    Why a year shows fewer countries than the map has.

    Without this a reader drags to 2024, sees an empty continent, and concludes
    the tool is broken. The panel genuinely runs to 2024; what it does not have
    is enough *reported* data to score it. Saying which of those two is true is
    the whole point of the greyed-not-blank rule, applied to the time axis.
    """
    if n_shown == n_total:
        return None

    reasons = []
    if year > PANEL.reference_year:
        reasons.append(
            f"The panel runs to {PANEL.panel_end}, but {PANEL.reference_year} is the "
            f"most recent year with enough reported data to score. World Bank series "
            f"publish on a lag, so later years are mostly empty rather than mostly bad."
        )
    if year == 2001:
        reasons.append(
            "Governance indicators were published biennially before 2002, so 2001 has "
            "no governance observation at all and is largely estimated."
        )

    severe = n_shown == 0
    colour = "#c0392b" if severe else "#7f8c8d"
    return html.Div([
        html.Span(f"{n_shown} of {n_total} countries scoreable in {year}. ",
                  style={"fontWeight": "700", "color": colour}),
        html.Span(" ".join(reasons) if reasons else
                  "The rest are greyed because too much of their data is inferred "
                  "rather than measured in this year.",
                  style={"color": "#7f8c8d"}),
    ], style={"fontSize": "11px", "background": "#f4f6f7", "border": "1px solid #dfe4e6",
              "borderLeft": f"4px solid {colour}", "borderRadius": "6px",
              "padding": "9px 13px", "margin": "8px 0"})


def rec_membership_caveat(mode: str, key: str | None, year: int):
    """
    Warn when a community grouping is applied to a year its membership predates.

    `asi.core.countries` stores REC membership as current status only — its own
    docstring flags that a time slider would need year-aware membership. Rather
    than silently compare "ECOWAS in 2010" using 2026's membership list, this
    names the countries whose own sourced narrative records say they were on the
    other side of the line that year.
    """
    if mode != "rec" or not key:
        return None

    now = {iso for iso, m in PANEL.countries.items() if key in (m.get("recs") or [])}
    joined_later, left_since = [], []
    for iso, record in NARRATIVE.items():
        spans = [m for m in record.rec_membership if m.org == key]
        if not spans:
            continue
        member_then = any(
            m.joined is not None and m.joined <= year and (m.left is None or year < m.left)
            for m in spans
        )
        name = PANEL.countries.get(iso, {}).get("name", iso)
        if iso in now and not member_then:
            joined_later.append(name)
        elif iso not in now and member_then:
            left_since.append(name)

    if not joined_later and not left_since:
        return None

    parts = []
    if joined_later:
        parts.append(f"{', '.join(sorted(joined_later))} had not joined yet")
    if left_since:
        parts.append(f"{', '.join(sorted(left_since))} were members then but are not now")
    return html.Div([
        html.Span(f"{key} membership is grouped as it stands today. ",
                  style={"fontWeight": "700", "color": "#8a6d3b"}),
        html.Span(f"In {year}, " + "; ".join(parts) + ".",
                  style={"color": "#8a6d3b"}),
    ], style={"fontSize": "10px", "background": "#fffaf0", "border": "1px solid #f0e2c0",
              "borderLeft": "4px solid #d4a017", "borderRadius": "6px",
              "padding": "8px 12px", "margin": "6px 0"})


def unreliable_banner(reliability: str, coverage: float | None, year: int):
    """Say plainly why a panel is greyed, rather than showing an empty box."""
    if reliability in D.DISPLAYABLE:
        return None
    return html.Div([
        html.Span("Not shown for " + str(year) + ". ",
                  style={"fontWeight": "700", "color": "#7f8c8d"}),
        html.Span(D.reliability_note(reliability, coverage), style={"color": "#7f8c8d"}),
    ], style={"fontSize": "11px", "background": "#f4f6f7", "border": "1px solid #dfe4e6",
              "borderLeft": "4px solid #95a5a6", "borderRadius": "6px",
              "padding": "9px 13px", "margin": "8px 0"})


# ── Figures ────────────────────────────────────────────────────────────────────

def fig_map(frame: pd.DataFrame, lens: D.Lens):
    """
    Two layers: countries we can show, and countries we cannot.

    The grey layer is the honest part — it keeps every country on the map while
    refusing to state a number the data does not support.
    """
    shown = frame[frame["displayable"] & frame["in_scope"]]
    muted = frame[~(frame["displayable"] & frame["in_scope"])]

    fig = go.Figure()

    if not muted.empty:
        reasons = [
            "Outside current comparison" if row.displayable
            else D.reliability_note(row.reliability, row.coverage_ratio)
            for row in muted.itertuples()
        ]
        fig.add_trace(go.Choropleth(
            locations=muted["iso3"], z=[0] * len(muted),
            colorscale=[[0, GREY], [1, GREY]], showscale=False,
            marker_line_color="#ffffff", marker_line_width=0.6,
            customdata=list(zip(muted["name"], reasons)),
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
        ))

    if not shown.empty:
        hover = [
            f"<b>{r.name}</b><br>Score {r.score:.1f}"
            + (f" &nbsp;·&nbsp; #{int(r.scope_rank)}" if pd.notna(getattr(r, "scope_rank", pd.NA)) else "")
            + f"<br>{TIER_STYLE.get(r.reliability, ('', ''))[1]}"
            for r in shown.itertuples()
        ]
        fig.add_trace(go.Choropleth(
            locations=shown["iso3"], z=shown["score"],
            colorscale=SCORE_CS, zmin=0, zmax=100,
            marker_line_color="#ffffff", marker_line_width=0.6,
            customdata=hover,
            hovertemplate="%{customdata}<extra></extra>",
            colorbar=dict(title="Score", tickvals=[0, 35, 65, 100],
                          ticktext=["0", "35", "65", "100"], len=0.55, thickness=12),
        ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(scope=ACTIVE_PROFILE.map_scope, bgcolor="rgba(0,0,0,0)",
                 showframe=False, showcoastlines=True, coastlinecolor="#ccc",
                 showland=True, landcolor="#f5f5f5",
                 showocean=True, oceancolor="#eaf3f8"),
    )
    return fig


def fig_country_series(series: pd.DataFrame, selected_year: int, title: str):
    """
    A country's trajectory, with unreliable years visibly interrupted.

    Undisplayable years are drawn as hollow grey markers on a broken line rather
    than being joined up — an unbroken line through inferred data would assert a
    continuity that was never measured.
    """
    fig = go.Figure()
    good = series[series["displayable"]]
    bad = series[~series["displayable"] & series["score"].notna()]

    if not good.empty:
        # break the line wherever a year is not displayable
        line = series.copy()
        line.loc[~line["displayable"], "score"] = None
        fig.add_trace(go.Scatter(
            x=line["year"], y=line["score"], mode="lines+markers",
            line=dict(color=BRAND_LIGHT, width=2), marker=dict(size=5),
            connectgaps=False, name=title,
            hovertemplate="%{x}: %{y:.1f}<extra></extra>",
        ))
    if not bad.empty:
        fig.add_trace(go.Scatter(
            x=bad["year"], y=bad["score"], mode="markers",
            marker=dict(size=6, color="#ffffff",
                        line=dict(color="#b0b7bd", width=1.5)),
            name="Not reliable",
            hovertemplate="%{x}: not shown — too much inferred<extra></extra>",
        ))

    fig.add_vline(x=selected_year, line_dash="dot", line_color="#c0392b", line_width=1.5)
    fig.update_layout(
        height=210, margin=dict(l=10, r=10, t=6, b=24),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[0, 100], title=None, gridcolor="#f0f0f0"),
        xaxis=dict(gridcolor="#fafafa"),
        showlegend=False,
    )
    return fig


# ── Views ──────────────────────────────────────────────────────────────────────

def view_overview(lens: D.Lens, group_mode: str, group_key: str | None,
                  exclude_islands: bool, year: int):
    frame = D.choropleth_frame(PANEL, lens, year)
    frame = D.apply_grouping(frame, group_mode, group_key,
                             exclude_islands=exclude_islands)
    ranked = D.rankings(frame)
    frame = frame.merge(ranked[["iso3", "scope_rank"]], on="iso3", how="left")

    n_shown = len(ranked)
    n_grey = int((~frame["displayable"]).sum())
    avg = ranked["score"].mean() if not ranked.empty else float("nan")

    def mini(rows, colour):
        return [html.Div([
            html.Span(f"#{int(r.scope_rank)} ", style={"color": "#aaa", "fontSize": "10px",
                                                       "minWidth": "26px",
                                                       "display": "inline-block"}),
            html.Span(r.name, style={"fontSize": "11px", "fontWeight": "600"}),
            html.Span(f"{r.score:.1f}", style={"color": colour, "fontSize": "11px",
                                               "float": "right"}),
        ], style={"padding": "3px 0", "borderBottom": "1px solid #f5f5f5"})
            for r in rows.itertuples()]

    scope_label = (
        f"{group_key}" if group_mode == "rec" and group_key else
        f"{group_key} Africa" if group_mode == "region" and group_key else
        "All of Africa"
    )

    return html.Div([
        html.Div([
            html.Div([
                html.Span(lens.label(METHOD_LABELS),
                          style={"fontWeight": "700", "color": BRAND, "fontSize": "12px"}),
                html.Span(f"  ·  {scope_label}  ·  {year}",
                          style={"color": "#888", "fontSize": "11px"}),
            ]),
            html.Span(f"{n_grey} greyed (not enough measured data)",
                      style={"fontSize": "10px", "color": "#95a5a6"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "center", "padding": "8px 14px",
                  "background": "#f8f9fa", "borderBottom": "1px solid #e4e4e4"}),

        html.Div([
            stat("Countries shown", n_shown, sub=f"of {len(frame)}"),
            stat("Average", f"{avg:.1f}" if pd.notna(avg) else "—", sub="0–100"),
            stat("Greyed", n_grey, sub="insufficient data", colour="#95a5a6"),
            stat("Year", year, sub=f"panel {PANEL.panel_start}–{PANEL.panel_end}"),
        ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap", "padding": "10px 14px"}),

        # The continent time slider. The goalposts are frozen across the whole
        # panel, which is what makes dragging this honest: a country moves only
        # when its own data moves, never because the comparison set changed.
        html.Div([
            year_slider("overview", year,
                        caption="— the whole map, this year"),
            year_coverage_note(year, n_shown, len(frame)),
            rec_membership_caveat(group_mode, group_key, year),
        ], style={"padding": "0 14px"}),

        html.Div([
            html.Div([
                html.H4("Highest", style={"fontSize": "11px", "color": "#27ae60",
                                          "fontWeight": "700", "margin": "0 0 6px"}),
                *mini(ranked.head(5), "#27ae60"),
                html.H4("Lowest", style={"fontSize": "11px", "color": "#c0392b",
                                         "fontWeight": "700", "margin": "14px 0 6px"}),
                *mini(ranked.tail(5), "#c0392b"),
                html.P("Select a country on the map to open its profile.",
                       style={"fontSize": "9px", "color": "#bbb", "marginTop": "12px"}),
            ], style={"width": "185px", "flexShrink": 0}),
            # Pattern-matching id, not a plain one: this graph exists only on the
            # Explore tab, and a plain Input naming a component that is not in the
            # current layout makes Dash refuse to run the whole callback.
            dcc.Graph(id={"type": "ov-map", "index": "main"}, figure=fig_map(frame, lens),
                      config={"displayModeBar": False},
                      style={"flex": "1", "height": "500px"}),
        ], style={"display": "flex", "gap": "10px", "padding": "0 14px 14px"}),
    ])


def view_country(iso3: str, lens: D.Lens, year: int):
    meta = PANEL.countries.get(iso3, {})
    name = meta.get("name", iso3)
    method = lens.key if lens.kind == "composite" else "equal"
    record = NARRATIVE.get(iso3)

    comp = D.country_composite_series(PANEL, iso3, method)
    row = comp[comp["year"] == year]
    row = row.iloc[0] if not row.empty else None

    pillars = D.country_pillar_series(PANEL, iso3)
    at_year = pillars[pillars["year"] == year].set_index("pillar_id")

    cards = []
    for pid, pname in PILLAR_DEFS.items():
        r = at_year.loc[pid] if pid in at_year.index else None
        shown = r is not None and r["reliability"] in D.DISPLAYABLE and pd.notna(r["score"])
        value = f"{r['score']:.1f}" if shown else "—"
        colour = ("#27ae60" if shown and r["score"] >= 65 else
                  "#e67e22" if shown and r["score"] >= 35 else
                  "#c0392b" if shown else "#b0b7bd")
        has_prose = record is not None and record.pillar(pid) is not None
        # Why a card may carry no ¶: the corpus does not write prose for a pillar
        # the index refused to score. Stating that on the card itself stops the
        # gap reading as a missing section the reader has to click to discover.
        prose_note = ("Written commentary available" if has_prose else
                      "No commentary: the index did not score this pillar, and the "
                      "corpus does not write prose the data cannot support"
                      if not shown else
                      "No commentary written for this pillar yet")
        cards.append(html.Button([
            html.Div([
                html.Span(f"{pid}", style={"fontWeight": "700", "fontSize": "11px",
                                           "color": BRAND}),
                html.Span("¶" if has_prose else "—", title=prose_note,
                          style={"fontSize": "10px",
                                 "color": BRAND_LIGHT if has_prose else "#ccc",
                                 "float": "right"}),
            ]),
            html.Div(pname, style={"fontSize": "9px", "color": "#666",
                                   "lineHeight": "1.25", "minHeight": "24px"}),
            html.Div(value, style={"fontSize": "20px", "fontWeight": "700",
                                   "color": colour, "marginTop": "3px"}),
            tier_badge(r["reliability"] if r is not None else "absent",
                       r["coverage_ratio"] if r is not None else None),
        ], id={"type": "pillar-btn", "index": pid}, n_clicks=0,
            style={"background": "#fafafa", "border": f"2px solid {colour}",
                   "borderRadius": "8px", "padding": "9px", "cursor": "pointer",
                   "textAlign": "left", "width": "calc(14.2% - 6px)",
                   "minWidth": "104px", "opacity": "1" if shown else "0.55"}))

    headline = (f"{row['score']:.1f}" if row is not None
                and row["reliability"] in D.DISPLAYABLE and pd.notna(row["score"]) else "—")
    rank = (f"#{int(row['rank'])}" if row is not None and pd.notna(row["rank"]) else "—")

    return html.Div([
        breadcrumb([("Overview", "overview"), (name, None)]),
        html.Div([
            html.Div([
                html.H2(name, style={"margin": 0, "fontSize": "19px",
                                     "fontWeight": "700", "color": BRAND}),
                html.Div(f"{meta.get('region', '')} Africa"
                         + (f"  ·  {', '.join(meta.get('recs', []))}"
                            if meta.get("recs") else ""),
                         style={"fontSize": "11px", "color": "#888", "marginTop": "2px"}),
            ]),
            html.Div([
                stat(f"{METHOD_LABELS.get(method, method)} ({year})", headline),
                stat("Rank", rank, sub="in scope"),
                stat("Pillars shown",
                     int(at_year["reliability"].isin(D.DISPLAYABLE).sum())
                     if not at_year.empty else 0, sub=f"of {len(PILLAR_DEFS)}"),
            ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "flex-start", "gap": "14px", "flexWrap": "wrap",
                  "borderBottom": "1px solid #eee", "paddingBottom": "10px"}),

        unreliable_banner(row["reliability"] if row is not None else "absent", None, year),

        # The country slider carries the same scale as the continent one, with
        # this country's recorded events drawn onto it.
        html.Div([
            year_slider(
                "country", year,
                caption="— carries into every pillar and indicator below",
                marks=N.slider_marks(record, PANEL.panel_start, PANEL.panel_end),
                trailing=html.Span(
                    [html.Span("▲ improve  ", style={"color": "#27ae60"}),
                     html.Span("▼ deteriorate  ", style={"color": "#c0392b"}),
                     html.Span("◆ mixed", style={"color": "#e67e22"})],
                    style={"fontSize": "9px", "fontWeight": "700", "marginLeft": "auto"},
                ) if record and record.events_in(PANEL.panel_start, PANEL.panel_end) else None,
            ),
            N.year_event_callout(record, year),
        ]),

        html.Div([
            html.H4(f"{METHOD_LABELS.get(method, method)} over time",
                    style={"fontSize": "11px", "fontWeight": "600", "margin": "0 0 2px"}),
            dcc.Graph(figure=fig_country_series(comp, year, name),
                      config={"displayModeBar": False}),
        ]),

        html.P([
            "Seven pillars — select one to see its indicators.  ",
            html.Span("¶", style={"color": BRAND_LIGHT, "fontWeight": "700"}),
            " marks a pillar with written commentary; ",
            html.Span("—", style={"color": "#ccc", "fontWeight": "700"}),
            " means none, because the index did not score that pillar here.",
        ], style={"fontSize": "10px", "color": "#aaa", "margin": "10px 0 6px"}),
        html.Div(cards, style={"display": "flex", "gap": "6px", "flexWrap": "wrap"}),

        render_context(iso3, record),
    ], style={"padding": "10px 14px"})


def view_pillar(iso3: str, pillar_id: str, year: int):
    name = PANEL.countries.get(iso3, {}).get("name", iso3)
    pname = PILLAR_DEFS.get(pillar_id, pillar_id)
    record = NARRATIVE.get(iso3)

    series = D.country_pillar_series(PANEL, iso3)
    series = series[series["pillar_id"] == pillar_id]
    at_year = series[series["year"] == year]
    r = at_year.iloc[0] if not at_year.empty else None

    inds = D.country_indicators(PANEL, iso3, year, pillar_id)

    rows = []
    for x in inds.itertuples():
        has = pd.notna(x.score)
        prov = str(x.provenance)
        rows.append(html.Div([
            html.Div([
                # identity rendered straight off the row — no registry lookup
                html.Div(x.display_name, style={"fontSize": "11px", "fontWeight": "600",
                                                "color": "#333"}),
                html.Div(f"{x.series_code}  ·  {prov.replace('_', ' ')}"
                         + (f" from {int(x.source_year)}"
                            if pd.notna(x.source_year) and x.source_year != x.year else ""),
                         style={"fontSize": "9px", "color": "#aaa"}),
            ], style={"flex": 1}),
            html.Div([
                html.Div(f"{x.raw_value:,.2f}" if pd.notna(x.raw_value) else "—",
                         style={"fontSize": "15px", "fontWeight": "700",
                                "textAlign": "right", "color": "#222"}),
                html.Div(f"score {x.score:.1f}" if has else "no score",
                         style={"fontSize": "9px", "color": "#888", "textAlign": "right"}),
            ], style={"minWidth": "110px"}),
        ], style={"display": "flex", "gap": "10px", "padding": "7px 0",
                  "borderBottom": "1px solid #f5f5f5",
                  "opacity": "1" if prov == "observed" else "0.68"}))

    return html.Div([
        breadcrumb([("Overview", "overview"), (name, "country"),
                    (f"{pillar_id}: {pname}", None)]),
        html.Div([
            html.H2(f"{pname}", style={"margin": 0, "fontSize": "17px",
                                       "fontWeight": "700", "color": BRAND}),
            html.Div(f"{name}  ·  {year}",
                     style={"fontSize": "11px", "color": "#888"}),
        ]),
        unreliable_banner(r["reliability"] if r is not None else "absent",
                          r["coverage_ratio"] if r is not None else None, year),
        html.Div([
            stat("Pillar score",
                 f"{r['score']:.1f}" if r is not None and r["reliability"] in D.DISPLAYABLE
                 and pd.notna(r["score"]) else "—"),
            stat("Measured", f"{int(r['n_observed'])}/{int(r['n_indicators'])}"
                 if r is not None else "—", sub="indicators"),
            stat("Inferred", int(r["n_imputed"]) if r is not None else "—",
                 sub="carried or regional", colour="#e67e22"),
        ], style={"display": "flex", "gap": "8px", "margin": "10px 0"}),

        # the prose explaining the number the reader has just seen
        N.pillar_narrative_block(
            record, pillar_id, pname,
            displayable=bool(r is not None and r["reliability"] in D.DISPLAYABLE),
        ),

        html.Div([
            html.H4("Over time", style={"fontSize": "11px", "fontWeight": "600",
                                        "margin": "0 0 2px"}),
            dcc.Graph(figure=fig_country_series(series, year, pname),
                      config={"displayModeBar": False}),
        ]),

        html.H4(f"Indicators in {year}",
                style={"fontSize": "11px", "fontWeight": "600", "margin": "12px 0 4px"}),
        html.P("Faded rows were estimated rather than measured in this year.",
               style={"fontSize": "9px", "color": "#aaa", "margin": "0 0 6px"}),
        html.Div(rows),
    ], style={"padding": "10px 14px"})


def render_context(iso3: str, record=None):
    """
    Everything about a country that is not a number: structured facts, colonial
    history, and the narrative record.

    Ordering follows what a reader asks in sequence — what is this place, what
    happened to it, what is happening now, what is this record's own standing.

    Where the narrative record covers ground the context YAMLs also cover, the
    record wins and the YAML's prose is dropped rather than printed twice: the
    narrative version is longer, cited, and validated. The YAML's *structured*
    fields (which powers colonised the country) are kept, because those are
    facts the narrative does not restate in machine-readable form.
    """
    ch = COLONIAL.get(iso3) or {}
    facts = COUNTRY_FACTS.get(iso3) or {}
    qual = QUAL_NOTES.get(iso3) or {}
    blocks = []

    if facts:
        chips = []
        for label, key, unit in (("Capital", "capital", ""),
                                 ("Population", "population_m", "m"),
                                 ("Area", "area_km2", "km²"),
                                 ("Currency", "currency", "")):
            if facts.get(key):
                v = facts[key]
                v = f"{v:,.1f}" if isinstance(v, float) else f"{v:,}" if isinstance(v, int) else v
                chips.append(html.Div([
                    html.Div(label, style={"fontSize": "9px", "color": "#999"}),
                    html.Div(f"{v} {unit}".strip(),
                             style={"fontSize": "13px", "fontWeight": "700"}),
                ], style={"background": "#fff", "border": "1px solid #e8e8e8",
                          "borderRadius": "6px", "padding": "7px 11px"}))
        if chips:
            blocks.append(html.Div(chips, style={"display": "flex", "gap": "8px",
                                                 "flexWrap": "wrap"}))

    if ch:
        note = (ch.get("colonial_note") or "").strip()
        colonisers = [c for c in [ch.get("primary_colonizer")]
                      + (ch.get("other_colonizers") or []) if c and c.lower() != "none"]
        years = ch.get("years_colonized")
        # The narrative record's colonial_legacy expands exactly this note, with
        # citations. Printing both would say the same thing twice, worse the
        # second time, so the note yields when a record exists.
        show_note = bool(note) and (record is None or not record.colonial_legacy)
        blocks.append(html.Div([
            html.H4("Colonial record",
                    style={"fontSize": "11px", "fontWeight": "700", "color": "#666",
                           "textTransform": "uppercase", "letterSpacing": ".06em",
                           "margin": "0 0 6px"}),
            html.Div(f"Colonised by {', '.join(colonisers)}"
                     + (f"  ·  {years} years" if years else "")
                     if colonisers else "Never formally colonised",
                     style={"fontSize": "11px", "fontWeight": "600", "color": "#444"}),
            html.P(note, style={"fontSize": "10px", "color": "#555",
                                "lineHeight": 1.6, "margin": "6px 0 0"}) if show_note else None,
            html.Div("Historical context only — not part of the score.",
                     style={"fontSize": "9px", "color": "#aaa", "marginTop": "6px"}),
        ], style={"background": "#fafafa", "border": "1px solid #e4e4e4",
                  "borderLeft": "4px solid #8e44ad", "borderRadius": "8px",
                  "padding": "12px 14px"}))

    # ── the narrative record ───────────────────────────────────────────────────
    if record is None:
        blocks.append(N.no_record_notice(PANEL.countries.get(iso3, {}).get("name", iso3)))
    else:
        blocks += N.history_block(record)
        for block in (N.recent_block(record),
                      N.events_block(record, PANEL.panel_start, PANEL.panel_end),
                      N.rec_membership_block(record),
                      N.balance_block(record),
                      N.sources_block(record)):
            if block is not None:
                blocks.append(block)
        blocks.append(N.record_footer(record))

    # Hand-written analyst notes, where any exist. The scaffolding ships with 54
    # empty stubs, so this renders only once someone has actually written one.
    overview = (qual.get("overview") or "").strip()
    if overview:
        blocks.append(html.Div([
            html.H4("Analyst notes",
                    style={"fontSize": "11px", "fontWeight": "700", "color": "#666",
                           "textTransform": "uppercase", "letterSpacing": ".06em",
                           "margin": "0 0 6px"}),
            html.P(overview, style={"fontSize": "12px", "lineHeight": 1.7, "margin": 0}),
        ], style={"background": "#fafafa", "border": "1px solid #e4e4e4",
                  "borderLeft": f"4px solid {BRAND_LIGHT}", "borderRadius": "8px",
                  "padding": "12px 14px"}))

    if not blocks:
        return html.Div()
    return html.Div(blocks, style={"display": "flex", "flexDirection": "column",
                                   "gap": "10px", "marginTop": "14px"})


def view_rankings(lens: D.Lens, group_mode, group_key, exclude_islands, year):
    frame = D.apply_grouping(D.choropleth_frame(PANEL, lens, year),
                             group_mode, group_key, exclude_islands=exclude_islands)
    ranked = D.rankings(frame)
    hidden = frame[~(frame["displayable"] & frame["in_scope"])]

    header = ["#", "Country", "Region", "Score", "Data quality"]
    rows = [html.Tr([html.Th(h, style={"textAlign": "left", "padding": "6px 10px",
                                       "background": BRAND, "color": "#fff",
                                       "fontSize": "10px"}) for h in header])]
    for r in ranked.itertuples():
        rows.append(html.Tr([
            html.Td(int(r.scope_rank), style={"padding": "5px 10px", "fontSize": "11px"}),
            html.Td(r.name, style={"padding": "5px 10px", "fontSize": "11px",
                                   "fontWeight": "600"}),
            html.Td(r.region, style={"padding": "5px 10px", "fontSize": "10px",
                                     "color": "#777"}),
            html.Td(f"{r.score:.1f}", style={"padding": "5px 10px", "fontSize": "11px"}),
            html.Td(tier_badge(r.reliability, r.coverage_ratio),
                    style={"padding": "5px 10px"}),
        ]))

    return html.Div([
        html.Div(f"{lens.label(METHOD_LABELS)} · {year} · {len(ranked)} ranked, "
                 f"{len(hidden)} not shown",
                 style={"fontSize": "10px", "color": "#888", "padding": "8px 14px",
                        "background": "#f8f9fa", "borderBottom": "1px solid #e4e4e4"}),
        html.Div([
            year_slider("rankings", year, caption="— re-ranks the table below"),
            year_coverage_note(year, len(ranked), len(frame)),
            rec_membership_caveat(group_mode, group_key, year),
        ], style={"padding": "0 14px"}),
        html.Div(html.Table(rows, style={"width": "100%", "borderCollapse": "collapse"}),
                 style={"padding": "10px 14px"}),
        html.Div([
            html.H4("Not shown", style={"fontSize": "11px", "fontWeight": "700",
                                        "color": "#7f8c8d", "margin": "0 0 4px"}),
            html.P(", ".join(hidden["name"].tolist()) or "None",
                   style={"fontSize": "10px", "color": "#95a5a6", "lineHeight": 1.6}),
            html.P("Excluded either by the current comparison or because too much "
                   "of the underlying data is inferred rather than measured.",
                   style={"fontSize": "9px", "color": "#bbb"}),
        ], style={"padding": "0 14px 16px"}) if not hidden.empty else None,
    ])


def view_methodology():
    """
    How a score is built, in the order it is built.

    Written for a reader who wants to check the index rather than trust it, so
    every claim points at the file that implements it.
    """
    w = PANEL.meta.get("weights", {})

    def step(n, title, body):
        return html.Div([
            html.Div([
                html.Span(str(n), style={"background": BRAND, "color": "#fff",
                                         "borderRadius": "50%", "width": "20px",
                                         "height": "20px", "display": "inline-flex",
                                         "alignItems": "center", "justifyContent": "center",
                                         "fontSize": "10px", "fontWeight": "700",
                                         "flexShrink": 0}),
                html.Span(title, style={"fontWeight": "700", "fontSize": "12px",
                                        "color": BRAND, "marginLeft": "8px"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"}),
            html.Div(body, style={"fontSize": "11px", "color": "#555", "lineHeight": 1.65,
                                  "paddingLeft": "28px"}),
        ], style={"marginBottom": "14px"})

    weight_rows = [html.Tr([html.Th(h, style={"textAlign": "left", "padding": "5px 9px",
                                              "fontSize": "10px", "background": "#f0f4f8"})
                            for h in ["Pillar", "Equal", "PCA", "Entropy"]])]
    for pid, pname in PILLAR_DEFS.items():
        weight_rows.append(html.Tr([
            html.Td(f"{pid} · {pname}", style={"padding": "4px 9px", "fontSize": "10px"}),
            *[html.Td(f"{w.get(k, {}).get(pid, 0) * 100:.1f}%",
                      style={"padding": "4px 9px", "fontSize": "10px",
                             "color": "#c0392b" if w.get(k, {}).get(pid, 0) == 0 else "#333"})
              for k in ("equal", "pca", "entropy")],
        ]))

    return html.Div([
        html.H3("How a score is built", style={"fontSize": "14px", "color": BRAND,
                                               "margin": "0 0 12px"}),

        step(1, "One value per country, per indicator, per year",
             "Each indicator declares how its yearly value is drawn from the source "
             "series — the most recent observation, or a rolling mean. Where a year "
             "has no observation, the last real measurement is carried forward for at "
             "most five years and labelled as such. Older than that and the cell is "
             "left empty: a fifteen-year-old number is not evidence about this year. "
             "(asi/pipeline/panel.py)"),

        step(2, "Gaps filled from regional peers, or not at all",
             "A missing value may be estimated from the same region in the same year, "
             "but only where at least three peers reported. Filled values are marked "
             "as estimates and never counted as measurements. (asi/pipeline/panel.py)"),

        step(3, "Transformed, capped, then scaled against fixed goalposts",
             "Skewed indicators are log-transformed, then extreme values are capped at "
             "two times the interquartile range, then values are mapped onto 0–100. "
             "The bounds are computed once across every country and every year and then "
             "frozen. This is what makes the time slider honest: a country's score moves "
             "only when its own data moves, never because other countries changed. "
             "(registry/goalposts.yaml)"),

        step(4, "Pillars, with their coverage attached",
             "A pillar is the mean of its available indicator scores, and it reports how "
             "many of its indicators were actually measured. Below 60% measured it is "
             "shown muted; below 40%, or where estimates outnumber measurements, it is "
             "not shown at all. (asi/pipeline/score.py)"),

        step(5, "Composites, with the weighting fixed in advance",
             "Pillars combine into an overall score. PCA and entropy weights are fitted "
             "once across the pooled panel and reused for every year — refitting them "
             "annually would move a country's score because the weighting changed rather "
             "than because the country did."),

        html.H4("Pillar weights actually in use",
                style={"fontSize": "12px", "color": BRAND, "margin": "16px 0 6px"}),
        html.Table(weight_rows, style={"borderCollapse": "collapse", "width": "100%",
                                       "maxWidth": "520px"}),
        html.P("A zero weight means that pillar loads against the stability dimension in "
               "the principal-component fit and is excluded rather than inverted. PCA and "
               "entropy currently disagree sharply about the Environmental pillar, which "
               "is an open methodological question, not a settled result.",
               style={"fontSize": "10px", "color": "#888", "lineHeight": 1.6,
                      "marginTop": "6px", "maxWidth": "620px"}),

        html.H4("What the data-quality labels mean",
                style={"fontSize": "12px", "color": BRAND, "margin": "16px 0 6px"}),
        html.Div([
            html.Div([tier_badge(t), html.Span(D.reliability_note(t),
                                               style={"fontSize": "10px", "color": "#555",
                                                      "marginLeft": "8px"})],
                     style={"display": "flex", "alignItems": "center", "marginBottom": "5px"})
            for t in ("reliable", "thin", "unreliable", "absent")
        ]),

        html.H4("Which countries are in scope",
                style={"fontSize": "12px", "color": BRAND, "margin": "16px 0 6px"}),
        html.P([
            f"The African Union has {len(PANEL.countries) + len(EXCLUDED_AU_MEMBERS)} "
            f"member states. This index scores {len(PANEL.countries)}. The exclusion "
            f"is ",
            html.B("Western Sahara"),
            f" ({EXCLUDED_AU_MEMBERS['Western Sahara']}).",
        ], style={"fontSize": "11px", "color": "#555", "lineHeight": 1.65,
                  "maxWidth": "660px", "margin": "0 0 6px"}),
        html.P(f"It is excluded on data availability, not on any position about the "
               f"territory's status. The World Bank publishes no WDI or WGI series for "
               f"Western Sahara: it has no entry in the source databases this index is "
               f"built from, so all {N_SCORING} scoring indicators would have to be "
               f"imputed from regional peers. That would produce a score with zero "
               f"measured inputs — which the reliability rules exist precisely to "
               f"refuse to display. Including it would mean showing a country-shaped "
               f"hole coloured as though it were evidence.",
               style={"fontSize": "11px", "color": "#555", "lineHeight": 1.65,
                      "maxWidth": "660px", "margin": "0 0 6px"}),
        html.P("The dispute itself is not omitted: it is documented in the narrative "
               "records for Morocco (the 1975 Green March, the 1991 ceasefire, the "
               "unheld referendum, and the 2025 Security Council vote on autonomy) and "
               "for Algeria (roughly 174,000 Sahrawi refugees hosted at Tindouf for five "
               "decades). What the index will not do is assign the territory a stability "
               "score it has no data to support.",
               style={"fontSize": "11px", "color": "#555", "lineHeight": 1.65,
                      "maxWidth": "660px", "margin": "0 0 6px"}),

        html.H4("Known limitations", style={"fontSize": "12px", "color": BRAND,
                                            "margin": "16px 0 6px"}),
        html.Ul([
            html.Li("Six governance indicators from one source family carry roughly a "
                    "third of the composite weight."),
            html.Li("Indicators counted in more than one pillar carry more weight than "
                    "single-pillar ones."),
            html.Li("2001 has no governance observation: the source was biennial before "
                    "2002, so that year is largely estimated."),
            html.Li(f"The panel runs to {PANEL.panel_end}, but the most recent year with "
                    f"enough reported data to score is {PANEL.reference_year}."),
            html.Li("Scores are comparable across years and countries, but only within "
                    "one edition: regenerating the goalposts would re-anchor everything."),
        ], style={"fontSize": "10px", "color": "#555", "lineHeight": 1.8,
                  "paddingLeft": "18px", "maxWidth": "660px"}),
    ], style={"padding": "16px 18px", "maxWidth": "900px"})


def view_sources():
    """Full indicator provenance — the answer to 'where did this number come from?'"""
    rows = [html.Tr([html.Th(h, style={"textAlign": "left", "padding": "6px 9px",
                                       "background": BRAND, "color": "#fff",
                                       "fontSize": "10px", "position": "sticky", "top": 0})
                     for h in ["Indicator", "Series code", "Source", "Pillars",
                               "Direction", "Transform"]])]

    for var, meta in sorted(PANEL.indicators.items(),
                            key=lambda kv: kv[1].get("display_name", kv[0])):
        if meta.get("role") != "scoring":
            continue
        pillars = ", ".join(meta.get("pillars", []))
        direction = ("higher is better" if meta.get("polarity") == "positive"
                     else "lower is better")
        transforms = []
        if meta.get("log_transform"):
            transforms.append("log")
        if meta.get("transform"):
            transforms.append(meta["transform"].replace("_", " "))
        rows.append(html.Tr([
            html.Td(meta.get("display_name", var),
                    style={"padding": "5px 9px", "fontSize": "10px", "fontWeight": "600"}),
            html.Td(meta.get("series_code", ""),
                    style={"padding": "5px 9px", "fontSize": "9px",
                           "fontFamily": "monospace", "color": "#666"}),
            html.Td(meta.get("database", "").upper(),
                    style={"padding": "5px 9px", "fontSize": "9px", "color": "#777"}),
            html.Td(pillars, style={"padding": "5px 9px", "fontSize": "9px",
                                    "color": "#c0392b" if "," in pillars else "#777"}),
            html.Td(direction, style={"padding": "5px 9px", "fontSize": "9px",
                                      "color": "#777"}),
            html.Td(", ".join(transforms) or "—",
                    style={"padding": "5px 9px", "fontSize": "9px", "color": "#777"}),
        ]))

    n_cross = sum(1 for m in PANEL.indicators.values()
                  if m.get("role") == "scoring" and len(m.get("pillars", [])) > 1)

    return html.Div([
        html.Div([
            html.P(f"{N_SCORING} scoring indicators from the World Bank's World "
                   f"Development Indicators and Worldwide Governance Indicators. "
                   f"{n_cross} are counted in more than one pillar and therefore carry "
                   f"more weight than the rest — shown in red.",
                   style={"fontSize": "11px", "color": "#555", "margin": 0,
                          "maxWidth": "760px", "lineHeight": 1.6}),
        ], style={"padding": "10px 14px", "background": "#f8f9fa",
                  "borderBottom": "1px solid #e4e4e4"}),
        html.Div(html.Table(rows, style={"borderCollapse": "collapse", "width": "100%"}),
                 style={"padding": "10px 14px", "maxHeight": "70vh", "overflowY": "auto"}),
    ])


# ── Layout ─────────────────────────────────────────────────────────────────────

def lens_options():
    """One vocabulary for 'what am I looking at', grouped by prefix."""
    opts = [{"label": f"Overall — {METHOD_LABELS.get(m, m)}", "value": f"composite:{m}"}
            for m in PANEL.methods]
    opts += [{"label": f"Pillar {p} — {n}", "value": f"pillar:{p}"}
             for p, n in PILLAR_DEFS.items()]
    return opts


def compare_options():
    opts = [{"label": "All of Africa", "value": "all:"}]
    opts += [{"label": f"Region — {r}", "value": f"region:{r}"}
             for r in ACTIVE_PROFILE.subregions]
    opts += [{"label": f"Community — {c}", "value": f"rec:{c}"}
             for c in ACTIVE_PROFILE.communities]
    return opts


def build_layout():
    return html.Div([
        html.Div([
            html.Div([
                html.H1("African Stability Index",
                        style={"color": "#fff", "margin": 0, "fontSize": "19px",
                               "fontWeight": "700"}),
                html.Div(f"{len(PANEL.countries)} of 55 AU member states  ·  "
                         f"{len(PILLAR_DEFS)} pillars  ·  "
                         f"{N_SCORING} indicators"
                         f"  ·  {PANEL.panel_start}–{PANEL.panel_end}",
                         title="Western Sahara (SADR) is an AU member state but is not "
                               "scored: the World Bank publishes no WDI or WGI series "
                               "for the territory, so every indicator would be imputed. "
                               "See Methodology.",
                         style={"color": "#9bb8d4", "fontSize": "10px", "marginTop": "2px"}),
            ]),
            html.Div("0 = most fragile · 100 = most stable",
                     style={"color": "#9bb8d4", "fontSize": "10px"}),
        ], style={"background": BRAND, "padding": "10px 18px", "display": "flex",
                  "justifyContent": "space-between", "alignItems": "center"}),

        # exactly two controls
        html.Div([
            html.Div([
                html.Label("Showing", style={"fontSize": "11px", "fontWeight": "600",
                                             "color": "#555", "marginRight": "6px"}),
                dcc.Dropdown(id="lens", options=lens_options(),
                             value="composite:equal", clearable=False,
                             style={"width": "260px"}),
            ], style={"display": "flex", "alignItems": "center", "gap": "4px"}),
            html.Div([
                html.Label("Compare", style={"fontSize": "11px", "fontWeight": "600",
                                             "color": "#555", "marginRight": "6px"}),
                dcc.Dropdown(id="compare", options=compare_options(),
                             value="all:", clearable=False,
                             style={"width": "230px"}),
            ], style={"display": "flex", "alignItems": "center", "gap": "4px"}),
            dcc.Checklist(id="islands", options=[{"label": " Exclude island states",
                                                  "value": "x"}], value=[],
                          labelStyle={"fontSize": "10px", "color": "#777"}),
        ], style={"display": "flex", "alignItems": "center", "gap": "20px",
                  "padding": "8px 18px", "background": "#f4f6f8",
                  "borderBottom": "1px solid #e4e4e4", "flexWrap": "wrap"}),

        dcc.Store(id="nav", data={"level": "overview", "iso3": None, "pillar": None,
                                  "year": PANEL.reference_year}),
        dcc.Store(id="map-click"), dcc.Store(id="nav-event"),

        html.Div([
            dcc.Tabs(id="tabs", value="explore", children=[
                dcc.Tab(label="Explore", value="explore"),
                dcc.Tab(label="Rankings", value="rankings"),
                dcc.Tab(label="Methodology", value="methodology"),
                dcc.Tab(label="Data sources", value="sources"),
            ]),
            html.Div(id="content"),
        ], style={"maxWidth": "1450px", "margin": "0 auto", "padding": "0 6px"}),
    ], style={"fontFamily": "'Segoe UI',system-ui,sans-serif", "background": "#fff",
              "minHeight": "100vh"})


# ── App ────────────────────────────────────────────────────────────────────────

def create_app() -> Dash:
    app = Dash(__name__,
               assets_folder=str(PROJECT_ROOT / "assets"),
               external_stylesheets=[dbc.themes.FLATLY],
               title="African Stability Index",
               suppress_callback_exceptions=True)

    # Cap the request body. Dash posts callback state to /_dash-update-component,
    # and the largest legitimate payload this app sends is a few KB — but Flask
    # will otherwise buffer a body of any size in memory before parsing it, so an
    # unauthenticated client could exhaust a small container with two requests.
    app.server.config["MAX_CONTENT_LENGTH"] = 1_000_000

    app.layout = build_layout()

    @app.callback(Output("content", "children"),
                  Input("tabs", "value"), Input("nav", "data"),
                  Input("lens", "value"), Input("compare", "value"),
                  Input("islands", "value"))
    def render(tab, nav, lens_value, compare_value, islands):
        lens = D.Lens.parse(lens_value)
        mode, _, key = (compare_value or "all:").partition(":")
        excl = bool(islands)
        year = int(nav.get("year", PANEL.reference_year))

        if tab == "rankings":
            return view_rankings(lens, mode, key or None, excl, year)
        if tab == "methodology":
            return view_methodology()
        if tab == "sources":
            return view_sources()
        level = nav.get("level", "overview")
        if level == "country":
            return view_country(nav["iso3"], lens, year)
        if level == "pillar":
            return view_pillar(nav["iso3"], nav["pillar"], year)
        return view_overview(lens, mode, key or None, excl, year)

    @app.callback(Output("map-click", "data"),
                  Input({"type": "ov-map", "index": ALL}, "clickData"),
                  prevent_initial_call=True)
    def relay_map(clicks):
        """
        Relay the first real map click.

        Matching on a pattern rather than a fixed id is what lets the map be
        absent — on Rankings, Methodology or a country page — without Dash
        treating the callback as referring to a nonexistent component.
        """
        for c in clicks or []:
            if c:
                return c
        return no_update

    @app.callback(Output("nav-event", "data"),
                  Input({"type": "pillar-btn", "index": ALL}, "n_clicks"),
                  Input({"type": "crumb", "index": ALL}, "n_clicks"),
                  prevent_initial_call=True)
    def relay_click(_p, _c):
        tid = callback_context.triggered_id
        if not isinstance(tid, dict):
            return no_update
        value = (callback_context.triggered or [{}])[0].get("value", 0)
        if not value:
            return no_update
        return {"type": tid.get("type"), "index": tid.get("index"), "n": value}

    @app.callback(Output("nav", "data"),
                  Input("map-click", "data"), Input("nav-event", "data"),
                  Input({"type": "year-slider", "index": ALL}, "value"),
                  State("nav", "data"), prevent_initial_call=True)
    def navigate(click, event, slider_years, nav):
        tid = callback_context.triggered_id
        nav = dict(nav)

        # The year persists across every view: set it on the continent map and it
        # carries into rankings, into a country page, and down into a pillar.
        # Read the value off the component that actually fired rather than the
        # first match, so the sliders cannot fight each other during a re-render.
        if isinstance(tid, dict) and tid.get("type") == "year-slider":
            fired = (callback_context.triggered or [{}])[0].get("value")
            if fired is None:
                fired = next((y for y in (slider_years or []) if y is not None), None)
            if fired is None:
                return no_update
            nav["year"] = int(fired)
            return nav

        if tid == "map-click" and click:
            iso3 = click["points"][0].get("location")
            if iso3 in PANEL.countries:
                return {**nav, "level": "country", "iso3": iso3}

        if tid == "nav-event" and event:
            if event["type"] == "crumb":
                return {**nav, "level": event["index"]}
            if event["type"] == "pillar-btn":
                return {**nav, "level": "pillar", "pillar": event["index"]}
        return no_update

    return app


app = create_app()
server = app.server


def main() -> int:
    """
    Development server. Production runs `gunicorn app:server`, which imports
    `server` and never calls this.

    Binds loopback by default. `DEBUG=true` enables the Werkzeug debugger, which
    is remote code execution behind a PIN, so it is refused on any non-loopback
    host rather than left one environment variable away from being exposed.
    """
    port = int(os.environ.get("PORT", 8050))
    host = os.environ.get("HOST", "127.0.0.1")
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    if debug and host not in ("127.0.0.1", "localhost", "::1"):
        print(f"Refusing to start: DEBUG=true exposes the Werkzeug debugger and "
              f"HOST is {host!r}. Use HOST=127.0.0.1, or unset DEBUG.")
        return 2
    print(f"\nAfrican Stability Index — http://{host}:{port}\n")
    app.run(debug=debug, host=host, port=port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
