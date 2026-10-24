// The "Spreading instability" tab's document (11_instability.py writes data/instability.json and geo/events.json):
// the owner's conflict theatres, each with UCDP's deaths by month and its spread by stated rules. Nothing here computes
// a figure but a theatre's monthly total, the sum of its states' (derived, said so where shown).

export interface NewGround { actor: string; iso3: string; first: string; events: number; deaths: number }

export interface Market { platform: string; id: string; question: string }

export interface PublishedMap { title: string; publisher: string; url: string; revised: string; read: string }

export interface Theatre {
  id: string; name: string; states: string[]; summary: string; links: string[]; markets: Market[]; maps: PublishedMap[];
  deaths: Record<string, number[]>; range: { low: number; best: number; high: number }; areas_now: number; areas_before: number; new_ground: NewGround[];
}

export interface InstabilityDoc {
  last_month: string; window: [string, string]; months: string[]; sources: string[];
  rules: { deaths: string; areas: string; new_ground: string };
  states: Record<string, { deaths: number; low: number; high: number; events: number }>;
  theatres: Theatre[];
}

// the events by type of violence, in three of the map's validated point hues (validate_palette.js, every pair, dark
// imagery-like surface #2b2f25: all checks pass; the relief its warnings ask for is the legend naming each type)
export const TYPE_COLOURS: Record<string, string> = {
  "state-based": "#d55181", "non-state": "#c98500", "one-sided": "#3987e5",
};

/** A theatre's deaths by month: the sum of its states' (a state in two theatres counts in each). */
export function theatreMonthly(t: Theatre): number[] {
  const rows = Object.values(t.deaths);
  return rows.length ? rows[0].map((_, i) => rows.reduce((a, r) => a + (r[i] ?? 0), 0)) : [];
}

/** The theatre's deaths in its last twelve months, and the twelve before (derived, the sum of the months). */
export function twelveMonths(t: Theatre): { now: number; before: number } {
  const m = theatreMonthly(t), n = m.length;
  const sum = (a: number, b: number) => m.slice(Math.max(a, 0), b).reduce((x, y) => x + y, 0);
  return { now: sum(n - 12, n), before: sum(n - 24, n - 12) };
}
