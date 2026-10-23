// The links between states (registry/links.yaml, the owner's compilation; 11_instability.py writes geo/links.json):
// who backs whom in Africa's conflicts. Nothing here makes a fact: each card is the registry's, with its sources.

export interface LinkSource { publisher: string; title: string; url: string; date: string; read: string }

export interface Link {
  id: string; from: string; to: string; actor?: string; conflict: string; kind: string;
  status: "confirmed" | "reported"; since: string; until?: string; summary: string; sources: LinkSource[];
  historical: boolean; from_name: string; to_name: string;
}

export interface LinksDoc {
  type: "FeatureCollection";
  kinds: Record<string, string>;
  features: { type: "Feature"; geometry: { type: "LineString"; coordinates: [number, number][] }; properties: Link }[];
}

// One hue per kind, the map's validated point hues (validate_palette.js, every pair, dark imagery-like surface
// #2b2f25, 2026-10-23: all checks pass, with a colour-blind warning between green and yellow and a contrast warning on
// green). The relief the warnings require: every line carries a light casing, and every card names its kind in words.
export const KIND_COLOURS: Record<string, string> = {
  forces: "#d55181", contractors: "#c98500", arms: "#3987e5", political: "#008300",
};

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

/** The status in words, as its sources put it, and the years. */
export function standing(l: Link): string {
  const years = l.until ? `${l.since}–${l.until}` : `since ${l.since}`;
  return `${l.status === "confirmed" ? "Confirmed by its source" : "Reported by its source"} · ${years}`;
}
