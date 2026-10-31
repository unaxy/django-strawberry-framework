"""Walked relation leaves use their root queryset's database on every correlation link.

The two databases carry the same keys but opposing genre membership, so a visibility
seed or relation link routed to default cannot answer the shard_b request correctly.
The consumer hook also records the actual queryset alias it receives.
"""

import os
from functools import wraps

import pytest

if os.environ.get("FAKESHOP_SHARDED") != "1":
    pytest.skip("requires FAKESHOP_SHARDED=1", allow_module_level=True)

import strawberry
from apps.library import models
from django.db import connections
from django.db import models as django_models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django_filters import CharFilter
from graphql_client import JSONObject, graphql_payload
from strawberry.scalars import JSON
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-relation-worlds-sharded/", _graphql_view)]


def _seed_alias(alias: str, *, matching_member: bool) -> None:
    """Give both aliases identical carrier keys and opposite visible membership."""
    branch = models.Branch.objects.using(alias).create(pk=1, name="branch")
    shelf = models.Shelf.objects.using(alias).create(pk=1, branch=branch, code="shelf")
    open_book = models.Book.objects.using(alias).create(pk=1, shelf=shelf, title="x")
    hidden_shelf = models.Shelf.objects.using(alias).create(pk=2, branch=branch, code="hidden")
    hidden_book = models.Book.objects.using(alias).create(
        pk=2,
        shelf=hidden_shelf,
        title="x",
        circulation_status="repair",
    )
    for key, name in enumerate(("matching", "hidden-only", "empty"), 1):
        models.Genre.objects.using(alias).create(pk=key, name=name)
    models.Book.genres.through.objects.using(alias).create(
        book_id=open_book.pk,
        genre_id=1 if matching_member else 2,
    )
    models.Book.genres.through.objects.using(alias).create(book_id=hidden_book.pk, genre_id=2)


def _schema(*, declared: bool, seen: list[str]) -> DjangoSchema:
    class BookTarget(DjangoType):
        class Meta:
            model = models.Book
            fields = ("id", "title")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: django_models.QuerySet[models.Book],
            info: strawberry.Info[object, object],
        ) -> django_models.QuerySet[models.Book]:
            del info
            seen.append(queryset.db)
            # This consumer publishes only its shard-local collection.
            if queryset.db != "shard_b":
                return queryset.none()
            return queryset.exclude(circulation_status="repair")

    class BookChild(FilterSet):
        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    class GenreParent(FilterSet):
        if declared:
            visible_books = RelatedFilter(BookChild, field_name="books")
        without_title = CharFilter(field_name="books__title", exclude=True)

        class Meta:
            model = models.Genre
            fields = {"name": ["exact"], "books": ["exact", "isnull"], "books__title": ["exact"]}

    class GenreOutput(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("name",)

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: strawberry.Info[object, object],
            where: JSON,
        ) -> django_models.QuerySet[models.Genre]:
            return GenreParent.apply_sync(
                where,
                models.Genre.objects.using("shard_b").order_by("pk"),
                info,
            )

        def _all_rows(self) -> django_models.QuerySet[models.Genre]:
            return models.Genre.objects.using("shard_b").order_by("pk")

        rows: django_models.QuerySet[models.Genre] = strawberry.field(
            resolver=_rows,
            graphql_type=list[GenreOutput],
        )
        all_rows: django_models.QuerySet[models.Genre] = strawberry.field(
            resolver=_all_rows,
            graphql_type=list[GenreOutput],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=[BookTarget],
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


@pytest.mark.django_db(databases=["default", "shard_b"])
@pytest.mark.parametrize("declared", [True, False], ids=["declared", "undeclared"])
@pytest.mark.parametrize("verdict", ["positive", "null", "exclude"])
def test_walked_filter_scopes_and_correlates_on_its_root_database(
    verdict: str,
    *,
    declared: bool,
) -> None:
    """A declared or undeclared Book hop reads shard_b's rows and passes that alias to its hook."""
    _seed_alias("default", matching_member=False)
    _seed_alias("shard_b", matching_member=True)
    seen: list[str] = []
    schema = _schema(declared=declared, seen=seen)
    if verdict == "positive":
        where: JSONObject = {"books__title": "x"}
        expected = ["matching"]
    elif verdict == "null":
        where = {"books": {"is_null": True}}
        expected = ["hidden-only", "empty"]
    else:
        where = {"without_title": "x"}
        expected = ["hidden-only", "empty"]
    _CURRENT["schema"] = schema
    try:
        with (
            override_settings(ROOT_URLCONF=__name__),
            CaptureQueriesContext(connections["default"]) as default_queries,
            CaptureQueriesContext(connections["shard_b"]) as shard_queries,
        ):
            payload = graphql_payload(
                "query($where: JSON!) { rows(where: $where) { name } allRows { name } }",
                variables={"where": where},
                url="/graphql-relation-worlds-sharded/",
            )
    finally:
        _CURRENT["schema"] = None
    assert payload == {
        "data": {
            "rows": [{"name": name} for name in expected],
            "allRows": [{"name": name} for name in ("matching", "hidden-only", "empty")],
        },
    }, payload
    assert seen == ["shard_b"]
    assert not any('"library_' in query["sql"] for query in default_queries), list(default_queries)
    roots = [query["sql"] for query in shard_queries if 'FROM "library_genre"' in query["sql"]]
    assert len(roots) == 2, list(shard_queries)
    filtered = [sql for sql in roots if "EXISTS" in sql.upper()]
    assert len(filtered) == 1, roots
    assert '"library_book"' in filtered[0], filtered
    assert '"library_book_genres"' in filtered[0], filtered
