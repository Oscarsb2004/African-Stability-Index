// customIndex.ts on invented series, each method checked against values worked by hand. Each rule has a negative
// control.

import { describe, expect, it } from "vitest";
import { type CustomIndex, fromIndexHash, indexHash, scoreIndex, scoreItem, type Series, valueAt } from "./customIndex";

const S = ["AAA", "BBB", "CCC"];
// 2018 to 2024
const gdp: Series = { y: [2018, 2024], v: {
  AAA: [10, null, null, null, null, null, 20], BBB: [5, null, null, null, 15, null, null], CCC: [0, null, null, null, null, null, 40] } };
const deaths: Series = { y: [2018, 2024], v: { AAA: [null, null, null, null, null, null, 4], BBB: [null, null, null, null, null, null, 2],
  CCC: [null, null, null, null, null, null, null] } };
const ix = (over: Partial<CustomIndex>): CustomIndex => ({ id: "x", name: "Mine", method: "minmax", aggregate: "mean",
  year: 2024, created: "2026-10-23", items: [{ measure: "gdp", label: "GDP", higherIsBetter: true },
    { measure: "deaths", label: "Deaths", higherIsBetter: false }], ...over });

describe("a reader's own index", () => {
  it("carries a value forward up to five years, never further", () => {
    expect(valueAt(gdp, "BBB", 2024)).toBe(15);  // from 2022
    expect(valueAt(gdp, "BBB", 2028)).toBeNull();  // negative control: 2022 is more than five years before 2028
  });

  it("scales min-max over the states' values since 2000, turned where lower is better", () => {
    const g = scoreItem(gdp, { measure: "gdp", label: "", higherIsBetter: true }, "minmax", 2024, S);
    expect(g).toEqual({ AAA: 50, BBB: 37.5, CCC: 100 });  // range 0 (CCC 2018) to 40: 20 → 50, 15 → 37.5
    const d = scoreItem(deaths, { measure: "deaths", label: "", higherIsBetter: false }, "minmax", 2024, S);
    expect(d).toEqual({ AAA: 0, BBB: 100 });  // fewer deaths scores higher
  });

  it("standardises z-scores and ranks percentiles, ties sharing a rank", () => {
    const z = scoreItem(gdp, { measure: "gdp", label: "", higherIsBetter: true }, "zscore", 2024, S);
    expect(z.CCC).toBeCloseTo(1.1339, 3);  // (40 − 25) / sd(20, 15, 40) = 15 / 13.229
    const tied: Series = { y: [2024, 2024], v: { AAA: [1], BBB: [1], CCC: [3] } };
    expect(scoreItem(tied, { measure: "t", label: "", higherIsBetter: true }, "percentile", 2024, S))
      .toEqual({ AAA: 25, BBB: 25, CCC: 100 });
  });

  it("scores a state only with half of the indicators, by the mean or the geometric mean", () => {
    const series = { gdp, deaths };
    const mean = scoreIndex(ix({}), series, S);
    expect(mean.values).toEqual({ AAA: 25, BBB: 68.75, CCC: 100 });  // CCC has 1 of 2: half is enough
    expect(mean.coverage.CCC).toBe(1);
    const three = scoreIndex(ix({ items: [...ix({}).items, { measure: "absent", label: "", higherIsBetter: true }] }),
      series, S);
    expect(three.values.CCC).toBeNull();  // negative control: 1 of 3 is under half
    const geo = scoreIndex(ix({ aggregate: "geometric" }), series, S);
    expect(geo.values.AAA).toBeCloseTo(Math.sqrt(50 * 1), 6);  // a 0 is floored at 1
  });

  it("shares an index by its definition, and refuses an address without one", () => {
    const back = fromIndexHash("#" + indexHash(ix({})));
    expect(back?.name).toBe("Mine");
    expect(back?.items).toHaveLength(2);
    expect(fromIndexHash("#index=%7B%7D")).toBeNull();
  });
});
