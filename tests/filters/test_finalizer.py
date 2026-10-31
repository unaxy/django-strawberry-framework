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

Bound and unbound filtersets answering requests live in ``test_query/``.
``test_filter_declarations_api.py`` owns copyable callable and widget controls
and independently owned enums. This file keeps exact class-owner slots,
finalize-time refusal and ordering, orphan rejection, and registry reset.
"""

from __future__ import annotations

import functools
import sys
import threading
from collections import OrderedDict
from collections.abc import Callable, Iterator
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
    ProxyBranch,
    Shelf,
    TaggedItem,
    Venue,
)
from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches
from django.db.models import Model, QuerySet, TextField
from django.http import HttpRequest
from django.test import override_settings
from django_filters import BooleanFilter, CharFilter, Filter, NumberFilter
from strawberry import relay
from typing_extensions import override

if TYPE_CHECKING:
    from typing_extensions import TypeIs

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    FilterInput,
    FilterSet,
    GlobalIDFilter,
    ListFilter,
    RelatedFilter,
    _helper_referenced_filtersets,
    filter_input_type,
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
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import is_dict, is_str, read_attr, require
from django_strawberry_framework.utils.typing import object_result
from tests._idioms import saved_pk
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
