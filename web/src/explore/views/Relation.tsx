// Two measures together. Scatter: every state at one year, the chosen ones in colour and named, the least-squares
// line with Pearson's r, Spearman's rho and n (an association, not a cause); the year can play. Trajectory: each
// chosen state's or averaged group's path through the two measures over the years.

import * as Plot from "@observablehq/plot";
import { useCallback, useEffect, useState } from "react";
import MeasurePicker from "../MeasurePicker";
import { at, type AverageHow, type Catalogue, type Measure, type Series, useSeries } from "../model";
import PlotFigure, { CONTEXT, GRID, INK2 } from "../PlotFigure";
import { num, POPULATION, type Resolved, valueAt } from "../resolve";
import { ols, pearson, spearman } from "../stats";
import { highlights, TIP } from "./common";

interface Point { iso3: string; name: string; x: number; y: number; pop: number | null; colour: string; picked: boolean }

const logScale = (m?: Measure) => !!m && /GDP|current US\$|current international|per capita|Population, total/i
  .test(m.label + m.unit);

export function Scatter({ rs, s, measure, year, setYear, names, catalogue, xId, setX }: {
  rs: Resolved[]; s: Series | undefined; measure: Measure; year: number; setYear: (y: number) => void;
  names: Record<string, string>; catalogue: Catalogue; xId: string; setX: (id: string) => void;
}) {
  const got = useSeries([xId, POPULATION]);
  const sx = got[xId], pop = got[POPULATION];
  const xm = catalogue.measures.find((m) => m.id === xId);
  const [playing, setPlaying] = useState(false);
  const lo = Math.max(s?.y[0] ?? 0, sx?.y[0] ?? 0), hi = Math.min(s?.y[1] ?? 0, sx?.y[1] ?? 0);
  useEffect(() => {
    if (!playing) return;
    const t = setInterval(() => setYear(year >= hi ? lo : year + 1), 700);
    return () => clearInterval(t);
  }, [playing, year, lo, hi, setYear]);
  const logX = logScale(xm);
  const points: Point[] = [];
  const picked = highlights(rs);
  for (const k of Object.keys(names)) {
    const x = at(sx, k, year), y = at(s, k, year);
    if (x === null || y === null || (logX && x <= 0)) continue;
    points.push({ iso3: k, name: names[k], x, y, pop: at(pop, k, year), colour: picked.get(k) ?? CONTEXT, picked: picked.has(k) });
  }
  const xs = points.map((p) => logX ? Math.log10(p.x) : p.x), ys = points.map((p) => p.y);
  const r = pearson(xs, ys), rho = spearman(xs, ys), fit = ols(xs, ys);
  const options = useCallback((width: number): Plot.PlotOptions => {
    const ext = [Math.min(...xs), Math.max(...xs)];
    const line = fit ? ext.map((v) => ({ x: logX ? 10 ** v : v, y: fit.intercept + fit.slope * v })) : [];
    return { height: Math.min(460, Math.max(300, width * 0.6)), marginLeft: 54, marginRight: 20,
      x: { type: logX ? "log" : "linear", label: xm ? `${xm.label}${logX ? " (log scale)" : ""}` : null, grid: true,
        tickFormat: (v: number) => num(v) },
      y: { label: measure.label, grid: true, tickFormat: (v: number) => num(v) },
      r: { range: [2.5, 14] }, color: { type: "identity" },
      marks: [
        Plot.gridX({ stroke: GRID }), Plot.gridY({ stroke: GRID }),
        Plot.line(line, { x: "x", y: "y", stroke: INK2, strokeDasharray: "5,4" }),
        Plot.dot(points.filter((p) => !p.picked), { x: "x", y: "y", r: (p: Point) => p.pop ?? 1e6, fill: CONTEXT,
          fillOpacity: 0.6 }),
        Plot.dot(points.filter((p) => p.picked), { x: "x", y: "y", r: (p: Point) => p.pop ?? 1e6, fill: "colour",
          stroke: "#111", strokeWidth: 1.5 }),
        Plot.text(points.filter((p) => p.picked), { x: "x", y: "y", text: "name", dy: -12, fill: INK2, fontSize: 10 }),
        Plot.tip(points, Plot.pointer({ x: "x", y: "y", title: (p: Point) => `${p.name}\n${xm?.label ?? ""}: ${num(p.x)}`
          + `\n${measure.label}: ${num(p.y)}` + (p.pop ? `\npopulation ${num(p.pop)}` : ""), ...TIP })),
      ] };
  }, [points, xs, fit, logX, xm, measure]);
  return (
    <>
      <div className="relation-controls">
        <MeasurePicker catalogue={catalogue} value={xId} onPick={setX} label="Across (x)" />
        <button className="linkish" onClick={() => setPlaying(!playing)} disabled={lo >= hi}>
          {playing ? "❚❚ Pause" : `▶ Play ${lo}–${hi}`}</button>
      </div>
      {!sx ? <p className="muted">Loading…</p> : <PlotFigure options={options}
        label={`${measure.label} against ${xm?.label ?? xId}, ${year}`} />}
      <p className="small muted">{year}: {points.length} states with both values. Pearson's r {num(r)}, Spearman's rho
        {" "}{num(rho)}{logX && " (on the logarithm of the x measure)"}; the dashed line is the least-squares fit. Dot
        size is population. An association, not a cause.</p>
    </>
  );
}

export function Trajectory({ rs, s, measure, how, weights, catalogue, xId, setX }: {
  rs: Resolved[]; s: Series | undefined; measure: Measure; how: AverageHow; weights?: Series;
  catalogue: Catalogue; xId: string; setX: (id: string) => void;
}) {
  const sx = useSeries([xId])[xId];
  const xm = catalogue.measures.find((m) => m.id === xId);
  const logX = logScale(xm);
  const options = useCallback((): Plot.PlotOptions => {
    const data: { key: string; label: string; colour: string; year: number; x: number; y: number }[] = [];
    const lo = Math.max(s?.y[0] ?? 0, sx?.y[0] ?? 0), hi = Math.min(s?.y[1] ?? 0, sx?.y[1] ?? 0);
    for (const r of rs.filter((r) => r.colour)) for (let y = lo; y <= hi; y++) {
      const a = valueAt(r, sx, y, how, weights).value, b = valueAt(r, s, y, how, weights).value;
      if (a !== null && b !== null && (!logX || a > 0)) data.push({ key: r.key, label: r.short, colour: r.colour as string, year: y, x: a, y: b });
    }
    const ends = data.filter((d, i) => i === data.length - 1 || data[i + 1].key !== d.key);
    const starts = data.filter((d, i) => i === 0 || data[i - 1].key !== d.key);
    return { height: 420, marginLeft: 54, marginRight: 60, color: { type: "identity" },
      x: { type: logX ? "log" : "linear", label: xm ? `${xm.label}${logX ? " (log scale)" : ""}` : null, grid: true,
        tickFormat: (v: number) => num(v) },
      y: { label: measure.label, grid: true, tickFormat: (v: number) => num(v) },
      marks: [
        Plot.gridX({ stroke: GRID }), Plot.gridY({ stroke: GRID }),
        Plot.line(data, { x: "x", y: "y", z: "key", stroke: "colour", strokeWidth: 1.8, marker: "dot", curve: "linear" }),
        Plot.text(starts, { x: "x", y: "y", text: (d: { year: number }) => String(d.year), dy: 12, fill: INK2, fontSize: 9 }),
        Plot.text(ends, { x: "x", y: "y", text: (d: { label: string; year: number }) => `${d.label} ${d.year}`, dx: 8,
          textAnchor: "start", fill: INK2, fontSize: 10 }),
        Plot.tip(data, Plot.pointer({ x: "x", y: "y", title: (d: { label: string; year: number; x: number; y: number }) =>
          `${d.label} ${d.year}\nx ${num(d.x)} · y ${num(d.y)}`, ...TIP })),
      ] };
  }, [rs, s, sx, how, weights, measure, xm, logX]);
  return (
    <>
      <div className="relation-controls"><MeasurePicker catalogue={catalogue} value={xId} onPick={setX} label="Across (x)" /></div>
      {!rs.some((r) => r.colour) ? <p className="muted empty">Add a state or average a group to trace its path.</p>
        : <PlotFigure options={options} label={`${measure.label} against ${xm?.label ?? xId} over time`} />}
      <p className="small muted">Each line runs from its first year (labelled) to its last.</p>
    </>
  );
}
