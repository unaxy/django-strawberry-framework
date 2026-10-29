"""Selection-tree traversal substrate - the AST and converted-selection adapters.

The optimizer reads GraphQL selections in two shapes: graphql-core **AST** nodes
(``optimizer/extension.py`` - plan-cache key construction, reachable-fragment
collection, cache-relevant variable extraction) and Strawberry's **converted**
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
  ``optimizer/extension.py``. ``resolve_unvisited_fragment`` accepts optional
  ``depth`` so the reachable-fragment walk (name key) and the
  cache-relevant-variable walk (``(name, depth)`` key) share one resolve
  guard.
- **Converted-selection adapter** (``should_include`` / ``is_fragment`` /
  ``response_key`` / ``response_keys`` / ``included_field_selections`` /
  ``named_children`` / ``with_runtime_prefix`` /
  ``node_children_with_runtime_prefix`` / ``connection_node_children`` /
  ``direct_child_selected``) - operates on Strawberry converted selections
  (and the ``SimpleNamespace`` shapes the walker synthesizes) for three
  consumers: ``optimizer/walker.py`` / ``nested_planner.py`` (nested
  connection windows), ``optimizer/extension.py``'s root-connection seam
  (both call ``connection_node_children`` for the ``edges { node }`` unwrap),
  and ``connection.py``'s ``totalCount`` detection (``direct_child_selected``
  only).

Cycle-safe: ``walker.py`` and ``extension.py`` both import from here; this
module imports neither. Beyond graphql-core and the stdlib it reaches
``utils/typing.py`` for the published-name reads the converter stamps
(``published_python_name``), and ``_context.py`` for the execution frame its
converted-selection memo lives on - both below it in the dependency order.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from graphql import (
    GraphQLInterfaceType,
    GraphQLObjectType,
    get_argument_values,
    get_named_type,
)
from graphql.language.ast import (
    DirectiveNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    VariableNode,
)
from strawberry.types.nodes import (
    FragmentSpread,
    InlineFragment,
    SelectedField,
    convert_arguments,
    convert_directives,
)

from django_strawberry_framework.utils._narrowing import is_dict, is_str, read_attr
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_type_of,
    inline_fragment_type_condition,
    published_python_name,
)

from ._context import converted_selections_memo

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from typing import TypeAlias

    from graphql.language.ast import (
        FieldNode,
        FragmentDefinitionNode,
        Node,
        SelectionSetNode,
    )
    from graphql.type.definition import GraphQLField, GraphQLNamedType, GraphQLResolveInfo
    from strawberry.types.info import Info
    from strawberry.types.nodes import (
        Selection,
    )

    from ._context import ConvertedMemoKey

    #: One graphql-core selection-set member: a selection set holds exactly these
    #: three node kinds.
    AstSelection: TypeAlias = FieldNode | InlineFragmentNode | FragmentSpreadNode
    #: One converted selection as this adapter reads it: a Strawberry
    #: ``SelectedField`` / ``FragmentSpread`` / ``InlineFragment`` or a
    #: ``SimpleNamespace`` clone the walker synthesizes in their shape.
    ConvertedSelection: TypeAlias = Selection | SimpleNamespace
    #: A converted FIELD selection (never a fragment): Strawberry's
    #: ``SelectedField`` or the walker's field-shaped ``SimpleNamespace`` clone.
    FieldSelection: TypeAlias = SelectedField | SimpleNamespace
    #: A ``resolve_unvisited_fragment`` visit key: the fragment name, or
    #: ``(name, depth)`` for the depth-sensitive walk.
    FragmentVisitKey: TypeAlias = str | tuple[str, int]

# ---------------------------------------------------------------------------
# AST -> converted-selection adapter - the package-owned ``convert_selections``
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
    declaration each published argument was built from back off the schema.
    """
    coerced = get_argument_values(field_def, node, variable_values)
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
# nodes' ids. ``prime_selected_fields`` runs the full AST -> ``SelectedField``
# conversion on every connection resolution, and a nested FALLBACK connection
# resolves once per parent row with a fresh Strawberry ``Info`` each time - but
# graphql-core's executor caches collected sub-fields per execution
# (``ExecutionContext._subfields_cache``), so every row's ``info.field_nodes``
# is the SAME node group, and the conversion depends only on per-execution
# constants (``info.fragments`` / ``info.variable_values``). Reusing the first
# row's converted list collapses N per-row conversions to one. The key mirrors
# graphql-core's own subfields-cache shape (the ids of the individual field
# nodes, NOT the id of the wrapping list, which may be rebuilt or reused): AST
# node ids are stable for the memo's whole lifetime because the document is
# owned by the execution context that spans the same ``on_execute`` lifecycle.
# The memo belongs to the execution frame ``DjangoOptimizerExtension.on_execute``
# opens (``_context.py::_ExecutionFrame``), so it ends when that execution does
# and a task that copied the binding reads nothing. ``None`` outside a managed
# execution disables the memo, so direct / test callers see unchanged behavior.
# Consumers treat the converted list as read-only (the walker clones before
# mutating; Strawberry's ``selected_fields`` readers only iterate), so sharing
# one list across rows is safe.


def ast_to_converted_selections(
    info: GraphQLResolveInfo,
    field_nodes: Sequence[AstSelection],
) -> list[Selection]:
    """Convert graphql-core ``field_nodes`` to converted selections, anonymous-safe.

    Same contract as ``strawberry/types/nodes.py::convert_selections``, but builds
    every inline-fragment shell with ``type_condition = None`` when the node has no
    ``on TypeName`` condition, instead of unguardedly reading
    ``node.type_condition.name.value`` (Strawberry's ``InlineFragment.from_node``
    raises ``AttributeError: 'NoneType' object has no attribute 'name'`` on a valid
    anonymous inline fragment ``... { f }``). The optimizer routes
    ``info.field_nodes`` through here so its own fragment-aware substrate
    (``is_fragment`` duck-types on ``type_condition``, which a ``None`` shell still
    satisfies, so the shell flows through ``included_field_selections`` /
    ``named_children`` / ``with_runtime_prefix``) handles the shape Strawberry
    cannot represent - rather than depending on a Strawberry internal that
    mishandles a spec-valid query.

    The whole recursion is reimplemented (not just the top-level inline branch)
    because an anonymous inline fragment can sit at any depth - e.g.
    ``{ items { edges { node { ... { name } } } } }`` - and Strawberry's
    ``SelectedField.from_node`` / ``FragmentSpread.from_node`` recurse back into
    its own crashing ``convert_selections``. ``FragmentSpread`` definitions still
    come from ``info.fragments`` (a named spread always carries a type condition);
    only its body selections are re-converted here.

    The result is built from Strawberry's own ``SelectedField`` / ``FragmentSpread``
    / ``InlineFragment`` dataclasses (not ad-hoc shells) so the converted list is
    drop-in compatible with BOTH the package's duck-typed substrate AND Strawberry's
    own consumers that ``isinstance``-check against those classes (e.g.
    ``strawberry.relay.utils.should_resolve_list_connection_edges`` reached via
    ``ListConnection.resolve_connection`` when the package primes
    ``info.selected_fields`` with this list). The only deviation from Strawberry is
    that the anonymous inline-fragment branch passes ``type_condition=None`` instead
    of dereferencing the missing condition.

    The output must stay identical to ``convert_selections``: for every non-anonymous query
    shape the output is byte-identical to ``convert_selections`` (verified
    field-by-field, including nested argument and directive values, against the
    stock converter). That identity is load-bearing because ``prime_selected_fields``
    seeds this list into ``info.selected_fields``; any divergence here would corrupt
    ``info.selected_fields`` for normal (non-anonymous) queries the moment a
    connection primes it. If Strawberry's ``convert_selections`` gains a field or
    changes a shape, change it here the same way.

    Memoized per execution on the execution frame (see the comment above):
    within one ``on_execute`` lifecycle the same field-node group converts once,
    so the per-parent-row ``prime_selected_fields`` calls of a fallback
    connection pipeline reuse the first row's list instead of re-running the
    conversion for every parent.

    The recursion also tracks the GraphQL type each selection set is read on (the
    resolver's ``parent_type`` at the top, a field's named type below it, a
    fragment's type condition inside it) so each field selection the schema
    publishes carries the Python name of its field (``PYTHON_NAME_ATTR``, read
    through ``selection_python_name``) and its arguments by Python name, coerced
    by graphql-core (``PYTHON_ARGUMENTS_ATTR``, read through
    ``python_arguments``). Those markers are attributes beside the dataclass
    fields, so the fields Strawberry's consumers read stay identical to the output
    described above.
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

    def _convert(
        nodes: Iterable[AstSelection],
        parent: GraphQLNamedType | None,
    ) -> list[Selection]:
        out: list[Selection] = []
        for node in nodes:
            if isinstance(node, InlineFragmentNode):
                condition = inline_fragment_type_condition(node)
                out.append(
                    InlineFragment(
                        # basedpyright: Strawberry types ``InlineFragment.type_condition`` as
                        # ``str``; a typeless fragment has no condition to name, so it rejects the
                        # ``None`` arm
                        type_condition=(condition.name.value if condition is not None else None),  # pyright: ignore[reportArgumentType]
                        directives=convert_directives(info, node.directives),
                        selections=_convert(
                            ast_child_selections(node),
                            parent
                            if condition is None
                            else info.schema.get_type(condition.name.value),
                        ),
                    ),
                )
            elif isinstance(node, FragmentSpreadNode):
                fragment = info.fragments[node.name.value]
                out.append(
                    FragmentSpread(
                        name=node.name.value,
                        type_condition=fragment.type_condition.name.value,
                        directives=convert_directives(info, node.directives),
                        selections=_convert(
                            ast_child_selections(fragment),
                            info.schema.get_type(fragment.type_condition.name.value),
                        ),
                    ),
                )
            else:
                field_def = _published_field(parent, node.name.value)
                selected = SelectedField(
                    name=node.name.value,
                    alias=getattr(node.alias, "value", None),
                    directives=convert_directives(info, node.directives),
                    arguments=convert_arguments(info, node.arguments),
                    selections=_convert(
                        ast_child_selections(node),
                        None if field_def is None else get_named_type(graphql_type_of(field_def)),
                    ),
                )
                field_python_name = None if field_def is None else published_python_name(field_def)
                if field_python_name is not None:
                    setattr(selected, PYTHON_NAME_ATTR, field_python_name)
                if field_def is not None and field_def.args:
                    setattr(
                        selected,
                        PYTHON_ARGUMENTS_ATTR,
                        _coerced_python_arguments(field_def, node, info.variable_values),
                    )
                out.append(selected)
        return out

    converted = _convert(field_nodes, info.parent_type)
    if memo is not None and memo_key is not None:
        memo[memo_key] = converted
    return converted


def prime_selected_fields(info: Info[object, object]) -> None:
    """Pre-seed Strawberry ``Info.selected_fields`` with the anonymous-safe conversion.

    ``Info.selected_fields`` is a ``functools.cached_property`` that lazily calls
    Strawberry's crashing ``convert_selections`` on first read. Several consumers
    on the connection resolve path read it - the package's own
    ``connection.py::_total_count_requested`` AND Strawberry's own
    ``relay.utils.should_resolve_list_connection_edges`` (reached via
    ``ListConnection.resolve_connection``) - so an anonymous inline fragment on a
    connection query crashes inside Strawberry's resolver before the package can
    intervene. Computing the conversion through ``ast_to_converted_selections`` and
    storing it in the cached-property slot makes every later read return the
    package's anonymous-safe list (built from Strawberry's own ``SelectedField`` /
    ``FragmentSpread`` / ``InlineFragment`` dataclasses, so Strawberry's
    ``isinstance``-based consumers keep working). Idempotent and a no-op when the
    info has no field nodes or the cache is already populated (so a consumer that
    legitimately read ``selected_fields`` first is never overwritten).

    Must run BEFORE any ``info.selected_fields`` read on the connection path - the
    cached property computes once on first read, so priming only wins if it lands
    first. ``connection.py::DjangoConnection.resolve_connection`` calls this immediately
    after the ``first`` + ``last`` guard, ahead of both the ``_total_count_requested``
    inspection and ``super().resolve_connection``.

    NOTE - this COUPLES to two Strawberry internals: the raw info living at
    ``Info._raw_info`` and ``Info.selected_fields`` being a ``functools.cached_property``
    backed by the ``info.__dict__["selected_fields"]`` slot. Both hold at the pinned
    Strawberry version. If a future Strawberry renames ``_raw_info`` (or stops using
    the dict-slot cache), this SILENTLY no-ops - ``getattr(info, "_raw_info", None)``
    returns ``None``, nothing is seeded, and the connection-path crash returns rather
    than failing loudly. The live anonymous-inline-fragment tests
    (``test_anonymous_inline_fragment_*`` in the fakeshop ``test_query`` suite) are
    the regression net that would catch such a Strawberry-internals rename on a
    version bump.
    """
    # Strawberry's own ``cached_property`` slot on the Info it handed us.
    namespace = info.__dict__  # truth: ok seeds Strawberry Info's cache slot, not an identity read
    if "selected_fields" in namespace:
        return
    selections = info_selections(info)
    if selections:
        namespace["selected_fields"] = selections


def info_selections(info: Info[object, object]) -> list[Selection]:
    """Return a resolver ``info``'s own field selections, converted and stamped.

    ``ast_to_converted_selections`` over the field nodes of the graphql-core info
    Strawberry wraps, so every field selection carries ``PYTHON_NAME_ATTR`` /
    ``PYTHON_ARGUMENTS_ATTR`` whoever read ``info.selected_fields`` first (a
    consumer extension reading it before ``prime_selected_fields`` leaves
    Strawberry's unstamped list in that slot). Memoized per execution like every
    conversion. Empty when ``info`` carries no field nodes.
    """
    # Strawberry's ``Info`` keeps the graphql-core info at ``_raw_info``, whose
    # ``field_nodes`` is a list of ``FieldNode``s.
    raw_info: GraphQLResolveInfo | None = getattr(info, "_raw_info", None)
    field_nodes: list[FieldNode] | None = getattr(raw_info, "field_nodes", None)
    if raw_info is None or not field_nodes:
        return []
    return ast_to_converted_selections(raw_info, field_nodes)


# ---------------------------------------------------------------------------
# AST adapter - graphql-core nodes (``optimizer/extension.py``)
# ---------------------------------------------------------------------------


def ast_child_selections(node: Node) -> tuple[AstSelection, ...]:
    """Return the AST node's selection-set children as a tuple, or ``()``.

    Centralizes the ``getattr(node, "selection_set", None)`` plus
    ``selections or ()`` shape so the AST walkers
    (``_walk_cache_relevant_vars``, ``_walk_reachable_fragment_definitions``,
    and by extension ``_collect_reachable_fragment_definitions``) share
    one "iterate children" implementation. ``FragmentSpreadNode`` has
    no ``selection_set``, so this returns ``()`` and the caller's
    per-child loop becomes a no-op.
    """
    # Every graphql-core node that has a ``selection_set`` types it as a
    # ``SelectionSetNode`` (optional on ``FieldNode``).
    selection_set: SelectionSetNode | None = getattr(node, "selection_set", None)
    if selection_set is None:
        return ()
    # graphql-core's parser fills a selection set only with these three node kinds
    # (``Parser.parse_selection``); the node class types them as ``SelectionNode``.
    return cast("tuple[AstSelection, ...]", tuple(selection_set.selections or ()))


def resolve_unvisited_fragment(
    node: Node,
    fragments: Mapping[str, FragmentDefinitionNode],
    visited_fragments: set[FragmentVisitKey],
    *,
    depth: int | None = None,
) -> FragmentDefinitionNode | None:
    """Resolve a ``FragmentSpreadNode`` to its definition, once per visit key.

    Returns the matching ``FragmentDefinitionNode`` and marks the visit key
    so a sibling or cyclic spread in the same walk is a no-op. The visit key
    is the fragment name when ``depth`` is omitted (reachable-fragment
    collection for the plan-cache document key) and ``(name, depth)`` when
    ``depth`` is supplied (depth-sensitive cache-relevant-variable walk: the
    same fragment spread at two response-path depths must be walked once per
    depth so nested pagination variables are not dropped). Returns ``None``
    when ``node`` is not a fragment spread, when the spread has no name, when
    the visit key is already present, or when the document does not define
    the named fragment (defensive - graphql-core's validation would normally
    reject the operation before the optimizer sees it). Mutates
    ``visited_fragments`` on success so callers share one cycle-detection set
    across recursive descents.
    """
    if not isinstance(node, FragmentSpreadNode):
        return None
    # graphql-core types ``name`` non-optional; a node built without ``name=`` holds None
    frag_name = node.name.value if node.name else None
    if frag_name is None:
        return None
    visit_key: FragmentVisitKey = frag_name if depth is None else (frag_name, depth)
    if visit_key in visited_fragments:
        return None
    frag_def = fragments.get(frag_name)
    if frag_def is None:
        return None
    visited_fragments.add(visit_key)
    return frag_def


def directive_variable_names(node: Node) -> set[str]:
    """Return the variable names referenced in ``@skip`` / ``@include`` on ``node``.

    Only variables inside the ``if`` argument of ``@skip`` / ``@include`` affect
    the selection tree (and therefore the plan cache); every other variable is
    excluded. Defensive against a ``directives`` collection carrying a
    non-``DirectiveNode`` object (pinned by
    ``test_walk_cache_relevant_vars_ignores_non_directive_objects``). The single
    directive-variable extraction the AST cache-key walk shares, so the
    ``("skip", "include")`` membership and the ``VariableNode`` check live once.
    """
    names: set[str] = set()
    directives: Iterable[object] = getattr(node, "directives", ()) or ()
    for directive in directives:
        if not isinstance(directive, DirectiveNode):
            continue
        # graphql-core types ``name`` non-optional; a node built without ``name=`` holds None
        d_name = directive.name.value if directive.name else None
        if d_name not in ("skip", "include"):
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
    converted selections, shared by the walker, the connection ``edges { node }``
    unwrap, and the connection ``totalCount`` detection (``direct_child_selected``)
    so the three cannot drift on what counts as a fragment.
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
# production-entry contract (spec-035 Decision 6 R1). Pseudocode: no classifier means INLINE-all
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
    Both callers (the walker's level descent and the FK-id-elision scalar
    scan) only iterate the result, so sharing the caller's list is safe.

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

    A child matches by ``selection_python_name``: the name the selected field was
    declared under, whatever wire name the schema's ``NameConverter`` published it as.
    """
    children: list[FieldSelection] = []
    members: Iterable[ConvertedSelection] = getattr(selection, "selections", None) or []
    for child in members:
        if not should_include(child):
            continue
        if is_fragment(child):
            # Recurse into the fragment directly: its own ``selections`` are the
            # children to search, so re-entering ``named_children`` on the
            # fragment iterates them (and descends nested fragments) with the
            # same ``should_include`` / name-match rules. This avoids allocating
            # a throwaway single-child ``SimpleNamespace`` shell per fragment
            # child - the former shape, which wrapped each child only to give the
            # recursion a ``.selections`` to walk.
            children.extend(named_children(child, name))
            continue
        if selection_python_name(child) == name:
            # ``is_fragment`` rejected it, so it is a field selection.
            children.append(cast("FieldSelection", child))
    return children


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
    children: list[SimpleNamespace] = []
    members: Iterable[ConvertedSelection] = getattr(node_selection, "selections", None) or []
    for child in members:
        if not should_include(child):
            continue
        children.append(with_runtime_prefix(child, runtime_prefixes))
    return children


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

    A selection matches by ``selection_python_name``, never by its wire name.
    Recurses ONLY through fragment wrappers (``is_fragment``), NOT into a regular
    field's sub-selections, so a field named ``name`` nested deeper in the tree
    does NOT count. The connection field's ``totalCount`` detection
    (``connection.py::_total_count_requested``) uses this so a fragment-wrapped
    direct ``totalCount`` still fires the count while a node-level nested
    connection's ``totalCount`` deep inside ``edges { node { ... } }`` does not
    trip the OUTER connection's predicate. Sharing the ``is_fragment``
    discriminator with the walker / edge-node unwrap keeps the "recurse through
    fragments only" rule from drifting between the count detection and the
    selection planning.

    Gated on ``should_include`` like ``included_field_selections`` and
    ``named_children``: converted selections carry live, already-evaluated
    ``@skip`` / ``@include`` args, so a ``totalCount @skip(if: true)`` (or a
    ``@skip``-ped fragment wrapping it) must NOT fire the connection ``COUNT``.
    A directive-excluded field returns ``False`` even on a name match, and an
    excluded fragment shell prunes its whole subtree.
    """

    def _check(selection: ConvertedSelection) -> bool:
        if not should_include(selection):
            return False
        if is_fragment(selection):
            members: Iterable[ConvertedSelection] = getattr(selection, "selections", None) or []
            return any(_check(child) for child in members)
        return selection_python_name(selection) == name

    return any(_check(child) for child in selection_roots)


def connection_total_count_selected(selection: ConvertedSelection) -> bool:
    """Return whether ``selection`` (a connection field) selects ``totalCount``.

    The count field as a DIRECT child of the connection, through fragment
    wrappers only (``direct_child_selected``). The single implementation of
    the count-observability walk: the plan-time
    ``nested_planner.py::plan_connection_relation`` and the resolve-time
    ``connection.py::_total_count_requested`` both call it, so the two
    halves of the conditional ``_dst_total_count`` contract share one walk
    by construction - and match the field by its Python name ``total_count``,
    so neither depends on the wire name the schema publishes it under.
    """
    children: Iterable[ConvertedSelection] = getattr(selection, "selections", None) or []
    return direct_child_selected(children, _TOTAL_COUNT)


def connection_has_next_page_selected(selection: ConvertedSelection) -> bool:
    """Return whether ``selection`` selects ``pageInfo { hasNextPage }``.

    The ``hasNextPage`` sibling of ``connection_total_count_selected``: a
    direct page-info child (through fragment wrappers, alias-merged via
    ``named_children``), then a direct has-next-page child under it. Shared by
    the plan-time ``nested_planner.py::plan_connection_relation`` and the
    resolve-time ``connection.py::_has_next_page_requested``.
    """
    return any(
        direct_child_selected(
            getattr(page_info, "selections", None) or [],
            _HAS_NEXT_PAGE,
        )
        for page_info in named_children(selection, _PAGE_INFO)
    )
