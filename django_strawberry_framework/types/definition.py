"""``DjangoTypeDefinition`` - canonical metadata for collected ``DjangoType`` classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from django.core.exceptions import FieldDoesNotExist
from graphql import GraphQLError, assert_name
from strawberry import relay
from strawberry.relay.exceptions import NodeIDAnnotationError
from strawberry.utils.str_converters import to_camel_case

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils import truth

from .relay import _STRAWBERRY_RESOLVE_ID

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypeAlias

    from django.db import models
    from django.utils.functional import Promise

    from django_strawberry_framework.filters.sets import FilterSet
    from django_strawberry_framework.optimizer.field_meta import FieldMeta
    from django_strawberry_framework.optimizer.hints import OptimizerHint
    from django_strawberry_framework.orders.sets import OrderSet
    from django_strawberry_framework.utils.typing import ModelField

    from .base import DjangoType

    #: A consumer ``globalid_strategy`` encoder, validated to bind
    #: ``(type_cls, model, root)``. Its return is checked per call
    #: (``types/relay.py::encode_typename``), so it is typed ``object``.
    GlobalIDEncoder: TypeAlias = Callable[[type[DjangoType], type[models.Model], object], object]
    #: A validated ``globalid_strategy``: a ``STRING_GLOBALID_STRATEGIES`` name or an encoder.
    GlobalIDStrategy: TypeAlias = str | GlobalIDEncoder


def _check_graphql_name(name: str, subject: str) -> None:
    """Raise ``ConfigurationError`` unless ``name`` is a GraphQL Name a type can publish.

    graphql-core's ``assert_name`` owns the Name grammar; the ``__`` prefix GraphQL
    reserves for introspection is enforced by graphql-core only while validating a
    built schema, so it is checked here, where the name is declared.
    """
    message = f"{subject} must be a valid GraphQL name; got {truth.render(name)}."
    try:
        _ = assert_name(name)
    except GraphQLError as exc:
        raise ConfigurationError(message) from exc
    if name.startswith("__"):
        raise ConfigurationError(message)


def surface_type_name(origin: type, name: str | None) -> str:
    """Return the GraphQL type name ``origin`` publishes: ``name`` when set, else its re-cased class name.

    ``name`` is the type's ``Meta.name`` (``_validate_meta`` checks it when declared).
    Strawberry derives the surface name the same way under the default
    ``NameConverter``: an unnamed class publishes ``to_camel_case(__name__)``
    (``strawberry/types/object_type.py``), so ``Cat_Node`` publishes ``CatNode`` and
    the connection, filter inputs and enums named from it follow. Derivation only:
    the class-name fallback is not checked against the GraphQL Name grammar here,
    since a schema's converter may publish
    another name for a class name the grammar refuses;
    ``DjangoTypeDefinition.graphql_type_name`` checks the result. It and the
    read-side choice-enum prefix (``types/base.py::_build_annotations``, which runs
    before the definition exists) both derive the name here, so a ``Meta.name``'d
    type names its enums after the name it publishes.
    """
    return name if name is not None else to_camel_case(truth.name(origin))


@dataclass
class DjangoTypeDefinition:
    """Collected metadata for a model-backed ``DjangoType`` subclass.

    The dataclass is the canonical metadata record consumed by the
    registry, optimizer, finalizer, relay interface injection, and
    relation resolvers. It has a single construction site in
    ``DjangoType.__init_subclass__`` (``types/base.py``).

    Invariants:
        - ``field_map`` is built and owned by
          ``DjangoType.__init_subclass__`` and treated as immutable by
          every reader (walker, extension, resolvers, finalizer). The
          ``dict`` type is a runtime convenience, not a license to
          mutate post-construction.
        - ``selected_fields`` carries Django field instances in
          ``Model._meta.get_fields()`` selection order; readers may
          rely on that order for stable iteration.
        - ``finalized`` flips exactly once, in
          ``finalize_django_types()`` (``types/finalizer.py``), and
          gates the re-finalization short-circuit; no other site may
          assign it.
        - The four ``consumer_*_fields`` frozensets are the four-corner
          override contract (annotated-vs-assigned x relation-vs-scalar)
          described in ``types/base.py``; their union,
          ``consumer_authored_fields``, is the short-circuit input
          ``_build_annotations`` reads to skip auto-synthesis for any
          name the consumer authored.
        - ``primary`` is a write-once introspection mirror of
          ``registry._primaries[model]``, owned by
          ``DjangoType.__init_subclass__`` (``types/base.py``) and never
          mutated post-construction. No package code reads it; the
          runtime "is this the primary?" predicate is
          ``registry.primary_for(model)`` (``registry.py``). Consumers
          may read ``definition.primary`` for introspection only.
        - ``filterset_class`` is the per-owner ``FilterSet`` sidecar
          populated by ``DjangoType.__init_subclass__`` from
          ``Meta.filterset_class``; consumed by
          ``finalize_django_types()`` phase 2.5 to bind the owning
          ``DjangoTypeDefinition`` on the FilterSet and to materialize
          the generated Strawberry input class as a module global of
          ``django_strawberry_framework.filters.inputs``.
        - ``orderset_class`` is the per-owner ``OrderSet`` sidecar
          populated by ``DjangoType.__init_subclass__`` from
          ``Meta.orderset_class``; consumed by
          ``finalize_django_types()`` phase 2.5 to bind the owning
          ``DjangoTypeDefinition`` on the OrderSet and to materialize
          the generated Strawberry input class as a module global of
          ``django_strawberry_framework.orders.inputs``.
        - ``fields_class`` is the forward-reserved ``FieldSet`` sidecar
          slot for spec-059. It intentionally stays
          ``None`` while ``Meta.fields_class`` remains in
          ``DEFERRED_META_KEYS``; spec-059 promotes the key and
          populates this slot when resolver binding applies end-to-end.
        - ``connection`` is the normalized ``Meta.connection`` value
          (``{"total_count": bool} | None``) populated by
          ``DjangoType.__init_subclass__`` from the validated ``Meta``
          (spec-030 Decision 8); consumed by
          ``connection.py::_connection_type_for`` to decide whether to
          emit the per-target ``<TypeName>Connection`` carrying the
          opt-in ``totalCount`` field.
        - ``relation_shapes`` is the normalized ``Meta.relation_shapes`` value
          (``dict[str, str] | None``, values in ``{"list", "connection",
          "both"}``) normalized by ``types/base.py::_validate_relation_shapes``
          (plus the stage-2 target validator
          ``_validate_relation_shape_targets``), populated by
          ``DjangoType.__init_subclass__`` (spec-032 Decision 7); consumed by
          the ``finalize_django_types()`` Phase-2.5 relation-as-Connection
          synthesis (``types/finalizer.py::_synthesize_relation_connections``)
          to resolve each eligible many-side relation's shape (absent keys
          default to ``DEFAULT_RELATION_SHAPE`` from ``types/base.py``,
          currently ``"connection"`` per spec-047 Decision 5).
        - ``relation_connections`` maps each synthesized relation
          connection's GENERATED Python attribute name to the UNDERLYING
          relation field name (``{"books_connection": "books"}``). Written
          once per attached sibling by the Phase-2.5 synthesis
          (``types/finalizer.py::_synthesize_relation_connections``); the
          suppressed shapes (``"list"`` narrowing, non-Node target,
          consumer-authored) record nothing, so the slot's keys are exactly
          the connections that genuinely exist. Read by
          ``optimizer/walker.py::_walk_selections`` to recognize a nested
          ``<field>Connection`` selection through definition metadata - the
          same channel it uses for ``field_map`` / ``optimizer_hints`` -
          without reaching into ``connection.py`` internals or the
          ``_dst_synthesized_relation_connection`` field marker (spec-033
          Decision 3). The walker resolves connection and model-field names
          through the same boundary: an exact reverse lookup first, then an
          authoritative forward match through the active Strawberry name
          converter when reversal is lossy or impossible.
        - ``globalid_strategy`` is the raw normalized ``Meta.globalid_strategy``
          value (``"model"`` / ``"type"`` / ``"type+model"`` / a callable /
          ``None``) populated by ``DjangoType.__init_subclass__`` from the
          validated ``Meta`` (spec-031 Decision 6); ``None`` means the per-type
          opt-in is absent and the precedence resolver
          (``types/relay.py::_resolve_globalid_strategy``) falls through to the
          ``RELAY_GLOBALID_STRATEGY`` setting then the ``"model"`` default.
        - ``effective_globalid_strategy`` is the finalization-time encode/decode
          classification string (``"model"`` / ``"type"`` / ``"type+model"`` /
          ``"callable"`` / ``"custom"``), distinct from the raw
          ``globalid_strategy`` slot above (a raw callable value and the resolved
          ``"callable"`` classification string are different things - spec-031
          Decision 10). It is set exactly once by the
          Phase-2.5 ``install_globalid_typename_resolver`` step
          (``types/relay.py``), read by ``decode_global_id`` and the
          strategy-aware ``GlobalID`` filter, and doubles as that step's
          re-entrancy guard (a non-``None`` value means "already processed in a
          prior partial finalize - skip"). ``None`` means "not a
          framework-decodable Relay-Node type" (the install step runs for Relay
          types only): decode rejects such a candidate (spec-031 Decision 8),
          and the strategy-aware ``GlobalID`` filter fails closed on it too - a
          known ``None`` on a resolved definition raises the coded
          ``GLOBALID_UNVALIDATABLE`` error at request time
          (``filters/base.py::_decode_and_validate_global_id``, the runtime
          backstop behind the build-time audit). The only surviving
          node-id-only paths are those with no target definition - and
          therefore no strategy - at all: no owner, an unbound set's own key,
          or a path into a model no ``DjangoType`` exposes (spec-031
          Decision 13).
        - ``related_target_for(field_name)`` resolves the
          ``(target_definition, model_field)`` pair the GlobalID filter's
          request-time path walk consults segment by segment; the lookup walks
          ``self.model._meta`` and resolves the target ``DjangoType``
          via ``registry.get(target_model)`` (which itself honors
          ``Meta.primary`` as its first return state, then falls back
          to the single-registered-type rule). Returns ``None`` for
          non-relation fields and for fields not present on the model.
        - ``has_custom_id_resolver_for(pk_name, pk_is_relation=...)``
          memoizes the custom id resolver check used by the optimizer's
          FK-id elision guard. It reports both an ``origin`` MRO-level id
          resolver override (ignoring the framework-installed Relay
          default) and a ``relay.NodeID`` annotation pointing off the pk
          column; both inputs are stable for a definition's lifetime.
    """

    origin: type[DjangoType]
    model: type[models.Model]
    name: str | None
    description: str | Promise | None
    fields_spec: tuple[str, ...] | Literal["__all__"] | None
    exclude_spec: tuple[str, ...] | None
    selected_fields: tuple[ModelField, ...]
    field_map: dict[str, FieldMeta]
    optimizer_hints: dict[str, OptimizerHint]
    has_custom_get_queryset: bool
    consumer_authored_fields: frozenset[str] = frozenset()
    consumer_annotated_relation_fields: frozenset[str] = frozenset()
    consumer_annotated_scalar_fields: frozenset[str] = frozenset()
    consumer_assigned_relation_fields: frozenset[str] = frozenset()
    consumer_assigned_scalar_fields: frozenset[str] = frozenset()
    primary: bool = False
    interfaces: tuple[type[object], ...] = ()
    # ``interfaces`` is populated by ``_validate_meta``; consumed by
    # ``finalize_django_types()`` as the finalizer's source of truth for
    # base injection.
    filterset_class: type[FilterSet] | None = None
    orderset_class: type[OrderSet] | None = None
    fields_class: type[object] | None = None
    connection: dict[str, bool] | None = None
    # Keyset-cursor opt-in (the spec-030 ``## Keyset cursors`` contract):
    # the validated ``Meta.cursor_field`` order strings, or ``None`` for the
    # shipped offset-cursor behavior. When set, every connection over this
    # type is KEYSET-MODE: it orders by these columns, mints value-encoded
    # signed cursors (``keyset.py``), and rejects offset cursors. Shape is
    # validated at class creation (``types/base.py::_validate_cursor_field``);
    # the column contract (local / concrete / non-nullable / unique terminal)
    # at finalization (``keyset.validate_cursor_field_columns``).
    cursor_field: tuple[str, ...] | None = None
    # Per-relation shape declaration; values pre-normalized to
    # {"list", "connection", "both"} (spec-032 Decision 7). See the
    # invariants docstring above.
    relation_shapes: dict[str, str] | None = None
    # Walker-readable synthesis slot (spec-033 Decision 3): maps each
    # synthesized connection's GENERATED Python attribute name to the
    # UNDERLYING relation field name (``{"books_connection": "books"}``).
    # See the invariants docstring above for the full read/write contract.
    relation_connections: dict[str, str] | None = None
    globalid_strategy: GlobalIDStrategy | None = None
    # Finalization-set encode/decode classification (spec-031 Decision 10).
    # Unlike the raw ``globalid_strategy`` slot above (populated at class
    # creation), it is set exactly once by the Phase-2.5 typename resolver
    # install (``types/relay.py::install_globalid_typename_resolver``) and
    # doubles as its re-entrancy guard. ``None`` => not a framework-decodable
    # Relay-Node type.
    effective_globalid_strategy: str | None = None
    finalized: bool = False
    # Per-instance memoization of ``related_target_for(field_name)``
    # results. Cache stores the full
    # ``(target_definition, model_field) | None`` tuple keyed by field
    # name (a ``None`` value IS a valid cached result; no in-band
    # sentinel is required). Populated lazily on first call. Definitions are
    # created fresh by ``DjangoType.__init_subclass__`` after every
    # ``registry.clear()`` so stale-cache contamination is bounded to
    # consumer code holding references to discarded definitions -
    # which would surface the same staleness on any direct attribute
    # read.
    _related_target_cache: dict[str, tuple[DjangoTypeDefinition, ModelField] | None] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )
    # Per-instance memoization of ``has_custom_id_resolver_for``. Values are
    # keyed by (concrete model primary-key field name, whether that key is a
    # relation), the two inputs the answer depends on, and include negative
    # results; use membership checks instead of ``dict.get`` so ``False``
    # remains a valid cached answer.
    _custom_id_resolver_cache: dict[tuple[str, bool], bool] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )

    @property
    def graphql_type_name(self) -> str:
        """Return the GraphQL type name Strawberry emits for this definition.

        That is the name under the default ``NameConverter``; a schema's converter
        can publish another name (``types/relay.py::published_node_type_name``).
        Strawberry derives the surface name as ``self.name`` when set,
        falling back to the origin class's re-cased name; the derivation is
        ``surface_type_name``, which every call site needing it reads
        (``finalizer.py``, ``filters/base.py``, ``filters/inputs.py`` through
        this property, ``types/base.py::_build_annotations`` directly) so the
        copies cannot diverge across renames. This property also checks the
        name is a non-empty string and a GraphQL Name.
        """
        published = surface_type_name(self.origin, self.name)
        label = truth.kind(self.origin)
        if not truth.is_instance(published, str):
            raise ConfigurationError(
                f"GraphQL type name for {label} must be a non-empty string; "
                f"got {truth.render(published)}.",
            )
        normalized = truth.text(published)
        if not normalized:
            raise ConfigurationError(
                f"GraphQL type name for {label} must be a non-empty string; got an empty name.",
            )
        _check_graphql_name(normalized, f"GraphQL type name for {label}")
        return normalized

    def related_target_for(
        self,
        field_name: object,
    ) -> tuple[DjangoTypeDefinition, ModelField] | None:
        """Return ``(target_definition, model_field)`` for a relation field.

        Walks ``self.model._meta.get_field(field_name)``; returns
        ``None`` when the field does not exist on the model (caught
        ``FieldDoesNotExist``) and ``None`` when the resolved field is
        not a relation. For a relation, resolves the target model via
        ``field.related_model`` (the canonical attribute on every
        Django relation field - forward FK / OneToOne / M2M, reverse FK
        / OneToOne / M2M). The target ``DjangoType`` is resolved via
        ``registry.get(target_model)`` - the registry's own first
        return state honors ``Meta.primary`` declarations, and the
        fallback path preserves the single-type-no-primary rule.
        Returns ``None`` when no ``DjangoType`` is registered for the
        target model.
        """
        if not truth.is_instance(field_name, str):
            return None
        field_name = truth.text(field_name)

        # In-function import: ``registry`` stays a method-local edge so this
        # module does not depend on it at import time (no load cycle exists
        # either way -- ``registry.py`` keeps its ``types.*`` edges
        # ``TYPE_CHECKING``-only). Do NOT hoist to module top.
        from django_strawberry_framework.registry import registry  # noqa: PLC0415

        # Memoize the lookup per field name. ``_meta.get_field`` is
        # cheap but not free, and the registry lookup is two calls
        # (``registry.get`` for the target type, then
        # ``get_definition``); on the filter-evaluation hot path this
        # adds up. Cache only valid post-finalize: pre-finalize the
        # registry can still mutate (consumer declares more
        # DjangoTypes), so populating the cache with a transient
        # ``None`` would lock in a wrong answer. ``finalized`` flips
        # exactly once and is the package's "registry is stable now"
        # signal.
        cache_ok = registry.is_finalized()
        if cache_ok and field_name in self._related_target_cache:
            return self._related_target_cache[field_name]

        try:
            model_field = self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            model_field = None
        result = None
        if model_field is not None and model_field.is_relation:
            target_model = model_field.related_model
            target_type = registry.get(target_model) if target_model is not None else None
            if target_type is not None:
                target_definition = registry.get_definition(target_type)
                if target_definition is not None:
                    result = (target_definition, model_field)

        if cache_ok:
            self._related_target_cache[field_name] = result
        return result

    def has_custom_id_resolver_for(self, pk_name: str, *, pk_is_relation: bool = False) -> bool:
        """Return whether ``origin`` resolves its id from something other than ``pk_name``.

        Reports the two shapes that make pk-only FK-id elision unsafe:

        - a consumer id resolver override (the framework-installed Relay
          default is *not* counted): ``resolve_{pk_name}`` or an attribute
          named ``pk_name`` for a scalar key; ``resolve_id`` for a key that
          is a relation (``pk_is_relation``), since the attribute named after
          such a key is the relation field's own resolver, never the id's; or
        - a ``relay.NodeID`` annotation pointing at a non-pk column, so the
          GlobalID is built from a column the FK-id stub does not carry.

        Memoized per ``(pk_name, pk_is_relation)``; both inputs (MRO class
        attributes and the ``NodeID`` annotation) are stable for the
        definition's lifetime.
        """
        normalized_pk_name = _normalize_pk_name(pk_name)
        if normalized_pk_name is None:
            return False
        cache_key = (normalized_pk_name, pk_is_relation)
        if cache_key in self._custom_id_resolver_cache:
            return self._custom_id_resolver_cache[cache_key]

        result = origin_has_custom_id_resolver(
            self.origin,
            normalized_pk_name,
            pk_is_relation=pk_is_relation,
        )
        self._custom_id_resolver_cache[cache_key] = result
        return result


def origin_has_custom_id_resolver(
    origin: type[object],
    pk_name: str,
    *,
    pk_is_relation: bool = False,
) -> bool:
    """Return whether ``origin`` customizes id resolution away from ``pk_name``.

    Shared by ``DjangoTypeDefinition.has_custom_id_resolver_for`` (the memoized
    hot path) and the optimizer's definition-less fallback so the two cannot
    drift. See ``has_custom_id_resolver_for`` for the two shapes detected and
    for what ``pk_is_relation`` changes. A relation key's own name is skipped
    because ``types/resolvers.py::_attach_relation_resolvers`` installs the
    relation resolver under it whenever the type lists the key, and that
    resolver never builds the id.
    """
    normalized_pk_name = _normalize_pk_name(pk_name)
    if normalized_pk_name is None:
        return False
    resolver_names = (
        ("resolve_id",)
        if pk_is_relation
        else (normalized_pk_name, f"resolve_{normalized_pk_name}")
    )
    if any(
        _class_has_custom_id_resolver(cls, name)
        for cls in truth.mro(origin)
        for name in resolver_names
    ):
        return True
    return _resolves_id_off_pk(origin, normalized_pk_name)


def _normalize_pk_name(pk_name: object) -> str | None:
    """Return a plain primary-key or id attribute name, or ``None`` for malformed input."""
    if not truth.is_instance(pk_name, str):
        return None
    return truth.text(pk_name) or None


def _resolves_id_off_pk(origin: type[object], pk_name: str) -> bool:
    """Return whether a Relay ``NodeID`` maps the id to a non-``pk_name`` column.

    A consumer ``relay.NodeID[...]`` annotation on a non-pk field (e.g.
    ``slug: relay.NodeID[str]``) makes the GlobalID derive from a column the
    FK-id elision stub does not populate, so eliding would silently encode the
    field default instead of the real id. Non-Relay targets (no
    ``resolve_id_attr``) resolve ``id`` straight from the pk and are always
    safe; a Relay target with no ``NodeID`` annotation resolves to ``"pk"`` and
    is likewise safe.
    """
    if not truth.is_subclass(origin, relay.Node):
        return False
    try:
        # A consumer ``Node`` may override ``resolve_id_attr`` to return anything, so the
        # result is normalized under the same guard that contains the call.
        normalized_id_attr = _normalize_pk_name(origin.resolve_id_attr())
    except NodeIDAnnotationError:
        # No ``NodeID`` annotation: the framework default resolves to "pk".
        return False
    # A non-string or empty override result cannot name the pk column.
    return normalized_id_attr is None or normalized_id_attr not in ("pk", pk_name)


def _class_has_custom_id_resolver(type_cls: type[object], name: str) -> bool:
    """Return whether ``type_cls``'s own namespace defines a consumer id resolver marker."""
    class_dict = truth.class_dict(type_cls)
    if name not in class_dict:
        return False
    if name != "resolve_id":
        return True
    return not _is_framework_relay_id_resolver(class_dict[name])


def _is_framework_relay_id_resolver(value: object) -> bool:
    """Return whether ``value`` holds Strawberry's own ``Node.resolve_id`` (installed or re-exported)."""
    return truth.stored_function(value) is _STRAWBERRY_RESOLVE_ID
