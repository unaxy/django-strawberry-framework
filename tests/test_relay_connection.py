"""Relation-connection construction, registry lifecycle and private window-state tests.

HTTP paging, strategy parity, query cost and consumer relation hints live in
examples/fakeshop/test_query/test_relation_connections_api.py. This module keeps
construction-time refusals, teardown identity, manually planted window records,
private fallback callbacks and original exception types that wire JSON cannot show.
"""

import copy
import inspect
from types import SimpleNamespace, new_class
from typing import cast, get_args

import pytest
import strawberry
from apps.library.models import Book, Branch, Genre, Loan, Shelf
from apps.products.models import Category, Item, Property
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import connection as db_connection
from django.db import models as djmodels
from django.db.models.manager import Manager
from django.http import HttpRequest
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from strategy_schemas import make_django_type
from strawberry import relay
from strawberry.relay.utils import from_base64, to_base64
from strawberry.types import ExecutionResult
from strawberry.types.field import StrawberryField
from strawberry.utils.await_maybe import AwaitableOrValue

from django_strawberry_framework import (
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import (
    DjangoConnection,
    _build_windowed_fallback,
    _connection_type_for,
    _consume_window,
    _resolve_from_window,
    _WindowedConnectionRows,
)
from django_strawberry_framework.exceptions import ConfigurationError, OptimizerError
from django_strawberry_framework.filters import FilterSet, filter_input_type
from django_strawberry_framework.optimizer._context import (
    DST_OPTIMIZER_STRICTNESS,
    begin_execution_frame,
    end_execution_frame,
    publish_planned_windows,
)
from django_strawberry_framework.optimizer.plans import (
    WINDOW_ROW_NUMBER,
    PlannedWindow,
    resolver_key,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.finalizer import (
    _register_relation_connection_teardown,
    _synthesize_relation_connections,
)
from django_strawberry_framework.types.relay import apply_interfaces
from django_strawberry_framework.types.resolvers import _check_n1
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.utils.connections import (
    ConnectionWindowBounds,
    PaginationArgumentError,
    UnwindowableConnection,
)
from django_strawberry_framework.utils.typing import graphql_fields, graphql_type_of
from tests._definition import make_definition
from tests._idioms import json_at, json_list
from tests._info import make_info
from tests._relation_connection_schemas import (
    _genres_filterable_book_schema,
    _genres_list_schema,
    _schema_with_root,
    _seed_library_books,
)


def _as_django_type(cls: type[object]) -> type[DjangoType]:
    """Hand a plain class whose ``__annotations__`` dict the test controls to a teardown seam."""
    # basedpyright: a class carrying no definition whose ``__annotations__`` dict identity is the
    # input under test (a declared DjangoType owns its own); the teardown seam types the
    # parameter as type[DjangoType]
    return cls  # pyright: ignore[reportReturnType]


def _window_rows(*row_numbers: int) -> list[djmodels.Model]:
    """Real ``Book`` rows carrying only the window row-number annotation, as Django sets it."""
    rows: list[djmodels.Model] = []
    for row_number in row_numbers:
        row = Book()
        vars(row)["_dst_row_number"] = row_number
        rows.append(row)
    return rows


def _synthesized_field() -> StrawberryField:
    """A resolver-backed Strawberry field, as connection synthesis plants one."""
    return strawberry.field(lambda: None)


def _path(*keys: str | int) -> object:
    """Build a graphql-core-style linked response path (integer keys are list indexes)."""
    path = None
    for key in keys:
        path = type("Path", (), {"key": key, "prev": path})()
    return path


pytestmark = pytest.mark.usefixtures("isolate_global_registry")


# The shared declaration core (``examples/fakeshop/strategy_schemas.py``)
# matches the signature this module calls ``_make_type`` with exactly.
_make_type = make_django_type


# =============================================================================
# Default "connection" on M2M: fakeshop ships ``"both"`` for genres/books
# =============================================================================


# =============================================================================
# Explicit shapes: "list" narrowing (``"connection"`` is live on PeriodicalType)
# =============================================================================


# =============================================================================
# Non-Node targets: explicit fail-loud (silent list-only is live on BookType.loans)
# =============================================================================


@pytest.mark.parametrize("shape", ["connection", "both"])
def test_non_node_target_explicit_raises(shape: str) -> None:
    """An explicit ``"connection"`` / ``"both"`` over a non-Node target raises at finalize.

    Construction-time ``ConfigurationError``: the silent list-only default is
    pinned live at
    ``examples/fakeshop/test_query/test_library_api.py::test_book_loans_relation_stays_list_only``.
    """
    _make_type("LoanType", Loan, ("id", "note"), node=False)
    _make_type(
        "BookType",
        Book,
        ("id", "title", "loans"),
        meta_extra={"relation_shapes": {"loans": shape}},
    )

    with pytest.raises(ConfigurationError) as excinfo:
        finalize_django_types()
    message = str(excinfo.value)
    assert "BookType.Meta.relation_shapes['loans']" in message
    assert "LoanType is not Relay-Node-shaped" in message


# =============================================================================
# Consumer overrides and name collisions
# =============================================================================


def test_generated_name_collision_raises() -> None:
    """A consumer attribute named ``<field>_connection`` raises with the opt-out."""
    _make_type("ItemType", Item, ("id", "name", "category"))
    _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        namespace_extra={"__annotations__": {"items_connection": str}},
    )

    with pytest.raises(ConfigurationError) as excinfo:
        finalize_django_types()
    message = str(excinfo.value)
    assert "'items_connection'" in message
    assert 'relation_shapes = {"items": "list"}' in message


@pytest.mark.parametrize("auto_camel_case", [True, False])
def test_generated_name_graphql_collision_is_the_schema_converters(
    *,
    auto_camel_case: bool,
) -> None:
    """A consumer ``itemsConnection`` beside the generated ``items_connection`` is the schema's call.

    The two are distinct Python names, so finalization attaches the connection;
    the default converter names both ``itemsConnection`` and that schema's build
    refuses the pair, naming both, while ``auto_camel_case=False`` publishes both.
    """
    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        namespace_extra={"__annotations__": {"itemsConnection": str}},
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type("Query", (), {"__annotations__": {"node": category_type | None}, "node": None}),
    )
    config = strawberry_config(auto_camel_case=auto_camel_case)

    if not auto_camel_case:
        sdl = str(DjangoSchema(query=query_cls, config=config))
        assert "itemsConnection: String!" in sdl
        assert "items_connection(" in sdl
        return
    with pytest.raises(ConfigurationError) as excinfo:
        _ = DjangoSchema(query=query_cls, config=config)
    assert str(excinfo.value).startswith(
        "CategoryType: fields 'itemsConnection' and 'items_connection' both publish the "
        "GraphQL field name 'itemsConnection'",
    )


# =============================================================================
# Partial-finalize re-entrancy
# =============================================================================


def test_synthesis_skips_already_attached_on_refinalize() -> None:
    """A rerun after a post-synthesis finalize failure skips the attached sibling.

    The re-entrancy marker path: the first ``finalize_django_types()`` attaches
    ``itemsConnection``, then raises in ``_bind_filtersets`` (an orphan
    ``filter_input_type`` reference, which runs AFTER the synthesis step).
    Wiring the orphan and re-finalizing must succeed - the rerun recognizes
    its own prior attachment via the marker instead of misreading it as a
    collision - and the SDL carries exactly one ``itemsConnection``.
    """

    class _PropertyFilter(FilterSet):
        class Meta:
            model = Property
            fields = {"name": ["exact"]}

    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type("CategoryType", Category, ("id", "name", "items"))
    filter_input_type(_PropertyFilter)  # Orphan: referenced but not wired.

    with pytest.raises(ConfigurationError, match="filter_input_type"):
        finalize_django_types()

    # Wire the orphan, then re-finalize through the schema builder.
    _make_type(
        "PropertyType",
        Property,
        ("id", "name"),
        node=False,
        meta_extra={"filterset_class": _PropertyFilter},
    )
    sdl = str(_schema_with_root(category_type))
    assert sdl.count("itemsConnection(") == 1


def test_connection_only_relation_stays_list_suppressed_on_refinalize() -> None:
    """A ``"connection"`` relation survives a partial-finalize rerun list-suppressed.

    The first ``finalize_django_types()`` synthesizes ``itemsConnection`` and
    removes the generated ``items`` list form, then raises in
    ``_bind_filtersets`` (an orphan ``filter_input_type``, which runs AFTER
    synthesis). On the rerun, Phase 2 must NOT reattach an unannotated ``items``
    resolver (it would otherwise survive: synthesis sees its own marker and
    skips before re-removing). The final SDL carries ``itemsConnection`` and no
    ``items`` field.
    """

    class _PropertyFilter(FilterSet):
        class Meta:
            model = Property
            fields = {"name": ["exact"]}

    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        meta_extra={"relation_shapes": {"items": "connection"}},
    )
    filter_input_type(_PropertyFilter)  # Orphan: referenced but not wired.

    with pytest.raises(ConfigurationError, match="filter_input_type"):
        finalize_django_types()

    # Wire the orphan, then re-finalize through the schema builder.
    _make_type(
        "PropertyType",
        Property,
        ("id", "name"),
        node=False,
        meta_extra={"filterset_class": _PropertyFilter},
    )
    sdl = str(_schema_with_root(category_type))
    assert sdl.count("itemsConnection(") == 1
    assert "items: [" not in sdl


# =============================================================================
# Target-driven sidecar arguments + totalCount; visibility; pagination
# =============================================================================


def test_registry_clear_preserves_replacement_for_synthesized_connection() -> None:
    """Identity-safe teardown leaves a later same-named consumer value untouched."""
    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type("CategoryType", Category, ("id", "name", "items"))
    finalize_django_types()

    replacement = object()
    # The consumer rebinds the synthesized attribute after finalization; the class declares
    # no such attribute, so the write and the read go through the class itself.
    type.__setattr__(category_type, "items_connection", replacement)
    registry.clear()

    assert vars(category_type)["items_connection"] is replacement


def test_relation_connection_teardown_restores_owned_annotations_in_place() -> None:
    """Teardown preserves the annotation-dict identity held by consumer tooling."""
    annotations: dict[str, object] = {"items": list[Item]}

    field_obj = _synthesized_field()

    @_as_django_type
    class CategoryType:
        __annotations__ = annotations
        items_connection = field_obj

    definition = make_definition(
        Category,
        origin=CategoryType,
        relation_connections={"items_connection": "items"},
    )
    registry.register(Category, CategoryType)
    _register_relation_connection_teardown(
        CategoryType,
        definition,
        generated="items_connection",
        field_obj=field_obj,
        relation_name="items",
        shape="both",
        annotations=annotations,
        annotations_snapshot={"items": list[Item]},
        list_resolver=object(),
    )

    registry.unregister(CategoryType)

    assert CategoryType.__annotations__ is annotations
    assert CategoryType.__annotations__ == {"items": list[Item]}
    assert definition.relation_connections is None


def test_relation_connection_teardown_inverts_a_replaced_annotations_dict() -> None:
    """Teardown applies the per-field inverse when the annotations dict was replaced.

    On Python <= 3.13 Phase 3 (``strawberry.type`` processing,
    ``strawberry.types.object_type._check_field_annotations``) REPLACES the
    class's own ``__annotations__`` dict, so the synthesis-time identity no
    longer matches even though no consumer touched the class. The teardown
    must still drop the synthesized annotation and restore the suppressed
    relation annotation into whatever dict is current.
    """
    synthesis_time_annotations: dict[str, object] = {"items": list[Item]}
    replaced = {"name": str, "items_connection": object}

    field_obj = _synthesized_field()

    @_as_django_type
    class CategoryType:
        __annotations__ = replaced
        items_connection = field_obj

    definition = make_definition(
        Category,
        origin=CategoryType,
        relation_connections={"items_connection": "items"},
    )
    registry.register(Category, CategoryType)
    _register_relation_connection_teardown(
        CategoryType,
        definition,
        generated="items_connection",
        field_obj=field_obj,
        relation_name="items",
        shape="connection",
        annotations=synthesis_time_annotations,
        annotations_snapshot={"name": str, "items": list[Item]},
        list_resolver=object(),
    )

    registry.unregister(CategoryType)

    # Raw ``__dict__`` on purpose: this asserts IDENTITY of the stored dict, and
    # ``inspect.get_annotations`` returns a copy.
    assert CategoryType.__dict__["__annotations__"] is replaced  # noqa: RUF063
    assert replaced == {"name": str, "items": list[Item]}


def test_relation_connection_teardown_keeps_a_present_relation_annotation() -> None:
    """The replaced-dict inverse never overwrites an already-present relation slot."""
    synthesis_time_annotations: dict[str, object] = {"items": list[Item]}
    consumer_items = object()
    replaced = {"items": consumer_items, "items_connection": object}

    field_obj = _synthesized_field()

    @_as_django_type
    class CategoryType:
        __annotations__ = replaced
        items_connection = field_obj

    definition = make_definition(
        Category,
        origin=CategoryType,
        relation_connections={"items_connection": "items"},
    )
    registry.register(Category, CategoryType)
    _register_relation_connection_teardown(
        CategoryType,
        definition,
        generated="items_connection",
        field_obj=field_obj,
        relation_name="items",
        shape="connection",
        annotations=synthesis_time_annotations,
        annotations_snapshot={"items": list[Item]},
        list_resolver=object(),
    )

    registry.unregister(CategoryType)

    assert replaced == {"items": consumer_items}


def test_relation_connection_teardown_refuses_a_non_dict_annotations_entry() -> None:
    """A class-namespace ``__annotations__`` entry that is not a dict is a typed error.

    The failed teardown stays registered; once the entry is a dict again, it runs.
    """
    field_obj = _synthesized_field()

    # Built through ``type()``: a class statement types ``__annotations__`` as a dict.
    category_type = _as_django_type(
        type("CategoryType", (), {"__annotations__": "not-a-dict", "items_connection": field_obj}),
    )

    definition = make_definition(
        Category,
        origin=category_type,
        relation_connections={"items_connection": "items"},
    )
    registry.register(Category, category_type)
    _register_relation_connection_teardown(
        category_type,
        definition,
        generated="items_connection",
        field_obj=field_obj,
        relation_name="items",
        shape="both",
        annotations={},
        annotations_snapshot={},
        list_resolver=object(),
    )

    with pytest.raises(TypeError, match="expected the type the source guarantees, got str"):
        registry.unregister(category_type)

    category_type.__annotations__ = {}
    registry.unregister(category_type)
    assert registry.get(Category) is None


def test_relation_connection_synthesis_refuses_a_non_class_related_model() -> None:
    """A many-side relation whose ``related_model`` is not a model class is a typed error."""
    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type("CategoryType", Category, ("id", "name", "items"))
    definition = category_type.__django_strawberry_definition__
    items = Category._meta.get_field("items")
    unresolved = copy.copy(items)
    vars(unresolved)["related_model"] = "products.Item"
    definition.selected_fields = tuple(
        unresolved if field is items else field for field in definition.selected_fields
    )
    # Synthesis reads only Relay-Node-shaped types, which the interface phase makes them.
    apply_interfaces(category_type, definition)

    with pytest.raises(TypeError, match="expected the type the source guarantees, got str"):
        _synthesize_relation_connections()


def test_registry_clear_removes_synthesized_state_before_different_shape_rebuild() -> None:
    """A fresh same-named type rebuild cannot inherit the prior connection shape.

    The first lifecycle suppresses ``items`` in favor of ``itemsConnection``.
    ``registry.clear()`` removes the exact generated field and restores the
    resolved list annotation/resolver on the discarded class. A module-reload-
    shaped second lifecycle then declares same-named fresh classes with the
    explicit ``"list"`` shape and finalizes without a stale connection.
    """
    item_type = _make_type("ItemType", Item, ("id", "name", "category"))
    old_category_type = _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        meta_extra={"relation_shapes": {"items": "connection"}},
    )
    finalize_django_types()
    old_definition = old_category_type.__django_strawberry_definition__

    assert "items_connection" in old_category_type.__dict__
    assert "items" not in old_category_type.__annotations__
    assert "items" not in old_category_type.__dict__

    registry.clear()

    assert "items_connection" not in old_category_type.__dict__
    assert "items_connection" not in old_category_type.__annotations__
    assert get_args(old_category_type.__annotations__["items"]) == (item_type,)
    assert "items" in old_category_type.__dict__
    assert old_definition.relation_connections is None

    _make_type("ItemType", Item, ("id", "name", "category"))
    fresh_category_type = _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        meta_extra={"relation_shapes": {"items": "list"}},
    )
    finalize_django_types()

    assert "items_connection" not in fresh_category_type.__dict__
    assert fresh_category_type.__django_strawberry_definition__.relation_connections is None


# =============================================================================
# spec-033 - connection-class fast path (Decision 5). The walker's
# windowed prefetch only lands on ``root`` when the PARENT queryset
# flows through ``DjangoOptimizerExtension``, so the fast-path schemas use a
# ``DjangoListField`` root (which the optimizer plans) with the extension
# installed. The existing ``_schema_with_root`` (a plain list resolver the
# optimizer never sees) stays the pipeline-path baseline; the ``1 + N`` cost
# an optimizer-less mount pays is pinned live at
# ``test_products_visibility_api.py::test_nested_connection_costs_one_query_per_parent_without_the_optimizer``.  # noqa: E501 - citation path cannot wrap
# =============================================================================


def _exec(schema: strawberry.Schema, query: str) -> ExecutionResult:
    """Return the complete in-process execution result after asserting no errors."""
    result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    return result


@pytest.mark.django_db
def test_windowed_fast_path_constructs_no_fallback_queryset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A served window constructs no related-manager queryset on the fast path.

    The relation resolver hands windowed rows to ``resolve_connection`` with a
    fallback factory that builds ``genre.books.all()`` only when the fallback
    runs; a served page never calls it, so a windowed request over four parents
    constructs zero querysets.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    for gi in range(4):
        genre = Genre.objects.create(name=f"g{gi}")
        for title in ("a", "b", "c"):
            book = Book.objects.create(title=f"g{gi}-{title}", shelf=shelf)
            book.genres.add(genre)

    schema = _genres_list_schema(optimizer=True)
    calls: list[int] = []
    original_all = Manager[djmodels.Model].all

    def counting_all(self: Manager[djmodels.Model]) -> djmodels.QuerySet[djmodels.Model]:
        if isinstance(getattr(self, "instance", None), Genre):
            calls.append(1)
        return original_all(self)

    with monkeypatch.context() as patch:
        patch.setattr(Manager, "all", counting_all)
        result = _exec(
            schema,
            "{ objs { name booksConnection(first: 2) { edges { node { title } } } } }",
        )
    assert result.data is not None
    assert len(json_list(result.data, "objs")) == 4
    assert all(
        len(json_list(g, "booksConnection", "edges")) == 2 for g in json_list(result.data, "objs")
    )
    assert len(calls) == 0


@pytest.mark.django_db
def test_divergent_alias_per_key_window_preferred_over_shared() -> None:
    """Rows under the per-key attr serve the alias even when the shared attr exists.

    The resolver probes ``_dst_books$<key>_connection`` FIRST and only falls
    back to the legacy shared ``_dst_books_connection``; planting DIFFERENT
    annotated rows under each proves the routing order (a desync here would
    silently serve another alias's window).
    """
    _seed_library_books(["a", "b", "c"])
    _make_type("BookType", Book, ("id", "title"))
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    assert genre_type.__django_strawberry_definition__.model is Genre

    def _resolver() -> list[djmodels.Model]:
        objs = list(Genre.objects.order_by("pk"))
        for obj in objs:
            books = list(obj.books.order_by("pk"))
            per_key = [books[1]]  # "b"
            shared = [books[0], books[2]]  # "a", "c"
            for number, row in enumerate(per_key, start=1):
                setattr(row, WINDOW_ROW_NUMBER, number)
            for number, row in enumerate(shared, start=1):
                setattr(row, WINDOW_ROW_NUMBER, number)
            # ``$``-delimited attrs are not identifier syntax - set via
            # ``setattr``, exactly as Django's prefetch machinery lands them.
            setattr(obj, "_dst_books$x_connection", per_key)
            vars(obj)["_dst_books_connection"] = shared
        return [*objs]

    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[genre_type]},
                "objs": strawberry.field(resolver=_resolver),
            },
        ),
    )
    schema = strawberry.Schema(query=query_cls, config=strawberry_config())
    # The window a plan would publish for the alias's ``first: 2``; no optimizer
    # runs here, so the test publishes it into its own execution frame.
    scope = begin_execution_frame({}, nested=False)
    try:
        publish_planned_windows(
            {resolver_key(genre_type, "books", ("objs", "x")): _FIRST_TWO_WINDOW},
        )
        result = schema.execute_sync(
            "{ objs { x: booksConnection(first: 2) { edges { node { title } } } } }",
        )
    finally:
        end_execution_frame(scope)
    assert result.errors is None, result.errors
    assert result.data is not None
    titles = [json_at(e, "node", "title") for e in json_list(result.data, "objs", 0, "x", "edges")]
    assert titles == ["b"]  # the per-key window, not the shared ["a", "c"]


@pytest.mark.django_db
def test_divergent_mixed_sidecar_strictness_flags_only_the_sidecar_key() -> None:
    """Under ``"raise"``, only the sidecar alias flags - its planned sibling is silent.

    Per-key strictness visibility: the sidecar key stays a real,
    flagged per-parent access with the actionable filter/orderBy reason; the
    planned sibling's identity was recorded, so it never flags.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="raise")
    result = schema.execute_sync(
        "{ objs { "
        'a: booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } "
        "b: booksConnection(first: 5) { edges { node { title } } } "
        "} }",
        context_value=HttpRequest(),
    )
    # The sidecar alias raises with the actionable reason...
    assert result.errors is not None
    messages = [str(e.original_error or e) for e in result.errors]
    assert any("selection carries filter/orderBy" in m for m in messages), messages
    # ...and it is the ONLY flag: the planned sibling never fires the checker.
    assert len([m for m in messages if "Unplanned N+1" in m]) == 1


@pytest.mark.django_db
def test_fast_path_total_count_marker_bypasses_non_queryset_guard() -> None:
    """``totalCount`` over the wrapper does NOT raise the non-queryset count guard.

    The ``_WindowedConnectionRows`` marker is not a ``QuerySet``; the totalCount
    variant must branch on it BEFORE ``_guard_total_count_countable`` /
    ``.count()`` (spec-033 Decision 5), so selecting ``totalCount`` over a
    fast-path window resolves cleanly instead of raising the M1 non-queryset
    ``GraphQLError``.
    """
    _seed_library_books(["a", "b", "c"])
    schema = _genres_list_schema(optimizer=True, book_total_count=True)
    result = schema.execute_sync(
        "{ objs { booksConnection(first: 2) { totalCount edges { node { title } } } } }",
    )
    assert result.errors is None, result.errors
    assert result.data is not None
    assert result.data["objs"][0]["booksConnection"]["totalCount"] == 3


@pytest.mark.django_db
def test_fast_path_ignores_window_when_sidecar_kwargs_present() -> None:
    """A sidecar refuses even an annotated, contradictory window planted by a drifted walker.

    The supported walker never plans a sidecar window, so the manually planted
    rows exercise the resolver's independent refusal rather than walker policy.
    The fallback must query and return banana instead of the annotated apple/avocado.
    """
    _, books = _seed_library_books(["apple", "banana", "avocado"])

    class _BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    make_django_type(
        "BookType",
        Book,
        ("id", "title"),
        meta_extra={"filterset_class": _BookFilter},
    )
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    planted = [books[0], books[2]]
    for number, book in enumerate(planted, start=1):
        setattr(book, WINDOW_ROW_NUMBER, number)

    def _resolver() -> list[Genre]:
        parents = list(Genre.objects.order_by("pk"))
        for parent in parents:
            vars(parent)["_dst_books_connection"] = planted
        return parents

    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[genre_type]},
                "objs": strawberry.field(resolver=_resolver),
            },
        ),
    )
    schema = DjangoSchema(query=query_cls, config=strawberry_config())
    request = RequestFactory().get("/graphql/")
    request.user = AnonymousUser()
    with CaptureQueriesContext(db_connection) as captured:
        result = schema.execute_sync(
            '{ objs { booksConnection(filter: { title: { exact: "banana" } }) '
            "{ edges { node { title } } } } }",
            context_value={"request": request},
        )
    assert result.errors is None, result.errors
    assert result.data == {
        "objs": [{"booksConnection": {"edges": [{"node": {"title": "banana"}}]}}],
    }
    fallback_sql = [
        query["sql"]
        for query in captured.captured_queries
        if 'FROM "library_book"' in query["sql"]
    ]
    assert len(fallback_sql) == 1, fallback_sql
    assert "banana" in fallback_sql[0]
    assert "ROW_NUMBER()" not in fallback_sql[0].upper()


def _page_info(
    connection_cls: type[object],
    selections: str,
    *,
    context: object = None,
) -> strawberry.Info[object, object]:
    """An ``Info`` for a ``books`` field a real schema publishes as ``connection_cls``.

    The page observers (``connection.py::_page_requested``) match ``edges`` /
    ``pageInfo`` by the Python names the schema's field definitions carry, so the
    selection is read against the published connection type, not a stand-in.
    """
    query = strawberry.type(
        type("Query", (), {"__annotations__": {"books": connection_cls}}),
    )
    schema = DjangoSchema(query=query, config=strawberry_config())
    parent_type = schema._schema.query_type
    assert parent_type is not None
    field = schema.get_field_for_type("books", parent_type.name)
    assert field is not None
    raw_info = make_info(
        context=context,
        field_name="books",
        selections=selections,
    )._raw_info._replace(
        parent_type=parent_type,
        return_type=graphql_type_of(graphql_fields(parent_type)["books"]),
        schema=schema._schema,
    )
    return schema.config.info_class(_raw_info=raw_info, _field=field)


@pytest.mark.django_db
@pytest.mark.parametrize("strictness", ["off", "raise"])
def test_fast_path_refuses_a_window_planned_under_other_bounds(strictness: str) -> None:
    """A window fetched for other bounds than the page's own arguments is not served.

    The rows here were fetched for ``first: 3`` (``planned``) while the page
    asks ``first: 2``; serving them would hand back rows of a page nobody
    asked for, so ``resolve_connection`` runs the carried per-parent fallback
    instead. The relation is planned, so that per-parent query reaches
    strictness through the fallback itself: ``"raise"`` refuses it.
    """
    _seed_library_books(["a", "b", "c"])
    book_type = make_django_type("BookType", Book, ("id", "title"))
    finalize_django_types()
    definition = book_type.__django_strawberry_definition__
    connection_cls = _connection_type_for(book_type, definition)
    info = _page_info(
        connection_cls,
        "{ edges { node { title } } }",
        context={DST_OPTIMIZER_STRICTNESS: strictness},
    )
    window = _WindowedConnectionRows(
        # Decoy rows (no title) standing for the first-three page.
        rows=_window_rows(1, 2, 3),
        fallback=_build_windowed_fallback(
            book_type,
            Book.objects.order_by("title").all,
            info,
            definition,
            relation_field_name="books",
            declaring_type=book_type,
        ),
        planned=PlannedWindow(ConnectionWindowBounds(offset=0, limit=3, reverse=False), None),
    )

    def _consume() -> AwaitableOrValue[DjangoConnection[DjangoType]]:
        return _consume_window(
            connection_cls,
            window,
            info=info,
            before=None,
            after=None,
            first=2,
            last=None,
            max_results=100,
            want_count=False,
        )

    if strictness == "raise":
        with pytest.raises(OptimizerError, match="planned window unservable"):
            _consume()
        return
    conn = _consume()
    assert isinstance(conn, connection_cls)
    assert [read_attr(edge.node, "title") for edge in conn.edges] == ["a", "b"]


@pytest.mark.django_db
def test_fallback_when_annotations_missing() -> None:
    """An unannotated reserved list is refused and a fresh per-parent query serves the page.

    Planting only c makes the reserved attribute observably different from the
    actual a/b page; SQL proves recovery ran instead of merely returning a/b
    from an indistinguishable cached list.
    """
    _, books = _seed_library_books(["a", "b", "c"])
    _make_type("BookType", Book, ("id", "title"))
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    assert not hasattr(books[2], WINDOW_ROW_NUMBER)

    def _resolver() -> list[Genre]:
        parents = list(Genre.objects.order_by("pk"))
        for parent in parents:
            vars(parent)["_dst_books_connection"] = [books[2]]
        return parents

    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[genre_type]},
                "objs": strawberry.field(resolver=_resolver),
            },
        ),
    )
    schema = DjangoSchema(query=query_cls, config=strawberry_config())
    with CaptureQueriesContext(db_connection) as captured:
        result = schema.execute_sync(
            "{ objs { booksConnection(first: 2) { edges { node { title } } } } }",
        )
    assert result.errors is None, result.errors
    assert result.data == {
        "objs": [
            {
                "booksConnection": {
                    "edges": [{"node": {"title": "a"}}, {"node": {"title": "b"}}],
                },
            },
        ],
    }
    fallback_sql = [
        query["sql"]
        for query in captured.captured_queries
        if 'FROM "library_book"' in query["sql"]
    ]
    assert len(fallback_sql) == 1, fallback_sql
    # The upstream offset connection fetches one probe row beyond first: 2.
    assert "LIMIT 3" in fallback_sql[0].upper()
    assert "ROW_NUMBER()" not in fallback_sql[0].upper()


# =============================================================================
# Strictness wiring for connection paths (spec-033 Decision 8).
#
# The synthesized relation-connection resolver consults the union-published
# optimizer sentinels via the PARAMETERIZED ``types/resolvers.py::_check_n1``
# (kind="connection_to_attr") before the per-parent fallback pipeline. An
# unplanned, unserved nested-connection access fires the B3 contract -
# ``OptimizerError`` under ``"raise"``, a logged warning under ``"warn"`` -
# through the SAME machinery list relations use. These pins need an
# optimizer-installed, strictness-active schema (the fakeshop project schema
# runs strictness-off), so they live here, not in the live suite (Test plan).
#
# The sidecar-filtered ``booksConnection(filter: ...)`` is the clearest
# live-reachable refusal arm (spec-033 Decision 6): the walker leaves it
# unplanned, so the resolver runs per-parent and is visible to strictness.
# =============================================================================


@pytest.mark.django_db
def test_strictness_raise_unplanned_nested_connection() -> None:
    """``"raise"`` + optimizer + a fallback nested connection -> ``OptimizerError``.

    The flagged message NAMES the generated relation field (the ``field_name``
    stem, the relation field name ``books`` the walker keyed the would-be plan
    under), exactly as a plain list relation's strictness flag reads.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="raise")
    result = schema.execute_sync(
        '{ objs { booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is not None
    messages = [str(e.original_error or e) for e in result.errors]
    assert any(isinstance(e.original_error, OptimizerError) for e in result.errors)
    assert any("Unplanned N+1: books" in m for m in messages)


@pytest.mark.django_db
def test_strictness_raise_malformed_cursor_surfaces_pagination_error_not_optimizer_error() -> None:
    """A malformed nested ``after:`` cursor raises the PAGINATION error, not ``OptimizerError``.

    Error-locality regression (spec-033 Decision 4 step f / Decision 8): a
    malformed cursor leaves the connection unwindowed so the per-parent pipeline
    can raise its own cursor-validation error. Under strictness ``"raise"`` the
    walker must still record the resolver key for this fallback, or the B3 check
    preempts the real error with a spurious ``OptimizerError("Unplanned N+1")``.
    The user should see the cursor error, not an optimizer defect.
    """
    _seed_library_books(["a", "b", "c"])
    schema = _genres_list_schema(optimizer=True, strictness="raise")
    result = schema.execute_sync(
        '{ objs { booksConnection(first: 2, after: "not-a-valid-cursor") '
        "{ edges { node { title } } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is not None
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, PaginationArgumentError)
    assert str(result.errors[0].original_error) == (
        "Argument 'after' contains a non-existing value."
    )


@pytest.mark.django_db
def test_sidecar_fallback_is_flagged_with_reason() -> None:
    """A sidecar fallback's ``"raise"`` message carries an ACTIONABLE reason.

    spec-033 Decision 6 consistency pin (rationale bullet "A whole-relation
    refusal stays visible to strictness on purpose"): a consumer who legitimately filters a nested
    connection gets a per-parent fallback that strictness flags - the message
    must explain WHY (the filter/orderBy wording) so it does not look like an
    optimizer defect.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="raise")
    result = schema.execute_sync(
        '{ objs { booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is not None
    messages = [str(e.original_error or e) for e in result.errors]
    assert any("selection carries filter/orderBy" in m for m in messages), messages


@pytest.mark.django_db
def test_strictness_warn_nested_fallback_preserves_parent_plan_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A completed warn-mode fallback preserves the parent's private planned-key stash.

    Resolve the filtered connection first so its optimizer publication really
    precedes the list sibling. Exact payload and warnings pin the consumer
    verdict; the post-execution stash membership pins the private union even
    when a prefetched list or the scoped-relation channel would mask its loss.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="warn")
    genre_type = registry.get(Genre)
    assert genre_type is not None
    request = HttpRequest()
    with CaptureQueriesContext(db_connection) as captured, caplog.at_level("WARNING"):
        result = schema.execute_sync(
            '{ objs { booksConnection(filter: { title: { exact: "banana" } }) '
            "{ edges { node { title } } } books { title } } }",
            context_value=request,
        )
    assert result.errors is None, result.errors
    assert result.data == {
        "objs": [
            {
                "booksConnection": {"edges": [{"node": {"title": "banana"}}]},
                "books": [{"title": title} for title in ("apple", "banana", "avocado")],
            },
        ],
    }
    assert caplog.messages == [
        (
            "Potential N+1 on books "
            "(not window-planned: selection carries filter/orderBy; resolving per-parent)"
        ),
    ]
    planned = read_attr(request, "dst_optimizer_planned")
    assert isinstance(planned, frozenset)
    assert resolver_key(genre_type, "books", ("objs", "books")) in planned
    book_sql = [
        query["sql"]
        for query in captured.captured_queries
        if 'FROM "library_book"' in query["sql"]
    ]
    assert len(book_sql) == 2, book_sql
    assert sum("banana" in query for query in book_sql) == 1


def test_strictness_silent_when_planned() -> None:
    """A planned connection key short-circuits BEFORE the ``to_attr`` probe.

    The load-bearing resolver-key parity: the resolver-side ``_check_n1`` builds
    ``resolver_key(declaring_type, relation_field_name, runtime_path)`` - the
    IDENTICAL shape the walker emits for a nested connection
    (``walker.py::_resolver_identities_for #"resolver_key(type_cls, relation_field_name"``,
    reached from ``_plan_connection_relation``). When that exact key is in
    ``DST_OPTIMIZER_PLANNED`` the resolver is silent even with the ``to_attr``
    ABSENT on ``root`` (the planned short-circuit beats the connection probe), so
    a window-planned connection never false-flags. A divergent key
    (generated ``books_connection`` name, or the target type) would miss the
    planned set and spuriously fire - this asserts the match directly.
    """

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    # The walker keys a planned connection under (declaring type, RELATION FIELD
    # NAME, runtime path) - matched here at resolve time off ``info.path``.
    info = SimpleNamespace(
        context={
            "dst_optimizer_planned": {
                resolver_key(GenreType, "books", ("objs", "booksConnection")),
            },
            "dst_optimizer_strictness": "raise",
        },
        path=_path("objs", 0, "booksConnection"),
    )
    # No window served, yet planned -> silent. The call mirrors the
    # connection.py consultation exactly.
    _check_n1(
        info,
        SimpleNamespace(),
        "books",
        GenreType,
        kind="connection_to_attr",
        reason="not window-planned; resolving per-parent",
    )

    # Sanity counter-proof: the SAME shape with the key absent DOES fire, so the
    # silence above is the planned-key match, not an inert no-op.
    info_unplanned = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=_path("objs", 0, "booksConnection"),
    )
    with pytest.raises(OptimizerError, match=r"Unplanned N\+1: books \("):
        _check_n1(
            info_unplanned,
            SimpleNamespace(),
            "books",
            GenreType,
            kind="connection_to_attr",
            reason="not window-planned; resolving per-parent",
        )


# ---------------------------------------------------------------------------
# Conditional ``_dst_total_count`` (spec-033 Decision 4).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("row_numbers", "offset"),
    [((1, 2), 0), ((1,), 5)],
    ids=["populated-page", "marker-only-overshoot"],
)
def test_count_less_window_with_count_observer_falls_back_defensively(
    row_numbers: tuple[int, ...],
    offset: int,
) -> None:
    """An observed count missing from a manually drifted window requires recovery.

    The planner and resolver share count selection, so these contradictory
    wrappers are private defense checks. Populated and marker-only pages each
    get an independent verdict rather than hiding the second assertion.
    """
    window = _WindowedConnectionRows(
        rows=_window_rows(*row_numbers),
        fallback=lambda: None,
    )
    assert (
        _resolve_from_window(
            DjangoConnection,
            window,
            info=make_info(),
            offset=offset,
            limit=2,
            want_count=True,
        )
        is None
    )


# ---------------------------------------------------------------------------
# Consumer-assigned relation gate under strictness (strawberry-django #697).
# ---------------------------------------------------------------------------


def _windowed_book_connection_class(
    *,
    total_count: bool = False,
) -> type[DjangoConnection[DjangoType]]:
    """A real generated ``<TypeName>Connection`` class for direct-call pins."""
    book_type = make_django_type(
        "BookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}} if total_count else None,
    )
    finalize_django_types()
    return _connection_type_for(book_type, book_type.__django_strawberry_definition__)


#: A count-free plain ``first: 2`` window row: with ``totalCount`` observed and no
#: count annotation, ``_resolve_from_window`` refuses it (the conditional-count
#: drift guard).
_COUNT_LESS_WINDOW_ROWS = _window_rows(1)

#: The planned window of an offset ``first: 2`` page, the bounds the direct-call pins derive.
_FIRST_TWO_WINDOW = PlannedWindow(ConnectionWindowBounds(offset=0, limit=2, reverse=False), None)


@pytest.mark.django_db
def test_consume_window_unservable_window_runs_the_sync_fallback() -> None:
    """The unservable-window tail of ``_consume_window`` is a defensive layer.

    No live path produces it (the planner and the resolver share the count
    selection walk, and the ambiguous-empty shapes serve from markers), but the
    resolve side must not ASSUME walker behavior: a window the resolver refuses
    (here: a count-less window under an observed ``totalCount``) recovers the
    carried per-parent queryset and runs the shipped sync pipeline.
    """
    connection_cls = _windowed_book_connection_class(total_count=True)
    calls: list[str] = []

    def _fallback() -> djmodels.QuerySet[Book]:
        calls.append("fallback")
        return Book.objects.none()

    window = _WindowedConnectionRows(
        rows=_COUNT_LESS_WINDOW_ROWS,
        fallback=_fallback,
        planned=_FIRST_TWO_WINDOW,
    )
    conn = _consume_window(
        connection_cls,
        window,
        # The shipped pipeline probes ``info.selected_fields`` for the
        # edges-resolution shortcut; an empty selection list is enough.
        info=make_info(),
        before=None,
        after=None,
        first=2,
        last=None,
        max_results=100,
        want_count=True,
    )
    assert isinstance(conn, DjangoConnection)
    assert conn.edges == []

    assert calls == ["fallback"]


@pytest.mark.django_db(transaction=True)
async def test_consume_window_unservable_window_runs_the_async_fallback() -> None:
    """The async sibling: an async-iterable fallback routes through ``_attach_count_async``.

    That is the awaitable arm of ``_consume_fallback``.
    """
    connection_cls = _windowed_book_connection_class(total_count=True)
    calls: list[str] = []

    def _fallback() -> djmodels.QuerySet[Book]:
        calls.append("fallback")
        return Book.objects.none()

    window = _WindowedConnectionRows(
        rows=_COUNT_LESS_WINDOW_ROWS,
        fallback=_fallback,
        planned=_FIRST_TWO_WINDOW,
    )
    pending = _consume_window(
        connection_cls,
        window,
        info=make_info(),
        before=None,
        after=None,
        first=2,
        last=None,
        max_results=100,
        want_count=True,
    )
    assert inspect.isawaitable(pending)
    conn = await pending
    assert conn.edges == []

    assert calls == ["fallback"]


@pytest.mark.django_db(transaction=True)
async def test_consume_window_recovery_runs_the_async_pipeline_under_async_execution() -> None:
    """The recovery the synthesized resolver carries is colored per call, like the resolver.

    Under the asynchronous executor ``_build_windowed_fallback`` hands back
    ``_pipeline_async``'s coroutine, and ``_consume_window`` awaits it before the
    per-parent tail. The target's ``get_queryset`` is ``async def``, which the
    synchronous pipeline refuses, so a served page proves the async pipeline ran.
    """

    async def _visible_books(
        _cls: type[DjangoType],
        queryset: djmodels.QuerySet[Book],
        _info: object,
    ) -> djmodels.QuerySet[Book]:
        return queryset.exclude(title="hidden")

    book_type = make_django_type(
        "AsyncHookBookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
        namespace_extra={"get_queryset": classmethod(_visible_books)},
    )
    await sync_to_async(finalize_django_types)()
    definition = book_type.__django_strawberry_definition__
    connection_cls = _connection_type_for(book_type, definition)
    await sync_to_async(_seed_library_books)(["shown", "hidden"])
    info = await sync_to_async(_page_info)(connection_cls, "{ edges { node { title } } }")
    window = _WindowedConnectionRows(
        rows=_COUNT_LESS_WINDOW_ROWS,
        fallback=_build_windowed_fallback(
            book_type,
            Book.objects.all,
            info,
            definition,
            relation_field_name="books",
            declaring_type=book_type,
        ),
        planned=_FIRST_TWO_WINDOW,
    )
    pending = _consume_window(
        connection_cls,
        window,
        info=info,
        before=None,
        after=None,
        first=2,
        last=None,
        max_results=100,
        want_count=True,
    )
    assert inspect.isawaitable(pending)
    conn = await pending
    assert [read_attr(edge.node, "title") for edge in conn.edges] == ["shown"]


@pytest.mark.django_db
def test_consume_window_offset_unwindowable_shape_propagates() -> None:
    """An OFFSET connection never recovers from ``UnwindowableConnection``.

    The two bounds derivations share one ``try``, but not one outcome. A keyset
    connection treats the refusal as the defensive backward-shape handoff and
    recovers the per-parent queryset; an offset connection has no such shape --
    the walker never plans one -- so a wrapper that reaches here alongside a
    refused window is real pagination drift and must surface, not silently
    degrade to the fallback and serve a differently-paginated page.
    """
    connection_cls = _windowed_book_connection_class()
    window = _WindowedConnectionRows(rows=[], fallback=Book.objects.none)
    with pytest.raises(UnwindowableConnection):
        _consume_window(
            connection_cls,
            window,
            info=make_info(),
            before=None,
            # ``after`` + ``last`` with no ``first`` / ``before`` is the
            # offset-bearing backward window the derivation refuses.
            after=to_base64("arrayconnection", 0),
            first=None,
            last=2,
            max_results=100,
            want_count=False,
        )


#: The ``CURSOR_PREFIX`` a consumer edge class declares in place of ``arrayconnection``.
_CONSUMER_CURSOR_PREFIX = "bookcursor"


def _consumer_edge_book_connection_class() -> type[DjangoConnection[DjangoType]]:
    """A ``DjangoConnection`` subclass whose edge class declares its own ``CURSOR_PREFIX``.

    No public path hands a window to a consumer connection (the planner windows
    only generated connections), so the window consumer is driven directly.
    """
    book_type = make_django_type("BookType", Book, ("id", "title"))
    # ``make_django_type`` declares a Relay-Node-shaped type, so it is the
    # ``relay.Node`` the edge is generic over.
    relay_node = cast("type[relay.Node]", book_type)
    edge_type = strawberry.type(
        new_class(
            "BookCursorEdge",
            (relay.Edge[relay_node],),
            exec_body=lambda namespace: namespace.update(CURSOR_PREFIX=_CONSUMER_CURSOR_PREFIX),
        ),
    )
    connection_type = strawberry.type(
        new_class(
            "BookCursorConnection",
            (DjangoConnection[book_type],),
            exec_body=lambda namespace: namespace.update(
                {"__annotations__": {"edges": list[edge_type]}},
            ),
        ),
    )
    finalize_django_types()
    return connection_type


def _consume_consumer_prefix_window(cursor_prefix: str) -> object:
    """Consume a window on the consumer-prefix connection from an ``after`` cursor at index 0."""
    return _consume_window(
        _consumer_edge_book_connection_class(),
        _WindowedConnectionRows(
            rows=_window_rows(1, 2, 3),
            fallback=Book.objects.none,
            planned=PlannedWindow(ConnectionWindowBounds(offset=1, limit=2, reverse=False), None),
        ),
        info=make_info(),
        before=None,
        after=to_base64(cursor_prefix, 0),
        first=2,
        last=None,
        max_results=100,
        want_count=False,
    )


@pytest.mark.django_db
def test_consume_window_serves_the_connections_own_prefix_cursor() -> None:
    """A window is bounded by a cursor under the connection's own edge prefix and mints under it."""
    conn = _consume_consumer_prefix_window(_CONSUMER_CURSOR_PREFIX)
    assert isinstance(conn, DjangoConnection)
    edges = cast("list[relay.Edge[relay.Node]]", conn.edges)
    assert [from_base64(edge.cursor) for edge in edges] == [
        (_CONSUMER_CURSOR_PREFIX, "1"),
        (_CONSUMER_CURSOR_PREFIX, "2"),
    ]


@pytest.mark.django_db
def test_consume_window_refuses_a_stock_cursor_under_a_consumer_prefix() -> None:
    """A stock ``arrayconnection`` cursor is the cursor error, never a position into the window.

    It is not a cursor this connection issued, so the window derivation refuses
    it under the connection's own edge prefix.
    """
    with pytest.raises(
        PaginationArgumentError,
        match=r"^Argument 'after' contains a non-existing value\.$",
    ):
        _consume_consumer_prefix_window(relay.Edge.CURSOR_PREFIX)
