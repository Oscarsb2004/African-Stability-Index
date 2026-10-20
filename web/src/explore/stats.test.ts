// stats.ts on invented numbers. Each rule has a negative control.

import { describe, expect, it } from "vitest";
import {
  againstValue, fifths, groupAverage, median, moransI, nearest, neighbourMean, normalQuantile, ols, pearson, quantile,
  ranks, sd, spearman, tCritical, welch,
} from "./stats";

describe("basic statistics", () => {
  it("median, sample sd and the type-7 quantile", () => {
    expect(median([3, 1, 2])).toBe(2);
    expect(median([4, 1, 2, 3])).toBe(2.5);
    expect(sd([2, 4, 4, 4, 5, 5, 7, 9])).toBeCloseTo(2.138, 3);
    expect(sd([1])).toBeNull();  // negative control: one value has no spread
    expect(quantile([1, 2, 3, 4], 0.25)).toBeCloseTo(1.75, 10);  // pandas' default
    expect(fifths([1, 2, 3, 4, 5, 6])).toEqual([2, 3, 4, 5]);
  });

  it("t and normal critical values match the published tables", () => {
    expect(normalQuantile(0.975)).toBeCloseTo(1.959964, 5);
    for (const [df, t] of [[1, 12.7062], [2, 4.3027], [3, 3.1824], [5, 2.5706], [10, 2.2281], [30, 2.0423]]) {
      expect(Math.abs(tCritical(df) - t)).toBeLessThan(0.006);
    }
    expect(tCritical(5)).toBeGreaterThan(tCritical(50));  // fewer degrees of freedom, a wider interval
  });
});

describe("group averages", () => {
  const values = { A: 10, B: 20, C: 30, D: null };

  it("each member counts once, and the interval is the members' t-interval", () => {
    const g = groupAverage(values, ["A", "B", "C", "D"]);
    expect(g.value).toBe(20);
    expect([g.n, g.of, g.min, g.max]).toEqual([3, 4, 10, 30]);
    expect(g.ci![1] - 20).toBeCloseTo(tCritical(2) * 10 / Math.sqrt(3), 10);
  });

  it("under half the members with a value gives no average", () => {
    expect(groupAverage({ A: 1 }, ["A", "B", "C"]).value).toBeNull();
    expect(groupAverage({ A: 1, B: 2 }, ["A", "B", "C"]).value).toBe(1.5);  // negative control: two of three
  });

  it("a weighting is the reader's choice, and a member without a weight is left out of it", () => {
    const w = { A: 1, B: 1, C: 2 };
    expect(groupAverage(values, ["A", "B", "C"], "population", w).value).toBe(22.5);
    expect(groupAverage(values, ["A", "B", "C"], "gdp", { A: 1, B: 1 }).value).toBe(15);
    expect(groupAverage(values, ["A", "B", "C"], "median").value).toBe(20);
  });

  it("an empty group has no average", () => {
    expect(groupAverage(values, []).value).toBeNull();
  });
});

describe("differences", () => {
  it("Welch's interval matches a hand computation", () => {
    const d = welch([1, 2, 3, 4], [2, 4, 6])!;
    expect(d.diff).toBeCloseTo(-1.5, 10);
    // se = sqrt(1.6667/4 + 4/3) = 1.3229; df = (0.4167 + 1.3333)^2 / (0.4167^2/3 + 1.3333^2/2) = 3.0625/0.94676
    expect(d.df).toBeCloseTo(3.2347, 3);
    expect(d.hi - d.diff).toBeCloseTo(tCritical(d.df) * 1.32288, 3);
  });

  it("identical groups differ by zero; one value has no interval", () => {
    expect(welch([1, 2, 3], [1, 2, 3])!.diff).toBe(0);
    expect(welch([1], [1, 2])).toBeNull();
    expect(againstValue([10, 20, 30], 5)!.diff).toBe(15);
  });
});

describe("association", () => {
  it("Pearson and Spearman, with ties averaged", () => {
    expect(pearson([1, 2, 3, 4], [2, 4, 6, 8])).toBeCloseTo(1, 10);
    expect(pearson([1, 2, 3, 4], [8, 6, 4, 2])).toBeCloseTo(-1, 10);
    expect(ranks([10, 20, 20, 30])).toEqual([1, 2.5, 2.5, 4]);
    expect(spearman([1, 2, 3, 4], [1, 4, 9, 16])).toBeCloseTo(1, 10);  // monotone, not linear
    expect(pearson([1, 2, 3, 4], [1, 4, 9, 16])!).toBeLessThan(1);      // negative control
  });

  it("least squares recovers a line, and its residuals sum to zero", () => {
    const fit = ols([1, 2, 3, 4], [3, 5, 7, 10])!;
    expect(fit.slope).toBeCloseTo(2.3, 10);
    expect(fit.residuals.reduce((a, b) => a + b, 0)).toBeCloseTo(0, 10);
  });
});

describe("space", () => {
  const line = { A: ["B"], B: ["A", "C"], C: ["B", "D"], D: ["C"] };

  it("Moran's I is positive when neighbours resemble each other and negative when they alternate", () => {
    expect(moransI({ A: 1, B: 2, C: 8, D: 9 }, line)!.I).toBeGreaterThan(0);
    expect(moransI({ A: 1, B: 9, C: 1, D: 9 }, line)!.I).toBeLessThan(0);
  });

  it("the neighbours' mean uses only neighbours with a value", () => {
    expect(neighbourMean({ A: 1, B: null, C: 5, D: 7 }, line)).toEqual({ A: null, B: 3, C: 7, D: 5 });
  });

  it("the nearest states on standardised measures, and a state too thinly measured is left out", () => {
    const rows = { A: [1, 1], B: [1.1, 1], C: [5, 5], D: [null, null] };
    const near = nearest(rows, "A");
    expect(near[0].iso3).toBe("B");
    expect(near.map((x) => x.iso3)).not.toContain("D");
  });
});
