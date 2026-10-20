// The languages of a state, under Wonders: its official languages (Wikidata), and the languages Glottolog places
// there, still spoken, with their families, endangerment and how well each is described. Glottolog counts languages,
// not speakers, so nothing here says how many people speak one. With no state chosen: the continent's.

import { useEffect, useMemo, useState } from "react";
import { load } from "../data";

interface StateLanguages {
  official: string[]; n: number; families: Record<string, number>; endangered: number;
  languages: [string, string, string, string, string][];  // name, family, endangerment, description, glottocode
}
interface LanguagesDoc { rule: string; states: Record<string, StateLanguages> }

let cached: Promise<LanguagesDoc> | null = null;

export default function Languages({ iso3, names }: { iso3: string | null; names: Record<string, string> }) {
  const [doc, setDoc] = useState<LanguagesDoc>();
  const [q, setQ] = useState("");
  useEffect(() => {
    cached ??= load<LanguagesDoc>("data/explore/languages.json");
    cached.then(setDoc).catch(() => undefined);
  }, []);
  const continent = useMemo(() => {
    if (!doc) return null;
    const seen = new Map<string, string>();
    for (const s of Object.values(doc.states)) for (const l of s.languages) seen.set(l[4], l[1]);
    const families = new Map<string, number>();
    for (const f of seen.values()) families.set(f, (families.get(f) ?? 0) + 1);
    const top = Object.entries(doc.states).sort((a, b) => b[1].n - a[1].n).slice(0, 8);
    return { n: seen.size, families: [...families.entries()].sort((a, b) => b[1] - a[1]), top };
  }, [doc]);
  if (!doc || !continent) return null;
  const s = iso3 ? doc.states[iso3] : null;
  const families = s ? Object.entries(s.families) : continent.families;
  const total = s ? s.n : continent.n;
  const shown = s ? s.languages.filter((l) => !q || l[0].toLowerCase().includes(q.toLowerCase())) : [];
  return (
    <section className="languages">
      <h3>Languages</h3>
      {s ? (
        <>
          <p className="small">{s.official.length ? <>Official: <b>{s.official.join(", ")}</b> (Wikidata). </> : null}
            Glottolog places <b>{s.n}</b> languages still spoken in {names[iso3 as string]}; {s.endangered} of them are
            endangered (threatened to nearly extinct).</p>
        </>
      ) : (
        <p className="small">Glottolog places <b>{continent.n.toLocaleString("en")}</b> languages still spoken across the 54
          member states. Most languages: {continent.top.map(([k, v]) => `${names[k]} ${v.n}`).join(", ")}.</p>
      )}
      <div className="family-bars">
        {families.slice(0, 8).map(([f, n]) => (
          <div key={f} className="family-bar">
            <span className="family-name">{f}</span>
            <span className="family-track"><span style={{ width: `${(100 * n) / total}%` }} /></span>
            <span className="num small">{n}</span>
          </div>
        ))}
        {families.length > 8 && <p className="muted small">and {families.length - 8} more families or isolates.</p>}
      </div>
      {s && s.n > 0 && (
        <details>
          <summary className="small">Every language ({s.n})</summary>
          {s.n > 20 && <input className="pick" placeholder="Find a language" value={q} onChange={(e) => setQ(e.target.value)}
            aria-label="Find a language" />}
          <table className="rows small">
            <thead><tr><th>Language</th><th>Family</th><th>Endangerment</th><th>Best description</th></tr></thead>
            <tbody>
              {shown.map((l) => (
                <tr key={l[4]}><td><a href={`https://glottolog.org/resource/languoid/id/${l[4]}`} target="_blank"
                  rel="noreferrer">{l[0]}</a></td><td>{l[1]}</td><td>{l[2] || "—"}</td><td>{l[3] || "—"}</td></tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
      <p className="muted small">Languages: Hammarström, Forkel, Haspelmath &amp; Bank (2026), Glottolog 5.3 (CC BY 4.0),
        counting languages, not speakers; a language spoken in several states is listed in each. Official languages:
        Wikidata (CC0).</p>
    </section>
  );
}
