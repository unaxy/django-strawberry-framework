"""Native scalar predicates preserve Django's transformed, duration and backend binding semantics.

Consumer-declared filters run through public apply_sync over HTTP, including models
whose duration column is not an output field and whose primary key is a datetime.
The ordinary JSON argument carries form-compatible values; each filter's own form
field, Django expression and executing database retain their upstream behavior.
A typed ``Decimal`` a declared ``NumberFilter`` publishes over an integer annotation or a
column past a ``FilteredRelation`` alias answers from the end of the column's range it
lies past without being converted, an annotation a consumer ``filter_queryset`` adds before
the leaves included. A declared ``ListFilter`` / ``RangeFilter`` over such a path, the alias
itself, an alias of the reverse ``children`` relation or a ``year`` of a date annotation
cleans and compares each value as the queryset does, a served set's own ``filter_queryset``
annotation included under the sync and the async view, its junk ``FILTER_INVALID`` keyed by
the leaf or its logical arm; a ``GlobalIDFilter`` over an alias of a typed relation
decodes and refuses as over that relation, and one over an alias into an untyped model or
over a key annotation coerces its node id through the related key.
"""

from __future__ import annotations

import contextlib
import datetime
import uuid
from collections.abc import Callable, Generator, Iterator, Mapping, Sequence
from decimal import Decimal
from functools import wraps
from typing import TYPE_CHECKING, NamedTuple, TypeVar

import django_filters
import pytest
import strawberry
from apps.library import models as library_models
from apps.scalars import models as scalar_models
from asgiref.sync import sync_to_async
from django.db import connection
from django.db import models as django_models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models import Count, F, FilteredRelation, QuerySet, Transform
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
    assert_database_answer,
    database_answer,
    graphql_payload,
    json_at,
    json_list,
    json_object,
    json_str,
    response_json,
)
from strawberry import relay
from strawberry.relay import to_base64
from strawberry.scalars import JSON
from strawberry.types import Info
from strawberry.types.base import StrawberryList
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import (
    FilterInput,
    FilterSet,
    GlobalIDFilter,
    ListFilter,
    RangeFilter,
    RelatedFilter,
)
from django_strawberry_framework.filters.base import _lookup_operand, _model_lookup_operand
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._cleaned_filter_sets import cleaned_specimen
from tests._idioms import saved_pk

if TYPE_CHECKING:
    from django.db.models.sql.compiler import SQLCompiler, _AsSqlType

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


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-scalar-predicates/", _graphql_view),
    path("graphql-scalar-predicates-async/", _async_graphql_view),
]


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
        payload = _post(schema, {"signed_big": {"plus_one_in": members}})
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
            assert _post(schema, {"signed_big": {"plus_one_unranged_in": ["8"]}}) == _expected(
                ("mid-2020", "new-year-2021"),
            )
        sqls = record_compiled_sql()
        payload = _post(schema, {"signed_big": {"plus_one_unranged_in": members}})
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


class _QuerysetIntegerPathFilter(FilterSet):
    annotated_at_least = django_filters.NumberFilter(field_name="n", lookup_expr="gte")
    annotated_below = django_filters.NumberFilter(field_name="n", lookup_expr="lt")
    annotated_among = ListFilter(field_name="n", lookup_expr="in")
    children_at_least = django_filters.NumberFilter(field_name="kids", lookup_expr="gte")
    parent_is = django_filters.NumberFilter(field_name="par", lookup_expr="exact")
    annotated_matching = django_filters.NumberFilter(field_name="n", lookup_expr="regex")
    parent_big_at_least = django_filters.NumberFilter(
        field_name="par__signed_big",
        lookup_expr="gte",
    )
    parent_big_below = django_filters.NumberFilter(field_name="par__signed_big", lookup_expr="lt")
    annotated_year_after = django_filters.NumberFilter(field_name="d", lookup_expr="year__gt")
    parent_year_after = django_filters.NumberFilter(
        field_name="par__occurred_on",
        lookup_expr="year__gt",
    )
    annotated_span = RangeFilter(field_name="n", lookup_expr="range")
    dated_years_among = ListFilter(field_name="d", lookup_expr="year__in")
    parents_among = ListFilter(field_name="par", lookup_expr="in")
    par_node = GlobalIDFilter(field_name="par")
    parent_node = GlobalIDFilter(field_name="parent")
    costs_among = ListFilter(field_name="cost", lookup_expr="in")
    offspring_among = ListFilter(field_name="offspring", lookup_expr="in")
    crossed_big_span = RangeFilter(field_name="par", lookup_expr="signed_big__range")
    direct_big_span = RangeFilter(field_name="par__signed_big", lookup_expr="range")
    crossed_big_among = ListFilter(field_name="par", lookup_expr="signed_big__in")
    direct_big_among = ListFilter(field_name="par__signed_big", lookup_expr="in")
    implicit_big_span = RangeFilter(field_name="par", lookup_expr="signed_big")
    offspring_node = GlobalIDFilter(field_name="offspring")
    children_node = GlobalIDFilter(field_name="children")
    tag_node = GlobalIDFilter(field_name="vtag")
    parent_ref_node = GlobalIDFilter(field_name="parent_ref")
    names_among = ListFilter(field_name="named", lookup_expr="in")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)


def _typed_queryset_path_holder() -> DjangoSchema:
    class QuerysetPathOutput(DjangoType):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = ("label",)
            filterset_class = _QuerysetIntegerPathFilter

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: Info[object, object],
            filter: FilterInput[_QuerysetIntegerPathFilter],  # noqa: A002
        ) -> QuerySet[scalar_models.ScalarSpecimen]:
            queryset = (
                scalar_models.ScalarSpecimen.objects.annotate(
                    n=F("signed_big"),
                    d=F("occurred_on"),
                    kids=Count("children"),
                    cost=F("price"),
                    named=F("label"),
                    parent_ref=F("parent"),
                )
                .alias(
                    par=FilteredRelation("parent"),
                    offspring=FilteredRelation("children"),
                    vtag=FilteredRelation("tag"),
                )
                .order_by("pk")
            )
            return _QuerysetIntegerPathFilter.apply_sync(filter, queryset, info)

        rows: QuerySet[scalar_models.ScalarSpecimen] = strawberry.field(
            resolver=_rows,
            graphql_type=StrawberryList(QuerysetPathOutput),
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config(), error_policy={"enabled": False})


def _post_typed_queryset_path(
    document: str,
    variables: JSONObject,
    schema: DjangoSchema | None = None,
) -> JSONObject:
    if schema is None:
        kept = cleaned_specimen("kept", kept=True)
        child = cleaned_specimen("child", kept=False)
        child.parent = kept
        child.save(update_fields=["parent"])
    _CURRENT["schema"] = schema or _typed_queryset_path_holder()
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                variables=variables,
                url="/graphql-scalar-predicates/",
            )
    finally:
        _CURRENT["schema"] = None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("criteria", "labels", "statements"),
    [
        pytest.param(
            "annotatedAtLeast: { gte: $number }",
            ("kept", "child"),
            1,
            id="annotation-gte",
        ),
        pytest.param("annotatedBelow: { lt: $number }", (), 0, id="annotation-lt"),
        pytest.param(
            "childrenAtLeast: { gte: $number }",
            ("kept", "child"),
            1,
            id="aggregate-annotation-gte",
        ),
        pytest.param(
            "parentBigAtLeast: { gte: $number }",
            ("child",),
            1,
            id="filtered-relation-gte",
        ),
        pytest.param("parentBigBelow: { lt: $number }", (), 0, id="filtered-relation-lt"),
    ],
)
def test_a_typed_decimal_past_a_queryset_integer_path_answers_without_being_converted(
    criteria: str,
    labels: tuple[str, ...],
    statements: int,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A path only the queryset resolves is held to its integer column's range on the wire.

    ``n`` annotates ``signed_big``, ``kids`` counts ``children`` (an output field no model
    owns) and ``par`` aliases ``parent`` through a ``FilteredRelation``; the declared
    ``NumberFilter`` over each publishes ``Decimal``,
    which carries ``-1e999999999999999999`` to a form capped only from above. The
    comparison reads which end of the 64-bit range it lies past, never its ``int()``.
    """
    sqls = record_compiled_sql()
    payload = _post_typed_queryset_path(
        "query($number: Decimal!) { rows(filter: { %s }) { label } }" % criteria,
        {"number": "-1e999999999999999999"},
    )
    assert payload == _expected(labels), payload
    assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == statements, sqls


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("criteria", "key"),
    [
        pytest.param(
            "annotatedYearAfter: { yearGt: $number }",
            "annotated_year_after",
            id="annotation",
        ),
        pytest.param(
            "parentYearAfter: { yearGt: $number }",
            "parent_year_after",
            id="filtered-relation",
        ),
    ],
)
def test_a_typed_decimal_past_a_queryset_paths_year_is_refused_without_being_converted(
    criteria: str,
    key: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A ``year`` of a date annotation or of a column past a ``FilteredRelation`` alias is held.

    The transform's ``IntegerField`` output holds ``-1e999999999999999999`` to one past
    the end of its range, which the database cannot bind as a year: ``FILTER_INVALID``
    keyed to the form field, as the same ``year__gt`` over the model's own column answers.
    """
    sqls = record_compiled_sql()
    payload = _post_typed_queryset_path(
        "query($number: Decimal!) { rows(filter: { %s }) { label } }" % criteria,
        {"number": "-1e999999999999999999"},
    )
    _refusal(payload, key)
    assert _root_sql(sqls, scalar_models.ScalarSpecimen) == [], sqls


@pytest.mark.django_db
def test_a_typed_decimal_past_a_filtered_relation_key_answers_as_one_past_the_range() -> None:
    """``par`` compared as the relation is held to its target key's range, never converted.

    The ``FilteredRelation`` alias's ``exact`` prepares a value through the target's
    primary key, so ``-1e999999999999999999`` answers as ``-9223372036854775809``, the
    integer one past that key's 64-bit range, does: as the backend answers Django's own
    ``par`` comparison with it, SQLite's driver unable to bind it and PostgreSQL comparing
    it and matching no row.
    """
    document = (
        "query($number: Decimal!) { rows(filter: { parentIs: { exact: $number } }) { label } }"
    )
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=False)
    child.parent = kept
    child.save(update_fields=["parent"])
    answer = database_answer(
        scalar_models.ScalarSpecimen.objects.alias(par=FilteredRelation("parent"))
        .filter(par=-(2**63) - 1)
        .order_by("pk")
        .values_list("label", flat=True),
    )
    schema = _typed_queryset_path_holder()
    past = _post_typed_queryset_path(document, {"number": "-1e999999999999999999"}, schema)
    assert_database_answer(past, "rows", answer)
    one_past = _post_typed_queryset_path(document, {"number": str(-(2**63) - 1)}, schema)
    assert past == one_past, past


@pytest.mark.django_db
def test_a_pattern_lookup_over_an_integer_annotation_compares_the_decimal_as_sent() -> None:
    """A ``regex`` over ``n`` never converts its value, so nothing is held: parity with the parent.

    Django's ``Regex`` does not prepare its value through the annotation's output
    (``Lookup.prepare_rhs`` false), so ``1e40`` reaches the backend as the decimal sent and
    answers as Django's own ``n__regex`` with it: SQLite matches its spelling and finds no
    row, PostgreSQL has no ``text ~ numeric`` operator and refuses it. Held to ``2**63`` it
    would be bound past what SQLite binds.
    """
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=False)
    child.parent = kept
    child.save(update_fields=["parent"])
    answer = database_answer(
        scalar_models.ScalarSpecimen.objects.annotate(n=F("signed_big"))
        .filter(n__regex=Decimal("1e40"))
        .order_by("pk")
        .values_list("label", flat=True),
    )
    payload = _post_typed_queryset_path(
        "query($number: Decimal!) { rows(filter: { annotatedMatching: { regex: $number } }) { label } }",
        {"number": "1e40"},
        _typed_queryset_path_holder(),
    )
    assert_database_answer(payload, "rows", answer)


class _DivisibleBy(django_models.Lookup):
    """A project lookup on integer columns, as Django's custom-lookup guide writes one."""

    lookup_name = "divisible_by"

    @override
    def as_sql(self, compiler: SQLCompiler, connection: BaseDatabaseWrapper) -> _AsSqlType:
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        return f"{lhs} %% {rhs} = 0", (*lhs_params, *rhs_params)


@contextlib.contextmanager
def _registered_lookup(
    field_class: type[django_models.Field[object, object]],
    lookup: type[django_models.Lookup],
) -> Generator[None]:
    """Register ``lookup`` on ``field_class`` while open, then drop the operands it resolved.

    ``filters/base.py`` caches each column's resolved lookup operand for the process; an
    entry written under the registration would outlive it into the next test on the
    worker.
    """
    try:
        with register_lookup(field_class, lookup):
            yield
    finally:
        _lookup_operand.cache_clear()
        _model_lookup_operand.cache_clear()


class _DivisibleAnnotationFilter(FilterSet):
    divisible = django_filters.NumberFilter(field_name="n", lookup_expr="divisible_by")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)


@pytest.mark.django_db
def test_a_project_lookup_over_an_integer_annotation_receives_the_number_as_sent() -> None:
    """A ``register_lookup`` lookup over a path only the queryset resolves is never held.

    ``divisible_by`` prepares ``-5`` through ``n`` (``unsigned_big``) but reads more than
    which side of the range ``-5`` lies on: held to ``-1``, every row would divide by it.
    It answers the rows holding 10, 0 and 15, as Django prepares ``-5``.
    """
    for label, stored in (
        ("a", 10),
        ("b", 7),
        ("c", 0),
        ("d", 15),
    ):
        row = cleaned_specimen(label, kept=False)
        row.unsigned_big = stored
        row.save(update_fields=["unsigned_big"])
    with _registered_lookup(django_models.IntegerField, _DivisibleBy):

        class DivisibleOutput(DjangoType):
            class Meta:
                model = scalar_models.ScalarSpecimen
                fields = ("label",)
                filterset_class = _DivisibleAnnotationFilter

        @strawberry.type
        class Query:
            def _rows(
                self,
                info: Info[object, object],
                filter: FilterInput[_DivisibleAnnotationFilter],  # noqa: A002
            ) -> QuerySet[scalar_models.ScalarSpecimen]:
                queryset = scalar_models.ScalarSpecimen.objects.annotate(
                    n=F("unsigned_big"),
                ).order_by("label")
                return _DivisibleAnnotationFilter.apply_sync(filter, queryset, info)

            rows: QuerySet[scalar_models.ScalarSpecimen] = strawberry.field(
                resolver=_rows,
                graphql_type=StrawberryList(DivisibleOutput),
            )

        finalize_django_types()
        payload = _post_typed_queryset_path(
            "query($number: Decimal!) { rows(filter: { divisible: { divisibleBy: $number } }) { label } }",
            {"number": "-5"},
            DjangoSchema(query=Query, config=strawberry_config()),
        )
    assert payload == _expected(("a", "c", "d")), payload


@pytest.mark.django_db
def test_a_declared_list_over_an_integer_annotation_compares_its_members_as_its_output(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A ``ListFilter`` over ``n``, a path no model column names, publishes text members.

    Each member is cleaned and compared as the annotation's output field, read over the
    queryset the set was handed, as a member of an integer column is.
    """
    sqls = record_compiled_sql()
    payload = _post_typed_queryset_path(
        '{ rows(filter: { annotatedAmong: { in: ["7"] } }) { label } }',
        {},
    )
    assert payload == _expected(("kept",)), payload
    assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == 1, sqls


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("criteria", "labels"),
    [
        pytest.param(
            'annotatedAmong: { in: ["-1e999999999999999999", "7"] }',
            ("kept",),
            id="integer-member-held",
        ),
        pytest.param(
            f'annotatedAmong: {{ in: ["{_PAST_INT64}", "1.5"] }}',
            (),
            id="integer-members-naming-no-row-drop",
        ),
        pytest.param(
            f'annotatedSpan: {{ range: {{ start: "{_BEFORE_INT64}", end: "8" }} }}',
            ("kept",),
            id="integer-range-below-the-column",
        ),
        pytest.param(
            f'annotatedSpan: {{ range: {{ start: "8", end: "{_PAST_INT64}" }} }}',
            ("child",),
            id="integer-range-past-the-column",
        ),
        pytest.param(
            'datedYearsAmong: { yearIn: ["2026"] }',
            ("kept", "child"),
            id="transform-member",
        ),
        pytest.param(
            'datedYearsAmong: { yearIn: ["2026.5"] }',
            ("kept", "child"),
            id="transform-fraction-as-the-column",
        ),
        pytest.param(
            f'parentsAmong: {{ in: ["{_PAST_INT64}"] }}',
            (),
            id="alias-member-naming-no-row-drops",
        ),
        pytest.param('namesAmong: { in: ["  kept  "] }', ("kept",), id="text-member-stripped"),
        pytest.param('costsAmong: { in: ["10.50"] }', ("kept",), id="decimal-member"),
    ],
)
def test_a_declared_list_or_range_over_a_queryset_path_compares_as_that_queryset_does(
    criteria: str,
    labels: tuple[str, ...],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Members and bounds over a path only the queryset resolves read its output field.

    ``n`` annotates ``signed_big``, ``d`` annotates ``occurred_on`` and ``par`` aliases
    ``parent``: a list over ``n`` holds a decimal past the 64-bit range and drops members
    naming no integer row, a range over ``n`` applies as ``gte`` + ``lte`` so a bound past
    the range widens, a ``year__in`` over ``d`` compares the transform's integers as the
    column's would (a fraction truncated, as Django truncates it), a list over the alias
    compares its target key, dropping a member past it, and a text member over ``named``
    (``label``) is stripped as the column's is. Each runs one statement.
    """
    sqls = record_compiled_sql()
    payload = _post_typed_queryset_path(
        "{ rows(filter: { %s }) { label } }" % criteria,
        {},
    )
    assert payload == _expected(labels), payload
    assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == (1 if labels else 0), sqls


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("criteria", "key"),
    [
        pytest.param('annotatedAmong: { in: ["abc"] }', "annotated_among", id="integer-member"),
        pytest.param(
            'annotatedSpan: { range: { start: "abc", end: "8" } }',
            "annotated_span",
            id="integer-bound",
        ),
        pytest.param('datedYearsAmong: { yearIn: ["abc"] }', "dated_years_among", id="transform"),
        pytest.param('parentsAmong: { in: ["abc"] }', "parents_among", id="alias-key"),
        pytest.param(
            'costsAmong: { in: ["1e60"] }',
            "costs_among",
            id="decimal-past-the-number-cap",
        ),
    ],
)
def test_a_value_a_queryset_path_cannot_hold_is_its_form_error(
    criteria: str,
    key: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A value the path's output cannot hold is its form error, before any statement.

    The value is cleaned as the queryset compares it, the annotation's output field, the
    ``year`` transform's ``IntegerField``, the alias's target key, never handed to Django:
    text no number spells is ``Enter a number.``, and a decimal past django-filter's
    ``1e50`` cap the cap's refusal, as over the ``price`` column itself.
    """
    sqls = record_compiled_sql()
    payload = _post_typed_queryset_path(
        "{ rows(filter: { %s }) { label } }" % criteria,
        {},
    )
    refusal = (
        {"message": "Ensure this value is less than or equal to 1e+50.", "code": "max_value"}
        if key == "costs_among"
        else {"message": "Enter a number.", "code": "invalid"}
    )
    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {key: [refusal]},
    }
    assert _root_sql(sqls, scalar_models.ScalarSpecimen) == [], sqls


@pytest.mark.django_db
def test_a_declared_list_over_a_filtered_relation_alias_compares_its_target_key() -> None:
    """``parentsAmong`` names the alias itself: each member is a key of its target, ``parent``."""
    kept_pk = _kept_pk_after_seed()
    payload = _post_typed_queryset_path(
        '{ rows(filter: { parentsAmong: { in: ["%s", "%s.0"] } }) { label } }'
        % (kept_pk, kept_pk),
        {},
        _typed_queryset_path_holder(),
    )
    assert payload == _expected(("child",)), payload


def _kept_pk_after_seed() -> str:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=False)
    child.parent = kept
    child.save(update_fields=["parent"])
    return str(saved_pk(kept))


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("node_id", "labels"),
    [
        pytest.param("tag", ("child",), id="key"),
        pytest.param("abc", None, id="junk"),
        pytest.param(_PAST_INT64, None, id="past-the-key"),
    ],
)
def test_a_global_id_over_a_filtered_relation_alias_is_coerced_through_its_target_key(
    node_id: str,
    labels: tuple[str, ...] | None,
) -> None:
    """``tagNode`` names an alias into a model no type exposes: its node id is the target key's.

    ``vtag`` joins ``tag``, whose ``ScalarSpecimenTag`` no ``DjangoType`` of this schema
    exposes, so the id is coerced through that model's primary key, the column the alias
    compares: one that key cannot hold is ``GLOBALID_INVALID``, never Django's
    ``ValueError``.
    """
    _ = _kept_pk_after_seed()
    tag = scalar_models.ScalarSpecimenTag.objects.create(label="tagged")
    _ = scalar_models.ScalarSpecimen.objects.filter(label="child").update(tag=tag)
    global_id = to_base64("Anything", str(saved_pk(tag)) if node_id == "tag" else node_id)
    schema = _typed_queryset_path_holder()
    payload = _post_typed_queryset_path(
        '{ rows(filter: { tagNode: { exact: "%s" } }) { label } }' % global_id,
        {},
        schema,
    )
    if labels is not None:
        assert payload == _expected(labels), payload
        return
    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "extensions") == {"code": "GLOBALID_INVALID"}


def _child_pk_after_seed() -> str:
    _ = _kept_pk_after_seed()
    return str(saved_pk(scalar_models.ScalarSpecimen.objects.get(label="child")))


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("members", "labels"),
    [
        pytest.param(["child"], ("kept",), id="key"),
        pytest.param(["child", "1.5", _PAST_INT64], ("kept",), id="members-naming-no-row-drop"),
        pytest.param([_PAST_INT64], (), id="every-member-drops"),
        pytest.param(["abc"], None, id="junk"),
    ],
)
def test_a_declared_list_over_a_reverse_relation_alias_compares_the_related_key(
    members: list[str],
    labels: tuple[str, ...] | None,
) -> None:
    """``offspringAmong`` names a ``FilteredRelation`` alias of ``children``: the child's key.

    The alias is a reverse relation, answered as the model answers ``children``: each member
    is cleaned and compared as the child's primary key, so a member naming no integer row
    drops and text no number spells is ``Enter a number.``, never Django's ``ValueError``.
    """
    child_pk = _child_pk_after_seed()
    sent = ", ".join(f'"{child_pk if member == "child" else member}"' for member in members)
    payload = _post_typed_queryset_path(
        "{ rows(filter: { offspringAmong: { in: [%s] } }) { label } }" % sent,
        {},
        _typed_queryset_path_holder(),
    )
    if labels is not None:
        assert payload == _expected(labels), payload
        return
    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {"offspring_among": [{"message": "Enter a number.", "code": "invalid"}]},
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("members", "labels"),
    [
        pytest.param(["-1e999999999999999999"], (), id="all-extreme-members-drop"),
        pytest.param(["child", "-1e999999999999999999"], ("kept",), id="valid-and-extreme"),
    ],
)
def test_a_reverse_alias_drops_extreme_negative_members_before_integer_conversion(
    members: list[str],
    labels: tuple[str, ...],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The real reverse alias compares its key without converting an enormous Decimal."""
    child_pk = _child_pk_after_seed()
    sent = ", ".join(f'"{child_pk if member == "child" else member}"' for member in members)
    sqls = record_compiled_sql()
    payload = _post_typed_queryset_path(
        "{ rows(filter: { offspringAmong: { in: [%s] } }) { label } }" % sent,
        {},
        _typed_queryset_path_holder(),
    )
    assert payload == _expected(labels), payload
    if not labels:
        assert _root_sql(sqls, scalar_models.ScalarSpecimen) == [], sqls


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("criterion", "labels"),
    [
        pytest.param(
            'crossedBigSpan: { signedBigRange: { start: "7", end: "9223372036854775808" } }',
            ("child",),
            id="continued-integer-range",
        ),
        pytest.param(
            'directBigSpan: { range: { start: "7", end: "9223372036854775808" } }',
            ("child",),
            id="direct-integer-range-control",
        ),
        pytest.param(
            'crossedBigAmong: { signedBigIn: ["7.5"] }',
            (),
            id="continued-fractional-member",
        ),
        pytest.param(
            'directBigAmong: { in: ["7.5"] }',
            (),
            id="direct-fractional-member-control",
        ),
    ],
)
def test_a_continued_alias_uses_its_terminal_integer_column_and_operation(
    criterion: str,
    labels: tuple[str, ...],
) -> None:
    """The alias spelling and direct spelling clean and apply the same lookup."""
    _kept_pk_after_seed()
    payload = _post_typed_queryset_path(
        "{ rows(filter: { %s }) { label } }" % criterion,
        {},
        _typed_queryset_path_holder(),
    )
    assert payload == _expected(labels), payload


@pytest.mark.django_db
def test_a_continued_alias_with_implicit_exact_cleans_a_lone_range_bound() -> None:
    """Django's implicit exact still supplies the terminal integer comparison field."""
    _kept_pk_after_seed()
    payload = _post_typed_queryset_path(
        '{ rows(filter: { implicitBigSpan: { signedBig: { start: "abc" } } }) { label } }',
        {},
        _typed_queryset_path_holder(),
    )
    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {"implicit_big_span": [{"message": "Enter a number.", "code": "invalid"}]},
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("leaf", "node_id", "labels"),
    [
        pytest.param("parentRefNode", "kept", ("child",), id="key-annotation"),
        pytest.param("parentRefNode", _PAST_INT64, None, id="key-annotation-past-the-key"),
    ],
)
def test_a_global_id_over_a_queryset_relation_path_is_coerced_through_the_related_key(
    leaf: str,
    node_id: str,
    labels: tuple[str, ...] | None,
) -> None:
    """A ``GlobalIDFilter`` with no type to resolve compares its node id on the related key.

    ``parent_ref`` annotates the ``parent`` key: the node id is coerced through the
    parent's primary key, so one that key cannot hold is ``GLOBALID_INVALID``, as over the
    model's own relation.
    """
    kept_pk = _kept_pk_after_seed()
    named = kept_pk if node_id == "kept" else node_id
    payload = _post_typed_queryset_path(
        '{ rows(filter: { %s: { exact: "%s" } }) { label } }' % (leaf, to_base64("Any", named)),
        {},
        _typed_queryset_path_holder(),
    )
    if labels is not None:
        assert payload == _expected(labels), payload
        return
    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "extensions") == {"code": "GLOBALID_INVALID"}


#: The refusal of an id over a relation into ``QuerysetPathOutput``, which is no Relay node.
_UNVALIDATABLE_SPECIMEN = (
    "GlobalID filter target QuerysetPathOutput has no recorded globalid strategy; the type "
    "was not finalized as a Relay node, so its filter input cannot validate a GlobalID."
)


@pytest.mark.django_db
@pytest.mark.parametrize("named", ["kept", "child", "abc"])
@pytest.mark.parametrize(
    "leaf",
    [
        "parNode",
        "parentNode",
        "offspringNode",
        "childrenNode",
    ],
)
def test_a_global_id_over_an_alias_of_a_typed_relation_answers_as_that_relation(
    leaf: str,
    named: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """``par`` / ``offspring`` answer as ``parent`` / ``children``: their target is no Relay node.

    The aliases join the self relations into ``ScalarSpecimen``, which
    ``QuerysetPathOutput`` exposes without a Relay id, so every id is refused as
    ``GLOBALID_UNVALIDATABLE`` before any statement, over the alias as over the relation.
    """
    kept_pk = _kept_pk_after_seed()
    child_pk = str(saved_pk(scalar_models.ScalarSpecimen.objects.get(label="child")))
    node_id = {"kept": kept_pk, "child": child_pk}.get(named, named)
    schema = _typed_queryset_path_holder()
    sqls = record_compiled_sql()
    payload = _post_typed_queryset_path(
        '{ rows(filter: { %s: { exact: "%s" } }) { label } }' % (leaf, to_base64("Any", node_id)),
        {},
        schema,
    )
    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "message") == _UNVALIDATABLE_SPECIMEN
    assert json_at(payload, "errors", 0, "extensions") == {"code": "GLOBALID_UNVALIDATABLE"}
    assert _root_sql(sqls, scalar_models.ScalarSpecimen) == [], sqls


class _LateAnnotationFilter(FilterSet):
    """A consumer ``filter_queryset`` annotating ``late`` before the leaves run."""

    late_at_least = django_filters.NumberFilter(field_name="late", lookup_expr="gte")
    late_span = RangeFilter(field_name="late", lookup_expr="range")
    late_among = ListFilter(field_name="late", lookup_expr="in")
    late_pair = ListFilter(field_name="late", lookup_expr="range")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)

    @override
    def filter_queryset(self, queryset: QuerySet[_M]) -> QuerySet[_M]:
        return super().filter_queryset(queryset.annotate(late=F("signed_big")))


@pytest.mark.django_db
@pytest.mark.parametrize("late_alias", [False, True], ids=["handed", "added-in-filter_queryset"])
@pytest.mark.parametrize(
    ("number", "labels"),
    [
        pytest.param("child", ("kept",), id="related-key"),
        pytest.param("0", (), id="missing-key"),
        pytest.param("-1e999999999999999999", (), id="held-below-key"),
    ],
)
def test_a_reverse_alias_added_only_by_filter_queryset_keeps_its_integer_target(
    number: str,
    labels: tuple[str, ...],
    *,
    late_alias: bool,
) -> None:
    """A reverse alias uses its native related lookup, holding huge decimals to one past.

    The related lookup lacks integer-column overflow handling. Ask the same
    one-past wire value for its backend-owned outcome rather than assuming it
    matches no rows; the fitting and missing-key controls retain their rowsets.
    """
    child_pk = _child_pk_after_seed()

    class ReverseAliasFilter(FilterSet):
        child_is = django_filters.NumberFilter(field_name="offspring", lookup_expr="exact")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

        @override
        def filter_queryset(self, queryset: QuerySet[_M]) -> QuerySet[_M]:
            if late_alias:
                queryset = queryset.alias(offspring=FilteredRelation("children"))
            return super().filter_queryset(queryset)

    class ReverseAliasOutput(DjangoType):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = ("label",)
            filterset_class = ReverseAliasFilter

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: Info[object, object],
            filter: FilterInput[ReverseAliasFilter],  # noqa: A002
        ) -> QuerySet[scalar_models.ScalarSpecimen]:
            rows = scalar_models.ScalarSpecimen.objects.order_by("pk")
            if not late_alias:
                rows = rows.alias(offspring=FilteredRelation("children"))
            return ReverseAliasFilter.apply_sync(filter, rows, info)

        # The local consumer class is resolved now, before Strawberry evaluates
        # this module's postponed annotations outside the test's local scope.
        _rows.__annotations__["filter"] = FilterInput[ReverseAliasFilter]

        rows: QuerySet[scalar_models.ScalarSpecimen] = strawberry.field(
            resolver=_rows,
            graphql_type=StrawberryList(ReverseAliasOutput),
        )

    finalize_django_types()
    sent = child_pk if number == "child" else number
    schema = DjangoSchema(query=Query, config=strawberry_config(), error_policy={"enabled": False})
    document = (
        "query($number: Decimal!) { rows(filter: { childIs: { exact: $number } }) { label } }"
    )
    payload = _post_typed_queryset_path(
        document,
        {"number": sent},
        schema,
    )
    if number == "-1e999999999999999999":
        one_past = _post_typed_queryset_path(document, {"number": str(-(2**63) - 1)}, schema)
        assert payload == one_past, payload
    else:
        assert payload == _expected(labels), payload


@pytest.mark.django_db
def test_a_typed_decimal_past_an_annotation_only_the_applied_queryset_holds_is_held(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """An annotation a ``filter_queryset`` adds before the leaves is read on that queryset.

    The set was handed a queryset without ``late``, so the filter's form reads no field
    for it; the leaf runs on the annotated queryset, whose ``late`` is ``signed_big``'s
    integer output, so ``-1e999999999999999999`` compares as one below the 64-bit range,
    never converted.
    """
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("child", kept=False)

    class LateOutput(DjangoType):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = ("label",)
            filterset_class = _LateAnnotationFilter

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: Info[object, object],
            filter: FilterInput[_LateAnnotationFilter],  # noqa: A002
        ) -> QuerySet[scalar_models.ScalarSpecimen]:
            return _LateAnnotationFilter.apply_sync(
                filter,
                scalar_models.ScalarSpecimen.objects.order_by("pk"),
                info,
            )

        rows: QuerySet[scalar_models.ScalarSpecimen] = strawberry.field(
            resolver=_rows,
            graphql_type=StrawberryList(LateOutput),
        )

    finalize_django_types()
    sqls = record_compiled_sql()
    payload = _post_typed_queryset_path(
        "query($number: Decimal!) { rows(filter: { lateAtLeast: { gte: $number } }) { label } }",
        {"number": "-1e999999999999999999"},
        DjangoSchema(query=Query, config=strawberry_config(), error_policy={"enabled": False}),
    )
    assert payload == _expected(("kept", "child")), payload
    assert len(_root_sql(sqls, scalar_models.ScalarSpecimen)) == 1, sqls


def _served_late_schema() -> DjangoSchema:
    """``_LateAnnotationFilter`` served on a connection: ``apply_sync`` / ``apply_async`` run it."""

    class LateNode(DjangoType):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = ("id", "label")
            interfaces = (relay.Node,)
            filterset_class = _LateAnnotationFilter

    @strawberry.type
    class Query:
        rows: DjangoConnection[LateNode] = DjangoConnectionField(LateNode)

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


_SERVED_LATE_ROWS = (
    "query($where: _LateAnnotationFilterInputType) "
    "{ rows(filter: $where) { edges { node { label } } } }"
)
_NOT_A_NUMBER = [{"message": "Enter a number.", "code": "invalid"}]


async def _post_served(schema: DjangoSchema, where: JSONObject, transport: str) -> JSONObject:
    """Send ``where`` to the served set over the sync view or the async one."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if transport == "sync":
                return await sync_to_async(graphql_payload)(
                    _SERVED_LATE_ROWS,
                    variables={"where": where},
                    url="/graphql-scalar-predicates/",
                )
            result = await AsyncTestClient().query(
                _SERVED_LATE_ROWS,
                variables={"where": where},
                assert_no_errors=False,
                url="/graphql-scalar-predicates-async/",
            )
            return response_json(result.response)
    finally:
        _CURRENT["schema"] = None


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("where", "answer"),
    [
        pytest.param(
            {"lateSpan": {"range": {"start": "abc", "end": "8"}}},
            {"late_span": _NOT_A_NUMBER},
            id="junk-bound",
        ),
        pytest.param(
            {"lateAmong": {"in": ["7", "abc"]}},
            {"late_among": _NOT_A_NUMBER},
            id="junk-member",
        ),
        pytest.param(
            {"or": [{"lateSpan": {"range": {"start": "abc"}}}, {"lateAmong": {"in": ["7"]}}]},
            {"or_0__late_span": _NOT_A_NUMBER},
            id="junk-bound-in-an-or-arm",
        ),
        pytest.param(
            {"not": {"lateAmong": {"in": ["abc"]}}},
            {"not__late_among": _NOT_A_NUMBER},
            id="junk-member-under-not",
        ),
        pytest.param(
            {"latePair": {"range": ["7"]}},
            {
                "late_pair": [
                    {"message": "Range query expects two values.", "code": "invalid_values"},
                ],
            },
            id="range-list-of-one",
        ),
        pytest.param({"latePair": {"range": ["1", "8"]}}, ["kept"], id="range-list"),
        pytest.param({"lateSpan": {"range": {"start": "1", "end": "8"}}}, ["kept"], id="bounds"),
        pytest.param({"lateSpan": {"range": {"start": "8"}}}, ["child"], id="one-bound"),
        pytest.param({"lateSpan": {"range": {}}}, ["kept", "child"], id="no-bound"),
        pytest.param({"lateAmong": {"in": ["900"]}}, ["child"], id="member"),
        pytest.param(
            {"lateAmong": {"in": ["-1e999999999999999999", "7"]}},
            ["kept"],
            id="member-past-any-integer-drops",
        ),
        pytest.param({"lateAmong": {"in": []}}, [], id="no-member"),
        pytest.param(
            {"or": [{"lateSpan": {"range": {"start": "8"}}}, {"lateAmong": {"in": ["7"]}}]},
            ["kept", "child"],
            id="or-arms",
        ),
        pytest.param({"not": {"lateAmong": {"in": ["7"]}}}, ["child"], id="not-arm"),
    ],
)
async def test_a_served_value_over_an_annotation_filter_queryset_adds_is_cleaned_as_it_compares(
    transport: str,
    where: JSONObject,
    answer: JSONObject | list[str],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A served list or range over ``late``, which only ``filter_queryset`` adds, cleans its values.

    The connection hands the set unannotated rows, so the form reads no field for ``late``;
    each bound and member is cleaned over the queryset the override passes on, as
    ``signed_big``'s integer: junk is ``FILTER_INVALID`` keyed by the leaf, a logical arm's
    included, before any statement, never a masked error; a member past any integer drops; an
    empty list matches no row; and the rows answer in one statement, under ``apply_sync`` and
    ``apply_async`` alike.
    """
    await sync_to_async(cleaned_specimen)("kept", kept=True)
    await sync_to_async(cleaned_specimen)("child", kept=False)
    schema = await sync_to_async(_served_late_schema)()
    statements = record_compiled_sql(scalar_models.ScalarSpecimen._meta.db_table)

    payload = await _post_served(schema, where, transport)

    if isinstance(answer, dict):
        assert payload["data"] is None, payload
        assert json_at(payload, "errors", 0, "message") == "Invalid filter input"
        assert json_at(payload, "errors", 0, "extensions") == {
            "code": "FILTER_INVALID",
            "errors": answer,
        }
        assert statements == []
    else:
        edges = json_list(payload, "data", "rows", "edges")
        assert [json_str(edge, "node", "label") for edge in edges] == answer, payload
        # An empty list matches no row: Django compiles it to no statement at all.
        assert len(statements) == (1 if answer else 0), statements


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
    "year-in-integral-decimal": (
        {"day_years_among": {"in_": ["2021.0"]}},
        ("new-year-2021", "mid-2021"),
    ),
    "year-in-integral-exponent": (
        {"day_years_among": {"in_": ["2.021e3"]}},
        ("new-year-2021", "mid-2021"),
    ),
    "year-range-integral-decimal": (
        {"day_years_span": {"range": {"start": "2021.0", "end": "2021.0"}}},
        ("new-year-2021", "mid-2021"),
    ),
    "year-range-start-integral-decimal": (
        {"day_years_span": {"range": {"start": "2021.0"}}},
        (
            "new-year-2021",
            "mid-2021",
            "mid-2022",
            "mid-9998",
        ),
    ),
    "year-range-end-integral-decimal": (
        {"day_years_span": {"range": {"end": "2021.0"}}},
        (
            "mid-2019",
            "mid-2020",
            "new-year-2021",
            "mid-2021",
        ),
    ),
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
def test_projected_child_lookup_crossing_relations_uses_its_declaring_model() -> None:
    """A flat projected filter types and executes a child's crossed text column over HTTP."""
    first = library_models.Branch.objects.create(name="b1", city="Boston")
    other = library_models.Branch.objects.create(name="b1extra", city="Boston")
    first_shelf = library_models.Shelf.objects.create(code="S1", topic="Fiction", branch=first)
    other_shelf = library_models.Shelf.objects.create(code="S2", topic="History", branch=other)
    library_models.Book.objects.create(title="first", shelf=first_shelf)
    library_models.Book.objects.create(title="other", shelf=other_shelf)

    class ShelfByBranchName(FilterSet):
        branch_named = django_filters.CharFilter(field_name="branch", lookup_expr="name__contains")

        class Meta:
            model = library_models.Shelf
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
            self.filters["branch_named"].lookup_expr = "name__iexact"

    class BookByShelf(FilterSet):
        shelf = RelatedFilter(ShelfByBranchName, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = []

    class BranchOutput(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("name",)

    class ShelfOutput(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("code",)

    class BookOutput(DjangoType):
        class Meta:
            model = library_models.Book
            fields = ("title",)
            filterset_class = BookByShelf

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: Info[object, object],
            filter: FilterInput[BookByShelf],  # noqa: A002
        ) -> QuerySet[library_models.Book]:
            return BookByShelf.apply_sync(
                filter,
                library_models.Book.objects.order_by("pk"),
                info,
            )

        # The local consumer class is resolved now, before Strawberry evaluates
        # this module's postponed annotations outside the test's local scope.
        _rows.__annotations__["filter"] = FilterInput[BookByShelf]

        rows: QuerySet[library_models.Book] = strawberry.field(
            resolver=_rows,
            graphql_type=StrawberryList(BookOutput),
        )

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        types=(BranchOutput, ShelfOutput),
        config=strawberry_config(),
        error_policy={"enabled": False},
    )
    payload = _post_typed_queryset_path(
        '{ rows(filter: {shelfBranchNamed: {nameContains: "b1"}}) { title } }',
        {},
        schema,
    )
    assert payload == {"data": {"rows": [{"title": "first"}]}}, payload


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
