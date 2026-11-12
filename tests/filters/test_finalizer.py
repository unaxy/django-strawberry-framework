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
- A filter a deep copy refuses fails the build naming its set and the key its
  table publishes it under (every published table a served set reaches by the
  subpass-2.5 copy audit, with the ``RelatedFilter`` path for a reached set, a
  ``get_filters()`` override's additions and in-place edits included; an unserved
  ``RelatedFilter`` child's by the expansion copy when it copies first).
- A declared leaf whose ``field_name`` and ``lookup_expr`` Django resolves on no
  queryset is refused when its set publishes, under every serving shape (a relation
  key's lookup asked of the relation, to-one or to-many), while the shapes Django
  resolves on some queryset (a name past a relation, a range applied as a relation's
  bounds) build; a raw set declaring such a to-many key leaf is refused at its first
  construction, as at the package's first read, whether or not a hop is walked.
- A model-choice filter with no queryset (none passed, a ``Meta.filter_overrides``
  selection without ``extra``) is refused when its set publishes, under every serving
  shape, while consumer code that can give one per request (a ``get_queryset`` or ``field``
  override, a form field ``__init__``, a ``get_filters()`` edit, a set ``__init__``,
  ``get_form_class`` or ``form``) builds.

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

import django_filters
import pytest
import strawberry
from apps.kanban.models import Actor, Card, CardItem, CardPathLink
from apps.library.models import (
    Book,
    Branch,
    Edition,
    Genre,
    KioskFault,
    LendingDesk,
    Loan,
    MembershipCard,
    Patron,
    PatronProfile,
    Printing,
    ProxyBranch,
    Publisher,
    RepairTicket,
    SelfServeDesk,
    Shelf,
    TaggedItem,
    Venue,
)
from apps.scalars.models import NullableScalarSpecimen, ScalarSpecimen
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches
from django.core.exceptions import FieldError
from django.db import connection
from django.db.models import (
    BigIntegerField,
    CharField,
    DateTimeField,
    F,
    ForeignKey,
    IntegerField,
    Lookup,
    Model,
    QuerySet,
    TextChoices,
    TextField,
    Transform,
)
from django.db.models import Field as ModelFieldClass
from django.db.models.functions import Abs, ExtractHour
from django.db.models.lookups import GreaterThan, IStartsWith
from django.http import HttpRequest, QueryDict
from django.test import override_settings
from django.test.utils import CaptureQueriesContext, isolate_apps, register_lookup
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
from django_filters.fields import ChoiceField as ChoiceFormField
from django_filters.filters import BaseRangeFilter, QuerySetRequestMixin
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
    ErrorPolicy,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError, LookupValidationError
from django_strawberry_framework.filters import (
    ArrayFilter,
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
from django_strawberry_framework.filters import inputs as filter_inputs_module
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
    _bind_filterset_owner,
)
from django_strawberry_framework.types.relay import apply_interfaces
from django_strawberry_framework.utils import querysets as querysets_module
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import (
    is_dict,
    is_list_or_tuple,
    is_queryset,
    is_str,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.permissions import set_bound_definition
from django_strawberry_framework.utils.typing import object_result
from tests._cleaned_filter_sets import cleaned_specimen
from tests._idioms import json_at, json_list, saved_pk
from tests._relation_fixtures import RpCompositeParent
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
    at module-fallback resolution time (spec-027 Decision 3). The
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
    type's ``get_queryset`` (spec-027 Decision 8), so a
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
    naming the filterset and the request key.
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


def test_phase_2_5_rejects_a_callable_strategy_target_a_crossing_lookup_reaches() -> None:
    """A GlobalID filter whose ``lookup_expr`` crosses into an encode-only type fails at build.

    ``field_name="shelf", lookup_expr="branch"`` compares ``Branch`` keys, the target the
    request-time walk validates against (the path Django walks, ``shelf__branch``), so the
    audit refuses the encode-only ``Branch`` type rather than reading ``shelf`` alone.
    """

    def encode(_type_cls: type[DjangoType], _model: type[Model], _root: object) -> str:
        return "BranchType"

    class BranchType(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = encode

    class CrossingFilter(FilterSet):
        branch_is = GlobalIDFilter(field_name="shelf", lookup_expr="branch")

        class Meta:
            model = Book
            fields = ()

    class OwnerType(DjangoType):
        class Meta:
            model = Book
            fields = ("id",)
            interfaces = (relay.Node,)
            filterset_class = CrossingFilter
            primary = True

    assert registry.get(Branch) is BranchType
    assert registry.get(Book) is OwnerType

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    msg = str(exc_info.value)
    assert "CrossingFilter" in msg
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
    is neither the own PK nor a relation head, so ``_globalid_target`` resolves
    ``None`` for it during the audit and the filter is skipped (there is no
    target strategy to fail-close on). This is a legal filterset - the
    pre-existing unregistered-related-target audit only walks ``RelatedFilter``
    instances - so finalization succeeds.
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


def _encode_by_name(type_cls: type[DjangoType], _model: type[Model], _root: object) -> str:
    """A ``callable`` GlobalID strategy: encode-only, no decode path."""
    return type_cls.__name__


def _relay_type(
    model: type[Model],
    fields: tuple[str, ...],
    *,
    name: str,
    filterset_class: type[FilterSet] | None = None,
    strategy: object = None,
    primary: bool | None = None,
    hook: bool = False,
) -> type[DjangoType]:
    """Build a Relay ``DjangoType`` named ``name`` over ``model`` for the GlobalID audit rows."""
    meta: dict[str, object] = {"model": model, "fields": fields, "interfaces": (relay.Node,)}
    if filterset_class is not None:
        meta["filterset_class"] = filterset_class
    if strategy is not None:
        meta["globalid_strategy"] = strategy
    if primary is not None:
        meta["primary"] = primary
    namespace: dict[str, object] = {"Meta": type("Meta", (), meta)}
    if hook:

        def get_queryset(
            _cls: type[DjangoType],
            queryset: QuerySet[Model],
            _info: object,
            **_kwargs: object,
        ) -> QuerySet[Model]:
            return queryset.exclude(pk=0)

        namespace["get_queryset"] = classmethod(get_queryset)
    return type(name, (DjangoType,), namespace)


def _desk_world(desk_set: str) -> None:
    """A ticket set whose ``venue`` branch targets an unwired set over an MTI descendant of ``Venue``.

    ``"self_serve"``: ``SelfServeDeskFilter`` publishes ``faults`` into a ``callable``
    ``KioskFault`` type (``"self_serve_init"``: its ``__init__`` override projects every
    copy, so the ticket set holds no rebound copy of ``faults``; ``"self_serve_wired"``:
    ``SelfServeDeskType`` wires the desk set too); ``"lending"``: ``LendingDeskFilter``
    publishes ``selfservedesk`` into a ``callable`` ``SelfServeDesk`` type.
    """
    if desk_set in {"self_serve", "self_serve_init", "self_serve_wired"}:

        class SelfServeDeskFilter(FilterSet):
            class Meta:
                model = SelfServeDesk
                fields = {"kiosk_code": ["exact"], "faults": ["exact"]}

        class InitSelfServeDeskFilter(FilterSet):
            @override
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
                model = SelfServeDesk
                fields = {"kiosk_code": ["exact"], "faults": ["exact"]}

        target: type[FilterSet] = (
            InitSelfServeDeskFilter if desk_set == "self_serve_init" else SelfServeDeskFilter
        )
        _relay_type(KioskFault, ("id", "note"), name="FaultType", strategy=_encode_by_name)
        _relay_type(
            SelfServeDesk,
            ("id", "kiosk_code"),
            name="SelfServeDeskType",
            filterset_class=target if desk_set == "self_serve_wired" else None,
        )
    else:

        class LendingDeskFilter(FilterSet):
            class Meta:
                model = LendingDesk
                fields = {"window_count": ["exact"], "selfservedesk": ["exact"]}

        target = LendingDeskFilter
        _relay_type(
            SelfServeDesk,
            ("id", "kiosk_code"),
            name="SelfServeDeskType",
            strategy=_encode_by_name,
        )
        _relay_type(LendingDesk, ("id", "window_count"), name="LendingDeskType")

    class RepairTicketFilter(FilterSet):
        venue = RelatedFilter(target, field_name="venue")

        class Meta:
            model = RepairTicket
            fields = {"code": ["exact"]}

    _relay_type(
        RepairTicket,
        ("id", "code", "venue"),
        name="TicketType",
        filterset_class=RepairTicketFilter,
    )
    _relay_type(Venue, ("id", "name"), name="VenueType")


def _scoped_reentry_world(
    *,
    callable_primary: bool = False,
    key: str = "shelf__books",
    isnull: bool = False,
) -> None:
    """``key`` re-enters ``Book`` past undeclared hops; a scoping secondary owns the set.

    The secondary is ``callable`` and the primary ``model``; with ``callable_primary`` the
    primary is ``callable`` and the secondary ``type``. The to-many key decodes against
    the primary its relation reaches twice, in the declared predicate it builds on the
    owner's rows first (``_LeafChain.terminal_value``) and on the target rows, whose face
    answers for the secondary. ``key`` is ``shelf__books`` (a foreign key, then its
    reverse) or ``genres__books`` (a many-to-many, then its reverse). With ``isnull`` the
    set declares a ``GlobalIDFilter`` on ``key`` with ``lookup_expr="isnull"`` instead.
    """
    book_filter = type(
        "ReentryBookFilter",
        (FilterSet,),
        {
            **({"leaf": GlobalIDFilter(field_name=key, lookup_expr="isnull")} if isnull else {}),
            "Meta": type(
                "Meta",
                (),
                {"model": Book, "fields": [] if isnull else {key: ["exact"]}},
            ),
        },
    )
    _relay_type(
        Book,
        ("id", "title"),
        name="BookPrimary",
        primary=True,
        strategy=_encode_by_name if callable_primary else None,
    )
    _relay_type(
        Book,
        ("id", "title"),
        name="BookSecondary",
        filterset_class=book_filter,
        strategy="type" if callable_primary else _encode_by_name,
        hook=True,
    )


def _unwired_hop_world(
    *,
    init: bool = False,
    wired: bool = False,
    callable_branch: bool = True,
    flat: bool = True,
    method: bool = False,
) -> None:
    """``BookFilter.shelf`` targets an unwired ``ShelfFilter`` publishing a ``callable`` ``branch``.

    With ``init`` the shelf set overrides ``__init__``, so ``BookFilter`` holds only a
    projected copy of ``branch`` and the leaf is reached only through the nested branch;
    with ``wired`` ``ShelfType`` wires the shelf set too; without ``callable_branch`` the
    ``Branch`` type keeps the default strategy. ``flat`` is ``BookFilter.shelf``'s; with
    ``method`` the shelf set's ``branch`` is a ``method=`` decoder.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"], "branch": ["exact"]}

    class MethodShelfFilter(FilterSet):
        branch = GlobalIDFilter(field_name="branch", method="decode")

        def decode(
            self,
            queryset: QuerySet[Shelf],
            name: str,
            value: object,
        ) -> QuerySet[Shelf]:
            del name, value
            return queryset

        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    class InitShelfFilter(FilterSet):
        @override
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
            model = Shelf
            fields = {"code": ["exact"], "branch": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(
            InitShelfFilter if init else MethodShelfFilter if method else ShelfFilter,
            field_name="shelf",
            flat=flat,
        )

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    _relay_type(
        Branch,
        ("id", "name"),
        name="BranchType",
        strategy=_encode_by_name if callable_branch else None,
    )
    _relay_type(
        Shelf,
        ("id", "code", "branch"),
        name="ShelfType",
        filterset_class=ShelfFilter if wired else None,
    )
    _relay_type(Book, ("id", "title", "shelf"), name="BookType", filterset_class=BookFilter)


def _walked_own_leaf_world(
    *,
    shelf_id: bool = False,
    flat: bool = True,
    wired: bool = True,
) -> None:
    """An own ``BookFilter`` leaf walks the declared ``shelf`` hop and decodes in ``ShelfFilter``.

    ``branch_is`` (``shelf__branch``) reaches a ``callable`` ``Branch`` type past an
    unwired ``ShelfFilter``; with ``shelf_id``, ``shelf_is`` (``shelf__id``) reaches the
    shelf's key on the ``callable`` ``Shelf`` type, in a ``ShelfFilter`` that type wires,
    or with ``wired`` false one no type wires, where the leaf names a row of the type
    registered for ``Shelf``. ``flat`` is the walked declaration's.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"code": ["exact"]}

    leaf = (
        {"shelf_is": GlobalIDFilter(field_name="shelf__id")}
        if shelf_id
        else {"branch_is": GlobalIDFilter(field_name="shelf__branch")}
    )
    book_filter = type(
        "BookFilter",
        (FilterSet,),
        {
            "shelf": RelatedFilter(ShelfFilter, field_name="shelf", flat=flat),
            **leaf,
            "Meta": type("Meta", (), {"model": Book, "fields": {"title": ["exact"]}}),
        },
    )
    _relay_type(
        Branch,
        ("id", "name"),
        name="BranchType",
        strategy=None if shelf_id else _encode_by_name,
    )
    _relay_type(
        Shelf,
        ("id", "code", "branch"),
        name="ShelfType",
        filterset_class=ShelfFilter if shelf_id and wired else None,
        strategy=_encode_by_name if shelf_id else None,
    )
    _relay_type(Book, ("id", "title", "shelf"), name="BookType", filterset_class=book_filter)


def _scoped_hop_world() -> None:
    """An own ``BookFilter`` key ``shelf__branch`` walks ``shelf``, an undeclared hop a scoping type reads.

    ``ShelfType``'s ``get_queryset`` makes the request walk the hop, so the key's terminal
    runs bound to the hop's face (``_UndeclaredHopSet``) and decodes against the
    ``callable`` ``Branch`` type it reaches.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"], "shelf__branch": ["exact"]}

    _relay_type(Branch, ("id", "name"), name="BranchType", strategy=_encode_by_name)
    _relay_type(Shelf, ("id", "code"), name="ShelfType", hook=True)
    _relay_type(Book, ("id", "title"), name="BookType", filterset_class=BookFilter)


def _behind_shelf_books_world(
    book_fields: dict[str, list[str]],
    book_set: str,
    *,
    flat: bool,
) -> None:
    """A wired ``ShelfFilter.books`` (``flat``) reaching an unwired book set holding ``book_fields``.

    ``"shelf__branch"`` walks the undeclared ``shelf`` hop a scoping ``ShelfType`` reads
    into a ``callable`` ``Branch``; ``"shelf__books"`` re-enters ``Book`` past it, onto a
    ``callable`` primary.
    """
    book_filter = type(
        book_set,
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": Book, "fields": book_fields})},
    )
    shelf_filter = type(
        "ShelfFilter",
        (FilterSet,),
        {
            "books": RelatedFilter(book_filter, field_name="books", flat=flat),
            "Meta": type("Meta", (), {"model": Shelf, "fields": {"code": ["exact"]}}),
        },
    )
    if "shelf__branch" in book_fields:
        _relay_type(Branch, ("id", "name"), name="BranchType", strategy=_encode_by_name)
        _relay_type(Book, ("id", "title"), name="BookType")
    else:
        _relay_type(
            Book,
            ("id", "title"),
            name="BookPrimary",
            primary=True,
            strategy=_encode_by_name,
        )
    _relay_type(Shelf, ("id", "code"), name="ShelfType", hook=True, filterset_class=shelf_filter)


@pytest.mark.parametrize("flat", [True, False])
@pytest.mark.parametrize(
    ("world", "head", "type_name"),
    [
        pytest.param(
            _unwired_hop_world,
            "filterset _unwired_hop_world.<locals>.BookFilter serves GlobalID filter "
            "'shelf__branch' (ShelfFilter.branch, reached through RelatedFilter "
            "BookFilter.shelf)",
            "BranchType",
            id="declared-hop",
        ),
        pytest.param(
            functools.partial(_unwired_hop_world, init=True),
            "filterset _unwired_hop_world.<locals>.BookFilter serves GlobalID filter "
            "'shelf__branch' (InitShelfFilter.branch, reached through RelatedFilter "
            "BookFilter.shelf)",
            "BranchType",
            id="declared-hop-init-override",
        ),
        pytest.param(
            functools.partial(
                _behind_shelf_books_world,
                {"title": ["exact"], "shelf__branch": ["exact"]},
                "BookFilter",
            ),
            "filterset ShelfFilter serves GlobalID filter 'books__shelf__branch' "
            "(BookFilter.shelf__branch, reached through RelatedFilter ShelfFilter.books)",
            "BranchType",
            id="scoped-undeclared-hop",
        ),
        pytest.param(
            functools.partial(
                _behind_shelf_books_world,
                {"shelf__books": ["exact"]},
                "ReentryBookFilter",
            ),
            "filterset ShelfFilter serves GlobalID filter 'books__shelf__books' "
            "(ReentryBookFilter.shelf__books, reached through RelatedFilter ShelfFilter.books)",
            "BookPrimary",
            id="undeclared-reentry",
        ),
        pytest.param(
            _walked_own_leaf_world,
            "filterset BookFilter declares GlobalID filter 'branch_is'",
            "BranchType",
            id="own-leaf-over-the-declared-hop",
        ),
        pytest.param(
            functools.partial(_walked_own_leaf_world, shelf_id=True, wired=False),
            "filterset BookFilter declares GlobalID filter 'shelf_is'",
            "ShelfType",
            id="own-leaf-over-the-declared-hop-onto-the-unwired-target-key",
        ),
    ],
)
def test_phase_2_5_refuses_a_globalid_leaf_behind_a_flat_false_declaration_alike(
    world: Callable[..., None],
    head: str,
    type_name: str,
    *,
    flat: bool,
) -> None:
    """A ``flat=False`` declaration keeps its target served, so the audit refuses alike.

    The published table keeps the declared head, which the audit's reach follows
    whatever the flag; each leaf is resolved where a request decodes it.
    """
    world(flat=flat)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    assert str(exc_info.value) == _encode_only_refusal(head, type_name)


@pytest.mark.parametrize("flat", [True, False])
def test_phase_2_5_admits_a_method_decoder_behind_either_flat(*, flat: bool) -> None:
    """A ``method=`` GlobalID leaf in the hop's target set builds under both flags."""
    _unwired_hop_world(flat=flat, method=True)

    finalize_django_types()


def _encode_only_refusal(head: str, type_name: str) -> str:
    """The audit's whole message: ``head`` names the leaf, ``type_name`` its ``callable`` target."""
    return (
        f"Cannot finalize Django types: {head} targeting {type_name}, whose globalid "
        "strategy is 'callable'. The 'callable' strategy is encode-only (no decode path "
        "exists), so this filter input could never validly consume the IDs its target "
        f"emits. Remove the filter, read its value in `method=`, or give {type_name} a "
        "decodable globalid strategy (model / type / type+model)."
    )


@pytest.mark.parametrize(
    ("world", "head", "type_name"),
    [
        pytest.param(
            functools.partial(_desk_world, "self_serve"),
            "filterset _desk_world.<locals>.RepairTicketFilter serves GlobalID filter "
            "'venue__faults' (SelfServeDeskFilter.faults, reached through RelatedFilter "
            "RepairTicketFilter.venue)",
            "FaultType",
            id="unwired-set-over-an-mti-descendant",
        ),
        pytest.param(
            functools.partial(_desk_world, "self_serve_init"),
            "filterset _desk_world.<locals>.RepairTicketFilter serves GlobalID filter "
            "'venue__faults' (InitSelfServeDeskFilter.faults, reached through RelatedFilter "
            "RepairTicketFilter.venue)",
            "FaultType",
            id="unwired-set-reached-only-through-its-nested-branch",
        ),
        pytest.param(
            functools.partial(_desk_world, "lending"),
            "filterset _desk_world.<locals>.RepairTicketFilter serves GlobalID filter "
            "'venue__selfservedesk' (LendingDeskFilter.selfservedesk, reached through "
            "RelatedFilter RepairTicketFilter.venue)",
            "SelfServeDeskType",
            id="unwired-set-key-into-an-mti-child",
        ),
        pytest.param(
            functools.partial(_scoped_reentry_world, callable_primary=True),
            "filterset ReentryBookFilter declares GlobalID filter 'shelf__books'",
            "BookPrimary",
            id="undeclared-reentry-declared-predicate-onto-the-primary",
        ),
        pytest.param(
            functools.partial(_scoped_reentry_world, callable_primary=True, key="genres__books"),
            "filterset ReentryBookFilter declares GlobalID filter 'genres__books'",
            "BookPrimary",
            id="many-to-many-reentry-declared-predicate-onto-the-primary",
        ),
        pytest.param(
            _unwired_hop_world,
            "filterset _unwired_hop_world.<locals>.BookFilter serves GlobalID filter "
            "'shelf__branch' (ShelfFilter.branch, reached through RelatedFilter "
            "BookFilter.shelf)",
            "BranchType",
            id="unwired-declared-hop-named-by-its-declaration",
        ),
        pytest.param(
            functools.partial(_unwired_hop_world, init=True),
            "filterset _unwired_hop_world.<locals>.BookFilter serves GlobalID filter "
            "'shelf__branch' (InitShelfFilter.branch, reached through RelatedFilter "
            "BookFilter.shelf)",
            "BranchType",
            id="unwired-declared-hop-reached-only-through-its-nested-branch",
        ),
        pytest.param(
            functools.partial(_desk_world, "self_serve_wired"),
            "filterset _desk_world.<locals>.SelfServeDeskFilter declares GlobalID filter 'faults'",
            "FaultType",
            id="wired-declaring-set-named-ahead-of-a-sibling-flat-copy-over-an-mti-descendant",
        ),
        pytest.param(
            functools.partial(_unwired_hop_world, wired=True),
            "filterset _unwired_hop_world.<locals>.ShelfFilter declares GlobalID filter 'branch'",
            "BranchType",
            id="wired-declaring-set-named-ahead-of-a-sibling-flat-copy",
        ),
        pytest.param(
            _scoped_hop_world,
            "filterset _scoped_hop_world.<locals>.BookFilter declares GlobalID filter "
            "'shelf__branch'",
            "BranchType",
            id="own-key-past-a-scoped-undeclared-hop-decodes-on-its-face",
        ),
        pytest.param(
            _walked_own_leaf_world,
            "filterset BookFilter declares GlobalID filter 'branch_is'",
            "BranchType",
            id="own-leaf-walking-a-declared-hop-decodes-in-the-target-set",
        ),
        pytest.param(
            functools.partial(_walked_own_leaf_world, shelf_id=True),
            "filterset BookFilter declares GlobalID filter 'shelf_is'",
            "ShelfType",
            id="own-leaf-walking-a-declared-hop-onto-the-wired-target-key",
        ),
        pytest.param(
            functools.partial(_walked_own_leaf_world, shelf_id=True, wired=False),
            "filterset BookFilter declares GlobalID filter 'shelf_is'",
            "ShelfType",
            id="own-leaf-walking-a-declared-hop-onto-the-unwired-target-key",
        ),
    ],
)
def test_phase_2_5_refuses_a_globalid_leaf_a_request_decodes_against_an_encode_only_type(
    world: Callable[[], None],
    head: str,
    type_name: str,
) -> None:
    """The audit asks where a request decodes each GlobalID leaf, every reached set included.

    A ``RelatedFilter`` into a set no type wires runs its leaves bound to that set (its
    model's registry primary), an own leaf walking a declared hop decodes in the hop's
    target set (onto the key of a set no type wires: as the type registered for the
    relation's target, as the relation's key does), a to-many key whose undeclared hops
    re-enter the owner's table decodes against the primary its relation reaches, and a leaf
    both a nested branch and a flat copy serve is named by its declaration, as its wired
    declaring set's own ahead of a wired sibling's flat copy. Each would build and answer
    ``GLOBALID_UNVALIDATABLE`` for every nonempty value. The ``null`` and ``[]`` values such
    a leaf answers without decoding go with it: no schema holding the leaf builds, so no
    request reaches either.
    """
    world()

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    assert str(exc_info.value) == _encode_only_refusal(head, type_name)


def _consumer_decoder_world(shape: str) -> None:
    """A GlobalID leaf into a ``callable`` type whose value consumer code reads (``method=`` or override)."""

    class _OverridingGlobalIDFilter(GlobalIDFilter):
        @override
        def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
            return qs

    def decode(
        _fs: FilterSet,
        queryset: QuerySet[Model],
        _name: str,
        _value: object,
    ) -> QuerySet[Model]:
        return queryset

    if shape in {"own-method", "own-override"}:
        own = (
            GlobalIDFilter(field_name="id", method="decode")
            if shape == "own-method"
            else _OverridingGlobalIDFilter(field_name="id")
        )
        genre_filter = type(
            "GenreFilter",
            (FilterSet,),
            {
                "id": own,
                "decode": decode,
                "Meta": type("Meta", (), {"model": Genre, "fields": {"name": ["exact"]}}),
            },
        )
        _relay_type(
            Genre,
            ("id", "name"),
            name="GenreType",
            filterset_class=genre_filter,
            strategy=_encode_by_name,
        )
        return
    book_filter = type(
        "BookFilter",
        (FilterSet,),
        {
            "branch_is": GlobalIDFilter(field_name="shelf__branch", method="decode"),
            "decode": decode,
            "Meta": type("Meta", (), {"model": Book, "fields": {"title": ["exact"]}}),
        },
    )
    _relay_type(Branch, ("id", "name"), name="BranchType", strategy=_encode_by_name)
    _relay_type(Shelf, ("id", "code"), name="ShelfType")
    _relay_type(Book, ("id", "title"), name="BookType", filterset_class=book_filter)


@pytest.mark.parametrize("shape", ["own-method", "own-override", "walked-method"])
def test_phase_2_5_admits_a_globalid_leaf_whose_value_consumer_code_reads(shape: str) -> None:
    """A ``method=`` or a class-level ``filter`` override reads the value undecoded, so it builds.

    ``filters/sets.py::_decodes_before_binding`` is the request's own answer: the
    consumer's code receives the value, whatever type the leaf's path reaches.
    """
    _consumer_decoder_world(shape)

    finalize_django_types()


@pytest.mark.parametrize("key", ["shelf__books", "genres__books"])
def test_phase_2_5_admits_a_reentry_key_decoding_against_the_primary_its_relation_reaches(
    key: str,
) -> None:
    """A scoped to-many re-entry key decodes against its relation's primary, never its set's type.

    ``ReentryBookFilter`` is bound to a ``callable`` ``BookSecondary`` whose
    ``get_queryset`` scopes the walk; the key's declared predicate and its copy over the
    target rows (bound to a face answering for ``BookSecondary``) both validate against
    the ``model`` primary the relation reaches, so no encode-only type is a target.
    """
    _scoped_reentry_world(key=key)

    finalize_django_types()


@pytest.mark.parametrize("key", ["shelf__books", "genres__books"])
def test_phase_2_5_admits_a_reentry_isnull_key_decoding_against_the_primary_its_relation_reaches(
    key: str,
) -> None:
    """A scoped re-entry key's ``isnull`` leaf names its relation's primary, never its set's type.

    Its terminal runs over the target rows' key on a face answering for the ``callable``
    ``BookSecondary``; the id it validates is the one the type registered for ``Book``
    mints, as its unscoped twin's is, so no encode-only type is a target.
    """
    _scoped_reentry_world(key=key, isnull=True)

    finalize_django_types()


@pytest.mark.parametrize("init", [False, True], ids=["plain-shelf-set", "init-override-shelf-set"])
def test_phase_2_5_admits_a_declared_reentry_decoding_against_the_bound_secondary(
    *,
    init: bool,
) -> None:
    """A declared re-entry decodes against the secondary its set is bound to, never the primary.

    ``BookFilter.shelf`` -> ``ShelfFilter.books`` -> ``BookFilter``: the ``id`` the
    request reaches runs in a ``BookFilter`` bound to ``BookSecondary`` (``type``), so a
    ``callable`` primary is no target of it. With ``init`` the shelf set overrides
    ``__init__``, so ``BookFilter`` holds the re-entry only as a projected copy, which the
    audit asks in the child set that runs it, never on the copy itself.
    """

    def __init__(  # noqa: N807 - the consumer's own __init__ override
        self: FilterSet,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        FilterSet.__init__(self, data, queryset, request=request, prefix=prefix)

    shelf_filter = type(
        "ShelfFilter",
        (FilterSet,),
        {
            "books": RelatedFilter(lambda: book_filter, field_name="books"),
            **({"__init__": __init__} if init else {}),
            "Meta": type("Meta", (), {"model": Shelf, "fields": {"code": ["exact"]}}),
        },
    )
    book_filter = type(
        "BookFilter",
        (FilterSet,),
        {
            "shelf": RelatedFilter(shelf_filter, field_name="shelf"),
            "Meta": type(
                "Meta",
                (),
                {"model": Book, "fields": {"title": ["exact"], "id": ["exact"]}},
            ),
        },
    )
    _relay_type(
        Book,
        ("id", "title", "shelf"),
        name="BookPrimary",
        primary=True,
        strategy=_encode_by_name,
    )
    _relay_type(
        Book,
        ("id", "title", "shelf"),
        name="BookSecondary",
        filterset_class=book_filter,
        strategy="type",
    )
    _relay_type(Shelf, ("id", "code"), name="ShelfType")

    finalize_django_types()


@pytest.mark.parametrize("shape", ["unwired-own-key", "secondary-wired-key"])
def test_phase_2_5_admits_a_key_of_the_hop_target_set_decoding_against_that_set(
    shape: str,
) -> None:
    """A key the hop's target set reads as its own builds behind a ``callable`` primary.

    ``unwired-own-key``: a ``gid`` (``id``) the unwired ``ShelfFilter`` declares is its own
    key, nested and as the flat copy ``shelf_gid`` alike: it keeps the upstream scalar
    reading (node id only), so the ``callable`` ``ShelfType`` is no target of it.
    ``secondary-wired-key``: ``shelf_is`` (``shelf__id``) past the declared ``shelf`` hop
    into a ``ShelfFilter`` the ``type`` secondary ``ShelfSecondary`` wires decodes against
    that secondary, never the ``callable`` primary.
    """
    unwired = shape == "unwired-own-key"
    shelf_filter = type(
        "ShelfFilter",
        (FilterSet,),
        {
            **({"gid": GlobalIDFilter(field_name="id")} if unwired else {}),
            "Meta": type("Meta", (), {"model": Shelf, "fields": {"code": ["exact"]}}),
        },
    )
    book_filter = type(
        "BookFilter",
        (FilterSet,),
        {
            "shelf": RelatedFilter(shelf_filter, field_name="shelf"),
            **({} if unwired else {"shelf_is": GlobalIDFilter(field_name="shelf__id")}),
            "Meta": type("Meta", (), {"model": Book, "fields": {"title": ["exact"]}}),
        },
    )
    _relay_type(Shelf, ("id", "code"), name="ShelfType", primary=True, strategy=_encode_by_name)
    if not unwired:
        _relay_type(
            Shelf,
            ("id", "code"),
            name="ShelfSecondary",
            filterset_class=shelf_filter,
            strategy="type",
        )
    _relay_type(Book, ("id", "title", "shelf"), name="BookType", filterset_class=book_filter)

    finalize_django_types()


def test_phase_2_5_asks_a_projected_copy_in_the_child_set_that_runs_it() -> None:
    """A projected copy of a reached set's leaf is asked in that set, never on the copy.

    ``ShelfFilter`` overrides ``__init__``, so ``BookFilter`` holds its ``branch`` key only
    as a projected copy, a filter no set binds; the audit asks ``ShelfFilter.branch``
    where it is declared and the schema builds (``Branch`` keeps the default strategy).
    """
    _unwired_hop_world(init=True, callable_branch=False)

    finalize_django_types()


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

    def shelves(self, request: object) -> QuerySet[Shelf]:
        """A request-aware ``queryset=`` callable bound to the instance."""
        del request
        return Shelf.objects.all()


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
    Subpass 2.5 copies each filter of the published table once and refuses the
    first, naming the set, the attribute and the filter's class, the copy's error
    kept as ``__cause__``.
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


@pytest.mark.parametrize("flat", [True, False])
def test_finalize_refuses_a_related_child_filter_a_deep_copy_refuses(*, flat: bool) -> None:
    """A ``RelatedFilter`` child set no type serves is refused, its declaration flat or not.

    The child set is reached only through the served set's ``RelatedFilter``. An
    enabled declaration's expansion copies its filters during subpass 2, before the
    subpass-2.5 audit asks the child's own table: the expansion copy refuses the
    filter naming the child set, its attribute and the ``RelatedFilter`` it was
    reached through (by qualified name). A ``flat=False`` declaration copies
    nothing, and the audit, following the published head, refuses the same filter
    naming the path by set name.
    """
    shelf_filter = _shelf_filter(
        CharFilter(field_name="code", method=_InstanceLockHolder().code_is),
    )

    class BookFilter(FilterSet):
        shelf = RelatedFilter(shelf_filter, field_name="shelf", flat=flat)

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
    via = f"{BookFilter.__qualname__}.shelf" if flat else "BookFilter.shelf"
    where = f"ShelfFilter.code_is (reached through RelatedFilter {via})"
    assert str(exc_info.value) == _copy_refusal(where, "CharFilter", cause, has_method=True)


def _locked_set(
    name: str,
    model: type[Model],
    fields: dict[str, list[str]],
    namespace: dict[str, object],
    *,
    lock: str | None = None,
    lock_field: str = "code",
) -> type[FilterSet]:
    """A filter set ``name``; ``lock`` adds a lock-holding ``locked`` filter as its own or by override."""
    body = dict(namespace)
    body["Meta"] = type("Meta", (), {"model": model, "fields": fields})
    if lock == "own":
        body["locked"] = CharFilter(field_name=lock_field, method=_InstanceLockHolder().code_is)
    built: list[type[FilterSet]] = []
    if lock == "override":

        def get_filters(cls: type[FilterSet]) -> OrderedDict[str, Filter]:
            # The metaclass reads the table while the class is being built.
            filters = super(built[0] if built else cls, cls).get_filters()
            filters["locked"] = CharFilter(
                field_name=lock_field,
                method=_InstanceLockHolder().code_is,
            )
            return filters

        body["get_filters"] = classmethod(get_filters)
    built.append(require(type(name, (FilterSet,), body), _is_filterset_class))
    return built[0]


def _plain_relay_free_type(
    model: type[Model],
    fields: tuple[str, ...],
    name: str,
    fs: object = None,
) -> None:
    meta: dict[str, object] = {"model": model, "fields": fields}
    if fs is not None:
        meta["filterset_class"] = fs
    type(name, (DjangoType,), {"Meta": type("Meta", (), meta)})


def _lock_refusal(where: str, cause: BaseException | None) -> str:
    return _copy_refusal(where, "CharFilter", cause, has_method=True)


@pytest.mark.parametrize("lock", ["own", "override"])
@pytest.mark.parametrize(
    "disabled",
    [
        "none",
        "book.shelf",
        "shelf.books",
        "both",
    ],
)
def test_finalize_refuses_a_lock_on_the_unwired_side_of_a_cycle_whichever_edge_is_flat_false(
    disabled: str,
    lock: str,
) -> None:
    """A wired book set and an unwired shelf set in one cycle: the shelf's lock is refused.

    Its own entry or one its ``get_filters()`` override adds: the expansion copy or
    the audit refuses it, naming the declaration it is reached through, under every
    choice of disabled edge.
    """
    holder: dict[str, type[FilterSet]] = {}
    shelf = _locked_set(
        "ShelfFilter",
        Shelf,
        {"topic": ["exact"]},
        {
            "books": RelatedFilter(
                lambda: holder["book"],
                field_name="books",
                flat=disabled not in {"shelf.books", "both"},
            ),
        },
        lock=lock,
    )
    holder["book"] = _locked_set(
        "BookFilter",
        Book,
        {"title": ["exact"]},
        {
            "shelf": RelatedFilter(
                shelf,
                field_name="shelf",
                flat=disabled not in {"book.shelf", "both"},
            ),
        },
    )
    _plain_relay_free_type(Shelf, ("id", "code"), "ShelfType")
    _plain_relay_free_type(Book, ("id", "title"), "BookType", holder["book"])

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    where = "ShelfFilter.locked (reached through RelatedFilter BookFilter.shelf)"
    assert str(exc_info.value) == _lock_refusal(where, exc_info.value.__cause__)


@pytest.mark.parametrize("lock", ["own", "override"])
@pytest.mark.parametrize("flat", [True, False])
def test_finalize_refuses_a_lock_two_declarations_deep_naming_the_path(
    lock: str,
    *,
    flat: bool,
) -> None:
    """Wired branch set, enabled into shelf, shelf into a locked book set: refused naming its path.

    An enabled inner declaration's expansion copy names that one declaration; behind
    ``flat=False`` the audit names the whole path from the served set.
    """
    book = _locked_set("BookFilter", Book, {"title": ["exact"]}, {}, lock=lock, lock_field="title")
    shelf = _locked_set(
        "ShelfFilter",
        Shelf,
        {"code": ["exact"]},
        {"books": RelatedFilter(book, field_name="books", flat=flat)},
    )
    branch = _locked_set(
        "BranchFilter",
        Branch,
        {"name": ["exact"]},
        {"shelves": RelatedFilter(shelf, field_name="shelves")},
    )
    _plain_relay_free_type(Book, ("id", "title"), "BookType")
    _plain_relay_free_type(Shelf, ("id", "code"), "ShelfType")
    _plain_relay_free_type(Branch, ("id", "name"), "BranchType", branch)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    via = "ShelfFilter.books" if flat else "BranchFilter.shelves, then ShelfFilter.books"
    where = f"BookFilter.locked (reached through RelatedFilter {via})"
    assert str(exc_info.value) == _lock_refusal(where, exc_info.value.__cause__)


@pytest.mark.parametrize("flat", [True, False])
def test_a_flat_false_declaration_with_an_uncorrelated_target_still_fails_its_build(
    *,
    flat: bool,
) -> None:
    """A disabled declaration is still validated: a target keyed on another model is refused."""
    wrong = _locked_set("BranchFilterAsShelf", Branch, {"name": ["exact"]}, {})
    book = _locked_set(
        "BookFilter",
        Book,
        {"title": ["exact"]},
        {"shelf": RelatedFilter(wrong, field_name="shelf", flat=flat)},
    )
    _plain_relay_free_type(Branch, ("id", "name"), "BranchType")
    _plain_relay_free_type(Shelf, ("id", "code"), "ShelfType")
    _plain_relay_free_type(Book, ("id", "title"), "BookType", book)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    assert str(exc_info.value).startswith(
        "FilterSet BookFilter: RelatedFilter 'shelf' has field_name 'shelf', which reaches "
        "Shelf, but its target FilterSet BranchFilterAsShelf is keyed on Branch.",
    )


@pytest.mark.parametrize("flat", [True, False])
def test_a_flat_false_declaration_over_no_relation_still_fails_its_build(*, flat: bool) -> None:
    """A disabled declaration whose ``field_name`` names a column, not a relation, is refused."""
    shelf = _locked_set("ShelfFilter", Shelf, {"code": ["exact"]}, {})
    book = _locked_set(
        "BookFilter",
        Book,
        {"title": ["exact"]},
        {"shelf": RelatedFilter(shelf, field_name="title", flat=flat)},
    )
    _plain_relay_free_type(Shelf, ("id", "code"), "ShelfType")
    _plain_relay_free_type(Book, ("id", "title"), "BookType", book)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    assert str(exc_info.value) == (
        "FilterSet BookFilter: RelatedFilter 'shelf' has field_name 'title', but 'title' is not "
        "a relation of the model the path has reached from Book. A RelatedFilter's field_name "
        "must name a path of relations."
    )


@pytest.mark.django_db
@pytest.mark.parametrize("typed", [False, True], ids=["no-types", "types"])
@pytest.mark.parametrize("flat", [True, False])
def test_an_unserved_set_into_a_locked_target_by_flat(*, flat: bool, typed: bool) -> None:
    """An unwired book set whose ``shelf`` targets a lock-holding shelf set, constructed directly.

    Enabled, the expansion copy refuses the lock at the parent's first construction
    and at every later one. Disabled, the parent constructs and filters, and the
    target raises django-filter's own ``TypeError`` at its own construction, as any
    set the schema does not serve does.
    """
    if typed:
        _plain_relay_free_type(Shelf, ("id", "code"), "ShelfType")
        _plain_relay_free_type(Book, ("id", "title"), "BookType")
    branch_row = Branch.objects.create(name="Unserved")
    shelf_row = Shelf.objects.create(code="U-1", branch=branch_row)
    book_row = Book.objects.create(title="Kept", shelf=shelf_row)
    shelf = _locked_set("ShelfFilter", Shelf, {"topic": ["exact"]}, {}, lock="own")
    book = _locked_set(
        "BookFilter",
        Book,
        {"title": ["exact"]},
        {"shelf": RelatedFilter(shelf, field_name="shelf", flat=flat)},
    )
    for data in ({"title": "Kept"}, {"shelf": str(shelf_row.pk)}, {"title": "Kept"}):
        if flat:
            with pytest.raises(ConfigurationError) as exc_info:
                _ = book(data=data, queryset=Book.objects.all())
            where = "ShelfFilter.locked (reached through RelatedFilter BookFilter.shelf)"
            assert str(exc_info.value) == _lock_refusal(where, exc_info.value.__cause__)
        else:
            instance = book(data=data, queryset=Book.objects.all())
            assert sorted(instance.filters) == ["shelf", "title"]
            assert list(instance.qs) == [book_row]
    with pytest.raises(TypeError, match=r"cannot pickle '_thread\.lock' object"):
        _ = shelf(data={"topic": "x"}, queryset=Shelf.objects.all())


_Reshape = Callable[[OrderedDict[str, Filter]], None]


class _LockedShelfChoice(ModelChoiceFilter):
    """A ``ModelChoiceFilter`` whose rows come from ``get_queryset``, read through a lock holder.

    No ``queryset=`` is passed, so no form field is built for it at schema build.
    """

    def __init__(self, *, field_name: str) -> None:
        super().__init__(field_name=field_name)
        self.holder: _InstanceLockHolder = _InstanceLockHolder()

    @override
    def get_queryset(self, request: HttpRequest | None) -> QuerySet[Shelf]:
        return self.holder.shelves(request)


def _add_a_locked_filter(filters: OrderedDict[str, Filter]) -> None:
    filters["topic_is"] = CharFilter(
        field_name="shelf__topic",
        method=_InstanceLockHolder().code_is,
    )


def _add_a_locked_choice(filters: OrderedDict[str, Filter]) -> None:
    filters["shelf_is"] = _LockedShelfChoice(field_name="shelf")


def _borrow_a_locked_head(filters: OrderedDict[str, Filter]) -> None:
    """Publish a donor set's ``RelatedFilter`` head, its ``method=`` over a lock, under a flat copy's key."""

    class DonorFilter(FilterSet):
        shelf = RelatedFilter(
            _shelf_filter(CharFilter(field_name="code")),
            field_name="shelf",
            method=_InstanceLockHolder().code_is,
        )

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    filters["shelf__code_is"] = DonorFilter.base_filters["shelf"]


def _lock_a_declared_filter(filters: OrderedDict[str, Filter]) -> None:
    filters["title_is"].method = _InstanceLockHolder().code_is


def _lock_a_flat_copy(filters: OrderedDict[str, Filter]) -> None:
    filters["shelf__code_is"].extra["help_text"] = threading.Lock()


_PUBLISHED_ONLY = [
    pytest.param(_add_a_locked_filter, "topic_is", "CharFilter", True, id="added"),
    pytest.param(
        _add_a_locked_choice,
        "shelf_is",
        "_LockedShelfChoice",
        False,
        id="added-choice-no-form-field-copies",
    ),
    pytest.param(
        _borrow_a_locked_head,
        "shelf__code_is",
        "RelatedFilter",
        True,
        id="borrowed-head-under-a-flat-copy-key",
    ),
    pytest.param(_lock_a_declared_filter, "title_is", "CharFilter", True, id="declared-edited"),
    pytest.param(_lock_a_flat_copy, "shelf__code_is", "CharFilter", False, id="flat-copy-edited"),
]


@pytest.mark.parametrize(
    (
        "reshape",
        "key",
        "kind",
        "has_method",
    ),
    _PUBLISHED_ONLY,
)
def test_finalize_refuses_a_published_filter_a_deep_copy_refuses(
    reshape: _Reshape,
    key: str,
    kind: str,
    *,
    has_method: bool,
) -> None:
    """A filter a ``get_filters()`` override publishes over the expanded surface is probed.

    The class-creation ``base_filters`` never holds it: the override adds, borrows or
    edits it only once ``super().get_filters()`` returns the expanded surface, which
    is the table every request copies. The build copies that published table and
    refuses the filter by the key it is published under, before the input build
    copies any form field (a ``get_queryset`` choice builds none) and before a request.
    """
    shelf_filter = _shelf_filter(CharFilter(field_name="code"))

    class BookFilter(FilterSet):
        shelf = RelatedFilter(shelf_filter, field_name="shelf")
        title_is = CharFilter(field_name="title", method=_code_is)

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            filters = super().get_filters()
            if "shelf__topic" in filters:
                reshape(filters)
            return filters

    assert "shelf__topic" not in BookFilter.base_filters
    _ = _relay_node(Shelf, ("id", "code"), None)
    _ = _relay_node(Book, ("id", "title"), BookFilter)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    cause = exc_info.value.__cause__
    where = f"{BookFilter.__qualname__}.{key}"
    assert str(exc_info.value) == _copy_refusal(where, kind, cause, has_method=has_method)


def _lock_a_copied_head(filters: OrderedDict[str, Filter]) -> None:
    filters["shelf__branch"].extra["help_text"] = threading.Lock()


def _lock_a_hidden_flat_copy(filters: OrderedDict[str, Filter]) -> None:
    filters["shelf__code_is"].method = _InstanceLockHolder().code_is


def _lock_a_hidden_flat_copy_extra(filters: OrderedDict[str, Filter]) -> None:
    filters["shelf__code_is"].extra["help_text"] = threading.Lock()


_UNNAMED_COPIES = [
    pytest.param(
        _lock_a_copied_head,
        "shelf__branch",
        "RelatedFilter",
        False,
        False,
        id="copied-head-edited",
    ),
    pytest.param(
        _lock_a_hidden_flat_copy,
        "shelf__code_is",
        "CharFilter",
        True,
        True,
        id="hidden-flat-copy-edited",
    ),
    pytest.param(
        _lock_a_hidden_flat_copy_extra,
        "shelf__code_is",
        "CharFilter",
        False,
        True,
        id="hidden-flat-copy-extra-edited",
    ),
]


@pytest.mark.parametrize(
    (
        "reshape",
        "key",
        "kind",
        "has_method",
        "hide",
    ),
    _UNNAMED_COPIES,
)
def test_finalize_refuses_an_edited_copy_no_graphql_key_names(
    reshape: _Reshape,
    key: str,
    kind: str,
    *,
    has_method: bool,
    hide: bool,
) -> None:
    """A copy the schema publishes under no GraphQL key, edited in place, is refused too.

    A copied ``RelatedFilter`` head and a flat copy ``HIDE_FLAT_FILTERS`` hides are
    deferred on a pipeline-built instance, but django-filter's own constructor copies
    the published table whole on every other construction (a raw ``FilterSet(data)``,
    ``DjangoFilterBackend``), so a table holding one a deep copy refuses is refused by
    the key it is published under.
    """

    class BranchFilter(FilterSet):
        class Meta:
            model = Branch
            fields = {"id": ["exact"]}

    class ShelfFilter(FilterSet):
        code_is = CharFilter(field_name="code")
        branch = RelatedFilter(BranchFilter, field_name="branch")

        class Meta:
            model = Shelf
            fields = {"topic": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"title": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            filters = super().get_filters()
            if key in filters:
                reshape(filters)
            return filters

    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"HIDE_FLAT_FILTERS": hide}):
        _ = _relay_node(Branch, ("id", "name"), None)
        _ = _relay_node(Shelf, ("id", "code"), None)
        _ = _relay_node(Book, ("id", "title"), BookFilter)
        with pytest.raises(ConfigurationError) as exc_info:
            finalize_django_types()
    cause = exc_info.value.__cause__
    where = f"{BookFilter.__qualname__}.{key}"
    assert str(exc_info.value) == _copy_refusal(where, kind, cause, has_method=has_method)


def _locked(filters: OrderedDict[str, Filter], *, lap: str) -> OrderedDict[str, Filter]:
    """``filters`` with a locked ``locked`` filter added when they hold ``lap``."""
    if lap in filters:
        filters["locked"] = CharFilter(field_name="pk", method=_InstanceLockHolder().code_is)
    return filters


def test_finalize_refuses_a_reached_filter_only_its_own_table_holds_naming_its_path() -> None:
    """A set reached around a cycle is probed on its own published table.

    ``ShelfFilter`` reaches back to ``BookFilter``, so ``BookFilter``'s expansion copies
    the surface ``ShelfFilter`` contributes along that path, which ends at the lap and
    lacks the key the override waits for; only ``ShelfFilter``'s own table, which every
    request through the nested ``shelf`` branch copies, holds the locked filter. The
    refusal names the set, the key and the ``RelatedFilter`` it was reached through.
    """
    later: dict[str, type[FilterSet]] = {}

    class ShelfFilter(FilterSet):
        books = RelatedFilter(lambda: later["book"], field_name="books")

        class Meta:
            model = Shelf
            fields = {"id": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            return _locked(super().get_filters(), lap="books__shelf__id")

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"id": ["exact"]}

    later["book"] = BookFilter
    _ = _relay_node(Shelf, ("id", "code"), None)
    _ = _relay_node(Book, ("id", "title"), BookFilter)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    assert "shelf__locked" not in BookFilter._filter_table()
    cause = exc_info.value.__cause__
    where = f"{ShelfFilter.__qualname__}.locked (reached through RelatedFilter BookFilter.shelf)"
    assert str(exc_info.value) == _copy_refusal(where, "CharFilter", cause, has_method=True)


def test_finalize_refuses_a_filter_two_branches_down_naming_both() -> None:
    """A set reached across two ``RelatedFilter`` branches is named with both, outermost first."""
    later: dict[str, type[FilterSet]] = {}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(lambda: later["shelf"], field_name="shelves")

        class Meta:
            model = Branch
            fields = {"id": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            return _locked(super().get_filters(), lap="shelves__branch__id")

    class ShelfFilter(FilterSet):
        branch = RelatedFilter(BranchFilter, field_name="branch")

        class Meta:
            model = Shelf
            fields = {"id": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"id": ["exact"]}

    later["shelf"] = ShelfFilter
    _ = _relay_node(Branch, ("id", "name"), None)
    _ = _relay_node(Shelf, ("id", "code"), None)
    _ = _relay_node(Book, ("id", "title"), BookFilter)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    cause = exc_info.value.__cause__
    where = (
        f"{BranchFilter.__qualname__}.locked (reached through RelatedFilter BookFilter.shelf, "
        "then ShelfFilter.branch)"
    )
    assert str(exc_info.value) == _copy_refusal(where, "CharFilter", cause, has_method=True)


def test_finalize_refuses_a_filter_three_branches_down_naming_each() -> None:
    """A set reached across three ``RelatedFilter`` branches is named with each, outermost first."""
    later: dict[str, type[FilterSet]] = {}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(lambda: later["shelf"], field_name="shelves")

        class Meta:
            model = Branch
            fields = {"id": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            return _locked(super().get_filters(), lap="shelves__branch__id")

    class ShelfFilter(FilterSet):
        branch = RelatedFilter(BranchFilter, field_name="branch")

        class Meta:
            model = Shelf
            fields = {"id": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = Book
            fields = {"id": ["exact"]}

    class LoanFilter(FilterSet):
        book = RelatedFilter(BookFilter, field_name="book")

        class Meta:
            model = Loan
            fields = {"id": ["exact"]}

    later["shelf"] = ShelfFilter
    _ = _relay_node(Branch, ("id", "name"), None)
    _ = _relay_node(Shelf, ("id", "code"), None)
    _ = _relay_node(Book, ("id", "title"), None)
    _ = _relay_node(Loan, ("id",), LoanFilter)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    cause = exc_info.value.__cause__
    where = (
        f"{BranchFilter.__qualname__}.locked (reached through RelatedFilter LoanFilter.book, "
        "then BookFilter.shelf, then ShelfFilter.branch)"
    )
    assert str(exc_info.value) == _copy_refusal(where, "CharFilter", cause, has_method=True)


def test_finalize_builds_a_set_whose_override_drops_a_filter_no_copy_takes() -> None:
    """A filter the override removes from the published table is never copied, so it builds.

    The class-creation ``base_filters`` holds the locked declaration; the table the set
    publishes, which every request copies, does not.
    """

    class BranchFilter(FilterSet):
        class Meta:
            model = Branch
            fields = {"id": ["exact"]}

    class ShelfFilter(FilterSet):
        code_is = CharFilter(field_name="code", method=_InstanceLockHolder().code_is)
        branch = RelatedFilter(BranchFilter, field_name="branch")

        class Meta:
            model = Shelf
            fields = {"id": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            filters = super().get_filters()
            if "branch__id" in filters:
                del filters["code_is"]
            return filters

    assert "code_is" in ShelfFilter.base_filters
    _ = _relay_node(Branch, ("id", "name"), None)
    _ = _relay_node(Shelf, ("id", "code"), ShelfFilter)

    finalize_django_types()

    assert "code_is" not in ShelfFilter._filter_table()


def _locked_method_filter() -> CharFilter:
    return CharFilter(field_name="title", method=_InstanceLockHolder().code_is)


def _locked_extra_filter() -> CharFilter:
    return CharFilter(field_name="title", help_text=threading.Lock())


@pytest.mark.parametrize(
    ("declare", "has_method"),
    [
        pytest.param(_locked_method_filter, True, id="method"),
        pytest.param(_locked_extra_filter, False, id="extra"),
    ],
)
def test_finalize_refuses_an_uncopyable_filter_before_an_unregistered_target(
    declare: Callable[[], CharFilter],
    *,
    has_method: bool,
) -> None:
    """The copy audit runs first among the published-table audits.

    ``BookFilter``'s own filter holds a lock (on its ``method=``, or in its ``extra``) and
    its ``RelatedFilter`` target model has no registered type: the build names the filter
    no request can copy, not the target.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = Shelf
            fields = {"id": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")
        code_is = declare()

        class Meta:
            model = Book
            fields = {"id": ["exact"]}

    _ = _relay_node(Book, ("id", "title"), BookFilter)

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    cause = exc_info.value.__cause__
    where = f"{BookFilter.__qualname__}.code_is"
    assert str(exc_info.value) == _copy_refusal(where, "CharFilter", cause, has_method=has_method)


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

    ``filters/inputs.py`` imports the predicate by name, so the build's own reference is the
    one replaced, beside the defining module's. With the predicate refusing Django's
    ``Abs``, a served leaf through ``Abs`` (registered under another name) is refused
    naming it.
    """
    genuine = querysets_module._type_is_genuinely_django
    assert read_attr(filter_inputs_module, "_type_is_genuinely_django") is genuine

    def genuine_but_abs(node_type: type[object]) -> bool:
        return node_type is not Abs and genuine(node_type)

    monkeypatch.setattr(querysets_module, "_type_is_genuinely_django", genuine_but_abs)
    monkeypatch.setattr(filter_inputs_module, "_type_is_genuinely_django", genuine_but_abs)
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


class _OwnFilterModelMultipleChoiceFilter(ModelMultipleChoiceFilter):
    """A consumer ``ModelMultipleChoiceFilter`` whose own ``filter`` decides what its value means."""

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
        lambda: _OwnFilterModelMultipleChoiceFilter(
            field_name="children",
            lookup_expr="icontains",
            queryset=_scalar_specimens(),
        ),
        id="filter-override-over-a-to-many-key-lookup-the-relation-refuses",
    ),
]


@pytest.mark.parametrize("declare", _UNWALKED_SERVED_LEAVES)
def test_a_served_leaf_the_build_does_not_walk_builds(declare: Callable[[], Filter]) -> None:
    """A served leaf whose query is consumer code, or whose path the model cannot walk, builds.

    A ``method=`` filter and a ``filter`` override build their own query, over a path or a
    relation's lookup Django refuses too, and a queryset annotation has no walk from the
    model: no class reaches the seal from the build's walk, which leaves each to the request.
    A name past a relation the related model lacks is read on the rows a walked hop's type
    shapes, so it is not refused as unresolvable
    (``filters/base.py::refuse_unresolvable_lookup``).
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
            filter: FilterInput[_DoubledSpecimenFilter],  # noqa: A002 - the GraphQL argument name
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
    related: str = ""
    """The relation's related column spelled past it, which the refusal names; ``""`` for none."""


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
        "parent__id",
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
        "parent__id",
    ),
    "forward-key-range-handed-whole": _UnresolvableCase(
        lambda: _NumberRangeFilter(field_name="branch", lookup_expr="range"),
        Shelf,
        "_NumberRangeFilter",
        "branch",
        "range",
        "range",
        "Shelf.branch (ForeignKey)",
        "branch__id",
    ),
    "forward-key-range-its-walk-refuses": _UnresolvableCase(
        lambda: RangeFilter(field_name="branch", lookup_expr="range"),
        Shelf,
        "RangeFilter",
        "branch",
        "range",
        "range",
        "Shelf.branch (ForeignKey)",
        "branch__id",
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
        "children__id",
    ),
    "reverse-key-lookup-its-target-key-resolves": _UnresolvableCase(
        lambda: ModelMultipleChoiceFilter(
            field_name="children",
            lookup_expr="icontains",
            queryset=_scalar_specimens(),
        ),
        ScalarSpecimen,
        "ModelMultipleChoiceFilter",
        "children",
        "icontains",
        "icontains",
        "ScalarSpecimen.children (ManyToOneRel)",
        "children__id",
    ),
    "many-to-many-key-lookup-its-target-key-resolves": _UnresolvableCase(
        lambda: ModelMultipleChoiceFilter(
            field_name="genres",
            lookup_expr="icontains",
            queryset=Genre.objects.all(),
        ),
        Book,
        "ModelMultipleChoiceFilter",
        "genres",
        "icontains",
        "icontains",
        "Book.genres (ManyToManyField)",
        "genres__id",
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
        "genres__id",
    ),
    "reverse-many-to-many-key-lookup": _UnresolvableCase(
        lambda: ModelMultipleChoiceFilter(
            field_name="books",
            lookup_expr="icontains",
            queryset=Book.objects.all(),
        ),
        Genre,
        "ModelMultipleChoiceFilter",
        "books",
        "icontains",
        "icontains",
        "Genre.books (ManyToManyRel)",
        "books__id",
    ),
    "generic-relation-key-lookup": _UnresolvableCase(
        lambda: ModelMultipleChoiceFilter(
            field_name="tags",
            lookup_expr="startswith",
            queryset=TaggedItem.objects.all(),
        ),
        Branch,
        "ModelMultipleChoiceFilter",
        "tags",
        "startswith",
        "startswith",
        "Branch.tags (GenericRelation)",
        "tags__id",
    ),
    "reverse-one-to-one-key-lookup-its-target-key-resolves": _UnresolvableCase(
        lambda: ModelChoiceFilter(
            field_name="card",
            lookup_expr="iexact",
            queryset=MembershipCard.objects.all(),
        ),
        Patron,
        "ModelChoiceFilter",
        "card",
        "iexact",
        "iexact",
        "Patron.card (OneToOneRel)",
        "card__id",
    ),
    "reverse-text-key-lookup-its-target-key-resolves": _UnresolvableCase(
        lambda: ModelMultipleChoiceFilter(
            field_name="editions",
            lookup_expr="contains",
            queryset=Edition.objects.all(),
        ),
        Publisher,
        "ModelMultipleChoiceFilter",
        "editions",
        "contains",
        "contains",
        "Publisher.editions (ManyToOneRel)",
        "editions__isbn_13",
    ),
}


def _unresolvable_refusal(case: _UnresolvableCase) -> str:
    """The refusal of the leaf ``probe`` ``case`` declares on ``SpecimenFilter``."""
    related_key = (
        f" (a relation's related column is named past it: field_name {case.related!r})"
        if case.related
        else ""
    )
    return (
        f"FilterSet SpecimenFilter: {case.kind} 'probe' has field_name {case.field_name!r} and "
        f"lookup_expr {case.lookup_expr!r}, but Django resolves no transform or lookup "
        f"{case.part!r} on {case.field}, so every request naming the filter would be refused. "
        "Spell the transforms and lookup the field registers (a column's lookups belong in "
        f"lookup_expr, not field_name{related_key}), register a project lookup at startup "
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
        filter: object,  # noqa: A002 - the GraphQL argument name
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

    Where the path ends on a column, or on a relation (to-one or to-many: the lookup is asked
    of the relation's last join, which every request applies it through, walked hop or not),
    Django refuses the predicate whatever rows it runs on, so the set refuses the leaf when it
    publishes: a served set when the schema builds, an unbound one at its first use. The
    refusal names the set, the filter class and name, its ``field_name`` and
    ``lookup_expr``, the part Django refuses and the field it is refused on (a relation's,
    with the related column spelled past it), chained from the walk's
    ``LookupValidationError``.
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


@dataclass(frozen=True)
class _ListlessCase:
    """A declared list filter whose Django lookup compares one value, and what its refusal names."""

    declare: Callable[[], Filter]
    kind: str
    field_name: str
    lookup_expr: str
    lookup: str
    lookup_name: str
    related: str = ""
    """The relation's related column spelled past it, which the refusal names; ``""`` for none."""


_LISTLESS_LEAVES: dict[str, _ListlessCase] = {
    "text-default-exact": _ListlessCase(
        lambda: ListFilter(field_name="label"),
        "ListFilter",
        "label",
        "exact",
        "Exact",
        "exact",
    ),
    "integer-gte": _ListlessCase(
        lambda: ListFilter(field_name="signed_big", lookup_expr="gte"),
        "ListFilter",
        "signed_big",
        "gte",
        "IntegerGreaterThanOrEqual",
        "gte",
    ),
    "decimal-icontains": _ListlessCase(
        lambda: ListFilter(field_name="price", lookup_expr="icontains"),
        "ListFilter",
        "price",
        "icontains",
        "IContains",
        "icontains",
    ),
    "date-year-transform": _ListlessCase(
        lambda: ListFilter(field_name="occurred_on", lookup_expr="year"),
        "ListFilter",
        "occurred_on",
        "year",
        "YearExact",
        "exact",
    ),
    "datetime-isnull": _ListlessCase(
        lambda: ListFilter(field_name="occurred_at", lookup_expr="isnull"),
        "ListFilter",
        "occurred_at",
        "isnull",
        "IsNull",
        "isnull",
    ),
    "json-icontains": _ListlessCase(
        lambda: ListFilter(field_name="payload", lookup_expr="icontains"),
        "ListFilter",
        "payload",
        "icontains",
        "JSONIContains",
        "icontains",
    ),
    "relation-default-exact": _ListlessCase(
        lambda: ListFilter(field_name="parent"),
        "ListFilter",
        "parent",
        "exact",
        "RelatedExact",
        "exact",
        "parent__id",
    ),
    "array-filter-text-startswith": _ListlessCase(
        lambda: ArrayFilter(field_name="label", lookup_expr="startswith"),
        "ArrayFilter",
        "label",
        "startswith",
        "StartsWith",
        "startswith",
    ),
    "array-filter-uuid-default-exact": _ListlessCase(
        lambda: ArrayFilter(field_name="external_id"),
        "ArrayFilter",
        "external_id",
        "exact",
        "Exact",
        "exact",
    ),
}


def _listless_refusal(case: _ListlessCase, name: str = "SpecimenFilter") -> str:
    """The refusal of the leaf ``probe`` ``case`` declares on the set ``name``."""
    related_key = (
        f" (a relation's related column is named past it: field_name {case.related!r})"
        if case.related
        else ""
    )
    return (
        f"FilterSet {name}: {case.kind} 'probe' has field_name {case.field_name!r} and "
        f"lookup_expr {case.lookup_expr!r}, but the lookup it applies, Django's {case.lookup} "
        f"({case.lookup_name!r}), compares one value, and the filter publishes and applies a "
        "list. Declare lookup_expr 'in' (any member matches) or 'range' (two bounds), or a "
        f"transform ending in either ('year__in'){related_key}; read the list in `method=`; "
        "or, for a Meta.filter_overrides selection, list only those lookups for the column in "
        "Meta.fields."
    )


#: Where a set publishes its leaves: a served set when the schema builds, an unserved one at
#: its first use.
_LISTLESS_SERVINGS: dict[str, Callable[[type[FilterSet]], None]] = {
    "root-connection": _build_at_root,
    "unserved-filter-input": _build_unserved_filter_input,
    "apply-sync-first-use": _apply_unbound,
}


@pytest.mark.parametrize(
    ("case", "serve"),
    [
        pytest.param(
            _LISTLESS_LEAVES[case_id],
            _LISTLESS_SERVINGS[serving],
            id=f"{case_id}-{serving}",
        )
        for case_id in _LISTLESS_LEAVES
        for serving in _LISTLESS_SERVINGS
    ],
)
def test_a_declared_list_filter_whose_lookup_compares_one_value_is_refused(
    case: _ListlessCase,
    serve: Callable[[type[FilterSet]], None],
) -> None:
    """A ``ListFilter`` / ``ArrayFilter`` applies its list through its lookup, which must take one.

    django-filter's default ``exact``, a comparison, a text pattern, ``isnull`` and a
    transform ending in one compare a single value, so the set refuses the leaf when it
    publishes: a served set when the schema builds, an unbound one at its first use. The
    refusal names the set, the filter class and name, its ``field_name`` and ``lookup_expr``,
    and the Django lookup it applies; over a relation it spells the related column past it.
    """
    filterset_cls = _specimen_set([], {"probe": case.declare()})
    with pytest.raises(ConfigurationError) as exc_info:
        serve(filterset_cls)
    assert str(exc_info.value) == _listless_refusal(case)


def test_a_listless_leaf_is_refused_at_every_use_until_fixed() -> None:
    """Nothing is kept: an unserved set refuses the leaf at its first use and again at the next."""
    filterset_cls = _specimen_set([], {"probe": _LISTLESS_LEAVES["text-default-exact"].declare()})
    for _attempt in range(2):
        with pytest.raises(ConfigurationError) as exc_info:
            _ = filterset_cls.get_filters()
        assert str(exc_info.value) == _listless_refusal(_LISTLESS_LEAVES["text-default-exact"])


class _ListTextField(TextField[object, object]):
    """A project column storing a list as comma-joined text in ``get_prep_value``."""

    @override
    def get_prep_value(self, value: object) -> object:
        if is_list_or_tuple(value):
            return ",".join(str(member) for member in value)
        return object_result(super().get_prep_value, value)


class _ListDbTextField(TextField[object, object]):
    """A project column storing a list as comma-joined text in ``get_db_prep_value`` only."""

    @override
    def get_db_prep_value(
        self,
        value: object,
        connection: BaseDatabaseWrapper,
        prepared: bool = False,
    ) -> object:
        if is_list_or_tuple(value):
            return ",".join(str(member) for member in value)
        return object_result(super().get_db_prep_value, value, connection, prepared)


class _ListCharField(CharField[object, object]):
    """A project column reading a list as comma-joined text in ``to_python``.

    Django's ``CharField.get_prep_value`` runs ``to_python``, so an ``exact`` list compares
    the joined text.
    """

    @override
    def to_python(self, value: object) -> object:
        if is_list_or_tuple(value):
            return ",".join(str(member) for member in value)
        return object_result(super().to_python, value)


def _read_filters(filterset_cls: type[FilterSet]) -> None:
    """The package's first read of an unbound set's table."""
    _ = filterset_cls.get_filters()


#: Where a set taking its list publishes: served at the root, or read unbound.
_ADMITTED_SERVINGS: dict[str, Callable[[type[FilterSet]], None]] = {
    "root-connection": _build_at_root,
    "get-filters": _read_filters,
}


@pytest.mark.parametrize("serve", list(_ADMITTED_SERVINGS.values()), ids=list(_ADMITTED_SERVINGS))
@pytest.mark.parametrize(
    "declare",
    [
        pytest.param(lambda: ListFilter(field_name="label", lookup_expr="in"), id="text-in"),
        pytest.param(
            lambda: ListFilter(field_name="signed_big", lookup_expr="range"),
            id="integer-range",
        ),
        pytest.param(
            lambda: ListFilter(field_name="occurred_on", lookup_expr="year__in"),
            id="year-in",
        ),
        pytest.param(
            lambda: ListFilter(field_name="occurred_at", lookup_expr="date__in"),
            id="date-in",
        ),
        pytest.param(
            lambda: ListFilter(field_name="parent__id", lookup_expr="in"),
            id="related-key-in",
        ),
        pytest.param(
            lambda: ArrayFilter(field_name="price", lookup_expr="in"),
            id="array-filter-in",
        ),
        pytest.param(lambda: ListFilter(field_name="payload"), id="json-default-exact"),
        pytest.param(
            lambda: ListFilter(field_name="payload", lookup_expr="contains"),
            id="json-contains",
        ),
        pytest.param(lambda: ListFilter(field_name="payload", lookup_expr="gte"), id="json-gte"),
        pytest.param(
            lambda: ListFilter(field_name="payload", lookup_expr="has_keys"),
            id="json-has-keys",
        ),
        pytest.param(
            lambda: ListFilter(field_name="payload", lookup_expr="has_any_keys"),
            id="json-has-any-keys",
        ),
    ],
)
def test_a_declared_list_filter_whose_lookup_takes_the_list_builds(
    declare: Callable[[], Filter],
    serve: Callable[[type[FilterSet]], None],
) -> None:
    """A lookup taking the list builds, served at the root or read unbound.

    ``in``, ``range``, a transform ending in either, a related key's ``in``, a ``JSONField``'s
    own comparisons (the list is one JSON array) and ``has_keys`` / ``has_any_keys`` (each
    member a key) take it.
    """
    filterset_cls = _specimen_set([], {"probe": declare()})
    serve(filterset_cls)
    assert "probe" in filterset_cls.get_filters()


def test_a_relations_own_in_builds_on_an_unserved_set() -> None:
    """A relation's ``in`` (``RelatedIn``) takes the list; only GraphQL cannot type its keys."""
    filterset_cls = _specimen_set([], {"probe": ListFilter(field_name="parent", lookup_expr="in")})
    assert "probe" in filterset_cls.get_filters()


def test_a_method_list_filter_receives_the_list_whatever_its_lookup() -> None:
    """A ``method=`` filter applies no lookup of its own: its default ``exact`` builds."""

    class MethodSpecimenFilter(FilterSet):
        probe = ListFilter(field_name="label", method="filter_among")

        class Meta:
            model = ScalarSpecimen
            fields = ()

        def filter_among(
            self,
            queryset: QuerySet[ScalarSpecimen],
            name: str,
            value: object,
        ) -> QuerySet[ScalarSpecimen]:
            del name
            return queryset.filter(label__in=value)

    _build_at_root(MethodSpecimenFilter)
    assert "probe" in MethodSpecimenFilter.get_filters()


def _specimen_rows() -> QuerySet[ScalarSpecimen]:
    return ScalarSpecimen._default_manager.all()


class _GetQuerysetChoice(ModelChoiceFilter):
    """A ``ModelChoiceFilter`` whose rows ``get_queryset`` answers for each request."""

    @override
    def get_queryset(self, request: object) -> QuerySet[ScalarSpecimen]:
        return _specimen_rows()


class _GetQuerysetMultipleChoice(ModelMultipleChoiceFilter):
    """A ``ModelMultipleChoiceFilter`` whose rows ``get_queryset`` answers for each request."""

    @override
    def get_queryset(self, request: object) -> QuerySet[ScalarSpecimen]:
        return _specimen_rows()


class _FieldChoice(ModelChoiceFilter):
    """A ``ModelChoiceFilter`` setting its queryset when its form field is first built."""

    @property
    @override
    def field(self) -> forms.Field:
        self.queryset = _specimen_rows()
        return super().field


class _FieldMultipleChoice(ModelMultipleChoiceFilter):
    """A ``ModelMultipleChoiceFilter`` setting its queryset when its form field is first built."""

    @property
    @override
    def field(self) -> forms.Field:
        self.queryset = _specimen_rows()
        return super().field


class _InitQuerysetChoice(ModelChoiceFilter):
    """A ``ModelChoiceFilter`` whose own ``__init__`` assigns its ``queryset`` after django-filter's."""

    def __init__(self, *, field_name: str) -> None:
        super().__init__(field_name=field_name)
        self.queryset = _specimen_rows()


class _InitQuerysetMultipleChoice(ModelMultipleChoiceFilter):
    """A ``ModelMultipleChoiceFilter`` whose own ``__init__`` assigns its ``queryset``."""

    def __init__(self, *, field_name: str) -> None:
        super().__init__(field_name=field_name)
        self.queryset = _specimen_rows()


class _InitExtraChoice(ModelChoiceFilter):
    """A ``ModelChoiceFilter`` whose own ``__init__`` puts a queryset in its ``extra``."""

    def __init__(self, *, field_name: str) -> None:
        super().__init__(field_name=field_name)
        self.extra["queryset"] = _specimen_rows()


class _InitExtraMultipleChoice(ModelMultipleChoiceFilter):
    """A ``ModelMultipleChoiceFilter`` whose own ``__init__`` puts a queryset in its ``extra``."""

    def __init__(self, *, field_name: str) -> None:
        super().__init__(field_name=field_name)
        self.extra["queryset"] = _specimen_rows()


class _OwnFieldChoice(ModelChoiceFilter):
    """A ``ModelChoiceFilter`` whose ``field`` builds its own form field over its rows."""

    @property
    @override
    def field(self) -> forms.Field:
        return forms.ModelChoiceField(queryset=_specimen_rows(), required=False)


class _OwnFieldMultipleChoice(ModelMultipleChoiceFilter):
    """A ``ModelMultipleChoiceFilter`` whose ``field`` builds its own form field over its rows."""

    @property
    @override
    def field(self) -> forms.Field:
        return forms.ModelMultipleChoiceField(queryset=_specimen_rows(), required=False)


class _SpecimenChoiceField(forms.ModelChoiceField[ScalarSpecimen]):
    """A model-choice form field whose own ``__init__`` supplies its queryset."""

    def __init__(
        self,
        *,
        label: str | None,
        empty_label: str,
        required: bool,
    ) -> None:
        super().__init__(
            queryset=_specimen_rows(),
            label=label,
            empty_label=empty_label,
            required=required,
        )


class _SpecimenMultipleChoiceField(forms.ModelMultipleChoiceField[ScalarSpecimen]):
    """A multiple model-choice form field whose own ``__init__`` supplies its queryset."""

    def __init__(self, *, label: str | None, required: bool) -> None:
        super().__init__(queryset=_specimen_rows(), label=label, required=required)


class _InheritedSpecimenChoiceField(_SpecimenChoiceField):
    """A model-choice form field inheriting a project base's queryset-supplying ``__init__``."""


class _InheritedSpecimenMultipleChoiceField(_SpecimenMultipleChoiceField):
    """A multiple model-choice form field inheriting a project base's ``__init__``."""


class _PlainSpecimenChoiceField(forms.ModelChoiceField[ScalarSpecimen]):
    """A model-choice form field of the project's own with no ``__init__``: it takes no rows."""


class _PlainSpecimenMultipleChoiceField(forms.ModelMultipleChoiceField[ScalarSpecimen]):
    """A multiple model-choice form field of the project's own with no ``__init__``."""


def _is_model_choice_filter_class(value: object) -> TypeIs[type[ModelChoiceFilter]]:
    return isinstance(value, type) and issubclass(value, ModelChoiceFilter)


def _is_model_multiple_choice_filter_class(
    value: object,
) -> TypeIs[type[ModelMultipleChoiceFilter]]:
    return isinstance(value, type) and issubclass(value, ModelMultipleChoiceFilter)


def _choice_over(field_class: type[forms.Field]) -> ModelChoiceFilter:
    """A ``ModelChoiceFilter`` on ``parent`` building its form field from ``field_class``."""
    filter_class = type("FieldClassChoice", (ModelChoiceFilter,), {"field_class": field_class})
    return require(filter_class, _is_model_choice_filter_class)(field_name="parent")


def _multiple_choice_over(field_class: type[forms.Field]) -> ModelMultipleChoiceFilter:
    """A ``ModelMultipleChoiceFilter`` on ``children`` building its form field from ``field_class``."""
    filter_class = type(
        "FieldClassMultipleChoice",
        (ModelMultipleChoiceFilter,),
        {"field_class": field_class},
    )
    return require(filter_class, _is_model_multiple_choice_filter_class)(field_name="children")


def _override_rows(_field: object) -> dict[str, object]:
    return {"queryset": _specimen_rows()}


def _override_set(
    filter_class: type[Filter],
    *,
    extra: bool,
    lookup: str = "exact",
) -> type[FilterSet]:
    """A set generating ``parent``'s ``lookup`` through a ``Meta.filter_overrides`` entry."""
    entry: dict[str, object] = {"filter_class": filter_class}
    if extra:
        entry["extra"] = _override_rows
    return _specimen_set({"parent": [lookup]}, meta={"filter_overrides": {ForeignKey: entry}})


def _querysetless_refusal(kind: str, name: str, field_name: str) -> str:
    """The refusal of the model-choice filter ``name`` with no queryset on ``SpecimenFilter``."""
    return (
        f"FilterSet SpecimenFilter: {kind} {name!r} has field_name {field_name!r} and no "
        "queryset, so the model-choice form field it builds has no rows to look a value up "
        "in, and every request building the set's form would fail. Pass queryset= (a model "
        "queryset, or a callable taking the request), override the filter's "
        "get_queryset(request), or give a Meta.filter_overrides entry an `extra` returning "
        '{"queryset": ...}.'
    )


#: (the set, the refused filter's class name, its name and its ``field_name``)
_QUERYSETLESS_CHOICES: dict[str, tuple[Callable[[], type[FilterSet]], str, str, str]] = {
    "forward-key": (
        lambda: _specimen_set([], {"probe": ModelChoiceFilter(field_name="parent")}),
        "ModelChoiceFilter",
        "probe",
        "parent",
    ),
    "reverse-many": (
        lambda: _specimen_set([], {"probe": ModelMultipleChoiceFilter(field_name="children")}),
        "ModelMultipleChoiceFilter",
        "probe",
        "children",
    ),
    "csv-in-wrapper": (
        lambda: _override_set(ModelChoiceFilter, extra=False, lookup="in"),
        "ModelChoiceInFilter",
        "parent__in",
        "parent",
    ),
    "column-path": (
        lambda: _specimen_set([], {"probe": ModelChoiceFilter(field_name="label")}),
        "ModelChoiceFilter",
        "probe",
        "label",
    ),
    "field-class-without-init": (
        lambda: _specimen_set([], {"probe": _choice_over(_PlainSpecimenChoiceField)}),
        "FieldClassChoice",
        "probe",
        "parent",
    ),
    "multiple-field-class-without-init": (
        lambda: _specimen_set(
            [],
            {"probe": _multiple_choice_over(_PlainSpecimenMultipleChoiceField)},
        ),
        "FieldClassMultipleChoice",
        "probe",
        "children",
    ),
    "filter-overrides-without-extra": (
        lambda: _override_set(ModelChoiceFilter, extra=False),
        "ModelChoiceFilter",
        "parent",
        "parent",
    ),
    "multiple-filter-overrides-without-extra": (
        lambda: _override_set(ModelMultipleChoiceFilter, extra=False),
        "ModelMultipleChoiceFilter",
        "parent",
        "parent",
    ),
}


@pytest.mark.parametrize(
    ("case", "serve"),
    [
        pytest.param(
            _QUERYSETLESS_CHOICES[case_id],
            _LISTLESS_SERVINGS[serving],
            id=f"{case_id}-{serving}",
        )
        for case_id in _QUERYSETLESS_CHOICES
        for serving in _LISTLESS_SERVINGS
    ],
)
def test_a_model_choice_filter_with_no_queryset_is_refused_when_its_set_publishes(
    case: tuple[Callable[[], type[FilterSet]], str, str, str],
    serve: Callable[[type[FilterSet]], None],
) -> None:
    """A model-choice filter nothing can give a queryset is refused before any request builds it.

    django-filter's ``QuerySetRequestMixin.field`` builds Django's model-choice form field
    with the queryset ``get_queryset`` answers, and with neither ``queryset=`` passed nor a
    ``queryset`` key in its ``extra`` there is none: the field cannot be built. So the set
    refuses the filter when it publishes, a served set when the schema builds and an unbound
    one at its first use, whatever its path names: a relation, a column, or one a
    ``Meta.filter_overrides`` entry without ``extra`` selects.
    """
    build, kind, name, field_name = case
    with pytest.raises(ConfigurationError) as exc_info:
        serve(build())
    assert str(exc_info.value) == _querysetless_refusal(kind, name, field_name)


@pytest.mark.parametrize(
    "probe",
    [
        pytest.param(lambda: ModelChoiceFilter(field_name="content_object"), id="choice"),
        pytest.param(
            lambda: ModelMultipleChoiceFilter(field_name="content_object"),
            id="multiple-choice",
        ),
    ],
)
def test_a_model_choice_filter_with_no_queryset_on_a_generic_key_takes_the_generic_key_refusal(
    probe: Callable[[], Filter],
) -> None:
    """Both refusals reach it; the ``GenericForeignKey`` one answers, asked first."""
    declared = probe()
    filterset_cls = _specimen_set(["tag"], {"probe": declared}, model=TaggedItem)
    with pytest.raises(ConfigurationError) as exc_info:
        _build_at_root(filterset_cls)
    assert str(exc_info.value) == (
        f"FilterSet SpecimenFilter: {type(declared).__name__} 'probe' has field_name "
        "'content_object', which names TaggedItem.content_object, a GenericForeignKey: Django "
        "filters no queryset through it, so no related row's identity can be compared on it. "
        "Filter through the GenericRelation that reverses it on the related model, or on the "
        "content type and object id columns it reads."
    )


@pytest.mark.parametrize("serve", list(_ADMITTED_SERVINGS.values()), ids=list(_ADMITTED_SERVINGS))
@pytest.mark.parametrize(
    "probe",
    [
        pytest.param(lambda: ModelChoiceFilter(field_name="parent", queryset=None), id="choice"),
        pytest.param(
            lambda: ModelMultipleChoiceFilter(field_name="children", queryset=None),
            id="multiple-choice",
        ),
    ],
)
def test_an_explicit_none_queryset_is_a_passed_value_and_is_not_judged(
    probe: Callable[[], Filter],
    serve: Callable[[type[FilterSet]], None],
) -> None:
    """``queryset=None`` reaches the form field as passed: it builds, so the set publishes it."""
    filterset_cls = _specimen_set([], {"probe": probe()})
    serve(filterset_cls)
    assert "probe" in filterset_cls.get_filters()
    assert "probe" in filterset_cls(data={}, queryset=_specimen_rows()).form.fields


class _InitSuppliedSet(FilterSet):
    """A set whose ``__init__`` gives its ``probe`` filter the rows each request reads."""

    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)
        require_instance(self.filters["probe"], QuerySetRequestMixin).queryset = _specimen_rows()


class _FormClassSuppliedSet(FilterSet):
    """A set whose ``get_form_class`` gives its ``probe`` filter its rows first."""

    @override
    def get_form_class(self) -> type[forms.Form]:
        require_instance(self.filters["probe"], QuerySetRequestMixin).queryset = _specimen_rows()
        return super().get_form_class()


class _FormSuppliedSet(FilterSet):
    """A set whose ``form`` gives its ``probe`` filter its rows first."""

    @property
    @override
    def form(self) -> forms.Form:
        require_instance(self.filters["probe"], QuerySetRequestMixin).queryset = _specimen_rows()
        return super().form


class _ProbeForm(forms.Form):
    """A form of the project's own, holding ``probe``'s rows itself."""

    probe = forms.ModelChoiceField(queryset=ScalarSpecimen._default_manager.all(), required=False)


class _OwnFormClassSet(FilterSet):
    """A set whose ``get_form_class`` answers a form class of its own."""

    @override
    def get_form_class(self) -> type[forms.Form]:
        return _ProbeForm


class _OwnFormSet(FilterSet):
    """A set whose ``form`` builds a form of its own over the set's data."""

    @property
    @override
    def form(self) -> forms.Form:
        return _ProbeForm(self.data)


class _QuerysetAssigningSet(FilterSet):
    """A set whose ``get_filters`` assigns its ``probe`` filter's ``queryset`` after construction."""

    @classmethod
    @override
    def get_filters(cls) -> OrderedDict[str, Filter]:
        filters = super().get_filters()
        if "probe" in filters:
            require_instance(filters["probe"], QuerySetRequestMixin).queryset = _specimen_rows()
        return filters


class _ExtraEditingSet(FilterSet):
    """A set whose ``get_filters`` puts a queryset in its ``probe`` filter's ``extra``."""

    @classmethod
    @override
    def get_filters(cls) -> OrderedDict[str, Filter]:
        filters = super().get_filters()
        if "probe" in filters:
            filters["probe"].extra["queryset"] = _specimen_rows()
        return filters


def _supplied_by_set(base: type[FilterSet]) -> Callable[[Filter], type[FilterSet]]:
    def build(probe: Filter) -> type[FilterSet]:
        meta_class = type("Meta", (), {"model": ScalarSpecimen, "fields": []})
        filterset_cls = type("SpecimenFilter", (base,), {"probe": probe, "Meta": meta_class})
        return require(filterset_cls, _is_filterset_class)

    return build


def _declared_on_specimen(probe: Filter) -> type[FilterSet]:
    return _specimen_set([], {"probe": probe})


#: (the set holding ``probe`` and the two filters it holds: a model choice, a multiple one)
_SUPPLIED_CHOICES: dict[
    str,
    tuple[Callable[[Filter], type[FilterSet]], Callable[[], Filter], Callable[[], Filter]],
] = {
    "queryset-given": (
        _declared_on_specimen,
        lambda: ModelChoiceFilter(field_name="parent", queryset=_specimen_rows()),
        lambda: ModelMultipleChoiceFilter(field_name="children", queryset=_specimen_rows()),
    ),
    "filter-get-queryset": (
        _declared_on_specimen,
        lambda: _GetQuerysetChoice(field_name="parent"),
        lambda: _GetQuerysetMultipleChoice(field_name="children"),
    ),
    "filter-field": (
        _declared_on_specimen,
        lambda: _FieldChoice(field_name="parent"),
        lambda: _FieldMultipleChoice(field_name="children"),
    ),
    "form-field-init": (
        _declared_on_specimen,
        lambda: _choice_over(_SpecimenChoiceField),
        lambda: _multiple_choice_over(_SpecimenMultipleChoiceField),
    ),
    "form-field-not-model-choice": (
        _declared_on_specimen,
        lambda: _choice_over(ChoiceFormField),
        lambda: _multiple_choice_over(forms.MultipleChoiceField),
    ),
    "filter-init-assigns-queryset": (
        _declared_on_specimen,
        lambda: _InitQuerysetChoice(field_name="parent"),
        lambda: _InitQuerysetMultipleChoice(field_name="children"),
    ),
    "filter-init-edits-extra": (
        _declared_on_specimen,
        lambda: _InitExtraChoice(field_name="parent"),
        lambda: _InitExtraMultipleChoice(field_name="children"),
    ),
    "filter-field-builds-its-own": (
        _declared_on_specimen,
        lambda: _OwnFieldChoice(field_name="parent"),
        lambda: _OwnFieldMultipleChoice(field_name="children"),
    ),
    "form-field-inherited-init": (
        _declared_on_specimen,
        lambda: _choice_over(_InheritedSpecimenChoiceField),
        lambda: _multiple_choice_over(_InheritedSpecimenMultipleChoiceField),
    ),
    "set-get-form-class-own-form": (
        _supplied_by_set(_OwnFormClassSet),
        lambda: ModelChoiceFilter(field_name="parent"),
        lambda: ModelMultipleChoiceFilter(field_name="children"),
    ),
    "set-form-own-form": (
        _supplied_by_set(_OwnFormSet),
        lambda: ModelChoiceFilter(field_name="parent"),
        lambda: ModelMultipleChoiceFilter(field_name="children"),
    ),
    "set-init": (
        _supplied_by_set(_InitSuppliedSet),
        lambda: ModelChoiceFilter(field_name="parent"),
        lambda: ModelMultipleChoiceFilter(field_name="children"),
    ),
    "set-get-form-class": (
        _supplied_by_set(_FormClassSuppliedSet),
        lambda: ModelChoiceFilter(field_name="parent"),
        lambda: ModelMultipleChoiceFilter(field_name="children"),
    ),
    "get-filters-assigns-queryset": (
        _supplied_by_set(_QuerysetAssigningSet),
        lambda: ModelChoiceFilter(field_name="parent"),
        lambda: ModelMultipleChoiceFilter(field_name="children"),
    ),
    "get-filters-edits-extra": (
        _supplied_by_set(_ExtraEditingSet),
        lambda: ModelChoiceFilter(field_name="parent"),
        lambda: ModelMultipleChoiceFilter(field_name="children"),
    ),
    "set-form": (
        _supplied_by_set(_FormSuppliedSet),
        lambda: ModelChoiceFilter(field_name="parent"),
        lambda: ModelMultipleChoiceFilter(field_name="children"),
    ),
}


@pytest.mark.parametrize("serve", list(_ADMITTED_SERVINGS.values()), ids=list(_ADMITTED_SERVINGS))
@pytest.mark.parametrize("multiple", [False, True], ids=["choice", "multiple-choice"])
@pytest.mark.parametrize("case_id", list(_SUPPLIED_CHOICES))
def test_a_model_choice_filter_consumer_code_can_give_a_queryset_builds(
    case_id: str,
    serve: Callable[[type[FilterSet]], None],
    *,
    multiple: bool,
) -> None:
    """Consumer code on the form-build path can supply the queryset: the set publishes it.

    A filter overriding ``get_queryset`` or ``field``, a form field class whose own
    ``__init__`` runs before Django's (or that is no model-choice field), and a set
    overriding ``__init__``, ``get_form_class`` or ``form`` are trusted: each builds served
    at the root or read unbound, and an instance's form cleans.
    """
    build, choice, multiple_choice = _SUPPLIED_CHOICES[case_id]
    filterset_cls = build(multiple_choice() if multiple else choice())
    serve(filterset_cls)
    assert "probe" in filterset_cls.get_filters()
    assert filterset_cls(data={}, queryset=_specimen_rows()).is_valid()


@pytest.mark.parametrize("filter_class", [ModelChoiceFilter, ModelMultipleChoiceFilter])
@pytest.mark.parametrize("serve", list(_ADMITTED_SERVINGS.values()), ids=list(_ADMITTED_SERVINGS))
def test_a_filter_overrides_entry_whose_extra_gives_a_queryset_builds(
    filter_class: type[Filter],
    serve: Callable[[type[FilterSet]], None],
) -> None:
    """A ``Meta.filter_overrides`` entry whose ``extra`` returns a queryset builds."""
    filterset_cls = _override_set(filter_class, extra=True)
    serve(filterset_cls)
    assert "parent" in filterset_cls.get_filters()
    assert filterset_cls(data={}, queryset=_specimen_rows()).is_valid()


#: Where an unserved set publishes without a schema serving it through a connection.
_UNSERVED_PUBLISHERS: dict[str, Callable[[type[FilterSet]], None]] = {
    "get-filters": _read_filters,
    "unserved-filter-input": _build_unserved_filter_input,
}


@pytest.mark.parametrize(
    "publish",
    list(_UNSERVED_PUBLISHERS.values()),
    ids=list(_UNSERVED_PUBLISHERS),
)
def test_a_project_lookup_a_list_filter_applies_is_not_judged_on_an_unserved_set(
    publish: Callable[[type[FilterSet]], None],
) -> None:
    """A lookup the project registers owns what its value means: an unserved set builds it."""
    with register_lookup(BigIntegerField, _NotEqual):
        filterset_cls = _specimen_set(
            [],
            {"probe": ListFilter(field_name="signed_big", lookup_expr="ne")},
        )
        publish(filterset_cls)
        assert "probe" in filterset_cls.get_filters()


@isolate_apps("apps.scalars")
@pytest.mark.parametrize(
    "column",
    [
        pytest.param(_ListTextField, id="get-prep-value"),
        pytest.param(_ListDbTextField, id="get-db-prep-value"),
    ],
)
@pytest.mark.parametrize(
    "publish",
    list(_UNSERVED_PUBLISHERS.values()),
    ids=list(_UNSERVED_PUBLISHERS),
)
def test_a_project_field_class_is_not_judged(
    column: Callable[[], ModelFieldClass[object, object]],
    publish: Callable[[type[FilterSet]], None],
) -> None:
    """A column whose field class is project code owns how it prepares a list: it builds."""

    class ListTextSpecimen(Model):
        tags = column()

        class Meta:
            app_label = "scalars"

    filterset_cls = _specimen_set(
        [],
        {"probe": ListFilter(field_name="tags")},
        model=ListTextSpecimen,
    )
    publish(filterset_cls)
    assert "probe" in filterset_cls.get_filters()


@pytest.mark.django_db(transaction=True)
@isolate_apps("apps.scalars")
def test_a_project_field_class_preparing_a_list_in_to_python_answers_over_graphql() -> None:
    """Served at the root, an ``exact`` list over such a column answers the row holding it."""

    class CsvSpecimen(Model):
        label = _ListCharField(max_length=50)

        class Meta:
            app_label = "scalars"

    with connection.schema_editor() as editor:
        editor.create_model(CsvSpecimen)
    try:
        _ = CsvSpecimen.objects.create(label="a,b")
        _ = CsvSpecimen.objects.create(label="c")
        schema = _served_schema(
            _specimen_set([], {"tags": ListFilter(field_name="label")}, model=CsvSpecimen),
            CsvSpecimen,
        )
        data = _post(
            schema,
            '{ rows(filter: {tags: {exact: ["a", "b"]}}) { edges { node { label } } } }',
        )
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(CsvSpecimen)

    assert _labels(data) == ["a,b"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("lookup_expr", "value", "expected"),
    [
        pytest.param("exact", "1,X", [(1, "X")], id="exact"),
        pytest.param("gt", "1,X", [(1, "Y"), (2, "A")], id="gt"),
    ],
)
def test_a_composite_primary_key_takes_the_list_as_one_value(
    lookup_expr: str,
    value: str,
    expected: list[tuple[int, str]],
) -> None:
    """A ``CompositePrimaryKey``'s ``exact`` / ``gt`` compare a list as one value per column."""
    with connection.schema_editor() as editor:
        editor.create_model(RpCompositeParent)
    try:
        for tenant_id, code in ((1, "X"), (1, "Y"), (2, "A")):
            _ = RpCompositeParent.objects.create(tenant_id=tenant_id, code=code, label=code)
        filterset_cls = _specimen_set(
            [],
            {"probe": ListFilter(field_name="pk", lookup_expr=lookup_expr)},
            model=RpCompositeParent,
        )
        filterset = filterset_cls(
            data=QueryDict(f"probe={value}"),
            queryset=RpCompositeParent.objects.all(),
        )
        assert filterset.is_valid(), filterset.errors
        rows = sorted(filterset.qs.values_list("tenant_id", "code"))
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(RpCompositeParent)

    assert rows == expected


def test_a_composite_primary_keys_null_test_is_refused() -> None:
    """``isnull`` takes one flag, never a list, over a ``CompositePrimaryKey`` too."""
    filterset_cls = _specimen_set(
        [],
        {"probe": ListFilter(field_name="pk", lookup_expr="isnull")},
        model=RpCompositeParent,
    )
    case = _ListlessCase(ListFilter, "ListFilter", "pk", "isnull", "TupleIsNull", "isnull")
    with pytest.raises(ConfigurationError) as exc_info:
        _ = filterset_cls.get_filters()
    assert str(exc_info.value) == _listless_refusal(case)


@pytest.mark.pg
@isolate_apps("apps.scalars")
@pytest.mark.parametrize(
    ("field_name", "lookup_expr"),
    [
        pytest.param("attrs", "has_keys", id="hstore-has-keys"),
        pytest.param("attrs", "has_any_keys", id="hstore-has-any-keys"),
        pytest.param("span", "exact", id="range-field-exact"),
    ],
)
def test_a_list_filter_over_a_postgres_column_taking_the_list_builds(
    field_name: str,
    lookup_expr: str,
) -> None:
    """``HStoreField``'s ``has_keys`` reads each member as a key; a ``RangeField`` two bounds.

    The set is unserved (no input types a range column), so it publishes at its first use.
    """
    from django.contrib.postgres.fields import (  # noqa: PLC0415 - needs a PostgreSQL driver
        HStoreField,
        IntegerRangeField,
    )

    class PostgresSpecimen(Model):
        attrs = HStoreField(default=dict)
        span = IntegerRangeField(null=True)

        class Meta:
            app_label = "scalars"

    filterset_cls = _specimen_set(
        [],
        {"probe": ListFilter(field_name=field_name, lookup_expr=lookup_expr)},
        model=PostgresSpecimen,
    )
    assert "probe" in filterset_cls.get_filters()


def test_a_stock_django_filter_parent_is_never_asked() -> None:
    """A stock django-filter ``FilterSet`` publishes through no package table: never refused."""
    meta = type("Meta", (), {"model": ScalarSpecimen, "fields": []})
    stock = type(
        "StockSpecimenFilter",
        (django_filters.FilterSet,),
        {"probe": ListFilter(field_name="label"), "Meta": meta},
    )
    assert "probe" in stock.get_filters()


@pytest.mark.parametrize("serve", list(_LISTLESS_SERVINGS.values()), ids=list(_LISTLESS_SERVINGS))
@pytest.mark.parametrize("lookup_expr", ["exact", "gte"])
def test_a_filter_overrides_list_filter_for_a_listless_lookup_is_refused(
    serve: Callable[[type[FilterSet]], None],
    lookup_expr: str,
) -> None:
    """``Meta.filter_overrides`` building a ``ListFilter`` for ``exact`` / ``gte`` is refused.

    ``in`` and ``range`` route to the generated membership and range filters; the override's
    ``ListFilter`` serves every other lookup ``Meta.fields`` lists for the column.
    """
    filterset_cls = _specimen_set(
        {"signed_big": ["in", lookup_expr]},
        meta={"filter_overrides": {BigIntegerField: {"filter_class": ListFilter}}},
    )
    name = "signed_big" if lookup_expr == "exact" else f"signed_big__{lookup_expr}"
    lookup = "IntegerFieldExact" if lookup_expr == "exact" else "IntegerGreaterThanOrEqual"
    with pytest.raises(ConfigurationError) as exc_info:
        serve(filterset_cls)
    case = _ListlessCase(
        ListFilter,
        "ListFilter",
        "signed_big",
        lookup_expr,
        lookup,
        lookup_expr,
    )
    assert str(exc_info.value) == _listless_refusal(case).replace("'probe'", repr(name))


def _twice(queryset: QuerySet[Model]) -> QuerySet[Model]:
    return queryset.annotate(twice=F("signed_big") * 2)


def _shaping_node(
    model: type[Model],
    shape: Callable[[QuerySet[Model]], QuerySet[Model]],
    filterset_cls: type[FilterSet] | None = None,
    fields: tuple[str, ...] = ("id", "label"),
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
        "fields": fields,
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


@dataclass(frozen=True)
class _ToManyRelation:
    """A to-many relation of ``source``, a row of it reaching one ``target`` row, and its key column."""

    source: Model
    relation: str
    target: Model
    column: str


def _reverse_key() -> _ToManyRelation:
    parent = cleaned_specimen("parent", kept=True)
    child = cleaned_specimen("child", kept=False)
    child.parent = parent
    child.save()
    return _ToManyRelation(parent, "children", child, "id")


def _shelved_book() -> Book:
    shelf = Shelf.objects.create(code="S1", branch=Branch.objects.create(name="east"))
    return Book.objects.create(title="Dune", shelf=shelf)


def _many_to_many_key() -> _ToManyRelation:
    book = _shelved_book()
    genre = Genre.objects.create(name="fiction")
    book.genres.add(genre)
    return _ToManyRelation(book, "genres", genre, "id")


def _reverse_many_to_many_key() -> _ToManyRelation:
    book = _shelved_book()
    genre = Genre.objects.create(name="fiction")
    book.genres.add(genre)
    return _ToManyRelation(genre, "books", book, "id")


def _generic_relation_key() -> _ToManyRelation:
    branch = Branch.objects.create(name="east")
    tag = TaggedItem.objects.create(
        tag="open",
        content_type=ContentType.objects.get_for_model(Branch),
        object_id=branch.pk,
    )
    return _ToManyRelation(branch, "tags", tag, "id")


def _reverse_one_to_one_key() -> _ToManyRelation:
    patron = Patron.objects.create(name="Ada")
    return _ToManyRelation(
        patron,
        "card",
        MembershipCard.objects.create(patron=patron, barcode="C-1"),
        "id",
    )


def _published_edition() -> Edition:
    publisher = Publisher.objects.create(name="House A", house_code="HA")
    return Edition.objects.create(isbn_13="x1", publisher=publisher)


def _reverse_text_key() -> _ToManyRelation:
    edition = _published_edition()
    return _ToManyRelation(edition.publisher, "editions", edition, "isbn_13")


def _many_to_many_text_key() -> _ToManyRelation:
    edition = _published_edition()
    printing = Printing.objects.create(edition=edition)
    printing.bound_with.add(edition)
    return _ToManyRelation(printing, "bound_with", edition, "isbn_13")


_TO_MANY_KEYS = [
    pytest.param(_reverse_key, id="reverse-foreign-key"),
    pytest.param(_many_to_many_key, id="many-to-many"),
    pytest.param(_reverse_many_to_many_key, id="reverse-many-to-many"),
    pytest.param(_generic_relation_key, id="generic-relation"),
    pytest.param(_reverse_one_to_one_key, id="reverse-one-to-one"),
    pytest.param(_reverse_text_key, id="reverse-foreign-text-key"),
]

_TEXT_TO_MANY_KEYS = [
    pytest.param(_reverse_text_key, id="reverse-foreign-text-key"),
    pytest.param(_many_to_many_text_key, id="many-to-many-text-key"),
]

#: How a raw set's to-many key leaf reaches the request: as Django's own predicate, or over a
#: walked hop (the target type's ``get_queryset``, or a ``RelatedFilter`` the set declares on
#: the relation).
_KEY_WALKS = ["unwalked", "target-get-queryset", "related-filter"]


def _raw_key_set(key: _ToManyRelation, walk: str, probe: Filter) -> type[FilterSet]:
    """A set over ``key``'s source model declaring ``probe``, its hop walked as ``walk`` names."""
    target_model = type(key.target)
    fields = (target_model._meta.pk.name,)
    if walk == "target-get-queryset":
        _ = _shaping_node(target_model, lambda queryset: queryset, None, fields=fields)
    elif walk == "related-filter":
        _ = _relay_node(target_model, fields, None)
    finalize_django_types()
    declared: dict[str, Filter] = {"probe": probe}
    if walk == "related-filter":
        declared["hop"] = RelatedFilter(
            _specimen_set([], name="TargetFilter", model=target_model),
            field_name=key.relation,
        )
    filterset_cls = _specimen_set([], declared, model=type(key.source))
    walked = filterset_cls._flat_leaf_walk(filterset_cls.base_filters["probe"]) is not None
    assert walked is (walk != "unwalked")
    return filterset_cls


def _first_use_refusal(filterset_cls: type[FilterSet], data: dict[str, object]) -> str:
    """The refusal ``filterset_cls``'s first construction raises, asserted again at every use.

    A refused set never publishes, so each construction asks again and raises the same
    refusal, and the package's first read (``get_filters()``) raises it too.
    """
    with pytest.raises(ConfigurationError) as first:
        _ = filterset_cls(data=data)
    with pytest.raises(ConfigurationError) as again:
        _ = filterset_cls(data=data)
    with pytest.raises(ConfigurationError) as read:
        _ = filterset_cls.get_filters()
    assert str(again.value) == str(first.value)
    assert str(read.value) == str(first.value)
    assert filterset_cls._expansion_snapshot() is None
    return str(first.value)


@pytest.mark.django_db
@pytest.mark.parametrize("walk", _KEY_WALKS)
@pytest.mark.parametrize("make_key", _TO_MANY_KEYS)
def test_a_raw_to_many_key_lookup_the_relation_refuses_is_refused_at_first_construction(
    make_key: Callable[[], _ToManyRelation],
    walk: str,
) -> None:
    """A raw set's to-many key lookup the relation does not register is refused when built.

    ``icontains`` is no lookup of a to-many relation (Django's query asks it of the relation's
    last join: a reverse relation, a many-to-many's through key onto its target), so Django
    refuses the predicate with ``FieldError``, and a set declaring it is refused at its first
    construction (``FilterSet(data=...)``, its first use) whether or not a hop is walked. The
    related column spelled past the relation (``children__id``) answers Django's rows.
    """
    key = make_key()
    value = str(read_attr(key.target, "pk"))
    model = type(key.source)
    with pytest.raises(FieldError):
        _ = model._default_manager.filter(**{f"{key.relation}__icontains": value})
    probe = ModelMultipleChoiceFilter(
        field_name=key.relation,
        lookup_expr="icontains",
        queryset=type(key.target)._default_manager.all(),
    )
    filterset_cls = _raw_key_set(key, walk, probe)
    refusal = _first_use_refusal(filterset_cls, {"probe": [value]})
    assert refusal.startswith(
        f"FilterSet SpecimenFilter: ModelMultipleChoiceFilter 'probe' has field_name "
        f"{key.relation!r} and lookup_expr 'icontains', but Django resolves no transform or "
        "lookup 'icontains' on ",
    )
    spelled = CharFilter(field_name=f"{key.relation}__{key.column}", lookup_expr="icontains")
    rows = _specimen_set([], {"probe": spelled}, name="SpelledFilter", model=model)
    expected = model._default_manager.filter(**{f"{key.relation}__{key.column}__icontains": value})
    assert list(expected) == [key.source]
    assert list(rows(data={"probe": value}).qs) == [key.source]


@pytest.mark.django_db
@pytest.mark.parametrize("walk", _KEY_WALKS)
@pytest.mark.parametrize(
    ("declare", "lookup_expr"),
    [
        pytest.param(
            lambda: CharFilter(field_name="children", lookup_expr="icontains"),
            "icontains",
            id="char-icontains",
        ),
        pytest.param(
            lambda: NumberFilter(field_name="children", lookup_expr="startswith"),
            "startswith",
            id="number-startswith",
        ),
        pytest.param(
            lambda: ModelChoiceFilter(
                field_name="children",
                lookup_expr="iexact",
                queryset=_scalar_specimens(),
            ),
            "iexact",
            id="model-choice-iexact",
        ),
    ],
)
def test_a_raw_reverse_key_lookup_any_filter_class_applies_is_refused_at_first_construction(
    declare: Callable[[], Filter],
    lookup_expr: str,
    walk: str,
) -> None:
    """Every filter class applying a lookup the reverse relation refuses is refused when built.

    Django refuses the predicate with ``FieldError`` whatever value the class's form cleans to
    (text, a decimal, a model instance), so a raw set declaring it is refused at its first
    construction, naming the class and the lookup, whether or not a hop is walked.
    """
    key = _reverse_key()
    value = str(saved_pk(key.target))
    with pytest.raises(FieldError):
        _ = ScalarSpecimen.objects.filter(**{f"children__{lookup_expr}": value})
    probe = declare()
    filterset_cls = _raw_key_set(key, walk, probe)
    refusal = _first_use_refusal(filterset_cls, {"probe": value})
    assert refusal.startswith(
        f"FilterSet SpecimenFilter: {truth.kind(probe)} 'probe' has field_name 'children' and "
        f"lookup_expr {lookup_expr!r}, but Django resolves no transform or lookup "
        f"{lookup_expr!r} on ",
    )


class _CountingOverride(ModelMultipleChoiceFilter):
    """A consumer class-level ``filter`` override recording each call and running one query."""

    calls: ClassVar[list[object]] = []

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        type(self).calls.append(value)
        _ = ScalarSpecimen.objects.exists()
        return qs


@pytest.mark.django_db
@pytest.mark.parametrize("walk", _KEY_WALKS)
def test_a_class_level_override_on_a_to_many_key_runs_once_per_request(walk: str) -> None:
    """A consumer ``filter`` override on a to-many key is called once, walked or not.

    The walked hop builds the declared predicate first only for shipped ``filter`` code
    (the rule a set publishes by); a consumer override is never run a second time, so the
    request runs the queries the unwalked request runs.
    """
    key = _reverse_key()
    data = {"probe": [str(saved_pk(key.target))]}
    unwalked_set = _raw_key_set(
        key,
        "unwalked",
        _CountingOverride(
            field_name="children",
            lookup_expr="icontains",
            queryset=_scalar_specimens(),
        ),
    )
    with CaptureQueriesContext(connection) as unwalked:
        _ = list(unwalked_set(data=data).qs)
    registry.clear()
    _CountingOverride.calls.clear()
    filterset_cls = _raw_key_set(
        key,
        walk,
        _CountingOverride(
            field_name="children",
            lookup_expr="icontains",
            queryset=_scalar_specimens(),
        ),
    )
    with CaptureQueriesContext(connection) as walked:
        _ = list(filterset_cls(data=data).qs)
    assert len(_CountingOverride.calls) == 1
    assert len(walked.captured_queries) == len(unwalked.captured_queries)


@pytest.mark.django_db
@pytest.mark.parametrize("walk", _KEY_WALKS)
@pytest.mark.parametrize("make_key", _TEXT_TO_MANY_KEYS)
def test_a_raw_text_key_in_handed_one_instance_raises_djangos_error(
    make_key: Callable[[], _ToManyRelation],
    walk: str,
) -> None:
    """A model-choice ``in`` on a to-many text key raises Django's ``TypeError``, walked or not.

    ``ModelMultipleChoiceFilter`` applies its lookup to each chosen row alone, so ``in`` is
    handed one instance, which Django's ``RelatedIn`` refuses to iterate. A walked hop builds
    the declared predicate before comparing the target's key, so the key's text is never
    iterated as a list of its characters.
    """
    key = make_key()
    model = type(key.source)
    with pytest.raises(TypeError) as django_refusal:
        _ = model._default_manager.filter(**{f"{key.relation}__in": key.target})
    probe = ModelMultipleChoiceFilter(
        field_name=key.relation,
        lookup_expr="in",
        queryset=type(key.target)._default_manager.all(),
    )
    filterset_cls = _raw_key_set(key, walk, probe)
    with pytest.raises(TypeError) as raised:
        _ = list(filterset_cls(data={"probe": [str(read_attr(key.target, "pk"))]}).qs)
    assert str(raised.value) == str(django_refusal.value)


@pytest.mark.django_db
@pytest.mark.parametrize("walked", [False, True], ids=["unwalked", "walked"])
def test_a_served_text_key_in_handed_one_instance_answers_walked_as_unwalked(
    *,
    walked: bool,
) -> None:
    """A served model-choice ``in`` on a to-many text key errors alike whether a hop is walked.

    Django refuses ``in`` handed the one row a ``ModelMultipleChoiceFilter`` applies it to
    (``RelatedIn``'s ``TypeError``); the walked hop builds that predicate as declared first,
    so the request answers the unwalked request's error, never the rows the key's characters
    would match.
    """
    edition = _published_edition()
    with pytest.raises(TypeError) as django_refusal:
        _ = Publisher.objects.filter(editions__in=edition)
    if walked:
        _ = _shaping_node(Edition, lambda queryset: queryset, None, fields=("isbn_13",))
    else:
        _ = _relay_node(Edition, ("isbn_13",), None)
    probe = ModelMultipleChoiceFilter(
        field_name="editions",
        lookup_expr="in",
        queryset=Edition.objects.all(),
    )
    node = _relay_node(
        Publisher,
        ("id", "name"),
        _specimen_set([], {"probe": probe}, model=Publisher),
    )
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
    # Unmasked, so the response carries the exception the request raised.
    schema = DjangoSchema(
        query=query,
        config=strawberry_config(),
        error_policy=ErrorPolicy(enabled=False),
    )
    result = schema.execute_sync(
        '{ rows(filter: {probe: {in: ["x1"]}}) { edges { node { name } } } }',
        context_value=HttpRequest(),
    )
    assert result.data is None
    assert [error.message for error in result.errors or []] == [str(django_refusal.value)]


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


def _csv_bounds(pk: int) -> dict[str, object]:
    return {"probe": f"{pk},{pk}"}


def _lone_lower_bound(pk: int) -> dict[str, object]:
    return {"probe_min": str(pk)}


def _both_bounds(pk: int) -> dict[str, object]:
    return {"probe_min": str(pk), "probe_max": str(pk)}


def _gte_and_lte(pk: int) -> dict[str, object]:
    return {"children__gte": pk, "children__lte": pk}


def _gte(pk: int) -> dict[str, object]:
    return {"children__gte": pk}


def _range(pk: int) -> dict[str, object]:
    return {"children__range": (pk, pk)}


def _django_outcome(model: type[Model], predicate: dict[str, object]) -> object:
    """The rows Django's own ``predicate`` on ``model`` answers, or the exception it raises."""
    try:
        return sorted(
            str(read_attr(row, "pk")) for row in model._default_manager.filter(**predicate)
        )
    except (TypeError, FieldError) as exc:
        return (truth.kind(exc), str(exc))


@pytest.mark.django_db
@pytest.mark.parametrize("walk", _KEY_WALKS)
@pytest.mark.parametrize(
    ("declare", "data", "predicate"),
    [
        pytest.param(
            lambda: IntegerRangeFilter(field_name="children", lookup_expr="range"),
            _csv_bounds,
            _gte_and_lte,
            id="integer-range-both-bounds",
        ),
        pytest.param(
            lambda: DjangoFilterRangeFilter(field_name="children", lookup_expr="range"),
            _lone_lower_bound,
            _gte,
            id="django-filter-range-lone-bound",
        ),
        pytest.param(
            lambda: DjangoFilterRangeFilter(field_name="children", lookup_expr="range"),
            _both_bounds,
            _range,
            id="django-filter-range-both-bounds",
        ),
    ],
)
def test_a_range_applied_as_bounds_over_a_to_many_key_publishes_and_answers_as_django(
    declare: Callable[[], Filter],
    data: Callable[[int], dict[str, object]],
    predicate: Callable[[int], dict[str, object]],
    walk: str,
) -> None:
    """A range filter applying a to-many relation's ``gte`` / ``lte`` publishes and answers as Django.

    ``IntegerRangeFilter`` applies both bounds, and django-filter's ``RangeFilter`` a lone one,
    as the relation's ``gte`` / ``lte``, which Django registers on every relation, so the set
    publishes the leaf; django-filter's ``RangeFilter`` hands Django ``range`` for both bounds,
    which no relation registers. Each request answers what Django answers for the predicate
    the filter applies, whether or not a hop is walked.
    """
    key = _reverse_key()
    pk = saved_pk(key.target)
    filterset_cls = _raw_key_set(key, walk, declare())
    assert "probe" in filterset_cls.get_filters()
    expected = _django_outcome(ScalarSpecimen, predicate(pk))
    assert expected != []
    assert _raw_outcome(filterset_cls, data(pk)) == expected


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


@pytest.mark.django_db
def test_a_method_the_set_names_receives_a_lazily_spelled_field_name_as_text() -> None:
    """A ``method=`` naming a method of the set receives the lazy ``field_name`` as its text.

    The published copy's ``FilterMethod`` is bound to that copy, so the method the request
    runs reads the copy's text, never the declaration's lazy object.
    """
    _ = cleaned_specimen("small", kept=True)
    _ = cleaned_specimen("large", kept=False)
    received: list[object] = []

    class MethodSpecimenFilter(FilterSet):
        probe = _respelled(CharFilter(method="by_label"), field_name=gettext_lazy("label"))

        class Meta:
            model = ScalarSpecimen
            fields: ClassVar[list[str]] = []

        def by_label(
            self,
            queryset: QuerySet[ScalarSpecimen],
            name: str,
            value: object,
        ) -> QuerySet[ScalarSpecimen]:
            received.append(name)
            return queryset.filter(**{name: value})

    instance = MethodSpecimenFilter(data={"probe": "large"}, queryset=ScalarSpecimen.objects.all())
    rows = require(instance.qs, is_queryset)
    assert sorted(str(read_attr(row, "label")) for row in rows) == ["large"]
    assert received == ["label"]
    assert type(received[0]) is str


@pytest.mark.django_db
def test_publication_reads_a_lazy_name_as_text_on_a_copy_of_the_shared_declaration() -> None:
    """The published table holds text; the declaration, and a stock set holding it, keep it lazy.

    django-filter hands one declared instance to every set holding it, so the package
    publishes a copy: the class attribute and ``declared_filters`` keep the lazy object, and
    a stock ``django_filters.FilterSet`` sharing the instance answers what django-filter
    answers for it (its multiple-choice predicate keys a ``Q`` by the lazy name).
    """
    _ = cleaned_specimen("small", kept=True)
    field_name = gettext_lazy("label")
    lookup_expr = gettext_lazy("exact")
    declared = _respelled(
        django_filters.MultipleChoiceFilter(choices=[("small", "small")]),
        field_name=field_name,
        lookup_expr=lookup_expr,
    )
    filterset_cls = _specimen_set([], {"probe": declared})
    stock_meta = type("Meta", (), {"model": ScalarSpecimen, "fields": []})
    stock = type(
        "StockSpecimenFilter",
        (django_filters.FilterSet,),
        {"probe": declared, "Meta": stock_meta},
    )

    published = filterset_cls._filter_table()["probe"]
    assert published is not declared
    assert filterset_cls.base_filters["probe"] is published
    assert (published.field_name, published.lookup_expr) == ("label", "exact")
    assert type(published.field_name) is str
    assert type(published.lookup_expr) is str
    assert filterset_cls.declared_filters["probe"] is declared
    assert declared.field_name is field_name
    assert declared.lookup_expr is lookup_expr
    assert stock.base_filters["probe"] is declared
    instance = filterset_cls(data={"probe": ["small"]}, queryset=ScalarSpecimen.objects.all())
    rows = require(instance.qs, is_queryset)
    assert sorted(str(read_attr(row, "label")) for row in rows) == ["small"]
    with pytest.raises(TypeError, match="keywords must be strings"):
        _ = list(stock(data={"probe": ["small"]}, queryset=ScalarSpecimen.objects.all()).qs)


def test_a_set_that_cannot_publish_reads_a_lazy_name_as_text() -> None:
    """A set that cannot publish yet reads, and its instances copy, a lazy name as its text.

    A model-less set whose ``RelatedFilter`` target is still a lazy string answers its
    ``get_filters()`` result on every read; each read holds the filter as the published
    table would, and the declaration keeps its lazy object.
    """
    field_name = gettext_lazy("name")
    declared = _respelled(
        CharFilter(),
        field_name=field_name,
        lookup_expr=gettext_lazy("icontains"),
    )

    class UnpublishableLazyFilter(FilterSet):
        probe = declared
        later = RelatedFilter("NoSuchShelfFilter", field_name="later")

    read = UnpublishableLazyFilter._filter_table()["probe"]
    instance = UnpublishableLazyFilter(data={}, queryset=Branch.objects.all())
    for held in (read, instance.filters["probe"]):
        assert (held.field_name, held.lookup_expr) == ("name", "icontains")
        assert type(held.field_name) is str
        assert type(held.lookup_expr) is str
    assert declared.field_name is field_name
    assert UnpublishableLazyFilter._expansion_snapshot() is None


class _SpecimenColumn(TextChoices):
    """A ``str``-subclass spelling of a column name and a lookup, as a project may declare one."""

    LABEL = "label"
    EXACT = "exact"


@pytest.mark.django_db
@pytest.mark.parametrize("lazy_field_name", [False, True], ids=["member", "lazy-beside-member"])
def test_a_str_subclass_field_name_reaches_a_filter_override_as_declared(
    *,
    lazy_field_name: bool,
) -> None:
    """A name that already is a ``str`` (a choices member) is published as declared.

    It needs no reading as text: alone it leaves the declared instance published, and a
    class-level ``filter`` override dispatching on the member it declared still finds it;
    beside a lazy ``field_name`` the published copy reads only that name as text and
    keeps the member ``lookup_expr``.
    """
    _ = cleaned_specimen("small", kept=True)
    _ = cleaned_specimen("large", kept=False)

    class DispatchingFilter(CharFilter):
        @override
        def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
            if (
                self.field_name is _SpecimenColumn.LABEL
                or self.lookup_expr is _SpecimenColumn.EXACT
            ):
                return qs.filter(label=value)
            return qs.none()

    if lazy_field_name:
        declared = _respelled(
            DispatchingFilter(lookup_expr=_SpecimenColumn.EXACT),
            field_name=gettext_lazy("label"),
        )
    else:
        declared = DispatchingFilter(field_name=_SpecimenColumn.LABEL)
    filterset_cls = _specimen_set([], {"probe": declared})
    published = filterset_cls._filter_table()["probe"]
    if lazy_field_name:
        assert published is not declared
        assert type(published.field_name) is str
        assert published.field_name == "label"
        assert published.lookup_expr is _SpecimenColumn.EXACT
    else:
        assert published is declared
    instance = filterset_cls(data={"probe": "large"}, queryset=ScalarSpecimen.objects.all())
    rows = require(instance.qs, is_queryset)
    assert sorted(str(read_attr(row, "label")) for row in rows) == ["large"]


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


@pytest.mark.parametrize(
    "lazy",
    [
        pytest.param({"field_name": SimpleLazyObject(lambda: "children")}, id="lazy-field-name"),
        pytest.param({"lookup_expr": gettext_lazy("icontains")}, id="lazy-lookup-expr"),
    ],
)
def test_a_lazily_spelled_to_many_key_lookup_is_refused_naming_its_text(
    lazy: dict[str, object],
) -> None:
    """A lazy ``field_name`` or ``lookup_expr`` on a to-many key is refused as its text would be."""
    case = _UNRESOLVABLE_LEAVES["reverse-key-lookup-its-target-key-resolves"]
    filterset_cls = _specimen_set([], {"probe": _respelled(case.declare(), **lazy)})
    with pytest.raises(ConfigurationError) as exc_info:
        _build_at_root(filterset_cls)
    assert str(exc_info.value) == _unresolvable_refusal(case)


def _raw_outcome(filterset_cls: type[FilterSet], data: dict[str, object]) -> object:
    """The rows ``filterset_cls`` applied raw to ``data`` answers, or the exception it raises.

    The exception is Django's at the request, or the set's refusal at its construction.
    """
    try:
        rows = require(filterset_cls(data=data).qs, is_queryset)
        return sorted(str(read_attr(row, "pk")) for row in rows)
    except (TypeError, FieldError, ConfigurationError) as exc:
        return (truth.kind(exc), str(exc))


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["target-get-queryset", "related-filter"])
@pytest.mark.parametrize(
    "lazy",
    [
        pytest.param({"field_name": gettext_lazy("children")}, id="lazy-field-name"),
        pytest.param(
            {"field_name": SimpleLazyObject(lambda: "children")},
            id="simple-lazy-object-field-name",
        ),
        pytest.param({"lookup_expr": gettext_lazy("exact")}, id="lazy-lookup-expr"),
        pytest.param(
            {"lookup_expr": SimpleLazyObject(lambda: "icontains")},
            id="lazy-lookup-expr-the-relation-refuses",
        ),
    ],
)
def test_a_lazily_spelled_raw_to_many_key_leaf_answers_walked_as_unwalked(
    lazy: dict[str, object],
    walk: str,
) -> None:
    """A walked hop builds a lazily spelled to-many key leaf as Django builds it unwalked.

    The set reads the lazy name as the text it renders and the walked leaf builds its
    declared predicate first, so whatever Django and django-filter answer that text with
    unwalked (rows, or the refusal of a lookup the relation does not register at the
    set's first construction), the walked request answers too.
    """
    key = _reverse_key()
    data: dict[str, object] = {"probe": [str(read_attr(key.target, "pk"))]}

    def declare() -> Filter:
        probe = ModelMultipleChoiceFilter(field_name="children", queryset=_scalar_specimens())
        return _respelled(probe, **lazy)

    unwalked = _raw_outcome(_raw_key_set(key, "unwalked", declare()), data)
    registry.clear()
    assert _raw_outcome(_raw_key_set(key, walk, declare()), data) == unwalked
