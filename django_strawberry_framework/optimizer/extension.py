"""``DjangoOptimizerExtension`` - Strawberry schema extension solving N+1 via queryset plans.

Opt-in at schema construction::

    _optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: _optimizer],
    )

The extension hooks Strawberry's ``resolve`` middleware. At the
operation's **root resolver** (detected via ``info.path.prev is None``)
it walks the entire selection tree once using the selection-tree walker, builds an
``OptimizationPlan``, and applies ``select_related`` /
``prefetch_related`` to the root queryset. Non-root resolvers pass
through untouched - Django's ``prefetch_related`` with ``__``-chained
paths handles nested optimization in a single pass.

Load-bearing rule: when a related field's target ``DjangoType``
defines a non-default ``get_queryset``, generate a
``Prefetch(...)`` keyed on the filtered queryset instead of a
``select_related``. This is the visibility-leak fix from
strawberry-graphql-django #572 / #583. We copy the behaviour, not the
API.

Architecture modeled on ``strawberry_django/optimizer.py`` - same
root-gate pattern, same per-execution state lifecycle, same recursive
type-tracing through graphql-core wrappers.
"""

from collections import OrderedDict
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import suppress
from typing import TYPE_CHECKING, NamedTuple, TypeVar, cast
from weakref import WeakKeyDictionary

from django.db import models
from graphql.language.ast import (
    DocumentNode,
    FieldNode,
    Location,
    VariableNode,
)
from graphql.language.printer import print_ast
from graphql.type.definition import (
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLUnionType,
    get_named_type,
)
from graphql.type.schema import GraphQLSchema
from graphql.utilities.separate_operations import separate_operations
from strawberry import Schema

# basedpyright: Strawberry annotates ``info`` as graphql-core's bare generic ``GraphQLResolveInfo``
from strawberry.types.nodes import get_variable_values  # pyright: ignore[reportUnknownVariableType]
from typing_extensions import override

from django_strawberry_framework.extensions.operation_state import (
    OperationState,
    _OperationBoundExtension,
    operation_is_nested,
)
from django_strawberry_framework.registry import register_subsystem_clear, registry
from django_strawberry_framework.utils import introspection
from django_strawberry_framework.utils._narrowing import (
    is_awaitable,
    is_dict,
    is_list_or_tuple,
    is_set_or_frozenset,
    is_str,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.connections import resolve_relay_max_results
from django_strawberry_framework.utils.execution_mode import operation_is_async
from django_strawberry_framework.utils.querysets import (
    normalize_query_source,
    run_in_one_sync_boundary,
    unwrap_async_queryset_adapter,
    wrap_async_queryset_adapter,
)
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_type_of,
    published_python_name,
    return_type_of,
    strawberry_schema_from_info,
)

from . import logger
from ._context import (
    DST_OPTIMIZER_FK_ID_ELISIONS,
    DST_OPTIMIZER_LOOKUP_PATHS,
    DST_OPTIMIZER_PLAN,
    DST_OPTIMIZER_PLANNED,
    DST_OPTIMIZER_STRICTNESS,
    active_optimizer,
    begin_execution_frame,
    cache_key_parts_memo,
    clear_optimizer_context,
    end_execution_frame,
    execution_plan_memo,
    operation_publishes_to_context,
    optimizer_value,
    publish_planned_windows,
    publish_scoped_relations,
    stash_for_optimizer,
)
from .hints import hint_is_skip
from .nested_fetch import NestedConnectionStrategy, StrategySelection, resolve_strategy
from .plans import (
    diff_plan_for_queryset,
    runtime_path_from_info,
    seals_consumer_prefetch,
)
from .selections import (
    ast_child_selections,
    ast_to_converted_selections,
    connection_node_children,
    directive_variable_names,
    named_children,
    node_children_with_runtime_prefix,
    resolve_unvisited_fragment,
    response_key,
)
from .walker import plan_optimizations

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet
    from types import SimpleNamespace
    from typing import TypeAlias

    from graphql.language.ast import FragmentDefinitionNode, Node, OperationDefinitionNode
    from graphql.type.definition import GraphQLResolveInfo, GraphQLType
    from strawberry.types.execution import ExecutionContext
    from strawberry.types.nodes import Selection

    from django_strawberry_framework.types.base import DjangoType
    from django_strawberry_framework.types.definition import DjangoTypeDefinition
    from django_strawberry_framework.utils.typing import EitherInfo

    from ._context import FrozenVariableValue, PlanCacheKey
    from .plans import OptimizationPlan
    from .selections import ConvertedSelection, FragmentVisitKey

    #: One ``_doc_key_cache`` key: source body, operation name, pagination wire names.
    _DocCacheKey: TypeAlias = tuple[str, str | None, frozenset[str]]

_M = TypeVar("_M", bound=models.Model)

_MAX_PLAN_CACHE_SIZE = 256

#: The strictness vocabulary ``DjangoOptimizerExtension`` accepts, keyed by name so a
#: match answers with the module's own constant and the validator and the rejection
#: message cannot drift apart.
_STRICTNESS_MODES = {mode: mode for mode in ("off", "warn", "raise")}


# The Python names of the Relay pagination arguments whose variable-supplied
# values must key the plan cache when they appear on a NON-ROOT field node (the
# planner bakes those resolved values into windowed prefetch querysets, so two
# requests differing only in a nested ``first: $n`` value need distinct cached
# plans -- spec-033 Decision 7). The document names them by the wire names the
# executing schema published them under (``_SchemaCacheRecord.pagination_wire_names``). Single
# source of truth for the family; a future ``search:`` extension
# would extend it here, not re-spell it inline.
_PAGINATION_PARAMETERS = frozenset(
    {
        "first",
        "last",
        "before",
        "after",
    },
)


class _SchemaCacheRecord(NamedTuple):
    """What the plan cache reads off one executable schema, built once per schema."""

    #: A fresh ``object()`` naming the schema in every plan-cache key. A plan bakes
    #: values the schema decides (its ``relay_max_results`` and resource-policy page
    #: caps, its published names), so one optimizer instance serving two schemas
    #: must never hand one schema's plan to the other. Neither ``id(schema)``
    #: (reused once the schema is collected) nor the schema itself (a strong
    #: reference from a long-lived cache would pin it).
    token: object
    #: Every wire name the schema publishes a pagination argument under.
    pagination_wire_names: frozenset[str]


#: ``{executable schema: its _SchemaCacheRecord}``, built once per schema and
#: dropped with it. Keyed per schema because one document can be executed against
#: schemas whose ``NameConverter`` spells the arguments differently, and because
#: one optimizer instance can serve several schemas.
_schema_cache_records: "WeakKeyDictionary[GraphQLSchema, _SchemaCacheRecord]" = WeakKeyDictionary()


def _schema_cache_record(schema: "GraphQLSchema") -> _SchemaCacheRecord:
    """Return ``schema``'s plan-cache record, building it on first sight.

    The pagination wire names are read back off the published field maps: an
    argument whose declaration's Python name (``published_python_name``) is one
    of ``_PAGINATION_PARAMETERS`` contributes the name a client sends it under,
    so a converter renaming ``first`` keys the renamed variable and a converter
    swapping ``first`` and ``last`` keys both. The set spans every field, which
    keeps the collection a superset by name (spec-033 Decision 7). Memoized for
    the schema's lifetime, so the schema's token stays the same across its
    operations.
    """
    memoized = _schema_cache_records.get(schema)
    if memoized is not None:
        return memoized
    # ``setdefault`` publishes the first record built for ``schema``: two threads
    # meeting a new schema at once both answer with one token.
    return _schema_cache_records.setdefault(
        schema,
        _SchemaCacheRecord(
            token=object(),
            pagination_wire_names=frozenset(
                wire_name
                for named_type in schema.type_map.values()
                if isinstance(named_type, (GraphQLObjectType, GraphQLInterfaceType))
                for field in graphql_fields(named_type).values()
                for wire_name, argument in field.args.items()
                if published_python_name(argument) in _PAGINATION_PARAMETERS
            ),
        ),
    )


__all__ = (
    "CacheInfo",
    "DjangoOptimizerExtension",
    "apply_connection_optimization",
    "apply_connection_optimization_async",
)


def _walk_cache_relevant_vars(
    node: "Node",
    fragments: "Mapping[str, FragmentDefinitionNode]",
    visited_fragments: "set[FragmentVisitKey]",
    depth: int,
    directive_names: set[str],
    pagination_names: set[str],
    pagination_wire_names: frozenset[str],
) -> None:
    """Collect BOTH cache-relevant variable families in a single AST traversal.

    One descent collects two families on different axes:

    * **Directive variables** - ``@skip`` / ``@include`` variable references on
      EVERY node, independent of depth.
    * **Nested pagination variables** - variable references under an argument
      named one of ``pagination_wire_names`` (the wire names the executing
      schema publishes ``first`` / ``last`` / ``before`` / ``after`` under,
      ``_SchemaCacheRecord.pagination_wire_names``) only when the current node
      is a ``FieldNode`` at response-path depth >= 1 (root-field pagination stays out: a root
      connection's slicing happens post-plan in ``ConnectionExtension`` and plan
      content is invariant in those, so hashing them would fragment the cache
      across every page of a pagination loop).

    Depth increments only when descending into a **field** node's selection set;
    descending into a resolved fragment definition keeps the SPREAD-SITE depth (a
    fragment is a transparent wrapper at its spread site -- spec-033 Decision 7's "depth at
    the spread SITE, not raw fragment-definition nesting"), so a spread at the
    root contributes root-depth fields and a spread inside a nested node
    contributes nested-depth fields. The cycle guard keys ``visited_fragments``
    on ``(fragment_name, spread-site depth)`` so a fragment spread twice at the
    SAME depth is walked once, while the SAME fragment spread at two DIFFERENT
    depths is walked once per depth: pagination collection is depth-sensitive, so
    a name-only guard would let the first-visited spread site (e.g. a root spread,
    where pagination is excluded) suppress a later nested spread of the same
    fragment and silently drop its nested pagination variable from the cache key
    -- a correctness bug (spec-033 Decision 7: "under-collection serves wrong data").
    Termination still holds: graphql-core rejects fragment cycles before the
    optimizer runs, and a defensive cycle that does not cross a field node keeps
    depth constant, so ``(name, depth)`` repeats and the descent stops.

    One walker for both families rather than a directive walker and a
    pagination-variable walker: the two collection RULES differ but the
    child-traversal, fragment-spread descent, and cycle-guard plumbing are
    identical, and keeping them apart would risk a future fragment-depth or cycle
    fix landing on only one path.
    """
    # Directive variables: collected on every node, depth-independent. The
    # ``@skip`` / ``@include`` variable extraction is the shared AST-adapter
    # primitive (``optimizer/selections.py::directive_variable_names``).
    directive_names.update(directive_variable_names(node))
    # Nested pagination variables: only on a field node at depth >= 1.
    if depth >= 1 and isinstance(node, FieldNode):
        for arg in node.arguments or ():
            if arg.name.value in pagination_wire_names and isinstance(arg.value, VariableNode):
                pagination_names.add(arg.value.name.value)
    # A field node deepens the response path for its children; a fragment
    # wrapper does not, so its body inherits the field node's depth here.
    child_depth = depth + 1 if isinstance(node, FieldNode) else depth
    for child in ast_child_selections(node):
        # Recurse into the child first so directives attached to the child
        # itself are collected (a FragmentSpreadNode has no ``selection_set``,
        # so this tail is just the directive sweep for spread-node directives).
        _walk_cache_relevant_vars(
            child,
            fragments,
            visited_fragments,
            child_depth,
            directive_names,
            pagination_names,
            pagination_wire_names,
        )
        # Resolve the fragment spread depth-aware: pass ``depth=child_depth`` so
        # the shared AST-adapter guard keys ``visited_fragments`` on
        # ``(name, depth)`` rather than name alone. A name-only key would drop
        # nested pagination variables when an earlier root-depth spread visited
        # the fragment first (spec-033 Decision 7).
        frag_def = resolve_unvisited_fragment(
            child,
            fragments,
            visited_fragments,
            depth=child_depth,
        )
        if frag_def is not None:
            _walk_cache_relevant_vars(
                frag_def,
                fragments,
                visited_fragments,
                child_depth,
                directive_names,
                pagination_names,
                pagination_wire_names,
            )


def _collect_cache_var_families(
    node: "Node",
    fragments: "Mapping[str, FragmentDefinitionNode]",
    pagination_wire_names: frozenset[str],
) -> tuple[set[str], set[str]]:
    """Run the unified traversal and return ``(directive_names, pagination_names)``.

    ``directive_names`` holds only the variables inside a ``@skip`` /
    ``@include`` ``if`` argument: every other variable leaves the selection tree
    unchanged and stays out of the cache key to avoid cardinality explosion.
    ``pagination_names`` holds the variables under a pagination argument
    (``pagination_wire_names``) on a non-root field node, which the planner bakes into windowed
    prefetch querysets; the collection is a syntactic SUPERSET by design, since
    over-collection costs a duplicate cache entry while under-collection would
    serve wrong data (spec-033 Decision 7). Both families come from ONE AST walk.
    """
    directive_names: set[str] = set()
    pagination_names: set[str] = set()
    _walk_cache_relevant_vars(
        node,
        fragments,
        set(),
        0,
        directive_names,
        pagination_names,
        pagination_wire_names,
    )
    return directive_names, pagination_names


def _collect_cache_relevant_var_names(
    operation: "OperationDefinitionNode",
    fragments: "Mapping[str, FragmentDefinitionNode]",
    pagination_wire_names: frozenset[str],
) -> frozenset[str]:
    """Union of the cache-relevant variable names for one operation.

    Combines the ``@skip`` / ``@include`` directive variable names with the
    non-root pagination variable names -- in ONE AST traversal
    (``_collect_cache_var_families``) -- so ``_build_cache_key`` folds one name
    set through its single ``(name, value)`` comprehension. The result is what
    ``_doc_cache_entry`` memoizes cross-request alongside the rendered document
    key (both are pure functions of the document text).
    """
    directive_names, pagination_names = _collect_cache_var_families(
        operation,
        fragments,
        pagination_wire_names,
    )
    return frozenset(directive_names | pagination_names)


def _hashable_variable_value(value: object) -> "FrozenVariableValue":
    """Return a hashable cache identity for one variable value.

    ``_build_cache_key`` stores cache-relevant ``(name, value)`` pairs in a
    ``frozenset``. GraphQL lists and input objects arrive as unhashable builtin
    containers, and a custom scalar parser may return any Python value; the
    nested-pagination collector over-collects by argument name, so a plain
    nested field such as ``logs(after: $values)`` can put any input type on
    this cache boundary.

    Builtin ``dict`` / ``set`` / ``frozenset`` / ``list`` / ``tuple`` values are
    frozen member by member; any other hashable value keys as itself. Every
    identity is tagged with its value's type, so ``1`` and ``True``, or a list
    and a tuple, never share a key, and unordered containers stay deterministic
    through their frozen members. A value of an unhashable class keys as a fresh
    opaque token: that request misses the cross-request plan cache.
    """
    value_type_id = id(type(value))
    if is_dict(value):
        return (
            "mapping",
            value_type_id,
            frozenset(
                (_hashable_variable_value(key), _hashable_variable_value(item))
                for key, item in value.items()
            ),
        )
    if is_set_or_frozenset(value):
        return ("set", value_type_id, frozenset(map(_hashable_variable_value, value)))
    if is_list_or_tuple(value):
        return ("sequence", value_type_id, tuple(map(_hashable_variable_value, value)))
    try:
        _ = hash(value)
    except TypeError:
        return ("opaque", value_type_id, object())
    return ("scalar", value_type_id, value)


def _print_operation_with_reachable_fragments(
    operation: "OperationDefinitionNode",
    fragments: "Mapping[str, FragmentDefinitionNode]",
) -> str:
    """Render the plan-cache document key.

    Prints the operation together with every fragment definition reachable
    from it, as graphql-core's ``separate_operations`` selects them (document
    order). This is the load-bearing distinction from a bare
    ``print_ast(operation)``: two operations with identical bodies but
    different reachable fragment bodies render to different strings, so they
    never share a cached plan built for the wrong fragment shape, while an
    unreachable fragment leaves the key unchanged.
    """
    (separated,) = separate_operations(
        DocumentNode(definitions=(operation, *fragments.values())),
    ).values()
    return print_ast(separated)


_MAX_DOC_KEY_CACHE_SIZE = 256

# Cross-request memo for the two document-derived cache-key ingredients - the
# rendered document key AND the cache-relevant variable-NAME frozenset - keyed by
# the operation's raw source text, its name, and the executing schema's
# pagination wire names (``_SchemaCacheRecord.pagination_wire_names``). Both values are pure
# functions of those: two requests with byte-identical document text parse to
# structurally identical ASTs, so the printed key and the ``@skip``/``@include``
# plus nested-pagination name set are identical under one wire vocabulary. Caching them together means a
# hot query neither ``print_ast``s NOR re-walks its full operation AST
# (``_collect_cache_relevant_var_names`` is a full AST descent) after first sight.
# The per-execution cache-key-parts memo only dedupes within ONE request (keyed on
# ``id(operation)``); this module-level LRU carries the far more valuable
# cross-request reuse. Correctness-neutral under concurrency exactly like
# ``_plan_cache`` - the cached value is deterministic, so a dropped or double
# insert only changes hit rate. Bounded LRU so a long-lived process with many
# distinct documents does not grow without limit.
_doc_key_cache: "OrderedDict[_DocCacheKey, tuple[str, frozenset[str]]]" = OrderedDict()


def clear_document_key_cache() -> None:
    """Empty the cross-request document-key memo shared by every extension instance.

    Registered with ``registry.clear()`` so a registry-clearing test also drops
    it. Correctness-neutral like the memo itself: the next request per document
    recomputes its key and variable-name set.
    """
    _doc_key_cache.clear()


register_subsystem_clear(clear_document_key_cache, owner="optimizer.document_key_cache")


def _doc_cache_entry(
    operation: "OperationDefinitionNode",
    fragments: "Mapping[str, FragmentDefinitionNode]",
    pagination_wire_names: frozenset[str],
) -> tuple[str, frozenset[str]]:
    """Return ``(doc_key, cache_relevant_var_names)``, memoized cross-request by source text.

    Keys on ``(operation.loc.source.body, operation_name, pagination_wire_names)``:
    the source body is the WHOLE document text (every operation and fragment
    definition), so any difference in a reachable fragment body is already
    reflected in it, the operation name disambiguates the operations of a
    multi-operation document (which share one body), and the wire names keep
    one document executed against two schemas' vocabularies apart. Strawberry
    parses every executed document from its source text, so the operation always
    carries its ``loc``.

    ``_collect_cache_relevant_var_names`` is called through the module global
    (not captured) so a test spy patched onto the module still intercepts the
    miss-path collection.
    """
    name = operation.name.value if operation.name is not None else None
    key = (require_instance(operation.loc, Location).source.body, name, pagination_wire_names)
    cached = _doc_key_cache.get(key)
    if cached is not None:
        # ``move_to_end`` is the LRU promotion; guard the concurrent-eviction
        # race the same way the plan cache does (one module cache is shared
        # across all extension instances and threads).
        with suppress(KeyError):
            _doc_key_cache.move_to_end(key)
        return cached
    entry = (
        _print_operation_with_reachable_fragments(operation, fragments),
        _collect_cache_relevant_var_names(operation, fragments, pagination_wire_names),
    )
    _doc_key_cache[key] = entry
    if len(_doc_key_cache) > _MAX_DOC_KEY_CACHE_SIZE:
        with suppress(KeyError):
            _ = _doc_key_cache.popitem(last=False)
    return entry


SelectionExtractor = Callable[
    [list["Selection"], "GraphQLResolveInfo[object]"],
    Sequence["ConvertedSelection"],
]


def _root_child_selections(
    selections: "list[Selection]",
    _info: "GraphQLResolveInfo[object]",
) -> "list[Selection]":
    """Flatten children from every converted root field node.

    GraphQL merges repeated root fields with the same response key
    into one resolver call but exposes every contributing ``FieldNode``
    in ``info.field_nodes``. After ``convert_selections``, the returned
    list has one entry per field node, and the walker needs the union
    of their children. Reading only ``selections[0].selections`` would
    drop relations selected by the second node, so
    ``{ allItems { name } allItems { category { name } } }`` would
    skip planning ``category``. The walker's existing alias merging
    (``_merge_aliased_selections``) deduplicates within the flattened
    list, so the order in which we flatten does not matter for plan
    correctness.
    """
    children: list[Selection] = []
    for selection in selections:
        children.extend(selection.selections)
    return children


def _connection_node_child_selections(
    selections: "list[Selection]",
    info: "GraphQLResolveInfo[object]",
) -> "list[SimpleNamespace]":
    """Return node-level selections from a Relay connection wrapper.

    Connection resolvers optimize the pre-slice node queryset, so the ORM walker
    must see the same child selection list it would receive for a list field over
    the node type. The GraphQL runtime path still includes ``edges`` and
    ``node``, though, so node children carry selection-specific prefixes for
    strictness and FK-id-elision resolver keys. The edges->node composition itself
    lives in ``selections.connection_node_children`` (shared with nested planning);
    this extractor only supplies the root response path from ``info``.
    """
    node_children: list[SimpleNamespace] = []
    root_path = runtime_path_from_info(info)
    for connection_selection in selections:
        node_children.extend(
            connection_node_children(connection_selection, runtime_prefixes=(root_path,)),
        )
    return node_children


def mutation_payload_child_selections(slot: str) -> SelectionExtractor:
    """Build a selection extractor for a mutation payload's object slot (spec-036 Decision 9).

    A mutation field returns ``<field> { <slot> { ...children } errors { ... } }``
    where ``<slot>`` is ``node`` (Relay-Node target) or ``result`` (non-Node). The
    post-write re-fetch must plan the SAME child-selection list a list field over
    the node type would, so the walker sees the response selection rooted at the
    node type - exactly the connection extractor's job, but navigating one
    ``<slot>`` level instead of ``edges { node }``. Returns a closure over ``slot``
    so the resolver passes ``mutation_payload_child_selections(slot)`` to
    ``apply_connection_optimization``.
    """

    def _extract(
        selections: "list[Selection]",
        info: "GraphQLResolveInfo[object]",
    ) -> "list[SimpleNamespace]":
        node_children: list[SimpleNamespace] = []
        root_path = runtime_path_from_info(info)
        for field_selection in selections:
            for slot_selection in named_children(field_selection, slot):
                slot_path = (*root_path, response_key(slot_selection))
                node_children.extend(
                    node_children_with_runtime_prefix(
                        slot_selection,
                        runtime_prefixes=(slot_path,),
                    ),
                )
        return node_children

    return _extract


class CacheInfo(NamedTuple):
    """Plan-cache statistics (hits, misses, current size)."""

    hits: int
    misses: int
    size: int


def _collect_schema_reachable_types(schema: object) -> "set[type[DjangoType]]":
    """Return the set of ``DjangoType`` classes reachable from the schema's root types.

    Traverses from ``query_type``, ``mutation_type``, and
    ``subscription_type`` through their field return types recursively,
    descending into object fields, union members, and the concrete
    implementations of any interface type encountered (so a
    ``DjangoType`` reachable only via an interface-typed root field -
    e.g. ``relay.Node`` implementers - still participates in the
    ``check_schema`` audit).  Only types reachable from a root
    operation are included; orphan types passed via ``types=[]`` at
    schema construction are excluded to avoid false-positive audit
    warnings.
    """
    reachable: set[type[DjangoType]] = set()
    strawberry_schema = require_instance(schema, Schema)
    # Strawberry's ``Schema.__init__`` stores the graphql-core schema it builds at
    # ``_schema``.
    gql_schema = require_instance(read_attr(strawberry_schema, "_schema"), GraphQLSchema)
    visited_type_names: set[str] = set()

    def _walk_gql_type(gql_type: "GraphQLType") -> None:
        """Recursively collect DjangoType origins from a graphql-core type."""
        named = get_named_type(gql_type)
        type_name = named.name
        if type_name in visited_type_names:
            return
        visited_type_names.add(type_name)
        # Check if this type is a DjangoType.
        definition = strawberry_schema.get_type_by_name(type_name)
        if definition is not None:
            registered = registry.get_definition(read_attr(definition, "origin", None))
            if registered is not None:
                reachable.add(registered.origin)
        # Recurse into fields; an output walk reaches no input object type.
        if isinstance(named, (GraphQLObjectType, GraphQLInterfaceType)):
            for field_obj in graphql_fields(named).values():
                _walk_gql_type(graphql_type_of(field_obj))

        # Recurse into a union's members and an interface's implementations, so a
        # ``DjangoType`` reachable only via an abstract-typed root field (e.g. a
        # ``relay.Node`` implementer) still participates in the audit.
        if isinstance(named, (GraphQLUnionType, GraphQLInterfaceType)):
            for possible_type in gql_schema.get_possible_types(named):
                _walk_gql_type(possible_type)

    for root_type in (
        gql_schema.query_type,
        gql_schema.mutation_type,
        gql_schema.subscription_type,
    ):
        if root_type is not None:
            _walk_gql_type(root_type)
    return reachable


def _resolve_model_from_return_type(
    info: "GraphQLResolveInfo[object]",
) -> "DjangoTypeDefinition | None":
    """Trace ``info.return_type`` through graphql-core wrappers to its ``DjangoTypeDefinition``.

    graphql-core wraps resolver return types in layers of
    ``GraphQLNonNull`` and ``GraphQLList``. This function reads the named
    type under them through graphql-core's ``get_named_type``, then looks
    up the corresponding Strawberry type definition via the schema by its
    name and reverse-maps to the registered definition, whose ``origin``
    feeds plan-cache identity and whose ``model`` feeds the walker.

    Returns ``None`` when any step fails (non-object leaf, missing
    schema backref, missing schema type, unregistered origin). The
    caller treats ``None`` as "nothing to optimize" and passes the
    queryset through unchanged.
    """
    type_name = get_named_type(return_type_of(info)).name
    strawberry_schema = strawberry_schema_from_info(info)
    if strawberry_schema is None:
        return None
    definition = strawberry_schema.get_type_by_name(type_name)
    if definition is None:
        return None
    return registry.get_definition(read_attr(definition, "origin", None))


class _OptimizerOperationState(OperationState):
    """One operation's optimizer state, for the extension answering it.

    ``stashes`` is this operation's own plan / elision / planned-relation /
    lookup-path / strictness store. The request context object is shared - a
    resolver may hand its own ``info.context`` to an inner execution - and the
    inner operation's start-of-execution clear would otherwise erase values the
    outer one is still resolving against.
    """

    __slots__: tuple[str, ...] = ("stashes",)

    def __init__(self, execution_context: "ExecutionContext") -> None:
        super().__init__(execution_context)
        self.stashes: dict[str, object] = {}


class DjangoOptimizerExtension(_OperationBoundExtension[_OptimizerOperationState]):
    """Strawberry schema extension that optimizes Django querysets per request.

    Pass a module-level singleton wrapped in a factory - that preserves
    the instance-bound plan cache (Strawberry runs the callable per
    request and gets the same instance back) and emits no deprecation
    warning (the entry is a callable, not an instance)::

        _optimizer = DjangoOptimizerExtension()
        schema = DjangoSchema(
            query=Query,
            config=strawberry_config(),
            extensions=[lambda: _optimizer],  # singleton wrapped in a factory
        )

    The plan cache is correctness-safe under concurrent / async access
    (a missed insert or a double-evict only reduces hit rate; it cannot
    return wrong data), but the hit-rate and counter introspection
    exposed via ``cache_info()`` is best-effort - see ``cache_info``
    for the full caveat.

    Hooks:

    - ``on_execute`` - opens the execution frame that marks the optimizer
      as active for the operation's lifetime, and closes it at the end.
    - ``resolve`` - gates on ``info.path.prev is None`` (root resolver
      only). Calls ``_next``, checks ``isinstance(QuerySet)``, traces
      the Django model from the graphql-core return type, runs the
      selection-tree walker, applies the plan.

    Resolver-shape contract: a root resolver that returns a Django
    ``Manager`` (e.g. ``Model.objects`` shorthand) is coerced to a
    ``QuerySet`` via ``.all()`` before the ``isinstance(QuerySet)`` gate
    in ``_optimize``, so the optimizer is applied uniformly whether the
    consumer wrote ``Model.objects`` or ``Model.objects.all()``.

    ``strictness`` is always the vocabulary's own plain ``str`` (``"off"`` /
    ``"warn"`` / ``"raise"``), whatever ``str`` subclass spelled it at
    construction, so every per-request comparison is the package's and never
    the caller's.
    """

    def __init__(
        self,
        strictness: str = "off",
        *,
        execution_context: "ExecutionContext | None" = None,
        nested_connection_strategy: StrategySelection | None = None,
    ) -> None:
        """Set the N+1 ``strictness`` and the nested-connection strategy for this instance."""
        # Strawberry assigns ``extension.execution_context`` once per
        # operation. The documented singleton-factory form returns this SAME
        # extension instance to concurrent and to NESTED operations, so the
        # engine's assignment is taken as a handoff and this operation's context
        # is read from the state the package runner binds
        # (``extensions/operation_state.py``); the plan cache below remains
        # intentionally instance-shared.
        super().__init__()
        # ``execution_context`` stays accepted for direct-construction
        # compatibility only: at the ``strawberry-graphql>=0.328.0`` floor the
        # engine invokes class/factory entries in ``extensions=[...]`` with
        # ZERO arguments and assigns ``extension.execution_context`` afterward,
        # so Strawberry itself never passes this keyword (spec-044 Decision 6
        # migration notes). Unknown consumer kwargs still raise ``TypeError``
        # at construction so typos (``strict=True``) surface at the call site
        # rather than being silently absorbed.
        self.execution_context: ExecutionContext | None = execution_context
        # The stored mode is the vocabulary's own constant, never the candidate.
        # Whether the candidate is a ``str`` is asked of its real type
        # (``utils/_narrowing.py::is_str``), so a ``__class__`` property can
        # neither claim ``str`` nor raise.
        accepted_strictness = _STRICTNESS_MODES.get(strictness) if is_str(strictness) else None
        if accepted_strictness is None:
            msg = f"strictness must be 'off', 'warn', or 'raise', got {strictness!r}"
            raise ValueError(msg)
        # The nested-connection fetch strategy is fixed per extension INSTANCE
        # at construction (``None`` reads the ``NESTED_CONNECTION_STRATEGY``
        # setting, defaulting to windowed). The plan cache below is
        # instance-bound, so pinning the strategy here guarantees one cache
        # never mixes plans from two strategies. ``"auto"`` itself is one
        # backend-neutral strategy whose lateral-capable windowed queryset
        # selects by its fetch-time alias (``optimizer/nested_fetch.py``);
        # cached plans therefore remain valid across router decisions. Unknown
        # names raise ``ConfigurationError`` at construction, not at query time.
        self.strictness: str = accepted_strictness
        self.nested_connection_strategy: NestedConnectionStrategy = resolve_strategy(
            nested_connection_strategy,
        )
        self._plan_cache: OrderedDict[PlanCacheKey, OptimizationPlan] = OrderedDict()
        self._cache_hits: int = 0
        self._cache_misses: int = 0

    @override
    def _new_operation_state(
        self,
        execution_context: "ExecutionContext",
    ) -> _OptimizerOperationState:
        """Build this operation's optimizer state."""
        return _OptimizerOperationState(execution_context)

    def cache_info(self) -> CacheInfo:
        """Return plan-cache statistics (hits, misses, current size).

        The extension instance is shared across requests, and the plan
        cache and counters are mutated without a lock. Under concurrent
        or async access the hit/miss counters and the reported ``size``
        are best-effort: two threads racing ``+= 1`` can drop a count,
        and two concurrent inserts at the eviction threshold can evict
        twice. The cache itself is correctness-neutral - a missed insert
        or a double-evict only reduces hit rate; it cannot return wrong
        data.
        """
        return CacheInfo(
            hits=self._cache_hits,
            misses=self._cache_misses,
            size=len(self._plan_cache),
        )

    def cache_clear(self) -> None:
        """Empty this instance's plan cache and zero its hit and miss counters.

        The next request per selection shape builds its plan again. The
        module-level document-key memo is shared across instances and stays
        warm; ``clear_document_key_cache`` empties it. Safe beside concurrent
        requests for the reason ``cache_info`` gives: a request racing the
        clear only loses a hit or a count, never gets a wrong plan.
        """
        self._plan_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    @override
    def on_execute(self) -> Iterator[None]:
        """Open this execution's frame, and close it however the operation ends.

        One frame carries everything the execution publishes to itself - this
        instance, its nested-fetch strategy and strictness, the stash store, the
        planned-relation keys and the three per-execution memos - because all of
        them end together (``_context.py::_ExecutionFrame``).
        """
        # ``execution_context.context`` is the same object resolvers see as
        # ``info.context`` (Strawberry wires both to ``context_value``), and it
        # is ``None`` for a direct caller that invokes ``on_execute`` outside
        # any operation.
        state = self._operation_state()
        execution_context: ExecutionContext | None = self.execution_context
        # This operation's own store for every optimizer stash. What the package
        # reads back is here, so an operation running inside another one can
        # neither erase nor answer for the outer operation's plan; the request's
        # own operation publishes there as well, as introspection. Which one
        # this is comes from the runner that owns the operation rather than from
        # where in the hook order the store is opened - an operation started
        # from a consumer extension's teardown begins after the outer
        # optimizer's frame was closed and is still inside the outer request.
        frame = begin_execution_frame(
            {} if state is None else state.stashes,
            nested=operation_is_nested(),
            optimizer=self,
            strategy=self.nested_connection_strategy,
            strictness=self.strictness,
        )
        # Drop any optimizer stashes left on a reused ``context_value`` before
        # this operation publishes, and only for the operation that object
        # describes. Without it, sequential ``execute_sync`` calls sharing one
        # context object would show a consumer reading the published plan off
        # their request a prior operation's FK-id elisions and planned-resolver
        # keys; the package's own reads answer from ``frame`` and never see them.
        if operation_publishes_to_context():
            clear_optimizer_context(getattr(execution_context, "context", None))
        try:
            yield
        finally:
            end_execution_frame(frame)

    @override
    def resolve(
        self,
        _next: Callable[..., object],
        root: object,
        info: "GraphQLResolveInfo[object]",
        *args: object,
        **kwargs: object,
    ) -> object:
        """Root-gated resolver hook.

        Only root-level resolvers (``info.path.prev is None``) trigger
        the optimization pass. All other resolvers pass through
        unchanged - the prefetch chain applied at the root handles
        nested relations via Django's ``__``-chain support.

        Handles both sync and async resolvers: when ``_next`` returns a
        coroutine (async resolver), returns an async wrapper that awaits
        the result and then builds a plan off the event loop. Strawberry's
        ``SchemaExtension.resolve`` returns ``AwaitableOrValue`` for
        exactly this reason. Which thread builds a plan follows the executor,
        not the resolver's color: under the asynchronous executor a plain
        ``def`` root runs on the event loop too, so a plan its queryset needs
        is built in the same sync boundary, and a cached plan is applied on the
        loop, by the one predicate both colors ask (``_needs_sync_boundary``).
        The synchronous executor never hops. Either way this hook returns the
        planned queryset unevaluated; under the asynchronous executor list
        completion fetches its rows off the loop (graphql-core completes a value
        exposing ``__aiter__`` through it).
        """
        result = _next(root, info, *args, **kwargs)
        if read_attr(info.path, "prev") is not None:
            return result
        if is_awaitable(result):

            async def _async_optimize() -> object:
                value = await result
                if self._needs_sync_boundary(value, info):
                    return await run_in_one_sync_boundary(self._optimize, value, info)
                return self._optimize(value, info)

            return _async_optimize()
        if operation_is_async() and self._needs_sync_boundary(result, info):
            return run_in_one_sync_boundary(self._optimize, result, info)
        return self._optimize(result, info)

    def _optimize(self, result: object, info: "GraphQLResolveInfo[object]") -> object:
        """Apply the selection-tree walker's plan to a root-level ``QuerySet`` (middleware path).

        Steps:

        1. ``Manager`` results are coerced via ``.all()`` so a resolver
           returning ``Model.objects`` (the Django shorthand) is
           optimized instead of being silently passed through. The
           manager's ``.all()`` returns a fresh unevaluated ``QuerySet``;
           no rows are fetched at this step.
        2. Non-``QuerySet`` results pass through unchanged.

           Steps 1-2 are the shared ``utils/querysets.py::normalize_query_source``
           contract - the same Manager-coercion + is-queryset decision the
           list / connection field consumer paths use, so the middleware never
           decides it independently.
        3. An already-evaluated queryset (``_result_cache`` populated) is
           returned unchanged (``spec-035`` Decision 3). The consumer's
           root resolver already ran the SQL (a ``len(qs)`` guard, a
           ``bool(qs)`` branch, a slice for a log line); past this point
           :meth:`apply_to` clones the queryset to attach ``.only()`` /
           ``select_related``, and a clone of an evaluated queryset silently
           re-executes that SQL - a doubled query invisible to the consumer.
           This extends queryset diffing's "respect what the consumer already did" posture
           from optimization state to execution state.
        4. Trace the graphql-core return type to a Django ``(origin, model)``.
        5. Delegate the plan-build-and-apply tail to :meth:`apply_to`, passing
           the resolved ``origin`` / ``model`` explicitly - the SAME helper
           the connection field's ``apply_connection_optimization`` calls, so
           the two share one plan-application implementation (spec-030 Decision 11).
           The middleware path is behavior-identical: ``_optimize`` only adds
           the return-type resolution the connection field does NOT need
           (the connection field's return type is the connection type, not the
           node type). A combined queryset passes through ``apply_to``
           unplanned.

        The async-adapter contract wraps every step: ``result`` is unwrapped
        on entry and re-wrapped on exit exactly when it arrived adapted, so
        each step sees the plain queryset
        (``utils/querysets.py::unwrap_async_queryset_adapter`` /
        ``utils/querysets.py::wrap_async_queryset_adapter``).

        """
        inner_result, was_adapted = unwrap_async_queryset_adapter(result)

        def finish(val: object) -> object:
            return wrap_async_queryset_adapter(val) if was_adapted else val

        normalized = normalize_query_source(inner_result)
        if normalized[1] is False:
            return finish(normalized[0])
        inner_result = normalized[0]
        # spec-035 Decision 3: a consumer-evaluated root queryset passes
        # through unchanged. Placement is load-bearing in both directions - it
        # sits AFTER the Manager coercion (a coerced ``.all()`` is always a
        # fresh unevaluated queryset, so a ``Model.objects``-returning resolver
        # still optimizes) and BEFORE the return-type resolution / ``apply_to``
        # clone (which would re-execute the SQL). ``is not None`` is the exact,
        # allocation-free signal upstream uses: ``_result_cache`` is ``None``
        # until evaluated and a (possibly empty) list after, so truthiness would
        # mis-handle an evaluated-but-empty queryset. The gate above proves a
        # queryset (``normalize_query_source`` narrows here), and Django's
        # ``QuerySet.__init__`` always sets the slot, so the typed read is
        # exact - a non-queryset returns at the gate and never reaches this line.
        if inner_result._result_cache is not None:
            return finish(inner_result)
        resolved = _resolve_model_from_return_type(info)
        if resolved is None:
            logger.debug(
                "Optimizer: return type for %s has no registered DjangoType; "
                "passing queryset through unchanged.",
                info.field_name,
            )
            return finish(inner_result)
        # Trusted, not checked: the root queryset's rows are planned as model instances
        # (a ``values()`` root is not refused before ``apply_to``).
        root_queryset = cast("models.QuerySet[models.Model]", inner_result)
        return finish(self.apply_to(resolved.origin, resolved.model, root_queryset, info))

    def _needs_sync_boundary(self, result: object, info: "GraphQLResolveInfo[object]") -> bool:
        """Whether ``_optimize(result, info)`` would build a plan and so must leave the loop.

        Reads the same steps ``_optimize`` takes before planning - the adapter
        unwrap, the ``Manager`` coercion, the evaluated-queryset pass-through and
        the return-type resolution - then asks ``_builds_plan``. Reading the
        coerced ``Manager`` here never fetches a row: ``.all()`` builds a fresh
        unevaluated queryset.

        Building a plan runs consumer code: the walker applies each planned
        relation target's ``get_queryset`` to its prefetch child
        (``walker.py::_build_child_queryset``), and a hook may read the database,
        which Django refuses on the event-loop thread. So a plan the walker must
        build is built, applied and published in ONE sync boundary off the loop;
        a plan already cached (or memoized for this execution) is applied on the
        loop, because applying a plan runs no consumer code. A plan that embeds a
        hook result is never cached, so every request that plans one hops.
        Reconciling a memoized plan can run a hook too: a consumer ``Prefetch`` on
        a path whose target type declares ``get_queryset`` is sealed through that
        hook (``plans.py::diff_plan_for_queryset``), so such a reuse hops as well
        (``_builds_plan``).
        """
        inner_result, _ = unwrap_async_queryset_adapter(result)
        normalized = normalize_query_source(inner_result)
        if normalized[1] is False or normalized[0]._result_cache is not None:
            return False
        resolved = _resolve_model_from_return_type(info)
        return resolved is not None and self._builds_plan(
            info,
            resolved.model,
            resolved.origin,
            normalized[0],
        )

    def _builds_plan(
        self,
        info: "GraphQLResolveInfo[object]",
        target_model: type[models.Model],
        origin: "type[DjangoType] | None",
        queryset: "models.QuerySet[models.Model, object]",
    ) -> bool:
        """Whether ``apply_to`` would run the walker for ``queryset`` rather than skip or reuse a plan.

        Mirrors ``apply_to``'s two pass-throughs (no root field nodes, a combined
        queryset), which plan nothing, then ``_get_or_build_plan``'s two lookups
        (the cross-request cache, then the execution memo), which reuse a plan.
        The remaining case runs the walker and so consumer hooks; so does reusing a
        plan whose reconciliation seals a consumer ``Prefetch`` of ``queryset``
        through its target type's hook (``plans.py::seals_consumer_prefetch``).
        """
        if not info.field_nodes or queryset.query.combinator:
            return False
        cache_key = self._build_cache_key(info, target_model, origin)
        reused = self._plan_cache.get(cache_key)
        if reused is None:
            exec_memo = execution_plan_memo()
            if exec_memo is None:
                return True
            reused = exec_memo.get(cache_key)
            if reused is None:
                return True
        return seals_consumer_prefetch(reused, queryset)

    def apply_to(
        self,
        target_type: "type[DjangoType] | None",
        target_model: type[models.Model],
        queryset: "models.QuerySet[_M]",
        info: "GraphQLResolveInfo[object]",
        *,
        selection_extractor: SelectionExtractor = _root_child_selections,
    ) -> "models.QuerySet[_M]":
        """Build and apply the plan to ``queryset`` given ``target_type`` / ``target_model``.

        The plan-build-and-apply tail ``_optimize`` and ``apply_connection_optimization``
        share (spec-030 Decision 11). Takes the node type / model **directly** rather than
        inferring them from ``info.return_type`` - the connection field's root return
        type is the connection type, not the node type, so the inference the
        middleware path uses would resolve the wrong model.

        Steps:

        1. Build (or fetch from cache) an ``OptimizationPlan`` via
           ``_get_or_build_plan`` (passing ``target_type`` as ``origin`` so
           plans cache-separate by node type exactly as middleware plans do).
        2. Reconcile a non-empty plan against the consumer's existing queryset
           optimizations (``diff_plan_for_queryset``): a consumer ``Prefetch``
           carrying a queryset keeps the rows of its path, so the planned JOIN
           or FK-id elision there and every planned prefetch it wins leave the
           plan with their resolver keys, and on a target whose type declares
           ``get_queryset`` the consumer's queryset is sealed through the hook
           (with ``info``) in place of the planned ``Prefetch``.
        3. Publish the reconciled plan + strictness sentinels via
           ``_publish_plan_to_context``, so a relation the plan no longer loads
           is never published as optimizer-scoped.
        4. Apply the plan to ``queryset``.

        Returns ``queryset`` unchanged when there are no root field nodes, when
        ``queryset`` is combined (``union`` / ``intersection`` / ``difference``),
        or when the plan is empty. Django refuses ``only`` / ``select_related`` /
        ``prefetch_related`` on a combined queryset with ``NotSupportedError``, so
        a combined root runs unplanned and publishes no plan: a relation it
        selects resolves per row and reaches ``_check_n1``, so
        ``strictness="raise"`` raises ``OptimizerError`` for it.
        """
        if not info.field_nodes:
            return queryset
        if queryset.query.combinator:
            logger.debug(
                "Optimizer: %s returned a combined (%s) queryset; passing it through unplanned.",
                info.field_name,
                queryset.query.combinator,
            )
            return queryset

        # The selection-tree walker expects the children of the root field, so we build
        # the Strawberry-shaped selection list from ``field_nodes`` through
        # ``ast_to_converted_selections``: Strawberry's ``convert_selections``, stamped
        # with the Python names the walker resolves selections by.
        #
        # Deferred behind a thunk: the conversion + extraction allocate a
        # per-node ``SelectedField`` tree (with ``convert_arguments`` /
        # ``convert_directives``), yet on a plan-cache HIT - the steady-state
        # production path - that list is used for nothing. ``_get_or_build_plan``
        # invokes the thunk ONLY when it actually has to build a plan, so a cache
        # hit never pays the conversion.
        def _node_selections() -> "Sequence[ConvertedSelection]":
            selections = ast_to_converted_selections(info, info.field_nodes)
            return selection_extractor(selections, info)

        plan = self._get_or_build_plan(
            _node_selections,
            target_model,
            info,
            target_type,
        )
        # Queryset diffing: reconcile against consumer queryset optimizations BEFORE
        # publishing sentinels. Consumer-wins drops must strip coupled
        # ``planned_resolver_keys`` / FK-id elisions (via
        # ``select_path_resolver_keys`` / ``prefetch_path_resolver_keys``)
        # before ``_publish_plan_to_context``:
        # a published key reads as optimizer-scoped, so the resolver would skip
        # the target type's ``get_queryset`` on rows the consumer's own
        # ``Prefetch`` loaded and ``_check_n1`` would stay silent for them.
        # Returns a fresh plan and (when an upgrade was applied) a
        # rewritten queryset; the cached plan is never mutated.
        if not plan.is_empty:
            plan, queryset = diff_plan_for_queryset(plan, queryset, info=info)
        self._publish_plan_to_context(plan, info)
        if plan.is_empty:
            return queryset
        return plan.apply(queryset)

    def _get_or_build_plan(
        self,
        selections: "Sequence[ConvertedSelection] | Callable[[], Sequence[ConvertedSelection]]",
        target_model: type[models.Model],
        info: "GraphQLResolveInfo[object]",
        origin: "type[DjangoType] | None",
    ) -> "OptimizationPlan":
        """Return the cached plan for ``(info, target_model, origin)`` or build a new one.

        Plan cache: hits increment ``_cache_hits`` and refresh
        recency; misses run the walker, evict the least-recently-used quarter
        when full, insert iff the plan is ``cacheable``, and increment
        ``_cache_misses``.

        ``selections`` is either the converted selection list or a zero-arg
        callable that produces it. The callable form lets the caller defer the
        AST -> converted-selection conversion until a build is actually needed,
        so a cache hit never pays for it; it is invoked at most once, only on the
        build path. Direct/test callers may still pass a plain list.

        A second, per-execution memo (the execution frame's ``plans``) sits
        between the cross-request cache and the walker for ``cacheable = False``
        plans: those
        never enter ``_plan_cache``, so a nested fallback connection pipeline that
        calls this once per parent row (identical cache key each time) would
        otherwise rebuild the same plan for every parent. An intra-execution memo
        hit reuses that plan and does NOT touch the ``_cache_hits`` /
        ``_cache_misses`` counters - those stay a report on the cross-request
        instance cache alone (``cache_info``); the miss counter therefore counts
        actual walker builds, one per distinct plan per execution.

        ``origin`` carries the resolver's actual Strawberry return type
        so primary-return and secondary-return resolvers on the same
        model do not share a cached plan. The extension's ``_plan_cache``
        is root-only - this helper is the sole insertion site, so
        ``origin`` always receives the concrete root origin in
        production; ``None`` is reserved for direct/test-only callers
        that deliberately build a plan without an origin.
        """
        cache_key = self._build_cache_key(info, target_model, origin)
        cached_plan = self._plan_cache.get(cache_key)
        if cached_plan is not None:
            # ``move_to_end`` is the LRU promotion. Guard the rare race where a
            # concurrent request's eviction sweep drops this key between the
            # ``get`` above and here (one extension instance is shared across an
            # ASGI/threaded execution). A lost promotion is harmless - the plan
            # we already hold is still the correct, cacheable plan. The
            # ``suppress`` context-manager overhead is once-per-request
            # (root-only cache), not per-row, so it stays off the row-scaled
            # hot path.
            with suppress(KeyError):
                self._plan_cache.move_to_end(cache_key)
            self._cache_hits += 1
            return cached_plan
        # Per-execution reuse of an uncacheable plan already built this execution
        # (the nested-fallback per-parent-row case). ``None`` outside an
        # ``on_execute`` lifecycle, so direct/test callers skip this entirely.
        exec_memo = execution_plan_memo()
        if exec_memo is not None:
            memoized_plan = exec_memo.get(cache_key)
            if memoized_plan is not None:
                return memoized_plan
        # Both caches missed: resolve the selections now (calling the thunk if the
        # caller deferred conversion) and run the walker.
        resolved_selections = selections() if callable(selections) else selections
        plan = plan_optimizations(resolved_selections, target_model, info=info, source_type=origin)
        if plan.cacheable and len(self._plan_cache) >= _MAX_PLAN_CACHE_SIZE:
            # LRU eviction: drop the least-recently-used quarter at once to
            # amortise eviction cost across many subsequent inserts. Cache hits
            # move entries to the most-recent end above, so hot plans survive a
            # sweep even when they were inserted early.
            to_remove = max(1, _MAX_PLAN_CACHE_SIZE // 4)
            for _ in range(min(to_remove, len(self._plan_cache))):
                # One extension instance is shared across a threaded / ASGI
                # execution; another request's eviction sweep can drain the
                # cache between the length read above and this pop, exactly
                # like the concurrent-eviction races the hit path and the
                # document-key cache guard with ``suppress``. A lost eviction
                # only costs a stale entry, so the sweep absorbs the KeyError.
                with suppress(KeyError):
                    _ = self._plan_cache.popitem(last=False)
        if plan.cacheable:
            self._plan_cache[cache_key] = plan
        elif exec_memo is not None:
            # Uncacheable across requests, but reusable within THIS execution: a
            # nested fallback connection re-entering per parent row gets the plan
            # (and its already-built child queryset) back instead of re-walking.
            exec_memo[cache_key] = plan
        self._cache_misses += 1
        return plan

    def _publish_plan_to_context(
        self,
        plan: "OptimizationPlan",
        info: "GraphQLResolveInfo[object]",
    ) -> None:
        """Stash the plan and (when strictness is active) the strictness sentinels on ``info.context``.

        Plan introspection: the stash lets consumers and tests inspect the
        optimizer's decisions.  Strictness: when ``strictness != "off"``, also
        stash the planned-resolver sentinel set, the lookup paths, and
        the strictness mode so per-relation resolvers can detect
        unplanned lazy loads.
        """
        # UNION the correctness sentinels into any existing frozenset stash
        # rather than overwriting (spec-033 Decision 8). Nested FALLBACK
        # connection pipelines are real optimizer runs that re-enter this
        # publish per parent; they must NOT destroy the parent plan's
        # planned / FK-id-elision / lookup-path sets (especially under
        # ``"warn"``, where execution continues after the nested connection
        # returns). Resolver keys and FK-id-elision keys embed runtime paths, so
        # parent and nested-connection plans coexist without collision.
        # ``DST_OPTIMIZER_PLAN`` stays LAST-WINS introspection data (not a
        # correctness sentinel - do not union it).
        context = read_attr(info, "context")
        stash_for_optimizer(context, DST_OPTIMIZER_PLAN, plan)
        fk_id_elisions = require(plan.finalized_fk_id_elisions, is_set_or_frozenset)
        self._stash_union(context, DST_OPTIMIZER_FK_ID_ELISIONS, fk_id_elisions)
        planned_resolver_keys = require(plan.finalized_planned_resolver_keys, is_set_or_frozenset)
        # Published on EVERY execution, and to the execution frame rather than
        # the request context: the generated relation resolvers' visibility
        # attribution is live under the default strictness and must also survive
        # an execution that carries no ``context_value`` at all.
        publish_scoped_relations(planned_resolver_keys)
        # Likewise frame-published on every execution: the bounds each planned
        # window was fetched under, and the vocabulary a keyset window mints
        # under, are correctness inputs of the relation-connection resolver,
        # not strictness sentinels.
        publish_planned_windows(plan.planned_windows)
        if self.strictness != "off":
            plan_lookup_paths = require(plan.finalized_lookup_paths, is_set_or_frozenset)
            self._stash_union(context, DST_OPTIMIZER_PLANNED, planned_resolver_keys)
            self._stash_union(context, DST_OPTIMIZER_LOOKUP_PATHS, plan_lookup_paths)
            stash_for_optimizer(context, DST_OPTIMIZER_STRICTNESS, self.strictness)

    @staticmethod
    def _stash_union(context: object, key: str, new: "AbstractSet[object]") -> None:
        """Stash ``new`` unioned with any existing frozenset under ``key``.

        Reads the current stash via the read-side ``get_context_value`` helper
        and unions it with ``new`` when the existing value is a ``frozenset`` /
        ``set``; otherwise stashes ``new`` alone (defensive: a non-set existing
        value, the empty/absent case, matches the file's defensive-coerce
        stance). This is the foundation that lets a nested fallback connection
        pipeline's publish coexist with the parent's planned set rather than
        overwriting it (spec-033 Decision 8).
        """
        existing = optimizer_value(context, key)
        if is_set_or_frozenset(existing):
            # Subset early-out: a nested fallback connection re-publishes the
            # SAME plan once per parent row, so after the first row ``new`` is
            # already contained in the stash. Skipping the union avoids
            # reallocating a growing frozenset per row - membership is
            # observably identical either way.
            if new <= existing:
                return
            merged = existing | new
        else:
            merged = new
        stash_for_optimizer(context, key, merged)

    @staticmethod
    def check_schema(schema: object) -> list[str]:
        """Audit schema-reachable types for unoptimized relations.

        Walks only the ``DjangoType``s reachable from the schema's root
        types (not the entire registry) and checks each **exposed**
        relation field (i.e., present in its registered definition's
        field map, not hidden by ``Meta.fields``/``Meta.exclude`` or
        ``OptimizerHint.SKIP``). Returns a list of warning strings for
        relations whose target model has no registered ``DjangoType``.

        Always returns warnings - never raises. The caller decides
        whether to raise based on the extension's ``strictness``.
        """
        reachable = _collect_schema_reachable_types(schema)
        # Dedupe (source_model, field_name) so multi-type models do not
        # double-warn: registry.iter_types() yields one entry per registered
        # type after spec-018, so a model with multiple types whose
        # field maps overlap on the same unregistered-target relation would
        # otherwise produce one identical warning per registered type. The
        # dedupe is a multi-type artifact, not generic defensiveness - every
        # reachable type is still audited (we cannot skip secondaries, since
        # a secondary may expose a relation the primary hides).
        seen: set[tuple[type[models.Model], str]] = set()
        warnings: list[str] = []
        for _model, type_cls in registry.iter_types():
            if type_cls not in reachable:
                continue
            definition = registry.get_definition(type_cls)
            if definition is None:
                continue
            field_map = definition.field_map
            hints = definition.optimizer_hints or {}
            for field_name, meta in field_map.items():
                if not meta.is_relation:
                    continue
                # Skip fields opted out via OptimizerHint.SKIP.
                if hint_is_skip(hints.get(field_name)):
                    continue
                if meta.related_model is not None and registry.get(meta.related_model) is None:
                    key = (_model, field_name)
                    if key in seen:
                        continue
                    seen.add(key)
                    warnings.append(
                        f"{introspection.name(type_cls)} ({introspection.name(_model)}.{field_name}) "
                        "has no registered target DjangoType",
                    )
        return warnings

    @staticmethod
    def _build_cache_key(
        info: "GraphQLResolveInfo[object]",
        target_model: type[models.Model],
        origin: "type[DjangoType] | None" = None,
    ) -> "PlanCacheKey":
        """Build the plan-cache key from resolver info, target model, and origin type.

        Key components:
        1. The selected operation's printed AST plus the printed definitions
           of any named fragments reachable from it.  ``print_ast(operation)``
           includes the operation name and its own selection set only, so
           reachable fragment definitions are appended to keep same-shaped
           operation bodies with different fragment bodies from sharing a
           plan.  Multi-operation documents (``query A {...} query B {...}``)
           still never collide - using the raw source body would, because
           ``loc.source.body`` is the entire document.  We store the printed
           string (not its ``hash``) to eliminate the rare-but-real chance of
           two distinct document shapes sharing a 64-bit hash and silently
           sharing a cached plan.
        2. Frozenset of ``(var_name, var_value)`` for the variables
           referenced in ``@skip``/``@include`` directives and in
           the arguments the schema publishes ``first``/``last``/``before``/
           ``after`` under, on non-root
           field nodes (nested pagination values are baked into windowed
           prefetch plans, so they must key the cache; root
           pagination variables stay out -- root slicing is post-plan).
        3. The target Django model class (different root fields in the
           same operation can return different models).
        4. The root response path, so multiple root fields returning the
           same model do not share a plan within one operation.
        5. The resolver's origin Strawberry type so primary-return and
           secondary-return resolvers for the same model do not share a
           cached plan. Direct/test-only callers may pass ``None``.
        6. The operation's effective connection cap
           (``utils/connections.py::resolve_relay_max_results``: the schema's
           ``relay_max_results`` under the operation's resource-policy
           ``max_page_size``). A planned nested window bakes it, and a policy
           a plain ``strawberry.Schema`` builds per operation can change it
           between two operations on one schema.
        7. The executing schema's token (``_SchemaCacheRecord.token``), so one
           optimizer instance installed on several schemas keeps each schema's
           plans apart: a plan reads the schema's published names and type
           map as well as its caps. Two schemas with identical settings do not
           share a plan either; a second operation on the same schema does.
        """
        operation = info.operation
        fragments = info.fragments or {}
        # Memoize the operation-constant key parts per execution: the rendered
        # document key, the resolved ``(name, value)`` variable frozenset, the
        # effective connection cap and the schema's token.
        # Many root resolvers in one operation share the same operation node,
        # and a nested fallback connection pipeline calls this once per parent
        # row - both the document rendering and the variable resolution are
        # constants for the operation (``info.variable_values`` is fixed per
        # execution), so one dict hit replaces the AST work and the per-row
        # frozenset rebuild.  On a memo miss the document-derived halves come
        # from the cross-request ``_doc_cache_entry`` LRU (so a hot query pays
        # neither ``print_ast`` nor the variable-name AST walk after first
        # sight); only the value resolution runs per execution.  The memo lives
        # on the execution frame ``on_execute`` opens; if the extension is
        # invoked outside an ``on_execute`` lifecycle (some test fixtures call
        # ``_build_cache_key`` directly), fall back to recomputing -- spec-033
        # Decision 7.
        memo = cache_key_parts_memo()
        parts = memo.get(id(operation)) if memo is not None else None
        if parts is None:
            schema_record = _schema_cache_record(info.schema)
            doc_key, relevant_var_names = _doc_cache_entry(
                operation,
                fragments,
                schema_record.pagination_wire_names,
            )
            variable_values: Mapping[str, object] = dict[str, object](get_variable_values(info))
            # The name-keyed pagination collector deliberately over-collects, so
            # any GraphQL input shape (including an arbitrary custom-scalar
            # result) can reach this frozenset through a same-named argument on a
            # non-connection field. Normalize every value at the cache boundary.
            relevant_vars = frozenset(
                (k, _hashable_variable_value(variable_values[k]))
                for k in relevant_var_names
                if k in variable_values
            )
            parts = (
                doc_key,
                relevant_vars,
                resolve_relay_max_results(info, None),
                schema_record.token,
            )
            if memo is not None:
                memo[id(operation)] = parts
        doc_key, relevant_vars, connection_cap, schema_token = parts
        return (
            doc_key,
            relevant_vars,
            target_model,
            runtime_path_from_info(info),
            origin,
            connection_cap,
            schema_token,
        )


def apply_connection_optimization(
    target_type: "type[DjangoType]",
    queryset: "models.QuerySet[_M]",
    info: "EitherInfo",
    *,
    selection_extractor: SelectionExtractor = _connection_node_child_selections,
) -> "models.QuerySet[_M]":
    """Apply the optimizer plan to a connection field's pre-slice queryset.

    The connection field's own optimizer cooperation point (spec-030 Decision 11), also
    reused by the mutation re-fetch (spec-036 Decision 9). Strawberry's
    ``ConnectionExtension`` returns a connection object, so the schema middleware
    (``DjangoOptimizerExtension.resolve``) never sees the pre-slice queryset and
    cannot optimize it; the connection resolver calls this helper as the last
    pipeline step before handing the queryset to ``ConnectionExtension`` for
    slicing.

    Resolves ``target_model`` from ``target_type``'s registered definition
    (NOT from ``info.return_type``, which is the connection type) and delegates
    to ``DjangoOptimizerExtension.apply_to``. The active extension instance is
    discovered from the execution frame ``on_execute`` opens
    (``_context.py::active_optimizer``) so the connection field shares the
    instance-bound plan cache. When no optimizer extension is running this
    execution - no frame - the helper
    short-circuits and returns the queryset unoptimized; the connection field
    does NOT fabricate a throwaway
    optimizer to self-optimize. This keeps the connection consistent with the
    rest of the schema: the middleware path only optimizes when the extension is
    installed, and connection fields follow the same opt-in contract.

    ``selection_extractor`` defaults to the connection ``edges { node { ... } }``
    navigator; a caller whose response selection nests the node type under a
    different slot passes its own (the mutation re-fetch passes a
    ``<payload>.node`` / ``<payload>.result`` extractor - spec-036 Decision 9), so
    the walker sees the same child-selection list a list field over the node type
    would. ``apply_to`` already accepts the extractor; this helper just forwards
    it instead of hardcoding the connection shape.

    Returns ``queryset`` unchanged when ``target_type`` has no registered
    model (nothing to plan), when no optimizer extension is installed, or when
    ``apply_to`` passes a combined queryset through unplanned.
    """
    target_model = registry.model_for_type(target_type)
    if target_model is None:
        return queryset
    optimizer = active_optimizer()
    if optimizer is None:
        return queryset
    # The connection resolver receives Strawberry's wrapped ``Info``; the plan
    # machinery (``_build_cache_key`` / ``convert_selections`` / the
    # ``info.context`` stash) expects the raw graphql-core ``GraphQLResolveInfo``
    # the middleware path uses. ``Info._raw_info`` is that object; the
    # ``getattr`` fallback keeps the helper usable when a caller already passes
    # a raw info (e.g. a direct test).
    return optimizer.apply_to(
        target_type,
        target_model,
        queryset,
        _raw_resolve_info(info),
        selection_extractor=selection_extractor,
    )


def _raw_resolve_info(info: "EitherInfo") -> "GraphQLResolveInfo[object]":
    """Return the graphql-core info behind ``info`` (a Strawberry ``Info`` or a raw one)."""
    # A Strawberry ``Info`` carries its raw info at ``_raw_info``; a raw info is itself.
    return cast("GraphQLResolveInfo[object]", getattr(info, "_raw_info", info))


async def apply_connection_optimization_async(
    target_type: "type[DjangoType]",
    queryset: "models.QuerySet[_M]",
    info: "EitherInfo",
) -> "models.QuerySet[_M]":
    """``apply_connection_optimization`` for the asynchronous connection pipeline.

    A plan the walker must build runs the planned targets' ``get_queryset`` hooks,
    so it is built in ONE sync boundary off the event loop
    (``DjangoOptimizerExtension._needs_sync_boundary`` states the rule); a reusable plan
    is applied here.
    """
    target_model = registry.model_for_type(target_type)
    optimizer = active_optimizer()
    if (
        target_model is not None
        and optimizer is not None
        and optimizer._builds_plan(_raw_resolve_info(info), target_model, target_type, queryset)
    ):
        return await run_in_one_sync_boundary(
            apply_connection_optimization,
            target_type,
            queryset,
            info,
        )
    return apply_connection_optimization(target_type, queryset, info)
