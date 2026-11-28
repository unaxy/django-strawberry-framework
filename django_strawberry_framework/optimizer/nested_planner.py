"""Transactional planner for nested Relay connection selections.

The general walker normalizes selections and resolves model/type metadata, then
delegates one recognized nested connection here. This component owns pagination
normalization, fallback classification, child-queryset construction, fetch
strategy dispatch, and acceptance bookkeeping. It builds a private result plan
and returns it only after orchestration completes, so refusal or an exception
cannot leak partial directives into the walker's parent plan.
"""

from __future__ import annotations

from functools import lru_cache
from types import SimpleNamespace
from typing import TYPE_CHECKING, TypeVar, cast

from django.core.exceptions import FieldDoesNotExist, FieldError
from django.db import connections, models
from django.db.models.expressions import Col
from django.db.models.options import Options
from django.db.models.sql.query import Query
from graphql import GraphQLError
from strawberry import relay

from django_strawberry_framework.conf import django_setting
from django_strawberry_framework.keyset import (
    CursorState,
    KeysetSeek,
    declared_cursor_state_for_definition,
    decode_keyset_cursor,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils import introspection
from django_strawberry_framework.utils._narrowing import (
    is_concrete_field,
    is_str,
    list_of,
    require,
)
from django_strawberry_framework.utils.connections import (
    ConnectionWindowBounds,
    FetchMode,
    PaginationArgumentError,
    UnwindowableConnection,
    derive_connection_window_bounds,
    derive_keyset_window_bounds,
    has_connection_sidecar_kwargs,
    relation_connection_to_attr,
    window_range_plan,
)
from django_strawberry_framework.utils.imports import import_attr_if_importable
from django_strawberry_framework.utils.querysets import expand_relation_order
from django_strawberry_framework.utils.relations import instance_accessor, is_model_class

from . import logger
from .hints import hint_is_skip
from .join_taxonomy import RelationJoinDescriptor, classify_relation_join
from .nested_fetch import (
    NestedConnectionRequest,
    active_strategy,
    resolve_strategy,
    unwindowable_child_queryset_reason,
)
from .plans import (
    JoinPrefix,
    OptimizationPlan,
    PlannedWindow,
    append_unique,
    append_unique_many,
    apply_projection,
    effective_connection_order,
    effective_cursor_state,
    has_random_term,
    local_cursor_attnames,
    normalize_order_direction,
    order_entry_has_explicit_nulls,
    order_entry_name_and_direction,
    resolver_key,
)
from .selections import (
    RUNTIME_PREFIXES_ATTR,
    connection_has_next_page_selected,
    connection_node_children,
    connection_total_count_selected,
    python_arguments,
    response_keys,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence
    from typing import TypeAlias

    from django.contrib.postgres.indexes import BTreeIndex
    from django.db.models import QuerySet
    from graphql.type.definition import GraphQLResolveInfo

    from django_strawberry_framework.keyset import CursorColumn
    from django_strawberry_framework.types.base import DjangoType
    from django_strawberry_framework.types.definition import DjangoTypeDefinition
    from django_strawberry_framework.utils.typing import ConcreteField

    from .field_meta import FieldMeta
    from .hints import OptimizerHint
    from .nested_fetch import NestedConnectionStrategy, StrategySelection
    from .plans import OrderEntry
    from .selections import FieldSelection

    #: One planned window: its response key, bounds, and decoded keyset seek.
    _KeyedWindow: TypeAlias = tuple[str | None, ConnectionWindowBounds, KeysetSeek | None]
    #: One ``_divergent_key_windows`` pass: ``(planned, malformed, fallbacks)``.
    _WindowPass: TypeAlias = tuple[
        list[_KeyedWindow],
        list[str | None],
        list[tuple[str | None, str]],
    ]
    #: Any model's ``Options``.
    _OptionsAny: TypeAlias = Options[models.Model]
else:
    # ``Options`` has no ``__class_getitem__`` at runtime: the hint stays the class.
    _OptionsAny = Options

_M = TypeVar("_M", bound=models.Model)

# The exact ``Index`` types proven to build an ordinary ORDER-serving B-tree:
# the plain ``models.Index`` and PostgreSQL's ``BTreeIndex``. ``GinIndex`` /
# ``GistIndex`` / ``HashIndex`` / ``BrinIndex`` / ``SpGistIndex`` share the base
# ``.fields`` API but back a non-ordering access method, and a custom ``Index``
# subclass's method we cannot vouch for; all are excluded so the inventory
# degrades them to UNKNOWN rather than trusting them to serve the window's
# ``ORDER BY`` (the false-``covered`` defect for non-B-tree indexes). Soft-import
# ``BTreeIndex`` through the shared optional-import owner (same policy as
# ``types/converters.py``'s postgres field classes): ``None`` when
# ``django.contrib.postgres`` is unimportable; loud ``AttributeError`` if the
# module loads but the class is missing. Absence leaves plain ``models.Index``
# as the sole B-tree-backed type (the safe default). The cast names the class the
# by-name lookup returns.
_PostgresBTreeIndex: type[models.Index] | None = cast(
    "type[BTreeIndex] | None",
    import_attr_if_importable("django.contrib.postgres.indexes", "BTreeIndex"),
)

_BTREE_INDEX_TYPES: tuple[type[object], ...] = (
    (models.Index,) if _PostgresBTreeIndex is None else (models.Index, _PostgresBTreeIndex)
)


def _every_backend_supports_index_column_ordering() -> bool:
    """Whether EVERY configured database can store per-column index directions.

    A ``-``-prefixed field in an ``Index`` (``fields=["title", "-id"]``) is a
    physical ``id DESC`` column ONLY when the backend supports index-column
    ordering; where it does not, Django silently builds a plain ascending index,
    so reading that term as ``("id", True)`` would be wrong.

    A nested plan is backend-NEUTRAL and cache-shared: the same cached plan may
    execute on whatever alias the parent prefetch's ``.using(...)`` or the router
    selects, and the advisory is computed at plan time with no parent instance in
    hand. Consulting one unhinted ``router.db_for_read`` route and treating its
    answer as universal is the alias-early error already removed from
    ``GenericRelation`` content-type planning: a divergent router can return a
    direction-capable default while the plan later runs on a shard that silently
    drops the direction. So a descending term is trusted only when NO reachable
    backend would drop it - every configured alias must support index-column
    ordering. Any failure enumerating the databases is fail-soft (``False``), and
    an empty configuration is treated as unproven, so the caller leaves such an
    index UNKNOWN rather than making a coverage claim it cannot prove.
    """
    try:
        aliases = list(connections)
        return bool(aliases) and all(
            connections[alias].features.supports_index_column_ordering for alias in aliases
        )
    except Exception:  # noqa: BLE001 - consumer code may raise anything
        return False


def _concrete_order_columns(order_by: Sequence[object], model: type[models.Model]) -> list[str]:
    """Return the LOCAL concrete column attnames referenced by ``order_by``.

    Related-span lookups (``author__name``) and unresolvable expressions are
    skipped: the window's ``OVER (ORDER BY ...)`` and the queryset ``ORDER BY``
    reference those columns in SQL regardless of the ``.only()`` projection, so a
    skipped column only forgoes loading an attribute a scalar-only selection
    never reads. The result keeps the scalar-only window projection minimal yet
    order-complete (spec-033 Decision 4 scalar-only bullet: the
    "pk/connector/order-only child projection").
    """
    by_name = {field.name: field.attname for field in model._meta.concrete_fields}
    attnames = set(by_name.values())
    columns: list[str] = []
    for entry in order_by:
        parsed = order_entry_name_and_direction(entry)
        if parsed is None or "__" in parsed[0]:
            continue
        name = parsed[0]
        if name in by_name:
            append_unique(columns, by_name[name])
        elif name in attnames:
            append_unique(columns, name)
    return columns


def _select_nested_strategy(hint: OptimizerHint | None) -> NestedConnectionStrategy:
    """Return the fetch strategy for a connection field, honoring a per-field hint.

    ``OptimizerHint.strategy(name)`` (``nested_strategy=...``) overrides the
    extension-wide default for one Relay connection field; the name was already
    validated through ``nested_fetch.py::resolve_strategy`` at
    ``Meta.optimizer_hints`` build time (``optimizer/hints.py::OptimizerHint``),
    so re-resolving it here cannot raise on a landed schema. When no hint sets a
    strategy, fall back to the active extension instance's default
    (``nested_fetch.py::active_strategy``). The knob is schema-static, so this
    selection never enters the instance-bound plan cache key.
    """
    name: StrategySelection | None = getattr(hint, "nested_strategy", None)
    if name is not None:
        return resolve_strategy(name)
    return active_strategy()


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
    is the cartesian product over those prefixes and ``response_keys(sel)``.
    """
    # Only the walker's ``SimpleNamespace`` clones carry runtime prefixes.
    carried_prefixes = _selection_runtime_prefixes(sel)
    selection_runtime_prefixes: tuple[tuple[str, ...], ...] = (
        tuple(carried_prefixes) if carried_prefixes is not None else runtime_prefixes
    )
    runtime_paths = tuple(
        (*runtime_prefix, response_key)
        for runtime_prefix in selection_runtime_prefixes
        for response_key in response_keys(sel)
    )
    resolver_identities = tuple(
        resolver_key(type_cls, field_name, runtime_path) for runtime_path in runtime_paths
    )
    return runtime_paths, resolver_identities


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
    aliases share one window. Payloads are graphql-core-coerced,
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


def _concrete_order_terms(
    order_by: Sequence[object],
    model: type[models.Model],
) -> list[tuple[str, bool]] | None:
    """Return the child-table ``(attname, descending)`` order terms, or ``None`` if any is not.

    The direction-carrying counterpart of ``_concrete_order_columns``: a B-tree
    can serve a requested ordering (or its full reverse) only when the index
    terms match the requested ``(column, direction)`` sequence, so the
    composite-index advisory must compare directions, not bare attnames (a mixed
    ``title ASC, id DESC`` is NOT served by ``(title, id)`` ascending). Each
    term's column is the one the window's ``ORDER BY`` names
    (``_window_column``): ``"pk"`` is the child's pk column, and on a
    multi-table-inheritance child the inherited pk name ``"id"`` is the child's
    own parent-link column.

    The fail-soft tri-state begins HERE, not only at index parsing: the SQL
    ``ORDER BY`` references EVERY effective ordering term regardless of the
    ``.only()`` projection, so a term that is not a column of the child's own
    table - a related span through a join (``author__name``), a column a
    multi-table-inheritance child inherits from a parent table, an arbitrary
    expression (``Lower("title")``), an alias, an unresolvable name - means the
    order is only PARTIALLY understood by any index the child's table can hold.
    Silently dropping it and coverage-checking the remaining suffix would let
    ``(Lower("title"), "id")`` be declared served by ``(parent_id, id)`` (a false
    positive) or recommend that incomplete index as the serving shape, and
    keeping an inherited column would recommend an index no table can hold.
    Return ``None`` the moment ANY term cannot be represented as a child-table
    ``(attname, direction)`` so the advisory stays SILENT for that plan shape -
    this UNKNOWN dominates the index-parsing tri-state exactly as an
    uninspectable index leaves absence unproven. (The projection helper
    ``_concrete_order_columns`` may still skip or keep such terms: ``.only()``
    accepts an inherited column and forgoing a column a scalar-only selection
    never reads is harmless, whereas a coverage CLAIM from a partial order is
    not.)

    Explicit NULLS placement is likewise UNKNOWN: an ``OrderBy`` carrying
    ``nulls_first`` / ``nulls_last`` executes ``title ASC NULLS FIRST`` (etc.),
    which a plain ``Meta.indexes`` term (whose NULL ordering is the backend
    default) cannot be PROVEN to serve, so any such term returns ``None`` rather
    than collapse to a bare ``(attname, direction)`` that would falsely read as
    covered (``plans.py::order_entry_has_explicit_nulls``).
    """
    terms: list[tuple[str, bool]] = []
    seen: set[str] = set()
    for entry in order_by:
        if order_entry_has_explicit_nulls(entry):
            return None
        parsed = order_entry_name_and_direction(entry)
        if parsed is None:
            return None
        name, descending = parsed
        field = _window_column(model, name)
        if field is None:
            return None
        if field.attname in seen:
            continue
        seen.add(field.attname)
        terms.append((field.attname, descending))
    return terms


def _window_column(related_model: type[models.Model], ref: str) -> ConcreteField | None:
    """Return the child-table column a nested window reference resolves to, or ``None``.

    Resolved exactly as the window resolves it:
    ``plans.py::apply_window_pagination`` hands the partition expression to
    ``Window(partition_by=...)`` and the order entries to
    ``Window(order_by=...)``; each string becomes ``F(ref)`` (under an
    ``OrderBy`` for a ``-`` prefix), and ``F.resolve_expression`` is
    ``Query.resolve_ref`` against the child model's query, which trims a join it
    can answer from the child's own row (a forward relation's local column, the
    inherited pk name on a multi-table-inheritance child).

    One index serves the page only when every column the window names sits on
    the child's own table, so the resolved column must belong to the query's
    base table. A column reached through a join carries another alias and
    returns ``None``: an M2M's through-table foreign key, a column a
    multi-table-inheritance child inherits from a parent table (a generic link
    the parent declares, an inherited order column), a related row's column
    (a self-referential relation joins the same table under a second alias).
    ``None`` too when the reference does not resolve (``resolve_ref`` raises
    ``FieldError``) or resolves to something other than one column (a
    transform, a composite primary key's column pair).
    """
    query = Query(related_model)
    try:
        resolved = query.resolve_ref(ref)
    except FieldError:
        return None
    if not isinstance(resolved, Col) or resolved.alias != query.get_initial_alias():
        return None
    return resolved.target


def _index_leading_terms(meta: _OptionsAny, index: object) -> list[tuple[str, bool]] | None:
    """Return an index's leading ``(attname, descending)`` terms, or ``None`` when uninspectable.

    ``Meta.indexes`` entries carry field NAMES (optionally ``-``-prefixed for a
    descending column), so each is mapped to its concrete attname AND direction
    for comparison with the window's leading terms. Several shapes are
    UNINSPECTABLE and return ``None`` so the caller leaves absence UNPROVEN
    rather than either concluding an index is absent OR trusting it to cover:

    - a NON-B-TREE / CUSTOM access method: ``GinIndex`` / ``GistIndex`` /
      ``HashIndex`` / ``BrinIndex`` / ``SpGistIndex`` (and any custom ``Index``
      subclass) all inherit ``.fields`` yet do not build an ordinary ordered
      B-tree, so only the exact ``models.Index`` / PostgreSQL ``BTreeIndex``
      types may claim to serve a multi-column ``ORDER BY``;
    - a NON-DEFAULT OPCLASS (``varchar_pattern_ops`` etc.): an explicit opclass
      is chosen for a lookup semantics (prefix search) that need not provide the
      query's ordinary ordering, so the term cannot be PROVEN covering;
    - an EXPRESSION index exposes no ``.fields``;
    - a PARTIAL index carries a ``.condition`` - PostgreSQL uses it only for
      queries whose predicate implies that condition, which the nested window
      does not, so a partial index on the right columns must NOT be read as
      covering the general page;
    - a name that no longer resolves is a migration lag;
    - a DESCENDING index column when any configured backend cannot store
      index-column ordering (Django then silently builds a plain ascending index,
      so the ``("id", True)`` reading would be wrong; the plan is backend-neutral,
      so the direction is trusted only when EVERY alias supports it -
      ``_every_backend_supports_index_column_ordering``).
    """
    if type(index) not in _BTREE_INDEX_TYPES:
        return None
    if getattr(index, "condition", None) is not None:
        return None
    if getattr(index, "opclasses", None):
        return None
    # The exact-type gate above admits only ``models.Index`` / ``BTreeIndex``, whose
    # ``__init__`` stores ``fields`` as a list of field-name strings.
    field_names: Sequence[str] | None = getattr(index, "fields", None)
    if not field_names:
        return None
    descending = [name.startswith("-") for name in field_names]
    ascending = _plain_field_terms(meta, [name.removeprefix("-") for name in field_names])
    if ascending is None:
        return None
    if any(descending) and not _every_backend_supports_index_column_ordering():
        return None
    return [(attname, flag) for (attname, _), flag in zip(ascending, descending, strict=True)]


# Tri-state result of index inspection: a covering index is present, no index in
# the represented model metadata covers the shape, or the metadata cannot be
# classified (a non-B-tree / expression / partial index, or a shape only a
# DBA-created index outside all Django model metadata could satisfy) so absence
# is UNPROVEN. "Represented model metadata" spans ``Meta.indexes``,
# ``Meta.constraints`` unique constraints, ``unique_together``, and field-level
# pk/unique/db_index - see ``_model_index_shapes``.
_INDEX_COVERED = "covered"
_INDEX_ABSENT = "absent"
_INDEX_UNKNOWN = "unknown"


def _terms_serve_order(
    rest: Sequence[tuple[str, bool]],
    order_terms: Sequence[tuple[str, bool]],
) -> bool:
    """Whether index terms ``rest`` serve ``order_terms`` exactly or fully reversed.

    After the equality-constrained prefix columns, a B-tree yields rows in the
    requested order only when its remaining leading terms equal the requested
    ``(attname, direction)`` sequence, or equal that sequence with EVERY
    direction flipped (a backward index scan). A partial flip cannot be served
    without a sort - the false-negative the advisory must still flag.
    """
    order_terms = list(order_terms)
    if len(rest) < len(order_terms):
        return False
    head = list(rest[: len(order_terms)])
    if head == order_terms:
        return True
    flipped = [(attname, not descending) for attname, descending in order_terms]
    return head == flipped


def _index_serves_window(
    index_terms: Sequence[tuple[str, bool]],
    equality: Sequence[str],
    order_terms: Sequence[tuple[str, bool]],
) -> bool:
    """Whether one index's leading terms cover the window's equality prefix + order.

    The window equality-constrains the ``equality`` columns (the partition
    column, and for a ``GenericRelation`` the ``content_type_id`` morph column),
    so any permutation of them at the index head is acceptable; direction on an
    equality column is irrelevant. The index's terms AFTER that prefix must then
    serve the requested order (``_terms_serve_order``).
    """
    prefix_len = len(equality)
    lead = list(index_terms[:prefix_len])
    if len(lead) < prefix_len:
        return False
    if {attname for attname, _ in lead} != set(equality):
        return False
    return _terms_serve_order(index_terms[prefix_len:], order_terms)


def _plain_field_terms(meta: _OptionsAny, names: Sequence[str]) -> list[tuple[str, bool]] | None:
    """Map DIRECTIONLESS field names to ascending ``(attname, False)`` terms, or ``None``.

    For ``UniqueConstraint`` / ``unique_together`` entries, which carry no
    per-column direction (and for an ``Index``'s names with their ``-`` prefix
    stripped, ``_index_leading_terms``): the unique btree is ascending, and
    ``_terms_serve_order`` still admits a FULL backward scan, so ascending terms
    correctly cover the requested order or its full reverse. ``None`` when any
    name does not resolve to a field (a migration lag), so the caller leaves
    absence unproven rather than trusting a stale shape.
    """
    terms: list[tuple[str, bool]] = []
    for name in names:
        try:
            field = meta.get_field(name)
        except FieldDoesNotExist:
            return None
        # Django's model checks admit only concrete local fields in unique sets and
        # ``Meta.indexes``; a name resolving to a reverse relation cannot be proven a column.
        if not is_concrete_field(field):
            return None
        terms.append((field.attname, False))
    return terms


def _model_index_shapes(meta: _OptionsAny) -> list[list[tuple[str, bool]] | None]:
    """Return the leading-term shape of every index of a table-owning model.

    The coverage inventory built from every PHYSICAL index shape model metadata
    represents inspectably, so the advisory reasons about the indexes PostgreSQL
    can actually use for a nested window - not only ``Meta.indexes``. ``meta`` is
    the options of the model that owns the table (``_meta.concrete_model``): a
    proxy's own ``Meta.indexes`` / ``constraints`` / ``unique_together`` are
    always empty (Django keeps them on the declaring class, and ``models.E016``
    refuses a proxy declaring any), so read through a proxy they would hide every
    index its table holds:

    - unconditional field-based ``Meta.indexes`` entries (direction-carrying);
    - unconditional field-based ``UniqueConstraint`` entries and legacy
      ``unique_together`` (a unique btree is a usable ascending composite);
    - single-field ``primary_key`` / ``unique`` / ``db_index`` columns on the
      model's own table (one shared field-index predicate - this is what makes
      the FK auto-index cover the partition-column-only window). A
      multi-table-inheritance child's ``concrete_fields`` also lists the fields
      it inherits, whose indexes sit on the parent's table; Django never copies a
      concrete parent's ``Meta.indexes`` / ``constraints`` / ``unique_together``
      onto the child, and its model checks (``models.E016``) refuse a child entry
      naming an inherited field, so every shape here is an index on the child's
      own table.

    A conditional/partial or expression ``Index``/``UniqueConstraint``, or a
    name that no longer resolves, is an UNINSPECTABLE ``None`` entry rather than
    a covering or an absent shape: its predicate cannot be proven to imply the
    window's, so absence stays unproven. ``CheckConstraint`` and other non-unique
    constraints are simply irrelevant (never uninspectable).
    """
    shapes: list[list[tuple[str, bool]] | None] = [
        _index_leading_terms(meta, index) for index in list_of(meta.indexes)
    ]
    total_unique = meta.total_unique_constraints
    # A conditional or expression ``UniqueConstraint`` is absent from Django's
    # total list; its index still exists, so it leaves absence unprovable.
    # ``CheckConstraint`` / ``ExclusionConstraint`` are not coverage shapes.
    if sum(
        isinstance(constraint, models.UniqueConstraint) for constraint in meta.constraints
    ) > len(total_unique):
        shapes.append(None)
    # A non-default opclass (``varchar_pattern_ops`` etc.) is chosen for a lookup
    # semantics that need not provide the window's ordinary ordering, exactly as
    # ``_index_leading_terms`` rejects an ``Index`` opclass - so route it through
    # the SAME capability gate rather than letting the constraint claim an
    # ordinary ascending B-tree.
    shapes.extend(
        None
        if getattr(constraint, "opclasses", None)
        else _plain_field_terms(meta, constraint.fields)
        for constraint in total_unique
    )
    shapes.extend(_plain_field_terms(meta, names) for names in meta.unique_together or ())
    shapes.extend(
        [(field.attname, False)]
        for field in meta.concrete_fields
        if field.model._meta.db_table == meta.db_table
        and (
            field.primary_key
            or getattr(field, "unique", False)
            or getattr(field, "db_index", False)
        )
    )
    return shapes


def _index_coverage(
    table_model: type[models.Model],
    equality: Sequence[str],
    order_terms: Sequence[tuple[str, bool]],
) -> str:
    """Tri-state classify whether a represented index covers the window's leading shape.

    ``table_model`` is the model that owns the window's table, never a proxy of
    it (``_model_index_shapes``). Returns ``_INDEX_COVERED`` when some
    inspectable physical index shape (``_model_index_shapes``: an
    unconditional field-based ``Index`` / ``UniqueConstraint`` /
    ``unique_together``, or a single equality column's
    field-level ``db_index`` / ``unique`` / FK auto-index) serves the
    ``(equality prefix, order terms)`` shape; ``_INDEX_UNKNOWN`` when a covering
    index is not represented but at least one index could not be classified
    (expression / partial index, migration-lagged field), so absence is
    unproven; ``_INDEX_ABSENT`` only when every represented index is inspectable
    and none covers. The caller warns solely on ``_INDEX_ABSENT`` - "not
    represented in model metadata" is never conflated with "proved absent" (a
    DBA-created index outside model metadata stays invisible here).
    """
    shapes = _model_index_shapes(table_model._meta)
    if any(t is not None and _index_serves_window(t, equality, order_terms) for t in shapes):
        return _INDEX_COVERED
    return _INDEX_UNKNOWN if None in shapes else _INDEX_ABSENT


# One plan shape warns at most once even when its plan is rebuilt on every
# request: plans carrying a custom ``get_queryset`` stay out of the extension's
# cross-request plan cache, so ``plan_connection_relation`` re-runs this advisory
# per request. The cache key is strategy- AND request-independent: the
# table-owning model, the equality-prefix columns and the effective order terms
# are the entire input that determines the recommended index, so rebuilds of one
# shape collapse (a proxy and its concrete model are one table) while different
# shapes each still warn once. The LRU bound keeps a pathological variety of
# shapes from growing memory; eviction only re-emits a long-cold advisory. The
# log level is chosen on the first emission, so tests toggling ``DEBUG`` call
# ``_emit_index_advisory.cache_clear()``.
@lru_cache(maxsize=512)
def _emit_index_advisory(
    app_label: str,
    object_name: str,
    equality: tuple[str, ...],
    effective_order: tuple[tuple[str, bool], ...],
) -> None:
    """Log the composite-index recommendation for one plan shape (once per shape).

    Equality columns carry no direction (an equality predicate is
    direction-agnostic); each order column shows ``DESC`` when the requested
    ordering is descending so the advisory names the exact B-tree shape.
    """
    columns = [
        *equality,
        *(f"{attname} DESC" if descending else attname for attname, descending in effective_order),
    ]
    log = logger.warning if django_setting("DEBUG") else logger.debug
    log(
        "Optimizer: nested connection on %s.%s has no represented index covering the "
        "window's leading columns %s; a composite index on (%s) would let the database "
        "serve each page from the index instead of sorting per partition. Advisory only "
        "(an index absent from Django model metadata is not visible here).",
        app_label,
        object_name,
        columns,
        ", ".join(columns),
    )


def _advise_composite_index(
    related_model: type[models.Model],
    join: RelationJoinDescriptor,
    order_by: Sequence[object],
) -> None:
    """Emit a dev-mode advisory when no index covers a nested window's leading columns.

    A windowed or lateral nested connection equality-constrains its partition
    column (``join.partition_expr``, resolved to its concrete column by
    ``_window_column``) - and, for a ``GenericRelation``, the
    ``content_type_id`` morph column (``join.content_type_column``) ahead of it -
    then orders by the deterministic order terms, so a composite index whose
    leading columns mirror ``(content_type_id?, partition column, order terms...,
    pk)`` lets the database serve each partition's page from the index instead of
    sorting per partition (the keyset composite mirrors
    ``keyset.py::KeysetSeek.q``'s redundant-leading-bound design). Direction is
    load-bearing: a B-tree serves only the requested order or its FULL reverse
    after the equality prefix.

    One index can serve the page only when the morph column, the partition
    column and the order columns all live on the child's table. When any of them
    lives on another table - an M2M's through table, or a
    multi-table-inheritance parent table holding a column the child inherits (a
    generic link the parent declares, an inherited order column such as a
    parent's ``name``) - the window spans two tables, no single B-tree holds every
    column, and the advisory stays silent, as it does when the partition
    expression does not resolve. Every column is resolved as the window resolves
    it (``_window_column``), so the recommendation names the child-table column
    the SQL reads (``"pk"`` and an inherited pk name read as the child's own pk
    column).

    Coverage is inspected against every physical index shape Django model
    metadata REPRESENTS, not only ``Meta.indexes``: unconditional field-based
    ``Meta.indexes``, ``Meta.constraints`` unique constraints, legacy
    ``unique_together``, and field-level primary-key / unique / ``db_index``
    columns (``_model_index_shapes``). A covering ``UniqueConstraint`` therefore
    correctly silences the advisory. That metadata is the table-owning model's
    (``_meta.concrete_model``): a proxy target (or a proxy of a proxy) declares
    none of its own, so its window is inspected, recommended and deduplicated as
    its concrete model's.

    This is advisory ONLY: it never raises, and logs at ``WARNING`` only under
    ``settings.DEBUG`` (``DEBUG`` off -> ``debug``). It stays SILENT unless
    absence is proven from fully-inspectable metadata. That fail-soft tri-state
    spans BOTH ends of the comparison: a non-B-tree / expression / partial index
    (or any shape the represented metadata cannot classify) leaves index
    coverage UNKNOWN, AND an effective ORDER term that is not a child-table
    column (a related span through a join, an inherited column, a
    ``Lower("title")`` expression, an alias, an unresolvable name -
    ``_concrete_order_terms`` returns ``None``) leaves the SQL order only
    partially understood; either UNKNOWN keeps the advisory silent
    so it never claims coverage from - or recommends an index covering only - the
    remaining suffix. A DBA-created index absent from Django model metadata is
    never visible here, so the wording frames the recommendation as advisory
    rather than asserting the index does not exist.

    Called once per plan shape from ``plan_connection_relation`` AFTER the first
    window a strategy accepts (a strategy that refuses every window plans no
    window, so it must advise no window index); cross-request plan caching
    handles the cached shapes, and the bounded ``_emit_index_advisory`` cache
    handles the request-scoped shapes a custom ``get_queryset`` keeps OUT of that
    cache, so a given ``(model, equality prefix, order terms)`` shape warns at
    most once.
    """
    if join.partition_expr is None:
        return
    # A proxy shares its concrete model's table, but Django keeps ``Meta.indexes``,
    # ``Meta.constraints`` and ``unique_together`` only on the declaring class, and
    # ``models.E016`` refuses a proxy declaring any: the table's indexes, the model the
    # recommendation names and the dedup identity are all the concrete model's.
    table_model = require(related_model._meta.concrete_model, is_model_class)
    partition_field = _window_column(table_model, join.partition_expr)
    if partition_field is None:
        return
    equality: list[str] = []
    if join.content_type_column is not None:
        content_type_field = _window_column(table_model, join.content_type_column)
        if content_type_field is None:
            return
        append_unique(equality, content_type_field.attname)
    append_unique(equality, partition_field.attname)
    order_terms = _concrete_order_terms(order_by, table_model)
    if order_terms is None:
        # Order-parsing UNKNOWN dominates: some effective ordering term is not a
        # child-table ``(attname, direction)`` (or carries explicit NULLS
        # placement), so no index on the child's table serves the SQL order - stay
        # silent rather than claim a false coverage or recommend an index that
        # omits or misplaces the unrepresented term.
        return
    # The window equality-constrains every ``equality`` column (the partition
    # column, and for a ``GenericRelation`` the ``content_type_id`` morph
    # column), so each is CONSTANT within a partition and contributes nothing to
    # the within-partition order. Strip them to the EFFECTIVE order before
    # comparison and rendering, or an order like ``parent_id, title, id`` would
    # be checked against - and recommended as - ``(parent_id, parent_id, title,
    # id)``, falsely reporting the real ``(parent_id, title, id)`` index absent
    # and naming a duplicated column.
    equality_columns = set(equality)
    effective_order = [term for term in order_terms if term[0] not in equality_columns]
    if _index_coverage(table_model, equality, effective_order) != _INDEX_ABSENT:
        return
    _emit_index_advisory(
        table_model._meta.app_label,
        table_model._meta.object_name,
        tuple(equality),
        tuple(effective_order),
    )


def _project_scalar_only_window(
    child_queryset: QuerySet[_M],
    django_field: FieldMeta,
    order_by: Sequence[object],
    *,
    introduce_projection: bool,
) -> QuerySet[_M]:
    """Restrict a scalar-only connection window to pk / connector / order columns.

    A ``pageInfo``-only or ``totalCount``-only selection unwraps to ``[]`` node
    children, so the child plan adds no ``.only()`` and the window would fetch
    full model rows even though the page needs only the target pk (Relay edge
    identity), the relation connector column (Django's prefetch attach), and the
    concrete ordering columns the deterministic window order references
    (spec-033 Decision 4 / Decision 6 scalar-only contract). The ``_dst_*`` window annotations
    compose with ``.only()`` (annotations, not deferred columns). The projection is written
    through ``apply_projection``, so a JOIN the child type's hook added keeps the connector
    it traverses.

    This direct projection never touches ``OptimizationPlan.only_fields``, so it
    carries the plan's ``introduce_projection`` itself: under a non-``QUERY``
    operation it only widens a projection the child queryset already carries.
    """
    related_model = require(django_field.related_model, is_model_class)
    fields: list[str] = []
    append_unique(fields, related_model._meta.pk.attname)
    # Attach-complete set from one classify (connector + GenericRelation morph).
    # Django's ``GenericRelatedObjectManager.get_prefetch_querysets`` attaches by
    # ``(object_id, content_type_id)``; masking either half deferred-refetches
    # once per row (N+1 sync / ``SynchronousOnlyOperation`` async). Same
    # ``prefetch_attach_columns`` owner as ``walker._ensure_connector_only_fields``.
    for column in classify_relation_join(django_field).prefetch_attach_columns:
        append_unique(fields, column)
    for column in _concrete_order_columns(order_by, related_model):
        append_unique(fields, column)
    return apply_projection(child_queryset, fields, introduce=introduce_projection)


def _int_argument(arguments: Mapping[str, object], name: str) -> int | None:
    """Return the Python-named ``Int`` page argument ``name``, ``None`` when it was not given.

    The payload is graphql-core-coerced (``selections.py::python_arguments``), so a
    given ``Int`` argument is already an ``int``.
    """
    value = arguments.get(name)
    return value if isinstance(value, int) else None


def _cursor_argument(arguments: Mapping[str, object], name: str) -> str | None:
    """Return the Python-named ``String`` cursor argument ``name``, ``None`` when it was not given.

    The payload is graphql-core-coerced, so a given ``String`` argument is a ``str``.
    """
    value = arguments.get(name)
    return value if is_str(value) else None


def _connection_window_slice_from_arguments(
    arguments: Mapping[str, object],
    info: GraphQLResolveInfo[object] | None,
) -> ConnectionWindowBounds | None:
    """Resolve the window bounds from one argument payload.

    Returns the ``ConnectionWindowBounds`` the shared derivation already built,
    rather than immediately destructuring it into an anonymous 3-tuple: the
    tuple carried the same three fields with none of their names, and every
    consumer down the chain had to re-spell ``(offset, limit, reverse)`` in the
    right order to get them back.


    The planner-side adapter over the shared
    ``utils/connections.py::derive_connection_window_bounds`` contract (so the
    plan-time and resolve-time windows can never drift). Both window schemes
    iterate this: the shared-window scheme with one payload, the per-key
    scheme with each response key's recorded payload
    (``_optimizer_response_key_arguments``). Reads the payload by Python name
    (graphql-core coerced it, ``selections.py::python_arguments``) and hands it
    to the shared helper, which reads the cap from the Strawberry schema config
    and owns the ``reverse`` / ``limit`` rule.

    Returns ``None`` when the shared helper raises ``PaginationArgumentError``
    (negative / over-max ``first`` / ``last``, malformed cursor) so
    ``plan_connection_relation`` leaves the selection UNPLANNED and the shipped
    nested field path raises at its own error locality (spec-033's error shapes). No
    other pagination exception can arise here: ``decode_offset_cursor`` folds
    every undecodable cursor, a non-``str`` one included, into that rejection,
    and once the validator has returned ``SliceMetadata.from_arguments`` has
    nothing left to reject. The walker only declines to plan: it constructs no
    error of its own. The resolver calls the same helper directly with
    Strawberry's arguments and lets the pagination error propagate instead.

    ``UnwindowableConnection`` (an offset-bearing backward or inverted interval)
    is deliberately NOT caught here: it is a VALID query that resolves correctly
    per-parent, so ``plan_connection_relation`` must treat it as a fully-unplanned
    Decision-6 fallback (no ``planned_resolver_keys`` entry, like the sidecar /
    distinct shapes) rather than the malformed-pagination ``None`` path that
    records the field as accounted-for (spec-033 Decision 5).
    """
    try:
        return derive_connection_window_bounds(
            info,
            before=_cursor_argument(arguments, "before"),
            after=_cursor_argument(arguments, "after"),
            first=_int_argument(arguments, "first"),
            last=_int_argument(arguments, "last"),
            # Only generated connections are planned, and each inherits the stock edge class.
            prefix=relay.Edge.CURSOR_PREFIX,
        )
    except PaginationArgumentError:
        return None


def _keyset_window_slice_from_arguments(
    arguments: Mapping[str, object],
    info: GraphQLResolveInfo[object] | None,
    *,
    columns: tuple[CursorColumn, ...],
    fingerprint: str,
) -> tuple[ConnectionWindowBounds, KeysetSeek | None] | None:
    """Resolve one keyset window ``(bounds, seek)`` per payload.

    The keyset twin of ``_connection_window_slice_from_arguments``, forking
    BEFORE the offset engine (``SliceMetadata`` cannot parse a value cursor):
    bounds come from the shared ``derive_keyset_window_bounds`` (the same
    helper the resolve side consumes, so the two windows agree by
    construction) and the ``after:`` cursor decodes through the canonical
    codec. Error contract mirrors the offset adapter:

    - ``None`` for malformed pagination - a negative / over-cap ``first`` or
      an invalid / tampered / wrong-order cursor (both a
      ``PaginationArgumentError``). The caller records the field as
      accounted-for and the per-parent pipeline raises the SAME error at
      the field's own locality.
    - ``UnwindowableConnection`` propagates for the valid backward shapes
      (``last`` / ``before:``) the keyset window does not plan - a real
      per-parent access that must stay strictness-visible.
    """
    first = _int_argument(arguments, "first")
    last = _int_argument(arguments, "last")
    after = _cursor_argument(arguments, "after")
    before = _cursor_argument(arguments, "before")
    seek: KeysetSeek | None = None
    try:
        # Validate both cursors before classifying a valid backward shape as
        # unwindowable. Otherwise strictness can mask malformed ``before:``
        # (or ``after:`` + ``last``) input as an unplanned N+1.
        if after is not None:
            cursor = decode_keyset_cursor(
                after,
                columns,
                fingerprint=fingerprint,
                argument="after",
            )
            seek = KeysetSeek(columns=columns, cursor=cursor)
        if before is not None:
            _ = decode_keyset_cursor(
                before,
                columns,
                fingerprint=fingerprint,
                argument="before",
            )
        bounds = derive_keyset_window_bounds(
            info,
            before=before,
            after=after,
            first=first,
            last=last,
        )
    except (GraphQLError, ValueError, TypeError):
        return None
    return bounds, seek


def _divergent_key_windows(
    response_key_arguments: Mapping[str | None, Mapping[str, object]],
    info: GraphQLResolveInfo[object] | None,
    keyset_context: CursorState | None = None,
) -> _WindowPass:
    """Resolve one window per payload for a nested connection selection.

    The arguments-derived window pass for both schemes. The caller supplies
    the payload map: per-response-key arguments
    (``_optimizer_response_key_arguments``) when aliases diverge, or
    ``{None: arguments}`` for the shared-window scheme (unmerged selections
    never grow that attribute, so this helper must not read it off ``sel``).

    Iterate the map and run the ARGUMENTS-DERIVED fallback gates per payload
    - each entry is its own windowed fetch (the graph-node model: one batched
    children query per response key, or one shared fetch when the key is
    ``None``), so one alias's refusal must not drag its siblings per-parent:

    - sidecar input (``filter`` / ``order_by``) -> that key stays UNPLANNED
      (per-parent, strictness-visible), siblings unaffected;
    - ``UnwindowableConnection`` (``after`` + ``last``; inverted offset interval;
      every backward keyset shape) -> likewise that key alone falls back
      per-parent;
    - malformed pagination -> that key is returned in ``malformed`` so the
      caller records ONLY its identities (per-key error locality: the
      per-parent pipeline raises that alias's own validation error). A
      ``None`` key is the shared-window scheme: the caller records every
      identity, matching the single-window write;
    - otherwise the key's ``ConnectionWindowBounds`` window joins ``planned``.

    ``keyset_context`` - the cursor vocabulary of the window's effective
    order (``plans.py::effective_cursor_state``) - routes every key through
    the keyset window adapter instead (each alias decodes its OWN ``after:``
    cursor into its own seek under that vocabulary); the entry shape gains
    that seek (``None`` under the offset vocabulary and for keyset first
    pages alike).

    Returns ``(planned, malformed, fallbacks)``; each fallback carries its
    stable reason for the caller's debug log. Relation-level gates (hint
    SKIP, join windowability, child-queryset safety) stay whole-relation in
    ``plan_connection_relation``.
    """
    planned: list[_KeyedWindow] = []
    malformed: list[str | None] = []
    fallbacks: list[tuple[str | None, str]] = []
    for resp_key, key_arguments in response_key_arguments.items():
        if has_connection_sidecar_kwargs(key_arguments):
            fallbacks.append((resp_key, "sidecar arguments"))
            continue
        seek: KeysetSeek | None = None
        try:
            if keyset_context is not None:
                keyed = _keyset_window_slice_from_arguments(
                    key_arguments,
                    info,
                    columns=keyset_context.columns,
                    fingerprint=keyset_context.fingerprint,
                )
                window = keyed[0] if keyed is not None else None
                seek = keyed[1] if keyed is not None else None
            else:
                window = _connection_window_slice_from_arguments(key_arguments, info)
        except UnwindowableConnection:
            fallbacks.append((resp_key, "unsupported pagination window"))
            continue
        if window is None:
            malformed.append(resp_key)
            continue
        planned.append((resp_key, window, seek))
    return planned, malformed, fallbacks


def _log_connection_fallback(
    relation_field_name: str,
    response_keys: Sequence[str | None],
    reason: str,
) -> None:
    """Log each response key that will use the per-parent connection pipeline."""
    for resp_key in dict.fromkeys(response_keys):
        logger.debug(
            "Optimizer: nested connection %s response key %r falls back "
            "to per-parent resolution (%s).",
            relation_field_name,
            resp_key,
            reason,
        )


def _identities_for_response_keys(
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
    response_keys: list[str | None],
) -> tuple[str, ...]:
    """Filter parallel ``(runtime_paths, resolver_identities)`` to given keys.

    ``_resolver_identities_for`` already builds identities per response key
    (the cartesian ``runtime_prefixes x response_keys(sel)``; each runtime
    path ENDS in its response key), so per-key selection is a filter over the
    parallel tuples, never a re-derivation. Used by the divergent-alias scheme
    to record identities only for the keys actually planned (or, for
    malformed keys, accounted-for).
    """
    wanted = set(response_keys)
    return tuple(
        identity
        for runtime_path, identity in zip(runtime_paths, resolver_identities, strict=True)
        if runtime_path[-1] in wanted
    )


def _settle_window_pass(
    window_pass: _WindowPass,
    plan: OptimizationPlan,
    sel: FieldSelection,
    *,
    relation_field_name: str,
    divergent: bool,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
) -> list[_KeyedWindow]:
    """Log one window pass's fallbacks, record its malformed keys, return its windows.

    Malformed pagination emits NO window so the connection pipeline raises its
    pagination error at the field, but RECORDS the identities as planned so
    strictness does not preempt that error (spec-033 Decision 8). Per-key under the
    divergent scheme (that alias's own error locality; siblings plan
    independently); every identity for the shared window (``None`` is not a
    runtime_path suffix, so the filter would drop them all).
    """
    keyed_windows, malformed_keys, fallback_keys = window_pass
    for fallback_key, reason in fallback_keys:
        _log_connection_fallback(
            relation_field_name,
            [fallback_key] if fallback_key is not None else response_keys(sel),
            reason,
        )
    if malformed_keys:
        _log_connection_fallback(
            relation_field_name,
            malformed_keys if divergent else response_keys(sel),
            "malformed pagination",
        )
        _record_accounted_keys(
            plan,
            malformed_keys,
            divergent=divergent,
            runtime_paths=runtime_paths,
            resolver_identities=resolver_identities,
        )
    return keyed_windows


def _record_accounted_keys(
    plan: OptimizationPlan,
    response_keys: list[str | None],
    *,
    divergent: bool,
    runtime_paths: tuple[tuple[str, ...], ...],
    resolver_identities: tuple[str, ...],
) -> None:
    """Record ``response_keys`` as accounted for: the field raises its own error per parent.

    Per-key under the divergent scheme; every identity for the shared window
    (``None`` is not a runtime_path suffix, so the filter would drop them all).
    An empty ``response_keys`` records nothing.
    """
    if not response_keys:
        return
    append_unique_many(
        plan.planned_resolver_keys,
        _identities_for_response_keys(runtime_paths, resolver_identities, response_keys)
        if divergent
        else resolver_identities,
    )


def plan_connection_relation(
    sel: FieldSelection,
    definition: DjangoTypeDefinition | None,
    *,
    relation_field_name: str,
    field_map: Mapping[str, FieldMeta],
    prefix: JoinPrefix,
    info: GraphQLResolveInfo[object] | None,
    runtime_prefixes: tuple[tuple[str, ...], ...],
    type_cls: type[DjangoType] | None,
    model: type[models.Model],
    introduce_projection: bool,
    build_child_queryset: Callable[..., QuerySet[models.Model]],
    build_prefetch_child_queryset_from_base: Callable[..., QuerySet[models.Model]],
) -> OptimizationPlan:
    """Plan one recognized nested connection as a windowed ``Prefetch``.

    Orchestrates the windowed-prefetch plan (spec-033 Decision 4); leaves the
    selection UNPLANNED (no ``Prefetch``, no ``planned_resolver_keys`` entry) for
    each spec-033 Decision 6 refusal arm so the strictness contract still sees
    the per-parent access. Delegates child-queryset construction to the same
    helper the list path uses (``_build_child_queryset``, reached here through
    ``_build_connection_child_queryset`` so the child's visibility seal spends the
    slice licence this path's own gate below answers for); the only addition is
    the window applied after ``child_plan.apply``.

    ``prefix`` spells the JOIN path above the relation in the two vocabularies
    the walker carries (``plans.py::JoinPrefix``): query names for the
    parent-row link columns, accessors for the window's ``Prefetch`` lookup.

    Every decision about the relation TARGET spends one resolution.
    ``_resolve_relation_target`` answers with the child definition beside its
    origin, and that object - never a fresh read of the target class - decides
    the ``get_queryset`` downgrade, supplies the model the child's visibility
    seal validates against, and fixes the declared cursor vocabulary each
    window's effective-order vocabulary derives from. A synthesized relation
    connection's resolver already takes its definition from the registry at
    finalization; planning the same field at request time reads the same
    one answer, so a target whose metadata changed after acceptance cannot
    answer the plan differently from the resolver - including on the
    ``has_custom_get_queryset`` verdict that decides whether the child's
    visibility hook runs before the window is built.
    """
    plan = OptimizationPlan(introduce_projection=introduce_projection)
    django_field = field_map.get(relation_field_name)
    if django_field is None:
        return plan
    # Parent-row link columns (a reverse ``to_field`` / ``ForeignObject``
    # link's non-pk targets). The window's attach reads them off each parent
    # row, and so does the per-parent resolution every refusal arm below - and
    # a SKIP hint - leaves the relation to, so they load before the first of
    # those arms, as in ``walker.py::_record_relation_carriers``. Only a field
    # the map does not carry leaves them unloaded.
    append_unique_many(
        plan.only_fields,
        [f"{prefix.query}{attname}" for attname in django_field.source_link_attnames],
    )
    hints_map = definition.optimizer_hints if definition is not None else {}
    if hint_is_skip(hints_map.get(relation_field_name)):
        return plan
    # (b) Refusal arms detectable before any queryset is built -> UNPLANNED.
    if _response_key_arguments_conflict(sel):
        _log_connection_fallback(
            relation_field_name,
            response_keys(sel),
            "conflicting arguments for one response key",
        )
        # ONE response key carries two different argument payloads - reachable
        # only when different parent-alias subtrees were union-merged (their
        # same-named children land in one merged selection). Neither scheme
        # can serve it: the shared window has one payload slot, and the
        # per-key scheme routes by response key, which is the very thing that
        # collides. Stay FULLY unplanned (no window, no resolver identities)
        # so each alias subtree's per-parent resolution applies its OWN
        # arguments and the access stays strictness-visible, like the sidecar
        # shapes. A silent first-payload-wins window here served the sibling
        # alias a wrong page.
        return plan
    # Scheme selector only (payload map + identity writes). Arguments-derived
    # gates including sidecar run per payload inside ``_divergent_key_windows``,
    # after the relation-level identities / related_model gates below.
    divergent = _aliased_arguments_diverge(sel)

    target_type, target_definition = _resolve_relation_target(
        definition,
        relation_field_name,
        django_field,
    )
    has_custom_get_queryset = _target_has_custom_get_queryset(target_type, target_definition)

    runtime_paths, resolver_identities = _resolver_identities_for(
        sel,
        relation_field_name,
        type_cls,
        runtime_prefixes,
    )

    if django_field.related_model is None:
        return plan

    # Keyset context (the ``cursor_field`` opt-in): when the relation target
    # is keyset-mode, every window below derives through the keyset adapter
    # (value-cursor decode + forward-only bounds) instead of the offset
    # engine, under the cursor vocabulary of the window's EFFECTIVE order
    # (step d below) - the declared ``cursor_field`` when nothing else orders
    # the child queryset, else the order a target ``get_queryset`` / manager
    # imposed, exactly as the root slicer resolves it.
    keyset_context = declared_cursor_state_for_definition(target_definition)

    # A target set with a ``required`` own filter has no unbound form
    # (``FilterSet._requires_bound_form``): its filter step runs on every
    # request, ``filter:`` supplied or not, so no payload can be served from a
    # window. The relation stays UNPLANNED and strictness-visible, like the
    # sidecar shapes.
    filterset_class = None if target_definition is None else target_definition.filterset_class
    if filterset_class is not None and filterset_class._requires_bound_form():
        _log_connection_fallback(
            relation_field_name,
            response_keys(sel),
            "target filter set has a required filter",
        )
        return plan

    # (e/f) Slice window(s) from the selection's resolved pagination arguments.
    # Pure (mutates nothing), so resolve BEFORE the child build - a malformed
    # slice must not leave child resolver keys / cacheable flips on the parent
    # plan. Both schemes feed ``_divergent_key_windows``: per-key payloads when
    # aliases diverge, ``{None: arguments}`` for the shared window (unmerged
    # selections never grew ``_optimizer_response_key_arguments``).
    # ``keyed_windows`` stays the scheme-agnostic hand-off: ``None`` keeps the
    # shared ``to_attr``; a real key namespaces it. ``seek`` is the
    # decoded keyset value seek, ``None`` under the offset vocabulary and for
    # keyset first pages alike.
    response_key_arguments: Mapping[str | None, Mapping[str, object]] = (
        # Diverging aliases exist only on the walker's merged ``SimpleNamespace``, whose
        # alias merge stored this map; read by name because the other selection shape
        # declares no such attribute.
        getattr(sel, "_optimizer_response_key_arguments")  # noqa: B009 - the attribute exists only on the merged namespace
        if divergent
        else {None: python_arguments(sel)}
    )
    argument_pass = _divergent_key_windows(response_key_arguments, info, keyset_context)

    def settle(window_pass: _WindowPass) -> list[_KeyedWindow]:
        return _settle_window_pass(
            window_pass,
            plan,
            sel,
            relation_field_name=relation_field_name,
            divergent=divergent,
            runtime_paths=runtime_paths,
            resolver_identities=resolver_identities,
        )

    # The offset vocabulary is fixed, so its pass settles here. A keyset pass
    # decodes cursors under the DECLARED vocabulary, which is the window's only
    # when step (d) finds no other order. With no planned and no malformed key
    # no vocabulary can change its outcome, so it settles here too and the
    # child queryset is never built. Otherwise it settles at the first refusal
    # below (a refused relation is judged under the declared vocabulary), or
    # after step (d), where a differing effective order re-runs the pass under
    # ITS vocabulary (``keyed_windows`` stays empty until then).
    keyed_windows: list[_KeyedWindow] = []
    if keyset_context is None or not (argument_pass[0] or argument_pass[1]):
        keyed_windows = settle(argument_pass)
        if not keyed_windows:
            return plan

    # (g, partition) pure; classify the join before the child build so an
    # unsupported relation kind (single-valued forward, or a shape with no
    # resolvable parent partition) falls back without leaking child metadata.
    # The partition derivation reads the RAW field from ``_meta`` (spec-033
    # Decision 4): the forward-M2M reverse query name lives only on its
    # ``remote_field``, which ``FieldMeta`` does not carry. The raw field also
    # rides the strategy request: the lateral backend reads ``remote_field`` /
    # through metadata that only the raw descriptor carries.
    raw_relation_field = model._meta.get_field(relation_field_name)
    join = classify_relation_join(raw_relation_field)
    if not join.windowable:
        if keyset_context is not None:
            _ = settle(argument_pass)
        return plan

    # (a) Unwrap edges { node }; scalar-only selections plan with [] node children.
    # ``runtime_paths`` spans ALL response keys (per-key child selections are
    # not preserved by the merge), so under the divergent scheme the child
    # plan records nested identities under an UNPLANNED sibling key's paths
    # too. Deliberate conservatism: that sibling's per-parent pipeline plans
    # its own subtree, so those nested accesses never lazy-load - the
    # imprecision can only mask a strictness flag, never serve wrong data. The
    # unwrap and both count observers below match the connection's own fields by
    # Python name (``selections.py::selection_python_name``), whatever wire names
    # the schema's ``NameConverter`` publishes them under.
    node_selections = connection_node_children(sel, runtime_prefixes=runtime_paths)
    scalar_only = not node_selections
    node_sel = SimpleNamespace(selections=node_selections)

    # (c, pre-build safety gate) the base child queryset comes from consumer
    # code even without a target ``get_queryset``: a custom default manager's
    # ``.all()`` can still return distinct/sliced/combined/values/locking
    # shapes no fetch strategy can window. Build that base exactly once,
    # classify it unconditionally, and feed the same value into child-plan
    # application on the success path.
    base_queryset = build_child_queryset(
        django_field,
        target_type,
        info,
        target_definition=target_definition,
    )
    if unwindowable_child_queryset_reason(base_queryset) is not None:
        if keyset_context is not None:
            _ = settle(argument_pass)
        return plan

    # (c) Build the child plan/queryset exactly like the list prefetch path, but
    # against a THROWAWAY sub-plan so a strategy refusal below (spec-033 Decision 6,
    # the every-response-key strategy refusal) can fall back without leaking the
    # child's resolver keys / fk-id elisions / cacheable flip into the parent. The
    # parent plan absorbs the child metadata only on the success path.
    sub_plan = OptimizationPlan(introduce_projection=introduce_projection)
    if has_custom_get_queryset:
        sub_plan.cacheable = False
    child_queryset = build_prefetch_child_queryset_from_base(
        node_sel,
        django_field,
        sub_plan,
        info,
        runtime_paths,
        base_queryset=base_queryset,
    )
    # GenericRelation morph predicate: NOT injected at plan time. The window
    # partitions by the child ``object_id`` column alone, so the parent's morph
    # content type must still constrain the scan - but resolving a ``ContentType``
    # here is alias-EARLY and DB I/O in the planner: the child queryset is
    # unrouted (``_default_manager.all()``, ``_db is None``), so ``.db`` asks the
    # router without the parent-instance hint and commonly returns ``default``,
    # baking a constant that is wrong under a divergent router (the ct pk can
    # differ per shard) AND a cached plan preserves; on a cold ``ContentType``
    # cache under async execution the lookup can raise ``SynchronousOnlyOperation``.
    # Django's own ``GenericRelatedObjectManager.get_prefetch_querysets`` adds the
    # correct alias-late predicate at fetch time - ``.using(queryset._db or
    # self._db)`` picks the parent instances' alias, ``get_content_type(obj)``
    # resolves the ct against THAT alias, and ``queryset.filter(
    # content_type__pk=..., object_id__in=...)`` is a base-column WHERE that
    # Django's qualify wrapping keeps INSIDE the window subquery (verified against
    # the compiled SQL: the morph predicate lands in the ``FROM`` the
    # ``ROW_NUMBER``/``COUNT`` windows partition over, only the row-number range
    # filter is pushed outside). Re-deriving it here would only DUPLICATE that
    # predicate with a possibly-wrong constant; the lateral backend refuses the
    # generic join (``parent_link_field=None``) and runs this same windowed body,
    # so both paths inherit Django's fetch-time morph. The ``for_concrete_model``
    # an MTI parent needs is honored by Django's manager too.
    # No post-build re-check: the classified base queryset is the single
    # strategy-independent gate; later child-plan application only adds the
    # package's optimizer directives.

    # (d) Deterministic total order shared with the resolve-time pipeline. The
    # precedence ladder - a keyset target's declared ``cursor_field`` when
    # nothing orders the child queryset (a sidecar-bearing connection is never
    # window-planned, so the only other order here is a target ``get_queryset``
    # / manager ``order_by``), else child-queryset / model ``Meta.ordering``
    # through ``deterministic_order`` - lives ONCE in
    # ``plans.py::effective_connection_order`` so this plan-time window order
    # and ``connection.py::_finalize_queryset`` cannot drift (the cursor-parity
    # invariant). ``QuerySet.order_by`` admits only a field-name string or an
    # expression (Django requires ``resolve_expression`` of anything else), which
    # django-stubs spells ``str | Combinable``; the window takes it as ``OrderEntry``.
    # A target ``get_queryset`` / manager ``extra(order_by=...)`` ordering is first
    # rewritten as the ``order_by`` terms it compiles as, and a ``.reverse()``
    # materialized as the reverse of the forward total order under the forward flag
    # (``plans.py::normalize_order_direction``), so the order read below is the
    # order the window's ``RowNumber`` and its ``ORDER BY`` both compile.
    window_cursor_field = keyset_context.cursor_field if keyset_context is not None else None
    child_queryset = normalize_order_direction(
        child_queryset,
        window_cursor_field,
        django_field.related_model,
    )
    order_by = cast(
        "list[OrderEntry]",
        list(
            effective_connection_order(
                window_cursor_field,
                child_queryset.query,
                django_field.related_model,
            ),
        ),
    )

    # The keyset cursor vocabulary of THAT order (``plans.py::effective_cursor_state``,
    # the one derivation the root slicer runs): the columns every ``after:``
    # cursor decodes into and seeks by, and the fingerprint every minted cursor
    # carries, so a window cursor is byte-identical to the root's and the
    # per-parent pipeline's for the same row. An order no value cursor can
    # anchor (an expression, a nullable or hidden-related column) leaves the
    # relation UNPLANNED: the per-parent pipeline resolves it and raises the
    # same keyset ``GraphQLError`` at the field the root path would.
    keyset_window_state: CursorState | None = None
    if keyset_context is not None:
        try:
            keyset_window_state, cursor_annotations = effective_cursor_state(
                keyset_context,
                order_by,
            )
        except GraphQLError:
            _ = settle(argument_pass)
            _log_connection_fallback(
                relation_field_name,
                response_keys(sel),
                "keyset order cannot anchor cursors",
            )
            # Every key this order governs raises that keyset error per parent,
            # so it is recorded as accounted for (like malformed pagination):
            # strictness must not preempt the field's own error with an N+1
            # error. A sidecar key stays strictness-visible: its ``orderBy:`` /
            # ``filter:`` is the shipped per-parent fallback.
            sidecar_keys = {
                key for key, reason in argument_pass[2] if reason == "sidecar arguments"
            }
            _record_accounted_keys(
                plan,
                [key for key in response_key_arguments if key not in sidecar_keys],
                divergent=divergent,
                runtime_paths=runtime_paths,
                resolver_identities=resolver_identities,
            )
            return plan
        if cursor_annotations:
            child_queryset = child_queryset.annotate(**cursor_annotations)
        # The declared vocabulary IS the window's (the same object) -> the
        # argument pass already decoded under it; otherwise re-decode every
        # key's cursors under the effective order's columns and fingerprint.
        keyed_windows = settle(
            argument_pass
            if keyset_window_state is keyset_context
            else _divergent_key_windows(response_key_arguments, info, keyset_window_state),
        )
        if not keyed_windows:
            return plan

    # The window numbers its rows by ``Query.resolve_ref``, which reads a relation
    # name as its key column, while the statement's ``ORDER BY`` (and the
    # per-parent pipeline) compile it into the related model's ``Meta.ordering``:
    # every reader below takes the order as the compiler runs it
    # (``utils/querysets.py::expand_relation_order``). The keyset vocabulary
    # above keeps the terms as written, as the root slicer does.
    order_by = expand_relation_order(order_by, child_queryset.query)
    # A random order (``"?"`` or ``Random()``, ``plans.py::has_random_term``) is
    # a fresh draw each time the database evaluates it, and the window evaluates
    # its order more than once per statement, so no window can serve one page of
    # ONE permutation. The per-parent pipeline orders each page query once:
    # leave the relation to it. A keyset order never reaches here random - the
    # cursor vocabulary above refuses it first, with its own error.
    if has_random_term(order_by, child_queryset):
        _log_connection_fallback(relation_field_name, response_keys(sel), "random order")
        return plan

    # A scalar-only (pageInfo/totalCount) selection unwrapped to [] node children,
    # so the child plan added no `.only()` projection; restrict it to the minimal
    # pk/connector/order columns now that the deterministic order is known
    # (spec-033 Decision 4 / Decision 6 scalar-only contract) rather than fetching full child rows.
    if scalar_only:
        child_queryset = _project_scalar_only_window(
            child_queryset,
            django_field,
            order_by,
            introduce_projection=introduce_projection,
        )
    elif keyset_window_state is not None:
        # Keyset edges mint cursors from the rows' ORDERING-COLUMN VALUES
        # (not the row-number annotation), so the local cursor columns must be
        # loaded on every page row - extend a node-selection ``.only()``
        # projection that did not select them as GraphQL fields (the
        # scalar-only branch above already carries its order columns; a
        # related-path column rides its annotation instead).
        child_queryset = apply_projection(
            child_queryset,
            local_cursor_attnames(keyset_window_state),
            introduce=False,
        )

    # Conditional total count (spec-033 Decision 4) + count-free ``hasNextPage``
    # (the n+1 overfetch probe): annotate the per-partition ``Count(1) OVER``
    # only when something needs it. The two selection observers come from the
    # shared per-selection walks (``selections.py``), computed ONCE here and
    # reused for the single fetch-mode decision. Both the count and the probe are
    # DERIVED from one
    # ``WindowRangePlan.fetch_mode`` value below - the shared ``FetchMode``
    # source of truth - so the two decisions cannot drift from each other or
    # from the resolver's physical-shape reads. The decision is made HERE only:
    # ``sel`` is the merged (union) selection when aliases share this relation,
    # so the resolver must not re-derive the mode per response key - it reads it
    # back off the window's physical shape (count annotation absent on a
    # probe-eligible page), which stays truthful only while ``FetchMode``'s
    # ``PROBED`` and ``COUNTED`` stay mutually exclusive (``_resolve_from_window``
    # documents that invariant; the ``NestedConnectionRequest`` seam enforces it
    # per window). Under the divergent scheme the observers stay
    # UNION-conservative on purpose: a sibling alias selecting ``totalCount``
    # keeps every per-key window on the count (no probe) - correct for each
    # window, one shared decision input.
    total_selected = connection_total_count_selected(sel)
    has_next_selected = connection_has_next_page_selected(sel)
    # (g) Hand one fully-resolved fetch request PER WINDOW to the active
    # strategy (the nested_fetch.py seam): the single-window scheme sends the
    # shared-``to_attr`` request; the divergent scheme sends one
    # request per response key under that key's namespaced ``to_attr`` (the
    # graph-node model - O(aliases) batched queries instead of
    # O(parents x aliases) per-parent fallbacks). A strategy returning
    # ``False`` leaves that window unplanned, keeping the spec-033 Decision 6
    # strictness contract (no resolver identities recorded for it).
    # Per-field strategy selection: a
    # ``OptimizerHint.strategy(name)`` overrides the extension default; otherwise
    # the active strategy applies. It is field-static (the same for every keyed
    # window), so resolve it once here rather than per window. The
    # composite-index advisory is likewise field-static, but it is emitted from INSIDE
    # the loop, only after the FIRST window a strategy accepts - a public
    # consumer-authored strategy may return ``False`` for every window (no nested
    # window planned, the per-parent fallback runs), and advising a composite
    # WINDOW index for a backend that will not run is confusing under strictness.
    # It still fires at most ONCE per plan build (the ``advised`` latch): the
    # recommendation is identical for every keyed window. Across requests it
    # self-dedupes on ``(model, equality prefix, order terms)`` so a request-scoped
    # plan a custom ``get_queryset`` keeps out of the cross-request plan cache
    # (rebuilt every request) still warns at most once, honoring the "one advisory
    # per plan shape" promise.
    strategy = _select_nested_strategy(hints_map.get(relation_field_name))
    planned_keys: list[str | None] = []
    advised = False
    for resp_key, bounds, window_seek in keyed_windows:
        range_plan = window_range_plan(
            offset=bounds.offset,
            limit=bounds.limit,
            reverse=bounds.reverse,
        )
        # Count policy, derived
        # from the ONE shared ``FetchMode`` value instead of two independent
        # expressions: ``COUNTED`` annotates the per-partition ``Count(1) OVER``
        # (``totalCount`` observed, or the ``first: 0`` marker shape); ``PROBED``
        # overfetches one sentinel row (``fetch_*`` bounds) so its presence
        # answers ``hasNextPage`` without a partition scan (plain-first / bounded
        # offset page); ``CONSTANT_FALSE`` / ``NONE`` need neither (unbounded
        # forward and reversed pages end at the partition tail; an edges-only page
        # observes no count-derived field). ``fetch_mode`` reads ``range_plan``'s
        # already-normalized ``limit`` (``window_range_plan`` folded the loop-local
        # ``sys.maxsize`` bound to ``None``), so the ``first: 0`` check is exact.
        mode = range_plan.fetch_mode(
            has_next_selected=has_next_selected,
            total_selected=total_selected,
        )
        with_total_count = mode is FetchMode.COUNTED
        next_page_probe = mode is FetchMode.PROBED
        request = NestedConnectionRequest(
            django_field=raw_relation_field,
            relation_field_name=relation_field_name,
            prefix=prefix.query,
            child_queryset=child_queryset,
            join=join,
            order_by=tuple(order_by),
            offset=bounds.offset,
            limit=bounds.limit,
            reverse=bounds.reverse,
            with_total_count=with_total_count,
            next_page_probe=next_page_probe,
            keyset_seek=window_seek,
            to_attr=relation_connection_to_attr(relation_field_name, resp_key),
            lookup=f"{prefix.accessor}{instance_accessor(django_field)}",
        )
        strategy_plan = OptimizationPlan()
        if strategy.plan(request, strategy_plan):
            plan.merge_from(strategy_plan)
            planned_keys.append(resp_key)
            # The bounds this window was fetched under (and, for a keyset
            # window, the vocabulary its cursors must be minted under),
            # published with the plan under each resolver key the window
            # serves (the same keys ``planned_resolver_keys`` records), so the
            # relation-connection resolver reads back its own window however
            # its relation name repeats elsewhere.
            plan.planned_windows.update(
                dict.fromkeys(
                    resolver_identities
                    if resp_key is None
                    else _identities_for_response_keys(
                        runtime_paths,
                        resolver_identities,
                        [resp_key],
                    ),
                    PlannedWindow(bounds, keyset_window_state),
                ),
            )
            if not advised:
                # First accepted window: emit the field-static composite-index
                # advisory exactly once (see the note above the loop).
                _advise_composite_index(django_field.related_model, join, order_by)
                advised = True
        else:
            _log_connection_fallback(
                relation_field_name,
                [resp_key] if resp_key is not None else response_keys(sel),
                f"strategy {getattr(strategy, 'name', introspection.name(type(strategy)))!r} "
                "refused the window",
            )
    if not planned_keys:
        return plan
    # Success path: absorb the child metadata the sub-plan collected into the
    # parent only now - a strategy that refused every window (like each earlier
    # refusal arm) must leak no child resolver keys / fk-id elisions /
    # cacheable flip into the parent plan (the spec-033 Decision 6 no-leakage contract).
    # The child queryset / node selections / order were built ONCE from the
    # merged UNION children and are shared by every per-key window, so one
    # absorb covers all planned keys.
    plan.merge_metadata_from(sub_plan)
    # (h) Record resolver identities so strictness sees the field as
    # planned - all identities for the shared window; only the planned keys'
    # identities under the divergent scheme (an unplanned sibling alias stays
    # strictness-visible as a real per-parent access).
    if divergent:
        append_unique_many(
            plan.planned_resolver_keys,
            _identities_for_response_keys(runtime_paths, resolver_identities, planned_keys),
        )
    else:
        append_unique_many(
            plan.planned_resolver_keys,
            resolver_identities,
        )
    return plan
