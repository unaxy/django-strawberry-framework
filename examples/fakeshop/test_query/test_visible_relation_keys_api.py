"""Native HTTP visible target keys and fully undeclared relation paths.

The generated raw relation key, authored model-choice carriers and authored
GlobalID carriers remain separate public inputs. Scoped Book types hide repair
rows for both declared and undeclared relation walks. Membership fixtures have
first-only, second-only, both and neither roots, so an implementation consuming
only the first requested member cannot pass. Pure hook-call/normalized-data
identity observations remain package-owned.
"""

from collections.abc import Sequence
from functools import wraps
from typing import NamedTuple

import pytest
import strawberry
from apps.library import models
from apps.library.filters import ModelChoiceInFilter
from django.db import models as django_models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import CharFilter, ModelChoiceFilter, ModelMultipleChoiceFilter
from graphql import GraphQLInputObjectType, get_named_type
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_object,
)
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
from django_strawberry_framework.filters import (
    FilterSet,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    RelatedFilter,
)
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_input_fields,
    graphql_type_of,
)
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-visible-keys/", _graphql_view)]


def _post(schema: DjangoSchema, where: JSONObject) -> JSONObject:
    query = (
        f"query($where: {_input(schema).name}!) {{ rows(filter: $where) {{ "
        "totalCount edges { node { id name } } } }"
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(query, variables={"where": where}, url="/graphql-visible-keys/")
    finally:
        _CURRENT["schema"] = None


def _input(schema: DjangoSchema) -> GraphQLInputObjectType:
    query = schema._schema.query_type
    assert query is not None
    named = get_named_type(graphql_type_of(graphql_fields(query)["rows"].args["filter"]))
    assert isinstance(named, GraphQLInputObjectType)
    return named


def _where(schema: DjangoSchema, python_path: Sequence[str], value: object) -> JSONObject:
    """Use the executing definitions and configured NameConverter for every published name."""
    current = _input(schema)
    names: list[str] = []
    for index, name in enumerate(python_path):
        definition = schema.get_type_by_name(current.name)
        assert isinstance(definition, StrawberryObjectDefinition)
        field = next(field for field in definition.fields if field.python_name == name)
        wire = schema.config.name_converter.from_field(field)
        names.append(wire)
        if index < len(python_path) - 1:
            child = get_named_type(graphql_type_of(graphql_input_fields(current)[wire]))
            assert isinstance(child, GraphQLInputObjectType)
            current = child
    assert names
    result: JSONObject = {names[-1]: value}
    for wire in reversed(names[:-1]):
        result = {wire: result}
    return result


def _expected(root: type[DjangoType], rows: Sequence[models.Genre]) -> JSONObject:
    return {
        "data": {
            "rows": {
                "totalCount": len(rows),
                "edges": [
                    {"node": {"id": global_id_for(root, saved_pk(row)), "name": row.name}}
                    for row in rows
                ],
            },
        },
    }


def _visible_books(
    _cls: type[DjangoType],
    queryset: django_models.QuerySet[models.Book],
    _info: object,
    **_kwargs: object,
) -> django_models.QuerySet[models.Book]:
    return queryset.exclude(circulation_status=models.Book.CirculationStatus.REPAIR)


def _visible_shelves(
    _cls: type[DjangoType],
    queryset: django_models.QuerySet[models.Shelf],
    _info: object,
    **_kwargs: object,
) -> django_models.QuerySet[models.Shelf]:
    return queryset.exclude(topic="secret")


class _World(NamedTuple):
    """Real identity and null-extension controls, ordered by their saved root keys."""

    genres: dict[str, models.Genre]
    books: dict[str, models.Book]
    shelves: list[models.Shelf]


def _world() -> _World:
    branch = models.Branch.objects.create(name="Visible key world")
    books: dict[str, models.Book] = {}
    shelves: list[models.Shelf] = []
    for name, title, subtitle, hidden in [
        (
            "first",
            "x",
            None,
            False,
        ),
        (
            "second",
            "y",
            "set",
            False,
        ),
        (
            "hidden-x",
            "x",
            "set",
            True,
        ),
        (
            "hidden-y",
            "y",
            "set",
            True,
        ),
        (
            "unlinked-x",
            "x",
            "set",
            False,
        ),
    ]:
        shelf = models.Shelf.objects.create(branch=branch, code=name)
        shelves.append(shelf)
        books[name] = models.Book.objects.create(
            shelf=shelf,
            title=title,
            subtitle=subtitle,
            circulation_status="repair" if hidden else "available",
        )
    genres: dict[str, models.Genre] = {}
    for name, members in [
        ("first-only", [books["first"]]),
        ("second-only", [books["second"]]),
        ("both", [books["first"], books["second"], books["hidden-x"]]),
        ("hidden-only", [books["hidden-x"], books["hidden-y"]]),
        ("neither", []),
    ]:
        genre = models.Genre.objects.create(name=name)
        genre.books.set(members)
        genres[name] = genre
    return _World(genres, books, shelves)


def _holder(
    *,
    mode: str,
    declared: bool = False,
    relay_books: bool = False,
    wrong_kind: str = "multiple-exact",
) -> tuple[DjangoSchema, type[DjangoType], type[DjangoType], type[DjangoType] | None]:
    class BookChild(FilterSet):
        class Meta:
            model = models.Book
            fields = {"title": ["exact"], "subtitle": ["isnull"]}

    book_meta: dict[str, object] = {"filterset_class": BookChild}
    if relay_books:
        book_meta["globalid_strategy"] = "type"
    book_type = make_django_type(
        "VisibleKeyBook",
        models.Book,
        ("id", "title"),
        node=relay_books,
        meta_extra=book_meta,
        namespace_extra={"get_queryset": classmethod(_visible_books)},
    )
    genre_filters: type[FilterSet]
    if mode == "carriers":

        class CarrierGenreKeys(FilterSet):
            if declared:
                visible_books = RelatedFilter(BookChild, field_name="books")
            has_book = ModelChoiceFilter(field_name="books", queryset=models.Book.objects.all())
            has_any_book = ModelMultipleChoiceFilter(
                field_name="books",
                queryset=models.Book.objects.all(),
            )
            has_book_in = ModelChoiceInFilter(
                field_name="books",
                queryset=models.Book.objects.all(),
            )
            has_book_global = GlobalIDMultipleChoiceFilter(field_name="books")

            class Meta:
                model = models.Genre
                fields = {"name": ["exact"]}

        genre_filters = CarrierGenreKeys
    elif mode == "wrong-model":

        class WrongModelKeys(FilterSet):
            if wrong_kind == "single-exact":
                has_book_global = GlobalIDFilter(field_name="books")
            else:
                has_book_global = GlobalIDMultipleChoiceFilter(
                    field_name="books",
                    lookup_expr="in" if wrong_kind == "multiple-in" else "exact",
                )

            class Meta:
                model = models.Genre
                fields = []

        genre_filters = WrongModelKeys
    else:

        class GeneratedGenreKeys(FilterSet):
            if declared:
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

        genre_filters = GeneratedGenreKeys
    root = make_django_type(
        "VisibleKeyGenre",
        models.Genre,
        ("id", "name"),
        meta_extra={
            "filterset_class": genre_filters,
            "connection": {"total_count": True},
            "globalid_strategy": "type",
        },
    )
    wrong_type: type[DjangoType] | None = None
    if mode == "wrong-model":
        wrong_type = make_django_type(
            "ActualWrongShelf",
            models.Shelf,
            ("id", "code"),
            meta_extra={"globalid_strategy": "type"},
        )

    def resolve_rows(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> django_models.QuerySet[models.Genre]:
        return models.Genre.objects.order_by("pk")

    @strawberry.type
    class Query:
        rows = DjangoConnectionField(root, resolver=resolve_rows)

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    extra = (book_type, wrong_type) if wrong_type is not None else (book_type,)
    schema = DjangoSchema(
        query=Query,
        types=extra,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    return schema, root, book_type, wrong_type


def _rows(world: _World, *names: str) -> list[models.Genre]:
    return [world.genres[name] for name in names]


@pytest.mark.django_db
@pytest.mark.parametrize("declared", [True, False], ids=["declared", "undeclared"])
@pytest.mark.parametrize("target", ["visible-members", "hidden-x", "hidden-y"])
def test_generated_raw_reverse_membership_reads_all_visible_requested_targets(
    target: str,
    *,
    declared: bool,
) -> None:
    """Raw generated relation IDs retain both membership alternatives and never admit a hidden target."""
    world = _world()
    schema, root, _book_type, _wrong_type = _holder(mode="generated", declared=declared)
    # Same-carrier first-target control also owns the original single-visible-ID verdict.
    assert _post(
        schema,
        _where(schema, ("books", "exact"), [saved_pk(world.books["first"])]),
    ) == _expected(
        root,
        _rows(world, "first-only", "both"),
    )
    keys = (
        [saved_pk(world.books["first"]), saved_pk(world.books["second"])]
        if target == "visible-members"
        else [saved_pk(world.books[target])]
    )
    payload = _post(schema, _where(schema, ("books", "exact"), keys))
    expected = (
        _rows(world, "first-only", "second-only", "both") if target == "visible-members" else []
    )
    assert payload == _expected(root, expected)


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["omitted", "null-key"])
def test_inactive_relation_key_keeps_empty_and_linked_roots_without_child_sql(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Omitted/None isNull does not impose existence; pure hook-call identity remains a private assertion."""
    world = _world()
    schema, root, _book_type, _wrong_type = _holder(mode="generated", declared=True)
    where = {} if case == "omitted" else _where(schema, ("books", "is_null"), None)
    sqls = record_compiled_sql()
    assert _post(schema, where) == _expected(root, list(world.genres.values()))
    assert all('"library_book"' not in sql for sql in sqls), sqls


@pytest.mark.django_db
@pytest.mark.parametrize("declared", [True, False], ids=["declared", "undeclared"])
@pytest.mark.parametrize("visibility", ["visible", "hidden"])
@pytest.mark.parametrize(
    "carrier",
    [
        "model-choice",
        "model-multiple",
        "model-choice-in",
        "globalid",
    ],
)
def test_authored_reverse_key_carriers_read_the_same_visible_target_rows(
    carrier: str,
    visibility: str,
    *,
    declared: bool,
) -> None:
    """Authored model-choice keys stay raw beside a Relay target; the GID carrier decodes real IDs."""
    world = _world()
    schema, root, book_type, _wrong_type = _holder(
        mode="carriers",
        declared=declared,
        relay_books=True,
    )
    chosen = (
        [world.books["first"], world.books["second"]]
        if visibility == "visible"
        else [world.books["hidden-x"], world.books["hidden-y"]]
    )
    if carrier == "model-choice":
        leaf = ("has_book", "exact")
        value: object = saved_pk(chosen[0])
        expected = _rows(world, "first-only", "both") if visibility == "visible" else []
    elif carrier == "model-multiple":
        leaf = ("has_any_book", "exact")
        value = [saved_pk(book) for book in chosen]
        expected = (
            _rows(world, "first-only", "second-only", "both") if visibility == "visible" else []
        )
    elif carrier == "model-choice-in":
        leaf = ("has_book_in", "in_")
        value = [saved_pk(book) for book in chosen]
        expected = (
            _rows(world, "first-only", "second-only", "both") if visibility == "visible" else []
        )
    else:
        leaf = ("has_book_global", "exact")
        value = [global_id_for(book_type, saved_pk(book)) for book in chosen]
        expected = (
            _rows(world, "first-only", "second-only", "both") if visibility == "visible" else []
        )
    assert _post(schema, _where(schema, leaf, value)) == _expected(root, expected)


_REVERSE_LEAF_CASES = [
    "positive",
    "null-subtitle",
    "nonnull-subtitle",
    "exclude",
    "no-visible-book",
    "visible-book",
]


@pytest.mark.django_db
@pytest.mark.parametrize("declared", [True, False], ids=["declared", "undeclared"])
@pytest.mark.parametrize("case", _REVERSE_LEAF_CASES)
def test_reverse_column_and_null_leaves_use_the_hidden_absent_world(
    case: str,
    *,
    declared: bool,
) -> None:
    """Column and key leaves read the Book scope with or without a declared relation branch."""
    world = _world()
    schema, root, _book_type, _wrong_type = _holder(mode="generated", declared=declared)
    if case == "positive":
        where = _where(schema, ("books_title", "exact"), "x")
        expected = _rows(world, "first-only", "both")
    elif case in {"null-subtitle", "nonnull-subtitle"}:
        null = case == "null-subtitle"
        where = _where(schema, ("books_subtitle", "is_null"), null)
        expected = (
            _rows(world, "first-only", "both", "hidden-only", "neither")
            if null
            else _rows(world, "second-only", "both")
        )
    elif case == "exclude":
        where = _where(schema, ("without_title", "exact"), "x")
        expected = _rows(world, "second-only", "hidden-only", "neither")
    else:
        null = case == "no-visible-book"
        where = _where(schema, ("books", "is_null"), null)
        expected = (
            _rows(world, "hidden-only", "neither")
            if null
            else _rows(world, "first-only", "second-only", "both")
        )
    assert _post(schema, where) == _expected(root, expected)


@pytest.mark.django_db
def test_expanded_reverse_child_column_reads_only_visible_books() -> None:
    """A renamed declared branch's expanded child leaf cannot match its hidden Book rows."""
    world = _world()
    schema, root, _book_type, _wrong_type = _holder(mode="generated", declared=True)

    payload = _post(schema, _where(schema, ("visible_books_title", "exact"), "x"))

    assert payload == _expected(root, _rows(world, "first-only", "both")), payload


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["multiple-exact", "multiple-in", "single-exact"])
def test_undeclared_globalid_carrier_rejects_a_real_other_models_vocabulary(
    kind: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The same active carrier accepts Book IDs, then rejects a saved Shelf ID with its mismatch error."""
    world = _world()
    schema, root, book_type, wrong_type = _holder(
        mode="wrong-model",
        relay_books=True,
        wrong_kind=kind,
    )
    assert wrong_type is not None
    first_id = global_id_for(book_type, saved_pk(world.books["first"]))
    second_id = global_id_for(book_type, saved_pk(world.books["second"]))
    wrong_id = global_id_for(wrong_type, saved_pk(world.shelves[0]))
    leaf = ("has_book_global", "in_" if kind == "multiple-in" else "exact")
    valid: object = first_id if kind == "single-exact" else [first_id, second_id]
    expected = (
        _rows(world, "first-only", "both")
        if kind == "single-exact"
        else _rows(world, "first-only", "second-only", "both")
    )
    assert _post(schema, _where(schema, leaf, valid)) == _expected(root, expected)
    sqls = record_compiled_sql()
    bad: object = wrong_id if kind == "single-exact" else [wrong_id]
    payload = _post(schema, _where(schema, leaf, bad))
    assert payload["data"] is None, payload
    assert len(json_list(payload, "errors")) == 1
    error = json_object(payload, "errors", 0)
    assert json_at(error, "path") == ["rows"]
    expected_name = strawberry.relay.GlobalID.from_id(first_id).type_name
    wrong_name = strawberry.relay.GlobalID.from_id(wrong_id).type_name
    suffix = "" if kind == "single-exact" else " at index 0"
    assert (
        json_at(error, "message")
        == f"GlobalID type mismatch: filter expects {expected_name} but received {wrong_name}{suffix}"
    )
    # Wrong-model mismatch is intentionally code-less, unlike malformed IDs.
    assert "extensions" not in error
    assert not [sql for sql in sqls if '"library_genre"' in sql or '"library_book"' in sql], sqls


@pytest.mark.django_db
@pytest.mark.parametrize("book_visibility", ["visible", "hidden"])
@pytest.mark.parametrize("shelf_visibility", ["open", "secret"])
def test_generated_key_after_two_undeclared_hops_requires_both_visible_targets(
    book_visibility: str,
    shelf_visibility: str,
) -> None:
    """A matching Shelf key is insufficient if either the intervening Book or final Shelf is hidden."""

    class GenreKeys(FilterSet):
        class Meta:
            model = models.Genre
            fields = {"books__shelf": ["exact"]}

    shelf_type = make_django_type(
        "TwoHiddenShelf",
        models.Shelf,
        ("code",),
        node=False,
        namespace_extra={"get_queryset": classmethod(_visible_shelves)},
    )
    book_type = make_django_type(
        "TwoHiddenBook",
        models.Book,
        ("title",),
        node=False,
        namespace_extra={"get_queryset": classmethod(_visible_books)},
    )
    root = make_django_type(
        "TwoHiddenGenre",
        models.Genre,
        ("id", "name"),
        meta_extra={"filterset_class": GenreKeys, "connection": {"total_count": True}},
    )
    branch = models.Branch.objects.create(name="Two hidden hops")
    shelves: dict[str, models.Shelf] = {}
    genres: dict[str, models.Genre] = {}
    for key, topic, status in [
        ("visible-open", "open", "available"),
        ("visible-secret", "secret", "available"),
        ("hidden-open", "open", "repair"),
        ("hidden-secret", "secret", "repair"),
    ]:
        shelf = models.Shelf.objects.create(branch=branch, code=key, topic=topic)
        shelves[key] = shelf
        book = models.Book.objects.create(shelf=shelf, title="same", circulation_status=status)
        genre = models.Genre.objects.create(name=key)
        genre.books.add(book)
        genres[key] = genre
    second_positive = models.Genre.objects.create(name="second-visible-open")
    open_book = models.Book.objects.get(shelf=shelves["visible-open"])
    second_positive.books.add(open_book)

    def resolve_rows(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> django_models.QuerySet[models.Genre]:
        return models.Genre.objects.order_by("pk")

    @strawberry.type
    class Query:
        rows = DjangoConnectionField(root, resolver=resolve_rows)

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=Query,
        types=(book_type, shelf_type),
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    positive = _where(schema, ("books_shelf", "exact"), saved_pk(shelves["visible-open"]))
    positive_rows = [genres["visible-open"], second_positive]
    assert _post(schema, positive) == _expected(root, positive_rows)
    key = f"{book_visibility}-{shelf_visibility}"
    payload = _post(schema, _where(schema, ("books_shelf", "exact"), saved_pk(shelves[key])))
    assert payload == _expected(root, positive_rows if key == "visible-open" else [])
