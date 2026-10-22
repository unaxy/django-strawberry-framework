"""``DjangoType`` - Meta-class-driven Django-model-to-Strawberry-type adapter.

Consumer surface::

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = "__all__"

A nested ``Meta`` class declares the model and (optionally) ``fields``,
``exclude``, ``name``, ``description``, ``optimizer_hints``,
``interfaces``, ``nullable_overrides``, ``required_overrides``,
``connection``, ``cursor_field``, ``filterset_class``,
``orderset_class``, ``globalid_strategy``, ``relation_shapes``,
``filesystem_path_fields``, and ``primary`` - see ``ALLOWED_META_KEYS`` for
the authoritative set.

Selection lives in ``Meta.fields`` / ``Meta.exclude``. A field may also be
written as a class annotation ``name: auto`` ("declare-but-infer"): the name
must still be selected via ``Meta.fields``, and its GraphQL type is synthesized
from the Django field exactly as bare selection would. ``auto`` never adds a
field; it only lets a selected field appear as a class annotation alongside
sibling overrides (or for IDE/type-checker visibility).

Subclassing
triggers the collection pipeline, which:

1. Detects whether the subclass declares its own ``Meta``. Intermediate
   abstract subclasses without ``Meta`` are skipped so consumers can
   layer their own bases on top of ``DjangoType``.
2. Validates ``Meta`` (required Django model class, supported option
   shapes, ``fields``/``exclude`` exclusivity, deferred-key rejection,
   relation-only optimizer hints, and interfaces).
3. Selects Django fields and builds a ``DjangoTypeDefinition``.
4. Synthesizes scalar annotations and records unresolved relations as
   pending records.
5. Registers the model/type pair for a later ``finalize_django_types()``
   pass.
"""

import inspect
import re
import typing
from collections.abc import Callable, Mapping, Sequence
from collections.abc import Set as AbstractSet
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Literal,
    NamedTuple,
    TypeVar,
    cast,
)

from django.db import models
from django.utils.functional import Promise
from strawberry import relay
from strawberry.relay.types import NodeIDPrivate
from strawberry.types.auto import StrawberryAuto
from strawberry.types.field import StrawberryField
from strawberry.types.object_type import StrawberryObjectDefinition
from typing_extensions import override

from django_strawberry_framework.conf import RELAY_GLOBALID_STRATEGY_KEY
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.keyset import validate_cursor_field_references
from django_strawberry_framework.optimizer.field_meta import FieldMeta
from django_strawberry_framework.optimizer.hints import OptimizerHint
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import dict_of, list_of
from django_strawberry_framework.utils.relations import is_single_column_foreign_key
from django_strawberry_framework.utils.typing import is_async_callable

from .converters import _field_output_type_for, convert_field_output
from .definition import _GRAPHQL_NAME_RE, DjangoTypeDefinition
from .relations import PendingRelation, PendingRelationAnnotation
from .relay import install_is_type_of

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typing_extensions import TypeIs

    from django_strawberry_framework.filters.sets import FilterSet
    from django_strawberry_framework.orders.sets import OrderSet
    from django_strawberry_framework.utils.typing import ConcreteField, ModelField

    from .definition import GlobalIDStrategy

_SidecarT = TypeVar("_SidecarT")

DEFERRED_META_KEYS: frozenset[str] = frozenset(
    {"aggregate_class", "fields_class", "search_fields"},
)

ALLOWED_META_KEYS: frozenset[str] = frozenset(
    {
        "connection",
        "cursor_field",
        "description",
        "exclude",
        "fields",
        "filesystem_path_fields",
        "filterset_class",
        "globalid_strategy",
        "interfaces",
        "model",
        "name",
        "nullable_overrides",
        "optimizer_hints",
        "orderset_class",
        "primary",
        "relation_shapes",
        "required_overrides",
        # Declarative visibility prototype (whitepaper section 11 steps 1-2):
        # ``visibility`` is a sequence of ``rules.Rule``; ``cascade`` is the
        # opt-out of the forward-FK cascade that is on by default once rules
        # exist; ``blessed`` is the stated reason a hand-written ``get_queryset``
        # body stays in Python, which moves it from the audit's O to its B.
        "visibility",
        "cascade",
        "blessed",
    },
)
# ``filesystem_path_fields`` (spec-048 Decision 2),
# ``nullable_overrides`` / ``required_overrides`` (spec-029 Decision 6),
# ``connection`` (spec-030 Decision 8), ``globalid_strategy`` (spec-031
# Decision 6), ``relation_shapes`` (spec-032 Decision 7), and
# ``cursor_field`` (the spec-030 ``## Keyset cursors``
# opt-in) are net-new ALLOWED keys, NOT DEFERRED_META_KEYS promotions -
# each one's feature ships in the same card that adds it, so they were
# never reserved-but-nonfunctional. DEFERRED_META_KEYS stays unchanged.

# The valid relation-shape vocabulary and the package default: the single
# source of both (spec-032 Decision 7). Mirrors the
# ``STRING_GLOBALID_STRATEGIES`` / ``DEFAULT_GLOBALID_STRATEGY`` precedent below.
RELATION_SHAPE_VALUES: frozenset[str] = frozenset({"list", "connection", "both"})
# ``"connection"`` is the secure default (spec-047 Decision 5): a raw many-side
# list has no cursor and therefore no page of its own, so emitting one BESIDE the
# bounded connection hands a client a way around the connection's cap by
# selecting the sibling. A raw many-side list is an explicit
# ``Meta.relation_shapes`` opt-in, and the one it opts into is row-bounded
# (``resource_policy.py::bounded_rows``) rather than unbounded.
DEFAULT_RELATION_SHAPE = "connection"

# The Relay-Node-gate lead-in: every ``Meta``-key gate composes this one
# literal by name, as does ``global_id_for`` in ``testing/relay.py`` - the
# ``_INTERFACES_SHAPE_ERROR_LEAD_IN`` precedent. Every gate appends
# ``_RELAY_NODE_GATE_INHERIT_TAIL`` but the relation_shapes gate, which
# appends the spec-pinned "or remove the key." (spec-032 Decision 7).
_RELAY_NODE_GATE_LEAD = "requires a Relay-Node-shaped type; add `relay.Node` to `Meta.interfaces`"
# The tail appended beside the lead-in by every gate but the relation_shapes
# gate, and by ``global_id_for`` in ``testing/relay.py``: byte-identical at
# every compose site. The ``_validate_relation_shapes`` gate's "or remove the
# key." tail and the parenthesized fifth-guard variants in ``relay.py`` /
# ``connection.py`` are a different byte shape and stay inline.
_RELAY_NODE_GATE_INHERIT_TAIL = "or inherit `relay.Node` directly."

# The valid string-strategy set and the package default are the single source
# of truth for the CONFIGURABLE GlobalID-encoding strategy vocabulary, what a
# consumer may declare (spec-031 Decisions 4/5/6). What each strategy emits or
# accepts is a separate contract, the payload-shape memberships in
# ``types/relay.py``, sharing an extension today. ``callable`` strategies are
# validated separately (arity + sync-ness), so they are not part of the string set.
STRING_GLOBALID_STRATEGIES: frozenset[str] = frozenset({"model", "type", "type+model"})
DEFAULT_GLOBALID_STRATEGY = "model"


def _validate_set_sidecar(
    model: type[models.Model],
    sidecar_class: object,
    *,
    expected: type[_SidecarT],
    meta_key: str,
    article: str,
) -> type[_SidecarT]:
    """Return ``sidecar_class`` if it is an ``expected`` subclass, else raise.

    The type-gate skeleton ``Meta.filterset_class`` and ``Meta.orderset_class``
    share. Wrappers keep the cycle-safe local import of ``FilterSet`` /
    ``OrderSet`` in their own body and the ``None``-means-unset
    short-circuit; this owns only the subclass check and the
    ``must be {article} {expected.__name__} subclass`` wording.
    """
    if not truth.is_subclass(sidecar_class, expected):
        raise ConfigurationError(
            f"{truth.name(model)}.Meta.{meta_key} must be {article} {truth.name(expected)} subclass; "
            f"got {truth.render(sidecar_class)}",
        )
    return sidecar_class


def _validate_filterset_class(
    model: type[models.Model],
    filterset_class: object,
) -> "type[FilterSet] | None":
    """Validate ``Meta.filterset_class`` is a package-``FilterSet`` subclass.

    Local import of ``FilterSet`` at function scope keeps ``types/base.py``
    free of a module-load cycle through ``filters.sets`` (which imports
    ``types.relay`` which imports ``types.base``). Validation runs at
    ``_validate_meta`` time - well after both modules have completed
    module load - so the local import resolves cheaply.

    Returns ``None`` when the meta does not declare ``filterset_class``;
    raises ``ConfigurationError`` for non-``FilterSet`` values.
    """
    if filterset_class is None:
        return None
    # In-function import: dodges the `types -> filters -> types` module-load
    # cycle. Do NOT hoist to module top.
    from django_strawberry_framework.filters.sets import FilterSet  # noqa: PLC0415 - import cycle

    return _validate_set_sidecar(
        model,
        filterset_class,
        expected=FilterSet,
        meta_key="filterset_class",
        article="a",
    )


def _validate_orderset_class(
    model: type[models.Model],
    orderset_class: object,
) -> "type[OrderSet] | None":
    """Validate ``Meta.orderset_class`` is a package-``OrderSet`` subclass.

    Local import of ``OrderSet`` at function scope keeps ``types/base.py``
    free of a module-load cycle through ``orders.sets`` (which imports
    ``..types.definition`` under ``TYPE_CHECKING`` and would close the
    cycle at module-load time if the import were hoisted to module
    scope). Validation runs at ``_validate_meta`` time -- well after
    both modules have completed module load -- so the local import
    resolves cheaply.

    Returns ``None`` when the meta does not declare ``orderset_class``;
    raises ``ConfigurationError`` for non-``OrderSet`` values.
    """
    if orderset_class is None:
        return None
    # In-function import: dodges the `types -> orders -> types` module-load
    # cycle. Do NOT hoist to module top.
    from django_strawberry_framework.orders.sets import OrderSet  # noqa: PLC0415 - import cycle

    return _validate_set_sidecar(
        model,
        orderset_class,
        expected=OrderSet,
        meta_key="orderset_class",
        article="an",
    )


def _validate_connection(
    model: type[models.Model],
    connection: object,
    *,
    relay_shaped: bool,
) -> dict[str, bool] | None:
    """Validate ``Meta.connection`` shape AND the Relay-Node requirement (spec-030 Decision 8).

    ``None``-short-circuits when unset; otherwise shape-checks the dict (for
    ``0.0.9`` the only recognized sub-key is ``{"total_count": bool}`` - unknown
    sub-keys and non-dict / non-bool values raise) and then enforces that the
    owning type is Relay-Node-shaped (a connection is only meaningful over a
    Relay-Node type). Returns the normalized dict, stored on
    ``DjangoTypeDefinition.connection`` and read by
    ``connection.py::_connection_type_for``.

    The Relay-Node gate takes the precomputed ``relay_shaped`` bool - the
    canonical ``_is_relay_shaped(cls, interfaces)`` value the caller
    (``_validate_meta``) computes once ``cls`` is in hand. That predicate is
    True for BOTH the ``Meta.interfaces`` tuple spelling AND direct inheritance
    (``class Foo(DjangoType, relay.Node)``), so it matches the
    ``DjangoConnectionField`` field guard - "Relay-shaped" means the same thing
    across the whole feature. Taking the bool (not ``interfaces``) keeps the
    predicate single-sourced and prevents the two surfaces drifting apart again.
    """
    if connection is None:
        return None
    model_name = truth.name(model)
    if not truth.is_instance(connection, dict):
        raise ConfigurationError(
            f"{model_name}.Meta.connection must be a dict; got {truth.render(connection)}",
        )
    unknown = [key for key in connection if key != "total_count"]
    if unknown:
        unknown_labels = sorted(truth.render(key) for key in unknown)
        raise ConfigurationError(
            f"{model_name}.Meta.connection has unknown sub-keys: "
            f"[{', '.join(unknown_labels)}]. "
            "Only 'total_count' is recognized in 0.0.9.",
        )
    # The returned options are built from the checks: the one recognized key, under its
    # own exact name, holding the bool it was proven to be.
    options: dict[str, bool] = {}
    if "total_count" in connection:
        total_count = connection["total_count"]
        if not truth.is_exact(total_count, bool):
            raise ConfigurationError(
                f"{model_name}.Meta.connection['total_count'] must be a bool; "
                f"got {truth.render(total_count)}",
            )
        options["total_count"] = total_count
    if not relay_shaped:
        raise ConfigurationError(
            f"{model_name}.Meta.connection {_RELAY_NODE_GATE_LEAD} "
            f"{_RELAY_NODE_GATE_INHERIT_TAIL}",
        )
    return options


def _is_str_tuple(entries: tuple[object, ...]) -> "TypeIs[tuple[str, ...]]":
    """Return whether every entry of ``entries`` is a ``str``."""
    return all(truth.is_instance(entry, str) for entry in entries)


def _validate_cursor_field(
    model: type[models.Model],
    value: object,
    *,
    relay_shaped: bool,
) -> tuple[str, ...] | None:
    """Validate ``Meta.cursor_field`` SHAPE and the Relay-Node gate (keyset cursors).

    Class-creation stage of the spec-030 ``## Keyset cursors`` two-stage validation
    (the spec-029 two-stage precedent): ``None``-short-circuits when unset;
    otherwise requires a non-empty string sequence whose entries parse as
    Django ``order_by`` strings over LOCAL columns (one optional leading
    ``-``; no ``__`` relation traversal; no duplicate columns), then applies
    the same Relay-Node gate as ``Meta.connection`` - keyset cursors only
    mean anything on a connection-capable type. Column-level checks
    (existence, concreteness, non-nullability, unique terminal) need the
    settled model field surface and run at finalization via
    ``keyset.validate_cursor_field_columns``.
    """
    if value is None:
        return None
    owner = f"{truth.name(model)}.Meta.cursor_field"
    is_sequence = not truth.is_instance(value, str) and issubclass(truth.class_of(value), Sequence)
    # ``is_sequence`` read the value's real class as a ``Sequence``.
    entries = tuple(list_of(value)) if is_sequence else ()
    if not entries or not _is_str_tuple(entries):
        raise ConfigurationError(
            f"{owner} must be a non-empty non-string sequence of order strings; "
            f"got {truth.render(value)}",
        )
    _ = validate_cursor_field_references(entries, owner=owner)
    if not relay_shaped:
        raise ConfigurationError(
            f"{owner} {_RELAY_NODE_GATE_LEAD} {_RELAY_NODE_GATE_INHERIT_TAIL}",
        )
    return entries


def _validate_relation_shapes(
    model: type[models.Model],
    value: object,
    *,
    relay_shaped: bool,
) -> dict[str, str] | None:
    """Validate ``Meta.relation_shapes`` shape AND the Relay-Node requirement (spec-032 Decision 7).

    Stage 1 of the relation-shapes validation flow, structurally modeled on
    ``_validate_connection`` and called from ``_validate_meta``:
    ``None``-short-circuits when unset (every eligible relation defaults to
    ``DEFAULT_RELATION_SHAPE`` at the Phase-2.5 synthesis); shape-checks the
    dict (string keys, values in ``RELATION_SHAPE_VALUES``); then enforces the
    Relay-Node gate with the spec-pinned "or remove the key" remediation tail.

    Field-level checks (unknown / excluded / non-relation / single-valued /
    consumer-authored) need the selected fields and the consumer-override
    union, which do not exist at ``_validate_meta`` time - they run in stage 2,
    ``_validate_relation_shape_targets``, from ``__init_subclass__`` (the
    spec-029 ``nullable_overrides`` two-stage precedent). The
    target-is-Node-shaped check runs at finalization, where relation targets
    are settled (Decision 6).

    Returns the normalized dict, stored on
    ``DjangoTypeDefinition.relation_shapes`` and read by the Phase-2.5
    relation-as-Connection synthesis.
    """
    if value is None:
        return None
    model_name = truth.name(model)
    if not truth.is_instance(value, dict):
        raise ConfigurationError(
            f"{model_name}.Meta.relation_shapes must be a dict mapping relation "
            f"field names to shapes; got {truth.render(value)}",
        )
    shapes: dict[str, str] = {}
    for key, shape in value.items():
        if not truth.is_instance(key, str):
            raise ConfigurationError(
                f"{model_name}.Meta.relation_shapes keys must be relation field "
                f"name strings; got {truth.render(key)}.",
            )
        # The ``str`` test comes first so an unhashable value (e.g. ``{"items":
        # ["both"]}``) raises the configured ConfigurationError rather than
        # leaking ``TypeError: unhashable type`` from the set membership.
        if not truth.is_instance(shape, str) or shape not in RELATION_SHAPE_VALUES:
            raise ConfigurationError(
                f"{model_name}.Meta.relation_shapes[{truth.render(key)}] "
                f"got unknown shape {truth.render(shape)}; valid shapes are "
                f"{sorted(RELATION_SHAPE_VALUES)}.",
            )
        shapes[key] = shape
    if not relay_shaped:
        raise ConfigurationError(
            f"{model_name}.Meta.relation_shapes {_RELAY_NODE_GATE_LEAD} or remove the key.",
        )
    return shapes


# The three positional parameters a ``callable`` GlobalID encoder must accept.
# The callable runs at encode time, BEFORE ``resolve_id``, so it never receives
# ``node_id``. ``info`` was dropped pre-1.0 (this is unpublished): a callable
# encoder is a deterministic pure per-(type, object) function, and withholding
# ``info`` prevents easy request/actor dependence (it cannot prevent I/O -
# purity stays the consumer's obligation). Named once so the validator's error
# text and the install closure stay in lockstep.
_GLOBALID_CALLABLE_PARAMS = ("type_cls", "model", "root")


def _validate_globalid_strategy(
    model: type[models.Model] | None,
    value: object,
    *,
    relay_shaped: bool,
    source: str = "meta",
) -> "GlobalIDStrategy | None":
    """Validate one ``globalid_strategy``-shaped value and return the normalized form.

    The single validator shared by BOTH the ``Meta.globalid_strategy`` path
    (via ``_validate_meta``) and the ``RELAY_GLOBALID_STRATEGY`` setting path
    (via ``types/relay.py::_validated_globalid_setting``, the finalizer's
    once-per-finalization setting snapshot) - spec-031 Decisions
    6/7's "one validator, two sources, source-specific error text" rule. The
    callable arity / sync-ness check lives here once so it is never duplicated
    across the two call sites.

    Structurally modeled on ``_validate_connection``: ``None``-short-circuits
    when unset; a string must be in ``STRING_GLOBALID_STRATEGIES`` (typo guard);
    a callable must accept the three positional ``_GLOBALID_CALLABLE_PARAMS`` and
    must NOT be ``async def`` (an opaque ``TypeError`` / coroutine per request is
    promoted to a build-time ``ConfigurationError``); any other type raises.

    ``model`` selects the error framing: a model names the offending type by
    its class name; ``None`` names ``RELAY_GLOBALID_STRATEGY``. ``source``
    selects the gate: ``"meta"`` (the default) enforces the Relay-Node-shape
    gate; ``"setting"`` skips it (the per-type gate already ran at type
    creation, so the setting path passes ``relay_shaped=True`` and
    ``model=None``).
    """
    if value is None:
        return None
    is_meta = source == "meta"
    # Only the setting path (``source="setting"``) passes ``model=None``.
    subject = (
        f"{truth.name(model)}.Meta.globalid_strategy"
        if model is not None
        else RELAY_GLOBALID_STRATEGY_KEY
    )
    if truth.is_instance(value, str):
        if value not in STRING_GLOBALID_STRATEGIES:
            raise ConfigurationError(
                f"{subject} got unknown strategy {truth.render(value)}; "
                f"valid strategies are {sorted(STRING_GLOBALID_STRATEGIES)} or a callable.",
            )
        normalized: GlobalIDStrategy = value
    elif callable(value):
        _validate_globalid_callable(subject, value)
        normalized = value
    else:
        raise ConfigurationError(
            f"{subject} must be one of {sorted(STRING_GLOBALID_STRATEGIES)} or a callable; "
            f"got {truth.render(value)}.",
        )
    # The Relay-Node-shape gate is a ``Meta``-only concern (the setting path's
    # per-type gate already ran at type creation); mirrors
    # ``_validate_connection``'s gate and remediation text.
    if is_meta and not relay_shaped:
        raise ConfigurationError(
            f"{subject} {_RELAY_NODE_GATE_LEAD} {_RELAY_NODE_GATE_INHERIT_TAIL}",
        )
    return normalized


def _validate_globalid_callable(subject: str, value: Callable[..., object]) -> None:
    """Reject a wrong-arity or async GlobalID encoder at validation time.

    ``inspect.signature`` must bind the three positional ``_GLOBALID_CALLABLE_PARAMS``
    and the encoder must be sync (spec-031 Decision 6).
    The sync-ness test (``utils/typing.py::is_async_callable``, shared with the
    field factories) sees through callable instances with
    an ``async def __call__`` and ``functools.partial`` wrappers around either an
    ``async def`` function or such an instance -- all of which
    ``inspect.iscoroutinefunction`` alone would miss, letting an async encoder
    survive to request time. A callable that survives both checks is returned to
    the caller untouched; the per-call non-``str`` return guard lives in the
    install closure.
    """
    if is_async_callable(value):
        raise ConfigurationError(
            f"{subject} callable encoder must be sync; "
            f"got an `async def`. Expected `(type_cls, model, root) -> str`.",
        )
    # ``inspect.signature`` documents ``ValueError`` (no signature available)
    # and ``TypeError`` (unsupported object); ``bind`` documents ``TypeError``
    # (the positional triple does not fit).
    try:
        _ = inspect.signature(value).bind(*_GLOBALID_CALLABLE_PARAMS)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"{subject} callable encoder must accept "
            f"`(type_cls, model, root) -> str`; got an incompatible signature ({exc}).",
        ) from exc


# Token-shaped NodeID matcher used by the string-form arm of
# ``_id_annotation_is_relay_node_id``. The ``(?:^|\.)`` anchor accepts both the
# qualified (``relay.NodeID[int]``) and unqualified (``NodeID[int]``) spellings
# while rejecting prefixed-substring lookalikes (``NotNodeID[int]``,
# ``MyNodeID[int]``). See ``_id_annotation_is_relay_node_id`` for the full
# string-vs-resolved rationale; the regex lives at module scope so the compile
# happens once at import time.
_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")


def _has_node_id_marker(hint: object) -> bool:
    """Return True when ``hint`` is ``Annotated[T, NodeIDPrivate()]``.

    In the installed Strawberry, ``relay.NodeID[T]`` IS
    ``typing.Annotated[T, NodeIDPrivate()]`` - the explicit ``Annotated``
    form and the ``relay.NodeID`` sugar collapse to the same shape, so
    ``typing.get_origin`` returns ``typing.Annotated`` for both and the
    ``NodeIDPrivate`` instance lives in ``typing.get_args(...)``'s
    metadata slot.
    """
    if typing.get_origin(hint) is not Annotated:
        return False
    args: tuple[object, ...] = typing.get_args(hint)
    return any(truth.is_instance(arg, NodeIDPrivate) for arg in args)


def _id_annotation_is_relay_node_id(cls: "type[DjangoType]") -> bool:
    r"""Return True when ``cls.__annotations__['id']`` is ``relay.NodeID[...]``.

    Reads ``cls.__annotations__`` directly - no ``typing.get_type_hints``
    call. The result does not depend on whether other annotations on the
    class resolve (an unrelated forward reference on a sibling attribute
    cannot mask the ``id`` annotation; pinned by
    ``tests/types/test_definition_order.py::test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted``),
    and the function's behavior is identical on every supported Python
    version (``typing.get_type_hints`` handles nested forward references
    differently across 3.10 vs 3.11+, so calling it would leave a code branch
    reachable only on the newer interpreter).

    Two annotation forms are accepted:

    1. **String form** (``id: "relay.NodeID[int]"`` or
       ``id: "NodeID[int]"``, typical under
       ``from __future__ import annotations`` or any explicit string
       annotation). Matched against ``(?:^|\.)NodeID\[`` - qualified and
       unqualified token-shaped NodeID references pass; prefixed-substring
       lookalikes (``"NotNodeID[int]"``, ``"MyNodeID[int]"``) and
       non-NodeID typos (``"MissingType"``) are rejected. Downstream
       Strawberry schema construction is responsible for resolving the
       string to a real ``NodeID[T]`` annotation; this function only
       confirms the shape so the H1 collision guard can accept the
       escape hatch at class-creation time.
    2. **Resolved-object form** (``id: relay.NodeID[int]``, evaluated at
       class-creation time). Delegated to ``_has_node_id_marker`` which
       checks for ``Annotated[T, NodeIDPrivate()]``.

    Precondition: ``"id" in cls.__annotations__``. The only call site
    (the Relay-id collision guard in ``DjangoType.__init_subclass__``)
    already gates on ``has_id_annotation`` before invoking this function,
    so the subscript below cannot ``KeyError`` from real flow. A future
    caller that violates the precondition gets a loud ``KeyError`` rather
    than a misleading ``False`` return.
    """
    raw = cls.__annotations__["id"]
    if truth.is_instance(raw, str):
        return bool(_NODEID_STRING_RE.search(truth.text(raw)))
    return _has_node_id_marker(raw)


def _is_relay_shaped(cls: "type[DjangoType]", interfaces: tuple[type[object], ...]) -> bool:
    """Return True when ``cls`` or any entry in ``interfaces`` is a Relay-Node-shaped type.

    Single source of truth for the Relay-shape predicate: every reader computes
    the same boolean from the same inputs at its own timing, so the contract
    stays single-sited.
    """
    return any(truth.is_subclass(i, relay.Node) for i in interfaces) or truth.is_subclass(
        cls,
        relay.Node,
    )


def _meta_attr(meta: object, key: str, default: object = None) -> object:
    """Read one declared ``Meta`` attribute (inherited ``Meta`` bases included).

    The value is read from the real namespaces of ``meta``'s MRO, so no
    metaclass ``__getattr__`` / ``__getattribute__`` or descriptor runs; a
    declared value comes back exactly as the class body stored it, with one
    exception: a ``staticmethod`` wrapper comes back as the function it wraps,
    which is what reading the attribute off the class returns. The wrapper is
    recognised by its exact builtin class, so its ``__func__`` slot is the
    interpreter's own and no consumer code runs to read it.
    """
    value = truth.static_attr(meta, key, default)
    if truth.is_exact(value, staticmethod):
        return value.__func__
    return value


def _is_auto_annotation(annotation: object) -> bool:
    """Return True for the ``field: auto`` declare-but-infer marker, every spelling.

    Recognized: the ``StrawberryAuto`` instance, the string ``"auto"``, and the
    string ``"strawberry.auto"``.

    The instance form is what a plain consumer module stores in
    ``cls.__annotations__``. Under ``from __future__ import annotations``
    (PEP 563) raw annotation values are never evaluated, so the marker
    reaches ``__init_subclass__`` as a STRING - the same string-annotation
    reality ``_id_annotation_is_relay_node_id`` already accounts for on the
    Relay-id path. Both source spellings survive into that string verbatim:
    ``field: auto`` (from ``from strawberry import auto``) becomes "auto",
    and ``field: strawberry.auto`` becomes "strawberry.auto". An explicit
    string annotation in a non-PEP 563 module asks for the same marker, so
    the string forms match there too.

    The dotted form is accepted ONLY under the ``strawberry`` prefix: an
    arbitrary ``x.auto`` is some other module's or class's attribute and must
    keep its ordinary annotation meaning rather than silently becoming the
    infer marker. Aliased imports (``import strawberry as sb``) are not
    recognized - resolving those would require evaluating the annotation
    against the defining module's namespace, which PEP 563 exists to avoid.
    """
    # ``strawberry.auto`` is ``Annotated[Any, StrawberryAuto()]``; Strawberry's
    # own ``StrawberryAuto`` metaclass ``__instancecheck__`` recognizes that
    # alias, so the protocol check stays ``isinstance``.
    if isinstance(annotation, StrawberryAuto):
        return True
    return truth.is_instance(annotation, str) and truth.text(annotation) in (
        "auto",
        "strawberry.auto",
    )


class DjangoType:
    """Base class for Django-model-backed Strawberry GraphQL types."""

    _is_default_get_queryset: ClassVar[bool] = True
    # Declarative visibility prototype: ``Meta.visibility`` rules and the
    # ``Meta.cascade`` opt-out, stamped by ``__init_subclass__``; read by
    # ``rules/apply.py`` and ``rules/audit.py``.
    __visibility_rules__: ClassVar[tuple[object, ...]] = ()
    __cascade__: ClassVar[bool | None] = None
    __blessed__: ClassVar[str | None] = None
    # ``True`` when the consumer wrote a ``get_queryset`` body on this type or an
    # ancestor, whatever rules are declared beside it (the audit reads this; the
    # ``has_custom_get_queryset`` flag below is also flipped by declared rules).
    __overrides_get_queryset__: ClassVar[bool] = False
    # ``True`` when any rule (type, model mixin, or cascade opt-out) reaches the
    # type: the default hook's fast path reads this flag and nothing else.
    __declares_visibility__: ClassVar[bool] = False
    # Set by ``__init_subclass__`` on every subclass that declares ``Meta``.
    __django_strawberry_definition__: ClassVar[DjangoTypeDefinition]
    # Installed alongside it by ``types/relay.py::install_is_type_of``.
    is_type_of: ClassVar[Callable[[object, object], bool]]
    if TYPE_CHECKING:
        # Rebuilt by ``__init_subclass__`` as the synthesized fields plus the
        # consumer's own; declared so checkers read it as the ``object`` attribute
        # it overrides, and never executed so the class records no such annotation.
        __annotations__: dict[str, object]

    @override
    def __init_subclass__(cls, **kwargs: object) -> None:
        """Collect model/type metadata without finalizing the Strawberry type."""
        super().__init_subclass__(**kwargs)
        # The ``_is_default_get_queryset`` sentinel must be stamped BEFORE the
        # ``meta is None`` early-return and the finalized-registry guard so an
        # abstract base that overrides ``get_queryset`` without declaring Meta
        # still flips the flag - concrete subclasses inheriting from it then
        # report ``has_custom_get_queryset() is True`` correctly. Pinned by
        # ``test_has_custom_get_queryset_inherits_through_abstract_base_without_meta``.
        has_custom_get_queryset = truth.overrides(cls, DjangoType, "get_queryset")
        cls._is_default_get_queryset = not has_custom_get_queryset
        # The class's own namespace, read from the interpreter: an inherited
        # ``Meta`` does not make an intermediate base concrete.
        meta: object = truth.class_dict(cls).get("Meta")
        if meta is None:
            return
        # Identity facts about ``cls`` are read once, here, from the
        # interpreter; every message below names the class by this value.
        type_name = truth.name(cls)
        if registry.is_finalized():
            raise ConfigurationError(
                f"finalize_django_types() already ran; cannot register {type_name} "
                "after finalization. Call registry.clear() first if this is a test.",
            )
        validated = _validate_meta(cls, meta)
        model = validated.model
        visibility_rules, cascade = _validate_visibility(cls, meta)
        cls.__visibility_rules__ = visibility_rules
        cls.__cascade__ = cascade
        cls.__blessed__ = _validate_blessed(cls, meta, has_custom_get_queryset)
        cls.__overrides_get_queryset__ = has_custom_get_queryset
        cls.__declares_visibility__ = _declares_visibility(cls, model)
        if cls.__declares_visibility__:
            # Declared rules make the default hook a real filter, so every
            # reader that asks "does this type scope its rows?" (the optimizer's
            # select_related downgrade, the cascade) must hear yes.
            has_custom_get_queryset = True
            cls._is_default_get_queryset = False
        fields = _select_fields(model, validated.fields_spec, validated.exclude_spec)
        _validate_optimizer_hints(validated.optimizer_hints, fields, model=model)

        field_map = {f.name: FieldMeta.from_django_field(f) for f in fields}
        consumer_annotations = dict(cls.__annotations__)
        # Class-body syntax can only produce string annotation keys, but a
        # metaclass may inject arbitrary keys into the namespace before
        # ``type.__new__`` runs. Downstream every annotation key is treated as
        # a field NAME (membership tests, ``sorted`` over the auto-name sets,
        # the final ``{**synthesized, **consumer_annotations}`` merge), so a
        # non-string key would raise raw ``TypeError``/``KeyError`` from those
        # walks. The string-keys contract is validated HERE, once, at the
        # collection boundary, so the walks below see only field names.
        annotation_keys: Iterable[object] = consumer_annotations
        non_string_annotation_keys = sorted(
            truth.render(key) for key in annotation_keys if not truth.is_instance(key, str)
        )
        if non_string_annotation_keys:
            raise ConfigurationError(
                f"{type_name}: class annotations must have string names; got non-string "
                f"keys [{', '.join(non_string_annotation_keys)}]. Annotation keys are field names; "
                "non-string keys cannot be synthesized or exposed.",
            )
        # ``field: auto`` is the "declare-but-infer" marker (the fifth corner of the
        # override surface): the field is written as a class annotation for
        # readability / IDE visibility / co-location with sibling overrides, but its
        # GraphQL type is synthesized from the Django field exactly as bare
        # ``Meta.fields`` selection would. Selection still belongs to ``Meta.fields`` -
        # an ``auto`` annotation never adds a field - so an ``auto`` name that is not
        # selected is a configuration error. Annotation-only ``auto`` names are routed
        # back into synthesis (excluded from the consumer-authored union below and
        # dropped from ``consumer_annotations`` so the synthesized annotation wins the
        # final merge); an ``auto`` name that ALSO carries an assigned
        # ``strawberry.field`` keeps the assignment-override path (``auto`` loses to a
        # real override).
        selected_field_names = {field.name for field in fields}
        auto_annotated_fields = frozenset(
            name
            for name, annotation in consumer_annotations.items()
            if _is_auto_annotation(annotation)
        )
        unselected_auto = sorted(auto_annotated_fields - selected_field_names)
        if unselected_auto:
            raise ConfigurationError(
                f"{type_name}: fields annotated `auto` but not selected in Meta.fields: "
                f"{unselected_auto}. `auto` declares an already-selected field's type as "
                "model-inferred; it does not add fields. Add the name to Meta.fields (or "
                'Meta.fields = "__all__"), or remove the annotation.',
            )
        consumer_annotated_relation_fields = frozenset(
            field.name
            for field in fields
            if field.is_relation
            and field.name in consumer_annotations
            and field.name not in auto_annotated_fields
        )
        consumer_annotated_scalar_fields = frozenset(
            field.name
            for field in fields
            if not field.is_relation
            and field.name in consumer_annotations
            and field.name not in auto_annotated_fields
        )
        consumer_assigned_relation_fields, consumer_assigned_scalar_fields = (
            _consumer_assigned_fields(
                cls,
                fields,
            )
        )
        # ``auto`` (model-inferred type) cannot combine with an assigned
        # ``strawberry.field`` (custom resolver / type): the annotation supplies no
        # type for the overlap idiom, so the pair is contradictory. Reject it rather
        # than silently leaving the field typed ``Any``.
        assigned_auto = sorted(
            auto_annotated_fields
            & (consumer_assigned_relation_fields | consumer_assigned_scalar_fields),
        )
        if assigned_auto:
            raise ConfigurationError(
                f"{type_name}: fields both annotated `auto` and assigned a "
                f"strawberry.field: {assigned_auto}. `auto` means model-inferred type and "
                "cannot combine with an assigned resolver. Use `name: <type> = "
                "strawberry.field(...)` for a typed resolver override, or drop the "
                "assignment to keep the inferred type.",
            )
        # Annotation-only ``auto`` fields defer to synthesis: drop their ``auto``
        # sentinel so ``{**synthesized, **consumer_annotations}`` below resolves them to
        # the model-inferred annotation rather than ``Any``.
        for name in auto_annotated_fields:
            _ = consumer_annotations.pop(name, None)
        # Four-corner consumer-override contract: relation/scalar x annotation/
        # assignment. Full enumeration of the contract lives on the
        # ``_consumer_assigned_fields`` docstring; this union is the single
        # short-circuit input read by ``_build_annotations`` to skip
        # auto-synthesis for any consumer-authored name on either branch.
        consumer_authored_fields = frozenset(
            {
                *consumer_annotated_relation_fields,
                *consumer_annotated_scalar_fields,
                *consumer_assigned_relation_fields,
                *consumer_assigned_scalar_fields,
            },
        )
        relay_shaped = _is_relay_shaped(cls, validated.interfaces)
        _validate_nullability_override_targets(
            model=model,
            selected_fields=fields,
            consumer_authored_fields=consumer_authored_fields,
            relay_shaped=relay_shaped,
            nullable_overrides=validated.nullable_overrides,
            required_overrides=validated.required_overrides,
        )
        _validate_filesystem_path_targets(
            model=model,
            selected_fields=fields,
            consumer_authored_fields=consumer_authored_fields,
            filesystem_path_fields=validated.filesystem_path_fields,
        )
        _validate_relation_shape_targets(
            model=model,
            relation_shapes=validated.relation_shapes,
            selected_fields=fields,
            field_map=field_map,
            consumer_authored_fields=consumer_authored_fields,
        )
        if relay_shaped:
            has_id_assignment = truth.is_instance(truth.class_dict(cls).get("id"), StrawberryField)
            has_id_annotation = "id" in cls.__annotations__
            if has_id_assignment:
                raise ConfigurationError(
                    f"{type_name}: cannot override the id field on a "
                    "relay.Node-shaped type with an assigned strawberry.field. "
                    "Use @classmethod resolve_id for a custom id resolver, "
                    "id: relay.NodeID[<pk_type>] for a custom id annotation, "
                    "or declare a resolver-backed sibling field - e.g., "
                    "`@strawberry.field(description=...) def display_id(self) -> "
                    "strawberry.ID: return str(self.pk)` - if you only need "
                    "GraphQL field-level metadata on a custom identifier "
                    "(a metadata-only sibling without a resolver builds but "
                    "fails at query time); "
                    "or remove relay.Node from Meta.interfaces.",
                )
            if has_id_annotation and not _id_annotation_is_relay_node_id(cls):
                raise ConfigurationError(
                    f"{type_name}: cannot override the id field on a "
                    "relay.Node-shaped type without using strawberry.relay.NodeID[...]. "
                    "The Relay interface supplies id: GlobalID! - declare the id "
                    "field via relay.NodeID[<pk_type>] if you need a different id "
                    "shape, or remove relay.Node from Meta.interfaces.",
                )
        synthesized, pending = _build_annotations(
            cls,
            fields,
            source_model=model,
            consumer_authored_fields=consumer_authored_fields,
            interfaces=validated.interfaces,
            nullable_overrides=validated.nullable_overrides,
            required_overrides=validated.required_overrides,
            filesystem_path_fields=validated.filesystem_path_fields,
        )
        definition = DjangoTypeDefinition(
            origin=cls,
            model=validated.model,
            name=validated.name,
            description=validated.description,
            fields_spec=validated.fields_spec,
            exclude_spec=validated.exclude_spec,
            selected_fields=tuple(fields),
            field_map=field_map,
            # ``_validate_optimizer_hints`` above rejected every non-``OptimizerHint`` value.
            optimizer_hints=cast("dict[str, OptimizerHint]", validated.optimizer_hints),
            has_custom_get_queryset=has_custom_get_queryset,
            consumer_authored_fields=consumer_authored_fields,
            consumer_annotated_relation_fields=consumer_annotated_relation_fields,
            consumer_annotated_scalar_fields=consumer_annotated_scalar_fields,
            consumer_assigned_relation_fields=consumer_assigned_relation_fields,
            consumer_assigned_scalar_fields=consumer_assigned_scalar_fields,
            interfaces=validated.interfaces,
            primary=validated.primary,
            filterset_class=validated.filterset_class,
            orderset_class=validated.orderset_class,
            connection=validated.connection,
            cursor_field=validated.cursor_field,
            globalid_strategy=validated.globalid_strategy,
            relation_shapes=validated.relation_shapes,
        )
        registry.register_with_definition(model, cls, definition, primary=validated.primary)
        for pending_relation in pending:
            registry.add_pending_relation(pending_relation)
        cls.__annotations__ = {**synthesized, **consumer_annotations}
        cls.__django_strawberry_definition__ = definition
        install_is_type_of(cls)

    @classmethod
    def get_queryset(
        cls,
        # basedpyright: consumer-overridden hook; an override narrows the queryset's model,
        # which a parameter typed narrower than Any rejects (reportIncompatibleMethodOverride)
        queryset: models.QuerySet[Any, Any],  # pyright: ignore[reportExplicitAny]
        # basedpyright: an override annotates ``info: strawberry.Info``, which object rejects; the
        # shared visibility runners also serve public helpers taking any info, which Info rejects
        info: Any,  # pyright: ignore[reportExplicitAny, reportAny]  # noqa: ANN401
        # basedpyright: an override returns ``super().get_queryset(...)`` as its own model's
        # queryset, which a concrete return rejects and a TypeVar return forbids non-generically
    ) -> models.QuerySet[Any, Any]:  # pyright: ignore[reportExplicitAny]
        """Default identity hook.

        Subclasses override this to scope visibility (permissions,
        multi-tenancy, soft-delete). An override makes
        ``has_custom_get_queryset`` report the hook as other than the identity,
        and the readers that cross a relation into this type then apply it: the
        optimizer downgrades ``select_related`` to ``Prefetch`` so the hook
        filters the related rows instead of a raw join reading them. The package
        calls it as ``get_queryset(queryset, info)`` and passes nothing
        else, so an override declares exactly those two parameters.
        ``info`` is the schema's ``strawberry.Info`` for the resolver that
        runs the hook; on the optimizer's ``Prefetch`` path that is the
        resolver whose plan reaches this type.

        An override may be ``def`` or ``async def``. Under the asynchronous
        executor a ``def`` override runs off the event loop in a thread-sensitive
        ``sync_to_async`` worker - its own per call, or the worker an optimizer
        plan build runs in - so it may read the database; an ``async def``
        override is awaited on the event loop.

        With no declared rules (``Meta.visibility``, a model mixin's
        ``visibility``, ``Meta.cascade``) and no schema-wide restriction this
        is the identity. Otherwise it is the framework-owned enforcement body
        (``rules/apply.py``): a restriction reaches every type, rules or not.
        """
        from django_strawberry_framework.rules.apply import (
            apply_declared_visibility,
            schema_restrictions,
        )

        if not cls.__declares_visibility__ and not schema_restrictions(info):
            return queryset
        return apply_declared_visibility(cls, queryset, info)

    @classmethod
    def has_custom_get_queryset(cls) -> bool:
        """Report whether the type's visibility hook is anything other than the identity.

        ``True`` means the type's rows are scoped, so a reader crossing a
        relation into this type applies the hook rather than reading the raw
        relation. A ``get_queryset`` other than ``DjangoType``'s own, declared on
        the type or inherited from an intermediate base, is what makes it
        ``True``.

        Readers: the optimizer walker (downgrades a join to a ``Prefetch``,
        disables FK-id elision, marks the plan uncacheable); the generated
        relation resolver (applies the hook to a relation the optimizer did not
        plan); relation-visibility resolution in ``utils/querysets.py`` and
        ``RelationHop.scope`` in ``utils/permissions.py`` (the hops a
        ``FilterSet`` relation path crosses); ``OrderSet`` (an order term across
        the relation reads ``NULL`` for a hidden row); the finalizer (refuses a
        ``FilterSet`` / ``OrderSet`` bound to two owners when either owner's hook
        is not the identity).

        Implementation: ``__init_subclass__`` stamps ``_is_default_get_queryset``
        on every subclass, ``Meta`` or not, from ``utils/truth.py::overrides``;
        this method reads the class's own stamp.
        """
        return not truth.static_attr(cls, "_is_default_get_queryset", default=True)


def _validate_visibility(
    cls: type[DjangoType],
    meta: object,
) -> tuple[tuple[object, ...], bool | None]:
    """Validate ``Meta.visibility`` (a sequence of ``Rule``) and ``Meta.cascade`` (a bool)."""
    from django_strawberry_framework.rules.fragment import Rule

    declared = _meta_attr(meta, "visibility")
    rules: tuple[object, ...] = ()
    if declared is not None:
        if isinstance(declared, (str, bytes)) or not isinstance(declared, (list, tuple)):
            raise ConfigurationError(
                f"{cls.__name__}.Meta.visibility must be a list or tuple of Rule",
            )
        for rule in declared:
            if not isinstance(rule, Rule):
                raise ConfigurationError(
                    f"{cls.__name__}.Meta.visibility holds {rule!r}; every entry must be a Rule",
                )
        rules = tuple(declared)
    cascade = _meta_attr(meta, "cascade")
    if cascade is not None and not isinstance(cascade, bool):
        raise ConfigurationError(f"{cls.__name__}.Meta.cascade must be a bool")
    return rules, cascade


def _validate_blessed(cls: type[DjangoType], meta: object, custom_hook: bool) -> str | None:
    """Validate ``Meta.blessed``: a reason string, only on a type with a hand-written hook."""
    reason = _meta_attr(meta, "blessed")
    if reason is None:
        return None
    if not isinstance(reason, str) or not reason.strip():
        raise ConfigurationError(f"{cls.__name__}.Meta.blessed must be a non-empty reason string")
    if not custom_hook:
        raise ConfigurationError(
            f"{cls.__name__}.Meta.blessed names a reason for a hand-written get_queryset, "
            "but the type does not override get_queryset",
        )
    return reason


def _declares_visibility(cls: type[DjangoType], model: type[models.Model]) -> bool:
    """Whether any declared rule (on the type or a model mixin) reaches ``cls``.

    Every row term of every rule must name a field reachable from ``model``;
    an unknown path is a configuration error here, not a silent no-op filter
    at request time. ``Meta.cascade`` alone declares nothing: with no rule
    there is nothing to cascade, and the hook stays the identity.
    """
    from django_strawberry_framework.rules.apply import model_rule_sites

    rules = [(cls.__name__, rule) for rule in cls.__visibility_rules__]
    rules += [(base.__name__, rule) for base, rule in model_rule_sites(model)]
    for site, rule in rules:
        _check_footprint(cls, site, rule, model)
    return bool(rules)


def _check_footprint(
    cls: type[DjangoType],
    site: str,
    rule: object,
    model: type[models.Model],
) -> None:
    """Raise ``ConfigurationError`` when ``rule`` reads a field ``model`` does not have."""
    from django_strawberry_framework.rules.fragment import Rule, validate_footprint

    assert isinstance(rule, Rule)
    try:
        validate_footprint(rule.predicate, model)
    except ValueError as exc:
        raise ConfigurationError(
            f"{cls.__name__}: visibility rule {rule.name!r} declared on {site} "
            f"does not fit {model.__name__}: {exc}",
        ) from None


def _normalize_fields_spec(value: object) -> tuple[str, ...] | Literal["__all__"] | None:
    """Normalize ``Meta.fields`` for storage on ``DjangoTypeDefinition``."""
    if value is None:
        return value
    if truth.is_instance(value, str):
        if truth.text(value) == "__all__":
            return "__all__"
        raise ConfigurationError(
            "Meta.fields must be '__all__' or a non-string sequence of field names",
        )
    if not issubclass(truth.class_of(value), Sequence):
        raise ConfigurationError(
            "Meta.fields must be '__all__' or a non-string sequence of field names",
        )
    # The real-class check above proved a ``Sequence``.
    entries = tuple(list_of(value))
    if _is_str_tuple(entries):
        return entries
    invalid = next(entry for entry in entries if not truth.is_instance(entry, str))
    raise ConfigurationError(
        f"Meta.fields must contain field name strings; got {truth.render(invalid)}",
    )


def _normalize_sequence_spec(value: object, key: str = "exclude") -> tuple[str, ...] | None:
    """Normalize one optional collection-valued ``Meta`` key for storage.

    ``key`` names the declaration being normalized so the rejection message
    names the key the consumer actually wrote. The default keeps ``Meta.exclude``,
    the first key through this helper, spelled the way it always was.

    A ``set`` / ``frozenset`` is accepted alongside ``tuple`` / ``list``: every key
    routed here (``Meta.exclude``, ``Meta.nullable_overrides``,
    ``Meta.required_overrides``, ``Meta.filesystem_path_fields``) is a SET of
    field names whose declaration order carries no meaning, and three of the four
    are normalized to a ``frozenset`` immediately after this call. Rejecting the
    literal a consumer would reasonably write for a set of names would be a
    shape gate that contradicts its own semantics. A ``str`` stays refused - it
    is iterable, so accepting it would silently read one field name as a
    sequence of single-character names.
    """
    if value is None:
        return None
    if truth.is_instance(value, str) or not issubclass(
        truth.class_of(value),
        (Sequence, AbstractSet),
    ):
        raise ConfigurationError(
            f"Meta.{key} must be a non-string sequence or set of field names",
        )
    # The real-class check above proved a ``Sequence`` or ``AbstractSet``.
    entries = tuple(list_of(value))
    if _is_str_tuple(entries):
        return entries
    invalid = next(entry for entry in entries if not truth.is_instance(entry, str))
    raise ConfigurationError(
        f"Meta.{key} must contain field name strings; got {truth.render(invalid)}",
    )


def _consumer_assigned_fields(
    cls: type[DjangoType],
    fields: "tuple[ModelField, ...]",
) -> tuple[frozenset[str], frozenset[str]]:
    """Return (relation, scalar) names assigned to explicit Strawberry field objects.

    One of four collection sites that together pin the consumer-override
    contract for ``DjangoType``. The four corners are:

    - **relation x annotation** - ``consumer_annotated_relation_fields``,
      collected at ``DjangoType.__init_subclass__`` by walking
      ``cls.__annotations__`` for names that match a selected relation
      field. Honours a consumer-written ``items: list["AdminItemType"]``-
      style annotation.
    - **relation x assigned** - ``consumer_assigned_relation_fields``,
      this function's first return value. Honours a consumer-written
      ``items = strawberry.field(resolver=...)`` assignment on a relation
      column.
    - **scalar x annotation** - ``consumer_annotated_scalar_fields``,
      collected in the same ``__init_subclass__`` walk. Honours a
      consumer-written ``description: int``-style annotation override on
      a scalar column.
    - **scalar x assigned** - ``consumer_assigned_scalar_fields``, this
      function's second return value. Honours a consumer-written
      ``description = strawberry.field(resolver=...)`` assignment on a
      scalar column.

    The four sets are stored on ``DjangoTypeDefinition`` as the
    introspection surface. Their union, ``consumer_authored_fields``, is
    the single short-circuit input that ``_build_annotations`` reads at
    its relation branch and its scalar branch to skip auto-synthesis for
    any name the consumer authored.

    Walks every selected Django field, not just relations. A consumer
    who writes ``name = strawberry.field(resolver=...)`` on a scalar
    column gets the same treatment as the relation case: their
    Strawberry field object is preserved and ``_build_annotations``
    skips synthesizing an annotation for that name. Any non-
    ``StrawberryField`` shadow of a Django field name raises the same
    ``ConfigurationError`` shape so the failure mode is consistent
    across scalar and relation columns.
    """
    relation_assigned: set[str] = set()
    scalar_assigned: set[str] = set()
    namespace = truth.class_dict(cls)
    for field in fields:
        if field.name not in namespace:
            continue
        value = namespace[field.name]
        if truth.is_instance(value, StrawberryField):
            if field.is_relation:
                relation_assigned.add(field.name)
            else:
                scalar_assigned.add(field.name)
            continue
        kind = "relation" if field.is_relation else "scalar"
        raise ConfigurationError(
            f"{truth.name(cls)}.{field.name} shadows a Django {kind} field with an unsupported "
            "class attribute. Use a type annotation for type overrides, or use "
            "strawberry.field(resolver=...) / @strawberry.field for resolver overrides.",
        )
    return frozenset(relation_assigned), frozenset(scalar_assigned)


def _meta_optimizer_hints(meta: object, model: type[models.Model]) -> dict[str, object]:
    """Return ``meta.optimizer_hints`` as a dict, or ``{}`` when unset.

    Centralizes the shape guard used across ``__init_subclass__`` and the
    validators so non-mapping declarations fail before hint keys or
    values are inspected. The non-mapping rejection names the value's kind
    (``utils/truth.py::kind``): an instance by its real class, a class by its
    own name (``got Category.``), never by its metaclass.
    """
    value = _meta_attr(meta, "optimizer_hints")
    if value is None:
        return {}
    if not issubclass(truth.class_of(value), Mapping):
        raise ConfigurationError(
            f"{truth.name(model)}.Meta.optimizer_hints must be a mapping of field names to OptimizerHint "
            f"instances, got {truth.kind(value)}.",
        )
    # The real-class check above proved a ``Mapping``. One pass over a plain copy of the
    # consumer mapping: the keys checked are the keys returned.
    hints: dict[str, object] = {}
    for key, hint in dict_of(value).items():
        if not truth.is_instance(key, str):
            raise ConfigurationError(
                f"{truth.name(model)}.Meta.optimizer_hints keys must be field name strings; "
                f"got {truth.render(key)}.",
            )
        hints[key] = hint
    return hints


def _format_unknown_fields_error(
    *,
    model: type[models.Model],
    attr: str,
    unknown: list[str],
    available: set[str],
) -> str:
    """Return the standard "unknown fields ... Available: ..." error message.

    Used by every validator that points at a typo in a ``Meta`` key naming
    model fields; ``attr`` names the offending key.  Centralizing the format
    keeps the consumer-visible error shape consistent across typo-guard sites.
    """
    return (
        f"{truth.name(model)}.Meta.{attr} names unknown fields: {unknown}. "
        f"Available: {sorted(available)}."
    )


_INTERFACES_SHAPE_ERROR_LEAD_IN = (
    "Meta.interfaces must be a tuple/list of Strawberry interface classes "
    "or a single interface class"
)


def _interfaces_shape_error(model: type[models.Model], got_suffix: str) -> str:
    """Format the top-level ``Meta.interfaces`` shape-rejection message.

    Both raise sites (string-typed raw, other non-sequence raw) share the
    long lead-in defined in ``_INTERFACES_SHAPE_ERROR_LEAD_IN``; this
    helper localizes the wording so the two sites cannot drift.
    """
    return f"{truth.name(model)}.{_INTERFACES_SHAPE_ERROR_LEAD_IN}, got {got_suffix}."


# Decision-8 remediation tail shared by all six named rejections: every
# message ends by naming what the consumer probably meant (``relay.Node``);
# the ``Connection`` / ``ListConnection`` rows additionally name
# ``Meta.connection`` / ``DjangoConnectionField`` in their descriptions.
_RELAY_NON_INTERFACE_REMEDIATION = (
    "If the goal is a Relay-Node-shaped type, add `relay.Node` to `Meta.interfaces` instead."
)

# ``relay.Connection`` and ``relay.ListConnection`` share one description
# (spec-032 Decision 8 pins "same remediation as ``Connection``").
_RELAY_CONNECTION_HELPER_DESCRIPTION = (
    "a generic output type; declare `Meta.connection` / use "
    "`DjangoConnectionField` for connection shapes"
)

# The six ``strawberry.relay`` NON-interface helpers rejected by name when
# found in ``Meta.interfaces`` (spec-032 Decision 8). Rows are
# ``(helper_object, display_label, what-it-is description)``; matching is by
# identity (``entry is helper``) because ``relay.NodeID`` is a
# ``typing.Annotated`` alias - not a class, not reliably hashable/equatable -
# and ``Meta.interfaces`` entries can be arbitrary (even unhashable) consumer
# objects. Single raise site in ``_validate_interfaces``.
_RELAY_NON_INTERFACE_HELPERS: tuple[tuple[object, str, str], ...] = (
    (
        relay.GlobalID,
        "relay.GlobalID",
        (
            "a scalar-like id wrapper, not an interface; Relay-Node-shaped types "
            "get `id: GlobalID!` automatically from `relay.Node`"
        ),
    ),
    (
        relay.NodeID,
        "relay.NodeID",
        "an annotation helper for custom id fields (`id: relay.NodeID[int]`), not an interface",
    ),
    (relay.Connection, "relay.Connection", _RELAY_CONNECTION_HELPER_DESCRIPTION),
    (relay.ListConnection, "relay.ListConnection", _RELAY_CONNECTION_HELPER_DESCRIPTION),
    (
        relay.Edge,
        "relay.Edge",
        "a generic output type the connection machinery instantiates; not consumer-declarable",
    ),
    (relay.PageInfo, "relay.PageInfo", "a generated pagination type; not an interface"),
)


def _validate_interfaces(meta: object, model: type[models.Model]) -> tuple[type[object], ...]:
    """Validate and normalize ``Meta.interfaces`` per Decision 4.

    Returns a normalized ``tuple[type[object], ...]`` ready to pass through to
    ``DjangoTypeDefinition.interfaces``. Returns ``()`` when the key is
    absent or set to an empty tuple/list (Decision 4,
    spec-015 #"An empty tuple is the same as not declaring").

    Validation rules (spec-015 #"may be a tuple/list of interface classes"):

    - Accepts a tuple/list of interface classes, or a single real
      Strawberry interface class (e.g. ``interfaces = relay.Node``).
    - Rejects strings, sets, generators, dicts, ints, and other
      non-sequence values.
    - Each entry must satisfy
      ``hasattr(entry, "__strawberry_definition__") and
      entry.__strawberry_definition__.is_interface``.
    - Rejects string entries (no lazy/forward-reference lookup).
    - Rejects the six ``strawberry.relay`` non-interface helpers
      (``GlobalID``, ``NodeID``, ``Connection``, ``ListConnection``,
      ``Edge``, ``PageInfo``) by name, before the generic non-interface
      rejection (spec-032 Decision 8).
    - Rejects ``DjangoType`` self-reference and other ``DjangoType``
      subclasses.
    - Rejects duplicates.

    The composite-pk constraint and ``relay.Node`` MRO inspection live
    in ``finalize_django_types()`` (Relay finalization phase); this
    helper only validates the shape and contents of the
    ``Meta.interfaces`` tuple itself.
    """
    raw = _meta_attr(meta, "interfaces")
    if raw is None:
        return ()
    if truth.is_instance(raw, str):
        raise ConfigurationError(_interfaces_shape_error(model, "a string"))
    if truth.is_type(raw):
        # Consumer-declared entries stay unproven until the loop below checks each one.
        entries: tuple[object, ...] = (raw,)
    elif truth.is_instance(raw, tuple) or truth.is_instance(raw, list):
        # The real-class check above proved a ``tuple`` or ``list``.
        entries = tuple(list_of(raw))
    else:
        raise ConfigurationError(_interfaces_shape_error(model, truth.name(truth.class_of(raw))))
    if entries == ():
        return ()
    model_name = truth.name(model)
    seen_ids: set[int] = set()
    duplicates: list[str] = []
    interfaces: list[type[object]] = []
    for entry in entries:
        if truth.is_instance(entry, str):
            raise ConfigurationError(
                f"{model_name}.Meta.interfaces must contain interface classes, "
                f"not strings (got {truth.render(entry)}). Lazy/forward-reference interface lookup is "
                "deferred (no current spec home).",
            )
        # Named-helper rejection (spec-032 Decision 8). Runs BEFORE the
        # non-class branch below because ``relay.NodeID`` is an ``Annotated``
        # alias, not a class - placed later it would die in the generic
        # non-class rejection without ever being named.
        for helper, label, description in _RELAY_NON_INTERFACE_HELPERS:
            if entry is helper:
                raise ConfigurationError(
                    f"{model_name}.Meta.interfaces entry {label} is "
                    f"{description}. {_RELAY_NON_INTERFACE_REMEDIATION}",
                )
        if not truth.is_type(entry):
            raise ConfigurationError(
                f"{model_name}.Meta.interfaces must contain interface classes, "
                f"got {truth.render(entry)}.",
            )
        if truth.is_subclass(entry, DjangoType):
            raise ConfigurationError(
                f"{model_name}.Meta.interfaces may not contain DjangoType or "
                f"DjangoType subclasses (got {truth.name(entry)}). DjangoType is not a "
                "Strawberry interface.",
            )
        definition: object = truth.static_attr(entry, "__strawberry_definition__")
        if not (
            truth.is_instance(definition, StrawberryObjectDefinition) and definition.is_interface
        ):
            raise ConfigurationError(
                f"{model_name}.Meta.interfaces entry {truth.name(entry)} is not a "
                "Strawberry interface. Use @strawberry.interface or one of the "
                "strawberry.relay interface classes.",
            )
        entry_id = id(entry)
        if entry_id in seen_ids:
            duplicates.append(truth.name(entry))
        else:
            seen_ids.add(entry_id)
        interfaces.append(entry)
    if duplicates:
        raise ConfigurationError(
            f"{model_name}.Meta.interfaces contains duplicate entries: {sorted(duplicates)}.",
        )
    return tuple(interfaces)


class _ValidatedMeta(NamedTuple):
    """Single-pass snapshot of validated ``Meta`` attributes.

    Threading the validated values back from ``_validate_meta`` keeps the
    caller from re-reading ``getattr(meta, ...)`` for the same keys and
    avoids re-running the shape gates (``_normalize_fields_spec``,
    ``_normalize_sequence_spec``, ``_meta_optimizer_hints``) at multiple
    sites in ``__init_subclass__``.
    """

    model: type[models.Model]
    interfaces: tuple[type[object], ...]
    name: str | None
    description: str | Promise | None
    primary: bool
    optimizer_hints: dict[str, object]
    fields_spec: tuple[str, ...] | Literal["__all__"] | None
    exclude_spec: tuple[str, ...] | None
    filterset_class: "type[FilterSet] | None"
    orderset_class: "type[OrderSet] | None"
    connection: dict[str, bool] | None
    cursor_field: tuple[str, ...] | None
    globalid_strategy: "GlobalIDStrategy | None"
    relation_shapes: dict[str, str] | None
    nullable_overrides: frozenset[str]
    required_overrides: frozenset[str]
    filesystem_path_fields: frozenset[str]


def _validate_meta(cls: type[DjangoType], meta: object) -> _ValidatedMeta:
    """Validate a ``DjangoType`` subclass's nested ``Meta`` class.

    Takes ``cls`` (the class object, available at ``__init_subclass__`` time)
    so the Relay-shape predicate (``_is_relay_shaped``) the ``Meta.connection``
    gate needs can see direct ``relay.Node`` inheritance, not only the declared
    ``Meta.interfaces`` tuple.

    Every shape gate tests a consumer value by its real class (``utils/truth.py::is_instance``,
    ``is_subclass``, ``is_exact``, ``class_of``), never through its ``__class__`` attribute,
    so a value whose ``__class__`` read raises is rejected with the same ``ConfigurationError``
    as any other malformed value. A Django lazy proxy (``SimpleLazyObject``) forwards
    ``__class__`` but is not the class it stands for, so every key refuses it with that same
    error (``utils/lazy.py`` states the rule).

    Validation order:

    1. ``Meta.model`` is required and must be a Django model class.
    2. ``fields`` and ``exclude`` are mutually exclusive.
    3. Any key in ``DEFERRED_META_KEYS`` raises with a clear message.
    4. Any non-dunder key on ``meta`` not in ``ALLOWED_META_KEYS |
       DEFERRED_META_KEYS`` raises (typo guard).
    5. ``fields``, ``exclude``, and ``optimizer_hints`` have supported
       declaration shapes before field selection or hint validation uses
       them.
    6. If ``Meta.interfaces`` is declared, validate it per
       ``_validate_interfaces`` (spec-015 Decision 4).
    7. ``Meta.connection`` (if declared) is shape-checked and gated to
       Relay-Node-shaped types via the ``relay_shaped`` bool derived from
       ``cls`` + the validated interfaces, so the
       gate accepts the same shapes as the ``DjangoConnectionField`` field guard.
    8. ``Meta.relation_shapes`` (if declared) is shape-checked and gated to
       Relay-Node-shaped types via ``_validate_relation_shapes`` (spec-032
       Decision 7); the field-level target checks run later in
       ``_validate_relation_shape_targets``.

    Returns:
        A ``_ValidatedMeta`` snapshot bundling the checked ``Meta.model``,
        the validated interfaces tuple, the ``primary`` bool, the normalized
        ``optimizer_hints`` dict, the normalized ``fields``/``exclude`` specs, the validated
        ``filterset_class``/``orderset_class``/``connection``/
        ``globalid_strategy``/``relation_shapes`` sidecars, and the
        ``nullable_overrides``/``required_overrides`` frozensets - see the
        ``_ValidatedMeta`` definition for the authoritative field list. The
        caller threads these through to ``DjangoTypeDefinition`` and
        ``_validate_optimizer_hints`` so the shape gates run exactly once
        per class definition.

    Raises:
        ConfigurationError: any of the above violations.

    """
    model = _meta_attr(meta, "model")
    if model is None:
        raise ConfigurationError("Meta.model is required")
    if not truth.is_subclass(model, models.Model):
        raise ConfigurationError("Meta.model must be a Django model class")
    model_name = truth.name(model)

    raw_name = _meta_attr(meta, "name")
    if raw_name is not None:
        if not truth.is_instance(raw_name, str):
            raise ConfigurationError(
                f"{model_name}.Meta.name must be a non-empty string; got {truth.render(raw_name)}.",
            )
        name = truth.text(raw_name)
        if not name:
            raise ConfigurationError(
                f"{model_name}.Meta.name must be a non-empty string; got an empty name.",
            )
        if not _GRAPHQL_NAME_RE.fullmatch(name) or name.startswith("__"):
            raise ConfigurationError(
                f"{model_name}.Meta.name must be a valid GraphQL name; got {truth.render(name)}.",
            )
    else:
        name = None

    raw_description = _meta_attr(meta, "description")
    description: str | Promise | None
    if raw_description is None or truth.is_instance(raw_description, Promise):
        # A lazy translation string stays lazy until finalize, which renders it once.
        description = raw_description
    elif truth.is_instance(raw_description, str):
        # A str subclass's own ``__str__`` is consumer code; keep the plain text it holds.
        description = truth.text(raw_description)
    else:
        raise ConfigurationError(
            f"{model_name}.Meta.description must be a string or a lazy translation "
            f"string; got {truth.render(raw_description)}.",
        )

    # ``meta``'s OWN namespace (no MRO walk) is deliberate for the typo-guard
    # below (the ``deferred`` / ``unknown`` checks): an unsupported key is
    # flagged only when THIS ``Meta`` declares it, so a base ``Meta``'s
    # already-validated keys are not re-flagged on every subclass. This is the
    # intentional counterpart to the MRO-walking ``_meta_attr`` check just
    # below; the two differ on purpose -- do not "unify" them.
    declared = {k for k in truth.class_dict(meta) if not k.startswith("_")}

    # Use the MRO-walking ``_meta_attr`` rather than own-namespace membership
    # so a child Meta inheriting ``fields`` from a base Meta still trips the
    # mutual-exclusion check when it declares ``exclude`` (and vice versa). ``fields = None``
    # (or ``exclude = None``) remains "unset" - matches
    # ``_normalize_fields_spec``'s treatment of ``None`` and the broader
    # convention that an explicit ``None`` means "no preference".
    has_fields = _meta_attr(meta, "fields") is not None
    has_exclude = _meta_attr(meta, "exclude") is not None
    if has_fields and has_exclude:
        raise ConfigurationError("Meta.fields and Meta.exclude are mutually exclusive")

    primary = _meta_attr(meta, "primary", default=False)
    if not truth.is_exact(primary, bool):
        raise ConfigurationError("Meta.primary must be a bool")

    deferred = sorted(declared & DEFERRED_META_KEYS)
    if deferred:
        raise ConfigurationError(
            f"Meta keys not supported yet: {deferred}. The feature that owns them has not shipped.",
        )

    unknown = sorted(declared - ALLOWED_META_KEYS - DEFERRED_META_KEYS)
    if unknown:
        raise ConfigurationError(f"Unknown Meta keys: {unknown}")

    fields_spec = _normalize_fields_spec(_meta_attr(meta, "fields"))
    exclude_spec = _normalize_sequence_spec(_meta_attr(meta, "exclude"), "exclude")
    optimizer_hints = _meta_optimizer_hints(meta, model)
    interfaces = _validate_interfaces(meta, model)
    relay_shaped = _is_relay_shaped(cls, interfaces)
    filterset_class = _validate_filterset_class(model, _meta_attr(meta, "filterset_class"))
    orderset_class = _validate_orderset_class(model, _meta_attr(meta, "orderset_class"))
    connection = _validate_connection(
        model,
        _meta_attr(meta, "connection"),
        relay_shaped=relay_shaped,
    )
    cursor_field = _validate_cursor_field(
        model,
        _meta_attr(meta, "cursor_field"),
        relay_shaped=relay_shaped,
    )
    globalid_strategy = _validate_globalid_strategy(
        model,
        _meta_attr(meta, "globalid_strategy"),
        relay_shaped=relay_shaped,
    )
    relation_shapes = _validate_relation_shapes(
        model,
        _meta_attr(meta, "relation_shapes"),
        relay_shaped=relay_shaped,
    )
    # Override shape stage (spec-029 Decision 8 step 1): the two set-valued
    # keys reuse the shared collection guard (``_normalize_sequence_spec``, which
    # names the key it rejects), then normalize to ``frozenset``. The
    # both-sets collision is a shape-level contradiction visible from the raw
    # ``Meta`` alone (no model/field access needed), so it raises here rather
    # than in the target-validator. Target existence / scope checks
    # (unknown / excluded / consumer-authored / Relay-pk / relation) need the
    # selected fields and run later in ``_validate_nullability_override_targets``.
    nullable_overrides = frozenset(
        _normalize_sequence_spec(_meta_attr(meta, "nullable_overrides"), "nullable_overrides")
        or (),
    )
    required_overrides = frozenset(
        _normalize_sequence_spec(_meta_attr(meta, "required_overrides"), "required_overrides")
        or (),
    )
    both_sets_collision = sorted(nullable_overrides & required_overrides)
    if both_sets_collision:
        raise ConfigurationError(
            f"{model_name}.Meta names {both_sets_collision} in both "
            "nullable_overrides and required_overrides; a field cannot be both "
            "forced-nullable and forced-required.",
        )

    # ``Meta.filesystem_path_fields`` reuses the same collection guard and
    # frozenset normalization (spec-048 Decision 2). Nothing about the
    # opt-in contradicts another Meta key, so there is no shape-level collision
    # to raise here; every target check needs the selected fields and runs in
    # ``_validate_filesystem_path_targets``.
    filesystem_path_fields = frozenset(
        _normalize_sequence_spec(
            _meta_attr(meta, "filesystem_path_fields"),
            "filesystem_path_fields",
        )
        or (),
    )

    return _ValidatedMeta(
        model=model,
        interfaces=interfaces,
        name=name,
        description=description,
        primary=primary,
        optimizer_hints=optimizer_hints,
        fields_spec=fields_spec,
        exclude_spec=exclude_spec,
        filterset_class=filterset_class,
        orderset_class=orderset_class,
        connection=connection,
        cursor_field=cursor_field,
        globalid_strategy=globalid_strategy,
        relation_shapes=relation_shapes,
        nullable_overrides=nullable_overrides,
        required_overrides=required_overrides,
        filesystem_path_fields=filesystem_path_fields,
    )


def _validate_optimizer_hints(
    hints: dict[str, object],
    fields: "tuple[ModelField, ...]",
    model: type[models.Model],
) -> None:
    """Validate ``Meta.optimizer_hints`` keys and values in one pass.

    Combines the field-surface and value checks in one place:

    1. Every hint key names a field on the model (typo guard).
    2. Every hint key is in the type's selected relation field set.
       Excluded fields and selected scalar fields would silently drop
       optimizer intent otherwise - the walker only reads hints after
       entering the relation branch.
    3. Every hint value is an ``OptimizerHint`` instance.

    Field-name error sites route through ``_format_unknown_fields_error``
    so the consumer-visible shape matches ``Meta.fields`` /
    ``Meta.exclude`` typo guards; value errors use a dedicated
    ``OptimizerHint`` message.

    Args:
        hints: The pre-normalized ``Meta.optimizer_hints`` dict (already
            shape-checked by ``_meta_optimizer_hints`` inside
            ``_validate_meta``). Empty dict short-circuits.
        fields: The Meta-filtered list of Django field objects produced
            by ``_select_fields``. Used to derive the selected relation
            field names so excluded or scalar fields with hints raise.
        model: The Django model whose ``_meta.get_fields()`` defines the
            valid hint key surface. Threaded from the validated
            ``Meta.model`` so the empty-``fields`` shape (e.g. ``Meta.exclude`` covering every
            field) is not fatal - earlier shapes inferred the model from
            ``fields[0].model`` and ``IndexError``'d here.

    """
    if not hints:
        return
    valid_field_names = {f.name for f in model._meta.get_fields()}
    selected_relation_names = {f.name for f in fields if f.is_relation}

    unknown_hint_fields = sorted(set(hints) - valid_field_names)
    if unknown_hint_fields:
        raise ConfigurationError(
            _format_unknown_fields_error(
                model=model,
                attr="optimizer_hints",
                unknown=unknown_hint_fields,
                available=valid_field_names,
            ),
        )
    excluded_hint_fields = sorted(set(hints) - selected_relation_names)
    if excluded_hint_fields:
        raise ConfigurationError(
            _format_unknown_fields_error(
                model=model,
                attr="optimizer_hints",
                unknown=excluded_hint_fields,
                available=selected_relation_names,
            ),
        )
    bad_values = sorted(k for k, v in hints.items() if not truth.is_instance(v, OptimizerHint))
    if bad_values:
        raise ConfigurationError(
            "optimizer_hints values must be OptimizerHint instances, "
            f"got non-OptimizerHint for: {bad_values}",
        )


def _selected_meta_targets(
    *,
    model: type[models.Model],
    selected_fields: "tuple[ModelField, ...]",
    attr: str,
    targets: AbstractSet[str],
    excluded_error: Callable[[list[str]], str],
) -> "tuple[dict[str, ModelField], list[str]]":
    """Run the shared unknown/excluded Meta-target guards; return ``(selected_by_name, sorted)``.

    The unknown/excluded half shared by every ``Meta`` key that targets a set
    of field names on the type (spec-029 Decision 8 / spec-032 Decision 7 /
    spec-048 Decision 2): reject names unknown to the model (via the shared
    ``_format_unknown_fields_error`` keyed on ``attr`` so the consumer-visible
    shape matches the ``Meta.fields`` / ``Meta.exclude`` typo guards), then
    reject names not in the selected set (via the caller's family-specific
    ``excluded_error``, which receives the sorted excluded names). Returns the
    ``{name: field}`` selected map and the sorted target names; the
    domain-specific per-name checks (consumer-authored, non-relation, Relay-pk,
    file/image column, many-side) stay in the caller, which iterates the
    returned names.

    Keeping the unknown-vs-excluded distinction here means a future ``Meta.*``
    target feature inherits both guards without re-deriving the model-wide vs
    selected name sets.
    """
    model_field_names = {f.name for f in model._meta.get_fields()}
    unknown = sorted(targets - model_field_names)
    if unknown:
        raise ConfigurationError(
            _format_unknown_fields_error(
                model=model,
                attr=attr,
                unknown=unknown,
                available=model_field_names,
            ),
        )
    selected_by_name = {f.name: f for f in selected_fields}
    excluded = sorted(targets - set(selected_by_name))
    if excluded:
        raise ConfigurationError(excluded_error(excluded))
    return selected_by_name, sorted(targets)


def _validate_nullability_override_targets(
    *,
    model: type[models.Model],
    selected_fields: "tuple[ModelField, ...]",
    consumer_authored_fields: frozenset[str],
    relay_shaped: bool,
    nullable_overrides: frozenset[str],
    required_overrides: frozenset[str],
) -> None:
    """Reject every illegal ``nullable_overrides`` / ``required_overrides`` target.

    Stage 2 of the override validation flow (spec-029 Decision 8). Runs in
    ``__init_subclass__`` AFTER ``_select_fields`` + ``consumer_authored_fields``
    + the Relay-shape check, so the selected fields, the consumer-override set,
    and the Relay-pk identity all exist. The shape check + both-sets collision
    already ran earlier in ``_validate_meta``; this helper only validates the
    union of the two normalized sets against the model and selected fields.

    Two distinct name sets are derived as separate error paths so the
    ``Meta.exclude`` contract is not collapsed into "unknown": the model-wide
    names (``model._meta.get_fields()``) gate the *unknown-field* path, and the
    selected-field names gate the *excluded / not-selected* path. The unknown
    path routes through ``_format_unknown_fields_error`` so its consumer-visible
    shape matches the ``Meta.fields`` / ``Meta.exclude`` / ``Meta.optimizer_hints``
    typo guards.

    Check order: unknown -> excluded -> consumer-authored -> Relay-pk ->
    relation. The last three operate on selected, known fields, so they run
    only after the first two have confirmed the name exists and is selected.
    Relay-pk precedes relation so a name that is both - a relation pk such as
    ``OneToOneField(primary_key=True)`` on a Relay-shaped type - is reported
    with the Relay reason rather than the relation one. Every failure raises
    ``ConfigurationError`` at type-creation time naming the offending field.

    Args:
        model: The Django model the type wraps; ``model._meta.get_fields()``
            defines the valid-field surface (unknown-field path) and
            ``model._meta.pk.name`` the Relay-suppressed pk identity.
        selected_fields: The Meta-filtered Django field objects from
            ``_select_fields`` - defines the selected name set (excluded path)
            and supplies ``field.is_relation`` for the relation-reject path.
        consumer_authored_fields: The four-corner consumer-override union; a
            name here already controls its own nullability via the annotation /
            ``strawberry.field`` assignment, so an override on it is rejected.
        relay_shaped: Whether the type participates in the Relay ``Node``
            interface; when ``True`` the suppressed pk's nullability is the
            interface's contract and cannot be overridden.
        nullable_overrides: Normalized ``Meta.nullable_overrides`` frozenset.
        required_overrides: Normalized ``Meta.required_overrides`` frozenset.

    Raises:
        ConfigurationError: any target is unknown / excluded / consumer-authored
            / the Relay-suppressed pk / a relation field.

    """
    targets = nullable_overrides | required_overrides
    if not targets:
        return
    selected_by_name, sorted_targets = _selected_meta_targets(
        model=model,
        selected_fields=selected_fields,
        attr="nullable_overrides/required_overrides",
        targets=targets,
        excluded_error=lambda excluded: (
            f"{truth.name(model)}.Meta nullable_overrides/required_overrides name fields not in "
            f"the selected set: {excluded}. "
            "The override targets a field that will not appear "
            "in the GraphQL type (excluded via Meta.exclude or absent from a subset Meta.fields); "
            "select the field or drop the override."
        ),
    )
    relay_pk_name = model._meta.pk.name if relay_shaped else None
    for name in sorted_targets:
        if name in consumer_authored_fields:
            raise ConfigurationError(
                f"{truth.name(model)}.Meta nullable_overrides/required_overrides names "
                f"consumer-authored field {truth.render(name)}; a consumer annotation or strawberry.field "
                "assignment already controls its nullability. Drop the override and control "
                "nullability through the annotation instead.",
            )
        if name == relay_pk_name:
            raise ConfigurationError(
                f"{truth.name(model)}.Meta nullable_overrides/required_overrides names the "
                f"Relay-Node-suppressed pk {truth.render(name)}; the pk's nullability is the relay.Node "
                "interface's contract (id: GlobalID!), not the column's, and cannot be overridden.",
            )
        if selected_by_name[name].is_relation:
            raise ConfigurationError(
                f"{truth.name(model)}.Meta nullable_overrides/required_overrides names relation "
                f"field {truth.render(name)}; nullability overrides apply to non-relation "
                "model fields only "
                "(scalar columns and file/image output objects). Relation-field "
                "nullability override is deferred (see spec-029 Decision 10).",
            )


def _validate_filesystem_path_targets(
    *,
    model: type[models.Model],
    selected_fields: "tuple[ModelField, ...]",
    consumer_authored_fields: frozenset[str],
    filesystem_path_fields: frozenset[str],
) -> None:
    """Reject every illegal ``Meta.filesystem_path_fields`` target (spec-048 Decision 2).

    Stage 2 of the opt-in's validation, the structural sibling of
    ``_validate_nullability_override_targets``: it runs in
    ``__init_subclass__`` after ``_select_fields`` and the consumer-override
    union exist, and reuses ``_selected_meta_targets`` for the shared
    unknown-name and not-selected guards so the consumer-visible error shape
    matches every other ``Meta.*`` target key.

    The key names the columns whose absolute server filesystem path the schema
    publishes, so an unnoticed no-op is the failure mode that matters: a name
    that silently does nothing reads to a reviewer as "the path is exposed" or
    "the path is not exposed" with equal plausibility. Every non-working target
    therefore raises at type-creation time rather than being ignored - a
    consumer-authored column (whose own annotation or ``strawberry.field``
    already owns the field's output type, so the opt-in could not take effect)
    and a non-file column (no path exists to publish).

    Args:
        model: The Django model the type wraps.
        selected_fields: The Meta-filtered Django field objects from
            ``_select_fields``.
        consumer_authored_fields: The four-corner consumer-override union.
        filesystem_path_fields: The normalized ``Meta.filesystem_path_fields``
            frozenset.

    Raises:
        ConfigurationError: any target is unknown / not selected /
            consumer-authored / not a file or image column.

    """
    if not filesystem_path_fields:
        return
    selected_by_name, sorted_targets = _selected_meta_targets(
        model=model,
        selected_fields=selected_fields,
        attr="filesystem_path_fields",
        targets=set(filesystem_path_fields),
        excluded_error=lambda excluded: (
            f"{truth.name(model)}.Meta filesystem_path_fields names fields not in the selected "
            f"set: {excluded}. "
            "The opt-in targets a field that will not appear in the GraphQL "
            "type (excluded via Meta.exclude or absent from a subset Meta.fields); select the "
            "field or drop the opt-in."
        ),
    )
    for name in sorted_targets:
        if name in consumer_authored_fields:
            raise ConfigurationError(
                f"{truth.name(model)}.Meta filesystem_path_fields names consumer-authored field "
                f"{truth.render(name)}; a consumer annotation or strawberry.field assignment already owns "
                "that field's output type, so the opt-in would have no effect. Drop the opt-in "
                "and expose the path from the consumer resolver instead.",
            )
        if _field_output_type_for(selected_by_name[name]) is None:
            raise ConfigurationError(
                f"{truth.name(model)}.Meta filesystem_path_fields names {truth.render(name)}, which is not a "
                "FileField or ImageField column. The filesystem-path opt-in applies only to "
                "file/image columns, whose output object is the only place a path field exists.",
            )


def _validate_relation_shape_targets(
    *,
    model: type[models.Model],
    relation_shapes: dict[str, str] | None,
    selected_fields: "tuple[ModelField, ...]",
    field_map: dict[str, FieldMeta],
    consumer_authored_fields: frozenset[str],
) -> None:
    """Reject every illegal ``Meta.relation_shapes`` key at type creation.

    Stage 2 of the relation-shapes validation flow (spec-032 Decision 7,
    structurally the ``_validate_nullability_override_targets`` sibling). Runs
    in ``__init_subclass__`` AFTER ``_select_fields`` + ``consumer_authored_fields``
    exist, because every check here needs the selected fields, the cardinality
    classifier, or the consumer-override union - none of which exist at
    ``_validate_meta`` time. The shape check + Relay-Node gate already ran in
    stage 1 (``_validate_relation_shapes``).

    Check order mirrors the sibling: unknown -> excluded -> per-name checks
    (non-relation / single-valued / consumer-authored), iterating keys sorted
    for deterministic messages. The unknown path routes through
    ``_format_unknown_fields_error`` so its consumer-visible shape matches the
    ``Meta.fields`` / ``Meta.exclude`` / ``Meta.optimizer_hints`` typo guards.
    Cardinality is read from ``FieldMeta.is_many_side`` (the same single-source
    classifier the generated relation resolvers and the Phase-2.5 synthesis
    key on), so the validator and the synthesis can never disagree about which
    relations are connection-eligible.

    ONLY the target-is-Node-shaped check runs at finalization (Decision 6) -
    relation targets are not settled at type creation.

    Raises:
        ConfigurationError: any key names an unknown / excluded / non-relation
            / single-valued / consumer-authored field.

    """
    if not relation_shapes:
        return
    selected_by_name, sorted_targets = _selected_meta_targets(
        model=model,
        selected_fields=selected_fields,
        attr="relation_shapes",
        targets=set(relation_shapes),
        excluded_error=lambda excluded: (
            f"{truth.name(model)}.Meta.relation_shapes names fields not in the selected set: "
            f"{excluded}. "
            "The entry targets a field that will not appear in the GraphQL type "
            "(excluded via Meta.exclude or absent from a subset Meta.fields); select the field "
            "or drop the entry."
        ),
    )
    for name in sorted_targets:
        if not selected_by_name[name].is_relation:
            raise ConfigurationError(
                f"{truth.name(model)}.Meta.relation_shapes names non-relation field {truth.render(name)}; "
                "only many-side relations (reverse FK, forward/reverse M2M) can take a "
                "connection shape.",
            )
        if not field_map[name].is_many_side:
            if field_map[name].relation_kind == "reverse_one_to_one":
                shape = "reverse OneToOne"
            elif is_single_column_foreign_key(selected_by_name[name]):
                shape = "forward FK / OneToOne"
            else:
                shape = "forward ForeignObject"
            raise ConfigurationError(
                f"{truth.name(model)}.Meta.relation_shapes names single-valued relation {truth.render(name)} "
                f"({shape}); there is nothing to paginate. Only many-side "
                "relations (reverse FK, forward/reverse M2M) can take a connection shape.",
            )
        if name in consumer_authored_fields:
            raise ConfigurationError(
                f"{truth.name(model)}.Meta.relation_shapes names consumer-authored relation "
                f"{truth.render(name)}; a consumer annotation or strawberry.field assignment owns that "
                "field's shape (spec-032 Decision 7). Drop the entry, or remove the override "
                "to let the framework synthesize the relation's shape.",
            )


def _select_fields(
    model: type[models.Model],
    fields_spec: tuple[str, ...] | str | None,
    exclude_spec: tuple[str, ...] | None,
) -> "tuple[ModelField, ...]":
    """Filter ``model._meta.get_fields()`` per ``Meta.fields`` / ``Meta.exclude``.

    Called once from ``DjangoType.__init_subclass__`` and the resulting
    list is reused by ``_build_annotations`` (in this module) and
    ``_attach_relation_resolvers`` (in ``types.resolvers``) so the field
    walk does not happen twice. Iteration order follows
    Django's ``_meta.get_fields()`` so the generated GraphQL type's field
    order matches Django's declared order, with reverse-side relations
    appended at the end.

    The caller threads ``fields_spec`` and ``exclude_spec`` from the
    ``_ValidatedMeta`` snapshot produced by ``_validate_meta`` so the
    shape gates (``_normalize_fields_spec`` / ``_normalize_sequence_spec``)
    run exactly once per class definition - matching the invariant the
    ``_ValidatedMeta`` docstring promises.

    Selection rules:

    - ``fields_spec == "__all__"`` (or both ``fields_spec`` /
      ``exclude_spec`` ``None``) -> every concrete + relation field.
    - ``fields_spec`` as a sequence -> only those names; unknown names raise.
    - ``exclude_spec`` as a sequence -> every field except those names;
      unknown names raise.

    Raises:
        ConfigurationError: ``Meta.fields`` or ``Meta.exclude`` names a
            field that does not exist on ``Meta.model``. The error names
            the model, the unknown values, and the available field set
            so typos surface loudly instead of silently dropping.

    """
    all_fields = list(model._meta.get_fields())
    all_names = [f.name for f in all_fields]
    valid_names = set(all_names)

    if fields_spec == "__all__" or (fields_spec is None and exclude_spec is None):
        selected_names = valid_names
    elif fields_spec is not None:
        unknown = sorted(set(fields_spec) - valid_names)
        if unknown:
            raise ConfigurationError(
                _format_unknown_fields_error(
                    model=model,
                    attr="fields",
                    unknown=unknown,
                    available=valid_names,
                ),
            )
        selected_names = set(fields_spec)
    else:
        # ``fields_spec`` is ``None`` here, so the first branch leaves ``exclude_spec`` set.
        excluded = cast("tuple[str, ...]", exclude_spec)
        unknown = sorted(set(excluded) - valid_names)
        if unknown:
            raise ConfigurationError(
                _format_unknown_fields_error(
                    model=model,
                    attr="exclude",
                    unknown=unknown,
                    available=valid_names,
                ),
            )
        selected_names = valid_names - set(excluded)

    return tuple(f for f in all_fields if f.name in selected_names)


# The default for each field-name set ``_build_annotations`` reads: no field names.
_NO_FIELD_NAMES: frozenset[str] = frozenset()


def _is_suppressed_relay_pk(
    cls: "type[DjangoType]",
    interfaces: tuple[type[object], ...],
    source_model: type[models.Model],
    field: "ModelField",
    consumer_authored_fields: frozenset[str],
) -> bool:
    """Return whether ``field`` loses its synthesized annotation to Relay suppression.

    Single owner of the Relay-pk suppression decision, read by both the
    ``_build_annotations`` synthesis loop and the ``inspect_django_type``
    predictor, so the two cannot drift. Suppressed iff the field is a
    NON-relation pk on a Relay-Node-shaped type that the consumer did not
    author. The checks run relation-first (a relation pk keeps its
    auto-synthesized annotation and finalize resolves it to the target
    type), then the consumer exemption (a consumer override keeps its
    annotation, so the predictor falls through to the consumer row), then
    the Relay-shape gate (``_is_relay_shaped``: ``Meta.interfaces`` holding
    a ``relay.Node`` subclass, or direct ``class Foo(DjangoType,
    relay.Node)`` inheritance - checked with ``issubclass`` per entry, so
    a consumer ``CustomNode(relay.Node)`` interface counts), then the
    pk-identity read.

    The pk identity is ``source_model._meta.pk.name`` - the Django field
    NAME, not the column attname. For a relation primary key
    (``OneToOneField(primary_key=True)``) those differ (``name="user"`` vs
    ``attname="user_id"``) and the comparison is against ``field.name``;
    naming the read ``pk_attname`` would invite reuse in a
    ``getattr(root, pk_attname)`` context, which would lazy-load the
    related row for a relation pk.

    Without suppression a Relay-shaped consumer would land in Phase 3
    ``strawberry.type(...)`` decoration with both the synthesized ``id:
    int`` and the interface-supplied ``id: GlobalID!`` and the schema build
    would blow up with ``NodeIDAnnotationError``.

    Reconsideration triggers: T-population (a new suppressed member extends
    this body; both callers follow); T-identity (a pk-identity change lands
    on the ``_meta.pk.name`` read); T-exemption (a new suppression
    exemption lands here, never as a second predicate at a caller).
    """
    if field.is_relation:
        return False
    if field.name in consumer_authored_fields:
        return False
    if not _is_relay_shaped(cls, interfaces):
        return False
    return field.name == source_model._meta.pk.name


def _build_annotations(
    cls: type[DjangoType],
    fields: "tuple[ModelField, ...]",
    *,
    source_model: type[models.Model],
    consumer_authored_fields: frozenset[str] = _NO_FIELD_NAMES,
    interfaces: tuple[type[object], ...] = (),
    nullable_overrides: frozenset[str] = _NO_FIELD_NAMES,
    required_overrides: frozenset[str] = _NO_FIELD_NAMES,
    filesystem_path_fields: frozenset[str] = _NO_FIELD_NAMES,
) -> tuple[dict[str, object], list[PendingRelation]]:
    """Build the annotation dict the Strawberry type decorator consumes.

    Field-by-field dispatch: non-relation entries in ``fields`` are
    routed through ``convert_field_output`` (the read-output entry point,
    which sends a ``FileField`` / ``ImageField`` to the structured
    ``DjangoFileType`` / ``DjangoImageType`` object and delegates every
    other column unchanged to ``convert_scalar``). Auto-synthesized relation
    entries always record a ``PendingRelation`` and set the annotation to
    ``PendingRelationAnnotation``; ``finalize_django_types()`` resolves
    them through ``registry.get(...)`` after every type has registered
    so multi-type / primary semantics apply uniformly. Consumer-authored
    fields short-circuit out of the synthesis loop on both branches: a
    name in ``consumer_authored_fields`` skips relation deferral at the
    ``field.is_relation`` branch and skips ``convert_field_output`` at the
    scalar branch. See ``_consumer_assigned_fields`` for the four-corner
    override contract that populates ``consumer_authored_fields``. The
    caller pre-computes the field list with
    ``_select_fields(model, fields_spec, exclude_spec)`` (threading the
    validated specs from the ``_ValidatedMeta`` snapshot) so this function
    does not need ``meta``.

    When ``relay.Node`` appears in ``interfaces``, the primary-key field's
    synthesized scalar annotation is dropped from the returned dict so
    Strawberry's interface-supplied ``id: GlobalID!`` is not shadowed by a
    Django ``int`` field. The pk field stays in ``fields`` so the
    optimizer's ``DjangoTypeDefinition.field_map`` continues to see it as a
    connector column (spec-015 Decision 7 #"keeps every selected Django field including the primary key").

    Args:
        cls: The consumer-facing ``DjangoType`` subclass (its ``__name__``
            threads into ``convert_field_output`` (and on to
            ``convert_scalar``) so generated choice enums carry a stable
            name).
        fields: The Meta-filtered list of Django field objects.
        source_model: The Django model the type wraps. Used to resolve the
            primary-key name when ``relay.Node`` suppression is active.
        consumer_authored_fields: Names of fields whose annotation /
            ``StrawberryField`` assignment is owned by the consumer. The
            synthesized annotation is skipped for these names so consumer
            overrides survive collection.
        interfaces: The validated ``Meta.interfaces`` tuple. When
            ``relay.Node`` is among them, the primary-key field's
            synthesized scalar annotation is suppressed so Strawberry's
            interface-supplied ``id: GlobalID!`` is not shadowed.
        nullable_overrides: Normalized ``Meta.nullable_overrides`` frozenset.
            A selected non-relation field named here is forced nullable
            (``force_nullable=True`` into ``convert_field_output``) regardless of
            the column's ``null`` / ``blank`` -- ``T | None`` for a scalar column,
            ``<object> | None`` for a file/image column.
        required_overrides: Normalized ``Meta.required_overrides`` frozenset.
            A selected non-relation field named here is forced required
            (``force_nullable=False``) regardless of the column -- ``T`` for a
            scalar, the bare ``DjangoFileType`` / ``DjangoImageType`` for a
            file/image column. The two sets are validated disjoint and
            non-relation (relation targets are rejected) upstream.
        filesystem_path_fields: Normalized ``Meta.filesystem_path_fields``
            frozenset. A selected file/image column named here resolves to the
            path-bearing output object (``DjangoFilePathType`` /
            ``DjangoImagePathType``) instead of the default one, which is the
            only way the server's absolute filesystem path enters the schema
            (spec-048 Decision 2). Validated to name selected, non-relation,
            non-consumer-authored file/image columns upstream.

    Returns:
        A tuple of ``(annotations, pending_relations)``.

    Raises:
        ConfigurationError: an unsupported scalar field type is encountered
            (raised by ``convert_scalar`` via ``convert_field_output``), or a
            selected relation has no concrete related model to map to a
            GraphQL type.

    """
    annotations: dict[str, object] = {}
    pending: list[PendingRelation] = []
    for field in fields:
        if field.is_relation:
            if field.name in consumer_authored_fields:
                continue
            if getattr(field, "related_model", None) is None:
                raise ConfigurationError(
                    f"{truth.name(source_model)}.{field.name} is a GenericForeignKey or other "
                    "relation without a concrete related model. It cannot be auto-mapped to "
                    "a single GraphQL type. Exclude it via Meta.exclude, or supply an "
                    "explicit annotation or resolver.",
                )
            # Always defer auto-synthesized relation annotations: the
            # consumer_authored short-circuit above leaves consumer overrides
            # alone, and every other relation field becomes a pending record
            # that ``finalize_django_types()`` resolves through
            # ``registry.get(...)`` (which returns the primary post-finalize,
            # or the single registered type when no primary was declared).
            # The earlier eager-bind branch froze the relation against
            # whichever type was already registered at ``__init_subclass__``
            # time, which mis-bound when a secondary was registered before
            # the primary (the import-order trap closed by spec-018).
            pending.append(
                PendingRelation(
                    source_type=cls,
                    source_model=source_model,
                    field_name=field.name,
                    django_field=field,
                    # The ``related_model is None`` gate above raised for this field.
                    related_model=cast("type[models.Model]", field.related_model),
                ),
            )
            annotations[field.name] = PendingRelationAnnotation
        else:
            if field.name in consumer_authored_fields:
                # A consumer-assigned ``StrawberryField`` (or annotation) on a
                # scalar column wins over the auto-synthesized annotation so
                # ``strawberry.field(resolver=...)`` overrides survive
                # collection. Relation override symmetry: see the
                # ``field.is_relation`` branch above.
                continue
            if _is_suppressed_relay_pk(
                cls,
                interfaces,
                source_model,
                field,
                consumer_authored_fields,
            ):
                # ``relay.Node`` supplies ``id: GlobalID!`` via the interface;
                # dropping the synthesized scalar annotation here keeps the
                # Strawberry surface clean. The pk field stays in ``fields``
                # so the optimizer's field map still sees it as a connector
                # column (spec-015 Decision 7 #"keeps every selected Django field including the primary key").
                continue
            # Per-field nullability override tri-state (spec-029 Decision 7):
            # membership in ``nullable_overrides`` forces nullable, membership in
            # ``required_overrides`` forces required, and absence from both leaves
            # ``None`` so ``convert_field_output`` applies the column's own default
            # (``field.null`` for a scalar, nullable-by-default for a file/image
            # object). The two sets are validated to be disjoint and non-relation
            # (relation targets rejected) in ``_validate_nullability_override_targets``
            # before this loop runs, so the elif is exhaustive and unambiguous.
            if field.name in nullable_overrides:
                force_nullable: bool | None = True
            elif field.name in required_overrides:
                force_nullable = False
            else:
                force_nullable = None
            # ``convert_field_output`` owns the file/image branch: it routes a
            # FileField / ImageField to the structured DjangoFileType /
            # DjangoImageType output object (nullable by default as ``| None`` to
            # match the parent resolver's empty-file ``None``) and delegates
            # every other column to ``convert_scalar`` unchanged. A
            # ``required_overrides`` (``force_nullable=False``) entry is the
            # opt-in for a stronger non-empty invariant. The ``force_nullable`` tri-state
            # computed above is threaded through exactly as before; a consumer
            # ``attachment: str`` override is already skipped by the
            # ``consumer_authored_fields`` short-circuit above, so it receives
            # no generated object type (spec-037 Decision 3 / Decision 4).
            annotations[field.name] = convert_field_output(
                # Every ``ForeignObjectRel`` is a relation, so a non-relation entry is a column.
                cast("ConcreteField", field),
                truth.name(cls),
                force_nullable=force_nullable,
                expose_filesystem_path=field.name in filesystem_path_fields,
            )
    return annotations, pending
