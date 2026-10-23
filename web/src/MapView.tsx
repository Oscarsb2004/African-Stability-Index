// The map: satellite imagery on a globe, Natural Earth borders, and countries that answer hover and click.
// Hover shows the name only; nothing lights up. A chosen country gets a faint tint so the eye can find it again.
// City labels are HTML markers, so the map needs no glyph server.

import { useEffect, useRef } from "react";
import maplibregl, { type ExpressionSpecification, type GeoJSONSource, type MapGeoJSONFeature } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Protocol } from "pmtiles";
import { asset, people, rampColour, type MetaDoc, type Section, type StabilityDoc, type Wonder } from "./data";
import { activityRows, cardRows, COLOURS, EDGE, parsed, RING, SHAPES, type Activity, type LayersDoc } from "./infra";

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

export default function MapView({ meta, stability, section, selected, showClasses, choropleth, marked = [], onSelect,
  wonders, onWonder, infra = null, infraOn = [], cities = false, names = {},
  stabilityColours = null, only = null }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const tip = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markers = useRef<maplibregl.Marker[]>([]);
  const places = useRef<{ p: Place; at: [number, number] }[]>([]);
  const sectionRef = useRef(section);
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
      if ((e.originalEvent.target as HTMLElement | null)?.closest?.(".place")) return;  // a city label has its own
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
      // a point's card, not the country under it; the hit box is wider than the dot, so a small mark is easy to take
      const near: [maplibregl.PointLike, maplibregl.PointLike] = [[e.point.x - 6, e.point.y - 6], [e.point.x + 6, e.point.y + 6]];
      const point = m.queryRenderedFeatures(near).find((f) => f.layer.id.startsWith("infra-pt-"));
      if (point) { cardRef.current(point, e.lngLat); return; }
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
      // only when switched on; the wonders have the map to themselves
      if (sectionRef.current === "wonders" || !citiesRef.current) return;
      const { clientWidth: width, clientHeight: height } = m.getCanvas();
      // capitals from the start; every other city once the map is zoomed to the level Natural Earth gives it.
      // places.json is ordered capitals first, then by population, so a label that would overlap one already
      // placed is the less important one and is skipped.
      const placed: number[][] = [];
      const shown = [];
      for (const c of places.current) {
        const { p, at } = c;
        if (!(p.capital ? zoom >= 2 : zoom >= p.min_zoom - 1) || !bounds.contains(at)) continue;
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
        markers.current.push(new maplibregl.Marker({ element: el, anchor: "left" }).setLngLat(at).addTo(m));
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
