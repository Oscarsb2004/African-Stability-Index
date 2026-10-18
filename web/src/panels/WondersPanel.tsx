// Wonders (P61): the continent's absolute highlights, chosen by a stated rule, each with a few photographs.
// The list shows the chosen country's wonders, or all of them; a click opens the full-screen viewer.

import type { Wonder, WondersDoc } from "../data";

interface Props {
  doc: WondersDoc | null;
  iso3: string | null;
  names: Record<string, string>;
  onOpen: (w: Wonder) => void;
}

export default function WondersPanel({ doc, iso3, names, onOpen }: Props) {
  if (!doc) {
    return (
      <div className="panel-body">
        <h3>Wonders of Africa</h3>
        <p className="muted">The list is being prepared.</p>
      </div>
    );
  }
  const list = iso3 ? doc.wonders.filter((w) => w.countries.includes(iso3)) : doc.wonders;
  return (
    <div className="panel-body">
      <p className="muted small">
        The continent's highlights, natural and human-made: World Heritage Sites and the most notable mountains,
        volcanoes, falls, lakes, rivers, deserts, rainforests, canyons, parks and ancient sites, ranked by how many
        Wikipedia languages describe them. Click one to see its photographs.
      </p>
      {list.length === 0 && <p className="muted">None of the {doc.wonders.length} wonders is in this country.</p>}
      <ul className="wonders">
        {list.map((w) => (
          <li key={w.id}>
            <button className="wonder" onClick={() => onOpen(w)} disabled={!w.photos.length}>
              {w.photos[0] ? <img src={w.photos[0].thumb} alt="" loading="lazy" /> : <span className="no-photo" />}
              <span className="wonder-text">
                <b>{w.name}</b>
                <span className="muted small">{w.kinds.join(" · ")}</span>
                <span className="muted small">{w.countries.map((c) => names[c] ?? c).join(", ")}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
      <p className="muted small">
        Places: Wikidata (CC0). Photographs: Wikimedia Commons, each under its own licence, credited in the viewer.
        Edition {doc.edition}.
      </p>
    </div>
  );
}
