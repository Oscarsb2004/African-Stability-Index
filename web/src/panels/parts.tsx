// Pieces every section panel shares: a headline tile, and a section's figures as a table.

import { fmt, type Figure, type SectionSpec } from "../data";

export function Tile({ label, figure, unit, sub }: { label: string; figure?: Figure; unit: string; sub?: string }) {
  return (
    <div className="tile">
      <div className="tile-label">{label}</div>
      <div className="tile-value">{fmt(figure?.value ?? null, unit)}</div>
      <div className="tile-sub">{sub ?? (figure?.period ? figure.period : "not published")}</div>
    </div>
  );
}

export function Rows({ section, figures, open = false }: { section: SectionSpec; figures: Record<string, Figure>;
  open?: boolean }) {
  return (
    <details className="block" open={open}>
      <summary><span>{section.title}</span><span className="muted small">{section.about}</span></summary>
      <table className="rows">
        <tbody>
          {section.figures.filter((f) => f.shell !== "trend").map((f) => {
            const r = figures[f.id];
            return (
              <tr key={f.id}>
                <td>{f.label}{f.derived && <span className="tag" title={`Computed by the ${f.shell} shell`}>derived</span>}</td>
                <td className="num">{f.unbound ? <span className="muted" title={f.unbound}>not yet</span>
                  : r?.value == null ? <span className="muted">—</span>
                  : <>{fmt(r.value, f.unit)} <span className="unit">{f.unit.startsWith("%") ? f.unit.slice(1)
                    : f.unit === "current US$" ? "" : f.unit}</span></>}</td>
                <td className="period">{r?.period ?? ""}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </details>
  );
}

export function trend(f?: Figure) {
  return { periods: f?.periods ?? [], values: (f?.values ?? []) as number[] };
}
