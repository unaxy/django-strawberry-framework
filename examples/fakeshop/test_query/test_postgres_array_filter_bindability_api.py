"""Real PostgreSQL array filter inputs are refused or applied through native HTTP consumers.

The shipped scalar model has scalar columns; array element preparation, subscripts and
list-valued driver parameters require real PostgreSQL ArrayField columns. A function-local
consumer model and table retain those declarations without installing a PostgreSQL-only
model in the backend-neutral example app. Ordinary JSON arguments carry raw numeric search
values; Time and DateTime list arguments retain their scalar's real aware Python values.
"""

import datetime
import decimal
from collections.abc import Iterator
from functools import wraps
from typing import TYPE_CHECKING, NamedTuple

import django_filters
import pytest
import strawberry
from django.db import connection, models
from django.db.models import F, QuerySet
from django.http import HttpRequest, HttpResponseBase, QueryDict
from django.test import override_settings
from django.test.utils import isolate_apps
from django.urls import path
from django_filters import DateTimeFilter, NumberFilter, TimeFilter
from django_filters.filterset import BaseFilterSet
from graphql_client import JSONObject, RecordCompiledSql, graphql_payload, json_list, json_object
from strawberry.scalars import JSON
from strawberry.types import Info
from typing_extensions import override

from django_strawberry_framework import (
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import ArrayFilter, FilterSet, ListFilter
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.views import DjangoGraphQLView

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

pytestmark = [pytest.mark.pg, pytest.mark.usefixtures("private_registry")]
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_UNBINDABLE = [{"message": "Enter a value the database can represent.", "code": "invalid"}]


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-array-search/", _graphql_view)]


class _ArrayConsumer(NamedTuple):
    schema: DjangoSchema
    table: str


@pytest.fixture
def array_consumer() -> Iterator[_ArrayConsumer]:
    # PostgreSQL-only fixture: the module's pg mark skips before importing this optional driver.
    from django.contrib.postgres.fields import ArrayField  # noqa: PLC0415

    with isolate_apps():

        class ArraySpecimen(models.Model):
            label: "models.CharField[str | int | Combinable, str]" = models.CharField(
                max_length=40
            )
            counts: ArrayField[list[int], list[int]] = ArrayField(models.IntegerField())
            small: ArrayField[list[int], list[int]] = ArrayField(models.SmallIntegerField())
            tags: ArrayField[list[str], list[str]] = ArrayField(models.TextField())
            stamps: ArrayField[list[datetime.datetime], list[datetime.datetime]] = ArrayField(
                models.DateTimeField(),
            )
            clocks: ArrayField[list[datetime.time], list[datetime.time]] = ArrayField(
                models.TimeField(),
            )

            prices: ArrayField[list[decimal.Decimal], list[decimal.Decimal]] = ArrayField(
                models.DecimalField(max_digits=20, decimal_places=4),
            )
            grid: ArrayField[list[list[datetime.datetime]], list[list[datetime.datetime]]] = (
                ArrayField(
                    ArrayField(models.DateTimeField()),
                )
            )

            class Meta:
                app_label = "filter_array_http"

            @override
            def __str__(self) -> str:
                return self.label

        class ArraySearch(FilterSet):
            counts_contain = ArrayFilter(field_name="counts", lookup_expr="contains")
            counts_are = ArrayFilter(field_name="counts", lookup_expr="exact")
            counts_overlap = ArrayFilter(field_name="counts", lookup_expr="overlap")
            first_count_among = ListFilter(field_name="counts__0", lookup_expr="in")
            first_two_counts = ArrayFilter(field_name="counts__0_2", lookup_expr="exact")
            counts_after = ArrayFilter(field_name="counts", lookup_expr="gt")
            small_contain = ArrayFilter(field_name="small", lookup_expr="contains")
            small_after = ArrayFilter(field_name="small", lookup_expr="gt")
            small_count = NumberFilter(field_name="small", lookup_expr="len")
            small_count_named = NumberFilter(field_name="small__len")
            small_count_over = NumberFilter(field_name="small", lookup_expr="len__gt")
            small_wide_slice = ArrayFilter(field_name="small__0_40000", lookup_expr="exact")
            joined_contain = ArrayFilter(field_name="joined", lookup_expr="contains")
            prices_after = ArrayFilter(field_name="prices", lookup_expr="gt")
            grid_contain = ArrayFilter(field_name="grid", lookup_expr="contains")
            stamps_contain = ArrayFilter(field_name="stamps", lookup_expr="contains")
            stamps_are = ArrayFilter(field_name="stamps", lookup_expr="exact")
            first_stamp = DateTimeFilter(field_name="stamps__0")
            first_two_stamps = ArrayFilter(field_name="stamps__0_2", lookup_expr="exact")
            stamps_after = ArrayFilter(field_name="stamps", lookup_expr="gt")
            clocks_contain = ArrayFilter(field_name="clocks", lookup_expr="contains")
            first_clock = TimeFilter(field_name="clocks__0")
            clocks_after = ArrayFilter(field_name="clocks", lookup_expr="gt")

            class Meta:
                model = ArraySpecimen
                fields = {"tags": ["len__in"]}

        class RawArraySearch(FilterSet):
            priced = ArrayFilter(field_name="prices", lookup_expr="contains")
            priced_overlap = ArrayFilter(field_name="prices", lookup_expr="overlap")

            class Meta:
                model = ArraySpecimen
                fields = ("label",)

        class PlainRawArraySearch(django_filters.FilterSet):
            priced = ArrayFilter(field_name="prices", lookup_expr="contains")
            priced_overlap = ArrayFilter(field_name="prices", lookup_expr="overlap")

            class Meta:
                model = ArraySpecimen
                fields = ("label",)

        def raw_search(parent: str) -> type[BaseFilterSet]:
            return {"package": RawArraySearch, "django-filter": PlainRawArraySearch}[parent]

        class ArrayOutput(DjangoType):
            class Meta:
                model = ArraySpecimen
                fields = ("label",)

        joined_type: ArrayField[list[int], list[int]] = ArrayField(models.SmallIntegerField())

        def rows() -> QuerySet[ArraySpecimen]:
            return ArraySpecimen.objects.annotate(
                joined=models.Case(
                    models.When(pk__in=[2**70], then=F("small")),
                    default=F("small"),
                    output_field=joined_type,
                ),
            ).order_by("label")

        @strawberry.type
        class Query:
            def _rows(self, info: Info, where: JSON) -> QuerySet[ArraySpecimen]:
                return ArraySearch.apply_sync(where, rows(), info)

            def _stamp_rows(
                self,
                info: Info,
                leaf: str,
                values: list[datetime.datetime],
            ) -> QuerySet[ArraySpecimen]:
                value = values[0] if leaf == "first_stamp" else values
                return ArraySearch.apply_sync({leaf: value}, rows(), info)

            def _clock_rows(
                self,
                info: Info,
                leaf: str,
                values: list[datetime.time],
            ) -> QuerySet[ArraySpecimen]:
                value = values[0] if leaf == "first_clock" else values
                return ArraySearch.apply_sync({leaf: value}, rows(), info)

            def _raw_array_rows(
                self,
                parent: str,
                query: str,
                where: JSON | None = None,
            ) -> QuerySet[ArraySpecimen]:
                data = QueryDict(query) if where is None else json_object(where)
                return raw_search(parent)(data=data, queryset=rows()).qs

            def _all_rows(self) -> QuerySet[ArraySpecimen]:
                return rows()

            rows: QuerySet[ArraySpecimen] = strawberry.field(
                resolver=_rows,
                graphql_type=list[ArrayOutput],
            )
            stamp_rows: QuerySet[ArraySpecimen] = strawberry.field(
                resolver=_stamp_rows,
                graphql_type=list[ArrayOutput],
            )
            clock_rows: QuerySet[ArraySpecimen] = strawberry.field(
                resolver=_clock_rows,
                graphql_type=list[ArrayOutput],
            )
            raw_array_rows: QuerySet[ArraySpecimen] = strawberry.field(
                resolver=_raw_array_rows,
                graphql_type=list[ArrayOutput],
            )
            all_rows: QuerySet[ArraySpecimen] = strawberry.field(
                resolver=_all_rows,
                graphql_type=list[ArrayOutput],
            )

        with connection.schema_editor() as editor:
            editor.create_model(ArraySpecimen)
        try:
            ArraySpecimen.objects.create(
                label="Match",
                counts=[1, 2],
                small=[1],
                tags=["a", "b"],
                stamps=[datetime.datetime(2021, 1, 1, tzinfo=datetime.timezone.utc)],
                clocks=[datetime.time(12)],
                prices=[decimal.Decimal(1)],
                grid=[[datetime.datetime(2021, 1, 1, tzinfo=datetime.timezone.utc)]],
            )
            ArraySpecimen.objects.create(
                label="Other",
                counts=[5],
                small=[5],
                tags=["c"],
                stamps=[datetime.datetime(2022, 1, 1, tzinfo=datetime.timezone.utc)],
                clocks=[datetime.time(15)],
                prices=[decimal.Decimal(5)],
                grid=[[datetime.datetime(2022, 1, 1, tzinfo=datetime.timezone.utc)]],
            )
            finalize_django_types()
            yield _ArrayConsumer(
                DjangoSchema(query=Query, config=strawberry_config()),
                ArraySpecimen._meta.db_table,
            )
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(ArraySpecimen)


def _post(consumer: _ArrayConsumer, document: str, variables: JSONObject) -> JSONObject:
    _CURRENT["schema"] = consumer.schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(document, variables=variables, url="/graphql-array-search/")
    finally:
        _CURRENT["schema"] = None


def _assert_answer(payload: JSONObject, names: list[str] | None, form_key: str) -> None:
    if names is None:
        assert payload["data"] is None, payload
        errors = json_list(payload, "errors")
        assert len(errors) == 1, payload
        error = json_object(errors[0])
        assert error["message"] == "Invalid filter input", payload
        assert error["path"] == ["rows"], payload
        assert error["extensions"] == {
            "code": "FILTER_INVALID",
            "errors": {form_key: _UNBINDABLE},
        }, payload
    else:
        assert payload == {
            "data": {
                "rows": [{"label": name} for name in names],
                "allRows": [{"label": name} for name in ("Match", "Other")],
            },
        }, payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("form_key", "value", "names"),
    [
        pytest.param("prices_after", ["-1e-16384"], None, id="decimal-list-parameter-past-format"),
        pytest.param(
            "prices_after",
            ["-1e-16383"],
            ["Match", "Other"],
            id="decimal-list-parameter-format-edge",
        ),
        pytest.param("prices_after", ["NaN"], None, id="decimal-element-form-refusal"),
        pytest.param("counts_contain", ["1", str(2**63)], None, id="contains-past-int64"),
        pytest.param("counts_are", ["1", str(2**63)], None, id="exact-past-int64"),
        pytest.param("counts_overlap", [str(-(2**63) - 1)], None, id="overlap-before-int64"),
        pytest.param("first_count_among", ["1", str(2**63)], None, id="index-past-int64"),
        pytest.param("first_two_counts", ["1", str(2**63)], None, id="slice-past-int64"),
        pytest.param("counts_after", [str(2**63)], None, id="list-parameter-past-int64"),
        pytest.param("counts_contain", ["1", str(2**31)], None, id="contains-past-int32"),
        pytest.param("counts_after", [str(-(2**31) - 1)], None, id="list-parameter-before-int32"),
        pytest.param("small_contain", ["1", str(2**15)], None, id="contains-past-int16"),
        pytest.param("small_after", [str(-(2**15) - 1)], None, id="list-parameter-before-int16"),
        pytest.param("tags__len__in", [str(2**70)], None, id="text-array-length-past-int64"),
        pytest.param("counts_contain", ["1"], ["Match"], id="contains-member"),
        pytest.param("counts_are", ["1", "2"], ["Match"], id="exact-array"),
        pytest.param("counts_overlap", ["2"], ["Match"], id="overlap-member"),
        pytest.param("first_count_among", ["1"], ["Match"], id="index-member"),
        pytest.param("first_two_counts", ["1", "2"], ["Match"], id="slice-members"),
        pytest.param("counts_after", ["2"], ["Other"], id="list-parameter-order"),
        pytest.param("counts_contain", ["1", str(2**31 - 1)], [], id="contains-max-int32"),
        pytest.param(
            "counts_after",
            [str(-(2**31))],
            ["Match", "Other"],
            id="list-parameter-min-int32",
        ),
        pytest.param("small_contain", [str(2**15 - 1)], [], id="contains-max-int16"),
        pytest.param("small_count", 2**15, [], id="length-not-small-element"),
        pytest.param("small_count_named", 2**15, [], id="named-length-not-small-element"),
        pytest.param("small_count_over", 2**15, [], id="length-comparison-not-small-element"),
        pytest.param("small_wide_slice", ["1"], ["Match"], id="slice-bound-not-small-element"),
        pytest.param(
            "joined_contain",
            ["1"],
            ["Match"],
            id="annotation-constant-not-small-element",
        ),
        pytest.param("tags__len__in", ["2"], ["Match"], id="text-array-length"),
    ],
)
def test_numeric_array_members_check_the_real_binding_type_and_keep_non_element_parameters(
    array_consumer: _ArrayConsumer,
    form_key: str,
    value: object,
    names: list[str] | None,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Real array members obey the backend's integer range; len, slice bounds and annotations keep theirs."""
    statements = record_compiled_sql(array_consumer.table)
    payload = _post(
        array_consumer,
        "query($where: JSON!) { rows(where: $where) { label } allRows { label } }",
        {"where": {form_key: value}},
    )
    if form_key == "prices_after" and value == ["NaN"]:
        assert payload["data"] is None, payload
        errors = json_list(payload, "errors")
        assert len(errors) == 1, payload
        assert json_object(errors[0], "extensions") == {
            "code": "FILTER_INVALID",
            "errors": {"prices_after": [{"message": "Enter a number.", "code": "invalid"}]},
        }, payload
    else:
        _assert_answer(payload, names, form_key)
    if names is None:
        assert statements == [], statements


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "surface",
        "leaf",
        "values",
        "names",
    ),
    [
        pytest.param(
            "stampRows",
            "grid_contain",
            ["2021-01-01T00:00:00+16:00"],
            None,
            id="nested-datetime-offset",
        ),
        pytest.param(
            "stampRows",
            "grid_contain",
            ["2021-01-01T00:00:00Z"],
            ["Match"],
            id="nested-datetime-contains",
        ),
        pytest.param(
            "clockRows",
            "clocks_after",
            ["12:00:00+00:00", "12:00:00"],
            ["Other"],
            id="time-list-dumper-aware-naive",
        ),
        pytest.param(
            "clockRows",
            "clocks_contain",
            ["12:00:00+00:00:01.500000"],
            None,
            id="time-contains-fractional-offset",
        ),
        pytest.param(
            "clockRows",
            "first_clock",
            ["12:00:00+00:00:01.500000"],
            None,
            id="time-index-fractional-offset",
        ),
        pytest.param(
            "clockRows",
            "clocks_after",
            ["12:00:00+00:00:01.500000"],
            None,
            id="time-list-parameter-fractional-offset",
        ),
        pytest.param(
            "stampRows",
            "stamps_contain",
            ["2021-01-01T00:00:00+16:00"],
            None,
            id="datetime-contains-offset",
        ),
        pytest.param(
            "stampRows",
            "stamps_are",
            ["2021-01-01T00:00:00+16:00"],
            None,
            id="datetime-exact-offset",
        ),
        pytest.param(
            "stampRows",
            "first_stamp",
            ["2021-01-01T00:00:00+16:00"],
            None,
            id="datetime-index-offset",
        ),
        pytest.param(
            "stampRows",
            "first_two_stamps",
            ["2021-01-01T00:00:00+16:00"],
            None,
            id="datetime-slice-offset",
        ),
        pytest.param(
            "stampRows",
            "stamps_after",
            ["2021-01-01T00:00:00+16:00"],
            None,
            id="datetime-list-parameter-offset",
        ),
        pytest.param(
            "clockRows",
            "clocks_contain",
            ["12:00:00+16:00"],
            None,
            id="time-contains-offset",
        ),
        pytest.param("clockRows", "first_clock", ["12:00:00+16:00"], None, id="time-index-offset"),
        pytest.param(
            "clockRows",
            "clocks_after",
            ["12:00:00+16:00"],
            None,
            id="time-list-parameter-offset",
        ),
        pytest.param(
            "clockRows",
            "clocks_after",
            ["12:00:00", "12:00:00+01:00"],
            None,
            id="time-list-dumper-naive-aware",
        ),
        pytest.param(
            "stampRows",
            "stamps_contain",
            ["2021-01-01T00:00:00Z"],
            ["Match"],
            id="datetime-contains",
        ),
        pytest.param(
            "stampRows",
            "stamps_are",
            ["2021-01-01T00:00:00Z"],
            ["Match"],
            id="datetime-exact",
        ),
        pytest.param(
            "stampRows",
            "first_stamp",
            ["2021-01-01T00:00:00Z"],
            ["Match"],
            id="datetime-index",
        ),
        pytest.param(
            "stampRows",
            "first_two_stamps",
            ["2021-01-01T00:00:00Z"],
            ["Match"],
            id="datetime-slice",
        ),
        pytest.param(
            "stampRows",
            "stamps_after",
            ["2021-01-01T00:00:00Z"],
            ["Other"],
            id="datetime-list-parameter",
        ),
        pytest.param("clockRows", "clocks_contain", ["12:00:00"], ["Match"], id="time-contains"),
        pytest.param("clockRows", "first_clock", ["12:00:00"], ["Match"], id="time-index"),
        pytest.param(
            "clockRows",
            "clocks_after",
            ["12:00:00"],
            ["Other"],
            id="time-list-parameter",
        ),
    ],
)
def test_temporal_arrays_check_each_scalar_and_the_real_psycopg_list_parameter(
    array_consumer: _ArrayConsumer,
    surface: str,
    leaf: str,
    values: list[str],
    names: list[str] | None,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Time and DateTime scalar arrays reach the real driver preparation, before any row fetch."""
    scalar = "Time" if surface == "clockRows" else "DateTime"
    document = (
        f"query($leaf: String!, $values: [{scalar}!]!) {{ "
        f"rows: {surface}(leaf: $leaf, values: $values) {{ label }} allRows {{ label }} }}"
    )
    statements = record_compiled_sql(array_consumer.table)
    payload = _post(array_consumer, document, {"leaf": leaf, "values": values})
    _assert_answer(payload, names, leaf)
    if names is None:
        assert statements == [], statements


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "surface",
        "leaf",
        "scalar",
        "values",
        "names",
    ),
    [
        pytest.param(
            "stampRows",
            "stamps_contain",
            "DateTime",
            ["2021-01-01T00:00:00+16:00"],
            [],
            id="datetime-offset-is-an-instant",
        ),
        pytest.param(
            "stampRows",
            "stamps_are",
            "DateTime",
            ["2021-01-01T00:00:00+16:00"],
            [],
            id="datetime-exact-offset",
        ),
        pytest.param(
            "stampRows",
            "first_stamp",
            "DateTime",
            ["2021-01-01T00:00:00+16:00"],
            [],
            id="datetime-index-offset",
        ),
        pytest.param(
            "stampRows",
            "first_two_stamps",
            "DateTime",
            ["2021-01-01T00:00:00+16:00"],
            [],
            id="datetime-slice-offset",
        ),
        pytest.param(
            "stampRows",
            "grid_contain",
            "DateTime",
            ["2021-01-01T00:00:00+16:00"],
            [],
            id="nested-datetime-offset",
        ),
        pytest.param(
            "stampRows",
            "stamps_after",
            "DateTime",
            ["2021-01-01T00:00:00+16:00"],
            None,
            id="datetime-list-parameter-stays-text",
        ),
        pytest.param(
            "clockRows",
            "clocks_contain",
            "Time",
            ["12:00:00+00:00:01.500000"],
            ["Match"],
            id="time-offset-travels-as-whole-seconds",
        ),
        pytest.param(
            "clockRows",
            "first_clock",
            "Time",
            ["12:00:00+00:00:01.500000"],
            [],
            id="time-index-offset",
        ),
        pytest.param(
            "clockRows",
            "clocks_after",
            "Time",
            ["12:00:00+00:00:01.500000"],
            None,
            id="time-list-parameter-stays-text",
        ),
        pytest.param(
            "clockRows",
            "clocks_after",
            "Time",
            ["12:00:00", "12:00:00+01:00"],
            None,
            id="mixed-list-dumper-naive-aware",
        ),
        pytest.param(
            "clockRows",
            "clocks_after",
            "Time",
            ["12:00:00+00:00", "12:00:00"],
            ["Other"],
            id="mixed-list-dumper-aware-naive",
        ),
        pytest.param(
            "clockRows",
            "clocks_after",
            "Time",
            ["12:00:00"],
            ["Other"],
            id="list-dumper-naive",
        ),
    ],
)
def test_server_bound_array_parameters_follow_the_actual_driver_protocol(
    array_consumer: _ArrayConsumer,
    surface: str,
    leaf: str,
    scalar: str,
    values: list[str],
    names: list[str] | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scalar binary parameters are distinct from text-bound list elements under actual server cursors."""
    options = json_object(read_attr(connection, "settings_dict"), "OPTIONS")
    # Django selects cursor_factory when it opens the connection. Reconnect under the actual
    # option instead of changing only the validator's view of an already-open client cursor.
    connection.close()
    with monkeypatch.context() as configured:
        configured.setitem(options, "server_side_binding", value=True)
        try:
            document = (
                f"query($leaf: String!, $values: [{scalar}!]!) {{ "
                f"rows: {surface}(leaf: $leaf, values: $values) {{ label }} allRows {{ label }} }}"
            )
            payload = _post(array_consumer, document, {"leaf": leaf, "values": values})
            _assert_answer(payload, names, leaf)
        finally:
            # Restore the default connection policy before the model fixture drops its table.
            connection.close()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("parent", ["package", "django-filter"])
@pytest.mark.parametrize(
    ("query", "where", "names"),
    [
        pytest.param("priced=1,1", None, ["Match"], id="raw-members"),
        pytest.param("priced=5", None, ["Other"], id="raw-other-member"),
        pytest.param("priced=1,5", None, [], id="raw-both-members-required"),
        pytest.param("priced=", None, ["Match", "Other"], id="raw-empty-is-omission"),
        pytest.param("", None, ["Match", "Other"], id="absent-is-omission"),
        pytest.param("", {"priced": []}, ["Match", "Other"], id="explicit-empty-contains"),
        pytest.param("priced_overlap=", None, ["Match", "Other"], id="raw-empty-overlap-omitted"),
        pytest.param("", {"priced_overlap": []}, [], id="explicit-empty-overlap-restricts"),
        pytest.param("priced=1,NaN", None, ["Match", "Other"], id="invalid-form-does-not-apply"),
    ],
)
def test_raw_array_forms_keep_upstream_csv_and_explicit_empty_membership(
    array_consumer: _ArrayConsumer,
    parent: str,
    query: str,
    where: JSONObject | None,
    names: list[str],
) -> None:
    """Raw CSV filters real numeric arrays; omission and invalid forms preserve upstream rows."""
    payload = _post(
        array_consumer,
        "query($parent: String!, $query: String!, $where: JSON) { "
        "rows: rawArrayRows(parent: $parent, query: $query, where: $where) { label } "
        "allRows { label } }",
        {"parent": parent, "query": query, "where": where},
    )
    _assert_answer(payload, names, "priced")
