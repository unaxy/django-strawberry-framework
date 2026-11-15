"""Strawberry's JSON decode seam, answered for every document a client can send.

Strawberry decodes every JSON document a request carries through one method,
``strawberry.http.base.BaseView.decode_json`` (``json.loads``): the HTTP body, the
GET ``variables`` / ``extensions`` parameters and the multipart ``operations`` /
``map`` fields reach it through ``BaseView.parse_json``, and every WebSocket frame
through the Channels adapter's ``iter_json``. Both callers answer a
``json.JSONDecodeError`` and nothing else: ``parse_json`` with
``HTTPException(400, "Unable to parse request body as JSON")``, ``iter_json`` with
``NonJsonMessageReceived`` (the ``graphql-transport-ws`` handler's ``4400`` /
"WebSocket message must be valid JSON"; the legacy ``graphql-ws`` handler drops the
frame).

``json.loads`` also refuses a well-formed document without a ``JSONDecodeError``:
an integer literal longer than CPython's integer string conversion limit
(``sys.get_int_max_str_digits``, 4300 digits by default, present from 3.10.7 on
and configurable per process) raises a plain ``ValueError`` from inside the
scanner, wherever the literal sits in the document. Neither upstream caller
catches it: left alone, a view would answer an unhandled ``500`` and the package
WebSocket consumer would close ``1011`` and log a server-side failure. (A document
nested past the recursion limit raises ``RecursionError`` instead; that one is
answered by ``views.py::_RequestBodyBoundaryMixin.parse_json`` on HTTP and by the consumer's loop
containment on WebSocket, not here.)

:func:`decode_json` is the package's override body for that seam, shared by
``views.py::_RequestBodyBoundaryMixin.decode_json`` (both HTTP views) and the
package WebSocket consumer (``consumers.py::build_revalidating_consumer_class``).
It delegates to upstream's own ``decode_json`` and re-raises that one refusal as
the ``json.JSONDecodeError`` upstream's callers already answer, so the client gets
upstream's own response and literal on every path, and the package writes no
status, message or close of its own. The interpreter's ``ValueError`` rides as
``__cause__``.

The translation is scoped by type, never by message: CPython's text differs
between 3.10 and 3.11+, and a configured limit changes the number in it. It
applies only to an exception of exactly ``ValueError`` (``JSONDecodeError`` and
``UnicodeDecodeError`` are subclasses and pass through untouched).

Package policy, not gated by ``APPLY_UPSTREAM_PATCHES``: the package's resource
policy names this limit as what bounds an integer a request carries and states that
such a request is refused as malformed input (spec-047 Decision 13), so the refusal
holds on every package mount.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ("decode_json",)

#: The ``JSONDecodeError`` message for the translated refusal. Never on the wire:
#: upstream's callers answer with their own literal.
_INTEGER_LIMIT_MESSAGE = (
    "Integer literal exceeds the interpreter's integer string conversion limit"
)


def decode_json(decode: Callable[[str | bytes], object], data: str | bytes) -> object:
    """Return ``decode(data)``, re-raising the integer digit-limit refusal as ``JSONDecodeError``.

    ``decode`` is the caller's ``super().decode_json``. The translated error
    carries no document or position (the scanner reports neither); the
    interpreter's ``ValueError`` is its ``__cause__``.
    """
    try:
        return decode(data)
    except ValueError as exc:
        if type(exc) is not ValueError:
            raise
        raise json.JSONDecodeError(_INTEGER_LIMIT_MESSAGE, "", 0) from exc
