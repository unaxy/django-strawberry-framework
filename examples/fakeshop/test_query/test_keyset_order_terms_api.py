"""Live keyset ordering over consumer visibility hooks and a multi-column ForeignObject.

A holder isolates a Periodical type with and without a row-hiding hook, so the
same flat/nested order input proves nullable-value refusal and identity-hook
acceptance. The shipped Periodical type cannot switch its visibility contract
within one request, so these consumer declarations run on the test mount.

For the accepted ForeignObject carrier order, the shipped ShelfLabel link has a
relation carrier and a hiding Shelf target. The existing LnkPairChild fixture
supplies two non-null scalar carriers instead, with the same real Django query,
connection pipeline and HTTP view. Its fixture table lifecycle remains explicit.

A consumer ``get_queryset`` order is the page's effective order too: a JSON
column and a related path through an optional or multivalued relation are
refused by name, as is an annotation alias, beside controls ordering
the same holders by a scalar column.
"""

import datetime
import uuid
from collections.abc import Mapping
from functools import wraps

import pytest
import strawberry
from apps.library.models import Issue, MembershipCard, Patron, Periodical
from apps.scalars.models import ScalarSpecimen
from django.db import connection
from django.db.models import Count, Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_at, json_list, json_object, json_str
from strategy_schemas import make_django_type

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.orders import OrderSet, RelatedOrder
from django_strawberry_framework.views import DjangoGraphQLView
from tests.optimizer._link_models import LnkPairChild, link_fixture_tables

pytestmark = pytest.mark.usefixtures("private_registry")

_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-keyset-order/", _graphql_view)]


def _post(
    schema: DjangoSchema,
    query: str,
    *,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(query, variables=variables, url="/graphql-keyset-order/")
    finally:
        _CURRENT["schema"] = None


def _names(page: JSONObject) -> list[str]:
    return [json_str(edge, "node", "name") for edge in json_list(page, "edges")]


@pytest.mark.django_db
@pytest.mark.parametrize("spelling", ["flat", "nested"])
@pytest.mark.parametrize("hides", [True, False], ids=["hiding-target", "identity-target"])
def test_related_keyset_order_respects_the_target_visibility_contract(
    *,
    hides: bool,
    spelling: str,
) -> None:
    """Flat and nested related order reject hiding targets and seek by both accepted terms."""
    public = Periodical.objects.create(name="public")
    secret = Periodical.objects.create(name="secret")
    Issue.objects.create(periodical=public, number=1, title="Public early issue")
    Issue.objects.create(periodical=public, number=3, title="Public later issue")
    Issue.objects.create(periodical=secret, number=2, title="Hidden issue")

    attrs: dict[str, object] = {}
    if hides:

        def _hide_secret(
            _cls: type[DjangoType],
            queryset: QuerySet[Periodical],
            _info: object,
            **_kwargs: object,
        ) -> QuerySet[Periodical]:
            return queryset.exclude(name="secret")

        attrs["get_queryset"] = classmethod(_hide_secret)
    make_django_type("OrderedPeriodicalNode", Periodical, ("id", "name"), namespace_extra=attrs)

    class PeriodicalNameOrder(OrderSet):
        class Meta:
            model = Periodical
            fields = ["name"]

    class IssuePeriodicalOrder(OrderSet):
        periodical = RelatedOrder(PeriodicalNameOrder, field_name="periodical")

        class Meta:
            model = Issue
            fields = ["number", "periodical__name"]

    issue_type = make_django_type(
        "RelatedOrderedIssueNode",
        Issue,
        ("id", "number", "title"),
        meta_extra={"cursor_field": ("-number", "id"), "orderset_class": IssuePeriodicalOrder},
    )
    finalize_django_types()

    @strawberry.type
    class Query:
        issues = DjangoConnectionField(issue_type)

    schema = DjangoSchema(query=Query, config=strawberry_config())
    term = "periodicalName: ASC" if spelling == "flat" else "periodical: { name: ASC }"
    query = (
        "query ($after: String) { issues(first: 1, after: $after, orderBy: [{ "
        + term
        + " }, { number: DESC }]) { edges { node { title } } "
        + "pageInfo { hasNextPage endCursor } } }"
    )
    payload = _post(schema, query)
    if hides:
        assert payload["data"] is None, payload
        assert len(json_list(payload, "errors")) == 1
        assert json_at(payload, "errors", 0, "path") == ["issues"]
        assert json_str(payload, "errors", 0, "message") == (
            "This connection uses keyset cursors (Meta.cursor_field), which require "
            "non-nullable ordering columns; 'periodical__name' is nullable: it is read "
            "through a relation whose type hides rows, and a hidden related row orders "
            "as missing. Order by a non-nullable column or paginate under the default order."
        )
        return
    assert "errors" not in payload, payload
    first = json_object(payload, "data", "issues")
    assert json_at(first, "edges") == [{"node": {"title": "Public later issue"}}]
    assert json_at(first, "pageInfo", "hasNextPage") is True
    after = json_str(first, "pageInfo", "endCursor")
    payload = _post(schema, query, variables={"after": after})
    assert "errors" not in payload, payload
    second = json_object(payload, "data", "issues")
    assert json_at(second, "edges") == [{"node": {"title": "Public early issue"}}]
    assert json_at(second, "pageInfo", "hasNextPage") is True
    payload = _post(
        schema,
        query,
        variables={"after": json_str(second, "pageInfo", "endCursor")},
    )
    assert "errors" not in payload, payload
    third = json_object(payload, "data", "issues")
    assert json_at(third, "edges") == [{"node": {"title": "Hidden issue"}}]
    assert json_at(third, "pageInfo", "hasNextPage") is False


_PAIR_PAGE = """
query ($after: String) {
  children(first: 2, after: $after, orderBy: [{ parent: ASC }]) {
    edges { node { name } }
    pageInfo { hasNextPage hasPreviousPage endCursor }
  }
}
"""


@pytest.mark.django_db(transaction=True)
def test_foreign_object_keyset_order_seeks_over_all_scalar_carriers() -> None:
    """A carrier-sensitive wire order and seek include both columns and reject another vocabulary."""

    class PairOrder(OrderSet):
        class Meta:
            model = LnkPairChild
            fields = ["parent", "name"]

    pair_type = make_django_type(
        "OrderedPairNode",
        LnkPairChild,
        ("id", "name"),
        meta_extra={"cursor_field": ("id",), "orderset_class": PairOrder},
    )
    finalize_django_types()

    @strawberry.type
    class Query:
        children = DjangoConnectionField(pair_type)

    schema = DjangoSchema(query=Query, config=strawberry_config())
    with link_fixture_tables(connection):
        # Move the lower-pk a2 behind a3 by the second carrier. Both (1, A)
        # and (1, B) parents exist, so only the carrier order distinguishes them.
        assert LnkPairChild.objects.filter(name="a2").update(p_code="B") == 1
        LnkPairChild.objects.create(p_tenant=0, p_code="Z", name="z9")
        first_payload = _post(schema, _PAIR_PAGE)
        assert "errors" not in first_payload, first_payload
        first = json_object(first_payload, "data", "children")
        assert _names(first) == ["z9", "a1"]
        assert json_at(first, "pageInfo", "hasNextPage") is True
        assert json_at(first, "pageInfo", "hasPreviousPage") is False
        cursor = json_str(first, "pageInfo", "endCursor")

        with CaptureQueriesContext(connection) as captured:
            second_payload = _post(schema, _PAIR_PAGE, variables={"after": cursor})
        assert "errors" not in second_payload, second_payload
        second = json_object(second_payload, "data", "children")
        assert _names(second) == ["a3", "a2"]
        assert json_at(second, "pageInfo", "hasNextPage") is True
        assert json_at(second, "pageInfo", "hasPreviousPage") is True
        (seek,) = [
            entry["sql"]
            for entry in captured.captured_queries
            if 'FROM "products_lnkpairchild"' in entry["sql"]
        ]
        where = seek.split(" WHERE ", 1)[1].split(" ORDER BY ", 1)[0]
        assert '"p_tenant"' in where, seek
        assert '"p_code"' in where, seek

        third_payload = _post(
            schema,
            _PAIR_PAGE,
            variables={"after": json_str(second, "pageInfo", "endCursor")},
        )
        assert "errors" not in third_payload, third_payload
        third = json_object(third_payload, "data", "children")
        assert _names(third) == ["b1"]
        assert json_at(third, "pageInfo", "hasNextPage") is False
        assert json_at(third, "pageInfo", "hasPreviousPage") is True

        replayed = _post(
            schema,
            _PAIR_PAGE.replace("parent: ASC", "name: ASC"),
            variables={"after": cursor},
        )
        assert replayed["data"] is None, replayed
        assert len(json_list(replayed, "errors")) == 1
        assert json_at(replayed, "errors", 0, "path") == ["children"]
        assert json_str(replayed, "errors", 0, "message") == (
            "Argument 'after' contains an invalid cursor for this connection."
        )


def _hook_ordered_keyset_schema(
    model: type[Model],
    fields: tuple[str, ...],
    hook_order: tuple[str, ...],
    *,
    annotations: Mapping[str, Count] | None = None,
) -> DjangoSchema:
    """A keyset connection (``cursor_field = ("id",)``) whose ``get_queryset`` orders by ``hook_order``.

    The hook's order is the page's effective order, so the cursor vocabulary is
    derived from it entry by entry. ``annotations`` are applied first, so an entry
    may name one of their aliases.
    """

    def _ordered(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[Model]:
        return queryset.annotate(**(annotations or {})).order_by(*hook_order)

    node_type = make_django_type(
        "HookOrderedNode",
        model,
        fields,
        meta_extra={"cursor_field": ("id",)},
        namespace_extra={"get_queryset": classmethod(_ordered)},
    )
    finalize_django_types()

    @strawberry.type
    class Query:
        rows = DjangoConnectionField(node_type)

    return DjangoSchema(query=Query, config=strawberry_config())


_JSON_ORDER_REFUSAL = (
    "This connection uses keyset cursors (Meta.cursor_field), which require portable "
    "ordering semantics; 'payload' is a JSONField, whose ordering differs between database "
    "backends. Order by a scalar column or paginate under the default order."
)


def _seed_two_specimens() -> None:
    """Two specimens whose ``label`` order is the reverse of their pk order."""
    for index, label in enumerate(("alpha", "bravo")):
        ScalarSpecimen.objects.create(
            label=label,
            occurred_on=datetime.date(2024, 1, 1),
            occurred_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
            occurred_time=datetime.time(8),
            payload={"rank": index},
            external_id=uuid.UUID(int=index + 1),
        )


@pytest.mark.django_db
def test_keyset_hook_order_by_a_json_column_is_refused() -> None:
    """A JSON column cannot anchor a keyset cursor: its ordering differs between backends.

    The refusal names the column and the request has no page, rather than one
    whose cursors would seek differently on another database.
    """
    _seed_two_specimens()
    payload = _post(
        _hook_ordered_keyset_schema(ScalarSpecimen, ("id", "label"), ("payload", "id")),
        "{ rows(first: 1) { edges { node { label } } } }",
    )
    assert payload["data"] is None, payload
    assert [
        (json_at(error, "message"), json_at(error, "path"))
        for error in json_list(payload, "errors")
    ] == [(_JSON_ORDER_REFUSAL, ["rows"])]


@pytest.mark.django_db
def test_keyset_hook_order_by_a_scalar_column_of_the_same_model_pages() -> None:
    """The control: the same holder ordered by the scalar ``label`` pages both rows by cursor.

    The hook orders by ``-label``, against pk order, so the cursor seeks under the
    hook's own column.
    """
    _seed_two_specimens()
    schema = _hook_ordered_keyset_schema(ScalarSpecimen, ("id", "label"), ("-label", "id"))
    query = (
        "query ($after: String) { rows(first: 1, after: $after) "
        "{ edges { node { label } } pageInfo { hasNextPage endCursor } } }"
    )
    first = _post(schema, query)
    assert "errors" not in first, first
    page = json_object(first, "data", "rows")
    assert json_at(page, "edges") == [{"node": {"label": "bravo"}}]
    assert json_at(page, "pageInfo", "hasNextPage") is True
    second = _post(schema, query, variables={"after": json_str(page, "pageInfo", "endCursor")})
    assert "errors" not in second, second
    page = json_object(second, "data", "rows")
    assert json_at(page, "edges") == [{"node": {"label": "alpha"}}]
    assert json_at(page, "pageInfo", "hasNextPage") is False


_UNANCHORED_ORDER_REFUSAL = (
    "This connection uses keyset cursors (Meta.cursor_field), which require every ordering "
    "entry to be a database column; the requested order cannot anchor stable cursors. Remove "
    "the unsupported orderBy entry or paginate under the default order."
)


def _seed_patrons_with_one_card() -> None:
    ada = Patron.objects.create(name="Ada")
    Patron.objects.create(name="Grace")
    MembershipCard.objects.create(patron=ada, barcode="CARD-1")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "hook_order",
    [("card__barcode", "id"), ("loans__note", "id")],
    ids=["optional-reverse-one-to-one", "multivalued-reverse-fk"],
)
def test_keyset_hook_order_through_an_optional_or_multivalued_relation_is_refused(
    hook_order: tuple[str, ...],
) -> None:
    """A related order path a value cursor cannot anchor is refused, not paged wrongly.

    ``card__barcode`` crosses a reverse one-to-one a patron may lack (a missing
    card orders as NULL), and ``loans__note`` crosses a reverse FK that repeats
    the patron once per loan; neither yields one stable value per row.
    """
    _seed_patrons_with_one_card()
    payload = _post(
        _hook_ordered_keyset_schema(Patron, ("id", "name"), hook_order),
        "{ rows(first: 1) { edges { node { name } } } }",
    )
    assert payload["data"] is None, payload
    assert [
        (json_at(error, "message"), json_at(error, "path"))
        for error in json_list(payload, "errors")
    ] == [(_UNANCHORED_ORDER_REFUSAL, ["rows"])]


@pytest.mark.django_db
def test_keyset_hook_order_by_an_annotation_alias_is_refused() -> None:
    """An annotation alias names no model column, so a value cursor cannot anchor it.

    The hook annotates ``loan_count`` and orders by it; the alias resolves to no
    field on the model and is refused by the same message as any other expression
    order.
    """
    _seed_patrons_with_one_card()
    payload = _post(
        _hook_ordered_keyset_schema(
            Patron,
            ("id", "name"),
            ("loan_count", "id"),
            annotations={"loan_count": Count("loans")},
        ),
        "{ rows(first: 1) { edges { node { name } } } }",
    )
    assert payload["data"] is None, payload
    assert [
        (json_at(error, "message"), json_at(error, "path"))
        for error in json_list(payload, "errors")
    ] == [(_UNANCHORED_ORDER_REFUSAL, ["rows"])]


@pytest.mark.django_db
def test_keyset_hook_order_by_the_patrons_own_column_pages() -> None:
    """The control: the same holder ordered by the patron's own ``name`` pages both rows."""
    _seed_patrons_with_one_card()
    query = (
        "query ($after: String) { rows(first: 1, after: $after) "
        "{ edges { node { name } } pageInfo { hasNextPage endCursor } } }"
    )
    schema = _hook_ordered_keyset_schema(Patron, ("id", "name"), ("-name", "id"))
    first = _post(schema, query)
    assert "errors" not in first, first
    assert _names(json_object(first, "data", "rows")) == ["Grace"]
    second = _post(
        schema,
        query,
        variables={"after": json_str(first, "data", "rows", "pageInfo", "endCursor")},
    )
    assert "errors" not in second, second
    assert _names(json_object(second, "data", "rows")) == ["Ada"]
