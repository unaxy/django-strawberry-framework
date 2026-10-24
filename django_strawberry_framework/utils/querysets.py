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

The boundary implements a SEALED-EXECUTION-QUERYSET contract
(``_seal_or_defect``), not a validated inventory of method overrides on the
consumer ``QuerySet`` *class* that then returns the consumer object. The zero-SQL
probes recorded by
``docs/SPECS/spec-045-visibility_boundary-0_0_14.md #"## Architectural decisions"``
show why: an instance-shadowed ``.all()``, a replaced instance-level
``Query.chain``, and subclass ``.filter()`` / ``_values`` / ``.first()`` /
``.__aiter__()`` overrides each erase the visibility predicate or return
synthetic rows AFTER a class-level inventory accepts the object. A finite
inventory is the wrong abstraction. Instead the boundary treats the consumer
queryset as untrusted query STATE: it reads that state without dispatching any
consumer code (every read comes from the real instance ``__dict__`` via
``truth.instance_dict``, so a custom ``__getattribute__``, a class-level
``__dict__`` override or an instance-shadowed attribute cannot lie or run code),
validates it, then rebuilds a fresh queryset from the validated state. It NEVER
returns the consumer object. Every rebuild the framework composes onto is a plain
``django.db.models.QuerySet``. Two rebuilds keep the source's own ``QuerySet``
class, so a hook can call the project methods of the class that supplied it (the
framework seeds each read from the model's default manager): the hook's input, and
the cascade's narrowed output, which ``_restated_as_source_class`` restates after
the plain seal and walk; the hook's result is sealed plain again.

What the seal preserves: the SQL query state (filters, annotations, joins,
ordering, values projection), database routing / hints, the prefetch metadata
Django needs -- everything that determines which rows the SQL selects -- and, on
Django 6.1 and later, the fetch mode (``QuerySet.fetch_mode``) its rows load their
deferred fields and relations under.
A combinator is preserved as the set of primary keys it selects, rebuilt as a
``pk__in`` membership test the recomposing surfaces can narrow (the raw-list row
source keeps it as it is), and a combinator whose rows that rewrite would change
fails closed (``combined``). What it deliberately drops on every rebuild the
framework composes onto and on the hook result it returns: the consumer's
executable override dispatch (the subclass identity itself), because that is
precisely the leak vector. A seal rebuilds only state made of Django's own objects,
so anything else in it -- a consumer-defined query, expression, lookup or join
class, a method assigned onto a query instance, a foreign row iterable, a fetch
mode that is not one of Django's own, deferred-filter state Django never writes --
fails closed (``untrusted``).

Caller-specific tails stay with their caller: the connection field keeps its
GraphQL non-queryset error (it calls ``normalize_query_source`` then guards),
the Relay node defaults keep their id filter, the optimizer keeps plan
building, and the filter related derive keeps its per-branch recursion. This
module owns only the source normalization + the colored visibility calls.

Cycle-safe by construction: it depends on ``django``, ``asgiref``,
``strawberry``'s context probe, ``..exceptions``, and the write-transaction
ContextVar helpers, so
``types/relay.py`` (imported at module top by ``types/base.py``) can import
from here without closing a load cycle, and it never imports back into
filters / orders / mutations / permissions.
"""

from __future__ import annotations

import asyncio
import dataclasses
import datetime
import enum
import inspect
import sys
import uuid
import zoneinfo
from collections.abc import AsyncIterable, Iterable
from collections.abc import Set as AbstractSet
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Generic, ParamSpec, TypeGuard, TypeVar, cast, overload

from asgiref.sync import sync_to_async
from django.core.exceptions import FieldDoesNotExist, FieldError, ValidationError
from django.core.validators import ProhibitNullCharactersValidator
from django.db import models, router
from django.db.models import Prefetch, sql
from django.db.models import query as django_query
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import (
    BaseExpression,
    Combinable,
    Exists,
    Expression,
    F,
    OrderBy,
    RawSQL,
)
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.db.models.lookups import Lookup
from django.db.models.manager import BaseManager
from django.db.models.query import (
    FlatValuesListIterable,
    ModelIterable,
    NamedValuesListIterable,
    ValuesIterable,
    ValuesListIterable,
)
from django.db.models.sql.where import ExtraWhere, WhereNode

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry

from . import truth
from ._narrowing import (
    is_awaitable,
    is_exact_dict,
    is_exact_list,
    is_exact_list_or_tuple,
    is_exact_pair,
    is_exact_set_or_frozenset,
    is_exact_tuple,
    is_str,
    pk_of,
)
from ._queryset_private import (
    is_django_fetch_mode,
    queryset_db,
    queryset_fetch_mode,
    queryset_fields,
    queryset_prefetch_lookups,
    set_queryset_fetch_mode,
    set_queryset_fields,
    set_queryset_for_write,
    set_queryset_prefetch_lookups,
    set_queryset_sticky_filter,
)
from .relations import leading_relation_hops, order_column_paths, stored_value_column
from .typing import MISSING_ATTRIBUTE, is_async_callable
from .write_transaction import (
    current_write_pipeline,
    pin_write_queryset,
    pipeline_rows_visible_after_lock,
    pipeline_scoped_queryset,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
    from typing import Literal, Protocol, TypeAlias

    from django.db.models.options import Options
    from django.db.models.query import BaseIterable
    from typing_extensions import TypeIs

    from django_strawberry_framework.filters.sets import FilterSet
    from django_strawberry_framework.orders.sets import OrderSet
    from django_strawberry_framework.types.base import DjangoType

    from .typing import ModelField

    #: A ``Prefetch`` as the seal rebuilds it: a string lookup over a model-row child.
    _SealedPrefetch: TypeAlias = Prefetch[str, models.QuerySet[models.Model], str]
    #: A ``Prefetch``'s ``(prefetch_through, prefetch_to, to_attr)`` read as exact text.
    _PrefetchPath: TypeAlias = tuple[str, str, str | None]
    #: A resolver source after ``Manager`` coercion: a ``QuerySet`` flagged ``True``, or
    #: any other value (a list, a generator) flagged ``False``. The flag discriminates
    #: the union, so ``source[1] is True`` narrows ``source[0]`` to the queryset.
    NormalizedSource: TypeAlias = (
        tuple[models.QuerySet[models.Model, object], Literal[True]] | tuple[object, Literal[False]]
    )
    #: The exact builtin containers the graph walkers descend into member-wise
    #: (``_PLAIN_CONTAINER_TYPES``), with members of unknown type.
    _PlainContainer: TypeAlias = (
        list[object] | tuple[object, ...] | set[object] | frozenset[object] | dict[object, object]
    )

    class _TableRef(Protocol):
        """An ``alias_map`` entry as ``_base_table_defect`` reads it: its ``table_name``."""

        @property
        def table_name(self) -> object: ...

    class _SourceExpressionNode(Protocol):
        """A genuine Django node exposing the operand accessor the expression walk calls."""

        def get_source_expressions(self) -> Iterable[object]: ...

    class _JoinColumn(Protocol):
        """One side of a join's column pair, as ``Join.join_cols`` reads it."""

        @property
        def column(self) -> object: ...

    class _JoiningRelation(Protocol):
        """A path step's ``join_field``: the relation (or reverse relation) a join follows."""

        def get_joining_fields(self) -> tuple[tuple[_JoinColumn, _JoinColumn], ...]: ...

    class _PathStep(Protocol):
        """One ``PathInfo`` step of ``Query.names_to_path``, as the ordering expansion reads it."""

        @property
        def to_opts(self) -> Options[models.Model]: ...

        @property
        def join_field(self) -> _JoiningRelation: ...

    def is_manager(_value: object, /) -> TypeIs[BaseManager[models.Model]]:
        """Return whether the value is a model manager (a related manager included).

        ``BaseManager`` rather than ``Manager``: Django builds a related manager by
        subclassing the target's default manager class, which a
        ``BaseManager.from_queryset(...)`` declaration leaves outside ``Manager``.
        """
        ...

    class _PythonCoercing(Protocol):
        """A model field as far as coercing a value to its Python type goes."""

        def to_python(self, value: object, /) -> object:
            """Return ``value`` coerced to the field's Python type."""
            ...

else:
    is_manager = BaseManager.__instancecheck__


# Django < 6.0 has no module-level constant; ``QuerySet._filter_or_exclude``
# rejects the same ``models.Q.__init__`` internals inline. The fallback mirrors Django
# 6.0's ``django.db.models.query.PROHIBITED_FILTER_KWARGS`` verbatim so the
# deferred-filter defect gate behaves identically at the declared
# ``Django>=5.2.16`` floor (pyproject ``[project.dependencies]``).
PROHIBITED_FILTER_KWARGS: frozenset[str] = getattr(
    django_query,
    "PROHIBITED_FILTER_KWARGS",
    frozenset({"_connector", "_negated"}),
)

_T = TypeVar("_T")
_R = TypeVar("_R")
_P = ParamSpec("_P")
_ModelT = TypeVar("_ModelT", bound=models.Model)
_RowT = TypeVar("_RowT")
_RowT_co = TypeVar("_RowT_co", covariant=True)
_QuerySetT = TypeVar("_QuerySetT", bound=models.QuerySet[models.Model, object])


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
    ``django_strawberry_framework.types.relay`` for back-compat) so it
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
    protocol. Native-coroutine error text is preserved for compatibility.
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

    The MODEL-keyed seed. ``initial_queryset`` is its TYPE-keyed wrapper, and
    the two are genuinely different questions: a surface that seeds from the
    registered type's model asks the first, while a surface that seeds from a
    relation's own target model (the optimizer walker's prefetch child, the
    cascade's per-edge base, a ``RelatedFilter``'s child) asks the second and
    must NOT route through the registered type - the relation's model is the
    authority there.

    ``using`` pins the seed to a database alias: a sharded parent must seed
    its children on the SAME connection, and the conditional-on-``None`` shape
    was being written out at each such site.

    An abstract model has no default manager, so it raises ``ConfigurationError``
    naming the model: a ``DjangoType`` over an abstract model serves rows only
    from a consumer resolver that returns concrete instances.
    """
    if model._meta.abstract:
        raise ConfigurationError(
            f"{truth.name(model)} is an abstract model and has no default manager to seed a "
            f"queryset from. Point Meta.model at a concrete model, or resolve the field with "
            f"a custom resolver that returns concrete rows.",
        )
    manager = model._default_manager
    return manager.using(using).all() if using is not None else manager.all()


def default_order(query: sql.Query, model: type[models.Model]) -> tuple[str | Combinable, ...]:
    """Return the ``Meta.ordering`` terms Django compiles for ``query`` when nothing explicit is set.

    ``django/db/models/sql/compiler.py::SQLCompiler._order_by_pairs`` reaches the
    model's ordering only while ``query.default_ordering`` stands (a bare
    ``.order_by()`` clears it) and reads the option by truthiness, so
    ``Meta.ordering = None`` - the idiom for clearing an abstract parent's
    ordering - is no default order, never an iterable. ``model`` is the caller's
    model rather than ``query.get_meta()``, so a connection's plan-time and
    resolve-time orders derive from one model read.
    """
    if not query.default_ordering:
        return ()
    return tuple(model._meta.ordering or ())


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
    ``Meta.ordering`` (``default_order``) is reached only when nothing explicit
    was set. They are alternatives, never a union, so a term left in a
    collection Django did not pick is dormant and reaches no SQL. ``source`` is
    one of the ``ORDER_FROM_*`` names.

    Read under the forward flag: a ``.reverse()``'d query (``standard_ordering``
    False) compiles each of these terms flipped.
    """
    if query.extra_order_by:
        return ORDER_FROM_EXTRA, tuple(query.extra_order_by)
    if query.order_by:
        return ORDER_FROM_EXPLICIT, tuple(query.order_by)
    ordering = default_order(query, model)
    if ordering:
        return ORDER_FROM_MODEL_DEFAULT, ordering
    return ORDER_FROM_NOTHING, ()


def applied_order(query: sql.Query, model: type[models.Model]) -> tuple[str | Combinable, ...]:
    """Return the ORDER BY terms Django compiles for ``query`` (``selected_order``'s terms).

    The connection order ladder reads this only after
    ``optimizer/plans.py::normalize_order_direction`` has rewritten an
    ``extra(order_by=...)`` ordering and a ``.reverse()`` into explicit
    ``order_by`` terms under the forward flag, so the terms it reads here are
    the ones Django compiles and the ones a later ``order_by(...)`` keeps.
    """
    return selected_order(query, model)[1]


class _UnexpandableOrderError(Exception):
    """An order name the compiler reads as written: it rejects the expansion, or cannot run it."""


def _names_to_path(
    query: sql.Query,
    names: Sequence[str],
    opts: Options[models.Model],
) -> tuple[list[_PathStep], ModelField, tuple[object, ...], Sequence[str]]:
    """Return ``query.names_to_path(names, opts, allow_many=True, fail_on_missing=False)``.

    django-stubs types the path steps and the final field ``Any``; Django returns the
    ``PathInfo`` steps, the field the last resolved name names, its targets, and the
    names left over.
    """
    return query.names_to_path(names, opts, allow_many=True, fail_on_missing=False)


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
    related_opts: Options[models.Model] | None
    substitute: Sequence[str | Combinable] | None


def resolve_order_name(
    query: sql.Query,
    name: str,
    opts: Options[models.Model],
) -> ResolvedOrderName:
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
    opts: Options[models.Model],
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


def to_python_value(field: _PythonCoercing, value: object) -> object:
    """Return ``field.to_python(value)``; django-stubs types the coerced value ``Any``."""
    return field.to_python(value)


#: Django's all-backend NUL rule; a text id holding a NUL names no row.
_PROHIBIT_NULL_CHARACTERS = ProhibitNullCharactersValidator()


def coerce_field_value_or_none(field: ModelField | None, value: object) -> object:
    """Coerce ``value`` through ``field``'s ``to_python`` + ``run_validators``; ``None`` if invalid.

    The single "raw literal -> Django field value, or nothing" safety wrapper
    every raw-identity decode runs through. ``to_python`` is a pure type
    cast that does NOT range-check, so a syntactically-valid but out-of-range
    literal (e.g. a pk past a backend's signed-64-bit column range) would
    otherwise reach a ``pk__in`` / ``filter`` call and raise a raw backend
    ``OverflowError`` (``Python int too large to convert to SQLite INTEGER``);
    the field's own validators (``integer_field_range`` Min/MaxValueValidators,
    etc.) reject it here as a ``ValidationError`` instead, and a non-numeric
    literal fails ``to_python`` itself. Most Django core fields wrap their
    ``to_python`` failure in ``ValidationError``; ``TypeError`` / ``ValueError``
    cover a field whose ``to_python`` raises one of those directly, and
    ``OverflowError`` is what ``DurationField.to_python`` raises for a
    well-formed duration string past ``timedelta``'s range (``int(inf)`` in
    ``IntegerField.to_python`` raises it too).

    Every caller treats ``None`` the same way - "identifies no row": dropped
    from a query, or mapped to a not-found / invalid sentinel - never a raw
    crash. WHICH field to coerce against is a genuine per-caller decision (a
    Relay type's resolved id field, a related model's pk, an arbitrary filtered
    column) and stays at each call site; only the coercion mechanics are
    single-sourced here. A ``ForeignObjectRel`` or ``None`` field has no column
    to coerce against, so it identifies no row either. A key (a one-to-one primary
    key, a multi-table-inheritance parent link, any ``ForeignKey``) carries only
    the validators declared on it, while its ``to_python`` delegates down the chain
    to the column storing its value (``relations.py::stored_value_column``): the
    value runs the key's own validators and then that column's, whose range
    validators reject an out-of-range id.

    A value coerced to text holding an embedded NUL (U+0000) identifies no row
    either, on every backend: no write stores one (Django's all-backend
    ``ProhibitNullCharactersValidator`` rule, which
    ``write_values.py::unstorable_text_error`` holds every write to), and
    PostgreSQL refuses to bind one at all (psycopg raises ``DataError``), so a NUL
    in a text-keyed id (a decoded ``GlobalID`` node id, a raw pk, a relation
    identity) answers the caller's not-found / invalid-id verdict before any query
    rather than a raw backend error.
    """
    if not isinstance(field, models.Field):
        return None
    column = stored_value_column(field)
    try:
        coerced = to_python_value(field, value)
        field.run_validators(coerced)
        if column is not field:
            column.run_validators(coerced)
        if isinstance(coerced, str):
            _PROHIBIT_NULL_CHARACTERS(str.__str__(coerced))
    except (
        ValidationError,
        TypeError,
        ValueError,
        OverflowError,
    ):
        return None
    return coerced


_RELAY_ASYNC_RECOURSE = (
    "The Relay node defaults only await async get_queryset hooks on the async "
    "branch; either invoke the Relay node default from an async resolver, or "
    "redefine get_queryset as a sync method."
)


def sync_pipeline_recourse(flavor_noun: str) -> str:
    """Build the ``SyncMisuseError`` recourse a sync write pipeline appends (spec-039).

    Every write flavor raises a ``SyncMisuseError`` naming the SAME recourse when an
    ``async def get_queryset`` is met inside its (synchronous) ORM pipeline -
    byte-identical except the flavor subject - so the sentence lives here and each
    flavor's own ``*_ASYNC_RECOURSE`` constant is computed from it. NOT used for the
    Relay recourse (``_RELAY_ASYNC_RECOURSE`` - async IS possible there) or the
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
    """Async-only completion adapter for a final sliced QuerySet under async execution.

    Exposes ONLY ``__aiter__`` (delegating to ``self._queryset.__aiter__()``)
    and deliberately omits ``__iter__`` so graphql-core cannot select synchronous
    ORM iteration in an event-loop thread.
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

    The generic one-boundary primitive (spec-040 D17): every async surface
    that must keep a consumer-overridable sync hook off the event loop shares
    this call, so the boundary discipline (``thread_sensitive=True``, never
    per-step hops inside one unit of work) cannot drift. The unit differs by
    surface. An auth or mutation resolution enters it exactly once, with its
    permission gate and write pipeline inside (spec-040 D17 pins that count for
    auth). A sidecar ``apply_async`` enters it once for its permission pass. A
    read path enters it once per custom synchronous ``get_queryset`` call
    (``apply_type_visibility_async``; a cascade walk inside that hook rides the
    same worker) and once per optimizer plan build
    (``DjangoOptimizerExtension._optimize_async``,
    ``apply_connection_optimization_async``), so one read resolution may enter it
    more than once.
    A ``sync_to_async`` worker is itself a sync context, so the standing
    ``SyncMisuseError`` guards still fire inside ``fn``.

    Neutral home: lives here with the sibling ``reject_async_in_sync_context``
    primitive (cycle-safe utils substrate) rather than under ``mutations/``, so
    read-side modules reuse it without a root-into-subpackage import.
    """
    return await sync_to_async(fn, thread_sensitive=True)(*args, **kwargs)


def _concrete_or_none(candidate: object) -> type[models.Model] | None:
    """Return ``candidate._meta.concrete_model`` if ``candidate`` is a model, else ``None``.

    A hostile or malformed ``QuerySet.model`` / ``Query.model`` may be a
    non-model object (or missing entirely). Reading ``._meta.concrete_model``
    directly would leak a raw ``AttributeError`` past the boundary's typed
    error contract; this returns ``None`` for anything that is not a Django
    model so the caller can fail it closed as a table defect instead.

    Being a Django MODEL CLASS is the requirement, not merely exposing a
    ``_meta.concrete_model``: the value that survives this check is installed as
    the sealed queryset's ``.model``, and every downstream reader treats
    ``queryset.model`` as a model class (``_meta`` descriptors, ``_default_manager``,
    ``__name__``). Duck-typing let a non-class object -- or a non-model class --
    carrying a convincing ``_meta`` pass the public ``QuerySet.model`` comparison and
    escape the typed boundary as malformed state. So the class-ness and the model
    ancestry are proven BEFORE any metadata is read, which also means a consumer
    ``_meta`` property / ``concrete_model`` descriptor on such an object never runs.
    Both are read from the real MRO (``truth.is_subclass`` / ``truth.static_attr``).
    """
    if not truth.is_subclass(candidate, models.Model):
        return None
    meta: object = truth.static_attr(candidate, "_meta", None)
    if meta is None:
        return None
    # ``ModelBase.__new__`` sets ``_meta.concrete_model`` on every model class to a
    # model class (the class itself, or its concrete ancestor for a proxy).
    concrete: type[models.Model] | None = getattr(meta, "concrete_model", None)
    return concrete


def _is_model_of_concrete(
    candidate: object,
    concrete: type[models.Model],
) -> TypeGuard[type[models.Model]]:
    """Return whether ``candidate`` is a model class whose concrete model is ``concrete``.

    ``_concrete_or_none(candidate) is concrete``, stated as a guard: ``_concrete_or_none``
    answers a model only for a ``models.Model`` subclass, so a match proves the class.
    """
    return _concrete_or_none(candidate) is concrete


def _base_table_defect(query: object, concrete: type[models.Model]) -> str | None:
    """Return the query's baked base table if it is not ``concrete``'s table.

    ``concrete`` is the registered type's ``_meta.concrete_model``, resolved once
    by the caller and threaded through (so a single seal walks the descriptor at
    most once rather than re-resolving it here).

    ``QuerySet.model`` and ``Query.model`` are mutable and are only what Django
    WILL consult to build the SQL alias map. Once that alias map is initialized
    the base table is frozen inside it, and reassigning the model attributes
    afterwards cannot change which table the SQL reads - so a hostile queryset
    can bake its alias map against one table, then spoof both model attributes
    to the registered type's model and pass a metadata-only check while still
    reading another table's rows. Read the authoritative base table straight
    from the initialized alias map (``Query.base_table`` ->
    ``alias_map[...].table_name``) and compare it to the concrete model's
    ``db_table``. An unbaked query (empty alias map) has no frozen table yet -
    ``Query.model`` still governs compilation and is validated separately by
    ``_combined_query_table_defect`` - so it returns ``None`` here.

    The base alias is recomputed from the FIRST key of ``alias_map`` rather than read
    from ``Query.base_table``: ``base_table`` is a ``@cached_property`` that can be
    poisoned in ``Query.__dict__`` to name a DIFFERENT alias than the one Django will
    use, and ``Query.clone`` deliberately DELETES that cache so the clone recomputes the
    first alias -- validation reading the poisoned cache would inspect one table while
    the cloned query compiles against another (spec-045 Decision 2).
    Iterating ``alias_map`` reproduces exactly what the cache-free clone does. The
    caller runs ``_query_ast_defect`` (which proves every ``alias_map`` join genuine and
    unshadowed) BEFORE this, so the ``.table_name`` read below dispatches no consumer
    code.
    """
    # ``_query_container_defect`` proved ``alias_map`` an exact ``dict`` with ``str`` keys
    # (or absent) before this runs.
    alias_map: dict[str, _TableRef] | None = getattr(query, "alias_map", None)
    if not alias_map:
        return None
    # The base table is the first alias (a ``BaseTable`` carrying ``table_name``) -- the
    # exact value ``Query.base_table`` recomputes after ``clone`` drops its cache.
    first_alias = next(iter(alias_map))
    table = alias_map[first_alias].table_name
    if not is_str(table):
        return truth.kind(table)
    # Django stores ``Meta.db_table`` as given, so a ``TextChoices`` / ``StrEnum`` member
    # names the table it spells; both sides compare as their exact text, and canonical
    # reconstruction rebinds the baked name as that text.
    table = _normalized_str(table)
    if table != _normalized_str(concrete._meta.db_table):
        return table
    return None


class VisibleRowExists(Exists):
    """The framework's visibility test over related rows: Django's ``Exists``, under its own name.

    ``optimizer/predicates.py::visible_row_exists`` builds it to read an order value
    only from related rows a target type's ``get_queryset`` lets the request see. It
    defines nothing of its own, so every method the seal and the compiler dispatch on
    it is Django's ``Exists`` code; it exists as a distinct exact type so the code
    reading an ordering (the ``DjangoListField`` offset guard, the keyset order state)
    can recognize the framework's test and nothing else. ``_type_is_genuinely_django``
    admits it by identity beside Django's own classes.
    """


def _type_is_genuinely_django(node_type: type[object]) -> bool:
    """Return whether ``node_type`` is a genuine Django class by IDENTITY, not ``__module__``.

    Every clonable / compilable node embedded in a sealed ``sql.Query`` -- ``where``
    leaves and their operands, annotation / order-by / join expressions, subquery
    nodes -- must be a trusted Django implementation, because ``sql.Query.clone`` and
    the compiler dispatch that node's own ``clone`` / ``as_sql`` /
    ``resolve_expression`` while the seal is still deciding whether the graph is
    trusted (spec-045 Decision 2). A ``type(node).__module__.startswith("django.")``
    check would not do: ``__module__`` is a plain writable string, so a consumer
    class declaring ``__module__ = "django.evil"`` spoofs it. Provenance is
    therefore proven by OBJECT IDENTITY: the type must be the exact
    object Django itself exposes at ``sys.modules[module].<qualname>``. A consumer subclass,
    or a spoofed ``__module__`` / ``__qualname__`` pointing at a genuine name, cannot make
    ``getattr(genuine_django_module, name)`` return the consumer type, so it fails closed. A
    dotted (nested) qualname, or a module absent from ``sys.modules``, also fails closed.
    Exact genuine Django types only -- consumer-defined expressions / lookups are NOT
    supported across the visibility boundary. The one framework type admitted beside
    them is ``VisibleRowExists``, matched by identity: it overrides nothing, so its
    ``clone`` / ``as_sql`` / ``resolve_expression`` are Django's ``Exists`` code.

    ``__module__`` and ``__qualname__`` are read truthfully (``truth.module`` /
    ``truth.qualname``) so a consumer METACLASS that overrides ``__getattribute__`` /
    ``__getattr__`` or defines a ``__module__`` property cannot run code (or return a
    lie) during the very read that is meant to reject the type (spec-045 Decision 2).
    """
    if node_type is VisibleRowExists:
        return True
    module_name = truth.module(node_type)
    qualname = truth.qualname(node_type)
    if not module_name.startswith("django."):
        return False
    if "." in qualname:
        return False
    module = sys.modules.get(module_name)
    if module is None:
        return False
    return getattr(module, qualname, None) is node_type


# Inert query-parameter leaf types: a bound value the compiler renders as ``%s`` with
# the value as a parameter, never dispatching an ``as_sql`` / ``resolve_expression``
# the seal would have to trust. These terminate the genuineness walk. A model
# instance is not inert. It is admitted as a direct lookup value and as a raw-SQL
# parameter by plain-data ancestry (``_DIRECT_RHS_DATA_BASES``), and as a deferred-filter
# value when it carries no ``resolve_expression`` (``_deferred_value_defect``);
# reconstruction retains it by reference as trusted schema (``_normalized_bound_value``).
# Membership is tested by EXACT type, never ``isinstance``: a ``str`` / ``int`` /
# ``datetime`` SUBCLASS can define ``resolve_expression`` (or an ``as_sql``) and would
# then be dispatched by ``add_q`` / the compiler, so a subclass is NOT inert and must
# prove genuine-Django provenance like any other object (spec-045 Decision 2).
# ``datetime.datetime`` is listed explicitly because exact-type
# membership does not inherit it from ``datetime.date``.
_INERT_VALUE_TYPES: truth.IdentitySet[type[object]] = truth.IdentitySet(
    (
        str,
        bytes,
        bytearray,
        bool,
        int,
        float,
        complex,
        Decimal,
        datetime.datetime,
        datetime.date,
        datetime.time,
        datetime.timedelta,
        uuid.UUID,
    ),
)


def _is_inert_value(value: object) -> bool:
    """Return whether ``value`` is an inert (non-dispatchable) query-parameter leaf.

    ``None`` is inert. Membership is by EXACT type, so a ``str`` / ``int`` /
    ``datetime`` SUBCLASS carrying a ``resolve_expression`` / ``as_sql`` is NOT treated
    as inert (spec-045 Decision 2) -- it falls through to the
    genuine-Django provenance walk and fails closed. Anything else is a container
    (walked member-wise) or an object that must prove provenance before the seal lets
    the compiler dispatch it.
    """
    return value is None or truth.is_exact_one_of(value, _INERT_VALUE_TYPES)


def _shadow_defect(node: object, label: str) -> tuple[str, str] | None:
    """Return a defect if ``node``'s instance ``__dict__`` shadows a callable method.

    Python methods are non-data descriptors, so an instance-``__dict__`` entry named
    after a class method wins over the genuine method even when ``type(node)`` is
    exactly the expected class (spec-045 Decision 2). ``sql.Query.clone`` and
    the compiler dispatch bound methods -- ``where.clone()``, an expression's
    ``as_sql`` -- so ANY ``__dict__`` key naming a callable attribute of the node's
    (already-proven-genuine) type fails closed. A non-string ``__dict__`` key is
    itself anomalous (Django never produces one) and would otherwise raise
    ``TypeError`` out of ``getattr`` past the typed contract, so it fails closed
    first. Read straight from ``__dict__`` so a shadow cannot hide itself; only ever
    called after the node's type is proven genuine (or exactly ``WhereNode`` /
    ``sql.Query``), so the ``getattr`` against that type dispatches no consumer code.

    Two wordings distinguish the canonical emitter from the dynamically-resolved
    per-vendor ones. ``as_sql`` is the fixed base compile method every ``Expression``
    defines, and any other callable class attribute a shadow overrides (``clone`` /
    ``resolve_expression`` / ...) is likewise a concrete method, so both read "shadows
    the ``<name>`` method". An instance key beginning ``as_`` OTHER than ``as_sql``
    reads "shadows the ``<name>`` compiler method": the compiler resolves the
    per-backend emitter DYNAMICALLY as ``getattr(node, "as_" + connection.vendor,
    node.as_sql)`` (``as_sqlite`` / ``as_postgresql`` / ...), so a shadow named for a
    vendor -- even one a mixin defines on this class (``SQLiteNumericMixin.as_sqlite``)
    -- gets dispatched at compile time through that dynamic lookup rather than the
    fixed ``as_sql`` slot (spec-045 Decision 2). The vendor-prefix
    check therefore runs BEFORE the callable-class-attribute check so a mixin-provided
    ``as_<vendor>`` still takes the "compiler method" wording. Genuine Django nodes
    never carry an ``as_*`` INSTANCE attribute (their emitters are class methods), so
    rejecting the prefix costs no legitimate query.

    A node with no instance ``__dict__`` at all fails closed rather than raising. Genuine
    Django provenance is proven by object identity against ``sys.modules``, and Django
    modules re-export SLOTTED classes at module level (``django.utils.safestring``
    ``SafeString``, the ``namedtuple`` helpers in ``django.db.models.query_utils`` /
    ``django.db.backends.*.introspection``, ``django.db.models.expressions.UUID``), so a
    provenance-genuine type whose instances carry no ``__dict__`` does reach here, and
    ``truth.instance_dict`` answers ``None`` for it, which becomes the boundary's typed
    ``(code, detail)`` defect. No such object is a clonable / compilable Django node --
    every ``Expression`` / ``WhereNode`` / ``Join`` / ``sql.Query`` carries an instance
    ``__dict__`` -- so its presence in a compiler-reachable slot is untrusted state.
    """
    node_dict = truth.instance_dict(node)
    if node_dict is None:
        return ("untrusted", f"{label} is a {truth.kind(node)} with no instance state")
    node_type = type(node)
    for key in node_dict:
        if type(key) is not str:
            return ("untrusted", f"{label} has a non-string __dict__ key")
        if key.startswith("as_") and key != "as_sql":
            return ("untrusted", f"{label} shadows the {key!r} compiler method")
        if key == "as_sql" or callable(getattr(node_type, key, None)):
            return ("untrusted", f"{label} shadows the {key!r} method")
    return None


# SQL-template metadata a genuine Django expression interpolates DIRECTLY into the
# emitted SQL string during ``as_sql`` -- never routed through ``get_source_expressions``
# and never bound as a ``%s`` parameter. ``Func`` joins its argument SQL with
# ``self.arg_joiner.join(...)`` and formats ``self.template % {"function": self.function,
# ...}``; ``CombinedExpression`` interpolates ``self.connector``; ``RawSQL`` emits
# ``self.sql`` verbatim. An EXACT genuine node whose instance ``__dict__`` overrides one
# of these with a non-``str`` object would run that object's ``join`` / ``__str__`` at
# compile time (spec-045 Decision 2), so each override present on the instance must be
# a text term (``_is_text_term``): an exact ``str``, or a ``TextChoices`` / ``StrEnum``
# member Django formats as the text it spells and reconstruction rebinds as that exact
# text. Genuine Django only ever stores strings here.
_SQL_TEMPLATE_ATTRS: tuple[str, ...] = (
    "template",
    "function",
    "arg_joiner",
    "connector",
    "sql",
    "base_template",
)


# Open-ended SQL-template parameters a genuine Django expression merges into its format
# context. ``Func`` / ``Case`` / ``Subquery`` collect their surplus constructor keywords
# into ``self.extra`` and emit ``self.template % {**self.extra, **extra_context}``, so
# EVERY value in that mapping is interpolated into the SQL string and has its ``__str__``
# / ``__format__`` invoked at compile time -- including the ``function`` / ``template`` /
# ``arg_joiner`` names, which ``Func.__init__`` routes into ``extra`` rather than onto the
# named instance slots ``_SQL_TEMPLATE_ATTRS`` pins. ``extra`` exists only as INSTANCE
# state (no class supplies it), so validating it needs no class-level proof. Values are
# pinned to the exact inert scalars Django itself stores there, or a text term; a consumer
# object under any key fails closed before the seal returns.
_TEMPLATE_PARAM_VALUE_TYPES: truth.IdentitySet[type[object]] = truth.IdentitySet(
    (
        str,
        int,
        float,
        bool,
    ),
)


def _template_params_defect(node_dict: Mapping[str, object], label: str) -> tuple[str, str] | None:
    """Return a defect unless an expression's ``extra`` template mapping is inert text.

    Read straight from the already-validated instance ``__dict__`` so the check itself
    dispatches nothing: the mapping must be an EXACT ``dict`` (a subclass ``items`` /
    ``__iter__`` would run consumer code when ``as_sql`` unpacks it into the format
    context), its keys text terms (they are the template's format names), and each
    value an exact inert scalar or a text term. Here a ``str`` subclass that defines
    ``resolve_expression`` is an expression, not a text term, and fails closed as key or
    value; a lookup value's mapping key is bound data instead, which admits any ``str``.
    Genuine Django only ever stores strings and numbers here, so the rule costs no
    legitimate query.
    """
    if "extra" not in node_dict:
        return None
    extra = node_dict["extra"]
    if not is_exact_dict(extra):
        return ("untrusted", f"{label} extra is a {truth.kind(extra)}")
    for key, value in extra.items():
        if type(key) is not str and not _is_text_term(key):
            kind = "an expression" if is_str(key) else "a non-string"
            return ("untrusted", f"{label} extra has {kind} key")
        if (
            value is not None
            and not truth.is_exact_one_of(value, _TEMPLATE_PARAM_VALUE_TYPES)
            and not _is_text_term(value)
        ):
            return (
                "untrusted",
                f"{label} extra[{_normalized_str(key)!r}] is a {truth.kind(value)}",
            )
    return None


def _node_metadata_defect(node: object, label: str) -> tuple[str, str] | None:
    """Return a defect for compiler-reachable node metadata NOT covered by source expressions.

    ``get_source_expressions`` enumerates the operand sub-expressions the compiler
    recurses, but ``Func.as_sql`` (and its cousins) ALSO interpolate formatting metadata
    no source-expression walk reaches (spec-045 Decision 2): each ``_SQL_TEMPLATE_ATTRS``
    name present on the instance ``__dict__`` must be a text term (``_is_text_term``),
    because it is formatted straight into the SQL string (``template % data``) or used
    as a ``.join`` separator, so a non-text override would run that object's ``__str__``
    / ``join`` at compile time; a ``TextChoices`` / ``StrEnum`` member is the text it
    spells and reconstruction rebinds it as that exact text. The named slots are not the
    whole template surface: ``Func`` / ``Case`` / ``Subquery`` keep their surplus
    constructor keywords in an ``extra`` MAPPING that ``as_sql`` merges into the same
    format context, so ``Func(Value("x"), function=<object>)`` stores the object under
    ``extra["function"]`` rather than on the ``function`` slot. ``_template_params_defect``
    pins that mapping to text-term keys and exact inert scalar or text-term values,
    closing the same interpolation route.

    ``node`` is proven an EXACT genuine Django expression type before this runs, so these
    attributes are Django's own string defaults unless the instance ``__dict__`` shadows
    them; genuine Django never stores a non-string there, so the check costs no
    legitimate query. ``output_field`` is deliberately NOT constrained to a Django-owned
    type here: a ``Col``'s ``output_field`` is the queried model's OWN field, which may
    legitimately be a consumer-defined ``models.Field`` subclass (part of the trusted
    schema, not injected by the hook) -- its shadow / ``as_`` surface is already covered
    when the field itself is reached, and forcing it Django-owned would fail-close every
    query over a custom model field.
    """
    node_dict = truth.instance_state(node)
    for attr in _SQL_TEMPLATE_ATTRS:
        if attr in node_dict:
            text = node_dict[attr]
            if type(text) is not str and not _is_text_term(text):
                return ("untrusted", f"{label} {attr} is a {truth.kind(text)}")
    return _template_params_defect(node_dict, label)


def _raw_sql_params_defect(params: object, label: str) -> tuple[str, str] | None:
    """Return a defect unless raw-SQL parameters are an exact sequence of plain-data leaves.

    Django passes ``RawSQL.params``, ``ExtraWhere.params`` and an ``extra(select=...)``
    payload's params straight to the database adapter. A container subclass can dispatch
    while iterated, and an arbitrary parameter object can dispatch from backend
    adaptation. Raw-SQL state therefore admits only the exact builtin sequence shapes
    Django creates, each member an inert leaf or a plain-data leaf under the same rule a
    direct lookup value meets (``_plain_data_leaf_defect``): a ``TextChoices`` / ``StrEnum``
    member or a ``Decimal`` / date subclass binds here exactly as it does in a lookup,
    and canonical reconstruction rebinds it as its exact inert value
    (``_normalized_bound_value``). A container inside the params stays refused. The rule
    reads type ancestry only; whether the driver can bind an admitted leaf stays Django's
    and the driver's question, so a model instance, which reconstruction retains by
    reference, binds only where the project registered a driver adapter for it, as in
    plain Django.
    """
    if not is_exact_list_or_tuple(params):
        return ("untrusted", f"{label} params is a {truth.kind(params)}")
    for param in params:
        if not _is_inert_value(param) and _plain_data_leaf_defect(param, label) is not None:
            return ("untrusted", f"{label} params carries a {truth.kind(param)}")
    return None


def _raw_sql_node_defect(node: object, label: str) -> tuple[str, str] | None:
    """Validate compiler-dispatched raw-SQL payloads outside expression children.

    An ``ExtraWhere`` fragment is a text term (``_is_text_term``): an exact ``str``, or
    a ``str`` subclass such as a ``StrEnum`` member that defines no
    ``resolve_expression``, which reconstruction rebinds as its exact text. Its
    ``params`` may be ``None``, which is what ``QuerySet.extra(where=...)`` stores when
    no ``params=`` is given and ``ExtraWhere.as_sql`` reads as no parameters; a
    ``RawSQL`` with ``None`` params stays refused, since Django cannot compile it.
    """
    if type(node) is RawSQL:
        return _raw_sql_params_defect(node.params, label)
    if type(node) is ExtraWhere:
        sqls = node.sqls
        if not is_exact_list_or_tuple(sqls):
            return ("untrusted", f"{label} sqls is a {truth.kind(sqls)}")
        for statement in sqls:
            if not _is_text_term(statement):
                return ("untrusted", f"{label} sqls carries a {truth.kind(statement)}")
        if node.params is None:
            return None
        return _raw_sql_params_defect(node.params, label)
    return None


class _WalkState(enum.Enum):
    """Outcome of admitting one node id to a ``_GraphWalk``.

    ``VALIDATED`` -- the node was already proven trusted on an earlier visit, so the
    caller returns ``None`` without re-walking it. ``CYCLE`` -- the node is still on the
    active recursion stack, so the graph closes a cycle and the caller returns its own
    ``untrusted`` cycle detail. ``ENTERED`` -- the node is newly on the stack and the
    caller must walk it and then ``leave`` it.
    """

    VALIDATED = "validated"
    CYCLE = "cycle"
    ENTERED = "entered"


class _GraphWalk:
    """Three-state identity bookkeeping shared by the recursive graph proofs.

    The walkers must distinguish two revisits of the same object. A node reached
    again AFTER it finished validating is a legitimate shared diamond (Django
    reuses one ``Col`` / ``Value`` across slots) and is cheap to accept. A node
    reached again while it is still IN PROGRESS closes a cycle -- and Django never
    produces a cyclic query graph, so such a graph is untrusted state that
    ``sql.Query.clone`` / the compiler would later recurse until a raw
    ``RecursionError`` escaped past the typed defect contract. One combined
    "already visited" set cannot tell the two apart and silently reports the cycle as
    validated, so the two identity sets are kept separate: ``visiting`` holds the
    active recursion stack, ``validated`` holds the nodes fully proven trusted.

    A node stays in ``visiting`` when the walk aborts on a defect; the walk
    unwinds to the caller immediately, so the entry is never consulted again.
    """

    __slots__: tuple[str, ...] = ("validated", "visiting")

    def __init__(self) -> None:
        self.visiting: set[int] = set()
        self.validated: set[int] = set()

    def enter(self, node_id: int) -> None:
        """Mark ``node_id`` as being validated right now."""
        self.visiting.add(node_id)

    def begin(self, node_id: int) -> _WalkState:
        """Classify ``node_id`` against both identity sets, entering it when it is new.

        The single admission point every recursive proof shares. Only the ``ENTERED``
        outcome puts the node on the ``visiting`` stack, so a caller that short-circuits
        on ``VALIDATED`` / ``CYCLE`` must NOT call ``leave``. The cycle DETAIL stays with
        the caller: each walker names the structure it is proving.
        """
        if node_id in self.validated:
            return _WalkState.VALIDATED
        if node_id in self.visiting:
            return _WalkState.CYCLE
        self.enter(node_id)
        return _WalkState.ENTERED

    def leave(self, node_id: int) -> None:
        """Promote ``node_id`` from in-progress to fully validated."""
        self.visiting.discard(node_id)
        self.validated.add(node_id)


def _walk_short_circuit(state: _WalkState, cycle_detail: str) -> tuple[str, str] | None:
    """Turn a non-``ENTERED`` walk state into the walker's own return value.

    ``VALIDATED`` means the node is already proven trusted, so the walk reports no
    defect; ``CYCLE`` means the node closes a reference cycle, which is untrusted state
    under ``cycle_detail`` -- the wording belongs to the call site because each walker
    names a different structure.
    """
    if state is _WalkState.VALIDATED:
        return None
    return ("untrusted", cycle_detail)


# Instance state a genuine Django ``get_source_expressions`` reads as a CONTAINER --
# it iterates, star-unpacks, or slices the slot to assemble the operand list it
# returns: ``Func.source_expressions``, ``Case.cases`` (``[*self.cases, self.default]``),
# and ``ColPairs.targets`` / ``.sources`` (zipped by ``get_cols``). Calling that genuine
# accessor is therefore NOT dispatch-free -- a container SUBCLASS planted in one of these
# slots runs its own ``__iter__`` / ``__getitem__`` during the very proof that is meant to
# decide whether the graph may be cloned, and by then the outer ``where`` tree has already
# been accepted, so that iterator can rewrite the accepted tree before
# ``sql.Query.clone`` runs. Each slot present on the instance must be exactly the builtin
# sequence Django stores there, proven BEFORE the accessor is invoked.
_EXPRESSION_SEQUENCE_STATE_ATTRS: tuple[str, ...] = (
    "source_expressions",
    "cases",
    "targets",
    "sources",
)


def _expression_state_defect(node: object, label: str) -> tuple[str, str] | None:
    """Validate expression-owned state that a genuine accessor reads, before calling it.

    ``node`` is already proven an EXACT genuine Django expression type with no
    instance-``__dict__`` method shadow, so ``node.get_source_expressions()`` resolves to
    Django's own implementation -- but that implementation still READS the node's own
    state, and state is consumer-controlled, so the accessor is not dispatch-free. Every
    slot a genuine accessor iterates, star-unpacks, or slices
    (``_EXPRESSION_SEQUENCE_STATE_ATTRS``) is therefore pinned to the exact builtin
    sequence Django stores there BEFORE the accessor is invoked, so no container
    subclass iterator can run during the proof.

    Slots are read straight from the instance ``__dict__`` so the validation itself
    dispatches nothing. Genuine Django only ever stores exact builtin sequences in these
    slots, so the check costs no legitimate query.
    """
    node_dict = truth.instance_state(node)
    for attr in _EXPRESSION_SEQUENCE_STATE_ATTRS:
        if attr in node_dict and not is_exact_list_or_tuple(node_dict[attr]):
            return ("untrusted", f"{label} {attr} is a {truth.kind(node_dict[attr])}")
    return None


def _genuine_node_defect(
    node: object,
    label: str,
    phrase: str = "is a",
    suffix: str = "",
) -> tuple[str, str] | None:
    """Prove ``node`` an exact genuine Django object, THEN that it carries no method shadow.

    The two proofs are ordered, not merely paired: ``_shadow_defect`` reads the node's
    ``__dict__`` and compares each key against a callable attribute of ``type(node)``,
    which is only meaningful once that type is known to be Django's own
    (``_type_is_genuinely_django``) -- a consumer type could otherwise define whatever
    callable surface makes its shadow look legitimate. Every compiler-reachable node
    (expression operands, ``alias_map`` joins and their ``filtered_relation``,
    ``_filtered_relations`` values) goes through this one ordering.

    The non-genuine detail reads ``"{label} {phrase} {type}{suffix}"`` and is formatted
    only on rejection, so a trusted node pays no string cost. Callers vary ``phrase`` /
    ``suffix`` to keep their own wording.
    """
    node_type = type(node)
    if not _type_is_genuinely_django(node_type):
        return ("untrusted", f"{label} {phrase} {truth.kind(node)}{suffix}")
    return _shadow_defect(node, label)


# Plain container types both graph walkers descend into member-wise. Django stores only
# these exact builtins in the slots they appear in; a SUBCLASS is not a container here,
# it is an object that must prove genuine-Django provenance like any other node.
# The plain containers the seal walks member-wise (and, having walked, must be
# able to REBUILD). ONE inventory of the sequence types and ``dict``, so no call
# site re-spells the union by hand and admitting a new container type is one
# edit here.
#
# The prove side and the rebuild side (``_reconstructed_value``) are two halves of
# one round trip, and the dangerous direction is prover-accepted /
# rebuilder-unhandled: such a value reaches reconstruction, matches no branch, and
# fails the seal CLOSED with no indication that the inventories disagree.
# ``tests/utils/test_querysets.py`` asserts the rebuild side answers for every
# member of this set, so the two cannot drift silently.
_PLAIN_CONTAINER_TYPES: truth.IdentitySet[type[object]] = truth.IdentitySet(
    (
        list,
        tuple,
        set,
        frozenset,
        dict,
    ),
)


def _is_plain_container(value_type: type[object]) -> bool:
    """Return whether ``value_type`` is EXACTLY one of the walked plain containers.

    Exact-type membership, never ``issubclass``: a ``list`` / ``dict`` SUBCLASS
    can override ``__iter__`` / ``items`` and would dispatch consumer code mid
    walk, so it is not a plain container and falls through to the provenance
    proof instead.
    """
    return value_type in _PLAIN_CONTAINER_TYPES


def _is_plain_container_value(value: object) -> TypeGuard[_PlainContainer]:
    """Return whether ``value``'s exact type is one of the walked plain containers.

    ``_is_plain_container`` over ``type(value)``, stated on the value itself so the
    member-wise walk receives it as the container that check just proved it to be.
    """
    return _is_plain_container(type(value))


def _expr_mapping_key_detail(label: str, _key: object) -> str:
    """Non-string mapping-key detail for the expression-graph walk.

    This walker names the slot, not the offending key type; the key is accepted so both
    detail formatters share one signature.
    """
    return f"{label} has a non-string mapping key"


def _deferred_mapping_key_detail(label: str, key: object) -> str:
    """Non-string mapping-key detail for the deferred-filter value walk."""
    return f"{label} mapping key is a {truth.kind(key)}"


def _container_defect(
    value: _PlainContainer,
    walk: _GraphWalk,
    label: str,
    recurse: Callable[[object, _GraphWalk, str], tuple[str, str] | None],
    key_detail: Callable[[str, object], str],
) -> tuple[str, str] | None:
    """Walk a plain sequence / dict member-wise under the shared three-state guard.

    Containers take part in the identity walk exactly like nodes do: Django never nests
    a container inside itself, so a self-referential list / dict is untrusted state
    rather than a shared diamond, and accepting it would let the unbounded recursion
    resurface downstream as a raw ``RecursionError`` past the typed defect contract.

    ``recurse`` is the caller's own ``(value, walk, label)`` walker, so the expression
    graph and the deferred-filter values share this traversal while each keeps its own
    element rule. Dict keys must be ``str``, a ``str`` subclass included: a
    ``TextChoices`` / ``StrEnum`` member a JSON payload is keyed by is the key it spells,
    and canonical reconstruction (of the sealed query, and of a deferred filter's
    arguments before the bake) rebinds it as that exact text (``_normalized_bound_value``).
    ``key_detail`` formats the rejection because the two walkers word it differently.
    ``leave`` runs only when the whole container proves clean -- a defect returns
    immediately with the container still on the ``visiting`` stack, which the unwinding
    walk never consults again.
    """
    value_id = id(value)
    state = walk.begin(value_id)
    if state is not _WalkState.ENTERED:
        return _walk_short_circuit(state, f"{label} contains a reference cycle")
    if is_exact_dict(value):
        for key, item in value.items():
            if type(key) is not str and not is_str(key):
                return ("untrusted", key_detail(label, key))
            defect = recurse(item, walk, label)
            if defect is not None:
                return defect
    else:
        for item in value:
            defect = recurse(item, walk, label)
            if defect is not None:
                return defect
    walk.leave(value_id)
    return None


# Attribute-interception hooks that make a direct lookup RHS attack surface rather than
# data. Either name defined on the value's own type runs consumer code on EVERY attribute
# read the lookup and the database adapter perform against the value, so the object is
# dispatchable in practice even though it exposes no ``as_sql``. Hooks inherited from a
# trusted data base (``_DIRECT_RHS_TRUSTED_MRO``) are Python's / Django's own -- CPython's
# ``Decimal`` defines a C ``__getattribute__`` slot -- so only definitions BELOW those bases
# are consumer-injected.
_RHS_ATTRIBUTE_HOOKS: tuple[str, ...] = ("__getattr__", "__getattribute__")

# Bases a direct lookup RHS must descend from to count as plain query data. Membership is
# by SUBCLASS here, not exact type: a direct RHS legitimately carries consumer domain data
# -- a ``TextChoices`` member (a ``str`` AND ``enum.Enum`` subclass), a model instance in
# foreign-key position, a ``Decimal`` / ``UUID`` / date subclass -- none of which the
# compiler dispatches, because a dispatchable RHS is routed to the expression walk before
# this rule is consulted. The exact-type discipline that governs ``_INERT_VALUE_TYPES``
# elsewhere would fail-close ordinary consumer schemas here.
_DIRECT_RHS_DATA_BASES: tuple[type[object], ...] = (*_INERT_VALUE_TYPES, enum.Enum, models.Model)

# MRO entries whose own hook definitions are trusted: the data bases themselves plus
# ``object`` (whose ``__getattribute__`` every type inherits).
_DIRECT_RHS_TRUSTED_MRO: truth.IdentitySet[type[object]] = truth.IdentitySet(
    (*_DIRECT_RHS_DATA_BASES, object),
)


def _static_attr_present(value: object, name: str) -> bool:
    """Return whether ``name`` resolves on ``value`` WITHOUT running an attribute hook.

    Reproduces the ``hasattr(value, name)`` semantics Django itself uses to classify a
    lookup RHS (``Lookup.rhs_is_direct_value`` / ``Lookup.process_rhs`` test
    ``hasattr(rhs, "as_sql")``) -- instance ``__dict__`` first, then the type's MRO --
    while dispatching nothing: ``truth.static_attr`` reads the real slots and never
    invokes ``__getattr__`` / ``__getattribute__`` / a descriptor. The real ``hasattr``
    would run a consumer RHS object's attribute hook DURING the proof, before the query
    is cloned, which is exactly the dispatch the seal exists to prevent.
    """
    return truth.static_attr(value, name, MISSING_ATTRIBUTE) is not MISSING_ATTRIBUTE


def _is_text_term(item: object) -> TypeGuard[str]:
    """Return whether ``item`` is a text term Django reads as a name or a SQL fragment.

    The slots Django fills from ``order_by(...)`` / ``distinct(...)`` names and from
    ``extra(order_by=..., tables=..., where=...)`` take any ``str``: Django asks
    ``hasattr(item, "resolve_expression")`` and treats everything without one as text,
    so a ``TextChoices`` / ``StrEnum`` member names a column or carries a fragment
    exactly as its value does. The same question is asked here statically
    (``_static_attr_present``), so a ``str`` subclass that DOES define
    ``resolve_expression`` is an expression and is walked or refused as one, never
    compiled as text. Canonical reconstruction rebinds an admitted subclass as its exact
    text (``_normalized_bound_value``), so the sealed query compiles Django's own SQL.
    """
    return type(item) is str or (
        is_str(item) and not _static_attr_present(item, "resolve_expression")
    )


def _rhs_hook_defect(value_type: type[object], label: str) -> tuple[str, str] | None:
    """Return a defect if a direct-RHS type defines an attribute hook below its data bases.

    The real MRO and each class's real namespace are read (``truth.mro`` /
    ``truth.class_dict``), so a consumer METACLASS overriding ``__getattribute__`` cannot
    run code (or lie) during the very read meant to reject the type. Classes in
    ``_DIRECT_RHS_TRUSTED_MRO`` are skipped: their hooks are the interpreter's own.
    """
    for klass in truth.mro(value_type):
        if klass in _DIRECT_RHS_TRUSTED_MRO:
            continue
        klass_dict = truth.class_dict(klass)
        for hook in _RHS_ATTRIBUTE_HOOKS:
            if hook in klass_dict:
                return ("untrusted", f"{label} lookup rhs defines the {hook!r} attribute hook")
    return None


def _direct_rhs_defect(value: object, walk: _GraphWalk, label: str) -> tuple[str, str] | None:
    """Return a defect unless a direct (non-dispatched) lookup RHS is plain query data.

    A direct RHS is never compiled through ``as_sql``; Django binds it as a ``%s``
    parameter and the database adapter converts it. It is nonetheless consumer-controlled
    state the adapter will touch, and no source-expression walk reaches it -- an exact
    Django ``Lookup``'s ``get_source_expressions`` returns only ``[lhs]`` when the RHS is
    direct, so without this check the RHS would leave the boundary unproven.

    The rule is deliberately the least restrictive one that still rejects dispatchable
    state: an inert leaf or a plain container of them is data; anything else must define
    no attribute hook of its own (``_rhs_hook_defect``) and must descend from a plain-data
    base (``_DIRECT_RHS_DATA_BASES``) -- the leaf half, ``_plain_data_leaf_defect``, which
    a raw-SQL parameter meets too. That admits the domain values real schemas bind --
    ``TextChoices`` members, model instances, ``Decimal`` / ``UUID`` / date subclasses,
    and ``__in`` sequences of them -- while an arbitrary object, or one whose attribute
    reads run consumer code, fails closed. Every check is type-level, so no hook on the
    value is invoked while deciding.

    Admission here is not retention: a permitted scalar-base SUBCLASS instance (a
    ``TextChoices`` member, a ``Decimal`` / ``UUID`` / date subclass) never reaches the
    sealed query by reference, because Django and the database adapter invoke ordinary
    methods on a bound parameter that no hook scan can enumerate. Canonical
    reconstruction replaces each such instance with an exact inert value and retains a
    model instance as trusted schema (``_normalized_bound_value``), so this rule decides
    only what MAY be bound, not which object is.
    """
    if _is_inert_value(value):
        return None
    if _is_plain_container_value(value):
        return _container_defect(value, walk, label, _direct_rhs_defect, _expr_mapping_key_detail)
    return _plain_data_leaf_defect(value, label)


def _plain_data_leaf_defect(value: object, label: str) -> tuple[str, str] | None:
    """Return a defect unless a non-container bound value is plain data the seal may bind.

    The leaf half of the admitted-bound-value rule, shared by a direct lookup RHS
    (``_direct_rhs_defect``) and a raw-SQL parameter (``_raw_sql_params_defect``): the
    value's type defines no attribute hook of its own (``_rhs_hook_defect``) and descends
    from a plain-data base (``_DIRECT_RHS_DATA_BASES``). Both checks read the type, so
    no hook on the value runs while deciding.
    """
    value_type = type(value)
    hook_defect = _rhs_hook_defect(value_type, label)
    if hook_defect is not None:
        return hook_defect
    if not issubclass(value_type, _DIRECT_RHS_DATA_BASES):
        return ("untrusted", f"{label} lookup rhs is a {truth.kind(value)}")
    return None


def _lookup_operands_defect(node: object, walk: _GraphWalk, label: str) -> tuple[str, str] | None:
    """Walk an exact genuine Django ``Lookup``'s operands without calling a bound accessor.

    ``Lookup.get_source_expressions`` cannot be used to discover a lookup's children: it
    first calls ``self.rhs_is_direct_value()``, whose ``hasattr(self.rhs, "as_sql")`` runs
    an arbitrary consumer RHS object's ``__getattr__`` hook DURING the proof -- while the
    query is still un-cloned and the boundary has not yet decided whether the graph may be
    compiled -- and it then returns ``[lhs]`` alone for a direct RHS, leaving that value
    unproven even though the adapter consumes it later.

    Both operands are therefore read straight from the instance ``__dict__``. ``node`` is
    already proven an EXACT genuine Django ``Lookup`` with no method shadow, so that read
    dispatches nothing and cannot raise (``_shadow_defect`` fails closed first on an
    instance with no ``__dict__``). ``lhs`` is always an expression and recurses through
    the ordinary graph walk. The RHS is classified STATICALLY -- ``as_sql`` resolved
    without invoking an attribute hook (``_static_attr_present``), the same slot Django's
    own ``hasattr`` would find -- so a dispatched RHS recurses like any other node and a
    direct one must satisfy the inert-data rules.
    """
    node_dict = truth.instance_state(node)
    lhs_defect = _expr_graph_defect(node_dict.get("lhs"), walk, label)
    if lhs_defect is not None:
        return lhs_defect
    rhs = node_dict.get("rhs")
    if _static_attr_present(rhs, "as_sql"):
        return _expr_graph_defect(rhs, walk, label)
    return _direct_rhs_defect(rhs, walk, label)


def _expr_graph_defect(node: object, walk: _GraphWalk, label: str) -> tuple[str, str] | None:
    """Return the first non-genuine / shadowed node in an expression graph, or ``None``.

    The single recursive, identity-memoized traversal of every compiler-reachable
    node hanging off one expression slot (a ``where`` leaf, an annotation value, an
    ``order_by`` element), never a top-level-only inventory
    (spec-045 Decision 2): each node must be an inert value, a plain
    container walked member-wise, an EXACT ``WhereNode`` subtree, or an EXACT genuine
    Django expression that is unshadowed, whose expression-owned state is exact-builtin
    shaped (``_expression_state_defect``, proven BEFORE the accessor that reads it runs),
    AND whose own operands (``get_source_expressions``, or raw ``lhs`` / ``rhs`` state for
    a ``Lookup`` -- see ``_lookup_operands_defect``) and any inner ``Subquery``
    recurse under the same rule. ``walk`` (node ``id``) collapses a shared expression
    diamond to a single visit, keeping the walk linear in the graph's unique node count,
    and rejects a cycle as untrusted.
    """
    if _is_inert_value(node):
        return None
    node_type = type(node)
    if _is_plain_container_value(node):
        return _container_defect(node, walk, label, _expr_graph_defect, _expr_mapping_key_detail)
    # ``WhereNode`` and ``sql.Query`` (a subquery's inner query, surfaced by
    # ``Subquery.get_source_expressions``) route to their dedicated walkers BEFORE this
    # level touches ``walk`` -- those walkers own the bookkeeping for their node, so
    # pre-marking the id here would make their own revisit guard short-circuit and skip
    # the subtree (a hostile leaf inside a subquery ``where`` would then escape).
    if node_type is WhereNode:
        return _where_tree_defect(node, walk)
    if node_type is sql.Query:
        return _query_genuineness_defect(node, walk)
    node_id = id(node)
    state = walk.begin(node_id)
    if state is not _WalkState.ENTERED:
        return _walk_short_circuit(state, f"{label} contains a reference cycle")
    genuine_defect = _genuine_node_defect(node, label, "carries a", " node")
    if genuine_defect is not None:
        return genuine_defect
    metadata_defect = _node_metadata_defect(node, label)
    if metadata_defect is not None:
        return metadata_defect
    raw_sql_defect = _raw_sql_node_defect(node, label)
    if raw_sql_defect is not None:
        return raw_sql_defect
    # Expression-owned state is validated BEFORE the bound accessor below is invoked:
    # a genuine ``get_source_expressions`` reads that state, so an unvalidated container
    # subclass there would run consumer code during the proof itself.
    state_defect = _expression_state_defect(node, label)
    if state_defect is not None:
        return state_defect
    if issubclass(node_type, Lookup):
        # A ``Lookup``'s own discovery accessor runs a consumer RHS's attribute hook and
        # hides a direct RHS from the walk, so its operands are read from raw state
        # instead (``_lookup_operands_defect``).
        operands_defect = _lookup_operands_defect(node, walk, label)
        if operands_defect is not None:
            return operands_defect
    elif getattr(node_type, "get_source_expressions", None) is not None:
        # ``node_type`` is an exact genuine Django class (proven above) that defines
        # ``get_source_expressions``, Django's own operand accessor.
        holder = cast("_SourceExpressionNode", node)
        for child in holder.get_source_expressions():
            defect = _expr_graph_defect(child, walk, label)
            if defect is not None:
                return defect
    walk.leave(node_id)
    # A ``Subquery`` / ``Exists`` surfaces its wrapped inner ``sql.Query`` through
    # ``get_source_expressions`` (verified for every genuine Django subquery node), so
    # the loop above already routes that inner query to ``_query_genuineness_defect``
    # (via the ``node_type is sql.Query`` branch) and recurses its whole graph -- a
    # foreign inner ``Query`` subclass or a buried consumer expression fails closed
    # there (``test_hostile_subquery_inner_query_fails_closed`` /
    # ``test_hostile_expression_inside_genuine_subquery_where_fails_closed``). No
    # separate subquery re-walk is needed; adding one would be dead, unreachable code
    # because ``get_source_expressions`` front-validates the same inner query.
    return None


def _expr_sequence_defect(holder: object, walk: _GraphWalk, label: str) -> tuple[str, str] | None:
    """Return a defect for an ``order_by`` / ``group_by`` / ``select`` sequence, or ``None``.

    These slots hold a mix of plain field-reference strings (safe) and expressions
    the compiler dispatches ``as_sql`` on. ``None`` and a bare ``bool`` (``group_by``
    is ``True`` / ``False`` for the default cases) carry no node. A text term
    (``_is_text_term``: an exact ``str``, or a ``TextChoices`` / ``StrEnum`` member
    Django reads as the name it spells) passes; every other element recurses through
    ``_expr_graph_defect`` so a consumer ``order_by`` expression fails closed
    (spec-045 Decision 2).
    """
    if holder is None or type(holder) is bool:
        return None
    if not is_exact_list_or_tuple(holder):
        return ("untrusted", f"query {label} is a {truth.kind(holder)}")
    for item in holder:
        if _is_text_term(item):
            continue
        defect = _expr_graph_defect(item, walk, label)
        if defect is not None:
            return defect
    return None


def _raw_sql_sequence_defect(holder: object, label: str) -> tuple[str, str] | None:
    """Return a defect for an ``extra_order_by`` / ``extra_tables`` sequence, or ``None``.

    The ``.extra()`` raw-SQL slots the compiler emits VERBATIM (never compiled through an
    expression's ``as_sql``): ``extra_order_by`` fragments become ``ORDER BY`` text and
    ``extra_tables`` become ``FROM`` aliases. No source-expression walk reaches them
    (spec-045 Decision 2), so without this check a non-``str`` element -- an object
    whose ``__str__`` runs at SQL-assembly time -- or a sequence SUBCLASS with a stateful
    ``__iter__`` would escape. Django stores an exact ``tuple`` / ``list`` here, each
    element the ``str`` the consumer passed; an element must be a text term
    (``_is_text_term``), which canonical reconstruction rebinds as its exact text, and
    anything else fails closed.
    """
    if holder is None:
        return None
    if not is_exact_list_or_tuple(holder):
        return ("untrusted", f"query {label} is a {truth.kind(holder)}")
    for item in holder:
        if not _is_text_term(item):
            return ("untrusted", f"query {label} carries a {truth.kind(item)}")
    return None


def _join_defect(join: object, alias: str, walk: _GraphWalk) -> tuple[str, str] | None:
    """Return a defect if an ``alias_map`` join is not a genuine, unshadowed Django join.

    ``sql.Query.clone`` shallow-copies ``alias_map`` (sharing the join objects) and
    the compiler later dispatches each join's ``as_sql`` / ``relabeled_clone``, so a
    consumer ``Join`` subclass -- or an exact ``BaseTable`` / ``Join`` with a shadowed
    method -- would run at compile time. Exact genuine Django join types only.

    A ``Join`` produced by ``.filter()`` over a ``FilteredRelation`` (Django's
    ``FilteredRelation`` / ``FILTERED_RELATION``) carries ``join.filtered_relation``,
    whose ``resolved_condition`` (a ``WhereNode``) the compiler dispatches from
    ``Join.as_sql`` -> ``FilteredRelation.as_sql`` (spec-045 Decision 2). That condition
    is NOT reachable from ``alias_map`` alone, so
    when present the filtered relation must itself be genuine + unshadowed and its
    resolved condition must pass the ``where``-tree walk; otherwise a consumer
    expression buried there would strip / rewrite the visibility predicate at compile
    time. ``walk`` is shared so a condition reachable two ways is walked once.
    """
    join_defect = _genuine_node_defect(join, f"join for alias {alias!r}")
    if join_defect is not None:
        return join_defect
    filtered: object = getattr(join, "filtered_relation", None)
    if filtered is None:
        return None
    filtered_defect = _genuine_node_defect(
        filtered,
        f"join for alias {alias!r} filtered_relation",
    )
    if filtered_defect is not None:
        return filtered_defect
    resolved: object = getattr(filtered, "resolved_condition", None)
    if resolved is None:
        return None
    return _where_tree_defect(resolved, walk)


def _where_tree_defect(node: object, walk: _GraphWalk) -> tuple[str, str] | None:
    """Return the first non-genuine / shadowed node in a ``where`` tree, or ``None``.

    ``sql.Query.clone`` calls ``self.where.clone()``, which dispatches
    ``child.clone()`` on every child, so a consumer ``WhereNode`` subclass -- OR an
    EXACT ``WhereNode`` whose instance ``__dict__`` shadows ``clone`` -- would run
    during sealing and strip the visibility predicate (spec-045 Decision 2, and
    the exact-``WhereNode`` shadow vector: a shadowed ``clone`` fires mid-seal and
    the sealed SQL loses its ``WHERE``). Every
    internal node must be EXACTLY ``WhereNode`` and unshadowed; every leaf and every
    leaf operand recurses through ``_expr_graph_defect`` so a consumer expression in
    lookup-RHS position or a shadowed ``as_sql`` on an exact Django leaf
    also fails closed.
    """
    if type(node) is not WhereNode:
        return _expr_graph_defect(node, walk, "where clause")
    node_id = id(node)
    state = walk.begin(node_id)
    if state is not _WalkState.ENTERED:
        return _walk_short_circuit(state, "where node contains a reference cycle")
    shadow = _shadow_defect(node, "where node")
    if shadow is not None:
        return shadow
    node_dict = truth.instance_state(node)
    # ``WhereNode.as_sql`` interpolates ``self.connector`` (``AND`` / ``OR``) straight
    # into the emitted SQL, so an instance override with a non-``str`` connector would
    # run its ``__str__`` at compile time (spec-045 Decision 2).
    connector = node_dict.get("connector")
    if connector is not None and type(connector) is not str:
        return ("untrusted", f"where node connector is a {truth.kind(connector)}")
    children = node_dict.get("children")
    if children is not None and not is_exact_list_or_tuple(children):
        return ("untrusted", f"where node children is a {truth.kind(children)}")
    for child in children or ():
        child_defect = _where_tree_defect(child, walk)
        if child_defect is not None:
            return child_defect
    walk.leave(node_id)
    return None


def _select_related_defect(select_related: object) -> tuple[str, str] | None:
    """Return a defect if ``select_related`` is not a plain bool / str-keyed dict tree.

    ``sql.Query.clone`` ``deepcopy``s ``select_related`` when it is not ``False``.
    Django only ever stores a bool or a nested ``{str: {str: ...}}`` dict there, so
    any other object (or a non-string key / non-dict value) is a consumer-injected
    structure whose ``__deepcopy__`` would dispatch during sealing; it fails closed
    as ``untrusted`` (spec-045 Decision 2).
    """
    if isinstance(select_related, bool):
        return None
    if not is_exact_dict(select_related):
        return ("untrusted", f"select_related is a {truth.kind(select_related)}")
    for key, value in select_related.items():
        if type(key) is not str:
            return ("untrusted", f"select_related key is a {truth.kind(key)}")
        nested_defect = _select_related_defect(value)
        if nested_defect is not None:
            return nested_defect
    return None


# Query containers ``sql.Query.clone`` calls ``.copy()`` on (dicts / sets) or
# ``deepcopy``s. Each must be EXACTLY the builtin Django uses so ``clone`` dispatches
# only builtin methods, never a consumer ``dict`` / ``set`` SUBCLASS ``.copy()`` (a
# custom ``alias_refcount.copy()`` would otherwise fire mid-clone).
_EXACT_DICT_QUERY_ATTRS: tuple[str, ...] = (
    "alias_refcount",
    "alias_map",
    "external_aliases",
    "table_map",
    "annotations",
    "_filtered_relations",
)
# ``extra`` is deliberately ABSENT: the raw-SQL scan below validates it as an
# exact ``dict`` with ``str`` keys AND its ``(sql, params)`` payloads, in
# byte-identical wording, so listing it here only ran the weaker half of that
# same check a second time on every seal.
_EXACT_SET_QUERY_ATTRS: tuple[str, ...] = (
    "annotation_select_mask",
    "extra_select_mask",
    "used_aliases",
    "subq_aliases",
)


def _query_payload_defect(query: object) -> tuple[str, str] | None:
    """Return a defect if a retained container's PAYLOAD is not its exact Django shape.

    The keys of ``alias_refcount`` / ``external_aliases`` / ``table_map`` /
    ``_filtered_relations`` are proven ``str`` by the caller; this proves what the
    dicts hold. Django's own invariants are narrow and are required exactly:

    - ``alias_refcount`` maps an alias to an exact ``int`` -- ``bool`` included in the
      rejection, since ``type(x) is int`` excludes it, and Django never stores one. The
      value is incremented / decremented by ``Query.ref_alias`` / ``unref_alias`` on
      every join reference, so an ``int`` SUBCLASS turns ordinary downstream query
      composition into a consumer callback with the sealed query in scope.
    - ``external_aliases`` maps an alias to an exact ``bool`` -- read as a truth value by
      the compiler and by ``Query.change_aliases``.
    - ``table_map`` maps a table name to an exact ``list`` of ``str`` aliases; the list
      itself is shallow-copied by ``clone`` and appended to by ``Query.join``.

    A key or alias may be a ``str`` subclass (a ``StrEnum`` member naming a
    ``FilteredRelation`` alias is stored as itself), so a defect label reads it through
    ``_normalized_str`` and never runs the subclass's ``__repr__``; canonical
    reconstruction rebinds every such name as its exact text.
    - ``_filtered_relations`` maps an alias to a ``FilteredRelation`` the compiler
      dispatches; it must be a genuine, unshadowed Django object like any other
      compiler-reachable node.
    """
    # ``_query_container_defect`` proved each of these an exact ``dict`` with ``str`` keys
    # (or absent) before calling here.
    refcount: dict[str, object] = getattr(query, "alias_refcount", None) or {}
    for alias, count in refcount.items():
        if type(count) is not int:
            return (
                "untrusted",
                f"query alias_refcount[{_normalized_str(alias)!r}] is a {truth.kind(count)}",
            )
    external: dict[str, object] = getattr(query, "external_aliases", None) or {}
    for alias, flag in external.items():
        if type(flag) is not bool:
            return (
                "untrusted",
                f"query external_aliases[{_normalized_str(alias)!r}] is a {truth.kind(flag)}",
            )
    table_map: dict[str, object] = getattr(query, "table_map", None) or {}
    for table, aliases in table_map.items():
        if not is_exact_list(aliases):
            return (
                "untrusted",
                f"query table_map[{_normalized_str(table)!r}] is a {truth.kind(aliases)}",
            )
        for table_alias in aliases:
            if not is_str(table_alias):
                table_label = _normalized_str(table)
                return (
                    "untrusted",
                    f"query table_map[{table_label!r}] carries a {truth.kind(table_alias)}",
                )
    filtered_relations: dict[str, object] = getattr(query, "_filtered_relations", None) or {}
    for alias, relation in filtered_relations.items():
        relation_defect = _genuine_node_defect(
            relation,
            f"query _filtered_relations[{_normalized_str(alias)!r}]",
        )
        if relation_defect is not None:
            return relation_defect
    return None


# Leaf types canonical reconstruction retains BY REFERENCE: the inert query-parameter
# set minus ``bytearray``, its one mutable member (a shared ``bytearray`` the candidate
# could still rewrite in place, so it is copied instead), plus the exact stdlib timezone
# types a genuine Django datetime expression stores in an ordinary instance slot
# (``Trunc(..., tzinfo=...)`` / ``Extract(..., tzinfo=...)`` keep the object on
# ``self.tzinfo``): ``datetime.timezone`` (not subclassable, so exact type covers every
# instance) and exact ``zoneinfo.ZoneInfo``, both immutable values whose every method is
# the interpreter's own. Every retained member is immutable, so sharing one between the
# candidate and the sealed query is unobservable.
_RETAINED_LEAF_TYPES: truth.IdentitySet[type[object]] = truth.IdentitySet(
    (
        *(leaf for leaf in _INERT_VALUE_TYPES if leaf is not bytearray),
        datetime.timezone,
        zoneinfo.ZoneInfo,
    ),
)

# Schema surfaces canonical reconstruction retains BY REFERENCE rather than rebuilds or
# normalizes: classes (``Query.model`` and every ``output_field`` class reference are
# shared schema), ``models.Field`` instances (the queried model's OWN column definitions,
# which rebuilding would detach from the model's descriptors), ``ForeignObjectRel``
# relation descriptors (the reverse side of those same fields -- a ``Join.join_field``
# over a reverse relation, whose state legitimately carries the model's own ``on_delete``
# / ``limit_choices_to`` callables), and ``models.Model`` instances (a bound value: in a
# lookup Django's own code extracts its pk; in a raw-SQL parameter it reaches the driver
# as is). One tuple so the rebuild-versus-retain policy (``_is_reconstructable_node``)
# and the bound-value rule (``_normalized_bound_value``) decide "trusted schema"
# identically and cannot drift.
_RETAINED_SCHEMA_BASES: tuple[type[object], ...] = (
    type,
    models.Field,
    ForeignObjectRel,
    models.Model,
)

# Types whose instances reconstruction retains BY REFERENCE, tested INLINE at every
# traversal step. Seeded with the retained leaves and grown lazily with the SCHEMA classes
# a query graph is full of -- ``models.Field`` subclasses, model classes (instances of a
# model metaclass), and relation / path descriptors. Growth is bounded by the installed
# schema: the ONE writer is ``_is_reconstructable_node``'s ``_RETAINED_SCHEMA_BASES``
# branch, so nothing a hostile hook plants can enter the set and thereby win the inline
# retain-by-reference test in every LATER seal this process runs.
_RETAINED_TYPES: truth.IdentitySet[type[object]] = truth.IdentitySet(_RETAINED_LEAF_TYPES)

# Positive-only memo of ``_is_reconstructable_node``: exact genuine Django AST classes
# proven once. Never holds a consumer type, so it cannot grow with consumer-defined
# classes.
_RECONSTRUCTABLE_NODE_TYPES: truth.IdentitySet[type[object]] = truth.IdentitySet()

# Instance attributes a rebuilt node leaves behind because Django's own copy of that node
# leaves them behind, so the rebuilt node recomputes each on first use exactly as the copy
# does and whatever the candidate holds under the name is never transferred, retained or
# called. ``convert_value`` is the row converter the ``BaseExpression.convert_value``
# ``cached_property`` stores on an expression the compiler selected
# (``SQLCompiler.get_converters`` at row fetch, through any clone sharing the node), which
# ``BaseExpression.__getstate__`` -- the state ``copy()`` / ``deepcopy`` / pickle read --
# drops (Django ticket #29330); ``sql.Query`` inherits that declaration and adds
# ``base_table``, the first-alias cache ``sql.Query.clone`` drops. The two sets restate
# Django's declarations and are pinned against the Django release under test
# (``tests/utils/test_querysets.py``), so a cache a later release adds to either fails the
# pin, and until it is listed here the rebuilt node takes it like any other slot (a
# function-valued one refused by the bound-value rule).
_EXPRESSION_COPY_DROPPED: frozenset[str] = frozenset({"convert_value"})
_QUERY_CLONE_DROPPED: frozenset[str] = _EXPRESSION_COPY_DROPPED | {"base_table"}


def _is_reconstructable_node(node_type: type[object]) -> bool:
    """Return whether canonical reconstruction rebuilds an object of ``node_type``.

    The reconstruction rebuilds QUERY AST, not schema and not bound data. An object is
    rebuilt when its type is a genuine Django implementation (proven by object identity
    against ``sys.modules``, the same provenance rule the graph proofs use) and is not
    one of the retained schema surfaces (``_RETAINED_SCHEMA_BASES``):

    - a CLASS is not a node (``Query.model`` and every ``output_field`` class reference
      are shared schema, and rebuilding a class is meaningless);
    - a ``models.Field`` is the queried model's OWN column definition -- part of the
      trusted schema the boundary composes over, not state the visibility hook injected
      -- and rebuilding it would detach it from ``field.model`` / the descriptor cache
      the compiler and the row initializer resolve against;
    - a ``ForeignObjectRel`` is the reverse side of such a field (a reverse-relation
      ``Join.join_field``), retained for the same reason -- and its state legitimately
      carries the model's own callables (``on_delete``), which are schema, not a bound
      payload;
    - a ``models.Model`` instance in an expression slot is a BOUND PARAMETER (Django
      extracts a lookup's pk from it; a raw-SQL parameter reaches the driver as is),
      inert with respect to SQL structure.

    Anything whose type is NOT genuine Django is likewise not rebuilt as a node: the only
    such objects the proofs admit are direct lookup right-hand-side values -- plain query
    data (``TextChoices`` members, ``Decimal`` / ``UUID`` / date subclasses, model
    instances) the adapter binds as ``%s`` parameters -- which carry no AST and whose
    ``__deepcopy__`` / ``__reduce__`` would dispatch consumer code mid-seal if copied.
    Those values go to ``_normalized_bound_value`` instead, which replaces a plain-data
    subclass with an exact inert equivalent, retains trusted schema and a bound model
    instance as-is, and fails everything else closed.

    A ``True`` verdict is memoized in ``_RECONSTRUCTABLE_NODE_TYPES``: sealing is a hot
    path and the identity proof walks ``sys.modules``, while the set of classes that can
    ever answer ``True`` is Django's own bounded AST surface. Only the positive verdict is
    cached, so a consumer type never enters the cache no matter how many classes it
    creates, and re-binding a Django module attribute afterwards cannot make an
    already-proven Django class stop being Django's own code.
    """
    if node_type in _RECONSTRUCTABLE_NODE_TYPES:
        return True
    if issubclass(node_type, _RETAINED_SCHEMA_BASES):
        _RETAINED_TYPES.add(node_type)
        return False
    if not _type_is_genuinely_django(node_type):
        return False
    _RECONSTRUCTABLE_NODE_TYPES.add(node_type)
    return True


def _normalized_str(value: str) -> str:
    """Return the exact ``str`` content of a ``str`` subclass instance."""
    return str.__str__(value)


def _normalized_bytes(value: bytes) -> bytes:
    """Return the exact ``bytes`` content of a ``bytes`` subclass instance."""
    return bytes.__getitem__(value, slice(None))


def _normalized_bytearray(value: bytearray) -> bytearray:
    """Return a fresh exact ``bytearray`` holding a ``bytearray`` subclass's bytes."""
    return bytearray.__getitem__(value, slice(None))


def _normalized_int(value: int) -> int:
    """Return the exact ``int`` value of an ``int`` subclass instance."""
    return int.__int__(value)


def _normalized_float(value: float) -> float:
    """Return the exact ``float`` value of a ``float`` subclass instance."""
    return float.__float__(value)


def _normalized_complex(value: complex) -> complex:
    """Return an exact ``complex`` built from a ``complex`` subclass's component slots."""
    return complex(complex.real.__get__(value), complex.imag.__get__(value))


def _normalized_decimal(value: Decimal) -> Decimal:
    """Return an exact ``Decimal`` rebuilt from a ``Decimal`` subclass's coefficient tuple."""
    # basedpyright: typeshed's Decimal() omits the DecimalTuple special-value exponents it accepts,
    # so it rejects ``DecimalTuple`` as ``_DecimalNew``
    return Decimal(Decimal.as_tuple(value))  # pyright: ignore[reportArgumentType]


def _normalized_date(value: datetime.date) -> datetime.date:
    """Return an exact ``datetime.date`` rebuilt from a date subclass's field slots."""
    return datetime.date(
        datetime.date.year.__get__(value),
        datetime.date.month.__get__(value),
        datetime.date.day.__get__(value),
    )


def _normalized_datetime(value: datetime.datetime) -> datetime.datetime:
    """Return an exact ``datetime.datetime`` rebuilt from a datetime subclass's field slots.

    ``tzinfo`` is carried over BY REFERENCE: it is the same object an exact
    ``datetime.datetime`` would carry, and an exact datetime is already an admitted inert
    bound value, so normalizing the instance does not widen what the adapter may touch.
    """
    base = datetime.datetime
    return base(
        base.year.__get__(value),
        base.month.__get__(value),
        base.day.__get__(value),
        base.hour.__get__(value),
        base.minute.__get__(value),
        base.second.__get__(value),
        base.microsecond.__get__(value),
        base.tzinfo.__get__(value),
        fold=base.fold.__get__(value),
    )


def _normalized_time(value: datetime.time) -> datetime.time:
    """Return an exact ``datetime.time`` rebuilt from a time subclass's field slots."""
    base = datetime.time
    return base(
        base.hour.__get__(value),
        base.minute.__get__(value),
        base.second.__get__(value),
        base.microsecond.__get__(value),
        base.tzinfo.__get__(value),
        fold=base.fold.__get__(value),
    )


def _normalized_timedelta(value: datetime.timedelta) -> datetime.timedelta:
    """Return an exact ``datetime.timedelta`` rebuilt from a timedelta subclass's slots."""
    base = datetime.timedelta
    return base(
        days=base.days.__get__(value),
        seconds=base.seconds.__get__(value),
        microseconds=base.microseconds.__get__(value),
    )


def _normalized_uuid(value: uuid.UUID) -> uuid.UUID:
    """Return an exact ``uuid.UUID`` rebuilt from a UUID subclass's integer slot."""
    # basedpyright: typeshed declares UUID.int an instance attribute, not its __slots__ descriptor,
    # so it reads ``UUID.int`` as an ``int`` with no ``__get__``
    return uuid.UUID(int=int.__index__(uuid.UUID.int.__get__(value)))  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]


# Plain-data bases a bound value may descend from, each paired with the primitive that
# rebuilds an EXACT instance of that base from a subclass instance. Every primitive reads
# the base type's OWN slot descriptors / C methods and never an instance-dispatched
# operation (no ``str(value)``, ``int(value)``, ``value.isoformat()``), so a subclass
# override -- an overridden ``__str__`` / ``__int__`` / ``__float__``, or a PROPERTY
# shadowing a field name such as ``year`` -- cannot run during normalization. Order is
# significant: ``datetime.datetime`` precedes ``datetime.date`` because it is a subclass
# of it, and the scalar bases precede the ``enum.Enum`` fallback so a ``TextChoices`` /
# ``IntegerChoices`` member (a ``str`` / ``int`` SUBCLASS) normalizes straight to its
# underlying exact scalar. ``bool`` is absent because it cannot be subclassed, and
# ``models.Model`` is absent because a model instance IS the bound value, retained as
# trusted schema.
# basedpyright: each normalizer takes its own pair's base, so no one Callable parameter type
# admits them all (parameters are contravariant); the issubclass test is the pairing proof
_BOUND_VALUE_NORMALIZERS: tuple[tuple[type[object], Callable[[Any], object]], ...] = (  # pyright: ignore[reportExplicitAny]
    (str, _normalized_str),
    (bytes, _normalized_bytes),
    (bytearray, _normalized_bytearray),
    (int, _normalized_int),
    (float, _normalized_float),
    (complex, _normalized_complex),
    (Decimal, _normalized_decimal),
    (datetime.datetime, _normalized_datetime),
    (datetime.date, _normalized_date),
    (datetime.time, _normalized_time),
    (datetime.timedelta, _normalized_timedelta),
    (uuid.UUID, _normalized_uuid),
)
# This is a hand-ordered MIRROR of ``_INERT_VALUE_TYPES`` minus ``bool`` (whose
# subclasses cannot exist): it pairs each base with its normalizer, and its ORDER is
# semantic -- ``datetime`` before ``date`` because the first subclasses the second --
# so it is written out rather than derived from the inert set.
# What CAN be checked without losing the order is that the two inventories still
# agree, and they must: an inert type admitted there with no normalizer entry
# here makes SUBCLASS instances of it fail the seal closed, and exact instances
# short-circuit earlier, so the gap stays invisible until a subclass shows up.
# ``tests/utils/test_querysets.py`` pins the agreement.


class _UntrustedBoundValueError(TypeError):
    """A bound payload that is neither inert, normalizable plain data, nor trusted schema.

    Raised by ``_normalized_bound_value`` when a bound value has no framework-owned
    representation, and caught by ``_reconstruction_defect`` so the seal reports a typed
    ``untrusted`` defect naming the payload's type. A distinct ``TypeError`` subclass so
    the reconstruction boundary can tell this deliberate refusal apart from an incidental
    failure (a re-hash raising) without matching on message text.
    """


def _normalized_bound_value(value: object) -> object:
    """Return an EXACT inert replacement for a plain-data SUBCLASS value; retain trusted schema.

    An admitted bound value is bound on plain-data ancestry rather than exact type,
    because real schemas bind ``TextChoices`` members and ``Decimal`` / ``UUID`` /
    date subclasses. Retaining such an instance BY REFERENCE in the sealed query would
    leave consumer code on the compile path: the absence of an ``__getattr__`` /
    ``__getattribute__`` hook does not stop Django or the database adapter from invoking
    an ordinary overridden method on a bound parameter (``__str__`` on a date, ``__int__``
    / ``__index__``, ``__float__``, an adapter ``__conform__``), and no enumeration of
    those methods can be complete. The sealed query therefore binds a framework-owned
    exact ``str`` / ``int`` / ``date`` / ``Decimal`` / ... whose every method is the
    interpreter's own, so the bound visibility value cannot change after sealing.

    Normalization itself dispatches nothing consumer-defined: each primitive in
    ``_BOUND_VALUE_NORMALIZERS`` reads the proven base type's own descriptors and C slots.
    An ``enum.Enum`` member with no scalar base is normalized to its underlying
    ``_value_``, read straight from the member's instance ``__dict__`` and normalized in
    turn. Trusted schema (``_RETAINED_SCHEMA_BASES``) is returned unchanged: a
    ``models.Model`` instance IS the bound value -- in foreign-key position Django's own
    code extracts its pk from a genuine-metaclass instance, and in a raw-SQL parameter it
    reaches the driver as is -- and a ``models.Field`` or a class is the queried model's
    own definition, not state the hook injected.

    Everything else FAILS CLOSED (spec-045 Decision 8): a bound payload that neither
    reduces to an exact inert value nor is trusted schema has no framework-owned
    representation, so it raises ``_UntrustedBoundValueError``, which the reconstruction
    boundary reports as an ``untrusted`` defect naming the type. This is the ONE home of
    the admitted-bound-value rule -- every bound payload reaches it through canonical
    reconstruction whether it sits in direct-lookup position, in an expression's own
    payload slot (``Value.value``), in raw-SQL params, or as a mapping key, so the verdict
    cannot vary with where the value sits. The same normalization rebinds a ``str``
    subclass the pre-clone checks admitted as a NAME or text term (a ``StrEnum``
    annotation key, ``table_map`` alias or ``extra_order_by`` element) as its exact text.
    """
    # Exact retained leaves pass through unchanged (the enum ``_value_`` recursion below
    # is the one caller that can hand this function an exact leaf). ``bytearray`` is NOT
    # in the retained set, so an exact one still routes to its copying normalizer rather
    # than being shared by reference.
    if value is None or truth.is_exact_one_of(value, _RETAINED_LEAF_TYPES):
        return value
    value_type = type(value)
    for base, primitive in _BOUND_VALUE_NORMALIZERS:
        if issubclass(value_type, base):
            normalized = primitive(value)
            break
    else:
        if issubclass(value_type, _RETAINED_SCHEMA_BASES):
            return value
        if not issubclass(value_type, enum.Enum):
            raise _UntrustedBoundValueError(f"binds a {truth.kind(value)} bound value")
        member_state = truth.instance_state(value)
        normalized = _normalized_bound_value(member_state["_value_"])
    if not _is_inert_value(normalized):
        raise _UntrustedBoundValueError(f"binds a {truth.kind(value)} bound value")
    return normalized


def _reconstructed_value(value: object, memo: dict[int, object]) -> object:
    """Return a framework-owned reconstruction of one validated query-state value.

    The recursive half of canonical reconstruction. Mutable builtin containers are
    rebuilt member-wise; every genuine Django AST node (``_is_reconstructable_node``) is
    re-instantiated as a fresh object of its OWN proven-genuine class via
    ``object.__new__`` and refilled slot-by-slot from the source instance ``__dict__``,
    each slot itself reconstructed, minus the derived caches Django's own copy of the node
    drops (``_EXPRESSION_COPY_DROPPED`` / ``_QUERY_CLONE_DROPPED``), which the rebuilt node
    recomputes on first use. Schema objects and bound model instances are retained
    by reference; every other bound value is an exact inert leaf, a plain-data subclass
    normalized to one, or refused closed (``_normalized_bound_value`` -- the one home of
    the admitted-bound-value rule). Mapping keys take the same rule as values.

    ``object.__new__`` + instance-``__dict__`` transfer rather than the node's own ``clone()``
    / ``copy()``: Django's expression ``copy()`` is a SHALLOW ``copy.copy`` (it would keep
    sharing the child graph, which is the whole point of the exercise) and ``deepcopy``
    is refused outright -- a direct lookup RHS is consumer plain data whose
    ``__deepcopy__`` / ``__reduce__`` would DISPATCH consumer code while the seal is
    still assembling the sealed query. The base allocator runs no ``__new__`` override, no
    ``__init__``, and no descriptor, and the transferred state is the state the graph
    proofs validated, less the dropped caches.

    ``memo`` maps a source object ``id`` to its reconstruction, so a node reached twice
    (Django reuses one ``Col`` / ``Value`` across ``where``, ``select`` and
    ``group_by``) reconstructs once and the sealed graph preserves the candidate's own
    sharing topology. Every source object stays reachable from the query being
    reconstructed for the whole pass, so an ``id`` cannot be recycled underneath the
    memo. A node is memoized BEFORE its slots are filled, so the pass terminates on any
    graph the proofs somehow admitted.

    A slotted genuine-Django object (no instance ``__dict__``) is not query AST and has no
    slot-by-slot reconstruction, so it takes the admitted-bound-value rule instead: every
    clonable / compilable node carries an instance ``__dict__``, while Django's slotted
    module-level exports are ``str`` subclasses (normalized to an exact ``str``) and
    namedtuples (refused closed). A namedtuple is NOT inert just because the tuple itself
    is immutable -- ``sql.Query.explain_info`` is an ``ExplainInfo`` whose ``options``
    member is a plain MUTABLE dict, and the compiler prepends
    ``explain_query_prefix(format, **options)`` to the emitted SQL of any query carrying
    one -- so retaining it by reference would leave the candidate holding a live handle
    into the sealed query's SQL. ``explain_info`` is one of the slots the graph proofs do
    not enumerate, which is exactly why the ownership decision has to be made here.

    Per-node SQL-template state needs no special case here, because validation already
    narrowed it to reconstructable shapes: an expression's ``extra`` mapping is an exact
    ``dict`` of text-term keys and exact inert scalar or text-term values, so the generic
    dict branch rebuilds it as a fresh framework-owned mapping whose every member is a
    bound leaf the interpreter owns, a ``TextChoices`` / ``StrEnum`` member rebound as
    its exact text like the same member on a named template slot. Nothing the compiler
    interpolates into a SQL template survives the seal as a consumer object.
    """
    value_type = type(value)
    if value is None or truth.is_exact_one_of(value, _RETAINED_TYPES):
        return value
    # Sealing is a hot path and query state is overwhelmingly retained leaves (alias
    # strings, flags, marks), so every comprehension below tests ``_RETAINED_TYPES``
    # INLINE and recurses only for a member that can carry AST, keeping the traversal one
    # call per non-leaf rather than one call per element.
    # Neither checker narrows ``value`` through the cached ``value_type``, so each branch
    # below casts to the exact builtin its identity test just proved.
    if value_type is tuple or value_type is frozenset:
        # IMMUTABLE containers take no memo entry: nothing can rewrite one in place, so
        # only their members need reconstruction, an empty one is already a shared
        # singleton, and a traversal cycle can only close through a MUTABLE member, which
        # IS memoized. Skipping the bookkeeping keeps the commonest query-state shape (a
        # tuple of alias strings) at one call and one allocation.
        frozen = cast("tuple[object, ...] | frozenset[object]", value)
        if not frozen:
            return value
        frozen_type = cast("type[tuple[object, ...] | frozenset[object]]", value_type)
        return frozen_type(
            [
                item
                if item is None or truth.is_exact_one_of(item, _RETAINED_TYPES)
                else _reconstructed_value(item, memo)
                for item in frozen
            ],
        )
    value_id = id(value)
    rebuilt = memo.get(value_id)
    if rebuilt is not None:
        return rebuilt
    if value_type is bytearray:
        # The one MUTABLE member of the inert-parameter set: copied, never shared.
        return bytearray(cast("bytearray", value))
    # A MUTABLE container is memoized EMPTY before its members are reconstructed, so a
    # graph that reaches it again mid-traversal terminates on the memo entry instead of
    # recursing forever.
    if value_type is list:
        rebuilt_list: list[object] = []
        memo[value_id] = rebuilt_list
        rebuilt_list.extend(
            [
                item
                if item is None or truth.is_exact_one_of(item, _RETAINED_TYPES)
                else _reconstructed_value(item, memo)
                for item in cast("list[object]", value)
            ],
        )
        return rebuilt_list
    if value_type is dict:
        rebuilt_dict: dict[object, object] = {}
        memo[value_id] = rebuilt_dict
        # Keys take the same retain-or-reconstruct rule as values: a rebuilt mapping that
        # kept a consumer-owned KEY by reference would still share a mutable object with
        # the candidate (and a JSON-bound payload dict may legitimately carry non-``str``
        # keys the graph proofs never constrain), so a key is retained only when it is a
        # retained leaf and otherwise reconstructed -- normalized, retained as schema, or
        # failed closed -- exactly like a value in the same slot.
        for raw_key, raw_item in cast("dict[object, object]", value).items():
            key = raw_key
            if not (key is None or truth.is_exact_one_of(key, _RETAINED_TYPES)):
                key = _reconstructed_value(key, memo)
            item = raw_item
            if not (item is None or truth.is_exact_one_of(item, _RETAINED_TYPES)):
                item = _reconstructed_value(item, memo)
            rebuilt_dict[key] = item
        return rebuilt_dict
    if value_type is set:
        rebuilt_set: set[object] = set()
        memo[value_id] = rebuilt_set
        rebuilt_set.update(
            [
                item
                if item is None or truth.is_exact_one_of(item, _RETAINED_TYPES)
                else _reconstructed_value(item, memo)
                for item in cast("set[object]", value)
            ],
        )
        return rebuilt_set
    if not _is_reconstructable_node(value_type):
        # Not query AST: either trusted schema / a bound model instance (returned
        # unchanged) or a plain-data SUBCLASS bound value, which is replaced by an exact
        # inert equivalent so no consumer method stays on the compile path.
        return _normalized_bound_value(value)
    source_state = truth.instance_dict(value)
    if source_state is None:
        # A genuine Django class whose instances are SLOTTED (the module-level namedtuple
        # and string-subclass exports) is not query AST: every clonable / compilable node
        # carries an instance ``__dict__``, so there is no state to rebuild slot-by-slot.
        # Retaining it by reference would share whatever its MEMBERS are -- an
        # ``ExplainInfo``'s ``options`` is a mutable dict the compiler interpolates into
        # the emitted SQL prefix -- so it takes the admitted-bound-value rule like any
        # other non-AST value: normalized when it reduces to an exact inert leaf, refused
        # closed otherwise.
        return _normalized_bound_value(value)
    # ``object.__new__``, never ``value_type.__new__``: the base allocator only, so a
    # class-level ``__new__`` (Django's ``@deconstructible`` wrapper, or any other) is not
    # dispatched during reconstruction and cannot observe or alter the fresh node before
    # its validated state is transferred.
    rebuilt = object.__new__(value_type)
    memo[value_id] = rebuilt
    dropped = _QUERY_CLONE_DROPPED if value_type is sql.Query else _EXPRESSION_COPY_DROPPED
    truth.instance_state(rebuilt).update(
        {
            key: item
            if item is None or truth.is_exact_one_of(item, _RETAINED_TYPES)
            else _reconstructed_value(item, memo)
            for key, item in source_state.items()
            if key not in dropped
        },
    )
    return rebuilt


def _rebuild_query_payloads(query: object) -> None:
    """Rebuild a cloned query's whole payload + AST graph as fresh framework-owned objects.

    ``sql.Query.clone`` is a SHALLOW copy: it rebuilds the ``where`` tree's ``WhereNode``
    wrappers and ``.copy()``s the retained dicts / sets, but the copy still shares, by
    identity, every leaf ``Lookup`` in the ``where`` tree, every ``annotations``
    expression, every ``alias_map`` join, every ``_filtered_relations`` object, every
    raw-SQL parameter container, and the lists inside ``table_map``. A consumer holding a
    reference into the candidate graph could therefore rewrite the sealed query AFTER the
    seal returned and BEFORE it compiled -- including the leaf that carries the
    visibility predicate itself, whose ``rhs`` a retained reference can flip.

    So the clone's state is CANONICALLY RECONSTRUCTED instead: every slot of the query's
    own ``__dict__`` is replaced by ``_reconstructed_value``, which rebuilds each mutable
    builtin container and each genuine Django AST node into a fresh framework-owned
    object of the same proven-genuine class. Afterwards the sealed query shares no
    mutable object with the candidate: not a ``WhereNode``, a ``Lookup``, an annotation
    expression, a ``Join`` / ``BaseTable``, a ``FilteredRelation`` and its resolved
    condition, a ``RawSQL`` / ``ExtraWhere`` parameter container, a ``table_map`` alias
    list, nor an embedded subquery ``sql.Query``. Combined branches are reconstructed by
    the same recursion, each keeping its own graph.

    What stays shared is deliberately inert: exact-``str`` / ``int`` / ``bool`` /
    ``Decimal`` / date / ``UUID`` leaves are BOUND PARAMETERS the adapter renders as
    ``%s``, never AST, and their every method is the interpreter's own, and the exact
    stdlib timezone objects (``datetime.timezone`` / ``zoneinfo.ZoneInfo``) a genuine
    ``Trunc`` / ``Extract`` carries are immutable interpreter-owned values retained the
    same way. A plain-data
    SUBCLASS leaf (a ``TextChoices`` member, a ``Decimal`` / date subclass) is NOT shared
    -- it is normalized to an exact inert equivalent, because an ordinary overridden
    method on it (``__str__``, ``__int__``, an adapter hook) would otherwise run consumer
    code at compile time and could change the bound value after sealing. A model instance
    IS the bound value and is retained: in foreign-key position Django's own code extracts
    its pk from a genuine-metaclass instance, and in a raw-SQL parameter it reaches the
    driver as is; ``models.Field`` instances and
    model classes are the trusted schema the boundary composes over, and rebuilding them
    would detach the compiler from the model's own descriptors. Any OTHER consumer
    payload -- an opaque object or a container subclass in an expression's own payload
    slot (``Value.value``), or planted as a mapping key -- has no framework-owned
    representation and fails the seal closed as ``untrusted`` rather than being retained
    by reference (spec-045 Decision 8); the graph proofs never enumerate such slots, so
    the ownership invariant is enforced here, where every retained object is decided.

    Runs only on the framework-owned clone, after the whole graph is proven genuine,
    unshadowed and exact-builtin shaped, so every read comes from validated state and
    reconstruction dispatches no consumer ``__init__``, descriptor, or copy hook.
    """
    memo: dict[int, object] = {}
    state = truth.instance_state(query)
    for key in tuple(state):
        state[key] = _reconstructed_value(state[key], memo)


def _reconstruction_defect(query: object, cls_name: str) -> tuple[str, str] | None:
    """Canonically reconstruct ``query`` in place, surfacing any failure as a typed defect.

    Reconstruction reads validated state and builds fresh builtins, so no consumer
    ``__init__`` / descriptor / copy hook runs -- but rebuilding a ``set`` or a ``dict``
    re-hashes its members, and a proven plain-data key / member still owns its
    ``__hash__``. The typed-defect contract holds across the whole seal path, so a raw
    exception from that (or from any other reconstruction step) is converted into an
    ``untrusted`` defect rather than escaping the boundary.

    A bound payload the admitted-bound-value rule refuses (``_UntrustedBoundValueError``)
    is the one deliberate rejection on this path, so its defect names the payload's type
    -- the consumer can find the ``Value(...)`` / expression slot that carries it --
    while an incidental failure keeps the generic wording.
    """
    try:
        _rebuild_query_payloads(query)
    except _UntrustedBoundValueError as refusal:
        return ("untrusted", f"{cls_name} {refusal}")
    except Exception:  # noqa: BLE001 - consumer code may raise anything
        return ("untrusted", f"{cls_name} query state cannot be reconstructed")
    return None


def _query_container_defect(query: object) -> tuple[str, str] | None:
    """Return a defect if any container ``sql.Query.clone`` copies is not an exact builtin.

    ``Query.clone`` calls ``.copy()`` on ``alias_refcount`` / ``alias_map`` /
    ``external_aliases`` / ``table_map`` / ``annotations`` / ``extra`` /
    ``_filtered_relations`` (dicts), on the ``annotation_select_mask`` /
    ``extra_select_mask`` / ``used_aliases`` / ``subq_aliases`` (sets), and on
    ``_extra_select_cache`` (dict). A consumer ``dict`` / ``set`` SUBCLASS with an
    overridden ``.copy()`` -- or a non-string mapping key that later raises out of
    ``getattr`` past the typed contract -- would dispatch consumer code during
    cloning, so each is required to be EXACTLY the builtin. Validates the object
    ATTRIBUTE ACCESS returns (what ``clone`` calls ``.copy()`` on -- a class default
    like ``subq_aliases`` lives off the instance ``__dict__``); the query is already
    proven exactly ``sql.Query`` and shadow-checked, so the reads run no consumer code.

    ``combined_queries`` (the ``.union()`` / ``.intersection()`` / ``.difference()``
    branch tuple) is required to be an EXACT ``tuple`` before any branch is walked:
    ``Query.clone`` rebuilds it as ``tuple(q.clone() for q in self.combined_queries)``,
    re-ITERATING it, so a ``tuple`` SUBCLASS with a stateful ``__iter__`` could yield
    ``concrete``'s branches during validation and a foreign model's branches during the
    clone / compile (spec-045 Decision 2). An exact tuple's
    iteration is deterministic, so validation and execution see identical branches.

    Container TYPE and KEYS are not sufficient: ``Query.clone``'s ``.copy()`` calls are
    SHALLOW, so every payload object inside a retained container survives into the sealed
    query and is later handed to Django's own bookkeeping. An ``int`` SUBCLASS stored as
    an ``alias_refcount`` value has its arithmetic invoked by ordinary downstream
    ``.filter()`` composition (``Query.ref_alias`` / ``unref_alias``), and that callback
    can rewrite the sealed ``where`` tree before the new predicate is added, dropping the
    visibility predicate from a queryset that already passed the seal. So each retained
    container is pinned to its COMPLETE Django shape -- exact-``int`` alias refcounts,
    exact-``bool`` external-alias flags, ``table_map`` entries that are exact lists of
    ``str`` aliases, ``str`` set members, genuine unshadowed ``_filtered_relations``
    values -- matching the payload validation ``extra`` / ``_extra_select_cache``
    already carried. Values whose own graph the AST walk proves (``alias_map`` joins,
    ``annotations`` expressions) are validated there, not here.

    A name (mapping key, set member, ``extra`` alias) must be a ``str``, a subclass
    included: Django stores the ``TextChoices`` / ``StrEnum`` member a consumer passes to
    ``annotate`` / ``alias`` / ``extra(select=...)`` / ``FilteredRelation`` as itself.
    The check reads the real type (``is_str``), a label reads the name through
    ``_normalized_str``, and canonical reconstruction rebinds every such name as its
    exact text, so the sealed query holds only exact ``str`` names.
    """
    for attr in _EXACT_DICT_QUERY_ATTRS:
        value: object = getattr(query, attr, None)
        if value is None:
            continue
        if not is_exact_dict(value):
            return ("untrusted", f"query {attr} is a {truth.kind(value)}")
        for key in value:
            if not is_str(key):
                return ("untrusted", f"query {attr} has a non-string key")
    payload_defect = _query_payload_defect(query)
    if payload_defect is not None:
        return payload_defect
    for attr in _EXACT_SET_QUERY_ATTRS:
        value = getattr(query, attr, None)
        if value is None:
            continue
        if not is_exact_set_or_frozenset(value):
            return ("untrusted", f"query {attr} is a {truth.kind(value)}")
        for member in value:
            if not is_str(member):
                return ("untrusted", f"query {attr} carries a {truth.kind(member)}")
    for attr in ("extra", "_extra_select_cache"):
        extra: object = getattr(query, attr, None)
        if extra is None:
            continue
        if not is_exact_dict(extra):
            return ("untrusted", f"query {attr} is a {truth.kind(extra)}")
        for raw_alias, payload in extra.items():
            if not is_str(raw_alias):
                return ("untrusted", f"query {attr} has a non-string key")
            alias = _normalized_str(raw_alias)
            if not is_exact_pair(payload):
                return ("untrusted", f"query {attr}[{alias!r}] has a malformed payload")
            statement, params = payload
            if type(statement) is not str:
                return (
                    "untrusted",
                    f"query {attr}[{alias!r}] SQL is a {truth.kind(statement)}",
                )
            params_defect = _raw_sql_params_defect(params, f"query {attr}[{alias!r}]")
            if params_defect is not None:
                return params_defect
    combined: object = getattr(query, "combined_queries", None)
    if combined is not None and type(combined) is not tuple:
        return ("untrusted", f"query combined_queries is a {truth.kind(combined)}")
    return None


def _query_ast_defect(query: object, walk: _GraphWalk) -> tuple[str, str] | None:
    """Return the first untrusted embedded AST node in ``query``, or ``None``.

    The complete genuineness walk over EVERY compiler-reachable expression slot the
    old inventory missed (spec-045 Decision 2): the ``where``
    and ``having`` trees and their leaf operands, ``annotations`` values (recursively,
    including nested ``Func`` / ``Case`` operands and inner ``Subquery`` graphs),
    the ``order_by`` / ``group_by`` / ``distinct_fields`` / ``select`` /
    ``values_select`` sequences, the ``alias_map`` joins (and any join's
    ``filtered_relation`` condition), the ``extra_order_by`` / ``extra_tables`` raw-SQL
    sequences (emitted verbatim by the compiler; spec-045 Decision 2), and the
    ``select_related`` structure. ``query`` is only ever
    passed here after the caller proved it is EXACTLY ``sql.Query`` and shadow-checked,
    so attribute access dispatches no consumer code and correctly returns class-default
    slots (``select_related`` is ``False``, ``order_by`` is ``()``) that never reach the
    instance ``__dict__``; ``walk`` is shared across every slot so a node reachable two
    ways is walked once.
    """
    where_defect = _where_tree_defect(getattr(query, "where", None), walk)
    if where_defect is not None:
        return where_defect
    having: object = getattr(query, "having", None)
    if having is not None:
        having_defect = _where_tree_defect(having, walk)
        if having_defect is not None:
            return having_defect
    # ``_query_container_defect`` proved ``annotations`` and ``alias_map`` exact ``dict``s
    # with ``str`` keys (or absent) before this walk runs; a key that is a ``str`` subclass
    # (a ``StrEnum`` alias) is read through ``_normalized_str`` before it is formatted.
    annotations: dict[str, object] = getattr(query, "annotations", None) or {}
    for name, expr in annotations.items():
        annotation_defect = _expr_graph_defect(
            expr,
            walk,
            f"annotation {_normalized_str(name)!r}",
        )
        if annotation_defect is not None:
            return annotation_defect
    for label in (
        "order_by",
        "group_by",
        "distinct_fields",
        "select",
        "values_select",
    ):
        sequence_defect = _expr_sequence_defect(getattr(query, label, None), walk, label)
        if sequence_defect is not None:
            return sequence_defect
    for label in ("extra_order_by", "extra_tables"):
        raw_defect = _raw_sql_sequence_defect(getattr(query, label, None), label)
        if raw_defect is not None:
            return raw_defect
    alias_map: dict[str, object] = getattr(query, "alias_map", None) or {}
    for alias, join in alias_map.items():
        join_defect = _join_defect(join, _normalized_str(alias), walk)
        if join_defect is not None:
            return join_defect
    return _select_related_defect(getattr(query, "select_related", False))


def _query_genuineness_defect(query: object, walk: _GraphWalk) -> tuple[str, str] | None:
    """Return the first genuineness defect in ``query`` (NO concrete-table check), or ``None``.

    A ``Subquery`` / ``Exists`` legitimately targets ANOTHER table, so only the
    genuineness half of ``_combined_query_table_defect`` applies to its embedded
    query -- every node it reaches must be genuine, unshadowed, and exact-builtin
    shaped so its clone / compile dispatch is trusted, but its base table is not
    required to be the outer concrete model. Fails closed unless the embedded query
    is EXACTLY ``sql.Query``; shares the caller's ``walk`` state and recurses combined
    branches under the same rule.
    """
    if type(query) is not sql.Query:
        return ("untrusted", f"embedded query is a {truth.kind(query)}")
    query_id = id(query)
    state = walk.begin(query_id)
    if state is not _WalkState.ENTERED:
        return _walk_short_circuit(state, "embedded query contains a reference cycle")
    shadow_defect = _shadow_defect(query, "subquery instance")
    if shadow_defect is not None:
        return shadow_defect
    container_defect = _query_container_defect(query)
    if container_defect is not None:
        return container_defect
    ast_defect = _query_ast_defect(query, walk)
    if ast_defect is not None:
        return ast_defect
    # ``_query_container_defect`` proved ``combined_queries`` an exact ``tuple`` or absent.
    combined_branches: tuple[object, ...] = getattr(query, "combined_queries", ()) or ()
    for branch in combined_branches:
        branch_defect = _query_genuineness_defect(branch, walk)
        if branch_defect is not None:
            return branch_defect
    walk.leave(query_id)
    return None


def _combined_query_table_defect(
    query: object,
    concrete: type[models.Model],
    branches: _GraphWalk | None = None,
) -> tuple[str, str] | None:
    """Return the first contributing-table / genuineness / foreign-branch defect, or ``None``.

    ``concrete`` is the registered type's ``_meta.concrete_model``, resolved once by
    the caller and threaded through the recursion (and into ``_base_table_defect``) so
    a single seal never re-walks that descriptor. This is the one place that proves,
    of a candidate ``sql.Query`` (and every combined branch), BOTH that it contributes
    only ``concrete``'s table AND that its whole clonable / compilable graph is trusted
    to dispatch:

    - ``Query.model`` may disagree with the public ``QuerySet.model`` (both are
      mutable); the SQL-bearing ``Query.model`` is validated directly. A ``None`` or
      non-model ``Query.model`` fails closed as a table defect -- a model-row select
      query with no model compiles to ``SELECT  FROM ...`` and escapes as malformed
      SQL otherwise (spec-045 Decision 5).
    - Any callable ``sql.Query`` method shadowed on the instance ``__dict__`` is
      rejected (``_shadow_defect``), and every container ``sql.Query.clone`` copies is
      required to be an exact builtin (``_query_container_defect``) -- both before the
      clone, because ``clone`` shallow-copies ``__dict__`` and calls ``.copy()`` /
      ``deepcopy`` on those containers (spec-045 Decision 2).
    - Every compiler-reachable embedded node (the ``where`` / ``having`` trees and
      their operands, ``annotations``, ``order_by`` / ``group_by`` / ``select`` /
      ``distinct`` sequences, ``alias_map`` joins, subquery graphs, ``select_related``)
      is proven a genuine, unshadowed Django implementation by ``_query_ast_defect``
      before the clone dispatches its ``clone`` / the compiler dispatches its
      ``as_sql`` (spec-045 Decision 2).
    - The alias map, once initialized, is the authoritative base table and can
      disagree with a since-reassigned ``Query.model`` -- ``_base_table_defect``
      catches that.
    - A combined queryset (``.union()`` / ``.intersection()`` / ``.difference()``)
      reports the outer model on ``QuerySet.model`` while a branch ``Query`` reads
      another model's table; with compatible projections the branch rows materialize
      as the outer model, so another table's rows would cross the boundary. Every
      ``combined_queries`` branch is recursed with the same checks, and a branch whose
      ``type(branch)`` is not exactly ``sql.Query`` is a foreign ``Query`` SUBCLASS
      whose consumer-overridable SQL synthesis fails closed as ``untrusted``.

    Returns ``(code, detail)`` -- ``code`` in ``{"table", "untrusted"}`` -- for the
    first offending branch, or ``None`` when every contributing table is
    ``concrete``'s table and the whole graph is trusted. A fresh ``walk`` state backs
    each top-level call so a shared expression diamond is walked once.

    ``branches`` is the three-state bookkeeping for the ``combined_queries`` recursion
    ITSELF, kept separate from the per-query AST walk: a branch reached again while it is
    still being validated closes a cycle (Django never builds one, and the recursion --
    here, in ``sql.Query.clone``, and in the compiler -- would otherwise escape as a raw
    ``RecursionError`` past the typed defect contract), while a branch already fully
    validated is a shared reference and is accepted. The AST walk cannot own this state:
    it deliberately admits an embedded ``sql.Query`` targeting ANOTHER table (a
    ``Subquery``), so a branch it already visited must still face the base-table proof
    here.
    """
    if branches is None:
        branches = _GraphWalk()
    query_id = id(query)
    state = branches.begin(query_id)
    if state is not _WalkState.ENTERED:
        return _walk_short_circuit(state, "combined-query branches contain a reference cycle")
    query_model: object = getattr(query, "model", None)
    if _concrete_or_none(query_model) is not concrete:
        return ("table", truth.name(query_model))
    shadow_defect = _shadow_defect(query, "query instance")
    if shadow_defect is not None:
        return shadow_defect
    container_defect = _query_container_defect(query)
    if container_defect is not None:
        return container_defect
    # The AST walk runs BEFORE the base-table check: it proves every ``alias_map`` join
    # is a genuine, unshadowed Django join, so ``_base_table_defect`` can then read the
    # first join's ``.table_name`` without dispatching consumer code.
    ast_defect = _query_ast_defect(query, _GraphWalk())
    if ast_defect is not None:
        return ast_defect
    base_defect = _base_table_defect(query, concrete)
    if base_defect is not None:
        return ("table", base_defect)
    # ``_query_container_defect`` proved ``combined_queries`` an exact ``tuple`` or absent.
    combined_branches: tuple[object, ...] = getattr(query, "combined_queries", ()) or ()
    for branch in combined_branches:
        if type(branch) is not sql.Query:
            return ("untrusted", f"combined-query branch is {truth.kind(branch)}")
        defect = _combined_query_table_defect(branch, concrete, branches)
        if defect is not None:
            return defect
    branches.leave(query_id)
    return None


# Django's own row-iterable classes. A sealed queryset may only carry one of
# these as its ``_iterable_class``: ``ModelIterable`` yields model instances,
# the four ``Values*`` classes yield the dict / tuple / namedtuple / flat shapes
# of ``.values()`` / ``.values_list()``. Anything else is a consumer-supplied
# row synthesizer (the ``.first()`` / ``.__aiter__()`` synthetic-row vector) and
# cannot be sealed.
_DJANGO_ITERABLE_CLASSES: truth.IdentitySet[type[object]] = truth.IdentitySet(
    (
        ModelIterable,
        ValuesIterable,
        ValuesListIterable,
        NamedValuesListIterable,
        FlatValuesListIterable,
    ),
)


def _is_django_iterable_class(value: object) -> TypeGuard[type[BaseIterable[object]]]:
    """Return whether ``value`` IS one of Django's own row-iterable classes."""
    return value in _DJANGO_ITERABLE_CLASSES


def _prefetch_path_or_defect(
    entry_state: Mapping[str, object],
    cls_name: str,
) -> tuple[_PrefetchPath | None, tuple[str, str] | None]:
    """Return a ``Prefetch``'s ``(prefetch_through, prefetch_to, to_attr)`` as exact text.

    The path state is what ``Prefetch.__init__`` stores from the consumer's lookup and
    ``to_attr``: a ``str``, the ``TextChoices`` / ``StrEnum`` member itself when the
    consumer named the relation with one, and ``None`` for an absent ``to_attr``. Each is
    admitted by its real type (``is_str``) and read through ``_normalized_str`` ONCE,
    here, so the relation-target guard (``_prefetch_relation_target_or_none``), every
    defect label and the rebuilt ``Prefetch`` all read the same exact text. Anything
    else fails closed as ``untrusted``.
    """
    through = entry_state.get("prefetch_through")
    prefetch_to = entry_state.get("prefetch_to")
    to_attr = entry_state.get("to_attr")
    if not is_str(through) or not is_str(prefetch_to):
        return None, ("untrusted", f"{cls_name} prefetch path is not a str")
    if to_attr is not None and not is_str(to_attr):
        return None, ("untrusted", f"{cls_name} prefetch to_attr is not a str or None")
    return (
        _normalized_str(through),
        _normalized_str(prefetch_to),
        None if to_attr is None else _normalized_str(to_attr),
    ), None


def _rebuilt_prefetch(
    path: _PrefetchPath,
    sealed_inner: models.QuerySet[models.Model, object] | None,
) -> _SealedPrefetch:
    """Rebuild a validated ``Prefetch`` as an EXACT ``django.db.models.Prefetch``.

    Every ``Prefetch`` -- including the ``queryset=None`` case -- is rebuilt from
    scratch so a consumer ``Prefetch`` subclass cannot survive with an executable
    ``get_current_querysets`` override that substitutes an unsealed child at fetch
    time (spec-045 Decision 4). Only the path state Django itself stores
    (``prefetch_through``, ``prefetch_to``, ``to_attr``), already read as exact text by
    ``_prefetch_path_or_defect``, is carried forward; a subclass-injected extra
    attribute is dropped.
    """
    through, prefetch_to, to_attr = path
    # ``Prefetch`` is generic only in django-stubs and not subscriptable at runtime, so the
    # parametrized class is named by annotation on a plain alias of it
    prefetch_cls: type[_SealedPrefetch] = Prefetch
    rebuilt = prefetch_cls.__new__(prefetch_cls)
    rebuilt_state = truth.instance_state(rebuilt)
    rebuilt_state["prefetch_through"] = through
    rebuilt_state["prefetch_to"] = prefetch_to
    rebuilt_state["to_attr"] = to_attr
    rebuilt_state["queryset"] = sealed_inner
    return rebuilt


def _prefetch_relation_target_or_none(
    parent_model: type[models.Model],
    path: object,
) -> type[models.Model] | None:
    """Return the model the prefetch lookup ``path`` terminates on, or ``None``.

    Resolves ``prefetch_through`` one segment at a time through each model's
    ``_meta`` (Django's own relation metadata -- no consumer dispatch, every
    ``parent_model`` here is already a proven model class) and returns the
    FINAL relation's ``related_model``. Each part is tried against the field map
    first (``_meta.get_field`` -- forward relations and explicit
    ``related_name``/bare-model-name reverse registrations), and on a miss
    against the model's reverse-ACCESSOR map: a reverse relation declared
    WITHOUT ``related_name`` is prefetched through the default
    ``<model>_set`` accessor (Django's own reverse-descriptor spelling) while
    the field map knows it under the bare child name, so the accessor scan is
    what proves the target for that spelling too -- ``Permission.user_set``,
    ``ContentType.permission_set``. A path that does not resolve to a
    relation at every segment (an unknown name, a plain column, a
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
        try:
            field: object = current._meta.get_field(part)
        except FieldDoesNotExist:
            # Not in the field map: the default ``<model>_set`` / bare-name
            # reverse accessor spelling (a relation declared without a
            # ``related_name``) is what prefetch actually accepts, so resolve
            # the part over the accessor map before giving up.
            field = _reverse_relation_by_accessor_or_none(current, part)
        if field is None or not getattr(field, "is_relation", False):
            return None
        related: object = getattr(field, "related_model", None)
        if not truth.is_subclass(related, models.Model):
            return None
        current = related
    return current


def _reverse_relation_by_accessor_or_none(model: type[models.Model], part: str) -> object:
    """Return the reverse relation whose accessor name is spelled ``part``.

    ``_meta.get_field`` registers a reverse relation under its declared name
    (the ``related_name``, or the child model's bare name when none is
    declared) -- NOT under the ``<model>_set`` accessor spelling the reverse
    descriptor (and therefore Django's prefetch traversal, which resolves the
    lookup by attribute access) actually accepts. The accessor map is Django's
    own relation metadata (``get_accessor_name()`` over ``_meta.get_fields()``),
    and only reverse relations (``ForeignObjectRel``) carry accessor names -- a
    forward M2M, a ``GenericForeignKey`` and a ``GenericRelation`` are
    non-concrete relations too, but have none; ``model`` is
    always an already-proven model class (the same proven ``parent_model`` walk
    the field-map path runs on), so no consumer dispatch is reachable. A miss
    returns ``None`` and the caller keeps the fail-open contract for genuinely
    unresolvable paths (generic FKs, lazy ``related_model`` strings, plain
    columns, unknown segments).
    """
    for candidate in model._meta.get_fields():
        if not isinstance(candidate, ForeignObjectRel):
            # Forward relations carry no accessor and are field-map names,
            # already resolved by ``_meta.get_field`` before this scan runs.
            continue
        accessor: object = candidate.get_accessor_name()
        if type(accessor) is str and accessor == part:
            return candidate
    return None


def _sealed_prefetch_related_lookups(
    lookups: object,
    cls_name: str,
    required_alias: str | None,
    parent_model: type[models.Model],
) -> tuple[tuple[str | _SealedPrefetch, ...] | None, tuple[str, str] | None]:
    """Seal every ``Prefetch`` entry's inner queryset; pass string lookups through.

    ``_prefetch_related_lookups`` entries are either plain string lookups (safe --
    Django builds the related queryset itself) or ``django.db.models.Prefetch``
    objects. A ``Prefetch`` carrying a consumer ``.queryset`` is the one-level-down
    leak vector the seal must close: at evaluation Django dispatches into that
    queryset's own ``_fetch_all`` / ``__iter__`` to populate the related
    descriptor, so a hostile ``QuerySet`` subclass could seed a synthetic
    in-memory row the SQL never selected and no visibility hook ever saw --
    defeating the seal's "never dispatch consumer code / never return synthetic
    rows" guarantee one edge down the object graph.

    Each such inner queryset is recursively sealed through ``_seal_or_defect``
    against its OWN declared model (read via ``__dict__``, never a shadowable
    descriptor) and rebuilt into a fresh plain ``Prefetch`` -- the subclass
    identity of both the inner queryset AND the ``Prefetch`` wrapper is dropped,
    so neither a hostile queryset override nor a hostile ``Prefetch`` method
    override can re-inject at fetch time. The child seal runs under
    ``_PREFETCH_CHILD_POLICY``, whose ``reject_sliced=False`` carries a sliced
    prefetch queryset through unchanged, while ``require_model_rows`` still
    holds. The licence covers exactly the ``Prefetch`` objects a CONSUMER built and
    attached to a queryset this seal received: the slice is the consumer's own
    ``Prefetch`` call, so Django's rules for it are the contract -- a sliced child
    survives when the lookup carries ``to_attr`` or targets a to-one relation, and
    raises Django's own ``TypeError`` when Django refilters it
    (``prefetch_one_level`` -> ``RelatedManager._apply_rel_filters``). This seal
    narrows neither, because rejecting the first shape would refuse a prefetch
    Django supports and the second is already Django answering for the consumer's
    own call. The package's OWN generated children are a different surface and do
    not pass through here: the walker seals them against the relation shape it
    plans (``_LIST_RELATION_CHILD_POLICY`` / ``_PREFETCH_CHILD_POLICY``). A child
    that cannot be sealed (a
    non-queryset ``.queryset``, a malformed model, or any state the child seal
    refuses -- ``_UNSEALABLE_STATE_CAUSES`` lists it) fails
    the OUTER seal closed with the ``untrusted`` defect -- carrying the inner
    child's own ``(code: detail)`` in the message rather than a generic string --
    rather than being silently dropped. A ``Prefetch`` whose ``.queryset is None``
    (Django builds the child itself) and a plain string lookup both pass through
    unchanged.

    The child's model must also belong to the RELATION the lookup path targets:
    Django's prefetch machinery populates the related cache from the child
    queryset without checking that its model matches the relation's target when
    both models carry a same-named foreign key (Django ticket #37267, unfixed),
    so a ``Prefetch("items", queryset=<unrelated model>.objects.all())`` over a
    coincidentally-named FK column would land that OTHER table's rows in the
    ``items`` relation -- rows the related type's ``get_queryset`` visibility
    hook never ran on, crossing the visibility boundary one edge down. The path
    is resolved here one segment at a time on the candidate's own model (the same
    resolution Django performs at fetch -- the declared ``related_name`` AND the
    default ``<model>_set`` accessor spelling a relation without one is reached
    by, e.g. ``Permission.user_set``) and the child's CONCRETE model must be the
    relation target's concrete model or one of its SUBCLASSES (proxy and MTI
    children are compatible, per Django's own directional contract). Both sides
    are reduced to their concrete model because the rule closes a cross-TABLE
    leak and a proxy reads its concrete model's table: a relation declared TO a
    proxy targets that same table, so comparing against the declared class would
    fail every child of such a relation closed. A child over an unrelated model fails
    the outer seal closed as ``untrusted``. A path whose target cannot be
    resolved here (a non-relation segment, a generic-FK alias) is left to
    Django's own fetch-time traversal unchanged -- the guard only ever narrows
    shapes Django itself mishandles, never a legitimate prefetch.

    Returns ``(sealed_lookups, None)`` on success or ``(None, (code, detail))``
    on the first unsealable child.
    """
    # ``_prefetch_related_lookups`` must be an exact ``tuple`` / ``list`` before it is
    # iterated: Django stores an exact tuple, and a consumer object with a custom
    # ``__bool__`` / ``__iter__`` would otherwise dispatch on the truthiness test / the
    # loop below (spec-045 Decision 1).
    if lookups is None:
        return (), None
    if not is_exact_list_or_tuple(lookups):
        return None, ("untrusted", f"{cls_name} prefetch lookups is a {truth.kind(lookups)}")
    sealed_entries: list[str | _SealedPrefetch] = []
    for entry in lookups:
        if not isinstance(entry, Prefetch):
            # A non-``Prefetch`` lookup must be a ``str`` (Django builds the related
            # queryset itself), a ``TextChoices`` / ``StrEnum`` member included; it is
            # carried as its exact text, and any other lookup object fails closed
            # (spec-045 Decision 4).
            if not is_str(entry):
                return None, ("untrusted", f"{cls_name} prefetch lookup is a {truth.kind(entry)}")
            sealed_entries.append(_normalized_str(entry))
            continue
        entry_state = truth.instance_state(entry)
        # The path is read as exact text BEFORE the relation-target guard below, so a
        # ``StrEnum`` lookup resolves its relation exactly as its text does.
        path, path_defect = _prefetch_path_or_defect(entry_state, cls_name)
        if path_defect is not None:
            return None, path_defect
        # A ``None`` path defect means the path was read.
        path = cast("_PrefetchPath", path)
        lookup = path[0]
        inner = entry_state.get("queryset")
        sealed_inner: models.QuerySet[models.Model, object] | None = None
        if inner is not None:
            inner_state = (
                truth.instance_dict(inner) if isinstance(inner, models.QuerySet) else None
            )
            inner_concrete = (
                _concrete_or_none(inner_state.get("model")) if inner_state is not None else None
            )
            if inner_state is None or inner_concrete is None:
                return None, (
                    "untrusted",
                    f"{cls_name} prefetch {lookup!r} queryset cannot be sealed",
                )
            # The child's rows will be handed to the LOOKUP's relation at fetch
            # time, so the child must be over that relation's own model (or a
            # subclass of it -- Django's directional compatibility). An unrelated
            # model with a coincidentally same-named FK passes Django's prefetch
            # machinery (no model check there), and the foreign rows would land in
            # the related cache -- and then the GraphQL relation -- without the
            # related type's ``get_queryset`` visibility hook ever running on
            # them, a cross-table leak the sealed boundary exists to close. The
            # path resolves from the parent's model metadata with no dispatch; an
            # unresolvable path (a generic FK, a traversal Django resolves
            # differently at fetch) is left untouched here, exactly as before.
            #
            # Both sides of the comparison are CONCRETE models, because the leak
            # the rule closes is a cross-TABLE one and a proxy shares its
            # concrete model's table. A relation may legitimately be declared to
            # a proxy model, and ``inner_concrete`` is already the child's
            # concrete model, so comparing it against the declared target would
            # reject every child of such a relation -- including the relation's
            # own proxy -- for reading the very table the relation targets.
            relation_target = _prefetch_relation_target_or_none(parent_model, lookup)
            relation_concrete = (
                _concrete_or_none(relation_target) if relation_target is not None else None
            )
            if relation_concrete is not None and not issubclass(inner_concrete, relation_concrete):
                return None, (
                    "untrusted",
                    (
                        f"{cls_name} prefetch {lookup!r} queryset is over "
                        f"{truth.name(inner_state.get('model'))} rows, but the {lookup!r} "
                        f"relation targets {truth.name(relation_target)} rows; a prefetch "
                        "child over an unrelated table would populate the relation with rows "
                        "the related type's visibility hook never saw"
                    ),
                )
            # Thread the OUTER effective alias into the child seal, which runs
            # with ``require_shared_alias``: a child explicitly pinned to a DIFFERENT
            # alias fails closed (the seal's ``alias`` defect), and -- critically --
            # when the outer alias is UNRESOLVED (``effective_alias is None`` because
            # the parent is unrouted), an explicitly routed child ALSO fails closed
            # rather than being accepted onto a divergent database, so one GraphQL
            # resolution never schedules the parent and its related rows across two
            # connections (spec-045 Decision 4). An unrouted child inherits the
            # outer alias.
            # A consumer's own ``Prefetch`` child may be sliced (Django >= 4.2
            # top-N per parent, e.g.
            # ``Prefetch("items", queryset=Item.objects.all()[:5], to_attr="top")``).
            # The consumer wrote that slice into their own Django call, so Django
            # answers for it; the ``sliced`` rejection exists because THIS package
            # would recompose, and here it does not.  ``require_model_rows`` still
            # holds (Django itself requires a ``ModelIterable`` for a prefetch
            # queryset).
            # Both facts are the two fields ``_PREFETCH_CHILD_POLICY`` sets.
            sealed_inner, defect = _seal_or_defect(
                inner,
                # ``_concrete_or_none`` answered a model for this same slot above, which it
                # does only for a ``models.Model`` subclass.
                cast("type[models.Model]", inner_state.get("model")),
                required_alias,
                _PREFETCH_CHILD_POLICY,
            )
            if defect is not None:
                code, detail = defect
                return None, (
                    "untrusted",
                    f"{cls_name} prefetch {lookup!r} queryset cannot be sealed ({code}: {detail})",
                )
        sealed_entries.append(_rebuilt_prefetch(path, sealed_inner))
    return tuple(sealed_entries), None


def _deferred_value_defect(value: object, walk: _GraphWalk, label: str) -> tuple[str, str] | None:
    """Return a defect if a deferred-filter value is neither inert nor genuine-Django.

    A pending ``_deferred_filter``'s ``args`` / ``kwargs`` are baked by ``add_q`` ->
    ``build_filter``, which dispatches ``resolve_expression(self=query)`` on any value
    that is an expression -- a consumer expression could there erase the visibility
    predicate and return a genuine-looking ``Value`` that the post-bake walk cannot
    detect (spec-045 Decision 5). So every value is proven BEFORE the bake:

    - an inert query parameter, a nested ``Q`` (its children recurse), or a plain
      container is safe;
    - an object Django will treat as an EXPRESSION (its type defines
      ``resolve_expression``) must be a genuine, unshadowed Django expression graph;
    - a model instance WITHOUT a class- OR instance-level ``resolve_expression`` is the
      legitimate reverse-relation value (``RelatedManager.core_filters`` stores the
      instance); Django extracts its pk to a bound parameter and never hands it the
      query, so it cannot strip the predicate. ``build_filter`` decides whether to
      dispatch via ``hasattr(value, "resolve_expression")`` -- which finds an
      INSTANCE-level attribute too -- so a model instance carrying ``resolve_expression``
      in its own ``__dict__`` would still be dispatched and fails closed
      (spec-045 Decision 2);
    - anything else fails closed.
    """
    if _is_inert_value(value):
        return None
    value_type = type(value)
    if value_type is models.Q:
        # ``Q`` trees and plain containers take the same three-state walk as the
        # expression graph: Django never produces a self-referential ``Q`` / list /
        # dict, so a node reached while it is still being validated closes a cycle and
        # is untrusted -- accepting it would let the unbounded recursion resurface
        # downstream as a raw ``RecursionError`` past the typed contract.
        value_id = id(value)
        state = walk.begin(value_id)
        if state is not _WalkState.ENTERED:
            return _walk_short_circuit(state, f"{label} contains a reference cycle")
        # ``value_type is models.Q`` above; neither checker narrows through the cached type.
        q_children: Sequence[object] = cast("models.Q", value).children
        for child in q_children:
            if type(child) is models.Q:
                child_defect = _deferred_value_defect(child, walk, label)
            elif is_exact_pair(child) and type(child[0]) is str:
                child_defect = _deferred_value_defect(child[1], walk, label)
            else:
                return ("untrusted", f"{label} Q child is a {truth.kind(child)}")
            if child_defect is not None:
                return child_defect
        walk.leave(value_id)
        return None
    if _is_plain_container_value(value):
        return _container_defect(
            value,
            walk,
            label,
            _deferred_value_defect,
            _deferred_mapping_key_detail,
        )
    if getattr(value_type, "resolve_expression", None) is not None:
        return _expr_graph_defect(value, walk, label)
    if isinstance(value, models.Model):
        # A class-level ``resolve_expression`` was handled above; an INSTANCE-level one
        # (in the model instance's own ``__dict__``) is still found by ``build_filter``'s
        # ``hasattr`` and dispatched, so reject it. Read ``__dict__`` directly to detect
        # the shadow without triggering it.
        if "resolve_expression" in truth.instance_state(value):
            return ("untrusted", f"{label} model instance shadows resolve_expression")
        return None
    return ("untrusted", f"{label} is a {truth.kind(value)}")


# Django's ``_deferred_filter`` is ``(negate, args, kwargs)``.
_DEFERRED_FILTER_ARITY = 3


def _bake_deferred_filter_or_defect(
    rebuilt_query: sql.Query,
    deferred: object,
    cls_name: str,
) -> tuple[str, str] | None:
    """Bake a validated ``_deferred_filter`` onto the DETACHED clone, or return a defect.

    ``deferred`` is the ``(negate, args, kwargs)`` tuple Django's
    ``RelatedManager._apply_rel_filters`` leaves on ``instance.rel.all()`` (baked into
    ``_query`` only on first ``.query`` access). Resolved WITHOUT Django's
    ``QuerySet.query`` getter -- whose ``_filter_or_exclude_inplace`` / ``add_q`` are
    instance-shadowable and would dispatch consumer code mid-seal -- and WITHOUT
    mutating the candidate: the predicate is added to ``rebuilt_query`` (a
    framework-owned clone) through the UNBOUND ``sql.Query.add_q``. Every argument is
    proven inert / genuine-Django FIRST (``_deferred_value_defect``) so ``add_q``'s
    ``resolve_expression`` dispatch (spec-045 Decision 5) only ever runs
    genuine Django code, and then canonically rebuilt (``_reconstructed_value``,
    positional and keyword arguments alike), so ``add_q`` builds the predicate from
    framework-owned nodes: a ``TextChoices`` / ``StrEnum`` member is rebound as its
    exact text, Django's in-place alias relabelling never reaches a consumer-held
    subquery, and a bound payload the admitted-bound-value rule refuses, or a graph
    that cannot be rebuilt, fails closed. A malformed shape Django never produces (a
    non-3-tuple, a ``negate`` that is not an exact ``bool``, a non-dict / non-tuple args,
    a prohibited ``_connector`` / ``_negated`` kwarg, a bad field) fails closed as a
    typed ``untrusted`` defect, never a raw exception.
    """
    # Exact-shape gate BEFORE the unpack: tuple unpacking dispatches ``__iter__``,
    # so an arbitrary object planted in the slot must be rejected without iteration.
    if not is_exact_tuple(deferred) or len(deferred) != _DEFERRED_FILTER_ARITY:
        return ("untrusted", f"{cls_name} deferred filter is malformed")
    negate, args, kwargs = deferred
    if type(negate) is not bool:
        # ``~predicate if negate else predicate`` TRUTH-TESTS this slot, so an object
        # planted here decides through its own ``__bool__`` whether the predicate is
        # negated -- the one consumer-dispatch point left inside a helper whose whole
        # contract is that it runs genuine Django code over pre-proven arguments.
        # Django stores an exact ``bool`` here, so every other shape fails closed.
        return ("untrusted", f"{cls_name} deferred filter negate is a {truth.kind(negate)}")
    if not is_exact_dict(kwargs):
        return ("untrusted", f"{cls_name} deferred filter kwargs is a {truth.kind(kwargs)}")
    if not is_exact_list_or_tuple(args):
        return ("untrusted", f"{cls_name} deferred filter args is a {truth.kind(args)}")
    if PROHIBITED_FILTER_KWARGS.intersection(kwargs):
        return ("untrusted", f"{cls_name} deferred filter carries prohibited kwargs")
    walk = _GraphWalk()
    for value in args:
        arg_defect = _deferred_value_defect(value, walk, f"{cls_name} deferred filter arg")
        if arg_defect is not None:
            return arg_defect
    for key, value in kwargs.items():
        if type(key) is not str:
            return ("untrusted", f"{cls_name} deferred filter kwarg key is a {truth.kind(key)}")
        kwarg_defect = _deferred_value_defect(value, walk, f"{cls_name} deferred filter {key!r}")
        if kwarg_defect is not None:
            return kwarg_defect
    # ``add_q`` builds the predicate from the arguments as they stand, so they are
    # canonically reconstructed first: the baked predicate then holds framework-owned
    # nodes and containers, a ``TextChoices`` / ``StrEnum`` member rebound as its exact
    # text, and a bound payload the admitted-bound-value rule refuses fails closed here.
    memo: dict[int, object] = {}
    try:
        owned_args = [_reconstructed_value(value, memo) for value in args]
        owned_kwargs = {key: _reconstructed_value(value, memo) for key, value in kwargs.items()}
    except _UntrustedBoundValueError as refusal:
        return ("untrusted", f"{cls_name} deferred filter {refusal}")
    except Exception:  # noqa: BLE001 - consumer code may raise anything
        return ("untrusted", f"{cls_name} deferred filter state cannot be reconstructed")
    try:
        # Every kwarg key was proven an exact ``str`` by the loop above.
        predicate = models.Q(*owned_args, **cast("dict[str, object]", owned_kwargs))
        sql.Query.add_q(rebuilt_query, ~predicate if negate else predicate)
    except Exception:  # noqa: BLE001 - consumer code may raise anything
        return ("untrusted", f"{cls_name} carries malformed deferred-filter state")
    return None


def _queryset_state_defect(state: Mapping[str, object], cls_name: str) -> tuple[str, str] | None:
    """Return a defect if a RETAINED ``QuerySet`` state field is not its exact shape.

    Beyond the query graph, the seal carries a handful of ``QuerySet.__dict__`` fields
    onto the rebuilt queryset (``_db`` routing, ``_hints``, ``_fields``,
    ``_sticky_filter``, ``_for_write``, ``_fetch_mode``). Each is later subjected to
    truthiness, an equality / ``str`` comparison, or a ``dict`` copy, or (the fetch
    mode) dispatched on every row load; a consumer object overriding ``__bool__`` /
    ``__eq__`` / ``__str__`` / ``__iter__`` / ``fetch`` there would dispatch mid-seal or
    after it even though the field was read from ``__dict__`` without dispatch
    (spec-045 Decision 1). So each is pinned to the EXACT shape Django
    stores before it is used:

    - ``_db``: ``None`` or a ``str`` alias;
    - ``_hints``: ``None`` or an exact ``dict`` with exact-``str`` keys;
    - ``_fields``: ``None`` or an exact ``tuple`` of ``str`` names;
    - ``_sticky_filter`` / ``_for_write``: ``None`` or an exact ``bool``;
    - ``_fetch_mode``: absent (Django below 6.1) or an instance of exactly one of
      Django's own fetch-mode classes (``utils/_queryset_private.py::is_django_fetch_mode``).

    The ``_db`` alias and the ``_fields`` names are the values a consumer passed to
    ``using(...)`` / ``values(...)`` / ``values_list(...)``, which Django stores as
    given, so a ``TextChoices`` / ``StrEnum`` member is admitted by its real type
    (``is_str``); the seal reads each through ``_normalized_str`` before any comparison
    and carries the exact text forward (``_normalized_db`` / ``_normalized_fields``).
    """
    db = state.get("_db")
    if db is not None and not is_str(db):
        return ("untrusted", f"{cls_name}._db is a {truth.kind(db)}")
    hints = state.get("_hints")
    if hints is not None:
        if not is_exact_dict(hints):
            return ("untrusted", f"{cls_name}._hints is a {truth.kind(hints)}")
        for key in hints:
            if type(key) is not str:
                return ("untrusted", f"{cls_name}._hints has a non-string key")
    fields = state.get("_fields")
    if fields is not None:
        if not is_exact_tuple(fields):
            return ("untrusted", f"{cls_name}._fields is a {truth.kind(fields)}")
        for name in fields:
            if not is_str(name):
                return ("untrusted", f"{cls_name}._fields carries a {truth.kind(name)}")
    for attr in ("_sticky_filter", "_for_write"):
        flag = state.get(attr)
        if flag is not None and type(flag) is not bool:
            return ("untrusted", f"{cls_name}.{attr} is a {truth.kind(flag)}")
    fetch_mode = state.get("_fetch_mode", MISSING_ATTRIBUTE)
    if fetch_mode is not MISSING_ATTRIBUTE and not is_django_fetch_mode(fetch_mode):
        return ("untrusted", f"{cls_name}._fetch_mode is a {truth.kind(fetch_mode)}")
    return None


def _normalized_db(state: Mapping[str, object]) -> str | None:
    """Return the ``_db`` alias ``_queryset_state_defect`` proved, as its exact text."""
    db = state.get("_db")
    return None if db is None else _normalized_str(cast("str", db))


def _normalized_fields(state: Mapping[str, object]) -> tuple[str, ...] | None:
    """Return the ``_fields`` names ``_queryset_state_defect`` proved, each its exact text."""
    fields = state.get("_fields")
    if fields is None:
        return None
    return tuple([_normalized_str(name) for name in cast("tuple[str, ...]", fields)])


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
      will recompose onto them), and fusing them is what forced the cascade to
      re-implement the slice rejection at both of its own entry points. Off one
      edge down only where something downstream answers for the slice: the
      optimizer walker's nested-connection child, whose own gate
      (``optimizer/nested_fetch.py::unwindowable_child_queryset_reason``) degrades
      a sliced child to the fully-unplanned per-parent fallback instead of
      recomposing filters / ordering onto it, and a consumer's own ``Prefetch``
      child, whose slice is the consumer's own Django call and answers to Django's
      rules for it. It stays ON for the walker's plain-list-relation child
      (``_LIST_RELATION_CHILD_POLICY``), which no gate classifies and which Django
      refilters at fetch time.
    - ``rewrite_combined`` -- a ``union()`` / ``intersection()`` /
      ``difference()`` query is served as the set of primary keys it selects:
      the seal rebuilds it as ``<model>.filter(pk__in=<combined>.values("pk"))``
      (``_pk_membership_query_or_defect``), because every recomposing surface
      narrows, projects or prefetches through the sealed queryset and Django
      supports none of that on a combinator. A combined shape whose rows that
      rewrite would change fails closed with the ``combined`` defect. Off for
      the raw-list row source alone, where nothing recomposes: its one
      ``[start:stop]`` window runs on a combinator as Django serves it.
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
    - ``carry_result_cache`` -- the rebuild carries the source's fetched rows
      forward, read from the same instance state every other retained slot comes
      from, so a source that already holds rows is windowed from them instead of
      being re-queried. On for the raw-list row source alone, the one surface
      where nothing is composed after the rebuild and the window is therefore the
      only operation the rows still have to survive. It is the complement of
      ``require_unevaluated``, and no policy sets both.
    """

    require_model_rows: bool = True
    reject_sliced: bool = True
    rewrite_combined: bool = True
    require_shared_alias: bool = False
    require_unevaluated: bool = False
    carry_result_cache: bool = False


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
# The optimizer walker's NESTED-CONNECTION ``Prefetch`` child, and every
# consumer-supplied ``Prefetch`` child sealed by
# ``_sealed_prefetch_related_lookups``. Its nested-connection gate
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
# A raw-list row source about to be windowed by ``resource_policy.py``. Every axis
# that exists to protect a RECOMPOSITION is off, because nothing recomposes here:
# one ``[start:stop]`` is taken and Django takes it on a sliced query and on a
# combinator alike, so a combinator is served as the query it is rather than
# rewritten to its primary-key set. A ``.values()`` projection is a legitimate
# list of rows, and a source the consumer already evaluated brings its rows with
# it: the fetched rows travel onto the rebuild, so a project queryset class is
# windowed from what it already holds and costs what Django's own manager costs.
# What is NOT optional is the rebuild itself: the point of sealing here is that
# the slice runs on a queryset this package built.
_RAW_LIST_SOURCE_POLICY: _SealPolicy[object] = _SealPolicy(
    require_model_rows=False,
    reject_sliced=False,
    rewrite_combined=False,
    carry_result_cache=True,
)


def _routing_hints_equal(cand_hints: object, orig_hints: object) -> bool:
    """Return True if candidate and original routing hints match without consumer dispatch.

    Preserves the exact distinction between absent (``None``) and empty (``{}``)
    hints. Keys must match exactly and every value must be the SAME OBJECT the
    snapshot holds: Django's ``ConnectionRouter`` hands hint values to consumer
    routers untouched, and a router is free to tell two equal tokens apart by
    identity, so semantic equality cannot prove equal routing without running
    the router. Identity is the only comparison that proves it without dispatch.
    """
    if cand_hints is orig_hints:
        return True
    if cand_hints is None or orig_hints is None:
        return False
    if not is_exact_dict(cand_hints) or not is_exact_dict(orig_hints):
        return False
    if len(cand_hints) != len(orig_hints):
        return False
    for k, orig_v in orig_hints.items():
        if k not in cand_hints:
            return False
        if cand_hints[k] is not orig_v:
            return False
    return True


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


def _snapshot_routing_intent(queryset: object, method_name: str) -> _RoutingIntent:
    """Freeze a sealed source's routing BEFORE consumer code receives it.

    The post-``OrderSet`` seal compares the returned candidate against this
    baseline, and the baseline has to be taken before the public ``apply_*``
    call: the override is handed the very same queryset object, so reading its
    routing afterwards would read whatever the override left there. The hints
    dictionary is copied (its values are kept by reference, which is what
    :func:`_routing_hints_equal` compares), so an in-place ``_hints`` edit on
    the source cannot rewrite the expectation either.

    The effective alias is then RESOLVED here, through the same
    ``ConnectionRouter`` method Django's own ``QuerySet.db`` property would use
    (``db_for_write`` for a write-marked queryset, ``db_for_read`` otherwise),
    and the seal pins the accepted result onto it. Django's router always
    answers with a concrete alias, falling back to ``DEFAULT_DB_ALIAS``, so an
    unrouted source resolves just as it would at execution - only earlier, while
    the hint values still hold the state the source intended. Django takes any
    ``str`` a router answers as the alias it names, so a ``TextChoices`` /
    ``StrEnum`` member is admitted by its real type (``is_str``) and frozen as its
    exact text (``_normalized_str``), the alias the seal pins; any other answer
    raises ``ConfigurationError``.

    Reads come from the instance ``__dict__`` without attribute dispatch,
    matching the seal; the model comes from that same state, because the source
    reaching this seam is already a sealed framework-owned queryset whose
    ``model`` the visibility boundary proved. The router is the deployment's own
    code: whatever it raises propagates.
    """
    state: dict[str, object] = truth.instance_state(queryset)
    # The source is a queryset this package built, so its routing slots are the ones
    # Django's own ``QuerySet`` writes: ``_db`` an alias or ``None`` (``using``), and
    # ``_hints`` a str-keyed dict.
    db = cast("str | None", state.get("_db"))
    hints = cast("dict[str, object] | None", state.get("_hints"))
    model = state.get("model")
    for_write = state.get("_for_write") is True
    if type(hints) is dict:
        hints = dict(hints)
    if db is not None:
        return _RoutingIntent(db=db, hints=hints, effective_alias=db)
    if not truth.is_subclass(model, models.Model):
        raise ConfigurationError(
            f"{method_name} could not resolve the source QuerySet's effective database "
            f"alias: its model is {truth.kind(model)}, so no router answer can be "
            f"obtained for it.",
        )
    resolve = router.db_for_write if for_write else router.db_for_read
    alias = resolve(model, **(hints if type(hints) is dict else {}))
    if not is_str(alias):
        raise ConfigurationError(
            f"{method_name} could not resolve the source QuerySet's effective database "
            f"alias: the database router answered {truth.render(alias)} for "
            f"{truth.name(model)}; an alias must be a string.",
        )
    return _RoutingIntent(db=None, hints=hints, effective_alias=_normalized_str(alias))


_ROUTING_SCALAR_TYPES: truth.IdentitySet[type[object]] = truth.IdentitySet(
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
        return truth.render(value)
    if is_exact_dict(value):
        items: list[str] = []
        for k in sorted(value.keys(), key=truth.text):
            v = value[k]
            if truth.is_exact_one_of(v, _ROUTING_SCALAR_TYPES):
                v_repr = truth.render(v)
            else:
                v_repr = f"<{truth.name(v)} at {hex(id(v))}>"
            items.append(f"{truth.render(k)}: {v_repr}")
        return "{" + ", ".join(items) + "}"
    return truth.render(value)


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
        model_name = truth.name(model)
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
                "untrusted",
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
            f"Field target {truth.name(target_type)} has no orderset_class configured.",
        )
    return orderset_class


def _apply_sidecar_sync(
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
    method_name = f"{truth.name(set_class)}.apply_sync"
    # Frozen BEFORE the override receives the queryset: it can mutate the
    # object it was handed, so a post-call read is not a baseline.
    expected_routing = _snapshot_routing_intent(queryset, method_name)
    candidate = set_class.apply_sync(input_value, queryset, info)
    if inspect.isawaitable(candidate):
        _dispose_sync_awaitable(candidate)
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


async def _apply_sidecar_async(
    target_type: type[DjangoType],
    set_class: type[FilterSet | OrderSet],
    queryset: models.QuerySet[models.Model],
    input_value: object,
    info: object,
    *,
    model: type[models.Model],
) -> models.QuerySet[models.Model]:
    """Async sibling of :func:`_apply_sidecar_sync`, running the same one seal.

    The awaited result carries the same ``_SIDECAR_RESULT_POLICY`` contract;
    the extra arms reject a public method that never returned an awaitable at
    all, and one that awaited to a second awaitable.
    """
    method_name = f"{truth.name(set_class)}.apply_async"
    expected_routing = _snapshot_routing_intent(queryset, method_name)
    candidate_awaitable = set_class.apply_async(input_value, queryset, info)
    if not inspect.isawaitable(candidate_awaitable):
        raise ConfigurationError(
            f"{method_name} returned a non-awaitable value "
            f"({truth.kind(candidate_awaitable)}); expected an awaitable coroutine or Future.",
        )
    candidate = await candidate_awaitable
    if inspect.isawaitable(candidate):
        _dispose_sync_awaitable(candidate)
        raise ConfigurationError(
            f"{method_name} returned a residual awaitable value "
            f"({truth.kind(candidate)}); expected a QuerySet.",
        )
    return _validate_post_orderset_result(
        target_type,
        expected_routing,
        candidate,
        method_name,
        model=model,
    )


def apply_orderset_sync(
    target_type: type[DjangoType],
    orderset_class: type[OrderSet] | None,
    queryset: models.QuerySet[models.Model],
    order_by: object,
    info: object,
    *,
    model: type[models.Model],
) -> models.QuerySet[models.Model]:
    """Run ``OrderSet.apply_sync`` through the shared post-sidecar seal.

    Both the list field and the Relay connection field enter here; see
    :func:`_apply_sidecar_sync` for the seal itself.
    """
    orderset_class = require_orderset_class(target_type, orderset_class)
    return _apply_sidecar_sync(target_type, orderset_class, queryset, order_by, info, model=model)


async def apply_orderset_async(
    target_type: type[DjangoType],
    orderset_class: type[OrderSet] | None,
    queryset: models.QuerySet[models.Model],
    order_by: object,
    info: object,
    *,
    model: type[models.Model],
) -> models.QuerySet[models.Model]:
    """Async sibling of :func:`apply_orderset_sync`."""
    orderset_class = require_orderset_class(target_type, orderset_class)
    return await _apply_sidecar_async(
        target_type,
        orderset_class,
        queryset,
        order_by,
        info,
        model=model,
    )


def apply_filterset_sync(
    target_type: type[DjangoType],
    filterset_class: type[FilterSet],
    queryset: models.QuerySet[models.Model],
    filter_input: object,
    info: object,
    *,
    model: type[models.Model],
) -> models.QuerySet[models.Model]:
    """Run ``FilterSet.apply_sync`` through the shared post-sidecar seal.

    The Relay connection field is the one field publishing ``filter:``; its
    pipeline enters here so a filter override answers to the same contract as
    an ordering override (:func:`_apply_sidecar_sync`).
    """
    return _apply_sidecar_sync(
        target_type,
        filterset_class,
        queryset,
        filter_input,
        info,
        model=model,
    )


async def apply_filterset_async(
    target_type: type[DjangoType],
    filterset_class: type[FilterSet],
    queryset: models.QuerySet[models.Model],
    filter_input: object,
    info: object,
    *,
    model: type[models.Model],
) -> models.QuerySet[models.Model]:
    """Async sibling of :func:`apply_filterset_sync`."""
    return await _apply_sidecar_async(
        target_type,
        filterset_class,
        queryset,
        filter_input,
        info,
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

    From the seal, ``query`` is proven genuine and acyclic first
    (``_combined_query_table_defect`` walks every branch); from the optimizer
    walker's ``OptimizerHint.prefetch`` path it is trusted schema configuration
    that no seal has walked.
    """
    if query.combinator_all:
        return "union(all=True) keeps duplicate rows, which a primary-key set cannot"
    if outer:
        for entry in query.order_by:
            if not _is_carried_order_term(entry, model):
                return (
                    f"its ordering by {entry!r} is not a {truth.name(model)} column, so the "
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
) -> tuple[sql.Query | None, tuple[str, str] | None]:
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
    return truth.is_subclass(value, models.QuerySet)


def _seal_or_defect(
    candidate: object,
    model: type[models.Model],
    required_alias: str | None,
    policy: _SealPolicy[object] = _DEFAULT_SEAL_POLICY,
    *,
    expected_routing: _RoutingIntent | None = None,
    keep_class: bool = False,
) -> tuple[models.QuerySet[models.Model, object] | None, tuple[str, str] | None]:
    """Rebuild a framework-owned ``QuerySet`` from ``candidate``'s validated state.

    The single sealing primitive both boundary sites run. Returns
    ``(sealed_queryset, None)`` on success, or ``(None, (code, detail))`` on the
    first defect. The rebuild is a plain ``QuerySet`` unless ``keep_class`` asks
    for an instance of ``candidate``'s own class, constructed as Django's
    ``QuerySet._clone`` constructs one (``model`` / ``query`` / ``using`` /
    ``hints``) and given the same state as the plain rebuild; attributes the class
    sets on an instance outside those constructor arguments are not carried. Only
    the visibility runners ask, for the hook's input: the framework calls nothing
    on that object but ``.using()`` (the write-pipeline pin), and it re-seals
    whatever the hook returns.

    The codes ``type`` / ``table`` / ``untrusted`` / ``routing`` /
    ``evaluated`` / ``sliced`` / ``projection`` / ``combined`` / ``alias`` are the
    one vocabulary every message-building site shares (a new code owes an arm at
    every site that can reach it); they are not one execution order. The checks
    run: ``type``; ``table`` on the model slot; ``untrusted`` on the outer
    exact-``sql.Query`` and the retained ``__dict__`` slots; ``routing``; then the
    combinator table walk, reconstruction, deferred-filter bake (over reconstructed
    arguments, then re-proved), iterable-class, prefetch and result-cache checks
    (``table`` / ``untrusted``); then ``evaluated`` -> ``sliced`` -> ``projection`` ->
    ``combined`` (the rewritten query reconstructed in turn) -> ``alias``.
    Routing is proven before any graph walk or clone, so no reconstructed
    queryset exists for a re-routed candidate; the outer ``sql.Query`` is proven
    before the walk because the walk reads query attributes through normal
    attribute access.

    Every read of ``candidate`` state comes from its real instance ``__dict__``
    (via ``truth.instance_dict``), never through attribute access, so a custom
    ``__getattribute__``, a redefined ``__dict__``, an instance-shadowed callable,
    or a redefined ``query`` / ``_query`` descriptor cannot run code or return a
    lie during extraction.
    The extracted state is what BOTH the validation checks and the rebuilt seal
    consume, so validation and execution provably cannot diverge.

    Defects:

    - ``type`` -- not a ``QuerySet`` at all.
    - ``table`` -- a contributing table (public ``QuerySet.model``, SQL-bearing
      ``Query.model``, the baked base table in ``Query.alias_map``, or any
      ``combined_queries`` branch) is not the registered type's concrete table.
    - ``untrusted`` -- the state cannot be faithfully rebuilt into a trusted
      execution queryset: the ``_query`` is not exactly ``django.db.models.sql``
      ``.Query`` (a foreign ``Query`` subclass), a ``combined_queries`` branch is
      a foreign ``Query`` subclass (the outer exact-type check never reaches the
      branches, yet ``sql.Query.clone`` preserves them), the query instance
      shadows a callable ``sql.Query`` method in its ``__dict__`` (``chain`` /
      ``clone`` / any -- ``sql.Query.clone`` shallow-copies the source
      ``__dict__``, so the shadow would dispatch on the first post-seal transform),
      a container ``sql.Query.clone`` copies (``alias_map`` / ``annotations`` /
      ``used_aliases`` / ...) is not an exact builtin (a ``dict`` / ``set`` subclass
      whose ``.copy()`` would dispatch mid-clone, or a non-string mapping key), an
      embedded AST node ``sql.Query.clone`` clones or the compiler later executes is
      not a trusted Django implementation, proven by a COMPLETE recursive
      identity-memoized walk of every compiler-reachable node -- the ``where`` /
      ``having`` trees AND their leaf operands, ``annotations`` (incl. nested ``Func``
      / ``Case`` operands and inner ``Subquery`` graphs), ``order_by`` / ``group_by``
      / ``distinct`` / ``select`` sequences, ``alias_map`` joins, ``select_related``
      -- where each node must be an EXACT genuine Django type (proven by object
      identity against ``sys.modules``, never the spoofable ``__module__``) that is
      unshadowed (a consumer ``WhereNode`` subclass, a consumer expression anywhere in
      the graph, a consumer join, an exact Django node with a shadowed ``as_sql``, or
      a foreign ``select_related`` all fail closed -- consumer-defined expressions /
      lookups are NOT supported across the visibility boundary), the
      ``_iterable_class`` is not one of Django's own row iterables (a synthetic-row
      iterable), the ``_fetch_mode`` is not an instance of exactly one of Django's own
      fetch-mode classes (a ``FetchMode`` subclass whose ``fetch`` would run on every
      row load), the ``_deferred_filter`` STATE is not the exact shape Django writes --
      a non-3-tuple, a ``negate`` that is not an exact ``bool``, a ``kwargs`` that is
      not an exact ``dict``, an ``args`` that is neither ``tuple`` nor ``list``, a
      non-string kwarg key, a prohibited connector kwarg, a value that is neither inert
      nor genuine Django, or a predicate ``add_q`` cannot resolve (a PENDING predicate
      itself is not a defect on any class: ``RelatedManager._apply_rel_filters`` leaves
      one on every relation queryset it builds, so it is baked onto the DETACHED CLONE
      through the UNBOUND ``sql.Query.add_q`` after every argument is proven inert /
      genuine-Django, never Django's ``QuerySet.query`` getter -- whose
      ``_filter_or_exclude_inplace`` / ``add_q`` are instance-shadowable and whose
      ``resolve_expression`` dispatch would run a consumer expression mid-bake -- and
      the candidate is never mutated) -- or a
      ``Prefetch`` in ``_prefetch_related_lookups`` carries an inner queryset that
      cannot itself be sealed, a non-``str`` lookup or path, a consumer
      ``Prefetch`` subclass (rebuilt as an exact ``Prefetch`` so no
      ``get_current_querysets`` override survives), or an inner queryset whose
      model is unrelated to the lookup path's relation target (Django ticket
      #37267: the fetch-time traversal groups a wrong-model child into the
      related cache, so the sealed boundary proves the child's model is the
      relation's own target or a subclass of it before admitting the entry,
      under either the declared ``related_name`` or the default
      ``<model>_set`` accessor spelling) -- or, when ``policy.carry_result_cache``
      carries the fetched rows forward, a populated ``_result_cache`` that is not
      an exact ``list`` (a ``list`` subclass would answer the windowing subscript
      with its own ``__getitem__``, which is the ceiling back inside consumer
      code). This REPLACES the old
      class-level method inventory: ``untrusted`` now means "cannot be sealed",
      not "overrides a listed method".
    - ``routing`` -- an OrderSet result changed the source queryset's database alias or
      router hints. The comparison is performed against the same extracted state the seal
      consumes, before any reconstructed queryset is returned.
    - ``sliced`` -- when ``policy.reject_sliced`` (every surface that recomposes
      onto the sealed queryset): the query is sliced (a ``LIMIT`` / ``OFFSET``
      was taken). Django forbids reordering or refiltering a sliced query, so
      the next framework transform (a Relay ``.filter(pk=...)``, a connection
      ordering, the cascade's ``.filter(...)`` narrowing) would raise a raw
      ``TypeError`` outside the typed defect contract. The same raw ``TypeError``
      is what Django raises when it refilters a sliced ``Prefetch`` child at fetch
      time, so it is on for the walker's plain-list-relation child too. It is off
      one edge down only where something downstream answers for the slice: the
      optimizer walker's nested-connection child, whose own gate degrades a sliced
      child instead of recomposing, and a consumer's own ``Prefetch`` child.
      The connection guard rejects this shape one step earlier with a
      wire-facing ``GraphQLError``; this arm stays because the visibility
      boundary owes authors its own ``ConfigurationError``.
    - ``projection`` -- only when ``policy.require_model_rows`` (every surface
      except the cascade and the raw-list row source): the row iterable is not
      ``ModelIterable`` (a ``.values()`` / ``.values_list()`` projection whose
      rows are not model instances). The cascade runs with
      ``require_model_rows=False`` because it re-projects the sealed queryset to
      the edge's target column and never iterates it.
    - ``combined`` -- when ``policy.rewrite_combined`` (every surface except the
      raw-list row source) and the query carries a ``union()`` /
      ``intersection()`` / ``difference()`` combinator that
      ``_pk_membership_query_or_defect`` cannot rewrite to its primary-key set
      without changing its rows (``_combined_lost_property`` names the lost
      property). Every other combinator is SERVED as that set: the sealed
      queryset is ``<model>.filter(pk__in=<combined>.values("pk"))`` with the
      outer ordering re-applied, a queryset of model rows every surface can
      narrow, re-project and prefetch through, where Django refuses
      ``.filter()`` / ``.only()`` after a combinator and silently drops a
      reverse-FK ``Prefetch``'s parent predicate from one.
    - ``alias`` -- a value explicitly routed off ``required_alias``. For a
      top-level source an UNROUTED value (``_db is None``) is never an alias defect;
      the seal pins it via ``using=`` at construction. For a prefetch child
      (``policy.require_shared_alias``), the child's explicit ``_db`` must EQUAL the outer
      effective alias, including when that alias is ``None`` -- an unrouted parent
      forces an unrouted child, so one resolution never spans two connections.

    An instance-shadowed clone / evaluation method (``.all()``, ``Query.chain``,
    ``.filter()``, ``_values``, ``.first()``, ``.__aiter__()`` probes) is neutralized WITHOUT
    rejection: the seal never dispatches through the consumer object, it rebuilds a fresh
    queryset from the extracted query and clones that query through the unbound
    ``sql.Query.clone``. Clone-safety is not assumed from the outer exact-type alone:
    ``sql.Query.clone`` dispatches ``where.clone()``, container ``.copy()`` methods, and (at
    compile) ``as_sql`` on the graph, so the seal first proves via
    ``_combined_query_table_defect`` that EVERY compiler-reachable node is a genuine,
    unshadowed Django implementation and every cloned container an exact builtin -- only then
    does the clone provably dispatch trusted code alone. The clone is then CANONICALLY
    RECONSTRUCTED (``_rebuild_query_payloads``): every container and every AST node in it is
    rebuilt as a fresh framework-owned object of the same proven-genuine class, so the sealed
    query shares no mutable object with the candidate graph and a retained consumer reference
    cannot rewrite the visibility predicate between seal and compile.
    """
    # ``issubclass(type(candidate), ...)`` and never ``isinstance``: an isinstance
    # test whose first check fails falls back to the candidate's ``__class__``, which
    # is a consumer-defined property on an arbitrary object - it can claim to be a
    # QuerySet, or raise, and either way the admission test itself has dispatched
    # consumer code. The real type is the one thing the candidate cannot restate, so
    # the shape proof starts from it and a spoofed class stays the typed ``type``
    # defect every other unusable shape is.
    candidate_class = type(candidate)
    if not _is_queryset_class(candidate_class):
        return None, ("type", truth.kind(candidate))
    state: dict[str, object] = truth.instance_state(candidate)
    query = state.get("_query")
    qmodel = state.get("model")
    iterable = state.get("_iterable_class")
    # A model class always carries its concrete model (``ModelBase`` sets it); django-stubs
    # types the attribute by ``Options``' pre-class ``None`` default.
    concrete = cast("type[models.Model]", model._meta.concrete_model)
    cls_name = truth.kind(candidate)
    if not _is_model_of_concrete(qmodel, concrete):
        return None, ("table", truth.name(qmodel))
    # The outer exact-type check must precede the table walk AND the deferred-filter
    # resolution below: the walk reads ``query.model`` / ``query.alias_map`` /
    # ``query.combined_queries`` through normal attribute access, which on a foreign
    # ``Query`` SUBCLASS could dispatch a consumer property during validation. Only a
    # proven-genuine ``sql.Query`` is walked (the walk itself type-checks each branch
    # before recursing into it, extending the same discipline down the combinator tree).
    if type(query) is not sql.Query:
        return None, ("untrusted", f"{cls_name}.query is {truth.kind(query)}")
    # Pin every retained ``QuerySet`` state field (``_db`` / ``_hints`` / ``_fields`` /
    # ``_sticky_filter`` / ``_for_write`` / ``_fetch_mode``) to its exact shape BEFORE any truthiness /
    # comparison / copy runs on it, so a consumer ``__bool__`` / ``__eq__`` / ``__iter__``
    # cannot dispatch mid-seal (spec-045 Decision 1).
    state_defect = _queryset_state_defect(state, cls_name)
    if state_defect is not None:
        return None, state_defect
    # ``_db`` is proven ``None`` or a ``str`` above; every later read takes its exact text.
    db = _normalized_db(state)
    if expected_routing is not None:
        original_db = expected_routing.db
        original_hints = expected_routing.hints
        candidate_db = db
        candidate_hints = state.get("_hints")
        if candidate_db != original_db or not _routing_hints_equal(
            candidate_hints,
            original_hints,
        ):
            return None, (
                "routing",
                (
                    f"expected db={_routing_repr(original_db)}, "
                    f"hints={_routing_repr(original_hints)}, got "
                    f"db={_routing_repr(candidate_db)}, "
                    f"hints={_routing_repr(candidate_hints)}"
                ),
            )
    # Validate the candidate's ENTIRE query graph BEFORE cloning it. sql.Query.clone is
    # not a no-dispatch boundary: its body calls bound methods on the source's own
    # sub-objects -- ``self.where.clone()``, ``alias_refcount.copy()`` /
    # ``annotations.copy()`` / ... on the containers, and (at compile time) ``as_sql``
    # on every embedded node -- so a consumer WhereNode / expression / container
    # SUBCLASS, or an instance-dict method shadow on an EXACT Django node, would run
    # mid-clone and strip the visibility predicate (an exact WhereNode whose
    # shadowed ``clone()`` fires leaves the sealed SQL with no WHERE).
    # ``_combined_query_table_defect`` proves every
    # compiler-reachable node is a genuine, unshadowed Django implementation and every
    # cloned container an exact builtin, so the clone below dispatches only trusted code.
    pre_clone_defect = _combined_query_table_defect(query, concrete)
    if pre_clone_defect is not None:
        return None, pre_clone_defect
    # Clone ONCE, off the proven-safe candidate, into a framework-owned detached query.
    # Every subsequent step (deferred-filter baking) mutates only this clone, never the
    # candidate -- the seal is observationally immutable, so a concurrent caller reusing
    # the same source queryset never observes a half-baked predicate, a cleared
    # ``_deferred_filter``, or partial state left after an exception mid-bake.
    rebuilt_query = sql.Query.clone(query)
    # ``clone`` is SHALLOW, so the clone still shares the candidate's mutable containers
    # AND its AST nodes -- ``where`` leaves, annotation expressions, joins, filtered
    # relations, raw-SQL parameter containers. The validated state is therefore
    # canonically reconstructed into fresh framework-owned objects, so no post-seal
    # mutation of the candidate graph can reach the sealed query before it compiles.
    reconstruction_defect = _reconstruction_defect(rebuilt_query, cls_name)
    if reconstruction_defect is not None:
        return None, reconstruction_defect
    # A pending ``_deferred_filter`` -- the ``(negate, args, kwargs)`` tuple Django's
    # ``RelatedManager._apply_rel_filters`` leaves on ``instance.rel.all()`` (baked into
    # ``_query`` only on first ``.query`` access) -- is baked onto the CLONE for EVERY
    # candidate. The related-manager machinery leaves that tuple on whatever class the
    # model's manager builds its querysets from, so the candidate's own class says
    # nothing about the state: the predicate is added to the DETACHED clone through the
    # UNBOUND ``sql.Query.add_q``, over arguments proven inert or genuine Django first,
    # and the candidate is never dispatched through and never mutated. What fails closed
    # is the pending STATE's shape rather than the class holding it.
    # ``is not None`` -- never truthiness: Django only ever stores ``None`` or the
    # 3-tuple here, and ``if deferred:`` would dispatch a consumer ``__bool__`` on an
    # arbitrary object planted in the slot, letting a
    # falsy hostile value silently skip the bake. Any non-``None`` value routes
    # through the bake path, whose exact-shape checks fail a malformed one closed.
    deferred = state.get("_deferred_filter")
    if deferred is not None:
        bake_defect = _bake_deferred_filter_or_defect(rebuilt_query, deferred, cls_name)
        if bake_defect is not None:
            return None, bake_defect
        # Re-prove the detached clone after baking: the predicate was added by unbound
        # Django machinery over arguments PRE-validated inert / genuine-Django (so no
        # consumer ``resolve_expression`` ran mid-bake), and this
        # walk re-proves the whole graph is still genuine and confined to concrete's table.
        post_bake_defect = _combined_query_table_defect(rebuilt_query, concrete)
        if post_bake_defect is not None:  # pragma: no cover - defense in depth
            # Genuinely unreachable through any validated input: every deferred-filter
            # argument is proven inert or genuine-unshadowed Django BEFORE the bake, and
            # ``sql.Query.add_q`` is Django's own machinery -- it can only assemble
            # genuine Django ``WhereNode`` / lookup / expression nodes over the base
            # concrete table, never a foreign type, a shadowed method, a non-exact
            # container, a foreign base table, or a combined branch. The re-prove is
            # kept as a belt-and-suspenders re-validation of the MUTATED clone (a
            # security-boundary invariant), but no argument the pre-bake proof admits can
            # drive this branch, so it is marked unreachable rather than surfaced with a
            # synthetic test that would have to bypass the pre-bake proof.
            return None, post_bake_defect
    if not _is_django_iterable_class(iterable):
        detail = truth.name(iterable)
        return None, ("untrusted", f"{cls_name}._iterable_class is {detail}")
    # The outer effective alias is what this seal pins the queryset onto (a required
    # alias, else the source's own explicit ``_db``); prefetch children are sealed
    # against it with ``require_shared_alias`` so neither a pinned parent nor an
    # UNROUTED parent (effective alias ``None``) can hold an explicitly cross-routed
    # child -- one GraphQL resolution never spans two database connections.
    effective_alias = required_alias if required_alias is not None else db
    sealed_prefetch, prefetch_defect = _sealed_prefetch_related_lookups(
        state.get("_prefetch_related_lookups"),
        cls_name,
        effective_alias,
        qmodel,
    )
    if prefetch_defect is not None:
        return None, prefetch_defect
    result_cache = state.get("_result_cache")
    if policy.carry_result_cache and result_cache is not None and type(result_cache) is not list:
        # ``type(...) is list``, never ``isinstance``: a ``list`` SUBCLASS brings its
        # own ``__getitem__``, and ``QuerySet.__getitem__`` returns
        # ``self._result_cache[k]`` once the cache is populated - so carrying a
        # subclass would put the raw-list ceiling back inside consumer code, which is
        # the one thing this seam exists to prevent. Django stores an exact ``list``
        # here and nothing else, so refusing every other shape fails closed on state
        # Django does not produce.
        return None, ("untrusted", f"{cls_name}._result_cache is a {truth.kind(result_cache)}")
    if policy.require_unevaluated and result_cache is not None:
        return None, ("evaluated", "the result cache is populated")
    if policy.reject_sliced and rebuilt_query.is_sliced:
        return None, ("sliced", f"rows {rebuilt_query.low_mark}:{rebuilt_query.high_mark}")
    if policy.require_model_rows and iterable is not ModelIterable:
        return None, ("projection", truth.name(iterable))
    # ``_fields`` is proven ``None`` or an exact ``tuple`` of ``str`` names by
    # ``_queryset_state_defect``, and is carried forward as exact text.
    fields = _normalized_fields(state)
    # ``combinator`` is a plain ``str | None`` slot on the proven-genuine
    # ``sql.Query``, read off the reconstructed clone -- no consumer dispatch. A
    # combined result is served as the set of primary keys it selects: the
    # recomposing surfaces narrow, project and prefetch through the sealed
    # queryset, none of which Django supports on a combinator, so the combinator
    # becomes the right-hand side of a ``pk__in`` membership test on a fresh
    # single-table query of model rows. It runs after the projection check, so a
    # ``.values()`` combinator a model-row surface refuses is never turned into
    # model rows. A shape whose rows that rewrite would change fails closed.
    if policy.rewrite_combined and rebuilt_query.combinator:
        rewritten, combined_defect = _pk_membership_query_or_defect(rebuilt_query, qmodel)
        if combined_defect is None:
            # The rewrite builds a fresh ``Query(model)``, which bakes ``Meta.db_table``
            # as given (a ``TextChoices`` / ``StrEnum`` member included) into its alias
            # map, so the rewritten query is canonically reconstructed in turn.
            combined_defect = _reconstruction_defect(rewritten, cls_name)
        if combined_defect is not None:
            return None, combined_defect
        # The rewrite returns a query exactly when it returns no defect.
        rebuilt_query = cast("sql.Query", rewritten)
        iterable = ModelIterable
        fields = None
    if policy.require_shared_alias:
        # A prefetch child: its explicit ``_db`` must EQUAL the outer effective alias,
        # INCLUDING when that alias is ``None`` (an unrouted parent forces an unrouted
        # child). ``required_alias`` here IS the outer effective alias.
        if db is not None and db != required_alias:
            return None, ("alias", str(db))
    elif required_alias is not None and db is not None and db != required_alias:
        return None, ("alias", str(db))
    using = required_alias if required_alias is not None else db
    queryset_class: type[models.QuerySet[models.Model, object]] = (
        candidate_class if keep_class else models.QuerySet
    )
    # Every slot is read without dispatch and proven exact-shape by
    # ``_queryset_state_defect`` (``_hints`` ``None`` or an exact ``dict`` with ``str``
    # keys, so the copy dispatches no consumer ``__iter__`` / ``keys``). The fetch mode
    # is Django 6.1's, proved one of Django's own when present; absent below 6.1, where
    # the rebuilt queryset has none either.
    sealed = _built_queryset(
        queryset_class,
        model=qmodel,
        query=rebuilt_query,
        using=using,
        hints=state.get("_hints"),
        iterable=iterable,
        fields=fields,
        fetch_mode=state.get("_fetch_mode"),
        # The prefetch seal returns lookups exactly when it returns no defect.
        prefetch_lookups=cast("tuple[str | _SealedPrefetch, ...]", sealed_prefetch),
        sticky_filter=state.get("_sticky_filter") is True,
        for_write=state.get("_for_write") is True,
    )
    if policy.carry_result_cache:
        # The rows the source already fetched travel onto the rebuild, so a surface
        # that only windows them re-queries nothing. The list object is taken as it
        # is rather than copied: the row objects are shared either way, ``QuerySet``
        # hands its own cache out uncopied at every other read of it, and an O(n)
        # copy here would be a per-parent-row cost on the relation branch the carry
        # exists to make cheap. Every other policy leaves the ``None`` that
        # ``models.QuerySet.__init__`` already set. Under this policy the check above
        # refused every populated cache that is not an exact ``list``.
        sealed._result_cache = cast("list[object] | None", result_cache)
    return sealed, None


def _built_queryset(
    queryset_class: type[_QuerySetT],
    *,
    model: type[models.Model],
    query: sql.Query,
    using: str | None,
    hints: object,
    iterable: type[BaseIterable[object]],
    fields: tuple[str, ...] | None,
    fetch_mode: object,
    prefetch_lookups: tuple[str | Prefetch[str], ...],
    sticky_filter: bool,
    for_write: bool,
) -> _QuerySetT:
    """Construct ``queryset_class`` over ``query`` the way ``QuerySet._clone`` constructs one.

    The one constructor path a framework-built queryset takes: the ``model`` / ``query``
    / ``using`` / ``hints`` constructor arguments (``hints`` copied into a fresh dict,
    never shared: the source could otherwise keep writing to a routing-control surface a
    custom router consults on an unrouted read), then exactly the state ``_clone`` copies
    forward MINUS ``_known_related_objects`` (an optional related-object cache dropped on
    purpose: a fresh fetch is always correct, whereas a copied cache could pre-seed
    related instances that bypass the related type's own visibility hook). A
    ``fetch_mode`` that is not one of Django's own is not carried. Attributes a class
    sets on an instance outside the constructor arguments are not carried either.
    ``query`` is used as given, so a caller hands over a query no other queryset will
    mutate.
    """
    built = queryset_class(
        model=model,
        query=query,
        using=using,
        # Every caller hands over ``None`` or an exact ``dict`` with ``str`` keys (the
        # seal proves it; the cascade's restatement reads the dict a seal wrote);
        # django-stubs types hint values as the model instances Django itself writes.
        hints=dict(cast("dict[str, models.Model]", hints)) if hints is not None else {},
    )
    built._iterable_class = iterable
    set_queryset_fields(built, fields)
    if is_django_fetch_mode(fetch_mode):
        set_queryset_fetch_mode(built, fetch_mode)
    set_queryset_prefetch_lookups(built, prefetch_lookups)
    set_queryset_sticky_filter(built, sticky=sticky_filter)
    set_queryset_for_write(built, for_write=for_write)
    return built


def _restated_as_source_class(
    narrowed: models.QuerySet[models.Model, object],
    source_class: type[_QuerySetT],
) -> _QuerySetT:
    """Hand a framework-built queryset back as an instance of ``source_class``.

    ``permissions.py::apply_cascade_permissions`` seals its source plain and narrows that
    plain rebuild, so no consumer ``filter`` override ever sees the cascade predicate;
    it then returns the narrowed state as the caller's own class through this
    restatement, so a project method chains after the cascade. ``narrowed`` is the
    cascade's own object, read by attribute and then dropped, so its ``query`` travels
    without a second clone and no SQL runs. A ``narrowed`` already of exactly
    ``source_class`` (a plain source) is returned as is.
    """
    if truth.is_exact(narrowed, source_class):
        return narrowed
    state = truth.instance_state(narrowed)
    return _built_queryset(
        source_class,
        model=narrowed.model,
        query=narrowed.query,
        using=queryset_db(narrowed),
        hints=state.get("_hints"),
        iterable=narrowed._iterable_class,
        fields=queryset_fields(narrowed),
        fetch_mode=queryset_fetch_mode(narrowed),
        prefetch_lookups=queryset_prefetch_lookups(narrowed),
        sticky_filter=state.get("_sticky_filter") is True,
        for_write=state.get("_for_write") is True,
    )


def _row_source_model(state: Mapping[str, object], origin: str) -> type[models.Model]:
    """Return the model a candidate row source declares, proven to be a model class.

    ``_seal_or_defect`` reaches ``model._meta.concrete_model`` on its first line,
    so the model it is given has to be a real model class before the call, not
    after it: a raw-list source is not validated against a registered type's
    table, so the model IT declares is the only one available, and that slot
    holds whatever the candidate's instance dictionary holds.

    ``truth.is_subclass`` asks whether ``model`` IS a model class from its real
    metaclass chain and MRO, without letting a ``__class__`` property answer.
    """
    model = state.get("model")
    if not truth.is_subclass(model, models.Model):
        raise ConfigurationError(
            f"{_sentence_start(origin)} a QuerySet subclass whose model is "
            f"{truth.kind(model)}; the row bound rebuilds a framework-owned "
            "queryset from that state and cannot do so without a model class.",
        )
    return model


def normalized_row_source(
    value: _T,
    *,
    origin: str = "a collection resolver returned",
) -> _T | models.QuerySet[models.Model, object]:
    """Return a row source whose slice is an operation this package owns.

    The raw-list ceiling is applied by slicing, because slicing a queryset is
    what carries the bound into SQL as ``LIMIT``. That only bounds anything if
    the package owns what the slice DOES. On an exact ``models.QuerySet`` it
    does: ``QuerySet.__getitem__`` is Django's, it sets ``low_mark`` /
    ``high_mark`` on the query, and the database returns no more rows than it
    was asked for. On a SUBCLASS the same expression is consumer code, free to
    ignore the slice and answer with every row - which turns the one thing
    standing between a client and the whole table into a call the client's own
    object decides the result of.

    So the shape is read from ``type(value)``, never through an ``isinstance``
    test a ``__class__`` property can answer, and:

    - an exact ``models.QuerySet`` is returned unchanged. It is the common case
      by an enormous margin (every framework-built queryset and every default
      manager's ``.all()``), and it already is what this seam exists to produce,
      so it pays nothing - no rebuild per parent row, no N+1 validation cost;
    - a ``QuerySet`` SUBCLASS is untrusted execution state and is rebuilt into a
      plain framework-owned queryset through the same seal every visibility
      boundary runs, which preserves its model, query graph, routing, row
      iterable and prefetch state. A sealable project subclass therefore keeps
      its ``LIMIT`` in SQL instead of being demoted to a counted Python
      truncation; one whose state cannot be faithfully rebuilt fails closed with
      a typed ``ConfigurationError``, and never by falling back to its own
      ``__getitem__``;
    - anything else is returned unchanged for the caller's counting path, which
      bounds by building a list of its own and needs no ownership of the source.

    The rebuild brings the source's fetched rows with it, so a subclass that
    arrives evaluated is windowed from the rows it holds and costs no query the
    exact shape would not have cost either. What the rebuild drops is the
    subclass's own methods.

    ``origin`` names where the value came from in every refusal, completing
    "<origin> a <type>": a relation resolver reading Django's prefetch cache
    passes its own, so the message points at the prefetch rather than at a
    resolver the consumer never wrote.
    """
    source_type = type(value)
    if source_type is models.QuerySet or not truth.is_subclass(source_type, models.QuerySet):
        return value
    model = _row_source_model(_readable_queryset_state(value), origin)
    sealed, defect = _seal_or_defect(value, model, None, _RAW_LIST_SOURCE_POLICY)
    if defect is not None:
        raise ConfigurationError(
            _raw_list_source_message(defect, truth.kind(value), origin),
        )
    # ``_seal_or_defect`` returns a queryset exactly when it returns no defect.
    return cast("models.QuerySet[models.Model, object]", sealed)


def materialized_rows(value: object) -> list[object] | None:
    """Return the rows a row source has already fetched, or ``None`` when it has none.

    Django's prefetch cache holds a queryset whose ``_result_cache`` is the list
    of rows it fetched, and returning that list directly is what lets a
    prefetched relation skip a clone and a copy per parent row. The read is
    taken out of the instance dictionary of an EXACT queryset, so it is the
    package reading Django's own slot rather than a ``getattr`` dispatching
    whatever a consumer subclass defines - the same object whose ``__getitem__``
    cannot be trusted with the bound cannot be trusted to answer what it has
    already fetched. Every other shape answers ``None`` and is bounded as the
    source it is - which is the reason the exact-type rule is correct rather than
    a claim that a subclass has no rows to give: a subclass answers nothing HERE
    because its ``__dict__`` is not Django's own slot on a package-owned object,
    and the rows it does hold reach a caller through ``normalized_row_source``'s
    rebuild, which carries them onto a queryset this package built.
    """
    if not _is_exact_queryset(value):
        return None
    # An exact ``QuerySet``'s ``_result_cache`` slot: its fetched rows, or ``None``.
    return cast("list[object] | None", _readable_queryset_state(value).get("_result_cache"))


def _is_exact_queryset(value: object) -> TypeGuard[models.QuerySet[models.Model, object]]:
    """Return whether ``value`` is EXACTLY Django's ``QuerySet`` (never a subclass)."""
    return type(value) is models.QuerySet


def _readable_queryset_state(value: object) -> dict[str, object]:
    """Return the real instance dictionary of ``value``, read without dispatching consumer code.

    ``truth.instance_dict`` is the only read here for the reason the seal gives:
    neither a custom ``__getattribute__`` nor a subclass that redefines
    ``__dict__`` itself can run code or return a lie during extraction. Every
    ``QuerySet`` instance carries the genuine slot Django's base class declares.
    """
    # Every caller hands in a ``QuerySet`` instance, which always carries the genuine
    # ``__dict__`` slot.
    return truth.instance_state(value)


def _sentence_start(phrase: str) -> str:
    """``phrase`` with its first letter capitalized, the rest untouched."""
    return phrase[:1].upper() + phrase[1:]


# What an ``untrusted`` refusal tells the consumer, shared by every surface that
# renders one: each surface prefixes its own subject and the defect detail, and the
# cause list and advice stay one text so no surface names fewer causes than the seal
# refuses.
_UNSEALABLE_STATE_CAUSES = (
    "the seal rebuilds only state made of Django's own objects, so it refuses a Query "
    "subclass; a consumer-defined expression, lookup, where-node or join class; a method "
    "assigned onto a query or node instance; a non-builtin value where Django stores a "
    "builtin; a foreign row iterable; a fetch mode other than Django's FETCH_ONE, "
    "FETCH_PEERS or FETCH_RAISE; a Prefetch it cannot rebuild; or deferred-filter "
    "state Django never writes. Build the queryset with Django's own query, expression "
    "and lookup classes, and do not assign to its internals."
)
# What a ``combined`` refusal tells the consumer, shared by every surface that renders
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


def _raw_list_source_message(defect: tuple[str, str], name: str, origin: str) -> str:
    """Return the wording for a row source the raw-list bound could not take ownership of.

    Only the defects ``_RAW_LIST_SOURCE_POLICY`` can actually reach have arms:
    ``evaluated``, ``sliced``, ``combined`` and ``projection`` are switched off
    by that policy, and ``routing`` / ``alias`` need an expectation this surface
    never states. A code added to the seal without an arm here renders as the
    framework defect it is rather than as one of these.
    """
    lead = _sentence_start(origin)
    return _defect_message(
        {
            "type": (
                f"{lead} a {name}, which the raw-list row "
                "bound cannot slice; the bound is applied by slicing a queryset."
            ),
            "table": (
                f"{lead} a {name} whose query is over a "
                f"different table than its own model declares ({defect[1]}), so the "
                "row bound cannot rebuild it into a framework-owned queryset."
            ),
            "untrusted": (
                f"{lead} a {name} that cannot be sealed into "
                f"a framework-owned execution queryset ({defect[1]}), so the raw-list "
                "row bound has nothing it owns the slice of. Slicing the subclass "
                "itself would let the object being bounded decide how many rows the "
                f"bound returns. {_sentence_start(_UNSEALABLE_STATE_CAUSES)} The "
                "raw-list bound also refuses a result cache that is not an exact list."
            ),
        },
        defect,
        f"The {name} {origin}",
    )


def _coerced_manager_queryset(
    manager: models.Manager[models.Model],
) -> models.QuerySet[models.Model]:
    """Coerce a ``Manager`` to its ``QuerySet``, preserving its explicit alias or failing closed.

    ``Manager.all()`` is consumer-overridable. A custom Manager can degrade it
    into a plain list / generator (which would otherwise be mistaken for the
    deliberate plain-iterable bypass and skip the visibility hook) or silently
    change the database it routes to (an explicitly ``.using("chosen")`` manager
    whose ``.all()`` returns rows on ``"elsewhere"``, or an unrouted manager that
    self-routes before the boundary's required-alias step runs). Both are
    cross-database / bypass leaks, so the coercion result must be a real
    ``QuerySet`` whose ``_db`` EXACTLY preserves the manager's explicit routing
    (an unrouted manager must stay unrouted until the required-alias resolution
    pins it). The returned queryset still flows through the full source /
    result validation (concrete table, actual base table, trust, alias); this
    helper only closes the Manager-coercion-specific holes. ``all()`` is the
    Manager's own code: whatever it raises propagates.
    """
    explicit = truth.instance_state(manager).get("_db")
    queryset = manager.all()
    if not truth.is_instance(queryset, models.QuerySet):
        raise ConfigurationError(
            f"A {truth.kind(manager)}.all() coercion must produce a QuerySet, but "
            f"returned {truth.kind(queryset)}; a Manager that degrades into a list "
            f"or other non-queryset cannot enter the visibility boundary and must not "
            f"be treated as the deliberate plain-iterable bypass.",
        )
    routed = queryset_db(queryset)
    if routed != explicit:
        raise ConfigurationError(
            f"A {truth.kind(manager)} pinned to alias {explicit!r} produced a "
            f"queryset routed to {routed!r} on .all(); a Manager coercion must "
            f"preserve the manager's explicit routing exactly (an unrouted manager "
            f"must stay unrouted until the resolution's required alias pins it), so a "
            f"visibility source or hook cannot silently change databases.",
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
    exhaustiveness, plus the two clause texts no surface respells -- the
    untrusted cause list (``_UNSEALABLE_STATE_CAUSES``) and the
    combined-queryset contract (``_COMBINED_WHAT``) -- each composed under the
    site's own subject.
    """
    code, detail = defect
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
    name = truth.name(type_cls)
    model_name = truth.name(model)
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
                "untrusted": (
                    f"{name}.get_queryset returned a queryset that cannot be sealed "
                    f"into a framework-owned execution queryset ({detail}); "
                    f"{_UNSEALABLE_STATE_CAUSES}"
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
    queryset: models.QuerySet[_ModelT, _RowT],
    *,
    model: type[models.Model] | None = ...,
    render_error: Callable[[str, str], str] | None = ...,
    policy: _SealPolicy[object] = ...,
    keep_class: bool = ...,
) -> tuple[models.QuerySet[_ModelT, _RowT], str | None]: ...
@overload
def _prepared_visibility_source(
    type_cls: type[DjangoType],
    queryset: object,
    *,
    model: type[models.Model] | None = ...,
    render_error: Callable[[str, str], str] | None = ...,
    policy: _SealPolicy[object] = ...,
    keep_class: bool = ...,
) -> tuple[models.QuerySet[models.Model, object], str | None]: ...
def _prepared_visibility_source(
    type_cls: type[DjangoType],
    queryset: object,
    *,
    model: type[models.Model] | None = None,
    render_error: Callable[[str, str], str] | None = None,
    policy: _SealPolicy[object] = _DEFAULT_SEAL_POLICY,
    keep_class: bool = False,
) -> tuple[models.QuerySet[models.Model, object], str | None]:
    """Validate and SEAL the source queryset before the visibility hook runs.

    Returns ``(sealed_queryset, required_alias)``. The source is sealed through
    ``_seal_or_defect`` before the hook runs - it must be a real ``QuerySet``
    over the registered type's concrete table, sealable (a plain ``sql.Query``, a
    Django row iterable, a pending deferred filter in the exact shape Django
    writes), and whatever else
    ``policy`` (a ``_SealPolicy``, default ``_DEFAULT_SEAL_POLICY``) requires:
    model rows and no slice (the cascade admits a projection), with a
    combinator served as its primary-key set. The
    sealed object is a fresh framework-owned ``QuerySet`` rebuilt from the
    source's query state, so the hook never receives the caller's object, only
    state rebuilt from it. It is a plain ``QuerySet`` by default; ``keep_class``
    rebuilds it as the source's own class instead (``_seal_or_defect``), which the
    visibility runners ask for so a hook can call its project ``QuerySet``
    methods, and which the cascade, recomposing onto the sealed source, leaves off
    and then restates its narrowed result as the source's class
    (``_restated_as_source_class``).
    An already-evaluated source seals to a fresh, unevaluated queryset (this
    seal's policies do not carry ``_result_cache`` forward), so cached rows never
    reach the hook. The required alias is then
    resolved in priority order:

    1. An active write pipeline's alias - the sealed source is pinned through
       ``pin_write_queryset`` (a ``.using()`` on the rebuilt source),
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

    A source typed ``QuerySet[M, R]`` seals to ``QuerySet[M, R]`` (the first
    overload): ``_seal_or_defect`` rebuilds over the source's own ``model``
    class (a proxy stays that proxy) with its own Django row iterable, and its
    combinator rewrite yields model rows only from a model-row combinator (a
    projected one fails closed with the ``combined`` defect), so neither the
    model nor the row type changes. Only the trusted rebuild of an untyped
    ``object`` source is typed ``QuerySet[Model, object]``.
    """
    model = _captured_model(type_cls, model)
    candidate, defect = _seal_or_defect(queryset, model, None, policy, keep_class=keep_class)
    if defect is not None:
        code, detail = defect
        if render_error is not None:
            raise ConfigurationError(render_error(code, detail))
        name = truth.name(type_cls)
        model_name = truth.name(model)
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
                    "untrusted": (
                        f"apply_type_visibility for {name} got a source queryset "
                        f"that cannot be sealed into a framework-owned execution queryset "
                        f"({detail}); {_UNSEALABLE_STATE_CAUSES}"
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
                },
                defect,
                f"The apply_type_visibility source for {name}",
            ),
        )
    # ``_seal_or_defect`` returns a queryset exactly when it returns no defect.
    sealed = cast("models.QuerySet[models.Model, object]", candidate)
    pipeline = current_write_pipeline()
    if pipeline is not None:
        sealed = pin_write_queryset(
            sealed,
            pipeline.alias,
            owner=f"The {truth.name(type_cls)} visibility source",
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
    then SEALED through ``_seal_or_defect``, so anything that is not a sealable
    ``QuerySet`` of the registered type's model rows (``None``, lists,
    generators, async generators, custom iterables, unrelated / MTI-child
    models, cross-model unions, base-table spoofs, foreign Query classes,
    ``.values()`` projections on non-cascade surfaces) fails closed. The return
    value is a fresh framework-owned plain ``QuerySet`` rebuilt from the hook
    result's validated query state - never the consumer object - so an
    instance-shadowed ``.all()`` / ``.filter()`` / ``.first()`` / ``.__aiter__()``
    or a replaced ``Query.chain`` cannot erase the predicate or synthesize rows
    after this point.

    Alias handling is done at construction: the seal passes
    ``using=required_alias`` when an alias is required (an unpinned result is
    pinned onto it, an explicitly matching one is preserved, an explicitly
    divergent one fails closed with the ``alias`` defect); with no required
    alias the hook's own ``_db`` is preserved. There is no post-seal ``.using()``
    repin or ``.all()`` refresh - the sealed queryset is fresh and correctly
    routed by construction. Normalization composes lazy query state only -
    filters, annotations, ordering, and values projection pass through unchanged
    (but subclass identity is deliberately dropped) - and executes zero SQL.

    ``model`` is the caller's captured model (``_captured_model``), the SAME
    value ``_prepared_visibility_source`` took for this call: the source seal
    and the result seal of one resolution validate against one model, never two
    answers to two reads.
    """
    model = _captured_model(type_cls, model)
    if isinstance(result, models.Manager):
        result = _coerced_manager_queryset(result)
    sealed, defect = _seal_or_defect(result, model, required_alias, policy)
    if defect is not None:
        raise _visibility_result_error(type_cls, model, required_alias, defect, render_error)
    # ``_seal_or_defect`` returns a queryset exactly when it returns no defect.
    return cast("models.QuerySet[models.Model, object]", sealed)


@overload
def apply_type_visibility_sync(
    type_cls: type[DjangoType],
    queryset: models.QuerySet[models.Model, object],
    info: object,
    async_recourse: str = ...,
    *,
    model: type[models.Model] | None = ...,
    render_error: Callable[[str, str], str] | None = ...,
) -> models.QuerySet[models.Model]: ...
@overload
def apply_type_visibility_sync(
    type_cls: type[DjangoType],
    queryset: models.QuerySet[models.Model, object],
    info: object,
    async_recourse: str = ...,
    *,
    model: type[models.Model] | None = ...,
    render_error: Callable[[str, str], str] | None = ...,
    policy: _SealPolicy[_RowT],
) -> models.QuerySet[models.Model, _RowT]: ...
def apply_type_visibility_sync(
    type_cls: type[DjangoType],
    queryset: models.QuerySet[models.Model, object],
    info: object,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
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
    the source and the hook result are each SEALED into a fresh framework-owned
    ``QuerySet`` rebuilt from validated query state (shape, concrete +
    actual-base table, sealability, model-row, alias) - the source as an instance
    of its own class, so the hook can call project ``QuerySet`` methods, the
    result as a plain ``QuerySet`` - with required-alias
    resolution (write pipeline > explicit source ``.using`` > none), Manager
    coercion with alias preservation, and fail-closed rejection of every
    non-sealable shape. ``SyncMisuseError`` stays reserved for this sync
    boundary; every other defect is a plain ``ConfigurationError``.

    ``async_recourse`` is the surface-specific guidance appended to the
    error. It defaults to the Relay node-defaults wording; callers whose
    recourse differs pass their own (the cascade, for instance, has no
    async-native walk -- its twin wraps this same sync walk -- so it tells
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
        keep_class=True,
    )
    result = type_cls.get_queryset(queryset, info)
    result = reject_async_in_sync_context(
        result,
        owner=truth.name(type_cls),
        method="get_queryset",
        context="resolver",
        recourse=async_recourse,
    )
    # No identity fast path: ``result is queryset`` proves object identity, not
    # immutability. A hook that held the sealed source can mutate ``_result_cache``
    # / ``_query`` / ``model`` / ``_db`` and return the SAME object, so the result
    # is ALWAYS re-sealed -- the second seal is the point that drops any injected
    # result cache and re-validates post-hook state (spec-045 Decision 3).
    return _normalized_visibility_result(
        type_cls,
        result,
        required_alias,
        render_error,
        model=model,
        policy=policy,
    )


def visibility_scoped_related_queryset(
    related_type: type[DjangoType],
    info: object,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> models.QuerySet[models.Model]:
    """Return a related type's base queryset scoped by its ``get_queryset`` visibility hook.

    The one-line composition of the two primitives every relation-visibility check
    shares - ``apply_type_visibility_sync(related_type, initial_queryset(
    related_type), info, recourse)``. Single-sourced so the model relation decode
    (``mutations/resolvers.py``) and the form relation decode
    (``forms/resolvers.py``) provably apply the SAME related-type ``get_queryset``
    (the cross-flavor security invariant spec-038 claims), rather than re-spelling
    the composition at each site. ``async_recourse`` stays a parameter: the model
    and form paths pass their own surface-specific wording.
    """
    return apply_type_visibility_sync(
        related_type,
        initial_queryset(related_type),
        info,
        async_recourse,
    )


def related_visibility_queryset(
    related_model: type[models.Model],
    info: object,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
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
    written once (spec-039). An ``async def get_queryset`` met here raises
    ``SyncMisuseError`` (inherited from ``apply_type_visibility_sync``).
    """
    related_type = registry.get(related_model)
    if related_type is None:
        return None
    return visibility_scoped_related_queryset(related_type, info, async_recourse)


def related_visibility_queryset_or_default(
    related_model: type[models.Model],
    info: object,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> models.QuerySet[models.Model]:
    """Return the visibility-scoped queryset, falling back to the default manager.

    The "no primary ``DjangoType`` => default-manager, no visibility contract"
    fallback ``visible_related_object`` and ``visible_related_objects`` both
    opened with - a security-adjacent rule, now single-bodied: a related model
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


def _stringified(pks: Iterable[object]) -> set[str]:
    """Stringify a pk collection into the type-agnostic comparison basis.

    The ``{str(pk) for pk in ...}`` coercion both membership helpers share, so
    the comparison basis (an int pk and its ``"3"`` string form compare equal -
    the GlobalID-in-filter string-explosion class) has exactly one body.
    """
    return {str(pk) for pk in pks}


def stringified_pks_present(
    queryset: models.QuerySet[models.Model],
    query_pks: Iterable[object],
    key_attname: str | None = None,
) -> dict[str, object]:
    """Map each pk among ``query_pks`` present in ``queryset``, stringified, to its key (one query).

    The ``queryset.filter(pk__in=...)`` lookup the relation membership checks share
    (spec-039): the model ``utils/write_values.py::decode_visible_relation_ids`` and the
    serializer ``visible_related_objects`` both build this present-map in one query,
    keyed by each pk stringified for a type-agnostic membership compare (an int pk and
    its ``"3"`` string form compare equal; the keys are the present set). Single-sites
    the query + the str-coercion so the no-existence-leak comparison basis cannot
    drift.

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
    surfaces run with no pipeline context and are byte-unchanged.
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
    return _keys_by_str_pk(rows)


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


def _keys_by_str_pk(rows: Iterable[tuple[object, object]]) -> dict[str, object]:
    """Index each row's key by its ``str``-formed ``pk``."""
    return {str(pk): key for pk, key in rows}


def pks_all_present(declared_pks: Iterable[object], present: AbstractSet[str]) -> bool:
    """Return whether every ``declared_pks`` member (stringified) is in ``present`` (spec-039).

    The subset-membership test the model relation guard
    (``utils/write_values.py::decode_visible_relation_ids``) and the serializer M2M
    decoder (``rest_framework/resolvers.py::_decode_relation_multi``) share: a
    ``declared`` set is fully present iff its stringified members are a subset of the
    ``present`` set (typically the keys of ``stringified_pks_present``'s map). A
    missing / hidden member fails the subset check, which each caller maps to the
    uniform field-keyed relation error - the same no-existence-leak outcome.
    """
    return _stringified(declared_pks) <= present


def visible_related_object(
    related_model: type[models.Model],
    pk: object,
    info: object,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
    key_attname: str | None = None,
) -> models.Model | None:
    """Resolve the VISIBLE related object by pk through the related primary's ``get_queryset``.

    The object-returning visibility-on-every-branch query, single-sited so the
    form AND serializer relation decoders share ONE implementation rather than
    forking a second object-returning decoder. Resolves the related model's primary
    ``DjangoType`` via the registry and runs the SAME visibility hook every read
    surface applies (``visibility_scoped_related_queryset`` =
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
    manager (no visibility contract to apply). ``async_recourse`` stays a parameter:
    the form and serializer paths pass their own surface-specific wording, matching
    ``visibility_scoped_related_queryset``.

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
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
    key_attname: str | None = None,
) -> dict[str, object]:
    """Map the VISIBLE pks among ``pks`` to their stored keys in ONE visibility-scoped query.

    The BATCHED counterpart to ``visible_related_object``: instead of one visibility query per
    id (the per-element multi-relation decode), decode/type-check all ids first, then confirm
    the whole set's visibility in ONE ``pk__in`` query through the related primary
    ``DjangoType.get_queryset`` (or the target's default manager when no primary is registered -
    no visibility contract). Returns ``stringified_pks_present``'s map: the pks actually visible
    (stringified for a type-agnostic membership compare) to the value a relation keyed by
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
    return stringified_pks_present(queryset, pks, key_attname)


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
    its coroutine awaited before the caller's tail runs - the Decision 9 contract
    that an earlier implementation broke (it called the hook synchronously then
    invoked ``.filter`` on a coroutine) - and a synchronous hook that returns an
    awaitable has it awaited here after its worker returns.

    The hook is invoked once and AT MOST ONE returned awaitable is awaited;
    a second-level awaitable after that await is malformed (an ``async def``
    returning another coroutine / future) and fails closed - never a
    recursive await over an unbounded chain. The source and result then run
    the same shared hardened boundary as the sync runner (the hook's input keeps
    the source's own class, its result is sealed plain)
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
        keep_class=True,
    )
    hook = type_cls.get_queryset
    # A synchronous hook runs in ONE thread-sensitive worker, never on the event
    # loop: it may read the database (``user.has_perm``, an ``.exists()``, a
    # cascade walk), which Django refuses on the loop thread. Only the identity
    # default, stamped at class creation (``DjangoType.has_custom_get_queryset``),
    # is known to do no I/O and runs inline; an ``async def`` hook is called here
    # and awaited on the loop.
    identity = truth.static_attr(type_cls, "_is_default_get_queryset", default=False)
    result: object = (
        hook(queryset, info)
        if identity is True or is_async_callable(hook)
        else await run_in_one_sync_boundary(hook, queryset, info)
    )
    if is_awaitable(result):
        result = await result
        if _disposed_awaitable(result):
            raise ConfigurationError(
                f"{truth.name(type_cls)}.get_queryset resolved to a nested awaitable; an "
                f"async get_queryset must resolve to a QuerySet (or Manager) after ONE "
                f"await, and an unbounded awaitable chain is never consumed.",
            )
    # No identity fast path -- same contract as the sync runner: object identity
    # is not immutability, so a hook can mutate the sealed source's
    # ``_result_cache`` / ``_query`` and return it. The result is ALWAYS re-sealed
    # so the second seal drops any injected cache (spec-045 Decision 3).
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
        f"A sync {truth.name(type_cls)} consumer resolver returned an awaitable. "
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
        f"An async {truth.name(type_cls)} consumer resolver resolved to another "
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
