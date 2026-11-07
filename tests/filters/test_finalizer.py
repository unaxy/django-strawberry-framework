"""Finalizer tests for filter binding, owner-aware materialization, and orphan validation.

Covers:

- ``Meta.filterset_class`` validation (positive + negative).
- Four-subpass ordering (every owner bound BEFORE any
  ``get_filters()`` runs across the whole registry).
- Strict multi-owner reuse: divergent own-PK Relay identity or custom
  ``get_queryset`` rejected; owners agreeing on every axis accepted; idempotent
  re-bind of the same ``(filterset, definition)`` pair accepted; owners over
  different tables (a multi-table-inheritance parent and child) rejected and
  owners over one model or its proxies accepted, in both declaration orders.
- Materialization idempotency under the ``(name, cls)`` contract.
- Orphan ``filter_input_type`` references rejected with the spec-pinned
  actionable message.
- ``registry.clear()`` co-clears the input-class namespace, the
  ``_helper_referenced_filtersets`` set, and the ``_field_specs`` map.
- ``registry.clear()`` runs without ``ImportError`` when the filters
  package was never imported (subprocess test pins the cycle-safe
  contract per spec-027 Decision 9).
- Unresolved ``RelatedFilter`` propagates as ``ConfigurationError``.
- A declared filter a deep copy refuses fails the build naming its set and
  attribute (a served set's by the subpass-1.5 probe, an unserved
  ``RelatedFilter`` child's by the expansion copy).
- A declared leaf whose ``field_name`` and ``lookup_expr`` Django resolves on no
  queryset is refused when its set publishes, under every serving shape, while the
  shapes Django resolves on some queryset (a name past a relation, a to-many key its
  target's key reads, a range applied as a relation's bounds) build.

Bound and unbound filtersets answering requests live in ``test_query/``.
``test_filter_declarations_api.py`` owns copyable callable and widget controls
and independently owned enums. This file keeps exact class-owner slots,
finalize-time refusal and ordering, orphan rejection, and registry reset.
"""

from __future__ import annotations

import contextlib
import copy
import functools
import sys
import threading
from collections import OrderedDict
from collections.abc import Callable, Generator, Iterator, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, NoReturn

import pytest
import strawberry
from apps.kanban.models import Actor, Card, CardItem, CardPathLink
from apps.library.models import (
    Book,
    Branch,
    Genre,
    LendingDesk,
    Loan,
    Patron,
    PatronProfile,
    ProxyBranch,
    Shelf,
    TaggedItem,
    Venue,
)
from apps.scalars.models import NullableScalarSpecimen, ScalarSpecimen
from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches
from django.db.models import (
    BigIntegerField,
    DateTimeField,
    F,
    ForeignKey,
    IntegerField,
    Lookup,
    Model,
    QuerySet,
    TextField,
    Transform,
)
from django.db.models import Field as ModelFieldClass
from django.db.models.functions import Abs, ExtractHour
from django.db.models.lookups import GreaterThan, IStartsWith
from django.http import HttpRequest
from django.test import override_settings
from django.test.utils import register_lookup
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy
from django_filters import (
    BooleanFilter,
    CharFilter,
    Filter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    NumberFilter,
)
from django_filters.filters import BaseRangeFilter
from django_filters.filters import RangeFilter as DjangoFilterRangeFilter
from strawberry import relay
from typing_extensions import override

if TYPE_CHECKING:
    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.models.sql.compiler import SQLCompiler, _AsSqlType
    from typing_extensions import TypeIs

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoListField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError, LookupValidationError
from django_strawberry_framework.filters import (
    FilterInput,
    FilterSet,
    GlobalIDFilter,
    ListFilter,
    RangeFilter,
    RelatedFilter,
    _connection_served_filtersets,
    _helper_referenced_filtersets,
    filter_input_type,
)
from django_strawberry_framework.filters.base import (
    IntegerRangeFilter,
    _lookup_operand,
    _model_lookup_operand,
)
from django_strawberry_framework.filters.factories import FilterArgumentsFactory
from django_strawberry_framework.filters.inputs import (
    INPUTS_MODULE_PATH,
    _field_specs,
    _materialized_names,
    clear_filter_input_namespace,
    materialize_input_class,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.definition import DjangoTypeDefinition
from django_strawberry_framework.types.finalizer import (
    _audit_globalid_filter_strategies,
    _bind_filterset_owner,
)
from django_strawberry_framework.types.relay import apply_interfaces
from django_strawberry_framework.utils import querysets as querysets_module
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import is_dict, is_str, read_attr, require
from django_strawberry_framework.utils.permissions import set_bound_definition
from django_strawberry_framework.utils.typing import object_result
from tests._cleaned_filter_sets import cleaned_specimen
from tests._idioms import json_at, json_list, saved_pk
from tests._subprocess import run_in_fresh_process


def _is_filter_map(value: object) -> TypeIs[OrderedDict[str, Filter]]:
    """Whether ``value`` is the ``OrderedDict`` of named filters ``get_filters`` returns."""
    return (
        is_dict(value)
        and isinstance(value, OrderedDict)
        and all(is_str(name) and isinstance(leaf, Filter) for name, leaf in value.items())
    )


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    registry.clear()
    _field_specs.clear()
    _helper_referenced_filtersets.clear()
    _materialized_names.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()
    yield
    registry.clear()
    _field_specs.clear()
    _helper_referenced_filtersets.clear()
    _materialized_names.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()


# ---------------------------------------------------------------------------
# Subpass ordering.
# ---------------------------------------------------------------------------


def test_phase_2_5_binds_all_owners_before_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Subpass 1 must complete across both owners before any ``get_filters`` runs.

    Pre-declares ``GenreFilter`` so ``BookFilter`` can reference it as a
    class object (not a forward-string - that would force resolution
    against the test function's local scope, which the resolver
    cannot reach). Instruments ``GenreFilter.get_filters`` so each
    invocation records whether ``_owner_definition`` was already set.
    Without the four-subpass discipline an observation would land
    ``False`` when ``BookFilter.get_filters`` expanded
    ``RelatedFilter(GenreFilter)`` before ``GenreType`` was iterated.
    """

    class GenreFilter(FilterSet):
        class Meta:
            model = Genre
            fields = {"name": ["exact"]}

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    observations: list[bool] = []
    original_get_filters = GenreFilter.get_filters.__func__

    @classmethod
    def instrumented_get_filters(cls: type[FilterSet]) -> OrderedDict[str, Filter]:
        observations.append(cls._owner_definition is not None)
        return require(object_result(original_get_filters, cls), _is_filter_map)

    monkeypatch.setattr(GenreFilter, "get_filters", instrumented_get_filters)

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            filterset_class = BookFilter

    assert registry.get(Book) is BookType

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            filterset_class = GenreFilter

    assert registry.get(Genre) is GenreType

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")
            filterset_class = ShelfFilter

    assert registry.get(Shelf) is ShelfType

    finalize_django_types()

    assert observations, "GenreFilter.get_filters was never called"
    assert all(observations), (
        "GenreFilter._owner_definition was unset during get_filters; "
        "subpass 1 did not complete across all owners before subpass 2 ran."
    )


# ---------------------------------------------------------------------------
# Strict multi-owner reuse.
# ---------------------------------------------------------------------------


def test_globalid_strategy_audit_refuses_a_filterset_with_no_bound_owner() -> None:
    """The audit reads only wired filtersets; one bound to no owner is a typed error."""

    class UnboundBookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    with pytest.raises(TypeError, match="expected an instance of"):
        _audit_globalid_filter_strategies([UnboundBookFilter])


def test_phase_2_5_rejects_multi_owner_with_diverging_pk_identity() -> None:
    """Two REAL owners diverging on own-PK Relay identity are rejected end-to-end.

    Exercises the own-PK Relay-identity axis, one of the three owner-dependent
    axes of the strict multi-owner check: one Relay-shaped owner and one plain owner share a
    single ``FilterSet``, so the shared filterset's own ``id`` filter
    would resolve to a GlobalID under one owner but a scalar under the
    other. ``finalize_django_types()`` must reject the second binding via
    ``_check_filterset_owner_pk_identity`` rather than silently pinning
    the first owner.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class RelayBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            interfaces = (relay.Node,)
            primary = True
            filterset_class = BookFilter

    assert registry.get(Book) is RelayBookType

    class PlainBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = BookFilter

    assert registry.model_for_type(PlainBookType) is Book

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "own-primary-key Relay identity" in msg
    assert "BookFilter" in msg
    assert "RelayBookType" in msg
    assert "PlainBookType" in msg


def test_phase_2_5_rejects_multi_owner_with_diverging_get_queryset() -> None:
    """Two owners of one filterset with divergent ``get_queryset`` are rejected end-to-end.

    ``get_queryset`` visibility is one of the three owner-dependent axes (beside
    the table and own-PK Relay identity): when the shared filterset is a ``RelatedFilter``
    target, ``FilterSet._target_type_for_related_filter`` scopes the related
    branch through the BOUND owner's ``get_queryset``, but only the FIRST binding
    is stored. Two owners with different ``get_queryset`` hooks would therefore
    scope the branch by whichever owner finalized first - a silent, registration-
    order-dependent row-visibility leak. ``finalize_django_types()`` must reject
    the second binding via ``_check_set_owner_get_queryset_safety`` rather
    than silently pinning the first owner's visibility.

    Both owners are plain (non-Relay) so the own-PK axis agrees and this test
    isolates the ``get_queryset`` axis; they diverge only on ``get_queryset``.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class PermissiveBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            primary = True
            filterset_class = BookFilter

    assert registry.get(Book) is PermissiveBookType

    class RestrictiveBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = BookFilter

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Book], info: object) -> QuerySet[Book]:
            # A distinct visibility hook: excludes a subset the permissive owner shows.
            return queryset.exclude(title="secret")

    assert registry.model_for_type(RestrictiveBookType) is Book

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "get_queryset visibility" in msg
    assert "BookFilter" in msg
    assert "PermissiveBookType" in msg
    assert "RestrictiveBookType" in msg


def test_phase_2_5_rejects_multi_owner_sharing_one_custom_get_queryset() -> None:
    """Two owners sharing ONE custom ``get_queryset`` (via a common base) are rejected.

    Function identity is NOT visibility equivalence. Both owners inherit the SAME
    ``get_queryset`` function object from ``_VisibleBooksBase``, so a coarse
    ``__func__`` identity compare would call the pairing safe - but the classmethod
    runs with each owner's own ``cls``. A ``cls``-parameterized hook
    (``queryset.filter(kind=cls.KIND)``) would then yield different rows per owner
    while sharing one function, reintroducing the registration-order row-leak the
    axis exists to close. Finalize must fail CLOSED on any custom ``get_queryset``
    rather than infer behavioral equivalence from function identity.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class _VisibleBooksBase(DjangoType):
        # A DjangoType base WITHOUT ``Meta`` is an abstract, unregistered base
        # (``__init_subclass__`` early-returns on ``meta is None``); both concrete
        # owners inherit this one ``get_queryset`` function.
        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Book], info: object) -> QuerySet[Book]:
            # cls-parameterized in spirit: the hook body can branch on ``cls`` even
            # when the function object is shared, so the shared filterset's
            # related-branch visibility is owner-dependent despite the identity.
            return queryset.exclude(title="secret")

    class PrimaryBookType(_VisibleBooksBase):
        class Meta:
            model = Book
            fields = ("id", "title")
            primary = True
            filterset_class = BookFilter

    assert registry.get(Book) is PrimaryBookType

    class SecondaryBookType(_VisibleBooksBase):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = BookFilter

    assert registry.model_for_type(SecondaryBookType) is Book

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "get_queryset visibility" in msg
    assert "BookFilter" in msg
    assert "PrimaryBookType" in msg
    assert "SecondaryBookType" in msg


@pytest.mark.parametrize("parent_first", [True, False], ids=["parent-first", "child-first"])
def test_phase_2_5_rejects_multi_owner_reading_different_tables(*, parent_first: bool) -> None:
    """A ``Venue`` owner and a ``LendingDesk`` owner of one ``FilterSet`` are refused in both orders.

    A path re-entering the set's table reads the type it is bound to, and
    multi-table-inheritance parent and child are different tables: bound to the
    parent owner a re-entered ``Venue`` row reads that owner, bound to the child
    it reads ``Venue``'s primary. Both owners are plain (non-Relay) and keep the
    identity hook, so only the table axis refuses them.
    """

    class VenueFilter(FilterSet):
        class Meta:
            model = Venue
            fields = {"name": ["exact"]}

    def parent() -> type[DjangoType]:
        class VenueOwnerType(DjangoType):
            class Meta:
                model = Venue
                fields = ("id", "name")
                filterset_class = VenueFilter

        return VenueOwnerType

    def child() -> type[DjangoType]:
        class DeskOwnerType(DjangoType):
            class Meta:
                model = LendingDesk
                fields = ("name",)
                filterset_class = VenueFilter

        return DeskOwnerType

    for declare in (parent, child) if parent_first else (child, parent):
        declare()
    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert msg.startswith("FilterSet ")
    assert "cannot bind to multiple owners over different tables" in msg
    assert "VenueOwnerType (model Venue)" in msg
    assert "DeskOwnerType (model LendingDesk)" in msg
    assert "Declare separate FilterSet subclasses per owner." in msg


@pytest.mark.parametrize("proxy_first", [True, False], ids=["proxy-first", "concrete-first"])
def test_phase_2_5_accepts_multi_owner_reading_one_table(*, proxy_first: bool) -> None:
    """A plain ``Branch`` owner and a plain ``ProxyBranch`` owner read one table, so they share a set."""

    class BranchFilter(FilterSet):
        class Meta:
            model = Branch
            fields = {"name": ["exact"]}

    def concrete() -> type[DjangoType]:
        class BranchOwnerType(DjangoType):
            class Meta:
                model = Branch
                fields = ("id", "name")
                filterset_class = BranchFilter

        return BranchOwnerType

    def proxy() -> type[DjangoType]:
        class ProxyOwnerType(DjangoType):
            class Meta:
                model = ProxyBranch
                fields = ("id", "name")
                filterset_class = BranchFilter

        return ProxyOwnerType

    owners = [declare() for declare in ((proxy, concrete) if proxy_first else (concrete, proxy))]
    finalize_django_types()
    assert BranchFilter._owner_definition is owners[0].__django_strawberry_definition__
    assert owners[1].__django_strawberry_definition__.filterset_class is BranchFilter


@pytest.mark.django_db
@pytest.mark.parametrize("proxy_first", [True, False], ids=["proxy-first", "concrete-first"])
def test_phase_2_5_accepts_one_table_owners_sharing_a_proxy_named_related_filter(
    *,
    proxy_first: bool,
) -> None:
    """A ``Branch`` and a ``ProxyBranch`` owner share a set whose ``RelatedFilter`` attr only the proxy has.

    ``proxy_tags = RelatedFilter(TagFilter, field_name="tags")`` is named like
    ``ProxyBranch.proxy_tags`` but walks ``tags``, the relation both models share.
    The declared attribute name is not an owner-dependent axis: the branch's target
    is the shared relation's target model, so both declaration orders finalize, and
    the set filters by tag through each owner's rows.
    """

    class TaggedItemType(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "tag")

    class TagFilter(FilterSet):
        class Meta:
            model = TaggedItem
            fields = {"tag": ["exact"]}

    class BranchFilter(FilterSet):
        proxy_tags = RelatedFilter(TagFilter, field_name="tags")

        class Meta:
            model = Branch
            fields = {"name": ["exact"]}

    def concrete() -> type[DjangoType]:
        class BranchOwnerType(DjangoType):
            class Meta:
                model = Branch
                fields = ("id", "name")
                filterset_class = BranchFilter

        return BranchOwnerType

    def proxy() -> type[DjangoType]:
        class ProxyOwnerType(DjangoType):
            class Meta:
                model = ProxyBranch
                fields = ("id", "name")
                filterset_class = BranchFilter

        return ProxyOwnerType

    declared = [declare() for declare in ((proxy, concrete) if proxy_first else (concrete, proxy))]
    concrete_type, proxy_type = declared[::-1] if proxy_first else declared
    finalize_django_types()
    assert registry.get(TaggedItem) is TaggedItemType
    assert BranchFilter._owner_definition is declared[0].__django_strawberry_definition__

    def via_concrete(info: strawberry.Info, tag: str) -> list[Branch]:
        rows = BranchFilter.apply_sync({"proxy_tags": {"tag": tag}}, Branch.objects.all(), info)
        return list(rows.order_by("name"))

    def via_proxy(info: strawberry.Info, tag: str) -> list[ProxyBranch]:
        rows = BranchFilter.apply_sync(
            {"proxy_tags": {"tag": tag}},
            ProxyBranch.objects.all(),
            info,
        )
        return list(rows.order_by("name"))

    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {
                    "via_concrete": list[concrete_type],
                    "via_proxy": list[proxy_type],
                },
                "via_concrete": strawberry.field(resolver=via_concrete),
                "via_proxy": strawberry.field(resolver=via_proxy),
            },
        ),
    )
    tagged = Branch.objects.create(name="tagged")
    other = Branch.objects.create(name="other")
    branch_type = ContentType.objects.get_for_model(Branch)
    TaggedItem.objects.create(tag="t", content_type=branch_type, object_id=saved_pk(tagged))
    TaggedItem.objects.create(tag="u", content_type=branch_type, object_id=saved_pk(other))
    result = strawberry.Schema(query=query, config=strawberry_config()).execute_sync(
        '{ viaConcrete(tag: "t") { name } viaProxy(tag: "t") { name } }',
        context_value=HttpRequest(),
    )
    assert result.errors is None, result.errors
    assert result.data == {"viaConcrete": [{"name": "tagged"}], "viaProxy": [{"name": "tagged"}]}


_SUBCLASS_OWNER_CASES = [
    pytest.param(hiding_first, base_on_hiding, id=f"{order}-{wiring}")
    for hiding_first, order in ((True, "hiding-declared-first"), (False, "plain-declared-first"))
    for base_on_hiding, wiring in ((True, "base-on-hiding"), (False, "subclass-on-hiding"))
]


@pytest.mark.parametrize(("hiding_first", "base_on_hiding"), _SUBCLASS_OWNER_CASES)
def test_a_filterset_subclass_binds_its_own_owner_apart_from_its_base(
    *,
    hiding_first: bool,
    base_on_hiding: bool,
) -> None:
    """Finalize binds a base filterset and subclass to distinct own class slots.

    Consumer-visible filtering is covered by
    ``examples/fakeshop/test_query/test_library_api.py::test_a_set_and_its_subclass_read_their_own_bound_owner_over_http``.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"topic": ["exact"]}

    class SubShelfFilter(ShelfFilter):
        pass

    hiding_set, plain_set = (
        (ShelfFilter, SubShelfFilter) if base_on_hiding else (SubShelfFilter, ShelfFilter)
    )

    def hiding() -> type[DjangoType]:
        class HidingShelfType(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "topic")
                primary = True
                filterset_class = hiding_set

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
                filterset_class = plain_set

        return PlainShelfType

    declared = [declare() for declare in ((hiding, plain) if hiding_first else (plain, hiding))]
    hiding_type, plain_type = declared if hiding_first else declared[::-1]

    class ViaHidingBookFilter(FilterSet):
        shelf = RelatedFilter(hiding_set, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ViaPlainBookFilter(FilterSet):
        shelf = RelatedFilter(plain_set, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ViaHidingBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            primary = True
            filterset_class = ViaHidingBookFilter
            interfaces = (relay.Node,)

    class ViaPlainBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = ViaPlainBookFilter
            interfaces = (relay.Node,)

    finalize_django_types()
    assert (
        ViaHidingBookType.__django_strawberry_definition__.filterset_class is ViaHidingBookFilter
    )
    assert ViaPlainBookType.__django_strawberry_definition__.filterset_class is ViaPlainBookFilter
    shelf_owner = truth.class_dict(ShelfFilter)["_owner_definition"]
    sub_shelf_owner = truth.class_dict(SubShelfFilter)["_owner_definition"]
    assert isinstance(shelf_owner, DjangoTypeDefinition)
    assert isinstance(sub_shelf_owner, DjangoTypeDefinition)
    assert shelf_owner.origin is (hiding_type if base_on_hiding else plain_type)
    assert sub_shelf_owner.origin is (plain_type if base_on_hiding else hiding_type)


@pytest.mark.parametrize(
    "subclass_target",
    [
        pytest.param(True, id="unwired-subclass-of-a-bound-filterset"),
        pytest.param(False, id="unrelated-unwired-filterset"),
    ],
)
def test_an_unwired_filterset_keeps_its_own_unbound_owner_slot(
    *,
    subclass_target: bool,
) -> None:
    """An unwired subclass has no own owner slot despite its bound base.

    Exact class-dictionary ownership stays private. Related-filter rowsets,
    key scalars and reentry visibility live in
    ``test_library_api.py::test_an_unwired_filter_subclass_answers_like_an_unrelated_unwired_set_over_http``.
    """

    class BackBookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    target_fields = {
        "topic": ["exact"],
        "id": ["exact"],
        "branch": ["exact"],
        "branch__shelves__topic": ["exact"],
    }

    class ShelfFilter(FilterSet):
        back = RelatedFilter(BackBookFilter, field_name="branch__shelves__books")

        class Meta:
            model = Shelf
            fields = target_fields

    class SubShelfFilter(ShelfFilter):
        pass

    class LoneShelfFilter(FilterSet):
        back = RelatedFilter(BackBookFilter, field_name="branch__shelves__books")

        class Meta:
            model = Shelf
            fields = target_fields

    target = SubShelfFilter if subclass_target else LoneShelfFilter

    class BranchType(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class HidingShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "topic")
            primary = True
            interfaces = (relay.Node,)

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Shelf],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Shelf]:
            return queryset.exclude(topic="secret")

    class PlainShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "topic")
            interfaces = (relay.Node,)
            filterset_class = ShelfFilter

    class ViaTargetBookFilter(FilterSet):
        shelf = RelatedFilter(target, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ViaTargetBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = ViaTargetBookFilter
            interfaces = (relay.Node,)

    finalize_django_types()
    assert (
        read_attr(truth.class_dict(ShelfFilter)["_owner_definition"], "origin") is PlainShelfType
    )
    assert "_owner_definition" not in truth.class_dict(target)
    assert registry.get(Shelf) is HidingShelfType
    assert registry.get(Branch) is BranchType
    assert registry.get(Book) is ViaTargetBookType


@pytest.mark.parametrize(
    "read_first",
    [
        pytest.param(True, id="column-in-meta-fields"),
        pytest.param(False, id="column-filtered-only"),
    ],
)
def test_a_meta_named_type_names_a_choice_enum_alike_whichever_side_reads_first(
    *,
    read_first: bool,
) -> None:
    """A ``Meta.name``'d type's choice enum carries its published name from either side.

    With ``condition`` in ``Meta.fields`` the read annotation builds the enum when the
    class is declared, before its filterset builds a leaf; without it the filterset's
    owned leaf builds it at schema build. Both name it after the published ``Meta.name``,
    never the Python class name, so the enum's name does not hang on which side reads
    the column first.
    """

    class PublishedShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"condition": ["exact"]}

    class ShelfClassType(DjangoType):
        class Meta:
            model = Shelf
            name = "PublishedShelf"
            fields = ("id", "topic", "condition") if read_first else ("id", "topic")
            filterset_class = PublishedShelfFilter
            interfaces = (relay.Node,)

    finalize_django_types()
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": DjangoConnection[ShelfClassType]},
                "shelves": DjangoConnectionField(ShelfClassType),
            },
        ),
    )
    schema = strawberry.Schema(query=query, config=strawberry_config())
    assert schema.get_type_by_name("PublishedShelfConditionEnum") is not None
    assert schema.get_type_by_name("ShelfClassTypeConditionEnum") is None


def test_two_unwired_targets_over_same_named_choice_columns_build_one_schema() -> None:
    """Two unwired sets over same-named choice columns of two models mint two enums.

    ``CardPathLink.kind`` and ``Actor.kind`` are choice columns no type exposes (their
    types publish other columns), each reached only through a ``RelatedFilter`` target
    no type wires, and
    ``HIDE_FLAT_FILTERS`` keeps both roots from building them as flat leaves. Each
    target names its enum after its own class, so the schema publishes both instead of
    two enums under one name.
    """
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"HIDE_FLAT_FILTERS": True}):

        class PathLinkFilter(FilterSet):
            class Meta:
                model = CardPathLink
                fields = {"kind": ["exact"]}

        class ActorFilter(FilterSet):
            class Meta:
                model = Actor
                fields = {"kind": ["exact"]}

        class LinkedCardFilter(FilterSet):
            path_links = RelatedFilter(PathLinkFilter, field_name="path_links")

            class Meta:
                model = Card
                fields = {"title": ["exact"]}

        class VerifiedItemFilter(FilterSet):
            verified_by = RelatedFilter(ActorFilter, field_name="verified_by")

            class Meta:
                model = CardItem
                fields = {"text": ["exact"]}

        class LinkedCardType(DjangoType):
            class Meta:
                model = Card
                fields = ("id", "title")
                filterset_class = LinkedCardFilter
                interfaces = (relay.Node,)

        class VerifiedItemType(DjangoType):
            class Meta:
                model = CardItem
                fields = ("id", "text")
                filterset_class = VerifiedItemFilter
                interfaces = (relay.Node,)

        class PathLinkType(DjangoType):
            class Meta:
                model = CardPathLink
                fields = ("id",)

        class ActorType(DjangoType):
            class Meta:
                model = Actor
                fields = ("id", "key")

        finalize_django_types()
        assert registry.get(CardPathLink) is PathLinkType
        assert registry.get(Actor) is ActorType
        query = strawberry.type(
            type(
                "Query",
                (),
                {
                    "__annotations__": {
                        "cards": DjangoConnection[LinkedCardType],
                        "items": DjangoConnection[VerifiedItemType],
                    },
                    "cards": DjangoConnectionField(LinkedCardType),
                    "items": DjangoConnectionField(VerifiedItemType),
                },
            ),
        )
        schema = strawberry.Schema(query=query, config=strawberry_config())
    assert schema.get_type_by_name("PathLinkFilterKindEnum") is not None
    assert schema.get_type_by_name("ActorFilterKindEnum") is not None


def test_phase_2_5_accepts_multi_owner_agreeing_on_every_axis() -> None:
    """Two distinct owner definitions agreeing on every axis share one ``FilterSet``.

    The accept companion to
    `tests/filters/test_finalizer.py::test_phase_2_5_rejects_multi_owner_with_diverging_pk_identity`.
    ``test_phase_2_5_accepts_idempotent_rebind_of_same_filterset_owner_pair``
    only exercises the ``previous is definition`` identity short-circuit in
    ``_bind_filterset_owner``; this test binds two distinct
    ``DjangoTypeDefinition`` instances, so the second runs
    ``_check_filterset_owner_axes`` and passes it.

    Setup: two ``DjangoType``s registered against ``Book`` (one primary,
    one secondary per ``Meta.primary``), both plain, both with the identity
    ``get_queryset``, sharing one ``BookFilter`` that declares
    ``shelf = RelatedFilter(ShelfFilter, field_name="shelf")``. They share
    the table, own-PK Relay identity and visibility. Assert: no raise, and
    the ``_owner_definition`` slot stores the FIRST binding
    (`django_strawberry_framework/types/finalizer.py::_bind_filterset_owner`).
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

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

    class PrimaryBookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            primary = True
            filterset_class = BookFilter

    class SecondaryBookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            filterset_class = BookFilter

    # Two distinct definitions both bind the same BookFilter; the second
    # passes every owner-dependent axis check.
    finalize_django_types()

    primary_definition = PrimaryBookType.__django_strawberry_definition__
    secondary_definition = SecondaryBookType.__django_strawberry_definition__
    # The two owner definitions are distinct (NOT the same identity);
    # the axis checks - not the ``previous is definition``
    # short-circuit - are what accepted the second binding.
    assert primary_definition is not secondary_definition
    # The ``_owner_definition`` slot stores the FIRST binding
    # (`django_strawberry_framework/types/finalizer.py::_bind_filterset_owner`).
    # Iteration order from ``registry.iter_definitions()`` is registration
    # order, so ``PrimaryBookType`` (declared first) wins.
    assert BookFilter._owner_definition is primary_definition


def test_phase_2_5_accepts_idempotent_rebind_of_same_filterset_owner_pair() -> None:
    """Re-binding the same ``(filterset, definition)`` pair is a no-op."""

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

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
            filterset_class = BookFilter

    finalize_django_types()
    bound = BookFilter._owner_definition
    assert bound is BookType.__django_strawberry_definition__

    # A second finalize is a no-op (registry.is_finalized() guard).
    finalize_django_types()
    assert BookFilter._owner_definition is bound


# ---------------------------------------------------------------------------
# Orphan ``filter_input_type`` references.
# ---------------------------------------------------------------------------


def test_orphan_filter_input_type_reference_raises_at_finalize() -> None:
    """A ``filter_input_type(StandaloneFilter)`` without ``Meta.filterset_class`` raises."""

    class StandaloneFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    # Helper-reference the filterset without wiring it to any DjangoType.
    filter_input_type(StandaloneFilter)

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

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "StandaloneFilter" in msg
    assert "is referenced via FilterInput[...] / filter_input_type(...) but never" in msg
    assert "filterset_class = StandaloneFilter" in msg


def test_phase_2_5_orphan_check_runs_before_materialization() -> None:
    """Orphan failure leaves no partial state in the materialization ledgers.

    Subpass 3 (orphan validation) runs BEFORE subpass 4
    (materialization), so a failed finalize does not leave wired
    filtersets' input classes registered in ``_materialized_names`` /
    ``FilterArgumentsFactory.input_object_types``; otherwise a re-run of
    ``finalize_django_types()`` after fixing the orphan would see stale
    ledger entries from the failed attempt.
    """

    class WiredFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class StandaloneFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    # The wired filterset would normally be materialized; the
    # standalone filterset is an orphan that must trigger the failure.
    filter_input_type(StandaloneFilter)

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
            filterset_class = WiredFilter

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError):
        finalize_django_types()

    # No input class registered for either filterset; the wired one's
    # would-be input type stayed un-materialized because the orphan
    # check halted the pass before subpass 4 ran.
    wired_input_name = f"{WiredFilter.__name__}InputType"
    assert wired_input_name not in FilterArgumentsFactory.input_object_types
    assert wired_input_name not in _materialized_names


def test_phase_2_5_orphan_validation_lists_every_orphan_filterset() -> None:
    """Two orphan FilterSets surface in one ``ConfigurationError`` with the multi-orphan lead-in.

    The single-orphan branch is exercised by
    ``test_orphan_filter_input_type_reference_raises_at_finalize``; this
    test pins the multi-orphan arm of
    ``_format_orphan_sets_error``: lead-in
    ``"FilterSets referenced via FilterInput[...] / filter_input_type(...)
    but not wired to any DjangoType:"`` followed by ``__module__.__qualname__``-sorted
    offenders. Without this test the multi-orphan branch could silently
    drift (e.g., inverting the sort key, dropping the lead-in) without
    a regression signal.
    """

    class StandaloneFilterA(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class StandaloneFilterB(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    # One orphan per helper spelling: both feed the one ledger the check reads.
    FilterInput[StandaloneFilterA]
    filter_input_type(StandaloneFilterB)

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

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    # Multi-orphan lead-in (mirrors ``_format_unresolved_targets_error``'s shape).
    assert (
        "FilterSets referenced via FilterInput[...] / filter_input_type(...) but not wired to "
        "any DjangoType:" in msg
    )
    # Both offenders surface.
    assert "StandaloneFilterA" in msg
    assert "StandaloneFilterB" in msg
    # Actionable suggestion for the multi-orphan arm.
    assert "Add 'filterset_class = <Name>' to the relevant DjangoType's Meta" in msg
    # Sort key contract: offenders ordered by ``__module__.__qualname__``.
    # ``StandaloneFilterA`` < ``StandaloneFilterB`` lexicographically; same module.
    idx_a = msg.index("StandaloneFilterA")
    idx_b = msg.index("StandaloneFilterB")
    assert idx_a < idx_b, (
        "Multi-orphan offenders must be sorted by '__module__.__qualname__'; "
        f"StandaloneFilterA appeared at index {idx_a}, "
        f"StandaloneFilterB at index {idx_b}."
    )


# ---------------------------------------------------------------------------
# Materialization & idempotency - Decision 9.
# ---------------------------------------------------------------------------


def test_phase_2_5_subpass_3_materializes_input_classes_as_module_globals() -> None:
    """The materialize pass writes ``BookFilterInputType`` to the inputs module globals."""

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

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
            filterset_class = BookFilter

    assert registry.get(Book) is BookType

    finalize_django_types()

    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "BookFilterInputType")
    assert "BookFilterInputType" in _materialized_names


def test_materialize_input_class_is_idempotent_on_same_pair() -> None:
    """Re-materializing the same ``(name, cls)`` pair is a no-op."""

    class _Stub:
        __module__ = "tests.filters.test_finalizer"
        __qualname__ = "_Stub"

    materialize_input_class("StubInputType", _Stub)
    materialize_input_class("StubInputType", _Stub)

    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert read_attr(inputs_module, "StubInputType") is _Stub
    assert _materialized_names["StubInputType"] is _Stub

    delattr(inputs_module, "StubInputType")


def test_materialize_input_class_rejects_collision_on_distinct_classes() -> None:
    """Re-materializing a name against a different class raises."""

    class _StubA:
        __module__ = "tests.filters.test_finalizer"
        __qualname__ = "_StubA"

    class _StubB:
        __module__ = "tests.filters.test_finalizer"
        __qualname__ = "_StubB"

    materialize_input_class("CollisionInputType", _StubA)
    with pytest.raises(ConfigurationError, match="two distinct FilterSet input classes"):
        materialize_input_class("CollisionInputType", _StubB)

    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    delattr(inputs_module, "CollisionInputType")


# ---------------------------------------------------------------------------
# Registry clear - Decision 9 lifecycle.
# ---------------------------------------------------------------------------


def test_registry_clear_clears_filter_input_namespace_and_helper_set() -> None:
    """``registry.clear()`` resets the ledger and the helper set.

    Materialized class objects are intentionally left parked in
    ``filters.inputs.__dict__`` so a consumer-held ``strawberry.lazy``
    LazyType still resolves between ``registry.clear()`` and the next
    ``finalize_django_types()`` call; ``materialize_input_class``
    overwrites the parked global in place on the next finalize.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    filter_input_type(BookFilter)
    assert BookFilter in _helper_referenced_filtersets

    # Materialize one input class directly.
    class _Stub:
        __module__ = "tests.filters.test_finalizer"
        __qualname__ = "_Stub"

    materialize_input_class("LedgerStubInputType", _Stub)
    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "LedgerStubInputType")

    registry.clear()

    # Ledger cleared so the next finalize re-emits, but the parked
    # class object stays in `module.__dict__` for any held LazyType.
    assert _materialized_names == {}
    assert _field_specs == {}
    assert _helper_referenced_filtersets == set()
    assert hasattr(inputs_module, "LedgerStubInputType")
    assert read_attr(inputs_module, "LedgerStubInputType") is _Stub

    # Teardown the parked global so the autouse fixture starts clean.
    delattr(inputs_module, "LedgerStubInputType")


def test_clear_filter_input_namespace_can_be_called_directly() -> None:
    """The public helper resets the ledger; parked module globals survive."""

    class _Stub:
        __module__ = "tests.filters.test_finalizer"
        __qualname__ = "_Stub"

    materialize_input_class("DirectClearInputType", _Stub)
    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "DirectClearInputType")

    clear_filter_input_namespace()

    # Ledger cleared so the next finalize re-emits, but the parked
    # class object stays in place so any consumer-held LazyType
    # resolves until the next `materialize_input_class` overwrites it.
    assert _materialized_names == {}
    assert hasattr(inputs_module, "DirectClearInputType")
    assert read_attr(inputs_module, "DirectClearInputType") is _Stub

    # Teardown the parked global so the autouse fixture starts clean.
    delattr(inputs_module, "DirectClearInputType")


def test_registry_clear_works_without_filters_imported() -> None:
    """``registry.clear()`` must not raise when filters package was never imported."""
    run_in_fresh_process(
        "import django_strawberry_framework.registry as r; "
        "assert 'django_strawberry_framework.filters' not in sys.modules; "
        "r.registry.clear()",
    )


# ---------------------------------------------------------------------------
# Unresolved RelatedFilter propagation.
# ---------------------------------------------------------------------------


def test_phase_2_5_unresolved_related_filter_raises_at_finalize() -> None:
    """A ``RelatedFilter("UnknownFilter")`` propagates as ``ConfigurationError``.

    ``LazyRelatedClassMixin.resolve_lazy_class`` raises ``ImportError``
    at Layer-2 resolution time (spec-027 Decision 3 Layer 2). The
    phase-2.5 binding pass re-wraps it as ``ConfigurationError`` per the
    package's "finalize-time errors are ``ConfigurationError``"
    convention; the original ``ImportError`` is preserved on
    ``__cause__`` so the failure mode is loud AND grep-stable against
    the sibling formatter convention.
    """

    class BookFilter(FilterSet):
        unknown = RelatedFilter("UnknownFilter", field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

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
            filterset_class = BookFilter

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "BookFilter" in msg
    assert "unresolved" in msg
    assert "UnknownFilter" in msg
    assert isinstance(exc_info.value.__cause__, ImportError)


def test_phase_2_5_unregistered_related_filter_target_raises_at_finalize() -> None:
    """A wired filterset whose ``RelatedFilter`` target model has no registered type raises.

    Subpass 2.5: a related branch's visibility scoping runs the target
    type's ``get_queryset`` (spec-027 Decision 8 step 3), so a
    ``RelatedFilter`` whose target model has no registered ``DjangoType``
    is unfulfillable even though its input field would be materialized
    into the schema. The misconfiguration surfaces at finalize, naming
    the filterset, instead of on the first request that activates the
    branch, nested or walked by a flat leaf (where
    ``FilterSet._branch_visibility_seed`` raises the runtime sibling of this
    error).
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    # No ShelfType registered - only the parent owner is wired.
    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = BookFilter

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "BookFilter" in msg
    assert "'shelf'" in msg
    assert "Shelf" in msg
    assert "no DjangoType is registered" in msg


def test_phase_2_5_unregistered_target_check_walks_transitive_filtersets() -> None:
    """Subpass 2.5 reaches ``RelatedFilter``s on UNWIRED child filtersets.

    The misconfigured ``RelatedFilter`` here lives on ``ShelfFilter``,
    which is never wired via ``Meta.filterset_class`` - it is only
    reachable as the target of the wired ``BookFilter.shelf`` branch.
    The sweep must walk wired filtersets transitively (with a visited
    set, since ``RelatedFilter`` cross-references may be cyclic) so a
    nested branch cannot smuggle an unregistered target past finalize.
    """

    class BranchFilter(FilterSet):
        class Meta:
            model = Branch
            fields = {"name": ["exact"]}

    class ShelfFilter(FilterSet):
        # Branch has no registered DjangoType below; this nested branch
        # is the misconfiguration the transitive walk must surface.
        branch = RelatedFilter(BranchFilter, field_name="branch")

        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")
            filterset_class = BookFilter

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "ShelfFilter" in msg
    assert "'branch'" in msg
    assert "no DjangoType is registered" in msg


def test_phase_2_5_non_import_get_filters_failure_propagates_unchanged() -> None:
    """A consumer factory's own exception raised during ``get_filters()`` propagates.

    Subpass 2 rewraps only an unresolved lazy target's ``ImportError``; any
    other exception (here a ``RelatedFilter`` callable factory that raises
    ``ValueError`` when evaluated) is consumer behaviour and reaches the
    caller unchanged.
    """

    def _broken_factory() -> NoReturn:
        raise ValueError("intentional factory failure")

    class BookFilter(FilterSet):
        # `LazyRelatedClassMixin.resolve_lazy_class` invokes the callable
        # when `.filterset` is read; this only happens at expansion time
        # (subpass 2), not at class creation, so the class itself builds
        # cleanly.
        broken = RelatedFilter(_broken_factory, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

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
            filterset_class = BookFilter

    assert registry.get(Book) is BookType

    with pytest.raises(ValueError, match="intentional factory failure"):
        finalize_django_types()


# ---------------------------------------------------------------------------
# Relay-shaped owner accepted under phase 2.5.
# ---------------------------------------------------------------------------


def test_phase_2_5_runs_under_relay_node_interface() -> None:
    """Phase 2.5 filter binding cooperates with Relay-Node interface injection."""

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

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
            filterset_class = BookFilter

    finalize_django_types()

    # Owner binding ran and the Relay-Node hooks survived.
    assert BookFilter._owner_definition is BookType.__django_strawberry_definition__
    assert issubclass(BookType, relay.Node)
    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "BookFilterInputType")


# ---------------------------------------------------------------------------
# A Meta.filterset_class declaring no Meta.model.
# ---------------------------------------------------------------------------


def _model_less_book_filter(shape: str) -> type[FilterSet]:
    """Return a ``FilterSet`` declaring no ``Meta.model`` in the named shape."""
    if shape == "no-meta":

        class NoMetaBookFilter(FilterSet):
            title = CharFilter(field_name="title")

        return NoMetaBookFilter
    if shape == "related-only":

        class RelatedShelfFilter(FilterSet):
            class Meta:
                model = Shelf
                fields = {"code": ["exact"]}

        class RelatedOnlyBookFilter(FilterSet):
            shelf = RelatedFilter(RelatedShelfFilter, field_name="shelf")

        return RelatedOnlyBookFilter
    meta_bodies: dict[str, dict[str, object]] = {
        "model-none": {"model": None},
        "all-fields": {"fields": "__all__"},
        "exclude": {"exclude": ("title",)},
        "fields-dict": {"fields": {"title": ["exact"]}},
    }
    return type(
        "MetaBookFilter",
        (FilterSet,),
        {"title": CharFilter(field_name="title"), "Meta": type("Meta", (), meta_bodies[shape])},
    )


def _wire_book_type(filterset: type[FilterSet], *, relay_node: bool) -> type[DjangoType]:
    """Declare a ``Book`` type naming ``filterset`` as its ``Meta.filterset_class``."""
    meta_body: dict[str, object] = {
        "model": Book,
        "fields": ("id", "title"),
        "filterset_class": filterset,
    }
    if relay_node:
        meta_body["interfaces"] = (relay.Node,)
    return type("WiredBookType", (DjangoType,), {"Meta": type("Meta", (), meta_body)})


def _serving_query(book_type: type[DjangoType], *, serving: str) -> type:
    """Declare the root ``Query`` serving ``book_type``, as a project does before finalize."""
    if serving == "list":
        annotations: dict[str, object] = {"books": list[book_type]}
        field: object = DjangoListField(book_type)
    else:
        annotations = {"books": DjangoConnection[book_type]}
        field = DjangoConnectionField(book_type)
    return strawberry.type(type("Query", (), {"__annotations__": annotations, "books": field}))


@pytest.mark.parametrize(
    "shape",
    [
        "no-meta",
        "model-none",
        "all-fields",
        "exclude",
        "fields-dict",
        "related-only",
    ],
)
@pytest.mark.parametrize(
    ("relay_node", "serving"),
    [(True, "connection"), (False, "list")],
    ids=["relay-connection", "plain-list"],
)
def test_a_filterset_class_declaring_no_meta_model_is_refused_at_finalize(
    *,
    shape: str,
    relay_node: bool,
    serving: str,
) -> None:
    """A served filterset must declare the ``Meta.model`` its owner's model is or derives from.

    Every filter of a served set is typed, validated and applied against the set's
    ``Meta.model``, so a set without one would publish an input no request could apply.
    The binding refuses it whatever else its ``Meta`` declares, naming the set, the owner
    type, the owner's model and the remedy, and stores no owner. The wiring is refused,
    not the serving: a ``DjangoListField`` publishes no filter argument, yet its type's
    ``Meta.filterset_class`` is refused the same way.
    """
    filterset = _model_less_book_filter(shape)
    book_type = _wire_book_type(filterset, relay_node=relay_node)
    _serving_query(book_type, serving=serving)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    name = filterset.__qualname__
    assert str(exc_info.value) == (
        f"FilterSet {name} is declared as the filterset_class of "
        f"{book_type.__qualname__} (model Book), but declares no Meta.model. A filterset's "
        "filters are typed, validated and applied against its Meta.model, so a filterset "
        "a DjangoType serves must declare one: set Meta.model = Book (with Meta.fields = "
        f"[] to publish only its declared filters) on {name}, or on a subclass declared as "
        "the filterset_class."
    )
    assert set_bound_definition(filterset) is None


def test_a_model_less_base_serves_through_a_subclass_declaring_meta_model_and_no_fields() -> None:
    """``Meta.model`` with ``Meta.fields = []`` publishes only the declared filters.

    The model-less base stays an unwired base; its subclass keys it on the owner's model
    and binds, and the generated input carries the declared filter and the logical arms,
    no model-derived leaf.
    """

    class DeclaredOnlyBase(FilterSet):
        title = CharFilter(field_name="title", lookup_expr="icontains")

    class DeclaredOnlyBookFilter(DeclaredOnlyBase):
        class Meta:
            model = Book
            fields: ClassVar[list[str]] = []

    book_type = _wire_book_type(DeclaredOnlyBookFilter, relay_node=True)
    query = _serving_query(book_type, serving="connection")
    finalize_django_types()
    schema = strawberry.Schema(query=query, config=strawberry_config())

    assert DeclaredOnlyBookFilter._owner_definition is book_type.__django_strawberry_definition__
    assert set_bound_definition(DeclaredOnlyBase) is None
    sdl = schema.as_str()
    block = sdl.split("input DeclaredOnlyBookFilterInputType {\n", 1)[1].split("\n}", 1)[0]
    published = sorted(line.split(":", 1)[0].strip() for line in block.splitlines())
    assert published == [
        "and",
        "not",
        "or",
        "title",
    ], block


# ---------------------------------------------------------------------------
# _bind_filterset_owner - direct unit coverage of the binding branches.
# ---------------------------------------------------------------------------


def _owner(model: type[Model]) -> DjangoTypeDefinition:
    """Declare a plain real ``DjangoType`` over ``model`` and return its definition."""
    owner_model = model

    class OwnerType(DjangoType):
        class Meta:
            model = owner_model
            fields = ("id",)

    return OwnerType.__django_strawberry_definition__


def test_bind_filterset_owner_idempotent_for_same_definition() -> None:
    """Re-binding the SAME definition object short-circuits via identity."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    definition = _owner(Shelf)
    _bind_filterset_owner(ShelfFilter, definition)  # previous None -> bind
    _bind_filterset_owner(ShelfFilter, definition)  # previous IS definition -> return
    assert ShelfFilter._owner_definition is definition


def test_bind_filterset_owner_rejects_filterset_model_unrelated_to_owner() -> None:
    """A first bind whose filterset ``Meta.model`` is unrelated to the owner raises (H-core-3).

    The single most common Phase-2.5 user error is wiring
    ``Meta.filterset_class`` to a FilterSet keyed on an entirely different
    model. Without this guard the FIRST binding stores silently and the
    mismatch only surfaces at query time as an opaque ``FieldError``; the
    guard fails loud at finalize, naming both models.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class BookOwnerType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

    book_def = BookOwnerType.__django_strawberry_definition__
    with pytest.raises(ConfigurationError) as exc_info:
        _bind_filterset_owner(ShelfFilter, book_def)
    msg = str(exc_info.value)
    assert "ShelfFilter" in msg
    assert "Shelf" in msg  # the filterset's own Meta.model
    assert "Book" in msg  # the owner's model
    # The rejected owner must NOT have been stored.
    assert getattr(ShelfFilter, "_owner_definition", None) is None


def test_bind_filterset_owner_rejects_diverging_own_pk_relay_node_ness() -> None:
    """A Relay-node owner and a plain owner cannot share one FilterSet (H4b).

    The filterset's own ``id`` resolves to a GlobalID under the Relay owner
    but a scalar under the plain owner - an own-PK ambiguity the binding
    must reject loudly rather than silently pinning to whichever bound
    first. Own-PK Relay identity is one of the three owner-dependent axes.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class RelayShelfType(DjangoType):
        class Meta:
            model = Shelf
            interfaces = (relay.Node,)
            fields = ("id", "code")

    class PlainShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    # ``apply_interfaces`` injects ``relay.Node`` so ``implements_relay_node``
    # sees the Relay owner as a node (the finalizer's phase-2.5 step, run
    # here in isolation).
    apply_interfaces(RelayShelfType, RelayShelfType.__django_strawberry_definition__)

    relay_def = RelayShelfType.__django_strawberry_definition__
    plain_def = PlainShelfType.__django_strawberry_definition__

    _bind_filterset_owner(ShelfFilter, relay_def)  # first binds
    with pytest.raises(ConfigurationError) as exc_info:
        _bind_filterset_owner(ShelfFilter, plain_def)
    msg = str(exc_info.value)
    assert "own-primary-key Relay identity" in msg
    assert "RelayShelfType" in msg
    assert "PlainShelfType" in msg


def test_bind_filterset_owner_rejects_diverging_own_pk_type_name() -> None:
    """Two Relay-node owners with different GraphQL type names can't share a FilterSet (H4b).

    Each owner types the own-PK GlobalID to its own ``graphql_type_name``,
    so the shared ``id`` filter would validate GlobalIDs against whichever
    owner finalized first.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class FirstShelfType(DjangoType):
        class Meta:
            model = Shelf
            interfaces = (relay.Node,)
            fields = ("id", "code")

    class SecondShelfType(DjangoType):
        class Meta:
            model = Shelf
            interfaces = (relay.Node,)
            fields = ("id", "code")

    apply_interfaces(FirstShelfType, FirstShelfType.__django_strawberry_definition__)
    apply_interfaces(SecondShelfType, SecondShelfType.__django_strawberry_definition__)

    _bind_filterset_owner(ShelfFilter, FirstShelfType.__django_strawberry_definition__)
    with pytest.raises(ConfigurationError) as exc_info:
        _bind_filterset_owner(ShelfFilter, SecondShelfType.__django_strawberry_definition__)
    assert "own-primary-key Relay identity" in str(exc_info.value)


def test_phase_2_5_configuration_error_from_get_filters_propagates_unwrapped() -> None:
    """A ``ConfigurationError`` raised inside ``get_filters()`` is re-raised as-is.

    The finalize loop rewraps only ``ImportError``; a ``ConfigurationError`` is
    already the canonical finalize-time error class, so it propagates
    unchanged rather than being double-wrapped.
    """

    def _config_error_factory() -> NoReturn:
        raise ConfigurationError("intentional configuration failure inside get_filters")

    class BookFilter(FilterSet):
        broken = RelatedFilter(_config_error_factory, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

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
            filterset_class = BookFilter

    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as excinfo:
        finalize_django_types()
    # Re-raised unchanged: the original message survives, not the
    # "Cannot finalize ..." rewrap used for ImportError / generic failures.
    assert "intentional configuration failure inside get_filters" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Build-time encode-only GlobalID-filter audit (spec-031 fail-closed).
# ---------------------------------------------------------------------------


def test_phase_2_5_rejects_globalid_filter_on_callable_strategy_target() -> None:
    """A GlobalID filter whose own-PK target uses a ``callable`` strategy fails at build.

    ``callable`` is encode-only (no decode path), so the schema would otherwise
    carry a typed GlobalID filter input that can never validly consume the IDs
    its target emits. ``_audit_globalid_filter_strategies`` raises at finalize,
    naming the filterset and field.
    """

    def encode(_type_cls: type[DjangoType], _model: type[Model], _root: object) -> str:
        return "GenreType"

    class GenreFilter(FilterSet):
        class Meta:
            model = Genre
            fields = {"id": ["exact"]}

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            interfaces = (relay.Node,)
            primary = True
            globalid_strategy = encode
            filterset_class = GenreFilter

    assert registry.get(Genre) is GenreType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "GenreFilter" in msg
    assert "encode-only" in msg
    assert "callable" in msg


@pytest.mark.parametrize(
    ("set_model", "key"),
    [
        pytest.param(Book, "shelf__branch", id="untyped-hop"),
        pytest.param(Loan, "book__shelf__branch", id="scoped-hop-then-untyped-hop"),
    ],
)
def test_phase_2_5_rejects_a_callable_strategy_target_behind_an_untyped_hop(
    set_model: type[Model],
    key: str,
) -> None:
    """A relation key into a ``callable``-strategy type through a hop no type exposes fails at build.

    No type registers ``Shelf``, so the audit's walk continues on the relation's model to
    ``Branch``'s type, the target the request-time walk validates against once the
    registry is finalized; build time refuses the encode-only target rather than leaving
    every request to answer ``GLOBALID_UNVALIDATABLE``. The ``Loan`` key first crosses a
    ``Book`` type carrying its own ``get_queryset``.
    """

    def encode(_type_cls: type[DjangoType], _model: type[Model], _root: object) -> str:
        return "BranchType"

    class BranchType(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = encode

    class ScopedBookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Book],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Book]:
            return queryset.exclude(title="hidden")

    class KeyFilter(FilterSet):
        class Meta:
            model = set_model
            fields = {key: ["exact"]}

    class OwnerType(DjangoType):
        class Meta:
            model = set_model
            fields = ("id",)
            interfaces = (relay.Node,)
            filterset_class = KeyFilter
            primary = True

    assert registry.get(Shelf) is None
    assert registry.get(Branch) is BranchType
    assert registry.get(set_model) is OwnerType
    assert ScopedBookType in registry.types_for(Book)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "KeyFilter" in msg
    assert "encode-only" in msg
    assert "callable" in msg


def test_phase_2_5_rejects_globalid_filter_on_custom_strategy_target() -> None:
    """A GlobalID filter whose own-PK target overrides ``resolve_typename`` fails at build.

    Overriding ``resolve_typename`` classifies the target ``custom`` - also
    encode-only - so the same build-time audit rejects the filter binding.
    """

    class GenreFilter(FilterSet):
        class Meta:
            model = Genre
            fields = {"id": ["exact"]}

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            interfaces = (relay.Node,)
            primary = True
            filterset_class = GenreFilter

        @classmethod
        def resolve_typename(cls, _root: object, _info: object) -> str:
            return "GenreType"

    assert registry.get(Genre) is GenreType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "GenreFilter" in msg
    assert "encode-only" in msg
    assert "custom" in msg


def test_phase_2_5_globalid_audit_skips_unresolvable_target() -> None:
    """The audit skips a GlobalID filter whose target definition resolves to ``None``.

    A consumer-declared ``GlobalIDFilter`` pointed at a scalar field ('name')
    is neither the own PK nor a relation head, so
    ``resolve_globalid_target_definition`` returns ``None`` during the audit and
    the filter is skipped (there is no target strategy to fail-close on). This
    is a legal filterset - the pre-existing unregistered-related-target audit
    only walks ``RelatedFilter`` instances - so finalization succeeds.
    """

    class GenreFilter(FilterSet):
        genre_gid = GlobalIDFilter(field_name="name")

        class Meta:
            model = Genre
            fields = {"name": ["exact"]}

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            primary = True
            filterset_class = GenreFilter

    # Finalization succeeds: the unresolvable-target branch is a no-op skip.
    finalize_django_types()
    assert GenreType.__django_strawberry_definition__.finalized


def test_finalize_surfaces_the_related_filter_target_gate_identity() -> None:
    """A mis-typed ``RelatedFilter`` target surfaces the GATE's typed message at finalize.

    It never surfaces as a raw ``AttributeError``.

    Ungated, the mis-typed target would survive declaration + binding +
    expansion and detonate inside ``_expand_related_filter``'s
    ``target.get_filters()`` as a raw ``AttributeError``. The ``.filterset``
    gate raises the typed ``ConfigurationError`` at first resolution, and
    subpass 2 propagates it BY IDENTITY -- the original gate message
    survives.
    """

    class _NotAFilterSet:
        """A plain class: the mis-typed RelatedFilter target."""

    class BrokenFilter(FilterSet):
        # basedpyright: the non-FilterSet target is the hostile input under test; RelatedFilter
        # types the parameter as _FilterSetTarget
        branch = RelatedFilter(_NotAFilterSet, field_name="branch")  # pyright: ignore[reportArgumentType]

        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")
            filterset_class = BrokenFilter

    assert registry.get(Shelf) is ShelfType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "declares RelatedFilter" in msg
    assert "_NotAFilterSet" in msg
    assert "is not a FilterSet subclass" in msg
    assert "raised during expansion" not in msg


# ---------------------------------------------------------------------------
# Deep-copy probe of declared filters.
# ---------------------------------------------------------------------------


def _code_is(queryset: QuerySet[Shelf], name: str, value: object) -> QuerySet[Shelf]:
    """A plain-function ``method=``: shelves whose code is ``value``."""
    del name
    return queryset.filter(code=value)


class _InstanceLockHolder:
    """A service holding a lock on the instance, which a deep copy of its bound method copies."""

    def __init__(self) -> None:
        self.lock = threading.Lock()

    def code_is(
        self,
        queryset: QuerySet[Shelf],
        name: str,
        value: object,
    ) -> QuerySet[Shelf]:
        return _code_is(queryset, name, value)


class _CacheHolder:
    """A service holding Django's default cache handler on the instance."""

    def __init__(self) -> None:
        self.cache = caches["default"]

    def code_is(
        self,
        queryset: QuerySet[Shelf],
        name: str,
        value: object,
    ) -> QuerySet[Shelf]:
        return _code_is(queryset, name, value)


_METHOD_ADVICE = (
    'Pass method= as the name of a FilterSet method (method="<name>") or as a plain function.'
)
_OBJECT_ADVICE = (
    "Keep the object off the filter: build it inside the filter's method or the FilterSet's "
    "filter_queryset, or hold it on a class."
)


def _copy_refusal(
    where: str,
    kind: str,
    cause: BaseException | None,
    *,
    has_method: bool,
) -> str:
    """The deep-copy refusal for filter ``where`` of class ``kind``, its cause as raised."""
    assert isinstance(cause, TypeError)
    advice = _METHOD_ADVICE if has_method else _OBJECT_ADVICE
    return (
        f"FilterSet {where}: {kind} cannot be deep-copied ({type(cause).__name__}: {cause}); "
        "django-filter deep-copies every filter for each request, so a filter must hold "
        f"nothing a deep copy refuses (a lock, a cache handler). {advice}"
    )


def _is_filterset_class(value: object) -> TypeIs[type[FilterSet]]:
    """Whether ``value`` is a ``FilterSet`` subclass."""
    return isinstance(value, type) and issubclass(value, FilterSet)


def _shelf_filter(declared: Filter) -> type[FilterSet]:
    """``ShelfFilter`` over ``Shelf`` declaring ``declared`` as ``code_is``."""
    meta = type("Meta", (), {"model": Shelf, "fields": {"topic": ["exact"]}})
    body: dict[str, object] = {"code_is": declared, "Meta": meta}
    return require(type("ShelfFilter", (FilterSet,), body), _is_filterset_class)


def _wire_shelf_type(filterset_cls: type[FilterSet]) -> type[DjangoType]:
    """A Relay ``ShelfType`` serving ``filterset_cls``."""

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")
            interfaces = (relay.Node,)
            filterset_class = filterset_cls

    return ShelfType


_REFUSED_DECLARATIONS = [
    pytest.param(
        lambda: CharFilter(field_name="code", method=_InstanceLockHolder().code_is),
        "CharFilter",
        True,
        id="char-filter-bound-method-over-instance-lock",
    ),
    pytest.param(
        lambda: NumberFilter(field_name="id", method=_InstanceLockHolder().code_is),
        "NumberFilter",
        True,
        id="number-filter-bound-method-over-instance-lock",
    ),
    pytest.param(
        lambda: BooleanFilter(field_name="code", method=_InstanceLockHolder().code_is),
        "BooleanFilter",
        True,
        id="boolean-filter-bound-method-over-instance-lock",
    ),
    pytest.param(
        lambda: CharFilter(
            field_name="code",
            method=functools.partial(_InstanceLockHolder.code_is, _InstanceLockHolder()),
        ),
        "CharFilter",
        True,
        id="partial-over-instance-lock",
    ),
    pytest.param(
        lambda: CharFilter(field_name="code", help_text=threading.Lock()),
        "CharFilter",
        False,
        id="lock-in-extra",
    ),
    pytest.param(
        lambda: CharFilter(field_name="code", method="filter_code", help_text=threading.Lock()),
        "CharFilter",
        False,
        id="lock-in-extra-beside-a-method-name",
    ),
    pytest.param(
        lambda: ListFilter(field_name="code", method=_InstanceLockHolder().code_is),
        "ListFilter",
        True,
        id="list-filter-bound-method-over-instance-lock",
    ),
    pytest.param(
        lambda: CharFilter(field_name="code", method=_CacheHolder().code_is),
        "CharFilter",
        True,
        id="bound-method-over-cache-handler",
    ),
]


@pytest.mark.parametrize(("declare", "kind", "has_method"), _REFUSED_DECLARATIONS)
def test_finalize_refuses_a_declared_filter_a_deep_copy_refuses(
    declare: Callable[[], Filter],
    kind: str,
    *,
    has_method: bool,
) -> None:
    """A served set's declared filter that no deep copy can take fails the build by name.

    django-filter deep-copies every declared filter into each request's
    ``FilterSet``, so such a filter could serve no request (a ``ListFilter``
    builds without a copy and would fail every filtered request instead).
    Subpass 1.5 copies each declared filter once and refuses the first, naming
    the set, the attribute and the filter's class, the copy's error kept as
    ``__cause__``.
    """
    _ = _wire_shelf_type(_shelf_filter(declare()))

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    cause = exc_info.value.__cause__
    expected = _copy_refusal("ShelfFilter.code_is", kind, cause, has_method=has_method)
    assert str(exc_info.value) == expected


def test_finalize_refuses_a_generated_filter_a_deep_copy_refuses() -> None:
    """A ``Meta.fields`` filter whose override ``extra`` no copy takes fails by name.

    The probe copies every filter of the set's ``base_filters``, the ones
    django-filter generates from ``Meta.fields`` included, so a lock an
    override's ``extra`` puts on the generated ``topic`` filter is refused
    naming that attribute.
    """
    lock = threading.Lock()

    def locked_extra(model_field: object) -> dict[str, object]:
        del model_field
        return {"help_text": lock}

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"topic": ["exact"]}
            filter_overrides: ClassVar[dict[type[object], dict[str, object]]] = {
                TextField: {"filter_class": CharFilter, "extra": locked_extra},
            }

    _ = _wire_shelf_type(ShelfFilter)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    cause = exc_info.value.__cause__
    where = f"{ShelfFilter.__qualname__}.topic"
    assert str(exc_info.value) == _copy_refusal(where, "CharFilter", cause, has_method=False)


def test_finalize_refuses_a_related_child_filter_a_deep_copy_refuses() -> None:
    """A ``RelatedFilter`` child set no type serves is refused by its expansion copy.

    The child set is reached only through the served set's ``RelatedFilter``,
    so the probe of served sets never copies its filters; the expansion copy
    refuses the filter naming the child set, its attribute and the
    ``RelatedFilter`` it was reached through.
    """
    shelf_filter = _shelf_filter(
        CharFilter(field_name="code", method=_InstanceLockHolder().code_is),
    )

    class BookFilter(FilterSet):
        shelf = RelatedFilter(shelf_filter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = BookFilter

    assert registry.get(Shelf) is ShelfType
    assert registry.get(Book) is BookType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    cause = exc_info.value.__cause__
    where = f"ShelfFilter.code_is (reached through RelatedFilter {BookFilter.__qualname__}.shelf)"
    assert str(exc_info.value) == _copy_refusal(where, "CharFilter", cause, has_method=True)


# ---------------------------------------------------------------------------
# Served leaves the visibility seal refuses.
# ---------------------------------------------------------------------------


class _Doubled(Transform):
    """A project transform: the column doubled, an integer like the column."""

    lookup_name = "doubled"
    template = "(%(expressions)s * 2)"


class _AbsoluteValue(Transform):
    """A project transform built on a database function, ``ABS``."""

    lookup_name = "absolute"
    function = "ABS"


class _NotEqual(Lookup):
    """A project comparison lookup, Django's custom-lookup guide example: ``<column> <> <value>``."""

    lookup_name = "ne"

    @override
    def as_sql(self, compiler: SQLCompiler, connection: BaseDatabaseWrapper) -> _AsSqlType:
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        return f"{lhs} <> {rhs}", (*lhs_params, *rhs_params)


class _SubclassedHour(ExtractHour):
    """A subclass of Django's ``ExtractHour`` that overrides nothing."""


@pytest.fixture(autouse=True)
def _fresh_lookup_operands() -> Iterator[None]:
    """Drop the filter operands resolved while a test's lookup registration was live.

    ``filters/base.py`` caches each column's resolved lookup operand for the process; an
    entry written under a registration would outlive it into the next test on the worker.
    """
    _lookup_operand.cache_clear()
    _model_lookup_operand.cache_clear()
    yield
    _lookup_operand.cache_clear()
    _model_lookup_operand.cache_clear()


@contextlib.contextmanager
def _instance_lookup(
    model: type[Model],
    field_name: str,
    lookup: type[Lookup],
    lookup_name: str,
) -> Generator[None]:
    """Register ``lookup`` as ``lookup_name`` on ``model``'s ``field_name`` instance alone while open."""
    field = model._meta.get_field(field_name)
    assert isinstance(field, ModelFieldClass)
    _ = field.register_instance_lookup(lookup, lookup_name)
    try:
        yield
    finally:
        field._unregister_instance_lookup(lookup, lookup_name)


def _specimen_set(
    fields: object,
    declared: dict[str, Filter] | None = None,
    *,
    name: str = "SpecimenFilter",
    model: type[Model] | None = ScalarSpecimen,
    meta: dict[str, object] | None = None,
) -> type[FilterSet]:
    """A set over ``model`` generating ``fields`` and declaring ``declared``."""
    meta_class = type("Meta", (), {"model": model, "fields": fields, **(meta or {})})
    body: dict[str, object] = {**(declared or {}), "Meta": meta_class}
    return require(type(name, (FilterSet,), body), _is_filterset_class)


def _relay_node(
    model: type[Model],
    fields: tuple[str, ...],
    filterset_cls: type[FilterSet] | None,
    *,
    relay_node: bool = True,
) -> type[DjangoType]:
    """A ``DjangoType`` over ``model``, a Relay node unless ``relay_node`` is false."""
    meta: dict[str, object] = {"model": model, "fields": fields}
    if relay_node:
        meta["interfaces"] = (relay.Node,)
    if filterset_cls is not None:
        meta["filterset_class"] = filterset_cls
    node = type(f"{model.__name__}Node", (DjangoType,), {"Meta": type("Meta", (), meta)})
    assert issubclass(node, DjangoType)
    return node


def _serve_at_root(filterset_cls: type[FilterSet]) -> type[DjangoType]:
    """Serve ``filterset_cls`` through a root connection over its model's node."""
    model = filterset_cls._meta.model
    assert model is not None
    node = _relay_node(model, ("id",), filterset_cls)
    _ = DjangoConnectionField(node)
    return node


def _serve_nested_only(filterset_cls: type[FilterSet]) -> None:
    """Serve ``filterset_cls`` (over ``NullableScalarSpecimen``) only as a nested connection.

    A Relay ``ScalarSpecimen`` node with no set of its own selects the to-many
    ``nullable_partners``, whose Relay target grows ``nullablePartnersConnection(filter:)``.
    """
    _ = _relay_node(NullableScalarSpecimen, ("id", "label"), filterset_cls)
    _ = DjangoConnectionField(_relay_node(ScalarSpecimen, ("id", "nullable_partners"), None))


def _serve_through_related_filter(child: type[FilterSet]) -> None:
    """Serve a partner set at the root that reaches ``child`` (over ``ScalarSpecimen``) nested only."""
    parent = _specimen_set(
        {"label": ["exact"]},
        {"partner": RelatedFilter(child, field_name="partner")},
        name="PartnerFilter",
        model=NullableScalarSpecimen,
    )
    _ = _relay_node(ScalarSpecimen, ("id", "label"), None)
    _ = _serve_at_root(parent)


def _unsealable_refusal(subject: str, lookup: str, refused: type[object]) -> str:
    """The refusal of a served leaf whose predicate holds ``refused``."""
    return (
        f"{subject} with lookup {lookup!r} resolves to {refused.__module__}."
        f"{refused.__qualname__}, which is not one of Django's own lookup or transform "
        "classes. A connection serves this filter (a DjangoConnectionField, or the "
        "<relation>Connection a Relay type grows for a to-many relation) and runs its filter: "
        "argument inside the visibility boundary, which admits only Django's own lookup and "
        "transform classes, so every request naming the filter would be refused. Filter "
        "through a Django class (registered under any lookup name), apply a FilterSet no "
        "connection serves from a resolver of your own (FilterInput[...] and apply_sync), or "
        'set Meta.relation_shapes = {"<relation>": "list"} on the type whose to-many '
        "relation grows the connection."
    )


@dataclass(frozen=True)
class _UnsealableCase:
    """A served set whose one leaf resolves to a class the seal refuses, and what its refusal names."""

    register: Callable[[], contextlib.AbstractContextManager[object]]
    serve: Callable[[], object]
    subject: str
    lookup: str
    refused: type[object]


def _doubled() -> contextlib.AbstractContextManager[object]:
    return register_lookup(BigIntegerField, _Doubled)


def _not_equal_on_big() -> contextlib.AbstractContextManager[object]:
    return register_lookup(BigIntegerField, _NotEqual)


_UNSEALABLE_CASES: dict[str, _UnsealableCase] = {
    "project-transform-generated-root": _UnsealableCase(
        _doubled,
        lambda: _serve_at_root(_specimen_set({"signed_big": ["doubled"]})),
        "SpecimenFilter: NumberFilter on 'signed_big'",
        "doubled",
        _Doubled,
    ),
    "project-lookup-declared-lookup-expr-root": _UnsealableCase(
        _not_equal_on_big,
        lambda: _serve_at_root(
            _specimen_set([], {"other": NumberFilter(field_name="signed_big", lookup_expr="ne")}),
        ),
        "SpecimenFilter: NumberFilter on 'signed_big'",
        "ne",
        _NotEqual,
    ),
    "func-transform-declared-field-name-root": _UnsealableCase(
        lambda: register_lookup(BigIntegerField, _AbsoluteValue),
        lambda: _serve_at_root(
            _specimen_set([], {"size": NumberFilter(field_name="signed_big__absolute")}),
        ),
        "SpecimenFilter: NumberFilter on 'signed_big__absolute'",
        "exact",
        _AbsoluteValue,
    ),
    "django-subclass-filter-overrides-root": _UnsealableCase(
        lambda: register_lookup(DateTimeField, _SubclassedHour, lookup_name="hour_of"),
        lambda: _serve_at_root(
            _specimen_set(
                {"occurred_at": ["hour_of"]},
                meta={"filter_overrides": {IntegerField: {"filter_class": CharFilter}}},
            ),
        ),
        "SpecimenFilter: CharFilter on 'occurred_at'",
        "hour_of",
        _SubclassedHour,
    ),
    "django-lookup-on-a-project-transform": _UnsealableCase(
        lambda: _both(_doubled(), register_lookup(_Doubled, GreaterThan, lookup_name="above")),
        lambda: _serve_at_root(_specimen_set({"signed_big": ["doubled__above"]})),
        "SpecimenFilter: NumberFilter on 'signed_big'",
        "doubled__above",
        _Doubled,
    ),
    "project-lookup-on-a-django-transform-output": _UnsealableCase(
        lambda: register_lookup(IntegerField, _NotEqual),
        lambda: _serve_at_root(_specimen_set({"occurred_at": ["hour__ne"]})),
        "SpecimenFilter: NumberFilter on 'occurred_at'",
        "hour__ne",
        _NotEqual,
    ),
    "instance-registration": _UnsealableCase(
        lambda: _instance_lookup(ScalarSpecimen, "signed_big", _NotEqual, "unequal"),
        lambda: _serve_at_root(_specimen_set({"signed_big": ["unequal"]})),
        "SpecimenFilter: NumberFilter on 'signed_big'",
        "unequal",
        _NotEqual,
    ),
    "nested-connection-only": _UnsealableCase(
        _doubled,
        lambda: _serve_nested_only(
            _specimen_set(
                {"signed_big": ["doubled"]},
                name="PartnerFilter",
                model=NullableScalarSpecimen,
            ),
        ),
        "PartnerFilter: NumberFilter on 'signed_big'",
        "doubled",
        _Doubled,
    ),
    "related-filter-nested-only-child": _UnsealableCase(
        _doubled,
        lambda: _serve_through_related_filter(
            _specimen_set(
                {"label": ["exact"]},
                {"twice": NumberFilter(field_name="signed_big", lookup_expr="doubled")},
            ),
        ),
        "SpecimenFilter.twice: NumberFilter on 'signed_big' (reached through PartnerFilter.partner)",
        "doubled",
        _Doubled,
    ),
    "meta-fields-relation-path": _UnsealableCase(
        _doubled,
        lambda: _serve_at_root(
            _specimen_set(
                {"partner__signed_big": ["doubled"]},
                name="PartnerFilter",
                model=NullableScalarSpecimen,
            ),
        ),
        "PartnerFilter: NumberFilter on 'partner__signed_big'",
        "doubled",
        _Doubled,
    ),
    "in-leaf": _UnsealableCase(
        _doubled,
        lambda: _serve_at_root(_specimen_set({"signed_big": ["doubled__in"]})),
        "SpecimenFilter: IntegerInFilter on 'signed_big'",
        "doubled__in",
        _Doubled,
    ),
    "range-leaf": _UnsealableCase(
        _doubled,
        lambda: _serve_at_root(_specimen_set({"signed_big": ["doubled__range"]})),
        "SpecimenFilter: IntegerRangeFilter on 'signed_big'",
        "doubled__range",
        _Doubled,
    ),
    "isnull-leaf": _UnsealableCase(
        _doubled,
        lambda: _serve_at_root(_specimen_set({"signed_big": ["doubled__isnull"]})),
        "SpecimenFilter: BooleanFilter on 'signed_big'",
        "doubled__isnull",
        _Doubled,
    ),
    "reverse-relation-key": _UnsealableCase(
        lambda: register_lookup(ForeignKey, _NotEqual, lookup_name="exact"),
        lambda: _serve_at_root(_specimen_set({"children": ["exact"]})),
        "SpecimenFilter: ModelMultipleChoiceFilter on 'children'",
        "exact",
        _NotEqual,
    ),
}


@contextlib.contextmanager
def _both(
    first: contextlib.AbstractContextManager[object],
    second: contextlib.AbstractContextManager[object],
) -> Generator[None]:
    """Hold ``first`` and then ``second`` open together."""
    with first, second:
        yield


@pytest.mark.parametrize("case", list(_UNSEALABLE_CASES.values()), ids=list(_UNSEALABLE_CASES))
def test_finalize_refuses_a_served_leaf_the_visibility_seal_refuses(case: _UnsealableCase) -> None:
    """A leaf a connection serves whose predicate holds a class not Django's own fails the build.

    The connection runs its ``filter:`` argument inside the visibility boundary, whose seal
    refuses such a class on every request, so the build names the declaring set, the
    filter class, the path, the lookup and the refused class, wherever the leaf comes
    from (generated, declared, ``Meta.filter_overrides``, a relation path, a
    ``RelatedFilter`` child only the nested branch reaches, a reverse relation key) and
    whichever connection serves it (root, or only a nested ``<relation>Connection``).
    """
    with case.register():
        _ = case.serve()
        with pytest.raises(ConfigurationError) as exc_info:
            finalize_django_types()
    assert str(exc_info.value) == _unsealable_refusal(case.subject, case.lookup, case.refused)


def test_a_connection_declared_after_finalize_refuses_an_unsealable_leaf() -> None:
    """A root connection declared once the registry is finalized is refused where it is declared."""
    with _doubled():
        node = _relay_node(ScalarSpecimen, ("id",), _specimen_set({"signed_big": ["doubled"]}))
        finalize_django_types()
        with pytest.raises(ConfigurationError) as exc_info:
            _ = DjangoConnectionField(node)
    subject = "SpecimenFilter: NumberFilter on 'signed_big'"
    assert str(exc_info.value) == _unsealable_refusal(subject, "doubled", _Doubled)


def test_the_seal_predicate_is_the_one_the_build_asks(monkeypatch: pytest.MonkeyPatch) -> None:
    """The build asks ``utils/querysets.py::_type_is_genuinely_django`` itself, never a copy.

    With the predicate refusing Django's ``Abs``, a served leaf through ``Abs`` (registered
    under another name) is refused naming it.
    """
    genuine = querysets_module._type_is_genuinely_django

    def genuine_but_abs(node_type: type[object]) -> bool:
        return node_type is not Abs and genuine(node_type)

    monkeypatch.setattr(querysets_module, "_type_is_genuinely_django", genuine_but_abs)
    with register_lookup(BigIntegerField, Abs, lookup_name="magnitude"):
        _ = _serve_at_root(_specimen_set({"signed_big": ["magnitude"]}))
        with pytest.raises(ConfigurationError) as exc_info:
            finalize_django_types()
    subject = "SpecimenFilter: NumberFilter on 'signed_big'"
    assert str(exc_info.value) == _unsealable_refusal(subject, "magnitude", Abs)


def _doubled_is(queryset: QuerySet[Model], name: str, value: object) -> QuerySet[Model]:
    """A plain-function ``method=``: rows whose doubled ``signed_big`` is ``value``."""
    del name
    return queryset.filter(signed_big__doubled=value)


class _OwnFilterNumberFilter(NumberFilter):
    """A consumer ``NumberFilter`` whose own ``filter`` decides what its value means."""

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        return qs


def _post(schema: object, query: str) -> object:
    """Execute ``query`` on ``schema`` with a request context; return its data, no errors."""
    assert isinstance(schema, strawberry.Schema)
    result = schema.execute_sync(query, context_value=HttpRequest())
    assert result.errors is None, result.errors
    return result.data


def _served_schema(
    filterset_cls: type[FilterSet],
    model: type[Model] = ScalarSpecimen,
) -> strawberry.Schema:
    """Serve ``filterset_cls`` (over ``model``) at the root ``rows`` connection."""
    node = _relay_node(model, ("id", "label"), filterset_cls)
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"rows": DjangoConnection[node]},
                "rows": DjangoConnectionField(node),
            },
        ),
    )
    finalize_django_types()
    return DjangoSchema(query=query, config=strawberry_config())


def _labels(data: object) -> list[str]:
    """Return the ``label`` of every ``rows`` edge in ``data``, sorted."""
    return sorted(str(json_at(edge, "node", "label")) for edge in json_list(data, "rows", "edges"))


_DJANGO_CLASSES_RENAMED = [
    pytest.param(
        lambda: register_lookup(DateTimeField, ExtractHour, lookup_name="hour_of_day"),
        {"occurred_at": ["hour_of_day"]},
        "occurredAt: {hourOfDay: 3}",
        ["dropped", "kept"],
        id="extract-hour-as-hour-of-day",
    ),
    pytest.param(
        lambda: register_lookup(BigIntegerField, Abs, lookup_name="magnitude"),
        {"signed_big": ["magnitude"]},
        'signedBig: {magnitude: "7"}',
        ["kept"],
        id="abs-as-magnitude",
    ),
    pytest.param(
        lambda: _instance_lookup(ScalarSpecimen, "label", IStartsWith, "begins"),
        {"label": ["begins"]},
        'label: {begins: "KE"}',
        ["kept"],
        id="istartswith-instance-registered-as-begins",
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "register",
        "fields",
        "where",
        "expected",
    ),
    _DJANGO_CLASSES_RENAMED,
)
def test_a_served_leaf_through_a_django_class_under_another_name_answers(
    register: Callable[[], contextlib.AbstractContextManager[object]],
    fields: dict[str, list[str]],
    where: str,
    expected: list[str],
) -> None:
    """A Django lookup or transform class registered under a new name builds and filters.

    The seal admits the class by identity, whatever name it is registered under, on a
    field class or on one field instance.
    """
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("dropped", kept=False)
    with register():
        schema = _served_schema(_specimen_set(fields))
        data = _post(schema, f"{{ rows(filter: {{{where}}}) {{ edges {{ node {{ label }} }} }} }}")
    assert _labels(data) == expected


_UNWALKED_SERVED_LEAVES = [
    pytest.param(
        lambda: NumberFilter(field_name="signed_big", method=_doubled_is),
        id="method-over-a-project-transform",
    ),
    pytest.param(
        lambda: _OwnFilterNumberFilter(field_name="signed_big", lookup_expr="doubled"),
        id="filter-override-over-a-project-transform",
    ),
    pytest.param(
        lambda: NumberFilter(field_name="twice", lookup_expr="exact"),
        id="declared-over-an-annotation",
    ),
    pytest.param(
        lambda: NumberFilter(field_name="signed_big__gt", method=_doubled_is),
        id="method-over-a-path-django-refuses",
    ),
    pytest.param(
        lambda: _OwnFilterNumberFilter(field_name="signed_big__gt"),
        id="filter-override-over-a-path-django-refuses",
    ),
    pytest.param(
        lambda: NumberFilter(field_name="parent__bogus"),
        id="name-past-a-relation-its-model-lacks",
    ),
    pytest.param(
        lambda: ModelMultipleChoiceFilter(
            field_name="children",
            lookup_expr="icontains",
            queryset=ScalarSpecimen.objects.all(),
        ),
        id="reverse-key-lookup-its-target-key-resolves",
    ),
]


@pytest.mark.parametrize("declare", _UNWALKED_SERVED_LEAVES)
def test_a_served_leaf_the_build_does_not_walk_builds(declare: Callable[[], Filter]) -> None:
    """A served leaf whose query is consumer code, or whose path the model cannot walk, builds.

    A ``method=`` filter and a ``filter`` override build their own query, over a path Django
    refuses too, and a queryset annotation has no walk from the model: no class reaches the
    seal from the build's walk, which leaves each to the request. A name past a relation the
    related model lacks is read on the rows a walked hop's type shapes, and a to-many key's
    lookup the target's key resolves is the comparison a walked hop makes, so neither is
    refused as unresolvable (``filters/base.py::refuse_unresolvable_lookup``).
    """
    with _doubled():
        _ = _serve_at_root(_specimen_set([], {"twice_of": declare()}))
        finalize_django_types()
    assert hasattr(sys.modules[INPUTS_MODULE_PATH], "SpecimenFilterInputType")


class _DoubledSpecimenFilter(FilterSet):
    """A set whose one declared leaf runs the project transform ``doubled``."""

    twice = NumberFilter(field_name="signed_big", lookup_expr="doubled")

    class Meta:
        model = ScalarSpecimen
        fields: ClassVar[list[str]] = []


@pytest.mark.django_db
def test_an_unserved_set_with_a_project_leaf_answers_through_its_own_resolver() -> None:
    """A set no connection serves keeps a project leaf: a project resolver applies it.

    ``FilterInput[...]`` and ``apply_sync`` run outside the visibility boundary, so the
    leaf builds and filters through ``doubled``.
    """
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("dropped", kept=False)
    with _doubled():
        output = _relay_node(ScalarSpecimen, ("label",), _DoubledSpecimenFilter, relay_node=False)

        def rows(
            info: strawberry.Info,
            filter: FilterInput[_DoubledSpecimenFilter],  # noqa: A002
        ) -> list[ScalarSpecimen]:
            queryset = ScalarSpecimen.objects.order_by("label")
            return list(_DoubledSpecimenFilter.apply_sync(filter, queryset, info))

        query = strawberry.type(
            type(
                "Query",
                (),
                {
                    "__annotations__": {"rows": list[output]},
                    "rows": strawberry.field(resolver=rows),
                },
            ),
        )
        finalize_django_types()
        schema = DjangoSchema(query=query, config=strawberry_config())
        data = _post(schema, "{ rows(filter: {twice: {doubled: 14}}) { label } }")
    assert data == {"rows": [{"label": "kept"}]}


@pytest.mark.parametrize("served", [True, False], ids=["served", "unserved"])
def test_all_leaves_out_a_project_lookup_on_its_column(*, served: bool) -> None:
    """``"__all__"`` publishes no lookup class that is not Django's own, served or not.

    The set builds either way, with the column's Django lookups and without ``ne``.
    """
    with _not_equal_on_big():
        filterset_cls = _specimen_set({"signed_big": "__all__"})
        if served:
            _ = _serve_at_root(filterset_cls)
        else:
            _ = _relay_node(ScalarSpecimen, ("id",), filterset_cls, relay_node=False)
        finalize_django_types()
    assert "signed_big__ne" not in filterset_cls.base_filters
    assert {"signed_big", "signed_big__gt", "signed_big__in"} <= set(filterset_cls.base_filters)


def test_registry_clear_clears_the_connection_served_ledger() -> None:
    """A connection records its set as served until ``registry.clear()`` resets the ledger."""
    filterset_cls = _specimen_set({"signed_big": ["exact"]})
    _ = _serve_at_root(filterset_cls)
    assert filterset_cls in _connection_served_filtersets

    registry.clear()

    assert _connection_served_filtersets == set()


def _signed_big_is(qs: QuerySet[Model], value: object) -> QuerySet[Model]:
    """A consumer ``filter``: rows whose ``signed_big`` is ``value``, no transform applied."""
    if value in (None, ""):
        return qs
    return qs.filter(signed_big=value)


class _SignedBigIsFilter(NumberFilter):
    """A consumer ``NumberFilter`` whose class-level ``filter`` override owns its query."""

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        return _signed_big_is(qs, value)


class _HeldSignedBigIsFilter(NumberFilter):
    """A consumer ``NumberFilter`` whose ``__init__`` holds its own ``filter`` on the instance."""

    def __init__(self, *, field_name: str, lookup_expr: str) -> None:
        super().__init__(field_name=field_name, lookup_expr=lookup_expr)
        self.filter = _signed_big_is


class _InitOverridingChildFilter(FilterSet):
    """A child set overriding ``__init__``, whose leaf's ``filter`` override owns its query.

    The override makes the parent's expansion project the child's leaves, so a flat copy
    runs package code that answers for the child's own ``filter``.
    """

    twice = _SignedBigIsFilter(field_name="signed_big", lookup_expr="doubled")

    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)

    class Meta:
        model = ScalarSpecimen
        fields: ClassVar[list[str]] = ["label"]


class _HeldFilterChildFilter(FilterSet):
    """A child set whose leaf holds its own ``filter`` on the instance."""

    twice = _HeldSignedBigIsFilter(field_name="signed_big", lookup_expr="doubled")

    class Meta:
        model = ScalarSpecimen
        fields: ClassVar[list[str]] = ["label"]


def _seed_partners() -> None:
    """A partner of the kept specimen (``signed_big`` 7) and one of the dropped (900)."""
    NullableScalarSpecimen.objects.create(label="pa", partner=cleaned_specimen("a", kept=True))
    NullableScalarSpecimen.objects.create(label="pb", partner=cleaned_specimen("b", kept=False))


def _partner_rows_schema(child: type[FilterSet]) -> strawberry.Schema:
    """Serve a partner set reaching ``child`` through ``partner`` at the root ``rows``."""
    parent = _specimen_set(
        ["label"],
        {"partner": RelatedFilter(child, field_name="partner")},
        name="PartnerFilter",
        model=NullableScalarSpecimen,
    )
    _ = _relay_node(ScalarSpecimen, ("id", "label"), None)
    return _served_schema(parent, NullableScalarSpecimen)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "child",
    [_InitOverridingChildFilter, _HeldFilterChildFilter],
    ids=["child-overriding-init", "leaf-holding-its-own-filter"],
)
def test_a_related_child_leaf_whose_filter_is_its_own_answers(child: type[FilterSet]) -> None:
    """A ``RelatedFilter`` child's leaf whose ``filter`` is consumer code builds and answers.

    The leaf is judged on the child set that declares it, never through the parent's flat
    copy (a projected copy runs package code that answers for the child's own ``filter``),
    so its ``filter`` owns its query, nested and flat alike.
    """
    _seed_partners()
    with _doubled():
        schema = _partner_rows_schema(child)
        nested = _post(
            schema,
            "{ rows(filter: {partner: {twice: {doubled: 7}}}) { edges { node { label } } } }",
        )
        flat = _post(
            schema,
            "{ rows(filter: {partnerTwice: {doubled: 7}}) { edges { node { label } } } }",
        )
    assert _labels(nested) == _labels(flat) == ["pa"]


def test_a_related_child_leaf_is_refused_without_its_flat_copy() -> None:
    """A child set the nested branch serves is asked itself, whatever flat copies the parent keeps.

    The parent's ``get_filters`` drops every flat copy, so the child's leaf reaches the
    connection only as the nested branch's, and is refused naming the child's declaration.
    """

    class ChildFilter(FilterSet):
        twice = NumberFilter(field_name="signed_big", lookup_expr="doubled")

        class Meta:
            model = ScalarSpecimen
            fields: ClassVar[list[str]] = ["label"]

    class PartnerFilter(FilterSet):
        partner = RelatedFilter(ChildFilter, field_name="partner")

        class Meta:
            model = NullableScalarSpecimen
            fields: ClassVar[list[str]] = ["label"]

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            own = super().get_filters()
            return OrderedDict((name, leaf) for name, leaf in own.items() if "__" not in name)

    with _doubled():
        _ = _relay_node(ScalarSpecimen, ("id", "label"), None)
        _ = _serve_at_root(PartnerFilter)
        assert "partner__twice" not in PartnerFilter._filter_table()
        with pytest.raises(ConfigurationError) as exc_info:
            finalize_django_types()
    subject = (
        "ChildFilter.twice: NumberFilter on 'signed_big' (reached through PartnerFilter.partner)"
    )
    assert str(exc_info.value) == _unsealable_refusal(subject, "doubled", _Doubled)


@pytest.mark.django_db
def test_a_related_child_behind_a_dropped_branch_builds() -> None:
    """A child set whose branch the parent's ``get_filters`` drops is served by no connection.

    The parent declares the ``RelatedFilter`` but publishes neither its branch nor its flat
    copies, so no request reaches the child, and its project leaf builds; the parent's own
    ``label`` filter answers.
    """
    _seed_partners()

    class ChildFilter(FilterSet):
        twice = NumberFilter(field_name="signed_big", lookup_expr="doubled")

        class Meta:
            model = ScalarSpecimen
            fields: ClassVar[list[str]] = ["label"]

    class PartnerFilter(FilterSet):
        partner = RelatedFilter(ChildFilter, field_name="partner")

        class Meta:
            model = NullableScalarSpecimen
            fields: ClassVar[list[str]] = ["label"]

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            own = super().get_filters()
            return OrderedDict(
                (name, leaf) for name, leaf in own.items() if not name.startswith("partner")
            )

    with _doubled():
        _ = _relay_node(ScalarSpecimen, ("id", "label"), None)
        schema = _served_schema(PartnerFilter, NullableScalarSpecimen)
        data = _post(
            schema,
            '{ rows(filter: {label: {exact: "pa"}}) { edges { node { label } } } }',
        )
    assert _labels(data) == ["pa"]


def _keep_head_under_its_name(own: OrderedDict[str, Filter]) -> OrderedDict[str, Filter]:
    """Replace the ``partner`` head with a deep copy under its declared name, dropping its flat copies."""
    kept = OrderedDict((name, leaf) for name, leaf in own.items() if "__" not in name)
    kept["partner"] = copy.deepcopy(kept["partner"])
    return kept


def _deep_copy_every_filter(own: OrderedDict[str, Filter]) -> OrderedDict[str, Filter]:
    """Return a deep copy of every filter, the head and its flat copies included."""
    return copy.deepcopy(own)


def _move_head_to_a_new_key(own: OrderedDict[str, Filter]) -> OrderedDict[str, Filter]:
    """Publish the declared ``partner`` head itself under another key, dropping its flat copies."""
    kept = OrderedDict(
        (name, leaf) for name, leaf in own.items() if not name.startswith("partner")
    )
    kept["counterpart"] = own["partner"]
    return kept


def _keep_only_the_flat_copies(own: OrderedDict[str, Filter]) -> OrderedDict[str, Filter]:
    """Drop the ``partner`` head, keeping its flat copies."""
    return OrderedDict((name, leaf) for name, leaf in own.items() if name != "partner")


@pytest.mark.parametrize(
    "reshape",
    [
        _keep_head_under_its_name,
        _deep_copy_every_filter,
        _move_head_to_a_new_key,
        _keep_only_the_flat_copies,
    ],
    ids=[
        "deep-copied-head-under-its-name",
        "deep-copy-of-every-filter",
        "declared-head-under-a-new-key",
        "flat-copies-without-the-head",
    ],
)
def test_a_related_child_behind_a_copied_branch_is_refused(
    reshape: Callable[[OrderedDict[str, Filter]], OrderedDict[str, Filter]],
) -> None:
    """A parent ``get_filters`` publishing a copy of its branch still serves the child.

    A deep copy of the branch under its declared name, a deep copy of every filter, the
    declared ``RelatedFilter`` under another key, or the branch's flat copies alone (each
    recording the child set) still reach the child, so its project leaf is refused naming
    the child's declaration and the branch.
    """

    class ChildFilter(FilterSet):
        twice = NumberFilter(field_name="signed_big", lookup_expr="doubled")

        class Meta:
            model = ScalarSpecimen
            fields: ClassVar[list[str]] = ["label"]

    class PartnerFilter(FilterSet):
        partner = RelatedFilter(ChildFilter, field_name="partner")

        class Meta:
            model = NullableScalarSpecimen
            fields: ClassVar[list[str]] = ["label"]

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            return reshape(super().get_filters())

    with _doubled():
        _ = _relay_node(ScalarSpecimen, ("id", "label"), None)
        _ = _serve_at_root(PartnerFilter)
        with pytest.raises(ConfigurationError) as exc_info:
            finalize_django_types()
    subject = (
        "ChildFilter.twice: NumberFilter on 'signed_big' (reached through PartnerFilter.partner)"
    )
    assert str(exc_info.value) == _unsealable_refusal(subject, "doubled", _Doubled)


def _hidden_copies_partner_set(*, keep_head: bool) -> type[FilterSet]:
    """A partner set reaching a child with a project leaf, its head kept or popped, copies kept."""

    class ChildFilter(FilterSet):
        twice = NumberFilter(field_name="signed_big", lookup_expr="doubled")

        class Meta:
            model = ScalarSpecimen
            fields: ClassVar[list[str]] = ["label"]

    class PartnerFilter(FilterSet):
        partner = RelatedFilter(ChildFilter, field_name="partner")

        class Meta:
            model = NullableScalarSpecimen
            fields: ClassVar[list[str]] = ["label"]

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            own = super().get_filters()
            if keep_head:
                return own
            return _keep_only_the_flat_copies(own)

    return PartnerFilter


@pytest.mark.django_db
def test_a_related_child_behind_hidden_flat_copies_alone_builds() -> None:
    """Flat copies ``HIDE_FLAT_FILTERS`` hides, with the branch popped, serve the child nothing.

    The schema publishes neither the branch nor its copies, so no request reaches the
    child, and its project leaf builds; the parent's own ``label`` filter answers.
    """
    _seed_partners()
    with (
        override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"HIDE_FLAT_FILTERS": True}),
        _doubled(),
    ):
        _ = _relay_node(ScalarSpecimen, ("id", "label"), None)
        schema = _served_schema(
            _hidden_copies_partner_set(keep_head=False),
            NullableScalarSpecimen,
        )
        data = _post(
            schema,
            '{ rows(filter: {label: {exact: "pa"}}) { edges { node { label } } } }',
        )
    assert _labels(data) == ["pa"]


def test_a_related_child_behind_hidden_flat_copies_is_refused_through_its_branch() -> None:
    """With ``HIDE_FLAT_FILTERS`` set, the branch the table keeps still serves the child."""
    with (
        override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"HIDE_FLAT_FILTERS": True}),
        _doubled(),
    ):
        _ = _relay_node(ScalarSpecimen, ("id", "label"), None)
        _ = _serve_at_root(_hidden_copies_partner_set(keep_head=True))
        with pytest.raises(ConfigurationError) as exc_info:
            finalize_django_types()
    subject = (
        "ChildFilter.twice: NumberFilter on 'signed_big' (reached through PartnerFilter.partner)"
    )
    assert str(exc_info.value) == _unsealable_refusal(subject, "doubled", _Doubled)


# ---------------------------------------------------------------------------
# A declared predicate Django resolves on no queryset.
# ---------------------------------------------------------------------------


class _NumberRangeFilter(BaseRangeFilter, NumberFilter):
    """django-filter's CSV ``range`` filter over numbers, which hands Django its ``range`` whole."""


@dataclass(frozen=True)
class _UnresolvableCase:
    """A declared leaf whose predicate Django resolves on no queryset, and what its refusal names."""

    declare: Callable[[], Filter]
    model: type[Model]
    kind: str
    field_name: str
    lookup_expr: str
    part: str
    field: str


def _scalar_specimens() -> QuerySet[ScalarSpecimen]:
    return ScalarSpecimen.objects.all()


_UNRESOLVABLE_LEAVES: dict[str, _UnresolvableCase] = {
    "column-lookup-spelled-in-field-name": _UnresolvableCase(
        lambda: NumberFilter(field_name="signed_big__gt"),
        ScalarSpecimen,
        "NumberFilter",
        "signed_big__gt",
        "exact",
        "gt",
        "ScalarSpecimen.signed_big (BigIntegerField)",
    ),
    "no-transform-past-a-transform": _UnresolvableCase(
        lambda: NumberFilter(field_name="occurred_at__year__gt"),
        ScalarSpecimen,
        "NumberFilter",
        "occurred_at__year__gt",
        "exact",
        "gt",
        "ScalarSpecimen.occurred_at (DateTimeField)",
    ),
    "lookup-no-field-registers": _UnresolvableCase(
        lambda: CharFilter(field_name="label", lookup_expr="unaccent"),
        ScalarSpecimen,
        "CharFilter",
        "label",
        "unaccent",
        "unaccent",
        "ScalarSpecimen.label (TextField)",
    ),
    "column-past-a-forward-hop": _UnresolvableCase(
        lambda: CharFilter(field_name="parent__label__icontains"),
        ScalarSpecimen,
        "CharFilter",
        "parent__label__icontains",
        "exact",
        "icontains",
        "ScalarSpecimen.label (TextField)",
    ),
    "column-past-a-reverse-hop": _UnresolvableCase(
        lambda: NumberFilter(field_name="children__signed_big__gt"),
        ScalarSpecimen,
        "NumberFilter",
        "children__signed_big__gt",
        "exact",
        "gt",
        "ScalarSpecimen.signed_big (BigIntegerField)",
    ),
    "column-past-a-many-to-many-hop": _UnresolvableCase(
        lambda: CharFilter(field_name="genres__name__typo"),
        Book,
        "CharFilter",
        "genres__name__typo",
        "exact",
        "typo",
        "Genre.name (TextField)",
    ),
    "forward-key-lookup-its-target-key-resolves": _UnresolvableCase(
        lambda: ModelChoiceFilter(
            field_name="parent",
            lookup_expr="icontains",
            queryset=_scalar_specimens(),
        ),
        ScalarSpecimen,
        "ModelChoiceFilter",
        "parent",
        "icontains",
        "icontains",
        "ScalarSpecimen.parent (ForeignKey)",
    ),
    "forward-key-lookup-nothing-resolves": _UnresolvableCase(
        lambda: ModelChoiceFilter(
            field_name="parent",
            lookup_expr="unknown",
            queryset=_scalar_specimens(),
        ),
        ScalarSpecimen,
        "ModelChoiceFilter",
        "parent",
        "unknown",
        "unknown",
        "ScalarSpecimen.parent (ForeignKey)",
    ),
    "forward-key-range-handed-whole": _UnresolvableCase(
        lambda: _NumberRangeFilter(field_name="branch", lookup_expr="range"),
        Shelf,
        "_NumberRangeFilter",
        "branch",
        "range",
        "range",
        "Shelf.branch (ForeignKey)",
    ),
    "forward-key-range-its-walk-refuses": _UnresolvableCase(
        lambda: RangeFilter(field_name="branch", lookup_expr="range"),
        Shelf,
        "RangeFilter",
        "branch",
        "range",
        "range",
        "Shelf.branch (ForeignKey)",
    ),
    "reverse-one-to-one-key-lookup": _UnresolvableCase(
        lambda: CharFilter(field_name="profile", lookup_expr="icontains"),
        Patron,
        "CharFilter",
        "profile",
        "icontains",
        "icontains",
        "Patron.profile (OneToOneRel)",
    ),
    "reverse-key-lookup-no-relation-resolves": _UnresolvableCase(
        lambda: ModelMultipleChoiceFilter(
            field_name="children",
            lookup_expr="unknown",
            queryset=_scalar_specimens(),
        ),
        ScalarSpecimen,
        "ModelMultipleChoiceFilter",
        "children",
        "unknown",
        "unknown",
        "ScalarSpecimen.children (ManyToOneRel)",
    ),
    "many-to-many-key-lookup-no-relation-resolves": _UnresolvableCase(
        lambda: ModelMultipleChoiceFilter(
            field_name="genres",
            lookup_expr="unknown",
            queryset=Genre.objects.all(),
        ),
        Book,
        "ModelMultipleChoiceFilter",
        "genres",
        "unknown",
        "unknown",
        "Book.genres (ManyToManyField)",
    ),
}


def _unresolvable_refusal(case: _UnresolvableCase) -> str:
    """The refusal of the leaf ``probe`` ``case`` declares on ``SpecimenFilter``."""
    return (
        f"FilterSet SpecimenFilter: {case.kind} 'probe' has field_name {case.field_name!r} and "
        f"lookup_expr {case.lookup_expr!r}, but Django resolves no transform or lookup "
        f"{case.part!r} on {case.field}, so every request naming the filter would be refused. "
        "Spell the transforms and lookup the field registers (a column's lookups belong in "
        "lookup_expr, not field_name), register a project lookup at startup "
        "(Field.register_lookup in AppConfig.ready), or read the value in `method=`."
    )


def _build_at_root(filterset_cls: type[FilterSet]) -> None:
    _ = _serve_at_root(filterset_cls)
    finalize_django_types()


def _build_nested_only(filterset_cls: type[FilterSet]) -> None:
    """Serve ``filterset_cls`` (over ``ScalarSpecimen``) only as the ``childrenConnection``."""
    _ = _relay_node(ScalarSpecimen, ("id", "children"), filterset_cls)
    finalize_django_types()


def _build_through_related_filter(filterset_cls: type[FilterSet]) -> None:
    _serve_through_related_filter(filterset_cls)
    finalize_django_types()


def _build_unserved_filter_input(filterset_cls: type[FilterSet]) -> None:
    """Bind ``filterset_cls`` to a type no connection serves, applied through ``FilterInput``."""
    model = filterset_cls._meta.model
    assert model is not None
    output = _relay_node(model, ("id",), filterset_cls, relay_node=False)

    def rows(
        info: strawberry.Info,
        filter: object,  # noqa: A002
    ) -> list[Model]:
        return list(filterset_cls.apply_sync(filter, model._default_manager.all(), info))

    # The input class is the set's own, which only a runtime annotation can name.
    rows.__annotations__["filter"] = FilterInput[filterset_cls]
    query = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"rows": list[output]}, "rows": strawberry.field(resolver=rows)},
        ),
    )
    finalize_django_types()
    _ = DjangoSchema(query=query, config=strawberry_config())


def _apply_unbound(filterset_cls: type[FilterSet]) -> None:
    """Apply ``filterset_cls``, bound to no type, from a resolver of the project's own."""
    model = filterset_cls._meta.model
    assert model is not None
    finalize_django_types()
    _ = filterset_cls.apply_sync({}, model._default_manager.all(), None)


_UNRESOLVABLE_SERVINGS: dict[str, Callable[[type[FilterSet]], None]] = {
    "root-connection": _build_at_root,
    "nested-connection": _build_nested_only,
    "related-filter-reached": _build_through_related_filter,
    "unserved-filter-input": _build_unserved_filter_input,
    "apply-sync-first-use": _apply_unbound,
}

#: The servings that read the set over a ``ScalarSpecimen`` as one served nested or reached.
_SPECIMEN_ONLY_SERVINGS = frozenset({"nested-connection", "related-filter-reached"})


@pytest.mark.parametrize(
    ("case", "serve"),
    [
        pytest.param(
            _UNRESOLVABLE_LEAVES[case_id],
            _UNRESOLVABLE_SERVINGS[serving],
            id=f"{case_id}-{serving}",
        )
        for case_id in _UNRESOLVABLE_LEAVES
        for serving in _UNRESOLVABLE_SERVINGS
        if _UNRESOLVABLE_LEAVES[case_id].model is ScalarSpecimen
        or serving not in _SPECIMEN_ONLY_SERVINGS
    ],
)
def test_a_declared_leaf_django_resolves_on_no_queryset_is_refused(
    case: _UnresolvableCase,
    serve: Callable[[type[FilterSet]], None],
) -> None:
    """A declared leaf whose path and lookup Django refuses on every queryset fails its set.

    Where the path ends on a column, on a to-one relation (read through the relation's own
    lookups on every request), or on a to-many relation none of whose key columns accepts the
    lookup either, Django refuses the predicate whatever rows it runs on, so the set refuses
    the leaf when it publishes: a served set when the schema builds, an unbound one at its
    first use. The refusal names the set, the filter class and name, its ``field_name`` and
    ``lookup_expr``, the part Django refuses and the field it is refused on, chained from the
    walk's ``LookupValidationError``.
    """
    filterset_cls = _specimen_set([], {"probe": case.declare()}, model=case.model)
    with pytest.raises(ConfigurationError) as exc_info:
        serve(filterset_cls)
    assert str(exc_info.value) == _unresolvable_refusal(case)
    cause = exc_info.value.__cause__
    assert isinstance(cause, LookupValidationError)
    assert cause.part == case.part


@pytest.mark.parametrize(
    "path",
    ["signed_big__magnitude", "signed_big"],
    ids=["transform", "lookup"],
)
def test_a_lookup_registered_before_the_set_publishes_builds(path: str) -> None:
    """A project registration in place when the set publishes resolves the leaf: it builds."""
    lookup_expr = "exact" if path.endswith("magnitude") else "magnitude"
    with register_lookup(BigIntegerField, Abs, lookup_name="magnitude"):
        _build_at_root(
            _specimen_set([], {"probe": NumberFilter(field_name=path, lookup_expr=lookup_expr)}),
        )
    assert hasattr(sys.modules[INPUTS_MODULE_PATH], "SpecimenFilterInputType")


def test_a_lookup_registered_after_a_set_publishes_is_not_seen_by_the_next_set() -> None:
    """Nothing is kept between sets: a registration gone when the next set publishes refuses it.

    The first set publishes while ``magnitude`` is registered and builds; the second
    declares the same leaf once the registration is gone and is refused at its first use,
    as one declared before the registration is (Django registers lookups at startup).
    """
    with register_lookup(BigIntegerField, Abs, lookup_name="magnitude"):
        _build_at_root(
            _specimen_set([], {"probe": NumberFilter(field_name="signed_big__magnitude")}),
        )
    later = _specimen_set(
        [],
        {"probe": NumberFilter(field_name="signed_big__magnitude")},
        name="LaterFilter",
    )
    with pytest.raises(ConfigurationError) as exc_info:
        _ = later.get_filters()
    assert str(exc_info.value).startswith(
        "FilterSet LaterFilter: NumberFilter 'probe' has field_name 'signed_big__magnitude' and "
        "lookup_expr 'exact', but Django resolves no transform or lookup 'magnitude' on "
        "ScalarSpecimen.signed_big (BigIntegerField)",
    )


def _twice(queryset: QuerySet[Model]) -> QuerySet[Model]:
    return queryset.annotate(twice=F("signed_big") * 2)


def _shaping_node(
    model: type[Model],
    shape: Callable[[QuerySet[Model]], QuerySet[Model]],
    filterset_cls: type[FilterSet] | None = None,
) -> type[DjangoType]:
    """A Relay ``DjangoType`` over ``model`` whose ``get_queryset`` hands back ``shape``'s rows."""

    def get_queryset(
        cls: type[DjangoType],
        queryset: QuerySet[Model],
        info: object,
        **kwargs: object,
    ) -> QuerySet[Model]:
        del cls, info, kwargs
        return shape(queryset)

    meta: dict[str, object] = {
        "model": model,
        "fields": ("id", "label"),
        "interfaces": (relay.Node,),
    }
    if filterset_cls is not None:
        meta["filterset_class"] = filterset_cls
    node = type(
        f"{model.__name__}Node",
        (DjangoType,),
        {"Meta": type("Meta", (), meta), "get_queryset": classmethod(get_queryset)},
    )
    assert issubclass(node, DjangoType)
    return node


@pytest.mark.django_db
def test_a_name_past_a_declared_hop_its_target_type_annotates_answers() -> None:
    """A name the related model lacks is read on the rows the hop's type shapes: it answers.

    ``partner__twice`` past the declared ``partner`` hop names no field of
    ``ScalarSpecimen``; the hop's type annotates ``twice`` onto the rows it walks, so the
    leaf is not judged unresolvable and filters on the annotation.
    """
    kept = cleaned_specimen("kept", kept=True)
    dropped = cleaned_specimen("dropped", kept=False)
    _ = NullableScalarSpecimen.objects.create(label="kept-partner", partner=kept)
    _ = NullableScalarSpecimen.objects.create(label="dropped-partner", partner=dropped)
    parent = _specimen_set(
        {"label": ["exact"]},
        {
            "partner": RelatedFilter(_specimen_set({"label": ["exact"]}), field_name="partner"),
            "partner_twice": NumberFilter(field_name="partner__twice"),
        },
        name="PartnerFilter",
        model=NullableScalarSpecimen,
    )
    _ = _shaping_node(ScalarSpecimen, _twice)
    schema = _served_schema(parent, NullableScalarSpecimen)
    data = _post(
        schema,
        f'{{ rows(filter: {{partnerTwice: {{exact: "{kept.signed_big * 2}"}}}}) '
        "{ edges { node { label } } } }",
    )
    assert _labels(data) == ["kept-partner"]


@pytest.mark.django_db
def test_a_reverse_key_lookup_its_target_key_resolves_answers_on_a_walked_hop() -> None:
    """A to-many key's lookup compares the target key on a walked hop: it builds and answers.

    ``children`` with ``icontains`` is no lookup of the reverse relation, but the target
    type's ``get_queryset`` walks the hop, which compares the children's primary key, whose
    column registers ``icontains``.
    """
    parent = cleaned_specimen("parent", kept=True)
    child = cleaned_specimen("child", kept=False)
    child.parent = parent
    child.save()
    filterset_cls = _specimen_set(
        [],
        {
            "probe": ModelMultipleChoiceFilter(
                field_name="children",
                lookup_expr="icontains",
                queryset=_scalar_specimens(),
            ),
        },
    )
    node = _shaping_node(ScalarSpecimen, lambda queryset: queryset, filterset_cls)
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"rows": DjangoConnection[node]},
                "rows": DjangoConnectionField(node),
            },
        ),
    )
    finalize_django_types()
    schema = DjangoSchema(query=query, config=strawberry_config())
    data = _post(
        schema,
        f"{{ rows(filter: {{probe: {{iContains: [{saved_pk(child)}]}}}}) "
        "{ edges { node { label } } } }",
    )
    assert _labels(data) == ["parent"]


@pytest.mark.parametrize(
    ("declare", "model"),
    [
        pytest.param(
            lambda: IntegerRangeFilter(field_name="branch", lookup_expr="range"),
            Shelf,
            id="integer-range",
        ),
        pytest.param(
            lambda: DjangoFilterRangeFilter(field_name="branch", lookup_expr="range"),
            Shelf,
            id="django-filter-range",
        ),
        pytest.param(
            lambda: RangeFilter(field_name="branch__pk", lookup_expr="range"),
            Shelf,
            id="range-over-the-key-column",
        ),
        pytest.param(
            lambda: RangeFilter(field_name="pk", lookup_expr="range"),
            PatronProfile,
            id="range-over-a-relation-valued-pk",
        ),
    ],
)
def test_a_range_applied_as_bounds_over_a_forward_key_publishes(
    declare: Callable[[], Filter],
    model: type[Model],
) -> None:
    """A filter applying a ``range`` the relation's lookups or its key's column take publishes.

    Django registers no ``range`` on a relation; ``IntegerRangeFilter`` applies both bounds,
    and django-filter's ``RangeFilter`` a lone one, as the relation's ``gte`` / ``lte``;
    ``branch__pk`` names the key's own column, and the package ``RangeFilter`` over a
    relation-valued ``pk`` ranges the column the key stores. None is refused.
    """
    filterset_cls = _specimen_set([], {"probe": declare()}, model=model)
    assert "probe" in filterset_cls.get_filters()


def test_a_declared_leaf_of_a_set_with_no_model_publishes() -> None:
    """A set declaring no ``Meta.model`` has no model to resolve a path on: its leaf publishes.

    The unresolvable-lookup refusal does not ask it; the missing ``Meta.model`` is refused on
    its own terms, when a type binds the set or when a leaf of it is applied unbound.
    """
    modelless = _specimen_set([], {"probe": NumberFilter(field_name="signed_big__gt")}, model=None)
    assert "probe" in modelless.get_filters()


def _respelled(filter_instance: Filter, **values: object) -> Filter:
    """``filter_instance`` with each of ``values`` set on it as a consumer may set a lazy value.

    The stubs type ``field_name`` and ``lookup_expr`` as ``str``; a project hands Django's lazy
    text (``gettext_lazy``, ``SimpleLazyObject``) where a ``str`` is read.
    """
    for name, value in values.items():
        setattr(filter_instance, name, value)
    return filter_instance


@pytest.mark.django_db
@pytest.mark.parametrize(
    "declare",
    [
        pytest.param(
            lambda: _respelled(
                NumberFilter(field_name="signed_big"),
                lookup_expr=gettext_lazy("gt"),
            ),
            id="lazy-lookup-expr",
        ),
        pytest.param(
            lambda: _respelled(
                NumberFilter(lookup_expr="gt"),
                field_name=SimpleLazyObject(lambda: "signed_big"),
            ),
            id="lazy-field-name",
        ),
    ],
)
def test_a_declared_leaf_spelled_lazily_builds_and_answers(declare: Callable[[], Filter]) -> None:
    """A lazy ``field_name`` or ``lookup_expr`` is read as the text it renders, as django-filter does.

    django-filter formats ``field_name`` and ``lookup_expr`` into the predicate's argument,
    so the set publishes the leaf and a request filters by it.
    """
    _ = cleaned_specimen("small", kept=True)
    _ = cleaned_specimen("large", kept=False)
    schema = _served_schema(_specimen_set([], {"probe": declare()}))
    data = _post(schema, '{ rows(filter: {probe: {gt: "7"}}) { edges { node { label } } } }')
    assert _labels(data) == ["large"]


def test_a_lazily_spelled_lookup_django_resolves_nowhere_is_refused_naming_its_text() -> None:
    """A lazy ``lookup_expr`` naming no lookup is refused, naming the text it renders."""
    filterset_cls = _specimen_set(
        [],
        {
            "probe": _respelled(
                NumberFilter(field_name="signed_big"),
                lookup_expr=gettext_lazy("unknown"),
            ),
        },
    )
    with pytest.raises(ConfigurationError) as exc_info:
        _build_at_root(filterset_cls)
    assert str(exc_info.value).startswith(
        "FilterSet SpecimenFilter: NumberFilter 'probe' has field_name 'signed_big' and "
        "lookup_expr 'unknown', but Django resolves no transform or lookup 'unknown' on "
        "ScalarSpecimen.signed_big (BigIntegerField)",
    )
