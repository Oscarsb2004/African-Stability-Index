"""
asi.dashboard.narrative_ui — rendering for the narrative layer.

The index says Chad ranks 51st. This module renders the half of the project that
says why. It is kept apart from `app.py` for the same reason `data.py` is: the
views should assemble blocks, not format prose inline.

Design rules specific to narrative rendering:

  1. **A sourced claim shows its source.** Every prose block that carries
     citations renders them next to the prose, not in a footnote nobody reaches.
     The corpus enforces citation-per-claim; hiding that in the UI would waste it.

  2. **Absence is stated, never faked.** A country without a record, a pillar the
     index greyed out, an event the slider cannot reach — each renders as an
     explicit sentence about what is missing and why, matching the panel's own
     "greyed, not blank" rule.

  3. **Framing balance is shown to the reader, not just counted in the file.**
     The corpus records how many positive, negative and mixed items a country
     has because coverage of Africa skews negative. A count kept in a YAML file
     nobody sees does not discharge that; showing it does.

  4. **Expandable sections use native <details>.** No callback, no component id,
     no state in the nav store — so a section can be opened on any country page
     without the interface having to remember which one is open.
"""

from __future__ import annotations

from dash import dcc, html

from asi.narrative.store import (
    Balance, Event, NarrativeRecord, PillarNarrative, RecentItem,
)

BRAND       = "#1B3A6B"
BRAND_LIGHT = "#2E6DB4"

SENTIMENT_STYLE = {
    "positive": ("#27ae60", "Positive"),
    "negative": ("#c0392b", "Negative"),
    "mixed":    ("#e67e22", "Mixed"),
}

DIRECTION_STYLE = {
    "improve":     ("#27ae60", "▲"),
    "deteriorate": ("#c0392b", "▼"),
    "mixed":       ("#e67e22", "◆"),
}

SOURCE_STYLE = {
    "wikipedia": "#7f8c8d",
    "news":      "#2E6DB4",
    "academic":  "#8e44ad",
    "official":  "#16a085",
}

CARD = {
    "background": "#fafafa", "border": "1px solid #e4e4e4",
    "borderRadius": "8px", "padding": "12px 14px",
}


# ── Small parts ────────────────────────────────────────────────────────────────

def section_heading(text: str, note: str | None = None):
    return html.Div([
        html.H4(text, style={"fontSize": "11px", "fontWeight": "700", "color": "#666",
                             "textTransform": "uppercase", "letterSpacing": ".06em",
                             "margin": 0}),
        html.Span(note, style={"fontSize": "9px", "color": "#aaa"}) if note else None,
    ], style={"display": "flex", "justifyContent": "space-between",
              "alignItems": "baseline", "marginBottom": "6px"})


def chip(text: str, colour: str, *, title: str | None = None):
    return html.Span(text, title=title,
                     style={"background": colour + "1a", "color": colour,
                            "fontWeight": "700", "fontSize": "9px",
                            "padding": "2px 7px", "borderRadius": "4px",
                            "whiteSpace": "nowrap"})


def source_links(record: NarrativeRecord, ids, *, label: str = "Sources"):
    """
    Inline citation list for one prose block.

    Rendered as numbered links rather than titles: a paragraph followed by five
    full source titles buries the paragraph.
    """
    cites = record.cite(ids)
    if not cites:
        return None
    parts = ([html.Span(f"{label}: ", style={"color": "#bbb", "fontSize": "9px"})]
             if label else [])
    for i, c in enumerate(cites):
        parts.append(html.A(
            c.domain,
            href=c.url, target="_blank", rel="noopener noreferrer",
            title=f"{c.title} — accessed {c.accessed}",
            style={"fontSize": "9px", "color": SOURCE_STYLE.get(c.source_type, "#888"),
                   "textDecoration": "underline", "marginRight": "7px"},
        ))
        if i < len(cites) - 1:
            parts.append(html.Span("·", style={"color": "#ddd", "fontSize": "9px",
                                               "marginRight": "7px"}))
    return html.Div(parts, style={"marginTop": "5px"})


def missing(text: str):
    """The honest empty state — says what is absent and why."""
    return html.Div(text, style={
        "fontSize": "10px", "color": "#95a5a6", "background": "#f4f6f7",
        "border": "1px solid #dfe4e6", "borderLeft": "4px solid #95a5a6",
        "borderRadius": "6px", "padding": "9px 13px",
    })


# ── History ────────────────────────────────────────────────────────────────────

def history_block(record: NarrativeRecord):
    """Overview, colonial legacy, and the key periods that produced them."""
    blocks = []

    if record.overview:
        blocks.append(html.Div([
            section_heading("Historical overview"),
            html.P(record.overview, style={"fontSize": "12px", "lineHeight": 1.75,
                                           "margin": 0, "color": "#333"}),
            source_links(record, record.overview_citations),
        ], style={**CARD, "borderLeft": f"4px solid {BRAND_LIGHT}"}))

    if record.colonial_legacy:
        blocks.append(html.Div([
            section_heading("Colonial legacy", "expands context/colonial_history.yaml"),
            html.P(record.colonial_legacy, style={"fontSize": "12px", "lineHeight": 1.75,
                                                  "margin": 0, "color": "#333"}),
            source_links(record, record.colonial_legacy_citations),
        ], style={**CARD, "borderLeft": "4px solid #8e44ad"}))

    if record.key_periods:
        rows = []
        for k in record.key_periods:
            rows.append(html.Div([
                html.Div([
                    html.Span(k.period, style={"fontSize": "10px", "fontWeight": "700",
                                               "color": BRAND, "fontFamily": "monospace"}),
                ], style={"minWidth": "84px", "flexShrink": 0}),
                html.Div([
                    html.Div(k.title, style={"fontSize": "11px", "fontWeight": "700",
                                             "color": "#333"}),
                    html.P(k.summary, style={"fontSize": "11px", "lineHeight": 1.65,
                                             "margin": "3px 0 0", "color": "#555"}),
                    source_links(record, k.citations),
                ], style={"flex": 1}),
            ], style={"display": "flex", "gap": "12px", "padding": "9px 0",
                      "borderBottom": "1px solid #f0f0f0"}))
        blocks.append(html.Div([
            section_heading("Key periods", f"{len(record.key_periods)} documented"),
            html.Div(rows),
        ], style={**CARD, "borderLeft": "4px solid #34495e"}))

    return blocks


# ── Recent developments ────────────────────────────────────────────────────────

def _recent_item(record: NarrativeRecord, item: RecentItem):
    colour, label = SENTIMENT_STYLE.get(item.sentiment, SENTIMENT_STYLE["mixed"])
    links = []
    if item.news_url:
        links.append(html.A("News source", href=item.news_url, target="_blank",
                            rel="noopener noreferrer",
                            style={"fontSize": "9px", "color": BRAND_LIGHT,
                                   "textDecoration": "underline", "marginRight": "10px"}))
    if item.wikipedia_url:
        links.append(html.A("Background", href=item.wikipedia_url, target="_blank",
                            rel="noopener noreferrer",
                            style={"fontSize": "9px", "color": "#7f8c8d",
                                   "textDecoration": "underline"}))

    return html.Div([
        html.Div([
            html.Span(item.date, style={"fontSize": "9px", "color": "#999",
                                        "fontFamily": "monospace"}),
            chip(label, colour),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "center", "marginBottom": "4px"}),
        html.Div(item.headline, style={"fontSize": "12px", "fontWeight": "700",
                                       "color": "#222", "lineHeight": 1.4}),
        html.P(item.summary, style={"fontSize": "11px", "lineHeight": 1.65,
                                    "margin": "5px 0 0", "color": "#555"}),
        html.Div([
            html.Span("Why it matters: ", style={"fontSize": "10px", "fontWeight": "700",
                                                 "color": colour}),
            html.Span(item.why_it_matters, style={"fontSize": "10px", "color": "#666",
                                                  "lineHeight": 1.6}),
        ], style={"marginTop": "6px"}) if item.why_it_matters else None,
        html.Div(links, style={"marginTop": "6px"}) if links else None,
    ], style={"background": "#fff", "border": "1px solid #e8e8e8",
              "borderLeft": f"3px solid {colour}", "borderRadius": "6px",
              "padding": "10px 12px"})


def recent_block(record: NarrativeRecord):
    """
    Three developments by default, the rest behind a native disclosure control.

    The blueprint fixes three as the default because a country page that opens
    with nine news items reads as a feed rather than as context for a score.
    """
    if not record.recent_primary and not record.recent_extended:
        return None

    items = [_recent_item(record, i) for i in record.recent_primary]

    extended = None
    if record.recent_extended:
        n = len(record.recent_extended)
        extended = html.Details([
            html.Summary(
                f"Show {n} further development{'s' if n > 1 else ''}",
                style={"fontSize": "10px", "color": BRAND_LIGHT, "cursor": "pointer",
                       "fontWeight": "600", "padding": "6px 0"},
            ),
            html.Div([_recent_item(record, i) for i in record.recent_extended],
                     style={"display": "flex", "flexDirection": "column",
                            "gap": "8px", "marginTop": "6px"}),
        ])

    return html.Div([
        section_heading(
            "Recent developments",
            f"{len(record.recent_primary)} shown"
            + (f" · {len(record.recent_extended)} more" if record.recent_extended else ""),
        ),
        html.Div(items, style={"display": "flex", "flexDirection": "column", "gap": "8px"}),
        extended,
    ], style={**CARD, "borderLeft": "4px solid #e67e22"})


# ── Events ─────────────────────────────────────────────────────────────────────

def _event_row(e: Event, *, reachable: bool):
    colour, glyph = DIRECTION_STYLE.get(e.direction, DIRECTION_STYLE["mixed"])
    title = (html.A(e.title, href=e.url, target="_blank", rel="noopener noreferrer",
                    style={"fontSize": "11px", "fontWeight": "700", "color": "#333",
                           "textDecoration": "underline"})
             if e.url else
             html.Span(e.title, style={"fontSize": "11px", "fontWeight": "700",
                                       "color": "#333"}))
    return html.Div([
        html.Div([
            html.Span(str(e.year), style={"fontSize": "11px", "fontWeight": "700",
                                          "color": BRAND, "fontFamily": "monospace"}),
            html.Span(glyph, style={"color": colour, "fontSize": "10px",
                                    "marginLeft": "5px"}),
        ], style={"minWidth": "58px", "flexShrink": 0}),
        html.Div([
            html.Div([title, chip(e.type.replace("_", " "), colour)],
                     style={"display": "flex", "gap": "8px", "alignItems": "center",
                            "flexWrap": "wrap"}),
            html.P(e.description, style={"fontSize": "10px", "lineHeight": 1.6,
                                         "margin": "3px 0 0", "color": "#666"}),
        ], style={"flex": 1}),
    ], style={"display": "flex", "gap": "10px", "padding": "8px 0",
              "borderBottom": "1px solid #f0f0f0",
              "opacity": "1" if reachable else "0.72"})


def events_block(record: NarrativeRecord, panel_start: int, panel_end: int):
    """
    Every recorded event, split by whether the slider can reach it.

    The split is the honest part. Most of this corpus's events predate the
    panel's first year, and presenting them together with in-panel events would
    imply the score reflects all of them.
    """
    if not record.events:
        return None

    inside = record.events_in(panel_start, panel_end)
    outside = record.events_outside(panel_start, panel_end)

    parts = [section_heading("Recorded events", f"{len(record.events)} total")]

    if inside:
        parts += [
            html.Div(f"Within the panel ({panel_start}–{panel_end}) — marked on the "
                     f"year slider above",
                     style={"fontSize": "9px", "color": "#888", "fontWeight": "600",
                            "margin": "2px 0 2px"}),
            html.Div([_event_row(e, reachable=True) for e in inside]),
        ]

    if outside:
        parts += [
            html.Div(f"Outside the panel — real history the score does not cover",
                     style={"fontSize": "9px", "color": "#aaa", "fontWeight": "600",
                            "margin": "12px 0 2px"}),
            html.Div([_event_row(e, reachable=False) for e in outside]),
        ]

    return html.Div(parts, style={**CARD, "borderLeft": "4px solid #c0392b"})


def slider_marks(record: NarrativeRecord | None, panel_start: int, panel_end: int,
                 *, every: int = 4) -> dict:
    """
    Year-slider marks: the regular scale, with recorded events called out.

    The blueprint asks for events as ticks on the country time slider. A year
    carrying an event gets its label coloured by direction and a marker glyph,
    so the reader can see *when* something happened before deciding where to
    drag — which is the whole point of putting them on the slider rather than
    only in a list below it.
    """
    marks = {
        y: {"label": str(y), "style": {"fontSize": "9px", "color": "#888"}}
        for y in range(panel_start, panel_end + 1, every)
    }
    if record is None:
        return marks

    for year, evs in record.event_years(panel_start, panel_end).items():
        if len(evs) == 1:
            colour, glyph = DIRECTION_STYLE.get(evs[0].direction, DIRECTION_STYLE["mixed"])
        else:
            dirs = {e.direction for e in evs}
            colour, glyph = (DIRECTION_STYLE[next(iter(dirs))] if len(dirs) == 1
                             else DIRECTION_STYLE["mixed"])
        marks[year] = {
            "label": f"{glyph}{year}",
            "style": {"fontSize": "9px", "color": colour, "fontWeight": "700",
                      "whiteSpace": "nowrap"},
        }
    return marks


def events_for_year(record: NarrativeRecord | None, year: int) -> list[Event]:
    if record is None:
        return []
    return [e for e in record.events if e.year == year]


def year_event_callout(record: NarrativeRecord | None, year: int):
    """What happened in the specific year the reader has selected."""
    evs = events_for_year(record, year)
    if not evs:
        return None
    rows = []
    for e in evs:
        colour, glyph = DIRECTION_STYLE.get(e.direction, DIRECTION_STYLE["mixed"])
        rows.append(html.Div([
            html.Span(glyph, style={"color": colour, "fontSize": "11px",
                                    "marginRight": "6px"}),
            html.Span(e.title, style={"fontSize": "11px", "fontWeight": "700",
                                      "color": "#333"}),
            chip(e.type.replace("_", " "), colour),
        ], style={"display": "flex", "alignItems": "center", "gap": "7px",
                  "flexWrap": "wrap"}))
    return html.Div([
        html.Div(f"Recorded in {year}", style={"fontSize": "9px", "color": "#999",
                                               "fontWeight": "700",
                                               "textTransform": "uppercase",
                                               "letterSpacing": ".05em",
                                               "marginBottom": "5px"}),
        html.Div(rows, style={"display": "flex", "flexDirection": "column", "gap": "4px"}),
    ], style={"background": "#fffaf5", "border": "1px solid #f0e0d0",
              "borderRadius": "6px", "padding": "8px 12px", "marginTop": "8px"})


# ── Pillars ────────────────────────────────────────────────────────────────────

def pillar_narrative_block(record: NarrativeRecord | None, pillar_id: str,
                           pillar_name: str, *, displayable: bool):
    """
    The prose for one pillar, or a statement of why there is none.

    The corpus refuses to write narrative for a pillar the index greyed out, so
    a missing summary here is a deliberate silence rather than an oversight —
    and saying that is more useful than an empty panel.
    """
    if record is None:
        return None

    p: PillarNarrative | None = record.pillar(pillar_id)
    if p is None or not p.summary:
        if not displayable:
            return missing(
                f"No narrative for pillar {pillar_id}. The index did not score it for "
                f"this country — too much of the underlying data is inferred rather "
                f"than measured — and the corpus does not write prose for a pillar the "
                f"data refused to support."
            )
        return None

    drivers = None
    if p.drivers:
        drivers = html.Div([
            html.Div("What drives it", style={"fontSize": "9px", "color": "#999",
                                              "fontWeight": "700",
                                              "textTransform": "uppercase",
                                              "letterSpacing": ".05em",
                                              "margin": "8px 0 4px"}),
            html.Ul([html.Li(d, style={"fontSize": "10px", "color": "#555",
                                       "lineHeight": 1.65, "marginBottom": "3px"})
                     for d in p.drivers],
                    style={"paddingLeft": "16px", "margin": 0}),
        ])

    return html.Div([
        section_heading(f"Pillar {pillar_id} — {pillar_name}", "narrative"),
        html.P(p.summary, style={"fontSize": "12px", "lineHeight": 1.75, "margin": 0,
                                 "color": "#333"}),
        drivers,
        source_links(record, p.citations),
    ], style={**CARD, "borderLeft": f"4px solid {BRAND_LIGHT}", "margin": "10px 0"})


# ── Balance, membership, sources ───────────────────────────────────────────────

def balance_block(record: NarrativeRecord):
    """
    The framing count, shown rather than merely stored.

    Coverage of Africa skews toward conflict and failure. The corpus counts its
    own framing so that skew is measurable; rendering the count is what turns
    the measurement into something a reader can hold the project to.
    """
    b: Balance | None = record.balance
    if b is None or b.total == 0:
        return None

    segs = []
    for n, key in ((b.n_positive, "positive"), (b.n_mixed, "mixed"),
                   (b.n_negative, "negative")):
        if n <= 0:
            continue
        colour, label = SENTIMENT_STYLE[key]
        segs.append(html.Div(
            str(n),
            title=f"{n} {label.lower()}",
            style={"flex": str(n), "background": colour, "color": "#fff",
                   "fontSize": "9px", "fontWeight": "700", "textAlign": "center",
                   "padding": "3px 0"},
        ))

    return html.Div([
        section_heading("Framing balance", f"{b.total} items counted"),
        html.Div(segs, style={"display": "flex", "borderRadius": "4px",
                              "overflow": "hidden", "marginBottom": "7px"}),
        html.P(b.note, style={"fontSize": "10px", "color": "#666", "lineHeight": 1.7,
                              "margin": 0}) if b.note else None,
        html.Div("Counted so the record can be held to its own standard: documented "
                 "gains belong beside documented failures wherever the evidence "
                 "supports them.",
                 style={"fontSize": "9px", "color": "#aaa", "marginTop": "6px"}),
    ], style={**CARD, "borderLeft": "4px solid #16a085"})


def rec_membership_block(record: NarrativeRecord):
    """Regional community membership with the join years the index itself lacks."""
    if not record.rec_membership:
        return None
    rows = []
    for m in record.rec_membership:
        current = m.status == "current"
        colour = "#16a085" if current else "#95a5a6"
        rows.append(html.Div([
            html.Span(m.org, style={"fontSize": "11px", "fontWeight": "700",
                                    "color": "#333", "minWidth": "72px"}),
            html.Span(m.span, style={"fontSize": "10px", "color": "#777",
                                     "fontFamily": "monospace", "minWidth": "72px"}),
            chip("current" if current else "withdrawn", colour),
            html.Div(source_links(record, m.citations, label="") or "",
                     style={"marginLeft": "auto"}),
        ], style={"display": "flex", "alignItems": "center", "gap": "10px",
                  "padding": "5px 0", "borderBottom": "1px solid #f5f5f5",
                  "flexWrap": "wrap"}))
    return html.Div([
        section_heading("Regional communities", "joined / left, sourced"),
        html.Div(rows),
    ], style={**CARD, "borderLeft": "4px solid #16a085"})


def sources_block(record: NarrativeRecord):
    """
    Every source behind the record, with an honest statement of their standing.

    The `verified` flag on a citation only means something once an AUDIT run has
    re-opened the page. Until then this says "cited", not "confirmed".
    """
    if not record.citations:
        return None

    by_type = record.sources_by_type
    summary_chips = [
        chip(f"{n} {t}", SOURCE_STYLE.get(t, "#888")) for t, n in by_type.items()
    ]

    rows = []
    for c in sorted(record.citations.values(), key=lambda c: (c.source_type, c.title)):
        rows.append(html.Div([
            chip(c.source_type, SOURCE_STYLE.get(c.source_type, "#888")),
            html.A(c.title or c.url, href=c.url, target="_blank",
                   rel="noopener noreferrer",
                   style={"fontSize": "10px", "color": "#444",
                          "textDecoration": "underline", "flex": 1}),
            html.Span(c.accessed, style={"fontSize": "9px", "color": "#bbb",
                                         "fontFamily": "monospace",
                                         "whiteSpace": "nowrap"}),
        ], style={"display": "flex", "alignItems": "center", "gap": "9px",
                  "padding": "4px 0", "borderBottom": "1px solid #f5f5f5"}))

    return html.Div([
        section_heading("Sources", f"{len(record.citations)} cited"),
        html.Div(summary_chips, style={"display": "flex", "gap": "6px",
                                       "flexWrap": "wrap", "marginBottom": "7px"}),
        html.Div(record.provenance_note,
                 style={"fontSize": "10px", "color": "#666", "lineHeight": 1.7,
                        "marginBottom": "8px"}),
        html.Details([
            html.Summary(f"List all {len(record.citations)} sources",
                         style={"fontSize": "10px", "color": BRAND_LIGHT,
                                "cursor": "pointer", "fontWeight": "600",
                                "padding": "4px 0"}),
            html.Div(rows, style={"marginTop": "5px"}),
        ]),
    ], style={**CARD, "borderLeft": "4px solid #7f8c8d"})


def record_footer(record: NarrativeRecord):
    """Provenance for the record itself: how current it is and what comes next."""
    return html.Div([
        html.Span(f"Narrative record · updated {record.last_updated} · "
                  f"iteration {record.iteration_count} · written by {record.model_used}",
                  style={"fontSize": "9px", "color": "#aaa"}),
        html.Span(f"next pass: {record.next_mode.value}",
                  style={"fontSize": "9px", "color": "#bbb"}),
    ], style={"display": "flex", "justifyContent": "space-between",
              "flexWrap": "wrap", "gap": "8px", "padding": "8px 2px 0",
              "borderTop": "1px solid #f0f0f0", "marginTop": "10px"})


def no_record_notice(name: str):
    return missing(
        f"No narrative record for {name} yet. The index still scores it; the "
        f"research pass that writes its history, pillar commentary and recent "
        f"developments has not run."
    )


__all__ = [
    "history_block", "recent_block", "events_block", "slider_marks",
    "year_event_callout", "events_for_year", "pillar_narrative_block",
    "balance_block", "rec_membership_block", "sources_block", "record_footer",
    "no_record_notice", "missing", "section_heading", "chip",
    "SENTIMENT_STYLE", "DIRECTION_STYLE", "SOURCE_STYLE",
]
