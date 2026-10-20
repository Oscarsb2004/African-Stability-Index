// Heatmaps and profiles. Heatmap: states by years for the measure, states by the eight ASI pillars at the year, or
// states by dataset for how much of each publisher's data covers them; fifths of the cells, in the validated ramp.
// Profile: the eight pillar scores of each chosen state and averaged group, every other state as faint context.

import * as Plot from "@observablehq/plot";
import { useCallback, useMemo, useState } from "react";
import { RAMP } from "../../data";
import { shortSource } from "../MeasurePicker";
import type { AverageHow, Catalogue, Measure, Series, StatesDoc } from "../model";
import { at, useSeries } from "../model";
import PlotFigure, { CONTEXT, GRID, INK2 } from "../PlotFigure";
import { num, type Resolved, valueAt } from "../resolve";
import { highlights, TIP } from "./common";

const PILLARS = ["GOV", "VOI", "SEC", "MAC", "EXT", "HUM", "COH", "ENV"];
export const PILLAR_IDS = PILLARS.map((p) => `asi/pillar.${p}`);

function chosenStates(rs: Resolved[], names: Record<string, string>): string[] {
  const picked = [...highlights(rs).keys()];
  return picked.length ? picked : Object.keys(names);
}

export function Heatmap({ rs, s, measure, year, names, states, catalogue }: {
  rs: Resolved[]; s: Series | undefined; measure: Measure; year: number; names: Record<string, string>;
  states: StatesDoc; catalogue: Catalogue;
}) {
  const [mode, setMode] = useState<"years" | "pillars" | "coverage">("years");
  const pillars = useSeries(mode === "pillars" ? PILLAR_IDS : []);
  const label = (id: string) => catalogue.measures.find((m) => m.id === id)?.label.replace("ASI pillar: ", "") ?? id;
  const options = useCallback((): Plot.PlotOptions => {
    const who = chosenStates(rs, names);
    let cells: { row: string; col: string; value: number }[] = [];
    if (mode === "years" && s) {
      for (const k of who) for (let y = s.y[0]; y <= s.y[1]; y++) {
        const v = at(s, k, y);
        if (v !== null) cells.push({ row: names[k] ?? k, col: String(y), value: v });
      }
    } else if (mode === "pillars") {
      for (const k of who) for (const id of PILLAR_IDS) {
        const v = at(pillars[id], k, year);
        if (v !== null) cells.push({ row: names[k] ?? k, col: label(id), value: v });
      }
    } else {
      cells = who.flatMap((k) => Object.entries(states.coverage ?? {}).map(([ds, by]) => ({ row: names[k] ?? k,
        col: shortSource(ds), value: Math.round((by[k] ?? 0) * 100) })));
    }
    const rowOrder = [...new Set(cells.map((c) => c.row))].sort((a, b) => a.localeCompare(b));
    return { height: 40 + 15 * rowOrder.length, marginLeft: 150, marginBottom: mode === "years" ? 20 : 60,
      x: { label: null, tickRotate: mode === "years" ? 0 : -30,
        ticks: mode === "years" && s ? Array.from({ length: s.y[1] - s.y[0] + 1 }, (_, i) => String(s.y[0] + i))
          .filter((y) => Number(y) % 5 === 0) : undefined },
      y: { domain: rowOrder, label: null, tickSize: 0 },
      color: { type: "quantile", n: 5, range: RAMP, legend: true, label: mode === "coverage" ? "% of series" : null,
        tickFormat: (v: number) => num(v) },
      marks: [
        Plot.cell(cells, { x: "col", y: "row", fill: "value", inset: 0.5 }),
        Plot.tip(cells, Plot.pointer({ x: "col", y: "row", title: (c: { row: string; col: string; value: number }) =>
          `${c.row}, ${c.col}: ${num(c.value)}${mode === "coverage" ? "% of series since 2015" : ""}`, ...TIP })),
      ] };
  }, [mode, rs, s, year, names, pillars, states, label]);
  return (
    <>
      <label className="small inline-control">Show{" "}
        <select className="pick" value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
          <option value="years">{measure.label}, every year</option>
          <option value="pillars">the eight ASI pillars, {year}</option>
          <option value="coverage">how much of each dataset covers each state (since 2015)</option>
        </select></label>
      <p className="small muted">{rs.length ? "The states in the selection." : "Every state; add states or groups to narrow it."}
        {" "}Colours are fifths of the cells shown, lighter higher.</p>
      <PlotFigure options={options} label={`Heatmap: ${mode}`} />
    </>
  );
}

export function Profile({ rs, year, how, weights, names, catalogue }: {
  rs: Resolved[]; year: number; how: AverageHow; weights?: Series; names: Record<string, string>; catalogue: Catalogue;
}) {
  const got = useSeries(PILLAR_IDS);
  const label = useMemo(() => Object.fromEntries(PILLAR_IDS.map((id) => [id, catalogue.measures.find((m) => m.id === id)
    ?.label.replace("ASI pillar: ", "") ?? id])), [catalogue]);
  const options = useCallback((): Plot.PlotOptions => {
    const context = Object.keys(names).flatMap((k) => PILLAR_IDS.map((id) => ({ key: k, pillar: label[id],
      value: at(got[id], k, year) }))).filter((d) => d.value !== null);
    const lines = rs.filter((r) => r.colour).flatMap((r) => PILLAR_IDS.map((id) => ({ key: r.key, name: r.short,
      colour: r.colour as string, pillar: label[id], value: valueAt(r, got[id], year, how, weights).value })))
      .filter((d) => d.value !== null);
    return { height: 360, marginBottom: 70, marginLeft: 44, color: { type: "identity" },
      x: { domain: PILLAR_IDS.map((id) => label[id]), label: null, tickRotate: -20 },
      y: { domain: [0, 100], label: "score 0-100, higher is more stable", grid: true },
      marks: [
        Plot.gridY({ stroke: GRID }),
        Plot.line(context, { x: "pillar", y: "value", z: "key", stroke: CONTEXT, strokeOpacity: 0.25 }),
        Plot.line(lines, { x: "pillar", y: "value", z: "key", stroke: "colour", strokeWidth: 2.2, marker: "dot" }),
        Plot.text(lines.filter((d) => d.pillar === label[PILLAR_IDS[PILLAR_IDS.length - 1]]), { x: "pillar", y: "value",
          text: "name", dx: 8, textAnchor: "start", fill: INK2, fontSize: 10 }),
        Plot.tip(lines, Plot.pointer({ x: "pillar", y: "value", title: (d: { name: string; pillar: string; value: number }) =>
          `${d.name}\n${d.pillar}: ${num(d.value)}`, ...TIP })),
      ] };
  }, [rs, got, year, how, weights, names, label]);
  if (!rs.some((r) => r.colour)) return <p className="muted empty">Add a state or average a group to see its pillar profile.</p>;
  return <><p className="small muted">The eight ASI pillars at {year}; every other state is a faint line behind. A pillar
    left out of a state's score that year still shows its value here.</p>
    <PlotFigure options={options} label={`Pillar profiles, ${year}`} /></>;
}
