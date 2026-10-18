// The map: satellite imagery on a globe, Natural Earth borders, and countries that answer hover and click.
// Hover shows the name only; nothing lights up. A chosen country gets a faint tint so the eye can find it again.
// City labels are HTML markers, so the map needs no glyph server.

import { useEffect, useRef } from "react";
import maplibregl, { type ExpressionSpecification, type GeoJSONSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { asset, people, rampColour, type MetaDoc, type Section, type StabilityDoc } from "./data";

interface Props {
  meta: MetaDoc;
  stability: StabilityDoc;
  section: Section;
  selected: string | null;
  showClasses: boolean;
  onSelect: (iso3: string | null) => void;
}

interface Place {
  name: string;
  iso3: string;
  capital: boolean;
  population: number;
  min_zoom: number;
}

const AFRICA: [number, number] = [19, 3];

// Imagery (P62): Esri World Imagery through ArcGIS Location Platform when a key is set: sub-metre in many cities,
// zoom to 19. Without a key, EOX's open 10 m mosaic. The key lives in web/.env.local as VITE_ESRI_KEY, never in git;
// it should be restricted to the site's addresses in the ArcGIS dashboard. Esri requires "Powered by Esri" and the
// service's own data credits, always visible (developers.arcgis.com, Esri and data attribution, read 2026-10-18).
const ESRI = "https://static-map-tiles-api.arcgis.com/arcgis/rest/services/static-basemap-tiles-service/v1/arcgis/imagery";
const ESRI_KEY = import.meta.env.VITE_ESRI_KEY as string | undefined;

export default function MapView({ meta, stability, section, selected, showClasses, onSelect }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const tip = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markers = useRef<maplibregl.Marker[]>([]);
  const places = useRef<{ p: Place; at: [number, number] }[]>([]);
  const sectionRef = useRef(section);
  const redraw = useRef<() => void>(() => {});
  const selectRef = useRef(onSelect);
  selectRef.current = onSelect;

  // ── build once ──────────────────────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!box.current) return;
    const m = new maplibregl.Map({
      container: box.current,
      center: AFRICA,
      zoom: 2.6,
      maxZoom: ESRI_KEY ? 19 : meta.imagery.max_zoom + 1,
      attributionControl: false,
      style: {
        version: 8,
        projection: { type: "globe" },
        sky: { "atmosphere-blend": ["interpolate", ["linear"], ["zoom"], 0, 1, 5, 1, 7, 0] },
        sources: {
          imagery: ESRI_KEY ? {
            type: "raster", tiles: [`${ESRI}/static/tile/{z}/{y}/{x}?token=${ESRI_KEY}`], tileSize: 512, maxzoom: 19,
            attribution: 'Powered by <a href="https://www.esri.com" target="_blank" rel="noreferrer">Esri</a>',
          } : {
            type: "raster", tiles: [meta.imagery.tiles], tileSize: 256, maxzoom: meta.imagery.max_zoom,
            attribution: `<a href="https://cloudless.eox.at" target="_blank" rel="noreferrer">${meta.imagery.attribution}</a>`,
          },
          countries: { type: "geojson", data: asset("geo/countries.json"), promoteId: "iso3" },
          borders: {
            type: "geojson", data: asset("geo/borders.json"),
            attribution: '<a href="https://www.naturalearthdata.com" target="_blank" rel="noreferrer">Natural Earth</a>',
          },
        },
        layers: [
          { id: "space", type: "background", paint: { "background-color": "#05070d" } },
          { id: "imagery", type: "raster", source: "imagery", paint: { "raster-fade-duration": 200 } },
          {
            id: "classes", type: "fill", source: "countries",
            paint: { "fill-color": "#000000", "fill-opacity": 0 },
          },
          {
            id: "chosen", type: "fill", source: "countries",
            paint: {
              "fill-color": "#ffffff",
              "fill-opacity": ["case", ["boolean", ["feature-state", "chosen"], false], 0.14, 0],
            },
          },
          {
            id: "borders", type: "line", source: "borders", filter: ["!", ["get", "dashed"]],
            paint: {
              "line-color": "#f4f1ea", "line-opacity": 0.75,
              "line-width": ["interpolate", ["linear"], ["zoom"], 2, 0.6, 6, 1.2, 10, 2],
            },
          },
          {
            id: "borders-disputed", type: "line", source: "borders", filter: ["get", "dashed"],
            paint: {
              "line-color": "#f4f1ea", "line-opacity": 0.75, "line-dasharray": [3, 3],
              "line-width": ["interpolate", ["linear"], ["zoom"], 2, 0.6, 6, 1.2, 10, 2],
            },
          },
        ],
      },
    });
    m.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");
    const credit = (sources?: string) => m.addControl(new maplibregl.AttributionControl(
      sources ? { customAttribution: `Sources: ${sources}` } : {}), "bottom-right");
    if (ESRI_KEY) {
      fetch(`${ESRI}/static?token=${ESRI_KEY}`).then((r) => r.json())
        .then((d) => credit(d.copyrightText), () => credit("Esri"));
    } else credit();
    m.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

    m.on("mousemove", "classes", (e) => {
      const f = e.features?.[0];
      if (!f || !tip.current) return;
      m.getCanvas().style.cursor = f.properties.member ? "pointer" : "default";
      tip.current.textContent = f.properties.name;
      tip.current.style.transform = `translate(${e.point.x + 14}px, ${e.point.y + 14}px)`;
      tip.current.style.opacity = "1";
    });
    m.on("mouseleave", "classes", () => {
      m.getCanvas().style.cursor = "";
      if (tip.current) tip.current.style.opacity = "0";
    });
    m.on("click", (e) => {
      const f = m.queryRenderedFeatures(e.point, { layers: ["classes"] })[0];
      selectRef.current(f && f.properties.member ? String(f.properties.iso3) : null);
    });

    fetch(asset("geo/places.json")).then((r) => r.json()).then((g) => {
      places.current = g.features.map((f: { properties: Place; geometry: { coordinates: [number, number] } }) =>
        ({ p: f.properties, at: f.geometry.coordinates }));
      drawPlaces();
    });
    m.on("moveend", drawPlaces);
    map.current = m;
    if (import.meta.env.DEV) (window as unknown as { asiMap: maplibregl.Map }).asiMap = m;

    function drawPlaces() {
      markers.current.forEach((mk) => mk.remove());
      markers.current = [];
      const zoom = m.getZoom();
      const bounds = m.getBounds();
      const all = sectionRef.current === "infrastructure";
      const { clientWidth: width, clientHeight: height } = m.getCanvas();
      // capitals from the start; every other city once the map is zoomed to the level Natural Earth gives it.
      // places.json is ordered capitals first, then by population, so a label that would overlap one already
      // placed is the less important one and is skipped.
      const placed: number[][] = [];
      const shown = [];
      for (const c of places.current) {
        const { p, at } = c;
        if (!(p.capital ? zoom >= 2 : all && zoom >= p.min_zoom - 1) || !bounds.contains(at)) continue;
        const pt = m.project(at);
        if (pt.x < 0 || pt.y < 0 || pt.x > width || pt.y > height) continue;
        const box = [pt.x - 5, pt.y - 9, pt.x + 14 + p.name.length * (p.capital ? 7 : 6.2), pt.y + 9];
        if (placed.some((b) => box[0] < b[2] && box[2] > b[0] && box[1] < b[3] && box[3] > b[1])) continue;
        placed.push(box);
        shown.push(c);
        if (shown.length >= 120) break;
      }
      for (const { p, at } of shown) {
        const el = document.createElement("div");
        el.className = p.capital ? "place capital" : "place";
        const dot = document.createElement("span");
        dot.className = "dot";
        const label = document.createElement("span");
        label.className = "label";
        label.textContent = p.name;
        el.append(dot, label);
        el.title = `${p.name}${p.capital ? " (capital)" : ""}: ${people(p.population)} people (Natural Earth)`;
        markers.current.push(new maplibregl.Marker({ element: el, anchor: "left" }).setLngLat(at).addTo(m));
      }
    }
    redraw.current = drawPlaces;

    return () => m.remove();
  }, [meta]);

  // ── the stability classes, shown only in the Stability section ─────────────────────────────────────────
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    const apply = () => {
      const breaks = stability.classes.breaks;
      const colour: ExpressionSpecification = ["match", ["get", "iso3"],
        ...Object.entries(stability.countries).flatMap(([iso3, c]) => [iso3, rampColour(c.composite.score, breaks)]),
        "#000000"] as unknown as ExpressionSpecification;
      m.setPaintProperty("classes", "fill-color", colour);
      m.setPaintProperty("classes", "fill-opacity",
        section === "stability" && showClasses ? ["case", ["get", "member"], 0.55, 0] : 0);
    };
    if (m.isStyleLoaded()) apply(); else m.once("load", apply);
  }, [section, showClasses, stability]);

  // ── the chosen country: a faint tint, and the map moves it clear of the panel ───────────────────────────
  const previous = useRef<string | null>(null);
  const extents = useRef<Record<string, [number, number, number, number]>>({});
  useEffect(() => {
    fetch(asset("geo/countries.json")).then((r) => r.json()).then((g) => {
      for (const f of g.features as { properties: { iso3: string }; geometry: { coordinates: unknown } }[]) {
        const e = extents.current[f.properties.iso3] ?? [180, 90, -180, -90];
        const walk = (c: unknown): void => {
          if (typeof (c as number[])[0] === "number") {
            const [x, y] = c as number[];
            e[0] = Math.min(e[0], x); e[1] = Math.min(e[1], y); e[2] = Math.max(e[2], x); e[3] = Math.max(e[3], y);
          } else (c as unknown[]).forEach(walk);
        };
        walk(f.geometry.coordinates);
        extents.current[f.properties.iso3] = e;
      }
    });
  }, []);
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    const apply = () => {
      if (!(m.getSource("countries") as GeoJSONSource | undefined)) return;
      if (previous.current) m.setFeatureState({ source: "countries", id: previous.current }, { chosen: false });
      if (selected) m.setFeatureState({ source: "countries", id: selected }, { chosen: true });
      previous.current = selected;
      const e = selected ? extents.current[selected] : undefined;
      if (e) {
        const phone = window.innerWidth < 760;
        m.fitBounds([[e[0], e[1]], [e[2], e[3]]], {
          padding: phone ? { top: 120, bottom: window.innerHeight * 0.6, left: 30, right: 30 }
            : { top: 90, bottom: 60, left: 60, right: 500 },
          maxZoom: 6.5, duration: 1400,
        });
      }
    };
    if (m.isStyleLoaded()) apply(); else m.once("idle", apply);
  }, [selected]);

  // ── cities follow the section ───────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    sectionRef.current = section;
    redraw.current();
  }, [section]);

  return (
    <div className="map">
      <div ref={box} className="map-canvas" />
      <div ref={tip} className="hover-name" />
    </div>
  );
}
