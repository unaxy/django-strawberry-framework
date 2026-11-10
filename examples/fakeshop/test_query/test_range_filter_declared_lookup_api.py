"""A declared ``RangeFilter`` compares two bounds as a range whatever lookup it declares.

django-filter's ``RangeFilter.filter`` replaces a declaration's ``lookup_expr`` with ``range``
for two bounds and ``gte`` / ``lte`` for one, so ``RangeFilter(field_name="price")`` (the
default ``exact``) is a range filter. The package's ``RangeFilter`` answers the same way: its
declared lookup names the published input key (``span: { exact: { start, end } }``) and the
transforms the bounds compare through, never the lookup applied
(``filters/base.py::RangeFilter.filter``). Each row declares one ``RangeFilter`` on a
module-local set over a decimal, text, date, datetime or integer column, a relation-valued
primary key or a path through a relation's key, under the default lookup or a declared
``exact``, ``gte``, ``lte``, ``lt``, ``in``, ``iexact``, ``icontains``, ``isnull`` or
``range``, or through a ``date`` / ``year`` transform (bare, ``exact``, ``range``, ``in``,
``gte``), and sends two bounds: the rows between them answer flat, their complement under
``not``, and the same rows answer the set's raw form data. A transform stays on the
compared path, so an end date keeps a row stamped later that day.

Raw form data reaches what no published input can: a range over a relation itself (forward
``parent`` and reverse ``children``), whose bounds compare the column the relation's values
are compared on (two bounds as its ``gte`` + ``lte``, since Django registers no ``range`` on
a relation), so a bound past that column widens or matches nothing exactly as over
``parent__id`` / ``children__id``; and a bound past an integer column's range under a
declared ``iexact`` / ``contains`` / ``icontains`` / ``exact``, held to the column's end as
under ``range`` (``filters/base.py::_integer_compared_column`` reads the lookups the range
applies), so the request answers at once instead of running ``int()`` of the decimal.
"""

import datetime
import time
import uuid
from decimal import Decimal
from functools import wraps
from typing import NamedTuple

import pytest
import strawberry
from apps.library import models as library
from apps.scalars import models as scalars
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase, QueryDict
from django.test import override_settings
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_list, json_str
from strawberry import relay

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RangeFilter
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-range-declared-lookup/", _graphql_view)]

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


class _Cell(NamedTuple):
    """One declaration and the two bounds sent to it, as a variable and as raw form text."""

    field_name: str
    lookup_expr: str | None
    bounds: tuple[object, object]
    raw: tuple[str, str]


def _seed_specimens() -> None:
    """Row ``i`` holds ``i`` in every column: price, ``10 * i``, day ``i`` of year ``2020 + i``."""
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


def _seed_parented_specimens() -> list[int]:
    """Parents ``p-a`` .. ``p-e``, each with the child labelled ``a`` .. ``e``; their keys."""
    keys: list[int] = []
    for label in _LABELS:
        parent = scalars.ScalarSpecimen.objects.create(
            label=f"p-{label}",
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
        assert parent.pk is not None
        keys.append(parent.pk)
    return keys


def _seed_profiles() -> list[int]:
    """Patrons whose profiles carry the postal codes ``a`` .. ``e``; the profiles' keys."""
    keys: list[int] = []
    for label in _LABELS:
        patron = library.Patron.objects.create(name=f"patron-{label}")
        library.PatronProfile.objects.create(patron=patron, postal_code=label)
        assert patron.pk is not None
        keys.append(patron.pk)
    return keys


def _set_class(model: type[Model], cell: _Cell) -> type[FilterSet]:
    meta = type("Meta", (), {"model": model, "fields": ()})
    span = (
        RangeFilter(field_name=cell.field_name)
        if cell.lookup_expr is None
        else RangeFilter(field_name=cell.field_name, lookup_expr=cell.lookup_expr)
    )
    return type("SpanFilter", (FilterSet,), {"span": span, "Meta": meta})


def _label(row: Model) -> str:
    """A specimen's label, a profile's postal code: the label each schema selects."""
    if isinstance(row, library.PatronProfile):
        return row.postal_code
    return str(row)


def _raw_labels(
    filterset_class: type[FilterSet],
    queryset: QuerySet[Model],
    query: str,
) -> list[str]:
    """Run ``query`` as raw form data on a first instance of ``filterset_class``; its rows."""
    filterset = filterset_class(data=QueryDict(query), queryset=queryset)
    assert filterset.is_valid(), filterset.errors
    matched: QuerySet[Model] = filterset.qs
    return sorted(_label(row) for row in matched)


def _raw_only_schema(cell: _Cell) -> DjangoSchema:
    """A schema serving no type: its one root runs the set's raw form data over specimens."""
    filterset_class = _set_class(scalars.ScalarSpecimen, cell)

    @strawberry.type
    class Query:
        @strawberry.field
        def raw_rows(self, query: str) -> list[str]:
            del self
            return _raw_labels(filterset_class, scalars.ScalarSpecimen.objects.all(), query)

    return DjangoSchema(query=Query, config=strawberry_config())


def _specimen_schema(cell: _Cell) -> DjangoSchema:
    served = _set_class(scalars.ScalarSpecimen, cell)

    class SpecimenNode(DjangoType):
        class Meta:
            model = scalars.ScalarSpecimen
            fields = ("id", "label")
            interfaces = (relay.Node,)
            filterset_class = served

    @strawberry.type
    class Query:
        rows: DjangoConnection[SpecimenNode] = DjangoConnectionField(SpecimenNode)

        @strawberry.field
        def raw_rows(self, query: str) -> list[str]:
            del self
            return _raw_labels(served, scalars.ScalarSpecimen.objects.all(), query)

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


def _profile_schema(cell: _Cell) -> DjangoSchema:
    served = _set_class(library.PatronProfile, cell)

    class ProfileNode(DjangoType):
        class Meta:
            model = library.PatronProfile
            fields = ("postal_code",)
            interfaces = (relay.Node,)
            filterset_class = served

    @strawberry.type
    class Query:
        rows: DjangoConnection[ProfileNode] = DjangoConnectionField(ProfileNode)

        @strawberry.field
        def raw_rows(self, query: str) -> list[str]:
            del self
            return _raw_labels(served, library.PatronProfile.objects.all(), query)

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


def _post(schema: DjangoSchema, query: str, variables: JSONObject) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                query,
                variables=variables,
                url="/graphql-range-declared-lookup/",
            )
    finally:
        _CURRENT["schema"] = None


def _span_key(schema: DjangoSchema) -> str:
    """The one key the ``span`` input publishes: the declared lookup's input name."""
    result = schema.execute_sync(
        '{ __type(name: "SpanFilterSpanFilterInputType") { inputFields { name } } }',
    )
    assert result.errors is None, result.errors
    (field,) = json_list({"data": result.data}, "data", "__type", "inputFields")
    return json_str(field, "name")


def _labels(schema: DjangoSchema, label: str, where: JSONObject) -> JSONObject:
    payload = _post(
        schema,
        "query($where: SpanFilterInputType) "
        f"{{ rows(filter: $where) {{ edges {{ node {{ {label} }} }} }} }}",
        {"where": where},
    )
    if "errors" in payload:
        return payload
    edges = json_list(payload, "data", "rows", "edges")
    return {"rows": sorted(json_str(edge, "node", label) for edge in edges)}


def _raw(schema: DjangoSchema, query: str) -> JSONObject:
    return _post(schema, "query($query: String!) { rawRows(query: $query) }", {"query": query})


_DAY = ("2022-01-02", "2024-01-04")
_YEAR = (2022, 2024)
_YEAR_RAW = ("2022", "2024")
_AT = ("2022-01-02T00:00:00+00:00", "2024-01-04T23:59:59+00:00")
_AT_RAW = ("2022-01-02 00:00:00", "2024-01-04 23:59:59")
_PLAIN_LOOKUPS = (
    None,
    "exact",
    "gte",
    "lte",
    "lt",
    "in",
    "iexact",
    "icontains",
    "isnull",
    "range",
)
_COLUMNS: dict[str, tuple[tuple[object, object], tuple[str, str]]] = {
    "price": (("2", "4"), ("2", "4")),
    "label": (("b", "d"), ("b", "d")),
    "signed_big": (("20", "40"), ("20", "40")),
    "occurred_on": (_DAY, _DAY),
    "occurred_at": (_AT, _AT_RAW),
}
_TRANSFORMS: list[tuple[str, str, tuple[object, object], tuple[str, str]]] = [
    (
        "occurred_on",
        "year",
        _YEAR,
        _YEAR_RAW,
    ),
    (
        "occurred_on",
        "year__exact",
        _YEAR,
        _YEAR_RAW,
    ),
    (
        "occurred_on",
        "year__range",
        _YEAR,
        _YEAR_RAW,
    ),
    (
        "occurred_on",
        "year__in",
        _YEAR,
        _YEAR_RAW,
    ),
    (
        "occurred_at",
        "date",
        _DAY,
        _DAY,
    ),
    (
        "occurred_at",
        "date__exact",
        _DAY,
        _DAY,
    ),
    (
        "occurred_at",
        "date__range",
        _DAY,
        _DAY,
    ),
    (
        "occurred_at",
        "date__gte",
        _DAY,
        _DAY,
    ),
    (
        "occurred_at",
        "year",
        _YEAR,
        _YEAR_RAW,
    ),
    (
        "occurred_at",
        "year__exact",
        _YEAR,
        _YEAR_RAW,
    ),
    (
        "occurred_at",
        "year__range",
        _YEAR,
        _YEAR_RAW,
    ),
]
_SPECIMEN_CELLS = [
    pytest.param(
        _Cell(column, lookup, bounds, raw),
        id=f"{column}-{lookup or 'default'}",
    )
    for column, (bounds, raw) in _COLUMNS.items()
    for lookup in _PLAIN_LOOKUPS
] + [
    pytest.param(_Cell(column, lookup, bounds, raw), id=f"{column}-{lookup}")
    for column, lookup, bounds, raw in _TRANSFORMS
]


def _rows_three_ways(schema: DjangoSchema, label: str, cell: _Cell) -> JSONObject:
    """The rows two bounds keep flat, under ``not`` and as raw form data."""
    key = _span_key(schema)
    start, end = cell.bounds
    span: JSONObject = {"span": {key: {"start": start, "end": end}}}
    return {
        "flat": _labels(schema, label, span),
        "not": _labels(schema, label, {"not": span}),
        "raw": _raw(schema, f"span_0={cell.raw[0]}&span_1={cell.raw[1]}"),
    }


_ANSWER: JSONObject = {
    "flat": {"rows": _BETWEEN},
    "not": {"rows": _OUTSIDE},
    "raw": {"data": {"rawRows": _BETWEEN}},
}


@pytest.mark.django_db
@pytest.mark.parametrize("cell", _SPECIMEN_CELLS)
def test_two_bounds_keep_the_rows_between_them_whatever_lookup_is_declared(cell: _Cell) -> None:
    """``span: { <declared>: { start, end } }`` keeps ``b`` .. ``d``; ``not`` keeps ``a`` and ``e``.

    The declared lookup is no comparison of the bounds: a default ``exact``, a ``gte`` or an
    ``in`` keeps the rows between them as ``range`` does, through the declared transform
    (``occurred_at`` + ``date`` keeps ``d``, stamped 09:30 on the end day), and the same
    rows answer the set's raw form data.
    """
    _seed_specimens()

    assert _rows_three_ways(_specimen_schema(cell), "label", cell) == _ANSWER


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("pk", id="relation-valued-pk"),
        pytest.param("patron__id", id="relation-valued-pk-key-column"),
    ],
)
@pytest.mark.parametrize(
    "lookup_expr",
    [
        None,
        "exact",
        "gte",
        "in",
        "range",
    ],
)
def test_two_bounds_over_a_relation_valued_key_keep_the_rows_between_them(
    field_name: str,
    lookup_expr: str | None,
) -> None:
    """A one-to-one primary key compares its stored integer column as ``gte`` + ``lte``."""
    keys = _seed_profiles()
    cell = _Cell(field_name, lookup_expr, (keys[1], keys[3]), (str(keys[1]), str(keys[3])))

    assert _rows_three_ways(_profile_schema(cell), "postalCode", cell) == _ANSWER


@pytest.mark.django_db
@pytest.mark.parametrize(
    "lookup_expr",
    [
        None,
        "exact",
        "gte",
        "in",
        "range",
    ],
)
def test_two_bounds_over_a_path_through_a_relations_key_keep_the_rows_between_them(
    lookup_expr: str | None,
) -> None:
    """``parent__id`` under any declared lookup keeps the children of the parents between.

    Under ``not`` the complement keeps the parents, whose null key no bound compares.
    """
    keys = _seed_parented_specimens()
    cell = _Cell(
        "parent__id",
        lookup_expr,
        (keys[1], keys[3]),
        (str(keys[1]), str(keys[3])),
    )

    assert _rows_three_ways(_specimen_schema(cell), "label", cell) == {
        "flat": {"rows": _BETWEEN},
        "not": {"rows": [*_OUTSIDE, *(f"p-{label}" for label in _LABELS)]},
        "raw": {"data": {"rawRows": _BETWEEN}},
    }


_PARENTS = [f"p-{label}" for label in _LABELS]
_EVERY_ROW = sorted([*_LABELS, *_PARENTS])


@pytest.mark.django_db
@pytest.mark.parametrize(
    "lookup_expr",
    [
        None,
        "exact",
        "gte",
        "in",
    ],
)
@pytest.mark.parametrize(
    ("field_name", "query", "labels"),
    [
        pytest.param("parent", "span_0={1}&span_1={3}", ["b", "c", "d"], id="forward-both"),
        pytest.param(
            "parent",
            "span_0={1}",
            [
                "b",
                "c",
                "d",
                "e",
            ],
            id="forward-start",
        ),
        pytest.param(
            "parent",
            "span_1={3}",
            [
                "a",
                "b",
                "c",
                "d",
            ],
            id="forward-end",
        ),
        pytest.param("parent", "span_0=-1e30", _EVERY_ROW, id="forward-start-below"),
        pytest.param("parent", "span_1=-1e30", [], id="forward-end-below"),
        pytest.param("parent", "span_1=1e30", _EVERY_ROW, id="forward-end-above"),
        pytest.param(
            "parent",
            "span_0=-1e30&span_1={3}",
            [
                "a",
                "b",
                "c",
                "d",
            ],
            id="forward-both-start-below",
        ),
        pytest.param("parent", "span_0=-1e30&span_1=1e30", _EVERY_ROW, id="forward-both-past"),
        pytest.param(
            "children",
            "span_0={1}&span_1={3}",
            ["p-b", "p-c", "p-d"],
            id="reverse-both",
        ),
        pytest.param("children", "span_0=-1e30", _PARENTS, id="reverse-start-below"),
        pytest.param("children", "span_1=-1e30", [], id="reverse-end-below"),
        pytest.param(
            "children",
            "span_0=-1e30&span_1={3}",
            [
                "p-a",
                "p-b",
                "p-c",
                "p-d",
            ],
            id="reverse-both-start-below",
        ),
        pytest.param(
            "children",
            "span_0={1}&span_1=1e30",
            _PARENTS[1:],
            id="reverse-both-end-above",
        ),
    ],
)
def test_a_raw_range_over_a_relation_itself_applies_its_bounds_as_gte_and_lte(
    field_name: str,
    query: str,
    labels: list[str],
    lookup_expr: str | None,
) -> None:
    """Raw ``span_0`` / ``span_1`` over ``parent`` or ``children`` keep the rows keyed between.

    No range input over a relation is published, so only raw form data reaches it. The
    bounds compare the column the relation's values are compared on (the target's primary
    key), two bounds as its ``gte`` + ``lte`` in one predicate since Django registers no
    ``range`` on a relation, the declared lookup aside. A bound past that column widens or
    matches nothing exactly as the same bound over ``<relation>__id`` does: a lone start
    below it, or an end above it, constrains the forward key to nothing, so the parents'
    null ``parent`` rows are kept too, while the reverse relation still joins, keeping only
    the rows with a related row, as ``children__id`` does.
    """
    seeded = _seed_parented_specimens()
    keys = (
        [
            child.pk
            for child in scalars.ScalarSpecimen.objects.filter(parent__isnull=False).order_by("pk")
            if child.pk is not None
        ]
        if field_name == "children"
        else seeded
    )
    raw = query.format(*keys)
    relation = _raw_only_schema(_Cell(field_name, lookup_expr, (None, None), ("", "")))
    column = _raw_only_schema(_Cell(f"{field_name}__id", lookup_expr, (None, None), ("", "")))

    assert _raw(relation, raw) == {"data": {"rawRows": sorted(labels)}}
    assert _raw(column, raw) == {"data": {"rawRows": sorted(labels)}}


#: A decimal past ``signed_big``'s range whose ``int()`` takes about three seconds, where the
#: held integer answers in about ten milliseconds.
_PAST_THE_COLUMN = "-1e400000"
#: The answer a held bound must arrive within: about a hundred times what a held request takes
#: and about a third of what converting ``_PAST_THE_COLUMN`` takes, so a slow runner neither
#: fails a held request nor passes an unheld one.
_HELD_WITHIN_SECONDS = 1.0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "lookup_expr",
    [
        "iexact",
        "contains",
        "icontains",
        "exact",
        "range",
    ],
)
@pytest.mark.parametrize(
    ("query", "labels"),
    [
        pytest.param(f"span_0={_PAST_THE_COLUMN}", _LABELS, id="lone-start-below"),
        pytest.param(f"span_1={_PAST_THE_COLUMN}", [], id="lone-end-below"),
        pytest.param(f"span_0={_PAST_THE_COLUMN}&span_1=30", ["a", "b", "c"], id="both"),
    ],
)
def test_a_raw_bound_past_an_integer_column_is_held_under_any_declared_lookup(
    query: str,
    labels: list[str],
    lookup_expr: str,
) -> None:
    """A ``signed_big`` bound below the column answers from the end it lies past, at once.

    The range applies ``gte`` / ``lte`` / ``range`` whatever it declares, each preparing its
    value through the column, so the bound is held to one past the column's end before any
    lookup reads it, under a declared ``iexact``, ``contains`` or ``icontains`` as under
    ``range``.
    """
    _seed_specimens()
    schema = _raw_only_schema(_Cell("signed_big", lookup_expr, (None, None), ("", "")))

    started = time.perf_counter()
    answered = _raw(schema, query)
    elapsed = time.perf_counter() - started

    assert answered == {"data": {"rawRows": labels}}
    assert elapsed < _HELD_WITHIN_SECONDS, elapsed
