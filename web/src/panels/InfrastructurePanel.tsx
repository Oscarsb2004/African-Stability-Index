// Infrastructure: the country's national figures first (the infrastructure dimension's sections, P66), then what
// the map shows of it: its ports' activity (PortWatch), its ports and what they export, its mines and mineral
// facilities, the railways, roads and power lines inside it, and its cities. The map figures are the stage's (10_infrastructure.py); which state a
// feature belongs to is derived by the stated rule, and each block names its source.

import { useEffect, useState } from "react";
import LineChart from "../LineChart";
import { asset, people, type SectionsDoc } from "../data";
import { km, totalKm, type CountriesDoc, type LayersDoc } from "../infra";
import { Rows, trend } from "./parts";

interface Place { name: string; iso3: string; capital: boolean; population: number }

const COMING = [
  ["Infrastructure projects (AID)", "waiting on AUDA-NEPAD's answer about republishing"],
  ["Pipelines and power stations", "waiting on the terms of their stated source; Global Energy Monitor next"],
  ["Wages", "ILOSTAT's minimum and median wages, once its terms are read"],
];

let countries: Promise<CountriesDoc> | null = null;  // loaded once, for every state

// a share as PortWatch publishes it, in percent to two decimals
const share = (v?: number) => v === undefined ? "" : `${v.toLocaleString("en", { maximumFractionDigits: 2 })}%`;

interface Props {
  iso3: string;
  infra: LayersDoc | null;
  doc: SectionsDoc;
  onCompare?: (measure: string) => void;
}

export default function InfrastructurePanel({ iso3, infra, doc: sections, onCompare }: Props) {
  const [places, setPlaces] = useState<Place[]>([]);
  const [doc, setDoc] = useState<CountriesDoc | null>(null);
  useEffect(() => {
    fetch(asset("geo/places.json")).then((r) => r.json()).then((g) =>
      setPlaces(g.features.map((f: { properties: Place }) => f.properties)));
    countries ??= fetch(asset("geo/infra/countries.json")).then((r) => r.json());
    countries.then(setDoc).catch(() => setDoc({}));
  }, []);
  const here = places.filter((p) => p.iso3 === iso3);
  const c = doc?.[iso3];
  const layer = (id: string) => [...(infra?.points ?? []), ...(infra?.lines ?? [])].find((l) => l.id === id);
  const source = (id: string) => {
    const l = layer(id);
    return l ? `${l.attribution} (${l.licence}).` : "";
  };
  const a = sections.areas[iso3] ?? {};
  const national = sections.sections.filter((s) => s.dimension === "infrastructure");
  const electricity = trend(a.services?.electricity_trend);
  const wdi = sections.datasets.find((d) => d.name.startsWith("wdi-"));
  return (
    <div className="panel-body">
      {national.map((s) => (
        <Rows key={s.id} section={s} figures={a[s.id] ?? {}} open={s.id === "services"} onCompare={onCompare} />
      ))}
      {electricity.periods.length > 1 && <>
        <div className="chart-title">Access to electricity since 2000, % of population</div>
        <LineChart periods={electricity.periods} values={electricity.values} unit="%" height={80} />
      </>}
      {national.length > 0 && <p className="muted small">
        Each figure as its publisher estimates it, with its year. {wdi?.attribution}, {wdi?.licence}.
      </p>}

      {c && (
        <>
          <h3>Port activity</h3>
          {c.portwatch?.length ? (
            <table className="rows">
              <thead><tr><th>Port</th><th className="num">Ships a year</th><th className="num">Imports</th>
                <th className="num">Exports</th></tr></thead>
              <tbody>
                {[...c.portwatch].sort((x, y) => (y.vessels ?? 0) - (x.vessels ?? 0)).map((p, i) => (
                  <tr key={`${p.name}-${i}`}>
                    <td>{p.name ?? "Unnamed"}</td>
                    <td className="num">{p.vessels === undefined ? "" : p.vessels.toLocaleString("en")}</td>
                    <td className="num">{share(p.imports)}</td>
                    <td className="num">{share(p.exports)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="muted small">PortWatch tracks no seaport here.</p>}
          <p className="muted small">
            Ships calling per year (average, 2019–2025) and each port's share of the country's maritime imports and
            exports, as PortWatch estimates them from ships' AIS signals; a port's card on the map gives each complete
            year. {source("portwatch")}
          </p>

          <h3>Ports and export hubs</h3>
          {c.ports?.length ? (
            <table className="rows">
              <tbody>
                {c.ports.map((p, i) => (
                  <tr key={`${p.name}-${i}`}>
                    <td>{p.name ?? "Unnamed"}{p.type && <span className="muted small"> · {p.type}</span>}</td>
                    <td className="small">{p.exports.join(", ") || <span className="muted">no commodity recorded</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="muted small">No mineral-exporting port recorded here.</p>}
          <p className="muted small">The commodities each port exports. {source("ports")}</p>

          <h3>Mines and mineral facilities</h3>
          {c.facilities ? (
            <table className="rows">
              <tbody>
                {Object.entries(c.facilities).map(([type, n]) => (
                  <tr key={type}><td>{type}</td><td className="num">{n.toLocaleString("en")}</td></tr>
                ))}
              </tbody>
            </table>
          ) : <p className="muted small">No mineral facility recorded here.</p>}
          <p className="muted small">
            Facilities by commodity type{c.deposits ? `; ${c.deposits.toLocaleString("en")} major deposits` : ""}
            {c.exploration ? `; ${c.exploration.toLocaleString("en")} exploration sites` : ""}. {source("facilities")}
          </p>

          <h3>Inside the country</h3>
          {c.km ? (
            <table className="rows">
              <tbody>
                {Object.entries(c.km).map(([id, byClass]) => (
                  <tr key={id}>
                    <td>{layer(id)?.title ?? id}
                      <div className="muted small">{Object.entries(byClass).map(([k, v]) => `${k} ${km(v)}`).join(" · ")}</div>
                    </td>
                    <td className="num">{km(totalKm(byClass))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="muted small">No line of these layers crosses the country.</p>}
          <p className="muted small">
            Length inside the country's borders, on the WGS84 ellipsoid (derived). {source("rail")} {source("grid")}
          </p>
        </>
      )}

      <h3>Cities</h3>
      <p className="muted small">The capital first, then the largest cities. On the map, more appear as you zoom.</p>
      <table className="rows">
        <tbody>
          {here.slice(0, 12).map((p) => (
            <tr key={p.name}>
              <td>{p.name}{p.capital && <span className="tag">capital</span>}</td>
              <td className="num">{people(p.population)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="muted small">Population of the urban area (Natural Earth, public domain).</p>

      {infra && <p className="muted small">Which country a feature belongs to: {infra.rules.place}.</p>}
      <h3>Still to come</h3>
      <ul className="coming">
        {COMING.map(([name, why]) => <li key={name}><b>{name}</b><span className="muted small">{why}</span></li>)}
      </ul>
    </div>
  );
}
