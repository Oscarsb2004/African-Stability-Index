// The site (P55): a satellite globe with four sections. Choosing a country opens its panel on the right (P56).

import { useEffect, useMemo, useState } from "react";
import MapView from "./MapView";
import MethodPage from "./MethodPage";
import PhotoViewer from "./PhotoViewer";
import EconomyPanel from "./panels/EconomyPanel";
import FinancePanel from "./panels/FinancePanel";
import WondersPanel from "./panels/WondersPanel";
import InfrastructurePanel from "./panels/InfrastructurePanel";
import StabilityPanel from "./panels/StabilityPanel";
import { load, RAMP, type MetaDoc, type Section, type SectionsDoc, type StabilityDoc, type Wonder,
  type WondersDoc } from "./data";

const SECTIONS: { id: Section; label: string }[] = [
  { id: "stability", label: "Stability" },
  { id: "economy", label: "Economy" },
  { id: "finance", label: "Finance" },
  { id: "infrastructure", label: "Infrastructure" },
  { id: "wonders", label: "Wonders" },
];

interface Docs { meta: MetaDoc; stability: StabilityDoc; sections: SectionsDoc }

export default function App() {
  const [docs, setDocs] = useState<Docs | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [section, setSection] = useState<Section>("stability");
  const [selected, setSelected] = useState<string | null>(null);
  const [showClasses, setShowClasses] = useState(true);
  const [wonders, setWonders] = useState<WondersDoc | null>(null);
  const [viewing, setViewing] = useState<Wonder | null>(null);
  // the method page has its own address, #method, so it can be linked to
  const [method, setMethod] = useState(() => window.location.hash === "#method");
  useEffect(() => {
    const sync = () => setMethod(window.location.hash === "#method");
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);
  const openMethod = () => { window.location.hash = "method"; };
  const closeMethod = () => {
    history.replaceState(null, "", window.location.pathname + window.location.search);
    setMethod(false);
  };

  useEffect(() => {
    Promise.all([load<MetaDoc>("data/meta.json"), load<StabilityDoc>("data/stability.json"),
      load<SectionsDoc>("data/sections.json")])
      .then(([meta, stability, sections]) => setDocs({ meta, stability, sections }))
      .catch((e) => setError(String(e)));
    load<WondersDoc>("data/wonders.json").then(setWonders).catch(() => setWonders(null));  // optional
  }, []);

  const names = useMemo(() => docs ? Object.entries(docs.sections.names).sort((a, b) => a[1].localeCompare(b[1]))
    : [], [docs]);

  if (error) return <div className="loading">Could not load the data: {error}</div>;
  if (!docs) return <div className="loading">Loading…</div>;

  const breaks = docs.stability.classes.breaks;
  const edges = [null, ...breaks, null];
  return (
    <div className="app">
      <MapView meta={docs.meta} stability={docs.stability} section={section} selected={selected}
        showClasses={showClasses} onSelect={setSelected} wonders={wonders?.wonders ?? null}
        onWonder={setViewing} />

      <div className="topleft">
      <header className="glass masthead">
        <div className="brand">
          <div className="brand-title">African Stability Atlas</div>
          <div className="brand-sub">54 African Union member states</div>
        </div>
        <nav className="tabs" aria-label="Sections">
          {SECTIONS.map((s) => (
            <button key={s.id} className={s.id === section ? "tab on" : "tab"} aria-pressed={s.id === section}
              onClick={() => setSection(s.id)}>{s.label}</button>
          ))}
        </nav>
        <select className="pick" value={selected ?? ""} onChange={(e) => setSelected(e.target.value || null)}
          aria-label="Choose a country">
          <option value="">Choose a country…</option>
          {names.map(([iso3, name]) => <option key={iso3} value={iso3}>{name}</option>)}
        </select>
      </header>

      {section === "stability" && (
        <div className="glass legend">
          <label className="legend-toggle">
            <input type="checkbox" checked={showClasses} onChange={(e) => setShowClasses(e.target.checked)} />
            ASI {docs.stability.reference_year}, composite score
          </label>
          {showClasses && (
            <>
              <div className="legend-ramp">
                {RAMP.map((c, i) => (
                  <div key={c} className="legend-step">
                    <span style={{ background: c }} />
                    <small>{edges[i] === null ? `< ${edges[i + 1]}` : edges[i + 1] === null ? `≥ ${edges[i]}`
                      : `${edges[i]}–${edges[i + 1]}`}</small>
                  </div>
                ))}
              </div>
              <div className="muted small">Classes: {docs.stability.classes.rule}. Lighter is more stable.</div>
            </>
          )}
        </div>
      )}
      </div>

      <aside className={selected ? "glass panel open" : "glass panel idle"} aria-live="polite">
        {selected ? (
          <>
            <div className="panel-head">
              <div>
                <div className="panel-kicker">{SECTIONS.find((s) => s.id === section)?.label}</div>
                <h2>{docs.sections.names[selected]}</h2>
              </div>
              <button className="close" onClick={() => setSelected(null)} aria-label="Close">×</button>
            </div>
            {section === "stability" && <StabilityPanel iso3={selected} stability={docs.stability} sections={docs.sections}
              onMethod={openMethod} />}
            {section === "economy" && <EconomyPanel iso3={selected} doc={docs.sections} />}
            {section === "finance" && <FinancePanel iso3={selected} doc={docs.sections} />}
            {section === "infrastructure" && <InfrastructurePanel iso3={selected} />}
            {section === "wonders" && <WondersPanel doc={wonders} iso3={selected} names={docs.sections.names}
              onOpen={setViewing} />}
            <details className="sources">
              <summary className="muted small">Sources and licences</summary>
              {docs.meta.sources.map((s) => (
                <div key={s.name} className="small">
                  {s.link ? <a href={s.link} target="_blank" rel="noreferrer">{s.name}</a> : s.name}
                  <span className="muted"> · {s.licence}</span>
                </div>
              ))}
            </details>
          </>
        ) : (
          <div className="panel-body welcome">
            <h2>Choose a country</h2>
            <p>Click a country on the map, or pick one above. Hovering shows its name.</p>
            {section === "wonders" ? <WondersPanel doc={wonders} iso3={null} names={docs.sections.names}
              onOpen={setViewing} /> : (
              <p className="muted small">
                Stability shows the ASI next to other institutions' scores. Economy leads with the IMF's outlook,
                then the latest figures and the record. Finance covers money, the currency and reserves, banks,
                markets and debt. Infrastructure shows cities now; roads, rail, ports and megaprojects follow.{" "}
                <button className="linkish" onClick={openMethod}>How the index is built</button>
              </p>
            )}
          </div>
        )}
      </aside>
      <button className="glass footer-link" onClick={openMethod}>How the index is built</button>
      {viewing && <PhotoViewer wonder={viewing} onClose={() => setViewing(null)} />}
      {method && <MethodPage onClose={closeMethod} />}
    </div>
  );
}
