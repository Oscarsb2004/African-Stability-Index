// The data view of the Stability section: the chosen state beside up to three others, over time, on the headline,
// any pillar or any indicator (its score or its raw value). One axis, a line per state in the validated comparison
// colours, each labelled at its end, and a crosshair that reads every line at a year. series.json is loaded only
// when this view opens.

import { useEffect, useMemo, useState } from "react";
import { COMPARE, load, type SeriesDoc, type StabilityDoc } from "./data";

interface Props {
  iso3: string;
  stability: StabilityDoc;
  names: Record<string, string>;
}

const W = 360, H = 190, PAD = { l: 34, r: 44, t: 10, b: 20 };

export default function DataView({ iso3, stability, names }: Props) {
  const [doc, setDoc] = useState<SeriesDoc | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [measure, setMeasure] = useState("headline");
  const [raw, setRaw] = useState(false);
  const [others, setOthers] = useState<string[]>([]);
  const [at, setAt] = useState<number | null>(null);
  useEffect(() => { load<SeriesDoc>("data/series.json").then(setDoc).catch((e) => setError(String(e))); }, []);
  useEffect(() => setOthers((o) => o.filter((x) => x !== iso3)), [iso3]);

  const states = [iso3, ...others];
  const isIndicator = measure.startsWith("i:");
  const label = measure === "headline" ? "The headline score"
    : measure.startsWith("p:") ? stability.pillars[measure.slice(2)].name
      : stability.indicators[measure.slice(2)].display_name;
  const lines = useMemo(() => {
    if (!doc) return [];
    return states.map((s) => {
      const c = doc.countries[s];
      const v = measure === "headline" ? c.headline
        : measure.startsWith("p:") ? c.pillars[measure.slice(2)]
          : c.indicators[measure.slice(2)]?.[raw ? "raw" : "score"];
      return { iso3: s, values: v ?? doc.years.map(() => null) };
    });
  }, [doc, measure, raw, states.join(",")]);

  if (error) return <p className="muted">Could not load the series: {error}</p>;
  if (!doc) return <p className="muted">Loading the series…</p>;

  const known = lines.flatMap((l) => l.values.filter((v): v is number => v !== null));
  const years = doc.years;
  let lo = known.length ? Math.min(...known) : 0, hi = known.length ? Math.max(...known) : 1;
  const scores = !raw || !isIndicator;
  if (hi === lo) hi = lo + 1;
  // the axis spans the data, widened to a round step (1, 2 or 5 times a power of ten) so differences between
  // states stay visible and the ticks read cleanly; scores stay within 0-100
  const p = 10 ** Math.floor(Math.log10((hi - lo) / 3)), f = (hi - lo) / 3 / p;
  const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * p;
  lo = Math.floor(lo / step) * step; hi = Math.ceil(hi / step) * step;
  if (scores) { lo = Math.max(0, lo); hi = Math.min(100, hi); }
  const x = (i: number) => PAD.l + (i / (years.length - 1)) * (W - PAD.l - PAD.r);
  const y = (v: number) => PAD.t + (1 - (v - lo) / (hi - lo)) * (H - PAD.t - PAD.b);
  const path = (vals: (number | null)[]) => vals.reduce((d, v, i) =>
    v === null ? d : d + `${d && vals[i - 1] !== null ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`, "");
  const last = (vals: (number | null)[]) => {
    for (let i = vals.length - 1; i >= 0; i -= 1) if (vals[i] !== null) return i;
    return -1;
  };
  const fmt = (v: number | null) => v === null ? "—"
    : raw && isIndicator ? v.toLocaleString(undefined, { maximumSignificantDigits: 4 }) : v.toFixed(1);
  const move = (e: React.MouseEvent<SVGRectElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const fx = ((e.clientX - r.left) / r.width) * W;
    setAt(Math.max(0, Math.min(years.length - 1, Math.round(((fx - PAD.l) / (W - PAD.l - PAD.r)) * (years.length - 1)))));
  };
  const ticks = Array.from({ length: Math.round((hi - lo) / step) + 1 }, (_, k) => lo + k * step);
  const tick = (v: number) => Number(v.toPrecision(6)).toLocaleString();
  // end labels sorted by height and pushed at least 10 units apart, so none overlaps another
  const ends = lines.map((l, i) => ({ i, j: last(l.values) })).filter((e) => e.j >= 0)
    .map((e) => ({ ...e, y: y(lines[e.i].values[e.j] as number) + 3 })).sort((a, b) => a.y - b.y);
  ends.forEach((e, k) => { if (k > 0 && e.y < ends[k - 1].y + 10) e.y = ends[k - 1].y + 10; });
  const ref = years.indexOf(stability.reference_year);
  const free = Object.keys(names).filter((k) => !states.includes(k)).sort((a, b) => names[a].localeCompare(names[b]));

  return (
    <div className="dataview">
      <div className="controls">
        <select className="pick" value={measure} onChange={(e) => setMeasure(e.target.value)} aria-label="Measure">
          <option value="headline">Headline score</option>
          <optgroup label="Pillars">
            {Object.entries(stability.pillars).map(([id, p]) => <option key={id} value={`p:${id}`}>{p.name}</option>)}
          </optgroup>
          {Object.entries(stability.pillars).map(([id, p]) => (
            <optgroup key={id} label={`${p.name}: indicators`}>
              {p.indicators.filter((v) => stability.indicators[v]).map((v) => (
                <option key={v} value={`i:${v}`}>{stability.indicators[v].display_name}</option>
              ))}
            </optgroup>
          ))}
        </select>
        {isIndicator && (
          <label className="small"><input type="checkbox" checked={raw} onChange={(e) => setRaw(e.target.checked)} />
            {" "}raw values</label>
        )}
      </div>
      <div className="chips">
        {states.map((s, i) => (
          <span key={s} className="chip" style={{ borderColor: COMPARE[i] }}>
            <span className="swatch" style={{ background: COMPARE[i] }} />{names[s]}
            {s !== iso3 && <button onClick={() => setOthers(others.filter((o) => o !== s))}
              aria-label={`Remove ${names[s]}`}>×</button>}
          </span>
        ))}
        {states.length < COMPARE.length && (
          <select className="pick" value="" onChange={(e) => e.target.value && setOthers([...others, e.target.value])}
            aria-label="Add a state to compare">
            <option value="">+ compare with…</option>
            {free.map((k) => <option key={k} value={k}>{names[k]}</option>)}
          </select>
        )}
      </div>
      <div className="small"><b>{label}</b>{isIndicator && raw ? " (the publisher's units)" : " (0 to 100, higher is more stable)"}</div>
      <div className="chart">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${label}, ${years[0]} to ${years[years.length - 1]}`}>
          {ticks.map((t) => (
            <g key={t}>
              <line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} className="grid" />
              <text x={PAD.l - 4} y={y(t) + 3} className="tick" textAnchor="end">{tick(t)}</text>
            </g>
          ))}
          <text x={PAD.l} y={H - 4} className="tick">{years[0]}</text>
          <text x={W - PAD.r} y={H - 4} className="tick" textAnchor="end">{years[years.length - 1]}</text>
          {lines.map((l, i) => <path key={l.iso3} d={path(l.values)} className="multi" style={{ stroke: COMPARE[i] }} />)}
          {ends.map((e) => (
            <text key={e.i} x={x(e.j) + 4} y={e.y} className="tick end-label">
              {lines[e.i].iso3}</text>
          ))}
          {at !== null && <line x1={x(at)} x2={x(at)} y1={PAD.t} y2={H - PAD.b} className="cross" />}
          {at !== null && lines.map((l, i) => l.values[at] === null ? null : (
            <circle key={l.iso3} cx={x(at)} cy={y(l.values[at] as number)} r={4} style={{ fill: COMPARE[i] }} />
          ))}
          <rect x={0} y={0} width={W} height={H} fill="transparent" onMouseMove={move} onMouseLeave={() => setAt(null)} />
        </svg>
        <div className="chart-read small">
          {at === null ? <span className="muted">Hover for each state's value in a year</span>
            : <>{years[at]}: {lines.map((l, i) => (
              <span key={l.iso3}> <span className="swatch" style={{ background: COMPARE[i] }} />{names[l.iso3]} <b>{fmt(l.values[at])}</b></span>
            ))}</>}
        </div>
      </div>
      <table className="rows">
        <thead><tr><th>State</th><th className="num">{years[ref - 10]}</th><th className="num">{years[ref]}</th></tr></thead>
        <tbody>
          {lines.map((l, i) => (
            <tr key={l.iso3}>
              <td><span className="swatch" style={{ background: COMPARE[i] }} />{names[l.iso3]}</td>
              <td className="num">{fmt(l.values[ref - 10] ?? null)}</td>
              <td className="num">{fmt(l.values[ref] ?? null)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="muted small">{doc.note}</p>
    </div>
  );
}
