"""Consumer form relation keys and projected reentry preserve their target and root universes.

Ordinary JSON reaches unbound public applicators and a consumer's direct queryset.
The Loan-to-Patron-to-Loan shape has independent hidden intermediate and terminal rows,
while authored model-choice empty values retain the roots their target types hide.
"""

import asyncio
from collections.abc import Awaitable, Mapping, Sequence
from functools import wraps

import pytest
import strawberry
from apps.library import models
from asgiref.sync import sync_to_async
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import CharFilter, ModelChoiceFilter, ModelMultipleChoiceFilter
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_object,
    response_json,
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
from django_strawberry_framework.filters import FilterSet, ListFilter, RangeFilter, RelatedFilter
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils._narrowing import (
    is_list_or_tuple,
    read_attr,
    require,
    require_instance,
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
async def _async_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-relation-form-paths/", _graphql_view),
    path("graphql-relation-form-paths-async/", _async_view),
]


def _scope(model: type[Model], **hidden: object) -> type[DjangoType]:
    def visible(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        _info: object,
    ) -> QuerySet[Model]:
        return queryset.exclude(**hidden)

    return type(
        model.__name__ + "Scope",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": model, "fields": ("id",), "primary": True}),
            "get_queryset": classmethod(visible),
        },
    )


def _schema(
    parent: type[FilterSet],
    model: type[Model],
    label: str,
    targets: Sequence[type[DjangoType]],
    *,
    direct: bool = False,
    secondary_output: bool = False,
    transport: str = "sync",
) -> DjangoSchema:
    parent.get_filters()
    output = type(
        "RootOutput",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": model, "fields": ("id", label), "primary": not secondary_output},
            ),
        },
    )

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[Model]:
        del root
        rows = model._default_manager.order_by("pk")
        if direct:
            return parent(
                data=json_object(where),
                queryset=rows,
                request=require_instance(read_attr(info.context, "request"), HttpRequest),
            ).qs
        return parent.apply_sync(where, rows, info)

    def resolve_all(root: object) -> QuerySet[Model]:
        del root
        return model._default_manager.order_by("pk")

    async def resolve_async_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> list[Model]:
        del root
        rows = await parent.apply_async(where, model._default_manager.order_by("pk"), info)
        return await sync_to_async(list)(rows)

    async def resolve_async_all(root: object) -> list[Model]:
        del root
        return await sync_to_async(list)(model._default_manager.order_by("pk"))

    @strawberry.type
    class Query:
        rows: QuerySet[Model] | Awaitable[list[Model]] = strawberry.field(
            resolver=resolve_async_rows if transport == "async" else resolve_rows,
            graphql_type=list[output],
        )
        all_rows: QuerySet[Model] | Awaitable[list[Model]] = strawberry.field(
            resolver=resolve_async_all if transport == "async" else resolve_all,
            graphql_type=list[output],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=targets,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


async def _async_post(document: str, where: JSONObject) -> JSONObject:
    response = await AsyncTestClient().query(
        document,
        {"where": where},
        url="/graphql-relation-form-paths-async/",
        assert_no_errors=False,
    )
    assert response.response.status_code == 200
    return response_json(response.response)


def _post(
    schema: DjangoSchema,
    where: JSONObject,
    label: str,
    *,
    transport: str = "sync",
) -> JSONObject:
    document = (
        f"query($where: JSON!) {{ rows(where: $where) {{ key: id label: {label} }} "
        f"allRows {{ key: id label: {label} }} }}"
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if transport == "async":
                return asyncio.run(_async_post(document, where))
            return graphql_payload(
                document,
                variables={"where": where},
                url="/graphql-relation-form-paths/",
            )
    finally:
        _CURRENT["schema"] = None


def _labels(rows: Sequence[Model], label: str) -> list[JSONObject]:
    return [
        {"key": saved_pk(row), "label": require_instance(read_attr(row, label), str)}
        for row in rows
    ]


def _expected(rows: Sequence[Model], universe: Sequence[Model], label: str) -> JSONObject:
    return {"data": {"rows": _labels(rows, label), "allRows": _labels(universe, label)}}


def _loan_world() -> tuple[list[models.Loan], list[models.Loan]]:
    branch = models.Branch.objects.create(name="Shared")
    shelf = models.Shelf.objects.create(branch=branch, code="Shared")
    seen = models.Patron.objects.create(name="seen", email="s@x")
    hidden = models.Patron.objects.create(name="hidden", email="h@x")
    open_loan = models.Loan.objects.create(
        book=models.Book.objects.create(shelf=shelf, title="Shared"),
        patron=seen,
        note="open",
    )
    secret_loan = models.Loan.objects.create(
        book=models.Book.objects.create(shelf=shelf, title="Second"),
        patron=seen,
        note="secret",
    )
    hidden_patron_loan = models.Loan.objects.create(
        book=models.Book.objects.create(shelf=shelf, title="Third"),
        patron=hidden,
        note="open",
    )
    return [open_loan, secret_loan], [open_loan, secret_loan, hidden_patron_loan]


def _loan_parent() -> type[FilterSet]:
    class LoanChild(FilterSet):
        class Meta:
            model = models.Loan
            fields = {"note": ["exact"]}

    class PatronChild(FilterSet):
        loans = RelatedFilter(LoanChild, field_name="loans")

        class Meta:
            model = models.Patron
            fields = {"name": ["exact"]}

        @override
        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

    class LoanParent(FilterSet):
        patron = RelatedFilter(PatronChild, field_name="patron")

        class Meta:
            model = models.Loan
            fields = {"note": ["exact"]}

    return LoanParent


@pytest.mark.django_db
@pytest.mark.parametrize("spelling", ["flat", "nested"])
@pytest.mark.parametrize("note", ["open", "secret"], ids=["visible-match", "hidden-match"])
def test_a_projected_childs_walked_leaf_scopes_both_hops_without_hiding_root_occurrences(
    spelling: str,
    note: str,
) -> None:
    """Loan reentry scopes target loans and patrons while keeping every matching patron's root loans."""
    seen, all_rows = _loan_world()
    schema = _schema(
        _loan_parent(),
        models.Loan,
        "note",
        (_scope(models.Patron, name="hidden"), _scope(models.Loan, note__startswith="secret")),
        secondary_output=True,
    )
    where: JSONObject = (
        {"patron__loans__note": note}
        if spelling == "flat"
        else {"patron": {"loans": {"note": note}}}
    )
    payload = _post(schema, where, "note")
    assert payload == _expected(seen if note == "open" else [], all_rows, "note"), payload


def _empty_key_world() -> tuple[list[models.Book], list[models.Genre]]:
    branch = models.Branch.objects.create(name="Shared")
    open_shelf = models.Shelf.objects.create(branch=branch, code="open", topic="open")
    secret_shelf = models.Shelf.objects.create(branch=branch, code="secret", topic="secret")
    open_book = models.Book.objects.create(shelf=open_shelf, title="open")
    secret_book = models.Book.objects.create(
        shelf=secret_shelf,
        title="secret",
        circulation_status="repair",
    )
    empty = models.Genre.objects.create(name="empty")
    mixed = models.Genre.objects.create(name="mixed")
    mixed.books.set([open_book, secret_book])
    return [open_book, secret_book], [empty, mixed]


def _forward_keys() -> type[FilterSet]:
    class ShelfChild(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    class BookParent(FilterSet):
        visible_shelf = RelatedFilter(ShelfChild, field_name="shelf")
        on_shelf = ModelChoiceFilter(field_name="shelf", queryset=models.Shelf.objects.all())
        not_on_shelf = ModelChoiceFilter(
            field_name="shelf",
            queryset=models.Shelf.objects.all(),
            exclude=True,
        )

        class Meta:
            model = models.Book
            fields = {"shelf": ["exact"]}

    return BookParent


def _many_keys() -> type[FilterSet]:
    class BookChild(FilterSet):
        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    class GenreParent(FilterSet):
        visible_books = RelatedFilter(BookChild, field_name="books")
        has_any_book = ModelMultipleChoiceFilter(
            field_name="books",
            queryset=models.Book.objects.all(),
        )

        class Meta:
            model = models.Genre
            fields = {"name": ["exact"]}

    return GenreParent


@pytest.mark.django_db
@pytest.mark.parametrize("leaf", ["on_shelf", "not_on_shelf", "has_any_book"])
def test_authored_model_choice_filters_skip_their_supplied_empty_value_without_restricting_roots(
    leaf: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Raw empty strings and an empty model-choice list preserve linked, hidden-target and empty roots."""
    books, genres = _empty_key_world()
    if leaf == "has_any_book":
        schema = _schema(
            _many_keys(),
            models.Genre,
            "name",
            (_scope(models.Book, circulation_status="repair"),),
            direct=True,
        )
        where: JSONObject = {leaf: []}
        expected = _expected(genres, genres, "name")
        label, table = "name", "library_genre"
    else:
        schema = _schema(
            _forward_keys(),
            models.Book,
            "title",
            (_scope(models.Shelf, topic="secret"),),
            direct=True,
        )
        where = {leaf: ""}
        expected = _expected(books, books, "title")
        label, table = "title", "library_book"
    statements = record_compiled_sql()
    payload = _post(schema, where, label)
    assert payload == expected, payload
    root_sql = [statement for statement in statements if f' FROM "{table}"' in statement]
    assert len(root_sql) == 2, statements
    assert all("EXISTS" not in statement.upper() for statement in root_sql), statements
    assert all(" JOIN " not in statement.upper() for statement in root_sql), statements


def _method_world() -> list[models.Branch]:
    alpha = models.Branch.objects.create(name="alpha")
    models.Shelf.objects.create(branch=alpha, code="match", topic="open")
    beta = models.Branch.objects.create(name="beta")
    models.Shelf.objects.create(branch=beta, code="other", topic="open")
    gamma = models.Branch.objects.create(name="gamma")
    models.Shelf.objects.create(branch=gamma, code="match", topic="secret")
    delta = models.Branch.objects.create(name="delta")
    return [
        alpha,
        beta,
        gamma,
        delta,
    ]


def _method_parent() -> type[FilterSet]:
    class ShelfChild(FilterSet):
        code_is = CharFilter(field_name="code", method="filter_code_is")
        code_among = ListFilter(field_name="code", lookup_expr="in", method="filter_code_among")
        code_span = RangeFilter(field_name="code", lookup_expr="range", method="filter_code_span")

        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

        def filter_code_is(
            self,
            queryset: QuerySet[models.Shelf],
            _name: str,
            value: object,
        ) -> QuerySet[models.Shelf]:
            return queryset.filter(code=value)

        def filter_code_among(
            self,
            queryset: QuerySet[models.Shelf],
            _name: str,
            value: object,
        ) -> QuerySet[models.Shelf]:
            return queryset.filter(code__in=require(value, is_list_or_tuple))

        def filter_code_span(
            self,
            queryset: QuerySet[models.Shelf],
            _name: str,
            value: object,
        ) -> QuerySet[models.Shelf]:
            lower, upper = require(value, is_list_or_tuple)
            if lower is not None:
                queryset = queryset.filter(code__gte=lower)
            if upper is not None:
                queryset = queryset.filter(code__lte=upper)
            return queryset

    class BranchParent(FilterSet):
        shelves = RelatedFilter(ShelfChild, field_name="shelves")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    return BranchParent


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    "shape",
    [
        "list",
        "range",
        "range-start",
        "range-end",
    ],
)
def test_projected_methods_receive_their_cleaned_list_and_range_values(
    shape: str,
    transport: str,
) -> None:
    """Compound methods keep the visible match and reject unrelated, hidden and empty parents."""
    roots = _method_world()
    inputs: dict[str, JSONObject] = {
        "list": {"shelves__code_among": ["match"]},
        "range": {"shelves__code_span": {"start": "m", "end": "n"}},
        "range-start": {"shelves__code_span": {"start": "n"}},
        "range-end": {"shelves__code_span": {"end": "n"}},
    }
    where = inputs[shape]
    schema = _schema(
        _method_parent(),
        models.Branch,
        "name",
        (_scope(models.Shelf, topic="secret"),),
        transport=transport,
    )
    payload = _post(schema, where, "name", transport=transport)
    selected = roots[1] if shape == "range-start" else roots[0]
    assert payload == _expected([selected], roots, "name"), payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_not_arm_negates_the_projected_method_at_its_parent(transport: str) -> None:
    """Negating the match keeps unrelated, hidden-only and empty parents without negating the child body."""
    roots = _method_world()
    schema = _schema(
        _method_parent(),
        models.Branch,
        "name",
        (_scope(models.Shelf, topic="secret"),),
        transport=transport,
    )
    payload = _post(
        schema,
        {"not_": {"shelves__code_is": "match"}},
        "name",
        transport=transport,
    )
    assert payload == _expected(roots[1:], roots, "name"), payload


def _deep_range_world() -> list[models.Branch]:
    roots = _method_world()
    alpha, beta, gamma, _delta = roots
    for branch, fines in ((alpha, 7), (beta, 2), (gamma, 7)):
        book = models.Book.objects.create(title=branch.name, shelf=branch.shelves.get())
        patron = models.Patron.objects.create(
            name=branch.name,
            email=branch.name + "@x",
            lifetime_fines_cents=fines,
        )
        models.Loan.objects.create(book=book, patron=patron, note=branch.name)
    epsilon = models.Branch.objects.create(name="epsilon")
    shelf = models.Shelf.objects.create(branch=epsilon, code="open", topic="open")
    hidden = models.Patron.objects.create(name="hidden", email="hidden@x", lifetime_fines_cents=7)
    models.Loan.objects.create(
        book=models.Book.objects.create(title="hidden-patron", shelf=shelf),
        patron=hidden,
        note="hidden-patron",
    )
    return [*roots, epsilon]


def _deep_range_parent() -> type[FilterSet]:
    class PatronChild(FilterSet):
        fines_span = RangeFilter(
            field_name="lifetime_fines_cents",
            lookup_expr="range",
            method="filter_fines_span",
        )

        class Meta:
            model = models.Patron
            fields = {"name": ["exact"]}

        def filter_fines_span(
            self,
            queryset: QuerySet[models.Patron],
            _name: str,
            value: object,
        ) -> QuerySet[models.Patron]:
            bounds = tuple(require(value, is_list_or_tuple))
            return queryset.filter(lifetime_fines_cents__range=bounds)

    class LoanMid(FilterSet):
        patron = RelatedFilter(PatronChild, field_name="patron")

        class Meta:
            model = models.Loan
            fields = {"note": ["exact"]}

    class BookMid(FilterSet):
        loans = RelatedFilter(LoanMid, field_name="loans")

        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    class ShelfMid(FilterSet):
        books = RelatedFilter(BookMid, field_name="books")

        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    class BranchTop(FilterSet):
        shelves = RelatedFilter(ShelfMid, field_name="shelves")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    return BranchTop


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("spelling", ["flat", "nested", "nested-prefix"])
def test_four_hop_projected_ranges_keep_their_terminal_bounds_and_visible_path(
    spelling: str,
    transport: str,
) -> None:
    """The four-hop range excludes a nonmatching fine, an empty root and independently hidden targets."""
    roots = _deep_range_world()
    bounds: JSONObject = {"start": 5, "end": 9}
    where: JSONObject
    if spelling == "flat":
        where = {"shelves__books__loans__patron__fines_span": bounds}
    elif spelling == "nested-prefix":
        where = {"shelves": {"books__loans__patron__fines_span": bounds}}
    else:
        where = {"shelves": {"books": {"loans": {"patron": {"fines_span": bounds}}}}}
    schema = _schema(
        _deep_range_parent(),
        models.Branch,
        "name",
        (
            _scope(models.Shelf, topic="secret"),
            _scope(models.Book),
            _scope(models.Loan),
            _scope(models.Patron, name="hidden"),
        ),
        transport=transport,
    )
    payload = _post(schema, where, "name", transport=transport)
    assert payload == _expected([roots[0]], roots, "name"), payload
