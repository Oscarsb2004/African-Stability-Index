// Observable Plot (ISC) in React: the figure is rebuilt when its options change, at the width of its container.
// The colours are the site's: text in the ink tokens, grids recessive, the background the glass behind it.

import * as Plot from "@observablehq/plot";
import { useEffect, useRef, useState } from "react";

export const INK = "#eef0f3", INK2 = "#b9bec7", INK3 = "#8a909a", GRID = "rgba(255,255,255,0.12)", CONTEXT = "#6f7682";

export default function PlotFigure({ options, label }: { options: (width: number) => Plot.PlotOptions; label: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(560);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setWidth(Math.max(200, Math.floor(e.contentRect.width))));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const o = options(width);
    const fig = Plot.plot({ width, style: { background: "transparent", color: INK2, fontSize: "11px",
      fontFamily: "inherit", overflow: "visible" }, ...o });
    fig.setAttribute("aria-label", label);
    el.replaceChildren(fig);
    return () => fig.remove();
  }, [options, width, label]);
  return <div className="plot" ref={ref} />;
}
