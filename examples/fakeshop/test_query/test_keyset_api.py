"""Live GraphQL HTTP tests for keyset (``Meta.cursor_field``) cursor pagination.

The acceptance surface for the ``stable_cursor_field`` contract over the
library app's ``IssueType`` (``cursor_field = ("-number", "id")`` - the
newest-first mixed-direction shape) and ``PeriodicalType.issuesConnection``
(the nested windowed keyset seek):

- value cursors round-trip (``endCursor`` -> ``after:``) and SURVIVE inserts
  and deletes before the cursor - the motivating fix for offset-cursor drift;
- ``totalCount`` stays the PRE-seek partition count on every ``after:`` page;
- a ``totalCount``-only document counts that set without fetching page rows;
- omitting every pagination argument serves the full set when it is under the
  Relay cap;
- nested seeks apply UNIFORM VALUE-POSITION semantics across every parent
  partition, and the batched window stays one prefetch query, a random
  ``Meta.ordering`` on the target included (the declared ``cursor_field`` stays
  the order);
- tampered, foreign-order, and offset (``arrayconnection``) cursors are
  rejected with the uniform invalid-cursor error;
- minted cursors are deterministic across requests and do not disclose
  ordering values in the clear (AES-SIV authenticated-encrypted payload);
- a cursor outlives a ``SECRET_KEY`` rotation that declares the old key in
  ``SECRET_KEY_FALLBACKS``, and dies with one that does not;
- cursors are permission-aware by construction: a staff-minted cursor
  replays for an anonymous viewer over only the rows that viewer can see;
- the nested window itself is scoped by the target hook the plan applied, so a
  keyset page is partitioned over the viewer's rows and counted on them;
- a target ``get_queryset`` ORDER is the connection's effective order: the
  nested window (reverse FK and M2M, batched or single-parent) orders, seeks
  and mints under that order's own cursor vocabulary, so page 2 serves every
  remaining row once, ``totalCount`` stays pre-seek, and one row's cursor is
  byte-identical from the root connection, the planned window and the
  per-parent pipeline (sync and async); one relation name windowed twice in
  an operation (``children`` under two root fields) keeps each window's own
  vocabulary; an order no cursor can anchor (an expression, ``"?"``,
  ``Random()``) is the same keyset error nested as at the root,
  ``strictness="raise"`` included, while on an offset relation a random hook
  order is an unplanned per-parent access ``strictness="raise"`` reports, and a
  malformed ``after:`` on a relation the planner refuses stays the cursor error
  under ``strictness="raise"``;
- a target ``get_queryset`` ``extra(order_by=...)`` ordering, which Django
  compiles in place of every other ordering, is the connection's order too: a
  field, a descending field, the child's own ``table.column``, a foreign key's
  raw column, a joined table's column and a quoted table name, each as written
  and ``.reverse()``'d, page every row once forward and backward at the root
  (offset and keyset), the planned window serves the per-parent page, a raw
  ``table.column`` term reaches every statement as Django compiles it, a random
  ``extra`` order keeps the pk tiebreaker, and a foreign-key or raw term is the
  keyset refusal at the root and nested (sync and async).

Resolver-contract refusals (a list source, an already-sliced QuerySet) and the
async slicer colour (``acount``, async iteration, deferred cursor columns) ride
a test-local holder: ``/graphql-test/`` (sync ``DjangoGraphQLView``) and
``/graphql-async/`` (``AsyncDjangoGraphQLView``) over shipped ``IssueType``.
The hook-order rows mount test-local ``Issue`` / ``Book`` children
(``cursor_field = ("id",)`` plus an ordering ``get_queryset``) under
``Periodical`` / ``Genre`` parents on the same holder, and the one-name rows mount ``CirculationDesk`` /
``ScalarSpecimen`` ``children`` the same way.
Async rows drive ``AsyncTestClient`` (``graphql_client.py`` is sync-only) with
``django_db(transaction=True)``.

Cursors are always MINTED then round-tripped - never pinned as literals -
because the payload is authenticated-encrypted opaque bytes (the codec contract).
"""

import base64
import datetime
import uuid
from collections.abc import Callable, Mapping

import pytest
import strawberry
from apps.library import models
from apps.library import schema as library_schema
from apps.scalars.models import ScalarSpecimen
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Model, QuerySet
from django.db.models.expressions import Combinable
from django.db.models.functions import Lower, Random
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches, path
from graphql_client import (
    JSONObject,
    json_at,
    json_bool,
    json_list,
    json_object,
    json_str,
    read_attr,
    response_json,
)
from graphql_client import assert_graphql_success as _assert_graphql_success
from graphql_client import graphql_payload as _graphql_payload
from graphql_client import post_graphql as _post_graphql
from strategy_schemas import make_django_type
from strawberry.relay.utils import from_base64, to_base64

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import AsyncTestClient, TestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

_CURRENT: dict[str, strawberry.Schema | None] = {"schema": None}


def _holder_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


async def _async_holder_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-test/", _holder_view), path("graphql-async/", _async_holder_view)]


def _issue_holder_schema(resolver: Callable[..., object]) -> strawberry.Schema:

    @strawberry.type
    class Query:
        issues = DjangoConnectionField(library_schema.IssueType, resolver=resolver)

    return strawberry.Schema(query=Query, config=strawberry_config())


def _post_holder(
    schema: strawberry.Schema,
    query: str,
    *,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            return _graphql_payload(query, variables=variables, url="/graphql-test/")
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


async def _post_async_holder(
    schema: strawberry.Schema,
    query: str,
    *,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            result = await AsyncTestClient().query(
                query,
                variables=variables,
                assert_no_errors=False,
                url="/graphql-async/",
            )
        assert result.response.status_code == 200, result.response.content
        return response_json(result.response)
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


def _seed_three_issues() -> None:
    periodical = models.Periodical.objects.create(name="Holder Journal")
    for number in (1, 2, 3):
        models.Issue.objects.create(
            periodical=periodical,
            number=number,
            title=f"i{number}",
        )


def _seed_periodicals() -> tuple[models.Periodical, models.Periodical, models.Periodical]:
    """Two populated periodicals plus one empty; issue numbers repeat across them.

    Under the declared ``("-number", "id")`` order the root connection
    interleaves: astro#5, astro#4, astro#3, bot#3, astro#2, bot#2, astro#1,
    bot#1 (equal numbers tie-break on ascending pk - astronomy rows were
    created first).
    """
    astronomy = models.Periodical.objects.create(name="Astronomy Weekly")
    botany = models.Periodical.objects.create(name="Botany Monthly")
    empty = models.Periodical.objects.create(name="Empty Gazette")
    for number in range(1, 6):
        models.Issue.objects.create(periodical=astronomy, number=number, title=f"Astro #{number}")
    for number in range(1, 4):
        models.Issue.objects.create(periodical=botany, number=number, title=f"Bot #{number}")
    return astronomy, botany, empty


ROOT_PAGE_QUERY = """
query ($first: Int, $last: Int, $after: String, $before: String) {
  allLibraryIssuesConnection(first: $first, last: $last, after: $after, before: $before) {
    totalCount
    pageInfo { hasNextPage hasPreviousPage startCursor endCursor }
    edges { cursor node { title number } }
  }
}
"""


def _root_page(**variables: object) -> JSONObject:
    data = _assert_graphql_success(ROOT_PAGE_QUERY, variables=variables)
    return json_object(data, "allLibraryIssuesConnection")


def _titles(connection_payload: object) -> list[str]:
    return [json_str(edge, "node", "title") for edge in json_list(connection_payload, "edges")]


@pytest.mark.django_db
def test_root_keyset_first_page_orders_by_cursor_field() -> None:
    """The declared ``cursor_field`` IS the connection's default order (newest-first)."""
    _seed_periodicals()
    page = _root_page(first=3)
    assert _titles(page) == ["Astro #5", "Astro #4", "Astro #3"]
    assert json_at(page, "totalCount") == 8
    assert json_at(page, "pageInfo", "hasNextPage") is True
    assert json_at(page, "pageInfo", "hasPreviousPage") is False
    assert json_at(page, "pageInfo", "startCursor") == json_at(page, "edges", 0, "cursor")
    assert json_at(page, "pageInfo", "endCursor") == json_at(page, "edges", -1, "cursor")
    prefix, _payload = from_base64(json_str(page, "edges", 0, "cursor"))
    assert prefix == "dstcursor"


@pytest.mark.django_db
def test_root_keyset_total_count_only_does_not_fetch_edges() -> None:
    """A ``totalCount``-only document counts the pre-pagination set and fetches no page rows."""
    _seed_periodicals()
    with CaptureQueriesContext(connection) as ctx:
        data = _assert_graphql_success("{ allLibraryIssuesConnection { totalCount } }")
    assert json_at(data, "allLibraryIssuesConnection") == {"totalCount": 8}
    issue_sql = [
        entry["sql"] for entry in ctx.captured_queries if 'FROM "library_issue"' in entry["sql"]
    ]
    assert issue_sql, ctx.captured_queries
    assert all("COUNT(" in sql.upper() for sql in issue_sql), issue_sql
    assert not any("LIMIT" in sql.upper() for sql in issue_sql), issue_sql


@pytest.mark.django_db
def test_root_keyset_cursors_are_deterministic() -> None:
    """Identical values under the same order mint identical cursor bytes across requests."""
    _seed_periodicals()
    first = _root_page(first=1)
    second = _root_page(first=1)
    first_cursors = [json_at(edge, "cursor") for edge in json_list(first, "edges")]
    second_cursors = [json_at(edge, "cursor") for edge in json_list(second, "edges")]
    assert len(first_cursors) == 1
    assert all(cursor for cursor in first_cursors)
    assert first_cursors == second_cursors
    assert json_at(first, "pageInfo", "endCursor") == json_at(second, "pageInfo", "endCursor")


@pytest.mark.django_db
def test_root_keyset_round_trip_and_pre_seek_total_count() -> None:
    """``endCursor`` -> ``after:`` continues exactly; ``totalCount`` stays pre-seek."""
    _seed_periodicals()
    first_page = _root_page(first=3)
    second_page = _root_page(first=3, after=json_at(first_page, "pageInfo", "endCursor"))
    assert _titles(second_page) == ["Bot #3", "Astro #2", "Bot #2"]
    assert (
        json_at(second_page, "totalCount") == 8
    )  # the pre-pagination set, not the post-seek tail
    assert json_at(second_page, "pageInfo", "hasPreviousPage") is True
    assert json_at(second_page, "pageInfo", "hasNextPage") is True
    third_page = _root_page(first=3, after=json_at(second_page, "pageInfo", "endCursor"))
    assert _titles(third_page) == ["Astro #1", "Bot #1"]
    assert json_at(third_page, "pageInfo", "hasNextPage") is False


@pytest.mark.django_db
def test_root_keyset_page_survives_inserts_and_deletes_before_cursor() -> None:
    """The motivating stability pin: mutations before the cursor cannot drift the page."""
    astronomy, _botany, _empty = _seed_periodicals()
    cursor = json_at(_root_page(first=3), "pageInfo", "endCursor")
    baseline = _titles(_root_page(first=3, after=cursor))

    # Insert a row that sorts BEFORE the cursor position (number 9 > 5 sorts
    # first under -number) and delete one from before it too - an offset
    # cursor would shift by one in each direction; the value cursor cannot.
    models.Issue.objects.create(periodical=astronomy, number=9, title="Astro #9")
    models.Issue.objects.get(title="Astro #5").delete()
    assert _titles(_root_page(first=3, after=cursor)) == baseline


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["tampered", "offset"], ids=["tampered", "offset"])
def test_root_keyset_rejects_tampered_and_offset_cursors(kind: str) -> None:
    """Tampered bytes and offset-vocabulary cursors both get the uniform rejection."""
    _seed_periodicals()
    minted = json_str(_root_page(first=1), "pageInfo", "endCursor")
    bad_cursor = {
        "tampered": minted[:-8] + "AAAAAAAA",
        "offset": to_base64("arrayconnection", 2),
    }[kind]
    response = _post_graphql(ROOT_PAGE_QUERY, variables={"first": 1, "after": bad_cursor})
    assert response.status_code == 200
    payload = response_json(response)
    assert "errors" in payload, payload
    assert "invalid cursor" in json_str(payload, "errors", 0, "message")
    assert json_at(payload, "data") is None, payload


@pytest.mark.django_db
def test_root_keyset_cursor_survives_a_secret_key_rotation_that_keeps_the_fallback() -> None:
    """A live cursor keeps working across a ``SECRET_KEY`` rotation that declares the old key.

    Cursors are authenticated-encrypted with the deployment's ``SECRET_KEY``, so a
    rotation would otherwise invalidate every page link a client is holding mid-
    session. The decode consults ``SECRET_KEY_FALLBACKS``, which is what makes a
    rotation a configuration change rather than an outage. The must-not is the
    second half: with the old key dropped from the fallbacks the SAME cursor is
    tamper-equivalent, so the fallback list is a declared trust set, not a
    weakening of the authentication.
    """
    _seed_periodicals()
    original_key = read_attr(settings, "SECRET_KEY")
    assert isinstance(original_key, str), original_key
    cursor = json_at(_root_page(first=3), "pageInfo", "endCursor")

    with override_settings(SECRET_KEY="rotated-live-key", SECRET_KEY_FALLBACKS=[original_key]):
        rotated = _root_page(first=3, after=cursor)
    assert _titles(rotated) == ["Bot #3", "Astro #2", "Bot #2"]

    with override_settings(SECRET_KEY="rotated-live-key", SECRET_KEY_FALLBACKS=[]):
        response = _post_graphql(ROOT_PAGE_QUERY, variables={"first": 3, "after": cursor})

    assert response.status_code == 200
    payload = response_json(response)
    assert "errors" in payload, payload
    assert json_at(payload, "data") is None, payload
    assert "invalid cursor" in json_str(payload, "errors", 0, "message"), payload


@pytest.mark.django_db
def test_root_keyset_backward_pagination() -> None:
    """``last:`` and ``last:``+``before:`` page backward through the value order."""
    _seed_periodicals()
    tail = _root_page(last=2)
    assert _titles(tail) == ["Astro #1", "Bot #1"]
    assert json_at(tail, "pageInfo", "hasPreviousPage") is True
    assert json_at(tail, "pageInfo", "hasNextPage") is False
    previous = _root_page(last=2, before=json_at(tail, "pageInfo", "startCursor"))
    assert _titles(previous) == ["Astro #2", "Bot #2"]
    assert json_at(previous, "pageInfo", "hasPreviousPage") is True
    assert json_at(previous, "pageInfo", "hasNextPage") is True
    # Walk all the way back: the head page reports no previous rows.
    head = previous
    while json_at(head, "pageInfo", "hasPreviousPage"):
        head = _root_page(last=2, before=json_at(head, "pageInfo", "startCursor"))
    assert _titles(head) == ["Astro #5"] or _titles(head) == ["Astro #5", "Astro #4"]
    assert json_at(head, "pageInfo", "hasPreviousPage") is False


#: ``first: 0``'s empty-page ``pageInfo`` when rows exist past the page.
_ZERO_PAGE_INFO = {"hasNextPage": True, "startCursor": None, "endCursor": None}


@pytest.mark.django_db
def test_root_keyset_last_zero_serves_the_first_zero_page() -> None:
    """``last: 0`` is the ``first: 0`` page: no edges, ``first: 0``'s ``pageInfo``.

    Seeded past the Relay cap, so a page serving every row cannot pass.
    """
    astronomy, _botany, _empty = _seed_periodicals()
    models.Issue.objects.bulk_create(
        [
            models.Issue(
                periodical=astronomy,
                number=number,
                title=f"Cap probe #{number}",
            )
            for number in range(100, 193)
        ],
    )
    page = _root_page(last=0)
    assert json_at(page, "totalCount") == 101
    assert json_at(page, "edges") == []
    assert json_at(page, "pageInfo") == {**_ZERO_PAGE_INFO, "hasPreviousPage": False}
    assert page == _root_page(first=0)


@pytest.mark.django_db
def test_root_keyset_last_zero_with_after_serves_the_first_zero_page() -> None:
    """``last: 0`` + ``after:`` is ``first: 0`` + the same ``after:``.

    No edges, the pre-seek ``totalCount``, and the value-domain flags ``first: 0``
    serves: the supplied cursor is the previous-page signal and rows past it exist.
    """
    _seed_periodicals()
    after = json_at(_root_page(first=2), "pageInfo", "endCursor")
    page = _root_page(last=0, after=after)
    assert json_at(page, "edges") == []
    assert json_at(page, "totalCount") == 8
    assert json_at(page, "pageInfo") == {**_ZERO_PAGE_INFO, "hasPreviousPage": True}
    assert page == _root_page(first=0, after=after)


NESTED_ZERO_PAGE = """
query ($first: Int, $last: Int, $after: String) {
  allLibraryPeriodicalsConnection(first: 10) {
    edges {
      node {
        name
        issuesConnection(first: $first, last: $last, after: $after) {
          totalCount
          edges { node { title } }
          pageInfo { hasNextPage hasPreviousPage }
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.parametrize("with_after", [False, True], ids=["no-cursor", "after"])
def test_nested_keyset_last_zero_serves_the_first_zero_window(*, with_after: bool) -> None:
    """Nested ``last: 0`` is the planned ``first: 0`` keyset window over the same cursor.

    The same payload ``first: 0`` returns, served by the one batched window
    prefetch rather than per parent.
    """
    astronomy, _botany, _empty = _seed_periodicals()
    cursor = {}
    if with_after:
        first_page = _nested_by_periodical(first=2)[astronomy.name]
        cursor = {"after": json_at(first_page, "pageInfo", "endCursor")}
    with CaptureQueriesContext(connection) as ctx:
        data = _assert_graphql_success(NESTED_ZERO_PAGE, variables={"last": 0, **cursor})
    issue_queries = [q["sql"] for q in ctx.captured_queries if "library_issue" in q["sql"]]
    assert len(issue_queries) == 1, issue_queries
    page = next(
        json_at(e, "node", "issuesConnection")
        for e in json_list(data, "allLibraryPeriodicalsConnection", "edges")
        if json_at(e, "node", "name") == astronomy.name
    )
    assert page == {
        "totalCount": 5,
        "edges": [],
        "pageInfo": {"hasNextPage": True, "hasPreviousPage": with_after},
    }
    assert data == _assert_graphql_success(
        NESTED_ZERO_PAGE,
        variables={"first": 0, **cursor},
    )


@pytest.mark.django_db
def test_root_keyset_first_and_last_guard_still_applies() -> None:
    """The package's first+last mutual-exclusivity guard precedes any slicing."""
    _seed_periodicals()
    response = _post_graphql(ROOT_PAGE_QUERY, variables={"first": 1, "last": 1})
    payload = response_json(response)
    assert "errors" in payload
    assert json_at(payload, "data") is None, payload
    assert "mutually exclusive" in json_str(payload, "errors", 0, "message")


ROOT_ORDERED_QUERY = """
query ($first: Int, $after: String) {
  allLibraryIssuesConnection(first: $first, after: $after, orderBy: [{ title: ASC }]) {
    pageInfo { endCursor }
    edges { node { title } }
  }
}
"""


@pytest.mark.django_db
def test_root_keyset_order_by_mints_order_fingerprinted_cursors() -> None:
    """An ``orderBy:`` page mints cursors bound to THAT order; replay elsewhere is rejected."""
    _seed_periodicals()
    data = _assert_graphql_success(ROOT_ORDERED_QUERY, variables={"first": 2})
    ordered = json_at(data, "allLibraryIssuesConnection")
    assert [json_at(e, "node", "title") for e in json_list(ordered, "edges")] == [
        "Astro #1",
        "Astro #2",
    ]
    ordered_cursor = json_at(ordered, "pageInfo", "endCursor")

    # Same order: the cursor seeks the next title page.
    data = _assert_graphql_success(
        ROOT_ORDERED_QUERY,
        variables={"first": 2, "after": ordered_cursor},
    )
    assert [
        json_at(e, "node", "title") for e in json_list(data, "allLibraryIssuesConnection", "edges")
    ] == ["Astro #3", "Astro #4"]

    # Default order: the fingerprint mismatch rejects the replay.
    response = _post_graphql(ROOT_PAGE_QUERY, variables={"first": 2, "after": ordered_cursor})
    payload = response_json(response)
    assert "errors" in payload, payload
    assert "invalid cursor" in json_str(payload, "errors", 0, "message")
    assert json_at(payload, "data") is None, payload


@pytest.mark.django_db
def test_root_keyset_order_by_literal_string_none_title_round_trips() -> None:
    """A real ``title == "None"`` row mints and seeks correctly (null is not encoded)."""
    astronomy, _botany, _empty = _seed_periodicals()
    models.Issue.objects.create(periodical=astronomy, number=80, title="None")
    models.Issue.objects.create(periodical=astronomy, number=81, title="None2")
    query = """
    query ($first: Int, $after: String) {
      allLibraryIssuesConnection(
        first: $first, after: $after, orderBy: [{ title: ASC }]
      ) {
        edges { cursor node { title } }
      }
    }
    """
    data = _assert_graphql_success(query, variables={"first": 20})
    edges = json_list(data, "allLibraryIssuesConnection", "edges")
    none_edge = next(e for e in edges if json_at(e, "node", "title") == "None")
    data2 = _assert_graphql_success(
        query,
        variables={"first": 5, "after": json_at(none_edge, "cursor")},
    )
    titles = [
        json_at(e, "node", "title")
        for e in json_list(data2, "allLibraryIssuesConnection", "edges")
    ]
    assert "None" not in titles
    assert "None2" in titles


@pytest.mark.django_db
def test_root_keyset_cursors_do_not_disclose_ordering_values() -> None:
    """An ``orderBy:`` cursor's encrypted payload does not contain the ordering value."""
    astronomy, _botany, _empty = _seed_periodicals()
    sentinel = "cursor-secret-value"
    models.Issue.objects.create(periodical=astronomy, number=80, title=sentinel)
    data = _assert_graphql_success(
        """
        query {
          allLibraryIssuesConnection(first: 20, orderBy: [{ title: ASC }]) {
            edges { cursor node { title } }
          }
        }
        """,
    )
    edge = next(
        e
        for e in json_list(data, "allLibraryIssuesConnection", "edges")
        if json_at(e, "node", "title") == sentinel
    )
    prefix, encrypted = from_base64(json_str(edge, "cursor"))
    assert prefix == "dstcursor"
    assert sentinel not in encrypted
    assert sentinel.encode() not in base64.urlsafe_b64decode(encrypted)


NESTED_QUERY = """
query ($first: Int, $after: String) {
  allLibraryPeriodicalsConnection(first: 10) {
    edges { node { name issuesConnection(first: $first, after: $after) {
      totalCount
      pageInfo { hasNextPage hasPreviousPage endCursor }
      edges { cursor node { title number } }
    } } }
  }
}
"""


def _nested_by_periodical(**variables: object) -> dict[str, JSONObject]:
    data = _assert_graphql_success(NESTED_QUERY, variables=variables)
    return {
        json_str(edge, "node", "name"): json_object(edge, "node", "issuesConnection")
        for edge in json_list(data, "allLibraryPeriodicalsConnection", "edges")
    }


@pytest.mark.django_db
def test_nested_keyset_window_is_one_batched_query() -> None:
    """The counted keyset window stays a single batched prefetch (no per-parent N+1)."""
    _seed_periodicals()
    with CaptureQueriesContext(connection) as ctx:
        by_name = _nested_by_periodical(first=2)
    # parents + ONE window prefetch (plus any session/auth noise Django adds -
    # pin the exact absence of per-parent issue queries instead of a raw count).
    issue_queries = [q["sql"] for q in ctx.captured_queries if "library_issue" in q["sql"]]
    assert len(issue_queries) == 1, issue_queries
    assert json_at(by_name, "Astronomy Weekly", "totalCount") == 5
    assert _titles(json_at(by_name, "Astronomy Weekly")) == ["Astro #5", "Astro #4"]
    assert json_at(by_name, "Botany Monthly", "totalCount") == 3
    assert json_at(by_name, "Empty Gazette", "totalCount") == 0
    assert json_at(by_name, "Empty Gazette", "edges") == []


@pytest.mark.django_db
@pytest.mark.parametrize("ordering", [("?",), (Random(),)], ids=["name", "expression"])
def test_nested_keyset_window_pages_the_cursor_field_under_a_random_model_ordering(
    ordering: tuple[object, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A random ``Meta.ordering`` on a keyset target leaves the nested window planned.

    Nothing orders the child queryset, so the connection's order is the declared
    ``cursor_field`` and the model default never reaches it: both pages stay one
    batched ``ROW_NUMBER() OVER`` statement with no random function, edge for
    edge the pages the shipped ordering serves.
    """
    _seed_periodicals()
    shipped_first = _nested_by_periodical(first=2)
    shipped_after = _nested_by_periodical(
        first=2,
        after=json_at(shipped_first, "Astronomy Weekly", "pageInfo", "endCursor"),
    )
    monkeypatch.setattr(models.Issue._meta, "ordering", ordering)
    with CaptureQueriesContext(connection) as first_captured:
        first = _nested_by_periodical(first=2)
    with CaptureQueriesContext(connection) as after_captured:
        after = _nested_by_periodical(
            first=2,
            after=json_at(first, "Astronomy Weekly", "pageInfo", "endCursor"),
        )
    issue_sql = [
        q["sql"]
        for captured in (first_captured, after_captured)
        for q in captured.captured_queries
        if "library_issue" in q["sql"]
    ]
    assert [("OVER (" in sql, "RAND" in sql.upper()) for sql in issue_sql] == [
        (True, False),
        (True, False),
    ], issue_sql
    assert [first, after] == [shipped_first, shipped_after]


@pytest.mark.django_db
def test_nested_keyset_after_uniform_value_position_and_pre_seek_totals() -> None:
    """One ``after:`` cursor re-positions EVERY partition by value; totals stay pre-seek."""
    _seed_periodicals()
    astro_cursor = json_at(
        _nested_by_periodical(first=2),
        "Astronomy Weekly",
        "pageInfo",
        "endCursor",
    )
    with CaptureQueriesContext(connection) as ctx:
        by_name = _nested_by_periodical(first=2, after=astro_cursor)
    issue_queries = [q["sql"] for q in ctx.captured_queries if "library_issue" in q["sql"]]
    assert len(issue_queries) == 1, issue_queries

    # Cursor sits at astro#4: astronomy continues #3, #2; botany's rows past
    # the VALUE position (number < 4) are #3, #2 - the uniform semantics.
    astronomy = json_at(by_name, "Astronomy Weekly")
    assert _titles(astronomy) == ["Astro #3", "Astro #2"]
    assert json_at(astronomy, "totalCount") == 5  # PRE-seek partition count
    assert json_at(astronomy, "pageInfo", "hasPreviousPage") is True
    assert json_at(astronomy, "pageInfo", "hasNextPage") is True
    botany = json_at(by_name, "Botany Monthly")
    assert _titles(botany) == ["Bot #3", "Bot #2"]
    assert json_at(botany, "totalCount") == 3
    # Childless parent with a cursor: empty page, hasPrev from the cursor.
    empty = json_at(by_name, "Empty Gazette")
    assert json_at(empty, "edges") == []
    assert json_at(empty, "totalCount") == 0
    assert json_at(empty, "pageInfo", "hasPreviousPage") is True
    assert json_at(empty, "pageInfo", "hasNextPage") is False


@pytest.mark.django_db
def test_nested_keyset_marker_distinguishes_pre_cursor_only_parents() -> None:
    """A parent whose rows ALL precede the cursor serves an empty page with its true count."""
    _seed_periodicals()
    # Cursor past astro#2 (deep page): botany's numbers 3..1 all precede it? No -
    # under (-number, id), "past the cursor" means SMALLER numbers. Take the
    # cursor at astro#1 (the last astronomy row): the only rows past it are
    # bot#1 (number 1, larger pk). Botany keeps a page; give botany a cursor
    # past ALL its rows instead by cursoring at the global tail.
    tail_cursor = json_at(_root_page(last=1), "pageInfo", "startCursor")  # bot#1, the final row
    by_name = _nested_by_periodical(first=2, after=tail_cursor)
    astronomy = json_at(by_name, "Astronomy Weekly")
    assert json_at(astronomy, "edges") == []
    assert json_at(astronomy, "totalCount") == 5  # the abs-first marker row carried it
    assert json_at(astronomy, "pageInfo", "hasNextPage") is False
    assert json_at(astronomy, "pageInfo", "hasPreviousPage") is True


@pytest.mark.django_db
def test_nested_keyset_count_free_page_uses_probe_not_partition_count() -> None:
    """A ``hasNextPage``-only nested page runs count-free (seek in WHERE + n+1 probe)."""
    _seed_periodicals()
    astro_cursor = json_at(
        _nested_by_periodical(first=2),
        "Astronomy Weekly",
        "pageInfo",
        "endCursor",
    )
    query = """
    query ($after: String) {
      allLibraryPeriodicalsConnection(first: 10) {
        edges { node { name issuesConnection(first: 2, after: $after) {
          pageInfo { hasNextPage }
          edges { node { title } }
        } } }
      }
    }
    """
    with CaptureQueriesContext(connection) as ctx:
        data = _assert_graphql_success(query, variables={"after": astro_cursor})
    issue_queries = [q["sql"] for q in ctx.captured_queries if "library_issue" in q["sql"]]
    assert len(issue_queries) == 1, issue_queries
    # Count-free shape: the seek narrows the base WHERE (no FILTER'd running
    # count, no partition COUNT) and the probe sentinel answers hasNextPage.
    assert "FILTER" not in issue_queries[0]
    assert "COUNT" not in issue_queries[0].upper().replace("ROW_NUMBER", "")
    by_name = {
        json_str(e, "node", "name"): json_object(e, "node", "issuesConnection")
        for e in json_list(data, "allLibraryPeriodicalsConnection", "edges")
    }
    assert _titles(json_at(by_name, "Astronomy Weekly")) == ["Astro #3", "Astro #2"]
    assert json_at(by_name, "Astronomy Weekly", "pageInfo", "hasNextPage") is True
    # Botany's post-seek set (numbers < 4) is three rows; the page of two
    # leaves Bot #1 past the sentinel.
    assert json_at(by_name, "Botany Monthly", "pageInfo", "hasNextPage") is True


@pytest.mark.django_db
def test_nested_keyset_unselected_cursor_column_is_not_lazy_loaded_per_edge() -> None:
    """A node selection omitting the cursor columns still mints cursors in ONE query.

    ``IssueType.cursor_field = ("-number", "id")``. When the node selection does
    NOT select ``number`` (only ``title``), the scalar-only window projection
    would ``.only("title", "id")`` and DEFER ``number`` - so minting each edge's
    value cursor would lazy-load ``number`` once PER edge (an N+1). The already
    -implemented ``_extend_only_projection`` (which killed the strawberry-django
    ``annotate_ordering_fields`` port) folds the cursor columns back into the
    projection, so the whole nested window stays a single batched prefetch with
    zero per-edge lazy loads. Pinned here as live behavior.
    """
    _seed_periodicals()
    query = """
    {
      allLibraryPeriodicalsConnection(first: 10) {
        edges { node { name issuesConnection(first: 3) {
          edges { cursor node { title } }
        } } }
      }
    }
    """
    with CaptureQueriesContext(connection) as ctx:
        data = _assert_graphql_success(query)
    issue_queries = [q["sql"] for q in ctx.captured_queries if "library_issue" in q["sql"]]
    # One batched window prefetch: no per-edge lazy-load of the deferred
    # ``number`` cursor column.
    assert len(issue_queries) == 1, issue_queries
    # Cursors still mint correctly for every edge (the projection carried the
    # cursor columns despite ``number`` not being selected).
    by_name = {
        json_str(e, "node", "name"): json_object(e, "node", "issuesConnection")
        for e in json_list(data, "allLibraryPeriodicalsConnection", "edges")
    }
    astronomy_edges = json_list(by_name, "Astronomy Weekly", "edges")
    assert [json_at(e, "node", "title") for e in astronomy_edges] == [
        "Astro #5",
        "Astro #4",
        "Astro #3",
    ]
    assert all(json_at(edge, "cursor") for edge in astronomy_edges)


@pytest.mark.django_db
def test_nested_keyset_first_zero_serves_flags_from_markers() -> None:
    """``first: 0`` with a cursor: empty edges, true pre-seek count, value-domain flags."""
    _seed_periodicals()
    astro_cursor = json_at(
        _nested_by_periodical(first=2),
        "Astronomy Weekly",
        "pageInfo",
        "endCursor",
    )
    by_name = _nested_by_periodical(first=0, after=astro_cursor)
    astronomy = json_at(by_name, "Astronomy Weekly")
    assert json_at(astronomy, "edges") == []
    assert json_at(astronomy, "totalCount") == 5
    assert json_at(astronomy, "pageInfo", "hasNextPage") is True  # rows past the cursor exist
    assert json_at(astronomy, "pageInfo", "hasPreviousPage") is True
    empty = json_at(by_name, "Empty Gazette")
    assert json_at(empty, "totalCount") == 0
    assert json_at(empty, "pageInfo", "hasNextPage") is False


@pytest.mark.django_db
def test_nested_keyset_backward_falls_back_per_parent_with_same_cursors() -> None:
    """``last:`` nested pages resolve per-parent through the SAME codec (parity)."""
    _seed_periodicals()
    query = """
    {
      allLibraryPeriodicalsConnection(first: 10) {
        edges { node { name issuesConnection(last: 2) {
          pageInfo { hasPreviousPage hasNextPage endCursor }
          edges { cursor node { title } }
        } } }
      }
    }
    """
    data = _assert_graphql_success(query)
    by_name = {
        json_str(e, "node", "name"): json_object(e, "node", "issuesConnection")
        for e in json_list(data, "allLibraryPeriodicalsConnection", "edges")
    }
    astronomy = json_at(by_name, "Astronomy Weekly")
    assert _titles(astronomy) == ["Astro #2", "Astro #1"]
    assert json_at(astronomy, "pageInfo", "hasPreviousPage") is True
    assert json_at(astronomy, "pageInfo", "hasNextPage") is False
    # Cross-path parity: a cursor minted by the per-parent fallback replays
    # against the WINDOWED forward path (same codec, same bytes).
    forward = _nested_by_periodical(first=2, after=json_at(astronomy, "edges", 0, "cursor"))
    assert _titles(json_at(forward, "Astronomy Weekly")) == ["Astro #1"]


NESTED_BACKWARD_QUERY = """
query ($last: Int, $before: String) {
  allLibraryPeriodicalsConnection(first: 10) {
    edges { node { name issuesConnection(last: $last, before: $before) {
      pageInfo { hasPreviousPage hasNextPage }
      edges { cursor node { title } }
    } } }
  }
}
"""


@pytest.mark.django_db
def test_nested_keyset_before_pages_backward_per_parent() -> None:
    """Nested ``before:`` (head + interior) rides the per-parent fallback with root parity.

    Nested ``before:`` is unwindowable, so it falls back to the same
    ``_resolve_keyset_connection`` codec the root uses. Both flags and edges
    must therefore match the root backward contract per parent.
    """
    _seed_periodicals()
    # Mint cursors from a full forward page: order is newest-first, #5..#1.
    forward = json_at(_nested_by_periodical(first=5), "Astronomy Weekly")
    assert _titles(forward) == [
        "Astro #5",
        "Astro #4",
        "Astro #3",
        "Astro #2",
        "Astro #1",
    ]
    cursors = {
        json_at(edge, "node", "title"): json_at(edge, "cursor")
        for edge in json_list(forward, "edges")
    }

    def _astro(**variables: object) -> JSONObject:
        data = _assert_graphql_success(NESTED_BACKWARD_QUERY, variables=variables)
        return next(
            json_object(edge, "node", "issuesConnection")
            for edge in json_list(data, "allLibraryPeriodicalsConnection", "edges")
            if json_at(edge, "node", "name") == "Astronomy Weekly"
        )

    # Interior cursor: the two rows before #2 are #4, #3 (both flags True).
    interior = _astro(last=2, before=json_at(cursors, "Astro #2"))
    assert _titles(interior) == ["Astro #4", "Astro #3"]
    assert json_at(interior, "pageInfo", "hasPreviousPage") is True
    assert json_at(interior, "pageInfo", "hasNextPage") is True

    # Head cursor: only #5 precedes #4, so the head page reports no previous rows.
    head = _astro(last=2, before=json_at(cursors, "Astro #4"))
    assert _titles(head) == ["Astro #5"]
    assert json_at(head, "pageInfo", "hasPreviousPage") is False
    assert json_at(head, "pageInfo", "hasNextPage") is True


@pytest.mark.django_db
def test_nested_keyset_divergent_aliases_each_decode_their_own_cursor() -> None:
    """Divergent aliased ``after:`` payloads window independently (per-key scheme)."""
    _seed_periodicals()
    first_pages = _nested_by_periodical(first=2)
    astro_cursor = json_at(first_pages, "Astronomy Weekly", "pageInfo", "endCursor")
    query = """
    query ($c: String!) {
      allLibraryPeriodicalsConnection(first: 10) {
        edges { node { name
          head: issuesConnection(first: 2) { edges { node { title } } }
          tail: issuesConnection(first: 2, after: $c) { edges { node { title } } }
        } }
      }
    }
    """
    data = _assert_graphql_success(query, variables={"c": astro_cursor})
    astronomy = next(
        json_at(e, "node")
        for e in json_list(data, "allLibraryPeriodicalsConnection", "edges")
        if json_at(e, "node", "name") == "Astronomy Weekly"
    )
    assert [json_at(e, "node", "title") for e in json_list(astronomy, "head", "edges")] == [
        "Astro #5",
        "Astro #4",
    ]
    assert [json_at(e, "node", "title") for e in json_list(astronomy, "tail", "edges")] == [
        "Astro #3",
        "Astro #2",
    ]


@pytest.mark.django_db
def test_keyset_cursor_decode_is_permission_aware() -> None:
    """A staff-minted cursor replays for anonymous viewers over ONLY their rows."""
    astronomy, _botany, _empty = _seed_periodicals()
    models.Issue.objects.create(
        periodical=astronomy,
        number=6,
        title="Embargoed #6",
        embargoed=True,
    )

    staff = User.objects.create_user(username="keyset-staff", password="pw", is_staff=True)
    client = TestClient()
    with client.login(staff):
        staff_result = client.query(ROOT_PAGE_QUERY, variables={"first": 2}).response
    staff_page = json_at(response_json(staff_result), "data", "allLibraryIssuesConnection")
    # Staff sees the embargoed issue first (number 6 sorts before 5).
    assert _titles(staff_page) == ["Embargoed #6", "Astro #5"]
    assert json_at(staff_page, "totalCount") == 9
    staff_cursor = json_at(staff_page, "pageInfo", "startCursor")  # points AT the embargoed row

    # Anonymous replay: the seek applies to the anonymous-visibility queryset -
    # no embargoed row leaks, the count is the viewer's, pagination proceeds.
    anon_page = _root_page(first=3, after=staff_cursor)
    assert _titles(anon_page) == ["Astro #5", "Astro #4", "Astro #3"]
    assert json_at(anon_page, "totalCount") == 8
    assert all("Embargoed" not in title for title in _titles(anon_page))


@pytest.mark.django_db
def test_root_keyset_order_by_related_path_seeks_via_annotation() -> None:
    """A related-path ``orderBy:`` mints/seeks through the annotated join column."""
    _seed_periodicals()
    query = """
    query ($after: String) {
      allLibraryIssuesConnection(
        first: 3
        after: $after
        orderBy: [{ periodical: { name: ASC } }, { number: ASC }]
      ) {
        pageInfo { endCursor hasNextPage }
        edges { node { title } }
      }
    }
    """
    data = _assert_graphql_success(query)
    page = json_at(data, "allLibraryIssuesConnection")
    assert [json_at(e, "node", "title") for e in json_list(page, "edges")] == [
        "Astro #1",
        "Astro #2",
        "Astro #3",
    ]
    data = _assert_graphql_success(
        query,
        variables={"after": json_at(page, "pageInfo", "endCursor")},
    )
    page2 = json_at(data, "allLibraryIssuesConnection")
    assert [json_at(e, "node", "title") for e in json_list(page2, "edges")] == [
        "Astro #4",
        "Astro #5",
        "Bot #1",
    ]


@pytest.mark.django_db
def test_root_keyset_unbounded_after_caps_at_relay_max_results() -> None:
    """``after:`` with no ``first`` mirrors ``ListConnection``'s max-results cap."""
    _seed_periodicals()
    cursor = json_at(_root_page(first=1), "pageInfo", "endCursor")
    page = _root_page(after=cursor)
    # relay_max_results (100) far exceeds the seven remaining rows.
    assert len(json_list(page, "edges")) == 7
    assert json_at(page, "pageInfo", "hasNextPage") is False
    assert json_at(page, "pageInfo", "hasPreviousPage") is True


@pytest.mark.django_db
def test_root_keyset_omitted_pagination_returns_the_full_set_under_the_cap() -> None:
    """Omitting ``first`` / ``last`` / ``after`` / ``before`` serves every row under the Relay cap."""
    _seed_periodicals()
    data = _assert_graphql_success(
        """
        {
          allLibraryIssuesConnection {
            pageInfo { hasNextPage hasPreviousPage }
            edges { node { title } }
          }
        }
        """,
    )
    page = json_at(data, "allLibraryIssuesConnection")
    assert _titles(page) == [
        "Astro #5",
        "Astro #4",
        "Astro #3",
        "Bot #3",
        "Astro #2",
        "Bot #2",
        "Astro #1",
        "Bot #1",
    ]
    assert json_at(page, "pageInfo") == {"hasNextPage": False, "hasPreviousPage": False}


@pytest.mark.django_db
def test_nested_keyset_omitted_first_caps_at_relay_max_results() -> None:
    """Optimized nested pages apply the same default cap as the root slicer."""
    periodical = models.Periodical.objects.create(name="Large Periodical")
    for number in range(1, 106):
        models.Issue.objects.create(
            periodical=periodical,
            number=number,
            title=f"Issue #{number}",
        )

    first_page = json_at(_nested_by_periodical(), "Large Periodical")
    assert len(json_list(first_page, "edges")) == 100
    assert json_at(first_page, "pageInfo", "hasNextPage") is True

    cursor = json_at(_nested_by_periodical(first=1), "Large Periodical", "pageInfo", "endCursor")
    after_page = json_at(_nested_by_periodical(after=cursor), "Large Periodical")
    assert len(json_list(after_page, "edges")) == 100
    assert json_at(after_page, "pageInfo", "hasNextPage") is True
    assert json_at(after_page, "pageInfo", "hasPreviousPage") is True


@pytest.mark.django_db
def test_nested_keyset_window_hides_embargoed_rows_and_counts_them_out() -> None:
    """The keyset window is built from the SAME definition that answered the hook.

    ``PeriodicalType.issuesConnection`` is a synthesized relation connection in
    keyset mode: the walker decides whether ``IssueType.get_queryset`` runs over
    the child queryset, then derives the window's cursor vocabulary - columns,
    ordering, fingerprint - from the target's declared ``cursor_field``. Both
    answers come from the child definition the relation was resolved through, so
    a keyset page cannot be partitioned over a population its visibility hook
    never saw.

    The embargoed issue is the newest one in its partition, so under the
    declared newest-first order it would be the FIRST edge of that page and the
    page's ``endCursor`` would point at a row the viewer may not see. It is
    absent, the partition count is the viewer's, and the whole page is still one
    batched query - the planned window, not a per-parent fallback.
    """
    astronomy, _botany, _empty = _seed_periodicals()
    models.Issue.objects.create(
        periodical=astronomy,
        number=6,
        title="Embargoed #6",
        embargoed=True,
    )

    with CaptureQueriesContext(connection) as ctx:
        by_name = _nested_by_periodical(first=2)
    issue_queries = [q["sql"] for q in ctx.captured_queries if 'FROM "library_issue"' in q["sql"]]
    assert len(issue_queries) == 1, issue_queries

    astro = json_at(by_name, "Astronomy Weekly")
    assert _titles(astro) == ["Astro #5", "Astro #4"]
    assert json_at(astro, "totalCount") == 5
    assert json_at(by_name, "Botany Monthly", "totalCount") == 3


@pytest.mark.django_db
def test_nested_keyset_window_keeps_embargoed_rows_for_staff() -> None:
    """The same window returns the embargoed issue first once the viewer is staff.

    The absence above is ``IssueType.get_queryset``'s non-staff branch running
    inside the plan, not the window declining to reach the row: under the declared
    newest-first order the embargoed issue leads its partition here, and the
    partition count is the staff viewer's.
    """
    astronomy, _botany, _empty = _seed_periodicals()
    models.Issue.objects.create(
        periodical=astronomy,
        number=6,
        title="Embargoed #6",
        embargoed=True,
    )
    staff = User.objects.create_user(username="nested-staff", password="pw", is_staff=True)
    client = TestClient()
    with client.login(staff), CaptureQueriesContext(connection) as ctx:
        payload = response_json(client.query(NESTED_QUERY, variables={"first": 2}).response)
    assert payload.get("errors") is None, payload
    by_name = {
        json_str(edge, "node", "name"): json_object(edge, "node", "issuesConnection")
        for edge in json_list(payload, "data", "allLibraryPeriodicalsConnection", "edges")
    }
    issue_queries = [q["sql"] for q in ctx.captured_queries if 'FROM "library_issue"' in q["sql"]]
    assert len(issue_queries) == 1, issue_queries

    astro = json_at(by_name, "Astronomy Weekly")
    assert _titles(astro) == ["Embargoed #6", "Astro #5"]
    assert json_at(astro, "totalCount") == 6


_HOLDER_PAGE_QUERY = """
query ($first: Int, $after: String) {
  issues(first: $first, after: $after) {
    totalCount
    pageInfo { hasNextPage endCursor }
    edges { cursor node { title } }
  }
}
"""


@pytest.mark.django_db
def test_keyset_list_source_is_rejected_over_http() -> None:
    """A keyset connection resolver that returns a list is refused on the wire."""

    def _list_resolver(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> list[models.Issue]:
        return list(models.Issue.objects.all())

    _seed_three_issues()
    payload = _post_holder(
        _issue_holder_schema(_list_resolver),
        "{ issues(first: 1) { edges { cursor } } }",
    )
    assert json_at(payload, "data") is None, payload
    assert "errors" in payload, payload
    assert "must return a QuerySet" in json_str(payload, "errors", 0, "message")


@pytest.mark.django_db
def test_keyset_pre_sliced_source_is_rejected_over_http() -> None:
    """A keyset connection resolver that returns an already-sliced QuerySet is refused."""

    def _sliced_resolver(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> QuerySet[models.Issue]:
        return models.Issue.objects.all()[:5]

    payload = _post_holder(
        _issue_holder_schema(_sliced_resolver),
        "{ issues(first: 1) { edges { cursor } } }",
    )
    assert json_at(payload, "data") is None, payload
    assert "errors" in payload, payload
    assert "already-sliced" in json_str(payload, "errors", 0, "message")


@pytest.mark.django_db(transaction=True)
async def test_async_keyset_first_page_slices_and_counts() -> None:
    """An async keyset field slices the first page through the async engine and ``acount``."""

    async def _async_resolver(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> QuerySet[models.Issue]:
        return models.Issue.objects.all()

    await sync_to_async(_seed_three_issues)()
    payload = await _post_async_holder(
        _issue_holder_schema(_async_resolver),
        _HOLDER_PAGE_QUERY,
        variables={"first": 2},
    )
    assert payload.get("errors") is None, payload
    page = json_at(payload, "data", "issues")
    assert json_at(page, "totalCount") == 3
    assert json_at(page, "pageInfo", "hasNextPage") is True
    assert [json_at(edge, "node", "title") for edge in json_list(page, "edges")] == ["i3", "i2"]


@pytest.mark.django_db(transaction=True)
async def test_async_keyset_after_cursor_continues_the_page() -> None:
    """A minted async keyset cursor round-trips on the same async field."""

    async def _async_resolver(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> QuerySet[models.Issue]:
        return models.Issue.objects.all()

    await sync_to_async(_seed_three_issues)()
    schema = _issue_holder_schema(_async_resolver)
    first = await _post_async_holder(schema, _HOLDER_PAGE_QUERY, variables={"first": 2})
    assert first.get("errors") is None, first
    cursor = json_at(first, "data", "issues", "pageInfo", "endCursor")
    second = await _post_async_holder(
        schema,
        _HOLDER_PAGE_QUERY,
        variables={"first": 2, "after": cursor},
    )
    assert second.get("errors") is None, second
    assert [
        json_at(edge, "node", "title") for edge in json_list(second, "data", "issues", "edges")
    ] == ["i1"]


@pytest.mark.django_db(transaction=True)
async def test_async_keyset_total_count_only() -> None:
    """A totalCount-only async keyset query counts via ``acount`` and fetches no edges."""

    async def _async_resolver(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> QuerySet[models.Issue]:
        return models.Issue.objects.all()

    await sync_to_async(_seed_three_issues)()
    payload = await _post_async_holder(
        _issue_holder_schema(_async_resolver),
        "{ issues { totalCount } }",
    )
    assert payload.get("errors") is None, payload
    assert json_at(payload, "data", "issues") == {"totalCount": 3}


@pytest.mark.django_db(transaction=True)
async def test_async_keyset_deferred_cursor_column_is_loaded() -> None:
    """Cursor minting on an async keyset field must not lazy-load a deferred order column."""

    async def _async_resolver(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> QuerySet[models.Issue]:
        return models.Issue.objects.defer("number", "title")

    await sync_to_async(_seed_three_issues)()
    payload = await _post_async_holder(
        _issue_holder_schema(_async_resolver),
        "{ issues(first: 1) { edges { cursor } } }",
    )
    assert payload.get("errors") is None, payload
    assert len(json_list(payload, "data", "issues", "edges")) == 1
    assert json_at(payload, "data", "issues", "edges", 0, "cursor")


# A target ``get_queryset`` that orders the child queryset makes THAT order the
# connection's effective order, ahead of the declared ``cursor_field``. The rows
# below mount a test-local keyset child (``cursor_field = ("id",)``) whose hook
# orders by ``-id`` (a unique column) or ``title`` (non-unique: the pk tiebreak
# decides between the two ``x`` rows), under a reverse-FK parent
# (``Periodical.issues``) and an M2M parent (``Genre.books``), on the
# ``/graphql-test/`` holder.

#: ``(child model, parent model, relation, label field)`` per relation shape.
_HOOK_SHAPES = {
    "fk": (
        models.Issue,
        models.Periodical,
        "issues",
        "number",
    ),
    "m2m": (
        models.Book,
        models.Genre,
        "books",
        "subtitle",
    ),
}

_HOOK_ORDERS = {"-id": ("-id",), "title": ("title",)}

#: A hook order the hook then ``.reverse()``s (``None``: a bare ``.reverse()``).
_REVERSED_HOOK_ORDERS: dict[str, tuple[str, ...] | None] = {
    "id": ("id",),
    "title": ("title",),
    "-id": ("-id",),
    "bare": None,
}

#: A hook order through a required forward FK: its cursor value rides an annotation.
_RELATED_HOOK_ORDERS = {"fk": ("periodical__name", "-id"), "m2m": ("shelf__code", "-id")}

_INVALID_AFTER = "Argument 'after' contains an invalid cursor for this connection."

_UNANCHORABLE_ORDER = (
    "This connection uses keyset cursors (Meta.cursor_field), which require every "
    "ordering entry to be a database column; the requested order cannot anchor stable "
    "cursors. Remove the unsupported orderBy entry or paginate under the default order."
)


#: A hook step ordering the child queryset some other way than ``order_by``.
_ChildOrder = Callable[
    [QuerySet[models.Issue | models.Book]],
    QuerySet[models.Issue | models.Book],
]

#: The strictness error for each shape's nested connection left to the per-parent pipeline.
_RANDOM_ORDER_N_PLUS_ONE = {
    shape: f"Unplanned N+1: {relation} (not window-planned; resolving per-parent)"
    for shape, relation in (("fk", "issues"), ("m2m", "books"))
}


def _hook_order_schema(
    shape: str,
    hook_order: tuple[str | Combinable, ...] | None,
    *,
    optimizer: bool = True,
    strictness: str = "off",
    distinct: bool = False,
    reverse: bool = False,
    keyset: bool = True,
    orderable: bool = False,
    order_hook: _ChildOrder | None = None,
) -> strawberry.Schema:
    """Holder schema: ``parents`` (a planned list root) plus a root ``children`` connection.

    The child type declares ``cursor_field = ("id",)`` (an offset connection
    when not ``keyset``) and a ``get_queryset`` ordering by ``hook_order``
    (left unordered when ``None``) or through ``order_hook`` when one is given,
    then ``.reverse()``'d when ``reverse`` (``.distinct()`` too when
    ``distinct``, which the planner refuses to window). ``orderable`` adds an
    ``orderBy:`` argument over the child's columns.
    """
    child_model, parent_model, relation, label = _HOOK_SHAPES[shape]

    def hook(
        _cls: type[DjangoType],
        queryset: QuerySet[models.Issue | models.Book],
        _info: strawberry.Info[object, object],
    ) -> QuerySet[models.Issue | models.Book]:
        if order_hook is not None:
            ordered = order_hook(queryset)
        elif hook_order is None:
            ordered = queryset
        else:
            ordered = queryset.order_by(*hook_order)
        if reverse:
            ordered = ordered.reverse()
        return ordered.distinct() if distinct else ordered

    registry.clear()
    meta_extra: dict[str, object] = {"connection": {"total_count": True}}
    if keyset:
        meta_extra["cursor_field"] = ("id",)
    if orderable:
        meta_extra["orderset_class"] = type(
            "HookOrderedChildOrder",
            (OrderSet,),
            {"Meta": type("Meta", (), {"model": child_model, "fields": ["id", label]})},
        )
    child_type = make_django_type(
        "HookOrderedChildType",
        child_model,
        ("id", label),
        meta_extra=meta_extra,
        namespace_extra={"get_queryset": classmethod(hook)},
    )
    parent_type = make_django_type(
        "HookOrderedParentType",
        parent_model,
        ("id", "name", relation),
        meta_extra={"relation_shapes": {relation: "connection"}},
    )
    finalize_django_types()

    async def async_parents(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> QuerySet[models.Periodical | models.Genre]:
        return parent_model.objects.order_by("name")

    def resolve_parents() -> QuerySet[models.Periodical | models.Genre]:
        return parent_model.objects.order_by("name")

    @strawberry.type
    class Query:
        children = DjangoConnectionField(child_type)
        # The async engine's planned root: a connection over an ``async def``
        # resolver (the async rows read ``parentsConnection``).
        parents_connection = DjangoConnectionField(parent_type, resolver=async_parents)
        parents: QuerySet[models.Periodical | models.Genre] = strawberry.field(
            resolver=resolve_parents,
            graphql_type=list[parent_type],
        )

    optimizer_extension = DjangoOptimizerExtension(strictness=strictness) if optimizer else None
    extensions = [lambda: optimizer_extension] if optimizer_extension is not None else []
    return strawberry.Schema(query=Query, config=strawberry_config(), extensions=extensions)


def _seed_hook_order_rows(shape: str, *, with_b: bool = True) -> None:
    """Parent ``A``: children labelled 1, 2, 3 titled ``y``, ``x``, ``x`` (in pk order).

    Parent ``B`` (``with_b``) holds one child labelled 1 titled ``a``, created
    last, so it sorts BEFORE ``A``'s rows under ``title`` and AFTER them under
    ``-id``: an ``after:`` cursor minted on ``A``'s page leaves ``B`` nothing.
    """
    rows = [("A", 1, "y"), ("A", 2, "x"), ("A", 3, "x")]
    if with_b:
        rows.append(("B", 1, "a"))
    names = dict.fromkeys(row[0] for row in rows)
    if shape == "fk":
        periodicals = {name: models.Periodical.objects.create(name=name) for name in names}
        for name, label, title in rows:
            models.Issue.objects.create(periodical=periodicals[name], number=label, title=title)
        return
    genres = {name: models.Genre.objects.create(name=name) for name in names}
    branch = models.Branch.objects.create(name="Hook Branch")
    for name, label, title in rows:
        # ``(shelf, title)`` is unique, so each book gets its own shelf.
        shelf = models.Shelf.objects.create(code=f"{name}-{label}", branch=branch)
        book = models.Book.objects.create(title=title, subtitle=str(label), shelf=shelf)
        book.genres.add(genres[name])


def _nested_hook_query(shape: str, *, total_count: bool = False) -> str:
    _child_model, _parent_model, relation, label = _HOOK_SHAPES[shape]
    count = "totalCount " if total_count else ""
    return (
        "query ($first: Int, $after: String) { parents { name "
        f"{relation}Connection(first: $first, after: $after) {{ {count}"
        "pageInfo { hasNextPage endCursor } "
        f"edges {{ cursor node {{ {label} }} }} }} }} }}"
    )


def _nested_hook_pages(shape: str, payload: JSONObject) -> dict[str, JSONObject]:
    assert payload.get("errors") is None, payload
    relation = _HOOK_SHAPES[shape][2]
    return {
        json_str(parent, "name"): json_object(parent, f"{relation}Connection")
        for parent in json_list(payload, "data", "parents")
    }


def _labels(shape: str, connection_payload: object) -> list[str]:
    label = _HOOK_SHAPES[shape][3]
    return [str(json_at(edge, "node", label)) for edge in json_list(connection_payload, "edges")]


def _table_statements(captured: CaptureQueriesContext, table: str) -> list[str]:
    return [q["sql"] for q in captured.captured_queries if f'FROM "{table}"' in q["sql"]]


def _child_table(shape: str) -> str:
    return _HOOK_SHAPES[shape][0]._meta.db_table


def _parent_table(shape: str) -> str:
    return _HOOK_SHAPES[shape][1]._meta.db_table


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["fk", "m2m"])
@pytest.mark.parametrize(
    ("hook", "page_one", "page_two"),
    [("-id", ["3", "2"], ["1"]), ("title", ["2", "3"], ["1"])],
    ids=["unique-column", "pk-tiebreak"],
)
def test_nested_keyset_window_pages_under_the_hook_order(
    shape: str,
    hook: str,
    page_one: list[str],
    page_two: list[str],
) -> None:
    """A hook-ordered nested window seeks under the hook order: page 2 serves the rest.

    Page 1's ``endCursor`` replays as ``after:``: ``A``'s rows are served once
    each across the two pages and ``B``'s only row sits before the cursor
    position. Each page is one parent statement and ONE child statement for
    both parents (the batched window, no per-parent fallback).
    """
    _seed_hook_order_rows(shape)
    schema = _hook_order_schema(shape, _HOOK_ORDERS[hook])
    query = _nested_hook_query(shape)
    with CaptureQueriesContext(connection) as first_captured:
        first = _nested_hook_pages(shape, _post_holder(schema, query, variables={"first": 2}))
    with CaptureQueriesContext(connection) as second_captured:
        second = _nested_hook_pages(
            shape,
            _post_holder(
                schema,
                query,
                variables={"first": 2, "after": json_at(first, "A", "pageInfo", "endCursor")},
            ),
        )

    assert [_labels(shape, json_at(first, "A")), _labels(shape, json_at(first, "B"))] == [
        page_one,
        ["1"],
    ]
    assert [_labels(shape, json_at(second, "A")), _labels(shape, json_at(second, "B"))] == [
        page_two,
        [],
    ]
    assert [
        json_at(first, "A", "pageInfo", "hasNextPage"),
        json_at(second, "A", "pageInfo", "hasNextPage"),
    ] == [True, False]
    for captured in (first_captured, second_captured):
        assert len(_table_statements(captured, _parent_table(shape))) == 1, (
            captured.captured_queries
        )
        assert len(_table_statements(captured, _child_table(shape))) == 1, (
            captured.captured_queries
        )


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["fk", "m2m"])
@pytest.mark.parametrize(
    "hook",
    [
        "-id",
        "title",
        "related",
        "id-reversed",
        "title-reversed",
    ],
)
def test_hook_ordered_cursor_bytes_match_across_root_window_and_per_parent_paths(
    shape: str,
    hook: str,
) -> None:
    """The same row mints the same cursor bytes from every path, and a root cursor replays.

    One parent, so the root ``children`` connection and the nested connection
    serve the same three rows: the root slicer, the planned window (optimizer
    on) and the per-parent pipeline (optimizer off) each mint one cursor per
    row, and the three maps are equal. The root's first cursor then pages
    the PLANNED nested window: one child statement serving the remaining rows.
    The ``related`` order reads its first cursor value through a forward FK,
    which the window, the seek and the mint carry as an annotation; a
    ``-reversed`` hook ``.reverse()``s its order, which every path pages under
    the same materialized order.
    """
    _seed_hook_order_rows(shape, with_b=False)
    reverse = hook.endswith("-reversed")
    if hook == "related":
        hook_order = _RELATED_HOOK_ORDERS[shape]
    elif reverse:
        hook_order = _REVERSED_HOOK_ORDERS[hook.removesuffix("-reversed")]
    else:
        hook_order = _HOOK_ORDERS[hook]
    relation, label = _HOOK_SHAPES[shape][2], _HOOK_SHAPES[shape][3]
    query = (
        f"{{ children(first: 3) {{ edges {{ cursor node {{ {label} }} }} }} "
        f"parents {{ {relation}Connection(first: 3) {{ edges {{ cursor node {{ {label} }} }} }} }} }}"
    )

    def cursors(payload: JSONObject) -> tuple[dict[str, str], dict[str, str]]:
        assert payload.get("errors") is None, payload
        root = json_list(payload, "data", "children", "edges")
        nested = json_list(payload, "data", "parents", 0, f"{relation}Connection", "edges")
        return (
            {str(json_at(edge, "node", label)): json_str(edge, "cursor") for edge in root},
            {str(json_at(edge, "node", label)): json_str(edge, "cursor") for edge in nested},
        )

    # Each build re-registers the child type, so the per-parent schema is used
    # up before the planned one is built.
    root_off, per_parent = cursors(
        _post_holder(
            _hook_order_schema(shape, hook_order, optimizer=False, reverse=reverse),
            query,
        ),
    )
    planned_schema = _hook_order_schema(shape, hook_order, reverse=reverse)
    root, planned = cursors(_post_holder(planned_schema, query))
    assert sorted(root) == ["1", "2", "3"]
    assert root_off == root
    assert planned == root
    assert per_parent == root

    first_label = next(iter(root))
    with CaptureQueriesContext(connection) as captured:
        replayed = _nested_hook_pages(
            shape,
            _post_holder(
                planned_schema,
                _nested_hook_query(shape),
                variables={"first": 3, "after": root[first_label]},
            ),
        )
    assert _labels(shape, json_at(replayed, "A")) == [key for key in root if key != first_label]
    assert len(_table_statements(captured, _child_table(shape))) == 1, captured.captured_queries


@pytest.mark.django_db
def test_hook_ordered_nested_total_count_stays_pre_seek_on_page_two() -> None:
    """A counted page 2 under the hook order: rows after the cursor, totals of the whole set."""
    _seed_hook_order_rows("fk")
    schema = _hook_order_schema("fk", _HOOK_ORDERS["title"])
    query = _nested_hook_query("fk", total_count=True)
    first = _nested_hook_pages("fk", _post_holder(schema, query, variables={"first": 2}))
    with CaptureQueriesContext(connection) as captured:
        second = _nested_hook_pages(
            "fk",
            _post_holder(
                schema,
                query,
                variables={"first": 2, "after": json_at(first, "A", "pageInfo", "endCursor")},
            ),
        )
    assert [
        (_labels("fk", second[name]), json_at(second[name], "totalCount")) for name in ("A", "B")
    ] == [(["1"], 3), ([], 1)]
    assert len(_table_statements(captured, "library_issue")) == 1, captured.captured_queries


@pytest.mark.django_db
def test_hook_ordered_single_parent_fast_path_pages_on() -> None:
    """One parent: page 1 rides the single-parent fast path, its cursor seeks page 2 right."""
    _seed_hook_order_rows("fk", with_b=False)
    schema = _hook_order_schema("fk", _HOOK_ORDERS["-id"])
    query = _nested_hook_query("fk")
    with CaptureQueriesContext(connection) as first_captured:
        first = _nested_hook_pages("fk", _post_holder(schema, query, variables={"first": 2}))
    with CaptureQueriesContext(connection) as second_captured:
        second = _nested_hook_pages(
            "fk",
            _post_holder(
                schema,
                query,
                variables={"first": 2, "after": json_at(first, "A", "pageInfo", "endCursor")},
            ),
        )
    first_sql = _table_statements(first_captured, "library_issue")
    second_sql = _table_statements(second_captured, "library_issue")
    assert [_labels("fk", json_at(first, "A")), _labels("fk", json_at(second, "A"))] == [
        ["3", "2"],
        ["1"],
    ]
    assert [len(first_sql), len(second_sql)] == [1, 1]
    # The fast path is the plain ``LIMIT`` re-query; the seek page keeps the window.
    assert ["OVER (" in first_sql[0], "OVER (" in second_sql[0]] == [False, True]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("optimizer", "strictness"),
    [(True, "off"), (False, "off"), (True, "raise")],
    ids=["planned", "unplanned", "strict"],
)
@pytest.mark.parametrize("shape", ["fk", "m2m"])
@pytest.mark.parametrize(
    "hook_order",
    [(Lower("title"),), ("?",), (Random(),)],
    ids=["expression", "random-name", "random-expression"],
)
def test_unanchorable_hook_order_raises_the_root_keyset_error_nested(
    shape: str,
    hook_order: tuple[str | Combinable, ...],
    *,
    optimizer: bool,
    strictness: str,
) -> None:
    """An expression or random hook order is refused nested as at the root, on every mount.

    The planner leaves the relation to the per-parent pipeline and records it
    as accounted for, so even ``strictness="raise"`` surfaces the keyset error,
    not an N+1 error. A random order meets the keyset refusal before the
    planner's random-order fallback, which would leave the relation
    strictness-visible.
    """
    _seed_hook_order_rows(shape, with_b=False)
    schema = _hook_order_schema(
        shape,
        hook_order,
        optimizer=optimizer,
        strictness=strictness,
    )
    root = _post_holder(schema, "{ children(first: 1) { edges { cursor } } }")
    nested = _post_holder(schema, _nested_hook_query(shape), variables={"first": 1})
    assert [json_at(error, "message") for error in json_list(root, "errors")] == [
        _UNANCHORABLE_ORDER,
    ]
    assert [json_at(error, "message") for error in json_list(nested, "errors")] == [
        _UNANCHORABLE_ORDER,
    ]


#: Per hook shape, the relation the child orders by and the ``Meta.ordering`` its model
#: declares, which Django compiles that relation name into.
_RELATION_HOOK_ORDERS: dict[str, tuple[str, type[Model], tuple[str, ...]]] = {
    "fk": ("periodical", models.Periodical, ("-name",)),
    "m2m": ("shelf", models.Shelf, ("-code",)),
}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("optimizer", "strictness"),
    [(True, "off"), (False, "off"), (True, "raise")],
    ids=["planned", "unplanned", "strict"],
)
@pytest.mark.parametrize("shape", ["fk", "m2m"])
def test_relation_name_hook_order_stays_unanchorable_under_a_related_ordering(
    shape: str,
    *,
    optimizer: bool,
    strictness: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A relation name is refused as a keyset order even though Django orders it by columns.

    The related model's ``Meta.ordering`` is what the name compiles into, but the
    keyset vocabulary reads the order as written, at the root and nested alike: a
    relation is no cursor column, so both raise the root keyset error on every mount.
    """
    relation, related_model, related_ordering = _RELATION_HOOK_ORDERS[shape]
    monkeypatch.setattr(related_model._meta, "ordering", related_ordering)
    _seed_hook_order_rows(shape, with_b=False)
    schema = _hook_order_schema(
        shape,
        (relation,),
        optimizer=optimizer,
        strictness=strictness,
    )
    root = _post_holder(schema, "{ children(first: 1) { edges { cursor } } }")
    nested = _post_holder(schema, _nested_hook_query(shape), variables={"first": 1})
    assert [json_at(error, "message") for error in json_list(root, "errors")] == [
        _UNANCHORABLE_ORDER,
    ]
    assert [json_at(error, "message") for error in json_list(nested, "errors")] == [
        _UNANCHORABLE_ORDER,
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["fk", "m2m"])
@pytest.mark.parametrize(
    "hook_order",
    [("?",), (Random(),)],
    ids=["random-name", "random-expression"],
)
def test_random_hook_order_on_an_offset_relation_is_an_unplanned_access_under_strictness(
    shape: str,
    hook_order: tuple[str | Combinable, ...],
) -> None:
    """A random hook order leaves an offset relation unplanned and strictness-visible.

    With no ``cursor_field`` no keyset refusal comes first: the planner leaves
    the relation to the per-parent pipeline without recording it as accounted
    for, so ``strictness="raise"`` reports the per-parent access as an unplanned
    N+1, while the root connection, which orders its one page query once, serves.
    """
    _seed_hook_order_rows(shape, with_b=False)
    schema = _hook_order_schema(shape, hook_order, keyset=False, strictness="raise")
    root = _post_holder(schema, "{ children(first: 1) { edges { cursor } } }")
    nested = _post_holder(schema, _nested_hook_query(shape), variables={"first": 1})
    assert root.get("errors") is None, root
    assert [json_at(error, "message") for error in json_list(nested, "errors")] == [
        _RANDOM_ORDER_N_PLUS_ONE[shape],
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["garbage", "offset", "tampered"])
@pytest.mark.parametrize("shape", ["fk", "m2m"])
def test_malformed_cursor_on_a_refused_keyset_relation_is_the_cursor_error_under_strictness(
    shape: str,
    kind: str,
) -> None:
    """A relation the planner refuses still reports a malformed ``after:`` as the cursor error.

    The ``.distinct()`` hook makes the child queryset unwindowable, so the
    relation runs per parent. The planner validated the pagination arguments
    first and recorded the relation as accounted for, so ``strictness="raise"``
    does not preempt the pipeline's invalid-cursor error with an N+1 error.
    """
    _seed_hook_order_rows(shape, with_b=False)
    schema = _hook_order_schema(shape, _HOOK_ORDERS["-id"], strictness="raise", distinct=True)
    minted = _post_holder(schema, "{ children(first: 1) { edges { cursor } } }")
    after = {
        "garbage": "not-a-valid-cursor",
        "offset": to_base64("arrayconnection", 0),
        "tampered": json_str(minted, "data", "children", "edges", 0, "cursor")[:-8] + "AAAAAAAA",
    }[kind]
    payload = _post_holder(
        schema,
        _nested_hook_query(shape),
        variables={"first": 1, "after": after},
    )
    assert [json_at(error, "message") for error in json_list(payload, "errors")] == [
        _INVALID_AFTER,
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["fk", "m2m"])
def test_hook_order_cursor_on_a_refused_keyset_relation_keeps_its_per_parent_page(
    shape: str,
) -> None:
    """A refused relation judges a hook-order cursor under the declared vocabulary.

    The root mints the cursor under the hook's ``-id`` order. The declared
    ``("id",)`` vocabulary rejects it, which records the relation as accounted
    for; the ``.distinct()`` hook then makes the planner refuse the relation,
    and the per-parent pipeline, which pages under the hook order, serves the
    page with no N+1 error under ``strictness="raise"``.
    """
    _seed_hook_order_rows(shape, with_b=False)
    schema = _hook_order_schema(shape, _HOOK_ORDERS["-id"], strictness="raise", distinct=True)
    root = _post_holder(schema, "{ children(first: 1) { edges { cursor } } }")
    after = json_at(root, "data", "children", "edges", 0, "cursor")
    page = _nested_hook_pages(
        shape,
        _post_holder(schema, _nested_hook_query(shape), variables={"first": 2, "after": after}),
    )
    assert _labels(shape, json_at(page, "A")) == ["2", "1"]


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["fk", "m2m"])
def test_cursor_of_another_order_is_the_cursor_error_nested(shape: str) -> None:
    """An authentic cursor minted under an order the window does not run is refused.

    The cursor carries the ``title`` order's fingerprint; the window pages
    under the hook's ``-id`` order, so the planner leaves the page to the
    per-parent pipeline, which rejects it as the root would.
    """
    _seed_hook_order_rows(shape, with_b=False)
    titled = _hook_order_schema(shape, _HOOK_ORDERS["title"])
    minted = _post_holder(titled, "{ children(first: 1) { edges { cursor } } }")
    after = json_at(minted, "data", "children", "edges", 0, "cursor")
    payload = _post_holder(
        _hook_order_schema(shape, _HOOK_ORDERS["-id"]),
        _nested_hook_query(shape),
        variables={"first": 1, "after": after},
    )
    assert [json_at(error, "message") for error in json_list(payload, "errors")] == [
        _INVALID_AFTER,
    ]


@pytest.mark.django_db(transaction=True)
async def test_async_nested_keyset_window_pages_under_the_hook_order() -> None:
    """The async twin of the first hook-order row: page 2 serves the rest of ``A``."""
    await sync_to_async(_seed_hook_order_rows)("fk")
    schema = await sync_to_async(_hook_order_schema)("fk", _HOOK_ORDERS["-id"])
    query = (
        "query ($first: Int, $after: String) { parentsConnection { edges { node { name "
        "issuesConnection(first: $first, after: $after) { pageInfo { endCursor } "
        "edges { node { number } } } } } } }"
    )

    async def pages(variables: dict[str, object]) -> dict[str, JSONObject]:
        payload = await _post_async_holder(schema, query, variables=variables)
        assert payload.get("errors") is None, payload
        return {
            json_str(edge, "node", "name"): json_object(edge, "node", "issuesConnection")
            for edge in json_list(payload, "data", "parentsConnection", "edges")
        }

    first = await pages({"first": 2})
    second = await pages({"first": 2, "after": json_at(first, "A", "pageInfo", "endCursor")})
    assert [_labels("fk", json_at(first, "A")), _labels("fk", json_at(first, "B"))] == [
        ["3", "2"],
        ["1"],
    ]
    assert [_labels("fk", json_at(second, "A")), _labels("fk", json_at(second, "B"))] == [
        ["1"],
        [],
    ]


# A target ``get_queryset`` that ``.reverse()``s its queryset compiles the reverse
# of its forward total order (explicit order, else ``Meta.ordering``, else the
# declared ``cursor_field``, made total by the pk tiebreaker): the root slicer,
# the planned nested window and the per-parent pipeline seek, mint and number
# rows under that same reversed order. Rows below reuse the hook-order seed:
# ``A1`` ``y``, ``A2`` ``x``, ``A3`` ``x``, ``B1`` ``a``, created in that order.

#: The full root order per reversed hook (``title``: ``title DESC, id DESC``).
_REVERSED_ROOT_ORDERS = {
    "id": [
        "B1",
        "A3",
        "A2",
        "A1",
    ],
    "title": [
        "A1",
        "A3",
        "A2",
        "B1",
    ],
    "-id": [
        "A1",
        "A2",
        "A3",
        "B1",
    ],
    "bare": [
        "B1",
        "A3",
        "A2",
        "A1",
    ],
}


def _root_children_page(
    schema: strawberry.Schema,
    *,
    order_by: str = "",
    **variables: object,
) -> JSONObject:
    """One root ``children`` page; ``order_by`` is an ``orderBy:`` argument literal."""
    argument = f", orderBy: {order_by}" if order_by else ""
    query = (
        "query ($first: Int, $after: String, $last: Int, $before: String) { "
        f"children(first: $first, after: $after, last: $last, before: $before{argument}) {{ "
        "pageInfo { hasNextPage hasPreviousPage startCursor endCursor } "
        "edges { node { id } } } }"
    )
    payload = _post_holder(schema, query, variables=variables)
    assert payload.get("errors") is None, payload
    return json_object(payload, "data", "children")


def _issue_labels(connection_payload: JSONObject) -> list[str]:
    """``<periodical><number>`` per edge, read back from the node's global id."""
    pks = [
        int(from_base64(json_str(edge, "node", "id"))[1])
        for edge in json_list(connection_payload, "edges")
    ]
    issues = models.Issue.objects.select_related("periodical").in_bulk(pks)
    return [f"{issues[pk].periodical.name}{issues[pk].number}" for pk in pks]


def _root_flags(*pages: JSONObject) -> list[list[bool]]:
    return [
        [
            json_bool(page, "pageInfo", "hasPreviousPage"),
            json_bool(page, "pageInfo", "hasNextPage"),
        ]
        for page in pages
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("hook", list(_REVERSED_ROOT_ORDERS))
def test_reversed_hook_root_pages_forward_every_row_once(hook: str) -> None:
    """``first`` then ``after: endCursor`` serves every row once in the reversed order.

    Each page is one statement; page 2 seeks past page 1's last row under the
    order the SQL compiles, so no row repeats and none is lost.
    """
    _seed_hook_order_rows("fk")
    schema = _hook_order_schema("fk", _REVERSED_HOOK_ORDERS[hook], reverse=True)
    with CaptureQueriesContext(connection) as first_captured:
        first = _root_children_page(schema, first=2)
    with CaptureQueriesContext(connection) as second_captured:
        second = _root_children_page(
            schema,
            first=2,
            after=json_at(first, "pageInfo", "endCursor"),
        )
    expected = _REVERSED_ROOT_ORDERS[hook]
    assert [_issue_labels(first), _issue_labels(second)] == [expected[:2], expected[2:]]
    assert [
        json_at(first, "pageInfo", "hasNextPage"),
        json_at(second, "pageInfo", "hasNextPage"),
    ] == [True, False]
    assert [len(first_captured), len(second_captured)] == [1, 1]


@pytest.mark.django_db
@pytest.mark.parametrize("hook", list(_REVERSED_ROOT_ORDERS))
def test_reversed_hook_root_pages_backward_every_row_once(hook: str) -> None:
    """``last`` then ``before: startCursor`` walks the same reversed order from its end."""
    _seed_hook_order_rows("fk")
    schema = _hook_order_schema("fk", _REVERSED_HOOK_ORDERS[hook], reverse=True)
    with CaptureQueriesContext(connection) as tail_captured:
        tail = _root_children_page(schema, last=2)
    with CaptureQueriesContext(connection) as head_captured:
        head = _root_children_page(schema, last=2, before=json_at(tail, "pageInfo", "startCursor"))
    expected = _REVERSED_ROOT_ORDERS[hook]
    assert [_issue_labels(head), _issue_labels(tail)] == [expected[:2], expected[2:]]
    assert [
        json_at(tail, "pageInfo", "hasPreviousPage"),
        json_at(head, "pageInfo", "hasPreviousPage"),
    ] == [True, False]
    assert [len(tail_captured), len(head_captured)] == [1, 1]


@pytest.mark.django_db
def test_reversed_non_unique_hook_order_compiles_the_pk_tiebreak_descending() -> None:
    """``order_by("title").reverse()`` pages under ``title DESC, id DESC`` on both pages.

    The whole forward total order is reversed, its pk tiebreaker included,
    which is the order Django compiles for the reversed queryset once the
    connection adds its tiebreaker; the seek on page 2 runs under it too.
    """
    _seed_hook_order_rows("fk")
    schema = _hook_order_schema("fk", ("title",), reverse=True)
    with CaptureQueriesContext(connection) as first_captured:
        first = _root_children_page(schema, first=2)
    with CaptureQueriesContext(connection) as second_captured:
        _root_children_page(schema, first=2, after=json_at(first, "pageInfo", "endCursor"))
    order = 'ORDER BY "library_issue"."title" DESC, "library_issue"."id" DESC'
    statements = [first_captured[0]["sql"], second_captured[0]["sql"]]
    assert [order in sql for sql in statements] == [True, True], statements


_REVERSED_NESTED_PAGES: list[
    tuple[str, tuple[list[str], list[str]], tuple[list[str], list[str]]]
] = [
    ("id", (["3", "2"], ["1"]), (["1"], [])),
    ("title", (["1", "3"], ["2"]), (["1"], ["1"])),
    ("-id", (["1", "2"], ["3"]), (["1"], ["1"])),
    ("bare", (["3", "2"], ["1"]), (["1"], [])),
]


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["fk", "m2m"])
@pytest.mark.parametrize(("hook", "a_pages", "b_pages"), _REVERSED_NESTED_PAGES)
def test_reversed_hook_nested_window_pages_under_the_reversed_order(
    shape: str,
    hook: str,
    a_pages: tuple[list[str], list[str]],
    b_pages: tuple[list[str], list[str]],
) -> None:
    """The planned window numbers, seeks and mints under the reversed order from page 1.

    ``A``'s rows are served once across both pages; ``A``'s ``endCursor``
    positions ``B`` by value. Each page is one parent statement and ONE
    batched child statement.
    """
    _seed_hook_order_rows(shape)
    schema = _hook_order_schema(shape, _REVERSED_HOOK_ORDERS[hook], reverse=True)
    query = _nested_hook_query(shape)
    with CaptureQueriesContext(connection) as first_captured:
        first = _nested_hook_pages(shape, _post_holder(schema, query, variables={"first": 2}))
    with CaptureQueriesContext(connection) as second_captured:
        second = _nested_hook_pages(
            shape,
            _post_holder(
                schema,
                query,
                variables={"first": 2, "after": json_at(first, "A", "pageInfo", "endCursor")},
            ),
        )
    assert [_labels(shape, json_at(first, "A")), _labels(shape, json_at(second, "A"))] == list(
        a_pages,
    )
    assert [_labels(shape, json_at(first, "B")), _labels(shape, json_at(second, "B"))] == list(
        b_pages,
    )
    for captured in (first_captured, second_captured):
        assert [
            len(_table_statements(captured, _parent_table(shape))),
            len(_table_statements(captured, _child_table(shape))),
        ] == [1, 1], captured.captured_queries


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["fk", "m2m"])
@pytest.mark.parametrize(
    ("hook", "a_page", "b_page"),
    [(hook, a_pages[0], b_pages[0]) for hook, a_pages, b_pages in _REVERSED_NESTED_PAGES],
)
def test_reversed_hook_nested_offset_window_matches_the_per_parent_page(
    shape: str,
    hook: str,
    a_page: list[str],
    b_page: list[str],
) -> None:
    """An offset connection's planned window serves the per-parent pipeline's page 1.

    No ``cursor_field``: the window's row numbers run under the reversed order
    the per-parent pipeline compiles, in one batched child statement where the
    pipeline issues one per parent.
    """
    _seed_hook_order_rows(shape)
    query = _nested_hook_query(shape)
    pages: list[list[list[str]]] = []
    child_statements: list[int] = []
    for optimizer in (True, False):
        schema = _hook_order_schema(
            shape,
            _REVERSED_HOOK_ORDERS[hook],
            reverse=True,
            keyset=False,
            optimizer=optimizer,
        )
        with CaptureQueriesContext(connection) as captured:
            page = _nested_hook_pages(shape, _post_holder(schema, query, variables={"first": 2}))
        pages.append([_labels(shape, json_at(page, "A")), _labels(shape, json_at(page, "B"))])
        child_statements.append(len(_table_statements(captured, _child_table(shape))))
    assert pages == [[a_page, b_page], [a_page, b_page]]
    assert child_statements == [1, 2]


@pytest.mark.django_db
def test_order_by_beside_a_reversed_hook_pages_every_row_once() -> None:
    """``orderBy:`` composes with the hook's ``.reverse()`` and its cursors replay.

    ``orderBy`` replaces the hook's terms under Django ``order_by()``
    semantics, so the hook's reversal inverts it: ``{number: ASC}`` pages
    under ``number DESC, id DESC``, every row once, and page 1's ``endCursor``
    serves the same page 2 on every replay.
    """
    _seed_hook_order_rows("fk")
    schema = _hook_order_schema("fk", ("id",), reverse=True, orderable=True)
    order_by = "[{ number: ASC }]"
    first = _root_children_page(schema, order_by=order_by, first=2)
    after = json_at(first, "pageInfo", "endCursor")
    second = _root_children_page(schema, order_by=order_by, first=2, after=after)
    replayed = _root_children_page(schema, order_by=order_by, first=2, after=after)
    assert [_issue_labels(first), _issue_labels(second), _issue_labels(replayed)] == [
        ["A3", "A2"],
        ["B1", "A1"],
        ["B1", "A1"],
    ]
    assert _root_flags(first, second) == [[False, True], [True, False]]


# A target ``get_queryset`` that orders through ``extra(order_by=...)`` hands the
# connection an ordering Django compiles in place of every other one and that any
# ``order_by(...)`` empties. The connection keeps it: the root slicer, the planned
# nested window and the per-parent pipeline page, seek and mint under it (its
# ``.reverse()`` included), extended by the pk tiebreaker rather than replaced.
# Rows below reuse the hook-order seed: ``A1`` ``y``, ``A2`` ``x``, ``A3`` ``x``,
# ``B1`` ``a``, created in that order (the ``m2m`` books each on their own shelf,
# shelf codes ``A-1`` .. ``B-1`` in that order too).

#: Per relation shape and spelling, the hook's ``extra`` ordering: a field, a descending
#: field, the child's own ``table.column``, its foreign key's raw column, a column of the
#: table the hook joins through a filter, and a quoted table name.
_EXTRA_HOOK_ORDERS: dict[str, dict[str, _ChildOrder]] = {
    "fk": {
        "field": lambda issues: issues.extra(order_by=["title"]),
        "descending-field": lambda issues: issues.extra(order_by=["-number"]),
        "table-column": lambda issues: issues.extra(order_by=["library_issue.title"]),
        "foreign-key": lambda issues: issues.extra(
            order_by=["library_issue.periodical_id", "-library_issue.number"],
        ),
        "joined-table": lambda issues: issues.filter(periodical__name__gte="").extra(
            order_by=["-library_periodical.name", "-number"],
        ),
        "quoted-table": lambda issues: issues.extra(order_by=['"library_issue".title']),
    },
    "m2m": {
        "field": lambda books: books.extra(order_by=["title"]),
        "descending-field": lambda books: books.extra(order_by=["-id"]),
        "table-column": lambda books: books.extra(order_by=["library_book.title"]),
        "foreign-key": lambda books: books.extra(order_by=["-library_book.shelf_id"]),
        "joined-table": lambda books: books.filter(shelf__code__gte="").extra(
            order_by=["-library_shelf.code"],
        ),
        "quoted-table": lambda books: books.extra(order_by=['"library_book".title']),
    },
}

#: The spellings a value cursor can anchor: each names a non-relation column of the child.
_ANCHORED_EXTRA_SPELLINGS = ("field", "descending-field", "table-column")

#: The spellings no value cursor can anchor: a foreign key's raw column (as
#: ``order_by("periodical_id")`` is not), and the raw ``table.column`` SQL below.
_UNANCHORED_EXTRA_SPELLINGS = ("foreign-key", "joined-table", "quoted-table")

#: The spellings Django passes through as raw ``table.column`` SQL.
_RAW_EXTRA_SPELLINGS = ("joined-table", "quoted-table")

#: The full root order per ``fk`` spelling, forward and ``.reverse()``'d (the reverse of
#: the forward order made total by the pk), one label per row.
_EXTRA_ROOT_ORDERS: dict[str, tuple[str, str]] = {
    "field": ("B1 A2 A3 A1", "A1 A3 A2 B1"),
    "descending-field": ("A3 A2 A1 B1", "B1 A1 A2 A3"),
    "table-column": ("B1 A2 A3 A1", "A1 A3 A2 B1"),
    "foreign-key": ("A3 A2 A1 B1", "B1 A1 A2 A3"),
    "joined-table": ("B1 A3 A2 A1", "A1 A2 A3 B1"),
    "quoted-table": ("B1 A2 A3 A1", "A1 A3 A2 B1"),
}

#: Parent ``A``'s ``first: 2`` page per spelling, forward and reversed, on either shape.
_EXTRA_NESTED_PAGES: dict[str, tuple[str, str]] = {
    "field": ("2 3", "1 3"),
    "descending-field": ("3 2", "1 2"),
    "table-column": ("2 3", "1 3"),
    "foreign-key": ("3 2", "1 2"),
    "joined-table": ("3 2", "1 2"),
    "quoted-table": ("2 3", "1 3"),
}

#: Every root and nested row: each spelling forward and reversed on an offset
#: connection, and each anchorable one on a keyset connection.
_EXTRA_PAGING_CASES = [
    pytest.param(
        spelling,
        reverse,
        keyset,
        id=f"{spelling}-{'reversed' if reverse else 'forward'}-{'keyset' if keyset else 'offset'}",
    )
    for spelling in _EXTRA_ROOT_ORDERS
    for reverse in (False, True)
    for keyset in (False, True)
    if not keyset or spelling in _ANCHORED_EXTRA_SPELLINGS
]


def _extra_hook_schema(
    shape: str,
    spelling: str,
    *,
    reverse: bool = False,
    keyset: bool = False,
    optimizer: bool = True,
    strictness: str = "off",
) -> strawberry.Schema:
    return _hook_order_schema(
        shape,
        None,
        order_hook=_EXTRA_HOOK_ORDERS[shape][spelling],
        reverse=reverse,
        keyset=keyset,
        optimizer=optimizer,
        strictness=strictness,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(("spelling", "reverse", "keyset"), _EXTRA_PAGING_CASES)
def test_extra_hook_root_pages_forward_every_row_once(
    spelling: str,
    *,
    reverse: bool,
    keyset: bool,
) -> None:
    """``first`` then ``after: endCursor`` serves every row once in the ``extra`` order.

    Each page is one statement; page 2 resumes past page 1's last row under
    the hook's order, so no row repeats and none is lost.
    """
    _seed_hook_order_rows("fk")
    schema = _extra_hook_schema("fk", spelling, reverse=reverse, keyset=keyset)
    with CaptureQueriesContext(connection) as first_captured:
        first = _root_children_page(schema, first=2)
    with CaptureQueriesContext(connection) as second_captured:
        second = _root_children_page(
            schema,
            first=2,
            after=json_at(first, "pageInfo", "endCursor"),
        )
    expected = _EXTRA_ROOT_ORDERS[spelling][reverse].split()
    assert [_issue_labels(first), _issue_labels(second)] == [expected[:2], expected[2:]]
    assert _root_flags(first, second) == [[False, True], [True, False]]
    assert [len(first_captured), len(second_captured)] == [1, 1]


@pytest.mark.django_db
@pytest.mark.parametrize(("spelling", "reverse", "keyset"), _EXTRA_PAGING_CASES)
def test_extra_hook_root_pages_backward_every_row_once(
    spelling: str,
    *,
    reverse: bool,
    keyset: bool,
) -> None:
    """``last`` then ``before: startCursor`` walks the same ``extra`` order from its end."""
    _seed_hook_order_rows("fk")
    schema = _extra_hook_schema("fk", spelling, reverse=reverse, keyset=keyset)
    with CaptureQueriesContext(connection) as tail_captured:
        tail = _root_children_page(schema, last=2)
    with CaptureQueriesContext(connection) as head_captured:
        head = _root_children_page(schema, last=2, before=json_at(tail, "pageInfo", "startCursor"))
    expected = _EXTRA_ROOT_ORDERS[spelling][reverse].split()
    assert [_issue_labels(head), _issue_labels(tail)] == [expected[:2], expected[2:]]
    assert _root_flags(head, tail) == [[False, True], [True, False]]
    assert [len(tail_captured), len(head_captured)] == [1, 1]


def _random_then_issue_pk_order_sql(pk_ordering: str) -> str:
    """Return the ``ORDER BY`` clause Django compiles for ``order_by("?", pk_ordering)``.

    Django spells ``Random()`` per vendor (``RAND()`` on SQLite, ``RANDOM()`` on
    PostgreSQL) and quotes names per vendor, so the expected clause is compiled
    from a reference queryset on the default connection rather than written in
    one backend's spelling.
    """
    reference = models.Issue.objects.order_by("?", pk_ordering)
    sql, _ = reference.query.sql_with_params()
    return sql[sql.index("ORDER BY") :]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("reverse", "pk_ordering"),
    [(False, "pk"), (True, "-pk")],
    ids=["forward", "reversed"],
)
def test_random_extra_hook_order_keeps_the_pk_tiebreaker_at_the_root(
    *,
    reverse: bool,
    pk_ordering: str,
) -> None:
    """An ``extra(order_by=["?"])`` hook order serves a random page tie-broken by the pk.

    The random term stays the page order, so the offset connection draws its
    rows at random instead of serving them by the pk alone; the pk joins it
    (descending under ``.reverse()``, which leaves the random term as it is).
    """
    order = _random_then_issue_pk_order_sql(pk_ordering)
    _seed_hook_order_rows("fk")
    schema = _hook_order_schema(
        "fk",
        None,
        order_hook=lambda issues: issues.extra(order_by=["?"]),
        reverse=reverse,
        keyset=False,
    )
    with CaptureQueriesContext(connection) as captured:
        page = _root_children_page(schema, first=4)
    assert sorted(_issue_labels(page)) == [
        "A1",
        "A2",
        "A3",
        "B1",
    ]
    assert len(captured) == 1, captured.captured_queries
    assert order in captured[0]["sql"], captured[0]["sql"]


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["fk", "m2m"])
@pytest.mark.parametrize(("spelling", "reverse", "keyset"), _EXTRA_PAGING_CASES)
def test_extra_hook_nested_window_serves_the_per_parent_page(
    shape: str,
    spelling: str,
    *,
    reverse: bool,
    keyset: bool,
) -> None:
    """The planned window serves the per-parent pipeline's page under the ``extra`` order.

    One batched child statement for both parents where the pipeline issues one
    per parent; both serve ``A``'s first two rows in the hook's order and
    ``B``'s one row.
    """
    _seed_hook_order_rows(shape)
    query = _nested_hook_query(shape)
    pages: list[list[list[str]]] = []
    child_statements: list[int] = []
    for optimizer in (True, False):
        schema = _extra_hook_schema(
            shape,
            spelling,
            reverse=reverse,
            keyset=keyset,
            optimizer=optimizer,
        )
        with CaptureQueriesContext(connection) as captured:
            page = _nested_hook_pages(shape, _post_holder(schema, query, variables={"first": 2}))
        pages.append([_labels(shape, json_at(page, "A")), _labels(shape, json_at(page, "B"))])
        child_statements.append(len(_table_statements(captured, _child_table(shape))))
    a_page = _EXTRA_NESTED_PAGES[spelling][reverse].split()
    assert pages == [[a_page, ["1"]], [a_page, ["1"]]]
    assert child_statements == [1, 2]


def _order_by_clause(queryset: QuerySet[models.Issue | models.Book]) -> str:
    """The ``ORDER BY`` terms Django itself compiles for ``queryset``."""
    return str(queryset.query).split(" ORDER BY ", maxsplit=1)[1]


#: The column each shape's planned window partitions its rows by.
_WINDOW_PARTITIONS = {
    "fk": '"library_issue"."periodical_id"',
    "m2m": '"library_book_genres"."genre_id"',
}


def _ordered_statements(captured: CaptureQueriesContext, shape: str) -> list[str]:
    """The child-table statements that order their rows (a ``last:`` page's count does not)."""
    return [sql for sql in _table_statements(captured, _child_table(shape)) if " ORDER BY " in sql]


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["fk", "m2m"])
@pytest.mark.parametrize("spelling", _RAW_EXTRA_SPELLINGS)
def test_raw_extra_hook_term_compiles_as_django_compiles_it(shape: str, spelling: str) -> None:
    """A raw ``table.column`` term reaches every statement as the SQL Django emits for it.

    Django's own compile of the hook queryset, forward and ``.reverse()``'d, is
    the order each statement opens with, the pk tiebreaker after it: the root
    ``first:`` and ``last:`` pages, the root page under the reversed hook, each
    per-parent page, and the planned window's ``ROW_NUMBER`` orders (a ``last:``
    window numbering from the partition end under the reversed order too).
    """
    _seed_hook_order_rows(shape)
    child_model, _parent_model, relation, label = _HOOK_SHAPES[shape]
    order_hook = _EXTRA_HOOK_ORDERS[shape][spelling]
    forward = _order_by_clause(order_hook(child_model.objects.all()))
    backward = _order_by_clause(order_hook(child_model.objects.all()).reverse())
    pk = f'"{_child_table(shape)}"."id"'
    partition = _WINDOW_PARTITIONS[shape]
    edges = f"edges {{ node {{ {label} }} }}"
    last_query = f"{{ parents {{ name {relation}Connection(last: 2) {{ {edges} }} }} }}"
    # Each build re-registers the child type, so each schema is used up before the next.
    per_parent = _extra_hook_schema(shape, spelling, optimizer=False)
    with CaptureQueriesContext(connection) as first_captured:
        _ = _root_children_page(per_parent, first=2)
    with CaptureQueriesContext(connection) as last_captured:
        _ = _root_children_page(per_parent, last=2)
    with CaptureQueriesContext(connection) as unplanned_captured:
        _ = _nested_hook_pages(
            shape,
            _post_holder(per_parent, _nested_hook_query(shape), variables={"first": 2}),
        )
    reversed_hook = _extra_hook_schema(shape, spelling, reverse=True, optimizer=False)
    with CaptureQueriesContext(connection) as reversed_captured:
        _ = _root_children_page(reversed_hook, first=2)
    planned = _extra_hook_schema(shape, spelling)
    with CaptureQueriesContext(connection) as window_captured:
        _ = _nested_hook_pages(
            shape,
            _post_holder(planned, _nested_hook_query(shape), variables={"first": 2}),
        )
    with CaptureQueriesContext(connection) as last_window_captured:
        _ = _nested_hook_pages(shape, _post_holder(planned, last_query))
    forward_page = f"ORDER BY {forward}, {pk} ASC"
    for statement in [
        *_ordered_statements(first_captured, shape),
        *_ordered_statements(last_captured, shape),
        *_ordered_statements(unplanned_captured, shape),
    ]:
        assert f"{forward_page} LIMIT" in statement, statement
    [reversed_page] = _ordered_statements(reversed_captured, shape)
    assert f"ORDER BY {backward}, {pk} DESC LIMIT" in reversed_page, reversed_page
    # A ``Window`` spells an ascending column term without ``ASC``, so the window
    # orders are read at the raw term itself, which opens each of them.
    forward_term, backward_term = forward.split(", ")[0], backward.split(", ")[0]
    [window] = _ordered_statements(window_captured, shape)
    [last_window] = _ordered_statements(last_window_captured, shape)
    over = f"OVER (PARTITION BY {partition} ORDER BY"
    assert [
        window.count(f"{over} {forward_term}"),
        last_window.count(f"{over} {forward_term}"),
        last_window.count(f"{over} {backward_term}"),
    ] == [1, 1, 1], (window, last_window)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("optimizer", "strictness"),
    [(True, "off"), (False, "off"), (True, "raise")],
    ids=["planned", "unplanned", "strict"],
)
@pytest.mark.parametrize("shape", ["fk", "m2m"])
@pytest.mark.parametrize("spelling", _UNANCHORED_EXTRA_SPELLINGS)
def test_unanchorable_extra_hook_order_raises_the_root_keyset_error_nested(
    shape: str,
    spelling: str,
    *,
    optimizer: bool,
    strictness: str,
) -> None:
    """A foreign key or raw ``table.column`` term is no cursor column: the keyset error, everywhere.

    The root and the nested connection, planned or not, raise the error an
    ``orderBy:`` / ``get_queryset`` order no cursor can anchor raises, at the field.
    """
    _seed_hook_order_rows(shape, with_b=False)
    schema = _extra_hook_schema(
        shape,
        spelling,
        keyset=True,
        optimizer=optimizer,
        strictness=strictness,
    )
    root = _post_holder(schema, "{ children(first: 1) { edges { cursor } } }")
    nested = _post_holder(schema, _nested_hook_query(shape), variables={"first": 1})
    relation = _HOOK_SHAPES[shape][2]
    assert [
        (json_at(error, "message"), json_at(error, "path")) for error in json_list(root, "errors")
    ] == [(_UNANCHORABLE_ORDER, ["children"])]
    assert [
        (json_at(error, "message"), json_at(error, "path"))
        for error in json_list(nested, "errors")
    ] == [(_UNANCHORABLE_ORDER, ["parents", 0, f"{relation}Connection"])]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reversed"])
async def test_async_extra_hook_keyset_pages_under_the_extra_order(*, reverse: bool) -> None:
    """The async twin: the root slicer and the planned window page under the ``extra`` order.

    Page 1's ``endCursor`` of each connection serves the rest of its rows on page 2.
    """
    await sync_to_async(_seed_hook_order_rows)("fk")
    schema = await sync_to_async(_extra_hook_schema)(
        "fk",
        "table-column",
        reverse=reverse,
        keyset=True,
    )
    query = (
        "query ($rootAfter: String, $nestedAfter: String) { "
        "children(first: 2, after: $rootAfter) { pageInfo { endCursor } edges { node { id } } } "
        "parentsConnection { edges { node { name "
        "issuesConnection(first: 2, after: $nestedAfter) { pageInfo { endCursor } "
        "edges { node { number } } } } } } }"
    )

    async def pages(variables: dict[str, object]) -> tuple[JSONObject, dict[str, JSONObject]]:
        payload = await _post_async_holder(schema, query, variables=variables)
        assert payload.get("errors") is None, payload
        return json_object(payload, "data", "children"), {
            json_str(edge, "node", "name"): json_object(edge, "node", "issuesConnection")
            for edge in json_list(payload, "data", "parentsConnection", "edges")
        }

    first_root, first_nested = await pages({})
    second_root, second_nested = await pages(
        {
            "rootAfter": json_at(first_root, "pageInfo", "endCursor"),
            "nestedAfter": json_at(first_nested, "A", "pageInfo", "endCursor"),
        },
    )
    expected = _EXTRA_ROOT_ORDERS["table-column"][reverse].split()
    labels = sync_to_async(_issue_labels)
    assert [await labels(first_root), await labels(second_root)] == [expected[:2], expected[2:]]
    a_rows = [label.removeprefix("A") for label in expected if label.startswith("A")]
    assert [
        _labels("fk", json_at(first_nested, "A")),
        _labels("fk", json_at(second_nested, "A")),
    ] == [a_rows[:2], a_rows[2:]]


def _reversed_reading_list_schema(
    cursor_field: tuple[str, ...] | None,
    hook_order: tuple[str, ...] = (),
) -> strawberry.Schema:
    """A root ``children`` connection over ``ReadingList`` whose hook ``.reverse()``s it.

    ``ReadingList`` orders by its inherited ``Meta.ordering = ["title"]``; the
    hook orders by ``hook_order`` first when given, and the type is a keyset
    connection over ``cursor_field`` unless it is ``None``.
    """

    def hook(
        _cls: type[DjangoType],
        queryset: QuerySet[models.ReadingList],
        _info: strawberry.Info[object, object],
    ) -> QuerySet[models.ReadingList]:
        return (queryset.order_by(*hook_order) if hook_order else queryset).reverse()

    registry.clear()
    list_type = make_django_type(
        "ReversedReadingListType",
        models.ReadingList,
        ("id", "title"),
        meta_extra={"cursor_field": cursor_field} if cursor_field is not None else None,
        namespace_extra={"get_queryset": classmethod(hook)},
    )
    finalize_django_types()

    @strawberry.type
    class Query:
        children = DjangoConnectionField(list_type)

    return strawberry.Schema(query=Query, config=strawberry_config())


def _seed_reading_lists() -> dict[int, str]:
    """``L1`` ``b``, ``L2`` ``a``, ``L3`` ``b``, ``L4`` ``c`` in pk order; returns pk -> label."""
    labels: dict[int, str] = {}
    for label, title in (
        ("L1", "b"),
        ("L2", "a"),
        ("L3", "b"),
        ("L4", "c"),
    ):
        pk = models.ReadingList.objects.create(title=title).pk
        assert pk is not None
        labels[pk] = label
    return labels


def _reading_list_labels(labels: dict[int, str], page: JSONObject) -> list[str]:
    return [
        labels[int(from_base64(json_str(edge, "node", "id"))[1])]
        for edge in json_list(page, "edges")
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("cursor_field", "pages"),
    [
        (("title", "id"), [["L4", "L3"], ["L1", "L2"]]),
        (("-title", "id"), [["L2", "L3"], ["L1", "L4"]]),
        (None, [["L4", "L3"], ["L1", "L2"]]),
    ],
    ids=["keyset-meta-order", "keyset-cursor-field", "offset"],
)
def test_bare_reverse_of_a_meta_ordering_pages_every_row_once(
    cursor_field: tuple[str, ...] | None,
    pages: list[list[str]],
) -> None:
    """A bare ``.reverse()`` pages under the reverse of the forward total order.

    The forward order is the declared ``cursor_field`` on a keyset type (it
    beats ``Meta.ordering``), else ``Meta.ordering = ["title"]`` with the pk
    tiebreaker: ``("-title", "id")`` reversed serves ``title ASC, id DESC``,
    ``title`` / ``("title", "id")`` reversed serves ``title DESC, id DESC``.
    """
    labels = _seed_reading_lists()
    schema = _reversed_reading_list_schema(cursor_field)
    first = _root_children_page(schema, first=2)
    second = _root_children_page(schema, first=2, after=json_at(first, "pageInfo", "endCursor"))
    assert [_reading_list_labels(labels, first), _reading_list_labels(labels, second)] == pages
    assert [
        json_at(first, "pageInfo", "hasNextPage"),
        json_at(second, "pageInfo", "hasNextPage"),
    ] == [True, False]


@pytest.mark.django_db
def test_reversed_random_hook_order_serves_every_row_under_a_descending_tiebreak() -> None:
    """``order_by("?").reverse()`` keeps ``"?"`` (it has no direction) and flips the pk.

    An offset connection: one ``first`` page over every row, no error, one
    statement ordered by the random term then the pk descending.
    """
    labels = _seed_reading_lists()
    schema = _reversed_reading_list_schema(None, ("?",))
    with CaptureQueriesContext(connection) as captured:
        page = _root_children_page(schema, first=4)
    assert sorted(_reading_list_labels(labels, page)) == [
        "L1",
        "L2",
        "L3",
        "L4",
    ]
    assert len(captured) == 1, captured.captured_queries
    sql = captured[0]["sql"]
    # SQLite compiles Django's random order as ``RAND()``, PostgreSQL as ``RANDOM()``.
    assert ["RAND" in sql, '"library_readinglist"."id" DESC' in sql] == [True, True], sql


# One relation name, two windows: ``CirculationDesk.children`` (``DeskShift``,
# hook order ``-id``) and ``ScalarSpecimen.children`` (self-referential, hook
# order ``label``) in one operation. Each window's vocabulary is published under
# its own resolver key, so neither page is minted under the other's columns.

_TWIN_CHILDREN_QUERY = """
query ($first: Int, $desk: String, $specimen: String) {
  desks { childrenConnection(first: $first, after: $desk) {
    pageInfo { endCursor } edges { cursor node { name } } } }
  specimens { childrenConnection(first: $first, after: $specimen) {
    pageInfo { endCursor } edges { cursor node { label } } } }
}
"""

_ASYNC_DESKS_FIELD = """
  desksConnection { edges { node { childrenConnection(first: $first, after: $desk) {
    pageInfo { endCursor } edges { node { name } } } } } }
"""

_ASYNC_SPECIMENS_FIELD = """
  specimensConnection { edges { node { childrenConnection(first: $first, after: $specimen) {
    pageInfo { endCursor } edges { node { label } } } } } }
"""


def _twin_children_schema(*, optimizer: bool = True) -> strawberry.Schema:
    """Holder schema whose two root fields each window a ``children`` relation."""

    def shifts_newest_first(
        _cls: type[DjangoType],
        queryset: QuerySet[models.DeskShift],
        _info: strawberry.Info[object, object],
    ) -> QuerySet[models.DeskShift]:
        return queryset.order_by("-id")

    def specimens_by_label(
        _cls: type[DjangoType],
        queryset: QuerySet[ScalarSpecimen],
        _info: strawberry.Info[object, object],
    ) -> QuerySet[ScalarSpecimen]:
        return queryset.order_by("label")

    registry.clear()
    make_django_type(
        "TwinShiftType",
        models.DeskShift,
        ("id", "name"),
        meta_extra={"cursor_field": ("id",)},
        namespace_extra={"get_queryset": classmethod(shifts_newest_first)},
    )
    desk_type = make_django_type(
        "TwinDeskType",
        models.CirculationDesk,
        ("id", "name", "children"),
        meta_extra={"relation_shapes": {"children": "connection"}},
    )
    specimen_type = make_django_type(
        "TwinSpecimenType",
        ScalarSpecimen,
        ("id", "label", "children"),
        meta_extra={"cursor_field": ("id",), "relation_shapes": {"children": "connection"}},
        namespace_extra={"get_queryset": classmethod(specimens_by_label)},
    )
    finalize_django_types()

    async def async_desks(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> QuerySet[models.CirculationDesk]:
        return models.CirculationDesk.objects.all()

    async def async_specimens(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> QuerySet[ScalarSpecimen]:
        return ScalarSpecimen.objects.filter(parent__isnull=True)

    def resolve_desks() -> QuerySet[models.CirculationDesk]:
        return models.CirculationDesk.objects.all()

    def resolve_specimens() -> QuerySet[ScalarSpecimen]:
        return ScalarSpecimen.objects.filter(parent__isnull=True)

    @strawberry.type
    class Query:
        desks_connection = DjangoConnectionField(desk_type, resolver=async_desks)
        specimens_connection = DjangoConnectionField(specimen_type, resolver=async_specimens)
        desks: QuerySet[models.CirculationDesk] = strawberry.field(
            resolver=resolve_desks,
            graphql_type=list[desk_type],
        )
        specimens: QuerySet[ScalarSpecimen] = strawberry.field(
            resolver=resolve_specimens,
            graphql_type=list[specimen_type],
        )

    optimizer_extension = DjangoOptimizerExtension() if optimizer else None
    extensions = [lambda: optimizer_extension] if optimizer_extension is not None else []
    return strawberry.Schema(query=Query, config=strawberry_config(), extensions=extensions)


def _seed_twin_children() -> None:
    """One desk with shifts s1, s2, s3 and one specimen with children c-b, c-c, c-a (pk order)."""
    branch = models.Branch.objects.create(name="Twin Branch")
    shelf = models.Shelf.objects.create(code="T-1", branch=branch)
    desk = models.CirculationDesk.objects.create(name="Twin Desk", branch=branch, shelf=shelf)
    for name in ("s1", "s2", "s3"):
        models.DeskShift.objects.create(name=name, desk=desk)
    stamp = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    parent = None
    for label in (
        "root",
        "c-b",
        "c-c",
        "c-a",
    ):
        specimen = ScalarSpecimen.objects.create(
            label=label,
            occurred_on=stamp.date(),
            occurred_at=stamp,
            occurred_time=stamp.time(),
            external_id=uuid.uuid4(),
            parent=parent,
        )
        parent = parent or specimen


def _twin_pages(payload: JSONObject) -> tuple[JSONObject, JSONObject]:
    assert payload.get("errors") is None, payload
    data = json_at(payload, "data")
    return json_object(data, "desks", 0, "childrenConnection"), json_object(
        data,
        "specimens",
        0,
        "childrenConnection",
    )


def _twin_names(desk_page: JSONObject, specimen_page: JSONObject) -> list[list[str]]:
    return [
        [json_str(edge, "node", "name") for edge in json_list(desk_page, "edges")],
        [json_str(edge, "node", "label") for edge in json_list(specimen_page, "edges")],
    ]


@pytest.mark.django_db
def test_one_relation_name_windowed_twice_keeps_each_windows_cursor_vocabulary() -> None:
    """Both ``childrenConnection`` windows stay batched and mint under their own order.

    Each page is one ``DeskShift`` statement and one specimen-children
    statement (beside the specimen root); page 1's cursors equal the
    optimizer-off cursors byte for byte, and each window's ``endCursor`` pages
    on to the rest of its own rows.
    """
    _seed_twin_children()
    unplanned = _twin_pages(
        _post_holder(
            _twin_children_schema(optimizer=False),
            _TWIN_CHILDREN_QUERY,
            variables={"first": 2},
        ),
    )
    schema = _twin_children_schema()
    with CaptureQueriesContext(connection) as first_captured:
        first = _twin_pages(_post_holder(schema, _TWIN_CHILDREN_QUERY, variables={"first": 2}))
    with CaptureQueriesContext(connection) as second_captured:
        second = _twin_pages(
            _post_holder(
                schema,
                _TWIN_CHILDREN_QUERY,
                variables={
                    "first": 2,
                    "desk": json_at(first[0], "pageInfo", "endCursor"),
                    "specimen": json_at(first[1], "pageInfo", "endCursor"),
                },
            ),
        )

    assert _twin_names(*first) == [["s3", "s2"], ["c-a", "c-b"]]
    assert _twin_names(*second) == [["s1"], ["c-c"]]
    assert [[json_at(edge, "cursor") for edge in json_list(page, "edges")] for page in first] == [
        [json_at(edge, "cursor") for edge in json_list(page, "edges")] for page in unplanned
    ]
    for captured in (first_captured, second_captured):
        statements = [
            len(_table_statements(captured, "library_deskshift")),
            len(_table_statements(captured, "scalars_scalarspecimen")),
        ]
        assert statements == [1, 2], captured.captured_queries


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("desks_first", [True, False], ids=["desks-first", "specimens-first"])
async def test_async_one_relation_name_windowed_twice_keeps_each_windows_cursor_vocabulary(
    *,
    desks_first: bool,
) -> None:
    """The async twin: two concurrently planned root fields, each window paged by its own cursor.

    The async engine plans both root fields before either one's rows resolve,
    so whichever field is planned first would mint under the other's
    vocabulary if the two windows shared one key.
    """
    await sync_to_async(_seed_twin_children)()
    schema = await sync_to_async(_twin_children_schema)()
    fields = (
        (_ASYNC_DESKS_FIELD, _ASYNC_SPECIMENS_FIELD)
        if desks_first
        else (_ASYNC_SPECIMENS_FIELD, _ASYNC_DESKS_FIELD)
    )
    query = "query ($first: Int, $desk: String, $specimen: String) {" + "".join(fields) + "}"

    async def pages(variables: dict[str, object]) -> tuple[JSONObject, JSONObject]:
        payload = await _post_async_holder(schema, query, variables=variables)
        assert payload.get("errors") is None, payload
        data = json_at(payload, "data")
        return (
            json_object(data, "desksConnection", "edges", 0, "node", "childrenConnection"),
            json_object(data, "specimensConnection", "edges", 0, "node", "childrenConnection"),
        )

    first = await pages({"first": 2})
    second = await pages(
        {
            "first": 2,
            "desk": json_at(first[0], "pageInfo", "endCursor"),
            "specimen": json_at(first[1], "pageInfo", "endCursor"),
        },
    )
    assert _twin_names(*first) == [["s3", "s2"], ["c-a", "c-b"]]
    assert _twin_names(*second) == [["s1"], ["c-c"]]
