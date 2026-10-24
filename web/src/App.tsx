// The site (P55): a satellite globe with five sections and a Data tab. Choosing a country opens its panel on the
// right (P56); the Data tab opens a wide workspace beside the map, and the map shows its measure (P105).

import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import type { MapLayer } from "./explore/DataTab";
import { DEFAULT, type ExploreState, fromHash, rememberedGroups, rememberGroups, toHash } from "./explore/model";
import { coloured } from "./explore/resolve";
import GroupPicker from "./GroupPicker";
import MapView from "./MapView";
import MethodPage from "./MethodPage";
import PhotoViewer from "./PhotoViewer";
import EconomyPanel from "./panels/EconomyPanel";
import FinancePanel from "./panels/FinancePanel";
import WondersPanel from "./panels/WondersPanel";
import InfrastructurePanel from "./panels/InfrastructurePanel";
import StabilityPanel from "./panels/StabilityPanel";
import StabilityMenu from "./StabilityMenu";
import { shown, shownValues, type Shown, type StabilityMeasure } from "./stabilityMap";
import { AGGREGATES, type CustomIndex, fromIndexHash, indexHash, loadIndexSeries, METHODS, rememberedIndices,
  rememberIndices, scoreIndex } from "./customIndex";
import type { Group } from "./explore/model";
import { load, RAMP, type MetaDoc, type Section, type SectionsDoc, type StabilityDoc, type Wonder,
  type WondersDoc } from "./data";
import { COLOURS, EDGE, SHAPES, SHOWN_FIRST, type LayersDoc } from "./infra";

const SECTIONS: { id: Section; label: string }[] = [
  { id: "stability", label: "Stability" },
  { id: "economy", label: "Economy" },
  { id: "finance", label: "Finance" },
  { id: "infrastructure", label: "Infrastructure" },
  { id: "wonders", label: "Wonders" },
  { id: "data", label: "Data" },
];
const DataTab = lazy(() => import("./explore/DataTab"));  // loaded only when the tab opens

interface Docs { meta: MetaDoc; stability: StabilityDoc; sections: SectionsDoc }

export default function App() {
  const [docs, setDocs] = useState<Docs | null>(null);
  const [error, setError] = useState<string | null>(null);
  const initial = useMemo(() => fromHash(window.location.hash), []);
  const [section, setSection] = useState<Section>(initial ? "data" : "stability");
  const [explore, setExplore] = useState<ExploreState>(() => initial ?? { ...DEFAULT, custom: rememberedGroups() });
  const [layer, setLayer] = useState<MapLayer | null>(null);
  const onMap = useCallback((l: MapLayer | null) => setLayer(l), []);
  const [selected, setSelected] = useState<string | null>(null);
  const [showClasses, setShowClasses] = useState(true);
  const [cities, setCities] = useState(false);  // cities and towns are drawn only when switched on
  // the Stability map: what it shows (the composite, a pillar or an indicator) and an optional grouping it is cut to
  // a reader's own indices (customIndex.ts), kept in this browser; one shared by address is added and shown
  const [shared] = useState<CustomIndex | null>(() => fromIndexHash(window.location.hash));
  const [indices, setIndices] = useState<CustomIndex[]>(() => {
    const list = rememberedIndices();
    return shared && !list.some((ix) => ix.name === shared.name) ? [...list, shared] : list;
  });
  useEffect(() => rememberIndices(indices), [indices]);
  const [measure, setMeasure] = useState<StabilityMeasure>(() => shared
    ? `custom:${(rememberedIndices().find((ix) => ix.name === shared.name) ?? shared).id}` : "composite");
  const [custom, setCustom] = useState<Shown | null>(null);
  const [group, setGroup] = useState<Group | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = useCallback(() => setMenuOpen(false), []);
  const [wonders, setWonders] = useState<WondersDoc | null>(null);
  const [viewing, setViewing] = useState<Wonder | null>(null);
  const [infra, setInfra] = useState<LayersDoc | null>(null);
  const [infraOn, setInfraOn] = useState<string[]>(SHOWN_FIRST);
  // the Infrastructure catalogue is loaded the first time the section opens
  useEffect(() => {
    if (section === "infrastructure" && !infra) load<LayersDoc>("geo/infra/layers.json").then(setInfra).catch(() => {});
  }, [section, infra]);
  const toggle = (id: string) => setInfraOn((on) => on.includes(id) ? on.filter((x) => x !== id) : [...on, id]);
  const [layersOpen, setLayersOpen] = useState(() => window.innerWidth >= 760);  // closed on a phone, where it covers the map
  // the method page has its own address, #method, so it can be linked to
  const [method, setMethod] = useState(() => window.location.hash === "#method");
  useEffect(() => {
    const sync = () => {
      setMethod(window.location.hash === "#method");
      const shared = fromHash(window.location.hash);  // a Data view pasted into the address
      if (shared) { setExplore(shared); setSection("data"); }
    };
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);
  const openMethod = () => { window.location.hash = "method"; };
  // the Data tab's view lives in the address while the tab is open, so it can be shared
  useEffect(() => {
    if (method) return;
    if (section === "data") history.replaceState(null, "", "#" + toHash(explore));
    else if (window.location.hash.startsWith("#data=")) history.replaceState(null, "", window.location.pathname);
  }, [explore, section, method]);
  useEffect(() => rememberGroups(explore.custom), [explore.custom]);
  const choose = (s: Section) => {
    if (s === "data" && selected) setExplore((x) => x.items.length ? x : { ...x, items: [{ t: "s", id: selected }] });
    setSection(s);
  };
  // "Compare" from any tab: the Data tab with that measure, and the chosen country added
  const compare = (measure: string) => {
    setExplore((x) => {
      const has = !selected || x.items.some((i) => i.t === "s" && i.id === selected);
      const room = x.items.filter(coloured).length < 4;
      return { ...x, measure, year: null, items: has || !room ? x.items : [...x.items, { t: "s", id: selected as string }] };
    });
    setSection("data");
  };
  // in the Data tab a click on the map adds a state to the comparison, or takes it out
  const onMapSelect = (iso3: string | null) => {
    if (section !== "data") { setSelected(iso3); return; }
    if (!iso3) return;
    setExplore((x) => x.items.some((i) => i.t === "s" && i.id === iso3)
      ? { ...x, items: x.items.filter((i) => !(i.t === "s" && i.id === iso3)) }
      : x.items.filter(coloured).length >= 4 ? x : { ...x, items: [...x.items, { t: "s", id: iso3 }] });
  };
  const closeMethod = () => {
    history.replaceState(null, "", window.location.pathname + window.location.search);
    setMethod(false);
  };

  useEffect(() => {
    Promise.all([load<MetaDoc>("data/meta.json"), load<StabilityDoc>("data/stability.json"),
      load<SectionsDoc>("data/sections.json")])
      .then(([meta, stability, sections]) => setDocs({ meta, stability, sections }))
      .catch((e) => setError(String(e)));
  }, []);
  // the wonders are loaded the first time their section opens; they are optional
  useEffect(() => {
    if (section === "wonders" && !wonders) load<WondersDoc>("data/wonders.json").then(setWonders).catch(() => {});
  }, [section, wonders]);

  const names = useMemo(() => docs ? Object.entries(docs.sections.names).sort((a, b) => a[1].localeCompare(b[1]))
    : [], [docs]);
  // a reader's own index is scored from its series once they load; until then the map keeps its colours
  useEffect(() => {
    const ix = measure.startsWith("custom:") ? indices.find((x) => `custom:${x.id}` === measure) : undefined;
    if (!ix || !docs) { setCustom(null); return; }
    let live = true;
    loadIndexSeries(ix).then((series) => {
      if (!live) return;
      const { values } = scoreIndex(ix, series, Object.keys(docs.sections.names));
      const method = METHODS.find((m) => m.id === ix.method)?.label, agg = AGGREGATES.find((a) => a.id === ix.aggregate)?.label;
      setCustom(shownValues(ix.name, values, `Your index, built in this browser, not the ASI: ${ix.items.length} indicators, ` +
        `${method}, ${agg?.toLowerCase()}, ${ix.year}. Fifths of the states with a value; lighter is higher.`));
    });
    return () => { live = false; };
  }, [measure, indices, docs]);
  const stab = useMemo(() => !docs ? null : measure.startsWith("custom:") ? custom : shown(docs.stability, measure),
    [docs, measure, custom]);

  if (error) return <div className="loading">Could not load the data: {error}</div>;
  if (!docs) return <div className="loading">Loading…</div>;

  const edges = [null, ...(stab?.breaks ?? []), null];
  return (
    <div className="app">
      <MapView meta={docs.meta} stability={docs.stability} section={section} selected={section === "data" ? null : selected}
        showClasses={showClasses} choropleth={section === "data" ? layer?.colours ?? null : null}
        marked={section === "data" ? explore.items.filter((i) => i.t === "s").map((i) => i.id) : []}
        onSelect={onMapSelect} wonders={wonders?.wonders ?? null} onWonder={setViewing} infra={infra} infraOn={infraOn}
        cities={cities} names={docs.sections.names} stabilityColours={stab?.colours ?? null}
        only={section === "stability" ? group?.members ?? null : null} />

      <div className="topleft">
      <header className="glass masthead">
        <div className="brand">
          <div className="brand-title">African Stability Atlas</div>
          <div className="brand-sub">54 African Union member states</div>
        </div>
        <nav className="tabs" aria-label="Sections">
          {SECTIONS.map((s) => (
            <button key={s.id} className={s.id === section ? "tab on" : "tab"} aria-pressed={s.id === section}
              onClick={() => choose(s.id)}>{s.label}</button>
          ))}
        </nav>
        {section === "stability" ? (
          <GroupPicker value={group?.id ?? null} names={docs.sections.names} onChange={setGroup} />
        ) : (
          <select className="pick" value={selected ?? ""} onChange={(e) => setSelected(e.target.value || null)}
            aria-label="Choose a country">
            <option value="">Choose a country…</option>
            {names.map(([iso3, name]) => <option key={iso3} value={iso3}>{name}</option>)}
          </select>
        )}
        {section !== "wonders" && (
          <label className="infra-toggle cities-toggle"
            title="Capitals first, more as you zoom: Natural Earth's populated places (public domain)">
            <input type="checkbox" checked={cities} onChange={(e) => setCities(e.target.checked)} />
            <span className="swatch dot" style={{ background: "#f4f1ea" }} />
            Cities and towns
          </label>
        )}
      </header>

      {section === "stability" && (
        <div className="glass legend">
          <div className="legend-toggle legend-head">
            <input type="checkbox" checked={showClasses} onChange={(e) => setShowClasses(e.target.checked)}
              aria-label="Show the map's colours" />
            <button className="measure-button" onClick={() => setMenuOpen(true)} aria-haspopup="dialog"
              title="Choose what the map shows">
              {stab?.label} <span className="muted">▾</span>
            </button>
          </div>
          {showClasses && stab && (
            <>
              <div className="legend-ramp">
                {RAMP.map((c, i) => (
                  <div key={c} className="legend-step">
                    <span style={{ background: c }} />
                    <small>{edges[i] === null ? `< ${fmtBreak(edges[i + 1] as number)}` : edges[i + 1] === null
                      ? `≥ ${fmtBreak(edges[i] as number)}` : `${fmtBreak(edges[i] as number)}–${fmtBreak(edges[i + 1] as number)}`}</small>
                  </div>
                ))}
              </div>
              <div className="muted small">{stab.scale}</div>
              {group && <div className="muted small">Only the {group.members.length} members of {group.name} are
                coloured; the classes are the 54 states'.</div>}
            </>
          )}
          {menuOpen && <StabilityMenu stability={docs.stability} value={measure} onChange={setMeasure}
            onClose={closeMenu} indices={indices}
            onSaveIndex={(ix) => setIndices((xs) => [...xs, ix])}
            onDeleteIndex={(id) => { setIndices((xs) => xs.filter((x) => x.id !== id));
              if (measure === `custom:${id}`) setMeasure("composite"); }}
            shareLink={(ix) => `${window.location.origin}${window.location.pathname}#${indexHash(ix)}`} />}
        </div>
      )}
      {section === "infrastructure" && infra && (
        <details className="glass legend infra-legend" open={layersOpen}
          onToggle={(e) => setLayersOpen(e.currentTarget.open)}>
          <summary className="legend-toggle">Layers <span className="muted small">{infraOn.length} on</span></summary>
          {[...infra.points, ...infra.lines].map((l) => (
            <label key={l.id} className="infra-toggle" title={`${l.note} ${l.attribution}, ${l.licence}.`}>
              <input type="checkbox" checked={infraOn.includes(l.id)} onChange={() => toggle(l.id)} />
              <span className={l.kind === "points" ? `swatch ${SHAPES[l.id]?.shape ?? "dot"}` : "swatch line"}
                style={SHAPES[l.id]?.shape === "ring" ? { borderColor: SHAPES[l.id].colour }
                  : SHAPES[l.id] ? { background: SHAPES[l.id].colour, boxShadow: `0 0 0 1px ${EDGE}` }
                  : { background: COLOURS[l.id] }} />
              {l.title} <span className="muted small">{l.count.toLocaleString("en")}</span>
            </label>
          ))}
          <div className="muted small">The lines appear as you zoom in. Click a point for its card; hover a layer for
            its source and licence. {infra.withheld.length} layers are withheld, each for a stated reason.</div>
        </details>
      )}
      {section === "data" && layer && (
        <div className="glass legend data-legend">
          <div className="legend-toggle">{layer.label}, {layer.year}</div>
          <div className="legend-ramp">
            {layer.ramp.map((c, i) => (
              <div key={c} className="legend-step">
                <span style={{ background: c }} />
                <small>{i === 0 ? `< ${fmtBreak(layer.breaks[0])}` : i === layer.ramp.length - 1
                  ? `≥ ${fmtBreak(layer.breaks[i - 1])}` : `${fmtBreak(layer.breaks[i - 1])}–${fmtBreak(layer.breaks[i])}`}</small>
              </div>
            ))}
          </div>
          <div className="muted small">{layer.signed
            ? "Red below zero, blue above, each side split at its median; the colours mark the sign, not whether it is good. Grey has no value."
            : "Fifths of the states with a value. Lighter is higher; grey has no value."}</div>
        </div>
      )}
      </div>

      {section === "data" ? (
        <aside className="glass panel wide open" aria-live="polite">
          <div className="panel-head">
            <div>
              <div className="panel-kicker">Data</div>
              <h2>Compare states and groups</h2>
            </div>
            <button className="linkish small" onClick={openMethod}>How the index is built</button>
          </div>
          <Suspense fallback={<div className="panel-body"><p className="muted">Loading the Data tab…</p></div>}>
            <DataTab state={explore} setState={setExplore} onMap={onMap} />
          </Suspense>
        </aside>
      ) : (
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
              onMethod={openMethod} onCompare={compare} />}
            {section === "economy" && <EconomyPanel iso3={selected} doc={docs.sections} onCompare={compare} />}
            {section === "finance" && <FinancePanel iso3={selected} doc={docs.sections} onCompare={compare} />}
            {section === "infrastructure" && <InfrastructurePanel iso3={selected} infra={infra} doc={docs.sections}
              onCompare={compare} />}
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
                markets and debt. Infrastructure maps ports, mines, railways, roads and the power grid, with each
                country's own figures.{" "}
                <button className="linkish" onClick={openMethod}>How the index is built</button>
              </p>
            )}
          </div>
        )}
      </aside>
      )}
      {section !== "data" && <button className="glass footer-link" onClick={openMethod}>How the index is built</button>}
      {viewing && <PhotoViewer wonder={viewing} onClose={() => setViewing(null)} />}
      {method && <MethodPage onClose={closeMethod} />}
    </div>
  );
}

function fmtBreak(v: number): string {
  return v.toLocaleString("en", { maximumSignificantDigits: 3 });
}
