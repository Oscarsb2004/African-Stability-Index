// What an economy or a population is made of, at the year. Economy: agriculture, industry and services as shares of
// GDP (WDI), one stacked bar per chosen state or averaged group. Population: the first chosen state's pyramid, each
// five-year age group as a share of its sex's population (WDI). Three and two categories, in the first slots of the
// validated comparison colours.

import * as Plot from "@observablehq/plot";
import { useCallback, useState } from "react";
import { COMPARE } from "../../data";
import type { AverageHow, Series } from "../model";
import { at, useSeries } from "../model";
import PlotFigure, { GRID, INK } from "../PlotFigure";
import { num, type Resolved, valueAt } from "../resolve";
import { TIP } from "./common";

const SECTORS = [["Agriculture", "wdi/NV.AGR.TOTL.ZS"], ["Industry", "wdi/NV.IND.TOTL.ZS"], ["Services", "wdi/NV.SRV.TOTL.ZS"]];
const AGES = ["0004", "0509", "1014", "1519", "2024", "2529", "3034", "3539", "4044", "4549", "5054", "5559", "6064",
  "6569", "7074", "7579", "80UP"];
const PYRAMID = AGES.flatMap((a) => [`wdi/SP.POP.${a}.FE.5Y`, `wdi/SP.POP.${a}.MA.5Y`]);
const ageLabel = (a: string) => a === "80UP" ? "80+" : `${Number(a.slice(0, 2))}–${Number(a.slice(2))}`;

export default function Composition({ rs, year, how, weights, names }: {
  rs: Resolved[]; year: number; how: AverageHow; weights?: Series; names: Record<string, string>;
}) {
  const [what, setWhat] = useState<"economy" | "population">("economy");
  const got = useSeries(what === "economy" ? SECTORS.map((x) => x[1]) : PYRAMID);
  const first = rs.find((r) => r.item.t === "s");
  const economy = useCallback((): Plot.PlotOptions => {
    const data = rs.filter((r) => r.colour).flatMap((r) => SECTORS.map(([sector, id]) => ({ who: r.short, sector,
      value: valueAt(r, got[id], year, how, weights).value }))).filter((d) => d.value !== null);
    return { height: 50 + 34 * new Set(data.map((d) => d.who)).size, marginLeft: 150, marginRight: 20,
      x: { label: "% of GDP", grid: true, axis: "top" }, y: { label: null, tickSize: 0 },
      color: { domain: SECTORS.map((x) => x[0]), range: COMPARE.slice(0, 3), legend: true },
      marks: [
        Plot.gridX({ stroke: GRID }),
        Plot.barX(data, Plot.stackX({ x: "value", y: "who", fill: "sector", inset: 1 })),
        Plot.tip(data, Plot.pointer(Plot.stackX({ x: "value", y: "who", title: (d: { who: string; sector: string;
          value: number }) => `${d.who}: ${d.sector} ${num(d.value)}% of GDP`, ...TIP }))),
      ] };
  }, [rs, got, year, how, weights]);
  const pyramid = useCallback((): Plot.PlotOptions => {
    const iso3 = first?.item.id as string;
    const data = AGES.flatMap((a) => [
      { age: ageLabel(a), sex: "Women", value: at(got[`wdi/SP.POP.${a}.FE.5Y`], iso3, year) },
      { age: ageLabel(a), sex: "Men", value: at(got[`wdi/SP.POP.${a}.MA.5Y`], iso3, year) }])
      .filter((d) => d.value !== null).map((d) => ({ ...d, signed: d.sex === "Men" ? -(d.value as number) : d.value as number }));
    return { height: 380, marginLeft: 50, x: { label: "% of each sex's population (men left, women right)", grid: true,
      tickFormat: (v: number) => num(Math.abs(v)) }, y: { domain: AGES.map(ageLabel).reverse(), label: "age" },
      color: { domain: ["Men", "Women"], range: COMPARE.slice(0, 2), legend: true },
      marks: [Plot.gridX({ stroke: GRID }), Plot.barX(data, { x: "signed", y: "age", fill: "sex", inset: 0.5 }),
        Plot.ruleX([0], { stroke: INK }),
        Plot.tip(data, Plot.pointer({ x: "signed", y: "age", title: (d: { sex: string; age: string; value: number }) =>
          `${d.sex} aged ${d.age}: ${num(d.value)}% of ${d.sex.toLowerCase()}`, ...TIP }))] };
  }, [first, got, year]);
  return (
    <>
      <label className="small inline-control">Show{" "}
        <select className="pick" value={what} onChange={(e) => setWhat(e.target.value as typeof what)}>
          <option value="economy">the economy by sector (each chosen state and averaged group)</option>
          <option value="population">the population by age and sex (the first chosen state)</option>
        </select></label>
      {what === "economy"
        ? rs.some((r) => r.colour) ? <PlotFigure options={economy} label={`Economy by sector, ${year}`} />
          : <p className="muted empty">Add a state or average a group.</p>
        : first ? <><p className="small muted">{names[first.item.id]}, {year}.</p>
          <PlotFigure options={pyramid} label={`Population pyramid, ${names[first.item.id]}, ${year}`} /></>
          : <p className="muted empty">Add a state to see its population pyramid.</p>}
      <p className="small muted">Sectors are value added as a share of GDP, as the WDI prints them; they need not sum to
        100 (taxes and statistical differences are not shown).</p>
    </>
  );
}
