"""Native scalar predicates preserve Django's transformed, duration and backend binding semantics.

Consumer-declared filters run through public apply_sync over HTTP, including models
whose duration column is not an output field and whose primary key is a datetime.
The ordinary JSON argument carries form-compatible values; each filter's own form
field, Django expression and executing database retain their upstream behavior.
"""

from __future__ import annotations

import datetime
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from decimal import Decimal
from functools import wraps
from typing import NamedTuple, TypeVar

import django_filters
import pytest
import strawberry
from apps.library import models as library_models
from apps.scalars import models as scalar_models
from django.db import connection
from django.db import models as django_models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models import QuerySet, Transform
from django.db.models.expressions import Combinable
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import register_lookup
from django.urls import path
from django.utils import timezone
from django_filters import MultipleChoiceFilter
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_object,
)
from strawberry.scalars import JSON
from strawberry.types import Info
from strawberry.types.base import StrawberryList
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, ListFilter, RangeFilter, RelatedFilter
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_M = TypeVar("_M", bound=django_models.Model)
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_UNBINDABLE = [{"message": "Enter a value the database can represent.", "code": "invalid"}]
_NAIVE_DATE_WARNING = pytest.mark.filterwarnings(
    "ignore:DateTimeField .* received a naive datetime:RuntimeWarning",
)
_PAST_INT64 = str(2**63)
_BEFORE_INT64 = str(-(2**63) - 1)
_THIRTY_DIGITS = str(10**30)
_BEFORE_YEAR_ONE = "0001-01-01T00:00:00+05:00"
_MATCH = "2021-06-15T09:30:00+00:00"
_PLUS_SIXTEEN = "2021-06-16T01:30:00+16:00"
_MINUS_SIXTEEN = "2021-06-14T17:30:00-16:00"


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-scalar-predicates/", _graphql_view)]


def _holder(
    filters: type[FilterSet],
    rows: Callable[[], QuerySet[_M]],
    output: type[DjangoType],
    *,
    types: Sequence[type[DjangoType]] = (),
) -> DjangoSchema:
    @strawberry.type
    class Query:
        def _rows(self, info: Info[object, object], where: JSON) -> QuerySet[_M]:
            return filters.apply_sync(where, rows(), info)

        rows: QuerySet[_M] = strawberry.field(
            resolver=_rows,
            graphql_type=StrawberryList(output),
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=types,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _scalar_holder(
    filters: type[FilterSet],
    rows: Callable[[], QuerySet[scalar_models.ScalarSpecimen]] | None = None,
) -> DjangoSchema:
    class ScalarPredicateOutput(DjangoType):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = ("label",)

    return _holder(
        filters,
        rows or (lambda: scalar_models.ScalarSpecimen.objects.order_by("pk")),
        ScalarPredicateOutput,
    )


def _post(
    schema: DjangoSchema,
    where: JSONObject,
    selection: str = "label",
    *,
    times: JSONObject | None = None,
) -> JSONObject:
    variables: JSONObject = {"where": where}
    definitions = "$where: JSON!"
    arguments = "where: $where"
    if times is not None:
        variables.update(times)
        definitions += ", $clock: Time, $start: Time, $end: Time"
        arguments += ", clock: $clock, start: $start, end: $end"
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                f"query({definitions}) {{ rows({arguments}) {{ {selection} }} }}",
                variables=variables,
                url="/graphql-scalar-predicates/",
            )
    finally:
        _CURRENT["schema"] = None


def _expected(labels: Sequence[str]) -> JSONObject:
    return {"data": {"rows": [{"label": label} for label in labels]}}


def _refusal(payload: JSONObject, key: str) -> None:
    assert payload["data"] is None, payload
    assert len(json_list(payload, "errors")) == 1, payload
    assert json_at(payload, "errors", 0, "message") == "Invalid filter input"
    assert json_at(payload, "errors", 0, "path") == ["rows"]
    assert json_at(payload, "errors", 0, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {key: _UNBINDABLE},
    }


def _root_sql(sqls: Sequence[str], model: type[django_models.Model]) -> list[str]:
    table = model._meta.db_table
    return [
        sql
        for sql in sqls
        if sql.lstrip().upper().startswith("SELECT ")
        and " FROM " in sql
        and sql.split(" FROM ", 1)[1].startswith(f'"{table}"')
    ]


def _integer_rows() -> dict[str, scalar_models.ScalarSpecimen]:
    days = {
        "mid-2019": datetime.date(2019, 6, 15),
        "mid-2020": datetime.date(2020, 6, 15),
        "new-year-2021": datetime.date(2021, 1, 1),
        "mid-2021": datetime.date(2021, 6, 15),
        "mid-2022": datetime.date(2022, 6, 15),
        "mid-9998": datetime.date(9998, 6, 15),
    }
    return {
        label: scalar_models.ScalarSpecimen.objects.create(
            label=label,
            occurred_on=day,
            occurred_at=datetime.datetime.combine(
                day,
                datetime.time(8)
                if label == "mid-2019"
                else datetime.time(15)
                if label == "mid-9998"
                else datetime.time(9, 30),
                datetime.timezone.utc,
            ),
            occurred_time=datetime.time(8)
            if label == "mid-2019"
            else datetime.time(15)
            if label == "mid-9998"
            else datetime.time(9, 30),
            signed_big=0,
            price="0" if label == "mid-2019" else "2" if label == "mid-9998" else "1",
            external_id=uuid.UUID(int=day.toordinal()),
        )
        for label, day in days.items()
    }


class _PlusOne(Transform):
    """A project transform over an integer column whose output is an integer no column stores."""

    lookup_name = "plus_one"
    template = "(%(expressions)s + 1)"

    def __init__(self, expression: object) -> None:
        """Wrap ``expression`` with an output Django stores as a 64-bit integer."""
        super().__init__(expression, output_field=django_models.BigIntegerField[int, int]())


class _UnrangedInteger(django_models.IntegerField[int, int]):
    """An integer column type naming an internal type no backend states a range for."""

    @override
    def get_internal_type(self) -> str:
        return "UnrangedIntegerField"

    @override
    def get_db_prep_value(
        self,
        value: object,
        connection: BaseDatabaseWrapper,
        prepared: bool = False,
    ) -> object:
        """Delegate parameter adaptation to Django's bigint field without declaring its range."""
        return object_result(
            django_models.BigIntegerField().get_db_prep_value,
            value,
            connection,
            prepared=prepared,
        )


class _PlusOneUnranged(Transform):
    """A project transform whose integer output is of a type the backend states no range for."""

    lookup_name = "plus_one_unranged"
    template = "(%(expressions)s + 1)"

    def __init__(self, expression: object) -> None:
        """Wrap ``expression`` with an output of the unranged integer type."""
        super().__init__(expression, output_field=_UnrangedInteger())


def _year_integer_filter_class() -> type[FilterSet]:
    """A specimen filterset whose declared filters bind a temporal transform's integers.

    The package's ``ListFilter`` (``in``) and ``RangeFilter`` (``range``) over the date
    column's ``year`` and the datetime column's ``iso_year``, the ``ListFilter`` through
    the reverse ``children`` relation with ``exclude=True`` (Django puts an excluded
    multi-valued relation's predicate in an ``Exists`` subquery), and django-filter's
    ``MultipleChoiceFilter`` over the ``month`` transform, which joins its choices with
    ``OR``.
    """

    class YearIntegerFilter(FilterSet):
        day_years_among = ListFilter(field_name="occurred_on__year", lookup_expr="in")
        day_years_span = RangeFilter(field_name="occurred_on__year", lookup_expr="range")
        iso_years_among = ListFilter(field_name="occurred_at__iso_year", lookup_expr="in")
        iso_years_span = RangeFilter(field_name="occurred_at__iso_year", lookup_expr="range")
        child_years_not_among = ListFilter(
            field_name="children__occurred_at__year",
            lookup_expr="in",
            exclude=True,
        )
        months_any = MultipleChoiceFilter(
            field_name="occurred_at__month",
            choices=[("1", "January"), (_PAST_INT64, "past 64 bits")],
        )

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    return YearIntegerFilter


class _ScalarElapsedProbe(django_models.Model):
    """A duration column on a consumer model whose output publishes only its integer key.

    The temporary real table is created only for its HTTP acceptance rows.
    """

    elapsed: django_models.DurationField[object, datetime.timedelta] = (
        django_models.DurationField()
    )

    class Meta:
        managed = False
        app_label = "library"

    @override
    def __str__(self) -> str:
        return str(self.elapsed)


def _elapsed_filter_class() -> type[FilterSet]:
    """A duration filterset opting into exact, comparison, membership and range lookups."""

    class ElapsedFilter(FilterSet):
        class Meta:
            model = _ScalarElapsedProbe
            fields = {
                "elapsed": [
                    "exact",
                    "gt",
                    "in",
                    "range",
                ],
            }

    return ElapsedFilter


class _ScalarStampKeyProbe(django_models.Model):
    """A table keyed by an aware ``DateTimeField``, which a filter reaches through ``pk``.

    The temporary real table is created only for its HTTP acceptance rows.
    """

    stamp: django_models.DateTimeField[
        str | datetime.datetime | datetime.date | Combinable,
        datetime.datetime,
    ] = django_models.DateTimeField(primary_key=True)

    class Meta:
        managed = False
        app_label = "library"

    @override
    def __str__(self) -> str:
        return self.stamp.isoformat()


class _ChildCustomizingSpecimenFilter(FilterSet):
    """A specimen filterset whose ``__init__`` override projects its filters onto a parent."""

    instant_day_of = django_filters.DateTimeFilter(field_name="occurred_at", lookup_expr="date")
    own_day_of = django_filters.DateTimeFilter(
        field_name="occurred_at",
        lookup_expr="date",
        method="keep_every_row",
    )

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = []

    @override
    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[django_models.Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)

    def keep_every_row(
        self,
        queryset: QuerySet[scalar_models.ScalarSpecimen],
        _name: str,
        _value: object,
    ) -> QuerySet[scalar_models.ScalarSpecimen]:
        return queryset


def _priced_filter_class() -> type[FilterSet]:
    """A specimen filterset reaching a bounded and an unbounded decimal column.

    Generated ``exact`` / ``in`` / ``range`` / ``gt`` / ``lt`` leaves on ``price`` (a
    ``DecimalField(20, 4)``), the package's declared ``ListFilter`` / ``RangeFilter`` on
    it, and a ``NumberFilter`` over ``loose_price``, an annotation whose output field is a
    ``DecimalField`` with no ``max_digits``.
    """

    class PricedSpecimenFilter(FilterSet):
        prices_among = ListFilter(field_name="price", lookup_expr="in")
        price_span = RangeFilter(field_name="price", lookup_expr="range")
        loose_price = django_filters.NumberFilter(field_name="loose_price")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {
                "price": [
                    "exact",
                    "in",
                    "range",
                    "gt",
                    "lt",
                ],
            }

    return PricedSpecimenFilter


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("members", "labels"),
    [
        pytest.param([str(2**70)], None, id="member-past-int64-refused"),
        pytest.param(["8", str(2**70)], None, id="mixed-list-refused"),
        pytest.param(["8", "3"], ("mid-2020", "new-year-2021"), id="in-range-matches"),
    ],
)
def test_project_integer_transform_members_bind_as_the_transform_output(
    members: list[str],
    labels: tuple[str, ...] | None,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Project integer transforms keep their matching rows and refuse an overflowing member."""
    rows = _integer_rows()
    scalar_models.ScalarSpecimen.objects.filter(
        pk__in=[saved_pk(rows["mid-2020"]), saved_pk(rows["new-year-2021"])],
    ).update(signed_big=7)
    with register_lookup(django_models.BigIntegerField, _PlusOne):

        class PlusOneFilter(FilterSet):
            class Meta:
                model = scalar_models.ScalarSpecimen
                fields = {"signed_big": ["plus_one__in"]}

        schema = _scalar_holder(PlusOneFilter)
        sqls = record_compiled_sql()
        payload = _post(schema, {"signed_big__plus_one__in": members})
    if labels is None:
        _refusal(payload, "signed_big__plus_one__in")
        assert _root_sql(sqls, scalar_models.ScalarSpecimen) == [], sqls
    else:
        assert payload == _expected(labels), payload
        assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == 1, sqls


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("members", "labels"),
    [
        pytest.param(["8"], ("mid-2020", "new-year-2021"), id="in-range-matches"),
        pytest.param([str(2**40)], (), id="past-int32-matches-nothing"),
    ],
)
def test_project_transform_without_a_backend_range_keeps_its_integer_members(
    members: list[str],
    labels: tuple[str, ...],
    record_compiled_sql: RecordCompiledSql,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A real backend states no range for the project's output type, so valid integers bind."""
    rows = _integer_rows()
    scalar_models.ScalarSpecimen.objects.filter(
        pk__in=[saved_pk(rows["mid-2020"]), saved_pk(rows["new-year-2021"])],
    ).update(signed_big=7)
    if connection.vendor == "postgresql":
        # psycopg adapts an integer by its internal type, so the type needs a psycopg mapping.
        from django.db.backends.postgresql.operations import (  # noqa: PLC0415 - psycopg is optional
            DatabaseOperations,
        )

        type_map = DatabaseOperations.integerfield_type_map
        monkeypatch.setitem(type_map, "UnrangedIntegerField", type_map["BigIntegerField"])
    with register_lookup(django_models.BigIntegerField, _PlusOneUnranged):

        class UnrangedFilter(FilterSet):
            class Meta:
                model = scalar_models.ScalarSpecimen
                fields = {"signed_big": ["plus_one_unranged__in"]}

        schema = _scalar_holder(UnrangedFilter)
        if not labels:
            assert _post(schema, {"signed_big__plus_one_unranged__in": ["8"]}) == _expected(
                ("mid-2020", "new-year-2021"),
            )
        sqls = record_compiled_sql()
        payload = _post(schema, {"signed_big__plus_one_unranged__in": members})
    assert payload == _expected(labels), payload
    assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == 1, sqls


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("years", "labels"),
    [
        pytest.param(["2021"], ("new-year-2021", "mid-2021"), id="in-range-matches"),
        pytest.param([_PAST_INT64], None, id="own-member-past-int64-refused"),
    ],
)
def test_a_queryset_annotations_constant_does_not_refuse_the_filters_year(
    years: list[str],
    labels: tuple[str, ...] | None,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Only the filter's own integer member is checked, not its annotation's fixed -1 constant."""
    _integer_rows()

    class AnnotatedYearFilter(FilterSet):
        day_years_among = ListFilter(field_name="day__year", lookup_expr="in")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    def annotated() -> QuerySet[scalar_models.ScalarSpecimen]:
        return scalar_models.ScalarSpecimen.objects.annotate(
            day=django_models.Case(
                django_models.When(unsigned_big__in=[-1], then=django_models.F("occurred_on")),
                default=django_models.F("occurred_on"),
            ),
        ).order_by("pk")

    schema = _scalar_holder(AnnotatedYearFilter, annotated)
    sqls = record_compiled_sql()
    payload = _post(schema, {"day_years_among": {"in_": years}})
    if labels is None:
        _refusal(payload, "day_years_among")
        assert _root_sql(sqls, scalar_models.ScalarSpecimen) == [], sqls
    else:
        assert payload == _expected(labels), payload
        assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == 1, sqls


_YEAR_INTEGER_REFUSALS: dict[str, tuple[JSONObject, str]] = {
    "year-in-past-int64": ({"day_years_among": {"in_": [_PAST_INT64]}}, "day_years_among"),
    "year-in-before-int64": (
        {"day_years_among": {"in_": ["2021", _BEFORE_INT64]}},
        "day_years_among",
    ),
    "year-in-thirty-digits": ({"day_years_among": {"in_": [_THIRTY_DIGITS]}}, "day_years_among"),
    "year-range-start-past-int64": (
        {"day_years_span": {"range": {"start": _PAST_INT64, "end": "2021"}}},
        "day_years_span",
    ),
    "year-range-start-before-int64": (
        {"day_years_span": {"range": {"start": _BEFORE_INT64, "end": "2021"}}},
        "day_years_span",
    ),
    "year-range-end-thirty-digits": (
        {"day_years_span": {"range": {"start": "2021", "end": _THIRTY_DIGITS}}},
        "day_years_span",
    ),
    "iso-year-in-past-int64": ({"iso_years_among": {"in_": [_PAST_INT64]}}, "iso_years_among"),
    "iso-year-range-end-before-int64": (
        {"iso_years_span": {"range": {"start": "2021", "end": _BEFORE_INT64}}},
        "iso_years_span",
    ),
    "excluded-multi-valued-relation": (
        {"child_years_not_among": {"in_": [_PAST_INT64]}},
        "child_years_not_among",
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", _YEAR_INTEGER_REFUSALS)
def test_declared_year_filters_refuse_each_integer_bound_the_database_cannot_bind(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Date-year, ISO-year and excluded-child declarations retain their exact refusal keys."""
    rows = _integer_rows()
    rows["new-year-2021"].parent = rows["mid-2019"]
    rows["new-year-2021"].save(update_fields=["parent"])
    schema = _scalar_holder(_year_integer_filter_class())
    where, key = _YEAR_INTEGER_REFUSALS[case]
    sqls = record_compiled_sql()
    payload = _post(schema, where)
    _refusal(payload, key)
    assert _root_sql(sqls, scalar_models.ScalarSpecimen) == [], sqls


_YEAR_INTEGER_ACCEPTED: dict[str, tuple[JSONObject, tuple[str, ...]]] = {
    "year-in": ({"day_years_among": {"in_": ["2021"]}}, ("new-year-2021", "mid-2021")),
    "iso-year-in": ({"iso_years_among": {"in_": ["2021"]}}, ("mid-2021",)),
    "excluded-multi-valued-relation": (
        {"child_years_not_among": {"in_": ["2021"]}},
        (
            "mid-2020",
            "new-year-2021",
            "mid-2021",
            "mid-2022",
            "mid-9998",
        ),
    ),
    "or-member-django-drops": ({"months_any": {"exact": ["1", _PAST_INT64]}}, ("new-year-2021",)),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", _YEAR_INTEGER_ACCEPTED)
def test_declared_year_filters_keep_their_matching_rows_and_exclusion_complements(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Each supported integer declaration selects populated roots, including the excluded-child complement."""
    rows = _integer_rows()
    rows["new-year-2021"].parent = rows["mid-2019"]
    rows["new-year-2021"].save(update_fields=["parent"])
    schema = _scalar_holder(_year_integer_filter_class())
    where, labels = _YEAR_INTEGER_ACCEPTED[case]
    sqls = record_compiled_sql()
    payload = _post(schema, where)
    assert payload == _expected(labels), payload
    assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == 1, sqls


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "form",
        "low_offset",
        "high_offset",
        "refused",
    ),
    [
        pytest.param("in", 0, None, False, id="in-min"),
        pytest.param("in", None, 0, False, id="in-max"),
        pytest.param("in", -1, None, True, id="in-below-min"),
        pytest.param("in", None, 1, True, id="in-above-max"),
        pytest.param("range", 0, 0, False, id="range-min-max"),
        pytest.param("range", -1, 0, True, id="range-start-below-min"),
        pytest.param("range", 0, 1, True, id="range-end-above-max"),
    ],
)
def test_declared_year_bounds_follow_the_executing_databases_integer_range(
    form: str,
    low_offset: int | None,
    high_offset: int | None,
    *,
    refused: bool,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The backend's own endpoints bind, and one beyond either endpoint is refused before SQL."""
    rows = _integer_rows()
    low, high = connection.ops.integer_field_range("IntegerField")
    assert low is not None
    assert high is not None
    ends = (
        str(low + low_offset) if low_offset is not None else None,
        str(high + high_offset) if high_offset is not None else None,
    )
    key = "day_years_among" if form == "in" else "day_years_span"
    where: JSONObject = (
        {key: {"in_": [value for value in ends if value is not None]}}
        if form == "in"
        else {key: {"range": {"start": ends[0], "end": ends[1]}}}
    )
    schema = _scalar_holder(_year_integer_filter_class())
    assert _post(schema, {"day_years_among": {"in_": ["2021"]}}) == _expected(
        ("new-year-2021", "mid-2021"),
    )
    sqls = record_compiled_sql()
    payload = _post(schema, where)
    if refused:
        _refusal(payload, key)
        assert _root_sql(sqls, scalar_models.ScalarSpecimen) == [], sqls
    else:
        expected = tuple(rows) if form == "range" else ()
        assert payload == _expected(expected), payload
        assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == 1, sqls


@pytest.fixture
def duration_table(transactional_db: None) -> Iterator[None]:
    """Create the duration consumer's table without changing the shipped scalar model."""
    _ = transactional_db
    with connection.schema_editor() as editor:
        editor.create_model(_ScalarElapsedProbe)
    try:
        yield
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(_ScalarElapsedProbe)


@pytest.fixture
def stamp_key_table(transactional_db: None) -> Iterator[None]:
    """Create the consumer's actual datetime-primary-key table for its HTTP rows."""
    _ = transactional_db
    with connection.schema_editor() as editor:
        editor.create_model(_ScalarStampKeyProbe)
    try:
        yield
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(_ScalarStampKeyProbe)


class _DurationCase(NamedTuple):
    """One duration declaration and its native/non-native interval result."""

    where: JSONObject
    key: str
    refuses_microseconds: bool
    labels: tuple[str, ...]


_DURATION_CASES = {
    "exact": _DurationCase(
        where={"elapsed": {"exact": "106751992 00:00:00"}},
        key="elapsed",
        refuses_microseconds=True,
        labels=(),
    ),
    "exact-negative": _DurationCase(
        where={"elapsed": {"exact": "-106751992 00:00:00"}},
        key="elapsed",
        refuses_microseconds=True,
        labels=(),
    ),
    "gt": _DurationCase(
        where={"elapsed": {"gt": "106751992 00:00:00"}},
        key="elapsed__gt",
        refuses_microseconds=True,
        labels=(),
    ),
    "in-member": _DurationCase(
        where={"elapsed": {"in_": ["1 00:00:00", "106751992 00:00:00"]}},
        key="elapsed__in",
        refuses_microseconds=True,
        labels=("one-day",),
    ),
    "range-start": _DurationCase(
        where={"elapsed": {"range": ["-106751992 00:00:00", "1 00:00:00"]}},
        key="elapsed__range",
        refuses_microseconds=True,
        labels=("negative-edge", "one-day"),
    ),
    "exact-in-range": _DurationCase(
        where={"elapsed": {"exact": "106751991 00:00:00"}},
        key="elapsed",
        refuses_microseconds=False,
        labels=("positive-edge",),
    ),
    "exact-negative-in-range": _DurationCase(
        where={"elapsed": {"exact": "-106751991 00:00:00"}},
        key="elapsed",
        refuses_microseconds=False,
        labels=("negative-edge",),
    ),
    "range-in-range": _DurationCase(
        where={"elapsed": {"range": ["-106751991 00:00:00", "106751991 00:00:00"]}},
        key="elapsed__range",
        refuses_microseconds=False,
        labels=("negative-edge", "one-day", "positive-edge"),
    ),
}


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("duration_table")
@pytest.mark.parametrize("case", _DURATION_CASES)
def test_duration_filters_bind_native_intervals_or_refuse_overflowing_microseconds(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The same public duration input selects real rows on interval backends and respects integer storage."""
    durations = {
        "negative-edge": datetime.timedelta(days=-106751991),
        "one-day": datetime.timedelta(days=1),
        "positive-edge": datetime.timedelta(days=106751991),
    }
    rows = {
        label: _ScalarElapsedProbe.objects.create(elapsed=value)
        for label, value in durations.items()
    }

    class ElapsedOutput(DjangoType):
        class Meta:
            model = _ScalarElapsedProbe
            fields = ("id",)

    schema = _holder(
        _elapsed_filter_class(),
        lambda: _ScalarElapsedProbe.objects.order_by("pk"),
        ElapsedOutput,
    )
    assert _post(schema, {"elapsed": {"exact": "1 00:00:00"}}, "id") == {
        "data": {"rows": [{"id": saved_pk(rows["one-day"])}]},
    }
    selected = _DURATION_CASES[case]
    sqls = record_compiled_sql()
    payload = _post(schema, selected.where, "id")
    if selected.refuses_microseconds and not connection.features.has_native_duration_field:
        _refusal(payload, selected.key)
        assert _root_sql(sqls, _ScalarElapsedProbe) == [], sqls
    else:
        assert payload == {
            "data": {"rows": [{"id": saved_pk(rows[label])} for label in selected.labels]},
        }, payload
        assert len(_root_sql(sqls, _ScalarElapsedProbe)) == 1, sqls


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("stamp_key_table")
@pytest.mark.parametrize(
    "value",
    [_BEFORE_YEAR_ONE, _MATCH],
    ids=["date-in-year-0", "date-in-range"],
)
def test_a_temporal_primary_key_is_checked_through_its_pk_date_transform(
    value: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The pk alias reaches its actual datetime column and refuses an unrepresentable projected date."""
    match = datetime.datetime(2021, 6, 15, 9, 30, tzinfo=datetime.timezone.utc)
    _ScalarStampKeyProbe.objects.create(stamp=match)
    _ScalarStampKeyProbe.objects.create(
        stamp=datetime.datetime(2022, 6, 15, tzinfo=datetime.timezone.utc),
    )

    class StampKeyFilter(FilterSet):
        day_of_key = django_filters.DateTimeFilter(field_name="pk", lookup_expr="date")

        class Meta:
            model = _ScalarStampKeyProbe
            fields = ()

    class StampKeyOutput(DjangoType):
        class Meta:
            model = _ScalarStampKeyProbe
            fields = ("stamp",)

    schema = _holder(
        StampKeyFilter,
        lambda: _ScalarStampKeyProbe.objects.order_by("pk"),
        StampKeyOutput,
    )
    sqls = record_compiled_sql()
    payload = _post(schema, {"day_of_key": {"date": value}}, "stamp")
    if value == _BEFORE_YEAR_ONE:
        _refusal(payload, "day_of_key")
        assert _root_sql(sqls, _ScalarStampKeyProbe) == [], sqls
    else:
        assert payload == {"data": {"rows": [{"stamp": match.isoformat()}]}}, payload
        assert len(_root_sql(sqls, _ScalarStampKeyProbe)) == 1, sqls


def _offset_filters() -> type[FilterSet]:
    class OffsetFilter(FilterSet):
        taken_before = django_filters.DateTimeFilter(field_name="occurred_at", lookup_expr="lt")
        taken_between = django_filters.DateTimeFromToRangeFilter(field_name="occurred_at")
        clock_time = django_filters.TimeFilter(field_name="occurred_at__time")
        timed_between = django_filters.TimeRangeFilter(field_name="occurred_time")
        taken_among = ListFilter(field_name="occurred_at", lookup_expr="in")
        taken_span = RangeFilter(field_name="occurred_at", lookup_expr="range")
        taken_on_day_of = django_filters.DateTimeFilter(
            field_name="occurred_at",
            lookup_expr="date",
        )

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    return OffsetFilter


def _offset_holder() -> DjangoSchema:
    filters = _offset_filters()

    class OffsetOutput(DjangoType):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = ("label",)

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: Info[object, object],
            where: JSON,
            *,
            clock: datetime.time | None = None,
            start: datetime.time | None = None,
            end: datetime.time | None = None,
        ) -> QuerySet[scalar_models.ScalarSpecimen]:
            data = json_object(where)
            if clock is not None:
                data["clock_time"] = {"exact": clock}
            if start is not None or end is not None:
                data["timed_between"] = {"exact": {"start": start, "end": end}}
            return filters.apply_sync(
                data,
                scalar_models.ScalarSpecimen.objects.order_by("pk"),
                info,
            )

        rows: QuerySet[scalar_models.ScalarSpecimen] = strawberry.field(
            resolver=_rows,
            graphql_type=list[OffsetOutput],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(query=Query, config=strawberry_config(), extensions=[lambda: optimizer])


class _OffsetCase(NamedTuple):
    """One offset declaration with its real compiled-parameter refusal and accepted root set."""

    where: JSONObject
    times: JSONObject | None
    key: str
    refuses_sqlite: bool
    refuses_pg: bool
    labels: tuple[str, ...]


_OFFSET_CASES = {
    "declared": _OffsetCase(
        where={"taken_before": {"lt": _PLUS_SIXTEEN}},
        times=None,
        key="taken_before",
        refuses_sqlite=False,
        refuses_pg=True,
        labels=("mid-2019", "mid-2020", "new-year-2021"),
    ),
    "declared-range-lone-bound": _OffsetCase(
        where={"taken_between": {"exact": {"start": _MINUS_SIXTEEN}}},
        times=None,
        key="taken_between",
        refuses_sqlite=False,
        refuses_pg=True,
        labels=("mid-2021", "mid-2022", "mid-9998"),
    ),
    "time-transform": _OffsetCase(
        where={},
        times={"clock": "09:30:00+16:00"},
        key="clock_time",
        refuses_sqlite=True,
        refuses_pg=True,
        labels=(),
    ),
    "declared-time-range": _OffsetCase(
        where={},
        times={"start": "01:00:00", "end": "09:30:00-16:00"},
        key="timed_between",
        refuses_sqlite=True,
        refuses_pg=True,
        labels=(),
    ),
    "list-equal-instant-member": _OffsetCase(
        where={"taken_among": {"in_": [_MATCH, _PLUS_SIXTEEN]}},
        times=None,
        key="taken_among",
        refuses_sqlite=False,
        refuses_pg=False,
        labels=("mid-2021",),
    ),
    "list-distinct-offset-member": _OffsetCase(
        where={"taken_among": {"in_": [_MATCH, "2021-06-16T01:31:00+16:00"]}},
        times=None,
        key="taken_among",
        refuses_sqlite=False,
        refuses_pg=True,
        labels=("mid-2021",),
    ),
    "range-bound": _OffsetCase(
        where={"taken_span": {"range": {"start": _MINUS_SIXTEEN, "end": _MATCH}}},
        times=None,
        key="taken_span",
        refuses_sqlite=False,
        refuses_pg=True,
        labels=("mid-2021",),
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", _OFFSET_CASES)
def test_declared_offset_filters_check_only_the_parameters_django_actually_binds(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Actual time scalars preserve awareness and an equal-instant member removed by Django never binds."""
    _integer_rows()
    schema = _offset_holder()
    selected = _OFFSET_CASES[case]
    with override_settings(TIME_ZONE="UTC", USE_TZ=True), timezone.override("UTC"):
        assert _post(schema, {"taken_before": {"lt": "2021-06-16T00:00:00+00:00"}}) == _expected(
            (
                "mid-2019",
                "mid-2020",
                "new-year-2021",
                "mid-2021",
            ),
        )
        sqls = record_compiled_sql()
        payload = _post(schema, selected.where, times=selected.times)
    refuses = selected.refuses_pg if connection.vendor == "postgresql" else selected.refuses_sqlite
    if refuses:
        _refusal(payload, selected.key)
        assert _root_sql(sqls, scalar_models.ScalarSpecimen) == [], sqls
    else:
        assert payload == _expected(selected.labels), payload
        assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == 1, sqls


@pytest.mark.django_db
def test_a_datetime_date_transform_keeps_its_date_at_a_sixteen_hour_offset(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A datetime's date transform binds a date and accepts an offset the raw datetime would refuse."""
    _integer_rows()
    schema = _offset_holder()
    with override_settings(TIME_ZONE="UTC", USE_TZ=True), timezone.override("UTC"):
        sqls = record_compiled_sql()
        payload = _post(schema, {"taken_on_day_of": {"date": _PLUS_SIXTEEN}})
    assert payload == _expected(("mid-2021",)), payload
    assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == 1, sqls


@pytest.mark.django_db
@pytest.mark.parametrize(
    "leaf",
    ["instant_day_of", "own_day_of"],
    ids=["shipped-filter", "method"],
)
def test_a_projected_temporal_leaf_uses_its_childs_binding_or_owned_method(
    leaf: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A projected temporal filter belongs to its child, whose identity method stays unconstraining."""
    rows = _integer_rows()
    scalar_models.NullableScalarSpecimen.objects.create(
        label="with-match",
        partner=rows["mid-2021"],
    )
    scalar_models.NullableScalarSpecimen.objects.create(
        label="with-other",
        partner=rows["mid-2020"],
    )
    scalar_models.NullableScalarSpecimen.objects.create(label="without-partner", partner=None)

    class ProjectedPartnerFilter(FilterSet):
        partner = RelatedFilter(_ChildCustomizingSpecimenFilter, field_name="partner")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    class ScalarTarget(DjangoType):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = ("label",)

    class NullableOutput(DjangoType):
        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = ("label",)

    schema = _holder(
        ProjectedPartnerFilter,
        lambda: scalar_models.NullableScalarSpecimen.objects.order_by("pk"),
        NullableOutput,
        types=(ScalarTarget,),
    )
    key = "partner__" + leaf
    sqls = record_compiled_sql()
    payload = _post(schema, {key: {"date": _BEFORE_YEAR_ONE}})
    if leaf == "instant_day_of":
        _refusal(payload, key)
        assert _root_sql(sqls, scalar_models.NullableScalarSpecimen) == [], sqls
    else:
        assert payload == _expected(("with-match", "with-other", "without-partner")), payload
        assert len(_root_sql(sqls, scalar_models.NullableScalarSpecimen)) == 1, sqls


@pytest.mark.django_db
def test_a_declared_lookup_can_continue_across_its_foreign_key(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The relation's name lookup keeps Django's full path and compares the related text."""
    first = library_models.Branch.objects.create(name="b1", city="Boston")
    other = library_models.Branch.objects.create(name="b2", city="Boston")
    library_models.Shelf.objects.create(code="S1", topic="Fiction", branch=first)
    library_models.Shelf.objects.create(code="S2", topic="History", branch=other)

    class ShelfByBranchName(FilterSet):
        branch_named = django_filters.CharFilter(field_name="branch", lookup_expr="name__iexact")

        class Meta:
            model = library_models.Shelf
            fields = []

    class ShelfOutput(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("code",)

    schema = _holder(
        ShelfByBranchName,
        lambda: library_models.Shelf.objects.order_by("pk"),
        ShelfOutput,
    )
    sqls = record_compiled_sql()
    payload = _post(schema, {"branch_named": "b1"}, "code")
    assert payload == {"data": {"rows": [{"code": "S1"}]}}, payload
    statements = _root_sql(sqls, library_models.Shelf)
    assert len(statements) == 1, sqls
    assert '"library_branch"' in statements[0], statements


@pytest.mark.django_db
@pytest.mark.parametrize("branch", ["not", "nested"])
def test_decimal_format_refusals_keep_their_logical_and_related_form_paths(
    branch: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Actual PostgreSQL numeric refusals name the logical or partner branch while SQLite filters normally."""
    rows = _integer_rows()
    scalar_models.NullableScalarSpecimen.objects.create(
        label="with-match",
        partner=rows["mid-2021"],
    )
    scalar_models.NullableScalarSpecimen.objects.create(
        label="with-other",
        partner=rows["mid-2020"],
    )
    scalar_models.NullableScalarSpecimen.objects.create(label="without-partner", partner=None)
    if branch == "not":
        schema = _scalar_holder(_priced_filter_class())
        where: JSONObject = {"not_": {"price": {"exact": "1e-1000000"}}}
        key = "not__price"
        model = scalar_models.ScalarSpecimen
        assert _post(schema, {"not_": {"price": {"exact": "1"}}}) == _expected(
            ("mid-2019", "mid-9998"),
        )
        labels = (
            tuple(
                scalar_models.ScalarSpecimen.objects.exclude(price=Decimal("1e-1000000"))
                .order_by("pk")
                .values_list("label", flat=True),
            )
            if connection.vendor != "postgresql"
            else ()
        )
    else:

        class ScalarTarget(DjangoType):
            class Meta:
                model = scalar_models.ScalarSpecimen
                fields = ("label",)

        class PartnerFilter(FilterSet):
            partner = RelatedFilter(_priced_filter_class(), field_name="partner")

            class Meta:
                model = scalar_models.NullableScalarSpecimen
                fields = {"price": ["exact"]}

        class NullableOutput(DjangoType):
            class Meta:
                model = scalar_models.NullableScalarSpecimen
                fields = ("label",)

        schema = _holder(
            PartnerFilter,
            lambda: scalar_models.NullableScalarSpecimen.objects.order_by("pk"),
            NullableOutput,
            types=(ScalarTarget,),
        )
        where = {"partner": {"price": {"lt": "-1e1000000"}}}
        key = "partner__price__lt"
        model = scalar_models.NullableScalarSpecimen
        assert _post(schema, {"partner": {"price": {"lt": "2"}}}) == _expected(
            ("with-match", "with-other"),
        )
        labels = (
            tuple(
                scalar_models.NullableScalarSpecimen.objects.filter(
                    partner__price__lt=Decimal("-1e1000000"),
                )
                .order_by("pk")
                .values_list("label", flat=True),
            )
            if connection.vendor != "postgresql"
            else ()
        )
    sqls = record_compiled_sql()
    payload = _post(schema, where)
    if connection.vendor == "postgresql":
        _refusal(payload, key)
        assert _root_sql(sqls, model) == [], sqls
    else:
        assert payload == _expected(labels), payload
        assert len(_root_sql(sqls, model)) == 1, sqls


@pytest.mark.django_db
def test_a_projected_consumer_method_reads_its_approval_table_only_when_filtering(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A real approval lookup runs once for a supplied method, never during the bind ask."""
    rows = _integer_rows()
    scalar_models.ScalarSpecimenTag.objects.create(label=_BEFORE_YEAR_ONE)
    scalar_models.ScalarSpecimenTag.objects.create(label="unrelated")
    scalar_models.NullableScalarSpecimen.objects.create(
        label="with-match",
        partner=rows["mid-2021"],
    )
    scalar_models.NullableScalarSpecimen.objects.create(
        label="with-other",
        partner=rows["mid-2020"],
    )
    scalar_models.NullableScalarSpecimen.objects.create(label="without-partner", partner=None)

    class ApprovedStampFilter(FilterSet):
        own_day_of = django_filters.DateTimeFilter(
            field_name="occurred_at",
            lookup_expr="date",
            method="approved_stamp",
        )

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

        def approved_stamp(
            self,
            queryset: QuerySet[scalar_models.ScalarSpecimen],
            _name: str,
            value: datetime.datetime,
        ) -> QuerySet[scalar_models.ScalarSpecimen]:
            approved = (
                scalar_models.ScalarSpecimenTag.objects.using(queryset.db)
                .filter(
                    label=value.isoformat(),
                )
                .exists()
            )
            return queryset if approved else queryset.none()

    class ApprovedPartnerFilter(FilterSet):
        partner = RelatedFilter(ApprovedStampFilter, field_name="partner")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    class ScalarTarget(DjangoType):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = ("label",)

    class NullableOutput(DjangoType):
        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = ("label",)

    schema = _holder(
        ApprovedPartnerFilter,
        lambda: scalar_models.NullableScalarSpecimen.objects.order_by("pk"),
        NullableOutput,
        types=(ScalarTarget,),
    )
    sqls = record_compiled_sql()
    payload = _post(schema, {"partner__own_day_of": {"date": _BEFORE_YEAR_ONE}})
    assert payload == _expected(("with-match", "with-other", "without-partner")), payload
    assert len(_root_sql(sqls, scalar_models.ScalarSpecimenTag)) == 1, sqls
    assert len(_root_sql(sqls, scalar_models.NullableScalarSpecimen)) == 1, sqls
    declined_sqls = record_compiled_sql()
    declined = _post(schema, {"partner__own_day_of": {"date": _MATCH}})
    assert declined == _expected(()), declined
    assert len(_root_sql(declined_sqls, scalar_models.ScalarSpecimenTag)) == 1, declined_sqls
    assert len(_root_sql(declined_sqls, scalar_models.NullableScalarSpecimen)) == 1, declined_sqls


def _approving_datetime_filter_override(kind: str) -> type[django_filters.DateTimeFilter]:
    """The original method, static method and type-built class declarations, reading approvals."""

    def approved_rows(queryset: QuerySet[_M], value: datetime.datetime) -> QuerySet[_M]:
        approved = (
            scalar_models.ScalarSpecimenTag.objects.using(queryset.db)
            .filter(label=value.isoformat())
            .exists()
        )
        return queryset if approved else queryset.none()

    if kind == "staticmethod":
        return type(
            "StaticApproving",
            (django_filters.DateTimeFilter,),
            {"filter": staticmethod(approved_rows)},
        )
    if kind == "type":

        def bound_approval(
            _self: object,
            queryset: QuerySet[_M],
            value: datetime.datetime,
        ) -> QuerySet[_M]:
            return approved_rows(queryset, value)

        return type(
            "DynamicApproving",
            (django_filters.DateTimeFilter,),
            {"filter": bound_approval},
        )

    class MethodApproving(django_filters.DateTimeFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: datetime.datetime) -> QuerySet[_M]:
            return approved_rows(qs, value)

    return MethodApproving


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["method", "staticmethod", "type"])
def test_a_class_level_filter_override_reads_its_approval_only_when_filtering(
    record_compiled_sql: RecordCompiledSql,
    kind: str,
) -> None:
    """Every class-level override owns its date value and reads its approval once per request."""
    rows = _integer_rows()
    scalar_models.ScalarSpecimenTag.objects.create(label=_BEFORE_YEAR_ONE)
    scalar_models.ScalarSpecimenTag.objects.create(label="unrelated")
    approving = _approving_datetime_filter_override(kind)

    class ApprovedFilter(FilterSet):
        day_of = approving(field_name="occurred_at", lookup_expr="date")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    schema = _scalar_holder(ApprovedFilter)
    sqls = record_compiled_sql()
    payload = _post(schema, {"day_of": {"date": _BEFORE_YEAR_ONE}})
    assert payload == _expected(tuple(rows)), payload
    assert len(_root_sql(sqls, scalar_models.ScalarSpecimenTag)) == 1, sqls
    assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == 1, sqls
    declined_sqls = record_compiled_sql()
    declined = _post(schema, {"day_of": {"date": _MATCH}})
    assert declined == _expected(()), declined
    assert len(_root_sql(declined_sqls, scalar_models.ScalarSpecimenTag)) == 1, declined_sqls
