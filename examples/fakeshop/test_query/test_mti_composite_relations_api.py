"""Native HTTP relation verdicts needing MTI-forward-M2M or composite-key parents.

The shipped Venue chain inherits a reverse M2M. Django's ancestor-prefetch
behavior requires a forward M2M on an MTI parent, so these requests use real
function-local models and temporary tables through the shared fixture builder.
A holder preserves that consumer declaration without changing the shipped Venue
contract. Both visibility-hook and identity-hook verdicts use the native view.

The composite-parent request reuses the existing Rp fixture: its explicit scalar
NodeID lets the consumer publish a composite-PK parent, while the reverse
ForeignObject has two carriers and cannot use one-column window partitioning.
The shipped ShelfLabel shape has a scalar-PK parent and cannot pin that projection.
"""

from functools import wraps

import django
import pytest
import strawberry
from asgiref.sync import sync_to_async
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, RecordCompiledSql, graphql_payload, response_json
from strawberry import relay
from strawberry.relay import NodeID

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._mti_relations import (
    create_mti_tag_tables,
    declare_mti_tag_models,
    drop_mti_tag_tables,
    mti_tag_schema,
    seed_mti_tags,
)
from tests._relation_fixtures import RpCompositeChild, RpCompositeParent, relation_fixture_tables

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
    path("graphql-mti-composite/", _graphql_view),
    path("graphql-mti-composite-async/", _async_graphql_view),
]


def _post(schema: DjangoSchema, document: str) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(document, url="/graphql-mti-composite/")
    finally:
        _CURRENT["schema"] = None


async def _post_async(schema: DjangoSchema, document: str) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            result = await AsyncTestClient().query(
                document,
                assert_no_errors=False,
                url="/graphql-mti-composite-async/",
            )
        assert result.response.status_code == 200
        return response_json(result.response)
    finally:
        _CURRENT["schema"] = None


def _selects_from(statements: list[str], table: str) -> list[str]:
    """Match the statement's first FROM, excluding JOIN/subquery mentions of a table."""
    return [
        sql
        for sql in statements
        if " FROM " in sql and sql.split(" FROM ", 1)[1].startswith(f'"{table}"')
    ]


def _expected_shops(first_shop_tags: list[str]) -> JSONObject:
    return {
        "data": {
            "shops": [
                {"name": "One", "tags": [{"name": name} for name in first_shop_tags]},
                {"name": "Two", "tags": [{"name": "Beta"}]},
            ],
        },
    }


def _assert_mti_cost(statements: list[str], *, tag_reads: int) -> None:
    assert len(_selects_from(statements, "resolvers_mti_place")) == 1, statements
    assert len(_selects_from(statements, "resolvers_mti_shop")) == 2, statements
    assert len(_selects_from(statements, "resolvers_mti_tag")) == tag_reads, statements
    assert all("COUNT(" not in sql.upper() for sql in statements), statements


_MTI_TAGS_QUERY = "{ shops { name tags { name } } }"


@pytest.mark.parametrize(
    ("hide_prefix", "first_shop_tags"),
    [
        pytest.param(None, ["Alpha", "Beta", "Hidden"], id="no-visibility-hook"),
        pytest.param("Hidden", ["Alpha", "Beta"], id="unplanned-visibility-reread"),
    ],
)
@pytest.mark.django_db(transaction=True)
async def test_async_forward_m2m_reads_an_mti_ancestor_prefetch_over_http(
    hide_prefix: str | None,
    first_shop_tags: list[str],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """An ancestor-served list remains async-safe, and a hook rechecks only its hidden rows.

    The identity-hook control serves Hidden; the hiding hook must remove it
    while retaining Alpha/Beta and the second parent's Beta. Below Django 6.1
    the upstream manager does not reuse an ancestor's cache, but wire data and
    hook visibility still hold; the table-specific cost reflects that tier.
    """
    tag_model, place_model, shop_model = declare_mti_tag_models()
    models_in_order = (tag_model, place_model, shop_model)
    await sync_to_async(create_mti_tag_tables)(*models_in_order)
    try:
        await sync_to_async(seed_mti_tags)(tag_model, shop_model)
        schema = await sync_to_async(mti_tag_schema)(
            tag_model,
            place_model,
            shop_model,
            hide_prefix=hide_prefix,
            run_async=True,
        )
        statements = record_compiled_sql()

        payload = await _post_async(schema, _MTI_TAGS_QUERY)

        assert payload == _expected_shops(first_shop_tags)
        tag_reads = 3 if hide_prefix is not None or django.VERSION < (6, 1) else 1
        _assert_mti_cost(statements, tag_reads=tag_reads)
    finally:
        await sync_to_async(drop_mti_tag_tables)(*models_in_order)


@pytest.mark.skipif(
    django.VERSION < (6, 1),
    reason="Django below 6.1 queries a child's M2M instead of reusing its ancestor prefetch",
)
@pytest.mark.django_db(transaction=True)
def test_sync_forward_m2m_reuses_the_mti_ancestor_prefetch_over_http() -> None:
    """Both shops serve exact ordered tags with one shared tag read and no per-child requery."""
    tag_model, place_model, shop_model = declare_mti_tag_models()
    models_in_order = (tag_model, place_model, shop_model)
    create_mti_tag_tables(*models_in_order)
    try:
        seed_mti_tags(tag_model, shop_model)
        schema = mti_tag_schema(tag_model, place_model, shop_model, run_async=False)

        with CaptureQueriesContext(connection) as captured:
            payload = _post(schema, _MTI_TAGS_QUERY)

        assert payload == _expected_shops(["Alpha", "Beta", "Hidden"])
        _assert_mti_cost([entry["sql"] for entry in captured], tag_reads=1)
    finally:
        drop_mti_tag_tables(*models_in_order)


def _composite_parent_schema() -> DjangoSchema:
    class RpChildNode(DjangoType):
        class Meta:
            model = RpCompositeChild
            fields = ("name",)
            interfaces = (relay.Node,)

    class RpParentNode(DjangoType):
        code: NodeID[str]

        class Meta:
            model = RpCompositeParent
            fields = ("label", "code", "children")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        def _rp_parents(self) -> QuerySet[RpCompositeParent]:
            return RpCompositeParent.objects.order_by("tenant_id", "code")

        rp_parents: QuerySet[RpCompositeParent] = strawberry.field(
            resolver=_rp_parents,
            graphql_type=list[RpParentNode],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=[RpChildNode],
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


@pytest.mark.django_db(transaction=True)
def test_composite_parent_reverse_connection_falls_back_per_parent_over_http() -> None:
    """Two-carrier parent links retain exact first-two partitions using two child reads.

    Crossed carrier rows are deliberate unmatched ForeignObject probes: dropping
    either carrier could leak one into a served page. A third admitted A child
    proves first:2, and the separate B parent proves per-parent attachment.
    """
    with relation_fixture_tables(connection):
        RpCompositeParent.objects.create(tenant_id=1, code="A", label="PA")
        RpCompositeParent.objects.create(tenant_id=2, code="B", label="PB")
        RpCompositeChild.objects.create(parent_tenant_id=1, parent_code="B", name="cross-code")
        RpCompositeChild.objects.create(parent_tenant_id=2, parent_code="A", name="cross-tenant")
        for name in ("a-one", "a-two", "a-three"):
            RpCompositeChild.objects.create(parent_tenant_id=1, parent_code="A", name=name)
        RpCompositeChild.objects.create(parent_tenant_id=2, parent_code="B", name="b-one")
        schema = _composite_parent_schema()

        with CaptureQueriesContext(connection) as captured:
            payload = _post(
                schema,
                "{ rpParents { label childrenConnection(first: 2) { "
                "edges { node { name } } pageInfo { hasNextPage } } } }",
            )

        assert payload == {
            "data": {
                "rpParents": [
                    {
                        "label": "PA",
                        "childrenConnection": {
                            "edges": [{"node": {"name": "a-one"}}, {"node": {"name": "a-two"}}],
                            "pageInfo": {"hasNextPage": True},
                        },
                    },
                    {
                        "label": "PB",
                        "childrenConnection": {
                            "edges": [{"node": {"name": "b-one"}}],
                            "pageInfo": {"hasNextPage": False},
                        },
                    },
                ],
            },
        }
        statements = [entry["sql"] for entry in captured]
        parent_sql = _selects_from(statements, "products_rpcompositeparent")
        child_sql = _selects_from(statements, "products_rpcompositechild")
        assert len(parent_sql) == 1, statements
        assert len(child_sql) == 2, statements
        for sql in child_sql:
            assert "ROW_NUMBER" not in sql.upper(), sql
            assert "COUNT(" not in sql.upper(), sql
            assert "LIMIT 3" in sql.upper(), sql
            where = sql.split(" WHERE ", 1)[1]
            assert '"parent_tenant_id"' in where, sql
            assert '"parent_code"' in where, sql
