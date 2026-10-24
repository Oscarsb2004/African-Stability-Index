// instability.ts on an invented theatre. Each rule has a negative control.

import { describe, expect, it } from "vitest";
import { type Theatre, theatreMonthly, twelveMonths, TYPE_COLOURS } from "./instability";

const months = Array.from({ length: 26 }, (_, i) => i);
const t = (deaths: Record<string, number[]>): Theatre => ({ id: "t", name: "T", states: Object.keys(deaths), summary: "",
  links: [], markets: [], maps: [], deaths, range: { low: 0, best: 0, high: 0 }, areas_now: 0, areas_before: 0, new_ground: [] });

describe("a theatre's deaths", () => {
  it("adds its states month by month", () => {
    expect(theatreMonthly(t({ AAA: [1, 2, 3], BBB: [10, 0, 5] }))).toEqual([11, 2, 8]);
    expect(theatreMonthly(t({}))).toEqual([]);  // negative control: no states, no months
  });

  it("compares its last twelve months with the twelve before", () => {
    const one = months.map(() => 1);
    expect(twelveMonths(t({ AAA: one }))).toEqual({ now: 12, before: 12 });
    const rising = months.map((i) => (i >= 14 ? 2 : 1));
    expect(twelveMonths(t({ AAA: rising }))).toEqual({ now: 24, before: 12 });
  });

  it("gives each type of violence a colour of its own", () => {
    const v = Object.values(TYPE_COLOURS);
    expect(new Set(v).size).toBe(3);
  });
});
