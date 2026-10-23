"""``DjangoVisibilityExplainExtension`` - which visibility rules fired, per operation.

The per-operation half of the rules inspector (the static half is
``manage.py inspect_rules``). While an operation runs, the framework-owned
enforcement body (``rules/apply.py``) records one event per type it scopes:
which schema bypass granted everything, or which rules filtered the rows and
whether the forward-FK cascade walked the type's edges. The events are returned
under ``extensions["visibility"]`` so a client (or a test) can read, for the
actor that made the request, exactly where each rule was enforced.

Prototype: no caps, no fail-closed gate, development schemas only. The shipped
``DjangoDebugExtension`` shows the posture a real version must adopt.

Opt in with the class in ``extensions=``::

    schema = DjangoSchema(query=Query, extensions=[DjangoVisibilityExplainExtension])
"""

from __future__ import annotations

from collections.abc import Iterator
from contextvars import ContextVar

from strawberry.extensions.base_extension import SchemaExtension
from typing_extensions import override

__all__ = ["DjangoVisibilityExplainExtension", "record"]

_events: ContextVar[list[dict[str, object]] | None] = ContextVar("visibility_events", default=None)


def record(event: dict[str, object]) -> None:
    """Append ``event`` to the operation's trace when an explain extension is listening."""
    events = _events.get()
    if events is not None:
        events.append(event)


class DjangoVisibilityExplainExtension(SchemaExtension):
    """Return the operation's visibility-rule trace under ``extensions["visibility"]``."""

    @override
    def on_operation(self) -> Iterator[None]:
        """Open a fresh trace for this operation and close it on teardown."""
        token = _events.set([])
        try:
            yield
        finally:
            self._trace = _events.get() or []
            _events.reset(token)

    @override
    def get_results(self) -> dict[str, list[dict[str, object]]]:
        """The recorded events, in enforcement order."""
        return {"visibility": list(getattr(self, "_trace", []))}
