// links.ts on invented links: the standing in the rule's words, the far end's label, the coverage note and the box
// that holds both ends. Each rule has a negative control.

import { describe, expect, it } from "vitest";
import { actorLabel, coverageNote, type Link, linksBounds, type LinksDoc, linksOf, standing } from "./links";

const link = (over: Partial<Link>): Link => ({
  id: "x", from: "XXX", to: "AAA", conflict: "C", kind: "arms", status: "reported", since: "2023", summary: "S.",
  sources: [{ tier: "context", publisher: "News", title: "T", url: "u", date: "d", read: "r" },
    { tier: "un-panel", publisher: "Panel", title: "T", url: "u", date: "d", read: "r" }],
  historical: false, from_name: "Xland", to_name: "Aland", ...over,
});
const TIERS = { "un-panel": "A UN Security Council Panel or Group of Experts", context: "Context only" };
const doc = (links: Link[], coords: [number, number][][]): LinksDoc => ({
  type: "FeatureCollection", kinds: {}, tiers: TIERS,
  coverage: [{ regime: "R1", report: "S/1", date: "d", read: "in full" }, { regime: "R2", report: "S/2", date: "d",
    read: "not yet" }],
  features: links.map((l, i) => ({ type: "Feature", geometry: { type: "LineString", coordinates: coords[i] },
    properties: l })),
});

describe("links between states", () => {
  it("names the qualifying kind of source, never the news that only adds context", () => {
    expect(standing(link({}), TIERS)).toBe(
      "Reported as credible by a UN Security Council Panel or Group of Experts · since 2023");
    expect(standing(link({ status: "confirmed", until: "2022", since: "2020" }), TIERS))
      .toBe("Confirmed by a UN Security Council Panel or Group of Experts · 2020–2022, ended");
    expect(standing(link({ sources: [link({}).sources[0]] }), TIERS)).toBe("Reported as credible · since 2023");
  });

  it("labels the far end with the armed actor's short name, or nothing for a government", () => {
    expect(actorLabel(link({ actor: "Rapid Support Forces (RSF)" }))).toBe("RSF");
    expect(actorLabel(link({ actor: "Group Y" }))).toBe("Group Y");
    expect(actorLabel(link({}))).toBeNull();  // negative control: the state's own government
  });

  it("says how much of the record is read, and frames both ends of a state's links", () => {
    const d = doc([link({ id: "a" }), link({ id: "b", from: "BBB", to: "CCC" })],
      [[[10, 50], [20, 5]], [[-5, 0], [0, -10]]]);
    expect(coverageNote(d)).toBe("2 links recorded. Not a complete record: 1 of 2 UN panels' latest reports read in full so far.");
    expect(linksOf(d, "AAA").map((l) => l.id)).toEqual(["a"]);
    expect(linksBounds(d, ["a"])).toEqual([10, 5, 20, 50]);
    expect(linksBounds(d, [])).toBeNull();  // negative control: no links, no box
  });
});
