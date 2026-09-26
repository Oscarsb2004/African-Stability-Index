"""The table view with a provenance panel. It displays numbers; it computes none except the difference it shows,
which is ours minus theirs as stored in the comparison."""

from __future__ import annotations

import html

from athena.vocab import ReproClass, ValidationLevel
from mdg.method import CARD, INDICATOR
from mdg.pipeline import Build
from mdg.validate import Validation

STYLE = """
body{font:14px/1.45 system-ui,sans-serif;margin:24px;color:#1c1c1c;max-width:1100px}
h1{font-size:20px;margin:0 0 4px}h2{font-size:16px;margin:24px 0 6px}
.note{color:#555;font-size:13px}.private{background:#fbf1e8;border:1px solid #d9b08c;padding:6px 10px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0 14px}
th{background:#1f3a5f;color:#fff;text-align:left;padding:4px 6px}td{border-bottom:1px solid #d8dde4;padding:4px 6px}
td.n{text-align:right;font-variant-numeric:tabular-nums}.pass{color:#0f6e56;font-weight:600}.fail{color:#a32d2d;font-weight:600}
code{font-size:12px}
"""


def _e(value) -> str:
    return html.escape(str(value))


def render(build: Build, v: Validation, run_id: str) -> str:
    regional = {r["group"]: r for r in build.frames["group-percent"].table.to_pylist()}
    rounded = {r["group"]: r["value"] for r in build.frames["group-percent-rounded"].table.to_pylist()}
    published = v.published["regions"]
    rows = []
    for group in sorted(regional, key=lambda g: (regional[g]["level"], g)):
        r = regional[group]
        theirs = published.get(group)
        match = theirs is not None and rounded[group] == theirs
        level = ValidationLevel.PUBLISHER_MATCH if match else ValidationLevel.UNVERIFIED
        rows.append(
            f"<tr><td>{_e(group)}</td><td>{_e(r['level'])}</td><td class=n>{r['countries']}</td>"
            f"<td class=n>{r['women']}</td><td class=n>{r['seats']}</td><td class=n>{r['value']:.4f}</td>"
            f"<td class=n>{rounded[group]:.1f}</td><td class=n>{'' if theirs is None else f'{theirs:.1f}'}</td>"
            f"<td class='{'pass' if match else 'fail'}'>{'match' if match else 'differs'}</td>"
            f"<td>{level.value} / {ReproClass.A.value}</td></tr>")
    checks = "".join(
        f"<tr><td>{_e(k)}</td><td>{c.compared}</td><td>{c.within}</td><td>{c.missing}</td><td>{c.extra}</td>"
        f"<td class=n>{c.max_abs_difference:.4f}</td><td class='{'pass' if c.passed else 'fail'}'>"
        f"{'pass' if c.passed else 'fail'}</td></tr>" for k, c in v.comparisons.items())
    mismatches = "".join(
        f"<tr><td>{_e(k)}</td><td>{_e(m.key)}</td><td>{m.side}</td><td class=n>{_e(m.ours)}</td>"
        f"<td class=n>{_e(m.theirs)}</td></tr>" for k, c in v.comparisons.items() for m in c.mismatches)
    divergences = "".join(
        f"<tr><td>{_e(d.id)}</td><td>{_e(d.checkpoint)}</td><td class=n>{d.size:.4f}</td>"
        f"<td>{_e(d.suspected_steps)}</td><td>{d.status.value}</td><td>{_e(d.cause or '')}</td></tr>"
        for d in v.register.current().values())
    readings = "".join(
        f"<tr><td>{r.step}</td><td>{_e(r.sentence.quote)}</td><td>{_e(r.adopted)}</td>"
        f"<td>{'ruled' if r.owner_ruled else 'awaiting the owner'}</td></tr>" for r in CARD.readings)
    provenance = "".join(f"<tr><td>{_e(k)}</td><td><code>{_e(h)}</code></td></tr>"
                         for k, h in sorted({**build.snapshots, **v.snapshots}.items()))
    receipts = "".join(f"<tr><td><code>{_e(r.step)}</code></td><td>{', '.join(r.invariants_checked)}</td>"
                       f"<td><code>{_e(r.output[:23])}…</code></td></tr>" for r in build.results)
    quotes = "".join(f"<li>{_e(p)}</li>" for p in v.quote_problems) or "<li>Every quote was found verbatim.</li>"
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8><title>MDG 3.3 replication</title>
<style>{STYLE}</style></head><body>
<h1>{_e(INDICATOR.title)} - MDG {INDICATOR.code}, 2015</h1>
<p class=note>Run <code>{_e(run_id)}</code>. Method <code>{_e(CARD.ref)}</code>. Rounding: {CARD.rounding.decimals} decimal,
{CARD.rounding.rule.value} ({'owner default' if CARD.rounding.is_default else 'publisher rule'}).</p>
<p class=private><b>Private.</b> Built from UN and IPU material under decision P24; not for publication.</p>
<h2>Regional values</h2>
<table><tr><th>Group</th><th>Level</th><th>Countries</th><th>Women</th><th>Seats</th><th>Ours</th><th>Ours, rounded</th>
<th>Published</th><th>Result</th><th>Level / class</th></tr>{''.join(rows)}</table>
<h2>Checkpoints</h2>
<table><tr><th>Checkpoint</th><th>Compared</th><th>Within</th><th>Missing</th><th>Extra</th><th>Largest difference</th>
<th>Result</th></tr>{checks}</table>
<p class=note>Blame window (method steps): {_e(v.window) if v.window else 'none - no checkpoint failed'}</p>
<h2>Mismatches</h2><table><tr><th>Checkpoint</th><th>Key</th><th>Side</th><th>Ours</th><th>Theirs</th></tr>
{mismatches or '<tr><td colspan=5>None.</td></tr>'}</table>
<h2>Divergence register</h2><table><tr><th>Id</th><th>Checkpoint</th><th>Size</th><th>Suspected steps</th><th>Status</th>
<th>Cause</th></tr>{divergences or '<tr><td colspan=6>Empty.</td></tr>'}</table>
<h2>Readings</h2><table><tr><th>Step</th><th>Sentence</th><th>Reading adopted</th><th>Status</th></tr>{readings}</table>
<h2>Quotes on the method card</h2><ul>{quotes}</ul>
<h2>Provenance</h2><table><tr><th>Recipe</th><th>Snapshot</th></tr>{provenance}</table>
<table><tr><th>Step</th><th>Invariants checked</th><th>Output</th></tr>{receipts}</table>
</body></html>"""
