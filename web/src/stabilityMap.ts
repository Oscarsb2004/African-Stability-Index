// What the Stability section's map shows, and the groupings it can be cut to (the owner, 2026-10-23): the composite
// (general stability), a pillar, or an indicator, each state coloured by fifths of the member states, lighter more
// stable; and a grouping, whose members alone are coloured. Nothing here computes a score: every value is the
// panel's, from stability.json.

import { RAMP, type StabilityDoc } from "./data";
import type { Group } from "./explore/model";
import { fifths } from "./explore/stats";

// "composite", "pillar:<id>" or "indicator:<id>"
export type StabilityMeasure = string;

// The highlighted choices at the top of the menu: a first position, for the owner to replace with their own.
export const HIGHLIGHTS: StabilityMeasure[] = [
  "composite", "pillar:SEC", "pillar:GOV", "pillar:MAC", "pillar:COH",
  "indicator:pv_estimate", "indicator:state_based_deaths", "indicator:inflation_5yr_avg",
];

export interface Shown {
  label: string;                         // what the legend calls it
  values: Record<string, number | null>; // each member state's value
  breaks: number[];                      // the four breaks of its five classes
  colours: Record<string, string>;       // each state with a value, its class colour
  scale: string;                         // what the colours mean
}

export function measureLabel(s: StabilityDoc, m: StabilityMeasure): string {
  if (m === "composite") return `ASI ${s.reference_year}, composite score`;
  const [kind, id] = m.split(":");
  if (kind === "pillar") return `${id} · ${s.pillars[id]?.name ?? id}`;
  return s.indicators[id]?.display_name ?? id;
}

/** Each state's value for a measure: the composite, a pillar's score, or an indicator's score (0 to 100, higher more
 *  stable); an indicator that has no score (a descriptive one) gives its raw value. */
export function measureValues(s: StabilityDoc, m: StabilityMeasure): { values: Record<string, number | null>; raw: boolean } {
  const [kind, id] = m.split(":");
  const all = Object.entries(s.countries);
  if (kind === "composite") return { values: Object.fromEntries(all.map(([k, c]) => [k, c.composite.score])), raw: false };
  if (kind === "pillar") return { values: Object.fromEntries(all.map(([k, c]) => [k, c.pillars[id]?.score ?? null])), raw: false };
  const scored = all.some(([, c]) => typeof c.indicators[id]?.score === "number");
  return { values: Object.fromEntries(all.map(([k, c]) => [k, (scored ? c.indicators[id]?.score : c.indicators[id]?.raw) ?? null])),
           raw: !scored };
}

/** The map's colours for a measure: the composite keeps the published classes (stability.json's breaks); any other
 *  measure is cut at the fifths of the member states with a value. */
export function shown(s: StabilityDoc, m: StabilityMeasure): Shown {
  const { values, raw } = measureValues(s, m);
  const xs = Object.values(values).filter((v): v is number => typeof v === "number");
  const breaks = m === "composite" ? s.classes.breaks : xs.length >= 5 ? fifths(xs) : [];
  const colours: Record<string, string> = {};
  for (const [k, v] of Object.entries(values)) {
    if (typeof v !== "number" || !breaks.length) continue;
    let i = 0;
    while (i < breaks.length && v >= breaks[i]) i++;
    colours[k] = RAMP[i];
  }
  const scale = m === "composite" ? `Classes: ${s.classes.rule}. Lighter is more stable.`
    : raw ? "Fifths of the states with a value, as published. Lighter is higher; it is shown, not scored."
    : "Fifths of the states with a value, on the ASI's 0 to 100 score. Lighter is more stable.";
  return { label: measureLabel(s, m), values, breaks, colours, scale };
}

export interface MenuSection { title: string; path?: string; items: StabilityMeasure[] }

/** The menu's sections, in the order of the indicator files: general stability, the eight pillars, then each
 *  pillar's indicators under the name of its file (indicators_list/pillar_<id>.yaml). */
export function menu(s: StabilityDoc): MenuSection[] {
  return [
    { title: "General stability", items: ["composite"] },
    { title: "The eight pillars", items: Object.keys(s.pillars).map((id) => `pillar:${id}`) },
    ...Object.entries(s.pillars).map(([id, p]) => ({
      title: `${id} · ${p.name}`, path: `indicators_list/pillar_${id.toLowerCase()}.yaml`,
      items: p.indicators.filter((v) => s.indicators[v]).map((v) => `indicator:${v}`),
    })),
  ];
}

/** A grouping's members by name, for the picker's hover: "Kenya, Rwanda, …". */
export function memberNames(g: Group, names: Record<string, string>): string {
  return g.members.map((m) => names[m] ?? m).sort((a, b) => a.localeCompare(b)).join(", ");
}
