// Stability: the ASI as one appraisal among several (P53). The composite drills down to pillars, and each pillar
// to its indicators. Other institutions' scores follow on their own scales, with their own intervals.

import { useState } from "react";
import LineChart from "../LineChart";
import { fmt, type Figure, type SectionsDoc, type StabilityDoc } from "../data";

interface Props {
  iso3: string;
  stability: StabilityDoc;
  sections: SectionsDoc;
}

function Bar({ score }: { score: number | null }) {
  return (
    <div className="bar"><div className="bar-fill" style={{ width: `${score ?? 0}%` }} /></div>
  );
}

function Interval({ f, level = 90 }: { f: Figure; level?: number }) {
  if (f.value === null) return <span className="muted">—</span>;
  const lo = f.lower ?? f.value, hi = f.upper ?? f.value;
  return (
    <svg viewBox="0 0 100 12" className="interval" preserveAspectRatio="none" role="img"
      aria-label={`${f.value.toFixed(1)}, ${level}% interval ${lo.toFixed(1)} to ${hi.toFixed(1)}`}>
      <line x1={0} x2={100} y1={6} y2={6} className="track" />
      <line x1={lo} x2={hi} y1={6} y2={6} className="whisker" />
      <circle cx={f.value} cy={6} r={3.2} className="point" />
    </svg>
  );
}

export default function StabilityPanel({ iso3, stability, sections }: Props) {
  const [open, setOpen] = useState<string | null>(null);
  const c = stability.countries[iso3];
  const h = c.composite;
  const appraisals = sections.sections.find((s) => s.id === "appraisals");
  const a = sections.areas[iso3].appraisals;
  // the narrative's first two sentences restate the hero (score, interval, tier, band), so the panel shows the rest
  const words = h.tier !== null ? c.narrative.slice(2) : c.narrative;
  return (
    <div className="panel-body">
      <h3>African Stability Index <span className="tag ours">this project</span></h3>
      <div className="hero">
        <div className="hero-value">{h.score.toFixed(1)}</div>
        <div className="hero-side">
          <div>out of 100, {stability.reference_year}</div>
          {h.ci_low !== null && h.ci_high !== null && (
            <div className="small">95% interval {h.ci_low.toFixed(1)} to {h.ci_high.toFixed(1)}</div>
          )}
          {h.tier !== null && (
            <div className="small">
              Tier {h.tier} of {stability.n_tiers}: its rank could be anywhere from {h.band_best} to {h.band_worst} of{" "}
              {stability.n_ranked}
            </div>
          )}
          <div className="muted small">{stability.method}; reliability: {h.reliability}</div>
          <div className="muted small">Edition 2, from {stability.inputs}.</div>
        </div>
      </div>
      {h.ci_low !== null && h.ci_high !== null && (
        <Interval f={{ value: h.score, lower: h.ci_low, upper: h.ci_high } as Figure} level={95} />
      )}
      <LineChart periods={c.history.years.map(String)} values={c.history.scores} unit="points" height={90} zero={false} />

      <h3>In words</h3>
      <p className="small">{words.join(" ")}</p>

      <h3>Pillars</h3>
      <p className="muted small">Click a pillar for its indicators. A pillar measured too thinly that year is left out of
        the score.</p>
      <ul className="pillars">
        {Object.entries(stability.pillars).map(([id, p]) => {
          const s = c.pillars[id];
          return (
            <li key={id}>
              <button className="pillar" onClick={() => setOpen(open === id ? null : id)} aria-expanded={open === id}>
                <span className="pillar-name">
                  {id} · {p.name}
                  {s && s.score !== null && s.reliability !== "reliable" && s.reliability !== "thin" && (
                    <> <span className="tag">left out</span></>
                  )}
                </span>
                <Bar score={s?.score ?? null} />
                <span className="num">{s?.score === null || !s ? "—" : s.score.toFixed(1)}</span>
              </button>
              {open === id && (
                <table className="rows indicators">
                  <tbody>
                    {p.indicators.filter((v) => stability.indicators[v]).map((v) => {
                      const i = c.indicators[v];
                      return (
                        <tr key={v}>
                          <td>{stability.indicators[v].display_name}</td>
                          <td className="num">{i?.score === null || !i ? "—" : i.score.toFixed(1)}</td>
                          <td className="period" title={`raw ${i?.raw ?? "—"}`}>
                            {i?.provenance === "observed" ? i.source_year : <span className="tag">{i?.provenance}</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </li>
          );
        })}
      </ul>

      <h3>Other appraisals</h3>
      <p className="muted small">{appraisals?.about}</p>
      <table className="rows appraisals">
        <tbody>
          {appraisals?.figures.map((f) => {
            const r = a[f.id];
            const on100 = f.unit === "score 0-100";
            return (
              <tr key={f.id}>
                <td>{f.label}</td>
                <td className="viz">{on100 && r ? <Interval f={r} /> : null}</td>
                <td className="num">{fmt(r?.value ?? null)} <span className="unit">{f.unit}</span></td>
                <td className="period">{r?.period ?? ""}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="muted small">
        Still to come, each once its terms allow: UNDP HDI, Transparency International CPI, V-Dem, IMF, INFORM,
        ND-GAIN, Fragile States Index, Global Peace Index, Ibrahim Index.
      </p>
    </div>
  );
}
