// The Infrastructure section's layers (P65): the catalogue 10_infrastructure.py writes (geo/infra/layers.json), each
// member state's figures (geo/infra/countries.json), and how each layer is drawn. Nothing here computes a figure: the
// counts and lengths are the stage's, and a card shows a feature's fields under the publisher's own labels.

export interface Field { name: string; label: string }

interface Credit { note: string; licence: string; attribution: string; link: string }

export interface PointLayerInfo extends Credit {
  id: string; title: string; kind: "points"; file: string; count: number; rows?: number;
  withheld?: number; withheld_reason?: string; unplaced: number; placed_by_degrees?: number; fields: Field[];
}

export interface LineLayerInfo extends Credit {
  id: string; title: string; kind: "lines"; count: number; classes: Record<string, number>; class_field: string;
}

export interface Archive { file: string; layers: string[]; licence: string; attribution: string; tiles: number }

export interface LayersDoc {
  points: PointLayerInfo[];
  lines: LineLayerInfo[];
  archives: Record<string, Archive>;
  withheld: { layer: string; reason: string }[];
  rules: { place: string; nearest_km: number; zooms: [number, number] };
}

export interface Port { name: string | null; type: string | null; exports: string[] }

export interface CountryInfra {
  ports?: Port[];
  facilities?: Record<string, number>;
  deposits?: number;
  exploration?: number;
  km?: Record<string, Record<string, number>>;
}

export type CountriesDoc = Record<string, CountryInfra>;

// The reference palette's dark steps (the dataviz skill), one slot per layer. Points and lines are told apart by
// shape, so each group was validated on its own, every pair, against a dark imagery-like surface (#2b2f25):
// validate_palette.js passes both. Points carry a light ring so they read over vegetation and desert alike.
export const COLOURS: Record<string, string> = {
  ports: "#3987e5", facilities: "#c98500", deposits: "#d55181", exploration: "#008300",
  rail: "#9085e9", roads: "#d95926", grid: "#199e70",
};
export const RING = "#f0efec";

// shown when the section opens; deposits and exploration sites are dense, so they wait for a click
export const SHOWN_FIRST = ["ports", "facilities", "rail", "roads", "grid"];

const KM = new Intl.NumberFormat("en", { maximumFractionDigits: 0 });

export function km(v: number): string {
  return `${KM.format(v)} km`;
}

export function totalKm(byClass: Record<string, number>): number {
  return Object.values(byClass).reduce((a, b) => a + b, 0);
}

// a feature's fields for its card, in the catalogue's order and under the publisher's labels; empty ones are left out
export function cardRows(props: Record<string, unknown>, fields: Field[]): [string, string][] {
  const out: [string, string][] = [];
  for (const f of fields) {
    const v = props[f.name];
    if (v === undefined || v === null || v === "") continue;
    out.push([f.label, String(v)]);
  }
  return out;
}

// GeoJSON properties that MapLibre hands back from a click: nested values arrive as JSON text
export function parsed(props: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(props)) {
    if (typeof v === "string" && (v.startsWith("[") || v.startsWith("{"))) {
      try { out[k] = JSON.parse(v); continue; } catch { /* plain text that starts with a bracket */ }
    }
    out[k] = v;
  }
  return out;
}
