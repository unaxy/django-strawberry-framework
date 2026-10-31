"""Consumer calendar arguments reach temporal filtering without a generated filter argument.

A year-search consumer accepts CSV text or BigInt bounds, and a calendar consumer accepts
DateTime values for its date/time columns. Their ordinary resolvers call the public
FilterSet apply entry point or its public queryset property over real ScalarSpecimen rows.
An explicitly declared ISO-year input carries its operator through Strawberry's ordinary
input dataclass, while each one-lookup head accepts its scalar or sequence directly.
The temporal declarations keep their upstream Django form parsing and lookup semantics.
"""

from __future__ import annotations

import datetime
import uuid
from collections.abc import Mapping, Sequence
from functools import wraps
from typing import NamedTuple

import django_filters
import pytest
import strawberry
from apps.scalars import models as scalar_models
from django.db import connection
from django.db import models as django_models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django.utils import timezone
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_object,
)
from strawberry import relay
from strawberry.django.context import StrawberryDjangoContext
from strawberry.types import Info
from strawberry.types.base import StrawberryObjectDefinition

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, ListFilter, RangeFilter
from django_strawberry_framework.scalars import BigInt
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import is_queryset, require
from django_strawberry_framework.utils.typing import graphql_fields, graphql_type_of
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_UNBINDABLE = [{"message": "Enter a value the database can represent.", "code": "invalid"}]
_NAIVE_DATE_WARNING = pytest.mark.filterwarnings(
    "ignore:DateTimeField .* received a naive datetime:RuntimeWarning",
)


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-calendar-search/", _graphql_view)]


def _temporal_filter_class() -> type[FilterSet]:
    """A specimen filterset reaching the temporal columns through every filter family.

    django-filter's declared filters (a ``DateTimeFilter``, its datetime and time range
    filters, a ``TimeFilter`` and a ``NumberFilter`` whose ``field_name`` carries the
    ``time`` / ``year`` transform or a ``month`` one, a ``DateFilter`` on the datetime
    column, a ``DateTimeFilter`` over its ``date`` transform and a ``DateTimeFilter`` on
    the time column), the package's ``ListFilter`` /
    ``RangeFilter``, opted-in ``Meta.fields`` year leaves (``year`` / ``iso_year`` ``in``
    and ``range`` among them, on the datetime and the date column), a filter with its own
    ``method``, ones over a datetime and a time annotation the queryset adds (the
    datetime one through ``year`` too), one over an annotation whose output field
    Django cannot resolve, and one over ``pk``, which Django reads as the primary key.
    """

    class SpecimenFilter(FilterSet):
        taken_before = django_filters.DateTimeFilter(field_name="occurred_at", lookup_expr="lt")
        taken_between = django_filters.DateTimeFromToRangeFilter(field_name="occurred_at")
        timed_between = django_filters.TimeRangeFilter(field_name="occurred_time")
        clock_time = django_filters.TimeFilter(field_name="occurred_at__time")
        year_from = django_filters.NumberFilter(field_name="occurred_at__year", lookup_expr="gte")
        year_of_day = django_filters.DateFilter(field_name="occurred_on", lookup_expr="year")
        month_after = django_filters.NumberFilter(
            field_name="occurred_at__month",
            lookup_expr="gt",
        )
        taken_on = django_filters.DateFilter(field_name="occurred_at")
        taken_on_day_of = django_filters.DateTimeFilter(
            field_name="occurred_at",
            lookup_expr="date",
        )
        timed_at = django_filters.DateTimeFilter(field_name="occurred_time")
        taken_among = ListFilter(field_name="occurred_at", lookup_expr="in")
        taken_span = RangeFilter(field_name="occurred_at", lookup_expr="range")
        own_before = django_filters.DateTimeFilter(field_name="occurred_at", method="own_filter")
        stamped_before = django_filters.DateTimeFilter(field_name="stamped_at", lookup_expr="lt")
        stamped_year_after = django_filters.NumberFilter(
            field_name="stamped_at__year",
            lookup_expr="gt",
        )
        clocked = django_filters.TimeFilter(field_name="clocked_at")
        mixed_below = django_filters.NumberFilter(field_name="mixed", lookup_expr="lt")
        by_pk = django_filters.NumberFilter(field_name="pk")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {
                "occurred_at": [
                    "exact",
                    "year__gt",
                    "year__lt",
                    "iso_year",
                    "year__in",
                    "year__range",
                    "iso_year__in",
                    "iso_year__range",
                ],
                "occurred_on": [
                    "year",
                    "iso_year__lte",
                    "year__in",
                    "year__range",
                    "iso_year__in",
                    "iso_year__range",
                ],
            }

        def own_filter(
            self,
            queryset: QuerySet[scalar_models.ScalarSpecimen],
            _name: str,
            _value: object,
        ) -> QuerySet[scalar_models.ScalarSpecimen]:
            return queryset

    return SpecimenFilter


class _DateInFilter(django_filters.BaseInFilter, django_filters.DateFilter):
    """django-filter's comma-separated ``in`` filter over dates."""


class _DateTimeInFilter(django_filters.BaseInFilter, django_filters.DateTimeFilter):
    """django-filter's comma-separated ``in`` filter over datetimes."""


class _InheritingDateTimeFilter(django_filters.DateTimeFilter):
    """A consumer subclass of ``DateTimeFilter`` that keeps django-filter's ``filter``."""


def _cross_kind_filter_class() -> type[FilterSet]:
    """A specimen filterset whose declared filters clean a value of another kind than their column.

    A ``DateFilter`` on the datetime column (``exact``, ``lt``, an ``in`` list and a
    ``DateFromToRangeFilter``); a ``DateTimeFilter`` on the date column (``exact``, ``gte``,
    an ``in`` list and a ``DateTimeFromToRangeFilter``); a ``DateTimeFilter`` through the
    datetime column's ``date`` transform (``date``, ``date__gte``, ``date__in`` and a
    ``DateTimeFromToRangeFilter`` over ``occurred_at__date``); and a consumer subclass of
    ``DateTimeFilter`` through the same transform keeping django-filter's ``filter``.
    """

    class CrossKindFilter(FilterSet):
        on_instant = django_filters.DateFilter(field_name="occurred_at")
        on_instant_before = django_filters.DateFilter(field_name="occurred_at", lookup_expr="lt")
        on_instant_among = _DateInFilter(field_name="occurred_at", lookup_expr="in")
        on_instant_between = django_filters.DateFromToRangeFilter(field_name="occurred_at")
        instant_on_day = django_filters.DateTimeFilter(field_name="occurred_on")
        instant_on_day_from = django_filters.DateTimeFilter(
            field_name="occurred_on",
            lookup_expr="gte",
        )
        instants_on_day = _DateTimeInFilter(field_name="occurred_on", lookup_expr="in")
        instants_on_day_between = django_filters.DateTimeFromToRangeFilter(
            field_name="occurred_on",
        )
        instant_day_of = django_filters.DateTimeFilter(
            field_name="occurred_at",
            lookup_expr="date",
        )
        instant_day_of_from = django_filters.DateTimeFilter(
            field_name="occurred_at",
            lookup_expr="date__gte",
        )
        instants_day_of = _DateTimeInFilter(field_name="occurred_at", lookup_expr="date__in")
        instants_day_of_between = django_filters.DateTimeFromToRangeFilter(
            field_name="occurred_at__date",
        )
        inheriting_day_of = _InheritingDateTimeFilter(field_name="occurred_at", lookup_expr="date")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    return CrossKindFilter


def _stamped_rows() -> QuerySet[scalar_models.ScalarSpecimen]:
    return scalar_models.ScalarSpecimen.objects.annotate(
        stamped_at=django_models.F("occurred_at"),
        clocked_at=django_models.F("occurred_time"),
    ).order_by("pk")


def _put(
    data: JSONObject,
    head: str,
    lookup: str,
    value: object,
) -> None:
    if value is not None:
        if head not in data:
            data[head] = {}
        json_object(data, head)[lookup] = value


@strawberry.input
class CalendarYear:
    """A consumer's ISO-year operator, carried by Strawberry's real input dataclass."""

    iso_year: BigInt


def _schema() -> tuple[DjangoSchema, type[DjangoType]]:
    """Normal scalar arguments feed the consumer's own filter classes over a plain output type."""
    temporal = _temporal_filter_class()
    calendar = _cross_kind_filter_class()

    class CalendarSpecimen(DjangoType):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = ("label",)
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        def _year_search(
            self,
            info: Info[StrawberryDjangoContext, object],
            datetime_years_csv: str | None = None,
            datetime_year_range_csv: str | None = None,
            datetime_iso_years_csv: str | None = None,
            datetime_iso_year_range_csv: str | None = None,
            date_years_csv: str | None = None,
            date_year_range_csv: str | None = None,
            date_iso_years_csv: str | None = None,
            date_iso_year_range_csv: str | None = None,
        ) -> QuerySet[django_models.Model, object]:
            values = (
                (datetime_years_csv, "occurred_at__year__in"),
                (datetime_year_range_csv, "occurred_at__year__range"),
                (datetime_iso_years_csv, "occurred_at__iso_year__in"),
                (datetime_iso_year_range_csv, "occurred_at__iso_year__range"),
                (date_years_csv, "occurred_on__year__in"),
                (date_year_range_csv, "occurred_on__year__range"),
                (date_iso_years_csv, "occurred_on__iso_year__in"),
                (date_iso_year_range_csv, "occurred_on__iso_year__range"),
            )
            data = {name: value for value, name in values if value is not None}
            return require(
                temporal(data=data, queryset=_stamped_rows(), request=info.context.request).qs,
                is_queryset,
            )

        year_search: QuerySet[django_models.Model, object] = strawberry.field(
            resolver=_year_search,
            graphql_type=list[CalendarSpecimen],
        )

        def _year_values(
            self,
            info: Info[StrawberryDjangoContext, object],
            *,
            datetime_year_gt: BigInt | None = None,
            datetime_year_lt: BigInt | None = None,
            datetime_iso_year: CalendarYear | None = None,
            date_year: BigInt | None = None,
            date_iso_year_lte: BigInt | None = None,
            datetime_years: list[BigInt] | None = None,
            date_years: list[BigInt] | None = None,
            date_iso_years: list[BigInt] | None = None,
            datetime_year_range: list[BigInt] | None = None,
            date_iso_year_range: list[BigInt] | None = None,
        ) -> QuerySet[django_models.Model, object]:
            data: JSONObject = {}
            for value, head in (
                (datetime_year_gt, "occurred_at__year__gt"),
                (datetime_year_lt, "occurred_at__year__lt"),
                (datetime_iso_year, "occurred_at"),
                (date_iso_year_lte, "occurred_on__iso_year__lte"),
                (datetime_years, "occurred_at__year__in"),
                (date_years, "occurred_on__year__in"),
                (date_iso_years, "occurred_on__iso_year__in"),
                (datetime_year_range, "occurred_at__year__range"),
                (date_iso_year_range, "occurred_on__iso_year__range"),
            ):
                if value is not None:
                    data[head] = value
            _put(data, "occurred_on", "year", date_year)
            return temporal.apply_sync(data, _stamped_rows(), info)

        year_values: QuerySet[django_models.Model, object] = strawberry.field(
            resolver=_year_values,
            graphql_type=list[CalendarSpecimen],
        )

        def _integer_key(
            self,
            info: Info[StrawberryDjangoContext, object],
            key: BigInt,
        ) -> QuerySet[django_models.Model, object]:
            return temporal.apply_sync({"by_pk": {"exact": key}}, _stamped_rows(), info)

        integer_key: QuerySet[django_models.Model, object] = strawberry.field(
            resolver=_integer_key,
            graphql_type=list[CalendarSpecimen],
        )

        def _calendar_dates(
            self,
            info: Info[StrawberryDjangoContext, object],
            *,
            at_date_time: datetime.datetime | None = None,
            at_or_after_date_time: datetime.datetime | None = None,
            date_times: list[datetime.datetime] | None = None,
            date_time_start: datetime.datetime | None = None,
            instant_date: datetime.date | None = None,
            instant_before_date: datetime.date | None = None,
            instant_dates: list[datetime.date] | None = None,
            instant_date_start: datetime.date | None = None,
            instant_day_of: datetime.datetime | None = None,
            instant_day_of_from: datetime.datetime | None = None,
            instants_day_of: list[datetime.datetime] | None = None,
            instant_day_of_start: datetime.datetime | None = None,
            instant_day_of_end: datetime.datetime | None = None,
            inheriting_day_of: datetime.datetime | None = None,
            empty_root: bool = False,
        ) -> QuerySet[django_models.Model, object]:
            data: JSONObject = {}
            _put(data, "instant_on_day", "exact", at_date_time)
            _put(data, "instant_on_day_from", "gte", at_or_after_date_time)
            _put(data, "instants_on_day", "in_", date_times)
            if date_time_start is not None:
                _put(data, "instants_on_day_between", "exact", {"start": date_time_start})
            _put(data, "on_instant", "exact", instant_date)
            _put(data, "on_instant_before", "lt", instant_before_date)
            _put(data, "on_instant_among", "in_", instant_dates)
            if instant_date_start is not None:
                _put(data, "on_instant_between", "exact", {"start": instant_date_start})
            _put(data, "instant_day_of", "date", instant_day_of)
            if instant_day_of_from is not None:
                data["instant_day_of_from"] = instant_day_of_from
            if instants_day_of is not None:
                data["instants_day_of"] = instants_day_of
            day_bounds = {
                key: value
                for key, value in (("start", instant_day_of_start), ("end", instant_day_of_end))
                if value is not None
            }
            if day_bounds:
                _put(data, "instants_day_of_between", "exact", day_bounds)
            _put(data, "inheriting_day_of", "date", inheriting_day_of)
            queryset = scalar_models.ScalarSpecimen.objects.order_by("pk")
            if empty_root:
                queryset = queryset.none()
            return calendar.apply_sync(data, queryset, info)

        calendar_dates: QuerySet[django_models.Model, object] = strawberry.field(
            resolver=_calendar_dates,
            graphql_type=list[CalendarSpecimen],
        )

        def _clock(
            self,
            info: Info[StrawberryDjangoContext, object],
            moment: datetime.datetime,
        ) -> QuerySet[django_models.Model, object]:
            return temporal.apply_sync(
                {"timed_at": {"exact": moment}},
                _stamped_rows(),
                info,
            )

        clock: QuerySet[django_models.Model, object] = strawberry.field(
            resolver=_clock,
            graphql_type=list[CalendarSpecimen],
        )

        def _before_text(
            self,
            info: Info[StrawberryDjangoContext, object],
            upper_text: str,
        ) -> QuerySet[django_models.Model, object]:
            # django-filter's DateTimeRangeField owns parsing this string, including
            # its fractional-second offset. The consumer does not parse or normalize it.
            return temporal.apply_sync(
                {"taken_between": {"exact": {"end": upper_text}}},
                _stamped_rows(),
                info,
            )

        before_text: QuerySet[django_models.Model, object] = strawberry.field(
            resolver=_before_text,
            graphql_type=list[CalendarSpecimen],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return (
        DjangoSchema(query=Query, config=strawberry_config(), extensions=[lambda: optimizer]),
        CalendarSpecimen,
    )


def _post(schema: DjangoSchema, root: str, arguments: Mapping[str, object]) -> JSONObject:
    query = schema._schema.query_type
    assert query is not None
    definition = schema.get_type_by_name(query.name)
    assert isinstance(definition, StrawberryObjectDefinition)
    field = next(field for field in definition.fields if field.python_name == root)
    root_name = schema.config.name_converter.from_field(field)
    field_arguments = graphql_fields(query)[root_name].args
    definitions: list[str] = []
    supplied: list[str] = []
    variables: JSONObject = {}
    for index, (python_name, value) in enumerate(arguments.items()):
        argument = next(arg for arg in field.arguments if arg.python_name == python_name)
        name = schema.config.name_converter.from_argument(argument)
        variable = f"v{index}"
        definitions.append(f"${variable}: {graphql_type_of(field_arguments[name])}")
        supplied.append(f"{name}: ${variable}")
        variables[variable] = value
    document = (
        f"query({', '.join(definitions)}) {{ rows: {root_name}({', '.join(supplied)}) "
        "{ id label } }"
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                variables=variables,
                url="/graphql-calendar-search/",
            )
    finally:
        _CURRENT["schema"] = None


def _expected(
    schema: DjangoSchema,
    row_type: type[DjangoType],
    rows: Mapping[str, scalar_models.ScalarSpecimen],
    labels: Sequence[str],
) -> JSONObject:
    return {
        "data": {
            "rows": [
                {
                    "id": global_id_for(row_type, saved_pk(rows[label]), schema=schema),
                    "label": label,
                }
                for label in labels
            ],
        },
    }


def _assert_refusal(payload: JSONObject, form_key: str) -> None:
    assert payload["data"] is None, payload
    assert len(json_list(payload, "errors")) == 1
    assert json_at(payload, "errors", 0, "path") == ["rows"]
    assert json_at(payload, "errors", 0, "message") == "Invalid filter input"
    assert json_at(payload, "errors", 0, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {form_key: _UNBINDABLE},
    }


def _root_sql(sqls: Sequence[str]) -> list[str]:
    return [
        sql
        for sql in sqls
        if sql.lstrip().upper().startswith("SELECT ")
        and " FROM " in sql
        and sql.split(" FROM ", 1)[1].startswith('"scalars_scalarspecimen"')
    ]


def _specimen(
    label: str,
    day: datetime.date,
    *,
    moment: datetime.datetime | None = None,
    clock: datetime.time | None = None,
) -> scalar_models.ScalarSpecimen:
    return scalar_models.ScalarSpecimen.objects.create(
        label=label,
        occurred_on=day,
        occurred_at=moment
        or datetime.datetime.combine(day, datetime.time(12), datetime.timezone.utc),
        occurred_time=clock if clock is not None else datetime.time(12),
        external_id=uuid.UUID(int=day.toordinal()),
    )


def _year_rows() -> dict[str, scalar_models.ScalarSpecimen]:
    days = {
        "mid-2019": datetime.date(2019, 6, 15),
        "mid-2020": datetime.date(2020, 6, 15),
        "new-year-2021": datetime.date(2021, 1, 1),
        "mid-2022": datetime.date(2022, 6, 15),
        "mid-9998": datetime.date(9998, 6, 15),
    }
    return {label: _specimen(label, day) for label, day in days.items()}


def _calendar_rows() -> dict[str, scalar_models.ScalarSpecimen]:
    return {
        "early": _specimen(
            "early",
            datetime.date(2020, 1, 10),
            moment=datetime.datetime(2020, 1, 10, 8, tzinfo=datetime.timezone.utc),
            clock=datetime.time(8),
        ),
        "match": _specimen(
            "match",
            datetime.date(2021, 6, 15),
            moment=datetime.datetime(2021, 6, 15, 9, 30, tzinfo=datetime.timezone.utc),
            clock=datetime.time(9, 30),
        ),
        "late": _specimen(
            "late",
            datetime.date(2022, 11, 20),
            moment=datetime.datetime(2022, 11, 20, 15, 45, tzinfo=datetime.timezone.utc),
            clock=datetime.time(15, 45),
        ),
    }


def _cross_kind_rows() -> dict[str, scalar_models.ScalarSpecimen]:
    return {
        "early": _specimen("early", datetime.date(2020, 1, 10)),
        "midnight-utc": _specimen(
            "midnight-utc",
            datetime.date(2021, 6, 15),
            moment=datetime.datetime(2021, 6, 15, tzinfo=datetime.timezone.utc),
        ),
        "midnight-tokyo": _specimen(
            "midnight-tokyo",
            datetime.date(2021, 6, 16),
            moment=datetime.datetime(2021, 6, 14, 15, tzinfo=datetime.timezone.utc),
        ),
        "late": _specimen("late", datetime.date(2022, 11, 20)),
    }


class _YearSearchCase(NamedTuple):
    """An original generated CSV declaration and its exact stored-row answer."""

    argument: str
    value: str
    labels: tuple[str, ...]
    #: Root statements the search issues: a membership every member of which is dropped
    #: (a fractional year names no year) matches nothing without querying.
    root_queries: int = 1


_YEAR_SEARCH = {
    "datetime-year-in": _YearSearchCase(
        "datetime_years_csv",
        "2020,2022",
        ("mid-2020", "mid-2022"),
    ),
    "datetime-year-range": _YearSearchCase(
        "datetime_year_range_csv",
        "2020,2021",
        ("mid-2020", "new-year-2021"),
    ),
    "datetime-iso-year-in": _YearSearchCase(
        "datetime_iso_years_csv",
        "2020",
        ("mid-2020", "new-year-2021"),
    ),
    "datetime-iso-year-range": _YearSearchCase(
        "datetime_iso_year_range_csv",
        "2021,2022",
        ("mid-2022",),
    ),
    "date-year-in": _YearSearchCase("date_years_csv", "2021", ("new-year-2021",)),
    "date-year-range": _YearSearchCase(
        "date_year_range_csv",
        "2019,2020",
        ("mid-2019", "mid-2020"),
    ),
    "date-iso-year-in": _YearSearchCase(
        "date_iso_years_csv",
        "2020",
        ("mid-2020", "new-year-2021"),
    ),
    "date-iso-year-range": _YearSearchCase(
        "date_iso_year_range_csv",
        "2020,2020",
        ("mid-2020", "new-year-2021"),
    ),
    "years-no-row-holds": _YearSearchCase("datetime_years_csv", "0,10000", ()),
    "fractional-year-names-none": _YearSearchCase("datetime_years_csv", "2020.5", (), 0),
    "fractional-year-dropped": _YearSearchCase(
        "datetime_years_csv",
        "2020.5,2022",
        ("mid-2022",),
    ),
}


class _RefusedYear(NamedTuple):
    """One scalar argument reaching a generated filter's original typed refusal."""

    arguments: JSONObject
    form_key: str


_YEAR_REFUSALS = {
    "year-gt-0": _RefusedYear({"datetime_year_gt": "0"}, "occurred_at__year__gt"),
    "year-lt-10000": _RefusedYear({"datetime_year_lt": "10000"}, "occurred_at__year__lt"),
    "year-past-int-reach-of-a-date": _RefusedYear(
        {"datetime_year_gt": str(10**40)},
        "occurred_at__year__gt",
    ),
    "iso-9999": _RefusedYear(
        {"datetime_iso_year": {"isoYear": "9999"}},
        "occurred_at__iso_year",
    ),
    "date-year": _RefusedYear({"date_year": "10000"}, "occurred_on__year"),
    "generated-year-in-member-past-int64": _RefusedYear(
        {"datetime_years": ["2020", str(2**63)]},
        "occurred_at__year__in",
    ),
    "generated-date-iso-year-in-member-past-int64": _RefusedYear(
        {"date_iso_years": [str(2**63)]},
        "occurred_on__iso_year__in",
    ),
    "generated-year-range-bound-past-int64": _RefusedYear(
        {"datetime_year_range": ["2020", str(2**63)]},
        "occurred_at__year__range",
    ),
    "generated-date-iso-year-range-bound-10000": _RefusedYear(
        {"date_iso_year_range": ["2020", "10000"]},
        "occurred_on__iso_year__range",
    ),
    "date-iso-year": _RefusedYear({"date_iso_year_lte": "9999"}, "occurred_on__iso_year__lte"),
}
_YEAR_ACCEPTED = {
    "year-gt": (
        {"datetime_year_gt": "1"},
        (
            "mid-2019",
            "mid-2020",
            "new-year-2021",
            "mid-2022",
            "mid-9998",
        ),
    ),
    "iso-year": ({"datetime_iso_year": {"isoYear": "9998"}}, ("mid-9998",)),
    "year-in-binds-integers": ({"date_years": ["0", "10000"]}, ()),
}


_BEFORE_YEAR_ONE = "0001-01-01T00:00:00+05:00"
_PAST_YEAR_9999 = "9999-12-31T23:00:00-05:00"
_CROSS_REFUSALS = {
    "datetime-on-date-before-year-one": _RefusedYear(
        {"at_date_time": _BEFORE_YEAR_ONE},
        "instant_on_day",
    ),
    "datetime-on-date-past-year-9999": _RefusedYear(
        {"at_date_time": _PAST_YEAR_9999},
        "instant_on_day",
    ),
    "datetime-on-date-gte": _RefusedYear(
        {"at_or_after_date_time": _BEFORE_YEAR_ONE},
        "instant_on_day_from",
    ),
    "datetime-on-date-in": _RefusedYear({"date_times": [_PAST_YEAR_9999]}, "instants_on_day"),
    "datetime-on-date-range": _RefusedYear(
        {"date_time_start": _BEFORE_YEAR_ONE},
        "instants_on_day_between",
    ),
}


class _CrossKindCase(NamedTuple):
    """An original declaration's scalar arguments, refusal key, zone and real PG answer."""

    arguments: JSONObject
    form_key: str
    zone: str
    pg_labels: tuple[str, ...] | None


_OTHER_CROSS_REFUSALS = {
    "date-on-datetime": _CrossKindCase(
        {"instant_date": "0001-01-01"},
        "on_instant",
        "Asia/Tokyo",
        (),
    ),
    "date-on-datetime-lt": _CrossKindCase(
        {"instant_before_date": "0001-01-01"},
        "on_instant_before",
        "Asia/Tokyo",
        (),
    ),
    "date-on-datetime-in": _CrossKindCase(
        {"instant_dates": ["2021-06-15", "0001-01-01"]},
        "on_instant_among",
        "Asia/Tokyo",
        ("midnight-tokyo",),
    ),
    "date-on-datetime-range": _CrossKindCase(
        {"instant_date_start": "0001-01-01"},
        "on_instant_between",
        "Asia/Tokyo",
        (
            "early",
            "midnight-utc",
            "midnight-tokyo",
            "late",
        ),
    ),
    "date-transform-before-year-one": _CrossKindCase(
        {"instant_day_of": _BEFORE_YEAR_ONE},
        "instant_day_of",
        "UTC",
        None,
    ),
    "date-transform-past-year-9999": _CrossKindCase(
        {"instant_day_of": _PAST_YEAR_9999},
        "instant_day_of",
        "UTC",
        None,
    ),
    "date-transform-gte": _CrossKindCase(
        {"instant_day_of_from": _BEFORE_YEAR_ONE},
        "instant_day_of_from",
        "UTC",
        None,
    ),
    "date-transform-in": _CrossKindCase(
        {"instants_day_of": [_PAST_YEAR_9999]},
        "instants_day_of",
        "UTC",
        None,
    ),
    "date-transform-range": _CrossKindCase(
        {"instant_day_of_start": _BEFORE_YEAR_ONE},
        "instants_day_of_between",
        "UTC",
        None,
    ),
    "consumer-subclass-keeping-the-filter": _CrossKindCase(
        {"inheriting_day_of": _BEFORE_YEAR_ONE},
        "inheriting_day_of",
        "UTC",
        None,
    ),
}
_OTHER_CROSS_ACCEPTED = {
    "date-on-datetime-at-utc": _CrossKindCase(
        {"instant_date": "0001-01-01"},
        "on_instant",
        "UTC",
        (),
    ),
    "date-on-datetime-in-range": _CrossKindCase(
        {"instant_dates": ["2021-06-15"]},
        "on_instant_among",
        "Asia/Tokyo",
        ("midnight-tokyo",),
    ),
    "date-transform-in-range": _CrossKindCase(
        {"instant_day_of_end": "2021-06-15T09:30:00+00:00"},
        "instants_day_of_between",
        "UTC",
        ("early", "midnight-utc", "midnight-tokyo"),
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", _YEAR_SEARCH)
def test_generated_year_csv_search_uses_each_original_date_or_datetime_lookup(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """CSV text keeps year versus ISO-year membership and range semantics on both temporal columns."""
    rows = _year_rows()
    schema, row_type = _schema()
    selected = _YEAR_SEARCH[case]
    with override_settings(TIME_ZONE="UTC", USE_TZ=True), timezone.override("UTC"):
        if not selected.labels:
            assert _post(schema, "year_search", {selected.argument: "2020"}) == _expected(
                schema,
                row_type,
                rows,
                ("mid-2020",),
            )
        sqls = record_compiled_sql()
        payload = _post(schema, "year_search", {selected.argument: selected.value})
    assert payload == _expected(schema, row_type, rows, selected.labels), payload
    assert len(_root_sql(sqls)) == selected.root_queries, sqls


@pytest.mark.django_db
@pytest.mark.parametrize("case", _YEAR_REFUSALS)
def test_generated_temporal_year_values_are_refused_under_their_original_form_keys(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A normal BigInt argument reaches the generated filter's typed bind refusal before row SQL."""
    _year_rows()
    schema, _row_type = _schema()
    selected = _YEAR_REFUSALS[case]
    with override_settings(TIME_ZONE="UTC", USE_TZ=True), timezone.override("UTC"):
        sqls = record_compiled_sql()
        payload = _post(schema, "year_values", selected.arguments)
    _assert_refusal(payload, selected.form_key)
    assert _root_sql(sqls) == [], sqls


@pytest.mark.django_db
@pytest.mark.parametrize("case", _YEAR_ACCEPTED)
def test_generated_year_arguments_keep_their_bindable_calendar_controls(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The upper valid ISO year matches a stored row, and ordinary years remain distinct from no-row years."""
    rows = _year_rows()
    schema, row_type = _schema()
    arguments, labels = _YEAR_ACCEPTED[case]
    with override_settings(TIME_ZONE="UTC", USE_TZ=True), timezone.override("UTC"):
        if not labels:
            assert _post(schema, "year_values", {"date_years": ["2020"]}) == _expected(
                schema,
                row_type,
                rows,
                ("mid-2020",),
            )
        sqls = record_compiled_sql()
        payload = _post(schema, "year_values", arguments)
    assert payload == _expected(schema, row_type, rows, labels), payload
    assert len(_root_sql(sqls)) == 1, sqls


@pytest.mark.django_db
def test_a_declared_pk_filter_matches_only_its_integer_key(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The non-temporal ``pk`` declaration selects its row beside the temporal refusals."""
    rows = _year_rows()
    schema, row_type = _schema()
    sqls = record_compiled_sql()
    payload = _post(schema, "integer_key", {"key": saved_pk(rows["mid-2020"])})
    assert payload == _expected(schema, row_type, rows, ("mid-2020",)), payload
    assert len(_root_sql(sqls)) == 1, sqls


@pytest.mark.django_db
@_NAIVE_DATE_WARNING
def test_a_datetime_year_bound_checks_the_actual_tokyo_projection(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Datetime year one's computed Tokyo bound is refused on SQLite while PostgreSQL binds it."""
    rows = _year_rows()
    schema, row_type = _schema()
    with override_settings(TIME_ZONE="Asia/Tokyo", USE_TZ=True), timezone.override("Asia/Tokyo"):
        sqls = record_compiled_sql()
        payload = _post(schema, "year_values", {"datetime_year_gt": "1"})
    if connection.vendor == "postgresql":
        assert payload == _expected(schema, row_type, rows, tuple(rows)), payload
        assert len(_root_sql(sqls)) == 1, sqls
    else:
        _assert_refusal(payload, "occurred_at__year__gt")
        assert _root_sql(sqls) == [], sqls


@pytest.mark.django_db
def test_a_date_year_bound_does_not_pick_up_the_datetimes_timezone(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A stored date in year one remains matchable under Tokyo without shifting its year boundary."""
    rows = _year_rows()
    rows["year-one-date"] = _specimen(
        "year-one-date",
        datetime.date(1, 1, 1),
        moment=datetime.datetime(2021, 6, 15, 12, tzinfo=datetime.timezone.utc),
    )
    schema, row_type = _schema()
    with override_settings(TIME_ZONE="Asia/Tokyo", USE_TZ=True), timezone.override("Asia/Tokyo"):
        sqls = record_compiled_sql()
        payload = _post(schema, "year_values", {"date_year": "1"})
    assert payload == _expected(schema, row_type, rows, ("year-one-date",)), payload
    assert len(_root_sql(sqls)) == 1, sqls


@pytest.mark.django_db
@pytest.mark.parametrize("case", _CROSS_REFUSALS)
def test_datetime_arguments_on_date_columns_are_checked_after_upstream_cleaning(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """DateTime scalar values remain datetimes until the original Date-column filter asks Django."""
    _calendar_rows()
    schema, _row_type = _schema()
    selected = _CROSS_REFUSALS[case]
    with override_settings(TIME_ZONE="UTC", USE_TZ=True), timezone.override("UTC"):
        sqls = record_compiled_sql()
        payload = _post(schema, "calendar_dates", selected.arguments)
    _assert_refusal(payload, selected.form_key)
    assert _root_sql(sqls) == [], sqls


@pytest.mark.django_db
@_NAIVE_DATE_WARNING
@pytest.mark.parametrize("case", _OTHER_CROSS_REFUSALS)
def test_calendar_arguments_obey_their_original_columns_and_date_transforms(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Each original cross-kind declaration binds after Django's conversion, or refuses its own key."""
    rows = _cross_kind_rows()
    schema, row_type = _schema()
    selected = _OTHER_CROSS_REFUSALS[case]
    with override_settings(TIME_ZONE=selected.zone, USE_TZ=True), timezone.override(selected.zone):
        sqls = record_compiled_sql()
        payload = _post(schema, "calendar_dates", selected.arguments)
    if connection.vendor == "postgresql" and selected.pg_labels is not None:
        assert payload == _expected(schema, row_type, rows, selected.pg_labels), payload
        assert len(_root_sql(sqls)) == 1, sqls
    else:
        _assert_refusal(payload, selected.form_key)
        assert _root_sql(sqls) == [], sqls


@pytest.mark.django_db
@_NAIVE_DATE_WARNING
@pytest.mark.parametrize("case", _OTHER_CROSS_ACCEPTED)
def test_bindable_calendar_arguments_keep_their_matching_datetime_rows(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """UTC year one binds and the date/list/range controls select actual midnight rows."""
    rows = _cross_kind_rows()
    schema, row_type = _schema()
    selected = _OTHER_CROSS_ACCEPTED[case]
    assert selected.pg_labels is not None
    with override_settings(TIME_ZONE=selected.zone, USE_TZ=True), timezone.override(selected.zone):
        if not selected.pg_labels:
            assert _post(schema, "calendar_dates", {"instant_date": "2021-06-15"}) == _expected(
                schema,
                row_type,
                rows,
                ("midnight-utc",),
            )
        sqls = record_compiled_sql()
        payload = _post(schema, "calendar_dates", selected.arguments)
    assert payload == _expected(schema, row_type, rows, selected.pg_labels), payload
    assert len(_root_sql(sqls)) == 1, sqls


@pytest.mark.django_db
@_NAIVE_DATE_WARNING
def test_an_empty_consumer_queryset_still_checks_its_date_filter_value(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A consumer's ``none()`` cannot hide SQLite's refusal of a Tokyo midnight in year one."""
    _cross_kind_rows()
    schema, _row_type = _schema()
    with override_settings(TIME_ZONE="Asia/Tokyo", USE_TZ=True), timezone.override("Asia/Tokyo"):
        sqls = record_compiled_sql()
        assert _post(
            schema,
            "calendar_dates",
            {"instant_date": "2021-06-15", "empty_root": True},
        ) == {"data": {"rows": []}}
        payload = _post(
            schema,
            "calendar_dates",
            {"instant_date": "0001-01-01", "empty_root": True},
        )
    if connection.vendor == "postgresql":
        assert payload == {"data": {"rows": []}}, payload
    else:
        _assert_refusal(payload, "on_instant")
    assert _root_sql(sqls) == [], sqls


@pytest.mark.django_db
def test_a_datetime_argument_filters_a_date_column_by_the_cleaned_date(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The ordinary DateTime argument matches the stored June date while other dates remain outside."""
    rows = _calendar_rows()
    schema, row_type = _schema()
    with override_settings(TIME_ZONE="UTC", USE_TZ=True), timezone.override("UTC"):
        sqls = record_compiled_sql()
        payload = _post(schema, "calendar_dates", {"at_date_time": "2021-06-15T09:30:00+00:00"})
    assert payload == _expected(schema, row_type, rows, ("match",)), payload
    assert len(_root_sql(sqls)) == 1, sqls


@pytest.mark.django_db
def test_a_datetime_argument_on_a_time_column_matches_its_cleaned_clock(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The original DateTimeFilter's time-column preparation retains the actual matching clock row."""
    rows = _calendar_rows()
    schema, row_type = _schema()
    with override_settings(TIME_ZONE="UTC", USE_TZ=True), timezone.override("UTC"):
        sqls = record_compiled_sql()
        payload = _post(schema, "clock", {"moment": "2021-06-15T09:30:00+00:00"})
    assert payload == _expected(schema, row_type, rows, ("match",)), payload
    assert len(_root_sql(sqls)) == 1, sqls


@pytest.mark.django_db
def test_a_string_datetime_bound_uses_upstream_fractional_offset_parsing(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The form's half-second offset moves its upper bound before the matching row, or PG refuses it."""
    rows = _calendar_rows()
    schema, row_type = _schema()
    with override_settings(TIME_ZONE="UTC", USE_TZ=True), timezone.override("UTC"):
        ordinary = _post(schema, "before_text", {"upper_text": "2021-06-15T10:30:00+01:00"})
        assert ordinary == _expected(schema, row_type, rows, ("early", "match")), ordinary
        sqls = record_compiled_sql()
        payload = _post(
            schema,
            "before_text",
            {"upper_text": "2021-06-15T10:30:00+01:00:00.500000"},
        )
    if connection.vendor == "postgresql":
        _assert_refusal(payload, "taken_between")
        assert _root_sql(sqls) == [], sqls
    else:
        assert payload == _expected(schema, row_type, rows, ("early",)), payload
        assert len(_root_sql(sqls)) == 1, sqls
