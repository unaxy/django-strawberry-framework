"""Optimizer tests for definition-order-independent DjangoType relation graphs.

The walker's select / prefetch verdict per relation after cyclic finalize, ``check_schema`` warning
absence, definition ``field_map`` identity, and annotation-only relation
metadata have no wire shape. Reverse-O2O JOIN SQL is
``examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_reverse_o2o_card_joins_in_root_sql``;
hooked-target Prefetch SQL is
``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_downgrade_to_prefetch_for_custom_get_queryset_in_http_query``.
"""

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
import strawberry
from apps.library.models import Book, Genre, MembershipCard, Patron
from apps.products.models import Category, Item
from django.db.models import Model, QuerySet
from typing_extensions import override

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types
from django_strawberry_framework.optimizer.nested_planner import (
    _target_has_custom_get_queryset,
)
from django_strawberry_framework.optimizer.selections import PYTHON_NAME_ATTR
from django_strawberry_framework.optimizer.walker import plan_optimizations
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def _sel(name: str, selections: list[object] | None = None) -> SimpleNamespace:
    """Build a synthetic selected field, published from the Python name ``name``."""
    return SimpleNamespace(
        name=name,
        alias=None,
        directives={},
        arguments={},
        selections=selections or [],
        **{PYTHON_NAME_ATTR: name},
    )


def _relation_plan(model: type[Model], name: str, child_column: str) -> str:
    """Return ``"select"`` or ``"prefetch"``: how the walker plans ``model.name``."""
    plan = plan_optimizations([_sel(name, [_sel(child_column)])], model)
    if plan.select_related:
        return "select"
    assert plan.prefetch_related
    return "prefetch"


def test_relation_plans_match_cardinality_after_finalization() -> None:
    """Cyclic finalization still plans each relation by its cardinality.

    The plan is not a wire value. Reverse-O2O JOIN SQL is
    ``examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_reverse_o2o_card_joins_in_root_sql``.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    class MembershipCardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode", "patron")

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name", "card")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "genres")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name", "books")

    finalize_django_types()
    # The registry holds the types; the walk reads them through it.
    del CategoryType, ItemType, MembershipCardType, PatronType, BookType, GenreType

    assert _relation_plan(Item, "category", "name") == "select"
    assert _relation_plan(Category, "items", "name") == "prefetch"
    assert _relation_plan(MembershipCard, "patron", "name") == "select"
    assert _relation_plan(Patron, "card", "barcode") == "select"
    assert _relation_plan(Book, "genres", "name") == "prefetch"
    assert _relation_plan(Genre, "books", "title") == "prefetch"


def test_custom_get_queryset_verdict_falls_back_to_the_target_class() -> None:
    """With no captured definition, the target class's own report decides the downgrade.

    A target that overrides ``get_queryset`` turns a forward FK into a
    ``Prefetch``. The walk always passes a definition; that captured arm is
    executed by
    ``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_downgrade_to_prefetch_for_custom_get_queryset_in_http_query``.
    """

    class FilteredCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @override
        @classmethod
        def get_queryset(
            cls,
            queryset: QuerySet[Category],
            info: strawberry.Info,
        ) -> QuerySet[Category]:
            return queryset

    assert _target_has_custom_get_queryset(FilteredCategoryType) is True


def test_check_schema_returns_no_warnings_for_registered_cyclic_targets() -> None:
    """The schema audit accepts reachable cyclic relations when every target is registered."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    assert DjangoOptimizerExtension.check_schema(schema) == []


def test_definition_field_map_carries_optimizer_metadata() -> None:
    """Definition-owned field metadata is the optimizer's canonical source."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = registry.get_definition(CategoryType)

    assert definition is not None
    assert sorted(definition.field_map) == ["id", "items", "name"]


def test_annotation_only_relation_override_still_plans_prefetch() -> None:
    """Annotation-only relation overrides keep optimizer-visible relation metadata."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        items: list[ItemType]

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    assert registry.get(Category) is CategoryType

    finalize_django_types()

    plan = plan_optimizations([_sel("items", selections=[_sel("name")])], Category)

    assert plan.select_related == ()
    assert getattr(plan.prefetch_related[0], "prefetch_to", None) == "items"
    assert plan.planned_resolver_keys == ("CategoryType.items@items",)
