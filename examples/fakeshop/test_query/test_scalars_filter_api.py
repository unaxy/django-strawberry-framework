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
``start`` / ``end`` applies as ``gte`` / ``lte`` and a range with no bound filters nothing.
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
