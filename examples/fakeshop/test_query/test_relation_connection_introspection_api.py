"""Live HTTP introspection tests for consumer relation shapes and target-owned connection fields."""

from functools import wraps

import pytest
import strawberry
from apps.library.models import Book, Genre
from apps.products.models import Category, Item, Property
from apps.products.services import seed_data
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_list, json_str
from strawberry import relay

from django_strawberry_framework import (
    DjangoListField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-relation-introspection/", _graphql_view)]


def _schema(root_type: type[DjangoType]) -> DjangoSchema:
    """Mount a consumer root that publishes the relation types for introspection."""
    finalize_django_types()
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objects": list[root_type]},
                "objects": DjangoListField(root_type),
            },
        ),
    )
    return DjangoSchema(query=query)


def _post(schema: DjangoSchema, document: str) -> JSONObject:
    """Inspect the native view's complete successful HTTP envelope and restore the mount."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload(document, url="/graphql-relation-introspection/")
        assert set(payload) == {"data"}, payload
        return payload
    finally:
        _CURRENT["schema"] = None


def _fields(payload: JSONObject, alias: str) -> dict[str, list[str]]:
    """Normalize introspection field/argument order without discarding any published field."""
    return {
        json_str(field, "name"): sorted(
            json_str(argument, "name") for argument in json_list(field, "args")
        )
        for field in json_list(payload, "data", alias, "fields")
    }


def test_default_m2m_relations_publish_only_connections() -> None:
    """Both M2M directions publish a connection and omit their list without a shape opt-in."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "genres")
            interfaces = (relay.Node,)

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name", "books")
            interfaces = (relay.Node,)

    assert registry.get(Book) is BookType
    schema = _schema(GenreType)
    payload = _post(
        schema,
        """
        {
          book: __type(name: "BookType") { fields { name args { name } } }
          genre: __type(name: "GenreType") { fields { name args { name } } }
        }
    """,
    )
    assert _fields(payload, "book") == {
        "id": [],
        "title": [],
        "genresConnection": [
            "after",
            "before",
            "first",
            "last",
        ],
    }
    assert _fields(payload, "genre") == {
        "id": [],
        "name": [],
        "booksConnection": [
            "after",
            "before",
            "first",
            "last",
        ],
    }


@pytest.mark.django_db
def test_list_relation_shape_omits_the_connection() -> None:
    """An explicit list-only relation publishes the list and no generated connection sibling."""
    seed_data(0)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")
            interfaces = (relay.Node,)
            relation_shapes = {"items": "list"}

    assert registry.get(Item) is ItemType
    payload = _post(
        _schema(CategoryType),
        """
        { category: __type(name: "CategoryType") { fields { name args { name } } } }
    """,
    )
    assert _fields(payload, "category") == {"id": [], "name": [], "items": []}


@pytest.mark.django_db
def test_consumer_relation_annotation_keeps_only_its_authored_list() -> None:
    """A consumer list annotation owns its relation shape even when the target is a Relay node."""
    seed_data(0)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class CategoryType(DjangoType):
        items: list[ItemType]

        class Meta:
            model = Category
            fields = ("id", "name", "items")
            interfaces = (relay.Node,)

    payload = _post(
        _schema(CategoryType),
        """
        { category: __type(name: "CategoryType") { fields { name args { name } } } }
    """,
    )
    assert _fields(payload, "category") == {"id": [], "name": [], "items": []}


@pytest.mark.django_db
def test_nested_connection_arguments_and_count_follow_each_target() -> None:
    """A configured target publishes sidecars and count while its bare sibling publishes neither."""
    seed_data(0)

    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"name": ["exact"]}

    class ItemOrder(OrderSet):
        class Meta:
            model = Item
            fields = ["name"]

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = ItemFilter
            orderset_class = ItemOrder
            connection = {"total_count": True}

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = (
                "id",
                "name",
                "items",
                "properties",
            )
            interfaces = (relay.Node,)

    assert registry.get(Item) is ItemType
    assert registry.get(Property) is PropertyType
    payload = _post(
        _schema(CategoryType),
        """
        {
          category: __type(name: "CategoryType") { fields { name args { name } } }
          items: __type(name: "ItemTypeConnection") { fields { name args { name } } }
          properties: __type(name: "PropertyTypeConnection") { fields { name args { name } } }
        }
    """,
    )
    assert _fields(payload, "category") == {
        "id": [],
        "name": [],
        "itemsConnection": [
            "after",
            "before",
            "filter",
            "first",
            "last",
            "orderBy",
        ],
        "propertiesConnection": [
            "after",
            "before",
            "first",
            "last",
        ],
    }
    assert _fields(payload, "items") == {"edges": [], "pageInfo": [], "totalCount": []}
    assert _fields(payload, "properties") == {"edges": [], "pageInfo": []}
