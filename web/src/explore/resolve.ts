// The selection made drawable: each item with its label, its colour (states and averaged groups take the validated
// comparison colours in order, at most four; groups shown as members are grey context) and its members; and an
// item's value at a year (a state's own, or its group's average by the chosen rule).

import { COMPARE } from "../data";
import type { AverageHow, Group, Item, Series } from "./model";
import { at, snapshot } from "./model";
import { groupAverage, type GroupAverage } from "./stats";

export const POPULATION = "wdi/SP.POP.TOTL", GDP = "wdi/NY.GDP.MKTP.CD";

export interface Resolved {
  key: string;
  item: Item;
  label: string;
  short: string;          // the line-end label: a state's name, a group's code
  colour: string | null;  // null: grey context (a group shown as its members)
  members: string[];      // a state is its own single member
  group?: Group;
}

export function itemKey(i: Item): string {
  return i.t === "s" ? `s:${i.id}` : `g:${i.id}`;
}

export function coloured(i: Item): boolean {
  return i.t === "s" || i.mode === "average";
}

export function resolve(items: Item[], groups: Group[], names: Record<string, string>): Resolved[] {
  const byId = new Map(groups.map((g) => [g.id, g]));
  let c = 0;
  const out: Resolved[] = [];
  for (const item of items) {
    const colour = coloured(item) ? COMPARE[c++] ?? null : null;
    if (item.t === "s") out.push({ key: itemKey(item), item, label: names[item.id] ?? item.id,
      short: names[item.id] ?? item.id, colour, members: [item.id] });
    else {
      const g = byId.get(item.id);
      if (!g) continue;  // a custom group from another browser that this address does not carry
      const code = g.kind === "rec" || g.kind === "organisation" ? g.id
        : g.name.length > 18 ? `${g.name.slice(0, 17)}…` : g.name;
      out.push({ key: itemKey(item), item, label: item.mode === "average" ? `${g.name} (average)` : g.name,
        short: item.mode === "average" ? `${code} avg` : code, colour, members: g.members, group: g });
    }
  }
  return out;
}

/** An item's value at a year: a state's own, or its group's average. */
export function valueAt(r: Resolved, s: Series | undefined, year: number, how: AverageHow,
  weights?: Series): GroupAverage {
  if (r.item.t === "s") {
    const v = at(s, r.item.id, year);
    return { value: v, n: v === null ? 0 : 1, of: 1, min: v, max: v, ci: null };
  }
  return groupAverage(snapshot(s, year), r.members, how, weights ? snapshot(weights, year) : undefined);
}

/** The first year of a publisher's projections for a state, or for a group the earliest among its members. */
export function firstProjected(r: Resolved, s: Series | undefined): number | null {
  if (!s?.f) return null;
  const ys = r.members.map((m) => s.f?.[m]).filter((x): x is number => x !== undefined).map((i) => s.y[0] + i);
  return ys.length ? Math.min(...ys) : null;
}

/** States that two or more of the selected groups share: they count in each group's average. */
export function shared(rs: Resolved[], names: Record<string, string>): string[] {
  const groups = rs.filter((r) => r.group);
  const notes: string[] = [];
  for (let i = 0; i < groups.length; i++) for (let j = i + 1; j < groups.length; j++) {
    const both = groups[i].members.filter((m) => groups[j].members.includes(m));
    if (both.length) notes.push(`${groups[i].group!.name} and ${groups[j].group!.name} share ${both.length}: `
      + `${both.map((m) => names[m] ?? m).join(", ")}. They count in both.`);
  }
  return notes;
}

/** A round axis: the data's range widened to a step of 1, 2 or 5 times a power of ten. */
export function niceDomain(xs: number[], zero = false): [number, number] {
  let lo = Math.min(...xs), hi = Math.max(...xs);
  if (!xs.length || !Number.isFinite(lo)) return [0, 1];
  if (zero) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
  if (lo === hi) { lo -= 1; hi += 1; }
  const raw = (hi - lo) / 4, p = 10 ** Math.floor(Math.log10(raw)), f = raw / p;
  const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * p;
  return [Math.floor(lo / step) * step, Math.ceil(hi / step) * step];
}

/** A number for reading: four significant figures, thousands separated. */
export function num(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return "—";
  const a = Math.abs(v);
  if (a >= 1e12) return `${(v / 1e12).toFixed(2)} tn`;
  if (a >= 1e9) return `${(v / 1e9).toFixed(2)} bn`;
  if (a >= 1e6) return `${(v / 1e6).toFixed(2)} m`;
  return v.toLocaleString("en", { maximumSignificantDigits: 4 });
}
