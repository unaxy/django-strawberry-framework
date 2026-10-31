"""Ordinary JSON arguments preserve the public primitive's own container contract.

These consumers call public Filter.filter directly. They do not introduce a form or
normalizer that could mask the primitive's refusal, or a generated FilterInput that
cannot spell the malformed container.
"""

import pytest
import strawberry
from apps.library import models
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django_filters import BaseInFilter, CharFilter
from django_filters.filters import Filter
from graphql_client import JSONObject, RecordCompiledSql, json_at, json_list
from strategy_schemas import make_django_type
from strawberry.scalars import JSON
from test_declared_key_primitives_api import _answer, _schema
from test_raw_filter_forms_api import _post

from django_strawberry_framework import DjangoSchema, finalize_django_types, strawberry_config
from django_strawberry_framework.filters import FilterSet, ListFilter
from django_strawberry_framework.filters.base import (
    GlobalIDMultipleChoiceFilter,
    IntegerInFilter,
    IntegerRangeFilter,
    RelationPkFilter,
    membership_in_filter_class,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")


class _TextInFilter(BaseInFilter, CharFilter):
    """Original upstream class composed through the public membership adapter."""


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["number", "string", "admitted"])
@pytest.mark.parametrize(
    "family",
    [
        "list",
        "membership",
        "integer",
        "unbound-integer",
        "global-id",
    ],
)
def test_direct_public_membership_primitives_refuse_scalar_containers(
    family: str,
    shape: str,
) -> None:
    """A string cannot become char-wise membership and an integer cannot leak iteration errors."""
    branch = models.Branch.objects.create(name="Primitive shapes")
    for code in ("2", "6", "26"):
        models.Shelf.objects.create(branch=branch, code=code)
    for name, fines in (("two", 2), ("six", 6), ("twenty-six", 26)):
        models.Patron.objects.create(
            name=name,
            email=f"{name}@example.test",
            lifetime_fines_cents=fines,
        )
    values: object = 42 if shape == "number" else "26"
    if family in {"integer", "unbound-integer"}:
        source = models.Patron
        leaf = IntegerInFilter(lookup_expr="in")
        field_name, selection = "lifetime_fines_cents", "name"
        expected, universe = ["twenty-six"], ["six", "twenty-six", "two"]
        admitted: list[object] = [26]
        message = "Invalid filter value: expected a list of integers."
    else:
        source = models.Shelf
        field_name, selection = "code", "code"
        expected, universe = ["26"], ["2", "26", "6"]
        admitted = ["26"]
        if family == "list":
            leaf = ListFilter(lookup_expr="in")
        elif family == "membership":
            leaf = membership_in_filter_class(_TextInFilter)(lookup_expr="in")
        else:
            leaf = GlobalIDMultipleChoiceFilter(lookup_expr="in")
            field_name = "pk"
        message = (
            "Invalid GlobalID list: expected a list of GlobalIDs."
            if family == "global-id"
            else "Invalid filter value: expected a list."
        )
    schema = _schema(
        source,
        leaf,
        field_name,
        selection,
        bound=family != "unbound-integer",
        node=family == "global-id",
    )
    if family == "global-id":
        output = registry.get(models.Shelf)
        assert output is not None
        admitted = [
            global_id_for(output, saved_pk(models.Shelf.objects.get(code="26")), schema=schema),
        ]
    if shape == "admitted":
        _answer(schema, admitted, selection, expected, universe)
        return
    query = f"query($values: JSON) {{ matches(values: $values) {{ {selection} }} }}"
    payload = _post(schema, query, {"values": values})
    expected_error: JSONObject = {
        "message": message,
        "locations": [{"line": 1, "column": query.index("matches") + 1}],
        "path": ["matches"],
        "extensions": {"code": "GLOBALID_INVALID" if family == "global-id" else "FILTER_INVALID"},
    }
    assert payload == {"data": None, "errors": [expected_error]}, payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("value", "names"),
    [
        pytest.param(None, ["A", "B", "C"], id="omitted"),
        pytest.param("", ["A", "B", "C"], id="empty-string"),
        pytest.param([1], ["A", "B", "C"], id="short-list"),
        pytest.param([1, 2, 3], ["A", "B", "C"], id="long-list"),
        pytest.param(123, ["A", "B", "C"], id="number"),
        pytest.param("invalid", ["A", "B", "C"], id="string"),
        pytest.param([2, 6], ["A", "B"], id="admitted-two-bounds"),
    ],
)
def test_a_direct_integer_range_primitive_keeps_upstreams_non_pair_skip(
    value: object,
    names: list[str],
) -> None:
    """Malformed direct inputs retain the primitive's no-bound result, while a real pair constrains."""
    for name, fines in (("A", 2), ("B", 6), ("C", 26)):
        models.Patron.objects.create(
            name=name,
            email=f"{name}@example.test",
            lifetime_fines_cents=fines,
        )
    _answer(
        _schema(
            models.Patron,
            IntegerRangeFilter(lookup_expr="range"),
            "lifetime_fines_cents",
            "name",
            bound=False,
        ),
        value,
        "name",
        names,
        ["A", "B", "C"],
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("primitive", "path"),
    [
        pytest.param(IntegerInFilter(lookup_expr="in"), "id", id="integer-membership"),
        pytest.param(RelationPkFilter(), "shelf", id="relation-key"),
    ],
)
def test_a_consumer_rebinding_a_primitive_without_a_field_path_is_refused(
    primitive: Filter,
    path: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A per-request constructor clearing the bound path gets a named configuration refusal."""
    branch = models.Branch.objects.create(name="rebound path")
    shelf = models.Shelf.objects.create(branch=branch, code="selected")
    other = models.Shelf.objects.create(branch=branch, code="other")
    selected = models.Book.objects.create(shelf=shelf, title="Selected")
    models.Book.objects.create(shelf=other, title="Other")
    primitive.field_name = path

    class ReboundBookFilter(FilterSet):
        chosen = primitive

        class Meta:
            model = models.Book
            fields = ()

        def __init__(
            self,
            data: dict[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
            clear_path: bool = False,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)
            if clear_path:
                self.filters["chosen"].field_name = None

    output = make_django_type("ReboundBookOutput", models.Book, ("title",))

    @strawberry.type
    class Query:
        def _matches(self, values: JSON, *, clear_path: bool = False) -> QuerySet[models.Book]:
            rows = models.Book.objects.order_by("title")
            selected_filter = ReboundBookFilter(queryset=rows, clear_path=clear_path)
            return selected_filter.filters["chosen"].filter(rows, values)

        matches: QuerySet[models.Book] = strawberry.field(
            resolver=_matches,
            graphql_type=list[output],
        )

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        config=strawberry_config(),
        error_policy={"enabled": False},
    )
    query = (
        "query($values: JSON!, $clear: Boolean!) { "
        "matches(values: $values, clearPath: $clear) { title } }"
    )
    value: object = [saved_pk(selected)] if path == "id" else saved_pk(shelf)
    accepted = _post(schema, query, {"values": value, "clear": False})
    assert accepted == {"data": {"matches": [{"title": "Selected"}]}}, accepted
    statements = record_compiled_sql(models.Book._meta.db_table)

    payload = _post(schema, query, {"values": value, "clear": True})

    assert payload["data"] is None, payload
    assert len(json_list(payload, "errors")) == 1, payload
    assert json_at(payload, "errors", 0, "path") == ["matches"], payload
    assert json_at(payload, "errors", 0, "message") == (
        f"{type(primitive).__name__} has no field_name; a filter bound to a "
        "FilterSet must name the model field path it filters."
    ), payload
    assert statements == []
