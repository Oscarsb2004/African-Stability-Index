// "What the map shows" (the owner, 2026-10-23): a popup to choose the Stability map's measure. The highlighted choices
// first (stabilityMap.HIGHLIGHTS), then everything, in the order of the indicator files: general stability, the
// reader's own indices, the eight pillars, and each pillar's indicators under its file's name, so the reader knows
// where each sits. "Build your own index" opens the builder in the same popup (IndexBuilder.tsx).

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { CustomIndex } from "./customIndex";
import type { StabilityDoc } from "./data";
import IndexBuilder from "./IndexBuilder";
import { HIGHLIGHTS, measureLabel, menu, type StabilityMeasure } from "./stabilityMap";

interface Props {
  stability: StabilityDoc;
  value: StabilityMeasure;
  onChange: (m: StabilityMeasure) => void;
  onClose: () => void;
  indices: CustomIndex[];                     // the reader's own, kept in this browser
  onSaveIndex: (ix: CustomIndex) => void;
  onDeleteIndex: (id: string) => void;
  shareLink: (ix: CustomIndex) => string;
}

export default function StabilityMenu({ stability, value, onChange, onClose, indices, onSaveIndex, onDeleteIndex,
  shareLink }: Props) {
  const dialog = useRef<HTMLDivElement>(null);
  const [building, setBuilding] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  useEffect(() => {
    dialog.current?.querySelector<HTMLButtonElement>("button.on, button")?.focus();
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", esc);
    return () => document.removeEventListener("keydown", esc);
  }, [onClose]);
  const choose = (m: StabilityMeasure) => { onChange(m); onClose(); };
  const label = (m: StabilityMeasure) => m.startsWith("custom:")
    ? indices.find((ix) => `custom:${ix.id}` === m)?.name ?? m : measureLabel(stability, m);
  const option = (m: StabilityMeasure, short = false) => (
    <button key={m} className={m === value ? "measure-option on" : "measure-option"} aria-pressed={m === value}
      onClick={() => choose(m)} title={label(m)}>
      {short && m.startsWith("indicator:") ? `${stability.indicators[m.slice(10)]?.display_name.split(",")[0]}`
        : label(m)}
    </button>
  );
  const highlights = HIGHLIGHTS.filter((m) => m === "composite" || m.startsWith("pillar:") ? true
    : !!stability.indicators[m.slice(10)]);
  const share = (ix: CustomIndex) => {
    const url = shareLink(ix);
    navigator.clipboard?.writeText(url).then(() => setCopied(ix.id), () => setCopied(null));
  };

  // drawn at the page's top level: inside the legend's glass (backdrop-filter) a fixed overlay would be clipped to it
  return createPortal(
    <div className="measure-scrim" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="glass measure-dialog" role="dialog" aria-modal="true" aria-label="What the map shows" ref={dialog}>
        <div className="measure-head">
          <h2>What the map shows</h2>
          <button className="close" aria-label="Close" onClick={onClose}>×</button>
        </div>
        {building ? (
          <IndexBuilder year={stability.reference_year} onCancel={() => setBuilding(false)}
            onSave={(ix) => { onSaveIndex(ix); choose(`custom:${ix.id}`); }} />
        ) : (
          <>
            <div className="panel-kicker">Highlighted</div>
            <div className="measure-chips">
              {highlights.map((m) => option(m, true))}
              <button className="measure-option build" onClick={() => setBuilding(true)}>＋ Build your own index</button>
            </div>
            <div className="measure-all">
              {menu(stability, indices.map((ix) => `custom:${ix.id}`)).map((s) => (
                <section key={s.title}>
                  <div className="measure-section">
                    {s.title}{s.path && <span className="muted small"> · {s.path}</span>}
                  </div>
                  <div className="measure-list">
                    {s.items.map((m) => !m.startsWith("custom:") ? option(m) : (
                      <div key={m} className="custom-entry">
                        {option(m)}
                        <span className="custom-actions">
                          <button className="linkish small" onClick={() => share(indices.find((ix) => `custom:${ix.id}` === m)!)}>
                            {copied && m === `custom:${copied}` ? "link copied" : "share"}</button>
                          <button className="linkish small" onClick={() => onDeleteIndex(m.slice(7))}>delete</button>
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              ))}
            </div>
            <p className="muted small">Every state is coloured by fifths of the member states with a value; the composite
              keeps its published classes. An indicator is shown by its ASI score (0 to 100, higher more stable), or as
              published where it is only shown, not scored. Your own indices are kept in this browser only.</p>
          </>
        )}
      </div>
    </div>,
    document.body,
  );
}
