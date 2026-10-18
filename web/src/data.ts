// The files 05_web.py writes to public/. Every type mirrors a document's shape; nothing here computes a figure.

export type Section = "stability" | "economy" | "infrastructure" | "wonders";

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
  method: string;
  classes: { rule: string; breaks: number[] };
  pillars: Record<string, { name: string; indicators: string[] }>;
  indicators: Record<string, { display_name: string; series_code: string; polarity: string }>;
  countries: Record<string, {
    composite: { score: number; reliability: string };
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

export function asset(path: string): string {
  return `${import.meta.env.BASE_URL}${path}`;
}

export async function load<T>(path: string): Promise<T> {
  const r = await fetch(asset(path));
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json() as Promise<T>;
}

// ── formatting: visuals show one decimal (P33) ────────────────────────────────────────────────────────────────

export function fmt(v: number | null | undefined, unit = ""): string {
  if (v === null || v === undefined) return "—";
  if (unit === "current US$") {
    const a = Math.abs(v);
    if (a >= 1e12) return `$${(v / 1e12).toFixed(1)} tn`;
    if (a >= 1e9) return `$${(v / 1e9).toFixed(1)} bn`;
    if (a >= 1e6) return `$${(v / 1e6).toFixed(1)} m`;
  }
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

export function rampColour(score: number | null, breaks: number[]): string {
  if (score === null) return "#3a3a3a";
  let i = 0;
  while (i < breaks.length && score >= breaks[i]) i++;
  return RAMP[i];
}
