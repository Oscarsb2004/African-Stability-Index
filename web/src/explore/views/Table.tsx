// The numbers behind every view: each item at the chosen year and ten years before; for a group, how many members
// have a value, their range and the interval of their mean; for a group shown as its members, every member.

import type { AverageHow, Series } from "../model";
import { at } from "../model";
import { num, type Resolved, valueAt } from "../resolve";
import type { GroupAverage } from "../stats";

interface Row { key: string; label: string; sub: string; colour: string | null; now: number | null;
  then: number | null; group: GroupAverage | null }

export default function Table({ rs, s, year, how, weights, names }: {
  rs: Resolved[]; s: Series | undefined; year: number; how: AverageHow; weights?: Series; names: Record<string, string>;
}) {
  if (!rs.length) return <p className="muted empty">Add a state or a group to begin.</p>;
  const before = year - 10;
  const rows: Row[] = rs.flatMap((r): Row[] => r.colour === null
    ? r.members.map((m) => ({ key: `${r.key}:${m}`, label: `${names[m] ?? m}`, sub: r.group?.name ?? "", colour: null,
      now: at(s, m, year), then: at(s, m, before), group: null }))
    : [{ key: r.key, label: r.label, sub: "", colour: r.colour, now: valueAt(r, s, year, how, weights).value,
      then: valueAt(r, s, before, how, weights).value, group: r.item.t === "g" ? valueAt(r, s, year, how, weights) : null }]);
  return (
    <div className="table-wrap">
      <table className="rows data-table">
        <thead>
          <tr><th></th><th className="num">{before}</th><th className="num">{year}</th><th className="num">Change</th>
            <th className="num">Members with a value</th><th className="num">Range</th><th className="num">95% interval</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key}>
              <td>{r.colour && <span className="swatch" style={{ background: r.colour }} />}{r.label}
                {r.sub && <span className="muted small"> · {r.sub}</span>}</td>
              <td className="num">{num(r.then)}</td>
              <td className="num">{num(r.now)}</td>
              <td className="num">{r.now !== null && r.then !== null ? num(r.now - r.then) : "—"}</td>
              <td className="num">{r.group ? `${r.group.n} of ${r.group.of}` : ""}</td>
              <td className="num">{r.group && r.group.min !== null ? `${num(r.group.min)} to ${num(r.group.max)}` : ""}</td>
              <td className="num">{r.group?.ci ? `${num(r.group.ci[0])} to ${num(r.group.ci[1])}` : ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
