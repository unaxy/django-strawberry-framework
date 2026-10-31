"""Live HTTP tests for generic-connection content types, projection and pagination.

The shipped schema deliberately leaves its generic relations unpublished. These
holder mounts declare the public Meta-based graph beside fakeshop and keep the
content-type, paging and query-cost claims on the HTTP tier.
"""

from collections.abc import Mapping, Sequence
from functools import wraps

import pytest
import strawberry
from apps.library.models import Branch, Genre, ProxyBranch, TaggedItem
from asgiref.sync import sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.db import connection as db_connection
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_object,
    response_json,
)
from strawberry import relay

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import AsyncTestClient
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
    path("graphql-generic/", _graphql_view),
    path("graphql-generic-async/", _async_graphql_view),
]


def _post(schema: DjangoSchema, query: str) -> JSONObject:
    """Serve the function-scoped graph through Django's HTTP request stack."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload(query, url="/graphql-generic/")
        assert "errors" not in payload, payload
        return json_object(payload, "data")
    finally:
        _CURRENT["schema"] = None


async def _post_async(schema: DjangoSchema, query: str) -> JSONObject:
    """Serve the same graph through the package's async HTTP view."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            result = await AsyncTestClient().query(query, url="/graphql-generic-async/")
        assert result.response.status_code == 200
        payload = response_json(result.response)
        assert "errors" not in payload, payload
        return json_object(payload, "data")
    finally:
        _CURRENT["schema"] = None


def _build_schema(*, strategy: str | None = None, total_count: bool = False) -> DjangoSchema:
    """Build a schema exposing ``branches`` with a windowed ``tagsConnection``.

    ``strategy`` selects the nested-connection strategy
    (``None`` -> windowed default, ``"lateral"`` -> auto/lateral). ``total_count``
    opts the target connection into a ``totalCount`` field.
    """

    class TaggedItemNode(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "tag")
            interfaces = (relay.Node,)
            if total_count:
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
            return Branch.objects.order_by("id")

        branches: QuerySet[Branch] = strawberry.field(
            resolver=_branches,
            graphql_type=list[BranchNode],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension(nested_connection_strategy=strategy)
    return DjangoSchema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: ext],
    )


def _tag_statements(captured_queries: Sequence[Mapping[str, str]]) -> list[str]:
    """Read only the child table's statements, excluding middleware and parent reads."""
    table = db_connection.ops.quote_name(TaggedItem._meta.db_table)
    return [query["sql"] for query in captured_queries if f"FROM {table}" in query["sql"]]


def _window_sql(captured_queries: Sequence[Mapping[str, str]]) -> str:
    """Return the windowed child SQL (the ``ROW_NUMBER`` prefetch), asserting it ran.

    Its presence proves the generic connection took the WINDOWED path rather
    than degrading to a per-parent fallback.
    """
    for sql in _tag_statements(captured_queries):
        if "ROW_NUMBER" in sql.upper():
            return sql
    raise AssertionError("no windowed (ROW_NUMBER) child query was captured")


@pytest.mark.django_db
def test_windowed_generic_connection_first_page_excludes_poison_row() -> None:
    """first:N page + cursors + totalCount are correct with a poison row present.

    The poison ``TaggedItem`` shares ``object_id`` with the branch but carries a
    DIFFERENT content type, so it lands in the same ``object_id`` partition. The
    alias-late content-type WHERE Django's generic prefetch adds at fetch time
    (inside the window subquery) excludes the foreign content type even though
    the partition alone would admit it.
    """
    branch = Branch.objects.create(name="Central")
    other = Branch.objects.create(name="Annex")
    for tag in ("a1", "a2", "a3"):
        TaggedItem.objects.create(content_object=branch, tag=tag)
    TaggedItem.objects.create(content_object=other, tag="b1")
    # Poison: same object_id as ``branch`` but a Genre content type.
    genre_ct = ContentType.objects.get_for_model(Genre)
    TaggedItem.objects.create(content_type=genre_ct, object_id=branch.pk, tag="poison")

    schema = _build_schema(total_count=True)
    data = _post(
        schema,
        """
        query {
          branches {
            tagsConnection(first: 2) {
              totalCount
              edges { cursor node { tag } }
              pageInfo { hasNextPage }
            }
          }
        }
        """,
    )

    conn = json_object(data, "branches", 0, "tagsConnection")
    edges = json_list(conn, "edges")
    assert [json_at(edge, "node", "tag") for edge in edges] == ["a1", "a2"]
    assert all(json_at(edge, "cursor") for edge in edges)
    # totalCount counts only the branch's own three tags - the poison row and
    # the other branch's tag are excluded by the morph WHERE / object_id partition.
    assert conn["totalCount"] == 3
    assert json_at(conn, "pageInfo", "hasNextPage") is True


@pytest.mark.django_db
def test_generic_connection_has_next_page_probe_avoids_a_partition_count() -> None:
    """A hasNextPage-only generic page composes with the count-free probe.

    No ``totalCount`` selected on a bounded first page -> the window overfetches
    a sentinel row instead of paying a ``Count(1) OVER`` scan; the sentinel's
    presence answers ``hasNextPage``.
    """
    branch = Branch.objects.create(name="Central")
    for index in range(3):
        TaggedItem.objects.create(content_object=branch, tag=f"t{index}")

    schema = _build_schema()

    with CaptureQueriesContext(db_connection) as ctx:
        data = _post(
            schema,
            "{ branches { tagsConnection(first: 2) {"
            " edges { node { tag } } pageInfo { hasNextPage } } } }",
        )
    conn = json_object(data, "branches", 0, "tagsConnection")
    assert [json_at(edge, "node", "tag") for edge in json_list(conn, "edges")] == ["t0", "t1"]
    assert json_at(conn, "pageInfo", "hasNextPage") is True
    # Windowed path taken, and count-free: the probe replaces the partition count.
    window_sql = _window_sql(ctx.captured_queries)
    assert "COUNT(" not in window_sql.upper()

    # Boundary: the page ending exactly at the partition tail -> hasNextPage False.
    exact = _post(
        schema,
        "{ branches { tagsConnection(first: 3) { pageInfo { hasNextPage } } } }",
    )
    assert json_at(exact, "branches", 0, "tagsConnection", "pageInfo", "hasNextPage") is False


@pytest.mark.django_db
def test_scalar_only_generic_connection_has_no_per_row_refetch() -> None:
    """A pageInfo-only generic window loads object_id + content_type_id, so no N+1.

    The projection includes BOTH the ``object_id`` connector and the
    ``content_type_id`` that Django's generic-prefetch attach reads off each
    child (its attach key is ``(object_id, content_type_id)``), so a scalar-only
    window never deferred-refetches either column once per row - the GenericRelation N+1
    fix. The query count must not scale with the number of tags.
    """
    schema = _build_schema()
    query = "{ branches { tagsConnection { pageInfo { hasNextPage } } } }"

    branch = Branch.objects.create(name="Central")
    for index in range(2):
        TaggedItem.objects.create(content_object=branch, tag=f"t{index}")
    with CaptureQueriesContext(db_connection) as small:
        data = _post(schema, query)
        assert data == {"branches": [{"tagsConnection": {"pageInfo": {"hasNextPage": False}}}]}

    for index in range(2, 8):
        TaggedItem.objects.create(content_object=branch, tag=f"t{index}")
    with CaptureQueriesContext(db_connection) as large:
        data = _post(schema, query)
        assert data == {"branches": [{"tagsConnection": {"pageInfo": {"hasNextPage": False}}}]}

    # No per-row deferred refetch: adding six tags does not add six queries.
    assert len(_tag_statements(large.captured_queries)) == 1
    assert len(_tag_statements(small.captured_queries)) == 1
    # The scalar-only window explicitly loads both morph columns.
    window_sql = _window_sql(large.captured_queries).lower()
    assert "object_id" in window_sql
    assert "content_type_id" in window_sql


@pytest.mark.django_db
def test_lateral_strategy_generic_connection_degrades_to_windowed() -> None:
    """A generic connection under the lateral strategy degrades to the windowed body.

    ``parent_link_field`` is ``None`` for the generic join, so the lateral
    backend refuses at ``_build_lateral_spec`` and the auto strategy runs the
    already-windowed ORM query - no error, correct rows.
    """
    branch = Branch.objects.create(name="Central")
    for index in range(3):
        TaggedItem.objects.create(content_object=branch, tag=f"t{index}")

    schema = _build_schema(strategy="lateral")
    with CaptureQueriesContext(db_connection) as captured:
        data = _post(
            schema,
            "{ branches { tagsConnection(first: 2) { edges { node { tag } } } } }",
        )
    assert "ROW_NUMBER" in _window_sql(captured.captured_queries).upper()

    conn = json_object(data, "branches", 0, "tagsConnection")
    assert [json_at(edge, "node", "tag") for edge in json_list(conn, "edges")] == ["t0", "t1"]


@pytest.mark.django_db(transaction=True)
async def test_generic_connection_serves_a_plain_root_under_async(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """An async HTTP request completes a generic connection under a plain ``def`` root.

    The root resolver returns an unevaluated queryset on the event-loop thread; the
    optimizer builds the windowed ``tagsConnection`` plan in a worker thread (the
    plan is not cached yet, so it hops) and the list completes the planned queryset
    off the loop, with a cold ``ContentType`` cache. That planning itself performs no
    ORM work is pinned on the walker:
    ``tests/optimizer/test_walker.py::test_generic_connection_planning_does_no_sync_db_io_under_async``.
    """
    branch = await sync_to_async(Branch.objects.create)(name="Central")
    for index in range(3):
        await sync_to_async(TaggedItem.objects.create)(content_object=branch, tag=f"t{index}")
    schema = _build_schema()
    ContentType.objects.clear_cache()
    compiled = record_compiled_sql(TaggedItem._meta.db_table)

    data = await _post_async(
        schema,
        "{ branches { tagsConnection(first: 2) { edges { node { tag } } } } }",
    )

    conn = json_object(data, "branches", 0, "tagsConnection")
    assert [json_at(edge, "node", "tag") for edge in json_list(conn, "edges")] == ["t0", "t1"]
    assert len(compiled) == 1, compiled


def _build_proxy_schema() -> DjangoSchema:
    """Build a schema exposing ``proxyBranches`` with a ``proxyTagsConnection``.

    ``ProxyBranch`` is a proxy of ``Branch`` whose ``proxy_tags`` generic
    relation is declared with ``for_concrete_model=False``, so the reverse tag
    manager filters ``TaggedItem`` rows by the PROXY content type rather than
    ``Branch``'s concrete content type.
    """

    class TaggedItemNode(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "tag")
            interfaces = (relay.Node,)
            connection = {"total_count": True}

    assert registry.get(TaggedItem) is TaggedItemNode

    class ProxyBranchNode(DjangoType):
        class Meta:
            model = ProxyBranch
            fields = ("id", "name", "proxy_tags")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        def _proxy_branches(self) -> QuerySet[ProxyBranch]:
            return ProxyBranch.objects.order_by("id")

        proxy_branches: QuerySet[ProxyBranch] = strawberry.field(
            resolver=_proxy_branches,
            graphql_type=list[ProxyBranchNode],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: ext],
    )


@pytest.mark.django_db
def test_generic_connection_honors_non_default_for_concrete_model() -> None:
    """A ``for_concrete_model=False`` generic connection morphs to the PROXY content type.

    ``ProxyBranch.proxy_tags`` is declared ``for_concrete_model=False``, so its
    alias-late morph predicate must select the ``ProxyBranch`` content type, not
    ``Branch``'s concrete content type. The two content types are forced apart by
    construction (a proxy model gets its own ``django_content_type`` row). The
    branch's real tags are seeded under the PROXY content type; a decoy tag is
    seeded under the CONCRETE ``Branch`` content type with the SAME
    ``object_id``.

    The connection must return only the proxy-content-type rows and exclude the
    decoy. If a future change discarded the ``GenericRelation`` field's
    ``for_concrete_model`` semantics - or re-baked a concrete-default
    content-type constant at plan time - the connection would instead return the
    concrete decoy (or empty), and these assertions bite.
    """
    proxy_ct = ContentType.objects.get_for_model(ProxyBranch, for_concrete_model=False)
    concrete_ct = ContentType.objects.get_for_model(Branch)
    # A proxy model carries its own content type, distinct from the concrete
    # parent's - the whole point of ``for_concrete_model=False``.
    assert proxy_ct.id != concrete_ct.id

    branch = Branch.objects.create(name="Central")
    for tag in ("p1", "p2", "p3"):
        TaggedItem.objects.create(content_type=proxy_ct, object_id=branch.pk, tag=tag)
    # Decoy: same ``object_id`` but the CONCRETE ``Branch`` content type. A plan
    # that discarded ``for_concrete_model=False`` would return THIS row.
    TaggedItem.objects.create(content_type=concrete_ct, object_id=branch.pk, tag="decoy")

    schema = _build_proxy_schema()
    data = _post(
        schema,
        """
        query {
          proxyBranches {
            proxyTagsConnection(first: 2) {
              totalCount
              edges { node { tag } }
              pageInfo { hasNextPage }
            }
          }
        }
        """,
    )

    conn = json_object(data, "proxyBranches", 0, "proxyTagsConnection")
    # Only the proxy-content-type rows come back; the concrete decoy is excluded.
    assert [json_at(edge, "node", "tag") for edge in json_list(conn, "edges")] == ["p1", "p2"]
    assert conn["totalCount"] == 3
    assert json_at(conn, "pageInfo", "hasNextPage") is True
