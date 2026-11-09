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
answered by ``_strawberry_patches.py`` on HTTP and by the consumer's loop
containment on WebSocket, not here.)

:func:`decode_json` is the package's override body for that seam, shared by
``views.py::_RequestBodyBoundaryMixin.decode_json`` (both HTTP views) and the
package WebSocket consumer (``consumers.py::build_revalidating_consumer_class``).
It delegates to upstream's own ``decode_json`` and re-raises that one refusal as
the ``json.JSONDecodeError`` upstream's callers already answer, so the client gets
upstream's own response and literal on every path, and the package writes no
status, message or close of its own. The interpreter's ``ValueError`` rides as
``__cause__``.

The translation is scoped by type and provenance, never by message: CPython's text
differs between 3.10 and 3.11+, and a configured limit changes the number in it. It
applies only to an exception of exactly ``ValueError`` (``JSONDecodeError`` and
``UnicodeDecodeError`` are subclasses and pass through untouched) whose traceback
runs through upstream's ``BaseView.decode_json`` frame, the ``json.loads`` call
that frame makes. A ``ValueError`` raised by a consumer's own ``decode_json``
override, or by any other code the delegate reaches, keeps its ``500``.

Permanent package policy, not an upstream-bug workaround riding the
``APPLY_UPSTREAM_PATCHES`` gate: the package's resource policy names this limit as
what bounds an integer a request carries and states that such a request is refused
as malformed input (spec-047 Decision 13), so the refusal must hold on every
package mount whatever that setting says.
"""

from __future__ import annotations

import json
from types import FunctionType
from typing import TYPE_CHECKING

from strawberry.http.base import BaseView

from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import require_instance

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import CodeType

__all__ = ("decode_json",)

#: Upstream's ``decode_json`` body, the frame a translated refusal must have
#: passed through.
_UPSTREAM_DECODE_JSON_CODE: CodeType = require_instance(
    truth.class_dict(BaseView)["decode_json"],
    FunctionType,
).__code__

#: The ``JSONDecodeError`` message for the translated refusal. Never on the wire:
#: upstream's callers answer with their own literal.
_INTEGER_LIMIT_MESSAGE = (
    "Integer literal exceeds the interpreter's integer string conversion limit"
)


def _raised_inside_upstream_decode(exc: BaseException) -> bool:
    """Return ``True`` when ``exc``'s traceback runs through ``BaseView.decode_json``."""
    traceback = exc.__traceback__
    while traceback is not None:
        if traceback.tb_frame.f_code is _UPSTREAM_DECODE_JSON_CODE:
            return True
        traceback = traceback.tb_next
    return False


def decode_json(decode: Callable[[str | bytes], object], data: str | bytes) -> object:
    """Return ``decode(data)``, re-raising the integer digit-limit refusal as ``JSONDecodeError``.

    ``decode`` is the caller's ``super().decode_json``. The translated error
    carries no document or position (the scanner reports neither); the
    interpreter's ``ValueError`` is its ``__cause__``.
    """
    try:
        return decode(data)
    except ValueError as exc:
        if not (truth.is_exact(exc, ValueError) and _raised_inside_upstream_decode(exc)):
            raise
        raise json.JSONDecodeError(_INTEGER_LIMIT_MESSAGE, "", 0) from exc
