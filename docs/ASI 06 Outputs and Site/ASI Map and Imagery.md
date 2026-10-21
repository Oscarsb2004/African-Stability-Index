---
type: "project-page"
project: "African Stability Index"
section: "06 Outputs and Site"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# ASI Map and Imagery

> [!abstract] Goal
> Show Africa as a satellite globe, sharp enough to zoom deep into a country, with borders drawn as the UN does and countries that answer hover and click without lighting up.

## Why it exists

The map is the site's front door; the owner asked for real imagery, deep zoom and quiet interaction.

## Precise objectives

1. Imagery (P62): Esri World Imagery through ArcGIS Location Platform when `VITE_ESRI_KEY` is set (zoom to 19, sub-metre in many cities); EOX Sentinel-2 cloudless 2025 otherwise (about zoom 14–15).
2. Attribution: "Powered by Esri" and the service's own data credits, always visible (Esri's rule); EOX's credit line otherwise.
3. Borders: Natural Earth 1:50m lines in ISO's view: Somaliland drawn as Somalia, Western Sahara apart and unscored, lines ISO does not recognise dropped, disputed lines dashed.
4. Hover shows the name only; a chosen country gets a faint tint; the map flies it clear of the panel.
5. Cities: capitals from the start, others by Natural Earth's zoom level, overlapping labels skipped.

## Inputs and outputs

- **In:** imagery tiles; `geo/countries.json`, `borders.json`, `places.json`
- **Out:** the map

## Where it stands

Built. The Esri key is the owner's to create: a free ArcGIS Location Platform account (2,000,000 basemap tiles a
month; pay-as-you-go stays off until a payment method is added), an API key with the basemaps privilege, restricted
to the site's addresses, saved in `projects/asi/web/.env.local`.

## Open questions

- The key in a published site is visible to visitors, as every browser key is; the referrer restriction is what protects it.

## Related

Sources (athena-data)
