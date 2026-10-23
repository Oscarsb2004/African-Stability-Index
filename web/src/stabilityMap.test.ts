// stabilityMap.ts on an invented document of six states. Each rule has a negative control.

import { describe, expect, it } from "vitest";
import { RAMP, type StabilityDoc } from "./data";
import { measureValues, memberNames, menu, shown } from "./stabilityMap";

const state = (score: number, gov: number | null, ind: number | null, raw: number | null) => ({
  composite: { score, reliability: "reliable", ci_low: null, ci_high: null, tier: null, band_best: null, band_worst: null },
  narrative: [], history: { years: [], scores: [] },
  pillars: { GOV: { score: gov, reliability: "reliable", observed: 1, indicators: 1 } },
  indicators: { ge: { raw: 1, score: ind, provenance: "observed", source_year: 2024 },
                gdp_total: { raw, score: null, provenance: "observed", source_year: 2024 } },
});
const doc: StabilityDoc = {
  reference_year: 2024, inputs: "", n_ranked: 6, n_tiers: 2, method: "",
  classes: { rule: "fifths of the member states", breaks: [20, 40, 60, 80] },
  pillars: { GOV: { name: "Governance", indicators: ["ge", "gdp_total", "absent"] } },
  indicators: { ge: { display_name: "Government effectiveness", series_code: "GE", polarity: "positive" },
                gdp_total: { display_name: "GDP", series_code: "NY", polarity: "neutral" } },
  countries: { AAA: state(10, 5, 50, 100), BBB: state(30, 15, 40, 200), CCC: state(50, 25, 30, 300),
               DDD: state(70, 35, 20, 400), EEE: state(90, 45, 10, 500), FFF: state(95, null, null, null) },
};

describe("what the stability map shows", () => {
  it("keeps the published classes for the composite, and fifths for a pillar", () => {
    expect(shown(doc, "composite").breaks).toEqual([20, 40, 60, 80]);
    expect(shown(doc, "composite").colours.EEE).toBe(RAMP[4]);
    const gov = shown(doc, "pillar:GOV");
    expect(gov.breaks).toEqual([13, 21, 29, 37]);  // the fifths of 5, 15, 25, 35, 45
    expect(gov.colours.AAA).toBe(RAMP[0]);
    expect("FFF" in gov.colours).toBe(false);  // negative control: no value, no colour
  });

  it("maps an indicator by its score, and a descriptive one by its raw value, saying so", () => {
    expect(measureValues(doc, "indicator:ge")).toEqual({ raw: false,
      values: { AAA: 50, BBB: 40, CCC: 30, DDD: 20, EEE: 10, FFF: null } });
    const gdp = measureValues(doc, "indicator:gdp_total");
    expect(gdp.raw).toBe(true);
    expect(gdp.values.EEE).toBe(500);
    expect(shown(doc, "indicator:gdp_total").scale).toContain("not scored");
    expect(shown(doc, "indicator:ge").scale).not.toContain("not scored");
  });

  it("orders the menu as the indicator files, leaving out an indicator the site does not show", () => {
    const m = menu(doc);
    expect(m.map((s) => s.title)).toEqual(["General stability", "The eight pillars", "GOV · Governance"]);
    expect(m[2]).toEqual({ title: "GOV · Governance", path: "indicators_list/pillar_gov.yaml",
      items: ["indicator:ge", "indicator:gdp_total"] });  // "absent" is not in the document
  });

  it("lists a grouping's members by name, and by code where a name is missing", () => {
    const g = { id: "G", name: "Group", kind: "rec" as const, members: ["BBB", "AAA", "ZZZ"] };
    expect(memberNames(g, { AAA: "Aland", BBB: "Bland" })).toBe("Aland, Bland, ZZZ");
  });
});
