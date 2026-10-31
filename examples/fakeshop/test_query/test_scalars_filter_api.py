"""Live GraphQL HTTP tests for scalar filtering, ordering, and related-queryset behavior.

Where ``test_scalars_api.py`` pins the converter table on the OUTPUT side,
these tests exercise it on the INPUT side via the filtersets wired in
``apps.scalars.schema``. The scalar types are NOT Relay nodes, so
``id: { in: [...] }`` resolves to the django-filter-generated
``BaseInFilter`` -> ``list[int]`` converter path -- the non-Relay
counterpart to the library/products own-PK ``GlobalIDMultipleChoiceFilter``
path. ``ScalarSpecimenFilter.tag`` (a ``RelatedFilter`` onto a type whose
``get_queryset`` filters ``active=True``) exercises related-branch
visibility through a relation traversal. The self-referential ``parent`` /
``children`` relation keys filter by raw ``Int`` specimen pks (the target type is
not a Relay node): one pk or a list for the forward key, a list for the reverse
one, with the README membership rules on every list. ``price_span`` is a declared
``RangeFilter`` on both specimen filtersets: its nested input type is scoped
per owning filterset and the ``range`` lookup applies over the wire; a lone
``start`` / ``end`` applies as ``gte`` / ``lte`` and a range with no bound filters nothing;
each bound is cleaned as ``price: { gte }`` cleans its value, so a bound the column cannot
hold is ``FILTER_INVALID``. ``price_among`` is a declared ``ListFilter`` (``in``) on the
same column whose elements are cleaned the same way. A temporal value the database the
query runs on cannot bind (on SQLite an aware datetime whose UTC projection leaves years
1..9999, an aware time) is ``FILTER_INVALID`` keyed to its form field on each adapter-bound
leaf, member and bound, under ``not`` and through ``partner``; PostgreSQL binds those
values, so there the same input filters. The declared ``occurredDayOf`` (``lookup_expr``
``date``) compares the ``date`` transform's output, so it takes a ``Date`` and filters by
that day, flat, under ``not`` and through ``partner`` nested and flat. ``parentDayOf`` on
``allScalarSpecimensByParentStamp`` crosses the ``FilteredRelation`` alias that root
field's queryset holds, a path the schema build cannot resolve, so it keeps its declared
``DateTime``: one whose date in the default time zone (``TIME_ZONE``) leaves years
1..9999 is ``FILTER_INVALID`` on every backend. The declared ``occurredYearAmong`` (``in``) and
``occurredYearSpan`` (``range``) over ``occurred_at__year``, a path through the column's
``year`` transform, are typed by the transform's ``IntegerField`` output (``[Int!]``,
``Int`` bounds) and filter by the year sent, flat, under ``not`` and through ``partner``
nested and flat; a text year or one past ``Int``'s 32 bits is the scalar's own refusal.
A holder schema (``generated_year_schema``) serves ``Meta.fields`` ``year`` / ``year__gt`` /
``year__in`` leaves on ``occurred_at``, which no shipped set generates: each takes the
transform's ``Int`` and filters by it, and a ``year`` / ``year__gt`` of 0 or 10000, whose
datetime bound Django cannot form, is ``FILTER_INVALID`` keyed to its form field, flat,
under ``not`` and through ``partner`` nested and flat. Its declared ``ListFilter``
(``year__in``) and ``RangeFilter`` (``year__range``, a lone bound included) take and filter
by an ``Int`` year, and the same shapes with a ``method=`` keep the column's ``DateTime``,
which reaches the method; the two ranges mint two range types.
On PostgreSQL a UTC offset the server refuses (16:00 or more either way, or, bound as
text as Django's default psycopg cursor binds, a fraction of a second) is
``FILTER_INVALID`` the same way, where SQLite projects the datetime onto UTC and filters.
django-filter's own range filters
(``priceBetween``, ``occurredBetween`` over ``DateRangeWidget``, ``occurredInBoxes`` over a
plain ``MultiWidget``, ``priceInUnderscoredBoxes`` over a consumer widget reading ``__``
keys, and ``priceInFieldBoxes``, whose consumer ``field`` property installs its widget)
apply every bound they are sent, under the keys each widget reads.
The per-field ``"__all__"`` leaves never publish a ``django.contrib.postgres``
lookup Django registers onto a core field (``containedBy`` on the numeric and
temporal leaves), whether or not a PostgreSQL driver is installed, and publish
the text-pattern lookups (``iExact`` / ``contains`` / ``startsWith`` / ``regex`` / ...)
only on the text column ``label``, where ``prefix``, a lookup registered on the
``ScalarSpecimen.label`` field instance alone, is a leaf of that set and of no
``ScalarSpecimenTag`` label set. Listed explicitly on ``occurredAt`` or
``unsignedBig``, a pattern leaf is a ``String`` the backend matches against its text
rendering of the column, on SQLite and PostgreSQL alike.
"""

import datetime
import uuid
from collections.abc import Iterator, Mapping
from decimal import Decimal

import pytest
import strawberry
from apps.scalars import models
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import (
    JSONObject,
    json_at,
    json_list,
    json_object,
    json_str,
    post_graphql,
    response_json,
)
from graphql_client import assert_graphql_data as _assert_graphql_data
from graphql_client import assert_graphql_success as _assert_graphql_success
from strawberry import relay

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, ListFilter, RangeFilter, RelatedFilter
from django_strawberry_framework.views import DjangoGraphQLView

_DATE = datetime.date(2021, 6, 15)
_DATETIME = datetime.datetime(2021, 6, 15, 9, 30, tzinfo=datetime.timezone.utc)
_TIME = datetime.time(9, 30)
_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")


def _seed_specimen(label: str, **overrides: object) -> models.ScalarSpecimen:
    defaults: dict[str, object] = {
        "label": label,
        "flag": False,
        "score": 1.0,
        "occurred_on": _DATE,
        "occurred_at": _DATETIME,
        "occurred_time": _TIME,
        "external_id": uuid.uuid4(),
        "signed_big": 1,
        "unsigned_big": 1,
    }
    defaults.update(overrides)
    return models.ScalarSpecimen.objects.create(**defaults)


@pytest.mark.django_db
def test_scalars_filter_by_label_icontains() -> None:
    """``label: { iContains }`` keeps only labels containing the supplied text."""
    _seed_specimen("alpha")
    _seed_specimen("beta")
    _assert_graphql_data(
        """
        query {
          allScalarSpecimens(filter: { label: { iContains: "alph" } }) {
            label
          }
        }
        """,
        {"allScalarSpecimens": [{"label": "alpha"}]},
    )


@pytest.mark.django_db
def test_scalars_filter_by_flag_exact() -> None:
    """``flag: { exact: true }`` keeps only the two true rows."""
    _seed_specimen("alpha", flag=True)
    _seed_specimen("beta", flag=False)
    _seed_specimen("gamma", flag=True)
    _assert_graphql_data(
        """
        query {
          allScalarSpecimens(filter: { flag: { exact: true } }, orderBy: [{ label: ASC }]) {
            label
          }
        }
        """,
        {"allScalarSpecimens": [{"label": "alpha"}, {"label": "gamma"}]},
    )


@pytest.mark.django_db
def test_scalars_filter_by_non_relay_pk_in_list() -> None:
    """Non-Relay ``id: { in: [...] }`` resolves to the integer CSV path.

    The scalar types are not Relay nodes, so ``id`` is a plain integer column.
    Its ``in`` lookup routes through the framework's ``IntegerInFilter`` (a
    ``BaseInFilter`` subclass that also drops out-of-range members and matches
    nothing on a fully-dropped non-empty list) and converts to a ``list[Int]``
    CSV input rather than the own-PK ``GlobalIDMultipleChoiceFilter`` the Relay
    apps use. The wire accepts raw integer keys rather than GlobalIDs.
    """
    alpha = _seed_specimen("alpha")
    _seed_specimen("beta")
    gamma = _seed_specimen("gamma")
    _assert_graphql_data(
        f"""
        query {{
          allScalarSpecimens(
            filter: {{ id: {{ in: [{alpha.pk}, {gamma.pk}] }} }}
            orderBy: [{{ label: ASC }}]
          ) {{
            label
          }}
        }}
        """,
        {"allScalarSpecimens": [{"label": "alpha"}, {"label": "gamma"}]},
    )


@pytest.mark.django_db
def test_scalars_filter_by_related_tag_label() -> None:
    """The related tag predicate reads active rows and excludes an inactive matching tag in SQL."""
    hot = models.ScalarSpecimenTag.objects.create(label="hot", active=True)
    hidden = models.ScalarSpecimenTag.objects.create(label="hot archived", active=False)
    _seed_specimen("alpha", tag=hot)
    _seed_specimen("hidden", tag=hidden)
    _seed_specimen("beta")
    with CaptureQueriesContext(connection) as captured:
        _assert_graphql_data(
            'query { allScalarSpecimens(filter: { tag: { label: { iContains: "hot" } } }) { label } }',
            {"allScalarSpecimens": [{"label": "alpha"}]},
        )
    specimen_sql = [
        row["sql"]
        for row in captured.captured_queries
        if 'FROM "scalars_scalarspecimen"' in row["sql"]
    ]
    assert len(specimen_sql) == 1, captured.captured_queries
    assert "active" in specimen_sql[0], specimen_sql
    assert "EXISTS" in specimen_sql[0].upper(), specimen_sql


@pytest.mark.django_db
def test_scalars_order_by_label_desc() -> None:
    """``orderBy: [{ label: DESC }]`` sorts specimens by label descending."""
    _seed_specimen("alpha")
    _seed_specimen("gamma")
    _seed_specimen("beta")
    expected = [
        {"label": specimen.label} for specimen in models.ScalarSpecimen.objects.order_by("-label")
    ]
    _assert_graphql_data(
        "query { allScalarSpecimens(orderBy: [{ label: DESC }]) { label } }",
        {"allScalarSpecimens": expected},
    )


_RANGE_TYPE_QUERY = """
query {
  scalar: __type(name: "ScalarSpecimenFilterPriceRangeInputType") {
    name
    inputFields { name }
  }
  nullable: __type(name: "NullableScalarSpecimenFilterPriceRangeInputType") {
    name
    inputFields { name }
  }
}
"""


@pytest.mark.django_db
def test_range_input_types_are_scoped_per_filterset() -> None:
    """Two shipped filtersets sharing a RangeFilter field_name mint distinct nested types.

    ``price_span`` is a declared ``RangeFilter(field_name="price")`` on both
    ``ScalarSpecimenFilter`` and ``NullableScalarSpecimenFilter``. Unscoped,
    both nested classes would claim ``PriceRangeInputType`` (one merged type
    while their axes match, two shapes no schema could serve once they differ).
    The owning-filterset qualifier keeps both
    ``__type`` results non-null, each with ``start`` / ``end``.
    """
    data = _assert_graphql_success(_RANGE_TYPE_QUERY)

    scalar = json_object(data, "scalar")
    nullable = json_object(data, "nullable")
    assert scalar["name"] == "ScalarSpecimenFilterPriceRangeInputType"
    assert nullable["name"] == "NullableScalarSpecimenFilterPriceRangeInputType"
    assert scalar["name"] != nullable["name"]
    assert {json_at(field, "name") for field in json_list(scalar, "inputFields")} == {
        "start",
        "end",
    }
    assert {json_at(field, "name") for field in json_list(nullable, "inputFields")} == {
        "start",
        "end",
    }


@pytest.mark.django_db
def test_scalars_filter_by_price_span_range() -> None:
    """Declared ``priceSpan: { range: { start, end } }`` keeps in-range rows and drops the rest."""
    _seed_specimen("cheap", price=Decimal("1.0000"))
    _seed_specimen("mid", price=Decimal("50.0000"))
    _seed_specimen("dear", price=Decimal("50000.0000"))
    _assert_graphql_data(
        """
        query {
          allScalarSpecimens(
            filter: { priceSpan: { range: { start: "10.0000", end: "100.0000" } } }
          ) {
            label
          }
        }
        """,
        {"allScalarSpecimens": [{"label": "mid"}]},
    )


_BY_FILTER = """
query ($filter: ScalarSpecimenFilterInputType) {
  allScalarSpecimens(filter: $filter, orderBy: [{ id: ASC }]) {
    label
  }
}
"""


def _seed_price_tiers() -> list[models.ScalarSpecimen]:
    """One specimen per price tier: ``cheap`` (1), ``mid`` (50), ``dear`` (50000)."""
    return [
        _seed_specimen("cheap", price=Decimal("1.0000")),
        _seed_specimen("mid", price=Decimal("50.0000")),
        _seed_specimen("dear", price=Decimal("50000.0000")),
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("price_range", "labels"),
    [
        pytest.param({"start": "10.0000"}, ["mid", "dear"], id="start-only"),
        pytest.param({"end": "100.0000"}, ["cheap", "mid"], id="end-only"),
        pytest.param({"start": "10.0000", "end": None}, ["mid", "dear"], id="start-null-end"),
        pytest.param({"start": None, "end": "100.0000"}, ["cheap", "mid"], id="null-start-end"),
        pytest.param({"start": None, "end": None}, ["cheap", "mid", "dear"], id="both-null"),
        pytest.param({}, ["cheap", "mid", "dear"], id="empty"),
        pytest.param(None, ["cheap", "mid", "dear"], id="range-null"),
        pytest.param({"start": "10.0000", "end": "100.0000"}, ["mid"], id="both-bounds"),
    ],
)
def test_scalars_filter_price_span_one_sided_bounds(
    price_range: dict[str, str | None] | None,
    labels: list[str],
) -> None:
    """A lone ``start`` keeps rows at or above it, a lone ``end`` rows at or below it.

    A ``null`` bound counts as left out, and a range with neither bound filters nothing.
    """
    _seed_price_tiers()
    _assert_graphql_data(
        _BY_FILTER,
        {"allScalarSpecimens": [{"label": label} for label in labels]},
        variables={"filter": {"priceSpan": {"range": price_range}}},
    )


@pytest.mark.django_db
def test_scalars_filter_not_price_span_start_only_keeps_the_complement() -> None:
    """``not: { priceSpan: { range: { start } } }`` keeps exactly the rows below the start."""
    _seed_price_tiers()
    _assert_graphql_data(
        _BY_FILTER,
        {"allScalarSpecimens": [{"label": "cheap"}]},
        variables={"filter": {"not": {"priceSpan": {"range": {"start": "10.0000"}}}}},
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("price_range", "labels"),
    [
        pytest.param({"start": "10.0000"}, ["of-mid", "of-dear"], id="start-only"),
        pytest.param({"end": "100.0000"}, ["of-cheap", "of-mid"], id="end-only"),
    ],
)
def test_nullable_scalars_filter_partner_price_span_one_sided_bounds(
    price_range: dict[str, str],
    labels: list[str],
) -> None:
    """A one-sided range under the ``partner`` related branch applies its lone bound too."""
    for partner in _seed_price_tiers():
        models.NullableScalarSpecimen.objects.create(label=f"of-{partner.label}", partner=partner)
    _assert_graphql_data(
        """
        query ($filter: NullableScalarSpecimenFilterInputType) {
          allNullableScalarSpecimens(filter: $filter) {
            label
          }
        }
        """,
        {"allNullableScalarSpecimens": [{"label": label} for label in labels]},
        variables={"filter": {"partner": {"priceSpan": {"range": price_range}}}},
    )


_NOT_A_NUMBER = {"message": "Enter a number.", "code": "invalid"}
_PAST_THE_CAP = {
    "message": "Ensure this value is less than or equal to 1e+50.",
    "code": "max_value",
}

_BY_NULLABLE_FILTER = """
query ($filter: NullableScalarSpecimenFilterInputType) {
  allNullableScalarSpecimens(filter: $filter) {
    label
  }
}
"""


def _bounds(side: str, bound: str) -> dict[str, str]:
    """A range holding ``bound`` on ``side`` (``start``, ``end`` or ``both``)."""
    return {"start": bound, "end": bound} if side == "both" else {side: bound}


@pytest.mark.django_db
@pytest.mark.parametrize("side", ["start", "end", "both"])
@pytest.mark.parametrize(
    ("bound", "refusal"),
    [
        pytest.param("NaN", _NOT_A_NUMBER, id="nan"),
        pytest.param("sNaN", _NOT_A_NUMBER, id="snan"),
        pytest.param("Infinity", _NOT_A_NUMBER, id="infinity"),
        pytest.param("-Infinity", _NOT_A_NUMBER, id="minus-infinity"),
        pytest.param("1e999999", _PAST_THE_CAP, id="past-the-cap"),
    ],
)
def test_scalars_filter_price_span_bound_the_column_cannot_hold_is_filter_invalid(
    side: str,
    bound: str,
    refusal: dict[str, str],
) -> None:
    """Each ``priceSpan`` bound is cleaned as ``price: { gte }`` cleans its value.

    A non-finite decimal is the ``DecimalField``'s ``Enter a number.`` and a value
    past django-filter's ``1e50`` number cap its ``max_value`` refusal, keyed to the
    range's form field, never a value handed to the ORM.
    """
    _seed_price_tiers()
    payload = response_json(
        post_graphql(
            _BY_FILTER,
            variables={"filter": {"priceSpan": {"range": _bounds(side, bound)}}},
        ),
    )

    assert payload["data"] is None, payload
    (error,) = json_list(payload, "errors")
    assert json_at(error, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {"price_span": [refusal]},
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "filter_input", "form_key"),
    [
        pytest.param(
            _BY_FILTER,
            {"not": {"priceSpan": {"range": {"start": "NaN"}}}},
            "not__price_span",
            id="not",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partner": {"priceSpan": {"range": {"end": "NaN"}}}},
            "partner__price_span",
            id="nested-partner",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partnerPriceSpan": {"range": {"start": "NaN", "end": "100.0000"}}},
            "partner__price_span",
            id="flat-partner",
        ),
    ],
)
def test_price_span_nan_bound_is_filter_invalid_in_every_branch(
    query: str,
    filter_input: dict[str, object],
    form_key: str,
) -> None:
    """A ``NaN`` bound is ``FILTER_INVALID`` under ``not`` and through the ``partner`` relation."""
    for partner in _seed_price_tiers():
        models.NullableScalarSpecimen.objects.create(label=f"of-{partner.label}", partner=partner)
    payload = response_json(post_graphql(query, variables={"filter": filter_input}))

    assert payload["data"] is None, payload
    (error,) = json_list(payload, "errors")
    assert json_at(error, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {form_key: [_NOT_A_NUMBER]},
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("prices", "labels"),
    [
        pytest.param(["50.0000", "1"], ["cheap", "mid"], id="members"),
        pytest.param(["1.0"], ["cheap"], id="cleaned-member"),
        pytest.param([], [], id="empty"),
    ],
)
def test_scalars_filter_price_among_keeps_the_listed_prices(
    prices: list[str],
    labels: list[str],
) -> None:
    """Declared ``priceAmong: { in }`` keeps the rows whose price is listed; ``[]`` keeps none."""
    _seed_price_tiers()
    _assert_graphql_data(
        _BY_FILTER,
        {"allScalarSpecimens": [{"label": label} for label in labels]},
        variables={"filter": {"priceAmong": {"in": prices}}},
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "query",
        "filter_input",
        "form_key",
        "refusal",
    ),
    [
        pytest.param(
            _BY_FILTER,
            {"priceAmong": {"in": ["NaN"]}},
            "price_among",
            _NOT_A_NUMBER,
            id="nan",
        ),
        pytest.param(
            _BY_FILTER,
            {"priceAmong": {"in": ["1", "sNaN"]}},
            "price_among",
            _NOT_A_NUMBER,
            id="snan-beside-a-number",
        ),
        pytest.param(
            _BY_FILTER,
            {"priceAmong": {"in": ["Infinity"]}},
            "price_among",
            _NOT_A_NUMBER,
            id="infinity",
        ),
        pytest.param(
            _BY_FILTER,
            {"priceAmong": {"in": ["-Infinity"]}},
            "price_among",
            _NOT_A_NUMBER,
            id="minus-infinity",
        ),
        pytest.param(
            _BY_FILTER,
            {"priceAmong": {"in": ["1e999999"]}},
            "price_among",
            _PAST_THE_CAP,
            id="past-the-cap",
        ),
        pytest.param(
            _BY_FILTER,
            {"not": {"priceAmong": {"in": ["NaN"]}}},
            "not__price_among",
            _NOT_A_NUMBER,
            id="not",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partner": {"priceAmong": {"in": ["NaN"]}}},
            "partner__price_among",
            _NOT_A_NUMBER,
            id="nested-partner",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partnerPriceAmong": {"in": ["NaN"]}},
            "partner__price_among",
            _NOT_A_NUMBER,
            id="flat-partner",
        ),
    ],
)
def test_price_among_element_the_column_cannot_hold_is_filter_invalid(
    query: str,
    filter_input: dict[str, object],
    form_key: str,
    refusal: dict[str, str],
) -> None:
    """Each ``priceAmong`` element is cleaned as ``price: { in }`` cleans its members.

    A non-finite decimal is the ``DecimalField``'s ``Enter a number.`` and a value past
    django-filter's ``1e50`` number cap its ``max_value`` refusal, keyed to the list's form
    field, flat, under ``not`` and through the ``partner`` relation, never a value handed
    to the ORM.
    """
    for partner in _seed_price_tiers():
        models.NullableScalarSpecimen.objects.create(label=f"of-{partner.label}", partner=partner)
    payload = response_json(post_graphql(query, variables={"filter": filter_input}))

    assert payload["data"] is None, payload
    (error,) = json_list(payload, "errors")
    assert json_at(error, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {form_key: [refusal]},
    }


_UNBINDABLE = {"message": "Enter a value the database can represent.", "code": "invalid"}
# Aware values the scalar parse and the form clean accept: a datetime whose UTC projection
# falls in year 0, one whose projection falls in year 10000, and an aware time. SQLite
# projects an aware datetime onto UTC and refuses an aware time; PostgreSQL binds all three,
# whose UTC offsets it accepts.
_BEFORE_YEAR_ONE = "0001-01-01T00:00:00+05:00"
_PAST_YEAR_9999 = "9999-12-31T23:00:00-05:00"
_AWARE_TIME = "09:30:00+00:00"
_BINDABLE_DATETIME = _DATETIME.isoformat()


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "query",
        "unbindable",
        "form_key",
        "postgresql_labels",
        "bindable",
        "labels",
    ),
    [
        pytest.param(
            _BY_FILTER,
            {"occurredAt": {"exact": _BEFORE_YEAR_ONE}},
            "occurred_at",
            [],
            {"occurredAt": {"exact": _BINDABLE_DATETIME}},
            ["alpha"],
            id="exact-before-year-one",
        ),
        pytest.param(
            _BY_FILTER,
            {"occurredAt": {"gt": _PAST_YEAR_9999}},
            "occurred_at__gt",
            [],
            {"occurredAt": {"lt": "9999-12-31T23:00:00+00:00"}},
            ["alpha"],
            id="gt-past-year-9999",
        ),
        pytest.param(
            _BY_FILTER,
            {"occurredAt": {"in": [_BINDABLE_DATETIME, _BEFORE_YEAR_ONE]}},
            "occurred_at__in",
            ["alpha"],
            {"occurredAt": {"in": [_BINDABLE_DATETIME]}},
            ["alpha"],
            id="in-member",
        ),
        pytest.param(
            _BY_FILTER,
            {"occurredAt": {"range": [_BEFORE_YEAR_ONE, _BINDABLE_DATETIME]}},
            "occurred_at__range",
            ["alpha"],
            {"occurredAt": {"range": ["0001-01-01T00:00:00+00:00", _BINDABLE_DATETIME]}},
            ["alpha"],
            id="range-bound",
        ),
        pytest.param(
            _BY_FILTER,
            {"occurredTime": {"exact": _AWARE_TIME}},
            "occurred_time",
            ["alpha"],
            {"occurredTime": {"exact": "09:30:00"}},
            ["alpha"],
            id="aware-time",
        ),
        pytest.param(
            _BY_FILTER,
            {"occurredTime": {"in": ["09:30:00", _AWARE_TIME]}},
            "occurred_time__in",
            ["alpha"],
            {"occurredTime": {"in": ["09:30:00"]}},
            ["alpha"],
            id="aware-time-in-member",
        ),
        pytest.param(
            _BY_FILTER,
            {"not": {"occurredAt": {"exact": _BEFORE_YEAR_ONE}}},
            "not__occurred_at",
            ["alpha"],
            {"not": {"occurredAt": {"exact": _BINDABLE_DATETIME}}},
            [],
            id="not",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partner": {"occurredAt": {"lte": _PAST_YEAR_9999}}},
            "partner__occurred_at__lte",
            ["of-alpha"],
            {"partner": {"occurredAt": {"lte": _BINDABLE_DATETIME}}},
            ["of-alpha"],
            id="nested-partner",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partnerOccurredAt": {"gte": _BEFORE_YEAR_ONE}},
            "partner__occurred_at__gte",
            ["of-alpha"],
            {"partnerOccurredAt": {"gte": _BINDABLE_DATETIME}},
            ["of-alpha"],
            id="flat-partner",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partnerOccurredTime": {"exact": _AWARE_TIME}},
            "partner__occurred_time",
            ["of-alpha"],
            {"partnerOccurredTime": {"exact": "09:30:00"}},
            ["of-alpha"],
            id="flat-partner-aware-time",
        ),
    ],
)
def test_temporal_value_the_database_cannot_bind_is_filter_invalid(
    query: str,
    unbindable: dict[str, object],
    form_key: str,
    postgresql_labels: list[str],
    bindable: dict[str, object],
    labels: list[str],
) -> None:
    """A temporal value the database cannot bind is ``FILTER_INVALID`` keyed to its form field.

    The value is held to the database the queryset runs on: on SQLite an aware
    datetime whose UTC projection leaves years 1..9999 and an aware time are each
    refused with the package's fixed message, for every member of an ``in`` list and
    every ``range`` bound, flat, under ``not`` and through the ``partner`` relation,
    nested and flat, never the driver's error. PostgreSQL binds them (their UTC offsets
    are ones it accepts), so there the same input filters (``postgresql_labels``). A value the
    database binds filters on both.
    """
    alpha = _seed_specimen("alpha")
    models.NullableScalarSpecimen.objects.create(label="of-alpha", partner=alpha)
    root = "allScalarSpecimens" if query == _BY_FILTER else "allNullableScalarSpecimens"
    control = response_json(post_graphql(query, variables={"filter": bindable}))
    payload = response_json(post_graphql(query, variables={"filter": unbindable}))

    assert control == {"data": {root: [{"label": label} for label in labels]}}
    if connection.vendor == "postgresql":
        assert payload == {"data": {root: [{"label": label} for label in postgresql_labels]}}
        return
    assert payload["data"] is None, payload
    (error,) = json_list(payload, "errors")
    assert json_at(error, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {form_key: [_UNBINDABLE]},
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "day_filter", "labels"),
    [
        pytest.param(_BY_FILTER, {"occurredDayOf": {"date": "2021-06-15"}}, ["alpha"], id="flat"),
        pytest.param(_BY_FILTER, {"occurredDayOf": {"date": "2021-06-16"}}, [], id="other-day"),
        pytest.param(_BY_FILTER, {"not": {"occurredDayOf": {"date": "2021-06-15"}}}, [], id="not"),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partner": {"occurredDayOf": {"date": "2021-06-15"}}},
            ["of-alpha"],
            id="nested-partner",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partnerOccurredDayOf": {"date": "2021-06-15"}},
            ["of-alpha"],
            id="flat-partner",
        ),
    ],
)
def test_date_through_the_declared_date_transform_filters_by_that_date(
    query: str,
    day_filter: dict[str, object],
    labels: list[str],
) -> None:
    """``occurredDayOf`` compares the ``date`` transform's output, so it takes a ``Date``.

    It is a declared ``DateTimeFilter`` over ``occurred_at`` with ``lookup_expr="date"``: the
    value is compared with the column's date in the default time zone (``TIME_ZONE``), a
    ``DateField`` output, so the input is a ``Date`` and filters by that day, flat, under
    ``not`` and through ``partner`` nested and flat. A datetime is the ``Date`` scalar's own
    refusal.
    """
    alpha = _seed_specimen("alpha")
    models.NullableScalarSpecimen.objects.create(label="of-alpha", partner=alpha)
    root = "allScalarSpecimens" if query == _BY_FILTER else "allNullableScalarSpecimens"
    refused = response_json(
        post_graphql(
            _BY_FILTER,
            variables={"filter": {"occurredDayOf": {"date": _BINDABLE_DATETIME}}},
        ),
    )

    assert response_json(post_graphql(query, variables={"filter": day_filter})) == {
        "data": {root: [{"label": label} for label in labels]},
    }
    assert refused.get("data") is None, refused
    (error,) = json_list(refused, "errors")
    assert "Date" in json_str(error, "message")


_BY_PARENT_STAMP = """
query ($filter: ScalarSpecimenParentStampFilterInputType) {
  allScalarSpecimensByParentStamp(filter: $filter) {
    label
  }
}
"""


@pytest.mark.django_db
def test_datetime_crossing_a_filtered_relation_alias_outside_years_one_to_9999_is_filter_invalid() -> (
    None
):
    """A datetime crossing a ``FilteredRelation`` alias is held to the database like any other path.

    ``parentDayOf`` is a declared ``DateTimeFilter`` whose ``field_name``
    (``par__occurred_at``) crosses ``par``, the ``FilteredRelation("parent")`` alias the
    resolver's queryset holds, into the parent's ``occurred_at`` ``date`` transform. The
    path names no model field, so it is resolved over that queryset as Django resolves it:
    a datetime whose date falls in year 0 is refused keyed to its form field on every
    backend, never the conversion's ``OverflowError``, and a datetime whose date binds
    filters by the parent's day.
    """
    alpha = _seed_specimen("alpha")
    _seed_specimen("child-of-alpha", parent=alpha)
    control = response_json(
        post_graphql(
            _BY_PARENT_STAMP,
            variables={"filter": {"parentDayOf": {"date": _BINDABLE_DATETIME}}},
        ),
    )
    payload = response_json(
        post_graphql(
            _BY_PARENT_STAMP,
            variables={"filter": {"parentDayOf": {"date": _BEFORE_YEAR_ONE}}},
        ),
    )

    assert control == {"data": {"allScalarSpecimensByParentStamp": [{"label": "child-of-alpha"}]}}
    assert payload["data"] is None, payload
    (error,) = json_list(payload, "errors")
    assert json_at(error, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {"parent_day_of": [_UNBINDABLE]},
    }


_YEAR_LEAF_TYPES_QUERY = """
query {
  among: __type(name: "ScalarSpecimenFilterOccurredYearAmongFilterInputType") {
    inputFields { name type { kind ofType { kind ofType { name } } } }
  }
  span: __type(name: "ScalarSpecimenFilterOccurredAtYearRangeInputType") {
    inputFields { name type { name } }
  }
}
"""


@pytest.mark.django_db
def test_year_through_a_declared_transform_path_is_typed_by_the_transforms_output() -> None:
    """A declared path through ``occurred_at``'s ``year`` publishes the transform's ``Int``.

    ``occurredYearAmong`` / ``occurredYearSpan`` are a declared ``ListFilter`` (``in``) and
    ``RangeFilter`` (``range``) over ``occurred_at__year``, a path naming no model field:
    each member and bound is a value of the ``year`` transform's ``IntegerField`` output,
    never of the declared form field (``String``) or the ``DateTimeField`` column.
    """
    data = _assert_graphql_success(_YEAR_LEAF_TYPES_QUERY)

    assert json_list(data, "among", "inputFields") == [
        {
            "name": "in",
            "type": {"kind": "LIST", "ofType": {"kind": "NON_NULL", "ofType": {"name": "Int"}}},
        },
    ]
    assert json_list(data, "span", "inputFields") == [
        {"name": "start", "type": {"name": "Int"}},
        {"name": "end", "type": {"name": "Int"}},
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "year_filter", "labels"),
    [
        pytest.param(_BY_FILTER, {"occurredYearAmong": {"in": [2021]}}, ["alpha"], id="in"),
        pytest.param(_BY_FILTER, {"occurredYearAmong": {"in": [2019]}}, [], id="in-no-row"),
        pytest.param(
            _BY_FILTER,
            {"occurredYearSpan": {"range": {"start": 2020, "end": 2020}}},
            ["beta"],
            id="range",
        ),
        pytest.param(
            _BY_FILTER,
            {"not": {"occurredYearAmong": {"in": [2020]}}},
            ["alpha"],
            id="not",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partner": {"occurredYearAmong": {"in": [2021]}}},
            ["of-alpha"],
            id="nested-partner",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partnerOccurredYearSpan": {"range": {"start": 2020, "end": 2020}}},
            ["of-beta"],
            id="flat-partner",
        ),
    ],
)
def test_year_through_a_declared_transform_path_filters_by_the_integer_sent(
    query: str,
    year_filter: dict[str, object],
    labels: list[str],
) -> None:
    """An ``Int`` year sent to ``occurredYearAmong`` / ``occurredYearSpan`` filters by that year.

    Flat, under ``not`` and through ``partner`` nested and flat, the integer reaches the
    ``year`` transform's predicate as sent.
    """
    alpha = _seed_specimen("alpha")
    beta = _seed_specimen("beta", occurred_at=_DATETIME.replace(year=2020))
    models.NullableScalarSpecimen.objects.create(label="of-alpha", partner=alpha)
    models.NullableScalarSpecimen.objects.create(label="of-beta", partner=beta)
    root = "allScalarSpecimens" if query == _BY_FILTER else "allNullableScalarSpecimens"

    assert response_json(post_graphql(query, variables={"filter": year_filter})) == {
        "data": {root: [{"label": label} for label in labels]},
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("member", "refusal"),
    [
        pytest.param("2021", "Int cannot represent non-integer value: '2021'", id="string"),
        pytest.param(
            2**63,
            f"Int cannot represent non 32-bit signed integer value: {2**63}",
            id="past-int32",
        ),
    ],
)
def test_year_member_off_the_int_scalar_is_refused_before_the_filter_runs(
    member: object,
    refusal: str,
) -> None:
    """A text year or one past ``Int``'s 32 bits is refused by the ``Int`` scalar itself.

    No such member reaches the filter, so none is a database bind question: every ``Int``
    year binds on SQLite (64 bits) and PostgreSQL (the transform's 32 bits).
    """
    _seed_specimen("alpha")
    payload = response_json(
        post_graphql(_BY_FILTER, variables={"filter": {"occurredYearAmong": {"in": [member]}}}),
    )

    assert payload.get("data") is None, payload
    (error,) = json_list(payload, "errors")
    assert refusal in json_str(error, "message")


_HOLDER: dict[str, DjangoSchema | None] = {"schema": None}


def _holder_view(request: HttpRequest) -> HttpResponseBase:
    schema = _HOLDER["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-test/", _holder_view)]


@pytest.fixture
def generated_year_schema(private_registry: None) -> Iterator[DjangoSchema]:
    """Serve sets whose leaves reach ``occurred_at``'s ``year`` through the ``lookup_expr``.

    No shipped fakeshop set spells a transform in a ``lookup_expr``, so the holder declares
    one over ``ScalarSpecimen``: ``Meta.fields`` ``year`` / ``year__gt`` / ``year__in`` and
    the null tests ``year__isnull`` / ``date__isnull``; a ``ListFilter`` (``year__in``) and a
    ``RangeFilter`` (``year__range``); and the same list and range shapes with a ``method=``,
    whose method receives the column's values.
    A ``NullableScalarSpecimen`` set reaches it through ``partner``, nested and flat, and
    carries the same two null tests over its own nullable ``occurred_at``.
    """
    del private_registry

    class GeneratedYearFilter(FilterSet):
        years_among = ListFilter(field_name="occurred_at", lookup_expr="year__in")
        years_span = RangeFilter(field_name="occurred_at", lookup_expr="year__range")
        years_of_stamps = ListFilter(
            field_name="occurred_at",
            lookup_expr="year__in",
            method="filter_years_of_stamps",
        )
        year_span_of_stamps = RangeFilter(
            field_name="occurred_at",
            lookup_expr="year__range",
            method="filter_year_span_of_stamps",
        )

        def filter_years_of_stamps(
            self,
            queryset: QuerySet[models.ScalarSpecimen],
            name: str,
            value: list[datetime.datetime],
        ) -> QuerySet[models.ScalarSpecimen]:
            """Keep the rows in the year of any datetime sent."""
            return queryset.filter(**{f"{name}__year__in": [stamp.year for stamp in value]})

        def filter_year_span_of_stamps(
            self,
            queryset: QuerySet[models.ScalarSpecimen],
            name: str,
            value: list[datetime.datetime],
        ) -> QuerySet[models.ScalarSpecimen]:
            """Keep the rows from the first datetime's year through the second's."""
            start, end = value
            return queryset.filter(**{f"{name}__year__range": (start.year, end.year)})

        class Meta:
            model = models.ScalarSpecimen
            fields = {
                "occurred_at": [
                    "year",
                    "year__gt",
                    "year__in",
                    "year__isnull",
                    "date__isnull",
                ],
            }

    class GeneratedYearSpecimenType(DjangoType):
        class Meta:
            model = models.ScalarSpecimen
            fields = ("id", "label")
            interfaces = (relay.Node,)
            filterset_class = GeneratedYearFilter

    class GeneratedYearPartnerFilter(FilterSet):
        partner = RelatedFilter(GeneratedYearFilter, field_name="partner")

        class Meta:
            model = models.NullableScalarSpecimen
            fields = {"label": ["exact"], "occurred_at": ["year__isnull", "date__isnull"]}

    class GeneratedYearPartnerType(DjangoType):
        class Meta:
            model = models.NullableScalarSpecimen
            fields = ("id", "label")
            interfaces = (relay.Node,)
            filterset_class = GeneratedYearPartnerFilter

    @strawberry.type
    class Query:
        specimens: DjangoConnection[GeneratedYearSpecimenType] = DjangoConnectionField(
            GeneratedYearSpecimenType,
        )
        partners: DjangoConnection[GeneratedYearPartnerType] = DjangoConnectionField(
            GeneratedYearPartnerType,
        )

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config())
    _HOLDER["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            yield schema
    finally:
        _HOLDER["schema"] = None


def _holder_payload(root: str, year_filter: Mapping[str, object]) -> JSONObject:
    query = (
        f"query ($filter: {'GeneratedYearFilter' if root == 'specimens' else 'GeneratedYearPartnerFilter'}"
        f"InputType) {{ {root}(filter: $filter) {{ edges {{ node {{ label }} }} }} }}"
    )
    return response_json(
        post_graphql(query, variables={"filter": year_filter}, url="/graphql-test/"),
    )


def _seed_year_partners() -> None:
    """``alpha`` in 2021 and ``beta`` in 2020, each with a nullable partner row."""
    alpha = _seed_specimen("alpha")
    beta = _seed_specimen("beta", occurred_at=_DATETIME.replace(year=2020))
    models.NullableScalarSpecimen.objects.create(label="of-alpha", partner=alpha)
    models.NullableScalarSpecimen.objects.create(label="of-beta", partner=beta)


_GENERATED_YEAR_TYPES_QUERY = """
query {
  exact: __type(name: "GeneratedYearFilterOccurredAtFilterInputType") {
    inputFields { name type { name } }
  }
  among: __type(name: "GeneratedYearFilterOccurredAtYearInFilterInputType") {
    inputFields { name type { kind ofType { kind ofType { name } } } }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.usefixtures("generated_year_schema")
def test_generated_year_leaf_is_typed_by_the_transforms_output() -> None:
    """A ``Meta.fields`` ``year`` / ``year__in`` leaf takes the transform's ``Int``, not ``DateTime``."""
    payload = response_json(post_graphql(_GENERATED_YEAR_TYPES_QUERY, url="/graphql-test/"))

    assert payload == {
        "data": {
            "exact": {"inputFields": [{"name": "year", "type": {"name": "Int"}}]},
            "among": {
                "inputFields": [
                    {
                        "name": "year_In",
                        "type": {
                            "kind": "LIST",
                            "ofType": {"kind": "NON_NULL", "ofType": {"name": "Int"}},
                        },
                    },
                ],
            },
        },
    }


@pytest.mark.django_db
@pytest.mark.usefixtures("generated_year_schema")
@pytest.mark.parametrize(
    ("root", "year_filter", "labels"),
    [
        pytest.param("specimens", {"occurredAt": {"year": 2021}}, ["alpha"], id="exact"),
        pytest.param("specimens", {"occurredAtYearGt": {"year_Gt": 2020}}, ["alpha"], id="gt"),
        pytest.param("specimens", {"occurredAtYearIn": {"year_In": [2020]}}, ["beta"], id="in"),
        pytest.param("specimens", {"not": {"occurredAt": {"year": 2021}}}, ["beta"], id="not"),
        pytest.param(
            "partners",
            {"partner": {"occurredAtYearIn": {"year_In": [2021]}}},
            ["of-alpha"],
            id="nested-partner",
        ),
        pytest.param(
            "partners",
            {"partnerOccurredAt": {"year": 2020}},
            ["of-beta"],
            id="flat-partner",
        ),
    ],
)
def test_generated_year_leaf_filters_by_the_integer_sent(
    root: str,
    year_filter: dict[str, object],
    labels: list[str],
) -> None:
    """An ``Int`` year sent to a generated ``year`` leaf filters by that year."""
    _seed_year_partners()

    assert _holder_payload(root, year_filter) == {
        "data": {root: {"edges": [{"node": {"label": label}} for label in labels]}},
    }


_TRANSFORMED_NULL_TEST_TYPES_QUERY = """
query {
  year: __type(name: "GeneratedYearFilterOccurredAtYearIsnullFilterInputType") {
    inputFields { name type { name } }
  }
  date: __type(name: "GeneratedYearFilterOccurredAtDateIsnullFilterInputType") {
    inputFields { name type { name } }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.usefixtures("generated_year_schema")
def test_generated_null_test_after_a_transform_takes_a_boolean() -> None:
    """A ``year__isnull`` / ``date__isnull`` leaf takes ``Boolean``, not the transform's output.

    The value is the ``isnull`` lookup's operand, which django-filter resolves as the
    terminal lookup past the transform, never a value of ``year``'s ``Int`` or ``date``'s
    ``Date``.
    """
    payload = response_json(post_graphql(_TRANSFORMED_NULL_TEST_TYPES_QUERY, url="/graphql-test/"))

    assert payload == {
        "data": {
            "year": {"inputFields": [{"name": "year_Isnull", "type": {"name": "Boolean"}}]},
            "date": {"inputFields": [{"name": "date_Isnull", "type": {"name": "Boolean"}}]},
        },
    }


@pytest.mark.django_db
@pytest.mark.usefixtures("generated_year_schema")
@pytest.mark.parametrize("transform", ["year", "date"])
@pytest.mark.parametrize(
    ("root", "is_null", "labels"),
    [
        pytest.param("specimens", False, ["alpha", "beta"], id="column-false"),
        pytest.param("specimens", True, [], id="column-true"),
        pytest.param("partners", False, ["dated"], id="nullable-column-false"),
        pytest.param("partners", True, ["of-alpha", "of-beta"], id="nullable-column-true"),
    ],
)
def test_generated_null_test_after_a_transform_filters_as_django_does(
    transform: str,
    root: str,
    *,
    is_null: bool,
    labels: list[str],
) -> None:
    """A ``Boolean`` sent to a transformed null test filters the rows Django's own lookup does.

    ``ScalarSpecimen.occurred_at`` stores no null, so ``true`` matches nothing there;
    ``NullableScalarSpecimen``'s ``of-*`` rows store a null timestamp, which ``true``
    matches, while its ``dated`` row stores one and answers ``false``.
    """
    _seed_year_partners()
    models.NullableScalarSpecimen.objects.create(label="dated", occurred_at=_DATETIME)
    model = models.ScalarSpecimen if root == "specimens" else models.NullableScalarSpecimen
    django_rows = model.objects.filter(**{f"occurred_at__{transform}__isnull": is_null})
    year_filter = {f"occurredAt{transform.title()}Isnull": {f"{transform}_Isnull": is_null}}

    assert sorted(django_rows.values_list("label", flat=True)) == labels
    assert _holder_payload(root, year_filter) == {
        "data": {root: {"edges": [{"node": {"label": label}} for label in labels]}},
    }


_LOOKUP_EXPR_RANGE_TYPES_QUERY = """
query {
  years: __type(name: "GeneratedYearFilterOccurredAtYearRangeInputType") {
    inputFields { name type { name } }
  }
  stamps: __type(name: "GeneratedYearFilterOccurredAtRangeInputType") {
    inputFields { name type { name } }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.usefixtures("generated_year_schema")
def test_two_ranges_over_one_column_are_named_by_what_each_compares() -> None:
    """A ``year__range`` and a ``method=`` ``year__range`` over ``occurred_at`` are two types.

    Each is stemmed on its value path: ``OccurredAtYear`` with the ``year`` transform's
    ``Int`` bounds, and ``OccurredAt`` with the column's ``DateTime`` bounds for the
    ``method=`` range, whose method receives the column's values.
    """
    payload = response_json(post_graphql(_LOOKUP_EXPR_RANGE_TYPES_QUERY, url="/graphql-test/"))

    assert payload == {
        "data": {
            "years": {
                "inputFields": [
                    {"name": "start", "type": {"name": "Int"}},
                    {"name": "end", "type": {"name": "Int"}},
                ],
            },
            "stamps": {
                "inputFields": [
                    {"name": "start", "type": {"name": "DateTime"}},
                    {"name": "end", "type": {"name": "DateTime"}},
                ],
            },
        },
    }


_ALPHA_YEAR_STAMP = "2021-03-01T00:00:00+00:00"
_BETA_YEAR_STAMP = "2020-03-01T00:00:00+00:00"


@pytest.mark.django_db
@pytest.mark.usefixtures("generated_year_schema")
@pytest.mark.parametrize(
    ("year_filter", "labels"),
    [
        pytest.param({"yearsAmong": {"year_In": [2020]}}, ["beta"], id="list-in"),
        pytest.param(
            {"yearsSpan": {"year_Range": {"start": 2020, "end": 2021}}},
            ["alpha", "beta"],
            id="range",
        ),
        pytest.param({"yearsSpan": {"year_Range": {"start": 2021}}}, ["alpha"], id="range-start"),
        pytest.param({"yearsSpan": {"year_Range": {"end": 2020}}}, ["beta"], id="range-end"),
        pytest.param(
            {"yearsOfStamps": {"year_In": [_ALPHA_YEAR_STAMP]}},
            ["alpha"],
            id="method-list",
        ),
        pytest.param(
            {
                "yearSpanOfStamps": {
                    "year_Range": {"start": _BETA_YEAR_STAMP, "end": _BETA_YEAR_STAMP},
                },
            },
            ["beta"],
            id="method-range",
        ),
    ],
)
def test_lookup_expr_transform_leaf_filters_by_its_output_and_a_method_by_its_column(
    year_filter: dict[str, object],
    labels: list[str],
) -> None:
    """A transform in the ``lookup_expr`` is published and cleaned as its output; a method's not.

    ``yearsAmong`` / ``yearsSpan`` take the ``year`` transform's ``Int`` and filter by it,
    a lone bound through ``year`` too. The ``method=`` shapes keep the column's
    ``DateTime``, cleaned as one, so each datetime reaches the method.
    """
    _seed_year_partners()

    assert _holder_payload("specimens", year_filter) == {
        "data": {"specimens": {"edges": [{"node": {"label": label}} for label in sorted(labels)]}},
    }


@pytest.mark.django_db
@pytest.mark.usefixtures("generated_year_schema")
@pytest.mark.parametrize(
    ("root", "year_filter", "form_key"),
    [
        pytest.param("specimens", {"occurredAt": {"year": 0}}, "occurred_at__year", id="year-0"),
        pytest.param(
            "specimens",
            {"occurredAtYearGt": {"year_Gt": 10000}},
            "occurred_at__year__gt",
            id="gt-10000",
        ),
        pytest.param(
            "specimens",
            {"not": {"occurredAt": {"year": 10000}}},
            "not__occurred_at__year",
            id="not",
        ),
        pytest.param(
            "partners",
            {"partner": {"occurredAt": {"year": 0}}},
            "partner__occurred_at__year",
            id="nested-partner",
        ),
        pytest.param(
            "partners",
            {"partnerOccurredAt": {"year": 10000}},
            "partner__occurred_at__year",
            id="flat-partner",
        ),
    ],
)
def test_generated_year_comparison_outside_years_one_to_9999_is_filter_invalid(
    root: str,
    year_filter: dict[str, object],
    form_key: str,
) -> None:
    """An ``Int`` year whose first or last instant leaves years 1..9999 is ``FILTER_INVALID``.

    Django compares ``year`` / ``year__gt`` as a datetime bound on the column, which year 0
    and year 10000 cannot form, so the value the ``Int`` scalar accepts is refused keyed to
    its form field, flat, under ``not`` and through ``partner`` nested and flat.
    """
    _seed_year_partners()
    payload = _holder_payload(root, year_filter)

    assert payload["data"] is None, payload
    (error,) = json_list(payload, "errors")
    assert json_at(error, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {form_key: [_UNBINDABLE]},
    }


# UTC offsets PostgreSQL refuses (``time zone displacement out of range``) though the scalar
# parse and the form clean accept them: 16:00 or more either way, and, bound as text (Django's
# default psycopg cursor), an offset carrying a fraction of a second, which only the ``Time``
# scalar parses. Both ``_ALPHA_AT_*`` datetimes name alpha's instant, which SQLite binds
# projected onto UTC. Django's ``In`` drops a member equal to an earlier one, so an ``in``
# list's refused member names its own instant, an hour past alpha's.
_ALPHA_AT_PLUS_16 = "2021-06-16T01:30:00+16:00"
_ALPHA_AT_MINUS_16 = "2021-06-14T17:30:00-16:00"
_HOUR_AFTER_ALPHA_AT_PLUS_16 = "2021-06-16T02:30:00+16:00"
_BEFORE_ALPHA_AT_MINUS_23_59 = "2021-06-14T00:00:00-23:59"
_TIME_AT_PLUS_16 = "09:30:00+16:00"
_TIME_AT_HALF_SECOND_OFFSET = "09:30:00+01:00:00.500000"


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "query",
        "refused",
        "form_key",
        "sqlite_labels",
    ),
    [
        pytest.param(
            _BY_FILTER,
            {"occurredAt": {"exact": _ALPHA_AT_PLUS_16}},
            "occurred_at",
            ["alpha"],
            id="exact-plus-16",
        ),
        pytest.param(
            _BY_FILTER,
            {"occurredAt": {"gt": _BEFORE_ALPHA_AT_MINUS_23_59}},
            "occurred_at__gt",
            ["alpha"],
            id="gt-minus-23-59",
        ),
        pytest.param(
            _BY_FILTER,
            {"occurredAt": {"in": [_BINDABLE_DATETIME, _HOUR_AFTER_ALPHA_AT_PLUS_16]}},
            "occurred_at__in",
            ["alpha"],
            id="in-member",
        ),
        pytest.param(
            _BY_FILTER,
            {"occurredAt": {"range": [_BEFORE_ALPHA_AT_MINUS_23_59, _BINDABLE_DATETIME]}},
            "occurred_at__range",
            ["alpha"],
            id="range-bound",
        ),
        pytest.param(
            _BY_FILTER,
            {"not": {"occurredAt": {"exact": _ALPHA_AT_PLUS_16}}},
            "not__occurred_at",
            [],
            id="not",
        ),
        pytest.param(
            _BY_FILTER,
            {"or": [{"label": {"exact": "beta"}}, {"occurredAt": {"exact": _ALPHA_AT_MINUS_16}}]},
            "or_1__occurred_at",
            ["alpha"],
            id="or-arm",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partner": {"occurredAt": {"lte": _ALPHA_AT_PLUS_16}}},
            "partner__occurred_at__lte",
            ["of-alpha"],
            id="nested-partner",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partnerOccurredAt": {"gte": _ALPHA_AT_MINUS_16}},
            "partner__occurred_at__gte",
            ["of-alpha"],
            id="flat-partner",
        ),
        pytest.param(
            _BY_FILTER,
            {"occurredTime": {"exact": _TIME_AT_PLUS_16}},
            "occurred_time",
            None,
            id="time-plus-16",
        ),
        pytest.param(
            _BY_FILTER,
            {"occurredTime": {"in": ["09:30:00", _TIME_AT_HALF_SECOND_OFFSET]}},
            "occurred_time__in",
            None,
            id="time-half-second-offset-in-member",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partnerOccurredTime": {"exact": _TIME_AT_PLUS_16}},
            "partner__occurred_time",
            None,
            id="flat-partner-time-plus-16",
        ),
    ],
)
def test_utc_offset_postgresql_refuses_is_filter_invalid_there(
    query: str,
    refused: dict[str, object],
    form_key: str,
    sqlite_labels: list[str] | None,
) -> None:
    """A UTC offset PostgreSQL refuses is ``FILTER_INVALID`` keyed to its form field there.

    On PostgreSQL an aware datetime or time whose offset is 16:00 or more either way, or
    (bound as text, as Django's default psycopg cursor binds) carries a fraction of a
    second, is refused with the package's fixed message, for every member of an ``in``
    list and every ``range`` bound, under ``not`` and an ``or`` arm, and through the
    ``partner`` relation, nested and flat, never the driver's error. SQLite projects the
    same datetimes onto UTC and filters (``sqlite_labels``); it refuses every aware time
    (``None``).
    """
    alpha = _seed_specimen("alpha")
    models.NullableScalarSpecimen.objects.create(label="of-alpha", partner=alpha)
    root = "allScalarSpecimens" if query == _BY_FILTER else "allNullableScalarSpecimens"
    payload = response_json(post_graphql(query, variables={"filter": refused}))

    if connection.vendor != "postgresql" and sqlite_labels is not None:
        assert payload == {"data": {root: [{"label": label} for label in sqlite_labels]}}
        return
    assert payload["data"] is None, payload
    (error,) = json_list(payload, "errors")
    assert json_at(error, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {form_key: [_UNBINDABLE]},
    }


# django-filter's own range filters, each declared on ``ScalarSpecimenFilter`` with its
# low / high bound: ``priceBetween`` (``RangeWidget``: ``_min`` / ``_max``),
# ``occurredBetween`` (``DateRangeWidget``: ``_after`` / ``_before``),
# ``occurredInBoxes`` (the same filter over a plain ``MultiWidget``: ``_0`` / ``_1``) and
# ``priceInUnderscoredBoxes`` (a consumer ``SuffixedMultiWidget``: ``__low`` / ``__high``,
# keys the flat-copy scan reads as a relation path) and ``priceInFieldBoxes`` (a consumer
# ``RangeFilter`` whose ``field`` property installs a widget reading ``_low`` / ``_high``).
_UPSTREAM_RANGES = {
    "priceBetween": ("10.0000", "100.0000"),
    "occurredBetween": ("2021-03-01", "2021-12-31"),
    "occurredInBoxes": ("2021-03-01", "2021-12-31"),
    "priceInUnderscoredBoxes": ("10.0000", "100.0000"),
    "priceInFieldBoxes": ("10.0000", "100.0000"),
}
# Each range shape and the specimens it keeps (the seed puts ``mid`` alone inside both bounds).
_RANGE_SHAPES = {
    "both": (True, True, ["mid"]),
    "start": (True, False, ["mid", "dear"]),
    "end": (False, True, ["cheap", "mid"]),
    "empty": (False, False, ["cheap", "mid", "dear"]),
    "both-null": (False, False, ["cheap", "mid", "dear"]),
}
_EVERY_SPECIMEN = ["cheap", "mid", "dear"]


def _upstream_range(name: str, shape: str) -> dict[str, str | None]:
    """The ``{start, end}`` input of ``shape`` for the upstream range filter ``name``."""
    low, high = _UPSTREAM_RANGES[name]
    with_start, with_end, _ = _RANGE_SHAPES[shape]
    if shape == "both-null":
        return {"start": None, "end": None}
    return {**({"start": low} if with_start else {}), **({"end": high} if with_end else {})}


def _seed_dated_price_tiers() -> None:
    """``cheap`` / ``mid`` / ``dear`` at rising prices and dates, each with an ``of-`` partner row."""
    tiers = [
        ("cheap", Decimal("1.0000"), datetime.date(2021, 1, 1)),
        ("mid", Decimal("50.0000"), datetime.date(2021, 6, 15)),
        ("dear", Decimal("50000.0000"), datetime.date(2022, 12, 31)),
    ]
    for label, price, occurred_on in tiers:
        partner = _seed_specimen(label, price=price, occurred_on=occurred_on)
        models.NullableScalarSpecimen.objects.create(label=f"of-{label}", partner=partner)


def _upstream_range_case(
    name: str,
    shape: str,
    context: str,
) -> tuple[str, dict[str, object], dict[str, object]]:
    """The query, filter input and expected data of ``name`` in ``shape`` under ``context``."""
    bag = {"exact": _upstream_range(name, shape)}
    kept = _RANGE_SHAPES[shape][2]
    if context == "not":
        labels = [label for label in _EVERY_SPECIMEN if label not in kept] or _EVERY_SPECIMEN
        return _BY_FILTER, {"not": {name: bag}}, {"allScalarSpecimens": labels}
    if context in {"nested-partner", "flat-partner"}:
        filter_input: dict[str, object] = (
            {"partner": {name: bag}}
            if context == "nested-partner"
            else {f"partner{name[0].upper()}{name[1:]}": bag}
        )
        return (
            _BY_NULLABLE_FILTER,
            filter_input,
            {"allNullableScalarSpecimens": [f"of-{label}" for label in kept]},
        )
    filter_input = {"and": [{name: bag}]} if context == "and" else {name: bag}
    return _BY_FILTER, filter_input, {"allScalarSpecimens": kept}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "context",
    [
        "top",
        "and",
        "not",
        "nested-partner",
        "flat-partner",
    ],
)
@pytest.mark.parametrize("shape", list(_RANGE_SHAPES))
@pytest.mark.parametrize("name", list(_UPSTREAM_RANGES))
def test_upstream_range_filter_reads_the_keys_its_widget_reads(
    name: str,
    shape: str,
    context: str,
) -> None:
    """A declared django-filter range filter applies each bound it is sent.

    The range input is sent under the keys the filter's own widget reads
    (``_min`` / ``_max``, ``_after`` / ``_before``, or a plain ``MultiWidget``'s
    ``_0`` / ``_1``), so a lone ``start`` keeps the rows at or after it, a lone ``end``
    the rows at or before it, and a range with no bound filters nothing, flat, inside
    ``and`` / ``not`` and through the ``partner`` relation, nested and flat. ``not`` of
    a range that constrains nothing keeps every row. The flat ``partner`` copy of a widget
    reading a ``__`` key (``priceInUnderscoredBoxes``) is named by exactly those keys, so
    its bounds apply too. A filter whose own ``field`` installs its widget
    (``priceInFieldBoxes``) is sent under the keys that widget reads, flat copy included.
    """
    _seed_dated_price_tiers()
    query, filter_input, expected = _upstream_range_case(name, shape, context)
    ((root, labels),) = expected.items()
    payload = response_json(post_graphql(query, variables={"filter": filter_input}))

    assert payload == {"data": {root: [{"label": label} for label in json_list(labels)]}}


@pytest.mark.django_db
def test_upstream_range_filter_nan_bound_is_filter_invalid() -> None:
    """A ``NaN`` bound on django-filter's ``RangeFilter`` is its ``DecimalField``'s refusal."""
    _seed_dated_price_tiers()
    payload = response_json(
        post_graphql(
            _BY_FILTER,
            variables={"filter": {"priceBetween": {"exact": {"start": "NaN", "end": "100"}}}},
        ),
    )

    assert payload["data"] is None, payload
    (error,) = json_list(payload, "errors")
    assert json_at(error, "extensions") == {
        "code": "FILTER_INVALID",
        "errors": {"price_between": [_NOT_A_NUMBER]},
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("shape", "kept"),
    [("both", ["mid"]), ("start", ["mid", "dear"]), ("end", ["cheap", "mid"])],
)
@pytest.mark.parametrize("context", ["top", "flat-partner"])
def test_range_filter_reads_the_keys_a_mixin_field_override_installs(
    shape: str,
    kept: list[str],
    context: str,
) -> None:
    """The package's ``RangeFilter`` is sent under the keys a mixin's ``field`` installs.

    ``priceSpanInFieldBoxes`` is the package's ``RangeFilter`` followed in its MRO by a
    mixin whose ``field`` installs a widget reading ``_low`` / ``_high``. The schema reads
    the keys off the form field the rest of the filter's MRO builds, the mixin included, so
    the bounds reach the keys the bound filter's form reads, flat and through the flat
    ``partner`` copy; read off ``Filter.field`` alone they would go to ``_0`` / ``_1`` and
    filter nothing.
    """
    _seed_dated_price_tiers()
    bounds = {"start": "10.0000", "end": "100.0000"}
    bag = {"range": {key: bounds[key] for key in ("start", "end") if shape in {"both", key}}}

    if context == "top":
        query, filter_input = _BY_FILTER, {"priceSpanInFieldBoxes": bag}
        root, labels = "allScalarSpecimens", kept
    else:
        query, filter_input = _BY_NULLABLE_FILTER, {"partnerPriceSpanInFieldBoxes": bag}
        root, labels = "allNullableScalarSpecimens", [f"of-{label}" for label in kept]
    payload = response_json(post_graphql(query, variables={"filter": filter_input}))

    assert payload == {"data": {root: [{"label": label} for label in labels]}}


_ALL_INPUT_FIELDS_QUERY = """
query {
  __schema { types { name inputFields { name } } }
  id: __type(name: "ScalarSpecimenFilterIdFilterInputType") { inputFields { name } }
}
"""


@pytest.mark.django_db
def test_all_lookup_leaves_publish_no_contrib_postgres_lookup() -> None:
    """No input type publishes ``containedBy``, and sending it is a validation error.

    ``django.contrib.postgres``'s range module (imported whenever a driver is
    installed) registers ``contained_by`` onto the core integer, decimal, date
    and datetime fields; fakeshop declares no PostgreSQL field, so no input type
    may carry it. The ``id`` leaf keeps its ordinary ``"__all__"`` lookups.
    """
    data = _assert_graphql_success(_ALL_INPUT_FIELDS_QUERY)

    carriers = [
        json_at(type_, "name")
        for type_ in json_list(data, "__schema", "types")
        if json_at(type_, "inputFields") is not None
        and any(
            json_at(field, "name") == "containedBy" for field in json_list(type_, "inputFields")
        )
    ]
    assert carriers == []
    id_lookups = {json_at(field, "name") for field in json_list(data, "id", "inputFields")}
    assert {
        "exact",
        "in",
        "gt",
        "range",
        "isNull",
    } <= id_lookups

    payload = response_json(
        post_graphql("query { allScalarSpecimens(filter: { id: { containedBy: 5 } }) { label } }"),
    )
    assert payload["data"] is None, payload
    assert (
        "Field 'containedBy' is not defined by type 'ScalarSpecimenFilterIdFilterInputType'."
        in json_str(
            payload,
            "errors",
            0,
            "message",
        )
    ), payload


_BY_PARENT = """
query ($filter: ScalarSpecimenFilterInputType) {
  allScalarSpecimens(filter: $filter, orderBy: [{ label: ASC }]) {
    label
  }
}
"""


@pytest.mark.django_db
@pytest.mark.parametrize("lookup", ["exact", "in", "isNull"], ids=["exact", "in", "is-null"])
def test_scalars_filter_by_forward_fk_primary_key_exact_and_in(lookup: str) -> None:
    """``parent`` takes one raw pk for ``exact`` and a list for ``in``; ``isNull`` stays Boolean."""
    root_a = _seed_specimen("root-a")
    root_b = _seed_specimen("root-b")
    _seed_specimen("child-a", parent=root_a)
    _seed_specimen("child-b", parent=root_b)

    cases = {
        "exact": ({"parent": {"exact": root_a.pk}}, ["child-a"]),
        "in": ({"parent": {"in": [root_a.pk, root_b.pk]}}, ["child-a", "child-b"]),
        "isNull": ({"parent": {"isNull": True}}, ["root-a", "root-b"]),
    }
    filter_input, labels = cases[lookup]
    _assert_graphql_data(
        _BY_PARENT,
        {"allScalarSpecimens": [{"label": label} for label in labels]},
        variables={"filter": filter_input},
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case",
    [
        "missing-exact",
        "missing-in",
        "mixed-in",
        "empty-in",
    ],
    ids=[
        "missing-exact",
        "missing-in",
        "mixed-in",
        "empty-in",
    ],
)
def test_scalars_forward_fk_primary_key_follows_the_membership_rules(case: str) -> None:
    """A missing pk matches nothing, beside a real one it is dropped, and ``in: []`` is empty.

    None of these is a validation error: the relation key never checks that the target
    row exists, so a missing pk and one the caller cannot see answer alike.
    """
    root = _seed_specimen("root")
    _seed_specimen("child", parent=root)
    root_pk = root.pk
    assert root_pk is not None
    missing = root_pk + 1000

    cases: dict[str, tuple[dict[str, object], list[str]]] = {
        "missing-exact": ({"parent": {"exact": missing}}, []),
        "missing-in": ({"parent": {"in": [missing]}}, []),
        "mixed-in": ({"parent": {"in": [missing, root_pk]}}, ["child"]),
        "empty-in": ({"parent": {"in": []}}, []),
    }
    filter_input, labels = cases[case]
    _assert_graphql_data(
        _BY_PARENT,
        {"allScalarSpecimens": [{"label": label} for label in labels]},
        variables={"filter": filter_input},
    )


@pytest.mark.django_db
def test_scalars_filter_by_reverse_fk_primary_keys() -> None:
    """``children`` (the reverse FK) takes a list of raw child pks."""
    root_a = _seed_specimen("root-a")
    root_b = _seed_specimen("root-b")
    child_a = _seed_specimen("child-a", parent=root_a)
    child_b = _seed_specimen("child-b", parent=root_b)
    _seed_specimen("child-a2", parent=root_a)

    _assert_graphql_data(
        _BY_PARENT,
        {"allScalarSpecimens": [{"label": "root-a"}, {"label": "root-b"}]},
        variables={"filter": {"children": {"exact": [child_a.pk, child_b.pk]}}},
    )


_TEXT_PATTERN_LEAVES = frozenset(
    {
        "iExact",
        "contains",
        "iContains",
        "startsWith",
        "iStartsWith",
        "endsWith",
        "iEndsWith",
        "regex",
        "iRegex",
    },
)

_LEAF_TYPES_QUERY = """
query ($name: String!) {
  __type(name: $name) { inputFields { name type { name } } }
}
"""


def _leaf_types(type_name: str) -> dict[str, object]:
    """Map each input field of ``type_name`` to its named GraphQL type."""
    data = _assert_graphql_success(_LEAF_TYPES_QUERY, variables={"name": type_name})
    return {
        json_str(field, "name"): json_at(field, "type", "name")
        for field in json_list(data, "__type", "inputFields")
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "type_name",
    [
        "ScalarSpecimenFilterOccurredAtFilterInputType",
        "ScalarSpecimenFilterOccurredOnFilterInputType",
        "ScalarSpecimenFilterOccurredTimeFilterInputType",
        "ScalarSpecimenFilterPriceFilterInputType",
        "ScalarSpecimenFilterScoreFilterInputType",
        "ScalarSpecimenFilterFlagFilterInputType",
        "ScalarSpecimenFilterExternalIdFilterInputType",
        "ScalarSpecimenFilterSignedBigFilterInputType",
        "ScalarSpecimenFilterIdFilterInputType",
    ],
)
def test_all_lookups_on_a_non_text_column_publish_no_text_pattern_leaf(type_name: str) -> None:
    """A per-field ``"__all__"`` on a non-text column keeps ``exact`` and drops every text pattern.

    Django matches a text-pattern lookup against the column's text rendering, which an
    input typed by the column cannot express, so only a text column publishes them.
    """
    leaves = set(_leaf_types(type_name))

    assert {"exact", "in", "isNull"} <= leaves
    assert leaves.isdisjoint(_TEXT_PATTERN_LEAVES)


@pytest.mark.django_db
def test_all_lookups_on_a_text_column_keep_every_text_pattern_leaf() -> None:
    """``label`` (a ``TextField``) keeps every text-pattern leaf, each a ``String``."""
    leaf_types = _leaf_types("ScalarSpecimenFilterLabelFilterInputType")

    assert {name: leaf_types[name] for name in _TEXT_PATTERN_LEAVES} == dict.fromkeys(
        _TEXT_PATTERN_LEAVES,
        "String",
    )


@pytest.mark.django_db
def test_instance_registered_lookup_is_a_leaf_of_its_own_field_only() -> None:
    """``prefix``, registered on ``ScalarSpecimen.label`` alone, is a leaf of that set only.

    ``ScalarSpecimenTag.label`` is a ``TextField`` too; its ``"__all__"`` reads its own
    field's registry, which holds no ``prefix``.
    """
    specimen_leaves = _leaf_types("ScalarSpecimenFilterLabelFilterInputType")
    tag_leaves = _leaf_types("ScalarSpecimenTagFilterLabelFilterInputType")

    assert specimen_leaves["prefix"] == "String"
    assert "prefix" not in tag_leaves
    assert {"exact", "iStartsWith"} <= set(tag_leaves)


@pytest.mark.django_db
def test_instance_registered_lookup_filters_by_its_own_comparison() -> None:
    """``label: { prefix }`` keeps the labels starting with the value, in any case."""
    _seed_specimen("alpha")
    _seed_specimen("Alder")
    _seed_specimen("beta")
    data = _assert_graphql_success(
        'query { allScalarSpecimens(filter: { label: { prefix: "al" } }) { label } }',
    )

    labels = [json_str(row, "label") for row in json_list(data, "allScalarSpecimens")]
    assert sorted(labels) == ["Alder", "alpha"], labels


@pytest.mark.django_db
def test_explicit_text_pattern_leaf_on_a_non_text_column_is_a_string() -> None:
    """An explicitly listed pattern lookup on a datetime or integer column is a ``String`` leaf."""
    occurred_at = _leaf_types("NullableScalarSpecimenFilterOccurredAtFilterInputType")
    unsigned_big = _leaf_types("NullableScalarSpecimenFilterUnsignedBigFilterInputType")

    assert occurred_at == {
        "exact": "DateTime",
        "iExact": "String",
        "iContains": "String",
        "startsWith": "String",
        "regex": "String",
        "iRegex": "String",
    }
    assert unsigned_big == {"exact": "BigInt", "contains": "String"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("leaf", "sqlite_value", "postgresql_value"),
    [
        pytest.param("iExact", "2021-06-15 09:30:00", "2021-06-15 09:30:00+00", id="iexact"),
        pytest.param("iContains", "2021-06", "2021-06", id="icontains"),
        pytest.param("startsWith", "2021-06-15 09", "2021-06-15 09", id="startswith"),
        pytest.param("regex", "^2021-06-15 09:30", "^2021-06-15 09:30", id="regex"),
        pytest.param("iRegex", "^2021-06-15 09:30", "^2021-06-15 09:30", id="iregex"),
    ],
)
def test_explicit_datetime_text_pattern_matches_the_backend_text_rendering(
    leaf: str,
    sqlite_value: str,
    postgresql_value: str,
) -> None:
    """A partial pattern on a datetime column matches the row whose text rendering it matches.

    The pattern runs against the backend's text rendering of the stored value, as
    Django's ORM compares it: SQLite stores ``2021-06-15 09:30:00`` (UTC), PostgreSQL
    renders the ``timestamptz`` as ``2021-06-15 09:30:00+00`` in the connection's UTC.
    """
    models.NullableScalarSpecimen.objects.create(
        label="june",
        occurred_at=datetime.datetime(2021, 6, 15, 9, 30, tzinfo=datetime.timezone.utc),
    )
    models.NullableScalarSpecimen.objects.create(
        label="march",
        occurred_at=datetime.datetime(2022, 3, 1, 18, 0, tzinfo=datetime.timezone.utc),
    )
    value = postgresql_value if connection.vendor == "postgresql" else sqlite_value

    _assert_graphql_data(
        _BY_NULLABLE_FILTER,
        {"allNullableScalarSpecimens": [{"label": "june"}]},
        variables={"filter": {"occurredAt": {leaf: value}}},
    )


@pytest.mark.django_db
def test_explicit_integer_contains_matches_the_digits() -> None:
    """``unsignedBig: { contains }`` takes a digit string and matches the column's decimal text."""
    models.NullableScalarSpecimen.objects.create(label="hit", unsigned_big=1234)
    models.NullableScalarSpecimen.objects.create(label="miss", unsigned_big=5678)

    _assert_graphql_data(
        _BY_NULLABLE_FILTER,
        {"allNullableScalarSpecimens": [{"label": "hit"}]},
        variables={"filter": {"unsignedBig": {"contains": "23"}}},
    )
