"""Live HTTP tests for generic-connection content-type isolation across database aliases.

The non-default alias assigns Branch a different content-type key. A generic
connection must use that alias's key at fetch time, rather than a default-alias
constant during planning. The holder graph exposes the relation without changing
fakeshop's intentionally unpublished generic fields.
"""

import os
from collections.abc import Iterator
from functools import wraps

import pytest

if os.environ.get("FAKESHOP_SHARDED") != "1":
    pytest.skip(
        "requires FAKESHOP_SHARDED=1 (the sharded DATABASES layout)",
        allow_module_level=True,
    )

import strawberry
from apps.library.models import Branch, TaggedItem
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_at, json_list, json_object
from strawberry import relay

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-generic-sharded/", _graphql_view)]


def _post(schema: DjangoSchema, query: str) -> JSONObject:
    """Read the non-default alias through a real GraphQL HTTP request."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload(query, url="/graphql-generic-sharded/")
        assert "errors" not in payload, payload
        return json_object(payload, "data")
    finally:
        _CURRENT["schema"] = None


@pytest.fixture(autouse=True)
def _isolate_content_types() -> Iterator[None]:
    """Forget content-type ids before and after the test changes their rows."""
    ContentType.objects.clear_cache()
    yield
    ContentType.objects.clear_cache()


def _build_schema() -> DjangoSchema:
    """Build a schema whose ``branches`` root reads from ``shard_b``."""

    class TaggedItemNode(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "tag")
            interfaces = (relay.Node,)
            connection = {"total_count": True}

    assert registry.get(TaggedItem) is TaggedItemNode

    class BranchNode(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name", "tags")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        def _branches(self) -> QuerySet[Branch]:
            return Branch.objects.using("shard_b").order_by("id")

        branches: QuerySet[Branch] = strawberry.field(
            resolver=_branches,
            graphql_type=list[BranchNode],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: ext],
    )


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_generic_connection_uses_shard_b_content_type_pk_not_default() -> None:
    """The GFK connection over ``shard_b`` parents returns rows under ``shard_b``'s ct pk.

    The default-alias ``Branch`` content-type pk and the ``shard_b`` one are
    forced apart. A plan-time constant would bake the default pk
    and, contradicting Django's fetch-time ``shard_b`` morph predicate, return
    zero rows; the alias-late design resolves the ct against ``shard_b`` and the
    branch's own three tags come back.
    """
    # Resolve the default-alias Branch content-type pk (what a plan-time
    # lookup on the unrouted child queryset would bake).
    default_branch_ct = ContentType.objects.db_manager("default").get_for_model(Branch)

    # Force ``shard_b``'s Branch content-type onto a DIFFERENT pk. Migrations
    # (post_migrate) pre-create a ``library.branch`` row on each alias with a
    # matching pk, so delete it and recreate at an explicit, distinct pk. The
    # FK cascade only touches TaggedItems, which are seeded afterwards.
    shard_branch_ct_pk = default_branch_ct.id + 500
    ContentType.objects.using("shard_b").filter(
        app_label="library",
        model="branch",
    ).delete()
    ContentType.objects.using("shard_b").create(
        pk=shard_branch_ct_pk,
        app_label="library",
        model="branch",
    )
    ContentType.objects.clear_cache()
    assert shard_branch_ct_pk != default_branch_ct.id

    # Seed the branch and its tags on ``shard_b`` under ``shard_b``'s ct pk.
    branch = Branch.objects.using("shard_b").create(name="Central")
    for tag in ("a1", "a2", "a3"):
        TaggedItem.objects.using("shard_b").create(
            content_type_id=shard_branch_ct_pk,
            object_id=branch.pk,
            tag=tag,
        )

    schema = _build_schema()
    data = _post(
        schema,
        """
        query {
          branches {
            tagsConnection(first: 2) {
              totalCount
              edges { node { tag } }
              pageInfo { hasNextPage }
            }
          }
        }
        """,
    )

    conn = json_object(data, "branches", 0, "tagsConnection")
    # Non-empty rows prove the fetch used ``shard_b``'s ct pk, not the baked
    # default pk (which would have matched zero rows on ``shard_b``).
    assert [json_at(edge, "node", "tag") for edge in json_list(conn, "edges")] == ["a1", "a2"]
    assert conn["totalCount"] == 3
    assert json_at(conn, "pageInfo", "hasNextPage") is True
