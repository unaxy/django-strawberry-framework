"""DjangoConnection construction, window internals, exception identity and planner metadata tests.

Request-shaped source, count, sidecar and cursor behavior lives in
``examples/fakeshop/test_query/test_connection_fields_api.py``. These rows keep
construction-time type identity, window state, original exception classes and
internal planner publication that a response does not expose. Shared consumer
declarations live in ``tests/_connection_field_schemas.py``.
"""

import asyncio
import copy
import functools
import gc
import warnings
from collections.abc import AsyncIterator, Awaitable, Iterable, Iterator
from types import SimpleNamespace
from typing import NoReturn, get_origin

import pytest
import strawberry
from apps.kanban.models import Status
from apps.products import services
from apps.products.models import Category, Item
from asgiref.sync import sync_to_async
from django.db import models
from graphql import GraphQLError
from strawberry import relay
from strawberry.relay.utils import from_base64, to_base64
from strawberry.types.base import get_object_definition
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import (
    _CONNECTION_ASYNC_RECOURSE,
    DjangoConnection,
    DjangoConnectionField,
    _attach_count_async,
    _connection_type_cache,
    _connection_type_for,
    _finalize_queryset,
    _guard_first_and_last,
    _guard_non_queryset_iterable,
    _offset_cursor_prefix,
    _pipeline_async,
    _pipeline_sync,
    _resolve_awaited_source,
    _total_count_requested,
    _window_edge_class,
    _window_edge_class_cache,
    _window_rows_are_annotated,
    _WindowedConnectionRows,
    clear_connection_type_cache,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import _helper_referenced_filtersets
from django_strawberry_framework.optimizer.extension import apply_connection_optimization
from django_strawberry_framework.optimizer.plans import (
    WINDOW_ROW_NUMBER,
    OptimizationPlan,
    _keyset_order_ref,
)
from django_strawberry_framework.orders import _helper_referenced_ordersets
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.relay import SyncMisuseError
from django_strawberry_framework.utils._narrowing import (
    is_abstract_set,
    read_attr,
    require,
)
from django_strawberry_framework.utils.connections import PaginationArgumentError
from django_strawberry_framework.utils.input_values import UNSET
from tests._connection_field_schemas import (
    _CONSUMER_CURSOR_PREFIX,
    _PLANNED_CONNECTION_DOCUMENT,
    _PLANNED_LIST_DOCUMENT,
    _capture_info,
    _CategoryFilter,
    _CategoryOrder,
    _consumer_edge_schema,
    _field_schema,
    _info_with_selection,
    _make_node_type,
    _make_relation_node_type,
    _make_sidecar_node_type,
    _node_over,
    _page_query,
    _planned_relation_request,
    _planned_relation_schema,
    _schema_for,
)
from tests._idioms import declare_django_type, json_at, json_list
from tests._info import make_info


@pytest.fixture(autouse=True)
def _isolate_global_registry() -> Iterator[None]:
    """Clear the global registry and the connection-type cache around each test.

    Connection classes are cached on ``target_type`` identity; function-scope
    ``DjangoType`` fixtures are recreated fresh each test, so clearing the cache
    keeps a discarded class from leaking into a later test's identity check.
    """
    registry.clear()
    _connection_type_cache.clear()
    yield
    registry.clear()
    _connection_type_cache.clear()


# =============================================================================
# DjangoConnection base shape + first/last guard
# =============================================================================


def test_django_connection_is_listconnection_subclass() -> None:
    """``DjangoConnection`` is a ``ListConnection`` subclass with no ``total_count`` field."""
    assert issubclass(DjangoConnection, relay.ListConnection)
    assert "total_count" not in getattr(DjangoConnection, "__annotations__", {})

    # The parametrized form is a generic alias whose origin is ``DjangoConnection``.
    node_type = _make_node_type("GuardNode", total_count=None)
    specialized = DjangoConnection[node_type]
    assert get_origin(specialized) is DjangoConnection


def test_first_and_last_raises_graphql_error() -> None:
    """``resolve_connection`` with both ``first`` and ``last`` raises ``GraphQLError``.

    The package's own guard - Strawberry's ``SliceMetadata.from_arguments`` does
    not reject the combination. Driven at the classmethod directly with a bare
    ``info``: only the schema's ``relay_max_results`` is read ahead of the guard.
    """
    with pytest.raises(GraphQLError, match="mutually exclusive"):
        DjangoConnection[object].resolve_connection([], info=make_info(), first=1, last=1)


def test_first_and_last_guard_on_generated_subclass() -> None:
    """The generated ``<TypeName>Connection`` shares the ``first`` + ``last`` guard."""
    node_type = _make_node_type("GuardCountNode", total_count=True)
    connection_type = _connection_type_for(node_type, node_type.__django_strawberry_definition__)

    with pytest.raises(GraphQLError, match="mutually exclusive"):
        connection_type.resolve_connection([], info=make_info(), first=1, last=1)


def test_first_and_last_guard_with_unset() -> None:
    """``_guard_first_and_last`` ignores ``strawberry.UNSET`` correctly."""
    # Omitted args arriving as UNSET do not trigger the mutual exclusivity error
    # basedpyright: the guard is annotated ``int | None``, but Strawberry hands an omitted
    # argument over as UNSET, the input this row pins
    omitted: int | None = UNSET  # pyright: ignore[reportAssignmentType]
    _guard_first_and_last(omitted, omitted)
    _guard_first_and_last(5, omitted)
    _guard_first_and_last(omitted, 5)

    with pytest.raises(GraphQLError, match="mutually exclusive"):
        _guard_first_and_last(5, 5)


# =============================================================================
# _connection_type_for: generation + caching + presence-by-opt-in
# =============================================================================


def test_connection_type_for_caches_per_target() -> None:
    """``_connection_type_for`` returns one cached class object per node type."""
    node_type = _make_node_type("CacheNode", total_count=True)

    first = _connection_type_for(node_type, node_type.__django_strawberry_definition__)
    second = _connection_type_for(node_type, node_type.__django_strawberry_definition__)
    assert first is second


def test_connection_type_for_generates_named_subclass_when_opted_in() -> None:
    """A ``total_count``-enabled type yields ``<TypeName>Connection`` declaring ``total_count``."""
    node_type = _make_node_type("OptedNode", total_count=True)

    connection_type = _connection_type_for(node_type, node_type.__django_strawberry_definition__)
    assert connection_type.__name__ == "OptedNodeConnection"
    assert "total_count" in connection_type.__annotations__
    assert issubclass(connection_type, DjangoConnection)


def test_generated_connection_name_uses_graphql_type_name_not_python_name() -> None:
    """Generated ``<Type>Connection`` names derive from ``graphql_type_name``, not ``__name__``.

    Two DjangoType classes can share a Python ``__name__`` while declaring distinct
    ``Meta.name`` values. Naming the generated connection from ``__name__`` produces two classes with the SAME
    SDL type name, which Strawberry collapses into one - corrupting both root
    fields' ``edges`` / node types. Deriving from ``graphql_type_name`` (the
    canonical surface name, ``Meta.name`` when set) keeps them distinct.
    """

    def _dup_named_node(meta_name: str, model: type[models.Model]) -> type[DjangoType]:
        # Identical Python ``__name__`` ("NodeType") for BOTH; distinct Meta.name.
        return declare_django_type(
            "NodeType",
            {
                "Meta": type(
                    "Meta",
                    (),
                    {
                        "model": model,
                        "fields": ("id", "name"),
                        "interfaces": (relay.Node,),
                        "name": meta_name,
                        "connection": {"total_count": True},
                    },
                ),
            },
        )

    category_node = _dup_named_node("PublicCategory", Category)
    item_node = _dup_named_node("PublicItem", Item)

    cat_conn = _connection_type_for(category_node, category_node.__django_strawberry_definition__)
    item_conn = _connection_type_for(item_node, item_node.__django_strawberry_definition__)

    # Distinct classes, each named from its ``graphql_type_name`` (Meta.name) -
    # not a single colliding ``NodeTypeConnection``.
    assert cat_conn.__name__ == "PublicCategoryConnection"
    assert item_conn.__name__ == "PublicItemConnection"
    assert cat_conn is not item_conn

    def _categories() -> Iterable[Category]:
        return Category.objects.all().order_by("pk")

    def _items() -> Iterable[Item]:
        return Item.objects.all().order_by("pk")

    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"categories": cat_conn, "items": item_conn},
                "categories": relay.connection(cat_conn, resolver=_categories),
                "items": relay.connection(item_conn, resolver=_items),
            },
        ),
    )
    finalize_django_types()
    sdl = str(strawberry.Schema(query=query_cls, config=strawberry_config()))

    # Both connection types present and distinct; no collapsed collision.
    assert "PublicCategoryConnection" in sdl
    assert "PublicItemConnection" in sdl
    assert "NodeTypeConnection" not in sdl
    # Each connection exposes its own edge type - no cross-wiring of node edges.
    assert "PublicCategoryEdge" in sdl
    assert "PublicItemEdge" in sdl


@pytest.mark.parametrize("total_count", [None, True], ids=["bare", "total_count"])
def test_generated_connection_name_keeps_an_underscore_in_meta_name(
    *,
    total_count: bool | None,
) -> None:
    """A ``Meta.name`` carrying an underscore publishes ``<Name>Connection`` verbatim.

    Strawberry names a type given no ``name=`` ``to_camel_case(__name__)``, which
    re-cases ``Cat_NodeConnection`` to ``CatNodeconnection``; the generator pins
    ``name=`` so the SDL carries the spec-030 ``<TypeName>Connection`` beside the
    ``<TypeName>Edge`` Strawberry already names from the node's GraphQL name.
    """
    node_type = _make_node_type("Cat_Node", total_count=total_count)
    sdl = _schema_for(node_type).as_str()

    assert "type Cat_NodeConnection " in sdl
    assert "type Cat_NodeEdge " in sdl
    assert "CatNodeconnection" not in sdl


def test_generated_connection_name_follows_an_unnamed_underscore_class() -> None:
    """An unnamed ``Cat_Node`` publishes ``CatNode``, and its connection ``CatNodeConnection``.

    Strawberry re-cases an unnamed class's ``__name__``; the connection name is
    derived from the same published name, not the raw class name, so node, edge
    and connection agree.
    """
    meta = type(
        "Meta",
        (),
        {"model": Category, "fields": ("id", "name"), "interfaces": (relay.Node,)},
    )
    node_type = declare_django_type("Cat_Node", {"Meta": meta})
    sdl = _schema_for(node_type).as_str()

    assert "type CatNode implements Node " in sdl
    assert "type CatNodeEdge " in sdl
    assert "type CatNodeConnection " in sdl
    assert "Cat_Node" not in sdl


def test_connection_type_for_returns_concrete_subclass_without_opt_in() -> None:
    """A non-opted Relay-Node type yields a generated concrete subclass without ``total_count``.

    Never the ``DjangoConnection[T]`` generic alias: a generic alias handed to
    the schema loses the ``resolve_connection`` override (and with it the
    ``first`` + ``last`` guard) at Strawberry's generic specialization
    (spec-032). The non-opted path must be a concrete
    class too, just with no ``total_count`` members.
    """
    node_type = _make_node_type("BareNode", total_count=None)

    connection_type = _connection_type_for(node_type, node_type.__django_strawberry_definition__)
    assert issubclass(connection_type, DjangoConnection)
    assert connection_type is not DjangoConnection
    assert connection_type.__name__ == "BareNodeConnection"
    assert "total_count" not in getattr(connection_type, "__annotations__", {})


def test_connection_type_for_returns_concrete_subclass_when_total_count_false() -> None:
    """``connection = {"total_count": False}`` yields the concrete subclass, no ``totalCount`` variant."""
    node_type = _make_node_type("FalseNode", total_count=False)

    connection_type = _connection_type_for(node_type, node_type.__django_strawberry_definition__)
    assert issubclass(connection_type, DjangoConnection)
    assert connection_type is not DjangoConnection
    assert connection_type.__name__ == "FalseNodeConnection"
    assert "total_count" not in getattr(connection_type, "__annotations__", {})


# =============================================================================
# _total_count_requested selection-gating (unit)
# Live COUNT SQL / skip / fragment gating is ``test_library_api.py``
# (``test_genre_connection_total_count_omitted_no_count``,
# ``test_genre_connection_total_count_skip_include_no_count``,
# ``test_anonymous_inline_fragment_with_total_count_resolves``). These rows pin
# the helper's AST walk: a nested ``totalCount`` under ``edges.node`` must not
# fire, and fragment wrappers at the connection's own level must.
# =============================================================================


def test_total_count_requested_true_when_selected() -> None:
    """``_total_count_requested`` is True when ``totalCount`` is in the selection set."""
    assert _total_count_requested(_info_with_selection("edges", "totalCount")) is True


def test_total_count_requested_false_when_absent() -> None:
    """``_total_count_requested`` is False when ``totalCount`` is not selected."""
    assert _total_count_requested(_info_with_selection("edges", "pageInfo")) is False


def test_total_count_requested_scoped_to_direct_children() -> None:
    """A ``totalCount`` nested in ``edges { node { ... } }`` does NOT fire the predicate.

    ``_total_count_requested`` checks only the connection's DIRECT children, so a
    (future) node-level ``totalCount`` deep in the subtree must not make the OUTER
    connection count spuriously. A direct-child ``totalCount`` still counts.
    """
    # Direct-child ``totalCount`` still counts.
    assert _total_count_requested(_info_with_selection("edges", "totalCount")) is True
    # ``totalCount`` ONLY nested inside ``edges { node { ... } }`` must NOT count:
    # the predicate does not descend into a regular field's selections.
    nested = make_info(
        field_name="connectionField",
        selections="{ edges { node { totalCount } } pageInfo }",
    )
    assert _total_count_requested(nested) is False


def test_total_count_requested_recurses_through_fragments() -> None:
    """``_total_count_requested`` recurses THROUGH fragment wrappers to find ``totalCount``.

    A ``totalCount`` reached only via a ``FragmentSpread`` / ``InlineFragment`` on
    the connection's direct selection set still counts -- the predicate descends
    into fragment ``.selections`` (but not into regular fields).
    """
    # ``totalCount`` reached only via a FragmentSpread on the connection's selections.
    info = make_info(
        field_name="connectionField",
        selections="{ edges ...ConnFields }",
        fragments="fragment ConnFields on XConnection { totalCount }",
    )
    assert _total_count_requested(info) is True

    # An InlineFragment WITHOUT totalCount stays False (recursion returns nothing).
    info_no_count = make_info(
        field_name="connectionField",
        selections="{ ... on XConnection { pageInfo } }",
    )
    assert _total_count_requested(info_no_count) is False


# =============================================================================
# totalCount counting + selection-gating through a real schema query
# =============================================================================


# =============================================================================
# DjangoConnectionField factory + pipeline + sidecar args
# =============================================================================


# --- Constructor guards ------------------------------------------------------


def test_connection_field_requires_djangotype() -> None:
    """A non-class target raises ``ConfigurationError``."""
    with pytest.raises(ConfigurationError, match="requires a DjangoType class"):
        # basedpyright: the non-class value is the hostile input under test; DjangoConnectionField
        # types the parameter as type[object]
        DjangoConnectionField(42)  # pyright: ignore[reportArgumentType]


def test_connection_field_requires_djangotype_subclass() -> None:
    """A non-``DjangoType`` class raises ``ConfigurationError``."""

    class Plain:
        pass

    with pytest.raises(ConfigurationError, match="requires a DjangoType subclass"):
        DjangoConnectionField(Plain)


def test_connection_field_rejects_non_callable_resolver() -> None:
    """A non-callable ``resolver=`` raises ``ConfigurationError``."""
    node_type = _make_sidecar_node_type("NonCallableResolverNode")
    with pytest.raises(ConfigurationError, match="resolver must be callable"):
        # basedpyright: the non-callable resolver is the hostile input under test;
        # DjangoConnectionField types the parameter as a callable
        DjangoConnectionField(node_type, resolver="not callable")  # pyright: ignore[reportArgumentType]


def test_connection_field_requires_relay_node() -> None:
    """A non-Relay ``DjangoType`` raises ``ConfigurationError`` naming ``relay.Node``."""
    non_relay = declare_django_type(
        "NonRelayNode",
        {"Meta": type("Meta", (), {"model": Category, "fields": ("id", "name"), "name": "NRN"})},
    )
    with pytest.raises(ConfigurationError, match=r"relay\.Node"):
        DjangoConnectionField(non_relay)


def test_connection_field_accepts_direct_relay_node_inheritance() -> None:
    """A direct ``class Foo(DjangoType, relay.Node)`` (no ``Meta.interfaces``) is accepted.

    ``spec-030-connection_field-0_0_9`` Decision 5: direct ``relay.Node``
    inheritance is a supported, fully-finalizable Relay shape (the finalizer keys
    Relay wiring off ``implements_relay_node``, not a non-empty
    ``Meta.interfaces``). The connection guard reuses the canonical
    ``_is_relay_shaped`` predicate, so it accepts this Strawberry-native spelling
    without a ``ConfigurationError`` - even though ``definition.interfaces`` is empty.
    """

    class DirectRelayNode(DjangoType, relay.Node):
        class Meta:
            model = Category
            fields = ("id", "name")
            name = "DirectRelayNode"

    # ``relay.Node`` is NOT in the declared Meta-tuple; acceptance comes purely
    # from the direct MRO inheritance (``issubclass(target_type, relay.Node)``).
    assert relay.Node not in DirectRelayNode.__django_strawberry_definition__.interfaces
    # Does not raise; produces a connection field over the bare connection shape.
    field = DjangoConnectionField(DirectRelayNode)
    assert field is not None


def test_connection_type_for_generates_total_count_for_direct_relay_inheritance() -> None:
    """Direct ``relay.Node`` inheritance can use the per-type ``totalCount`` opt-in.

    Once ``Meta.connection`` validation accepts direct inheritance, the ``totalCount``
    surface works for it too - ``_connection_type_for`` generates the concrete ``<Name>Connection`` carrying
    ``total_count`` exactly as it does for the ``Meta.interfaces`` spelling.
    """

    class DirectCountNode(DjangoType, relay.Node):
        class Meta:
            model = Category
            fields = ("id", "name")
            name = "DirectCount"
            connection = {"total_count": True}

    assert relay.Node not in DirectCountNode.__django_strawberry_definition__.interfaces
    connection_type = _connection_type_for(
        DirectCountNode,
        DirectCountNode.__django_strawberry_definition__,
    )
    assert connection_type.__name__ == "DirectCountConnection"
    assert "total_count" in connection_type.__annotations__

    # Schema-level: ``totalCount`` is exposed in the SDL for the direct-inheritance type.
    sdl = str(_schema_for(DirectCountNode))
    assert "totalCount" in sdl


# --- Orphan-ledger registration ----------------------------------------------


def test_connection_field_registers_sidecars_against_orphan_ledgers() -> None:
    """Constructing the field records the FilterSet / OrderSet in the orphan ledgers."""
    node_type = _make_sidecar_node_type("LedgerNode")
    _helper_referenced_filtersets.discard(_CategoryFilter)
    _helper_referenced_ordersets.discard(_CategoryOrder)

    DjangoConnectionField(node_type)

    assert _CategoryFilter in _helper_referenced_filtersets
    assert _CategoryOrder in _helper_referenced_ordersets


# --- Four consumer-resolver cases --------------------------------------------


def test_non_iterable_source_rejection_names_the_source_kind() -> None:
    """The shape gate's message names the returned value's real class."""
    with pytest.raises(GraphQLError) as exc_info:
        _guard_non_queryset_iterable(42)
    assert str(exc_info.value) == (
        "A connection resolver returned int, which is neither a QuerySet (or a Manager) nor "
        "a plain iterable. A connection field paginates by slicing or iterating its source, "
        "so return a QuerySet (or a Manager), or an iterable of nodes, from the connection "
        "resolver."
    )


@pytest.mark.django_db
def test_guard_non_queryset_iterable_admits_getitem_only_sequence() -> None:
    """A ``__getitem__``-only legacy sequence stays admitted by the shape gate.

    ``isinstance(value, Iterable)`` is False for an object implementing only
    the sequence protocol, yet Relay's slicer paginates it via the
    slice-subscript path - so the guard must not reject it.
    """

    class LegacySequence:
        def __getitem__(self, index: int) -> object:
            empty: list[object] = []
            return empty[index]

    _guard_non_queryset_iterable(LegacySequence())  # does not raise
    with pytest.raises(GraphQLError, match="plain iterable"):
        _guard_non_queryset_iterable(None)


async def test_attach_count_async_awaits_before_guard_raises() -> None:
    """``_attach_count_async`` awaits the connection coroutine BEFORE the non-queryset guard can raise.

    Regression guard for the await-before-raise discipline (Decision 10, mirroring
    ``utils/querysets.py::apply_type_visibility_sync``'s close-before-raise). Were the
    guard to run first, a guard-raise on the non-queryset + ``totalCount``
    path would leave the queued connection coroutine unawaited -> ``RuntimeWarning: coroutine
    ... was never awaited`` (a hard failure under ``-W error``). Deterministic: assert
    the coroutine was actually awaited (``consumed``) AND that no unawaited-coroutine
    ``RuntimeWarning`` leaks even after a forced GC.
    """
    consumed = {"flag": False}

    async def make_conn() -> DjangoConnection[object]:
        consumed["flag"] = True
        return DjangoConnection[object](
            page_info=relay.PageInfo(
                has_previous_page=False,
                has_next_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
            edges=[],
        )

    coro = make_conn()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(GraphQLError, match="totalCount"):
            await _attach_count_async(coro, ["not", "a", "queryset"], want_count=True)
        gc.collect()
        leaked = [
            w
            for w in caught
            if issubclass(w.category, RuntimeWarning) and "never awaited" in str(w.message)
        ]

    assert consumed["flag"], "the connection coroutine must be awaited before the guard raises"
    assert not leaked, (
        f"unawaited-coroutine RuntimeWarning leaked: {[str(w.message) for w in leaked]}"
    )


# --- Default deterministic ordering ------------------------------------------


@pytest.mark.django_db
def test_default_ordering_applied_when_unordered() -> None:
    """An unordered base + no ``orderBy`` gets ``order_by(pk)`` applied."""
    services.seed_data(1)
    node_type = _make_sidecar_node_type("DefaultOrderNode")
    info = _capture_info(node_type)

    qs = _pipeline_sync(
        node_type,
        Category.objects.all(),
        info,
        definition=node_type.__django_strawberry_definition__,
        filter_input=None,
        order_by_input=None,
    )
    assert isinstance(qs, models.QuerySet)
    assert qs.ordered
    assert qs.query.order_by == (Category._meta.pk.attname,)


@pytest.mark.django_db
def test_default_ordering_preserves_supplied_orderby() -> None:
    """A queryset already ordered (e.g. by a supplied ``orderBy``) is NOT pk-overridden."""
    services.seed_data(1)
    node_type = _make_sidecar_node_type("PreservedOrderNode")
    info = _capture_info(node_type)

    # A pre-ordered source stands in for a supplied ``orderBy`` / model
    # ``Meta.ordering`` - both mark ``qs.ordered`` True before the default step.
    qs = _pipeline_sync(
        node_type,
        Category.objects.order_by("name"),
        info,
        definition=node_type.__django_strawberry_definition__,
        filter_input=None,
        order_by_input=None,
    )
    assert isinstance(qs, models.QuerySet)
    assert qs.query.order_by == ("name",)


@pytest.mark.django_db
def test_default_ordering_preserves_meta_ordering() -> None:
    """A queryset that is already ``ordered`` keeps its ordering (the ``Meta.ordering`` shape).

    ``qs.ordered`` is the property the default-ordering step branches on; a
    descending pre-order stands in for a model ``Meta.ordering`` - the pk default
    must not fire because ``qs.ordered`` is already True.
    """
    services.seed_data(1)
    node_type = _make_sidecar_node_type("MetaOrderNode")
    info = _capture_info(node_type)

    qs = _pipeline_sync(
        node_type,
        Category.objects.order_by("-name"),
        info,
        definition=node_type.__django_strawberry_definition__,
        filter_input=None,
        order_by_input=None,
    )
    assert isinstance(qs, models.QuerySet)
    assert qs.query.order_by == ("-name",)


# --- Composition order -------------------------------------------------------


# --- Sync + async dispatch + SyncMisuseError ---------------------------------


@pytest.mark.django_db
def test_connection_sync_async_generator_resolver_raises_sync_misuse() -> None:
    """Sync execution rejects an async-generator resolver with a typed error."""
    services.seed_data(1)
    rows = list(Category.objects.all())

    async def resolver(_root: object, _info: object) -> AsyncIterator[Category]:
        for row in rows:
            yield row

    schema = _field_schema(
        _make_sidecar_node_type("AsyncGeneratorNode"),
        resolver=resolver,
    )
    result = schema.execute_sync("{ items(first: 1) { edges { node { id } } } }")
    assert result.errors is not None
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "AsyncIterable in a sync execution context" in str(result.errors[0])


@pytest.mark.django_db
def test_connection_partial_async_generator_resolver_raises_sync_misuse() -> None:
    """``partial`` around an async-gen callable instance still fails closed under sync execution.

    The wrapper calls the partial, classifies the returned value by VALUE
    (an async-only iterable), and the sync-misuse guard rejects it before
    Relay's synchronous slicer can consume it.
    """
    services.seed_data(1)
    rows = list(Category.objects.all())

    class _Resolver:
        async def __call__(
            self,
            _prefix: str,
            root: object,
            info: object,
        ) -> AsyncIterator[Category]:
            del root, info  # Strawberry passes both by keyword; the stream reads neither
            for row in rows:
                yield row

    resolver = functools.partial(_Resolver(), "ignored")

    schema = _field_schema(
        _make_sidecar_node_type("PartialAsyncGeneratorNode"),
        resolver=resolver,
    )
    result = schema.execute_sync("{ items(first: 1) { edges { node { id } } } }")
    assert result.errors is not None
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "AsyncIterable in a sync execution context" in str(result.errors[0])


@pytest.mark.django_db
def test_connection_sync_resolver_returning_async_iterable_raises_sync_misuse() -> None:
    """A plain resolver's async-only return is rejected before Relay's sync slicer crashes.

    Resolver classification cannot see this shape at schema construction: the
    callable is ordinary ``def`` and only its runtime result is an async
    generator. Without the source-level guard, Strawberry first subscripts it,
    then raises a blank internal ``AssertionError`` instead of the package's
    actionable sync-misuse error.
    """
    services.seed_data(1)
    rows = list(Category.objects.order_by("pk"))

    def resolver(_root: object, _info: object) -> AsyncIterator[Category]:
        async def stream() -> AsyncIterator[Category]:
            for row in rows:
                yield row

        return stream()

    schema = _field_schema(
        _make_sidecar_node_type("SyncReturnAsyncIterableNode"),
        resolver=resolver,
    )
    result = schema.execute_sync("{ items(first: 1) { edges { node { id } } } }")

    assert result.errors is not None
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "AsyncIterable in a sync execution context" in str(result.errors[0])


@pytest.mark.django_db
def test_sync_context_async_get_queryset_raises_sync_misuse() -> None:
    """An async ``get_queryset`` invoked from the sync resolver path raises ``SyncMisuseError``."""
    services.seed_data(1)

    async def get_queryset(
        _cls: type[DjangoType],
        qs: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        return qs

    node_type = _make_sidecar_node_type(
        "AsyncVisibilitySyncNode",
        get_queryset=get_queryset,
    )
    schema = _field_schema(node_type)
    result = schema.execute_sync("{ items { edges { node { id } } } }")
    assert result.errors is not None
    (error,) = result.errors
    assert isinstance(error.original_error, SyncMisuseError)
    assert str(error.original_error) == (
        "AsyncVisibilitySyncNode.get_queryset returned a coroutine in a sync resolver "
        f"context. {_CONNECTION_ASYNC_RECOURSE}"
    )


async def test_connection_sync_resolver_returning_coroutine_raises_sync_misuse() -> None:
    """A plain ``def`` returning a coroutine cannot enter connection slicing."""
    node_type = _make_sidecar_node_type("CoroSyncConnNode")

    async def _inner() -> list[object]:
        return []

    def _sync_resolver_returning_coroutine(
        _root: object,
        _info: object,
    ) -> Awaitable[list[object]]:
        return _inner()

    schema = _field_schema(
        node_type,
        resolver=_sync_resolver_returning_coroutine,
    )
    result = await schema.execute("{ items { edges { node { id } } } }")

    assert result.errors is not None
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "returned an awaitable" in str(result.errors[0])
    assert result.data is None


async def test_an_awaited_connection_source_resolving_to_another_awaitable_fails_closed() -> None:
    """One await is spent on an awaitable connection source; a second awaitable is refused.

    ``connection.py::_resolve_awaited_source`` is the completion step both awaitable
    sources share (``DjangoConnection.resolve_connection`` and the windowed
    fallback). The nested awaitable is disposed, never awaited, so neither coroutine
    is left unawaited and the consumer step is never reached.
    """

    async def _inner() -> list[object]:
        return []

    async def _outer() -> Awaitable[list[object]]:
        return _inner()

    def _never_reached(_value: object) -> DjangoConnection[DjangoType]:
        raise AssertionError("a nested awaitable must not reach the connection step")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(ConfigurationError, match="resolved to another awaitable"):
            await _resolve_awaited_source(_outer(), _never_reached)
        gc.collect()
    assert [str(warning.message) for warning in caught] == []


async def test_connection_async_resolver_resolving_to_residual_awaitable_fails_closed() -> None:
    """An async connection resolver resolving to a SECOND awaitable fails closed before visibility.

    ``_build_connection_resolver``'s async branch awaits the consumer resolver
    once; a value that is STILL awaitable after that await is a nested async
    resolver whose inner awaitable would otherwise pass the non-queryset sidecar
    guard and skip ``get_queryset`` entirely. This is the connection twin of the
    list field's ``reject_residual_async_source`` guard, which the list helper's
    own unit test pins. Exercised at
    a real ``DjangoConnectionField`` with NO sidecar input (the bypass shape),
    so the residual-awaitable guard, not the sidecar guard, is what rejects it.
    """
    node_type = _make_sidecar_node_type("ResidualAsyncConnNode")

    async def _inner() -> Iterable[object]:
        return []

    async def _async_resolver_returning_awaitable(
        _root: object,
        _info: object,
    ) -> Awaitable[Iterable[object]]:
        return _inner()  # resolves (after one await) to ANOTHER coroutine

    schema = _field_schema(node_type, resolver=_async_resolver_returning_awaitable)
    result = await schema.execute("{ items { edges { node { id } } } }")

    assert result.errors is not None
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, ConfigurationError)
    assert "silently skip the get_queryset visibility hook" in str(result.errors[0])
    assert result.data is None


# =============================================================================
# Optimizer cooperation point + connection-aware-planning gap guard
# =============================================================================


@pytest.mark.django_db
def test_root_connection_field_queryset_is_planned() -> None:
    """The field's helper plans ``edges.node`` selections on the pre-slice queryset.

    A root ``DjangoConnectionField`` self-optimizes by calling
    ``apply_connection_optimization`` before ``ConnectionExtension`` slices -
    the schema middleware (``DjangoOptimizerExtension.resolve``) cannot reach the
    pre-slice queryset behind the connection result, so any published plan over
    the connection IS the field's own cooperation point running (per the spec's
    "the cooperation point the field now owns, NOT the middleware" framing).

    The published plan is asserted via ``info.context.dst_optimizer_plan`` (the
    B5 plan-introspection shape from ``tests/optimizer/test_extension.py``): its
    presence on the context proves ``apply_to`` -> ``_publish_plan_to_context``
    ran for the connection field, which it does ONLY through the field's helper.
    Live SQL for a hooked target is Prefetch, not ``select_related``
    (``test_products_api.py::test_products_optimizer_merges_duplicate_root_field_nodes_over_http``);
    this row keeps the plan-object for a hook-free throwaway, which no shipped
    type reproduces.
    """
    services.seed_data(2)
    # ``ItemNode`` exposes the forward FK ``category`` - the relation a plain
    # ``DjangoListField`` over the same type plans as ``select_related``.
    _make_relation_node_type("PlanCatNode", fields=("id", "name"))
    item_node = _make_relation_node_type(
        "PlanItemNode",
        fields=("id", "name", "category"),
        model=Item,
    )
    schema = _field_schema(item_node, optimizer=DjangoOptimizerExtension(strictness="raise"))

    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ items { edges { node { id name category { id name } } } } }",
        context_value=ctx,
    )
    assert result.errors is None
    # The cooperation point ran: the field's helper published a plan to context.
    # (The middleware never sees the pre-slice queryset behind ConnectionExtension,
    # so this plan can only have come from the field's own helper.)
    plan = read_attr(ctx, "dst_optimizer_plan", None)
    assert isinstance(plan, OptimizationPlan)
    assert plan.select_related == ("category",)
    assert plan.prefetch_related == ()
    assert plan.only_fields == (
        "id",
        "name",
        "category_id",
        "category__id",
        "category__name",
    )
    assert "PlanItemNode.category@items.edges.node.category" in require(
        read_attr(ctx, "dst_optimizer_planned"),
        is_abstract_set,
    )


@pytest.mark.django_db
def test_root_connection_field_queryset_prefetches_node_many_relation() -> None:
    """A many-side relation under ``edges.node`` is planned as a prefetch.

    Live SQL for the same many-side under a root connection is
    ``test_products_visibility_api.py``'s planned-list / planned-connection rows
    (one ``FROM "products_item"`` query). This row keeps the plan-object
    (``prefetch_related`` / ``only_fields``) a response cannot uniquely show.
    """
    services.seed_data(2)
    _make_relation_node_type("PlanPrefetchItemNode", fields=("id", "name"), model=Item)
    category_node = _make_relation_node_type(
        "PlanPrefetchCatNode",
        fields=("id", "name", "items"),
        list_relations=("items",),
    )
    schema = _field_schema(category_node, optimizer=DjangoOptimizerExtension(strictness="raise"))

    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ items { edges { node { id name items { id name } } } } }",
        context_value=ctx,
    )

    assert result.errors is None
    plan = read_attr(ctx, "dst_optimizer_plan", None)
    assert isinstance(plan, OptimizationPlan)
    assert plan.select_related == ()
    assert [read_attr(entry, "prefetch_to", entry) for entry in plan.prefetch_related] == ["items"]
    assert plan.only_fields == ("id", "name")
    assert "PlanPrefetchCatNode.items@items.edges.node.items" in require(
        read_attr(ctx, "dst_optimizer_planned"),
        is_abstract_set,
    )


# =============================================================================
# Deterministic-total-order tiebreaker (``spec-030-connection_field-0_0_9``)
# =============================================================================


def test_finalize_queryset_appends_pk_tiebreaker_to_non_unique_ordering() -> None:
    """A queryset ordered by a NON-UNIQUE column gets the pk appended.

    Otherwise the connection's positional offset cursors are unstable across
    requests when ties exist (rows silently skipped / duplicated across pages).
    No DB query runs - ``_finalize_queryset`` only shapes the lazy queryset and
    the optimizer cooperation point short-circuits with no optimizer installed.
    """
    node = _node_over(Item, "P1ItemNode")
    result = _finalize_queryset(
        node,
        Item.objects.order_by("name"),
        make_info(),
        definition=node.__django_strawberry_definition__,
    )
    assert tuple(result.query.order_by) == ("name", "id")


def test_finalize_queryset_skips_pk_when_terminal_already_unique() -> None:
    """An ordering already ending in a UNIQUE column is left alone (no double pk)."""
    node = _node_over(Category, "P1CatNode")
    # Category.name is unique=True -> already a deterministic total order.
    by_name = _finalize_queryset(
        node,
        Category.objects.order_by("name"),
        make_info(),
        definition=node.__django_strawberry_definition__,
    )
    assert tuple(by_name.query.order_by) == ("name",)
    # Ordering by the pk itself is not doubled into ``("id", "id")``.
    by_pk = _finalize_queryset(
        node,
        Category.objects.order_by("id"),
        make_info(),
        definition=node.__django_strawberry_definition__,
    )
    assert tuple(by_pk.query.order_by) == ("id",)


def test_finalize_queryset_preserves_meta_ordering_and_appends_pk() -> None:
    """A model ``Meta.ordering`` is PRESERVED + pk appended, not clobbered to pk-only.

    ``qs.query.order_by`` is empty when the order comes from ``Meta.ordering``
    even though ``qs.ordered`` is True; ``_finalize_queryset`` resolves the
    effective ordering from ``_meta.ordering`` so ``ORDER BY order`` becomes
    ``ORDER BY order, pk`` rather than dropping to ``ORDER BY pk``
    (``spec-030-connection_field-0_0_9``). ``Status`` (kanban)
    declares ``Meta.ordering = ["order"]`` over a non-unique ``PositiveIntegerField``.
    """
    node = _node_over(Status, "P1StatusNode", fields=("id",))
    qs = Status.objects.all()
    assert qs.ordered is True
    assert tuple(qs.query.order_by) == ()  # order comes implicitly from Meta.ordering
    result = _finalize_queryset(
        node,
        qs,
        make_info(),
        definition=node.__django_strawberry_definition__,
    )
    assert tuple(result.query.order_by) == ("order", "id")


# =============================================================================
# Optimizer cooperation short-circuit + connection-type-cache reset
# =============================================================================


def test_apply_connection_optimization_short_circuits_without_optimizer() -> None:
    """With no optimizer installed, the cooperation point returns the qs unchanged.

    The connection field does NOT fabricate a throwaway optimizer to
    self-optimize; outside an execution no execution frame is open, so
    ``active_optimizer()`` returns ``None`` and the helper short-circuits
    (``spec-030-connection_field-0_0_9`` Decision 11).
    """
    node = _make_node_type("NoOptimizerNode", total_count=None)
    qs = Category.objects.all()
    assert apply_connection_optimization(node, qs, make_info()) is qs


def test_apply_connection_optimization_short_circuits_when_target_has_no_model() -> None:
    """An unregistered target type has no model to plan, so the qs is returned.

    Hits the ``target_model is None`` guard before the optimizer lookup: a type the
    registry does not know maps to no Django model, so there is nothing to optimize.
    """

    class _UnregisteredNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    registry.unregister(_UnregisteredNode)  # the registry no longer maps it to a model
    assert registry.model_for_type(_UnregisteredNode) is None

    qs = Category.objects.all()
    result = apply_connection_optimization(_UnregisteredNode, qs, make_info())
    assert result is qs


@pytest.mark.django_db
def test_pipeline_async_coerces_manager_source_and_finalizes() -> None:
    """``_pipeline_async`` coerces a Manager to a queryset and applies the default pk ordering.

    Async twin of the sync default-ordering path: a ``Manager`` source is run through
    ``.all()``, the async ``get_queryset`` hook, then ``_finalize_queryset_async`` (which
    appends the pk tiebreaker to the otherwise-unordered base).
    """
    node_type = _make_sidecar_node_type("AsyncManagerNode")
    info = _capture_info(node_type)
    qs = asyncio.run(
        _pipeline_async(
            node_type,
            Category.objects,
            info,
            definition=node_type.__django_strawberry_definition__,
            filter_input=None,
            order_by_input=None,
        ),
    )
    assert isinstance(qs, models.QuerySet)
    assert qs.ordered
    assert qs.query.order_by == (Category._meta.pk.attname,)


# --- Post-OrderSet seal on the connection field -------------------------------


#: One row per defect shape the post-``OrderSet`` seal names at the CONNECTION
#: field; ``materialized-list`` and ``none`` share the ``type`` branch.
#: ``(id, override, expected message start, required substrings)``. The
#: connection takes the Relay window on whatever ordering returned, so an
#: unsealed result is a wrong page or a foreign row rather than a loud error -
#: each row proves the seal rejects instead.


def test_clear_connection_type_cache_empties_the_cache() -> None:
    """``clear_connection_type_cache`` drops the generated-connection-class cache."""
    node_type = _make_node_type("CacheClearDirectNode", total_count=True)
    _connection_type_for(node_type, node_type.__django_strawberry_definition__)
    assert _connection_type_cache
    clear_connection_type_cache()
    assert not _connection_type_cache


def test_registry_clear_also_clears_connection_type_cache() -> None:
    """``registry.clear()`` resets the connection-type cache too."""
    node_type = _make_node_type("CacheClearRegistryNode", total_count=True)
    _connection_type_for(node_type, node_type.__django_strawberry_definition__)
    assert _connection_type_cache
    registry.clear()
    assert not _connection_type_cache


def test_registry_clear_also_clears_window_edge_class_cache() -> None:
    """``registry.clear()`` drops the resolved edge classes with the connection classes."""
    node_type = _make_node_type("EdgeClassCacheNode", total_count=None)
    _window_edge_class(
        _connection_type_for(node_type, node_type.__django_strawberry_definition__),
    )
    assert _window_edge_class_cache
    registry.clear()
    assert not _window_edge_class_cache


@pytest.mark.parametrize("total_count", [None, True], ids=["bare", "total-count"])
def test_generated_connections_decode_under_the_stock_edge_prefix(
    *,
    total_count: bool | None,
) -> None:
    """Every generated connection mints and decodes under the stock ``relay.Edge`` prefix.

    The nested planner derives window bounds under ``relay.Edge.CURSOR_PREFIX``
    without holding the connection class, which is exact only because it plans
    generated connections alone and each inherits the stock edge class.
    """
    node_type = _make_node_type(f"StockPrefix{total_count}Node", total_count=total_count)
    connection_type = _connection_type_for(node_type, node_type.__django_strawberry_definition__)
    assert _offset_cursor_prefix(connection_type) == relay.Edge.CURSOR_PREFIX


def test_registry_clear_also_clears_offset_cursor_prefix_memo() -> None:
    """``registry.clear()`` drops the per-class offset cursor prefix memo with the class cache."""
    node_type = _make_node_type("PrefixMemoNode", total_count=None)
    _offset_cursor_prefix(
        _connection_type_for(node_type, node_type.__django_strawberry_definition__),
    )
    assert _offset_cursor_prefix.cache_info().currsize
    registry.clear()
    assert not _offset_cursor_prefix.cache_info().currsize


# =============================================================================
# A consumer DjangoConnection subclass whose edge class declares its own prefix
# =============================================================================

#: The ``CURSOR_PREFIX`` the consumer edge class declares in place of ``arrayconnection``.

#: One page walk: three pages of two, forward from ``first`` or backward from ``last``.


@pytest.mark.django_db
@pytest.mark.parametrize("argument", ["after", "before"])
def test_consumer_edge_prefix_refuses_a_stock_cursor(argument: str) -> None:
    """A stock ``arrayconnection`` cursor on a consumer edge prefix is the cursor error.

    The package's own validation refuses it under the connection's prefix,
    so it never reaches ``ListConnection`` as a foreign cursor.
    """
    services.seed_data(1)
    schema = _consumer_edge_schema(_make_node_type("ForeignCursorNode", total_count=None))
    result = schema.execute_sync(_page_query(argument, to_base64(relay.Edge.CURSOR_PREFIX, 0)))
    assert result.errors is not None
    assert result.errors[0].message == f"Argument '{argument}' contains a non-existing value."
    assert isinstance(result.errors[0].original_error, PaginationArgumentError)


@pytest.mark.django_db(transaction=True)
async def test_async_consumer_edge_prefix_pages_and_refuses_a_stock_cursor() -> None:
    """Under async execution a consumer edge prefix pages with its own cursors and refuses a stock one."""
    await sync_to_async(services.seed_data)(1)
    schema = await sync_to_async(_consumer_edge_schema)(
        _make_node_type("AsyncConsumerCursorNode", total_count=None),
    )
    first = await schema.execute(_page_query("after", None))
    assert first.errors is None, first.errors
    assert first.data is not None
    end_cursor = str(json_at(first.data, "items", "pageInfo", "endCursor"))
    assert from_base64(end_cursor) == (_CONSUMER_CURSOR_PREFIX, "1")

    second = await schema.execute(_page_query("after", end_cursor))
    assert second.errors is None, second.errors
    assert second.data is not None
    edges = json_list(second.data, "items", "edges")
    assert [from_base64(str(json_at(edge, "cursor"))) for edge in edges] == [
        (_CONSUMER_CURSOR_PREFIX, "2"),
        (_CONSUMER_CURSOR_PREFIX, "3"),
    ]

    foreign = await schema.execute(_page_query("after", to_base64(relay.Edge.CURSOR_PREFIX, 0)))
    assert foreign.errors is not None
    assert foreign.errors[0].message == "Argument 'after' contains a non-existing value."
    assert isinstance(foreign.errors[0].original_error, PaginationArgumentError)


# spec-033 Slices 1-2: the root-connection fence. The
# root-connection planning pins here (edges { node } extraction ->
# select_related / Prefetch on the pre-slice queryset) hold the ROOT half; the
# shared helper (Decision 9) and the fast path (Decision 5) touch only the
# NESTED half (the spec-033 "no root-connection regression" contract).


# =============================================================================
# Connection <-> cascade composition pin (spec-034). The connection pipeline applies
# get_queryset (where the cascade lives) before filter / order / slice (Decision 12).
# =============================================================================


# =============================================================================
# Sealed-execution boundary at the connection surface
# (docs/SPECS/spec-045-visibility_boundary-0_0_14.md #"## Architectural decisions").
# A hostile hook-return SUBCLASS whose overrides would erase the visibility
# predicate or synthesize rows is neutralized by sealing: edges carry only the
# visible rows and totalCount counts only the visible rows, sync AND async. Each
# test asserts WHICH ROWS SURVIVE, and the seeding makes visible != raw so the
# assertions are not vacuous.
# =============================================================================


# --- Manager failure propagation at the connection surface -------------------


# =============================================================================
# Exception containment and directive validation
# =============================================================================


def test_connection_field_directives_string_rejected() -> None:
    """A string ``directives=`` is rejected as ``ConfigurationError`` (not iterated char-wise)."""
    node = _make_node_type("DirStringNode", total_count=None)
    with pytest.raises(ConfigurationError, match="directives must be a sequence"):
        DjangoConnectionField(node, directives="not-a-sequence")


def test_connection_field_directives_bytes_rejected() -> None:
    """Bytes ``directives=`` is rejected as ``ConfigurationError``."""
    node = _make_node_type("DirBytesNode", total_count=None)
    with pytest.raises(ConfigurationError, match="directives must be a sequence"):
        DjangoConnectionField(node, directives=b"not-a-sequence")


def test_connection_field_directives_iteration_error_propagates() -> None:
    """A ``directives=`` iterable whose ``__iter__`` raises lets that error through.

    Only ``list()``'s documented ``TypeError`` refusal of a non-iterable becomes the
    typed ``ConfigurationError``; an iterable's own iteration error is its behaviour.
    """

    class HostileIter(tuple[object, ...]):
        @override
        def __iter__(self) -> NoReturn:
            raise ValueError("hostile iter")

    class HostileAttr(tuple[object, ...]):
        @override
        def __iter__(self) -> NoReturn:
            raise AttributeError("hostile attr")

    node = _make_node_type("DirHostileNode", total_count=None)
    with pytest.raises(ValueError, match="hostile iter"):
        DjangoConnectionField(node, directives=HostileIter())
    with pytest.raises(AttributeError, match="hostile attr"):
        DjangoConnectionField(node, directives=HostileAttr())


@pytest.mark.parametrize("raised", [ValueError, KeyError])
def test_window_rows_are_annotated_iteration_error_propagates(raised: type[Exception]) -> None:
    """``_window_rows_are_annotated`` iterates the rows on their own terms; errors propagate."""

    class HostileList(list[object]):
        @override
        def __iter__(self) -> NoReturn:
            raise raised("hostile iter")

    with pytest.raises(raised, match="hostile iter"):
        _window_rows_are_annotated(HostileList([object()]))


def test_keyset_order_ref_unparseable_entry_returns_none() -> None:
    """``_keyset_order_ref`` answers ``None`` for an entry with no resolvable name."""
    assert _keyset_order_ref(None) is None


def test_keyset_order_ref_attribute_read_error_propagates() -> None:
    """An entry whose attribute read raises lets that error through, never ``None``."""

    class Hostile:
        def __getattr__(self, name: str) -> NoReturn:
            raise ValueError("hostile getattr")

    with pytest.raises(ValueError, match="hostile getattr"):
        _keyset_order_ref(Hostile())


def test_consume_window_malformed_pagination_is_graphql_error() -> None:
    """A windowed ``_WindowedConnectionRows`` with ``first: -1`` is ``GraphQLError`` (not ``ValueError``)."""
    node = _make_sidecar_node_type("WindowMalformedNode")
    finalize_django_types()
    conn_type = _connection_type_for(node, node.__django_strawberry_definition__)
    # Create a window marker with one annotated row

    row = Category(id=1, name="a")
    setattr(row, WINDOW_ROW_NUMBER, 1)
    window = _WindowedConnectionRows(rows=[row], fallback=Category.objects.all)
    info = make_info(
        context={},
        field_name="items",
        selections="{ edges }",
        config=strawberry_config(),
    )
    with pytest.raises(GraphQLError, match="non-negative"):
        conn_type.resolve_connection(window, info=info, first=-1)


# =============================================================================
# The captured definition: one read at construction, none at runtime
# =============================================================================


@pytest.mark.django_db
def test_a_relay_target_with_no_registered_definition_fails_the_synthesized_connection() -> None:
    """A registered Relay primary carrying no definition is a framework defect, named as one.

    The synthesized relation connection is built from the registry's definition,
    so the one state that cannot produce one - a primary registered without it -
    fails loudly rather than silently degrading the declared shape to a list.
    """

    @strawberry.type
    class BareNode(relay.Node):
        id: relay.NodeID[int]

    class BareParentNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")
            interfaces = (relay.Node,)
            name = "BareParentNode"
            relation_shapes = {"items": "connection"}
            primary = False

    assert registry.get(Category) is BareParentNode

    # basedpyright: the Relay node registered without a definition is the hostile input under test;
    # TypeRegistry.register types the parameter as type[DjangoType]
    registry.register(Item, BareNode, primary=True)  # pyright: ignore[reportArgumentType]
    with pytest.raises(ConfigurationError, match="carries no registered DjangoTypeDefinition"):
        finalize_django_types()


#: One relation, two vocabularies. Planning them from separate documents keeps a
#: regression in one from hiding behind the other's rows in the same response.


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("vocabulary", "document"),
    [("List", _PLANNED_LIST_DOCUMENT), ("Connection", _PLANNED_CONNECTION_DOCUMENT)],
    ids=["list", "connection"],
)
@pytest.mark.parametrize("custom_hook", [False, True], ids=["default-hook", "custom-hook"])
def test_the_optimizer_plans_a_relation_without_reading_the_target_class(
    vocabulary: str,
    document: str,
    *,
    custom_hook: bool,
) -> None:
    """Planning a nested relation spends the walker's resolution, not a fresh read.

    The optimizer plans the same field the finalizer already resolved, and every
    decision it makes about the TARGET - whether the visibility hook runs over the
    child queryset, which model that queryset's seal validates against, and which
    cursor vocabulary the window derives through - comes from the child definition
    ``related_target_for`` handed back. The target's definition attribute is
    replaced by a decoy over a DIFFERENT MODEL once the schema is built, so a
    residual read would move the planned prefetch to another table.

    Both hook flavours run because they need different halves of the capture: a
    hook-less target never enters the visibility runner, while a hook-bearing one
    does and must find the captured model already there. Both plan states are
    covered too, and the cold and warm requests are asserted apart, each against
    the cache counters that say which state it ran in. Calling a second request
    "warm" without reading those counters would pass just as well if caching had
    stopped altogether.

    Package-side because the claim is which definition the plan was built from,
    which no response names; the decoy makes a residual read consequential. The
    consequence has live siblings -
    ``examples/fakeshop/test_query/test_products_visibility_api.py``'s
    planned-relation rows and
    ``examples/fakeshop/test_query/test_keyset_api.py::test_nested_keyset_window_hides_embargoed_rows_and_counts_them_out``
    pin the rows a mis-answered plan would serve.
    """
    services.seed_data(3)
    hook_calls: list[type[models.Model]] | None = [] if custom_hook else None
    suffix = f"{vocabulary}{'Hooked' if custom_hook else 'Bare'}"

    schema, optimizer = _planned_relation_schema(suffix, hook_calls=hook_calls)
    assert optimizer.cache_info().size == 0, optimizer.cache_info()

    item_names = set(Item.objects.values_list("name", flat=True))
    # A hook-less plan is cacheable, so its second request is a hit on the stored
    # entry; a plan carrying a hook is deliberately not cached and is rebuilt.
    cold_cache, warm_cache = ((0, 1, 0), (0, 2, 0)) if custom_hook else ((0, 1, 1), (1, 1, 1))

    cold_rows, cold_counters = _planned_relation_request(schema, optimizer, document, vocabulary)
    assert cold_counters == cold_cache, cold_counters
    assert cold_rows, cold_rows
    assert cold_rows <= item_names, cold_rows

    warm_rows, warm_counters = _planned_relation_request(schema, optimizer, document, vocabulary)
    assert warm_counters == warm_cache, warm_counters
    assert warm_rows == cold_rows, (warm_rows, cold_rows)

    if custom_hook:
        # The hook has to have RUN for its request to say anything about the
        # model the runner was handed.
        assert hook_calls == [Item, Item], hook_calls


@pytest.mark.django_db
def test_a_warm_connection_cache_refuses_alternate_metadata_for_its_target() -> None:
    """A second definition for one target is rejected, not silently served the first shape.

    The cache is keyed on target identity, so a warm hit returns a class whose
    ``totalCount`` shape, SDL name and keyset vocabulary were fixed by whichever
    definition arrived first. A caller holding different metadata would get its
    own published arguments beside somebody else's return class - the exact
    split answer the one-definition rule forbids. The entry therefore records
    the definition it was generated from and refuses anything else.

    Package-side for the same reason as the rest of this file's construction
    rows: presenting two definitions for one target is something a schema author
    does at construction and a request cannot express.
    """

    class CacheProvenanceNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CacheProvenanceNode"
            primary = False

    real = CacheProvenanceNode.__django_strawberry_definition__
    finalize_django_types()
    clear_connection_type_cache()

    warm = _connection_type_for(CacheProvenanceNode, real)
    assert _connection_type_for(CacheProvenanceNode, real) is warm
    assert "total_count" not in {
        field.python_name for field in get_object_definition(warm, strict=True).fields
    }

    replacement = copy.copy(real)
    replacement.connection = {"total_count": True}
    with pytest.raises(ConfigurationError, match="built from a different DjangoTypeDefinition"):
        _connection_type_for(CacheProvenanceNode, replacement)
    # And the rejection did not disturb the entry the real definition owns.
    assert _connection_type_for(CacheProvenanceNode, real) is warm


# --- Post-FilterSet seal at the connection field -----------------------------


#: The post-``FilterSet`` seal at the connection field, one row per defect shape.
#: ``(id, override, expected message start, required substrings)``. The filter
#: step runs BEFORE ordering and the Relay window, so an unsealed return would
#: hand every later step a widened, re-routed or already-evaluated queryset.
