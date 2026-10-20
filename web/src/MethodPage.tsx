// How the index is built: the justification page, opened from the link at the bottom of the site. Every figure on
// it comes from method.json (05_web.py), which reads the panel, the registry and the frozen rules; nothing here
// computes a number.

import { useEffect, useState } from "react";
import { load, type MethodDoc } from "./data";

const pct = (x: number) => `${(x * 100).toFixed(1)}%`;
const whole = (x: number) => `${Math.round(x * 100)}%`;

const DIRECTION: Record<string, string> = { positive: "higher is more stable", negative: "higher is less stable" };
const BLEND: Record<string, string> = { geometric: "the geometric mean", pca: "PCA weights", entropy: "entropy weights" };

export default function MethodPage({ onClose }: { onClose: () => void }) {
  const [m, setM] = useState<MethodDoc | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { load<MethodDoc>("data/method.json").then(setM).catch((e) => setError(String(e))); }, []);
  useEffect(() => {
    const esc = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);

  return (
    <div className="method" role="dialog" aria-modal="true" aria-label="How the index is built">
      <div className="glass method-sheet">
        <div className="panel-head">
          <div>
            <div className="panel-kicker">African Stability Index · edition 2</div>
            <h2>How the index is built</h2>
          </div>
          <button className="close" onClick={onClose} aria-label="Close">×</button>
        </div>
        {error && <p>Could not load the method: {error}</p>}
        {!m && !error && <p className="muted">Loading…</p>}
        {m && (
          <div className="method-body">
            <p>
              The index turns {m.n_scored} published indicators for the {m.n_states} African Union states into one
              score from 0 (least stable) to 100 (most stable), and says how sure we can be of it. No figure is
              invented: every value comes from a publisher (the World Bank's WDI and WGI, Uppsala's UCDP), and the
              index only cleans, rescales and averages them, by rules written down before the numbers were seen.
              Another {m.n_descriptive} indicators are shown beside them but not scored.
            </p>

            <h3>The steps</h3>
            <ol className="steps">
              <li><b>One value per state, indicator and year.</b> A missing year may carry the last real value forward
                for up to {m.rules.carry_forward_years} years; after that it stays empty. A gap is never filled with a
                regional average: the states that report least are often the least stable, and an average would
                flatter them. The year shown, {m.reference_year}, is the latest in which at least{" "}
                {whole(m.rules.reference_coverage)} of states can be scored.</li>
              <li><b>Admission.</b> An indicator is scored only if at least {m.rules.admission_floor} of the{" "}
                {m.n_states} states have a real value (the Ibrahim Index's rule); below that it is shown, not scored.</li>
              <li><b>Logs for skewed indicators.</b> When an indicator's skew is significant (z above 1.96), it is
                logged first, so a few extreme states do not flatten everyone else.</li>
              <li><b>Outliers.</b> A value more than {m.rules.outlier_sd} trimmed standard deviations from the trimmed
                mean is pulled in to {m.rules.outlier_replace_sd}. For counts that are mostly zero, such as deaths in
                conflict, the test compares violent years with other violent years, so only true extremes are
                capped.</li>
              <li><b>Scaling.</b> Each indicator becomes 0 to 100 between two fixed goalposts (the lowest and highest
                observed values, or natural bounds such as 0 to 100%), turned so that higher always means more stable.
                The goalposts are frozen, so new data never rewrites old scores.</li>
              <li><b>Pillars.</b> Indicators sit in {m.pillars.length} pillars, each the average of its indicators.
                Indicators that largely duplicate one another share one place in that average (below). A pillar
                too thinly measured that year is left out: under {whole(m.rules.thin_at)} of its indicators measured
                that year, or more than {whole(m.rules.max_imputed)} of its values carried forward from earlier
                years.</li>
              <li><b>The headline.</b> The equal-weight average of the pillars that entered; at least{" "}
                {m.rules.min_pillars} must. Other blends are computed only as checks:{" "}
                {Object.entries(m.method_roles).filter(([, r]) => r !== "headline")
                  .map(([k, r]) => `${BLEND[k] ?? k} (${r})`).join(", ")}.</li>
              <li><b>How sure.</b> The headline is the average of a few pillar scores, so it has a{" "}
                {whole(m.rules.interval_level)} interval. Two states differ only when the gap between them is
                significant, which gives each state a band of ranks it could hold, and tiers of states the data cannot
                separate.</li>
            </ol>

            <h3>The pillars and their indicators</h3>
            <p className="muted small">The weight is each indicator's share of the headline when every pillar is
              measured. Indicators marked ⧉ share one place in their pillar with the others of their group.</p>
            {m.pillars.map((p) => {
              const scored = p.indicators.filter((i) => i.role === "scoring");
              const shown = p.indicators.filter((i) => i.role !== "scoring");
              return (
                <details key={p.id} className="method-pillar">
                  <summary><b>{p.id}</b> · {p.name} <span className="muted small">({scored.length} scored
                    {shown.length ? `, ${shown.length} shown` : ""})</span></summary>
                  <table className="rows">
                    <thead><tr><th>Indicator</th><th>Source</th><th>Direction</th><th className="num">Weight</th></tr></thead>
                    <tbody>
                      {scored.map((i) => (
                        <tr key={i.id}>
                          <td>{i.cluster ? "⧉ " : ""}{i.name}{i.log ? <span className="tag">logged</span> : null}</td>
                          <td>{i.database.toUpperCase()}</td>
                          <td className="small">{DIRECTION[i.polarity] ?? i.polarity}</td>
                          <td className="num">{i.weight === null ? "—" : pct(i.weight)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {shown.length > 0 && (
                    <p className="muted small">Shown, not scored: {shown.map((i) => i.name).join("; ")}.</p>
                  )}
                </details>
              );
            })}

            <h3>Indicators that share a weight</h3>
            <p>Two indicators of one pillar share one place when, after taking out what both owe to a country's
              income (log GDP per capita), their correlation is still at least {m.rules.overlap_bar}: more than half
              of what they say is the same. Measured at {m.rules.overlap_year} and frozen.</p>
            <ul className="small">
              {m.clusters.map((c) => (
                <li key={c.slot}><b>{c.slot.split(":")[0]}</b>, sharing one place
                  <span className="muted"> (partial correlations {c.pairs.map((q) => q.partial_r.toFixed(2))
                    .join(", ")})</span>
                  <ul>{c.members.map((n) => <li key={n}>{n}</li>)}</ul>
                </li>
              ))}
            </ul>
            <p className="muted small">A negative correlation means the two move in opposite directions, as life
              expectancy and child mortality do; the overlap is the same.</p>
            <p className="muted small">So no single source dominates: the World Bank's governance indicators carry{" "}
              {pct(m.wgi_share)} of the headline.</p>

            <h3>How sure we can be</h3>
            <ul className="small">
              <li><b>Interval:</b> {m.uncertainty.interval}. The median state's standard error is {m.se_median.toFixed(2)}{" "}
                points.</li>
              <li><b>Bands:</b> {m.uncertainty.bands}. At {m.reference_year} the median band is{" "}
                {m.band_median_width.toFixed(0)} places wide.</li>
              <li><b>Tiers:</b> {m.uncertainty.tiers}. At {m.reference_year}: {m.tiers.length} tiers of{" "}
                {m.tiers.join(", ")} states.</li>
            </ul>
            <p>That is why the site shows tiers and bands, not a single rank: the data separate a handful of groups,
              not {m.n_ranked} exact places.</p>

            <h3>Is it robust?</h3>
            <ul className="small">
              <li>Rankings under other blends agree with the headline's (Spearman's rho):{" "}
                {Object.entries(m.robustness.agreement).map(([k, v]) => `${BLEND[k] ?? k} ${v.toFixed(3)}`).join(", ")}.</li>
              <li>The worst defensible weighting of the pillars still gives {m.robustness.worst_weighting.toFixed(3)}:
                "{m.robustness.verdict}".</li>
              <li>Using only directly measured values gives {m.robustness.measured_only.toFixed(3)}.</li>
            </ul>

            <h3>What it does not do</h3>
            <ul className="small">
              <li>It never fills a gap with a guess, and never ranks states it cannot separate.</li>
              <li>It never rescales or blends other institutions' indices: those are shown as their publishers print
                them.</li>
              <li>Every published file is rebuilt from the inputs and recomputed by a second, independent program before
                release.</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
