"""Shared consumer connection declarations for package and live HTTP tests."""

from collections.abc import Callable, Iterable
from types import new_class
from typing import TypeAlias, cast

import strawberry
from apps.products.models import Category, Item
from django.db import models
from django.db.models import Q
from django.http import HttpRequest
from graphql_client import JSONObject
from strawberry import relay
from strawberry.relay.utils import from_base64
from strawberry.schema.config import StrawberryConfig
from strawberry.types import Info
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import (
    DjangoConnection,
    DjangoConnectionField,
    _connection_type_for,
)
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.permissions import apply_cascade_permissions
from django_strawberry_framework.schema import DjangoSchema
from django_strawberry_framework.utils._narrowing import (
    is_str,
    require,
)
from django_strawberry_framework.utils._queryset_private import (
    set_queryset_deferred_filter,
    set_queryset_hints,
)
from tests._catalog_data import categories_from_seed
from tests._idioms import declare_django_type, json_at, json_list, json_object
from tests._info import make_info


def _edge_names(connection: object) -> list[str]:
    """The ``node.name`` of every edge in a connection payload, each asserted to be a string."""
    return [
        require(json_at(edge, "node", "name"), is_str) for edge in json_list(connection, "edges")
    ]


def _make_node_type(name: str, *, total_count: bool | None) -> type[DjangoType]:
    """Build a Relay-Node-shaped ``DjangoType`` over ``Category`` for a test.

    ``total_count`` controls the opt-in: ``True`` / ``False`` declares
    ``Meta.connection = {"total_count": ...}``; ``None`` omits the key.
    """
    meta_attrs: dict[str, object] = {
        "model": Category,
        "fields": ("id", "name"),
        "interfaces": (relay.Node,),
        "name": name,
    }
    if total_count is not None:
        meta_attrs["connection"] = {"total_count": total_count}
    return declare_django_type(name, {"Meta": type("Meta", (), meta_attrs)})


def _schema_for(node_type: type[DjangoType]) -> strawberry.Schema:
    """Build an in-process schema exposing ``items`` as a connection over ``node_type``.

    The connection type comes from ``_connection_type_for`` so the schema
    exercises whichever generated ``<TypeName>Connection`` shape (with or
    without ``totalCount``) the node type's ``Meta.connection`` selects,
    through the real Strawberry relay slicing / ``info`` path.
    """
    connection_type = _connection_type_for(node_type, node_type.__django_strawberry_definition__)

    def items_resolver() -> Iterable[Category]:
        return Category.objects.all().order_by("pk")

    query_namespace = {
        "__annotations__": {"items": connection_type},
        "items": relay.connection(connection_type, resolver=items_resolver),
    }
    query_cls = strawberry.type(type("Query", (), query_namespace))
    finalize_django_types()
    return strawberry.Schema(query=query_cls, config=strawberry_config())


def _info_with_selection(*field_names: str) -> Info[object, object]:
    """An ``info`` whose connection selection set carries ``field_names``."""
    return make_info(field_name="connectionField", selections=f"{{ {' '.join(field_names)} }}")


class _CategoryFilter(FilterSet):
    class Meta:
        model = Category
        fields = {"name": ["exact", "icontains"]}


class _CategoryOrder(OrderSet):
    class Meta:
        model = Category
        fields = ["name"]


def _make_sidecar_node_type(
    name: str,
    *,
    total_count: bool = False,
    filterset: type | None = _CategoryFilter,
    orderset: type | None = _CategoryOrder,
    get_queryset: Callable[..., object] | None = None,
) -> type[DjangoType]:
    """Build a Relay-Node ``DjangoType`` over ``Category`` with optional sidecars.

    ``filterset`` / ``orderset`` default to the module fixtures; pass ``None`` to
    omit a sidecar. ``get_queryset`` (when given) is installed as a method so the
    visibility hook / ``SyncMisuseError`` paths can be exercised.
    """
    meta_attrs: dict[str, object] = {
        "model": Category,
        "fields": ("id", "name"),
        "interfaces": (relay.Node,),
        "name": name,
    }
    if filterset is not None:
        meta_attrs["filterset_class"] = filterset
    if orderset is not None:
        meta_attrs["orderset_class"] = orderset
    if total_count:
        meta_attrs["connection"] = {"total_count": True}
    namespace: dict[str, object] = {"Meta": type("Meta", (), meta_attrs)}
    if get_queryset is not None:
        namespace["get_queryset"] = classmethod(get_queryset)
    return declare_django_type(name, namespace)


def _field_schema(
    node_type: type[DjangoType],
    *,
    resolver: Callable[..., object] | None = None,
    optimizer: DjangoOptimizerExtension | None = None,
    config: StrawberryConfig | None = None,
) -> strawberry.Schema:
    """Build an in-process schema exposing ``items`` via ``DjangoConnectionField``.

    ``config`` overrides the default ``strawberry_config()`` (e.g. a
    ``relay_max_results`` passthrough); ``None`` keeps the default.
    """
    conn_type = _connection_type_for(node_type, node_type.__django_strawberry_definition__)
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"items": conn_type},
                "items": DjangoConnectionField(node_type, resolver=resolver),
            },
        ),
    )
    finalize_django_types()
    extensions = [lambda: optimizer] if optimizer is not None else []
    return strawberry.Schema(
        query=query_cls,
        config=config or strawberry_config(),
        extensions=extensions,
    )


def _capture_info(node_type: type[DjangoType]) -> Info[object, object]:
    """Return a real resolver ``Info`` captured from an in-process execution.

    The composition-pipeline helpers (``_pipeline_sync`` / ``_finalize_queryset``)
    need a real ``Info`` (the optimizer plan reads ``info._raw_info`` for
    ``field_nodes`` / ``operation`` / ``fragments``); a ``SimpleNamespace`` double
    is insufficient. A hand-written ``relay.connection`` resolver stashes the
    ``Info`` it is handed during a throwaway query.
    """
    conn_type = _connection_type_for(node_type, node_type.__django_strawberry_definition__)
    captured: dict[str, strawberry.Info[object, object]] = {}

    def capture(info: strawberry.Info[object, object]) -> Iterable[Category]:
        captured["info"] = info
        return Category.objects.all()

    query_cls = strawberry.type(
        type(
            "CaptureQuery",
            (),
            {
                "__annotations__": {"items": conn_type},
                "items": relay.connection(conn_type, resolver=capture),
            },
        ),
    )
    finalize_django_types()
    schema = strawberry.Schema(query=query_cls, config=strawberry_config())
    schema.execute_sync("{ items { edges { node { id } } } }")
    return captured["info"]


def _make_relation_node_type(
    name: str,
    *,
    fields: tuple[str, ...],
    model: type[models.Model] = Category,
    list_relations: tuple[str, ...] = (),
) -> type[DjangoType]:
    """Build a bare Relay-Node ``DjangoType`` (no sidecars) exposing ``fields``.

    The optimizer tests below reach a relation under ``edges { node }``; the
    sidecar machinery (``_make_sidecar_node_type``) is irrelevant noise here, so
    this builds the minimal Relay-Node shape with the relation field exposed.

    ``list_relations`` names the many-side relations that must keep their RAW
    LIST form. The package default is ``"connection"``, so a test that plans a
    prefetch under a plain ``items { ... }`` selection has to ask for the list
    shape explicitly.
    """
    meta_attrs: dict[str, object] = {
        "model": model,
        "fields": fields,
        "interfaces": (relay.Node,),
        "name": name,
    }
    if list_relations:
        meta_attrs["relation_shapes"] = dict.fromkeys(list_relations, "both")
    return declare_django_type(
        name,
        {"Meta": type("Meta", (), meta_attrs)},
    )


def _node_over(
    model: type[models.Model],
    name: str,
    *,
    fields: tuple[str, ...] = ("id", "name"),
) -> type[DjangoType]:
    """Build a minimal registered ``DjangoType`` over ``model`` (no Relay needed)."""
    return declare_django_type(
        name,
        {"Meta": type("Meta", (), {"model": model, "fields": fields, "name": name})},
    )


_CATEGORY_ORDER_SHAPE_PREFIX = (
    "_CategoryOrder.apply_sync must return an unevaluated, unsliced "
    "QuerySet of Category rows; got "
)


class _DeferredFilterQuerySet(models.QuerySet[Category]):
    """A project queryset class, used here to carry a deferred filter Django never writes.

    A PENDING predicate is ordinary: Django's related-manager machinery leaves
    one on every relation queryset whatever class built it, and the seal bakes
    it. What cannot be faithfully rebuilt is a deferred-filter STATE outside the
    exact shape Django writes, which is what this class is planted with.
    """


async def _awaitable_queryset(queryset: object) -> object:
    return queryset


def _order_override_evaluated(
    _cls: type[_CategoryOrder],
    _order_input: object,
    queryset: models.QuerySet[Category],
    _info: object,
) -> models.QuerySet[Category]:
    list(queryset)
    return queryset


def _order_override_untrusted(
    _cls: type[_CategoryOrder],
    _order_input: object,
    _queryset: models.QuerySet[Category],
    _info: object,
) -> _DeferredFilterQuerySet:
    candidate = _DeferredFilterQuerySet(model=Category)
    # ``negate`` decides whether the predicate is inverted and is truth-tested to
    # do it, so Django's exact ``bool`` is the only shape the bake accepts there.
    # basedpyright: plants a non-``bool`` negate, a deferred-filter shape Django never writes
    set_queryset_deferred_filter(candidate, (1, (), {"name": "A"}))  # pyright: ignore[reportArgumentType]
    return candidate


def _order_override_in_place_routing(
    _cls: type[_CategoryOrder],
    _order_input: object,
    queryset: models.QuerySet[Category],
    _info: object,
) -> models.QuerySet[Category]:
    set_queryset_hints(queryset, {"tenant": 2})
    return queryset


def _order_override_passthrough(
    cls: type[_CategoryOrder],
    order_input: object,
    queryset: models.QuerySet[Category],
    info: object,
) -> models.QuerySet[Category]:
    return super(_CategoryOrder, cls).apply_sync(order_input, queryset, info)


_OrderOverride: TypeAlias = Callable[
    [
        type[_CategoryOrder],
        object,
        models.QuerySet[Category],
        object,
    ],
    object,
]


_OrderRow: TypeAlias = tuple[str, _OrderOverride, str, tuple[str, ...]]


_CONNECTION_MALFORMED_ORDER_ROWS: tuple[_OrderRow, ...] = (
    (
        "evaluated",
        _order_override_evaluated,
        _CATEGORY_ORDER_SHAPE_PREFIX + "evaluated defect",
        (),
    ),
    (
        "materialized-list",
        lambda _cls, _order_input, queryset, _info: list(queryset),
        _CATEGORY_ORDER_SHAPE_PREFIX + "type defect",
        (),
    ),
    (
        "none",
        lambda _cls, _order_input, _queryset, _info: None,
        _CATEGORY_ORDER_SHAPE_PREFIX + "type defect",
        (),
    ),
    (
        "projection",
        lambda _cls, _order_input, queryset, _info: queryset.values("name"),
        _CATEGORY_ORDER_SHAPE_PREFIX + "projection defect",
        (),
    ),
    (
        "wrong-model",
        lambda _cls, _order_input, _queryset, _info: Item.objects.all(),
        _CATEGORY_ORDER_SHAPE_PREFIX + "table defect",
        (),
    ),
    (
        "sliced",
        lambda _cls, _order_input, queryset, _info: queryset.order_by("name")[:1],
        _CATEGORY_ORDER_SHAPE_PREFIX + "sliced defect",
        (),
    ),
    (
        "combined-duplicates",
        lambda _cls, _order_input, queryset, _info: queryset.union(queryset, all=True),
        (
            "_CategoryOrder.apply_sync returned a combined queryset; the visibility boundary serves a "
            "combined queryset as the set of Category primary keys it selects"
        ),
        ("union: union(all=True) keeps duplicate rows, which a primary-key set cannot",),
    ),
    (
        "awaitable-in-sync",
        lambda _cls, _order_input, queryset, _info: _awaitable_queryset(queryset),
        "_CategoryOrder.apply_sync returned an awaitable in a sync resolver context.",
        (),
    ),
    (
        "routing-rewritten-in-place",
        _order_override_in_place_routing,
        "_CategoryOrder.apply_sync changed database routing intent",
        ("expected db=None, hints={}", "got db=None, hints={'tenant': 2}"),
    ),
    (
        "malformed-deferred-filter",
        _order_override_untrusted,
        _CATEGORY_ORDER_SHAPE_PREFIX + "untrusted defect",
        ("deferred filter negate is a int",),
    ),
)


_CONSUMER_CURSOR_PREFIX = "categorycursor"


_CONSUMER_WALK_PAGES = 3


def _consumer_edge_schema(node_type: type[DjangoType]) -> strawberry.Schema:
    """Build a schema whose ``items`` is a consumer connection with its own cursor prefix.

    Strawberry's documented customization: an ``Edge`` subclass declaring
    ``CURSOR_PREFIX`` and a ``DjangoConnection`` subclass whose ``edges`` are
    that edge, mounted with ``relay.connection`` over the same ordered source
    ``_schema_for`` serves.
    """
    # The node type declares ``Meta.interfaces = (relay.Node,)``, so it is the
    # ``relay.Node`` the edge is generic over.
    relay_node = cast("type[relay.Node]", node_type)
    edge_type = strawberry.type(
        new_class(
            "CategoryCursorEdge",
            (relay.Edge[relay_node],),
            exec_body=lambda namespace: namespace.update(CURSOR_PREFIX=_CONSUMER_CURSOR_PREFIX),
        ),
    )
    connection_type = strawberry.type(
        new_class(
            "CategoryCursorConnection",
            (DjangoConnection[node_type],),
            exec_body=lambda namespace: namespace.update(
                {"__annotations__": {"edges": list[edge_type]}},
            ),
        ),
    )

    def items_resolver() -> Iterable[Category]:
        return Category.objects.all().order_by("pk")

    query_namespace = {
        "__annotations__": {"items": connection_type},
        "items": relay.connection(connection_type, resolver=items_resolver),
    }
    query_cls = strawberry.type(type("Query", (), query_namespace))
    finalize_django_types()
    return strawberry.Schema(query=query_cls, config=strawberry_config())


def _page_query(argument: str, cursor: str | None) -> str:
    """One page of two, forward (``after`` + ``first``) or backward (``before`` + ``last``)."""
    size = "first" if argument == "after" else "last"
    bound = "" if cursor is None else f', {argument}: "{cursor}"'
    return (
        f"{{ items({size}: 2{bound}) {{ edges {{ cursor node {{ id }} }} "
        "pageInfo { startCursor endCursor } } }"
    )


def _walk_pages(
    execute: Callable[[str], JSONObject],
    argument: str,
) -> list[tuple[str, tuple[str, str]]]:
    """Walk ``_CONSUMER_WALK_PAGES`` pages, each requested from the previous page's own cursor.

    Returns every edge served as its node id beside its decoded cursor
    ``(prefix, index)``, so a walk under one prefix compares to a walk under another.
    """
    walk: list[tuple[str, tuple[str, str]]] = []
    cursor: str | None = None
    for _ in range(_CONSUMER_WALK_PAGES):
        items = json_object(execute(_page_query(argument, cursor)), "items")
        walk.extend(
            (str(json_at(edge, "node", "id")), from_base64(str(json_at(edge, "cursor"))))
            for edge in json_list(items, "edges")
        )
        page_info = json_object(items, "pageInfo")
        cursor = str(page_info["endCursor" if argument == "after" else "startCursor"])
    return walk


def _swap_prefix(walk: list[tuple[str, tuple[str, str]]]) -> list[tuple[str, tuple[str, str]]]:
    """The same walk with every cursor re-prefixed under the consumer prefix."""
    return [(node_id, (_CONSUMER_CURSOR_PREFIX, index)) for node_id, (_prefix, index) in walk]


def _make_cascading_item_node(name: str) -> type[DjangoType]:
    """Relay-Node ``DjangoType`` over ``Item`` (forward FK ``category``) that cascades.

    ``_make_sidecar_node_type`` is hardcoded to ``Category`` (the chain TOP, no
    forward FK to cascade), so the connection cascade pin needs a minimal local
    variant over ``Item`` (plan discretion item (a)): same Relay-Node /
    ``total_count`` shape, sidecars omitted (the pin exercises visibility, not
    filter/order), and a ``get_queryset`` that calls ``apply_cascade_permissions``
    so items whose ``category`` is hidden drop out of the connection.
    """

    def get_queryset(
        cls: type[DjangoType],
        queryset: models.QuerySet[Item],
        info: object,
    ) -> models.QuerySet[Item]:
        return apply_cascade_permissions(cls, queryset, info)

    return declare_django_type(
        name,
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": Item,
                    "fields": ("id", "name"),
                    "interfaces": (relay.Node,),
                    "name": name,
                    "connection": {"total_count": True},
                },
            ),
            "get_queryset": classmethod(get_queryset),
        },
    )


class _HostileConnQuerySet(models.QuerySet[Category]):
    """A predicate-erasing / synthetic-count ``QuerySet`` subclass.

    Every override would widen the result if the framework dispatched through the
    consumer object: ``.filter()`` / ``.order_by()`` drop all narrowing, slicing
    returns the unfiltered rows, and ``.count()`` / ``.acount()`` report the raw
    table count. The seal rebuilds a plain ``QuerySet`` from the validated query
    state, so none of these run.
    """

    @override
    def filter(self, *args: object, **kwargs: object) -> models.QuerySet[Category]:
        return Category.objects.all()

    @override
    def order_by(self, *args: object, **kwargs: object) -> models.QuerySet[Category]:
        return Category.objects.all()

    @override
    # basedpyright: deliberately answers a slice with a list, the shape the seal must neutralize
    def __getitem__(self, item: int | slice) -> Category | list[Category]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return list(Category.objects.all().order_by("pk"))[item]

    @override
    def count(self) -> int:
        return Category.objects.count()

    @override
    async def acount(self) -> int:
        return await Category.objects.acount()


def _hostile_visibility_hook(
    _cls: type[DjangoType],
    _qs: models.QuerySet[Category],
    _info: object,
) -> models.QuerySet[Category]:
    """Return the hostile subclass carrying a genuine ``is_private=False`` predicate."""
    return models.QuerySet[Category].filter(_HostileConnQuerySet(model=Category), is_private=False)


def _seed_public_private_categories() -> list[str]:
    """Create two public + one private ``Category``; return the ordered public names."""
    public_a, public_b, _private = categories_from_seed(
        ("public_a", False),
        ("public_b", False),
        ("private_x", True),
    )
    return [public_a.name, public_b.name]


class _ListManager(models.Manager[Category]):
    """A hostile Manager whose ``.all()`` degrades into a plain list (a bypass shape)."""

    @override
    # basedpyright: deliberately degrades ``all()`` into a list, the bypass shape the guard refuses
    def all(self) -> list[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return ["secret"]


def _degrading_manager() -> models.Manager[Category]:
    """An unrouted ``_ListManager`` bound to ``Category``."""
    manager = _ListManager()
    manager.model = Category
    manager._db = None
    return manager


class _DriftManager(models.Manager[Category]):
    """A Manager pinned to one alias whose ``.all()`` silently routes to another."""

    @override
    def get_queryset(self) -> models.QuerySet[Category]:
        return Category.objects.using("elsewhere")


def _alias_drift_manager() -> models.Manager[Category]:
    """A ``_DriftManager`` pinned to ``other`` whose ``.all()`` drifts to ``elsewhere``."""
    manager = _DriftManager()
    manager.model = Category
    manager._db = "other"
    return manager


def _node_type(
    name: str,
    *,
    model: type[models.Model],
    orderset: type | None = None,
    filterset: type | None = None,
    get_queryset: Callable[..., object] | None = None,
) -> type[DjangoType]:
    """Build a Relay-Node ``DjangoType`` whose definition attribute a test can swap.

    A test replaces the class's ``__django_strawberry_definition__`` with a
    decoy over another model once the definition is captured, so any residual
    read of the class would be consequential: rows of the wrong table.

    ``get_queryset`` installs a visibility hook on the target. It changes which
    metadata the planner needs: a target with a hook sends its child queryset
    through the visibility runner, which is the seam the captured MODEL is
    threaded into, so only an instrumented hook-bearing target can witness that
    half of the capture.
    """
    meta_attrs = {
        "model": model,
        "fields": ("id", "name"),
        "interfaces": (relay.Node,),
        "name": name,
        "primary": False,
    }
    if filterset is not None:
        meta_attrs["filterset_class"] = filterset
    if orderset is not None:
        meta_attrs["orderset_class"] = orderset
    namespace: dict[str, object] = {"Meta": type("Meta", (), meta_attrs)}
    if get_queryset is not None:
        namespace["get_queryset"] = classmethod(get_queryset)
    return declare_django_type(name, namespace)


def _item_node_type(name: str) -> type[DjangoType]:
    """Build a Relay-Node ``DjangoType`` over ``Item`` to serve as a decoy definition."""
    return declare_django_type(
        name,
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": Item,
                    "fields": ("id", "name"),
                    "interfaces": (relay.Node,),
                    "name": name,
                    "primary": False,
                },
            ),
        },
    )


_PLANNED_LIST_DOCUMENT = "{ parents { edges { node { name items { name } } } } }"


_PLANNED_CONNECTION_DOCUMENT = (
    "{ parents { edges { node { name itemsConnection(first: 2) { edges { node { name } } } } } } }"
)


def _planned_relation_schema(
    suffix: str,
    *,
    hook_calls: list[type[models.Model]] | None,
) -> tuple[DjangoSchema, DjangoOptimizerExtension]:
    """Compose the parent/child/decoy trio and return ``(schema, optimizer)``.

    The child carries a visibility hook exactly when ``hook_calls`` is given. That
    is the dimension the capture's two halves split on: a hook-less target never
    reaches the visibility runner, so it cannot witness the captured model the
    walker threads there, and a request against one says nothing about a target
    that does.
    """

    class OptimizedParentNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")
            interfaces = (relay.Node,)
            name = f"OptimizedParent{suffix}"
            relation_shapes = {"items": "both"}
            primary = True

    def _hook(
        _cls: type[DjangoType],
        queryset: models.QuerySet[Item],
        _info: object,
    ) -> models.QuerySet[Item]:
        assert hook_calls is not None  # installed only when the caller collects hook calls
        hook_calls.append(queryset.model)
        return queryset

    child = _node_type(
        f"OptimizedChild{suffix}",
        model=Item,
        get_queryset=None if hook_calls is None else _hook,
    )
    decoy = declare_django_type(
        f"OptimizedChildDecoy{suffix}",
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": Category,
                    "fields": ("id", "name"),
                    "interfaces": (relay.Node,),
                    "name": f"OptimizedChildDecoy{suffix}",
                    "primary": False,
                },
            ),
        },
    )
    # The decoy answers with Category, not Item: a plan built from it would
    # seed, seal and window the wrong table outright rather than merely differ.
    assert decoy.__django_strawberry_definition__.model is Category

    finalize_django_types()
    parent_conn = _connection_type_for(
        OptimizedParentNode,
        OptimizedParentNode.__django_strawberry_definition__,
    )
    query_cls = strawberry.type(
        type(
            f"OptimizedQuery{suffix}",
            (),
            {
                "__annotations__": {"parents": parent_conn},
                "parents": DjangoConnectionField(OptimizedParentNode),
            },
        ),
    )
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    child.__django_strawberry_definition__ = decoy.__django_strawberry_definition__
    return schema, optimizer


def _planned_relation_request(
    schema: strawberry.Schema,
    optimizer: DjangoOptimizerExtension,
    document: str,
    vocabulary: str,
) -> tuple[set[str], tuple[int, int, int]]:
    """Run one planned request; report its child names and the plan cache counters after it."""
    result = schema.execute_sync(document, context_value={"request": HttpRequest()})
    assert result.errors is None, result.errors
    info = optimizer.cache_info()
    assert result.data is not None
    rows = {
        name
        for parent in json_list(result.data, "parents", "edges")
        for name in _relation_page(json_at(parent, "node"), vocabulary)
    }
    return rows, (info.hits, info.misses, info.size)


def _relation_page(node: object, vocabulary: str) -> list[str]:
    """Read the child names out of whichever relation vocabulary the document selected."""
    if vocabulary == "List":
        return [require(json_at(row, "name"), is_str) for row in json_list(node, "items")]
    return _edge_names(json_at(node, "itemsConnection"))


_CATEGORY_FILTER_SHAPE_PREFIX = (
    "_CategoryFilter.apply_sync must return an unevaluated, unsliced "
    "QuerySet of Category rows; got "
)


_FILTERED_CONNECTION_QUERY = (
    '{ items(filter: {name: {iContains: ""}}) { edges { node { name } } } }'
)


def _filter_override_in_place_routing(
    _cls: type[_CategoryFilter],
    _input_value: object,
    queryset: models.QuerySet[Category],
    _info: object,
) -> models.QuerySet[Category]:
    set_queryset_hints(queryset, {"tenant": 2})
    return queryset


_FilterOverride: TypeAlias = Callable[
    [
        type[_CategoryFilter],
        object,
        models.QuerySet[Category],
        object,
    ],
    object,
]


_FilterRow: TypeAlias = tuple[str, _FilterOverride, str, tuple[str, ...]]


_CONNECTION_MALFORMED_FILTER_ROWS: tuple[_FilterRow, ...] = (
    (
        "evaluated",
        lambda _cls, _input_value, queryset, _info: (list(queryset), queryset)[1],
        _CATEGORY_FILTER_SHAPE_PREFIX + "evaluated defect",
        (),
    ),
    (
        "none",
        lambda _cls, _input_value, _queryset, _info: None,
        _CATEGORY_FILTER_SHAPE_PREFIX + "type defect",
        (),
    ),
    (
        "projection",
        lambda _cls, _input_value, queryset, _info: queryset.values("name"),
        _CATEGORY_FILTER_SHAPE_PREFIX + "projection defect",
        (),
    ),
    (
        "wrong-model",
        lambda _cls, _input_value, _queryset, _info: Item.objects.all(),
        _CATEGORY_FILTER_SHAPE_PREFIX + "table defect",
        (),
    ),
    (
        "sliced",
        lambda _cls, _input_value, queryset, _info: queryset.order_by("name")[:1],
        _CATEGORY_FILTER_SHAPE_PREFIX + "sliced defect",
        (),
    ),
    (
        "combined-duplicates",
        lambda _cls, _input_value, queryset, _info: queryset.union(queryset, all=True),
        (
            "_CategoryFilter.apply_sync returned a combined queryset; the visibility boundary serves a "
            "combined queryset as the set of Category primary keys it selects"
        ),
        ("union: union(all=True) keeps duplicate rows, which a primary-key set cannot",),
    ),
    (
        "awaitable-in-sync",
        lambda _cls, _input_value, queryset, _info: _awaitable_queryset(queryset),
        "_CategoryFilter.apply_sync returned an awaitable in a sync resolver context.",
        (),
    ),
    (
        "routing-rewritten-in-place",
        _filter_override_in_place_routing,
        "_CategoryFilter.apply_sync changed database routing intent",
        ("expected db=None, hints={}", "got db=None, hints={'tenant': 2}"),
    ),
)


def _combined_get_queryset(
    _cls: type[DjangoType],
    qs: models.QuerySet[Category],
    _info: object,
) -> models.QuerySet[Category]:
    return qs.filter(name__startswith="a").union(qs.filter(name__startswith="b"))


def _a_or_b_category_names() -> list[str]:
    return sorted(
        Category.objects.filter(Q(name__startswith="a") | Q(name__startswith="b")).values_list(
            "name",
            flat=True,
        ),
    )
