"""Package Relay refetch construction, identity, cache and exception-class contracts.

Consumer refetch over HTTP lives in
``examples/fakeshop/test_query/test_library_api.py`` (shipped model-label
refetch) and ``examples/fakeshop/test_query/test_node_refetch_api.py`` (consumer
type-name routing, shared rows and lazy proxies, custom NodeID columns,
alternate primary-key spellings and override return contracts).

This module owns construction/finalize refusal (``DjangoSchema``'s check of a
typed field's annotation against its target included), class cache and private
decoder status, stamp identity, original_error exception classes, helper return
shapes and public-export identity. The private stamping tests inspect the
original ORM row's cast attribute directly; the required-node test inspects the
original model exception hidden by the GraphQL error envelope. Refetch over key
shapes no fakeshop model carries (an unhashable comma-list key, a decimal key
SQLite stores as a float, naive datetime keys in the default time zone) runs
over HTTP on function-local models in ``test_node_refetch_api.py``, as do the
sync-misuse messages whose exception classes stay here. The NodeID over a
queryset annotation refetches live on ``SeriesType``
(``test_library_api.py::test_library_series_node_refetches_by_its_annotated_handle``).
Fakeshop ships no ``type+model`` secondary, so the hook a ``type+model``
type-name id reads (its named type's, where the emitted model-label id reads the
primary's) is pinned here on function-local types.
"""

import re
from collections.abc import Awaitable, Callable, Iterable, Iterator
from types import UnionType

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from asgiref.sync import sync_to_async
from django.db import DEFAULT_DB_ALIAS, connection
from django.db.models import Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils.functional import SimpleLazyObject
from strategy_schemas import make_django_type
from strawberry import relay
from strawberry.schema_directive import Location as DirectiveLocation
from strawberry.schema_directive import schema_directive
from strawberry.types.cast import TYPE_CAST_ATTRIBUTE
from typing_extensions import override

import django_strawberry_framework
import django_strawberry_framework.relay as relay_module
from django_strawberry_framework import (
    DjangoNodeField,
    DjangoNodesField,
    DjangoSchema,
    DjangoType,
    ErrorPolicy,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.relay import (
    GlobalIDDecode,
    _coerce_pk_or_none,
    _node_fields_declared,
    _stamp_node_type,
    decode_model_global_id,
)
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.types.relay import implements_relay_node
from django_strawberry_framework.utils import truth as real_truth
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.utils.querysets import SyncMisuseError
from tests._idioms import (
    saved_pk,
)


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Drop registry state (and the co-cleared node-field ledger) around each test."""
    registry.clear()
    yield
    registry.clear()


def _gid(type_name: str, node_id: object) -> str:
    """Encode a ``GlobalID`` payload string the way the framework emits it."""
    return str(relay.GlobalID(type_name, str(node_id)))


def _make_node_type(
    name: str,
    *,
    model: type[Model] = Category,
    strategy: str | None = None,
    interfaces: tuple[type, ...] = (relay.Node,),
) -> type[DjangoType]:
    """Build a Relay-Node-shaped ``DjangoType`` over ``model`` for a test."""
    meta_attrs = {
        "model": model,
        "fields": ("id", "name"),
        "interfaces": interfaces,
        "name": name,
    }
    if strategy is not None:
        meta_attrs["globalid_strategy"] = strategy
    node_type = type(name, (DjangoType,), {"Meta": type("Meta", (), meta_attrs)})
    assert issubclass(node_type, DjangoType)
    return node_type


def _schema_with(
    field_name: str,
    annotation: object,
    field_value: object,
    *,
    extra_types: Iterable[type] = (),
) -> strawberry.Schema:
    """Build an in-process schema exposing one root field built by a factory.

    ``extra_types`` feeds ``strawberry.Schema(types=[...])`` - the documented
    engine constraint for a schema whose only root field is interface-typed
    (concrete types are otherwise unreachable from the schema walk).
    """
    namespace = {"__annotations__": {field_name: annotation}, field_name: field_value}
    query_cls = strawberry.type(type("Query", (), namespace))
    finalize_django_types()
    return strawberry.Schema(query=query_cls, config=strawberry_config(), types=list(extra_types))


_CATEGORY_QUERY = "query ($id: ID!) { category(id: $id) { name } }"
_CATEGORIES_QUERY = "query ($ids: [ID!]!) { categories(ids: $ids) { name } }"


@pytest.mark.parametrize("factory", [DjangoNodeField, DjangoNodesField], ids=["node", "nodes"])
def test_an_unannotated_assignment_fails_the_schema_build_on_the_resolver_any(
    factory: Callable[[], object],
) -> None:
    """An assignment with no annotation takes the resolver's ``Any`` return and fails the build.

    Strawberry falls back to the resolver's return annotation when the assignment
    carries none; the factories' resolvers carry ``Any`` there, so graphql-core
    refuses the field with the message the module docstring documents as
    "annotate the assignment", rather than building a field of some other type.
    """
    category_node = _make_node_type("CategoryNode")
    query_cls = strawberry.type(type("Query", (), {"node": factory()}))
    finalize_django_types()
    with pytest.raises(TypeError, match=re.escape("Unexpected type 'typing.Any'")):
        strawberry.Schema(query=query_cls, config=strawberry_config(), types=[category_node])


# ---------------------------------------------------------------------------
# Type-name strategy + multi-type-over-one-model routing
# ---------------------------------------------------------------------------


def _make_multi_type_category_nodes() -> tuple[type, type]:
    """Two Relay-Node types over ``Category`` - the multi-type-over-one-model shape.

    Both carry ``globalid_strategy = "type"`` so each type is addressable by
    its own GraphQL-type-name gid (under the default model-label strategy a
    secondary type's gid would decode to the primary).
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            primary = True
            globalid_strategy = "type"

    class CategoryAdminNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = "type"

    return CategoryNode, CategoryAdminNode


@pytest.mark.django_db
def test_node_type_hint_does_not_poison_reused_model_instance() -> None:
    """Stamp a distinct copy while leaving the original ORM row's private cast absent."""
    services.seed_data(1)
    row = Category.objects.order_by("pk").first()
    assert row is not None
    _primary, secondary = _make_multi_type_category_nodes()

    stamped = _stamp_node_type(secondary, row)

    assert stamped is not row
    assert read_attr(stamped, TYPE_CAST_ATTRIBUTE) is secondary
    assert not hasattr(row, TYPE_CAST_ATTRIBUTE)


@pytest.mark.django_db
def test_node_type_hint_from_a_lazy_resolve_node_return_does_not_poison_the_row() -> None:
    """Unwrap a lazy proxy before copying, leaving its original row's private cast absent."""
    services.seed_data(1)
    row = Category.objects.order_by("pk").first()
    assert row is not None
    _primary, secondary = _make_multi_type_category_nodes()
    proxy = SimpleLazyObject(lambda: row)

    stamped = _stamp_node_type(secondary, proxy)

    assert stamped is not row
    assert read_attr(stamped, TYPE_CAST_ATTRIBUTE) is secondary
    assert TYPE_CAST_ATTRIBUTE not in vars(row)


def test_stamp_node_type_passes_through_none_and_unstampable_objects() -> None:
    """``None`` rides through; an attribute-rejecting return stays unstamped.

    ``None`` is the hidden/missing/uncoercible -> ``null`` contract; a bare
    ``object()`` stands in for a consumer ``resolve_node(s)`` override
    returning a ``__slots__``-style object that rejects attribute writes -
    the stamp is best-effort and such returns keep the isinstance fallback.
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    assert implements_relay_node(CategoryNode)
    assert _stamp_node_type(CategoryNode, None) is None
    unstampable = object()
    # basedpyright: a plain stand-in class carrying no definition, which the code under test
    # reads through getattr; _stamp_node_type types the parameter as type[_RelayDjangoType]
    assert _stamp_node_type(object, unstampable) is unstampable  # pyright: ignore[reportArgumentType]
    assert not hasattr(unstampable, TYPE_CAST_ATTRIBUTE)


# ---------------------------------------------------------------------------
# Custom relay.NodeID[...] id attribute (coercion must key on resolve_id_attr())
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_decode_model_global_id_resolves_custom_node_id_to_real_pk() -> None:
    """Write-side decode maps a custom NodeID value to the REAL pk, not the attr value.

    ``decode_model_global_id`` feeds every WRITE consumer (update/delete
    ``locate_instance``'s ``get(pk=...)``, the relation ``pk__in`` visibility query,
    and FK / M2M assignment), all of which treat ``result.pk`` as an actual primary
    key. For a consumer ``id: relay.NodeID[str]`` over the non-pk ``name`` column,
    the decoded value is the ``name`` string; handing that to a ``pk=`` lookup
    targets the wrong column. The value resolves to ``row.pk`` here.
    """
    services.seed_data(1)

    class CategoryNode(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

    assert registry.get(Category) is CategoryNode

    finalize_django_types()
    row = Category.objects.order_by("pk").first()
    assert row is not None
    result = decode_model_global_id(_gid("products.category", row.name), Category)
    assert result.status is GlobalIDDecode.OK
    # The REAL integer pk, NOT the ``name`` string the GlobalID carried.
    assert result.pk == saved_pk(row)
    assert result.pk != row.name


@pytest.mark.django_db
def test_decode_model_global_id_custom_node_id_no_row_is_uncoercible() -> None:
    """A custom NodeID value matching no row decodes as UNCOERCIBLE_PK, never a phantom pk.

    A ``name`` that exists on no row resolves to ``None`` in ``_resolve_real_pk``,
    which the caller maps to the same not-found surface a hidden row yields (no
    existence leak) - rather than passing the literal through as a fake pk.
    """
    services.seed_data(1)

    class CategoryNode(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

    assert registry.get(Category) is CategoryNode

    finalize_django_types()
    result = decode_model_global_id(_gid("products.category", "no-such-category-name"), Category)
    assert result.status is GlobalIDDecode.UNCOERCIBLE_PK
    assert result.pk is None


@pytest.mark.django_db
def test_decode_model_global_id_passes_raw_value_for_non_field_node_id() -> None:
    """A NodeID over a non-concrete attr has no column to resolve, so the value passes through.

    ``_resolve_real_pk`` mirrors ``_coerce_pk_or_none``'s ``FieldDoesNotExist``
    fall-through: with no concrete column to map to a pk, the coerced literal is
    returned unchanged rather than crashing on ``get_field`` (a downstream
    ``pk=<literal>`` lookup then fails as not-found).
    """
    services.seed_data(1)

    class SlugNode(DjangoType):
        slug: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "SlugNode"

    assert registry.get(Category) is SlugNode

    finalize_django_types()
    result = decode_model_global_id(_gid("products.category", "abc-123"), Category)
    assert result.status is GlobalIDDecode.OK
    assert result.pk == "abc-123"


def test_coerce_pk_or_none_passes_raw_string_for_non_field_node_id() -> None:
    """A NodeID over a non-model-field attr skips coercion and passes the raw string.

    ``_coerce_pk_or_none`` keys on ``resolve_id_attr()``; when that names no
    concrete model field (``FieldDoesNotExist``) it cannot coerce, so it
    returns the literal unchanged rather than crashing.
    """

    class SlugNode(DjangoType):
        slug: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "SlugNode"

    finalize_django_types()
    assert implements_relay_node(SlugNode)
    assert _coerce_pk_or_none(SlugNode, "abc-123", alias=DEFAULT_DB_ALIAS) == "abc-123"


@pytest.mark.django_db
def test_batch_coercion_computes_id_slot_once_per_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """The id slot is computed once per distinct type per call path.

    ``_node_id_slot`` is a per-type constant threaded through the batch coerce
    loop and the write decode halves. A 4-id same-type batch computes it twice,
    never per id: once in the field's gate, and once in the default
    ``resolve_nodes``, which receives the decoded ``node_id`` strings (Strawberry's
    contract) and coerces them itself. One write decode computes it once.
    """
    services.seed_data(4)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with(
        "categories",
        list[category_node | None],
        DjangoNodesField(category_node),
    )
    rows = list(Category.objects.order_by("pk")[:4])
    gids = [_gid("products.category", row.pk) for row in rows]

    calls: list[type] = []
    real_slot = relay_module._node_id_slot

    def counting_slot(resolved_type: type) -> object:
        calls.append(resolved_type)
        return real_slot(resolved_type)

    monkeypatch.setattr(relay_module, "_node_id_slot", counting_slot)
    result = schema.execute_sync(_CATEGORIES_QUERY, variable_values={"ids": gids})
    assert result.errors is None
    assert len(calls) == 2
    calls.clear()
    decoded = decode_model_global_id(gids[0], Category)
    assert decoded.status is GlobalIDDecode.OK
    assert len(calls) == 1


# ---------------------------------------------------------------------------
# Private value-based reorder and required-node exception causes
# ---------------------------------------------------------------------------


def _strawberry_node_schema() -> strawberry.Schema:
    """A schema whose root fields are Strawberry's own ``relay.node()`` over the defaults."""

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"
            globalid_strategy = "type"

    @strawberry.type
    class Query:
        node: relay.Node | None = relay.node()
        required_node: relay.Node = relay.node()
        nodes: list[relay.Node | None] = relay.node()

    finalize_django_types()
    return strawberry.Schema(query=Query, config=strawberry_config(), types=[CategoryNode])


@pytest.mark.django_db
def test_required_default_resolver_keeps_the_uncoercible_id_cause() -> None:
    """An upstream required Node field preserves the model's original DoesNotExist cause."""
    services.seed_data(1)
    schema = _strawberry_node_schema()

    required = schema.execute_sync(
        "query ($bad: ID!) { requiredNode(id: $bad) { __typename } }",
        variable_values={"bad": _gid("CategoryNode", "abc")},
    )

    assert required.errors is not None
    assert len(required.errors) == 1
    assert isinstance(required.errors[0].original_error, Category.DoesNotExist)
    assert "no row matching pk='abc'" in str(required.errors[0])


# ---------------------------------------------------------------------------
# Construction-time guards + finalize-time ledger check
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("factory", [DjangoNodeField, DjangoNodesField])
def test_node_field_target_guards(factory: Callable[..., object]) -> None:
    """The typed form runs the four shared guards plus the Relay-Node-shaped fifth."""
    with pytest.raises(
        ConfigurationError,
        match=rf"{factory.__name__} requires a DjangoType class",
    ):
        factory(42)

    class NotADjangoType:
        pass

    with pytest.raises(
        ConfigurationError,
        match=rf"{factory.__name__} requires a DjangoType subclass",
    ):
        factory(NotADjangoType)

    class NoMetaType(DjangoType):
        pass

    with pytest.raises(ConfigurationError, match="is not a registered DjangoType"):
        factory(NoMetaType)

    class PlainCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    with pytest.raises(
        ConfigurationError,
        match=rf"{factory.__name__} requires a Relay-Node-shaped DjangoType target",
    ):
        factory(PlainCategoryType)


@pytest.mark.parametrize("factory", [DjangoNodeField, DjangoNodesField])
@pytest.mark.parametrize("bare", ["@deprecated", b"@deprecated"])
def test_node_field_rejects_bare_string_directives(
    factory: Callable[..., object],
    bare: str | bytes,
) -> None:
    """A bare str / bytes ``directives`` is rejected at the construction line.

    Both root Relay factories forwarded ``directives`` to ``strawberry.field()``
    unvalidated, so a bare string was iterated character-wise into a field whose
    "directives" are chars without ``__strawberry_directive__`` (raw
    AttributeError at schema build) and a bytes built silently then crashed SDL
    render. The containment is
    ``utils/directives.py::validated_field_directives``.
    """
    with pytest.raises(
        ConfigurationError,
        match=rf"{factory.__name__} directives must be a sequence of directive instances",
    ):
        factory(directives=bare)


@pytest.mark.parametrize("factory", [DjangoNodeField, DjangoNodesField])
def test_node_field_passes_real_directive_instances_through(
    factory: Callable[..., object],
) -> None:
    """Positive control: a genuine directive instance still constructs and declares."""

    @schema_directive(locations=[DirectiveLocation.FIELD_DEFINITION], name="probeTag")
    class ProbeTag:
        marker: str = "probe"

    assert factory(directives=(ProbeTag(),)) is not None
    assert _node_fields_declared == [factory.__name__]


def test_node_field_without_node_types_raises_at_finalize() -> None:
    """The ledger check fires with the documented message; ``registry.clear()`` resets it."""

    class PlainCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is PlainCategoryType

    DjangoNodeField()  # bare declaration appends the ledger
    with pytest.raises(
        ConfigurationError,
        match=r"node lookup configured but no Node types registered\.",
    ):
        finalize_django_types()

    # The ledger-reset half: clear() co-clears the ledger, and a Node-shaped
    # registration with a fresh declaration finalizes cleanly.
    registry.clear()
    _make_node_type("CategoryNode")
    DjangoNodesField()
    finalize_django_types()


# ---------------------------------------------------------------------------
# DjangoSchema construction check of a typed field's annotation
# ---------------------------------------------------------------------------


@strawberry.interface
class Labelled:
    """A narrower interface than ``relay.Node`` that ``CatNode`` implements."""

    name: str


def _node_query(
    field: str,
    annotation: object,
    value: object,
    *,
    nested: bool = False,
) -> type[object]:
    """A ``Query`` holding ``field``, or a ``Query.viewer: Viewer`` whose ``Viewer`` holds it."""
    namespace: dict[str, object] = {"__annotations__": {field: annotation}, field: value}
    if not nested:
        return strawberry.type(type("Query", (), namespace))
    viewer = strawberry.type(type("Viewer", (), namespace))
    root: dict[str, object] = {"__annotations__": {"viewer": viewer | None}, "viewer": None}
    return strawberry.type(
        type("Query", (), root),
    )


def _optional(field: str, held: type | UnionType) -> object:
    """``held | None`` for ``node``, ``list[held | None]`` for ``nodes``."""
    optional = held | None
    return optional if field == "node" else list[optional]


def _typed(field: str, target: type[DjangoType]) -> object:
    """``DjangoNodeField(target)`` or ``DjangoNodesField(target)``."""
    return DjangoNodeField(target) if field == "node" else DjangoNodesField(target)


_FACTORY = {"node": "DjangoNodeField", "nodes": "DjangoNodesField"}


@pytest.mark.parametrize("nested", [False, True], ids=["root", "nested"])
@pytest.mark.parametrize("field", ["node", "nodes"])
def test_djangoschema_refuses_a_typed_field_annotated_with_a_type_that_cannot_hold_its_target(
    field: str,
    *,
    nested: bool,
) -> None:
    """``DjangoNodeField(CatNode)`` annotated ``ItemNode`` is refused naming the field, at any depth."""
    cat = _make_node_type("CatNode")
    item = _make_node_type("ItemNode", model=Item)
    query = _node_query(field, _optional(field, item), _typed(field, cat), nested=nested)
    finalize_django_types()
    owner = "Viewer" if nested else "Query"
    message = (
        f"{owner}.{field}: {_FACTORY[field]}(CatNode) returns ItemNode, which cannot return a "
        "CatNode row; annotate the field with CatNode, or an interface or union CatNode "
        "belongs to."
    )
    with pytest.raises(ConfigurationError, match=f"^{re.escape(message)}$"):
        DjangoSchema(query=query, config=strawberry_config(), types=[cat])


@pytest.mark.parametrize("field", ["node", "nodes"])
def test_djangoschema_refuses_a_typed_field_whose_target_it_does_not_publish(field: str) -> None:
    """A ``relay.Node`` annotation does not publish the target, so the typed field is refused."""
    cat = _make_node_type("CatNode")
    item = _make_node_type("ItemNode", model=Item)
    query = _node_query(field, _optional(field, relay.Node), _typed(field, cat))
    finalize_django_types()
    message = (
        f"Query.{field}: {_FACTORY[field]}(CatNode) targets a type this schema does not "
        "publish; reach it from a root or relation field, or list it in the schema's types=."
    )
    with pytest.raises(ConfigurationError, match=f"^{re.escape(message)}$"):
        DjangoSchema(query=query, config=strawberry_config(), types=[item])


@pytest.mark.parametrize(
    "annotation",
    [
        "node",
        "union",
        "target",
        "interface",
    ],
)
@pytest.mark.parametrize("field", ["node", "nodes"])
def test_djangoschema_builds_typed_fields_annotated_with_a_holding_type(
    field: str,
    annotation: str,
) -> None:
    """``relay.Node``, a union holding the target, the target and its narrower interface build."""
    cat = _make_node_type("CatNode", interfaces=(relay.Node, Labelled))
    item = _make_node_type("ItemNode", model=Item)
    held = {
        "node": relay.Node,
        "union": cat | item,
        "target": cat,
        "interface": Labelled,
    }
    query = _node_query(field, _optional(field, held[annotation]), _typed(field, cat))
    finalize_django_types()
    schema = DjangoSchema(query=query, config=strawberry_config(), types=[cat, item])
    assert schema.get_type_by_name("CatNode") is not None


@pytest.mark.parametrize("annotation", ["union", "interface"])
@pytest.mark.parametrize("field", ["node", "nodes"])
def test_djangoschema_builds_bare_fields_annotated_with_a_restriction(
    field: str,
    annotation: str,
) -> None:
    """A bare field restricted to a union or narrower interface is no configuration error."""
    cat = _make_node_type("CatNode", interfaces=(relay.Node, Labelled))
    item = _make_node_type("ItemNode", model=Item)
    held = {"union": cat | item, "interface": Labelled}
    bare = DjangoNodeField() if field == "node" else DjangoNodesField()
    query = _node_query(field, _optional(field, held[annotation]), bare)
    finalize_django_types()
    schema = DjangoSchema(query=query, config=strawberry_config(), types=[cat, item])
    assert schema.get_type_by_name("CatNode") is not None


@strawberry.type
class Plain:
    """A Strawberry object type no ``DjangoType`` declares, so it carries no ``is_type_of``."""

    name: str


@pytest.mark.django_db
def test_a_plain_object_annotation_holds_no_relay_type() -> None:
    """An object return holds only itself, though the engine would complete any row as it.

    A bare ``node: Plain | None`` refuses a ``CatNode`` id with no statement rather than
    serving the row with ``__typename: "Plain"``; ``DjangoSchema`` refuses
    ``DjangoNodeField(CatNode)`` annotated ``Plain`` at construction.
    """
    services.seed_data(1)
    row = Category.objects.order_by("pk").first()
    assert row is not None
    cat = _make_node_type("CatNode")
    bare = _node_query("node", Plain | None, DjangoNodeField())
    typed = _node_query("node", Plain | None, DjangoNodeField(cat))
    finalize_django_types()
    schema = strawberry.Schema(query=bare, config=strawberry_config(), types=[cat])
    with CaptureQueriesContext(connection) as captured:
        result = schema.execute_sync(
            "query ($id: ID!) { node(id: $id) { __typename } }",
            variable_values={"id": global_id_for(cat, saved_pk(row))},
        )
    assert result.data == {"node": None}
    assert result.errors is not None
    refusal = (
        "Invalid GlobalID: model label 'products.category' decodes to a Relay-Node "
        "DjangoType this field does not return"
    )
    assert [(error.message, error.extensions) for error in result.errors] == [
        (refusal, {"code": "GLOBALID_INVALID"}),
    ]
    assert captured.captured_queries == []
    message = (
        "Query.node: DjangoNodeField(CatNode) returns Plain, which cannot return a CatNode "
        "row; annotate the field with CatNode, or an interface or union CatNode belongs to."
    )
    with pytest.raises(ConfigurationError, match=f"^{re.escape(message)}$"):
        DjangoSchema(query=typed, config=strawberry_config(), types=[cat])


@pytest.mark.parametrize("field", ["node", "nodes"])
def test_strawberry_schema_builds_a_typed_field_that_djangoschema_refuses(field: str) -> None:
    """The construction check is ``DjangoSchema``'s; a plain ``strawberry.Schema`` builds the field."""
    cat = _make_node_type("CatNode")
    item = _make_node_type("ItemNode", model=Item)
    query = _node_query(field, _optional(field, item), _typed(field, cat))
    finalize_django_types()
    schema = strawberry.Schema(query=query, config=strawberry_config(), types=[cat])
    assert schema.get_type_by_name("CatNode") is not None
    with pytest.raises(
        ConfigurationError,
        match=r"returns ItemNode, which cannot return a CatNode row",
    ):
        DjangoSchema(query=query, config=strawberry_config(), types=[cat])


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["node", "nodes"], ids=["node", "nodes"])
def test_a_type_model_secondary_type_name_id_runs_its_own_hook_not_the_primarys(
    field: str,
) -> None:
    """Under ``type+model`` a type-name id reads its named type's hook; the emitted id the primary's.

    The primary hides one row; the hookless secondary declares none. The
    secondary's type-name id of that row decodes to the secondary and serves
    it, while the model-label id the secondary emits decodes to the primary and
    answers ``null``.
    """
    services.seed_data(1)
    hidden = Category.objects.order_by("pk").first()
    assert hidden is not None
    hidden_pk = saved_pk(hidden)

    class HidingCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            primary = True
            globalid_strategy = "type+model"

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Category], info: object) -> QuerySet[Category]:
            return queryset.exclude(pk=hidden_pk)

    class HooklessCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = "type+model"

    if field == "node":
        schema = _schema_with(
            "node",
            relay.Node | None,
            DjangoNodeField(),
            extra_types=(HidingCategoryNode, HooklessCategoryNode),
        )
    else:
        schema = _schema_with(
            "nodes",
            list[relay.Node | None],
            DjangoNodesField(),
            extra_types=(HidingCategoryNode, HooklessCategoryNode),
        )
    emitted = global_id_for(HooklessCategoryNode, hidden_pk)
    assert emitted == _gid("products.category", hidden_pk)
    ids = (_gid("HooklessCategoryNode", hidden_pk), emitted)
    selection = (
        "__typename ... on HooklessCategoryNode { name } ... on HidingCategoryNode { name }"
    )
    if field == "node":
        document = (
            f'{{ named: node(id: "{ids[0]}") {{ {selection} }} '
            f'emitted: node(id: "{ids[1]}") {{ {selection} }} }}'
        )
    else:
        document = f'{{ nodes(ids: ["{ids[0]}", "{ids[1]}"]) {{ {selection} }} }}'
    result = schema.execute_sync(document)
    assert result.errors is None, result.errors
    served = {"__typename": "HooklessCategoryNode", "name": hidden.name}
    if field == "node":
        assert result.data == {"named": served, "emitted": None}
    else:
        assert result.data == {"nodes": [served, None]}


# ---------------------------------------------------------------------------
# Consumer resolve_nodes override + SyncMisuseError pass-through
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sync_refetch_async_resolve_node_error_is_a_sync_misuse_error() -> None:
    """The error a sync refetch raises for an async ``resolve_node`` is a ``SyncMisuseError``.

    The message naming the override, its path and the null row are pinned live by
    ``examples/fakeshop/test_query/test_node_refetch_api.py::test_sync_refetch_refuses_an_async_consumer_resolve_node``;
    this row keeps the exception class the wire envelope does not carry.
    """
    services.seed_data(1)

    class AsyncCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        async def resolve_node(
            cls,
            node_id: str,
            *,
            info: strawberry.Info,
            required: bool = False,
        ) -> None:
            del cls, node_id, info, required

    schema = _schema_with(
        "category",
        AsyncCategoryNode | None,
        DjangoNodeField(AsyncCategoryNode),
    )
    row = Category.objects.order_by("pk").first()
    assert row is not None
    result = schema.execute_sync(
        _CATEGORY_QUERY,
        variable_values={"id": _gid("products.category", saved_pk(row))},
    )
    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)


@pytest.mark.django_db(transaction=True)
async def test_node_sync_operation_inside_an_event_loop_never_calls_async_resolve_node() -> None:
    """``execute_sync`` under a running loop refuses before the override is called.

    Masking is off because the subject is the typed error itself.
    """
    await sync_to_async(services.seed_data)(1)
    calls: list[str] = []

    async def _no_row() -> None:
        return None

    class AsyncCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        def resolve_node(
            cls,
            node_id: str,
            *,
            info: strawberry.Info,
            required: bool = False,
        ) -> Awaitable[None]:
            del cls, info, required
            calls.append(node_id)
            return _no_row()

    @strawberry.type
    class Query:
        category: AsyncCategoryNode | None = DjangoNodeField(AsyncCategoryNode)

    await sync_to_async(finalize_django_types)()
    schema = DjangoSchema(query=Query, error_policy=ErrorPolicy(enabled=False))
    row = await Category.objects.order_by("pk").afirst()
    assert row is not None

    result = schema.execute_sync(
        _CATEGORY_QUERY,
        variable_values={"id": _gid("products.category", saved_pk(row))},
    )

    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "await schema.execute" in str(result.errors[0])
    assert result.data == {"category": None}
    assert calls == []


@pytest.mark.django_db
def test_sync_batch_refetch_async_resolve_nodes_error_is_a_sync_misuse_error() -> None:
    """The error a sync batch refetch raises for an async ``resolve_nodes`` is a ``SyncMisuseError``.

    The message naming the override, its path and the null ``data`` are pinned live by
    ``examples/fakeshop/test_query/test_node_refetch_api.py::test_sync_batch_refetch_refuses_an_async_consumer_resolve_nodes``;
    this row keeps the exception class the wire envelope does not carry.
    """
    services.seed_data(1)

    class AsyncCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        async def resolve_nodes(
            cls,
            *,
            info: strawberry.Info,
            node_ids: Iterable[str],
            required: bool = False,
        ) -> list[None]:
            del cls, info, required
            return [None for _ in node_ids]

    schema = _schema_with(
        "categories",
        list[AsyncCategoryNode | None],
        DjangoNodesField(AsyncCategoryNode),
    )
    row = Category.objects.order_by("pk").first()
    assert row is not None
    result = schema.execute_sync(
        _CATEGORIES_QUERY,
        variable_values={"ids": [_gid("products.category", saved_pk(row))]},
    )
    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)


@pytest.mark.django_db
def test_sync_refetch_async_get_queryset_error_is_a_sync_misuse_error() -> None:
    """The error an async ``get_queryset`` raises under a sync refetch is a ``SyncMisuseError``.

    The message, the null row and the absent ``GLOBALID_INVALID`` code (spec-032
    Decision 5: the id-error conversion is scoped to the decode call only) are
    pinned live by
    ``examples/fakeshop/test_query/test_node_refetch_api.py::test_sync_refetch_reports_an_async_get_queryset_as_misuse_not_an_invalid_id``;
    this row keeps the exception class the wire envelope does not carry.
    """
    services.seed_data(1)

    async def _async_get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[Category],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[Category]:
        return queryset

    async_category_node = make_django_type(
        "AsyncCategoryNode",
        Category,
        ("id", "name"),
        meta_extra={"name": "CategoryNode"},
        namespace_extra={"get_queryset": classmethod(_async_get_queryset)},
    )
    schema = _schema_with(
        "category",
        async_category_node | None,
        DjangoNodeField(async_category_node),
    )
    row = Category.objects.order_by("pk").first()
    assert row is not None
    result = schema.execute_sync(
        _CATEGORY_QUERY,
        variable_values={"id": _gid("products.category", saved_pk(row))},
    )
    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)


@pytest.mark.django_db
def test_sync_node_path_builds_no_owner_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sync node(s) success paths skip the error-only owner-name build.

    ``reject_async_in_sync_context`` reads ``owner`` only on the raise path, so
    both sync resolvers guard the ``truth.name`` call with ``isawaitable``: one
    sync single refetch plus one sync batch refetch build zero owner names. The
    spy is scoped to this module's own ``truth`` reference (other subsystems
    name eagerly on their own paths), and the ``SyncMisuseError`` rows still pin
    the raise path.
    """
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode")
    single_schema = _schema_with(
        "category",
        category_node | None,
        DjangoNodeField(category_node),
    )
    batch_schema = _schema_with(
        "categories",
        list[category_node | None],
        DjangoNodesField(category_node),
    )
    row = Category.objects.order_by("pk").first()
    assert row is not None
    gid = _gid("products.category", row.pk)

    calls: list[object] = []

    class _CountingTruth:
        """Delegate every truth read while counting ``name`` calls."""

        def __getattr__(self, attr: str) -> object:
            return read_attr(real_truth, attr)

        def name(self, obj: object) -> str:
            calls.append(obj)
            return real_truth.name(obj)

    monkeypatch.setattr(relay_module, "truth", _CountingTruth())
    single = single_schema.execute_sync(_CATEGORY_QUERY, variable_values={"id": gid})
    assert single.errors is None
    batch = batch_schema.execute_sync(_CATEGORIES_QUERY, variable_values={"ids": [gid, gid]})
    assert batch.errors is None
    assert calls == []


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


def test_public_exports() -> None:
    """``DjangoNodeField`` / ``DjangoNodesField`` are importable package-root exports."""
    assert django_strawberry_framework.DjangoNodeField is DjangoNodeField
    assert django_strawberry_framework.DjangoNodesField is DjangoNodesField
    assert "DjangoNodeField" in django_strawberry_framework.__all__
    assert "DjangoNodesField" in django_strawberry_framework.__all__
