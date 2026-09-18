// boot.js — run the dashboard's Python in the visitor's browser.
//
// Built into the Pages site by scripts/build_pages.py, which also writes the
// configuration this reads (window.__ASI_PAGES__). The site is static files;
// this script is what stands in for the server.
//
// Dash's renderer talks to its server through window.fetch, on three endpoints.
// This replaces fetch before the renderer starts, answers those three from the
// app's own Flask test client running under Pyodide, and passes every other
// request through untouched. Requests the renderer makes before Python is ready
// simply wait: the renderer shows its loading state until the promise settles.

(() => {
  "use strict";

  const cfg = window.__ASI_PAGES__;
  const ROUTES = new Set(cfg.dash_routes);
  const nativeFetch = window.fetch.bind(window);

  // Statuses whose Response may not carry a body. Dash answers a callback that
  // raises PreventUpdate with 204, and `new Response("", {status: 204})` throws.
  const NULL_BODY = new Set([101, 204, 205, 304]);

  let answer = null;                      // the Python handler, once booted
  let settle;
  const ready = new Promise((resolve, reject) => { settle = { resolve, reject }; });

  const setStatus = (text, isError = false) => {
    const el = document.getElementById("asi-boot-status");
    if (!el) return;
    el.textContent = text;
    el.classList.toggle("error", isError);
  };

  // Long synchronous Python calls freeze the page, so give the browser a frame
  // to paint the latest status before starting one.
  const paint = () => new Promise((r) => setTimeout(r, 30));

  const dashRoute = (url) => {
    if (url.origin !== location.origin || !url.pathname.startsWith(cfg.base)) return null;
    const rel = url.pathname.slice(cfg.base.length);
    return ROUTES.has(rel) ? rel : null;
  };

  window.fetch = async (input, init = {}) => {
    const request = input instanceof Request ? input : null;
    const url = new URL(request ? request.url : String(input), location.href);
    const route = dashRoute(url);
    if (route === null) return nativeFetch(input, init);

    const handle = answer ?? (await ready);
    const method = (init.method || (request && request.method) || "GET").toUpperCase();
    let body = init.body !== undefined ? init.body : request ? await request.text() : "";
    if (body != null && typeof body !== "string") body = await new Response(body).text();

    const result = handle(method, "/" + route + url.search, body ?? "");
    const [status, text, contentType] = result.toJs();
    result.destroy();

    if (route === "_dash-layout") document.getElementById("asi-boot")?.remove();
    return new Response(NULL_BODY.has(status) ? null : text,
                        { status, headers: { "Content-Type": contentType } });
  };

  async function boot() {
    setStatus("Loading the Python runtime…");
    const pyodide = await loadPyodide({ indexURL: cfg.pyodide });

    setStatus("Loading pandas, NumPy and friends…");
    await pyodide.loadPackage(cfg.packages);

    setStatus("Installing Dash…");
    const wheelUrls = cfg.wheels.map((w) => new URL(`${cfg.base}py/wheels/${w}`, location.href).href);
    pyodide.globals.set("WHEEL_URLS", pyodide.toPy(wheelUrls));
    await pyodide.runPythonAsync(
      "import micropip\nawait micropip.install(WHEEL_URLS, deps=False)"
    );

    setStatus("Loading the index data…");
    const archive = await nativeFetch(`${cfg.base}py/${cfg.bundle}`);
    if (!archive.ok) throw new Error(`${cfg.bundle}: HTTP ${archive.status}`);
    pyodide.unpackArchive(await archive.arrayBuffer(), "zip", { extractDir: "/home/pyodide/asi" });

    setStatus("Starting the dashboard…");
    await paint();
    pyodide.globals.set("BASE", cfg.base);
    pyodide.runPython(`
import os, sys
os.environ["DASH_REQUESTS_PATHNAME_PREFIX"] = BASE
sys.path.insert(0, "/home/pyodide/asi")
from asi.dashboard.app import app

_client = app.server.test_client()

def handle(method, path, body):
    kwargs = {"method": method}
    if method != "GET":
        kwargs.update(data=body, content_type="application/json")
    r = _client.open(path, **kwargs)
    return (r.status_code, r.get_data(as_text=True),
            r.headers.get("Content-Type", "application/json"))
`);
    answer = pyodide.globals.get("handle");
    settle.resolve(answer);
    setStatus("Rendering…");
  }

  boot().catch((err) => {
    console.error(err);
    setStatus(`The dashboard could not start: ${err.message}`, true);
    settle.reject(err);
  });
})();
