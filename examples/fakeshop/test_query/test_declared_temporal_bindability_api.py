"""Declared temporal filters and resolver annotations use the real database's bind boundary.

Rung 3: one consumer FilterSet combines django-filter's temporal/range declarations,
package list/range filters, and F-expression annotations over the existing ScalarSpecimen.
The shipped generated field filters cannot express that combination. All requests use a
native connection over HTTP.
"""

import datetime
import uuid
from collections.abc import Sequence
from functools import wraps
from typing import NamedTuple

import pytest
import strawberry
from apps.scalars import models
from django import forms
from django.db import connection
from django.db.models import F, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django.utils import timezone
from django_filters import (
    BaseInFilter,
    CharFilter,
    DateFilter,
    DateFromToRangeFilter,
    DateTimeFilter,
    DateTimeFromToRangeFilter,
    Filter,
    NumberFilter,
    TimeFilter,
    TimeRangeFilter,
)
from graphql import GraphQLInputObjectType, get_named_type
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_object,
)
from strawberry import relay
from strawberry.types import Info
from strawberry.types.base import StrawberryObjectDefinition
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, ListFilter, RangeFilter, TypedFilter
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
_UNBINDABLE = [{"message": "Enter a value the database can represent.", "code": "invalid"}]
_NAIVE_DATE_WARNING = pytest.mark.filterwarnings(
    "ignore:DateTimeField .* received a naive datetime:RuntimeWarning",
)


class DatesInFilter(BaseInFilter, DateFilter):
    """A consumer CSV filter whose form cleans each member as a date, as django-filter documents."""


class DateTypedFilter(TypedFilter):
    """A consumer ``TypedFilter`` whose form cleans its value as a date."""

    field_class = forms.DateField


class ParentBuiltNumberFilter(NumberFilter):
    """A consumer ``NumberFilter`` whose form field is built only once a FilterSet binds it.

    ``field`` reads the bound set (``parent``) first, as django-filter's ``AllValuesFilter``
    reads its ``model``, so the class-level declaration builds no form field.
    """

    # Annotated only: the FilterSet instance binding the filter sets it.
    parent: FilterSet

    @property
    @override
    def field(self) -> forms.Field:
        _ = self.parent
        return super().field


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-declared-temporal/", _graphql_view)]


def _holder() -> tuple[DjangoSchema, type[DjangoType]]:
    """Use public declarations, with real queryset annotations returned by the consumer resolver."""

    class DeclaredTemporalFilter(FilterSet):
        taken_before = DateTimeFilter(field_name="occurred_at", lookup_expr="lt")
        taken_between = DateTimeFromToRangeFilter(field_name="occurred_at")
        timed_between = TimeRangeFilter(field_name="occurred_time")
        clock_time = TimeFilter(field_name="occurred_at__time")
        year_from = NumberFilter(field_name="occurred_at__year", lookup_expr="gte")
        bound_year_from = ParentBuiltNumberFilter(
            field_name="occurred_at__year",
            lookup_expr="gte",
        )
        year_of_day = DateFilter(field_name="occurred_on", lookup_expr="year")
        years_of_days = DatesInFilter(field_name="occurred_on", lookup_expr="year__in")
        years_of_day_span = DateFromToRangeFilter(field_name="occurred_on__year")
        typed_year_of_day = DateTypedFilter(field_name="occurred_on", lookup_expr="year")
        any_year_of_day = TypedFilter(field_name="occurred_on", lookup_expr="year")
        bare_year_of_day = Filter(field_name="occurred_on", lookup_expr="year")
        bare_day_year = Filter(field_name="occurred_on__year")
        text_year_of_day = CharFilter(field_name="occurred_on", lookup_expr="year")
        text_day_year = CharFilter(field_name="occurred_on__year")
        days_of_span = DateFromToRangeFilter(field_name="occurred_at__date")
        month_after = NumberFilter(field_name="occurred_at__month", lookup_expr="gt")
        taken_on = DateFilter(field_name="occurred_at")
        taken_among = ListFilter(field_name="occurred_at", lookup_expr="in")
        taken_span = RangeFilter(field_name="occurred_at", lookup_expr="range")
        own_before = DateTimeFilter(field_name="occurred_at", method="own_filter")
        stamped_before = DateTimeFilter(field_name="stamped_at", lookup_expr="lt")
        stamped_year_after = NumberFilter(field_name="stamped_at__year", lookup_expr="gt")
        clocked = TimeFilter(field_name="clocked_at")

        class Meta:
            model = models.ScalarSpecimen
            fields = {"occurred_on": ["year__in"]}

        def own_filter(
            self,
            queryset: QuerySet[models.ScalarSpecimen],
            _name: str,
            _value: object,
        ) -> QuerySet[models.ScalarSpecimen]:
            return queryset

    class DeclaredTemporalSpecimen(DjangoType):
        class Meta:
            model = models.ScalarSpecimen
            fields = ("label",)
            interfaces = (relay.Node,)
            filterset_class = DeclaredTemporalFilter

    finalize_django_types()

    @strawberry.type
    class Query:
        def _rows(self, _info: Info) -> QuerySet[models.ScalarSpecimen]:
            return models.ScalarSpecimen.objects.annotate(
                stamped_at=F("occurred_at"),
                clocked_at=F("occurred_time"),
            ).order_by("pk")

        rows: DjangoConnection[DeclaredTemporalSpecimen] = DjangoConnectionField(
            DeclaredTemporalSpecimen,
            resolver=_rows,
        )

    return DjangoSchema(query=Query, config=strawberry_config()), DeclaredTemporalSpecimen


def _input(schema: DjangoSchema) -> GraphQLInputObjectType:
    query = schema._schema.query_type
    assert query is not None
    named = get_named_type(graphql_type_of(graphql_fields(query)["rows"].args["filter"]))
    assert isinstance(named, GraphQLInputObjectType)
    return named


def _where(schema: DjangoSchema, python_path: Sequence[str], value: object) -> JSONObject:
    """Ask the published definitions and NameConverter for each input field's actual name."""
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
    for name in reversed(names[:-1]):
        result = {name: result}
    return result


def _case_input(schema: DjangoSchema, case: "_TemporalCase") -> JSONObject:
    if case.shape == "list":
        return _where(schema, case.path, list(case.values))
    if case.shape == "range-end":
        return _where(schema, (*case.path, "end"), case.values[0])
    if case.shape == "range-start":
        return _where(schema, (*case.path, "start"), case.values[0])
    if case.shape == "range-both":
        start = _where(schema, (*case.path, "start"), case.values[0])
        end = _where(schema, (*case.path, "end"), case.values[1])
        first = next(iter(start))
        # The two axes are on the same real range input; merge only the leaf object.
        start_bag = json_object(start, first)
        end_bag = json_object(end, first)
        operator = next(iter(start_bag))
        json_object(start_bag, operator).update(json_object(end_bag, operator))
        return start
    assert case.shape == "scalar"
    return _where(schema, case.path, case.values[0])


def _post(schema: DjangoSchema, where: JSONObject) -> JSONObject:
    document = (
        f"query($where: {_input(schema).name}!) {{ rows(filter: $where) "
        "{ edges { node { id label } } } }"
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                variables={"where": where},
                url="/graphql-declared-temporal/",
            )
    finally:
        _CURRENT["schema"] = None


def _seed() -> dict[str, models.ScalarSpecimen]:
    """Three distinct dates, months and clock times make each accepted filter observable."""
    return {
        label: models.ScalarSpecimen.objects.create(
            label=label,
            occurred_on=datetime.date.fromisoformat(stamp[:10]),
            occurred_at=datetime.datetime.fromisoformat(stamp),
            occurred_time=datetime.time.fromisoformat(clock),
            external_id=uuid.UUID(int=index),
        )
        for index, (label, stamp, clock) in enumerate(
            (
                ("early", "2020-01-10T08:00:00+00:00", "08:00:00"),
                ("match", "2021-06-15T00:00:00+00:00", "09:30:00"),
                ("late", "2022-11-20T15:45:00+00:00", "15:45:00"),
            ),
            start=1,
        )
    }


def _expected(
    row_type: type[DjangoType],
    rows: dict[str, models.ScalarSpecimen],
    labels: tuple[str, ...],
) -> JSONObject:
    return {
        "data": {
            "rows": {
                "edges": [
                    {
                        "node": {
                            "id": global_id_for(row_type, saved_pk(rows[label])),
                            "label": label,
                        },
                    }
                    for label in labels
                ],
            },
        },
    }


def _assert_unbindable(payload: JSONObject, form_key: str) -> None:
    assert payload["data"] is None, payload
    assert len(json_list(payload, "errors")) == 1
    assert json_at(payload, "errors", 0, "path") == ["rows"]
    assert json_at(payload, "errors", 0, "message") == "Invalid filter input"
    assert json_at(payload, "errors", 0, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {form_key: _UNBINDABLE},
    }


class _TemporalCase(NamedTuple):
    """One actual input spelling, expected form-key boundary and explicit result on this backend."""

    path: tuple[str, str]
    values: tuple[str | int, ...]
    shape: str
    form_key: str
    refused: str
    labels: tuple[str, ...]


_BEFORE_YEAR_ONE = "0001-01-01T00:00:00+05:00"
_PAST_YEAR_9999 = "9999-12-31T23:00:00-05:00"
_MATCH = "2021-06-15T00:00:00+00:00"
_CUTOFF = "2021-06-16T00:00:00+00:00"
_REFUSALS = {
    "declared": _TemporalCase(
        ("taken_before", "lt"),
        (_BEFORE_YEAR_ONE,),
        "scalar",
        "taken_before",
        "non-postgresql",
        (),
    ),
    "declared-range-lone-bound": _TemporalCase(
        ("taken_between", "exact"),
        (_PAST_YEAR_9999,),
        "range-start",
        "taken_between",
        "non-postgresql",
        (),
    ),
    "declared-time-range": _TemporalCase(
        ("timed_between", "exact"),
        ("01:00:00", "09:30:00+00:00"),
        "range-both",
        "timed_between",
        "non-postgresql",
        ("early", "match"),
    ),
    "time-transform": _TemporalCase(
        ("clock_time", "exact"),
        ("09:30:00+00:00",),
        "scalar",
        "clock_time",
        "non-postgresql",
        (),
    ),
    "annotation": _TemporalCase(
        ("stamped_before", "lt"),
        (_BEFORE_YEAR_ONE,),
        "scalar",
        "stamped_before",
        "non-postgresql",
        (),
    ),
    "annotation-year": _TemporalCase(
        ("stamped_year_after", "gt"),
        ("10000",),
        "scalar",
        "stamped_year_after",
        "all",
        (),
    ),
    "time-annotation": _TemporalCase(
        ("clocked", "exact"),
        ("09:30:00+00:00",),
        "scalar",
        "clocked",
        "non-postgresql",
        ("match",),
    ),
    "list-element": _TemporalCase(
        ("taken_among", "in_"),
        (_MATCH, _BEFORE_YEAR_ONE),
        "list",
        "taken_among",
        "non-postgresql",
        ("match",),
    ),
    "range-bound": _TemporalCase(
        ("taken_span", "range"),
        (_MATCH, _PAST_YEAR_9999),
        "range-both",
        "taken_span",
        "non-postgresql",
        ("match", "late"),
    ),
    "year-in-field-name": _TemporalCase(
        ("year_from", "gte"),
        (10000,),
        "scalar",
        "year_from",
        "all",
        (),
    ),
    "year-of-a-date": _TemporalCase(
        ("year_of_day", "year"),
        ("2021-01-01",),
        "scalar",
        "year_of_day",
        "all",
        (),
    ),
    "years-of-csv-dates": _TemporalCase(
        ("years_of_days", "year__in"),
        ("2021-01-01",),
        "list",
        "years_of_days",
        "all",
        (),
    ),
    "year-span-of-dates": _TemporalCase(
        ("years_of_day_span", "exact"),
        ("2021-01-01",),
        "range-start",
        "years_of_day_span",
        "all",
        (),
    ),
    "typed-year-of-a-date": _TemporalCase(
        ("typed_year_of_day", "year"),
        ("2021-01-01",),
        "scalar",
        "typed_year_of_day",
        "all",
        (),
    ),
}
_ACCEPTED = {
    "declared": _TemporalCase(
        ("taken_before", "lt"),
        (_CUTOFF,),
        "scalar",
        "taken_before",
        "none",
        ("early", "match"),
    ),
    "declared-range": _TemporalCase(
        ("taken_between", "exact"),
        (_MATCH,),
        "range-end",
        "taken_between",
        "none",
        ("early", "match"),
    ),
    "declared-time-range": _TemporalCase(
        ("timed_between", "exact"),
        ("09:30:00",),
        "range-end",
        "timed_between",
        "none",
        ("early", "match"),
    ),
    "time-transform": _TemporalCase(
        ("clock_time", "exact"),
        ("00:00:00",),
        "scalar",
        "clock_time",
        "none",
        ("match",),
    ),
    "date-on-a-datetime-column": _TemporalCase(
        ("taken_on", "exact"),
        (_MATCH,),
        "scalar",
        "taken_on",
        "none",
        ("match",),
    ),
    "unknown-transform": _TemporalCase(
        ("month_after", "gt"),
        (5,),
        "scalar",
        "month_after",
        "none",
        ("match", "late"),
    ),
    "list-element": _TemporalCase(
        ("taken_among", "in_"),
        (_MATCH,),
        "list",
        "taken_among",
        "none",
        ("match",),
    ),
    "range-bound": _TemporalCase(
        ("taken_span", "range"),
        (_MATCH,),
        "range-end",
        "taken_span",
        "none",
        ("early", "match"),
    ),
    "year-in-field-name": _TemporalCase(
        ("year_from", "gte"),
        (2021,),
        "scalar",
        "year_from",
        "none",
        ("match", "late"),
    ),
    "own-method": _TemporalCase(
        ("own_before", "exact"),
        (_BEFORE_YEAR_ONE,),
        "scalar",
        "own_before",
        "none",
        ("early", "match", "late"),
    ),
    "annotation": _TemporalCase(
        ("stamped_before", "lt"),
        (_CUTOFF,),
        "scalar",
        "stamped_before",
        "none",
        ("early", "match"),
    ),
    "annotation-year": _TemporalCase(
        ("stamped_year_after", "gt"),
        ("2020",),
        "scalar",
        "stamped_year_after",
        "none",
        ("match", "late"),
    ),
    "time-annotation": _TemporalCase(
        ("clocked", "exact"),
        ("09:30:00",),
        "scalar",
        "clocked",
        "none",
        ("match",),
    ),
    "generated-year-in": _TemporalCase(
        ("occurred_on_year_in", "year__in"),
        (2021, 2022),
        "list",
        "occurred_on__year__in",
        "none",
        ("match", "late"),
    ),
    "date-span-of-a-datetime": _TemporalCase(
        ("days_of_span", "exact"),
        ("2021-06-15", "2022-12-31"),
        "range-both",
        "days_of_span",
        "none",
        ("match", "late"),
    ),
    "pass-through-typed-year": _TemporalCase(
        ("any_year_of_day", "year"),
        (2021,),
        "scalar",
        "any_year_of_day",
        "none",
        ("match",),
    ),
    "pass-through-year-lookup": _TemporalCase(
        ("bare_year_of_day", "year"),
        (2021,),
        "scalar",
        "bare_year_of_day",
        "none",
        ("match",),
    ),
    "pass-through-year-in-field-name": _TemporalCase(
        ("bare_day_year", "exact"),
        (2021,),
        "scalar",
        "bare_day_year",
        "none",
        ("match",),
    ),
    "text-year-lookup": _TemporalCase(
        ("text_year_of_day", "year"),
        ("2021",),
        "scalar",
        "text_year_of_day",
        "none",
        ("match",),
    ),
    "text-year-in-field-name": _TemporalCase(
        ("text_day_year", "exact"),
        ("2021",),
        "scalar",
        "text_day_year",
        "none",
        ("match",),
    ),
}


def _request_case(case: _TemporalCase, record_compiled_sql: RecordCompiledSql) -> None:
    rows = _seed()
    schema, row_type = _holder()
    sqls = record_compiled_sql()
    payload = _post(schema, _case_input(schema, case))
    refused = case.refused == "all" or (
        case.refused == "non-postgresql" and connection.vendor != "postgresql"
    )
    root_sql = [sql for sql in sqls if '"scalars_scalarspecimen"' in sql]
    if refused:
        _assert_unbindable(payload, case.form_key)
        assert root_sql == [], sqls
        return
    assert payload == _expected(row_type, rows, case.labels), payload
    assert len(root_sql) == 1, sqls


@pytest.mark.django_db
@pytest.mark.parametrize("case", _REFUSALS)
def test_declared_temporal_filters_check_the_value_their_form_will_bind(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Every declared family refuses under its own form key before row SQL, or binds on real PG."""
    with override_settings(TIME_ZONE="UTC", USE_TZ=True), timezone.override("UTC"):
        _request_case(_REFUSALS[case], record_compiled_sql)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            case,
            id=case,
            marks=_NAIVE_DATE_WARNING if case == "date-on-a-datetime-column" else (),
        )
        for case in _ACCEPTED
    ],
)
def test_declared_temporal_filters_return_the_rows_their_cleaned_values_match(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Each bindable control selects populated rows, while the owned method retains all three."""
    with override_settings(TIME_ZONE="UTC", USE_TZ=True), timezone.override("UTC"):
        _request_case(_ACCEPTED[case], record_compiled_sql)


@pytest.mark.django_db
@_NAIVE_DATE_WARNING
def test_a_date_filter_on_a_datetime_checks_the_actual_timezone_projection(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The DateTime wire value is cleaned to a date whose Tokyo midnight reaches year zero UTC."""
    case = _TemporalCase(
        ("taken_on", "exact"),
        ("0001-01-01T00:00:00+00:00",),
        "scalar",
        "taken_on",
        "non-postgresql",
        (),
    )
    with override_settings(TIME_ZONE="Asia/Tokyo", USE_TZ=True), timezone.override("Asia/Tokyo"):
        _request_case(case, record_compiled_sql)


def _leaf_type_name(schema: DjangoSchema, python_path: tuple[str, str]) -> str:
    """Return the published scalar of one operator-bag leaf, named as the wire names it."""
    where = _where(schema, python_path, None)
    head = next(iter(where))
    lookup = next(iter(json_object(where, head)))
    bag = get_named_type(graphql_type_of(graphql_input_fields(_input(schema))[head]))
    assert isinstance(bag, GraphQLInputObjectType)
    return get_named_type(graphql_type_of(graphql_input_fields(bag)[lookup])).name


def _range_axis_type_names(schema: DjangoSchema, python_path: tuple[str, str]) -> set[str]:
    """Return the published scalars of a range leaf's ``start`` / ``end`` axes."""
    where = _where(schema, python_path, None)
    head = next(iter(where))
    lookup = next(iter(json_object(where, head)))
    bag = get_named_type(graphql_type_of(graphql_input_fields(_input(schema))[head]))
    assert isinstance(bag, GraphQLInputObjectType)
    axes = get_named_type(graphql_type_of(graphql_input_fields(bag)[lookup]))
    assert isinstance(axes, GraphQLInputObjectType)
    return {
        get_named_type(graphql_type_of(field)).name
        for field in graphql_input_fields(axes).values()
    }


@pytest.mark.django_db
def test_a_form_field_built_per_request_leaves_the_transform_output_to_type_the_leaf() -> None:
    """A filter past ``year`` whose form field needs its bound set takes the output's Int.

    The class-level declaration builds no form field, so nothing says its form cleans
    another kind; the bound filter's ``NumberFilter`` form cleans the year it is sent.
    """
    rows = _seed()
    schema, row_type = _holder()
    assert _leaf_type_name(schema, ("bound_year_from", "gte")) == "Int"
    payload = _post(schema, _where(schema, ("bound_year_from", "gte"), 2021))
    assert payload == _expected(row_type, rows, ("match", "late")), payload


@pytest.mark.django_db
def test_a_declared_filter_past_a_transform_publishes_what_its_own_form_cleans() -> None:
    """A DateFilter on ``year`` binds a DateField, so it takes a Date; a NumberFilter keeps Int.

    A Date CSV member and a Date range axis on ``year`` follow the same rule; each
    refuses its date under its own form key (``_REFUSALS``), where an Int would reach a
    form that cannot clean it.
    """
    schema, _row_type = _holder()
    assert _leaf_type_name(schema, ("year_of_day", "year")) == "Date"
    assert _leaf_type_name(schema, ("year_from", "gte")) == "Int"
    # A ``TypedFilter`` follows the rule too: a date-cleaning form takes Date, while the bare
    # ``forms.Field`` (``TypedFilter`` / ``Filter``) hands the lookup the value as sent, so it
    # keeps Int; a ``CharFilter`` cleans text, so it takes String. Both spellings agree.
    assert _leaf_type_name(schema, ("typed_year_of_day", "year")) == "Date"
    assert _leaf_type_name(schema, ("any_year_of_day", "year")) == "Int"
    assert _leaf_type_name(schema, ("bare_year_of_day", "year")) == "Int"
    assert _leaf_type_name(schema, ("bare_day_year", "exact")) == "Int"
    assert _leaf_type_name(schema, ("text_year_of_day", "year")) == "String"
    assert _leaf_type_name(schema, ("text_day_year", "exact")) == "String"
    # The containers follow the same rule: a CSV member and a range axis.
    assert _leaf_type_name(schema, ("years_of_days", "year__in")) == "Date"
    assert _range_axis_type_names(schema, ("years_of_day_span", "exact")) == {"Date"}
    # A generated ``year__in`` filter is built from the transform's output, so it keeps Int,
    # and a DateTime range past ``date`` cleans a datetime, which is a date: it keeps Date.
    assert _leaf_type_name(schema, ("occurred_on_year_in", "year__in")) == "Int"
    assert _range_axis_type_names(schema, ("days_of_span", "exact")) == {"Date"}
    where = _where(schema, ("year_of_day", "year"), 2021)
    head = next(iter(where))
    lookup = next(iter(json_object(where, head)))
    payload = _post(schema, where)
    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "message") == (
        f"Variable '$where' got invalid value 2021 at 'where.{head}.{lookup}'; "
        'Value cannot represent a Date: "2021". Expected a string.'
    ), payload
