"""Consumer filter declarations publish inputs and apply callbacks and postponed annotations over HTTP."""

import copy
import logging
import threading
from collections import OrderedDict
from collections.abc import Generator
from contextlib import contextmanager
from functools import wraps

import pytest
import strawberry
from apps.library.models import Book, Branch, Shelf
from apps.scalars.models import ScalarSpecimen
from django.db.models import F, QuerySet
from django.forms import TextInput
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import CharFilter, Filter
from graphql_client import JSONObject, graphql_payload
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RangeFilter, RelatedFilter
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import consumer_module, consumer_query

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-filter-declarations/", _graphql_view)]


def _post(schema: DjangoSchema, document: str) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(document, url="/graphql-filter-declarations/")
    finally:
        _CURRENT["schema"] = None


_DEFERRED_CONSUMER = """
from __future__ import annotations

import strawberry
from apps.library.models import Branch
from strawberry.types import Info

from django_strawberry_framework import DjangoType
from django_strawberry_framework.filters import FilterInput, FilterSet, filter_input_type


class Pep563BranchFilter(FilterSet):
    class Meta:
        model = Branch
        fields = {"name": ["exact"]}


class Pep563BranchType(DjangoType):
    class Meta:
        model = Branch
        fields = ("id", "name")
        filterset_class = Pep563BranchFilter


@strawberry.type
class Query:
    @strawberry.field
    def by_call(
        self, info: Info, filter: filter_input_type(Pep563BranchFilter),
    ) -> list[Pep563BranchType]:
        return Pep563BranchFilter.apply_sync(filter, Branch.objects.order_by("name"), info)

    @strawberry.field
    def by_optional_call(
        self, info: Info, filter: filter_input_type(Pep563BranchFilter) | None = None,
    ) -> list[Pep563BranchType]:
        return Pep563BranchFilter.apply_sync(filter, Branch.objects.order_by("name"), info)

    @strawberry.field
    def by_subscript(
        self, info: Info, filter: FilterInput[Pep563BranchFilter] | None = None,
    ) -> list[Pep563BranchType]:
        return Pep563BranchFilter.apply_sync(filter, Branch.objects.order_by("name"), info)

    @strawberry.field
    def first(
        self, info: Info, filter: filter_input_type(Pep563BranchFilter) | None = None,
    ) -> list[Pep563BranchType]:
        return Pep563BranchFilter.apply_sync(filter, Branch.objects.order_by("name"), info)

    @strawberry.field
    def second(
        self, info: Info, filter: filter_input_type(Pep563BranchFilter) | None = None,
    ) -> list[Pep563BranchType]:
        return Pep563BranchFilter.apply_sync(filter, Branch.objects.order_by("name"), info)
"""


@contextmanager
def _deferred_schema() -> Generator[DjangoSchema]:
    """Keep the postponed annotations' real consumer module loaded through the HTTP request."""
    with consumer_module("filter_declarations_deferred_consumer", _DEFERRED_CONSUMER) as namespace:
        finalize_django_types()
        yield DjangoSchema(query=consumer_query(namespace), config=strawberry_config())


@pytest.mark.parametrize("field", ["byCall", "byOptionalCall", "bySubscript"])
@pytest.mark.django_db
def test_a_deferred_filter_annotation_applies_the_requested_predicate(field: str) -> None:
    """Each postponed helper spelling resolves its input outside the consumer's namespace."""
    Branch.objects.create(name="Alpha")
    Branch.objects.create(name="Beta")

    with _deferred_schema() as schema:
        assert _post(
            schema,
            f'{{ {field}(filter: {{name: {{exact: "Alpha"}}}}) {{ name }} }}',
        ) == {
            "data": {field: [{"name": "Alpha"}]},
        }


@pytest.mark.parametrize("field", ["byOptionalCall", "bySubscript"])
@pytest.mark.django_db
def test_an_optional_deferred_filter_annotation_accepts_omission(field: str) -> None:
    """An omitted optional postponed input leaves both otherwise matching rows visible."""
    Branch.objects.create(name="Alpha")
    Branch.objects.create(name="Beta")

    with _deferred_schema() as schema:
        assert _post(schema, f"{{ {field} {{ name }} }}") == {
            "data": {field: [{"name": "Alpha"}, {"name": "Beta"}]},
        }


@pytest.mark.django_db
def test_a_required_deferred_filter_annotation_refuses_omission() -> None:
    """The required call spelling remains non-null when its postponed annotation resolves."""
    with _deferred_schema() as schema:
        payload = _post(schema, "{ byCall { name } }")

    assert payload["data"] is None, payload
    assert payload["errors"] == [
        {
            "message": (
                "Field 'byCall' argument 'filter' of type 'Pep563BranchFilterInputType!' "
                "is required, but it was not provided."
            ),
            "locations": [{"line": 1, "column": 3}],
        },
    ], payload


@pytest.mark.django_db
def test_repeated_deferred_helper_evaluation_keeps_each_fields_input_value() -> None:
    """Two fields share the generated input type while applying their own argument values."""
    Branch.objects.create(name="Alpha")
    Branch.objects.create(name="Beta")

    with _deferred_schema() as schema:
        assert _post(
            schema,
            """
            {
              first(filter: {name: {exact: "Alpha"}}) { name }
              second(filter: {name: {exact: "Beta"}}) { name }
            }
            """,
        ) == {"data": {"first": [{"name": "Alpha"}], "second": [{"name": "Beta"}]}}


def _code_is(queryset: QuerySet[Shelf], _name: str, value: object) -> QuerySet[Shelf]:
    return queryset.filter(code=value)


class _ClassLockHolder:
    """A service whose lock is shared by copies of its bound method."""

    lock = threading.Lock()

    def code_is(
        self,
        queryset: QuerySet[Shelf],
        name: str,
        value: object,
    ) -> QuerySet[Shelf]:
        return _code_is(queryset, name, value)


class _LoggerHolder:
    """A service containing a logger, which copies as itself."""

    def __init__(self) -> None:
        self.log = logging.getLogger(__name__)

    def code_is(
        self,
        queryset: QuerySet[Shelf],
        name: str,
        value: object,
    ) -> QuerySet[Shelf]:
        return _code_is(queryset, name, value)


class _LockedInput(TextInput):
    """Django's widget copy shares its lock instead of copying it."""

    def __init__(self) -> None:
        super().__init__()
        self.lock = threading.Lock()


def _declaration(kind: str) -> CharFilter:
    if kind == "class-lock":
        return CharFilter(field_name="code", method=_ClassLockHolder().code_is)
    if kind == "method-name":
        return CharFilter(field_name="code", method="filter_code")
    if kind == "plain-function":
        return CharFilter(field_name="code", method=_code_is)
    if kind == "logger":
        return CharFilter(field_name="code", method=_LoggerHolder().code_is)
    assert kind == "widget-lock"
    return CharFilter(field_name="code", widget=_LockedInput())


def _copyable_schema(kind: str) -> DjangoSchema:
    class ShelfFilter(FilterSet):
        code_is = _declaration(kind)

        class Meta:
            model = Shelf
            fields = []

        def filter_code(
            self,
            queryset: QuerySet[Shelf],
            name: str,
            value: object,
        ) -> QuerySet[Shelf]:
            return _code_is(queryset, name, value)

    class ShelfNode(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")
            interfaces = (relay.Node,)
            filterset_class = ShelfFilter

    @strawberry.type
    class Query:
        shelves: DjangoConnection[ShelfNode] = DjangoConnectionField(ShelfNode)

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


@pytest.mark.parametrize(
    "kind",
    [
        "class-lock",
        "method-name",
        "plain-function",
        "logger",
        "widget-lock",
    ],
)
@pytest.mark.django_db
def test_a_copyable_declared_filter_answers_a_real_filtered_request(kind: str) -> None:
    """A copied callback or widget keeps the requested predicate and excludes the other shelf."""
    branch = Branch.objects.create(name="Copyable declarations")
    Shelf.objects.create(branch=branch, code="a")
    Shelf.objects.create(branch=branch, code="b")

    assert _post(
        _copyable_schema(kind),
        '{ shelves(filter: {codeIs: {exact: "a"}}) { edges { node { code } } } }',
    ) == {"data": {"shelves": {"edges": [{"node": {"code": "a"}}]}}}


def _choice_schema(*, subclass_target: bool) -> DjangoSchema:
    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"condition": ["exact"]}

    class SubShelfFilter(ShelfFilter):
        pass

    class LoneShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"condition": ["exact"]}

    target = SubShelfFilter if subclass_target else LoneShelfFilter

    class ViaShelfBookFilter(FilterSet):
        shelf = RelatedFilter(target, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ViaShelfBookNode(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            interfaces = (relay.Node,)
            filterset_class = ViaShelfBookFilter

    class PlainShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "topic")
            filterset_class = ShelfFilter

    @strawberry.type
    class Query:
        books: DjangoConnection[ViaShelfBookNode] = DjangoConnectionField(ViaShelfBookNode)

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config(), types=[PlainShelfType])


@pytest.mark.parametrize("subclass_target", [True, False], ids=["subclass", "unrelated"])
def test_an_unwired_set_names_its_own_choice_enum_over_http(*, subclass_target: bool) -> None:
    """An unwired subclass names its choice enum after itself, like an unrelated unwired control.

    An unbound set's enum carries the set's own class name; the subclass never
    inherits the ``PlainShelfType``-qualified name its wired base publishes.
    """
    unbound = "SubShelfFilterConditionEnum" if subclass_target else "LoneShelfFilterConditionEnum"
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"HIDE_FLAT_FILTERS": True}):
        payload = _post(
            _choice_schema(subclass_target=subclass_target),
            f'{{ unbound: __type(name: "{unbound}") {{ name }} '
            'inherited: __type(name: "PlainShelfTypeConditionEnum") { name } }',
        )
    assert payload == {
        "data": {"unbound": {"name": unbound}, "inherited": None},
    }


def test_same_named_ranges_with_different_axis_scalars_publish_distinct_inputs() -> None:
    """A decimal column and a text annotation keep both owner-qualified range inputs."""

    class ScalarPriceFilter(FilterSet):
        price = RangeFilter(field_name="price")

        class Meta:
            model = ScalarSpecimen
            fields = []

    class TextPriceFilter(FilterSet):
        price = RangeFilter(field_name="price")

        class Meta:
            model = Branch
            fields = []

    class ScalarRangeNode(DjangoType):
        class Meta:
            model = ScalarSpecimen
            fields = ("id", "label")
            interfaces = (relay.Node,)
            filterset_class = ScalarPriceFilter

    class TextRangeNode(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = TextPriceFilter

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Branch],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Branch]:
            return queryset.annotate(price=F("name"))

    @strawberry.type
    class Query:
        specimens: DjangoConnection[ScalarRangeNode] = DjangoConnectionField(ScalarRangeNode)
        branches: DjangoConnection[TextRangeNode] = DjangoConnectionField(TextRangeNode)

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config())
    assert _post(
        schema,
        '{ decimal: __type(name: "ScalarPriceFilterPriceRangeInputType") '
        "{ inputFields { name type { kind name } } } "
        'text: __type(name: "TextPriceFilterPriceRangeInputType") '
        "{ inputFields { name type { kind name } } } }",
    ) == {
        "data": {
            "decimal": {
                "inputFields": [
                    {"name": "start", "type": {"kind": "SCALAR", "name": "Decimal"}},
                    {"name": "end", "type": {"kind": "SCALAR", "name": "Decimal"}},
                ],
            },
            "text": {
                "inputFields": [
                    {"name": "start", "type": {"kind": "SCALAR", "name": "String"}},
                    {"name": "end", "type": {"kind": "SCALAR", "name": "String"}},
                ],
            },
        },
    }


@pytest.mark.parametrize("declares_branch", [False, True], ids=["borrowed", "expanded"])
def test_flat_filter_hiding_uses_the_set_that_actually_declares_the_branch(
    *,
    declares_branch: bool,
) -> None:
    """A borrowed leaf stays available unless its receiving set declares the branch it expands."""

    class ChildShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class SourceBranchFilter(FilterSet):
        shelves = RelatedFilter(ChildShelfFilter, field_name="shelves")

        class Meta:
            model = Branch
            fields = []

    class BorrowingBranchFilter(FilterSet):
        if declares_branch:
            shelves = RelatedFilter(ChildShelfFilter, field_name="shelves")

        class Meta:
            model = Branch
            fields = {"name": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            filters = OrderedDict(super().get_filters())
            filters["borrowed_code"] = copy.deepcopy(
                SourceBranchFilter.get_filters()["shelves__code"],
            )
            return filters

    class BorrowingShelfNode(DjangoType):
        class Meta:
            model = Shelf
            fields = ("code",)

    class BorrowingBranchNode(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = BorrowingBranchFilter

    @strawberry.type
    class Query:
        branches: DjangoConnection[BorrowingBranchNode] = DjangoConnectionField(
            BorrowingBranchNode,
        )

    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"HIDE_FLAT_FILTERS": True}):
        finalize_django_types()
        schema = DjangoSchema(
            query=Query,
            config=strawberry_config(),
            types=[BorrowingShelfNode],
        )
        payload = _post(
            schema,
            '{ __type(name: "BorrowingBranchFilterInputType") { inputFields { name } } }',
        )
    expected = ["name", "shelves"] if declares_branch else ["name", "borrowedCode"]
    assert payload == {
        "data": {
            "__type": {
                "inputFields": [
                    {"name": name}
                    for name in [
                        *expected,
                        "and",
                        "or",
                        "not",
                    ]
                ],
            },
        },
    }


def _naming_schema(case: str) -> DjangoSchema:
    if case == "digit-bags":
        declarations = {
            "field_2": CharFilter(field_name="name", lookup_expr="exact"),
            "field2": CharFilter(field_name="name", lookup_expr="icontains"),
        }
    elif case == "edge-bags":
        declarations = {
            "price": CharFilter(field_name="name", lookup_expr="exact"),
            "price_": RangeFilter(field_name="city"),
        }
    elif case == "digit-ranges":
        declarations = {
            "price_2": RangeFilter(field_name="price_2"),
            "price2": RangeFilter(field_name="price2"),
        }
    else:
        assert case == "leading-ranges"
        declarations = {
            "_price": RangeFilter(field_name="_price"),
            "price": RangeFilter(field_name="price"),
        }
    naming_filter = type(
        "NamingFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": Branch, "fields": []}), **declarations},
    )

    class NamingNode(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = naming_filter

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Branch],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Branch]:
            return queryset.annotate(
                price=F("name"),
                _price=F("city"),
                price2=F("city"),
                price_2=F("name"),
            )

    @strawberry.type
    class Query:
        branches: DjangoConnection[NamingNode] = DjangoConnectionField(NamingNode)

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


@pytest.mark.parametrize(
    (
        "case",
        "first",
        "second",
        "first_fields",
        "second_fields",
    ),
    [
        pytest.param(
            "digit-bags",
            "NamingFilterField_2FilterInputType",
            "NamingFilterField2FilterInputType",
            [{"name": "exact", "type": {"kind": "SCALAR", "name": "String"}}],
            [{"name": "iContains", "type": {"kind": "SCALAR", "name": "String"}}],
            id="digit-bags",
        ),
        pytest.param(
            "edge-bags",
            "NamingFilterPriceFilterInputType",
            "NamingFilterPrice_FilterInputType",
            [{"name": "exact", "type": {"kind": "SCALAR", "name": "String"}}],
            [
                {
                    "name": "exact",
                    "type": {"kind": "INPUT_OBJECT", "name": "NamingFilterCityRangeInputType"},
                },
            ],
            id="edge-bags",
        ),
        pytest.param(
            "digit-ranges",
            "NamingFilterPrice_2RangeInputType",
            "NamingFilterPrice2RangeInputType",
            [
                {"name": "start", "type": {"kind": "SCALAR", "name": "String"}},
                {"name": "end", "type": {"kind": "SCALAR", "name": "String"}},
            ],
            [
                {"name": "start", "type": {"kind": "SCALAR", "name": "String"}},
                {"name": "end", "type": {"kind": "SCALAR", "name": "String"}},
            ],
            id="digit-ranges",
        ),
        pytest.param(
            "leading-ranges",
            "NamingFilter_PriceRangeInputType",
            "NamingFilterPriceRangeInputType",
            [
                {"name": "start", "type": {"kind": "SCALAR", "name": "String"}},
                {"name": "end", "type": {"kind": "SCALAR", "name": "String"}},
            ],
            [
                {"name": "start", "type": {"kind": "SCALAR", "name": "String"}},
                {"name": "end", "type": {"kind": "SCALAR", "name": "String"}},
            ],
            id="leading-ranges",
        ),
    ],
)
def test_filter_input_names_preserve_digit_and_underscore_boundaries_over_http(
    case: str,
    first: str,
    second: str,
    first_fields: list[JSONObject],
    second_fields: list[JSONObject],
) -> None:
    """Both generated inputs survive with the declared names and their independent field shapes."""
    schema = _naming_schema(case)
    assert _post(
        schema,
        f'{{ first: __type(name: "{first}") {{ name inputFields {{ name type {{ kind name }} }} }} '
        f'second: __type(name: "{second}") {{ name inputFields {{ name type {{ kind name }} }} }} }}',
    ) == {
        "data": {
            "first": {"name": first, "inputFields": first_fields},
            "second": {"name": second, "inputFields": second_fields},
        },
    }
