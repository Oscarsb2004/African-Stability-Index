// "Build your own index" (the owner's ruling of 2026-10-23), inside the Stability popup: a name; indicators from the
// Data tab's catalogue, found by category and search, several at once; each one's direction, stated by the reader
// (the ASI's own scores already say higher is more stable; nothing else is guessed); a scoring method and a way to
// combine, each with its formula, the recommended one marked; and the year.

import { useEffect, useMemo, useState } from "react";
import { AGGREGATES, type Aggregate, type CustomIndex, type IndexItem, METHODS, type Method } from "./customIndex";
import { type Catalogue, loadCatalogue, type Measure } from "./explore/model";

interface Props {
  year: number;                       // the ASI's reference year, the default
  onSave: (ix: CustomIndex) => void;
  onCancel: () => void;
}

const MAX_SHOWN = 120;

export default function IndexBuilder({ year: refYear, onSave, onCancel }: Props) {
  const [catalogue, setCatalogue] = useState<Catalogue | null>(null);
  const [name, setName] = useState("");
  const [topic, setTopic] = useState("African Stability Index: indicator scores");
  const [search, setSearch] = useState("");
  const [items, setItems] = useState<(Omit<IndexItem, "higherIsBetter"> & { higherIsBetter: boolean | null })[]>([]);
  const [method, setMethod] = useState<Method>("minmax");
  const [aggregate, setAggregate] = useState<Aggregate>("mean");
  const [year, setYear] = useState(refYear);
  useEffect(() => { loadCatalogue().then(setCatalogue).catch(() => setCatalogue(null)); }, []);

  const topics = useMemo(() => {
    const n = new Map<string, number>();
    for (const m of catalogue?.measures ?? []) n.set(m.topic, (n.get(m.topic) ?? 0) + 1);
    return [...n.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [catalogue]);
  const list = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (catalogue?.measures ?? []).filter((m) => (!q ? m.topic === topic
      : `${m.label} ${m.code} ${m.topic}`.toLowerCase().includes(q))).slice(0, MAX_SHOWN);
  }, [catalogue, topic, search]);

  const chosen = (m: Measure) => items.some((i) => i.measure === m.id);
  const toggle = (m: Measure) => setItems((xs) => chosen(m) ? xs.filter((i) => i.measure !== m.id)
    : [...xs, { measure: m.id, label: m.label, higherIsBetter: m.polarity === "higher is more stable" ? true : null }]);
  const direction = (id: string, v: boolean) => setItems((xs) => xs.map((i) => i.measure === id ? { ...i, higherIsBetter: v } : i));
  const undirected = items.filter((i) => i.higherIsBetter === null).length;
  const ready = name.trim() && items.length > 0 && undirected === 0;

  const save = () => {
    if (!ready) return;
    onSave({ id: `ix-${Date.now()}`, name: name.trim(), method, aggregate: method === "zscore" ? "mean" : aggregate,
      year, created: new Date().toISOString().slice(0, 10),
      items: items.map((i) => ({ measure: i.measure, label: i.label, higherIsBetter: i.higherIsBetter as boolean })) });
  };

  return (
    <div className="builder">
      <div className="panel-kicker">Build your own index</div>
      <p className="muted small">Your index is built in this browser from the indicators you choose. It is yours, not
        the ASI, and the project never publishes it. Every rule it uses is written below.</p>

      <label className="builder-field">Name
        <input className="pick" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Health and peace" />
      </label>

      <div className="builder-cols">
        <div>
          <div className="measure-section">1. Choose indicators</div>
          <div className="builder-row">
            <select className="pick" value={topic} onChange={(e) => { setTopic(e.target.value); setSearch(""); }}
              aria-label="Category">
              {topics.map(([t, n]) => <option key={t} value={t}>{t} ({n})</option>)}
            </select>
            <input className="pick" value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="or search every category" aria-label="Search indicators" />
          </div>
          <div className="builder-list" role="group" aria-label="Indicators">
            {!catalogue && <div className="muted small">Loading the catalogue…</div>}
            {list.map((m) => (
              <label key={m.id} className="builder-option">
                <input type="checkbox" checked={chosen(m)} onChange={() => toggle(m)} />
                <span>{m.label}<span className="muted small"> · {m.n} states{m.unit ? ` · ${m.unit}` : ""}</span></span>
              </label>
            ))}
            {list.length === MAX_SHOWN && <div className="muted small">The first {MAX_SHOWN}; search to narrow.</div>}
          </div>
        </div>

        <div>
          <div className="measure-section">2. Which way is better? ({items.length} chosen)</div>
          {!items.length && <div className="muted small">Tick indicators on the left.</div>}
          {items.map((i) => (
            <div key={i.measure} className="builder-chosen">
              <span className="small">{i.label}</span>
              <span className="builder-dir">
                <button className={i.higherIsBetter === true ? "measure-option on" : "measure-option"}
                  onClick={() => direction(i.measure, true)}>Higher is better</button>
                <button className={i.higherIsBetter === false ? "measure-option on" : "measure-option"}
                  onClick={() => direction(i.measure, false)}>Lower is better</button>
                <button className="close" aria-label={`Remove ${i.label}`}
                  onClick={() => setItems((xs) => xs.filter((x) => x.measure !== i.measure))}>×</button>
              </span>
            </div>
          ))}

          <div className="measure-section">3. Scoring</div>
          {METHODS.map((m) => (
            <label key={m.id} className="builder-option">
              <input type="radio" name="method" checked={method === m.id} onChange={() => setMethod(m.id)} />
              <span>{m.label}{m.recommended && <span className="tag">recommended</span>}
                <span className="muted small"> {m.formula}</span></span>
            </label>
          ))}
          <div className="measure-section">4. Combining</div>
          {AGGREGATES.map((a) => (
            <label key={a.id} className="builder-option">
              <input type="radio" name="aggregate" checked={aggregate === a.id} disabled={a.id === "geometric" && method === "zscore"}
                onChange={() => setAggregate(a.id)} />
              <span>{a.label}{a.recommended && <span className="tag">recommended</span>}
                <span className="muted small"> {a.formula}</span></span>
            </label>
          ))}
          <label className="builder-field">5. Year
            <input className="pick" type="number" min={2000} max={2031} value={year}
              onChange={(e) => setYear(Number(e.target.value) || refYear)} />
          </label>
          <p className="muted small">A value counts for up to five years after it; a state is scored only with at least
            half of the chosen indicators. The map then colours the states by fifths of their values.</p>
        </div>
      </div>

      <div className="builder-actions">
        <button className="measure-option" onClick={onCancel}>Cancel</button>
        <button className="measure-option on" disabled={!ready} onClick={save}>
          {ready ? "Save and show on the map" : !name.trim() ? "Name your index" : !items.length ? "Choose indicators"
            : `Choose a direction for ${undirected}`}
        </button>
      </div>
    </div>
  );
}
