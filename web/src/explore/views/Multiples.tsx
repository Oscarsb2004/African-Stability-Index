// Small multiples: one small panel per state (each chosen state, and every member of each chosen group), all on one
// axis, so a whole REC can be read at once. A member's group average is the dashed grey reference line.

import * as Plot from "@observablehq/plot";
import { useCallback, useMemo } from "react";
import type { AverageHow, Measure, Series } from "../model";
import PlotFigure, { CONTEXT, GRID, INK } from "../PlotFigure";
import { niceDomain, num, type Resolved, valueAt } from "../resolve";

export default function Multiples({ rs, s, measure, how, weights, names }: {
  rs: Resolved[]; s: Series | undefined; measure: Measure; how: AverageHow; weights?: Series;
  names: Record<string, string>;
}) {
  const panels = useMemo(() => {
    const seen = new Map<string, Resolved | null>();
    for (const r of rs) for (const m of r.members) if (!seen.has(m)) seen.set(m, r.group ? r : null);
    return [...seen.entries()];
  }, [rs]);
  const years = useMemo(() => s ? Array.from({ length: s.y[1] - s.y[0] + 1 }, (_, i) => s.y[0] + i) : [], [s]);
  const domain = useMemo(() => niceDomain(panels.flatMap(([m]) => (s?.v[m] ?? []).filter((v): v is number =>
    typeof v === "number"))), [panels, s]);
  if (!panels.length) return <p className="muted empty">Add a state or a group to begin.</p>;
  return (
    <div className="multiples">
      {panels.map(([m, group]) => (
        <Panel key={m} name={names[m] ?? m} values={years.map((y) => ({ year: y, value: s?.v[m]?.[y - s.y[0]] ?? null }))}
          reference={group ? years.map((y) => ({ year: y, value: valueAt(group, s, y, how, weights).value })) : []}
          domain={domain} measure={measure} />
      ))}
    </div>
  );
}

function Panel({ name, values, reference, domain, measure }: {
  name: string; values: { year: number; value: number | null }[]; reference: { year: number; value: number | null }[];
  domain: [number, number]; measure: Measure;
}) {
  const options = useCallback((): Plot.PlotOptions => ({
    width: 190, height: 112, marginLeft: 34, marginRight: 8, marginTop: 20, marginBottom: 18,
    x: { tickFormat: "d", ticks: 2, label: null }, y: { domain, ticks: 3, tickFormat: (v: number) => num(v), label: null },
    marks: [
      Plot.gridY({ stroke: GRID, ticks: 3 }),
      Plot.lineY(reference.filter((d) => d.value !== null), { x: "year", y: "value", stroke: CONTEXT, strokeDasharray: "3,3" }),
      Plot.lineY(values.filter((d) => d.value !== null), { x: "year", y: "value", stroke: INK, strokeWidth: 1.6 }),
      Plot.text([name], { frameAnchor: "top-left", dy: -16, fill: INK, fontWeight: 600, fontSize: 11 }),
      Plot.tip(values.filter((d) => d.value !== null), Plot.pointerX({ x: "year", y: "value",
        title: (d: { year: number; value: number }) => `${name} ${d.year}: ${num(d.value)}`, fill: "#15181f" })),
    ],
  }), [name, values, reference, domain]);
  return <PlotFigure options={options} label={`${name}: ${measure.label}`} />;
}
