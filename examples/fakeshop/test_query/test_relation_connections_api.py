"""Live HTTP tests for relation-connection windows, fallbacks, hints and strategy parity.

The holder graph deliberately omits the target visibility hook that fakeshop's
BookType carries: the cases compare a consumer's hook-free planned window with
its per-parent pipeline under the same published field names. Private planted
window records and exception identities remain in tests/test_relay_connection.py.
"""

import re
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from functools import wraps

import pytest
import strawberry
from apps.library.models import Book, Branch, Genre, Loan, Patron, RepairTicket, Shelf, Venue
from asgiref.sync import sync_to_async
from django.db import connection as db_connection
from django.db import models as djmodels
from django.db.models import ForeignObjectRel
from django.db.models.expressions import Combinable
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import RecordCompiledSql, middleware_without_debug_toolbar
from strategy_schemas import make_django_type
from strategy_schemas import make_django_type as _make_type
from strawberry import relay
from strawberry.test.client import Response as GraphQLResponse
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoSchema,
    OptimizerHint,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import (
    _connection_type_cache,
    _connection_type_for,
)
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import AsyncTestClient, TestClient
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._idioms import declare_django_type, json_at, json_list
from tests._relation_connection_schemas import (
    _genres_distinct_book_schema,
    _genres_expression_ordered_schema,
    _genres_filterable_book_schema,
    _genres_list_schema,
    _schema_with_root,
    _seed_library_books,
    _shelves_with_consumer_books_schema,
)

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, strawberry.Schema | None] = {"schema": None}


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
    path("graphql-relation-connections/", _graphql_view),
    path("graphql-relation-connections-async/", _async_graphql_view),
]


@pytest.fixture(autouse=True)
def _pass_through_errors() -> Iterator[None]:
    """Keep the strictness message observable without installing the debug toolbar."""
    with override_settings(DEBUG=True, MIDDLEWARE=middleware_without_debug_toolbar()):
        yield


def _exec(
    schema: strawberry.Schema,
    query: str,
    *,
    expect_errors: bool = False,
) -> GraphQLResponse:
    """Post the consumer operation against the function-scoped graph."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            result = TestClient().query(
                query,
                assert_no_errors=False,
                url="/graphql-relation-connections/",
            )
        assert result.response.status_code == 200
        if not expect_errors:
            assert result.errors is None, result.errors
        return result
    finally:
        _CURRENT["schema"] = None


async def _exec_async(schema: strawberry.Schema, query: str) -> GraphQLResponse:
    """Post the same graph through the async view and client."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            result = await AsyncTestClient().query(
                query,
                assert_no_errors=False,
                url="/graphql-relation-connections-async/",
            )
        assert result.response.status_code == 200
        return result
    finally:
        _CURRENT["schema"] = None


@contextmanager
def _capture_relations(
    *,
    parent_table: str = "library_genre",
    child_table: str = "library_book",
    windows: int = 1,
) -> Generator[CaptureQueriesContext]:
    """Count the parent read and batched child statements independently of auth SQL."""
    with CaptureQueriesContext(db_connection) as captured:
        yield captured
    parent_sql = _table_selects(captured, parent_table)
    child_sql = _table_selects(captured, child_table)
    assert len(parent_sql) == 1, parent_sql
    assert len(child_sql) == windows, child_sql
    assert all("ROW_NUMBER() OVER" in sql.upper() for sql in child_sql), child_sql


def _table_selects(captured: CaptureQueriesContext, table: str) -> list[str]:
    """Read statements for the model's exact FROM table, including window wrappers."""
    return [q["sql"] for q in captured.captured_queries if f'FROM "{table}"' in q["sql"]]


def _seed_window_books(titles: list[str]) -> None:
    """Use two populated partitions so a single-parent LIMIT cannot satisfy a window claim."""
    _, books = _seed_library_books(titles)
    other = Genre.objects.create(name="other")
    other.books.add(*books)


def _assert_same_partitions(data: object) -> None:
    """The paired fixture gives both parents exactly the same selected connection."""
    objects = json_list(data, "objs")
    assert len(objects) == 2
    assert objects[0] == objects[1]


@pytest.mark.django_db
def test_fast_path_single_query() -> None:
    """Parent page + one window query, zero per-parent queries (the cost contract).

    The optimizer-on mirror of the optimizer-less ``1 + N`` cost (live at
    ``test_products_visibility_api.py::test_nested_connection_costs_one_query_per_parent_without_the_optimizer``):
    a nested connection under a parent list pays parent list + one batched
    window query. Pinned at ONE cardinality, with the ABSOLUTE count that makes
    it distinguishing: 4 parent genres and exactly 2 queries, where a per-parent
    pipeline would pay 1 + 4. The two-cardinality form of the same property is
    earned live by
    ``examples/fakeshop/test_query/test_library_api.py::test_nested_books_connection_fixed_query_count``,
    which runs the identical shape at 3 and 10 genres.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    for gi in range(4):
        genre = Genre.objects.create(name=f"g{gi}")
        for title in ("a", "b", "c"):
            book = Book.objects.create(title=f"g{gi}-{title}", shelf=shelf)
            book.genres.add(genre)

    schema = _genres_list_schema(optimizer=True)
    with _capture_relations():
        result = _exec(
            schema,
            "{ objs { name booksConnection(first: 2) { edges { node { title } } } } }",
        )
    assert result.data is not None
    assert result.data == {
        "objs": [
            {
                "name": f"g{i}",
                "booksConnection": {
                    "edges": [{"node": {"title": f"g{i}-{suffix}"}} for suffix in ("a", "b")],
                },
            }
            for i in range(4)
        ],
    }


@pytest.mark.django_db
def test_fast_path_through_schema_connection_extension() -> None:
    """The fast path survives Strawberry's ``ConnectionExtension.resolve`` wrapper.

    MANDATORY (spec-033 Decision 5, the through-schema mandate): execute the real
    ``relay.connection(...)`` field end to end. The resolver returns a
    ``_WindowedConnectionRows`` node wrapper and the generated connection class builds the
    Relay object - a direct helper call would miss the ``ConnectionExtension`` layer boundary. The fixed query
    count (parent + one window, no per-parent query) proves the fast path fired
    rather than the per-parent pipeline.
    """
    _seed_window_books(["a", "b", "c"])
    schema = _genres_list_schema(optimizer=True)
    with _capture_relations():
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 2) { edges { node { title } } } } }",
        )
    assert result.data is not None
    titles = [
        json_at(e, "node", "title")
        for e in json_list(result.data, "objs", 0, "booksConnection", "edges")
    ]
    assert titles == ["a", "b"]

    _assert_same_partitions(result.data)


@pytest.mark.django_db
def test_divergent_aliases_one_window_query_per_alias() -> None:
    """Divergent aliases cost parents + ONE window query per alias.

    ``a: booksConnection(first: 2)`` + ``b: booksConnection(first: 5)`` take no
    whole-relation fallback (O(parents x aliases) per-parent
    queries); the per-response-key scheme plans one window per key and the
    resolver routes each alias to its ``_dst_books$<key>_connection`` attr via
    ``info.path.key`` - so the cost is ONE window PER ALIAS on top of the parent
    list, and each alias serves ITS OWN page bound. Pinned at ONE cardinality,
    with the ABSOLUTE count that makes it distinguishing: 4 parent genres, two
    aliases, and exactly 3 queries (1 parent list + 2 windows), where a
    per-parent pipeline would pay 1 + 4 x 2. The two-cardinality form of the
    parent-count property is earned live by
    ``examples/fakeshop/test_query/test_library_api.py::test_nested_books_connection_fixed_query_count``.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    for gi in range(4):
        genre = Genre.objects.create(name=f"g{gi}")
        for title in ("a", "b", "c"):
            book = Book.objects.create(title=f"g{gi}-{title}", shelf=shelf)
            book.genres.add(genre)

    schema = _genres_list_schema(optimizer=True)
    with _capture_relations(windows=2):
        result = _exec(
            schema,
            "{ objs { name "
            "a: booksConnection(first: 2) { edges { node { title } } } "
            "b: booksConnection(first: 5) { edges { node { title } } } "
            "} }",
        )
    assert result.data is not None
    assert result.data == {
        "objs": [
            {
                "name": f"g{i}",
                **{
                    alias: {
                        "edges": [{"node": {"title": f"g{i}-{suffix}"}} for suffix in suffixes],
                    }
                    for alias, suffixes in (("a", ("a", "b")), ("b", ("a", "b", "c")))
                },
            }
            for i in range(4)
        ],
    }


@pytest.mark.django_db
def test_divergent_aliases_wire_parity() -> None:
    """Divergent aliases: per-key windows and the pipeline are byte-identical.

    Full page, short page, cursors, and page flags - the optimizer-on wire
    payload for both aliases must equal the optimizer-less per-parent
    pipeline's, exactly like the shared-window parity pins.
    """
    _seed_window_books(
        [
            "a",
            "b",
            "c",
            "d",
        ],
    )
    selection = (
        "a: booksConnection(first: 2) { edges { cursor node { title } } "
        "pageInfo { hasNextPage hasPreviousPage startCursor endCursor } } "
        "b: booksConnection(first: 9) { edges { cursor node { title } } "
        "pageInfo { hasNextPage hasPreviousPage startCursor endCursor } }"
    )
    query = f"{{ objs {{ {selection} }} }}"

    with _capture_relations(windows=2):
        fast = _exec(_genres_list_schema(optimizer=True), query)
    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False), query)
    assert fast.data == slow.data
    # And the fast payload is substantively right, not vacuously equal.
    assert fast.data is not None
    fast_obj = json_at(fast.data, "objs", 0)
    assert [json_at(e, "node", "title") for e in json_list(fast_obj, "a", "edges")] == ["a", "b"]
    assert json_at(fast_obj, "a", "pageInfo", "hasNextPage") is True
    assert [json_at(e, "node", "title") for e in json_list(fast_obj, "b", "edges")] == [
        "a",
        "b",
        "c",
        "d",
    ]
    assert json_at(fast_obj, "b", "pageInfo", "hasNextPage") is False

    _assert_same_partitions(fast.data)


@pytest.mark.django_db
def test_divergent_mixed_sidecar_serves_each_alias_correctly() -> None:
    """A sidecar alias resolves per-parent while its divergent sibling is windowed.

    ``a`` (filtered) takes the per-parent pipeline and narrows correctly; ``b``
    (plain page) is served from its per-key window - one alias's refusal must
    not corrupt the other's rows.
    """
    _seed_window_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="off")
    with CaptureQueriesContext(db_connection) as captured:
        result = _exec(
            schema,
            "{ objs { "
            'a: booksConnection(filter: { title: { exact: "banana" } }) '
            "{ edges { node { title } } } "
            "b: booksConnection(first: 5) { edges { node { title } } } "
            "} }",
        )
    assert result.errors is None, result.errors
    assert result.data is not None
    obj = json_at(result.data, "objs", 0)
    assert [json_at(e, "node", "title") for e in json_list(obj, "a", "edges")] == ["banana"]
    assert [json_at(e, "node", "title") for e in json_list(obj, "b", "edges")] == [
        "apple",
        "banana",
        "avocado",
    ]

    _assert_same_partitions(result.data)
    assert len(_table_selects(captured, "library_genre")) == 1
    child_sql = _table_selects(captured, "library_book")
    assert len(child_sql) == 3, child_sql
    assert sum("ROW_NUMBER() OVER" in sql.upper() for sql in child_sql) == 1, child_sql
    fallback_sql = [sql for sql in child_sql if "ROW_NUMBER() OVER" not in sql.upper()]
    assert len(fallback_sql) == 2
    assert all("banana" in sql for sql in fallback_sql), fallback_sql


@pytest.mark.django_db
def test_divergent_aliases_strictness_raise_planned_keys_silent() -> None:
    """Plain divergent aliases are PLANNED - strictness ``"raise"`` stays silent."""
    _seed_library_books(["a", "b", "c"])
    schema = _genres_list_schema(optimizer=True, strictness="raise")
    result = _exec(
        schema,
        "{ objs { "
        "a: booksConnection(first: 2) { edges { node { title } } } "
        "b: booksConnection(first: 5) { edges { node { title } } } "
        "} }",
    )
    assert result.errors is None, result.errors
    assert result.data is not None
    obj = json_at(result.data, "objs", 0)
    assert [json_at(e, "node", "title") for e in json_list(obj, "a", "edges")] == ["a", "b"]
    assert [json_at(e, "node", "title") for e in json_list(obj, "b", "edges")] == ["a", "b", "c"]


@pytest.mark.django_db
def test_distinct_target_fallback_reports_correct_total_count() -> None:
    """A ``.distinct()`` target falls back per-parent AND reports the right ``totalCount``.

    Earns the executed second clause of the walker's plan-shape pin
    ``test_distinct_child_queryset_left_unplanned_for_correct_total_count``: the
    ``genres__isnull=False`` join fans each multi-genre book into several rows, so
    a window ``Count(1) OVER`` would report the inflated pre-DISTINCT total; the
    per-parent fallback instead counts ``.distinct()`` and reports the true book
    count. Run with the optimizer ON so the DISTINCT guard is what routes the
    selection to the counting fallback.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    fiction = Genre.objects.create(name="fiction")
    scifi = Genre.objects.create(name="scifi")
    # fiction holds {a, b, c} = 3 distinct books; a and c are ALSO in scifi, so the
    # genres-join fans fiction's rows out to a(2) + b(1) + c(2) = 5 pre-DISTINCT.
    for title, extra in (("a", scifi), ("b", None), ("c", scifi)):
        book = Book.objects.create(title=title, shelf=shelf)
        book.genres.add(fiction)
        if extra is not None:
            book.genres.add(extra)

    schema = _genres_distinct_book_schema(optimizer=True)
    result = _exec(schema, "{ objs { name booksConnection { totalCount } } }")
    assert result.data is not None
    by_name = {
        json_at(g, "name"): json_at(g, "booksConnection", "totalCount")
        for g in json_list(result.data, "objs")
    }
    # True distinct count (3), NOT the inflated 5 a pre-DISTINCT Count(1) OVER reports.
    assert by_name == {"fiction": 3, "scifi": 2}


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "mode",
        "expected_titles",
        "has_next",
        "has_previous",
    ),
    [
        pytest.param("first", ["a", "b"], True, False, id="first-page"),
        pytest.param(
            "overrun",
            [
                "a",
                "b",
                "c",
                "d",
            ],
            False,
            False,
            id="overrun",
        ),
        pytest.param("after", ["b", "c"], True, True, id="continuation"),
    ],
)
def test_fast_path_wire_parity_with_pipeline(
    mode: str,
    expected_titles: list[str],
    *,
    has_next: bool,
    has_previous: bool,
) -> None:
    """Identical edges / cursors / pageInfo for the same data, optimizer on vs off.

    The core parity matrix: the fast path (optimizer installed, window consumed)
    and the per-parent pipeline (no optimizer) must produce byte-identical wire
    results across forward windows, overruns, and ``after:`` continuation.
    """
    _seed_window_books(
        [
            "a",
            "b",
            "c",
            "d",
        ],
    )
    schema = _genres_list_schema(optimizer=True)
    args = "first: 10" if mode == "overrun" else "first: 2"
    if mode == "after":
        prior = _exec(schema, "{ objs { booksConnection(first: 1) { pageInfo { endCursor } } } }")
        cursor = json_at(prior.data, "objs", 0, "booksConnection", "pageInfo", "endCursor")
        assert isinstance(cursor, str)
        args += f', after: "{cursor}"'
    selection = (
        f"booksConnection({args}) {{ edges {{ cursor node {{ title }} }} "
        f"pageInfo {{ hasNextPage hasPreviousPage startCursor endCursor }} }}"
    )
    query = f"{{ objs {{ {selection} }} }}"

    # The seeded rows persist across both schema builds in one test transaction;
    # only the registry / connection-cache need clearing between the two
    # ``DjangoType`` declarations (re-seeding would collide on unique fields).
    with _capture_relations(windows=1):
        fast = _exec(schema, query)
    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False), query)
    assert fast.data == slow.data

    assert fast.data is not None
    conn = json_at(fast.data, "objs", 0, "booksConnection")
    assert [json_at(e, "node", "title") for e in json_list(conn, "edges")] == expected_titles
    assert json_at(conn, "pageInfo", "hasNextPage") is has_next
    assert json_at(conn, "pageInfo", "hasPreviousPage") is has_previous

    _assert_same_partitions(fast.data)


@pytest.mark.django_db
def test_fast_path_wire_parity_last_only() -> None:
    """Reversed (``last``-only) window maps to the SAME cursors and page flags.

    The planner keeps ``_dst_row_number`` forward (a separate
    ``_dst_row_number_reversed`` drives only the plan-time row filter), so the
    fast path's positional cursor (``_dst_row_number - 1``) and forward page-flag
    comparisons land on the pipeline's values for a ``last``-only page too.
    """
    _seed_window_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    selection = (
        "booksConnection(last: 2) { edges { cursor node { title } } "
        "pageInfo { hasNextPage hasPreviousPage startCursor endCursor } }"
    )
    query = f"{{ objs {{ {selection} }} }}"

    with _capture_relations(windows=1):
        fast = _exec(_genres_list_schema(optimizer=True), query)
    assert fast.data is not None
    fast_conn = json_at(fast.data, "objs", 0, "booksConnection")
    assert [json_at(e, "node", "title") for e in json_list(fast_conn, "edges")] == ["d", "e"]
    assert json_at(fast_conn, "pageInfo", "hasPreviousPage") is True
    assert json_at(fast_conn, "pageInfo", "hasNextPage") is False

    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False), query)
    assert fast.data == slow.data

    _assert_same_partitions(fast.data)


@pytest.mark.django_db
def test_windowed_last_page_reverses_a_bare_expression_ordering() -> None:
    """A ``last: N`` window under an EXPRESSION ordering serves the partition's TAIL.

    ``_reverse_order_by`` builds ``_dst_row_number_reversed`` and flips a term
    with no ``descending`` slot (here ``Lower("title")``) too; passed through
    unflipped, the reversed numbering would run FORWARD on that column and
    ``rn_reversed <= N`` would return the partition's FIRST rows. Seeded in the
    inverse of title order so pk order and ``Lower(title)`` order disagree -
    otherwise the pk tiebreaker alone would mask the unflipped term.

    Pinned as an optimizer-on/off wire comparison AND a query-count assertion:
    without the count the test could pass by silently falling back to the
    per-parent pipeline instead of proving the WINDOW reverses correctly.
    """
    _seed_window_books(
        [
            "e",
            "d",
            "c",
            "b",
            "a",
        ],
    )
    selection = (
        "booksConnection(last: 2) { edges { cursor node { title } } "
        "pageInfo { hasNextPage hasPreviousPage } }"
    )
    query = f"{{ objs {{ {selection} }} }}"

    with _capture_relations():  # parents + ONE windowed prefetch.
        fast = _exec(_genres_expression_ordered_schema(optimizer=True), query)
    assert fast.data is not None
    fast_conn = json_at(fast.data, "objs", 0, "booksConnection")
    assert [json_at(e, "node", "title") for e in json_list(fast_conn, "edges")] == ["d", "e"]
    assert json_at(fast_conn, "pageInfo", "hasPreviousPage") is True
    assert json_at(fast_conn, "pageInfo", "hasNextPage") is False

    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_expression_ordered_schema(optimizer=False), query)
    assert fast.data == slow.data

    _assert_same_partitions(fast.data)


@pytest.mark.django_db
def test_nested_window_count_observers_follow_a_non_camel_case_schema() -> None:
    """``auto_camel_case=False`` renames the count observers; the planner must follow.

    The observers are matched by the Python name each field was published from
    (``optimizer/selections.py::selection_python_name``). Matching camelCase
    wire literals made BOTH report absent on such a schema, so the window
    carried neither the partition count nor the n+1 probe: ``has_next_page``
    resolved ``False`` on a page that had one, and ``total_count`` raised
    ``AttributeError`` for an attribute ``resolve_connection`` never set.

    Asserted against the identical query on the default-converter schema so the
    two vocabularies are proven to agree, and with a query count so a silent
    per-parent fallback cannot green it.
    """
    _seed_window_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    snake = (
        "books_connection(first: 2) { total_count "
        "page_info { has_next_page has_previous_page } edges { node { title } } }"
    )
    with _capture_relations():  # parents + ONE windowed prefetch.
        result = _exec(
            _genres_expression_ordered_schema(optimizer=True, auto_camel_case=False),
            f"{{ objs {{ {snake} }} }}",
        )
    assert result.data is not None
    conn = json_at(result.data, "objs", 0, "books_connection")
    assert json_at(conn, "total_count") == 5
    assert json_at(conn, "page_info", "has_next_page") is True
    assert json_at(conn, "page_info", "has_previous_page") is False
    assert [json_at(e, "node", "title") for e in json_list(conn, "edges")] == ["a", "b"]

    registry.clear()
    _connection_type_cache.clear()
    camel = (
        "booksConnection(first: 2) { totalCount "
        "pageInfo { hasNextPage hasPreviousPage } edges { node { title } } }"
    )
    default = _exec(
        _genres_expression_ordered_schema(optimizer=True, auto_camel_case=True),
        f"{{ objs {{ {camel} }} }}",
    )
    assert default.data is not None
    default_conn = json_at(default.data, "objs", 0, "booksConnection")
    assert json_at(default_conn, "totalCount") == json_at(conn, "total_count")
    assert json_at(default_conn, "pageInfo", "hasNextPage") == json_at(
        conn,
        "page_info",
        "has_next_page",
    )
    assert [json_at(e, "node", "title") for e in json_list(default_conn, "edges")] == ["a", "b"]

    _assert_same_partitions(result.data)

    assert default.data == {
        "objs": [
            {
                "booksConnection": {
                    "totalCount": 5,
                    "edges": [{"node": {"title": title}} for title in ("a", "b")],
                    "pageInfo": {"hasNextPage": True, "hasPreviousPage": False},
                },
            },
        ]
        * 2,
    }


@pytest.mark.django_db(transaction=True)
def test_fast_path_non_pk_ordering_applies_explicit_deterministic_order_by() -> None:
    """A non-pk-ordered child: the windowed prefetch's outer ORDER BY carries the pk tiebreaker.

    The pk-ordered parity tests order ``Book`` by pk, where DB-natural (rowid) order
    coincides with the window order and cannot expose a missing
    ``queryset.order_by``. Even here, where the child orders by a non-pk
    ``Meta.ordering`` (``title``), SQLite's window sort emits rows in title order
    and Django propagates ``Meta.ordering`` to the outer query on its own - so a
    wire comparison cannot catch a missing order on SQLite. What this row uniquely pins is
    the **deterministic order** applied to the queryset: the outer ORDER BY gains
    the pk tiebreaker (``ORDER BY <title>, <pk>``) instead of the single
    ``Meta.ordering`` column, which is what keeps fast-path cursors stable across
    rows that tie on ``title``. This asserts that two-column outer order directly
    on the prefetch SQL (the deterministic-order regression) and pins
    optimizer-on vs optimizer-off wire parity for the distinct-title case.

    ``OConnTag`` / ``OConnPost`` stay test-local models: the example child with a
    non-pk ``Meta.ordering`` (kanban ``Decision``) reads the same outer
    ``ORDER BY <order column>, pk`` live in
    ``examples/fakeshop/test_query/test_kanban_api.py``, and the clause only this
    row carries is the optimizer-off parity, which needs a second schema built
    without ``DjangoOptimizerExtension`` over one declared child type. The pair is a
    legal consumer shape is mounted over HTTP to compare the two strategies
    under the same non-pk order and exact page contract.
    """

    class OConnTag(djmodels.Model):
        name: "djmodels.TextField[str | Combinable, str]" = djmodels.TextField()

        class Meta:
            app_label = "products"
            managed = False
            ordering = ["id"]

        @override
        def __str__(self) -> str:
            return self.name

    class OConnPost(djmodels.Model):
        title: "djmodels.TextField[str | Combinable, str]" = djmodels.TextField()
        tag: "djmodels.ForeignKey[OConnTag | Combinable, OConnTag]" = djmodels.ForeignKey(
            OConnTag,
            related_name="posts",
            on_delete=djmodels.CASCADE,
        )

        class Meta:
            app_label = "products"
            managed = False
            ordering = ["title"]

        @override
        def __str__(self) -> str:
            return self.title

    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(OConnTag)
        schema_editor.create_model(OConnPost)
    try:
        tag = OConnTag.objects.create(name="t")
        for title in (
            "d",
            "a",
            "c",
            "b",
        ):  # pk order (d,a,c,b) != title order (a,b,c,d)
            OConnPost.objects.create(title=title, tag=tag)
        # A SECOND parent keeps the prefetch multi-parent so the windowed body
        # runs: the single-parent degenerate fast path
        # (optimizer/single_parent_fetch.py) would otherwise serve a plain
        # filtered LIMIT (no ROW_NUMBER) for a lone parent, which this test
        # cannot inspect for the outer ORDER BY tiebreaker. The fast path applies
        # the SAME deterministic order; here we pin the windowed path explicitly.
        other = OConnTag.objects.create(name="u")
        for title in ("z", "y"):
            OConnPost.objects.create(title=title, tag=other)

        query = (
            "{ objs { name postsConnection(first: 2) { edges { cursor node { title } } "
            "pageInfo { startCursor endCursor } } } }"
        )

        def _build(*, optimizer: bool) -> strawberry.Schema:
            declare_django_type(
                "OConnPostType",
                {
                    "Meta": type(
                        "Meta",
                        (),
                        {
                            "model": OConnPost,
                            "fields": ("id", "title"),
                            "interfaces": (relay.Node,),
                        },
                    ),
                },
            )
            tag_type = _make_type("OConnTagType", OConnTag, ("id", "name", "posts"))
            finalize_django_types()
            query_cls = strawberry.type(
                type(
                    "Query",
                    (),
                    {
                        "__annotations__": {"objs": list[tag_type]},
                        "objs": DjangoListField(tag_type),
                    },
                ),
            )
            extensions = []
            if optimizer:
                optimizer_ext = DjangoOptimizerExtension()
                extensions = [lambda: optimizer_ext]
            return DjangoSchema(
                error_policy={"enabled": False},
                query=query_cls,
                config=strawberry_config(),
                extensions=extensions,
            )

        with CaptureQueriesContext(db_connection) as ctx:
            fast = _exec(_build(optimizer=True), query)
        window_sql = next(
            q["sql"] for q in ctx.captured_queries if "ROW_NUMBER" in q["sql"].upper()
        )
        # The outer query (after the row-number filter) must order by the FULL
        # deterministic tuple - title AND the pk tiebreaker. Without the explicit
        # `queryset.order_by`, Django still propagates the single Meta.ordering
        # column. Resolve the selected aliases back to the actual model columns,
        # then require title followed by the primary key rather than any two terms.
        tail = window_sql.upper().split('"_DST_ROW_NUMBER" <=')[-1]
        assert "ORDER BY" in tail, window_sql
        outer_order = tail.split("ORDER BY", 1)[-1]
        aliases: list[str] = []
        for field in (OConnPost._meta.get_field("title"), OConnPost._meta.pk):
            assert isinstance(field, djmodels.Field)
            column = field.column
            assert isinstance(column, str)
            selected = (
                f"{db_connection.ops.quote_name(OConnPost._meta.db_table)}."
                f"{db_connection.ops.quote_name(column)} AS "
            )
            match = re.search(re.escape(selected) + r'"([^"]+)"', window_sql)
            assert match is not None, window_sql
            aliases.append(db_connection.ops.quote_name(match[1]).upper())
        assert outer_order.strip() == f"{aliases[0]} ASC, {aliases[1]} ASC", window_sql

        registry.clear()
        _connection_type_cache.clear()
        slow = _exec(_build(optimizer=False), query)
        assert fast.data == slow.data
        assert fast.data is not None
        titles = [
            json_at(e, "node", "title")
            for e in json_list(fast.data, "objs", 0, "postsConnection", "edges")
        ]
        assert titles == ["a", "b"]
        assert [json_at(g, "name") for g in json_list(fast.data, "objs")] == ["t", "u"]
        assert [
            json_at(e, "node", "title")
            for e in json_list(
                fast.data,
                "objs",
                1,
                "postsConnection",
                "edges",
            )
        ] == ["y", "z"]
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(OConnPost)
            schema_editor.delete_model(OConnTag)


@pytest.mark.django_db
def test_fast_path_cursor_round_trips_to_fallback_after() -> None:
    """A fast-path ``endCursor`` fed to ``after:`` on an optimizer-less execution continues.

    The cursor-parity invariant's observable proof (spec-033 Decision 4): the
    fast path's positional offset cursors are format-compatible with the
    pipeline's, so a page-1 ``endCursor`` captured under the optimizer drives a
    correct page-2 ``after:`` with the optimizer absent.
    """
    _seed_window_books(
        [
            "a",
            "b",
            "c",
            "d",
        ],
    )
    with _capture_relations():
        fast = _exec(
            _genres_list_schema(optimizer=True),
            "{ objs { booksConnection(first: 2) { pageInfo { endCursor } } } }",
        )
    assert fast.data is not None
    end_cursor = json_at(fast.data, "objs", 0, "booksConnection", "pageInfo", "endCursor")

    registry.clear()
    _connection_type_cache.clear()
    page_two = _exec(
        _genres_list_schema(optimizer=False),
        f'{{ objs {{ booksConnection(first: 2, after: "{end_cursor}") '
        f"{{ edges {{ node {{ title }} }} }} }} }}",
    )
    assert page_two.data is not None
    titles = [
        json_at(e, "node", "title")
        for e in json_list(page_two.data, "objs", 0, "booksConnection", "edges")
    ]
    assert titles == ["c", "d"]

    _assert_same_partitions(fast.data)
    _assert_same_partitions(page_two.data)


@pytest.mark.django_db
def test_fast_path_fires_for_reverse_fk_without_related_name() -> None:
    """The fast path fires for a reverse FK without ``related_name``.

    spec-033 Decision 5: the resolver receives the relation FIELD NAME
    (``repairticket``), not the accessor (``repairticket_set``), so its
    ``_dst_<field>_connection`` probe matches the ``to_attr`` the walker keyed
    on the field name. The fixed query count (parent + one window) proves the
    fast path fired rather than silently falling back because the probe missed.
    The shipped ``VenueType`` publishes no ``repairticketConnection``, so the
    window is planned here over test-local types on ``Venue`` / ``RepairTicket``.
    """
    repairticket_rel = Venue._meta.get_field("repairticket")
    assert isinstance(repairticket_rel, ForeignObjectRel)
    assert repairticket_rel.get_accessor_name() == "repairticket_set"

    declare_django_type(
        "RepairTicketNode",
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": RepairTicket,
                    "fields": ("id", "code"),
                    "interfaces": (relay.Node,),
                },
            ),
        },
    )
    venue_type = _make_type("VenueNode", Venue, ("id", "name", "repairticket"))
    finalize_django_types()

    def ordered_venues(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> djmodels.QuerySet[Venue]:
        return Venue.objects.order_by("pk")

    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[venue_type]},
                "objs": DjangoListField(venue_type, resolver=ordered_venues),
            },
        ),
    )
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        error_policy={"enabled": False},
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    for vi in range(3):
        venue = Venue.objects.create(name=f"v{vi}")
        for ti in range(3):
            RepairTicket.objects.create(code=f"v{vi}-t{ti}", venue=venue)

    with _capture_relations(parent_table="library_venue", child_table="library_repairticket"):
        result = _exec(
            schema,
            "{ objs { name repairticketConnection(first: 2) { edges { node { code } } } } }",
        )
    assert result.data is not None
    assert result.data == {
        "objs": [
            {
                "name": f"v{i}",
                "repairticketConnection": {
                    "edges": [{"node": {"code": f"v{i}-t{j}"}} for j in range(2)],
                },
            }
            for i in range(3)
        ],
    }


@pytest.mark.django_db
def test_fast_path_total_count_from_annotation_no_query() -> None:
    """A fast-path ``totalCount`` reads ``_dst_total_count`` - zero extra COUNT queries."""
    _seed_window_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    schema = _genres_list_schema(optimizer=True, book_total_count=True)
    with _capture_relations():  # parent + window only; no per-relation COUNT
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 2) { totalCount edges { node { title } } } } }",
        )
    assert result.data is not None
    assert result.data["objs"][0]["booksConnection"]["totalCount"] == 5

    _assert_same_partitions(result.data)

    assert result.data == {
        "objs": [
            {
                "booksConnection": {
                    "totalCount": 5,
                    "edges": [{"node": {"title": "a"}}, {"node": {"title": "b"}}],
                },
            },
        ]
        * 2,
    }


@pytest.mark.django_db
def test_fast_path_has_next_page_without_edges_on_window() -> None:
    """``hasNextPage`` is correct on the WINDOW path even when ``edges`` is unrequested.

    The Relay invariant (spec-032 Goal 4 / DoD: "the connection MUST resolve
    ``hasNextPage`` correctly even when the consumer didn't request ``edges``")
    asserted on the exact path spec-033 introduces - the others assert it only on
    the root field and the optimizer-less per-parent fallback. A nested
    ``booksConnection { pageInfo { hasNextPage } }`` with no ``edges`` is
    recognized by field name, window-planned as a scalar-only projection, and
    serves ``hasNextPage`` from the extra-row probe, without a count aggregate.
    It is correct WITHOUT ``edges`` AND WITHOUT the ``totalCount`` opt-in
    (``book_total_count=False`` here), and it costs one batched window query (no
    per-parent fallback, no per-relation COUNT).
    """
    _seed_window_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    schema = _genres_list_schema(optimizer=True)  # NO totalCount opt-in
    with _capture_relations() as captured:  # parent + window only; no edges, no fallback
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 2) { pageInfo { hasNextPage } } } }",
        )
    # 5 books, first: 2 -> a further page exists.
    assert result.data is not None
    assert result.data["objs"][0]["booksConnection"]["pageInfo"]["hasNextPage"] is True

    _assert_same_partitions(result.data)

    assert all("COUNT(" not in sql.upper() for sql in _table_selects(captured, "library_book"))


@pytest.mark.django_db
def test_fast_path_has_no_next_page_at_boundary_without_edges_on_window() -> None:
    """The boundary twin: ``first >= total`` -> ``hasNextPage`` False on the window path.

    Pins that the scalar-only window's ``hasNextPage`` is not hard-wired True: 5
    books with ``first: 5`` exhausts the window, so ``hasNextPage`` is False -
    still served from the annotation with no ``edges`` selected.
    """
    _seed_window_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    schema = _genres_list_schema(optimizer=True)
    with _capture_relations():
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 5) { pageInfo { hasNextPage } } } }",
        )
    assert result.data is not None
    assert result.data["objs"][0]["booksConnection"]["pageInfo"]["hasNextPage"] is False

    _assert_same_partitions(result.data)


@pytest.mark.django_db
def test_fast_path_total_count_without_edges_on_window() -> None:
    """``totalCount`` alone (no ``edges``) reads ``_dst_total_count`` on the window path.

    The totalCount-only sibling of the pageInfo-only pin: a nested
    ``booksConnection { totalCount }`` with no ``edges`` is the scalar-only window
    projection, served from the annotation in a single batched window query - the
    existing ``totalCount`` window pins all also select ``edges``.
    """
    _seed_window_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    schema = _genres_list_schema(optimizer=True, book_total_count=True)
    with _capture_relations():  # parent + window only; no edges, no per-relation COUNT
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 2) { totalCount } } }",
        )
    assert result.data is not None
    assert result.data["objs"][0]["booksConnection"]["totalCount"] == 5

    _assert_same_partitions(result.data)


@pytest.mark.django_db
@pytest.mark.parametrize("overshot", [False, True], ids=["zero-bound", "overshot-cursor"])
def test_fast_path_ambiguous_empty_served_from_marker_row(
    *,
    overshot: bool,
) -> None:
    """``first: 0`` (``limit == 0``) and overshot ``after:`` (``offset > 0``) serve from markers.

    The marker-row disambiguation (spec-033 Decision 5):
    an empty window alone is ambiguous for these shapes, so the window keeps
    each partition's row 1, and the empty page
    is served with the TRUE ``totalCount`` / ``pageInfo`` - byte-identical to
    the pipeline - in the fixed two-query cost with NO per-parent fallback.
    """
    _seed_window_books(["a", "b", "c"])
    # Offset 99 deliberately lies beyond all rows and has no real prior page.
    cursor = relay.to_base64(relay.Edge.CURSOR_PREFIX, 99)
    args = f'first: 2, after: "{cursor}"' if overshot else "first: 0"
    selection = (
        f"booksConnection({args}) {{ edges {{ node {{ title }} }} totalCount "
        f"pageInfo {{ hasNextPage hasPreviousPage }} }}"
    )
    query = f"{{ objs {{ {selection} }} }}"

    with _capture_relations():  # parent + window; the fallback never fires.
        fast = _exec(_genres_list_schema(optimizer=True, book_total_count=True), query)
    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False, book_total_count=True), query)
    assert fast.data == slow.data
    # The marker carries the true totalCount (3), never a spurious 0 from
    # inferring "the window is empty so the parent is empty".
    assert fast.data is not None
    assert fast.data["objs"][0]["booksConnection"]["totalCount"] == 3

    _assert_same_partitions(fast.data)

    assert fast.data == {
        "objs": [
            {
                "booksConnection": {
                    "edges": [],
                    "totalCount": 3,
                    "pageInfo": {"hasNextPage": not overshot, "hasPreviousPage": overshot},
                },
            },
        ]
        * 2,
    }


@pytest.mark.django_db(transaction=True)
async def test_async_fast_path_last_zero_serves_the_first_zero_page(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """``last: 0`` under ASYNC execution is the ``first: 0`` page served from the window.

    Driven by the async HTTP view: empty ``edges``, the true
    ``totalCount`` and ``first: 0``'s ``pageInfo`` (a next page exists), the
    same payload ``first: 0`` returns on the same schema.
    """
    await sync_to_async(_seed_window_books)(["a", "b", "c"])
    schema = await sync_to_async(_genres_list_schema)(optimizer=True, book_total_count=True)
    page = (
        "{ edges { node { title } } totalCount "
        "pageInfo { hasNextPage hasPreviousPage startCursor endCursor } }"
    )
    parents = record_compiled_sql('FROM "library_genre"')
    children = record_compiled_sql('FROM "library_book"')
    last_zero = await _exec_async(schema, f"{{ objs {{ booksConnection(last: 0) {page} }} }}")
    first_zero = await _exec_async(schema, f"{{ objs {{ booksConnection(first: 0) {page} }} }}")
    assert last_zero.errors is None, last_zero.errors
    assert first_zero.errors is None, first_zero.errors
    assert last_zero.data is not None
    assert last_zero.data["objs"][0]["booksConnection"] == {
        "edges": [],
        "totalCount": 3,
        "pageInfo": {
            "hasNextPage": True,
            "hasPreviousPage": False,
            "startCursor": None,
            "endCursor": None,
        },
    }
    assert last_zero.data == first_zero.data

    _assert_same_partitions(last_zero.data)

    assert len(parents) == 2, parents
    assert len(children) == 2, children
    assert all("ROW_NUMBER() OVER" in sql.upper() for sql in children), children


@pytest.mark.django_db
def test_fast_path_last_zero_serves_the_first_zero_page() -> None:
    """``last: 0`` is the planned ``first: 0`` window, optimizer on and off alike.

    The walker plans the ``first: 0`` window for it, so the page is served from
    the marker row in the fixed two-query cost, and the payload is the one
    ``first: 0`` returns and the one the optimizer-off pipeline returns.
    """
    _seed_window_books(["a", "b", "c"])
    page = (
        "{ edges { node { title } } totalCount "
        "pageInfo { hasNextPage hasPreviousPage startCursor endCursor } }"
    )
    query = f"{{ objs {{ booksConnection(last: 0) {page} }} }}"

    schema = _genres_list_schema(optimizer=True, book_total_count=True)
    with CaptureQueriesContext(db_connection) as captured:
        fast = _exec(schema, query)
    assert len(_table_selects(captured, "library_genre")) == 1
    child_sql = _table_selects(captured, "library_book")
    assert len(child_sql) == 1
    assert "_dst_row_number" in child_sql[0]
    assert fast.data == _exec(schema, f"{{ objs {{ booksConnection(first: 0) {page} }} }}").data
    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False, book_total_count=True), query)
    assert fast.data == slow.data
    assert fast.data is not None
    assert fast.data["objs"][0]["booksConnection"]["edges"] == []
    assert fast.data["objs"][0]["booksConnection"]["pageInfo"]["hasNextPage"] is True

    _assert_same_partitions(fast.data)

    assert fast.data == {
        "objs": [
            {
                "booksConnection": {
                    "edges": [],
                    "totalCount": 3,
                    "pageInfo": {
                        "hasNextPage": True,
                        "hasPreviousPage": False,
                        "startCursor": None,
                        "endCursor": None,
                    },
                },
            },
        ]
        * 2,
    }


@pytest.mark.django_db
def test_fast_path_genuinely_empty_parent_serves_zero() -> None:
    """A parent with no related rows is fast-pathed: totalCount 0, no fallback query.

    Empty window with ``offset == 0`` and a positive bound proves the parent
    genuinely has none, so the fast path serves ``totalCount = 0`` / no cursors /
    both flags ``False`` without a per-parent fallback query.
    """
    branch = Branch.objects.create(name="central")
    Shelf.objects.create(code="A1", branch=branch)
    Genre.objects.create(name="empty")
    Genre.objects.create(name="also-empty")
    schema = _genres_list_schema(optimizer=True, book_total_count=True)
    with _capture_relations():  # parent + the (empty) window; no fallback
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 2) { totalCount edges { node { title } } "
            "pageInfo { hasNextPage hasPreviousPage } } } }",
        )
    assert result.data is not None
    conn = json_at(result.data, "objs", 0, "booksConnection")
    assert json_at(conn, "edges") == []
    assert json_at(conn, "totalCount") == 0
    assert json_at(conn, "pageInfo") == {"hasNextPage": False, "hasPreviousPage": False}

    _assert_same_partitions(result.data)


@pytest.mark.django_db
@pytest.mark.parametrize("overshot", [False, True], ids=["zero-bound", "overshot-cursor"])
def test_fast_path_zero_children_parent_serves_under_ambiguous_shapes(
    *,
    overshot: bool,
) -> None:
    """A zero-children parent is served (not fallen back) under the marker shapes.

    The marker contract's serve side (spec-033 Decision 5): with markers
    planned, an EMPTY window under
    ``first: 0`` / overshot ``after:`` PROVES the parent has no children
    (a parent with children would have kept its row 1), so the fast path
    serves ``totalCount 0`` in the fixed two-query cost. Byte parity with the
    pipeline pins the flag arithmetic - notably ``hasPreviousPage`` is True
    for the overshot ``after:`` even with zero children, because upstream
    ``ListConnection`` computes ``start > 0`` before looking at the data.
    """
    branch = Branch.objects.create(name="central")
    Shelf.objects.create(code="A1", branch=branch)
    Genre.objects.create(name="empty")
    Genre.objects.create(name="also-empty")
    # Offset 99 deliberately lies beyond all rows and has no real prior page.
    cursor = relay.to_base64(relay.Edge.CURSOR_PREFIX, 99)
    args = f'first: 2, after: "{cursor}"' if overshot else "first: 0"
    selection = (
        f"booksConnection({args}) {{ totalCount edges {{ node {{ title }} }} "
        f"pageInfo {{ hasNextPage hasPreviousPage }} }}"
    )
    query = f"{{ objs {{ {selection} }} }}"
    with _capture_relations():  # parent + the (empty) window; no fallback
        fast = _exec(_genres_list_schema(optimizer=True, book_total_count=True), query)
    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False, book_total_count=True), query)
    assert fast.data == slow.data
    assert fast.data is not None
    conn = json_at(fast.data, "objs", 0, "booksConnection")
    assert json_at(conn, "edges") == []
    assert json_at(conn, "totalCount") == 0

    _assert_same_partitions(fast.data)

    assert fast.data == {
        "objs": [
            {
                "booksConnection": {
                    "edges": [],
                    "totalCount": 0,
                    "pageInfo": {"hasNextPage": False, "hasPreviousPage": overshot},
                },
            },
        ]
        * 2,
    }


@pytest.mark.django_db
def test_outer_total_count_predicate_ignores_nested_total_count() -> None:
    """A nested connection's ``totalCount`` does not fire the OUTER connection's count.

    Per spec-033 Edge cases (the outer-``totalCount`` direct-children-scoped
    rule), with nested ``totalCount`` a fast-path read: a two-level selection of
    the nested ``totalCount`` must not make the root connection's ``_total_count_requested``
    predicate fire (no spurious outer COUNT, no outer non-queryset guard raise). The root here is a
    ``DjangoConnectionField`` (its own ``totalCount`` opt-in) whose ``totalCount``
    is NOT selected - only the nested one is.
    """
    _seed_library_books(["a", "b", "c"])
    make_django_type(
        "BookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
    )
    genre_type = _make_type(
        "GenreType",
        Genre,
        ("id", "name", "books"),
        meta_extra={"connection": {"total_count": True}},
    )
    finalize_django_types()

    conn_type = _connection_type_for(genre_type, genre_type.__django_strawberry_definition__)
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"objs": conn_type}, "objs": DjangoConnectionField(genre_type)},
        ),
    )
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        error_policy={"enabled": False},
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    # Only the NESTED totalCount is selected; the outer one is not. The outer
    # predicate must stay False (its direct children are edges + the nested
    # connection), so no spurious root COUNT fires and no outer non-queryset
    # guard raises.
    with CaptureQueriesContext(db_connection) as captured:
        result = _exec(
            schema,
            "{ objs { edges { node { name booksConnection(first: 2) "
            "{ totalCount edges { node { title } } } } } } }",
        )
    assert result.errors is None, result.errors
    assert result.data is not None
    genre_node = json_at(result.data, "objs", "edges", 0, "node")
    assert json_at(genre_node, "booksConnection", "totalCount") == 3

    root_statements = _table_selects(captured, "library_genre")
    assert len(root_statements) == 1, root_statements
    assert "COUNT(" not in root_statements[0].upper(), root_statements
    assert result.data == {
        "objs": {
            "edges": [
                {
                    "node": {
                        "name": "fiction",
                        "booksConnection": {
                            "totalCount": 3,
                            "edges": [{"node": {"title": "a"}}, {"node": {"title": "b"}}],
                        },
                    },
                },
            ],
        },
    }


@pytest.mark.django_db
def test_strictness_warn_logs_once_per_occurrence(caplog: pytest.LogCaptureFixture) -> None:
    """``"warn"`` + a fallback nested connection -> logged warning, execution CONTINUES.

    The query still resolves correctly (warn does not abort); the resolver
    logger emits a warning naming the field. Pinned via ``caplog``.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="warn")
    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = _exec(
        schema,
        '{ objs { booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } } }",
    )
    assert result.errors is None, result.errors
    # Warn continues: the filtered page is still served correctly.
    assert result.data is not None
    titles = [
        json_at(e, "node", "title")
        for e in json_list(result.data, "objs", 0, "booksConnection", "edges")
    ]
    assert titles == ["banana"]
    warnings = [
        r.getMessage() for r in caplog.records if r.name.startswith("django_strawberry_framework")
    ]
    assert warnings == [
        (
            "Potential N+1 on books (not window-planned: selection carries filter/orderBy; "
            "resolving per-parent)"
        ),
    ]


@pytest.mark.django_db
def test_strictness_silent_when_window_served(caplog: pytest.LogCaptureFixture) -> None:
    """``"raise"`` + a WINDOW-PLANNED nested connection -> no raise, no warn.

    The fast path served the rows under ``_dst_books_connection`` (the ``to_attr``
    is present on each parent), so ``_check_n1``'s connection lazy probe returns
    "not lazy" and the contract is silent. Wire result correct.
    """
    _seed_window_books(["apple", "banana", "avocado"])
    caplog.set_level("WARNING", logger="django_strawberry_framework")
    schema = _genres_list_schema(optimizer=True, strictness="raise")
    with _capture_relations():
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 2) { edges { node { title } } } } }",
        )
    assert result.errors is None, result.errors
    assert result.data is not None
    titles = [
        json_at(e, "node", "title")
        for e in json_list(result.data, "objs", 0, "booksConnection", "edges")
    ]
    assert titles == ["apple", "banana"]

    assert not [r for r in caplog.records if "Potential N+1" in r.getMessage()]

    _assert_same_partitions(result.data)


@pytest.mark.django_db
def test_strictness_silent_when_off(caplog: pytest.LogCaptureFixture) -> None:
    """``"off"`` (optimizer installed) -> neither raise nor warn on a fallback.

    ``strictness == "off"`` is the resolver's no-op: the extension arms that
    value on the per-execution strictness ``ContextVar`` at ``on_execute``
    entry, so ``types/resolvers.py::_strictness_for`` answers ``"off"`` and
    ``_check_n1``'s prelude returns immediately - before any sentinel or
    ``to_attr`` probe - even on the unplanned sidecar fallback.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    caplog.set_level("WARNING", logger="django_strawberry_framework")
    schema = _genres_filterable_book_schema(strictness="off")
    result = _exec(
        schema,
        '{ objs { booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } } }",
    )
    assert result.errors is None, result.errors
    assert result.data is not None
    titles = [
        json_at(e, "node", "title")
        for e in json_list(result.data, "objs", 0, "booksConnection", "edges")
    ]
    assert titles == ["banana"]

    assert not [r for r in caplog.records if "Potential N+1" in r.getMessage()]


@pytest.mark.django_db
def test_strictness_silent_no_optimizer(caplog: pytest.LogCaptureFixture) -> None:
    """No optimizer installed -> strictness reads ``"off"`` -> ``_check_n1`` is a no-op.

    The root-shaped no-op: with no extension nothing arms the per-execution
    strictness ``ContextVar`` and nothing stashes ``DST_OPTIMIZER_STRICTNESS``,
    so ``types/resolvers.py::_strictness_for`` falls back to its ``"off"``
    default and the prelude returns before any probe - the per-parent pipeline
    runs byte-identically to a tree with no optimizer installed, no flag.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    # No-optimizer variant: the plain list schema installs no extension at all,
    # so nothing ever arms strictness (``strictness="raise"`` is inert here).
    caplog.set_level("WARNING", logger="django_strawberry_framework")
    schema = _genres_list_schema(optimizer=False, strictness="raise")
    result = _exec(schema, "{ objs { booksConnection(first: 2) { edges { node { title } } } } }")
    assert result.errors is None, result.errors
    assert result.data is not None
    titles = [
        json_at(e, "node", "title")
        for e in json_list(result.data, "objs", 0, "booksConnection", "edges")
    ]
    assert titles == ["apple", "banana"]

    assert not [r for r in caplog.records if "Potential N+1" in r.getMessage()]


@pytest.mark.django_db
def test_fast_path_count_less_window_serves_cheap_page() -> None:
    """A window planned WITHOUT the count still fast-paths the cheap page shape.

    ``edges`` + ``hasPreviousPage`` + cursors derive from ``_dst_row_number``
    alone, so the walker drops ``_dst_total_count`` (spec-033 Decision 4) and the
    relaxed row probe (``_window_rows_are_annotated``) still hands the rows to
    the fast path - fixed two-query cost, correct page, no per-parent
    fallback. The window SQL carries no count aggregate.
    """
    _seed_window_books(["a", "b", "c"])
    schema = _genres_list_schema(optimizer=True)
    query = (
        "{ objs { booksConnection(first: 2) { "
        "edges { cursor node { title } } pageInfo { hasPreviousPage startCursor } } } }"
    )

    with _capture_relations() as captured:
        result = _exec(schema, query)
    assert result.data is not None
    conn = json_at(result.data, "objs", 0, "booksConnection")
    assert [json_at(e, "node", "title") for e in json_list(conn, "edges")] == ["a", "b"]
    assert json_at(conn, "pageInfo", "hasPreviousPage") is False
    assert json_at(conn, "pageInfo", "startCursor") == json_at(conn, "edges", 0, "cursor")
    # The SQL-negative pin: the count window never compiled.
    window_sql = _table_selects(captured, "library_book")[0]
    assert "_dst_row_number" in window_sql
    assert "_dst_total_count" not in window_sql

    _assert_same_partitions(result.data)

    assert "COUNT(" not in window_sql.upper()


@pytest.mark.django_db
def test_reverse_fk_without_related_name_resolves_list_and_connection() -> None:
    """A reverse FK with NO ``related_name`` resolves on both relation surfaces.

    ``apps/library/models.py::RepairTicket.venue`` declares no
    ``related_name``, so Django's ``ForeignObjectRel.name`` on ``Venue`` is the
    related QUERY name (``"repairticket"``) while the instance attribute is
    ``get_accessor_name()`` (``"repairticket_set"``). Both the Phase-2 list
    resolver and the synthesized connection resolver reach rows through
    ``utils.relations.instance_accessor``, never ``getattr(root, field.name)``,
    which raises ``AttributeError``; the GraphQL field names stay
    query-name-derived (``repairticket`` / ``repairticketConnection``). This
    schema installs no optimizer, so the list half reads the relation manager
    here; the optimized list half is live in
    ``examples/fakeshop/test_query/test_library_inheritance_api.py``. The
    HTTP holder publishes both relation shapes over the real models.
    """
    rel = Venue._meta.get_field("repairticket")
    assert isinstance(rel, ForeignObjectRel)
    assert rel.get_accessor_name() == "repairticket_set"  # the split this test pins

    _make_type("RepairTicketNode", RepairTicket, ("id", "code"))
    venue_type = _make_type(
        "VenueNode",
        Venue,
        ("id", "name", "repairticket"),
        meta_extra={"relation_shapes": {"repairticket": "both"}},
    )
    schema = _schema_with_root(venue_type)

    venue = Venue.objects.create(name="a1")
    RepairTicket.objects.create(code="b1", venue=venue)

    result = _exec(
        schema,
        "{ objs { name repairticket { code } "
        "repairticketConnection { edges { node { code } } } } }",
    )
    assert result.errors is None
    assert result.data is not None
    assert result.data["objs"] == [
        {
            "name": "a1",
            "repairticket": [{"code": "b1"}],
            "repairticketConnection": {"edges": [{"node": {"code": "b1"}}]},
        },
    ]


@pytest.mark.django_db
def test_consumer_assigned_relation_subtree_n1_visible_under_strictness() -> None:
    """The N+1 under a consumer-owned relation FIRES under strictness ``"raise"``.

    The consumer-assigned relation (strawberry-django #697): the walker records
    no ``planned_resolver_keys`` for the consumer-owned relation's walked
    subtree, so the nested ``loans`` accesses on the consumer resolver's FRESH
    instances do not short-circuit ``_check_n1``. With the selection left fully
    unplanned, strictness sees the real per-book lazy loads - the consumer's
    documented recourse is an explicit ``OptimizerHint`` (the sibling test).
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    patron = Patron.objects.create(name="reader")
    for title in ("a", "b"):
        book = Book.objects.create(title=title, shelf=shelf)
        Loan.objects.create(book=book, patron=patron, note=f"loan-{title}")

    schema = _shelves_with_consumer_books_schema(strictness="raise")
    with CaptureQueriesContext(db_connection) as captured:
        result = _exec(
            schema,
            "{ objs { code books { title loans { note } } } }",
            expect_errors=True,
        )
    assert result.errors, "the unplanned subtree access must be strictness-visible"
    assert len(result.errors) == 1
    assert result.errors[0].get("message") == "Unplanned N+1: loans"
    assert result.errors[0].get("path") == [
        "objs",
        0,
        "books",
        0,
        "loans",
    ]
    assert result.data is None

    assert len(_table_selects(captured, "library_shelf")) == 1
    assert len(_table_selects(captured, "library_book")) == 1
    assert _table_selects(captured, "library_loan") == []


@pytest.mark.django_db
def test_consumer_assigned_relation_with_hint_is_planned_and_silent() -> None:
    """``OptimizerHint.prefetch_related()`` opts the delegating resolver back in.

    With the hint declared, the walker plans the relation per the hint and
    records the resolver keys, so strictness stays silent - the documented
    migration for consumers whose resolver delegates to the relation.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    patron = Patron.objects.create(name="reader")
    for title in ("a", "b"):
        book = Book.objects.create(title=title, shelf=shelf)
        Loan.objects.create(book=book, patron=patron, note=f"loan-{title}")

    schema = _shelves_with_consumer_books_schema(
        strictness="raise",
        books_hint=OptimizerHint.prefetch_related(),
    )
    with CaptureQueriesContext(db_connection) as captured:
        result = _exec(schema, "{ objs { code books { title loans { note } } } }")
    assert result.errors is None, result.errors
    assert result.data is not None
    assert result.data == {
        "objs": [
            {
                "code": "A1",
                "books": [
                    {"title": title, "loans": [{"note": f"loan-{title}"}]} for title in ("a", "b")
                ],
            },
        ],
    }

    assert len(_table_selects(captured, "library_shelf")) == 1
    assert len(_table_selects(captured, "library_book")) == 1
    assert len(_table_selects(captured, "library_loan")) == 1


@pytest.mark.django_db
def test_nested_fallback_preserves_a_sibling_fk_id_elision_over_http(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A planned forward-FK sibling still elides after a nested fallback publishes.

    The ``DST_OPTIMIZER_FK_ID_ELISIONS`` union must survive the nested
    fallback pipeline's own publish: a query selecting an elided forward-FK
    (``shelf { id }`` on each book) alongside a fallback nested connection
    resolves with no spurious strictness flag on the FK-id resolver and no extra
    per-row query for the elided FK.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    genre = Genre.objects.create(name="fiction")
    for title in ("apple", "banana"):
        book = Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)

    # ``BookType`` exposes its forward FK ``shelf`` (a ``{ id }``-only selection
    # elides it) and the M2M ``genres`` (the fallback nested connection target).
    declare_django_type(
        "ShelfType",
        {
            "Meta": type(
                "Meta",
                (),
                {"model": Shelf, "fields": ("id",), "interfaces": (relay.Node,)},
            ),
        },
    )

    class _GenreFilter(FilterSet):
        class Meta:
            model = Genre
            fields = {"name": ["exact"]}

    declare_django_type(
        "GenreType",
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": Genre,
                    "fields": ("id", "name"),
                    "interfaces": (relay.Node,),
                    "filterset_class": _GenreFilter,
                },
            ),
        },
    )
    book_type = _make_type(
        "BookType",
        Book,
        (
            "id",
            "title",
            "shelf",
            "genres",
        ),
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"objs": list[book_type]}, "objs": DjangoListField(book_type)},
        ),
    )
    optimizer = DjangoOptimizerExtension(strictness="warn")
    schema = DjangoSchema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    shelf_type = registry.get(Shelf)
    assert shelf_type is not None
    shelf_id = global_id_for(shelf_type, shelf.pk, schema=schema)
    with CaptureQueriesContext(db_connection) as captured, caplog.at_level("WARNING"):
        result = _exec(
            schema,
            '{ objs { genresConnection(filter: { name: { exact: "fiction" } }) '
            "{ edges { node { name } } } shelf { id } } }",
        )
    assert result.errors is None, result.errors
    assert result.data == {
        "objs": [
            {
                "genresConnection": {"edges": [{"node": {"name": "fiction"}}]},
                "shelf": {"id": shelf_id},
            }
            for _ in range(2)
        ],
    }
    assert (
        caplog.messages
        == [
            (
                "Potential N+1 on genres "
                "(not window-planned: selection carries filter/orderBy; resolving per-parent)"
            ),
        ]
        * 2
    )
    assert len(_table_selects(captured, "library_book")) == 1
    shelf_sql = _table_selects(captured, "library_shelf")
    genre_sql = _table_selects(captured, "library_genre")
    assert shelf_sql == []
    assert len(genre_sql) == 2, genre_sql
