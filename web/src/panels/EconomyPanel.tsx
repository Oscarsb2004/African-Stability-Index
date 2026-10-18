// The economy (P56): analyses before history. The headline figures, then the record, then the economy dimension's
// other sections; money, banks, markets and debt are under Finance. Every figure shows its period.

import LineChart from "../LineChart";
import { fmt, type Figure, type SectionsDoc } from "../data";
import { Rows, Tile, trend } from "./parts";

interface Props {
  iso3: string;
  doc: SectionsDoc;
}

function spec(doc: SectionsDoc, section: string, id: string) {
  return doc.sections.find((s) => s.id === section)?.figures.find((f) => f.id === id);
}

export default function EconomyPanel({ iso3, doc }: Props) {
  const a = doc.areas[iso3];
  const out = a.output, prices = a.prices;
  const peaks = (prices.inflation_peaks?.values ?? []) as { value: number; period: string }[];
  const infl = trend(prices.inflation_trend), growth = trend(out.growth_trend);
  return (
    <div className="panel-body">
      <div className="note">
        Forecasts (IMF World Economic Outlook) will lead this panel once that database is in Athena. Until then
        it starts with the latest published figures.
      </div>

      <h3>Headline</h3>
      <div className="tiles">
        <Tile label="GDP" figure={out.gdp} unit="current US$" />
        <Tile label="GDP per person (PPP)" figure={out.gdp_per_person} unit="current international $" />
        <Tile label="Real growth" figure={out.growth} unit="%"
          sub={`${out.growth?.period ?? ""} · 3-yr avg ${fmt(out.growth_mean_3?.value ?? null, "%")}`} />
        <Tile label="Inflation" figure={prices.inflation} unit="%"
          sub={`${prices.inflation?.period ?? ""} · 3-yr avg ${fmt(prices.inflation_mean_3?.value ?? null, "%")}`} />
      </div>

      <h3>Inflation: the record</h3>
      <div className="peaks">
        {peaks.length === 0 && <span className="muted">No inflation series published.</span>}
        {peaks.map((p) => (
          <div key={p.period} className="peak"><b>{fmt(p.value, "%")}</b><span>{p.period}</span></div>
        ))}
      </div>
      <p className="muted small">
        {spec(doc, "prices", "inflation_peaks")?.label}, searched over {String((prices.inflation_peaks as Figure & { searched?: string })?.searched ?? "")}.
      </p>
      {infl.periods.length > 1 && <>
        <div className="chart-title">Inflation since 2000, % a year</div>
        <LineChart periods={infl.periods} values={infl.values} unit="%" />
      </>}
      {growth.periods.length > 1 && <>
        <div className="chart-title">Real GDP growth since 2000, % a year</div>
        <LineChart periods={growth.periods} values={growth.values} unit="%" />
      </>}
      <p className="muted small">
        Growth volatility over 10 years: {fmt(out.growth_spread_10?.value ?? null)} percentage points
        ({out.growth_spread_10?.period ?? "—"}).
      </p>

      {doc.sections.filter((s) => s.dimension === "economy" && !["output", "prices"].includes(s.id)).map((s) => (
        <Rows key={s.id} section={s} figures={a[s.id]} open={s.id === "public_finances"} />
      ))}
    </div>
  );
}
