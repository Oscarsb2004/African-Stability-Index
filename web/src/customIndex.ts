// A reader's own index (the owner's ruling of 2026-10-23): indicators chosen from the Data tab's catalogue, scored by a
// stated method, combined, named, and kept in the reader's browser. It is derived (P4), "your index, not the ASI", and
// never published by the project. Every rule below is shown to the reader in the builder.

export type Method = "minmax" | "zscore" | "percentile";
export type Aggregate = "mean" | "geometric";

export interface IndexItem { measure: string; label: string; higherIsBetter: boolean }

export interface CustomIndex {
  id: string; name: string; items: IndexItem[]; method: Method; aggregate: Aggregate; year: number; created: string;
}

// a series file of the Data tab: the first and last years, and each state's values year by year
export interface Series { y: [number, number]; v: Record<string, (number | null)[]> }

export const CARRY = 5;          // a value counts for up to 5 years after it, as the ASI's carry-forward
export const FIRST_YEAR = 2000;  // the range a min-max scale is taken over starts here, as the Data tab's
export const MIN_SHARE = 0.5;    // a state is scored only with at least half of the chosen indicators

export const METHODS: { id: Method; label: string; formula: string; recommended?: boolean }[] = [
  { id: "minmax", recommended: true, label: "Min–max, 0 to 100",
    formula: "100 × (value − lowest) ÷ (highest − lowest), the lowest and highest taken over the 54 states' values since 2000 (as the ASI's observed goalposts); turned around where lower is better" },
  { id: "zscore", label: "Z-scores",
    formula: "(value − mean) ÷ standard deviation, across the states with a value in the year; sign turned where lower is better" },
  { id: "percentile", label: "Percentile ranks, 0 to 100",
    formula: "100 × (rank − 1) ÷ (states − 1), ties sharing their mean rank; turned around where lower is better" },
];

export const AGGREGATES: { id: Aggregate; label: string; formula: string; recommended?: boolean }[] = [
  { id: "mean", recommended: true, label: "Arithmetic mean", formula: "the mean of a state's scores, each indicator weighing the same" },
  { id: "geometric", label: "Geometric mean",
    formula: "the geometric mean of a state's scores, each floored at 1 (min–max and percentile scales only), so a low score is not made up by a high one" },
];

/** A state's value for a year: its own, else its latest within CARRY years before; null when none. */
export function valueAt(s: Series, iso3: string, year: number): number | null {
  const row = s.v[iso3];
  if (!row) return null;
  for (let y = year; y >= Math.max(s.y[0], year - CARRY); y--) {
    const v = row[y - s.y[0]];
    if (typeof v === "number" && Number.isFinite(v)) return v;
  }
  return null;
}

/** Each state's score on one indicator, by the method. */
export function scoreItem(s: Series, item: IndexItem, method: Method, year: number, states: string[]):
  Record<string, number> {
  const at: Record<string, number> = {};
  for (const iso3 of states) {
    const v = valueAt(s, iso3, year);
    if (v !== null) at[iso3] = v;
  }
  const xs = Object.values(at), sign = item.higherIsBetter ? 1 : -1, out: Record<string, number> = {};
  if (!xs.length) return out;
  if (method === "minmax") {
    const all = states.flatMap((iso3) => (s.v[iso3] ?? []).filter((v, i): v is number =>
      typeof v === "number" && s.y[0] + i >= FIRST_YEAR && s.y[0] + i <= year));
    const lo = Math.min(...all, ...xs), hi = Math.max(...all, ...xs);
    for (const [k, v] of Object.entries(at)) {
      const t = hi > lo ? (100 * (v - lo)) / (hi - lo) : 50;
      out[k] = item.higherIsBetter ? t : 100 - t;
    }
  } else if (method === "zscore") {
    const mu = xs.reduce((a, b) => a + b, 0) / xs.length;
    const sd = Math.sqrt(xs.reduce((a, b) => a + (b - mu) ** 2, 0) / Math.max(xs.length - 1, 1));
    for (const [k, v] of Object.entries(at)) out[k] = sd > 0 ? (sign * (v - mu)) / sd : 0;
  } else {
    const sorted = Object.entries(at).sort((a, b) => sign * (a[1] - b[1]));
    const n = sorted.length;
    let i = 0;
    while (i < n) {
      let j = i;
      while (j + 1 < n && sorted[j + 1][1] === sorted[i][1]) j++;
      const rank = (i + j) / 2;  // ties share their mean rank (0-based)
      for (let k = i; k <= j; k++) out[sorted[k][0]] = n > 1 ? (100 * rank) / (n - 1) : 50;
      i = j + 1;
    }
  }
  return out;
}

/** Each state's index value and how many of the chosen indicators it had; a state below MIN_SHARE is unscored. */
export function scoreIndex(ix: CustomIndex, series: Record<string, Series>, states: string[]):
  { values: Record<string, number | null>; coverage: Record<string, number> } {
  const per = ix.items.map((it) => series[it.measure] ? scoreItem(series[it.measure], it, ix.method, ix.year, states) : {});
  const values: Record<string, number | null> = {}, coverage: Record<string, number> = {};
  const geometric = ix.aggregate === "geometric" && ix.method !== "zscore";
  for (const iso3 of states) {
    const xs = per.map((p) => p[iso3]).filter((v): v is number => typeof v === "number");
    coverage[iso3] = xs.length;
    if (!xs.length || xs.length < Math.ceil(ix.items.length * MIN_SHARE)) { values[iso3] = null; continue; }
    values[iso3] = geometric
      ? Math.exp(xs.reduce((a, v) => a + Math.log(Math.max(v, 1)), 0) / xs.length)
      : xs.reduce((a, b) => a + b, 0) / xs.length;
  }
  return { values, coverage };
}

/** The series of an index's indicators, from the Data tab's files; one that fails to load is left out. */
export async function loadIndexSeries(ix: CustomIndex): Promise<Record<string, Series>> {
  const { loadSeries } = await import("./explore/model");
  const got = await Promise.all(ix.items.map((it) => loadSeries(it.measure).then((s) => [it.measure, s] as const,
    () => null)));
  return Object.fromEntries(got.filter((g): g is readonly [string, Series] => g !== null));
}

// ── kept in the reader's browser ─────────────────────────────────────────────────────────────────────────────
const KEY = "asi-custom-indices";

export function rememberedIndices(): CustomIndex[] {
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as CustomIndex[]) : [];
  } catch { return []; }
}

export function rememberIndices(list: CustomIndex[]): void {
  try { window.localStorage.setItem(KEY, JSON.stringify(list)); } catch { /* private window: kept for this visit */ }
}

/** A shareable address for an index: its definition in the hash, never its values. */
export function indexHash(ix: CustomIndex): string {
  return "index=" + encodeURIComponent(JSON.stringify({ ...ix, id: undefined }));
}

export function fromIndexHash(hash: string): CustomIndex | null {
  const m = hash.match(/index=([^&]+)/);
  if (!m) return null;
  try {
    const ix = JSON.parse(decodeURIComponent(m[1])) as CustomIndex;
    if (!ix.name || !Array.isArray(ix.items) || !ix.items.length) return null;
    return { ...ix, id: `shared-${Date.now()}` };
  } catch { return null; }
}
