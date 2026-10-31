"""Live ``/graphql/`` coverage for routed nested-fetch strategy selection.

Postgres-marked rows pin per-field ``OptimizerHint.strategy`` overrides over
HTTP: a windowed hint under a lateral extension default emits no
``CROSS JOIN LATERAL``, and a lateral hint under a windowed default emits one.
SQLite rows pin the auto fallback's window SQL, a per-field windowed hint
that wins over a refusing extension default (OVER cannot come from the
default), a ``.distinct()`` child that refuses the window, and an unhashable
custom-scalar variable that still shares one plan-cache identity across
requests.
"""

import logging
from collections.abc import Callable, Iterator
from functools import wraps
from typing import NewType, TypeAlias

import pytest
import strawberry
from apps.library.models import Book, Branch, Shelf
from apps.products import services
from apps.products.models import Category
from debug_toolbar.toolbar import debug_toolbar_urls
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, assert_graphql_success, middleware_without_debug_toolbar
from strategy_schemas import build_strategy_schema, make_django_type
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    OptimizerHint,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import _connection_type_cache
from django_strawberry_framework.optimizer import logger as optimizer_logger
from django_strawberry_framework.optimizer.nested_fetch import (
    NestedConnectionRequest,
    StrategySelection,
)
from django_strawberry_framework.optimizer.nested_planner import clear_index_advisory_dedup
from django_strawberry_framework.optimizer.plans import OptimizationPlan
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import TestClient
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.urls(__name__)

_current: dict[str, object | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    """Serve the probe schema installed by the current test's holder fixture."""
    schema = _current["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql/", _graphql_view), *debug_toolbar_urls()]


@pytest.fixture
def install_auto_strategy_schema(
    private_registry: None,
) -> Iterator[None]:
    """Install a minimal library graph whose nested queryset is lateral-capable."""
    del private_registry  # The dependency clears before holder declarations.
    registry.clear()
    make_django_type(
        "AutoBookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
    )
    shelf_type = make_django_type("AutoShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_type = strawberry.type(
        type(
            "AutoStrategyQuery",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    _current["schema"] = build_strategy_schema(
        query_type,
        "auto",
        schema_class=DjangoSchema,
    )
    yield
    _current["schema"] = None


@pytest.mark.django_db
@pytest.mark.usefixtures("install_auto_strategy_schema")
@pytest.mark.usefixtures("private_registry")
def test_auto_strategy_picks_the_vendor_body_and_pages_truthfully_over_http() -> None:
    """Auto runs LATERAL on Postgres, the windowed body elsewhere, with truthful page metadata."""
    branch = Branch.objects.create(name="Auto strategy", city="Boston")
    shelf = Shelf.objects.create(code="AUTO", topic="Routing", branch=branch)
    for title in ("a", "b", "c"):
        Book.objects.create(title=title, shelf=shelf)

    document = """
        query {
          shelves {
            code
            booksConnection(first: 2) {
              edges { node { title } }
              totalCount
              pageInfo { hasNextPage }
            }
          }
        }
        """
    with CaptureQueriesContext(connection) as captured:
        response = TestClient().query(document)

    assert response.data == {
        "shelves": [
            {
                "code": "AUTO",
                "booksConnection": {
                    "edges": [{"node": {"title": "a"}}, {"node": {"title": "b"}}],
                    "totalCount": 3,
                    "pageInfo": {"hasNextPage": True},
                },
            },
        ],
    }
    book_sql = [
        entry["sql"] for entry in captured.captured_queries if "library_book" in entry["sql"]
    ]
    windowed = [sql for sql in book_sql if "OVER (" in sql]
    assert len(windowed) == 1, book_sql
    if connection.vendor == "postgresql":
        assert "CROSS JOIN LATERAL" in windowed[0], book_sql
        assert "PARTITION BY" not in windowed[0], book_sql
    else:
        assert "PARTITION BY" in windowed[0], book_sql
        assert "LATERAL" not in windowed[0], book_sql


@pytest.fixture
def install_hashable_scalar_cache_schema(
    private_registry: None,
) -> Iterator[DjangoOptimizerExtension]:
    """Install a live schema whose custom scalar returns hostile hashable values."""
    del private_registry  # The dependency clears before holder declarations.
    registry.clear()

    class CacheCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class EqualityBomb:
        @override
        def __hash__(self) -> int:
            return 1

        @override
        def __eq__(self, _other: object) -> bool:
            raise RuntimeError("custom scalar equality must not run in cache lookup")

    def _serialize_bomb(_value: object) -> str:
        return "ok"

    def _parse_bomb(_value: object) -> EqualityBomb:
        return EqualityBomb()

    BombValue = NewType("BombValue", object)
    bomb_scalar = strawberry.scalar(
        name="BombValue",
        serialize=_serialize_bomb,
        parse_value=_parse_bomb,
    )

    @strawberry.type
    class Misc:
        @strawberry.field
        def logs(self, after: BombValue) -> list[str]:
            return [type(after).__name__]

    @strawberry.type
    class Query:
        objs: list[CacheCategoryType] = DjangoListField(CacheCategoryType)

        @strawberry.field
        def misc(self) -> Misc:
            return Misc()

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    _current["schema"] = DjangoSchema(
        query=Query,
        config=strawberry_config(extra_scalar_map={BombValue: bomb_scalar}),
        extensions=[lambda: optimizer],
    )
    yield optimizer
    _current["schema"] = None


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
def test_repeated_live_query_survives_hashable_custom_scalar_equality(
    install_hashable_scalar_cache_schema: DjangoOptimizerExtension,
) -> None:
    """A hostile custom scalar cannot abort a repeated optimizer cache lookup."""
    services.seed_data(1)
    query = """
        query Q($value: BombValue!) {
          objs { name }
          misc { logs(after: $value) }
        }
    """

    first = TestClient().query(query, variables={"value": "marker"})
    second = TestClient().query(query, variables={"value": "marker"})

    assert first.data is not None
    assert second.data is not None
    assert first.data["misc"]["logs"] == ["EqualityBomb"]
    assert second.data["misc"]["logs"] == ["EqualityBomb"]
    assert install_hashable_scalar_cache_schema.cache_info().misses == 2
    assert install_hashable_scalar_cache_schema.cache_info().hits == 0


@pytest.fixture
def install_unhashable_set_scalar_cache_schema(
    private_registry: None,
) -> Iterator[DjangoOptimizerExtension]:
    """Install a live schema whose custom scalar parser returns a ``set``."""
    del private_registry  # The dependency clears before holder declarations.
    registry.clear()

    class SetCacheCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    SetValue = NewType("SetValue", set[str])
    set_scalar = strawberry.scalar(
        name="SetValue",
        serialize=sorted,
        parse_value=set,
    )

    @strawberry.type
    class Misc:
        @strawberry.field
        def logs(self, after: SetValue) -> list[str]:
            return sorted(after)

    @strawberry.type
    class Query:
        objs: list[SetCacheCategoryType] = DjangoListField(SetCacheCategoryType)

        @strawberry.field
        def misc(self) -> Misc:
            return Misc()

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    _current["schema"] = DjangoSchema(
        query=Query,
        config=strawberry_config(extra_scalar_map={SetValue: set_scalar}),
        extensions=[lambda: optimizer],
    )
    yield optimizer
    _current["schema"] = None


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
def test_repeated_live_query_shares_plan_cache_for_unhashable_set_scalar(
    install_unhashable_set_scalar_cache_schema: DjangoOptimizerExtension,
) -> None:
    """A ``set``-valued custom scalar is frozen structurally, so two requests share one plan.

    The sibling ``EqualityBomb`` row is the opaque-identity miss; this is the
    must-not: a library-owned container freeze still hits the cache. Returning
    the raw set from the freezer would ``TypeError`` inside the plan-key
    ``frozenset``.
    """
    services.seed_data(1)
    query = """
        query Q($x: SetValue!) {
          objs { name }
          misc { logs(after: $x) }
        }
    """

    first = TestClient().query(query, variables={"x": ["b", "a"]})
    second = TestClient().query(query, variables={"x": ["a", "b"]})

    assert first.data is not None
    assert second.data is not None
    assert first.data["misc"]["logs"] == ["a", "b"]
    assert second.data["misc"]["logs"] == ["a", "b"]
    assert install_unhashable_set_scalar_cache_schema.cache_info().misses == 1
    assert install_unhashable_set_scalar_cache_schema.cache_info().hits == 1
    assert install_unhashable_set_scalar_cache_schema.cache_info().size == 1


_HINT_PAGE_DOCUMENT = """
query {
  shelves {
    code
    booksConnection(first: 2) {
      edges { node { title } }
    }
  }
}
"""

#: One shelf's nested ``booksConnection`` window: ``edges`` of ``{"node": {"title": ...}}``.
_HintPage: TypeAlias = dict[str, list[dict[str, dict[str, str]]]]

_HINT_PAGE_DATA: dict[str, list[dict[str, str | _HintPage]]] = {
    "shelves": [
        {
            "code": "A",
            "booksConnection": {
                "edges": [{"node": {"title": "a0"}}, {"node": {"title": "a1"}}],
            },
        },
        {
            "code": "B",
            "booksConnection": {
                "edges": [{"node": {"title": "b0"}}],
            },
        },
        {
            "code": "C",
            "booksConnection": {
                "edges": [],
            },
        },
    ],
}


def _seed_hint_shelf() -> None:
    """Three shelves with 5, 1 and 0 books.

    More than one parent keeps the nested page off the single-parent fetch
    (``django_strawberry_framework/optimizer/single_parent_fetch.py``), whose
    SQL carries neither a window nor a lateral join, and the uneven counts make
    ``first: 2`` a real bounded page on one parent only.
    """
    branch = Branch.objects.create(name="Hint strategy", city="Boston")
    shelf_a = Shelf.objects.create(code="A", topic="Strategy", branch=branch)
    shelf_b = Shelf.objects.create(code="B", topic="Strategy", branch=branch)
    Shelf.objects.create(code="C", topic="Strategy", branch=branch)
    for index in range(5):
        Book.objects.create(title=f"a{index}", shelf=shelf_a)
    Book.objects.create(title="b0", shelf=shelf_b)


def _book_sql(captured: CaptureQueriesContext) -> list[str]:
    """Captured statements that touch ``library_book`` (the nested child table)."""
    return [entry["sql"] for entry in captured.captured_queries if "library_book" in entry["sql"]]


@pytest.fixture
def install_hinted_strategy_schema(
    private_registry: None,
) -> Iterator[Callable[[StrategySelection, OptimizerHint], None]]:
    """Install a library graph whose ``booksConnection`` carries a strategy hint."""
    del private_registry  # The dependency clears before holder declarations.

    def _install(default_strategy: StrategySelection, books_hint: OptimizerHint) -> None:
        registry.clear()
        make_django_type(
            "HintBookType",
            Book,
            ("id", "title"),
            meta_extra={"connection": {"total_count": True}},
        )
        shelf_type = make_django_type(
            "HintShelfType",
            Shelf,
            ("id", "code", "books"),
            meta_extra={"optimizer_hints": {"books": books_hint}},
        )
        finalize_django_types()
        query_type = strawberry.type(
            type(
                "HintStrategyQuery",
                (),
                {
                    "__annotations__": {"shelves": list[shelf_type]},
                    "shelves": DjangoListField(shelf_type),
                },
            ),
        )
        _current["schema"] = build_strategy_schema(
            query_type,
            default_strategy,
            schema_class=DjangoSchema,
        )

    yield _install
    _current["schema"] = None


class _RefusingNestedStrategy:
    """Extension default that never accepts a nested connection plan.

    A windowed per-field hint must still emit ``OVER (``; if the hint is
    ignored, the refusing default leaves per-parent fallback SQL with no window.
    """

    name = "refusing"

    def plan(self, _request: NestedConnectionRequest, _plan: OptimizationPlan) -> bool:
        return False


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
def test_per_field_strategy_hint_windowed_emits_over_when_the_default_refuses(
    install_hinted_strategy_schema: Callable[[StrategySelection, OptimizerHint], None],
) -> None:
    """``OptimizerHint.strategy("windowed")`` plans ``ROW_NUMBER() OVER`` on SQLite.

    Postgres HTTP rows pin the same branch against LATERAL; this row is the
    SQLite pin and the must-not (a refusing extension default cannot be the
    source of the window).
    """
    _seed_hint_shelf()
    install_hinted_strategy_schema(_RefusingNestedStrategy(), OptimizerHint.strategy("windowed"))

    with CaptureQueriesContext(connection) as captured:
        response = TestClient().query(_HINT_PAGE_DOCUMENT)

    assert response.data == _HINT_PAGE_DATA
    book_sql = _book_sql(captured)
    assert any("OVER (" in sql and "PARTITION BY" in sql for sql in book_sql), book_sql
    windowed = [sql for sql in book_sql if "OVER (" in sql]
    assert len(windowed) == 1, book_sql


@pytest.mark.django_db
@pytest.mark.pg
@pytest.mark.usefixtures("private_registry")
def test_per_field_strategy_hint_windowed_under_lateral_default_skips_lateral_over_http(
    install_hinted_strategy_schema: Callable[[StrategySelection, OptimizerHint], None],
) -> None:
    """``OptimizerHint.strategy("windowed")`` wins over a lateral extension default."""
    _seed_hint_shelf()
    install_hinted_strategy_schema("lateral", OptimizerHint.strategy("windowed"))

    with CaptureQueriesContext(connection) as captured:
        response = TestClient().query(_HINT_PAGE_DOCUMENT)

    assert response.data == _HINT_PAGE_DATA
    book_sql = _book_sql(captured)
    assert book_sql, captured.captured_queries
    assert any("OVER (" in sql and "PARTITION BY" in sql for sql in book_sql), book_sql
    assert all("LATERAL" not in sql for sql in book_sql), book_sql


@pytest.mark.django_db
@pytest.mark.pg
@pytest.mark.usefixtures("private_registry")
def test_per_field_strategy_hint_lateral_under_windowed_default_emits_lateral_over_http(
    install_hinted_strategy_schema: Callable[[StrategySelection, OptimizerHint], None],
) -> None:
    """``OptimizerHint.strategy("lateral")`` wins over a windowed extension default."""
    _seed_hint_shelf()
    install_hinted_strategy_schema("windowed", OptimizerHint.strategy("lateral"))

    with CaptureQueriesContext(connection) as captured:
        response = TestClient().query(_HINT_PAGE_DOCUMENT)

    assert response.data == _HINT_PAGE_DATA
    book_sql = _book_sql(captured)
    assert book_sql, captured.captured_queries
    assert any("CROSS JOIN LATERAL" in sql for sql in book_sql), book_sql
    assert any("LATERAL" in sql for sql in book_sql), book_sql


@pytest.fixture
def install_distinct_child_schema(
    private_registry: None,
) -> Iterator[None]:
    """Install a library graph whose nested book queryset is ``.distinct()``."""
    del private_registry  # The dependency clears before holder declarations.

    def _distinct(
        _cls: type[DjangoType],
        queryset: QuerySet[Book],
        _info: strawberry.Info[object, object],
        **_kwargs: object,
    ) -> QuerySet[Book]:
        return queryset.distinct()

    registry.clear()
    make_django_type(
        "DistinctBookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
        namespace_extra={"get_queryset": classmethod(_distinct)},
    )
    shelf_type = make_django_type("DistinctShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_type = strawberry.type(
        type(
            "DistinctChildQuery",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    _current["schema"] = build_strategy_schema(
        query_type,
        "windowed",
        schema_class=DjangoSchema,
    )
    yield
    _current["schema"] = None


@pytest.mark.django_db
@pytest.mark.usefixtures("install_distinct_child_schema")
@pytest.mark.usefixtures("private_registry")
def test_distinct_child_queryset_never_windows_over_http() -> None:
    """A target ``get_queryset`` returning ``.distinct()`` leaves the nested page unplanned.

    The nested planner refuses the whole relation (spec-033 Decision 6), so each parent
    pays its own child query and no ``ROW_NUMBER() OVER`` window is emitted.
    """
    _seed_hint_shelf()

    with CaptureQueriesContext(connection) as captured:
        response = TestClient().query(_HINT_PAGE_DOCUMENT)

    assert response.data == _HINT_PAGE_DATA
    book_sql = _book_sql(captured)
    assert book_sql, captured.captured_queries
    assert not any("OVER (" in sql for sql in book_sql), book_sql
    assert len(book_sql) > 1, book_sql


@pytest.mark.django_db
@pytest.mark.usefixtures("private_registry")
class TestAdvisoryDeferredUntilWindowAccepted:
    """Only a strategy that accepts the window emits its composite-index advisory."""

    _QUERY = "{ shelves { code booksConnection(first: 2) { edges { node { title } } } } }"

    class _RefuseEveryWindow:
        name = "refuse-all"

        def plan(self, _request: NestedConnectionRequest, _plan: OptimizationPlan) -> bool:
            return False

    @staticmethod
    def _warnings(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
        return [
            record
            for record in caplog.records
            if record.levelname == "WARNING" and record.name == optimizer_logger.name
        ]

    @staticmethod
    def _reset_type_caches() -> None:
        registry.clear()
        _connection_type_cache.clear()
        clear_index_advisory_dedup()

    @pytest.fixture(autouse=True)
    def _isolate_registry(self) -> Iterator[None]:
        """Each strategy gets its own registrations and empty advisory dedup state."""
        self._reset_type_caches()
        yield
        self._reset_type_caches()

    @staticmethod
    def _shelf_books_schema(strategy: StrategySelection) -> DjangoSchema:
        """A library holder whose public strategy decides whether its window is accepted."""

        class BookNode(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title")
                interfaces = (relay.Node,)

        assert registry.get(Book) is BookNode

        class ShelfNode(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "code", "books")
                interfaces = (relay.Node,)

        @strawberry.type
        class Query:
            shelves: list[ShelfNode] = DjangoListField(ShelfNode)

        finalize_django_types()
        extension = DjangoOptimizerExtension(nested_connection_strategy=strategy)
        return DjangoSchema(
            query=Query,
            config=strawberry_config(),
            extensions=[lambda: extension],
        )

    def _post(self, strategy: StrategySelection) -> JSONObject:
        _current["schema"] = self._shelf_books_schema(strategy)
        try:
            return assert_graphql_success(self._QUERY)
        finally:
            _current["schema"] = None

    @override_settings(DEBUG=True, MIDDLEWARE=middleware_without_debug_toolbar())
    def test_refusing_strategy_emits_no_advisory_but_windowed_does(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A refusing strategy advises no index; the accepting control advises its actual window."""
        shelf = Shelf.objects.create(code="A", branch=Branch.objects.create(name="c"))
        for index in range(3):
            Book.objects.create(title=f"t{index}", shelf=shelf)
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        expected = {
            "shelves": [
                {
                    "code": "A",
                    "booksConnection": {
                        "edges": [{"node": {"title": "t0"}}, {"node": {"title": "t1"}}],
                    },
                },
            ],
        }

        self._reset_type_caches()
        assert self._post(self._RefuseEveryWindow()) == expected
        assert not self._warnings(caplog)

        caplog.clear()
        self._reset_type_caches()
        assert self._post("windowed") == expected
        (warning,) = self._warnings(caplog)
        assert "composite index" in warning.getMessage()
