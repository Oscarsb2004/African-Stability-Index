// The Stability section's grouping picker (the owner, 2026-10-23): optional; hovering or focusing a grouping lists its
// members beside the menu. A list of buttons rather than a <select>, because a native option cannot show anything on
// hover. The groupings are the Data tab's: the regional economic communities, other organisations, and each state's
// categories (explore/model.ts, allGroups).

import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { allGroups, type Group, loadGroups, loadStates } from "./explore/model";
import { memberNames } from "./stabilityMap";

const KINDS: [Group["kind"], string][] = [
  ["rec", "Regional economic communities"], ["organisation", "Organisations"], ["category", "Categories"],
];

interface Props {
  value: string | null;
  names: Record<string, string>;
  onChange: (group: Group | null) => void;
}

export default function GroupPicker({ value, names, onChange }: Props) {
  const [groups, setGroups] = useState<Group[]>([]);
  const [open, setOpen] = useState(false);
  const [peek, setPeek] = useState<Group | null>(null);
  const box = useRef<HTMLDivElement>(null);
  const list = useRef<HTMLDivElement>(null);
  const [at, setAt] = useState<{ top: number; left: number }>({ top: 0, left: 0 });
  useEffect(() => {
    Promise.all([loadGroups(), loadStates()]).then(([g, s]) => setGroups(allGroups(g, s, []))).catch(() => setGroups([]));
  }, []);
  useEffect(() => {  // closes on a click elsewhere, or on Escape
    if (!open) return;
    const away = (e: MouseEvent) => {
      const t = e.target as Node;
      if (!box.current?.contains(t) && !list.current?.contains(t)) setOpen(false);
    };
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", away);
    document.addEventListener("keydown", esc);
    return () => { document.removeEventListener("mousedown", away); document.removeEventListener("keydown", esc); };
  }, [open]);
  const byKind = useMemo(() => KINDS.map(([k, title]) => [title, groups.filter((g) => g.kind === k)] as const)
    .filter(([, gs]) => gs.length), [groups]);
  const chosen = groups.find((g) => g.id === value) ?? null;
  const pick = (g: Group | null) => { onChange(g); setOpen(false); setPeek(null); };

  return (
    <div className="group-picker" ref={box}>
      <button className="pick" aria-haspopup="listbox" aria-expanded={open} onClick={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        setAt({ top: r.bottom + 6, left: r.left });
        setOpen(!open);
      }}>
        {chosen ? `${chosen.name} (${chosen.members.length})` : "Choose a grouping (optional)…"}
      </button>
      {/* drawn at the page's top level, so no glass panel clips it or sits above it */}
      {open && createPortal(
        <div className="glass group-menu" role="listbox" aria-label="Groupings" ref={list}
          style={{ top: at.top, left: at.left }}>
          <div className="group-list">
            <button role="option" aria-selected={!value} className="group-option" onClick={() => pick(null)}
              onMouseEnter={() => setPeek(null)} onFocus={() => setPeek(null)}>All 54 member states</button>
            {byKind.map(([title, gs]) => (
              <div key={title}>
                <div className="panel-kicker">{title}</div>
                {gs.map((g) => (
                  <button key={g.id} role="option" aria-selected={g.id === value}
                    className={g.id === value ? "group-option on" : "group-option"}
                    onClick={() => pick(g)} onMouseEnter={() => setPeek(g)} onFocus={() => setPeek(g)}>
                    {g.name} <span className="muted small">{g.members.length}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>
          <div className="group-members" aria-live="polite">
            {peek ? (
              <>
                <div className="group-members-title">{peek.name}</div>
                <div className="small">{memberNames(peek, names)}</div>
                {peek.source && <div className="muted small">Source: {peek.source}</div>}
              </>
            ) : <div className="muted small">Hover over a grouping to see its members.</div>}
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}
