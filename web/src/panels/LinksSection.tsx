// "Links to other states" in the country panel: a state's links (registry/links.yaml, R5), each one line that opens to
// its conflict, summary and sources; hovering one picks out its line on the map. A state with none says so, and says
// that the record is not complete; "How links are chosen" gives the rule (R7) and how much of each UN panel's latest
// report has been read. Nothing here makes a fact: every card is the registry's.

import { coverageNote, heading, KIND_COLOURS, type LinksDoc, linksOf, standing } from "../links";

interface Props {
  doc: LinksDoc | null;
  iso3: string;
  name: string;
  linksOn: boolean;              // the map's "Links between states" switch
  onShow: () => void;            // switch it on
  onFocus: (id: string | null) => void;  // the link a reader points at, picked out on the map
}

export default function LinksSection({ doc, iso3, name, linksOn, onShow, onFocus }: Props) {
  if (!doc) return null;
  const ls = linksOf(doc, iso3);
  return (
    <section className="links-section">
      <h3>Links to other states <span className="tag">the owner's compilation</span></h3>
      {ls.length ? ls.map((l) => (
        <details key={l.id} className="link-card" onMouseEnter={() => onFocus(l.id)} onMouseLeave={() => onFocus(null)}>
          <summary>
            <span className={l.status === "confirmed" ? "swatch line" : "swatch line dashed"}
              style={{ background: KIND_COLOURS[l.kind], opacity: l.historical ? 0.5 : 1 }} />
            <span className="link-card-title">{heading(l)}</span>
            <span className="muted small">{doc.kinds[l.kind] ?? l.kind} · {standing(l, doc.tiers)}</span>
          </summary>
          <div className="muted small">{l.conflict}</div>
          <p className="small">{l.summary}</p>
          {l.sources.map((s) => (
            <div key={s.url} className="muted small">
              <a href={s.url} target="_blank" rel="noreferrer">{s.publisher}, {s.title}</a> ({s.date}) ·{" "}
              {doc.tiers[s.tier] ?? s.tier}
            </div>
          ))}
        </details>
      )) : (
        <p className="small">No link recorded for {name}. That is not evidence of none: the record is not complete.</p>
      )}
      {ls.length > 0 && !linksOn && <button className="linkish small" onClick={onShow}>Show on the map</button>}
      <p className="muted small">{coverageNote(doc)}</p>
      <details className="sources">
        <summary className="muted small">How links are chosen</summary>
        <p className="small">A link is listed only when a UN Security Council panel of experts, the government
          concerned, or a UN human-rights investigation names it; news only adds context. It is drawn solid where that
          source finds it, dashed where it judges it credible, and faded once it has ended. The UN panels' latest
          reports, and how much of each has been read:</p>
        {doc.coverage.map((c) => (
          <div key={c.report} className="small">
            {c.regime}: <a href={`https://docs.un.org/en/${c.report}`} target="_blank" rel="noreferrer">{c.report}</a>
            <span className="muted"> ({c.date}) · {c.read}</span>
          </div>
        ))}
      </details>
    </section>
  );
}
