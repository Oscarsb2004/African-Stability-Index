import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// public/ holds what 05_web.py writes (data/, geo/); Vite serves it verbatim. A GitHub Pages project site lives
// under /<repo>/, so the base comes from VITE_BASE when building for it.
export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE || "/",
  server: { port: 5176, strictPort: false },
});
