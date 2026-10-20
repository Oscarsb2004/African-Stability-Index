// One indicator across every state at the reference year: a strip of dots on the 0-100 score scale, the chosen
// state marked, and the full list below. Values are the panel's; the strip only places them.

import { useMemo, useState } from "react";
import type { StabilityDoc } from "./data";

interface Props {
  variable: string;
  iso3: string;
  stability: StabilityDoc;
  names: Record<string, string>;
}

const W = 360, H = 64, PAD = 14;

export default function IndicatorCompare({ variable, iso3, stability, names }: Props) {
  const [at, setAt] = useState<string | null>(null);
  const meta = stability.indicators[variable];
  const rows = useMemo(() => Object.entries(stability.countries)
    .map(([k, c]) => ({ iso3: k, ...c.indicators[variable] }))
    .filter((r) => r.score !== null && r.score !== undefined)
    .sort((a, b) => (b.score as number) - (a.score as number)), [stability, variable]);
  const x = (s: number) => PAD + (s / 100) * (W - 2 * PAD);
  // stack dots that would touch, so each state stays visible
  const placed = useMemo(() => {
    const out: { iso3: string; cx: number; row: number }[] = [];
    [...rows].sort((a, b) => (a.score as number) - (b.score as number)).forEach((r) => {
      const cx = x(r.score as number);
      let row = 0;
      while (out.some((p) => p.row === row && Math.abs(p.cx - cx) < 7)) row += 1;
      out.push({ iso3: r.iso3, cx, row });
    });
    return out;
  }, [rows]);
  const y = (row: number) => H - 22 - row * 7;
  const mine = rows.find((r) => r.iso3 === iso3);
  const shown = rows.find((r) => r.iso3 === (at ?? iso3));
  const move = (e: React.MouseEvent<SVGRectElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const fx = ((e.clientX - r.left) / r.width) * W, fy = ((e.clientY - r.top) / r.height) * H;
    let best: string | null = null, dist = Infinity;
    placed.forEach((p) => {
      const d = Math.hypot(p.cx - fx, y(p.row) - fy);
      if (d < dist) { dist = d; best = p.iso3; }
    });
    setAt(dist < 16 ? best : null);
  };
  return (
    <div className="compare">
      <div className="small"><b>{meta.display_name}</b>: every state, {stability.reference_year}</div>
      <svg viewBox={`0 0 ${W} ${H}`} role="img"
        aria-label={`${meta.display_name}: ${rows.length} states, scores 0 to 100`}>
        <line x1={PAD} x2={W - PAD} y1={H - 14} y2={H - 14} className="grid" />
        {[0, 50, 100].map((t) => (
          <text key={t} x={x(t)} y={H - 2} className="tick" textAnchor="middle">{t}</text>
        ))}
        {placed.map((p) => (
          <circle key={p.iso3} cx={p.cx} cy={y(p.row)} r={p.iso3 === iso3 ? 5 : 3}
            className={p.iso3 === iso3 ? "dot-mine" : p.iso3 === at ? "dot-at" : "dot-other"} />
        ))}
        <rect x={0} y={0} width={W} height={H} fill="transparent" onMouseMove={move} onMouseLeave={() => setAt(null)} />
      </svg>
      <div className="chart-read small">
        {shown ? <>{names[shown.iso3]}: <b>{(shown.score as number).toFixed(1)}</b> of 100
          <span className="muted"> · {shown.raw === null ? "—" : shown.raw.toLocaleString(undefined,
            { maximumSignificantDigits: 4 })} {shown.provenance === "observed" ? `(${shown.source_year})`
            : `(${shown.provenance.replace("_", " ")}${shown.source_year ? ` from ${shown.source_year}` : ""})`}</span></>
          : <span className="muted">{names[iso3]} has no value; hover a dot for another state</span>}
      </div>
      <p className="muted small">Scores 0 to 100, higher is more stable; {rows.length} of{" "}
        {Object.keys(stability.countries).length} states have a value.{mine ? "" : ` ${names[iso3]} has none.`}</p>
      <details>
        <summary className="muted small">Every state</summary>
        <table className="rows compare-list">
          <tbody>
            {rows.map((r) => (
              <tr key={r.iso3} className={r.iso3 === iso3 ? "mine" : ""}>
                <td>{names[r.iso3]}</td>
                <td className="num">{r.raw === null ? "—" : r.raw.toLocaleString(undefined, { maximumSignificantDigits: 4 })}</td>
                <td className="num">{(r.score as number).toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
