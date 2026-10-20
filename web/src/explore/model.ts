// The Data tab's documents (09_explore.py) and its state. The state lives in the address (#data=...), so any view can
// be shared; custom groups are also remembered in this browser.

import { useEffect, useState } from "react";
import { load } from "../data";

export interface Measure {
  id: string; ds: string; code: string; label: string; unit: string; topic: string; n: number; y: [number, number];
  polarity?: string; interval?: string;
  ref?: number;  // the year to open on: the ASI's reference year for its own measures
}
export interface Catalogue {
  floor: number; first_year: number; names: Record<string, string>;
  sources: Record<string, { name: string; licence: string; link: string }>;
  measures: Measure[];
}
type Grid = Record<string, (number | null)[]>;
export interface Series { y: [number, number]; v: Grid; lo?: Grid; hi?: Grid; f?: Record<string, number>; tier?: Grid }
export interface Group {
  id: string; name: string; kind: "rec" | "organisation" | "custom" | "category"; members: string[];
  basis?: string; source?: string;
}
export interface GroupsDoc {
  note: string; groups: Group[];
  history: { group: string; date: string; change: string; source: string }[];
  crosscheck: { group: string; wikidata_count: number; owner_only: string[]; wikidata_only: string[] }[];
}
export interface Attribute {
  id: string; label: string; source: string; kind: string; asof: string;
  values: Record<string, string | string[]>; order?: string[];
}
export interface StatesDoc {
  attributes: Attribute[];
  neighbours: Record<string, string[]>;
  coverage?: Record<string, Record<string, number>>;  // each dataset's share of series covering each state
}

export type View = "lines" | "multiples" | "slope" | "dumbbell" | "distribution" | "intervals" | "scatter"
  | "trajectory" | "heatmap" | "profile" | "composition" | "categories" | "memberships" | "table";
export type Item = { t: "s"; id: string } | { t: "g"; id: string; mode: "members" | "average" };
export type AverageHow = "mean" | "median" | "population" | "gdp";

export interface ExploreState {
  items: Item[];
  measure: string;      // the y measure
  x: string;            // the scatter's x measure
  view: View;
  year: number | null;  // the year of snapshot views and the map; null means the measure's latest well-covered year
  avg: AverageHow;
  attr: string;         // the category the Categories view and the category groups use
  custom: Group[];      // groups the reader made
}

export const DEFAULT: ExploreState = {
  items: [], measure: "asi/headline", x: "wdi/NY.GDP.PCAP.PP.CD", view: "lines", year: null, avg: "mean",
  attr: "income", custom: [],
};

/** The state as the address carries it, and back. An unreadable address gives the default view. */
export function toHash(s: ExploreState): string {
  return "data=" + encodeURIComponent(JSON.stringify(s));
}
export function fromHash(hash: string): ExploreState | null {
  const m = hash.match(/^#?data=(.*)$/);
  if (!m) return null;
  try {
    return { ...DEFAULT, ...JSON.parse(decodeURIComponent(m[1])) };
  } catch {
    return null;
  }
}

const CUSTOM_KEY = "asi-explore-custom-groups";
export function rememberedGroups(): Group[] {
  try {
    return JSON.parse(localStorage.getItem(CUSTOM_KEY) ?? "[]");
  } catch {
    return [];
  }
}
export function rememberGroups(groups: Group[]): void {
  try {
    localStorage.setItem(CUSTOM_KEY, JSON.stringify(groups));
  } catch { /* a private window keeps them in the address only */ }
}

// ── loading: each file once, then from memory ────────────────────────────────────────────────────────────────
const cache = new Map<string, Promise<unknown>>();
function once<T>(path: string): Promise<T> {
  if (!cache.has(path)) cache.set(path, load<T>(path));
  return cache.get(path) as Promise<T>;
}
export const fileId = (code: string) => code.replace(/[^A-Za-z0-9._-]/g, "_");
export const loadCatalogue = () => once<Catalogue>("data/explore/catalogue.json");
export const loadGroups = () => once<GroupsDoc>("data/explore/groups.json");
export const loadStates = () => once<StatesDoc>("data/explore/states.json");
export function loadSeries(id: string): Promise<Series> {
  const i = id.indexOf("/");
  return once<Series>(`data/explore/s/${id.slice(0, i)}/${fileId(id.slice(i + 1))}.json`);
}

/** Series by id, loaded as they are asked for; a series still loading is undefined. */
export function useSeries(ids: string[]): Record<string, Series | undefined> {
  const [got, setGot] = useState<Record<string, Series>>({});
  const key = ids.join("|");
  useEffect(() => {
    let live = true;
    ids.filter((id) => id && !got[id]).forEach((id) => loadSeries(id).then((s) => live && setGot((g) => ({ ...g, [id]: s })))
      .catch(() => undefined));
    return () => { live = false; };
  }, [key]);  // eslint-disable-line react-hooks/exhaustive-deps
  return got;
}

/** One state's value in a series at a year, or null. */
export function at(s: Series | undefined, iso3: string, year: number): number | null {
  if (!s) return null;
  const v = s.v[iso3]?.[year - s.y[0]];
  return v === undefined ? null : v;
}

/** Every state's value at a year. */
export function snapshot(s: Series | undefined, year: number): Record<string, number | null> {
  if (!s) return {};
  return Object.fromEntries(Object.keys(s.v).map((k) => [k, at(s, k, year)]));
}

/** The latest year at which at least half the states the series covers have a value. */
export function latestCovered(s: Series | undefined): number | null {
  if (!s) return null;
  const n = Object.keys(s.v).length;
  for (let y = s.y[1]; y >= s.y[0]; y--) {
    const have = Object.values(s.v).filter((row) => row[y - s.y[0]] !== null && row[y - s.y[0]] !== undefined).length;
    if (have * 2 >= n) return y;
  }
  return s.y[1];
}

/** Every group the tab offers: the RECs, the organisations, one per category value, and the reader's own. */
export function allGroups(doc: GroupsDoc | undefined, states: StatesDoc | undefined, custom: Group[]): Group[] {
  const cats: Group[] = [];
  for (const a of states?.attributes ?? []) {
    const byValue = new Map<string, string[]>();
    for (const [iso3, v] of Object.entries(a.values)) {
      for (const x of Array.isArray(v) ? v : [v]) byValue.set(x, [...(byValue.get(x) ?? []), iso3]);
    }
    for (const [value, members] of byValue) {
      if (members.length > 1) cats.push({ id: `cat:${a.id}=${value}`, name: `${a.label}: ${value}`, kind: "category",
        members: members.sort(), source: a.source });
    }
  }
  return [...(doc?.groups ?? []), ...cats, ...custom];
}
