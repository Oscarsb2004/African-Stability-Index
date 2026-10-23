import { describe, expect, it } from "vitest";
import { activityRows, cardRows, COLOURS, km, parsed, RING, SHAPES, SHOWN_FIRST, totalKm } from "./infra";

describe("the infrastructure layers", () => {
  it("shows a card's fields in the catalogue's order, under the publisher's labels, leaving out empty ones", () => {
    const fields = [{ name: "FeatureNam", label: "Name" }, { name: "DsgAttr01", label: "Commodity" },
      { name: "OwnerName", label: "Owner" }];
    expect(cardRows({ DsgAttr01: "Copper", FeatureNam: "Kansanshi", OwnerName: "", extra: 1 }, fields))
      .toEqual([["Name", "Kansanshi"], ["Commodity", "Copper"]]);
    expect(cardRows({}, fields)).toEqual([]);  // nothing invented for a feature without fields
  });

  it("formats kilometres and adds a state's classes without rounding them first", () => {
    expect(km(1234.56)).toBe("1,235 km");
    expect(totalKm({ railway: 0.4, "narrow-gauge railway": 0.4 })).toBeCloseTo(0.8);
    expect(km(totalKm({}))).toBe("0 km");
  });

  it("reads back the nested values MapLibre returns as text, and leaves plain text alone", () => {
    expect(parsed({ rows: '[{"DsgAttr03":"Iron ore"}]', name: "[Not a list", n: 3 }))
      .toEqual({ rows: [{ DsgAttr03: "Iron ore" }], name: "[Not a list", n: 3 });
  });

  it("gives every layer shown first a colour of its own, or a shape in a validated colour", () => {
    for (const id of SHOWN_FIRST) expect(COLOURS[id] ?? SHAPES[id]?.colour).toMatch(/^#[0-9a-f]{6}$/);
    const values = Object.values(COLOURS);
    expect(new Set(values).size).toBe(values.length);
    // a shape adds no hue: it reuses a validated one, or the neutral ring
    for (const s of Object.values(SHAPES)) expect([...values, RING]).toContain(s.colour);
    expect(Object.keys(SHAPES).filter((id) => id in COLOURS)).toEqual([]);
  });

  it("lists a point's complete years newest first, as whole numbers, leaving a missing value empty", () => {
    const columns = [{ name: "portcalls", label: "Port calls" }, { name: "import", label: "Imports, t" }];
    expect(activityRows({ years: [2019, 2020], portcalls: [1200, 1310], import: [2500000.4, 2612345] }, columns))
      .toEqual([["2020", "1,310", "2,612,345"], ["2019", "1,200", "2,500,000"]]);
    expect(activityRows({ years: [2021], portcalls: [5] }, columns)).toEqual([["2021", "5", ""]]);
  });
});
