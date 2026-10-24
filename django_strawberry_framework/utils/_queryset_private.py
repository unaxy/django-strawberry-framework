"""Typed reads and writes of the ``QuerySet`` and row state Django keeps in private attributes.

The visibility seal, the optimizer and the write pipeline read and rebuild a
queryset's routing (``_db``, ``_hints``), its projection (``_fields``), its
pending prefetches, its deferred filter and its fetch mode. Django keeps all of
these as private ``QuerySet`` attributes that django-stubs does not declare, so
every direct access is an unknown attribute to the type checker. Each one is spelled here
once, under the type Django stores, and every caller goes through these
functions instead of the attribute.

These are attribute reads and writes, so they suit a queryset the framework
built, sealed or already proved a ``QuerySet``. The seal's inspection of an
untrusted consumer queryset must not dispatch consumer code, so it reads the
instance namespace through ``truth.instance_state`` instead
(``django_strawberry_framework/utils/querysets.py::_seal_or_defect``) and comes
here to write the validated state onto the queryset it rebuilds. The fetch mode
is the one state read here too: ``queryset_fetch_mode`` reads it through
``truth.instance_state`` and admits only Django's own modes
(``is_django_fetch_mode``), so the write pipeline's base-manager read carries
what the seal already validated.

The model-row state Django's queryset iterators set lives here too: the
``_state.peers`` list of weak references an iteration under a peer-tracking
fetch mode shares across the rows it yields. A row may come from a consumer
``resolve_nodes`` override, so the read goes through ``truth.instance_state``
and dispatches nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeGuard, TypeVar

from . import truth
from .imports import import_attr_if_importable

if TYPE_CHECKING:
    import weakref
    from typing import TypeAlias

    from django.db import models
    from django.db.models import Prefetch
    from django.db.models.fetch_modes import FetchMode
    from django.db.models.sql import Query

    #: One ``prefetch_related`` lookup as Django stores it: a lookup path or a ``Prefetch``.
    PrefetchLookup: TypeAlias = str | Prefetch[str]
    #: ``QuerySet._deferred_filter``: the ``(negate, args, kwargs)`` of a filter Django
    #: applies on the next ``query`` read, or ``None`` when none is pending.
    DeferredFilter: TypeAlias = tuple[bool, tuple[object, ...], dict[str, object]]

_QuerySetT = TypeVar("_QuerySetT", bound="models.QuerySet[models.Model, object]")


def queryset_db(queryset: models.QuerySet[models.Model, object]) -> str | None:
    """Return the alias ``using()`` pinned, or ``None`` when the router decides."""
    # basedpyright: django-stubs omits QuerySet._db, reported as an unknown attribute
    return queryset._db  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]


def set_queryset_db(queryset: models.QuerySet[models.Model, object], alias: str | None) -> None:
    """Pin ``queryset`` to ``alias`` without the clone ``using()`` makes."""
    # basedpyright: django-stubs omits QuerySet._db, reported as an unknown attribute
    queryset._db = alias  # pyright: ignore[reportAttributeAccessIssue]


def queryset_hints(queryset: models.QuerySet[models.Model, object]) -> dict[str, object]:
    """Return the router hints dict ``queryset`` holds (the object itself, not a copy)."""
    # basedpyright: django-stubs omits QuerySet._hints, reported as an unknown attribute
    return queryset._hints  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]


def set_queryset_hints(
    queryset: models.QuerySet[models.Model, object],
    hints: dict[str, object],
) -> None:
    """Replace the router hints dict ``queryset`` holds."""
    # basedpyright: django-stubs omits QuerySet._hints, reported as an unknown attribute
    queryset._hints = hints  # pyright: ignore[reportAttributeAccessIssue]


def queryset_fields(queryset: models.QuerySet[models.Model, object]) -> tuple[str, ...] | None:
    """Return the ``values()`` / ``values_list()`` field names, or ``None`` for model rows."""
    # basedpyright: django-stubs omits QuerySet._fields, reported as an unknown attribute
    return queryset._fields  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]


def set_queryset_fields(
    queryset: models.QuerySet[models.Model, object],
    fields: tuple[str, ...] | None,
) -> None:
    """Set the ``values()`` / ``values_list()`` field names ``queryset`` projects."""
    # basedpyright: django-stubs omits QuerySet._fields, reported as an unknown attribute
    queryset._fields = fields  # pyright: ignore[reportAttributeAccessIssue]


def queryset_prefetch_lookups(
    queryset: models.QuerySet[models.Model, object],
) -> tuple[PrefetchLookup, ...]:
    """Return the ``prefetch_related`` lookups ``queryset`` will run, in order."""
    # basedpyright: django-stubs omits QuerySet._prefetch_related_lookups, reported as an
    # unknown attribute
    return queryset._prefetch_related_lookups  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]


def set_queryset_prefetch_lookups(
    queryset: models.QuerySet[models.Model, object],
    lookups: tuple[PrefetchLookup, ...],
) -> None:
    """Replace the ``prefetch_related`` lookups ``queryset`` will run."""
    # basedpyright: django-stubs omits QuerySet._prefetch_related_lookups, reported as an
    # unknown attribute
    queryset._prefetch_related_lookups = lookups  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_deferred_filter(
    queryset: models.QuerySet[models.Model, object],
    deferred: DeferredFilter | None,
) -> None:
    """Set the filter Django applies to ``queryset`` on its next ``query`` read."""
    # basedpyright: django-stubs omits QuerySet._deferred_filter, reported as an unknown attribute
    queryset._deferred_filter = deferred  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_defer_next_filter(
    queryset: models.QuerySet[models.Model, object],
    *,
    defer: bool,
) -> None:
    """Set whether ``queryset``'s next ``filter()`` is deferred instead of applied."""
    # basedpyright: django-stubs omits QuerySet._defer_next_filter, reported as an unknown
    # attribute
    queryset._defer_next_filter = defer  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_sticky_filter(
    queryset: models.QuerySet[models.Model, object],
    *,
    sticky: bool,
) -> None:
    """Set whether ``queryset``'s next two ``filter()`` calls share their multi-valued joins."""
    # basedpyright: django-stubs omits QuerySet._sticky_filter, reported as an unknown attribute
    queryset._sticky_filter = sticky  # pyright: ignore[reportAttributeAccessIssue]


def set_queryset_for_write(
    queryset: models.QuerySet[models.Model, object],
    *,
    for_write: bool,
) -> None:
    """Set whether ``queryset`` routes through the router's write alias."""
    # basedpyright: django-stubs omits QuerySet._for_write, reported as an unknown attribute
    queryset._for_write = for_write  # pyright: ignore[reportAttributeAccessIssue]


def _django_fetch_mode_classes() -> truth.IdentitySet[type[object]]:
    """Return Django's own fetch-mode classes, empty on a release without fetch modes.

    Django 6.1 added ``QuerySet.fetch_mode`` and ``django.db.models.fetch_modes``;
    ``FETCH_ONE`` / ``FETCH_PEERS`` / ``FETCH_RAISE`` are the one stateless instance
    of each class (``__slots__ = ()``), so an instance of exactly one of these
    classes behaves as that singleton. Below 6.1 the module does not exist, no
    queryset carries ``_fetch_mode``, and the set is never consulted.
    """
    classes: list[type[object]] = []
    for class_name in ("FetchOne", "FetchPeers", "FetchRaise"):
        fetch_mode_class = import_attr_if_importable("django.db.models.fetch_modes", class_name)
        if truth.is_type(fetch_mode_class):
            classes.append(fetch_mode_class)
    return truth.IdentitySet(classes)


# The fetch modes the framework carries from one queryset onto another it builds: an
# instance of exactly one of Django's own fetch-mode classes. ``FetchMode.fetch`` runs on
# every deferred-field and relation load of every row the queryset yields, so anything
# else (a ``FetchMode`` subclass, a foreign object) is consumer code at row-load time.
_DJANGO_FETCH_MODE_CLASSES = _django_fetch_mode_classes()


def is_django_fetch_mode(value: object) -> TypeGuard[FetchMode]:
    """Return whether ``value`` is an instance of exactly one of Django's own fetch-mode classes."""
    return truth.is_exact_one_of(value, _DJANGO_FETCH_MODE_CLASSES)


def queryset_fetch_mode(queryset: models.QuerySet[models.Model, object]) -> FetchMode | None:
    """Return ``queryset``'s fetch mode when it is one of Django's own, else ``None``.

    ``None`` below Django 6.1, where no queryset carries one. The slot is read from the
    instance namespace (``truth.instance_state``), so the read dispatches nothing.
    """
    fetch_mode = truth.instance_state(queryset).get("_fetch_mode")
    return fetch_mode if is_django_fetch_mode(fetch_mode) else None


def set_queryset_fetch_mode(
    queryset: models.QuerySet[models.Model, object],
    fetch_mode: FetchMode,
) -> None:
    """Set the fetch mode ``queryset``'s rows load their deferred fields and relations under."""
    # django-stubs omits ``QuerySet._fetch_mode``; the base ``object.__setattr__`` writes
    # the instance attribute the type checker cannot see, as ``QuerySet.fetch_mode`` does.
    object.__setattr__(queryset, "_fetch_mode", fetch_mode)


def _model_row_state(row: models.Model) -> dict[str, object]:
    """Return the instance namespace of ``row``'s ``ModelState``, read without dispatch."""
    return truth.instance_state(truth.instance_state(row)["_state"])


def model_row_peers(row: models.Model) -> object | None:
    """Return the peers list ``row``'s queryset iteration shares across its rows, or ``None``.

    ``None`` for a row whose ``_state.peers`` is ``ModelState``'s class default ``()``:
    one no peer-tracking iteration yielded, or one copied or unpickled since
    (``ModelState.__getstate__`` drops the weak references).
    """
    return _model_row_state(row).get("peers")


def set_model_row_peers(
    row: models.Model,
    peers: list[weakref.ReferenceType[models.Model]],
) -> None:
    """Set the rows ``row`` batches its deferred and relation loads with under a peer-tracking mode."""
    row._state.peers = peers


def set_queryset_query(queryset: models.QuerySet[models.Model, object], query: Query) -> None:
    """Replace the ``Query`` ``queryset`` holds, past the ``query`` property's setter.

    The setter also switches ``_iterable_class`` for a ``values()`` query, and the
    getter applies a pending deferred filter; this write does neither.
    """
    # basedpyright: django-stubs omits QuerySet._query, reported as an unknown attribute
    queryset._query = query  # pyright: ignore[reportAttributeAccessIssue]


def super_clone_queryset(owner: type[_QuerySetT], queryset: _QuerySetT) -> _QuerySetT:
    """Return ``super(owner, queryset)._clone()``: the clone the class after ``owner`` makes.

    For a ``QuerySet`` subclass's own ``_clone`` override, which extends the copy its
    superclass makes.
    """
    # basedpyright: django-stubs omits QuerySet._clone, reported as an unknown attribute
    return super(owner, queryset)._clone()  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]


def chain_queryset(queryset: _QuerySetT) -> _QuerySetT:
    """Return Django's ``_chain()`` clone of ``queryset``: same class, same state."""
    # basedpyright: django-stubs omits QuerySet._chain, reported as an unknown attribute
    return queryset._chain()  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]
