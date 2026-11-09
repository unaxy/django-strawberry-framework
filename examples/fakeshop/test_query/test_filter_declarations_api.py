"""Consumer filter declarations publish inputs and apply callbacks and postponed annotations over HTTP."""

import copy
import datetime
import decimal
import logging
import threading
import uuid
from collections import OrderedDict
from collections.abc import Callable, Generator, Iterable, Mapping, Sized
from contextlib import contextmanager
from functools import wraps

import pytest
import strawberry
from apps.library.models import Book, Branch, Shelf, Venue
from apps.scalars.models import ScalarSpecimen
from django import forms
from django.db import connection
from django.db.models import F, Model, QuerySet, TextField
from django.forms import TextInput
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django.utils.choices import CallableChoiceIterator
from django.utils.functional import SimpleLazyObject, lazy
from django_filters import (
    BaseInFilter,
    BaseRangeFilter,
    CharFilter,
    ChoiceFilter,
    DateFilter,
    DateRangeFilter,
    Filter,
    MultipleChoiceFilter,
    TypedChoiceFilter,
    TypedMultipleChoiceFilter,
)
from django_filters.fields import ChoiceField
from graphql_client import JSONObject, graphql_payload
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
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet, RangeFilter, RelatedFilter
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils._narrowing import dict_of
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
                "Argument 'Query.byCall(filter:)' of type 'Pep563BranchFilterInputType!' "
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


def _declared_choice_schema(
    target: type[Model],
    declared: Filter,
    selected: tuple[str, ...] = ("id",),
) -> DjangoSchema:
    """Serve ``target`` rows, ``selected`` fields each, through a set whose one filter is ``pick``."""

    class ChoiceDeclarationFilter(FilterSet):
        pick = declared

        class Meta:
            model = target
            fields = []

    class ChoiceDeclarationNode(DjangoType):
        class Meta:
            model = target
            fields = selected
            interfaces = (relay.Node,)
            filterset_class = ChoiceDeclarationFilter

    @strawberry.type
    class Query:
        rows: DjangoConnection[ChoiceDeclarationNode] = DjangoConnectionField(
            ChoiceDeclarationNode,
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


_OFF_THE_COLUMN = (
    ", but its own form field accepts none of that column's `choices`, so every value of its "
    "input would be refused (a `DateRangeFilter`'s fixed date-range keys are no column's "
    "choices); give the filter `choices` drawn from the column's "
    "(`choices=<Model>.<Choices>.choices`, or a subset of them), or filter that column through "
    "a non-choice filter (`CharFilter`, `NumberFilter`, `DateFromToRangeFilter`, its lookups in "
    "Meta.fields, or `CharFilter(method=...)` for a method filter)."
)


@pytest.mark.parametrize(
    ("target", "make_filter", "expected"),
    [
        pytest.param(
            Shelf,
            lambda: DateRangeFilter(field_name="condition"),
            "ChoiceDeclarationFilter: DateRangeFilter on 'condition' publishes the choice enum "
            f"of Shelf.condition{_OFF_THE_COLUMN}",
            id="date-range-on-text-choices",
        ),
        pytest.param(
            Shelf,
            lambda: DateRangeFilter(field_name="tier"),
            "ChoiceDeclarationFilter: DateRangeFilter on 'tier' publishes the choice enum of "
            f"Shelf.tier{_OFF_THE_COLUMN}",
            id="date-range-on-integer-choices",
        ),
        pytest.param(
            Book,
            lambda: DateRangeFilter(field_name="circulation_status"),
            "ChoiceDeclarationFilter: DateRangeFilter on 'circulation_status' publishes the "
            f"choice enum of Book.circulation_status{_OFF_THE_COLUMN}",
            id="date-range-on-a-second-model",
        ),
        pytest.param(
            Shelf,
            lambda: MultipleChoiceFilter(field_name="condition", choices=[("mint", "Mint")]),
            "ChoiceDeclarationFilter: MultipleChoiceFilter on 'condition' publishes the choice "
            f"enum of Shelf.condition{_OFF_THE_COLUMN}",
            id="multiple-choice-disjoint",
        ),
        pytest.param(
            Shelf,
            lambda: ChoiceFilter(field_name="condition"),
            "ChoiceDeclarationFilter: ChoiceFilter on 'condition' publishes the choice enum of "
            f"Shelf.condition{_OFF_THE_COLUMN}",
            id="choice-without-choices",
        ),
        pytest.param(
            Venue,
            lambda: DateRangeFilter(field_name="opened_on", lookup_expr="year"),
            "ChoiceDeclarationFilter: DateRangeFilter on 'opened_on' reads a transform's output "
            "(IntegerField), which declares no `choices` whatever its column declares, so no "
            "choice enum types its input (the filter's own `choices` never feed the enum); "
            "filter the column through a non-choice filter (`CharFilter`, `NumberFilter`, "
            "`DateFromToRangeFilter`, its lookups in Meta.fields, or `CharFilter(method=...)` "
            "for a method filter).",
            id="date-range-over-a-year-transform",
        ),
    ],
)
def test_a_choice_declaration_no_value_of_its_input_can_serve_refuses_the_schema(
    target: type[Model],
    make_filter: Callable[[], Filter],
    expected: str,
) -> None:
    """A choice filter whose own form accepts no member of the enum it would publish is refused.

    django-filter validates a declared filter's value against the filter's own ``choices``,
    never the column's, so a ``DateRangeFilter``'s date-range keys, a disjoint ``choices=``
    list and a ``ChoiceFilter`` declaring none would answer ``invalid_choice`` for every
    member; past a ``year`` transform no field declaring ``choices`` types the leaf at all.
    """
    with pytest.raises(ConfigurationError) as exc:
        _ = _declared_choice_schema(target, make_filter())

    assert str(exc.value) == expected


def _shelves() -> None:
    branch = Branch.objects.create(name="Choice declarations")
    Shelf.objects.create(branch=branch, code="g", condition="good", tier=Shelf.Tier.LOWER)
    Shelf.objects.create(branch=branch, code="w", condition="worn", tier=Shelf.Tier.MIDDLE)
    Shelf.objects.create(branch=branch, code="d", condition="damaged", tier=Shelf.Tier.UPPER)


#: The one shelf both a ``good`` condition and the ``LOWER`` tier select.
_GOOD_OR_LOWER = {"data": {"rows": {"edges": [{"node": {"code": "g"}}]}}}


def _picked(schema: DjangoSchema, member: str) -> JSONObject:
    return _post(
        schema,
        f"{{ rows(filter: {{pick: {{exact: {member}}}}}) {{ edges {{ node {{ code }} }} }} }}",
    )


def _refused_choice(value: object) -> JSONObject:
    return {
        "data": None,
        "errors": [
            {
                "message": "Invalid filter input",
                "locations": [{"line": 1, "column": 3}],
                "path": ["rows"],
                "extensions": {
                    "code": "FILTER_INVALID",
                    "errors": {
                        "pick": [
                            {
                                "message": (
                                    f"Select a valid choice. {value} is not one of the available "
                                    "choices."
                                ),
                                "code": "invalid_choice",
                            },
                        ],
                    },
                },
            },
        ],
    }


@pytest.mark.parametrize(
    (
        "make_filter",
        "accepted",
        "refused",
        "refused_value",
    ),
    [
        pytest.param(
            lambda: ChoiceFilter(
                field_name="condition",
                choices=[("good", "Good"), ("worn", "Worn")],
            ),
            "good",
            "damaged",
            "damaged",
            id="choice-subset-on-text-choices",
        ),
        pytest.param(
            lambda: TypedChoiceFilter(
                field_name="tier",
                choices=Shelf.Tier.choices[:2],
                coerce=int,
            ),
            "MEMBER_1",
            "MEMBER_3",
            3,
            id="typed-choice-subset-on-integer-choices",
        ),
    ],
)
@pytest.mark.django_db
def test_a_choice_declaration_sharing_a_value_with_its_column_serves_its_own_choices(
    make_filter: Callable[[], Filter],
    accepted: str,
    refused: str,
    refused_value: object,
) -> None:
    """A subset of the column's ``choices`` builds: its members filter, the others are refused.

    The input publishes the column's enum and the filter's own form field validates each value,
    so a member the declaration keeps filters the rows and one it leaves out is
    ``FILTER_INVALID`` ``invalid_choice``.
    """
    _shelves()
    schema = _declared_choice_schema(Shelf, make_filter(), ("id", "code"))

    assert _picked(schema, accepted) == _GOOD_OR_LOWER
    assert _picked(schema, refused) == _refused_choice(refused_value)


_Choices = Callable[[], list[tuple[str, str]]]


def _counted_choices(calls: list[None]) -> _Choices:
    """Choices recording each evaluation; a deep copy keeps the function itself."""

    def choices() -> list[tuple[str, str]]:
        calls.append(None)
        return [("good", "Good")]

    return choices


def _as_called(choices: _Choices) -> object:
    """Hand the declaration the callable itself."""
    return choices


def _as_lazy_promise(choices: _Choices) -> object:
    """Hand the declaration a ``lazy()`` promise evaluating ``choices`` on use."""
    return lazy(choices, list)()


def _as_choice_iterator(choices: _Choices) -> object:
    """Hand the declaration Django's own lazy wrapper over ``choices``."""
    return CallableChoiceIterator(choices)


class _TypedFieldChoiceFilter(ChoiceFilter):
    """A consumer ``ChoiceFilter`` whose ``field_class`` is Django's own ``TypedChoiceField``."""

    field_class: type[forms.TypedChoiceField] = forms.TypedChoiceField


def _choice(choices: object) -> Filter:
    return ChoiceFilter(field_name="condition", choices=choices)


def _typed_choice(choices: object) -> Filter:
    return TypedChoiceFilter(field_name="condition", choices=choices, coerce=str)


def _multiple_choice(choices: object) -> Filter:
    return MultipleChoiceFilter(field_name="condition", choices=choices)


def _typed_multiple_choice(choices: object) -> Filter:
    return TypedMultipleChoiceFilter(field_name="condition", choices=choices, coerce=str)


def _typed_field_choice(choices: object) -> Filter:
    return _TypedFieldChoiceFilter(field_name="condition", choices=choices)


def _typed_choices_in(choices: object) -> Filter:
    return _TypedChoicesInFilter(
        field_name="condition",
        lookup_expr="in",
        choices=choices,
        coerce=str,
    )


#: Each choice filter class, built over ``Shelf.condition`` with the ``choices`` it is handed,
#: and the operator bag a request selecting the ``good`` shelf sends it.
_DEFERRING_CLASSES = [
    pytest.param(_choice, "{exact: good}", id="choice"),
    pytest.param(_typed_choice, "{exact: good}", id="typed-choice"),
    pytest.param(_multiple_choice, "{exact: [good]}", id="multiple-choice"),
    pytest.param(_typed_multiple_choice, "{exact: [good]}", id="typed-multiple-choice"),
    pytest.param(_typed_field_choice, "{exact: good}", id="django-typed-choice-field-class"),
    pytest.param(_typed_choices_in, "{in: [good]}", id="typed-choice-csv-in"),
]


#: The statements a request filtering by a ``QuerySet`` declared as ``choices`` runs: the
#: queryset itself, then the rows.
_QUERYSET_CHOICES_REQUEST_STATEMENTS = 2


#: The ``choices`` evaluations and statements a consumer reading ``len()`` of its deferred
#: choices runs at schema build: one per form field the build reads.
_LEN_BUILD_CALLS = 2
_LEN_BUILD_STATEMENTS = 2


def _as_counted_queryset(_choices: _Choices) -> object:
    """Hand the declaration a ``QuerySet`` of ``Shelf.condition`` pairs keeping ``good``."""
    return Shelf.objects.filter(condition="good").values_list("condition", "condition")


def _picked_by(schema: DjangoSchema, operators: str) -> JSONObject:
    return _post(
        schema,
        f"{{ rows(filter: {{pick: {operators}}}) {{ edges {{ node {{ code }} }} }} }}",
    )


@pytest.mark.parametrize(
    "wrap",
    [
        pytest.param(_as_called, id="callable"),
        pytest.param(_as_lazy_promise, id="lazy-promise"),
        pytest.param(SimpleLazyObject, id="simple-lazy-object"),
        pytest.param(_as_choice_iterator, id="choice-iterator"),
    ],
)
@pytest.mark.parametrize(("declare", "operators"), _DEFERRING_CLASSES)
@pytest.mark.django_db
def test_deferred_choices_are_evaluated_per_request_never_at_schema_build(
    declare: Callable[[object], Filter],
    operators: str,
    wrap: Callable[[_Choices], object],
) -> None:
    """A declaration's callable or lazy ``choices`` are left to the form each request builds.

    Building the schema evaluates no consumer choices and runs no query, whatever form field
    the filter's class builds: django-filter's choice fields, Django's own
    ``TypedChoiceField`` and ``TypedMultipleChoiceField`` (which normalize ``choices`` when
    they are built), a consumer ``field_class`` on one, and a CSV ``in`` over a typed choice
    form. The declaration builds whatever the choices would return; the one request's form
    evaluates them once and filters by the kept member.
    """
    _shelves()
    calls: list[None] = []
    with CaptureQueriesContext(connection) as captured:
        schema = _declared_choice_schema(
            Shelf,
            declare(wrap(_counted_choices(calls))),
            ("id", "code"),
        )
    assert calls == []
    assert captured.captured_queries == []

    assert _picked_by(schema, operators) == _GOOD_OR_LOWER
    assert len(calls) == 1


@pytest.mark.parametrize(("declare", "operators"), _DEFERRING_CLASSES)
@pytest.mark.django_db
def test_queryset_choices_are_run_per_request_never_at_schema_build(
    declare: Callable[[object], Filter],
    operators: str,
) -> None:
    """A ``QuerySet`` handed as ``choices`` runs no query at build and one per request.

    The schema builds before the rows its queryset reads exist; the request's form runs it
    beside the request's own rows statement, and filters by the member it returned.
    """
    with CaptureQueriesContext(connection) as built:
        schema = _declared_choice_schema(
            Shelf,
            declare(Shelf.objects.filter(condition="good").values_list("condition", "condition")),
            ("id", "code"),
        )
    assert built.captured_queries == []
    _shelves()

    with CaptureQueriesContext(connection) as served:
        assert _picked_by(schema, operators) == _GOOD_OR_LOWER
    assert len(served.captured_queries) == _QUERYSET_CHOICES_REQUEST_STATEMENTS


class _CountingChoiceField(forms.TypedChoiceField):
    """A consumer choice form whose ``__init__`` reads ``len()`` of its own ``choices``."""

    choice_count: int

    def __init__(
        self,
        *,
        choices: Iterable[tuple[str, str]],
        coerce: Callable[[str], object] = str,
        required: bool,
        label: str | None,
    ) -> None:
        super().__init__(choices=choices, coerce=coerce, required=required, label=label)
        field_choices: object = self.choices
        assert isinstance(field_choices, Sized)
        self.choice_count = len(field_choices)


class _CountingFieldClassFilter(TypedChoiceFilter):
    """A ``TypedChoiceFilter`` whose ``field_class`` counts its ``choices`` when built."""

    field_class: type[forms.TypedChoiceField] = _CountingChoiceField


class _CountingFieldOverrideFilter(TypedChoiceFilter):
    """A ``TypedChoiceFilter`` whose ``field`` override reads ``len()`` of its ``choices``."""

    @property
    @override
    def field(self) -> forms.Field:
        choices = dict_of(self.extra).get("choices")
        assert isinstance(choices, Sized)
        self.choice_count: int = len(choices)
        return super().field


def _counting_field_class(choices: object) -> Filter:
    return _CountingFieldClassFilter(field_name="condition", choices=choices, coerce=str)


def _counting_field_override(choices: object) -> Filter:
    return _CountingFieldOverrideFilter(field_name="condition", choices=choices, coerce=str)


@pytest.mark.parametrize(
    (
        "wrap",
        "build_calls",
        "build_statements",
        "request_calls",
        "request_statements",
    ),
    [
        pytest.param(
            SimpleLazyObject,
            _LEN_BUILD_CALLS,
            0,
            1,
            1,
            id="simple-lazy-object",
        ),
        pytest.param(
            _as_counted_queryset,
            0,
            _LEN_BUILD_STATEMENTS,
            0,
            _QUERYSET_CHOICES_REQUEST_STATEMENTS,
            id="queryset",
        ),
    ],
)
@pytest.mark.parametrize(
    "declare",
    [
        pytest.param(_counting_field_class, id="field-class-init"),
        pytest.param(_counting_field_override, id="field-override"),
    ],
)
@pytest.mark.django_db
def test_consumer_code_counting_its_choices_at_build_builds_and_serves(
    declare: Callable[[object], Filter],
    wrap: Callable[[_Choices], object],
    build_calls: int,
    build_statements: int,
    request_calls: int,
    request_statements: int,
) -> None:
    """A consumer ``field_class`` or ``field`` override reading ``len()`` of its choices builds.

    Consumer code reading its own deferred ``choices`` evaluates them where it is built, the
    schema build included, as often as it would on the declared value (a
    ``SimpleLazyObject`` and a ``QuerySet`` cache what they evaluate); the request's form
    evaluates them once more and filters by the kept member.
    """
    calls: list[None] = []
    with CaptureQueriesContext(connection) as built:
        schema = _declared_choice_schema(
            Shelf,
            declare(wrap(_counted_choices(calls))),
            ("id", "code"),
        )
    assert (len(calls), len(built.captured_queries)) == (build_calls, build_statements)
    _shelves()
    del calls[:]

    with CaptureQueriesContext(connection) as served:
        assert _picked_by(schema, "{exact: good}") == _GOOD_OR_LOWER
    assert (len(calls), len(served.captured_queries)) == (request_calls, request_statements)


def _csv_class(name: str, wrapper: type[Filter], member: type[Filter]) -> type[Filter]:
    """The CSV class ``wrapper`` over ``member``, as django-filter's ``filter_for_lookup`` builds one."""
    built: type[Filter] = type(name, (wrapper, member), {})
    return built


#: A CSV ``in`` whose members are ``DateRangeFilter``'s fixed date-range keys.
_DateRangesInFilter = _csv_class("DateRangesInFilter", BaseInFilter, DateRangeFilter)
#: A CSV ``range`` whose two bounds are ``DateRangeFilter``'s date-range keys.
_DateRangesRangeFilter = _csv_class("DateRangesRangeFilter", BaseRangeFilter, DateRangeFilter)
#: A CSV ``in`` whose every member its form reads as a list of choices.
_MultipleChoicesInFilter = _csv_class(
    "MultipleChoicesInFilter",
    BaseInFilter,
    MultipleChoiceFilter,
)
#: A CSV ``in`` whose members its form validates against its own ``choices``.
_ChoicesInFilter = _csv_class("ChoicesInFilter", BaseInFilter, ChoiceFilter)


class _AnyValueChoiceField(ChoiceField):
    """A consumer choice form whose ``valid_value`` accepts any value, its keys or not."""

    @override
    def valid_value(self, value: object) -> bool:
        return True


class _UncheckedChoiceField(ChoiceField):
    """A consumer choice form whose ``validate`` checks no value against its keys."""

    @override
    def validate(self, value: object) -> None:
        _ = value


#: A CSV ``in`` whose member form accepts any value in ``valid_value``.
_AnyValueChoicesInFilter = _csv_class(
    "AnyValueChoicesInFilter",
    BaseInFilter,
    type("AnyValueChoiceFilter", (ChoiceFilter,), {"field_class": _AnyValueChoiceField}),
)
#: A CSV ``in`` whose member form validates nothing in ``validate``.
_UncheckedChoicesInFilter = _csv_class(
    "UncheckedChoicesInFilter",
    BaseInFilter,
    type("UncheckedChoiceFilter", (ChoiceFilter,), {"field_class": _UncheckedChoiceField}),
)


class _TypedChoicesInFilter(BaseInFilter, TypedChoiceFilter):
    """A consumer CSV ``in`` whose members its form coerces after validating its own ``choices``."""


class _DatesRangeFilter(BaseRangeFilter, DateFilter):
    """A consumer CSV ``range`` whose two bounds its form cleans as dates."""


def _overridden_specimen_schema(
    column: str,
    lookup: str,
    filter_class: type[Filter],
) -> DjangoSchema:
    """Serve specimens through a set whose ``column`` leaf ``Meta.filter_overrides`` selects."""

    class OverrideDeclarationFilter(FilterSet):
        class Meta:
            model = ScalarSpecimen
            fields = {column: [lookup]}
            filter_overrides = {TextField: {"filter_class": filter_class}}

    class OverrideDeclarationNode(DjangoType):
        class Meta:
            model = ScalarSpecimen
            fields = ("id", "label")
            interfaces = (relay.Node,)
            filterset_class = OverrideDeclarationFilter

    @strawberry.type
    class Query:
        rows: DjangoConnection[OverrideDeclarationNode] = DjangoConnectionField(
            OverrideDeclarationNode,
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


def _no_value(
    subject: str,
    column: str,
    form: str,
    lookup: str,
) -> str:
    """The refusal of a leaf whose own form and lookup answer no value of its column."""
    return (
        f"{subject} is published as {column} values, but its own form field ({form}) and "
        f"lookup {lookup!r} answer no value of that column, so every value of its input would "
        "be refused or would constrain nothing (match every row); filter a transform of the "
        'column whose output its form cleans (a TimeFilter on `field_name="<column>__time"`), '
        "declare a filter class whose form cleans the column's kind, or read the value in "
        "`method=`."
    )


@pytest.mark.parametrize(
    ("make_schema", "expected"),
    [
        pytest.param(
            lambda: _declared_choice_schema(
                ScalarSpecimen,
                _DateRangesInFilter(field_name="label", lookup_expr="in"),
            ),
            _no_value(
                "ChoiceDeclarationFilter: DateRangesInFilter on 'label'",
                "ScalarSpecimen.label",
                "ChoiceInField",
                "in",
            ),
            id="date-range-keys-in-on-text",
        ),
        pytest.param(
            lambda: _overridden_specimen_schema("label", "in", DateRangeFilter),
            _no_value(
                "OverrideDeclarationFilter: DateRangeInFilter on 'label'",
                "ScalarSpecimen.label",
                "ChoiceInField",
                "in",
            ),
            id="override-date-range-keys-in-on-text",
        ),
        pytest.param(
            lambda: _declared_choice_schema(
                ScalarSpecimen,
                _DateRangesRangeFilter(field_name="occurred_on", lookup_expr="range"),
            ),
            _no_value(
                "ChoiceDeclarationFilter: DateRangesRangeFilter on 'occurred_on'",
                "ScalarSpecimen.occurred_on",
                "ChoiceRangeField",
                "range",
            ),
            id="date-range-keys-range-on-a-date",
        ),
        pytest.param(
            lambda: _declared_choice_schema(
                ScalarSpecimen,
                _DateRangesRangeFilter(field_name="label", lookup_expr="range"),
            ),
            _no_value(
                "ChoiceDeclarationFilter: DateRangesRangeFilter on 'label'",
                "ScalarSpecimen.label",
                "ChoiceRangeField",
                "range",
            ),
            id="date-range-keys-range-on-text",
        ),
        pytest.param(
            lambda: _declared_choice_schema(
                ScalarSpecimen,
                _MultipleChoicesInFilter(
                    field_name="label",
                    lookup_expr="in",
                    choices=[("alpha", "Alpha")],
                ),
            ),
            _no_value(
                "ChoiceDeclarationFilter: MultipleChoicesInFilter on 'label'",
                "ScalarSpecimen.label",
                "MultipleChoiceInField",
                "in",
            ),
            id="multiple-choice-members-in-on-text",
        ),
        pytest.param(
            lambda: _declared_choice_schema(
                Shelf,
                _MultipleChoicesInFilter(
                    field_name="condition",
                    lookup_expr="in",
                    choices=Shelf.Condition.choices,
                ),
            ),
            _no_value(
                "ChoiceDeclarationFilter: MultipleChoicesInFilter on 'condition'",
                "Shelf.condition",
                "MultipleChoiceInField",
                "in",
            ),
            id="multiple-choice-members-in-on-a-choice-column",
        ),
        pytest.param(
            lambda: _declared_choice_schema(
                ScalarSpecimen,
                _ChoicesInFilter(field_name="occurred_on", lookup_expr="in", choices=[("x", "X")]),
            ),
            _no_value(
                "ChoiceDeclarationFilter: ChoicesInFilter on 'occurred_on'",
                "ScalarSpecimen.occurred_on",
                "ChoiceInField",
                "in",
            ),
            id="disjoint-choices-in-on-a-date",
        ),
    ],
)
def test_a_csv_declaration_no_value_of_its_column_answers_refuses_the_schema(
    make_schema: Callable[[], DjangoSchema],
    expected: str,
) -> None:
    """A CSV leaf whose own form and lookup answer no value of its column is refused at build.

    Each is asked as a request asks it, whatever the column: a choice form by each key of its
    own choices (a ``DateRangeFilter``'s fixed keys, which its own ``filter`` cannot look up
    as a list, or a key no date spells), any other form by the column's samples, and a
    ``MultipleChoiceField`` member reads no single value. ``BaseRangeField`` and
    ``BaseCSVField`` clean each member through django-filter's and Django's own classes, so
    the wrapper is asked as its member is.
    """
    with pytest.raises(ConfigurationError) as exc:
        _ = make_schema()

    assert str(exc.value) == expected


def _specimens() -> None:
    for day, label, signed_big in ((1, "", 1), (2, "alpha", 2), (3, "beta", 3)):
        _ = ScalarSpecimen.objects.create(
            label=label,
            occurred_on=datetime.date(2024, 1, day),
            occurred_at=datetime.datetime(2024, 1, day, 12, tzinfo=datetime.timezone.utc),
            occurred_time=datetime.time(day),
            external_id=uuid.UUID(int=day),
            signed_big=signed_big,
            price=decimal.Decimal(day) + decimal.Decimal("0.5"),
        )


@pytest.mark.parametrize(
    (
        "declared",
        "lookup",
        "value",
        "labels",
    ),
    [
        pytest.param(
            lambda: _ChoicesInFilter(
                field_name="occurred_on",
                lookup_expr="in",
                choices=[("2024-01-02", "Second"), ("2024-01-03", "Third")],
            ),
            "in",
            '["2024-01-02"]',
            ["alpha"],
            id="date-keys-in-on-a-date",
        ),
        pytest.param(
            lambda: _DatesRangeFilter(field_name="occurred_on", lookup_expr="range"),
            "range",
            '["2024-01-02", "2024-01-03"]',
            ["alpha", "beta"],
            id="dates-range-on-a-date",
        ),
        pytest.param(
            lambda: _ChoicesInFilter(
                field_name="label",
                lookup_expr="in",
                choices=[("", "Blank")],
            ),
            "in",
            '[""]',
            [""],
            id="blank-key-in-on-text",
        ),
        pytest.param(
            lambda: _ChoicesInFilter(field_name="label", lookup_expr="in"),
            "in",
            '[""]',
            [""],
            id="no-choices-in-on-text",
        ),
        pytest.param(
            lambda: _TypedChoicesInFilter(
                field_name="signed_big",
                lookup_expr="in",
                choices=[(1, "One"), (2, "Two")],
                coerce=int,
            ),
            "in",
            "[2]",
            ["alpha"],
            id="integer-keys-in-on-a-big-integer",
        ),
        pytest.param(
            lambda: _TypedChoicesInFilter(
                field_name="price",
                lookup_expr="in",
                choices=[("all", "All"), ("1.5", "One and a half")],
                coerce=decimal.Decimal,
            ),
            "in",
            '["1.5"]',
            [""],
            id="decimal-coerce-keys-in-on-a-decimal",
        ),
        pytest.param(
            lambda: _AnyValueChoicesInFilter(
                field_name="occurred_on",
                lookup_expr="in",
                choices=[("x", "X")],
            ),
            "in",
            '["2024-01-02"]',
            ["alpha"],
            id="consumer-valid-value-off-its-keys-on-a-date",
        ),
        pytest.param(
            lambda: _UncheckedChoicesInFilter(
                field_name="occurred_on",
                lookup_expr="in",
                choices=[("x", "X")],
            ),
            "in",
            '["2024-01-03"]',
            ["beta"],
            id="consumer-validate-off-its-keys-on-a-date",
        ),
    ],
)
@pytest.mark.django_db
def test_a_csv_declaration_some_value_of_its_column_answers_serves_it(
    declared: Callable[[], Filter],
    lookup: str,
    value: str,
    labels: list[str],
) -> None:
    """A CSV leaf one value of its column answers builds and filters by the value sent.

    A choice form's keys spelling the column's values (dates, the blank text its own or
    django-filter's empty choice declares, integers its ``coerce=int`` reads, the decimal
    its ``coerce=Decimal`` reads beside a key it cannot parse) and a
    ``BaseRangeFilter`` over a ``DateFilter`` each answer, so the schema builds and the request
    selects exactly the rows the value names. A choice form whose ``validate`` or
    ``valid_value`` is the consumer's accepts values off its keys, so it is asked the column's
    samples instead, and serves the date sent though no key spells it.
    """
    _specimens()
    schema = _declared_choice_schema(ScalarSpecimen, declared(), ("id", "label"))

    assert _post(
        schema,
        f"{{ rows(filter: {{pick: {{{lookup}: {value}}}}}) {{ edges {{ node {{ label }} }} }} }}",
    ) == {"data": {"rows": {"edges": [{"node": {"label": label}} for label in labels]}}}


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


# The default converter names ``field_2`` and ``field2`` (``price_2`` / ``price2``) alike,
# so a schema serving both is built under ``auto_camel_case=False``, which names them apart.
_SNAKE_NAMING_CASES = frozenset({"digit-bags", "digit-ranges"})


def _naming_schema(case: str, *, snake: bool | None = None) -> DjangoSchema:
    if snake is None:
        snake = case in _SNAKE_NAMING_CASES
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
    return DjangoSchema(query=Query, config=strawberry_config(auto_camel_case=not snake))


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
            [{"name": "i_contains", "type": {"kind": "SCALAR", "name": "String"}}],
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
    """Both generated inputs survive with the declared names and their independent field shapes.

    The type names come from ``pascal_case``, which keeps an underscore before a digit;
    the digit cases are served under ``auto_camel_case=False`` (``_SNAKE_NAMING_CASES``).
    """
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


def test_a_path_member_beside_a_declared_filter_the_converter_names_alike_names_the_path() -> None:
    """The refusal names a ``Meta.fields`` path as declared, not by the attr it flattens to.

    ``shelves__code`` flattens to the input attr ``shelves_code``, which the default
    converter names ``shelvesCode``, the declared filter's name; the consumer changes
    the ``Meta.fields`` entry, so the refusal names ``shelves__code``.
    """

    class PathNamingFilter(FilterSet):
        shelvesCode = CharFilter(  # noqa: N815 - the camel-case member is the collision under test
            field_name="name",
            lookup_expr="exact",
        )

        class Meta:
            model = Branch
            fields = {"shelves__code": ["exact"]}

    class PathNamingNode(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = PathNamingFilter

    @strawberry.type
    class Query:
        branches: DjangoConnection[PathNamingNode] = DjangoConnectionField(PathNamingNode)

    finalize_django_types()
    with pytest.raises(ConfigurationError) as exc:
        _ = DjangoSchema(query=Query, config=strawberry_config())

    assert str(exc.value) == (
        "PathNamingFilterInputType: fields 'shelves_code' and 'shelvesCode' both publish the "
        "GraphQL field name 'shelvesCode' under this schema's name converter, so one would "
        "silently replace the other. FilterSet 'test_a_path_member_beside_a_declared_filter_"
        "the_converter_names_alike_names_the_path.<locals>.PathNamingFilter' generates them "
        "from members 'shelves__code' and 'shelvesCode'. Drop 'shelves__code' via Meta.fields "
        "/ Meta.exclude, or rename or remove the declaration 'shelvesCode' (disable an "
        "inherited one with `shelvesCode = None`)."
    )


class _UpperCaseNames(NameConverter):
    """Upper-case every name, an explicit ``name=`` included."""

    @override
    def get_graphql_name(self, obj: HasGraphQLName) -> str:
        return super().get_graphql_name(obj).upper()


class _StripTrailingE(NameConverter):
    """Drop a trailing ``e``, which names the ``gt`` and ``gte`` lookups alike."""

    @override
    def get_graphql_name(self, obj: HasGraphQLName) -> str:
        return super().get_graphql_name(obj).removesuffix("e")


def _converter_schema(filterset_cls: type[FilterSet], converter: NameConverter) -> DjangoSchema:
    class ConverterNode(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = filterset_cls

    @strawberry.type
    class Query:
        branches: DjangoConnection[ConverterNode] = DjangoConnectionField(ConverterNode)

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config(name_converter=converter))


def test_a_member_the_converter_names_like_a_logic_key_names_the_key_reserved() -> None:
    """A filter the converter names like ``and`` is refused, naming the logic key reserved.

    Under a converter that upper-cases every name, the declared ``AND`` and the logic
    key ``and_`` (``name="and"``) both publish ``AND``; the key is the package's, so
    the remedy names the member's own lever only.
    """

    class LogicNamingFilter(FilterSet):
        AND = CharFilter(field_name="name", lookup_expr="exact")

        class Meta:
            model = Branch
            fields = []

    with pytest.raises(ConfigurationError) as exc:
        _ = _converter_schema(LogicNamingFilter, _UpperCaseNames())

    assert str(exc.value).startswith(
        "LogicNamingFilterInputType: fields 'AND' and 'and_' both publish the GraphQL field "
        "name 'AND'",
    )
    assert str(exc.value).endswith(
        "generates them from members 'AND' and 'and_'. 'and_' is a reserved logic key: rename "
        "or remove the declaration 'AND' (disable an inherited one with `AND = None`).",
    )


def test_operator_bag_lookups_the_converter_names_alike_name_the_lookup_list() -> None:
    """Two lookups of one head the converter names alike point at that head's lookup list.

    ``gt`` and ``gte`` both publish ``gt`` under a converter that drops a trailing ``e``;
    a lookup takes no declaration of its own, so the remedy names the ``Meta.fields``
    lookup list of ``name``.
    """

    class BagNamingFilter(FilterSet):
        class Meta:
            model = Branch
            fields = {"name": ["gt", "gte"]}

    with pytest.raises(ConfigurationError) as exc:
        _ = _converter_schema(BagNamingFilter, _StripTrailingE())

    assert str(exc.value) == (
        "BagNamingFilterNameFilterInputType: fields 'gt' and 'gte' both publish the GraphQL "
        "field name 'gt' under this schema's name converter, so one would silently replace "
        "the other. FilterSet 'test_operator_bag_lookups_the_converter_names_alike_name_the_"
        "lookup_list.<locals>.BagNamingFilter' generates them from lookups 'gt' and 'gte'. "
        "Drop one from the Meta.fields lookup list of 'name'."
    )


@pytest.mark.parametrize("case", ["digit-bags", "digit-ranges"])
def test_filter_members_the_default_converter_names_alike_refuse_the_schema(case: str) -> None:
    """``field_2`` beside ``field2`` both publish ``field2`` by default, so the build refuses them.

    Generated filter fields carry no ``name=``; the executing schema's ``NameConverter``
    names each, so the refusal names the generated filter input type, the set and the
    two declared members to rename or remove.
    """
    first, second = ("field_2", "field2") if case == "digit-bags" else ("price_2", "price2")
    with pytest.raises(ConfigurationError) as exc:
        _ = _naming_schema(case, snake=False)
    assert str(exc.value).startswith(
        f"NamingFilterInputType: fields {first!r} and {second!r} both publish the GraphQL "
        f"field name {second!r}",
    )
    assert str(exc.value).endswith(
        f"FilterSet 'NamingFilter' generates them from members {first!r} and {second!r}. "
        "Rename or remove one of the declarations (disable an inherited one with "
        "`<name> = None`).",
    )


def _flat_copy_schema(
    shelf_lookups: list[str],
    declarations: Mapping[str, object],
    converter: NameConverter | None = None,
) -> DjangoSchema:
    """A schema whose branch filter set expands ``RelatedFilter`` ``shelves`` into flat copies."""
    registry.clear()
    shelf_filter = type(
        "FlatShelfFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": Shelf, "fields": {"code": shelf_lookups}})},
    )
    flat_branch_filter = type(
        "FlatBranchFilter",
        (FilterSet,),
        {
            "shelves": RelatedFilter(shelf_filter, field_name="shelves"),
            "Meta": type("Meta", (), {"model": Branch, "fields": ["name"]}),
            **declarations,
        },
    )

    class FlatShelfNode(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class FlatBranchNode(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = flat_branch_filter

    del FlatShelfNode

    @strawberry.type
    class Query:
        branches: DjangoConnection[FlatBranchNode] = DjangoConnectionField(FlatBranchNode)

    finalize_django_types()
    config = (
        strawberry_config() if converter is None else strawberry_config(name_converter=converter)
    )
    return DjangoSchema(query=Query, config=config)


def test_a_flat_copy_the_converter_names_like_a_declared_filter_names_its_relatedfilter() -> None:
    """A ``RelatedFilter`` flat copy beside a declared filter names the branch and the setting.

    ``shelves__code`` (the flat copy of ``shelves``' ``code``) publishes ``shelvesCode``,
    the declared filter's name; no ``Meta.fields`` entry of the branch set lists the copy,
    so its lever is the ``RelatedFilter`` or ``HIDE_FLAT_FILTERS``, which builds.
    """
    declarations = {"shelvesCode": CharFilter(field_name="name", lookup_expr="exact")}
    with pytest.raises(ConfigurationError) as exc:
        _ = _flat_copy_schema(["exact"], declarations)

    assert str(exc.value).endswith(
        "FilterSet 'FlatBranchFilter' generates them from members 'shelvesCode' and "
        "'shelves__code'. Rename or remove the declaration 'shelvesCode' (disable an "
        "inherited one with `shelvesCode = None`), or rename the RelatedFilter 'shelves' that "
        "'shelves__code' is the flat copy of, or hide flat copies with the HIDE_FLAT_FILTERS "
        "setting.",
    )
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"HIDE_FLAT_FILTERS": True}):
        schema = _flat_copy_schema(["exact"], declarations)
    assert "shelvesCode" in str(schema)


def test_flat_copy_lookups_the_converter_names_alike_name_the_child_lookup_list() -> None:
    """A flat copy's two lookups the converter names alike point at the child set's list.

    ``shelves__code`` copies ``code``'s ``gt`` and ``gte`` lookups off the shelf set,
    which a converter dropping a trailing ``e`` names alike; the branch set lists no
    lookup of the copy, so the remedy names ``code`` on the shelf set.
    """
    with pytest.raises(ConfigurationError) as exc:
        _ = _flat_copy_schema(["gt", "gte"], {}, _StripTrailingE())

    assert str(exc.value).endswith(
        "FilterSet 'FlatBranchFilter' generates them from lookups 'gt' and 'gte'. Drop one "
        "from the Meta.fields lookup list of 'code' on FlatShelfFilter.",
    )
