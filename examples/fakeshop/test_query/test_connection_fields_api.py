"""Live HTTP root-connection sources, pagination, sidecars and visibility contracts.

Each consumer declaration crosses the package view with real rows and request context.
The responses and SQL distinguish source validation, pagination, sidecars and visibility.
"""

import asyncio
from collections.abc import AsyncIterator, Callable, Iterable
from functools import wraps
from typing import TYPE_CHECKING, Literal, TypeVar

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from asgiref.sync import sync_to_async
from django.db import models
from django.db.models.sql import Query
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import JSONObject, json_str
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import (
    DjangoConnectionField,
    _connection_type_cache,
    _connection_type_for,
    clear_connection_type_cache,
)
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import AsyncTestClient, Response, TestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._catalog_data import categories_from_seed, items_from_seed
from tests._connection_field_schemas import (
    _CONNECTION_MALFORMED_FILTER_ROWS,
    _CONNECTION_MALFORMED_ORDER_ROWS,
    _CONSUMER_WALK_PAGES,
    _FILTERED_CONNECTION_QUERY,
    _a_or_b_category_names,
    _alias_drift_manager,
    _CategoryFilter,
    _CategoryOrder,
    _combined_get_queryset,
    _consumer_edge_schema,
    _degrading_manager,
    _edge_names,
    _field_schema,
    _hostile_visibility_hook,
    _item_node_type,
    _make_cascading_item_node,
    _make_node_type,
    _make_relation_node_type,
    _make_sidecar_node_type,
    _node_type,
    _order_override_passthrough,
    _schema_for,
    _seed_public_private_categories,
    _swap_prefix,
    _walk_pages,
)
from tests._idioms import declare_django_type, json_at, json_list, json_object

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedASGIResponse, _MonkeyPatchedWSGIResponse

_M = TypeVar("_M", bound=models.Model)

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, strawberry.Schema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-connection/", _graphql_view),
    path("graphql-connection-async/", _async_graphql_view),
]


def _post(schema: strawberry.Schema, query: str) -> "Response[_MonkeyPatchedWSGIResponse]":
    """Send one ordinary operation through the package's sync HTTP view."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            result = TestClient(path="/graphql-connection/").query(query, assert_no_errors=False)
        assert result.response.status_code == 200
        return result
    finally:
        _CURRENT["schema"] = None


async def _post_async(
    schema: strawberry.Schema,
    query: str,
) -> "Response[_MonkeyPatchedASGIResponse]":
    """Send one ordinary operation through the package's async HTTP view."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            result = await AsyncTestClient(path="/graphql-connection-async/").query(
                query,
                assert_no_errors=False,
            )
        assert result.response.status_code == 200
        return result
    finally:
        _CURRENT["schema"] = None


def _sync_executor(schema: strawberry.Schema) -> Callable[[str], JSONObject]:
    """Return an HTTP page executor for the consumer's cursor walk."""

    def execute(query: str) -> JSONObject:
        result = _post(schema, query)
        assert result.errors is None, result.errors
        assert result.data is not None
        return result.data

    return execute


@pytest.mark.django_db(transaction=True)
async def test_async_opted_connection_reports_the_whole_set_count() -> None:
    """An async opted connection returns one edge and the count of the whole queryset."""
    await sync_to_async(services.seed_data)(2)
    expected = await Category.objects.acount()

    schema = await sync_to_async(_schema_for)(_make_node_type("AsyncCountNode", total_count=True))
    result = await _post_async(schema, "{ items(first: 1) { edges { node { id } } totalCount } }")
    assert result.errors is None
    assert result.data is not None
    assert len(json_list(result.data, "items", "edges")) == 1
    assert result.data["items"]["totalCount"] == expected


@pytest.mark.django_db
def test_consumer_resolver_manager_coerced() -> None:
    """A Manager consumer source serves exactly its rows through the connection pipeline."""
    services.seed_data(2)

    def resolver(_root: object, _info: object) -> models.Manager[Category]:
        return Category.objects  # a Manager, not a QuerySet

    schema = _field_schema(_make_sidecar_node_type("ManagerNode"), resolver=resolver)
    result = _post(schema, "{ items { edges { node { name } } } }")
    assert result.errors is None
    assert result.data is not None
    names = _edge_names(json_at(result.data, "items"))
    assert sorted(names) == sorted(Category.objects.values_list("name", flat=True))


@pytest.mark.django_db
def test_consumer_resolver_queryset_full_pipeline() -> None:
    """A consumer QuerySet source is filtered, ordered, counted and sliced over HTTP."""
    services.seed_data(0)
    categories_from_seed(("Keep Alpha", False), ("Other Bravo", False), ("Keep Charlie", False))

    def resolver(_root: object, _info: object) -> Iterable[object]:
        return Category.objects.all()

    schema = _field_schema(
        _make_sidecar_node_type("QuerySetNode", total_count=True),
        resolver=resolver,
    )
    result = _post(
        schema,
        '{ items(first: 1, filter: {name: {iContains: "Keep"}}, orderBy: [{name: DESC}]) '
        "{ edges { node { name } } totalCount } }",
    )
    assert result.errors is None, result.errors
    assert _edge_names(json_at(result.data, "items")) == ["Keep Charlie"]
    assert json_at(result.data, "items", "totalCount") == 2


@pytest.mark.django_db
def test_consumer_resolver_iterable_without_sidecar_input_paginates() -> None:
    """A non-queryset iterable with NO sidecar input paginates normally."""
    services.seed_data(1)
    rows = list(Category.objects.order_by("pk"))

    def resolver(_root: object, _info: object) -> Iterable[object]:
        return list(rows)  # a plain list

    schema = _field_schema(_make_sidecar_node_type("IterableOkNode"), resolver=resolver)
    result = _post(schema, "{ items(first: 1) { edges { node { name } } } }")
    assert result.errors is None
    assert result.data is not None
    assert _edge_names(json_at(result.data, "items")) == [rows[0].name]


@pytest.mark.django_db
def test_consumer_resolver_iterable_with_sidecar_input_raises() -> None:
    """A non-queryset iterable WITH ``filter:`` / ``orderBy:`` input raises a package error."""
    services.seed_data(1)
    rows = list(Category.objects.all())

    def resolver(_root: object, _info: object) -> Iterable[object]:
        return list(rows)

    schema = _field_schema(_make_sidecar_node_type("IterableBadNode"), resolver=resolver)
    result = _post(schema, '{ items(filter: {name: {exact: "x"}}) { edges { node { id } } } }')
    assert result.errors is not None
    assert any("non-queryset iterable" in str(json_str(err, "message")) for err in result.errors)


@pytest.mark.django_db
def test_consumer_resolver_iterable_with_total_count_selected_raises() -> None:
    """Selecting ``totalCount`` over a non-queryset consumer return raises a package error.

    NOT the engine's ``Cannot return null for non-nullable field ...totalCount``
    violation - the count helper raises a clear ``GraphQLError`` because a plain
    iterable cannot be ``.count()``-ed into the non-null ``totalCount: Int!``.
    """
    services.seed_data(1)
    rows = list(Category.objects.all())

    def resolver(_root: object, _info: object) -> Iterable[object]:
        return list(rows)

    schema = _field_schema(
        _make_sidecar_node_type("IterableTotalCountNode", total_count=True),
        resolver=resolver,
    )
    result = _post(schema, "{ items { edges { node { id } } totalCount } }")
    assert result.errors is not None
    messages = [str(json_str(err, "message")) for err in result.errors]
    assert any("totalCount" in m and "non-queryset iterable" in m for m in messages)
    assert not any("Cannot return null for non-nullable field" in m for m in messages)


@pytest.mark.django_db
@pytest.mark.parametrize("make_source", [iter, set, frozenset])
def test_consumer_resolver_countless_iterable_paginates_without_total_count(
    make_source: Callable[[list[Category]], Iterable[object]],
) -> None:
    """A count-less non-queryset source paginates with ``totalCount`` NOT selected.

    ``_attach_count_sync`` must not read ``.count`` eagerly: passing
    ``value=nodes.count`` when the count is NOT requested is itself an eager
    attribute access, so a generator / set / one-shot iterator (shapes the
    consumer-resolver contract admits) would raise a raw
    ``AttributeError: 'set' object has no attribute 'count'`` on every page
    without ``totalCount``. The read is gated on ``want_count`` exactly
    like the async helper's ``acount()`` call.
    """
    services.seed_data(3)
    rows = list(Category.objects.order_by("pk"))[1:]

    def resolver(_root: object, _info: object) -> Iterable[object]:
        return make_source(rows)

    schema = _field_schema(
        _make_sidecar_node_type("CountlessIterableNode", total_count=True),
        resolver=resolver,
    )
    result = _post(schema, "{ items(first: 1) { edges { node { name } } } }")
    assert result.errors is None
    assert result.data is not None
    names = _edge_names(json_at(result.data, "items"))
    assert len(names) == 1
    assert names[0] in {row.name for row in rows}


@pytest.mark.django_db
def test_consumer_resolver_generator_paginates_without_total_count() -> None:
    """A generator return paginates normally when ``totalCount`` is not selected.

    Generators are NAMED in the consumer-``resolver=`` contract (a non-queryset
    iterable may be paginated when no ``filter:`` / ``orderBy:`` input is
    supplied). The eager ``.count`` attribute read in ``_attach_count_sync``
    broke that contract outright: ``AttributeError: 'generator' object has no
    attribute 'count'`` on every page without ``totalCount``. This is the
    schema-level pin of the gated read; the opted connection shape proves the
    count was not merely requested-and-skipped.
    """
    services.seed_data(2)
    rows = list(Category.objects.order_by("pk"))

    def resolver(_root: object, _info: object) -> Iterable[object]:
        yield from rows

    schema = _field_schema(
        _make_sidecar_node_type("GeneratorSourceNode", total_count=True),
        resolver=resolver,
    )
    result = _post(
        schema,
        "{ items(first: 1) { pageInfo { hasNextPage } edges { node { name } } } }",
    )
    assert result.errors is None
    assert result.data is not None
    assert _edge_names(json_at(result.data, "items")) == [rows[0].name]
    assert json_at(result.data, "items", "pageInfo", "hasNextPage") is True


@pytest.mark.django_db
@pytest.mark.parametrize("bad_source", [None, 42])
def test_consumer_resolver_non_iterable_source_raises_graphql_error(bad_source: object) -> None:
    """A scalar source fails closed with a package error, not a blank AssertionError.

    ``None`` / an ``int`` are neither QuerySet nor iterable; Relay's slicer
    first slice-subscripts (``TypeError``), then trips its own bare
    ``assert isinstance(nodes, (Iterable, Iterator))`` - an empty-message
    ``AssertionError`` at the GraphQL boundary. The pipeline's shape gate
    refuses the source instead.
    """
    services.seed_data(1)

    def resolver(_root: object, _info: object) -> object:
        return bad_source

    schema = _field_schema(_make_sidecar_node_type("ScalarSourceNode"), resolver=resolver)
    result = _post(schema, "{ items(first: 1) { edges { node { id } } } }")

    assert result.errors is not None
    messages = [str(json_str(err, "message")) for err in result.errors]
    assert any("neither a QuerySet" in m and "plain iterable" in m for m in messages)


@pytest.mark.django_db(transaction=True)
async def test_async_consumer_resolver_set_source_paginates_without_total_count() -> None:
    """Async path: a set source paginates with ``totalCount`` unselected (no raw leak).

    The async execution reaches the SAME ``_attach_count_sync`` (a set is not
    an ``AsyncIterator``, so Relay's async resolver branch does not fire and
    the count helper runs synchronously); before the gate the eager
    ``.count`` read leaked ``AttributeError`` here too.
    """
    await sync_to_async(services.seed_data)(2)
    rows = await sync_to_async(lambda: list(Category.objects.order_by("pk"))[1:])()

    async def resolver(_root: object, _info: object) -> Iterable[object]:
        return set(rows)

    schema = await sync_to_async(_field_schema)(
        _make_sidecar_node_type("AsyncSetSourceNode", total_count=True),
        resolver=resolver,
    )
    result = await _post_async(schema, "{ items(first: 1) { edges { node { name } } } }")
    assert result.errors is None
    assert result.data is not None
    names = _edge_names(json_at(result.data, "items"))
    assert len(names) == 1
    assert names[0] in {row.name for row in rows}


@pytest.mark.django_db(transaction=True)
async def test_async_consumer_resolver_iterable_with_total_count_selected_raises() -> None:
    """End-to-end on the async path: a clear package error, NOT the engine non-null violation.

    An ``async def`` consumer ``resolver=`` returning a non-queryset iterable while
    ``totalCount`` is selected drives ``_attach_count_async`` through the real
    ``resolve_connection`` async path. The guard's ``GraphQLError`` surfaces (NOT the
    engine ``Cannot return null for non-nullable field ...totalCount`` violation). The
    deterministic no-leak assertion lives in
    ``test_attach_count_async_awaits_before_guard_raises``.
    """
    await sync_to_async(services.seed_data)(1)
    rows = await sync_to_async(lambda: list(Category.objects.all()))()

    async def resolver(_root: object, _info: object) -> Iterable[object]:
        return list(rows)

    schema = await sync_to_async(_field_schema)(
        _make_sidecar_node_type("AsyncIterableTotalCountNode", total_count=True),
        resolver=resolver,
    )
    result = await _post_async(schema, "{ items { edges { node { id } } totalCount } }")

    assert result.errors is not None
    messages = [str(json_str(err, "message")) for err in result.errors]
    assert any("totalCount" in m and "non-queryset iterable" in m for m in messages)
    assert not any("Cannot return null for non-nullable field" in m for m in messages)


@pytest.mark.django_db
def test_connection_resolver_composition_order() -> None:
    """Public hooks run visibility, filter and order before the counted page is sliced."""
    services.seed_data(0)
    categories_from_seed(
        ("Keep Alpha", False),
        ("Other Bravo", False),
        ("Keep Charlie", False),
        ("Keep Hidden", True),
    )
    calls: list[str] = []

    def get_queryset(
        _cls: type[DjangoType],
        qs: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        calls.append("visibility")
        return qs.filter(is_private=False)

    class _OrderedFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["icontains"]}

        @classmethod
        @override
        def apply_sync(
            cls,
            input_value: object,
            queryset: models.QuerySet[_M],
            info: object,
            *,
            run_permissions: bool = True,
            _depth: int = 0,
            _branch_path: str = "",
        ) -> models.QuerySet[_M]:
            calls.append("filter")
            return super().apply_sync(
                input_value,
                queryset,
                info,
                run_permissions=run_permissions,
                _depth=_depth,
                _branch_path=_branch_path,
            )

    class _OrderedOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

        @classmethod
        @override
        def apply_sync(
            cls,
            input_value: object,
            queryset: models.QuerySet[_M],
            info: object,
        ) -> models.QuerySet[_M]:
            calls.append("order")
            return super().apply_sync(input_value, queryset, info)

    node_type = _make_sidecar_node_type(
        "CompositionNode",
        total_count=True,
        filterset=_OrderedFilter,
        orderset=_OrderedOrder,
        get_queryset=get_queryset,
    )
    schema = _field_schema(node_type)
    result = _post(
        schema,
        """
                 {
                   items(first: 1, filter: {name: {iContains: "Keep"}}, orderBy: [{name: DESC}]) {
                     edges {
                       node {
                         name
                       }
                     }
                     totalCount
                   }
                 }
                 """,
    )
    assert result.errors is None
    assert calls == ["visibility", "filter", "order"]
    assert result.data is not None
    assert _edge_names(json_at(result.data, "items")) == ["Keep Charlie"]
    # totalCount counts the full post-filter pre-slice set, not the sliced page.
    assert result.data["items"]["totalCount"] == 2


@pytest.mark.django_db
def test_relay_max_results_cap() -> None:
    """A consumer relay_max_results setting refuses an oversized page and accepts its limit."""
    services.seed_data(2)
    schema = _field_schema(
        _make_node_type("MaxResultsNode", total_count=None),
        config=strawberry_config(relay_max_results=2),
    )

    over_cap = _post(schema, "{ items(first: 3) { edges { node { id } } } }")
    assert over_cap.errors is not None
    assert len(over_cap.errors) == 1
    assert json_str(over_cap.errors[0], "message") == "Argument 'first' cannot be higher than 2."
    assert over_cap.data is None

    at_cap = _post(schema, "{ items(first: 2) { edges { node { id } } } }")
    assert at_cap.errors is None
    assert at_cap.data is not None
    assert len(json_list(at_cap.data, "items", "edges")) == 2


@pytest.mark.django_db(transaction=True)
async def test_connection_resolver_async_dispatch() -> None:
    """The default resolver returns an async HTTP page and counts the full source."""
    await sync_to_async(services.seed_data)(2)
    expected = await Category.objects.acount()
    schema = await sync_to_async(_field_schema)(
        _make_sidecar_node_type("AsyncDispatchNode", total_count=True),
    )
    result = await _post_async(schema, "{ items(first: 1) { edges { node { id } } totalCount } }")
    assert result.errors is None
    assert result.data is not None
    assert len(json_list(result.data, "items", "edges")) == 1
    assert result.data["items"]["totalCount"] == expected


@pytest.mark.django_db(transaction=True)
async def test_connection_async_generator_resolver_executes_on_async_path() -> None:
    """An async-generator consumer source serves its first row through async HTTP."""
    await sync_to_async(services.seed_data)(2)
    rows = await sync_to_async(list)(Category.objects.order_by("pk"))

    async def resolver(_root: object, _info: object) -> AsyncIterator[Category]:
        for row in rows:
            yield row

    schema = await sync_to_async(_field_schema)(
        _make_sidecar_node_type("AsyncGeneratorExecutionNode"),
        resolver=resolver,
    )
    result = await _post_async(schema, "{ items(first: 1) { edges { node { name } } } }")
    assert result.errors is None, result.errors
    assert result.data is not None
    assert _edge_names(json_at(result.data, "items")) == [rows[0].name]


@pytest.mark.django_db
@pytest.mark.parametrize("strictness", ["raise", "off"])
def test_nested_connection_unplanned_raises_under_strictness(
    strictness: Literal["raise", "off"],
) -> None:
    """A materialized connection source leaves nested lazy loads visible to the real strictness policy."""
    services.seed_data(2)
    _make_relation_node_type("NestedGapItemNode", fields=("id", "name"), model=Item)
    category_node = _make_relation_node_type(
        "NestedGapCatNode",
        fields=("id", "name", "items"),
        list_relations=("items",),
    )

    def resolver(_root: object, _info: object) -> list[Category]:
        return list(Category.objects.order_by("pk"))

    schema = _field_schema(
        category_node,
        resolver=resolver,
        optimizer=DjangoOptimizerExtension(strictness=strictness),
    )
    result = _post(schema, "{ items { edges { node { name items { name } } } } }")
    if strictness == "raise":
        assert result.errors is not None
        assert any("Unplanned N+1: items" in json_str(error, "message") for error in result.errors)
    else:
        assert result.errors is None, result.errors
        served = {
            str(json_at(edge, "node", "name")): sorted(
                json_str(item, "name") for item in json_list(edge, "node", "items")
            )
            for edge in json_list(result.data, "items", "edges")
        }
        expected = {
            category.name: sorted(category.items.values_list("name", flat=True))
            for category in Category.objects.order_by("pk")
        }
        assert served == expected


@pytest.mark.django_db(transaction=True)
async def test_connection_async_pipeline_applies_filter_and_order() -> None:
    """Async sidecars filter and reorder a consumer source before counting and slicing."""
    await sync_to_async(services.seed_data)(0)
    await sync_to_async(categories_from_seed)(
        ("Keep Alpha", False),
        ("Other Bravo", False),
        ("Keep Charlie", False),
    )

    async def resolver(_root: object, _info: object) -> models.QuerySet[Category]:
        return Category.objects.all()

    node_type = _make_sidecar_node_type("AsyncFilterOrderNode", total_count=True)
    schema = await sync_to_async(_field_schema)(node_type, resolver=resolver)
    result = await _post_async(
        schema,
        '{ items(first: 1, filter: {name: {iContains: "Keep"}}, orderBy: [{name: DESC}]) '
        "{ edges { node { name } } totalCount } }",
    )
    assert result.errors is None, result.errors
    assert _edge_names(json_at(result.data, "items")) == ["Keep Charlie"]
    assert json_at(result.data, "items", "totalCount") == 2


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("override", "message_start", "substrings"),
    [row[1:] for row in _CONNECTION_MALFORMED_ORDER_ROWS],
    ids=[row[0] for row in _CONNECTION_MALFORMED_ORDER_ROWS],
)
def test_connection_seals_a_malformed_apply_sync_result(
    monkeypatch: pytest.MonkeyPatch,
    override: Callable[..., object],
    message_start: str,
    substrings: tuple[str, ...],
) -> None:
    """Each malformed ``apply_sync`` result is rejected by name at the connection field.

    The connection runs the SAME post-``OrderSet`` seal the list field runs, so
    every defect shape the seal can name has to arrive here too; without it the
    Relay window is taken on whatever came back.
    """
    services.seed_data(2)
    monkeypatch.setattr(_CategoryOrder, "apply_sync", classmethod(override))

    schema = _field_schema(_make_sidecar_node_type("SealedOrderNode"))
    result = _post(schema, "{ items(orderBy: [{name: ASC}]) { edges { node { name } } } }")

    assert result.errors is not None
    assert result.data is None
    message = str(json_str(result.errors[0], "message"))
    assert message.startswith(message_start), message
    for substring in substrings:
        assert substring in message, message


@pytest.mark.django_db
def test_connection_healthy_apply_sync_override_still_orders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``super()`` pass-through override is ACCEPTED and yields the ordered page.

    The seal's positive control: it rejects malformed results without rejecting
    a consumer ``OrderSet`` that simply delegates.
    """
    services.seed_data(0)
    categories_from_seed(("Charlie", False), ("Alpha", False), ("Bravo", False))
    monkeypatch.setattr(_CategoryOrder, "apply_sync", classmethod(_order_override_passthrough))

    schema = _field_schema(_make_sidecar_node_type("HealthyOrderNode"))
    result = _post(schema, "{ items(orderBy: [{name: ASC}]) { edges { node { name } } } }")

    assert result.errors is None, result.errors
    assert result.data is not None
    names = _edge_names(json_at(result.data, "items"))
    assert names == ["Alpha", "Bravo", "Charlie"]


@pytest.mark.django_db(transaction=True)
def test_connection_async_seal_rejects_a_non_awaitable_apply_async(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``apply_async`` returning a plain value is rejected on the connection's async path."""

    def _plain_apply_async(
        _cls: type[_CategoryOrder],
        _order_input: object,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        return queryset

    monkeypatch.setattr(_CategoryOrder, "apply_async", classmethod(_plain_apply_async))

    async def resolver(_root: object, _info: object) -> models.QuerySet[Category]:
        return Category.objects.all()

    schema = _field_schema(_make_sidecar_node_type("AsyncSealNonAwaitableNode"), resolver=resolver)
    result = asyncio.run(
        _post_async(schema, "{ items(orderBy: [{ name: ASC }]) { edges { node { name } } } }"),
    )

    assert result.errors is not None
    assert str(json_str(result.errors[0], "message")).startswith(
        "_CategoryOrder.apply_async returned a non-awaitable value",
    )


@pytest.mark.django_db(transaction=True)
def test_connection_async_seal_rejects_a_sliced_apply_async_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sliced ``apply_async`` result is rejected with the shared shape wording."""

    async def _sliced(
        _cls: type[_CategoryOrder],
        _order_input: object,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        return queryset.order_by("name")[:1]

    monkeypatch.setattr(_CategoryOrder, "apply_async", classmethod(_sliced))

    async def resolver(_root: object, _info: object) -> models.QuerySet[Category]:
        return Category.objects.all()

    schema = _field_schema(_make_sidecar_node_type("AsyncSealSlicedNode"), resolver=resolver)
    result = asyncio.run(
        _post_async(schema, "{ items(orderBy: [{ name: ASC }]) { edges { node { name } } } }"),
    )

    assert result.errors is not None
    assert str(json_str(result.errors[0], "message")).startswith(
        "_CategoryOrder.apply_async must return an unevaluated, unsliced "
        "QuerySet of Category rows; got sliced defect",
    )


@pytest.mark.django_db
@pytest.mark.parametrize("argument", ["after", "before"])
def test_consumer_edge_prefix_pages_with_its_own_cursors(argument: str) -> None:
    """A consumer edge prefix pages with the cursors it mints, as the stock connection does.

    Each page is requested from the previous page's own cursor; the walk is the
    stock connection's walk over the same rows with only the prefix changed.
    """
    services.seed_data(1)
    stock = _walk_pages(
        _sync_executor(_schema_for(_make_node_type("StockWalkNode", total_count=None))),
        argument,
    )
    registry.clear()
    consumer = _walk_pages(
        _sync_executor(_consumer_edge_schema(_make_node_type("StockWalkNode", total_count=None))),
        argument,
    )
    assert len(stock) == 2 * _CONSUMER_WALK_PAGES
    assert {prefix for _node_id, (prefix, _index) in stock} == {relay.Edge.CURSOR_PREFIX}
    assert consumer == _swap_prefix(stock)


@pytest.mark.django_db
def test_connection_over_cascading_type_narrows_edges_and_total_count() -> None:
    """A counted Item connection drops rows under private categories through cascade visibility."""
    services.seed_data(2)

    class CcCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: models.QuerySet[Category],
            info: object,
        ) -> models.QuerySet[Category]:
            return queryset.filter(is_private=False)

    assert registry.get(Category) is CcCategoryType

    item_node = _make_cascading_item_node("CcItemNode")
    schema = _field_schema(item_node)

    public_cat, private_cat = categories_from_seed(("public_cat", False), ("private_cat", True))
    visible_a, visible_b = items_from_seed(public_cat, ("visible_a", False), ("visible_b", False))
    items_from_seed(private_cat, ("hidden", False))

    result = _post(
        schema,
        """
                 {
                   items {
                     edges {
                       cursor
                       node {
                         id
                         name
                       }
                     }
                     pageInfo {
                       hasNextPage
                       hasPreviousPage
                     }
                     totalCount
                   }
                 }
                 """,
    )
    assert result.errors is None
    assert result.data is not None
    conn = json_object(result.data, "items")
    # edges: only the two items under the visible category; the hidden-target item
    # is dropped by the cascade.
    edge_names = _edge_names(conn)
    assert edge_names == [visible_a.name, visible_b.name]
    # totalCount counts the post-visibility set (2), NOT the raw 3 rows.
    assert conn["totalCount"] == 2
    # Cursors are consistent: present, distinct, one per edge.
    cursors = [json_at(edge, "cursor") for edge in json_list(conn, "edges")]
    assert all(cursors)
    assert len(set(cursors)) == len(cursors)
    # No further pages over the narrowed set.
    assert json_at(conn, "pageInfo", "hasNextPage") is False
    assert json_at(conn, "pageInfo", "hasPreviousPage") is False


@pytest.mark.django_db
def test_consumer_resolver_pre_sliced_queryset_raises_clear_error() -> None:
    """A pre-sliced consumer queryset raises a clear ``GraphQLError``, not a raw ``TypeError``.

    ``_finalize_queryset`` appends the deterministic total-order tiebreaker with
    ``order_by``, which Django forbids on a sliced queryset (``TypeError: Cannot
    reorder a query once a slice has been taken``). ``Category._meta.ordering`` is
    empty, so an unordered slice always trips the reorder. That raw internal must
    not leak to the client: the connection boundary must reject a pre-sliced
    source with a clear, actionable ``GraphQLError``, symmetric with the existing
    non-queryset-iterable guard.
    """
    services.seed_data(2)

    def resolver(_root: object, _info: object) -> Iterable[object]:
        return Category.objects.all()[:5]  # already sliced before the pipeline reorders

    schema = _field_schema(_make_sidecar_node_type("PreSlicedNode"), resolver=resolver)
    result = _post(schema, "{ items { edges { node { id } } } }")

    assert result.errors is not None
    messages = [str(json_str(err, "message")) for err in result.errors]
    # The raw Django internal must NOT leak to the client...
    assert not any("Cannot reorder a query once a slice has been taken" in m for m in messages)
    # ...it is replaced by the connection's clear pre-sliced guard.
    assert any("already-sliced" in m for m in messages)


@pytest.mark.django_db
def test_connection_hostile_hook_narrows_edges_and_total_count_sync() -> None:
    """A hostile-subclass hook through ``DjangoConnectionField`` narrows edges + totalCount (sync)."""
    services.seed_data(0)
    public_names = _seed_public_private_categories()
    node_type = _make_sidecar_node_type(
        "HostileConnNode",
        total_count=True,
        filterset=None,
        orderset=None,
        get_queryset=_hostile_visibility_hook,
    )
    schema = _field_schema(node_type)
    result = _post(schema, "{ items { edges { node { name } } totalCount } }")
    assert result.errors is None
    assert result.data is not None
    conn = json_object(result.data, "items")
    assert _edge_names(conn) == public_names
    assert conn["totalCount"] == len(public_names)  # only the visible rows, not the raw 3


@pytest.mark.django_db(transaction=True)
async def test_connection_hostile_hook_narrows_edges_and_total_count_async() -> None:
    """Async twin: the hostile ``.acount()`` / slicing overrides are sealed away too."""
    await sync_to_async(services.seed_data)(0)
    public_names = await sync_to_async(_seed_public_private_categories)()
    node_type = _make_sidecar_node_type(
        "AsyncHostileConnNode",
        total_count=True,
        filterset=None,
        orderset=None,
        get_queryset=_hostile_visibility_hook,
    )
    schema = await sync_to_async(_field_schema)(node_type)
    result = await _post_async(schema, "{ items { edges { node { name } } totalCount } }")
    assert result.errors is None
    assert result.data is not None
    conn = json_object(result.data, "items")
    assert _edge_names(conn) == public_names
    assert conn["totalCount"] == len(public_names)


@pytest.mark.django_db
def test_connection_instance_shadowed_all_hook_is_sealed() -> None:
    """A hook returning a PLAIN queryset with an instance-shadowed ``.all()`` is sealed.

    The seal reads the queryset's state from ``__dict__`` via
    ``object.__getattribute__``, never through attribute access, so an instance
    attribute ``all`` shadowing the method (which would drop the predicate if the
    framework called ``.all()``) cannot lie or run: only the visible rows are served.
    """
    services.seed_data(0)
    public_names = _seed_public_private_categories()

    def _shadowed_all_hook(
        _cls: type[DjangoType],
        _qs: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        source = Category.objects.filter(is_private=False)
        source.all = Category.objects.all  # instance shadow (predicate-dropping)
        return source

    node_type = _make_sidecar_node_type(
        "ShadowAllConnNode",
        filterset=None,
        orderset=None,
        get_queryset=_shadowed_all_hook,
    )
    schema = _field_schema(node_type)
    result = _post(schema, "{ items { edges { node { name } } } }")
    assert result.errors is None
    assert result.data is not None
    assert _edge_names(json_at(result.data, "items")) == public_names


@pytest.mark.django_db
def test_connection_query_chain_shadow_hook_is_sealed() -> None:
    """A hook whose ``query.chain`` is instance-replaced FAILS CLOSED (Decision 2).

    ``sql.Query.clone`` shallow-copies the source ``Query.__dict__``, so an
    instance ``chain`` shadow would ride into the sealed query and dispatch on the
    connection's first post-seal transform (ordering / slicing), erasing the
    predicate. The structural no-shadow check rejects the query at the boundary, so
    the connection surface raises the typed error rather than serving widened rows.
    """
    services.seed_data(0)
    _seed_public_private_categories()

    def _shadowed_chain_hook(
        _cls: type[DjangoType],
        _qs: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        source = Category.objects.filter(is_private=False)
        unfiltered = Category.objects.all().query

        def _unfiltered_chain(*_args: object, **_kwargs: object) -> Query:
            return unfiltered

        source.query.chain = _unfiltered_chain  # instance shadow
        return source

    node_type = _make_sidecar_node_type(
        "ChainShadowConnNode",
        filterset=None,
        orderset=None,
        get_queryset=_shadowed_chain_hook,
    )
    schema = _field_schema(node_type)
    result = _post(schema, "{ items { edges { node { name } } } }")
    assert result.errors is not None
    assert "cannot be sealed" in json_str(result.errors[0], "message")


@pytest.mark.django_db
def test_connection_resolver_manager_degrading_to_list_fails_closed() -> None:
    """A consumer resolver returning a Manager that degrades to a list fails closed (sync)."""

    def resolver(_root: object, _info: object) -> models.Manager[Category]:
        return _degrading_manager()

    schema = _field_schema(
        _make_sidecar_node_type("MgrDegradeConnNode", filterset=None, orderset=None),
        resolver=resolver,
    )
    result = _post(schema, "{ items { edges { node { id } } } }")
    assert result.errors is not None
    assert any("must produce a QuerySet" in str(json_str(err, "message")) for err in result.errors)


@pytest.mark.django_db
def test_connection_resolver_manager_alias_drift_fails_closed() -> None:
    """A consumer resolver returning a Manager whose ``.all()`` drifts alias fails closed (sync)."""

    def resolver(_root: object, _info: object) -> models.Manager[Category]:
        return _alias_drift_manager()

    schema = _field_schema(
        _make_sidecar_node_type("MgrDriftConnNode", filterset=None, orderset=None),
        resolver=resolver,
    )
    result = _post(schema, "{ items { edges { node { id } } } }")
    assert result.errors is not None
    assert any(
        "preserve the manager's explicit routing" in str(json_str(err, "message"))
        for err in result.errors
    )


@pytest.mark.django_db(transaction=True)
async def test_connection_resolver_manager_degrading_to_list_fails_closed_async() -> None:
    """Sync/async parity: the Manager-degrade failure propagates on the async path too."""

    async def resolver(_root: object, _info: object) -> models.Manager[Category]:
        return _degrading_manager()

    schema = await sync_to_async(_field_schema)(
        _make_sidecar_node_type("AsyncMgrDegradeConnNode", filterset=None, orderset=None),
        resolver=resolver,
    )
    result = await _post_async(schema, "{ items { edges { node { id } } } }")
    assert result.errors is not None
    assert any("must produce a QuerySet" in str(json_str(err, "message")) for err in result.errors)


@pytest.mark.django_db
def test_a_root_connection_uses_only_the_definition_captured_at_construction() -> None:
    """The construction-time definition serves schema build and request alike.

    The generated connection class and its name, the ``totalCount`` shape, the
    published ``filter:`` / ``orderBy:`` arguments, the default seed, both
    visibility seals, the cursor vocabulary and the resolve-time total order all
    come from that one object. The target's definition attribute is replaced by
    a decoy over a DIFFERENT MODEL once the field is built, so a residual read
    would move the query to another table.
    """
    services.seed_data(3)
    node = _node_type("ColdCacheCountedNode", model=Category)
    decoy = _item_node_type("ColdCacheDecoyNode")
    finalize_django_types()
    clear_connection_type_cache()

    field = DjangoConnectionField(node)
    conn_type = _connection_type_cache[node].connection_type
    node.__django_strawberry_definition__ = decoy.__django_strawberry_definition__

    query_cls = strawberry.type(
        type(
            "ColdCacheQuery",
            (),
            {"__annotations__": {"rows": conn_type}, "rows": field},
        ),
    )
    schema = strawberry.Schema(query=query_cls, config=strawberry_config())

    result = _post(schema, "{ rows { edges { node { id name } } } }")
    assert result.errors is None, result.errors
    assert result.data is not None
    returned = _edge_names(json_at(result.data, "rows"))
    expected = list(Category.objects.order_by("pk").values_list("name", flat=True))
    assert returned == expected


@pytest.mark.django_db
def test_a_synthesized_relation_connection_is_built_from_the_registrys_definition() -> None:
    """Finalization resolves the target's definition once, from the registry.

    The synthesized field asks the registry rather than the target class - not
    for its connection class, not for its sidecar arguments, not for the model
    its pipeline seeds and seals against - so a target whose definition attribute
    is replaced after finalization has nothing to answer when the generated
    ``<field>Connection`` is built or resolved.
    """
    services.seed_data(3)

    class RelationParentNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")
            interfaces = (relay.Node,)
            name = "RelationParentNode"
            relation_shapes = {"items": "connection"}
            primary = True

    child = _node_type("RelationChildNode", model=Item)
    decoy = declare_django_type(
        "RelationChildDecoyNode",
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": Category,
                    "fields": ("id", "name"),
                    "interfaces": (relay.Node,),
                    "name": "RelationChildDecoyNode",
                    "primary": False,
                },
            ),
        },
    )

    finalize_django_types()
    child.__django_strawberry_definition__ = decoy.__django_strawberry_definition__

    parent_conn = _connection_type_for(
        RelationParentNode,
        RelationParentNode.__django_strawberry_definition__,
    )
    query_cls = strawberry.type(
        type(
            "RelationQuery",
            (),
            {
                "__annotations__": {"parents": parent_conn},
                "parents": DjangoConnectionField(RelationParentNode),
            },
        ),
    )
    schema = strawberry.Schema(query=query_cls, config=strawberry_config())
    result = _post(
        schema,
        """
                 {
                   parents {
                     edges {
                       node {
                         name
                         itemsConnection {
                           edges {
                             node {
                               name
                             }
                           }
                         }
                       }
                     }
                   }
                 }
                 """,
    )
    assert result.errors is None, result.errors
    assert result.data is not None
    nested = {
        name
        for parent in json_list(result.data, "parents", "edges")
        for name in _edge_names(json_at(parent, "node", "itemsConnection"))
    }
    assert nested == set(Item.objects.values_list("name", flat=True))


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("override", "message_start", "substrings"),
    [row[1:] for row in _CONNECTION_MALFORMED_FILTER_ROWS],
    ids=[row[0] for row in _CONNECTION_MALFORMED_FILTER_ROWS],
)
def test_connection_seals_a_malformed_filter_apply_sync_result(
    monkeypatch: pytest.MonkeyPatch,
    override: Callable[..., object],
    message_start: str,
    substrings: tuple[str, ...],
) -> None:
    """Each malformed ``FilterSet.apply_sync`` result is rejected by name at the connection.

    The filter arm runs the same post-sidecar seal as the ordering arm
    (``utils/querysets.py::apply_filterset_sync``), so every defect shape the
    seal names has to arrive here too.
    """
    services.seed_data(2)
    monkeypatch.setattr(_CategoryFilter, "apply_sync", classmethod(override))

    schema = _field_schema(_make_sidecar_node_type("SealedFilterNode"))
    result = _post(schema, _FILTERED_CONNECTION_QUERY)

    assert result.errors is not None
    assert result.data is None
    message = str(json_str(result.errors[0], "message"))
    assert message.startswith(message_start), message
    for substring in substrings:
        assert substring in message, message


@pytest.mark.django_db(transaction=True)
def test_connection_async_seal_rejects_a_non_awaitable_filter_apply_async(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``FilterSet.apply_async`` returning a plain value is rejected on the async path."""

    def _plain_apply_async(
        _cls: type[_CategoryFilter],
        _input_value: object,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        return queryset

    monkeypatch.setattr(_CategoryFilter, "apply_async", classmethod(_plain_apply_async))

    async def resolver(_root: object, _info: object) -> models.QuerySet[Category]:
        return Category.objects.all()

    schema = _field_schema(
        _make_sidecar_node_type("AsyncFilterSealNonAwaitableNode"),
        resolver=resolver,
    )
    result = asyncio.run(
        _post_async(schema, _FILTERED_CONNECTION_QUERY),
    )

    assert result.errors is not None
    assert str(json_str(result.errors[0], "message")).startswith(
        "_CategoryFilter.apply_async returned a non-awaitable value",
    )


@pytest.mark.django_db(transaction=True)
def test_connection_async_seal_rejects_a_sliced_filter_apply_async_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sliced ``FilterSet.apply_async`` result is rejected with the shared shape wording."""

    async def _sliced(
        _cls: type[_CategoryFilter],
        _input_value: object,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        return queryset.order_by("name")[:1]

    monkeypatch.setattr(_CategoryFilter, "apply_async", classmethod(_sliced))

    async def resolver(_root: object, _info: object) -> models.QuerySet[Category]:
        return Category.objects.all()

    schema = _field_schema(_make_sidecar_node_type("AsyncFilterSealSlicedNode"), resolver=resolver)
    result = asyncio.run(
        _post_async(schema, _FILTERED_CONNECTION_QUERY),
    )

    assert result.errors is not None
    assert str(json_str(result.errors[0], "message")).startswith(
        "_CategoryFilter.apply_async must return an unevaluated, unsliced "
        "QuerySet of Category rows; got sliced defect",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "descending"),
    [
        pytest.param("{ items { edges { node { name } } } }", False, id="bare"),
        pytest.param(_FILTERED_CONNECTION_QUERY, False, id="filtered"),
        pytest.param(
            "{ items(orderBy: [{name: DESC}]) { edges { node { name } } } }",
            True,
            id="ordered",
        ),
    ],
)
def test_connection_visibility_serves_a_combinator_hook_with_and_without_a_sidecar(
    query: str,
    *,
    descending: bool,
) -> None:
    """The combined hook's primary-key set can be filtered or sorted by the requested sidecar."""
    services.seed_data(2)
    node_type = _make_sidecar_node_type("CombinatorHookNode", get_queryset=_combined_get_queryset)
    schema = _field_schema(node_type)
    expected = _a_or_b_category_names()
    assert expected

    result = _post(schema, query)
    assert result.errors is None, (query, result.errors)
    assert result.data is not None
    names = _edge_names(json_at(result.data, "items"))
    assert sorted(names) == expected, query
    if descending:
        assert names == expected[::-1]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("set_class", "query"),
    [
        pytest.param(
            _CategoryOrder,
            "{ items(orderBy: [{name: ASC}]) { edges { node { name } } } }",
            id="order",
        ),
        pytest.param(_CategoryFilter, _FILTERED_CONNECTION_QUERY, id="filter"),
    ],
)
def test_connection_serves_a_combined_sidecar_result_as_its_primary_key_set(
    monkeypatch: pytest.MonkeyPatch,
    set_class: type[object],
    query: str,
) -> None:
    """A sidecar ``apply_sync`` returning a union is windowed as the rows it selects."""
    services.seed_data(2)

    def _a_or_b_union(
        _cls: type[object],
        _value: object,
        queryset: models.QuerySet[Category],
        _info: object,
    ) -> models.QuerySet[Category]:
        return (
            queryset.filter(name__startswith="a")
            .union(queryset.filter(name__startswith="b"))
            .order_by("name")
        )

    monkeypatch.setattr(set_class, "apply_sync", classmethod(_a_or_b_union))

    schema = _field_schema(_make_sidecar_node_type("CombinedSidecarNode"))
    result = _post(schema, query)

    assert result.errors is None, result.errors
    assert result.data is not None
    names = _edge_names(json_at(result.data, "items"))
    assert names == _a_or_b_category_names()


@pytest.mark.parametrize("orderset", [None, _CategoryOrder], ids=["neither", "orderset-only"])
def test_connection_field_omits_args_without_sidecars(orderset: type | None) -> None:
    """HTTP introspection publishes only declared sidecars beside the four Relay arguments."""
    schema = _field_schema(
        _make_sidecar_node_type(
            f"Sidecar{orderset is not None}Node",
            filterset=None,
            orderset=orderset,
        ),
    )
    result = _post(schema, '{ __type(name: "Query") { fields { name args { name } } } }')
    assert result.errors is None, result.errors
    fields = json_list(result.data, "__type", "fields")
    (field,) = fields
    assert json_str(field, "name") == "items"
    arguments = {json_str(argument, "name") for argument in json_list(field, "args")}
    expected = {
        "before",
        "after",
        "first",
        "last",
    }
    if orderset is not None:
        expected.add("orderBy")
    assert arguments == expected
