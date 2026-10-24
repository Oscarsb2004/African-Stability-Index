import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// public/ holds what 05_web.py writes (data/, geo/); Vite serves it verbatim. A GitHub Pages project site lives
// under /<repo>/, so the base comes from VITE_BASE when building for it.
export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE || "/",
  server: { port: 5176, strictPort: false },
  // the map library (1 MB of the 1.3 MB) in a file of its own: it changes only when its version does, so a reader's
  // browser keeps it across the site's updates, and it loads beside the site's own code
  build: { rollupOptions: { output: { manualChunks: { map: ["maplibre-gl", "pmtiles"] } } } },
});
