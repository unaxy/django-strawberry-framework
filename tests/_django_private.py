"""Typed views of Django's private attributes that django-stubs omits.

Tests read a few attributes Django defines but its stubs never declare, so a plain read
reports an unknown attribute
(``reportAttributeAccessIssue``). Each ``has_*`` accessor narrows the object to a
declaration-only subclass of the real class that adds the one attribute; the subclasses
exist for the checker alone (they sit under ``TYPE_CHECKING`` and are never instantiated).
The narrowing is a real run-time check that the attribute exists, so a Django release that
drops it fails at the ``assert has_x(obj)`` line rather than as a bare ``AttributeError``
deeper in the test. ``TypeIs`` over a ``Protocol`` that does not subclass the real class is
rejected, so every view subclasses the class it narrows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from django.db.models import (
    Manager,
    Model,
    QuerySet,
)
from django.http import HttpRequest

if TYPE_CHECKING:
    from typing_extensions import TypeIs

_M = TypeVar("_M", bound=Model)
_QuerySetT = TypeVar("_QuerySetT", bound="QuerySet[Model, object]")

if TYPE_CHECKING:

    class HttpRequestWithReadState(HttpRequest):
        """An ``HttpRequest`` carrying the flag ``HttpRequest.read`` sets on first read."""

        _read_started: bool

    class ModelWithPrefetchCache(Model):
        """A model row carrying the cache ``prefetch_related_objects`` fills."""

        _prefetched_objects_cache: dict[str, QuerySet[Model, object]]

    class ManagerWithRelFilters(Manager[_M]):
        """A related manager carrying the ``_apply_rel_filters`` method Django binds on it."""

        def _apply_rel_filters(self, _queryset: _QuerySetT) -> _QuerySetT: ...


def has_read_started(request: HttpRequest) -> TypeIs[HttpRequestWithReadState]:
    """Return whether ``request`` carries ``_read_started``."""
    return hasattr(request, "_read_started")


def has_prefetched_objects_cache(row: Model) -> TypeIs[ModelWithPrefetchCache]:
    """Return whether ``row`` carries ``_prefetched_objects_cache``."""
    return hasattr(row, "_prefetched_objects_cache")


def has_apply_rel_filters(manager: Manager[_M]) -> TypeIs[ManagerWithRelFilters[_M]]:
    """Return whether ``manager`` carries the ``_apply_rel_filters`` method."""
    return hasattr(manager, "_apply_rel_filters")
