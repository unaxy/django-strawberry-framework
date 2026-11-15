"""Rebind Strawberry's Relay connection-page check, applied at app load.

``ListConnection.resolve_connection``'s synchronous branch serves an empty page
(no ``edges``, ``hasNextPage: false``) unless
``strawberry/relay/utils.py::should_resolve_list_connection_edges`` answers
``True``, and that check looks for a selection spelled ``edges`` or ``pageInfo``
on the wire. Under a ``NameConverter`` that respells both - a custom converter,
or ``auto_camel_case=False`` with only ``page_info { has_next_page }``
selected - a query that selects the page gets an empty one. The same check also
answers ``True`` for a fragment spread merely named ``edges``.

:func:`apply` rebinds the ``strawberry.relay.types`` global that branch reads to
:func:`_patched_should_resolve_list_connection_edges`, which answers by
``connection.py::_page_requested`` alone: the two fields matched by the Python
names they were declared under. ``strawberry.relay.utils`` keeps its own
binding. The ``DjangoConnection`` offset page reaches the check through
``connection.py::_consume_fallback``; the keyset page in
``connection.py::_resolve_keyset_connection`` asks ``_page_requested`` itself.

:func:`apply` runs once from
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.
It is gated by the ``APPLY_UPSTREAM_PATCHES`` setting (default on):
``DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}`` or
``{"APPLY_UPSTREAM_PATCHES": {"strawberry": False}}`` leaves upstream's check in
place, and the offset page under such a converter serves the empty page again.
A ``ListConnection.resolve_connection`` that no longer reads the global by name
fails :func:`apply` loudly, since the rebind would then change nothing.

Unfixed upstream through ``strawberry-graphql`` 0.341.2: every published release
from 0.322.2 on matches the literal ``{"edges", "pageInfo"}`` against
``selection.name``. Retire the rebind once upstream decides by the schema's own
field names and ignores fragment-spread names.
"""

from types import FunctionType
from typing import TYPE_CHECKING

from strawberry.relay import types as _relay_types

from .conf import upstream_patches_enabled
from .connection import _page_requested
from .utils import truth

if TYPE_CHECKING:
    from strawberry.types import Info

# The ``strawberry.relay.types`` global ``ListConnection.resolve_connection`` calls to
# decide whether a page's rows are selected: imported there from
# ``strawberry.relay.utils`` and read by name at call time, so rebinding it in
# ``strawberry.relay.types`` reaches that call and nothing else.
_EDGES_CHECK = "should_resolve_list_connection_edges"


def _patched_should_resolve_list_connection_edges(info: "Info[object, object]") -> bool:
    """Answer the connection-page check by Python name: ``connection.py::_page_requested``."""
    return _page_requested(info)


def apply() -> None:
    """Rebind the connection-page check, unless ``APPLY_UPSTREAM_PATCHES`` opts out.

    Idempotent: a repeated call rebinds the same function, and one after a third
    party restored upstream's check rebinds it again.
    """
    if not upstream_patches_enabled("strawberry"):
        return
    resolver = truth.stored_function(
        truth.class_dict(_relay_types.ListConnection).get("resolve_connection"),
    )
    if not isinstance(resolver, FunctionType) or _EDGES_CHECK not in resolver.__code__.co_names:
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Strawberry patch: "
            "ListConnection.resolve_connection no longer calls "
            f"strawberry.relay.types.{_EDGES_CHECK}. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"strawberry": False} '
            "or use a supported Strawberry version.",
        )
    setattr(_relay_types, _EDGES_CHECK, _patched_should_resolve_list_connection_edges)
