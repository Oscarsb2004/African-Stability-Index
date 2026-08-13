"""
Callback wiring.

These exist because of a real failure: the navigation callback declared a plain
`Input("year-slider", ...)`, but the year slider is rendered inside the country
page rather than in the base layout. Dash refuses to run a callback whose Input
names a component absent from the current layout, so on the overview page — the
only page from which a country can be opened — navigation silently did nothing
and the console filled with "A nonexistent object was used in an `Input`".

The rule that prevents it: a callback may reference a plain string id only if
that component is always present. Anything rendered into `content` must use a
pattern-matching id, which matches zero components without error.
"""

import json

import pytest

from asi.dashboard.app import build_layout, create_app


def _walk(component):
    """Yield every component in a layout tree."""
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if hasattr(child, "children") or hasattr(child, "id"):
            yield from _walk(child)


@pytest.fixture(scope="module")
def base_layout_ids() -> set[str]:
    """Ids that exist no matter which tab or level is being shown."""
    ids = set()
    for c in _walk(build_layout()):
        cid = getattr(c, "id", None)
        if isinstance(cid, str):
            ids.add(cid)
    return ids


@pytest.fixture(scope="module")
def app():
    return create_app()


def _dependencies(app):
    for key, spec in app.callback_map.items():
        yield key, list(spec.get("inputs", [])) + list(spec.get("state", []))


def test_every_plain_input_id_is_always_present(app, base_layout_ids):
    """
    The regression itself. A plain id that only exists inside `content` breaks
    every callback that names it, on every page where it is absent.
    """
    offenders = []
    for output, deps in _dependencies(app):
        for dep in deps:
            cid = dep["id"]
            if isinstance(cid, str) and not cid.startswith("{"):
                if cid not in base_layout_ids:
                    offenders.append(f"{output} <- {cid}")
    assert not offenders, (
        "callbacks reference plain ids that are not in the base layout; "
        "use a pattern-matching id for components rendered into `content`: "
        + "; ".join(offenders)
    )


@pytest.mark.parametrize("component", ["ov-map", "year-slider"])
def test_dynamic_components_use_pattern_matching_ids(app, component):
    """
    Both of these live inside `content` — the map only on Explore, the slider
    only on country pages — so both must be matched by pattern.
    """
    seen = []
    for _, deps in _dependencies(app):
        for dep in deps:
            cid = dep["id"]
            if isinstance(cid, str) and cid.startswith("{"):
                parsed = json.loads(cid)
                if parsed.get("type") == component:
                    seen.append(parsed)
            elif isinstance(cid, dict) and cid.get("type") == component:
                seen.append(cid)
    assert seen, f"{component} is not referenced by any pattern-matching callback"


def test_content_and_stores_are_in_the_base_layout(base_layout_ids):
    """The containers the callbacks write into must never be conditional."""
    for required in ("content", "nav", "map-click", "nav-event", "tabs"):
        assert required in base_layout_ids
