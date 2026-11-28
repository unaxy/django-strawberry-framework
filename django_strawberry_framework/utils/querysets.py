"""Shared query-source, field-coercion, sync/async hook, and visibility contracts.

The neutral query-source mechanics every resolver surface shares: coerce a
``Manager`` to a ``QuerySet`` exactly once, decide whether a value is a
queryset, run the ``DjangoType.get_queryset`` visibility hook through the sync
or async path, and combine those into the list-field consumer-resolver shape.
Every surface reaches ONE implementation of the contract --
``get_queryset`` is the visibility hook, and a visibility-hook mistake is a
data-leak bug, so the routing must not be re-decided per surface.

``coerce_field_value_or_none`` is the sibling neutral
primitive for the "raw literal -> Django field value, or nothing" safety
wrapper every raw-identity decode needs against a DIFFERENT field -
single-sourcing the coercion mechanics while leaving the field selection to
each caller.

``run_in_one_sync_boundary`` is the sibling neutral
primitive for "run a sync callable in exactly one
``sync_to_async(thread_sensitive=True)`` worker", so the off-event-loop
boundary cannot drift.

The two colored visibility runners are the package's hardened ``get_queryset``
security boundary (the get_queryset-visibility-boundary decision): every
framework-owned invocation of the hook routes through them, so source
preparation and result normalization live in exactly one place rather than per
surface.

The boundary's seal (``_seal_or_defect``) is a clone and a shape check, not a
proof: the hook is application Python and is trusted (GOAL.md "Trust
boundary"), so the seal catches the mistakes a hook can make by accident and
hands the surface a fresh clone (``QuerySet.all()``) of what the hook returned.
The clone keeps the queryset's own class, drops any fetched rows, and bakes a
related manager's pending filter, so a surface never windows stale or shared
rows and never composes onto the hook's own object. The checks refuse a value
that is not a ``QuerySet``, a queryset over another table, a sliced query a
surface would recompose onto, a projection where model rows are required, a
queryset routed off the resolution's alias, and a ``Prefetch`` child, at any
depth, over a model its relation does not target or routed off that alias. A
``union()`` / ``intersection()`` / ``difference()`` is served as the set of
primary keys it selects, rewritten as a ``pk__in`` membership test the
recomposing surfaces can narrow; a combinator with a branch over another model,
or whose rows that rewrite would change, fails closed.

Caller-specific tails stay with their caller: the connection field keeps its
GraphQL non-queryset error (it calls ``normalize_query_source`` then guards),
the Relay node defaults keep their id filter, the optimizer keeps plan
building, and the filter related derive keeps its per-branch recursion. This
module owns only the source normalization + the colored visibility calls.

Cycle-safe by construction: it depends on ``django``, ``asgiref``, ``..conf``,
``..exceptions``, ``..registry`` and its own ``utils`` siblings (the
write-transaction ContextVar helpers among them), so ``types/relay.py``
(imported at module top by ``types/base.py``) can import from here without
closing a load cycle, and it never imports back into filters / orders /
mutations / permissions.
"""

from __future__ import annotations

import asyncio
import copy
import dataclasses
import datetime
import inspect
import math
import sys
from collections.abc import AsyncIterable, Iterable
from collections.abc import Set as AbstractSet
from decimal import Context as DecimalContext
from decimal import Decimal, InvalidOperation
from typing import (
    TYPE_CHECKING,
    Generic,
    Literal,
    ParamSpec,
    TypeGuard,
    TypeVar,
    cast,
    overload,
)

from asgiref.sync import sync_to_async
from django.core.exceptions import FieldDoesNotExist, FieldError, ValidationError
from django.db import connections, models, router
from django.db.models import sql
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import (
    BaseExpression,
    Combinable,
    Exists,
    Expression,
    F,
    OrderBy,
)
from django.db.models.manager import BaseManager
from django.db.models.options import Options
from django.db.models.query import (
    ModelIterable,
)

from django_strawberry_framework.conf import django_setting
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry

from . import introspection
from ._narrowing import (
    instance_state,
    is_awaitable,
    is_class,
    is_exact_dict,
    is_queryset,
    is_str,
    pk_of,
    read_attr,
    require,
)
from ._queryset_private import (
    clear_queryset_known_related_objects,
    queryset_db,
    queryset_hints,
    queryset_prefetch_lookups,
    set_queryset_hints,
)
from .errors import (
    _PROHIBIT_NULL_CHARACTERS,
    binds_integer,
    datetime_django_binds,
    refuses_numeric_format,
    unbindable_temporal,
)
from .lazy import unwrap_lazy_object
from .relations import (
    generated_column,
    leading_relation_hops,
    order_column_paths,
    reverse_relation_by_accessor,
    stored_value_column,
)
from .typing import is_async_callable, object_result
from .write_transaction import (
    current_write_pipeline,
    pin_write_queryset,
    pipeline_rows_visible_after_lock,
    pipeline_scoped_queryset,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
    from typing import Literal, Protocol, TypeAlias

    from django.db.backends.base.base import BaseDatabaseWrapper
    from typing_extensions import TypeIs

    from django_strawberry_framework.filters.sets import FilterSet
    from django_strawberry_framework.orders.sets import OrderSet
    from django_strawberry_framework.types.base import DjangoType

    from ._queryset_private import PrefetchLookup
    from .typing import ConcreteField, ModelField

    #: Any model's ``Options``.
    _OptionsAny: TypeAlias = Options[models.Model]
    #: A resolver source after ``Manager`` coercion: a ``QuerySet`` flagged ``True``, or
    #: any other value (a list, a generator) flagged ``False``. The flag discriminates
    #: the union, so ``source[1] is True`` narrows ``source[0]`` to the queryset.
    NormalizedSource: TypeAlias = (
        tuple[models.QuerySet[models.Model, object], Literal[True]] | tuple[object, Literal[False]]
    )

    class _JoinColumn(Protocol):
        """One side of a join's column pair, as ``Join.join_cols`` reads it."""

        @property
        def column(self) -> object: ...

    class _JoiningRelation(Protocol):
        """A path step's ``join_field``: the relation (or reverse relation) a join follows."""

        @property
        def null(self) -> bool: ...

        def get_joining_fields(self) -> tuple[tuple[_JoinColumn, _JoinColumn], ...]: ...

    class _PathStep(Protocol):
        """One ``PathInfo`` step of ``Query.names_to_path``, as the order-name readers read it."""

        @property
        def to_opts(self) -> Options[models.Model]: ...

        @property
        def join_field(self) -> _JoiningRelation: ...

        @property
        def m2m(self) -> bool: ...

        @property
        def direct(self) -> bool: ...

    def is_manager(_value: object, /) -> TypeIs[BaseManager[models.Model]]:
        """Return whether the value is a model manager (a related manager included).

        ``BaseManager`` rather than ``Manager``: Django builds a related manager by
        subclassing the target's default manager class, which a
        ``BaseManager.from_queryset(...)`` declaration leaves outside ``Manager``.
        """
        ...

else:
    # ``Options`` has no ``__class_getitem__`` at runtime (only the ``django_stubs_ext``
    # patch adds one): the hint stays the class.
    _OptionsAny = Options
    is_manager = BaseManager.__instancecheck__

_T = TypeVar("_T")
_QuerySetT = TypeVar("_QuerySetT", bound=models.QuerySet[models.Model, object])
_R = TypeVar("_R")
_P = ParamSpec("_P")
_ModelT = TypeVar("_ModelT", bound=models.Model)
_RowT = TypeVar("_RowT")
_RowT_co = TypeVar("_RowT_co", covariant=True)


class SyncMisuseError(ConfigurationError, RuntimeError):
    """Raised when a sync resolver context encounters an async ``get_queryset``.

    Typed marker for the "async ``get_queryset`` hook invoked from a
    sync resolver" misuse. Multiple-inherits ``ConfigurationError``
    AND ``RuntimeError`` so callers catching either base class still
    match:

    - ``except ConfigurationError`` (the package's convention for
      configuration-time errors).
    - ``except RuntimeError`` (consumer code catching ``RuntimeError``
      after the ``FilterSet.apply`` dispatcher rethrow continues to
      work).

    The dispatcher in ``filters/sets.py::FilterSet.apply`` catches
    this subclass directly. Consumers who want a focused catch should
    also match the subclass. Exported through
    ``django_strawberry_framework`` (and re-exported from
    ``django_strawberry_framework.types.relay``) so it
    can be imported without reaching into this private ``utils`` module.
    """


def reject_async_in_sync_context(
    value: Awaitable[object] | _T,
    *,
    owner: str,
    method: str,
    context: str,
    recourse: str,
) -> _T:
    """Guard a synchronous hook result against any awaitable return.

    The caller is a sync seam invoking a consumer-overridable hook. It cannot
    await, so an ``async def`` override returns an orphaned coroutine; treating
    that truthy coroutine as success would be a silent bug - an authorization
    BYPASS for a permission hook - so it is rejected loudly.

    Native coroutines are closed and futures are cancelled before
    ``SyncMisuseError`` is raised; other awaitables have no standard cleanup
    protocol. The error names a native coroutine ``a coroutine`` and any other
    awaitable ``an awaitable``.
    Otherwise ``value`` is returned unchanged, so callers read
    ``x = reject_async_in_sync_context(x, ...)``.
    """
    if inspect.isawaitable(value):
        kind = "a coroutine" if inspect.iscoroutine(value) else "an awaitable"
        _dispose_sync_awaitable(value)
        raise SyncMisuseError(
            f"{owner}.{method} returned {kind} in a sync {context} context. {recourse}",
        )
    return value


def _disposed_awaitable(value: object) -> bool:
    """Return whether ``value`` was an awaitable, DISPOSING it when it was.

    The shared half of every awaitable refusal in the package: detect, then
    close the coroutine / cancel the future so no "coroutine was never awaited"
    warning escapes.

    The raise deliberately stays at the caller. The ``SyncMisuseError`` versus
    ``ConfigurationError`` split is a documented contract (``SyncMisuseError``
    is reserved for sync boundaries), and the prose differs per seam - but the
    load-bearing reason is the hot path: these guards run on every sync
    resolver return, and threading the message through a shared refuser would
    build the f-string on every non-awaitable call. Here the message is
    constructed only when one is actually raised.
    """
    if not inspect.isawaitable(value):
        return False
    _dispose_sync_awaitable(value)
    return True


def _dispose_sync_awaitable(value: object) -> None:
    """Release a rejected awaitable without awaiting it, when possible.

    Native coroutines are closed and futures cancelled; other awaitables have
    no standard cleanup protocol. Used by every boundary that refuses an
    awaitable - the sync misuse guards AND the async runners' nested /
    residual awaitable rejections (those must not recursively await an
    unbounded chain, so disposal is the only safe handling there too).
    """
    if inspect.iscoroutine(value):
        value.close()
    elif asyncio.isfuture(value):
        _ = value.cancel()


def model_for(type_cls: type[DjangoType]) -> type[models.Model]:
    """Return the Django model registered to a ``DjangoType``.

    Centralizes the ``type_cls.__django_strawberry_definition__.model`` lookup
    so every model-only read shares one source of truth with the
    queryset-variant seed below - the Relay node / id helpers, the connection
    total-order derive, the write pipeline's target-model reads, and the
    cascade-permission walk. Callers are responsible for ``type_cls`` being a
    registered ``DjangoType``; a missing definition surfaces as a raw
    ``AttributeError``.
    """
    return type_cls.__django_strawberry_definition__.model


def base_queryset(model: type[_ModelT], *, using: str | None = None) -> models.QuerySet[_ModelT]:
    """Return a fresh unevaluated base queryset for ``model``, optionally alias-pinned.

    The MODEL-keyed ``_default_manager`` seed of a read that starts at ``model``
    (a root list or connection, a Relay id lookup, a write's target rows, a
    many-side relation's planned child, which Django's own related managers read
    through the default manager's class). ``initial_queryset`` is its TYPE-keyed
    wrapper. A read that reaches ``model`` across a relation seeds from
    :func:`related_queryset` instead.

    ``using`` pins the seed to a database alias: a sharded parent must seed
    its children on the SAME connection, and the conditional-on-``None`` shape
    was being written out at each such site.

    An abstract model has no default manager, so it raises ``ConfigurationError``
    naming the model: a ``DjangoType`` over an abstract model serves rows only
    from a consumer resolver that returns concrete instances.
    """
    if model._meta.abstract:
        raise ConfigurationError(
            f"{introspection.name(model)} is an abstract model and has no default manager to seed a "
            f"queryset from. Point Meta.model at a concrete model, or resolve the field with "
            f"a custom resolver that returns concrete rows.",
        )
    manager = model._default_manager
    return manager.using(using).all() if using is not None else manager.all()


def _yields_model_rows(
    value: models.QuerySet[models.Model, object],
) -> TypeGuard[models.QuerySet[models.Model]]:
    """Whether ``value``'s own ``_iterable_class`` is a ``ModelIterable``.

    ``QuerySet.__init__`` stores the row iterable on the instance, and a subclass
    ``__init__`` may store another: django-polymorphic's ``PolymorphicModelIterable`` (a
    ``ModelIterable``, so model rows), or a projection's ``Values*`` iterable (no model
    rows). The class alone proves no row type. Read from the instance ``__dict__``, so a
    class-level property dispatches nothing.
    """
    iterable = instance_state(value).get("_iterable_class")
    return is_class(iterable) and issubclass(iterable, ModelIterable)


def related_queryset(
    model: type[models.Model],
    *,
    using: str | None = None,
) -> models.QuerySet[models.Model]:
    """Return a fresh unevaluated queryset of every ``model`` row, in its default manager's class.

    The MODEL-keyed seed of a read that reaches ``model`` across a relation: a
    declared or undeclared ``FilterSet`` hop, a related ordering, the cascade's
    per-edge base and a planned or re-checked single-valued relation, each
    before the target type's ``get_queryset`` runs. A join reads no manager (a
    filter, an ordering or a subquery across a relation sees every row of the
    table), and Django loads a single related row through ``_base_manager``,
    which its documentation requires never filter rows away. A filtered
    ``_default_manager`` is not a visibility rule (that is a model's declared
    rule or a type's ``get_queryset``), so the manager's own ``get_queryset``
    override contributes only its class here: no filter, annotation, ordering
    or other query state.

    The class is the one the model's default manager returns
    (``MyQuerySet.as_manager()``, ``Manager.from_queryset(MyQuerySet)``, or a
    ``get_queryset`` that builds a class of its own), read from the queryset
    :func:`base_queryset` hands back, so a hook can call that class's methods.
    The rows are a fresh instance of that class, constructed the way Django's
    ``BaseManager.get_queryset`` constructs one (``model``, the alias and the
    manager's ``hints``; the class's own ``__init__`` runs). An ``__init__`` that
    leaves a row iterable other than a ``ModelIterable`` (rows that are no model
    instances) raises ``ConfigurationError`` naming the model, the class and the
    iterable. A ``Meta.base_manager_name`` is not read:
    Django documents that a base manager must not filter, and the rows here are
    the join's. ``using`` pins the seed to
    a database alias, as :func:`base_queryset`'s does; unpinned, the manager's
    own alias stands. An abstract model raises :func:`base_queryset`'s
    ``ConfigurationError``.
    """
    # The manager's override runs (trusted project code) only to name its class and alias.
    supplied = base_queryset(model)
    queryset_class = require(type(supplied), _is_queryset_class)
    rows = queryset_class(model=model, using=using if using is not None else queryset_db(supplied))
    if not _yields_model_rows(rows):
        iterable = instance_state(rows).get("_iterable_class")
        raise ConfigurationError(
            f"{introspection.name(model)}'s default manager returns "
            f"{introspection.name(queryset_class)}, whose "
            f"__init__ leaves the row iterable {introspection.name(iterable)}. A relation's rows are "
            f"model instances: the QuerySet class must keep a ModelIterable row iterable.",
        )
    set_queryset_hints(rows, dict(queryset_hints(supplied)))
    return rows


#: Which collection ``SQLCompiler._order_by_pairs`` selects as the ordering it emits.
ORDER_FROM_EXTRA = "extra"
ORDER_FROM_EXPLICIT = "explicit"
ORDER_FROM_MODEL_DEFAULT = "model_default"
ORDER_FROM_NOTHING = "nothing"


def selected_order(
    query: sql.Query,
    model: type[models.Model],
) -> tuple[str, tuple[str | Combinable, ...]]:
    """Return the ordering collection Django compiles for ``query``, as ``(source, terms)``.

    ``django/db/models/sql/compiler.py::SQLCompiler._order_by_pairs`` picks ONE
    collection and ignores the rest: an ``extra(order_by=...)`` ordering wins
    outright, an explicit ``order_by`` comes next, and the model's
    ``Meta.ordering`` is reached only when nothing explicit was set and
    ``query.default_ordering`` stands (a bare ``.order_by()`` clears it). They
    are alternatives, never a union, so a term left in a collection Django did
    not pick is dormant and reaches no SQL. ``source`` is one of the
    ``ORDER_FROM_*`` names. Django reads the ordering option by truthiness, so
    ``Meta.ordering = None`` - the idiom for clearing an abstract parent's
    ordering - is no default order, never an iterable. ``model`` is the
    caller's model rather than ``query.get_meta()``, so a connection's
    plan-time and resolve-time orders derive from one model read.

    Read under the forward flag: a ``.reverse()``'d query (``standard_ordering``
    False) compiles each of these terms flipped.
    """
    if query.extra_order_by:
        return ORDER_FROM_EXTRA, tuple(query.extra_order_by)
    if query.order_by:
        return ORDER_FROM_EXPLICIT, tuple(query.order_by)
    if query.default_ordering and model._meta.ordering:
        return ORDER_FROM_MODEL_DEFAULT, tuple(model._meta.ordering)
    return ORDER_FROM_NOTHING, ()


class _UnexpandableOrderError(Exception):
    """An order name the compiler reads as written: it rejects the expansion, or cannot run it."""


def _names_to_path(
    query: sql.Query,
    names: Sequence[str],
    opts: _OptionsAny,
) -> tuple[list[_PathStep], ModelField, tuple[object, ...], Sequence[str]]:
    """Return ``query.names_to_path(names, opts, allow_many=True, fail_on_missing=False)``.

    django-stubs types the path steps and the final field ``Any``; Django returns the
    ``PathInfo`` steps, the field the last resolved name names, its targets, and the
    names left over.
    """
    return query.names_to_path(names, opts, allow_many=True, fail_on_missing=False)


def lookup_target_fields(query: sql.Query, lookup: str) -> tuple[object, ...]:
    """Return the fields a filter on ``lookup`` holds its value to, over ``query``; ``()`` for none.

    Resolved the way ``django/db/models/sql/query.py::Query.build_filter`` resolves a
    filter argument: ``Query.solve_lookup_type`` splits ``lookup`` into the field path
    and the transforms and lookup left over, reading a name ``query`` annotates or
    aliases (``Query.annotations``) at the start of the path as that expression and a
    name past a relation as a name of the related model (``_solve_lookup_type``), and
    the field path is then walked by ``Query.names_to_path``, the walk
    ``Query.setup_joins`` runs, which reads ``pk`` as the primary key, a
    ``FilteredRelation`` alias ``query`` holds as its relation and a field on a concrete
    parent through the parent hop. The fields are the walk's targets: the column a path
    ending on a field names (``occurred_at`` for ``occurred_at__year``), or the fields
    of the model the last hop of a path ending on a relation reaches that the join
    compares. An annotation's is its ``output_field``. ``()`` where Django refuses the
    path (``FieldError``: a name naming nothing, a generic foreign key hop, an
    expression whose output field Django cannot resolve).
    """
    try:
        query, _lookups, field_parts, expression = _solve_lookup_type(query, lookup)
        if expression is not False:
            return (read_attr(expression, "output_field"),)
        return _names_to_path(query, field_parts, query.get_meta())[2]
    except FieldError:
        return ()


def _solve_lookup_type(
    query: sql.Query,
    lookup: str,
) -> tuple[sql.Query, Sequence[str], Sequence[str], Expression | Literal[False]]:
    """Return ``query.solve_lookup_type(lookup)`` with no annotation read past a relation, and its query.

    ``Query.names_to_path`` reads a name the model a relation reaches has no field for as
    the ``query``'s own selected annotation of that name (``Query.annotation_select``) at
    any position of the path, though the annotation is an expression over ``query``'s
    model, never over the rows past the hop: a name a relation reaches is a name of the
    related model. A path ending on such a name is walked again over a clone of ``query``
    selecting no annotation (``Query.set_annotation_mask``, the mask ``QuerySet.alias``
    leaves an alias out of that walk by), so it is split as it is over the same rows
    unannotated. A name the path starts with is still read as ``query``'s annotation or
    alias: ``Query.solve_lookup_type`` matches it against ``Query.annotations`` before it
    walks, and ``FilteredRelation`` aliases are read at the start of the path alone. The
    first element is the query the answer was walked over, for a caller's later walk.
    """
    lookups, field_parts, expression = query.solve_lookup_type(lookup)
    # An annotation or alias the path starts with is ``expression``: a selected annotation
    # the walk ends on was read past a relation.
    if expression is not False or field_parts[-1] not in query.annotation_select:
        return query, lookups, field_parts, expression
    unselected = query.clone()
    unselected.set_annotation_mask(())
    return unselected, *unselected.solve_lookup_type(lookup)


def split_lookup(
    query: sql.Query,
    lookup: str,
) -> tuple[tuple[str, ...], ModelField | Expression, tuple[str, ...]]:
    """Split ``lookup`` as ``Query.build_filter`` splits a filter argument over ``query``.

    ``Query.solve_lookup_type`` divides it into the names walked as a path and the
    transforms and lookup left over. The answer is the names the path is spelled with (a
    relation hop and a name ``query`` annotates or aliases at the start of the path
    included; a name past a relation is a name of the related model, never ``query``'s
    annotation, ``_solve_lookup_type``), what ``Query.build_lookup`` applies the
    leftover to, and the leftover. That start is the expression an annotation or alias
    names, else the final field ``Query.names_to_path`` (the walk ``Query.setup_joins``
    runs) ends on, the output field of the column Django builds: the relation's own
    field where the path ends on a relation (a reverse relation's ``ForeignObjectRel``,
    a many-to-many's through key onto its target). Raises ``FieldError`` where Django
    refuses the path.
    """
    query, lookups, field_parts, expression = _solve_lookup_type(query, lookup)
    names = lookup.split(LOOKUP_SEP)
    start = (
        expression
        if expression is not False
        else _names_to_path(query, field_parts, query.get_meta())[1]
    )
    return tuple(names[: len(names) - len(lookups)]), start, tuple(lookups)


def joinless_relation_on(
    model: type[models.Model],
    lookup: str,
) -> tuple[ModelField, tuple[str, ...]] | None:
    """Return the relation Django builds no join for that a filter on ``lookup`` reaches; ``None``.

    ``lookup`` is walked name by name as ``Query.names_to_path`` walks a filter argument
    (the walk ``Query.setup_joins`` runs), each name read on the model the hop before it
    reaches: ``pk`` as the primary key, a field a concrete parent declares through the
    parent hop. The walk refuses a name naming a relation with no ``related_model`` (a
    ``GenericForeignKey``, whose target is no one model) wherever it stands, with
    ``FieldError``, before it reads any name past it; the answer is that name's field on
    the model the walk stands on (``Options.get_field``), held to the walk's own test
    (``is_relation and not related_model``), with the names ``lookup`` spells past it.
    ``None`` where the walk reaches a column, one a concrete parent declares included (the
    names left are its transforms and lookup, a JSON key named as a relation among them), a
    name the model does not carry (a queryset's annotation or alias, a typo, a lookup), or
    the end of ``lookup`` on a relation Django joins.
    """
    query = sql.Query(model)
    opts: _OptionsAny = model._meta
    names = lookup.split(LOOKUP_SEP)
    for position, name in enumerate(names):
        try:
            # One name: Django answers its hops, or raises for a name it cannot walk.
            steps, reached, _targets, _rest = _names_to_path(query, [name], opts)
        except FieldError:
            try:
                field = opts.get_field(name)
            except FieldDoesNotExist:
                return None
            joinless = field.is_relation and not field.related_model
            return (field, tuple(names[position + 1 :])) if joinless else None
        # A column ends the walk, a parent's inherited one included (its steps are the parent
        # hop): the names past it are its transforms and lookup, never fields.
        if not reached.is_relation:
            return None
        opts = steps[-1].to_opts
    return None


@dataclasses.dataclass(frozen=True, slots=True)
class ResolvedOrderName:
    """An order name as ``Query.setup_joins`` resolves it (``resolve_order_name``).

    ``path`` is the ``PathInfo`` steps of the joins the name sets up.
    ``final_field`` is the field the walk ends on: a local column, or the join
    field of the last hop - for a many-to-many the through table's key to the
    target, for a generic relation its reverse relation. It is the field
    ``Query.build_filter`` compares a lookup against and
    ``SQLCompiler.find_ordering_name`` tests for expansion. ``lookups`` is the
    pieces left over once a piece names no field: transforms and a final lookup.
    ``related_opts`` is the model the last hop reaches when nothing is left
    over. ``substitute`` is the related ``Meta.ordering`` the compiler orders the
    name by instead of a column, or ``None``.
    """

    path: Sequence[_PathStep]
    final_field: ModelField
    lookups: Sequence[str]
    related_opts: _OptionsAny | None
    substitute: Sequence[str | Combinable] | None


def resolve_order_name(query: sql.Query, name: str, opts: _OptionsAny) -> ResolvedOrderName:
    """Resolve ``name`` (no direction) against ``opts`` the way the compiler resolves an order name.

    ``Query.names_to_path`` is the walk ``setup_joins`` runs for
    ``django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name``,
    ``Query.resolve_ref`` and ``Query.solve_lookup_type`` alike: ``pk`` names the
    primary key, a reverse relation names its model, a field on a concrete
    parent adds the parent hop, and the first piece naming no field ends the
    walk. It reads ``query`` only for the annotation and filtered-relation names
    it falls back to, and adds no join to it. Raises ``FieldError`` where Django
    raises: a first piece naming nothing, or a generic foreign key.

    The substitution is the condition ``find_ordering_name`` tests on what
    ``setup_joins`` returns: no transform left over, the final field a relation,
    the model the path ends on declaring ``Meta.ordering``, and the name neither
    the final field's ``attname`` (``"author_id"``) nor ``"pk"``. A reverse
    relation has no ``attname``, which the compiler reads as ``None`` too, and a
    many-to-many's final field is the through key (``"genre_id"``), so its name
    always expands.
    """
    path, final_field, _targets, rest = _names_to_path(query, name.split(LOOKUP_SEP), opts)
    related_opts: Options[models.Model] | None = path[-1].to_opts if path and not rest else None
    substitute = (
        related_opts.ordering
        if related_opts is not None
        and related_opts.ordering
        and final_field.is_relation
        and getattr(final_field, "attname", None) != name.rsplit(LOOKUP_SEP, maxsplit=1)[-1]
        and name != "pk"
        else None
    )
    return ResolvedOrderName(path, final_field, rest, related_opts, substitute)


def take_order_expansion_step(
    resolved: ResolvedOrderName,
    *,
    start: object,
    seen: set[tuple[object, ...]],
) -> tuple[object, ...] | None:
    """Record the expansion of ``resolved`` in ``seen`` and return its key, or None on a repeat.

    ``django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name`` threads
    one ``already_seen`` set through the whole expansion of a top-level ordering
    term, sibling items of every related ``Meta.ordering`` included, and raises
    ``FieldError("Infinite loop caused by ordering.")`` when an expansion's key
    is already in it. The key is the ``join_cols`` of the join the expansion
    starts from (``start``: None for the query's base table, otherwise the last
    element of the key of the expansion it hangs under) and of every join its
    path adds, each the ``(lhs, rhs)`` column pairs
    ``django/db/models/sql/datastructures.py::Join`` reads off its
    ``join_field``. A None return is that repeat; ``seen`` is left unchanged.
    """
    step = (
        start,
        *(
            tuple((lhs.column, rhs.column) for lhs, rhs in hop.join_field.get_joining_fields())
            for hop in resolved.path
        ),
    )
    if step in seen:
        return None
    seen.add(step)
    return step


def _expanded_order_name(
    query: sql.Query,
    name: str,
    *,
    descending: bool,
    opts: _OptionsAny,
    prefix: str,
    start: object,
    seen: set[tuple[object, ...]],
) -> list[str | F | Expression]:
    """Expand one order name the way ``SQLCompiler.find_ordering_name`` does, as order terms.

    Resolves ``name`` against ``opts`` with ``Query.names_to_path``, the walk the
    compiler's ``setup_joins`` runs, and returns terms spelled from ``query``'s
    model (``prefix`` is the relation path the expansion descended through)
    that the compiler and ``Query.resolve_ref`` both read as the same columns or
    expression. A name the compiler does not expand is spelled as the columns it
    orders by: a carrier-backed relation as its carriers
    (``utils/relations.py::order_column_paths``), a ``"pk"`` reached through a
    relation as that model's key column. Raises ``_UnexpandableOrderError`` where
    the compiler raises: a name that resolves to no field (a related ``"?"``), a
    relation step ``seen`` already holds (``"Infinite loop caused by
    ordering."``, keyed by ``take_order_expansion_step``), or an ordering item
    that is neither a name nor an order expression.
    """
    try:
        resolved = resolve_order_name(query, name, opts)
    except FieldError:
        raise _UnexpandableOrderError(name) from None
    ordering = resolved.substitute
    related_opts = resolved.related_opts
    if related_opts is None or ordering is None:
        # A transform left over is never spelled by carriers either.
        terminal: object = None if resolved.lookups else resolved.final_field
        sign = "-" if descending else ""
        # ``"pk"`` inside a related ordering is never expanded there; spelled from the
        # outer query it must name the key column, or a relation key would expand.
        spelled = opts.pk.attname if prefix and name == "pk" else name
        return [f"{sign}{column}" for column in order_column_paths(f"{prefix}{spelled}", terminal)]
    step = take_order_expansion_step(resolved, start=start, seen=seen)
    if step is None:
        raise _UnexpandableOrderError(name)
    nested = f"{prefix}{name}{LOOKUP_SEP}"
    expanded: list[str | F | Expression] = []
    for item in ordering:
        if isinstance(item, str):
            expanded.extend(
                _expanded_order_name(
                    query,
                    item.removeprefix("-"),
                    descending=descending != item.startswith("-"),
                    opts=related_opts,
                    prefix=nested,
                    start=step[-1],
                    seen=seen,
                ),
            )
            continue
        if not isinstance(item, (F, BaseExpression)):
            # The compiler calls ``asc()`` on any other item and fails there.
            raise _UnexpandableOrderError(name)
        # An ``OrderBy`` is lifted as written - ``-relation`` does not invert it - while a
        # bare expression takes the relation term's direction.
        ordered = item if isinstance(item, OrderBy) else item.desc() if descending else item.asc()
        expanded.append(ordered.prefix_references(nested))
    return expanded


def expand_relation_order(
    order_by: Iterable[str | F | Expression],
    query: sql.Query,
) -> list[str | F | Expression]:
    """Return ``order_by`` with every relation-name term replaced by what the compiler orders by.

    ``django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name`` does not
    order a STRING term ending on a relation by the relation's key when the
    related model declares ``Meta.ordering`` (unless the name is the final join
    field's ``attname``, as a multi-column ``ForeignObject``'s always is, which
    keeps its carrier columns; a many-to-many's final join field is the through
    table's key, so its name always expands): it substitutes that ordering,
    recursively, a ``-`` inverting each string and bare-expression item while an
    ``OrderBy`` item keeps its own direction. An expression term never takes that
    path (``Query.resolve_ref`` reads ``F("author")`` as the key column), and
    neither does a ``Window`` order (it resolves every string as such an ``F``),
    so a window ordered by the terms as written numbers its rows in a different
    order than the statement compiling them. Every term returned here is read the
    same way by both: a column path, or an expression with its references
    spelled from ``query``'s model.

    A string the compiler reads before the field path (an annotation, an
    ``extra`` name) stays as written, and so does a name ``Query.names_to_path``
    cannot resolve (``"?"``) or whose expansion the compiler rejects (a related
    ``"?"``, an ordering loop): the compiler reads it as written wherever it is
    compiled, raising Django's own ``FieldError`` where Django raises one.
    """
    return [spelled for term in order_by for spelled in _expanded_order_term(term, query)]


def _expanded_order_term(
    term: str | F | Expression,
    query: sql.Query,
) -> Sequence[str | F | Expression]:
    """Expand one ``expand_relation_order`` term, or return it as written."""
    if not isinstance(term, str):
        return (term,)
    name = term.removeprefix("-")
    if name in query.annotations or name in query.extra:
        # The compiler reads these before the field path, as the term written.
        return (term,)
    try:
        return _expanded_order_name(
            query,
            name,
            descending=term.startswith("-"),
            opts=query.get_meta(),
            prefix="",
            start=None,
            seen=set(),
        )
    except _UnexpandableOrderError:
        return (term,)


def initial_queryset(type_cls: type[DjangoType]) -> models.QuerySet[models.Model]:
    """Return ``model._default_manager.all()`` for a ``DjangoType``'s model.

    Step 1 of the Relay node defaults' four-step shape and the default
    resolver seed for list / connection fields. Seeds from
    ``model_for(type_cls)`` so the model lookup stays single-sited; every
    surface that needs a fresh unevaluated base queryset for a registered TYPE
    shares this one source (the model-keyed seed underneath is
    :func:`base_queryset`). Callers are responsible for ``type_cls`` being a
    registered ``DjangoType``; a missing definition surfaces as a raw
    ``AttributeError``.
    """
    return base_queryset(model_for(type_cls))


def normalize_query_source(source: object) -> NormalizedSource:
    """Coerce a ``Manager`` to its ``QuerySet`` and report whether the result is one.

    The single Manager-to-QuerySet coercion shared by every resolver surface
    that accepts a consumer-supplied source (``DjangoListField`` /
    ``DjangoConnectionField`` consumer ``resolver=`` returns, the optimizer
    middleware's root return). A ``Manager`` (the ``Model.objects`` shorthand)
    becomes a fresh unevaluated ``QuerySet`` via ``.all()``; a ``QuerySet``
    passes through; a non-queryset iterable (a Python list / generator) passes
    through unchanged with ``is_queryset=False`` so the caller can short-circuit
    (pass it through, or raise its own GraphQL-specific error before pagination).

    Returns ``(source, is_queryset)`` rather than deciding the tail itself so
    each caller keeps its colored steps (``apply_type_visibility_*`` / the
    connection sidecar guard / the optimizer plan) explicit, never hidden behind
    a maybe-await abstraction.

    A ``Manager`` source is coerced through ``_coerced_manager_queryset``, which
    fails closed if the manager's ``.all()`` degrades into a non-queryset or
    silently changes the routed database - a Manager has explicitly selected the
    queryset / visibility path, so it must NEVER be allowed to fall into the
    plain-iterable (``is_queryset=False``) bypass reserved for a consumer that
    directly returns a list / generator.
    """
    if isinstance(source, models.Manager):
        return _coerced_manager_queryset(source), True
    if isinstance(source, models.QuerySet):
        return source, True
    return source, False


def identity_key(field: ModelField | None, value: object) -> object:
    """Return the key one identity of ``field``'s column compares by: the column's own value.

    The comparison basis wherever the package matches an identity it decoded against
    the rows a query returned (the ``nodes`` reorder, the relation membership map).
    ``field.to_python`` (the cast every identity decode and every lookup goes through)
    turns both sides into the column's Python value, which compares by value, not by
    spelling: an unconstrained decimal key ``2.50`` is the stored ``2.5`` (PostgreSQL
    keeps the written scale, so a row read back as ``1.50`` is the decoded ``1.5``), an
    aware datetime key in any UTC offset is the row read back in UTC (an aware key is its
    instant, so a wall clock a DST fold repeats or a gap skips keys as that instant too),
    ``"07"`` is the integer pk ``7`` and an upper-case UUID is its lower-case form. A naive
    datetime on a ``DateTimeField`` column under ``USE_TZ`` is the aware value Django binds
    for it (``column_python_value``), so it keys as the row read back. Equality a database
    collation adds (a case-insensitive key) is no part of the column's value, so an id
    the lookup matched only through it misses.

    A side with no column to cast against (``field`` is ``None`` or no concrete
    ``models.Field``: a ``relay.NodeID`` attribute naming no model field) keys by
    ``str``, the only form its raw literal has, and so does a value the cast leaves
    unhashable (a list from a composite or array column).
    """
    if not isinstance(field, models.Field):
        return str(value)
    key = column_python_value(field, value)
    if isinstance(key, datetime.datetime):
        offset = key.utcoffset()
        if offset is not None:
            # An aware datetime keys by its instant, a ``timedelta`` from ``datetime.min``
            # that no instant overflows. PEP 495 makes a wall clock its zone repeats or
            # skips (a DST fold or gap) unequal to the same instant in any other zone, so
            # a naive id made aware in the default zone would never equal its UTC row.
            utc = datetime.timezone.utc
            origin = datetime.datetime.min.replace(tzinfo=utc)
            return key.replace(tzinfo=utc) - origin - offset
    try:
        _ = hash(key)
    except TypeError:
        return str(key)
    return key


def _value_codecs(field: ConcreteField) -> tuple[ConcreteField, ...]:
    """Return the fields whose ``to_python`` / ``get_db_prep_value`` code ``field``'s value, in order.

    ``field`` first, so a consumer subclass's own methods hold (Django's
    ``ForeignKey.to_python`` / ``get_db_prep_value`` delegate to the column the key
    references). When the value is stored in a ``GeneratedField`` (``field`` itself or the
    ``to_field`` its key links reach), that delegation ends on the generated field's own
    methods, the identity, so the column it computes (``relations.py::generated_column``)
    codes the value next: a key subclass's cast and the computed column's both apply.
    """
    stored: ConcreteField = field
    while isinstance(stored, models.ForeignKey):
        stored = stored.target_field
    column = generated_column(stored)
    return (field,) if column is None else (field, column)


def _cast_value(field: ConcreteField, value: object) -> object:
    """Return ``value`` cast by each of ``_value_codecs(field)``'s ``to_python`` in turn."""
    for codec in _value_codecs(field):
        value = object_result(codec.to_python, value)
    return value


def column_python_value(field: ConcreteField, value: object) -> object:
    """Return ``field.to_python(value)``, a ``DateTimeField``'s naive value read as Django binds it.

    The cast is ``_value_codecs``': the declared field's own ``to_python``, so a consumer
    key subclass's cast holds, then for a value stored in a ``GeneratedField`` the column it
    computes. When the column the value is stored in (``relations.py::stored_value_column``)
    is a ``DateTimeField``, a date or naive datetime (one ``to_python`` returns for a
    spelling without an offset, a date-only spelling as its midnight) is the datetime
    Django's lookup and save bind for it: under ``USE_TZ``, aware in the default time zone
    (``errors.py::datetime_django_binds``). Django makes that projection with a
    ``RuntimeWarning``; reading it here is silent, so an identity decode neither warns nor
    keys a naive request apart from the aware row it matched. Every other value is
    ``to_python``'s.
    """
    if not isinstance(stored_value_column(field), models.DateTimeField):
        return _cast_value(field, value)
    stamp = value if isinstance(value, datetime.date) else _cast_value(field, value)
    if not isinstance(stamp, datetime.date):
        return stamp
    return datetime_django_binds(stamp, use_tz=bool(django_setting("USE_TZ")))


def truncates_to_integer(field: ModelField | None, value: object) -> bool:
    """Whether ``value`` is a fractional number the integer column ``field`` would truncate.

    ``IntegerField.to_python`` is ``int(value)``, which turns ``Decimal("1.5")`` into ``1``
    and ``-1.5`` into ``-1``: a fractional number equals no integer, so it names no row an
    integer column (or an integer transform's output) holds. Raw form data reaches this as
    a ``forms.DecimalField``'s cleaned ``Decimal``. The number answers for its own
    integrality (``Decimal.to_integral_value``, ``float.is_integer``) and is never cast to
    an integer to be compared with it: django-filter caps a decimal only from above, so a
    ``Decimal`` such as ``-1E+1000000`` is a million-digit integer, and each cast or
    comparison of it costs seconds. A number equal to its integer cast (``1.0``,
    ``Decimal("1E+2")``) is the integer it spells; a ``bool``, a string, a non-finite
    number and any other type is no fractional number. ``False`` for a non-integer
    ``field``.
    """
    if not isinstance(field, models.IntegerField):
        return False
    if isinstance(value, Decimal):
        return value.is_finite() and value != value.to_integral_value()
    return isinstance(value, float) and math.isfinite(value) and not value.is_integer()


def lookup_read_alias(model: type[models.Model]) -> str:
    """Return the database a lookup of ``model``'s rows reads when no queryset is in hand.

    The write pipeline's pinned alias inside ``open_write_pipeline`` (every write
    flavor's reads go through it), the router's read database for ``model``
    everywhere else. The alias an identity decode coerces against
    (``coerce_field_value_or_none``) is this one, so the value is prepared for the
    connection the lookup binds it on.
    """
    pipeline = current_write_pipeline()
    if pipeline is not None:
        return pipeline.alias
    return router.db_for_read(model)


def coerce_field_value_or_none(field: ModelField | None, value: object, *, alias: str) -> object:
    """Coerce ``value`` to what ``field``'s column can hold on ``alias``; ``None`` if it names no row.

    The single "raw literal -> Django field value, or nothing" safety wrapper
    every raw-identity decode runs through: a decoded ``GlobalID`` node id, a raw
    pk, a relation identity, an integer ``in`` member. A value identifies a stored
    row when the column can hold it, so the checks are the ones the lookup's bind
    and the column's storage domain make, never the field's validators: a row a
    validator would refuse can still be stored (``objects.create``,
    ``bulk_create``, ``QuerySet.update`` and a migration all skip
    ``full_clean``), and an identity decode that ran them would miss it.

    A lazy value (a ``SimpleLazyObject``) is read as the object it stands for
    (``utils/lazy.py::unwrap_lazy_object``), so the checks below see its real text.
    ``to_python`` casts the value and refuses a wrong shape (``column_python_value``: a
    date or naive datetime for a ``DateTimeField`` column is the aware value Django binds
    for it under ``USE_TZ``, made aware in the default time zone without Django's
    naive-datetime warning, and is the value returned). Most Django core
    fields wrap that failure in ``ValidationError``; ``TypeError`` / ``ValueError``
    cover a field whose ``to_python`` raises one of those directly, and
    ``OverflowError`` is what ``DurationField.to_python`` raises for a well-formed
    duration string past ``timedelta``'s range (``int(inf)`` in
    ``IntegerField.to_python`` raises it too).

    The value is then prepared for the database ``alias`` reads from, as Django's
    own lookup prepares it (``Field.get_db_prep_value``; a key delegates to the
    column it references), so a value that backend's adapter refuses (an aware
    datetime SQLite cannot project to UTC, a malformed address PostgreSQL's
    ``inet`` adapter rejects) names no row there, and only there. PostgreSQL's
    server refuses one value its adapters pass, an aware datetime or time whose UTC
    offset it cannot hold, so ``errors.py::refuses_utc_offset`` answers that past
    the bind. ``alias`` is the database the lookup reads: the filtered queryset's
    ``db``, or ``lookup_read_alias`` (the pinned write-pipeline alias, else the
    router's read database for the queried model).

    The prepared value is held to the column's storage domain. An integer stays
    inside the range ``alias`` stores for the internal type of the column holding
    the value (``binds_integer``: ``DatabaseOperations.integer_field_range``, the
    range Django's integer comparison lookups test a bound against before binding
    it; a ``BigIntegerField``'s for a column that is no ``IntegerField`` yet binds
    an integer, as a ``DurationField`` binds its microsecond count on a backend
    without a native interval, so a duration past 64 bits of microseconds names
    no row there). That column is the one ``relations.py::stored_value_column`` walks
    a key to, so a one-to-one primary key, a parent link or a ``ForeignKey`` is
    held to its referenced column's range. A fractional number on an integer column
    (``Decimal("1.5")``, ``0.9``) names no row and is ``None`` (``truncates_to_integer``),
    never the integer ``to_python`` truncates it to. A decimal on a ``DecimalField`` with
    ``max_digits`` is the value of the column it equals, quantized to
    ``decimal_places`` within ``max_digits``: a value no stored decimal equals
    (too many integer digits, a finer fraction) names no row, and an in-range
    value spelled with any number of trailing zeros is the column's value, so its
    spelling never reaches a backend that would refuse to bind it. A decimal on a
    ``DecimalField`` without ``max_digits`` binds as written when its spelling fits
    PostgreSQL's unconstrained ``numeric`` (131072 digits before the point, 16383
    after: PostgreSQL's documented limits, past which ``numeric_in`` refuses the
    bind); a spelling past them loses its trailing fractional zeros without
    rounding, and is ``None`` if it still does not fit. Every other backend binds it
    as given.

    A value coerced to text holding an embedded NUL (U+0000) identifies no row
    either, on every backend: no write stores one (Django's all-backend
    ``ProhibitNullCharactersValidator`` rule, which
    ``write_values.py::unstorable_text_error`` holds every write to), and
    PostgreSQL refuses to bind one at all (psycopg raises ``DataError``), so a NUL
    in a text-keyed id answers the caller's not-found / invalid-id verdict before
    any query rather than a raw backend error.

    Every caller treats ``None`` the same way - "identifies no row": dropped
    from a query, or mapped to a not-found / invalid sentinel - never a raw
    crash. WHICH field to coerce against is a genuine per-caller decision (a
    Relay type's resolved id field, a related model's pk, an arbitrary filtered
    column) and stays at each call site; only the coercion mechanics are
    single-sourced here. A ``ForeignObjectRel`` or ``None`` field has no column
    to coerce against, so it identifies no row either.
    """
    if not isinstance(field, models.Field):
        return None
    connection = connections[alias]
    # The declared field casts and prepares the value, then for a generated column the
    # column it computes (``_value_codecs``); the storage-domain checks below read the
    # column the value is stored in (``stored_value_column``).
    try:
        coerced = column_python_value(field, unwrap_lazy_object(value))
        if is_str(coerced):
            _PROHIBIT_NULL_CHARACTERS(coerced)
        bound = coerced
        for codec in _value_codecs(field):
            bound = object_result(codec.get_db_prep_value, bound, connection, prepared=False)
    except (
        ValidationError,
        TypeError,
        ValueError,
        OverflowError,
    ):
        return None
    column = stored_value_column(field)
    if truncates_to_integer(column, value):
        return None
    if unbindable_temporal(column, coerced, lambda: alias):
        return None
    if (
        isinstance(bound, int)
        and not isinstance(bound, bool)
        and not binds_integer(connection, column, bound)
    ):
        return None
    if isinstance(coerced, Decimal) and isinstance(column, models.DecimalField):
        return _stored_decimal_or_none(coerced, column, connection)
    return coerced


def _stored_decimal_or_none(
    number: Decimal,
    column: ModelField,
    connection: BaseDatabaseWrapper,
) -> Decimal | None:
    """Return the value ``column`` stores that equals ``number``, or ``None`` when none does.

    ``number`` is quantized to ``decimal_places`` within ``max_digits``: one needing more
    integer digits than the column holds, or a finer fraction than it keeps, equals no
    stored value. A column declared without ``max_digits`` (django-stubs types it ``int``,
    Django accepts ``None``) is held to the domain of the backend's unconstrained decimal
    on ``connection``, the database the lookup binds on. On PostgreSQL that is ``numeric``
    with no precision, whose format ``utils/errors.py::refuses_numeric_format`` holds a
    spelling to. It stores the written scale, so ``number`` binds as written when its
    spelling fits. A spelling past the limits loses its trailing fractional zeros,
    exactly and without rounding (the same value, so it names the same row; a zero
    becomes plain ``0``), and the digits left past either limit equal no stored value.
    Every other backend binds ``number`` as given.
    """
    digits = read_attr(column, "max_digits")
    if not isinstance(digits, int):
        return _unconstrained_decimal_or_none(number, connection)
    places = read_attr(column, "decimal_places")
    try:
        held = number.quantize(
            Decimal(1).scaleb(-places if isinstance(places, int) else 0),
            context=DecimalContext(prec=digits),
        )
    except InvalidOperation:
        return None
    return held if held == number else None


def _unconstrained_decimal_or_none(
    number: Decimal,
    connection: BaseDatabaseWrapper,
) -> Decimal | None:
    """Return ``number`` as an unconstrained ``numeric`` on ``connection`` binds it, else ``None``.

    The spelling binds as written when ``refuses_numeric_format`` does not refuse it (on
    every backend but PostgreSQL, always); otherwise the trailing fractional zeros go
    from the coefficient itself, never through ``Decimal.normalize``, whose context
    precision would round a long coefficient.
    """
    if not refuses_numeric_format(connection, (number,)):
        return number
    sign, coefficient, _ = number.as_tuple()
    exponent = number.adjusted() - len(coefficient) + 1
    kept = len(coefficient)
    while exponent < 0 and kept > 1 and coefficient[kept - 1] == 0:
        kept -= 1
        exponent += 1
    if not any(coefficient[:kept]):
        return Decimal((sign, (0,), 0))
    stripped = Decimal((sign, coefficient[:kept], exponent))
    return None if refuses_numeric_format(connection, (stripped,)) else stripped


def sync_pipeline_recourse(flavor_noun: str) -> str:
    """Build the ``SyncMisuseError`` recourse a sync write pipeline appends.

    Every write flavor raises a ``SyncMisuseError`` naming the SAME recourse when an
    ``async def get_queryset`` is met inside its (synchronous) ORM pipeline -
    byte-identical except the flavor subject - so the sentence lives here and each
    flavor's own ``*_ASYNC_RECOURSE`` constant is computed from it. NOT used for the
    Relay recourse (``types/relay.py::_RELAY_ASYNC_RECOURSE`` - async IS possible there) or the
    permission recourses (about the permission hooks, not ``get_queryset``), which
    are genuinely different wordings.
    """
    return (
        f"A {flavor_noun} runs its ORM pipeline synchronously (under one sync_to_async "
        "call on the async surface), so it cannot await an async get_queryset hook; "
        "redefine the target type's get_queryset as a sync method."
    )


def is_async_only_iterable(value: object) -> TypeGuard[AsyncIterable[object]]:
    """Whether ``value`` iterates only asynchronously.

    The one spelling of the async-only-iterable predicate: an
    ``AsyncIterable`` that is NOT also a plain ``Iterable``. The ``not
    Iterable`` half is essential - a Django ``QuerySet`` is both sync and
    async iterable and must never classify as async-only. Shared by
    ``reject_async_iterable_in_sync_context`` below, ``list_field.py``'s
    async-completion branch, and ``resource_policy.py::bounded_rows_async``'s
    bound dispatch, so the shapes the package treats as "async-only" cannot
    drift between the surface that rejects them and the surfaces that consume
    them.
    """
    return isinstance(value, AsyncIterable) and not isinstance(value, Iterable)


class _AsyncQuerySetRows:
    """Async-only completion adapter for a QuerySet a list field completes under async execution.

    Exposes ONLY ``__aiter__`` (delegating to ``self._queryset.__aiter__()``)
    and deliberately omits ``__iter__`` so graphql-core cannot select synchronous
    ORM iteration in an event-loop thread. ``DjangoListField``'s async pipeline
    wraps its final sliced queryset in it. It changes where the rows are fetched,
    never what a resolver body does on the loop.
    """

    __slots__: tuple[str, ...] = ("_queryset",)

    def __init__(self, queryset: models.QuerySet[models.Model, object]) -> None:
        self._queryset: models.QuerySet[models.Model, object] = queryset

    def __aiter__(self) -> AsyncIterator[object]:
        return self._queryset.__aiter__()


def wrap_async_queryset_adapter(qs: _T) -> _T | _AsyncQuerySetRows:
    """Wrap a QuerySet in an async-only completion adapter; pass non-querysets through unchanged."""
    if isinstance(qs, models.QuerySet):
        return _AsyncQuerySetRows(qs)
    return qs


def unwrap_async_queryset_adapter(
    val: _T,
) -> tuple[_T | models.QuerySet[models.Model, object], bool]:
    """Unwrap an ``_AsyncQuerySetRows`` adapter to ``(inner_queryset, True)`` or ``(val, False)``."""
    if isinstance(val, _AsyncQuerySetRows):
        return val._queryset, True
    return val, False


def reject_async_iterable_in_sync_context(
    value: object,
    *,
    flavor_noun: str,
    async_executor: bool,
) -> None:
    """Reject an async-only resolver SOURCE under synchronous GraphQL execution.

    The read-flavor sibling of ``reject_async_in_sync_context`` (that one
    refuses an awaitable returned by a sync HOOK; this refuses the
    ``AsyncIterable`` a plain-``def`` resolver RETURNED). Strawberry's sync
    list / connection completion routes such a value to its synchronous
    slicer, which fails with an internal blank ``AssertionError``, so both
    field flavors fail closed with the public sync-misuse error instead -
    one rule, one recourse sentence; only the flavor subject differs (the
    guard fires on the ACTUAL returned source rather than only the callable's
    declared shape, so every async-only source is caught no matter which
    construction-time branch produced it). Under async execution this is a
    no-op: the native async executor consumes the AsyncIterable itself.

    ``async_executor`` is the CALLER's answer to which executor is driving
    (``utils/execution_mode.py::operation_is_async``), never a reading this
    guard takes for itself: the ambient event loop and the executor disagree
    whenever a synchronous operation is started from inside an asynchronous
    one, and a guard that sampled the loop would call that operation async and
    pass a value its executor cannot consume.
    """
    if is_async_only_iterable(value) and not async_executor:
        raise SyncMisuseError(
            f"A {flavor_noun} resolver returned an AsyncIterable in a sync execution "
            "context. Use `await schema.execute(...)` for async iterable resolvers.",
        )


async def run_in_one_sync_boundary(
    fn: Callable[_P, _R],
    *args: _P.args,
    **kwargs: _P.kwargs,
) -> _R:
    """Run ``fn(*args, **kwargs)`` in ONE ``sync_to_async(thread_sensitive=True)`` worker.

    The generic one-boundary primitive (spec-040 Decision 10): every async surface
    that must keep a consumer-overridable sync hook off the event loop shares
    this call, so the boundary discipline (``thread_sensitive=True``, never
    per-step hops inside one unit of work) cannot drift. The unit differs by
    surface. An auth or mutation resolution enters it exactly once, with its
    permission gate and write pipeline inside (spec-040 Decision 10 pins that count for
    auth). A sidecar ``apply_async`` enters it once for its permission pass. A
    read path enters it once per custom synchronous ``get_queryset`` call
    (``apply_type_visibility_async``; a cascade walk inside that hook rides the
    same worker) and once per optimizer plan build
    (``DjangoOptimizerExtension._needs_sync_boundary``,
    ``apply_connection_optimization_async``), so one read resolution may enter it
    more than once; the optimizer's hop serves a plain ``def`` root under the
    asynchronous executor too (``DjangoOptimizerExtension.resolve``).
    A ``sync_to_async`` worker is itself a sync context, so the standing
    ``SyncMisuseError`` guards still fire inside ``fn``.

    Neutral home: lives here with the sibling ``reject_async_in_sync_context``
    primitive (cycle-safe utils substrate) rather than under ``mutations/``, so
    read-side modules reuse it without a root-into-subpackage import.
    """
    return await sync_to_async(fn, thread_sensitive=True)(*args, **kwargs)


def _concrete_or_none(candidate: object) -> type[models.Model] | None:
    """Return ``candidate._meta.concrete_model`` if ``candidate`` is a model class, else ``None``.

    ``types/base.py::_hinted_prefetch_seed_defect`` compares a hinted ``Prefetch``
    seed's model with the relation's target by their concrete models; a value that is
    not a model class answers ``None``. ``_meta`` is read statically
    (``utils/introspection.py::mro_attr``).
    """
    if not (is_class(candidate) and issubclass(candidate, models.Model)):
        return None
    meta: object = introspection.mro_attr(candidate, "_meta", None)
    if meta is None:
        return None
    # ``ModelBase.__new__`` sets ``_meta.concrete_model`` on every model class to a
    # model class (the class itself, or its concrete ancestor for a proxy).
    concrete: type[models.Model] | None = getattr(meta, "concrete_model", None)
    return concrete


class VisibleRowExists(Exists):
    """The framework's visibility test over related rows: Django's ``Exists``, under its own name.

    ``optimizer/predicates.py::visible_row_exists`` builds it to read an order value
    only from related rows a target type's ``get_queryset`` lets the request see. It
    defines nothing of its own, so every method the compiler dispatches on it is
    Django's ``Exists`` code; it exists as a distinct exact type so the code
    reading an ordering (the ``DjangoListField`` offset guard, the keyset order state)
    can recognize the framework's test and nothing else.
    """


def _type_is_genuinely_django(node_type: type[object]) -> bool:
    """Return whether ``node_type`` is a genuine Django class by IDENTITY, not ``__module__``.

    The ``DjangoListField`` offset guard reads an ordering's nodes through it, and
    ``filters/sets.py::_lookups_for_field`` leaves a lookup class it answers ``False``
    for out of ``"__all__"``. A ``type(node).__module__.startswith("django.")`` check
    would not do: ``__module__`` is a plain writable string, so a class declaring
    ``__module__ = "django.evil"`` passes it. Provenance is therefore proven by OBJECT
    IDENTITY: the type must be the exact object Django itself exposes at
    ``sys.modules[module].<qualname>``. A subclass, or a ``__module__`` /
    ``__qualname__`` pointing at a genuine name, cannot make
    ``getattr(genuine_django_module, name)`` return another type, so it answers
    ``False``. A dotted (nested) qualname, or a module absent from ``sys.modules``, also
    answers ``False``. ``__module__`` and ``__qualname__`` are the class's own.
    """
    module_name = node_type.__module__
    qualname = node_type.__qualname__
    if not module_name.startswith("django."):
        return False
    if "." in qualname:
        return False
    module = sys.modules.get(module_name)
    if module is None:
        return False
    return getattr(module, qualname, None) is node_type


# SQL-template metadata a genuine Django expression interpolates DIRECTLY into the
# emitted SQL string during ``as_sql`` -- never routed through ``get_source_expressions``
# and never bound as a ``%s`` parameter. ``Func`` joins its argument SQL with
# ``self.arg_joiner.join(...)`` and formats ``self.template % {"function": self.function,
# ...}``; ``CombinedExpression`` interpolates ``self.connector``; ``RawSQL`` emits
# ``self.sql`` verbatim. Genuine Django only ever stores strings here.
_SQL_TEMPLATE_ATTRS: tuple[str, ...] = (
    "template",
    "function",
    "arg_joiner",
    "connector",
    "sql",
    "base_template",
)


def _prefetch_relation_target_or_none(
    parent_model: type[models.Model],
    path: object,
) -> type[models.Model] | None:
    """Return the model the prefetch lookup ``path`` terminates on, or ``None``.

    Resolves ``prefetch_through`` one segment at a time through each model's
    ``_meta`` (Django's own relation metadata -- no consumer dispatch, every
    ``parent_model`` here is already a proven model class) and returns the
    FINAL relation's ``related_model``. Each part is tried against the model's
    reverse-ACCESSOR map first, the spelling Django's prefetch traversal itself
    resolves by attribute access (the default ``<model>_set`` of a relation
    declared WITHOUT ``related_name`` -- ``Permission.user_set``,
    ``ContentType.permission_set`` -- or a ``related_name`` beside its own
    ``related_query_name``), so a part that is one relation's accessor and
    another's query name resolves to the relation prefetch fetches. On a miss
    the field map answers (``_meta.get_field`` -- forward relations and reverse
    query names). A path that does not resolve to a relation at every segment
    (an unknown name, a plain column, a
    ``GenericForeignKey``-shaped accessor Django resolves through descriptors at
    fetch time rather than through the model's field map, an unresolved
    lazy-FK string whose ``related_model`` stays a raw string) returns ``None``,
    and the caller keeps the status-quo behavior for that entry -- the
    fetch-time traversal is Django's own responsibility, and the check must
    never fail-close a prefetch path Django supports. Multi-segment paths walk
    intermediate relations, so the target of ``"items__entries"`` is the
    reverse-relation target of ``entries`` on the child model, not the first
    relation's model.
    """
    if type(path) is not str:
        return None
    current: type[models.Model] = parent_model
    for part in path.split(LOOKUP_SEP):
        field: object = reverse_relation_by_accessor(current, part)
        if field is None:
            try:
                field = current._meta.get_field(part)
            except FieldDoesNotExist:
                return None
        if not getattr(field, "is_relation", False):
            return None
        related: object = getattr(field, "related_model", None)
        if not (is_class(related) and issubclass(related, models.Model)):
            return None
        current = related
    return current


@dataclasses.dataclass(frozen=True, slots=True)
class _SealPolicy(Generic[_RowT_co]):
    """The per-surface option set ``_seal_or_defect`` runs under, declared once.

    The type parameter is the row type a sealed queryset yields under the
    policy: ``models.Model`` when ``require_model_rows`` holds, ``object``
    otherwise. Each constant below declares it beside the flag it follows.

    Every surface that seals a queryset differs from the default on one or two
    axes. One frozen policy object carries them down the whole boundary chain
    (source preparation, result normalization, both colored runners), so a new
    axis is a field here plus its check in the seal -- never a keyword threaded
    through five signatures, where a runner that misses the keyword silently
    reaches none of them.

    - ``require_model_rows`` -- the row iterable must be ``ModelIterable``. Off
      only for the cascade, which re-projects the sealed queryset to the edge's
      target column and never iterates its rows, so a ``.values()`` return is
      supported input rather than a defect.
    - ``reject_sliced`` -- a sliced query (a ``LIMIT`` / ``OFFSET`` was taken) is
      a defect. Deliberately INDEPENDENT of ``require_model_rows``: the two
      answer different questions (what the rows ARE, versus whether this surface
      will recompose onto them), and fusing them would force the cascade to
      re-implement the slice rejection at both of its own entry points. Off one
      edge down only where something downstream answers for the slice: the
      optimizer walker's nested-connection child, whose own gate
      (``optimizer/nested_fetch.py::unwindowable_child_queryset_reason``) degrades
      a sliced child to the fully-unplanned per-parent fallback instead of
      recomposing filters / ordering onto it. It stays ON for the walker's plain-list-relation child
      (``_LIST_RELATION_CHILD_POLICY``), which no gate classifies and which Django
      refilters at fetch time.
    - ``require_shared_alias`` -- the candidate's explicit ``_db`` must EQUAL the
      outer effective alias, INCLUDING when that alias is ``None``. Set solely
      for a ``Prefetch`` child, so one GraphQL resolution never spans two
      database connections.
    - ``require_unevaluated`` -- the candidate's ``_result_cache`` must be ``None``.
      The axis separates a RESULT the surface itself demanded from a SOURCE the
      consumer supplies. It is on for every post-sidecar result
      (``_SIDECAR_RESULT_POLICY``): a public ``FilterSet.apply_*`` or
      ``OrderSet.apply_*`` return, on the list field and the Relay connection
      alike. The surface invoked that method one step earlier and windows what
      comes back, so rows already fetched mean the override filtered, ordered or
      paged something other than the query about to run. It is off for every
      ``get_queryset`` seal, this surface's included, because that hook's
      contract is shared with the Relay node, connection and relation surfaces -
      all of which rebuild their own query from the returned one - and holding
      one hook to a stricter rule here would make its verdict depend on which
      field called it and on whether a client happened to send window arguments.
      A consumer that evaluates inside the hook pays for the discarded
      ``_result_cache`` in one extra query, which is a cost, not a broken seal.
    """

    require_model_rows: bool = True
    reject_sliced: bool = True
    require_shared_alias: bool = False
    require_unevaluated: bool = False


# Every read surface (Relay node defaults, connection root, list field with or
# without list arguments, the related-object hooks): model rows, nothing sliced
# to recompose onto, a combinator served as its primary-key set, one alias.
_DEFAULT_SEAL_POLICY: _SealPolicy[models.Model] = _SealPolicy()
# ``apply_cascade_permissions`` at BOTH of its ends -- the root it is handed and
# every target hook's return. A ``.values()`` projection is supported input
# (the cascade re-projects it), while a sliced shape is rejected because the
# walk narrows by ``.filter(...)`` and re-projects to the edge's target column,
# which Django refuses after a slice. A combinator reaches the walk as its
# primary-key set, which takes both.
_CASCADE_SEAL_POLICY: _SealPolicy[object] = _SealPolicy(require_model_rows=False)
# The optimizer walker's NESTED-CONNECTION ``Prefetch`` child. Its nested-connection gate
# (``nested_fetch.py::unwindowable_child_queryset_reason``) classifies a sliced
# child and degrades the nested connection to the fully-unplanned per-parent
# fallback WITHOUT recomposing, so the slice rejection's premise does not hold
# there; the shared-alias requirement keeps one GraphQL resolution on one
# database connection.
_PREFETCH_CHILD_POLICY: _SealPolicy[models.Model] = _SealPolicy(
    reject_sliced=False,
    require_shared_alias=True,
)
# The optimizer walker's PLAIN-LIST-relation ``Prefetch`` child. It differs from
# ``_PREFETCH_CHILD_POLICY`` on ``reject_sliced`` and on no other axis, because
# exactly one thing differs: no gate downstream of this child classifies a slice.
# The walker installs the value as ``Prefetch(<lookup>, queryset=...)`` with no
# ``to_attr``, and Django then re-applies the relation's own filters to it
# (``prefetch_one_level`` -> ``RelatedManager._apply_rel_filters``), which raises a
# raw ``TypeError`` on a sliced query. A hook that returns a sliced queryset for
# such a child therefore gets the seal's typed ``sliced`` defect here, the same
# contract every other bad-hook shape answers to.
_LIST_RELATION_CHILD_POLICY: _SealPolicy[models.Model] = _SealPolicy(require_shared_alias=True)
# Post-sidecar result policy, one for both public ``FilterSet.apply_*`` and
# ``OrderSet.apply_*`` returns: model rows, unevaluated, unsliced, a combinator
# served as its primary-key set. The two sidecars hand back the same kind of object
# to the same downstream steps, so they answer to one policy (Decision 8: a second
# constant would differ on nothing).
_SIDECAR_RESULT_POLICY: _SealPolicy[models.Model] = _SealPolicy(require_unevaluated=True)


def _routing_hints_equal(cand_hints: object, orig_hints: object) -> bool:
    """Return True if candidate and original routing hints match without consumer dispatch.

    Preserves the exact distinction between absent (``None``) and empty (``{}``)
    hints. Keys must match exactly and every value must be the SAME OBJECT the
    snapshot holds: Django's ``ConnectionRouter`` hands hint values to consumer
    routers untouched, and a router is free to tell two equal tokens apart by
    identity, so semantic equality cannot prove equal routing without running
    the router. Identity is the only comparison that proves it without dispatch.
    """
    if not is_exact_dict(cand_hints) or not is_exact_dict(orig_hints):
        return False
    if cand_hints.keys() != orig_hints.keys():
        return False
    return all(cand_hints[k] is v for k, v in orig_hints.items())


@dataclasses.dataclass(frozen=True, slots=True)
class _RoutingIntent:
    """The source queryset's routing, frozen before consumer ordering code receives it.

    ``db`` and ``hints`` are the raw ``QuerySet`` state the post-``OrderSet``
    seal compares a returned candidate against. ``effective_alias`` is the
    connection that state RESOLVES to - the answer Django's
    ``ConnectionRouter`` gave for this model and these hints at snapshot time -
    and it is what the seal pins the accepted result onto.

    The resolved alias is the load-bearing member. A hint VALUE is an arbitrary
    consumer object handed to ``ConnectionRouter.db_for_read`` untouched, and a
    legal router may read mutable state inside one (a standard ``instance``
    hint is itself mutable), so preserving the hint dictionary - by identity or
    otherwise - proves nothing about the connection a later read would pick.
    Resolving the alias BEFORE the override can touch anything, and pinning the
    accepted output to it, is what makes "the ordered result reads the source's
    database" a mechanical guarantee rather than a promise about hint contents.
    """

    db: str | None
    hints: dict[str, object] | None
    effective_alias: str


def _snapshot_routing_intent(queryset: models.QuerySet[models.Model]) -> _RoutingIntent:
    """Freeze a sealed source's routing BEFORE consumer code receives it.

    The post-``OrderSet`` seal compares the returned candidate against this
    baseline, and the baseline has to be taken before the public ``apply_*``
    call: the override is handed the very same queryset object, so reading its
    routing afterwards would read whatever the override left there. The hints
    dictionary is copied, so an in-place ``_hints`` edit on the source cannot
    rewrite the expectation either; the seal compares a candidate's hints to
    the copy with ``==``, keeping absent (``None``) apart from empty (``{}``).

    The effective alias is then RESOLVED here, through the same
    ``ConnectionRouter`` method Django's own ``QuerySet.db`` property would use
    (``db_for_write`` for a write-marked queryset, ``db_for_read`` otherwise),
    and the seal pins the accepted result onto it. Django's router always
    answers with a concrete alias, falling back to ``DEFAULT_DB_ALIAS``, so an
    unrouted source resolves just as it would at execution - only earlier, while
    the hint values still hold the state the source intended. A ``TextChoices`` /
    ``StrEnum`` alias a router answers is frozen as its exact text
    (``utils/introspection.py::text``), the alias the seal pins.

    Routing reads come from the instance ``__dict__``; the model is the
    queryset's own, because the source reaching this seam is already a sealed
    queryset whose ``model`` the visibility boundary checked. The router is the deployment's own
    code and is trusted: whatever it raises propagates.
    """
    state: dict[str, object] = instance_state(queryset)
    # The source is a queryset this package built, so its routing slots are the ones
    # Django's own ``QuerySet`` writes: ``_db`` an alias or ``None`` (``using``), and
    # ``_hints`` a str-keyed dict.
    db = cast("str | None", state.get("_db"))
    hints = cast("dict[str, object] | None", state.get("_hints"))
    model = queryset.model
    for_write = state.get("_for_write") is True
    if type(hints) is dict:
        hints = dict(hints)
    if db is not None:
        return _RoutingIntent(db=db, hints=hints, effective_alias=db)
    resolve = router.db_for_write if for_write else router.db_for_read
    alias = resolve(model, **(hints if type(hints) is dict else {}))
    return _RoutingIntent(db=None, hints=hints, effective_alias=introspection.text(alias))


_ROUTING_SCALAR_TYPES: frozenset[type[object]] = frozenset(
    (
        int,
        float,
        bool,
        str,
        bytes,
        type(None),
    ),
)


def _routing_repr(value: object) -> str:
    """Format database routing intent for a ``routing`` defect.

    Scalars render as their builtin repr; an exact ``dict`` of hints renders its
    keys in ``str`` order and each non-scalar hint value as ``<ClassName at 0x...>``
    (its real name and identity), so an instance hint is named by what it is
    rather than by its own ``__repr__``.
    """
    if value is None:
        return "None"
    if type(value) is str:
        return repr(value)
    if is_exact_dict(value):
        items: list[str] = []
        for k in sorted(value.keys(), key=str):
            v = value[k]
            if type(v) in _ROUTING_SCALAR_TYPES:
                v_repr = repr(v)
            else:
                v_repr = f"<{introspection.name(v)} at {hex(id(v))}>"
            items.append(f"{k!r}: {v_repr}")
        return "{" + ", ".join(items) + "}"
    return repr(value)


def _validate_post_orderset_result(
    target_type: type[DjangoType],
    expected_routing: _RoutingIntent,
    post_order_candidate: object,
    method_name: str,
    *,
    model: type[models.Model] | None = None,
) -> models.QuerySet[models.Model]:
    """Validate and seal a public sidecar ``apply_sync`` / ``apply_async`` return.

    ``method_name`` names the ``FilterSet`` or ``OrderSet`` method that produced
    ``post_order_candidate``; the wording is the same for both because the
    contract is.

    ``expected_routing`` is the record :func:`_snapshot_routing_intent` froze
    before the public method ran; the validator never reads the source queryset
    itself, because by now the override has had it. The frozen effective alias
    is passed in as the seal's required alias, so the accepted result is PINNED
    to the connection the source resolved to and a hint object mutated behind a
    preserved identity cannot re-route the eventual read.

    ``model`` is the caller's captured model (``_captured_model``): the table
    the ordered result is validated against is the one the field seeded and
    sealed over, not an answer to a fresh request-time read of the target.
    """
    model = _captured_model(target_type, model)
    sealed, defect = _seal_or_defect(
        post_order_candidate,
        model,
        expected_routing.effective_alias,
        _SIDECAR_RESULT_POLICY,
        expected_routing=expected_routing,
    )
    if defect is not None:
        model_name = introspection.name(model)
        # Every SHAPE defect renders one wording: the public method's contract is a
        # single sentence, and naming the code plus its detail is what makes each
        # rejection actionable. ``routing`` is the one defect that is not a shape
        # problem, so it keeps its own arm, and ``combined`` keeps the shared
        # combined-queryset text (``_COMBINED_WHAT``) because a combinator is served
        # here unless it is a shape the primary-key rewrite would change. Spelled as
        # an explicit per-code map rather than a ``_defect_message`` default so a code
        # added to the seal without an arm here still self-names as a framework defect.
        #
        # ``alias`` is the one canonical code with no arm, because ``routing``
        # subsumes it at THIS site and nowhere else: the seal reaches the alias
        # check only after the routing check admitted ``candidate_db ==
        # intent.db``, and ``_snapshot_routing_intent`` sets ``effective_alias``
        # to ``intent.db`` whenever that is not ``None``. So a routed intent
        # leaves the candidate pinned to the required alias, and an unrouted one
        # leaves it unrouted, which is never an alias defect for a top-level
        # result. A surface that seals WITHOUT an expected routing record has no
        # such subsumption and owes the code its own wording. Each site renders
        # the subset it can reach; an arm for a code that cannot arrive would be
        # wording no rejection can ever quote.
        shape_message = (
            f"{method_name} must return an unevaluated, unsliced "
            f"QuerySet of {model_name} rows; got {defect[0]} defect ({defect[1]})."
        )
        messages: dict[str, str] = dict.fromkeys(
            (
                "type",
                "table",
                "evaluated",
                "sliced",
                "projection",
            ),
            shape_message,
        )
        messages["combined"] = f"{method_name} returned a combined queryset; " + (
            _COMBINED_WHAT.format(model=model_name, detail=defect[1])
        )
        messages["routing"] = f"{method_name} changed database routing intent; {defect[1]}."
        raise ConfigurationError(_defect_message(messages, defect, method_name))
    # ``_seal_or_defect`` returns a queryset exactly when it returns no defect, and
    # ``_SIDECAR_RESULT_POLICY`` requires model rows.
    return cast("models.QuerySet[models.Model]", sealed)


def require_orderset_class(
    target_type: type[DjangoType],
    orderset_class: type[OrderSet] | None,
) -> type[OrderSet]:
    """Return the field's captured ``OrderSet``, or reject an ordering call without one.

    Reachable only through a direct call that supplies ``order_by`` to a field
    whose target declares no ``Meta.orderset_class``; over the wire the argument
    is simply not published.
    """
    if orderset_class is None:
        raise ConfigurationError(
            f"Field target {introspection.name(target_type)} has no orderset_class configured.",
        )
    return orderset_class


def apply_sidecar_sync(
    target_type: type[DjangoType],
    set_class: type[FilterSet | OrderSet],
    queryset: models.QuerySet[models.Model],
    input_value: object,
    info: object,
    *,
    model: type[models.Model],
) -> models.QuerySet[models.Model]:
    """Call a sidecar set's ``apply_sync`` and re-seal what it returned.

    The awaitable refusal below names every awaitable kind ``an awaitable``
    (uniform, with no coroutine special-case): this guard fires on any
    awaitable kind and carries no coroutine-compat wording burden, while
    ``reject_async_in_sync_context`` keeps its kind-distinguishing template
    for its hook-result seams.

    The ONE post-sidecar seal the list field and the Relay connection field run
    over a public ``FilterSet.apply_sync`` / ``OrderSet.apply_sync`` return:
    routing intent is frozen before the consumer override receives the
    queryset, and the value it hands back is validated against
    ``_SIDECAR_RESULT_POLICY`` (lazy, model rows of the captured model,
    unsliced, a combinator served as its primary-key set, same routing)
    before any later step sees it. Every
    step after a sidecar can only NARROW the sealed queryset (spec-030
    Decision 7), so an override that widens, re-routes, re-tables or
    pre-evaluates its result is rejected here rather than silently serving
    foreign rows or a wrong page.
    """
    method_name = f"{introspection.name(set_class)}.apply_sync"
    # Frozen BEFORE the override receives the queryset: it can mutate the
    # object it was handed, so a post-call read is not a baseline.
    expected_routing = _snapshot_routing_intent(queryset)
    candidate = set_class.apply_sync(input_value, queryset, info)
    if _disposed_awaitable(candidate):
        raise SyncMisuseError(
            f"{method_name} returned an awaitable in a sync resolver context. "
            f"Make apply_sync synchronous or execute the query asynchronously.",
        )
    return _validate_post_orderset_result(
        target_type,
        expected_routing,
        candidate,
        method_name,
        model=model,
    )


async def apply_sidecar_async(
    target_type: type[DjangoType],
    set_class: type[FilterSet | OrderSet],
    queryset: models.QuerySet[models.Model],
    input_value: object,
    info: object,
    *,
    model: type[models.Model],
) -> models.QuerySet[models.Model]:
    """Async sibling of :func:`apply_sidecar_sync`, running the same one seal.

    The awaited result carries the same ``_SIDECAR_RESULT_POLICY`` contract;
    the extra arms reject a public method that never returned an awaitable at
    all, and one that awaited to a second awaitable.
    """
    method_name = f"{introspection.name(set_class)}.apply_async"
    expected_routing = _snapshot_routing_intent(queryset)
    candidate_awaitable = set_class.apply_async(input_value, queryset, info)
    if not inspect.isawaitable(candidate_awaitable):
        raise ConfigurationError(
            f"{method_name} returned a non-awaitable value "
            f"({introspection.kind(candidate_awaitable)}); expected an awaitable coroutine or Future.",
        )
    candidate = await candidate_awaitable
    if _disposed_awaitable(candidate):
        raise ConfigurationError(
            f"{method_name} returned a residual awaitable value "
            f"({introspection.kind(candidate)}); expected a QuerySet.",
        )
    return _validate_post_orderset_result(
        target_type,
        expected_routing,
        candidate,
        method_name,
        model=model,
    )


def _is_model_column(name: str, model: type[models.Model]) -> bool:
    """Return whether ``name`` (its leading ``-`` already stripped) names a column of ``model``."""
    if name == "pk":
        return True
    return any(name in (field.name, field.attname) for field in model._meta.concrete_fields)


def _is_carried_order_term(entry: object, model: type[models.Model]) -> bool:
    """Return whether a combinator's outer ``order_by`` ``entry`` orders by a ``model`` column.

    Carried: a column name (``"title"``, ``"-title"``, ``"pk"``, a forward
    relation's ``name`` or ``attname``), an exact ``F`` over one, and an exact
    ``OrderBy`` wrapping such an ``F`` (``F(c).asc()`` / ``.desc()``, any
    ``nulls_first`` / ``nulls_last``). Not carried: a lookup or relation span
    (``F("books__title")``), a transform (``Lower(c)``) or any other expression,
    whose value the rewritten single-table query has no column for or would
    multiply rows to reach.
    """
    if isinstance(entry, str):
        return _is_model_column(entry.removeprefix("-"), model)
    if type(entry) is OrderBy:
        entry = entry.expression
    if type(entry) is not F:
        return False
    # django-stubs does not declare ``F.name``, so it is read and proven a string.
    name: object = getattr(entry, "name", None)
    return isinstance(name, str) and _is_model_column(name, model)


def _rewrite_order_term(entry: str | Combinable, model: type[models.Model]) -> str | Combinable:
    """Spell a carried outer ``order_by`` ``entry`` so the rewrite orders exactly as the combinator.

    A combinator orders a string term by the selected column itself, while a
    plain queryset expands a forward relation's ``name`` (``"shelf"``) into the
    related model's ``Meta.ordering``; the rewrite therefore spells a string
    naming a concrete field by that field's ``attname`` (``"-shelf"`` becomes
    ``"-shelf_id"``). An ``F`` / ``OrderBy`` term already resolves to the column
    on both, and every other string (an ``attname``, ``"pk"``) is already the
    column spelling.
    """
    if not isinstance(entry, str):
        return entry
    sign = "-" if entry.startswith("-") else ""
    name = entry.removeprefix("-")
    for field in model._meta.concrete_fields:
        if field.name == name:
            return f"{sign}{field.attname}"
    return entry


# The ``sql.Query`` state ``_combined_lost_property`` and
# ``_pk_membership_query_or_defect`` read, audited over every published Django
# release 5.2.16 .. 6.1.1 (19 releases): ``combinator``, ``combinator_all``,
# ``combined_queries``, ``values_select``, ``select_for_update``, ``order_by``,
# ``standard_ordering`` and ``low_mark`` / ``high_mark`` are class-level
# ``sql.Query`` slots; ``annotation_select``, ``extra_select`` and ``is_sliced``
# are properties. They are read, never patched. In every audited release the
# outer query of a combinator is a clone of branch 0 whose ordering
# (``extra_order_by`` included) ``_combinator_query`` clears, and ``extra()``
# after a combinator raises, so no outer ``extra(order_by=)`` ordering exists to
# lose; ``values(...)`` after a combinator sets only the OUTER projection, which the
# compiler copies into every branch without a ``values()`` of its own (so the
# combinator is computed over those columns); ``reverse()`` after a combinator
# flips the outer ``standard_ordering``; an outer ``select_for_update()`` never
# emits ``FOR UPDATE`` (``SQLCompiler.as_sql``), so it is no lost property.


def _combined_lost_property(
    query: sql.Query,
    model: type[models.Model],
    *,
    outer: bool,
) -> str | None:
    """Name the property a primary-key-set rewrite of ``query`` would lose, or ``None``.

    ``query`` is a combined ``sql.Query``. The rewrite keeps exactly the SET of
    primary keys the combinator selects, so anything the combinator carries
    beyond that set -- duplicate rows, selected annotations, ``extra(select=)``
    aliases, a branch or outer projection, a row lock, an outer ordering the base
    table cannot express, an outer slice -- is a lost property, and the caller fails closed
    on it rather than serving different rows. ``outer`` is ``True`` for the
    query the surface receives and ``False`` for a nested combinator branch,
    whose own ordering and slice stay inside the subquery the rewrite keeps.

    From the seal, every branch is first checked to be over the model's table
    (``_foreign_combined_model``); from the optimizer walker's
    ``OptimizerHint.prefetch`` path it is trusted schema configuration.
    """
    if query.combinator_all:
        return "union(all=True) keeps duplicate rows, which a primary-key set cannot"
    if outer:
        for entry in query.order_by:
            if not _is_carried_order_term(entry, model):
                return (
                    f"its ordering by {entry!r} is not a {introspection.name(model)} column, so the "
                    "rewritten query cannot carry it (it carries a column name or an F() "
                    "over a column, with .asc() / .desc(); never a lookup, transform or "
                    "other expression)"
                )
        if query.is_sliced:
            return "it is sliced, and a LIMIT/OFFSET cannot ride inside the primary-key subquery"
    if query.values_select:
        combined_values: tuple[object, ...] = query.values_select
        cols = ", ".join(repr(col) for col in combined_values)
        if outer:
            return (
                f"it projects .values({cols}) after the combinator, which computes the "
                "combinator over those columns instead of the primary key"
            )
        return (
            f"a nested combinator projects .values({cols}), which the primary-key "
            "subquery cannot re-project"
        )
    # Django's ``_combinator_query`` builds ``combined_queries`` from each branch's
    # ``QuerySet.query``, so every member is a ``sql.Query``.
    branches: tuple[sql.Query, ...] = query.combined_queries
    for branch in branches:
        if branch.combinator:
            nested = _combined_lost_property(branch, model, outer=False)
            if nested is not None:
                return nested
            continue
        if branch.annotation_select:
            names = ", ".join(repr(name) for name in branch.annotation_select)
            return f"a branch selects annotations ({names}) that would be dropped from the rows"
        if branch.extra_select:
            names = ", ".join(repr(name) for name in branch.extra_select)
            return f"a branch selects extra(select=...) aliases ({names}) that would be dropped"
        if branch.values_select:
            branch_values: tuple[object, ...] = branch.values_select
            cols = ", ".join(repr(col) for col in branch_values)
            return (
                f"a branch projects .values({cols}), which the primary-key subquery "
                "cannot re-project"
            )
        if branch.select_for_update:
            return (
                "a branch carries select_for_update(), which the database refuses inside "
                "a compound query"
            )
    return None


def _pk_membership_query_or_defect(
    query: sql.Query,
    model: type[models.Model],
) -> tuple[sql.Query, None] | tuple[None, tuple[str, str]]:
    """Rewrite a combined ``query`` as ``<model>.filter(pk__in=<combined>.values("pk"))``.

    Returns ``(rewritten, None)``: a fresh single-table ``sql.Query`` over
    ``model`` whose one predicate is membership in the combinator's primary-key
    set, with the outer ordering and its direction re-applied
    (``_combined_lost_property`` has proven every entry a column;
    ``_rewrite_order_term`` spells each so it orders exactly as the combinator
    does). Every surface
    can then narrow, project and prefetch through it, which Django supports on no
    combinator. Returns
    ``(None, ("combined", "<combinator>: <lost property>"))`` for a shape the
    rewrite would serve different rows for.
    """
    lost = _combined_lost_property(query, model, outer=True)
    if lost is not None:
        return None, ("combined", f"{query.combinator}: {lost}")
    combined: models.QuerySet[models.Model] = models.QuerySet(model=model, query=query)
    unfiltered: models.QuerySet[models.Model] = models.QuerySet(model=model)
    rewritten = unfiltered.filter(pk__in=combined.order_by().values("pk"))
    if query.order_by:
        rewritten = rewritten.order_by(
            *(_rewrite_order_term(entry, model) for entry in query.order_by),
        )
    # ``reverse()`` after a combinator flips only this flag; carried, the rewrite
    # keeps the reversed order (including a reversed ``Meta.ordering``).
    rewritten.query.standard_ordering = query.standard_ordering
    return rewritten.query, None


def _is_queryset_class(value: object) -> TypeIs[type[models.QuerySet[models.Model, object]]]:
    """Whether ``value`` is a ``QuerySet`` class by its real MRO."""
    return is_class(value) and issubclass(value, models.QuerySet)


def _is_queryset(value: object) -> TypeIs[models.QuerySet[models.Model, object]]:
    """Whether ``value`` is a ``QuerySet`` by its real class, never a ``__class__`` claim."""
    return _is_queryset_class(type(value))


def _foreign_combined_model(query: sql.Query, concrete: type[models.Model] | None) -> str | None:
    """Return the name of the first combinator branch's model off ``concrete``'s table, else ``None``.

    The primary-key rewrite selects this model's rows whose primary key is in the
    combinator's set, so a branch over another model would match rows by an
    unrelated table's primary keys. Nested combinators are walked branch by branch.
    """
    # Django's ``_combinator_query`` builds ``combined_queries`` from each branch's
    # ``QuerySet.query``, so every member is a ``sql.Query`` with its model.
    branches: tuple[sql.Query, ...] = query.combined_queries
    for branch in branches:
        branch_model = branch.model
        if branch_model is None or branch_model._meta.concrete_model is not concrete:
            return introspection.name(branch_model)
        if branch.combinator:
            nested = _foreign_combined_model(branch, concrete)
            if nested is not None:
                return nested
    return None


def _with_prefetch_children_served(
    queryset: _QuerySetT,
    alias: str | None,
) -> tuple[_QuerySetT, None] | tuple[None, tuple[str, str]]:
    """Check and serve each ``Prefetch`` child of ``queryset``, at any depth.

    Django's prefetch hands a child's rows to the lookup's relation without checking
    the child's model (Django ticket #37267), so a child whose concrete model is not
    the relation target's concrete model (or a subclass of it) would populate the
    relation with rows the related type's visibility hook never saw; and a child
    explicitly routed off ``alias`` (the outer effective alias, ``None`` for an
    unrouted parent) would split one resolution across two connections. Both are the
    ``prefetch`` defect. A path ``_prefetch_relation_target_or_none`` cannot resolve
    is left to Django, and an unrouted child inherits the outer alias at fetch.

    Django's prefetch also filters a child by its relation (``.filter()`` /
    ``.extra()``), which it refuses after a combinator, and it hoists a child's own
    lookups into the outer prefetch, whose relation predicate a combinator's compiler
    ignores; so a ``Prefetch(..., queryset=a.union(b))`` child is rewritten the way a
    combined hook result is, however deep it sits. A child over another model's table
    is the ``table`` defect and a shape the rewrite would change is ``combined``.
    ``queryset`` is returned as it is when no child below it changed.
    """
    rewritten: list[PrefetchLookup] = []
    changed = False
    parent = queryset.model
    for lookup in queryset_prefetch_lookups(queryset):
        child = None if is_str(lookup) else lookup.queryset
        if is_str(lookup) or child is None:
            rewritten.append(lookup)
            continue
        path = lookup.prefetch_through
        target = _prefetch_relation_target_or_none(parent, path)
        target_concrete = _concrete_or_none(target)
        child_concrete = _concrete_or_none(child.model)
        if (
            target_concrete is not None
            and child_concrete is not None
            and not issubclass(child_concrete, target_concrete)
        ):
            return None, (
                "prefetch",
                (
                    f"{introspection.name(parent)} prefetch {path!r} queryset is over "
                    f"{introspection.name(child.model)} rows, but the {path!r} relation targets "
                    f"{introspection.name(target)} rows; a prefetch child over an unrelated table "
                    "would populate the relation with rows the related type's visibility "
                    "hook never saw"
                ),
            )
        child_db = queryset_db(child)
        if child_db is not None and child_db != alias:
            return None, (
                "prefetch",
                (
                    f"{introspection.name(parent)} prefetch {path!r} queryset is routed to alias "
                    f"{child_db!r}, but this resolution reads alias {alias!r}; one "
                    "resolution never spans two database connections"
                ),
            )
        served = _served_prefetch_child(child, alias)
        if served[1] is not None:
            return None, served[1]
        if served[0] is child:
            rewritten.append(lookup)
            continue
        replaced = copy.copy(lookup)
        replaced.queryset = served[0]
        rewritten.append(replaced)
        changed = True
    if not changed:
        return queryset, None
    return queryset.prefetch_related(None).prefetch_related(*rewritten), None


def _served_prefetch_child(
    child: _QuerySetT,
    alias: str | None,
) -> tuple[_QuerySetT, None] | tuple[None, tuple[str, str]]:
    """Return ``child`` with its own children checked and combinators served as primary-key sets.

    ``child`` itself is returned when nothing in it changed.
    """
    nested = _with_prefetch_children_served(child, alias)
    if nested[1] is not None:
        return None, nested[1]
    served = nested[0]
    if not served.query.combinator:
        return served, None
    foreign = _foreign_combined_model(served.query, served.model._meta.concrete_model)
    if foreign is not None:
        return None, ("table", foreign)
    served_query = _pk_membership_query_or_defect(served.query, served.model)
    if served_query[1] is not None:
        return None, served_query[1]
    served = served.all()
    served.query = served_query[0]
    return served, None


def _seal_or_defect(
    candidate: object,
    model: type[models.Model],
    required_alias: str | None,
    policy: _SealPolicy[object] = _DEFAULT_SEAL_POLICY,
    *,
    expected_routing: _RoutingIntent | None = None,
) -> tuple[models.QuerySet[models.Model, object], None] | tuple[None, tuple[str, str]]:
    """Return a fresh clone of ``candidate`` for a surface to compose onto, or its defect.

    The single sealing primitive every boundary site runs. Returns
    ``(sealed_queryset, None)`` on success, or ``(None, (code, detail))`` on the
    first defect. The sealed queryset is ``candidate.all()`` (pinned with
    ``.using(required_alias)`` when the candidate is unrouted and an alias is
    required): Django's own clone, of the candidate's own class, carrying its
    query, routing, prefetches and fetch mode, with no fetched rows, no related
    manager's parent instances to install on its rows, and a related manager's
    pending filter baked into the query. The candidate is
    application code's own object and is trusted (GOAL.md "Trust boundary"); the
    checks catch the shapes a surface cannot compose onto.

    The codes ``type`` / ``table`` / ``routing`` / ``evaluated`` / ``sliced`` /
    ``projection`` / ``combined`` / ``prefetch`` / ``alias`` are the one vocabulary
    every message-building site shares (a new code owes an arm at every site that can
    reach it; ``prefetch`` carries its whole clause and ``_defect_message`` renders it
    for every site). The checks run in this order:

    - ``type`` -- not a ``QuerySet`` at all.
    - ``table`` -- the queryset's model, or a combinator branch's, is not the
      registered type's concrete table (a proxy of it is).
    - ``routing`` -- when ``expected_routing`` is given (a sidecar result): the
      candidate's ``_db`` or its router hints differ from the source's, frozen
      before the sidecar method ran.
    - ``evaluated`` -- when ``policy.require_unevaluated``: the result cache is
      populated.
    - ``sliced`` -- when ``policy.reject_sliced`` (every surface that recomposes
      onto the sealed queryset): the query is sliced (a ``LIMIT`` / ``OFFSET``
      was taken). Django forbids reordering or refiltering a sliced query, so
      the next framework transform (a Relay ``.filter(pk=...)``, a connection
      ordering, the cascade's ``.filter(...)`` narrowing) would raise a raw
      ``TypeError`` outside the typed defect contract. The same raw ``TypeError``
      is what Django raises when it refilters a sliced ``Prefetch`` child at fetch
      time, so it is on for the walker's plain-list-relation child too, and off
      for the walker's nested-connection child, whose own gate degrades a sliced
      child instead of recomposing. The connection guard rejects this shape one
      step earlier with a wire-facing ``GraphQLError``; this arm stays because the
      visibility boundary owes authors its own ``ConfigurationError``.
    - ``projection`` -- when ``policy.require_model_rows`` (every surface but the
      cascade): the row iterable is not a ``ModelIterable`` (a ``.values()`` /
      ``.values_list()`` projection). The cascade re-projects the sealed queryset
      to the edge's target column and never iterates it.
    - ``combined`` -- on every surface, when the query carries a
      ``union()`` / ``intersection()`` / ``difference()`` that
      ``_pk_membership_query_or_defect`` cannot rewrite to its primary-key set
      without changing its rows (``_combined_lost_property`` names the lost
      property). Every other combinator is SERVED as that set: the sealed
      queryset is ``<model>.filter(pk__in=<combined>.values("pk"))`` with the
      outer ordering re-applied, a queryset of model rows every surface can
      narrow, re-project and prefetch through, where Django refuses
      ``.filter()`` / ``.only()`` after a combinator and silently drops a
      reverse-FK ``Prefetch``'s parent predicate from one. A branch over another
      model is the ``table`` defect.
    - ``alias`` -- a queryset explicitly routed off ``required_alias``. For a
      top-level source an UNROUTED queryset (``_db is None``) is never an alias
      defect; the seal pins it with ``.using(required_alias)``. For a prefetch
      child (``policy.require_shared_alias``), the child's explicit ``_db`` must
      EQUAL the outer effective alias, including when that alias is ``None`` -- an
      unrouted parent forces an unrouted child, so one resolution never spans two
      connections.
    - ``prefetch`` -- a ``Prefetch`` child, at any depth, over a model that is not
      its relation's target, or explicitly routed off the effective alias
      (``_with_prefetch_children_served``). A combined child is served like a
      combined candidate.
    """
    if not _is_queryset(candidate):
        return None, ("type", introspection.kind(candidate))
    concrete = model._meta.concrete_model
    if candidate.model._meta.concrete_model is not concrete:
        return None, ("table", introspection.name(candidate.model))
    db = queryset_db(candidate)
    if expected_routing is not None:
        hints = queryset_hints(candidate)
        if db != expected_routing.db or not _routing_hints_equal(hints, expected_routing.hints):
            return None, (
                "routing",
                (
                    f"expected db={_routing_repr(expected_routing.db)}, "
                    f"hints={_routing_repr(expected_routing.hints)}, got "
                    f"db={_routing_repr(db)}, hints={_routing_repr(hints)}"
                ),
            )
    # Read before the clone: ``all()`` starts the clone with no fetched rows.
    if policy.require_unevaluated and candidate._result_cache is not None:
        return None, ("evaluated", "the result cache is populated")
    queryset = candidate.all()
    # A related manager's parent instance would be cached on every row before any
    # ``Prefetch`` the hook added runs, and Django skips a ``Prefetch`` on a relation it
    # finds cached, so the clone starts with none: the rows load as an unplanned read does.
    clear_queryset_known_related_objects(queryset)
    query = queryset.query
    if policy.reject_sliced and query.is_sliced:
        return None, ("sliced", f"rows {query.low_mark}:{query.high_mark}")
    if policy.require_model_rows and not _yields_model_rows(queryset):
        return None, ("projection", introspection.name(queryset._iterable_class))
    if query.combinator:
        foreign = _foreign_combined_model(query, concrete)
        if foreign is not None:
            return None, ("table", foreign)
        rewritten = _pk_membership_query_or_defect(query, queryset.model)
        if rewritten[1] is not None:
            return None, rewritten[1]
        queryset.query = rewritten[0]
    if policy.require_shared_alias:
        # A prefetch child: its explicit ``_db`` must EQUAL the outer effective alias,
        # INCLUDING when that alias is ``None`` (an unrouted parent forces an unrouted
        # child). ``required_alias`` here IS the outer effective alias.
        if db is not None and db != required_alias:
            return None, ("alias", str(db))
    elif required_alias is not None and db is not None and db != required_alias:
        return None, ("alias", str(db))
    with_children = _with_prefetch_children_served(
        queryset,
        db if db is not None else required_alias,
    )
    if with_children[1] is not None:
        return None, with_children[1]
    queryset = with_children[0]
    if required_alias is not None and db is None:
        queryset = queryset.using(required_alias)
    return queryset, None


def materialized_rows(value: object) -> list[object] | None:
    """Return the rows a row source has already fetched, or ``None`` when it has none.

    Django's prefetch cache holds a queryset whose ``_result_cache`` is the list
    of rows it fetched, and returning that list directly is what lets a
    prefetched relation skip a clone and a copy per parent row. Any ``QuerySet``
    answers from that slot; every other shape answers ``None`` and is bounded as
    the source it is.
    """
    if not _is_queryset(value):
        return None
    return value._result_cache


# one (``{model}`` is the model whose primary keys the rewrite selects, ``{detail}`` the
# seal's ``"<combinator>: <lost property>"``): each surface prefixes its own subject, and
# the contract and advice stay one text.
_COMBINED_WHAT = (
    "the visibility boundary serves a combined queryset as the set of {model} primary keys "
    "it selects (every surface narrows, projects or prefetches through that set with "
    ".filter(pk__in=...)), and this one cannot be reduced to that set without changing its "
    "rows: {detail}. Return an uncombined QuerySet (compose the branches with Q objects or "
    "pk__in subqueries) or drop that property from the branches."
)


def _coerced_manager_queryset(
    manager: models.Manager[models.Model],
) -> models.QuerySet[models.Model]:
    """Coerce a ``Manager`` to its ``QuerySet``, or fail closed when ``all()`` is not one.

    A custom Manager's ``all()`` can return a plain list or generator by
    mistake, which would otherwise be taken for the deliberate plain-iterable
    bypass and skip the visibility hook. The returned queryset still runs the
    full source / result checks (concrete table, alias). ``all()`` is the
    Manager's own code: whatever it raises propagates.
    """
    queryset = manager.all()
    if not is_queryset(queryset):
        raise ConfigurationError(
            f"A {introspection.kind(manager)}.all() coercion must produce a QuerySet, but "
            f"returned {introspection.kind(queryset)}; a Manager that degrades into a list "
            f"or other non-queryset cannot enter the visibility boundary and must not "
            f"be treated as the deliberate plain-iterable bypass.",
        )
    return queryset


def _defect_message(messages: dict[str, str], defect: tuple[str, str], subject: str) -> str:
    """Return ``subject``'s wording for a ``(code, detail)`` seal defect.

    The seal's defect codes are a closed, canonically ordered set, but each
    message-building site renders only the subset IT can reach, so a ladder
    ending in an unconditional branch for its own last code is tempting. That
    shape cannot fail loudly: a code added to the seal without an arm at a site does
    not raise there, it MISLABELS -- the schema author is told about an alias
    mismatch or a wrong table for a rejection that was neither. Dispatch is
    exhaustive instead, and an unrendered code says exactly that, so the defect
    still fails closed and the missing arm is legible in the message.

    Each site owns its own prose (a cascade edge names the edge, a read surface
    names ``get_queryset``); what is shared is the dispatch and the
    exhaustiveness, plus the clause text no surface respells: the
    combined-queryset contract (``_COMBINED_WHAT``), composed under the site's own
    subject, and the ``prefetch`` defect, whose detail names the child and the
    relation it was refused for and is rendered here for every site.
    """
    code, detail = defect
    if code == "prefetch":
        return f"{subject} was refused: its {detail}."
    message = messages.get(code)
    if message is None:
        return (
            f"{subject} was rejected by the visibility boundary with the {code!r} defect "
            f"({detail}), which this surface declares no wording for. This is a framework "
            f"defect: a seal defect code was added without an arm at this site."
        )
    return message


def _visibility_result_error(
    type_cls: type[DjangoType],
    model: type[models.Model],
    required_alias: str | None,
    defect: tuple[str, str],
    render_error: Callable[[str, str], str] | None,
) -> ConfigurationError:
    """Build the fail-closed error for a defective ``get_queryset`` result.

    ``render_error`` is the caller-supplied error-rendering seam: a
    ``(code, detail) -> str`` callable whose message replaces the default
    wording wholesale. The cascade passes one so its path-rich per-edge
    prose (``"... for the cascade subquery on Model.field ..."``) survives
    the checks moving into this shared boundary; surfaces without bespoke
    prose take the defaults below.
    """
    code, detail = defect
    if render_error is not None:
        return ConfigurationError(render_error(code, detail))
    name = introspection.name(type_cls)
    model_name = introspection.name(model)
    return ConfigurationError(
        _defect_message(
            {
                "type": (
                    f"{name}.get_queryset must return a QuerySet or Manager of "
                    f"{model_name} rows; got {detail}. A list / generator / iterable has no "
                    f"lazy query for the surface to compose into, and None discards the "
                    f"visibility contract entirely."
                ),
                "table": (
                    f"{name}.get_queryset returned a {detail} queryset; the "
                    f"visibility contract composes over {model_name}'s concrete table "
                    f"(proxy siblings are compatible, MTI children and unrelated models "
                    f"are not)."
                ),
                "sliced": (
                    f"{name}.get_queryset returned a sliced queryset ({detail}); "
                    f"the surface composes further filters and ordering onto the hook result, "
                    f"and Django forbids refiltering or reordering a sliced query, so the next "
                    f"transform would raise a raw TypeError outside the visibility contract. "
                    f"Return the unsliced queryset and let the surface paginate."
                ),
                "combined": (
                    f"{name}.get_queryset returned a combined queryset; "
                    + _COMBINED_WHAT.format(model=model_name, detail=detail)
                ),
                "projection": (
                    f"{name}.get_queryset returned a {detail} projection; the "
                    f"visibility contract composes over {model_name} model rows, not a "
                    f".values() / .values_list() (or custom-iterable) projection whose rows "
                    f"are not {model_name} instances. Return a queryset of model rows."
                ),
                "alias": (
                    f"{name}.get_queryset returned a queryset routed to alias "
                    f"{detail!r}, but this resolution is pinned to alias {required_alias!r}; "
                    f"a visibility hook cannot re-route a pinned resolution. Remove the "
                    f".using(...) call."
                ),
            },
            defect,
            f"{name}.get_queryset",
        ),
    )


def _captured_model(
    type_cls: type[DjangoType],
    model: type[models.Model] | None,
) -> type[models.Model]:
    """Return the caller's already-captured model, else read one for ``type_cls``.

    The seam that lets a surface holding its target's ``DjangoTypeDefinition``
    spend its ONE definition read at construction and hand the model down,
    while every type-keyed caller keeps the convenience of naming only the
    type. Both seals of one visibility call take the same value, so the source
    seal and the result seal cannot be validated against two different models -
    which is precisely what a second read of a stateful target's
    ``__django_strawberry_definition__`` could arrange.
    """
    return model_for(type_cls) if model is None else model


@overload
def _prepared_visibility_source(
    type_cls: type[DjangoType],
    queryset: _QuerySetT,
    *,
    model: type[models.Model] | None = ...,
    render_error: Callable[[str, str], str] | None = ...,
    policy: _SealPolicy[object] = ...,
) -> tuple[_QuerySetT, str | None]: ...
@overload
def _prepared_visibility_source(
    type_cls: type[DjangoType],
    queryset: object,
    *,
    model: type[models.Model] | None = ...,
    render_error: Callable[[str, str], str] | None = ...,
    policy: _SealPolicy[object] = ...,
) -> tuple[models.QuerySet[models.Model, object], str | None]: ...
def _prepared_visibility_source(
    type_cls: type[DjangoType],
    queryset: object,
    *,
    model: type[models.Model] | None = None,
    render_error: Callable[[str, str], str] | None = None,
    policy: _SealPolicy[object] = _DEFAULT_SEAL_POLICY,
) -> tuple[models.QuerySet[models.Model, object], str | None]:
    """Validate and SEAL the source queryset before the visibility hook runs.

    Returns ``(sealed_queryset, required_alias)``. The source is sealed through
    ``_seal_or_defect`` before the hook runs - it must be a real ``QuerySet``
    over the registered type's concrete table, and whatever else ``policy`` (a
    ``_SealPolicy``, default ``_DEFAULT_SEAL_POLICY``) requires: model rows and no
    slice (the cascade admits a projection), with a combinator served as its
    primary-key set. The sealed object is a fresh clone of the source, of the
    source's own class, so a hook can call its project ``QuerySet`` methods and
    never receives the caller's object itself.
    An already-evaluated source seals to a fresh, unevaluated queryset (the
    clone does not copy ``_result_cache``), so cached rows never
    reach the hook. The required alias is then
    resolved in priority order:

    1. An active write pipeline's alias - the sealed source is pinned through
       ``pin_write_queryset`` (a ``.using()`` on the sealed source),
       which fail-closes an explicitly divergent source alias.
    2. The sealed source's own explicit ``_db`` (a caller that routed with
       ``.using(...)`` keeps that routing through the hook).
    3. ``None`` - no required alias; an unpinned read hook keeps its
       documented ability to choose ``.using(alias)`` itself.

    ``render_error`` mirrors ``_normalized_visibility_result``'s parameter of the
    same name: a ``(code, detail) -> str`` callable whose message replaces the
    default wording wholesale. A surface that is not ``apply_type_visibility``
    itself - ``permissions.py::apply_cascade_permissions``, whose source is a
    consumer hook's own argument - passes one so a source defect is attributed
    to the call the consumer actually made. Surfaces without bespoke prose take
    the defaults below.

    ``model`` is the caller's captured model (``_captured_model``): a field that
    already holds its target's definition passes it so no request-time read of
    ``__django_strawberry_definition__`` decides which table this seal validates
    against. Omitted, the model is read from ``type_cls``.

    Resolver-source ``Manager`` coercion stays in ``normalize_query_source``;
    framework-created seeds are querysets by construction. Preparation composes
    lazy query state only; it executes zero SQL.

    A source typed as a ``QuerySet`` class seals to that class (the first
    overload): ``_seal_or_defect`` returns the source's own clone, and its
    combinator rewrite yields model rows only from a model-row combinator (a
    projected one fails closed with the ``combined`` defect), so neither the
    class, the model nor the row type changes. Only an untyped ``object`` source
    is typed ``QuerySet[Model, object]``.
    """
    model = _captured_model(type_cls, model)
    candidate = _seal_or_defect(queryset, model, None, policy)
    if candidate[1] is not None:
        defect = candidate[1]
        code, detail = defect
        if render_error is not None:
            raise ConfigurationError(render_error(code, detail))
        name = introspection.name(type_cls)
        model_name = introspection.name(model)
        raise ConfigurationError(
            _defect_message(
                {
                    "type": (
                        f"apply_type_visibility requires a QuerySet of {model_name} rows "
                        f"for {name}; got {detail}. Coerce a Manager with .all(); "
                        f"a list has no lazy query for the hook to narrow."
                    ),
                    "table": (
                        f"apply_type_visibility for {name} requires a QuerySet over "
                        f"{model_name}'s concrete table; got a {detail} queryset (proxy "
                        f"siblings are compatible, MTI children and unrelated models are not)."
                    ),
                    "sliced": (
                        f"apply_type_visibility for {name} got a sliced source "
                        f"queryset ({detail}); the visibility hook and the surface compose "
                        f"further filters and ordering onto the source, and Django forbids "
                        f"refiltering or reordering a sliced query. Pass the unsliced queryset "
                        f"and let the surface paginate."
                    ),
                    "combined": (
                        f"apply_type_visibility for {name} got a combined source queryset; "
                        + _COMBINED_WHAT.format(model=model_name, detail=detail)
                    ),
                    "projection": (
                        f"apply_type_visibility for {name} got a {detail} projection "
                        f"source; the visibility contract composes over {model_name} model "
                        f"rows, not a .values() / .values_list() (or custom-iterable) "
                        f"projection."
                    ),
                    "alias": (
                        f"apply_type_visibility for {name} got a source queryset routed to "
                        f"alias {detail!r}, but a prefetch child shares its parent's database "
                        f"connection and this one's parent is unrouted. Remove the "
                        f".using(...) call."
                    ),
                },
                defect,
                f"The apply_type_visibility source for {name}",
            ),
        )
    sealed = candidate[0]
    pipeline = current_write_pipeline()
    if pipeline is not None:
        sealed = pin_write_queryset(
            sealed,
            pipeline.alias,
            owner=f"The {introspection.name(type_cls)} visibility source",
        )
        required_alias = pipeline.alias
    else:
        required_alias = queryset_db(sealed)
    return sealed, required_alias


def _normalized_visibility_result(
    type_cls: type[DjangoType],
    result: object,
    required_alias: str | None,
    render_error: Callable[[str, str], str] | None = None,
    *,
    model: type[models.Model] | None = None,
    policy: _SealPolicy[object] = _DEFAULT_SEAL_POLICY,
) -> models.QuerySet[models.Model, object]:
    """Normalize a ``get_queryset`` hook result into a composable, correctly-routed queryset.

    The shared result contract both colored visibility runners apply (the sealed
    boundary): a ``Manager`` is coerced exactly once through
    ``_coerced_manager_queryset`` (which preserves the manager's explicit
    routing and fails a degrade-to-non-queryset closed); the coerced value is
    then SEALED through ``_seal_or_defect``, so anything that is not a
    ``QuerySet`` of the registered type's model rows (``None``, lists,
    generators, async generators, custom iterables, unrelated / MTI-child
    models, cross-model unions, ``.values()`` projections on non-cascade
    surfaces) fails closed. The return value is a fresh clone of the hook's
    result, of its own class, so the surface never composes onto or windows the
    hook's own object.

    Alias handling: the seal pins an unrouted result onto ``required_alias`` when
    an alias is required, preserves an explicitly matching one and fails an
    explicitly divergent one closed with the ``alias`` defect; with no required
    alias the hook's own ``_db`` is preserved. Normalization composes lazy query
    state only and executes zero SQL.

    ``model`` is the caller's captured model (``_captured_model``), the SAME
    value ``_prepared_visibility_source`` took for this call: the source seal
    and the result seal of one resolution validate against one model, never two
    answers to two reads.
    """
    model = _captured_model(type_cls, model)
    result = normalize_query_source(result)[0]
    sealed = _seal_or_defect(result, model, required_alias, policy)
    if sealed[1] is not None:
        raise _visibility_result_error(type_cls, model, required_alias, sealed[1], render_error)
    return sealed[0]


@overload
def apply_type_visibility_sync(
    type_cls: type[DjangoType],
    queryset: models.QuerySet[models.Model, object],
    info: object,
    async_recourse: str,
    *,
    model: type[models.Model] | None = ...,
    render_error: Callable[[str, str], str] | None = ...,
) -> models.QuerySet[models.Model]: ...
@overload
def apply_type_visibility_sync(
    type_cls: type[DjangoType],
    queryset: models.QuerySet[models.Model, object],
    info: object,
    async_recourse: str,
    *,
    model: type[models.Model] | None = ...,
    render_error: Callable[[str, str], str] | None = ...,
    policy: _SealPolicy[_RowT],
) -> models.QuerySet[models.Model, _RowT]: ...
def apply_type_visibility_sync(
    type_cls: type[DjangoType],
    queryset: models.QuerySet[models.Model, object],
    info: object,
    async_recourse: str,
    *,
    model: type[models.Model] | None = None,
    render_error: Callable[[str, str], str] | None = None,
    policy: _SealPolicy[object] = _DEFAULT_SEAL_POLICY,
) -> models.QuerySet[models.Model, object]:
    """Run ``type_cls.get_queryset`` in a sync context; reject async hooks loudly.

    Decision 9 makes a consumer's ``DjangoType.get_queryset`` allowed to
    be sync or async, but a sync resolver context cannot await an async
    hook safely (event-loop edge cases dominate the bridge). On the sync
    path we therefore close the unawaited coroutine to silence the
    "coroutine was never awaited" warning and raise a named
    ``SyncMisuseError`` (a ``ConfigurationError`` subclass that also
    inherits ``RuntimeError``) that points the consumer at the correct
    recourse for the surface that called in.

    The source is prepared and the result normalized through the shared sealed
    boundary (``_prepared_visibility_source`` / ``_normalized_visibility_result``):
    the source and the hook result are each checked (shape, concrete table,
    model rows, alias) and handed on as a fresh clone of their own class, with
    required-alias resolution (write pipeline > explicit source ``.using`` >
    none), Manager coercion, and fail-closed rejection of every shape a surface
    cannot compose onto. ``SyncMisuseError`` stays reserved for this sync
    boundary; every other defect is a plain ``ConfigurationError``.

    ``async_recourse`` is the surface-specific guidance appended to the
    error; every caller passes its own recourse (the cascade, for instance, has
    no async-native walk -- its twin wraps this same sync walk -- so it tells
    the consumer to make the target hook sync or scope ``fields=`` rather
    than reach for an async resolver that cannot help).
    ``render_error`` is the result-normalization error seam
    (``_visibility_result_error``): the cascade supplies its path-rich
    per-edge prose; other surfaces take the shared defaults.
    ``policy`` is the seal's option set (``_SealPolicy``), applied to BOTH the
    source and the result so the two seals of one call cannot diverge. It
    defaults to ``_DEFAULT_SEAL_POLICY`` (model rows, no slice, a combinator
    served as its primary-key set); ``permissions.py`` passes ``_CASCADE_SEAL_POLICY`` and the
    optimizer walker's prefetch-child plan path passes one of its two child
    policies -- ``_PREFETCH_CHILD_POLICY`` for a nested-connection child
    (``spec-045-visibility_boundary-0_0_14`` Decision 5 degrade-to-unplanned,
    plus the shared-alias requirement) and ``_LIST_RELATION_CHILD_POLICY`` for a
    plain list relation, which differs only in keeping the slice rejection.
    ``model`` is the captured-model seam (``_captured_model``): the field
    factories hand down the model off the ONE definition they read at
    construction, so neither seal of this call re-reads
    ``__django_strawberry_definition__``. Type-keyed callers omit it.
    """
    queryset, required_alias = _prepared_visibility_source(
        type_cls,
        queryset,
        model=model,
        policy=policy,
    )
    result = type_cls.get_queryset(queryset, info)
    result = reject_async_in_sync_context(
        result,
        owner=introspection.name(type_cls),
        method="get_queryset",
        context="resolver",
        recourse=async_recourse,
    )
    # No identity fast path: ``result is queryset`` proves object identity, not
    # immutability. A hook can evaluate or re-route the sealed source and return the
    # SAME object, so the result is ALWAYS re-sealed -- the second seal's clone drops
    # any fetched rows and re-checks post-hook state (spec-045 Decision 3).
    return _normalized_visibility_result(
        type_cls,
        result,
        required_alias,
        render_error,
        model=model,
        policy=policy,
    )


def related_visibility_queryset(
    related_model: type[models.Model],
    info: object,
    async_recourse: str,
) -> models.QuerySet[models.Model] | None:
    """Return the related model's visibility-scoped queryset, or ``None`` when it has no primary.

    The ``registry.get(related_model)`` resolve + the "scope through the primary
    ``DjangoType.get_queryset`` visibility hook, else no contract" branch that four
    relation surfaces open with (``visible_related_object`` /
    ``visible_related_objects`` here, the model
    ``utils/write_values.py::decode_visible_relation``, and the serializer
    ``rest_framework/resolvers.py::_scope_specs_over_serializer``). ``None`` means
    "the related model has no registered primary ``DjangoType``" - a raw-pk relation
    with no visibility contract - and each caller keeps its OWN None-handling
    explicit (default-manager existence, an existence-only check, or skip), because
    that tail genuinely diverges per surface. Single-sites only the resolve + the
    visibility-scoping call, so the ONE place a drift is a data-leak bug class is
    written once. An ``async def get_queryset`` met here raises
    ``SyncMisuseError`` (inherited from ``apply_type_visibility_sync``).
    """
    related_type = registry.get(related_model)
    if related_type is None:
        return None
    return apply_type_visibility_sync(
        related_type,
        initial_queryset(related_type),
        info,
        async_recourse,
    )


def related_visibility_queryset_or_default(
    related_model: type[models.Model],
    info: object,
    async_recourse: str,
) -> models.QuerySet[models.Model]:
    """Return the visibility-scoped queryset, falling back to the default manager.

    The "no primary ``DjangoType`` => default-manager, no visibility contract"
    fallback ``visible_related_object`` and ``visible_related_objects`` both
    opened with - a security-adjacent rule written once: a related model
    with a registered primary is scoped through its ``get_queryset`` visibility
    hook; one without gets its plain ``_default_manager.all()`` (existence
    semantics only). Each caller keeps its own tail (``.filter(pk=pk).first()``
    vs the batched ``pk__in`` present-map).
    """
    queryset = related_visibility_queryset(related_model, info, async_recourse)
    if queryset is None:
        return base_queryset(related_model)
    return queryset


def relation_target_type(
    related_model: type[models.Model],
    *,
    root: type[DjangoType] | None = None,
) -> type[DjangoType] | None:
    """Return the ``DjangoType`` a relation path reaching ``related_model`` rows answers for.

    The resolution for a relation hop no ``RelatedFilter`` / ``RelatedOrder``
    declares: a relation-key leaf over such a relation, a flat path crossing one,
    and each intermediate model of a declaration whose ``field_name`` spans
    several relations. ``root`` is the exact type the walking set is bound to: a
    path re-entering its table answers with ``root`` itself, never the model's
    primary type, so a set bound to a secondary type reads the secondary's hook.

    Re-entry is by table: ``related_model`` and ``root``'s model share one
    ``_meta.concrete_model``. A proxy reads its concrete model's table, so a
    proxy-typed root re-entering the concrete model, a concrete root reaching a
    relation declared to one of its proxies, and a sibling proxy all answer with
    ``root``. Multi-table-inheritance parent and child are different tables: a
    path from a child-typed root reaching parent rows answers with the parent's
    type, and one reaching the child model answers with ``root``. Any other
    model answers with ``registry.get``'s type; ``None`` when it has none.
    """
    if (
        root is not None
        and model_for(root)._meta.concrete_model is related_model._meta.concrete_model
    ):
        return root
    return registry.get(related_model)


def relation_visibility_type(
    related_model: type[models.Model],
    *,
    root: type[DjangoType] | None = None,
) -> type[DjangoType] | None:
    """Return the type whose ``get_queryset`` scopes ``related_model`` rows a path reaches, or ``None``.

    ``relation_target_type``'s type when it declares a ``get_queryset`` of its
    own: ``root`` for a path re-entering its table (the same
    ``_meta.concrete_model``, proxies included), the registered type otherwise.
    ``None`` for a model with no registered type and for a type keeping the
    identity default hook (scoping would change no row): such a hop reads the
    raw relation, as Django's join does.
    """
    related_type = relation_target_type(related_model, root=root)
    if related_type is None or not related_type.has_custom_get_queryset():
        return None
    return related_type


def relation_path_visibility_types(
    model: type[models.Model],
    relation_path: str,
    *,
    root: type[DjangoType] | None = None,
) -> tuple[type[DjangoType] | None, ...]:
    """Return ``relation_visibility_type`` of each model ``relation_path`` reaches from ``model``.

    One entry per relation hop ``utils/relations.py::leading_relation_hops``
    reads, in path order, each for the model that hop's join reaches.
    """
    return tuple(
        relation_visibility_type(hop.target_model, root=root)
        for hop in leading_relation_hops(model, relation_path)
    )


def pks_present(
    queryset: models.QuerySet[models.Model],
    query_pks: Iterable[object],
    key_attname: str | None = None,
) -> dict[object, object]:
    """Map the ``identity_key`` of each pk among ``query_pks`` present in ``queryset`` to its key.

    The ``queryset.filter(pk__in=...)`` lookup the relation membership checks share:
    the model ``utils/write_values.py::decode_visible_relation_ids`` and the
    serializer ``visible_related_objects`` both build this present-map in one query,
    keyed by each present pk's ``identity_key`` through ``queryset``'s pk field, the
    basis ``pks_all_present`` keys the requested pks by (the keys are the present set),
    so a requested pk matches the row whose pk holds the same column value however it
    is spelled (``"3"`` and ``3``, ``2.50`` and a stored ``2.5``). Single-sites the query + the
    comparison key so the no-existence-leak comparison basis cannot drift.

    Each value is the key a relation stores for that row. ``key_attname`` ``None``
    reads the pk alone (``values_list("pk", flat=True)``), so the value is the pk; a
    relation keyed by another column (a ``to_field``) names it and the same query
    reads it beside the pk, over ``linkable_rows`` only: a row whose key column is
    ``NULL`` is left out, the same absence as a hidden or missing row.

    Inside an active write pipeline (``utils/write_transaction.py``) the query is
    pinned to the operation's write alias - a hook-re-routed queryset fails
    closed - and, when the operation locks (``Meta.select_for_update``), the
    membership read doubles as the relation-target row lock: a base-manager
    ``SELECT ... FOR UPDATE`` constrained by the (pinned) queryset's pk subquery,
    so an FK / M2M target confirmed visible here cannot be deleted out from under
    the write before the transaction commits. The locked rows are then confirmed
    by a fresh visibility read (``pipeline_rows_visible_after_lock``): a row a
    concurrent commit hid while this read waited on its lock is absent. Read
    surfaces run with no pipeline context, so the lock and re-read are skipped.
    """
    scoped = linkable_rows(
        pipeline_scoped_queryset(queryset, queryset.model),
        key_attname,
    ).filter(pk__in=list(query_pks))
    if key_attname is None:
        pks: list[object] = list(scoped.values_list("pk", flat=True))
        rows: list[tuple[object, object]] = [(pk, pk) for pk in pks]
    else:
        rows = list(scoped.values_list("pk", key_attname))
    still_visible = pipeline_rows_visible_after_lock(
        queryset,
        queryset.model,
        [pk for pk, _key in rows],
    )
    if still_visible is not None:
        rows = [(pk, key) for pk, key in rows if pk in still_visible]
    pk_field = queryset.model._meta.pk
    return {identity_key(pk_field, pk): key for pk, key in rows}


def linkable_rows(
    queryset: models.QuerySet[_ModelT, _RowT],
    key_attname: str | None,
) -> models.QuerySet[_ModelT, _RowT]:
    """Narrow ``queryset`` to the rows a relation storing ``key_attname`` can link.

    A relation keyed by a column other than the related pk (a ``to_field``; the
    ``key_attname`` of ``utils/relations.py::non_pk_relation_key_attname``) stores that
    column's value. A row whose key is ``NULL`` names no row through it: storing the
    key would clear the relation rather than link the row. So the row is left out,
    the same absence as a hidden or missing row. ``None`` (a relation keyed by the
    pk) keeps every row.
    """
    if key_attname is None:
        return queryset
    return queryset.filter(**{f"{key_attname}__isnull": False})


def pks_all_present(
    pk_field: ModelField | None,
    declared_pks: Iterable[object],
    present: AbstractSet[object],
) -> bool:
    """Return whether every ``declared_pks`` member's ``identity_key`` is in ``present``.

    The subset-membership test the model relation guard
    (``utils/write_values.py::decode_visible_relation_ids``) and the serializer M2M
    decoder (``rest_framework/resolvers.py::_decode_relation_multi``) share: a
    ``declared`` set is fully present iff its members, keyed through ``pk_field`` (the
    related model's pk), are a subset of the ``present`` set (typically the keys of
    ``pks_present``'s map, keyed the same way). A missing / hidden member fails the
    subset check, which each caller maps to the uniform field-keyed relation error -
    the same no-existence-leak outcome.
    """
    return {identity_key(pk_field, pk) for pk in declared_pks} <= present


def visible_related_object(
    related_model: type[models.Model],
    pk: object,
    info: object,
    async_recourse: str,
    key_attname: str | None = None,
) -> models.Model | None:
    """Resolve the VISIBLE related object by pk through the related primary's ``get_queryset``.

    The object-returning visibility-on-every-branch query, single-sited so the
    form AND serializer relation decoders share ONE implementation rather than
    forking a second object-returning decoder. Resolves the related model's primary
    ``DjangoType`` via the registry and runs the SAME visibility hook every read
    surface applies (``related_visibility_queryset`` =
    ``apply_type_visibility_sync(initial_queryset(...))``), so a writer cannot
    attach a row they could not *see*. Returns the visible object or ``None``
    (hidden / missing - the caller maps ``None`` to the field-keyed ``FieldError``,
    indistinguishable). The decoder needs the OBJECT (the form converts it to its
    ``to_field_name`` key; the serializer reduces it to the pk), which the ``036``
    ``utils/errors.py::relation_field_error`` does not return, so it cannot call
    that helper -
    but it reuses the same primitives so the query shape is identical. An ``async
    def get_queryset`` met here raises ``SyncMisuseError``.

    The related model has a primary type only when a typed relation input was
    generated for it; a raw-pk relation's primary is resolved the same way
    (``registry.get``), and a model with no primary still resolves via the default
    manager (no visibility contract to apply). ``async_recourse`` is required: the
    form and serializer paths pass their own surface-specific wording, matching
    ``related_visibility_queryset``.

    The helper accepts a raw pk AFTER a flavor-specific decoder has chosen that
    branch; it does NOT imply every generated GraphQL relation input accepts both a
    raw pk and a GlobalID (the input exposes one strategy-dependent shape).

    ``key_attname`` names the column a relation keyed by another column stores
    (``linkable_rows``): a visible row whose key is ``NULL`` is ``None`` here, the same
    answer as a hidden or missing row.
    """
    # The visibility-or-default-manager base is single-sited in
    # ``related_visibility_queryset_or_default``. Inside an
    # active write pipeline the read is pinned to the write alias (fail-closed on
    # a hook alias switch) and - when the operation locks - acquired as a
    # base-manager ``FOR UPDATE`` constrained by the visibility pk subquery, the
    # same relation-target lock (and post-lock visibility re-read) the batched
    # membership check applies.
    queryset = related_visibility_queryset_or_default(related_model, info, async_recourse)
    obj = (
        linkable_rows(pipeline_scoped_queryset(queryset, related_model), key_attname)
        .filter(pk=pk)
        .first()
    )
    if obj is None:
        return None
    still_visible = pipeline_rows_visible_after_lock(queryset, related_model, [pk_of(obj)])
    return None if still_visible is not None and pk_of(obj) not in still_visible else obj


def visible_related_objects(
    related_model: type[models.Model],
    pks: Iterable[object],
    info: object,
    async_recourse: str,
    key_attname: str | None = None,
) -> dict[object, object]:
    """Map the VISIBLE pks among ``pks`` to their stored keys in ONE visibility-scoped query.

    The BATCHED counterpart to ``visible_related_object``: instead of one visibility query per
    id (the per-element multi-relation decode), decode/type-check all ids first, then confirm
    the whole set's visibility in ONE ``pk__in`` query through the related primary
    ``DjangoType.get_queryset`` (or the target's default manager when no primary is registered -
    no visibility contract). Returns ``pks_present``'s map: the pks actually visible (each
    keyed by its ``identity_key``, the column's own value) to the value a relation keyed by
    ``key_attname`` stores for each (the pk itself when ``None``); the caller asserts the
    REQUESTED set is a subset of its keys, so a hidden / missing member collapses to the same
    field-keyed relation error (no existence leak), exactly as the single decoder does. An
    ``async def get_queryset`` raises ``SyncMisuseError``. ``related_model`` has a primary type
    only when a typed relation input was generated for it; a raw-pk relation resolves its
    primary the same way (``registry.get``).
    """
    # The visibility-or-default-manager base is single-sited in
    # ``related_visibility_queryset_or_default``.
    queryset = related_visibility_queryset_or_default(related_model, info, async_recourse)
    return pks_present(queryset, pks, key_attname)


@overload
async def apply_type_visibility_async(
    type_cls: type[DjangoType],
    queryset: models.QuerySet[models.Model, object],
    info: object,
    *,
    model: type[models.Model] | None = ...,
    render_error: Callable[[str, str], str] | None = ...,
) -> models.QuerySet[models.Model]: ...
@overload
async def apply_type_visibility_async(
    type_cls: type[DjangoType],
    queryset: models.QuerySet[models.Model, object],
    info: object,
    *,
    model: type[models.Model] | None = ...,
    render_error: Callable[[str, str], str] | None = ...,
    policy: _SealPolicy[_RowT],
) -> models.QuerySet[models.Model, _RowT]: ...
async def apply_type_visibility_async(
    type_cls: type[DjangoType],
    queryset: models.QuerySet[models.Model, object],
    info: object,
    *,
    model: type[models.Model] | None = None,
    render_error: Callable[[str, str], str] | None = None,
    policy: _SealPolicy[object] = _DEFAULT_SEAL_POLICY,
) -> models.QuerySet[models.Model, object]:
    """Run ``type_cls.get_queryset`` in an async context, awaiting awaitables.

    A custom synchronous ``get_queryset`` runs in ONE thread-sensitive worker
    (``run_in_one_sync_boundary``), never on the event loop: a hook may read the
    database (``user.has_perm``, an ``.exists()``, a cascade walk) and Django
    refuses that on the loop thread. The identity default runs inline, because it
    is package code that does no I/O. An ``async def`` hook is called here and
    its coroutine awaited before the caller's tail runs (spec-015 Decision 9), so
    no caller invokes ``.filter`` on a coroutine - and a synchronous hook that
    returns an awaitable has it awaited here after its worker returns.

    The hook is invoked once and AT MOST ONE returned awaitable is awaited;
    a second-level awaitable after that await is malformed (an ``async def``
    returning another coroutine / future) and fails closed - never a
    recursive await over an unbounded chain. The source and result then run
    the same shared boundary as the sync runner
    (``_prepared_visibility_source`` / ``_normalized_visibility_result``),
    so the two colored paths cannot drift. ``render_error`` and ``policy`` are
    the sync runner's own seams, declared here for that reason: a surface whose
    seal differs from the default (the cascade's ``_CASCADE_SEAL_POLICY``, the
    walker's ``_PREFETCH_CHILD_POLICY`` / ``_LIST_RELATION_CHILD_POLICY``) must be
    able to state the same
    contract on either colored path, and an option only one twin can reach IS
    the drift the shared boundary exists to prevent. ``SyncMisuseError`` stays
    reserved for sync boundaries: every defect here is a plain
    ``ConfigurationError``. ``model`` is the sync runner's captured-model seam,
    declared here for the same reason: a field whose async pipeline could not
    hand down its captured model would re-read the target attribute on exactly
    one of the two colorings.
    """
    queryset, required_alias = _prepared_visibility_source(
        type_cls,
        queryset,
        model=model,
        policy=policy,
    )
    hook = type_cls.get_queryset
    # ``_is_default_get_queryset`` is stamped at class creation
    # (``DjangoType.has_custom_get_queryset`` reads it): the identity default does no I/O.
    identity = introspection.mro_attr(type_cls, "_is_default_get_queryset", default=False)
    result: object = (
        hook(queryset, info)
        if identity is True or is_async_callable(hook)
        else await run_in_one_sync_boundary(hook, queryset, info)
    )
    if is_awaitable(result):
        result = await result
        if _disposed_awaitable(result):
            raise ConfigurationError(
                f"{introspection.name(type_cls)}.get_queryset resolved to a nested awaitable; an "
                f"async get_queryset must resolve to a QuerySet (or Manager) after ONE "
                f"await, and an unbounded awaitable chain is never consumed.",
            )
    # No identity fast path -- same contract as the sync runner: object identity
    # is not immutability, so a hook can mutate the sealed source's
    # state (evaluate it, re-route it) and return it. The result is ALWAYS re-sealed
    # so the second seal's clone drops any fetched rows (spec-045 Decision 3).
    return _normalized_visibility_result(
        type_cls,
        result,
        required_alias,
        render_error,
        model=model,
        policy=policy,
    )


def reject_awaitable_sync_source(source: object, type_cls: type[DjangoType]) -> None:
    """Reject an awaitable source from a sync list or connection resolver.

    A plain ``def`` that returns an awaitable is committed to the sync field
    path. Passing that value onward would either skip queryset visibility or
    leak a Strawberry pagination error, so both field factories share this
    boundary.
    """
    if not _disposed_awaitable(source):
        return
    raise SyncMisuseError(
        f"A sync {introspection.name(type_cls)} consumer resolver returned an awaitable. "
        "Declare the resolver `async def` (or use an async callable) so the "
        "field awaits it and applies the get_queryset visibility hook; a plain "
        "`def` resolver that returns an awaitable is committed to the sync path "
        "and passing it through would silently skip get_queryset.",
    )


def reject_residual_async_source(source: object, type_cls: type[DjangoType]) -> None:
    """Reject a residual awaitable from an already-awaited async consumer resolver.

    Both async consumer pipelines await the consumer ``resolver=`` return
    exactly once before the value reaches source normalization: the list
    field's ``list_field.py::DjangoListField._async_wrap`` and the connection field's
    ``connection.py::_pipeline_async``. A value that is STILL awaitable after
    that await is an ``async def`` resolver that resolved to another awaitable;
    it is neither a ``QuerySet`` nor a legitimate plain iterable, so the
    non-queryset branch would pass it through and silently SKIP the
    ``get_queryset`` visibility hook - a data-leak escape. The awaitable is
    disposed (never recursively awaited over an unbounded chain, matching the
    async runner's nested-awaitable handling) and the resolution fails closed.

    Single-sited here, beside ``reject_awaitable_sync_source`` (the sync twin),
    so the list and connection async pipelines cannot drift on the one boundary
    where a miss skips visibility - a connection pipeline without this guard
    would let a nested async connection resolver bypass the hook.
    """
    if not _disposed_awaitable(source):
        return
    raise ConfigurationError(
        f"An async {introspection.name(type_cls)} consumer resolver resolved to another "
        f"awaitable after being awaited; a nested awaitable is neither a QuerySet "
        f"nor a plain iterable, and passing it through would silently skip the "
        f"get_queryset visibility hook. Return the queryset (or iterable) directly.",
    )


def prepared_resolver_source(
    result: object,
    type_cls: type[DjangoType],
    *,
    async_guard: Callable[[object, type[DjangoType]], None],
    non_queryset_guard: Callable[[object], None] | None = None,
    queryset_guard: Callable[[models.QuerySet[models.Model, object]], None] | None = None,
) -> NormalizedSource:
    """Refuse the wrong async shape, coerce a Manager, and report what the source IS.

    The head every consumer-resolver pipeline runs, in the one order that is
    safe: refuse the wrong async shape FIRST, then normalize, then let the
    surface apply its own guard to whichever branch the value landed in. Both
    list-field runners and both connection pipelines run it, and the miss it
    guards against is not cosmetic - a value that slips past the async refusal
    reaches the NON-QUERYSET branch and is passed through, skipping the
    ``get_queryset`` visibility hook entirely (see ``reject_residual_async_source``),
    which is why the order is fixed here rather than at four call sites.

    ``async_guard`` is the caller's colored refusal (``reject_awaitable_sync_source``
    on a sync path, ``reject_residual_async_source`` on an already-awaited async
    one) - passed in rather than selected by a flag, so each pipeline still names
    the mistake it is refusing. ``queryset_guard`` / ``non_queryset_guard`` are
    the surface's own per-branch checks (the connection's pre-sliced and
    sidecar-on-a-plain-iterable rejections); the list field has neither.

    Returns ``(source, is_queryset)`` rather than deciding the tail, so every
    caller keeps its colored visibility step explicit and no ``await`` hides
    behind a maybe-await abstraction.
    """
    async_guard(result, type_cls)
    normalized = normalize_query_source(result)
    if normalized[1] is False:
        if non_queryset_guard is not None:
            non_queryset_guard(normalized[0])
        return normalized[0], False
    if queryset_guard is not None:
        queryset_guard(normalized[0])
    return normalized[0], True
