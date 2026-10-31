"""Real-backend numeric format and timezone-setting filter boundaries over HTTP.

Fifteen numeric cases use shipped ScalarSpecimen filters. Two need a legitimate
consumer annotation with an unbounded Decimal output field, so a native holder
publishes its NumberFilter. Decimal strings preserve exponents and written
fractional zeros through the actual scalar/form pipeline. Accepted comparisons
ask the executing backend through Django's ORM; notably SQLite and PostgreSQL
do not give the same equality answer for a tiny but valid PostgreSQL numeric.
Generated DateTime inputs receive timestamp values through their published scalar.
The accepted comparisons use the database connection handling the actual request.
"""

import datetime
import uuid
from collections.abc import Sequence
from decimal import Decimal
from functools import wraps
from importlib import import_module
from typing import Annotated, NamedTuple

import pytest
import strawberry
from apps.scalars import models
from django.db import connection
from django.db import models as django_models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django.utils import timezone
from django_filters import NumberFilter
from graphql import GraphQLInputObjectType, get_named_type
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_object,
)
from strawberry.types.base import StrawberryObjectDefinition

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterInput, FilterSet
from django_strawberry_framework.utils._narrowing import read_attr, require_instance
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_input_fields,
    graphql_type_of,
)
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_UNBINDABLE = [{"message": "Enter a value the database can represent.", "code": "invalid"}]


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-bindability/", _graphql_view)]


def _shipped_schema() -> DjangoSchema:
    return require_instance(read_attr(import_module("config.schema"), "schema"), DjangoSchema)


def _input(schema: DjangoSchema, root: str) -> GraphQLInputObjectType:
    query = schema._schema.query_type
    assert query is not None
    named = get_named_type(graphql_type_of(graphql_fields(query)[root].args["filter"]))
    assert isinstance(named, GraphQLInputObjectType)
    return named


def _where(
    schema: DjangoSchema,
    root: str,
    python_path: Sequence[str],
    value: object,
) -> JSONObject:
    """Read the input's definitions and NameConverter, including actual range-bound names."""
    current = _input(schema, root)
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


def _post(schema: DjangoSchema, root: str, where: JSONObject) -> JSONObject:
    document = (
        f"query($where: {_input(schema, root).name}!) {{ {root}(filter: $where) {{ id label }} }}"
    )
    if root == "allScalarSpecimens":
        with override_settings(ROOT_URLCONF="config.urls"):
            return graphql_payload(document, variables={"where": where})
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                variables={"where": where},
                url="/graphql-bindability/",
            )
    finally:
        _CURRENT["schema"] = None


def _expected(root: str, rows: Sequence[models.ScalarSpecimen]) -> JSONObject:
    return {"data": {root: [{"id": saved_pk(row), "label": row.label} for row in rows]}}


def _assert_unbindable(payload: JSONObject, root: str, form_key: str) -> None:
    assert payload["data"] is None, payload
    assert len(json_list(payload, "errors")) == 1
    assert json_at(payload, "errors", 0, "path") == [root]
    assert json_at(payload, "errors", 0, "message") == "Invalid filter input"
    assert json_at(payload, "errors", 0, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {form_key: _UNBINDABLE},
    }


def _specimen(
    label: str,
    *,
    price: str = "1",
    stamp: datetime.datetime | None = None,
) -> models.ScalarSpecimen:
    if stamp is None:
        stamp = datetime.datetime(2021, 6, 15, 9, 30, tzinfo=datetime.timezone.utc)
    return models.ScalarSpecimen.objects.create(
        label=label,
        price=Decimal(price),
        occurred_on=datetime.date(2021, 6, 15),
        occurred_at=stamp,
        occurred_time=datetime.time(9, 30),
        external_id=uuid.UUID(int=1),
    )


def _prices() -> list[models.ScalarSpecimen]:
    return [_specimen("zero", price="0"), _specimen("one", price="1"), _specimen("two", price="2")]


class _NumericCase(NamedTuple):
    """One representable Decimal input, its independent Django predicate and exact refusal key."""

    path: tuple[str, str]
    values: tuple[str, ...]
    mode: str
    orm_lookup: str
    form_key: str
    refused_on_pg: bool


_NEGATIVE_HUGE = "-1e1000000"
_TINY = "1e-1000000"
_PAST_FRACTION = "1e-16384"
_EDGE_FRACTION = "1e-16383"
_NUMERIC_CASES = {
    "exact-negative-huge": _NumericCase(
        ("price", "exact"),
        (_NEGATIVE_HUGE,),
        "scalar",
        "price",
        "price",
        refused_on_pg=True,
    ),
    "exact-tiny": _NumericCase(
        ("price", "exact"),
        (_TINY,),
        "scalar",
        "price",
        "price",
        refused_on_pg=True,
    ),
    "exact-16384-fraction-digits": _NumericCase(
        ("price", "exact"),
        (_PAST_FRACTION,),
        "scalar",
        "price",
        "price",
        refused_on_pg=True,
    ),
    "exact-16384-trailing-zeros": _NumericCase(
        ("price", "exact"),
        ("1." + "0" * 16384,),
        "scalar",
        "price",
        "price",
        refused_on_pg=True,
    ),
    "gt-tiny": _NumericCase(
        ("price", "gt"),
        (_TINY,),
        "scalar",
        "price__gt",
        "price__gt",
        refused_on_pg=True,
    ),
    "lt-negative-huge": _NumericCase(
        ("price", "lt"),
        (_NEGATIVE_HUGE,),
        "scalar",
        "price__lt",
        "price__lt",
        refused_on_pg=True,
    ),
    "in-member": _NumericCase(
        ("price", "in_"),
        ("1", _PAST_FRACTION),
        "list",
        "price__in",
        "price__in",
        refused_on_pg=True,
    ),
    "range-start": _NumericCase(
        ("price", "range"),
        (_NEGATIVE_HUGE, "1"),
        "list",
        "price__range",
        "price__range",
        refused_on_pg=True,
    ),
    "declared-list": _NumericCase(
        ("price_among", "in_"),
        ("1", _TINY),
        "list",
        "price__in",
        "price_among",
        refused_on_pg=True,
    ),
    "declared-range-bound": _NumericCase(
        ("price_span", "range"),
        ("1", _PAST_FRACTION),
        "span",
        "price__range",
        "price_span",
        refused_on_pg=True,
    ),
    "unbounded-column": _NumericCase(
        ("loose_price", "exact"),
        (_PAST_FRACTION,),
        "scalar",
        "loose_price",
        "loose_price",
        refused_on_pg=True,
    ),
    "exact-16383-fraction-digits": _NumericCase(
        ("price", "exact"),
        (_EDGE_FRACTION,),
        "scalar",
        "price",
        "price",
        refused_on_pg=False,
    ),
    "in-edge": _NumericCase(
        ("price", "in_"),
        ("1", "-" + _EDGE_FRACTION),
        "list",
        "price__in",
        "price__in",
        refused_on_pg=False,
    ),
    "declared-range-edges": _NumericCase(
        ("price_span", "range"),
        ("-" + _EDGE_FRACTION, "1e50"),
        "span",
        "price__range",
        "price_span",
        refused_on_pg=False,
    ),
    "unbounded-edge": _NumericCase(
        ("loose_price", "exact"),
        (_EDGE_FRACTION,),
        "scalar",
        "loose_price",
        "loose_price",
        refused_on_pg=False,
    ),
    "exact-zero-huge-exponent": _NumericCase(
        ("price", "exact"),
        ("0e1000000",),
        "scalar",
        "price",
        "price",
        refused_on_pg=False,
    ),
    "in-zero-past-fraction": _NumericCase(
        ("price", "in_"),
        ("1", "0e-16384"),
        "list",
        "price__in",
        "price__in",
        refused_on_pg=True,
    ),
}
_SHIPPED_NUMERIC = [name for name, case in _NUMERIC_CASES.items() if case.path[0] != "loose_price"]
_ANNOTATED_NUMERIC = ["unbounded-column", "unbounded-edge"]


def _numeric_where(schema: DjangoSchema, root: str, case: _NumericCase) -> JSONObject:
    if case.mode == "span":
        result = _where(schema, root, (*case.path, "start"), case.values[0])
        # Both bounds inhabit the same published range object.
        end = _where(schema, root, (*case.path, "end"), case.values[1])
        first = next(iter(result))
        inner = json_object(result, first)
        other = json_object(end, first)
        range_name = next(iter(inner))
        json_object(inner, range_name).update(json_object(other, range_name))
        return result
    value: object = list(case.values) if case.mode == "list" else case.values[0]
    return _where(schema, root, case.path, value)


def _raw_numeric_answer(
    queryset: django_models.QuerySet[models.ScalarSpecimen],
    case: _NumericCase,
) -> list[models.ScalarSpecimen]:
    """Ask Django and this real backend for the accepted comparison, without a package FilterSet."""
    values = tuple(Decimal(value) for value in case.values)
    operand: object = values[0] if case.mode == "scalar" else values
    return list(queryset.filter(**{case.orm_lookup: operand}).order_by("pk"))


def _assert_no_specimen_sql(sqls: Sequence[str]) -> None:
    assert not [sql for sql in sqls if '"scalars_scalarspecimen"' in sql], sqls


def _numeric_request(
    schema: DjangoSchema,
    root: str,
    case: _NumericCase,
    one: models.ScalarSpecimen,
    queryset: django_models.QuerySet[models.ScalarSpecimen],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    control_path = ("loose_price", "exact") if root == "rows" else ("price", "exact")
    assert _post(schema, root, _where(schema, root, control_path, "1")) == _expected(root, [one])
    if connection.vendor == "postgresql" and case.refused_on_pg:
        sqls = record_compiled_sql()
        payload = _post(schema, root, _numeric_where(schema, root, case))
        _assert_unbindable(payload, root, case.form_key)
        _assert_no_specimen_sql(sqls)
    else:
        expected = _raw_numeric_answer(queryset, case)
        assert _post(schema, root, _numeric_where(schema, root, case)) == _expected(root, expected)


@pytest.mark.django_db
@pytest.mark.parametrize("case", _SHIPPED_NUMERIC)
def test_shipped_decimal_filter_families_use_the_executing_backends_numeric_format(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Published scalar/list/range inputs preserve numeric spellings until real backend preparation."""
    _zero, one, _two = _prices()
    _numeric_request(
        _shipped_schema(),
        "allScalarSpecimens",
        _NUMERIC_CASES[case],
        one,
        models.ScalarSpecimen.objects.all(),
        record_compiled_sql,
    )


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
@pytest.mark.parametrize("case", _ANNOTATED_NUMERIC)
def test_unbounded_decimal_annotation_has_the_same_backend_format_guard(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A real annotation keeps its unbounded Decimal output while the filter checks the bound value."""

    class AnnotatedPriceFilter(FilterSet):
        loose_price = NumberFilter(field_name="loose_price")

        class Meta:
            model = models.ScalarSpecimen
            fields = []

    class AnnotatedPriceSpecimen(DjangoType):
        class Meta:
            model = models.ScalarSpecimen
            fields = ("id", "label")
            filterset_class = AnnotatedPriceFilter

    def priced() -> django_models.QuerySet[models.ScalarSpecimen]:
        return models.ScalarSpecimen.objects.annotate(
            loose_price=django_models.ExpressionWrapper(
                django_models.F("price"),
                output_field=django_models.DecimalField(max_digits=None, decimal_places=None),
            ),
        ).order_by("pk")

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: strawberry.Info[object, object],
            where: Annotated[
                FilterInput[AnnotatedPriceFilter] | None,
                strawberry.argument(name="filter"),
            ] = None,
        ) -> django_models.QuerySet[models.ScalarSpecimen]:
            queryset = priced()
            return (
                queryset
                if where is None
                else AnnotatedPriceFilter.apply_sync(where, queryset, info)
            )

        rows: django_models.QuerySet[models.ScalarSpecimen] = strawberry.field(
            resolver=_rows,
            graphql_type=list[AnnotatedPriceSpecimen],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    _zero, one, _two = _prices()
    _numeric_request(schema, "rows", _NUMERIC_CASES[case], one, priced(), record_compiled_sql)


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["tokyo-naive-year-one", "aware-without-tz"])
def test_shipped_datetime_bindability_reads_the_actual_timezone_settings(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The same real occurredAt input honors Tokyo's naive projection and USE_TZ=False aware refusal."""
    schema = _shipped_schema()
    root = "allScalarSpecimens"
    zone = "Asia/Tokyo" if case == "tokyo-naive-year-one" else "UTC"
    use_tz = case == "tokyo-naive-year-one"
    with override_settings(TIME_ZONE=zone, USE_TZ=use_tz), timezone.override(zone):
        stamp = datetime.datetime.fromisoformat(
            "2021-06-15T09:30:00+00:00" if use_tz else "2021-06-15T09:30:00",
        )
        one = _specimen("one", stamp=stamp)
        other_stamp = datetime.datetime.fromisoformat(
            "2021-06-16T09:30:00+00:00" if use_tz else "2021-06-16T09:30:00",
        )
        _specimen("other", stamp=other_stamp)
        control = "2021-06-15T18:30:00" if use_tz else "2021-06-15T09:30:00"
        assert _post(
            schema,
            root,
            _where(schema, root, ("occurred_at", "exact"), control),
        ) == _expected(root, [one])
        value = "0001-01-01T00:00:00" if use_tz else "2021-06-15T09:30:00+00:00"
        sqls = record_compiled_sql()
        payload = _post(schema, root, _where(schema, root, ("occurred_at", "exact"), value))
        if connection.vendor == "postgresql":
            assert payload == _expected(root, [] if use_tz else [one])
        else:
            _assert_unbindable(payload, root, "occurred_at")
            _assert_no_specimen_sql(sqls)
