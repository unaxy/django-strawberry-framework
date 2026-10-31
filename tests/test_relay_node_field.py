"""Package Relay refetch construction, identity, cache and exception-class contracts.

Consumer refetch over HTTP lives in
``examples/fakeshop/test_query/test_library_api.py`` (shipped model-label
refetch) and ``examples/fakeshop/test_query/test_node_refetch_api.py`` (consumer
type-name routing, shared rows and lazy proxies, custom NodeID columns,
alternate primary-key spellings and override return contracts).

This module owns construction/finalize refusal, class cache and private decoder
status, stamp identity, original_error exception classes, helper return shapes
and public-export identity. The private stamping tests inspect the original ORM
row's cast attribute directly; the required-node test inspects the original
model exception hidden by the GraphQL error envelope. It also keeps the refetch
rows over key shapes no fakeshop model carries: a NodeID over a queryset
annotation, a test-local comma-list key whose value is unhashable, a decimal key
SQLite stores as a float, and naive datetime keys read in the default time zone
(including a wall clock the zone repeats or skips).
"""

import contextlib
import datetime
import re
import zoneinfo
from collections.abc import Awaitable, Callable, Generator, Iterable, Iterator
from decimal import Decimal
from typing import TYPE_CHECKING

import django
import pytest
import strawberry
from apps.products import services
from apps.products.models import Category
from asgiref.sync import sync_to_async
from django.db import DEFAULT_DB_ALIAS, connection, models
from django.db.models import Model, QuerySet
from django.test import override_settings
from django.utils.functional import SimpleLazyObject
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
from django_strawberry_framework.types.relay import (
    SyncMisuseError,
    implements_relay_node,
)
from django_strawberry_framework.utils import truth as real_truth
from django_strawberry_framework.utils._narrowing import is_exact_list, read_attr
from tests._idioms import (
    saved_pk,
)

if TYPE_CHECKING:
    from typing import TypeAlias

    from django.db.models.expressions import Combinable

    # The field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them.
    _AwareStamp: TypeAlias = models.DateTimeField[
        str | datetime.datetime | datetime.date | Combinable,
        datetime.datetime,
    ]


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
) -> type[DjangoType]:
    """Build a Relay-Node-shaped ``DjangoType`` over ``model`` for a test."""
    meta_attrs = {
        "model": model,
        "fields": ("id", "name"),
        "interfaces": (relay.Node,),
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
def test_refetch_finds_a_row_by_a_node_id_over_a_queryset_annotation() -> None:
    """A NodeID naming a ``get_queryset`` annotation, no model field, refetches its row.

    The slot has no column (``_node_id_slot`` answers ``None``), so the raw literal
    filters the annotated queryset and the reorder keys the row's annotation value and
    the requested id by ``str`` (``utils/querysets.py::identity_key``): ``node`` and
    ``nodes`` answer the row, and a literal no row holds is ``null``.
    """
    services.seed_data(1)

    class SlugNode(DjangoType):
        slug: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "SlugNode"

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Category],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Category]:
            return queryset.annotate(slug=models.F("name"))

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        nodes: list[relay.Node | None] = DjangoNodesField()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, config=strawberry_config(), types=[SlugNode])
    row = Category.objects.order_by("pk").first()
    assert row is not None
    found = _gid("products.category", row.name)
    missing = _gid("products.category", "no-such-category-name")
    result = schema.execute_sync(
        "query ($id: ID!, $ids: [ID!]!) {"
        " node(id: $id) { ... on SlugNode { id name } }"
        " nodes(ids: $ids) { ... on SlugNode { name } } }",
        variable_values={"id": found, "ids": [missing, found]},
    )
    assert result.errors is None, result.errors
    assert result.data == {
        "node": {"id": found, "name": row.name},
        "nodes": [None, {"name": row.name}],
    }


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


class _SpelledDecimalKeyed(Model):
    """A Relay row keyed by a ``DecimalField`` without ``max_digits``."""

    code: "models.DecimalField[str | float | Decimal | Combinable, Decimal]" = models.DecimalField(
        primary_key=True,
        max_digits=None,
        decimal_places=None,
    )
    name: "models.TextField[str | Combinable, str]" = models.TextField()

    class Meta:
        app_label = "products"
        managed = False
        db_table = "relay_spelled_decimal_keyed"


class _SpelledStampKeyed(Model):
    """A Relay row keyed by an aware ``DateTimeField``."""

    stamp: "_AwareStamp" = models.DateTimeField(primary_key=True)
    name: "models.TextField[str | Combinable, str]" = models.TextField()

    class Meta:
        app_label = "products"
        managed = False
        db_table = "relay_spelled_stamp_keyed"


# The stubs make ``TextField`` generic; the runtime class takes no subscript.
if TYPE_CHECKING:
    _CommaListBase = models.TextField[str | list[str] | Combinable, list[str]]
else:
    _CommaListBase = models.TextField


class _CommaListField(_CommaListBase):
    """A consumer column holding a list of words, stored as their comma-joined text."""

    @override
    def to_python(self, value: object) -> object:
        return value.split(",") if isinstance(value, str) else value

    def from_db_value(self, value: object, *_context: object) -> object:
        """Read the stored text back as the list it holds; Django passes two more arguments."""
        return self.to_python(value)

    @override
    def get_prep_value(self, value: object) -> object:
        return ",".join(str(word) for word in value) if is_exact_list(value) else value


class _SpelledListKeyed(Model):
    """A Relay row keyed by a consumer column whose Python value is a list, never hashable."""

    code: "_CommaListField" = _CommaListField(primary_key=True)
    name: "models.TextField[str | Combinable, str]" = models.TextField()

    class Meta:
        app_label = "products"
        managed = False
        db_table = "relay_spelled_list_keyed"


@contextlib.contextmanager
def _spelled_key_table(model: type[Model], key: object) -> Generator[str, None, None]:
    """Create ``model``'s table holding one row keyed ``key``; yield its model-label prefix."""
    with connection.schema_editor() as editor:
        editor.create_model(model)
    try:
        _ = model._default_manager.create(pk=key, name="stored")
        yield f"products.{model._meta.model_name}"
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(model)


def _spelled_key_answer(
    model: type[Model],
    label: str,
    spelled: str,
    root: str,
) -> object:
    """Query the ``root`` refetch field over ``model`` with the id spelled ``spelled``."""
    return _spelled_key_answers(model, label, [spelled], root)[0]


def _spelled_key_answers(
    model: type[Model],
    label: str,
    spellings: Iterable[str],
    root: str,
) -> list[object]:
    """Query the ``root`` refetch field over ``model`` once per id spelling in ``spellings``."""
    meta = {
        "model": model,
        "fields": ("name",),
        "interfaces": (relay.Node,),
        "name": "SpelledNode",
    }
    spelled_node = type("SpelledNode", (DjangoType,), {"Meta": type("Meta", (), meta)})

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        nodes: list[relay.Node | None] = DjangoNodesField()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, config=strawberry_config(), types=[spelled_node])
    selection = "node(id: $id)" if root == "node" else "nodes(ids: [$id])"
    answers: list[object] = []
    for spelled in spellings:
        result = schema.execute_sync(
            f"query ($id: ID!) {{ {selection} {{ ... on SpelledNode {{ name }} }} }}",
            variable_values={"id": _gid(label, spelled)},
        )
        assert result.errors is None, result.errors
        answers.append(result.data)
    return answers


_STORED_ANSWER = {"node": {"node": {"name": "stored"}}, "nodes": {"nodes": [{"name": "stored"}]}}
_MISSING_ANSWER = {"node": {"node": None}, "nodes": {"nodes": [None]}}
_REFETCH_ROOTS = pytest.mark.parametrize("root", ["node", "nodes"])


@pytest.mark.django_db(transaction=True)
@_REFETCH_ROOTS
def test_refetch_finds_a_row_whose_key_value_is_unhashable(root: str) -> None:
    """A key column whose Python value is a list keys the reorder by its ``str``.

    ``to_python`` turns the id and the row's key into lists, which cannot key the
    reorder's index (``utils/querysets.py::identity_key``), so both sides key by the
    list's ``str`` and ``node`` and ``nodes`` get the row instead of raising.
    """
    with _spelled_key_table(_SpelledListKeyed, ["ab", "cd"]) as label:
        answer = _spelled_key_answer(_SpelledListKeyed, label, "ab,cd", root)
    assert answer == _STORED_ANSWER[root]


@pytest.mark.skipif(
    connection.vendor != "sqlite",
    reason="SQLite stores such a decimal as a float",
)
@pytest.mark.skipif(
    django.VERSION < (6, 1),
    reason="Django below 6.1 cannot read back a DecimalField without decimal_places",
)
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "stored",
    [
        pytest.param(Decimal("1234567890.1234567"), id="non-integral-past-15-digits"),
        pytest.param(Decimal(123456789012345678901), id="integral-past-64-bits"),
    ],
)
@_REFETCH_ROOTS
def test_refetch_cannot_address_a_decimal_key_sqlite_stores_as_a_float(
    stored: Decimal,
    root: str,
) -> None:
    """On SQLite a decimal key past 15 significant digits is stored as a float.

    Django reads it back rounded to 15 digits, so neither the written value nor the
    rounded one the row reads back as (the value its emitted id carries) equals the
    stored float: both spellings answer null.
    """
    with _spelled_key_table(_SpelledDecimalKeyed, stored) as label:
        read_back = _SpelledDecimalKeyed.objects.get().code
        assert read_back != stored
        answers = _spelled_key_answers(
            _SpelledDecimalKeyed,
            label,
            [str(stored), str(read_back)],
            root,
        )
    assert answers == [_MISSING_ANSWER[root]] * 2


#: A non-UTC default time zone, so a naive id read in UTC would name another instant.
_NAIVE_ZONE = "America/New_York"


@override_settings(TIME_ZONE=_NAIVE_ZONE)
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("spelled", "answers"),
    [
        pytest.param("2024-01-01T08:00:00", _STORED_ANSWER, id="naive-iso-t"),
        pytest.param("2024-01-01 08:00:00", _STORED_ANSWER, id="naive-iso-space"),
        pytest.param("2024-01-01", _MISSING_ANSWER, id="date-only-is-midnight"),
        pytest.param("2024-01-01T13:00:00", _MISSING_ANSWER, id="naive-utc-wall-clock"),
    ],
)
@_REFETCH_ROOTS
def test_refetch_reads_a_naive_datetime_key_in_the_default_time_zone(
    spelled: str,
    answers: dict[str, object],
    root: str,
) -> None:
    """A naive datetime id names the instant Django's lookup binds: its wall clock in ``TIME_ZONE``.

    The id is made aware in the default zone without Django's naive-datetime warning, so
    ``node`` and ``nodes`` get the row stored at that instant; a date-only spelling is its
    midnight and the same wall clock read as UTC is another instant, so both answer null.
    """
    stored = datetime.datetime(2024, 1, 1, 8, tzinfo=zoneinfo.ZoneInfo(_NAIVE_ZONE))
    with _spelled_key_table(_SpelledStampKeyed, stored) as label:
        answer = _spelled_key_answer(_SpelledStampKeyed, label, spelled, root)
    assert answer == answers[root]


@override_settings(TIME_ZONE=_NAIVE_ZONE)
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("stored", "spelled"),
    [
        pytest.param(
            datetime.datetime(2024, 11, 3, 5, 30, tzinfo=datetime.timezone.utc),
            "2024-11-03T01:30:00",
            id="dst-fold",
        ),
        pytest.param(
            datetime.datetime(2024, 3, 10, 7, 30, tzinfo=datetime.timezone.utc),
            "2024-03-10T02:30:00",
            id="dst-gap",
        ),
    ],
)
@_REFETCH_ROOTS
def test_refetch_reads_a_naive_datetime_key_the_default_zone_repeats_or_skips(
    stored: datetime.datetime,
    spelled: str,
    root: str,
) -> None:
    """A naive id on a DST fold or gap wall clock names the instant Django's lookup binds.

    Django makes the wall clock aware at its first offset; the row it matches reads back
    in UTC, and the reorder keys both as that instant, so ``node`` and ``nodes`` get it.
    """
    with _spelled_key_table(_SpelledStampKeyed, stored) as label:
        answer = _spelled_key_answer(_SpelledStampKeyed, label, spelled, root)
    assert answer == _STORED_ANSWER[root]


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
# Consumer resolve_nodes override + SyncMisuseError pass-through
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_node_sync_with_async_consumer_resolve_node_raises_sync_misuse() -> None:
    """Sync node refetch rejects an async consumer ``resolve_node`` explicitly."""
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
    assert "resolve_node" in str(result.errors[0])
    assert result.data == {"category": None}


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
def test_nodes_sync_with_async_consumer_resolve_nodes_raises_sync_misuse() -> None:
    """Sync batch refetch rejects an async consumer ``resolve_nodes`` explicitly."""
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
    assert "resolve_nodes" in str(result.errors[0])
    assert result.data is None


@pytest.mark.django_db
def test_node_sync_async_get_queryset_raises_sync_misuse() -> None:
    """An async ``get_queryset`` under sync execution surfaces SyncMisuseError, NOT GLOBALID_INVALID.

    Discriminating (spec-032 Decision 5): ``SyncMisuseError`` IS-A
    ``ConfigurationError``, so a blanket catch-convert around the resolver
    body would mislabel this server misconfiguration a client id error; the
    boundary scopes the decode call only.
    """
    services.seed_data(1)

    class AsyncCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        @override
        # basedpyright: deliberately async on the sync path: the coroutine is the input the guard refuses
        async def get_queryset(  # pyright: ignore[reportIncompatibleMethodOverride]
            cls,
            queryset: QuerySet[Category],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Category]:
            return queryset

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
    assert (result.errors[0].extensions or {}).get("code") != "GLOBALID_INVALID"
    assert "Invalid GlobalID" not in str(result.errors[0])


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
