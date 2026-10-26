// The map: satellite imagery on a globe, Natural Earth borders, and countries that answer hover and click.
// Each state's name is written at its label point at all times (the owner, 2026-10-23); hover repeats it, and nothing
// lights up. A chosen country gets a faint tint so the eye can find it again.
// City labels are HTML markers, so the map needs no glyph server.

import { useEffect, useRef } from "react";
import maplibregl, { type ExpressionSpecification, type GeoJSONSource, type MapGeoJSONFeature } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Protocol } from "pmtiles";
import { asset, loadOnce, people, rampColour, type MetaDoc, type Section, type StabilityDoc, type Wonder } from "./data";
import { activityRows, cardRows, COLOURS, EDGE, parsed, RING, SHAPES, type Activity, type LayersDoc } from "./infra";
import { actorLabel, heading, KIND_COLOURS, linksBounds, linksOf, standing, type Link, type LinksDoc } from "./links";

// The Infrastructure section's line layers are PMTiles archives, read by range requests from the site's own files
// (pmtiles, BSD-3-Clause, its licence read in protomaps/PMTiles on 2026-10-21).
maplibregl.addProtocol("pmtiles", new Protocol().tile);

interface Props {
  meta: MetaDoc;
  stability: StabilityDoc;
  section: Section;
  selected: string | null;
  showClasses: boolean;
  choropleth?: Record<string, string> | null;  // the Data tab's measure, a colour per state
  marked?: string[];  // the Data tab's chosen states
  onSelect: (iso3: string | null) => void;
  wonders: Wonder[] | null;
  onWonder: (w: Wonder) => void;
  infra?: LayersDoc | null;  // the Infrastructure section's catalogue, once loaded
  infraOn?: string[];  // the layers switched on
  cities?: boolean;  // cities and towns are drawn only when switched on
  names?: Record<string, string>;  // each member state's name, for a city's tooltip
  stabilityColours?: Record<string, string> | null;  // the Stability map's measure, a colour per state
  only?: string[] | null;  // a grouping: only its members are coloured
  linksOn?: boolean;  // the links between states are drawn only when switched on
  linkFocus?: string | null;  // a link pointed at in the panel, picked out alone
}

// geo/countries.json, as the map reads it: each state's code, name, Natural Earth label point, rank and abbreviation
interface CountriesGeo {
  features: { properties: { iso3: string; name: string; label?: [number, number]; rank?: number; abbrev?: string };
    geometry: { coordinates: unknown } }[];
}

interface Place {
  name: string;
  iso3: string;
  capital: boolean;
  population: number;
  min_zoom: number;
}
interface PlacesGeo { features: { properties: Place; geometry: { coordinates: [number, number] } }[] }

const AFRICA: [number, number] = [19, 3];

// Imagery (P62): Esri World Imagery through ArcGIS Location Platform when a key is set: sub-metre in many cities,
// zoom to 19. Without a key, EOX's open 10 m mosaic. The key lives in web/.env.local as VITE_ESRI_KEY, never in git;
// it should be restricted to the site's addresses in the ArcGIS dashboard. Esri requires "Powered by Esri" and the
// service's own data credits, always visible (developers.arcgis.com, Esri and data attribution, read 2026-10-18).
const ESRI = "https://static-map-tiles-api.arcgis.com/arcgis/rest/services/static-basemap-tiles-service/v1/arcgis/imagery";
const ESRI_KEY = import.meta.env.VITE_ESRI_KEY as string | undefined;
// each link in its kind's hue (links.ts)
const KIND_PAINT = ["match", ["get", "kind"], ...Object.entries(KIND_COLOURS).flat(), RING] as unknown as
  ExpressionSpecification;
// a link that has ended is drawn faded, faint or in full
const LINK_FAINT: ExpressionSpecification = ["case", ["get", "historical"], 0.3, 0.7];
const LINK_FULL: ExpressionSpecification = ["case", ["get", "historical"], 0.45, 1];
const LINK_LAYERS = ["links-casing", "links", "links-reported", "links-arrows"];

// The chevron that marks a link's direction, from backer to backed: drawn on a canvas in a kind's hue over a light
// casing, one image per kind (no sprite or glyph server needed).
function chevron(colour: string): ImageData {
  const size = 24, c = document.createElement("canvas");
  c.width = c.height = size;
  const g = c.getContext("2d")!;
  g.lineCap = g.lineJoin = "round";
  for (const [style, width] of [[RING, 7], [colour, 3.5]] as const) {
    g.strokeStyle = style;
    g.lineWidth = width;
    g.beginPath();
    g.moveTo(8, 5);
    g.lineTo(16, 12);
    g.lineTo(8, 19);
    g.stroke();
  }
  return g.getImageData(0, 0, size, size);
}

// A country name's width in pixels at a size, from the canvas's text metrics in the label's own font (the weight of
// .country-name, and its letter spacing of 0.02em), so measuring never forces the page's layout. Each is kept.
const metrics = document.createElement("canvas").getContext("2d");
const widths = new Map<string, number>();
let family = "";
function textWidth(el: HTMLElement, text: string, size: number): number {
  const key = `${size}|${text}`;
  let w = widths.get(key);
  if (w === undefined) {
    family ||= getComputedStyle(el).fontFamily;
    if (metrics) metrics.font = `600 ${size}px ${family}`;
    w = (metrics?.measureText(text).width ?? text.length * size * 0.62) + 0.02 * size * text.length;
    widths.set(key, w);
  }
  return w;
}

export default function MapView({ meta, stability, section, selected, showClasses, choropleth, marked = [], onSelect,
  wonders, onWonder, infra = null, infraOn = [], cities = false, names = {},
  stabilityColours = null, only = null, linksOn = false, linkFocus = null }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const tip = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markers = useRef(new Map<number, maplibregl.Marker>());  // the cities shown, by their place in places.json
  const places = useRef<{ p: Place; at: [number, number] }[]>([]);
  // each state's name, its marker, and its rank (lower is more important)
  const labels = useRef<{ name: string; abbrev: string; at: [number, number]; size: number; rank: number;
    marker: maplibregl.Marker; el: HTMLElement; shown?: string }[]>([]);
  const sectionRef = useRef(section);
  const linksDoc = useRef<LinksDoc | null>(null);
  const linksPopup = useRef<maplibregl.Popup | null>(null);
  const linkEnds = useRef<maplibregl.Marker[]>([]);  // the names at a shown link's ends
  const linksOnRef = useRef(linksOn);
  linksOnRef.current = linksOn;
  const focusRef = useRef(linkFocus);
  focusRef.current = linkFocus;
  const selectedRef = useRef(selected);
  selectedRef.current = selected;
  const otherRef = useRef<string | null>(null);  // a non-member state clicked, whose links are shown
  // draws the links the switch, the chosen state and the panel call for; a click on another state opens its cards
  const linksRef = useRef<(at?: maplibregl.LngLat) => void>(() => {});
  const citiesRef = useRef(cities);
  const namesRef = useRef(names);
  namesRef.current = names;
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
          // every other state, thin and grey around Africa; and the links between states (the owner, 2026-10-23)
          world: { type: "geojson", data: asset("geo/world.json") },
          links: { type: "geojson", data: asset("geo/links.json") },
          borders: {
            type: "geojson", data: asset("geo/borders.json"),
            attribution: '<a href="https://www.naturalearthdata.com" target="_blank" rel="noreferrer">Natural Earth</a>',
          },
        },
        layers: [
          { id: "space", type: "background", paint: { "background-color": "#05070d" } },
          { id: "imagery", type: "raster", source: "imagery", paint: { "raster-fade-duration": 200 } },
          { id: "world-fill", type: "fill", source: "world", paint: { "fill-color": "#000000", "fill-opacity": 0 } },
          {
            id: "world-lines", type: "line", source: "world",
            paint: { "line-color": "#c9c7c0", "line-opacity": 0.5,
              "line-width": ["interpolate", ["linear"], ["zoom"], 2, 0.3, 6, 0.7, 10, 1.2] },
          },
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
          // the links between states, only while their switch is on: every link faint, so the reader sees what the
          // record holds; then the chosen state's (or the one pointed at in the panel) in full, a light casing under
          // each line in its kind's hue, solid where its source finds it, dashed where it judges it credible, and
          // faded once it has ended
          {
            id: "links-faint", type: "line", source: "links", layout: { visibility: "none", "line-cap": "round" },
            filter: ["==", ["get", "status"], "confirmed"],
            paint: { "line-color": KIND_PAINT, "line-width": 2, "line-opacity": LINK_FAINT },
          },
          {
            id: "links-faint-reported", type: "line", source: "links", layout: { visibility: "none" },
            filter: ["==", ["get", "status"], "reported"],
            paint: { "line-color": KIND_PAINT, "line-width": 2, "line-opacity": LINK_FAINT,
              "line-dasharray": [2, 1.5] },
          },
          {
            id: "links-casing", type: "line", source: "links", filter: ["==", ["get", "id"], ""],
            layout: { "line-cap": "round" },
            paint: { "line-color": RING, "line-opacity": ["case", ["get", "historical"], 0.25, 0.55], "line-width": 5 },
          },
          {
            id: "links", type: "line", source: "links", filter: ["==", ["get", "id"], ""],
            layout: { "line-cap": "round" },
            paint: { "line-color": KIND_PAINT, "line-width": 3, "line-opacity": LINK_FULL },
          },
          {
            id: "links-reported", type: "line", source: "links", filter: ["==", ["get", "id"], ""],
            paint: { "line-color": KIND_PAINT, "line-width": 3, "line-opacity": LINK_FULL,
              "line-dasharray": [2, 1.5] },
          },
        ],
      },
    });
    // the chevrons along a shown link, pointing from backer to backed
    m.on("load", () => {
      for (const [kind, colour] of Object.entries(KIND_COLOURS)) m.addImage(`chevron-${kind}`, chevron(colour));
      m.addLayer({
        id: "links-arrows", type: "symbol", source: "links", filter: ["==", ["get", "id"], ""],
        layout: { "symbol-placement": "line", "symbol-spacing": 90, "icon-image": ["concat", "chevron-", ["get", "kind"]],
          "icon-size": 0.75, "icon-allow-overlap": true, "icon-ignore-placement": true,
          "icon-rotation-alignment": "map", "icon-keep-upright": false },
        paint: { "icon-opacity": LINK_FULL },
      });
      linksRef.current();  // a state chosen before the map loaded gets its links now
    });
    m.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");
    const credit = (sources?: string) => m.addControl(new maplibregl.AttributionControl(
      sources ? { customAttribution: `Sources: ${sources}` } : {}), "bottom-right");
    if (ESRI_KEY) {
      fetch(`${ESRI}/static?token=${ESRI_KEY}`).then((r) => r.json())
        .then((d) => credit(d.copyrightText), () => credit("Esri"));
    } else credit();
    m.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

    // hover: the state under the pointer, an African one before any other, looked up once a frame however fast the
    // mouse moves. Another state shows a pointer where it has links into Africa.
    let pending: maplibregl.MapMouseEvent | null = null;
    const hide = () => {
      m.getCanvas().style.cursor = "";
      if (tip.current) tip.current.style.opacity = "0";
    };
    const hover = () => {
      const e = pending;
      pending = null;
      if (!e || !tip.current) return;
      if ((e.originalEvent.target as HTMLElement | null)?.closest?.(".place")) return;  // a city label has its own
      if (e.originalEvent.buttons) { hide(); return; }  // the map is being dragged
      const found = m.queryRenderedFeatures(e.point, { layers: ["classes", "world-fill"] });
      const f = found.find((x) => x.layer.id === "classes");
      const w = f ? undefined : found.find((x) => x.layer.id === "world-fill");
      if (!f && !w) { hide(); return; }
      const has = !!w && linksOnRef.current && linksOf(linksDoc.current, String(w.properties.iso3)).length > 0;
      m.getCanvas().style.cursor = f?.properties.member || has ? "pointer" : "default";
      tip.current.textContent = f ? f.properties.name
        : has ? `${w!.properties.name} · its links into Africa on click` : w!.properties.name;
      tip.current.style.transform = `translate(${e.point.x + 14}px, ${e.point.y + 14}px)`;
      tip.current.style.opacity = "1";
    };
    m.on("mousemove", (e) => {
      if (!pending) requestAnimationFrame(hover);
      pending = e;
    });
    m.on("mouseout", () => { pending = null; hide(); });
    loadOnce<LinksDoc>("geo/links.json").then((d) => { linksDoc.current = d; linksRef.current(); },
      () => { linksDoc.current = null; });
    m.on("click", (e) => {
      // a point's card, not the country under it; the hit box is wider than the dot, so a small mark is easy to take
      const near: [maplibregl.PointLike, maplibregl.PointLike] = [[e.point.x - 6, e.point.y - 6], [e.point.x + 6, e.point.y + 6]];
      const point = m.queryRenderedFeatures(near).find((f) => f.layer.id.startsWith("infra-pt-"));
      if (point) { cardRef.current(point, e.lngLat); return; }
      const f = m.queryRenderedFeatures(e.point, { layers: ["classes"] })[0];
      const w = f ? undefined : m.queryRenderedFeatures(e.point, { layers: ["world-fill"] })[0];
      const member = f && f.properties.member ? String(f.properties.iso3) : null;
      const other = w ? String(w.properties.iso3) : null;
      // a member state opens its panel, where its links are listed; another state, which has no panel, shows its
      // links and their cards at the click while the links are switched on
      if (!other || member) selectRef.current(member);
      otherRef.current = member ? null : other;
      linksRef.current(e.lngLat);
    });

    loadOnce<PlacesGeo>("geo/places.json").then((g) => {
      places.current = g.features.map((f) => ({ p: f.properties, at: f.geometry.coordinates }));
      drawPlaces();
    });
    // each state's name at Natural Earth's label point, always: drawn once, it moves with the map; the size follows
    // Natural Earth's label rank, and a small state's name is smaller, never hidden
    loadOnce<CountriesGeo>("geo/countries.json").then((g) => {
      for (const f of g.features) {
        const { name, label, rank = 5, abbrev = name } = f.properties;
        if (!label) continue;
        const size = rank <= 3 ? 13 : rank <= 5 ? 12 : 11;
        const el = document.createElement("div");
        el.className = "country-name";
        el.style.fontSize = `${size}px`;
        el.textContent = name;
        const marker = new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat(label).addTo(m);
        labels.current.push({ name, abbrev, at: label, size, rank, marker, el });
      }
      labels.current.sort((a, b) => a.rank - b.rank);
      drawPlaces();
    });
    m.on("moveend", drawPlaces);
    map.current = m;
    if (import.meta.env.DEV) (window as unknown as { asiMap: maplibregl.Map }).asiMap = m;

    function drawPlaces() {
      const zoom = m.getZoom();
      const bounds = m.getBounds();
      // the countries' names come first, the more important first (Natural Earth's label rank). Below zoom 4 they are
      // drawn a little smaller. Each takes the first free place among: its full name on its point, then a line below or
      // above; Natural Earth's abbreviation in the same three places; else its full name on its point. A name is never
      // hidden or moved off its state, and hover always gives the full name. A city label that would cover a name
      // gives way.
      // Widths come from the canvas's text metrics, cached, so no try forces the page's layout; a label's element is
      // written only when its text, size or place changes.
      const overlaps = (a: number[], b: number[]) => a[0] < b[2] && a[2] > b[0] && a[1] < b[3] && a[3] > b[1];
      const scale = zoom < 3.2 ? 0.8 : zoom < 4.2 ? 0.9 : 1;
      const placed: number[][] = [];
      for (const l of labels.current) {
        const size = Math.round(l.size * scale), h = size * 1.25, pt = m.project(l.at);
        const box = (text: string, dy: number) => {
          const half = (textWidth(l.el, text, size) + 2) / 2;
          return [pt.x - half, pt.y + dy - h / 2, pt.x + half, pt.y + dy + h / 2];
        };
        const tries = [l.name, l.abbrev].flatMap((text) => [0, h, -h].map((dy) => [text, dy] as const));
        const [text, dy] = tries.find(([t, d]) => !placed.some((b) => overlaps(box(t, d), b))) ?? [l.name, 0];
        placed.push(box(text, dy));
        if (l.el.textContent !== text) l.el.textContent = text;
        if (l.shown !== `${size}|${dy}`) {
          l.el.style.fontSize = `${size}px`;
          l.marker.setOffset([0, dy]);
          l.shown = `${size}|${dy}`;
        }
      }
      // only when switched on; the wonders have the map to themselves
      const shown = new Set<number>();
      if (sectionRef.current !== "wonders" && citiesRef.current) {
        const { clientWidth: width, clientHeight: height } = m.getCanvas();
        // capitals from the start; every other city once the map is zoomed to the level Natural Earth gives it.
        // places.json is ordered capitals first, then by population, so a label that would overlap one already
        // placed is the less important one and is skipped.
        for (const [i, { p, at }] of places.current.entries()) {
          if (!(p.capital ? zoom >= 2 : zoom >= p.min_zoom - 1) || !bounds.contains(at)) continue;
          const pt = m.project(at);
          if (pt.x < 0 || pt.y < 0 || pt.x > width || pt.y > height) continue;
          const box = [pt.x - 5, pt.y - 9, pt.x + 14 + p.name.length * (p.capital ? 7 : 6.2), pt.y + 9];
          if (placed.some((b) => overlaps(box, b))) continue;
          placed.push(box);
          shown.add(i);
          if (shown.size >= 120) break;
        }
      }
      // a city still shown keeps its marker; only those that come or go are added or removed
      for (const [i, mk] of markers.current) if (!shown.has(i)) { mk.remove(); markers.current.delete(i); }
      for (const i of shown) {
        if (markers.current.has(i)) continue;
        const { p, at } = places.current[i];
        const el = document.createElement("div");
        el.className = p.capital ? "place capital" : "place";
        const dot = document.createElement("span");
        dot.className = "dot";
        const label = document.createElement("span");
        label.className = "label";
        label.textContent = p.name;
        el.append(dot, label);
        // the city's name with its country's, as the countries' own hover shows theirs
        el.addEventListener("mouseenter", () => {
          const t = tip.current, pt = m.project(at);
          if (!t) return;
          t.textContent = `${p.name}, ${namesRef.current[p.iso3] ?? p.iso3}${p.capital ? " (capital)" : ""} · ` +
            `${people(p.population)} people`;
          t.style.transform = `translate(${pt.x + 14}px, ${pt.y + 14}px)`;
          t.style.opacity = "1";
        });
        el.addEventListener("mouseleave", () => { if (tip.current) tip.current.style.opacity = "0"; });
        markers.current.set(i, new maplibregl.Marker({ element: el, anchor: "left" }).setLngLat(at).addTo(m));
      }
    }
    redraw.current = drawPlaces;

    return () => m.remove();
  }, [meta]);

  // ── the stability classes in the Stability section, or the Data tab's measure in the Data section ─────────────
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    const apply = () => {
      const breaks = stability.classes.breaks;
      const pairs = (section === "data" && choropleth ? Object.entries(choropleth)
        : stabilityColours ? Object.entries(stabilityColours)
        : Object.entries(stability.countries).map(([iso3, c]) => [iso3, rampColour(c.composite.score, breaks)]))
        .filter(([iso3]) => !only || only.includes(iso3));
      const colour = (pairs.length ? ["match", ["get", "iso3"], ...pairs.flat(), "#000000"]
        : "#000000") as unknown as ExpressionSpecification;
      m.setPaintProperty("classes", "fill-color", colour);
      const shown = (section === "stability" && showClasses) || (section === "data" && !!choropleth);
      m.setPaintProperty("classes", "fill-opacity", shown
        ? ["case", ["all", ["get", "member"], ["in", ["get", "iso3"], ["literal", pairs.map((x) => x[0])]]], 0.55, 0] : 0);
    };
    // "load" fires once: colours that arrive after it, while the style is still busy, wait for "idle" instead
    if (m.isStyleLoaded()) apply(); else m.once("idle", apply);
  }, [section, showClasses, stability, choropleth, stabilityColours, only]);

  // ── the Data tab's chosen states share the chosen country's tint ─────────────────────────────────────────────
  const marks = useRef<string[]>([]);
  const markKey = marked.join(",");
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    const apply = () => {
      if (!(m.getSource("countries") as GeoJSONSource | undefined)) return;
      for (const k of marks.current) if (k !== selected) m.setFeatureState({ source: "countries", id: k }, { chosen: false });
      for (const k of marked) m.setFeatureState({ source: "countries", id: k }, { chosen: true });
      marks.current = marked;
    };
    if (m.isStyleLoaded()) apply(); else m.once("idle", apply);
  }, [markKey]);  // eslint-disable-line react-hooks/exhaustive-deps

  // ── the chosen country: a faint tint, and the map moves it clear of the panel ───────────────────────────
  const previous = useRef<string | null>(null);
  const extents = useRef<Record<string, [number, number, number, number]>>({});
  useEffect(() => {
    loadOnce<CountriesGeo>("geo/countries.json").then((g) => {
      for (const f of g.features) {
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
      const own = selected ? extents.current[selected] : undefined;
      // with the links switched on, the map takes in both ends of the state's links, so a backer is never off-screen
      const far = selected && linksOn && section !== "wonders"
        ? linksBounds(linksDoc.current, linksOf(linksDoc.current, selected).map((l) => l.id)) : null;
      const e = own && far ? [Math.min(own[0], far[0]), Math.min(own[1], far[1]), Math.max(own[2], far[2]),
        Math.max(own[3], far[3])] : own;
      if (e) {
        const phone = window.innerWidth < 760;
        m.fitBounds([[e[0], e[1]], [e[2], e[3]]], {
          // a link's ends kept clear of the keys stacked on the left as well as of the panel
          padding: phone ? { top: 120, bottom: window.innerHeight * 0.6, left: 30, right: 30 }
            : { top: 90, bottom: 60, left: far ? 320 : 60, right: 500 },
          maxZoom: 6.5, duration: 1400,
        });
      }
    };
    if (m.isStyleLoaded()) apply(); else m.once("idle", apply);
  }, [selected, linksOn]);  // eslint-disable-line react-hooks/exhaustive-deps

  // ── wonders, in the Wonders section only: a click opens the viewer ──────────────────────────────────────────
  const wonderPins = useRef<maplibregl.Marker[]>([]);
  const wonderRef = useRef(onWonder);
  wonderRef.current = onWonder;
  useEffect(() => {
    const m = map.current;
    wonderPins.current.forEach((mk) => mk.remove());
    wonderPins.current = [];
    if (!m || section !== "wonders" || !wonders) return;
    for (const w of wonders) {
      const el = document.createElement("button");
      el.className = "wonder-pin";
      el.setAttribute("aria-label", `${w.name}: open its photographs`);
      const label = document.createElement("span");
      label.textContent = w.name;
      el.append(label);
      el.addEventListener("click", (e) => { e.stopPropagation(); wonderRef.current(w); });
      wonderPins.current.push(new maplibregl.Marker({ element: el, anchor: "left" }).setLngLat([w.lon, w.lat]).addTo(m));
    }
  }, [section, wonders]);

  // ── infrastructure: the layers are added once, hidden, and shown in their section as they are switched on ──────
  const infraRef = useRef<LayersDoc | null>(null);
  const popup = useRef<maplibregl.Popup | null>(null);
  const cardRef = useRef<(f: MapGeoJSONFeature, at: maplibregl.LngLat) => void>(() => {});
  linksRef.current = (at) => {
    const m = map.current;
    const doc = linksDoc.current;
    if (!m || !m.getLayer("links")) return;
    // only while switched on, and never in Wonders: every link faint, and in full the one pointed at in the panel, or
    // else the links of the state chosen (a member) or clicked (any other state)
    const on = linksOnRef.current && sectionRef.current !== "wonders";
    for (const id of ["links-faint", "links-faint-reported"]) m.setLayoutProperty(id, "visibility", on ? "visible" : "none");
    const who = otherRef.current ?? (sectionRef.current === "data" ? null : selectedRef.current);
    const ls = !on ? [] : focusRef.current ? (doc?.features.map((f) => f.properties)
      .filter((l) => l.id === focusRef.current) ?? []) : linksOf(doc, who);
    const ids: ExpressionSpecification = ["in", ["get", "id"], ["literal", ls.map((l) => l.id)]];
    for (const id of LINK_LAYERS) {
      if (!m.getLayer(id)) continue;
      m.setFilter(id, id === "links" ? ["all", ids, ["==", ["get", "status"], "confirmed"]]
        : id === "links-reported" ? ["all", ids, ["==", ["get", "status"], "reported"]] : ids);
    }
    // each shown link's ends named: the armed actor it backs, and a backer outside Africa, which has no name drawn
    linkEnds.current.forEach((mk) => mk.remove());
    linkEnds.current = [];
    const line = (l: Link) => doc?.features.find((f) => f.properties.id === l.id)?.geometry.coordinates ?? [];
    for (const l of ls) {
      const pts = line(l), actor = actorLabel(l);
      const ends: [string | null, [number, number] | undefined][] = [
        [actor, pts[pts.length - 1]], [namesRef.current[l.from] ? null : l.from_name, pts[0]]];
      for (const [text, at2] of ends) {
        if (!text || !at2) continue;
        const el = document.createElement("div");
        el.className = l.historical ? "link-end ended" : "link-end";
        el.textContent = text;
        el.style.borderColor = KIND_COLOURS[l.kind] ?? RING;
        linkEnds.current.push(new maplibregl.Marker({ element: el, anchor: "bottom", offset: [0, -6] })
          .setLngLat(at2).addTo(m));
      }
    }
    // a click on another state (no panel of its own) opens its cards; any other change closes them
    linksPopup.current?.remove();
    if (at && on && otherRef.current && ls.length && doc) {
      linksPopup.current = new maplibregl.Popup({ maxWidth: "280px", className: "infra-popup" })
        .setLngLat(at).setDOMContent(linkCards(ls, doc.kinds, doc.tiers)).addTo(m);
    }
  };
  useEffect(() => {  // the links follow the switch, the chosen state and the panel's pointer
    sectionRef.current = section;
    if (selected) otherRef.current = null;
    linksRef.current();
  }, [selected, section, linksOn, linkFocus]);
  cardRef.current = (f, at) => {
    const info = infraRef.current?.points.find((p) => `infra-pt-${p.id}` === f.layer.id);
    const m = map.current;
    if (!info || !m) return;
    popup.current?.remove();
    popup.current = new maplibregl.Popup({ maxWidth: "340px", className: "infra-popup" })
      .setLngLat(at).setDOMContent(card(info, parsed(f.properties))).addTo(m);
  };
  useEffect(() => {
    const m = map.current;
    if (!m || !infra) return;
    infraRef.current = infra;
    const add = () => {
      if (m.getLayer(`infra-pt-${infra.points[0]?.id}`)) return;  // already added
      for (const [name, a] of Object.entries(infra.archives)) {
        m.addSource(`infra-arch-${name}`, { type: "vector", attribution: `${a.attribution} (${a.licence})`,
          url: `pmtiles://${new URL(asset(`geo/infra/${a.file}`), window.location.href).href}` });
        for (const id of a.layers) addLines(m, id, name);
      }
      for (const p of infra.points) {
        m.addSource(`infra-${p.id}`, { type: "geojson", data: asset(`geo/infra/${p.file}`),
          attribution: `<a href="${p.link}" target="_blank" rel="noreferrer">${p.attribution}</a>` });
        const s = SHAPES[p.id];
        // a ring is sized by the ships calling per year (PortWatch's yearly average), so a USGS port's dot sits inside
        const ships: ExpressionSpecification = ["sqrt", ["coalesce", ["get", "vessel_count_total"], 0]];
        m.addLayer({
          id: `infra-pt-${p.id}`, type: "circle", source: `infra-${p.id}`, layout: { visibility: "none" },
          paint: s?.shape === "ring" ? {
            "circle-color": s.colour, "circle-opacity": 0, "circle-stroke-color": s.colour, "circle-stroke-width": 2,
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, ["+", 4, ["*", 0.08, ships]],
              9, ["+", 9, ["*", 0.16, ships]]],
          } : {
            "circle-color": s?.colour ?? COLOURS[p.id] ?? RING, "circle-stroke-color": s ? EDGE : RING,
            "circle-stroke-width": s ? 1.5 : 1,
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, s ? 5 : p.id === "ports" ? 4 : 2.5,
              9, s ? 9 : p.id === "ports" ? 8 : 6],
          },
        });
        m.on("mouseenter", `infra-pt-${p.id}`, () => { m.getCanvas().style.cursor = "pointer"; });
        m.on("mouseleave", `infra-pt-${p.id}`, () => { m.getCanvas().style.cursor = ""; });
      }
    };
    // "load" fires once, and the catalogue can arrive after it while the style is still busy: wait for "idle"
    if (m.isStyleLoaded()) add(); else m.once("idle", add);
  }, [infra]);
  const infraKey = infraOn.join(",");
  useEffect(() => {
    const m = map.current;
    if (!m || !infra) return;
    const apply = () => {
      for (const layer of m.getStyle().layers) {
        if (!layer.id.startsWith("infra-")) continue;
        const id = layer.id.replace(/^infra-(pt|ln)-/, "").split("-")[0];
        m.setLayoutProperty(layer.id, "visibility", section === "infrastructure" && infraOn.includes(id) ? "visible" : "none");
      }
      if (section !== "infrastructure") popup.current?.remove();
    };
    if (m.isStyleLoaded()) apply(); else m.once("idle", apply);
  }, [section, infra, infraKey]);  // eslint-disable-line react-hooks/exhaustive-deps

  // ── cities follow the section and their switch ────────────────────────────────────────────────────────────
  useEffect(() => {
    sectionRef.current = section;
    citiesRef.current = cities;
    redraw.current();
  }, [section, cities]);

  return (
    <div className="map">
      <div ref={box} className="map-canvas" />
      <div ref={tip} className="hover-name" />
    </div>
  );
}

const MAJOR = ["Road (Motorway)", "Road (Trunk)"];

// One line layer from one archive, under the borders. The grid's existing lines are solid and every other status
// (planned, under construction, decommissioned) is dashed, as the World Bank records them; roads widen by class.
function addLines(m: maplibregl.Map, id: string, archive: string) {
  const base = { type: "line" as const, source: `infra-arch-${archive}`, "source-layer": id,
    layout: { visibility: "none" as const, "line-cap": "round" as const } };
  const colour = COLOURS[id] ?? RING;
  const width = id === "roads"
    ? ["interpolate", ["linear"], ["zoom"], 4, ["match", ["get", "class"], MAJOR, 1.2, 0.5],
      10, ["match", ["get", "class"], MAJOR, 3, 1.4]]
    : ["interpolate", ["linear"], ["zoom"], 3, 0.8, 9, 2.4];
  const paint = { "line-color": colour, "line-width": width as ExpressionSpecification, "line-opacity": 0.9 };
  if (id === "grid") {
    m.addLayer({ ...base, id: `infra-ln-grid-${archive}`, filter: ["==", ["get", "status"], "Existing"], paint }, "borders");
    m.addLayer({ ...base, id: `infra-ln-grid-${archive}-other`, filter: ["!=", ["get", "status"], "Existing"],
      paint: { ...paint, "line-dasharray": [2, 2] } }, "borders");
  } else m.addLayer({ ...base, id: `infra-ln-${id}-${archive}`, paint }, "borders");
}

// A non-member state's links (it has no panel of its own), kept small: one line each (its colour, the two sides, its
// kind in words and its standing under the rule), opened by a click to its conflict, summary and sources, each with
// its tier. Built from DOM nodes, so no text from the data is ever read as HTML.
function linkCards(ls: Link[], kinds: Record<string, string>, tiers: Record<string, string>): HTMLElement {
  const el = document.createElement("div");
  el.className = "infra-card link-cards";
  const add = (parent: HTMLElement, tag: string, text: string, cls?: string) => {
    const n = document.createElement(tag);
    n.textContent = text;
    if (cls) n.className = cls;
    parent.append(n);
    return n;
  };
  add(el, "div", ls.length === 1 ? "Link" : `${ls.length} links`, "panel-kicker");
  for (const l of ls) {
    const card = add(el, "details", "", "link-card");
    const line = add(card, "summary", "");
    const sw = document.createElement("span");
    sw.className = l.status === "confirmed" ? "swatch line" : "swatch line dashed";
    sw.style.background = KIND_COLOURS[l.kind] ?? RING;
    line.append(sw);
    add(line, "span", heading(l), "link-card-title");
    add(line, "span", `${kinds[l.kind] ?? l.kind} · ${standing(l, tiers)}`, "muted small");
    add(card, "div", l.conflict, "muted small");
    add(card, "p", l.summary, "small");
    for (const src of l.sources) {
      const line = add(card, "div", "", "muted small");
      const a = document.createElement("a");
      a.href = src.url;
      a.target = "_blank";
      a.rel = "noreferrer";
      a.textContent = `${src.publisher}, ${src.title}`;
      line.append(a, ` (${src.date}) · ${tiers[src.tier] ?? src.tier}`);
    }
  }
  add(el, "div", "The owner's compilation, from the sources each names.", "muted small");
  return el;
}

// A feature's card: its fields under the publisher's labels, a port's commodities one per line, and the source.
// Built from DOM nodes, so no value from the data is ever read as HTML.
function card(info: LayersDoc["points"][number], props: Record<string, unknown>): HTMLElement {
  const el = document.createElement("div");
  el.className = "infra-card";
  const add = (tag: string, text: string, cls?: string) => {
    const n = document.createElement(tag);
    n.textContent = text;
    if (cls) n.className = cls;
    el.append(n);
    return n;
  };
  add("div", info.title, "panel-kicker");
  const name = info.name ?? "FeatureNam";
  add("div", String(props[name] ?? info.title), "infra-card-title");
  const rows = Array.isArray(props.rows) ? props.rows as Record<string, unknown>[] : [];
  const perRow = info.fields.filter((f) => rows.some((r) => f.name in r));
  const table = document.createElement("table");
  table.className = "rows";
  for (const [label, value] of cardRows(props, info.fields.filter((f) => f.name !== name && !perRow.includes(f)))) {
    const tr = table.insertRow();
    tr.insertCell().textContent = label;
    tr.insertCell().textContent = value;
  }
  el.append(table);
  for (const r of rows) add("div", cardRows(r, perRow).map(([l, v]) => `${l}: ${v}`).join(" · "), "small infra-card-row");
  if (typeof props.portwatch_name === "string") {
    add("div", `The same port in PortWatch: ${props.portwatch_name} (by its World Port Index ID and UN/LOCODE)`,
      "small infra-card-row");
  }
  const activity = props.activity as Activity | undefined;
  if (activity?.years?.length && info.activity?.length) {
    add("div", "Each complete year, derived: the sum of PortWatch's daily figures (t: metric tons, as PortWatch " +
      "estimates them). Sources: UN Global Platform; IMF PortWatch.", "small muted infra-card-row");
    const t = document.createElement("table");
    t.className = "rows";
    const head = t.createTHead().insertRow();
    ["Year", ...info.activity.map((c) => c.label)].forEach((h, i) => {
      const th = document.createElement("th");
      th.textContent = h;
      if (i) th.className = "num";
      head.append(th);
    });
    const body = t.createTBody();
    for (const row of activityRows(activity, info.activity)) {
      const tr = body.insertRow();
      row.forEach((v, i) => { const td = tr.insertCell(); td.textContent = v; if (i) td.className = "num"; });
    }
    el.append(t);
  }
  const source = add("div", "", "muted small");
  const link = document.createElement("a");
  link.href = info.link;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = info.attribution;
  source.append(link, ` · ${info.licence}`);
  return el;
}
