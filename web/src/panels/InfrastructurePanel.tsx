// Infrastructure: the cities that are on the map today, and the layers still to come with their sources.

import { useEffect, useState } from "react";
import { asset, people } from "../data";

interface Place { name: string; iso3: string; capital: boolean; population: number }

const COMING = [
  ["Roads", "Microsoft Road Detections (AI-detected from imagery), ODbL"],
  ["Rail and ports", "OpenStreetMap (ODbL) and the World Port Index"],
  ["Megaprojects and dams", "Global Energy Monitor, GRanD and Wikidata"],
];

export default function InfrastructurePanel({ iso3 }: { iso3: string }) {
  const [places, setPlaces] = useState<Place[]>([]);
  useEffect(() => {
    fetch(asset("geo/places.json")).then((r) => r.json()).then((g) =>
      setPlaces(g.features.map((f: { properties: Place }) => f.properties)));
  }, []);
  const here = places.filter((p) => p.iso3 === iso3);
  return (
    <div className="panel-body">
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
      <h3>Layers in preparation</h3>
      <ul className="coming">
        {COMING.map(([name, source]) => <li key={name}><b>{name}</b><span className="muted small">{source}</span></li>)}
      </ul>
    </div>
  );
}
