"""Live HTTP execution over relations whose link is not a plain pk ``ForeignKey``.

A child joins its parent through a ``ForeignObject`` (one or two carrier
columns), a ``ForeignKey`` bound on a non-pk ``to_field``, or an M2M whose
through model's foreign keys bind on non-pk ``to_field`` columns. The optimizer
derives every column of such a link from
``django_strawberry_framework/utils/relations.py::relation_link``: the child's
carrier columns load under the prefetch ``.only()`` and partition the window
when there is exactly one, and the parent's non-pk target columns load under the
parent ``.only()``, so no row refetches a deferred link column. A two-column link
has no single partition expression and resolves per parent. A forward hop loads
its own carriers and, on the Prefetch path, every target column of the link.

Fakeshop does not publish every link direction and cardinality exercised here, so
the test-local models of
``tests/optimizer/_link_models.py`` stand in on a holder HTTP mount. Each row compares
the optimized wire against the optimizer-off wire and pins the optimized query count.

A raw JSON filter holder deliberately registers no parent type, so a two-column
relation's ``isnull`` filter tests the stored carriers instead of joining a parent.
"""

from collections.abc import Callable, Iterator
from functools import wraps

import pytest
import strawberry
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, assert_graphql_success
from strategy_schemas import make_django_type
from strawberry import relay
from strawberry.scalars import JSON

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    OptimizerHint,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import _connection_type_cache
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils._narrowing import is_dict, is_list, is_str, require
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import is_object_dict, is_object_list
from tests.optimizer._link_models import (
    LnkColumnChild,
    LnkOptionalPairChild,
    LnkPairChild,
    LnkParent,
    LnkSlugChild,
    LnkTag,
    link_fixture_tables,
)

pytestmark = pytest.mark.usefixtures("private_registry")

_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-link/", _graphql_view)]


def _post(schema: DjangoSchema, query: str) -> JSONObject:
    """Send the operation through the package view using the current holder schema."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return assert_graphql_success(query, url="/graphql-link/")
    finally:
        _CURRENT["schema"] = None


def _link_statements(captured: CaptureQueriesContext) -> list[str]:
    """Count statements over the synthetic link graph, excluding middleware queries."""
    return [
        query["sql"]
        for query in captured.captured_queries
        if '"products_lnk' in query["sql"] or "`products_lnk" in query["sql"]
    ]


@pytest.fixture
def link_tables() -> Iterator[None]:
    """Materialize and seed the link fixture tables for one row."""
    with link_fixture_tables(connection):
        yield


def _parent_visibility(
    _cls: type[DjangoType],
    queryset: QuerySet[LnkParent],
    _info: object,
    **_kwargs: object,
) -> QuerySet[LnkParent]:
    """An identity ``get_queryset`` hook: forces every hop onto the parent into a ``Prefetch``."""
    return queryset


def _schema(*, optimizer: bool, parent_hook: bool) -> DjangoSchema:
    registry.clear()
    _connection_type_cache.clear()
    make_django_type("LnkPairChildType", LnkPairChild, ("id", "name"))
    column_type = make_django_type("LnkColumnChildType", LnkColumnChild, ("id", "name", "parent"))
    slug_type = make_django_type("LnkSlugChildType", LnkSlugChild, ("id", "name", "parent"))
    tag_type = make_django_type(
        "LnkTagType",
        LnkTag,
        ("id", "name", "parents"),
        meta_extra={"relation_shapes": {"parents": "both"}},
    )
    relations = (
        "pair_children",
        "column_children",
        "slug_children",
        "tags",
    )
    parent_type = make_django_type(
        "LnkParentType",
        LnkParent,
        ("id", "label", *relations),
        meta_extra={"relation_shapes": dict.fromkeys(relations, "both")},
        namespace_extra=(
            {"get_queryset": classmethod(_parent_visibility)} if parent_hook else None
        ),
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {
                    "parents": list[parent_type],
                    "parents_connection": DjangoConnection[parent_type],
                    "column_children": list[column_type],
                    "slug_children": list[slug_type],
                    "tags": list[tag_type],
                },
                "parents": DjangoListField(parent_type),
                "parents_connection": DjangoConnectionField(parent_type),
                "column_children": DjangoListField(column_type),
                "slug_children": DjangoListField(slug_type),
                "tags": DjangoListField(tag_type),
            },
        ),
    )
    extensions = []
    if optimizer:
        extension = DjangoOptimizerExtension()
        extensions = [lambda: extension]
    return DjangoSchema(query=query_cls, config=strawberry_config(), extensions=extensions)


def _run(query: str, *, parent_hook: bool = False) -> tuple["_WireData", int]:
    """Execute ``query`` optimized; return its data and query count after the oracle agrees."""
    expected = _post(_schema(optimizer=False, parent_hook=parent_hook), query)
    schema = _schema(optimizer=True, parent_hook=parent_hook)
    with CaptureQueriesContext(connection) as ctx:
        data = _post(schema, query)
    assert data == expected
    return require(data, is_object_dict), len(_link_statements(ctx))


#: One decoded GraphQL wire object; each member is narrowed where a test reads it.
_WireData = dict[object, object]


def _at(value: object, *keys: str) -> object:
    """The member of wire value ``value`` at the object-key path ``keys``."""
    for key in keys:
        assert is_object_dict(value), value
        value = value[key]
    return value


def _list_at(value: object, *keys: str) -> list[object]:
    """The wire list member of ``value`` at the object-key path ``keys``."""
    return require(_at(value, *keys), is_object_list)


def _names(rows: list[object], key: str) -> list[list[object]]:
    return [[_at(child, "name") for child in _list_at(row, key)] for row in rows]


def _edge_names(rows: list[object], key: str) -> list[list[object]]:
    return [[_at(edge, "node", "name") for edge in _list_at(row, key, "edges")] for row in rows]


_EXPECTED_ROWS = [["a1", "a2", "a3"], ["b1"], []]
_EXPECTED_PAGE = [["a1", "a2"], ["b1"], []]


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("link_tables")
def test_two_column_link_list_prefetch_loads_every_carrier() -> None:
    """A plain list over the two-column link is one parent query plus one prefetch.

    The prefetch ``.only()`` carries both ``p_tenant`` and ``p_code`` (the
    attach key), and the parent ``.only()`` carries ``tenant`` and ``code`` (the
    link targets the selection never names), so no row refetches either.
    """
    data, queries = _run("{ parents { label pairChildren { name } } }")
    assert _names(_list_at(data, "parents"), "pairChildren") == _EXPECTED_ROWS
    assert queries == 2


_LINK_CONNECTION_ROOT_ROWS: list[tuple[str, Callable[[_WireData], list[object]]]] = [
    (
        "{ parents { label pairChildrenConnection(first: 2) { edges { node { name } } } } }",
        lambda data: _list_at(data, "parents"),
    ),
    (
        (
            "{ parentsConnection(first: 10) { edges { node { label "
            "pairChildrenConnection(first: 2) { edges { node { name } } } } } } }"
        ),
        lambda data: [_at(edge, "node") for edge in _list_at(data, "parentsConnection", "edges")],
    ),
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("query", "rows_of"),
    _LINK_CONNECTION_ROOT_ROWS,
    ids=["list_root", "connection_root"],
)
@pytest.mark.usefixtures("link_tables")
def test_two_column_link_connection_resolves_per_parent(
    query: str,
    rows_of: Callable[[_WireData], list[object]],
) -> None:
    """A nested connection over the two-column link has no partition and resolves per parent.

    The window is left unplanned (one page query per parent after the root
    query), the parent rows still carry the link targets, and the pages match
    the optimizer-off wire exactly.
    """
    data, queries = _run(query)
    assert _edge_names(rows_of(data), "pairChildrenConnection") == _EXPECTED_PAGE
    assert queries == 1 + 3


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("relation", "query"),
    [
        ("columnChildren", "{ parents { label columnChildren { name } } }"),
        ("slugChildren", "{ parents { label slugChildren { name } } }"),
    ],
    ids=["one_column_foreign_object", "to_field_foreign_key"],
)
@pytest.mark.usefixtures("link_tables")
def test_one_column_link_list_prefetch_is_batched(relation: str, query: str) -> None:
    """A plain list over a one-column link is one parent query plus one prefetch.

    The child carrier (``p_id`` / the ``slug`` FK column) and, for the
    ``to_field`` link, the parent's ``slug`` load in the projections, so
    neither side refetches per row.
    """
    data, queries = _run(query)
    assert _names(_list_at(data, "parents"), relation) == _EXPECTED_ROWS
    assert queries == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("relation", "query"),
    [
        (
            "columnChildrenConnection",
            "{ parents { label columnChildrenConnection(first: 2) { edges { node { name } } } } }",
        ),
        (
            "slugChildrenConnection",
            "{ parents { label slugChildrenConnection(first: 2) { edges { node { name } } } } }",
        ),
    ],
    ids=["one_column_foreign_object", "to_field_foreign_key"],
)
@pytest.mark.usefixtures("link_tables")
def test_one_column_link_connection_is_one_window(relation: str, query: str) -> None:
    """A nested connection over a one-column link is one root query plus one window.

    The window partitions by the lone carrier column, and both projections load
    the link columns, so no page row and no parent refetches a deferred column.
    """
    data, queries = _run(query)
    assert _edge_names(_list_at(data, "parents"), relation) == _EXPECTED_PAGE
    assert queries == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "root",
    ["columnChildren", "slugChildren"],
    ids=["one_column_foreign_object", "to_field_foreign_key"],
)
@pytest.mark.usefixtures("link_tables")
def test_forward_link_prefetch_loads_the_child_carrier(root: str) -> None:
    """A forward hop downgraded to a ``Prefetch`` is one child query plus one parent query.

    The parent type's ``get_queryset`` forces the ``Prefetch``, whose attach reads
    the child row's carrier (``p_id``, or the ``slug`` FK column): the child
    ``.only()`` carries it, so no child row refetches it.
    """
    data, queries = _run(f"{{ {root} {{ name parent {{ label }} }} }}", parent_hook=True)
    assert [_at(row, "parent", "label") for row in _list_at(data, root)] == [
        "pa",
        "pa",
        "pa",
        "pb",
    ]
    assert queries == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("link_tables")
def test_conflicting_alias_connection_loads_the_parent_link_columns() -> None:
    """A connection refused for conflicting alias arguments still loads the parent ``slug``.

    Two aliases of one parent hop select the nested connection with different
    ``first:`` under one response key, so the planner leaves it to per-parent
    resolution; that resolution reads each parent's ``slug``, which the
    ``select_related`` projection (``parent__label`` selected, ``slug`` not)
    still carries, so no parent row refetches it: one root query plus one page
    query per child row and alias.
    """
    query = (
        "{ slugChildren { name "
        "a: parent { label slugChildrenConnection(first: 1) { edges { node { name } } } } "
        "b: parent { label slugChildrenConnection(first: 2) { edges { node { name } } } } } }"
    )
    data, queries = _run(query)
    first_child = _list_at(data, "slugChildren")[0]
    assert [
        _at(edge, "node", "name")
        for edge in _list_at(first_child, "a", "slugChildrenConnection", "edges")
    ] == [
        "a1",
    ]
    assert [
        _at(edge, "node", "name")
        for edge in _list_at(first_child, "b", "slugChildrenConnection", "edges")
    ] == ["a1", "a2"]
    assert queries == 1 + 4 * 2


def _leaf(node: object) -> str:
    assert is_dict(node)
    leaf = node.get("name", node.get("label"))
    assert isinstance(leaf, str)
    return leaf


def _related_nodes(related: object) -> list[object]:
    """One wire row's related rows: a list field's items, or a connection's edge nodes."""
    if is_list(related):
        return related
    assert is_dict(related)
    edges = related["edges"]
    assert is_list(edges)
    nodes: list[object] = []
    for edge in edges:
        assert is_dict(edge)
        nodes.append(edge["node"])
    return nodes


def _m2m_rows(data: _WireData) -> list[list[str]]:
    """Each root row's related leaves, from a list field or a connection's edges."""
    root = require(data.get("parents", data.get("tags")), is_object_list)
    rows: list[list[str]] = []
    for row in root:
        assert is_object_dict(row)
        related = next(value for key, value in row.items() if key not in {"label", "name"})
        rows.append([_leaf(node) for node in _related_nodes(related)])
    return rows


_M2M_ROWS = {
    "forward_list": ("{ parents { label tags { name } } }", [["t1", "t2", "t3"], ["t1"], []]),
    "forward_connection": (
        "{ parents { label tagsConnection(first: 2) { edges { node { name } } } } }",
        [["t1", "t2"], ["t1"], []],
    ),
    "reverse_list": ("{ tags { name parents { label } } }", [["pa", "pb"], ["pa"], ["pa"]]),
    "reverse_connection": (
        "{ tags { name parentsConnection(first: 1) { edges { node { label } } } } }",
        [["pa"], ["pa"], ["pa"]],
    ),
}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("row", list(_M2M_ROWS), ids=list(_M2M_ROWS))
@pytest.mark.usefixtures("link_tables")
def test_m2m_through_to_field_link_loads_the_source_key(row: str) -> None:
    """An M2M hop whose through FK targets a non-pk column loads that column on the source.

    Django matches through rows to source rows by the through FK's target
    (``LnkParent.slug`` forward, ``LnkTag.code`` reverse), reading it off every
    source row; the source ``.only()`` carries it, so a list or a window is one
    root query plus one batched query, with the optimizer-off wire's rows.
    """
    query, expected_rows = _M2M_ROWS[row]
    data, queries = _run(query)
    assert _m2m_rows(data) == expected_rows
    assert queries == 2


def _pair_parent_schema(*, optimizer: bool, route: str) -> DjangoSchema:
    """Expose the two-column forward ``ForeignObject`` through a consumer-authored field.

    ``"annotation"`` annotates ``parent`` over a target whose ``get_queryset``
    forces a ``Prefetch``; ``"hint"`` assigns a resolver and opts back into
    planning with ``OptimizerHint.prefetch_related()``.
    """
    registry.clear()
    _connection_type_cache.clear()
    parent_namespace: dict[str, object] = {
        "Meta": type("Meta", (), {"model": LnkParent, "fields": ("id", "label")}),
    }
    if route == "annotation":
        parent_namespace["get_queryset"] = classmethod(_parent_visibility)
    parent_type = type("LnkParentType", (DjangoType,), parent_namespace)
    child_meta: dict[str, object] = {"model": LnkPairChild, "fields": ("id", "name", "parent")}
    child_namespace: dict[str, object] = {"__annotations__": {"parent": parent_type | None}}
    if route == "hint":
        child_meta["optimizer_hints"] = {"parent": OptimizerHint.prefetch_related()}

        def _parent(root: LnkPairChild) -> LnkParent | None:
            return root.parent

        child_namespace["parent"] = strawberry.field(
            resolver=_parent,
            graphql_type=parent_type | None,
        )
    child_namespace["Meta"] = type("Meta", (), child_meta)
    child_type = type("LnkPairChildType", (DjangoType,), child_namespace)
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"pairs": list[child_type]}, "pairs": DjangoListField(child_type)},
        ),
    )
    extensions = []
    if optimizer:
        extension = DjangoOptimizerExtension()
        extensions = [lambda: extension]
    return DjangoSchema(query=query_cls, config=strawberry_config(), extensions=extensions)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("route", ["annotation", "hint"], ids=["visibility_hook", "prefetch_hint"])
@pytest.mark.usefixtures("link_tables")
def test_consumer_authored_two_column_forward_link_prefetch_loads_every_target(
    route: str,
) -> None:
    """A prefetched two-column forward link is one child query plus one parent query.

    Django attaches each prefetched parent by the link's targets (``tenant``,
    ``code``), which ``relation_link`` names and the parent ``.only()`` carries,
    alongside the child's two carriers, so no row on either side refetches.
    """
    query = "{ pairs { name parent { label } } }"
    expected = _post(_pair_parent_schema(optimizer=False, route=route), query)
    schema = _pair_parent_schema(optimizer=True, route=route)
    with CaptureQueriesContext(connection) as ctx:
        data = _post(schema, query)
    assert data == expected
    assert [
        (_at(row, "name"), _at(row, "parent", "label")) for row in _list_at(data, "pairs")
    ] == [
        ("a1", "pa"),
        ("a2", "pa"),
        ("a3", "pa"),
        ("b1", "pb"),
    ]
    assert len(_link_statements(ctx)) == 2


def _generated_pair_schema(
    *,
    optimizer: bool,
    parent_hook: bool,
    child_model: type = LnkPairChild,
) -> DjangoSchema:
    """Expose a two-column forward ``ForeignObject`` as the generated ``parent`` field.

    The child type names ``parent`` in ``Meta.fields``; the parent type exposes
    the reverse ``pair_children`` of ``LnkPairChild`` as a list and a
    connection, so a selection can walk the link forward and back. ``parent_hook`` gives the
    parent type an identity ``get_queryset``, which turns the forward hop into a
    ``Prefetch``.
    """
    registry.clear()
    _connection_type_cache.clear()
    reverse = ("pair_children",) if child_model is LnkPairChild else ()
    make_django_type(
        "LnkParentType",
        LnkParent,
        ("id", "label", *reverse),
        meta_extra={"relation_shapes": dict.fromkeys(reverse, "both")} if reverse else None,
        namespace_extra=(
            {"get_queryset": classmethod(_parent_visibility)} if parent_hook else None
        ),
    )
    child_type = make_django_type(
        f"{child_model.__name__}Type",
        child_model,
        ("id", "name", "parent"),
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {
                    "pairs": list[child_type],
                    "pairs_connection": DjangoConnection[child_type],
                },
                "pairs": DjangoListField(child_type),
                "pairs_connection": DjangoConnectionField(child_type),
            },
        ),
    )
    extensions = []
    if optimizer:
        extension = DjangoOptimizerExtension()
        extensions = [lambda: extension]
    return DjangoSchema(query=query_cls, config=strawberry_config(), extensions=extensions)


def _run_generated(
    query: str,
    *,
    parent_hook: bool = False,
    child_model: type = LnkPairChild,
) -> tuple[_WireData, list[str]]:
    """Execute ``query`` optimized over the generated link; return its data and SQL.

    The optimizer-off wire is the oracle: the optimized data must equal it.
    """
    expected = _post(
        _generated_pair_schema(
            optimizer=False,
            parent_hook=parent_hook,
            child_model=child_model,
        ),
        query,
    )
    schema = _generated_pair_schema(
        optimizer=True,
        parent_hook=parent_hook,
        child_model=child_model,
    )
    with CaptureQueriesContext(connection) as ctx:
        data = _post(schema, query)
    assert data == expected
    return require(data, is_object_dict), _link_statements(ctx)


def _pair_rows(data: _WireData) -> list[object]:
    """The child rows of a ``pairs`` list or a ``pairsConnection`` page."""
    if "pairs" in data:
        return _list_at(data, "pairs")
    return [_at(edge, "node") for edge in _list_at(data, "pairsConnection", "edges")]


_PAIR_PARENTS = [
    ("a1", "pa"),
    ("a2", "pa"),
    ("a3", "pa"),
    ("b1", "pb"),
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "query",
    [
        "{ pairs { name parent { label } } }",
        "{ pairsConnection(first: 10) { edges { node { name parent { label } } } } }",
    ],
    ids=["list_root", "connection_root"],
)
@pytest.mark.parametrize(
    ("parent_hook", "queries"),
    [(False, 1), (True, 2)],
    ids=["select_related", "prefetch"],
)
@pytest.mark.usefixtures("link_tables")
def test_generated_two_column_forward_link_resolves_every_parent(
    query: str,
    *,
    parent_hook: bool,
    queries: int,
) -> None:
    """The generated forward field over a two-column link joins on both columns.

    ``pa`` and ``pb`` share ``code="A"`` under different tenants, so a link that
    joined on one column would hand ``b1`` the wrong parent. Without a parent
    ``get_queryset`` the hop is one ``select_related`` join; with one it is a
    ``Prefetch`` matched on ``(tenant, code)``, one query more.
    """
    data, sql = _run_generated(query, parent_hook=parent_hook)
    assert [
        (_at(row, "name"), _at(row, "parent", "label")) for row in _pair_rows(data)
    ] == _PAIR_PARENTS
    assert len(sql) == queries


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("link_tables")
def test_generated_two_column_forward_link_id_selection_joins_the_parent() -> None:
    """An id-only selection over the link reads the parent row, never one carrier column.

    FK-id elision answers an id-only hop from the source row's one link column;
    a two-column link has no such column, so the hop stays a join and every
    child gets its own parent's pk.
    """
    data, sql = _run_generated("{ pairs { name parent { id } } }")
    parent_ids = dict(LnkParent.objects.values_list("label", "id"))
    assert [
        (_at(row, "name"), int(relay.from_base64(require(_at(row, "parent", "id"), is_str))[1]))
        for row in _list_at(data, "pairs")
    ] == [(name, parent_ids[label]) for name, label in _PAIR_PARENTS]
    assert len(sql) == 1
    assert 'JOIN "products_lnkparent"' in sql[0]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("relation", "queries"),
    [
        ("pairChildren { name }", 2),
        ("pairChildrenConnection(first: 2) { edges { node { name } } }", 1 + 4),
    ],
    ids=["reverse_list", "reverse_connection"],
)
@pytest.mark.usefixtures("link_tables")
def test_generated_two_column_forward_link_round_trips_through_the_reverse_side(
    relation: str,
    queries: int,
) -> None:
    """Forward over the link and back through its reverse side returns each parent's children.

    The reverse list prefetches on both carriers (one query after the join);
    the reverse connection has no single partition column and pages per
    parent row.
    """
    data, sql = _run_generated(f"{{ pairs {{ name parent {{ label {relation} }} }} }}")
    siblings = {"pa": ["a1", "a2", "a3"], "pb": ["b1"]}
    for row in _list_at(data, "pairs"):
        parent = _at(row, "parent")
        assert is_object_dict(parent)
        related = next(value for key, value in parent.items() if key != "label")
        expected = siblings[require(parent["label"], is_str)]
        if not is_list(related):
            expected = expected[:2]
        assert [_leaf(node) for node in _related_nodes(related)] == expected
    assert len(sql) == queries


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("parent_hook", "queries"),
    [(False, 1), (True, 2)],
    ids=["select_related", "prefetch"],
)
@pytest.mark.usefixtures("link_tables")
def test_generated_nullable_two_column_forward_link_resolves_absent_parents_to_null(
    *,
    parent_hook: bool,
    queries: int,
) -> None:
    """A ``null=True`` link over nullable carriers is null wherever no parent matches.

    Both carriers ``NULL``, one carrier ``NULL`` and carriers matching no parent
    all resolve ``null`` and keep their row: the join is an outer join, and the
    prefetch leaves the unmatched rows without a parent.
    """
    data, sql = _run_generated(
        "{ pairs { name parent { label } } }",
        parent_hook=parent_hook,
        child_model=LnkOptionalPairChild,
    )
    assert [
        (_at(row, "name"), _at(row, "parent") and _at(row, "parent", "label"))
        for row in _list_at(data, "pairs")
    ] == [
        ("o1", "pa"),
        ("o2", None),
        ("o3", None),
        ("o4", None),
    ]
    assert len(sql) == queries
    if not parent_hook:
        assert 'LEFT OUTER JOIN "products_lnkparent"' in sql[0]


def _unregistered_pair_filter_schema() -> DjangoSchema:
    class PairFilter(FilterSet):
        class Meta:
            model = LnkOptionalPairChild
            fields = {"parent": ["isnull"]}

    class PairOutput(DjangoType):
        class Meta:
            model = LnkOptionalPairChild
            fields = ("name",)

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[LnkOptionalPairChild]:
        del root
        return PairFilter.apply_sync(where, LnkOptionalPairChild.objects.order_by("id"), info)

    def resolve_all(root: object) -> QuerySet[LnkOptionalPairChild]:
        del root
        return LnkOptionalPairChild.objects.order_by("id")

    @strawberry.type
    class Query:
        rows: QuerySet[LnkOptionalPairChild] = strawberry.field(
            resolver=resolve_rows,
            graphql_type=list[PairOutput],
        )
        all_rows: QuerySet[LnkOptionalPairChild] = strawberry.field(
            resolver=resolve_all,
            graphql_type=list[PairOutput],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("link_tables")
@pytest.mark.parametrize(
    ("is_null", "names"),
    [(True, ["o2", "o3"]), (False, ["o1", "o4"])],
    ids=["null-carrier", "set-carriers"],
)
def test_unregistered_two_column_relation_filters_test_null_carriers_without_joining_a_parent(
    *,
    is_null: bool,
    names: list[str],
) -> None:
    """A dangling pair with two set carriers stays nonnull; either null carrier answers null."""
    schema = _unregistered_pair_filter_schema()
    literal = "true" if is_null else "false"
    query = "{ rows(where: { parent: { is_null: " + literal + " } }) { name } allRows { name } }"
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, query)
    assert payload == {
        "rows": [{"name": name} for name in names],
        "allRows": [
            {"name": name}
            for name in (
                "o1",
                "o2",
                "o3",
                "o4",
            )
        ],
    }, payload
    statements = _link_statements(captured)
    assert len(statements) == 2, statements
    assert all(" JOIN " not in statement.upper() for statement in statements), statements
    assert all('"products_lnkparent"' not in statement for statement in statements), statements
