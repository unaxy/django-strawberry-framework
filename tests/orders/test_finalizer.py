"""Finalizer tests for order binding, Meta.orderset_class promotion, and orphan validation.

Covers:

- ``Meta.orderset_class`` promotion and validation (positive + negative).
- Four-subpass ordering: bind owners -> expand fields -> orphan-validate ->
  materialize. Subpass 1 completes across all owners before subpass 2 runs;
  subpass 3 runs BEFORE subpass 4 so an orphan failure leaves no partial
  state.
- First-bind model compatibility per spec-028 (rejects orderset
  wired to unrelated owner model; message names all four entities).
- Multi-owner reuse: idempotent re-bind of the same ``(orderset, definition)`` pair accepted;
  a second owner refused when either owner has a custom ``get_queryset``, or
  when the two owners read different tables (a multi-table-inheritance parent
  and child), in both declaration orders.
- Per Decision 6 the order side does NOT enforce the filter side's own-PK
  Relay-identity check.
- Unresolved ``RelatedOrder`` propagates as ``ConfigurationError`` with the
  underlying ``ImportError`` preserved on ``__cause__``; a non-import
  expansion failure propagates unchanged.
- Materialization writes input classes to ``orders.inputs.__dict__``;
  idempotent ``finalize_django_types()``.
- Partial-failure recovery (the partially-materialized state stays consistent
  with the ledger).

Finalize-time bind / orphan / collision have no request. Shipped
``Meta.orderset_class`` wiring is exercised live by
``examples/fakeshop/test_query/test_library_api.py``.
"""

from __future__ import annotations

import sys
from collections import OrderedDict
from collections.abc import Iterator
from types import SimpleNamespace
from typing import TYPE_CHECKING, NoReturn, TypeAlias, TypeVar

import pytest
from apps.library.models import (
    Book,
    Branch,
    DeskProfile,
    Genre,
    KioskFault,
    LendingDesk,
    ProxyBranch,
    RepairTicket,
    SelfServeDesk,
    Shelf,
    Venue,
)
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.orders import (
    Ordering,
    OrderInput,
    OrderSet,
    RelatedOrder,
    _helper_referenced_ordersets,
    order_input_type,
)
from django_strawberry_framework.orders.factories import OrderArgumentsFactory
from django_strawberry_framework.orders.inputs import (
    INPUTS_MODULE_PATH,
    _field_specs,
    _materialized_names,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.definition import DjangoTypeDefinition
from django_strawberry_framework.types.finalizer import _bind_orderset_owner
from django_strawberry_framework.types.relay import apply_interfaces
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import read_attr
from tests._idioms import definition_raises

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

_M = TypeVar("_M", bound=models.Model)

if TYPE_CHECKING:
    # Each field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them.
    _FK: TypeAlias = models.ForeignKey[_M | Combinable, _M]
    _Text: TypeAlias = models.TextField[str | Combinable, str]


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    registry.clear()
    _field_specs.clear()
    _helper_referenced_ordersets.clear()
    _materialized_names.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()
    yield
    registry.clear()
    _field_specs.clear()
    _helper_referenced_ordersets.clear()
    _materialized_names.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()


# ---------------------------------------------------------------------------
# Meta.orderset_class promotion + validation
# ---------------------------------------------------------------------------


def test_meta_orderset_class_accepts_order_set_subclass() -> None:
    """``Meta.orderset_class`` promotes onto the definition."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            orderset_class = BookOrder

    assert BookType.__django_strawberry_definition__.orderset_class is BookOrder


def test_meta_orderset_class_rejects_non_order_set() -> None:
    """A non-``OrderSet`` value at class-creation time raises ``ConfigurationError``."""

    class NotAnOrderSet:
        pass

    with pytest.raises(ConfigurationError) as exc_info:

        @definition_raises
        class BookType(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title")
                orderset_class = NotAnOrderSet

    msg = str(exc_info.value)
    assert "OrderSet subclass" in msg
    assert "NotAnOrderSet" in msg


# ---------------------------------------------------------------------------
# Subpass 1 -> Subpass 2 ordering
# ---------------------------------------------------------------------------


def test_phase_2_5_binds_all_owners_before_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every owner binds before any ``get_fields()`` runs (subpass 1 before subpass 2)."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    observations: list[bool] = []

    @classmethod
    def instrumented_get_fields(cls: type[ShelfOrder]) -> OrderedDict[str, RelatedOrder | None]:
        observations.append(cls._owner_definition is not None)
        # The inherited ``OrderSet.get_fields`` the spy shadows on ``ShelfOrder``.
        return super(ShelfOrder, cls).get_fields()

    monkeypatch.setattr(ShelfOrder, "get_fields", instrumented_get_fields)

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")
            orderset_class = ShelfOrder

    assert registry.get(Shelf) is ShelfType

    finalize_django_types()

    assert observations, "ShelfOrder.get_fields was never called"
    assert all(observations), (
        "ShelfOrder._owner_definition was unset during get_fields; "
        "subpass 1 did not complete across all owners before subpass 2 ran."
    )


# ---------------------------------------------------------------------------
# Subpass 2 -- ImportError rewrap; other failures propagate
# ---------------------------------------------------------------------------


def test_phase_2_5_unresolved_related_order_raises_at_finalize() -> None:
    """``RelatedOrder("NonExistent")`` -> ``ConfigurationError`` with ``ImportError`` cause."""

    class BookOrder(OrderSet):
        shelf = RelatedOrder("NonExistentOrder", field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "Cannot finalize Django types: orderset" in msg
    assert "BookOrder" in msg
    assert "NonExistentOrder" in msg
    assert isinstance(exc_info.value.__cause__, ImportError)


def test_phase_2_5_non_import_get_fields_failure_propagates_unchanged() -> None:
    """A consumer factory's own exception raised during ``get_fields()`` propagates."""

    def _broken_factory() -> NoReturn:
        raise ValueError("intentional factory failure")

    class BookOrder(OrderSet):
        broken = RelatedOrder(_broken_factory, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

    with pytest.raises(ValueError, match="intentional factory failure"):
        finalize_django_types()


def test_phase_2_5_non_order_set_related_target_raises_uniform_error() -> None:
    """A ``RelatedOrder`` resolving to a non-``OrderSet`` class surfaces typed at finalize.

    The target-type gate on ``RelatedOrder.orderset`` raises
    ``ConfigurationError`` at the subpass-2 Layer-2 walk (``_expand_orderset``
    forces ``related.orderset``), which propagates BY IDENTITY -- the
    mis-wiring cannot survive until subpass 4's BFS materialization, where it
    would leak a raw ``AttributeError`` (``type_name_for`` missing on the
    target).
    """

    class NotAnOrderSet:
        pass

    class BookOrder(OrderSet):
        # basedpyright: the non-OrderSet target is the hostile input under test; RelatedOrder types
        # the parameter as _OrderSetTarget
        shelf = RelatedOrder(NotAnOrderSet, field_name="shelf")  # pyright: ignore[reportArgumentType]

        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    # The typed gate's message, propagated by identity (no subpass-2 rewrap).
    assert "BookOrder" in msg
    assert "NotAnOrderSet" in msg
    assert "OrderSet subclass" in msg
    assert "raised during expansion" not in msg


def test_phase_2_5_configuration_error_during_expansion_propagates_by_identity() -> None:
    """A ``ConfigurationError`` from the subpass-2 expansion re-raises unchanged.

    If ``get_fields()`` / the ``related.orderset`` Layer-2 walk raises a
    ``ConfigurationError`` directly (as opposed to an ``ImportError``), it
    propagates by identity rather than being re-wrapped into a second
    ``ConfigurationError`` with the first on ``__cause__``.
    """
    sentinel = ConfigurationError("intentional config failure from related factory")

    def _config_error_factory() -> NoReturn:
        raise sentinel

    class BookOrder(OrderSet):
        broken = RelatedOrder(_config_error_factory, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    # Propagated by identity -- NOT re-wrapped (no second ConfigurationError,
    # no ``raised during expansion`` prefix, the original is not on __cause__).
    assert exc_info.value is sentinel
    assert "raised during expansion" not in str(exc_info.value)


# ---------------------------------------------------------------------------
# Subpass 3 -- orphan validation (runs BEFORE materialize)
# ---------------------------------------------------------------------------


def test_orphan_order_input_type_reference_raises_at_finalize() -> None:
    """A ``order_input_type(StandaloneOrder)`` without wiring raises."""

    class StandaloneOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    # Helper-reference the orderset without wiring it to any DjangoType.
    order_input_type(StandaloneOrder)

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "StandaloneOrder" in msg
    assert "is referenced via OrderInput[...] / order_input_type(...) but never" in msg
    assert "orderset_class = StandaloneOrder" in msg


def test_phase_2_5_orphan_check_runs_before_materialization() -> None:
    """Orphan failure leaves no partial state in the materialization ledgers."""

    class WiredOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class StandaloneOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    order_input_type(StandaloneOrder)

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = WiredOrder

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError):
        finalize_django_types()

    # No input class registered for either orderset; the wired one's
    # would-be input type stayed un-materialized because the orphan
    # check halted the pass before subpass 4 ran.
    wired_input_name = f"{WiredOrder.__name__}InputType"
    assert wired_input_name not in OrderArgumentsFactory.input_object_types
    assert wired_input_name not in _materialized_names


def test_phase_2_5_orphan_validation_lists_every_orphan_orderset() -> None:
    """Two orphans surface in one ``ConfigurationError`` with the multi-orphan lead-in."""

    class OrphanA(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class OrphanB(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    # One orphan per helper spelling: both feed the one ledger the check reads.
    OrderInput[OrphanA]
    order_input_type(OrphanB)

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert (
        "OrderSets referenced via OrderInput[...] / order_input_type(...) but not wired to "
        "any DjangoType:" in msg
    )
    assert "OrphanA" in msg
    assert "OrphanB" in msg
    assert "Add 'orderset_class = <Name>' to the relevant DjangoType's Meta" in msg
    # Sort key contract: offenders ordered by ``__module__.__qualname__``.
    idx_a = msg.index("OrphanA")
    idx_b = msg.index("OrphanB")
    assert idx_a < idx_b


# ---------------------------------------------------------------------------
# Subpass 4 -- materialize
# ---------------------------------------------------------------------------


def test_phase_2_5_subpass_4_materializes_input_classes_as_module_globals() -> None:
    """The materialize pass writes ``BookOrderInputType`` to the inputs module globals."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

    finalize_django_types()

    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "BookOrderInputType")
    assert "BookOrderInputType" in _materialized_names


# ---------------------------------------------------------------------------
# Decision 6 -- first-bind model compatibility
# ---------------------------------------------------------------------------


def test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model() -> None:
    """Rejects an orderset wired to an unrelated model.

    The error message names ALL FOUR entities: owner type, owner model,
    orderset class, and orderset model.
    """

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class BranchType(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")
            orderset_class = BookOrder

    assert registry.get(Branch) is BranchType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    # All four entity names appear in the message.
    assert "BookOrder" in msg
    assert "Book" in msg
    assert "BranchType" in msg
    assert "Branch" in msg


# ---------------------------------------------------------------------------
# Multi-owner reuse -- _bind_orderset_owner direct branches
# ---------------------------------------------------------------------------


def _owner(model: type[models.Model]) -> DjangoTypeDefinition:
    """Declare a plain real ``DjangoType`` over ``model`` and return its definition."""
    owner_model = model

    class OwnerType(DjangoType):
        class Meta:
            model = owner_model
            fields = ("id",)

    return OwnerType.__django_strawberry_definition__


def test_bind_orderset_owner_idempotent_for_same_definition() -> None:
    """Re-binding the SAME ``(orderset, definition)`` pair is a no-op."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    definition = _owner(Shelf)
    _bind_orderset_owner(ShelfOrder, definition)  # previous None -> bind
    _bind_orderset_owner(ShelfOrder, definition)  # previous IS definition -> no-op
    assert ShelfOrder._owner_definition is definition


def test_bind_orderset_owner_does_not_check_own_pk_relay_identity() -> None:
    """Per spec-028 Decision 6 the order side does NOT enforce own-PK Relay identity.

    Two owners whose Relay-node-ness diverges still share one OrderSet
    successfully -- ``ORDER BY id`` uses the column, not the GraphQL ID
    type, so this is not an owner-dependent axis.
    """

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    # Both owners share one table and keep the identity ``get_queryset``, so
    # only the Relay-identity divergence remains. The filter-side equivalent
    # test FAILS here because the filter family checks own-PK Relay identity;
    # the order-side equivalent must succeed.
    class RelayShelfType(DjangoType):
        class Meta:
            model = Shelf
            interfaces = (relay.Node,)
            fields = ("id", "code")

    class PlainShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    apply_interfaces(RelayShelfType, RelayShelfType.__django_strawberry_definition__)
    relay_def = RelayShelfType.__django_strawberry_definition__

    _bind_orderset_owner(ShelfOrder, relay_def)
    # Second distinct owner -- no raise, even though the owners diverge on
    # Relay-node-ness; the order side simply does not care about own-PK Relay
    # identity.
    _bind_orderset_owner(ShelfOrder, PlainShelfType.__django_strawberry_definition__)
    assert ShelfOrder._owner_definition is relay_def


def _declare_shared_shelf_order_owners(*, hooked_first: bool) -> list[type[DjangoType]]:
    """Declare one ``ShelfOrder`` on a hiding and a plain ``Shelf`` type, a ``RelatedOrder`` target.

    ``hooked_first`` picks which owner registers, and so binds, first; the two
    owners return in declaration order.
    """

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["topic"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    def hiding() -> type[DjangoType]:
        class HidingShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "topic")
                primary = True
                orderset_class = ShelfOrder

            @classmethod
            @override
            def get_queryset(
                cls,
                queryset: QuerySet[Shelf],
                info: object,
                **kwargs: object,
            ) -> QuerySet[Shelf]:
                return queryset.exclude(topic="secret")

        return HidingShelfType

    def plain() -> type[DjangoType]:
        class PlainShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "topic")
                primary = False
                orderset_class = ShelfOrder

        return PlainShelfType

    owners = [declare() for declare in ((hiding, plain) if hooked_first else (plain, hiding))]

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            orderset_class = BookOrder

    assert BookType.__django_strawberry_definition__.orderset_class is BookOrder
    return owners


@pytest.mark.parametrize("hooked_first", [True, False], ids=["hiding-first", "plain-first"])
def test_phase_2_5_rejects_shared_orderset_when_an_owner_scopes_get_queryset(
    *,
    hooked_first: bool,
) -> None:
    """One ``OrderSet`` on a hiding and a plain owner is refused in both declaration orders.

    ``orderBy: [{shelf: {topic: ...}}]`` reads the ``shelf`` hop through the type
    ``ShelfOrder`` is bound to (``OrderSet._scoped_hops``), and only the first
    binding is stored: bound to ``PlainShelfType`` a hidden shelf's topic would
    position its book, bound to ``HidingShelfType`` it would sort as a missing
    shelf. Finalize refuses the pairing instead of letting declaration order
    pick the visibility.
    """
    owners = _declare_shared_shelf_order_owners(hooked_first=hooked_first)
    expected = ["HidingShelfType", "PlainShelfType"]
    assert [owner.__name__ for owner in owners] == (expected if hooked_first else expected[::-1])
    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert msg.startswith("OrderSet ")
    assert "get_queryset visibility" in msg
    assert "RelatedOrder target" in msg
    assert "ShelfOrder" in msg
    assert "HidingShelfType" in msg
    assert "PlainShelfType" in msg
    assert "Declare separate OrderSet subclasses per owner." in msg


def test_phase_2_5_rejects_shared_orderset_whose_owners_share_one_custom_get_queryset() -> None:
    """Two owners inheriting ONE custom ``get_queryset`` are refused: function identity is not visibility.

    The hook runs with each owner's own ``cls``, so a ``cls``-parameterized body
    can hide different rows per owner while both owners share its function.
    """

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["topic"]

    class _HidingShelfBase(DjangoType):
        # No ``Meta``: an unregistered base both owners inherit the hook from.
        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Shelf],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Shelf]:
            return queryset.exclude(topic="secret")

    class PrimaryShelfType(_HidingShelfBase):
        class Meta:
            model = Shelf
            fields = ("id", "topic")
            primary = True
            orderset_class = ShelfOrder

    class SecondaryShelfType(_HidingShelfBase):
        class Meta:
            model = Shelf
            fields = ("id", "topic")
            orderset_class = ShelfOrder

    assert registry.get(Shelf) is PrimaryShelfType
    assert registry.model_for_type(SecondaryShelfType) is Shelf
    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "get_queryset visibility" in msg
    assert "PrimaryShelfType" in msg
    assert "SecondaryShelfType" in msg


def test_phase_2_5_accepts_shared_orderset_whose_owners_keep_the_identity_get_queryset() -> None:
    """Two owners of one model that both keep the default hook hide nothing, so they share a set."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["topic"]

    class PrimaryShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "topic")
            primary = True
            orderset_class = ShelfOrder

    class SecondaryShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "topic")
            orderset_class = ShelfOrder

    finalize_django_types()
    assert ShelfOrder._owner_definition is PrimaryShelfType.__django_strawberry_definition__
    assert SecondaryShelfType.__django_strawberry_definition__.orderset_class is ShelfOrder


@pytest.mark.parametrize("parent_first", [True, False], ids=["parent-first", "child-first"])
def test_phase_2_5_rejects_shared_orderset_whose_owners_read_different_tables(
    *,
    parent_first: bool,
) -> None:
    """A ``Venue`` owner and a ``LendingDesk`` owner of one ``OrderSet`` are refused in both orders.

    A path re-entering the set's table reads the type it is bound to, and
    multi-table-inheritance parent and child are different tables: bound to the
    parent owner a re-entered ``Venue`` row reads that owner, bound to the child
    it reads ``Venue``'s primary. Both owners keep the identity hook, so only the
    table axis refuses them.
    """

    class VenueOrder(OrderSet):
        class Meta:
            model = Venue
            fields = ["name"]

    def parent() -> type[DjangoType]:
        class VenueOwnerType(DjangoType):
            class Meta:
                model = Venue
                fields = ("id", "name")
                orderset_class = VenueOrder

        return VenueOwnerType

    def child() -> type[DjangoType]:
        class DeskOwnerType(DjangoType):
            class Meta:
                model = LendingDesk
                fields = ("name",)
                orderset_class = VenueOrder

        return DeskOwnerType

    for declare in (parent, child) if parent_first else (child, parent):
        declare()
    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert msg.startswith("OrderSet ")
    assert "cannot bind to multiple owners over different tables" in msg
    assert "VenueOwnerType (model Venue)" in msg
    assert "DeskOwnerType (model LendingDesk)" in msg
    assert "Declare separate OrderSet subclasses per owner." in msg


@pytest.mark.parametrize("proxy_first", [True, False], ids=["proxy-first", "concrete-first"])
def test_phase_2_5_accepts_shared_orderset_whose_owners_read_one_table(
    *,
    proxy_first: bool,
) -> None:
    """A plain ``Branch`` owner and a plain ``ProxyBranch`` owner read one table, so they share a set."""

    class BranchOrder(OrderSet):
        class Meta:
            model = Branch
            fields = ["name"]

    def concrete() -> type[DjangoType]:
        class BranchOwnerType(DjangoType):
            class Meta:
                model = Branch
                fields = ("id", "name")
                orderset_class = BranchOrder

        return BranchOwnerType

    def proxy() -> type[DjangoType]:
        class ProxyOwnerType(DjangoType):
            class Meta:
                model = ProxyBranch
                fields = ("id", "name")
                orderset_class = BranchOrder

        return ProxyOwnerType

    owners = [declare() for declare in ((proxy, concrete) if proxy_first else (concrete, proxy))]
    finalize_django_types()
    assert BranchOrder._owner_definition is owners[0].__django_strawberry_definition__
    assert owners[1].__django_strawberry_definition__.orderset_class is BranchOrder


_SUBCLASS_OWNER_CASES = [
    pytest.param(hiding_first, base_on_hiding, id=f"{order}-{wiring}")
    for hiding_first, order in ((True, "hiding-declared-first"), (False, "plain-declared-first"))
    for base_on_hiding, wiring in ((True, "base-on-hiding"), (False, "subclass-on-hiding"))
]


@pytest.mark.parametrize(("hiding_first", "base_on_hiding"), _SUBCLASS_OWNER_CASES)
def test_an_orderset_subclass_binds_its_own_owner_apart_from_its_base(
    *,
    hiding_first: bool,
    base_on_hiding: bool,
) -> None:
    """Finalize binds a base orderset and its subclass to distinct own class slots in every declaration order.

    Consumer-visible ordering is covered by
    ``examples/fakeshop/test_query/test_library_api.py::test_a_set_and_its_subclass_read_their_own_bound_owner_over_http``.
    """

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["topic"]

    class SubShelfOrder(ShelfOrder):
        pass

    hiding_set, plain_set = (
        (ShelfOrder, SubShelfOrder) if base_on_hiding else (SubShelfOrder, ShelfOrder)
    )

    def hiding() -> type[DjangoType]:
        class HidingShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "topic")
                primary = True
                orderset_class = hiding_set

            @classmethod
            @override
            def get_queryset(
                cls,
                queryset: QuerySet[Shelf],
                info: object,
                **kwargs: object,
            ) -> QuerySet[Shelf]:
                return queryset.exclude(topic="secret")

        return HidingShelfType

    def plain() -> type[DjangoType]:
        class PlainShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "topic")
                primary = False
                orderset_class = plain_set

        return PlainShelfType

    declared = [declare() for declare in ((hiding, plain) if hiding_first else (plain, hiding))]
    hiding_type, plain_type = declared if hiding_first else declared[::-1]

    class ViaHidingBookOrder(OrderSet):
        shelf = RelatedOrder(hiding_set, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class ViaPlainBookOrder(OrderSet):
        shelf = RelatedOrder(plain_set, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class ViaHidingBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            primary = True
            orderset_class = ViaHidingBookOrder

    class ViaPlainBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            orderset_class = ViaPlainBookOrder

    finalize_django_types()
    assert ViaHidingBookType.__django_strawberry_definition__.orderset_class is ViaHidingBookOrder
    assert ViaPlainBookType.__django_strawberry_definition__.orderset_class is ViaPlainBookOrder
    assert read_attr(truth.class_dict(ShelfOrder)["_owner_definition"], "origin") is (
        hiding_type if base_on_hiding else plain_type
    )
    assert read_attr(truth.class_dict(SubShelfOrder)["_owner_definition"], "origin") is (
        plain_type if base_on_hiding else hiding_type
    )


def test_bind_orderset_owner_rejects_orderset_model_unrelated_to_owner() -> None:
    """A first bind whose orderset ``Meta.model`` is unrelated to the owner raises."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOwnerType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

    book_def = BookOwnerType.__django_strawberry_definition__
    with pytest.raises(ConfigurationError) as exc_info:
        _bind_orderset_owner(ShelfOrder, book_def)
    msg = str(exc_info.value)
    assert "ShelfOrder" in msg
    assert "Shelf" in msg  # orderset model
    assert "Book" in msg  # owner model
    # The rejected owner must NOT have been stored.
    assert getattr(ShelfOrder, "_owner_definition", None) is None


# ---------------------------------------------------------------------------
# Idempotent finalize after orderset wiring
# ---------------------------------------------------------------------------


def test_finalize_django_types_is_idempotent_after_orderset_wiring() -> None:
    """A second ``finalize_django_types()`` call is a no-op."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            orderset_class = BookOrder

    finalize_django_types()
    bound = BookOrder._owner_definition
    assert bound is BookType.__django_strawberry_definition__

    # Second call short-circuits via the ``registry.is_finalized()`` guard.
    finalize_django_types()
    assert BookOrder._owner_definition is bound


# ---------------------------------------------------------------------------
# Cooperates with Relay-Node owners
# ---------------------------------------------------------------------------


def test_phase_2_5_runs_under_relay_node_interface() -> None:
    """Phase 2.5 order binding cooperates with Relay-Node interface injection."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    assert registry.get(Genre) is GenreType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            interfaces = (relay.Node,)
            orderset_class = BookOrder

    finalize_django_types()

    assert BookOrder._owner_definition is BookType.__django_strawberry_definition__
    assert issubclass(BookType, relay.Node)
    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "BookOrderInputType")


# ---------------------------------------------------------------------------
# Subpass 2.5 -- every RelatedOrder a wired set reaches names a path of
# relations and a target its hop can scope by
# ---------------------------------------------------------------------------


class _OtUnmanagedModel(models.Model):
    """The abstract base whose ``Meta`` the multi-table children below subclass.

    Fakeshop's ``Venue`` line has no sibling children and no child keyed on a
    column of its own, so these models stand in for those shapes. ``managed =
    False``: the audit reads model metadata and no table.
    """

    class Meta:
        abstract = True
        app_label = "products"
        managed = False


class _OtRoot(_OtUnmanagedModel):
    """Root of a multi-table-inheritance line with two sibling children."""

    name: _Text = models.TextField()


class _OtLeft(_OtRoot):
    """A child keyed by its parent link (its key is ``_OtRoot.id``), with a unique ``tag`` of its own."""

    tag: _Text = models.TextField(unique=True)

    class Meta(_OtUnmanagedModel.Meta):
        pass


class _OtRight(_OtRoot):
    """The sibling of ``_OtLeft``, keyed by its own parent link onto the same column."""

    class Meta(_OtUnmanagedModel.Meta):
        pass


class _OtOwnKey(_OtRoot):
    """A child keyed on its own ``code``, so its parent link is not its primary key."""

    code: _Text = models.TextField(primary_key=True)

    class Meta(_OtUnmanagedModel.Meta):
        pass


class _OtHolder(_OtUnmanagedModel):
    """Relations onto each member of the ``_OtRoot`` line."""

    # DO_NOTHING, not CASCADE: these unmanaged models have no table, so a cascade would
    # make a delete of the target query a missing table.
    left: _FK[_OtLeft] = models.ForeignKey(
        _OtLeft,
        on_delete=models.DO_NOTHING,
        related_name="+",
    )
    tagged: _FK[_OtLeft] = models.ForeignKey(
        _OtLeft,
        on_delete=models.DO_NOTHING,
        to_field="tag",
        related_name="+",
    )
    loose_left: _FK[_OtLeft] = models.ForeignKey(
        _OtLeft,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="+",
    )
    lefts: models.ManyToManyField[_OtLeft, models.Model] = models.ManyToManyField(
        _OtLeft,
        related_name="+",
    )
    root: _FK[_OtRoot] = models.ForeignKey(
        _OtRoot,
        on_delete=models.DO_NOTHING,
        related_name="+",
    )
    own: _FK[_OtOwnKey] = models.ForeignKey(
        _OtOwnKey,
        on_delete=models.DO_NOTHING,
        related_name="+",
    )


def _column(model: type[models.Model]) -> str:
    """Return the name of ``model``'s first concrete column that is not a relation."""
    return next(field.name for field in model._meta.concrete_fields if not field.is_relation)


def _serving_type(
    model: type[models.Model],
    name: str,
    orderset: type[OrderSet] | None = None,
    *,
    primary: bool = True,
) -> type[DjangoType]:
    """Register a type for ``model`` exposing one column, wired to ``orderset`` when given."""
    meta: dict[str, object] = {"model": model, "fields": (_column(model),), "primary": primary}
    if orderset is not None:
        meta["orderset_class"] = orderset
    return type(name, (DjangoType,), {"Meta": type("Meta", (), meta)})


def _order_set(
    name: str,
    model: type[models.Model] | None,
    fields: list[str],
    **related: RelatedOrder,
) -> type[OrderSet]:
    """Declare an ``OrderSet`` named ``name`` (``Meta.model`` omitted when ``model`` is ``None``)."""
    meta: dict[str, object] = {"fields": fields}
    if model is not None:
        meta["model"] = model
    return type(
        name,
        (OrderSet,),
        {**related, "Meta": type("Meta", (), meta), "__module__": __name__},
    )


def _finalize_wired_declaration(
    owner_model: type[models.Model],
    field_name: str,
    set_model: type[models.Model] | None,
    type_model: type[models.Model] | None,
) -> None:
    """Wire ``OwnerOrder.rel = RelatedOrder(TargetOrder, field_name=...)`` and finalize.

    ``TargetOrder`` declares ``set_model`` (no ``Meta.model`` when ``None``) and is
    bound to ``TargetType``, a type of ``type_model``, or to no type when that is
    ``None``. ``OwnerOrder`` is the ``orderset_class`` of a type of ``owner_model``.
    """
    column_model = set_model or type_model or owner_model
    target = _order_set("TargetOrder", set_model, [_column(column_model)])
    owner = _order_set(
        "OwnerOrder",
        owner_model,
        [_column(owner_model)],
        rel=RelatedOrder(target, field_name=field_name),
    )
    _ = _serving_type(owner_model, "OwnerType", owner)
    if type_model is not None:
        _ = _serving_type(type_model, "TargetType", target, primary=type_model is not owner_model)
    finalize_django_types()


def _scope_refusal(field_name: str, reached: str, model: str) -> str:
    """The refusal of ``OwnerOrder.rel``, whose target is bound to ``TargetType`` of ``model``."""
    return (
        f"OrderSet OwnerOrder: RelatedOrder 'rel' has field_name '{field_name}', which reaches "
        f"{reached}, but its target OrderSet TargetOrder is bound to TargetType, whose model is "
        f"{model}. A RelatedOrder's target OrderSet must be bound to a type of {reached}, a "
        "proxy of it, or a multi-table-inheritance parent or child of it keyed by the same "
        "column."
    )


def _path_refusal(
    owner: str,
    attr: str,
    field_name: str,
    segment: str,
    model: str,
) -> str:
    """The refusal of a ``RelatedOrder`` whose ``field_name`` leaves the relations at ``segment``."""
    return (
        f"OrderSet {owner}: RelatedOrder '{attr}' has field_name '{field_name}', but "
        f"'{segment}' is not a relation of the model the path has reached from {model}. A "
        "RelatedOrder's field_name must name a path of relations."
    )


@pytest.mark.parametrize(
    (
        "owner_model",
        "field_name",
        "set_model",
        "type_model",
        "reached",
    ),
    [
        (
            Book,
            "shelf",
            DeskProfile,
            DeskProfile,
            "Shelf",
        ),
        (
            Shelf,
            "books",
            Genre,
            Genre,
            "Book",
        ),
        (
            Book,
            "genres",
            Shelf,
            Shelf,
            "Genre",
        ),
        (
            Book,
            "shelf__branch",
            Shelf,
            Shelf,
            "Branch",
        ),
        (
            Book,
            "shelf",
            None,
            DeskProfile,
            "Shelf",
        ),
        (
            _OtHolder,
            "left",
            _OtRight,
            _OtRight,
            "_OtLeft",
        ),
        (
            _OtHolder,
            "lefts",
            _OtRight,
            _OtRight,
            "_OtLeft",
        ),
        (
            _OtHolder,
            "left",
            _OtRoot,
            _OtRight,
            "_OtLeft",
        ),
        (
            _OtHolder,
            "root",
            _OtOwnKey,
            _OtOwnKey,
            "_OtRoot",
        ),
        (
            _OtHolder,
            "own",
            _OtRoot,
            _OtRoot,
            "_OtOwnKey",
        ),
    ],
    ids=[
        "unrelated-forward-foreign-key",
        "unrelated-reverse-foreign-key",
        "unrelated-many-to-many",
        "multi-hop-target-on-the-intermediate-model",
        "model-less-target-served-by-an-unrelated-type",
        "mti-sibling-across-a-foreign-key",
        "mti-sibling-across-a-many-to-many",
        "ancestor-set-bound-to-a-sibling-type",
        "descendant-keyed-on-its-own-column",
        "ancestor-of-a-descendant-keyed-on-its-own-column",
    ],
)
def test_related_order_whose_target_type_the_hop_cannot_scope_by_is_refused_at_finalize(
    owner_model: type[models.Model],
    field_name: str,
    set_model: type[models.Model] | None,
    type_model: type[models.Model],
    reached: str,
) -> None:
    """A target bound to a type whose rows are not the reached model's rows fails finalize.

    The compared model is the bound type's (``set_bound_type``), not the set's
    ``Meta.model``: a model-less set served by an unrelated type, and a set declaring
    the reached model's ancestor while bound to a sibling's type, are refused too.
    """
    with pytest.raises(ConfigurationError) as exc_info:
        _finalize_wired_declaration(owner_model, field_name, set_model, type_model)
    assert str(exc_info.value) == _scope_refusal(field_name, reached, truth.qualname(type_model))


@pytest.mark.parametrize(
    ("owner_model", "field_name", "set_model"),
    [
        (Book, "shelf", Shelf),
        (Shelf, "branch", ProxyBranch),
        (RepairTicket, "venue", LendingDesk),
        (RepairTicket, "venue", SelfServeDesk),
        (KioskFault, "kiosk", Venue),
        (KioskFault, "kiosk", LendingDesk),
        (Venue, "lendingdesk", Venue),
        (LendingDesk, "selfservedesk", LendingDesk),
        (_OtHolder, "tagged", _OtRoot),
        (_OtHolder, "loose_left", _OtRoot),
    ],
    ids=[
        "the-reached-model",
        "a-proxy-of-the-reached-model",
        "mti-child-across-a-forward-foreign-key",
        "mti-grandchild-across-a-forward-foreign-key",
        "mti-grandparent-across-a-forward-foreign-key",
        "mti-parent-across-a-forward-foreign-key",
        "mti-parent-across-a-reverse-one-to-one",
        "mti-parent-across-a-reverse-one-to-one-one-level-down",
        "mti-parent-lacking-the-to-field-column",
        "mti-parent-across-an-unconstrained-foreign-key",
    ],
)
def test_related_order_whose_target_type_shares_the_reached_rows_finalizes(
    owner_model: type[models.Model],
    field_name: str,
    set_model: type[models.Model],
) -> None:
    """A target bound to a type of the reached model, a proxy, or an MTI relative keyed alike binds.

    The hop's test keeps the scope rows whose key equals the joined row's, so an
    ancestor answers across a reverse one-to-one as across a forward key, across a
    ``to_field`` key onto a column only the child declares, and across a key no
    constraint holds: rows the filter side's link-column rule refuses.
    """
    _finalize_wired_declaration(owner_model, field_name, set_model, set_model)
    assert hasattr(sys.modules[INPUTS_MODULE_PATH], "OwnerOrderInputType")


@pytest.mark.parametrize(
    ("owner_model", "field_name", "set_model"),
    [(Book, "shelf", DeskProfile), (Shelf, "books", Genre)],
    ids=["forward-foreign-key", "reverse-foreign-key"],
)
def test_related_order_whose_target_is_bound_to_no_type_finalizes(
    owner_model: type[models.Model],
    field_name: str,
    set_model: type[models.Model],
) -> None:
    """An unbound target names no scope (the hop reads the relation's own type), so it binds."""
    _finalize_wired_declaration(owner_model, field_name, set_model, None)
    assert hasattr(sys.modules[INPUTS_MODULE_PATH], "OwnerOrderInputType")


def test_related_order_with_no_target_finalizes() -> None:
    """``RelatedOrder(None)`` expands nothing and scopes nothing."""
    owner = _order_set("OwnerOrder", Book, ["title"], rel=RelatedOrder(None, field_name="shelf"))
    _ = _serving_type(Book, "OwnerType", owner)
    finalize_django_types()
    assert hasattr(sys.modules[INPUTS_MODULE_PATH], "OwnerOrderInputType")


def test_related_order_cycle_ends_at_a_walked_set_and_model() -> None:
    """``BookOrder.shelf`` <-> ``ShelfOrder.books`` binds; the walk stops at a pair it has seen."""

    class ShelfOrder(OrderSet):
        books = RelatedOrder(None, field_name="books")

        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    ShelfOrder.related_orders["books"].orderset = BookOrder
    _ = _serving_type(Book, "BookType", BookOrder)
    _ = _serving_type(Shelf, "ShelfType")
    finalize_django_types()
    assert ShelfOrder.related_orders["books"].orderset is BookOrder
    assert hasattr(sys.modules[INPUTS_MODULE_PATH], "BookOrderInputType")


@pytest.mark.parametrize(
    "field_name",
    ["title", "nope", "shelf__code"],
    ids=["a-column", "a-name-the-model-lacks", "a-column-past-a-relation"],
)
def test_related_order_whose_field_name_is_not_a_path_of_relations_is_refused_at_finalize(
    field_name: str,
) -> None:
    """A wired set's ``RelatedOrder`` over a column or a missing name fails finalize."""
    segment = field_name.rsplit("__", 1)[-1]
    with pytest.raises(ConfigurationError) as exc_info:
        _finalize_wired_declaration(Book, field_name, Shelf, None)
    assert str(exc_info.value) == _path_refusal("OwnerOrder", "rel", field_name, segment, "Book")


@pytest.mark.parametrize(
    ("leaf_field_name", "expected"),
    [
        (
            "branch",
            (
                "OrderSet MiddleOrder: RelatedOrder 'leaf' has field_name 'branch', which reaches "
                "Branch, but its target OrderSet TargetOrder is bound to TargetType, whose model "
                "is DeskProfile. A RelatedOrder's target OrderSet must be bound to a type of "
                "Branch, a proxy of it, or a multi-table-inheritance parent or child of it keyed "
                "by the same column."
            ),
        ),
        ("code", _path_refusal("MiddleOrder", "leaf", "code", "code", "Shelf")),
    ],
    ids=["a-target-bound-to-an-unrelated-type", "a-field-name-naming-a-column"],
)
def test_a_declaration_two_sets_down_is_audited_from_the_model_the_outer_relation_reached(
    leaf_field_name: str,
    expected: str,
) -> None:
    """The audit walks from each wired set through every target, transitively.

    ``MiddleOrder`` is wired to no type: its declaration resolves against ``Shelf``,
    the model ``OwnerOrder.mid`` reached.
    """
    target = _order_set("TargetOrder", DeskProfile, ["code"])
    middle = _order_set(
        "MiddleOrder",
        Shelf,
        ["code"],
        leaf=RelatedOrder(target, field_name=leaf_field_name),
    )
    owner = _order_set("OwnerOrder", Book, ["title"], mid=RelatedOrder(middle, field_name="shelf"))
    _ = _serving_type(Book, "OwnerType", owner)
    _ = _serving_type(DeskProfile, "TargetType", target)
    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    assert str(exc_info.value) == expected


def test_an_unresolved_target_two_sets_down_raises_its_import_error_at_finalize() -> None:
    """A lazy target of a set no type is wired to raises the resolver's ``ImportError`` unchanged."""
    middle = _order_set(
        "MiddleOrder",
        Shelf,
        ["code"],
        leaf=RelatedOrder("NoSuchBranchOrder", field_name="branch"),
    )
    owner = _order_set("OwnerOrder", Book, ["title"], mid=RelatedOrder(middle, field_name="shelf"))
    _ = _serving_type(Book, "OwnerType", owner)
    with pytest.raises(ImportError) as exc_info:
        finalize_django_types()
    assert type(exc_info.value) is ImportError
    assert str(exc_info.value) == (
        f'Module "{__name__}" does not define a "NoSuchBranchOrder" attribute/class'
    )


def test_apply_refuses_a_target_reassigned_after_finalize_to_an_unscopable_set() -> None:
    """A ``.orderset`` swapped after the finalize audit is refused at the next apply."""
    target = _order_set("ShelfOrder", Shelf, ["code"])
    other = _order_set("TargetOrder", DeskProfile, ["code"])
    owner = _order_set("OwnerOrder", Book, ["title"], rel=RelatedOrder(target, field_name="shelf"))
    _ = _serving_type(Book, "OwnerType", owner)
    _ = _serving_type(Shelf, "ShelfType", target)
    _ = _serving_type(DeskProfile, "TargetType", other)
    finalize_django_types()
    owner.related_orders["rel"].orderset = other
    request = HttpRequest()
    request.user = AnonymousUser()
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    with pytest.raises(ConfigurationError) as exc_info:
        _ = owner.apply_sync({"rel": {"code": Ordering.ASC}}, Book.objects.all(), info)
    assert str(exc_info.value) == _scope_refusal("shelf", "Shelf", "DeskProfile")
