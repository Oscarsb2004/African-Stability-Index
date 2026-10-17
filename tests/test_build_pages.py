"""
The GitHub Pages build — the static site that runs the dashboard in the browser.

A broken Pages build has one symptom whatever the cause: the site loads, and
then shows nothing. These tests cover the causes that can be checked without a
browser or the network:

  * a file index.html references that was never copied;
  * the shim loading after Dash's renderer, so the renderer's first requests
    escape to a server that does not exist;
  * the browser missing a Python package the dashboard imports — the first
    build shipped without pandas, because Dash does not depend on it;
  * the resolver trusting a Pyodide package too old for its dependents;
  * a rebuild that is not byte-identical, which would make every deploy a diff.

The site is built in a subprocess (`--no-wheels`, so offline) because the
dashboard reads its URL prefix once, at import, and must import fresh under the
Pages prefix. What only a browser can show — that Python actually boots and the
callbacks answer — was verified by hand in the Browser pane; see the PR.
"""

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_pages.py"
BASE = "/asi-test/"


def _build(out: Path) -> Path:
    subprocess.run([sys.executable, str(SCRIPT), "--base", BASE, "--out", str(out),
                    "--no-wheels"], check=True, cwd=ROOT, capture_output=True, text=True)
    return out


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_pages", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def site(tmp_path_factory) -> Path:
    return _build(tmp_path_factory.mktemp("pages"))


@pytest.fixture(scope="module")
def html(site) -> str:
    return (site / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def config(html) -> dict:
    return json.loads(re.search(r"window\.__ASI_PAGES__ = (\{.*?\});", html).group(1))


# ── The page ───────────────────────────────────────────────────────────────────

def test_every_local_reference_in_the_page_exists(site, html):
    refs = [u for u in re.findall(r'(?:src|href)="([^"]+)"', html) if u.startswith(BASE)]
    assert len(refs) > 10, "found almost no local references — the check would pass on nothing"
    missing = [u for u in refs if not (site / u[len(BASE):].split("?", 1)[0]).is_file()]
    assert not missing


def test_the_shim_loads_before_any_of_dashs_scripts(html):
    """boot.js replaces fetch; Dash requests its layout the moment it starts."""
    assert html.index("py/boot.js") < html.index("_dash-component-suites")
    assert html.index("pyodide.js") < html.index("py/boot.js")


def test_lazily_loaded_chunks_are_shipped_under_their_plain_names(site):
    """
    Dash never names these in the page; its renderer requests them on first use
    by their plain file names. A site that copies only what the page references
    renders, then breaks the first time a graph or dropdown appears.
    """
    dcc = site / "_dash-component-suites" / "dash" / "dcc"
    for chunk in ("async-graph.js", "async-dropdown.js", "async-slider.js"):
        assert (dcc / chunk).is_file(), chunk
    assert (site / "_dash-component-suites" / "plotly" / "package_data" / "plotly.min.js").is_file()


def test_jekyll_is_disabled(site):
    """Jekyll drops every path starting with '_' — all of _dash-component-suites/."""
    assert (site / ".nojekyll").is_file()


# ── What boot.js is told ───────────────────────────────────────────────────────

def test_the_config_carries_the_prefix_the_page_was_built_for(config):
    assert config["base"] == BASE


def test_the_intercepted_routes_are_routes_the_app_has(config):
    """The shim answers these paths from Python; each must exist in the app."""
    from asi.dashboard.app import app
    routes = {rule.rule.lstrip("/") for rule in app.server.url_map.iter_rules()}
    assert config["dash_routes"], "no routes — the shim would intercept nothing"
    assert set(config["dash_routes"]) <= routes


def test_boot_js_reads_the_routes_from_config_rather_than_its_own_list(site):
    """One list, in build_pages.py, so the shim and the app cannot disagree."""
    boot = (site / "py" / "boot.js").read_text(encoding="utf-8")
    assert "cfg.dash_routes" in boot
    assert "_dash-update-component" not in boot


# ── The Python the browser gets ────────────────────────────────────────────────

def test_the_bundle_carries_what_the_dashboard_reads(site, config):
    names = set(zipfile.ZipFile(site / "py" / config["bundle"]).namelist())
    for required in ("asi/dashboard/app.py", "asi/results.py", "asi/narrative/store.py",
                     "data/panel/bundle.json", "data/panel/observations.csv",
                     "data/panel/pillar_scores.csv", "data/panel/composites.csv",
                     "narrative/countries/GHA.yaml", "context/colonial_history.yaml",
                     "assets/asi.css"):
        assert required in names, required
    assert not any("__pycache__" in n or n.endswith(".pyc") for n in names)


def test_the_browser_is_given_every_package_the_dashboard_imports():
    """
    Prevents the first build's defect: Dash's dependencies were resolved, the
    dashboard's own were not, and the site shipped without pandas.
    """
    wanted = set(_load_builder().app_distributions())
    assert {"pandas", "numpy", "pyyaml", "dash", "plotly", "dash-bootstrap-components"} <= wanted


# ── The resolver ───────────────────────────────────────────────────────────────

def _fake_lock(**versions) -> dict:
    """A Pyodide lockfile providing the named packages at the given versions."""
    packages = {name: {"name": name, "version": v} for name, v in versions.items()}
    return {"info": {"python": "3.14.2"}, "packages": packages}


PROVIDED = dict(numpy="2.4.6", pandas="3.0.2", pyyaml="6.0.3", pydantic="2.12.5",
                markupsafe="3.0.3", jinja2="3.1.6", requests="2.33.1", setuptools="82.0.1",
                **{"typing-extensions": "4.15.0"}, packaging="26.1", narwhals="2.18.1",
                click="8.3.1", retrying="1.4.2")


def test_the_roots_are_vendored_even_when_pyodide_offers_them():
    """
    The Dash whose JavaScript is copied must be the Dash that answers it, so a
    Pyodide-supplied plotly or dash must never be preferred.
    """
    builder = _load_builder()
    _, vendored = builder.resolve(_fake_lock(**PROVIDED, plotly="6.0.0"),
                                  builder.app_distributions())
    assert {"dash", "dash-bootstrap-components", "plotly"} <= set(vendored)


def test_a_pyodide_package_too_old_for_its_dependents_stops_the_build():
    """Dash needs pydantic>=2.10; offering 2.0 must fail here, not in a browser."""
    builder = _load_builder()
    lock = _fake_lock(**{**PROVIDED, "pydantic": "2.0.0"})
    with pytest.raises(SystemExit, match="pydantic"):
        builder.resolve(lock, builder.app_distributions())


# ── Determinism ────────────────────────────────────────────────────────────────

def test_a_rebuild_is_byte_identical(site, tmp_path):
    """A deploy of an unchanged commit must not be a diff."""
    again = _build(tmp_path / "again")

    def digest(root: Path) -> dict:
        return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(root.rglob("*")) if p.is_file()}

    assert digest(site) == digest(again)
