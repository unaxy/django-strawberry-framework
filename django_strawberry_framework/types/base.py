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
    NoReturn,
    TypeAlias,
    TypeVar,
)

from django.db import models
from django.utils.functional import Promise
from strawberry import relay
from strawberry.relay.types import NodeIDPrivate
from strawberry.types.auto import StrawberryAuto
from strawberry.types.base import get_object_definition
from strawberry.types.field import StrawberryField
from typing_extensions import override

from django_strawberry_framework.conf import RELAY_GLOBALID_STRATEGY_KEY
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.keyset import validate_cursor_field_references
from django_strawberry_framework.optimizer.field_meta import FieldMeta
from django_strawberry_framework.optimizer.hints import OptimizerHint
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils import introspection
from django_strawberry_framework.utils._narrowing import (
    class_namespace,
    dict_of,
    is_class,
    is_dict,
    is_list,
    is_str,
    is_text_atom,
    is_tuple,
    list_of,
    read_attr,
)
from django_strawberry_framework.utils.querysets import (
    _concrete_or_none,
    _prefetch_relation_target_or_none,
)
from django_strawberry_framework.utils.relations import is_single_column_foreign_key, relation_kind
from django_strawberry_framework.utils.typing import is_async_callable, object_result

from .converters import _field_output_type_for, convert_field_output
from .definition import DjangoTypeDefinition, _check_graphql_name, surface_type_name
from .relations import PendingRelation, PendingRelationAnnotation
from .relay import install_is_type_of

if TYPE_CHECKING:
    from typing_extensions import TypeIs

    from django_strawberry_framework.filters.sets import FilterSet
    from django_strawberry_framework.optimizer.hints import _PrefetchAny
    from django_strawberry_framework.orders.sets import OrderSet
    from django_strawberry_framework.utils.typing import ModelField

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
    },
)
# ``filesystem_path_fields`` (spec-048 Decision 2),
# ``nullable_overrides`` / ``required_overrides`` (spec-029 Decision 6),
# ``connection`` (spec-030 Decision 8), ``globalid_strategy`` (spec-031
# Decision 6), ``relation_shapes`` (spec-032 Decision 7), and
# ``cursor_field`` (the spec-030 ``## Keyset cursors``
# opt-in) are ALLOWED keys whose features are live, NOT DEFERRED_META_KEYS
# entries: none of them is reserved-but-nonfunctional.

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
# every compose site. The ``_validate_relation_shapes`` gate passes its "or
# remove the key." tail instead; the parenthesized fifth-guard variants in
# ``relay.py`` / ``connection.py`` are a different byte shape and stay inline.
_RELAY_NODE_GATE_INHERIT_TAIL = "or inherit `relay.Node` directly."


def _require_relay_shape(
    subject: str,
    *,
    relay_shaped: bool,
    tail: str = _RELAY_NODE_GATE_INHERIT_TAIL,
) -> None:
    """Raise the Relay-Node gate's ``ConfigurationError`` for ``subject`` unless ``relay_shaped``."""
    if not relay_shaped:
        raise ConfigurationError(f"{subject} {_RELAY_NODE_GATE_LEAD} {tail}")


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
    if not (is_class(sidecar_class) and issubclass(sidecar_class, expected)):
        raise ConfigurationError(
            f"{model.__name__}.Meta.{meta_key} must be {article} {expected.__name__} subclass; "
            f"got {sidecar_class!r}",
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

    ``None``-short-circuits when unset; otherwise shape-checks the dict (the
    only recognized sub-key is ``{"total_count": bool}`` - unknown
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
    model_name = model.__name__
    if not is_dict(connection):
        raise ConfigurationError(
            f"{model_name}.Meta.connection must be a dict; got {connection!r}",
        )
    unknown = [key for key in connection if key != "total_count"]
    if unknown:
        unknown_labels = sorted(repr(key) for key in unknown)
        raise ConfigurationError(
            f"{model_name}.Meta.connection has unknown sub-keys: "
            f"[{', '.join(unknown_labels)}]. "
            "Only 'total_count' is recognized.",
        )
    # The returned options are built from the checks: the one recognized key, under its
    # own exact name, holding the bool it was proven to be.
    options: dict[str, bool] = {}
    if "total_count" in connection:
        total_count = connection["total_count"]
        if type(total_count) is not bool:
            raise ConfigurationError(
                f"{model_name}.Meta.connection['total_count'] must be a bool; got {total_count!r}",
            )
        options["total_count"] = total_count
    _require_relay_shape(f"{model_name}.Meta.connection", relay_shaped=relay_shaped)
    return options


def _is_str_tuple(entries: tuple[object, ...]) -> "TypeIs[tuple[str, ...]]":
    """Return whether every entry of ``entries`` is a ``str``."""
    return all(isinstance(entry, str) for entry in entries)


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
    owner = f"{model.__name__}.Meta.cursor_field"
    is_sequence = not is_text_atom(value) and issubclass(type(value), Sequence)
    # ``is_sequence`` read the value's real class as a ``Sequence``.
    entries = tuple(list_of(value)) if is_sequence else ()
    if not entries or not _is_str_tuple(entries):
        raise ConfigurationError(
            f"{owner} must be a non-empty non-string sequence of order strings; got {value!r}",
        )
    _ = validate_cursor_field_references(entries, owner=owner)
    _require_relay_shape(owner, relay_shaped=relay_shaped)
    return entries


def _validate_relation_shapes(
    model: type[models.Model],
    value: object,
    *,
    relay_shaped: bool,
) -> dict[str, str] | None:
    """Validate ``Meta.relation_shapes`` shape AND the Relay-Node requirement (spec-032 Decision 7).

    The shape stage of the relation-shapes validation flow, structurally modeled on
    ``_validate_connection`` and called from ``_validate_meta``:
    ``None``-short-circuits when unset (every eligible relation defaults to
    ``DEFAULT_RELATION_SHAPE`` at the Phase-2.5 synthesis); shape-checks the
    dict (string keys, values in ``RELATION_SHAPE_VALUES``); then enforces the
    Relay-Node gate with the spec-pinned "or remove the key" remediation tail.

    Field-level checks (unknown / excluded / non-relation / single-valued /
    consumer-authored) need the selected fields and the consumer-override
    union, which do not exist at ``_validate_meta`` time - they run in the
    field-name stage, ``_validate_relation_shape_targets``, from
    ``__init_subclass__`` (the spec-029 ``nullable_overrides`` two-stage
    precedent). The
    target-is-Node-shaped check runs at finalization, where relation targets
    are settled (Decision 6).

    Returns the normalized dict, stored on
    ``DjangoTypeDefinition.relation_shapes`` and read by the Phase-2.5
    relation-as-Connection synthesis.
    """
    if value is None:
        return None
    model_name = model.__name__
    if not is_dict(value):
        raise ConfigurationError(
            f"{model_name}.Meta.relation_shapes must be a dict mapping relation "
            f"field names to shapes; got {value!r}",
        )
    shapes: dict[str, str] = {}
    for key, shape in value.items():
        if not isinstance(key, str):
            raise ConfigurationError(
                f"{model_name}.Meta.relation_shapes keys must be relation field "
                f"name strings; got {key!r}.",
            )
        # The ``str`` test comes first so an unhashable value (e.g. ``{"items":
        # ["both"]}``) raises the configured ConfigurationError rather than
        # leaking ``TypeError: unhashable type`` from the set membership.
        if not isinstance(shape, str) or shape not in RELATION_SHAPE_VALUES:
            raise ConfigurationError(
                f"{model_name}.Meta.relation_shapes[{key!r}] "
                f"got unknown shape {shape!r}; valid shapes are "
                f"{sorted(RELATION_SHAPE_VALUES)}.",
            )
        shapes[key] = shape
    _require_relay_shape(
        f"{model_name}.Meta.relation_shapes",
        relay_shaped=relay_shaped,
        tail="or remove the key.",
    )
    return shapes


# The three positional parameters a ``callable`` GlobalID encoder must accept.
# The callable runs at encode time, BEFORE ``resolve_id``, so it never receives
# ``node_id``. It never receives ``info`` either: a callable
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
        f"{model.__name__}.Meta.globalid_strategy"
        if model is not None
        else RELAY_GLOBALID_STRATEGY_KEY
    )
    if isinstance(value, str):
        if value not in STRING_GLOBALID_STRATEGIES:
            raise ConfigurationError(
                f"{subject} got unknown strategy {value!r}; "
                f"valid strategies are {sorted(STRING_GLOBALID_STRATEGIES)} or a callable.",
            )
        normalized: GlobalIDStrategy = value
    elif callable(value):
        _validate_globalid_callable(subject, value)
        normalized = value
    else:
        raise ConfigurationError(
            f"{subject} must be one of {sorted(STRING_GLOBALID_STRATEGIES)} or a callable; "
            f"got {value!r}.",
        )
    # The Relay-Node-shape gate is a ``Meta``-only concern (the setting path's
    # per-type gate already ran at type creation); mirrors
    # ``_validate_connection``'s gate and remediation text.
    _require_relay_shape(subject, relay_shaped=relay_shaped or not is_meta)
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
    return any(isinstance(arg, NodeIDPrivate) for arg in args)


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
       confirms the shape so the id-field collision guard can accept the
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
    if is_str(raw):
        return bool(_NODEID_STRING_RE.search(introspection.text(raw)))
    return _has_node_id_marker(raw)


def _is_relay_shaped(cls: "type[DjangoType]", interfaces: tuple[type[object], ...]) -> bool:
    """Return True when ``cls`` or any entry in ``interfaces`` is a Relay-Node-shaped type.

    Single source of truth for the Relay-shape predicate: every reader computes
    the same boolean from the same inputs at its own timing, so the contract
    stays single-sited.
    """
    return any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)


# ``strawberry.auto`` is ``Annotated[Any, StrawberryAuto()]``; this alias carries the same
# marker over ``object`` so a consumer's ``name: auto`` does not spell ``Any``. The package
# root re-exports it; ``_is_auto_annotation`` recognizes it beside Strawberry's own.
#: Strawberry's one ``StrawberryAuto`` instance (its metaclass makes the class a singleton).
_AUTO_MARKER = object_result(StrawberryAuto)
auto: TypeAlias = Annotated[object, _AUTO_MARKER]  # noqa: PYI042 - the consumer spelling is ``auto``


def _is_auto_annotation(annotation: object) -> bool:
    """Return True for the ``field: auto`` declare-but-infer marker, every spelling.

    Recognized: the ``StrawberryAuto`` instance, ``strawberry.auto``, the package's
    own ``auto`` (``Annotated[object, StrawberryAuto()]``), the string ``"auto"``, and
    the string ``"strawberry.auto"``.

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
    # The package's ``auto`` annotates ``object``, which Strawberry's check does not
    # accept; its marker is found with ``in``, which compares each metadata entry by
    # identity and then by ``==``.
    if (
        typing.get_origin(annotation) is Annotated
        and _AUTO_MARKER in typing.get_args(annotation)[1:]
    ):
        return True
    return is_str(annotation) and introspection.text(annotation) in ("auto", "strawberry.auto")


class DjangoType:
    """Base class for Django-model-backed Strawberry GraphQL types."""

    _is_default_get_queryset: ClassVar[bool] = True
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
        has_custom_get_queryset = introspection.overrides(cls, DjangoType, "get_queryset")
        cls._is_default_get_queryset = not has_custom_get_queryset
        # The class's own namespace, read from the interpreter: an inherited
        # ``Meta`` does not make an intermediate base concrete.
        meta: object = class_namespace(cls).get("Meta")
        if meta is None:
            # A ``Meta``-less class registers nothing, so it is an abstract base only
            # while no concrete type sits above it. Under a concrete type it inherits that
            # type's definition: every annotation or resolver naming it would publish the
            # parent, dropping its own fields and never consulting its own
            # ``get_queryset`` (graphene-django refuses the same shape at class creation).
            inherited = read_attr(cls, "__django_strawberry_definition__", None)
            if isinstance(inherited, DjangoTypeDefinition):
                parent = inherited.origin.__name__
                raise ConfigurationError(
                    f"{cls.__name__} subclasses the concrete DjangoType {parent} without "
                    f"declaring its own `class Meta`, so it would publish as {parent}. Declare "
                    f"`class Meta` (with `model`) on {cls.__name__} for a second type of the "
                    "model, or make the shared base a Meta-less abstract subclass of DjangoType.",
                )
            return
        # Identity facts about ``cls`` are read once, here, from the
        # interpreter; every message below names the class by this value.
        type_name = cls.__name__
        if registry.is_finalized():
            raise ConfigurationError(
                f"finalize_django_types() already ran; cannot register {type_name} "
                "after finalization. Call registry.clear() first if this is a test.",
            )
        validated = _validate_meta(cls, meta)
        model = validated.model
        fields = _select_fields(model, validated.fields_spec, validated.exclude_spec)
        optimizer_hints = _validate_optimizer_hints(
            validated.optimizer_hints,
            fields,
            model=model,
            type_name=type_name,
        )

        field_map = {f.name: FieldMeta.from_django_field(f) for f in fields}
        consumer_annotations = dict(cls.__annotations__)
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
        consumer_annotated_relation_fields, consumer_annotated_scalar_fields = (
            _partition_by_relation(fields, consumer_annotations.keys() - auto_annotated_fields)
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
            has_id_assignment = isinstance(class_namespace(cls).get("id"), StrawberryField)
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
            meta_name=validated.name,
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
            selected_fields=tuple(fields),
            field_map=field_map,
            optimizer_hints=optimizer_hints,
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
        info: Any,  # pyright: ignore[reportExplicitAny, reportAny]  # noqa: ANN401 - consumer hook; an override narrows it
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
        resolver whose plan reaches this type. A ``FilterSet`` built outside a
        GraphQL execution with ``request=`` (``DjangoFilterBackend``,
        ``FilterView``, a consumer's own call) hands the hooks it reaches an
        ``info`` carrying only ``context.request``, that request, so
        ``info.context.request.user`` reads the actor on both paths; one built
        with no request hands ``None``.

        Cascading is the override's contract, which the package cannot check:
        a type with a non-null forward key into a type whose hook hides rows
        calls ``apply_cascade_permissions`` from its override (and narrows by
        hand an edge the helper cannot walk). Otherwise a row it shows whose
        key names a row the viewer cannot see reads as one whose related row
        is missing: the relation resolves ``None``, which a non-null field
        reports as a completion error, and a ``FilterSet`` ``isNull: true``
        test on the key matches the row.

        ``queryset`` is a fresh instance of the class that supplied it - for
        every framework-seeded read, the ``QuerySet`` class behind the model's
        default manager (``ProjectQuerySet.as_manager()``,
        ``Manager.from_queryset(...)``) - so an override can call that class's
        own methods. It carries the source's query state, routing, hints and
        prefetch lookups, not attributes the class sets on an instance outside
        Django's constructor arguments. A read that starts at the model (a root
        list or connection, a Relay id lookup, a write's target rows) and a
        nested many-side list or connection (Django's related managers subclass
        the default manager's class) are sourced from the default manager, so
        that query state is the manager's own. A read that reaches the model
        across a relation (a filter or ordering hop, a cascade edge, a
        single-valued relation) starts from every row of the model, in that same
        class, since Django's join reads no manager: the default manager's own
        ``get_queryset`` override contributes only its class there, no filter,
        annotation, ordering or other query state. A filter or hook that names a
        column the manager annotates is answered at a root and in a nested list
        or connection, and across a hop, a cascade edge or a single-valued
        relation only when the type's ``get_queryset`` adds it. Whatever the
        override returns is checked and cloned (``QuerySet.all()``) before the
        framework composes onto it.

        An override may be ``def`` or ``async def``. Under the asynchronous
        executor a ``def`` override runs off the event loop in a thread-sensitive
        ``sync_to_async`` worker - its own per call, or the worker an optimizer
        plan build runs in - so it may read the database; an ``async def``
        override is awaited on the event loop.
        """
        # the identity default reads no ``info``, but the readers pass it to every override
        del info
        return queryset

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
        ``UndeclaredHop.scope`` in ``utils/permissions.py`` (the hops a
        ``FilterSet`` relation path crosses); ``OrderSet`` (an order term across
        the relation reads ``NULL`` for a hidden row); the finalizer (refuses a
        ``FilterSet`` / ``OrderSet`` bound to two owners when either owner's hook
        is not the identity).

        Implementation: ``__init_subclass__`` stamps ``_is_default_get_queryset``
        on every subclass, ``Meta`` or not, from ``utils/introspection.py::overrides``;
        this method reads the class's own stamp.
        """
        return not read_attr(cls, "_is_default_get_queryset", True)


def _is_django_type_class(value: object) -> "TypeIs[type[DjangoType]]":
    """Return whether ``value`` is a ``DjangoType`` subclass, asked of its real MRO."""
    return is_class(value) and issubclass(value, DjangoType)


def _normalize_fields_spec(value: object) -> tuple[str, ...] | Literal["__all__"] | None:
    """Normalize ``Meta.fields`` for storage on ``DjangoTypeDefinition``."""
    if value is None:
        return value
    if is_str(value):
        if introspection.text(value) == "__all__":
            return "__all__"
        raise ConfigurationError(
            "Meta.fields must be '__all__' or a non-string sequence of field names",
        )
    if is_text_atom(value) or not issubclass(type(value), Sequence):
        raise ConfigurationError(
            "Meta.fields must be '__all__' or a non-string sequence of field names",
        )
    # The real-class check above proved a ``Sequence``.
    return _field_name_entries(value, "fields")


def _field_name_entries(value: object, key: str) -> tuple[str, ...]:
    """Return the entries of a ``Meta.{key}`` collection, refusing any that is not a ``str``."""
    entries = tuple(list_of(value))
    if _is_str_tuple(entries):
        return entries
    invalid = next(entry for entry in entries if not isinstance(entry, str))
    raise ConfigurationError(
        f"Meta.{key} must contain field name strings; got {invalid!r}",
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
    shape gate that contradicts its own semantics. A text atom
    (``utils/_narrowing.py::is_text_atom``: a ``str``, bytes-like value or lazy
    translation string) stays refused - it is iterable, so accepting it would
    silently read one field name as a sequence of single characters or bytes.
    """
    if value is None:
        return None
    if is_text_atom(value) or not issubclass(
        type(value),
        (Sequence, AbstractSet),
    ):
        raise ConfigurationError(
            f"Meta.{key} must be a non-string sequence or set of field names",
        )
    # The real-class check above proved a ``Sequence`` or ``AbstractSet``.
    return _field_name_entries(value, key)


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
    namespace = class_namespace(cls)
    for field in fields:
        if field.name in namespace and not isinstance(namespace[field.name], StrawberryField):
            kind = "relation" if field.is_relation else "scalar"
            raise ConfigurationError(
                f"{cls.__name__}.{field.name} shadows a Django {kind} field with an unsupported "
                "class attribute. Use a type annotation for type overrides, or use "
                "strawberry.field(resolver=...) / @strawberry.field for resolver overrides.",
            )
    return _partition_by_relation(fields, namespace.keys())


def _partition_by_relation(
    fields: "tuple[ModelField, ...]",
    names: AbstractSet[str],
) -> tuple[frozenset[str], frozenset[str]]:
    """Return the ``(relation, scalar)`` split of the selected ``fields`` named in ``names``."""
    named = [field for field in fields if field.name in names]
    return (
        frozenset(field.name for field in named if field.is_relation),
        frozenset(field.name for field in named if not field.is_relation),
    )


def _meta_optimizer_hints(meta: object, model: type[models.Model]) -> dict[str, object]:
    """Return ``meta.optimizer_hints`` as a dict, or ``{}`` when unset.

    Centralizes the shape guard used across ``__init_subclass__`` and the
    validators so non-mapping declarations fail before hint keys or
    values are inspected. The non-mapping rejection names the value's kind
    (``utils/introspection.py::kind``): an instance by its real class, a class by its
    own name (``got Category.``), never by its metaclass.
    """
    value = read_attr(meta, "optimizer_hints", None)
    if value is None:
        return {}
    if not issubclass(type(value), Mapping):
        raise ConfigurationError(
            f"{model.__name__}.Meta.optimizer_hints must be a mapping of field names to OptimizerHint "
            f"instances, got {introspection.kind(value)}.",
        )
    # The real-class check above proved a ``Mapping``. One pass over a plain copy of the
    # consumer mapping: the keys checked are the keys returned.
    hints: dict[str, object] = {}
    for key, hint in dict_of(value).items():
        if not isinstance(key, str):
            raise ConfigurationError(
                f"{model.__name__}.Meta.optimizer_hints keys must be field name strings; "
                f"got {key!r}.",
            )
        hints[key] = hint
    return hints


def _refuse_unknown_fields(
    *,
    model: type[models.Model],
    attr: str,
    unknown: list[str],
    available: set[str],
) -> NoReturn:
    """Raise the standard "unknown fields ... Available: ..." ``ConfigurationError``.

    Used by every validator that points at a typo in a ``Meta`` key naming
    model fields; ``attr`` names the offending key.  Centralizing the message
    keeps the consumer-visible error shape consistent across typo-guard sites.
    """
    raise ConfigurationError(
        f"{model.__name__}.Meta.{attr} names unknown fields: {unknown}. "
        f"Available: {sorted(available)}.",
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
    return f"{model.__name__}.{_INTERFACES_SHAPE_ERROR_LEAD_IN}, got {got_suffix}."


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
      ``get_object_definition(entry)`` answering an interface definition.
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
    raw = read_attr(meta, "interfaces", None)
    if raw is None:
        return ()
    if isinstance(raw, str):
        raise ConfigurationError(_interfaces_shape_error(model, "a string"))
    if is_class(raw):
        # Consumer-declared entries stay unproven until the loop below checks each one.
        entries: tuple[object, ...] = (raw,)
    elif is_tuple(raw) or is_list(raw):
        # The real-class check above proved a ``tuple`` or ``list``.
        entries = tuple(list_of(raw))
    else:
        raise ConfigurationError(_interfaces_shape_error(model, type(raw).__name__))
    if entries == ():
        return ()
    model_name = model.__name__
    seen_ids: set[int] = set()
    duplicates: list[str] = []
    interfaces: list[type[object]] = []
    for entry in entries:
        if isinstance(entry, str):
            raise ConfigurationError(
                f"{model_name}.Meta.interfaces must contain interface classes, "
                f"not strings (got {entry!r}). Lazy/forward-reference interface lookup is "
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
        if not is_class(entry):
            raise ConfigurationError(
                f"{model_name}.Meta.interfaces must contain interface classes, got {entry!r}.",
            )
        if issubclass(entry, DjangoType):
            raise ConfigurationError(
                f"{model_name}.Meta.interfaces may not contain DjangoType or "
                f"DjangoType subclasses (got {entry.__name__}). DjangoType is not a "
                "Strawberry interface.",
            )
        definition = get_object_definition(entry)
        if definition is None or not definition.is_interface:
            raise ConfigurationError(
                f"{model_name}.Meta.interfaces entry {entry.__name__} is not a "
                "Strawberry interface. Use @strawberry.interface or one of the "
                "strawberry.relay interface classes.",
            )
        entry_id = id(entry)
        if entry_id in seen_ids:
            duplicates.append(entry.__name__)
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

    A Django lazy proxy (``SimpleLazyObject``) forwards ``__class__`` but is not the class it
    stands for: a key whose gate reads the real type (``Meta.model``, ``Meta.fields``,
    ``Meta.name``, ``Meta.description``, an interface entry) refuses it with the same
    ``ConfigurationError`` as any other malformed value, and a key whose gate only iterates
    or compares (``Meta.interfaces`` as a whole, ``Meta.globalid_strategy``) reads through
    it (``utils/lazy.py`` states the rule).

    Validation order:

    1. ``Meta.model`` is required and must be a Django model class.
    2. ``fields`` and ``exclude`` are mutually exclusive.
    3. Any key in ``DEFERRED_META_KEYS`` raises with a clear message.
    4. Any key ``meta`` declares in its own body (underscore-prefixed keys
       skipped) not in ``ALLOWED_META_KEYS |
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
    model = read_attr(meta, "model", None)
    if model is None:
        raise ConfigurationError("Meta.model is required")
    if not (is_class(model) and issubclass(model, models.Model)):
        raise ConfigurationError("Meta.model must be a Django model class")
    model_name = model.__name__

    raw_name = read_attr(meta, "name", None)
    if raw_name is not None:
        if not is_str(raw_name):
            raise ConfigurationError(
                f"{model_name}.Meta.name must be a non-empty string; got {raw_name!r}.",
            )
        name = introspection.text(raw_name)
        if not name:
            raise ConfigurationError(
                f"{model_name}.Meta.name must be a non-empty string; got an empty name.",
            )
        _check_graphql_name(name, f"{model_name}.Meta.name")
    else:
        name = None

    raw_description = read_attr(meta, "description", None)
    description: str | Promise | None
    if raw_description is None or isinstance(raw_description, Promise):
        # A lazy translation string stays lazy until finalize, which renders it once.
        description = raw_description
    elif is_str(raw_description):
        # A str subclass's own ``__str__`` is consumer code; keep the plain text it holds.
        description = introspection.text(raw_description)
    else:
        raise ConfigurationError(
            f"{model_name}.Meta.description must be a string or a lazy translation "
            f"string; got {raw_description!r}.",
        )

    # ``meta``'s OWN namespace (no MRO walk) is deliberate for the typo-guard
    # below (the ``deferred`` / ``unknown`` checks): an unsupported key is
    # flagged only when THIS ``Meta`` declares it, so a base ``Meta``'s
    # already-validated keys are not re-flagged on every subclass. This is the
    # intentional counterpart to the MRO-walking ``read_attr`` check just
    # below; the two differ on purpose -- do not "unify" them.
    declared = sorted(key for key in vars(meta) if not key.startswith("_"))

    # Use the MRO-walking ``read_attr`` rather than own-namespace membership
    # so a child Meta inheriting ``fields`` from a base Meta still trips the
    # mutual-exclusion check when it declares ``exclude`` (and vice versa). ``fields = None``
    # (or ``exclude = None``) remains "unset" - matches
    # ``_normalize_fields_spec``'s treatment of ``None`` and the broader
    # convention that an explicit ``None`` means "no preference".
    has_fields = read_attr(meta, "fields", None) is not None
    has_exclude = read_attr(meta, "exclude", None) is not None
    if has_fields and has_exclude:
        raise ConfigurationError("Meta.fields and Meta.exclude are mutually exclusive")

    primary = read_attr(meta, "primary", False)
    if type(primary) is not bool:
        raise ConfigurationError("Meta.primary must be a bool")

    deferred = [key for key in declared if key in DEFERRED_META_KEYS]
    if deferred:
        raise ConfigurationError(
            f"Meta keys not supported yet: {deferred}. The feature that owns them has not shipped.",
        )

    unknown = [key for key in declared if key not in ALLOWED_META_KEYS]
    if unknown:
        raise ConfigurationError(f"Unknown Meta keys: {unknown}")

    fields_spec = _normalize_fields_spec(read_attr(meta, "fields", None))
    exclude_spec = _normalize_sequence_spec(read_attr(meta, "exclude", None), "exclude")
    optimizer_hints = _meta_optimizer_hints(meta, model)
    interfaces = _validate_interfaces(meta, model)
    relay_shaped = _is_relay_shaped(cls, interfaces)
    filterset_class = _validate_filterset_class(model, read_attr(meta, "filterset_class", None))
    orderset_class = _validate_orderset_class(model, read_attr(meta, "orderset_class", None))
    connection = _validate_connection(
        model,
        read_attr(meta, "connection", None),
        relay_shaped=relay_shaped,
    )
    cursor_field = _validate_cursor_field(
        model,
        read_attr(meta, "cursor_field", None),
        relay_shaped=relay_shaped,
    )
    globalid_strategy = _validate_globalid_strategy(
        model,
        read_attr(meta, "globalid_strategy", None),
        relay_shaped=relay_shaped,
    )
    relation_shapes = _validate_relation_shapes(
        model,
        read_attr(meta, "relation_shapes", None),
        relay_shaped=relay_shaped,
    )
    # Override shape stage (spec-029 Decision 8, shape + normalize): the two set-valued
    # keys reuse the shared collection guard (``_normalize_sequence_spec``, which
    # names the key it rejects), then normalize to ``frozenset``. The
    # both-sets collision is a shape-level contradiction visible from the raw
    # ``Meta`` alone (no model/field access needed), so it raises here rather
    # than in the target-validator. Target existence / scope checks
    # (unknown / excluded / consumer-authored / Relay-pk / relation) need the
    # selected fields and run later in ``_validate_nullability_override_targets``.
    nullable_overrides = frozenset(
        _normalize_sequence_spec(read_attr(meta, "nullable_overrides", None), "nullable_overrides")
        or (),
    )
    required_overrides = frozenset(
        _normalize_sequence_spec(read_attr(meta, "required_overrides", None), "required_overrides")
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
            read_attr(meta, "filesystem_path_fields", None),
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
    type_name: str,
) -> dict[str, OptimizerHint]:
    """Validate ``Meta.optimizer_hints`` keys and values in one pass.

    Combines the field-surface and value checks in one place:

    1. Every hint key names a field on the model (typo guard).
    2. Every hint key is in the type's selected relation field set.
       Excluded fields and selected scalar fields would silently drop
       optimizer intent otherwise - the walker only reads hints after
       entering the relation branch.
    3. Every hint value is an ``OptimizerHint`` instance.
    4. Every ``OptimizerHint.prefetch(Prefetch(lookup, queryset=seed))``
       without ``to_attr`` seeds rows the lookup's relation can serve
       (``_hinted_prefetch_seed_defect``).

    Field-name error sites route through ``_refuse_unknown_fields``
    so the consumer-visible shape matches ``Meta.fields`` /
    ``Meta.exclude`` typo guards; value errors use a dedicated
    ``OptimizerHint`` message.

    Args:
        hints: The pre-normalized ``Meta.optimizer_hints`` dict (already
            shape-checked by ``_meta_optimizer_hints`` inside
            ``_validate_meta``). Empty dict short-circuits.
        fields: The Meta-filtered list of Django field objects produced
            by ``_select_fields``. The selected relation field names
            are derived from it, so excluded or scalar fields with
            hints raise.
        model: The Django model whose ``_meta.get_fields()`` defines the
            valid hint key surface. Threaded from the validated
            ``Meta.model`` so the empty-``fields`` shape (e.g. ``Meta.exclude`` covering every
            field) is not fatal.
        type_name: The type's class name, named in the ``prefetch(obj)``
            seed-model refusal.

    Returns:
        The validated hints, every value an ``OptimizerHint``.

    """
    if not hints:
        return {}
    valid_field_names = {f.name for f in model._meta.get_fields()}
    selected_relation_names = {f.name for f in fields if f.is_relation}

    unknown_hint_fields = sorted(set(hints) - valid_field_names)
    if unknown_hint_fields:
        _refuse_unknown_fields(
            model=model,
            attr="optimizer_hints",
            unknown=unknown_hint_fields,
            available=valid_field_names,
        )
    excluded_hint_fields = sorted(set(hints) - selected_relation_names)
    if excluded_hint_fields:
        _refuse_unknown_fields(
            model=model,
            attr="optimizer_hints",
            unknown=excluded_hint_fields,
            available=selected_relation_names,
        )
    validated: dict[str, OptimizerHint] = {}
    bad_values: list[str] = []
    for key, value in hints.items():
        if isinstance(value, OptimizerHint):
            validated[key] = value
        else:
            bad_values.append(key)
    if bad_values:
        raise ConfigurationError(
            "optimizer_hints values must be OptimizerHint instances, "
            f"got non-OptimizerHint for: {sorted(bad_values)}",
        )
    for key, hint in validated.items():
        if hint.prefetch_obj is None:
            continue
        defect = _hinted_prefetch_seed_defect(model, hint.prefetch_obj)
        if defect is not None:
            raise ConfigurationError(
                f"OptimizerHint.prefetch(obj) on {type_name}.{key}: {defect}",
            )
    return validated


def _hinted_prefetch_seed_defect(
    model: type[models.Model],
    prefetch: "_PrefetchAny",
) -> str | None:
    """Return why a hinted seed cannot serve its relation, or ``None`` when it can.

    Django builds a prefetch's rows from its queryset's ``Query.model`` and
    hands them to the lookup's final relation as they are, so a seed serves the
    relation only when its model is the relation's target or a proxy of it: a
    subclass sharing the target's concrete model reads the target's table and
    yields instances the target type's ``is_type_of`` accepts. The target's
    concrete model under a proxy target, a sibling proxy, a multi-table child or
    parent and an unrelated model are refused, and both the public
    ``QuerySet.model`` and the row-building ``Query.model`` must pass, a model
    slot that holds no model class failing closed. The target comes from
    Django's relation metadata through
    ``utils/querysets.py::_prefetch_relation_target_or_none``, over the lookup
    read as exact text (a ``TextChoices`` / ``StrEnum`` member resolves as its
    text); a lookup it cannot resolve (a generic
    relation, a lazy string target) is left to Django at fetch. Only a
    ``Prefetch`` without ``to_attr`` is checked: a ``to_attr`` lands its rows on
    that attribute, which only a consumer-assigned resolver reads, never on the
    relation's cache, and a ``Prefetch`` with no queryset has no seed.
    """
    queryset = prefetch.queryset
    if queryset is None or prefetch.to_attr:
        return None
    lookup = introspection.text(prefetch.prefetch_through)
    target = _prefetch_relation_target_or_none(model, lookup)
    if target is None:
        return None
    concrete = _concrete_or_none(target)
    for row_model in (queryset.query.model, queryset.model):
        if not (
            is_class(row_model)
            and issubclass(row_model, target)
            and _concrete_or_none(row_model) is concrete
        ):
            served, wanted = introspection.name(row_model), target.__name__
            return (
                f"the hinted Prefetch({lookup!r}) queryset is over {served} rows, but the "
                f"{lookup!r} relation targets {wanted} rows. Django builds the prefetched rows "
                f"from the queryset's model, so the relation would serve {served} instances in "
                f"place of {wanted} ones. Pass a queryset over {wanted} (or a proxy model of it)."
            )
    return None


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
    ``_refuse_unknown_fields`` keyed on ``attr`` so the consumer-visible
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
        _refuse_unknown_fields(
            model=model,
            attr=attr,
            unknown=unknown,
            available=model_field_names,
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

    The target-validation stage of the override flow (spec-029 Decision 8). Runs in
    ``__init_subclass__`` AFTER ``_select_fields`` + ``consumer_authored_fields``
    + the Relay-shape check, so the selected fields, the consumer-override set,
    and the Relay-pk identity all exist. The shape check + both-sets collision
    already ran earlier in ``_validate_meta``; this helper only validates the
    union of the two normalized sets against the model and selected fields.

    Two distinct name sets are derived as separate error paths so the
    ``Meta.exclude`` contract is not collapsed into "unknown": the model-wide
    names (``model._meta.get_fields()``) gate the *unknown-field* path, and the
    selected-field names gate the *excluded / not-selected* path. The unknown
    path routes through ``_refuse_unknown_fields`` so its consumer-visible
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
            f"{model.__name__}.Meta nullable_overrides/required_overrides name fields not in "
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
                f"{model.__name__}.Meta nullable_overrides/required_overrides names "
                f"consumer-authored field {name!r}; a consumer annotation or strawberry.field "
                "assignment already controls its nullability. Drop the override and control "
                "nullability through the annotation instead.",
            )
        if name == relay_pk_name:
            raise ConfigurationError(
                f"{model.__name__}.Meta nullable_overrides/required_overrides names the "
                f"Relay-Node-suppressed pk {name!r}; the pk's nullability is the relay.Node "
                "interface's contract (id: GlobalID!), not the column's, and cannot be overridden.",
            )
        if selected_by_name[name].is_relation:
            raise ConfigurationError(
                f"{model.__name__}.Meta nullable_overrides/required_overrides names relation "
                f"field {name!r}; nullability overrides apply to non-relation "
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
            f"{model.__name__}.Meta filesystem_path_fields names fields not in the selected "
            f"set: {excluded}. "
            "The opt-in targets a field that will not appear in the GraphQL "
            "type (excluded via Meta.exclude or absent from a subset Meta.fields); select the "
            "field or drop the opt-in."
        ),
    )
    for name in sorted_targets:
        if name in consumer_authored_fields:
            raise ConfigurationError(
                f"{model.__name__}.Meta filesystem_path_fields names consumer-authored field "
                f"{name!r}; a consumer annotation or strawberry.field assignment already owns "
                "that field's output type, so the opt-in would have no effect. Drop the opt-in "
                "and expose the path from the consumer resolver instead.",
            )
        if _field_output_type_for(selected_by_name[name]) is None:
            raise ConfigurationError(
                f"{model.__name__}.Meta filesystem_path_fields names {name!r}, which is not a "
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

    The field-name stage of the relation-shapes validation flow (spec-032 Decision 7,
    structurally the ``_validate_nullability_override_targets`` sibling). Runs
    in ``__init_subclass__`` AFTER ``_select_fields`` + ``consumer_authored_fields``
    exist, because every check here needs the selected fields, the cardinality
    classifier, or the consumer-override union - none of which exist at
    ``_validate_meta`` time. The shape check + Relay-Node gate already ran in
    the shape stage (``_validate_relation_shapes``).

    Check order mirrors the sibling: unknown -> excluded -> per-name checks
    (non-relation / single-valued / consumer-authored), iterating keys sorted
    for deterministic messages. The unknown path routes through
    ``_refuse_unknown_fields`` so its consumer-visible shape matches the
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
            f"{model.__name__}.Meta.relation_shapes names fields not in the selected set: "
            f"{excluded}. "
            "The entry targets a field that will not appear in the GraphQL type "
            "(excluded via Meta.exclude or absent from a subset Meta.fields); select the field "
            "or drop the entry."
        ),
    )
    for name in sorted_targets:
        if not selected_by_name[name].is_relation:
            raise ConfigurationError(
                f"{model.__name__}.Meta.relation_shapes names non-relation field {name!r}; "
                "only many-side relations (reverse FK, forward/reverse M2M) can take a "
                "connection shape.",
            )
        if not field_map[name].is_many_side:
            kind = field_map[name].relation_kind
            if kind == "reverse_one_to_one":
                shape = "reverse OneToOne"
            elif kind == "reverse_generic":
                shape = "reverse GenericRelation"
            elif is_single_column_foreign_key(selected_by_name[name]):
                shape = "forward FK / OneToOne"
            else:
                shape = "forward ForeignObject"
            raise ConfigurationError(
                f"{model.__name__}.Meta.relation_shapes names single-valued relation {name!r} "
                f"({shape}); there is nothing to paginate. Only many-side "
                "relations (reverse FK, forward/reverse M2M) can take a connection shape.",
            )
        if name in consumer_authored_fields:
            raise ConfigurationError(
                f"{model.__name__}.Meta.relation_shapes names consumer-authored relation "
                f"{name!r}; a consumer annotation or strawberry.field assignment owns that "
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
    all_fields = tuple(model._meta.get_fields())
    valid_names = {f.name for f in all_fields}
    if fields_spec == "__all__":
        return all_fields
    if fields_spec is not None:
        attr, names = "fields", set(fields_spec)
    elif exclude_spec is not None:
        attr, names = "exclude", set(exclude_spec)
    else:
        return all_fields
    unknown = sorted(names - valid_names)
    if unknown:
        _refuse_unknown_fields(model=model, attr=attr, unknown=unknown, available=valid_names)
    selected_names = names if attr == "fields" else valid_names - names
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

    Reconsideration triggers: a new suppressed member extends this body (every
    caller follows); a pk-identity change lands on the ``_meta.pk.name``
    read; a new suppression exemption lands here, never as a second predicate
    at a caller.
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
    meta_name: str | None,
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
        cls: The consumer-facing ``DjangoType`` subclass.
        fields: The Meta-filtered list of Django field objects.
        source_model: The Django model the type wraps. The primary-key name
            is resolved from it when ``relay.Node`` suppression is active.
        meta_name: The validated ``Meta.name`` (``None`` when unset). With
            ``cls`` it gives the published type name
            (``types/definition.py::surface_type_name``) that threads into
            ``convert_field_output`` (and on to ``convert_scalar``) as the
            generated choice enums' prefix, so a ``Meta.name``'d type's enum
            carries the name the type publishes, whichever of its read or its
            filterset reaches the column first.
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
            (raised by ``convert_scalar`` via ``convert_field_output``), a
            selected relation has no concrete related model to map to a
            GraphQL type, or a selected relation is the reverse ``GenericRel``
            of a ``GenericRelation`` (``relation_kind`` ``"reverse_generic"``).

    """
    annotations: dict[str, object] = {}
    pending: list[PendingRelation] = []
    type_name = surface_type_name(cls, meta_name)
    for field in fields:
        # Every ``ForeignObjectRel`` is a relation, so the ``else`` branch is a column.
        if isinstance(field, models.ForeignObjectRel) or field.is_relation:
            if field.name in consumer_authored_fields:
                continue
            related_model = field.related_model
            if related_model is None:
                raise ConfigurationError(
                    f"{source_model.__name__}.{field.name} is a GenericForeignKey or other "
                    "relation without a concrete related model. It cannot be auto-mapped to "
                    "a single GraphQL type. Exclude it via Meta.exclude, or supply an "
                    "explicit annotation or resolver.",
                )
            if relation_kind(field) == "reverse_generic":
                raise ConfigurationError(
                    f"{source_model.__name__}.{field.name} is the reverse side of a "
                    "GenericRelation (its related_query_name). Django can neither "
                    "select_related it nor read it as a related object, so it cannot be "
                    "auto-mapped to a GraphQL type. Exclude it via Meta.exclude, or supply an "
                    "explicit annotation or resolver.",
                )
            # Deferred, never bound here: binding at ``__init_subclass__`` would freeze the
            # relation against whichever type is registered at that moment, which mis-binds
            # when a secondary registers before the primary (spec-018 Decision 6).
            pending.append(
                PendingRelation(
                    source_type=cls,
                    source_model=source_model,
                    field_name=field.name,
                    related_model=related_model,
                ),
            )
            annotations[field.name] = PendingRelationAnnotation
        else:
            if field.name in consumer_authored_fields:
                # A consumer-assigned ``StrawberryField`` (or annotation) on a scalar column
                # wins over the auto-synthesized annotation, as on the relation branch.
                continue
            if _is_suppressed_relay_pk(
                cls,
                interfaces,
                source_model,
                field,
                consumer_authored_fields,
            ):
                continue
            # Nullability tri-state (spec-029 Decision 7): ``None`` leaves the column's own
            # default; the two sets are disjoint (``_validate_nullability_override_targets``
            # runs before this loop), so the elif is exhaustive.
            if field.name in nullable_overrides:
                force_nullable: bool | None = True
            elif field.name in required_overrides:
                force_nullable = False
            else:
                force_nullable = None
            # File / image output is nullable by default to match the parent resolver's
            # empty-file ``None`` (spec-037 Decision 4).
            annotations[field.name] = convert_field_output(
                field,
                type_name,
                force_nullable=force_nullable,
                expose_filesystem_path=field.name in filesystem_path_fields,
            )
    return annotations, pending
