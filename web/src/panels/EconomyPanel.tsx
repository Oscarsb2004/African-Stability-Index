// The economy (P56): analyses before history. The IMF's outlook, the headline figures, the record, then the
// economy dimension's other sections; money, banks, markets and debt are under Finance. Every figure shows its period.

import LineChart from "../LineChart";
import { fmt, type Figure, type SectionsDoc } from "../data";
import { Rows, Tile, trend } from "./parts";

interface Props {
  iso3: string;
  doc: SectionsDoc;
  onCompare?: (measure: string) => void;
}

function spec(doc: SectionsDoc, section: string, id: string) {
  return doc.sections.find((s) => s.id === section)?.figures.find((f) => f.id === id);
}

export default function EconomyPanel({ iso3, doc, onCompare }: Props) {
  const a = doc.areas[iso3];
  const out = a.output, prices = a.prices;
  const peaks = (prices.inflation_peaks?.values ?? []) as { value: number; period: string }[];
  const infl = trend(prices.inflation_trend), growth = trend(out.growth_trend);
  const o = a.outlook ?? {}, path = trend(o.growth_path);
  const weo = doc.datasets.find((d) => d.name.startsWith("weo-"));
  const later = (f?: Figure) => f?.value == null ? "" : ` · ${f.period}: ${fmt(f.value, "%")}`;
  return (
    <div className="panel-body">
      <h3>Outlook</h3>
      {o.growth_first?.value == null && o.inflation_first?.value == null && o.debt_first?.value == null
        ? <p className="muted small">The IMF publishes no projections for this state in this edition.</p>
        : <>
          <div className="tiles">
            <Tile label="Real growth" figure={o.growth_first} unit="%"
              sub={`${o.growth_first?.period ?? "not projected"}${later(o.growth_last)}`} />
            <Tile label="Inflation" figure={o.inflation_first} unit="%"
              sub={`${o.inflation_first?.period ?? "not projected"}${later(o.inflation_last)}`} />
            <Tile label="Government debt, % of GDP" figure={o.debt_first} unit="%"
              sub={`${o.debt_first?.period ?? "not projected"}${later(o.debt_last)}`} />
          </div>
          {path.periods.length > 1 && <>
            <div className="chart-title">Real GDP growth, projected, % a year</div>
            <LineChart periods={path.periods} values={path.values} unit="%" height={80} />
          </>}
        </>}
      <p className="muted small">
        The IMF's projections as published, from the first year after its last actual data to the last year it
        projects. {weo?.attribution}.{" "}
        {onCompare && <button className="linkish" onClick={() => onCompare("weo/NGDP_RPCH")}>Compare outlooks in Data →</button>}
      </p>

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

      {doc.sections.filter((s) => s.dimension === "economy" && !["outlook", "output", "prices"].includes(s.id)).map((s) => (
        <Rows key={s.id} section={s} figures={a[s.id]} open={s.id === "public_finances"} onCompare={onCompare} />
      ))}
    </div>
  );
}
