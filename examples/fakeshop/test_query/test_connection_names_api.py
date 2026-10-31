"""Live connection selection names and row-fetch elision under schema name conversion.

A holder is required for this consumer configuration: one library declaration is served under
both the default converter and a converter renaming every Relay selection and its page-size
argument. Offset and keyset variants share the same real Genre rows and native package mounts.
"""

import asyncio
import operator
from collections.abc import AsyncIterator, Iterable
from functools import wraps
from typing import ClassVar

import pytest
import strawberry
from apps.library import models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    json_list,
    json_object,
    post_graphql,
    response_json,
)
from strawberry import relay
from strawberry.schema.name_converter import HasGraphQLName, NameConverter
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView


class _RelayNameConverter(NameConverter):
    """Publish consumer-selected wire names for all Relay page inputs and outputs."""

    _NAMES: ClassVar[dict[str, str]] = {
        "edges": "rows",
        "node": "entry",
        "pageInfo": "window",
        "totalCount": "size",
        "first": "take",
    }

    @override
    def get_graphql_name(self, obj: HasGraphQLName) -> str:
        published = super().get_graphql_name(obj)
        return self._NAMES.get(published, published)


_CURRENT: dict[str, strawberry.Schema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _sync_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-names/", _sync_view), path("graphql-names-async/", _async_view)]


def _schema(*, keyset: bool, renamed: bool) -> DjangoSchema:
    """Rung 3: two mutually exclusive cursor declarations under alternate consumer converters."""

    class NamedGenreType(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("id", "name")
            interfaces = (relay.Node,)
            connection = {"total_count": True}
            cursor_field = ("name", "id") if keyset else None

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.Genre],
            info: strawberry.Info,
        ) -> QuerySet[models.Genre]:
            return queryset.order_by("name", "pk")

    finalize_django_types()

    @strawberry.type
    class Query:
        genres: DjangoConnection[NamedGenreType] = DjangoConnectionField(NamedGenreType)

    converter = _RelayNameConverter() if renamed else NameConverter()
    return DjangoSchema(query=Query, config=strawberry_config(name_converter=converter))


def _post(schema: strawberry.Schema, document: str, color: str) -> JSONObject:
    """Drive a real native transport, reading the held schema only when the request arrives."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if color == "sync":
                return response_json(post_graphql(document, url="/graphql-names/"))
            response = asyncio.run(
                AsyncTestClient("/graphql-names-async/").query(document, assert_no_errors=False),
            )
            assert response.response.status_code == 200
            return response_json(response.response)
    finally:
        _CURRENT["schema"] = None


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("keyset", [False, True], ids=["offset", "keyset"])
@pytest.mark.parametrize("renamed", [False, True], ids=["default-names", "renamed"])
@pytest.mark.parametrize("color", ["sync", "async"])
@pytest.mark.parametrize(
    "selection",
    [
        "edges",
        "page-info",
        "count",
        "typename",
    ],
)
def test_connection_selected_pages_and_unselected_rows_follow_wire_names(
    record_compiled_sql: RecordCompiledSql,
    selection: str,
    color: str,
    *,
    keyset: bool,
    renamed: bool,
) -> None:
    """Each transport fetches selected pages and counts without fetching unselected node rows."""
    for name in ("C", "A", "B"):
        models.Genre.objects.create(name=name)
    schema = _schema(keyset=keyset, renamed=renamed)
    edge, node, page, count, first = (
        (
            "rows",
            "entry",
            "window",
            "size",
            "take",
        )
        if renamed
        else (
            "edges",
            "node",
            "pageInfo",
            "totalCount",
            "first",
        )
    )
    documents = {
        "edges": (
            edge + " { " + node + " { name } }",
            {edge: [{node: {"name": "A"}}, {node: {"name": "B"}}]},
        ),
        "page-info": (
            page + " { hasNextPage hasPreviousPage }",
            {page: {"hasNextPage": True, "hasPreviousPage": False}},
        ),
        "count": (count, {count: 3}),
        "typename": ("__typename", {"__typename": "NamedGenreTypeConnection"}),
    }
    fields, expected = documents[selection]
    sql = record_compiled_sql('FROM "library_genre"')
    payload = _post(schema, "{ genres(" + first + ": 2) { " + fields + " } }", color)
    assert payload == {"data": {"genres": expected}}, payload
    count_sql = [statement for statement in sql if "COUNT(" in statement.upper()]
    row_sql = [statement for statement in sql if "COUNT(" not in statement.upper()]
    if selection == "count":
        assert len(count_sql) == 1, sql
        assert row_sql == [], sql
    elif selection == "typename":
        assert sql == []
    else:
        assert count_sql == [], sql
        assert len(row_sql) == 1, sql
        assert "LIMIT 3" in row_sql[0].upper(), row_sql


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("keyset", [False, True], ids=["offset", "keyset"])
@pytest.mark.parametrize("color", ["sync", "async"])
def test_renamed_connection_selection_survives_aliases_and_anonymous_fragments(
    record_compiled_sql: RecordCompiledSql,
    color: str,
    *,
    keyset: bool,
) -> None:
    """Aliases retain response keys while anonymous fragments retain the renamed page selection."""
    for name in ("C", "A", "B"):
        models.Genre.objects.create(name=name)
    schema = _schema(keyset=keyset, renamed=True)
    sql = record_compiled_sql('FROM "library_genre"')
    payload = _post(
        schema,
        "{ page: genres(take: 2) { ... { picked: rows { entry { name } } } } }",
        color,
    )
    assert payload == {
        "data": {"page": {"picked": [{"entry": {"name": "A"}}, {"entry": {"name": "B"}}]}},
    }, payload
    assert len(sql) == 1, sql
    assert "COUNT(" not in sql[0].upper(), sql
    assert "LIMIT 3" in sql[0].upper(), sql


def _plain_schema(*, stream: bool = False) -> strawberry.Schema:
    """A standalone Strawberry ListConnection keeps its original async behavior.

    ``stream`` serves the rows from an async generator, which upstream slices lazily.
    """

    class PlainGenreType(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()

    def genre_rows() -> Iterable[models.Genre]:
        return models.Genre.objects.order_by("name", "pk")

    async def streamed_genre_rows() -> AsyncIterator[models.Genre]:
        async for genre in models.Genre.objects.order_by("name", "pk"):
            yield genre

    # Meta.interfaces installs Node at runtime. Ask the upstream generic seam for its
    # specialization, rather than claiming the Python DjangoType class statically inherits Node.
    connection_type = object_result(operator.getitem, relay.ListConnection, PlainGenreType)
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"genres": connection_type},
                "genres": object_result(
                    relay.connection,
                    resolver=streamed_genre_rows if stream else genre_rows,
                ),
            },
        ),
    )
    return strawberry.Schema(query=query)


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db(transaction=True)
def test_plain_strawberry_async_connection_keeps_anonymous_fragments_working(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The upstream async path already serves anonymous fragments and must retain that behavior."""
    for name in ("C", "A", "B"):
        models.Genre.objects.create(name=name)
    schema = _plain_schema()
    sql = record_compiled_sql('FROM "library_genre"')
    payload = _post(schema, "{ genres(first: 2) { ... { edges { node { name } } } } }", "async")
    assert payload == {
        "data": {"genres": {"edges": [{"node": {"name": "A"}}, {"node": {"name": "B"}}]}},
    }, payload
    assert len(sql) == 1, sql
    assert "COUNT(" not in sql[0].upper(), sql
    assert "LIMIT 3" in sql[0].upper(), sql


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db(transaction=True)
def test_plain_strawberry_async_generator_connection_serves_its_trailing_page() -> None:
    """An async-generator source pages lazily, and ``last`` alone keeps its trailing rows."""
    for name in ("C", "A", "B"):
        models.Genre.objects.create(name=name)
    payload = _post(
        _plain_schema(stream=True),
        "{ genres(last: 2) { edges { node { name } } pageInfo { hasNextPage hasPreviousPage } } }",
        "async",
    )
    assert payload == {
        "data": {
            "genres": {
                "edges": [{"node": {"name": "B"}}, {"node": {"name": "C"}}],
                "pageInfo": {"hasNextPage": False, "hasPreviousPage": True},
            },
        },
    }, payload


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("color", ["sync", "async"])
@pytest.mark.parametrize("size", [-1, 101], ids=["negative", "over-cap"])
def test_plain_strawberry_unselected_connection_still_validates_its_page(
    record_compiled_sql: RecordCompiledSql,
    color: str,
    size: int,
) -> None:
    """Unselected rows do not bypass Strawberry's native page validation or its error path."""
    models.Genre.objects.create(name="A")
    schema = _plain_schema()
    sql = record_compiled_sql('FROM "library_genre"')
    payload = _post(schema, "{ genres(first: " + str(size) + ") { ... { __typename } } }", color)
    assert payload["data"] is None, payload
    errors = json_list(payload, "errors")
    assert len(errors) == 1
    error = json_object(errors, 0)
    expected = (
        "Argument 'first' must be a non-negative integer."
        if size < 0
        else "Argument 'first' cannot be higher than 100."
    )
    assert error["message"] == expected
    assert error["path"] == ["genres"]
    assert sql == []


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("keyset", [False, True], ids=["offset", "keyset"])
@pytest.mark.parametrize("color", ["sync", "async"])
def test_a_fragment_named_edges_does_not_select_the_connection_field(
    record_compiled_sql: RecordCompiledSql,
    color: str,
    *,
    keyset: bool,
) -> None:
    """A fragment name is not a published field: typename alone performs no row query."""
    for name in ("C", "A", "B"):
        models.Genre.objects.create(name=name)
    schema = _schema(keyset=keyset, renamed=False)
    sql = record_compiled_sql('FROM "library_genre"')
    payload = _post(
        schema,
        "{ genres(first: 2) { ...edges } } fragment edges on NamedGenreTypeConnection { __typename }",
        color,
    )
    assert payload == {"data": {"genres": {"__typename": "NamedGenreTypeConnection"}}}, payload
    assert sql == []
