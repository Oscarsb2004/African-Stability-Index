// The Wonders viewer (P61): one click opened it; swipe, or the arrow keys, move through the photographs; one more
// click, or Escape, closes it. Every photograph shows its author and licence, as Commons asks of reusers.

import { useEffect, useRef, useState } from "react";
import type { Wonder } from "./data";

export default function PhotoViewer({ wonder, onClose }: { wonder: Wonder; onClose: () => void }) {
  const [i, setI] = useState(0);
  const start = useRef<{ x: number; y: number } | null>(null);
  const photos = wonder.photos;
  const n = photos.length;
  const go = (d: number) => setI((k) => (k + d + n) % n);

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowRight") go(1);
      else if (e.key === "ArrowLeft") go(-1);
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  });

  useEffect(() => {  // the next photograph loads while this one is looked at
    if (n > 1) new Image().src = photos[(i + 1) % n].src;
  }, [i, n, photos]);

  if (!n) return null;
  const p = photos[i];
  const up = (e: React.PointerEvent) => {
    const s = start.current;
    start.current = null;
    if (!s) return;
    const dx = e.clientX - s.x, dy = e.clientY - s.y;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) go(dx < 0 ? 1 : -1);  // a swipe moves on
    else if (Math.abs(dx) < 8 && Math.abs(dy) < 8) onClose();                      // a click closes
  };
  return (
    <div className="viewer" role="dialog" aria-modal="true" aria-label={`${wonder.name}, photographs`}>
      <img key={p.src} src={p.src} alt={`${wonder.name}, photograph ${i + 1} of ${n}`} draggable={false}
        onPointerDown={(e) => { start.current = { x: e.clientX, y: e.clientY }; }} onPointerUp={up} />
      {n > 1 && <>
        <button className="viewer-nav prev" onClick={() => go(-1)} aria-label="Previous photograph">‹</button>
        <button className="viewer-nav next" onClick={() => go(1)} aria-label="Next photograph">›</button>
      </>}
      <button className="viewer-close" onClick={onClose} aria-label="Close">×</button>
      <div className="viewer-caption">
        <div className="viewer-title">{wonder.name} <span className="muted">{i + 1} / {n}</span></div>
        <div className="small">
          {p.artist || <a href={p.page} target="_blank" rel="noreferrer">author named on Commons</a>} ·{" "}
          {p.licence_url ? <a href={p.licence_url} target="_blank" rel="noreferrer">{p.licence}</a> : p.licence} ·{" "}
          <a href={p.page} target="_blank" rel="noreferrer">Wikimedia Commons</a>
        </div>
      </div>
    </div>
  );
}
