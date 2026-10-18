// Finance (P64's example): a macro-financial picture on yearly horizons, never trading ones. Headline tiles, three
// histories, then every finance section: money, the currency and reserves, banks, capital markets, debt, flows.

import LineChart from "../LineChart";
import { fmt, type SectionsDoc } from "../data";
import { Rows, Tile, trend } from "./parts";

export default function FinancePanel({ iso3, doc }: { iso3: string; doc: SectionsDoc }) {
  const a = doc.areas[iso3];
  const { monetary, currency, banks, sovereign } = a;
  const charts = [
    { title: "Real interest rate since 2000, %", t: trend(monetary.real_interest_rate_trend), unit: "%" },
    { title: "Reserves since 2000, months of imports", t: trend(currency.reserves_trend), unit: "months",
      zero: true },
    { title: "External debt since 2000, % of GNI", t: trend(sovereign.external_debt_trend), unit: "% of GNI" },
  ];
  return (
    <div className="panel-body">
      <div className="note">
        Macro-financial conditions on yearly horizons. A charter for this dimension lists what a professional review
        should add next: policy rates, bank soundness and yields from the IMF and BIS, once their terms allow.
      </div>

      <h3>Headline</h3>
      <div className="tiles">
        <Tile label="Real interest rate" figure={monetary.real_interest_rate} unit="%" />
        <Tile label="Reserves" figure={currency.reserves_months} unit="months"
          sub={`${currency.reserves_months?.period ?? "not published"} · months of imports`} />
        <Tile label="Bad loans" figure={banks.bad_loans} unit="%"
          sub={`${banks.bad_loans?.period ?? "not published"} · % of bank loans`} />
        <Tile label="Local currency per US$" figure={currency.currency_5} unit="%"
          sub={`${currency.currency_5?.period ?? "not published"} · change a year`} />
      </div>
      <p className="muted small">
        Interest on public debt: {fmt(sovereign.interest_revenue?.value ?? null, "%")} of revenue
        ({sovereign.interest_revenue?.period ?? "—"}).
      </p>

      {charts.filter((c) => c.t.periods.length > 1).map((c) => (
        <div key={c.title}>
          <div className="chart-title">{c.title}</div>
          <LineChart periods={c.t.periods} values={c.t.values} unit={c.unit} zero={c.zero ?? true} />
        </div>
      ))}

      {doc.sections.filter((s) => s.dimension === "finance").map((s) => (
        <Rows key={s.id} section={s} figures={a[s.id]} open={s.id === "monetary"} />
      ))}
    </div>
  );
}
