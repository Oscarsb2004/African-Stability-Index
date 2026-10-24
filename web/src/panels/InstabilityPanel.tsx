// "Spreading instability" (the owner's rulings of 2026-10-23): the owner's conflict theatres. Choosing one fits the
// map to its states and draws its events and links; the panel gives its deaths by month since 2018, its states' last
// twelve months, its spread by two stated rules, the armed groups on new ground, its links with their cards, and the
// prediction markets that belong to it. Every figure is UCDP's or a sum of UCDP's, said so.

import { useEffect, useState } from "react";
import LineChart from "../LineChart";
import { loadOnce } from "../data";
import { type InstabilityDoc, theatreMonthly, twelveMonths, TYPE_COLOURS } from "../instability";
import { heading, KIND_COLOURS, type LinksDoc, standing } from "../links";

interface Props {
  doc: InstabilityDoc | null;
  theatre: string | null;
  onTheatre: (id: string) => void;
  names: Record<string, string>;
}

const N = new Intl.NumberFormat("en");

export default function InstabilityPanel({ doc, theatre, onTheatre, names }: Props) {
  const [links, setLinks] = useState<LinksDoc | null>(null);
  useEffect(() => {
    loadOnce<LinksDoc>("geo/links.json").then(setLinks).catch(() => setLinks(null));
  }, []);
  if (!doc) return <div className="panel-body"><p className="muted">Loading the conflicts…</p></div>;
  const t = doc.theatres.find((x) => x.id === theatre) ?? doc.theatres[0];
  const monthly = theatreMonthly(t), twelve = twelveMonths(t);
  const cards = (links?.features ?? []).map((f) => f.properties).filter((l) => t.links.includes(l.id));

  return (
    <div className="panel-body">
      <div className="theatre-list" role="tablist" aria-label="Theatres">
        {doc.theatres.map((x) => (
          <button key={x.id} role="tab" aria-selected={x.id === t.id} className={x.id === t.id ? "measure-option on" : "measure-option"}
            onClick={() => onTheatre(x.id)}>{x.name}</button>
        ))}
      </div>

      <h3>{t.name}</h3>
      <p className="muted small">{t.summary}</p>

      <div className="chart-title">Deaths in organised violence by month, {doc.months[0]} to {doc.last_month}</div>
      <LineChart periods={doc.months} values={monthly} unit="deaths" height={110} />
      <p className="muted small">
        {N.format(twelve.now)} deaths in the last twelve months ({doc.window[0]} to {doc.window[1]}), against{" "}
        {N.format(twelve.before)} in the twelve before: the sum of UCDP's best estimates in the theatre's states
        (derived). UCDP's own range for the last twelve months: {N.format(t.range.low)} to {N.format(t.range.high)}. The
        months since UCDP's last annual release are provisional.
      </p>

      <table className="rows">
        <thead><tr><th>State</th><th className="num">Deaths, last 12 months</th><th className="num">UCDP's range</th>
          <th className="num">Events</th></tr></thead>
        <tbody>
          {[...t.states].sort((a, b) => (doc.states[b]?.deaths ?? 0) - (doc.states[a]?.deaths ?? 0)).map((s) => (
            <tr key={s}><td>{names[s] ?? s}</td><td className="num">{N.format(doc.states[s]?.deaths ?? 0)}</td>
              <td className="num muted">{N.format(doc.states[s]?.low ?? 0)}–{N.format(doc.states[s]?.high ?? 0)}</td>
              <td className="num">{N.format(doc.states[s]?.events ?? 0)}</td></tr>
          ))}
        </tbody>
      </table>

      {t.maps.length > 0 && (
        <p className="muted small">
          Who holds what, as others map it (not reproduced here):{" "}
          {t.maps.map((mp, i) => (
            <span key={mp.url}>{i > 0 && "; "}<a href={mp.url} target="_blank" rel="noreferrer">{mp.title}</a>{" "}
              ({mp.publisher}, revised {mp.revised})</span>
          ))}. No open source publishes the frontlines as data; the map shows UCDP's events instead.
        </p>
      )}

      <h3>Spread</h3>
      <p className="small">
        <b>{t.areas_now}</b> first-level areas with a deadly event in the last twelve months, against{" "}
        <b>{t.areas_before}</b> in the twelve before.
      </p>
      <p className="muted small">{doc.rules.areas}.</p>
      {t.new_ground.length > 0 ? (
        <>
          <div className="chart-title">Armed groups on new ground</div>
          <table className="rows">
            <tbody>
              {t.new_ground.slice(0, 12).map((g) => (
                <tr key={`${g.actor}-${g.iso3}`}>
                  <td>{g.actor}<div className="muted small">{names[g.iso3] ?? g.iso3}, first on {g.first}</div></td>
                  <td className="num">{g.events} events · {N.format(g.deaths)} deaths</td>
                </tr>
              ))}
            </tbody>
          </table>
          {t.new_ground.length > 12 && <p className="muted small">The twelve with the most deaths of {t.new_ground.length}.</p>}
        </>
      ) : <p className="muted small">No identified armed group on new ground in the last twelve months.</p>}
      <p className="muted small">New ground: {doc.rules.new_ground}.</p>

      <h3>Who backs whom</h3>
      {cards.length ? cards.map((l) => (
        <div key={l.id} className="link-card">
          <div className="infra-card-title">{heading(l)}</div>
          <div className="small"><span className={l.status === "confirmed" ? "swatch line" : "swatch line dashed"}
            style={{ background: KIND_COLOURS[l.kind] }} /> {links?.kinds[l.kind] ?? l.kind} · {standing(l)}</div>
          <p className="small">{l.summary}</p>
          {l.sources.map((s) => (
            <div key={s.url} className="muted small"><a href={s.url} target="_blank" rel="noreferrer">{s.publisher}, {s.title}</a> ({s.date})</div>
          ))}
        </div>
      )) : <p className="muted small">No link is recorded for this theatre yet. Click any state for its own.</p>}

      <h3>Who may be drawn in</h3>
      {t.markets.length ? null : (
        <p className="muted small">No prediction market is listed for this theatre yet. Markets are added only by their
          platform's own id, with their terms read first; a state with no market shows no likelihood.</p>
      )}

      <div className="chart-title">On the map</div>
      <div className="legend-types">
        {Object.entries(TYPE_COLOURS).map(([k, c]) => (
          <span key={k} className="small"><span className="swatch dot" style={{ background: c }} /> {k} violence</span>
        ))}
      </div>
      <p className="muted small">Each event of the last twelve months, sized by its deaths.</p>
      <details className="sources">
        <summary className="muted small">Sources</summary>
        {doc.sources.map((s) => <div key={s} className="small">{s}</div>)}
      </details>
    </div>
  );
}
