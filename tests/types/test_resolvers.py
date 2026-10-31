"""Relation resolver tests for FK-id elision, N+1 strictness, and multi-database routing.

Generated relation payloads, reverse-O2O custom visibility (planned and
unplanned), and unoptimized many-side query cost live in
``examples/fakeshop/test_query/test_products_visibility_api.py``
and ``examples/fakeshop/test_query/test_relations_async_api.py``. A nullable dangling
self-FK over HTTP lives in
``examples/fakeshop/test_query/test_scalars_api.py``
(``test_nullable_self_fk_dangling_parent_resolves_to_null_over_http``). This module
keeps direct ``_make_relation_resolver`` / ``_check_n1`` calls, consumer-exception propagation,
router mocks, ``resolver.__name__``, and the nullable ``DoesNotExist`` swallow a
planned JOIN never takes.

Ancestor-prefetch MTI payloads and SQL costs live in
``examples/fakeshop/test_query/test_mti_composite_relations_api.py``; the resolver exception
identities and private cache/plan observations remain here.
"""

import datetime
import inspect
import uuid
from collections.abc import Callable, Iterable, Iterator, Sized
from types import SimpleNamespace
from typing import TYPE_CHECKING, Literal, NoReturn
from unittest.mock import Mock

import pytest
from apps.library.models import Patron
from apps.products import services
from apps.products.models import Category, Item
from apps.scalars.models import ScalarSpecimen
from asgiref.sync import sync_to_async
from django.db import connection as db_connection
from django.db import models, router
from django.db.models import Model, QuerySet
from django.utils import timezone
from graphql import OperationType
from strawberry.types import Info
from typing_extensions import override

import django_strawberry_framework.types.resolvers as resolvers_mod
import django_strawberry_framework.types.resolvers as resolvers_module
from django_strawberry_framework import (
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError, OptimizerError
from django_strawberry_framework.optimizer._context import (
    DST_OPTIMIZER_FK_ID_ELISIONS,
    DST_OPTIMIZER_PLANNED,
    DST_OPTIMIZER_STRICTNESS,
    begin_execution_frame,
    end_execution_frame,
    publish_scoped_relations,
)
from django_strawberry_framework.optimizer._context import (
    begin_execution_frame as _begin_execution_frame,
)
from django_strawberry_framework.optimizer._context import (
    end_execution_frame as _end_execution_frame,
)
from django_strawberry_framework.optimizer._context import (
    publish_scoped_relations as _publish_scoped_relations,
)
from django_strawberry_framework.optimizer.field_meta import FieldMeta
from django_strawberry_framework.optimizer.plans import resolver_key, runtime_path_from_info
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.resolvers import (
    _FK_ELISION_UNSAFE,
    _attach_file_resolvers,
    _attach_relation_resolvers,
    _build_fk_id_stub,
    _check_n1,
    _fk_attname_is_deferred,
    _make_relation_resolver,
    _visible_related_object,
)
from django_strawberry_framework.utils._narrowing import is_awaitable, is_iterable, read_attr
from tests._catalog_data import categories_from_seed, items_from_seed
from tests._idioms import saved_pk
from tests._info import make_info, response_path, unread_info

if TYPE_CHECKING:
    from django_strawberry_framework.utils.typing import ModelField


def _parent_type(
    model: type[Model],
    name: str | None = None,
    fields: tuple[str, ...] = ("id",),
) -> type[DjangoType]:
    """Declare a real ``DjangoType`` over ``model``, the parent a relation resolver is built for.

    The autouse ``_isolate_registry`` fixture clears the registration at the next test.
    """
    meta = type("Meta", (), {"model": model, "fields": fields})
    return type(name or f"{model.__name__}Type", (DjangoType,), {"Meta": meta})


def _as_field(stand_in: object) -> "ModelField":
    """Hand a duck-typed relation field to a resolver builder that takes a Django field."""
    # basedpyright: a stand-in field carrying only the slots the code under test reads; the
    # relation resolver builders type the parameter as a Django field
    return stand_in  # pyright: ignore[reportReturnType]


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# Custom relation resolvers
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_make_relation_resolver_many_side_is_named_resolve_field() -> None:
    """Generated many-side resolver is named ``resolve_<field>`` and reads the relation's manager.

    Payload and SQL live in ``examples/fakeshop/test_query/test_products_visibility_api.py``.
    """
    services.seed_data(1)
    category = Category.objects.first()
    assert category is not None
    resolver = _make_relation_resolver(Category._meta.get_field("items"))
    assert resolver.__name__ == "resolve_items"
    rows = resolver(category, make_info())
    assert is_iterable(rows)
    assert list(rows) == list(category.items.all())


def test_make_relation_resolver_forward_is_named_resolve_field() -> None:
    """Generated forward-FK resolver is named ``resolve_<field>``.

    Payload and SQL live in ``examples/fakeshop/test_query/test_products_visibility_api.py``.
    """
    fake_field = SimpleNamespace(
        name="category",
        attname="category_id",
        many_to_many=False,
        one_to_many=False,
        one_to_one=False,
    )
    resolver = _make_relation_resolver(_as_field(fake_field))
    assert resolver.__name__ == "resolve_category"

    sentinel = object()
    fake_info = make_info()
    assert resolver(SimpleNamespace(category=sentinel), fake_info) is sentinel


def test_b2_forward_fk_id_elision_returns_stub_without_accessing_relation() -> None:
    """Forward resolver returns a target stub from ``<field>_id`` when elided."""
    ItemType = _parent_type(Item)

    class Root:
        category_id = 42

        @property
        def category(self) -> NoReturn:
            raise AssertionError("the relation resolver must not lazy-load the relation")

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_info = make_info(
        context=SimpleNamespace(dst_optimizer_fk_id_elisions={key}),
        field_name="category",
        path=response_path("allItems", 0, "category"),
    )

    root = Root()
    result = resolver(root, fake_info)
    assert isinstance(result, Category)
    assert saved_pk(result) == 42
    assert result._state.adding is False
    assert result._state.db == router.db_for_read(Category)


@pytest.mark.django_db
def test_fk_id_elision_stub_is_scoped_when_the_relation_was_not_planned() -> None:
    """An FK-id stub for a CUSTOM-visibility target is re-read through the hook.

    The walker refuses to elide a target whose type overrides ``get_queryset``
    (``optimizer/walker.py::_plan_select_relation``), but the resolver's own
    ``visibility_type`` comes from ``registry.get(related_model)`` while that gate
    reads the plan-time target type - a multi-type registry can disagree. The
    guard therefore stays, and it must fail CLOSED: an unscoped stub is resolved
    through the target hook, which drops a stub whose row the hook excludes.
    """
    services.seed_data(1)
    category = Category.objects.first()
    assert category is not None

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Category],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Category]:
            return queryset.none()

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    finalize_django_types()

    # Bound outside the class body: ``category`` is class-local there (the
    # property below), so the class body cannot read the enclosing name.
    elided_pk = saved_pk(category)

    class Root:
        category_id = elided_pk

        @property
        def category(self) -> NoReturn:
            raise AssertionError("the relation resolver must not lazy-load the relation")

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_info = make_info(
        context=SimpleNamespace(dst_optimizer_fk_id_elisions={key}),
        field_name="category",
        path=response_path("allItems", 0, "category"),
    )

    # No optimizer published this relation as planned, so the stub is rescoped -
    # and this target's hook hides every row.
    assert resolver(Root(), fake_info) is None

    # Published as planned: the stub is served as-is, no visibility re-read. The
    # execution that planned it published its elisions to its own frame, which is
    # where a managed read looks; the unmanaged read above has only the context.
    frame = _begin_execution_frame(
        {DST_OPTIMIZER_FK_ID_ELISIONS: {key}},
        nested=False,
    )
    try:
        _publish_scoped_relations({key})
        scoped = resolver(Root(), fake_info)
    finally:
        _end_execution_frame(frame)
    assert isinstance(scoped, Category)
    assert saved_pk(scoped) == saved_pk(category)


def test_b2_forward_fk_id_elision_uses_registered_field_meta_attname() -> None:
    """Resolver FK-id elision reads attname from registered FieldMeta."""
    # The real ``Item`` type registers its own ``FieldMeta`` for ``category``.
    ItemType = _parent_type(Item, fields=("id", "category"))
    field = SimpleNamespace(name="category", attname="wrong_id")
    resolver = _make_relation_resolver(_as_field(field), parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_info = make_info(
        context={"dst_optimizer_fk_id_elisions": {key}},
        field_name="category",
        path=response_path("allItems", 0, "category"),
    )

    class Root:
        category_id = 42

        @property
        def category(self) -> NoReturn:
            raise AssertionError("the relation resolver must not lazy-load the relation")

    result = resolver(Root(), fake_info)

    assert isinstance(result, Category)
    assert saved_pk(result) == 42


def test_b2_forward_fk_id_elision_returns_none_for_null_fk() -> None:
    """Nullable FK ids still resolve to ``None`` instead of a stub."""
    ItemType = _parent_type(Item, "ItemType")

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_root = SimpleNamespace(category_id=None)
    fake_info = make_info(
        context={"dst_optimizer_fk_id_elisions": {key}},
        field_name="category",
        path=response_path("allItems", 0, "category"),
    )

    assert resolver(fake_root, fake_info) is None


def test_b2_fk_id_stub_returns_none_without_related_model() -> None:
    """Direct unit: incomplete metadata cannot build an FK-id stub."""
    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        attname="category_id",
        related_model=None,
    )

    assert _build_fk_id_stub(SimpleNamespace(category_id=42), field_meta) is None


def test_b2_forward_fk_id_elision_does_not_leak_across_parent_types() -> None:
    """Elision for one parent type does not affect another type."""
    ItemType = _parent_type(Item, "ItemType")

    OtherType = _parent_type(Category, "OtherType")

    sentinel = object()
    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    wrong_key = resolver_key(OtherType, "category", ("allItems", "category"))
    fake_root = SimpleNamespace(category_id=42, category=sentinel)
    fake_info = make_info(
        context={"dst_optimizer_fk_id_elisions": {wrong_key}},
        field_name="category",
        path=response_path("allItems", 0, "category"),
    )

    assert resolver(fake_root, fake_info) is sentinel


def test_b2_forward_fk_id_elision_ignores_bare_field_name_key() -> None:
    """Elision requires the full branch-sensitive resolver key."""
    ItemType = _parent_type(Item, "ItemType")

    sentinel = object()
    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    fake_root = SimpleNamespace(category_id=42, category=sentinel)
    fake_info = make_info(
        context={"dst_optimizer_fk_id_elisions": {"category"}},
        field_name="category",
        path=response_path("allItems", 0, "category"),
    )

    assert resolver(fake_root, fake_info) is sentinel


def test_check_n1_ignores_bare_field_name_key() -> None:
    """Planned relations require the full branch-sensitive resolver key."""
    ItemType = _parent_type(Item, "ItemType")

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": {"category"}, "dst_optimizer_strictness": "raise"},
        field_name="category",
        path=response_path("allItems", 0, "category"),
    )

    with pytest.raises(OptimizerError, match="Unplanned N\\+1"):
        _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind=None)


def test_check_n1_returns_when_relation_is_already_loaded() -> None:
    """Unplanned-but-cached relations do not warn or raise."""
    ItemType = _parent_type(Item, "ItemType")

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=response_path("allItems", 0, "category"),
    )

    _check_n1(
        fake_info,
        SimpleNamespace(category="cached"),
        "category",
        ItemType,
        kind=None,
    )


def test_check_n1_warns_for_unplanned_lazy_load(caplog: pytest.LogCaptureFixture) -> None:
    """Warn strictness logs an unplanned lazy-load relation."""
    ItemType = _parent_type(Item, "ItemType")

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "warn"},
        path=response_path("allItems", 0, "category"),
    )

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    _check_n1(fake_info, SimpleNamespace(), "category", ItemType, kind=None)

    assert any("Potential N+1 on category" in r.message for r in caplog.records)


def test_check_n1_planned_absent_is_silent() -> None:
    """No planned sentinel on context -> optimizer is not engaged."""
    ItemType = _parent_type(Item, "ItemType")

    fake_info = SimpleNamespace(context={}, path=response_path("allItems", 0, "category"))
    # No exception, no log, no side effect - strictness is irrelevant when the
    # optimizer never set DST_OPTIMIZER_PLANNED.
    _check_n1(
        fake_info,
        SimpleNamespace(),
        "category",
        ItemType,
        kind="forward_single",
    )


def test_check_n1_planned_hit_is_silent() -> None:
    """Planned key present -> resolver is a no-op regardless of strictness."""
    ItemType = _parent_type(Item, "ItemType")

    key = resolver_key(ItemType, "category", ("allItems", "category"))
    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": {key}, "dst_optimizer_strictness": "raise"},
        path=response_path("allItems", 0, "category"),
    )
    _check_n1(
        fake_info,
        SimpleNamespace(),
        "category",
        ItemType,
        kind="forward_single",
    )


def test_check_n1_default_strictness_off_is_silent_on_lazy_load() -> None:
    """Strictness defaults to ``off`` and an unplanned lazy load is silent."""
    ItemType = _parent_type(Item, "ItemType")

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set()},
        path=response_path("allItems", 0, "category"),
    )
    _check_n1(
        fake_info,
        SimpleNamespace(),
        "category",
        ItemType,
        kind="forward_single",
    )


def test_check_n1_raise_strictness_raises_on_lazy_load() -> None:
    """Strictness=raise + unplanned + lazy -> OptimizerError."""
    ItemType = _parent_type(Item, "ItemType")

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=response_path("allItems", 0, "category"),
    )
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: category"):
        _check_n1(
            fake_info,
            SimpleNamespace(),
            "category",
            ItemType,
            kind="forward_single",
        )


@pytest.mark.parametrize("kind", ["many", "reverse_many_to_one"])
def test_check_n1_many_side_kind_treats_consumer_set_attribute_as_lazy(
    kind: Literal["many", "reverse_many_to_one"],
) -> None:
    """Many-side ignores ``__dict__`` short-circuit.

    A consumer (or test double) setting ``root.<field>`` directly does
    not populate Django's prefetch cache, so the many-side resolver
    must still treat the access as lazy. Pinned via strictness=raise.
    """
    CategoryType = _parent_type(Category, "CategoryType")

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=response_path("allCategories", 0, "items"),
    )
    # ``items`` is set directly on the root - that would short-circuit the
    # single-valued cache check via ``__dict__`` membership but must NOT
    # short-circuit the many-side check.
    root = SimpleNamespace(items=["not-a-real-prefetch"])
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: items"):
        _check_n1(fake_info, root, "items", CategoryType, kind=kind)


def test_check_n1_many_kind_respects_prefetched_objects_cache() -> None:
    """Many-side recognises ``_prefetched_objects_cache`` as the only valid cache."""
    CategoryType = _parent_type(Category, "CategoryType")

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=response_path("allCategories", 0, "items"),
    )
    root = SimpleNamespace(_prefetched_objects_cache={"items": []})
    # No raise - the relation is prefetched, so the strictness branch is skipped.
    _check_n1(fake_info, root, "items", CategoryType, kind="many")


def test_check_n1_probes_prefetch_cache_under_cache_name() -> None:
    """The cache probe keys on the CACHE NAME, the plan key on the field name.

    Django stores a reverse-FK prefetch under the instance accessor
    (``"plainbook_set"``), which diverges from ``field.name``
    (``"plainbook"``) for reverse relations without ``related_name``.
    With ``cache_name`` supplied - as every
    production resolver does - a manually prefetched relation is
    recognized as cached; the field-name fallback (test-double direct
    callers) would mislabel the same root as lazy and raise.
    """
    PlainAuthorType = _parent_type(Category, "PlainAuthorType")

    fake_info = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=response_path("authors", 0, "plainbook"),
    )
    root = SimpleNamespace(_prefetched_objects_cache={"plainbook_set": []})
    # No raise: the cache-name-keyed probe finds the prefetched rows.
    _check_n1(
        fake_info,
        root,
        "plainbook",
        PlainAuthorType,
        kind="reverse_many_to_one",
        cache_name="plainbook_set",
    )
    # Without the cache name the probe falls back to the field name and
    # misses the cache - documenting why production callers must pass it.
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: plainbook"):
        _check_n1(
            fake_info,
            root,
            "plainbook",
            PlainAuthorType,
            kind="reverse_many_to_one",
        )


def test_runtime_path_from_info_strips_list_indexes_and_keeps_aliases() -> None:
    """Runtime response paths preserve aliases and omit list indexes.

    ``runtime_path_from_info`` is an optimizer-plan helper with no GraphQL
    selection of its own; the live sibling for planned vs unplanned relations is
    ``examples/fakeshop/test_query/test_products_visibility_api.py``.
    """
    info = SimpleNamespace(path=response_path("allItems", 0, "cat"))
    assert runtime_path_from_info(info) == ("allItems", "cat")


def test_o1_make_relation_resolver_reverse_one_to_one_returns_none_on_doesnotexist() -> None:
    """Direct unit: reverse OneToOne resolver swallows DoesNotExist into None.

    Direct ``_make_relation_resolver`` call with a fabricated ``DoesNotExist``.
    Live reverse-O2O payloads live in
    ``examples/fakeshop/test_query/test_products_visibility_api.py``; this row
    keeps the swallow-to-None branch a request cannot name without a missing
    reverse accessor.
    """

    class FakeDoesNotExist(Exception):  # noqa: N818  (mirrors Django's Model.DoesNotExist naming)
        pass

    class FakeProfile:
        DoesNotExist = FakeDoesNotExist

    fake_field = SimpleNamespace(
        name="profile",
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=True,
        related_model=FakeProfile,
    )
    resolver = _make_relation_resolver(_as_field(fake_field))

    class RootMissingProfile:
        @property
        def profile(self) -> NoReturn:
            raise FakeDoesNotExist

    class RootWithProfile:
        profile = "the-profile"

    fake_info = make_info()
    assert resolver(RootMissingProfile(), fake_info) is None
    assert resolver(RootWithProfile(), fake_info) == "the-profile"
    assert resolver.__name__ == "resolve_profile"


# ---------------------------------------------------------------------------
# Absence containment: a relation that does not resolve to a row collapses to
# ``None`` instead of letting the ORM's absence signal escape the resolver.
# Forward and reverse, sync and async, fast path and planned path.
# ---------------------------------------------------------------------------


def _forward_category_resolver(
    parent_type: type[DjangoType],
) -> Callable[[object, Info[object, object]], object]:
    """Build the generated forward resolver for ``Item.category`` under ``parent_type``."""
    return _make_relation_resolver(
        Item._meta.get_field("category"),
        parent_type=parent_type,
    )


def test_forward_resolver_contains_unsaved_instance_does_not_exist() -> None:
    """Forward resolver: an unsaved instance's unset non-null FK collapses to None.

    Django's ``ForwardManyToOneDescriptor`` answers ``item.category`` on an
    unsaved row with ``RelatedObjectDoesNotExist`` (an ``AttributeError``
    subclass) raised WITHOUT a query. The generated resolver contains it into
    ``None`` - the same absent-row contract the reverse OneToOne branch has -
    instead of letting the ORM exception escape the public resolver boundary.
    """
    resolver = _forward_category_resolver(_parent_type(Item))
    root = Item(name="unsaved")
    assert root.category_id is None
    fake_info = make_info()
    assert resolver(root, fake_info) is None


@pytest.mark.asyncio
async def test_forward_resolver_async_contains_unsaved_instance_does_not_exist() -> None:
    """Async parity of the unsaved-instance containment (fast path).

    The async branch offloads the unloaded descriptor read through
    ``sync_to_async``; the absence signal raised inside that thread is
    contained into ``None`` exactly as the sync branch contains it.
    """
    resolver = _forward_category_resolver(_parent_type(Item))
    root = Item(name="unsaved-async")
    fake_info = make_info()
    pending = resolver(root, fake_info)
    assert inspect.isawaitable(pending)
    assert await pending is None


def test_forward_resolver_planned_path_contains_unsaved_instance_does_not_exist() -> None:
    """Planned-path parity: FK-id elisions armed, unsaved root still contained.

    Arming elisions (with a key that does not match this field) routes the
    resolve through the planned branch past ``_check_n1``; the descriptor
    read there carries the same containment as the fast path.
    """
    item_type = _parent_type(Item)
    resolver = _forward_category_resolver(item_type)
    armed = {resolver_key(item_type, "category", ("elsewhere", "category"))}
    fake_info = make_info(
        context={DST_OPTIMIZER_FK_ID_ELISIONS: armed},
        path=response_path("allItems", 0, "category"),
    )
    root = Item(name="unsaved-planned")
    assert resolver(root, fake_info) is None


@pytest.mark.asyncio
async def test_forward_resolver_async_planned_path_contains_unsaved_instance() -> None:
    """Async planned-path parity of the unsaved-instance containment."""
    item_type = _parent_type(Item)
    resolver = _forward_category_resolver(item_type)
    armed = {resolver_key(item_type, "category", ("elsewhere", "category"))}
    fake_info = make_info(
        context={DST_OPTIMIZER_FK_ID_ELISIONS: armed},
        path=response_path("allItems", 0, "category"),
    )
    root = Item(name="unsaved-async-planned")
    pending = resolver(root, fake_info)
    assert inspect.isawaitable(pending)
    assert await pending is None


def test_o1_reverse_one_to_one_propagates_plain_attribute_error() -> None:
    """Reverse OneToOne: a plain ``AttributeError`` is a BUG, not an absent row.

    The catch is exactly ``related_model.DoesNotExist`` - which Django's
    per-relation ``RelatedObjectDoesNotExist`` subclasses, so the real absent
    reverse row is still contained. A plain ``AttributeError`` is not that: it
    comes from a consumer's own descriptor / property or a typo'd accessor,
    and swallowing it would turn a programming error into a silent ``null``.
    It propagates instead.
    """

    class FakeDoesNotExist(Exception):  # noqa: N818  (mirrors Django's Model.DoesNotExist naming)
        pass

    class FakeProfile:
        DoesNotExist = FakeDoesNotExist

    fake_field = SimpleNamespace(
        name="profile",
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=True,
        related_model=FakeProfile,
    )
    resolver = _make_relation_resolver(_as_field(fake_field))

    class RootHostileProfile:
        @property
        def profile(self) -> NoReturn:
            raise AttributeError("hostile reverse descriptor")

    fake_info = make_info()
    with pytest.raises(AttributeError, match="hostile reverse descriptor"):
        resolver(RootHostileProfile(), fake_info)


def test_reverse_one_to_one_real_model_missing_row_contained() -> None:
    """Real reverse OneToOne (library app): unsaved patron resolves to None.

    ``patron.card`` on an unsaved ``Patron`` raises
    ``MembershipCard.DoesNotExist`` from the descriptor without a query; the
    generated resolver contains it into ``None``.
    """
    resolver = _make_relation_resolver(
        Patron._meta.get_field("card"),
        parent_type=_parent_type(Patron),
    )
    fake_info = make_info()
    assert resolver(Patron(name="No Card"), fake_info) is None


@pytest.mark.asyncio
async def test_reverse_one_to_one_async_contains_missing_row() -> None:
    """Async parity of the real-model reverse OneToOne containment."""
    resolver = _make_relation_resolver(
        Patron._meta.get_field("card"),
        parent_type=_parent_type(Patron),
    )
    fake_info = make_info()
    pending = resolver(Patron(name="No Card Async"), fake_info)
    assert inspect.isawaitable(pending)
    assert await pending is None


@pytest.mark.django_db
def test_forward_resolver_nullable_dangling_fk_resolves_to_none() -> None:
    """Direct resolver: a nullable dangling FK swallows the target's ``DoesNotExist``.

    The non-nullable dangling case raises ``RelatedObjectDoesNotExist`` (an
    ``AttributeError`` subclass); the nullable one lets the target's plain
    ``Model.DoesNotExist`` out of ``get_object()``. A planned JOIN on the
    shipped schema never takes this arm. Wire ``parent: null`` with the column
    still set lives in
    ``examples/fakeshop/test_query/test_scalars_api.py``
    (``test_nullable_self_fk_dangling_parent_resolves_to_null_over_http``).
    """

    def create_specimen(label: str, *, parent: ScalarSpecimen | None = None) -> ScalarSpecimen:
        return ScalarSpecimen.objects.create(
            label=label,
            occurred_on=datetime.date(2026, 1, 1),
            occurred_at=timezone.now(),
            occurred_time=datetime.time(12, 0),
            payload={},
            external_id=uuid.uuid4(),
            parent=parent,
        )

    parent = create_specimen("dangling-fk-parent")
    child = create_specimen("dangling-fk-child", parent=parent)
    resolver = _make_relation_resolver(
        ScalarSpecimen._meta.get_field("parent"),
        parent_type=_parent_type(ScalarSpecimen),
    )
    fake_info = make_info()
    disabled = db_connection.disable_constraint_checking()
    try:
        with db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM scalars_scalarspecimen WHERE id = %s", [saved_pk(parent)])
        # Re-read so the instance carries the dangling column with an EMPTY
        # relation cache: the row created above still holds the parent object
        # in ``_state.fields_cache`` and would answer from it without a query.
        dangling = ScalarSpecimen.objects.get(pk=saved_pk(child))
        assert dangling.parent_id == saved_pk(parent)
        assert resolver(dangling, fake_info) is None
    finally:
        # Clear the dangling column BEFORE re-enabling constraint checks so
        # the fixture teardown's ``PRAGMA foreign_key_check`` sees a
        # consistent database (the test's transaction rolls back anyway).
        ScalarSpecimen.objects.filter(pk=saved_pk(child)).update(parent=None)
        if disabled:
            db_connection.enable_constraint_checking()


def test_forward_resolver_propagates_consumer_attribute_error() -> None:
    """A consumer descriptor raising ``AttributeError`` is NOT swallowed.

    The containment catches the target's ``DoesNotExist`` only. A plain
    ``AttributeError`` from a consumer-authored property / descriptor (or a
    typo'd accessor) is a programming error: collapsing it to ``None`` would
    answer the query with a silent ``null`` and hide the bug, so it
    propagates out of the resolver unchanged.
    """
    resolver = _forward_category_resolver(_parent_type(Item))

    class HostileItem:
        """Stands in for a consumer overriding the relation with a broken property."""

        @property
        def category(self) -> NoReturn:
            raise AttributeError("consumer descriptor bug")

    fake_info = make_info()
    with pytest.raises(AttributeError, match="consumer descriptor bug"):
        resolver(HostileItem(), fake_info)


def test_reverse_one_to_one_without_related_model_propagates_attribute_error() -> None:
    """Reverse OneToOne with no target model: a plain ``AttributeError`` propagates.

    The absence catch degrades to "catch nothing" when the relation carries no
    target model, exactly as the forward branch degrades: a consumer descriptor
    raising ``AttributeError`` is a programming error, not an absent row, on
    both branches.
    """
    fake_field = SimpleNamespace(
        name="profile",
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=True,
    )
    resolver = _make_relation_resolver(_as_field(fake_field))

    class RootHostileProfile:
        @property
        def profile(self) -> NoReturn:
            raise AttributeError("hostile reverse descriptor, unknown target")

    with pytest.raises(AttributeError, match="hostile reverse descriptor, unknown target"):
        resolver(RootHostileProfile(), make_info())


def test_forward_resolver_without_related_model_propagates_attribute_error() -> None:
    """Forward FK with no target model at all: a plain ``AttributeError`` propagates.

    Pins the survivor half of the unified fallback: a double field without
    ``related_model`` degrades to "catch nothing", so a consumer descriptor
    raising ``AttributeError`` propagates instead of collapsing to ``None``.
    """
    fake_field = SimpleNamespace(
        name="category",
        many_to_many=False,
        one_to_many=False,
        one_to_one=False,
    )
    resolver = _make_relation_resolver(_as_field(fake_field))

    class HostileRoot:
        @property
        def category(self) -> NoReturn:
            raise AttributeError("hostile forward descriptor, no target")

    with pytest.raises(AttributeError, match="hostile forward descriptor, no target"):
        resolver(HostileRoot(), make_info())


# ---------------------------------------------------------------------------
# Multi-database cooperation (spec-023)
# ---------------------------------------------------------------------------
#
# Per ``docs/SPECS/spec-023-multi_db-0_0_7.md``.
#
# Five resolver-level tests pin Decision 3 axis 1 (FK-id elision router
# call shape; four tests) and axis 4 (strictness connection-agnostic shape;
# one test). The four FK-id tests mock ``router.db_for_read`` per Decision 5;
# the strictness test does NOT mock the router (it never reaches that path
# per ``django_strawberry_framework/types/resolvers.py::_check_n1``).
#
# Mock pattern (per spec-023 Decision 5 + ``Mock contract`` block):
#
# ruff: disable[ERA001]
#     from unittest.mock import Mock
#     import django_strawberry_framework.types.resolvers as resolvers_module
#     mock_router = Mock()
#     mock_router.db_for_read.return_value = "default"
#     monkeypatch.setattr(resolvers_module, "router", mock_router)
#     # ...
#     mock_router.db_for_read.assert_called_once_with(
#         <related_model>, instance=<expected_instance>
#     )
# ruff: enable[ERA001]
#
# Rebinding the module-local ``router`` name leaves the shared
# ``django.db.router`` singleton untouched (Decision 5); ``monkeypatch``
# restores the name at teardown.
#
# Fixture rows: the FK-id elision path needs a ``root`` with the FK
# ``attname`` populated (so ``getattr(root, field_meta.attname)`` is
# non-None). The tests below use an unsaved ``Item`` instance (has
# ``_state``) or a ``SimpleNamespace`` (no ``_state``).


def test_fk_id_elision_stub_sets_state_db_via_router_db_for_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Decision 3 axis 1 - stub's ``_state.db`` is set via ``router.db_for_read``."""
    db_for_read = Mock(return_value="default")
    mock_router = Mock(db_for_read=db_for_read)
    monkeypatch.setattr(resolvers_module, "router", mock_router)

    parent_row = Item(category_id=42)
    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        related_model=Category,
        attname="category_id",
    )

    stub = _build_fk_id_stub(parent_row, field_meta)

    assert stub is not None
    assert isinstance(stub, Category)
    assert saved_pk(stub) == 42
    assert stub._state.db == "default"
    db_for_read.assert_called_once()


def test_fk_id_elision_router_call_passes_parent_row_as_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Decision 3 axis 1 - ``router.db_for_read`` receives ``instance=<parent_row>`` with ``_state``."""
    db_for_read = Mock(return_value="default")
    mock_router = Mock(db_for_read=db_for_read)
    monkeypatch.setattr(resolvers_module, "router", mock_router)

    parent_row = Item(category_id=42)
    assert hasattr(parent_row, "_state")  # invariant: Django model instances always have _state
    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        related_model=Category,
        attname="category_id",
    )

    _build_fk_id_stub(parent_row, field_meta)

    # ``instance=`` is load-bearing - a regression switching it to ``instance=None``
    # would silently break consumer routers that consult the parent row's ``_state.db``.
    db_for_read.assert_called_once_with(Category, instance=parent_row)


def test_fk_id_elision_router_call_passes_none_instance_when_parent_lacks_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Decision 3 axis 1 - router.db_for_read receives ``instance=None`` when parent lacks ``_state``."""
    db_for_read = Mock(return_value="default")
    mock_router = Mock(db_for_read=db_for_read)
    monkeypatch.setattr(resolvers_module, "router", mock_router)

    # ``SimpleNamespace`` has no ``_state`` attribute, so the
    # ``getattr(root, "_state", None) is not None`` branch at
    # ``django_strawberry_framework/types/resolvers.py::_build_fk_id_stub #"instance = root if getattr"``
    # forwards ``instance=None`` to the router.
    parent_row = SimpleNamespace(pk=1, category_id=42)
    assert not hasattr(parent_row, "_state")

    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        related_model=Category,
        attname="category_id",
    )

    stub = _build_fk_id_stub(parent_row, field_meta)

    assert stub is not None
    db_for_read.assert_called_once_with(Category, instance=None)


def test_fk_id_elision_returns_none_for_null_fk_and_does_not_call_router(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Decision 3 axis 1 - null FK takes the early-return branch BEFORE the router is consulted."""
    db_for_read = Mock(return_value="default")
    mock_router = Mock(db_for_read=db_for_read)
    monkeypatch.setattr(resolvers_module, "router", mock_router)

    parent_row = SimpleNamespace(category_id=None)
    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        related_model=Category,
        attname="category_id",
    )

    # ``django_strawberry_framework/types/resolvers.py::_build_fk_id_stub #"if related_id is None"``
    # - early ``return None`` before reaching the
    # router. Split from the parent-lacks-``_state`` case because
    # the two branches are distinct and a regression in either is a
    # different bug class.
    result = _build_fk_id_stub(parent_row, field_meta)

    assert result is None
    db_for_read.assert_not_called()


def test_strictness_check_is_connection_agnostic_under_non_default_alias() -> None:
    """Decision 3 axis 4 - strictness mode raises ``OptimizerError`` regardless of ``_state.db``."""
    _ParentType = _parent_type(Item, "_ParentType")

    # ``_state.db = "shard_b"`` proves the non-default alias is accepted
    # without altering the check's shape; ``fields_cache`` is empty so the
    # second lazy-load gate at ``_will_lazy_load_single`` reports the
    # relation is unloaded.
    fields_cache: dict[str, object] = {}
    state = SimpleNamespace(db="shard_b", fields_cache=fields_cache)
    root = SimpleNamespace(_state=state)
    assert "shelf" not in vars(root)
    assert "shelf" not in fields_cache

    # Non-empty planned set that does NOT include this resolver's key so
    # the lazy-load gate is reached (an empty planned set is also valid;
    # the unrelated key documents the "planned but not this one" shape).
    info = SimpleNamespace(
        context={
            DST_OPTIMIZER_PLANNED: {"some.unrelated.key@/"},
            DST_OPTIMIZER_STRICTNESS: "raise",
        },
        path=None,
    )

    with pytest.raises(OptimizerError, match="Unplanned N\\+1: shelf"):
        _check_n1(info, root, "shelf", _ParentType, kind="forward_single")


# ---------------------------------------------------------------------------
# spec-035 Decision 5 - FK-id elision loaded-check + loud fallback
# ---------------------------------------------------------------------------


def test_fk_id_elision_enabled_under_mutation() -> None:
    """Decision 5: a fully-loaded FK column still elides; no join, no lazy load.

    The resolver never sees the operation type - the elision set is on
    ``info.context`` regardless of operation, so this asserts elision works when
    the FK column IS loaded (the optimizer-owned norm and the
    consumer-``.only()``-that-includes-the-FK case), which is exactly why the
    Decision 5 guard is operation-independent.
    """
    ItemType = _parent_type(Item, "ItemType")

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))

    class Root:
        category_id = 42

        @property
        def category(self) -> NoReturn:
            raise AssertionError("loaded FK column must elide, never lazy-load the relation")

    fake_info = make_info(
        context={DST_OPTIMIZER_FK_ID_ELISIONS: {key}},
        field_name="category",
        path=response_path("allItems", 0, "category"),
    )
    result = resolver(Root(), fake_info)
    assert isinstance(result, Category)
    assert saved_pk(result) == 42


@pytest.mark.parametrize("operation_arm", ["query", "mutation"])
def test_fk_id_elision_falls_back_when_consumer_only_defers_fk(
    operation_arm: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Decision 5: a deferred consumer-``.only()`` FK column falls back loudly.

    A row the plan did not project - one a consumer-owned
    ``Prefetch(queryset=Item.objects.only("name"))`` loaded - defers ``category_id``
    while the plan still carries the ``category`` elision AND records it planned.
    The resolver must NOT silently read the deferred ``category_id`` (the per-row
    lazy load Decision 5 forbids), and because the relation is planned it must
    NOT let ``_check_n1`` mistake the planned key for a satisfied relation - the
    fallback forces the lazy-load probe so strictness sees the access. The
    resolver is operation-agnostic, so each ``operation_arm`` builds its info under
    that operation and both fall back the same way.
    """
    ItemType = _parent_type(Item, "ItemType")

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))

    class Root:
        accessed_relation = False

        def get_deferred_fields(self) -> set[str]:
            return {"category_id"}

        @property
        def category_id(self) -> NoReturn:
            raise AssertionError("deferred FK column must NOT be read (silent per-row load)")

        @property
        def category(self) -> object:
            # The honest fallback: a real lazy load, which strictness must see.
            self.accessed_relation = True
            return SimpleNamespace(pk=42)

    def context(strictness: str) -> dict[str, set[str] | str]:
        # The relation is in BOTH elisions and planned (the elision branch records
        # it planned), exactly the production shape Decision 5 must not mistake.
        return {
            DST_OPTIMIZER_FK_ID_ELISIONS: {key},
            DST_OPTIMIZER_PLANNED: {key},
            DST_OPTIMIZER_STRICTNESS: strictness,
        }

    # "raise": the fallback is loud - OptimizerError, not a silent planned-relation
    # lazy load, and never a read of the deferred FK column.
    info = make_info(
        context=context("raise"),
        field_name="category",
        path=response_path("allItems", 0, "category"),
        operation=OperationType(operation_arm),
    )
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: category"):
        resolver(Root(), info)

    # "warn": logs and returns the related object via the normal resolve.
    root = Root()
    info = make_info(
        context=context("warn"),
        field_name="category",
        path=response_path("allItems", 0, "category"),
        operation=OperationType(operation_arm),
    )
    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = resolver(root, info)
    assert any("Potential N+1 on category" in r.message for r in caplog.records)
    assert root.accessed_relation is True
    assert isinstance(result, SimpleNamespace)
    assert read_attr(result, "pk") == 42


def test_fk_id_stub_returns_unsafe_sentinel_when_attname_deferred() -> None:
    """Direct unit: ``_build_fk_id_stub`` signals unsafe without reading the column.

    Pins the loaded-check at the function boundary (mirrors
    ``test_b2_fk_id_stub_returns_none_without_related_model``): a deferred FK
    ``attname`` yields ``_FK_ELISION_UNSAFE`` and the deferred column is never read
    (spec-035 Decision 5).
    """
    field_meta = FieldMeta(
        name="category",
        is_relation=True,
        attname="category_id",
        related_model=Category,
    )

    class Root:
        def get_deferred_fields(self) -> set[str]:
            return {"category_id"}

        @property
        def category_id(self) -> NoReturn:
            raise AssertionError("deferred FK column must NOT be read")

    assert _build_fk_id_stub(Root(), field_meta) is _FK_ELISION_UNSAFE
    # A fully-loaded double (column in ``__dict__``) still builds the stub.
    stub = _build_fk_id_stub(SimpleNamespace(category_id=42), field_meta)
    assert isinstance(stub, Category)
    assert saved_pk(stub) == 42


@pytest.mark.django_db
def test_fk_id_elision_falls_back_on_real_deferred_only_instance(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Decision 5: a REAL ``Item.objects.only("name")`` instance.

    The double-based fallback test asserts the behavior; this pins the actual
    Django deferred-field bookkeeping the guard depends on - that a real
    ``Item.objects.only("name").get(...)`` reports ``category_id`` in
    ``get_deferred_fields()`` and absent from ``__dict__`` - so the loaded-check
    fires on the genuine ORM shape, not just a simulated one. With the relation
    in BOTH the elision set and the planned set (the production shape), the
    resolver must fall back loudly (``raise`` -> ``OptimizerError``; ``warn`` ->
    logged + normal resolve), never a silent per-row read of the deferred FK
    column.
    """
    services.seed_data(1)

    ItemType = _parent_type(Item, "ItemType")

    field = Item._meta.get_field("category")
    resolver = _make_relation_resolver(field, parent_type=ItemType)
    key = resolver_key(ItemType, "category", ("allItems", "category"))

    # The Django contract the guard depends on, asserted on a real instance.
    pk = Item.objects.values_list("pk", flat=True).first()
    root = Item.objects.only("name").get(pk=pk)
    assert "category_id" in root.get_deferred_fields()
    assert "category_id" not in root.__dict__

    def context(strictness: str) -> dict[str, set[str] | str]:
        return {
            DST_OPTIMIZER_FK_ID_ELISIONS: {key},
            DST_OPTIMIZER_PLANNED: {key},
            DST_OPTIMIZER_STRICTNESS: strictness,
        }

    # "raise": the deferred FK column is never read silently; the fallback is loud.
    info = make_info(
        context=context("raise"),
        field_name="category",
        path=response_path("allItems", 0, "category"),
    )
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: category"):
        resolver(root, info)

    # "warn": logs the access and resolves the real related object normally.
    root = Item.objects.only("name").get(pk=pk)
    info = make_info(
        context=context("warn"),
        field_name="category",
        path=response_path("allItems", 0, "category"),
    )
    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = resolver(root, info)
    assert any("Potential N+1 on category" in r.message for r in caplog.records)
    assert isinstance(result, Category)


def test_fk_attname_is_deferred_and_stub_exceptions() -> None:
    class BrokenDeferred:
        def get_deferred_fields(self) -> NoReturn:
            raise RuntimeError("consumer get_deferred_fields")

    # A consumer ``get_deferred_fields`` override is consumer behaviour: its
    # exception propagates to the schema's error policy.
    with pytest.raises(RuntimeError, match="consumer get_deferred_fields"):
        _fk_attname_is_deferred(BrokenDeferred(), "category_id")

    # _visible_related_object(None, ...) -> None
    assert _visible_related_object(None, DjangoType, unread_info()) is None

    # _build_fk_id_stub with an unreadable attname
    class BrokenRoot:
        @property
        def category_id(self) -> NoReturn:
            raise AttributeError("broken attr")

    fm = FieldMeta.from_django_field(Item._meta.get_field("category"))
    assert _build_fk_id_stub(BrokenRoot(), fm) is None

    # A model refusing the pk-only stub with an ``Exception`` degrades to the
    # ordinary load (pinned live in ``examples/fakeshop/test_query/test_library_api.py``);
    # a ``BaseException`` is not an elision outcome and propagates.
    class StubInterrupted(BaseException):
        pass

    class InterruptedModel:
        def __init__(self, pk: object = None) -> None:
            del pk  # the keyword is part of the model constructor contract; the body only raises
            raise StubInterrupted("stub construction interrupted")

    fake_fm = SimpleNamespace(attname="target_id", related_model=InterruptedModel)
    with pytest.raises(StubInterrupted, match="stub construction interrupted"):
        # basedpyright: a stand-in field meta carrying only the slots the code under test reads;
        # _build_fk_id_stub types the parameter as FieldMeta
        _build_fk_id_stub(SimpleNamespace(target_id=1), fake_fm)  # pyright: ignore[reportArgumentType]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_resolvers_optimizer_scoped_and_visibility() -> None:
    await sync_to_async(services.seed_data)(1)

    class CustomCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Category], info: object) -> QuerySet[Category]:
            return queryset.filter(name__startswith="Visible")

    assert registry.get(Category) is CustomCategoryType

    class CustomItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Item], info: object) -> QuerySet[Item]:
            return queryset.filter(name__startswith="Visible")

    assert registry.get(Item) is CustomItemType

    finalize_django_types()
    frame = begin_execution_frame({}, nested=False)

    try:

        class FakeRevRel:
            name = "profile"
            is_relation = True
            one_to_one = True
            auto_created = True
            related_model = Category

            def get_accessor_name(self) -> str:
                return "profile"

        # Reverse one-to-one resolver (scoped and unscoped)
        rev_field = FakeRevRel()
        rev_resolver = _make_relation_resolver(
            _as_field(rev_field),
            parent_type=CustomItemType,
        )

        key = resolver_key(CustomItemType, "profile", ("item", "profile"))
        publish_scoped_relations({key})

        (cat,) = await sync_to_async(categories_from_seed)(("Visible Cat", False))

        class FakeRevRoot:
            _state = SimpleNamespace(fields_cache={})

            @property
            def profile(self) -> Category:
                return cat

        fake_info = make_info(path=response_path("item", "profile"), context={})
        fake_root = FakeRevRoot()

        res = rev_resolver(fake_root, fake_info)

        if is_awaitable(res):
            res = await res
        assert res == cat

        unscoped_info = make_info(path=response_path("other", "profile"), context={})
        res_unscoped = rev_resolver(fake_root, unscoped_info)
        if is_awaitable(res_unscoped):
            res_unscoped = await res_unscoped
        assert isinstance(res_unscoped, Category)
        assert saved_pk(res_unscoped) == saved_pk(cat)

        # Forward resolver (scoped and unscoped, without strictness)
        fwd_field = Item._meta.get_field("category")
        fwd_resolver = _make_relation_resolver(fwd_field, parent_type=CustomItemType)
        fwd_key = resolver_key(CustomItemType, "category", ("item", "category"))
        publish_scoped_relations({fwd_key})
        fwd_info = make_info(path=response_path("item", "category"), context={})

        res_fwd = fwd_resolver(
            Item(name="Test Item 1", category_id=saved_pk(cat)),
            fwd_info,
        )
        if is_awaitable(res_fwd):
            res_fwd = await res_fwd
        assert isinstance(res_fwd, Category)
        assert saved_pk(res_fwd) == saved_pk(cat)

        fwd_unscoped_info = make_info(path=response_path("other", "category"), context={})
        res_fwd_unscoped = fwd_resolver(
            Item(name="Test Item 2", category_id=saved_pk(cat)),
            fwd_unscoped_info,
        )
        if is_awaitable(res_fwd_unscoped):
            res_fwd_unscoped = await res_fwd_unscoped
        assert isinstance(res_fwd_unscoped, Category)
        assert saved_pk(res_fwd_unscoped) == saved_pk(cat)

        # Forward resolver under an execution armed at ``warn``, which is a
        # whole execution rather than a switch inside one: strictness is part of
        # the frame ``on_execute`` opens, so the planned relation is published
        # into that frame too.
        strict_frame = begin_execution_frame({}, nested=False, strictness="warn")
        try:
            publish_scoped_relations({fwd_key})
            # Scoped
            res_strict_scoped = fwd_resolver(
                Item(name="Test Item 3", category_id=saved_pk(cat)),
                fwd_info,
            )
            if is_awaitable(res_strict_scoped):
                res_strict_scoped = await res_strict_scoped
            assert isinstance(res_strict_scoped, Category)
            assert saved_pk(res_strict_scoped) == saved_pk(cat)

            # Unscoped
            res_strict_unscoped = fwd_resolver(
                Item(name="Test Item 4", category_id=saved_pk(cat)),
                fwd_unscoped_info,
            )
            if is_awaitable(res_strict_unscoped):
                res_strict_unscoped = await res_strict_unscoped
            assert isinstance(res_strict_unscoped, Category)
            assert saved_pk(res_strict_unscoped) == saved_pk(cat)

            # Sync / loaded path under strictness
            loaded_item = Item(name="Test Item Loaded", category_id=saved_pk(cat))
            loaded_item._state.fields_cache["category"] = cat
            res_sync_scoped = fwd_resolver(loaded_item, fwd_info)
            assert isinstance(res_sync_scoped, Category)
            assert saved_pk(res_sync_scoped) == saved_pk(cat)
        finally:
            end_execution_frame(strict_frame)

        # Fallback when _visible_related_object returns a non-awaitable object.
        orig_vis = resolvers_mod._visible_related_object
        try:
            resolvers_mod._visible_related_object = lambda rel, _vt, _inf: rel

            res_rev_sync = rev_resolver(FakeRevRoot(), unscoped_info)
            if is_awaitable(res_rev_sync):
                res_rev_sync = await res_rev_sync
            assert isinstance(res_rev_sync, Category)
            assert saved_pk(res_rev_sync) == saved_pk(cat)

            res_fwd_sync = fwd_resolver(
                Item(name="Test Item 5", category_id=saved_pk(cat)),
                fwd_unscoped_info,
            )
            if is_awaitable(res_fwd_sync):
                res_fwd_sync = await res_fwd_sync
            assert isinstance(res_fwd_sync, Category)
            assert saved_pk(res_fwd_sync) == saved_pk(cat)

            strict_frame = begin_execution_frame({}, nested=False, strictness="warn")
            try:
                res_strict_sync = fwd_resolver(
                    Item(name="Test Item 6", category_id=saved_pk(cat)),
                    fwd_unscoped_info,
                )
                if is_awaitable(res_strict_sync):
                    res_strict_sync = await res_strict_sync
                assert isinstance(res_strict_sync, Category)
                assert saved_pk(res_strict_sync) == saved_pk(cat)

                class FakeItemNull:
                    _state = SimpleNamespace(fields_cache={})
                    category = None

                res_strict_null = fwd_resolver(
                    FakeItemNull(),
                    fwd_unscoped_info,
                )
                if is_awaitable(res_strict_null):
                    res_strict_null = await res_strict_null
                assert res_strict_null is None

            finally:
                end_execution_frame(strict_frame)
        finally:
            resolvers_mod._visible_related_object = orig_vis

        # Many-side resolver with prefetched cache and visibility in async context
        many_field = Category._meta.get_field("items")

        many_resolver = _make_relation_resolver(many_field, parent_type=CustomCategoryType)
        (item_obj,) = await sync_to_async(items_from_seed)(cat, ("Visible Item", False))
        cat_with_cache = SimpleNamespace(
            _prefetched_objects_cache={"items": [item_obj]},
            items=cat.items,
        )
        many_res_unscoped = many_resolver(cat_with_cache, unscoped_info)
        if is_awaitable(many_res_unscoped):
            many_res_unscoped = await many_res_unscoped
        assert isinstance(many_res_unscoped, Sized)
        assert len(many_res_unscoped) == 1

        many_scoped_key = resolver_key(CustomCategoryType, "items", ("category", "items"))
        publish_scoped_relations({many_scoped_key})
        many_scoped_info = make_info(path=response_path("category", "items"), context={})
        many_res_scoped = many_resolver(cat_with_cache, many_scoped_info)
        assert isinstance(many_res_scoped, Iterable)
        assert len(list(many_res_scoped)) == 1
    finally:
        end_execution_frame(frame)


@pytest.mark.django_db
def test_sync_forward_and_many_resolver_visibility() -> None:
    services.seed_data(1)

    class CustomCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Category], info: object) -> QuerySet[Category]:
            return queryset.filter(name__startswith="Visible")

    assert registry.get(Category) is CustomCategoryType

    class CustomItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Item], info: object) -> QuerySet[Item]:
            return queryset.filter(name__startswith="Visible")

    assert registry.get(Item) is CustomItemType

    finalize_django_types()
    frame = begin_execution_frame({}, nested=False)

    try:
        (cat,) = categories_from_seed(("Visible Cat", False))
        (item,) = items_from_seed(cat, ("Visible Item", False))

        fwd_field = Item._meta.get_field("category")
        fwd_resolver = _make_relation_resolver(fwd_field, parent_type=CustomItemType)

        fwd_key = resolver_key(CustomItemType, "category", ("item", "category"))
        publish_scoped_relations({fwd_key})
        fwd_scoped_info = make_info(path=response_path("item", "category"), context={})
        res_scoped = fwd_resolver(item, fwd_scoped_info)
        assert isinstance(res_scoped, Category)
        assert saved_pk(res_scoped) == saved_pk(cat)

        fwd_unscoped_info = make_info(path=response_path("other", "category"), context={})
        res_unscoped = fwd_resolver(item, fwd_unscoped_info)
        assert isinstance(res_unscoped, Category)
        assert saved_pk(res_unscoped) == saved_pk(cat)

        many_field = Category._meta.get_field("items")
        many_resolver = _make_relation_resolver(many_field, parent_type=CustomCategoryType)
        cat_with_cache = SimpleNamespace(
            _prefetched_objects_cache={"items": [item]},
            items=cat.items,
        )
        many_unscoped_info = make_info(path=response_path("other", "items"), context={})
        res_many_unscoped = many_resolver(cat_with_cache, many_unscoped_info)
        assert isinstance(res_many_unscoped, Sized)
        assert len(res_many_unscoped) == 1

        many_key = resolver_key(CustomCategoryType, "items", ("category", "items"))
        publish_scoped_relations({many_key})
        many_scoped_info = make_info(path=response_path("category", "items"), context={})
        res_many_scoped = many_resolver(cat_with_cache, many_scoped_info)
        assert isinstance(res_many_scoped, Iterable)
        assert len(list(res_many_scoped)) == 1

        # ``strictness="warn"`` takes the non-cheap resolver arm; scoped True
        # returns the loaded related object without a visibility re-query.
        warn_frame = begin_execution_frame({}, nested=False, strictness="warn")
        try:

            class FakeRevRel:
                name = "profile"
                is_relation = True
                one_to_one = True
                auto_created = True
                related_model = Category

                def get_accessor_name(self) -> str:
                    return "profile"

            rev_resolver = _make_relation_resolver(
                _as_field(FakeRevRel()),
                parent_type=CustomItemType,
            )
            rev_key = resolver_key(CustomItemType, "profile", ("item", "profile"))
            publish_scoped_relations({rev_key, fwd_key})

            class FakeRevRoot:
                _state = SimpleNamespace(fields_cache={})

                @property
                def profile(self) -> Category:
                    return cat

            rev_info = make_info(path=response_path("item", "profile"), context={})
            assert rev_resolver(FakeRevRoot(), rev_info) == cat
            related = fwd_resolver(item, fwd_scoped_info)
            assert isinstance(related, Category)
            assert saved_pk(related) == saved_pk(cat)
        finally:
            end_execution_frame(warn_frame)
    finally:
        end_execution_frame(frame)


def test_an_unsealable_prefetch_cache_is_refused_under_the_accessor_it_was_read_from() -> None:
    """A prefetch-cache entry the seal refuses is named as the cache it came from.

    The consumer wrote no collection resolver here; the queryset is the one
    Django cached under the relation's accessor, so that is what the error names.
    """

    class _ProjectQuerySet(models.QuerySet[Item]):
        """A project's own queryset class."""

    cached = _ProjectQuerySet(model=Item)
    # basedpyright: the planted foreign row iterable is the hostile input under test; django-stubs
    # types the slot as one of Django's BaseIterable classes
    cached._iterable_class = list  # pyright: ignore[reportAttributeAccessIssue]
    resolver = _make_relation_resolver(
        Category._meta.get_field("items"),
        parent_type=_parent_type(Category),
    )
    root = SimpleNamespace(_prefetched_objects_cache={"items": cached})
    info = make_info(path=response_path("category", "items"), context={})
    with pytest.raises(ConfigurationError) as excinfo:
        resolver(root, info)
    message = str(excinfo.value)
    assert message.startswith("The prefetch cache for 'items' held a _ProjectQuerySet ")
    assert "cannot be sealed into a framework-owned execution queryset" in message
    assert "collection resolver" not in message


def test_resolver_helpers_edge_cases() -> None:
    # kind == "connection_to_attr" never re-probes root: its caller reached the
    # per-parent branch, so a window attribute present on root still queries.
    info = SimpleNamespace(path=SimpleNamespace(key="items", prev=None), context={})
    root_with_attr = SimpleNamespace(_dst_items_connection=["item1"])
    with pytest.raises(OptimizerError, match="Unplanned N\\+1: items"):
        _check_n1(
            info,
            root_with_attr,
            "items",
            _parent_type(Category),
            kind="connection_to_attr",
            strictness="raise",
        )

    # Lines 639 and 697: skip_field_names
    DummyTarget = _parent_type(Category, "DummyTarget")

    fake_rel = SimpleNamespace(name="skipped_rel", is_relation=True)
    _attach_relation_resolvers(
        DummyTarget,
        (_as_field(fake_rel),),
        skip_field_names=frozenset({"skipped_rel"}),
    )
    assert not hasattr(DummyTarget, "skipped_rel")

    fake_file = SimpleNamespace(name="skipped_file", is_relation=False)
    _attach_file_resolvers(
        DummyTarget,
        (_as_field(fake_file),),
        skip_field_names=frozenset({"skipped_file"}),
    )
    assert not hasattr(DummyTarget, "skipped_file")


# ---------------------------------------------------------------------------
# The async many-side bound (MTI ancestor-prefetch reads are live in
# examples/fakeshop/test_query/test_mti_composite_relations_api.py)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@pytest.mark.parametrize("visibility_hook", [False, True], ids=["no-hook", "visibility-hook"])
async def test_async_many_side_refuses_a_bound_that_is_not_a_queryset(
    monkeypatch: pytest.MonkeyPatch,
    visibility_hook: bool,  # noqa: FBT001 - the parametrized branch
) -> None:
    """The async many side iterates the bound as a queryset and refuses any other value.

    An unevaluated queryset's bound is always a queryset slice, so no real relation
    reaches the refusal; the bound is replaced by a ``list`` to pin that the iteration
    raises ``TypeError`` instead of reading the rows of something that is not a queryset.
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryRowsType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    class ItemRowsType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

        if visibility_hook:

            @classmethod
            @override
            def get_queryset(cls, queryset: QuerySet[Item], info: object) -> QuerySet[Item]:
                # The hook hides nothing; its presence routes the rows through visibility.
                return queryset

    assert registry.get(Item) is ItemRowsType
    finalize_django_types()
    category = await Category.objects.afirst()
    assert category is not None

    async def _unbounded_list(result: object, info: object) -> list[object]:
        del result, info  # the stand-in bound ignores its source
        return []

    monkeypatch.setattr(resolvers_mod, "bounded_rows_async", _unbounded_list)
    resolver = _make_relation_resolver(
        Category._meta.get_field("items"),
        parent_type=CategoryRowsType,
    )
    pending = resolver(category, make_info(path=response_path("category", "items"), context={}))

    assert is_awaitable(pending)
    with pytest.raises(TypeError, match="expected the type the source guarantees, got list"):
        await pending
