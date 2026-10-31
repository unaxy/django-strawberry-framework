"""``DjangoListField`` - non-Relay ``list[T]`` field for root Query fields.

Spec: ``docs/SPECS/spec-020-list_field-0_0_7.md``.
Extension spec: ``docs/SPECS/spec-050-list_field_arguments-0_0_15.md``.
"""

from __future__ import annotations

import contextlib
import inspect
from dataclasses import dataclass
from types import GenericAlias
from typing import TYPE_CHECKING, Literal, TypeVar, cast, get_args

import strawberry
from django.core.exceptions import FieldError
from django.db import connections, models
from django.db.models import aggregates, sql
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import (
    BaseExpression,
    Case,
    Col,
    Combinable,
    CombinedExpression,
    DurationExpression,
    ExpressionList,
    ExpressionWrapper,
    OrderBy,
    Star,
    TemporalSubtraction,
    When,
)
from django.db.models.fields.related_lookups import (
    RelatedExact,
    RelatedGreaterThan,
    RelatedGreaterThanOrEqual,
    RelatedIn,
    RelatedIsNull,
    RelatedLessThan,
    RelatedLessThanOrEqual,
)
from django.db.models.functions import (
    Cast,
    Coalesce,
    Concat,
    ConcatPair,
    ExtractDay,
    ExtractMonth,
    ExtractYear,
    Length,
    Lower,
    TruncDate,
    TruncMonth,
    TruncYear,
    Upper,
)
from django.db.models.lookups import (
    Exact,
    GreaterThan,
    GreaterThanOrEqual,
    In,
    IntegerFieldExact,
    IntegerGreaterThan,
    IntegerGreaterThanOrEqual,
    IntegerLessThan,
    IntegerLessThanOrEqual,
    IsNull,
    LessThan,
    LessThanOrEqual,
    Range,
    YearExact,
    YearGt,
    YearGte,
    YearLt,
    YearLte,
)
from django.db.models.options import Options
from django.db.models.sql.where import AND, OR, XOR, WhereNode
from graphql import GraphQLError
from strawberry.types import Info
from typing_extensions import override

from .exceptions import ConfigurationError, DjangoStrawberryFrameworkError
from .registry import registry
from .resource_policy import (
    _cleanup_rejected_async_iterable,
    _windowed_rows,
    _windowed_rows_async,
    effective_bound,
    policy_from_info,
    validate_collection_bound,
    validate_trusted_flag,
)
from .types import DjangoType
from .types.base import _is_relay_shaped
from .utils import truth
from .utils._narrowing import (
    is_exact_dict,
    is_list_or_tuple,
    is_set_or_frozenset,
    is_str,
    is_tuple,
    list_of,
    read_attr,
    require_instance,
)
from .utils.connections import is_supplied
from .utils.directives import validated_field_directives
from .utils.errors import coded_error_extensions
from .utils.execution_mode import async_execution, operation_is_async
from .utils.input_values import UNSET
from .utils.querysets import (
    _SQL_TEMPLATE_ATTRS,
    ORDER_FROM_MODEL_DEFAULT,
    VisibleRowExists,
    _type_is_genuinely_django,
    apply_orderset_async,
    apply_orderset_sync,
    apply_type_visibility_async,
    apply_type_visibility_sync,
    base_queryset,
    is_async_only_iterable,
    prepared_resolver_source,
    reject_async_iterable_in_sync_context,
    reject_awaitable_sync_source,
    reject_residual_async_source,
    resolve_order_name,
    selected_order,
    take_order_expansion_step,
    wrap_async_queryset_adapter,
)
from .utils.typing import is_async_callable, published_argument_wire_name

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Mapping, Sequence
    from typing import TypeAlias

    from django.db.models.sql.query import Query
    from typing_extensions import Never

    from .orders.sets import OrderSet
    from .types.definition import DjangoTypeDefinition
    from .utils.querysets import ResolvedOrderName

    #: Any model's ``Options``.
    _OptionsAny: TypeAlias = Options[models.Model]
else:
    # ``Options`` has no ``__class_getitem__`` at runtime: the hint stays the class.
    _OptionsAny = Options

__all__ = ("DjangoListField", "ListArgumentError")

_TargetT = TypeVar("_TargetT")

# Strawberry calls a resolver with at most ``(root, info)`` positionally.
_RESOLVER_POSITIONAL_INPUTS = 2

_ListArgumentReason = Literal[
    "negative",
    "non_integer",
    "order_required",
    "over_ceiling",
    "queryset_required",
]
_KNOWN_LIST_ARGUMENT_REASONS: frozenset[str] = frozenset(get_args(_ListArgumentReason))


def _validate_djangotype_target(
    target_type: object,
    resolver: object,
    *,
    field: str,
) -> DjangoTypeDefinition:
    """Run the shared DjangoType-target constructor guards for a field factory.

    Shared by ``DjangoListField``, ``DjangoConnectionField``, and the Relay node
    fields (via ``_validate_relay_djangotype_target``). ``field`` is the
    factory's public name
    (e.g. ``"DjangoListField"``) interpolated into the ``ConfigurationError``
    messages so each factory's errors name itself. These constructor-site
    checks fail at the line that wrote ``<field>(...)`` rather than at
    finalize-time.

    Order is load-bearing - each target-type check assumes the previous one
    passed. The class and subclass gates read the real metaclass chain and MRO
    (``utils/truth.py``); the registration check accepts only the target's own
    registered definition (``registry.py::TypeRegistry.registered_own_definition``),
    so a Meta-less abstract base, a class the registry dropped, and a fabricated or
    copied definition are rejected here, at the line that constructed the field, instead
    of surfacing later as a Strawberry runtime-type error over an unrelated
    model. Rejection messages render the target through ``truth.render`` /
    ``truth.name``.

    Raises ``ConfigurationError`` on failure; returns the canonical
    ``DjangoTypeDefinition`` when every guard passes, so the Relay validator
    consumes the SAME read instead of reading the attribute a second time.
    The caller runs any factory-specific guards (e.g. the connection field's
    Relay-Node guard) AFTER this returns.
    """
    if not truth.is_type(target_type):
        raise ConfigurationError(
            f"{field} requires a DjangoType class; got {truth.render(target_type)}.",
        )
    if not truth.is_subclass(target_type, DjangoType):
        raise ConfigurationError(
            f"{field} requires a DjangoType subclass; got {truth.name(target_type)}.",
        )
    definition = registry.registered_own_definition(target_type)
    if definition is None:
        raise ConfigurationError(
            f"{field} target {truth.name(target_type)} is not a registered DjangoType. "
            f"This usually means {truth.name(target_type)} declares no `class Meta` "
            "(a Meta-less abstract base never registers a definition), or its definition "
            "was replaced or cleared.",
        )
    if resolver is not None and not callable(resolver):
        raise ConfigurationError(f"{field} resolver must be callable.")
    return definition


def _validate_relay_djangotype_target(
    target_type: type[object],
    resolver: object,
    *,
    field: str,
    relay_error_message: str,
) -> DjangoTypeDefinition:
    """Run the shared DjangoType-target guards plus the Relay-Node-shaped one.

    The Relay-shaped target guard shared by ``DjangoConnectionField`` and
    ``relay.py::_validate_node_target`` (which backs ``DjangoNodeField`` /
    ``DjangoNodesField``) -- single-sited. Delegates the base checks -
    including the registry-canonicality identity check - to
    ``_validate_djangotype_target`` (with the call site's
    ``resolver`` seam), then rejects a non-Relay-Node-shaped target.
    ``_is_relay_shaped`` reads the declared ``Meta.interfaces`` (a
    Meta-declared ``relay.Node`` is in ``definition.interfaces`` before Phase
    2.5 injects it into ``__bases__``) OR direct ``relay.Node`` inheritance.
    The caller supplies the full ``relay_error_message`` so each factory keeps
    its own wording, and the same single definition read is returned onward so a
    factory can build its whole field from it without a second read.

    Reconsideration triggers: a new Relay-shape arm
    (``types/base.py::_is_relay_shaped`` owns the predicate), a
    registration-canonicality change
    (``registry.py::TypeRegistry.registered_own_definition`` owns it), or a
    guard reading ``DecodeResult`` statuses (row existence lives in the
    ``types/relay.py`` resolve defaults, relation-target existence in the
    finalizer audit - construction answers registered + shaped only).
    """
    # The definition comes back from the base validator's one read; the Relay
    # guard and the field build consume that same object.
    definition = _validate_djangotype_target(target_type, resolver, field=field)
    # The base validator proved ``definition.origin is target_type``.
    if not _is_relay_shaped(definition.origin, definition.interfaces):
        raise ConfigurationError(relay_error_message)
    return definition


# basedpyright: ``GraphQLError.__init__`` calls ``super().__init__(message)``, which reaches
# ``BaseException.__init__`` through the package base (it defines no ``__init__``)
class ListArgumentError(GraphQLError, DjangoStrawberryFrameworkError):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """An argument to ``DjangoListField`` was invalid or violated policy bounds.

    Dual-inherits ``GraphQLError`` (so Strawberry/GraphQL transport serializes it
    as an execution error with structured extensions) and
    ``DjangoStrawberryFrameworkError`` (so consumers can catch it alongside any
    other framework error).

    Every numeric value interpolated into the wording renders through
    ``truth.render``. For the ordinary ``int`` the boundary admits that is
    byte-identical to the value itself; what it closes is the direct call
    carrying an integer with more digits than CPython will convert to a string,
    which would raise ``ValueError`` from the f-string assembled at the raise
    site and replace this typed rejection with an unrelated exception.
    """

    def __init__(
        self,
        field: str,
        argument: str,
        reason: _ListArgumentReason,
        value: object = None,
        ceiling: int | None = None,
        order_argument: str | None = None,
    ) -> None:
        """Record which argument of ``field`` failed and why; ``reason`` must be a known reason."""
        if reason not in _KNOWN_LIST_ARGUMENT_REASONS:
            raise ValueError(f"Unknown ListArgumentError reason {reason!r}.")
        self.field: str = field
        self.argument: str = argument
        self.reason: _ListArgumentReason = reason
        self.ceiling: int | None = ceiling
        self.order_argument: str | None = order_argument

        if reason == "non_integer":
            self.value: object = (
                truth.text(value) if truth.is_instance(value, str) else truth.describe(value)
            )
            msg = (
                f"Invalid argument {argument!r} on {field}: expected a non-negative "
                f"integer, got {self.value}."
            )
        elif reason == "negative":
            self.value = value
            msg = (
                f"Invalid argument {argument!r} on {field}: expected a non-negative "
                f"integer, got {truth.render(value)}."
            )
        elif reason == "over_ceiling":
            self.value = value
            msg = (
                f"Invalid argument {argument!r} on {field}: value {truth.render(value)} "
                f"exceeds the maximum allowed ceiling of {ceiling}."
            )
        elif reason == "order_required":
            self.value = value
            if order_argument:
                ordering_phrase = f"via {order_argument!r} or model 'Meta.ordering'"
            else:
                ordering_phrase = "via model 'Meta.ordering'"
            msg = (
                f"Invalid argument {argument!r} on {field}: non-zero offset "
                f"({truth.render(value)}) requires an active ordering {ordering_phrase}."
            )
        elif reason == "queryset_required":
            self.value = value
            msg = (
                f"Invalid argument {argument!r} on {field}: an ordering argument "
                "requires a QuerySet source."
            )
        detail: dict[str, object] = {"argument": argument, "reason": reason}
        if self.value is not None:
            detail["value"] = self.value
        if ceiling is not None:
            detail["ceiling"] = ceiling

        super().__init__(
            msg,
            extensions=coded_error_extensions("LIST_ARGUMENT_INVALID", **detail),
        )

    @override
    def __reduce__(self) -> tuple[object, ...]:
        """Preserve constructor arguments and instance state across pickle roundtrips."""
        return (
            type(self),
            (
                self.field,
                self.argument,
                self.reason,
                self.value,
                self.ceiling,
                self.order_argument,
            ),
            vars(self),  # truth: ok the exception's own pickle state, read by its own __reduce__
        )


_DEFAULT_WIRE_NAMES: dict[str, str] = {"offset": "offset", "limit": "limit", "order_by": "orderBy"}


def _resolve_argument_wire_name(info: Info[object, object], parameter_name: str) -> str:
    """Resolve the active GraphQL wire name for an internal parameter name.

    Only invoked on error paths (e.g. inside ``ListArgumentError`` instantiation or
    normalizer error branches) so successful requests perform zero name lookups.
    The name comes from the executable schema's published argument map
    (``utils/typing.py::published_argument_wire_name``); the schema's ``NameConverter`` is
    never invoked at request time.
    """
    return published_argument_wire_name(
        info,
        parameter_name,
        _DEFAULT_WIRE_NAMES.get(parameter_name, parameter_name),
    )


# ``slots=True`` is deliberately absent: combined with ``frozen=True`` the
# dataclass-generated ``__setattr__`` closes over the pre-slots class, so an
# undeclared attribute raises ``TypeError`` from ``super()`` instead of the
# ``FrozenInstanceError`` every other write path raises.
@dataclass(frozen=True)
class _ListArguments:
    offset: int | None
    limit: int | None
    order_by: object
    order_by_supplied: bool
    any_argument_supplied: bool


def _normalize_list_arguments(
    field_name: str,
    info: Info[object, object],
    max_rows: int | None,
    *,
    trusted_max_rows: bool,
    offset: object = None,
    limit: object = None,
    order_by: object = UNSET,
) -> _ListArguments:
    """Normalize and validate pagination arguments against effective resource policy ceilings.

    ``offset`` and ``limit`` must each be an EXACT ``int``. GraphQL's own ``Int``
    coercion always supplies one, so the exactness costs a wire request nothing;
    what it closes is the direct call the spec also promises to keep typed. An
    ``int`` SUBCLASS would otherwise reach the range comparisons and the error
    rendering below, running its ``__lt__`` / ``__gt__`` / ``__format__`` inside
    the argument boundary and replacing the typed rejection with whatever that
    consumer hook raised. Everything that is not exactly an ``int`` -- ``bool``
    included, which is a subclass -- takes the ``non_integer`` arm and renders
    through ``truth.describe``.

    Delegation guarantee:
        While offset and limit are validated here (integer type, non-negative, and limit
        within the effective ceiling), order_by structure and semantics are delegated to
        the target DjangoType's OrderSet (or to Strawberry's schema-level input validation
        when executed over GraphQL). Direct callers supplying non-null order_by to a target
        without an OrderSet are caught by
        ``django_strawberry_framework/utils/querysets.py::require_orderset_class``
        at pipeline execution time.
    """
    offset_supplied = is_supplied(offset)
    limit_supplied = is_supplied(limit)
    order_by_supplied = is_supplied(order_by)
    any_argument_supplied = offset_supplied or limit_supplied or order_by_supplied

    norm_offset = None if not offset_supplied else offset
    norm_limit = None if not limit_supplied else limit
    norm_order_by = None if not order_by_supplied else order_by

    if not any_argument_supplied:
        return _ListArguments(
            offset=None,
            limit=None,
            order_by=None,
            order_by_supplied=False,
            any_argument_supplied=False,
        )

    policy = policy_from_info(info)
    offset_ceiling = policy.max_list_rows

    if norm_offset is not None:
        if type(norm_offset) is not int:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "offset"),
                reason="non_integer",
                value=truth.describe(norm_offset),
            )
        if norm_offset < 0:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "offset"),
                reason="negative",
                value=norm_offset,
            )
        if norm_offset > offset_ceiling:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "offset"),
                reason="over_ceiling",
                value=norm_offset,
                ceiling=offset_ceiling,
            )

    if norm_limit is not None:
        effective_ceiling = effective_bound(
            policy.max_list_rows,
            max_rows,
            trusted=trusted_max_rows,
        )
        if type(norm_limit) is not int:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "limit"),
                reason="non_integer",
                value=truth.describe(norm_limit),
            )
        if norm_limit < 0:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "limit"),
                reason="negative",
                value=norm_limit,
            )
        if norm_limit > effective_ceiling:
            raise ListArgumentError(
                field_name,
                _resolve_argument_wire_name(info, "limit"),
                reason="over_ceiling",
                value=norm_limit,
                ceiling=effective_ceiling,
            )

    return _ListArguments(
        offset=norm_offset,
        limit=norm_limit,
        order_by=norm_order_by,
        order_by_supplied=order_by_supplied,
        any_argument_supplied=any_argument_supplied,
    )


def _synthesized_list_signature(
    orderset_class: type[OrderSet] | None,
) -> tuple[inspect.Signature, dict[str, object]]:
    """Build the resolver ``__signature__`` and ``__annotations__`` for DjangoListField.

    Carries ``offset`` and ``limit`` arguments, plus conditional ``order_by`` when
    the field captured an ``OrderSet`` for its target. The return annotation is left empty
    (``inspect.Signature.empty``) and omitted from annotations so the outer class attribute
    annotation retains sole ownership of outer nullability (``list[T]`` vs ``list[T] | None``).

    ``orderset_class`` is the field's ONE selected class, read from the single
    definition the target validator returned; the SDL published here and the
    class the resolver dispatches through are therefore the same object by
    construction.
    """
    params: list[inspect.Parameter] = [
        inspect.Parameter("root", inspect.Parameter.POSITIONAL_OR_KEYWORD, default=None),
        inspect.Parameter("info", inspect.Parameter.KEYWORD_ONLY, annotation=Info),
        inspect.Parameter(
            "offset",
            inspect.Parameter.KEYWORD_ONLY,
            default=None,
            annotation=int | None,
        ),
        inspect.Parameter(
            "limit",
            inspect.Parameter.KEYWORD_ONLY,
            default=None,
            annotation=int | None,
        ),
    ]
    annotations: dict[str, object] = {"info": Info, "offset": int | None, "limit": int | None}

    if orderset_class is not None:
        from .orders import order_input_type  # noqa: PLC0415 - keeps orders/filters out of the root graph

        order_ann = GenericAlias(list, (order_input_type(orderset_class),)) | None
        params.append(
            inspect.Parameter(
                "order_by",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=order_ann,
            ),
        )
        annotations["order_by"] = order_ann

    return inspect.Signature(params, return_annotation=inspect.Signature.empty), annotations


#: The expression leaves this package can read: a column, the ``*`` of a row count,
#: a literal value, and the framework's own visibility test. Matched by EXACT type,
#: like every other approved form below, because a subclass carries its own
#: ``as_sql``. ``VisibleRowExists`` decides only whether an ``OrderSet`` term reads
#: its column or ``NULL``, and its rows are a target type's ``get_queryset``, which
#: this guard trusts for the parent rows as well.
_READABLE_ORDER_LEAVES: truth.IdentitySet[type[object]] = truth.IdentitySet(
    (
        models.Value,
        Col,
        Star,
        VisibleRowExists,
    ),
)


def _aggregate_filter_classes() -> tuple[type[object], ...]:
    """Return Django's ``AggregateFilter``, or nothing on a release without it.

    Django 6.0 wraps an aggregate's ``filter=`` predicate in
    ``django/db/models/aggregates.py::AggregateFilter``, whose SQL is the
    ``FILTER (WHERE ...)`` punctuation around that predicate. Below 6.0 the class
    does not exist and the predicate sits directly among the aggregate's sources.
    """
    aggregate_filter = read_attr(aggregates, "AggregateFilter", None)
    return (aggregate_filter,) if truth.is_type(aggregate_filter) else ()


#: Expressions whose own SQL is punctuation around their sources - the branches of
#: a ``CASE``, an operator between two operands (including the temporal forms
#: ``CombinedExpression.resolve_expression`` turns date and duration arithmetic
#: into, which compile the backend's own subtraction or interval arithmetic), a
#: wrapper that only supplies an output field, the direction marker on a term, the
#: commas of an expression list an ``__in`` compares against, and the
#: ``FILTER (WHERE ...)`` around an aggregate's predicate. A node listed here
#: orders by whatever its sources order by and by nothing else, so it is read
#: through.
_TRANSPARENT_ORDER_EXPRESSIONS: tuple[type[object], ...] = (
    Case,
    CombinedExpression,
    DurationExpression,
    ExpressionList,
    ExpressionWrapper,
    OrderBy,
    TemporalSubtraction,
    When,
    *_aggregate_filter_classes(),
)

#: Database functions whose SQL is a deterministic function of their arguments:
#: the same arguments produce the same value on every execution, so such a node
#: is read through to its sources and adds no volatility of its own. Membership
#: is by EXACT type - a subclass overrides ``as_sql`` and emits whatever it
#: likes, so it is not this class and is not approved. Nothing is listed for
#: being harmless-looking: a function reaches this set only by being one of
#: Django's own and pure.
_APPROVED_ORDER_FUNCTIONS: tuple[type[object], ...] = (
    Cast,
    Coalesce,
    Concat,
    ConcatPair,
    Length,
    Lower,
    Upper,
)

#: Aggregates under the same rule:
#: ``orders/sets.py::OrderSet._resolve_order_expressions`` annotates ``Min`` /
#: ``Max`` for a to-many ordering path, and ``Count`` admits the row-count
#: aggregate a consumer ordering may annotate.
_APPROVED_ORDER_AGGREGATES: tuple[type[object], ...] = (models.Count, models.Max, models.Min)

#: Transforms under the same purity rule and the same exact-type match. A
#: transform piece of an ``F`` or a predicate's left-hand side is applied by
#: resolution, so it is read as the node it resolves into: ``F("stamp__year")``
#: is ``ExtractYear(...)`` ordered directly and annotated alike.
_APPROVED_ORDER_TRANSFORMS: truth.IdentitySet[type[object]] = truth.IdentitySet(
    (
        ExtractDay,
        ExtractMonth,
        ExtractYear,
        Length,
        Lower,
        TruncDate,
        TruncMonth,
        TruncYear,
        Upper,
    ),
)

#: Lookups a predicate may compare with: Django's own comparison, membership and
#: null tests, each of which compiles to an operator over its two sides and
#: contributes no SQL a caller could steer. The integer- and relation-specific
#: spellings are listed beside the general ones because Django substitutes them
#: by field type for the same operators - an exact-type match sees the class the
#: field hands back, not the base it derives from.
_APPROVED_ORDER_LOOKUPS: truth.IdentitySet[type[object]] = truth.IdentitySet(
    (
        Exact,
        GreaterThan,
        GreaterThanOrEqual,
        In,
        IntegerFieldExact,
        IntegerGreaterThan,
        IntegerGreaterThanOrEqual,
        IntegerLessThan,
        IntegerLessThanOrEqual,
        IsNull,
        LessThan,
        LessThanOrEqual,
        Range,
        RelatedExact,
        RelatedGreaterThan,
        RelatedGreaterThanOrEqual,
        RelatedIn,
        RelatedIsNull,
        RelatedLessThan,
        RelatedLessThanOrEqual,
        YearExact,
        YearGt,
        YearGte,
        YearLt,
        YearLte,
    ),
)

#: Every node read THROUGH to its sources. A term whose type is absent from this
#: union and from ``_READABLE_ORDER_LEAVES`` is refused, whatever it holds.
_APPROVED_ORDER_NODES: truth.IdentitySet[type[object]] = truth.IdentitySet(
    (
        *_TRANSPARENT_ORDER_EXPRESSIONS,
        *_APPROVED_ORDER_FUNCTIONS,
        *_APPROVED_ORDER_AGGREGATES,
        *_APPROVED_ORDER_TRANSFORMS,
    ),
)

#: The operators ``CombinedExpression.as_sql`` writes between its two operands,
#: which are Django's own ``Combinable`` constants. The connector is instance
#: state, so a node of an approved class can still carry any text there. The
#: two subclasses a resolved temporal operand produces store one too, and are
#: held to the same constants: ``DurationExpression`` hands it to the backend's
#: duration arithmetic, while ``TemporalSubtraction`` stores ``-`` and compiles
#: the backend's own subtraction without reading it.
_COMBINED_ORDER_NODES: truth.IdentitySet[type[object]] = truth.IdentitySet(
    (CombinedExpression, DurationExpression, TemporalSubtraction),
)
_COMBINED_ORDER_CONNECTORS: tuple[str, ...] = (
    Combinable.ADD,
    Combinable.SUB,
    Combinable.MUL,
    Combinable.DIV,
    Combinable.POW,
    Combinable.MOD,
    Combinable.BITAND,
    Combinable.BITOR,
    Combinable.BITLEFTSHIFT,
    Combinable.BITRIGHTSHIFT,
    Combinable.BITXOR,
)

#: The connectors ``WhereNode.as_sql`` writes between a predicate's children.
_WHERE_ORDER_CONNECTORS: tuple[str, ...] = (AND, OR, XOR)

#: Approved nodes whose SQL calls a hook on their own output field:
#: ``Value.as_sql`` asks it for a placeholder and ``Cast.as_sql`` for the type it
#: casts to. Either hook emits SQL, so such a node is read only over one of
#: Django's own field classes.
_FIELD_HOOK_ORDER_NODES: truth.IdentitySet[type[object]] = truth.IdentitySet((models.Value, Cast))


def _resolve_order_field_path(opts: _OptionsAny, path: str) -> ResolvedOrderName | None:
    """Resolve a field path against ``opts`` as the compiler does, or return None.

    ``utils/querysets.py::resolve_order_name`` is the ``Query.names_to_path``
    walk ``setup_joins`` runs for an order name, an ``F`` and a lookup alike, so
    the field it ends on is the one Django compiles against: for a many-to-many,
    the through table's key to the target rather than the ``ManyToManyField``.
    The walk runs against the model alone. The annotation and ``extra`` steps
    that read the query's own state come first, by name, where the compiler
    takes them; a piece only the query's annotations or filtered relations could
    resolve further along a path is not a column this package can name. A path
    that does not resolve is None, and is never certified.
    """
    try:
        return resolve_order_name(sql.Query(opts.model), path, opts)
    except FieldError:
        return None


def _is_deterministic_order_field_path(
    query: Query,
    path: str,
    opts: _OptionsAny,
    seen: set[tuple[object, ...]] | None,
    start: object,
    prefix: str,
) -> bool:
    """Classify a resolved field path, expanding a relation the way the compiler does.

    ``django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name`` does not
    order by a relation: when the path ends on a relation whose target model has
    its own ``Meta.ordering``, and the last piece is neither the ``attname`` of
    the last hop's join field nor ``pk``, the compiler REPLACES the term with
    that model's ordering and keeps recursing
    (``utils/querysets.py::resolve_order_name``). For a many-to-many that
    join field is the through table's key to the target, and for a generic
    relation its reverse relation, which has no ``attname``, so either relation
    name always expands. So the order the rows come back in is the
    related model's, and it is that ordering - not the relation name standing in
    front of it - that decides whether the request is repeatable.

    An expansion Django would reject with ``FieldError("Infinite loop caused by
    ordering.")`` is refused rather than followed. The compiler threads ONE
    ``already_seen`` set through the whole expansion of a top-level term,
    sibling items of every related ordering included, so ``seen`` is that set:
    None on a top-level term, which creates it here, and shared by everything
    the expansion reaches below. ``start`` is the key of the join the expansion
    hangs from, and ``utils/querysets.py::take_order_expansion_step`` keys and
    records each step exactly as the compiler does, so a join one sibling
    already expanded refuses the next sibling that repeats it. A path with a
    piece left over once a piece names no field is refused too: that is a
    transform or a lookup, which this package does not read.

    ``prefix`` is the name the expanded terms hang under. The compiler rewrites
    an expression it lifts out of a related ordering through
    ``prefix_references``, so a reference written against the related model
    arrives at the outer query under the relation path that reached it, and a
    classifier reading references must name them the same way.
    """
    resolved = _resolve_order_field_path(opts, path)
    if resolved is None or resolved.lookups:
        return False
    related_opts = resolved.related_opts
    if resolved.substitute is None or related_opts is None:
        return True
    # A top-level term's expansion owns one set, shared by every sibling below it.
    taken: set[tuple[object, ...]] = set() if seen is None else seen
    step = take_order_expansion_step(resolved, start=start, seen=taken)
    if step is None:
        return False
    nested_prefix = f"{prefix}{path}{LOOKUP_SEP}"
    return all(
        _is_deterministic_order_term(query, item, related_opts, taken, step[-1], nested_prefix)
        for item in resolved.substitute
    )


def _is_deterministic_order_name(
    query: Query,
    name: str,
    opts: _OptionsAny | None = None,
    seen: set[tuple[object, ...]] | None = None,
    start: object = None,
    prefix: str = "",
) -> bool:
    """Resolve a string ordering term the way the compiler resolves it, then classify it.

    ``django/db/models/sql/compiler.py::SQLCompiler._order_by_pairs`` tests
    ``field == "?"`` exactly, so a descending spelling such as ``"-?"`` is not a
    random order at all - Django resolves it as a column named ``?`` and raises
    ``FieldError``. Every other name is looked up as an annotation (the whole
    name first, then the head of a transform chain), then as an ``extra`` key,
    and only then as a field path, so the name that survives to the field path
    is the only one that could order by a column. This package reads no
    transform in a string order name: a name whose head alone names an
    annotation is refused, exactly as a field path with pieces left over is.
    An annotation is already resolved, so the whole-name match reads it as the
    resolved graph it is.

    Raw SQL reached through ``extra`` is opaque, which is not the same as
    deterministic. Those strings are passed through verbatim and this package
    parses no SQL, so it cannot say what such a term orders by - and a term it
    cannot read is one it must not certify as repeatable across the two queries
    an offset window spans.

    Surviving to a field path is still not the end of the resolution:
    ``django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name`` expands
    a path ending on a relation into the related model's own ``Meta.ordering``,
    so a random default one indirection away is what such a name really orders
    by. ``opts`` names the model a path is resolved against, which is the related
    model while such an expansion is being read - and at that depth there are no
    annotations and no ``extra`` to consult, because the compiler resolves those
    terms against the related model's fields alone.
    """
    if name == "?":
        return False
    col = name.removeprefix("-")
    if opts is None:
        annotation = query.annotations.get(col)
        if annotation is not None:
            return _is_readable_order_node(annotation)
        if col.split(LOOKUP_SEP, maxsplit=1)[0] in query.annotations:
            return False
        if col in query.extra:
            return False
        if "." in name and name in query.extra_order_by:
            return False
        opts = query.get_meta()
    return _is_deterministic_order_field_path(query, col, opts, seen, start, prefix)


def _is_deterministic_order_term(
    query: Query,
    term: object,
    opts: _OptionsAny | None = None,
    seen: set[tuple[object, ...]] | None = None,
    start: object = None,
    prefix: str = "",
) -> bool:
    """Classify one selected ordering term by the form Django will compile it into.

    Which arm a term takes is decided the way
    ``django/db/models/sql/compiler.py::SQLCompiler._order_by_pairs`` decides
    it: a term carrying ``resolve_expression`` is an expression and is read as
    one, and only a term without it is read as a string name. A ``str`` subclass
    that carries that method is therefore classified as the expression Django
    will resolve it to rather than as the field path it spells.

    A STRING term is resolved through ``query.annotations`` and ``query.extra``
    before it is read as a field path (``_is_deterministic_order_name``). One
    that resolves to a relation is one more indirection:
    ``django/db/models/sql/compiler.py::SQLCompiler.find_ordering_name``
    replaces it with the related model's ``Meta.ordering``, and every term of
    that ordering is classified against THAT model - which is what ``opts``
    carries, together with ``seen`` and ``start`` so a relation cycle Django
    would reject is refused instead of followed, and ``prefix`` so an expression
    lifted out of the expansion is named the way the outer query will resolve
    it.

    An EXPRESSION term is not compiled as written.
    ``django/db/models/sql/compiler.py::SQLCompiler.get_order_by`` resolves it
    against the query first, and resolution is where its SQL is decided: an
    ``F`` becomes a column, an annotation or a transform over either; a ``Q``
    becomes a ``WhereNode`` of the lookups the field registry hands back for the
    value given, null compensation for a negated nullable comparison included;
    arithmetic over temporal operands becomes ``TemporalSubtraction`` or
    ``DurationExpression``. So the term is resolved the same way
    (``_resolved_order_expression``) and the resolved graph is what is classified
    (``_is_readable_order_node``) - the graph an annotation of the same spelling
    holds, so a spelling gets one verdict ordered directly or annotated first.
    An expression lifted out of a relation expansion is not a reference to the
    related model's default, because only a string reaches the expansion:
    ``F("branch")`` resolves to the foreign key column whatever the branch model
    declares.

    ``query`` is the clone a verdict resolves on (``_are_deterministic_order_terms``),
    never the queryset's own query, because resolving sets up joins.
    """
    if hasattr(term, "resolve_expression"):
        resolved = _resolved_order_expression(query, term, prefix)
        return resolved is not None and _is_readable_order_node(resolved)
    if isinstance(term, str):
        return _is_deterministic_order_name(query, term, opts, seen, start, prefix)
    return False


def _resolved_order_expression(query: Query, term: object, prefix: str) -> object | None:
    """Resolve an expression ordering term as the compiler does, or return None.

    Mirrors ``SQLCompiler._order_by_pairs`` and ``SQLCompiler.get_order_by``:
    a term that is not an ``OrderBy`` is wrapped in one, an expression lifted
    out of a related model's ordering is renamed under the relation path that
    reached it (``find_ordering_name`` calls ``prefix_references`` on the
    ``OrderBy``, the only form that has it), and the result is resolved against
    the query with joins allowed and none reserved. A ``When`` over a ``Q`` in
    such an ordering raises here exactly as it does in that method. A name the
    query cannot resolve is a ``FieldError`` and is never certified.

    The term must first pass ``_is_readable_order_node`` as written, which keeps
    a project node class, a subclass of ``F`` or ``Q``, and a ``str`` subclass
    standing in for a name out of resolution altogether: Django's own
    ``resolve_expression`` methods are the only ones it runs. Resolution still
    calls what the compile itself calls - the hooks of the fields a reference
    reaches, and the constructors of the transforms and lookups those fields
    register - which is application code inside the trust boundary. A project
    class those calls produce is in the resolved graph, where it is refused by
    exact type.

    ``query`` is shared by every expression term of one verdict and resolved
    in the order the compiler resolves them, because a resolution can change the
    next one: ``Q.resolve_expression`` promotes the joins it uses, and
    ``Query.build_filter`` adds its null-compensating ``isnull`` to a negated
    comparison over a ``LEFT OUTER`` join, so a term after one that promoted a
    join compiles a test a fresh query would not show. A string term needs no
    such replay: ``Query.join`` types a new join from its nullability and its
    parent's type alone, and reusing a join never changes its type.
    """
    if not _is_readable_order_node(term) or not isinstance(term, BaseExpression | models.F):
        return None
    ordered: BaseExpression = term if type(term) is OrderBy else term.asc()
    if prefix:
        ordered = ordered.prefix_references(prefix)
    try:
        return ordered.resolve_expression(query, allow_joins=True, reuse=None)
    except FieldError:
        return None


def _order_select_references(
    query: Query,
    term: object,
    *,
    nulls_modifier: bool,
) -> tuple[object, ...]:
    """Return the selected expressions a top-level expression term orders by, if any.

    ``SQLCompiler._order_by_pairs`` does not resolve a top-level expression term
    that names a selected one: an ``F`` naming a selected annotation or an
    ``extra`` select alias, or an expression equal to a selected one, becomes a
    reference to that select position - unless the term places nulls and the
    backend cannot say so in SQL, in which case the term is resolved as written.
    The statement then orders by the SELECTED expression, so that is what is
    classified: an ``F("name")`` under ``extra(select={"name": "RANDOM()"})``
    orders by position 1, which is ``RANDOM()``, even though ``name`` is also a
    column. An ``extra`` select is returned as the ``(sql, params)`` pair the
    query holds - opaque SQL, which no reader certifies.

    A combined query's own fallback is unreachable here: the post-``OrderSet``
    seal rewrites a combinator queryset to a primary-key filter, so a combinator
    never reaches the guard. An empty result means the term is resolved.
    """
    if not _is_readable_order_node(term) or not isinstance(term, BaseExpression | models.F):
        return ()
    ordered = term if type(term) is OrderBy else term.asc()
    placement = truth.instance_state(ordered)
    if not nulls_modifier and (
        placement.get("nulls_first") is not None or placement.get("nulls_last") is not None
    ):
        return ()
    expression = placement.get("expression")
    if type(expression) is models.F:
        # The shape pass proved the name an exact ``str``; ``is_str`` states it for the
        # checker.
        name = read_attr(expression, "name")
        if is_str(name):
            extra: object = query.extra_select.get(name)
            if extra is not None:
                return (extra,)
            annotation: object = query.annotation_select.get(name)
            if annotation is not None:
                return (annotation,)
    return tuple(
        selected
        for selected in list_of(query.annotation_select.values())
        if selected == expression
    )


def _is_readable_order_node(node: object) -> bool:
    """Return whether an expression node compiles only to SQL this package can read.

    Certification is positive and the boundary is an explicit list of APPROVED
    FORMS. Having source expressions is not a promise about a node's own SQL:
    ``Func``, ``Transform``, ``Aggregate`` and ``Window`` each emit SQL of their
    own around their sources, and any of them can be subclassed with an
    ``as_sql`` that emits anything at all - so "it has readable children" would
    certify a one-class project expression spelling ``RANDOM()`` over a column.
    A node is therefore read through only when it is one of the forms this
    package names: a transparent composition
    (``_TRANSPARENT_ORDER_EXPRESSIONS``), a pure database function
    (``_APPROVED_ORDER_FUNCTIONS``), an approved aggregate
    (``_APPROVED_ORDER_AGGREGATES``: ``Min`` / ``Max`` the shipped surface emits,
    ``Count`` a consumer ordering may annotate), or an approved transform
    (``_APPROVED_ORDER_TRANSFORMS``). Each of those is then certified only if
    every source expression it holds is, so an approved wrapper launders
    nothing: ``Coalesce(Random(), Random())`` is refused through its children. A
    readable leaf (``_READABLE_ORDER_LEAVES``) carries all of its own SQL and is
    named outright: a column reference, the ``*`` of a row count, a literal
    value, and the framework's own ``VisibleRowExists`` visibility test.

    The class is not the whole of a node's SQL, so every approved node and leaf
    must also carry its class's own SQL (``_order_node_state_is_stock``): an
    instance can still hold a template, a function name, an operator or an
    output field whose hooks emit SQL of their own.

    A resolved predicate is a ``WhereNode`` of lookups - what a ``When``
    condition and an aggregate's ``filter=`` (wrapped in ``AggregateFilter``
    from Django 6.0) hold once resolved. A ``WhereNode`` is punctuation over its
    children, and a lookup of an approved class (``_APPROVED_ORDER_LOOKUPS``) is
    certified when both of its sides are. The lookup is the class Django chose
    for the value given, its rewrites included, so nothing is re-derived for it.

    An ``F`` or a ``Q`` is the unresolved spelling of a term and is read for its
    SHAPE only, as the gate ``_resolved_order_expression`` passes before it
    resolves anything: the exact class with a ``str`` name, or with
    ``(str, value)`` children and nested predicates and expressions this reader
    passes. What either resolves to is read after resolution.

    Every match is by EXACT type, the two reference forms included. A subclass
    of an approved class is a different ``as_sql`` and is refused, which is the
    whole difference between naming a form and recognizing a family; a subclass
    of ``F`` or of ``Q`` is a different ``resolve_expression``, which is the
    same difference one step earlier. Everything unlisted is refused too -
    ``Random()``, a bare or custom ``Func``, an unlisted ``Transform`` or
    lookup, an unlisted ``Aggregate``, a ``Window``, a ``RawSQL`` fragment, the
    inner ``Query`` a ``Subquery`` wraps, a ``NothingNode`` or ``ExtraWhere``
    predicate child - because a term this package cannot read is one it must
    not certify as repeatable across the two queries an offset window spans.
    """
    if not hasattr(node, "resolve_expression"):
        return False
    if type(node) is models.F:
        # ``F.name`` is the path ``F.__init__`` stored; anything but a ``str`` is not a
        # name Django's own resolution reads, so it is refused before it is resolved.
        return type(read_attr(node, "name")) is str
    if type(node) is models.Q:
        return _is_readable_order_condition(node)
    if truth.is_exact_one_of(node, _READABLE_ORDER_LEAVES):
        return _order_node_state_is_stock(node)
    if type(node) is WhereNode:
        children = truth.instance_state(node).get("children")
        return (
            is_list_or_tuple(children)
            and _order_node_state_is_stock(node)
            and all(_is_readable_order_node(child) for child in children)
        )
    if truth.is_exact_one_of(node, _APPROVED_ORDER_LOOKUPS):
        # Both operands are read from the instance state, as the seal reads them:
        # ``Lookup.get_source_expressions`` omits a direct right-hand side.
        operands = truth.instance_state(node)
        return (
            _order_node_state_is_stock(node)
            and _is_readable_order_node(operands.get("lhs"))
            and _is_deterministic_order_value(operands.get("rhs"))
        )
    # Every approved node is a ``BaseExpression`` subclass, so the instance test only
    # states for the reader of ``get_source_expressions`` what the membership proved.
    if not truth.is_exact_one_of(node, _APPROVED_ORDER_NODES) or not isinstance(
        node,
        BaseExpression,
    ):
        return False
    return _order_node_state_is_stock(node) and all(
        _is_readable_order_node(source)
        for source in list_of(node.get_source_expressions())
        if source is not None
    )


def _is_readable_order_condition(condition: models.Q) -> bool:
    """Return whether an unresolved predicate has the shape Django's resolution reads.

    A ``Q`` child is either a nested predicate or expression, read by
    ``_is_readable_order_node``, or a ``(lookup, value)`` pair: an exact ``str``
    lookup ``Query.build_filter`` splits into a reference, transforms and a
    lookup, and a value read for the SQL it carries
    (``_is_deterministic_order_value``). Which column, transforms and lookup
    class the pair compiles to is decided by resolution and read after it.
    """
    for child in condition.children:
        if not is_tuple(child):
            if not _is_readable_order_node(child):
                return False
            continue
        # A ``tuple`` subclass would unpack through its own methods.
        if type(child) is not tuple:
            return False
        lookup, value = child
        if type(lookup) is not str or not _is_deterministic_order_value(value):
            return False
    return True


def _order_node_state_is_stock(term: object) -> bool:
    """Return whether an approved node carries only the SQL its class supplies.

    Approving a class approves the ``as_sql`` it defines, and that method
    formats instance state into the statement. The seal admits text in every
    such slot (``utils/querysets.py::_SQL_TEMPLATE_ATTRS``) and in the ``extra``
    mapping ``Func`` merges into its template, so ``Lower("name",
    template="RANDOM()")`` is an exact ``Lower`` that compiles to ``RANDOM()``.
    The state is read from the instance namespace, which dispatches nothing,
    and every slot must be absent or restate the text the class itself
    defines, as ``Subquery`` (so the framework's ``VisibleRowExists``) always
    stores its ``template``. The operator a ``CombinedExpression`` or
    ``WhereNode`` always stores has no class value and must be one of Django's
    own (``_COMBINED_ORDER_CONNECTORS``, ``_WHERE_ORDER_CONNECTORS``). ``extra``
    must be empty.

    ``Value`` and ``Cast`` also call a hook on their output field
    (``_FIELD_HOOK_ORDER_NODES``), so such a node is read only when that field
    is one of Django's own classes. Django infers a ``Value``'s field from the
    Python type, and gives an ``__in`` list's literal the compared field's
    class: a project field's ``get_placeholder`` is SQL Django will compile,
    and is refused like any other. A column's field is the model's own and is
    not constrained, because no hook of it reaches the order SQL.
    """
    state = truth.instance_state(term)
    for attr in _SQL_TEMPLATE_ATTRS:
        if attr not in state:
            continue
        connector = state[attr]
        if type(connector) is not str:
            return False
        if connector == truth.mro_attr(type(term), attr):
            continue
        if attr != "connector":
            return False
        if truth.is_exact_one_of(term, _COMBINED_ORDER_NODES):
            connectors = _COMBINED_ORDER_CONNECTORS
        elif type(term) is WhereNode:
            connectors = _WHERE_ORDER_CONNECTORS
        else:
            return False
        if connector not in connectors:
            return False
    extra = state.get("extra")
    if extra is not None and (not is_exact_dict(extra) or extra):
        return False
    if truth.is_exact_one_of(term, _FIELD_HOOK_ORDER_NODES):
        output_field = state.get("output_field")
        return output_field is None or _type_is_genuinely_django(type(output_field))
    return True


def _is_deterministic_order_value(value: object) -> bool:
    """Classify one value a predicate's lookup compares its column against.

    A value carries SQL of its own either as an expression or inside a container
    of them, because a lookup taking a sequence compiles every member into the
    statement the same way it compiles a value given alone. Reading only the top
    level would certify a fragment written one bracket deeper - ``name__in`` is
    a list, ``created__range`` a pair - as an ordinary comparison against
    literals. A value that is neither an expression nor such a container is a
    plain literal, which is already as readable as a term gets.
    """
    if hasattr(value, "resolve_expression"):
        return _is_readable_order_node(value)
    # The container shapes a predicate's right-hand side arrives in: ``__in`` takes a
    # sequence and ``__range`` a pair, and each member is compiled into the statement.
    if is_list_or_tuple(value) or is_set_or_frozenset(value):
        return all(_is_deterministic_order_value(member) for member in value)
    return True


def _has_deterministic_ordering(queryset: models.QuerySet[models.Model]) -> bool:
    """Return True when every term of the order Django will compile is deterministic.

    Classifies the SELECTED ordering, not every collection holding terms: a
    ``"?"`` sitting in ``query.order_by`` under an ``extra`` ordering that
    supersedes it never reaches SQL, while a ``"?"`` the model brought in
    through ``Meta.ordering`` does. Either way the verdict has to be about the
    collection Django is going to run.

    The selection is ``utils/querysets.py::selected_order``, the compiler's own
    one-collection choice (the read the connection order ladder shares). Both
    questions the offset guard asks - this one and
    ``_is_model_default_ordering_active`` - read that one selection of the
    already-sealed queryset, rather than scanning ``order_by``,
    ``extra_order_by`` and ``Meta.ordering`` separately in ways that can
    disagree with each other and with the compiler.
    """
    _source, terms = selected_order(queryset.query, queryset.model)
    return _are_deterministic_order_terms(queryset, terms)


def _is_model_default_ordering_active(queryset: models.QuerySet[models.Model]) -> bool:
    """Return True when the model's own ``Meta.ordering`` is the order Django will compile.

    The guard's public-order eligibility rule: ordering the resolver alone put on
    the queryset never authorizes a positive offset, so the only two orders that
    do are an active ``orderBy`` input and this one. ``default_ordering`` must be
    exactly ``True`` - a merely truthy stand-in is a shape the queryset pipeline
    does not produce, and an offset window is not granted on one. Grouping
    suppresses the default for the same reason ``QuerySet.ordered`` does: an
    aggregate query does not carry the model's row order. The selection is the
    one ``_has_deterministic_ordering`` reads.
    """
    query = queryset.query
    source, terms = selected_order(query, queryset.model)
    if source != ORDER_FROM_MODEL_DEFAULT:
        return False
    if query.default_ordering is not True or query.group_by:
        return False
    return _are_deterministic_order_terms(queryset, terms)


def _are_deterministic_order_terms(
    queryset: models.QuerySet[models.Model],
    terms: tuple[object, ...],
) -> bool:
    """Classify every selected ordering term, in compile order, on one resolution of the query.

    Every expression term resolves on the same clone of the queryset's query, in
    the order ``SQLCompiler.get_order_by`` resolves them, because one
    resolution can change the next (``_resolved_order_expression``); the
    queryset's own query is never touched. A top-level term that names a
    selected expression is read as that expression, as the compiler orders by
    it (``_order_select_references``); whether a term placing nulls still does
    is the backend's ``supports_order_by_nulls_modifier``, read on the
    connection the queryset runs on.
    """
    query = queryset.query.clone()
    nulls_modifier = connections[queryset.db].features.supports_order_by_nulls_modifier
    for term in terms:
        selected = _order_select_references(query, term, nulls_modifier=nulls_modifier)
        if selected:
            if not all(_is_readable_order_node(expression) for expression in selected):
                return False
        elif not _is_deterministic_order_term(query, term):
            return False
    return True


def _model_from_definition(definition: DjangoTypeDefinition) -> type[models.Model]:
    """Read the target's Django model off its ONE definition read.

    Called exactly once per field, at construction. The value seeds the default
    resolver and pins both visibility seals, so the table the field queries and
    the table those seals validate against are the same object by construction:
    there is no second read through which another model could be substituted
    between the seed and the seal.
    """
    model = definition.model
    # The canonical definition records a model class, but it is a mutable record
    # reachable from the target's public class attribute; the check fails loud if
    # that invariant is ever broken instead of seeding a resolver over a non-model.
    if not truth.is_subclass(model, models.Model):
        raise ConfigurationError(
            f"DjangoListField target {truth.name(definition.origin)} has a definition "
            f"whose model is not a Django model; got {truth.render(model)}.",
        )
    return model


def _orderset_class_from_definition(definition: DjangoTypeDefinition) -> type[OrderSet] | None:
    """Read the target's declared ``Meta.orderset_class`` off its ONE definition read.

    Called exactly once per field, at construction, from the definition
    ``_validate_djangotype_target`` returned, so the published ``orderBy``
    argument and the dispatch come from one answer.
    """
    return definition.orderset_class


def _field_label(info: Info[object, object]) -> str:
    """Return the resolver field label, or ``"DjangoListField"`` when ``info`` names none."""
    # A consumer ``info_class`` can shadow ``field_name`` with anything.
    field_name = read_attr(info, "field_name", None)
    if not truth.is_instance(field_name, str):
        return "DjangoListField"
    return truth.text(field_name, "DjangoListField")


def _resolver_root_and_info(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> tuple[object, Info[object, object]]:
    """Extract Strawberry's positional resolver context and reject unknown call inputs."""
    if len(args) > _RESOLVER_POSITIONAL_INPUTS:
        raise TypeError("DjangoListField resolver accepts only root and info positional inputs.")
    unexpected = set(kwargs) - {"info", "root"}
    if unexpected:
        names = ", ".join(sorted(unexpected))
        raise TypeError(f"DjangoListField resolver received unexpected keyword inputs: {names}.")
    if args and "root" in kwargs:
        raise TypeError("DjangoListField resolver received multiple values for root.")
    if len(args) > 1 and "info" in kwargs:
        raise TypeError("DjangoListField resolver received multiple values for info.")
    root = args[0] if args else kwargs.get("root")
    if len(args) > 1:
        info = args[1]
    else:
        try:
            info = kwargs["info"]
        except KeyError as exc:
            raise TypeError("DjangoListField resolver requires info.") from exc
    # Strawberry binds its own ``Info`` to the resolver parameter annotated ``Info`` (here
    # the synthesized keyword-only ``info``); any other value is a ``TypeError``.
    return root, require_instance(info, Info)


def _argument_record(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
    *,
    max_rows: int | None,
    trusted_max_rows: bool,
    offset: object = None,
    limit: object = None,
    order_by: object = UNSET,
) -> tuple[object, Info[object, object], _ListArguments]:
    """Extract root, info, and normalize list arguments for any resolver invocation."""
    root, info = _resolver_root_and_info(args, kwargs)
    field_name = _field_label(info)
    args_record = _normalize_list_arguments(
        field_name,
        info,
        max_rows,
        trusted_max_rows=trusted_max_rows,
        offset=offset,
        limit=limit,
        order_by=order_by,
    )
    return root, info, args_record


def _build_non_queryset_rejection_error(
    args_record: _ListArguments,
    info: Info[object, object],
    *,
    orderset_class: type[OrderSet] | None = None,
) -> ListArgumentError | None:
    field_name = _field_label(info)
    if args_record.order_by_supplied:
        return ListArgumentError(
            field_name,
            _resolve_argument_wire_name(info, "order_by"),
            reason="queryset_required",
        )
    if args_record.offset is not None and args_record.offset > 0:
        order_arg = _resolve_argument_wire_name(info, "order_by") if orderset_class else ""
        return ListArgumentError(
            field_name,
            _resolve_argument_wire_name(info, "offset"),
            reason="order_required",
            value=args_record.offset,
            order_argument=order_arg,
        )
    return None


async def _handle_non_queryset_rejections_async(
    source: object,
    args_record: _ListArguments,
    info: Info[object, object],
    *,
    orderset_class: type[OrderSet] | None = None,
) -> None:
    """Reject a non-queryset source, closing an async-only one on EVERY rejecting exit.

    spec-050 Decision 8 promises a rejected async-only source is never advanced and is
    closed when possible, with the primary error keeping precedence. Building
    the rejection can itself fail (malformed schema metadata behind the wire
    name lookup), and that exit owes the same close: the source is being
    rejected either way, so the failure becomes the primary error the cleanup
    utility attaches its notes to.
    """
    try:
        err = _build_non_queryset_rejection_error(
            args_record,
            info,
            orderset_class=orderset_class,
        )
    except BaseException as primary:
        if is_async_only_iterable(source):
            await _cleanup_rejected_async_iterable(source, primary, caller="DjangoListField")
        raise
    if err is not None:
        if is_async_only_iterable(source):
            await _cleanup_rejected_async_iterable(source, err, caller="DjangoListField")
        raise err


def _check_nonzero_offset_guard(
    queryset: models.QuerySet[models.Model],
    args_record: _ListArguments,
    orderset_class: type[OrderSet] | None,
    info: Info[object, object],
) -> None:
    """Validate that non-zero offset pagination is backed by a deterministic ordering.

    A positive ``offset`` needs an order the request can name: active ``OrderSet``
    terms the consumer supplied, or the model's own eligible ``Meta.ordering``.
    With neither in effect the offset is rejected, because the rows it skips are
    otherwise whichever rows the database happened to return first.

    The empty-queryset allowance lives inside the active-input branch alone.
    Django reports ``ordered`` True for an ``EmptyQuerySet`` whatever it carries
    (``Category.objects.none().ordered is True``), so that half of the branch is
    vacuous there and an empty window supplied with active terms rides through on
    an order that orders nothing. A request with no active input and no eligible
    model ordering is rejected whether its queryset is empty or not.
    """
    if args_record.offset is None or args_record.offset <= 0:
        return
    has_active_order = False
    if (
        args_record.order_by_supplied
        and orderset_class is not None
        and orderset_class._input_has_active_terms(args_record.order_by)
        and queryset.ordered
        and _has_deterministic_ordering(queryset)
    ):
        has_active_order = True
    if not has_active_order and not _is_model_default_ordering_active(queryset):
        field_name = _field_label(info)
        order_arg = (
            _resolve_argument_wire_name(info, "order_by") if orderset_class is not None else ""
        )
        raise ListArgumentError(
            field_name,
            _resolve_argument_wire_name(info, "offset"),
            reason="order_required",
            value=args_record.offset,
            order_argument=order_arg,
        )


def _order_normalization_scope(
    args_record: _ListArguments,
    orderset_class: type[OrderSet] | None,
) -> contextlib.AbstractContextManager[None]:
    """Return the capture scope this request actually needs, or an inert one.

    The handoff exists for exactly one consumer: the non-zero-offset guard's
    active-order check, which is the only caller of
    ``OrderSet._input_has_active_terms``. It runs only when a positive ``offset``
    arrives WITH an ``orderBy`` AND the field captured an ``OrderSet`` to
    normalize through, so every other argument-bearing request - a ``limit``
    alone, ``offset: 0``, positive offset riding model ``Meta.ordering`` - has
    nothing to hand over and does not pay for the scope. One conditional
    context, chosen here, keeps both colorings' pipelines identical in shape and
    the cost on the path that uses it.

    ``orderset_class`` is the field's captured sidecar, so the no-``OrderSet``
    condition is decidable here rather than asserted: over the wire that target
    publishes no ``orderBy`` at all, and the direct call that supplies one
    reaches the rejection in
    ``django_strawberry_framework/utils/querysets.py::require_orderset_class``
    without having opened a scope first.
    """
    if (
        args_record.order_by_supplied
        and orderset_class is not None
        and args_record.offset is not None
        and args_record.offset > 0
    ):
        # Deferred: ``orders`` stays out of the package-root import graph.
        from .orders.sets import capture_applied_order_normalization  # noqa: PLC0415 - keeps orders/filters out of the root graph

        return capture_applied_order_normalization()
    return contextlib.nullcontext()


#: The ``SyncMisuseError`` recourse ``_execute_queryset_pipeline_sync`` appends when
#: the target's ``get_queryset`` is ``async def``: the field is driven by the
#: synchronous executor, and the asynchronous one awaits the same hook on every
#: resolver shape.
_LIST_FIELD_ASYNC_RECOURSE = (
    "A DjangoListField runs its synchronous pipeline under schema.execute_sync(), "
    "which cannot await an async get_queryset hook; run the operation with await "
    "schema.execute() (or the async view), or redefine get_queryset as a sync method."
)


def _execute_queryset_pipeline_sync(
    target_type: type[DjangoType],
    source: models.QuerySet[models.Model, object],
    info: Info[object, object],
    args_record: _ListArguments,
    max_rows: int | None,
    *,
    trusted_max_rows: bool,
    model: type[models.Model],
    orderset_class: type[OrderSet] | None,
) -> object:
    post_vis_qs = apply_type_visibility_sync(
        target_type,
        source,
        info,
        async_recourse=_LIST_FIELD_ASYNC_RECOURSE,
        model=model,
    )
    if not args_record.any_argument_supplied:
        return _windowed_rows(post_vis_qs, info, max_rows, trusted=trusted_max_rows)

    # One task-local capture scope spans public ordering and the offset guard,
    # so the base ``OrderSet`` can hand its normalized terms to the guard without
    # writing into the consumer's ``info.context`` - opened only when that
    # handoff can happen.
    with _order_normalization_scope(args_record, orderset_class):
        if args_record.order_by_supplied:
            post_order_qs = apply_orderset_sync(
                target_type,
                orderset_class,
                post_vis_qs,
                args_record.order_by,
                info,
                model=model,
            )
        else:
            post_order_qs = post_vis_qs

        _check_nonzero_offset_guard(post_order_qs, args_record, orderset_class, info)

    return _windowed_rows(
        post_order_qs,
        info,
        max_rows,
        trusted=trusted_max_rows,
        offset=args_record.offset,
        requested_limit=args_record.limit,
    )


async def _execute_queryset_pipeline_async(
    target_type: type[DjangoType],
    source: models.QuerySet[models.Model, object],
    info: Info[object, object],
    args_record: _ListArguments,
    max_rows: int | None,
    *,
    trusted_max_rows: bool,
    model: type[models.Model],
    orderset_class: type[OrderSet] | None,
) -> object:
    post_vis_qs = await apply_type_visibility_async(target_type, source, info, model=model)
    if not args_record.any_argument_supplied:
        bounded = _windowed_rows(post_vis_qs, info, max_rows, trusted=trusted_max_rows)
        return wrap_async_queryset_adapter(bounded)

    # One task-local capture scope spans public ordering and the offset guard,
    # so the base ``OrderSet`` can hand its normalized terms to the guard without
    # writing into the consumer's ``info.context`` - opened only when that
    # handoff can happen.
    with _order_normalization_scope(args_record, orderset_class):
        if args_record.order_by_supplied:
            post_order_qs = await apply_orderset_async(
                target_type,
                orderset_class,
                post_vis_qs,
                args_record.order_by,
                info,
                model=model,
            )
        else:
            post_order_qs = post_vis_qs

        _check_nonzero_offset_guard(post_order_qs, args_record, orderset_class, info)

    bounded = _windowed_rows(
        post_order_qs,
        info,
        max_rows,
        trusted=trusted_max_rows,
        offset=args_record.offset,
        requested_limit=args_record.limit,
    )
    return wrap_async_queryset_adapter(bounded)


def DjangoListField(  # noqa: N802  # PascalCase for graphene-django parity - consumer usage is `DjangoListField(BranchType)`
    target_type: type[_TargetT],
    *,
    resolver: Callable[..., object] | None = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
    max_rows: int | None = None,
    trusted_max_rows: bool = False,
) -> list[_TargetT]:
    """Build a non-Relay ``list[T]`` root Query field bound to a ``DjangoType``.

    The declared return type is the value the field resolves to, not the object
    returned: at run time this returns a ``StrawberryField``. The annotation states
    the resolved value, as ``strawberry.field``'s own overloads do, so a consumer's
    class-body ``rows: list[T] = DjangoListField(T)`` (or ``list[T] | None``)
    type-checks.

    Outer nullability comes from the class-attribute annotation: ``list[T]`` renders
    ``[T!]!`` and ``list[T] | None`` renders ``[T!]``. The default resolver pulls
    ``model._default_manager.all()`` and applies the target type's ``get_queryset``
    visibility hook in sync and async contexts. A custom ``resolver=`` overrides
    the default body; when its return value is a ``Manager`` or ``QuerySet``, the
    wrapper applies ``get_queryset``.

    Argument surface:
    - Every ``DjangoListField`` publishes nullable optional ``offset`` and ``limit``
      arguments (GraphQL ``Int``).
    - When the target ``DjangoType`` declares ``Meta.orderset_class``, a typed
      ``orderBy`` argument is conditionally published. Targets without an orderset
      publish only ``offset`` and ``limit``.
    - Wire argument names follow the active schema naming converter (by default
      camelCase ``offset``, ``limit``, ``orderBy``; with ``auto_camel_case=False``,
      ``order_by``).

    Ordering contract (strictly ordered offset):
    A ``DjangoListField`` provides ordered-offset paging, NOT stable or repeatable
    pagination. An active order fixes the sort expression, not which of two tied rows
    falls on either side of a page boundary. Unlike Relay connection fields, which
    make their order total (appending a primary-key tiebreaker unless the order
    already ends in a unique column), flat lists inject no tiebreaker and no
    ``DISTINCT``. Consumers wanting deterministic pagination across pages with
    duplicate values must add a unique final term to the ordering themselves.

    Non-zero offset precondition:
    A published ``offset`` argument is a runtime precondition rather than a per-field
    capability claim. Usable only where an order source exists, ``offset > 0``
    requires a materially active order on the post-visibility queryset -- either a
    supplied ``orderBy`` with surviving non-null ordering terms, or a still-effective
    model ``Meta.ordering``. On a target with neither ``Meta.orderset_class`` nor
    still-effective model ``Meta.ordering``, positive offset values permanently raise
    ``ListArgumentError`` with ``reason="order_required"``.

    Row bounds and ceilings:
    Every ``DjangoListField`` is bounded. The effective row bound is the minimum of
    the client ``limit``, the field's ``max_rows``, and the request
    ``ResourcePolicy.max_list_rows`` (with ``trusted_max_rows=True`` permitting
    field-declared widening). Client ``offset`` is bounded by the request's
    ``ResourcePolicy.max_list_rows``. Both ceilings are accepted-coordinate ceilings,
    not physical database scan budgets. Exceeding either ceiling raises
    ``ListArgumentError`` with ``reason="over_ceiling"``.

    Async execution:
    Under asynchronous execution, querysets are completed through the package-internal
    async-only completion adapter, preventing synchronous event-loop iteration during
    GraphQL result execution while preserving query optimization.

    Optimizer cooperation rides the root-gated optimizer extension hook, so
    root-position list selections receive automatic select_related / prefetch_related
    / only planning.
    """
    if max_rows is not None:
        validate_collection_bound(max_rows, field="DjangoListField max_rows")
    validate_trusted_flag(trusted_max_rows, field="DjangoListField trusted_max_rows")
    # ONE definition read for the whole field: the validator's read is what the
    # signature, the SDL, the default seed, both visibility seals, and every
    # resolver dispatch below run on.
    definition = _validate_djangotype_target(target_type, resolver, field="DjangoListField")
    # The validator proved ``definition.origin is target_type``; the origin is the
    # typed spelling of the same class.
    node_type = definition.origin
    target_model = _model_from_definition(definition)
    orderset_class = _orderset_class_from_definition(definition)
    directives = validated_field_directives("DjangoListField", directives)

    # Factory-site async commitment (spec-020 Decision 3; spec-020 Decision 2
    # "Async-detection asymmetry - intentional, not a harmonization candidate"):
    # ``_default`` reads the operation's executor per call
    # (``utils/execution_mode.py::async_execution``) so the same factory output
    # dispatches correctly under both ``schema.execute_sync`` and
    # ``await schema.execute``. The consumer-wrapper branch below commits
    # per-construction via ``is_async_callable(user_resolver)`` (contract in
    # ``utils/typing.py::is_async_callable``) because Strawberry inspects the
    # resolver signature once at schema construction and freezes the
    # sync-vs-async handling.
    #
    # That commitment is per-RESOLVER, not per-request, so the sync wrapper is
    # the one that runs when a sync consumer resolver is executed under the
    # asynchronous executor - and on that path it returns a value graphql-core
    # completes asynchronously rather than a finished list: the queryset branch
    # returns ``_execute_queryset_pipeline_async``'s coroutine, exactly as
    # ``_default`` does, and the async-only-iterable branch returns
    # ``_resolve_async_iterable``'s coroutine, which the field executor awaits.
    # Neither is a slip. The alternative is running the ordering sidecar's
    # permission checks, ORM iteration or an async generator from a sync frame
    # on the event-loop thread, which is what the async pipeline exists to
    # avoid. Code reaching past the executor to ``field.base_resolver`` under a
    # running loop owes the return value the same completion the executor gives
    # it.
    if resolver is None:

        def _default(
            *args: object,
            offset: object = None,
            limit: object = None,
            order_by: object = UNSET,
            **kwargs: object,
        ) -> object:
            _, info, args_record = _argument_record(
                args,
                kwargs,
                max_rows=max_rows,
                trusted_max_rows=trusted_max_rows,
                offset=offset,
                limit=limit,
                order_by=order_by,
            )
            qs = base_queryset(target_model)
            if async_execution():
                return _execute_queryset_pipeline_async(
                    node_type,
                    qs,
                    info,
                    args_record,
                    max_rows,
                    trusted_max_rows=trusted_max_rows,
                    model=target_model,
                    orderset_class=orderset_class,
                )
            return _execute_queryset_pipeline_sync(
                node_type,
                qs,
                info,
                args_record,
                max_rows,
                trusted_max_rows=trusted_max_rows,
                model=target_model,
                orderset_class=orderset_class,
            )

        wrapped = _default
    else:
        user_resolver = resolver

        async def _resolve_async_iterable(
            source: object,
            info: Info[object, object],
            args_record: _ListArguments,
        ) -> object:
            if args_record.any_argument_supplied:
                await _handle_non_queryset_rejections_async(
                    source,
                    args_record,
                    info,
                    orderset_class=orderset_class,
                )
            return await _windowed_rows_async(
                source,
                info,
                max_rows,
                trusted=trusted_max_rows,
                offset=args_record.offset,
                requested_limit=args_record.limit,
            )

        # Each wrapper is built in its own scope: one is a coroutine function and the
        # other is not, and both keep ``_wrap`` as the resolver name Strawberry reads.
        def _async_wrap(
            async_resolver: Callable[..., Coroutine[object, Never, object]],
        ) -> Callable[..., object]:

            async def _wrap(
                *args: object,
                offset: object = None,
                limit: object = None,
                order_by: object = UNSET,
                **kwargs: object,
            ) -> object:
                root, info, args_record = _argument_record(
                    args,
                    kwargs,
                    max_rows=max_rows,
                    trusted_max_rows=trusted_max_rows,
                    offset=offset,
                    limit=limit,
                    order_by=order_by,
                )
                raw_source = await async_resolver(root, info)
                prepared = prepared_resolver_source(
                    raw_source,
                    node_type,
                    async_guard=reject_residual_async_source,
                )
                source = prepared[0]
                if prepared[1] is True:
                    return await _execute_queryset_pipeline_async(
                        node_type,
                        prepared[0],
                        info,
                        args_record,
                        max_rows,
                        trusted_max_rows=trusted_max_rows,
                        model=target_model,
                        orderset_class=orderset_class,
                    )
                return await _resolve_async_iterable(source, info, args_record)

            return _wrap

        def _sync_wrap() -> Callable[..., object]:

            def _wrap(
                *args: object,
                offset: object = None,
                limit: object = None,
                order_by: object = UNSET,
                **kwargs: object,
            ) -> object:
                root, info, args_record = _argument_record(
                    args,
                    kwargs,
                    max_rows=max_rows,
                    trusted_max_rows=trusted_max_rows,
                    offset=offset,
                    limit=limit,
                    order_by=order_by,
                )
                source = user_resolver(root, info)
                if is_async_only_iterable(source):
                    reject_async_iterable_in_sync_context(
                        source,
                        flavor_noun="DjangoListField",
                        async_executor=operation_is_async(),
                    )
                    return _resolve_async_iterable(
                        source,
                        info,
                        args_record,
                    )
                prepared = prepared_resolver_source(
                    source,
                    node_type,
                    async_guard=reject_awaitable_sync_source,
                )
                source = prepared[0]
                if prepared[1] is True:
                    if async_execution():
                        return _execute_queryset_pipeline_async(
                            node_type,
                            prepared[0],
                            info,
                            args_record,
                            max_rows,
                            trusted_max_rows=trusted_max_rows,
                            model=target_model,
                            orderset_class=orderset_class,
                        )
                    return _execute_queryset_pipeline_sync(
                        node_type,
                        prepared[0],
                        info,
                        args_record,
                        max_rows,
                        trusted_max_rows=trusted_max_rows,
                        model=target_model,
                        orderset_class=orderset_class,
                    )
                rejection = _build_non_queryset_rejection_error(
                    args_record,
                    info,
                    orderset_class=orderset_class,
                )
                if rejection is not None:
                    raise rejection
                return _windowed_rows(
                    source,
                    info,
                    max_rows,
                    trusted=trusted_max_rows,
                    offset=args_record.offset,
                    requested_limit=args_record.limit,
                )

            return _wrap

        wrapped = _async_wrap(user_resolver) if is_async_callable(user_resolver) else _sync_wrap()

    signature, annotations = _synthesized_list_signature(orderset_class)
    wrapped.__signature__ = signature
    wrapped.__annotations__ = annotations

    # The field object stands in for the value it resolves to (see the docstring).
    return cast(
        "list[_TargetT]",
        strawberry.field(
            resolver=wrapped,
            description=description,
            deprecation_reason=deprecation_reason,
            directives=directives,
        ),
    )
