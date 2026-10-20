// What every snapshot view shares: which states the selection highlights and in what colour, the tooltip style,
// and every state's row at a year.

import type { Series } from "../model";
import { at } from "../model";
import { CONTEXT, INK2 } from "../PlotFigure";
import type { Resolved } from "../resolve";

export const TIP = { fill: "#15181f", stroke: "rgba(255,255,255,0.15)" };

/** Each selected state's colour: a chosen state its own; a group's members the group's colour, or light ink when
 *  the group is shown as its members. The first item to claim a state wins. */
export function highlights(rs: Resolved[]): Map<string, string> {
  const out = new Map<string, string>();
  for (const r of rs) for (const m of r.members) if (!out.has(m)) out.set(m, r.colour ?? INK2);
  return out;
}

export interface StateRow { iso3: string; name: string; value: number; lo: number | null; hi: number | null;
  tier: number | null; colour: string; picked: boolean }

/** Every state with a value at the year, with the publisher's interval and the ASI's tier where the series has them. */
export function rows(s: Series | undefined, year: number, names: Record<string, string>,
  picked: Map<string, string>): StateRow[] {
  if (!s) return [];
  const i = year - s.y[0];
  return Object.keys(s.v).map((k) => ({ iso3: k, name: names[k] ?? k, value: at(s, k, year) as number,
    lo: s.lo?.[k]?.[i] ?? null, hi: s.hi?.[k]?.[i] ?? null, tier: s.tier?.[k]?.[i] ?? null,
    colour: picked.get(k) ?? CONTEXT, picked: picked.has(k) })).filter((r) => r.value !== null);
}
