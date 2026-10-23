// "What the map shows" (the owner, 2026-10-23): a popup to choose the Stability map's measure. The highlighted choices
// first (stabilityMap.HIGHLIGHTS), then everything, in the order of the indicator files: general stability, the eight
// pillars, and each pillar's indicators under its file's name, so the reader knows where each sits.

import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import type { StabilityDoc } from "./data";
import { HIGHLIGHTS, measureLabel, menu, type StabilityMeasure } from "./stabilityMap";

interface Props {
  stability: StabilityDoc;
  value: StabilityMeasure;
  onChange: (m: StabilityMeasure) => void;
  onClose: () => void;
}

export default function StabilityMenu({ stability, value, onChange, onClose }: Props) {
  const dialog = useRef<HTMLDivElement>(null);
  useEffect(() => {
    dialog.current?.querySelector<HTMLButtonElement>("button.on, button")?.focus();
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", esc);
    return () => document.removeEventListener("keydown", esc);
  }, [onClose]);
  const choose = (m: StabilityMeasure) => { onChange(m); onClose(); };
  const option = (m: StabilityMeasure, short = false) => (
    <button key={m} className={m === value ? "measure-option on" : "measure-option"} aria-pressed={m === value}
      onClick={() => choose(m)} title={measureLabel(stability, m)}>
      {short && m.startsWith("indicator:") ? `${stability.indicators[m.slice(10)]?.display_name.split(",")[0]}`
        : measureLabel(stability, m)}
    </button>
  );
  const highlights = HIGHLIGHTS.filter((m) => m === "composite" || m.startsWith("pillar:") ? true
    : !!stability.indicators[m.slice(10)]);

  // drawn at the page's top level: inside the legend's glass (backdrop-filter) a fixed overlay would be clipped to it
  return createPortal(
    <div className="measure-scrim" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="glass measure-dialog" role="dialog" aria-modal="true" aria-label="What the map shows" ref={dialog}>
        <div className="measure-head">
          <h2>What the map shows</h2>
          <button className="close" aria-label="Close" onClick={onClose}>×</button>
        </div>
        <div className="panel-kicker">Highlighted</div>
        <div className="measure-chips">{highlights.map((m) => option(m, true))}</div>
        <div className="measure-all">
          {menu(stability).map((s) => (
            <section key={s.title}>
              <div className="measure-section">
                {s.title}{s.path && <span className="muted small"> · {s.path}</span>}
              </div>
              <div className="measure-list">{s.items.map((m) => option(m))}</div>
            </section>
          ))}
        </div>
        <p className="muted small">Every state is coloured by fifths of the member states with a value; the composite
          keeps its published classes. An indicator is shown by its ASI score (0 to 100, higher more stable), or as
          published where it is only shown, not scored.</p>
      </div>
    </div>,
    document.body,
  );
}
