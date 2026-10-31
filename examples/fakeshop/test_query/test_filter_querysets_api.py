"""Live HTTP filters preserve consumer row occurrences and paginate generated deep loan predicates."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from functools import wraps
from typing import TYPE_CHECKING, TypeVar

import pytest
import strawberry
from apps.library import models
from django.db import connection
from django.db import models as django_models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase, QueryDict
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django_filters import CharFilter, Filter, ModelMultipleChoiceFilter
from graphql_client import JSONObject, graphql_payload, json_list, json_object, json_str
from strawberry import relay
from strawberry.django.context import StrawberryDjangoContext
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

if TYPE_CHECKING:
    from django_strawberry_framework.utils.typing import ModelField

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-filter-querysets/", _graphql_view)]


def _post(
    schema: DjangoSchema,
    query: str,
    *,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(query, variables=variables, url="/graphql-filter-querysets/")
    finally:
        _CURRENT["schema"] = None


def _named_type(description: object) -> tuple[str, str]:
    current = json_object(description)
    while current["name"] is None:
        current = json_object(current, "ofType")
    return json_str(current, "name"), json_str(current, "kind")


def _inputs(schema: DjangoSchema, type_name: str) -> list[object]:
    described = _post(
        schema,
        """
        query($name: String!) {
          __type(name: $name) {
            inputFields {
              name
              type {
                kind name
                ofType {
                  kind name
                  ofType {
                    kind name
                    ofType { kind name }
                  }
                }
              }
            }
          }
        }
        """,
        variables={"name": type_name},
    )
    assert set(described) == {"data"}, described
    return json_list(described, "data", "__type", "inputFields")


def _arguments(schema: DjangoSchema, root: str) -> tuple[str, str, str, str]:
    """Ask the served schema for its filter bag, operator and ordering field spellings."""
    described = _post(
        schema,
        """
        { __schema { queryType { fields {
          name args { name type { kind name ofType { kind name ofType { kind name } } } }
        } } } }
        """,
    )
    assert set(described) == {"data"}, described
    field = next(
        entry
        for entry in json_list(described, "data", "__schema", "queryType", "fields")
        if json_str(entry, "name") == root
    )
    args = {json_str(arg, "name"): json_object(arg, "type") for arg in json_list(field, "args")}
    filter_name, _kind = _named_type(args["filter"])
    order_name, _kind = _named_type(args["orderBy"])
    (order_field,) = _inputs(schema, order_name)
    bags: list[tuple[str, str]] = []
    for candidate in _inputs(schema, filter_name):
        candidate_type, kind = _named_type(json_object(candidate, "type"))
        if kind != "INPUT_OBJECT":
            continue
        members = _inputs(schema, candidate_type)
        if len(members) != 1:
            continue
        (operator,) = members
        if _named_type(json_object(operator, "type"))[1] == "SCALAR":
            bags.append((json_str(candidate, "name"), json_str(operator, "name")))
    ((leaf, operator),) = bags
    return filter_name, leaf, operator, json_str(order_field, "name")


def _root_sql(captured: CaptureQueriesContext, table: str) -> list[str]:
    quoted = connection.ops.quote_name(table)
    return [row["sql"] for row in captured.captured_queries if f"FROM {quoted}" in row["sql"]]


def _page_sql(captured: CaptureQueriesContext, table: str) -> str:
    statements = _root_sql(captured, table)
    assert len(statements) == 2, statements
    counts = [sql for sql in statements if "COUNT(" in sql.upper()]
    pages = [sql for sql in statements if "COUNT(" not in sql.upper()]
    assert len(counts) == len(pages) == 1, statements
    return pages[0]


def _multiset_world() -> tuple[models.Book, models.Book, models.Book]:
    branch = models.Branch.objects.create(name="Multiset branch")
    shelf = models.Shelf.objects.create(branch=branch, code="MULTI-1")
    double = models.Book.objects.create(
        shelf=shelf,
        title="Two matching genres",
        circulation_status=models.Book.CirculationStatus.REPAIR,
    )
    single = models.Book.objects.create(shelf=shelf, title="One matching genre")
    other = models.Book.objects.create(shelf=shelf, title="Nonmatching genre")
    double.genres.add(
        models.Genre.objects.create(name="cardiology"),
        models.Genre.objects.create(name="cardio-thoracic"),
    )
    single.genres.add(models.Genre.objects.create(name="cardio-vascular"))
    other.genres.add(models.Genre.objects.create(name="neurology"))
    return double, single, other


def _book_schema(shape: str, source: str) -> tuple[DjangoSchema, type[DjangoType]]:
    class GenreNameFilter(FilterSet):
        class Meta:
            model = models.Genre
            fields = {"name": ["icontains"]}

    class RoutedBookFilter(FilterSet):
        class Meta:
            model = models.Book
            fields = {"genres__name": ["icontains"]}

    class DeclaredBookFilter(FilterSet):
        genres = RelatedFilter(GenreNameFilter, field_name="genres")

        class Meta:
            model = models.Book
            fields = []

    class ConsumerFanFilter(FilterSet):
        genres_fan = CharFilter(
            field_name="genres__name",
            lookup_expr="icontains",
            distinct=False,
        )

        class Meta:
            model = models.Book
            fields = []

    class BookOrder(OrderSet):
        class Meta:
            model = models.Book
            fields = ["id"]

    class GenreNode(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("id", "name")

    assert registry.get(models.Genre) is GenreNode
    selected_filter = RoutedBookFilter if shape == "direct" else DeclaredBookFilter

    class BookNode(DjangoType):
        class Meta:
            model = models.Book
            fields = ("id", "title")
            interfaces = (relay.Node,)
            filterset_class = selected_filter
            orderset_class = BookOrder
            connection = {"total_count": True}

    def book_source(
        _root: object,
        info: strawberry.Info[StrawberryDjangoContext, object],
    ) -> QuerySet[models.Book]:
        rows = models.Book.objects.order_by("id")
        if source == "plain":
            return rows
        if source == "custom-filter":
            ConsumerFanFilter.get_filters()
            return ConsumerFanFilter(
                data={"genres_fan": "cardio"},
                queryset=rows,
                request=info.context.request,
            ).qs
        fanned = rows.filter(genres__name__icontains="o")
        return fanned.distinct() if source == "consumer-distinct" else fanned

    finalize_django_types()

    @strawberry.type
    class Query:
        books = DjangoConnectionField(BookNode, resolver=book_source)

    return DjangoSchema(query=Query), BookNode


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["direct", "declared"])
@pytest.mark.parametrize(
    "source",
    [
        "plain",
        "prefanned",
        "consumer-distinct",
        "custom-filter",
    ],
)
def test_a_framework_predicate_preserves_the_consumers_matching_row_occurrences(
    shape: str,
    source: str,
) -> None:
    """Matching occurrences survive once each, including consumer duplicates and explicit distinct."""
    double, single, _other = _multiset_world()
    schema, book_type = _book_schema(shape, source)
    input_name, leaf, operator, order = _arguments(schema, "books")
    query = (
        f"query($filter: {input_name}!) {{ books(first: 20, filter: $filter, "
        f"orderBy: [{{ {order}: ASC }}]) {{ totalCount edges {{ node {{ id title }} }} }} }}"
    )
    expected = (
        [double, double, single] if source in {"prefanned", "custom-filter"} else [double, single]
    )
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, query, variables={"filter": {leaf: {operator: "cardio"}}})
    assert payload == {
        "data": {
            "books": {
                "totalCount": len(expected),
                "edges": [
                    {
                        "node": {
                            "id": global_id_for(book_type, saved_pk(book), schema=schema),
                            "title": book.title,
                        },
                    }
                    for book in expected
                ],
            },
        },
    }
    page = _page_sql(captured, "library_book")
    upper = page.upper()
    outer = upper.split(" WHERE ", 1)[0]
    # A declared M2M hop tests the linking rows and the visible matching genre separately.
    assert upper.count("EXISTS") == (1 if shape == "direct" else 2), page
    assert '"LIBRARY_BOOK"."ID" ASC' in upper, page
    assert outer.startswith("SELECT DISTINCT") is (source == "consumer-distinct"), page
    if source == "plain":
        assert " JOIN " not in outer, page
    else:
        assert outer.count('JOIN "LIBRARY_BOOK_GENRES"') == 1, page
        assert outer.count('JOIN "LIBRARY_GENRE"') == 1, page
    if source != "consumer-distinct":
        assert all("DISTINCT" not in sql.upper() for sql in _root_sql(captured, "library_book"))


def _loan_world() -> tuple[models.Loan, models.Loan]:
    branch = models.Branch.objects.create(name="Deep predicate branch")
    shelf = models.Shelf.objects.create(branch=branch, code="DEEP-1")
    shared = models.Book.objects.create(
        shelf=shelf,
        title="Shared manual",
        circulation_status=models.Book.CirculationStatus.REPAIR,
    )
    direct_book = models.Book.objects.create(shelf=shelf, title="Direct-only manual")
    unrelated_book = models.Book.objects.create(shelf=shelf, title="Unrelated manual")
    first = models.Loan.objects.create(
        book=shared,
        patron=models.Patron.objects.create(name="A", email="cardio-a@example.test"),
        note="Cardio direct",
    )
    second = models.Loan.objects.create(
        book=shared,
        patron=models.Patron.objects.create(name="B", email="cardio-b@example.test"),
        note="Relation-only",
    )
    models.Loan.objects.create(
        book=direct_book,
        patron=models.Patron.objects.create(name="C", email="neuro@example.test"),
        note="Cardio direct",
    )
    models.Loan.objects.create(
        book=unrelated_book,
        patron=models.Patron.objects.create(name="D", email="ortho@example.test"),
        note="Unrelated",
    )
    return first, second


def _loan_schema() -> tuple[DjangoSchema, type[DjangoType]]:
    class DeepLoanFilter(FilterSet):
        class Meta:
            model = models.Loan
            fields = {"book__loans__patron__email": ["icontains"]}

    class LoanOrder(OrderSet):
        class Meta:
            model = models.Loan
            fields = ["id"]

    class LoanNode(DjangoType):
        class Meta:
            model = models.Loan
            fields = ("id", "note")
            interfaces = (relay.Node,)
            filterset_class = DeepLoanFilter
            orderset_class = LoanOrder
            connection = {"total_count": True}

    def loan_source(_root: object, _info: object) -> QuerySet[models.Loan]:
        return models.Loan.objects.order_by("id")

    finalize_django_types()

    @strawberry.type
    class Query:
        loans = DjangoConnectionField(LoanNode, resolver=loan_source)

    return DjangoSchema(query=Query), LoanNode


def _assert_deep_sql(captured: CaptureQueriesContext, *, offset: bool = False) -> None:
    page = _page_sql(captured, "library_loan")
    upper = page.upper()
    outer = upper.split(" WHERE ", 1)[0]
    assert " JOIN " not in outer, page
    assert upper.count("EXISTS") == 1, page
    assert upper.count('"LIBRARY_LOAN"') >= 2, page
    assert '"LIBRARY_PATRON"' in upper, page
    assert '"LIBRARY_LOAN"."ID" ASC' in upper, page
    assert all("DISTINCT" not in sql.upper() for sql in _root_sql(captured, "library_loan"))
    if offset:
        assert "LIMIT 2 OFFSET 1" in upper, page


@pytest.mark.django_db
def test_a_generated_deep_loan_predicate_keeps_each_matching_root_once() -> None:
    """One generated deep predicate keeps both shared-book loans and excludes direct-only matches."""
    first, second = _loan_world()
    schema, loan_type = _loan_schema()
    input_name, leaf, operator, order = _arguments(schema, "loans")
    query = (
        f"query($filter: {input_name}!) {{ loans(first: 20, filter: $filter, "
        f"orderBy: [{{ {order}: ASC }}]) {{ totalCount edges {{ node {{ id note }} }} }} }}"
    )
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, query, variables={"filter": {leaf: {operator: "Cardio"}}})
    assert payload == {
        "data": {
            "loans": {
                "totalCount": 2,
                "edges": [
                    {
                        "node": {
                            "id": global_id_for(loan_type, saved_pk(loan), schema=schema),
                            "note": loan.note,
                        },
                    }
                    for loan in (first, second)
                ],
            },
        },
    }
    _assert_deep_sql(captured)


@pytest.mark.django_db
def test_a_generated_deep_loan_connection_pages_by_minted_cursors_without_repeating_roots() -> (
    None
):
    """A generated deep predicate serves two one-edge pages with the same full-set count."""
    first, second = _loan_world()
    schema, loan_type = _loan_schema()
    input_name, leaf, operator, order = _arguments(schema, "loans")
    query = (
        f"query($filter: {input_name}!, $after: String) {{ "
        f"loans(first: 1, after: $after, filter: $filter, orderBy: [{{ {order}: ASC }}]) {{ "
        "totalCount edges { node { id note } } "
        "pageInfo { hasNextPage hasPreviousPage endCursor } } }"
    )
    variables: dict[str, object] = {"filter": {leaf: {operator: "Cardio"}}}
    with CaptureQueriesContext(connection) as first_sql:
        first_response = _post(schema, query, variables=variables)
    cursor = json_str(first_response, "data", "loans", "pageInfo", "endCursor")
    assert cursor
    assert first_response == {
        "data": {
            "loans": {
                "totalCount": 2,
                "edges": [
                    {
                        "node": {
                            "id": global_id_for(loan_type, saved_pk(first), schema=schema),
                            "note": first.note,
                        },
                    },
                ],
                "pageInfo": {"hasNextPage": True, "hasPreviousPage": False, "endCursor": cursor},
            },
        },
    }
    _assert_deep_sql(first_sql)
    variables["after"] = cursor
    with CaptureQueriesContext(connection) as second_sql:
        second_response = _post(schema, query, variables=variables)
    next_cursor = json_str(second_response, "data", "loans", "pageInfo", "endCursor")
    assert next_cursor
    assert next_cursor != cursor
    assert second_response == {
        "data": {
            "loans": {
                "totalCount": 2,
                "edges": [
                    {
                        "node": {
                            "id": global_id_for(loan_type, saved_pk(second), schema=schema),
                            "note": second.note,
                        },
                    },
                ],
                "pageInfo": {
                    "hasNextPage": False,
                    "hasPreviousPage": True,
                    "endCursor": next_cursor,
                },
            },
        },
    }
    _assert_deep_sql(second_sql, offset=True)


_ConsumerModel = TypeVar("_ConsumerModel", bound=django_models.Model)


def _consumer_world() -> tuple[
    models.Book,
    models.Book,
    models.Book,
    models.Book,
    models.Genre,
    models.Genre,
]:
    """Both requested keys have an exclusive root, a shared root and an unrelated contrast."""
    branch = models.Branch.objects.create(name="Consumer fallback")
    shelf = models.Shelf.objects.create(branch=branch, code="CONSUMER-1")
    first = models.Book.objects.create(shelf=shelf, title="A First only")
    second = models.Book.objects.create(shelf=shelf, title="B Second only")
    both = models.Book.objects.create(shelf=shelf, title="C Both")
    neither = models.Book.objects.create(shelf=shelf, title="D Neither")
    genre_a = models.Genre.objects.create(name="A")
    genre_b = models.Genre.objects.create(name="B")
    genre_c = models.Genre.objects.create(name="C")
    first.genres.add(genre_a)
    second.genres.add(genre_b)
    both.genres.add(genre_a, genre_b)
    neither.genres.add(genre_c)
    for index, (book, note) in enumerate(
        (
            (first, "Cardio first"),
            (second, "Cardio second"),
            (both, "Cardio both A"),
            (both, "Cardio both B"),
            (neither, "routine"),
        ),
        start=1,
    ):
        patron = models.Patron.objects.create(
            name=f"Consumer borrower {index}",
            email=f"consumer-borrower-{index}@example.test",
        )
        models.Loan.objects.create(book=book, patron=patron, note=note)
    return first, second, both, neither, genre_a, genre_b


def _consumer_schema(mode: str) -> tuple[DjangoSchema, type[DjangoType]]:
    """Native filtering preserves the actual consumer declaration's input, rowset and ordering."""

    class ConsumerGenreNode(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class ConsumerRelationFilter(ModelMultipleChoiceFilter):
        """An ordinary consumer class whose upstream model-choice cleaning keeps raw keys."""

    def genre_extra(_field: ModelField) -> dict[str, object]:
        return {"queryset": models.Genre.objects.all()}

    class MetaRelationOverride(FilterSet):
        class Meta:
            model = models.Book
            fields = {"genres": ["exact"]}
            filter_overrides = {
                django_models.ManyToManyField: {
                    "filter_class": ConsumerRelationFilter,
                    "extra": genre_extra,
                },
            }

    class DefaultExtraOverride(FilterSet):
        FILTER_DEFAULTS = {
            **FilterSet.FILTER_DEFAULTS,
            django_models.ManyToManyField: {
                **FilterSet.FILTER_DEFAULTS[django_models.ManyToManyField],
                "extra": genre_extra,
            },
        }

        class Meta:
            model = models.Book
            fields = {"genres": ["exact"]}

    def restricted_genre_extra(_field: ModelField) -> dict[str, object]:
        return {"queryset": models.Genre.objects.filter(name="A"), "required": True}

    class RestrictedMetaOverride(FilterSet):
        class Meta:
            model = models.Book
            fields = {"genres": ["exact"]}
            filter_overrides = {
                django_models.ManyToManyField: {
                    "filter_class": ModelMultipleChoiceFilter,
                    "extra": restricted_genre_extra,
                },
            }

    class RestrictedDefaultsOverride(FilterSet):
        FILTER_DEFAULTS = {
            **FilterSet.FILTER_DEFAULTS,
            django_models.ManyToManyField: {
                **FilterSet.FILTER_DEFAULTS[django_models.ManyToManyField],
                "extra": restricted_genre_extra,
            },
        }

        class Meta:
            model = models.Book
            fields = {"genres": ["exact"]}

    class ConsumerDistinctCharFilter(CharFilter):
        """A supported inherited filter body with consumer-owned DISTINCT."""

    class SourceLoanFilter(FilterSet):
        class Meta:
            model = models.Book
            fields = {"loans__note": ["icontains"]}

    SourceLoanFilter.get_filters()

    class BorrowedDirectFilter(FilterSet):
        loans__note__icontains = SourceLoanFilter.base_filters["loans__note__icontains"]

        class Meta:
            model = models.Book
            fields = []

    class BorrowedCopyFilter(FilterSet):
        loans__note__icontains = copy.deepcopy(
            SourceLoanFilter.base_filters["loans__note__icontains"],
        )

        class Meta:
            model = models.Book
            fields = []

    class DeclaredStockDistinctFilter(FilterSet):
        loan_note = CharFilter(
            field_name="loans__note",
            lookup_expr="icontains",
            distinct=True,
        )

        class Meta:
            model = models.Book
            fields = []

    class DeclaredDistinctFilter(FilterSet):
        loan_note = ConsumerDistinctCharFilter(
            field_name="loans__note",
            lookup_expr="icontains",
            distinct=True,
        )

        class Meta:
            model = models.Book
            fields = []

    class MethodDistinctFilter(FilterSet):
        loan_note = CharFilter(method="filter_note")

        class Meta:
            model = models.Book
            fields = []

        def filter_note(
            self,
            queryset: QuerySet[models.Book],
            _name: str,
            value: object,
        ) -> QuerySet[models.Book]:
            return queryset.filter(loans__note__icontains=value).distinct()

    def fanout_extra(_field: ModelField) -> dict[str, object]:
        return {"lookup_expr": "icontains"}

    class OverrideFanoutFilter(FilterSet):
        class Meta:
            model = models.Book
            fields = {"loans__note": ["icontains"]}
            filter_overrides = {
                django_models.TextField: {"filter_class": CharFilter, "extra": fanout_extra},
            }

    class ExcludeAtGeneration(FilterSet):
        class Meta:
            model = models.Book
            fields = {"loans__note": ["icontains"]}

        @classmethod
        @override
        def filter_for_field(
            cls,
            field: ModelField,
            field_name: str,
            lookup_expr: str | None = None,
        ) -> Filter | None:
            leaf = super().filter_for_field(field, field_name, lookup_expr)
            if leaf is not None:
                leaf.exclude = True
            return leaf

    class TitleAtInit(FilterSet):
        class Meta:
            model = models.Book
            fields = {"genres__name": ["icontains"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)
            self.filters["genres__name__icontains"] = CharFilter(
                field_name="title",
                lookup_expr="icontains",
            )

    class NoOpInitFilter(FilterSet):
        class Meta:
            model = models.Book
            fields = {"loans__note": ["icontains"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

    class CopiedDefaultsFilter(FilterSet):
        FILTER_DEFAULTS = dict(FilterSet.FILTER_DEFAULTS)

        class Meta:
            model = models.Book
            fields = {"loans__note": ["icontains"]}

    class ParentGeneratedCharFilter(CharFilter):
        """A consumer-owned scalar class returned by the parent's own lookup factory."""

    class ParentLookupFilter(FilterSet):
        class Meta:
            model = models.Book
            fields = {"loans__note": ["icontains"]}

        @classmethod
        @override
        def filter_for_lookup(
            cls,
            field: ModelField,
            lookup_type: str,
        ) -> tuple[type[Filter] | None, dict[str, object]]:
            _default_class, params = super().filter_for_lookup(field, lookup_type)
            return ParentGeneratedCharFilter, params

    class ConsumerGeneratedCharFilter(CharFilter):
        """A consumer-generated child filter keeps its inherited input and filter body."""

    class CustomLoanFilter(FilterSet):
        class Meta:
            model = models.Loan
            fields = {"note": ["icontains"]}

        @classmethod
        @override
        def filter_for_lookup(
            cls,
            field: ModelField,
            lookup_type: str,
        ) -> tuple[type[Filter] | None, dict[str, object]]:
            _default_class, params = super().filter_for_lookup(field, lookup_type)
            return ConsumerGeneratedCharFilter, params

    class CustomChildBookFilter(FilterSet):
        loans = RelatedFilter(CustomLoanFilter, field_name="loans")

        class Meta:
            model = models.Book
            fields = []

    class ConsumerOrderingCharFilter(CharFilter):
        @override
        def filter(self, qs: QuerySet[_ConsumerModel], value: object) -> QuerySet[_ConsumerModel]:
            return qs.order_by("-title")

    class ConsumerOrderingFilter(FilterSet):
        class Meta:
            model = models.Book
            fields = {"loans__note": ["icontains"]}
            filter_overrides = {
                django_models.TextField: {"filter_class": ConsumerOrderingCharFilter},
            }

    selected_filter = {
        "raw-model-choice-meta-override": MetaRelationOverride,
        "raw-model-choice-default-extra": DefaultExtraOverride,
        "restricted-meta-extra": RestrictedMetaOverride,
        "restricted-default-extra": RestrictedDefaultsOverride,
        "borrowed-direct": BorrowedDirectFilter,
        "borrowed-deepcopy": BorrowedCopyFilter,
        "declared-stock-distinct": DeclaredStockDistinctFilter,
        "declared-distinct-subclass": DeclaredDistinctFilter,
        "owned-method-distinct": MethodDistinctFilter,
        "override-generated-fanout": OverrideFanoutFilter,
        "exclude-at-generation": ExcludeAtGeneration,
        "title-at-init": TitleAtInit,
        "generated-custom-child": CustomChildBookFilter,
        "consumer-ordering": ConsumerOrderingFilter,
        "no-op-init": NoOpInitFilter,
        "copied-defaults": CopiedDefaultsFilter,
        "parent-lookup-class": ParentLookupFilter,
    }[mode]

    class ConsumerLoanNode(DjangoType):
        class Meta:
            model = models.Loan
            fields = ("note",)
            filterset_class = CustomLoanFilter

    class ConsumerBookOrder(OrderSet):
        class Meta:
            model = models.Book
            fields = ["id"]

    class ConsumerBookNode(DjangoType):
        class Meta:
            model = models.Book
            fields = ("id", "title")
            interfaces = (relay.Node,)
            filterset_class = selected_filter
            orderset_class = ConsumerBookOrder
            connection = {"total_count": True}

    def book_source(_root: object, _info: object) -> QuerySet[models.Book]:
        queryset = models.Book.objects.order_by("pk")
        if mode in ("no-op-init", "copied-defaults", "parent-lookup-class"):
            return queryset.filter(loans__note__icontains="cardio")
        return queryset

    finalize_django_types()

    @strawberry.type
    class Query:
        books = DjangoConnectionField(ConsumerBookNode, resolver=book_source)

    return (
        DjangoSchema(query=Query, types=[ConsumerGenreNode, ConsumerLoanNode]),
        ConsumerBookNode,
    )


def _consumer_request(schema: DjangoSchema, value: object) -> tuple[str, JSONObject]:
    input_name, leaf, operator, _order = _arguments(schema, "books")
    document = (
        f"query($filter: {input_name}!) {{ books(first: 20, filter: $filter) {{ "
        "totalCount edges { node { id title } } } }"
    )
    return document, {leaf: {operator: value}}


def _consumer_expected(
    schema: DjangoSchema,
    book_type: type[DjangoType],
    rows: Sequence[models.Book],
) -> JSONObject:
    return {
        "data": {
            "books": {
                "totalCount": len(rows),
                "edges": [
                    {
                        "node": {
                            "id": global_id_for(book_type, saved_pk(book), schema=schema),
                            "title": book.title,
                        },
                    }
                    for book in rows
                ],
            },
        },
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mode",
    ["raw-model-choice-meta-override", "raw-model-choice-default-extra"],
)
def test_consumer_relation_overrides_keep_their_model_choice_input(mode: str) -> None:
    """Two real raw keys retain first-only, second-only and shared roots exactly once."""
    first, second, both, _neither, genre_a, genre_b = _consumer_world()
    schema, book_type = _consumer_schema(mode)
    document, where = _consumer_request(schema, [saved_pk(genre_a), saved_pk(genre_b)])
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, document, variables={"filter": where})
    assert payload == _consumer_expected(schema, book_type, [first, second, both]), payload
    page = _page_sql(captured, "library_book")
    outer = page.upper().split(" WHERE ", 1)[0]
    assert outer.startswith("SELECT DISTINCT"), page
    assert 'JOIN "LIBRARY_BOOK_GENRES"' in outer, page
    assert "EXISTS" not in page.upper(), page


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mode",
    [
        "borrowed-direct",
        "borrowed-deepcopy",
        "declared-stock-distinct",
        "declared-distinct-subclass",
        "owned-method-distinct",
        "override-generated-fanout",
    ],
)
def test_consumer_filters_keep_their_owned_distinct_and_occurrences(mode: str) -> None:
    """Authored DISTINCT and a method's DISTINCT keep roots once; an authored fanout keeps both copies."""
    first, second, both, _neither, _genre_a, _genre_b = _consumer_world()
    schema, book_type = _consumer_schema(mode)
    document, where = _consumer_request(schema, "cardio")
    expected = (
        [
            first,
            second,
            both,
            both,
        ]
        if mode == "override-generated-fanout"
        else [first, second, both]
    )
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, document, variables={"filter": where})
    assert payload == _consumer_expected(schema, book_type, expected), payload
    page = _page_sql(captured, "library_book")
    outer = page.upper().split(" WHERE ", 1)[0]
    assert outer.startswith("SELECT DISTINCT") is (mode != "override-generated-fanout"), page
    assert 'JOIN "LIBRARY_LOAN"' in outer, page
    assert "EXISTS" not in page.upper(), page


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["exclude-at-generation", "title-at-init"])
def test_consumer_generation_hooks_keep_their_live_filter_semantics(mode: str) -> None:
    """Generation-time exclusion and per-instance replacement retain their real outer invocation."""
    if mode == "exclude-at-generation":
        _first, _second, _both, neither, _genre_a, _genre_b = _consumer_world()
        expected = [neither]
    else:
        branch = models.Branch.objects.create(name="Instance replacement")
        shelf = models.Shelf.objects.create(branch=branch, code="REPLACED-1")
        by_title = models.Book.objects.create(shelf=shelf, title="Cardiology Handbook")
        by_genre = models.Book.objects.create(shelf=shelf, title="Neurology Atlas")
        by_genre.genres.add(models.Genre.objects.create(name="cardio-club"))
        expected = [by_title]
    schema, book_type = _consumer_schema(mode)
    document, where = _consumer_request(schema, "cardio")
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, document, variables={"filter": where})
    assert payload == _consumer_expected(schema, book_type, expected), payload
    page = _page_sql(captured, "library_book")
    upper = page.upper()
    outer = upper.split(" WHERE ", 1)[0]
    assert not outer.startswith("SELECT DISTINCT"), page
    assert " JOIN " not in outer, page
    if mode == "exclude-at-generation":
        # Django owns the negative relation predicate. A second, positive outer
        # EXISTS would be the declined generated rewrite wrapped around that body.
        assert upper.count("EXISTS") == 1, page
        assert "NOT (EXISTS" in upper, page
        assert '"LIBRARY_LOAN"' in upper, page
    else:
        assert "EXISTS" not in upper, page
        assert '"LIBRARY_BOOK"."TITLE"' in upper, page
        assert '"LIBRARY_GENRE"' not in upper, page


@pytest.mark.django_db
def test_custom_generated_child_filter_keeps_the_declared_branch_rowset() -> None:
    """A real custom generated child class matches all three parents once through its declared branch."""
    first, second, both, _neither, _genre_a, _genre_b = _consumer_world()
    schema, book_type = _consumer_schema("generated-custom-child")
    document, where = _consumer_request(schema, "cardio")
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, document, variables={"filter": where})
    assert payload == _consumer_expected(schema, book_type, [first, second, both]), payload
    page = _page_sql(captured, "library_book")
    outer = page.upper().split(" WHERE ", 1)[0]
    assert " JOIN " not in outer, page
    assert "EXISTS" in page.upper(), page
    assert "DISTINCT" not in page.upper(), page


@pytest.mark.django_db
def test_consumer_filter_ordering_survives_native_connection_completion() -> None:
    """A filter which owns descending title order returns every root in the reverse of PK order."""
    first, second, both, neither, _genre_a, _genre_b = _consumer_world()
    schema, book_type = _consumer_schema("consumer-ordering")
    document, where = _consumer_request(schema, "cardio")
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, document, variables={"filter": where})
    assert payload == _consumer_expected(
        schema,
        book_type,
        [
            neither,
            both,
            second,
            first,
        ],
    ), payload
    page = _page_sql(captured, "library_book")
    assert '"LIBRARY_BOOK"."TITLE" DESC' in page.upper(), page
    assert "EXISTS" not in page.upper(), page


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["no-op-init", "copied-defaults", "parent-lookup-class"])
def test_parent_generation_seams_keep_their_outer_join_and_authored_occurrences(mode: str) -> None:
    """Even a no-op constructor or same-content table keeps its actual upstream outer invocation."""
    first, second, both, _neither, _genre_a, _genre_b = _consumer_world()
    schema, book_type = _consumer_schema(mode)
    document, where = _consumer_request(schema, "cardio")
    expected = (
        [
            first,
            second,
            both,
            both,
            both,
            both,
        ]
        if mode == "parent-lookup-class"
        else [first, second, both]
    )
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, document, variables={"filter": where})
    assert payload == _consumer_expected(schema, book_type, expected), payload
    page = _page_sql(captured, "library_book")
    upper = page.upper()
    outer = upper.split(" WHERE ", 1)[0]
    assert 'JOIN "LIBRARY_LOAN"' in outer, page
    assert outer.startswith("SELECT DISTINCT") is (mode != "parent-lookup-class"), page
    assert "EXISTS" not in upper, page


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["restricted-meta-extra", "restricted-default-extra"])
def test_consumer_relation_extra_keeps_its_allowed_model_choice_rows(mode: str) -> None:
    """A stock-class override keeps its restricted raw-key choice beside a Relay target."""
    first, _second, both, _neither, allowed, _blocked = _consumer_world()
    schema, book_type = _consumer_schema(mode)
    document, where = _consumer_request(schema, [saved_pk(allowed)])

    payload = _post(schema, document, variables={"filter": where})

    assert payload == _consumer_expected(schema, book_type, [first, both]), payload


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["restricted-meta-extra", "restricted-default-extra"])
def test_consumer_relation_extra_refuses_a_saved_key_outside_its_queryset(mode: str) -> None:
    """A real related Genre outside the consumer queryset fails model-choice validation."""
    _first, _second, _both, _neither, _allowed, blocked = _consumer_world()
    schema, _book_type = _consumer_schema(mode)
    document, where = _consumer_request(schema, [saved_pk(blocked)])

    payload = _post(schema, document, variables={"filter": where})

    assert payload["data"] is None, payload
    errors = json_list(payload, "errors")
    assert len(errors) == 1, payload
    error = json_object(errors[0])
    assert error["path"] == ["books"], payload
    assert error["message"] == "Invalid filter input", payload
    assert error["extensions"] == {
        "code": "FILTER_INVALID",
        "errors": {
            "genres": [
                {
                    "message": (
                        f"Select a valid choice. {saved_pk(blocked)} is not one of the available choices."
                    ),
                    "code": "invalid_choice",
                },
            ],
        },
    }, payload
