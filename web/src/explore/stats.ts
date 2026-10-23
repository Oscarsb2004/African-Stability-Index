// The Data tab's statistics (P105). Every figure here is derived by a stated formula and labelled so on the page;
// nothing is filled, imputed or rescaled, and each state counts once unless the reader chooses a weighting.
// Tested in stats.test.ts, each rule with a negative control.

export type Values = Record<string, number | null | undefined>;
export type Average = "mean" | "median" | "population" | "gdp";

const ok = (x: number | null | undefined): x is number => typeof x === "number" && Number.isFinite(x);

export function mean(xs: number[]): number | null {
  return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
}

export function median(xs: number[]): number | null {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b), m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/** The sample standard deviation (n − 1). */
export function sd(xs: number[]): number | null {
  if (xs.length < 2) return null;
  const m = mean(xs) as number;
  return Math.sqrt(xs.reduce((a, x) => a + (x - m) ** 2, 0) / (xs.length - 1));
}

/** The quantile of type 7 (linear), as pandas and R use by default. */
export function quantile(xs: number[], p: number): number | null {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b), h = (s.length - 1) * p, lo = Math.floor(h);
  return s[lo] + (h - lo) * ((s[Math.min(lo + 1, s.length - 1)]) - s[lo]);
}

/** The two-sided Student t critical value for a level such as 0.95: exact for 1 and 2 degrees of freedom, the
 *  Cornish-Fisher expansion (Abramowitz & Stegun 26.7.5) beyond, accurate to about 0.001 from 3. */
export function tCritical(df: number, level = 0.95): number {
  const p = 1 - (1 - level) / 2;
  if (df <= 1) return Math.tan(Math.PI * (p - 0.5));
  if (df < 3) return (2 * p - 1) / Math.sqrt(2 * p * (1 - p));
  const z = normalQuantile(p), z3 = z ** 3, z5 = z ** 5, z7 = z ** 7, z9 = z ** 9;
  return z + (z3 + z) / (4 * df) + (5 * z5 + 16 * z3 + 3 * z) / (96 * df ** 2)
    + (3 * z7 + 19 * z5 + 17 * z3 - 15 * z) / (384 * df ** 3)
    + (79 * z9 + 776 * z7 + 1482 * z5 - 1920 * z3 - 945 * z) / (92160 * df ** 4);
}

/** The standard normal quantile (Acklam's algorithm, relative error below 1.2e-9). */
export function normalQuantile(p: number): number {
  const a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.357751867269, -30.66479806614716,
    2.506628277459239];
  const b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572];
  const c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968,
    2.938163982698783];
  const d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416];
  const lo = 0.02425;
  if (p < lo) {
    const q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p > 1 - lo) return -normalQuantile(1 - p);
  const q = p - 0.5, r = q * q;
  return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
    / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
}

export interface GroupAverage {
  value: number | null;     // null when fewer than half the members have a value
  n: number;                // members with a value
  of: number;               // members
  min: number | null;
  max: number | null;
  ci: [number, number] | null;  // the t-interval of the members' mean: the spread among them, not measurement error
}

/** A group's average at one year. Each member counts once (the mean), unless the reader chooses the median or a
 *  weighting by population or GDP; a member without a weight is left out of a weighted average. */
export function groupAverage(values: Values, members: string[], how: Average = "mean",
  weights?: Values, level = 0.95): GroupAverage {
  const have = members.filter((m) => ok(values[m]));
  const xs = have.map((m) => values[m] as number);
  const out: GroupAverage = { value: null, n: xs.length, of: members.length, min: xs.length ? Math.min(...xs) : null,
    max: xs.length ? Math.max(...xs) : null, ci: null };
  if (xs.length === 0 || xs.length * 2 < members.length) return out;
  if (how === "median") out.value = median(xs);
  else if (how === "mean") out.value = mean(xs);
  else {
    const w = have.map((m) => weights?.[m]);
    const pairs = xs.map((x, i) => [x, w[i]] as const).filter(([, wi]) => ok(wi) && (wi as number) > 0);
    const total = pairs.reduce((a, [, wi]) => a + (wi as number), 0);
    out.value = total > 0 ? pairs.reduce((a, [x, wi]) => a + x * (wi as number), 0) / total : null;
  }
  const s = sd(xs);
  if (how === "mean" && s !== null && out.value !== null) {
    const half = tCritical(xs.length - 1, level) * s / Math.sqrt(xs.length);
    out.ci = [out.value - half, out.value + half];
  }
  return out;
}

export interface Difference { diff: number; lo: number; hi: number; df: number }

/** The difference of two means with Welch's interval (unequal variances). Members shared by both groups count in
 *  both, so the two samples are not independent: the page says so beside the interval. */
export function welch(a: number[], b: number[], level = 0.95): Difference | null {
  const sa = sd(a), sb = sd(b);
  if (sa === null || sb === null) return null;
  const va = sa ** 2 / a.length, vb = sb ** 2 / b.length, se = Math.sqrt(va + vb);
  if (se === 0) return null;
  const df = (va + vb) ** 2 / (va ** 2 / (a.length - 1) + vb ** 2 / (b.length - 1));
  const diff = (mean(a) as number) - (mean(b) as number), half = tCritical(df, level) * se;
  return { diff, lo: diff - half, hi: diff + half, df };
}

/** A group's mean less one state's value, with the one-sample t-interval of the group's mean. */
export function againstValue(a: number[], x: number, level = 0.95): Difference | null {
  const s = sd(a);
  if (s === null) return null;
  const diff = (mean(a) as number) - x, half = tCritical(a.length - 1, level) * s / Math.sqrt(a.length);
  return { diff, lo: diff - half, hi: diff + half, df: a.length - 1 };
}

/** Pearson's r over the pairs where both are present. */
export function pearson(x: number[], y: number[]): number | null {
  if (x.length < 3 || x.length !== y.length) return null;
  const mx = mean(x) as number, my = mean(y) as number;
  let sxy = 0, sxx = 0, syy = 0;
  x.forEach((xi, i) => { sxy += (xi - mx) * (y[i] - my); sxx += (xi - mx) ** 2; syy += (y[i] - my) ** 2; });
  return sxx && syy ? sxy / Math.sqrt(sxx * syy) : null;
}

/** Ranks from 1, ties given their average rank. */
export function ranks(xs: number[]): number[] {
  const order = xs.map((x, i) => [x, i] as const).sort((a, b) => a[0] - b[0]);
  const out = new Array<number>(xs.length);
  for (let i = 0; i < order.length;) {
    let j = i;
    while (j + 1 < order.length && order[j + 1][0] === order[i][0]) j++;
    for (let k = i; k <= j; k++) out[order[k][1]] = (i + j) / 2 + 1;
    i = j + 1;
  }
  return out;
}

/** Spearman's rho: Pearson's r on the ranks. */
export function spearman(x: number[], y: number[]): number | null {
  return pearson(ranks(x), ranks(y));
}

/** Ordinary least squares of y on x: slope, intercept, and the residual of each point. */
export function ols(x: number[], y: number[]): { slope: number; intercept: number; residuals: number[] } | null {
  if (x.length < 3) return null;
  const mx = mean(x) as number, my = mean(y) as number;
  const sxx = x.reduce((a, xi) => a + (xi - mx) ** 2, 0);
  if (!sxx) return null;
  const slope = x.reduce((a, xi, i) => a + (xi - mx) * (y[i] - my), 0) / sxx, intercept = my - slope * mx;
  return { slope, intercept, residuals: y.map((yi, i) => yi - (intercept + slope * x[i])) };
}

/** Moran's I with binary contiguity weights: above 0, neighbours' values resemble each other; near −1/(n−1), no
 *  pattern. Only states with a value and at least one neighbour with a value enter. */
export function moransI(values: Values, neighbours: Record<string, string[]>): { I: number; n: number } | null {
  const keys = Object.keys(neighbours).filter((k) => ok(values[k]) && neighbours[k].some((j) => ok(values[j])));
  if (keys.length < 3) return null;
  const m = mean(keys.map((k) => values[k] as number)) as number;
  let num = 0, w = 0;
  for (const i of keys) for (const j of neighbours[i]) {
    if (!keys.includes(j)) continue;
    num += ((values[i] as number) - m) * ((values[j] as number) - m);
    w += 1;
  }
  const den = keys.reduce((a, k) => a + ((values[k] as number) - m) ** 2, 0);
  return w && den ? { I: (keys.length / w) * (num / den), n: keys.length } : null;
}

/** Each state's neighbours' mean (the spatial lag), where at least one neighbour has a value. */
export function neighbourMean(values: Values, neighbours: Record<string, string[]>): Values {
  const out: Values = {};
  for (const [k, ns] of Object.entries(neighbours)) {
    const xs = ns.map((j) => values[j]).filter(ok);
    out[k] = xs.length ? mean(xs) : null;
  }
  return out;
}

/** The fifths of the values present: the four breaks the map's classes use, as the ASI's own map does. */
export function fifths(xs: number[]): number[] {
  return [0.2, 0.4, 0.6, 0.8].map((p) => quantile(xs, p) as number);
}

/** For values with both signs, the three breaks of a diverging map: the median of the values below zero, zero, and
 *  the median of the values above it, so each side has two classes and zero is the boundary between them. Null when
 *  every value has the same sign (or is zero): the map then keeps its fifths. */
export function signedBreaks(xs: number[]): number[] | null {
  const below = xs.filter((x) => x < 0), above = xs.filter((x) => x > 0);
  if (!below.length || !above.length) return null;
  return [median(below) as number, 0, median(above) as number];
}

/** Distances between states over several measures, each standardised to mean 0 and standard deviation 1 across
 *  the states that have it; a pair is compared on the measures both have, and needs at least half of them. */
export function nearest(rows: Record<string, (number | null)[]>, of: string, k = 5): { iso3: string; d: number }[] {
  const keys = Object.keys(rows), m = rows[of]?.length ?? 0;
  const z = Object.fromEntries(keys.map((key) => [key, [] as (number | null)[]]));
  for (let j = 0; j < m; j++) {
    const col = keys.map((key) => rows[key][j]).filter(ok);
    const mu = mean(col), s = sd(col);
    for (const key of keys) {
      const v = rows[key][j];
      z[key][j] = ok(v) && mu !== null && s ? (v - mu) / s : null;
    }
  }
  const out: { iso3: string; d: number }[] = [];
  for (const key of keys) {
    if (key === of) continue;
    const both = z[of].map((a, j) => [a, z[key][j]] as const).filter(([a, b]) => ok(a) && ok(b));
    if (both.length * 2 < m || !both.length) continue;
    out.push({ iso3: key, d: Math.sqrt(both.reduce((s, [a, b]) => s + ((a as number) - (b as number)) ** 2, 0)
      / both.length) });
  }
  return out.sort((a, b) => a.d - b.d).slice(0, k);
}
