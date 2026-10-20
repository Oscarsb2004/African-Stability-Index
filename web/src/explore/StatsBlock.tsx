// The statistics beside the charts, for the measure at the year. Each is derived by a stated formula (stats.ts) and
// reads as a description, never a cause: change and volatility of each coloured item, convergence within each
// group, the measure against income, the neighbours, whether high values cluster in space, and the states most like
// the first chosen one on the eight pillars.

import { useMemo } from "react";
import { at, type AverageHow, type Measure, type Series, snapshot, type StatesDoc, useSeries } from "./model";
import { num, type Resolved, valueAt } from "./resolve";
import { moransI, nearest, neighbourMean, ols, sd } from "./stats";
import { PILLAR_IDS } from "./views/Grid";

const INCOME = "wdi/NY.GDP.PCAP.PP.CD";

export default function StatsBlock({ rs, s, measure, year, how, weights, names, states }: {
  rs: Resolved[]; s: Series; measure: Measure; year: number; how: AverageHow; weights?: Series;
  names: Record<string, string>; states: StatesDoc;
}) {
  const got = useSeries([INCOME, ...PILLAR_IDS]);
  const snap = useMemo(() => snapshot(s, year), [s, year]);
  const from = Math.max(s.y[0], year - 10);

  const change = rs.filter((r) => r.colour).map((r) => {
    const ys: number[] = [], vs: number[] = [];
    for (let y = from; y <= year; y++) {
      const v = valueAt(r, s, y, how, weights).value;
      if (v !== null) { ys.push(y); vs.push(v); }
    }
    const fit = ols(ys, vs);
    return { label: r.label, perDecade: fit ? fit.slope * 10 : null, volatility: sd(vs), n: vs.length };
  });

  const convergence = rs.filter((r) => r.group).map((r) => {
    const a = r.members.map((m) => at(s, m, from)), b = r.members.map((m) => at(s, m, year));
    const both = r.members.map((_, i) => [a[i], b[i]]).filter(([x, y]) => x !== null && y !== null) as [number, number][];
    const beta = ols(both.map(([x]) => x), both.map(([x, y]) => y - x));
    return { name: r.group!.name, sdFrom: sd(a.filter((x): x is number => x !== null)),
      sdTo: sd(b.filter((x): x is number => x !== null)), beta: beta?.slope ?? null, n: both.length };
  });

  const income = useMemo(() => {
    const keys = Object.keys(snap).filter((k) => snap[k] !== null && (at(got[INCOME], k, year) ?? 0) > 0);
    const fit = ols(keys.map((k) => Math.log10(at(got[INCOME], k, year) as number)), keys.map((k) => snap[k] as number));
    return fit && { fit, residual: Object.fromEntries(keys.map((k, i) => [k, fit.residuals[i]])), n: keys.length };
  }, [snap, got, year]);

  const moran = moransI(snap, states.neighbours);
  const lag = neighbourMean(snap, states.neighbours);
  const stateItems = rs.filter((r) => r.item.t === "s");
  const like = useMemo(() => {
    const first = stateItems[0]?.item.id;
    if (!first || PILLAR_IDS.some((id) => !got[id])) return null;
    const table = Object.fromEntries(Object.keys(names).map((k) => [k, PILLAR_IDS.map((id) => at(got[id], k, year))]));
    return { of: first, near: nearest(table, first) };
  }, [stateItems, got, names, year]);

  return (
    <details className="stats small" open>
      <summary>Statistics, {year} <span className="muted">(derived; descriptions, not causes)</span></summary>
      {change.length > 0 && (
        <p><b>Change, {from}–{year}:</b> {change.map((c) => `${c.label}: ${c.perDecade === null ? "—"
          : `${c.perDecade >= 0 ? "+" : ""}${num(c.perDecade)} a decade`} (least-squares trend), standard deviation
          ${num(c.volatility)} over ${c.n} years`).join("; ")}.</p>
      )}
      {convergence.map((c) => (
        <p key={c.name}><b>{c.name}, convergence:</b> the spread among members (standard deviation) went from
          {" "}{num(c.sdFrom)} in {from} to {num(c.sdTo)} in {year} ({c.sdTo !== null && c.sdFrom !== null
            ? c.sdTo < c.sdFrom ? "narrower: σ-convergence" : "wider: no σ-convergence" : "not enough values"});
          {" "}regressing the change on the starting level over {c.n} members gives a slope of {num(c.beta)}
          {c.beta !== null && (c.beta < 0 ? ": below zero, so on average lower starters gained more (β-convergence)"
            : ": above zero, so on average lower starters did not catch up")}; a slope near zero means little either way.</p>
      ))}
      {income && (
        <p><b>Against income:</b> across {income.n} states, {measure.label} rises by {num(income.fit.slope)} for
          each tenfold rise in GDP per person (PPP). {stateItems.filter((r) => income.residual[r.item.id] !== undefined).map((r) =>
            `${r.label} sits ${num(Math.abs(income.residual[r.item.id]))} ${income.residual[r.item.id] >= 0 ? "above" : "below"} what its income predicts`).join("; ")}{stateItems.length ? "." : ""}</p>
      )}
      {moran && (
        <p><b>Neighbours:</b> Moran's I is {num(moran.I)} over {moran.n} states with a land neighbour ({moran.I > 0.1
          ? "neighbours tend to resemble each other" : moran.I < -0.1 ? "neighbours tend to differ" : "little spatial pattern"};
          {" "}0 would be none). {stateItems.filter((r) => lag[r.item.id] !== null && lag[r.item.id] !== undefined).map((r) =>
            `${r.label}'s neighbours average ${num(lag[r.item.id])}`).join("; ")}{stateItems.length ? "." : ""}</p>
      )}
      {like && like.near.length > 0 && (
        <p><b>Most like {names[like.of]} on the eight pillars, {year}:</b> {like.near.map((n) => `${names[n.iso3]} (${num(n.d)})`)
          .join(", ")}. Distance is the root-mean-square gap in standard deviations, pillar by pillar.</p>
      )}
    </details>
  );
}
