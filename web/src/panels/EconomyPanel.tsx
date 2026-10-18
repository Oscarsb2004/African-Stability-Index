// The economic outlook (P56): analyses before history. Stressors first, then the headline figures, then the
// record, then the detail sections. Every figure shows its period; a derived one says so.

import LineChart from "../LineChart";
import { fmt, type Figure, type SectionSpec, type SectionsDoc } from "../data";

interface Props {
  iso3: string;
  doc: SectionsDoc;
}

function spec(doc: SectionsDoc, section: string, id: string) {
  return doc.sections.find((s) => s.id === section)?.figures.find((f) => f.id === id);
}

function Tile({ label, figure, unit, sub }: { label: string; figure?: Figure; unit: string; sub?: string }) {
  return (
    <div className="tile">
      <div className="tile-label">{label}</div>
      <div className="tile-value">{fmt(figure?.value ?? null, unit)}</div>
      <div className="tile-sub">{sub ?? (figure?.period ? figure.period : "not published")}</div>
    </div>
  );
}

function Rows({ section, figures }: { section: SectionSpec; figures: Record<string, Figure> }) {
  return (
    <details className="block" open={section.id === "public_finances"}>
      <summary><span>{section.title}</span><span className="muted small">{section.about}</span></summary>
      <table className="rows">
        <tbody>
          {section.figures.filter((f) => f.shell !== "trend").map((f) => {
            const r = figures[f.id];
            return (
              <tr key={f.id}>
                <td>{f.label}{f.derived && <span className="tag" title={`Computed by the ${f.shell} shell`}>derived</span>}</td>
                <td className="num">{f.unbound ? <span className="muted" title={f.unbound}>not yet</span>
                  : r?.value == null ? <span className="muted">—</span>
                  : <>{fmt(r.value, f.unit)} <span className="unit">{f.unit.startsWith("%") ? f.unit.slice(1) : f.unit}</span></>}</td>
                <td className="period">{r?.period ?? ""}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </details>
  );
}

export default function EconomyPanel({ iso3, doc }: Props) {
  const a = doc.areas[iso3];
  const out = a.output, prices = a.prices;
  const peaks = (prices.inflation_peaks?.values ?? []) as { value: number; period: string }[];
  const trend = (f?: Figure) => ({ periods: f?.periods ?? [], values: (f?.values ?? []) as number[] });
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

      {doc.sections.filter((s) => !["appraisals", "output", "prices"].includes(s.id)).map((s) => (
        <Rows key={s.id} section={s} figures={a[s.id]} />
      ))}
    </div>
  );
}
