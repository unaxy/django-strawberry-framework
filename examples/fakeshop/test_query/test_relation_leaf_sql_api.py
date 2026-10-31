"""Walked relation predicates preserve null extension, orphan-safe negation and independent SQL.

Ordinary JSON reaches the original unbound FilterSet through a native HTTP holder.
The visible orphan has no genre link, so child-key NOT IN would be poisoned by NULL.
The unfiltered sibling preserves empty and hidden-only roots for every verdict.
"""

from collections.abc import Sequence
from functools import wraps

import pytest
import strawberry
from apps.library import models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import CharFilter
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
)
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


urlpatterns = [path("graphql-relation-leaf-sql/", _graphql_view)]


def _schema() -> DjangoSchema:
    class BookChild(FilterSet):
        class Meta:
            model = models.Book
            fields = {"title": ["exact"], "subtitle": ["exact", "isnull"]}

    class GenreParent(FilterSet):
        visible_books = RelatedFilter(BookChild, field_name="books")
        without_title = CharFilter(field_name="books__title", exclude=True)

        class Meta:
            model = models.Genre
            fields = {
                "name": ["exact"],
                "books": ["exact", "isnull"],
                "books__title": ["exact"],
                "books__subtitle": ["isnull"],
            }

    class VisibleBook(DjangoType):
        class Meta:
            model = models.Book
            fields = ("title", "subtitle")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.Book],
            info: object,
        ) -> QuerySet[models.Book]:
            del info
            return queryset.exclude(circulation_status="repair")

    class GenreOutput(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("name",)

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[models.Genre]:
        del root
        return GenreParent.apply_sync(where, models.Genre.objects.order_by("name"), info)

    def resolve_all_rows(root: object) -> QuerySet[models.Genre]:
        del root
        return models.Genre.objects.order_by("name")

    @strawberry.type
    class Query:
        rows: QuerySet[models.Genre] = strawberry.field(
            resolver=resolve_rows,
            graphql_type=list[GenreOutput],
        )
        all_rows: QuerySet[models.Genre] = strawberry.field(
            resolver=resolve_all_rows,
            graphql_type=list[GenreOutput],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=[VisibleBook],
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _book(title: str, *, subtitle: str | None = None, hidden: bool = False) -> models.Book:
    branch = models.Branch.objects.create(name=f"branch-{models.Branch.objects.count()}")
    shelf = models.Shelf.objects.create(branch=branch, code="own")
    return models.Book.objects.create(
        title=title,
        subtitle=subtitle,
        shelf=shelf,
        circulation_status="repair" if hidden else "available",
    )


def _world() -> None:
    visible_x = _book("x")
    hidden_x = _book("x", subtitle="s", hidden=True)
    hidden_y = _book("y", hidden=True)
    visible_y = _book("y", subtitle="s")
    _book("x", subtitle="orphan-null-key")
    for name, members in (
        ("mixed", [visible_x, hidden_x]),
        ("hidden_only", [hidden_y]),
        ("empty", []),
        ("other", [visible_y]),
        ("plain", [visible_x, visible_y]),
    ):
        genre = models.Genre.objects.create(name=name)
        genre.books.set(members)


def _post(schema: DjangoSchema, where: JSONObject) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                "query($where: JSON!) { rows(where: $where) { name } allRows { name } }",
                variables={"where": where},
                url="/graphql-relation-leaf-sql/",
            )
    finally:
        _CURRENT["schema"] = None


def _expected(names: Sequence[str]) -> JSONObject:
    return {
        "data": {
            "rows": [{"name": name} for name in names],
            "allRows": [
                {"name": name}
                for name in (
                    "empty",
                    "hidden_only",
                    "mixed",
                    "other",
                    "plain",
                )
            ],
        },
    }


def _root_selects(statements: Sequence[str]) -> list[str]:
    return [
        statement
        for statement in statements
        if statement.lstrip().startswith("SELECT ") and ' FROM "library_genre"' in statement
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("where", "names"),
    [
        pytest.param(
            {"visible_books": {"subtitle": {"is_null": True}}},
            ["mixed", "plain"],
            id="nested-null-is-existential",
        ),
        pytest.param(
            {"books__subtitle": {"is_null": True}},
            [
                "empty",
                "hidden_only",
                "mixed",
                "plain",
            ],
            id="flat-null-extends",
        ),
        pytest.param(
            {"without_title": "x"},
            ["empty", "hidden_only", "other"],
            id="flat-exclude",
        ),
        pytest.param(
            {"not_": {"books__title": "x"}},
            ["empty", "hidden_only", "other"],
            id="logical-not",
        ),
    ],
)
def test_flat_null_extension_and_negation_keep_their_distinct_relation_meanings(
    where: JSONObject,
    names: list[str],
) -> None:
    """Hidden-only and empty genres distinguish null extension from nested existence over visible books."""
    _world()
    payload = _post(_schema(), where)
    assert payload == _expected(names), payload


@pytest.mark.django_db
def test_excluding_a_book_title_uses_not_exists_despite_a_visible_orphans_null_genre_key(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A visible matching book with no genre cannot poison the exclusion as a NOT IN NULL would."""
    _world()
    schema = _schema()
    statements = record_compiled_sql()
    payload = _post(schema, {"without_title": "x"})
    assert payload == _expected(["empty", "hidden_only", "other"]), payload
    sql = _root_selects(statements)
    assert len(sql) == 2, sql
    assert sql[0].upper().count("NOT (EXISTS(") == 1, sql
    assert " NOT IN " not in sql[0].upper(), sql
    assert "DISTINCT" not in sql[0].upper(), sql


@pytest.mark.django_db
def test_independent_walked_leaves_correlate_without_rescanning_the_parent_or_earlier_leaves(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Two book leaves add their own correlated predicates without rescanning Genre or adding DISTINCT."""
    _world()
    schema = _schema()
    statements = record_compiled_sql()
    payload = _post(
        schema,
        {"books__title": "x", "books__subtitle": {"is_null": False}, "name": "mixed"},
    )
    assert payload == _expected([]), payload
    sql = _root_selects(statements)
    assert len(sql) == 2, sql
    assert sql[0].count("EXISTS") == 4, sql
    assert sql[0].count('FROM "library_genre"') == 1, sql
    assert "DISTINCT" not in sql[0], sql
    assert " IN (SELECT" not in sql[0], sql
