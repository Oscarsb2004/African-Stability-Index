// The continent by category and by membership. Categories: how many states take each value of a category (the
// World Bank's income groups, landlocked or coastal, UNDP's development groups…), and the measure's mean in each,
// with its 95% interval. Memberships: how the eight RECs overlap, as an UpSet chart (each column a combination of
// RECs, its bar the states in exactly that combination), which reads where a Venn diagram of eight sets cannot.

import * as Plot from "@observablehq/plot";
import { useCallback, useMemo } from "react";
import type { Attribute, Group, Measure, Series, StatesDoc } from "../model";
import { snapshot } from "../model";
import PlotFigure, { GRID, INK, INK2, INK3 } from "../PlotFigure";
import { num } from "../resolve";
import { groupAverage } from "../stats";
import { TIP } from "./common";

export function Categories({ s, measure, year, names, states, attr, setAttr }: {
  s: Series | undefined; measure: Measure; year: number; names: Record<string, string>; states: StatesDoc;
  attr: string; setAttr: (id: string) => void;
}) {
  const a: Attribute | undefined = states.attributes.find((x) => x.id === attr) ?? states.attributes[0];
  const counts = useCallback((): Plot.PlotOptions => {
    const by = valuesOf(a);
    const data = order(a, by).map((v) => ({ value: v, n: by.get(v)!.length, who: by.get(v)!.map((k) => names[k] ?? k) }));
    return { height: 40 + 26 * data.length, marginLeft: 190, marginRight: 40,
      x: { label: "states", grid: true, axis: "top" }, y: { domain: data.map((d) => d.value), label: null, tickSize: 0 },
      marks: [
        Plot.gridX({ stroke: GRID }),
        Plot.barX(data, { x: "n", y: "value", fill: INK2, fillOpacity: 0.75 }),
        Plot.text(data, { x: "n", y: "value", text: (d: { n: number }) => String(d.n), dx: 8, textAnchor: "start", fill: INK }),
        Plot.tip(data, Plot.pointerY({ x: "n", y: "value", title: (d: { value: string; who: string[] }) =>
          `${d.value}: ${d.who.join(", ")}`, ...TIP })),
      ] };
  }, [a, names]);
  const means = useCallback((): Plot.PlotOptions => {
    const by = valuesOf(a), snap = snapshot(s, year);
    const data = order(a, by).map((cat) => ({ cat, avg: groupAverage(snap, by.get(cat)!) }))
      .filter((d) => d.avg.value !== null);
    type D = (typeof data)[number];
    return { height: 40 + 26 * data.length, marginLeft: 190, marginRight: 40,
      x: { label: `${measure.label}, mean of the states, ${year}`, grid: true, axis: "top", tickFormat: (v: number) => num(v) },
      y: { domain: data.map((d) => d.cat), label: null, tickSize: 0 },
      marks: [
        Plot.gridX({ stroke: GRID }),
        Plot.ruleY(data.filter((d) => d.avg.ci), { y: "cat", x1: (d: D) => d.avg.ci![0], x2: (d: D) => d.avg.ci![1],
          stroke: INK3, strokeWidth: 2 }),
        Plot.dot(data, { y: "cat", x: (d: D) => d.avg.value, r: 4.5, fill: INK }),
        Plot.tip(data, Plot.pointerY({ y: "cat", x: (d: D) => d.avg.value, title: (d: D) => `${d.cat}: ${num(d.avg.value)} `
          + `(${d.avg.n} of ${d.avg.of} states)` + (d.avg.ci ? `
95% interval ${num(d.avg.ci[0])} to ${num(d.avg.ci[1])}` : ""),
          ...TIP })),
      ] };
  }, [a, s, year, measure]);
  if (!a) return null;
  return (
    <>
      <label className="small inline-control">Category{" "}
        <select className="pick" value={a.id} onChange={(e) => setAttr(e.target.value)}>
          {states.attributes.map((x) => <option key={x.id} value={x.id}>{x.label}</option>)}
        </select></label>
      <p className="small muted">{a.label}: {a.kind}{a.asof && `, ${a.asof}`}. A state with several values counts in each.
        The second chart is the mean of the states in each category, each counting once, with the t-interval of
        that mean; under half the states with a value gives none.</p>
      <div className="two-up">
        <PlotFigure options={counts} label={`${a.label}: states in each`} />
        <PlotFigure options={means} label={`${measure.label} by ${a.label}`} />
      </div>
    </>
  );
}

function valuesOf(a: Attribute | undefined): Map<string, string[]> {
  const by = new Map<string, string[]>();
  for (const [k, v] of Object.entries(a?.values ?? {})) for (const x of [v].flat()) by.set(x, [...(by.get(x) ?? []), k]);
  return by;
}

function order(a: Attribute | undefined, by: Map<string, string[]>): string[] {
  const known = (a?.order ?? []).filter((v) => by.has(v));
  return [...known, ...[...by.keys()].filter((v) => !known.includes(v)).sort((x, y) => by.get(y)!.length - by.get(x)!.length)];
}

export function Memberships({ groups, names }: { groups: Group[]; names: Record<string, string> }) {
  const recs = groups.filter((g) => g.kind === "rec");
  const options = useCallback((part: "bars" | "matrix") => (width: number): Plot.PlotOptions => {
    const combos = new Map<string, string[]>();
    for (const k of Object.keys(names)) {
      const key = recs.filter((g) => g.members.includes(k)).map((g) => g.id).join("+") || "none";
      combos.set(key, [...(combos.get(key) ?? []), k]);
    }
    const cols = [...combos.entries()].sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]));
    const domain = cols.map(([k]) => k);
    const x = { domain, axis: null, padding: 0.25 };
    if (part === "bars") {
      const data = cols.map(([k, who]) => ({ key: k, n: who.length, who: who.map((w) => names[w]).sort() }));
      return { width, height: 170, marginLeft: 90, x, y: { label: "states", grid: true },
        marks: [Plot.gridY({ stroke: GRID }), Plot.barY(data, { x: "key", y: "n", fill: INK2 }),
          Plot.text(data, { x: "key", y: "n", text: (d: { n: number }) => String(d.n), dy: -7, fill: INK }),
          Plot.tip(data, Plot.pointerX({ x: "key", y: "n", title: (d: { key: string; who: string[] }) =>
            `${d.key.replace(/\+/g, " + ")}\n${d.who.join(", ")}`, ...TIP }))] };
    }
    const dots = domain.flatMap((k) => recs.map((g) => ({ key: k, rec: `${g.id} (${g.members.length})`, on: k.split("+").includes(g.id) })));
    return { width, height: 30 + 22 * recs.length, marginLeft: 90, x, y: { domain: recs.map((g) => `${g.id} (${g.members.length})`),
      label: null, tickSize: 0 }, marks: [
      Plot.dot(dots, { x: "key", y: "rec", r: 5, fill: (d: { on: boolean }) => d.on ? INK : "rgba(255,255,255,0.12)" }),
      Plot.line(dots.filter((d) => d.on), { x: "key", y: "rec", z: "key", stroke: INK, strokeWidth: 2 }),
    ] };
  }, [recs, names]);
  const bars = useMemo(() => options("bars"), [options]);
  const matrix = useMemo(() => options("matrix"), [options]);
  return (
    <>
      <p className="small muted">Each column is a combination of RECs; its bar counts the states that belong to exactly
        that combination (hover for their names). The rows give each REC's size. REC membership is the owner's
        compilation, as it stands today.</p>
      <PlotFigure options={bars} label="States in each combination of RECs" />
      <PlotFigure options={matrix} label="Which RECs each combination holds" />
    </>
  );
}
