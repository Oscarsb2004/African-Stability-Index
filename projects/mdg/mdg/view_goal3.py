"""The Goal 3 report: 3.1 checkpoints and regional tables, and 3.2 hosted with the reason it is not rebuilt."""

from __future__ import annotations

import html

from mdg.goal3 import YEARS
from mdg.method import CARD_31, CARD_32, INDICATOR_31, INDICATOR_32
from mdg.pipeline import Build
from mdg.sources import LEVELS
from mdg.validate_goal3 import Goal3
from mdg.view import STYLE


def _e(value) -> str:
    return html.escape(str(value))


def render_goal3(b: Build, v: Goal3, run_id: str) -> str:
    checks = "".join(
        f"<tr><td>{_e(k)}</td><td>{c.compared}</td><td>{c.within}</td><td>{c.missing}</td><td>{c.extra}</td>"
        f"<td class=n>{c.max_abs_difference:.4f}</td><td class='{'pass' if c.passed else 'fail'}'>"
        f"{'pass' if c.passed else 'fail'}</td></tr>" for k, c in v.comparisons.items())
    tables = []
    for part, (level, *_rest) in LEVELS.items():
        for year in YEARS:
            tag = f"{part}-{year}"
            ours = {r["group"]: r for r in b.frames[f"3.1{tag}-group"].table.to_pylist()}
            rounded = {r["group"]: r["value"] for r in b.frames[f"3.1{tag}-group-rounded"].table.to_pylist()}
            published = v.published[f"region-{tag}"]
            rows = "".join(
                f"<tr><td>{_e(g)}</td><td class=n>{ours[g]['countries'] if g in ours else ''}</td>"
                f"<td class=n>{'' if g not in rounded else f'{rounded[g]:.2f}'}</td>"
                f"<td class=n>{'' if g not in published else f'{published[g]:.2f}'}</td>"
                f"<td class='{'pass' if g in rounded and g in published and rounded[g] == published[g] else 'fail'}'>"
                f"{'match' if g in rounded and g in published and rounded[g] == published[g] else 'differs'}</td>"
                f"</tr>" for g in sorted(set(ours) | set(published)))
            tables.append(f"<h3>{_e(level.title())}, {year}</h3><p class=note>Blame window: "
                          f"{_e(v.windows[tag]) or 'none'}</p><table><tr><th>Group</th><th>Countries</th>"
                          f"<th>Ours, rounded</th><th>Published</th><th>Result</th></tr>{rows}</table>")
    divergences = "".join(
        f"<tr><td>{_e(d.id)}</td><td class=n>{d.size:.4f}</td><td>{_e(d.suspected_steps)}</td>"
        f"<td>{d.status.value}</td><td>{_e(d.cause.value if d.cause else '')}</td><td>{_e(d.explanation)}</td></tr>"
        for d in v.register.current().values())
    hosted = "".join(
        f"<tr><td>{_e(g)}</td>" + "".join(f"<td class=n>{v.hosted_32[str(y)].get(g, '')}</td>"
                                           for y in (1990, 2000, 2005, 2013)) + "</tr>"
        for g in sorted(v.hosted_32["2013"]))
    readings = "".join(f"<tr><td>{_e(CARD_31.ref)} step {r.step}</td><td>{_e(r.adopted)}</td>"
                       f"<td>{'ruled' if r.owner_ruled else 'awaiting the owner'}</td></tr>" for r in CARD_31.readings)
    coverage = ", ".join(f"{y}: {n} countries" for y, n in v.coverage_32.items())
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8><title>MDG Goal 3 replication</title>
<style>{STYLE}h3{{font-size:14px;margin:14px 0 4px}}</style></head><body>
<h1>MDG Goal 3 - indicators {INDICATOR_31.code} and {INDICATOR_32.code}</h1>
<p class=note>Run <code>{_e(run_id)}</code>. Methods <code>{_e(CARD_31.ref)}</code>, <code>{_e(CARD_32.ref)}</code>.</p>
<p class=private><b>Private.</b> Built from UN material under decision P24. UIS data is CC BY-SA 4.0.</p>
<h2>3.1 {_e(INDICATOR_31.title)} - class {INDICATOR_31.repro_class.value}</h2>
<p class=note>Built from today's UIS counts through the published method. K0 checks our arithmetic against UIS's own
ratios (same edition); K1 compares country ratios with the MDG database of July 2015; K3 compares groups with the 2015
annex.</p>
<table><tr><th>Checkpoint</th><th>Compared</th><th>Within</th><th>Missing</th><th>Extra</th><th>Largest difference</th>
<th>Result</th></tr>{checks}</table>
{''.join(tables)}
<h2>Divergence register</h2><table><tr><th>Id</th><th>Size</th><th>Suspected steps</th><th>Status</th><th>Proposed cause</th>
<th>Explanation</th></tr>{divergences or '<tr><td colspan=6>Empty.</td></tr>'}</table>
<h2>Quotes on the method cards</h2><ul>{''.join(f"<li>{_e(q)}</li>" for q in v.quote_problems) or "<li>Every quote was found verbatim.</li>"}</ul>
<h2>Readings</h2><table><tr><th>Where</th><th>Reading adopted</th><th>Status</th></tr>{readings}</table>
<h2>3.2 {_e(INDICATOR_32.title)} - class {INDICATOR_32.repro_class.value}, hosted only</h2>
<p class=note>Not rebuilt. The regional weights are each country's economically active population in the
non-agricultural sector in 1990, and the publisher imputes missing countries with models it has not released. The
2015 edition's country values are stored ({coverage}).</p>
<table><tr><th>Group</th><th>1990</th><th>2000</th><th>2005</th><th>2013</th></tr>{hosted}</table>
</body></html>"""
