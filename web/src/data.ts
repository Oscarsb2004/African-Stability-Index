// The files 05_web.py writes to public/. Every type mirrors a document's shape; nothing here computes a figure.

export type Section = "stability" | "economy" | "finance" | "infrastructure" | "wonders" | "instability" | "data";

export interface Figure {
  value: number | null;
  period: string | null;
  n: number;
  lower?: number | null;
  upper?: number | null;
  values?: { value: number; period: string }[] | number[];
  periods?: string[];
}

export interface FigureSpec {
  id: string;
  label: string;
  unit: string;
  shell: string;
  derived: boolean;
  dataset?: string;
  series?: string;
  unbound?: string;
  note?: string;
}

export interface SectionSpec {
  id: string;
  title: string;
  order: number;
  dimension: string;
  about: string;
  figures: FigureSpec[];
}

export interface SectionsDoc {
  format: string;
  datasets: { name: string; publisher: string; licence: string; attribution: string; link?: string }[];
  sections: SectionSpec[];
  areas: Record<string, Record<string, Record<string, Figure>>>;
  names: Record<string, string>;
}

export interface StabilityDoc {
  reference_year: number;
  inputs: string;
  n_ranked: number;
  n_tiers: number;
  method: string;
  classes: { rule: string; breaks: number[] };
  pillars: Record<string, { name: string; indicators: string[] }>;
  indicators: Record<string, { display_name: string; series_code: string; polarity: string }>;
  countries: Record<string, {
    // the headline with its 95% interval, tier and rank band (edition 2, step 8)
    composite: { score: number; reliability: string; ci_low: number | null; ci_high: number | null;
      tier: number | null; band_best: number | null; band_worst: number | null };
    narrative: string[];  // the data narrative (step 10, part A): templates filled with the panel's numbers
    history: { years: number[]; scores: (number | null)[] };
    pillars: Record<string, { score: number | null; reliability: string; observed: number; indicators: number }>;
    indicators: Record<string, { raw: number | null; score: number | null; provenance: string;
      source_year: number | null }>;
  }>;
}

export interface MetaDoc {
  sources: { name: string; licence: string; link: string }[];
  imagery: { tiles: string; attribution: string; max_zoom: number };
}

// method.json: what the "How the index is built" page shows; every figure comes from the panel or the registry
export interface MethodDoc {
  reference_year: number;
  n_states: number;
  n_ranked: number;
  n_scored: number;
  n_descriptive: number;
  tiers: number[];
  band_median_width: number;
  se_median: number;
  wgi_share: number;
  rules: {
    admission_floor: number; carry_forward_years: number; reference_coverage: number; outlier_sd: number;
    outlier_replace_sd: number; outlier_trim: number; zero_heavy: number; overlap_bar: number; overlap_year: number;
    interval_level: number; band_z: number; min_pillars: number; reliable_at: number; thin_at: number;
    max_imputed: number;
  };
  method_roles: Record<string, string>;
  uncertainty: { interval: string; bands: string; tiers: string };
  pillars: { id: string; name: string; indicators: { id: string; name: string; database: string; polarity: string;
    role: string; log: boolean; goalposts: string | null; weight: number | null; cluster: string | null }[] }[];
  clusters: { slot: string; members: string[]; pairs: { a: string; b: string; n: number; partial_r: number }[] }[];
  robustness: { agreement: Record<string, number>; worst_weighting: number; verdict: string; measured_only: number };
}

// The comparison colours (dataviz validate_palette.js, dark, surface #111111: all checks pass, worst adjacent CVD
// delta E 8.4, so every line also carries a direct label). At most four countries are compared at once.
export const COMPARE = ["#3987e5", "#d95926", "#199e70", "#c98500"];

export interface Photo {
  src: string;
  thumb: string;
  page: string;
  licence: string;
  licence_url: string;
  artist: string;
  credit: string;
}

export interface Wonder {
  id: string;
  name: string;
  description: string;
  kinds: string[];
  countries: string[];
  lon: number;
  lat: number;
  notability: number;
  photos: Photo[];
}

export interface WondersDoc {
  edition: string;
  rule: string;
  sources: { name: string; licence: string; link: string }[];
  wonders: Wonder[];
}

export function asset(path: string): string {
  return `${import.meta.env.BASE_URL}${path}`;
}

export async function load<T>(path: string): Promise<T> {
  const r = await fetch(asset(path));
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json() as Promise<T>;
}

// A file several parts of the site read (countries.json, links.json, places.json): fetched and parsed once, then
// shared. A failed load is forgotten, so the next caller tries again.
const once = new Map<string, Promise<unknown>>();
export function loadOnce<T>(path: string): Promise<T> {
  let p = once.get(path);
  if (!p) {
    p = load<T>(path).catch((e) => { once.delete(path); throw e; });
    once.set(path, p);
  }
  return p as Promise<T>;
}

// ── formatting: visuals show one decimal (P33) ────────────────────────────────────────────────────────────────

export function fmt(v: number | null | undefined, unit = ""): string {
  if (v === null || v === undefined) return "—";
  if (unit === "current US$") {
    const a = Math.abs(v), sign = v < 0 ? "−" : "";
    if (a >= 1e12) return `${sign}$${(a / 1e12).toFixed(1)} tn`;
    if (a >= 1e9) return `${sign}$${(a / 1e9).toFixed(1)} bn`;
    if (a >= 1e6) return `${sign}$${(a / 1e6).toFixed(1)} m`;
    return `${sign}$${Math.round(a).toLocaleString("en")}`;
  }
  if (unit === "companies") return Math.round(v).toLocaleString("en");
  if (unit === "current international $") return `$${Math.round(v).toLocaleString("en")}`;
  const s = Math.abs(v) >= 1000 ? Math.round(v).toLocaleString("en") : v.toFixed(1);
  return unit.startsWith("%") ? `${s}%` : s;
}

export function people(n: number): string {
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)} m`;
  if (n >= 1e3) return `${Math.round(n / 1e3)}k`;
  return String(n);
}

// The validated sequential ramp (dataviz validate_palette.js --ordinal, dark, surface #111111: all checks pass).
// Low scores are dark, high scores light: on a dark surface the light end is "more". The breaks come from
// stability.json (fifths of the member states), never from here.
export const RAMP = ["#4b3c9e", "#6650c4", "#8771e8", "#ab99f6", "#d3c9ff"];

// The Data tab's diverging ramp, for a measure whose values have both signs: red below zero, blue above (the
// reference palette's diverging pair), each arm darker toward zero. Each arm passes validate_palette.js --ordinal
// (dark, surface #111111; its dark end at 3.58:1 and 3.50:1), and the two arms clear the colour-blind check against
// each other (2026-10-23). Zero is a boundary, not a grey class, so it is never mistaken for "no value".
export const DIVERGING = ["#ef8a84", "#b54848", "#256abf", "#6da7ec"];

export function rampColour(score: number | null, breaks: number[]): string {
  if (score === null) return "#3a3a3a";
  let i = 0;
  while (i < breaks.length && score >= breaks[i]) i++;
  return RAMP[i];
}
