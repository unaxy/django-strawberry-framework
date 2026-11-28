"""Selection-tree traversal substrate - the AST and converted-selection adapters.

The optimizer reads GraphQL selections in two shapes: graphql-core **AST** nodes
(``optimizer/extension.py`` - plan-cache key construction, cache-relevant
variable extraction) and Strawberry's **converted**
selection objects (``optimizer/walker.py`` + the connection optimizer seam -
plan building, nested connection windows). Both shapes repeat the same
concepts: child-selection iteration, fragment descent, ``@skip`` / ``@include``
directive handling, response-key preservation, and ``edges { node { ... } }``
unwrapping. The plan cache and nested-connection windows depend on those rules
being aligned across the two shapes; a directive or fragment fix landing on one
traversal but not the other produces wrong cached plans, missed nested
prefetches, false strictness warnings, or extra ``COUNT`` work.

This module is the single home for both, deliberately split into two explicit
adapters rather than one over-generic polymorphic walker: the adapters stay
explicit, while the recursion and directive/fragment policies are shared so the
contracts cannot drift:

- **AST adapter** (``ast_child_selections`` / ``resolve_unvisited_fragment`` /
  ``directive_variable_names``) - operates on graphql-core AST nodes for
  ``optimizer/extension.py``. ``resolve_unvisited_fragment`` keys its visits
  on ``(name, depth)`` for the depth-sensitive cache-relevant-variable walk.
- **Converted-selection adapter** (``should_include`` / ``is_fragment`` /
  ``response_key`` / ``response_keys`` / ``included_field_selections`` /
  ``named_children`` / ``with_runtime_prefix`` /
  ``node_children_with_runtime_prefix`` / ``connection_node_children`` /
  ``direct_child_selected``) - operates on Strawberry converted selections
  (and the ``SimpleNamespace`` shapes the walker synthesizes). The fragment,
  include and response-key rules for converted selections live here and
  nowhere else, so none can drift.

Cycle-safe: ``walker.py`` and ``extension.py`` both import from here; this
module imports neither. Beyond graphql-core and the stdlib it reaches
``utils/typing.py`` for the published-name reads the converter stamps
(``published_python_name``), and ``_context.py`` for the execution frame its
converted-selection memo lives on - both below it in the dependency order.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from graphql import GraphQLError, GraphQLInterfaceType, GraphQLObjectType, get_named_type
from graphql.execution.values import VariableValues, get_argument_values
from graphql.language.ast import (
    DirectiveNode,
    FieldNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    VariableNode,
)

# basedpyright: Strawberry annotates both helpers' ``info`` as graphql-core's bare generic
# ``GraphQLResolveInfo``, so each reads as partially Unknown
from strawberry.types.nodes import (
    convert_selections,  # pyright: ignore[reportUnknownVariableType]
    get_variable_values,  # pyright: ignore[reportUnknownVariableType]
)

from django_strawberry_framework.utils._narrowing import (
    is_dict,
    is_str,
    read_attr,
    require_instance,
)
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_type_of,
    published_python_name,
)

from ._context import converted_selections_memo

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from typing import TypeAlias

    from graphql.language.ast import (
        FragmentDefinitionNode,
        Node,
        SelectionNode,
        SelectionSetNode,
    )
    from graphql.type.definition import GraphQLField, GraphQLNamedType, GraphQLResolveInfo
    from strawberry.types.nodes import SelectedField, Selection

    from ._context import ConvertedMemoKey

    #: One converted selection as this adapter reads it: a Strawberry
    #: ``SelectedField`` / ``FragmentSpread`` / ``InlineFragment`` or a
    #: ``SimpleNamespace`` clone the walker synthesizes in their shape.
    ConvertedSelection: TypeAlias = Selection | SimpleNamespace
    #: A converted FIELD selection (never a fragment): Strawberry's
    #: ``SelectedField`` or the walker's field-shaped ``SimpleNamespace`` clone.
    FieldSelection: TypeAlias = SelectedField | SimpleNamespace
    #: A ``resolve_unvisited_fragment`` visit key: ``(fragment name, spread-site depth)``.
    FragmentVisitKey: TypeAlias = tuple[str, int]

# ---------------------------------------------------------------------------
# AST -> converted-selection adapter - Strawberry's ``convert_selections``, stamped
# ---------------------------------------------------------------------------

#: The marker a converted field selection carries its arguments under, keyed by
#: the Python name each was declared with and coerced by graphql-core.
#: ``ast_to_converted_selections`` writes it beside Strawberry's own
#: ``arguments`` (which keep the wire names and the raw literal tokens),
#: ``with_runtime_prefix`` and the walker's merge copy it, and
#: ``python_arguments`` reads it.
PYTHON_ARGUMENTS_ATTR = "_optimizer_python_arguments"

#: The marker a converted field selection carries the Python name of the field
#: it selects under: the name the schema published the field from
#: (``utils/typing.py::published_python_name``), whatever wire name the
#: ``NameConverter`` gave it. ``ast_to_converted_selections`` writes it,
#: ``with_runtime_prefix`` and the walker's merge copy it, and
#: ``selection_python_name`` reads it.
PYTHON_NAME_ATTR = "_optimizer_python_name"


def selection_python_name(selection: object) -> str | None:
    """Return the Python name of the field a converted field selection selects.

    The name ``ast_to_converted_selections`` stamped on the selection: the
    declaration the executing schema published the selected field from, so a
    reader matches a selection to a model field, a synthesized connection or a
    connection's own ``edges`` / ``node`` / ``page_info`` / ``total_count`` /
    ``has_next_page`` by the name it was declared under, never by the wire name
    a ``NameConverter`` gave it. ``None`` for a selection the converter could not
    resolve to a field of the schema (a meta field such as ``__typename``).
    """
    name = read_attr(selection, PYTHON_NAME_ATTR, None)
    return name if is_str(name) else None


def python_arguments(selection: object) -> Mapping[str, object]:
    """Return a converted field selection's arguments by Python name, coerced.

    The map ``ast_to_converted_selections`` stamped on the selection: the value
    graphql-core coerced for each argument the field declares (a literal and a
    variable alike), keyed by the Python name the schema published it from, so
    no reader depends on the names a ``NameConverter`` gave the arguments on the
    wire. Empty for a selection the converter could not resolve to a field of
    the schema.
    """
    arguments = read_attr(selection, PYTHON_ARGUMENTS_ATTR, None)
    if not is_dict(arguments):
        return {}
    return {name: value for name, value in arguments.items() if is_str(name)}


def _coerced_python_arguments(
    field_def: GraphQLField,
    node: FieldNode,
    variable_values: dict[str, object],
) -> dict[str, object]:
    """Coerce ``node``'s arguments against ``field_def``; key each by its Python name.

    ``graphql.execution.values.get_argument_values`` is the executor's own
    coercion (literal tokens to values, variables and defaults resolved) and keys
    its answer by the published name; ``published_python_name`` reads the
    declaration each published argument was built from back off the schema. It
    reads only a ``VariableValues``' ``coerced`` dict, which is what Strawberry's
    resolve info carries (``get_variable_values``); ``sources`` serves
    ``replace_variables`` alone, so it is left empty.

    Empty when the arguments do not coerce: the executor raises that same error as
    the field's own error when it resolves the field, and a field a ``@skip`` /
    ``@include`` leaves out never resolves, so a valid request (a nullable
    variable that is ``null`` on a skipped field's non-null argument) runs, and
    the selection is planned with no arguments rather than failing its root.
    """
    try:
        coerced = get_argument_values(field_def, node, VariableValues({}, variable_values))
    except GraphQLError:
        return {}
    by_python_name: dict[str, object] = {}
    for wire_name, argument in field_def.args.items():
        out_name = argument.out_name or wire_name
        python_name = published_python_name(argument)
        if python_name is not None and out_name in coerced:
            by_python_name[python_name] = coerced[out_name]
    return by_python_name


def _published_field(parent: GraphQLNamedType | None, name: str) -> GraphQLField | None:
    """Return the field ``parent`` publishes under ``name``, ``None`` when it has no such field.

    Only object and interface types carry fields; a meta field such as
    ``__typename`` is in no type's map.
    """
    if isinstance(parent, (GraphQLObjectType, GraphQLInterfaceType)):
        return graphql_fields(parent).get(name)
    return None


# Per-execution memo for the converted-selection tree, keyed by the field
# nodes' ids. ``connection.py::_connection_field_requested`` runs the full AST
# -> ``SelectedField`` conversion on every connection resolution, and a nested
# FALLBACK connection resolves once per parent row with a fresh Strawberry
# ``Info`` each time - but graphql-core's executor caches collected sub-fields
# per execution (``ExecutionContext._subfields_cache``), so every row's
# ``info.field_nodes`` is the SAME node group, and the conversion depends only
# on per-execution constants (``info.fragments`` / ``info.variable_values``).
# Reusing the first row's converted list collapses N per-row conversions to
# one. The key mirrors graphql-core's own subfields-cache shape (the ids of the
# individual field nodes, NOT the id of the wrapping list, which may be rebuilt
# or reused): AST node ids are stable for the memo's whole lifetime because the
# document is owned by the execution context that spans the same ``on_execute``
# lifecycle. The memo belongs to the execution frame
# ``DjangoOptimizerExtension.on_execute`` opens
# (``_context.py::_ExecutionFrame``), so it ends when that execution does and a
# task that copied the binding reads nothing. ``None`` outside a managed
# execution disables the memo, so direct / test callers see unchanged behavior.
# Consumers treat the converted list as read-only (the walker clones before
# mutating; Strawberry's ``selected_fields`` readers only iterate), so sharing
# one list across rows is safe.


def ast_to_converted_selections(
    info: GraphQLResolveInfo[object],
    field_nodes: Sequence[FieldNode],
) -> list[Selection]:
    """Convert ``field_nodes`` with Strawberry's ``convert_selections``, stamped by Python name.

    The list is Strawberry's own - its ``SelectedField`` / ``FragmentSpread`` /
    ``InlineFragment`` dataclasses, a typeless inline fragment (``... { f }``) carrying
    ``type_condition=None`` - the shape ``Info.selected_fields`` holds. ``_stamp`` then
    walks it beside the AST it came from, tracking the GraphQL type each selection set
    is read on (the resolver's ``parent_type`` at the top, a field's named type below
    it, a fragment's type condition inside it), and gives each field selection the
    schema publishes the Python name of its field (``PYTHON_NAME_ATTR``, read through
    ``selection_python_name``) and its arguments by Python name, coerced by graphql-core
    (``PYTHON_ARGUMENTS_ATTR``, read through ``python_arguments``). Both markers sit
    beside the dataclass fields, so what Strawberry's own readers see is unchanged.

    Memoized per execution on the execution frame (see the comment above):
    within one ``on_execute`` lifecycle the same field-node group converts once,
    so the per-parent-row ``connection.py::_connection_field_requested`` calls
    of a fallback connection pipeline reuse the first row's list instead of
    re-running the conversion for every parent.
    """
    memo = converted_selections_memo()
    memo_key: ConvertedMemoKey | None = None
    if memo is not None:
        # One-node groups are the overwhelmingly common shape; key on the single
        # node's id directly to skip the tuple build (graphql-core's own
        # subfields cache makes the same trade).
        memo_key = id(field_nodes[0]) if len(field_nodes) == 1 else tuple(map(id, field_nodes))
        converted = memo.get(memo_key)
        if converted is not None:
            return converted

    converted = convert_selections(info, field_nodes)
    _stamp(info, converted, field_nodes, info.parent_type)
    if memo is not None and memo_key is not None:
        memo[memo_key] = converted
    return converted


def _stamp(
    info: GraphQLResolveInfo[object],
    selections: Iterable[Selection],
    nodes: Iterable[SelectionNode],
    read_on: GraphQLNamedType | None,
) -> None:
    """Mark each field selection under ``nodes`` with its Python name and arguments.

    ``selections`` is ``nodes`` converted, one for one in order: ``convert_selections``
    converts a selection set member by member, and a spread's body comes from the
    same ``info.fragments`` entry. ``read_on`` is the type the selection set is read
    on, ``None`` for one the schema does not publish, where no field resolves and
    nothing is stamped. graphql-core's parser fills a selection set only with field,
    inline-fragment and fragment-spread nodes; any other ``SelectionNode`` raises
    ``TypeError``.
    """
    for selection, node in zip(selections, nodes, strict=True):
        if isinstance(node, InlineFragmentNode):
            condition = node.type_condition
            below = read_on if condition is None else info.schema.get_type(condition.name.value)
            _stamp(info, selection.selections, ast_child_selections(node), below)
        elif isinstance(node, FragmentSpreadNode):
            fragment = info.fragments[node.name.value]
            below = info.schema.get_type(fragment.type_condition.name.value)
            _stamp(info, selection.selections, ast_child_selections(fragment), below)
        else:
            field_node = require_instance(node, FieldNode)
            field_def = _published_field(read_on, field_node.name.value)
            below = None
            if field_def is not None:
                python_name = published_python_name(field_def)
                if python_name is not None:
                    setattr(selection, PYTHON_NAME_ATTR, python_name)
                if field_def.args:
                    setattr(
                        selection,
                        PYTHON_ARGUMENTS_ATTR,
                        _coerced_python_arguments(
                            field_def,
                            field_node,
                            get_variable_values(info),
                        ),
                    )
                below = get_named_type(graphql_type_of(field_def))
            _stamp(info, selection.selections, ast_child_selections(field_node), below)


# ---------------------------------------------------------------------------
# AST adapter - graphql-core nodes (``optimizer/extension.py``)
# ---------------------------------------------------------------------------


def ast_child_selections(node: Node) -> tuple[SelectionNode, ...]:
    """Return the AST node's selection-set children as a tuple, or ``()``.

    Centralizes the ``getattr(node, "selection_set", None)`` plus
    ``selections or ()`` shape for the AST cache-key walk
    (``optimizer/extension.py::_walk_cache_relevant_vars``).
    ``FragmentSpreadNode`` has
    no ``selection_set``, so this returns ``()`` and the caller's
    per-child loop becomes a no-op.
    """
    # Every graphql-core node that has a ``selection_set`` types it as a
    # ``SelectionSetNode`` (optional on ``FieldNode``).
    selection_set: SelectionSetNode | None = getattr(node, "selection_set", None)
    if selection_set is None:
        return ()
    return tuple(selection_set.selections or ())


def resolve_unvisited_fragment(
    node: Node,
    fragments: Mapping[str, FragmentDefinitionNode],
    visited_fragments: set[FragmentVisitKey],
    *,
    depth: int,
) -> FragmentDefinitionNode | None:
    """Resolve a ``FragmentSpreadNode`` to its definition, once per visit key.

    Returns the matching ``FragmentDefinitionNode`` and marks the visit key
    so a sibling or cyclic spread in the same walk is a no-op. The visit key
    is ``(name, depth)``: the cache-relevant-variable walk must walk the same
    fragment spread at two response-path depths once per depth so nested
    pagination variables are not dropped. Returns ``None``
    when ``node`` is not a fragment spread or when the visit key is already
    present. The walk runs on a validated document, where graphql-core has
    already refused a spread of an undefined fragment. Mutates
    ``visited_fragments`` on success so callers share one cycle-detection set
    across recursive descents.
    """
    if not isinstance(node, FragmentSpreadNode):
        return None
    frag_name = node.name.value
    visit_key: FragmentVisitKey = (frag_name, depth)
    if visit_key in visited_fragments:
        return None
    visited_fragments.add(visit_key)
    return fragments[frag_name]


def directive_variable_names(node: Node) -> set[str]:
    """Return the variable names referenced in ``@skip`` / ``@include`` on ``node``.

    Only variables inside the ``if`` argument of ``@skip`` / ``@include`` affect
    the selection tree (and therefore the plan cache); every other variable is
    excluded. The single
    directive-variable extraction the AST cache-key walk shares, so the
    ``("skip", "include")`` membership and the ``VariableNode`` check live once.
    """
    names: set[str] = set()
    directives: Iterable[DirectiveNode] = getattr(node, "directives", ()) or ()
    for directive in directives:
        if directive.name.value not in ("skip", "include"):
            continue
        for arg in directive.arguments or ():
            if isinstance(arg.value, VariableNode):
                names.add(arg.value.name.value)
    return names


# ---------------------------------------------------------------------------
# Converted-selection adapter - Strawberry converted selections + the
# ``SimpleNamespace`` shapes the walker synthesizes (``optimizer/walker.py`` +
# the connection optimizer seam).
# ---------------------------------------------------------------------------


def is_fragment(selection: object) -> bool:
    """Return ``True`` if the selection is a fragment spread or inline fragment.

    Duck-typed on ``type_condition`` so it matches both Strawberry's
    ``InlineFragment`` / ``FragmentSpread`` and the ``SimpleNamespace`` fragment
    shells the walker clones - a regular field selection has no
    ``type_condition``. This is the SINGLE fragment-vs-field discriminator for
    converted selections, so no reader can drift on what counts as a fragment.
    """
    return hasattr(selection, "type_condition")


def should_include(selection: object) -> bool:
    """Evaluate ``@skip`` / ``@include`` directives on a converted selection."""
    # Strawberry's converted selections (and the walker clones copying them) carry
    # ``Directives``: directive name -> converted argument payload.
    directives: Mapping[str, Mapping[str, object]] | None = getattr(
        selection,
        "directives",
        None,
    )
    # Directive-free selections are the overwhelmingly common shape, and this
    # predicate runs once per selection per walk level; skip the two dict
    # probes when there is nothing to evaluate.
    if not directives:
        return True
    skip = directives.get("skip")
    if skip is not None:
        value = skip.get("if")
        if value is True:
            return False
    include = directives.get("include")
    if include is not None:
        value = include.get("if")
        if value is False:
            return False
    return True


def response_key(selection: FieldSelection) -> str:
    """Return the GraphQL response key for a field selection."""
    return getattr(selection, "alias", None) or selection.name


def response_keys(selection: FieldSelection) -> tuple[str, ...]:
    """Return all response keys represented by a possibly merged selection."""
    return tuple(
        getattr(selection, "_optimizer_response_keys", None) or (response_key(selection),),
    )


# TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card): add a
# tri-state fragment classifier to this converted selection inliner, but keep the default path
# byte-for-byte unconditional. Design contract: spec-035 Decision 6 (the tri-state classifier and
# its accept set) and Decision 7 (narrow, do not multi-plan). Reachability: an abstract
# (interface/union) root field never reaches the walker today - registry.model_for_type returns
# None for the abstract origin, so _optimize passes the queryset through before this inliner runs;
# the classifier therefore ships nothing until that card first builds the abstract-return
# production-entry contract (spec-035 Decision 6). Pseudocode: no classifier means INLINE-all
# for extension cache-key and connection extraction callers; a walker-supplied classifier returns
# INLINE, SKIP, or RECURSE_FRAGMENTS_ONLY. The recursion mode drops direct fields for an unknown
# composite/union condition while still re-checking nested fragments.
def included_field_selections(
    selections: Iterable[ConvertedSelection],
) -> Sequence[FieldSelection]:
    """Return included fields with fragment bodies inlined before field merging.

    Directive filtering happens on both fragment nodes and their nested field
    selections. Returning a flat field list lets alias/relation merging combine
    duplicate relation branches before generated child ``Prefetch`` querysets
    are built.

    Fast path: when no selection is a fragment and none is directive-excluded
    (the overwhelmingly common query shape), the flatten/filter loop would
    rebuild an identical list - so the input list is returned unchanged
    instead, mirroring ``walker._merge_aliased_selections``'s passthrough.
    The result may be the input list itself; callers only iterate it, so
    sharing it is safe.

    Non-``list``/``tuple`` iterables are materialized once at entry. The
    fast-path probe loop and the rebuild loop below BOTH iterate the
    collection, so a one-shot iterable (Strawberry's converter always builds
    lists, but the parameter accepts any ``Iterable`` from a direct caller)
    would be silently exhausted between them: fields before the first
    fragment, and a fragment's whole body, would vanish from the plan
    without any error. Re-iterable list/tuple inputs keep the identity
    passthrough above.
    """
    if not isinstance(selections, (list, tuple)):
        selections = list(selections)
    for selection in selections:
        if is_fragment(selection) or not should_include(selection):
            break
    else:
        # The probe loop found no fragment, so every member is a field selection.
        return cast("Sequence[FieldSelection]", selections)
    result: list[FieldSelection] = []
    for selection in selections:
        if not should_include(selection):
            continue
        if is_fragment(selection):
            # No defensive ``list(...)`` copy: the recursion only iterates the
            # child collection, so any sequence shape passes through as-is.
            result.extend(
                included_field_selections(getattr(selection, "selections", None) or []),
            )
            continue
        # ``is_fragment`` rejected it, so it is a field selection.
        result.append(cast("FieldSelection", selection))
    return result


def named_children(selection: ConvertedSelection, name: str) -> list[FieldSelection]:
    """Return included direct children selecting the field Python-named ``name``, through fragments.

    A member matches by ``selection_python_name``: the name the selected field
    was declared under, whatever wire name the schema's ``NameConverter``
    published it as. ``included_field_selections`` enters fragment wrappers and
    never a field's own sub-selections, and drops every directive-excluded member.
    """
    members: Iterable[ConvertedSelection] = getattr(selection, "selections", None) or []
    return [s for s in included_field_selections(members) if selection_python_name(s) == name]


#: Attribute naming the runtime-path prefixes a walker clone carries:
#: ``with_runtime_prefix`` and the walker's merge write it, and the walker's
#: ``_selection_runtime_prefixes`` reads it with a ``None`` default, so a
#: misspelled site would read "no prefixes" silently.
RUNTIME_PREFIXES_ATTR = "_optimizer_runtime_prefixes"


def with_runtime_prefix(
    selection: ConvertedSelection,
    runtime_prefixes: tuple[tuple[str, ...], ...],
) -> SimpleNamespace:
    """Clone a node-level selection carrying runtime prefixes for the walker.

    Fragments are descended, never marked; the ``RUNTIME_PREFIXES_ATTR``
    marker lands on field leaves only. A fragment shell carrying the prefix
    would be meaningless - prefixes belong on the field selections the walker
    eventually plans.
    """
    if is_fragment(selection):
        members: Iterable[ConvertedSelection] = getattr(selection, "selections", None) or []
        return SimpleNamespace(
            name=getattr(selection, "name", None),
            # ``is_fragment`` accepted it, so it carries a ``type_condition``.
            type_condition=read_attr(selection, "type_condition"),
            directives=getattr(selection, "directives", None) or {},
            selections=[with_runtime_prefix(child, runtime_prefixes) for child in members],
        )
    return SimpleNamespace(
        # ``is_fragment`` rejected it, so it is a field selection.
        name=cast("FieldSelection", selection).name,
        alias=getattr(selection, "alias", None),
        directives=getattr(selection, "directives", None) or {},
        arguments=getattr(selection, "arguments", None) or {},
        selections=list(getattr(selection, "selections", None) or []),
        **{
            RUNTIME_PREFIXES_ATTR: list(runtime_prefixes),
            PYTHON_NAME_ATTR: selection_python_name(selection),
            PYTHON_ARGUMENTS_ATTR: python_arguments(selection),
        },
    )


def node_children_with_runtime_prefix(
    node_selection: ConvertedSelection,
    *,
    runtime_prefixes: tuple[tuple[str, ...], ...],
) -> list[SimpleNamespace]:
    """Clone node children with a connection-aware runtime prefix."""
    members: Iterable[ConvertedSelection] = getattr(node_selection, "selections", None) or []
    return [
        with_runtime_prefix(child, runtime_prefixes) for child in members if should_include(child)
    ]


# The Python names of a Relay connection's own fields, the names Strawberry's
# ``relay.Connection`` / ``Edge`` / ``PageInfo`` and ``connection.py``'s
# ``total_count`` declare them under. Every walk below matches a selection to
# them through ``selection_python_name``, so the wire names the executing
# schema's ``NameConverter`` publishes them as never enter the match.
_EDGES = "edges"
_NODE = "node"
_PAGE_INFO = "page_info"
_TOTAL_COUNT = "total_count"
_HAS_NEXT_PAGE = "has_next_page"


def connection_node_children(
    selection: ConvertedSelection,
    *,
    runtime_prefixes: tuple[tuple[str, ...], ...],
) -> list[SimpleNamespace]:
    """Unwrap a Relay connection's ``edges { node { ... } }`` child selections.

    Single owner of the edges->node composition that accumulates response-key
    prefixes and clones node children for the walker. Shared by the root
    connection apply seam (``extension.py``) and nested-connection planning
    (``nested_planner.py``) so fragment / directive / prefix semantics cannot
    drift between those call sites. Returns an empty list when the selection
    has no ``edges { node }`` (e.g. ``pageInfo`` / ``totalCount`` only). Both
    levels match by Python name (``named_children``), so the unwrap holds under
    any wire names the schema publishes them as.
    """
    node_children: list[SimpleNamespace] = []
    for edge_selection in named_children(selection, _EDGES):
        edge_path_prefixes = tuple((*rp, response_key(edge_selection)) for rp in runtime_prefixes)
        for node_selection in named_children(edge_selection, _NODE):
            node_path_prefixes = tuple(
                (*ep, response_key(node_selection)) for ep in edge_path_prefixes
            )
            node_children.extend(
                node_children_with_runtime_prefix(
                    node_selection,
                    runtime_prefixes=node_path_prefixes,
                ),
            )
    return node_children


def direct_child_selected(selection_roots: Iterable[ConvertedSelection], name: str) -> bool:
    """Return whether the field Python-named ``name`` is a direct child, through fragments only.

    A same-named field deep inside ``edges { node { ... } }`` (a nested
    connection's ``totalCount``) does not trip the outer connection's predicate,
    and a ``totalCount @skip(if: true)`` (or a ``@skip``-ped fragment wrapping it)
    does not fire the connection ``COUNT`` (``included_field_selections``).
    """
    return any(
        selection_python_name(s) == name for s in included_field_selections(selection_roots)
    )


def connection_total_count_selected(selection: ConvertedSelection) -> bool:
    """Return whether ``selection`` (a connection field) selects ``totalCount``.

    The count field as a DIRECT child of the connection, through fragment
    wrappers only (``direct_child_selected``). The single implementation of
    the count-observability walk, so the plan-time and resolve-time halves of
    the conditional ``_dst_total_count`` contract share one walk by
    construction - and match the field by its Python name ``total_count``,
    so neither depends on the wire name the schema publishes it under.
    """
    children: Iterable[ConvertedSelection] = getattr(selection, "selections", None) or []
    return direct_child_selected(children, _TOTAL_COUNT)


def connection_page_selected(selection: ConvertedSelection) -> bool:
    """Return whether ``selection`` (a connection field) selects ``edges`` or ``pageInfo``.

    A direct edges or page-info child, through fragment wrappers
    (``named_children``), matched by Python name. Both read the page's rows, so a
    connection resolves its rows when either is selected and skips them when
    neither is. ``strawberry/relay/utils.py::should_resolve_list_connection_edges``
    asks the same question of the wire names ``edges`` / ``pageInfo`` and answers
    ``False`` under a ``NameConverter`` that spells them otherwise (``page_info``
    under ``auto_camel_case=False``), so ``connection.py::_page_requested`` asks
    this one instead.
    """
    return bool(named_children(selection, _EDGES) or named_children(selection, _PAGE_INFO))


def connection_has_next_page_selected(selection: ConvertedSelection) -> bool:
    """Return whether ``selection`` selects ``pageInfo { hasNextPage }``.

    The ``hasNextPage`` sibling of ``connection_total_count_selected``: a
    direct page-info child (through fragment wrappers, alias-merged via
    ``named_children``), then a direct has-next-page child under it. The one
    has-next-page walk, so plan time and resolve time cannot disagree on it.
    """
    return any(
        direct_child_selected(
            getattr(page_info, "selections", None) or [],
            _HAS_NEXT_PAGE,
        )
        for page_info in named_children(selection, _PAGE_INFO)
    )
