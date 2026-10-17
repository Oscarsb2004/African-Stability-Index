"""
scripts/build_pages.py — build a static GitHub Pages site that runs the real
dashboard in the visitor's browser.

GitHub Pages serves files and cannot run Python, and this interface is a Dash
app: Dash's renderer asks a Python server for its layout, and again on every
callback. Rather than rewrite the interface, the site ships the server as well —
compiled to WebAssembly by Pyodide — and answers the renderer's requests in
memory:

    here, at build time (CPython)             the visitor's browser
    ─────────────────────────────             ──────────────────────────────────
    render index.html under the Pages prefix  load index.html and Dash's JS
    copy every Dash and dbc JS/CSS file       boot Pyodide; install the wheels
    zip asi/ and the files it reads           unpack the zip; import the app
    fetch the exact wheels installed here     answer _dash-layout, _dash-dependencies
                                              and _dash-update-component from the
                                              app's own Flask test client

No application code changes. Nothing runs on a server: the published site is
static files, so there is no attack surface and nothing to keep awake.

The build refuses to finish unless three things hold, because each is a way to
ship a site that loads and then shows nothing:

  * every script and stylesheet index.html references exists in the output;
  * every Python requirement is either provided by the pinned Pyodide release at
    a version that satisfies it, or vendored as a pure-Python wheel;
  * the Dash whose JavaScript was copied is the Dash whose wheel was vendored —
    its Python and its renderer must match exactly, so both come from this
    environment.

    python scripts/build_pages.py                     # prefix /African-Stability-Index/
    python scripts/build_pages.py --base /x/ --out d  # any other prefix and output
    python scripts/build_pages.py --no-wheels         # offline; for tests — will not boot
"""

from __future__ import annotations

import argparse
import importlib.metadata as md
import json
import os
import pkgutil
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_SRC = Path(__file__).resolve().parent / "pages"

PYODIDE_VERSION = "314.0.7"
PYODIDE_URL = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/"

#: What the dashboard reads at runtime, relative to the repository root. Found
#: by reading every PROJECT_ROOT path in asi/; nothing else enters the bundle.
BUNDLE = ["asi", "data/panel", "narrative/countries", "context", "qualitative",
          "assets", "indicators_list", "registry"]

#: Distributions the site must provide. Always vendored at the version installed
#: here, never taken from Pyodide: the Dash renderer copied into the site must
#: match the Dash that answers it, and Plotly's figure JSON must match the
#: plotly.js that Dash bundles. Their dependencies may come from Pyodide.
ROOTS = ["dash", "dash-bootstrap-components", "plotly"]

#: The Dash endpoints the browser-side shim answers from Python. Everything else
#: is a static file. Passed into boot.js so the two cannot disagree, and checked
#: against the app's own URL map below.
DASH_ROUTES = ["_dash-layout", "_dash-dependencies", "_dash-update-component"]

BUNDLE_NAME = "asi_app.zip"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)   # deterministic archives: re-runs diff clean


def canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


# ── The app, under the Pages prefix ────────────────────────────────────────────

def load_app(base: str):
    """
    Import the dashboard with Dash's request prefix set to the Pages path.

    Dash reads DASH_REQUESTS_PATHNAME_PREFIX when the app is constructed, so it
    must be set before the import. The assertion guards that mechanism: if a
    future Dash stops reading the variable, every URL in the site would point at
    the domain root and 404, and it is better to fail here.
    """
    os.environ["DASH_REQUESTS_PATHNAME_PREFIX"] = base
    sys.path.insert(0, str(ROOT))
    from asi.dashboard.app import app

    got = app.config.requests_pathname_prefix
    if got != base:
        raise SystemExit(f"Dash ignored the prefix: wanted {base!r}, got {got!r}")

    routes = {rule.rule.lstrip("/") for rule in app.server.url_map.iter_rules()}
    missing = [r for r in DASH_ROUTES if r not in routes]
    if missing:
        raise SystemExit(f"This Dash has no route for {missing}; boot.js would "
                         f"intercept requests nothing answers. Routes: {sorted(routes)}")

    # A background callback runs as a job behind a cache or a worker process and
    # is polled for by page-load-bound handles (Dash's `end_id`). None of that
    # exists in a browser, so the site would render and then hang on the first
    # such callback. Refuse to build rather than ship that.
    background = [out for out, spec in app.callback_map.items() if spec.get("background")]
    if background:
        raise SystemExit(f"background callbacks cannot run in the browser: {background}")
    return app


def local_refs(html: str, base: str) -> list[str]:
    """Every src/href in the page that the site itself must serve."""
    return [u for u in re.findall(r'(?:src|href)="([^"]+)"', html) if u.startswith(base)]


def extract_static(app, base: str, out: Path) -> tuple[str, int]:
    """
    Render index.html and copy every file it, or Dash's renderer, will request.

    Two sources, because the page names only what it loads up front. Dash also
    registers resources it loads later on demand — plotly.js among them, fetched
    the first time a figure renders — and those never appear as a tag.
    """
    client = app.server.test_client()
    page = client.get("/")
    if page.status_code != 200:
        raise SystemExit(f"index rendered {page.status_code}")
    html = page.get_data(as_text=True)

    # Dash 4 mints a random, signed `end_id` into every page it renders. Its only
    # use is binding background-callback job handles to one page load (see
    # dash/_callback_signing.py), and load_app() has already refused any app with
    # a background callback, so the value is inert here — the in-browser app
    # holds a different signing secret and never verifies it. Left random, it
    # makes every build of an unchanged commit differ; pinned, rebuilds are
    # byte-identical. Exactly one is expected, so a Dash change that moves or
    # duplicates it stops the build instead of silently reintroducing the churn.
    html, pinned = re.subn(r'"end_id":"[^"]*"', '"end_id":"static-site"', html)
    if pinned != 1:
        raise SystemExit(f"expected one end_id in Dash's page, found {pinned}")

    written = 0
    for url in local_refs(html, base):
        rel = url[len(base):]
        resp = client.get("/" + rel)
        if resp.status_code != 200:
            raise SystemExit(f"{url} rendered {resp.status_code}")
        dest = out / rel.split("?", 1)[0]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.get_data())
        written += 1

    for package, paths in sorted(app.registered_paths.items()):
        for rel in sorted(paths):
            try:
                data = pkgutil.get_data(package, rel)
            except FileNotFoundError:
                # Dash registers source maps its wheel does not ship. Only a
                # browser's devtools ever request them, so their absence cannot
                # break the page; any other missing file can, and stops the build.
                if rel.endswith(".map"):
                    continue
                raise SystemExit(f"{package}/{rel} is registered but not installed")
            if data is None:
                raise SystemExit(f"{package}/{rel} is registered but not readable")
            dest = out / "_dash-component-suites" / package / rel
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                written += 1
    return html, written


# ── The Python the browser needs ───────────────────────────────────────────────

def bundle(out: Path) -> tuple[int, int]:
    """Zip the package and the files it reads, deterministically."""
    files = []
    for entry in BUNDLE:
        src = ROOT / entry
        if not src.exists():
            raise SystemExit(f"bundle entry {entry} does not exist")
        files += [p for p in sorted(src.rglob("*"))
                  if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]

    dest = out / "py" / BUNDLE_NAME
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
    return len(files), dest.stat().st_size


def app_distributions() -> list[str]:
    """
    The distributions asi/ imports directly, found by reading its source.

    These seed the resolver alongside ROOTS. Deriving them rather than listing
    them means a new import in the dashboard is either supplied or stops the
    build by name — instead of the site loading and then dying on an ImportError
    in a visitor's browser. Dash's own dependencies never pull in pandas, so
    without this the first build shipped a dashboard that could not import.
    """
    import ast

    stdlib = set(sys.stdlib_module_names)
    modules: set[str] = set()
    for path in sorted((ROOT / "asi").rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                modules |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                modules.add(node.module.split(".")[0])
    third_party = sorted(modules - stdlib - {"asi"})

    owners = md.packages_distributions()
    unknown = [m for m in third_party if m not in owners]
    if unknown:
        raise SystemExit(f"asi/ imports {unknown}, which no installed distribution provides")
    return sorted({canon(d) for m in third_party for d in owners[m]})


def pyodide_lock() -> dict:
    with urllib.request.urlopen(PYODIDE_URL + "pyodide-lock.json", timeout=60) as r:
        return json.load(r)


def resolve(lock: dict, app_roots: list[str]) -> tuple[list[str], dict[str, str]]:
    """
    Split the dependency closure of ROOTS and the app's own imports into what
    Pyodide provides and what must be vendored.

    Markers are evaluated for Pyodide's interpreter, not this one. A requirement
    Pyodide provides is taken from Pyodide only if its version satisfies every
    specifier that asks for it; otherwise the build stops, since the alternative
    is a runtime ImportError on the visitor's machine.
    """
    from packaging.requirements import Requirement
    from packaging.version import Version

    full = lock["info"]["python"]
    env = {"python_version": ".".join(full.split(".")[:2]), "python_full_version": full,
           "sys_platform": "emscripten", "platform_system": "Emscripten",
           "os_name": "posix", "platform_machine": "wasm32",
           "implementation_name": "cpython", "platform_python_implementation": "CPython",
           "extra": ""}
    provided = {canon(k): v for k, v in lock["packages"].items()}

    pyodide_pkgs: set[str] = set()
    vendored: dict[str, str] = {}
    edges: list[tuple[str, Requirement]] = []
    roots = {canon(r) for r in ROOTS}
    queue, seen = sorted(roots | set(app_roots)), set()

    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        if name in provided and name not in roots:
            pyodide_pkgs.add(provided[name]["name"])
            continue
        try:
            version = md.version(name)
        except md.PackageNotFoundError:
            raise SystemExit(f"{name} is needed in the browser but is neither provided "
                             f"by Pyodide {PYODIDE_VERSION} nor installed here to vendor")
        vendored[name] = version
        for spec in md.requires(name) or []:
            req = Requirement(spec)
            if req.marker and not req.marker.evaluate(env):
                continue
            edges.append((name, req))
            queue.append(canon(req.name))

    for parent, req in edges:
        child = canon(req.name)
        have = vendored.get(child) or provided[child]["version"]
        if req.specifier and not req.specifier.contains(Version(have), prereleases=True):
            raise SystemExit(f"{parent} needs {req}, but the browser would get {child} {have}")

    return sorted(pyodide_pkgs | {"micropip"}), dict(sorted(vendored.items()))


def fetch_wheels(vendored: dict[str, str], dest: Path, python: str) -> list[str]:
    """Download each pin as a pure-Python wheel; anything else cannot run here."""
    dest.mkdir(parents=True, exist_ok=True)
    pins = [f"{n}=={v}" for n, v in vendored.items()]
    subprocess.run(
        [sys.executable, "-m", "pip", "download", "--quiet", "--no-deps",
         "--only-binary=:all:", "--platform", "any", "--implementation", "py",
         "--abi", "none", "--python-version", python, "--dest", str(dest), *pins],
        check=True)
    wheels = sorted(p.name for p in dest.glob("*.whl"))
    impure = [w for w in wheels if not w.endswith("-none-any.whl")]
    if impure:
        raise SystemExit(f"not pure-Python, cannot run in Pyodide: {impure}")
    got = {canon(w.split("-")[0]) for w in wheels}
    if got != set(vendored):
        raise SystemExit(f"wheel set mismatch: missing {set(vendored) - got}, "
                         f"extra {got - set(vendored)}")
    return wheels


# ── The page ───────────────────────────────────────────────────────────────────

LOADER = """
<div id="asi-boot" role="status" aria-live="polite">
  <div class="asi-boot-card">
    <h1>African Stability Index</h1>
    <p>This site runs its analysis in your browser, so the first visit downloads
       a Python runtime. Later visits load from your browser's cache.</p>
    <p id="asi-boot-status">Starting&hellip;</p>
  </div>
</div>
<style>
  #asi-boot { position: fixed; inset: 0; z-index: 9999; display: grid; place-items: center;
              background: #f7f8fa; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  .asi-boot-card { max-width: 32rem; padding: 2rem; color: #1b3a6b; }
  .asi-boot-card h1 { font-size: 1.5rem; margin: 0 0 .75rem; }
  .asi-boot-card p { color: #3d4a5c; line-height: 1.5; margin: .5rem 0; }
  #asi-boot-status { font-family: ui-monospace, Consolas, monospace; font-size: .9rem; color: #2e6db4; }
  #asi-boot-status.error { color: #b3261e; }
</style>
"""


def inject(html: str, config: dict, base: str) -> str:
    """
    Load the shim before anything of Dash's.

    boot.js replaces window.fetch, and Dash's renderer requests its layout the
    moment it starts, so the shim has to be installed first: a plain script at
    the top of <head> runs before the renderer's scripts at the end of <body>.
    """
    head = (f"<script>window.__ASI_PAGES__ = {json.dumps(config)};</script>\n"
            f'<script src="{PYODIDE_URL}pyodide.js"></script>\n'
            f'<script src="{base}py/boot.js"></script>\n')
    html, n_head = re.subn(r"<head>", "<head>\n" + head, html, count=1)
    html, n_body = re.subn(r"<body>", "<body>\n" + LOADER, html, count=1)
    if n_head != 1 or n_body != 1:
        raise SystemExit("could not find <head> and <body> in Dash's index page")
    return html


# ── Build ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="/African-Stability-Index/",
                    help="URL prefix the site is served under (must start and end with /)")
    ap.add_argument("--out", default="build/pages", help="output directory (replaced)")
    ap.add_argument("--no-wheels", action="store_true",
                    help="skip the network: no Pyodide lockfile, no wheels (tests only)")
    args = ap.parse_args()

    base = args.base
    if not (base.startswith("/") and base.endswith("/")):
        ap.error("--base must start and end with /")

    out = (ROOT / args.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    app = load_app(base)
    html, n_static = extract_static(app, base, out)
    n_files, zip_bytes = bundle(out)

    if args.no_wheels:
        packages, wheels = ["micropip"], []
    else:
        lock = pyodide_lock()
        packages, vendored = resolve(lock, app_distributions())
        python = ".".join(lock["info"]["python"].split(".")[:2])
        wheels = fetch_wheels(vendored, out / "py" / "wheels", python)
        if f"dash-{md.version('dash')}-" not in " ".join(wheels):
            raise SystemExit("the vendored Dash is not the Dash whose JavaScript was copied")

    config = {"base": base, "pyodide": PYODIDE_URL, "packages": packages,
              "wheels": wheels, "bundle": BUNDLE_NAME, "dash_routes": DASH_ROUTES}
    shutil.copyfile(PAGES_SRC / "boot.js", out / "py" / "boot.js")
    html = inject(html, config, base)
    (out / "index.html").write_text(html, encoding="utf-8")
    # Pages runs Jekyll on branch-deployed sites, and Jekyll drops every path
    # starting with an underscore — which is all of _dash-component-suites/.
    # The Actions deploy skips Jekyll anyway; this keeps a branch deploy working.
    (out / ".nojekyll").write_text("", encoding="utf-8")

    missing = [u for u in local_refs(html, base)
               if not (out / u[len(base):].split("?", 1)[0]).is_file()]
    if missing:
        raise SystemExit(f"index.html references files the site does not contain: {missing}")

    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"built {out}")
    print(f"  prefix            {base}")
    print(f"  static files      {n_static}")
    print(f"  bundled files     {n_files} ({zip_bytes:,} bytes zipped)")
    print(f"  Pyodide packages  {len(packages)}: {', '.join(packages)}")
    print(f"  vendored wheels   {len(wheels)}: {', '.join(wheels) or '(skipped)'}")
    print(f"  total             {size:,} bytes on disk (Pyodide itself loads from its CDN)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
