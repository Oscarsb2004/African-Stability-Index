"""Citations: where in a stored document a statement comes from."""

from __future__ import annotations

from athena.base import Record
from athena.ids import Id


class Citation(Record):
    """A locator in a stored document, and the quote that must be found verbatim there."""

    document: Id
    locator: str
    quote: str
