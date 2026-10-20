// The measure search: every series in the catalogue, found by any words of its label, code, topic or source. An
// empty search offers a short list to start from.

import { useMemo, useRef, useState } from "react";
import type { Catalogue, Measure } from "./model";

const STARTERS = ["asi/headline", "wdi/NY.GDP.PCAP.PP.CD", "wdi/NY.GDP.MKTP.KD.ZG", "wdi/FP.CPI.TOTL.ZG",
  "weo/NGDP_RPCH", "weo/GGXWDG_NGDP", "hdr/hdi", "cpi/cpi_score", "wgi/GOV_WGI_CC.SC", "wgi/GOV_WGI_PV.SC",
  "ucdp/sb_total_deaths_best", "wdi/SP.DYN.LE00.IN", "wdi/EG.ELC.ACCS.ZS", "wdi/SP.URB.GROW", "glottolog/languages"];
const DS: Record<string, string> = { asi: "ASI", wdi: "WDI", wgi: "WGI", hdr: "UNDP HDR", cpi: "TI CPI",
  weo: "IMF WEO", ucdp: "UCDP", glottolog: "Glottolog" };

export function shortSource(ds: string): string {
  return DS[ds] ?? ds;
}

export default function MeasurePicker({ catalogue, value, onPick, label = "Measure" }: {
  catalogue: Catalogue; value: string; onPick: (id: string) => void; label?: string;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const byId = useMemo(() => new Map(catalogue.measures.map((m) => [m.id, m])), [catalogue]);
  const current = byId.get(value);
  const found = useMemo(() => {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!words.length) return STARTERS.map((id) => byId.get(id)).filter((m): m is Measure => !!m);
    return catalogue.measures.filter((m) => {
      const hay = `${m.label} ${m.code} ${m.topic} ${shortSource(m.ds)}`.toLowerCase();
      return words.every((w) => hay.includes(w));
    }).slice(0, 80);
  }, [q, catalogue, byId]);
  const pick = (id: string) => { onPick(id); setOpen(false); setQ(""); };
  return (
    <div className="picker" ref={box} onBlur={(e) => !box.current?.contains(e.relatedTarget) && setOpen(false)}>
      <span className="picker-label small muted">{label}</span>
      <input className="pick picker-input" value={open ? q : current ? current.label : value} aria-label={`${label}: search`}
        placeholder="Search 1,700+ series: growth, literacy, corruption…" onFocus={() => setOpen(true)}
        onChange={(e) => { setQ(e.target.value); setOpen(true); }}
        onKeyDown={(e) => { if (e.key === "Escape") setOpen(false); if (e.key === "Enter" && found[0]) pick(found[0].id); }} />
      {open && (
        <ul className="picker-list glass" role="listbox">
          {!q && <li className="muted small picker-head">A few to start with; type to search every series</li>}
          {found.map((m) => (
            <li key={m.id}>
              <button role="option" aria-selected={m.id === value} onMouseDown={(e) => e.preventDefault()}
                onClick={() => pick(m.id)}>
                <span>{m.label}</span>
                <span className="muted small"> {shortSource(m.ds)} · {m.topic} · {m.n} states · {m.y[0]}–{m.y[1]}</span>
              </button>
            </li>
          ))}
          {q && !found.length && <li className="muted small picker-head">Nothing matches every word.</li>}
        </ul>
      )}
    </div>
  );
}
