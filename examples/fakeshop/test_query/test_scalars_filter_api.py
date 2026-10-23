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
same column whose elements are cleaned the same way. django-filter's own range filters
(``priceBetween``, ``occurredBetween`` over ``DateRangeWidget``, ``occurredInBoxes`` over a
plain ``MultiWidget`` and ``priceInUnderscoredBoxes`` over a consumer widget reading ``__``
keys) apply every bound they are sent, under the keys each widget reads.
The per-field ``"__all__"`` leaves never publish a ``django.contrib.postgres``
lookup Django registers onto a core field (``containedBy`` on the numeric and
temporal leaves), whether or not a PostgreSQL driver is installed.
"""

import datetime
import uuid
from decimal import Decimal

import pytest
from apps.scalars import models
from graphql_client import assert_graphql_data as _assert_graphql_data
from graphql_client import assert_graphql_success as _assert_graphql_success
from graphql_client import json_at, json_list, json_object, post_graphql, response_json

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
    """Text-scalar filter input (``label: { iContains }``)."""
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
    """Boolean-scalar filter input (``flag: { exact: true }``)."""
    _seed_specimen("alpha", flag=True)
    _seed_specimen("beta", flag=False)
    _seed_specimen("gamma", flag=True)
    _assert_graphql_data(
        """
        query {
          allScalarSpecimens(filter: { flag: { exact: true } }) {
            label
          }
        }
        """,
        {"allScalarSpecimens": [{"label": "alpha"}, {"label": "gamma"}]},
    )


@pytest.mark.django_db
def test_scalars_filter_by_non_relay_pk_in_list() -> None:
    """Non-Relay ``id: { in: [...] }`` resolves to the integer CSV path (H5c).

    The scalar types are not Relay nodes, so ``id`` is a plain integer column.
    Its ``in`` lookup routes through the framework's ``IntegerInFilter`` (a
    ``BaseInFilter`` subclass that also drops out-of-range members and matches
    nothing on a fully-dropped non-empty list) and converts to a ``list[Int]``
    CSV input rather than the own-PK ``GlobalIDMultipleChoiceFilter`` the Relay
    apps use. This pins the non-Relay counterpart of that fix end to end.
    """
    alpha = _seed_specimen("alpha")
    _seed_specimen("beta")
    gamma = _seed_specimen("gamma")
    _assert_graphql_data(
        f"""
        query {{
          allScalarSpecimens(filter: {{ id: {{ in: [{alpha.pk}, {gamma.pk}] }} }}) {{
            label
          }}
        }}
        """,
        {"allScalarSpecimens": [{"label": "alpha"}, {"label": "gamma"}]},
    )


@pytest.mark.django_db
def test_scalars_filter_by_related_tag_label() -> None:
    """``RelatedFilter`` onto ``ScalarSpecimenTag`` (whose ``get_queryset`` is active=True)."""
    hot = models.ScalarSpecimenTag.objects.create(label="hot", active=True)
    _seed_specimen("alpha", tag=hot)
    _seed_specimen("beta")
    _assert_graphql_data(
        """
        query {
          allScalarSpecimens(filter: { tag: { label: { exact: "hot" } } }) {
            label
          }
        }
        """,
        {"allScalarSpecimens": [{"label": "alpha"}]},
    )


@pytest.mark.django_db
def test_scalars_order_by_label_desc() -> None:
    """``orderBy: [{ label: DESC }]`` sorts specimens by label descending (DONE-028 wiring)."""
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
  allScalarSpecimens(filter: $filter) {
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
            "price_span",
            id="not",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partner": {"priceSpan": {"range": {"end": "NaN"}}}},
            "price_span",
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
            "price_among",
            _NOT_A_NUMBER,
            id="not",
        ),
        pytest.param(
            _BY_NULLABLE_FILTER,
            {"partner": {"priceAmong": {"in": ["NaN"]}}},
            "price_among",
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


# django-filter's own range filters, each declared on ``ScalarSpecimenFilter`` with its
# low / high bound: ``priceBetween`` (``RangeWidget``: ``_min`` / ``_max``),
# ``occurredBetween`` (``DateRangeWidget``: ``_after`` / ``_before``),
# ``occurredInBoxes`` (the same filter over a plain ``MultiWidget``: ``_0`` / ``_1``) and
# ``priceInUnderscoredBoxes`` (a consumer ``SuffixedMultiWidget``: ``__low`` / ``__high``,
# keys the flat-copy scan reads as a relation path).
_UPSTREAM_RANGES = {
    "priceBetween": ("10.0000", "100.0000"),
    "occurredBetween": ("2021-03-01", "2021-12-31"),
    "occurredInBoxes": ("2021-03-01", "2021-12-31"),
    "priceInUnderscoredBoxes": ("10.0000", "100.0000"),
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
    reading a ``__`` key (``priceInUnderscoredBoxes``) is copied by every request, so its
    bounds apply too.
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
    assert "data" not in payload or payload["data"] is None, payload
    assert "containedBy" in str(payload["errors"]), payload


_BY_PARENT = """
query ($filter: ScalarSpecimenFilterInputType) {
  allScalarSpecimens(filter: $filter) {
    label
  }
}
"""


@pytest.mark.django_db
def test_scalars_filter_by_forward_fk_primary_key_exact_and_in() -> None:
    """``parent`` takes one raw pk for ``exact`` and a list for ``in``; ``isNull`` stays Boolean."""
    root_a = _seed_specimen("root-a")
    root_b = _seed_specimen("root-b")
    _seed_specimen("child-a", parent=root_a)
    _seed_specimen("child-b", parent=root_b)

    for filter_input, labels in (
        ({"parent": {"exact": root_a.pk}}, ["child-a"]),
        ({"parent": {"in": [root_a.pk, root_b.pk]}}, ["child-a", "child-b"]),
        ({"parent": {"isNull": True}}, ["root-a", "root-b"]),
    ):
        _assert_graphql_data(
            _BY_PARENT,
            {"allScalarSpecimens": [{"label": label} for label in labels]},
            variables={"filter": filter_input},
        )


@pytest.mark.django_db
def test_scalars_forward_fk_primary_key_follows_the_membership_rules() -> None:
    """A missing pk matches nothing, beside a real one it is dropped, and ``in: []`` is empty.

    None of these is a validation error: the relation key never checks that the target
    row exists, so a missing pk and one the caller cannot see answer alike.
    """
    root = _seed_specimen("root")
    _seed_specimen("child", parent=root)
    root_pk = root.pk
    assert root_pk is not None
    missing = root_pk + 1000

    cases: tuple[tuple[dict[str, dict[str, int | list[int]]], list[str]], ...] = (
        ({"parent": {"exact": missing}}, []),
        ({"parent": {"in": [missing]}}, []),
        ({"parent": {"in": [missing, root_pk]}}, ["child"]),
        ({"parent": {"in": []}}, []),
    )
    for filter_input, labels in cases:
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
