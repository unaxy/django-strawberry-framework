"""Live PostgreSQL HTTP tests for lateral strategy parity, paging, visibility and custom joins."""

import re
from functools import wraps
from typing import NamedTuple

import pytest
import strawberry
from apps.library.models import Book, Branch, Genre, Issue, Loan, Patron, Periodical, Shelf
from apps.products.services import create_users
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection as db_connection
from django.db import models
from django.db.models import F, Model, QuerySet
from django.db.models.expressions import Combinable
from django.http import HttpRequest, HttpResponseBase
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject
from strategy_schemas import build_strategy_schema, make_django_type
from strawberry.relay.utils import to_base64
from strawberry.test.client import Response
from typing_extensions import override

from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.optimizer.nested_fetch import StrategySelection
from django_strawberry_framework.testing import TestClient
from django_strawberry_framework.utils._narrowing import (
    read_attr,
)
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import (
    is_object_dict,
    is_object_list,
    json_at,
    json_list,
    saved_pk,
)
from tests._lateral_data import _seed_periodicals

pytestmark = [pytest.mark.pg, pytest.mark.django_db, pytest.mark.usefixtures("private_registry")]
_CURRENT: dict[str, strawberry.Schema | None] = {"schema": None}


def _build_strategy_schema(
    query_cls: type[object],
    strategy: StrategySelection,
) -> strawberry.Schema:
    """Use the benchmark's strategy seam with the complete consumer schema boundary."""
    return build_strategy_schema(query_cls, strategy, schema_class=DjangoSchema)


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-lateral/", _graphql_view)]


def _post(schema: strawberry.Schema, query: str, *, client: Client | None = None) -> Response:
    """Execute the operation through the real package view and request middleware."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            result = TestClient(client=client).query(
                query,
                assert_no_errors=False,
                url="/graphql-lateral/",
            )
        assert result.response.status_code == 200
        return result
    finally:
        _CURRENT["schema"] = None


def _application_selects(captured: CaptureQueriesContext) -> list[dict[str, str]]:
    """Keep only statements reading the library tables, including raw lateral reads."""
    tables = {
        db_connection.ops.quote_name(model._meta.db_table)
        for model in apps.get_app_config("library").get_models(include_auto_created=True)
    }
    return [
        entry for entry in captured if any(f"FROM {table}" in entry["sql"] for table in tables)
    ]


def _connections_by_code(data: object) -> dict[object, object]:
    """Each root shelf's ``booksConnection`` payload, keyed by the shelf's ``code``."""
    return {
        json_at(shelf, "code"): json_at(shelf, "booksConnection")
        for shelf in json_list(data, "shelves")
    }


def _count(value: object, *path: str) -> int:
    """The integer count ``json_at(value, *path)`` reaches, failing on any other kind."""
    found = json_at(value, *path)
    assert type(found) is int, found
    return found


def _make_type(
    name: str,
    model: type[Model],
    fields: tuple[str, ...],
    *,
    total_count: bool = False,
) -> type[DjangoType]:
    """Declare a Relay-Node ``DjangoType``; the shared core owns the boilerplate."""
    return make_django_type(
        name,
        model,
        fields,
        meta_extra={"connection": {"total_count": True}} if total_count else None,
    )


def _library_schemas() -> tuple[strawberry.Schema, strawberry.Schema]:
    """One finalized type graph, two schemas: windowed vs lateral extension.

    ``shelves`` roots the reverse-FK direction (``Shelf.books``), ``genres``
    the reverse-M2M direction (``Genre.books``); ``BookType`` carries the
    forward M2M (``genresConnection``) and the depth-2 reverse FK
    (``loansConnection``). Every connection target opts into ``totalCount``.
    """
    _make_type("LoanType", Loan, ("id", "note"), total_count=True)
    _make_type(
        "BookType",
        Book,
        (
            "id",
            "title",
            "loans",
            "genres",
        ),
        total_count=True,
    )
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"), total_count=True)
    shelf_type = _make_type("ShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type], "genres": list[genre_type]},
                "shelves": DjangoListField(shelf_type),
                "genres": DjangoListField(genre_type),
            },
        ),
    )

    # The strategy-mounting seam is the shared ``strategy_schemas`` builder -
    # the SAME construction the nested-fetch benchmark compares.
    return (
        _build_strategy_schema(query_cls, "windowed"),
        _build_strategy_schema(query_cls, "lateral"),
    )


def _seed_library() -> None:
    """Overlap-shaped data: uneven fan-outs, shared genres, a childless parent.

    Shelf A holds five books, shelf B one, shelf C none (the empty-window
    disambiguation case). Every book carries two of three genres (the M2M
    through-table overlap that would expose duplicate-join row inflation),
    and the first two books carry loans for the depth-2 shape.
    """
    branch = Branch.objects.create(name="central")
    shelf_a = Shelf.objects.create(code="A", branch=branch)
    shelf_b = Shelf.objects.create(code="B", branch=branch)
    Shelf.objects.create(code="C", branch=branch)
    genres = [Genre.objects.create(name=f"g{index}") for index in range(3)]
    books: list[Book] = []
    for index in range(5):
        book = Book.objects.create(title=f"a{index}", shelf=shelf_a)
        book.genres.add(genres[index % 3], genres[(index + 1) % 3])
        books.append(book)
    lone = Book.objects.create(title="b0", shelf=shelf_b)
    lone.genres.add(genres[0], genres[2])
    patrons = [Patron.objects.create(name=f"p{index}") for index in range(2)]
    Loan.objects.create(book=books[0], patron=patrons[0], note="n0")
    Loan.objects.create(book=books[0], patron=patrons[1], note="n1")
    Loan.objects.create(book=books[1], patron=patrons[0], note="n2")


def _canonical(data: dict[str, object] | None) -> dict[str, list[object]]:
    """Sort every root parent list by ``id`` (the roots are unordered)."""
    assert data is not None
    canonical: dict[str, list[object]] = {}
    for root, parents in data.items():
        assert is_object_list(parents)
        rows = [parent for parent in parents if is_object_dict(parent)]
        assert len(rows) == len(parents)
        # Any total order serves: both sides of a parity check are sorted the same way.
        ordered = sorted(rows, key=lambda row: str(row["id"]))
        canonical[root] = [*ordered]
    return canonical


def _assert_parity(
    query: str,
    *,
    queries: int = 2,
    expect_lateral: bool = True,
    count_free: bool = False,
    schemas: tuple[strawberry.Schema, strawberry.Schema] | None = None,
) -> tuple[JSONObject | None, list[dict[str, str]]]:
    """Execute under both strategies; pin identical data and the lateral cost.

    Returns ``(data, captured)`` - the (parity-asserted) response data plus
    the lateral run's ``CaptureQueriesContext`` - so tests that layer extra
    SQL-shape asserts (the through-once tripwire) reuse this preamble instead
    of re-spelling the capture/compare. ``schemas`` is a ``_library_schemas()``
    pair for a test that compares several queries over ONE finalized type
    graph; a second ``_library_schemas()`` call would redeclare its types after
    finalization.
    """
    windowed_schema, lateral_schema = schemas if schemas is not None else _library_schemas()
    if _MID_CURSOR in query:
        prior = _post(
            windowed_schema,
            "{ shelves { code booksConnection(first: 1) { pageInfo { endCursor } } } }",
        )
        assert prior.errors is None, prior.errors
        (shelf_a,) = [
            row for row in json_list(prior.data, "shelves") if json_at(row, "code") == "A"
        ]
        continuation = json_at(shelf_a, "booksConnection", "pageInfo", "endCursor")
        assert isinstance(continuation, str)
        query = query.replace(_MID_CURSOR, continuation)
    windowed = _post(windowed_schema, query)
    assert windowed.errors is None, windowed.errors
    with CaptureQueriesContext(db_connection) as captured:
        lateral = _post(lateral_schema, query)
    assert lateral.errors is None, lateral.errors
    assert _canonical(lateral.data) == _canonical(windowed.data)
    statements = _application_selects(captured)
    assert len(statements) == queries, statements
    executed_sql = " ".join(entry["sql"] for entry in captured)
    if expect_lateral:
        assert "CROSS JOIN LATERAL" in executed_sql
    else:
        # ``expect_lateral=False`` means the shape must NOT have paid a
        # lateral (or any window) query before falling back - absence is
        # asserted, not merely unchecked.
        assert "CROSS JOIN LATERAL" not in executed_sql
    if count_free:
        assert "_dst_total_count" not in executed_sql
    return windowed.data, statements


_CHEAP_PAGE = "edges { cursor node { title } } pageInfo { hasPreviousPage startCursor }"


_FULL_PAGE = (
    "edges { cursor node { title } } totalCount "
    "pageInfo { hasPreviousPage hasNextPage startCursor endCursor }"
)


_NEXT_PAGE_PROBE = "edges { cursor node { title } } pageInfo { hasNextPage }"


_MID_CURSOR = "__prior_end_cursor__"


_OVERSHOOT_CURSOR = to_base64("arrayconnection", "49")


@pytest.mark.parametrize(
    ("arguments", "page", "count_free"),
    [
        pytest.param("(first: 2)", _CHEAP_PAGE, True, id="first-2-count-free"),
        pytest.param("(first: 2)", _FULL_PAGE, False, id="first-2-full"),
        pytest.param("(first: 0)", _FULL_PAGE, False, id="first-0-marker"),
        pytest.param(
            f'(first: 2, after: "{_MID_CURSOR}")',
            _FULL_PAGE,
            False,
            id="after-mid",
        ),
        pytest.param(
            f'(first: 2, after: "{_OVERSHOOT_CURSOR}")',
            _FULL_PAGE,
            False,
            id="after-overshoot",
        ),
        pytest.param("(last: 2)", _FULL_PAGE, False, id="last-2"),
        pytest.param("", _FULL_PAGE, False, id="unbounded"),
    ],
)
def test_reverse_fk_parity_across_pagination_shapes(
    arguments: str,
    page: str,
    *,
    count_free: bool,
) -> None:
    """Every reverse-FK pagination shape: identical data, two queries, real lateral."""
    _seed_library()
    data, _ = _assert_parity(
        f"{{ shelves {{ id booksConnection{arguments} {{ {page} }} }} }}",
        count_free=count_free,
    )
    assert data is not None
    assert len(json_list(data, "shelves")) == 3  # including the childless shelf C.


@pytest.mark.parametrize(
    "arguments",
    [
        # Bounded offset page: the composed probe + marker (A1 lateral half - the
        # ``fetch_upper_bound`` rn-filter bind, invisible on the SQLite tier).
        pytest.param(f'(first: 2, after: "{_MID_CURSOR}")', id="offset-probe"),
        # Offset overshoot: marker-only, hasNextPage False, no per-parent fallback.
        pytest.param(f'(first: 2, after: "{_OVERSHOOT_CURSOR}")', id="offset-overshoot"),
        # Unbounded forward: constant-False hasNextPage (A2).
        pytest.param("", id="unbounded-constant-false"),
        # Reversed last:N: constant-False hasNextPage (A2).
        pytest.param("(last: 2)", id="reverse-constant-false"),
    ],
)
def test_count_free_has_next_page_parity_across_shapes(arguments: str) -> None:
    """Count-free ``hasNextPage`` shapes page byte-identically with NO count.

    The A1 composed offset probe (bounded offset page) and the A2 constant-False
    shapes (unbounded forward, reversed ``last: N``, offset overshoot) all resolve
    ``hasNextPage`` without a ``COUNT(1) OVER`` window under BOTH strategies. The
    lateral half of the offset probe depends on the ``fetch_upper_bound``
    rn-filter bind (a raw ``upper_bound`` would read ``hasNextPage`` constantly
    False on PG only). Byte parity + count-free + fixed two-query cost (no
    per-parent fallback, asserted via the real lateral join) is the bar.
    """
    _seed_library()
    query = f"{{ shelves {{ id code booksConnection{arguments} {{ {_NEXT_PAGE_PROBE} }} }} }}"
    _assert_parity(query, count_free=True)


def test_next_page_probe_parity_is_count_free() -> None:
    """``first: N`` + ``hasNextPage`` (no ``totalCount``): the count-free n+1 probe.

    Both strategies serve identical data - ``hasNextPage`` included - with NO
    ``_dst_total_count`` / ``COUNT`` window in the executed SQL: the plain first
    page overfetches one sentinel row instead of scanning the partition to
    count. The exact ``LIMIT page + 1`` builder shape is pinned on SQLite
    (``test_sql_next_page_probe_overfetches_one_row_in_branch``); here the bar is
    that a live Postgres server pages byte-identically without a count - for a
    populated parent AND the childless shelf C (the empty-window branch).
    """
    _seed_library()
    query = f"{{ shelves {{ id code booksConnection(first: 2) {{ {_NEXT_PAGE_PROBE} }} }} }}"
    data, captured = _assert_parity(query, count_free=True)
    assert "COUNT(" not in captured[1]["sql"].upper()
    assert data is not None
    assert len(json_list(data, "shelves")) == 3  # including the childless shelf C.
    by_code = {
        json_at(shelf, "code"): json_at(shelf, "booksConnection")
        for shelf in json_list(data, "shelves")
    }
    # Shelf C (no books) resolves as an EMPTY page - empty edges + no next page -
    # not a missing sentinel; shelf A (5 books) reports a next page from the probe.
    assert json_at(by_code, "C", "edges") == []
    assert json_at(by_code, "C", "pageInfo", "hasNextPage") is False
    assert json_at(by_code, "A", "pageInfo", "hasNextPage") is True


def test_next_page_probe_parity_childless_no_edges_shape() -> None:
    """The count-free probe on the no-``edges`` shape, populated and childless parents.

    The Relay invariant (``hasNextPage`` resolves without ``edges`` selected) on
    the lateral probe path: a separate test (not a second ``_assert_parity`` call
    in the sibling above) because each ``_assert_parity`` re-declares the shared
    ``DjangoType`` graph, and the registry isolation is per-test. Both strategies
    agree byte-for-byte and stay count-free; shelf C (no books) reports no next
    page, shelf A (5 books) reports one - the empty window distinguished from a
    short page with no ``edges`` in play.
    """
    _seed_library()
    # ``id`` rides along for ``_assert_parity``'s ``_canonical`` root sort,
    # not the shape under test (the no-``edges`` invariant is on the nested
    # connection's selection, which stays ``pageInfo``-only).
    query = "{ shelves { id code booksConnection(first: 2) { pageInfo { hasNextPage } } } }"
    data, _ = _assert_parity(query, count_free=True)
    assert data is not None
    flags = {
        json_at(shelf, "code"): json_at(shelf, "booksConnection", "pageInfo", "hasNextPage")
        for shelf in json_list(data, "shelves")
    }
    assert flags["C"] is False
    assert flags["A"] is True


def test_reverse_m2m_parity_joins_the_through_table_once() -> None:
    """Reverse M2M over overlapping genre membership: parity plus a single through-table join.

    The lateral SQL carries exactly one through-table join (the duplicate-join tripwire).
    """
    _seed_library()
    query = f"{{ genres {{ id booksConnection(first: 2) {{ {_FULL_PAGE} }} }} }}"
    data, captured = _assert_parity(query)
    lateral_sql = captured[1]["sql"]
    # The duplicate-join tripwire, lateral edition: each lateral branch scans
    # the through table exactly once (as FROM, joining the child) - a second
    # join would inflate the row numbers with duplicated M2M rows.
    assert (
        'FROM "library_book_genres" AS "__dst_through"'
        ' INNER JOIN "library_book" AS "__dst_child"' in lateral_sql
    )
    assert lateral_sql.count("INNER JOIN") == 1
    assert lateral_sql.count('FROM "library_book_genres"') == 1
    # Overlap sanity: every genre relates to four books (5 two-genre shelf-A
    # books + the two-genre loner distribute evenly); each page shows 2 of 4.
    assert data is not None
    by_name = {json_at(genre, "id"): genre for genre in json_list(data, "genres")}
    counts = sorted(_count(genre, "booksConnection", "totalCount") for genre in by_name.values())
    assert counts == [4, 4, 4]


def test_depth_two_lateral_under_lateral_parity() -> None:
    """Nested connections two levels deep: one lateral query per level."""
    _seed_library()
    query = (
        "{ shelves { id booksConnection(first: 2) { edges { node { title "
        "loansConnection(first: 1) { edges { node { note } } totalCount } "
        "} } } } }"
    )
    _assert_parity(query, queries=3)


def test_depth_two_forward_m2m_parity() -> None:
    """Forward M2M as the inner level (``genresConnection`` under books)."""
    _seed_library()
    query = (
        "{ shelves { id booksConnection(first: 2) { edges { node { title "
        "genresConnection(first: 2) { edges { node { name } } totalCount } "
        "} } } } }"
    )
    _assert_parity(query, queries=3)


def test_divergent_alias_parity_one_lateral_per_response_key() -> None:
    """Divergent aliases ride the lateral backend too: one lateral query per key.

    The per-response-key scheme is strategy-independent - the walker
    hands one ``NestedConnectionRequest`` per key, so the lateral strategy
    plans one ``CROSS JOIN LATERAL`` query per alias (3 queries total: roots +
    2 laterals) with byte parity against the windowed strategy. Neither alias
    observes ``totalCount``, so BOTH per-key windows engage the count-free n+1
    probe - the executed SQL carries no count aggregate.
    """
    _seed_library()
    query = (
        "{ shelves { id code "
        f"a: booksConnection(first: 2) {{ {_NEXT_PAGE_PROBE} }} "
        f"b: booksConnection(first: 9) {{ {_NEXT_PAGE_PROBE} }} "
        "} }"
    )
    data, captured = _assert_parity(query, queries=3, count_free=True)
    executed_sql = " ".join(entry["sql"] for entry in captured)
    assert "COUNT(" not in executed_sql.upper()
    assert data is not None
    by_code = {json_at(shelf, "code"): shelf for shelf in json_list(data, "shelves")}
    # Shelf A (5 books): each alias serves ITS OWN page bound and probe flag.
    assert len(json_list(by_code, "A", "a", "edges")) == 2
    assert json_at(by_code, "A", "a", "pageInfo", "hasNextPage") is True
    assert len(json_list(by_code, "A", "b", "edges")) == 5
    assert json_at(by_code, "A", "b", "pageInfo", "hasNextPage") is False
    # Childless shelf C: an empty page for BOTH per-key windows.
    assert json_at(by_code, "C", "a", "edges") == []
    assert json_at(by_code, "C", "b", "pageInfo", "hasNextPage") is False


def test_divergent_alias_total_count_sibling_keeps_count_on_both_laterals() -> None:
    """A ``totalCount`` alias keeps the count on EVERY divergent lateral window.

    The union-conservative observer rule under the lateral backend: ``b``
    observing ``totalCount`` retains the count on ``a``'s window too (no probe
    on either), and each alias still pages by its own bound with full parity.
    """
    _seed_library()
    query = (
        "{ shelves { id code "
        f"a: booksConnection(first: 2) {{ {_NEXT_PAGE_PROBE} }} "
        f"b: booksConnection(first: 9) {{ {_FULL_PAGE} }} "
        "} }"
    )
    data, captured = _assert_parity(query, queries=3)
    # EACH lateral window query carries the count annotation (union rule, per
    # window) - asserted per captured query, not on the concatenated SQL,
    # because one counted lateral alone emits the token twice (inner alias +
    # outer select) and would satisfy a global count even if the sibling
    # window regressed to the probe.
    window_sqls = [entry["sql"] for entry in captured if "CROSS JOIN LATERAL" in entry["sql"]]
    assert len(window_sqls) == 2
    for window_sql in window_sqls:
        assert "_dst_total_count" in window_sql
    assert data is not None
    by_code = {json_at(shelf, "code"): shelf for shelf in json_list(data, "shelves")}
    assert json_at(by_code, "A", "a", "pageInfo", "hasNextPage") is True
    assert json_at(by_code, "A", "b", "totalCount") == 5


def test_last_zero_serves_the_first_zero_page_under_both_strategies() -> None:
    """``last: 0`` is the planned ``first: 0`` lateral page: parity, two queries, same payload."""
    _seed_library()
    schemas = _library_schemas()
    last_zero, _ = _assert_parity(
        f"{{ shelves {{ id booksConnection(last: 0) {{ {_FULL_PAGE} }} }} }}",
        schemas=schemas,
    )
    first_zero, _ = _assert_parity(
        f"{{ shelves {{ id booksConnection(first: 0) {{ {_FULL_PAGE} }} }} }}",
        schemas=schemas,
    )
    assert _canonical(last_zero) == _canonical(first_zero)


def _visibility_schemas() -> tuple[strawberry.Schema, strawberry.Schema]:
    """A ``ShelfType.booksConnection`` whose child type hides repair books.

    The anonymous-traffic substrate: ``get_queryset`` applies a single-table
    plain-column ``exclude`` (the ``BookType`` visibility shape), which rides
    the lateral branch as a spliced WHERE rather than forcing the windowed
    body. The scope is unconditional so both strategies filter identically.
    """

    @classmethod
    def _hide_repair(
        _cls: type[DjangoType],
        queryset: QuerySet[Book],
        _info: object,
    ) -> QuerySet[Book]:
        return queryset.exclude(circulation_status="repair")

    make_django_type(
        "VisibilityBookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
        namespace_extra={"get_queryset": _hide_repair},
    )
    shelf_type = make_django_type("VisibilityShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    return (
        _build_strategy_schema(query_cls, "windowed"),
        _build_strategy_schema(query_cls, "lateral"),
    )


def _seed_visibility() -> None:
    """Shelf A: four visible books + two hidden ``repair`` books; shelf B empty."""
    branch = Branch.objects.create(name="central")
    shelf_a = Shelf.objects.create(code="A", branch=branch)
    Shelf.objects.create(code="B", branch=branch)
    for index in range(4):
        Book.objects.create(
            title=f"a{index}",
            shelf=shelf_a,
            circulation_status=Book.CirculationStatus.AVAILABLE,
        )
    for index in range(2):
        Book.objects.create(
            title=f"r{index}",
            shelf=shelf_a,
            circulation_status=Book.CirculationStatus.REPAIR,
        )


def test_visibility_scope_takes_the_lateral_path_with_parity() -> None:
    """A single-table ``get_queryset`` scope takes the lateral path.

    Anonymous traffic over a visibility-scoped connection
    executes ``CROSS JOIN LATERAL`` (not the windowed downgrade), the scope's
    column rides into the lateral SQL, and the response is byte-identical to the
    windowed strategy - the hidden ``repair`` books excluded under both.
    """
    _seed_visibility()
    windowed_schema, lateral_schema = _visibility_schemas()
    query = (
        "{ shelves { id code booksConnection(first: 2) "
        "{ edges { node { title } } totalCount pageInfo { hasNextPage } } } }"
    )
    windowed = _post(windowed_schema, query)
    assert windowed.errors is None, windowed.errors
    with CaptureQueriesContext(db_connection) as captured:
        lateral = _post(lateral_schema, query)
    assert lateral.errors is None, lateral.errors
    assert _canonical(lateral.data) == _canonical(windowed.data)
    executed_sql = " ".join(entry["sql"] for entry in captured)
    assert "CROSS JOIN LATERAL" in executed_sql
    assert "circulation_status" in executed_sql  # the scope rode into the branch.
    assert lateral.data is not None
    by_code = _connections_by_code(lateral.data)
    # Anonymous sees only the four available books on shelf A (two repair hidden).
    assert json_at(by_code, "A", "totalCount") == 4
    assert json_at(by_code, "A", "pageInfo", "hasNextPage") is True


def test_visibility_scope_lateral_applies_the_filter_exactly_once() -> None:
    """The scope predicate is spliced ONCE - no double-apply, correct rows.

    A double-apply would be invisible on this idempotent ``exclude``, so the pin
    is structural: the ``circulation_status`` predicate appears exactly once in
    the executed lateral SQL, and only the four visible books surface.
    """
    _seed_visibility()
    _windowed_schema, lateral_schema = _visibility_schemas()
    query = "{ shelves { id code booksConnection(first: 10) { edges { node { title } } totalCount } } }"
    with CaptureQueriesContext(db_connection) as captured:
        result = _post(lateral_schema, query)
    assert result.errors is None, result.errors
    lateral_sql = next(entry["sql"] for entry in captured if "CROSS JOIN LATERAL" in entry["sql"])
    assert lateral_sql.count("circulation_status") == 1
    assert result.data is not None
    by_code = _connections_by_code(result.data)
    titles = [json_at(edge, "node", "title") for edge in json_list(by_code, "A", "edges")]
    assert titles == [
        "a0",
        "a1",
        "a2",
        "a3",
    ]  # repair books excluded, in order.
    assert json_at(by_code, "A", "totalCount") == 4


def test_multi_table_visibility_scope_downgrades_off_the_lateral_path() -> None:
    """A join-traversal ``get_queryset`` scope is refused - the windowed body runs.

    The refusal boundary at the live tier: a scope filtering through a relation
    (``branch__city``) uses more than the child table, so the spec refuses it
    and the connection serves through the windowed strategy (no lateral SQL) -
    still byte-identical to the standalone windowed run.
    """
    _seed_visibility()

    @classmethod
    def _hide_by_branch(
        _cls: type[DjangoType],
        queryset: QuerySet[Book],
        _info: object,
    ) -> QuerySet[Book]:
        return queryset.exclude(shelf__branch__city="restricted")

    make_django_type(
        "MultiTableBookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
        namespace_extra={"get_queryset": _hide_by_branch},
    )
    shelf_type = make_django_type("MultiTableShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    lateral_schema = _build_strategy_schema(query_cls, "lateral")
    query = (
        "{ shelves { id code booksConnection(first: 2) { edges { node { title } } totalCount } } }"
    )
    with CaptureQueriesContext(db_connection) as captured:
        result = _post(lateral_schema, query)
    assert result.errors is None, result.errors
    executed_sql = " ".join(entry["sql"] for entry in captured)
    assert "CROSS JOIN LATERAL" not in executed_sql  # multi-table scope refused.
    assert result.data is not None
    by_code = _connections_by_code(result.data)
    assert json_at(by_code, "A", "totalCount") == 6  # no city is restricted, so all six show.


def _request_varying_visibility_schema() -> tuple[
    strawberry.Schema,
    DjangoOptimizerExtension,
]:
    """A ``ShelfType.booksConnection`` whose child scope VARIES by request.

    Mirrors the real fakeshop permission idiom (``BookType.get_queryset`` hides
    ``circulation_status="repair"`` from non-staff): an anonymous request gets the
    restrictive predicate, a staff request gets the queryset unchanged. Returns
    ONE lateral schema bound to a SINGLE persistent extension instance
    (``extensions=[lambda: extension]``) so its plan-cache counters report BOTH
    requests rather than resetting per execution.
    """

    @classmethod
    def _scope_by_staff(
        _cls: type[DjangoType],
        queryset: QuerySet[Book],
        info: object,
    ) -> QuerySet[Book]:
        # The real idiom: unwrap info.context -> request -> user -> is_staff.
        context = read_attr(info, "context", None)
        request = read_attr(context, "request", None) or context
        user = read_attr(request, "user", None)
        if user is not None and read_attr(user, "is_staff", False):
            return queryset
        return queryset.exclude(circulation_status="repair")

    make_django_type(
        "ReqVaryBookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
        namespace_extra={"get_queryset": _scope_by_staff},
    )
    shelf_type = make_django_type("ReqVaryShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    extension = DjangoOptimizerExtension(nested_connection_strategy="lateral")
    schema = DjangoSchema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: extension],
    )
    return schema, extension


def test_request_varying_visibility_is_not_cached_across_callers() -> None:
    """Two callers of ONE extension get their OWN visibility WHERE, never a replay.

    A custom ``get_queryset`` marks this request-varying plan non-cacheable, so the anonymous
    caller's restrictive predicate must never survive in the plan cache and be
    replayed for a staff caller (or the reverse). Both callers execute real
    lateral SQL through the SAME extension instance; the anonymous branch carries
    the ``circulation_status`` scope and the staff branch does not; their visible
    rows differ; and the extension's plan-cache counters prove the request-varying
    plan was never cached or reused.
    """
    create_users(1)
    _seed_visibility()  # shelf A: 4 available + 2 repair; shelf B empty.
    schema, extension = _request_varying_visibility_schema()
    query = (
        "{ shelves { id code booksConnection(first: 10) "
        "{ edges { node { title } } totalCount } } }"
    )

    staff_client = Client()
    staff_client.force_login(get_user_model().objects.get(username="staff_1"))

    with CaptureQueriesContext(db_connection) as anon_captured:
        anon = _post(schema, query)
    assert anon.errors is None, anon.errors
    with CaptureQueriesContext(db_connection) as staff_captured:
        staff = _post(schema, query, client=staff_client)
    assert staff.errors is None, staff.errors

    assert anon.data is not None
    anon_books = _connections_by_code(anon.data)
    assert staff.data is not None
    staff_books = _connections_by_code(staff.data)
    # The two callers see DIFFERENT rows - each request's scope was applied, not
    # replayed from a cached first-caller plan.
    assert json_at(anon_books, "A", "totalCount") == 4  # repair hidden from anonymous.
    assert json_at(staff_books, "A", "totalCount") == 6  # staff sees all six.
    staff_titles = {
        json_at(edge, "node", "title") for edge in json_list(staff_books, "A", "edges")
    }
    anon_titles = {json_at(edge, "node", "title") for edge in json_list(anon_books, "A", "edges")}
    assert staff_titles - anon_titles == {"r0", "r1"}  # the two repair books.

    anon_sql = " ".join(entry["sql"] for entry in anon_captured)
    staff_sql = " ".join(entry["sql"] for entry in staff_captured)
    # Both take the lateral path; only the anonymous branch splices the scope.
    assert "CROSS JOIN LATERAL" in anon_sql
    assert "CROSS JOIN LATERAL" in staff_sql
    assert "circulation_status" in anon_sql
    assert "circulation_status" not in staff_sql

    # The plan is request-scoped (custom get_queryset -> non-cacheable): it never
    # enters the cross-request cache, so no caller can be served another's plan.
    info = extension.cache_info()
    assert info.hits == 0
    assert info.size == 0
    assert info.misses >= 2


def _keyset_schemas(
    cursor_field: tuple[str, ...] = ("-number", "id"),
) -> tuple[strawberry.Schema, strawberry.Schema]:
    """Periodical -> issuesConnection graph with a KEYSET child type.

    ``cursor_field`` parameterizes the seek arm: the mixed-direction default
    exercises the redundant-bound OR-expansion; a uniform ``("number", "id")``
    exercises the native row-value comparison.
    """
    make_django_type(
        "KeysetIssueType",
        Issue,
        ("id", "number", "title"),
        meta_extra={"cursor_field": cursor_field, "connection": {"total_count": True}},
    )
    periodical_type = make_django_type(
        "KeysetPeriodicalType",
        Periodical,
        ("id", "name", "issues"),
        meta_extra={"relation_shapes": {"issues": "connection"}},
    )

    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"periodicals": list[periodical_type]},
                "periodicals": DjangoListField(periodical_type),
            },
        ),
    )

    finalize_django_types()
    return (
        _build_strategy_schema(query_cls, "windowed"),
        _build_strategy_schema(query_cls, "lateral"),
    )


def _mint_issue_cursor(
    issue: object,
    cursor_field: tuple[str, ...] = ("-number", "id"),
) -> tuple[str, tuple[strawberry.Schema, strawberry.Schema]]:
    """Mint the continuation from the actual first-page HTTP edge for this issue."""
    schemas = _keyset_schemas(cursor_field)
    page = _post(
        schemas[0],
        "{ periodicals { issuesConnection(first: 5) { edges { cursor node { title } } } } }",
    )
    assert page.errors is None, page.errors
    cursors = [
        json_at(edge, "cursor")
        for parent in json_list(page.data, "periodicals")
        for edge in json_list(parent, "issuesConnection", "edges")
        if json_at(edge, "node", "title") == read_attr(issue, "title")
    ]
    (cursor,) = cursors
    assert isinstance(cursor, str)
    return cursor, schemas


def _assert_keyset_parity(
    query: str,
    *,
    cursor_field: tuple[str, ...] = ("-number", "id"),
    expect_lateral: bool = True,
    schemas: tuple[strawberry.Schema, strawberry.Schema] | None = None,
) -> tuple[JSONObject | None, list[dict[str, str]]]:
    """The keyset twin of ``_assert_parity`` (its own type graph per call)."""
    windowed_schema, lateral_schema = (
        schemas if schemas is not None else _keyset_schemas(cursor_field)
    )
    windowed = _post(windowed_schema, query)
    assert windowed.errors is None, windowed.errors
    with CaptureQueriesContext(db_connection) as captured:
        lateral = _post(lateral_schema, query)
    assert lateral.errors is None, lateral.errors
    assert _canonical(lateral.data) == _canonical(windowed.data)
    statements = _application_selects(captured)
    assert len(statements) == 2, statements
    executed_sql = " ".join(entry["sql"] for entry in captured)
    if expect_lateral:
        assert "CROSS JOIN LATERAL" in executed_sql
    else:
        assert "CROSS JOIN LATERAL" not in executed_sql
    return lateral.data, statements


_KEYSET_PROBE_PAGE = "edges { cursor node { title } } pageInfo { hasNextPage hasPreviousPage }"


_KEYSET_FULL_PAGE = (
    "edges { cursor node { title } } totalCount pageInfo { hasNextPage hasPreviousPage endCursor }"
)


def test_keyset_count_free_seek_runs_in_branch_on_postgres() -> None:
    """The O(page) headline: the seek + ORDER BY + LIMIT inside the lateral branch."""
    issues = _seed_periodicals()
    cursor, schemas = _mint_issue_cursor(issues[3])  # p4 under (-number, id)
    data, captured = _assert_keyset_parity(
        f'{{ periodicals {{ id issuesConnection(first: 2, after: "{cursor}") '
        f"{{ {_KEYSET_PROBE_PAGE} }} }} }}",
        schemas=schemas,
    )
    lateral_sql = next(sql for sql in (e["sql"] for e in captured) if "LATERAL" in sql)
    # The seek predicate landed INSIDE the branch (count-free shape), with the
    # in-branch LIMIT - not an outer row-number filter.
    assert "_dst_total_count" not in lateral_sql
    assert "LIMIT" in lateral_sql
    assert data is not None
    by_name = {
        json_at(parent, "id"): json_at(parent, "issuesConnection")
        for parent in json_list(data, "periodicals")
    }
    pages = {
        tuple(json_at(edge, "node", "title") for edge in json_list(connection_data, "edges"))
        for connection_data in by_name.values()
    }
    # populated continues past p4; sparse re-positions by VALUE (numbers < 4).
    assert ("p3", "p2") in pages
    assert ("s3", "s2") in pages
    assert () in pages  # the childless periodical


def test_keyset_uniform_direction_uses_row_value_seek() -> None:
    """Uniform directions emit the native row-value comparison on Postgres."""
    issues = _seed_periodicals()
    cursor, schemas = _mint_issue_cursor(issues[1], ("number", "id"))
    _data, captured = _assert_keyset_parity(
        f'{{ periodicals {{ id issuesConnection(first: 2, after: "{cursor}") '
        f"{{ {_KEYSET_PROBE_PAGE} }} }} }}",
        schemas=schemas,
        cursor_field=("number", "id"),
    )
    lateral_sql = next(sql for sql in (e["sql"] for e in captured) if "LATERAL" in sql)
    assert ") > (" in lateral_sql  # the row-value tuple comparison


def test_keyset_counted_seek_downgrades_to_windowed_with_pre_seek_totals() -> None:
    """A ``totalCount`` + ``after`` selection: the lateral strategy runs the qualify-wrapped window."""
    issues = _seed_periodicals()
    cursor, schemas = _mint_issue_cursor(issues[3])
    data, captured = _assert_keyset_parity(
        f'{{ periodicals {{ id issuesConnection(first: 2, after: "{cursor}") '
        f"{{ {_KEYSET_FULL_PAGE} }} }} }}",
        schemas=schemas,
        expect_lateral=False,
    )
    executed_sql = " ".join(entry["sql"] for entry in captured)
    assert "FILTER (WHERE" in executed_sql  # the page-relative filtered count
    assert data is not None
    totals = {
        json_at(parent, "issuesConnection", "totalCount")
        for parent in json_list(data, "periodicals")
    }
    assert totals == {5, 3, 0}  # PRE-seek partition counts


def test_keyset_first_page_full_shape_parity() -> None:
    """The cursor-less keyset page has identical full payloads under both SQL strategies."""
    _seed_periodicals()
    _assert_keyset_parity(
        f"{{ periodicals {{ id issuesConnection(first: 2) {{ {_KEYSET_FULL_PAGE} }} }} }}",
    )


class _HookShape(NamedTuple):
    """One parent -> child relation a hook-ordered nested connection pages."""

    child: type[Model]
    parent: type[Model]
    relation: str
    #: The child field each edge selects: the row's rank in pk order (1, 2, 3).
    label: str
    #: The child table's quoted name inside the lateral branch.
    alias: str


_HOOK_SHAPES = {
    "fk": _HookShape(Issue, Periodical, "issues", "number", '"library_issue"'),
    "m2m": _HookShape(Book, Genre, "books", "subtitle", '"__dst_child"'),
}


def _hook_ordered_schemas(
    shape: _HookShape,
    hook_order: tuple[str | Combinable, ...] | None,
    *,
    reverse: bool,
    keyset: bool,
) -> tuple[strawberry.Schema, strawberry.Schema]:
    """A parent type whose child connection's ``get_queryset`` orders (and may reverse) it.

    ``hook_order`` ``None`` leaves the hook unordered, so ``reverse`` flips the
    fallback order. The keyset child declares ``cursor_field = ("id",)``, so the
    hook's order, not the declared one, is what its window pages, seeks and
    mints by; the offset child declares none.
    """

    @classmethod
    def _ordered(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        _info: object,
    ) -> QuerySet[Model]:
        ordered = queryset if hook_order is None else queryset.order_by(*hook_order)
        return ordered.reverse() if reverse else ordered

    meta_extra: dict[str, object] = {"connection": {"total_count": True}}
    if keyset:
        meta_extra["cursor_field"] = ("id",)
    make_django_type(
        "HookOrderedChildType",
        shape.child,
        ("id", shape.label, "title"),
        meta_extra=meta_extra,
        namespace_extra={"get_queryset": _ordered},
    )
    parent_type = make_django_type(
        "HookOrderedParentType",
        shape.parent,
        ("id", "name", shape.relation),
        meta_extra={"relation_shapes": {shape.relation: "connection"}},
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"parents": list[parent_type]},
                "parents": DjangoListField(parent_type),
            },
        ),
    )
    return (
        _build_strategy_schema(query_cls, "windowed"),
        _build_strategy_schema(query_cls, "lateral"),
    )


def _seed_hook_ordered_rows(shape: _HookShape) -> None:
    """Parent ``A``: children ranked 1, 2, 3 in pk order, titled ``y``, ``x``, ``x``; ``B``: one.

    The tied titles make the hook's ``title`` order lean on the pk tiebreaker;
    ``B`` is a second partition in the same window query.
    """
    rows = [
        ("A", 1, "y"),
        ("A", 2, "x"),
        ("A", 3, "x"),
        ("B", 1, "a"),
    ]
    if shape.child is Issue:
        periodicals = {name: Periodical.objects.create(name=name) for name in ("A", "B")}
        for name, rank, title in rows:
            Issue.objects.create(periodical=periodicals[name], number=rank, title=title)
        return
    genres = {name: Genre.objects.create(name=name) for name in ("A", "B")}
    branch = Branch.objects.create(name="central")
    for name, rank, title in rows:
        # One shelf per book: a shelf holds one book per title.
        shelf = Shelf.objects.create(code=f"{name}{rank}", branch=branch)
        book = Book.objects.create(title=title, subtitle=str(rank), shelf=shelf)
        book.genres.add(genres[name])


def _hook_page(shape: _HookShape, arguments: str) -> str:
    return (
        f"{{ parents {{ id name {shape.relation}Connection({arguments}) {{ "
        f"pageInfo {{ hasNextPage endCursor }} edges {{ cursor node {{ {shape.label} }} }} }} }} }}"
    )


def _connection_of_a(data: JSONObject | None, shape: _HookShape) -> object:
    """Parent ``A``'s connection payload."""
    assert data is not None
    (parent,) = (row for row in json_list(data, "parents") if json_at(row, "name") == "A")
    return json_at(parent, f"{shape.relation}Connection")


def _window_order(captured: list[dict[str, str]]) -> str:
    """The lateral branch's ``ROW_NUMBER()`` order with its table names dropped (``title ASC``)."""
    lateral_sql = next(sql for sql in (e["sql"] for e in captured) if "LATERAL" in sql)
    window = lateral_sql.split("ROW_NUMBER() OVER (ORDER BY ", 1)[1].split(")", 1)[0]
    return re.sub(r'"[^"]+"\."([^"]+)"', r"\1", window)


def _uniform_seek(shape: _HookShape, window_order: str) -> str:
    """The keyset seek a uniform-direction ``window_order`` compiles to in the branch.

    One column compares itself; several compare as a native row value. ``>``
    follows an ascending order, ``<`` a descending one.
    """
    terms = [term.split() for term in window_order.split(", ")]
    columns = ", ".join(f'{shape.alias}."{column}"' for column, _ in terms)
    operator = ">" if terms[0][1] == "ASC" else "<"
    return f"({columns}) {operator} (" if len(terms) > 1 else f"{columns} {operator} "


@pytest.mark.parametrize("shape", list(_HOOK_SHAPES))
@pytest.mark.parametrize("keyset", [True, False], ids=["keyset", "offset"])
@pytest.mark.parametrize(
    (
        "hook_order",
        "reverse",
        "window_order",
        "pages",
    ),
    [
        pytest.param(("title",), False, "title ASC, id ASC", (["2", "3"], ["1"]), id="title"),
        pytest.param(
            ("title",),
            True,
            "title DESC, id DESC",
            (["1", "3"], ["2"]),
            id="title-reversed",
        ),
        pytest.param(("-id",), False, "id DESC", (["3", "2"], ["1"]), id="-id"),
        pytest.param(("-id",), True, "id ASC", (["1", "2"], ["3"]), id="-id-reversed"),
        pytest.param(None, True, "id DESC", (["3", "2"], ["1"]), id="unordered-reversed"),
        pytest.param(
            (F("title").asc(),),
            False,
            "title ASC, id ASC",
            (["2", "3"], ["1"]),
            id="title-expression",
        ),
    ],
)
def test_hook_ordered_window_pages_in_branch_with_parity(
    *,
    shape: str,
    keyset: bool,
    hook_order: tuple[str | Combinable, ...] | None,
    reverse: bool,
    window_order: str,
    pages: tuple[list[str], list[str]],
) -> None:
    """A child ``get_queryset`` order, forward or ``.reverse()``d, is what the lateral window pages by.

    Page 1 (``first: 2``) and page 2 (after page 1's ``endCursor``) each run
    real ``CROSS JOIN LATERAL`` SQL whose data and cursors equal the windowed
    body's, and number rows under the order Django compiles for the hook. A
    keyset page 2 seeks inside the branch by that order's own columns in its
    own direction; an offset page 2 carries no seek. ``A``'s three rows are
    served once each across the two pages. The order may be names or the
    ``asc()`` expression Django compiles onto the same column.
    """
    hook_shape = _HOOK_SHAPES[shape]
    _seed_hook_ordered_rows(hook_shape)
    schemas = _hook_ordered_schemas(hook_shape, hook_order, reverse=reverse, keyset=keyset)
    first, first_captured = _assert_parity(_hook_page(hook_shape, "first: 2"), schemas=schemas)
    cursor = json_at(_connection_of_a(first, hook_shape), "pageInfo", "endCursor")
    assert isinstance(cursor, str)
    second, second_captured = _assert_parity(
        _hook_page(hook_shape, f'first: 2, after: "{cursor}"'),
        schemas=schemas,
    )
    labels = tuple(
        [
            str(json_at(edge, "node", hook_shape.label))
            for edge in json_list(_connection_of_a(data, hook_shape), "edges")
        ]
        for data in (first, second)
    )
    assert labels == pages
    assert _window_order(first_captured) == _window_order(second_captured) == window_order
    second_sql = " ".join(entry["sql"] for entry in second_captured)
    assert (_uniform_seek(hook_shape, window_order) in second_sql) is keyset


def _deferring_schemas() -> tuple[strawberry.Schema, strawberry.Schema]:
    """A ``ShelfType.booksConnection`` whose child type's ``get_queryset`` defers ``subtitle``.

    The query never selects ``subtitle``, so the plan keeps the hook's deferral
    (``plans.py::apply_projection``) and the child queryset reaches the
    strategy ``defer()``-shaped.
    """

    @classmethod
    def _defer_subtitle(
        _cls: type[DjangoType],
        queryset: QuerySet[Book],
        _info: object,
    ) -> QuerySet[Book]:
        return queryset.defer("subtitle")

    make_django_type(
        "DeferringBookType",
        Book,
        ("id", "title", "subtitle"),
        meta_extra={"connection": {"total_count": True}},
        namespace_extra={"get_queryset": _defer_subtitle},
    )
    shelf_type = make_django_type("DeferringShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    return (
        _build_strategy_schema(query_cls, "windowed"),
        _build_strategy_schema(query_cls, "lateral"),
    )


def test_deferring_child_hook_takes_the_lateral_path_with_parity() -> None:
    """A ``defer()``-shaped child runs ``CROSS JOIN LATERAL`` with the windowed body's data.

    The lateral branch selects the columns Django selects for the deferral
    (``lateral_fetch.py::_select_columns``), so the deferred ``subtitle``
    column never reaches the lateral SQL.
    """
    _seed_library()
    _data, captured = _assert_parity(
        f"{{ shelves {{ id booksConnection(first: 2) {{ {_FULL_PAGE} }} }} }}",
        schemas=_deferring_schemas(),
    )
    lateral_sql = next(entry["sql"] for entry in captured if "CROSS JOIN LATERAL" in entry["sql"])
    assert "subtitle" not in lateral_sql


@pytest.mark.django_db(transaction=True)
def test_lateral_custom_through_joins_the_foreign_key_target_column() -> None:
    """A public custom-through connection joins the child target column and pages its rows."""

    class NaturalChild(models.Model):
        code: "models.TextField[str | Combinable, str]" = models.TextField(unique=True)
        rank: "models.IntegerField[float | int | str | Combinable, int]" = models.IntegerField()

        class Meta:
            app_label = "library"
            managed = False
            db_table = "lateral_natural_child"

        @override
        def __str__(self) -> str:
            return self.code

    class NaturalParent(models.Model):
        name: "models.TextField[str | Combinable, str]" = models.TextField()
        children: "models.ManyToManyField[NaturalChild, NaturalMembership]" = (
            models.ManyToManyField(
                NaturalChild,
                through="NaturalMembership",
                related_name="natural_parents",
            )
        )

        class Meta:
            app_label = "library"
            managed = False
            db_table = "lateral_natural_parent"

        @override
        def __str__(self) -> str:
            return self.name

    class NaturalMembership(models.Model):
        parent: "models.ForeignKey[NaturalParent | Combinable, NaturalParent]" = models.ForeignKey(
            NaturalParent,
            on_delete=models.CASCADE,
        )
        child: "models.ForeignKey[NaturalChild | Combinable, NaturalChild]" = models.ForeignKey(
            NaturalChild,
            db_column="child_code",
            on_delete=models.CASCADE,
            to_field="code",
        )

        class Meta:
            app_label = "library"
            managed = False
            db_table = "lateral_natural_membership"

        @override
        def __str__(self) -> str:
            return str(saved_pk(self))

    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(NaturalChild)
        schema_editor.create_model(NaturalParent)
        schema_editor.create_model(NaturalMembership)
    try:
        parent = NaturalParent.objects.create(name="parent")
        children = [
            NaturalChild.objects.create(code=f"code-{rank}", rank=rank) for rank in range(3)
        ]
        NaturalMembership.objects.bulk_create(
            [NaturalMembership(parent=parent, child=child) for child in children],
        )
        NaturalParent.objects.create(name="empty")
        make_django_type("NaturalChildNode", NaturalChild, ("id", "code", "rank"))
        parent_type = make_django_type(
            "NaturalParentNode",
            NaturalParent,
            ("id", "name", "children"),
            meta_extra={"relation_shapes": {"children": "connection"}},
        )
        finalize_django_types()
        query_cls = strawberry.type(
            type(
                "Query",
                (),
                {
                    "__annotations__": {"parents": list[parent_type]},
                    "parents": DjangoListField(parent_type),
                },
            ),
        )
        schema = _build_strategy_schema(query_cls, "lateral")
        with CaptureQueriesContext(db_connection) as captured:
            result = _post(
                schema,
                "{ parents { name childrenConnection(first: 2) { "
                "edges { node { code } } pageInfo { hasNextPage } } } }",
            )
        assert result.errors is None, result.errors
        assert result.data is not None
        assert {
            json_at(row, "name"): json_at(row, "childrenConnection")
            for row in json_list(result.data, "parents")
        } == {
            "parent": {
                "edges": [{"node": {"code": "code-0"}}, {"node": {"code": "code-1"}}],
                "pageInfo": {"hasNextPage": True},
            },
            "empty": {"edges": [], "pageInfo": {"hasNextPage": False}},
        }
        lateral_sqls = [
            entry["sql"]
            for entry in _application_selects(captured)
            if "CROSS JOIN LATERAL" in entry["sql"]
        ]
        assert len(lateral_sqls) == 1, lateral_sqls
        assert '"__dst_child"."code" = "__dst_through"."child_code"' in lateral_sqls[0]
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(NaturalMembership)
            schema_editor.delete_model(NaturalParent)
            schema_editor.delete_model(NaturalChild)


def test_single_parent_fast_path_pages_identically_to_lateral() -> None:
    """The windowed single-parent fast path pages byte-identically to lateral.

    With exactly one seeded shelf the Django-prefetch-injected parent ``IN`` list
    has length one, so under the windowed strategy
    ``WindowedPrefetchStrategy.plan``'s runtime wrap swaps in the plain filtered
    ``LIMIT`` fast path (``optimizer/single_parent_fetch.py``) instead of the
    ``ROW_NUMBER() OVER (PARTITION BY fk)`` body. That fast-path run must return
    rows / cursors / ``pageInfo`` byte-identical to the lateral strategy's output
    for the same count-free page - the same parity bar every shape here holds.

    Under ``strategy=lateral`` the fast path never engages (the wrap is
    windowed-branch-only), so the lateral half executes real ``CROSS JOIN
    LATERAL`` SQL and stands as the parity oracle.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A", branch=branch)
    for index in range(5):
        Book.objects.create(title=f"a{index}", shelf=shelf)
    data, _ = _assert_parity(
        f"{{ shelves {{ id booksConnection(first: 2) {{ {_CHEAP_PAGE} }} }} }}",
        count_free=True,
    )
    # The single seeded parent is what drives the len==1 IN list the fast path
    # keys on; shelf A carries five books so ``first: 2`` is a real bounded page.
    assert data is not None
    assert len(json_list(data, "shelves")) == 1
