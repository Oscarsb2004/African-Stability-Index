// One series over time: a thin line, a zero line when the range crosses it, and a crosshair with the value on
// hover. One axis only. The title outside names the series, so there is no legend.

import { useState } from "react";

interface Props {
  periods: string[];
  values: (number | null)[];
  unit: string;
  height?: number;
  mark?: { period: string; label: string }[];
  zero?: boolean;  // keep 0 in the range (rates); off for an index that never nears it
}

const W = 360;

export default function LineChart({ periods, values, unit, height = 120, mark = [], zero = true }: Props) {
  const [at, setAt] = useState<number | null>(null);
  const pad = { l: 34, r: 10, t: 10, b: 20 };
  const known = values.filter((v): v is number => v !== null);
  if (known.length < 2) return <p className="muted">Too few values to draw.</p>;
  let lo = zero ? Math.min(...known, 0) : Math.min(...known);
  let hi = Math.max(...known);
  if (hi === lo) hi = lo + 1;
  const span = hi - lo;
  lo -= span * 0.05;
  hi += span * 0.05;
  const x = (i: number) => pad.l + (i / (periods.length - 1)) * (W - pad.l - pad.r);
  const y = (v: number) => pad.t + (1 - (v - lo) / (hi - lo)) * (height - pad.t - pad.b);
  let d = "";
  values.forEach((v, i) => {
    if (v === null) return;
    d += `${d && values[i - 1] !== null ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
  });
  const ticks = [lo + (hi - lo) * 0.1, (lo + hi) / 2, hi - (hi - lo) * 0.1];
  const move = (e: React.MouseEvent<SVGRectElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const fx = ((e.clientX - r.left) / r.width) * W;
    const i = Math.round(((fx - pad.l) / (W - pad.l - pad.r)) * (periods.length - 1));
    setAt(Math.max(0, Math.min(periods.length - 1, i)));
  };
  const v = at === null ? null : values[at];
  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${height}`} role="img"
        aria-label={`${periods[0]} to ${periods[periods.length - 1]}, ${unit}`}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} className="grid" />
            <text x={pad.l - 4} y={y(t) + 3} className="tick" textAnchor="end">{t.toFixed(0)}</text>
          </g>
        ))}
        {lo < 0 && hi > 0 && <line x1={pad.l} x2={W - pad.r} y1={y(0)} y2={y(0)} className="zero" />}
        <text x={pad.l} y={height - 4} className="tick">{periods[0]}</text>
        <text x={W - pad.r} y={height - 4} className="tick" textAnchor="end">{periods[periods.length - 1]}</text>
        {mark.map((m) => {
          const i = periods.indexOf(m.period);
          return i < 0 || values[i] === null ? null : (
            <circle key={m.period} cx={x(i)} cy={y(values[i] as number)} r={4} className="mark" />
          );
        })}
        <path d={d} className="line" />
        {at !== null && v !== null && (
          <g>
            <line x1={x(at)} x2={x(at)} y1={pad.t} y2={height - pad.b} className="cross" />
            <circle cx={x(at)} cy={y(v)} r={4} className="dot" />
          </g>
        )}
        <rect x={0} y={0} width={W} height={height} fill="transparent" onMouseMove={move}
          onMouseLeave={() => setAt(null)} />
      </svg>
      <div className="chart-read">
        {at !== null ? <>{periods[at]}: <b>{v === null ? "—" : `${v.toFixed(1)}${unit === "%" ? "%" : ` ${unit}`}`}</b></>
          : <span className="muted">Hover for values</span>}
      </div>
    </div>
  );
}
