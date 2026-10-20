// The Data tab (P105): a statistical workspace beside the map. Choose a measure from every series in the catalogue,
// add states or whole groups (a REC, an organisation, a category, or a group of one's own), and read them in one of
// several views. Every item can be removed, the first included. Averages, intervals and comparisons are derived by
// stated formulas (stats.ts); shared members of compared groups are named at the bottom.

import { Component, type ReactNode, useEffect, useMemo, useState } from "react";
import { RAMP } from "../data";
import MeasurePicker, { shortSource } from "./MeasurePicker";
import {
  allGroups, type AverageHow, type Catalogue, type ExploreState, type Group, type GroupsDoc, type Item,
  latestCovered, loadCatalogue, loadGroups, loadStates, snapshot, type StatesDoc, useSeries, type View,
} from "./model";
import { coloured, GDP, itemKey, num, POPULATION, resolve, shared } from "./resolve";
import { againstValue, fifths, welch } from "./stats";
import StatsBlock from "./StatsBlock";
import { Dumbbell, Slope } from "./views/Change";
import Composition from "./views/Composition";
import { Heatmap, Profile } from "./views/Grid";
import { Categories, Memberships } from "./views/Groups";
import Lines from "./views/Lines";
import Multiples from "./views/Multiples";
import { Scatter, Trajectory } from "./views/Relation";
import { Distribution, Ordered } from "./views/Snapshot";
import Table from "./views/Table";

export interface MapLayer { colours: Record<string, string>; breaks: number[]; label: string; year: number }

export const VIEWS: { id: View; label: string; group: string }[] = [
  { id: "lines", label: "Lines over time", group: "Over time" },
  { id: "multiples", label: "Small multiples", group: "Over time" },
  { id: "slope", label: "Slope: two years", group: "Over time" },
  { id: "dumbbell", label: "Dumbbell: two years", group: "Over time" },
  { id: "distribution", label: "Distribution of every state", group: "One year" },
  { id: "intervals", label: "Every state in order (with intervals)", group: "One year" },
  { id: "heatmap", label: "Heatmap", group: "One year" },
  { id: "scatter", label: "Scatter: two measures", group: "Two measures" },
  { id: "trajectory", label: "Trajectory: two measures over time", group: "Two measures" },
  { id: "profile", label: "Pillar profile", group: "Shape" },
  { id: "composition", label: "Composition: economy or population", group: "Shape" },
  { id: "categories", label: "Categories across the continent", group: "Groups" },
  { id: "memberships", label: "How the RECs overlap", group: "Groups" },
  { id: "table", label: "Table", group: "Numbers" },
];
const AVERAGES: { id: AverageHow; label: string }[] = [
  { id: "mean", label: "Mean (each state once)" },
  { id: "median", label: "Median state" },
  { id: "population", label: "By population" },
  { id: "gdp", label: "By GDP" },
];
const MAX_COLOURED = 4;

interface Props {
  state: ExploreState;
  setState: (f: (s: ExploreState) => ExploreState) => void;
  onMap: (layer: MapLayer | null) => void;
}

export default function DataTab({ state, setState, onMap }: Props) {
  const [catalogue, setCatalogue] = useState<Catalogue>();
  const [groupsDoc, setGroupsDoc] = useState<GroupsDoc>();
  const [states, setStates] = useState<StatesDoc>();
  const [error, setError] = useState<string>();
  useEffect(() => {
    Promise.all([loadCatalogue(), loadGroups(), loadStates()])
      .then(([c, g, s]) => { setCatalogue(c); setGroupsDoc(g); setStates(s); }).catch((e) => setError(String(e)));
  }, []);
  const groups = useMemo(() => allGroups(groupsDoc, states, state.custom), [groupsDoc, states, state.custom]);
  const names = catalogue?.names ?? {};
  const rs = useMemo(() => resolve(state.items, groups, names), [state.items, groups, names]);
  const measure = catalogue?.measures.find((m) => m.id === state.measure);
  const weighted = state.avg === "population" ? POPULATION : state.avg === "gdp" ? GDP : "";
  const got = useSeries([state.measure, weighted]);
  const s = got[state.measure], weights = weighted ? got[weighted] : undefined;
  const year = Math.min(Math.max(state.year ?? measure?.ref ?? latestCovered(s) ?? 2024, s?.y[0] ?? 2000), s?.y[1] ?? 2031);

  // the map shows the measure at the year: fifths of the states with a value, lighter is higher
  useEffect(() => {
    if (!s || !measure) { onMap(null); return; }
    const snap = snapshot(s, year);
    const xs = Object.values(snap).filter((v): v is number => v !== null);
    if (xs.length < 5) { onMap(null); return; }
    const breaks = fifths(xs);
    const colours = Object.fromEntries(Object.entries(snap).filter(([, v]) => v !== null).map(([k, v]) => {
      let i = 0;
      while (i < breaks.length && (v as number) >= breaks[i]) i++;
      return [k, RAMP[i]];
    }));
    onMap({ colours, breaks, label: measure.label, year });
  }, [s, measure, year, onMap]);
  useEffect(() => () => onMap(null), [onMap]);

  if (error) return <div className="panel-body"><p>Could not load the Data tab: {error}</p></div>;
  if (!catalogue || !groupsDoc || !states) return <div className="panel-body"><p className="muted">Loading the catalogue…</p></div>;

  const set = (patch: Partial<ExploreState>) => setState((x) => ({ ...x, ...patch }));
  const colouredCount = state.items.filter(coloured).length;
  const add = (item: Item) => {
    if (state.items.some((i) => itemKey(i) === itemKey(item))) return;
    set({ items: [...state.items, item] });
  };
  const remove = (key: string) => set({ items: state.items.filter((i) => itemKey(i) !== key) });
  const toggleMode = (key: string) => set({ items: state.items.map((i) => itemKey(i) === key && i.t === "g"
    ? { ...i, mode: i.mode === "members" ? "average" : "members" } : i) });
  const full = colouredCount >= MAX_COLOURED;
  const stateItems = state.items.filter((i): i is { t: "s"; id: string } => i.t === "s");
  const makeGroup = () => {
    const members = stateItems.map((i) => i.id);
    const g: Group = { id: `custom:${Date.now().toString(36)}`, name: `My group (${members.length} states)`,
      kind: "custom", members };
    set({ custom: [...state.custom, g], items: [...state.items.filter((i) => i.t !== "s"), { t: "g", id: g.id, mode: "average" }] });
  };
  const rename = (id: string, name: string) => set({ custom: state.custom.map((g) => g.id === id ? { ...g, name } : g) });

  const common = { rs, s, year, how: state.avg, weights, names };
  const setYear = (y: number) => set({ year: y });
  const setX = (id: string) => set({ x: id });
  const views: Record<View, ReactNode> = measure ? {
    lines: <Lines {...common} measure={measure} />,
    multiples: <Multiples {...common} measure={measure} />,
    slope: <Slope {...common} measure={measure} />,
    dumbbell: <Dumbbell {...common} measure={measure} />,
    distribution: <Distribution {...common} measure={measure} states={states} />,
    intervals: <Ordered {...common} measure={measure} />,
    heatmap: <Heatmap {...common} measure={measure} states={states} catalogue={catalogue} />,
    scatter: <Scatter {...common} measure={measure} setYear={setYear} catalogue={catalogue} xId={state.x} setX={setX} />,
    trajectory: <Trajectory {...common} measure={measure} catalogue={catalogue} xId={state.x} setX={setX} />,
    profile: <Profile {...common} catalogue={catalogue} />,
    composition: <Composition {...common} />,
    categories: <Categories {...common} measure={measure} states={states} attr={state.attr}
      setAttr={(id) => set({ attr: id })} />,
    memberships: <Memberships groups={groups} names={names} />,
    table: <Table {...common} />,
  } : {} as Record<View, ReactNode>;

  return (
    <div className="panel-body dataview-tab">
      <div className="controls">
        <MeasurePicker catalogue={catalogue} value={state.measure} onPick={(id) => set({ measure: id, year: null })} />
        <label className="control"><span className="small muted">View</span>
          <select className="pick" value={state.view} onChange={(e) => set({ view: e.target.value as View })}>
            {[...new Set(VIEWS.map((v) => v.group))].map((g) => (
              <optgroup key={g} label={g}>
                {VIEWS.filter((v) => v.group === g).map((v) => <option key={v.id} value={v.id}>{v.label}</option>)}
              </optgroup>
            ))}
          </select></label>
        <label className="control"><span className="small muted">Group average</span>
          <select className="pick" value={state.avg} onChange={(e) => set({ avg: e.target.value as AverageHow })}>
            {AVERAGES.map((a) => <option key={a.id} value={a.id}>{a.label}</option>)}
          </select></label>
      </div>

      <Selection rs={rs} names={names} groups={groups} states={states} full={full} onAdd={add} onRemove={remove}
        onMode={toggleMode} onMakeGroup={stateItems.length >= 2 ? makeGroup : undefined} onRename={rename} />

      {s && (
        <div className="year">
          <span className="small muted">Year</span>
          <input type="range" min={s.y[0]} max={s.y[1]} value={year} aria-label="Year"
            onChange={(e) => set({ year: Number(e.target.value) })} />
          <b>{year}</b>
          <span className="small muted">{Object.values(snapshot(s, year)).filter((v) => v !== null).length} of 54 states have
            a value · the map and the table read this year</span>
        </div>
      )}

      {!measure ? <p className="note">This series is not in the Data tab: it covers fewer than {catalogue.floor} member
        states since {catalogue.first_year}. Search for another.</p>
        : !s ? <p className="muted">Loading the series…</p>
        : <div className="view"><Guard key={`${state.view}|${state.measure}`}>{views[state.view] ?? views.lines}</Guard>
          {!rs.length && state.view === "lines" && <p className="muted empty-overlay">Add a state or a group to begin.</p>}</div>}

      {measure && s && <StatsBlock rs={rs} s={s} measure={measure} year={year} how={state.avg} weights={weights} names={names}
        states={states} />}
      {measure && s && <Notes rs={rs} measure={measure} catalogue={catalogue} groupsDoc={groupsDoc} year={year}
        how={state.avg} s={s} names={names} />}
    </div>
  );
}

function Selection({ rs, names, groups, states, full, onAdd, onRemove, onMode, onMakeGroup, onRename }: {
  rs: ReturnType<typeof resolve>; names: Record<string, string>; groups: Group[]; states: StatesDoc; full: boolean;
  onAdd: (i: Item) => void; onRemove: (key: string) => void; onMode: (key: string) => void;
  onMakeGroup?: () => void; onRename: (id: string, name: string) => void;
}) {
  const sorted = Object.entries(names).sort((a, b) => a[1].localeCompare(b[1]));
  const kinds: [string, (g: Group) => boolean][] = [
    ["Regional Economic Communities", (g) => g.kind === "rec"],
    ["Organisations", (g) => g.kind === "organisation"],
    ["My groups", (g) => g.kind === "custom"],
  ];
  const attrs = states.attributes.filter((a) => a.id !== "recs" && new Set(Object.values(a.values).flat()).size <= 12);
  return (
    <div className="selection">
      <div className="chips">
        {rs.map((r) => (
          <span key={r.key} className={r.colour ? "chip" : "chip context"} style={r.colour ? { borderColor: r.colour } : {}}>
            <span className="swatch" style={{ background: r.colour ?? "#6f7682" }} />
            {r.group?.kind === "custom"
              ? <input className="chip-name" value={r.group.name} aria-label="Group name"
                onChange={(e) => onRename(r.group!.id, e.target.value)} />
              : r.item.t === "g" ? r.group!.name : r.label}
            {r.item.t === "g" && (
              <button className="chip-mode" onClick={() => onMode(r.key)} disabled={r.item.mode === "members" && full}
                title={r.item.mode === "members" ? "Show the group's average" : "Show every member"}>
                {r.item.mode === "members" ? `${r.members.length} members` : "average"}
              </button>
            )}
            <button onClick={() => onRemove(r.key)} aria-label={`Remove ${r.label}`}>×</button>
          </span>
        ))}
        {!rs.length && <span className="muted small">Nothing chosen: add a state or a group, or click states on the map.</span>}
      </div>
      <div className="adders">
        <select className="pick" value="" disabled={full} aria-label="Add a state"
          onChange={(e) => e.target.value && onAdd({ t: "s", id: e.target.value })}>
          <option value="">{full ? "Four in colour: remove one to add a state" : "+ Add a state"}</option>
          {sorted.map(([k, n]) => <option key={k} value={k}>{n}</option>)}
        </select>
        <select className="pick" value="" aria-label="Add a group"
          onChange={(e) => e.target.value && onAdd({ t: "g", id: e.target.value, mode: full ? "members" : "average" })}>
          <option value="">+ Add a group</option>
          {kinds.map(([label, test]) => {
            const list = groups.filter(test);
            return list.length ? (
              <optgroup key={label} label={label}>
                {list.map((g) => <option key={g.id} value={g.id}>{g.name} ({g.members.length})</option>)}
              </optgroup>
            ) : null;
          })}
          {attrs.map((a) => (
            <optgroup key={a.id} label={a.label}>
              {groups.filter((g) => g.id.startsWith(`cat:${a.id}=`)).map((g) => (
                <option key={g.id} value={g.id}>{g.name.slice(a.label.length + 2)} ({g.members.length})</option>
              ))}
            </optgroup>
          ))}
        </select>
        {onMakeGroup && <button className="linkish small" onClick={onMakeGroup}>Make a group of these states</button>}
      </div>
    </div>
  );
}

function Notes({ rs, measure, catalogue, groupsDoc, year, how, s, names }: {
  rs: ReturnType<typeof resolve>; measure: NonNullable<Catalogue["measures"][number]>; catalogue: Catalogue;
  groupsDoc: GroupsDoc; year: number; how: AverageHow; s: NonNullable<ReturnType<typeof useSeries>[string]>;
  names: Record<string, string>;
}) {
  const src = catalogue.sources[measure.ds];
  const cs = rs.filter((r) => r.colour);
  const first = cs[0];
  const comparisons = first ? cs.slice(1).map((r) => {
    const valuesOf = (x: typeof r) => x.members.map((m) => s.v[m]?.[year - s.y[0]]).filter((v): v is number => typeof v === "number");
    const a = valuesOf(r), b = valuesOf(first);
    const d = r.item.t === "g" && first.item.t === "g" ? welch(a, b)
      : r.item.t === "g" && b.length === 1 ? againstValue(a, b[0])
      : first.item.t === "g" && a.length === 1 ? (() => { const x = againstValue(b, a[0]); return x && { ...x,
        diff: -x.diff, lo: -x.hi, hi: -x.lo }; })()
      : a.length === 1 && b.length === 1 ? { diff: a[0] - b[0], lo: NaN, hi: NaN, df: 0 } : null;
    const how = r.item.t === "g" && first.item.t === "g" ? "Welch's t over the members, who are not independent samples"
      : "the one-sample t-interval of the group's mean";
    return d && { label: r.label, d, how };
  }).filter((x) => !!x) : [];
  const histories = groupsDoc.history.filter((h) => rs.some((r) => r.group?.id === h.group));
  const sharedNotes = shared(rs.filter((r) => r.item.t === "g"), names);
  return (
    <div className="notes small">
      <p><b>{measure.label}</b>{measure.unit && ` (${measure.unit})`}{measure.polarity && `, ${measure.polarity}`}.
        {measure.interval && ` The publisher's ${measure.interval} interval is available in the interval views.`}
        {s.f && " Years the IMF projects are dashed."} Source: {src?.link ? <a href={src.link} target="_blank"
          rel="noreferrer">{src.name}</a> : src?.name ?? shortSource(measure.ds)} · {src?.licence}.</p>
      {comparisons.length > 0 && (
        <div>
          <p className="muted">Compared with {first!.label} at {year} (derived):</p>
          <ul>
            {comparisons.map((c) => (
              <li key={c.label}>{c.label}: {c.d.diff >= 0 ? "+" : ""}{num(c.d.diff)}
                {Number.isFinite(c.d.lo) && ` (95% interval ${num(c.d.lo)} to ${num(c.d.hi)}; ${c.how})`}</li>
            ))}
          </ul>
        </div>
      )}
      {rs.some((r) => r.item.t === "g") && (
        <p className="muted">Group averages: {how === "mean" ? "the mean of the members with a value, each counting once"
          : how === "median" ? "the median member" : how === "population" ? "weighted by population (WDI SP.POP.TOTL)"
          : "weighted by GDP in current US$ (WDI NY.GDP.MKTP.CD)"}; drawn only where at least half the members have a
          value; the ribbon runs from the lowest member to the highest. {groupsDoc.note} A group average describes the
          group, not each member.</p>
      )}
      {sharedNotes.map((n) => <p key={n} className="shared">{n}</p>)}
      {histories.map((h) => <p key={h.date + h.group} className="muted">{h.group}: {h.change} on {h.date} ({h.source}).</p>)}
      {rs.some((r) => r.group?.kind === "rec") && (
        <p className="muted">REC membership is the owner's compilation; Wikidata's records were checked against it
          and differ only by members Wikidata lacks.</p>
      )}
      <p className="muted">Values as each publisher prints them, to four significant figures; nothing is
        filled or rescaled.</p>
    </div>
  );
}

/** A view that fails says so and leaves the rest of the site working. */
class Guard extends Component<{ children: ReactNode }, { error: string | null }> {
  state = { error: null as string | null };
  static getDerivedStateFromError(e: unknown) {
    return { error: String(e) };
  }
  render() {
    return this.state.error ? <p className="note">This view could not be drawn: {this.state.error}</p> : this.props.children;
  }
}
