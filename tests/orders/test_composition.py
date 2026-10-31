"""Filter and order finalization shares input namespaces, caches, and the neutral related-set mixin.

A finalization pass publishes each family's input class in its own module,
materialization ledger, and factory cache. These identities are private
lifecycle state, which a response cannot expose. Consumer filter/order
composition is pinned by the live HTTP
``examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_and_order_compose``.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator

import pytest
from apps.library.models import Book

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.filters import (
    FilterSet,
    RelatedFilter,
    _helper_referenced_filtersets,
)
from django_strawberry_framework.filters.factories import FilterArgumentsFactory
from django_strawberry_framework.filters.inputs import (
    INPUTS_MODULE_PATH as FILTER_INPUTS_MODULE_PATH,
)
from django_strawberry_framework.filters.inputs import (
    _field_specs as _filter_field_specs,
)
from django_strawberry_framework.filters.inputs import (
    _materialized_names as _filter_materialized_names,
)
from django_strawberry_framework.orders import (
    OrderSet,
    RelatedOrder,
    _helper_referenced_ordersets,
)
from django_strawberry_framework.orders.factories import OrderArgumentsFactory
from django_strawberry_framework.orders.inputs import (
    INPUTS_MODULE_PATH as ORDER_INPUTS_MODULE_PATH,
)
from django_strawberry_framework.orders.inputs import (
    _field_specs as _order_field_specs,
)
from django_strawberry_framework.orders.inputs import (
    _materialized_names as _order_materialized_names,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.sets_mixins import LazyRelatedClassMixin
from django_strawberry_framework.utils._narrowing import read_attr


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Clear both subsystems' caches around every test.

    Mirrors ``tests/orders/test_finalizer.py::_isolate_registry`` extended
    to also reset the filter-side ledgers + factory caches so the
    composition test starts from a clean state on BOTH subsystems. The
    ``registry.clear()`` call already triggers
    ``clear_order_input_namespace()`` / ``clear_filter_input_namespace()``
    plus both ``_helper_referenced_*.clear()`` via the registered-callback replay
    (spec-028 Decision 9); the explicit per-ledger clears below pin the
    contract -- a regression in the ``registry.clear()`` lifecycle would
    surface as state bleed across tests, not as a silent test pass.
    """
    registry.clear()
    _filter_field_specs.clear()
    _filter_materialized_names.clear()
    _helper_referenced_filtersets.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()
    _order_field_specs.clear()
    _order_materialized_names.clear()
    _helper_referenced_ordersets.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()
    yield
    registry.clear()
    _filter_field_specs.clear()
    _filter_materialized_names.clear()
    _helper_referenced_filtersets.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()
    _order_field_specs.clear()
    _order_materialized_names.clear()
    _helper_referenced_ordersets.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()


def test_finalizer_materializes_both_input_families_in_their_own_namespaces() -> None:
    """One finalization publishes both families to their own module, ledger, and cache."""

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = BookFilter
            orderset_class = BookOrder

    assert registry.get(Book) is BookType

    finalize_django_types()

    filter_inputs_mod = sys.modules[FILTER_INPUTS_MODULE_PATH]
    order_inputs_mod = sys.modules[ORDER_INPUTS_MODULE_PATH]
    assert "BookFilterInputType" in _filter_materialized_names
    assert "BookOrderInputType" in _order_materialized_names
    assert (
        read_attr(filter_inputs_mod, "BookFilterInputType")
        is FilterArgumentsFactory.input_object_types["BookFilterInputType"]
    )
    assert (
        read_attr(order_inputs_mod, "BookOrderInputType")
        is OrderArgumentsFactory.input_object_types["BookOrderInputType"]
    )


def test_filter_and_order_share_lazy_related_class_mixin_via_neutral_module() -> None:
    """Both subsystems' ``Related*`` primitives inherit the shared mixin.

    Spec-028 pinned the mixin's neutral home at
    ``django_strawberry_framework/sets_mixins.py``. ``RelatedFilter``
    (declared at ``django_strawberry_framework.filters.base.RelatedFilter``)
    AND ``RelatedOrder`` (declared at
    ``django_strawberry_framework.orders.base.RelatedOrder``) BOTH inherit
    ``LazyRelatedClassMixin`` directly via sibling-imports from the
    neutral module -- the mixin object is shared, not duplicated. A
    future refactor that re-declares a sibling copy under either
    subsystem fails this MRO-identity pin loudly.
    """
    # Both ``Related*`` primitives inherit the shared mixin.
    assert LazyRelatedClassMixin in RelatedFilter.__mro__
    assert LazyRelatedClassMixin in RelatedOrder.__mro__
    # And it IS the same class object -- not a sibling-copy under each
    # subsystem.
    filter_mixin = next(
        cls for cls in RelatedFilter.__mro__ if cls.__name__ == "LazyRelatedClassMixin"
    )
    order_mixin = next(
        cls for cls in RelatedOrder.__mro__ if cls.__name__ == "LazyRelatedClassMixin"
    )
    assert filter_mixin is order_mixin is LazyRelatedClassMixin
