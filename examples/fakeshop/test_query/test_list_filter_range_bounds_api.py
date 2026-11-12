"""A ``ListFilter`` declared with ``range`` applies exactly two bounds; any other count is refused.

Django's ``Range`` reads a list's first two members, so a one-member list would raise an
``IndexError`` and a three-member one a ``TypeError`` past the form. The filter's form field
refuses both before any query runs, with django-filter's ``BaseRangeField`` message and code
(``Range query expects two values.``, ``invalid_values``), as ``FILTER_INVALID`` keyed by the
filter under the sync and the async view alike (``filters/base.py::_ElementField.validate``).
Each row declares ``span = ListFilter(field_name=<column>, lookup_expr="range")`` on a
module-local set over an integer, a date or a text column: two bounds answer the rows between
them flat and their complement under ``not``, an empty list matches no row (every row under
``not``), and raw form data (``?span=20,40``) answers the same rows, refuses one or three
bounds with the same message and code, and reads an empty ``?span=`` as no constraint. The
flat copy of a child set's ``range`` list over a value only the child type's ``get_queryset``
annotates (``parentTwiceSpan``) keeps the rule: its cleaner, built from that queryset
(``filters/sets.py::FilterSet._install_source_comparison``), refuses one or three bounds too.
"""

import datetime
import uuid
from decimal import Decimal
from functools import wraps
from typing import NamedTuple

import pytest
import strawberry
from apps.scalars import models as scalars
from asgiref.sync import sync_to_async
from django.db import connection
from django.db.models import F, QuerySet
from django.forms.utils import ErrorDict
from django.http import HttpRequest, HttpResponseBase, QueryDict
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_list, json_str, response_json
from strawberry import relay
from strawberry.scalars import JSON
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, ListFilter, RelatedFilter
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils._narrowing import require_instance
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


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
    path("graphql-list-range-bounds/", _graphql_view),
    path("graphql-list-range-bounds-async/", _async_graphql_view),
]

#: Five rows, ``a`` .. ``e``, each column ordered as the labels are; two bounds keep ``b`` .. ``d``.
_LABELS = [
    "a",
    "b",
    "c",
    "d",
    "e",
]
_BETWEEN = ["b", "c", "d"]
_OUTSIDE = ["a", "e"]
#: django-filter's ``BaseRangeField`` refusal of a count other than two.
_TWO_VALUES = [{"message": "Range query expects two values.", "code": "invalid_values"}]


class _Column(NamedTuple):
    """One column the ``range`` list compares, its two bounds and a third, sent and raw."""

    field_name: str
    bounds: tuple[object, object, object]
    raw: tuple[str, str, str]


_COLUMNS: dict[str, _Column] = {
    "integer": _Column("signed_big", (20, 40, 50), ("20", "40", "50")),
    "date": _Column(
        "occurred_on",
        ("2022-01-02", "2024-01-04", "2025-01-05"),
        ("2022-01-02", "2024-01-04", "2025-01-05"),
    ),
    "text": _Column("label", ("b", "d", "e"), ("b", "d", "e")),
}


def _seed_specimens() -> None:
    """Row ``i`` holds ``10 * i`` and day ``i`` of year ``2020 + i``, labelled ``a`` .. ``e``."""
    for i, label in enumerate(_LABELS, start=1):
        scalars.ScalarSpecimen.objects.create(
            label=label,
            price=Decimal(i),
            signed_big=10 * i,
            occurred_on=datetime.date(2020 + i, 1, i),
            occurred_at=datetime.datetime(2020 + i, 1, i, 9, 30, tzinfo=datetime.timezone.utc),
            occurred_time=datetime.time(9, 30),
            external_id=uuid.uuid4(),
        )


def _schema(column: _Column) -> DjangoSchema:
    meta = type("Meta", (), {"model": scalars.ScalarSpecimen, "fields": ()})
    span = ListFilter(field_name=column.field_name, lookup_expr="range")
    served = type("SpanFilter", (FilterSet,), {"span": span, "Meta": meta})

    class SpecimenNode(DjangoType):
        class Meta:
            model = scalars.ScalarSpecimen
            fields = ("id", "label")
            interfaces = (relay.Node,)
            filterset_class = served

    @strawberry.type
    class Query:
        rows: DjangoConnection[SpecimenNode] = DjangoConnectionField(SpecimenNode)

        def _raw_rows(self, query: str) -> dict[str, object]:
            """The set's raw form data over every specimen: its rows, else its form errors."""
            del self
            filterset = served(
                data=QueryDict(query),
                queryset=scalars.ScalarSpecimen.objects.all(),
            )
            if not filterset.is_valid():
                return {"errors": require_instance(filterset.errors, ErrorDict).get_json_data()}
            rows = scalars.ScalarSpecimen.objects.filter(pk__in=filterset.qs.values("pk"))
            return {"rows": sorted(row.label for row in rows)}

        raw_rows: dict[str, object] = strawberry.field(resolver=_raw_rows, graphql_type=JSON)

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


_ROWS = "query($where: SpanFilterInputType) { rows(filter: $where) { edges { node { label } } } }"


def _post(schema: DjangoSchema, query: str, variables: JSONObject) -> tuple[JSONObject, int]:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__), CaptureQueriesContext(connection) as sql:
            payload = graphql_payload(
                query,
                variables=variables,
                url="/graphql-list-range-bounds/",
            )
    finally:
        _CURRENT["schema"] = None
    return payload, len(sql)


def _labels(payload: JSONObject) -> list[str]:
    edges = json_list(payload, "data", "rows", "edges")
    return sorted(json_str(edge, "node", "label") for edge in edges)


def _refused(payload: JSONObject) -> None:
    assert payload == {
        "data": None,
        "errors": [
            {
                "message": "Invalid filter input",
                "locations": [{"line": 1, "column": 38}],
                "path": ["rows"],
                "extensions": {"code": "FILTER_INVALID", "errors": {"span": _TWO_VALUES}},
            },
        ],
    }, payload


@pytest.mark.django_db
@pytest.mark.parametrize("column", sorted(_COLUMNS))
@pytest.mark.parametrize("negated", [False, True], ids=["flat", "not"])
def test_two_bounds_answer_the_rows_between_them(column: str, *, negated: bool) -> None:
    """Two bounds keep ``b`` .. ``d`` in one statement; ``not`` keeps the rest."""
    _seed_specimens()
    low, high, _third = _COLUMNS[column].bounds
    span: JSONObject = {"span": {"range": [low, high]}}

    payload, statements = _post(
        _schema(_COLUMNS[column]),
        _ROWS,
        {"where": {"not": span} if negated else span},
    )

    assert "errors" not in payload, payload
    assert _labels(payload) == (_OUTSIDE if negated else _BETWEEN)
    assert statements == 1


@pytest.mark.django_db
@pytest.mark.parametrize("column", sorted(_COLUMNS))
@pytest.mark.parametrize("count", [1, 3], ids=["one-bound", "three-bounds"])
def test_a_count_other_than_two_is_refused_before_any_query(column: str, count: int) -> None:
    """One or three bounds are ``FILTER_INVALID`` with ``invalid_values``; no statement runs."""
    _seed_specimens()
    values = list(_COLUMNS[column].bounds[:count])

    payload, statements = _post(
        _schema(_COLUMNS[column]),
        _ROWS,
        {"where": {"span": {"range": values}}},
    )

    _refused(payload)
    assert statements == 0


@pytest.mark.django_db
@pytest.mark.parametrize("column", sorted(_COLUMNS))
@pytest.mark.parametrize(
    ("negated", "expected"),
    [(False, []), (True, _LABELS)],
    ids=["flat", "not"],
)
def test_an_empty_list_matches_no_row(column: str, *, negated: bool, expected: list[str]) -> None:
    """``[]`` keeps the filter's empty-list meaning: no row, every row under ``not``."""
    _seed_specimens()
    span: JSONObject = {"span": {"range": []}}

    payload, statements = _post(
        _schema(_COLUMNS[column]),
        _ROWS,
        {"where": {"not": span} if negated else span},
    )

    assert "errors" not in payload, payload
    assert _labels(payload) == expected
    assert statements == (1 if negated else 0)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("column", sorted(_COLUMNS))
@pytest.mark.parametrize("count", [1, 2, 3])
async def test_the_async_view_answers_two_bounds_and_refuses_any_other_count(
    column: str,
    count: int,
) -> None:
    """Under the async view (``apply_async``) the same two bounds answer and other counts refuse."""
    await sync_to_async(_seed_specimens)()
    schema = _schema(_COLUMNS[column])
    values = list(_COLUMNS[column].bounds[:count])
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            result = await AsyncTestClient().query(
                _ROWS,
                variables={"where": {"span": {"range": values}}},
                assert_no_errors=False,
                url="/graphql-list-range-bounds-async/",
            )
    finally:
        _CURRENT["schema"] = None
    payload = response_json(result.response)

    if count == 2:
        assert _labels(payload) == _BETWEEN, payload
    else:
        _refused(payload)


def _raw(schema: DjangoSchema, query: str) -> tuple[JSONObject, int]:
    return _post(schema, "query($query: String!) { rawRows(query: $query) }", {"query": query})


@pytest.mark.django_db
@pytest.mark.parametrize("column", sorted(_COLUMNS))
@pytest.mark.parametrize(
    ("count", "expected", "statements"),
    [
        pytest.param(0, {"rows": _LABELS}, 1, id="empty-no-constraint"),
        pytest.param(1, {"errors": {"span": _TWO_VALUES}}, 0, id="one-bound"),
        pytest.param(2, {"rows": _BETWEEN}, 1, id="two-bounds"),
        pytest.param(3, {"errors": {"span": _TWO_VALUES}}, 0, id="three-bounds"),
    ],
)
def test_raw_form_data_reads_comma_separated_bounds(
    column: str,
    count: int,
    expected: JSONObject,
    statements: int,
) -> None:
    """``?span=low,high`` answers the rows between; one or three bounds are the form's error."""
    _seed_specimens()
    query = f"span={','.join(_COLUMNS[column].raw[:count])}"

    payload, ran = _raw(_schema(_COLUMNS[column]), query)

    assert payload == {"data": {"rawRows": expected}}, payload
    assert ran == statements


def _seed_parented() -> None:
    """Parents ``p-a`` .. ``p-e`` holding ``10 * i``, each with the child labelled ``a`` .. ``e``."""
    for i, label in enumerate(_LABELS, start=1):
        parent = scalars.ScalarSpecimen.objects.create(
            label=f"p-{label}",
            signed_big=10 * i,
            occurred_on=datetime.date(2021, 1, 1),
            occurred_at=datetime.datetime(2021, 1, 1, tzinfo=datetime.timezone.utc),
            occurred_time=datetime.time(9, 30),
            external_id=uuid.uuid4(),
        )
        scalars.ScalarSpecimen.objects.create(
            label=label,
            parent=parent,
            occurred_on=datetime.date(2021, 1, 1),
            occurred_at=datetime.datetime(2021, 1, 1, tzinfo=datetime.timezone.utc),
            occurred_time=datetime.time(9, 30),
            external_id=uuid.uuid4(),
        )


def _annotated_child_schema() -> DjangoSchema:
    """A root set reaching a child set whose ``range`` list compares an annotation only.

    ``twice`` exists only on the rows the child type's ``get_queryset`` hands over, so the
    flat copy ``parentTwiceSpan`` reads its comparison from that queryset.
    """
    child_meta = type("Meta", (), {"model": scalars.ScalarSpecimen, "fields": ()})
    child = type(
        "TwiceSpanFilter",
        (FilterSet,),
        {"twice_span": ListFilter(field_name="twice", lookup_expr="range"), "Meta": child_meta},
    )
    root_meta = type("Meta", (), {"model": scalars.ScalarSpecimen, "fields": ()})
    root = type(
        "ParentSpanFilter",
        (FilterSet,),
        {"parent": RelatedFilter(child, field_name="parent"), "Meta": root_meta},
    )

    class TwiceNode(DjangoType):
        class Meta:
            model = scalars.ScalarSpecimen
            fields = ("id", "label")
            interfaces = (relay.Node,)
            filterset_class = child
            primary = True

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[scalars.ScalarSpecimen],
            info: object,
            **kwargs: object,
        ) -> QuerySet[scalars.ScalarSpecimen]:
            del info, kwargs
            return queryset.annotate(twice=F("signed_big") * 2)

    class RootNode(DjangoType):
        class Meta:
            model = scalars.ScalarSpecimen
            fields = ("id", "label", "parent")
            interfaces = (relay.Node,)
            filterset_class = root
            name = "SpanRootNode"

    @strawberry.type
    class Query:
        rows: DjangoConnection[RootNode] = DjangoConnectionField(RootNode)
        children: DjangoConnection[TwiceNode] = DjangoConnectionField(TwiceNode)

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


_FLAT_ROWS = (
    "query($where: ParentSpanFilterInputType) "
    "{ rows(filter: $where) { edges { node { label } } } }"
)


@pytest.mark.django_db
@pytest.mark.parametrize("count", [1, 2, 3])
def test_a_flat_copy_over_a_child_annotation_takes_exactly_two_bounds(count: int) -> None:
    """The flat copy of a child's ``range`` list over its type's annotation keeps the rule.

    Two bounds answer the children whose parent's ``twice`` lies between them; one or three
    are ``FILTER_INVALID`` with ``invalid_values`` before any query.
    """
    _seed_parented()
    values = ["40", "80", "100"][:count]

    payload, statements = _post(
        _annotated_child_schema(),
        _FLAT_ROWS,
        {"where": {"parentTwiceSpan": {"range": values}}},
    )

    if count == 2:
        assert "errors" not in payload, payload
        assert _labels(payload) == _BETWEEN
        assert statements == 1
    else:
        assert payload == {
            "data": None,
            "errors": [
                {
                    "message": "Invalid filter input",
                    "locations": [{"line": 1, "column": 44}],
                    "path": ["rows"],
                    "extensions": {
                        "code": "FILTER_INVALID",
                        "errors": {"parent__twice_span": _TWO_VALUES},
                    },
                },
            ],
        }, payload
        assert statements == 0
