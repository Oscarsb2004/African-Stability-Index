// Change between two years. Slope: one line per state from the earlier year to the later, the coloured items in
// their colours and group members grey. Dumbbell: one row per state, its earlier and later values joined, in order
// of the later.

import * as Plot from "@observablehq/plot";
import { useCallback, useState } from "react";
import type { AverageHow, Measure, Series } from "../model";
import { at } from "../model";
import PlotFigure, { CONTEXT, GRID, INK2, INK3 } from "../PlotFigure";
import { num, type Resolved, valueAt } from "../resolve";
import { TIP } from "./common";

interface Pair { key: string; label: string; colour: string; a: number; b: number }

function pairs(rs: Resolved[], s: Series | undefined, from: number, to: number, how: AverageHow, weights: Series | undefined,
  names: Record<string, string>): Pair[] {
  const out: Pair[] = [];
  const seen = new Set<string>();  // a state in two chosen groups is drawn once
  for (const r of rs) {
    if (r.colour === null) {
      for (const m of r.members) {
        const a = at(s, m, from), b = at(s, m, to);
        if (a !== null && b !== null && !seen.has(m)) out.push({ key: `${r.key}:${m}`, label: names[m] ?? m, colour: CONTEXT, a, b });
        seen.add(m);
      }
    } else {
      const a = valueAt(r, s, from, how, weights).value, b = valueAt(r, s, to, how, weights).value;
      if (a !== null && b !== null) out.push({ key: r.key, label: r.short, colour: r.colour, a, b });
    }
  }
  return out;
}

function FromYear({ s, from, setFrom, to }: { s?: Series; from: number; setFrom: (y: number) => void; to: number }) {
  return (
    <label className="small inline-control">From{" "}
      <select className="pick" value={from} onChange={(e) => setFrom(Number(e.target.value))}>
        {s && Array.from({ length: to - s.y[0] }, (_, i) => s.y[0] + i).map((y) => <option key={y} value={y}>{y}</option>)}
      </select> to {to} (the year above)</label>
  );
}

export function Slope({ rs, s, measure, year, how, weights, names }: {
  rs: Resolved[]; s: Series | undefined; measure: Measure; year: number; how: AverageHow; weights?: Series;
  names: Record<string, string>;
}) {
  const [from, setFrom] = useState(Math.max(s?.y[0] ?? year - 10, year - 10));
  const options = useCallback((): Plot.PlotOptions => {
    const data = pairs(rs, s, from, year, how, weights, names);
    const long = data.flatMap((d) => [{ ...d, year: from, value: d.a }, { ...d, year, value: d.b }]);
    return { height: 380, marginLeft: 120, marginRight: 120, color: { type: "identity" },
      x: { domain: [from, year], ticks: [from, year], tickFormat: "d", label: null, inset: 10 },
      y: { label: measure.unit || null, grid: true, tickFormat: (v: number) => num(v) },
      marks: [
        Plot.gridY({ stroke: GRID }),
        Plot.line(long, { x: "year", y: "value", z: "key", stroke: "colour", strokeWidth: (d: Pair) => d.colour === CONTEXT ? 1 : 2.2 }),
        Plot.dot(long, { x: "year", y: "value", fill: "colour", r: 3 }),
        Plot.text(data, { x: () => year, y: "b", text: (d: Pair) => `${d.label} ${num(d.b)}`, dx: 8, textAnchor: "start",
          fill: (d: Pair) => d.colour === CONTEXT ? INK3 : INK2, fontSize: 10 }),
        Plot.text(data, { x: () => from, y: "a", text: (d: Pair) => num(d.a), dx: -8, textAnchor: "end", fill: INK3, fontSize: 9 }),
      ] };
  }, [rs, s, from, year, how, weights, names, measure]);
  if (!rs.length) return <p className="muted empty">Add a state or a group to begin.</p>;
  return <><FromYear s={s} from={from} setFrom={setFrom} to={year} />
    <PlotFigure options={options} label={`${measure.label}, ${from} to ${year}`} /></>;
}

export function Dumbbell({ rs, s, measure, year, how, weights, names }: {
  rs: Resolved[]; s: Series | undefined; measure: Measure; year: number; how: AverageHow; weights?: Series;
  names: Record<string, string>;
}) {
  const [from, setFrom] = useState(Math.max(s?.y[0] ?? year - 10, year - 10));
  const options = useCallback((): Plot.PlotOptions => {
    const data = pairs(rs, s, from, year, how, weights, names).sort((p, q) => q.b - p.b);
    return { height: 40 + 18 * data.length, marginLeft: 150, color: { type: "identity" },
      x: { label: measure.unit || null, grid: true, axis: "top", tickFormat: (v: number) => num(v) },
      y: { domain: data.map((d) => d.label), label: null, tickSize: 0 },
      marks: [
        Plot.gridX({ stroke: GRID }),
        Plot.link(data, { y1: "label", y2: "label", x1: "a", x2: "b", stroke: (d: Pair) => d.colour === CONTEXT ? INK3 : d.colour,
          strokeWidth: 2 }),
        Plot.dot(data, { y: "label", x: "a", r: 3.5, fill: "#111", stroke: INK2 }),
        Plot.dot(data, { y: "label", x: "b", r: 4.5, fill: (d: Pair) => d.colour === CONTEXT ? INK2 : d.colour }),
        Plot.tip(data, Plot.pointerY({ y: "label", x: "b", title: (d: Pair) => `${d.label}\n${from}: ${num(d.a)}\n${year}: `
          + `${num(d.b)}\nchange ${d.b - d.a >= 0 ? "+" : ""}${num(d.b - d.a)}`, ...TIP })),
      ] };
  }, [rs, s, from, year, how, weights, names, measure]);
  if (!rs.length) return <p className="muted empty">Add a state or a group to begin.</p>;
  return <><FromYear s={s} from={from} setFrom={setFrom} to={year} />
    <p className="small muted">Open circle: {from}. Filled: {year}.</p>
    <PlotFigure options={options} label={`${measure.label}: ${from} and ${year}`} /></>;
}
