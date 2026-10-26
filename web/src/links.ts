// The links between states (registry/links.yaml, the owner's compilation; 11_instability.py writes geo/links.json):
// who backs whom in Africa's conflicts. Nothing here makes a fact: each card is the registry's, with its sources.
// A link is listed only when a UN panel, the government concerned or a UN human-rights investigation names it (the
// rule, R7); the coverage list says how much of each UN panel's latest report has been read, so the site can say what
// the record does not yet hold.

export interface LinkSource { tier: string; publisher: string; title: string; url: string; date: string; read: string }

export interface Link {
  id: string; from: string; to: string; actor?: string; conflict: string; kind: string;
  status: "confirmed" | "reported"; since: string; until?: string; summary: string; sources: LinkSource[];
  historical: boolean; from_name: string; to_name: string;
}

export interface Coverage { regime: string; report: string; date: string; read: "in full" | "in part" | "not yet" }

export interface LinksDoc {
  type: "FeatureCollection";
  kinds: Record<string, string>;
  tiers: Record<string, string>;
  coverage: Coverage[];
  features: { type: "Feature"; geometry: { type: "LineString"; coordinates: [number, number][] }; properties: Link }[];
}

// One hue per kind, the map's validated point hues (validate_palette.js, every pair, dark imagery-like surface
// #2b2f25, 2026-10-23: all checks pass, with a colour-blind warning between green and yellow and a contrast warning on
// green). The relief the warnings require: every line carries a light casing, and every card names its kind in words.
export const KIND_COLOURS: Record<string, string> = {
  forces: "#d55181", contractors: "#c98500", arms: "#3987e5", political: "#008300",
};

const QUALIFYING = ["un-panel", "government", "un-rights"];

/** A state's links, as backer or as the state supported; the more recent first, the historical last. */
export function linksOf(doc: LinksDoc | null, iso3: string | null): Link[] {
  if (!doc || !iso3) return [];
  return doc.features.map((f) => f.properties).filter((l) => l.from === iso3 || l.to === iso3)
    .sort((a, b) => Number(a.historical) - Number(b.historical) || b.since.localeCompare(a.since));
}

/** A link's heading: "United Arab Emirates → Sudan · Rapid Support Forces (RSF)". */
export function heading(l: Link): string {
  return `${l.from_name} → ${l.to_name}${l.actor ? ` · ${l.actor}` : ""}`;
}

/** The status in the words of the rule, the kind of source that qualifies it, and the years: "Confirmed by a UN
 * Security Council Panel or Group of Experts · since 2021". */
export function standing(l: Link, tiers: Record<string, string> = {}): string {
  const years = l.until ? `${l.since}–${l.until}, ended` : `since ${l.since}`;
  const basis = l.sources.find((s) => QUALIFYING.includes(s.tier))?.tier;
  const by = basis && tiers[basis] ? ` by ${tiers[basis].replace(/^A /, "a ").replace(/^The /, "the ")}` : "";
  return `${l.status === "confirmed" ? "Confirmed" : "Reported as credible"}${by} · ${years}`;
}

/** What the line's far end is called on the map: the armed actor's short name ("RSF" from "Rapid Support Forces
 * (RSF)"), or nothing where the state's own government is backed. */
export function actorLabel(l: Link): string | null {
  if (!l.actor) return null;
  return l.actor.match(/\(([^)]+)\)\s*$/)?.[1] ?? l.actor;
}

/** The record's limits in one line: how many links, and how much of the UN panels' latest reports has been read. */
export function coverageNote(doc: LinksDoc): string {
  const full = doc.coverage.filter((c) => c.read === "in full").length;
  return `${doc.features.length} links recorded. Not a complete record: ${full} of ${doc.coverage.length} UN panels' ` +
    `latest reports read in full so far.`;
}

/** The box around every line of these links, [west, south, east, north], so the map can show both their ends. */
export function linksBounds(doc: LinksDoc | null, ids: string[]): [number, number, number, number] | null {
  const lines = doc?.features.filter((f) => ids.includes(f.properties.id)) ?? [];
  if (!lines.length) return null;
  const pts = lines.flatMap((f) => f.geometry.coordinates);
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}
