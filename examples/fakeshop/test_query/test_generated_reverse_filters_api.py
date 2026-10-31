"""Generated reverse relation predicates through native sync and async HTTP.

The shipped library filters declare relation branches. These holders publish
only the specified Meta.fields traversal, preserving the hook-free generated
candidate path rather than substituting its declared RelatedFilter twin.
All root resolvers supply explicit primary-key order. Exact occurrence lists
and selected totalCount expose fan-out; crossed range rows, empty parents and
wrong generic content types distinguish independently false predicates.
"""

import asyncio
import datetime
import uuid
from collections.abc import Mapping, Sequence
from functools import wraps

import pytest
import strawberry
from apps.library import models as library_models
from apps.scalars import models as scalar_models
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql import GraphQLInputObjectType, get_named_type
from graphql_client import JSONObject, RecordCompiledSql, graphql_payload, response_json
from strategy_schemas import make_django_type
from strawberry.types.base import StrawberryObjectDefinition

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_input_fields,
    graphql_type_of,
)
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._idioms import saved_pk

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
    path("graphql-generated-reverse/", _graphql_view),
    path("graphql-generated-reverse-async/", _async_graphql_view),
]


async def _async_post(document: str, variables: Mapping[str, object]) -> JSONObject:
    result = await AsyncTestClient().query(
        document,
        variables,
        assert_no_errors=False,
        url="/graphql-generated-reverse-async/",
    )
    assert result.response.status_code == 200
    return response_json(result.response)


def _post(
    schema: DjangoSchema,
    document: str,
    variables: Mapping[str, object],
    *,
    transport: str = "sync",
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if transport == "async":
                return asyncio.run(_async_post(document, variables))
            return graphql_payload(
                document,
                variables=variables,
                url="/graphql-generated-reverse/",
            )
    finally:
        _CURRENT["schema"] = None


def _holder(
    model: type[models.Model],
    scalar: str,
    fields: Mapping[str, Sequence[str]],
    *,
    targets: Sequence[type[DjangoType]] = (),
) -> tuple[DjangoSchema, type[DjangoType]]:
    declared = type(
        "GeneratedReverseFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": model, "fields": fields})},
    )
    assert issubclass(declared, FilterSet)
    row_type = make_django_type(
        "GeneratedReverseRow",
        model,
        ("id", scalar),
        meta_extra={"filterset_class": declared, "connection": {"total_count": True}},
    )

    def resolve_rows(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> models.QuerySet[models.Model]:
        return model._default_manager.order_by("pk")

    @strawberry.type
    class Query:
        rows = DjangoConnectionField(row_type, resolver=resolve_rows)

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return (
        DjangoSchema(
            query=Query,
            types=targets,
            config=strawberry_config(),
            extensions=[lambda: optimizer],
        ),
        row_type,
    )


def _filter_input(schema: DjangoSchema) -> GraphQLInputObjectType:
    query = schema._schema.query_type
    assert query is not None
    named = get_named_type(graphql_type_of(graphql_fields(query)["rows"].args["filter"]))
    assert isinstance(named, GraphQLInputObjectType)
    return named


def _where(schema: DjangoSchema, python_path: Sequence[str], value: object) -> JSONObject:
    """Read each input's actual definition and configured converter, including logic keys."""
    current = _filter_input(schema)
    names: list[str] = []
    for index, python_name in enumerate(python_path):
        definition = schema.get_type_by_name(current.name)
        assert isinstance(definition, StrawberryObjectDefinition)
        field = next(field for field in definition.fields if field.python_name == python_name)
        published = schema.config.name_converter.from_field(field)
        names.append(published)
        if index < len(python_path) - 1:
            nested = get_named_type(graphql_type_of(graphql_input_fields(current)[published]))
            assert isinstance(nested, GraphQLInputObjectType)
            current = nested
    assert names
    result: JSONObject = {names[-1]: value}
    for name in reversed(names[:-1]):
        result = {name: result}
    return result


def _document(schema: DjangoSchema, scalar: str) -> str:
    return (
        f"query($where: {_filter_input(schema).name}!) {{ rows(filter: $where) {{ "
        f"totalCount edges {{ node {{ id name: {scalar} }} }} }} }}"
    )


def _expected(row_type: type[DjangoType], rows: Sequence[tuple[models.Model, str]]) -> JSONObject:
    return {
        "data": {
            "rows": {
                "totalCount": len(rows),
                "edges": [
                    {"node": {"id": global_id_for(row_type, saved_pk(row)), "name": name}}
                    for row, name in rows
                ],
            },
        },
    }


def _assert_root_predicate_sql(sqls: Sequence[str], model: type[models.Model]) -> None:
    """Positive witnesses read one root page and one count without multiplying its outer FROM."""
    table = model._meta.db_table
    statements = [
        sql
        for sql in sqls
        if sql.lstrip().upper().startswith("SELECT ")
        and " FROM " in sql
        and sql.split(" FROM ", 1)[1].startswith(f'"{table}"')
    ]
    pages = [sql for sql in statements if "COUNT(" not in sql.upper()]
    counts = [sql for sql in statements if "COUNT(" in sql.upper()]
    assert len(pages) == 1, sqls
    assert len(counts) == 1, sqls
    for sql in statements:
        assert "EXISTS" in sql.upper(), sql
        assert "DISTINCT" not in sql.upper(), sql
        assert " JOIN " not in sql.split(" WHERE ", 1)[0].upper(), sql


def _shelf() -> library_models.Shelf:
    branch = library_models.Branch.objects.create(name="Generated reverse branch")
    return library_models.Shelf.objects.create(branch=branch, code="GENERATED")


def _loan(book: library_models.Book, note: str) -> library_models.Loan:
    patron = library_models.Patron.objects.create(name=note)
    return library_models.Loan.objects.create(book=book, patron=patron, note=note)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("relation", ["reverse-fk", "reverse-m2m"])
def test_generated_reverse_text_keeps_each_matching_root_once_on_each_executor(
    relation: str,
    transport: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Generated reverse FK/M2M leaves retain two distinct matches, excluding empty and nonmatching roots."""
    shelf = _shelf()
    if relation == "reverse-fk":
        first = library_models.Book.objects.create(shelf=shelf, title="Two matching loans")
        second = library_models.Book.objects.create(shelf=shelf, title="One matching loan")
        other = library_models.Book.objects.create(shelf=shelf, title="Other loans")
        library_models.Book.objects.create(shelf=shelf, title="No loans")
        _loan(first, "Cardio one")
        _loan(first, "Cardio two")
        _loan(second, "Cardio three")
        _loan(other, "Neuro")
        target = make_django_type("GeneratedLoan", library_models.Loan, ("note",), node=False)
        model: type[models.Model] = library_models.Book
        scalar = "title"
        path = "loans_note"
        fields = {"loans__note": ["icontains"]}
        expected_rows: list[tuple[models.Model, str]] = [
            (first, "Two matching loans"),
            (second, "One matching loan"),
        ]
    else:
        first_genre = library_models.Genre.objects.create(name="Two matching books")
        second_genre = library_models.Genre.objects.create(name="One matching book")
        other_genre = library_models.Genre.objects.create(name="Other books")
        library_models.Genre.objects.create(name="No books")
        first_book = library_models.Book.objects.create(shelf=shelf, title="Cardio one")
        first_book.genres.add(first_genre, second_genre)
        second_book = library_models.Book.objects.create(shelf=shelf, title="Cardio two")
        second_book.genres.add(first_genre)
        other_book = library_models.Book.objects.create(shelf=shelf, title="Neuro")
        other_book.genres.add(other_genre)
        target = make_django_type("GeneratedBook", library_models.Book, ("title",), node=False)
        model = library_models.Genre
        scalar = "name"
        path = "books_title"
        fields = {"books__title": ["icontains"]}
        expected_rows = [(first_genre, "Two matching books"), (second_genre, "One matching book")]
    schema, row_type = _holder(model, scalar, fields, targets=(target,))
    where = _where(schema, (path, "i_contains"), "cardio")
    sqls = record_compiled_sql()
    payload = _post(schema, _document(schema, scalar), {"where": where}, transport=transport)
    assert payload == _expected(row_type, expected_rows)
    _assert_root_predicate_sql(sqls, model)


@pytest.mark.django_db
def test_generated_generic_relation_matches_only_the_correct_content_type(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Two matching tags retain one Branch and a same-ID Book tag cannot make another Branch match."""
    first = library_models.Branch.objects.create(name="Two matching tags")
    second = library_models.Branch.objects.create(name="One matching tag")
    other = library_models.Branch.objects.create(name="Wrong content type")
    library_models.Branch.objects.create(name="No tags")
    content_type = ContentType.objects.get_for_model(library_models.Branch)
    for branch, tag in [(first, "cardio one"), (first, "cardio two"), (second, "cardio three")]:
        library_models.TaggedItem.objects.create(
            content_type=content_type,
            object_id=saved_pk(branch),
            tag=tag,
        )
    library_models.TaggedItem.objects.create(
        content_type=content_type,
        object_id=saved_pk(other),
        tag="neuro",
    )
    shelf = library_models.Shelf.objects.create(branch=other, code="OTHER")
    wrong_domain = library_models.Book.objects.create(
        id=saved_pk(other),
        shelf=shelf,
        title="Book sharing a Branch primary key",
    )
    library_models.TaggedItem.objects.create(
        content_type=ContentType.objects.get_for_model(library_models.Book),
        object_id=saved_pk(wrong_domain),
        tag="cardio wrong domain",
    )
    target = make_django_type("GeneratedTag", library_models.TaggedItem, ("tag",), node=False)
    schema, row_type = _holder(
        library_models.Branch,
        "name",
        {"tags__tag": ["icontains"]},
        targets=(target,),
    )
    sqls = record_compiled_sql()
    payload = _post(
        schema,
        _document(schema, "name"),
        {"where": _where(schema, ("tags_tag", "i_contains"), "cardio")},
    )
    assert payload == _expected(row_type, [(first, first.name), (second, second.name)])
    _assert_root_predicate_sql(sqls, library_models.Branch)
    assert any('"content_type_id"' in sql for sql in sqls), sqls


@pytest.mark.django_db
@pytest.mark.parametrize("is_null", [True, False], ids=["null-or-empty", "nonnull-child"])
def test_generated_nullable_child_test_includes_empty_roots_only_for_null(
    record_compiled_sql: RecordCompiledSql,
    *,
    is_null: bool,
) -> None:
    """Null extension includes the empty Genre; mixed and multiply matching children never fan it out."""
    shelf = _shelf()
    nonnull = library_models.Genre.objects.create(name="Nonnull")
    null = library_models.Genre.objects.create(name="Null")
    empty = library_models.Genre.objects.create(name="Empty")
    mixed = library_models.Genre.objects.create(name="Mixed")
    for title, subtitle, genres in [
        ("Has subtitle", "Sub", (nonnull, mixed)),
        ("Also has subtitle", "Other", (nonnull,)),
        ("No subtitle", None, (null, mixed)),
        ("Also no subtitle", None, (null,)),
    ]:
        book = library_models.Book.objects.create(shelf=shelf, title=title, subtitle=subtitle)
        book.genres.add(*genres)
    target = make_django_type("GeneratedBook", library_models.Book, ("subtitle",), node=False)
    schema, row_type = _holder(
        library_models.Genre,
        "name",
        {"books__subtitle": ["isnull"]},
        targets=(target,),
    )
    sqls = record_compiled_sql()
    payload = _post(
        schema,
        _document(schema, "name"),
        {"where": _where(schema, ("books_subtitle", "is_null"), is_null)},
    )
    expected = (
        [(null, "Null"), (empty, "Empty"), (mixed, "Mixed")]
        if is_null
        else [(nonnull, "Nonnull"), (mixed, "Mixed")]
    )
    assert payload == _expected(row_type, expected)
    _assert_root_predicate_sql(sqls, library_models.Genre)


def _specimen(
    label: str,
    *,
    parent: scalar_models.ScalarSpecimen | None = None,
) -> scalar_models.ScalarSpecimen:
    return scalar_models.ScalarSpecimen.objects.create(
        label=label,
        occurred_on=datetime.date(2020, 1, 1),
        occurred_at=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
        occurred_time=datetime.time(1, 2, 3),
        external_id=uuid.UUID(int=1),
        parent=parent,
    )


@pytest.mark.django_db
def test_generated_nullable_parent_then_children_requires_a_real_parent_chain(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A matching sibling admits both children, while an identical label behind a NULL parent admits none."""
    parent = _specimen("Parent")
    first = _specimen("cardiology child", parent=parent)
    second = _specimen("Sibling", parent=parent)
    _specimen("cardiology but null parent")
    other_parent = _specimen("Other parent")
    _specimen("Unmatched child", parent=other_parent)
    schema, row_type = _holder(
        scalar_models.ScalarSpecimen,
        "label",
        {"parent__children__label": ["icontains"]},
    )
    sqls = record_compiled_sql()
    payload = _post(
        schema,
        _document(schema, "label"),
        {"where": _where(schema, ("parent_children_label", "i_contains"), "cardio")},
    )
    assert payload == _expected(row_type, [(first, first.label), (second, second.label)])
    _assert_root_predicate_sql(sqls, scalar_models.ScalarSpecimen)


@pytest.mark.django_db
def test_generated_independent_leaves_can_match_different_children(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Name and numeric-ID predicates may match separate genres; either single-condition book is excluded."""
    shelf = _shelf()
    cross = library_models.Book.objects.create(shelf=shelf, title="Cross row")
    name_only = library_models.Book.objects.create(shelf=shelf, title="Name only")
    id_only = library_models.Book.objects.create(shelf=shelf, title="ID only")
    library_models.Book.objects.create(shelf=shelf, title="No genres")
    cardio = library_models.Genre.objects.create(name="cardiology")
    neuro = library_models.Genre.objects.create(name="neurology")
    cross.genres.add(cardio, neuro)
    name_only.genres.add(cardio)
    id_only.genres.add(neuro)
    target = make_django_type("GeneratedGenre", library_models.Genre, ("name",), node=False)
    schema, row_type = _holder(
        library_models.Book,
        "title",
        {"genres__name": ["icontains"], "genres__id": ["gt"]},
        targets=(target,),
    )
    where = _where(schema, ("genres_name", "i_contains"), "cardio")
    where.update(_where(schema, ("genres_id", "gt"), saved_pk(cardio)))
    sqls = record_compiled_sql()
    payload = _post(schema, _document(schema, "title"), {"where": where})
    assert payload == _expected(row_type, [(cross, cross.title)])
    _assert_root_predicate_sql(sqls, library_models.Book)


@pytest.mark.django_db
@pytest.mark.parametrize("negated", [False, True], ids=["inside-single-child", "not-inside"])
def test_generated_range_does_not_combine_bounds_from_different_children(
    record_compiled_sql: RecordCompiledSql,
    *,
    negated: bool,
) -> None:
    """A split low/high pair cannot satisfy one closed range; NOT keeps that book and the empty book."""
    shelf = _shelf()
    split = library_models.Book.objects.create(shelf=shelf, title="Split")
    middle = library_models.Book.objects.create(shelf=shelf, title="Middle")
    empty = library_models.Book.objects.create(shelf=shelf, title="Empty")
    low = _loan(split, "low")
    mid = _loan(middle, "mid")
    high = _loan(split, "high")
    assert saved_pk(low) < saved_pk(mid) < saved_pk(high)
    target = make_django_type("GeneratedLoan", library_models.Loan, ("note",), node=False)
    schema, row_type = _holder(
        library_models.Book,
        "title",
        {"loans__id": ["range"]},
        targets=(target,),
    )
    path = ("not_", "loans_id", "range") if negated else ("loans_id", "range")
    where = _where(schema, path, [saved_pk(mid), saved_pk(mid)])
    sqls = record_compiled_sql()
    payload = _post(schema, _document(schema, "title"), {"where": where})
    expected = [(split, "Split"), (empty, "Empty")] if negated else [(middle, "Middle")]
    assert payload == _expected(row_type, expected)
    _assert_root_predicate_sql(sqls, library_models.Book)


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["empty", "mixed", "missing"])
def test_generated_reverse_integer_membership_keeps_empty_and_missing_restrictive(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """books.id membership is numeric even with a Relay Genre root, and absent IDs cannot widen it."""
    shelf = _shelf()
    first = library_models.Genre.objects.create(name="First")
    second = library_models.Genre.objects.create(name="Second")
    library_models.Genre.objects.create(name="No books")
    book = library_models.Book.objects.create(shelf=shelf, title="Requested")
    book.genres.add(first)
    other = library_models.Book.objects.create(shelf=shelf, title="Other")
    other.genres.add(second)
    absent = library_models.Book.objects.create(shelf=shelf, title="Deleted")
    missing_pk = saved_pk(absent)
    absent.delete()
    target = make_django_type("GeneratedBook", library_models.Book, ("title",), node=False)
    schema, row_type = _holder(
        library_models.Genre,
        "name",
        {"books__id": ["in"]},
        targets=(target,),
    )
    values = {"empty": [], "mixed": [saved_pk(book), missing_pk], "missing": [missing_pk]}
    sqls = record_compiled_sql()
    payload = _post(
        schema,
        _document(schema, "name"),
        {"where": _where(schema, ("books_id", "in_"), values[case])},
    )
    expected = [(first, "First")] if case == "mixed" else []
    assert payload == _expected(row_type, expected)
    if expected:
        _assert_root_predicate_sql(sqls, library_models.Genre)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case",
    [
        "union",
        "empty",
        "mixed",
        "missing",
    ],
)
def test_generated_relay_membership_preserves_one_occurrence_per_matching_book(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Real Genre IDs union whole memberships without duplicating the book matching both requested genres."""
    shelf = _shelf()
    first = library_models.Genre.objects.create(name="First")
    second = library_models.Genre.objects.create(name="Second")
    outside = library_models.Genre.objects.create(name="Outside")
    absent = library_models.Genre.objects.create(name="Deleted")
    both = library_models.Book.objects.create(shelf=shelf, title="Both")
    both.genres.add(first, second)
    one = library_models.Book.objects.create(shelf=shelf, title="One")
    one.genres.add(first)
    second_only = library_models.Book.objects.create(shelf=shelf, title="Second only")
    second_only.genres.add(second)
    other = library_models.Book.objects.create(shelf=shelf, title="Other")
    other.genres.add(outside)
    library_models.Book.objects.create(shelf=shelf, title="Empty")
    target = make_django_type("GeneratedGenre", library_models.Genre, ("id", "name"))
    schema, row_type = _holder(
        library_models.Book,
        "title",
        {"genres": ["in"]},
        targets=(target,),
    )
    first_id = global_id_for(target, saved_pk(first))
    second_id = global_id_for(target, saved_pk(second))
    missing_id = global_id_for(target, saved_pk(absent))
    absent.delete()
    values = {
        "union": [first_id, second_id],
        "empty": [],
        "mixed": [first_id, missing_id],
        "missing": [missing_id],
    }
    sqls = record_compiled_sql()
    payload = _post(
        schema,
        _document(schema, "title"),
        {"where": _where(schema, ("genres", "in_"), values[case])},
    )
    expected = {
        "union": [(both, "Both"), (one, "One"), (second_only, "Second only")],
        "mixed": [(both, "Both"), (one, "One")],
        "empty": [],
        "missing": [],
    }[case]
    assert payload == _expected(row_type, expected)
    if expected:
        _assert_root_predicate_sql(sqls, library_models.Book)
