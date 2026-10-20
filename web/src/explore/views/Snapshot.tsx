// Two views of every state at one year. Distribution: a beeswarm of all states, or one row of dots and a box per
// category value, the chosen states in colour. Ordered: every state in order of its value, with the publisher's
// interval where there is one (the ASI's 95%, WGI's and CPI's 90%); the ASI's states coloured by tier, never numbered,
// since the index separates tiers and bands of ranks, not single places (P96).

import * as Plot from "@observablehq/plot";
import { useCallback, useState } from "react";
import { RAMP } from "../../data";
import type { Measure, Series, StatesDoc } from "../model";
import PlotFigure, { CONTEXT, GRID, INK, INK2, INK3 } from "../PlotFigure";
import { num, type Resolved } from "../resolve";
import { highlights, rows, type StateRow, TIP } from "./common";

const TIERS = [RAMP[4], RAMP[3], RAMP[2], RAMP[1], RAMP[0]];  // tier 1 lightest, as the map's lighter-is-more-stable

export function Distribution({ rs, s, measure, year, names, states }: {
  rs: Resolved[]; s: Series | undefined; measure: Measure; year: number; names: Record<string, string>;
  states: StatesDoc;
}) {
  const [split, setSplit] = useState("");
  const attr = states.attributes.find((a) => a.id === split);
  const options = useCallback((): Plot.PlotOptions => {
    const picked = highlights(rs);
    const data = rows(s, year, names, picked).map((r) => ({ ...r,
      cat: attr ? [attr.values[r.iso3]].flat()[0] ?? "no value" : "" }));
    const tip = (d: StateRow) => `${d.name}: ${num(d.value)}`;
    if (!attr) {
      return { height: 230, marginLeft: 20, marginRight: 20, x: { label: measure.unit || null, grid: true,
        tickFormat: (v: number) => num(v) },
        marks: [
          Plot.gridX({ stroke: GRID }),
          Plot.dotX(data.filter((d) => !d.picked), Plot.dodgeY({ x: "value", r: 4.5, fill: CONTEXT, anchor: "middle" })),
          Plot.dotX(data.filter((d) => d.picked), Plot.dodgeY({ x: "value", r: 5.5, fill: "colour", stroke: "#111",
            anchor: "middle" })),
          Plot.tip(data, Plot.pointer(Plot.dodgeY({ x: "value", r: 5, anchor: "middle", title: tip, ...TIP }))),
        ], color: { type: "identity" } };
    }
    const order = attr.order ?? [...new Set(data.map((d) => d.cat))].sort();
    return { height: 70 + 46 * order.length, marginLeft: Math.min(200, 7 * Math.max(...order.map((o) => o.length))),
      x: { label: measure.unit || null, grid: true, tickFormat: (v: number) => num(v) }, y: { domain: order, label: null },
      color: { type: "identity" },
      marks: [
        Plot.gridX({ stroke: GRID }),
        Plot.boxX(data, { x: "value", y: "cat", fill: "rgba(255,255,255,0.06)", stroke: INK2, r: 0 }),
        Plot.dot(data, { x: "value", y: "cat", r: 4, fill: "colour", stroke: "#111", strokeWidth: 1 }),
        Plot.tip(data, Plot.pointer({ x: "value", y: "cat", title: tip, ...TIP })),
      ] };
  }, [rs, s, year, names, attr, measure]);
  return (
    <>
      <label className="small inline-control">Split by{" "}
        <select className="pick" value={split} onChange={(e) => setSplit(e.target.value)}>
          <option value="">nothing (every state together)</option>
          {states.attributes.filter((a) => a.id !== "recs" && new Set(Object.values(a.values).flat()).size <= 12)
            .map((a) => <option key={a.id} value={a.id}>{a.label}</option>)}
        </select></label>
      <PlotFigure options={options} label={`${measure.label}, every state, ${year}`} />
    </>
  );
}

export function Ordered({ rs, s, measure, year, names }: {
  rs: Resolved[]; s: Series | undefined; measure: Measure; year: number; names: Record<string, string>;
}) {
  const options = useCallback((): Plot.PlotOptions => {
    const picked = highlights(rs);
    const data = rows(s, year, names, picked).sort((a, b) => b.value - a.value);
    const chosen = new Set(data.filter((d) => d.picked).map((d) => d.name));
    const tiered = data.some((d) => d.tier !== null);
    const fill = (d: StateRow) => tiered && d.tier ? TIERS[d.tier - 1] : d.colour;
    const interval = data.some((d) => d.lo !== null && d.hi !== null);
    return { height: 30 + 15 * data.length, marginLeft: 150, marginRight: 30,
      x: { label: measure.unit || null, grid: true, axis: "top", tickFormat: (v: number) => num(v) },
      y: { domain: data.map((d) => d.name), label: null, axis: null }, color: { type: "identity" },
      marks: [
        Plot.gridX({ stroke: GRID }),
        interval ? Plot.ruleY(data, { y: "name", x1: "lo", x2: "hi", stroke: fill, strokeWidth: 2, strokeOpacity: 0.7 })
          : Plot.barX(data, { y: "name", x: "value", fill, fillOpacity: 0.85 }),
        interval ? Plot.dot(data, { y: "name", x: "value", fill, r: 3.5, stroke: "#111" }) : null,
        Plot.axisY({ tickSize: 0, fill: (name: string) => chosen.has(name) ? INK : INK3 }),
        Plot.tip(data, Plot.pointerY({ y: "name", x: "value", title: (d: StateRow) => `${d.name}: ${num(d.value)}`
          + (d.lo !== null ? `\ninterval ${num(d.lo)} to ${num(d.hi)}` : "") + (d.tier ? `\nTier ${d.tier}` : ""), ...TIP })),
      ] };
  }, [rs, s, year, names, measure]);
  const tiers = s?.tier ? Math.max(...Object.values(s.tier).flat().filter((t): t is number => typeof t === "number")) : 0;
  return (
    <>
      {s?.lo && <p className="small muted">Each line is the publisher's {measure.interval} interval; the dot is the
        value. {tiers > 0 && "Colour is the tier: states in one tier cannot be told apart by the data, so no state is given a single place."}</p>}
      {tiers > 0 && (
        <div className="chips small">
          {TIERS.slice(0, tiers).map((c, i) => <span key={c}><span className="swatch" style={{ background: c }} />Tier {i + 1}</span>)}
        </div>
      )}
      <PlotFigure options={options} label={`${measure.label}, every state in order, ${year}`} />
      <p className="small muted">The states in the selection are named in white.</p>
    </>
  );
}
