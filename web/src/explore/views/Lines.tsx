// Lines: each state and each averaged group over the years, one axis, in the comparison colours, labelled at their
// ends; a group shown as its members is grey context, its hovered member named. A group's average carries a ribbon
// from its lowest to its highest member. Years the publisher projects are dashed.

import * as Plot from "@observablehq/plot";
import { useCallback } from "react";
import type { AverageHow, Measure, Series } from "../model";
import PlotFigure, { CONTEXT, GRID, INK2, INK3 } from "../PlotFigure";
import { firstProjected, niceDomain, num, type Resolved, valueAt } from "../resolve";

interface Row { key: string; label: string; short?: string; colour: string; year: number; value: number;
  min?: number | null; max?: number | null }

const H = 330, TOP = 18, BOTTOM = 30;

export default function Lines({ rs, s, measure, how, weights, year, names }: {
  rs: Resolved[]; s: Series | undefined; measure: Measure; how: AverageHow; weights?: Series; year: number;
  names: Record<string, string>;
}) {
  const options = useCallback((width: number): Plot.PlotOptions => {
    const years = s ? Array.from({ length: s.y[1] - s.y[0] + 1 }, (_, i) => s.y[0] + i) : [];
    const solid: Row[] = [], dashed: Row[] = [], context: Row[] = [], ribbons: Row[] = [];
    for (const r of rs) {
      if (r.colour === null) {
        for (const m of r.members) for (const y of years) {
          const v = s?.v[m]?.[y - s.y[0]];
          if (typeof v === "number") context.push({ key: `${r.key}:${m}`, label: names[m] ?? m, colour: CONTEXT, year: y, value: v });
        }
        continue;
      }
      const proj = firstProjected(r, s);
      for (const y of years) {
        const a = valueAt(r, s, y, how, weights);
        if (a.value === null) continue;
        const row = { key: r.key, label: r.label, short: r.short, colour: r.colour, year: y, value: a.value, min: a.min,
          max: a.max };
        if (proj === null || y < proj) solid.push(row);
        if (proj !== null && y >= proj - 1) dashed.push(row);
        if (r.item.t === "g" && a.min !== null && a.max !== null) ribbons.push(row);
      }
    }
    const all = [...solid, ...dashed, ...context];
    const allValues = [...all.map((d) => d.value), ...ribbons.flatMap((d) => [d.min as number, d.max as number])];
    const domain = niceDomain(allValues.length ? allValues
      : Object.values(s?.v ?? {}).flat().filter((v): v is number => typeof v === "number"));
    // direct labels at each coloured line's end, nudged at least 15 pixels apart
    const px = (v: number) => TOP + (1 - (v - domain[0]) / (domain[1] - domain[0])) * (H - TOP - BOTTOM);
    const back = (p: number) => domain[0] + (1 - (p - TOP) / (H - TOP - BOTTOM)) * (domain[1] - domain[0]);
    const ends = rs.filter((r) => r.colour).map((r) => {
      const mine = [...solid, ...dashed].filter((d) => d.key === r.key).sort((a, b) => a.year - b.year);
      const last = mine[mine.length - 1];
      return last && { ...last, p: px(last.value) };
    }).filter((d): d is Row & { p: number } => !!d).sort((a, b) => a.p - b.p);
    ends.forEach((e, i) => { if (i && e.p < ends[i - 1].p + 15) e.p = ends[i - 1].p + 15; });
    return {
      height: H, marginTop: TOP, marginBottom: BOTTOM, marginLeft: 52, marginRight: 96,
      x: { domain: s ? [s.y[0], s.y[1]] : undefined, tickFormat: "d", label: null, ticks: Math.min(8, Math.floor(width / 80)) },
      y: { domain, label: measure.unit || null, grid: true, tickFormat: (v: number) => num(v) },
      color: { type: "identity" },
      marks: [
        Plot.gridY({ stroke: GRID, strokeOpacity: 1 }),
        Plot.ruleX([year], { stroke: INK3, strokeDasharray: "2,3" }),
        Plot.lineY(context, { x: "year", y: "value", z: "key", stroke: CONTEXT, strokeOpacity: 0.55, strokeWidth: 1 }),
        Plot.areaY(ribbons, { x: "year", y1: "min", y2: "max", z: "key", fill: "colour", fillOpacity: 0.13 }),
        Plot.lineY(solid, { x: "year", y: "value", z: "key", stroke: "colour", strokeWidth: 2 }),
        Plot.lineY(dashed, { x: "year", y: "value", z: "key", stroke: "colour", strokeWidth: 2, strokeDasharray: "4,3" }),
        Plot.text(ends, { x: "year", y: (d: Row & { p: number }) => back(d.p), text: "short", dx: 6, textAnchor: "start",
          fill: INK2, fontSize: 10 }),
        Plot.ruleX(all, Plot.pointerX({ x: "year", stroke: INK3, strokeOpacity: 0.6 })),
        Plot.dot(all, Plot.pointer({ x: "year", y: "value", fill: "colour", r: 4, stroke: "#111", strokeWidth: 2 })),
        Plot.tip(all, Plot.pointer({ x: "year", y: "value", title: (d: Row) => `${d.label}\n${d.year}: ${num(d.value)}`
          + (d.min !== undefined && d.min !== null && d.max !== d.min ? `\nmembers ${num(d.min)} to ${num(d.max)}` : ""),
          fill: "#15181f", stroke: "rgba(255,255,255,0.15)" })),
      ],
    };
  }, [rs, s, measure, how, weights, year, names]);
  return <PlotFigure options={options} label={`${measure.label}, ${s?.y[0] ?? ""} to ${s?.y[1] ?? ""}`} />;
}
