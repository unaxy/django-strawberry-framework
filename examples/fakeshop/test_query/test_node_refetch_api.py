"""Native HTTP Relay refetch contracts requiring consumer declarations.

The shipped library schema owns ordinary model-label refetch, mixed model batches,
hidden/missing holes, and default hook fetch modes. These holders add type-name
routing over two types for one model, shared-row consumer overrides, custom NodeID
columns, canonical key spellings, iterable override returns and deferred-column peer
loads. Every valid ordinary id is emitted over HTTP or minted with global_id_for;
alternate spellings and uncoercible literals are deliberate input probes.

The unconstrained decimal and datetime primary keys have no shipped equivalent.
Their function-local models use real temporary tables and native HTTP requests.
Both equal-value alternate spellings and different existing-type keys cross the
same public refetch fields.
"""

import contextlib
import datetime
from collections.abc import Generator, Iterable, Iterator, Mapping
from decimal import Decimal
from functools import wraps
from typing import TYPE_CHECKING

import django
import pytest
import strawberry
from apps.products import services
from apps.products.models import Category
from asgiref.sync import sync_to_async
from django.db import connection, models
from django.db.models import Model
from django.db.models.functions import Length
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django.utils.functional import SimpleLazyObject
from graphql_client import (
    JSONObject,
    graphql_payload,
    json_at,
    json_list,
    json_str,
    response_json,
)
from strategy_schemas import make_django_type
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoNodeField,
    DjangoNodesField,
    DjangoSchema,
    DjangoType,
    ErrorPolicy,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._idioms import FETCH_MODES, pickle_roundtrip, requires_fetch_modes, saved_pk

if TYPE_CHECKING:
    from typing import TypeAlias

    from django.db.models.expressions import Combinable

    _AwareStamp: TypeAlias = models.DateTimeField[
        str | datetime.datetime | datetime.date | Combinable,
        datetime.datetime,
    ]

pytestmark = pytest.mark.usefixtures("private_registry")

_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


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
    path("graphql-refetch/", _graphql_view),
    path("graphql-refetch-async/", _async_graphql_view),
]


def _post(
    schema: DjangoSchema,
    query: str,
    *,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(query, variables=variables, url="/graphql-refetch/")
    finally:
        _CURRENT["schema"] = None


async def _post_async(
    schema: DjangoSchema,
    query: str,
    *,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            result = await AsyncTestClient().query(
                query,
                variables=variables,
                assert_no_errors=False,
                url="/graphql-refetch-async/",
            )
        assert result.response.status_code == 200
        return response_json(result.response)
    finally:
        _CURRENT["schema"] = None


def _category_type(name: str, **meta_extra: object) -> type[DjangoType]:
    return make_django_type(name, Category, ("id", "name"), meta_extra=meta_extra)


def _schema_with(
    field_name: str,
    annotation: object,
    field_value: object,
    *,
    extra_types: Iterable[type] = (),
    expose_errors: bool = False,
) -> DjangoSchema:
    query = strawberry.type(
        type("Query", (), {"__annotations__": {field_name: annotation}, field_name: field_value}),
    )
    finalize_django_types()
    return DjangoSchema(
        query=query,
        config=strawberry_config(),
        types=list(extra_types),
        error_policy=ErrorPolicy(enabled=False) if expose_errors else None,
    )


def _multi_type_schema(row: Category, *, lazy_override: bool | None = None) -> DjangoSchema:
    primary_type = _category_type("PrimaryNode", primary=True, globalid_strategy="type")
    namespace: dict[str, object] = {}
    if lazy_override is not None:

        def _resolve_node(
            _cls: type[DjangoType],
            node_id: str,
            *,
            info: strawberry.Info[object, object],
            required: bool = False,
        ) -> Category | SimpleLazyObject[Category]:
            del node_id, info, required
            return SimpleLazyObject(lambda: row) if lazy_override else row

        namespace["resolve_node"] = classmethod(_resolve_node)
    secondary_type = make_django_type(
        "SecondaryNode",
        Category,
        ("id", "name"),
        meta_extra={"globalid_strategy": "type"},
        namespace_extra=namespace,
    )

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        nodes: list[relay.Node | None] = DjangoNodesField()
        primary: Category = strawberry.field(graphql_type=primary_type, resolver=lambda: row)
        secondary: Category = strawberry.field(graphql_type=secondary_type, resolver=lambda: row)

    finalize_django_types()
    return DjangoSchema(
        query=Query,
        config=strawberry_config(),
        types=[primary_type, secondary_type],
    )


_EMIT_TYPES = "{ primary { id name __typename } secondary { id name __typename } }"


def _emitted_type_ids(schema: DjangoSchema, row: Category) -> tuple[str, str]:
    emitted = _post(schema, _EMIT_TYPES)
    primary_id = json_str(emitted, "data", "primary", "id")
    secondary_id = json_str(emitted, "data", "secondary", "id")
    assert emitted == {
        "data": {
            "primary": {"id": primary_id, "name": row.name, "__typename": "PrimaryNode"},
            "secondary": {"id": secondary_id, "name": row.name, "__typename": "SecondaryNode"},
        },
    }
    assert primary_id != secondary_id
    return primary_id, secondary_id


@pytest.mark.django_db
@pytest.mark.parametrize("root", ["primary", "secondary"])
def test_type_name_ids_refetch_as_the_concrete_type_that_emitted_them(root: str) -> None:
    """Two types for one model round-trip their distinct emitted type-name IDs."""
    services.seed_data(1)
    row = Category.objects.order_by("pk").first()
    assert row is not None
    schema = _multi_type_schema(row)
    primary_id, secondary_id = _emitted_type_ids(schema, row)
    expected_type = "PrimaryNode" if root == "primary" else "SecondaryNode"
    expected_id = primary_id if root == "primary" else secondary_id
    payload = _post(
        schema,
        """
        query ($id: ID!) {
          node(id: $id) {
            id
            __typename
            ... on PrimaryNode { name }
            ... on SecondaryNode { name }
          }
        }
        """,
        variables={"id": expected_id},
    )
    assert payload == {
        "data": {"node": {"id": expected_id, "__typename": expected_type, "name": row.name}},
    }


@pytest.mark.django_db
def test_a_batch_preserves_each_emitting_type_for_the_same_model_row() -> None:
    """A repeated model key remains secondary/primary/secondary in input order."""
    services.seed_data(1)
    row = Category.objects.order_by("pk").first()
    assert row is not None
    schema = _multi_type_schema(row)
    primary_id, secondary_id = _emitted_type_ids(schema, row)
    payload = _post(
        schema,
        """
        query ($ids: [ID!]!) {
          nodes(ids: $ids) {
            id
            __typename
            ... on PrimaryNode { name }
            ... on SecondaryNode { name }
          }
        }
        """,
        variables={"ids": [secondary_id, primary_id, secondary_id]},
    )
    assert payload == {
        "data": {
            "nodes": [
                {"id": secondary_id, "__typename": "SecondaryNode", "name": row.name},
                {"id": primary_id, "__typename": "PrimaryNode", "name": row.name},
                {"id": secondary_id, "__typename": "SecondaryNode", "name": row.name},
            ],
        },
    }


@pytest.mark.django_db
@pytest.mark.parametrize("lazy", [False, True], ids=["shared-row", "lazy-proxy"])
def test_refetch_type_hints_leave_a_shared_primary_row_dispatchable(*, lazy: bool) -> None:
    """Secondary refetch followed by the primary field succeeds for a shared row or its proxy."""
    services.seed_data(1)
    row = Category.objects.order_by("pk").first()
    assert row is not None
    schema = _multi_type_schema(row, lazy_override=lazy)
    _primary_id, secondary_id = _emitted_type_ids(schema, row)
    payload = _post(
        schema,
        "query ($id: ID!) { node(id: $id) { __typename } primary { name __typename } }",
        variables={"id": secondary_id},
    )
    assert payload == {
        "data": {
            "node": {"__typename": "SecondaryNode"},
            "primary": {"name": row.name, "__typename": "PrimaryNode"},
        },
    }


@pytest.mark.django_db
def test_a_custom_string_node_id_round_trips_the_emitted_id_field() -> None:
    """The custom nonnumeric name slot is emitted and refetched as the identical ID."""
    services.seed_data(1)
    row = Category.objects.order_by("pk").first()
    assert row is not None

    class CategoryNode(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        category: Category = strawberry.field(graphql_type=CategoryNode, resolver=lambda: row)

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config(), types=[CategoryNode])
    emitted = _post(schema, "{ category { id __typename } }")
    gid = json_str(emitted, "data", "category", "id")
    assert emitted == {
        "data": {
            "category": {
                "id": global_id_for(CategoryNode, row.name),
                "__typename": "CategoryNode",
            },
        },
    }
    payload = _post(
        schema,
        "query ($id: ID!) { node(id: $id) { id __typename } }",
        variables={"id": gid},
    )
    assert payload == {"data": {"node": {"id": gid, "__typename": "CategoryNode"}}}


@pytest.mark.django_db
@pytest.mark.parametrize("literal", ["emitted", "uncoercible"])
def test_a_datetime_node_id_resolves_only_a_coercible_literal(literal: str) -> None:
    """The actual datetime NodeID accepts its emitted value and rejects invalid text before SQL."""
    services.seed_data(1)
    row = Category.objects.order_by("pk").first()
    assert row is not None

    class CategoryNode(DjangoType):
        created_date: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        category: Category = strawberry.field(graphql_type=CategoryNode, resolver=lambda: row)

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config(), types=[CategoryNode])
    emitted = _post(schema, "{ category { id } }")
    assert "errors" not in emitted, emitted
    gid = json_str(emitted, "data", "category", "id")
    if literal == "uncoercible":
        gid = global_id_for(CategoryNode, "not-a-datetime")
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            schema,
            "query ($id: ID!) { node(id: $id) { __typename } }",
            variables={"id": gid},
        )
    node: JSONObject | None = {"__typename": "CategoryNode"} if literal == "emitted" else None
    assert payload == {"data": {"node": node}}
    category_reads = [
        entry["sql"]
        for entry in captured.captured_queries
        if 'FROM "products_category"' in entry["sql"]
    ]
    assert len(category_reads) == (1 if literal == "emitted" else 0), category_reads


@pytest.mark.django_db
def test_consumer_resolvers_receive_decoded_strings_and_serve_each_position() -> None:
    """Single and batch consumer overrides receive strings and return the selected row per position."""
    services.seed_data(1)
    row = Category.objects.order_by("pk").first()
    assert row is not None
    received: list[str | list[str]] = []

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def resolve_node(
            cls,
            node_id: str,
            *,
            info: strawberry.Info[object, object],
            required: bool = False,
        ) -> Category | None:
            del cls, info, required
            received.append(node_id)
            return None if node_id.startswith("legacy-") else row

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info: strawberry.Info[object, object],
            node_ids: Iterable[str],
            required: bool = False,
        ) -> list[Category]:
            del cls, info, required
            ids = list(node_ids)
            received.append(ids)
            return [row for _ in ids]

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        nodes: list[relay.Node | None] = DjangoNodesField()

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config(), types=[CategoryNode])
    gid = global_id_for(CategoryNode, saved_pk(row))
    payload = _post(
        schema,
        """
        query ($id: ID!) {
          node(id: $id) { ... on CategoryNode { name } }
          nodes(ids: [$id, $id]) { ... on CategoryNode { name } }
        }
        """,
        variables={"id": gid},
    )
    assert payload == {
        "data": {"node": {"name": row.name}, "nodes": [{"name": row.name}, {"name": row.name}]},
    }
    assert received == [str(saved_pk(row)), [str(saved_pk(row)), str(saved_pk(row))]]


@pytest.mark.django_db
def test_default_refetch_resolves_a_padded_integer_key_by_value() -> None:
    """Single and batch defaults find the same row when the integer ID has a leading zero."""
    services.seed_data(1)
    category_type = _category_type("CategoryNode")

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        nodes: list[relay.Node | None] = DjangoNodesField()

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config(), types=[category_type])
    row = Category.objects.order_by("pk").first()
    assert row is not None
    padded = global_id_for(category_type, f"0{saved_pk(row)}")
    payload = _post(
        schema,
        """
        query ($id: ID!) {
          node(id: $id) { ... on CategoryNode { name } }
          nodes(ids: [$id]) { ... on CategoryNode { name } }
        }
        """,
        variables={"id": padded},
    )
    assert payload == {"data": {"node": {"name": row.name}, "nodes": [{"name": row.name}]}}


def _spelled_model(kind: str) -> type[Model]:
    if kind == "decimal":

        class RefetchDecimalRow(Model):
            code: "models.DecimalField[str | float | Decimal | Combinable, Decimal]" = (
                models.DecimalField(primary_key=True, max_digits=None, decimal_places=None)
            )
            name: "models.TextField[str | Combinable, str]" = models.TextField()

            class Meta:
                app_label = "products"
                managed = False
                db_table = "refetch_decimal_row"

            @override
            def __str__(self) -> str:
                return self.name

        return RefetchDecimalRow

    class RefetchStampRow(Model):
        stamp: "_AwareStamp" = models.DateTimeField(
            primary_key=True,
        )
        name: "models.TextField[str | Combinable, str]" = models.TextField()

        class Meta:
            app_label = "products"
            managed = False
            db_table = "refetch_stamp_row"

        @override
        def __str__(self) -> str:
            return self.name

    return RefetchStampRow


@contextlib.contextmanager
def _key_table(model: type[Model], key: object) -> Generator[None, None, None]:
    with connection.schema_editor() as editor:
        editor.create_model(model)
    try:
        _ = model._default_manager.create(pk=key, name="stored")
        yield
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(model)


def _spelled_answer(model: type[Model], spelled: str, root: str) -> JSONObject:
    node_type = make_django_type("SpelledNode", model, ("name",))

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        nodes: list[relay.Node | None] = DjangoNodesField()

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config(), types=[node_type])
    selection = "node(id: $id)" if root == "node" else "nodes(ids: [$id])"
    return _post(
        schema,
        f"query ($id: ID!) {{ {selection} {{ ... on SpelledNode {{ name }} }} }}",
        variables={"id": global_id_for(node_type, spelled)},
    )


@pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="PostgreSQL numeric preserves written scale",
)
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("required", [False, True], ids=["optional", "required"])
def test_refetch_matches_a_decimal_row_stored_at_another_scale(*, required: bool) -> None:
    """Numeric rows stored as 1.50 fill optional and required batch slots requested as 1.5."""
    model = _spelled_model("decimal")
    with _key_table(model, Decimal("1.50")):
        stored_key = read_attr(model._default_manager.get(), "pk")
        assert isinstance(stored_key, Decimal)
        assert stored_key.as_tuple().exponent == -2
        node_type = make_django_type("StoredScaleNode", model, ("name",))
        nodes_annotation = list[relay.Node] if required else list[relay.Node | None]
        schema = _schema_with(
            "nodes",
            nodes_annotation,
            DjangoNodesField(),
            extra_types=[node_type],
        )
        payload = _post(
            schema,
            "query ($id: ID!) { nodes(ids: [$id]) { ... on StoredScaleNode { name } } }",
            variables={"id": global_id_for(node_type, "1.5", schema=schema)},
        )
    assert payload == {"data": {"nodes": [{"name": "stored"}]}}, payload


@pytest.mark.skipif(connection.vendor != "sqlite", reason="SQLite stores the value it is bound")
@pytest.mark.skipif(
    django.VERSION < (6, 1),
    reason="Django below 6.1 cannot read an unconstrained DecimalField",
)
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("stored", "spelled"),
    [
        pytest.param(Decimal("2.5"), "2.50", id="trailing-zero"),
        pytest.param(Decimal(7), "7.0", id="one-fractional-zero"),
        pytest.param(Decimal(7), "7.00", id="two-fractional-zeros"),
        pytest.param(Decimal(70), "7E+1", id="exponent"),
        pytest.param(Decimal(0), "0.00", id="zero"),
    ],
)
@pytest.mark.parametrize("root", ["node", "nodes"])
def test_refetch_matches_an_alternate_decimal_primary_key_spelling(
    stored: Decimal,
    spelled: str,
    root: str,
) -> None:
    """A scalar decimal key is matched by numeric value, including scale and exponent spellings."""
    model = _spelled_model("decimal")
    with _key_table(model, stored):
        payload = _spelled_answer(model, spelled, root)
    expected: object = {"name": "stored"} if root == "node" else [{"name": "stored"}]
    assert payload == {"data": {root: expected}}


@pytest.mark.skipif(connection.vendor != "sqlite", reason="SQLite stores the value it is bound")
@pytest.mark.skipif(
    django.VERSION < (6, 1),
    reason="Django below 6.1 cannot read an unconstrained DecimalField",
)
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("root", ["node", "nodes"])
def test_refetch_does_not_substitute_a_row_for_a_different_decimal_key(root: str) -> None:
    """A valid decimal key with a different numeric value remains a null, never the stored row."""
    model = _spelled_model("decimal")
    with _key_table(model, Decimal(7)):
        payload = _spelled_answer(model, "8.00", root)
    assert payload == {"data": {root: None if root == "node" else [None]}}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("root", ["node", "nodes"])
def test_refetch_matches_a_datetime_primary_key_at_another_offset(root: str) -> None:
    """An aware key written at UTC is refetched by the same instant at another offset."""
    model = _spelled_model("datetime")
    with _key_table(model, datetime.datetime(2024, 1, 1, 8, tzinfo=datetime.timezone.utc)):
        payload = _spelled_answer(model, "2024-01-01T10:00:00+02:00", root)
    expected: object = {"name": "stored"} if root == "node" else [{"name": "stored"}]
    assert payload == {"data": {root: expected}}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("root", ["node", "nodes"])
def test_refetch_does_not_substitute_a_row_for_a_different_datetime_key(root: str) -> None:
    """A valid datetime key for another instant remains a null, never the stored row."""
    model = _spelled_model("datetime")
    with _key_table(model, datetime.datetime(2024, 1, 1, 8, tzinfo=datetime.timezone.utc)):
        payload = _spelled_answer(model, "2024-01-01T11:00:00+02:00", root)
    assert payload == {"data": {root: None if root == "node" else [None]}}


class _KeyPrefixedOneToOneField(models.OneToOneField["Category", "Category"]):
    """A consumer one-to-one key whose ``to_python`` also reads the ``key:<pk>`` spelling."""

    @override
    def to_python(self, value: object) -> object:
        if isinstance(value, str):
            value = value.removeprefix("key:")
        return object_result(super().to_python, value)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("root", ["node", "nodes"])
def test_refetch_casts_an_emitted_id_through_a_custom_key_fields_to_python(root: str) -> None:
    """A one-to-one primary key's own ``to_python`` decodes the ``key:<pk>`` id its type emitted.

    The id slot is coerced through the declared key field (spec-032 Decision 5), whose
    ``to_python`` a consumer subclass overrides, never through the column the key references,
    which reads ``key:<pk>`` as no integer.
    """
    services.seed_data(1)
    category = Category.objects.order_by("pk").first()
    assert category is not None

    class RefetchKeyedRow(Model):
        category: "_KeyPrefixedOneToOneField" = _KeyPrefixedOneToOneField(
            Category,
            on_delete=models.CASCADE,
            primary_key=True,
        )
        name: "models.TextField[str | Combinable, str]" = models.TextField()

        class Meta:
            app_label = "products"
            managed = False
            db_table = "refetch_keyed_row"

        @override
        def __str__(self) -> str:
            return self.name

    class KeyedNode(DjangoType):
        class Meta:
            model = RefetchKeyedRow
            fields = ("name",)
            interfaces = (relay.Node,)

        @classmethod
        def resolve_id(cls, root: RefetchKeyedRow, *, info: object) -> str:
            del cls, info
            return f"key:{saved_pk(root)}"

    with connection.schema_editor() as editor:
        editor.create_model(RefetchKeyedRow)
    try:
        row = RefetchKeyedRow.objects.create(category=category, name="stored")

        @strawberry.type
        class Query:
            node: relay.Node | None = DjangoNodeField()
            nodes: list[relay.Node | None] = DjangoNodesField()
            keyed: RefetchKeyedRow = strawberry.field(graphql_type=KeyedNode, resolver=lambda: row)

        finalize_django_types()
        schema = DjangoSchema(query=Query, config=strawberry_config(), types=[KeyedNode])
        emitted = _post(schema, "{ keyed { id } }")
        gid = json_str(emitted, "data", "keyed", "id")
        assert gid == global_id_for(KeyedNode, f"key:{saved_pk(category)}")
        selection = "node(id: $id)" if root == "node" else "nodes(ids: [$id])"
        payload = _post(
            schema,
            f"query ($id: ID!) {{ {selection} {{ ... on KeyedNode {{ name }} }} }}",
            variables={"id": gid},
        )
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(RefetchKeyedRow)
    expected: object = {"name": "stored"} if root == "node" else [{"name": "stored"}]
    assert payload == {"data": {root: expected}}


class _KeyPrefixedModelKeyField(models.OneToOneField[Model, Model]):
    """A consumer one-to-one key, to any column, whose ``to_python`` also reads ``key:<value>``."""

    @override
    def to_python(self, value: object) -> object:
        if isinstance(value, str):
            value = value.removeprefix("key:")
        return object_result(super().to_python, value)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("root", ["node", "nodes"])
def test_refetch_casts_through_a_custom_key_to_a_generated_column_and_then_the_column(
    root: str,
) -> None:
    """A key subclass whose ``to_field`` is a unique generated column keeps its own cast.

    The key's ``to_python`` reads the ``key:<value>`` id its type emitted, and the integer
    column the generated field computes casts the rest: ``key:3`` refetches the row whose
    source is three characters long, and ``key:<2**70>``, past the column's range, names
    no row. Neither cast replaces the other.
    """

    class RefetchGeneratedTarget(Model):
        source: "models.TextField[str | Combinable, str]" = models.TextField()
        # Unannotated: django-stubs declares ``GeneratedField`` without type parameters.
        size = models.GeneratedField(
            expression=Length("source"),
            output_field=models.BigIntegerField(),
            db_persist=True,
            unique=True,
        )

        class Meta:
            app_label = "products"
            managed = False
            db_table = "refetch_generated_target"

        @override
        def __str__(self) -> str:
            return self.source

    class RefetchGeneratedKeyedRow(Model):
        target: "_KeyPrefixedModelKeyField" = _KeyPrefixedModelKeyField(
            RefetchGeneratedTarget,
            on_delete=models.CASCADE,
            primary_key=True,
            to_field="size",
        )
        name: "models.TextField[str | Combinable, str]" = models.TextField()

        class Meta:
            app_label = "products"
            managed = False
            db_table = "refetch_generated_keyed_row"

        @override
        def __str__(self) -> str:
            return self.name

    class GeneratedKeyedNode(DjangoType):
        class Meta:
            model = RefetchGeneratedKeyedRow
            fields = ("name",)
            interfaces = (relay.Node,)

        @classmethod
        def resolve_id(cls, root: RefetchGeneratedKeyedRow, *, info: object) -> str:
            del cls, info
            return f"key:{read_attr(root, 'pk')}"

    with connection.schema_editor() as editor:
        editor.create_model(RefetchGeneratedTarget)
        editor.create_model(RefetchGeneratedKeyedRow)
    try:
        target = RefetchGeneratedTarget.objects.create(source="abc")
        target.refresh_from_db()
        row = RefetchGeneratedKeyedRow.objects.create(target=target, name="stored")

        @strawberry.type
        class Query:
            node: relay.Node | None = DjangoNodeField()
            nodes: list[relay.Node | None] = DjangoNodesField()
            keyed: RefetchGeneratedKeyedRow = strawberry.field(
                graphql_type=GeneratedKeyedNode,
                resolver=lambda: row,
            )

        finalize_django_types()
        schema = DjangoSchema(query=Query, config=strawberry_config(), types=[GeneratedKeyedNode])
        emitted = _post(schema, "{ keyed { id } }")
        gid = json_str(emitted, "data", "keyed", "id")
        assert gid == global_id_for(GeneratedKeyedNode, "key:3")
        selection = "node(id: $id)" if root == "node" else "nodes(ids: [$id])"
        query = f"query ($id: ID!) {{ {selection} {{ ... on GeneratedKeyedNode {{ name }} }} }}"
        payload = _post(schema, query, variables={"id": gid})
        past_range = _post(
            schema,
            query,
            variables={"id": global_id_for(GeneratedKeyedNode, f"key:{2**70}")},
        )
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(RefetchGeneratedKeyedRow)
            editor.delete_model(RefetchGeneratedTarget)
    expected: object = {"name": "stored"} if root == "node" else [{"name": "stored"}]
    assert payload == {"data": {root: expected}}
    assert past_range == {"data": {root: None if root == "node" else [None]}}


def _upstream_node_schema() -> tuple[DjangoSchema, type[DjangoType]]:
    category_type = _category_type("CategoryNode", globalid_strategy="type")

    @strawberry.type
    class Query:
        node: relay.Node | None = relay.node()
        nodes: list[relay.Node | None] = relay.node()

    finalize_django_types()
    return DjangoSchema(
        query=Query,
        config=strawberry_config(),
        types=[category_type],
    ), category_type


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("executor", ["sync", "async"])
async def test_default_resolvers_under_upstream_fields_keep_uncoercible_id_holes(
    executor: str,
) -> None:
    """Strawberry's own root fields hand raw IDs to both framework defaults, sync and async."""
    await sync_to_async(services.seed_data)(1)
    schema, node_type = _upstream_node_schema()
    row = await Category.objects.order_by("pk").afirst()
    assert row is not None
    variables = {
        "bad": global_id_for(node_type, "abc", schema=schema),
        "good": global_id_for(node_type, saved_pk(row), schema=schema),
    }
    query = """
    query ($bad: ID!, $good: ID!) {
      node(id: $bad) { __typename }
      nodes(ids: [$bad, $good]) { ... on CategoryNode { name } }
    }
    """
    payload = (
        await sync_to_async(_post)(schema, query, variables=variables)
        if executor == "sync"
        else await _post_async(schema, query, variables=variables)
    )
    assert payload == {"data": {"node": None, "nodes": [None, {"name": row.name}]}}


@pytest.mark.django_db(transaction=True)
async def test_async_refetch_accepts_a_synchronous_consumer_batch_override() -> None:
    """The async HTTP gatherer accepts a sync list, preserving duplicate positions and missing holes."""
    await sync_to_async(services.seed_data)(2)
    rows = {str(saved_pk(row)): row async for row in Category.objects.order_by("pk")[:2]}
    assert len(rows) == 2

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info: strawberry.Info[object, object],
            node_ids: Iterable[str],
            required: bool = False,
        ) -> list[Category | None]:
            del cls, info, required
            return [rows.get(node_id) for node_id in node_ids]

    schema = _schema_with(
        "nodes",
        list[relay.Node | None],
        DjangoNodesField(),
        extra_types=[CategoryNode],
    )
    first, second = list(rows.values())
    missing = max(saved_pk(first), saved_pk(second)) + 1000
    gids = [
        global_id_for(CategoryNode, key)
        for key in [
            saved_pk(second),
            saved_pk(first),
            saved_pk(second),
            missing,
        ]
    ]
    payload = await _post_async(
        schema,
        "query ($ids: [ID!]!) { nodes(ids: $ids) { __typename ... on CategoryNode { name } } }",
        variables={"ids": gids},
    )
    assert payload == {
        "data": {
            "nodes": [
                {"__typename": "CategoryNode", "name": second.name},
                {"__typename": "CategoryNode", "name": first.name},
                {"__typename": "CategoryNode", "name": second.name},
                None,
            ],
        },
    }


@pytest.mark.django_db
def test_a_wrong_length_consumer_batch_has_one_named_configuration_error() -> None:
    """A consumer returning no rows for two IDs gets the named cardinality error at its field."""
    services.seed_data(2)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info: strawberry.Info[object, object],
            node_ids: Iterable[str],
            required: bool = False,
        ) -> list[Category]:
            del cls, info, node_ids, required
            return []

    schema = _schema_with(
        "categories",
        list[CategoryNode | None],
        DjangoNodesField(CategoryNode),
        expose_errors=True,
    )
    rows = list(Category.objects.order_by("pk")[:2])
    payload = _post(
        schema,
        "query ($ids: [ID!]!) { categories(ids: $ids) { name } }",
        variables={"ids": [global_id_for(CategoryNode, saved_pk(row)) for row in rows]},
    )
    assert payload["data"] is None, payload
    assert len(json_list(payload, "errors")) == 1
    assert json_at(payload, "errors", 0, "path") == ["categories"]
    assert json_str(payload, "errors", 0, "message") == (
        "CategoryNode.resolve_nodes returned 0 row(s) for 2 requested id(s); "
        "a resolve_nodes override must return a list input-ordered and 1:1 with node_ids "
        "(None for missing) - the _resolve_nodes_default / _order_nodes shape."
    )


@pytest.mark.django_db
def test_a_consumer_batch_generator_preserves_reverse_order_and_duplicates() -> None:
    """An ordered generator is materialized and keeps all requested positions."""
    services.seed_data(2)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info: strawberry.Info[object, object],
            node_ids: Iterable[str],
            required: bool = False,
        ) -> Iterator[Category | None]:
            del cls, info, required
            ids = list(node_ids)
            rows = {str(saved_pk(row)): row for row in Category.objects.filter(pk__in=ids)}
            return (rows.get(node_id) for node_id in ids)

    schema = _schema_with("categories", list[CategoryNode | None], DjangoNodesField(CategoryNode))
    first, second = Category.objects.order_by("pk")[:2]
    payload = _post(
        schema,
        "query ($ids: [ID!]!) { categories(ids: $ids) { name } }",
        variables={
            "ids": [global_id_for(CategoryNode, saved_pk(row)) for row in [second, first, second]],
        },
    )
    assert payload == {
        "data": {
            "categories": [{"name": second.name}, {"name": first.name}, {"name": second.name}],
        },
    }


@requires_fetch_modes
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("mode_name", "source", "name_statements"),
    [
        pytest.param("FETCH_PEERS", "queryset", 1, id="queryset-rows"),
        pytest.param("project", "queryset", 1, id="project-mode-rows"),
        pytest.param("FETCH_PEERS", "unpickled", 3, id="unpickled-rows"),
    ],
)
def test_consumer_override_rows_keep_their_deferred_column_fetch_mode(
    mode_name: str,
    source: str,
    name_statements: int,
) -> None:
    """Stamping preserves peer batches for deferred names and the no-peers pickle fallback."""
    services.seed_data(3)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info: strawberry.Info[object, object],
            node_ids: Iterable[str],
            required: bool = False,
        ) -> list[Category | None]:
            del cls, info, required
            ids = list(node_ids)
            queryset = (
                Category.objects.filter(pk__in=ids).only("id").fetch_mode(FETCH_MODES[mode_name])
            )
            loaded = list(queryset)
            if source == "unpickled":
                loaded = pickle_roundtrip(loaded)
            rows = {str(saved_pk(row)): row for row in loaded}
            return [rows.get(node_id) for node_id in ids]

    schema = _schema_with("categories", list[CategoryNode | None], DjangoNodesField(CategoryNode))
    rows = list(Category.objects.order_by("pk")[:3])
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            schema,
            "query ($ids: [ID!]!) { categories(ids: $ids) { name } }",
            variables={"ids": [global_id_for(CategoryNode, saved_pk(row)) for row in rows]},
        )
    assert payload == {"data": {"categories": [{"name": row.name} for row in rows]}}
    category_sql = [
        entry["sql"]
        for entry in captured.captured_queries
        if 'FROM "products_category"' in entry["sql"]
    ]
    name_sql = [sql for sql in category_sql if '"name"' in sql.split(" FROM ", 1)[0]]
    assert len(category_sql) == 1 + name_statements, category_sql
    assert len(name_sql) == name_statements, name_sql
