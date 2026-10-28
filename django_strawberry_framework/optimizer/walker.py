"""Selection walker that emits the ``OptimizationPlan``, delegating nested Relay connections."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from django.db import models
from django.db.models import Prefetch
from graphql import OperationType
from strawberry import relay
from strawberry.schema.config import StrawberryConfig
from strawberry.schema.schema_converter import GraphQLCoreConverter
from strawberry.types.base import get_object_definition
from strawberry.types.field import StrawberryField

from django_strawberry_framework.exceptions import ConfigurationError, OptimizerError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.relay import implements_relay_node
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import (
    get_item,
    is_list,
    list_of,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils._queryset_private import (
    queryset_db,
    queryset_hints,
    queryset_prefetch_lookups,
)
from django_strawberry_framework.utils.connections import relay_max_results_from_info
from django_strawberry_framework.utils.querysets import (
    _COMBINED_WHAT,
    _LIST_RELATION_CHILD_POLICY,
    _PREFETCH_CHILD_POLICY,
    _pk_membership_query_or_defect,
    _SealPolicy,
    apply_type_visibility_sync,
    base_queryset,
)
from django_strawberry_framework.utils.relations import (
    instance_accessor,
    is_many_side_relation_kind,
    is_model_class,
    relation_kind,
)
from django_strawberry_framework.utils.typing import graphql_fields, schema_config_from_info

from . import logger
from . import nested_planner as _nested_planner
from .field_meta import FieldMeta
from .hints import OptimizerHint, _PrefetchAny, hint_is_skip
from .join_taxonomy import classify_relation_join
from .nested_planner import (
    plan_connection_relation as _plan_nested_connection_relation,
)
from .plans import (
    JoinPrefix,
    OptimizationPlan,
    PrefetchSeal,
    _consumer_projection,
    append_prefetch_unique,
    append_unique,
    append_unique_many,
    diff_plan_for_queryset,
    resolver_key,
    runtime_path_from_info,
)
from .selections import (
    PYTHON_ARGUMENTS_ATTR,
    PYTHON_NAME_ATTR,
    RUNTIME_PREFIXES_ATTR,
    included_field_selections,
    is_fragment,
    python_arguments,
    response_key,
    response_keys,
    selection_python_name,
    should_include,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from django.db.models import QuerySet
    from graphql.type.definition import GraphQLResolveInfo
    from strawberry.types import Info

    from django_strawberry_framework.types.base import DjangoType
    from django_strawberry_framework.types.definition import DjangoTypeDefinition
    from django_strawberry_framework.types.relay import _RelayDjangoType

    from .selections import ConvertedSelection, FieldSelection


# The selection-traversal primitives live in ``optimizer/selections.py`` so the
# walker and the AST seam in ``extension.py`` share ONE
# fragment/directive/response-key implementation. Readers of the underscore
# aliases below: ``_is_fragment``, ``_response_key``, ``_response_keys`` and
# ``_included_field_selections`` are consumed by this module's own bodies;
# ``_should_include`` and ``_is_fragment`` are imported from
# ``optimizer.walker`` by ``tests/optimizer/test_walker.py``.
_should_include = should_include
_is_fragment = is_fragment
_response_key = response_key
_response_keys = response_keys
_included_field_selections = included_field_selections
# Two underscore aliases with live test readers (both imported from
# ``optimizer.walker`` by ``tests/optimizer/test_walker.py``):
# ``_concrete_order_columns`` is implemented in ``optimizer/nested_planner.py``;
# ``_relay_max_results_from_info`` binds ``utils/connections.py``'s
# ``relay_max_results_from_info``.
_concrete_order_columns = _nested_planner._concrete_order_columns
_relay_max_results_from_info = relay_max_results_from_info


def _record_path_resolver_keys(
    path_map: dict[str, tuple[str, ...]],
    lookup_path: str,
    keys: tuple[str, ...],
) -> None:
    """Append unique resolver keys onto one path ledger entry."""
    if not keys:
        return
    recorded = path_map.get(lookup_path, ())
    path_map[lookup_path] = recorded + tuple(key for key in keys if key not in recorded)


def _record_prefetch_path_keys(
    plan: OptimizationPlan,
    lookup_path: str,
    keys: tuple[str, ...],
) -> None:
    """Attribute resolver / FK-id keys to a ``prefetch_related`` lookup path."""
    _record_path_resolver_keys(plan.prefetch_path_resolver_keys, lookup_path, keys)


def _introduces_projection_for_operation(info: GraphQLResolveInfo | None) -> bool:
    """Return whether the plan may introduce a column projection for ``info``'s operation.

    Only a ``QUERY`` operation turns a queryset that carried no ``.only()`` /
    ``.defer()`` into a projected one. ``MUTATION`` and ``SUBSCRIPTION`` plans
    record the same columns but only widen a projection the queryset already
    carries (``OptimizationPlan.apply``), so a mutation-returned queryset never
    gains a deferred-field set of the optimizer's making.

    Defensive by design (the package's ``getattr`` posture, mirroring
    ``runtime_path_from_info`` and ``_relay_max_results_from_info``): a
    ``None`` ``info`` *or* a partial test-double whose ``operation`` (or
    ``operation.operation``) is absent falls to the introducing default rather
    than raising. During real execution ``info.operation`` is always present
    (``extension.py::_build_cache_key`` reads it directly), so the defensive
    arm exists only for direct / test callers of ``plan_optimizations``.
    """
    operation = getattr(getattr(info, "operation", None), "operation", None)
    return operation is None or operation is OperationType.QUERY


def plan_optimizations(
    selected_fields: Iterable[ConvertedSelection],
    model: type[models.Model],
    info: GraphQLResolveInfo | None = None,
    *,
    runtime_prefixes: tuple[tuple[str, ...], ...] | None = None,
    source_type: type[DjangoType] | None = None,
) -> OptimizationPlan:
    """Walk the selection tree and produce an ``OptimizationPlan``.

    ``source_type`` is the resolver's actual Strawberry return type
    (``origin``). Threaded into the root ``_walk_selections`` call so the
    root ``_resolve_field_map(...)`` uses that type's ``field_map`` /
    ``optimizer_hints`` instead of ``registry.get(model)`` (which
    returns the primary). Nested relation traversal stays unchanged -
    nested ``_walk_selections`` calls leave ``source_type`` ``None`` so
    nested targets continue to route through the primary.
    """
    # The operation decides once, here, whether the plan may introduce a
    # projection; the plan carries it (cached with the plan under a key that
    # already names the operation), and every ``Prefetch`` child plan and
    # scalar-only connection window reads it from its parent plan.
    plan = OptimizationPlan(introduce_projection=_introduces_projection_for_operation(info))
    _walk_selections(
        selected_fields,
        model,
        plan,
        info=info,
        runtime_prefixes=(
            runtime_prefixes if runtime_prefixes is not None else (runtime_path_from_info(info),)
        ),
        source_type=source_type,
    )
    # Finalise at handoff: list fields become tuples so post-walker
    # mutation (by callers, the plan cache, or downstream resolvers)
    # raises ``AttributeError`` instead of silently corrupting the
    # cached plan for subsequent requests.
    return plan.finalize()


def plan_relation(
    field: FieldMeta,
    target_type: type[DjangoType] | None,
    *,
    target_definition: DjangoTypeDefinition | None = None,
) -> tuple[str, str]:
    """Return relation traversal kind without constructing querysets.

    ``target_definition`` is the walker's captured child definition
    (``_resolve_relation_target``'s second answer). The walk always supplies
    it; a direct caller may omit it and the predicate falls back to the
    target's own report.
    """
    if _target_has_custom_get_queryset(target_type, target_definition):
        logger.debug(
            "Optimizer: will downgrade %s to Prefetch because %s overrides get_queryset.",
            field.name,
            truth.name(target_type),
        )
        return ("prefetch", "custom_get_queryset")
    if is_many_side_relation_kind(relation_kind(field)):
        return ("prefetch", "default")
    return ("select", "default")


def _target_has_custom_get_queryset(
    target_type: type[DjangoType] | None,
    target_definition: DjangoTypeDefinition | None = None,
) -> bool:
    """Report whether a relation target overrides ``get_queryset``.

    Answers from the CAPTURED definition when the walk resolved one, so the
    verdict that decides ``select_related`` versus ``Prefetch`` - and, through
    ``_build_child_queryset``, whether the child's visibility hook runs at all -
    comes from the same object the relation was resolved through, not from a
    second request-time read of the target class.

    The class fallback is reached only for a registration the registry holds
    WITHOUT a definition. ``DjangoType.__init_subclass__`` registers the type
    and its definition in one atomic call, so no real ``DjangoType`` can
    present that shape; a bare class registered directly through
    ``registry.register`` carries no definition to read, and its own report is
    the only answer there is.
    """
    if target_definition is not None:
        return target_definition.has_custom_get_queryset
    return target_type is not None and target_type.has_custom_get_queryset()


# The GlobalID field ``relay.Node`` declares, its only field. Every Relay type's definition
# holds this same field object, so a selection of it carries the Python name the field
# was declared under whatever wire name the schema's converter publishes; a Strawberry
# that gives ``Node`` a second field fails here.
(_RELAY_ID_FIELD,) = get_object_definition(relay.Node, strict=True).fields
_RELAY_ID_PYTHON_NAME: str = _RELAY_ID_FIELD.python_name
# The name ``relay.Node`` declares the field under (``id``), fixed by the declaration and
# never a converter's answer: an id no column holds resolves through the field map under it.
_RELAY_ID_DECLARED_NAME: str = require_instance(_RELAY_ID_FIELD.graphql_name, str)


def _resolve_selection_target(
    python_name: str | None,
    field_map: Mapping[str, FieldMeta],
    relation_connections: Mapping[str, str],
) -> tuple[str, str, FieldMeta | None] | None:
    """Resolve a selection across model-field and synthesized-connection namespaces.

    Matches by the Python name the executing schema published the selected field
    from (``selections.py::selection_python_name``): a synthesized connection's
    generated attribute name (a key of ``relation_connections``) outranks a model
    field of the same name (a key of ``field_map``). ``None`` for a selection the
    schema publishes from neither namespace.
    """
    if python_name is None:
        return None
    relation_field_name = relation_connections.get(python_name)
    if relation_field_name is not None:
        return "connection", relation_field_name, None
    field = field_map.get(python_name)
    if field is not None:
        return "field", python_name, field
    return None


def _resolve_field_map(
    model: type[models.Model],
    *,
    source_type: type[DjangoType] | None = None,
) -> tuple[type[DjangoType] | None, DjangoTypeDefinition | None, dict[str, FieldMeta]]:
    """Return ``(registered DjangoType, definition, field_map)`` for ``model``.

    Prefers the canonical ``DjangoTypeDefinition.field_map`` registered
    for the ``DjangoType`` subclass; falls back to a fresh
    ``model._meta.get_fields()`` walk stamped through
    ``FieldMeta.from_django_field`` when the model has no registered
    definition. Centralizes the brittle Django-private ``_meta`` access
    used by the walker. Both paths key the map by the raw Django
    ``f.name``, the Python name a ``DjangoType`` publishes the field from, so
    ``_resolve_selection_target`` matches a selection's published Python name
    against it.

    ``source_type`` carries the root resolver's actual return type when
    the call comes from ``plan_optimizations`` - that type's field_map /
    optimizer_hints are used so a secondary-return resolver plans
    against the secondary's metadata rather than the primary's.
    Nested ``_walk_selections`` calls leave ``source_type`` ``None``,
    which routes through ``registry.get(model)`` and resolves nested
    relation targets to the primary (the spec-018 nested contract).

    Map values are ``FieldMeta`` on both paths.
    ``types/resolvers.py::_field_meta_for_resolver`` shares the same
    policy and the same shape -- prefer the canonical definition-backed
    metadata, fall back when it is unreachable -- so callers on either
    site read every attribute directly. Keep the policy in sync.
    """
    type_cls = source_type if source_type is not None else registry.get(model)
    definition = registry.get_definition(type_cls) if type_cls is not None else None
    if definition is not None:
        field_map = definition.field_map
    else:
        field_map = {f.name: FieldMeta.from_django_field(f) for f in model._meta.get_fields()}
    return type_cls, definition, field_map


def _resolve_relation_target(
    definition: DjangoTypeDefinition | None,
    django_name: str,
    django_field: FieldMeta,
) -> tuple[type[DjangoType] | None, DjangoTypeDefinition | None]:
    """Return one relation target as ``(origin, definition)``.

    The owner definition's ``related_target_for`` already resolved the child
    ``DjangoTypeDefinition``; both halves of that one answer are returned
    together so every later decision about the target - the ``get_queryset``
    downgrade, the child visibility model, the declared cursor vocabulary -
    spends this resolution instead of asking the target class again at request
    time. Collapsing the pair to its ``origin`` here is what forced those
    re-reads, and a target whose metadata changes between them is exactly the
    threat the one-definition rule exists for.

    The unresolved-relation fallback stays registry-only and answers in the
    same shape: the registry's type for the related model plus the registry's
    definition for that type (``registry.get_definition``, the same canonical
    lookup ``_has_custom_id_resolver`` uses). A model with no registered type
    yields ``(None, None)``; a type the registry holds without a definition
    yields its origin and ``None``, and each consumer degrades on its own
    documented contract rather than reaching for a class attribute.
    """
    if definition is not None:
        resolved = definition.related_target_for(django_name)
        if resolved is not None:
            target_definition, _model_field = resolved
            return target_definition.origin, target_definition
    related_model = django_field.related_model
    if related_model is None:
        return None, None
    origin = registry.get(related_model)
    if origin is None:
        return None, None
    return origin, registry.get_definition(origin)


def _resolve_optimizer_hints(definition: DjangoTypeDefinition | None) -> dict[str, OptimizerHint]:
    """Return optimizer hints from the resolved ``DjangoTypeDefinition``."""
    if definition is None:
        return {}
    return definition.optimizer_hints or {}


def _hook_info(info: GraphQLResolveInfo | None, target_type: type[DjangoType]) -> Info:
    """Return the Strawberry ``Info`` the resolver that owns ``info`` was handed.

    The plan walk reads graphql-core's ``GraphQLResolveInfo`` (the schema
    middleware hands the extension nothing else, and the connection and mutation
    entries unwrap to it), but a consumer ``get_queryset`` is called with
    ``strawberry.Info`` on every resolver surface. This rebuilds the object
    Strawberry built for the resolver whose plan is being walked, the way
    Strawberry's own resolver wrapper does: the schema's ``info_class`` over the
    raw info and the ``StrawberryField`` the executable schema filed under its
    definition backref for that field. The hook therefore reads one coherent
    field (``field_name``, ``python_name``, ``return_type``,
    ``selected_fields``) and the same ``context`` / ``schema`` it reads on the
    root path.

    A walk with no resolve info is a direct caller planning outside any
    operation; the hook has no ``Info`` to receive there, so a relation whose
    target declares one fails loudly instead of handing it ``None``.
    """
    if info is None:
        raise OptimizerError(
            f"{truth.name(target_type)}.get_queryset runs under an executing operation; a "
            f"relation to it cannot be planned without that operation's resolve info.",
        )
    strawberry_field = require_instance(
        get_item(
            graphql_fields(info.parent_type)[info.field_name].extensions,
            GraphQLCoreConverter.DEFINITION_BACKREF,
        ),
        StrawberryField,
    )
    config = require_instance(schema_config_from_info(info), StrawberryConfig)
    return config.info_class(_raw_info=info, _field=strawberry_field)


_WALKER_ASYNC_RECOURSE = (
    "The optimizer walker plans prefetch children synchronously on both the sync "
    "and async surfaces, so it cannot await an async get_queryset hook; redefine "
    "the target type's get_queryset as a sync method."
)


def _build_child_queryset(
    field: FieldMeta,
    target_type: type[DjangoType] | None,
    info: GraphQLResolveInfo | None,
    *,
    has_custom_qs: bool,
    target_definition: DjangoTypeDefinition | None = None,
    policy: _SealPolicy[models.Model] = _LIST_RELATION_CHILD_POLICY,
    seed: QuerySet[models.Model] | None = None,
) -> QuerySet[models.Model]:
    """Build the queryset used inside a generated or hinted ``Prefetch`` object.

    ``policy`` is the seal the child's ``get_queryset`` return is held to. It
    defaults to ``_LIST_RELATION_CHILD_POLICY``, the plain-list-relation seal;
    the nested-connection planner takes ``_PREFETCH_CHILD_POLICY`` through
    ``_build_connection_child_queryset``. The two differ on ``reject_sliced``
    and on nothing else, because one thing differs between the paths: only the
    connection path has a gate that classifies a sliced child.

    ``has_custom_qs`` is the caller's verdict from the captured child
    definition (``_target_has_custom_get_queryset``), so the question is
    answered once per relation rather than once per consumer of the answer.

    ``target_definition`` is that same definition, spent here for its model:
    both seals of this visibility call validate against the model the
    relation was resolved through. The read lives here - the builder is its
    only consumer - rather than once per caller, so the two child paths
    cannot name two validation subjects. Without a definition the runner
    reads the target class for a model of its own, which is a second
    request-time definition read on the one path that decides which rows a
    prefetch may see.

    The custom ``get_queryset`` visibility hook receives the Strawberry ``Info``
    of the resolver whose plan is walked (``_hook_info``), never the walk's raw
    graphql-core info, and runs through the shared
    ``utils/querysets.py::apply_type_visibility_sync`` so
    plan-time prefetch visibility uses the SAME sync routing the resolver
    surfaces do: an async-only related ``get_queryset`` surfaces a clean
    ``SyncMisuseError`` here (the optimizer walker is sync; a coroutine would
    otherwise leak into ``OptimizationPlan.apply``) - consistent with the
    connection field's documented "nested async ``get_queryset`` ->
    ``relation_shapes = list``" recourse. The base queryset is the related
    model's own ``_default_manager.all()`` (NOT ``initial_queryset(target_type)``
    - the prefetch child is keyed on ``field.related_model``) and carries no
    explicit ``.using(...)``. A plan walk is a read with no write pipeline in
    force, so nothing pins an alias ahead of that seed either: the child's
    effective alias entering the hook is ``None`` on this path, and the hook
    cannot pin one of its own.

    ``seed`` replaces that base with the queryset of a consumer
    ``OptimizerHint.prefetch(Prefetch(...))``: the hint chooses how the relation
    is fetched, never which rows the target type admits, so the hook narrows the
    consumer's queryset exactly as it narrows the generated base. The seal adopts
    the seed's explicit ``.using(...)`` as the alias the hook must keep, and a
    hinted plan is never cached, so a routed seed answers to that one request.
    """
    queryset = (
        seed if seed is not None else base_queryset(require(field.related_model, is_model_class))
    )
    if has_custom_qs:
        # The slice axis is the one axis the two child policies differ on, and it
        # differs because the paths do.
        #
        # ``_PREFETCH_CHILD_POLICY`` (``reject_sliced=False``, the nested-connection
        # child): a nested-connection child may legitimately return a sliced
        # queryset, and the plan's own gate
        # (``nested_fetch.py::unwindowable_child_queryset_reason``) detects that shape
        # and degrades to the fully-unplanned per-parent fallback WITHOUT recomposing
        # filters / ordering, so the seal's slice rejection (which exists because
        # recomposing surfaces would raise a raw ``TypeError``) must not pre-empt the
        # designed degradation (``spec-045-visibility_boundary-0_0_14`` Decision 5
        # degrade-to-unplanned).
        #
        # ``_LIST_RELATION_CHILD_POLICY`` (``reject_sliced`` kept, the plain list
        # relation): nothing downstream classifies this child. It is installed as
        # ``Prefetch(<lookup>, queryset=...)`` with no ``to_attr``, and Django then
        # re-applies the relation's own filters to it at fetch time
        # (``prefetch_one_level`` -> ``RelatedManager._apply_rel_filters``), raising a
        # raw ``TypeError`` on a sliced query. The hook therefore gets the seal's
        # typed ``sliced`` defect instead, naming itself the way every other
        # bad-hook shape is named here.
        #
        # ``require_shared_alias=True`` (both): the value built here is installed as the
        # ``Prefetch`` queryset of a parent this walk never holds, and the plan
        # carrying it is reused across requests, so the child must leave this call
        # UNROUTED. Its effective alias is the unpinned seed's ``None``, and a hook
        # returning an explicitly routed queryset therefore fails closed instead of
        # scheduling the parent and its related rows on two connections; an unrouted
        # child inherits the parent's connection at fetch time, so a routed parent
        # still carries its children. A consumer-supplied ``Prefetch`` child meets the
        # same rule in ``utils/querysets.py::_sealed_prefetch_related_lookups``, which
        # the generated one never passes through: the plan applies it after the
        # parent's own seal has run.
        # ``has_custom_qs`` is True only for a resolved target type.
        hook_type = cast("type[DjangoType]", target_type)
        queryset = apply_type_visibility_sync(
            hook_type,
            queryset,
            _hook_info(info, hook_type),
            async_recourse=_WALKER_ASYNC_RECOURSE,
            model=target_definition.model if target_definition is not None else None,
            policy=policy,
        )
    return queryset


def _build_connection_child_queryset(
    field: FieldMeta,
    target_type: type[DjangoType] | None,
    info: GraphQLResolveInfo | None,
    *,
    has_custom_qs: bool,
    target_definition: DjangoTypeDefinition | None = None,
) -> QuerySet[models.Model]:
    """Build a nested-connection child queryset under ``_PREFETCH_CHILD_POLICY``.

    The nested-connection planner reaches the shared child builder through this
    seam, so the slice licence is spent at the one call site whose premise holds:
    the planner classifies the value it gets back with
    ``nested_fetch.py::unwindowable_child_queryset_reason`` and degrades a sliced
    child to the per-parent fallback. The plain list relation, which has no such
    gate, takes the builder's default seal. The seal choice stays on this seam -
    the planner takes the fixed-policy callable and holds no seal-policy
    vocabulary of its own; a future child path whose seal needs planner-local
    state moves the choice into the planner with a ``policy`` argument.
    """
    return _build_child_queryset(
        field,
        target_type,
        info,
        has_custom_qs=has_custom_qs,
        target_definition=target_definition,
        policy=_PREFETCH_CHILD_POLICY,
    )


def _resolver_identities_for(
    sel: FieldSelection,
    field_name: str,
    type_cls: type[DjangoType] | None,
    runtime_prefixes: tuple[tuple[str, ...], ...],
) -> tuple[tuple[tuple[str, ...], ...], tuple[str, ...]]:
    """Return ``(runtime_paths, resolver_identities)`` for one selection.

    Shared by the list-relation walk (``_walk_selections``, keyed on the
    Django field name) and the nested-connection planner
    (``_plan_connection_relation``, keyed on ``relation_field_name`` - the
    underlying relation field, NOT the generated ``<field>_connection``
    accessor). ``field_name`` is the resolver-key vocabulary, so passing
    ``relation_field_name`` at the connection site keeps the walker's emitted
    key MATCHING the resolve-time key ``connection.py``'s
    ``_check_n1(kind="connection_to_attr")`` rebuilds via
    ``resolver_key(type_cls, relation_field_name, runtime_path)`` - the
    load-bearing "planned -> silent" parity (``connection.py`` resolver doc).

    A selection-specific ``RUNTIME_PREFIXES_ATTR`` (set by connection
    extraction) overrides the inherited ``runtime_prefixes``; the runtime path
    is the cartesian product over those prefixes and ``_response_keys(sel)``.
    """
    # Only the walker's ``SimpleNamespace`` clones carry runtime prefixes.
    carried_prefixes = _selection_runtime_prefixes(sel)
    selection_runtime_prefixes: tuple[tuple[str, ...], ...] = (
        tuple(carried_prefixes) if carried_prefixes is not None else runtime_prefixes
    )
    runtime_paths = tuple(
        (*runtime_prefix, response_key)
        for runtime_prefix in selection_runtime_prefixes
        for response_key in _response_keys(sel)
    )
    resolver_identities = tuple(
        resolver_key(type_cls, field_name, runtime_path) for runtime_path in runtime_paths
    )
    return runtime_paths, resolver_identities


def _relay_id_column(node_type: type[_RelayDjangoType]) -> str | None:
    """Return the column a Relay type's GlobalID is read from, for ``only()``.

    ``types/relay.py::_resolve_id_default`` reads ``resolve_id_attr()`` off the
    row's instance namespace and loads it lazily on a miss, so a row that did
    not load that column pays one query per row for its id (spec-015
    Decision 7). ``relay.py::_node_id_slot`` names the model field behind the
    id; a concrete one is projected by ``attname`` (a forward key named by its
    ``attname``, or a primary key that is a one-to-one key, projects its key
    column). ``None`` when the id is not read from a column: a consumer
    ``resolve_id`` anywhere in the type's MRO, or an id attribute no concrete
    model field holds (a property, an attribute ``get_queryset`` annotates).
    """
    # Lazy imports: ``relay`` imports ``list_field``, whose ``types`` import
    # loads this walker; ``types.definition`` pulls in ``optimizer.field_meta``.
    from django_strawberry_framework.relay import _node_id_slot  # noqa: PLC0415 - import cycle
    from django_strawberry_framework.types.definition import (  # noqa: PLC0415 - import cycle
        _class_has_custom_id_resolver,
    )

    if any(_class_has_custom_id_resolver(cls, "resolve_id") for cls in truth.mro(node_type)):
        return None
    _id_attr, field = _node_id_slot(node_type)
    if truth.is_instance(field, models.Field) and field.concrete:
        return field.attname
    return None


def _walk_selections(
    selections: Iterable[ConvertedSelection],
    model: type[models.Model],
    plan: OptimizationPlan,
    prefix: str = "",
    info: GraphQLResolveInfo | None = None,
    runtime_prefixes: tuple[tuple[str, ...], ...] = ((),),
    *,
    lookup_prefix: str = "",
    source_type: type[DjangoType] | None = None,
) -> None:
    """Recursive workhorse: descend one normalized level of the selection tree.

    ``prefix`` and ``lookup_prefix`` both name the ``select_related`` JOIN path
    this level hangs beneath, each in the vocabulary of the ledgers it builds
    (``utils/relations.py::RelationSpelling``). ``prefix`` is the query-name
    spelling Django's ``select_related`` and ``only()`` read: the plan's
    ``select_related``, ``only_fields`` and ``select_path_resolver_keys``.
    ``lookup_prefix`` is the accessor spelling ``prefetch_related`` resolves on
    the instance: every prefetch lookup planned beneath the JOIN, with its
    ``prefetch_path_resolver_keys`` and ``prefetch_path_seals`` entries and a
    hinted ``Prefetch``'s rebase. A reverse relation whose ``related_query_name``
    differs from its accessor spells one JOIN hop two ways.

    ``source_type`` is set only on the root invocation from
    ``plan_optimizations`` so the resolver's actual Strawberry return
    type drives the root ``_resolve_field_map`` lookup. Recursive
    nested calls (``_plan_select_relation`` and
    ``_build_prefetch_child_queryset`` below) intentionally omit it so
    nested relation targets keep routing through ``registry.get(model)``
    and resolve to the primary type.

    The default ``runtime_prefixes=((),)`` encodes "one empty-path
    prefix" for direct or test-only callers without ``info``;
    ``plan_optimizations`` always passes an explicit single-tuple via
    ``runtime_path_from_info(info)``.

    Every writer records its columns whatever the operation; whether the plan
    may introduce a projection is ``plan.introduce_projection``, read where the
    plan is applied.
    """
    type_cls, definition, field_map = _resolve_field_map(model, source_type=source_type)
    hints_map = _resolve_optimizer_hints(definition)
    # TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card): supply
    # a registry-only type-condition classifier to ``included_field_selections`` at this planning
    # seam. Design contract: spec-035 Decision 6 (the tri-state classifier and its accept set) and
    # Decision 7 (narrow, do not multi-plan). That card must first build the abstract-return
    # production-entry contract (R1); until it exists no abstract root field reaches this walker,
    # so the classifier has nothing to narrow.
    # Pseudocode: accept the planning type's GraphQL name plus declared and
    # MRO-inherited interface names; skip known sibling concrete types; recurse
    # fragments-only for unknown composite/union names; never accept the model
    # primary type merely because the Django model matches. The classifier must
    # not call into graphql-core schema introspection.
    merged = _merge_aliased_selections(_included_field_selections(selections))
    relation_connections: Mapping[str, str] = (
        getattr(definition, "relation_connections", None) or {}
    )
    # On a ``relay.Node`` type the GlobalID is the field ``relay.Node`` declares, selected
    # under whatever name the executing schema's converter publishes for it and matched
    # by the Python name it was declared under, never a model field named ``id``: when
    # the id is read from a column it projects that column whatever the field map holds
    # (spec-015 Decision 7); an id no column holds resolves through the field map under
    # the name ``relay.Node`` declares the field as, like any selection.
    relay_type = type_cls if type_cls is not None and implements_relay_node(type_cls) else None
    relay_id_column = _relay_id_column(relay_type) if relay_type is not None else None
    for sel in merged:
        python_name = selection_python_name(sel)
        if relay_type is not None and python_name == _RELAY_ID_PYTHON_NAME:
            if relay_id_column is not None:
                append_unique(plan.only_fields, f"{prefix}{relay_id_column}")
                continue
            python_name = _RELAY_ID_DECLARED_NAME
        # Resolve the selection through the ONE consolidated resolver, by the
        # Python name the schema published its field from. It recognizes a
        # synthesized nested connection BEFORE the field namespace and BEFORE
        # the unknown-name guard below: ``books_connection`` /
        # ``line_2_connection`` name no model field, so without this branch the
        # unknown-name guard silently ``continue``s and the nested connection
        # is never planned (the gap spec-033 closes). The ``relation_connections`` slot (Phase-2.5
        # synthesis metadata) maps the generated attr name to the underlying
        # relation field name; recognition is metadata-driven, never
        # name-pattern guessing (Decision 3). The ``definition`` resolved above
        # is the model's PRIMARY type, so a divergent secondary type's
        # connection is out of scope for windowed planning and falls through to
        # per-parent (Decision 3 primary contract).
        resolved = _resolve_selection_target(python_name, field_map, relation_connections)
        if resolved is not None and resolved[0] == "connection":
            _plan_connection_relation(
                sel,
                definition,
                relation_field_name=resolved[1],
                field_map=field_map,
                plan=plan,
                prefix=prefix,
                lookup_prefix=lookup_prefix,
                info=info,
                runtime_prefixes=runtime_prefixes,
                type_cls=type_cls,
                model=model,
            )
            continue
        if resolved is None or resolved[2] is None:
            # Neither namespace matched: an unknown name plans nothing.
            continue
        django_name, django_field = resolved[1], resolved[2]
        if not django_field.is_relation:
            append_unique(
                plan.only_fields,
                f"{prefix}{django_name}",
            )
            continue

        # Consumer-assigned relation fields are FULLY unplanned without an
        # explicit hint (the strawberry-django #697 bug class). The consumer
        # replaced the generated relation resolver
        # (``finalizer.py::finalize_django_types`` skips attaching one via this
        # same frozenset), so the walker cannot know what their resolver
        # fetches: a speculative model-shaped ``Prefetch`` may pay a query
        # nobody consumes, and - worse - recording ``planned_resolver_keys``
        # for the walked subtree would short-circuit
        # ``types/resolvers.py::_check_n1`` for every generated resolver under
        # the consumer's OWN returned instances, silencing a real N+1 under
        # strictness. Leaving the selection unplanned (no
        # ``Prefetch``, no resolver keys) is the
        # spec-033 Decision 6 fallback discipline: strictness SEES the per-parent
        # accesses, and a delegating resolver opts back in with an explicit
        # ``OptimizerHint`` (``force_select`` / ``force_prefetch`` /
        # ``prefetch(...)``) - the hint dispatch below runs when one is
        # declared. Consumer-assigned SCALAR shadows are unaffected (the
        # scalar branch above projects columns, which is harmless). The
        # relation's link columns on the parent row are the one thing recorded:
        # the consumer's resolver reaches the relation from that row, and a
        # deferred carrier would refetch per parent before it does.
        consumer_assigned = (
            definition is not None and django_name in definition.consumer_assigned_relation_fields
        )
        if consumer_assigned and hints_map.get(django_name) is None:
            _record_relation_carriers(plan, django_field, prefix)
            continue

        full_path = f"{prefix}{django_name}"
        runtime_paths, resolver_identities = _resolver_identities_for(
            sel,
            django_name,
            type_cls,
            runtime_prefixes,
        )
        target_type, target_definition = _resolve_relation_target(
            definition,
            django_name,
            django_field,
        )

        hint = hints_map.get(django_name)
        if hint is not None and _apply_hint(
            hint,
            sel=sel,
            django_field=django_field,
            django_name=django_name,
            # Hints come only from a registered definition, so ``type_cls`` is set.
            type_cls=cast("type[DjangoType]", type_cls),
            target_type=target_type,
            target_definition=target_definition,
            plan=plan,
            prefix=prefix,
            lookup_prefix=lookup_prefix,
            full_path=full_path,
            info=info,
            runtime_paths=runtime_paths,
            resolver_identities=resolver_identities,
            consumer_assigned=consumer_assigned,
        ):
            continue

        relation_plan_kind, _ = plan_relation(
            django_field,
            target_type,
            target_definition=target_definition,
        )
        _dispatch_single_relation(
            prefer_prefetch=relation_plan_kind == "prefetch",
            sel=sel,
            django_field=django_field,
            target_type=target_type,
            target_definition=target_definition,
            plan=plan,
            prefix=prefix,
            lookup_prefix=lookup_prefix,
            full_path=full_path,
            info=info,
            runtime_paths=runtime_paths,
            resolver_identities=resolver_identities,
        )


def _dispatch_single_relation(
    *,
    prefer_prefetch: bool,
    sel: FieldSelection,
    django_field: FieldMeta,
    target_type: type[DjangoType] | None,
    target_definition: DjangoTypeDefinition | None,
    plan: OptimizationPlan,
    prefix: str,
    lookup_prefix: str,
    full_path: str,
    info: GraphQLResolveInfo | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
) -> None:
    """Route one relation selection to the prefetch or the select planner.

    The single owner of the ``_plan_prefetch_relation`` /
    ``_plan_select_relation`` argument threading its three deciders share:
    the cardinality dispatch in ``_walk_selections`` (``plan_relation``'s
    verdict), and the two hint branches in ``_apply_hint`` (``force_select``'s
    custom-``get_queryset`` downgrade and ``force_prefetch``). Only the
    DECISION (``prefer_prefetch``) differs per site; ``full_path`` is a
    select-only concern (``select_related`` resolves query paths), and
    ``lookup_prefix`` the accessor spelling of ``prefix`` (``_walk_selections``).
    """
    if prefer_prefetch:
        _plan_prefetch_relation(
            sel,
            django_field,
            target_type,
            target_definition,
            plan,
            prefix,
            info,
            runtime_paths,
            resolver_identities,
            lookup_prefix=lookup_prefix,
        )
    else:
        _plan_select_relation(
            sel,
            django_field,
            target_type,
            target_definition,
            plan,
            prefix,
            full_path,
            info,
            runtime_paths,
            resolver_identities,
            lookup_prefix=lookup_prefix,
        )


def _plan_select_relation(
    sel: FieldSelection,
    django_field: FieldMeta,
    target_type: type[DjangoType] | None,
    target_definition: DjangoTypeDefinition | None,
    plan: OptimizationPlan,
    prefix: str,
    full_path: str,
    info: GraphQLResolveInfo | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
    *,
    lookup_prefix: str,
) -> None:
    """Plan a same-query single-valued relation traversal.

    ``full_path`` (field-name vocabulary) is correct here: Django's
    ``select_related`` and ``only()`` resolve QUERY paths. A reverse one-to-one
    is joined under its query name (``FieldMeta.name``) but reached on the
    instance through its accessor (``FieldMeta.accessor_name``), and the two
    differ for a relation declared without ``related_name`` or with a
    ``related_query_name`` of its own; the child level therefore carries the
    JOIN in both spellings, the accessor one for every prefetch lookup planned
    beneath it (``_walk_selections``).
    """
    _record_relation_access(
        plan,
        django_field,
        prefix,
        resolver_identities,
    )
    # Both outcomes below serve the relation without a prefetch, so a consumer
    # ``Prefetch`` that takes this path over withdraws these keys with them.
    _record_path_resolver_keys(plan.select_path_resolver_keys, full_path, resolver_identities)
    target_pk_name = django_field.target_pk_name
    if (
        django_field.fk_id_elision_eligible
        and not _target_has_custom_get_queryset(target_type, target_definition)
        and not _has_custom_id_resolver(target_type, target_pk_name)
        and _selected_scalar_names(sel.selections, django_field.related_model) == {target_pk_name}
    ):
        append_unique_many(plan.fk_id_elisions, resolver_identities)
        return
    append_unique(plan.select_related, full_path)
    if django_field.related_model is not None:
        child_prefix = f"{full_path}__"
        _walk_selections(
            sel.selections,
            django_field.related_model,
            plan,
            prefix=child_prefix,
            info=info,
            runtime_prefixes=runtime_paths,
            lookup_prefix=f"{lookup_prefix}{instance_accessor(django_field)}__",
        )
        # A reverse one-to-one JOIN (an MTI parent link included) has no column
        # on this row, so a selection that reads no column of the related row
        # (``__typename`` only, say) leaves nothing projected under the path:
        # Django's select mask then reads it as deferred and refuses the JOIN
        # (``cannot be both deferred and traversed using select_related``). The
        # target pk is the narrowest column that keeps it valid. A forward join
        # needs no floor: its FK column, recorded above, loads the row whole.
        if django_field.relation_kind != "forward_single" and not any(
            f.startswith(child_prefix) for f in plan.only_fields
        ):
            append_unique(
                plan.only_fields,
                f"{child_prefix}{django_field.related_model._meta.pk.attname}",
            )


def _plan_prefetch_relation(
    sel: FieldSelection,
    django_field: FieldMeta,
    target_type: type[DjangoType] | None,
    target_definition: DjangoTypeDefinition | None,
    plan: OptimizationPlan,
    prefix: str,
    info: GraphQLResolveInfo | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
    *,
    lookup_prefix: str,
) -> None:
    """Plan a queryset-boundary relation traversal with optional child optimization.

    The prefetch LOOKUP is spelled in accessors throughout: ``lookup_prefix``
    (the JOINs above, ``_walk_selections``) plus the relation's instance
    accessor (``django_strawberry_framework/utils/relations.py::instance_accessor``),
    not ``field.name``. Django's ``prefetch_related`` resolves lookups via
    ``getattr`` on the instance, and for a reverse relation without
    ``related_name`` the field name is the related QUERY name (``"book"``)
    while the accessor is ``"book_set"``; a query name in any hop fails with
    ``AttributeError: ... invalid parameter to prefetch_related()``. Resolver
    identities stay in field-name vocabulary; the lookup string Django consumes
    and the ledgers keyed by it use the accessor.
    """
    _record_relation_access(
        plan,
        django_field,
        prefix,
        resolver_identities,
    )
    lookup_path = f"{lookup_prefix}{instance_accessor(django_field)}"
    has_custom_get_queryset = _target_has_custom_get_queryset(target_type, target_definition)
    if has_custom_get_queryset:
        plan.cacheable = False
    if django_field.related_model is None:
        _record_prefetch_path_keys(plan, lookup_path, resolver_identities)
        append_unique(plan.prefetch_related, lookup_path)
        return

    # Snapshot before the child absorb so nested PLANNED keys that land on
    # the parent are attributed to THIS prefetch lookup (B8 consumer-wins
    # must strip them with the dropped Prefetch, so strictness re-sees the
    # now-lazy relation). Nested FK-id elisions are deliberately NOT recorded
    # here: an elision reads a column already on the parent row (``obj.<fk>_id``)
    # and adds no query whether or not this prefetch survives, so it must
    # never be stripped.
    prior_planned = frozenset(plan.planned_resolver_keys)
    child_queryset = _build_prefetch_child_queryset(
        sel,
        django_field,
        target_type,
        target_definition,
        plan,
        info,
        runtime_paths,
        has_custom_get_queryset=has_custom_get_queryset,
    )
    nested_keys = tuple(k for k in plan.planned_resolver_keys if k not in prior_planned)
    _record_prefetch_path_keys(plan, lookup_path, (*resolver_identities, *nested_keys))
    if has_custom_get_queryset:
        _record_prefetch_seal(
            plan,
            lookup_path,
            django_field,
            target_type,
            target_definition,
            resolver_identities,
        )
    append_prefetch_unique(
        plan.prefetch_related,
        Prefetch(lookup_path, queryset=child_queryset),
    )


def _record_prefetch_seal(
    plan: OptimizationPlan,
    lookup_path: str,
    django_field: FieldMeta,
    target_type: type[DjangoType] | None,
    target_definition: DjangoTypeDefinition | None,
    resolver_identities: tuple[str, ...],
) -> None:
    """Record how a consumer queryset on ``lookup_path`` is scoped by the target's hook.

    The seal is ``_build_child_queryset`` seeded with the consumer's queryset, the
    move ``_scoped_hint_prefetch`` makes for a hinted ``Prefetch``: the consumer
    chooses how the relation is fetched, the hook which rows the target type
    admits. It binds only the relation's static field and target metadata; the
    reconciliation hands it the request's resolve info
    (``plans.py::diff_plan_for_queryset``).
    """

    def seal(
        seed: QuerySet[models.Model] | None,
        info: GraphQLResolveInfo | None,
    ) -> QuerySet[models.Model]:
        return _build_child_queryset(
            django_field,
            target_type,
            info,
            has_custom_qs=True,
            target_definition=target_definition,
            seed=seed,
        )

    _ = plan.prefetch_path_seals.setdefault(
        lookup_path,
        PrefetchSeal(
            own_keys=resolver_identities,
            model=django_field.related_model,
            seal=seal,
        ),
    )


def _record_relation_access(
    plan: OptimizationPlan,
    django_field: FieldMeta,
    prefix: str,
    resolver_identities: tuple[str, ...],
) -> None:
    """Record the shared connector and resolver metadata for a relation.

    MUST run before the FK-id elision check in ``_plan_select_relation``:
    the FK ``attname`` appended to ``plan.only_fields`` here is the column
    Django still needs to materialise the relation when the JOIN is elided
    (``_resolve_id_default`` reads ``obj.<fk>_id`` directly instead of
    triggering a lazy load through ``obj.<fk>.pk``). Moving this call
    after the elision check would silently drop the FK column on the
    elided path and reintroduce the N+1.

    The connector columns are ``FieldMeta.source_link_attnames``: a forward
    relation's carrier columns on the source row (its FK column, every
    ``from_fields`` member of a ``ForeignObject``); for every other relation, the
    non-pk source columns its link targets - a reverse FK / reverse one-to-one
    link's ``to_field`` / ``to_fields``, an M2M through table's source FK
    ``to_field`` in either direction, nothing for a ``GenericRelation`` (whose
    link always targets the pk). Django's prefetch attach reads them on every
    source row.
    """
    _record_relation_carriers(plan, django_field, prefix)
    append_unique_many(
        plan.planned_resolver_keys,
        resolver_identities,
    )


def _record_relation_carriers(
    plan: OptimizationPlan,
    django_field: FieldMeta,
    prefix: str,
) -> None:
    """Keep the source-row link columns of a relation the selection touches loaded.

    Every relation a selection reaches is traversed at resolve time, planned or
    not: a planned one by Django's JOIN or prefetch attach, an unplanned one (a
    ``SKIP`` hint, a consumer-assigned resolver) by the per-row access the plan
    leaves to the resolver. Each read ``FieldMeta.source_link_attnames`` on the
    source row, and a projected row that defers them pays a second query per row
    before the relation's own. So the carriers are recorded for every traversal
    while ``planned_resolver_keys`` stay with the planned ones only, keeping an
    unplanned relation strictness-visible.
    """
    append_unique_many(
        plan.only_fields,
        [f"{prefix}{attname}" for attname in django_field.source_link_attnames],
    )


def _build_prefetch_child_queryset(
    sel: FieldSelection,
    django_field: FieldMeta,
    target_type: type[DjangoType] | None,
    target_definition: DjangoTypeDefinition | None,
    parent_plan: OptimizationPlan,
    info: GraphQLResolveInfo | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    *,
    has_custom_get_queryset: bool,
) -> QuerySet[models.Model]:
    """Build and optimize the child queryset for a generated ``Prefetch``."""
    base_queryset = _build_child_queryset(
        django_field,
        target_type,
        info,
        has_custom_qs=has_custom_get_queryset,
        target_definition=target_definition,
    )
    return _build_prefetch_child_queryset_from_base(
        sel,
        django_field,
        parent_plan,
        info,
        runtime_paths,
        base_queryset=base_queryset,
    )


def _build_prefetch_child_queryset_from_base(
    sel: FieldSelection,
    django_field: FieldMeta,
    parent_plan: OptimizationPlan,
    info: GraphQLResolveInfo | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    *,
    base_queryset: QuerySet[models.Model],
) -> QuerySet[models.Model]:
    """Apply the child optimization plan to an already-built base queryset.

    This is the queryset-boundary abstraction: the visibility/default-manager
    base queryset is built once by the caller, then every child-plan writer
    operates on that single value. Nested connections classify that base before
    this helper runs so unsafe manager or hook shapes fall back before
    projection or window planning can touch them.
    """
    child_plan = OptimizationPlan(introduce_projection=parent_plan.introduce_projection)
    _walk_selections(
        sel.selections,
        require(django_field.related_model, is_model_class),
        child_plan,
        prefix="",
        info=info,
        runtime_prefixes=runtime_paths,
    )
    _ensure_connector_only_fields(child_plan, django_field, base_queryset=base_queryset)
    # The base is a consumer queryset too (the target type's hook, its default
    # manager), reconciled exactly as the root reconciles the resolver's: a
    # generated ``Prefetch`` never collides with a lookup the hook added
    # (Django's "lookup was already seen with a different queryset"), a
    # ``Prefetch(queryset=...)`` the hook added keeps the rows of its path over
    # a planned JOIN or elision, or is sealed through its own target type's
    # hook, a consumer-wins drop strips its resolver keys before the parent
    # absorbs them, and ``apply`` writes the union of the hook's projection and
    # the child selection's.
    child_plan, base_queryset = diff_plan_for_queryset(child_plan, base_queryset, info=info)
    _absorb_child_plan(parent_plan, child_plan)
    return child_plan.apply(base_queryset)


def _apply_hint(
    hint: OptimizerHint,
    *,
    sel: FieldSelection,
    django_field: FieldMeta,
    django_name: str,
    type_cls: type[DjangoType],
    target_type: type[DjangoType] | None,
    target_definition: DjangoTypeDefinition | None,
    plan: OptimizationPlan,
    prefix: str,
    lookup_prefix: str,
    full_path: str,
    info: GraphQLResolveInfo | None,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
    consumer_assigned: bool = False,
) -> bool:
    """Apply a Meta-level ``OptimizerHint`` to ``plan``; return ``True`` when handled.

    Dispatches the four configurable hint shapes (``SKIP``,
    ``prefetch_obj``, ``force_select``, ``force_prefetch``) plus the
    no-op empty form. Returns ``True`` when one of the configurable
    shapes is matched. Returns ``False`` for an ``OptimizerHint()`` with
    no flag set - the caller falls back to the default cardinality
    dispatch in that case. ``OptimizerHint.__post_init__`` already
    rejects conflicting flag combinations, so the priority order here
    is documentation, not collision arbitration.

    ``consumer_assigned`` marks a relation whose resolver the consumer
    supplied (``definition.consumer_assigned_relation_fields``) - the one
    shape allowed to hint a ``Prefetch(..., to_attr=...)``, because only the
    consumer's own resolver can honor the attribute contract.
    """
    if hint_is_skip(hint):
        # Unplanned: no Prefetch, no JOIN, no resolver keys. The parent row still
        # carries the link columns the per-row access reads.
        _record_relation_carriers(plan, django_field, prefix)
        return True
    if hint.prefetch_obj is not None:
        hinted_to_attr = getattr(hint.prefetch_obj, "to_attr", None)
        if hinted_to_attr and not consumer_assigned:
            # Django lands ``to_attr`` rows on that attribute instead of its
            # prefetch cache (``_prefetched_objects_cache``) - which is what the
            # GENERATED relation resolver reads. Accepting the hint
            # would record the relation as planned (silencing strictness)
            # while every row still lazy-loads. Only a consumer-assigned
            # resolver can consume the attribute, so anything else fails
            # loud at plan time with the fix spelled out.
            raise ConfigurationError(
                f"OptimizerHint.prefetch(Prefetch(..., to_attr={hinted_to_attr!r})) on "
                f"{truth.name(type_cls)}.{django_name}: the generated relation resolver "
                "reads Django's prefetch cache (_prefetched_objects_cache) and would "
                "ignore rows landed on the to_attr (per-row lazy loads behind a plan strictness "
                "trusts). Drop to_attr from the hinted Prefetch, or assign your own "
                "resolver for the field (consumer-assigned relations may hint with "
                "to_attr because their resolver owns the attribute contract).",
            )
        # ``_apply_hint`` is only entered when ``_resolve_optimizer_hints``
        # returned a non-empty hints map, which it cannot do for
        # ``type_cls is None`` (it short-circuits to ``{}``). The hint
        # error attribution can therefore read ``type_cls.__name__``
        # unguarded; a future direct caller with ``type_cls=None`` will
        # ``AttributeError`` loudly rather than rotting behind a silent
        # ``"UnknownType"`` literal.
        #
        # Validate the consumer-supplied Prefetch BEFORE mutating ``plan``:
        # ``_prefetch_hint_for_path`` may raise ``ConfigurationError`` for
        # a missing lookup path or a lookup that does not target the
        # hinted relation. Recording the resolver identity / non-cacheable
        # flip before validation would leave the plan with phantom
        # connector columns and resolver keys for a relation that was
        # never actually planned, which any future caller catching
        # ``ConfigurationError`` at this layer would consume. Compute the
        # rebased Prefetch first, mutate only on success.
        # The rebase TARGET is the accessor path (what Django's
        # prefetch_related resolves via getattr); the consumer-facing
        # lookup vocabulary in the match below stays ``django_name``.
        rebased_prefetch = _prefetch_hint_for_path(
            _scoped_hint_prefetch(
                hint.prefetch_obj,
                django_field=django_field,
                django_name=django_name,
                type_name=truth.name(type_cls),
                target_type=target_type,
                target_definition=target_definition,
                info=info,
            ),
            django_name=django_name,
            accessor=instance_accessor(django_field),
            full_path=f"{lookup_prefix}{instance_accessor(django_field)}",
            type_name=truth.name(type_cls),
        )
        _record_relation_access(
            plan,
            django_field,
            prefix,
            resolver_identities,
        )
        # Consumer-supplied Prefetch objects commonly close over a queryset
        # built with request- or user-scoped filters; matching the
        # has_custom_get_queryset discipline in _plan_prefetch_relation, mark
        # the plan non-cacheable so the plan cache cannot serve one
        # request's queryset to the next.
        plan.cacheable = False
        # B8 coupling: attribute the relation's resolver keys to the rebased
        # lookup so a later consumer-wins drop strips them from strictness.
        hinted_lookup = rebased_prefetch.prefetch_to or rebased_prefetch.prefetch_through
        _record_prefetch_path_keys(plan, hinted_lookup, resolver_identities)
        # A consumer ``Prefetch`` that wins on this path is sealed through the
        # target's hook only when the generated resolver reads the relation
        # itself: a consumer-assigned resolver owns its rows (and may read a
        # ``to_attr`` or a deeper lookup), so its winner stays as written.
        if (
            _target_has_custom_get_queryset(target_type, target_definition)
            and not consumer_assigned
            and hinted_lookup == f"{lookup_prefix}{instance_accessor(django_field)}"
        ):
            _record_prefetch_seal(
                plan,
                hinted_lookup,
                django_field,
                target_type,
                target_definition,
                resolver_identities,
            )
        append_prefetch_unique(
            plan.prefetch_related,
            rebased_prefetch,
        )
        return True
    if hint.force_select:
        kind = relation_kind(django_field)
        if is_many_side_relation_kind(kind):
            raise ConfigurationError(
                f"OptimizerHint.select_related() on {truth.name(type_cls)}.{django_name}: "
                f"Django requires prefetch_related for {kind} relations; "
                "use OptimizerHint.prefetch_related() or OptimizerHint.prefetch(obj) instead.",
            )
        _dispatch_single_relation(
            prefer_prefetch=_target_has_custom_get_queryset(target_type, target_definition),
            sel=sel,
            django_field=django_field,
            target_type=target_type,
            target_definition=target_definition,
            plan=plan,
            prefix=prefix,
            lookup_prefix=lookup_prefix,
            full_path=full_path,
            info=info,
            runtime_paths=runtime_paths,
            resolver_identities=resolver_identities,
        )
        return True
    if hint.force_prefetch:
        _dispatch_single_relation(
            prefer_prefetch=True,
            sel=sel,
            django_field=django_field,
            target_type=target_type,
            target_definition=target_definition,
            plan=plan,
            prefix=prefix,
            lookup_prefix=lookup_prefix,
            full_path=full_path,
            info=info,
            runtime_paths=runtime_paths,
            resolver_identities=resolver_identities,
        )
        return True
    return False


def _scoped_hint_prefetch(
    prefetch: _PrefetchAny,
    *,
    django_field: FieldMeta,
    django_name: str,
    type_name: str,
    target_type: type[DjangoType] | None,
    target_definition: DjangoTypeDefinition | None,
    info: GraphQLResolveInfo | None,
) -> _PrefetchAny:
    """Return the consumer's hinted ``prefetch`` with its rows held to the target's visibility.

    A target whose type overrides ``get_queryset`` gets its hook over the hinted
    queryset through the same sealed child builder a generated ``Prefetch`` uses
    (``_build_child_queryset``), so the relation's resolver keys, which the hint
    records as optimizer-planned, are as scoped as a planned relation's. That
    seal also serves a combined hinted queryset as its primary-key set and fails
    a sliced one closed, because the hook narrows what it is handed. Any other
    target keeps the hinted queryset, rewritten only when it is combined
    (``_hint_prefetch_over_pk_set``).
    """
    if not _target_has_custom_get_queryset(target_type, target_definition):
        return _hint_prefetch_over_pk_set(prefetch, django_name=django_name, type_name=type_name)
    scoped = _build_child_queryset(
        django_field,
        target_type,
        info,
        has_custom_qs=True,
        target_definition=target_definition,
        seed=prefetch.queryset,
    )
    return Prefetch(prefetch.prefetch_through, queryset=scoped, to_attr=prefetch.to_attr)


def _hint_prefetch_over_pk_set(
    prefetch: _PrefetchAny,
    *,
    django_name: str,
    type_name: str,
) -> _PrefetchAny:
    """Return ``prefetch`` with a combined queryset rewritten to its primary-key set.

    Django's reverse-FK prefetch adds the parent-batch predicate to the child
    queryset with ``query.add_q()``, which the combinator compiler drops, so a
    hinted ``Prefetch(..., queryset=<union>)`` would scan the whole table and then
    fail on the unmatched rows. The hinted queryset therefore takes the same
    rewrite a sealed ``get_queryset`` result takes
    (``utils/querysets.py::_pk_membership_query_or_defect``), keeping its
    database alias, routing hints and nested prefetches, and a combinator the
    rewrite would serve different rows for fails at plan time. Any other ``Prefetch`` is returned
    unchanged.
    """
    inner = prefetch.queryset
    if inner is None or not inner.query.combinator:
        return prefetch
    rewritten, defect = _pk_membership_query_or_defect(inner.query, inner.model)
    if defect is not None:
        raise ConfigurationError(
            f"OptimizerHint.prefetch(obj) on {type_name}.{django_name}: the hinted "
            f"Prefetch queryset is combined ({defect[1]}); "
            + _COMBINED_WHAT.format(model=truth.name(inner.model), detail=defect[1]),
        )
    rebuilt: models.QuerySet[models.Model] = models.QuerySet(
        model=inner.model,
        query=rewritten,
        using=queryset_db(inner),
        # django-stubs types hint values as model instances (the ``instance`` hint Django
        # itself writes); a router hint can carry any value.
        hints=cast("dict[str, models.Model]", dict(queryset_hints(inner))),
    )
    queryset = rebuilt.prefetch_related(*queryset_prefetch_lookups(inner))
    return Prefetch(prefetch.prefetch_through, queryset=queryset, to_attr=prefetch.to_attr)


def _prefetch_hint_for_path(
    prefetch: _PrefetchAny,
    *,
    django_name: str,
    accessor: str,
    full_path: str,
    type_name: str,
) -> _PrefetchAny:
    """Return ``prefetch`` adapted from a type-relative lookup to ``full_path``.

    The type-relative lookup names the hinted relation in either of Django's
    spellings (``utils/relations.py::RelationSpelling``): its ``accessor``, the
    one ``prefetch_related`` takes, or its query name ``django_name``, the
    GraphQL field's. Either is rebased onto ``full_path``, which is spelled in
    accessors through every JOIN above it.
    """
    lookup: str | None = getattr(prefetch, "prefetch_through", None)
    if lookup is None:
        raise ConfigurationError(
            f"OptimizerHint.prefetch(obj) on {type_name}.{django_name} "
            "requires a Prefetch with a lookup path.",
        )
    if lookup == full_path or lookup.startswith(f"{full_path}__"):
        return prefetch
    for spelled in dict.fromkeys((accessor, django_name)):
        if lookup == spelled or lookup.startswith(f"{spelled}__"):
            adjusted_lookup = f"{full_path}{lookup.removeprefix(spelled)}"
            break
    else:
        raise ConfigurationError(
            f"OptimizerHint.prefetch(obj) lookup on {type_name}.{django_name} "
            f"must target the hinted relation {django_name!r}; got {lookup!r}.",
        )
    return Prefetch(
        adjusted_lookup,
        queryset=prefetch.queryset,
        to_attr=getattr(prefetch, "to_attr", None),
    )


def _absorb_child_plan(parent_plan: OptimizationPlan, child_plan: OptimizationPlan) -> None:
    """Absorb an ACCEPTED child queryset plan's metadata into the parent plan.

    Resolver metadata (``fk_id_elisions`` / ``planned_resolver_keys``) plus
    the ``cacheable`` propagation: a non-cacheable child (request-scoped
    consumer queryset, custom hook) must poison the parent's cacheability, or
    the plan cache could serve one request's child queryset to the next.
    Folded in here so the absorb cannot be forgotten (the cache-poisoning
    hazard the plan docstring warns about).

    Pure delegation to ``OptimizationPlan.merge_metadata_from``: the planner
    keeps its own direct merge line while the absorb is one call. If the
    absorb gains logic beyond delegation, the planner site routes through
    the (injected) wrapper or this wrapper dies.
    """
    parent_plan.merge_metadata_from(child_plan)


def _selected_scalar_names(
    selections: Iterable[ConvertedSelection],
    model: type[models.Model] | None,
) -> set[str] | None:
    """Return selected scalar Django field names, or ``None`` when elision is unsafe.

    Each selection resolves by the Python name the schema published its field
    from. On a Relay target the GlobalID selection (the field ``relay.Node``
    declares) resolves under the name ``relay.Node`` declares it as (``id``), so
    it reads the target key only where the field map's ``id`` is that key; the
    caller's ``_has_custom_id_resolver`` refuses an id read from anything else.
    """
    if model is None:
        return None
    # Nested-only: do NOT thread source_type here. The only caller is
    # _plan_select_relation for FK-id elision; the model argument is
    # django_field.related_model, never the resolver's root return type.
    # Nested relation targets correctly route through the primary via
    # registry.get(model), which is what the default _resolve_field_map(model)
    # call already does. The scalar-only secondary-type regression is
    # exercised through the root _walk_selections path, not through this
    # helper. (An audit invariant.)
    type_cls, _definition, field_map = _resolve_field_map(model)
    relay_type = type_cls if type_cls is not None and implements_relay_node(type_cls) else None
    # TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card): audit
    # this FK-id-elision helper as the walker's second ``included_field_selections`` consumer. This
    # is that card's requirement R2 in spec-035 Decision 6, and it is unreachable until the same
    # card builds the abstract-return production-entry contract (R1).
    # Pseudocode: either share the same type-condition classifier used by
    # ``_walk_selections`` or prove the helper only receives concretely typed
    # relation child selections where sibling fragments are GraphQL-invalid.
    #
    # No ``_merge_aliased_selections`` here (unlike ``_walk_selections``): this
    # helper only builds a SET of scalar field names, and merging aliased
    # duplicates before set insertion cannot change that set - two aliases of one
    # field collapse to a single name either way, and merging never turns a
    # scalar into a relation. Skipping the merge avoids a redundant second pass
    # over the same child selections the caller re-walks when elision does not
    # fire (the common case: any non-pk scalar selected).
    scalar_names: set[str] = set()
    for sel in _included_field_selections(selections):
        python_name = selection_python_name(sel)
        if relay_type is not None and python_name == _RELAY_ID_PYTHON_NAME:
            python_name = _RELAY_ID_DECLARED_NAME
        if python_name is None:
            return None
        django_field = field_map.get(python_name)
        if django_field is None or django_field.is_relation:
            return None
        scalar_names.add(python_name)
    return scalar_names


def _has_custom_id_resolver(
    target_type: type[DjangoType] | None,
    target_pk_name: str | None,
) -> bool:
    """Return ``True`` when target type customizes the selected id field.

    Routes through the registered definition's memoized check when one exists,
    and otherwise delegates to the *same* free function
    (``definition.origin_has_custom_id_resolver``) so the registered and
    definition-less paths cannot answer the same type differently.
    """
    if target_type is None or target_pk_name is None:
        return False
    definition = registry.get_definition(target_type)
    if definition is not None:
        return definition.has_custom_id_resolver_for(target_pk_name)
    # Lazy import: ``types.definition`` pulls in ``optimizer.field_meta`` at
    # module load, so importing it at the top of the walker risks an
    # import-time cycle through the optimizer package init.
    from django_strawberry_framework.types.definition import origin_has_custom_id_resolver  # noqa: PLC0415 - import cycle

    return origin_has_custom_id_resolver(target_type, target_pk_name)


def _ensure_connector_only_fields(
    plan: OptimizationPlan,
    parent_field: FieldMeta,
    *,
    base_queryset: QuerySet[models.Model],
) -> None:
    """Inject columns Django needs to attach prefetched rows to parents.

    Uses ``RelationJoinDescriptor.prefetch_attach_columns`` so a
    ``GenericRelation`` list prefetch (and every nested-connection child plan
    that shares this writer) loads both the ``object_id`` connector and the
    ``content_type_id`` morph half of Django's attach key - the same completeness
    ``_project_scalar_only_window`` already applied for scalar-only windows.

    The columns are recorded whenever the child rows will be projected: the child
    plan reads a column of its own, or ``base_queryset`` (the target type's hook
    or default manager) already carries an ``.only()`` / ``.defer()``, which a
    selection reading no column (``{ items { __typename } }``) would otherwise
    leave deferring the connector, so the attach would load it once per row. A
    plan reading no column over an unprojected base records nothing and the child
    rows load whole.
    """
    if not plan.only_fields and _consumer_projection(base_queryset) is None:
        return
    columns = classify_relation_join(parent_field).prefetch_attach_columns
    if not columns:
        logger.debug(
            "Optimizer: could not resolve connector column for Prefetch %s; "
            "only() may be less precise.",
            getattr(parent_field, "name", parent_field),
        )
        return
    for attname in columns:
        append_unique(plan.only_fields, attname)


class _MergedSelection(SimpleNamespace):
    """A field selection merged across duplicate response names, carrying per-key payloads."""

    _optimizer_response_key_arguments: dict[str, Mapping[str, object]]


def _merge_aliased_selections(selections: Sequence[FieldSelection]) -> Sequence[FieldSelection]:
    """Merge same-field selections while preserving all represented response keys.

    The main walker path passes fragment-inlined field selections here, so
    duplicate relation branches are combined before planning. The fragment
    passthrough below is retained for defensive direct helper use.

    Fast path: when no two selections share an exact GraphQL field name (the
    overwhelmingly common query shape - each field selected once), there is
    nothing to merge, so the input list is returned unchanged instead of
    rebuilding it into per-selection ``SimpleNamespace`` clones. Downstream
    readers (``_response_keys`` / ``_selection_runtime_prefixes`` /
    ``_aliased_arguments_diverge``) all ``getattr``-default the ``_optimizer_*``
    markers a raw selection lacks, so the passthrough is shape-compatible. Any
    fragment defensively forces the slow path (fragments cannot be deduped by
    name and are passed through by the merge loop below unchanged).
    """
    seen_names: set[str] = set()
    for sel in selections:
        if _is_fragment(sel):
            break
        key = sel.name
        if key in seen_names:
            break
        seen_names.add(key)
    else:
        return selections
    seen: dict[str, _MergedSelection] = {}
    result: list[FieldSelection] = []
    for sel in selections:
        if _is_fragment(sel):
            result.append(sel)
            continue
        key = sel.name
        if key in seen:
            merged = seen[key]
            # Keep duplicate selections as defensive as the first-seen
            # construction below; Strawberry currently provides a list here,
            # but some tests and future integration shims may omit it.
            merged.selections = list_of(read_attr(merged, "selections")) + list(
                getattr(sel, "selections", None) or [],
            )
            response_key = _response_key(sel)
            # The first-seen branch below built this as a list of response keys.
            merged_keys = require(read_attr(merged, "_optimizer_response_keys"), is_list)
            if response_key not in merged_keys:
                merged_keys.append(response_key)
            _merge_runtime_prefixes(merged, sel)
            # Preserve per-response-key argument payloads so a synthesized
            # connection sibling's pagination/sidecar arguments stay
            # comparable AFTER the merge (spec-033 Decision 6): identical
            # arguments across aliases are window-planned together (one shared
            # ``to_attr``), while divergent aliases (``a: books(first:2)`` +
            # ``b: books(first:5)``, or differing filter/order_by) plan ONE
            # WINDOW PER RESPONSE KEY under per-key ``to_attr``s
            # (O(aliases) batched queries). The first occurrence's
            # ``arguments`` stays the merged selection's primary value (the
            # pre-033 first-args-win contract for non-connection fields); the
            # per-response-key map is the side-channel ``_plan_connection_relation``
            # reads to select the scheme and derive each key's window.
            _record_response_key_arguments(merged, sel)
        else:
            merged = _MergedSelection(
                name=sel.name,
                alias=getattr(sel, "alias", None),
                directives=getattr(sel, "directives", None) or {},
                arguments=getattr(sel, "arguments", None) or {},
                selections=list(getattr(sel, "selections", None) or []),
                _optimizer_response_keys=[_response_key(sel)],
                **{
                    RUNTIME_PREFIXES_ATTR: _selection_runtime_prefixes(sel),
                    PYTHON_NAME_ATTR: selection_python_name(sel),
                    PYTHON_ARGUMENTS_ATTR: python_arguments(sel),
                },
                # Per-response-key argument payloads (spec-033 Decision 6), by
                # Python name; see the merge branch above and
                # ``_aliased_arguments_diverge``.
                _optimizer_response_key_arguments={_response_key(sel): python_arguments(sel)},
            )
            seen[key] = merged
            result.append(merged)
    return result


def _record_response_key_arguments(merged: _MergedSelection, selection: FieldSelection) -> None:
    """Record a duplicate selection's arguments under its response key.

    The merged selection carries ``_optimizer_response_key_arguments``: a map
    from response key to that occurrence's argument payload by Python name
    (``selections.py::python_arguments``). Kept off
    the inline merge branch so ``_merge_aliased_selections`` (a control-flow
    hotspot) does not grow another branch (spec-033 Decision 6).

    ONE response key arriving twice with DIFFERENT payloads is flagged as a
    conflict (``_optimizer_response_key_argument_conflict``). graphql-core's
    field-merging validation forbids that within one selection set, but the
    walker also merges the same-named CHILDREN of different parent-alias
    subtrees (``a: books(first: 1) { loans(first: 1) }`` + ``b: books(first:
    3) { loans(first: 2) }`` union their node children), where two payloads
    under one key are legal - and unservable by any single child plan, since
    the resolve side routes by response key alone (a silent overwrite here
    planned ONE nested window from the first payload and served the other
    alias a wrong page). ``_plan_connection_relation`` treats the flag as a
    fully-unplanned fallback. Payloads are graphql-core-coerced, so an inline
    literal and an equal resolved variable compare equal.
    """
    response_key = _response_key(selection)
    payload = python_arguments(selection)
    per_key = merged._optimizer_response_key_arguments
    if response_key in per_key and per_key[response_key] != payload:
        merged._optimizer_response_key_argument_conflict = True
    per_key[response_key] = payload


def _response_key_arguments_conflict(selection: FieldSelection) -> bool:
    """Return whether one response key carries two DIFFERENT argument payloads.

    Set by ``_record_response_key_arguments`` when parent-alias subtrees were
    union-merged (the only reachable source - graphql-core validation rules
    the shape out within one selection set). Selections built outside
    ``_merge_aliased_selections`` never carry the flag.
    """
    return getattr(selection, "_optimizer_response_key_argument_conflict", False)


def _aliased_arguments_diverge(selection: FieldSelection) -> bool:
    """Return whether a merged selection's aliases carry divergent arguments.

    ``True`` when two response keys of the same field were selected with
    different argument payloads (e.g. ``a: books(first: 2)`` +
    ``b: books(first: 5)``). The scheme selector for
    ``_plan_connection_relation``: divergent aliases plan one window PER
    RESPONSE KEY (each under its own ``to_attr``), while agreeing
    aliases share the single legacy window. Payloads are graphql-core-coerced,
    so the literal ``first: 2`` and a variable resolving to ``2`` agree. Selections built
    outside ``_merge_aliased_selections`` (direct test/helper callers) carry
    no per-response-key map and never diverge.
    """
    # ``_merge_aliased_selections`` built this map from response keys to payloads.
    per_key: dict[str, Mapping[str, object]] | None = getattr(
        selection,
        "_optimizer_response_key_arguments",
        None,
    )
    if not per_key:
        return False
    payloads = list(per_key.values())
    first = payloads[0]
    return any(payload != first for payload in payloads[1:])


def _selection_runtime_prefixes(selection: FieldSelection) -> list[tuple[str, ...]] | None:
    """Return selection-specific runtime prefixes carried by connection extraction."""
    # Every writer (``with_runtime_prefix`` and the merge below) stores a list of
    # runtime-path tuples.
    prefixes: Iterable[tuple[str, ...]] | None = getattr(
        selection,
        RUNTIME_PREFIXES_ATTR,
        None,
    )
    if prefixes is None:
        return None
    return list(prefixes)


def _merge_runtime_prefixes(merged: SimpleNamespace, selection: FieldSelection) -> None:
    """Union connection-carried runtime prefixes while preserving order."""
    incoming = _selection_runtime_prefixes(selection)
    if incoming is None:
        return
    # The first-seen merge branch stored a list of runtime-path tuples or ``None``.
    stored = read_attr(merged, RUNTIME_PREFIXES_ATTR)
    if stored is None:
        setattr(merged, RUNTIME_PREFIXES_ATTR, incoming)
        return
    carried = require(stored, is_list)
    for prefix in incoming:
        if prefix not in carried:
            carried.append(prefix)


def _plan_connection_relation(
    sel: FieldSelection,
    definition: DjangoTypeDefinition | None,
    *,
    relation_field_name: str,
    field_map: Mapping[str, FieldMeta],
    plan: OptimizationPlan,
    prefix: str,
    lookup_prefix: str,
    info: GraphQLResolveInfo | None,
    runtime_prefixes: tuple[tuple[str, ...], ...],
    type_cls: type[DjangoType] | None,
    model: type[models.Model],
) -> None:
    """Delegate one normalized nested connection and atomically merge its result."""
    result = _plan_nested_connection_relation(
        sel,
        definition,
        relation_field_name=relation_field_name,
        field_map=field_map,
        prefix=JoinPrefix(query=prefix, accessor=lookup_prefix),
        info=info,
        runtime_prefixes=runtime_prefixes,
        type_cls=type_cls,
        model=model,
        introduce_projection=plan.introduce_projection,
        resolve_optimizer_hints=_resolve_optimizer_hints,
        resolve_relation_target=_resolve_relation_target,
        response_key_arguments_conflict=_response_key_arguments_conflict,
        aliased_arguments_diverge=_aliased_arguments_diverge,
        target_has_custom_get_queryset=_target_has_custom_get_queryset,
        resolver_identities_for=_resolver_identities_for,
        build_child_queryset=_build_connection_child_queryset,
        build_prefetch_child_queryset_from_base=_build_prefetch_child_queryset_from_base,
    )
    plan.merge_from(result.plan)
