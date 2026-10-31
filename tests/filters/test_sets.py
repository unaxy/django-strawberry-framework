"""FilterSet construction, generation provenance, form data, callback counts, and object identity.

Covers the metaclass (`FilterSetMetaclass`), `FilterSet`'s class-creation
behavior (cycle-safe `get_filters` expansion + `_get_fields` narrowing),
the spec-027 Decision 4 Relay-vs-scalar conditional in
`filter_for_field`, and the spec-027 Decision 8 apply pipeline
(`apply_sync` / `apply_async` / `apply` + the five named helpers).

Empty-filter, ``FILTER_INVALID``, nested ``check_<field>_permission`` denial,
EXISTS SQL, and Relay-relation ``isNull`` Boolean vs GlobalID-list ``exact``
live in ``test_library_api.py`` / ``test_products_api.py``.
This file keeps generation provenance, capability gates, permission callback
counts, normalized form data and exact query-object state.
``test_filter_apply_compatibility_api.py`` owns dispatcher errors and consumer
contexts; ``test_filter_consumer_contracts_api.py`` owns explicit related querysets;
``test_filter_publication_api.py`` owns published shapes, constructor-edited fields
and the corresponding request outcomes.

Consumer-shaped queryset multiplicity, generated relation/reverse predicates and operator bags
live in ``test_filter_querysets_api.py``, ``test_generated_relation_filters_api.py``,
``test_generated_reverse_filters_api.py`` and ``test_library_api.py`` under
``examples/fakeshop/test_query/``. Exact normalized form keys, generation markers and raw Query
state remain package observations.

Default values, unresolved targets, consumer forms and prefixed methods are owned by
``examples/fakeshop/test_query/test_relation_filter_defaults_api.py``.
Compound values, projected reentry and authored empty relation keys are owned by
``examples/fakeshop/test_query/test_relation_filter_form_paths_api.py``.
Null extension, orphan-safe negation and correlated SQL are owned by
``examples/fakeshop/test_query/test_relation_leaf_sql_api.py``.
The retained projection classes, class templates and callback counts are private
observations; these live siblings own their corresponding payloads and SQL.
"""

from __future__ import annotations

import asyncio
import copy
import dataclasses
import datetime
import importlib
import re
import threading
import uuid
from collections import OrderedDict
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping
from decimal import Decimal
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Literal,
    NamedTuple,
    NoReturn,
    TypeAlias,
    TypeVar,
    cast,
)
from unittest import mock

import django_filters
import pytest
import strawberry
from apps.kanban import models as kanban_models
from apps.library import models as library_models
from apps.library.filters import (
    BookFilter,
    LoanFilter,
    PatronFilter,
)
from apps.products import services
from apps.products.models import Category, Item
from apps.scalars import models as scalar_models
from asgiref.sync import sync_to_async
from django import forms
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import DEFAULT_DB_ALIAS, connection, connections, models
from django.db import models as dj_models
from django.db import models as django_models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.sqlite3.operations import DatabaseOperations as SQLiteOperations
from django.db.models import Lookup, Q, QuerySet
from django.db.models.fields.related import ManyToManyRel, ManyToOneRel, OneToOneRel
from django.db.models.functions import Length, Upper
from django.forms import ModelChoiceField, ModelMultipleChoiceField
from django.http import HttpRequest, QueryDict
from django.test import override_settings
from django.test.utils import CaptureQueriesContext, isolate_apps
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy
from django_filters import (
    AllValuesFilter,
    BaseInFilter,
    BaseRangeFilter,
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    Filter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    NumberFilter,
)
from django_filters.exceptions import FieldLookupError
from django_filters.filterset import FILTER_FOR_DBFIELD_DEFAULTS as UPSTREAM
from django_filters.filterset import BaseFilterSet, UnknownFieldBehavior
from django_filters.filterset import FilterSetMetaclass as DjangoFilterMetaclass
from django_filters.widgets import SuffixedMultiWidget
from graphql import GraphQLError
from typing_extensions import override

from django_strawberry_framework import (
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError, PathResolutionError
from django_strawberry_framework.filters import (
    ArrayFilter,
    FilterSet,
    FilterSetMetaclass,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    ListFilter,
    RangeFilter,
    RelatedFilter,
)
from django_strawberry_framework.filters import sets as sets_module
from django_strawberry_framework.filters.base import (
    _GLOBALID_RELATION_PK_ATTR,
    EnumChoiceFilter,
    EnumLookupFilter,
    EnumMemberValue,
    IntegerInFilter,
    MembershipInFilter,
    RelationPkFilter,
    RelationPkMultipleFilter,
    _GlobalIDMultipleChoiceField,
    membership_in_filter_class,
)
from django_strawberry_framework.filters.inputs import (
    _field_specs,
    convert_filter_to_input_annotation,
    filter_lookup_table,
)
from django_strawberry_framework.filters.sets import (
    _ALL_FAMILY_PROFILES,
    _AUDITED_DJANGO_FILTER_RANGE,
    _EMPTY_BODY_DYNAMIC_CSV_ATTRS,
    _FILTER_FAMILY_REGISTRY,
    _GENERATION_PROVENANCE_ATTR,
    _MODEL_CHOICE_ONLY_EXTRAS,
    _PACKAGE_POLICY_BASELINE,
    _PUBLIC_PACKAGE_FILTER_DEFAULTS,
    _SEQUENCE_LOOKUP_PROFILE,
    CandidateFilterMetadata,
    ChildProjection,
    ExpansionSnapshot,
    FilterGenerationProvenance,
    ProjectedChildFilter,
    _candidate_metadata_for,
    _expansion_record,
    _family_profile_for,
    _lookups_for_field,
    _normalize_policy_entry,
    _NormalizedPolicyEntry,
    _release_is_audited,
    _stamp_generation_provenance,
    _upstream_authored,
    filter_generation_provenance,
)
from django_strawberry_framework.optimizer.predicates import correlated_inner_root
from django_strawberry_framework.registry import registry
from django_strawberry_framework.sets_mixins import collect_related_declarations
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.types.relay import SyncMisuseError, apply_interfaces
from django_strawberry_framework.utils import truth, widgets
from django_strawberry_framework.utils._narrowing import (
    is_dict,
    is_exact_pair,
    is_list_or_tuple,
    read_attr,
    require,
)
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.utils.permissions import DeclaredHop, UndeclaredHop
from django_strawberry_framework.utils.relations import ClassifiedPath, classify_path
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.utils.widgets import multi_widget_keys
from tests._idioms import (
    STR_ENUM,
    STR_SUBCLASS_KINDS,
    ClassReadRaises,
    canonical_order,
    comparing_metaclass,
    definition_raises,
    is_object_dict,
    pickle_roundtrip,
    saved_pk,
    scrambled,
    str_subclass_name,
)
from tests._postgres_fields import (
    FakeArrayField,
    FakeSplitArrayWidget,
    patch_array_field,
    real_array_of,
)
from tests._postgresql_stand_in import BINDING_MODES, postgresql_stand_in
from tests._relation_fixtures import (
    RpGenericHolder,
    RpGenericProxyHolder,
    RpGenericTag,
    generic_fixture_rows,
)
from tests._subprocess import run_in_fresh_process
from tests.optimizer import _link_models

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable
    from typing_extensions import Never, TypeIs

    from django_strawberry_framework.utils.typing import ModelField

_M = TypeVar("_M", bound=django_models.Model)

if TYPE_CHECKING:
    # Each field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them;
    # ``null=True`` adds ``None`` to both.
    _FK: TypeAlias = django_models.ForeignKey[_M | Combinable, _M]
    _O2O: TypeAlias = django_models.OneToOneField[_M | Combinable, _M]
    _Text: TypeAlias = django_models.TextField[str | Combinable, str]
    _PositiveInt: TypeAlias = django_models.PositiveIntegerField[
        float | int | str | Combinable,
        int,
    ]


def _is_model_choice_field(field: object) -> TypeIs[ModelChoiceField[django_models.Model]]:
    """Return whether ``field`` is a ``ModelChoiceField`` (multiple-choice subclass included)."""
    return isinstance(field, ModelChoiceField)


def _is_model_multiple_choice_field(
    field: object,
) -> TypeIs[ModelMultipleChoiceField[django_models.Model]]:
    """Return whether ``field`` is a ``ModelMultipleChoiceField``."""
    return isinstance(field, ModelMultipleChoiceField)


def _snapshot(filterset_class: type[FilterSet]) -> ExpansionSnapshot:
    """Return ``filterset_class``'s published expansion snapshot, failing when none is published."""
    snapshot = filterset_class._expansion_snapshot()
    assert snapshot is not None
    return snapshot


def _provenance(filter_instance: object) -> FilterGenerationProvenance:
    """Return the generation-provenance record stamped on ``filter_instance``, failing when unstamped."""
    provenance = filter_generation_provenance(filter_instance)
    assert provenance is not None
    return provenance


class _CrDesk(django_models.Model):
    """Root of a test-local multi-table-inheritance line the target-model check reads.

    Fakeshop's ``Venue`` line has no forward relation onto a column a child
    declares, and no child keyed on anything but its parent link, so these
    models stand in for the shapes the check refuses there. ``managed = False``:
    the check runs at expansion and reads no table.
    """

    name: _Text = django_models.TextField()

    class Meta:
        app_label = "products"
        managed = False


class _CrKioskDesk(_CrDesk):
    """An MTI child declaring its own unique ``kiosk_code``."""

    kiosk_code: _Text = django_models.TextField(unique=True)

    # basedpyright: Django's ModelBase pops a concrete model's Meta (only an abstract model keeps
    # one), so _CrDesk has no Meta at run time for this one to subclass
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        app_label = "products"
        managed = False


class _CrOwnKeyDesk(_CrDesk):
    """An MTI child keyed on its own ``code``, so its parent link is not its primary key."""

    code: _Text = django_models.TextField(primary_key=True)

    # basedpyright: Django's ModelBase pops a concrete model's Meta (only an abstract model keeps
    # one), so _CrDesk has no Meta at run time for this one to subclass
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        app_label = "products"
        managed = False


class _CrLamp(django_models.Model):
    """A lamp keyed to desks by their key and to kiosk desks by the child's ``kiosk_code``.

    One relation per link shape onto each side: a foreign key, a one-to-one and
    a many-to-many onto ``_CrDesk``'s key, and the same three onto
    ``_CrKioskDesk.kiosk_code``.
    """

    desk: _FK[_CrDesk] = django_models.ForeignKey(
        _CrDesk,
        on_delete=django_models.CASCADE,
        related_name="lamps",
    )
    spare_desk: _O2O[_CrDesk] = django_models.OneToOneField(
        _CrDesk,
        on_delete=django_models.CASCADE,
        related_name="spare_lamp",
    )
    desks: django_models.ManyToManyField[_CrDesk, django_models.Model] = (
        django_models.ManyToManyField(_CrDesk, related_name="shared_lamps")
    )
    kiosk: _FK[_CrKioskDesk] = django_models.ForeignKey(
        _CrKioskDesk,
        on_delete=django_models.CASCADE,
        to_field="kiosk_code",
        related_name="kiosk_lamps",
    )
    spare_kiosk: _O2O[_CrKioskDesk] = django_models.OneToOneField(
        _CrKioskDesk,
        on_delete=django_models.CASCADE,
        to_field="kiosk_code",
        related_name="spare_kiosk_lamp",
    )
    kiosks: django_models.ManyToManyField[_CrKioskDesk, CrLampKiosk] = (
        django_models.ManyToManyField(
            _CrKioskDesk,
            through="CrLampKiosk",
            related_name="shared_kiosk_lamps",
        )
    )

    class Meta:
        app_label = "products"
        managed = False


class CrLampKiosk(django_models.Model):
    """The ``_CrLamp.kiosks`` join row, keyed to the kiosk desk by its ``kiosk_code``."""

    lamp: _FK[_CrLamp] = django_models.ForeignKey(_CrLamp, on_delete=django_models.CASCADE)
    kiosk: _FK[_CrKioskDesk] = django_models.ForeignKey(
        _CrKioskDesk,
        on_delete=django_models.CASCADE,
        to_field="kiosk_code",
    )

    class Meta:
        app_label = "products"
        managed = False


class _CrUnmanagedModel(django_models.Model):
    """The abstract base whose ``Meta`` an MTI child below subclasses.

    Django keeps the ``Meta`` of an abstract model only, so a child of a concrete
    model spells its own ``Meta`` as a subclass of this one (Django's documented
    abstract-``Meta`` inheritance), and the checker reads that ``Meta`` as a
    compatible override.
    """

    class Meta:
        abstract = True
        app_label = "products"
        managed = False


class _CrDeskNote(django_models.Model):
    """A generic-key note whose reverse ``GenericRel`` ``note_desk`` reaches ``_CrNoteDesk``.

    Its ``object_id`` is no foreign key: a note may carry a ``_CrNoteRoot`` row's
    pk under ``_CrNoteDesk``'s content type with no ``_CrNoteDesk`` row extending it.
    """

    content_type: _FK[ContentType] = django_models.ForeignKey(
        ContentType,
        on_delete=django_models.CASCADE,
        related_name="+",
    )
    object_id: _PositiveInt = django_models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        app_label = "products"
        managed = False


class _CrNoteRoot(_CrUnmanagedModel):
    """Root of the MTI line whose child declares the ``GenericRelation``."""


class _CrNoteDesk(_CrNoteRoot):
    """An MTI child whose ``GenericRelation`` makes ``_CrDeskNote.note_desk`` a visible field."""

    notes = GenericRelation(_CrDeskNote, related_query_name="note_desk")

    class Meta(_CrUnmanagedModel.Meta):
        pass


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


class _RequestContext:
    """The `info.context` shape the filter pipeline reads: one `request`."""

    def __init__(self, req: HttpRequest) -> None:
        super().__init__()
        self.request = req


class _RequestInfo:
    """The `info` shape the filter pipeline reads: one `context`."""

    def __init__(self, ctx: _RequestContext) -> None:
        super().__init__()
        self.context = ctx


def _make_info(request: HttpRequest | None = None) -> _RequestInfo:
    """Return a minimal `info`-shaped object carrying `info.context.request`."""
    return _RequestInfo(_RequestContext(request or HttpRequest()))


def test_filterset_metaclass_is_django_filter_metaclass_subclass() -> None:
    assert issubclass(FilterSetMetaclass, DjangoFilterMetaclass)


def test_filterset_metaclass_collects_related_filters() -> None:
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    assert isinstance(BranchFilter.related_filters, OrderedDict)
    assert "shelves" in BranchFilter.related_filters
    assert BranchFilter.related_filters["shelves"].bound_filterset is BranchFilter


def test_filterset_metaclass_none_removal_survives_diamond_inheritance() -> None:
    """An earlier base's ``None`` tombstone prevents later-base resurrection."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BaseFilter(FilterSet):
        # ``None`` in a subclass is the django-filter removal idiom, so the slot admits it.
        shelves: RelatedFilter | None = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    class RemovedFilter(BaseFilter):
        shelves = None

    class KeptFilter(BaseFilter):
        pass

    class CombinedFilter(RemovedFilter, KeptFilter):
        pass

    for filterset_cls in (RemovedFilter, CombinedFilter):
        assert "shelves" not in filterset_cls.declared_filters
        assert "shelves" not in filterset_cls.related_filters
        assert not any(
            name == "shelves" or name.startswith("shelves__")
            for name in filterset_cls.base_filters
        )
        assert not any(
            name == "shelves" or name.startswith("shelves__")
            for name in filterset_cls.get_filters()
        )
    assert "shelves" in BaseFilter.related_filters


def test_filterset_metaclass_aliases_filter_fields_to_fields() -> None:
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            filter_fields = {"code": ["exact"]}

    # Aliasing happens at metaclass time; the `Meta.fields` attribute lands.
    assert ShelfFilter._meta.fields == {"code": ["exact"]}
    # The consumer's synonym stays on the class Meta (factory kwargs drop it).
    assert ShelfFilter.Meta.filter_fields == {"code": ["exact"]}


def test_filterset_metaclass_fields_alias_sees_inherited_meta_fields() -> None:
    """``hasattr`` (not ``__dict__``) is the class-Meta alias presence contract.

    A consumer Meta that subclasses another Meta already carrying ``fields``
    skips the alias -- shipped FilterSetMetaclass behavior. The shared
    resolver must not switch the class path to own-attribute checks.
    """

    class BaseMeta:
        model = library_models.Shelf
        fields = {"code": ["exact"]}

    class ShelfFilter(FilterSet):
        class Meta(BaseMeta):
            filter_fields = {"is_private": ["exact"]}

    assert ShelfFilter._meta.fields == {"code": ["exact"]}


def test_filterset_metaclass_does_not_expand_at_class_creation() -> None:
    class ShelfFilter(FilterSet):
        # `RelatedFilter("SiblingFilter")` references a class declared LATER.
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter("ShelfFilter", field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # Class creation succeeded with a string forward reference; nothing cached yet.
    assert ShelfFilter.__dict__.get("_expanded_filters") is None
    assert BranchFilter.__dict__.get("_expanded_filters") is None


def test_filterset_get_filters_triggers_expansion() -> None:
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact", "icontains"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    filters = BranchFilter.get_filters()
    # Same-class filter plus expanded `<rel>__<child_lookup>` keys.
    assert "name" in filters
    assert "shelves__code" in filters
    assert "shelves__code__icontains" in filters


def test_filterset_get_filters_caches_after_full_resolution() -> None:
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    first = BranchFilter.get_filters()
    second = BranchFilter.get_filters()
    # A fresh map per call, as django-filter's; the filters themselves are the cached ones.
    assert first is not second
    assert first == second == BranchFilter.__dict__.get("_expanded_filters")
    # The published table is one object every read shares.
    table = BranchFilter._filter_table()
    assert table is BranchFilter._filter_table()
    assert dict(table) == first


def test_filterset_get_filters_resets_expansion_guard() -> None:
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    BranchFilter.get_filters()
    assert BranchFilter._is_expanding_filters is False


def test_filterset_get_filters_does_not_cache_when_string_filterset_remains() -> None:
    class BranchFilter(FilterSet):
        # Reference to a non-existent class - `expand_related_filter` raises.
        bogus = RelatedFilter("DefinitelyDoesNotExistFilter", field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    with pytest.raises(ImportError):
        BranchFilter.get_filters()
    assert BranchFilter.__dict__.get("_expanded_filters") is None


def _desk_ring(base: type[FilterSet] = FilterSet) -> dict[str, type[FilterSet]]:
    """Three filter sets in one ``RelatedFilter`` cycle: branch -> desk -> shelf -> branch.

    Each target is a factory, so the cycle closes over sets declared later in this scope.
    Every set subclasses ``base``.
    """

    class RingBranchFilter(base):
        desks = RelatedFilter(lambda: RingDeskFilter, field_name="circulation_desks")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"], "city": ["exact"]}

    class RingDeskFilter(base):
        shelf = RelatedFilter(lambda: RingShelfFilter, field_name="shelf")

        class Meta:
            model = library_models.CirculationDesk
            fields = {"name": ["exact"]}

    class RingShelfFilter(base):
        branch = RelatedFilter(lambda: RingBranchFilter, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"], "topic": ["exact"]}

    return {"branch": RingBranchFilter, "desk": RingDeskFilter, "shelf": RingShelfFilter}


# Each set follows the cycle until it reaches a set already on the path, whose
# own filters (its ``RelatedFilter`` head included) end the path there.
_DESK_RING_FILTERS = {
    "branch": {
        "name",
        "city",
        "desks",
        "desks__name",
        "desks__shelf",
        "desks__shelf__code",
        "desks__shelf__topic",
        "desks__shelf__branch",
        "desks__shelf__branch__name",
        "desks__shelf__branch__city",
        "desks__shelf__branch__desks",
    },
    "desk": {
        "name",
        "shelf",
        "shelf__code",
        "shelf__topic",
        "shelf__branch",
        "shelf__branch__name",
        "shelf__branch__city",
        "shelf__branch__desks",
        "shelf__branch__desks__name",
        "shelf__branch__desks__shelf",
    },
    "shelf": {
        "code",
        "topic",
        "branch",
        "branch__name",
        "branch__city",
        "branch__desks",
        "branch__desks__name",
        "branch__desks__shelf",
        "branch__desks__shelf__code",
        "branch__desks__shelf__topic",
        "branch__desks__shelf__branch",
    },
}


@pytest.mark.parametrize("first", sorted(_DESK_RING_FILTERS))
def test_a_related_filter_cycle_expands_each_set_alike_whichever_set_expands_first(
    first: str,
) -> None:
    """Each set of a ``RelatedFilter`` cycle has one surface, whichever set's ``get_filters`` runs first.

    Expanding one member builds the others' expansions while it is still
    expanding; none of them depends on which member that was.
    """
    ring = _desk_ring()
    ring[first].get_filters()

    assert {name: set(fs.get_filters()) for name, fs in ring.items()} == _DESK_RING_FILTERS


@pytest.mark.parametrize("first", sorted(_DESK_RING_FILTERS))
def test_a_related_filter_cycle_finalizes_the_same_private_tables_in_every_registration_order(
    first: str,
) -> None:
    """Finalization leaves each cycle member with the same private flat-key table in every registration order.

    Published GraphQL names are owned by test_filter_publication_api.py.
    """
    ring = _desk_ring()
    models = {
        "branch": library_models.Branch,
        "desk": library_models.CirculationDesk,
        "shelf": library_models.Shelf,
    }
    order = sorted(ring, key=lambda name: name != first)
    for name in order:
        meta = {"model": models[name], "fields": ("id",), "filterset_class": ring[name]}
        type(f"Ring{name.title()}Type", (DjangoType,), {"Meta": type("Meta", (), meta)})
    finalize_django_types()

    assert {name: set(fs.get_filters()) for name, fs in ring.items()} == _DESK_RING_FILTERS


@pytest.mark.parametrize("paused", sorted(_DESK_RING_FILTERS))
def test_a_get_filters_call_reentering_a_set_mid_build_gets_the_surface_the_build_publishes(
    paused: str,
) -> None:
    """A second thread reading a cycle member while its first expansion runs gets the whole surface.

    The reentry guard is class-level, so the second call sees the set mid-build;
    it gets the surface built again, unpublished, never the unexpanded filters.
    """
    inside, release = threading.Event(), threading.Event()
    builders: set[int] = set()
    pausing: list[type[FilterSet]] = []

    class PausingFilterSet(FilterSet):
        @classmethod
        @override
        def get_fields(cls) -> OrderedDict[str, object]:
            if cls in pausing and threading.get_ident() in builders:
                inside.set()
                assert release.wait(5)
            return super().get_fields()

    ring = _desk_ring(PausingFilterSet)
    pausing.append(ring[paused])
    built: list[set[str]] = []

    def build() -> None:
        builders.add(threading.get_ident())
        built.append(set(ring[paused].get_filters()))

    builder = threading.Thread(target=build)
    builder.start()
    assert inside.wait(5)
    try:
        reentered = set(ring[paused].get_filters())
    finally:
        release.set()
        builder.join(5)

    assert reentered == _DESK_RING_FILTERS[paused]
    assert built == [reentered]


@pytest.mark.parametrize("member", sorted(_DESK_RING_FILTERS))
def test_a_get_filters_call_reentering_a_set_from_its_own_build_gets_the_surface_the_build_publishes(
    member: str,
) -> None:
    """A cycle member's build reading the member again gets the surface the build then publishes.

    ``get_fields`` runs inside the member's own expansion, so its ``get_filters`` call
    meets the member mid-build in the same thread.
    """
    observed: list[set[str]] = []
    reading: list[type[FilterSet]] = []

    class ReadingFilterSet(FilterSet):
        @classmethod
        @override
        def get_fields(cls) -> OrderedDict[str, object]:
            if cls in reading and cls.__dict__.get(cls._lifecycle.guard):
                reading.remove(cls)
                observed.append(set(cls.get_filters()))
            return super().get_fields()

    ring = _desk_ring(ReadingFilterSet)
    reading.append(ring[member])

    published = set(ring[member].get_filters())

    assert observed == [_DESK_RING_FILTERS[member]]
    assert published == _DESK_RING_FILTERS[member]


# A two-set cycle with a ``RelatedFilter(None)`` placeholder on one set: the
# placeholder stays a head on its set and on every flat copy of that set.
_PLACEHOLDER_CYCLE_FILTERS = {
    "shelf": {
        "branch": {
            "name",
            "shelves",
            "shelves__code",
            "shelves__books",
            "shelves__branch",
            "shelves__branch__name",
            "shelves__branch__shelves",
        },
        "shelf": {
            "code",
            "books",
            "branch",
            "branch__name",
            "branch__shelves",
            "branch__shelves__code",
            "branch__shelves__books",
            "branch__shelves__branch",
        },
    },
    "branch": {
        "branch": {
            "name",
            "shelves",
            "desks",
            "shelves__code",
            "shelves__branch",
            "shelves__branch__name",
            "shelves__branch__shelves",
            "shelves__branch__desks",
        },
        "shelf": {
            "code",
            "branch",
            "branch__name",
            "branch__shelves",
            "branch__desks",
            "branch__shelves__code",
            "branch__shelves__branch",
        },
    },
}


@pytest.mark.parametrize("first", ["branch", "shelf"])
@pytest.mark.parametrize("owner", sorted(_PLACEHOLDER_CYCLE_FILTERS))
def test_a_related_filter_cycle_through_a_set_with_a_placeholder_declaration_expands_each_set(
    owner: str,
    first: str,
) -> None:
    """A ``RelatedFilter(None)`` placeholder inside a cycle reaches no set and expands nothing.

    The cycle still ends where a path reaches a set already on it, whichever set
    of the cycle declares the placeholder and whichever set expands first.
    """
    branch_attrs: dict[str, object] = {
        "shelves": RelatedFilter(lambda: sets["shelf"], field_name="shelves"),
        "Meta": type("Meta", (), {"model": library_models.Branch, "fields": {"name": ["exact"]}}),
    }
    shelf_attrs: dict[str, object] = {
        "branch": RelatedFilter(lambda: sets["branch"], field_name="branch"),
        "Meta": type("Meta", (), {"model": library_models.Shelf, "fields": {"code": ["exact"]}}),
    }
    if owner == "branch":
        branch_attrs["desks"] = RelatedFilter(None, field_name="circulation_desks")
    else:
        shelf_attrs["books"] = RelatedFilter(None, field_name="books")
    sets: dict[str, type[FilterSet]] = {
        "branch": type("PlaceholderBranchFilter", (FilterSet,), branch_attrs),
        "shelf": type("PlaceholderShelfFilter", (FilterSet,), shelf_attrs),
    }
    sets[first].get_filters()

    assert {name: set(fs.get_filters()) for name, fs in sets.items()} == (
        _PLACEHOLDER_CYCLE_FILTERS[owner]
    )


@pytest.mark.parametrize("hostile", ["path", "target"])
@pytest.mark.parametrize("verdict", ["equal", "unequal", "raises"])
def test_a_related_filter_target_is_matched_against_the_expansion_path_by_identity(
    verdict: Literal["equal", "unequal", "raises"],
    hostile: Literal["path", "target"],
) -> None:
    """A ``RelatedFilter`` target expands whatever its or a path set's metaclass ``__eq__`` says.

    The cycle rule finds a set already on the path by identity, so a consumer metaclass
    ``__eq__`` (on the target set or on the set whose path it extends) is never called: an
    always-equal answer cannot end the path early, a raising one cannot escape ``get_filters``.
    """
    calls: list[str] = []
    meta = comparing_metaclass(FilterSetMetaclass, verdict, calls)

    class IdentityBranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    class IdentityShelfFilter(
        FilterSet,
        metaclass=meta if hostile == "target" else FilterSetMetaclass,
    ):
        branch = RelatedFilter(IdentityBranchFilter, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class IdentityBookFilter(
        FilterSet,
        metaclass=meta if hostile == "path" else FilterSetMetaclass,
    ):
        shelf = RelatedFilter(IdentityShelfFilter, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    assert set(IdentityBookFilter.get_filters()) == {
        "title",
        "shelf",
        "shelf__code",
        "shelf__branch",
        "shelf__branch__name",
    }
    assert calls == []


@pytest.mark.parametrize("relation", ["parent", "children"])
def test_a_self_referential_related_filter_ends_its_path_one_step_after_the_set(
    relation: str,
) -> None:
    """A set whose ``RelatedFilter`` targets the set itself publishes the target's filters once.

    The root is already on the path when its own declaration expands, so the
    target contributes its unexpanded filters, its ``RelatedFilter`` head included,
    and the path ends there.
    """
    self_referential = type(
        "SelfReferentialSpecimenFilter",
        (FilterSet,),
        {
            relation: RelatedFilter(lambda: self_referential, field_name=relation),
            "Meta": type(
                "Meta",
                (),
                {"model": scalar_models.ScalarSpecimen, "fields": {"label": ["exact"]}},
            ),
        },
    )

    assert set(self_referential.get_filters()) == {
        "label",
        relation,
        f"{relation}__label",
        f"{relation}__{relation}",
    }


def test_a_related_filter_target_off_the_path_contributes_its_own_get_filters() -> None:
    """A target whose declarations reach no set on the path copies its own ``get_filters()``.

    The target expands as it does alone, so a filter a consumer ``get_filters``
    override adds is published under the declaring set's relation too.
    """

    class OverridingShelfFilter(FilterSet):
        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            filters = OrderedDict(super().get_filters())
            filters["extra"] = CharFilter(field_name="topic", lookup_expr="icontains")
            return filters

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class OverriddenTargetBranchFilter(FilterSet):
        shelves = RelatedFilter(OverridingShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    assert set(OverriddenTargetBranchFilter.get_filters()) == {
        "name",
        "shelves",
        "shelves__code",
        "shelves__extra",
    }


def _without_code(filters: OrderedDict[str, Filter]) -> OrderedDict[str, Filter]:
    reshaped = OrderedDict(filters)
    del reshaped["code"]
    return reshaped


def _delete_code_in_place(filters: OrderedDict[str, Filter]) -> OrderedDict[str, Filter]:
    del filters["code"]
    return filters


def _code_as_kode(filters: OrderedDict[str, Filter]) -> OrderedDict[str, Filter]:
    return OrderedDict(("kode" if name == "code" else name, f) for name, f in filters.items())


def _code_over_topic(filters: OrderedDict[str, Filter]) -> OrderedDict[str, Filter]:
    reshaped = OrderedDict(filters)
    reshaped["code"] = CharFilter(field_name="topic", lookup_expr="icontains")
    return reshaped


def _deep_copies(filters: OrderedDict[str, Filter]) -> OrderedDict[str, Filter]:
    return OrderedDict((name, copy.deepcopy(f)) for name, f in filters.items())


def _extra_in_place(filters: OrderedDict[str, Filter]) -> OrderedDict[str, Filter]:
    filters["extra"] = CharFilter(field_name="topic", lookup_expr="icontains")
    return filters


_Reshape: TypeAlias = Callable[[OrderedDict[str, Filter]], OrderedDict[str, Filter]]


#: Each ``get_filters()`` override over a ``code`` shelf set: what it does to
#: ``super().get_filters()``, the filter and value that then keep shelf ``S1``
#: (``None`` when it leaves none to send), and the key it drops.
_SHELF_OVERRIDES: dict[str, tuple[_Reshape, tuple[str, str] | None, str | None]] = {
    "remove": (_without_code, None, "code"),
    "delete-in-place": (_delete_code_in_place, None, "code"),
    "rename": (_code_as_kode, ("kode", "S1"), "code"),
    "replace": (_code_over_topic, ("code", "alp"), None),
    "deep-copies": (_deep_copies, ("code", "S1"), None),
    "add-in-place": (_extra_in_place, ("extra", "alp"), None),
}


_DROPPING_SHELF_OVERRIDES = [name for name, (_, _, dropped) in _SHELF_OVERRIDES.items() if dropped]


def _overridden_shelf_set(reshape: _Reshape, *, customize: bool) -> type[FilterSet]:
    """A ``code`` shelf set whose ``get_filters()`` returns ``reshape(super().get_filters())``.

    When ``customize`` it also overrides ``__init__``, so a parent projects its
    filters (``ProjectedChildFilter``), each running inside an instance of it.
    """

    class OverriddenShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            return reshape(super().get_filters())

    if not customize:
        return OverriddenShelfFilter

    class CustomizedShelfFilter(OverriddenShelfFilter):
        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

    return CustomizedShelfFilter


def _shelves_parent(child: type[FilterSet]) -> type[FilterSet]:
    """A branch set expanding ``shelves`` into ``child``."""

    class ShelvesBranchFilter(FilterSet):
        shelves = RelatedFilter(child, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    return ShelvesBranchFilter


def _seed_two_shelved_branches() -> None:
    """Branch ``B1`` holds shelf ``S1`` (topic ``alpha``); ``B2`` holds ``S2`` (``beta``)."""
    _register_plain_types(library_models.Shelf, library_models.Branch)
    first = library_models.Branch.objects.create(name="B1")
    second = library_models.Branch.objects.create(name="B2")
    library_models.Shelf.objects.create(branch=first, code="S1", topic="alpha")
    library_models.Shelf.objects.create(branch=second, code="S2", topic="beta")


@pytest.mark.django_db
@pytest.mark.parametrize("customize", [False, True], ids=["expanded", "projected"])
@pytest.mark.parametrize("shape", _DROPPING_SHELF_OVERRIDES)
def test_a_key_a_get_filters_override_drops_is_absent_everywhere(
    shape: str,
    *,
    customize: bool,
) -> None:
    """A key the override removes or renames is no filter of the set, its parent or an instance.

    Every call returns the same table, an override deleting from what
    ``super().get_filters()`` returned included.
    """
    reshape, _probe, dropped = _SHELF_OVERRIDES[shape]
    assert dropped is not None
    child = _overridden_shelf_set(reshape, customize=customize)
    parent = _shelves_parent(child)
    flat = f"shelves__{dropped}"

    assert flat not in parent._filter_table()
    assert flat not in filter_lookup_table(parent).by_input_attr
    assert dropped not in child._filter_table()
    assert dropped not in child.base_filters
    assert dropped not in filter_lookup_table(child).by_input_attr
    assert list(child.get_filters()) == list(child.get_filters()) == list(child._filter_table())
    assert dropped not in child(queryset=library_models.Shelf.objects.none()).filters


@pytest.mark.django_db
@pytest.mark.parametrize("customize", [False, True], ids=["expanded", "projected"])
@pytest.mark.parametrize("shape", ["rename", "replace", "add-in-place"])
def test_a_directly_constructed_set_runs_the_filters_its_override_published(
    shape: str,
    *,
    customize: bool,
) -> None:
    """``Set(data, queryset).qs``, django-filter's own use, filters by the published table."""
    reshape, probe, _dropped = _SHELF_OVERRIDES[shape]
    assert probe is not None
    key, value = probe
    _seed_two_shelved_branches()
    child = _overridden_shelf_set(reshape, customize=customize)
    _ = _shelves_parent(child)._filter_table()

    filtered = child({key: value}, queryset=library_models.Shelf.objects.all()).qs
    assert sorted(filtered.values_list("code", flat=True)) == ["S1"]


@pytest.mark.parametrize("spelling", ["standalone", "flat", "nested"])
@pytest.mark.parametrize("customize", [False, True], ids=["expanded", "projected"])
def test_a_published_filter_read_does_not_repeat_the_consumer_override(
    spelling: str,
    *,
    customize: bool,
) -> None:
    """Publishing invokes the child override twice; each consumer path then reuses its published table.

    Callback counts are private. Runtime copied-filter payloads are owned by
    test_library_api.py::test_a_published_filter_override_runs_through_every_wire_spelling.
    """
    calls: list[str] = []

    def counted(filters: OrderedDict[str, Filter]) -> OrderedDict[str, Filter]:
        calls.append("get_filters")
        return _deep_copies(filters)

    _register_plain_types(library_models.Shelf, library_models.Branch)
    child = _overridden_shelf_set(counted, customize=customize)
    parent = _shelves_parent(child)
    calls.clear()

    _ = parent._filter_table()
    assert calls == ["get_filters", "get_filters"]
    calls.clear()
    selected, criteria = {
        "standalone": (child, {"code": "S1"}),
        "flat": (parent, {"shelves__code": "S1"}),
        "nested": (parent, {"shelves": {"code": "S1"}}),
    }[spelling]
    model = selected._meta.model
    assert model is not None
    selected.apply_sync(criteria, model._default_manager.all(), _make_info())
    assert calls == []


def _shelf_branch_cycle(reshape: _Reshape, *, customize: bool) -> tuple[type[FilterSet], ...]:
    """A shelf set (overriding ``get_filters()``) and a branch set expanding each other.

    Returns ``(shelf set, branch set)``; the branch's ``shelves`` resolves to the
    shelf set, its ``__init__`` overridden when ``customize``.
    """
    resolved: dict[str, type[FilterSet]] = {}

    class CycleBranchFilter(FilterSet):
        shelves = RelatedFilter(lambda: resolved["shelf"], field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    class CycleShelfFilter(FilterSet):
        branch = RelatedFilter(CycleBranchFilter, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            return reshape(super().get_filters())

    shelf: type[FilterSet] = CycleShelfFilter
    if customize:

        class CustomizedCycleShelfFilter(CycleShelfFilter):
            def __init__(
                self,
                data: QueryDict | dict[str, object] | None = None,
                queryset: QuerySet[django_models.Model] | None = None,
                *,
                request: HttpRequest | None = None,
                prefix: str | None = None,
            ) -> None:
                super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

        shelf = CustomizedCycleShelfFilter
    resolved["shelf"] = shelf
    return shelf, CycleBranchFilter


@pytest.mark.parametrize("customize", [False, True], ids=["expanded", "projected"])
@pytest.mark.parametrize("shape", ["remove", "rename", "add-in-place"])
def test_a_cycle_member_override_contributes_only_its_private_published_keys(
    shape: str,
    *,
    customize: bool,
) -> None:
    """Every lap of a cycle retains the override's private keys and omits any key it removed.

    Native cyclic rename/add predicates live in test_filter_publication_api.py.
    """
    reshape, probe, dropped = _SHELF_OVERRIDES[shape]
    shelf, branch = _shelf_branch_cycle(reshape, customize=customize)

    shelf_table = shelf._filter_table()
    branch_table = branch._filter_table()
    if dropped is not None:
        assert f"shelves__{dropped}" not in branch_table
        assert f"branch__shelves__{dropped}" not in shelf_table
    if probe is not None:
        key, _value = probe
        assert f"branch__shelves__{key}" in shelf_table


def test_a_cycle_of_projected_copies_publishes_each_set_once_and_reexpands_it_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Around a cycle of projected copies each set publishes once and re-expands once per build.

    Every set overrides ``__init__``, so every flat copy is a ``ProjectedChildFilter``
    whose form field reads its child set's table: publishing a set reads its copies'
    widget keys, which read the next set's table around the ring and back to the set
    publishing (served the table being published), and to a set still building (served
    the surface the build's scope keeps for it).
    """

    class InitFilterSet(FilterSet):
        @override
        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

    ring = _desk_ring(InitFilterSet)
    publishes: list[type[FilterSet]] = []
    root_expansions: list[type[FilterSet]] = []
    publish = FilterSet._publish_filters.__func__
    expand_along = FilterSet._expand_along.__func__

    def counting_publish(cls: type[FilterSet], expansion: Mapping[str, Filter]) -> None:
        publishes.append(cls)
        publish(cls, expansion)

    def counting_expand_along(
        cls: type[FilterSet],
        path: tuple[type[FilterSet], ...],
        scope: object,
    ) -> object:
        if path == (cls,):
            root_expansions.append(cls)
        return object_result(expand_along, cls, path, scope)

    monkeypatch.setattr(FilterSet, "_publish_filters", classmethod(counting_publish))
    monkeypatch.setattr(FilterSet, "_expand_along", classmethod(counting_expand_along))

    table = ring["branch"]._filter_table()

    assert isinstance(table["desks__shelf__code"], ProjectedChildFilter)
    assert set(table) == _DESK_RING_FILTERS["branch"]
    for member in ring.values():
        assert publishes.count(member) == 1
        assert root_expansions.count(member) <= 2  # its build, and every read re-entering it


def test_a_set_read_while_it_builds_answers_its_unpublished_get_filters() -> None:
    """A captured-branch check re-entering the set being built reads its ``get_filters()``.

    ``ReachingShelfFilter`` declares ``branch`` beside ``branch__shelves__books``, so
    its build checks whether ``branch``'s target reaches ``shelves__books``; that walk
    returns to ``ReachingShelfFilter`` through ``LoopBranchFilter.shelves`` while it is
    still building, where its filters (its override's ``extra`` included) answer
    unpublished. No path it reaches starts with ``books``, so the set publishes.
    """
    reads_while_building: list[bool] = []
    resolved: dict[str, type[FilterSet]] = {}

    class BooksTitleFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    class LoopBranchFilter(FilterSet):
        shelves = RelatedFilter(lambda: resolved["shelf"], field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    class ReachingShelfFilter(FilterSet):
        branch = RelatedFilter(LoopBranchFilter, field_name="branch")
        branch_books = RelatedFilter(BooksTitleFilter, field_name="branch__shelves__books")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            reads_while_building.append(bool(cls.__dict__.get("_is_expanding_filters")))
            return _extra_in_place(super().get_filters())

    resolved["shelf"] = ReachingShelfFilter
    reads_while_building.clear()

    table = ReachingShelfFilter._filter_table()

    assert True in reads_while_building
    assert ReachingShelfFilter._expansion_snapshot() is not None
    assert {"code", "extra", "branch__shelves__extra"} <= set(table)


@pytest.mark.parametrize("target", ["apps.library.filters.ShelfFilter", "ShelfFilter"])
@pytest.mark.parametrize("overridden", [False, True], ids=["plain", "overridden"])
def test_a_set_that_cannot_publish_answers_its_get_filters_on_every_read(
    target: str,
    *,
    overridden: bool,
) -> None:
    """A model-less set whose ``RelatedFilter`` target is still a lazy string never publishes.

    Its expansion never resolves the target, so no read caches it; the set's table is
    its ``get_filters()`` result, a ``get_filters()`` override's ``extra`` included,
    read after read.
    """

    class UnpublishableFilter(FilterSet):
        name = CharFilter(field_name="name")
        later = RelatedFilter(target, field_name="later")

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            filters = super().get_filters()
            return _extra_in_place(filters) if overridden else filters

    expected = ["name", "later", "extra"] if overridden else ["name", "later"]
    assert list(UnpublishableFilter._filter_table()) == expected
    assert list(UnpublishableFilter._filter_table()) == expected
    assert UnpublishableFilter._expansion_snapshot() is None


@pytest.mark.parametrize("customize", [False, True], ids=["expanded", "projected"])
def test_a_flat_copy_under_a_parents_own_generated_key_is_deferred(
    *,
    customize: bool,
) -> None:
    """The expansion snapshot defers a required copy even over a generated parent key.

    The live publication tests exercise the request verdicts. This row retains the private
    publication-table ownership verdict.
    """

    class RequiredCodeShelfFilter(FilterSet):
        code = CharFilter(field_name="code", required=True)

        class Meta:
            model = library_models.Shelf
            fields = {"topic": ["exact"]}

    child: type[FilterSet] = RequiredCodeShelfFilter
    if customize:

        class CustomizedRequiredCodeShelfFilter(RequiredCodeShelfFilter):
            def __init__(
                self,
                data: QueryDict | dict[str, object] | None = None,
                queryset: QuerySet[django_models.Model] | None = None,
                *,
                request: HttpRequest | None = None,
                prefix: str | None = None,
            ) -> None:
                super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

        child = CustomizedRequiredCodeShelfFilter

    class CollidingBranchFilter(FilterSet):
        shelves = RelatedFilter(child, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"], "shelves__code": ["exact"]}

    _ = CollidingBranchFilter._filter_table()
    snapshot = CollidingBranchFilter._expansion_snapshot()
    assert snapshot is not None
    assert "shelves__code" in snapshot.deferred_copies


@pytest.mark.django_db
def test_a_filter_a_get_filters_override_adds_is_gated_on_its_field_name() -> None:
    """An added filter no class body declares gates as a generated one: ``check_<field_name>``.

    ``extra`` filters ``topic``, so supplying it fires ``check_topic_permission``,
    never ``check_extra_permission`` (a declared head's own-name gate).
    """
    _register_plain_types(library_models.Shelf)

    class GatedOverriddenShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            return _extra_in_place(super().get_filters())

        check_extra_permission = _gate("Shelf.extra")
        check_topic_permission = _gate("Shelf.topic")

    root = library_models.Shelf.objects.all()
    assert _fired_gates(GatedOverriddenShelfFilter, {"extra": "alp"}, root) == {"Shelf.topic"}


def _flat_limit_message(
    root: type[FilterSet],
    crossing: str,
    trail: str,
    limit: int,
) -> str:
    """The ``ConfigurationError`` a set's expansion raises past ``MAX_FLAT_FILTERS``."""
    return (
        f"FilterSet {root.__qualname__}: its RelatedFilter expansion publishes more than "
        f"{limit} flat filters, crossed expanding {crossing} along {trail}. Raise "
        "DJANGO_STRAWBERRY_FRAMEWORK['MAX_FLAT_FILTERS'], or declare fewer RelatedFilter "
        "edges in the cycle."
    )


@pytest.mark.parametrize("hide_flat_filters", [False, True])
@pytest.mark.parametrize(
    ("limit", "crossing"),
    [
        (8, None),
        (7, ("branch", "desks", ("branch",))),
        (5, ("desk", "shelf", ("branch", "desk"))),
    ],
    ids=["at-the-limit", "one-past-at-the-root", "past-on-an-inner-path"],
)
def test_a_set_whose_expansion_passes_max_flat_filters_fails_its_build(
    limit: int,
    crossing: tuple[str, str, tuple[str, ...]] | None,
    hide_flat_filters: bool,  # noqa: FBT001
) -> None:
    """A set publishes up to ``MAX_FLAT_FILTERS`` flat filters; one more fails its build.

    Every ring set publishes eight flat filters. Past the limit, the walk stops at
    the first path whose flat filters pass it: a path's filters are copied onto
    every set before it, so an inner path past the limit names the root, the
    declaration being expanded and the path. ``HIDE_FLAT_FILTERS`` hides the flat
    fields from the schema only, so the limit holds under it too.
    """
    ring = _desk_ring()
    with override_settings(
        DJANGO_STRAWBERRY_FRAMEWORK={
            "MAX_FLAT_FILTERS": limit,
            "HIDE_FLAT_FILTERS": hide_flat_filters,
        },
    ):
        if crossing is None:
            surfaces = {name: set(fs.get_filters()) for name, fs in ring.items()}
            assert surfaces == _DESK_RING_FILTERS
            return
        owner, declaration, path = crossing
        with pytest.raises(ConfigurationError) as excinfo:
            ring["branch"].get_filters()

    assert str(excinfo.value) == _flat_limit_message(
        ring["branch"],
        f"{ring[owner].__qualname__}.{declaration}",
        " -> ".join(ring[name].__qualname__ for name in path),
        limit,
    )
    # A failed build publishes nothing; the set builds once the limit admits it.
    assert ring["branch"].__dict__.get("_expanded_filters") is None
    assert set(ring["branch"].get_filters()) == _DESK_RING_FILTERS["branch"]


def test_max_flat_filters_zero_admits_a_set_that_publishes_no_flat_filter() -> None:
    """``MAX_FLAT_FILTERS = 0`` refuses any flat copy and admits a set with none."""

    class LoneShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"MAX_FLAT_FILTERS": 0}):
        assert list(LoneShelfFilter.get_filters()) == ["code"]


@pytest.mark.parametrize(
    ("value", "rendered"),
    [
        (True, "bool True"),
        (False, "bool False"),
        (-1, "int -1"),
        (-10_000, "int -10000"),
        (1.5, "float 1.5"),
        ("10", "str '10'"),
        (None, "NoneType None"),
    ],
    ids=[
        "true",
        "false",
        "negative",
        "large-negative",
        "float",
        "str",
        "none",
    ],
)
def test_max_flat_filters_must_be_a_non_negative_int(value: object, rendered: str) -> None:
    """A ``bool``, a negative or a non-``int`` ``MAX_FLAT_FILTERS`` fails the build, naming the key.

    There is no spelling that disables the limit: ``None`` is refused like any
    other non-``int``.
    """
    ring = _desk_ring()
    with (
        override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"MAX_FLAT_FILTERS": value}),
        pytest.raises(ConfigurationError) as excinfo,
    ):
        ring["branch"].get_filters()

    assert str(excinfo.value) == (
        f"DJANGO_STRAWBERRY_FRAMEWORK['MAX_FLAT_FILTERS'] must be a non-negative int; "
        f"got {rendered}."
    )


def _dense_library_filtersets() -> dict[str, type[FilterSet]]:
    """Six library filter sets, each declaring a ``RelatedFilter`` over every relation between them.

    Several cycles share sets (``shelf`` <-> ``desk``, ``branch`` -> ``shelf`` and
    ``branch`` -> ``desk``), so one set is reached along many paths through the same
    sets in different orders.
    """

    class DenseBranchFilter(FilterSet):
        shelves = RelatedFilter(lambda: DenseShelfFilter, field_name="shelves")
        desks = RelatedFilter(lambda: DenseDeskFilter, field_name="circulation_desks")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    class DenseShelfFilter(FilterSet):
        branch = RelatedFilter(lambda: DenseBranchFilter, field_name="branch")
        books = RelatedFilter(lambda: DenseBookFilter, field_name="books")
        desk = RelatedFilter(lambda: DenseDeskFilter, field_name="circulation_desk")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class DenseDeskFilter(FilterSet):
        branch = RelatedFilter(lambda: DenseBranchFilter, field_name="branch")
        shelf = RelatedFilter(lambda: DenseShelfFilter, field_name="shelf")

        class Meta:
            model = library_models.CirculationDesk
            fields = {"name": ["exact"]}

    class DenseBookFilter(FilterSet):
        shelf = RelatedFilter(lambda: DenseShelfFilter, field_name="shelf")
        loans = RelatedFilter(lambda: DenseLoanFilter, field_name="loans")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    class DenseLoanFilter(FilterSet):
        book = RelatedFilter(lambda: DenseBookFilter, field_name="book")
        patron = RelatedFilter(lambda: DensePatronFilter, field_name="patron")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    class DensePatronFilter(FilterSet):
        loans = RelatedFilter(lambda: DenseLoanFilter, field_name="loans")

        class Meta:
            model = library_models.Patron
            fields = {"email": ["exact"]}

    return {
        "branch": DenseBranchFilter,
        "shelf": DenseShelfFilter,
        "desk": DenseDeskFilter,
        "book": DenseBookFilter,
        "loan": DenseLoanFilter,
        "patron": DensePatronFilter,
    }


def _path_walk(filterset: type[FilterSet], path: tuple[type[FilterSet], ...] = ()) -> list[str]:
    """The flat surface by the cycle rule alone, walking every path afresh.

    Each declaration copies its target's names along the path; a target already on
    the path contributes its own names unexpanded. A name copied twice keeps its
    first position, as ``dict.update`` does.
    """
    path = (*path, filterset)
    names = dict.fromkeys(filterset._unexpanded_filters())
    declarations = truth.class_dict(filterset)["related_filters"]
    assert is_dict(declarations)
    for declaration_name, declaration in declarations.items():
        assert isinstance(declaration, RelatedFilter)
        target = declaration.filterset
        assert target is not None
        child = (
            list(target._unexpanded_filters())
            if any(visited is target for visited in path)
            else _path_walk(target, path)
        )
        names.update(dict.fromkeys(f"{declaration_name}__{name}" for name in child))
    return list(names)


@pytest.mark.parametrize(
    "first",
    [
        "branch",
        "shelf",
        "desk",
        "book",
        "loan",
        "patron",
    ],
)
def test_a_dense_related_filter_graph_publishes_the_fresh_path_walk_whichever_set_builds_first(
    first: str,
) -> None:
    """Every set's surface, in order, is the walk that expands every path afresh.

    One build keeps each inner path's expansion by the set and the sets on its
    path and serves it to every other path through the same sets; the published
    surface is the one a walk recomputing every path yields, whichever set builds
    first.
    """
    dense = _dense_library_filtersets()
    _ = dense[first].get_filters()

    surfaces = {name: list(fs.get_filters()) for name, fs in dense.items()}
    expected = {name: _path_walk(fs) for name, fs in dense.items()}
    assert surfaces == expected
    assert {name: len(names) for name, names in surfaces.items()} == {
        "branch": 72,
        "shelf": 56,
        "desk": 72,
        "book": 55,
        "loan": 55,
        "patron": 54,
    }


_FS = TypeVar("_FS", bound=FilterSet)


def _pipeline_instance(
    filterset_class: type[_FS],
    *,
    data: Mapping[str, object] | None = None,
    queryset: QuerySet[django_models.Model] | None = None,
    request: HttpRequest | None = None,
    prefix: str | None = None,
) -> _FS:
    """Construct ``filterset_class`` as the package's request pipeline does, deferring flat copies."""
    with sets_module._pipeline_built(filterset_class):
        return filterset_class(data=data, queryset=queryset, request=request, prefix=prefix)


def _seed_desk_ring_rows() -> dict[str, int]:
    """Three branches, each with one shelf and one desk on it; returns the branch pks by name."""
    north = library_models.Branch.objects.create(name="North", city="Oslo")
    south = library_models.Branch.objects.create(name="South", city="Rome")
    east = library_models.Branch.objects.create(name="East", city="Kyiv")
    north_shelf = library_models.Shelf.objects.create(branch=north, code="N-1", topic="maps")
    south_shelf = library_models.Shelf.objects.create(branch=south, code="S-1", topic="law")
    east_shelf = library_models.Shelf.objects.create(branch=east, code="E-1", topic="art")
    library_models.CirculationDesk.objects.create(branch=north, shelf=north_shelf, name="Front")
    library_models.CirculationDesk.objects.create(branch=south, shelf=south_shelf, name="Back")
    library_models.CirculationDesk.objects.create(branch=east, shelf=east_shelf, name="Side")
    # Each hop's target needs a registered type; ``fields`` keeps the desk's
    # generic foreign key, which maps to no single GraphQL type, off it.
    for model in (library_models.Branch, library_models.CirculationDesk, library_models.Shelf):
        meta = {"model": model, "fields": ("id",)}
        type(f"Ring{model.__name__}Type", (DjangoType,), {"Meta": type("Meta", (), meta)})
    return {"North": saved_pk(north), "South": saved_pk(south), "East": saved_pk(east)}


def test_a_request_copies_the_sets_own_filters_and_the_flat_copies_its_data_names() -> None:
    """An instance copies its own filters and the named flat copies; reading ``filters`` copies all.

    The named copy is bound like every copy django-filter makes, and the copies
    already made are the ones ``filters`` returns, in the class's order.
    """
    branch = _desk_ring()["branch"]
    flat = sorted(set(branch.get_filters()) - {"name", "city", "desks"})
    assert _snapshot(branch).deferred_copies == frozenset(flat)

    instance = _pipeline_instance(
        branch,
        data={"desks__shelf__code": "N-1"},
        queryset=library_models.Branch.objects.all(),
    )
    copied = dict(instance._copied_filters)
    assert list(copied) == [
        "name",
        "city",
        "desks",
        "desks__shelf__code",
    ]
    named = copied["desks__shelf__code"]
    assert named is not branch.base_filters["desks__shelf__code"]
    assert vars(named)["parent"] is instance
    assert vars(named)["model"] is library_models.Branch

    filters = instance.filters
    assert list(filters) == list(branch.base_filters)
    assert filters["desks__shelf__code"] is named
    assert all(filters[name] is copied[name] for name in copied)
    for name, original in branch.base_filters.items():
        assert filters[name] is not original
        assert vars(filters[name])["parent"] is instance
    assert instance.filters is filters


def test_a_filter_copy_refuses_an_instance_whose_queryset_was_unset() -> None:
    """``__init__`` always defaults ``queryset``; an instance stripped of it copies no filter."""
    branch = _desk_ring()["branch"]
    branch.get_filters()
    instance = _pipeline_instance(
        branch,
        data={"name": "North"},
        queryset=library_models.Branch.objects.all(),
    )
    instance.queryset = None
    with pytest.raises(TypeError, match="expected the type the source guarantees"):
        instance._filter_named("desks__shelf__branch__city")


def test_a_flat_copy_read_by_name_is_copied_alone_and_kept() -> None:
    """A package read by name copies that one deferred filter; reading ``filters`` keeps it."""
    branch = _desk_ring()["branch"]
    branch.get_filters()
    instance = _pipeline_instance(
        branch,
        data={"name": "North"},
        queryset=library_models.Branch.objects.all(),
    )

    read = instance._filter_named("desks__shelf__branch__city")

    assert list(instance._copied_filters) == [
        "name",
        "city",
        "desks",
        "desks__shelf__branch__city",
    ]
    assert vars(read)["parent"] is instance
    assert instance.filters["desks__shelf__branch__city"] is read
    assert list(instance.filters) == list(branch.base_filters)


@pytest.mark.parametrize(
    ("member", "data", "copied"),
    [
        (
            "branch",
            {"desks__shelf__code": "N-1", "name": "North"},
            [
                "name",
                "city",
                "desks",
                "desks__shelf__code",
            ],
        ),
        (
            "shelf",
            {"branch__desks__name": "Front"},
            [
                "code",
                "topic",
                "branch",
                "branch__desks__name",
            ],
        ),
    ],
)
def test_a_bound_form_holds_the_copied_filters_and_an_unbound_one_every_filter(
    member: str,
    data: dict[str, object],
    copied: list[str],
) -> None:
    """A bound request's form holds what it copied, in the class's order; an unbound form all."""
    filterset = _desk_ring()[member]
    filterset.get_filters()
    model = filterset._meta.model
    assert model is not None

    bound = _pipeline_instance(filterset, data=data, queryset=model._default_manager.all())
    unbound = _pipeline_instance(filterset, queryset=model._default_manager.all())

    assert list(bound.form.fields) == copied
    assert list(unbound.form.fields) == list(filterset.base_filters)


class _DunderRangeWidget(SuffixedMultiWidget):
    """A two-box range widget reading ``<name>__low`` / ``<name>__high``, a ``__`` past the name."""

    suffixes: list[str] = ["_low", "_high"]

    def __init__(self, attrs: dict[str, object] | None = None) -> None:
        super().__init__((forms.TextInput, forms.TextInput), attrs)


@pytest.mark.parametrize(
    ("data", "prefix", "expected"),
    [
        ({"p-desks__shelf__code": "N-1"}, "p", ["desks__shelf__code"]),
        ({"desks__shelf__code": "N-1"}, "p", []),
        ({"desks__name_min": "A"}, None, ["desks__name"]),
        ({"desks__name": "A"}, None, []),
        ({"desks__span__low": "1"}, None, ["desks__span"]),
        ({"desks__probe_min": "x"}, None, ["desks__probe_min"]),
        ({"desks__shelf__code_0": "N", "desks__shelf": "1"}, None, []),
    ],
    ids=[
        "prefixed",
        "unprefixed-under-a-prefix",
        "widget-suffix",
        "multi-widget-bare-name",
        "dunder-widget-suffix",
        "suffix-head-is-not-a-name",
        "relation-heads-and-unread-suffixes",
    ],
)
def test_the_flat_copies_a_request_names_are_the_ones_whose_widgets_read_its_keys(
    data: dict[str, object],
    prefix: str | None,
    expected: list[str],
) -> None:
    """A form key names exactly the flat copies whose form field widget reads it, after the prefix.

    A multi-widget's copy is named by its own keys (``_min``, or a consumer's
    ``__low``), never by its bare name; a plain copy by its name. A key's head before a
    suffix or a relation separator names nothing, so ``desks__probe_min`` never names
    ``desks__probe``.
    """
    filters: dict[str, Filter] = {
        "desks__shelf__code": CharFilter(field_name="code"),
        "desks__name": django_filters.RangeFilter(field_name="name"),
        "desks__span": django_filters.RangeFilter(field_name="name", widget=_DunderRangeWidget),
        "desks__probe": CharFilter(field_name="name", required=True),
        "desks__probe_min": CharFilter(field_name="name"),
    }
    copy_keys = sets_module._copy_form_keys(filters, frozenset(filters))
    assert sorted(set(sets_module._named_flat_copies(data, copy_keys, prefix))) == expected


def test_a_prefixed_pipeline_instance_copies_its_named_flat_filter() -> None:
    """A prefixed pipeline instance copies the exact flat key its physical data names.

    This observes private copy membership. The real prefixed two-hop form is
    exercised by test_filter_publication_api.py.
    """
    branch = _desk_ring()["branch"]
    branch.get_filters()

    instance = _pipeline_instance(
        branch,
        data={"p-desks__shelf__code": "S-1"},
        queryset=library_models.Branch.objects.order_by("pk"),
        prefix="p",
    )

    assert "desks__shelf__code" in instance._copied_filters


def _split_code_branch_filter(monkeypatch: pytest.MonkeyPatch) -> type[FilterSet]:
    """A ``Branch`` set copying a shelf ``code__in`` filter whose widget is a size-2 ``SplitArrayWidget``.

    The widget sentinel points at the driver-free double before the set publishes, so
    its copy keys are read off the widget the published copy builds.
    """
    monkeypatch.setattr(widgets, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)

    class SplitShelfChild(FilterSet):
        arr = Filter(
            field_name="code",
            lookup_expr="in",
            widget=FakeSplitArrayWidget(forms.TextInput(), size=2),
        )

        class Meta:
            model = library_models.Shelf
            fields = {"topic": ["exact"]}

    class SplitBranch(FilterSet):
        shelves = RelatedFilter(SplitShelfChild, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    _register_plain_types(library_models.Shelf)
    SplitBranch.get_filters()
    return SplitBranch


@pytest.mark.parametrize("prefix", [None, "p"], ids=["unprefixed", "prefixed"])
def test_a_driver_free_split_widget_names_only_its_indexed_copy_keys(
    prefix: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A deferred copy whose widget is a ``SplitArrayWidget`` is named by ``<name>_0`` / ``_1``.

    Only the frozen copy-key index and copied/unnamed ledgers remain here, using
    the optional widget classifier's driver-free shape. Public query results for
    the real widget, including pipeline apply and direct prefixed forms, live in
    ``examples/fakeshop/test_query/test_raw_filter_forms_api.py::test_a_real_split_array_widget_filters_under_its_actual_index_keys``.
    """
    branch_filter = _split_code_branch_filter(monkeypatch)
    assert _snapshot(branch_filter).copy_keys["shelves__arr_0"] == {"shelves__arr"}
    assert _snapshot(branch_filter).copy_keys["shelves__arr_1"] == {"shelves__arr"}
    assert "shelves__arr" not in _snapshot(branch_filter).copy_keys
    lead = f"{prefix}-" if prefix else ""

    instance = _pipeline_instance(
        branch_filter,
        data={f"{lead}shelves__arr_0": "A-1", f"{lead}shelves__arr_1": "Z-9"},
        queryset=library_models.Branch.objects.none(),
        prefix=prefix,
    )

    assert "shelves__arr" in instance._copied_filters
    assert "shelves__arr" not in instance._unnamed_copies


@pytest.mark.django_db
def test_a_supplied_split_array_leaf_is_read_by_its_prefixed_per_index_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A directly built prefixed set reads ``p-shelves__arr_0`` / ``_1`` as the leaf's keys.

    Any per-index key present supplies the leaf; with none of them the leaf is absent.
    """
    branch_filter = _split_code_branch_filter(monkeypatch)

    def build(data: dict[str, object]) -> FilterSet:
        return branch_filter(
            data=data,
            queryset=library_models.Branch.objects.all(),
            request=HttpRequest(),
            prefix="p",
        )

    supplied = build({"p-shelves__arr_0": "A-1", "p-shelves__arr_1": "B-1"})
    assert not supplied._leaf_absent("shelves__arr")
    assert not build({"p-shelves__arr_1": "B-1"})._leaf_absent("shelves__arr")
    assert build({"p-shelves__arr": "A-1"})._leaf_absent("shelves__arr")
    assert build({})._leaf_absent("shelves__arr")


@pytest.mark.django_db
def test_a_leaf_whose_widget_reads_no_key_is_read_by_its_prefixed_name() -> None:
    """A ``MultiWidget`` with no sub-widget reads no key, so its leaf is read under its name.

    The bare prefixed key supplies the leaf; with none of it present the leaf is absent.
    """

    class EmptyShelfChild(FilterSet):
        bare = Filter(field_name="code", widget=forms.MultiWidget([]))

        class Meta:
            model = library_models.Shelf
            fields = {"topic": ["exact"]}

    class EmptyBranch(FilterSet):
        shelves = RelatedFilter(EmptyShelfChild, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    _register_plain_types(library_models.Shelf)
    EmptyBranch.get_filters()

    def build(data: dict[str, object]) -> FilterSet:
        return EmptyBranch(
            data=data,
            queryset=library_models.Branch.objects.all(),
            request=HttpRequest(),
            prefix="p",
        )

    assert not build({"p-shelves__bare": "A-1"})._leaf_absent("shelves__bare")
    assert build({})._leaf_absent("shelves__bare")


def test_a_copys_form_keys_are_every_key_its_widget_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_widget_keys`` answers each key the widget reads, recursively, else the bare name.

    A ``SplitArrayWidget`` reads one key per index; a ``MultiWidget`` nested in a
    ``MultiWidget`` reads its own sub-widgets' keys; a ``MultiWidget`` with no
    sub-widget reads none, so the copy is read under its name.
    """
    monkeypatch.setattr(widgets, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)
    split = CharFilter(field_name="code", widget=FakeSplitArrayWidget(forms.TextInput(), size=3))
    nested = CharFilter(
        field_name="code",
        widget=forms.MultiWidget(
            [forms.MultiWidget([forms.TextInput, forms.TextInput]), forms.TextInput],
        ),
    )
    empty = CharFilter(field_name="code", widget=forms.MultiWidget([]))

    assert sets_module._widget_keys(split, "arr") == ["arr_0", "arr_1", "arr_2"]
    assert sets_module._widget_keys(nested, "pair") == ["pair_0_0", "pair_0_1", "pair_1"]
    assert sets_module._widget_keys(empty, "none") == ["none"]


_DEFERRED_EQUIVALENCE_INPUTS: dict[str, tuple[dict[str, object], list[str], int]] = {
    "own-leaf": ({"name": {"exact": "North"}}, ["North"], 1),
    "flat": ({"desks__shelf__code": {"exact": "S-1"}}, ["South"], 1),
    "deep-flat": ({"desks__shelf__branch__city": {"exact": "Oslo"}}, ["North"], 1),
    "nested": ({"desks": {"shelf": {"code": {"exact": "N-1"}}}}, ["North"], 1),
    "or-of-flat": (
        {
            "or_": [
                {"desks__name": {"exact": "Back"}},
                {"desks__shelf__topic": {"exact": "maps"}},
            ],
        },
        ["North", "South"],
        1,
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(_DEFERRED_EQUIVALENCE_INPUTS))
def test_a_request_deferring_flat_copies_filters_as_one_copying_every_filter(
    case: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The deferred copies change no result and no query: a set deferring none answers the same.

    The comparison set's snapshot defers nothing, so its instances copy every
    filter up front, as django-filter's own constructor does.
    """
    filter_input, expected_names, expected_queries = _DEFERRED_EQUIVALENCE_INPUTS[case]
    pks = _seed_desk_ring_rows()
    branch = _desk_ring()["branch"]
    branch.get_filters()

    def run() -> tuple[list[int], int]:
        with CaptureQueriesContext(connection) as ctx:
            rows = list(
                branch.apply_sync(
                    filter_input,
                    library_models.Branch.objects.order_by("pk"),
                    _make_info(),
                ).values_list("pk", flat=True),
            )
        return rows, len(ctx.captured_queries)

    deferring = run()
    monkeypatch.setattr(
        branch,
        "_expanded_snapshot",
        dataclasses.replace(_snapshot(branch), deferred_copies=frozenset()),
    )
    copying_all = run()

    assert deferring == copying_all == ([pks[name] for name in expected_names], expected_queries)


def test_a_constructor_instance_edit_leaves_the_class_filter_template_unchanged() -> None:
    """The class template is private; native constructor holders own the per-request lookup edit."""
    base_branch = _desk_ring()["branch"]

    class CaseFoldingBranchFilter(base_branch):
        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            self.filters["desks__shelf__code"].lookup_expr = "iexact"

    CaseFoldingBranchFilter.get_filters()
    _ = _pipeline_instance(
        CaseFoldingBranchFilter,
        data={"desks__shelf__code": "s-1"},
        queryset=library_models.Branch.objects.order_by("pk"),
    )

    assert CaseFoldingBranchFilter.base_filters["desks__shelf__code"].lookup_expr == "exact"


class _SettlingFilterSet(FilterSet):
    """A filter set whose ``__init__`` reads ``self.filters``, which copies every filter, named or not."""

    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[django_models.Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)
        assert self.filters


def _required_child_branch_filter(base: type[FilterSet], method: str | None) -> type[FilterSet]:
    """A ``Branch`` filter set on ``base`` expanding ``shelves`` over a child with a required leaf."""

    class RequiredCodeShelfFilter(FilterSet):
        code_required = CharFilter(field_name="code", required=True, method=method)

        def filter_code(
            self,
            queryset: QuerySet[library_models.Shelf],
            name: str,
            value: str,
        ) -> QuerySet[library_models.Shelf]:
            return queryset.filter(**{name: value})

        class Meta:
            model = library_models.Shelf
            fields = {"topic": ["exact"]}

    class RequiredChildBranchFilter(base):
        shelves = RelatedFilter(RequiredCodeShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    return RequiredChildBranchFilter


@pytest.mark.parametrize("parent_init", ["inherited", "reads-filters"])
@pytest.mark.parametrize("method", [None, "filter_code"], ids=["rebound", "projected"])
def test_a_required_child_leaf_is_recorded_as_a_deferred_parent_copy(
    method: str | None,
    parent_init: str,
) -> None:
    """The expansion snapshot defers a required child leaf for both parent declaration shapes.

    The live publication tests exercise form ownership over HTTP. This row retains the private
    deferred-copy metadata instead of repeating its payloads.
    """
    base = _SettlingFilterSet if parent_init == "reads-filters" else FilterSet
    parent = _required_child_branch_filter(base, method)
    parent.get_filters()
    assert "shelves__code_required" in _snapshot(parent).deferred_copies


class _OpenIssuesOnlyFilter(CharFilter):
    """A consumer filter that constrains the rows even when its value is empty."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        return qs.filter(embargoed=False)


class _UnembargoedOnlyFilter(BooleanFilter):
    """A consumer boolean filter that keeps only unembargoed rows whatever its value."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        return qs.filter(embargoed=False)


class _AlwaysUnembargoedWidget(forms.NullBooleanSelect):
    """A consumer widget that reads every request as ``embargoed: false``, named or not."""

    @override
    def value_from_datadict(
        self,
        data: Mapping[str, object],
        files: object,
        name: str,
    ) -> bool | None:
        return False


def _issue_filter_whose_absence_filters(shape: str) -> type[FilterSet]:
    """An ``Issue`` filter set with one filter that constrains the rows when its key is absent."""
    absent_constrains: dict[str, Filter] = {
        # An absent checkbox key reads as ``False``, which is no empty value.
        "checkbox": BooleanFilter(field_name="embargoed", widget=forms.CheckboxInput),
        # A disabled field cleans to its ``initial`` whatever the data says.
        "disabled": BooleanFilter(field_name="embargoed", disabled=True, initial=False),
        "disabled-text": CharFilter(field_name="title", disabled=True, initial="B"),
        # Its ``filter`` is consumer code, which may act on an empty value.
        "consumer-filter": _OpenIssuesOnlyFilter(field_name="title"),
        "consumer-boolean-filter": _UnembargoedOnlyFilter(field_name="embargoed"),
        # A ``null_value`` equal to the absent key's cleaned value runs ``IS NULL``.
        "null-choice": ChoiceFilter(field_name="title", choices=[("B", "B")], null_value=""),
        "null-model-choice": ModelChoiceFilter(
            field_name="periodical",
            queryset=library_models.Periodical.objects.all(),
            null_value=None,
        ),
        # A consumer widget reads the data its own way.
        "consumer-widget": BooleanFilter(
            field_name="embargoed",
            widget=_AlwaysUnembargoedWidget,
        ),
    }
    return type(
        "AbsenceIssueFilter",
        (FilterSet,),
        {
            "open_only": absent_constrains[shape],
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Issue, "fields": {"title": ["exact"]}},
            ),
        },
    )


def _absence_periodical_filter(
    issue_filter: type[FilterSet],
    **namespace: object,
) -> type[FilterSet]:
    """A ``Periodical`` filter set expanding ``issues`` over ``issue_filter``, plus ``namespace``."""
    return type(
        "AbsencePeriodicalFilter",
        (FilterSet,),
        {
            "issues": RelatedFilter(issue_filter, field_name="issues"),
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Periodical, "fields": {"name": ["exact"]}},
            ),
            **namespace,
        },
    )


_ABSENCE_SHAPES: list[str] = [
    "checkbox",
    "disabled",
    "disabled-text",
    "consumer-filter",
    "consumer-boolean-filter",
    "null-choice",
    "null-model-choice",
    "consumer-widget",
]


@pytest.mark.parametrize("shape", _ABSENCE_SHAPES)
def test_a_child_absence_leaf_is_deferred_on_the_parent(shape: str) -> None:
    """The parent snapshot defers every child declaration whose own missing value would act.

    Snapshot membership is private generation metadata. Live unnamed-copy isolation and
    each named spelling, nested sibling and direct child form are covered by
    ``examples/fakeshop/test_query/test_filter_absence_api.py`` over HTTP.
    """
    parent = _absence_periodical_filter(_issue_filter_whose_absence_filters(shape))
    _register_plain_types(library_models.Issue)
    parent.get_filters()
    assert "issues__open_only" in _snapshot(parent).deferred_copies


@pytest.mark.parametrize(
    "filter_input",
    [{}, {"name": {"exact": "Open Review"}}],
    ids=["nothing", "own-leaf"],
)
def test_an_unnamed_flat_copy_calls_no_async_hop_visibility_hook(
    filter_input: dict[str, object],
) -> None:
    """An unnamed flat copy invokes no async target hook.

    The exact private callback list stays empty. Consumer absence payloads are
    owned by test_filter_absence_api.py.
    """
    calls: list[str] = []

    class AsyncOnlyIssueType(DjangoType):
        class Meta:
            model = library_models.Issue
            fields = ("id", "title")

        @classmethod
        @override
        # basedpyright: an ``async def get_queryset`` is a supported hook, awaited on the async path,
        # but the base hook has one signature, and its return cannot admit both a sync child's
        # ``QuerySet`` and an async child's coroutine without breaking every sync caller that
        # reads ``super().get_queryset(...)`` as a ``QuerySet``
        async def get_queryset(  # pyright: ignore[reportIncompatibleMethodOverride]
            cls,
            queryset: QuerySet[library_models.Issue],
            info: object,
            **kwargs: object,
        ) -> QuerySet[library_models.Issue]:
            calls.append("get_queryset")
            return await sync_to_async(lambda: queryset)()

    assert registry.get(library_models.Issue) is AsyncOnlyIssueType
    periodical_filter = _absence_periodical_filter(_issue_filter_whose_absence_filters("checkbox"))
    periodical_filter.get_filters()

    asyncio.run(
        periodical_filter.apply_async(
            filter_input,
            library_models.Periodical.objects.order_by("name"),
            _make_info(),
        ),
    )

    assert calls == []


def test_only_a_named_flat_copy_dispatches_its_child_gate() -> None:
    """Only the named flat copy dispatches the private child callback.

    Checkbox filtering and unnamed-copy absence outcomes are owned by
    test_filter_absence_api.py.
    """
    fired: list[str] = []

    class GatedIssueFilter(FilterSet):
        open_only = BooleanFilter(field_name="embargoed", widget=forms.CheckboxInput)

        class Meta:
            model = library_models.Issue
            fields = {"title": ["exact"]}

        def check_open_only_permission(self, _request: object) -> None:
            fired.append("open_only")

    periodical_filter = _absence_periodical_filter(GatedIssueFilter)
    _register_plain_types(library_models.Issue)
    periodical_filter.get_filters()

    periodical_filter.apply_sync({}, library_models.Periodical.objects.none(), _make_info())
    assert fired == []
    named = {"issues__open_only": {"exact": True}}
    periodical_filter.apply_sync(named, library_models.Periodical.objects.none(), _make_info())
    assert fired == ["open_only"]


class _DunderRangeIssueFilter(FilterSet):
    """An ``Issue`` filter set whose range widget reads ``number__low`` / ``number__high``."""

    span = django_filters.RangeFilter(field_name="number", widget=_DunderRangeWidget)

    class Meta:
        model = library_models.Issue
        fields = {"title": ["exact"]}


def test_a_deferred_range_copy_indexes_each_double_underscore_widget_key() -> None:
    """The expansion snapshot maps both physical widget keys to their deferred copy.

    ``test_filter_copy_keys_api.py`` owns the named and unnamed HTTP row verdicts;
    the snapshot's exact reverse index is private construction metadata.
    """
    _register_plain_types(library_models.Issue)
    periodical_filter = _absence_periodical_filter(_DunderRangeIssueFilter)
    periodical_filter.get_filters()
    keys = _snapshot(periodical_filter).copy_keys
    assert keys["issues__span__low"] == {"issues__span"}
    assert keys["issues__span__high"] == {"issues__span"}


def test_a_consumer_meta_form_preserves_the_deferred_copy_metadata() -> None:
    """Deferred-copy metadata is private; the native Meta.form holder owns named-field cleaning."""

    class ReadingForm(forms.Form):
        pass

    branch = _desk_ring()["branch"]
    branch.get_filters()
    meta = {"model": library_models.Branch, "fields": branch._meta.fields, "form": ReadingForm}
    own_form = type("OwnFormFilter", (branch,), {"Meta": type("Meta", (), meta)})
    own_form.get_filters()
    own = set(own_form._unexpanded_filters())
    assert _snapshot(own_form).deferred_copies == frozenset(set(own_form.base_filters) - own)


@pytest.mark.parametrize(
    "seam",
    [
        "filter_queryset",
        "qs",
        "form",
        "get_form_class",
        "errors",
        "is_valid",
        "meta-form",
    ],
)
def test_a_set_overriding_a_form_reading_seam_defers_every_flat_copy(seam: str) -> None:
    """A set overriding a seam that reads its form defers every flat copy, as any set does.

    An override of a seam that reads ``self.form`` / ``cleaned_data``, or its own
    ``Meta.form``, finds the set's own filters and the flat copies a request
    names; it reads any other copy's key with ``.get``.
    """

    class ReadingForm(forms.Form):
        pass

    branch = _desk_ring()["branch"]
    branch.get_filters()
    assert _snapshot(branch).deferred_copies
    meta: dict[str, object] = {"model": library_models.Branch, "fields": branch._meta.fields}
    namespace: dict[str, object] = {}
    if seam == "meta-form":
        meta["form"] = ReadingForm
    else:
        namespace[seam] = getattr(FilterSet, seam)
        if callable(namespace[seam]):
            original = cast("Callable[..., object]", namespace[seam])

            def overridden(self: FilterSet, *args: object) -> object:
                return original(self, *args)

            namespace[seam] = overridden
        else:
            namespace[seam] = property(cast("property", namespace[seam]).fget)
    namespace["Meta"] = type("Meta", (), meta)

    reading = type("ReadingBranchFilter", (branch,), namespace)
    reading.get_filters()
    own = set(reading._unexpanded_filters())
    assert _snapshot(reading).deferred_copies == frozenset(set(reading.base_filters) - own)


def test_a_consumer_filter_queryset_sees_only_its_named_copy_in_cleaned_data() -> None:
    """Only private metadata or callback observations remain here.

    Live sibling: ``examples/fakeshop/test_query/test_relation_filter_defaults_api.py``.
    """
    for model in (library_models.Branch, library_models.CirculationDesk, library_models.Shelf):
        meta = {"model": model, "fields": ("id",)}
        type(f"Ring{model.__name__}Type", (DjangoType,), {"Meta": type("Meta", (), meta)})
    base_branch = _desk_ring()["branch"]
    seen: list[tuple[object, bool]] = []

    class ReadingBranchFilter(base_branch):
        @override
        def filter_queryset(self, queryset: QuerySet[_M]) -> QuerySet[_M]:
            cleaned_data: dict[str, object] = self.form.cleaned_data
            seen.append((cleaned_data.get("desks__shelf__code"), "desks__name" in cleaned_data))
            return super().filter_queryset(queryset)

    ReadingBranchFilter.get_filters()
    instance = _pipeline_instance(
        ReadingBranchFilter,
        data={"name": "North", "desks__shelf__code": "N-1"},
        queryset=library_models.Branch.objects.order_by("pk"),
        request=HttpRequest(),
    )

    _ = instance.qs
    assert seen == [("N-1", False)]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("member", "own", "flat"),
    [
        ("branch", ["name", "city", "desks"], "desks__shelf__code"),
        ("shelf", ["code", "topic", "branch"], "branch__desks__name"),
    ],
)
def test_a_set_built_outside_the_package_pipeline_copies_and_renders_every_filter(
    member: str,
    own: list[str],
    flat: str,
) -> None:
    """A direct construction (a django-filter view, DRF's backend) copies every filter.

    Its form, bound or unbound, holds and renders every flat field, as django-filter's
    own constructor makes it; only an instance the package's request pipeline builds
    defers.
    """
    filterset = _desk_ring()[member]
    filterset.get_filters()
    model = filterset._meta.model
    assert model is not None

    bound = filterset(data=QueryDict(""), queryset=model._default_manager.all())
    unbound = filterset(queryset=model._default_manager.all())
    deferring = _pipeline_instance(
        filterset,
        data=QueryDict(""),
        queryset=model._default_manager.all(),
    )

    assert list(bound.form.fields) == list(filterset.base_filters)
    assert list(unbound.form.fields) == list(filterset.base_filters)
    assert f'name="{flat}"' in bound.form.as_p()
    assert list(deferring.form.fields) == own


def _customizing_issue_filter(edit: str) -> type[FilterSet]:
    """An ``Issue`` filter set whose ``__init__`` edits a filter so its absence constrains."""

    class CustomizingIssueFilter(FilterSet):
        open_only = BooleanFilter(field_name="embargoed")
        title_required = CharFilter(field_name="title")

        class Meta:
            model = library_models.Issue
            fields = {"title": ["exact"]}

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            if edit == "required":
                self.filters["title_required"].extra["required"] = True
            else:
                self.filters["open_only"].extra["widget"] = forms.CheckboxInput

    return CustomizingIssueFilter


@pytest.mark.parametrize("edit", ["required", "checkbox"])
def test_constructor_edited_child_leaves_remain_deferred_parent_copies(
    edit: str,
) -> None:
    """Constructor-customized child leaves remain in the parent's exact deferred-copy metadata.

    Real named/unnamed fields and the required/checkbox edits themselves are
    exercised by test_filter_publication_api.py.
    """
    issue_filter = _customizing_issue_filter(edit)

    class EditedPeriodicalFilter(FilterSet):
        issues = RelatedFilter(issue_filter, field_name="issues")

        class Meta:
            model = library_models.Periodical
            fields = {"name": ["exact"]}

    EditedPeriodicalFilter.get_filters()
    edited = "issues__title_required" if edit == "required" else "issues__open_only"
    assert edited in _snapshot(EditedPeriodicalFilter).deferred_copies


@pytest.mark.parametrize("read", ["by-name", "settled"])
def test_a_late_copied_filter_binds_to_the_instance_model(read: str) -> None:
    """Every late copy carries the exact parent model identity, whether read by name or by the full mapping.

    A real consumer reading the dynamic choice field over HTTP lives in
    test_filter_publication_api.py; upstream choice tuples are not repeated here.
    """

    class TitlesIssueFilter(FilterSet):
        any_title = AllValuesFilter(field_name="title")

        class Meta:
            model = library_models.Issue
            fields = {"number": ["exact"]}

    class TitlesPeriodicalFilter(FilterSet):
        issues = RelatedFilter(TitlesIssueFilter, field_name="issues")

        class Meta:
            model = library_models.Periodical
            fields = {"name": ["exact"]}

    TitlesPeriodicalFilter.get_filters()
    assert "issues__any_title" in _snapshot(TitlesPeriodicalFilter).deferred_copies
    instance = _pipeline_instance(
        TitlesPeriodicalFilter,
        data={"name": "Review"},
        queryset=library_models.Periodical.objects.all(),
    )

    copy_ = (
        instance._filter_named("issues__any_title")
        if read == "by-name"
        else instance.filters["issues__any_title"]
    )

    assert vars(copy_)["model"] is library_models.Periodical


def test_filterset_get_fields_includes_pk_for_all_fields_shorthand() -> None:
    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = "__all__"
            # ``Item.attachment`` is a ``FileField`` (spec-038) that
            # ``django-filter`` has no default filter for; the ``"__all__"``
            # sweep would otherwise raise on it. Excluding it keeps this test
            # focused on its intent: the shorthand adds the PK column.
            exclude = ("attachment",)

    fields = ItemFilter.get_fields()
    pk_name = Item._meta.pk.name
    assert pk_name in fields


def test_filterset_get_fields_excludes_m2m_for_all_fields_shorthand() -> None:
    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = "__all__"

    fields = BookFilter.get_fields()
    # `Book.genres` is an M2M relation; it must be excluded.
    assert "genres" not in fields


class _TagManager(django_models.ForeignObject[object, object]):
    """A many-to-many field that is no ``ManyToManyField``, as taggit's ``TaggableManager`` is.

    It joins the model the way taggit's does: ``Options.add_field`` files it under
    ``Options.many_to_many``, the list django-filter's whole-set sweep reads. It is a
    ``ForeignObject`` (taggit's is a ``RelatedField``) only because django-stubs types a
    relation's ``field`` as one.
    """

    many_to_many = True
    many_to_one = False
    one_to_many = False
    one_to_one = False

    def __init__(self, to: type[django_models.Model]) -> None:
        super().__init__(
            to,
            on_delete=django_models.CASCADE,
            from_fields=[],
            to_fields=[],
            rel=django_models.ForeignObjectRel(self, to, related_name="+"),
        )

    @override
    def contribute_to_class(
        self,
        cls: type[django_models.Model],
        name: str,
        private_only: bool = False,
        **kwargs: object,
    ) -> None:
        self.set_attributes_from_name(name)
        self.model = cls
        cls._meta.add_field(self)
        setattr(cls, name, self)


@isolate_apps("apps.library")
def test_filterset_get_fields_excludes_an_m2m_field_outside_many_to_many_field() -> None:
    """``fields = "__all__"`` drops every many-to-many field upstream's sweep added.

    The sweep removes the names in ``Options.many_to_many``, so a third-party M2M field
    that does not subclass ``ManyToManyField`` leaves the swept keys like the built-in one,
    and building the filters no longer refuses it as a path that is no traversable relation.
    """

    class _Tagged(django_models.Model):
        name: django_models.TextField[str | Combinable, str] = django_models.TextField()
        tags = _TagManager(library_models.Genre)

        class Meta:
            app_label = "library"

    class TaggedFilter(FilterSet):
        class Meta:
            model = _Tagged
            fields = "__all__"

    assert list(TaggedFilter.get_fields()) == ["name", "id"]
    assert set(TaggedFilter.get_filters()) == {"name", "id"}


class _SweepModel(NamedTuple):
    """One model the whole-set sweep runs over, and the filter keys ``fields = "__all__"`` yields."""

    model: type[django_models.Model]
    keys: frozenset[str]
    pk: str
    column: str
    m2m: str | None
    other_column: str


_SWEEP_MODELS: dict[str, _SweepModel] = {
    # ``archive_genres`` is an ``editable=False`` many-to-many beside the editable ``genres``.
    "auto-pk-with-m2m": _SweepModel(
        library_models.Book,
        frozenset(
            {
                "id",
                "title",
                "subtitle",
                "circulation_status",
                "shelf",
            },
        ),
        "id",
        "title",
        "archive_genres",
        "subtitle",
    ),
    "auto-pk-with-two-m2m": _SweepModel(
        library_models.Printing,
        frozenset(
            {
                "id",
                "edition",
                "publisher_2",
                "licensor",
                "series",
                "run_size",
            },
        ),
        "id",
        "run_size",
        "co_publishers",
        "edition",
    ),
    "non-auto-pk": _SweepModel(
        library_models.Edition,
        frozenset(
            {
                "isbn_13",
                "isbn_10",
                "imprint",
                "publisher",
                "publisher_2",
            },
        ),
        "isbn_13",
        "imprint",
        None,
        "isbn_10",
    ),
    "mti-child": _SweepModel(
        library_models.LendingDesk,
        frozenset(
            {
                "venue_ptr",
                "name",
                "opened_on",
                "window_count",
                "lead_ticket",
            },
        ),
        "venue_ptr",
        "name",
        None,
        "window_count",
    ),
    "no-m2m": _SweepModel(
        library_models.Branch,
        frozenset(
            {
                "id",
                "name",
                "city",
                "isil",
            },
        ),
        "id",
        "city",
        None,
        "name",
    ),
}


def _sweep_exclude(spec: _SweepModel, excluded: str) -> list[str]:
    """Return the ``Meta.exclude`` list one grid row declares."""
    if excluded == "nothing":
        return []
    if excluded == "column":
        return [spec.column]
    if excluded == "pk":
        return [spec.pk]
    assert spec.m2m is not None
    return [spec.m2m]


_SWEEP_GRID = [
    pytest.param(model_key, excluded, id=f"{model_key}-exclude-{excluded}")
    for model_key, spec in _SWEEP_MODELS.items()
    for excluded in (
        "nothing",
        "column",
        "pk",
        "m2m",
    )
    if excluded != "m2m" or spec.m2m is not None
]


@pytest.mark.parametrize(("model_key", "excluded"), _SWEEP_GRID)
@pytest.mark.parametrize(
    "fields",
    [pytest.param(None, id="exclude-only"), pytest.param("__all__", id="all-fields")],
)
def test_filterset_whole_set_sweep_publishes_the_same_keys_for_both_spellings(
    fields: str | None,
    model_key: str,
    excluded: str,
) -> None:
    """``Meta.exclude`` alone and ``fields = "__all__"`` with it publish one key set.

    The sweep adds the primary key (an MTI child's parent link included) unless
    ``Meta.exclude`` names it, never keeps a many-to-many, and drops every excluded name.
    """
    spec = _SWEEP_MODELS[model_key]
    exclude = _sweep_exclude(spec, excluded)
    meta: dict[str, object] = {"model": spec.model, "exclude": exclude}
    if fields is not None:
        meta["fields"] = fields
    probe = type("SweepProbe", (FilterSet,), {"Meta": type("Meta", (), meta)})

    expected = spec.keys - set(exclude)
    assert set(probe.get_fields()) == expected
    assert set(probe.base_filters) == expected


@pytest.mark.parametrize("excluded", ["pk-alias", "unknown-name"])
@pytest.mark.parametrize("model_key", list(_SWEEP_MODELS))
@pytest.mark.parametrize(
    "fields",
    [pytest.param(None, id="exclude-only"), pytest.param("__all__", id="all-fields")],
)
def test_filterset_whole_set_sweep_refuses_an_exclude_name_no_field_carries(
    fields: str | None,
    model_key: str,
    excluded: str,
) -> None:
    """An exclude naming no model field is refused at class creation, naming the set.

    A typo would exclude nothing and leave the column it meant filterable; ``"pk"`` is
    not an alias of the primary key's name, so it is no field either.
    """
    spec = _SWEEP_MODELS[model_key]
    name = "pk" if excluded == "pk-alias" else "no_such_field"
    meta: dict[str, object] = {"model": spec.model, "exclude": [name]}
    if fields is not None:
        meta["fields"] = fields

    with pytest.raises(ConfigurationError) as excinfo:
        type("SweepProbe", (FilterSet,), {"Meta": type("Meta", (), meta)})
    message = str(excinfo.value)
    assert message.startswith(
        f"FilterSet SweepProbe.Meta.exclude names unknown fields: [{name!r}]. Available: [",
    )
    assert message.endswith(
        f"Exclude only a field of {spec.model.__name__} or a Meta.fields entry.",
    )


@pytest.mark.parametrize("model_key", list(_SWEEP_MODELS))
def test_filterset_explicit_field_list_with_exclude_is_not_swept(model_key: str) -> None:
    """A field list beside ``Meta.exclude`` publishes exactly the listed names it keeps.

    A listed many-to-many stays, no primary key is added, and the excluded name drops out.
    """
    spec = _SWEEP_MODELS[model_key]
    listed = [spec.column, spec.other_column] + ([spec.m2m] if spec.m2m is not None else [])
    meta = {"model": spec.model, "fields": listed, "exclude": [spec.other_column]}
    probe = type("ListProbe", (FilterSet,), {"Meta": type("Meta", (), meta)})

    expected = {spec.column} if spec.m2m is None else {spec.column, spec.m2m}
    assert set(probe.get_fields()) == expected


@pytest.mark.parametrize("model_key", list(_SWEEP_MODELS))
def test_filterset_explicit_field_list_excluding_its_pk_answers_as_django_filter(
    model_key: str,
) -> None:
    """A field list naming the primary key and excluding it publishes the rest, as upstream does."""
    spec = _SWEEP_MODELS[model_key]
    meta = {"model": spec.model, "fields": [spec.pk, spec.column], "exclude": [spec.pk]}
    probe = type("ListProbe", (FilterSet,), {"Meta": type("Meta", (), meta)})

    assert set(probe.get_fields()) == {spec.column}


def test_filterset_dict_fields_with_exclude_is_not_swept() -> None:
    """A dict ``Meta.fields`` beside ``Meta.exclude`` publishes its kept keys and no primary key."""

    class DictProbe(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"], "subtitle": ["exact"]}
            exclude = ("subtitle",)

    assert dict(DictProbe.get_fields()) == {"title": ["exact"]}


@pytest.mark.parametrize(
    "exclude",
    [
        pytest.param((), id="exclude-nothing"),
        pytest.param(("subtitle",), id="exclude-column"),
        pytest.param(("id",), id="exclude-pk"),
    ],
)
@pytest.mark.parametrize(
    "fields",
    [pytest.param(None, id="exclude-only"), pytest.param("__all__", id="all-fields")],
)
def test_filterset_whole_set_sweep_under_a_relay_owner_keeps_the_pk_global_id(
    fields: str | None,
    exclude: tuple[str, ...],
) -> None:
    """Under a Relay owner the swept primary key is the GlobalID filter, unless excluded."""

    class RelayBookType(DjangoType):
        class Meta:
            model = library_models.Book
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(RelayBookType, RelayBookType.__django_strawberry_definition__)
    meta: dict[str, object] = {"model": library_models.Book, "exclude": exclude}
    if fields is not None:
        meta["fields"] = fields
    probe = type("RelaySweepProbe", (FilterSet,), {"Meta": type("Meta", (), meta)})
    probe._owner_definition = RelayBookType.__django_strawberry_definition__

    generated = probe.get_filters()

    expected = {
        "id",
        "title",
        "subtitle",
        "circulation_status",
        "shelf",
    } - set(exclude)
    assert set(generated) == expected
    if "id" in expected:
        assert type(generated["id"]) is GlobalIDFilter


@pytest.mark.parametrize(
    "fields",
    [pytest.param(None, id="exclude-only"), pytest.param("__all__", id="all-fields")],
)
def test_related_filter_flattens_a_whole_set_sweep_target_alike_for_both_spellings(
    fields: str | None,
) -> None:
    """A ``RelatedFilter`` into an exclude-only set flattens the ``"__all__"`` keys.

    The target's swept primary key becomes a flat ``books__id`` key and no many-to-many
    leaf reaches the parent.
    """
    meta: dict[str, object] = {"model": library_models.Book, "exclude": ("subtitle",)}
    if fields is not None:
        meta["fields"] = fields
    child = type("SweptBookFilter", (FilterSet,), {"Meta": type("Meta", (), meta)})

    class SweptShelfFilter(FilterSet):
        books = RelatedFilter(child, field_name="books")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    assert set(SweptShelfFilter.get_filters()) == {
        "code",
        "books",
        "books__id",
        "books__title",
        "books__circulation_status",
        "books__shelf",
    }


def test_filterset_get_fields_does_not_alter_explicit_dict_meta() -> None:
    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"name": ["exact"]}

    fields = ItemFilter.get_fields()
    # Explicit dict is returned by `super().get_fields()` unchanged.
    assert set(fields.keys()) == {"name"}


def test_filterset_get_fields_rejects_one_shot_iterator_at_class_creation() -> None:
    """``Meta.fields`` as a one-shot iterator fails closed at class creation.

    ``FilterSetOptions`` stores the declaration verbatim and upstream
    ``get_fields`` consumes it into a fresh ``OrderedDict`` per call, so a
    generator expands correctly ONCE and then silently re-expands to an EMPTY
    field map on every later pass -- exactly the divergence the
    lazy-``RelatedFilter`` re-expansion exists to serve
    (``should_cache_expansion`` refuses the first cache write while a string
    target is unresolved). The gate fires BEFORE the first consumption, so the
    declaration is rejected at the metaclass instead of diverging at
    finalization time. Mirrors the order family's ``_expand_meta_fields`` gate.
    """
    with pytest.raises(ConfigurationError) as excinfo:

        @definition_raises
        class ShelfFilter(FilterSet):
            class Meta:
                model = library_models.Shelf
                fields = (f for f in ["code"])

    message = str(excinfo.value)
    assert "ShelfFilter" in message
    assert "Meta.fields" in message
    # The message names what was RECEIVED and enumerates what IS accepted, so
    # it never describes a wider contract than the gate enforces.
    assert "generator" in message
    assert "'__all__', a lookup-bag dict, or a re-readable collection of field names" in message
    assert "dict keys/values" in message
    assert "not a one-shot iterator or generator" in message


@pytest.mark.parametrize("escape", [RuntimeError, KeyboardInterrupt])
def test_filterset_get_fields_rejects_a_declaration_whose_class_read_raises(
    escape: type[BaseException],
) -> None:
    """``Meta.fields`` whose ``__class__`` raises is rejected at class creation, typed.

    The shape gate runs before upstream consumes the declaration; the ``str`` exemption in
    front of it must not read the value's ``__class__`` unguarded, or the value's own
    exception replaces the typed rejection.
    """
    meta = type("Meta", (), {"model": library_models.Shelf, "fields": ClassReadRaises(escape)})

    with pytest.raises(ConfigurationError) as excinfo:
        type("HostileFieldsFilter", (FilterSet,), {"Meta": meta})
    assert str(excinfo.value) == (
        "FilterSet HostileFieldsFilter.Meta.fields must be '__all__', a lookup-bag dict, "
        "or a re-readable collection of field names; got ClassReadRaises (<ClassReadRaises>). "
        "Accepted: a re-readable collection of field names -- list, tuple, set, frozenset, "
        "dict keys/values, or another sized collection; not a one-shot iterator or generator, "
        "and not a bare string."
    )


def test_filterset_get_fields_rejects_builtin_iterator_too() -> None:
    with pytest.raises(ConfigurationError):

        @definition_raises
        class ShelfFilter(FilterSet):
            class Meta:
                model = library_models.Shelf
                fields = iter(["code"])


def test_filterset_fields_alias_carried_generator_hits_the_gate() -> None:
    """An alias-carried one-shot ``filter_fields`` iterator hits the re-readability gate.

    ``filter_fields`` promotes onto ``Meta.fields`` at the metaclass, so the alias
    carries the same one-shot iterator the gate refuses.
    """
    with pytest.raises(ConfigurationError):

        @definition_raises
        class ShelfFilter(FilterSet):
            class Meta:
                model = library_models.Shelf
                filter_fields = (f for f in ["code"])


@pytest.mark.parametrize("declared_fields", ["__all__", ["title"], {"title": ["exact"]}])
def test_filterset_rejects_an_abstract_model_at_class_build(declared_fields: object) -> None:
    """An abstract ``Meta.model`` fails at the class statement, naming the model.

    django-filter resolves every generated lookup through the model's default
    manager, which an abstract model does not have, so each ``Meta.fields`` shape
    would otherwise die in ``resolve_field`` with an ``AttributeError`` on ``None``.
    """
    with pytest.raises(ConfigurationError, match=r"Meta.model TitledEntry is an abstract model"):

        @definition_raises
        class TitledEntryFilter(FilterSet):
            class Meta:
                model = library_models.TitledEntry
                fields = declared_fields


@pytest.mark.parametrize(
    ("meta", "expected"),
    [
        pytest.param({"fields": ["code"]}, {"code"}, id="list"),
        pytest.param({"fields": ("code",)}, {"code"}, id="tuple"),
        pytest.param({"fields": {"code"}}, {"code"}, id="set"),
        pytest.param({"fields": frozenset({"code"})}, {"code"}, id="frozenset"),
        pytest.param({"fields": {"code": ["exact"]}}, {"code"}, id="mapping"),
        pytest.param({"fields": "__all__"}, None, id="all"),
        pytest.param(
            {"exclude": ["code"]},
            {
                "code_length",
                "topic",
                "topic_length",
                "condition",
                "tier",
                "branch",
                "id",
            },
            id="exclude-only",
        ),
    ],
)
def test_filterset_get_fields_re_readables_still_expand(
    meta: dict[str, object],
    expected: set[str] | None,
) -> None:
    """Each supported re-readable field declaration expands consistently on repeated reads."""
    probe = type(
        "ReadableShelfFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": library_models.Shelf, **meta})},
    )
    first = probe.get_fields()
    assert probe.get_fields() == first
    if expected is None:
        assert "code" in first
    else:
        assert set(first) == expected


@pytest.mark.parametrize(
    "shape",
    ["keys-view", "custom-collection"],
    ids=["keys-view", "custom-collection"],
)
def test_filterset_accepts_a_computed_re_readable_collection(shape: str) -> None:
    """A ``dict`` view or a custom ``Collection`` is a legal declaration.

    The contract is re-readability, not membership of a builtin allow-list: a
    consumer computing ``Meta.fields`` from a mapping's keys or from a project
    container holds the field names just as a list does, so the expansion
    re-runs to the same result and the declaration must be accepted.
    """

    class _NameSet:
        def __init__(self, *names: str) -> None:
            super().__init__()
            self._names = names

        def __iter__(self) -> Iterator[str]:
            return iter(self._names)

        def __len__(self) -> int:
            return len(self._names)

        def __contains__(self, item: object) -> bool:
            return item in self._names

    fields = {"code": ["exact"]}.keys() if shape == "keys-view" else _NameSet("code")
    probe = type(
        "ComputedShelfFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": library_models.Shelf, "fields": fields})},
    )
    assert set(probe.get_fields()) == {"code"}
    assert set(probe.get_fields()) == {"code"}


def _category_filter_with_exclude(exclude: Callable[[], object]) -> type[FilterSet]:
    """Build a ``Category`` FilterSet whose only declaration is ``Meta.exclude``."""
    meta = type("Meta", (), {"model": Category, "exclude": exclude()})
    return type("ExcludeProbeFilter", (FilterSet,), {"Meta": meta})


@pytest.mark.parametrize(
    ("exclude", "received"),
    [
        pytest.param(lambda: (n for n in ["is_private"]), "generator", id="generator"),
        pytest.param(lambda: iter(["is_private"]), "list_iterator", id="iter"),
        pytest.param(lambda: map(str, ["is_private"]), "map", id="map"),
        pytest.param(lambda: "is_private", "str", id="bare-str"),
        pytest.param(lambda: gettext_lazy("is_private"), "__proxy__", id="lazy-str"),
        pytest.param(lambda: gettext_lazy("is_priv"), "__proxy__", id="lazy-str-substring"),
    ],
)
def test_filterset_rejects_a_meta_exclude_that_cannot_be_re_read(
    exclude: Callable[[], object],
    received: str,
) -> None:
    """A one-shot or bare-string ``Meta.exclude`` fails closed at class creation.

    Upstream ``get_fields`` keeps a field when ``f not in exclude``: a one-shot
    exclude is exhausted by the first membership test, so every later field
    (the excluded column included) would become a client-queryable filter, and
    a bare string answers by substring. Both are refused before upstream reads
    the declaration, naming ``Meta.exclude``. A lazy translation string is a
    bare string whose proxy class is no ``str``: it would drop ``is_private``
    as the name it spells and exclude nothing as a substring of one, so it is
    refused as the plain string is.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        _category_filter_with_exclude(exclude)

    message = str(excinfo.value)
    assert message.startswith(
        "FilterSet ExcludeProbeFilter.Meta.exclude must be a re-readable collection of "
        f"field names; got {received} (",
    )
    assert message.endswith("not a one-shot iterator or generator, and not a bare string.")


@pytest.mark.parametrize(
    "exclude",
    [
        pytest.param(["is_private"], id="list"),
        pytest.param(("is_private",), id="tuple"),
        pytest.param({"is_private"}, id="set"),
        pytest.param(frozenset({"is_private"}), id="frozenset"),
        pytest.param({"is_private": None}.keys(), id="dict-keys"),
        pytest.param({"field": "is_private"}.values(), id="dict-values"),
        pytest.param(SimpleLazyObject(lambda: ["is_private"]), id="lazy-list"),
    ],
)
def test_filterset_meta_exclude_re_readable_collection_drops_the_column(exclude: object) -> None:
    """Every re-readable ``Meta.exclude`` keeps the excluded column out of ``base_filters``."""
    probe = _category_filter_with_exclude(lambda: exclude)

    assert "is_private" not in probe.base_filters
    assert "name" in probe.base_filters
    # A second expansion reads the same declaration to the same field map.
    assert "is_private" not in probe.get_fields()


def test_filterset_meta_fields_lazy_translation_string_reads_as_the_plain_string() -> None:
    """A lazy translation ``Meta.fields`` takes the text exemption the plain string takes.

    ``"__all__"`` spelled lazily is the whole-set sweep, and any other lazy string
    reaches django-filter's own ``TypeError`` for a bare-string ``Meta.fields``,
    exactly as the plain string it stands for does.
    """
    swept = _category_filter_with_meta(fields=gettext_lazy("__all__"))
    plain = _category_filter_with_meta(fields="__all__")
    assert set(swept.base_filters) == set(plain.base_filters)

    with pytest.raises(TypeError) as lazy_error:
        _category_filter_with_meta(fields=gettext_lazy("name"))
    with pytest.raises(TypeError) as plain_error:
        _category_filter_with_meta(fields="name")
    assert str(lazy_error.value) == str(plain_error.value)


def test_filterset_meta_exclude_accepts_a_listed_path() -> None:
    """A ``Meta.fields`` path is a legal ``Meta.exclude`` name though it is no model field.

    Upstream excludes a listed path before it resolves it, so the exclude removes it.
    """
    probe = type(
        "ExcludeNamesFilter",
        (FilterSet,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": Category, "fields": ["name", "items__name"], "exclude": ["items__name"]},
            ),
        },
    )

    assert set(probe.get_fields()) == {"name"}
    assert set(probe.base_filters) == {"name"}


def _declared_exclude_parent() -> type[FilterSet]:
    """Return a ``Category`` set declaring a filter and a ``RelatedFilter`` for a child to inherit."""
    item_filter = type(
        "ItemExcludeProbeFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": Item, "fields": ["name"]})},
    )
    return type(
        "DeclaredParentFilter",
        (FilterSet,),
        {
            "search": CharFilter(field_name="name"),
            "items": RelatedFilter(item_filter, field_name="items"),
            "Meta": type("Meta", (), {"model": Category, "fields": ["name"]}),
        },
    )


@pytest.mark.parametrize(
    "shape",
    [
        "own filter",
        "own filter over a model field",
        "inherited filter",
        "inherited related filter",
    ],
)
def test_filterset_meta_exclude_refuses_a_declared_name(shape: str) -> None:
    """An exclude naming a declared filter fails at class creation, naming the remedy.

    django-filter publishes every declared filter whatever ``Meta.exclude`` says, so the
    exclude would remove nothing and leave the filter it meant published; a declaration
    over a model field's own name is no exception. The remedy is DRF's: remove the
    declaration, or disable an inherited one with ``name = None``.
    """
    base: type[FilterSet] = FilterSet
    attrs: dict[str, object] = {}
    meta: dict[str, object] = {"model": Category, "fields": ["name"]}
    if shape == "own filter":
        attrs["search"] = CharFilter(field_name="name")
        name = "search"
    elif shape == "own filter over a model field":
        attrs["name"] = CharFilter(field_name="name", lookup_expr="icontains")
        meta["fields"] = "__all__"
        name = "name"
    else:
        base = _declared_exclude_parent()
        name = "search" if shape == "inherited filter" else "items"
    meta["exclude"] = [name]

    with pytest.raises(ConfigurationError) as excinfo:
        type("DeclaredExcludeFilter", (base,), {**attrs, "Meta": type("Meta", (), meta)})
    assert str(excinfo.value) == (
        f"FilterSet DeclaredExcludeFilter.Meta.exclude names declared filters: [{name!r}]. "
        "An exclude never removes a declaration: remove it, or disable an inherited one with "
        f"`{name} = None` in the class body."
    )


def test_filterset_meta_exclude_accepts_the_field_name_of_a_tombstoned_declaration() -> None:
    """A declaration disabled with ``name = None`` is no declaration, so its field excludes."""
    parent = type(
        "OverrideParentFilter",
        (FilterSet,),
        {
            "name": CharFilter(field_name="name", lookup_expr="icontains"),
            "Meta": type("Meta", (), {"model": Category, "fields": ["name", "description"]}),
        },
    )
    child = type(
        "TombstoneChildFilter",
        (parent,),
        {
            "name": None,
            "Meta": type(
                "Meta",
                (),
                {"model": Category, "fields": ["name", "description"], "exclude": ["name"]},
            ),
        },
    )

    assert set(child.base_filters) == {"description"}


_NON_STRING_ENTRIES = [
    pytest.param(None, "NoneType (None)", id="none"),
    pytest.param(b"name", "bytes (b'name')", id="bytes"),
    pytest.param(7, "int (7)", id="int"),
    pytest.param(("name",), "tuple (('name',))", id="tuple"),
]


def _non_string_entry_meta(shape: str, entry: object) -> dict[str, object]:
    """Return the ``Meta`` declarations one non-string-entry row builds around ``entry``."""
    if shape == "exclude":
        return {"exclude": [entry]}
    if shape == "all-exclude":
        return {"fields": "__all__", "exclude": ["name", entry]}
    if shape == "fields-list":
        return {"fields": ["name", entry]}
    return {"fields": {"name": ["exact"], entry: ["exact"]}}


@pytest.mark.parametrize(("entry", "received"), _NON_STRING_ENTRIES)
@pytest.mark.parametrize(
    "shape",
    [
        "exclude",
        "all-exclude",
        "fields-list",
        "fields-dict",
    ],
)
def test_filterset_meta_refuses_a_non_string_field_name_entry(
    shape: str,
    entry: object,
    received: str,
) -> None:
    """A ``Meta.fields`` / ``Meta.exclude`` entry that is no string fails closed by name.

    In an exclude it would match no field (a silent no-op); in a field list it would reach
    upstream as a raw ``AttributeError`` / ``TypeError``. The gate is the order family's.
    """
    declared = _non_string_entry_meta(shape, entry)
    attr = "exclude" if "exclude" in declared else "fields"

    with pytest.raises(ConfigurationError) as excinfo:
        _category_filter_with_meta(**declared)
    assert str(excinfo.value) == (
        f"FilterSet MetaProbeFilter.Meta.{attr} entries must be field-name strings; "
        f"got {received}."
    )


_MALFORMED_LOOKUP_VALUE_PREFIX = "FilterSet MetaProbeFilter.Meta.fields['name']"


_NOT_A_LOOKUP_BAG = " must be '__all__' or a re-readable collection of lookup-name strings; got "


_NOT_A_LOOKUP_NAME = " entries must be lookup-name strings; got "


@pytest.mark.parametrize(
    ("lookups", "message"),
    [
        pytest.param([1], f"{_NOT_A_LOOKUP_NAME}int (1).", id="int-member"),
        pytest.param([None], f"{_NOT_A_LOOKUP_NAME}NoneType (None).", id="none-member"),
        pytest.param([b"exact"], f"{_NOT_A_LOOKUP_NAME}bytes (b'exact').", id="bytes-member"),
        pytest.param([["exact"]], f"{_NOT_A_LOOKUP_NAME}list (['exact']).", id="list-member"),
        pytest.param(None, f"{_NOT_A_LOOKUP_BAG}NoneType (None).", id="none"),
        pytest.param("exact", f"{_NOT_A_LOOKUP_BAG}str ('exact').", id="bare-str"),
        pytest.param(
            gettext_lazy("exact"),
            f"{_NOT_A_LOOKUP_BAG}__proxy__ ('exact').",
            id="bare-lazy",
        ),
        pytest.param(
            [gettext_lazy("exact")],
            f"{_NOT_A_LOOKUP_NAME}__proxy__ ('exact').",
            id="lazy-member",
        ),
        # A one-shot value's repr carries its address, so only its kind is pinned.
        pytest.param(
            (lookup for lookup in ["exact"]),
            f"{_NOT_A_LOOKUP_BAG}generator (",
            id="generator",
        ),
        pytest.param(iter(["exact"]), f"{_NOT_A_LOOKUP_BAG}list_iterator (", id="iterator"),
    ],
)
def test_filterset_meta_refuses_a_malformed_lookup_value(lookups: object, message: str) -> None:
    """A lookup-bag value that is no ``"__all__"`` or lookup-name collection fails closed by name.

    django-filter walks the value as the field's lookups: a bare string letter by letter
    (``"exact"`` becomes the unsupported lookup ``"e"``), a non-string member into a raw
    ``TypeError``, and a one-shot iterator once, publishing no filters on every later
    expansion.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        _category_filter_with_meta(fields={"name": lookups})
    expected = _MALFORMED_LOOKUP_VALUE_PREFIX + message
    if message.endswith("."):
        assert str(excinfo.value) == expected
    else:
        assert str(excinfo.value).startswith(expected)


def test_filterset_meta_admits_a_lazy_all_lookup_value() -> None:
    """A lazy translation string spelling ``"__all__"`` is the per-field shorthand it spells."""
    lazy_filter = _category_filter_with_meta(fields={"name": gettext_lazy("__all__")})
    plain_filter = _category_filter_with_meta(fields={"name": "__all__"})
    assert list(lazy_filter.get_filters()) == list(plain_filter.get_filters())
    assert "name" in lazy_filter.get_filters()


_META_KEY_REFUSALS: dict[str, tuple[object, str]] = {
    "unknown key": (
        type("Meta", (), {"model": Category, "fields": ["name"], "bogus": True}),
        "FilterSet MetaKeyFilter.Meta has unknown keys: ['bogus'].",
    ),
    "misspelt fields": (
        type("Meta", (), {"model": Category, "fields": ["name"], "fiels": ["name"]}),
        "FilterSet MetaKeyFilter.Meta has unknown keys: ['fiels'].",
    ),
    "key the package does not apply": (
        type("Meta", (), {"model": Category, "fields": ["name"], "search_fields": ["name"]}),
        "FilterSet MetaKeyFilter.Meta has unknown keys: ['search_fields'].",
    ),
    "non-class Meta": (
        SimpleNamespace(model=Category, fields=["name"]),
        "FilterSet MetaKeyFilter.Meta must be a class; got namespace(",
    ),
}


@pytest.mark.parametrize("shape", list(_META_KEY_REFUSALS))
def test_filterset_meta_refuses_an_unknown_key_at_class_creation(shape: str) -> None:
    """An own ``Meta`` declaring a key a filterset does not read fails at class creation.

    django-filter ignores a key its options object does not store, so a typo would
    narrow nothing. The guard is the one every write flavor runs.
    """
    meta, message = _META_KEY_REFUSALS[shape]

    with pytest.raises(ConfigurationError) as excinfo:
        type("MetaKeyFilter", (FilterSet,), {"Meta": meta})
    assert str(excinfo.value).startswith(message)


def test_filterset_meta_accepts_every_key_django_filter_reads_and_the_fields_synonym() -> None:
    """Every ``FilterSetOptions`` key and ``filter_fields`` build; the audited set is pinned.

    The allowed set is asked of upstream's options object; the literal below is the set
    audited across the supported django-filter range, so a key upstream adds fails here
    until it is audited.
    """
    assert {
        "model",
        "fields",
        "exclude",
        "filter_overrides",
        "form",
        "unknown_field_behavior",
        "filter_fields",
    } == sets_module._ALLOWED_FILTERSET_META_KEYS

    probe = type(
        "EveryKeyFilter",
        (FilterSet,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": Category,
                    "filter_fields": ["name"],
                    "exclude": ["description"],
                    "filter_overrides": {},
                    "form": forms.Form,
                    "unknown_field_behavior": UnknownFieldBehavior.RAISE,
                },
            ),
        },
    )

    assert set(probe.base_filters) == {"name"}


@pytest.mark.parametrize(
    ("meta", "declaration"),
    [
        pytest.param({"fields": "__all__"}, "Meta.fields = '__all__'", id="all-fields"),
        pytest.param(
            {"exclude": ["name"]},
            "Meta.exclude without Meta.fields (the '__all__' sweep minus exclude)",
            id="exclude-only",
        ),
        pytest.param(
            {"exclude": []},
            "Meta.exclude without Meta.fields (the '__all__' sweep minus exclude)",
            id="empty-exclude",
        ),
    ],
)
@pytest.mark.parametrize("related", [False, True], ids=["plain", "with-related-filter"])
def test_filterset_model_less_sweep_is_refused_by_name_and_a_subclass_supplies_the_model(
    meta: dict[str, object],
    declaration: str,
    *,
    related: bool,
) -> None:
    """A model-less sweep raises ``ConfigurationError`` naming the set, never upstream's crash.

    The refusal runs where the sweep is expanded, so the model-less base still builds and
    a subclass whose ``Meta`` adds ``Meta.model`` sweeps that model.
    """
    attrs: dict[str, object] = {"Meta": type("Meta", (), meta)}
    if related:
        item_filter = type(
            "ItemProbeFilter",
            (FilterSet,),
            {"Meta": type("Meta", (), {"model": Item, "fields": ["name"]})},
        )
        attrs["items"] = RelatedFilter(item_filter, field_name="items")
    base = type("ModelLessSweepFilter", (FilterSet,), attrs)

    with pytest.raises(ConfigurationError) as excinfo:
        base.get_fields()
    assert str(excinfo.value) == (
        f"ModelLessSweepFilter.{declaration} requires Meta.model so the filter field names "
        "can be derived from model._meta.get_fields()."
    )

    base_meta = truth.static_attr(base, "Meta")
    assert truth.is_type(base_meta)
    child = type(
        "ModelSweepFilter",
        (base,),
        {"Meta": type("Meta", (base_meta,), {"model": Category})},
    )
    fields = child.get_fields()
    assert "id" in fields
    assert ("name" in fields) is (meta.get("exclude") != ["name"])


def _category_filter_with_meta(**meta: object) -> type[FilterSet]:
    """Build a ``Category`` FilterSet over the given ``Meta`` declarations."""
    return type(
        "MetaProbeFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": Category, **meta})},
    )


_Namer: TypeAlias = Callable[[str], str]


class _StrSubclassMetaShape(NamedTuple):
    """One ``Meta`` spelling a ``str``-subclass name and the filter it must generate and apply."""

    meta: Callable[[_Namer], dict[str, object]]
    applied: str  # the generated filter the row applies
    lookup: str  # its operator-bag key in the filter input
    absent: str | None = None  # a model field the declaration must NOT generate


def _meta_list(n: _Namer) -> dict[str, object]:
    return {"fields": [n("name")]}


def _meta_tuple(n: _Namer) -> dict[str, object]:
    return {"fields": (n("name"),)}


def _meta_set(n: _Namer) -> dict[str, object]:
    return {"fields": {n("name")}}


def _meta_dict_key(n: _Namer) -> dict[str, object]:
    return {"fields": {n("name"): ["exact", "icontains"]}}


def _meta_dict_lookup(n: _Namer) -> dict[str, object]:
    return {"fields": {"name": [n("icontains")]}}


def _meta_dict_all(n: _Namer) -> dict[str, object]:
    return {"fields": {"name": n("__all__")}}


def _meta_alias(n: _Namer) -> dict[str, object]:
    return {"filter_fields": [n("name")]}


def _meta_all(n: _Namer) -> dict[str, object]:
    return {"fields": n("__all__")}


def _meta_exclude(n: _Namer) -> dict[str, object]:
    return {"fields": "__all__", "exclude": [n("name")]}


def _meta_exclude_view(n: _Namer) -> dict[str, object]:
    return {"fields": "__all__", "exclude": {n("name"): None}.keys()}


_STR_SUBCLASS_FILTER_SHAPES: dict[str, _StrSubclassMetaShape] = {
    "list": _StrSubclassMetaShape(_meta_list, "name", "exact"),
    "tuple": _StrSubclassMetaShape(_meta_tuple, "name", "exact"),
    "set": _StrSubclassMetaShape(_meta_set, "name", "exact"),
    "dict key": _StrSubclassMetaShape(_meta_dict_key, "name__icontains", "i_contains"),
    "dict lookup value": _StrSubclassMetaShape(_meta_dict_lookup, "name__icontains", "i_contains"),
    "dict per-field __all__": _StrSubclassMetaShape(
        _meta_dict_all,
        "name__icontains",
        "i_contains",
    ),
    "filter_fields alias": _StrSubclassMetaShape(_meta_alias, "name", "exact"),
    "top-level __all__": _StrSubclassMetaShape(_meta_all, "name", "exact"),
    "exclude": _StrSubclassMetaShape(_meta_exclude, "description", "exact", absent="name"),
    "exclude dict view": _StrSubclassMetaShape(
        _meta_exclude_view,
        "description",
        "exact",
        absent="name",
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("kind", STR_SUBCLASS_KINDS)
@pytest.mark.parametrize("shape", list(_STR_SUBCLASS_FILTER_SHAPES))
def test_filterset_meta_names_a_field_through_a_str_subclass_by_its_text(
    shape: str,
    kind: str,
) -> None:
    """A ``str``-subclass name in ``Meta.fields`` / ``filter_fields`` / ``Meta.exclude`` is its text.

    Every generated filter is keyed by plain ``str`` and carries a plain ``str``
    ``field_name`` / ``lookup_expr``, the filter applies to the rows its text
    names, an excluded name is excluded, and no dunder of the subclass runs.
    """
    services.seed_data(1)
    category = Category.objects.order_by("pk").first()
    assert category is not None
    spec = _STR_SUBCLASS_FILTER_SHAPES[shape]
    calls: list[str] = []
    meta = type(
        "Meta",
        (),
        {"model": Category, **spec.meta(lambda text: str_subclass_name(kind, text, calls))},
    )
    calls.clear()

    probe = type("StrSubclassProbe", (FilterSet,), {"Meta": meta, "__module__": __name__})
    filters = probe.get_filters()
    assert issubclass(probe, FilterSet)
    value = category.description if spec.applied == "description" else category.name
    head = spec.applied.split("__", maxsplit=1)[0]
    rows = probe.apply_sync({head: {spec.lookup: value}}, Category.objects.all(), _make_info())

    assert calls == []
    assert all(type(name) is str for name in filters)
    generated = [fltr for fltr in filters.values() if fltr.field_name is not None]
    assert generated
    assert all(type(fltr.field_name) is str for fltr in generated)
    assert all(type(fltr.lookup_expr) is str for fltr in generated)
    assert spec.applied in filters
    if spec.absent is not None:
        assert spec.absent not in filters
    expected = Category.objects.filter(**{spec.applied: value}).order_by("pk")
    assert expected.exists()
    assert list(rows.order_by("pk")) == list(expected)


class _FieldNames:
    """Field names behind ``__iter__`` / ``__len__`` / ``__contains__``, with no ``list`` / ``tuple`` base.

    A ``collections.abc.Collection`` by structure only (it does not subclass it).
    """

    def __init__(self, *names: str) -> None:
        super().__init__()
        self._names = names

    def __iter__(self) -> Iterator[str]:
        return iter(self._names)

    def __len__(self) -> int:
        return len(self._names)

    def __contains__(self, item: object) -> bool:
        return item in self._names


def _declared_filter_probe_error(fields: object) -> str:
    """The error declaring a set with a ``custom`` declared filter named in ``fields`` raises."""
    meta = type("Meta", (), {"model": Category, "fields": fields})
    namespace = {"custom": CharFilter(field_name="name"), "Meta": meta, "__module__": __name__}
    with pytest.raises(TypeError, match="must not contain non-model field names") as exc_info:
        _ = type("DeclaredInFieldsProbe", (FilterSet,), namespace)
    return str(exc_info.value)


_DECLARED_NAME_COLLECTIONS: dict[str, Callable[[_Namer], object]] = {
    "custom Collection": lambda n: _FieldNames(n("name"), "custom"),
    "dict_keys": lambda n: {n("name"): None, "custom": None}.keys(),
}


@pytest.mark.parametrize("kind", STR_SUBCLASS_KINDS)
@pytest.mark.parametrize("shape", list(_DECLARED_NAME_COLLECTIONS))
def test_a_str_subclass_name_keeps_a_collection_out_of_the_declared_filter_allowance(
    shape: str,
    kind: str,
) -> None:
    """Reading the names as plain text never changes which declared filters ``Meta.fields`` may name.

    django-filter lets a ``list`` / ``tuple`` ``Meta.fields`` name a declared
    filter and refuses one in any other collection. A collection holding a
    ``str``-subclass name is refused exactly as its plain twin is: the plain-text
    copy is no ``list`` / ``tuple`` either.
    """
    calls: list[str] = []
    declare = _DECLARED_NAME_COLLECTIONS[shape]
    fields = declare(lambda text: str_subclass_name(kind, text, calls))
    calls.clear()

    assert _declared_filter_probe_error(fields) == _declared_filter_probe_error(declare(str))
    assert calls == []


def test_a_str_enum_class_meta_fields_is_refused_a_declared_filter_like_a_collection() -> None:
    """A ``StrEnum`` class as ``Meta.fields`` is a collection of its members' text, not a list."""
    names = STR_ENUM("FieldNames", {"NAME": "name", "CUSTOM": "custom"})

    assert _declared_filter_probe_error(names) == _declared_filter_probe_error(
        _FieldNames("name", "custom"),
    )


_CATEGORY_COLUMNS = (
    "name",
    "description",
    "is_private",
    "created_date",
    "updated_date",
    "id",
)


_NAME_LOOKUPS = (
    "exact",
    "icontains",
    "istartswith",
    "iendswith",
)


class _CanonicalOrderRow(NamedTuple):
    """One unordered ``Meta`` declaration and the order it must expand in."""

    meta: dict[str, object]
    # ``(field name, lookups)`` in the expected order: each lookup a ``base_filters`` entry.
    expected: list[tuple[str, list[str]]]


_RowBuilder: TypeAlias = Callable[[], _CanonicalOrderRow]


def _names_meta(key: str, kind: type[set[str] | frozenset[str]]) -> _RowBuilder:
    def build() -> _CanonicalOrderRow:
        names = scrambled(kind, _CATEGORY_COLUMNS)
        return _CanonicalOrderRow(
            {key: names},
            [(name, ["exact"]) for name in canonical_order(names)],
        )

    return build


def _excluded_meta() -> _CanonicalOrderRow:
    kept = tuple(name for name in _CATEGORY_COLUMNS if name != "updated_date")
    names = scrambled(set, kept, drop=("updated_date",))
    return _CanonicalOrderRow(
        {"fields": names, "exclude": {"updated_date"}},
        [(name, ["exact"]) for name in canonical_order(names) if name != "updated_date"],
    )


def _lookup_set_meta() -> _CanonicalOrderRow:
    lookups = scrambled(set, _NAME_LOOKUPS)
    return _CanonicalOrderRow(
        {"fields": {"name": lookups, "description": ["exact"]}},
        [("name", canonical_order(lookups)), ("description", ["exact"])],
    )


_CANONICAL_ORDER_ROWS: dict[str, _RowBuilder] = {
    "fields set": _names_meta("fields", set),
    "fields frozenset": _names_meta("fields", frozenset),
    "filter_fields set": _names_meta("filter_fields", set),
    "filter_fields frozenset": _names_meta("filter_fields", frozenset),
    "set beside a set exclude": _excluded_meta,
    "set of lookups in a dict": _lookup_set_meta,
}


@pytest.mark.parametrize("row", list(_CANONICAL_ORDER_ROWS))
def test_unordered_meta_fields_canonicalize_the_private_table_without_rewriting_meta(
    row: str,
) -> None:
    """Unordered Meta declarations sort the private filter table without replacing their original value.

    Actual GraphQL field and lookup order is owned by
    test_filter_publication_api.py.
    """
    declared, expected = _CANONICAL_ORDER_ROWS[row]()
    name = "CanonicalOrder" + "".join(word.title() for word in row.replace("_", " ").split())
    meta = type("Meta", (), {"model": Category, **declared})
    probe = type(name, (FilterSet,), {"Meta": meta, "__module__": __name__})
    assert issubclass(probe, FilterSet)

    assert list(probe.base_filters) == [
        field if lookup == "exact" else f"{field}__{lookup}"
        for field, lookups in expected
        for lookup in lookups
    ]
    assert read_attr(read_attr(probe, "_meta"), "fields") is next(iter(declared.values()))


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        pytest.param(
            ["updated_date", "name", "is_private"],
            ["updated_date", "name", "is_private"],
            id="list",
        ),
        pytest.param(
            ("updated_date", "name", "is_private"),
            ["updated_date", "name", "is_private"],
            id="tuple",
        ),
        pytest.param(
            {"name": ["istartswith", "exact", "icontains"]},
            ["name__istartswith", "name", "name__icontains"],
            id="dict of lists",
        ),
    ],
)
def test_an_ordered_meta_fields_keeps_its_declared_order(
    fields: object,
    expected: list[str],
) -> None:
    """Positive control: a declaration out of canonical order but ordered is expanded as declared."""
    meta = type("Meta", (), {"model": Category, "fields": fields})
    probe = type("DeclaredOrderProbe", (FilterSet,), {"Meta": meta, "__module__": __name__})
    assert issubclass(probe, FilterSet)

    assert list(probe.base_filters) == expected
    assert read_attr(read_attr(probe, "_meta"), "fields") is fields


@pytest.mark.parametrize("kind", [set, frozenset])
def test_an_unordered_meta_fields_stays_out_of_the_declared_filter_allowance(
    kind: Callable[[Iterable[str]], Collection[str]],
) -> None:
    """The canonical reorder never turns a set into the ``list`` django-filter lets name a declared filter."""
    assert "'Meta.fields' must not contain non-model field names: custom" in (
        _declared_filter_probe_error(kind(["name", "custom"]))
    )


_Wrap: TypeAlias = Callable[[Callable[[], object]], object]


def _lazy_meta_outcome(meta: dict[str, object]) -> object:
    """The filters a set with a ``custom`` declared filter generates from ``meta``, or its error text."""
    namespace = {
        "custom": CharFilter(field_name="name"),
        "Meta": type("Meta", (), {"model": Category, **meta}),
        "__module__": __name__,
    }
    try:
        probe = type("LazyMetaProbe", (FilterSet,), namespace)
    except TypeError as exc:
        return str(exc)
    assert issubclass(probe, FilterSet)
    return {
        name: (type(fltr).__name__, fltr.field_name, fltr.lookup_expr)
        for name, fltr in probe.base_filters.items()
    }


_LAZY_FILTER_META: dict[str, Callable[[_Wrap], dict[str, object]]] = {
    "fields list": lambda w: {"fields": w(lambda: ["name", "custom"])},
    "fields tuple": lambda w: {"fields": w(lambda: ("name", "custom"))},
    "fields set": lambda w: {"fields": w(lambda: {"name", "custom"})},
    "fields frozenset": lambda w: {"fields": w(lambda: frozenset({"name", "custom"}))},
    "fields set of model names": lambda w: {"fields": w(lambda: {"name", "is_private"})},
    "fields dict": lambda w: {"fields": w(lambda: {"name": ["exact", "icontains"]})},
    "fields dict lazy lookups": lambda w: {"fields": {"name": w(lambda: ["exact", "in"])}},
    "fields str-enum member": lambda w: {
        "fields": w(lambda: [STR_ENUM("Names", {"NAME": "name"})["NAME"], "custom"]),
    },
    "fields nested lazy": lambda w: {"fields": w(lambda: w(lambda: ["name", "custom"]))},
    "filter_fields alias": lambda w: {"filter_fields": w(lambda: ["name"])},
    "exclude list": lambda w: {"exclude": w(lambda: ["name"])},
    "exclude tuple": lambda w: {"exclude": w(lambda: ("name",))},
    "exclude set": lambda w: {"exclude": w(lambda: {"name"})},
    "exclude frozenset": lambda w: {"exclude": w(lambda: frozenset({"name"}))},
}


@pytest.mark.parametrize("shape", list(_LAZY_FILTER_META))
def test_filterset_reads_a_lazy_meta_declaration_as_the_object_it_stands_for(shape: str) -> None:
    """A ``SimpleLazyObject`` ``Meta.fields`` / ``filter_fields`` / ``Meta.exclude`` is its target.

    Each lazy declaration generates exactly the filters its evaluated twin does,
    and django-filter's declared-filter allowance (a ``list`` / ``tuple`` may name
    a declared filter, any other collection may not) answers as it does for the
    twin.
    """
    meta = _LAZY_FILTER_META[shape]

    assert _lazy_meta_outcome(meta(SimpleLazyObject)) == _lazy_meta_outcome(
        meta(lambda target: target()),
    )


def test_filter_for_field_on_a_model_less_set_adds_no_fan_out_distinct() -> None:
    """A set without ``Meta.model`` has no relation path to classify, so no ``distinct`` is added."""

    class ModelLessProbe(FilterSet):
        pass

    generated = ModelLessProbe.filter_for_field(Item._meta.get_field("name"), "name", "exact")

    assert generated is not None
    assert generated.distinct is False


def test_filter_for_field_preserves_upstream_none_contract_for_unrecognized_field() -> None:
    """An unrecognized model field returns ``None`` under WARN / IGNORE behavior.

    django-filter's ``filter_for_field`` returns ``None`` for a model field
    with no ``FILTER_DEFAULTS`` entry (``Item.attachment`` is a ``FileField``)
    whenever ``Meta.unknown_field_behavior`` is ``WARN`` or ``IGNORE``; upstream
    ``get_filters`` then skips the leaf. The package override dereferences
    ``default.distinct`` / ``default.field_name`` / ``default.extra``, so it
    MUST return the ``None`` verbatim instead of crashing with a raw
    ``AttributeError`` on a field type the package deliberately does not
    filter. The default (``RAISE``) behavior keeps upstream's assertion.
    """

    class AttachmentProbe(FilterSet):
        class Meta:
            model = Item
            fields = ["name", "attachment"]
            unknown_field_behavior = UnknownFieldBehavior.IGNORE

    filters = AttachmentProbe.get_filters()
    assert set(filters) == {"name"}
    assert type(filters["name"]) is CharFilter
    assert filters["name"].field_name == "name"
    assert filters["name"].lookup_expr == "exact"

    attachment_field = Item._meta.get_field("attachment")
    assert AttachmentProbe.filter_for_field(attachment_field, "attachment", "exact") is None
    assert AttachmentProbe.filter_for_field(attachment_field, "attachment", "in") is None

    with pytest.raises(
        AssertionError,
        match=r"RaiseProbe resolved field 'attachment'.*unrecognized field type FileField",
    ):

        @definition_raises
        class RaiseProbe(FilterSet):
            class Meta:
                model = Item
                fields = ["name", "attachment"]


def test_filter_for_field_picks_global_id_multiple_choice_filter_for_relay_m2m_target() -> None:
    """An M2M to a Relay-Node-shaped target maps to `GlobalIDMultipleChoiceFilter`.

    Decision 4 ports BOTH `GlobalIDFilter` (single-valued) and
    `GlobalIDMultipleChoiceFilter` (multi-valued); the runtime override
    has to pick the multi-valued primitive for `ManyToManyField` so the
    underlying queryset semantics match the field's cardinality.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    # The finalizer's owner-binding pass is not exercised here; this test only
    # needs `GenreType` to be a subclass of `relay.Node` so `implements_relay_node`
    # returns `True`. `apply_interfaces` (spec-015) is the helper that injects bases.
    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("genres")
    resolved = BookFilter.filter_for_field(field, "genres")
    assert isinstance(resolved, GlobalIDMultipleChoiceFilter)


def test_filter_for_field_picks_global_id_filter_for_relay_forward_fk_target() -> None:
    """A forward FK to a Relay-Node-shaped target maps to `GlobalIDFilter`.

    Complement of the M2M case above - single-valued relations pick the
    single-value Relay primitive.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ShelfType, ShelfType.__django_strawberry_definition__)

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(field, "shelf")
    assert isinstance(resolved, GlobalIDFilter)
    assert not isinstance(resolved, GlobalIDMultipleChoiceFilter)


def test_filter_for_field_marks_non_pk_to_field_relation_globalid_with_pk_path() -> None:
    """A forward FK on a non-pk ``to_field`` gets the pk-qualification flag.

    The generated ``GlobalIDFilter`` must carry the boolean
    ``_GLOBALID_RELATION_PK_ATTR`` flag set ``True`` so its predicate derives
    ``f"{field_name}__pk"`` and compares the target's primary key (which a Relay
    GlobalID carries) rather than the raw FK-stored ``name`` column of
    ``PatronProfile.favorite_genre``.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class ChildFilter(FilterSet):
        class Meta:
            model = library_models.PatronProfile
            fields = {"postal_code": ["exact"]}

    field = library_models.PatronProfile._meta.get_field("favorite_genre")
    resolved = ChildFilter.filter_for_field(field, "favorite_genre")
    assert isinstance(resolved, GlobalIDFilter)
    assert getattr(resolved, _GLOBALID_RELATION_PK_ATTR, None) is True


def test_filter_for_field_fk_to_pk_relation_globalid_carries_no_marker() -> None:
    """An ordinary FK-to-pk GlobalID relation filter must NOT carry the marker."""

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ShelfType, ShelfType.__django_strawberry_definition__)

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(field, "shelf")
    assert isinstance(resolved, GlobalIDFilter)
    assert getattr(resolved, _GLOBALID_RELATION_PK_ATTR, False) is not True


def test_generated_forward_fk_in_is_multiple_choice_over_fk_to_pk() -> None:
    """Forward Relay FK ``in`` over an ordinary FK-to-pk generates a list filter.

    The generated ``shelf__in`` leaf must be ``GlobalIDMultipleChoiceFilter`` with a
    ``list[str]`` input annotation, while the sibling ``shelf`` (exact) leaf stays the
    scalar ``GlobalIDFilter`` -- proving only the lookup-aware ``in`` shape is a list and
    the cardinality-selected non-``in`` shape stays scalar.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ShelfType, ShelfType.__django_strawberry_definition__)

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"shelf": ["exact", "in"]}

    field = library_models.Book._meta.get_field("shelf")
    generated = BookFilter.get_filters()

    in_leaf = generated["shelf__in"]
    assert isinstance(in_leaf, GlobalIDMultipleChoiceFilter)
    assert convert_filter_to_input_annotation(in_leaf, field, None, BookFilter) == list[str] | None
    # An ordinary FK-to-pk relation carries no pk-qualification marker.
    assert getattr(in_leaf, _GLOBALID_RELATION_PK_ATTR, False) is not True

    exact_leaf = generated["shelf"]
    assert isinstance(exact_leaf, GlobalIDFilter)
    assert not isinstance(exact_leaf, GlobalIDMultipleChoiceFilter)
    assert convert_filter_to_input_annotation(exact_leaf, field, None, BookFilter) == str | None


def test_generated_forward_fk_in_uses_globalid_multiple_choice_filter() -> None:
    """A generated Relay forward-FK membership keeps its concrete Python filter class."""

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ShelfType, ShelfType.__django_strawberry_definition__)

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"shelf": ["in"]}

    in_leaf = BookFilter.get_filters()["shelf__in"]
    assert isinstance(in_leaf, GlobalIDMultipleChoiceFilter)


def test_generated_forward_fk_to_field_in_is_pk_qualified_multiple_choice() -> None:
    """Forward Relay FK ``in`` over a non-pk ``to_field`` is pk-qualified.

    ``PatronProfile.favorite_genre`` binds on ``Genre.name`` (a non-pk column), so the
    generated ``favorite_genre__in`` leaf must be a ``GlobalIDMultipleChoiceFilter``
    that STILL carries the boolean ``_GLOBALID_RELATION_PK_ATTR`` marker (stamped after
    the lookup-aware class is chosen) so its predicate derives
    ``favorite_genre__pk__in`` and compares the genre primary key a Relay GlobalID
    carries. The sibling exact leaf
    keeps the marked scalar ``GlobalIDFilter`` shape.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class ChildFilter(FilterSet):
        class Meta:
            model = library_models.PatronProfile
            fields = {"favorite_genre": ["exact", "in"]}

    field = library_models.PatronProfile._meta.get_field("favorite_genre")
    generated = ChildFilter.get_filters()

    in_leaf = generated["favorite_genre__in"]
    assert isinstance(in_leaf, GlobalIDMultipleChoiceFilter)
    assert getattr(in_leaf, _GLOBALID_RELATION_PK_ATTR, None) is True
    assert (
        convert_filter_to_input_annotation(in_leaf, field, None, ChildFilter) == list[str] | None
    )

    exact_leaf = generated["favorite_genre"]
    assert isinstance(exact_leaf, GlobalIDFilter)
    assert not isinstance(exact_leaf, GlobalIDMultipleChoiceFilter)
    assert getattr(exact_leaf, _GLOBALID_RELATION_PK_ATTR, None) is True


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("child_name", "marked"),
    [("LnkSlugObjectChild", True), ("LnkPairChild", True), ("LnkColumnChild", False)],
    ids=["one_column_fo_non_pk_target", "two_column_fo", "one_column_fo_pk_target"],
)
def test_generated_foreign_object_filter_keeps_its_pk_qualification_marker(
    child_name: str,
    *,
    marked: bool,
) -> None:
    """Generated ForeignObject filters keep their Python class and per-shape pk marker."""
    child_model = read_attr(_link_models, child_name)
    assert isinstance(child_model, type)
    assert issubclass(child_model, django_models.Model)

    class LnkParentType(DjangoType):
        class Meta:
            model = _link_models.LnkParent
            fields = ("id", "label")
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(LnkParentType, LnkParentType.__django_strawberry_definition__)

    child_filter = type(
        "ChildFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": child_model, "fields": {"parent": ["exact"]}})},
    )
    leaf = child_filter.get_filters()["parent"]
    assert isinstance(leaf, GlobalIDFilter)
    assert getattr(leaf, _GLOBALID_RELATION_PK_ATTR, False) is marked


@pytest.mark.django_db
def test_expanded_globalid_leaf_keeps_its_live_path_and_marker() -> None:
    """The expanded filter copy retains its full live path and boolean pk-qualification marker."""

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class ChildFilter(FilterSet):
        class Meta:
            model = library_models.PatronProfile
            fields = {"favorite_genre": ["exact"]}

    class ParentFilter(FilterSet):
        favoring_profiles = RelatedFilter(ChildFilter)

        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    # (a) The expanded leaf's LIVE field_name is the full relation path, and the
    # boolean pk-qualification flag rode the deepcopy through unchanged.
    expanded_leaf = ParentFilter.get_filters()["favoring_profiles__favorite_genre"]
    assert isinstance(expanded_leaf, GlobalIDFilter)
    assert expanded_leaf.field_name == "favoring_profiles__favorite_genre"
    assert getattr(expanded_leaf, _GLOBALID_RELATION_PK_ATTR, False) is True


def _register_relay_target(model: type[django_models.Model]) -> type[DjangoType]:
    """Register ``model`` as a Relay-Node-shaped ``DjangoType`` for relation resolution.

    Mirrors the inline pattern in the ``filter_for_field`` relation tests above:
    a relation key's target type is ``registry.get`` of its related model, so a
    relation to ``model`` resolves to a Relay node and the Relay wire-shape policy
    applies.
    """
    django_type = type(
        f"{model.__name__}RelayType",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model, "interfaces": (strawberry.relay.Node,)})},
    )
    apply_interfaces(django_type, django_type.__django_strawberry_definition__)
    return django_type


def _register_plain_types(*models: type[django_models.Model]) -> None:
    """Register a plain ``DjangoType`` per model, the visibility a declared hop's target needs.

    A flat leaf walking a declared ``RelatedFilter`` hop applies the target
    type's ``get_queryset`` exactly as the nested branch does, so the target
    model needs a registered type (the default ``get_queryset`` hides nothing).
    """
    for model in models:
        type(
            f"{model.__name__}PlainType",
            (DjangoType,),
            {"Meta": type("Meta", (), {"model": model})},
        )


@pytest.mark.parametrize("lookup", ["gt", "lt"], ids=["gt", "lt"])
def test_framework_relay_forward_fk_unsupported_lookup_raises_at_build(lookup: str) -> None:
    """An unsupported ordering lookup on a framework-owned forward FK is rejected."""
    _register_relay_target(library_models.Shelf)

    with pytest.raises(ConfigurationError) as exc_info:

        @definition_raises
        class BookFilter(FilterSet):
            class Meta:
                model = library_models.Book
                fields = {"shelf": [lookup]}

    message = str(exc_info.value)
    assert "BookFilter" in message
    assert "shelf" in message
    assert lookup in message


def test_framework_relay_m2m_unsupported_lookup_raises_at_build() -> None:
    """An unsupported pattern lookup on a framework-owned M2M relation is rejected."""
    _register_relay_target(library_models.Genre)

    with pytest.raises(ConfigurationError) as exc_info:

        @definition_raises
        class BookFilter(FilterSet):
            class Meta:
                model = library_models.Book
                fields = {"genres": ["icontains"]}

    message = str(exc_info.value)
    assert "BookFilter" in message
    assert "genres" in message
    assert "icontains" in message


def test_framework_relay_reverse_relation_unsupported_lookup_raises_at_build() -> None:
    """An unsupported ordering lookup on a framework-owned reverse relation is rejected."""
    _register_relay_target(library_models.Loan)

    with pytest.raises(ConfigurationError) as exc_info:

        @definition_raises
        class BookFilter(FilterSet):
            class Meta:
                model = library_models.Book
                fields = {"loans": ["gt"]}

    message = str(exc_info.value)
    assert "BookFilter" in message
    assert "loans" in message
    assert "gt" in message


def test_framework_raw_pk_relation_unsupported_lookup_raises_at_build() -> None:
    """An ordering lookup on a non-Relay relation key fails at build and points at RelatedFilter."""
    with pytest.raises(ConfigurationError) as exc_info:

        @definition_raises
        class BookFilter(FilterSet):
            class Meta:
                model = library_models.Book
                fields = {"shelf": ["gt"]}

    message = str(exc_info.value)
    assert "BookFilter" in message
    assert "'shelf'" in message
    assert "'gt'" in message
    assert "primary key" in message
    assert "RelatedFilter" in message
    assert "SCALAR_MAP" not in message


def test_related_filter_target_relay_relation_unsupported_lookup_raises_at_build() -> None:
    """A RelatedFilter target declaring an unsupported relay-relation lookup fails at build.

    The parent references the child (the expansion target) by string, so it
    defines successfully with an unresolved lazy target. The child's own
    ``Meta.fields`` then declares an unsupported ordering lookup on its
    framework-owned relay relation. Because the child's filters are generated at
    the child's class creation -- the SAME generation pass
    ``_expand_related_filter`` consumes when the parent expands it -- the corrupt
    relay-relation leaf is rejected there rather than becoming an expanded leaf
    that fails only at query execution.
    """
    _register_relay_target(library_models.Patron)

    class BookParentFilter(FilterSet):
        loans = RelatedFilter("LoanTargetFilter", field_name="loans")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    assert BookParentFilter._expansion_snapshot() is None

    with pytest.raises(ConfigurationError) as exc_info:

        @definition_raises
        class LoanTargetFilter(FilterSet):
            class Meta:
                model = library_models.Loan
                fields = {"patron": ["gt"]}

    message = str(exc_info.value)
    assert "LoanTargetFilter" in message
    assert "patron" in message
    assert "gt" in message


def test_framework_relay_relation_supported_lookups_generate_without_raising() -> None:
    """Positive controls: exact/in/isnull on framework-owned relay relations still build.

    ``exact`` is cardinality-selected (``GlobalIDFilter`` single-valued /
    ``GlobalIDMultipleChoiceFilter`` many-side), ``in`` is always the list-shaped
    ``GlobalIDMultipleChoiceFilter``, and ``isnull`` stays the upstream Boolean --
    none of them raise.
    """
    _register_relay_target(library_models.Shelf)
    _register_relay_target(library_models.Genre)

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"shelf": ["exact", "in", "isnull"], "genres": ["exact", "in", "isnull"]}

    generated = BookFilter.get_filters()

    # Single-valued forward FK: exact -> scalar GlobalIDFilter.
    shelf_exact = generated["shelf"]
    assert isinstance(shelf_exact, GlobalIDFilter)
    assert not isinstance(shelf_exact, GlobalIDMultipleChoiceFilter)
    # Many-side M2M: exact -> list GlobalIDMultipleChoiceFilter.
    assert isinstance(generated["genres"], GlobalIDMultipleChoiceFilter)
    # ``in`` is list-shaped for BOTH cardinalities.
    assert isinstance(generated["shelf__in"], GlobalIDMultipleChoiceFilter)
    assert isinstance(generated["genres__in"], GlobalIDMultipleChoiceFilter)
    # ``isnull`` is the upstream Boolean, never a GlobalID.
    for isnull_name in ("shelf__isnull", "genres__isnull"):
        isnull_leaf = generated[isnull_name]
        assert isinstance(isnull_leaf, BooleanFilter)
        assert not isinstance(isnull_leaf, (GlobalIDFilter, GlobalIDMultipleChoiceFilter))


def test_consumer_override_relation_nonstandard_lookup_not_rejected() -> None:
    """A consumer-owned relation override implementing a nonstandard lookup is NOT rejected.

    Ownership is decided before the wire-shape policy: a ``Meta.filter_overrides``
    entry selecting a custom filter class means the consumer owns the wire shape,
    so ``filter_for_lookup`` returns the consumer's class unchanged and never
    raises -- even for a lookup outside ``{exact, in, isnull}``.
    """
    _register_relay_target(library_models.Genre)

    class CustomM2M(ModelMultipleChoiceFilter):
        """Consumer filter class governing the M2M relation selection."""

    def _override_extra(_f: object) -> dict[str, object]:
        return {"queryset": library_models.Genre.objects.all()}

    class OverrideFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["icontains"]}
            filter_overrides = {
                dj_models.ManyToManyField: {"filter_class": CustomM2M, "extra": _override_extra},
            }

    genres_field = library_models.Book._meta.get_field("genres")
    # ``filter_for_lookup`` short-circuits on the consumer-owned origin and returns
    # the consumer's class unchanged -- no ConfigurationError.
    selected_class, _params = OverrideFilter.filter_for_lookup(genres_field, "icontains")
    assert selected_class is CustomM2M
    # The full generation path also builds without raising and keeps the consumer class.
    leaf = OverrideFilter.get_filters()["genres__icontains"]
    assert isinstance(leaf, CustomM2M)


@pytest.mark.django_db
def test_generated_to_field_scalar_candidate_owns_one_predicate_alias() -> None:
    """A routable generated to-field scalar candidate owns one raw reserved predicate alias."""

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)
    finalize_django_types()

    class ParentFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"], "favoring_profiles__favorite_genre": ["exact"]}

    # Publish the atomic expansion snapshot (sets ``base_filters`` + candidate
    # rows). The traversal to_field leaf is an eligible, pk-marked, ROUTABLE candidate.
    ParentFilter.get_filters()
    candidate = _snapshot(ParentFilter).candidates["favoring_profiles__favorite_genre"]
    assert candidate.eligible is True
    assert candidate.routable is True

    target = library_models.Genre.objects.create(name="C1")
    query = ParentFilter(
        data={"favoring_profiles__favorite_genre": global_id_for(GenreType, saved_pk(target))},
        queryset=library_models.Genre.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    assert len(_reserved_aliases(query)) == 1


@pytest.mark.django_db
def test_generated_to_field_membership_keeps_its_marker_annotation_and_alias() -> None:
    """A generated membership copy retains its Python annotation, marker and raw outer alias ownership."""

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)
    finalize_django_types()

    class ParentFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"], "favoring_profiles__favorite_genre": ["in"]}

    ParentFilter.get_filters()
    candidate = _snapshot(ParentFilter).candidates["favoring_profiles__favorite_genre__in"]
    assert candidate.eligible is True
    assert candidate.routable is True

    expanded_leaf = ParentFilter.get_filters()["favoring_profiles__favorite_genre__in"]
    assert isinstance(expanded_leaf, GlobalIDMultipleChoiceFilter)
    assert getattr(expanded_leaf, _GLOBALID_RELATION_PK_ATTR, None) is True
    child_target_field = library_models.PatronProfile._meta.get_field("favorite_genre")
    assert (
        convert_filter_to_input_annotation(expanded_leaf, child_target_field, None, ParentFilter)
        == list[str] | None
    )

    first = library_models.Genre.objects.create(name="C1")
    second = library_models.Genre.objects.create(name="C2")
    bound = ParentFilter(
        data={
            "favoring_profiles__favorite_genre__in": [
                global_id_for(GenreType, saved_pk(row)) for row in (first, second)
            ],
        },
        queryset=library_models.Genre.objects.order_by("id"),
        request=HttpRequest(),
    )
    query = bound.qs
    live = bound.filters["favoring_profiles__favorite_genre__in"]
    assert getattr(live, _GLOBALID_RELATION_PK_ATTR, None) is True
    assert len(_reserved_aliases(query)) == 1
    _ = str(query.query)
    outer_tables = sorted({join.table_name for join in query.query.alias_map.values()})
    assert outer_tables == [library_models.Genre._meta.db_table]


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["exact", "membership", "empty"])
def test_declared_to_field_branch_owns_no_generated_predicate_alias(case: str) -> None:
    """Declared relation branches allocate no generated-adapter predicate aliases."""

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class ProfileType(DjangoType):
        class Meta:
            model = library_models.PatronProfile
            fields = ("postal_code",)

    finalize_django_types()
    assert registry.get(library_models.PatronProfile) is ProfileType

    class ChildFilter(FilterSet):
        class Meta:
            model = library_models.PatronProfile
            fields = {"favorite_genre": ["exact", "in"]}

    class ParentFilter(FilterSet):
        favoring_profiles = RelatedFilter(ChildFilter)

        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    ParentFilter.get_filters()
    first = library_models.Genre.objects.create(name="C1")
    second = library_models.Genre.objects.create(name="C2")
    encoded = [global_id_for(GenreType, saved_pk(row)) for row in (first, second)]
    options: dict[str, dict[str, object]] = {
        "exact": {"favoring_profiles__favorite_genre": encoded[0]},
        "membership": {"favoring_profiles__favorite_genre__in": encoded},
        "empty": {"favoring_profiles__favorite_genre__in": []},
    }
    data = options[case]
    query = ParentFilter(
        data=data,
        queryset=library_models.Genre.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    assert _reserved_aliases(query) == []


def test_direct_m2m_relation_override_on_relay_target_is_honored() -> None:
    """A ``Meta.filter_overrides`` M2M relation filter over a Relay target is kept."""

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class CustomRelationFilter(django_filters.ModelMultipleChoiceFilter):
        pass

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}
            filter_overrides = {
                django_models.ManyToManyField: {"filter_class": CustomRelationFilter},
            }

    leaf = BookFilter.get_filters()["genres"]
    # The consumer's class survives -- NOT replaced by GlobalIDMultipleChoiceFilter.
    assert isinstance(leaf, CustomRelationFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    # override_generated is not framework-generated, so it gets NO candidate row.
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "genres" not in snapshot.candidates


def test_direct_forward_fk_relation_override_on_relay_target_is_honored() -> None:
    """A ``Meta.filter_overrides`` forward-FK filter over a Relay target is kept."""

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ShelfType, ShelfType.__django_strawberry_definition__)

    class CustomFKFilter(django_filters.ModelChoiceFilter):
        pass

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"shelf": ["exact"]}
            filter_overrides = {
                django_models.ForeignKey: {"filter_class": CustomFKFilter},
            }

    leaf = BookFilter.get_filters()["shelf"]
    assert isinstance(leaf, CustomFKFilter)
    assert not isinstance(leaf, GlobalIDFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "shelf" not in snapshot.candidates


def test_filter_defaults_shadow_relation_override_on_relay_target_is_honored() -> None:
    """A shadowed class-level ``FILTER_DEFAULTS`` relation override is honored too.

    A ``FILTER_DEFAULTS`` shadow makes the class non-capable
    (``_is_generation_capable``), which declines routing but not the Relay
    conversion: the ownership oracle is what keeps the consumer's class, stamping
    ``override_generated`` instead of ``package_replacement``.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class CustomRelationFilter(django_filters.ModelMultipleChoiceFilter):
        pass

    def _override_extra(_f: object) -> dict[str, object]:
        return {
            "queryset": library_models.Genre._default_manager.all(),
        }

    class BookFilter(FilterSet):
        # Shallow-copy the public table: untouched entries retain their framework
        # identity, while the replacement M2M entry is consumer-owned.
        FILTER_DEFAULTS = {
            **FilterSet.FILTER_DEFAULTS,
            django_models.ManyToManyField: {
                "filter_class": CustomRelationFilter,
                "extra": _override_extra,
            },
        }

        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}

    leaf = BookFilter.get_filters()["genres"]
    assert isinstance(leaf, CustomRelationFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    assert BookFilter._is_generation_capable() is False
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "genres" not in snapshot.candidates


def test_related_filter_expansion_preserves_child_relation_override() -> None:
    """An expanded ``<related>__<relation>`` leaf inherits the child's override.

    The child ``BookFilter`` overrides its own Relay-node M2M relation
    (``genres``) via ``Meta.filter_overrides``. When a parent expands it across
    ``book`` (Loan -> Book), the expanded ``book__genres`` leaf must keep the
    consumer's class and its ``override_generated`` origin, so it never becomes a
    correlated-EXISTS candidate.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class CustomRelationFilter(django_filters.ModelMultipleChoiceFilter):
        pass

    class ChildBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}
            filter_overrides = {
                django_models.ManyToManyField: {"filter_class": CustomRelationFilter},
            }

    class LoanParentFilter(FilterSet):
        book = RelatedFilter(ChildBookFilter, field_name="book")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    expanded = LoanParentFilter.get_filters()
    leaf = expanded["book__genres"]
    assert isinstance(leaf, CustomRelationFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    snapshot = LoanParentFilter._expansion_snapshot()
    assert snapshot is not None
    assert "book__genres" not in snapshot.candidates


def test_a_consumer_relation_override_is_absent_from_the_frozen_candidate_table() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class CustomRelationFilter(django_filters.ModelMultipleChoiceFilter):
        pass

    def _override_extra(_f: object) -> dict[str, object]:
        return {
            "queryset": library_models.Genre._default_manager.all(),
        }

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}
            filter_overrides = {
                django_models.ManyToManyField: {
                    "filter_class": CustomRelationFilter,
                    "extra": _override_extra,
                },
            }

    BookFilter.get_filters()
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "genres" not in snapshot.candidates


def test_filter_for_field_picks_scalar_filter_for_non_relay_target() -> None:
    """A non-Relay `DjangoType` target yields the raw-pk pair, typed from the target pk column."""

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf

    assert registry.get(library_models.Shelf) is ShelfType

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(field, "shelf")
    assert isinstance(resolved, RelationPkFilter)
    assert convert_filter_to_input_annotation(resolved, field, None, BookFilter) == (int | None)
    resolved_in = BookFilter.filter_for_field(field, "shelf", "in")
    assert isinstance(resolved_in, RelationPkMultipleFilter)
    assert convert_filter_to_input_annotation(resolved_in, field, None, BookFilter) == (
        list[int] | None
    )


def test_filter_for_field_types_raw_pk_when_target_model_not_registered() -> None:
    """No registered `DjangoType` for the target -> the raw-pk filter, typed from the pk column."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(field, "shelf")
    assert isinstance(resolved, RelationPkFilter)
    assert convert_filter_to_input_annotation(resolved, field, None, BookFilter) == (int | None)


@pytest.mark.parametrize(
    ("model_class", "field_name"),
    [
        (Category, "items__name"),
        (library_models.Book, "genres__name"),
        (library_models.Genre, "books__title"),
    ],
)
def test_filter_for_field_marks_generated_to_many_paths_distinct(
    model_class: type[django_models.Model],
    field_name: str,
) -> None:
    class GeneratedFilter(FilterSet):
        class Meta:
            model = model_class
            fields = {field_name: ["icontains"]}

    filter_instance = GeneratedFilter.get_filters()[f"{field_name}__icontains"]

    assert filter_instance.distinct is True


def test_filter_for_field_keeps_generated_to_one_path_non_distinct() -> None:
    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"shelf__code": ["icontains"]}

    filter_instance = BookFilter.get_filters()["shelf__code__icontains"]

    assert filter_instance.distinct is False


def test_a_flattened_related_copy_keeps_its_python_path_and_distinct_flag() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """
    _register_plain_types(library_models.Genre)
    leaf = BookFilter.get_filters()["genres__name__icontains"]
    assert leaf.field_name == "genres__name"
    assert leaf.distinct is False


@pytest.mark.django_db
def test_invoke_suppressing_helper_restores_distinct_after_success() -> None:
    """The helper restores the per-instance ``distinct`` flag after a successful apply."""

    class BookGenreFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    bare = BookGenreFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    filter_instance = bare.filters["genres__name__icontains"]
    assert filter_instance.distinct is True

    inner_root = correlated_inner_root(library_models.Book.objects.all())
    result = FilterSet._invoke_suppressing_framework_distinct(
        filter_instance,
        inner_root,
        "cardio",
    )
    assert isinstance(result, QuerySet)
    assert result.model is library_models.Book
    # Restored to the original live value after a successful invocation.
    assert filter_instance.distinct is True


@pytest.mark.django_db
def test_invoke_suppressing_helper_restores_distinct_after_exception() -> None:
    """The helper restores ``distinct`` even when the wrapped invocation raises."""

    class BookGenreFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    bare = BookGenreFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    filter_instance = bare.filters["genres__name__icontains"]
    assert filter_instance.distinct is True

    boom = RuntimeError("decode failure mid-invocation")

    def _raising_filter(qs: QuerySet[django_models.Model], value: object) -> NoReturn:
        del qs, value  # assigned over Filter.filter, whose typed signature fixes both names
        # The flag is suppressed at this point; prove it, then blow up.
        assert filter_instance.distinct is False
        raise boom

    filter_instance.filter = _raising_filter
    inner_root = correlated_inner_root(library_models.Book.objects.all())
    with pytest.raises(RuntimeError, match="decode failure"):
        FilterSet._invoke_suppressing_framework_distinct(filter_instance, inner_root, "cardio")
    # Restored to the original live value despite the exception.
    assert filter_instance.distinct is True


def test_an_active_candidate_gets_only_its_one_private_predicate_alias() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_raw_filter_forms_api.py``.
    """

    class MultiBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"], "loans__note": ["icontains"]}

    MultiBookFilter.get_filters()
    bare = MultiBookFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    result = bare.qs
    reserved = [name for name in result.query.annotations if name.startswith("_dst_predicate_")]
    assert reserved == ["_dst_predicate_0"]


def test_sixteen_inactive_candidates_build_their_inner_roots_without_private_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_raw_filter_forms_api.py``.
    """
    lookups = [
        "icontains",
        "exact",
        "iexact",
        "startswith",
    ]

    class ManyInactiveBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {
                "genres__name": lookups,
                "loans__note": lookups,
                "loans__patron__email": lookups,
                "loans__patron__name": lookups,
            }

    ManyInactiveBookFilter.get_filters()
    real_inner_root = correlated_inner_root
    builds = {"n": 0}

    def _counting_inner_root(queryset: QuerySet[_M]) -> QuerySet[_M]:
        builds["n"] += 1
        return real_inner_root(queryset)

    monkeypatch.setattr(sets_module, "correlated_inner_root", _counting_inner_root)
    base = library_models.Book.objects.order_by("id")
    inactive = ManyInactiveBookFilter(data={}, queryset=base, request=HttpRequest())
    inactive_qs = inactive.qs
    assert len(inactive.form.cleaned_data) == 16
    assert builds["n"] == 16
    reserved = [n for n in inactive_qs.query.annotations if n.startswith("_dst_predicate_")]
    assert reserved == []


def test_restrictive_empty_membership_keeps_its_private_predicate_alias() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_raw_filter_forms_api.py``.
    """

    class BookGenreInFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__id": ["in"]}

    BookGenreInFilter.get_filters()
    bare = BookGenreInFilter(
        # A member past SQLite's signed-64-bit range drops, leaving an empty but
        # RESTRICTIVE membership (``_match_none_queryset``), as an explicit [] is.
        data={"genres__id__in": [99999999999999999999999]},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    result = bare.qs
    reserved = [name for name in result.query.annotations if name.startswith("_dst_predicate_")]
    assert reserved == ["_dst_predicate_0"]


@pytest.mark.django_db
def test_a_forced_missing_expansion_snapshot_keeps_the_leaf_on_the_outer_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A private missing-snapshot state retains the outer query metadata instead of routing a leaf.

    Ordinary constructors publish their snapshot; this forced fallback is a private
    state. Real consumer multiplicity and SQL live in test_filter_querysets_api.py.
    """

    class BookGenreFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    # Expand ``base_filters`` (so the flat leaf is a real form field) THEN force
    # the pre-snapshot state.
    BookGenreFilter.get_filters()

    def _no_snapshot(_cls: type[FilterSet]) -> None:
        return None

    monkeypatch.setattr(BookGenreFilter, "_expansion_snapshot", classmethod(_no_snapshot))
    bare = BookGenreFilter(
        data={"genres__name__icontains": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    )
    result = bare.qs

    assert _reserved_aliases(result) == []
    assert result.query.distinct is True
    assert "EXISTS" not in str(result.query).upper()


def test_generated_reverse_fk_text_keeps_filter_class_and_distinct_provenance() -> None:
    """Generated text leaves retain their Python filter class and framework distinct provenance."""

    class BookLoanFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

    leaf = BookLoanFilter.get_filters()["loans__note__icontains"]
    assert isinstance(leaf, CharFilter)
    assert leaf.distinct is True


def test_generated_generic_relation_keeps_filter_class_and_distinct_provenance() -> None:
    """Generated text leaves retain their Python filter class and framework distinct provenance."""

    class BranchTagFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"tags__tag": ["icontains"]}

    leaf = BranchTagFilter.get_filters()["tags__tag__icontains"]
    assert isinstance(leaf, CharFilter)
    assert leaf.distinct is True


def test_generated_reverse_to_field_filter_keeps_framework_distinct_provenance() -> None:
    """The generated reverse to-field leaf retains framework distinct provenance on its filter object."""

    class TargetChildrenFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"favoring_profiles__postal_code": ["icontains"]}

    leaf = TargetChildrenFilter.get_filters()["favoring_profiles__postal_code__icontains"]
    assert leaf.distinct is True


@pytest.mark.django_db
def test_generated_independent_leaf_aliases_preserve_invocation_order() -> None:
    """Two independently active generated leaves allocate two distinct ordered private aliases."""

    class TwoLeafFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"], "genres__id": ["gt"]}

    TwoLeafFilter.get_filters()
    result = TwoLeafFilter(
        data={"genres__name__icontains": "cardio", "genres__id__gt": 7},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    reserved = [name for name in result.query.annotations if name.startswith("_dst_predicate_")]
    assert reserved == ["_dst_predicate_0", "_dst_predicate_1"]


def _make_scalar_specimen(
    label: str,
    parent: scalar_models.ScalarSpecimen | None = None,
) -> scalar_models.ScalarSpecimen:
    """Create a ``ScalarSpecimen`` with all required non-null scalar fields set."""
    return scalar_models.ScalarSpecimen.objects.create(
        label=label,
        occurred_on=datetime.date(2020, 1, 1),
        occurred_at=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
        occurred_time=datetime.time(1, 2, 3),
        external_id=uuid.uuid4(),
        parent=parent,
    )


@pytest.mark.parametrize(
    "name",
    [
        "title",
        "title__icontains",
        "genres__name__icontains",
        "genres__name__in",
        "loans__note__icontains",
        "loans__id__range",
        "loans__id__gt",
    ],
)
def test_generated_flat_leaves_never_carry_exclude(name: str) -> None:
    """Each generated representative leaf carries provenance and never embeds logical negation."""

    class RepresentativeFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {
                "title": ["exact", "icontains"],
                "genres__name": ["icontains", "in"],
                "loans__note": ["icontains"],
                "loans__id": ["range", "gt"],
            }

    generated = RepresentativeFilter.get_filters()
    assert generated  # the representative leaves were actually produced
    leaf = generated[name]
    assert filter_generation_provenance(leaf) is not None
    assert leaf.exclude is False


@pytest.mark.parametrize("lookup", ["exact", "in"])
def test_flat_relay_m2m_leaf_builds_form_field_without_model_choice_extras(lookup: str) -> None:
    """Each Relay M2M replacement has the plain multiple-choice field class and no model-choice kwargs."""

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class FlatBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact", "in"]}

    generated = FlatBookFilter.get_filters()
    leaf = generated["genres" if lookup == "exact" else "genres__in"]
    assert isinstance(leaf, GlobalIDMultipleChoiceFilter)
    assert _MODEL_CHOICE_ONLY_EXTRAS.isdisjoint(leaf.extra)
    assert isinstance(leaf.field, _GlobalIDMultipleChoiceField)


def test_flat_relay_fk_leaf_builds_form_field_without_model_choice_extras() -> None:
    """The single-valued Relay FK replacement strips the extras too.

    Upstream's FK default carries ``queryset`` AND ``to_field_name`` /
    ``empty_label`` / ``null_label``, none of which ``GlobalIDFilter``'s plain
    ``CharField`` accepts.
    """

    class BookType(DjangoType):
        class Meta:
            model = library_models.Book
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(BookType, BookType.__django_strawberry_definition__)

    class FlatLoanFilter(FilterSet):
        class Meta:
            model = library_models.Loan
            fields = {"book": ["exact"]}

    leaf = FlatLoanFilter.get_filters()["book"]
    assert isinstance(leaf, GlobalIDFilter)
    assert _MODEL_CHOICE_ONLY_EXTRAS.isdisjoint(leaf.extra)
    _ = leaf.field


@pytest.mark.django_db
def test_generated_relay_membership_keeps_candidate_and_outer_query_state() -> None:
    """Relay membership retains candidate eligibility and exact private outer-query ownership."""

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            # ``books`` (reverse M2M -> Book) is excluded so finalization does
            # not demand a registered Book type; the filter targets Genre ids.
            fields = ("id", "name")
            interfaces = (strawberry.relay.Node,)

    finalize_django_types()

    class FlatBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["in"]}

    first = library_models.Genre.objects.create(name="gid-alpha")
    second = library_models.Genre.objects.create(name="gid-beta")
    FlatBookFilter.get_filters()
    snapshot = FlatBookFilter._expansion_snapshot()
    assert snapshot is not None
    assert snapshot.candidates["genres__in"].eligible is True
    result = FlatBookFilter(
        data={"genres__in": [global_id_for(GenreType, saved_pk(row)) for row in (first, second)]},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    assert result.query.distinct is False
    assert "_dst_predicate_0" in result.query.annotations
    outer_tables = {join.table_name for join in result.query.alias_map.values()}
    assert "library_book_genres" not in outer_tables
    assert "library_genre" not in outer_tables


def test_consumer_owned_filters_keep_their_private_query_annotations_clear() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """
    outer = library_models.Book.objects.order_by("id")

    class DeclaredDistinctFilter(FilterSet):
        loan_note = CharFilter(field_name="loans__note", lookup_expr="icontains", distinct=True)

        class Meta:
            model = library_models.Book
            fields = []

    DeclaredDistinctFilter.get_filters()
    declared = DeclaredDistinctFilter(
        data={"loan_note": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs
    assert [n for n in declared.query.annotations if n.startswith("_dst_predicate_")] == []
    assert declared.query.distinct is True

    class MethodFilter(FilterSet):
        loan_note = CharFilter(method="filter_note")

        class Meta:
            model = library_models.Book
            fields = []

        def filter_note(
            self,
            queryset: QuerySet[library_models.Book],
            _name: str,
            value: object,
        ) -> QuerySet[library_models.Book]:
            return queryset.filter(loans__note__icontains=value).distinct()

    MethodFilter.get_filters()
    method = MethodFilter(
        data={"loan_note": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs
    assert [n for n in method.query.annotations if n.startswith("_dst_predicate_")] == []

    class CustomLoanNoteFilter(CharFilter):
        """A declared custom ``CharFilter`` subclass (ineligible: not generated)."""

    class CustomSubclassFilter(FilterSet):
        loan_note = CustomLoanNoteFilter(
            field_name="loans__note",
            lookup_expr="icontains",
            distinct=True,
        )

        class Meta:
            model = library_models.Book
            fields = []

    CustomSubclassFilter.get_filters()
    custom = CustomSubclassFilter(
        data={"loan_note": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs
    assert [n for n in custom.query.annotations if n.startswith("_dst_predicate_")] == []

    def _override_extra(_f: object) -> dict[str, object]:
        return {"lookup_expr": "icontains"}

    class OverridesFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}
            filter_overrides = {
                library_models.Loan._meta.get_field("note").__class__: {
                    "filter_class": CharFilter,
                    "extra": _override_extra,
                },
            }

    OverridesFilter.get_filters()
    overridden = OverridesFilter(
        data={"loans__note__icontains": "cardio"},
        queryset=outer,
        request=HttpRequest(),
    ).qs
    assert [n for n in overridden.query.annotations if n.startswith("_dst_predicate_")] == []


_BOOK_GENRE_LEAF_SHAPES = ("routed", "branch")


def _apply_book_genre_leaf(
    queryset: QuerySet[library_models.Book],
    shape: str,
) -> QuerySet[library_models.Book]:
    """Apply the ``genres__name`` icontains leaf via the consumer-shaped-queryset seam.

    Constructing the filter set with ``queryset=<shaped input>`` is exactly the
    consumer-shaped-queryset seam production uses; form validation is
    transparent (the flat leaf name is a valid form key). ``shape`` picks the
    routed traversal or the ``BookFilter`` expansion that runs as its branch.
    """
    if shape == "routed":

        class RoutedBookGenreFilter(FilterSet):
            class Meta:
                model = library_models.Book
                fields = {"genres__name": ["icontains"]}

        filterset_cls = RoutedBookGenreFilter
    else:
        _register_plain_types(library_models.Genre)
        filterset_cls = BookFilter
    filterset_cls.get_filters()
    return filterset_cls(
        data={"genres__name__icontains": "cardio"},
        queryset=queryset,
        request=HttpRequest(),
    ).qs


@pytest.mark.django_db
@pytest.mark.parametrize("shape", _BOOK_GENRE_LEAF_SHAPES)
def test_non_fanned_input_keeps_the_query_distinct_flag_off(shape: str) -> None:
    """The raw Query distinct flag survives the framework restriction."""
    result = _apply_book_genre_leaf(library_models.Book.objects.order_by("id"), shape)
    assert result.query.distinct is False


@pytest.mark.django_db
@pytest.mark.parametrize("shape", _BOOK_GENRE_LEAF_SHAPES)
def test_pre_fanned_input_keeps_the_query_distinct_flag_off(shape: str) -> None:
    """The raw Query distinct flag survives the framework restriction."""
    shaped = library_models.Book.objects.filter(genres__name__icontains="o").order_by("id")
    result = _apply_book_genre_leaf(shaped, shape)
    assert result.query.distinct is False


@pytest.mark.django_db
@pytest.mark.parametrize("shape", _BOOK_GENRE_LEAF_SHAPES)
def test_consumer_distinct_query_flag_is_preserved(shape: str) -> None:
    """The raw Query distinct flag survives the explicit consumer DISTINCT."""
    shaped = (
        library_models.Book.objects.filter(genres__name__icontains="o").order_by("id").distinct()
    )
    result = _apply_book_genre_leaf(shaped, shape)
    assert result.query.distinct is True


@pytest.mark.django_db
@pytest.mark.parametrize("shape", _BOOK_GENRE_LEAF_SHAPES)
def test_custom_filter_input_keeps_the_query_distinct_flag_off(shape: str) -> None:
    """The raw Query distinct flag survives the framework restriction."""

    class ConsumerFanFilter(FilterSet):
        genres_fan = CharFilter(
            field_name="genres__name",
            lookup_expr="icontains",
            distinct=False,
        )

        class Meta:
            model = library_models.Book
            fields = []

    ConsumerFanFilter.get_filters()
    shaped = ConsumerFanFilter(
        data={"genres_fan": "cardio"},
        queryset=library_models.Book.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    result = _apply_book_genre_leaf(shaped, shape)
    assert result.query.distinct is False


def _routed_deep_loan_filter() -> type[FilterSet]:
    """A ``Loan`` filter set whose deep ``book__loans__patron__email`` leaf routes."""

    class RoutedDeepLoanFilter(FilterSet):
        class Meta:
            model = library_models.Loan
            fields = {"book__loans__patron__email": ["icontains"]}

    return RoutedDeepLoanFilter


@pytest.mark.django_db
def test_generated_deep_loan_query_keeps_only_the_outer_root_alias() -> None:
    """A generated deep predicate keeps the raw outer alias map rooted only in Loan."""
    DeepLoanFilter = _routed_deep_loan_filter()
    DeepLoanFilter.get_filters()
    result = DeepLoanFilter(
        data={"book__loans__patron__email__icontains": "Cardio"},
        queryset=library_models.Loan.objects.order_by("id"),
        request=HttpRequest(),
    ).qs
    root_tables = [join.table_name for join in result.query.alias_map.values()]
    assert root_tables == ["library_loan"]
    assert "library_patron" not in root_tables
    assert result.query.distinct is False


def test_request_from_info_uses_context_request_attribute() -> None:
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    request = HttpRequest()
    info = _make_info(request)
    assert CategoryFilter._request_from_info(info) is request


def test_request_from_info_falls_back_to_bare_http_request() -> None:
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    class _Info:
        def __init__(self) -> None:
            super().__init__()
            self.context = HttpRequest()

    info = _Info()
    assert CategoryFilter._request_from_info(info) is info.context


def test_normalize_input_returns_empty_dict_for_none() -> None:
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._normalize_input(None) == {}


def test_normalize_input_skips_none_valued_attrs() -> None:
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"], "description": ["icontains"]}

    data = CategoryFilter._normalize_input({"name": None, "description": {"i_contains": "foo"}})
    assert data == {"description__icontains": "foo"}


def test_normalize_input_maps_in_python_attr_to_in_form_data_key() -> None:
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["in"]}

    data = CategoryFilter._normalize_input({"name": {"in_": ["a", "b"]}})
    assert data == {"name__in": ["a", "b"]}


def test_normalize_input_maps_logic_keys_to_short_form() -> None:
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input(
        {"and_": [{"name": "foo"}], "or_": [{"name": "bar"}], "not_": {"name": "baz"}},
    )
    assert data["and"] == [{"name": "foo"}]
    assert data["or"] == [{"name": "bar"}]
    assert data["not"] == {"name": "baz"}


def test_normalize_input_walks_strawberry_dataclass() -> None:
    """A dataclass-shaped input (Strawberry input) is walked via `__dataclass_fields__`."""

    @strawberry.input
    class _Input:
        # basedpyright: Strawberry types UNSET Any; an input field defaults to it under its
        # declared GraphQL annotation, which no typed sentinel satisfies
        name: str | None = strawberry.UNSET  # pyright: ignore[reportAny]

    value = _Input(name="hello")
    # `__dataclass_fields__` carries the declared field names.

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input(value)
    assert data.get("name") == "hello"


def test_normalize_input_inner_bag_loop_skips_unset_lookups() -> None:
    """Partial operator bags don't leak ``UNSET`` into form data.

    Strawberry input dataclasses default every operator-bag lookup
    (``exact``, ``i_contains``, ``in_``, ...) to ``UNSET`` rather than
    ``None``. The inner loop in ``_normalize_input`` must skip UNSET
    the same way the outer loop does; otherwise the UNSET sentinel
    reaches ``normalize_input_value`` and either raises
    ``TypeError: argument of type 'UNSET' is not iterable`` (list-like
    filters) or lands in ``data[form_key]`` as a bogus value (scalar
    filters). The common case is a consumer who supplies one lookup
    but not the others - partially-supplied bags must not break.
    """

    @strawberry.input
    class _Bag:
        # basedpyright: Strawberry types UNSET Any; an input field defaults to it under its
        # declared GraphQL annotation, which no typed sentinel satisfies
        exact: str | None = strawberry.UNSET  # pyright: ignore[reportAny]
        # basedpyright: Strawberry types UNSET Any; an input field defaults to it under its
        # declared GraphQL annotation, which no typed sentinel satisfies
        i_contains: str | None = strawberry.UNSET  # pyright: ignore[reportAny]

    @strawberry.input
    class _Input:
        # basedpyright: Strawberry types UNSET Any; an input field defaults to it under its
        # declared GraphQL annotation, which no typed sentinel satisfies
        name: _Bag | None = strawberry.UNSET  # pyright: ignore[reportAny]

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    # Bag with only ``i_contains`` supplied; ``exact`` defaults to UNSET.
    bag = _Bag(i_contains="foo")
    data = CategoryFilter._normalize_input(_Input(name=bag))
    # The UNSET ``exact`` does NOT pollute form-data as ``name=UNSET``.
    assert "name" not in data
    # The supplied ``i_contains`` lands at its django-filter form key.
    assert data.get("name__icontains") == "foo"


def test_normalize_input_skips_strawberry_unset_attrs() -> None:
    """``strawberry.UNSET`` attrs are skipped the same as ``None``.

    Strawberry input dataclasses default unsupplied fields to ``UNSET``
    rather than ``None``. Leaving them in ``data`` would route them
    through the parent form and surface as a spurious "missing /
    invalid" form error for fields the consumer never sent.
    """

    @strawberry.input
    class _Input:
        # basedpyright: Strawberry types UNSET Any; an input field defaults to it under its
        # declared GraphQL annotation, which no typed sentinel satisfies
        name: str | None = strawberry.UNSET  # pyright: ignore[reportAny]

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input(_Input())
    assert "name" not in data


def test_run_permission_checks_fires_only_for_active_input_fields() -> None:
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, _request: object) -> None:
            fired.append("name")

    CategoryFilter._run_permission_checks({}, request=HttpRequest())
    assert fired == []

    CategoryFilter._run_permission_checks({"name": "anything"}, request=HttpRequest())
    assert fired == ["name"]


def test_run_permission_checks_skips_unset_related_branch() -> None:
    """``strawberry.UNSET`` on a related branch is treated as "not supplied".

    Strawberry input dataclasses default unsupplied fields to ``UNSET``
    rather than ``None``. The active-branch detection in
    ``_iter_active_related_branches`` must collapse UNSET so the parent
    per-branch permission gate does not fire for fields the consumer
    never sent.
    """
    fired: list[str] = []

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    @strawberry.input
    class BranchInput:
        # basedpyright: Strawberry types UNSET Any; an input field defaults to it under its
        # declared GraphQL annotation, which no typed sentinel satisfies
        name: str | None = strawberry.UNSET  # pyright: ignore[reportAny]
        # basedpyright: Strawberry types UNSET Any; an input field defaults to it under its
        # declared GraphQL annotation, which no typed sentinel satisfies
        shelves: object = strawberry.UNSET  # pyright: ignore[reportAny]

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def check_shelves_permission(self, _request: object) -> None:
            fired.append("shelves")

    BranchFilter._run_permission_checks(BranchInput(), request=HttpRequest())
    assert fired == []


def test_run_permission_checks_recurses_into_active_related_branch() -> None:
    fired: list[str] = []

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def check_code_permission(self, _request: object) -> None:
            fired.append("shelf.code")

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    BranchFilter._run_permission_checks({"name": "x"}, request=HttpRequest())
    assert fired == []

    BranchFilter._run_permission_checks(
        {"shelves": {"code": "anything"}},
        request=HttpRequest(),
    )
    assert "shelf.code" in fired


@pytest.mark.parametrize(
    "logic_input",
    [
        {"and_": [{"name": "foo"}, {"name": "bar"}]},
        {"or_": [{"name": "foo"}, {"name": "bar"}]},
        {"not_": {"name": "baz"}},
    ],
    ids=["and", "or", "not"],
)
def test_run_permission_checks_recurses_into_logical_branches(
    logic_input: dict[str, object],
) -> None:
    """Per-call dedup: a gate fires once even when the field appears in many branches.

    The recursion correctly walks ``and`` / ``or`` / ``not`` sub-trees
    so a nested field is gated the same as a top-level one. The dedup
    keys on ``check_<field>_permission`` method names for the lifetime
    of one top-level call; a field appearing in multiple ``or`` arms
    fires its gate ONCE per call (the gate's logic is idempotent, so
    multi-firing is functionally harmless but produces duplicate audit
    log entries - the R4 contract dedupes to avoid that).
    """
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, _request: object) -> None:
            fired.append("name")

    CategoryFilter._run_permission_checks(logic_input, request=HttpRequest())
    assert fired == ["name"]
    CategoryFilter._run_permission_checks(logic_input, request=HttpRequest())
    assert fired == ["name", "name"]


@pytest.mark.parametrize(
    ("logic_input", "message"),
    list(
        zip(
            [{"or_": {"name": "foo"}}, {"and_": ["bad_scalar"]}, {"not_": [{"name": "foo"}]}],
            [
                "takes a list of filter inputs",
                "must be a mapping or filter-input",
                "takes a single filter input",
            ],
            strict=True,
        ),
    ),
    ids=["mapping-for-sequence", "scalar-element", "sequence-for-single"],
)
def test_run_permission_checks_rejects_malformed_logical_branch_before_hooks(
    logic_input: dict[str, object],
    message: str,
) -> None:
    """Malformed logical input is rejected before check_*_permission gates fire."""
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, _request: object) -> None:
            fired.append("name")

    with pytest.raises(ConfigurationError, match=message):
        CategoryFilter._run_permission_checks(logic_input, request=HttpRequest())
    assert fired == []


def test_run_permission_checks_dedups_child_gate_across_sibling_branches() -> None:
    """A child filterset gate fires once even when entered from sibling ``or`` arms.

    The ``_fired`` map is keyed by ``FilterSet`` class and shared across
    BOTH the logical-branch recursion and the child-filterset recursion.
    So ``or: [{shelves: {...}}, {shelves: {...}}]`` enters ``ShelfFilter``
    twice (once per arm) but its ``check_code_permission`` fires only
    once - the per-class set keyed on ``ShelfFilter`` dedups the second
    entry. The parent's per-branch ``check_shelves_permission`` likewise
    fires once (deduped on the parent's per-class set).
    """
    fired: list[str] = []

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def check_code_permission(self, _request: object) -> None:
            fired.append("shelf.code")

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def check_shelves_permission(self, _request: object) -> None:
            fired.append("branch.shelves")

    BranchFilter._run_permission_checks(
        {
            "or_": [{"shelves": {"code": "a"}}, {"shelves": {"code": "b"}}],
        },
        request=HttpRequest(),
    )
    # Parent per-branch gate fires once; child class gate fires once -
    # NOT once per arm.
    assert fired.count("branch.shelves") == 1
    assert fired.count("shelf.code") == 1


@pytest.mark.django_db
def test_evaluate_logic_tree_preserves_request_context() -> None:
    captured_requests: list[object] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        @override
        def filter_queryset(self, queryset: QuerySet[_M]) -> QuerySet[_M]:
            captured_requests.append(self.request)
            return super().filter_queryset(queryset)

    request = HttpRequest()
    info = _make_info(request)
    CategoryFilter.apply_sync(
        {"and_": [{"name": "alpha"}]},
        Category.objects.all(),
        info,
    )
    assert captured_requests
    # First entry in captured_requests is from the parent category filter,
    # and subsequent are from the nested logic branch evaluation.
    # All of them must preserve the same HttpRequest object.
    assert all(req is request for req in captured_requests)


def test_permission_checks_run_only_through_apply_entrypoint() -> None:
    """``apply_*`` is the sole permission-aware entry; the bare ``.qs`` path does not gate.

    Permission hooks fire from ``_run_permission_checks``, which
    ``apply_sync`` / ``apply_async`` invoke up-front (recursing into nested
    branches). The tree-composition path
    (``filter_queryset`` -> ``_q_for_branch`` -> ``.qs``) deliberately does
    NOT re-run permission checks -- it relies on that up-front call. This
    pins the contract: bypassing
    ``apply_*`` by constructing the filterset and reading ``.qs`` directly
    skips the gate, so ``apply_*`` must remain the only permission-aware
    entry point. If a future refactor moves filtering off ``apply_*`` this
    test fails loudly, so permissions are re-wired rather than silently lost.
    """
    fired: list[str] = []

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def check_name_permission(self, _request: object) -> None:
            fired.append("name")

    BranchFilter.apply_sync({"name": "alpha"}, library_models.Branch.objects.none(), _make_info())
    assert fired == ["name"]
    fired.clear()
    bare = BranchFilter(
        data={"name": "alpha"},
        queryset=library_models.Branch.objects.none(),
        request=HttpRequest(),
    )
    list(bare.qs)
    assert fired == []


@pytest.mark.parametrize(
    ("filter_input", "expected"),
    [
        pytest.param({"shelves": {"code": {"exact": "AAA"}}}, ["branch.shelves"], id="one-hop"),
        pytest.param(
            {"shelves": {"books": {"title": {"i_contains": "T"}}}},
            ["branch.shelves", "shelf.books", "title"],
            id="two-hops",
        ),
    ],
)
def test_apply_sync_nested_related_gate_fires_once_not_per_level(
    filter_input: dict[str, object],
    expected: list[str],
) -> None:
    """A nested ``RelatedFilter`` child gate fires exactly once through ``apply_sync``.

    Call-count has no wire shape. Nested denial over HTTP:
    ``test_products_api.py::test_products_items_related_category_name_permission_fires_for_anonymous``.

    The related-visibility derivation invokes the child filterset's
    ``apply_*``, and the top-level dedicated ``_run_permission_checks`` pass
    ALSO recurses into the child. Were the child to run its own
    ``_run_permission_checks`` too, a nested ``check_<field>_permission`` gate
    would fire once per enclosing level (twice at one level of relation
    nesting, three times at two levels, compounding with depth), breaking the
    documented contract that the derivation / tree-composition paths do NOT
    re-run permission checks (only the single up-front pass fires gates) and
    double-invoking side-effectful gates (audit logging, rate limiting,
    metrics). The derivation threads ``run_permissions=False`` into the
    child's ``apply_*`` calls so the child's gates fire only via the top-level
    pass.
    """
    fired: list[str] = []

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    assert registry.get(library_models.Shelf) is ShelfType

    class BookType(DjangoType):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")

    assert registry.get(library_models.Book) is BookType

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact", "icontains"]}

        def check_title_permission(self, _request: object) -> None:
            fired.append("title")

    class ShelfFilter(FilterSet):
        books = RelatedFilter(BookFilter, field_name="books")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def check_books_permission(self, _request: object) -> None:
            fired.append("shelf.books")

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def check_shelves_permission(self, _request: object) -> None:
            fired.append("branch.shelves")

    BranchFilter.apply_sync(filter_input, library_models.Branch.objects.all(), _make_info())
    assert sorted(fired) == sorted(expected)


def test_apply_async_nested_related_gate_fires_once() -> None:
    """The async related derivation invokes the nested gate exactly once.

    Only the private callback count remains. HTTP denial and successful filtering
    belong to test_filter_apply_arguments_api.py and test_products_api.py.
    """
    fired: list[str] = []

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    assert registry.get(library_models.Shelf) is ShelfType

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact", "icontains"]}

        def check_code_permission(self, _request: object) -> None:
            fired.append("code")

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    asyncio.run(
        BranchFilter.apply_async(
            {"shelves": {"code": {"i_contains": "AAA"}}},
            library_models.Branch.objects.all(),
            _make_info(),
        ),
    )
    assert fired == ["code"]


@pytest.mark.django_db
def test_apply_sync_passes_constrained_queryset_to_filterset_instance() -> None:
    """Pipeline ordering - constraints land in `self.queryset`.

    `apply_sync` must apply `_apply_related_constraints` BEFORE
    constructing the `FilterSet` instance so the explicit
    `RelatedFilter(queryset=...)` ledger and the visibility queryset
    propagate through to `.qs` via `self.queryset`. A future refactor
    that instantiates first and mutates `self._queryset` afterwards
    would not carry the constraint through `BaseFilterSet`'s internal
    `filter_queryset` path; this test pins the order.
    """
    branch = library_models.Branch.objects.create(name="alpha")
    library_models.Shelf.objects.create(branch=branch, code="active")

    explicit_qs = library_models.Shelf.objects.filter(code="active")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class ShelfType(DjangoType):
        """Registered target so the active ``shelves`` branch resolves."""

        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    assert registry.get(library_models.Shelf) is ShelfType

    captured: dict[str, list[QuerySet[django_models.Model] | None]] = {}
    real_init = FilterSet.__init__

    def spy_init(
        self: FilterSet,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[django_models.Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        # Record the `queryset` kwarg every consumer-`FilterSet` subclass
        # receives during this call. The active `shelves` branch's
        # visibility scoping constructs the child `ShelfFilter` first
        # (its `apply_sync` runs during `_derive_related_visibility_*`),
        # so the calls list interleaves child + parent constructions; the
        # test selects the parent (Branch-model) call by queryset model
        # rather than assuming a position.
        captured.setdefault("calls", []).append(queryset)
        real_init(self, data=data, queryset=queryset, request=request, prefix=prefix)

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves", queryset=explicit_qs)

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    FilterSet.__init__ = spy_init
    try:
        # Related-branch keys are stripped from the form-data dict
        # before form validation (`shelves` is owned by
        # `_apply_related_constraints`, not the parent's form), so
        # `apply_sync` returns normally. The contract this test
        # pins: the constructor's `queryset=` kwarg must
        # carry the `<rel>__in=<intersected>` clause already baked in.
        BranchFilter.apply_sync(
            {"shelves": {"code": "active"}},
            library_models.Branch.objects.all(),
            _make_info(),
        )
    finally:
        FilterSet.__init__ = real_init

    # Select the parent (Branch-model) construction; child ShelfFilter
    # constructions from the visibility-scoping pass also land in `calls`.
    parent_querysets = [
        qs for qs in captured["calls"] if qs is not None and qs.model is library_models.Branch
    ]
    assert parent_querysets, "BranchFilter was never constructed with a queryset kwarg"
    parent_queryset = parent_querysets[0]
    # The constrained queryset reached `BranchFilter.__init__` BEFORE the
    # filterset was constructed; the SQL carries the branch's correlated
    # `EXISTS` restriction that `_apply_related_constraints` baked in.
    sql = str(parent_queryset.query).lower()
    assert "library_shelf" in sql
    assert "active" in sql


def test_get_filters_skips_none_target_related_filter() -> None:
    """A ``RelatedFilter(None, ...)`` placeholder expands to nothing.

    ``_expand_related_filter`` returns an empty mapping when the target
    filterset is unresolved (``None``), so no ``<rel>__<lookup>`` keys
    leak into ``get_filters()``.
    """

    class PlaceholderFilter(FilterSet):
        rel = RelatedFilter(None, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    filters = PlaceholderFilter.get_filters()
    assert not any(name.startswith("rel__") for name in filters)


@pytest.mark.parametrize(
    "value",
    [object()],
    ids=["object"],
)
def test_normalize_input_rejects_an_opaque_python_object(value: object) -> None:
    """An opaque Python object has no JSON or input-dataclass mapping protocol."""

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError, match=r"skip every check_\* permission gate"):
        BranchFilter._normalize_input(value)


@pytest.mark.parametrize(
    ("shape", "expected"),
    [
        pytest.param("package-scalar", {"fines_0": 1, "fines_1": 5}, id="package-scalar"),
        pytest.param(
            "upstream-scalar",
            {"upstream_fines_min": 1, "upstream_fines_max": 5},
            id="upstream-scalar",
        ),
        pytest.param(
            "operator-bag",
            {"lifetime_fines_cents__range_0": 1, "lifetime_fines_cents__range_1": 5},
            id="operator-bag",
        ),
    ],
)
def test_range_patch_dict_values_still_merge_their_widget_keys(
    shape: str,
    expected: dict[str, int],
) -> None:
    """Each range normalizer merges its patch under the keys its own widget reads.

    The scalar and operator-bag entry paths both keep their range-filter exemption from
    dict-valued scalar rejection, including django-filter's distinct min/max suffixes.
    """

    @dataclasses.dataclass
    class _NameBag:
        range: object = None

    class PatronFilter(FilterSet):
        fines = RangeFilter(field_name="lifetime_fines_cents")
        upstream_fines = django_filters.RangeFilter(field_name="lifetime_fines_cents")
        lifetime_fines_cents__range = RangeFilter(
            field_name="lifetime_fines_cents",
            lookup_expr="range",
        )

        class Meta:
            model = library_models.Patron
            fields = []

    inputs: dict[str, dict[str, object]] = {
        "package-scalar": {"fines": {"start": 1, "end": 5}},
        "upstream-scalar": {"upstream_fines": {"start": 1, "end": 5}},
        "operator-bag": {
            "lifetime_fines_cents_range": _NameBag(range={"start": 1, "end": 5}),
        },
    }
    assert PatronFilter._normalize_input(inputs[shape]) == expected


#: The refusal a temporal value the queryset's database cannot bind answers.
_UNBINDABLE = [{"message": "Enter a value the database can represent.", "code": "invalid"}]


_PLUS_FIVE = datetime.timezone(datetime.timedelta(hours=5))


#: A datetime projecting into year 0, a bindable datetime, and an aware time.
_BEFORE_YEAR_ONE = datetime.datetime(1, 1, 1, tzinfo=_PLUS_FIVE)


_BINDABLE_DATETIME = datetime.datetime(2021, 6, 15, 9, 30, tzinfo=datetime.timezone.utc)


_AWARE_TIME = datetime.time(9, 30, tzinfo=datetime.timezone.utc)


def _temporal_filter_class() -> type[FilterSet]:
    """Only the temporal declarations used by validation-only internal observations.

    Real declared filter families and their backend verdicts live in
    ``test_declared_temporal_bindability_api.py``, ``test_explicit_temporal_arguments_api.py``
    and ``test_scalar_predicate_binding_api.py``.
    """

    class SpecimenFilter(FilterSet):
        taken_before = django_filters.DateTimeFilter(field_name="occurred_at", lookup_expr="lt")
        clock_time = django_filters.TimeFilter(field_name="occurred_at__time")
        mixed_below = django_filters.NumberFilter(field_name="mixed", lookup_expr="lt")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    return SpecimenFilter


def _specimens_with_unresolved_output() -> QuerySet[scalar_models.ScalarSpecimen]:
    """An unresolved decimal/float sum used only by validation-time observations.

    Django cannot execute this expression without an explicit output field.
    """
    return scalar_models.ScalarSpecimen.objects.annotate(
        mixed=models.F("price") + models.F("score"),
    )


@pytest.mark.django_db
def test_an_annotation_without_an_output_field_has_no_bind_target() -> None:
    """An unresolved output expression supplies no column to the validator's bind ask.

    This is validation-only: Django cannot execute the mixed decimal/float expression
    without an explicit output field. Bindable consumer declarations are exercised by
    the native HTTP rows in ``test_declared_temporal_bindability_api.py`` and
    ``test_explicit_temporal_arguments_api.py``.
    """
    specimen_filter = _temporal_filter_class()
    filterset = specimen_filter(
        data={"mixed_below": 5},
        queryset=_specimens_with_unresolved_output(),
    )
    specimen_filter._validate_form_or_raise(filterset)


def _specimens_in_years() -> dict[str, scalar_models.ScalarSpecimen]:
    """Four specimens by label, each dated on its date and datetime column alike.

    ``new-year-2021`` falls on 2021-01-01, a Friday in ISO week 53 of 2020, so its
    ``iso_year`` is 2020 where its ``year`` is 2021.
    """
    days = {
        "mid-2019": datetime.date(2019, 6, 15),
        "mid-2020": datetime.date(2020, 6, 15),
        "new-year-2021": datetime.date(2021, 1, 1),
        "mid-2022": datetime.date(2022, 6, 15),
    }
    return {
        label: scalar_models.ScalarSpecimen.objects.create(
            label=label,
            occurred_on=day,
            occurred_at=datetime.datetime.combine(
                day,
                datetime.time(12),
                tzinfo=datetime.timezone.utc,
            ),
            occurred_time=datetime.time(12),
            external_id=uuid.uuid4(),
        )
        for label, day in days.items()
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("data", "labels"),
    [
        pytest.param({"years_among": [2020, 2022]}, ["mid-2020", "mid-2022"], id="list-in"),
        pytest.param({"days_among": [datetime.date(2021, 1, 1)]}, ["new-year-2021"], id="date-in"),
        pytest.param(
            {"years_span_0": 2019, "years_span_1": 2020},
            ["mid-2019", "mid-2020"],
            id="range",
        ),
    ],
)
def test_declared_filter_through_a_lookup_expr_transform_cleans_values_as_its_output(
    data: dict[str, object],
    labels: list[str],
) -> None:
    """A ``ListFilter`` / ``RangeFilter`` whose ``lookup_expr`` carries a transform cleans its output.

    Each member or bound is a value of the transform's output (``year``'s ``IntegerField``,
    ``date``'s ``DateField``), the type its input is published as, so it is cleaned as one
    and filters by it, never refused by the datetime column's own form field.
    """

    class TransformLookupFilter(FilterSet):
        years_among = ListFilter(field_name="occurred_at", lookup_expr="year__in")
        days_among = ListFilter(field_name="occurred_at", lookup_expr="date__in")
        years_span = RangeFilter(field_name="occurred_at", lookup_expr="year__range")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    _ = _specimens_in_years()
    filterset = TransformLookupFilter(
        data=data,
        queryset=scalar_models.ScalarSpecimen.objects.order_by("occurred_at"),
    )

    TransformLookupFilter._validate_form_or_raise(filterset)
    assert list(filterset.qs.values_list("label", flat=True)) == labels


#: UTC offsets PostgreSQL refuses: 16:00 or more either way, and (bound as text, as Django's
#: default psycopg cursor binds) a fraction of a second.
_PLUS_SIXTEEN = datetime.timezone(datetime.timedelta(hours=16))


_MINUS_SIXTEEN = datetime.timezone(datetime.timedelta(hours=-16))


_HALF_SECOND_OFFSET = datetime.timezone(datetime.timedelta(hours=1, microseconds=500_000))


_AT_PLUS_SIXTEEN = datetime.datetime(2021, 6, 16, 1, 30, tzinfo=_PLUS_SIXTEEN)


_AT_MINUS_SIXTEEN = datetime.datetime(2021, 6, 14, 17, 30, tzinfo=_MINUS_SIXTEEN)


_AT_HALF_SECOND_OFFSET = datetime.datetime(2021, 6, 15, 10, 30, tzinfo=_HALF_SECOND_OFFSET)


#: An hour past ``_BINDABLE_DATETIME``: Django's ``In`` drops a member equal to an earlier one,
#: so an ``in`` list's refused member must name its own instant to reach the database.
_HOUR_LATER_AT_PLUS_SIXTEEN = datetime.datetime(2021, 6, 16, 2, 30, tzinfo=_PLUS_SIXTEEN)


class _RefusingOperations(SQLiteOperations):
    """SQLite's operations, whose datetime adapter refuses every value, as a backend's own refusal does."""

    @override
    def adapt_datetimefield_value(self, value: datetime.datetime | None) -> str | None:
        raise ValueError(value)


class _BindingOperations(SQLiteOperations):
    """SQLite's operations, whose datetime adapter binds every value it is handed."""

    @override
    def adapt_datetimefield_value(self, value: datetime.datetime | None) -> str | None:
        return None if value is None else value.isoformat()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("operations", "value", "refused"),
    [
        pytest.param(_RefusingOperations, _BINDABLE_DATETIME, True, id="refusing-database"),
        pytest.param(_BindingOperations, _BEFORE_YEAR_ONE, False, id="binding-database"),
    ],
)
def test_temporal_value_is_held_to_the_database_the_queryset_runs_on(
    operations: type[BaseDatabaseOperations],
    value: datetime.datetime,
    refused: bool,  # noqa: FBT001
) -> None:
    """The rule asks the connection of the queryset's own alias, not ``default``'s.

    On a stand-in alias whose adapter refuses every datetime, one ``default`` binds is
    refused; on one whose adapter binds every datetime, one the SQLite, MySQL and Oracle
    adapters refuse passes.
    """
    alias = "temporal_stand_in"
    wrapper = connections.create_connection(DEFAULT_DB_ALIAS)
    wrapper.ops = operations(wrapper)
    connections[alias] = wrapper
    specimen_filter = _temporal_filter_class()
    try:
        filterset = specimen_filter(
            data={"taken_before": value},
            queryset=_specimens_with_unresolved_output().using(alias),
        )
        if not refused:
            specimen_filter._validate_form_or_raise(filterset)
            return
        with pytest.raises(GraphQLError) as excinfo:
            specimen_filter._validate_form_or_raise(filterset)
    finally:
        del connections[alias]
    assert excinfo.value.extensions == {
        "code": "FILTER_INVALID",
        "errors": {"taken_before": _UNBINDABLE},
    }


class _RecordingRouter:
    """A database router recording each model it is asked to route a read for."""

    def __init__(self) -> None:
        self.asked: list[type[models.Model]] = []

    def db_for_read(self, model: type[models.Model], **_hints: object) -> None:
        self.asked.append(model)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("data", "asked"),
    [
        pytest.param({"label": "alpha"}, [], id="non-temporal"),
        pytest.param(
            {"occurred_at": _BINDABLE_DATETIME},
            [scalar_models.ScalarSpecimen],
            id="temporal",
        ),
    ],
)
def test_queryset_alias_is_resolved_only_for_a_temporal_leaf(
    data: dict[str, object],
    asked: list[type[models.Model]],
) -> None:
    """The queryset's alias, which asks the router, is read only when a leaf is temporal."""

    class SpecimenFilter(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"label": ["exact"], "occurred_at": ["exact"]}

    router = _RecordingRouter()
    with override_settings(DATABASE_ROUTERS=[router]):
        filterset = SpecimenFilter(data=data, queryset=scalar_models.ScalarSpecimen.objects.all())

        SpecimenFilter._validate_form_or_raise(filterset)
    assert router.asked == asked


def _recording_override(kind: str, applied: list[object]) -> type[django_filters.DateTimeFilter]:
    """A consumer ``DateTimeFilter`` subclass whose class-level ``filter`` records each value.

    ``method`` overrides it with a plain method, ``staticmethod`` with a static method and
    ``type`` with a plain function, the last two in a class built at runtime by ``type()``.
    """

    def record(qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        applied.append(value)
        return qs

    if kind == "staticmethod":
        return type(
            "StaticRecording",
            (django_filters.DateTimeFilter,),
            {"filter": staticmethod(record)},
        )
    if kind == "type":

        def bound_record(_self: object, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            return record(qs, value)

        return type("DynamicRecording", (django_filters.DateTimeFilter,), {"filter": bound_record})

    class MethodRecording(django_filters.DateTimeFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            return record(qs, value)

    return MethodRecording


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["method", "staticmethod", "type"])
def test_a_class_level_filter_override_is_not_invoked_during_form_validation(kind: str) -> None:
    """Validation leaves the exact private invocation list empty before queryset filtering.

    The method, static-method and type-built override declarations retain this timing
    observation: an HTTP response cannot expose the list before queryset filtering.
    Their real payload and single approval-table read are exercised over
    HTTP by ``test_scalar_predicate_binding_api.py``.
    """
    applied: list[object] = []
    recording = _recording_override(kind, applied)

    class RecordingFilter(FilterSet):
        day_of = recording(field_name="occurred_at", lookup_expr="date")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    filterset = RecordingFilter(
        data={"day_of": _BEFORE_YEAR_ONE},
        queryset=scalar_models.ScalarSpecimen.objects.all(),
    )

    RecordingFilter._validate_form_or_raise(filterset)
    assert applied == []


@pytest.mark.django_db
def test_value_is_asked_free_of_the_querysets_slice() -> None:
    """A sliced queryset is asked without its slice, so a bindable value passes.

    Django refuses to filter a sliced queryset (``TypeError``); the ask builds the
    filter's clause on a copy holding no slice, so that refusal never reads as an
    unbindable value.
    """
    specimen_filter = _temporal_filter_class()
    filterset = specimen_filter(
        data={"taken_before": _BINDABLE_DATETIME},
        queryset=_specimens_with_unresolved_output()[:5],
    )

    specimen_filter._validate_form_or_raise(filterset)


class _ChildCustomizingSpecimenFilter(FilterSet):
    """A specimen filterset whose ``__init__`` override projects its filters onto a parent."""

    instant_day_of = django_filters.DateTimeFilter(field_name="occurred_at", lookup_expr="date")
    own_day_of = django_filters.DateTimeFilter(
        field_name="occurred_at",
        lookup_expr="date",
        method="keep_every_row",
    )

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = []

    @override
    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[dj_models.Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)

    def keep_every_row(
        self,
        queryset: QuerySet[scalar_models.ScalarSpecimen],
        _name: str,
        _value: object,
    ) -> QuerySet[scalar_models.ScalarSpecimen]:
        return queryset


@pytest.mark.parametrize("form_key", ["partner__instant_day_of", "partner__own_day_of"])
def test_a_child_init_override_constructs_projected_filter_copies(form_key: str) -> None:
    """A child initializer's projected copy has the package's exact internal wrapper class.

    A response cannot expose this class identity. Runtime date and consumer-method
    behavior, including the method's approval-table cost, is exercised over HTTP in
    ``test_scalar_predicate_binding_api.py``.
    """

    class PartnerParent(FilterSet):
        partner = RelatedFilter(_ChildCustomizingSpecimenFilter, field_name="partner")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    assert isinstance(PartnerParent.get_filters()[form_key], ProjectedChildFilter)


@pytest.mark.parametrize("mode", list(BINDING_MODES))
@pytest.mark.parametrize(
    (
        "data",
        "form_key",
        "refused_as_text",
        "refused_on_server",
    ),
    [
        pytest.param(
            {"clock_time": datetime.time(12, tzinfo=_PLUS_SIXTEEN)},
            "clock_time",
            True,
            True,
            id="time-transform-16-00",
        ),
        pytest.param(
            {"clock_time": datetime.time(12, tzinfo=_HALF_SECOND_OFFSET)},
            "clock_time",
            True,
            False,
            id="time-transform-half-second",
        ),
        pytest.param({"clock_time": _AWARE_TIME}, "clock_time", False, False, id="time-transform"),
        pytest.param(
            {"taken_before": _AT_PLUS_SIXTEEN},
            "taken_before",
            True,
            False,
            id="datetime-16-00",
        ),
    ],
)
def test_compiled_predicate_is_held_to_the_utc_offsets_postgresql_refuses(
    mode: str,
    data: dict[str, object],
    form_key: str,
    refused_as_text: bool,  # noqa: FBT001
    refused_on_server: bool,  # noqa: FBT001
) -> None:
    """The parameters a filter's compiled predicate binds are held to PostgreSQL's offset rule.

    A stand-in alias carries each binding mode: bound as text a time through a datetime's
    ``time`` transform, or a datetime, is refused for an offset of 16:00 or more or one
    with a fraction of a second; bound on the server only a time's 16:00 is.
    """
    driver, cursor_factory, client_side = BINDING_MODES[mode]
    refused = refused_as_text if client_side else refused_on_server
    specimen_filter = _temporal_filter_class()
    with postgresql_stand_in(driver, cursor_factory) as alias:
        filterset = specimen_filter(
            data=data,
            queryset=_specimens_with_unresolved_output().using(alias),
        )
        if not refused:
            specimen_filter._validate_form_or_raise(filterset)
            return
        with pytest.raises(GraphQLError) as excinfo:
            specimen_filter._validate_form_or_raise(filterset)
    assert excinfo.value.extensions == {
        "code": "FILTER_INVALID",
        "errors": {form_key: _UNBINDABLE},
    }


def _stamped_shelf_filter_class(
    array_of: Callable[[django_models.Field[object, object]], django_models.Field[object, object]],
) -> tuple[type[django_models.Model], type[FilterSet]]:
    """A model with arrays of datetimes and of times, and a filterset through every shape they bind.

    ``array_of`` builds each array column. The whole-array ``contains`` and ``exact``, the
    first element (index ``0``) and the first two (slice ``0_2``), each element wrapped in an
    ``ARRAY[...]`` of its own parameters on PostgreSQL, and ``gt``, which binds the list as
    one parameter. Query-build only (``managed = False``): the rule compiles the filter's
    predicate and never runs it.
    """

    class StampedShelf(django_models.Model):
        stamps = array_of(django_models.DateTimeField())
        clocks = array_of(django_models.TimeField())
        grid = array_of(array_of(django_models.DateTimeField()))

        class Meta:
            managed = False
            app_label = "test_array_bind_ask"

    class StampedShelfFilter(FilterSet):
        stamps_contain = ArrayFilter(field_name="stamps", lookup_expr="contains")
        stamps_are = ArrayFilter(field_name="stamps", lookup_expr="exact")
        first_stamp = django_filters.DateTimeFilter(field_name="stamps__0")
        first_two_stamps = ArrayFilter(field_name="stamps__0_2", lookup_expr="exact")
        stamps_after = ArrayFilter(field_name="stamps", lookup_expr="gt")
        clocks_contain = ArrayFilter(field_name="clocks", lookup_expr="contains")
        first_clock = django_filters.TimeFilter(field_name="clocks__0")
        clocks_after = ArrayFilter(field_name="clocks", lookup_expr="gt")
        grid_contain = ArrayFilter(field_name="grid", lookup_expr="contains")

        class Meta:
            model = StampedShelf
            fields = []

    return StampedShelf, StampedShelfFilter


@pytest.mark.parametrize("mode", list(BINDING_MODES))
def test_array_leaf_list_parameter_is_held_to_the_text_rule_in_every_binding_mode(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    """A temporal array leaf is asked wherever ``django.contrib.postgres`` is unavailable too.

    On the ``ArrayField`` double a ``gt`` binds the list as one parameter, as a real
    ``ArrayField``'s does, whose elements are held to the text rule in every binding mode:
    a datetime at +16:00 is refused.
    """
    patch_array_field(monkeypatch)
    model, shelf_filter = _stamped_shelf_filter_class(FakeArrayField)
    driver, cursor_factory, _ = BINDING_MODES[mode]
    with postgresql_stand_in(driver, cursor_factory) as alias:
        filterset = shelf_filter(
            data={"stamps_after": [_AT_PLUS_SIXTEEN]},
            queryset=model.objects.using(alias),
        )
        with pytest.raises(GraphQLError) as excinfo:
            shelf_filter._validate_form_or_raise(filterset)
    assert excinfo.value.extensions == {
        "code": "FILTER_INVALID",
        "errors": {"stamps_after": _UNBINDABLE},
    }


def _priced_filter_class() -> type[FilterSet]:
    """A specimen filterset reaching a bounded and an unbounded decimal column.

    Generated ``exact`` / ``in`` / ``range`` / ``gt`` / ``lt`` leaves on ``price`` (a
    ``DecimalField(20, 4)``), the package's declared ``ListFilter`` / ``RangeFilter`` on
    it, and a ``NumberFilter`` over ``loose_price``, an annotation whose output field is a
    ``DecimalField`` with no ``max_digits``.
    """

    class PricedSpecimenFilter(FilterSet):
        prices_among = ListFilter(field_name="price", lookup_expr="in")
        price_span = RangeFilter(field_name="price", lookup_expr="range")
        loose_price = django_filters.NumberFilter(field_name="loose_price")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {
                "price": [
                    "exact",
                    "in",
                    "range",
                    "gt",
                    "lt",
                ],
            }

    return PricedSpecimenFilter


def _specimens_priced() -> QuerySet[scalar_models.ScalarSpecimen]:
    """Every specimen, annotated with its ``price`` as an unbounded ``DecimalField``."""
    return scalar_models.ScalarSpecimen.objects.annotate(
        loose_price=models.ExpressionWrapper(
            models.F("price"),
            output_field=models.DecimalField(max_digits=None, decimal_places=None),
        ),
    )


#: A spelling past PostgreSQL ``numeric``'s format by the integer digits, by the fraction
#: digits, by the fraction digits alone at the format's edge, and by written trailing zeros.
_NEGATIVE_HUGE = "-1e1000000"


_TINY = "1e-1000000"


#: A decimal spelling past PostgreSQL ``numeric``'s fractional-digit limit.
_PAST_FRACTION = "1e-16384"


#: The finest fraction ``numeric`` stores.
_EDGE_FRACTION = "1e-16383"


@pytest.mark.skipif(
    connections["default"].vendor != "sqlite",
    reason="pins how SQLite compares a decimal filter value, as a double",
)
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("data", "labels"),
    [
        pytest.param({"price": _TINY}, ["zero"], id="exact-tiny"),
        pytest.param({"price__in": f"5,{_TINY}"}, ["zero"], id="in-tiny"),
        pytest.param({"price__range": f"{_TINY},0.2"}, ["zero"], id="range-start-tiny"),
        pytest.param({"price__lt": _TINY}, [], id="lt-tiny"),
        pytest.param(
            {"price": "0.30000000000000000000001"},
            ["tenths"],
            id="exact-past-15-digits",
        ),
        pytest.param({"price": "0.30000000000001"}, [], id="exact-within-15-digits"),
        pytest.param({"price__lt": _NEGATIVE_HUGE}, [], id="lt-negative-huge"),
        pytest.param(
            {"price__range": f"{_NEGATIVE_HUGE},0.5"},
            ["tenths", "zero"],
            id="range-start-negative-huge",
        ),
    ],
)
def test_decimal_filter_value_compares_as_a_double_on_sqlite(
    data: dict[str, object],
    labels: list[str],
) -> None:
    """On SQLite a decimal filter value is compared as a double, not refused for its spelling.

    Django binds a ``Decimal`` as its text and the column's ``NUMERIC`` affinity reads it as
    a double, so a non-zero value below the smallest double compares as zero (``exact``,
    ``in`` and a ``range`` start match a stored zero, ``lt`` drops it) and a value differing
    from a stored one only past a double's 15 to 17 significant digits can compare equal to
    it, while a value past the largest double compares as an infinity and answers the rows it
    orders.
    """
    for label, price in (("zero", "0"), ("tenths", "0.3"), ("one", "1")):
        specimen = _make_scalar_specimen(label)
        specimen.price = Decimal(price)
        specimen.save(update_fields=["price"])
    priced_filter = _priced_filter_class()
    filterset = priced_filter(data=data, queryset=_specimens_priced())
    priced_filter._validate_form_or_raise(filterset)
    assert sorted(filterset.qs.values_list("label", flat=True)) == labels


class _PreparedCountedArrayField(FakeArrayField):
    """A ``len``-carrying ``ArrayField`` double that prepares each element as a real one does.

    ``ArrayField.get_db_prep_value`` prepares a list element by element through its
    ``base_field``, so an integer element a form cleans to a ``Decimal`` binds as an
    ``int``.
    """

    @override
    def get_db_prep_value(
        self,
        value: object,
        connection: BaseDatabaseWrapper,
        prepared: bool = False,
    ) -> object:
        if is_list_or_tuple(value):
            return [
                self.base_field.get_db_prep_value(element, connection, prepared=False)
                for element in value
            ]
        return value


class _SmallCountedShelf(django_models.Model):
    """A table with an array of small integers, its ``len`` registered as a real one's is.

    Query-build only (``managed = False``): the bind ask compiles, never runs, its clause.
    """

    counts = _PreparedCountedArrayField(django_models.SmallIntegerField())

    class Meta:
        managed = False
        app_label = "test_small_integer_array_double"


@pytest.mark.parametrize(
    ("form_key", "value", "refused"),
    [
        pytest.param("counts_after", ["1", str(2**15)], True, id="gt-member-past-int16"),
        pytest.param("counts_after", ["1", str(2**15 - 1)], False, id="gt-member-max-int16"),
        pytest.param("counts__len__in", str(2**15), False, id="len-past-int16"),
    ],
)
def test_integer_array_leaf_is_asked_wherever_django_contrib_postgres_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    form_key: str,
    value: object,
    refused: bool,  # noqa: FBT001
) -> None:
    """An integer array leaf is asked on the ``ArrayField`` double too.

    A ``gt`` binds the list as one parameter, each integer of which is held to the
    element's range the connection states (Django's default ranges, PostgreSQL's: 16 bits
    for a ``SmallIntegerField``), while the array's ``len`` is held to its own
    ``IntegerField`` output's.
    """
    patch_array_field(monkeypatch)

    class SmallCountedShelfFilter(FilterSet):
        counts_after = ArrayFilter(field_name="counts", lookup_expr="gt")

        class Meta:
            model = _SmallCountedShelf
            fields = {"counts": ["len__in"]}

    monkeypatch.setattr(
        connection.ops,
        "integer_field_range",
        _default_range_operations(connection).integer_field_range,
    )
    filterset = SmallCountedShelfFilter(
        data={form_key: value},
        queryset=_SmallCountedShelf.objects.all(),
    )
    if not refused:
        SmallCountedShelfFilter._validate_form_or_raise(filterset)
        return
    with pytest.raises(GraphQLError) as excinfo:
        SmallCountedShelfFilter._validate_form_or_raise(filterset)
    assert excinfo.value.extensions == {
        "code": "FILTER_INVALID",
        "errors": {form_key: _UNBINDABLE},
    }


_NAIVE_CLOCK = datetime.time(9, 30)


#: A time whose UTC offset PostgreSQL refuses in every binding mode.
_CLOCK_AT_PLUS_SIXTEEN = datetime.time(12, tzinfo=_PLUS_SIXTEEN)


@pytest.mark.parametrize("mode", list(BINDING_MODES))
@pytest.mark.parametrize(
    ("clock", "refused"),
    [
        pytest.param(_AWARE_TIME, False, id="in-range-offset"),
        pytest.param(_CLOCK_AT_PLUS_SIXTEEN, True, id="own-offset-16-00"),
    ],
)
def test_annotation_offset_the_leaf_reads_never_refuses_its_time(
    mode: str,
    clock: datetime.time,
    refused: bool,  # noqa: FBT001
) -> None:
    """A UTC offset a queryset annotation the leaf reads binds is the queryset's own, never asked.

    The annotation picks ``occurred_time`` through a ``When`` comparing it with a time at
    +16:00, an offset PostgreSQL refuses in every binding mode. A time over the annotation
    whose own offset binds passes, never ``FILTER_INVALID`` for the annotation's constant,
    while the leaf's own time at +16:00 is refused.
    """

    class AnnotatedClockFilter(FilterSet):
        clocked = django_filters.TimeFilter(field_name="clocked_at")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    driver, cursor_factory, _ = BINDING_MODES[mode]
    with postgresql_stand_in(driver, cursor_factory) as alias:
        queryset = scalar_models.ScalarSpecimen.objects.using(alias).annotate(
            clocked_at=models.Case(
                models.When(
                    occurred_time__gt=models.Value(_CLOCK_AT_PLUS_SIXTEEN),
                    then=models.F("occurred_time"),
                ),
                default=models.F("occurred_time"),
            ),
        )
        filterset = AnnotatedClockFilter(data={"clocked": clock}, queryset=queryset)
        if not refused:
            AnnotatedClockFilter._validate_form_or_raise(filterset)
            return
        with pytest.raises(GraphQLError) as excinfo:
            AnnotatedClockFilter._validate_form_or_raise(filterset)
    assert excinfo.value.extensions == {
        "code": "FILTER_INVALID",
        "errors": {"clocked": _UNBINDABLE},
    }


@pytest.mark.parametrize("mode", list(BINDING_MODES))
@pytest.mark.parametrize(
    ("price", "refused"),
    [
        pytest.param("1.5", False, id="in-range"),
        pytest.param(_PAST_FRACTION, True, id="own-16384-fraction-digits"),
    ],
)
def test_annotation_decimal_the_leaf_reads_never_refuses_its_value(
    mode: str,
    price: str,
    refused: bool,  # noqa: FBT001
) -> None:
    """A decimal a queryset annotation the leaf reads binds is the queryset's own, never asked.

    The annotation picks ``price`` through a ``When`` comparing it with a ``Value`` whose
    16384 fraction digits PostgreSQL ``numeric`` cannot hold. A decimal over the
    annotation inside the format passes, never ``FILTER_INVALID`` for the annotation's
    constant, while the leaf's own decimal past the format is refused.
    """

    class AnnotatedPriceFilter(FilterSet):
        priced = django_filters.NumberFilter(field_name="priced_at")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    driver, cursor_factory, _ = BINDING_MODES[mode]
    with postgresql_stand_in(driver, cursor_factory) as alias:
        queryset = scalar_models.ScalarSpecimen.objects.using(alias).annotate(
            priced_at=models.Case(
                models.When(
                    price__gt=models.Value(Decimal(_PAST_FRACTION)),
                    then=models.F("price"),
                ),
                default=models.F("price"),
            ),
        )
        filterset = AnnotatedPriceFilter(data={"priced": price}, queryset=queryset)
        if not refused:
            AnnotatedPriceFilter._validate_form_or_raise(filterset)
            return
        with pytest.raises(GraphQLError) as excinfo:
            AnnotatedPriceFilter._validate_form_or_raise(filterset)
    assert excinfo.value.extensions == {
        "code": "FILTER_INVALID",
        "errors": {"priced": _UNBINDABLE},
    }


@pytest.mark.parametrize("client_side", [False, True], ids=["server-side", "client-side"])
@pytest.mark.parametrize(
    ("clocks", "refused"),
    [
        pytest.param([_AWARE_TIME], False, id="aware"),
        pytest.param([_NAIVE_CLOCK, _AWARE_TIME], True, id="own-naive-aware"),
    ],
)
def test_annotation_list_parameter_the_leaf_reads_never_refuses_its_list(
    client_side: bool,  # noqa: FBT001
    clocks: list[datetime.time],
    refused: bool,  # noqa: FBT001
) -> None:
    """A list parameter a queryset annotation the leaf reads binds is the queryset's own, never asked.

    The annotation picks the time array through a ``When`` whose ``gt`` binds a naive time
    before an aware one, a list psycopg 3 cannot dump. A list over the annotation psycopg
    dumps passes, never ``FILTER_INVALID`` for the annotation's constant, while the leaf's
    own naive-then-aware list is refused. The alias stands in for PostgreSQL on the real
    driver module, never connected.
    """
    pytest.importorskip("psycopg")
    psycopg = importlib.import_module("psycopg")
    shelf_model, _ = _stamped_shelf_filter_class(real_array_of)

    class AnnotatedClocksFilter(FilterSet):
        clocks_seen_after = ArrayFilter(field_name="clocks_seen", lookup_expr="gt")

        class Meta:
            model = shelf_model
            fields = []

    cursor_factory = (
        require(read_attr(psycopg, "ClientCursor"), truth.is_type) if client_side else None
    )
    with postgresql_stand_in(psycopg, cursor_factory) as alias:
        queryset = shelf_model.objects.using(alias).annotate(
            clocks_seen=models.Case(
                models.When(clocks__gt=[_NAIVE_CLOCK, _AWARE_TIME], then=models.F("clocks")),
                default=models.F("clocks"),
            ),
        )
        filterset = AnnotatedClocksFilter(data={"clocks_seen_after": clocks}, queryset=queryset)
        if not refused:
            AnnotatedClocksFilter._validate_form_or_raise(filterset)
            return
        with pytest.raises(GraphQLError) as excinfo:
            AnnotatedClocksFilter._validate_form_or_raise(filterset)
    assert excinfo.value.extensions == {
        "code": "FILTER_INVALID",
        "errors": {"clocks_seen_after": _UNBINDABLE},
    }


_PAST_INT64 = str(2**63)


def _year_integer_filter_class() -> type[FilterSet]:
    """A declared year member used only to inspect per-alias internal range dispatch.

    The actual date, ISO-year, range and reverse-relation verdicts live in
    ``test_scalar_predicate_binding_api.py``.
    """

    class YearIntegerFilter(FilterSet):
        day_years_among = ListFilter(field_name="occurred_on__year", lookup_expr="in")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    return YearIntegerFilter


class _ElapsedSpecimen(django_models.Model):
    """A duration column for validation-only per-alias internal range dispatch.

    The real-table HTTP duration cohort selects ordinary identifiers, so filtering a
    duration does not require exposing it as an output scalar.
    """

    elapsed: django_models.DurationField[object, datetime.timedelta] = (
        django_models.DurationField()
    )

    class Meta:
        managed = False
        app_label = "library"


def _elapsed_filter_class() -> type[FilterSet]:
    """An exact duration leaf used only to inspect per-alias internal range dispatch.

    Real duration filtering and backend verdicts live in ``test_scalar_predicate_binding_api.py``.
    """

    class ElapsedFilter(FilterSet):
        class Meta:
            model = _ElapsedSpecimen
            fields = {"elapsed": ["exact"]}

    return ElapsedFilter


@pytest.mark.django_db
def test_integer_column_value_is_not_asked() -> None:
    """An integer column's leaf is never asked: its values are held where its filters bind them.

    A generated ``in`` over the integer column drops a member past the column's range
    (``_identifying_members``) and its ``gt`` is Django's own range-aware comparison, so
    neither reaches the rule and the queryset's alias is never resolved for them.
    """

    class SignedBigFilter(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"signed_big": ["in", "gt"]}

    router = _RecordingRouter()
    with override_settings(DATABASE_ROUTERS=[router]):
        filterset = SignedBigFilter(
            data={"signed_big__in": _PAST_INT64, "signed_big__gt": _PAST_INT64},
            queryset=scalar_models.ScalarSpecimen.objects.all(),
        )

        SignedBigFilter._validate_form_or_raise(filterset)
    assert router.asked == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("members", "labels"),
    [
        pytest.param("1.5,2", ["two"], id="fraction-dropped"),
        pytest.param("0.9,-1.5", [], id="every-member-fractional"),
        pytest.param("1.0,2", ["one", "two"], id="integral-spelling-kept"),
    ],
)
def test_integer_column_in_drops_a_fractional_member(members: str, labels: list[str]) -> None:
    """Raw form data's fractional member names no row; ``int()`` never truncates it to one.

    The ``in`` form field cleans ``"1.5"`` to ``Decimal("1.5")``, which equals no integer a
    ``signed_big`` row holds, so it never matches the row holding 1; a list whose every
    member is fractional matches nothing.
    """

    class SignedBigFilter(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"signed_big": ["in"]}

    for label, number in (
        ("zero", 0),
        ("minus-one", -1),
        ("one", 1),
        ("two", 2),
    ):
        scalar_models.ScalarSpecimen.objects.create(
            label=label,
            signed_big=number,
            occurred_on=datetime.date(2020, 1, 1),
            occurred_at=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
            occurred_time=datetime.time(12),
            external_id=uuid.uuid4(),
        )
    filterset = SignedBigFilter(
        data={"signed_big__in": members},
        queryset=scalar_models.ScalarSpecimen.objects.all(),
    )

    SignedBigFilter._validate_form_or_raise(filterset)
    assert sorted(filterset.qs.values_list("label", flat=True)) == sorted(labels)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("data", "labels"),
    [
        pytest.param({"signed_big__gte": "1.5"}, ["one", "two", "three"], id="gte-truncates"),
        pytest.param({"signed_big__lt": "1.5"}, ["minus-one", "zero"], id="lt-truncates"),
        pytest.param({"signed_big": "1.5"}, ["one"], id="exact-truncates"),
        pytest.param({"signed_big": "-1.5"}, ["minus-one"], id="exact-truncates-toward-zero"),
        pytest.param({"signed_big__range": "1.5,2.5"}, ["one", "two"], id="range-truncates"),
        pytest.param({"signed_big__in": "1.5"}, [], id="in-drops"),
    ],
)
def test_integer_comparison_truncates_a_fractional_value(
    data: dict[str, str],
    labels: list[str],
) -> None:
    """Raw form data's fractional comparison value truncates toward zero; ``in`` drops it.

    The comparison leaves are django-filter's ``NumberFilter``, whose ``DecimalField`` cleans
    ``"1.5"`` to ``Decimal("1.5")``; Django's float ceiling (``IntegerFieldFloatRounding``)
    reads only a ``float``, so the ``Decimal`` reaches ``IntegerField.get_prep_value``'s
    ``int()``, as it does under a stock django-filter ``FilterSet``. An ``in`` member equal
    to no integer names no row instead. The GraphQL ``Int`` / ``BigInt`` scalars refuse a
    fraction before any of these binds.
    """

    class SignedBigFilter(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {
                "signed_big": [
                    "exact",
                    "gte",
                    "lt",
                    "range",
                    "in",
                ],
            }

    for label, number in (
        ("minus-one", -1),
        ("zero", 0),
        ("one", 1),
        ("two", 2),
        ("three", 3),
    ):
        scalar_models.ScalarSpecimen.objects.create(
            label=label,
            signed_big=number,
            occurred_on=datetime.date(2020, 1, 1),
            occurred_at=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
            occurred_time=datetime.time(12),
            external_id=uuid.uuid4(),
        )
    filterset = SignedBigFilter(data=data, queryset=scalar_models.ScalarSpecimen.objects.all())

    SignedBigFilter._validate_form_or_raise(filterset)
    assert sorted(filterset.qs.values_list("label", flat=True)) == sorted(labels)


def _default_range_operations(wrapper: BaseDatabaseWrapper) -> BaseDatabaseOperations:
    """``wrapper``'s own operations, reading Django's default integer ranges (PostgreSQL's)."""

    class DefaultRangeOperations(type(wrapper.ops)):
        @override
        def integer_field_range(self, internal_type: str) -> tuple[int, int]:
            return BaseDatabaseOperations.integer_field_range(self, internal_type)

    return DefaultRangeOperations(wrapper)


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "filter_class",
        "model",
        "data",
        "form_key",
        "refused",
    ),
    [
        pytest.param(
            _year_integer_filter_class,
            scalar_models.ScalarSpecimen,
            {"day_years_among": [str(2**31)]},
            "day_years_among",
            True,
            id="year-past-int32",
        ),
        pytest.param(
            _year_integer_filter_class,
            scalar_models.ScalarSpecimen,
            {"day_years_among": [str(2**31 - 1)]},
            "day_years_among",
            False,
            id="year-max-int32",
        ),
        pytest.param(
            _elapsed_filter_class,
            _ElapsedSpecimen,
            {"elapsed": datetime.timedelta(microseconds=2**31)},
            "elapsed",
            False,
            id="duration-past-int32",
        ),
    ],
)
def test_integer_is_held_to_the_range_of_the_type_its_lookup_binds(
    filter_class: Callable[[], type[FilterSet]],
    model: type[django_models.Model],
    data: dict[str, object],
    form_key: str,
    refused: bool,  # noqa: FBT001
) -> None:
    """Each integer is held to the range the queryset's database stores for its lookup's type.

    On a stand-in alias reading Django's default ranges (PostgreSQL's), a ``year``
    transform's ``IntegerField`` output holds 32 bits, so 2**31 is refused there and
    2**31-1 binds, while a duration's microsecond count holds ``BigIntegerField``'s 64
    bits, so 2**31 microseconds binds.
    """
    alias = "integer_range_stand_in"
    wrapper = connections.create_connection(DEFAULT_DB_ALIAS)
    wrapper.ops = _default_range_operations(wrapper)
    connections[alias] = wrapper
    filterset_class = filter_class()
    try:
        filterset = filterset_class(data=data, queryset=model._default_manager.using(alias))
        if not refused:
            filterset_class._validate_form_or_raise(filterset)
            return
        with pytest.raises(GraphQLError) as excinfo:
            filterset_class._validate_form_or_raise(filterset)
    finally:
        del connections[alias]
    assert excinfo.value.extensions == {
        "code": "FILTER_INVALID",
        "errors": {form_key: _UNBINDABLE},
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param({"exact": "x"}, [("exact", "x")], id="exact"),
        pytest.param({"i_contains": "y"}, [("i_contains", "y")], id="python-lookup-name"),
    ],
)
def test_operator_bag_items_walks_lookup_attr_dict(
    value: dict[str, str],
    expected: list[tuple[str, str]],
) -> None:
    """A dict made only of lookup attributes is walked as a bag, preserving its key and value."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    assert CategoryFilter._operator_bag_items(value) == expected


@pytest.mark.parametrize(
    "value",
    [{"start": 1, "end": 5}, {"exact": "x", "start": 1}],
    ids=["range-patch", "mixed-lookup-and-value-keys"],
)
def test_operator_bag_items_returns_none_for_non_lookup_key_dict(
    value: dict[str, object],
) -> None:
    """A value dict with any non-lookup key stays scalar instead of emitting bogus form keys.

    A range patch must reach its widget-key normalizer intact. Mixing an ordinary value
    key with a lookup key does not turn that value into a bag either.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._operator_bag_items(value) is None


@pytest.mark.parametrize("value", ["x", ["x"]], ids=["scalar", "sequence"])
def test_operator_bag_items_still_returns_none_for_scalars(value: object) -> None:
    """Scalar and sequence values are not operator bags."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._operator_bag_items(value) is None


def test_extract_branch_value_returns_none_for_none_input() -> None:
    """``_extract_branch_value(None, ...)`` short-circuits to ``None``."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._extract_branch_value(None, "shelves") is None


@pytest.mark.parametrize("input_value", [None, UNSET], ids=["none", "unset"])
def test_run_permission_checks_short_circuits_on_none_and_unset(input_value: object) -> None:
    """An inactive input returns before any gate dispatch."""
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, _request: object) -> None:
            fired.append("name")

    CategoryFilter._run_permission_checks(input_value, request=HttpRequest())
    assert fired == []


@pytest.mark.django_db
def test_check_permissions_walks_explicit_requested_fields() -> None:
    """The explicit-``requested_fields`` path fires each named gate directly."""
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, _request: object) -> None:
            fired.append("name")

    instance = CategoryFilter(data={}, queryset=Category.objects.all())
    instance.check_permissions(HttpRequest(), requested_fields={"name", "unknown_field"})
    # Only the declared gate fires; the unknown field has no ``check_*`` method.
    assert fired == ["name"]


def test_evaluate_logic_tree_caps_recursion_depth() -> None:
    """``_evaluate_logic_tree`` raises past ``_MAX_LOGIC_DEPTH``.

    The depth guard is independent of the ``_run_permission_checks``
    cap; this pins the ``_evaluate_logic_tree`` / ``_q_for_branch`` arm.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter._evaluate_logic_tree(
            Category.objects.all(),
            {"and": [{"name": "x"}]},
            _depth=CategoryFilter._MAX_LOGIC_DEPTH + 1,
            _flat_hop_visibility={},
        )
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)


def test_evaluate_logic_tree_caps_a_non_int_knob_at_the_neutral_default() -> None:
    """A non-int ``_MAX_LOGIC_DEPTH`` knob caps at the neutral default, typed.

    The filter enforcement sites resolve their budget through the shared
    check, which honors a declared int and takes the neutral default for
    anything else: depth past the default raises the shared typed
    sentence instead of failing on the comparison, and the sentence names
    the default, not the knob that did not set it.
    """

    class CategoryFilter(FilterSet):
        # basedpyright: the wrong-typed knob is the misconfiguration under test
        _MAX_LOGIC_DEPTH = "10"  # pyright: ignore[reportAssignmentType]

        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(
        ConfigurationError,
        match=r"nesting exceeded the maximum traversal depth \(8\)\. ",
    ):
        CategoryFilter._evaluate_logic_tree(
            Category.objects.all(),
            {"and": [{"name": "x"}]},
            _depth=FilterSet._MAX_LOGIC_DEPTH + 1,
            _flat_hop_visibility={},
        )


def test_evaluate_logic_tree_and_direct_branch_treat_inactive_values_as_identity() -> None:
    """Inactive AND arms and direct branch calls return the identity query."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    queryset = Category.objects.all()
    assert (
        CategoryFilter._evaluate_logic_tree(queryset, {"and": [None]}, _flat_hop_visibility={})
        == Q()
    )
    assert CategoryFilter._q_for_branch(queryset, UNSET, _flat_hop_visibility={}) == Q()


def test_collect_nested_visibility_querysets_async_caps_recursion_depth() -> None:
    """``_collect_nested_visibility_querysets_async`` raises past ``_MAX_LOGIC_DEPTH``.

    Third site of the shared ``_assert_logic_depth`` binding -- the async
    pre-walker enforces the same depth cap as ``_run_permission_checks`` and
    ``_evaluate_logic_tree``, surfacing the identical typed error rather than
    silently bottoming out into a Python ``RecursionError``.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError) as excinfo:
        asyncio.run(
            CategoryFilter._collect_nested_visibility_querysets_async(
                {"and_": [{"name": "x"}]},
                _make_info(),
                _depth=CategoryFilter._MAX_LOGIC_DEPTH + 1,
                flat_hop_visibility={},
            ),
        )
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)
    # Pin the qualname-prefixed shape that the shared helper preserves.
    assert "CategoryFilter" in str(excinfo.value)


def test_target_type_for_related_filter_returns_none_without_child_model() -> None:
    """A ``RelatedFilter`` whose filterset has no model resolves to ``None``."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._target_type_for_related_filter(RelatedFilter(None)) is None


def test_is_own_pk_under_relay_owner_false_for_relation_field() -> None:
    """An ``is_relation`` field never takes the own-PK Relay branch."""

    class BookType(DjangoType):
        class Meta:
            model = library_models.Book
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(BookType, BookType.__django_strawberry_definition__)

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    # Bind a Relay owner directly on the throwaway local class so the early
    # ``owner is None`` guard is passed; ``registry.clear()`` (autouse
    # teardown) strips the binding afterward.
    BookFilter._owner_definition = BookType.__django_strawberry_definition__
    relation_field = library_models.Book._meta.get_field("genres")
    assert BookFilter._is_own_pk_under_relay_owner(relation_field, "genres") is False


def test_is_own_pk_under_relay_owner_false_when_model_missing() -> None:
    """A non-relation field with a model-less filterset returns ``False``."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(CategoryType, CategoryType.__django_strawberry_definition__)

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._owner_definition = CategoryType.__django_strawberry_definition__
    # The local class is discarded after the test, so nulling its own
    # ``_meta.model`` does not leak into other tests.
    CategoryFilter._meta.model = None
    non_relation = SimpleNamespace(is_relation=False)
    assert CategoryFilter._is_own_pk_under_relay_owner(non_relation, "name") is False


def _relay_bound_book_filter(fields: dict[str, object]) -> type[FilterSet]:
    """A ``Book`` set with ``fields``, bound to a Relay-Node ``BookType``."""

    class BookType(DjangoType):
        class Meta:
            model = library_models.Book
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(BookType, BookType.__django_strawberry_definition__)
    meta = type("Meta", (), {"model": library_models.Book, "fields": fields})
    book_filter = type("BookFilter", (FilterSet,), {"__module__": __name__, "Meta": meta})
    assert issubclass(book_filter, FilterSet)
    book_filter._owner_definition = BookType.__django_strawberry_definition__
    return book_filter


def test_is_own_pk_under_relay_owner_false_for_a_dotted_key() -> None:
    """Only the single-segment key names the own PK; a hop key ending on it does not."""
    book_filter = _relay_bound_book_filter({"title": ["exact"]})
    pk_field = library_models.Book._meta.pk

    assert book_filter._is_own_pk_under_relay_owner(pk_field, "id") is True
    assert book_filter._is_own_pk_under_relay_owner(pk_field, None) is True
    assert book_filter._is_own_pk_under_relay_owner(pk_field, "archive_genres__books__id") is False


def test_hop_key_ending_on_own_pk_is_a_plain_column_filter() -> None:
    """``archive_genres__books__id`` filters the hop's book: the column filter, every lookup."""
    book_filter = _relay_bound_book_filter({"archive_genres__books__id": ["exact", "in", "gt"]})

    leaves = book_filter.get_filters()

    assert type(leaves["archive_genres__books__id"]) is NumberFilter
    assert isinstance(leaves["archive_genres__books__id__in"], IntegerInFilter)
    assert type(leaves["archive_genres__books__id__gt"]) is NumberFilter


def test_dict_all_narrows_the_own_pk_but_not_a_hop_key_ending_on_it() -> None:
    """The dict ``"__all__"`` GlobalID narrowing applies to the own ``id`` key only."""
    book_filter = _relay_bound_book_filter(
        {"id": "__all__", "archive_genres__books__id": "__all__"},
    )

    fields = book_filter.get_fields()

    assert set(require(fields["id"], is_list_or_tuple)) == {"exact", "in", "isnull"}
    assert "gt" in require(fields["archive_genres__books__id"], is_list_or_tuple)


def test_delegating_filter_for_lookup_override_keeps_the_own_pk_global_id() -> None:
    """An override answering ``super().filter_for_lookup()`` keeps the own-PK GlobalID policy."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(CategoryType, CategoryType.__django_strawberry_definition__)

    class DelegatingFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"id": ["exact", "in"]}

        @classmethod
        @override
        def filter_for_lookup(
            cls,
            field: ModelField,
            lookup_type: str,
        ) -> tuple[type[Filter] | None, dict[str, object]]:
            return super().filter_for_lookup(field, lookup_type)

    DelegatingFilter._owner_definition = CategoryType.__django_strawberry_definition__

    leaves = DelegatingFilter.get_filters()
    assert type(leaves["id"]) is GlobalIDFilter
    assert type(leaves["id__in"]) is GlobalIDMultipleChoiceFilter
    with pytest.raises(ConfigurationError, match="'gt' is not supported"):
        DelegatingFilter.filter_for_field(Category._meta.pk, "id", "gt")


def test_another_sets_filter_for_lookup_during_generation_reads_as_a_direct_call() -> None:
    """A set's ``filter_for_lookup`` called inside another set's generation sees no key.

    ``BookFilter`` builds the dotted ``archive_genres__books__id`` key, and its override
    asks ``CategoryFilter`` about Category's primary key meanwhile; the published key
    is Book's, so Category's own pk keeps its GlobalID.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(CategoryType, CategoryType.__django_strawberry_definition__)

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._owner_definition = CategoryType.__django_strawberry_definition__
    asked: list[type[Filter] | None] = []

    class AskingBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"archive_genres__books__id": ["exact"]}

        @classmethod
        @override
        def filter_for_lookup(
            cls,
            field: ModelField,
            lookup_type: str,
        ) -> tuple[type[Filter] | None, dict[str, object]]:
            asked.append(CategoryFilter.filter_for_lookup(Category._meta.pk, "exact")[0])
            return super().filter_for_lookup(field, lookup_type)

    asked.clear()
    _ = AskingBookFilter.get_filters()

    assert asked
    assert all(answer is GlobalIDFilter for answer in asked)


def test_generic_foreign_key_key_is_refused_by_path() -> None:
    """A ``GenericForeignKey`` key (no ``related_model``) is refused naming its path."""

    def declare() -> type[FilterSet]:
        class TaggedItemFilter(FilterSet):
            class Meta:
                model = library_models.TaggedItem
                fields = {"content_object": ["exact"]}

        _ = TaggedItemFilter.get_filters()
        return TaggedItemFilter

    with pytest.raises(ConfigurationError, match="content_object"):
        declare()


def test_dotted_relation_key_targets_its_own_relation_not_a_root_relation_of_the_leaf_name() -> (
    None
):
    """``branch__notes__branch`` on a bound Shelf set targets ``ProxyBranch``, not ``Branch``.

    The leaf ``BranchNote.branch`` is named like ``Shelf.branch``; the Relay
    ``ProxyBranch`` type makes the key a GlobalID, where the non-Relay ``Branch`` type
    behind the root relation of that name would make it a raw primary key.
    """

    class BranchType(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")

    class ProxyBranchType(DjangoType):
        class Meta:
            model = library_models.ProxyBranch
            fields = ("id", "name")
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ProxyBranchType, ProxyBranchType.__django_strawberry_definition__)

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    assert registry.get(library_models.Branch) is BranchType
    ShelfFilter._owner_definition = ShelfType.__django_strawberry_definition__
    leaf = library_models.BranchNote._meta.get_field("branch")

    resolved = ShelfFilter.filter_for_field(leaf, "branch__notes__branch", "exact")

    assert isinstance(resolved, GlobalIDFilter)


def test_filter_for_lookup_rejects_unsupported_lookup_on_relay_owner_pk() -> None:
    """An explicit unsupported lookup on a Relay owner's PK raises.

    The ``get_fields`` ``"__all__"`` narrowing only covers the generated
    surface; an explicit ``Meta.fields`` list naming ``range`` / ``gt`` / a
    pattern lookup still reaches ``filter_for_lookup``. A Relay node's wire id
    has no ordering / pattern semantics, so those lookups are rejected with a
    ``ConfigurationError`` (naming the lookup) instead of silently becoming a
    GlobalID-shaped ``String``. Only ``exact`` / ``in`` / ``isnull`` are allowed.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(CategoryType, CategoryType.__django_strawberry_definition__)

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._owner_definition = CategoryType.__django_strawberry_definition__
    pk_field = Category._meta.pk

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter.filter_for_lookup(pk_field, "range")
    assert "range" in str(excinfo.value)
    # The same rejection holds via the per-field entry point (which routes
    # through ``filter_for_lookup`` in ``super().filter_for_field``).
    with pytest.raises(ConfigurationError):
        CategoryFilter.filter_for_field(pk_field, "id", "range")

    # The three supported lookups resolve without raising.
    exact_class, _ = CategoryFilter.filter_for_lookup(pk_field, "exact")
    assert exact_class is GlobalIDFilter
    in_class, _ = CategoryFilter.filter_for_lookup(pk_field, "in")
    assert in_class is GlobalIDMultipleChoiceFilter
    isnull_class, _ = CategoryFilter.filter_for_lookup(pk_field, "isnull")
    assert isnull_class is not GlobalIDFilter


def test_relation_key_target_type_prefers_declared_primary() -> None:
    """A relation key's target type is the declared primary when two types share a model.

    ``FilterSet.filter_for_lookup`` reads the target as ``registry.get(related_model)``,
    NOT a ``registry.primary_for(related_model) or registry.get(related_model)`` chain.
    The single call is safe only because ``registry.get`` itself honors ``_primaries``
    as its first return state; the Relay-shaped primary over a non-Relay sibling makes
    the pick visible as the generated class. The
    ``tests/types/test_definition_relations.py`` twin pins the same contract for
    ``DjangoTypeDefinition.related_target_for``.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    assert registry.get(library_models.Shelf) is ShelfType

    class AdminShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            primary = True
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(AdminShelfType, AdminShelfType.__django_strawberry_definition__)

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    shelf_field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(shelf_field, "shelf", "exact")
    assert isinstance(resolved, GlobalIDFilter)


def test_target_type_for_related_filter_registry_fallback_prefers_declared_primary() -> None:
    """The unbound-child fallback resolves the declared primary for the child model.

    Twin of ``test_relation_key_target_type_prefers_declared_primary`` for
    ``FilterSet._target_type_for_related_filter``: with no bound child
    owner the method resolves via ``registry.get(child_model)`` - NOT a
    ``registry.primary_for(child_model) or registry.get(child_model)``
    chain - so a shared-target primary wins here exactly as it does for every
    other plain-``get`` consumer.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    assert registry.get(library_models.Shelf) is ShelfType

    class AdminShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            primary = True

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    resolved = CategoryFilter._target_type_for_related_filter(RelatedFilter(ShelfFilter))
    assert resolved is AdminShelfType


@pytest.mark.django_db
def test_apply_related_constraints_skips_branch_without_qs_or_explicit() -> None:
    """An active branch with neither child qs nor explicit qs is skipped."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        # No explicit ``queryset=`` on the RelatedFilter.
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    parent_qs = library_models.Branch.objects.all()
    # Active ``shelves`` branch, but the child-qs map is empty AND the
    # RelatedFilter has no explicit queryset -> the branch is skipped.
    constrained = BranchFilter._apply_related_constraints(
        {"shelves": {"code": "x"}},
        parent_qs,
        {},
        None,
        {},
    )
    assert "shelves__in" not in str(constrained.query)


@pytest.mark.django_db
def test_normalize_input_operator_bag_exact_resolves_explicit_suffixed_key() -> None:
    """A literal __exact declaration retains its exact filter registry and normalized form keys."""
    services.seed_data(0)

    @dataclasses.dataclass
    class _NameBag:
        exact: object = None

    class WeirdCategoryFilter(FilterSet):
        name__exact = django_filters.CharFilter(field_name="name", lookup_expr="exact")

        class Meta:
            model = Category
            fields = []

    assert list(WeirdCategoryFilter.get_filters()) == ["name__exact"]
    data = WeirdCategoryFilter._normalize_input({"name_exact": _NameBag(exact="foo")})
    assert data == {"name__exact": "foo"}


def test_normalize_input_declared_head_keeps_its_form_key_and_skips_unset_lookup() -> None:
    """A declared head keeps its exact form key while an inactive lookup contributes none."""

    @dataclasses.dataclass
    class _CustomBag:
        i_contains: object = None
        starts_with: object = None

    class DeclaredCategoryFilter(FilterSet):
        custom = CharFilter(field_name="name", lookup_expr="icontains")

        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    # One active lookup plus one inactive entry keeps the scalar shape.
    data = DeclaredCategoryFilter._normalize_input(
        {"custom": _CustomBag(i_contains="foo", starts_with=UNSET)},
    )
    assert data == {"custom": "foo"}


@pytest.mark.django_db
def test_normalize_input_overlap_head_binds_named_generated_lookup() -> None:
    """A foreign single lookup over an overlap head binds the generated key.

    When a declared filter shares its head with generated lookups, the
    operator-bag attrs still map to their own django-filter lookups: a bag
    naming only ``icontains`` applies ``name__icontains`` rather than
    reinterpreting the value under the declared ``exact`` key.
    """

    @dataclasses.dataclass
    class _OverlapBag:
        exact: object = None
        i_contains: object = None

    class OverlapCategoryFilter(FilterSet):
        name = CharFilter(field_name="name", lookup_expr="exact")

        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    data = OverlapCategoryFilter._normalize_input(
        {"name": _OverlapBag(exact=UNSET, i_contains="Zulu")},
    )
    assert data == {"name__icontains": "Zulu"}


@pytest.mark.django_db
def test_normalize_input_overlap_head_mapping_binds_named_generated_lookup() -> None:
    """The mapping twin of the overlap binding: same generated key."""

    class OverlapMappingFilter(FilterSet):
        name = CharFilter(field_name="name", lookup_expr="exact")

        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    data = OverlapMappingFilter._normalize_input({"name": {"i_contains": "Zulu"}})
    assert data == {"name__icontains": "Zulu"}


@pytest.mark.django_db
def test_normalize_input_overlap_head_declared_lookup_keeps_declared_key() -> None:
    """The declared filter's own lookup still binds the declared key.

    The generated-key binding covers only lookups the declared filter does
    not own; the declared lookup keeps its single form key.
    """

    @dataclasses.dataclass
    class _OverlapBag:
        exact: object = None
        i_contains: object = None

    class OverlapOwnFilter(FilterSet):
        name = CharFilter(field_name="name", lookup_expr="exact")

        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    data = OverlapOwnFilter._normalize_input(
        {"name": _OverlapBag(exact="Zulu", i_contains=UNSET)},
    )
    assert data == {"name": "Zulu"}


@pytest.mark.parametrize(
    ("bag", "form_data"),
    [
        pytest.param(
            {"i_contains": "dune"},
            {"name__icontains": "dune"},
            id="generated-lookup-alone",
        ),
        pytest.param({"i_exact": "dune"}, {"name": "dune"}, id="declared-lookup-alone"),
        pytest.param(
            {"i_exact": "dune", "i_contains": "messiah"},
            {"name": "dune", "name__icontains": "messiah"},
            id="both-lookups-and",
        ),
        pytest.param(
            {"i_exact": "dune messiah", "i_contains": "dune"},
            {"name": "dune messiah", "name__icontains": "dune"},
            id="both-lookups-matching-rows",
        ),
    ],
)
def test_normalize_input_overlap_head_binds_each_lookup_to_its_own_filter(
    bag: dict[str, object],
    form_data: dict[str, object],
) -> None:
    """Each operator bag keeps its exact private normalized django-filter form keys."""

    class OverlapBranchFilter(FilterSet):
        name = CharFilter(lookup_expr="iexact")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["icontains"]}

    assert OverlapBranchFilter._normalize_input({"name": bag}) == form_data


@pytest.mark.parametrize(
    ("bag", "form_data"),
    [
        pytest.param({"exact": "dune"}, {"name": "dune"}, id="declared-exact"),
        pytest.param(
            {"i_contains": "dune"},
            {"name__icontains": "dune"},
            id="generated-icontains",
        ),
    ],
)
def test_normalize_input_declared_head_with_its_own_field_name(
    bag: dict[str, object],
    form_data: dict[str, object],
) -> None:
    """Each operator bag keeps its exact private normalized django-filter form keys."""

    class CityNameBranchFilter(FilterSet):
        name = CharFilter(field_name="city")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["icontains"]}

    assert CityNameBranchFilter._normalize_input({"name": bag}) == form_data


@pytest.mark.django_db
@pytest.mark.parametrize("lookup", ["i_exact", "in_"])
def test_normalize_input_declared_fk_head_keeps_the_generated_in_lookup(lookup: str) -> None:
    """A declared relation head retains its distinct generated membership form key."""

    class BranchNameShelfFilter(FilterSet):
        branch = CharFilter(field_name="branch__name", lookup_expr="iexact")

        class Meta:
            model = library_models.Shelf
            fields = {"branch": ["exact", "in"]}

    value, form_data = {
        "i_exact": ("alpha", {"branch": "alpha"}),
        "in_": ([17], {"branch__in": [17]}),
    }[lookup]
    assert BranchNameShelfFilter._normalize_input({"branch": {lookup: value}}) == form_data


@pytest.mark.parametrize(
    ("filter_input", "form_data"),
    [
        pytest.param(
            {"branch_title": {"i_contains": "lph"}},
            {"branch__title": "lph"},
            id="declared-child-icontains",
        ),
        pytest.param(
            {"branch_name_exact": {"exact": "Alpha"}},
            {"branch__name__exact": "Alpha"},
            id="declared-child-named-like-a-lookup",
        ),
        pytest.param(
            {"branch_name": {"exact": "Beta"}},
            {"branch__name": "Beta"},
            id="generated-child-exact",
        ),
    ],
)
def test_normalize_input_flat_expanded_children_bind_their_expanded_form_keys(
    filter_input: dict[str, object],
    form_data: dict[str, object],
) -> None:
    """Each operator bag keeps its exact private normalized django-filter form keys."""
    _register_plain_types(library_models.Branch)

    class ChildBranchFilter(FilterSet):
        title = CharFilter(field_name="name", lookup_expr="icontains")
        name__exact = CharFilter(field_name="name", lookup_expr="exact")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    class ParentShelfFilter(FilterSet):
        branch = RelatedFilter(ChildBranchFilter, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = []

    assert ParentShelfFilter._normalize_input(filter_input) == form_data


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("filter_input", "form_data"),
    [
        pytest.param(
            {"branch__name": {"i_contains": "lph"}},
            {"branch__name__icontains": "lph"},
            id="head-spelling",
        ),
        pytest.param(
            {"branch_name": {"i_contains": "lph"}},
            {"branch__name__icontains": "lph"},
            id="input-attr-spelling",
        ),
        pytest.param(
            {"branch__name": "lph"},
            {"branch__name__icontains": "lph"},
            id="bare-value-takes-the-only-lookup",
        ),
        pytest.param({"code": "A1"}, {"code": "A1"}, id="bare-value-takes-exact"),
    ],
)
def test_normalize_input_direct_mapping_without_a_built_input_class(
    filter_input: dict[str, object],
    form_data: dict[str, object],
) -> None:
    """A hand-built mapping on a never-built filter set reads the same lookup table."""

    class DirectShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"branch__name": ["icontains"], "code": ["exact", "icontains"]}

    assert DirectShelfFilter._normalize_input(filter_input) == form_data
    assert not any(owner is DirectShelfFilter for owner, _attr in _field_specs)


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        pytest.param({"name": "Alpha"}, ["name"], id="active"),
        pytest.param({}, [], id="omitted"),
        pytest.param({"name": None}, [], id="inactive"),
    ],
)
def test_check_permissions_falls_back_to_active_input_when_no_requested_fields(
    data: dict[str, object],
    expected: list[str],
) -> None:
    """Without explicit requested fields, only the active form field dispatches its gate."""
    fired: list[str] = []
    request = HttpRequest()

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def check_name_permission(self, actual_request: object) -> None:
            assert actual_request is request
            fired.append("name")

    instance = BranchFilter(data=data, queryset=library_models.Branch.objects.none())
    instance.check_permissions(request)
    assert fired == expected


@pytest.mark.django_db
def test_iter_visibility_steps_yields_pre_await_tuple_for_active_branches() -> None:
    """``_iter_visibility_steps`` yields the shared pre-await state both derive methods consume.

    Pins the shared path: both
    ``_derive_related_visibility_querysets_sync`` and
    ``_derive_related_visibility_querysets_async`` route through the
    single ``_iter_visibility_steps`` classmethod, so the helper's
    five-tuple shape (``field_name, target_type, child_filterset,
    child_input, child_base``) is the load-bearing contract. Branches
    missing ``target_type`` or ``child_filterset`` raise (see the
    sibling fail-loud test) so the derive methods carry only the two
    awaits / calls per step.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    steps = list(
        BranchFilter._iter_visibility_steps({"shelves": {"code": "A"}}),
    )
    assert len(steps) == 1
    field_name, target_type, child_filterset, child_input, child_base = steps[0]
    assert field_name == "shelves"
    assert target_type is ShelfType
    assert child_filterset is ShelfFilter
    assert child_input == {"code": "A"}
    assert child_base.model is library_models.Shelf


def test_registering_an_async_related_target_keeps_its_class_identity() -> None:
    """Registered class identity is private; the native nested OR holder owns actual async execution."""

    async def visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        _info: object,
    ) -> QuerySet[library_models.Shelf]:
        return queryset

    target = type(
        "RegisteredAsyncShelf",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.Shelf, "fields": ("id", "code")}),
            "get_queryset": classmethod(visible),
        },
    )
    assert registry.get(library_models.Shelf) is target


@pytest.mark.django_db
def test_apply_async_runs_permission_checks_off_event_loop_thread() -> None:
    """A blocking ``check_*_permission`` hook does not block the event loop.

    ``apply_async`` routes finalize (incl. permission checks) through
    ``run_in_one_sync_boundary``.

    Asserts the permission method observed a thread ident DIFFERENT from
    the event-loop thread ident -- which is what
    ``sync_to_async(thread_sensitive=True)`` guarantees. Run inline on the
    event-loop thread, ``_run_permission_checks`` would make the two ident
    reads match.
    """
    captured: dict[str, int] = {}

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, _request: object) -> None:
            captured["permission_thread"] = threading.get_ident()

    async def _run() -> int:
        captured["event_loop_thread"] = threading.get_ident()
        await CategoryFilter.apply_async(
            {"name": "alpha"},
            Category.objects.all(),
            _make_info(),
        )
        return captured["event_loop_thread"]

    event_loop_thread = asyncio.run(_run())
    assert captured["permission_thread"] != event_loop_thread


@pytest.mark.django_db
def test_apply_async_collect_nested_visibility_querysets_pre_derives_or_branch() -> None:
    """The nested-visibility pre-walk keys its awaited map on ``id(child_input)`` per ``or`` arm.

    The pre-walk is ``_collect_nested_visibility_querysets_async``.

    Unit-level pin on the new helper -- given an ``or_`` input shape with
    one inner branch carrying an active ``RelatedFilter``, the helper
    returns a map whose only key is ``id`` of that nested child dict, and
    whose value carries the ``shelves`` queryset derived via the async
    path.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    inner = {"shelves": {"code": "A"}}
    result = asyncio.run(
        BranchFilter._collect_nested_visibility_querysets_async(
            {"or_": [inner]},
            _make_info(),
            flat_hop_visibility={},
        ),
    )
    assert id(inner) in result
    assert "shelves" in result[id(inner)]
    assert result[id(inner)]["shelves"].model is library_models.Shelf
    assert registry.get(library_models.Shelf) is ShelfType


@pytest.mark.parametrize(
    ("shape", "expected"),
    [
        pytest.param("none", [], id="none"),
        pytest.param("unset", [], id="unset"),
        pytest.param("non-walkable", [], id="non-walkable"),
        pytest.param("dataclass", ["name"], id="dataclass"),
        pytest.param("dict", ["name"], id="dict"),
    ],
)
def test_active_permission_leaf_paths_covers_input_shapes(shape: str, expected: list[str]) -> None:
    """The leaf-path walker ignores inactive/scalar inputs and excludes related and logical keys."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    @dataclasses.dataclass
    class _Input:
        name: object = None
        shelves: object = None
        and_: object = None

    inputs: dict[str, object] = {
        "none": None,
        "unset": UNSET,
        "non-walkable": 42,
        "dataclass": _Input(name="x", shelves={"code": "y"}, and_=[{"name": "z"}]),
        "dict": {"name": "x"},
    }
    assert BranchFilter._active_permission_targets(inputs[shape])[0] == expected


@pytest.mark.parametrize("kind", ["text", "datetime", "missing"])
def test_lookups_for_field_returns_concrete_lookups_and_excludes_transforms(kind: str) -> None:
    """The lookup reader lists concrete field lookups, excludes transforms and handles no field."""
    if kind == "missing":
        assert _lookups_for_field(None) == []
        return
    if kind == "text":
        field = Category._meta.get_field("name")
        required = {
            "exact",
            "icontains",
            "gt",
            "lt",
            "in",
            "range",
            "isnull",
            "startswith",
        }
        excluded: set[str] = set()
    else:
        field = Category._meta.get_field("created_date")
        required = {"exact", "gt", "lt"}
        excluded = {
            "year",
            "month",
            "day",
            "date",
            "time",
            "week",
        }
    lookups = set(_lookups_for_field(field))
    assert required <= lookups
    assert excluded.isdisjoint(lookups)


def test_collect_nested_visibility_querysets_async_returns_empty_for_none_input() -> None:
    """``_collect_nested_visibility_querysets_async(None, ...)`` short-circuits to ``{}``.

    The ``input_value is None or input_value is UNSET`` guard returns the
    empty map before any branch walk -- the apply_async pre-pass over a
    branch with no nested logical input does no work.
    """

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    result = asyncio.run(
        BranchFilter._collect_nested_visibility_querysets_async(
            None,
            _make_info(),
            flat_hop_visibility={},
        ),
    )
    assert result == {}


def test_collect_nested_visibility_querysets_async_skips_none_child_branch() -> None:
    """A ``None`` child inside a logical branch is skipped without a derive.

    ``{"or": [None]}`` yields a single ``None`` child; the child loop's
    ``if child_input is None or child_input is UNSET: continue`` skips it, so
    no visibility derive runs and the result stays empty.
    """

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    result = asyncio.run(
        BranchFilter._collect_nested_visibility_querysets_async(
            {"or": [None]},
            _make_info(),
            flat_hop_visibility={},
        ),
    )
    assert result == {}


@pytest.mark.parametrize(
    ("logic_input", "message"),
    list(
        zip(
            [
                {"or": {"shelves": {"code": {"exact": "A"}}}},
                {"and": ["bad_scalar"]},
                {"not": [{"shelves": {"code": {"exact": "A"}}}]},
            ],
            [
                "takes a list of filter inputs",
                "must be a mapping or filter-input",
                "takes a single filter input",
            ],
            strict=True,
        ),
    ),
    ids=["mapping-for-sequence", "scalar-element", "sequence-for-single"],
)
def test_collect_nested_visibility_querysets_async_rejects_malformed_logical_branch_before_hooks(
    logic_input: dict[str, object],
    message: str,
) -> None:
    """Malformed logical input on the async path is rejected before related visibility queries run."""
    visibility_called: list[str] = []

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[library_models.Shelf],
            info: object,
        ) -> QuerySet[library_models.Shelf]:
            visibility_called.append("shelf")
            return queryset

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError, match=message):
        asyncio.run(
            BranchFilter._collect_nested_visibility_querysets_async(
                logic_input,
                _make_info(),
                flat_hop_visibility={},
            ),
        )
    assert visibility_called == []
    assert registry.get(library_models.Shelf) is ShelfType


@pytest.mark.django_db
def test_q_for_branch_falls_back_to_sync_derive_on_stash_miss() -> None:
    """``_q_for_branch`` with a present-but-missing stash uses the sync-derive fallback.

    Under ``apply_sync`` and ``apply_async`` the nested visibility map is pre-derived
    and threaded through ``_nested_qs_by_branch_id`` keyed by ``id(child_input)``. A
    consumer who short-circuits past the pre-pass (modeled here by an empty stash
    dict, so ``.get(id(child_input))`` misses) still gets a correct result via
    the defensive sync-derive fallback rather than a ``None`` map.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf

    assert registry.get(library_models.Shelf) is ShelfType

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    child_input = {"shelves": {"code": "A"}}
    q = BranchFilter._q_for_branch(
        library_models.Branch.objects.all(),
        child_input,
        info=_make_info(),
        _nested_qs_by_branch_id={},  # present but empty -> stash miss -> sync fallback
        _flat_hop_visibility={},
    )
    assert isinstance(q, Q)


@pytest.mark.django_db
def test_q_for_branch_composes_arms_outside_the_pipeline() -> None:
    """A set built outside the apply pipeline composes its arms with no pre-derived stash.

    No pre-pass ran, so the instance carries no ``_nested_qs_by_branch_id`` stash;
    ``_q_for_branch`` derives each arm's (empty) branch map itself and the ``or``
    keeps the two branches its arms name.
    """

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    _seed_open_and_secret_match_shelves()
    library_models.Branch.objects.create(name="gamma")
    filter_set = BranchFilter(
        data={"or": [{"name": "alpha"}, {"name": "beta"}]},
        queryset=library_models.Branch.objects.order_by("name"),
    )
    assert filter_set._nested_qs_by_branch_id is None
    assert list(filter_set.qs.values_list("name", flat=True)) == ["alpha", "beta"]


def test_collect_related_declarations_honors_base_tombstone() -> None:
    """A direct base's non-related declaration removes a later inherited candidate."""

    class Declaration(RelatedFilter):
        @override
        def _bind_owner(self, owner: object) -> NoReturn:
            raise AssertionError(f"removed declaration was bound to {owner!r}")

    declaration = Declaration("ShelfFilter")

    class Base(FilterSet):
        related_declarations: OrderedDict[str, Declaration] = OrderedDict(probe=declaration)
        all_declarations = {"probe": object()}

    class Child(Base):
        pass

    collected = collect_related_declarations(
        Child,
        (Base,),
        own_items=(),
        declaration_type=Declaration,
        collection_attr="related_declarations",
        inherit_from_bases=True,
        base_declarations_attr="all_declarations",
    )

    assert collected == OrderedDict()


@pytest.mark.django_db
def test_iter_visibility_steps_threads_parent_db_alias() -> None:
    """The child visibility base is pinned to the parent request's DB alias.

    The cascade-permission path builds its base with
    ``._default_manager.using(queryset.db).all()``; the related-visibility path
    must match so an alias-sensitive ``get_queryset`` hook runs against the
    parent's shard rather than the default alias.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    assert registry.get(library_models.Shelf) is ShelfType

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    input_value = {"shelves": {"code": {"exact": "AAA"}}}
    aliased = list(BranchFilter._iter_visibility_steps(input_value, "shard_b"))
    assert aliased
    assert aliased[0][4].db == "shard_b"
    # No alias threaded -> the router default stays in place (single-DB case).
    default = list(BranchFilter._iter_visibility_steps(input_value))
    assert default
    assert default[0][4].db == "default"


@pytest.mark.django_db
def test_related_visibility_hook_receives_parent_db_alias() -> None:
    """The child ``get_queryset`` visibility hook runs against the parent's alias."""
    seen: list[str] = []

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[library_models.Shelf],
            info: object,
        ) -> QuerySet[library_models.Shelf]:
            seen.append(queryset.db)
            return queryset

    assert registry.get(library_models.Shelf) is ShelfType

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    BranchFilter._derive_related_visibility_querysets_sync(
        {"shelves": {"code": {"exact": "AAA"}}},
        _make_info(),
        parent_db="shard_b",
    )
    assert seen == ["shard_b"]


def test_apply_sync_caps_related_recursion_depth() -> None:
    """A private continuation counter isolates the sync entry point's depth guard.

    A request cannot supply ``_depth``. Real input-driven related and logical recursion
    lives in the raw-argument HTTP tests; this direct call reaches the later guard
    without being refused by an earlier traversal of the same request input.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter.apply_sync(
            {"name": "x"},
            Category.objects.all(),
            _make_info(),
            _depth=CategoryFilter._MAX_LOGIC_DEPTH + 1,
        )
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)


def test_apply_async_caps_related_recursion_depth() -> None:
    """Async sibling of ``test_apply_sync_caps_related_recursion_depth``."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError) as excinfo:
        asyncio.run(
            CategoryFilter.apply_async(
                {"name": "x"},
                Category.objects.all(),
                _make_info(),
                _depth=CategoryFilter._MAX_LOGIC_DEPTH + 1,
            ),
        )
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)


@pytest.mark.parametrize("operator", ["and", "not"], ids=["multi-branch", "single-branch"])
def test_validate_logic_branch_shape_accepts_inactive_value(operator: str) -> None:
    """An inactive logical value is accepted by either container-shape validator."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._validate_logic_branch_shape(operator, None)


@pytest.mark.parametrize(
    ("operator", "value"),
    [
        pytest.param("or", [None, {"name": {"exact": "x"}}], id="or-leading-inactive"),
        pytest.param("and", [{"name": {"exact": "x"}}, None], id="and-trailing-inactive"),
    ],
)
def test_validate_logic_branch_shape_accepts_inactive_list_element(
    operator: str,
    value: list[object],
) -> None:
    """A None list arm is inactive in either multi-branch operator and at either list position."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._validate_logic_branch_shape(operator, value)


@pytest.mark.parametrize(
    ("input_value", "expected", "message"),
    [
        pytest.param(None, [], None, id="none"),
        pytest.param(UNSET, [], None, id="unset"),
        pytest.param(
            {
                "and": [{"name": {"exact": "a"}}, None],
                "or": [None],
                "not": {"name": {"exact": "b"}},
            },
            [("and", [{"name": {"exact": "a"}}]), ("not", [{"name": {"exact": "b"}}])],
            None,
            id="wire-keys-and-inactive-arms",
        ),
        pytest.param(
            {"and_": [{"name": {"exact": "a"}}], "or_": None, "not_": None},
            [("and", [{"name": {"exact": "a"}}])],
            None,
            id="python-keys-and-inactive-operators",
        ),
        pytest.param(
            {"or": {"name": {"exact": "x"}}},
            None,
            "takes a list of filter inputs",
            id="mapping-for-sequence-refused",
        ),
    ],
)
def test_iter_logic_branches_walks_active_branches_and_filters_inactive(
    input_value: object,
    expected: list[tuple[str, list[dict[str, object]]]] | None,
    message: str | None,
) -> None:
    """The private walker preserves operator order, skips inactive arms and refuses bad containers."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    if message is not None:
        with pytest.raises(ConfigurationError, match=message):
            list(CategoryFilter._iter_logic_branches(input_value))
        return
    branches = [
        (operator.wire_name, children)
        for operator, children in CategoryFilter._iter_logic_branches(input_value)
    ]
    assert branches == expected


def test_generation_provenance_framework_default_for_generated_leaf() -> None:
    """A plainly generated CharFilter leaf is ``framework_default``, no distinct."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["icontains"]}

    leaf = BookFilter.get_filters()["title__icontains"]
    record = filter_generation_provenance(leaf)
    assert record == FilterGenerationProvenance(
        origin="framework_default",
        framework_added_distinct=False,
    )
    assert _expansion_record(leaf) is None


def test_generation_provenance_package_replacement_for_own_pk_global_id() -> None:
    """The own-PK GlobalID branch stamps ``package_replacement`` on the new instance."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(CategoryType, CategoryType.__django_strawberry_definition__)

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._owner_definition = CategoryType.__django_strawberry_definition__
    pk_field = Category._meta.pk

    resolved = CategoryFilter.filter_for_field(pk_field, "id", "exact")
    assert isinstance(resolved, GlobalIDFilter)
    record = filter_generation_provenance(resolved)
    assert record is not None
    assert record.origin == "package_replacement"
    assert record.framework_added_distinct is False


def test_generation_provenance_package_replacement_for_relay_relation() -> None:
    """The Relay-relation branch stamps ``package_replacement`` on the new instance."""

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("genres")
    resolved = BookFilter.filter_for_field(field, "genres")
    assert isinstance(resolved, GlobalIDMultipleChoiceFilter)
    record = filter_generation_provenance(resolved)
    assert record is not None
    assert record.origin == "package_replacement"
    # ``genres`` is an M2M (a many-side hop), so the framework adds distinct.
    assert record.framework_added_distinct is True


def test_generation_provenance_declared_for_consumer_declared_filter() -> None:
    """A consumer-declared filter attribute is ``declared``."""

    class BookFilter(FilterSet):
        title_search = django_filters.CharFilter(field_name="title")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    leaf = BookFilter.get_filters()["title_search"]
    record = filter_generation_provenance(leaf)
    assert record == FilterGenerationProvenance(origin="declared")


def test_generation_provenance_override_generated_for_meta_filter_overrides() -> None:
    """A leaf produced through ``Meta.filter_overrides`` is ``override_generated``.

    The override must GENUINELY diverge from the package policy: ownership is a
    normalized VALUE comparison, so a ``filter_overrides`` entry
    byte-equal to the package default (same ``filter_class``, no ``extra``) is
    framework-equivalent -- the generated filter would be identical to the package's own.
    A consumer ``extra`` provider (here ``required=True``) makes the normalized entry
    diverge, which is the real consumer-owned case.
    """

    def _override_extra(_f: object) -> dict[str, object]:
        return {"required": True}

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}
            # ``Book.title`` is a ``TextField``; key the override on its class so
            # ``try_dbfield`` matches it (the framework mirrors django-filter's
            # own MRO-walked override selection). The consumer ``extra`` provider
            # diverges the normalized entry from the package default.
            filter_overrides = {
                models.TextField: {
                    "filter_class": django_filters.CharFilter,
                    "extra": _override_extra,
                },
            }

    leaf = BookFilter.get_filters()["title"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"


def test_generation_provenance_framework_added_distinct_for_to_many_path() -> None:
    """A generated to-many path leaf records ``framework_added_distinct=True``."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    leaf = BookFilter.get_filters()["genres__name__icontains"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "framework_default"
    assert record.framework_added_distinct is True
    assert leaf.distinct is True


def test_generation_provenance_framework_added_distinct_false_for_to_one_path() -> None:
    """A generated to-one path leaf records ``framework_added_distinct=False``."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"shelf__code": ["icontains"]}

    leaf = BookFilter.get_filters()["shelf__code__icontains"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.framework_added_distinct is False
    assert leaf.distinct is False


def test_generation_provenance_expanded_leaf_inherits_generated_child_origin() -> None:
    """An expanded leaf inherits the child leaf's origin and records the child filter it copies."""

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["icontains"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    leaf = BookFilter.get_filters()["genres__name__icontains"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "framework_default"
    assert _expansion_record(leaf) == ChildProjection(GenreFilter, "name__icontains", "genres")


def test_generation_provenance_expanded_leaf_of_declared_child_stays_declared() -> None:
    """Appearing in expansion output does not make a DECLARED child expanded-generated."""

    class GenreFilter(FilterSet):
        label = django_filters.CharFilter(field_name="name")

        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    leaf = BookFilter.get_filters()["genres__label"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "declared"
    assert _expansion_record(leaf) == ChildProjection(GenreFilter, "label", "genres")


def test_generation_provenance_expanded_leaf_of_unstamped_child_stays_none() -> None:
    """An expanded copy of an UNSTAMPED child leaf inherits no record (fail closed)."""

    class GenreFilter(FilterSet):
        @classmethod
        @override
        def filter_for_field(
            cls,
            field: ModelField,
            field_name: str,
            lookup_expr: str | None = None,
        ) -> CharFilter:
            # Returns its OWN object, so the child leaf carries no framework record.
            return django_filters.CharFilter(field_name=field_name)

        class Meta:
            model = library_models.Genre
            fields = {"name": ["icontains"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    leaf = BookFilter.get_filters()["genres__name__icontains"]
    assert filter_generation_provenance(leaf) is None


def test_generation_provenance_none_for_consumer_overridden_filter_for_field() -> None:
    """A consumer ``filter_for_field`` returning its OWN object yields no record."""

    class OverridingFilter(FilterSet):
        @classmethod
        @override
        def filter_for_field(
            cls,
            field: ModelField,
            field_name: str,
            lookup_expr: str | None = None,
        ) -> CharFilter:
            return django_filters.CharFilter(field_name=field_name)

        class Meta:
            model = library_models.Book
            fields = {"title": ["icontains"]}

    leaf = OverridingFilter.get_filters()["title__icontains"]
    assert filter_generation_provenance(leaf) is None


def test_generation_provenance_survives_deepcopy_and_per_request_instance() -> None:
    """The record survives ``copy.deepcopy`` and the per-request instance filters."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"], "title": ["exact"]}

    base_leaf = BookFilter.get_filters()["genres__name__icontains"]
    clone = copy.deepcopy(base_leaf)
    clone_record = filter_generation_provenance(clone)
    assert clone_record is not None
    assert clone_record.framework_added_distinct is True

    instance = BookFilter(
        data={},
        queryset=library_models.Book.objects.all(),
        request=None,
    )
    instance_record = filter_generation_provenance(instance.filters["genres__name__icontains"])
    assert instance_record is not None
    assert instance_record.origin == "framework_default"
    assert instance_record.framework_added_distinct is True


def test_generation_provenance_declared_never_restamped_by_later_machinery() -> None:
    """A declared filter's record is stamped once and never overwritten."""

    class BookFilter(FilterSet):
        custom = django_filters.CharFilter(field_name="title")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    declared = BookFilter.declared_filters["custom"]
    first = filter_generation_provenance(declared)
    assert first is not None
    assert first.origin == "declared"

    # Repeated expansion passes must not restamp (same identity preserved).
    BookFilter.get_filters()
    BookFilter.get_filters()
    assert filter_generation_provenance(declared) is first


def test_a_borrowed_generated_leaf_gets_its_own_declared_provenance_and_no_candidate() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """

    class SourceBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

    assert SourceBookFilter._is_generation_capable() is True
    SourceBookFilter.get_filters()
    source_leaf = SourceBookFilter.base_filters["loans__note__icontains"]
    source_record = filter_generation_provenance(source_leaf)
    assert source_record is not None
    assert source_record.origin == "framework_default"
    borrowed = copy.deepcopy(source_leaf)
    assert _provenance(borrowed).origin == "framework_default"

    class DeclaredReuse(FilterSet):
        loans__note__icontains = borrowed

        class Meta:
            model = library_models.Book
            fields = {"title": ["icontains"]}

    own_decl = DeclaredReuse.declared_filters["loans__note__icontains"]
    assert own_decl is not borrowed
    assert _provenance(borrowed).origin == "framework_default"
    assert filter_generation_provenance(source_leaf) is source_record
    assert _provenance(own_decl).origin == "declared"
    DeclaredReuse.get_filters()
    snapshot = DeclaredReuse._expansion_snapshot()
    assert snapshot is not None
    assert "loans__note__icontains" not in snapshot.candidates


def test_inherited_declared_filter_retains_declared_record_unchanged() -> None:
    """Positive control: an INHERITED declared filter keeps its ``declared`` record.

    A subclass that does not re-declare the filter must not restamp or mangle the
    inherited declaration: it is the SAME instance, and its record (stamped once by
    the base class's metaclass run) is retained untouched.
    """

    class BaseDeclaredFilter(FilterSet):
        title_search = django_filters.CharFilter(field_name="title")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    base_decl = BaseDeclaredFilter.declared_filters["title_search"]
    base_record = filter_generation_provenance(base_decl)
    assert base_record == FilterGenerationProvenance(origin="declared")

    class SubDeclaredFilter(BaseDeclaredFilter):
        pass

    inherited = SubDeclaredFilter.declared_filters["title_search"]
    # Same instance, same record object -- not re-stamped by the subclass run.
    assert inherited is base_decl
    assert filter_generation_provenance(inherited) is base_record
    assert filter_generation_provenance(inherited) == FilterGenerationProvenance(origin="declared")


def test_inherited_declaration_without_record_is_backfilled() -> None:
    """The ``if provenance is None`` fallback backfills a record-less inheritance.

    The fallback is kept for an inherited declaration that somehow reaches
    the subclass metaclass run without a provenance record: it is stamped
    ``declared`` (never left record-less), while an inherited declaration that DOES
    carry a record is untouched (covered by the positive control above).
    """

    class BaseDeclaredFilter(FilterSet):
        title_search = django_filters.CharFilter(field_name="title")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    base_decl = BaseDeclaredFilter.declared_filters["title_search"]
    # Strip the record stamped at base creation to simulate an inherited
    # declaration that reaches the subclass metaclass run without one.
    base_decl.__dict__.pop(_GENERATION_PROVENANCE_ATTR, None)
    assert filter_generation_provenance(base_decl) is None

    class SubDeclaredFilter(BaseDeclaredFilter):
        pass

    inherited = SubDeclaredFilter.declared_filters["title_search"]
    assert inherited is base_decl
    assert filter_generation_provenance(inherited) == FilterGenerationProvenance(origin="declared")


def test_candidate_snapshot_rows_cover_direct_leaves_only() -> None:
    """A direct to-many leaf's row is eligible, a direct to-one leaf's is not, an expansion has none."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["icontains"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = {"title": ["icontains"], "genres__name": ["icontains"]}

    BookFilter.get_filters()
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None

    to_many_row = snapshot.candidates["genres__name__icontains"]
    assert to_many_row.eligible is True
    assert to_many_row.path_plan.first_many_index is not None
    # Classified against the ROOT model (Book), on the model-field path.
    assert to_many_row.path_plan.model is library_models.Book
    assert to_many_row.path_plan.path == "genres__name"
    assert to_many_row.provenance.origin == "framework_default"

    to_one_row = snapshot.candidates["title__icontains"]
    assert to_one_row.eligible is False
    assert to_one_row.path_plan.first_many_index is None
    assert to_one_row.provenance.origin == "framework_default"
    assert _expansion_record(snapshot.filters["title__icontains"]) is None

    # The expansion is a framework-generated leaf of the child set, and still rowless.
    expanded = snapshot.filters["shelf__code__icontains"]
    expanded_record = filter_generation_provenance(expanded)
    assert expanded_record is not None
    assert expanded_record.origin == "framework_default"
    assert _expansion_record(expanded) == ChildProjection(ShelfFilter, "code__icontains", "shelf")
    assert "shelf__code__icontains" not in snapshot.candidates


def test_candidate_snapshot_omits_declared_and_method_filters() -> None:
    """Declared filters (incl. method filters) are ``declared`` origin -> no row."""

    class BookFilter(FilterSet):
        title_search = django_filters.CharFilter(field_name="title")
        note_method = django_filters.CharFilter(
            field_name="title",
            method="filter_note",
        )

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

        def filter_note(
            self,
            queryset: QuerySet[library_models.Book],
            _name: str,
            _value: object,
        ) -> QuerySet[library_models.Book]:
            return queryset

    BookFilter.get_filters()
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    # A framework-generated leaf DOES get a row ...
    assert "title" in snapshot.candidates
    # ... but declared / method-carrying declared leaves do NOT (fail closed).
    assert "title_search" not in snapshot.candidates
    assert "note_method" not in snapshot.candidates


def test_candidate_snapshot_omits_override_generated_leaf() -> None:
    """A ``Meta.filter_overrides`` product is ``override_generated`` -> no row.

    The override must GENUINELY diverge from the package policy (a consumer ``extra``
    provider here): a byte-equal override is framework-equivalent under the normalized
    value comparison and would keep its row.
    """

    def _override_extra(_f: object) -> dict[str, object]:
        return {"required": True}

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}
            filter_overrides = {
                django_models.TextField: {
                    "filter_class": django_filters.CharFilter,
                    "extra": _override_extra,
                },
            }

    BookFilter.get_filters()
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "title" not in snapshot.candidates


def test_candidate_snapshot_includes_package_replacement_global_id_leaf() -> None:
    """An own-PK GlobalID ``package_replacement`` leaf gets a row (ineligible per path)."""

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"id": ["exact"], "name": ["icontains"]}

    GenreFilter._owner_definition = GenreType.__django_strawberry_definition__

    GenreFilter.get_filters()
    snapshot = GenreFilter._expansion_snapshot()
    assert snapshot is not None
    id_row = snapshot.candidates["id"]
    assert id_row.provenance.origin == "package_replacement"
    # The own PK is a local column (no many-side hop), so it is ineligible.
    assert id_row.eligible is False
    assert id_row.path_plan.first_many_index is None


def test_candidate_metadata_helper_raises_on_unclassifiable_framework_leaf() -> None:
    """A framework-generated leaf with an unresolvable path is a defect -> RAISES.

    Unreachable through the public pipeline (``get_model_field`` guards
    generation), so the internal build helper is exercised directly with a
    synthetic provenance-stamped filter whose ``field_name`` is garbage.
    """
    leaf = django_filters.CharFilter(field_name="not_a_real_field")
    _stamp_generation_provenance(
        leaf,
        FilterGenerationProvenance(origin="framework_default"),
    )
    with pytest.raises(PathResolutionError):
        _candidate_metadata_for(library_models.Book, leaf)


def test_candidate_metadata_helper_never_classifies_declared_leaf() -> None:
    """A declared leaf with a garbage path returns ``None`` and is NEVER classified."""
    leaf = django_filters.CharFilter(field_name="not_a_real_field")
    _stamp_generation_provenance(leaf, FilterGenerationProvenance(origin="declared"))
    # No raise despite the unresolvable path -- declared leaves fail closed.
    assert _candidate_metadata_for(library_models.Book, leaf) is None


def test_candidate_metadata_helper_returns_none_for_unstamped_leaf() -> None:
    """An unstamped (consumer-returned) leaf has no record -> no row, fail closed."""
    leaf = django_filters.CharFilter(field_name="genres__name")
    assert _candidate_metadata_for(library_models.Book, leaf) is None


def test_expansion_snapshot_build_failure_publishes_nothing_then_retry_recovers() -> None:
    """A mid-build classification failure publishes NOTHING; a retry republishes both."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"], "genres__name": ["icontains"]}

    real_classify = classify_path
    calls = {"n": 0}

    def flaky_classify(model: type[django_models.Model], field_path: str) -> ClassifiedPath:
        calls["n"] += 1
        if calls["n"] >= 2:
            raise PathResolutionError(model, field_path, field_path)
        return real_classify(model, field_path)

    unpublished = BookFilter.base_filters
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(sets_module, "classify_path", flaky_classify)
    try:
        with pytest.raises(PathResolutionError):
            BookFilter.get_filters()
        # A failed publication published neither the table nor the snapshot.
        assert "_expanded_snapshot" not in BookFilter.__dict__
        assert BookFilter.base_filters is unpublished
        assert BookFilter._expansion_snapshot() is None
    finally:
        monkeypatch.undo()

    # After un-patching, the next build succeeds and republishes both together.
    filters = BookFilter.get_filters()
    assert "genres__name__icontains" in filters
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "genres__name__icontains" in snapshot.candidates


def test_expansion_snapshot_is_isolated_per_subclass() -> None:
    """A subclass builds its OWN snapshot and never observes its parent's."""

    class BaseBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

    class SubBookFilter(BaseBookFilter):
        pass

    BaseBookFilter.get_filters()
    parent_snapshot = BaseBookFilter._expansion_snapshot()
    assert parent_snapshot is not None

    SubBookFilter.get_filters()
    sub_snapshot = SubBookFilter._expansion_snapshot()
    assert sub_snapshot is not None
    # Distinct objects; the subclass never inherits the parent's classification.
    assert sub_snapshot is not parent_snapshot
    # The parent's snapshot is unchanged by the subclass build.
    assert BaseBookFilter._expansion_snapshot() is parent_snapshot


def test_expansion_snapshot_absent_for_unresolved_lazy_target() -> None:
    """A ``RelatedFilter`` naming a not-registered target caches no snapshot; each call rebuilds."""

    class BranchFilter(FilterSet):
        # A reference to a non-existent class - expansion raises and nothing
        # (neither the filter cache nor the snapshot) is published, mirroring
        # ``test_filterset_get_filters_does_not_cache_when_string_filterset_remains``.
        bogus = RelatedFilter("DefinitelyDoesNotExistFilter", field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    with pytest.raises(ImportError):
        BranchFilter.get_filters()
    assert BranchFilter._expansion_snapshot() is None
    assert "_expanded_snapshot" not in BranchFilter.__dict__
    # Each call re-attempts the build (no half-built snapshot is ever cached).
    with pytest.raises(ImportError):
        BranchFilter.get_filters()
    assert BranchFilter._expansion_snapshot() is None


def test_expansion_snapshot_none_before_build_is_the_fail_closed_hook() -> None:
    """Pre-finalization (no snapshot built), the accessor returns None for the adapter."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter("ShelfFilter", field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # No ``get_filters`` build has cached a snapshot yet: the accessor is None,
    # so a filterset instantiated before its lazy targets resolve presents the
    # unexpanded surface and every flat name is absent from the (absent)
    # mapping -- the adapter runs every leaf's plain outer invocation.
    assert ShelfFilter._expansion_snapshot() is None
    assert BranchFilter._expansion_snapshot() is None
    instance = BranchFilter(
        data={},
        queryset=library_models.Branch.objects.all(),
        request=None,
    )
    assert type(instance)._expansion_snapshot() is None


def test_expansion_snapshot_reset_by_registry_clear_and_rebuilt_fresh() -> None:
    """``registry.clear()`` resets filters + metadata together; the next build republishes."""

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["icontains"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    BookFilter.get_filters()
    snapshot = BookFilter._expansion_snapshot()
    assert snapshot is not None
    assert "genres__name__icontains" in snapshot.filters
    assert "title" in snapshot.candidates

    registry.clear()

    # The snapshot slot is gone from the class dict together with the filter
    # cache -- no stale metadata observable between the clear and the rebuild.
    assert "_expanded_snapshot" not in BookFilter.__dict__
    assert "_expanded_filters" not in BookFilter.__dict__
    assert BookFilter._expansion_snapshot() is None

    BookFilter.get_filters()
    rebuilt = BookFilter._expansion_snapshot()
    assert rebuilt is not None
    assert rebuilt is not snapshot
    assert "genres__name__icontains" in rebuilt.filters
    assert "title" in rebuilt.candidates


def _reserved_aliases(queryset: QuerySet[django_models.Model]) -> list[str]:
    """Return the reserved ``_dst_predicate_`` EXISTS aliases attached to ``queryset``."""
    return [n for n in queryset.query.annotations if n.startswith("_dst_predicate_")]


def test_a_no_op_constructor_keeps_the_frozen_candidate_unroutable() -> None:
    """Generation capability, candidate bits and the Python selected class are private metadata.

    Native outer JOIN semantics, exact occurrences and query counts are owned by
    ``examples/fakeshop/test_query/test_filter_querysets_api.py::test_parent_generation_seams_keep_their_outer_join_and_authored_occurrences``.
    """

    class InitOverrideFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

    assert InitOverrideFilter._is_generation_capable() is False
    InitOverrideFilter.get_filters()
    row = _snapshot(InitOverrideFilter).candidates["loans__note__icontains"]
    assert row.eligible is True
    assert row.routable is False


def test_a_mutating_generation_hook_keeps_its_frozen_candidate_unroutable() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """

    class MutatingFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

        @classmethod
        @override
        def filter_for_field(
            cls,
            field: ModelField,
            field_name: str,
            lookup_expr: str | None = None,
        ) -> Filter:
            leaf = super().filter_for_field(field, field_name, lookup_expr)
            assert leaf is not None
            leaf.exclude = True  # consumer mutation of the framework-stamped leaf
            return leaf

    assert MutatingFilter._is_generation_capable() is False
    MutatingFilter.get_filters()
    row = _snapshot(MutatingFilter).candidates["loans__note__icontains"]
    assert row.eligible is True
    assert row.routable is False


def test_filter_override_distinct_is_preserved_on_to_many_path() -> None:
    """A consumer ``distinct=True`` override reaches the leaf without a framework stamp.

    The override owns the selection, so the to-many path grants no framework
    ``distinct``: the ``True`` on the leaf can only have come from the consumer's
    ``extra`` provider, and the provenance record records no framework stamp.
    """

    def _override_extra(_field: object) -> dict[str, object]:
        return {"distinct": True}

    class OverrideFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}
            filter_overrides = {
                django_models.TextField: {"filter_class": CharFilter, "extra": _override_extra},
            }

    leaf = OverrideFilter.get_filters()["loans__note__icontains"]
    assert leaf.distinct is True
    provenance = filter_generation_provenance(leaf)
    assert provenance is not None
    assert provenance.origin == "override_generated"
    assert provenance.framework_added_distinct is False


def test_filter_for_lookup_override_own_relay_pk_is_preserved() -> None:
    """A consumer ``filter_for_lookup`` override is not replaced with GlobalID."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(CategoryType, CategoryType.__django_strawberry_definition__)

    class OverrideFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"id": ["exact"]}

        @classmethod
        @override
        def filter_for_lookup(
            cls,
            field: ModelField,
            lookup_type: str,
        ) -> tuple[type[CharFilter], dict[str, object]]:
            return CharFilter, {}

    OverrideFilter._owner_definition = CategoryType.__django_strawberry_definition__
    leaf = OverrideFilter.get_filters()["id"]
    assert isinstance(leaf, CharFilter)
    assert not isinstance(leaf, GlobalIDFilter)
    provenance = filter_generation_provenance(leaf)
    assert provenance is not None
    assert provenance.origin == "override_generated"
    assert provenance.framework_added_distinct is False


def test_filter_override_extra_only_does_not_add_distinct_on_to_many_path() -> None:
    """An extra-only consumer override keeps the default distinct value."""

    def _override_extra(_field: object) -> dict[str, object]:
        return {}

    class OverrideFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}
            filter_overrides = {
                django_models.TextField: {"filter_class": CharFilter, "extra": _override_extra},
            }

    leaf = OverrideFilter.get_filters()["loans__note__icontains"]
    assert leaf.distinct is False
    provenance = filter_generation_provenance(leaf)
    assert provenance is not None
    assert provenance.origin == "override_generated"
    assert provenance.framework_added_distinct is False
    snapshot = OverrideFilter._expansion_snapshot()
    assert snapshot is not None
    assert "loans__note__icontains" not in snapshot.candidates


def test_filter_override_own_relay_pk_is_preserved() -> None:
    """A consumer own-PK override is not replaced with a GlobalID filter."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(CategoryType, CategoryType.__django_strawberry_definition__)

    def _override_extra(_field: object) -> dict[str, object]:
        return {}

    class OverrideFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"id": ["exact"]}
            filter_overrides = {
                django_models.BigAutoField: {"filter_class": CharFilter, "extra": _override_extra},
            }

    OverrideFilter._owner_definition = CategoryType.__django_strawberry_definition__
    leaf = OverrideFilter.get_filters()["id"]
    assert isinstance(leaf, CharFilter)
    assert not isinstance(leaf, GlobalIDFilter)
    provenance = filter_generation_provenance(leaf)
    assert provenance is not None
    assert provenance.origin == "override_generated"


def test_a_parent_lookup_override_keeps_its_custom_class_and_unroutable_candidate() -> None:
    """Generation capability, candidate bits and the Python selected class are private metadata.

    Native outer JOIN semantics, exact occurrences and query counts are owned by
    ``examples/fakeshop/test_query/test_filter_querysets_api.py::test_parent_generation_seams_keep_their_outer_join_and_authored_occurrences``.
    """

    class CustomGenerated(django_filters.CharFilter):
        """A consumer-owned generated filter class returned from filter_for_lookup."""

    class LookupOverrideFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

        @classmethod
        @override
        def filter_for_lookup(
            cls,
            field: ModelField,
            lookup_type: str,
        ) -> tuple[type[Filter] | None, dict[str, object]]:
            _default_class, params = super().filter_for_lookup(field, lookup_type)
            return CustomGenerated, params

    assert LookupOverrideFilter._is_generation_capable() is False
    LookupOverrideFilter.get_filters()
    leaf = LookupOverrideFilter.get_filters()["loans__note__icontains"]
    assert isinstance(leaf, CustomGenerated)
    row = _snapshot(LookupOverrideFilter).candidates["loans__note__icontains"]
    assert row.routable is False


def test_a_copied_defaults_table_keeps_the_frozen_candidate_unroutable() -> None:
    """Generation capability, candidate bits and the Python selected class are private metadata.

    Native outer JOIN semantics, exact occurrences and query counts are owned by
    ``examples/fakeshop/test_query/test_filter_querysets_api.py::test_parent_generation_seams_keep_their_outer_join_and_authored_occurrences``.
    """

    class DefaultsOverrideFilter(FilterSet):
        # A shadowing COPY is a NEW dict object, so it breaks the identity check against
        # ``_PUBLIC_PACKAGE_FILTER_DEFAULTS`` and the class is not generation-capable.
        FILTER_DEFAULTS = dict(FilterSet.FILTER_DEFAULTS)

        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

    assert DefaultsOverrideFilter._is_generation_capable() is False
    DefaultsOverrideFilter.get_filters()
    row = _snapshot(DefaultsOverrideFilter).candidates["loans__note__icontains"]
    assert row.routable is False


def test_an_instance_replacement_constructor_keeps_its_frozen_candidate_unroutable() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """

    class ReplacingFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)
            # Replace the deepcopied live filter with an unstamped title filter.
            self.filters["genres__name__icontains"] = CharFilter(
                field_name="title",
                lookup_expr="icontains",
            )

    assert ReplacingFilter._is_generation_capable() is False
    ReplacingFilter.get_filters()
    frozen = _snapshot(ReplacingFilter).candidates["genres__name__icontains"]
    assert frozen.eligible is True
    assert frozen.routable is False


def test_an_unmodified_generated_candidate_is_frozen_as_eligible_and_routable() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """

    class BookLoanFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

    assert BookLoanFilter._is_generation_capable() is True
    BookLoanFilter.get_filters()
    frozen = _snapshot(BookLoanFilter).candidates["loans__note__icontains"]
    assert frozen.eligible is True
    assert frozen.routable is True


def test_is_generation_capable_true_for_unmodified_subclass() -> None:
    """A plain package ``FilterSet`` subclass with no seam override IS capable."""

    class PlainFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    assert PlainFilter._is_generation_capable() is True
    assert PlainFilter.FILTER_DEFAULTS is FilterSet.FILTER_DEFAULTS


@pytest.mark.parametrize("seam", ["filter_for_field", "filter_for_lookup"])
def test_is_generation_capable_true_for_a_classmethod_rewrap_of_the_package_seam(
    seam: str,
) -> None:
    """A subclass re-wrapping the package's own seam function in a ``classmethod`` overrides nothing."""
    package_function = truth.stored_function(truth.class_dict(FilterSet)[seam])
    assert callable(package_function)

    class RewrappedFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    setattr(RewrappedFilter, seam, classmethod(package_function))

    assert truth.class_dict(RewrappedFilter)[seam] is not truth.class_dict(FilterSet)[seam]
    assert RewrappedFilter._is_generation_capable() is True


def test_is_generation_capable_false_for_plain_function_seam_override() -> None:
    """A ``filter_for_field`` shadowed by a plain function is an override -> False.

    ``truth.overrides`` compares the function each class stores for the seam: a
    plain function is its own stored function, which is not the one ``FilterSet``'s
    ``classmethod`` holds, so ``_is_generation_capable`` reports the seam
    overridden without binding or calling it. Empty ``fields`` keeps class
    creation from invoking the shadowed seam during ``get_filters``.
    """

    def _plain_seam(
        _field: ModelField,
        _field_name: str,
        _lookup_expr: str | None = None,
    ) -> NoReturn:
        raise AssertionError("never invoked")

    class PlainSeamFilter(FilterSet):
        # basedpyright: the seam is shadowed by a plain function on purpose; the test proves
        # ``_is_generation_capable`` reads it as an override without calling it
        filter_for_field = _plain_seam  # pyright: ignore[reportAssignmentType]

        class Meta:
            model = library_models.Book
            fields = []

    # A plain function, not a ``classmethod`` or bound method: it has no ``__func__``.
    assert not hasattr(PlainSeamFilter.filter_for_field, "__func__")
    assert PlainSeamFilter._is_generation_capable() is False


def test_a_custom_generated_child_keeps_its_class_provenance_and_no_candidate() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """
    _register_plain_types(library_models.Loan)

    class CustomChildGenerated(django_filters.CharFilter):
        """A consumer-owned generated filter class returned from the CHILD's seam."""

    class ChildLoanFilter(FilterSet):
        class Meta:
            model = library_models.Loan
            fields = {"note": ["icontains"]}

        @classmethod
        @override
        def filter_for_lookup(
            cls,
            field: ModelField,
            lookup_type: str,
        ) -> tuple[type[Filter] | None, dict[str, object]]:
            _default_class, params = super().filter_for_lookup(field, lookup_type)
            return CustomChildGenerated, params

    class ParentBookFilter(FilterSet):
        loans = RelatedFilter(ChildLoanFilter, field_name="loans")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    assert ParentBookFilter._is_generation_capable() is True
    assert ChildLoanFilter._is_generation_capable() is False
    leaf = ParentBookFilter.get_filters()["loans__note__icontains"]
    assert isinstance(leaf, CustomChildGenerated)
    assert _provenance(leaf).origin == "framework_default"
    assert _family_profile_for(leaf) is None  # unaudited subclass -> no family
    assert "loans__note__icontains" not in _snapshot(ParentBookFilter).candidates


def test_a_stock_generated_child_copy_is_owned_by_the_declared_branch() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_raw_filter_forms_api.py``.
    """
    _register_plain_types(library_models.Loan)

    class ChildLoanFilter(FilterSet):
        class Meta:
            model = library_models.Loan
            fields = {"note": ["icontains"]}

    class ParentBookFilter(FilterSet):
        loans = RelatedFilter(ChildLoanFilter, field_name="loans")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    assert ParentBookFilter._is_generation_capable() is True
    assert ChildLoanFilter._is_generation_capable() is True
    leaf = ParentBookFilter.get_filters()["loans__note__icontains"]
    assert _family_profile_for(leaf) is not None
    assert "loans__note__icontains" not in _snapshot(ParentBookFilter).candidates


def test_origin_isnull_boolean_override_on_many_side_is_override_generated() -> None:
    """A BooleanField override selected by ``isnull`` -> override_generated.

    ``Loan.note`` is a ``TextField``; the ``isnull`` lookup resolves the SELECTION
    field to ``BooleanField``, which the consumer override governs. The generated
    ``loans__note__isnull`` leaf (a many-side path) must therefore be
    ``override_generated`` and INELIGIBLE (no candidate row), even though the
    unresolved model field is a TextField.
    """

    class CustomBoolean(django_filters.BooleanFilter):
        """Consumer override BooleanField product."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["isnull"]}
            filter_overrides = {
                models.BooleanField: {"filter_class": CustomBoolean},
            }

    leaf = BookFilter.get_filters()["loans__note__isnull"]
    # django-filter actually selected the override product ...
    assert isinstance(leaf, CustomBoolean)
    # ... and the origin oracle agrees via the RESOLVED (BooleanField) selection.
    assert _provenance(leaf).origin == "override_generated"
    # An override product gets NO candidate row -> never routed.
    assert "loans__note__isnull" not in _snapshot(BookFilter).candidates


def test_origin_transform_output_field_selects_override_is_override_generated() -> None:
    """A transform whose OUTPUT field selects an override -> override_generated.

    ``ScalarSpecimen.occurred_on`` is a ``DateField``; the ``year`` transform
    resolves the output field to ``IntegerField``, which the consumer override
    governs. The generated ``occurred_on__year`` leaf must be classified from
    that resolved output field, not the unresolved ``DateField``.
    """

    class CustomNumber(django_filters.NumberFilter):
        """Consumer override IntegerField product."""

    class SpecimenFilter(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"occurred_on": ["year"]}
            filter_overrides = {
                models.IntegerField: {"filter_class": CustomNumber},
            }

    leaf = SpecimenFilter.get_filters()["occurred_on__year"]
    assert isinstance(leaf, CustomNumber)
    assert _provenance(leaf).origin == "override_generated"


def test_origin_precision_plain_many_side_leaf_stays_framework_default_and_eligible() -> None:
    """An unmatched leaf on an override-bearing class stays framework_default.

    On the SAME class that carries a ``BooleanField`` override, the plain
    ``loans__note__icontains`` leaf resolves to a ``TextField`` selection the
    override does NOT govern, so it stays ``framework_default``, eligible AND
    routable. This proves per-leaf precision -- a
    ``filter_overrides`` entry does NOT blanket-demote every leaf on the class.
    """

    class CustomBoolean(django_filters.BooleanFilter):
        """Consumer override that governs only the isnull-resolved BooleanField."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains", "isnull"]}
            filter_overrides = {
                models.BooleanField: {"filter_class": CustomBoolean},
            }

    BookFilter.get_filters()
    candidates = _snapshot(BookFilter).candidates
    # isnull leaf is the override product -> no row.
    assert "loans__note__isnull" not in candidates
    # icontains leaf is untouched by the BooleanField override.
    icontains = BookFilter.get_filters()["loans__note__icontains"]
    assert _provenance(icontains).origin == "framework_default"
    row = candidates["loans__note__icontains"]
    assert row.eligible is True
    assert row.routable is True


def test_generation_origin_oracle_fails_closed_on_unresolvable_lookup() -> None:
    """``_generation_origin_for_field`` returns override_generated when resolve_field raises.

    A lookup that cannot be resolved raises ``FieldLookupError`` upstream before
    any filter is generated (so such a leaf can never become an eligible
    candidate); the oracle fails closed to ``override_generated`` -- the
    ineligible origin -- so an unresolvable lookup is never treated as an
    eligible framework leaf. Exercised directly because the public generation
    path raises before reaching here.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Genre._meta.get_field("name")
    assert (
        BookFilter._generation_origin_for_field(field, "not_a_real_lookup") == "override_generated"
    )


def test_method_owned_leaf_is_ineligible_on_framework_many_side_path() -> None:
    """A framework-origin many-side leaf carrying a consumer ``method`` is INELIGIBLE.

    ``_candidate_metadata_for`` eligibility requires ``method is None`` -- a set method
    routes through a consumer ``FilterMethod`` whose semantics the correlated adapter
    must never smuggle into a subquery. A synthetic
    framework-stamped leaf with a genuine to-many ``field_name`` but a set method gets
    a candidate row that is ineligible SOLELY because of the method (mirrors the
    unknown-family eligibility probe).
    """

    def _passthrough_method(qs: object, _name: str, _value: object) -> object:
        return qs

    leaf = CharFilter(field_name="genres", method=_passthrough_method)
    _stamp_generation_provenance(
        leaf,
        FilterGenerationProvenance(origin="framework_default"),
    )
    assert _family_profile_for(leaf) is not None  # CharFilter IS a registered family
    row = _candidate_metadata_for(library_models.Book, leaf)
    assert isinstance(row, CandidateFilterMetadata)
    assert row.path_plan.first_many_index is not None  # genuinely many-side
    assert getattr(leaf, "method", None) is not None  # method IS set
    assert row.eligible is False  # ...ineligible SOLELY because a method is set


def _register_relay(model: type[django_models.Model]) -> type[DjangoType]:
    # Build the Relay-node type dynamically so each call gets a fresh type bound to
    # ``model`` (the autouse registry-isolation fixture clears it between tests).
    meta = type("Meta", (), {"model": model, "interfaces": (strawberry.relay.Node,)})
    relay_type = type(f"{model.__name__}RelayType", (DjangoType,), {"Meta": meta})
    apply_interfaces(relay_type, relay_type.__django_strawberry_definition__)
    return relay_type


def _extra_only_shadow_filter(
    model: type[django_models.Model],
    field_cls: type[ModelField],
    extra_fn: Callable[[ModelField], dict[str, object]],
    meta_fields: object,
    name: str = "BookFilter",
) -> type[FilterSet]:
    """Build a FilterSet whose ``FILTER_DEFAULTS`` shadows ONE field class.

    The shared shape of these tests: an ordinary
    ``{**FilterSet.FILTER_DEFAULTS, field_cls: {...}}`` shallow copy that keeps the
    SAME upstream ``filter_class`` but supplies a consumer ``extra`` provider. The
    copy is taken from ``FilterSet.FILTER_DEFAULTS`` -- the package-authored public
    table (``_PUBLIC_PACKAGE_FILTER_DEFAULTS``) -- NOT
    django-filter's mutable ``BaseFilterSet.FILTER_DEFAULTS``, so every untouched
    nested entry is carried by reference as the SAME (filter_class, provider) pair the
    ownership oracle NORMALIZES and compares by value against the private baseline
    (those classes stay ``framework_default``) while the one shadowed class supplies a
    NEW consumer ``extra`` provider, so its normalized value diverges (it is
    ``override_generated``). Built via ``type(...)`` so the metaclass runs exactly as
    for a ``class`` statement.
    """
    base_entry = FilterSet.FILTER_DEFAULTS[field_cls]
    filter_defaults = {
        **FilterSet.FILTER_DEFAULTS,
        field_cls: {"filter_class": base_entry["filter_class"], "extra": extra_fn},
    }
    meta = type("Meta", (), {"model": model, "fields": meta_fields})
    return type(name, (FilterSet,), {"FILTER_DEFAULTS": filter_defaults, "Meta": meta})


def test_m2m_extra_only_shadow_is_consumer_owned() -> None:
    """Same base M2M class + a consumer ``extra`` (restricted queryset) is honored."""
    _register_relay(library_models.Genre)
    BookFilter = _extra_only_shadow_filter(
        library_models.Book,
        dj_models.ManyToManyField,
        lambda _f: {"queryset": library_models.Genre.objects.none()},
        {"genres": ["exact"]},
    )

    leaf = BookFilter.get_filters()["genres"]
    # The consumer's class survives -- NOT discarded for a package GlobalID.
    assert isinstance(leaf, django_filters.ModelMultipleChoiceFilter)
    assert not isinstance(leaf, GlobalIDMultipleChoiceFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    assert "genres" not in _snapshot(BookFilter).candidates
    # OBSERVABLE: the consumer's restricted queryset survived generation (a GlobalID
    # replacement would have stripped it as a model-choice-only extra).
    assert _is_model_multiple_choice_field(leaf.field)
    assert leaf.field.queryset is not None
    assert leaf.field.queryset.query.is_empty()


def test_fk_extra_only_shadow_is_consumer_owned() -> None:
    """Same base FK class + a consumer ``extra`` (non-default to_field_name) is kept."""
    _register_relay(library_models.Shelf)
    BookFilter = _extra_only_shadow_filter(
        library_models.Book,
        dj_models.ForeignKey,
        lambda _f: {"queryset": library_models.Shelf.objects.all(), "to_field_name": "code"},
        {"shelf": ["exact"]},
    )

    leaf = BookFilter.get_filters()["shelf"]
    assert isinstance(leaf, django_filters.ModelChoiceFilter)
    assert not isinstance(leaf, GlobalIDFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    assert "shelf" not in _snapshot(BookFilter).candidates
    # OBSERVABLE: the consumer's non-default to_field target survived.
    assert _is_model_choice_field(leaf.field)
    assert leaf.field.to_field_name == "code"


def test_extra_only_shadow_survives_related_filter_expansion() -> None:
    """An ``extra``-only shadow on a child survives ``RelatedFilter`` expansion."""
    _register_relay(library_models.Genre)
    ChildBookFilter = _extra_only_shadow_filter(
        library_models.Book,
        dj_models.ManyToManyField,
        lambda _f: {"queryset": library_models.Genre.objects.none()},
        {"genres": ["exact"]},
        name="ChildBookFilter",
    )

    class LoanParentFilter(FilterSet):
        book = RelatedFilter(ChildBookFilter, field_name="book")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    leaf = LoanParentFilter.get_filters()["book__genres"]
    assert isinstance(leaf, django_filters.ModelMultipleChoiceFilter)
    assert not isinstance(leaf, GlobalIDMultipleChoiceFilter)
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "override_generated"
    assert "book__genres" not in _snapshot(LoanParentFilter).candidates
    assert _is_model_multiple_choice_field(leaf.field)
    assert leaf.field.queryset is not None
    assert leaf.field.queryset.query.is_empty()


def test_an_extra_only_relation_override_has_no_frozen_framework_candidate() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """
    _register_relay(library_models.Genre)
    BookFilter = _extra_only_shadow_filter(
        library_models.Book,
        dj_models.ManyToManyField,
        lambda _f: {"queryset": library_models.Genre._default_manager.all()},
        {"genres": ["exact"]},
    )
    BookFilter.get_filters()
    assert "genres" not in _snapshot(BookFilter).candidates


def test_shallow_copy_untouched_entry_stays_framework_default() -> None:
    """Positive control: an untouched entry in a shallow-copied defaults map stays framework-owned.

    It is NOT falsely treated as consumer-owned. A ``{**base, M2M: {...}}`` shadow that changes
    ONLY the M2M entry reuses the SAME nested object for the untouched forward-FK
    entry, so the FK relation stays ``framework_default`` and is still converted to
    the package GlobalID primitive, while the changed M2M entry is
    ``override_generated`` and keeps the consumer class.
    """
    _register_relay(library_models.Genre)
    _register_relay(library_models.Shelf)
    BookFilter = _extra_only_shadow_filter(
        library_models.Book,
        dj_models.ManyToManyField,
        lambda _f: {"queryset": library_models.Genre.objects.none()},
        {"genres": ["exact"], "shelf": ["exact"]},
    )

    filters = BookFilter.get_filters()
    genres_field = library_models.Book._meta.get_field("genres")
    shelf_field = library_models.Book._meta.get_field("shelf")
    # The CHANGED M2M entry -> consumer-owned; class preserved.
    assert BookFilter._generation_origin_for_field(genres_field, "exact") == "override_generated"
    assert not isinstance(filters["genres"], GlobalIDMultipleChoiceFilter)
    # The UNTOUCHED FK entry (same object in the shallow copy) -> framework default;
    # still converted to the package GlobalID primitive.
    assert BookFilter._generation_origin_for_field(shelf_field, "exact") == "framework_default"
    assert isinstance(filters["shelf"], GlobalIDFilter)


def test_public_filter_defaults_is_deepcopyable() -> None:
    """``copy.deepcopy(FilterSet.FILTER_DEFAULTS)`` works and the copy is independent.

    The public table is a plain ``dict`` of plain ``dict`` entries (the ``extra``
    providers are functions, which ``deepcopy`` treats as atomic), so
    ``copy.deepcopy`` succeeds -- keeping django-filter's inherited customization seam,
    which a nested ``MappingProxyType`` would break on both the Python 3.10 floor and
    current Python. This is a pure ``deepcopy`` of plain dicts, so it is
    version-independent (passes identically on the 3.10 floor). A nested entry replaced
    in the copy does NOT mutate the package table, and another ``FilterSet`` on the same
    model is unaffected.
    """
    clone = copy.deepcopy(FilterSet.FILTER_DEFAULTS)
    assert isinstance(clone, dict)
    before = FilterSet.FILTER_DEFAULTS[dj_models.CharField]["filter_class"]
    # Replace one nested entry in the COPY only.
    clone[dj_models.CharField] = {"filter_class": object}
    assert FilterSet.FILTER_DEFAULTS[dj_models.CharField]["filter_class"] is before

    # A separate FilterSet still generates the framework default for the same field.
    class PlainFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    assert PlainFilter.FILTER_DEFAULTS is _PUBLIC_PACKAGE_FILTER_DEFAULTS
    assert isinstance(PlainFilter.get_filters()["title"], CharFilter)


def test_private_baseline_is_immutable_and_independent() -> None:
    """The PRIVATE normalized baseline is immutable and a distinct object graph.

    ``_PACKAGE_POLICY_BASELINE`` is a ``MappingProxyType`` (mutating it raises
    ``TypeError``), holds normalized ``_NormalizedPolicyEntry`` records rather than the
    raw public entries, and is derived from -- but independent of -- the public table.
    Mutating the public table's nested entry therefore cannot change the normalized
    baseline record (they are distinct object graphs), which is exactly why ownership
    is anchored on the private baseline and compared by value.
    """
    # Immutable: the outer mapping rejects assignment.
    with pytest.raises(TypeError):
        # basedpyright: the baseline is a read-only Mapping; the test proves item assignment raises
        # TypeError
        _PACKAGE_POLICY_BASELINE[dj_models.ManyToManyField] = None  # pyright: ignore[reportIndexIssue]

    # Normalized records, not the raw public dict entries.
    record = _PACKAGE_POLICY_BASELINE[dj_models.CharField]
    assert isinstance(record, _NormalizedPolicyEntry)
    assert record.filter_class is CharFilter
    assert record.extra is None

    # Distinct object graph: mutating the public entry does not touch the baseline.
    public_entry = _PUBLIC_PACKAGE_FILTER_DEFAULTS[dj_models.CharField]
    original = public_entry["filter_class"]
    try:
        public_entry["filter_class"] = object
        char_record = _PACKAGE_POLICY_BASELINE[dj_models.CharField]
        assert char_record is not None
        assert char_record.filter_class is CharFilter
    finally:
        public_entry["filter_class"] = original


def test_normalize_policy_entry_none_returns_none() -> None:
    """``_normalize_policy_entry(None)`` returns ``None`` (the symmetric-absence case).

    The ownership oracle normalizes the merged selection with ``_normalize_policy_entry``
    and compares it against the baseline record from ``try_dbfield``, which returns
    ``None`` when a selection class has no matching entry along its MRO. Both sides must
    therefore represent absence as ``None`` so a present-vs-absent comparison is unequal;
    a present entry normalizes to a record.
    """
    assert _normalize_policy_entry(None) is None
    present = _normalize_policy_entry({"filter_class": CharFilter})
    assert present == _NormalizedPolicyEntry(CharFilter, None)


def test_public_filter_defaults_names_the_upstream_field_families() -> None:
    """The package-authored defaults name exactly the upstream field classes."""
    assert set(_PUBLIC_PACKAGE_FILTER_DEFAULTS) == set(UPSTREAM)


@pytest.mark.parametrize("field_type", list(UPSTREAM), ids=[field.__name__ for field in UPSTREAM])
def test_public_filter_default_retains_the_upstream_class_and_extra_presence(
    field_type: type,
) -> None:
    """Each adapted default keeps upstream's filter class and optional extra provider slot."""
    upstream = UPSTREAM[field_type]
    package = _PUBLIC_PACKAGE_FILTER_DEFAULTS[field_type]
    assert package.get("filter_class") is upstream.get("filter_class")
    assert ("extra" in package) is ("extra" in upstream)


@pytest.mark.parametrize(
    ("field_type", "sample"),
    [
        (dj_models.ForeignKey, library_models.Book._meta.get_field("shelf")),
        (dj_models.OneToOneField, library_models.MembershipCard._meta.get_field("patron")),
        (dj_models.ManyToManyField, library_models.Book._meta.get_field("genres")),
        (ManyToOneRel, library_models.Book._meta.get_field("loans")),
        (ManyToManyRel, library_models.Genre._meta.get_field("books")),
        (OneToOneRel, library_models.Patron._meta.get_field("card")),
    ],
    ids=[
        "foreign-key",
        "one-to-one",
        "many-to-many",
        "reverse-fk",
        "reverse-m2m",
        "reverse-o2o",
    ],
)
def test_relation_default_provider_retains_upstreams_owned_parameters(
    field_type: type,
    sample: object,
) -> None:
    """Every adapted relation provider returns upstream's keys, target model and optional parameters."""
    upstream_by_type: dict[type, dict[str, object]] = dict(UPSTREAM.items())
    upstream_provider = upstream_by_type[field_type]["extra"]
    package_provider = _PUBLIC_PACKAGE_FILTER_DEFAULTS[field_type]["extra"]
    assert callable(upstream_provider)
    assert callable(package_provider)
    upstream = require(upstream_provider(sample), is_object_dict)
    package = require(package_provider(sample), is_object_dict)
    assert set(package) == set(upstream)
    assert package.get("to_field_name") == upstream.get("to_field_name")
    assert package.get("null_label") == upstream.get("null_label")
    package_queryset = package["queryset"]
    upstream_queryset = upstream["queryset"]
    assert isinstance(package_queryset, QuerySet)
    assert isinstance(upstream_queryset, QuerySet)
    assert package_queryset.model is upstream_queryset.model


def test_a_consumer_ordering_override_keeps_override_provenance_and_no_candidate() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """

    class ConsumerOrderingCharFilter(CharFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            return qs.order_by("-title")

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}
            filter_overrides = {
                dj_models.TextField: {"filter_class": ConsumerOrderingCharFilter},
            }

    note_field = library_models.Loan._meta.get_field("note")
    assert BookFilter._generation_origin_for_field(note_field, "icontains") == "override_generated"
    BookFilter.get_filters()
    assert "loans__note__icontains" not in _snapshot(BookFilter).candidates


def _consumer_extra(_field: object) -> dict[str, object]:
    return {"exclude": True}


_ConsumerNamedCharFilter = type("CharFilter", (CharFilter,), {})


_ConsumerJSONFilter = type("ConsumerJSONFilter", (CharFilter,), {})


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        pytest.param(UPSTREAM[dj_models.CharField], True, id="pristine"),
        pytest.param(UPSTREAM[dj_models.ForeignKey], True, id="pristine-lambda-extra"),
        pytest.param({"filter_class": NumberFilter}, True, id="upstream-class-no-extra"),
        pytest.param({"filter_class": _ConsumerNamedCharFilter}, False, id="consumer-namesake"),
        pytest.param({}, False, id="no-filter-class"),
        pytest.param(
            {"filter_class": ModelChoiceFilter, "extra": _consumer_extra},
            False,
            id="consumer-extra",
        ),
        pytest.param({"filter_class": _ConsumerJSONFilter}, False, id="consumer-added-key"),
    ],
)
def test_upstream_authored_accepts_only_django_filters_own_entries(
    entry: dict[str, object],
    *,
    expected: bool,
) -> None:
    """``_upstream_authored`` accepts an entry only when django-filter itself wrote it.

    Its ``filter_class`` must be the ``django_filters.filters`` class of that name (a
    consumer subclass reusing the name ``CharFilter`` is rejected) and its ``extra``
    provider, when present, must be defined in ``django_filters.filterset``.
    """
    assert _upstream_authored(entry) is expected


def test_pre_import_consumer_mutation_is_adopted_but_override_generated() -> None:
    """Fresh-process: a pre-import mutation of django-filter's table is adopted, not trusted.

    In a FRESH process, a consumer swaps the ``TextField`` ``filter_class`` to its own
    class and installs an ``exclude=True`` ``extra`` provider for ``CharField`` BEFORE
    importing ``django_strawberry_framework.filters.sets``. The package table copies
    django-filter's, so it carries both mutated entries (as stock django-filter would use
    them), but neither is upstream-authored: their baseline records are the truthy
    tainted sentinel, so every selection of them is ``override_generated``, while an
    untouched class stays ``framework_default``. Process isolation makes global-state
    restoration in the parent unnecessary (the child is disposable); the child exits 0.
    """
    run_in_fresh_process(
        "from django.db import models\n"
        "from django_filters import filterset\n"
        "from django_filters import CharFilter\n"
        "Consumer = type('Consumer', (CharFilter,), {})\n"
        "consumer_extra = lambda f: {'exclude': True}\n"
        "g = filterset.BaseFilterSet.FILTER_DEFAULTS\n"
        "g[models.TextField]['filter_class'] = Consumer\n"
        "g[models.CharField]['extra'] = consumer_extra\n"
        "assert 'django_strawberry_framework.filters.sets' not in sys.modules\n"
        "import django_strawberry_framework.filters.sets as S\n"
        "pub = S.FilterSet.FILTER_DEFAULTS\n"
        "assert pub[models.TextField]['filter_class'] is Consumer, pub[models.TextField]\n"
        "assert pub[models.CharField]['extra'] is consumer_extra, pub[models.CharField]\n"
        "origin = S.FilterSet._origin_for_selection_class\n"
        "assert origin(models.TextField) == 'override_generated'\n"
        "assert origin(models.CharField) == 'override_generated'\n"
        "assert origin(models.IntegerField) == 'framework_default'\n"
        "tainted = S._PACKAGE_POLICY_BASELINE[models.TextField]\n"
        "assert tainted is S._TAINTED_POLICY and tainted\n",
    )


def test_exclude_extra_override_refused_and_pristine_never_excludes() -> None:
    """An ``exclude=True`` ``extra`` provider is refused; pristine candidates never exclude.

    An ``extra`` provider that yields ``{"exclude": True}`` installed via
    ``Meta.filter_overrides`` diverges the normalized entry, so the leaf is
    ``override_generated`` and gets NO candidate row (the gate refuses it) even though
    the generated instance itself carries ``exclude=True``. On the PRISTINE framework
    path every generated candidate leaf carries ``exclude=False`` -- the standing
    invariant that generated candidates never carry ``exclude=True``.
    """

    def _override_extra(_f: object) -> dict[str, object]:
        return {"exclude": True}

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}
            filter_overrides = {
                dj_models.TextField: {"filter_class": CharFilter, "extra": _override_extra},
            }

    note_field = library_models.Loan._meta.get_field("note")
    assert BookFilter._generation_origin_for_field(note_field, "icontains") != "framework_default"
    filters = BookFilter.get_filters()
    assert "loans__note__icontains" not in _snapshot(BookFilter).candidates
    # The consumer asked for exclude; the instance carries it, but it is NOT a candidate.
    assert filters["loans__note__icontains"].exclude is True

    class PristineFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

    pristine_filters = PristineFilter.get_filters()
    candidates = _snapshot(PristineFilter).candidates
    assert candidates  # pristine framework leaves DID produce candidate rows
    # No pristine framework leaf carries the consumer's ``exclude`` -- read off the
    # generated instances themselves, which is what django-filter executes.
    assert set(candidates) == {"loans__note__icontains"}
    assert pristine_filters["loans__note__icontains"].exclude is False


def test_pristine_defaults_produce_routable_candidate() -> None:
    """Positive control: a pristine framework to-many leaf is still ROUTABLE.

    Proves pristine package defaults still generate routable candidates, so the
    ownership fix is not merely closing routing everywhere.
    """

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["icontains"]}

    BookFilter.get_filters()
    row = _snapshot(BookFilter).candidates["loans__note__icontains"]
    assert row.eligible is True
    assert row.routable is True
    assert BookFilter.base_filters["loans__note__icontains"].exclude is False


@pytest.mark.django_db
def test_reverse_o2o_relation_generation_uses_upstream_reverse_o2o_provider() -> None:
    """Generating a reverse-O2O filter runs the table's ``OneToOneRel`` ``extra`` provider.

    ``Patron.card`` is the reverse of ``MembershipCard.patron`` (a ``OneToOneRel``), so
    django-filter selects the package table's ``OneToOneRel`` entry (copied from
    upstream's) and calls its ``extra`` provider to build the choice queryset from the
    reverse relation (the rarest relation kind).
    The generated leaf is then the raw-pk ``RelationPkFilter`` (no ``DjangoType`` exposes
    ``MembershipCard`` here), which drops the model-choice ``queryset`` kwarg.
    """

    class PatronFilter(FilterSet):
        class Meta:
            model = library_models.Patron
            fields = {"card": ["exact"]}

    field = library_models.Patron._meta.get_field("card")
    lookup = object_result(BaseFilterSet.filter_for_lookup.__func__, PatronFilter, field, "exact")
    assert is_exact_pair(lookup)
    _, params = lookup
    assert is_object_dict(params)
    queryset = params["queryset"]
    assert isinstance(queryset, QuerySet)
    assert queryset.model is library_models.MembershipCard
    leaf = PatronFilter.get_filters()["card"]
    assert isinstance(leaf, RelationPkFilter)
    assert "queryset" not in leaf.extra


def test_replacement_shadow_does_not_contaminate_other_filtersets() -> None:
    """Cross-filterset isolation: A's replaced M2M entry cannot alter unmodified B.

    Filterset A legitimately REPLACES the M2M entry (a new dict with a restricted
    queryset) in a shadow copied from ``FilterSet.FILTER_DEFAULTS``; filterset B is an
    unmodified ``FilterSet`` on the SAME model. A keeps its own
    ``ModelMultipleChoiceFilter`` while B still generates the framework GlobalID for the
    relation, and the shared package public entry is unchanged -- proving the
    customization is confined to A. A ``{**FilterSet.FILTER_DEFAULTS, M2M: {...}}``
    shadow puts a NEW object at the M2M key and carries every other entry by reference,
    so A never mutates the shared package table; ownership is decided by normalizing A's
    replaced entry and comparing it by value against the private baseline.
    """
    _register_relay(library_models.Genre)

    def _override_extra(_f: object) -> dict[str, object]:
        return {"queryset": library_models.Genre.objects.none()}

    class FiltersetA(FilterSet):
        FILTER_DEFAULTS = {
            **FilterSet.FILTER_DEFAULTS,
            dj_models.ManyToManyField: {
                "filter_class": django_filters.ModelMultipleChoiceFilter,
                "extra": _override_extra,
            },
        }

        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}

    class FiltersetB(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}

    a_leaf = FiltersetA.get_filters()["genres"]
    b_leaf = FiltersetB.get_filters()["genres"]
    # A keeps its own filter; B is untouched and still framework-converted.
    assert isinstance(a_leaf, django_filters.ModelMultipleChoiceFilter)
    assert not isinstance(a_leaf, GlobalIDMultipleChoiceFilter)
    assert isinstance(b_leaf, GlobalIDMultipleChoiceFilter)
    # The shared package public entry is unchanged -- no cross-filterset
    # contamination -- and the private normalized baseline still holds the framework
    # policy record.
    assert (
        _PUBLIC_PACKAGE_FILTER_DEFAULTS[dj_models.ManyToManyField]["filter_class"]
        is django_filters.ModelMultipleChoiceFilter
    )
    m2m_record = _PACKAGE_POLICY_BASELINE[dj_models.ManyToManyField]
    assert m2m_record is not None
    assert m2m_record.filter_class is django_filters.ModelMultipleChoiceFilter


def test_replacement_preserves_its_empty_queryset_and_required_form_metadata() -> None:
    """The replacement retains its exact class, unevaluated empty queryset and required form flag.

    Seeded allowed/refused choices are owned by
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """
    _register_relay(library_models.Genre)

    def _override_extra(_f: object) -> dict[str, object]:
        return {"queryset": library_models.Genre.objects.none(), "required": True}

    class BookFilter(FilterSet):
        FILTER_DEFAULTS = {
            **FilterSet.FILTER_DEFAULTS,
            dj_models.ManyToManyField: {
                "filter_class": django_filters.ModelMultipleChoiceFilter,
                "extra": _override_extra,
            },
        }

        class Meta:
            model = library_models.Book
            fields = {"genres": ["exact"]}

    genres_field = library_models.Book._meta.get_field("genres")
    assert BookFilter._generation_origin_for_field(genres_field, "exact") == "override_generated"
    leaf = BookFilter.get_filters()["genres"]
    assert isinstance(leaf, django_filters.ModelMultipleChoiceFilter)
    assert not isinstance(leaf, GlobalIDMultipleChoiceFilter)
    # The restricted queryset survived generation (a GlobalID replacement would have
    # stripped it as a model-choice-only extra), and the wire-shape ``required`` too.
    assert _is_model_multiple_choice_field(leaf.field)
    assert leaf.field.queryset is not None
    assert leaf.field.queryset.query.is_empty()
    assert leaf.field.required is True


class _ConsumerBooleanFilter(BooleanFilter):
    """A consumer's ``BooleanField`` override class."""


_CONSUMER_NULL_TEST_LABEL = "consumer null test"


def _consumer_null_test_extra(field: object) -> dict[str, object]:
    """A consumer ``BooleanField`` entry's ``extra`` provider: a label for every null test."""
    del field
    return {"label": _CONSUMER_NULL_TEST_LABEL}


@pytest.mark.parametrize(
    ("model", "field_name"),
    [
        (_link_models.LnkColumnChild, "parent"),
        (_link_models.LnkSlugObjectChild, "parent"),
        (_link_models.LnkOptionalPairChild, "parent"),
        (_link_models.LnkParent, "column_children"),
        (library_models.Shelf, "shelf_labels"),
        (library_models.Branch, "tags"),
    ],
    ids=[
        "one_column_fo_pk_target",
        "one_column_fo_non_pk_target",
        "nullable_two_column_fo",
        "reverse_one_column_fo",
        "reverse_two_column_fo",
        "generic_relation",
    ],
)
def test_relation_key_with_no_filter_defaults_entry_builds_the_boolean_null_test(
    model: type[django_models.Model],
    field_name: str,
) -> None:
    """A relation class the table does not name gets a ``ForeignKey``'s ``isnull`` leaf.

    django-filter returns ``(None, {})`` for a ``ForeignObject``, its reverse and a
    ``GenericRelation`` before its ``isnull`` branch, which failed the class with
    "unrecognized field type". The key's ``isnull`` is the framework ``BooleanFilter``
    beside the identity ``exact`` leaf.
    """
    probe = type(
        "NullTestProbe",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": model, "fields": {field_name: ["exact", "isnull"]}})},
    )

    leaf = probe.get_filters()[f"{field_name}__isnull"]

    assert type(leaf) is BooleanFilter
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "framework_default"
    assert isinstance(
        probe.get_filters()[field_name],
        (RelationPkFilter, RelationPkMultipleFilter),
    )


@pytest.mark.parametrize(
    ("model", "field_name"),
    [
        (library_models.Book, "shelf"),
        (library_models.ShelfLabel, "shelf"),
        (library_models.Shelf, "shelf_labels"),
        (library_models.Branch, "tags"),
    ],
    ids=[
        "foreign_key",
        "forward_foreign_object",
        "reverse_foreign_object",
        "generic_relation",
    ],
)
@pytest.mark.parametrize(
    (
        "overrides",
        "isnull_class",
        "isnull_origin",
        "isnull_label",
    ),
    [
        (
            {
                dj_models.BooleanField: {
                    "filter_class": _ConsumerBooleanFilter,
                    "extra": _consumer_null_test_extra,
                },
            },
            _ConsumerBooleanFilter,
            "override_generated",
            _CONSUMER_NULL_TEST_LABEL,
        ),
        (
            {dj_models.ForeignObject: {"filter_class": ModelChoiceFilter}},
            BooleanFilter,
            "framework_default",
            None,
        ),
    ],
    ids=["boolean_field_override", "foreign_object_override"],
)
def test_relation_key_isnull_follows_the_boolean_field_selection_like_a_foreign_key(
    *,
    model: type[django_models.Model],
    field_name: str,
    overrides: dict[type[object], dict[str, object]],
    isnull_class: type[Filter],
    isnull_origin: str,
    isnull_label: str | None,
) -> None:
    """Every relation key's ``isnull`` is owned as a ``ForeignKey``'s is.

    Upstream selects a relation null test off the ``BooleanField`` entry, so a
    consumer ``BooleanField`` override owns it on a ``ForeignObject``, its reverse
    and a ``GenericRelation`` exactly as on the ``ForeignKey`` control, its
    ``extra`` provider's parameters included, while an override of the relation
    class owns only ``exact`` and leaves ``isnull`` the framework ``BooleanFilter``.
    """
    probe = type(
        "OwnershipProbe",
        (FilterSet,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": model,
                    "fields": {field_name: ["isnull"]},
                    "filter_overrides": overrides,
                },
            ),
        },
    )

    leaf = probe.get_filters()[f"{field_name}__isnull"]

    assert type(leaf) is isnull_class
    assert (leaf.label == _CONSUMER_NULL_TEST_LABEL) is (isnull_label is not None), leaf.label
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == isnull_origin


#: The package table without its ``BooleanField`` entry, the class a null test is selected off.
_FILTER_DEFAULTS_WITHOUT_BOOLEAN = {
    field_class: entry
    for field_class, entry in FilterSet.FILTER_DEFAULTS.items()
    if field_class is not dj_models.BooleanField
}


@pytest.mark.parametrize(
    ("model", "field_name"),
    [(library_models.ShelfLabel, "shelf"), (library_models.Branch, "tags")],
    ids=["forward_foreign_object", "generic_relation"],
)
def test_relation_key_isnull_without_a_boolean_field_entry_raises_as_unrecognized(
    model: type[django_models.Model],
    field_name: str,
) -> None:
    """A table with no ``BooleanField`` entry leaves the key unrecognized under ``RAISE``.

    The null test has no class to be selected off, so the key keeps upstream's
    unrecognized-field contract: the class statement fails with django-filter's
    assertion naming the relation class.
    """
    with pytest.raises(AssertionError, match=rf"resolved field '{field_name}'.*unrecognized"):
        type(
            "NoBooleanProbe",
            (FilterSet,),
            {
                "FILTER_DEFAULTS": _FILTER_DEFAULTS_WITHOUT_BOOLEAN,
                "Meta": type("Meta", (), {"model": model, "fields": {field_name: ["isnull"]}}),
            },
        )


@pytest.mark.parametrize(
    ("model", "field_name"),
    [(library_models.ShelfLabel, "shelf"), (library_models.Branch, "tags")],
    ids=["forward_foreign_object", "generic_relation"],
)
def test_relation_key_isnull_without_a_boolean_field_entry_is_dropped_under_ignore(
    model: type[django_models.Model],
    field_name: str,
) -> None:
    """Under ``IGNORE`` the same key is dropped and the rest of the set still builds."""
    probe = type(
        "NoBooleanIgnoreProbe",
        (FilterSet,),
        {
            "FILTER_DEFAULTS": _FILTER_DEFAULTS_WITHOUT_BOOLEAN,
            "Meta": type(
                "Meta",
                (),
                {
                    "model": model,
                    "fields": {"id": ["exact"], field_name: ["isnull"]},
                    "unknown_field_behavior": UnknownFieldBehavior.IGNORE,
                },
            ),
        },
    )

    assert set(probe.get_filters()) == {"id"}


def _attachment_isnull_meta(behavior: UnknownFieldBehavior) -> type:
    """``Meta`` declaring ``isnull`` on ``Item.attachment``, a ``FileField`` the table omits."""
    return type(
        "Meta",
        (),
        {
            "model": Item,
            "fields": {"name": ["exact"], "attachment": ["isnull"]},
            "unknown_field_behavior": behavior,
        },
    )


def test_unrecognized_non_relation_column_isnull_still_raises_under_raise() -> None:
    """Only a relation key gains a null test: a ``FileField``'s ``isnull`` stays unrecognized.

    ``Item.attachment`` has no ``FILTER_DEFAULTS`` entry, so django-filter returns
    ``(None, {})`` for every lookup on it, ``isnull`` included, and the class
    statement fails with its assertion.
    """
    meta = _attachment_isnull_meta(UnknownFieldBehavior.RAISE)

    with pytest.raises(AssertionError, match=r"'attachment'.*unrecognized field type FileField"):
        type("AttachmentNullProbe", (FilterSet,), {"Meta": meta})


def test_unrecognized_non_relation_column_isnull_is_still_dropped_under_ignore() -> None:
    """Under ``IGNORE`` the ``FileField`` ``isnull`` leaf is dropped, as upstream drops it."""
    probe = type(
        "AttachmentNullProbe",
        (FilterSet,),
        {"Meta": _attachment_isnull_meta(UnknownFieldBehavior.IGNORE)},
    )

    assert set(probe.get_filters()) == {"name"}


def test_override_shadowed_by_more_derived_default_stays_framework() -> None:
    """A ``filter_overrides`` entry shadowed by a more-derived default does NOT govern.

    ``MembershipCard.patron`` is a ``OneToOneField``; base ``FILTER_DEFAULTS`` has a
    ``OneToOneField`` entry nearer on the MRO than the ``ForeignKey`` override, so
    upstream selects the base default and the leaf is framework-generated (converted to
    the Relay GlobalID). Walking ``filter_overrides`` ALONE mis-classified this
    ``override_generated`` -- declining the conversion (a silent GlobalID -> ModelChoice
    wire-shape regression).
    """
    _register_relay(library_models.Patron)

    def _override_extra(_f: object) -> dict[str, object]:
        return {}

    class MembershipCardFilter(FilterSet):
        class Meta:
            model = library_models.MembershipCard
            fields = {"patron": ["exact"]}
            filter_overrides = {
                dj_models.ForeignKey: {"filter_class": CharFilter, "extra": _override_extra},
            }

    field = library_models.MembershipCard._meta.get_field("patron")
    assert MembershipCardFilter._generation_origin_for_field(field, "exact") == "framework_default"
    assert isinstance(MembershipCardFilter.get_filters()["patron"], GlobalIDFilter)


def test_override_that_actually_governs_is_consumer_owned() -> None:
    """Positive control: an override that WINS the merged walk stays consumer-owned.

    A ``filter_overrides`` entry keyed on the EXACT field class (``OneToOneField``)
    overwrites the base default in the merged map, so upstream selects it. The oracle
    agrees (``override_generated``) and the consumer's class is NOT converted.
    """
    _register_relay(library_models.Patron)

    def _override_extra(_f: object) -> dict[str, object]:
        return {}

    class MembershipCardFilter(FilterSet):
        class Meta:
            model = library_models.MembershipCard
            fields = {"patron": ["exact"]}
            filter_overrides = {
                dj_models.OneToOneField: {"filter_class": CharFilter, "extra": _override_extra},
            }

    field = library_models.MembershipCard._meta.get_field("patron")
    assert (
        MembershipCardFilter._generation_origin_for_field(field, "exact") == "override_generated"
    )
    leaf = MembershipCardFilter.get_filters()["patron"]
    assert isinstance(leaf, CharFilter)
    assert not isinstance(leaf, GlobalIDFilter)


def test_benign_base_override_does_not_block_to_many_routing() -> None:
    """A shadowed override must NOT drop a genuine framework to-many leaf from routing.

    ``Loan.note`` is a ``TextField`` with its own base ``FILTER_DEFAULTS`` entry; a
    ``filter_overrides`` keyed on the less-derived ``models.Field`` is shadowed by it,
    so upstream selects the framework default across the reverse ``loans`` (to-many)
    path. Walking ``filter_overrides`` ALONE mis-stamped the leaf ``override_generated``
    -- so it never became a candidate and never routed through the ``EXISTS`` adapter
    (a false-closed routing loss).
    """

    def _override_extra(_f: object) -> dict[str, object]:
        return {}

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"loans__note": ["exact"]}
            filter_overrides = {
                dj_models.Field: {"filter_class": CharFilter, "extra": _override_extra},
            }

    BookFilter.get_filters()
    candidates = _snapshot(BookFilter).candidates
    assert "loans__note" in candidates
    assert candidates["loans__note"].eligible is True


class _UnknownFamilyFilter(Filter):
    """A direct ``Filter`` subclass in NO registered family fails closed.

    Stands in for a novel filter class a future unbounded ``django-filter`` (or any
    path that places an unaudited class behind a framework origin) could introduce.
    Its ``.filter`` records that the OUTER invocation ran and returns the queryset
    unchanged, so a defence-in-depth test can prove the applicator took the fallback
    path rather than the correlated ``EXISTS`` adapter.
    """

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        self._outer_called = True
        return qs


def _genuine_dynamic_csv_class(lookup: str) -> type[Filter]:
    """Return a genuine django-filter dynamic ``in`` / ``range`` CSV class (a real product).

    ``FilterSet.filter_for_lookup`` on a plain scalar field returns django-filter's
    ``class ConcreteRangeFilter(BaseRangeFilter, <scalar>): pass`` and, for ``in``, an
    empty-body ``(MembershipInFilter, <django-filter's ConcreteInFilter>)`` wrapper, so
    this exercises the structural validator on a REAL product rather than a hand-built
    stand-in. A
    ``CharField`` (``in``) / ``FloatField`` (``range``) is used because those fields carry
    NO static package CSV class, so ``filter_for_lookup`` builds a dynamic one -- an
    ``IntegerField`` would instead return the STATIC package ``IntegerInFilter`` /
    ``IntegerRangeFilter`` (an exact registry key), not a dynamic class.
    """
    field: ModelField = dj_models.CharField() if lookup == "in" else dj_models.FloatField()
    dynamic_class, _params = FilterSet.filter_for_lookup(field, lookup)
    assert dynamic_class is not None
    return dynamic_class


@pytest.mark.parametrize("lookup", ["in", "range"], ids=["in", "range"])
def test_genuine_dynamic_concrete_in_and_range_resolve_to_sequence_profile(lookup: str) -> None:
    """A genuine dynamic CSV class and its membership wrapper keep the sequence family."""
    concrete = _genuine_dynamic_csv_class(lookup)
    assert concrete not in _FILTER_FAMILY_REGISTRY
    if lookup == "in":
        assert concrete.__bases__[0] is MembershipInFilter
        inner = concrete.__bases__[1]
        assert inner.__bases__ == (BaseInFilter, CharFilter)
        assert issubclass(inner, Filter)
        assert _family_profile_for(object.__new__(inner)) is _SEQUENCE_LOOKUP_PROFILE
    else:
        assert concrete.__bases__[0] is BaseRangeFilter
    assert _family_profile_for(object.__new__(concrete)) is _SEQUENCE_LOOKUP_PROFILE


@pytest.mark.parametrize("shape", ["unaudited-inner", "audited-inner", "wrapper-body"])
def test_membership_wrapper_only_unwraps_an_audited_empty_body(shape: str) -> None:
    """An unaudited inner scalar or an added wrapper body prevents sequence-family routing."""

    class UnauditedScalar(Filter):
        pass

    class UnauditedIn(BaseInFilter, UnauditedScalar):
        pass

    class GenuineIn(BaseInFilter, CharFilter):
        pass

    class WrapperWithBody(MembershipInFilter, GenuineIn):
        extra_state = 1

    wrapped = {
        "unaudited-inner": membership_in_filter_class(UnauditedIn),
        "audited-inner": membership_in_filter_class(GenuineIn),
        "wrapper-body": WrapperWithBody,
    }[shape]
    expected = _SEQUENCE_LOOKUP_PROFILE if shape == "audited-inner" else None
    assert _family_profile_for(object.__new__(wrapped)) is expected


def test_in_lookup_inherited_as_a_non_base_in_filter_fails_at_build() -> None:
    """An inherited non-``BaseInFilter`` ``in`` class never generates a filter that skips ``[]``.

    A cooperative ``BaseFilterSet`` mixin behind ``FilterSet`` returns the bare scalar
    class for ``in``; the package refuses it at build instead of generating a filter
    that would skip an explicit ``[]``.
    """

    class _ScalarInDefaults(BaseFilterSet):
        @classmethod
        @override
        def filter_for_lookup(
            cls,
            field: ModelField,
            lookup_type: str,
        ) -> tuple[type[CharFilter], dict[str, object]]:
            return CharFilter, {}

    # basedpyright: ``FilterSet`` narrows ``filter_for_field`` / ``filter_for_lookup`` /
    # ``get_fields`` / ``FILTER_DEFAULTS`` against the stubs, which the plain mixin keeps; the
    # clash is the shape under test. The mixin defines no ``__init__``, so ``FilterSet``'s
    # cooperative one runs ``BaseFilterSet``'s
    class _ScalarInFilterSet(FilterSet, _ScalarInDefaults):  # pyright: ignore[reportIncompatibleMethodOverride, reportIncompatibleVariableOverride, reportUnsafeMultipleInheritance]
        pass

    with pytest.raises(
        ConfigurationError,
        match="inherited filter_for_lookup returned 'CharFilter' for the 'in' lookup on 'code'",
    ):
        _ScalarInFilterSet.filter_for_lookup(django_models.CharField(name="code"), "in")


@pytest.mark.parametrize(
    ("specific", "base"),
    [
        (GlobalIDMultipleChoiceFilter, MultipleChoiceFilter),
        (ModelMultipleChoiceFilter, MultipleChoiceFilter),
        (ModelChoiceFilter, ChoiceFilter),
    ],
)
def test_exact_match_keeps_registered_subclass_and_base_distinct(
    specific: type[Filter],
    base: type[Filter],
) -> None:
    """A registered subclass and its registered base resolve to their OWN profiles.

    No "MRO most-specific" lookup applies: each is an exact registry key, so
    ``_family_profile_for`` returns each one's own (distinct) profile by exact type.
    """
    assert issubclass(specific, base)
    specific_profile = _family_profile_for(object.__new__(specific))
    base_profile = _family_profile_for(object.__new__(base))
    assert specific_profile is _FILTER_FAMILY_REGISTRY[specific]
    assert base_profile is _FILTER_FAMILY_REGISTRY[base]
    assert specific_profile is not base_profile


def test_integer_in_resolves_by_exact_type_and_bare_base_in_is_unregistered() -> None:
    """``IntegerInFilter`` resolves by exact key; the bare ``BaseInFilter`` base is None.

    ``BaseInFilter`` / ``BaseRangeFilter`` are not registry keys (the structural validator
    does their MRO-walk job), so a bare ``BaseInFilter`` instance resolves to no
    profile -- only the STATIC package ``IntegerInFilter`` (an exact key) still routes.
    """
    assert IntegerInFilter in _FILTER_FAMILY_REGISTRY
    assert BaseInFilter not in _FILTER_FAMILY_REGISTRY
    assert BaseRangeFilter not in _FILTER_FAMILY_REGISTRY
    assert (
        _family_profile_for(object.__new__(IntegerInFilter))
        is _FILTER_FAMILY_REGISTRY[IntegerInFilter]
    )
    assert _family_profile_for(object.__new__(BaseInFilter)) is None
    assert _family_profile_for(object.__new__(BaseRangeFilter)) is None


@pytest.mark.parametrize(
    "base_cls",
    [CharFilter, ModelMultipleChoiceFilter, BaseInFilter],
    ids=["CharFilter", "ModelMultipleChoiceFilter", "BaseInFilter"],
)
def test_unregistered_subclass_of_registered_category_fails_closed(base_cls: type[Filter]) -> None:
    """An unaudited subclass of EACH broad registered category resolves to NO profile.

    The dangerous case: a subclass of a registered base (with an overridden
    ``.filter`` and added state) is NOT accepted through its ancestor. Exact match misses
    (it is not a registry key) and the structural validator refuses it (a single-base
    subclass is not the ``(BaseInFilter|BaseRangeFilter, <scalar>)`` 2-tuple shape, and a
    behavior-bearing body fails the empty-body check).
    """

    class _UnauditedSubclass(base_cls):
        extra_state = True

        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            return qs

    assert _family_profile_for(object.__new__(_UnauditedSubclass)) is None


@pytest.mark.parametrize(
    "shape",
    [
        "added-state",
        "added-method",
        "range-state",
        "dunder-state",
        "dunder-behavior",
        "init-subclass",
        "slots",
        "unaudited-scalar",
        "non-csv-first-base",
    ],
    ids=[
        "added-state",
        "added-method",
        "range-state",
        "dunder-state",
        "dunder-behavior",
        "init-subclass",
        "slots",
        "unaudited-scalar",
        "non-csv-first-base",
    ],
)
def test_dynamic_csv_subclass_with_added_behavior_fails_closed(shape: str) -> None:
    """A dynamic-CSV-shaped class with ONE added body member fails closed.

    The structural validator accepts ONLY genuine empty-body dynamic classes over an
    exact-audited scalar. Each variant below violates exactly one condition and must
    resolve to ``None``. Crucially this covers DUNDER-NAMED state and behavior, not just
    non-dunder members: an exact own-name-set compare against a ``pass``-body reference is
    what closes the gap where a
    "startswith/endswith ``__``" test let ``__evil_state__`` / an overridden
    ``__getattribute__`` / ``__init_subclass__`` / ``__slots__`` slip through.
    """

    class _EvilInAddedState(BaseInFilter, CharFilter):
        reverse = True

    class _EvilInAddedMethod(BaseInFilter, CharFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            return qs

    class _EvilRangeAddedState(BaseRangeFilter, NumberFilter):
        descending = True

    class _EvilInDunderState(BaseInFilter, CharFilter):
        __evil_state__ = True

    class _EvilInDunderBehavior(BaseInFilter, CharFilter):
        @override
        def __getattribute__(self, name: str) -> object:
            return object_result(object.__getattribute__, self, name)

    class _EvilInInitSubclass(BaseInFilter, CharFilter):
        def __init_subclass__(cls, **kwargs: object) -> None:
            super().__init_subclass__(**kwargs)

    class _EvilRangeSlots(BaseRangeFilter, NumberFilter):
        __slots__ = ()

    class _UnauditedScalar(Filter):
        pass

    class _EvilInUnauditedScalar(BaseInFilter, _UnauditedScalar):
        pass

    _TwoBaseFirstNotCsv = type("_TwoBaseFirstNotCsv", (CharFilter, BooleanFilter), {})

    variants = {
        "added-state": _EvilInAddedState,
        "added-method": _EvilInAddedMethod,
        "range-state": _EvilRangeAddedState,
        "dunder-state": _EvilInDunderState,
        "dunder-behavior": _EvilInDunderBehavior,
        "init-subclass": _EvilInInitSubclass,
        "slots": _EvilRangeSlots,
        "unaudited-scalar": _EvilInUnauditedScalar,
        "non-csv-first-base": _TwoBaseFirstNotCsv,
    }
    assert _family_profile_for(object.__new__(variants[shape])) is None


@pytest.mark.parametrize("lookup", ["in", "range"], ids=["in", "range"])
def test_empty_body_dynamic_csv_reference_matches_genuine_class_own_names(lookup: str) -> None:
    """The empty-body reference name-set equals a GENUINE dynamic CSV class's own ``vars``.

    ``_EMPTY_BODY_DYNAMIC_CSV_ATTRS`` is derived from a live ``pass``-body ``class`` statement,
    so it tracks the running interpreter's structural dunders (``__firstlineno__`` /
    ``__static_attributes__`` on 3.13+) instead of hardcoding a version-coupled allowlist.
    This pins that derivation to what django-filter actually produces: a genuine
    ``ConcreteInFilter`` / ``ConcreteRangeFilter`` has EXACTLY these own names -- so the
    exact-set compare in ``_dynamic_csv_profile_for`` neither false-closes a real dynamic
    class nor admits an extra member.
    """
    genuine = _genuine_dynamic_csv_class(lookup)
    assert frozenset(vars(genuine)) == _EMPTY_BODY_DYNAMIC_CSV_ATTRS


@pytest.mark.parametrize(
    "family_cls",
    list(_FILTER_FAMILY_REGISTRY),
    ids=[cls.__name__ for cls in _FILTER_FAMILY_REGISTRY],
)
def test_registry_is_a_closed_exact_allowlist(family_cls: type[Filter]) -> None:
    """An audited family's identity is accepted, while an arbitrary subclass is refused."""
    profile = _FILTER_FAMILY_REGISTRY[family_cls]
    assert profile in _ALL_FAMILY_PROFILES
    assert _family_profile_for(object.__new__(family_cls)) is profile
    generated_subclass = type(f"Sub_{family_cls.__name__}", (family_cls,), {})
    assert _family_profile_for(object.__new__(generated_subclass)) is None


def test_bare_filter_base_is_not_a_registered_family() -> None:
    """The universal ``Filter`` base resolves to NO profile (not a catch-all key)."""
    assert Filter not in _FILTER_FAMILY_REGISTRY
    assert _family_profile_for(object.__new__(Filter)) is None


def test_unknown_family_leaf_is_ineligible_on_framework_many_side_path() -> None:
    """An unknown family behind a framework origin on a many-side path fails CLOSED.

    Mirrors the ``_candidate_metadata_for`` provenance tests: a synthetic filter with
    a stamped framework-generated provenance and a genuine to-many ``field_name``
    ("genres" is an M2M on ``Book``) DOES get a candidate row and DOES cross a
    many-side hop, yet is INELIGIBLE because its class resolves to no registered
    family. Without the family gate this leaf would be routable before its runtime
    reads were audited.
    """
    leaf = _UnknownFamilyFilter(field_name="genres")
    _stamp_generation_provenance(
        leaf,
        FilterGenerationProvenance(origin="framework_default"),
    )
    assert _family_profile_for(leaf) is None
    row = _candidate_metadata_for(library_models.Book, leaf)
    assert isinstance(row, CandidateFilterMetadata)
    assert row.path_plan.first_many_index is not None  # genuinely many-side
    assert getattr(leaf, "method", None) is None  # not disqualified by a method
    assert row.eligible is False  # ...ineligible SOLELY because the family is unknown


@pytest.mark.parametrize(
    ("raw_version", "audited"),
    [
        ("25.2", True),  # the exact audited lower edge
        ("25.2.1", True),  # a patch release inside the floor family
        ("26.1", True),  # the compatibility-floor cell's version
        ("26.9.9", True),  # anything below the exclusive upper bound
        ("25.1", False),  # BELOW the audited floor
        ("25", False),  # a bare major below the floor (25 < 25.2)
        ("27.0", False),  # AT the exclusive upper bound
        ("27", False),  # a bare major at the upper bound
        ("28.4", False),  # a future unreviewed family
        ("26.1.dev0", True),  # dev suffix -> compares as its numeric prefix (26, 1)
        ("junk", False),  # unparseable -> FAIL CLOSED
        ("", False),  # empty -> FAIL CLOSED
    ],
)
def test_release_is_audited_range_edges(raw_version: str, *, audited: bool) -> None:
    """``_release_is_audited`` is an inclusive-lower / exclusive-upper numeric compare.

    Pure-string parsing, so the edges are testable without touching global state.
    Unparseable input must FAIL CLOSED (not audited): an optimizer that cannot prove
    the installed release was reviewed must decline the rewrite, never assume it.
    """
    lower, upper = _AUDITED_DJANGO_FILTER_RANGE
    assert (lower, upper) == ((25, 2), (27,)), "update this test with the audited range"
    assert _release_is_audited(raw_version) is audited


def test_installed_django_filter_is_inside_the_audited_range() -> None:
    """CI tripwire: the INSTALLED django-filter must be inside the audited range.

    Deliberately couples the lock to the audit. When the dependency moves to a family
    outside ``_AUDITED_DJANGO_FILTER_RANGE`` this fails, forcing the SQL-shape and
    semantic-parity suite to be run against the new release and the range widened
    on purpose -- rather than silently optimizing on unreviewed upstream behavior. (The
    package still INSTALLS and filters correctly on such a release; only the
    optimization is declined, so this failure is an audit prompt, not a breakage.)
    """
    assert _release_is_audited(django_filters.__version__) is True, (
        f"django-filter {django_filters.__version__} is outside the audited optimizer "
        f"range {_AUDITED_DJANGO_FILTER_RANGE}; re-audit, then widen the range."
    )


def test_audited_release_changes_only_the_frozen_candidate_routability() -> None:
    """Only Python query metadata and construction callbacks remain here.

    Observable SQL and rowsets belong to the native HTTP module
    ``examples/fakeshop/test_query/test_filter_querysets_api.py``.
    """

    def candidate(*, audited: bool) -> CandidateFilterMetadata:
        with mock.patch.object(sets_module, "_DJANGO_FILTER_OPTIMIZER_AUDITED", audited):

            class GateBookFilter(FilterSet):
                class Meta:
                    model = library_models.Book
                    fields = {"genres__name": ["icontains"]}

            GateBookFilter.get_filters()
            return _snapshot(GateBookFilter).candidates["genres__name__icontains"]

    audited = candidate(audited=True)
    unaudited = candidate(audited=False)
    assert audited.eligible is True
    assert unaudited.eligible is True
    assert audited.routable is True
    assert unaudited.routable is False


def _patron_child_with_method_string() -> type[FilterSet]:
    class Child(FilterSet):
        email = CharFilter(field_name="email", method="filter_email")

        class Meta:
            model = library_models.Patron
            fields = {"name": ["icontains"]}

        def filter_email(
            self,
            queryset: QuerySet[library_models.Patron],
            _name: str,
            value: object,
        ) -> QuerySet[library_models.Patron]:
            return queryset.filter(email=value)

    return Child


def _patron_child_with_method_callable() -> type[FilterSet]:
    def _filter_by_name(
        queryset: QuerySet[library_models.Patron],
        name: str,
        value: object,
    ) -> QuerySet[library_models.Patron]:
        return queryset.filter(**{name: value})

    class Child(FilterSet):
        email = CharFilter(field_name="email", method=_filter_by_name)

        class Meta:
            model = library_models.Patron
            fields = {"name": ["icontains"]}

    return Child


def _patron_child_with_init_override() -> type[FilterSet]:
    class Child(FilterSet):
        email = CharFilter(field_name="email")
        loans = RelatedFilter(LoanFilter, field_name="loans")

        class Meta:
            model = library_models.Patron
            fields = {"name": ["icontains"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

    return Child


def _patron_child_plain() -> type[FilterSet]:
    class Child(FilterSet):
        email = CharFilter(field_name="email")

        class Meta:
            model = library_models.Patron
            fields = {"name": ["icontains"]}

    return Child


class _OwnFilterCharFilter(CharFilter):
    """A ``CharFilter`` whose ``__init__`` stores a ``filter`` of its own on the instance.

    The bound method reads the object it was bound to, never a shallow copy of
    it with a rebound ``field_name``; it applies the filter's own lookup and
    ``exclude``.
    """

    def __init__(
        self,
        field_name: str,
        *,
        lookup_expr: str = "exact",
        exclude: bool = False,
    ) -> None:
        super().__init__(field_name=field_name, lookup_expr=lookup_expr, exclude=exclude)
        self.filter = self._own_filter

    def _own_filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        return CharFilter.filter(self, qs, value)


class _OwnFilterBooleanFilter(BooleanFilter):
    """A ``BooleanFilter`` whose ``__init__`` stores a ``filter`` of its own on the instance."""

    def __init__(self, field_name: str, *, lookup_expr: str = "exact") -> None:
        super().__init__(field_name=field_name, lookup_expr=lookup_expr)
        self.filter = self._own_filter

    def _own_filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        return BooleanFilter.filter(self, qs, value)


class _ClassFilterCharFilter(CharFilter):
    """A ``CharFilter`` overriding ``filter`` on its class: behavior of the filter object itself."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        return super().filter(qs, value)


def _patron_child_with_own_filter() -> type[FilterSet]:
    class Child(FilterSet):
        email = _OwnFilterCharFilter("email")

        class Meta:
            model = library_models.Patron
            fields = {"name": ["icontains"]}

    return Child


def _patron_child_with_class_filter() -> type[FilterSet]:
    class Child(FilterSet):
        email = _ClassFilterCharFilter(field_name="email")

        class Meta:
            model = library_models.Patron
            fields = {"name": ["icontains"]}

    return Child


class _OwnerBoundCase(NamedTuple):
    """One child filter set shape, the leaf expanded under ``patron``, and the verdict."""

    build_child: Callable[[], type[FilterSet]]
    leaf: str
    projected: bool


_OWNER_BOUND_CASES = {
    "method_string": _OwnerBoundCase(_patron_child_with_method_string, "email", projected=True),
    "method_callable": _OwnerBoundCase(
        _patron_child_with_method_callable,
        "email",
        projected=True,
    ),
    "init_override_generated": _OwnerBoundCase(
        _patron_child_with_init_override,
        "name__icontains",
        projected=True,
    ),
    "init_override_declared": _OwnerBoundCase(
        _patron_child_with_init_override,
        "email",
        projected=True,
    ),
    "init_override_related_branch": _OwnerBoundCase(
        _patron_child_with_init_override,
        "loans",
        projected=False,
    ),
    "own_filter": _OwnerBoundCase(_patron_child_with_own_filter, "email", projected=True),
    "class_filter": _OwnerBoundCase(_patron_child_with_class_filter, "email", projected=False),
    "declared_plain": _OwnerBoundCase(_patron_child_plain, "email", projected=False),
    "generated_plain": _OwnerBoundCase(_patron_child_plain, "name__icontains", projected=False),
}


@pytest.mark.parametrize("label", list(_OWNER_BOUND_CASES))
def test_expand_related_filter_projects_owner_bound_children_only(label: str) -> None:
    """A child leaf is projected iff its behavior belongs to the child filter set.

    A ``method=`` (string or callable), any other ``filter`` the child filter
    holds on its instance, and every leaf of a child overriding ``__init__`` are
    projected; a plain declared or generated leaf, and one overriding ``filter``
    on its class, is a rebound copy; a child ``RelatedFilter`` is a branch,
    never a flat leaf, so it is copied as is even under an ``__init__``
    override. Either way the copy keeps the child filter's class and carries
    the rebound ORM path.
    """
    case = _OWNER_BOUND_CASES[label]
    child = case.build_child()

    class Parent(FilterSet):
        patron = RelatedFilter(child, field_name="patron")

        class Meta:
            model = library_models.Loan
            fields = []

    child_filter = child.get_filters()[case.leaf]
    copy = Parent.get_filters()[f"patron__{case.leaf}"]
    assert isinstance(copy, ProjectedChildFilter) is case.projected
    assert isinstance(copy, type(child_filter))
    assert copy.field_name == f"patron__{child_filter.field_name}"
    if case.projected:
        projected = copy
        assert isinstance(projected, ProjectedChildFilter)
        assert projected._projection == ChildProjection(child, case.leaf, "patron")
        # The per-instance ``filter`` shadow (a ``method=``'s ``FilterMethod``, a
        # consumer's own callable) is the child's; the projection's own ``filter``
        # runs on the parent.
        assert "filter" not in vars(projected)


def test_customizes_instances_is_the_init_seam() -> None:
    """``_customizes_instances`` is the ``__init__`` half of ``_is_generation_capable``."""
    plain = _patron_child_plain()
    customized = _patron_child_with_init_override()
    assert plain._customizes_instances() is False
    assert plain._is_generation_capable() is True
    assert customized._customizes_instances() is True
    assert customized._is_generation_capable() is False


def test_projected_field_identity_belongs_to_its_child_but_templates_are_fresh() -> None:
    """A bound projected field is its child instance's, while every template read returns a fresh field.

    Validation answers are owned by
    ``examples/fakeshop/test_query/test_library_api.py::test_library_flat_expanded_declared_filter_keeps_its_own_validation_over_http``.
    """
    LoanFilter.get_filters()
    bound = LoanFilter(
        data={"patron__email_must_have_at_sign": "no-at"},
        queryset=library_models.Loan.objects.all(),
        request=HttpRequest(),
    )
    child = bound._projection_child(PatronFilter)
    assert (
        bound.filters["patron__email_must_have_at_sign"].field
        is child.filters["email_must_have_at_sign"].field
    )
    template = LoanFilter.base_filters["patron__email_must_have_at_sign"]
    assert isinstance(template, ProjectedChildFilter)
    assert template.field is not template.field
    assert "parent" not in vars(template)


def test_a_twice_projected_leaf_keeps_its_child_projection_metadata() -> None:
    """Only private metadata or callback observations remain here.

    Live sibling: ``examples/fakeshop/test_query/test_projected_owned_filters_api.py``.
    """
    patron_child = _patron_child_with_method_string()

    class LoanChild(FilterSet):
        patron = RelatedFilter(patron_child, field_name="patron")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    class BookParent(FilterSet):
        loans = RelatedFilter(LoanChild, field_name="loans")

        class Meta:
            model = library_models.Book
            fields = []

    _register_plain_types(library_models.Loan, library_models.Patron)
    leaf = BookParent.get_filters()["loans__patron__email"]
    assert isinstance(leaf, ProjectedChildFilter)
    assert leaf._projection == ChildProjection(LoanChild, "patron__email", "loans")
    assert leaf.field_name == "loans__patron__email"


def test_a_projection_child_binds_its_own_deferred_copy_to_its_own_instance() -> None:
    """Only private metadata or callback observations remain here.

    Live sibling: ``examples/fakeshop/test_query/test_projected_owned_filters_api.py``.
    """
    patron_child = _patron_child_with_method_string()

    class LoanChild(FilterSet):
        patron = RelatedFilter(patron_child, field_name="patron")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    class BookParent(FilterSet):
        loans = RelatedFilter(LoanChild, field_name="loans")

        class Meta:
            model = library_models.Book
            fields = []

    _register_plain_types(library_models.Loan, library_models.Patron)
    BookParent.get_filters()
    assert "patron__email" in _snapshot(LoanChild).deferred_copies

    instance = BookParent(
        data={"loans__patron__email": "p1@x"},
        queryset=library_models.Book.objects.all(),
        request=HttpRequest(),
    )

    _ = instance.qs
    children = instance._projection_children
    assert children is not None
    child = children[LoanChild]
    copied = child._copied_filters
    assert list(copied) == ["note", "patron", "patron__email"]
    assert copied["patron__email"] is not LoanChild.base_filters["patron__email"]
    assert vars(copied["patron__email"])["parent"] is child


def test_projected_leaf_gets_no_candidate_row() -> None:
    """A projected generated many-side leaf gets no candidate row.

    Its class is the projected subclass, which no audited family names, and it is
    a ``RelatedFilter`` expansion, so the snapshot holds no row for it.
    """

    class LoanChild(FilterSet):
        class Meta:
            model = library_models.Loan
            fields = {"note": ["icontains"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

    class BookParent(FilterSet):
        loans = RelatedFilter(LoanChild, field_name="loans")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    leaf = BookParent.get_filters()["loans__note__icontains"]
    assert isinstance(leaf, ProjectedChildFilter)
    assert _family_profile_for(leaf) is None
    assert _provenance(leaf).origin == "framework_default"
    snapshot = BookParent._expansion_snapshot()
    assert snapshot is not None
    assert "loans__note__icontains" not in snapshot.candidates


def test_projected_leaf_child_runs_on_the_parents_database_with_its_request() -> None:
    """One child instance per parent instance, built on first use, on the parent's alias.

    Every projected leaf of one parent instance expanded from ``PatronFilter``
    runs in the same child instance, which seeds the child model's rows on the
    parent queryset's alias and carries the parent's request; another parent
    instance builds its own.
    """
    LoanFilter.get_filters()
    request = HttpRequest()
    parent = LoanFilter(
        data={},
        queryset=library_models.Loan.objects.using("shard_b"),
        request=request,
    )
    assert parent._projection_children is None
    leaf = parent.filters["patron__email_must_have_at_sign"]
    sibling = parent.filters["patron__name__icontains"]
    assert isinstance(leaf, ProjectedChildFilter)
    assert isinstance(sibling, ProjectedChildFilter)
    child = leaf._child()
    assert isinstance(child, PatronFilter)
    assert child.queryset is not None
    assert child.queryset.db == "shard_b"
    assert child.queryset.model is library_models.Patron
    assert child.request is request
    assert sibling._child() is child
    assert parent._projection_children == {PatronFilter: child}
    other = LoanFilter(data={}, queryset=library_models.Loan.objects.all(), request=request)
    other_leaf = other.filters["patron__email_must_have_at_sign"]
    assert isinstance(other_leaf, ProjectedChildFilter)
    assert other_leaf._child() is not child


@pytest.mark.parametrize("how", ["pickle", "deepcopy"])
def test_projected_leaf_copies_keep_their_projected_class_and_projection(how: str) -> None:
    """A projected template survives ``pickle`` and ``deepcopy`` as the same class.

    The projected class is built at runtime, so pickle cannot import it by name;
    the round trip rebuilds it from the child filter's own class.
    """
    template = LoanFilter.get_filters()["patron__email_must_have_at_sign"]
    assert isinstance(template, ProjectedChildFilter)
    restored = pickle_roundtrip(template) if how == "pickle" else copy.deepcopy(template)
    assert type(restored) is type(template)
    assert restored._projection == template._projection
    assert restored.method == "filter_email_must_have_at_sign"
    assert "filter" not in vars(restored)


def test_flat_expanded_declared_child_fires_the_gates_its_nested_twin_fires() -> None:
    """``shelf__home_branch`` reaches the child's ``check_home_branch_permission`` flat as nested."""
    fired: list[str] = []

    class ChildShelfFilter(FilterSet):
        home_branch = ModelChoiceFilter(
            field_name="branch",
            queryset=library_models.Branch.objects.all(),
        )

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def check_home_branch_permission(self, _request: object) -> None:
            fired.append("child.home_branch")

        def check_branch_permission(self, _request: object) -> None:
            fired.append("child.branch")

    class ParentBookFilter(FilterSet):
        shelf = RelatedFilter(ChildShelfFilter, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = []

        def check_shelf_permission(self, _request: object) -> None:
            fired.append("parent.shelf")

        def check_shelf_home_branch_permission(self, _request: object) -> None:
            fired.append("parent.shelf_home_branch")

        def check_shelf_branch_permission(self, _request: object) -> None:
            fired.append("parent.shelf_branch")

    ParentBookFilter.get_filters()
    ParentBookFilter._run_permission_checks({"shelf__home_branch": 1}, HttpRequest())
    assert sorted(fired) == ["child.home_branch", "parent.shelf", "parent.shelf_home_branch"]
    fired.clear()
    ParentBookFilter._run_permission_checks({"shelf": {"home_branch": 1}}, HttpRequest())
    assert sorted(fired) == ["child.home_branch", "parent.shelf"]


def _shelf_and_branch_filters(
    shelf_type_get_queryset: Callable[..., object] | None = None,
) -> type[FilterSet]:
    """``BranchFilter.shelves -> ShelfFilter`` plus a ``ShelfType`` whose ``get_queryset`` is given.

    ``ShelfFilter.code_is`` is a ``method=`` filter, so ``shelves__code_is`` is a
    ``ProjectedChildFilter``; ``shelves__code`` / ``shelves__topic`` and the range
    ``shelves__code_span`` are plain expansions. ``shelf_type_get_queryset`` of
    ``None`` registers no ``ShelfType``.
    """
    if shelf_type_get_queryset is not None:
        type(
            "ShelfType",
            (DjangoType,),
            {
                "Meta": type("Meta", (), {"model": library_models.Shelf}),
                "get_queryset": classmethod(shelf_type_get_queryset),
            },
        )

    class ShelfFilter(FilterSet):
        code_is = CharFilter(field_name="code", method="filter_code_is")
        code_span = RangeFilter(field_name="code", lookup_expr="range")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"], "topic": ["exact"]}

        def filter_code_is(
            self,
            queryset: QuerySet[library_models.Shelf],
            _name: str,
            value: object,
        ) -> QuerySet[library_models.Shelf]:
            return queryset.filter(code=value)

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    BranchFilter.get_filters()
    return BranchFilter


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    ("filter_input", "derivations", "_names"),
    [
        ({"name": "beta"}, {"sync": 0, "async": 0}, ["beta"]),
        ({"shelves__code": ""}, {"sync": 1, "async": 1}, ["alpha", "beta"]),
        ({"shelves__code_is": ""}, {"sync": 1, "async": 1}, ["alpha", "beta"]),
        ({"shelves__code": "match"}, {"sync": 1, "async": 1}, ["alpha"]),
        (
            {"shelves__code": "match", "shelves__topic": "open", "shelves__code_is": "match"},
            {"sync": 1, "async": 1},
            ["alpha"],
        ),
        (
            {"or_": [{"shelves__code": "match"}, {"shelves__topic": "open"}]},
            {"sync": 1, "async": 1},
            ["alpha"],
        ),
        (
            {"shelves__code_span": {"start": None, "end": None}},
            {"sync": 0, "async": 0},
            ["alpha", "beta"],
        ),
        ({"shelves__code_span": dict[str, object]()}, {"sync": 0, "async": 0}, ["alpha", "beta"]),
        (
            {"or_": [{"shelves__code_span": {"start": None, "end": None}}]},
            {"sync": 0, "async": 0},
            ["alpha", "beta"],
        ),
        (
            {"or_": [{"shelves__code_span": dict[str, object]()}]},
            {"sync": 0, "async": 0},
            ["alpha", "beta"],
        ),
        ({"shelves__code_span": {"start": "a", "end": None}}, {"sync": 1, "async": 1}, ["alpha"]),
    ],
    ids=[
        "no-relation-leaf",
        "empty-expanded",
        "empty-projected",
        "one-leaf",
        "three-leaves-one-hop",
        "two-or-arms-one-hop",
        "range-both-bounds-null",
        "range-no-bounds",
        "range-both-bounds-null-in-or-arm",
        "range-no-bounds-in-or-arm",
        "range-one-bound",
    ],
)
def test_flat_hop_hook_counts_and_info_identity_match_the_named_leaves(
    filter_input: dict[str, object],
    derivations: dict[str, int],
    _names: list[str],
    mode: str,
) -> None:
    """Callback counts and request identity are private; native relation form holders own the rows."""
    calls: list[object] = []

    def _visible_shelves(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        calls.append(info)
        return queryset.exclude(topic="secret")

    branch_filter = _shelf_and_branch_filters(_visible_shelves)
    info = _make_info()
    base = library_models.Branch.objects.order_by("name")

    if mode == "sync":
        _ = branch_filter.apply_sync(filter_input, base, info)
    else:
        _ = asyncio.run(branch_filter.apply_async(filter_input, base, info))
    assert len(calls) == derivations[mode]
    assert all(seen is info for seen in calls)


def _seed_open_and_secret_match_shelves() -> None:
    """``alpha`` owns an open ``match`` shelf, ``beta`` a secret one."""
    alpha = library_models.Branch.objects.create(name="alpha")
    library_models.Shelf.objects.create(branch=alpha, code="match", topic="open")
    beta = library_models.Branch.objects.create(name="beta")
    library_models.Shelf.objects.create(branch=beta, code="match", topic="secret")


def _counting_branch_filters(calls: list[str]) -> type[FilterSet]:
    """``BranchCounter.shelves -> ShelfCounter``, whose filter bodies record each run in ``calls``.

    ``code_is``, ``code_among`` (``in``) and ``code_span`` (a range) are ``method=``
    filters, so their flat spellings are owner-bound ``ProjectedChildFilter``
    copies; ``topic_seen`` is a ``CharFilter`` subclass whose class-level
    ``filter`` records its run and value, so ``shelves__topic_seen`` is a plain
    walked copy; a nested ``shelves`` branch runs it with the empty value too, as
    django-filter runs every filter of a set it builds.
    ``ShelfCounter.books`` holds ``BookCounter.title_is`` flat as
    ``books__title_is`` (a projected copy) for a nested ``shelves`` branch to carry.
    """
    _register_plain_types(library_models.Shelf, library_models.Book)

    class TopicSeen(CharFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            calls.append(f"topic_seen={value}")
            return super().filter(qs, value)

    class BookCounter(FilterSet):
        title_is = CharFilter(field_name="title", method="filter_title_is")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

        def filter_title_is(
            self,
            queryset: QuerySet[library_models.Book],
            _name: str,
            value: object,
        ) -> QuerySet[library_models.Book]:
            calls.append("title_is")
            return queryset.filter(title=value)

    class ShelfCounter(FilterSet):
        books = RelatedFilter(BookCounter, field_name="books")
        code_is = CharFilter(field_name="code", method="filter_code_is")
        code_among = ListFilter(field_name="code", lookup_expr="in", method="filter_code_among")
        code_span = RangeFilter(field_name="code", lookup_expr="range", method="filter_code_span")
        topic_seen = TopicSeen(field_name="topic")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def filter_code_is(
            self,
            queryset: QuerySet[library_models.Shelf],
            _name: str,
            value: object,
        ) -> QuerySet[library_models.Shelf]:
            calls.append("code_is")
            return queryset.filter(code=value)

        def filter_code_among(
            self,
            queryset: QuerySet[library_models.Shelf],
            _name: str,
            value: object,
        ) -> QuerySet[library_models.Shelf]:
            calls.append("code_among")
            return queryset.filter(code__in=require(value, is_list_or_tuple))

        def filter_code_span(
            self,
            queryset: QuerySet[library_models.Shelf],
            _name: str,
            value: object,
        ) -> QuerySet[library_models.Shelf]:
            calls.append("code_span")
            return queryset.filter(code__range=tuple(require(value, is_list_or_tuple)))

    class BranchCounter(FilterSet):
        shelves = RelatedFilter(ShelfCounter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    BranchCounter.get_filters()
    return BranchCounter


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    ("filter_input", "runs", "_names"),
    [
        ({"shelves__code_is": "match"}, ["code_is"], ["alpha"]),
        ({"shelves__topic_seen": "open"}, ["topic_seen=open"], ["alpha"]),
        (
            {"shelves__code_is": "match", "shelves__topic_seen": "open"},
            ["code_is", "topic_seen=open"],
            ["alpha"],
        ),
        (
            {"shelves__code_is": "match", "shelves": {"code_is": "match"}},
            ["code_is", "code_is", "topic_seen="],
            ["alpha"],
        ),
        ({"not_": {"shelves__code_is": "match"}}, ["code_is"], ["beta"]),
        ({"and_": [{"or_": [{"shelves__topic_seen": "open"}]}]}, ["topic_seen=open"], ["alpha"]),
        ({"shelves__code_among": ["match"]}, ["code_among"], ["alpha"]),
        ({"shelves__code_span": {"start": "m", "end": "n"}}, ["code_span"], ["alpha"]),
        ({"shelves": {"books__title_is": "x"}}, ["title_is", "topic_seen="], ["alpha"]),
        ({"shelves__code_is": ""}, [], ["alpha", "beta"]),
        ({"shelves__topic_seen": ""}, ["topic_seen="], ["alpha", "beta"]),
        ({"name": "alpha"}, [], ["alpha"]),
    ],
    ids=[
        "projected",
        "plain-copy",
        "two-leaves-one-relation",
        "flat-beside-nested",
        "in-not-arm",
        "in-and-or-arms",
        "in-value",
        "range-value",
        "nested-branch-holding-a-projected-copy",
        "empty-projected",
        "empty-plain-copy",
        "omitted",
    ],
)
def test_flat_leaf_callback_counts_match_the_supplied_values(
    filter_input: dict[str, object],
    runs: list[str],
    _names: list[str],
    mode: str,
) -> None:
    """Callback counts and request identity are private; native relation form holders own the rows."""
    calls: list[str] = []
    branch_filter = _counting_branch_filters(calls)
    info = _make_info()
    base = library_models.Branch.objects.order_by("name")

    if mode == "sync":
        _ = branch_filter.apply_sync(filter_input, base, info)
    else:
        _ = asyncio.run(branch_filter.apply_async(filter_input, base, info))
    assert sorted(calls) == runs


def _counting_patron_chain(calls: list[str]) -> type[FilterSet]:
    """``BranchTop`` reaches ``PatronCounter`` through ``shelves``, ``books``, ``loans`` and ``patron``.

    ``PatronCounter.fines_span`` is a ``method=`` range, so
    ``shelves__books__loans__patron__fines_span`` is a projected copy four hops deep
    (every set between expands the child's projected copy as one of its own).
    """
    _register_plain_types(
        library_models.Shelf,
        library_models.Book,
        library_models.Loan,
        library_models.Patron,
    )

    class PatronCounter(FilterSet):
        fines_span = RangeFilter(
            field_name="lifetime_fines_cents",
            lookup_expr="range",
            method="filter_fines_span",
        )

        class Meta:
            model = library_models.Patron
            fields = {"name": ["exact"]}

        def filter_fines_span(
            self,
            queryset: QuerySet[library_models.Patron],
            _name: str,
            value: object,
        ) -> QuerySet[library_models.Patron]:
            calls.append("fines_span")
            bounds = tuple(require(value, is_list_or_tuple))
            return queryset.filter(lifetime_fines_cents__range=bounds)

    class LoanMid(FilterSet):
        patron = RelatedFilter(PatronCounter, field_name="patron")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    class BookMid(FilterSet):
        loans = RelatedFilter(LoanMid, field_name="loans")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    class ShelfMid(FilterSet):
        books = RelatedFilter(BookMid, field_name="books")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchTop(FilterSet):
        shelves = RelatedFilter(ShelfMid, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    BranchTop.get_filters()
    return BranchTop


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    ("filter_input", "_names"),
    [
        ({"shelves__books__loans__patron__fines_span": {"start": 5, "end": 9}}, ["alpha"]),
        (
            {"shelves": {"books": {"loans": {"patron": {"fines_span": {"start": 5, "end": 9}}}}}},
            ["alpha"],
        ),
    ],
    ids=["flat", "nested"],
)
def test_four_hop_projected_range_callback_runs_once(
    filter_input: dict[str, object],
    _names: list[str],
    mode: str,
) -> None:
    """Callback counts and request identity are private; native relation form holders own the rows."""
    calls: list[str] = []
    branch_filter = _counting_patron_chain(calls)
    info = _make_info()
    base = library_models.Branch.objects.order_by("name")

    if mode == "sync":
        _ = branch_filter.apply_sync(filter_input, base, info)
    else:
        _ = asyncio.run(branch_filter.apply_async(filter_input, base, info))
    assert calls == ["fines_span"]


@pytest.mark.parametrize("projected", [True, False], ids=["projected", "plain-copy"])
def test_an_unresolved_childs_customization_selects_the_projected_leaf_class(
    *,
    projected: bool,
) -> None:
    """Projection class identity is private; native unresolved-hop holders own both wire verdicts."""
    _register_plain_types(library_models.Shelf)

    class ShelfChild(FilterSet):
        branch = RelatedFilter(
            None,
            field_name="branch",
            queryset=library_models.Branch.objects.all(),
        )

        class Meta:
            model = library_models.Shelf
            fields = {"branch__name": ["exact"]}

    child: type[FilterSet] = ShelfChild
    if projected:

        class OwnedShelfChild(ShelfChild):
            def __init__(
                self,
                data: QueryDict | dict[str, object] | None = None,
                queryset: QuerySet[django_models.Model] | None = None,
                *,
                request: HttpRequest | None = None,
                prefix: str | None = None,
            ) -> None:
                super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

        child = OwnedShelfChild

    class BranchParent(FilterSet):
        shelves = RelatedFilter(child, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    leaf = BranchParent.get_filters()["shelves__branch__name"]
    assert isinstance(leaf, ProjectedChildFilter) is projected


class _SkipEmptyCodeFilter(CharFilter):
    """A consumer ``CharFilter`` whose class ``filter`` skips an empty value."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        if value is None or value == "":
            return qs
        return super().filter(qs, value)


@pytest.mark.parametrize(
    ("declared", "derivations"),
    [
        (CharFilter(field_name="shelves__code", empty_value="match"), 1),
        (
            BooleanFilter(
                field_name="shelves__topic",
                lookup_expr="isnull",
                widget=forms.CheckboxInput,
            ),
            1,
        ),
        (CharFilter(field_name="shelves__code"), 0),
        (_SkipEmptyCodeFilter(field_name="shelves__code"), 0),
        (
            ModelMultipleChoiceFilter(
                field_name="shelves__books",
                queryset=library_models.Book.objects.all(),
            ),
            0,
        ),
    ],
    ids=[
        "empty-value-field",
        "checkbox",
        "empty",
        "consumer-filter-skipping-empty",
        "model-multiple-choice",
    ],
)
def test_omitted_walked_leaf_hook_counts_follow_its_filter_default(
    declared: Filter,
    derivations: int,
) -> None:
    """Only private metadata or callback observations remain here.

    Live sibling: ``examples/fakeshop/test_query/test_relation_filter_defaults_api.py``.
    """
    calls: list[object] = []

    def _visible_shelves(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        calls.append(info)
        return queryset.exclude(topic="secret")

    _register_plain_types(library_models.Book)
    branch_filter = _shelf_and_branch_filters(_visible_shelves)
    parent = type(
        "BranchOwnLeaf",
        (branch_filter,),
        {
            "own": declared,
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Branch, "fields": {"name": ["exact"]}},
            ),
        },
    )
    parent.get_filters()
    _ = parent.apply_sync({}, library_models.Branch.objects.order_by("name"), _make_info())
    assert len(calls) == derivations


@pytest.mark.parametrize(
    ("declared", "data"),
    [
        (CharFilter(field_name="shelves__code"), {"own": ""}),
        (django_filters.RangeFilter(field_name="shelves__code"), {"own_min": "", "own_max": ""}),
    ],
    ids=["text", "range-widget-keys"],
)
def test_supplied_empty_walked_leaf_hook_count_is_one(
    declared: Filter,
    data: dict[str, object],
) -> None:
    """Only private metadata or callback observations remain here.

    Live sibling: ``examples/fakeshop/test_query/test_relation_filter_form_paths_api.py``.
    """
    calls: list[object] = []

    def _visible_shelves(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        calls.append(info)
        return queryset.exclude(topic="secret")

    branch_filter = _shelf_and_branch_filters(_visible_shelves)
    parent = type(
        "BranchOwnLeaf",
        (branch_filter,),
        {
            "own": declared,
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Branch, "fields": {"name": ["exact"]}},
            ),
        },
    )
    parent.get_filters()
    built = parent(
        data=data,
        queryset=library_models.Branch.objects.order_by("name"),
        request=HttpRequest(),
    )
    _ = built.qs
    assert len(calls) == 1


class _DefaultCodeFilter(CharFilter):
    """A consumer ``CharFilter`` whose class ``filter`` reads an absent value as ``"match"``."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        return super().filter(qs, value or "match")


@pytest.mark.parametrize(
    ("leaf", "mode"),
    [
        ("walked", "sync"),
        ("walked", "async"),
        ("walked", "direct"),
        ("projected", "direct"),
    ],
)
def test_an_absent_class_default_derives_its_target_hook_once(leaf: str, mode: str) -> None:
    """Callback counts and request identity are private; native relation form holders own the rows."""
    calls: list[object] = []

    def _visible_shelves(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        calls.append(info)
        return queryset.exclude(topic="secret")

    type(
        "ShelfType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.Shelf}),
            "get_queryset": classmethod(_visible_shelves),
        },
    )

    class OwnedShelf(FilterSet):
        code_default = _DefaultCodeFilter(field_name="code")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

    attrs: dict[str, object] = {
        "shelves": RelatedFilter(OwnedShelf, field_name="shelves"),
        "Meta": type("Meta", (), {"model": library_models.Branch, "fields": {"name": ["exact"]}}),
    }
    if leaf == "walked":
        attrs["own"] = _DefaultCodeFilter(field_name="shelves__code")
    parent = type("BranchOwn", (FilterSet,), attrs)
    assert issubclass(parent, FilterSet)
    assert isinstance(parent.get_filters()["shelves__code_default"], ProjectedChildFilter)
    base = library_models.Branch.objects.order_by("name")
    if mode == "sync":
        _ = parent.apply_sync({}, base, _make_info())
    elif mode == "async":
        _ = asyncio.run(parent.apply_async({}, base, _make_info()))
    else:
        _ = parent(data={}, queryset=base, request=HttpRequest()).qs
    assert len(calls) == 1


@pytest.mark.parametrize("projected", [True, False], ids=["projected", "plain-copy"])
def test_an_unresolved_child_default_keeps_its_projection_class(
    *,
    projected: bool,
) -> None:
    """Projection class identity is private; native unresolved-hop holders own both wire verdicts."""
    _register_plain_types(library_models.Shelf)

    class ShelfChild(FilterSet):
        branch = RelatedFilter(
            None,
            field_name="branch",
            queryset=library_models.Branch.objects.all(),
        )
        branch_default = _DefaultCodeFilter(field_name="branch__name")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    child: type[FilterSet] = ShelfChild
    if projected:

        class OwnedShelfChild(ShelfChild):
            def __init__(
                self,
                data: QueryDict | dict[str, object] | None = None,
                queryset: QuerySet[django_models.Model] | None = None,
                *,
                request: HttpRequest | None = None,
                prefix: str | None = None,
            ) -> None:
                super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

        child = OwnedShelfChild

    class BranchParent(FilterSet):
        shelves = RelatedFilter(child, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    leaf = BranchParent.get_filters()["shelves__branch_default"]
    assert isinstance(leaf, ProjectedChildFilter) is projected


def test_a_consumer_upstream_loop_keeps_its_projected_filter_class() -> None:
    """The copied filter class is private; the native upstream-loop holder owns its visible rows."""

    def _visible_shelves(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        return queryset.exclude(topic="secret")

    branch_filter = _shelf_and_branch_filters(_visible_shelves)

    class UpstreamLoop(branch_filter):
        @override
        def filter_queryset(self, queryset: QuerySet[_M]) -> QuerySet[_M]:
            return BaseFilterSet.filter_queryset(self, queryset)

    UpstreamLoop.get_filters()
    built = UpstreamLoop(
        data={"shelves__code_is": "match"},
        queryset=library_models.Branch.objects.all(),
        request=HttpRequest(),
    )
    assert isinstance(built.filters["shelves__code_is"], ProjectedChildFilter)


def test_a_prefixed_direct_form_runs_only_the_supplied_method_and_absence_probe() -> None:
    """Callback counts and request identity are private; native relation form holders own the rows."""
    calls: list[str] = []
    branch_filter = _counting_branch_filters(calls)
    built = branch_filter(
        data={"p-shelves__code_is": "match"},
        queryset=library_models.Branch.objects.order_by("name"),
        request=HttpRequest(),
        prefix="p",
    )
    # The absent ``topic_seen`` copy runs once over unscoped rows to learn it constrains nothing.
    _ = built.qs
    assert sorted(calls) == ["code_is", "topic_seen="]


def test_one_bound_projected_range_calls_only_the_named_method_once() -> None:
    """One physical range axis invokes its method once, without a false absence probe.

    A second invocation can produce the same response, so wire JSON cannot
    distinguish this callback-count contract. Live open-bound filtering lives in
    ``examples/fakeshop/test_query/test_relation_filter_form_paths_api.py``.
    """
    calls: list[str] = []
    branch_filter = _counting_branch_filters(calls)
    leaf = branch_filter.get_filters()["shelves__code_span"]
    keys = multi_widget_keys(read_attr(leaf.field, "widget"), "shelves__code_span")
    assert keys is not None
    built = branch_filter(
        data={keys[0]: "m"},
        queryset=library_models.Branch.objects.order_by("name"),
        request=HttpRequest(),
    )
    _ = built.qs
    # The absent ``topic_seen`` copy runs once over unscoped rows to learn it constrains nothing.
    assert sorted(calls) == ["code_span", "topic_seen="]


def test_a_direct_form_keeps_its_omitted_projected_field_without_deriving_its_hook() -> None:
    """Only private metadata or callback observations remain here.

    Live sibling: ``examples/fakeshop/test_query/test_relation_filter_defaults_api.py``.
    """
    calls: list[object] = []

    def _visible_shelves(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        calls.append(info)
        return queryset

    branch_filter = _shelf_and_branch_filters(_visible_shelves)
    assert isinstance(branch_filter.get_filters()["shelves__code_is"], ProjectedChildFilter)
    built = branch_filter(
        data={"name": "alpha"},
        queryset=library_models.Branch.objects.order_by("name"),
        request=HttpRequest(),
    )
    assert "shelves__code_is" in built.form.fields
    _ = built.qs
    assert calls == []


@pytest.mark.parametrize("name", ["on_shelf", "not_on_shelf"], ids=["key", "excluding-key"])
def test_a_supplied_empty_forward_key_derives_its_target_hook_once(name: str) -> None:
    """Callback counts and request identity are private; native relation form holders own the rows."""
    calls: list[object] = []

    def _visible_shelves(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        calls.append(info)
        return queryset.exclude(topic="secret")

    type(
        "ShelfCountingType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.Shelf}),
            "get_queryset": classmethod(_visible_shelves),
        },
    )

    class ShelfChild(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BookParent(FilterSet):
        visible_shelf = RelatedFilter(ShelfChild, field_name="shelf")
        on_shelf = ModelChoiceFilter(
            field_name="shelf",
            queryset=library_models.Shelf.objects.all(),
        )
        not_on_shelf = ModelChoiceFilter(
            field_name="shelf",
            queryset=library_models.Shelf.objects.all(),
            exclude=True,
        )

        class Meta:
            model = library_models.Book
            fields = {"shelf": ["exact"]}

    BookParent.get_filters()
    built = BookParent(
        data={name: ""},
        queryset=library_models.Book.objects.all(),
        request=HttpRequest(),
    )
    _ = built.qs
    assert len(calls) == 1


def test_a_supplied_empty_many_key_derives_its_target_hook_once() -> None:
    """Callback counts and request identity are private; native relation form holders own the rows."""
    calls: list[object] = []

    def _visible_books(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Book],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Book]:
        calls.append(info)
        return queryset

    type(
        "BookCountingType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.Book}),
            "get_queryset": classmethod(_visible_books),
        },
    )

    class BookChild(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    class GenreKeys(FilterSet):
        visible_books = RelatedFilter(BookChild, field_name="books")
        has_any_book = ModelMultipleChoiceFilter(
            field_name="books",
            queryset=library_models.Book.objects.all(),
        )

        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    GenreKeys.get_filters()
    built = GenreKeys(
        data={"has_any_book": []},
        queryset=library_models.Genre.objects.all(),
        request=HttpRequest(),
    )
    _ = built.qs
    assert len(calls) == 1


def test_kanban_multirelation_method_callback_count_matches_the_nested_spelling() -> None:
    """Only private metadata or callback observations remain here.

    Live sibling: ``examples/fakeshop/test_query/test_visible_relation_boundaries_api.py``.
    """
    _register_plain_types(kanban_models.Milestone, kanban_models.TargetVersion)
    calls: list[str] = []

    class MilestoneCounter(FilterSet):
        key_is = CharFilter(field_name="key", method="filter_key_is")

        class Meta:
            model = kanban_models.Milestone
            fields = {"key": ["exact"]}

        def filter_key_is(
            self,
            queryset: QuerySet[kanban_models.Milestone],
            _name: str,
            value: object,
        ) -> QuerySet[kanban_models.Milestone]:
            calls.append("key_is")
            return queryset.filter(key=value)

    class CardCounter(FilterSet):
        milestone = RelatedFilter(MilestoneCounter, field_name="target_version__milestone")

        class Meta:
            model = kanban_models.Card
            fields = {"title": ["exact"]}

    CardCounter.get_filters()
    for filter_input in ({"milestone__key_is": "alpha"}, {"milestone": {"key_is": "alpha"}}):
        _ = CardCounter.apply_sync(filter_input, kanban_models.Card.objects.all(), _make_info())
    assert calls == ["key_is", "key_is"]


def test_mti_projected_child_method_is_invoked_once() -> None:
    """An MTI child's projected method is called once before the parent queryset is evaluated.

    Descendant correlation and rowsets are owned by
    ``examples/fakeshop/test_query/test_relation_filter_boundaries_api.py``.
    """
    _register_plain_types(library_models.LendingDesk)
    calls: list[str] = []

    class DeskCounter(FilterSet):
        windows_are = NumberFilter(field_name="window_count", method="filter_windows_are")

        class Meta:
            model = library_models.LendingDesk
            fields = {"window_count": ["exact"]}

        def filter_windows_are(
            self,
            queryset: QuerySet[library_models.LendingDesk],
            _name: str,
            value: object,
        ) -> QuerySet[library_models.LendingDesk]:
            calls.append("windows_are")
            return queryset.filter(window_count=value)

    class TicketCounter(FilterSet):
        desk = RelatedFilter(DeskCounter, field_name="venue")

        class Meta:
            model = library_models.RepairTicket
            fields = {"code": ["exact"]}

    TicketCounter.get_filters()
    TicketCounter.apply_sync(
        {"desk__windows_are": 2},
        library_models.RepairTicket.objects.all(),
        _make_info(),
    )
    assert calls == ["windows_are"]


def test_a_customized_childs_walked_leaf_keeps_its_projection_class() -> None:
    """The projection class is private; native Loan reentry holders own intermediate and target rows."""

    def _visible_patrons(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Patron],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Patron]:
        return queryset.exclude(name="hidden")

    def _visible_loans(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Loan],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Loan]:
        return queryset.exclude(note__startswith="secret")

    for model, hook in (
        (library_models.Patron, classmethod(_visible_patrons)),
        (library_models.Loan, classmethod(_visible_loans)),
    ):
        type(
            f"{model.__name__}VisibleType",
            (DjangoType,),
            {"Meta": type("Meta", (), {"model": model}), "get_queryset": hook},
        )

    class LoanChild(FilterSet):
        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    class PatronChild(FilterSet):
        loans = RelatedFilter(LoanChild, field_name="loans")

        class Meta:
            model = library_models.Patron
            fields = {"name": ["exact"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

    class LoanParent(FilterSet):
        patron = RelatedFilter(PatronChild, field_name="patron")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    leaf = LoanParent.get_filters()["patron__loans__note"]
    assert isinstance(leaf, ProjectedChildFilter)


_ACTING_ABSENT_SHAPES: dict[str, tuple[str, dict[str, object], list[str], int]] = {
    # shape: (leaf, input, visible result, consumer ``filter`` calls)
    "omitted": (
        "text",
        {},
        ["alpha"],
        2,
    ),
    "range-no-bounds": (
        "range",
        {"own": dict[str, object]()},
        ["alpha"],
        2,
    ),
    "range-both-bounds-null": (
        "range",
        {"own": {"start": None, "end": None}},
        ["alpha"],
        2,
    ),
    "omitted-in-or-arm": (
        "text",
        {"or_": [{"name": "alpha"}, {"name": "beta"}]},
        ["alpha"],
        4,
    ),
    "undeclared-scoped-hop": (
        "alt",
        {},
        ["alpha"],
        2,
    ),
    "nested-child-level": (
        "text",
        {"branch": {}},
        ["open"],
        2,
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("shape", list(_ACTING_ABSENT_SHAPES))
def test_absent_walking_leaf_acting_on_its_absent_value_awaits_its_hops_under_apply_async(
    shape: str,
    mode: str,
) -> None:
    """``apply_async`` awaits the hops of an absent walking leaf whose filter acts on the absent value.

    ``own`` reads an absent value as a default (``"match"``; ``"a"``..``"z"`` for
    the range, absent when omitted or naming no bound), so it constrains to
    branches with a visible ``match`` shelf (``beta``'s is hidden). Under
    ``apply_async`` the target type's ``get_queryset`` is async-only and the
    hop it scopes is awaited before the ``.qs`` read; under ``apply_sync`` it
    is sync. Both run the hook once and the consumer ``filter`` as often: once
    per request to learn the absent value acts, then once over the visible rows
    per set or arm the leaf is absent on. The hop is a declared ``shelves`` branch, or the
    undeclared ``alt_shelves`` relation ``ShelfType`` scopes; at the nested
    child level the walking set is a ``RelatedFilter`` target on shelves.
    """
    leaf, filter_input, visible, filter_runs = _ACTING_ABSENT_SHAPES[shape]
    hook_calls: list[object] = []
    filter_calls: list[object] = []

    def _sync_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        hook_calls.append(info)
        return queryset.exclude(topic="secret")

    async def _async_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        hook_calls.append(info)
        return await sync_to_async(lambda: queryset.exclude(topic="secret"))()

    class _DefaultText(CharFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            filter_calls.append(value)
            return super().filter(qs, value or "match")

    class _DefaultSpan(RangeFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            filter_calls.append(value)
            return super().filter(qs, value or ["a", "z"])

    branch_filter = _shelf_and_branch_filters(_sync_visible if mode == "sync" else _async_visible)
    own: Filter = (
        _DefaultSpan(field_name="shelves__code", lookup_expr="range")
        if leaf == "range"
        else _DefaultText(field_name="alt_shelves__code" if leaf == "alt" else "shelves__code")
    )
    walking = type(
        "BranchOwn",
        (branch_filter,),
        {
            "own": own,
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Branch, "fields": {"name": ["exact"]}},
            ),
        },
    )
    walking.get_filters()
    _seed_open_and_secret_match_shelves()
    for shelf in library_models.Shelf.objects.select_related("branch"):
        shelf.alt_branches.add(shelf.branch)
    applied: type[FilterSet] = walking
    base: QuerySet[django_models.Model] = library_models.Branch.objects.order_by("name")
    column = "name"
    if shape == "nested-child-level":
        _register_plain_types(library_models.Branch)
        applied = type(
            "ShelfOverBranchOwn",
            (FilterSet,),
            {
                "branch": RelatedFilter(walking, field_name="branch"),
                "Meta": type(
                    "Meta",
                    (),
                    {"model": library_models.Shelf, "fields": {"code": ["exact"]}},
                ),
            },
        )
        assert issubclass(applied, FilterSet)
        applied.get_filters()
        base = library_models.Shelf.objects.order_by("topic")
        column = "topic"
    if mode == "sync":
        qs = applied.apply_sync(filter_input, base, _make_info())
    else:
        qs = asyncio.run(applied.apply_async(filter_input, base, _make_info()))
    assert list(qs.values_list(column, flat=True)) == visible
    assert len(hook_calls) == 1
    assert len(filter_calls) == filter_runs


@pytest.mark.django_db
def test_apply_async_derives_nothing_for_an_inert_absent_walking_leaf_over_an_unregistered_target() -> (
    None
):
    """An absent walking leaf whose filter skips the absent value awaits no hop, so nothing raises.

    ``own`` walks ``shelves`` whose target model has no registered ``DjangoType``:
    deriving the hop would raise the branch's ``ConfigurationError``, so the
    absent leaf returning its rows by identity derives nothing, as on
    ``apply_sync``, and every branch comes back.
    """
    branch_filter = _shelf_and_branch_filters()
    walking = type(
        "BranchOwn",
        (branch_filter,),
        {
            "own": CharFilter(field_name="shelves__code"),
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Branch, "fields": {"name": ["exact"]}},
            ),
        },
    )
    walking.get_filters()
    _seed_open_and_secret_match_shelves()
    base = library_models.Branch.objects.order_by("name")
    for qs in (
        walking.apply_sync({}, base, _make_info()),
        asyncio.run(walking.apply_async({}, base, _make_info())),
    ):
        assert list(qs.values_list("name", flat=True)) == ["alpha", "beta"]


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    (
        "reads_queryset",
        "visible",
        "filter_runs",
        "hook_runs",
    ),
    [
        (
            False,
            ["open"],
            2,
            1,
        ),
        (
            True,
            ["open", "secret"],
            1,
            0,
        ),
    ],
    ids=["value-default", "queryset-state"],
)
def test_absent_relation_key_leaf_on_one_forward_hop_answers_alike_on_both_colors(
    mode: str,
    reads_queryset: bool,  # noqa: FBT001 - a parametrized row
    visible: list[str],
    filter_runs: int,
    hook_runs: int,
) -> None:
    """An absent relation-key leaf on one forward hop is asked over the rows the set was built over.

    ``home`` compares ``Shelf.branch``'s key, so its chain walks no hop and its
    absent probe reads the set's own rows, never the rows ``code_first`` left:
    ``apply_sync`` and ``apply_async`` (whose ``BranchType.get_queryset`` is
    async-only) agree on rows, hook runs and filter runs. Read as a default,
    the absent value names ``alpha`` (``beta`` is hidden), so the leaf acts and
    the key hop is awaited; a filter acting only on rows another leaf already
    filtered sees unfiltered rows when asked, so it constrains nothing on either
    color.
    """
    hook_calls: list[object] = []
    filter_calls: list[object] = []

    def _sync_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        hook_calls.append(info)
        return queryset.exclude(name="beta")

    async def _async_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        hook_calls.append(info)
        return await sync_to_async(lambda: queryset.exclude(name="beta"))()

    _seed_open_and_secret_match_shelves()
    alpha_pk = library_models.Branch.objects.get(name="alpha").pk

    class _DefaultHome(CharFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            filter_calls.append(value)
            if reads_queryset:
                if not value and qs.query.has_filters():
                    return qs.filter(branch=alpha_pk)
                return super().filter(qs, value)
            return super().filter(qs, value or str(alpha_pk))

    type(
        "BranchType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.Branch}),
            "get_queryset": classmethod(_sync_visible if mode == "sync" else _async_visible),
        },
    )

    class BranchOnly(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    shelf_filter = type(
        "ShelfOverBranch",
        (FilterSet,),
        {
            "branch": RelatedFilter(BranchOnly, field_name="branch"),
            "code_first": CharFilter(field_name="code"),
            "home": _DefaultHome(field_name="branch"),
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Shelf, "fields": {"topic": ["exact"]}},
            ),
        },
    )
    assert issubclass(shelf_filter, FilterSet)
    shelf_filter.get_filters()
    base = library_models.Shelf.objects.order_by("topic")
    filter_input = {"code_first": "match"}
    if mode == "sync":
        qs = shelf_filter.apply_sync(filter_input, base, _make_info())
    else:
        qs = asyncio.run(shelf_filter.apply_async(filter_input, base, _make_info()))
    assert list(qs.values_list("topic", flat=True)) == visible
    assert len(hook_calls) == hook_runs
    assert len(filter_calls) == filter_runs


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_absent_leaf_verdict_holds_in_every_logical_arm_on_both_colors(mode: str) -> None:
    """An absent walking leaf is asked once per request, over the rows the root set was built over.

    ``home`` compares ``Shelf.branch``'s key and acts on its absent value only
    over rows something already filtered. The root set is built over unfiltered
    shelves, so ``home`` constrains nothing there, and the ``or`` arm reads that
    answer instead of asking again over the rows its ``branch`` clause left:
    ``apply_sync`` and ``apply_async`` (whose ``BranchType.get_queryset`` is
    async-only) agree on rows, hook runs and filter runs, and the ``.qs`` read
    derives no hop ``home`` walks.
    """
    hook_calls: list[object] = []
    filter_calls: list[object] = []

    def _sync_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        hook_calls.append(info)
        return queryset.exclude(name="beta")

    async def _async_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        hook_calls.append(info)
        return await sync_to_async(lambda: queryset.exclude(name="beta"))()

    _seed_open_and_secret_match_shelves()
    alpha_pk = library_models.Branch.objects.get(name="alpha").pk

    class _FilteredRowsHome(CharFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            filter_calls.append(value)
            if not value and qs.query.has_filters():
                return qs.filter(branch=alpha_pk)
            return super().filter(qs, value)

    type(
        "BranchType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.Branch}),
            "get_queryset": classmethod(_sync_visible if mode == "sync" else _async_visible),
        },
    )

    class BranchOnly(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    shelf_filter = type(
        "ShelfOverBranch",
        (FilterSet,),
        {
            "branch": RelatedFilter(BranchOnly, field_name="branch"),
            "home": _FilteredRowsHome(field_name="branch"),
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Shelf, "fields": {"topic": ["exact"]}},
            ),
        },
    )
    assert issubclass(shelf_filter, FilterSet)
    shelf_filter.get_filters()
    base = library_models.Shelf.objects.order_by("topic")
    filter_input = {"or_": [{"branch": {"name": "alpha"}}]}
    if mode == "sync":
        qs = shelf_filter.apply_sync(filter_input, base, _make_info())
    else:
        qs = asyncio.run(shelf_filter.apply_async(filter_input, base, _make_info()))
    assert list(qs.values_list("topic", flat=True)) == ["open"]
    assert len(hook_calls) == 1
    assert len(filter_calls) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_an_arm_cleaning_an_absent_leaf_to_another_value_asks_it_again_on_both_colors(
    mode: str,
) -> None:
    """A verdict is per (leaf, cleaned value): an arm cleaning the leaf to another value asks again.

    The consumer ``Meta.form`` cleans the absent ``home`` to ``"alpha"`` wherever
    ``topic`` is supplied. The root set names no ``topic``, so its ``home`` cleans
    to ``""`` and constrains nothing; each ``or`` arm names a ``topic``, so its
    ``home`` cleans to ``"alpha"``, which the root never answered for, and the arm
    asks it over its own value and applies it, as django-filter applies each
    arm's cleaned value: the secret shelf's branch is ``beta``, so only the open
    shelf matches, on ``apply_sync`` and ``apply_async`` alike. The arm asks
    before the ``.qs`` read, so under ``apply_async`` (whose
    ``BranchType.get_queryset`` is async-only) the hop ``home`` walks is awaited
    first; both colors run the hook once.
    """
    hook_calls: list[object] = []
    filter_calls: list[object] = []

    def _visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        hook_calls.append(info)
        return queryset

    async def _async_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        hook_calls.append(info)
        return queryset

    class _TopicDefaultsHome(forms.Form):
        @override
        def clean(self) -> dict[str, object]:
            cleaned: dict[str, object] = self.cleaned_data
            if not cleaned.get("home") and cleaned.get("topic"):
                cleaned["home"] = "alpha"
            return cleaned

    class _CountedHome(CharFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            filter_calls.append(value)
            return super().filter(qs, value)

    type(
        "BranchType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.Branch}),
            "get_queryset": classmethod(_visible if mode == "sync" else _async_visible),
        },
    )

    class BranchOnly(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    shelf_filter = type(
        "ShelfDefaultingHome",
        (FilterSet,),
        {
            "branch": RelatedFilter(BranchOnly, field_name="branch"),
            "home": _CountedHome(field_name="branch__name"),
            "Meta": type(
                "Meta",
                (),
                {
                    "model": library_models.Shelf,
                    "fields": {"topic": ["exact"]},
                    "form": _TopicDefaultsHome,
                },
            ),
        },
    )
    assert issubclass(shelf_filter, FilterSet)
    shelf_filter.get_filters()
    _seed_open_and_secret_match_shelves()
    base = library_models.Shelf.objects.order_by("topic")
    filter_input = {"or_": [{"topic": "secret"}, {"topic": "open"}]}
    if mode == "sync":
        qs = shelf_filter.apply_sync(filter_input, base, _make_info())
    else:
        qs = asyncio.run(shelf_filter.apply_async(filter_input, base, _make_info()))
    assert list(qs.values_list("topic", flat=True)) == ["open"]
    assert len(hook_calls) == 1
    assert filter_calls == [
        "",
        "alpha",
        "alpha",
        "alpha",
        "alpha",
    ]


def _shelf_filter_adding_home_from_topic(
    hook: Callable[..., object],
    init_calls: list[object],
    filter_calls: list[object],
) -> type[FilterSet]:
    """A ``Shelf`` set whose ``__init__`` adds an absent ``home`` leaf wherever ``topic`` is sent.

    ``home`` walks the declared ``branch`` hop and reads its absent value as
    ``"alpha"``, so it acts; ``BranchType.get_queryset`` is ``hook``.
    """
    type(
        "BranchType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.Branch}),
            "get_queryset": classmethod(hook),
        },
    )

    class _ActingHome(CharFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            filter_calls.append(value)
            return super().filter(qs, value or "alpha")

    class BranchOnly(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    class ShelfAddingHome(FilterSet):
        branch = RelatedFilter(BranchOnly, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = {"topic": ["exact"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            init_calls.append(data)
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)
            if data and "topic" in data:
                self.filters["home"] = _ActingHome(field_name="branch__name")

    ShelfAddingHome.get_filters()
    return ShelfAddingHome


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    ("filter_input", "inits"),
    [
        ({"or_": [{"topic": "secret"}, {"topic": "open"}]}, 3),
        ({"or_": [{"and_": [{"topic": "secret"}]}, {"and_": [{"topic": "open"}]}]}, 5),
    ],
    ids=["arm", "nested-arm"],
)
def test_an_arm_only_absent_leaf_a_consumer_init_adds_is_awaited_on_both_colors(
    filter_input: dict[str, object],
    inits: int,
    mode: str,
) -> None:
    """An absent leaf only an arm's ``__init__`` adds is asked before the ``.qs`` read.

    The root set names no ``topic``, so it has no ``home``; each arm (or each arm
    of an arm) naming one gets an acting ``home``, which the root's probe never
    saw. The probe builds every arm as the ``.qs`` read will, asks its ``home``,
    and under ``apply_async`` (whose ``BranchType.get_queryset`` is async-only)
    awaits the ``branch`` hop before the ``.qs`` read, which reuses the arms: the
    secret shelf's branch is ``beta``, so only the open shelf matches, and both
    colors run the hook once, each arm's ``__init__`` once and each ``home``
    twice (asked, then applied).
    """
    hook_calls: list[object] = []
    init_calls: list[object] = []
    filter_calls: list[object] = []

    def _sync_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        hook_calls.append(info)
        return queryset

    async def _async_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        hook_calls.append(info)
        return queryset

    shelf_filter = _shelf_filter_adding_home_from_topic(
        _sync_visible if mode == "sync" else _async_visible,
        init_calls,
        filter_calls,
    )
    _seed_open_and_secret_match_shelves()
    base = library_models.Shelf.objects.order_by("topic")
    if mode == "sync":
        qs = shelf_filter.apply_sync(filter_input, base, _make_info())
    else:
        qs = asyncio.run(shelf_filter.apply_async(filter_input, base, _make_info()))
    assert list(qs.values_list("topic", flat=True)) == ["open"]
    assert len(hook_calls) == 1
    assert len(init_calls) == inits
    assert filter_calls == [
        "",
        "",
        "",
        "",
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_an_inert_arm_only_absent_leaf_over_an_unregistered_target_derives_nothing(
    mode: str,
) -> None:
    """An arm-only absent leaf whose filter skips its value derives no hop, whatever its target.

    ``own`` walks ``shelves``, whose target has no registered ``DjangoType``, so
    deriving that hop raises; an ``__init__`` adds it only to an arm naming
    ``name``. Its absent value cleans to ``""``, which django-filter's
    ``CharFilter`` skips, so the probe derives nothing and the arm matches on
    ``name`` alone, on both colors.
    """
    branch_filter = _shelf_and_branch_filters()

    class InitAddsOwn(branch_filter):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)
            if data and "name" in data:
                self.filters["own"] = CharFilter(field_name="shelves__code")

    InitAddsOwn.get_filters()
    _seed_open_and_secret_match_shelves()
    base = library_models.Branch.objects.order_by("name")
    filter_input = {"or_": [{"name": "alpha"}]}
    if mode == "sync":
        qs = InitAddsOwn.apply_sync(filter_input, base, _make_info())
    else:
        qs = asyncio.run(InitAddsOwn.apply_async(filter_input, base, _make_info()))
    assert list(qs.values_list("name", flat=True)) == ["alpha"]


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_an_arm_whose_init_replaces_its_queryset_is_built_again_over_the_arm_rows(
    mode: str,
) -> None:
    """A probed arm whose ``__init__`` replaced its queryset is built again for the ``.qs`` read.

    The probe builds each arm over the rows the root set was built over; an arm
    reusing it would have its ``queryset`` reset to the arm's rows, losing what
    the ``__init__`` narrowed. This set's ``__init__`` drops ``beta``'s shelves
    wherever ``topic`` is sent and its ``qs`` override reads ``self.queryset``,
    so the ``secret`` arm matches nothing and only the open shelf survives. Each
    arm is built twice (probe, then ``.qs`` read), keeping the probe's verdict
    for ``home``: both colors run the hook once, ``__init__`` five times and
    ``home`` four times.
    """
    hook_calls: list[object] = []
    init_calls: list[object] = []
    filter_calls: list[object] = []

    def _sync_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        hook_calls.append(info)
        return queryset

    async def _async_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        hook_calls.append(info)
        return queryset

    adding_home = _shelf_filter_adding_home_from_topic(
        _sync_visible if mode == "sync" else _async_visible,
        init_calls,
        filter_calls,
    )

    class NarrowingShelf(adding_home):
        class Meta:
            model = library_models.Shelf
            fields = {"topic": ["exact"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            if data and "topic" in data and queryset is not None:
                queryset = queryset.exclude(branch__name="beta")
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

        @property
        @override
        def qs(self) -> QuerySet[django_models.Model]:
            return super().qs

    NarrowingShelf.get_filters()
    _seed_open_and_secret_match_shelves()
    base = library_models.Shelf.objects.order_by("topic")
    filter_input = {"or_": [{"topic": "secret"}, {"topic": "open"}]}
    if mode == "sync":
        qs = NarrowingShelf.apply_sync(filter_input, base, _make_info())
    else:
        qs = asyncio.run(NarrowingShelf.apply_async(filter_input, base, _make_info()))
    assert list(qs.values_list("topic", flat=True)) == ["open"]
    assert len(hook_calls) == 1
    assert len(init_calls) == 5
    assert filter_calls == [
        "",
        "",
        "",
        "",
    ]


@pytest.mark.django_db
def test_an_arm_a_filter_queryset_override_replaces_is_built_from_the_new_input() -> None:
    """An arm input a consumer ``filter_queryset`` swaps in is built from that input, not the probed one.

    The override swaps the ``OPEN`` arm for an ``open`` one before django-filter's
    pipeline runs; the probe built the arm from the input sent, so the ``.qs``
    read builds it from the swapped-in input instead of reusing it, and the arm
    matches the ``open`` shelf.
    """

    class LoweringShelf(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"topic": ["exact"]}

        @override
        def filter_queryset(self, queryset: QuerySet[_M]) -> QuerySet[_M]:
            if self.data == {"or": [{"topic": "OPEN"}]}:
                self.data = {"or": [{"topic": "open"}]}
            return super().filter_queryset(queryset)

    LoweringShelf.get_filters()
    _seed_open_and_secret_match_shelves()
    qs = LoweringShelf.apply_sync(
        {"or_": [{"topic": "OPEN"}]},
        library_models.Shelf.objects.order_by("topic"),
        _make_info(),
    )
    assert list(qs.values_list("topic", flat=True)) == ["open"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("leaf", "filter_input"),
    [
        (None, {"shelves": {"code": "match"}}),
        (None, {"shelves__code": "match"}),
        ("alt_shelves__code", {"own": "match"}),
    ],
    ids=["nested-branch", "declared-hop", "undeclared-hop"],
)
def test_apply_sync_over_an_async_only_hop_hook_names_the_filter_recourse(
    leaf: str | None,
    filter_input: dict[str, object],
) -> None:
    """An async-only ``get_queryset`` a filter reads on ``apply_sync`` raises naming ``apply_async``.

    The ``shelves`` branch, a flat leaf over its declared hop and a flat leaf over
    the undeclared ``alt_shelves`` relation ``ShelfType`` scopes each read
    ``ShelfType.get_queryset``; the ``SyncMisuseError`` points at
    ``FilterSet.apply_async`` or a sync hook, never at the Relay node defaults.
    """

    async def _async_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        return queryset

    applied = _shelf_and_branch_filters(_async_visible)
    if leaf is not None:
        walking = type(
            "BranchOwn",
            (applied,),
            {
                "own": CharFilter(field_name=leaf),
                "Meta": type(
                    "Meta",
                    (),
                    {"model": library_models.Branch, "fields": {"name": ["exact"]}},
                ),
            },
        )
        assert issubclass(walking, FilterSet)
        walking.get_filters()
        applied = walking
    _seed_open_and_secret_match_shelves()
    with pytest.raises(SyncMisuseError, match=r"await FilterSet\.apply_async") as raised:
        list(applied.apply_sync(filter_input, library_models.Branch.objects.all(), _make_info()))
    assert "Relay node defaults" not in str(raised.value)


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    "path",
    ["shelves__code", "alt_shelves__code"],
    ids=["declared", "undeclared"],
)
def test_walking_leaf_a_consumer_init_adds_awaits_its_hops_under_apply_async(
    path: str,
    mode: str,
) -> None:
    """A walking leaf a consumer ``__init__`` puts on the set is probed like a declared one.

    ``own`` acts on its absent value (``"match"``), so it constrains to branches
    with a visible ``match`` shelf (``beta``'s is hidden). Its hop is the
    declared ``shelves`` branch, or the undeclared ``alt_shelves`` relation
    ``ShelfType`` scopes. Under ``apply_async`` ``ShelfType.get_queryset`` is
    async-only and the hop is awaited before the ``.qs`` read; both colors run
    the hook once and the filter twice.
    """
    hook_calls: list[object] = []
    filter_calls: list[object] = []

    def _sync_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        hook_calls.append(info)
        return queryset.exclude(topic="secret")

    async def _async_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Shelf],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Shelf]:
        hook_calls.append(info)
        return await sync_to_async(lambda: queryset.exclude(topic="secret"))()

    class _DefaultText(CharFilter):
        @override
        def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
            filter_calls.append(value)
            return super().filter(qs, value or "match")

    branch_filter = _shelf_and_branch_filters(_sync_visible if mode == "sync" else _async_visible)

    class InitAdded(branch_filter):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)
            self.filters["own"] = _DefaultText(field_name=path)

    InitAdded.get_filters()
    _seed_open_and_secret_match_shelves()
    for shelf in library_models.Shelf.objects.select_related("branch"):
        shelf.alt_branches.add(shelf.branch)
    base = library_models.Branch.objects.order_by("name")
    if mode == "sync":
        qs = InitAdded.apply_sync({}, base, _make_info())
    else:
        qs = asyncio.run(InitAdded.apply_async({}, base, _make_info()))
    assert list(qs.values_list("name", flat=True)) == ["alpha"]
    assert len(hook_calls) == 1
    assert len(filter_calls) == 2


def _hide(model: type[django_models.Model], fields: object = "__all__", **lookups: object) -> None:
    """Register a type for ``model`` whose ``get_queryset`` hides the rows matching ``lookups``."""

    def get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[django_models.Model],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[django_models.Model]:
        return queryset.exclude(**lookups)

    type(
        f"{model.__name__}HidingType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": model, "fields": fields}),
            "get_queryset": classmethod(get_queryset),
        },
    )


def _applied(
    filterset: type[FilterSet],
    filter_input: object,
    base: QuerySet[django_models.Model],
) -> set[object]:
    """The pks ``filterset.apply_sync`` keeps for ``filter_input`` over ``base``."""
    return set(filterset.apply_sync(filter_input, base, _make_info()).values_list("pk", flat=True))


def _genre_parent(*, declared: bool = True) -> type[FilterSet]:
    """Genres filtered through ``books``, declared as ``visible_books`` unless ``declared`` is off."""

    class BookChild(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"], "subtitle": ["exact", "isnull"]}

    class GenreParent(FilterSet):
        if declared:
            visible_books = RelatedFilter(BookChild, field_name="books")
        without_title = CharFilter(field_name="books__title", exclude=True)

        class Meta:
            model = library_models.Genre
            fields = {
                "name": ["exact"],
                "books": ["exact", "isnull"],
                "books__title": ["exact"],
                "books__subtitle": ["isnull"],
            }

    GenreParent.get_filters()
    return GenreParent


@pytest.mark.parametrize(
    "filter_input",
    [
        {"books": {"is_null": True}},
        {"books": {"exact": [0]}},
        {"without_title": "x"},
        {"not_": {"books": {"is_null": False}}},
    ],
    ids=[
        "key-isnull",
        "key-membership",
        "exclude",
        "key-in-not-arm",
    ],
)
def test_async_relation_key_and_exclusion_hops_derive_the_target_once(
    filter_input: dict[str, object],
) -> None:
    """Only private metadata or callback observations remain here.

    Live sibling: ``examples/fakeshop/test_query/test_visible_relation_boundaries_api.py``.
    """
    calls: list[object] = []

    async def _visible_books(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Book],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Book]:
        calls.append(info)
        return await sync_to_async(lambda: queryset.exclude(circulation_status="repair"))()

    type(
        "BookAsyncType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.Book}),
            "get_queryset": classmethod(_visible_books),
        },
    )
    parent = _genre_parent()
    _ = asyncio.run(
        parent.apply_async(filter_input, library_models.Genre.objects.all(), _make_info()),
    )
    assert len(calls) == 1


def test_inactive_relation_key_leaf_derives_no_target_hook() -> None:
    """A skipped relation-key leaf calls no target hook.

    Complete linked/empty root membership and child SQL are owned by
    ``examples/fakeshop/test_query/test_visible_relation_keys_api.py::test_inactive_relation_key_keeps_empty_and_linked_roots_without_child_sql``.
    """
    calls: list[object] = []

    def _visible_books(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Book],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Book]:
        calls.append(info)
        return queryset

    type(
        "BookCountingType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.Book}),
            "get_queryset": classmethod(_visible_books),
        },
    )
    _genre_parent().apply_sync(
        {"books": {"is_null": None}},
        library_models.Genre.objects.all(),
        _make_info(),
    )
    assert calls == []


@pytest.mark.parametrize(
    "register",
    [False, True],
    ids=["unregistered-target", "identity-hook-target"],
)
def test_undeclared_relation_no_type_scopes_is_not_walked(*, register: bool) -> None:
    """A relation whose target no type scopes keeps Django's own join: the leaf walks no hop.

    Neither an unregistered target model nor a type keeping the identity
    ``get_queryset`` changes a row, so the leaf keeps its original invocation
    (and its routing); a target type with a hook of its own is walked.
    """
    if register:
        type(
            "ShelfType",
            (DjangoType,),
            {"Meta": type("Meta", (), {"model": library_models.Shelf})},
        )

    class BranchKeys(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"alt_shelves": ["exact"], "alt_shelves__code": ["exact"]}

    filters = BranchKeys.get_filters()
    assert BranchKeys._flat_leaf_walk(filters["alt_shelves"]) is None
    assert BranchKeys._flat_leaf_walk(filters["alt_shelves__code"]) is None


def test_undeclared_relation_to_a_hooked_type_walks_one_hop_per_relation() -> None:
    """Each relation segment past the declared hops is one undeclared hop; a column ends the walk."""
    _hide(library_models.Book, circulation_status="repair")

    class BranchPaths(FilterSet):
        by_pk = NumberFilter(field_name="pk")

        class Meta:
            model = library_models.Branch
            fields = {"shelves__books__title": ["exact"]}

    filters = BranchPaths.get_filters()
    walk = BranchPaths._flat_leaf_walk(filters["shelves__books__title"])
    assert walk is not None
    hops, rest = walk
    assert all(isinstance(hop, UndeclaredHop) for hop in hops)
    assert [(hop.declared_attr, hop.model) for hop in hops if isinstance(hop, UndeclaredHop)] == [
        ("shelves", library_models.Shelf),
        ("books", library_models.Book),
    ]
    assert [hop.owner for hop in hops] == [BranchPaths, None]
    assert rest == "title"
    assert BranchPaths._flat_leaf_walk(filters["by_pk"]) is None


class _HopShelfFilter(FilterSet):
    """A model-backed target set for the declared-hop reads below."""

    class Meta:
        model = library_models.Shelf
        fields = ("code",)


class _HopModellessFilter(FilterSet):
    """A target set declaring no ``Meta.model``."""


class _HopBranchFilter(FilterSet):
    """The set declaring the ``shelves`` branch the declared-hop reads walk."""

    shelves = RelatedFilter(_HopShelfFilter, field_name="shelves")

    class Meta:
        model = library_models.Branch
        fields = ("name",)


def _declared_hop(
    *,
    owner: type[object] = _HopBranchFilter,
    related_obj: object = None,
    target: type[object] | None = _HopShelfFilter,
) -> DeclaredHop:
    """A declared ``shelves`` hop, its declaration ``_HopBranchFilter``'s unless one is given."""
    declaration = (
        _HopBranchFilter.related_filters["shelves"] if related_obj is None else related_obj
    )
    return DeclaredHop(owner, "shelves", declaration, target)


def test_a_declared_filter_hop_reads_its_declaring_set_and_relation() -> None:
    """A declared hop answers for its owner set, its ``RelatedFilter``, its relation and its model."""
    hop = _declared_hop()
    owner, declaration = sets_module._filter_declaration(hop)
    assert owner is _HopBranchFilter
    assert declaration is _HopBranchFilter.related_filters["shelves"]
    assert sets_module._hop_target_set(hop) is _HopShelfFilter
    assert sets_module._hop_relation(hop) == "shelves"
    assert sets_module._hop_model(hop) is library_models.Shelf
    assert sets_module._hop_source_model((hop,), 0) is library_models.Branch


@pytest.mark.parametrize(
    "hop",
    [
        pytest.param(_declared_hop(owner=library_models.Branch), id="owner-not-a-filter-set"),
        pytest.param(_declared_hop(related_obj=object()), id="declaration-not-a-related-filter"),
    ],
)
def test_a_declared_filter_hop_off_the_filter_family_is_refused(hop: DeclaredHop) -> None:
    """A filter set's walk reads only ``RelatedFilter`` declarations on ``FilterSet`` classes."""
    with pytest.raises(TypeError):
        sets_module._filter_declaration(hop)
    with pytest.raises(TypeError):
        sets_module._hop_relation(hop)


@pytest.mark.parametrize(
    "target",
    [
        pytest.param(None, id="unresolved"),
        pytest.param(library_models.Shelf, id="not-a-filter-set"),
    ],
)
def test_a_declared_hop_with_no_target_set_is_refused(target: type[object] | None) -> None:
    """A hop's target set is read only once the walk resolved it to a ``FilterSet``."""
    hop = _declared_hop(target=target)
    with pytest.raises(TypeError, match="expected the type the source guarantees"):
        sets_module._hop_target_set(hop)
    with pytest.raises(TypeError, match="expected the type the source guarantees"):
        sets_module._hop_model(hop)


def test_a_declared_hop_whose_target_set_has_no_model_is_refused() -> None:
    """A resolved branch target declares ``Meta.model``; one declaring none reaches no model."""
    hop = _declared_hop(target=_HopModellessFilter)
    with pytest.raises(TypeError, match="expected the type the source guarantees"):
        sets_module._hop_model(hop)


@pytest.mark.parametrize(
    "owner",
    [
        pytest.param(library_models.Branch, id="not-a-filter-set"),
        pytest.param(_HopModellessFilter, id="filter-set-without-model"),
    ],
)
def test_an_owner_of_a_walked_hop_with_no_model_is_refused(owner: type[object]) -> None:
    """The model a hop starts on is its owner set's ``Meta.model``; an owner with none has none."""
    hop = UndeclaredHop(owner, "shelves", library_models.Shelf, None)
    with pytest.raises(TypeError, match="expected the type the source guarantees"):
        sets_module._hop_source_model((hop,), 0)


def test_a_leaf_walking_no_hop_has_no_chain_to_apply() -> None:
    """Only a leaf ``_flat_leaf_walk`` reads or a projected copy reaches the relation-leaf path."""

    class BranchLeaves(FilterSet):
        by_pk = NumberFilter(field_name="pk")

        class Meta:
            model = library_models.Branch
            fields = ("name",)

    rows = library_models.Branch.objects.all()
    instance = BranchLeaves(data={}, queryset=rows)
    leaf = instance.filters["by_pk"]
    with pytest.raises(TypeError, match="expected an instance of _LeafChain, got NoneType"):
        instance._absent_leaf_applies(leaf, 1)
    with pytest.raises(TypeError, match="expected an instance of _LeafChain, got NoneType"):
        instance._apply_relation_leaf(rows, leaf, 1, supplied=True)


@pytest.mark.parametrize(
    ("parent_model", "field_name", "segment"),
    [
        (library_models.Book, "title__shelf", "title"),
        (library_models.Book, "shelf__nowhere", "nowhere"),
        (library_models.TaggedItem, "content_object", "content_object"),
    ],
    ids=["column", "missing", "generic-foreign-key"],
)
def test_branch_declared_over_a_non_relation_path_is_refused_at_expansion(
    parent_model: type[django_models.Model],
    field_name: str,
    segment: str,
) -> None:
    """A ``RelatedFilter`` whose ``field_name`` crosses a non-relation fails when the expansion builds.

    The check reads the parent model only: the unresolvable string target is
    never looked up.
    """
    parent = type(
        "Parent",
        (FilterSet,),
        {
            "misdeclared": RelatedFilter("NoSuchFilterSet", field_name=field_name),
            "Meta": type("Meta", (), {"model": parent_model, "fields": {"id": ["exact"]}}),
        },
    )
    with pytest.raises(
        ConfigurationError,
        match=rf"RelatedFilter 'misdeclared' has field_name '{field_name}', but '{segment}' is not",
    ):
        parent.get_filters()


def _branch_parent(
    parent_model: type[django_models.Model],
    field_name: str,
    child_model: type[django_models.Model],
    child_field: str = "id",
) -> type[FilterSet]:
    """A ``parent_model`` set declaring ``branch = RelatedFilter(<set on child_model>, field_name)``."""
    child = type(
        "Child",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": child_model, "fields": {child_field: ["exact"]}})},
    )
    return type(
        "Parent",
        (FilterSet,),
        {
            "branch": RelatedFilter(child, field_name=field_name),
            "Meta": type("Meta", (), {"model": parent_model, "fields": {"id": ["exact"]}}),
        },
    )


@pytest.mark.parametrize(
    (
        "parent_model",
        "field_name",
        "child_model",
        "reached",
    ),
    [
        (
            library_models.Book,
            "shelf",
            library_models.Genre,
            library_models.Shelf,
        ),
        (
            library_models.Book,
            "genres",
            library_models.Shelf,
            library_models.Genre,
        ),
        (
            library_models.Book,
            "loans",
            library_models.Patron,
            library_models.Loan,
        ),
        (
            library_models.Venue,
            "lendingdesk",
            library_models.Venue,
            library_models.LendingDesk,
        ),
        (
            library_models.LendingDesk,
            "selfservedesk",
            library_models.LendingDesk,
            library_models.SelfServeDesk,
        ),
        (
            library_models.LendingDesk,
            "selfservedesk",
            library_models.Venue,
            library_models.SelfServeDesk,
        ),
        (
            _CrLamp,
            "kiosk",
            _CrDesk,
            _CrKioskDesk,
        ),
        (
            _CrLamp,
            "spare_kiosk",
            _CrDesk,
            _CrKioskDesk,
        ),
        (
            _CrLamp,
            "kiosks",
            _CrDesk,
            _CrKioskDesk,
        ),
        (
            _CrLamp,
            "desk",
            _CrOwnKeyDesk,
            _CrDesk,
        ),
        (
            _CrLamp,
            "spare_desk",
            _CrOwnKeyDesk,
            _CrDesk,
        ),
        (
            _CrLamp,
            "desks",
            _CrOwnKeyDesk,
            _CrDesk,
        ),
        (
            _CrDeskNote,
            "note_desk",
            _CrNoteRoot,
            _CrNoteDesk,
        ),
    ],
    ids=[
        "unrelated-forward",
        "unrelated-many-to-many",
        "unrelated-reverse",
        "mti-ancestor-across-a-reverse-link",
        "mti-parent-across-a-reverse-link",
        "mti-grandparent-across-a-reverse-link",
        "mti-ancestor-without-the-foreign-key-to-field",
        "mti-ancestor-without-the-one-to-one-to-field",
        "mti-ancestor-without-the-many-to-many-to-field",
        "mti-descendant-keyed-off-its-parent-link-by-foreign-key",
        "mti-descendant-keyed-off-its-parent-link-by-one-to-one",
        "mti-descendant-keyed-off-its-parent-link-by-many-to-many",
        "mti-ancestor-across-a-reverse-generic-relation",
    ],
)
def test_branch_whose_target_set_model_the_relation_cannot_correlate_is_refused(
    parent_model: type[django_models.Model],
    field_name: str,
    child_model: type[django_models.Model],
    reached: type[django_models.Model],
) -> None:
    """A target set keyed on a model whose rows the relation's columns do not name fails at expansion.

    The branch correlates the target set's rows by the relation's own link
    columns (``optimizer/predicates.py::correlates_related_rows``): on an
    unrelated model, on an MTI ancestor lacking a column the target declares,
    or on an MTI descendant whose key is not its parent link, those columns
    hold other rows' values, and across a reverse link an ancestor's row
    matches itself whether or not a target row extends it. A reverse
    ``GenericRel``'s ``object_id`` is no foreign key, so it proves no target row
    exists either: an ancestor row would answer for a note no target row backs.
    """
    parent = _branch_parent(parent_model, field_name, child_model)
    with pytest.raises(
        ConfigurationError,
        match=(
            rf"FilterSet Parent: RelatedFilter 'branch' has field_name '{field_name}', "
            rf"which reaches {reached.__qualname__}, but its target FilterSet Child is "
            rf"keyed on {child_model.__qualname__}\."
        ),
    ):
        parent.get_filters()


def test_branch_whose_target_set_declares_no_model_is_refused() -> None:
    """A target set with no ``Meta.model`` has no rows to correlate, so the expansion refuses it."""
    child = type("Child", (FilterSet,), {"name": CharFilter(field_name="name")})
    parent = type(
        "Parent",
        (FilterSet,),
        {
            "branch": RelatedFilter(child, field_name="shelf"),
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Book, "fields": {"id": ["exact"]}},
            ),
        },
    )
    with pytest.raises(
        ConfigurationError,
        match=r"which reaches Shelf, but its target FilterSet Child declares no Meta\.model\.",
    ):
        parent.get_filters()


@pytest.mark.parametrize(
    ("parent_model", "field_name", "child_model"),
    [
        (library_models.Book, "shelf", library_models.Shelf),
        (library_models.RepairTicket, "venue", library_models.OpenVenue),
        (library_models.BranchSignage, "branch", library_models.Branch),
        (library_models.BranchSignage, "branch", library_models.ProxyBranch),
        (library_models.RepairTicket, "venue", library_models.LendingDesk),
        (library_models.RepairTicket, "venue", library_models.SelfServeDesk),
        (library_models.VenueSponsor, "venues", library_models.LendingDesk),
        (library_models.SelfServeDesk, "lendingdesk_ptr", library_models.Venue),
    ],
    ids=[
        "the-target",
        "proxy-of-the-target",
        "concrete-model-of-a-proxy-target",
        "sibling-proxy-of-a-proxy-target",
        "mti-child",
        "mti-grandchild",
        "mti-child-across-a-many-to-many",
        "mti-ancestor-across-a-forward-link",
    ],
)
def test_branch_whose_target_set_model_the_relation_correlates_expands(
    parent_model: type[django_models.Model],
    field_name: str,
    child_model: type[django_models.Model],
) -> None:
    """The target, a proxy on its table, an MTI descendant, or a forward link's MTI ancestor expands."""
    parent = _branch_parent(parent_model, field_name, child_model)
    assert "branch__id" in parent.get_filters()


@pytest.mark.django_db
def test_consumer_qs_override_runs_inside_a_logical_arm() -> None:
    """A ``FilterSet.qs`` override (django-filter's seam) shapes a logical arm as it does the root.

    The override keeps only worn shelves when the input names ``worn_only``; a
    ``worn_only`` filter that itself returns its queryset unchanged still makes
    ``not: { worn_only }`` the complement of the worn shelves.
    """

    class WornOnlyShelfFilter(FilterSet):
        worn_only = CharFilter(method="keep_all")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def keep_all(
            self,
            queryset: QuerySet[library_models.Shelf],
            _name: str,
            _value: object,
        ) -> QuerySet[library_models.Shelf]:
            return queryset

        @property
        @override
        def qs(self) -> QuerySet[library_models.Shelf]:
            rows = super().qs
            if self.form.cleaned_data.get("worn_only"):
                rows = rows.filter(condition="worn")
            return rows

    WornOnlyShelfFilter.get_filters()
    branch = library_models.Branch.objects.create(name="North", city="Boston")
    good = library_models.Shelf.objects.create(
        code="G",
        topic="t",
        branch=branch,
        condition="good",
    )
    library_models.Shelf.objects.create(code="W", topic="t", branch=branch, condition="worn")

    kept = _applied(
        WornOnlyShelfFilter,
        {"not_": {"worn_only": "y"}},
        library_models.Shelf.objects.all(),
    )

    assert kept == {saved_pk(good)}


def _book_genre_book_parent(*, customize_child: bool) -> type[FilterSet]:
    """``BookParent.genres -> GenreChild.books -> BookChild``; ``GenreChild`` declares an excluding leaf.

    With ``customize_child`` the genre set overrides ``__init__``, so every
    expanded genre leaf is a ``ProjectedChildFilter``; without it the excluding
    leaf expands as a plain copy walking both hops.
    """

    class BookChild(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    def filter_named(
        _self: FilterSet,
        queryset: QuerySet[library_models.Genre],
        _name: str,
        value: object,
    ) -> QuerySet[library_models.Genre]:
        return queryset.filter(name=value)

    attrs: dict[str, object] = {
        "books": RelatedFilter(BookChild, field_name="books"),
        "without_book_titled": CharFilter(field_name="books__title", exclude=True),
        "subtitle_missing": BooleanFilter(field_name="books__subtitle", lookup_expr="isnull"),
        "named_by_method": CharFilter(field_name="name", method="filter_named", exclude=True),
        "filter_named": filter_named,
        "Meta": type("Meta", (), {"model": library_models.Genre, "fields": {"name": ["exact"]}}),
    }
    if customize_child:

        def _forwarding_init(
            self: FilterSet,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            FilterSet.__init__(self, data=data, queryset=queryset, request=request, prefix=prefix)

        attrs["__init__"] = _forwarding_init
    genre_child = type("GenreChild", (FilterSet,), attrs)

    class BookParent(FilterSet):
        genres = RelatedFilter(genre_child, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    BookParent.get_filters()
    return BookParent


@pytest.mark.parametrize("customize_child", [True, False], ids=["projected", "expanded"])
@pytest.mark.parametrize("leaf", ["genres__without_book_titled", "genres__subtitle_missing"])
def test_child_customization_selects_the_projected_leaf_class(
    leaf: str,
    *,
    customize_child: bool,
) -> None:
    """The copied leaf class records child customization, which the wire cannot distinguish.

    ``test_relation_authority_worlds_api.py`` owns the exclusion/null-extension payloads.
    """
    _hide(library_models.Book, circulation_status="repair")
    _hide(library_models.Genre, name__startswith="secret")
    parent = _book_genre_book_parent(customize_child=customize_child)
    assert isinstance(parent.get_filters()[leaf], ProjectedChildFilter) is customize_child


def _own_filter_sets() -> dict[type[django_models.Model], type[FilterSet]]:
    """Filter sets whose leaves hold a ``filter`` of their own, keyed by root model.

    ``Loan`` reaches ``Patron`` and ``Book`` to-one; ``Shelf`` reaches ``Book``
    to-many and declares ``book_titled`` on the same path beside the branch;
    ``Genre`` reaches ``Book`` many-to-many; ``Book`` filters its own column.
    """
    _register_plain_types(library_models.Patron)

    class PatronChild(FilterSet):
        email = _OwnFilterCharFilter("email")

        class Meta:
            model = library_models.Patron
            fields = []

    class BookChild(FilterSet):
        titled = _OwnFilterCharFilter("title")
        not_titled = _OwnFilterCharFilter("title", exclude=True)
        subtitle_missing = _OwnFilterBooleanFilter("subtitle", lookup_expr="isnull")

        class Meta:
            model = library_models.Book
            fields = []

    class LoanParent(FilterSet):
        patron = RelatedFilter(PatronChild, field_name="patron")
        book = RelatedFilter(BookChild, field_name="book")

        class Meta:
            model = library_models.Loan
            fields = []

    class ShelfParent(FilterSet):
        books = RelatedFilter(BookChild, field_name="books")
        book_titled = _OwnFilterCharFilter("books__title")

        class Meta:
            model = library_models.Shelf
            fields = []

    class GenreParent(FilterSet):
        books = RelatedFilter(BookChild, field_name="books")

        class Meta:
            model = library_models.Genre
            fields = []

    return {
        library_models.Loan: LoanParent,
        library_models.Shelf: ShelfParent,
        library_models.Genre: GenreParent,
        library_models.Book: BookChild,
    }


class _OwnFilterRow(NamedTuple):
    """One own callable's root, declared name and projection class."""

    root: type[django_models.Model]
    filter_input: dict[str, object]
    projected: bool


_OWN_FILTER_ROWS = {
    "child-to-one": _OwnFilterRow(library_models.Loan, {"patron__email": "p1@x"}, projected=True),
    "child-to-one-over-a-hidden-row": _OwnFilterRow(
        library_models.Loan,
        {"book__titled": "x"},
        projected=True,
    ),
    "child-to-many": _OwnFilterRow(library_models.Shelf, {"books__titled": "x"}, projected=True),
    "parent-declared-beside-the-branch": _OwnFilterRow(
        library_models.Shelf,
        {"book_titled": "x"},
        projected=False,
    ),
    "child-to-one-exclude": _OwnFilterRow(
        library_models.Loan,
        {"book__not_titled": "x"},
        projected=True,
    ),
    "child-to-many-exclude": _OwnFilterRow(
        library_models.Shelf,
        {"books__not_titled": "x"},
        projected=True,
    ),
    "child-to-many-isnull-null-extends": _OwnFilterRow(
        library_models.Shelf,
        {"books__subtitle_missing": True},
        projected=True,
    ),
    "child-many-to-many-exclude": _OwnFilterRow(
        library_models.Genre,
        {"books__not_titled": "x"},
        projected=True,
    ),
    "child-many-to-many-isnull-null-extends": _OwnFilterRow(
        library_models.Genre,
        {"books__subtitle_missing": True},
        projected=True,
    ),
    "flat": _OwnFilterRow(library_models.Book, {"titled": "x"}, projected=False),
}


@pytest.mark.parametrize("shape", list(_OWN_FILTER_ROWS))
def test_instance_owned_filter_templates_keep_their_projection_class(shape: str) -> None:
    """An instance-owned child callable becomes projected; an own filter on the parent does not.

    Payloads, exclusion and null extension are owned by
    ``examples/fakeshop/test_query/test_projected_owned_filters_api.py::test_own_callable_keeps_its_owner_exclusion_and_null_extension_on_each_executor``.
    """
    _hide(library_models.Book, circulation_status="repair")
    sets = _own_filter_sets()
    row = _OWN_FILTER_ROWS[shape]
    filterset = sets[row.root]
    leaf = filterset.get_filters()[next(iter(row.filter_input))]
    assert isinstance(leaf, ProjectedChildFilter) is row.projected


class _RawOwnFilterGlobalIDFilter(GlobalIDFilter):
    """A ``GlobalIDFilter`` whose ``__init__`` stores its own ``filter``, binding the raw value."""

    def __init__(self, field_name: str) -> None:
        super().__init__(field_name=field_name)
        self.filter = self._raw_filter

    def _raw_filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        return qs.filter(title=value)


class _DecodingOwnFilterGlobalIDFilter(GlobalIDFilter):
    """A ``GlobalIDFilter`` whose ``__init__`` stores its own ``filter``, delegating to the decode."""

    def __init__(self, field_name: str) -> None:
        super().__init__(field_name=field_name)
        self.filter = self._decoding_filter

    def _decoding_filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        return GlobalIDFilter.filter(self, qs, value)


def _book_ids_by_raw_title(
    queryset: QuerySet[library_models.Book],
    _name: str,
    value: object,
) -> QuerySet[library_models.Book]:
    """A ``method=`` body binding a GlobalID filter's value undecoded."""
    return queryset.filter(title=value)


def _global_id_child(kind: str) -> GlobalIDFilter:
    """The ``gid`` filter of a ``Book`` child set: a ``method=``, an own ``filter``, or plain."""
    if kind == "method":
        return GlobalIDFilter(field_name="id", method=_book_ids_by_raw_title)
    if kind == "own-raw":
        return _RawOwnFilterGlobalIDFilter("id")
    if kind == "own-decoding":
        return _DecodingOwnFilterGlobalIDFilter("id")
    return GlobalIDFilter(field_name="id")


@pytest.mark.parametrize(
    "kind",
    [
        "method",
        "own-raw",
        "own-decoding",
        "plain",
    ],
)
def test_global_id_child_callables_select_the_projected_filter_class(
    kind: str,
) -> None:
    """Only private metadata or callback observations remain here.

    Live sibling: ``examples/fakeshop/test_query/test_projected_owned_filters_api.py``.
    """
    _register_plain_types(library_models.Book)

    class BookChild(FilterSet):
        gid = _global_id_child(kind)

        class Meta:
            model = library_models.Book
            fields = []

    class ShelfParent(FilterSet):
        books = RelatedFilter(BookChild, field_name="books")

        class Meta:
            model = library_models.Shelf
            fields = []

    assert isinstance(ShelfParent.get_filters()["books__gid"], ProjectedChildFilter) is (
        kind != "plain"
    )


def _desk_ticket_parent() -> type[FilterSet]:
    """``TicketParent.desk`` targets ``Venue`` (``field_name="venue"``) with a child set on ``LendingDesk``.

    ``LendingDesk`` is a multi-table-inheritance child of ``Venue``, so the
    expanded ``desk__window_count`` leaf's path resolves only on the child
    set's model, never on the parent's ``venue`` relation.
    """

    class DeskChild(FilterSet):
        class Meta:
            model = library_models.LendingDesk
            fields = {"window_count": ["exact"]}

    class TicketParent(FilterSet):
        desk = RelatedFilter(DeskChild, field_name="venue")

        class Meta:
            model = library_models.RepairTicket
            fields = {"code": ["exact"]}

    TicketParent.get_filters()
    return TicketParent


def test_omitted_mti_child_leaf_runs_no_visibility_hook() -> None:
    """An empty child value derives no hook; HTTP owns ancestor/descendant payloads and SQL."""
    calls: list[object] = []

    def get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.LendingDesk],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.LendingDesk]:
        calls.append(info)
        return queryset.exclude(name__startswith="secret")

    type(
        "LendingDeskHidingType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.LendingDesk}),
            "get_queryset": classmethod(get_queryset),
        },
    )
    parent = _desk_ticket_parent()
    parent.apply_sync(
        {"desk__window_count": None},
        library_models.RepairTicket.objects.all(),
        _make_info(),
    )
    assert calls == []


class _GateProbeRequest(HttpRequest):
    """An ``HttpRequest`` carrying the probe slots the gate tests hang on it."""

    denied: bool
    fired: set[str]


def test_a_customized_child_walking_its_branch_expands_as_a_projected_leaf() -> None:
    """Only private metadata or callback observations remain here.

    Live sibling: ``examples/fakeshop/test_query/test_filter_consumer_contracts_api.py``.
    """
    _register_plain_types(library_models.Genre, library_models.Book)

    class BookChild(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    class GenreChild(FilterSet):
        books = RelatedFilter(BookChild, field_name="books")
        named = CharFilter(field_name="books__title")

        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

        def check_books_permission(self, request: object) -> None:
            if getattr(request, "denied", False):
                raise GraphQLError("books denied")

    class BookParent(FilterSet):
        genres = RelatedFilter(GenreChild, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    BookParent.get_filters()
    assert isinstance(BookParent.get_filters()["genres__named"], ProjectedChildFilter)


def _gate(label: str) -> Callable[[FilterSet, _GateProbeRequest], None]:
    """A ``check_*_permission`` that records ``label`` on the request it is handed."""

    def check(_self: FilterSet, request: _GateProbeRequest) -> None:
        request.fired.add(label)

    return check


def _fired_gates(
    filterset: type[FilterSet],
    filter_input: object,
    root: QuerySet[django_models.Model],
) -> set[str]:
    """The labels of every gate ``filterset.apply_sync`` fires for ``filter_input``."""
    request = _GateProbeRequest()
    request.fired = set()
    list(filterset.apply_sync(filter_input, root, _make_info(request)))
    return request.fired


def _gate_recording_branch_parent(branch_attr: str) -> type[FilterSet]:
    """``BranchParent.<branch_attr>`` over ``shelves``; every set records each gate it fires."""
    _register_plain_types(library_models.Shelf)

    class ShelfChild(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"id": ["exact", "isnull"], "code": ["exact", "isnull"]}

        check_id_permission = _gate("Shelf.id")
        check_code_permission = _gate("Shelf.code")

    def code_by_method(
        _self: FilterSet,
        queryset: QuerySet[library_models.Branch],
        _name: str,
        value: object,
    ) -> QuerySet[library_models.Branch]:
        return queryset.filter(shelves__code=value)

    declared = {
        "has_code": CharFilter(field_name="shelves__code"),
        "not_code": CharFilter(field_name="shelves__code", exclude=True),
        "code_missing": BooleanFilter(field_name="shelves__code", lookup_expr="isnull"),
        "no_shelf": BooleanFilter(field_name="shelves", lookup_expr="isnull"),
        "shelf_is": NumberFilter(field_name="shelves"),
        "code_by_method": CharFilter(field_name="shelves__code", method="filter_code"),
        "code_by_own_filter": _OwnFilterCharFilter("shelves__code"),
    }
    attrs = {
        branch_attr: RelatedFilter(ShelfChild, field_name="shelves"),
        **declared,
        "filter_code": code_by_method,
        f"check_{branch_attr}_permission": _gate(f"Branch.{branch_attr}"),
        "Meta": type("Meta", (), {"model": library_models.Branch, "fields": {"name": ["exact"]}}),
    }
    for name in declared:
        attrs[f"check_{name}_permission"] = _gate(f"Branch.{name}")
    parent = type("BranchParent", (FilterSet,), attrs)
    parent.get_filters()
    return parent


@pytest.mark.django_db
@pytest.mark.parametrize(
    "branch_attr",
    ["shelves", "visible_shelves"],
    ids=["same-name", "renamed"],
)
@pytest.mark.parametrize(
    ("leaf", "value", "twin"),
    [
        ("has_code", "x", {"code": "x"}),
        ("not_code", "x", {"code": "x"}),
        ("code_missing", True, {"code": {"is_null": True}}),
        ("no_shelf", True, {"id": {"is_null": True}}),
        ("shelf_is", 1, {"id": 1}),
    ],
    ids=[
        "positive",
        "exclude",
        "isnull",
        "key-isnull",
        "key-membership",
    ],
)
def test_declared_walked_leaf_fires_exactly_its_nested_twins_gates_plus_its_own(
    branch_attr: str,
    leaf: str,
    value: object,
    twin: dict[str, object],
) -> None:
    """A declared leaf walking a branch fires the twin's branch AND target field gates, plus its own."""
    parent = _gate_recording_branch_parent(branch_attr)
    root = library_models.Branch.objects.all()
    flat = _fired_gates(parent, {leaf: value}, root)
    nested = _fired_gates(parent, {branch_attr: twin}, root)
    assert nested
    assert flat == nested | {f"Branch.{leaf}"}


@pytest.mark.django_db
@pytest.mark.parametrize("leaf", ["code_by_method", "code_by_own_filter"], ids=["method", "own"])
def test_parent_method_filter_fires_only_its_own_gate(leaf: str) -> None:
    """A parent filter holding a ``filter`` of its own owns its scoping, walking no branch or twin gate.

    ``method=`` installs one; ``code_by_own_filter``'s ``__init__`` stores another.
    """
    parent = _gate_recording_branch_parent("shelves")
    fired = _fired_gates(parent, {leaf: "x"}, library_models.Branch.objects.all())
    assert fired == {f"Branch.{leaf}"}


def _gate_recording_genre_parent(branch_attr: str, *, customize_child: bool) -> type[FilterSet]:
    """``BookParent.<branch_attr>`` over ``genres``; every set records each gate it fires.

    ``GenreChild`` declares ``named`` and ``title_missing`` walking its own
    ``books`` branch beside its generated ``name``. When ``customize_child`` it
    overrides ``__init__``, so the parent projects its filters
    (``ProjectedChildFilter``) instead of rebinding them.
    """
    _register_plain_types(library_models.Genre, library_models.Book)

    class BookChild(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

        check_title_permission = _gate("Book.title")

    class GenreChild(FilterSet):
        books = RelatedFilter(BookChild, field_name="books")
        named = CharFilter(field_name="books__title")
        title_missing = BooleanFilter(field_name="books__title", lookup_expr="isnull")

        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

        check_books_permission = _gate("Genre.books")
        check_named_permission = _gate("Genre.named")
        check_title_missing_permission = _gate("Genre.title_missing")
        check_name_permission = _gate("Genre.name")

    class CustomizedGenreChild(GenreChild):
        def __init__(
            self,
            data: QueryDict | dict[str, object] | None = None,
            queryset: QuerySet[django_models.Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

    attrs: dict[str, object] = {
        branch_attr: RelatedFilter(
            CustomizedGenreChild if customize_child else GenreChild,
            field_name="genres",
        ),
        f"check_{branch_attr}_permission": _gate(f"Book.{branch_attr}"),
        "Meta": type("Meta", (), {"model": library_models.Book, "fields": {"title": ["exact"]}}),
    }
    return type("BookParent", (FilterSet,), attrs)


#: Each ``GenreChild`` leaf of ``_gate_recording_genre_parent``: its value and the
#: gates it fires supplied on ``GenreChild``, its own and its walk's.
_GENRE_CHILD_LEAVES = {
    "walking": ("named", "x", {"Genre.named", "Genre.books", "Book.title"}),
    "isnull-walking": (
        "title_missing",
        True,
        {"Genre.title_missing", "Genre.books", "Book.title"},
    ),
    "plain": ("name", "x", {"Genre.name"}),
}


@pytest.mark.django_db
@pytest.mark.parametrize("leaf_case", list(_GENRE_CHILD_LEAVES))
@pytest.mark.parametrize("customize_child", [True, False], ids=["projected", "expanded"])
@pytest.mark.parametrize("branch_attr", ["genres", "aliased_genres"], ids=["same-name", "renamed"])
def test_child_set_leaf_reached_flat_fires_exactly_its_nested_twins_gates(
    branch_attr: str,
    leaf_case: str,
    *,
    customize_child: bool,
) -> None:
    """A child set's leaf reached flat fires the branch gate, the child filter's gate and its own walk's.

    Projected (the child overrides ``__init__``) or expanded as a plain copy,
    under a branch named as its relation or renamed (``aliased_genres`` over
    ``genres``, whose flat key spells no relation), the flat leaf fires the
    same gates as ``<branch>: {<child filter>: ...}``.
    """
    child_name, value, child_gates = _GENRE_CHILD_LEAVES[leaf_case]
    parent = _gate_recording_genre_parent(branch_attr, customize_child=customize_child)
    leaf = f"{branch_attr}__{child_name}"
    assert isinstance(parent.get_filters()[leaf], ProjectedChildFilter) is customize_child
    root = library_models.Book.objects.all()
    expected = {f"Book.{branch_attr}", *child_gates}
    assert _fired_gates(parent, {branch_attr: {child_name: value}}, root) == expected
    assert _fired_gates(parent, {leaf: value}, root) == expected


def _rekeyed(
    parent: type[FilterSet],
    *,
    rename: bool,
    fresh: bool,
    branch_attr: str | None = None,
) -> type[FilterSet]:
    """``parent`` under a ``get_filters()`` override reshaping its expanded child leaves.

    Each ``_GENRE_CHILD_LEAVES`` copy of ``branch_attr`` (``parent``'s one
    branch when ``None``) is held under ``alias_<child name>`` when
    ``rename``, and every filter is a deep copy of the one ``super()`` returns
    when ``fresh``.
    """
    if branch_attr is None:
        (branch_attr,) = parent.related_filters
    aliases = {
        f"{branch_attr}__{child_name}": f"alias_{child_name}"
        for child_name, _value, _gates in _GENRE_CHILD_LEAVES.values()
    }

    class Rekeyed(parent):
        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            return OrderedDict(
                (
                    aliases.get(name, name) if rename else name,
                    copy.deepcopy(filter_instance) if fresh else filter_instance,
                )
                for name, filter_instance in super().get_filters().items()
            )

    return Rekeyed


@pytest.mark.django_db
@pytest.mark.parametrize("leaf_case", list(_GENRE_CHILD_LEAVES))
@pytest.mark.parametrize("customize_child", [True, False], ids=["projected", "expanded"])
@pytest.mark.parametrize("branch_attr", ["genres", "aliased_genres"], ids=["same-name", "renamed"])
@pytest.mark.parametrize(
    ("rename", "fresh"),
    [(False, True), (True, True), (True, False)],
    ids=["deep-copies", "deep-copies-rekeyed", "rekeyed"],
)
def test_a_get_filters_override_keeps_each_copy_gated_as_its_nested_twin(
    branch_attr: str,
    leaf_case: str,
    *,
    customize_child: bool,
    rename: bool,
    fresh: bool,
) -> None:
    """Copies a ``get_filters()`` override deep-copies or holds under keys of its own keep their gates.

    Each copy carries the child filter it stands for, so whatever key holds it
    and however often it is copied, it fires the branch gate and the child
    filter's gates, as ``<branch>: {<child filter>: ...}`` does.
    """
    child_name, value, child_gates = _GENRE_CHILD_LEAVES[leaf_case]
    parent = _rekeyed(
        _gate_recording_genre_parent(branch_attr, customize_child=customize_child),
        rename=rename,
        fresh=fresh,
    )
    leaf = f"alias_{child_name}" if rename else f"{branch_attr}__{child_name}"
    assert isinstance(parent.get_filters()[leaf], ProjectedChildFilter) is customize_child
    root = library_models.Book.objects.all()
    expected = {f"Book.{branch_attr}", *child_gates}
    assert _fired_gates(parent, {branch_attr: {child_name: value}}, root) == expected
    assert _fired_gates(parent, {leaf: value}, root) == expected


@pytest.mark.django_db
@pytest.mark.parametrize("leaf_case", list(_GENRE_CHILD_LEAVES))
@pytest.mark.parametrize("customize_child", [True, False], ids=["projected", "expanded"])
@pytest.mark.parametrize("branch_attr", ["genres", "aliased_genres"], ids=["same-name", "renamed"])
def test_a_leaf_reached_flat_across_two_hops_fires_its_fully_nested_twins_gates(
    branch_attr: str,
    leaf_case: str,
    *,
    customize_child: bool,
) -> None:
    """``lent__<branch>__<child filter>`` fires both branch gates and the child filter's gates.

    ``LoanParent.lent`` hops over ``book`` under a name of its own and expands
    ``BookParent``'s copy again, so the flat leaf answers as
    ``lent: {<branch>: {<child filter>: ...}}`` does.
    """
    child_name, value, child_gates = _GENRE_CHILD_LEAVES[leaf_case]
    book_parent = _gate_recording_genre_parent(branch_attr, customize_child=customize_child)
    _register_plain_types(library_models.Loan)

    class LoanParent(FilterSet):
        lent = RelatedFilter(book_parent, field_name="book")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

        check_lent_permission = _gate("Loan.lent")

    root = library_models.Loan.objects.all()
    expected = {"Loan.lent", f"Book.{branch_attr}", *child_gates}
    nested = {"lent": {branch_attr: {child_name: value}}}
    assert _fired_gates(LoanParent, nested, root) == expected
    flat = {f"lent__{branch_attr}__{child_name}": value}
    assert _fired_gates(LoanParent, flat, root) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("borrower_branch", "borrower_gates"),
    [(False, {"Borrower.aliased"}), (True, {"Borrower.aliased", "Borrower.genres"})],
    ids=["no-branch", "branch-to-another-set"],
)
def test_a_borrowed_expanded_copy_is_its_borrowers_own_filter(
    *,
    borrower_branch: bool,
    borrower_gates: set[str],
) -> None:
    """A set declaring another set's expanded copy gates it as its own filter; the donor keeps its gates.

    ``Borrower.aliased`` is the object ``BookParent.get_filters()`` holds as
    ``genres__named``. ``Borrower`` expands no ``genres`` branch into
    ``GenreChild`` (it declares none, or one into another set), so the copy
    fires its own gate and the walk of its ``field_name`` on ``Borrower``,
    never ``GenreChild``'s. ``Borrower`` declares a deep copy of it, so the
    donor's object keeps its own records and ``BookParent``'s flat leaf still
    fires its nested twin's gates.
    """
    donor = _gate_recording_genre_parent("genres", customize_child=False)
    borrowed = donor.get_filters()["genres__named"]
    donor_provenance = filter_generation_provenance(borrowed)
    donor_expansion = _expansion_record(borrowed)
    assert donor_provenance is not None
    assert donor_expansion is not None

    class OtherGenreChild(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    attrs: dict[str, object] = {
        "aliased": borrowed,
        "check_aliased_permission": _gate("Borrower.aliased"),
        "check_genres_permission": _gate("Borrower.genres"),
        "Meta": type("Meta", (), {"model": library_models.Book, "fields": {"title": ["exact"]}}),
    }
    if borrower_branch:
        attrs["genres"] = RelatedFilter(OtherGenreChild, field_name="genres")
    borrower = type("Borrower", (FilterSet,), attrs)
    aliased = borrower.get_filters()["aliased"]
    assert aliased is not borrowed
    assert aliased is borrower.declared_filters["aliased"]
    assert _expansion_record(aliased) is donor_expansion
    assert filter_generation_provenance(borrowed) is donor_provenance
    assert _expansion_record(borrowed) is donor_expansion
    assert donor.get_filters()["genres__named"] is borrowed

    root = library_models.Book.objects.all()
    assert _fired_gates(borrower, {"aliased": "x"}, root) == borrower_gates
    donor_gates = {
        "Book.genres",
        "Genre.named",
        "Genre.books",
        "Book.title",
    }
    assert _fired_gates(donor, {"genres": {"named": "x"}}, root) == donor_gates
    assert _fired_gates(donor, {"genres__named": "x"}, root) == donor_gates


@pytest.mark.django_db
def test_a_borrowed_copy_reached_through_a_branch_is_gated_as_its_borrowers_own_filter() -> None:
    """A child set's borrowed copy reached flat fires the gates ``lent: {aliased: ...}`` fires.

    ``BorrowerChild.aliased`` is the object ``BookParent.get_filters()`` holds as
    ``genres__named``; ``BorrowerChild`` expands no ``genres`` branch, so the copy
    is its own filter there. ``LoanParent.lent`` (over ``book``) expands it again:
    the flat leaf fires the branch gate and the borrower's own gate, never the
    donor's ``GenreChild`` gates, as the nested spelling does.
    """
    donor = _gate_recording_genre_parent("genres", customize_child=False)
    borrowed = donor.get_filters()["genres__named"]
    _register_plain_types(library_models.Loan)

    class BorrowerChild(FilterSet):
        aliased = borrowed

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

        check_aliased_permission = _gate("BorrowerChild.aliased")

    class LoanParent(FilterSet):
        lent = RelatedFilter(BorrowerChild, field_name="book")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

        check_lent_permission = _gate("Loan.lent")

    root = library_models.Loan.objects.all()
    expected = {"Loan.lent", "BorrowerChild.aliased"}
    assert _fired_gates(LoanParent, {"lent": {"aliased": "x"}}, root) == expected
    assert _fired_gates(LoanParent, {"lent__aliased": "x"}, root) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "borrower_branch",
    [False, True],
    ids=["no-branch", "branch-to-another-set"],
)
def test_a_borrowed_projected_copy_is_refused_where_its_branch_is_not_held(
    *,
    borrower_branch: bool,
) -> None:
    """A projected copy declared on a set that does not expand its branch into its child set is refused.

    ``Borrower.aliased`` is the ``ProjectedChildFilter`` ``BookParent.get_filters()``
    holds as ``genres__named``: it runs ``CustomizedGenreChild.named`` across the
    ``genres`` hop inside a child set instance, which ``Borrower`` lacks (it
    declares no ``genres`` branch, or one into another set), so the table
    publishing it is a ``ConfigurationError`` naming the remedy. The donor's
    object keeps its records and its flat leaf its nested twin's gates.
    """
    donor = _gate_recording_genre_parent("genres", customize_child=True)
    borrowed = donor.get_filters()["genres__named"]
    assert isinstance(borrowed, ProjectedChildFilter)
    donor_provenance = filter_generation_provenance(borrowed)
    donor_expansion = _expansion_record(borrowed)

    class OtherGenreChild(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    attrs: dict[str, object] = {
        "aliased": borrowed,
        "Meta": type("Meta", (), {"model": library_models.Book, "fields": {"title": ["exact"]}}),
    }
    if borrower_branch:
        attrs["genres"] = RelatedFilter(OtherGenreChild, field_name="genres")
    borrower = type("Borrower", (FilterSet,), attrs)
    with pytest.raises(ConfigurationError) as exc_info:
        borrower.get_filters()
    message = str(exc_info.value)
    assert "Borrower: filter 'aliased' is a projected copy of" in message
    assert "CustomizedGenreChild.named expanded through a 'genres' branch" in message
    assert "declares no 'genres' RelatedFilter into" in message
    assert "Declare that RelatedFilter, or declare a filter of this set's own." in message

    assert filter_generation_provenance(borrowed) is donor_provenance
    assert _expansion_record(borrowed) is donor_expansion
    root = library_models.Book.objects.all()
    donor_gates = {
        "Book.genres",
        "Genre.named",
        "Genre.books",
        "Book.title",
    }
    assert _fired_gates(donor, {"genres": {"named": "x"}}, root) == donor_gates
    assert _fired_gates(donor, {"genres__named": "x"}, root) == donor_gates


@pytest.mark.django_db
def test_a_projected_copy_publishes_where_its_branch_is_held() -> None:
    """A set expanding the copy's branch into its child set holds a borrowed projected copy.

    ``Borrower`` declares ``genres`` into the donor's own child set, so
    ``aliased`` runs as ``genres: {named: ...}`` and fires its gates; a subclass
    of the donor keeping the inherited branch publishes its own projected copies.
    """
    donor = _gate_recording_genre_parent("genres", customize_child=True)
    borrowed = donor.get_filters()["genres__named"]
    child = donor.related_filters["genres"].filterset
    borrower = type(
        "Borrower",
        (FilterSet,),
        {
            "aliased": borrowed,
            "genres": RelatedFilter(child, field_name="genres"),
            "check_aliased_permission": _gate("Borrower.aliased"),
            "check_genres_permission": _gate("Borrower.genres"),
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Book, "fields": {"title": ["exact"]}},
            ),
        },
    )
    assert isinstance(borrower.get_filters()["aliased"], ProjectedChildFilter)
    root = library_models.Book.objects.all()
    child_gates = {
        "Borrower.genres",
        "Genre.named",
        "Genre.books",
        "Book.title",
    }
    assert _fired_gates(borrower, {"aliased": "x"}, root) == {"Borrower.aliased", *child_gates}
    assert _fired_gates(borrower, {"genres": {"named": "x"}}, root) == child_gates

    subclass = type("BookParentSubclass", (donor,), {})
    assert isinstance(subclass.get_filters()["genres__named"], ProjectedChildFilter)
    donor_gates = {
        "Book.genres",
        "Genre.named",
        "Genre.books",
        "Book.title",
    }
    assert _fired_gates(subclass, {"genres__named": "x"}, root) == donor_gates


def _real_shelf_child() -> type[FilterSet]:
    """``ShelfChild``, recording each ``_GENRE_CHILD_LEAVES`` and key gate."""
    _register_plain_types(library_models.Shelf)
    gates = {
        f"check_{child_name}_permission": _gate(f"Shelf.{child_name}")
        for child_name, _value, _gates in _GENRE_CHILD_LEAVES.values()
    }
    return type(
        "ShelfChild",
        (FilterSet,),
        {
            **gates,
            "check_id_permission": _gate("Shelf.id"),
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Shelf, "fields": {"code": ["exact"]}},
            ),
        },
    )


@pytest.mark.django_db
@pytest.mark.parametrize("leaf_case", list(_GENRE_CHILD_LEAVES))
@pytest.mark.parametrize("customize_child", [True, False], ids=["projected", "expanded"])
@pytest.mark.parametrize(
    ("rename", "fresh"),
    [
        (False, False),
        (False, True),
        (True, True),
        (True, False),
    ],
    ids=[
        "published",
        "deep-copies",
        "deep-copies-rekeyed",
        "rekeyed",
    ],
)
def test_a_flat_copy_named_like_another_branchs_relation_fires_only_its_nested_twins_gates(
    leaf_case: str,
    *,
    customize_child: bool,
    rename: bool,
    fresh: bool,
) -> None:
    """``shelf__<child filter>`` beside ``real_shelf`` over ``shelf`` fires no ``real_shelf`` gate.

    ``BookParent.shelf`` is a branch over ``genres``; ``real_shelf`` declares
    the ``shelf`` relation. The flat copy's key is a name, not an ORM path, so
    its first segment names no hop of ``real_shelf``: flat and nested fire the
    same gates, held as published or under a ``get_filters()`` override. No gate
    from the unrelated ``ShelfChild`` branch is called.
    """
    child_name, value, child_gates = _GENRE_CHILD_LEAVES[leaf_case]
    collision = type(
        "Collision",
        (_gate_recording_genre_parent("shelf", customize_child=customize_child),),
        {
            "real_shelf": RelatedFilter(_real_shelf_child(), field_name="shelf"),
            "check_real_shelf_permission": _gate("Book.real_shelf"),
        },
    )
    parent = (
        _rekeyed(collision, rename=rename, fresh=fresh, branch_attr="shelf")
        if rename or fresh
        else collision
    )
    leaf = f"alias_{child_name}" if rename else f"shelf__{child_name}"
    assert isinstance(parent.get_filters()[leaf], ProjectedChildFilter) is customize_child
    root = library_models.Book.objects.all()
    expected = {"Book.shelf", *child_gates}
    assert _fired_gates(parent, {"shelf": {child_name: value}}, root) == expected
    assert _fired_gates(parent, {leaf: value}, root) == expected


@pytest.mark.django_db
def test_a_declared_filter_named_like_another_branchs_relation_fires_only_its_own_gate() -> None:
    """``shelf = CharFilter(field_name="title")`` beside ``real_shelf`` over ``shelf`` walks no hop.

    Its gate path is its name, never read as the ``shelf`` relation, so it fires
    ``check_shelf_permission`` alone and calls no gate from the unrelated ``ShelfChild``
    branch. Reached flat through ``LoanParent.lent`` it
    fires the gates ``lent: {shelf: ...}`` fires.
    """
    parent = type(
        "PlainParent",
        (FilterSet,),
        {
            "shelf": CharFilter(field_name="title"),
            "real_shelf": RelatedFilter(_real_shelf_child(), field_name="shelf"),
            "check_shelf_permission": _gate("Book.shelf"),
            "check_real_shelf_permission": _gate("Book.real_shelf"),
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Book, "fields": {"title": ["exact"]}},
            ),
        },
    )
    root = library_models.Book.objects.all()
    assert _fired_gates(parent, {"shelf": "x"}, root) == {"Book.shelf"}

    _register_plain_types(library_models.Loan, library_models.Book)

    class LoanParent(FilterSet):
        lent = RelatedFilter(parent, field_name="book")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

        check_lent_permission = _gate("Loan.lent")

    loans = library_models.Loan.objects.all()
    expected = {"Loan.lent", "Book.shelf"}
    assert _fired_gates(LoanParent, {"lent": {"shelf": "x"}}, loans) == expected
    assert _fired_gates(LoanParent, {"lent__shelf": "x"}, loans) == expected


@pytest.mark.django_db
@pytest.mark.parametrize("declared", [False, True], ids=["alone", "beside-a-declared-name"])
def test_a_leaf_gating_on_its_field_name_walks_it_where_a_declared_name_spells_it(
    *,
    declared: bool,
) -> None:
    """A leaf that is no declared head walks its ``field_name`` whatever declared name spells it.

    ``by_code``, a ``method=`` filter over ``shelf__code`` a ``get_filters()``
    override adds, gates on its ``field_name``: an ORM path through
    ``real_shelf``, walked alone and beside a declared ``shelf__code`` over
    ``title``, whose gate path is the same string; reached flat through
    ``LoanParent.lent`` it fires the gates ``lent: {by_code: ...}`` fires. The
    declared ``shelf__code`` walks nothing.
    """
    _register_plain_types(library_models.Shelf, library_models.Loan, library_models.Book)

    class CodeShelfChild(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        check_code_permission = _gate("Shelf.code")

    def filter_code(
        _self: FilterSet,
        queryset: QuerySet[library_models.Book],
        _name: str,
        value: object,
    ) -> QuerySet[library_models.Book]:
        return queryset.filter(shelf__code=value)

    attrs: dict[str, object] = {
        "real_shelf": RelatedFilter(CodeShelfChild, field_name="shelf"),
        "filter_code": filter_code,
        "check_real_shelf_permission": _gate("Book.real_shelf"),
        "check_shelf_code_permission": _gate("Book.shelf_code"),
        "Meta": type("Meta", (), {"model": library_models.Book, "fields": {"title": ["exact"]}}),
    }
    if declared:
        attrs["shelf__code"] = CharFilter(field_name="title")
    base = type("CodeParent", (FilterSet,), attrs)

    class CodeParent(base):
        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            filters = super().get_filters()
            filters["by_code"] = CharFilter(field_name="shelf__code", method="filter_code")
            return filters

    root = library_models.Book.objects.all()
    walked = {"Book.shelf_code", "Book.real_shelf", "Shelf.code"}
    assert _fired_gates(CodeParent, {"by_code": "x"}, root) == walked
    if declared:
        assert _fired_gates(CodeParent, {"shelf__code": "x"}, root) == {"Book.shelf_code"}

    class LoanParent(FilterSet):
        lent = RelatedFilter(CodeParent, field_name="book")

        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

        check_lent_permission = _gate("Loan.lent")

    loans = library_models.Loan.objects.all()
    expected = {"Loan.lent", *walked}
    assert _fired_gates(LoanParent, {"lent": {"by_code": "x"}}, loans) == expected
    assert _fired_gates(LoanParent, {"lent__by_code": "x"}, loans) == expected


@pytest.mark.parametrize("how", ["pickle", "deepcopy"])
def test_a_rebound_copy_keeps_the_child_filter_it_copies(how: str) -> None:
    """A rebound copy's ``ChildProjection`` survives ``pickle`` and ``deepcopy`` as a projected one's."""
    template = LoanFilter.get_filters()["book__id"]
    assert not isinstance(template, ProjectedChildFilter)
    record = _expansion_record(template)
    assert record is not None
    assert (record.name, record.branch) == ("id", "book")
    restored = pickle_roundtrip(template) if how == "pickle" else copy.deepcopy(template)
    assert _expansion_record(restored) == record
    assert _expansion_record(LoanFilter.get_filters()["book"]) is None


def test_enum_choice_filter_resolves_to_the_choice_family_profile() -> None:
    """The generated choice ``exact`` class shares ``ChoiceFilter``'s audited family.

    ``EnumChoiceFilter`` only adds the enum-member-is-a-value predicate, so it is an exact
    registry key under the choice profile; without the key a generated to-many choice leaf
    would resolve to no family and lose its row-preserving routing.
    """
    instance = object.__new__(EnumChoiceFilter)
    assert _family_profile_for(instance) is _FILTER_FAMILY_REGISTRY[ChoiceFilter]


def test_generated_choice_exact_over_to_many_path_is_an_eligible_enum_choice_leaf() -> None:
    """A generated to-many choice ``exact`` is an eligible ``EnumChoiceFilter`` leaf."""

    class BranchConditionFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"shelves__condition": ["exact"]}

    leaf = BranchConditionFilter.get_filters()["shelves__condition"]
    assert type(leaf) is EnumChoiceFilter
    snapshot = BranchConditionFilter._expansion_snapshot()
    assert snapshot is not None
    assert snapshot.candidates["shelves__condition"].eligible is True


_TEXT_CHOICE_SINGLE_VALUE_LOOKUPS = (
    "iexact",
    "contains",
    "icontains",
    "startswith",
    "istartswith",
    "endswith",
    "iendswith",
    "regex",
    "iregex",
    "gt",
    "gte",
    "lt",
    "lte",
)


class _ShelfConditionLookupFilter(FilterSet):
    """Every single-value lookup on the blank-admitting ``Shelf.condition`` choice column."""

    class Meta:
        model = library_models.Shelf
        fields = {"condition": ["exact", *_TEXT_CHOICE_SINGLE_VALUE_LOOKUPS]}


def _condition_filter_name(lookup: str) -> str:
    """The form-data key of ``_ShelfConditionLookupFilter``'s ``condition`` ``lookup``."""
    return "condition" if lookup == "exact" else f"condition__{lookup}"


@pytest.mark.parametrize("lookup", ["exact", *_TEXT_CHOICE_SINGLE_VALUE_LOOKUPS])
def test_every_text_choice_lookup_resolves_to_an_enum_member_filter(lookup: str) -> None:
    """A text choice column's single-value lookups are the enum-member filter classes.

    ``exact`` is ``EnumChoiceFilter`` under the choice family and every other single-value
    lookup is ``EnumLookupFilter`` under ``CharFilter``'s scalar family, each an exact registry
    key: without the key a flat to-many leaf over the lookup resolves to no family and is
    unroutable.
    """
    leaf = _ShelfConditionLookupFilter.get_filters()[_condition_filter_name(lookup)]
    if lookup == "exact":
        assert type(leaf) is EnumChoiceFilter
        assert _family_profile_for(leaf) is _FILTER_FAMILY_REGISTRY[ChoiceFilter]
    else:
        assert type(leaf) is EnumLookupFilter
        assert _family_profile_for(leaf) is _FILTER_FAMILY_REGISTRY[CharFilter]


@pytest.mark.parametrize("clone", [copy.deepcopy, pickle_roundtrip])
def test_enum_member_value_survives_copy_and_pickle(clone: Callable[[object], object]) -> None:
    """The marker is matched by type and compared by value, so a copied one still applies.

    A deep copy or a pickle round trip of ``EnumMemberValue("")`` is equal to the original
    and is still applied by the generated filter as the ``''`` predicate.
    """
    cloned = clone(EnumMemberValue(""))
    assert isinstance(cloned, EnumMemberValue)
    assert cloned == EnumMemberValue("")
    leaf = _ShelfConditionLookupFilter.get_filters()["condition__iexact"]
    filtered = leaf.filter(library_models.Shelf.objects.all(), cloned)
    where = filtered.query.where.children
    assert len(where) == 1
    assert isinstance(where[0], Lookup)
    assert read_attr(where[0], "rhs") == ""


def test_visibility_unresolved_model_less_child_names_unresolved() -> None:
    """The pre-publication helper labels an unexpandable model-less child as unresolved.

    Ordinary expansion already rejects a child with no Meta.model, so no schema can
    reach this earlier internal diagnostic. Construction refusal is pinned by
    ``tests/filters/test_sets.py::test_branch_whose_target_set_declares_no_model_is_refused``.
    """

    class OrphanFilter(FilterSet):
        class Meta:
            model = None
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        orphans = RelatedFilter(OrphanFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError) as excinfo:
        BranchFilter._derive_related_visibility_querysets_sync(
            {"orphans": {"code": "x"}},
            info=None,
        )
    assert "<unresolved>" in str(excinfo.value)


_BAD_BRANCH = {"branch": {"name": "bad"}}


_NO_KEYS: list[str] = []


def _arm_error_order_filter(
    mode: str,
    *,
    gated: bool,
    hook_runs: list[str] | None = None,
) -> type[FilterSet]:
    """A shelf set whose ``topic`` and ``branch`` ``name`` reject ``"bad"`` (``NumberFilter``).

    ``BranchType.get_queryset`` is sync for ``"sync"`` and ``"async_sync_hooks"``
    and async-only for ``"async_only_hooks"``, and appends to ``hook_runs`` when
    given; with ``gated`` the set's ``check_topic_permission`` denies every
    request naming ``topic``.
    """
    runs = [] if hook_runs is None else hook_runs

    def _sync_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        runs.append("branch")
        return queryset

    async def _async_visible(
        _cls: type[DjangoType],
        queryset: QuerySet[library_models.Branch],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[library_models.Branch]:
        runs.append("branch")
        return queryset

    type(
        "BranchType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": library_models.Branch}),
            "get_queryset": classmethod(
                _async_visible if mode == "async_only_hooks" else _sync_visible,
            ),
        },
    )

    class BranchByNumber(FilterSet):
        name = NumberFilter(field_name="name")

        class Meta:
            model = library_models.Branch
            fields: dict[str, list[str]] = {}

    class ShelfByNumber(FilterSet):
        branch = RelatedFilter(BranchByNumber, field_name="branch")
        topic = NumberFilter(field_name="topic")

        class Meta:
            model = library_models.Shelf
            fields: dict[str, list[str]] = {}

    if not gated:
        return ShelfByNumber

    class GatedShelfByNumber(ShelfByNumber):
        def check_topic_permission(self, _request: object) -> bool:
            return False

    return GatedShelfByNumber


def _first_filter_error(
    filter_set: type[FilterSet],
    filter_input: dict[str, object],
    mode: str,
) -> tuple[type[BaseException], object, list[str]]:
    """Run ``filter_set`` on ``mode``'s color; return the error's type, code and error keys."""
    filter_set.get_filters()
    base = library_models.Shelf.objects.all()

    def _apply() -> object:
        if mode == "sync":
            return filter_set.apply_sync(filter_input, base, _make_info())
        return asyncio.run(filter_set.apply_async(filter_input, base, _make_info()))

    with pytest.raises(GraphQLError) as excinfo:
        _apply()
    extensions = excinfo.value.extensions or {}
    errors = extensions.get("errors")
    keys = sorted(str(key) for key in errors) if is_dict(errors) else []
    return type(excinfo.value), extensions.get("code"), keys


_ARM_FORM_VERSUS_BRANCH_CASES = [
    pytest.param(
        {"or_": [_BAD_BRANCH, {"topic": "bad"}]},
        ["or_0__branch__name"],
        id="branch-arm-first",
    ),
    pytest.param(
        {"or_": [{"topic": "bad"}, _BAD_BRANCH]},
        ["or_1__branch__name"],
        id="form-arm-first",
    ),
    pytest.param(
        {"or_": [{**_BAD_BRANCH, "topic": "bad"}]},
        ["or_0__branch__name"],
        id="one-arm-both",
    ),
    pytest.param(
        {"and_": [{"topic": "bad"}], "or_": [_BAD_BRANCH]},
        ["or_0__branch__name"],
        id="and-form-or-branch",
    ),
    pytest.param(
        {"or_": [{"topic": "bad", "or_": [_BAD_BRANCH]}]},
        ["or_0__or_0__branch__name"],
        id="nested-arm-branch",
    ),
    pytest.param(
        {"and_": [{"or_": [{"topic": "bad"}, _BAD_BRANCH]}]},
        ["and_0__or_1__branch__name"],
        id="nested-or-in-and",
    ),
    pytest.param(
        {"or_": [{"topic": "bad"}, {"and_": [_BAD_BRANCH]}]},
        ["or_1__and_0__branch__name"],
        id="deeper-branch-later-arm",
    ),
    pytest.param(
        {"not_": _BAD_BRANCH, "topic": "bad"},
        ["not__branch__name"],
        id="not-branch-root-form",
    ),
    pytest.param(
        {"not_": {"topic": "bad"}, "or_": [_BAD_BRANCH]},
        ["or_0__branch__name"],
        id="not-form-or-branch",
    ),
    pytest.param(
        {"not_": {"or_": [{"topic": "bad"}, _BAD_BRANCH]}},
        ["not__or_1__branch__name"],
        id="nested-or-in-not",
    ),
    pytest.param(
        {"topic": "bad", "or_": [_BAD_BRANCH]},
        ["or_0__branch__name"],
        id="root-form-arm-branch",
    ),
    pytest.param(
        {**_BAD_BRANCH, "or_": [{"topic": "bad"}]},
        ["branch__name"],
        id="root-branch-arm-form",
    ),
    pytest.param(
        {"or_": [_BAD_BRANCH, _BAD_BRANCH]},
        ["or_0__branch__name"],
        id="two-branch-arms",
    ),
    pytest.param(
        {"or_": [{**_BAD_BRANCH, "or_": [_BAD_BRANCH]}]},
        ["or_0__branch__name"],
        id="arm-branch-before-its-nested-arm",
    ),
    pytest.param({"or_": [{"topic": "bad"}]}, ["or_0__topic"], id="control-arm-form-alone"),
]


@pytest.mark.django_db
@pytest.mark.parametrize(("filter_input", "keys"), _ARM_FORM_VERSUS_BRANCH_CASES)
@pytest.mark.parametrize("mode", ["sync", "async_sync_hooks", "async_only_hooks"])
def test_an_arm_branch_error_answers_before_any_form_error_on_both_colors(
    filter_input: dict[str, object],
    keys: list[str],
    mode: str,
) -> None:
    """Every arm's related branches derive, in tree order, before any set's form validates.

    Both colors derive the root's and every ``and`` / ``or`` / ``not`` arm's
    ``branch`` before the root form and the arm forms validate (spec-027
    Decision 8, step 3), so an input holding a rejected ``topic`` beside a
    rejected ``branch`` ``name`` answers the branch's ``FILTER_INVALID`` key,
    the first in tree order, on ``apply_sync`` and on ``apply_async`` with a sync
    or an async-only ``BranchType.get_queryset``.
    """
    filter_set = _arm_error_order_filter(mode, gated=False)
    assert _first_filter_error(filter_set, filter_input, mode) == (
        GraphQLError,
        "FILTER_INVALID",
        keys,
    )


_ARM_PERMISSION_VERSUS_BRANCH_CASES = [
    pytest.param(
        {"topic": "1", "or_": [_BAD_BRANCH]},
        ("FILTER_INVALID", ["or_0__branch__name"]),
        id="root-gate-arm-branch",
    ),
    pytest.param(
        {"or_": [{"topic": "1"}, _BAD_BRANCH]},
        ("FILTER_INVALID", ["or_1__branch__name"]),
        id="arm-gate-later-branch",
    ),
    pytest.param(
        {"or_": [{"topic": "1", **_BAD_BRANCH}]},
        ("FILTER_INVALID", ["or_0__branch__name"]),
        id="one-arm-gate-branch",
    ),
    pytest.param(
        {"and_": [{"or_": [{"topic": "1"}]}], "not_": _BAD_BRANCH},
        ("FILTER_INVALID", ["not__branch__name"]),
        id="nested-gate-not-branch",
    ),
    pytest.param({"or_": [{"topic": "1"}]}, (None, _NO_KEYS), id="control-gate-alone"),
]


@pytest.mark.django_db
@pytest.mark.parametrize(("filter_input", "expected"), _ARM_PERMISSION_VERSUS_BRANCH_CASES)
@pytest.mark.parametrize("mode", ["sync", "async_sync_hooks", "async_only_hooks"])
def test_an_arm_branch_error_answers_before_a_permission_denial_on_both_colors(
    filter_input: dict[str, object],
    expected: tuple[str | None, list[str]],
    mode: str,
) -> None:
    """Every arm's related branches derive before the permission pass, on both colors.

    ``check_topic_permission`` denies any ``topic``; each input also holds a
    rejected ``branch`` ``name`` in an arm, whose ``FILTER_INVALID`` answers
    first on ``apply_sync`` and on ``apply_async`` with a sync or an async-only
    ``BranchType.get_queryset`` (spec-027 Decision 8: step 3 before step 5).
    The gate alone answers its denial, a ``GraphQLError`` with no code.
    """
    filter_set = _arm_error_order_filter(mode, gated=True)
    code, keys = expected
    assert _first_filter_error(filter_set, filter_input, mode) == (GraphQLError, code, keys)


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["sync", "async_sync_hooks", "async_only_hooks"])
def test_each_arm_branch_derives_once_on_both_colors(mode: str) -> None:
    """The ``.qs`` read reuses each arm's pre-derived branch rather than deriving it again.

    ``BranchType.get_queryset`` runs once per active ``branch``, the root's and
    each ``and`` / ``or`` / ``not`` arm's, on ``apply_sync`` and on ``apply_async``
    with a sync or an async-only hook.
    """
    hook_runs: list[str] = []
    filter_set = _arm_error_order_filter(mode, gated=False, hook_runs=hook_runs)
    filter_set.get_filters()
    filter_input = {
        "branch": {"name": "1"},
        "or_": [{"branch": {"name": "2"}}, {"and_": [{"branch": {"name": "3"}}]}],
        "not_": {"branch": {"name": "4"}},
    }
    base = library_models.Shelf.objects.all()
    if mode == "sync":
        rows = filter_set.apply_sync(filter_input, base, _make_info())
    else:
        rows = asyncio.run(filter_set.apply_async(filter_input, base, _make_info()))
    assert list(rows) == []
    assert hook_runs == ["branch"] * 4


@pytest.mark.django_db(transaction=True)
def test_filters_over_a_visible_reverse_generic_relation_compare_the_one_holder() -> None:
    """The reverse ``GenericRel`` filters as the single-valued relation it is.

    A key naming the holder matches the tag that holder carries, and a path through it
    compares that one holder's column, as Django's own ``filter(holder=...)`` does; a
    tag whose ``object_id`` matches under another content type belongs to no holder.
    """

    class RpGenericTagFilter(FilterSet):
        class Meta:
            model = RpGenericTag
            fields = {"holder": ["exact"], "holder__title": ["exact"]}

    with generic_fixture_rows(connection) as (first, _second):
        rows = RpGenericTag.objects.all()
        by_holder = RpGenericTagFilter({"holder": first.pk}, queryset=rows).qs
        by_title = RpGenericTagFilter({"holder__title": "a"}, queryset=rows).qs
        assert list(by_holder.values_list("name", flat=True)) == ["t1"]
        assert list(by_title.values_list("name", flat=True)) == ["t2"]


@pytest.mark.django_db(transaction=True)
def test_related_filter_over_a_visible_reverse_generic_relation_requires_the_tag_content_type() -> (
    None
):
    """A ``RelatedFilter`` branch through the reverse ``GenericRel`` reads Django's own join.

    The branch correlates the holder to the tag's ``object_id`` AND requires the tag's
    content type to be the holder's, as ``filter(holder__title=...)`` does, so the stray
    tag storing holder ``"a"``'s pk under another content type never matches.
    """

    class RpGenericHolderType(DjangoType):
        class Meta:
            model = RpGenericHolder
            fields = ("id", "title")

    class RpGenericHolderFilter(FilterSet):
        class Meta:
            model = RpGenericHolder
            fields = {"title": ["exact"]}

    class RpGenericTagBranchFilter(FilterSet):
        holder = RelatedFilter(RpGenericHolderFilter, field_name="holder")

        class Meta:
            model = RpGenericTag
            fields = {"name": ["exact"]}

    assert registry.get(RpGenericHolder) is RpGenericHolderType
    with generic_fixture_rows(connection):
        rows = RpGenericTag.objects.order_by("name")
        filtered = RpGenericTagBranchFilter.apply_sync(
            {"holder": {"title": {"exact": "a"}}},
            rows,
            _make_info(),
        )
        django_answer = list(rows.filter(holder__title="a").values_list("name", flat=True))
        assert django_answer == ["t2"]
        assert list(filtered.values_list("name", flat=True)) == django_answer


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("relation", "title"),
    [("proxy_holder", "a"), ("proxy_only_holder", "b")],
    ids=["for_concrete_model", "proxy_content_type"],
)
def test_related_filter_over_a_proxy_reverse_generic_relation_reads_its_content_type(
    relation: str,
    title: str,
) -> None:
    """The reverse ``GenericRel`` of a proxy's ``GenericRelation`` reads Django's content type.

    With the default ``for_concrete_model=True`` the tag's content type must be the
    concrete holder's; with ``for_concrete_model=False`` the proxy's own. Each branch
    returns exactly the rows Django's own ``filter(<relation>__title=...)`` does.
    """

    class RpGenericProxyHolderType(DjangoType):
        class Meta:
            model = RpGenericProxyHolder
            fields = ("id", "title")

    class RpGenericProxyHolderFilter(FilterSet):
        class Meta:
            model = RpGenericProxyHolder
            fields = {"title": ["exact"]}

    branch_filter = type(
        "RpGenericTagProxyBranchFilter",
        (FilterSet,),
        {
            "__module__": __name__,
            relation: RelatedFilter(RpGenericProxyHolderFilter, field_name=relation),
            "Meta": type("Meta", (), {"model": RpGenericTag, "fields": {"name": ["exact"]}}),
        },
    )
    assert registry.get(RpGenericProxyHolder) is RpGenericProxyHolderType
    with generic_fixture_rows(connection):
        rows = RpGenericTag.objects.order_by("name")
        filtered = branch_filter.apply_sync(
            {relation: {"title": {"exact": title}}},
            rows,
            _make_info(),
        )
        django_answer = list(
            rows.filter(**{f"{relation}__title": title}).values_list("name", flat=True),
        )
        assert django_answer
        assert list(filtered.values_list("name", flat=True)) == django_answer


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("relation", "name"),
    [("proxy_tags", "t2"), ("proxy_only_tags", "p1")],
    ids=["for_concrete_model", "proxy_content_type"],
)
def test_related_filter_over_a_proxy_generic_relation_reads_its_content_type(
    relation: str,
    name: str,
) -> None:
    """A proxy's ``GenericRelation`` branch restricts the tags to Django's content type.

    With the default ``for_concrete_model=True`` the concrete holder's content type,
    with ``for_concrete_model=False`` the proxy's own: each branch returns exactly the
    holders Django's own ``filter(<relation>__name=...)`` does.
    """

    class RpGenericTagType(DjangoType):
        class Meta:
            model = RpGenericTag
            fields = ("id", "name")

    class RpGenericTagNameFilter(FilterSet):
        class Meta:
            model = RpGenericTag
            fields = {"name": ["exact"]}

    branch_filter = type(
        "RpGenericProxyHolderBranchFilter",
        (FilterSet,),
        {
            "__module__": __name__,
            relation: RelatedFilter(RpGenericTagNameFilter, field_name=relation),
            "Meta": type(
                "Meta",
                (),
                {"model": RpGenericProxyHolder, "fields": {"title": ["exact"]}},
            ),
        },
    )
    assert registry.get(RpGenericTag) is RpGenericTagType
    with generic_fixture_rows(connection):
        rows = RpGenericProxyHolder.objects.order_by("title")
        filtered = branch_filter.apply_sync(
            {relation: {"name": {"exact": name}}},
            rows,
            _make_info(),
        )
        django_answer = list(
            rows.filter(**{f"{relation}__name": name}).values_list("title", flat=True),
        )
        assert django_answer
        assert list(filtered.values_list("title", flat=True)) == django_answer


@pytest.mark.parametrize("default_lookup", ["exact", "gte"])
def test_generated_column_filter_for_field_reads_the_default_lookup_when_none_is_given(
    default_lookup: str,
) -> None:
    """A direct ``filter_for_field`` call with no lookup builds django-filter's default lookup.

    django-filter's signature defaults ``lookup_expr`` to ``None`` and its body reads
    ``FILTERS_DEFAULT_LOOKUP_EXPR``; a ``GeneratedField`` runs the adapted body, which
    reads the same setting, so the call builds what naming that lookup builds.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = ()

    field = library_models.Shelf._meta.get_field("code_length")
    with override_settings(FILTERS_DEFAULT_LOOKUP_EXPR=default_lookup):
        defaulted = ShelfFilter.filter_for_field(field, "code_length")
    named = ShelfFilter.filter_for_field(field, "code_length", default_lookup)
    assert defaulted is not None
    assert named is not None
    assert (type(defaulted), defaulted.field_name, defaulted.lookup_expr) == (
        type(named),
        "code_length",
        default_lookup,
    )


def _generated_filter_owner(**columns: django_models.GeneratedField) -> type[django_models.Model]:
    """Return a ``library`` model with a text ``source`` and the generated ``columns``.

    Declared inside ``isolate_apps("apps.library")`` by each caller.
    """
    attrs: dict[str, object] = {
        "__module__": __name__,
        "source": django_models.TextField(),
        "Meta": type("Meta", (), {"app_label": "library"}),
        **columns,
    }
    return type("GeneratedFilterOwner", (django_models.Model,), attrs)


def _computed(
    output_field: django_models.Field[Never, object],
    *,
    choices: list[tuple[object, str]] | None = None,
) -> django_models.GeneratedField:
    """A ``GeneratedField`` over ``source`` whose expression the output type matches."""
    expression = (
        Upper("source") if isinstance(output_field, django_models.TextField) else Length("source")
    )
    return django_models.GeneratedField(
        expression=expression,
        output_field=output_field,
        db_persist=True,
        choices=choices,
    )


@isolate_apps("apps.library")
def test_generated_columns_publish_their_output_lookups_in_one_filterset() -> None:
    """Two generated columns of different output types each expand ``"__all__"`` as their output.

    The text output keeps the text-pattern lookups; the integer output keeps its comparisons
    and drops the patterns, as each output column would. Each leaf's filter class is the one
    django-filter builds for the output column.
    """
    owner = _generated_filter_owner(
        shout=_computed(django_models.TextField()),
        size=_computed(django_models.IntegerField()),
    )

    class GeneratedLookupFilter(FilterSet):
        class Meta:
            model = owner
            fields = {"shout": "__all__", "size": "__all__"}

    fields = GeneratedLookupFilter.get_fields()
    shout = set(require(fields["shout"], is_list_or_tuple))
    size = set(require(fields["size"], is_list_or_tuple))
    assert {"icontains", "startswith", "gt"} <= shout
    assert {"gt", "in", "range"} <= size
    assert not {"icontains", "startswith", "regex"} & size
    filters = GeneratedLookupFilter.base_filters
    assert type(filters["shout__icontains"]) is CharFilter
    assert type(filters["size__gt"]) is NumberFilter
    assert type(filters["size__in"]) is IntegerInFilter


@isolate_apps("apps.library")
def test_choice_bearing_generated_column_filters_through_its_enum_filters() -> None:
    """The generated field's choices give its leaves the choice filters a choice column gets.

    ``exact`` is ``EnumChoiceFilter`` (``BLANK`` is a value, never django-filter's empty-value
    skip that widens to every row) and another single-value text lookup ``EnumLookupFilter``.
    """
    owner = _generated_filter_owner(
        grade=_computed(django_models.TextField(), choices=[("A", "Top"), ("B", "Next")]),
    )

    class GeneratedGradeFilter(FilterSet):
        class Meta:
            model = owner
            fields = {"grade": ["exact", "iexact"]}

    filters = GeneratedGradeFilter.base_filters
    assert type(filters["grade"]) is EnumChoiceFilter
    assert type(filters["grade__iexact"]) is EnumLookupFilter


@isolate_apps("apps.library")
def test_generated_column_filter_override_is_honoured() -> None:
    """A ``Meta.filter_overrides`` entry for ``GeneratedField`` selects the filter as written."""
    owner = _generated_filter_owner(size=_computed(django_models.IntegerField()))

    class GeneratedOverrideFilter(FilterSet):
        class Meta:
            model = owner
            fields = {"size": ["exact", "gt"]}
            filter_overrides: ClassVar[dict[type[django_models.Field[Never, object]], object]] = {
                django_models.GeneratedField: {"filter_class": CharFilter},
            }

    filters = GeneratedOverrideFilter.base_filters
    assert type(filters["size"]) is CharFilter
    assert type(filters["size__gt"]) is CharFilter


@isolate_apps("apps.library")
@pytest.mark.parametrize(
    ("output_class", "refusal"),
    [
        pytest.param(
            django_models.FileField,
            "GeneratedField GeneratedFilterOwner.computed has a file output_field 'FileField'",
            id="file",
        ),
        pytest.param(
            django_models.DurationField,
            "Unsupported output_field type 'DurationField' on GeneratedField "
            "GeneratedFilterOwner.computed",
            id="unsupported",
        ),
    ],
)
def test_generated_column_filter_refuses_an_output_no_conversion_publishes(
    output_class: type[django_models.Field[Never, object]],
    refusal: str,
) -> None:
    """The filter side refuses the outputs the type side refuses, naming the generated field."""
    owner = _generated_filter_owner(
        computed=django_models.GeneratedField(
            expression=Length("source"),
            output_field=output_class(),
            db_persist=True,
        ),
    )

    with pytest.raises(ConfigurationError, match=re.escape(refusal)):

        @definition_raises
        class GeneratedRefusedFilter(FilterSet):
            class Meta:
                model = owner
                fields = {"computed": ["exact"]}


@isolate_apps("apps.library")
def test_generated_column_filter_refuses_a_lookup_its_column_does_not_resolve() -> None:
    """A lookup Django's query cannot resolve on the computed column is upstream's refusal."""
    owner = _generated_filter_owner(size=_computed(django_models.IntegerField()))

    with pytest.raises(FieldLookupError, match=re.escape("'bogus'")):

        @definition_raises
        class GeneratedBogusFilter(FilterSet):
            class Meta:
                model = owner
                fields = {"size": ["bogus"]}


@isolate_apps("apps.library")
@pytest.mark.parametrize("column", ["size", "source"], ids=["generated", "plain"])
def test_an_empty_lookup_expression_is_refused_on_a_generated_column_as_on_a_plain_one(
    column: str,
) -> None:
    """``""`` is a lookup expression, never django-filter's ``DEFAULT_LOOKUP_EXPR`` fallback.

    Upstream falls back only for ``None``, so ``Meta.fields`` naming ``""`` resolves the empty
    name and refuses it on the generated column as on the plain ``source`` column, never
    building a ``size__`` filter.
    """
    owner = _generated_filter_owner(size=_computed(django_models.IntegerField()))

    with pytest.raises(FieldLookupError, match=re.escape("Unsupported lookup ''")):

        @definition_raises
        class GeneratedEmptyLookupFilter(FilterSet):
            class Meta:
                model = owner
                fields: ClassVar[dict[str, list[str]]] = {column: [""]}


@isolate_apps("apps.library")
def test_generated_column_with_no_default_filter_takes_the_unrecognized_field_behavior() -> None:
    """A generated ``JSONField`` output has no default filter: ``IGNORE`` skips it, ``RAISE`` names it."""
    owner = _generated_filter_owner(
        computed=django_models.GeneratedField(
            expression=Length("source"),
            output_field=django_models.JSONField(),
            db_persist=True,
        ),
    )

    class GeneratedIgnoredFilter(FilterSet):
        class Meta:
            model = owner
            fields = {"source": ["exact"], "computed": ["exact"]}
            unknown_field_behavior = UnknownFieldBehavior.IGNORE

    assert list(GeneratedIgnoredFilter.base_filters) == ["source"]
    with pytest.raises(
        AssertionError,
        match=re.escape(
            "resolved field 'computed' with 'exact' lookup to an unrecognized field type "
            "GeneratedField.",
        ),
    ):

        @definition_raises
        class GeneratedRaisedFilter(FilterSet):
            class Meta:
                model = owner
                fields = {"computed": ["exact"]}
