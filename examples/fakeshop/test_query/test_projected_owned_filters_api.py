"""Native HTTP owners for projected methods and filters carrying their own callable.

These requests pin the independently observable distinctions:
constraining none versus identity, two method projections with independent
sibling predicates, the callable's own exclude/isnull behavior, and typed text
refusals before either a consumer binding or the inherited GlobalID decoder.
"""

import asyncio
from collections.abc import Mapping, Sequence
from functools import wraps
from importlib import import_module
from typing import NamedTuple, TypeVar

import pytest
import strawberry
from apps.library import models
from django.db import models as django_models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import BooleanFilter, CharFilter
from graphql import GraphQLInputObjectType, get_named_type
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_str,
    response_json,
)
from strategy_schemas import make_django_type
from strawberry.types.base import StrawberryObjectDefinition
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, GlobalIDFilter, RelatedFilter
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import read_attr, require_instance
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_input_fields,
    graphql_type_of,
)
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._idioms import saved_pk

_M = TypeVar("_M", bound=django_models.Model)
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
    path("graphql-owned-filters/", _graphql_view),
    path("graphql-owned-filters-async/", _async_graphql_view),
]


async def _async_post(document: str, variables: Mapping[str, object]) -> JSONObject:
    result = await AsyncTestClient().query(
        document,
        variables,
        assert_no_errors=False,
        url="/graphql-owned-filters-async/",
    )
    assert result.response.status_code == 200
    return response_json(result.response)


def _post(
    schema: DjangoSchema,
    document: str,
    where: JSONObject,
    *,
    transport: str = "sync",
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            variables = {"where": where}
            if transport == "async":
                return asyncio.run(_async_post(document, variables))
            return graphql_payload(document, variables=variables, url="/graphql-owned-filters/")
    finally:
        _CURRENT["schema"] = None


def _holder(
    model: type[django_models.Model],
    scalar: str,
    filterset: type[FilterSet],
    *,
    targets: Sequence[type[DjangoType]] = (),
    primary: bool = True,
) -> tuple[DjangoSchema, type[DjangoType]]:
    meta: dict[str, object] = {
        "filterset_class": filterset,
        "connection": {"total_count": True},
        "primary": primary,
    }
    if not primary:
        # A non-Relay primary cannot decode a secondary output's model-label ID.
        meta["globalid_strategy"] = "type"
    row_type = make_django_type(
        "OwnedFilterRoot",
        model,
        ("id", scalar),
        meta_extra=meta,
    )

    def resolve_rows(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> django_models.QuerySet[django_models.Model]:
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


def _filter_input(schema: DjangoSchema, root: str = "rows") -> GraphQLInputObjectType:
    query = schema._schema.query_type
    assert query is not None
    named = get_named_type(graphql_type_of(graphql_fields(query)[root].args["filter"]))
    assert isinstance(named, GraphQLInputObjectType)
    return named


def _where(
    schema: DjangoSchema,
    python_path: Sequence[str],
    value: object,
    *,
    root: str = "rows",
) -> JSONObject:
    """Read the executing input's definitions and configured NameConverter at every hop."""
    current = _filter_input(schema, root)
    published: list[str] = []
    for index, name in enumerate(python_path):
        definition = schema.get_type_by_name(current.name)
        assert isinstance(definition, StrawberryObjectDefinition)
        field = next(field for field in definition.fields if field.python_name == name)
        wire = schema.config.name_converter.from_field(field)
        published.append(wire)
        if index < len(python_path) - 1:
            target = get_named_type(graphql_type_of(graphql_input_fields(current)[wire]))
            assert isinstance(target, GraphQLInputObjectType)
            current = target
    assert published
    result: JSONObject = {published[-1]: value}
    for wire in reversed(published[:-1]):
        result = {wire: result}
    return result


def _document(schema: DjangoSchema, scalar: str) -> str:
    return (
        f"query($where: {_filter_input(schema).name}!) {{ rows(filter: $where) {{ "
        f"totalCount edges {{ node {{ id name: {scalar} }} }} }} }}"
    )


def _expected(
    row_type: type[DjangoType],
    rows: Sequence[tuple[django_models.Model, str]],
) -> JSONObject:
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


def _root_sql(sqls: Sequence[str], model: type[django_models.Model]) -> list[str]:
    return [
        sql
        for sql in sqls
        if sql.lstrip().upper().startswith("SELECT ")
        and " FROM " in sql
        and sql.split(" FROM ", 1)[1].startswith(f'"{model._meta.db_table}"')
    ]


def _shelf(code: str = "METHOD") -> models.Shelf:
    branch = models.Branch.objects.create(name=code)
    return models.Shelf.objects.create(branch=branch, code=code)


def _loan(book: models.Book, email: str, note: str) -> models.Loan:
    patron = models.Patron.objects.create(name=f"{saved_pk(book)}:{note}", email=email)
    return models.Loan.objects.create(book=book, patron=patron, note=note)


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
@pytest.mark.parametrize("answer", ["none", "zero", "identity"])
def test_projected_method_distinguishes_constraining_none_from_identity(
    answer: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A real method's .none() constrains its parent, while returning its actual input leaves all parents."""

    class PatronChild(FilterSet):
        decision = CharFilter(field_name="email", method="filter_decision")

        class Meta:
            model = models.Patron
            fields = []

        def filter_decision(
            self,
            queryset: django_models.QuerySet[models.Patron],
            _name: str,
            value: object,
        ) -> django_models.QuerySet[models.Patron]:
            if value == "none":
                return queryset.none()
            if value == "zero":
                return queryset.filter(email="absent@example.test")
            return queryset

    class LoanParent(FilterSet):
        patron = RelatedFilter(PatronChild)

        class Meta:
            model = models.Loan
            fields = []

    shelf = _shelf()
    book = models.Book.objects.create(shelf=shelf, title="Method book")
    first = _loan(book, "one@example.test", "one")
    second = _loan(book, "two@example.test", "two")
    target = make_django_type(
        "DecisionPatron",
        models.Patron,
        ("email",),
        node=False,
        meta_extra={"filterset_class": PatronChild},
    )
    schema, row_type = _holder(models.Loan, "note", LoanParent, targets=(target,))
    sqls = record_compiled_sql()
    payload = _post(
        schema,
        _document(schema, "note"),
        _where(schema, ("patron_decision", "exact"), answer),
    )
    expected = [(first, "one"), (second, "two")] if answer == "identity" else []
    assert payload == _expected(row_type, expected)
    statements = _root_sql(sqls, models.Loan)
    assert len(statements) == 2, sqls
    if answer == "none":
        # Exists(queryset.none()) compiles as a false constant on the parent;
        # the compiler still emits parent SELECT/COUNT, without a Patron scan.
        assert all('"library_patron"' not in sql for sql in statements), statements
        assert all("EXISTS" not in sql.upper() for sql in statements), statements
    elif answer == "zero":
        assert all('"library_patron"' in sql for sql in statements), statements
        assert all("EXISTS" in sql.upper() for sql in statements), statements


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case",
    [
        "accepted",
        "missing",
        "different-loan",
        "empty",
    ],
)
def test_shipped_twice_projected_method_keeps_an_independent_sibling_loan_predicate(
    case: str,
) -> None:
    """Twice-projected methods and sibling notes may use different loans; empty keeps bookless roots."""
    schema = require_instance(read_attr(import_module("config.schema"), "schema"), DjangoSchema)
    book_type = registry.get(models.Book)
    assert book_type is not None

    shelf = _shelf("TWICE")
    cross = models.Book.objects.create(shelf=shelf, title="Cross row")
    method_only = models.Book.objects.create(shelf=shelf, title="Method only")
    note_only = models.Book.objects.create(shelf=shelf, title="Note only")
    bookless = models.Book.objects.create(shelf=shelf, title="Bookless")
    _loan(cross, "p1@x", "alpha")
    _loan(cross, "p2@x", "beta")
    _loan(method_only, "p1@x", "gamma")
    _loan(note_only, "p2@x", "beta")
    value = {
        "accepted": "p1@x",
        "missing": "absent@x",
        "different-loan": "p1@x",
        "empty": "",
    }[case]
    where = _where(
        schema,
        ("loans_patron_email_must_have_at_sign", "exact"),
        value,
        root="allLibraryBooks",
    )
    if case == "different-loan":
        where.update(_where(schema, ("loans_note", "exact"), "beta", root="allLibraryBooks"))
    document = (
        f"query($where: {_filter_input(schema, 'allLibraryBooks').name}!) {{ "
        "allLibraryBooks(filter: $where) { id title } }"
    )
    with override_settings(ROOT_URLCONF="config.urls"):
        payload = graphql_payload(document, variables={"where": where})
    expected = {
        "accepted": [cross, method_only],
        "missing": [],
        "different-loan": [cross],
        "empty": [
            cross,
            method_only,
            note_only,
            bookless,
        ],
    }[case]
    assert payload == {
        "data": {
            "allLibraryBooks": [
                {"id": global_id_for(book_type, saved_pk(book)), "title": book.title}
                for book in expected
            ],
        },
    }


class _OwnCharFilter(CharFilter):
    """A consumer instance callable owns its original field name, lookup and exclusion."""

    def __init__(self, field_name: str, *, exclude: bool = False) -> None:
        super().__init__(field_name=field_name, exclude=exclude)
        self.filter = self._run

    def _run(self, qs: django_models.QuerySet[_M], value: object) -> django_models.QuerySet[_M]:
        return CharFilter.filter(self, qs, value)


class _OwnBooleanFilter(BooleanFilter):
    """The consumer callable delegates Boolean isnull handling to django-filter itself."""

    def __init__(self, field_name: str) -> None:
        super().__init__(field_name=field_name, lookup_expr="isnull")
        self.filter = self._run

    def _run(self, qs: django_models.QuerySet[_M], value: object) -> django_models.QuerySet[_M]:
        return BooleanFilter.filter(self, qs, value)


def _hide_repair(
    _cls: type[DjangoType],
    queryset: django_models.QuerySet[models.Book],
    _info: object,
    **_kwargs: object,
) -> django_models.QuerySet[models.Book]:
    return queryset.exclude(circulation_status=models.Book.CirculationStatus.REPAIR)


def _own_world() -> tuple[
    dict[str, django_models.Model],
    dict[type[django_models.Model], type[FilterSet]],
    tuple[type[DjangoType], ...],
]:
    class PatronChild(FilterSet):
        email = _OwnCharFilter("email")

        class Meta:
            model = models.Patron
            fields = []

    class BookChild(FilterSet):
        titled = _OwnCharFilter("title")
        not_titled = _OwnCharFilter("title", exclude=True)
        subtitle_missing = _OwnBooleanFilter("subtitle")

        class Meta:
            model = models.Book
            fields = []

    class LoanParent(FilterSet):
        patron = RelatedFilter(PatronChild)
        book = RelatedFilter(BookChild)

        class Meta:
            model = models.Loan
            fields = []

    class ShelfParent(FilterSet):
        books = RelatedFilter(BookChild)
        book_titled = _OwnCharFilter("books__title")

        class Meta:
            model = models.Shelf
            fields = []

    class GenreParent(FilterSet):
        books = RelatedFilter(BookChild)

        class Meta:
            model = models.Genre
            fields = []

    class PlainBookRoot(FilterSet):
        titled = _OwnCharFilter("title")

        class Meta:
            model = models.Book
            fields = []

    patron_type = make_django_type(
        "OwnedPatron",
        models.Patron,
        ("email",),
        node=False,
        meta_extra={"filterset_class": PatronChild},
    )
    book_type = make_django_type(
        "ScopedOwnedBook",
        models.Book,
        ("title",),
        node=False,
        meta_extra={"filterset_class": BookChild, "primary": True},
        namespace_extra={"get_queryset": classmethod(_hide_repair)},
    )
    branch = models.Branch.objects.create(name="Owned world")
    open_shelf = models.Shelf.objects.create(branch=branch, code="open")
    hidden_shelf = models.Shelf.objects.create(branch=branch, code="hidden")
    alone_shelf = models.Shelf.objects.create(branch=branch, code="alone")
    empty_shelf = models.Shelf.objects.create(branch=branch, code="empty")
    open_x = models.Book.objects.create(shelf=open_shelf, title="x")
    hidden_x = models.Book.objects.create(
        shelf=hidden_shelf,
        title="x",
        subtitle="s",
        circulation_status=models.Book.CirculationStatus.REPAIR,
    )
    plain = models.Book.objects.create(shelf=open_shelf, title="plain")
    models.Book.objects.create(shelf=alone_shelf, title="alone")
    open_loan = _loan(open_x, "p1@x", "open")
    hidden_loan = _loan(hidden_x, "p2@x", "hidden")
    plain_loan = _loan(plain, "p2@x", "plain")
    genres: dict[str, models.Genre] = {}
    for name, books in [
        ("open_x", [open_x]),
        ("hidden_x", [hidden_x]),
        ("mixed", [open_x, plain]),
        ("bookless", []),
    ]:
        genre = models.Genre.objects.create(name=name)
        genre.books.set(books)
        genres[name] = genre
    rows: dict[str, django_models.Model] = {
        "open-shelf": open_shelf,
        "hidden-shelf": hidden_shelf,
        "alone-shelf": alone_shelf,
        "empty-shelf": empty_shelf,
        "open-book": open_x,
        "hidden-book": hidden_x,
        "open-loan": open_loan,
        "hidden-loan": hidden_loan,
        "plain-loan": plain_loan,
        **genres,
    }
    return (
        rows,
        {
            models.Loan: LoanParent,
            models.Shelf: ShelfParent,
            models.Genre: GenreParent,
            models.Book: PlainBookRoot,
        },
        (patron_type, book_type),
    )


class _OwnCase(NamedTuple):
    """One consumer-owned invocation with an independently specified ordered result."""

    model: type[django_models.Model]
    scalar: str
    path: tuple[str, ...]
    value: object
    expected: list[tuple[str, str]]


_OWN_CASES: dict[str, _OwnCase] = {
    "child-to-one": _OwnCase(
        models.Loan,
        "note",
        ("patron_email", "exact"),
        "p1@x",
        [("open-loan", "open")],
    ),
    "child-to-one-hidden-book": _OwnCase(
        models.Loan,
        "note",
        ("book_titled", "exact"),
        "x",
        [("open-loan", "open")],
    ),
    "child-to-many": _OwnCase(
        models.Shelf,
        "code",
        ("books_titled", "exact"),
        "x",
        [("open-shelf", "open")],
    ),
    "parent-declared-beside-branch": _OwnCase(
        models.Shelf,
        "code",
        ("book_titled", "exact"),
        "x",
        [("open-shelf", "open"), ("hidden-shelf", "hidden")],
    ),
    "child-to-one-exclude": _OwnCase(
        models.Loan,
        "note",
        ("book_not_titled", "exact"),
        "x",
        [("plain-loan", "plain")],
    ),
    "child-to-many-exclude": _OwnCase(
        models.Shelf,
        "code",
        ("books_not_titled", "exact"),
        "x",
        [("open-shelf", "open"), ("alone-shelf", "alone")],
    ),
    "child-to-many-null": _OwnCase(
        models.Shelf,
        "code",
        ("books_subtitle_missing", "is_null"),
        value=True,
        expected=[
            ("open-shelf", "open"),
            ("hidden-shelf", "hidden"),
            ("alone-shelf", "alone"),
            ("empty-shelf", "empty"),
        ],
    ),
    "m2m-exclude": _OwnCase(
        models.Genre,
        "name",
        ("books_not_titled", "exact"),
        "x",
        [("mixed", "mixed")],
    ),
    "m2m-null": _OwnCase(
        models.Genre,
        "name",
        ("books_subtitle_missing", "is_null"),
        value=True,
        expected=[
            ("open_x", "open_x"),
            ("hidden_x", "hidden_x"),
            ("mixed", "mixed"),
            ("bookless", "bookless"),
        ],
    ),
    "plain-root": _OwnCase(
        models.Book,
        "title",
        ("titled", "exact"),
        "x",
        [("open-book", "x"), ("hidden-book", "x")],
    ),
}


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("private_registry")
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("case", list(_OWN_CASES))
def test_own_callable_keeps_its_owner_exclusion_and_null_extension_on_each_executor(
    case: str,
    transport: str,
) -> None:
    """Own callables keep their positive/excluding/null behavior and their owner's visibility."""
    rows, filters, targets = _own_world()
    model, scalar, leaf, value, expected = _OWN_CASES[case]
    schema, row_type = _holder(
        model,
        scalar,
        filters[model],
        targets=targets,
        primary=model is not models.Book,
    )
    payload = _post(
        schema,
        _document(schema, scalar),
        _where(schema, leaf, value),
        transport=transport,
    )
    assert payload == _expected(row_type, [(rows[key], name) for key, name in expected])


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
@pytest.mark.parametrize("name", ["named", "secret"], ids=["visible", "hidden"])
def test_projected_method_with_exclude_true_still_selects_its_positive_visible_match(
    name: str,
) -> None:
    """django-filter hands a method its value without negating it; a hidden named Genre cannot satisfy it."""

    class GenreChild(FilterSet):
        named = CharFilter(field_name="name", method="filter_named", exclude=True)

        class Meta:
            model = models.Genre
            fields = []

        def filter_named(
            self,
            queryset: django_models.QuerySet[models.Genre],
            _name: str,
            value: object,
        ) -> django_models.QuerySet[models.Genre]:
            return queryset.filter(name=value)

    class BookParent(FilterSet):
        genres = RelatedFilter(GenreChild)

        class Meta:
            model = models.Book
            fields = []

    def visible_genres(
        _cls: type[DjangoType],
        queryset: django_models.QuerySet[models.Genre],
        _info: object,
        **_kwargs: object,
    ) -> django_models.QuerySet[models.Genre]:
        return queryset.exclude(name__startswith="secret")

    target = make_django_type(
        "MethodGenre",
        models.Genre,
        ("name",),
        node=False,
        meta_extra={"filterset_class": GenreChild},
        namespace_extra={"get_queryset": classmethod(visible_genres)},
    )
    shelf = _shelf("EXCLUDE")
    visible = models.Genre.objects.create(name="named")
    hidden = models.Genre.objects.create(name="secret")
    first = models.Book.objects.create(shelf=shelf, title="Visible match")
    first.genres.add(visible)
    second = models.Book.objects.create(shelf=shelf, title="Hidden match")
    second.genres.add(hidden)
    models.Book.objects.create(shelf=shelf, title="No genre")
    schema, row_type = _holder(models.Book, "title", BookParent, targets=(target,))
    payload = _post(
        schema,
        _document(schema, "title"),
        _where(schema, ("genres_named", "exact"), name),
    )
    expected = [(first, "Visible match")] if name == "named" else []
    assert payload == _expected(row_type, expected)


class _RawOwnGlobalIDFilter(GlobalIDFilter):
    """A supported instance callable replaces decoding with raw consumer binding."""

    def __init__(self, field_name: str) -> None:
        super().__init__(field_name=field_name)
        self.filter = self._raw

    def _raw(self, qs: django_models.QuerySet[_M], value: object) -> django_models.QuerySet[_M]:
        return qs.filter(title=value)


class _DecodingOwnGlobalIDFilter(GlobalIDFilter):
    """An instance callable still receives text before it chooses to invoke the inherited decoder."""

    def __init__(self, field_name: str) -> None:
        super().__init__(field_name=field_name)
        self.filter = self._decode

    def _decode(self, qs: django_models.QuerySet[_M], value: object) -> django_models.QuerySet[_M]:
        return GlobalIDFilter.filter(self, qs, value)


class _ClassRawGlobalIDFilter(GlobalIDFilter):
    """A class override also owns its raw binding contract."""

    @override
    def filter(self, qs: django_models.QuerySet[_M], value: object) -> django_models.QuerySet[_M]:
        return qs.filter(title=value)


class _InheritedGlobalIDFilter(GlobalIDFilter):
    """The subclass inherits the real decoder without replacing it."""


def _raw_title(
    queryset: django_models.QuerySet[models.Book],
    _name: str,
    value: object,
) -> django_models.QuerySet[models.Book]:
    return queryset.filter(title=value)


def _gid_filter(kind: str) -> GlobalIDFilter:
    if kind == "method":
        return GlobalIDFilter(field_name="id", method=_raw_title)
    if kind == "own-raw":
        return _RawOwnGlobalIDFilter("id")
    if kind == "own-decoding":
        return _DecodingOwnGlobalIDFilter("id")
    if kind == "class-raw":
        return _ClassRawGlobalIDFilter(field_name="id")
    if kind == "class-inherited":
        return _InheritedGlobalIDFilter(field_name="id")
    return GlobalIDFilter(field_name="id")


_GID_REFUSALS = [
    ("root", "own-raw", "surrogate"),
    ("root", "own-raw", "nul"),
    ("root", "own-decoding", "surrogate"),
    ("root", "own-decoding", "nul"),
    ("root", "class-raw", "surrogate"),
    ("root", "class-inherited", "surrogate"),
    ("projected", "method", "surrogate"),
    ("projected", "method", "nul"),
    ("projected", "own-raw", "surrogate"),
    ("projected", "own-raw", "nul"),
    ("projected", "own-decoding", "surrogate"),
    ("projected", "own-decoding", "nul"),
    ("projected", "plain", "surrogate"),
    ("projected", "plain", "nul"),
]


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
@pytest.mark.parametrize(
    ("surface", "kind", "bad_text"),
    _GID_REFUSALS,
    ids=["-".join(case) for case in _GID_REFUSALS],
)
def test_globalid_consumer_binding_refusals_follow_the_filter_that_actually_runs(
    surface: str,
    kind: str,
    bad_text: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Own bindings refuse unstoreable text; inherited decoders retain GLOBALID_INVALID."""

    class BookChild(FilterSet):
        gid = _gid_filter(kind)

        class Meta:
            model = models.Book
            fields = []

    shelf = _shelf("GID")
    book = models.Book.objects.create(shelf=shelf, title="plain")
    expected: list[tuple[django_models.Model, str]]
    if surface == "projected":
        target = make_django_type(
            "GlobalIDChildBook",
            models.Book,
            ("id", "title"),
            meta_extra={"filterset_class": BookChild},
        )

        class ShelfParent(FilterSet):
            books = RelatedFilter(BookChild)

            class Meta:
                model = models.Shelf
                fields = []

        schema, row_type = _holder(models.Shelf, "code", ShelfParent, targets=(target,))
        scalar = "code"
        leaf = ("books_gid", "exact")
        form_key = "books__gid"
        expected = [(shelf, "GID")]
    else:
        schema, row_type = _holder(models.Book, "title", BookChild)
        target = row_type
        scalar = "title"
        leaf = ("gid", "exact")
        form_key = "gid"
        expected = [(book, "plain")]
    decoder = kind in {"own-decoding", "class-inherited", "plain"}
    accepted = global_id_for(target, saved_pk(book)) if decoder else "plain"
    sqls = record_compiled_sql()
    positive = _post(schema, _document(schema, scalar), _where(schema, leaf, accepted))
    assert positive == _expected(row_type, expected)
    boundary = len(sqls)
    value = "\ud800" if bad_text == "surrogate" else "a\x00b"
    payload = _post(schema, _document(schema, scalar), _where(schema, leaf, value))
    assert payload["data"] is None, payload
    assert len(json_list(payload, "errors")) == 1
    assert json_at(payload, "errors", 0, "path") == ["rows"]
    if kind in {"class-inherited", "plain"}:
        assert json_at(payload, "errors", 0, "extensions") == {"code": "GLOBALID_INVALID"}
        assert json_str(payload, "errors", 0, "message").startswith("Invalid GlobalID:")
    else:
        refusal = "invalid" if bad_text == "surrogate" else "null_characters_not_allowed"
        message = (
            "Text contains invalid Unicode (unpaired surrogate code points)."
            if bad_text == "surrogate"
            else "Null characters are not allowed."
        )
        assert json_at(payload, "errors", 0, "message") == "Invalid filter input"
        assert json_at(payload, "errors", 0, "extensions") == {
            "code": "FILTER_INVALID",
            "errors": {form_key: [{"message": message, "code": refusal}]},
        }
    assert _root_sql(sqls[boundary:], models.Book) == []
    assert _root_sql(sqls[boundary:], models.Shelf) == []
