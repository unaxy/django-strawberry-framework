"""Filter input-generation tests for lookup naming, field construction, normalization, references, and reset.

Covers the lookup-name table, the `_build_logic_fields` /
`_build_input_fields` operator-bag builders, `construct_search`,
`convert_filter_to_input_annotation` / `normalize_input_value` table
cases, `FieldSpec` source-path mapping, and the `filter_input_type`
consumer helper (Decision 11).

``HIDE_FLAT_FILTERS`` wire shape lives in
``test_library_api.py`` / ``test_products_api.py``. Scoped ``RangeFilter``
type names live in ``test_scalars_filter_api.py``. Relay-relation
``isNull`` Boolean vs GlobalID-list ``exact`` lives in
``test_library_api.py``. This file keeps converter dispatch, namespace
lifecycle, and digit-boundary type-name injectivity -- construction and
private helpers a request cannot name.
"""

from __future__ import annotations

import dataclasses
import datetime
import decimal
import gc
import re
import typing
import uuid
import weakref
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol, TypeAlias, get_args, get_origin, runtime_checkable

import django_filters
import pytest
import strawberry
from apps.library import models as library_models
from apps.products.models import Category, Item
from apps.scalars import models as scalar_models
from django import forms
from django.db import models
from django.db.models import QuerySet
from django_filters import (
    AllValuesFilter,
    AllValuesMultipleFilter,
    BaseInFilter,
    BaseRangeFilter,
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    DateRangeFilter,
    Filter,
    LookupChoiceFilter,
    NumberFilter,
)
from django_filters import RangeFilter as DjangoRangeFilter
from django_filters.filters import BaseInFilter as DjangoBaseInFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.test import APIRequestFactory
from strawberry import relay
from strawberry.types.base import get_object_definition
from strawberry.types.field import StrawberryField
from typing_extensions import override

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    FilterInput,
    FilterSet,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    ListFilter,
    RangeFilter,
    RelatedFilter,
    TypedFilter,
    _helper_referenced_filtersets,
    filter_input_type,
)
from django_strawberry_framework.filters import inputs as inputs_mod
from django_strawberry_framework.filters.base import RelationPkFilter, RelationPkMultipleFilter
from django_strawberry_framework.filters.factories import FilterArgumentsFactory
from django_strawberry_framework.filters.inputs import (
    _FILTER_INPUT_KIND_TYPES,
    INPUTS_MODULE_PATH,
    LOGIC_OP_AND,
    LOGIC_OP_NOT,
    LOGIC_OP_OR,
    LOGIC_OPERATORS,
    LOGIC_OPERATORS_BY_PYTHON_ATTR,
    LOGIC_OPERATORS_BY_WIRE,
    LOOKUP_NAME_MAP,
    _build_input_fields,
    _build_logic_fields,
    _build_range_input_class,
    _camel_case,
    _field_specs,
    _filter_input_prechecks,
    _iter_filterset_subclasses,
    _pascal_case,
    _scalar_from_form_field,
    _scalar_from_model_field,
    _unexpected_filter_dispatch,
    build_input_class,
    clear_filter_input_namespace,
    construct_search,
    convert_filter_to_input_annotation,
    filter_lookup_table,
    materialize_input_class,
    normalize_input_value,
)
from django_strawberry_framework.filters.sets import filter_generation_provenance
from django_strawberry_framework.registry import registry
from django_strawberry_framework.sets_mixins import ClassBasedTypeNameMixin
from django_strawberry_framework.types.finalizer import finalize_django_types
from django_strawberry_framework.utils._narrowing import dict_of, read_attr
from django_strawberry_framework.utils.input_values import UNSET
from tests._generated_inputs import keyword_constructor as _keyword_constructor
from tests._idioms import (
    ClaimsClass,
    ClassReadRaises,
    ModelSerializerBase,
    consumer_module,
    consumer_query,
    is_object_list,
)
from tests._soft_dependency import blocked_modules

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

    from django_strawberry_framework.utils.typing import ModelField

    # Each field's descriptor types as django-stubs declares them (set type, get type),
    # spelled out because the checker runs without the django-stubs mypy plugin.
    _Char: TypeAlias = models.CharField[str | int | Combinable, str]
    _Int: TypeAlias = models.IntegerField[float | int | str | Combinable, int]


def _args(annotation: object) -> tuple[object, ...]:
    """``typing.get_args`` with each member typed ``object`` (typeshed declares them ``Any``)."""
    return get_args(annotation)


def _class_arg(annotation: object) -> type:
    """The one non-``None`` member of ``annotation`` (``X | None``), asserted to be a class."""
    (member,) = (arg for arg in _args(annotation) if arg is not type(None))
    assert isinstance(member, type), member
    return member


def _annotations(cls: type) -> dict[object, object]:
    """A copy of ``cls.__annotations__`` (typeshed types its values ``Any``)."""
    return dict_of(read_attr(cls, "__annotations__"))


def _definition_fields(cls: object) -> list[StrawberryField]:
    """The Strawberry fields of generated input class ``cls``, failing when it has no definition."""
    return get_object_definition(cls, strict=True).fields


@runtime_checkable
class _ScratchInput(Protocol):
    """The two fields the scratch ``build_input_class`` call generates."""

    name: str | None
    count: int | None


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    registry.clear()
    _field_specs.clear()
    _helper_referenced_filtersets.clear()
    yield
    registry.clear()
    _field_specs.clear()
    _helper_referenced_filtersets.clear()


# ---------------------------------------------------------------------------
# LOOKUP_NAME_MAP table
# ---------------------------------------------------------------------------


def test_lookup_name_map_full_table_matches_spec() -> None:
    """Pin the spec-027 Decision 3 Layer-5 table verbatim against accidental drift."""
    expected = {
        "exact": ("exact", "exact"),
        "iexact": ("i_exact", "iExact"),
        "contains": ("contains", "contains"),
        "icontains": ("i_contains", "iContains"),
        "startswith": ("starts_with", "startsWith"),
        "istartswith": ("i_starts_with", "iStartsWith"),
        "endswith": ("ends_with", "endsWith"),
        "iendswith": ("i_ends_with", "iEndsWith"),
        "regex": ("regex", "regex"),
        "iregex": ("i_regex", "iRegex"),
        "gt": ("gt", "gt"),
        "gte": ("gte", "gte"),
        "lt": ("lt", "lt"),
        "lte": ("lte", "lte"),
        "isnull": ("is_null", "isNull"),
        "in": ("in_", "in"),
        "range": ("range", "range"),
        "date": ("date", "date"),
        "year": ("year", "year"),
        "month": ("month", "month"),
        "day": ("day", "day"),
        "week_day": ("week_day", "weekDay"),
        "quarter": ("quarter", "quarter"),
        "hour": ("hour", "hour"),
        "minute": ("minute", "minute"),
        "second": ("second", "second"),
    }
    assert expected == LOOKUP_NAME_MAP


# ---------------------------------------------------------------------------
# _build_logic_fields
# ---------------------------------------------------------------------------


def test_build_logic_fields_uses_inside_list_annotated_for_and_or() -> None:
    """`Annotated[...]` lives INSIDE the `list[...]`, not outside."""
    triples = _build_logic_fields("DemoFilterInputType")
    by_attr = {python_attr: (annotation, kwargs) for python_attr, annotation, kwargs in triples}

    # `and_` / `or_` -> `list[Annotated["X", strawberry.lazy(...)]] | None`
    for attr in ("and_", "or_"):
        annotation, _ = by_attr[attr]
        # Strip the `| None` to inspect the list shape.
        non_none_args = [arg for arg in _args(annotation) if arg is not type(None)]
        assert len(non_none_args) == 1
        list_type = non_none_args[0]
        assert get_origin(list_type) is list
        inner = _args(list_type)[0]
        # The inner type must be Annotated with a string forward ref.
        assert get_origin(inner) is typing.Annotated or hasattr(inner, "__metadata__")
        inner_args = _args(inner)
        assert inner_args[0] == "DemoFilterInputType" or (
            read_attr(inner_args[0], "__forward_arg__", None) == "DemoFilterInputType"
        )

    # `not_` -> `Annotated["X", strawberry.lazy(...)] | None`
    annotation, _ = by_attr["not_"]
    non_none_args = [arg for arg in _args(annotation) if arg is not type(None)]
    assert len(non_none_args) == 1
    not_inner = non_none_args[0]
    assert hasattr(not_inner, "__metadata__")
    not_inner_args = _args(not_inner)
    assert not_inner_args[0] == "DemoFilterInputType" or (
        read_attr(not_inner_args[0], "__forward_arg__", None) == "DemoFilterInputType"
    )


def test_build_logic_fields_emits_strawberry_field_name_for_python_keywords() -> None:
    """`and` / `or` / `not` are Python keywords -- they ride through `strawberry.field(name=...)`.

    Each carries an explicit ``default=None`` so it stays OPTIONAL: an
    omitted ``default`` builds a REQUIRED field.
    """
    triples = _build_logic_fields("X")
    by_attr = {python_attr: kwargs for python_attr, _, kwargs in triples}
    assert by_attr["and_"] == {"name": "and", "default": None}
    assert by_attr["or_"] == {"name": "or", "default": None}
    assert by_attr["not_"] == {"name": "not", "default": None}


def test_build_logic_fields_tracks_logic_operators() -> None:
    """Emission order and ``(python_attr, wire_name)`` pairs must match ``LOGIC_OPERATORS``.

    ``FilterSet._normalize_input`` maps the same constant onto django-filter
    wire keys; re-spelling the pairs in ``_build_logic_fields`` would let the
    input surface and the runtime normalizer diverge.
    """
    triples = _build_logic_fields("X")
    assert [(python_attr, kwargs["name"]) for python_attr, _, kwargs in triples] == [
        (op.python_attr, op.wire_name) for op in LOGIC_OPERATORS
    ]


def test_logic_operator_descriptors_and_mappings() -> None:
    """Descriptors encapsulate python attr, wire name, sequence cardinality, and Q compose."""
    assert LOGIC_OPERATORS == (LOGIC_OP_AND, LOGIC_OP_OR, LOGIC_OP_NOT)
    assert LOGIC_OPERATORS_BY_WIRE == {"and": LOGIC_OP_AND, "or": LOGIC_OP_OR, "not": LOGIC_OP_NOT}
    assert LOGIC_OPERATORS_BY_PYTHON_ATTR == {
        "and_": LOGIC_OP_AND,
        "or_": LOGIC_OP_OR,
        "not_": LOGIC_OP_NOT,
    }
    assert isinstance(LOGIC_OPERATORS_BY_WIRE, MappingProxyType)
    assert isinstance(LOGIC_OPERATORS_BY_PYTHON_ATTR, MappingProxyType)
    with pytest.raises(TypeError):
        # basedpyright: the table is a read-only MappingProxyType; the test proves item assignment
        # raises TypeError
        LOGIC_OPERATORS_BY_WIRE["custom"] = LOGIC_OP_AND  # pyright: ignore[reportIndexIssue]
    with pytest.raises(TypeError):
        # basedpyright: the table is a read-only MappingProxyType; the test proves item assignment
        # raises TypeError
        LOGIC_OPERATORS_BY_PYTHON_ATTR["custom_"] = LOGIC_OP_AND  # pyright: ignore[reportIndexIssue]
    assert LOGIC_OP_AND.is_sequence is True
    assert LOGIC_OP_OR.is_sequence is True
    assert LOGIC_OP_NOT.is_sequence is False


def test_logic_operator_composition_semantics() -> None:
    """Each operator compose function builds the expected Django Q structure."""
    q1 = models.Q(name="a")
    q2 = models.Q(name="b")

    # and_ compose
    assert LOGIC_OP_AND.compose([]) == models.Q()
    assert LOGIC_OP_AND.compose([q1]) == models.Q(name="a")
    assert LOGIC_OP_AND.compose([q1, q2]) == (models.Q(name="a") & models.Q(name="b"))

    # or_ compose
    assert LOGIC_OP_OR.compose([]) == models.Q()
    assert LOGIC_OP_OR.compose([q1, q2]) == (models.Q(name="a") | models.Q(name="b"))

    # not_ compose
    assert LOGIC_OP_NOT.compose([]) == models.Q()
    assert LOGIC_OP_NOT.compose([q1]) == ~models.Q(name="a")


# ---------------------------------------------------------------------------
# build_input_class
# ---------------------------------------------------------------------------


def test_build_input_class_returns_strawberry_input_decorated_dataclass() -> None:
    """The constructed class is a Strawberry input AND a dataclass."""
    cls = build_input_class(
        "ScratchInput",
        [("name", str | None, {"default": None}), ("count", int | None, {"default": None})],
    )
    instance = _keyword_constructor(cls)(name="hi", count=3)
    assert isinstance(instance, _ScratchInput)
    assert instance.name == "hi"
    assert instance.count == 3
    assert hasattr(cls, "__strawberry_definition__")


def test_build_input_class_emits_strawberry_field_name_alias() -> None:
    """`name=...` field kwarg lands as the Strawberry field's GraphQL alias."""
    cls = build_input_class(
        "AliasedInput",
        [
            ("in_", list[int] | None, {"name": "in", "default": None}),
        ],
    )
    # Walk the Strawberry definition to find the field named `in`.
    fields = cls.__strawberry_definition__.fields
    assert any(field.graphql_name == "in" for field in fields)


# ---------------------------------------------------------------------------
# _build_input_fields
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_build_input_fields_populates_field_specs_table() -> None:
    class GalaxyFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    _build_input_fields(GalaxyFilter)
    spec = _field_specs[(GalaxyFilter, "name")]
    assert spec.python_attr == "name"
    assert spec.graphql_name == "name"
    assert spec.django_source_path == "name"


@pytest.mark.django_db
def test_field_spec_maps_galaxy_name_flat_field_to_django_source_path() -> None:
    """A flat ``galaxy__name`` field carries the source path verbatim."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            # Use the `branch__name` relation traversal: same shape as
            # the spec's `galaxy__name` example.
            fields = {"branch__name": ["exact"]}

    _build_input_fields(ShelfFilter)
    spec = _field_specs[(ShelfFilter, "branch_name")]
    assert spec.python_attr == "branch_name"
    assert spec.graphql_name == "branchName"
    assert spec.django_source_path == "branch__name"


@pytest.mark.django_db
def test_build_input_fields_pins_every_lookup_name_to_its_camel_name() -> None:
    """The operator-bag wire name is pinned to ``graphql_camel_name`` for EVERY lookup.

    The shared input builder pins ``exact`` -> ``exact`` even though the optional-field
    helper does not need to carry an identity alias. Strawberry's converter therefore
    cannot re-derive generated names or collapse a digit-adjacent underscore.
    """

    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"name": ["exact", "icontains", "isnull"], "id": ["in"]}

    triples = _build_input_fields(ItemFilter)
    by_attr = {python_attr: (annotation, kwargs) for python_attr, annotation, kwargs in triples}
    # Find the `name` field's bag class and walk its Strawberry fields.
    name_annotation = by_attr["name"][0]
    # `bag_class | None` -> strip None to get the bag class.
    bag = next(arg for arg in _args(name_annotation) if arg is not type(None))
    bag_fields = {field.python_name: field.graphql_name for field in _definition_fields(bag)}
    # `exact` -> attr `exact`, pinned by the shared builder rather than Strawberry.
    assert bag_fields["exact"] == "exact"
    # `icontains` -> attr `i_contains`, alias `iContains`.
    assert bag_fields["i_contains"] == "iContains"
    # `isnull` -> attr `is_null`, alias `isNull`.
    assert bag_fields["is_null"] == "isNull"

    id_annotation = by_attr["id"][0]
    id_bag = next(arg for arg in _args(id_annotation) if arg is not type(None))
    id_fields = {field.python_name: field.graphql_name for field in _definition_fields(id_bag)}
    # `in_` -> alias `in`.
    assert id_fields["in_"] == "in"


@pytest.mark.django_db
def test_build_input_fields_handles_field_name_in_lookup_name_map() -> None:
    """A relation field named like a ``LOOKUP_NAME_MAP`` key is not grouped as field plus lookup.

    When a traversed relation field is named like a ``LOOKUP_NAME_MAP`` key, e.g. ``branch__year``,
    but the filter lookup differs, e.g. ``exact``, it must not be grouped as field ``branch`` with
    lookup ``year``.
    """

    class YearFilter(FilterSet):
        branch__year = GlobalIDFilter(field_name="branch__name", lookup_expr="exact")

        class Meta:
            model = library_models.Shelf
            fields = []

    triples = _build_input_fields(YearFilter)
    by_attr = {python_attr: (annotation, kwargs) for python_attr, annotation, kwargs in triples}

    # Under correct behavior, the top-level field is `branch_year`, NOT `branch`!
    assert "branch_year" in by_attr
    assert "branch" not in by_attr


def test_declared_filter_name_ending_in_lookup_keeps_its_form_key() -> None:
    """A declared ``name__exact`` filter must not collapse onto the ``name`` field.

    The declaration name is the django-filter form key. If grouping treats its
    final ``exact`` token as an auto-generated lookup, input generation emits a
    ``name`` bag and normalization writes ``name``; the bound form only reads
    ``name__exact`` and silently drops the supplied predicate.
    """

    class DeclaredLookupNameFilter(FilterSet):
        name__exact = CharFilter(field_name="name", lookup_expr="exact")

        class Meta:
            model = Category
            fields = []

    triples = _build_input_fields(DeclaredLookupNameFilter)
    by_attr = {python_attr: annotation for python_attr, annotation, _kwargs in triples}
    assert "name_exact" in by_attr
    assert "name" not in by_attr
    assert _field_specs[(DeclaredLookupNameFilter, "name_exact")].django_source_path == (
        "name__exact"
    )
    assert DeclaredLookupNameFilter._normalize_input(
        {"name_exact": {"exact": "alpha"}},
    ) == {"name__exact": "alpha"}


def test_declared_non_exact_filter_keeps_its_form_key() -> None:
    """A declared non-``exact`` filter must not gain a generated lookup suffix.

    django-filter registers a class-body declaration under its attribute name
    (``custom``), even when ``lookup_expr="icontains"``. Emitting
    ``custom__icontains`` in ``data`` is an unknown form key, so the form drops
    the value and the declared filter silently applies nothing.
    """

    class DeclaredContainsFilter(FilterSet):
        custom = CharFilter(field_name="name", lookup_expr="icontains")

        class Meta:
            model = Category
            fields = []

    _build_input_fields(DeclaredContainsFilter)
    assert DeclaredContainsFilter._normalize_input(
        {"custom": {"i_contains": "alpha"}},
    ) == {"custom": "alpha"}


def _bag_lookup_attrs(filterset_cls: type[FilterSet], python_attr: str) -> list[str]:
    """Return the lookup attrs of one generated operator-bag field, in emission order."""
    triples = _build_input_fields(filterset_cls)
    annotation = {attr: annotation for attr, annotation, _kwargs in triples}[python_attr]
    return [field.name for field in dataclasses.fields(_class_arg(annotation))]


def test_overlap_head_emits_one_bag_with_each_lookup_keeping_its_own_form_key() -> None:
    """A declared head that is also a ``Meta.fields`` head emits one bag, two form keys.

    The declared ``name`` (``iexact``) and the generated ``name__icontains`` share
    the ``name`` head; the table keeps each lookup's own ``get_filters()`` name.
    """

    class OverlapBranchFilter(FilterSet):
        name = CharFilter(lookup_expr="iexact")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["icontains"]}

    assert _bag_lookup_attrs(OverlapBranchFilter, "name") == ["i_contains", "i_exact"]
    lookups = filter_lookup_table(OverlapBranchFilter).by_input_attr["name"]
    assert {attr: form_key for attr, (form_key, _filter) in lookups.items()} == {
        "i_contains": "name__icontains",
        "i_exact": "name",
    }


def _normalize_name_mapping(cls: type[FilterSet]) -> object:
    return cls._normalize_input({"name": {"i_contains": "x"}})


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_build_input_fields, id="input-build"),
        pytest.param(_normalize_name_mapping, id="direct-mapping"),
    ],
)
def test_two_filters_on_one_head_lookup_slot_raise(
    build: Callable[[type[FilterSet]], object],
) -> None:
    """A declared filter and a generated one claiming one ``(head, lookup)`` slot raise.

    The declared ``name`` (``icontains`` over ``city``) and the generated
    ``name__icontains`` both land on ``name`` / ``icontains``; one would vanish from
    the generated input, so the table refuses the class wherever it is first read.
    """

    class SameSlotBranchFilter(FilterSet):
        name = CharFilter(field_name="city", lookup_expr="icontains")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["icontains"]}

    with pytest.raises(ConfigurationError) as excinfo:
        build(SameSlotBranchFilter)
    assert str(excinfo.value) == (
        "test_two_filters_on_one_head_lookup_slot_raise.<locals>.SameSlotBranchFilter: "
        "filters 'name__icontains' and 'name' both bind the 'icontains' lookup of input "
        "field 'name', so one would be unreachable from the generated input. Rename one "
        "filter or drop one via Meta.fields / Meta.exclude."
    )


def test_two_heads_flattening_to_one_input_attr_raise() -> None:
    """Two ``__`` heads sharing one flattened input attr raise; neither is reachable alone."""

    class AliasCollisionBranchFilter(FilterSet):
        a__b_c = CharFilter(field_name="name")
        a_b__c = CharFilter(field_name="city")

        class Meta:
            model = library_models.Branch
            fields = []

    with pytest.raises(ConfigurationError) as excinfo:
        filter_lookup_table(AliasCollisionBranchFilter)
    assert str(excinfo.value) == (
        "test_two_heads_flattening_to_one_input_attr_raise.<locals>.AliasCollisionBranchFilter: "
        "filters 'a__b_c' and 'a_b__c' both generate the input attribute 'a_b_c' (Django "
        "path separators flatten to '_'), so one would be unreachable. Rename one filter or "
        "drop one via Meta.fields / Meta.exclude."
    )


def test_expanded_declared_child_filter_is_its_own_head() -> None:
    """A ``RelatedFilter`` expansion of a child's declared filter keeps its own head.

    The child declares ``title`` (``field_name="name"``) and ``name__exact`` beside a
    generated ``name``. Expanded under ``branch``, ``branch__name__exact`` is its own
    head (it would otherwise shadow the generated ``branch__name`` exact), and every
    flat head binds its own expanded form key.
    """

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

    table = filter_lookup_table(ParentShelfFilter)
    flat = {
        head: {token: form_key for token, (form_key, _filter) in bag.items()}
        for head, bag in table.heads.items()
        if head != "branch"
    }
    assert flat == {
        "branch__name": {"exact": "branch__name"},
        "branch__title": {"icontains": "branch__title"},
        "branch__name__exact": {"exact": "branch__name__exact"},
    }
    assert table.by_input_attr["branch_name_exact"] is table.by_input_attr["branch__name__exact"]
    # An expanded declared child keeps its declared name as its gate path; the
    # generated ``branch__name`` gates on the ORM path it is named after.
    assert table.gate_paths["branch_title"] == "branch__title"
    assert table.gate_paths["branch__name"] == "branch__name"


# ---------------------------------------------------------------------------
# convert_filter_to_input_annotation
# ---------------------------------------------------------------------------


def test_convert_filter_to_input_annotation_handles_globalid_filter() -> None:
    f = GlobalIDFilter()
    assert convert_filter_to_input_annotation(f, None) == str | None


def test_convert_filter_to_input_annotation_handles_globalid_multiple_choice_filter() -> None:
    f = GlobalIDMultipleChoiceFilter()
    assert convert_filter_to_input_annotation(f, None) == list[str] | None


def test_convert_filter_to_input_annotation_handles_range_filter() -> None:
    f = RangeFilter(field_name="value")
    model_field: _Int = models.IntegerField()
    annotation = convert_filter_to_input_annotation(f, model_field)
    non_none = [arg for arg in _args(annotation) if arg is not type(None)]
    assert len(non_none) == 1
    range_cls = non_none[0]
    assert hasattr(range_cls, "__strawberry_definition__")
    fields = {field.python_name for field in _definition_fields(range_cls)}
    assert fields == {"start", "end"}


def test_convert_filter_to_input_annotation_handles_list_filter() -> None:
    f = ListFilter(field_name="value")
    model_field: _Int = models.IntegerField()
    annotation = convert_filter_to_input_annotation(f, model_field)
    assert annotation == list[int] | None


def test_convert_filter_to_input_annotation_handles_choice_filter_via_converter_pipeline() -> None:
    """`ChoiceFilter` reaches into ``convert_choices_to_enum`` via the model field."""
    # ``Book.circulation_status`` is a TextChoices field on the example model.
    f = ChoiceFilter()
    model_field: ModelField = library_models.Book._meta.get_field("circulation_status")
    annotation = convert_filter_to_input_annotation(f, model_field)
    non_none = [arg for arg in _args(annotation) if arg is not type(None)]
    assert len(non_none) == 1
    enum_cls = non_none[0]
    # The converter pipeline yields a Strawberry-decorated enum.
    assert isinstance(enum_cls, type)
    assert issubclass(enum_cls, Enum)


def test_convert_filter_to_input_annotation_rejects_non_choices_derived_enum() -> None:
    f = ChoiceFilter()
    model_field: _Char = models.CharField()  # No `choices` attribute set.
    with pytest.raises(ConfigurationError):
        convert_filter_to_input_annotation(f, model_field)


def test_convert_filter_to_input_annotation_rejects_unknown_method_filter() -> None:
    """A ``method=`` filter whose form field cannot be built on a copy raises ConfigurationError.

    The real shape is a filter whose ``field`` needs the bound ``FilterSet``, such as
    ``AllValuesMultipleFilter`` reading the per-request ``model``; unbound, the copy
    builds no form field, so nothing can type the input. A bare ``Filter(method=...)``
    is not one: it builds the base ``forms.Field`` and types as ``str``.
    """

    # A stand-in with ``method`` set and no form field to read, local to this test so no
    # shared filter class is patched.
    def _passthrough_method(qs: object, _name: str, _value: object) -> object:
        return qs

    class _NoFieldFilter:
        extra = {}
        method = staticmethod(_passthrough_method)
        field = None
        lookup_expr = "exact"

    f = _NoFieldFilter()
    # It subclasses none of the filter kinds the converter dispatches on, so it reaches
    # the catch-all, where a ``method`` with no form field raises.
    with pytest.raises(ConfigurationError):
        # basedpyright: a stand-in filter carrying only the slots the code under test reads;
        # convert_filter_to_input_annotation types the parameter as Filter
        convert_filter_to_input_annotation(f, None)  # pyright: ignore[reportArgumentType]


def test_convert_filter_to_input_annotation_malformed_filter_diagnostics() -> None:
    """Malformed filters raise ConfigurationError naming the method and the filter."""

    class NoFieldFilter:
        extra = {}
        method = "filter_custom"
        field = None
        lookup_expr = "exact"

    with pytest.raises(ConfigurationError) as exc_info:
        # basedpyright: the duck-typed filter with no form field is the malformed input under
        # test; convert_filter_to_input_annotation types the parameter as Filter
        convert_filter_to_input_annotation(NoFieldFilter(), None)  # pyright: ignore[reportArgumentType]
    assert str(exc_info.value).startswith("NoFieldFilter(method='filter_custom') on <")
    assert "exposes no form field" in str(exc_info.value)

    # ``AllValuesMultipleFilter`` reads the per-request ``model`` to build its field, so
    # unbound it builds none; the refusal advises the two spellings that build one.
    unbound = AllValuesMultipleFilter(field_name="city", method="filter_custom")
    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(unbound, None)
    assert str(exc_info.value) == (
        f"AllValuesMultipleFilter(method='filter_custom') on {unbound!r} exposes no form "
        "field; put the method on a typed filter primitive (`CharFilter(method=...)`, "
        "`NumberFilter(method=...)`, `ListFilter(method=...)` for a list value, ...) or on a "
        "`Filter` subclass declaring `field_class` at class level."
    )


@pytest.mark.parametrize(
    ("make_filter", "model_field"),
    [
        pytest.param(
            lambda: ChoiceFilter(field_name="title", choices=[("a", "A")]),
            library_models.Book._meta.get_field("title"),
            id="choice-filter-plain-column",
        ),
        pytest.param(
            lambda: AllValuesFilter(field_name="city"),
            library_models.Branch._meta.get_field("city"),
            id="all-values-filter-text-column",
        ),
        pytest.param(
            lambda: DateRangeFilter(field_name="created_date"),
            Item._meta.get_field("created_date"),
            id="date-range-filter-datetime-column",
        ),
    ],
)
def test_choice_filter_without_a_choices_column_names_the_declared_class(
    make_filter: Callable[[], ChoiceFilter],
    model_field: ModelField,
) -> None:
    """A choice filter whose column declares no ``choices`` is refused under its own class name.

    ``AllValuesFilter`` and ``DateRangeFilter`` subclass ``ChoiceFilter``, so they reach the
    choice-enum refusal; the message names the class the consumer declared and advises the
    spellings that build for each of them.
    """
    choice_filter = make_filter()
    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(choice_filter, model_field)
    assert str(exc_info.value) == (
        f"{type(choice_filter).__name__} on {choice_filter!r} is backed by no model field "
        "declaring `choices`; declare `choices` on the column it filters (a `TextChoices` / "
        "`IntegerChoices` class), or filter that column through a non-choice filter "
        "(`CharFilter`, `NumberFilter`, `DateFromToRangeFilter`, its lookups in Meta.fields, "
        "or `CharFilter(method=...)` for a method filter)."
    )


def test_convert_filter_to_input_annotation_wraps_nullable() -> None:
    """``extra['required']=False`` (the default) wraps the annotation in `T | None`."""
    f = CharFilter()
    annotation = convert_filter_to_input_annotation(f, models.CharField())
    assert annotation == str | None


def test_convert_filter_to_input_annotation_does_not_wrap_required() -> None:
    f = CharFilter(required=True)
    annotation = convert_filter_to_input_annotation(f, models.CharField())
    # Required filters return the scalar without the `| None` wrap.
    assert annotation is str


# ---------------------------------------------------------------------------
# Class-level declarations: refused LookupChoiceFilter, unwritten reads
# ---------------------------------------------------------------------------


class _PriceLookupChoiceFilter(LookupChoiceFilter):
    """A consumer subclass of ``LookupChoiceFilter``; the refusal keys on the class."""


_LOOKUP_CHOICE_DECLARATIONS = [
    pytest.param(
        lambda: LookupChoiceFilter(field_name="price", field_class=forms.DecimalField),
        id="lookups-from-the-column",
    ),
    pytest.param(
        lambda: LookupChoiceFilter(
            field_name="price",
            field_class=forms.DecimalField,
            lookup_choices=[("exact", "Equals"), ("gt", "Greater than")],
        ),
        id="declared-lookups",
    ),
    pytest.param(
        lambda: _PriceLookupChoiceFilter(field_name="price", field_class=forms.DecimalField),
        id="subclass",
    ),
]


def _price_lookup_set(declared: LookupChoiceFilter) -> type[FilterSet]:
    """A package ``FilterSet`` over ``ScalarSpecimen`` declaring ``declared`` as ``price``."""

    class PriceLookupSet(FilterSet):
        price = declared

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    return PriceLookupSet


def _serve(served: type[FilterSet]) -> type[DjangoType]:
    """Declare a ``ScalarSpecimen`` ``DjangoType`` whose ``Meta.filterset_class`` is ``served``."""

    class PriceLookupSpecimenType(DjangoType):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = ("id", "label")
            filterset_class = served

    return PriceLookupSpecimenType


@pytest.mark.parametrize("declare", _LOOKUP_CHOICE_DECLARATIONS)
def test_lookup_choice_filter_on_a_served_filterset_is_refused_when_the_schema_is_built(
    declare: Callable[[], LookupChoiceFilter],
) -> None:
    """A ``LookupChoiceFilter`` filters by a value and a lookup no GraphQL input carries.

    The schema build refuses it before reading its form field, so the declaration
    keeps every attribute it had. No fakeshop FilterSet can declare one: its schema
    would refuse to build.
    """
    declared = declare()
    _ = _serve(_price_lookup_set(declared))
    state = dict(vars(declared))
    extra = dict(declared.extra)

    with pytest.raises(ConfigurationError) as excinfo:
        finalize_django_types()

    assert str(excinfo.value) == (
        f"PriceLookupSet: {type(declared).__name__} on 'price' filters by a value and a "
        "lookup read from two form-data keys, and no GraphQL input carries that pair. List "
        "the lookups in Meta.fields dict form (one input field per lookup), or keep the "
        "filter on a FilterSet the schema does not serve."
    )
    assert (vars(declared), declared.extra) == (state, extra)


def _priced_specimen(label: str, price: str) -> None:
    """Create a ``ScalarSpecimen`` named ``label`` at ``price``."""
    _ = scalar_models.ScalarSpecimen.objects.create(
        label=label,
        price=decimal.Decimal(price),
        occurred_on=datetime.date(2026, 1, 2),
        occurred_at=datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc),
        occurred_time=datetime.time(3, 4, 5),
        external_id=uuid.uuid4(),
    )


class _SpecimenLabelSerializer(ModelSerializerBase[scalar_models.ScalarSpecimen]):
    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)


@pytest.mark.django_db
@pytest.mark.parametrize("declare", _LOOKUP_CHOICE_DECLARATIONS)
def test_lookup_choice_filter_the_schema_refused_still_filters_under_django_filter(
    declare: Callable[[], LookupChoiceFilter],
) -> None:
    """The refused declaration filters as django-filter documents it, directly and through DRF.

    The same ``FilterSet`` class serves a ``DjangoFilterBackend`` list view after the
    failed schema build: the refusal wrote nothing the per-request copy carries.
    """
    served = _price_lookup_set(declare())
    _ = _serve(served)
    with pytest.raises(ConfigurationError):
        finalize_django_types()
    _priced_specimen("kept", "10.5")
    _priced_specimen("other", "99")
    queryset = scalar_models.ScalarSpecimen.objects.order_by("label")

    class PriceLookupListView(generics.ListAPIView[scalar_models.ScalarSpecimen]):
        serializer_class = _SpecimenLabelSerializer
        filter_backends = (DjangoFilterBackend,)
        filterset_class = served
        authentication_classes = ()
        permission_classes = ()
        pagination_class = None

    direct = served(data={"price": "10.5", "price_lookup": "exact"}, queryset=queryset)
    request = APIRequestFactory().get("/specimens/?price=10.5&price_lookup=exact")
    response = PriceLookupListView.as_view(queryset=queryset)(request)

    assert list(direct.qs.values_list("label", flat=True)) == ["kept"]
    assert (response.status_code, read_attr(response, "data")) == (200, [{"label": "kept"}])


def _no_rows(queryset: QuerySet[library_models.Branch], _name: str, _value: object) -> object:
    """A ``method=`` filter body; the schema build never runs it."""
    return queryset.none()


class _DecimalMethodFilter(Filter):
    """A consumer ``method=`` filter whose form field cleans a decimal."""

    field_class = forms.DecimalField


def _declared_filtersets() -> tuple[type[FilterSet], type[FilterSet]]:
    """Fresh child and parent sets, so no other test's schema build touched a declaration.

    The child declares every class-level filter whose form field the input converter
    reads; the parent expands them through ``branch``, a ``method=`` child leaf as a
    projected copy reading the child's declaration.
    """

    class DeclaredChildBranchFilter(FilterSet):
        title = CharFilter(field_name="name", lookup_expr="icontains")
        tagged = CharFilter(method="filter_tagged")
        open_on = BooleanFilter(field_name="city", lookup_expr="isnull")
        city_in = AllValuesMultipleFilter(field_name="city")
        floor = NumberFilter(method="filter_tagged")
        price = _DecimalMethodFilter(method="filter_tagged")

        class Meta:
            model = library_models.Branch
            fields = []

        def filter_tagged(
            self,
            queryset: QuerySet[library_models.Branch],
            name: str,
            value: object,
        ) -> object:
            """Answer no rows; the schema build never runs it."""
            return _no_rows(queryset, name, value)

    class DeclaredParentShelfFilter(FilterSet):
        branch = RelatedFilter(DeclaredChildBranchFilter, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = []

    return DeclaredChildBranchFilter, DeclaredParentShelfFilter


@pytest.mark.parametrize(
    "name",
    [
        "title",
        "tagged",
        "open_on",
        "city_in",
        "floor",
        "price",
    ],
)
def test_building_the_schema_writes_nothing_to_a_class_level_declaration(name: str) -> None:
    """The input converter reads each declaration's form field on a copy of it.

    A declaration is shared by every request and deep-copied into each one, so a form
    field the build cached on it would ride every copy. Each child declaration is read
    as the child's own input field and, through ``branch``, as the parent's expanded leaf.
    """
    child, parent = _declared_filtersets()
    declared = child.base_filters[name]
    state = dict(vars(declared))
    extra = dict(declared.extra)

    class DeclaredChildBranchType(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            filterset_class = child

    class DeclaredParentShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            filterset_class = parent

    finalize_django_types()

    assert registry.get(library_models.Branch) is DeclaredChildBranchType
    assert registry.get(library_models.Shelf) is DeclaredParentShelfType
    assert "DeclaredParentShelfFilterInputType" in FilterArgumentsFactory.input_object_types
    assert (vars(declared), declared.extra) == (state, extra)


# ---------------------------------------------------------------------------
# normalize_input_value
# ---------------------------------------------------------------------------


def test_normalize_input_value_encodes_globalid_object_to_wire_form() -> None:
    """``relay.GlobalID`` OBJECT -> base64 wire string (``type_name`` preserved).

    The object keeps its type through normalization so the bound
    ``GlobalIDFilter.filter`` can validate it before decoding; the value
    round-trips back to the original ``(type_name, node_id)``.
    """
    f = GlobalIDFilter()
    gid = relay.GlobalID(type_name="X", node_id="42")
    encoded = normalize_input_value(f, gid)
    assert encoded == str(gid)
    assert isinstance(encoded, str)
    round_tripped = relay.GlobalID.from_id(encoded)
    assert (round_tripped.type_name, round_tripped.node_id) == ("X", "42")


def test_normalize_input_value_passes_string_globalid_through() -> None:
    f = GlobalIDFilter()
    assert normalize_input_value(f, "42") == "42"


def test_normalize_input_value_unwraps_enum_member() -> None:
    """A Strawberry-enum-member input becomes its `.value`."""

    @strawberry.enum
    class Color(Enum):
        RED = "red"
        BLUE = "blue"

    f = ChoiceFilter()
    assert normalize_input_value(f, Color.RED) == "red"


def test_normalize_input_value_unwraps_enum_member_with_none_value() -> None:
    """An enum member whose ``.value`` is ``None`` unwraps to ``None``.

    The structural ``isinstance(value, enum.Enum)`` check unwraps it; a
    value-truthiness guard would return the member object un-unwrapped instead.
    """

    class Tri(Enum):
        YES = "yes"
        UNKNOWN = None

    assert normalize_input_value(ChoiceFilter(), Tri.UNKNOWN) is None


def test_normalize_input_value_range_filter_emits_its_widget_keys() -> None:
    """RangeFilter -> `{<field>_0: start, <field>_1: end}`, the keys its ``MultiWidget`` reads."""
    f = RangeFilter(field_name="lifetime_fines_cents")

    @dataclass
    class _RangeInput:
        start: int | None = 1
        end: int | None = 10

    patch = normalize_input_value(f, _RangeInput(), field_name="lifetime_fines_cents")
    assert patch == {"lifetime_fines_cents_0": 1, "lifetime_fines_cents_1": 10}


def test_normalize_input_value_range_filter_drops_none_axes_partial_range() -> None:
    """Partial-range inputs surface only the supplied key.

    A ``None``-valued axis is "axis not supplied"; emitting ``{<name>_0: None}``
    to the form-data dict surfaces "axis supplied, value is None" to any
    caller walking ``data.keys()``. The normalizer drops ``None``-valued
    axes so the patch shape matches django-filter's form-data convention
    for partial ranges.
    """
    f = RangeFilter(field_name="lifetime_fines_cents")

    @dataclass
    class _RangeInput:
        start: int | None = None
        end: int | None = None

    # Only ``start`` supplied -> single-key patch.
    only_start = normalize_input_value(
        f,
        _RangeInput(start=5),
        field_name="lifetime_fines_cents",
    )
    assert only_start == {"lifetime_fines_cents_0": 5}

    # Only ``end`` supplied -> single-key patch.
    only_end = normalize_input_value(
        f,
        _RangeInput(end=10),
        field_name="lifetime_fines_cents",
    )
    assert only_end == {"lifetime_fines_cents_1": 10}

    # Both supplied -> both-key patch (existing both-axes contract preserved).
    both = normalize_input_value(
        f,
        _RangeInput(start=5, end=10),
        field_name="lifetime_fines_cents",
    )
    assert both == {"lifetime_fines_cents_0": 5, "lifetime_fines_cents_1": 10}

    # Neither supplied -> empty patch (no positional keys at all).
    neither = normalize_input_value(
        f,
        _RangeInput(),
        field_name="lifetime_fines_cents",
    )
    assert neither == {}


def test_normalize_input_value_range_filter_drops_unset_axes_partial_range() -> None:
    """Partial-range inputs drop ``UNSET``-valued axes identically to ``None``."""
    f = RangeFilter(field_name="lifetime_fines_cents")

    @dataclass
    class _RangeInput:
        start: object = UNSET
        end: object = UNSET

    # Dataclass inputs with UNSET
    assert normalize_input_value(
        f,
        _RangeInput(start=5, end=UNSET),
        field_name="lifetime_fines_cents",
    ) == {"lifetime_fines_cents_0": 5}

    assert normalize_input_value(
        f,
        _RangeInput(start=UNSET, end=10),
        field_name="lifetime_fines_cents",
    ) == {"lifetime_fines_cents_1": 10}

    assert (
        normalize_input_value(
            f,
            _RangeInput(start=UNSET, end=UNSET),
            field_name="lifetime_fines_cents",
        )
        == {}
    )

    # Dict inputs with UNSET
    assert normalize_input_value(
        f,
        {"start": 5, "end": UNSET},
        field_name="lifetime_fines_cents",
    ) == {"lifetime_fines_cents_0": 5}

    assert normalize_input_value(
        f,
        {"start": UNSET, "end": 10},
        field_name="lifetime_fines_cents",
    ) == {"lifetime_fines_cents_1": 10}

    assert (
        normalize_input_value(
            f,
            {"start": UNSET, "end": UNSET},
            field_name="lifetime_fines_cents",
        )
        == {}
    )


def test_normalize_input_value_range_filter_unwraps_enum_members() -> None:
    """RangeFilter unwraps enum members on start and end axes."""
    f = RangeFilter(field_name="status_range")

    class StatusEnum(Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    assert normalize_input_value(
        f,
        {"start": StatusEnum.ACTIVE, "end": StatusEnum.INACTIVE},
        field_name="status_range",
    ) == {"status_range_0": "active", "status_range_1": "inactive"}


class _StartEndAttrs:
    """An object exposing ``start`` / ``end`` attributes that is neither a dict nor a dataclass."""

    start = 1
    end = 5


@pytest.mark.parametrize(
    "filter_class",
    [RangeFilter, DjangoRangeFilter],
    ids=["package", "django-filter"],
)
@pytest.mark.parametrize(
    "bad",
    [
        pytest.param([1, 5], id="list"),
        pytest.param((1, 5), id="tuple"),
        pytest.param(42, id="int"),
        pytest.param("1,5", id="str"),
        pytest.param(range(1, 5), id="python-range"),
        pytest.param(object(), id="object"),
        pytest.param(_StartEndAttrs(), id="start-end-attributes"),
        pytest.param({"from": 1, "to": 5}, id="only-unknown-keys"),
        pytest.param({"start": 1, "zzz": 5}, id="start-and-unknown-key"),
        pytest.param({"start": 1, "end": 5, "zzz": 9}, id="both-axes-and-unknown-key"),
    ],
)
def test_normalize_input_value_range_filter_rejects_a_value_it_cannot_read(
    filter_class: type[Filter],
    bad: object,
) -> None:
    """A range value that is not a ``{start, end}`` mapping or input object raises.

    Answering it with an empty or partial patch would drop the caller's
    constraint, so the error names the filter, its input and the value.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        normalize_input_value(filter_class(field_name="price"), bad, field_name="price_span")
    assert str(excinfo.value) == (
        f"{filter_class.__name__} consumes a range input with only 'start' / 'end' axes for "
        f"its 'price_span' input, but received {type(bad).__name__} {bad!r}; send a mapping "
        "or input object with 'start' / 'end' (the GraphQL schema already rejects this "
        "shape over the wire)."
    )


@pytest.mark.parametrize(
    ("widget", "keys"),
    [
        pytest.param(forms.TextInput(), "None", id="not-a-multi-widget"),
        pytest.param(
            forms.MultiWidget(widgets=(forms.TextInput, forms.TextInput, forms.TextInput)),
            "['price_span_0', 'price_span_1', 'price_span_2']",
            id="three-keys",
        ),
    ],
)
def test_range_filter_whose_widget_does_not_read_two_keys_is_refused_when_the_schema_is_built(
    widget: forms.Widget,
    keys: str,
) -> None:
    """A range filter whose widget does not read exactly two keys has no patch to send.

    The refusal comes from the input conversion the schema build runs, never from a
    request. Live: each upstream widget's keys,
    ``test_scalars_filter_api.py::test_upstream_range_filter_reads_the_keys_its_widget_reads``.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        convert_filter_to_input_annotation(
            DjangoRangeFilter(field_name="price_span", widget=widget),
            None,
        )
    assert str(excinfo.value) == (
        "RangeFilter consumes a range input for its 'price_span' input, but its form field's "
        f"widget does not read exactly two form-data keys ({keys}); give it a two-widget "
        "MultiWidget."
    )


def test_normalize_input_value_range_filter_reads_a_dict_subclass_through_the_base_slots() -> None:
    """A ``dict`` subclass is a mapping: its own ``get`` never decides the axes."""

    class _LyingDict(dict[str, object]):
        @override
        def get(self, key: object, default: object = None) -> object:
            return 999

    value = _LyingDict(start=1, end=5)
    assert normalize_input_value(RangeFilter(field_name="price"), value) == {
        "price_0": 1,
        "price_1": 5,
    }


def test_normalize_input_value_csv_range_filter_accepts_element_list() -> None:
    """The expanded ``__range`` CSV leaf still takes its element list.

    ``BaseRangeFilter`` rides the CSV arm (element-binding ``[start, end]``
    list over the wire), not the ``{start, end}`` object arm -- a list
    here is the legitimate shape, and the dict rejection for it stays
    pinned by ``test_normalize_input_value_rejects_dict_on_expanded_range_csv``.
    """

    class IntRange(BaseRangeFilter, NumberFilter):
        pass

    assert normalize_input_value(IntRange(), [1, 5], field_name="code__range") == [1, 5]


def test_normalize_input_value_global_id_list() -> None:
    """GlobalID OBJECTS keep their ``type_name`` (wire form), not bare node_ids.

    Pre-decoding to a bare ``node_id`` here stripped the type *before*
    the bound filter could validate it, so a wrong-type GlobalID object
    passed silently. The normalizer now
    re-encodes objects to the base64 wire string so
    ``GlobalIDMultipleChoiceFilter.filter`` runs the type-name check;
    the value still round-trips to the original ``(type_name, node_id)``.
    """
    f = GlobalIDMultipleChoiceFilter()
    gid_a = relay.GlobalID(type_name="X", node_id="1")
    gid_b = relay.GlobalID(type_name="X", node_id="2")
    encoded = normalize_input_value(f, [gid_a, gid_b])
    assert encoded == [str(gid_a), str(gid_b)]
    assert is_object_list(encoded)
    decoded = [relay.GlobalID.from_id(value) for value in encoded if isinstance(value, str)]
    assert [(g.type_name, g.node_id) for g in decoded] == [("X", "1"), ("X", "2")]


def test_normalize_input_value_none_returns_none() -> None:
    f = GlobalIDFilter()
    assert normalize_input_value(f, None) is None


def test_normalize_input_value_rejects_dict_on_csv_filter() -> None:
    """A mapping into a CSV filter fails loud instead of leaking its KEYS.

    The ``in`` / ``range`` arms iterate ``raw_value`` element-by-element, so
    a mapping container would splat into its keys -- a direct ``apply_sync``
    patch like ``{'start': 1, 'end': 5}`` on a ``__range`` CSV leaf would
    normalize to ``['start', 'end']``, silently swapping the caller's values
    for the mapping's keys in the form-data dict. The shape is invalid
    (the schema declares these inputs as GraphQL lists), so the normalizer
    fails loud with the typed error instead of guessing an element source.
    """

    class CharInFilter(BaseInFilter, CharFilter):
        pass

    f = CharInFilter(field_name="code", lookup_expr="in")
    with pytest.raises(ConfigurationError, match="non-list container"):
        normalize_input_value(f, {"start": 1, "end": 5})


def test_normalize_input_value_rejects_scalar_on_list_filter() -> None:
    """A scalar (string / int) into a list-consuming arm fails loud.

    A ``str`` container would iterate its CHARACTERS (``"abc"`` becoming
    ``['a', 'b', 'c']``), the same silent shape coercion as the dict-keys
    case, so the guard rejects every non-list container. The message is
    pinned byte for byte.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        normalize_input_value(ListFilter(field_name="code"), "abc")
    assert str(excinfo.value) == (
        "ListFilter consumes a list of values for its 'code' input, but received a "
        "non-list container (str 'abc') for the list input; send a list (the GraphQL "
        "schema already rejects this shape over the wire)."
    )
    with pytest.raises(ConfigurationError, match="non-list container"):
        normalize_input_value(GlobalIDMultipleChoiceFilter(), 42)


def test_normalize_input_value_rejects_dict_on_expanded_range_csv() -> None:
    """The expanded ``__range`` CSV leaf rejects a {start, end} patch shape.

    The expanded ``__range`` filter is a ``BaseCSVFilter`` (element-binding
    ``[start, end]`` list over the wire); only the package's own
    ``RangeFilter`` primitive owns the ``{start, end}`` mapping shape through
    its ``RangeField`` patch. A dict into the CSV branch must fail loud,
    never normalize its keys into the membership list.
    """

    class IntRange(BaseRangeFilter, NumberFilter):
        pass

    with pytest.raises(ConfigurationError, match="non-list container"):
        normalize_input_value(IntRange(), {"start": 1, "end": 5}, field_name="code__range")


def test_normalize_input_value_unset_returns_none() -> None:
    """``strawberry.UNSET`` is treated as "not supplied", same as ``None``.

    Defensive short-circuit at the entry to ``normalize_input_value``:
    every branch below either iterates / indexes / coerces ``raw_value``
    and would either raise ``TypeError`` (list-shaped branches) or
    silently pass the UNSET sentinel into the form-data dict
    (scalar branches). UNSET must be skipped here so every call site
    benefits, including the operator-bag inner loop and the
    ``_q_for_branch`` recursion.
    """
    for f in (GlobalIDFilter(), GlobalIDMultipleChoiceFilter()):
        assert normalize_input_value(f, UNSET) is None


# ---------------------------------------------------------------------------
# construct_search
# ---------------------------------------------------------------------------


def test_construct_search_translates_lookup_prefixes() -> None:
    """Each `^` / `=` / `@` / `$` prefix maps to its `LOOKUP_PREFIXES` lookup."""
    result = construct_search(
        {
            "^name": object(),
            "=code": object(),
            "@title": object(),
            "$pattern": object(),
            "no_prefix": object(),
        },
    )
    assert result == {
        "name": "istartswith",
        "code": "iexact",
        "title": "search",
        "pattern": "iregex",
    }
    # `no_prefix` (no prefix character) -> not in the result.
    assert "no_prefix" not in result


def test_construct_search_empty_input_returns_empty_dict() -> None:
    assert construct_search({}) == {}


# ---------------------------------------------------------------------------
# filter_input_type (Decision 11)
# ---------------------------------------------------------------------------


def test_filter_input_type_returns_lazy_type_resolving_in_the_inputs_module() -> None:
    """The `LazyType` resolves against the inputs module, with no relative-import package."""

    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    result = filter_input_type(MyFilter)
    assert isinstance(result, strawberry.LazyType)
    assert result.module == INPUTS_MODULE_PATH
    assert result.package is None


def test_filter_input_type_returns_lazy_type_named_for_the_input_class() -> None:
    """The `LazyType` names the generated input class by its runtime-computed name."""

    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    result = filter_input_type(MyFilter)
    assert isinstance(result, strawberry.LazyType)
    assert result.type_name == "MyFilterInputType"


def test_filter_input_type_records_filterset_into_helper_referenced_set() -> None:
    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    filter_input_type(MyFilter)
    assert MyFilter in _helper_referenced_filtersets


def test_filter_input_type_is_idempotent_under_repeated_calls() -> None:
    """Repeated calls converge on one ledger entry and equal `LazyType` annotations."""

    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    first = filter_input_type(MyFilter)
    second = filter_input_type(MyFilter)
    third = filter_input_type(MyFilter)
    assert _helper_referenced_filtersets == {MyFilter}
    assert isinstance(first, strawberry.LazyType)
    assert first == second
    assert second == third


def test_filter_input_type_rejects_non_filterset() -> None:
    """`int` / non-FilterSet class / `None` all raise TypeError naming the bad value."""
    with pytest.raises(TypeError) as excinfo:
        # basedpyright: the non-class value is the hostile input under test; filter_input_type
        # types the parameter as type[FilterSet]
        filter_input_type(42)  # pyright: ignore[reportArgumentType]
    assert "42" in str(excinfo.value)

    class NotAFilter:
        pass

    with pytest.raises(TypeError):
        # basedpyright: the non-FilterSet class is the hostile input under test; filter_input_type
        # types the parameter as type[FilterSet]
        filter_input_type(NotAFilter)  # pyright: ignore[reportArgumentType]

    with pytest.raises(TypeError):
        # basedpyright: the None target is the hostile input under test; filter_input_type types
        # the parameter as type[FilterSet]
        filter_input_type(None)  # pyright: ignore[reportArgumentType]


# ---------------------------------------------------------------------------
# FilterInput[...] (the type-checkable spelling of filter_input_type)
# ---------------------------------------------------------------------------


def test_filter_input_subscript_returns_the_filter_input_type_annotation() -> None:
    """`FilterInput[MyFilter]` is the same `LazyType` the call form returns."""

    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    subscripted = FilterInput[MyFilter]
    called = filter_input_type(MyFilter)
    assert isinstance(subscripted, strawberry.LazyType)
    assert subscripted.type_name == "MyFilterInputType"
    assert subscripted.module == INPUTS_MODULE_PATH
    assert subscripted == called


def test_filter_input_subscript_records_filterset_into_helper_referenced_set() -> None:
    """The subscript feeds the one ledger the finalizer's orphan check reads."""

    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    FilterInput[MyFilter]
    assert _helper_referenced_filtersets == {MyFilter}
    filter_input_type(MyFilter)
    assert _helper_referenced_filtersets == {MyFilter}


def test_filter_input_subscript_rejects_non_filterset_naming_the_subscript() -> None:
    """A non-FilterSet raises TypeError worded with the spelling the consumer wrote."""

    class NotAFilter:
        pass

    with pytest.raises(TypeError) as excinfo:
        # basedpyright: a non-FilterSet subscript is the bad input this test proves is rejected
        FilterInput[NotAFilter]  # pyright: ignore[reportInvalidTypeArguments]
    assert str(excinfo.value).startswith("FilterInput[...] requires a FilterSet subclass; got ")
    assert "NotAFilter" in str(excinfo.value)
    with pytest.raises(TypeError, match=r"^filter_input_type\(\) requires a FilterSet subclass"):
        # basedpyright: the non-FilterSet class is the hostile input under test; filter_input_type
        # types the parameter as type[FilterSet]
        filter_input_type(NotAFilter)  # pyright: ignore[reportArgumentType]
    assert _helper_referenced_filtersets == set()


class _RaisingRepr:
    """A value whose ``repr`` raises while the rejection message is being built."""

    @override
    def __repr__(self) -> str:
        raise RuntimeError("hostile __repr__")


def _filter_input_call_form(value: object) -> object:
    # basedpyright: the hostile value is the input under test; filter_input_type types the
    # parameter as type[FilterSet]
    return filter_input_type(value)  # pyright: ignore[reportArgumentType]


def _filter_input_subscript_form(value: object) -> object:
    # basedpyright: the hostile value is the input under test; FilterInput types its
    # subscript as a FilterSet subclass
    return FilterInput[value]  # pyright: ignore[reportInvalidTypeArguments]


@pytest.mark.parametrize(
    ("spell", "prefix"),
    [
        pytest.param(
            _filter_input_call_form,
            "filter_input_type() requires a FilterSet subclass; got ",
            id="call-form",
        ),
        pytest.param(
            _filter_input_subscript_form,
            "FilterInput[...] requires a FilterSet subclass; got ",
            id="subscript-form",
        ),
    ],
)
@pytest.mark.parametrize(
    ("value", "rendered"),
    [
        pytest.param(ClassReadRaises(RuntimeError), "<ClassReadRaises>", id="class-read-raises"),
        pytest.param(
            ClassReadRaises(KeyboardInterrupt),
            "<ClassReadRaises>",
            id="class-read-interrupts",
        ),
        pytest.param(ClaimsClass(type), "<ClaimsClass>", id="claims-type"),
    ],
)
def test_filter_input_helpers_type_reject_a_value_whose_class_hooks_fail(
    spell: Callable[[object], object],
    prefix: str,
    value: object,
    rendered: str,
) -> None:
    """The helpers promise ``TypeError`` for any non-FilterSet argument, whatever its hooks do.

    ``isinstance`` / ``issubclass`` fall back to the argument's ``__class__``, which can raise
    or claim a class it is not, and the message quotes the argument's ``repr``.
    """
    with pytest.raises(TypeError) as excinfo:
        spell(value)
    assert str(excinfo.value) == f"{prefix}{rendered}"
    assert _helper_referenced_filtersets == set()


@pytest.mark.parametrize(
    "spell",
    [
        pytest.param(_filter_input_call_form, id="call-form"),
        pytest.param(_filter_input_subscript_form, id="subscript-form"),
    ],
)
def test_filter_input_helpers_propagate_a_rejected_value_whose_repr_raises(
    spell: Callable[[object], object],
) -> None:
    """A rejected value's own ``__repr__`` runs to quote it, and what it raises propagates.

    The class test reads the real class and never runs a hook, but the message quotes the
    argument through ``utils/truth.py::render``, which is the value's consumer ``__repr__``.
    """
    with pytest.raises(RuntimeError, match="hostile __repr__"):
        spell(_RaisingRepr())
    assert _helper_referenced_filtersets == set()


# ---------------------------------------------------------------------------
# filter_input_type / FilterInput[...] under PEP 563 deferred annotations
# ---------------------------------------------------------------------------

_PEP563_FILTER_PROGRAM = """
from __future__ import annotations

import strawberry
from apps.library.models import Branch

from django_strawberry_framework import DjangoType
from django_strawberry_framework.filters import FilterInput, FilterSet, filter_input_type


class Pep563BranchFilter(FilterSet):
    class Meta:
        model = Branch
        fields = {"name": ["exact"]}


class Pep563BranchType(DjangoType):
    class Meta:
        model = Branch
        fields = ("id", "name")
        filterset_class = Pep563BranchFilter


@strawberry.type
class Query:
    @strawberry.field
    def by_call(self, filter: filter_input_type(Pep563BranchFilter)) -> list[Pep563BranchType]:
        return []

    @strawberry.field
    def by_optional_call(
        self,
        filter: filter_input_type(Pep563BranchFilter) | None = None,
    ) -> list[Pep563BranchType]:
        return []

    @strawberry.field
    def by_subscript(
        self,
        filter: FilterInput[Pep563BranchFilter] | None = None,
    ) -> list[Pep563BranchType]:
        return []
"""


def test_filter_input_helpers_resolve_under_pep563_deferred_annotations() -> None:
    """Every helper spelling in a ``from __future__ import annotations`` module builds its input.

    Strawberry evaluates the annotation STRING in the consumer module's globals, where the
    generated ``Pep563BranchFilterInputType`` is not a name; the helper's return must resolve
    against the inputs module, not the consumer's globals.
    """
    with consumer_module("tests_filters_pep563_consumer", _PEP563_FILTER_PROGRAM) as namespace:
        finalize_django_types()
        sdl = str(strawberry.Schema(query=consumer_query(namespace)))
    assert "byCall(filter: Pep563BranchFilterInputType!): [Pep563BranchType!]!" in sdl
    assert "byOptionalCall(filter: Pep563BranchFilterInputType = null)" in sdl
    assert "bySubscript(filter: Pep563BranchFilterInputType = null)" in sdl
    assert _helper_referenced_filtersets == {namespace["Pep563BranchFilter"]}
    assert sdl.count("input Pep563BranchFilterInputType {") == 1


def test_filter_input_type_needs_its_filterset_in_module_globals_under_pep563() -> None:
    """A ``TYPE_CHECKING``-only FilterSet import is the one name the build cannot resolve.

    The deferred annotation is the helper CALL, evaluated in the consumer's globals at schema
    build, so the FilterSet the call names must be a runtime global there. The generated input
    name never needs to be: the field declared first, over a runtime FilterSet, resolves, and
    the build fails only at the field whose FilterSet is a type-checking import.
    """
    program = """
from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry
from apps.library.models import Branch

from django_strawberry_framework import DjangoType
from django_strawberry_framework.filters import FilterSet, filter_input_type

if TYPE_CHECKING:
    from tests.filters.fixtures.filtersets import ShelfFilter


class Pep563GuardFilter(FilterSet):
    class Meta:
        model = Branch
        fields = {"name": ["exact"]}


class Pep563GuardType(DjangoType):
    class Meta:
        model = Branch
        fields = ("id", "name")
        filterset_class = Pep563GuardFilter


@strawberry.type
class Query:
    @strawberry.field
    def branches(self, filter: filter_input_type(Pep563GuardFilter) | None = None) -> list[str]:
        return []

    @strawberry.field
    def shelves(self, filter: filter_input_type(ShelfFilter) | None = None) -> list[str]:
        return []
"""
    with consumer_module("tests_filters_pep563_type_checking", program) as namespace:
        finalize_django_types()
        with pytest.raises(
            TypeError,
            match=r"^Query fields cannot be resolved\. name 'ShelfFilter' is not defined$",
        ):
            strawberry.Schema(query=consumer_query(namespace))
    assert _helper_referenced_filtersets == {namespace["Pep563GuardFilter"]}


def test_filter_input_type_resolves_each_repeated_pep563_evaluation() -> None:
    """Two resolvers re-evaluating one helper call share one input and one ledger entry."""
    program = """
from __future__ import annotations

import strawberry
from apps.library.models import Branch

from django_strawberry_framework import DjangoType
from django_strawberry_framework.filters import FilterSet, filter_input_type


class Pep563RepeatFilter(FilterSet):
    class Meta:
        model = Branch
        fields = {"name": ["exact"]}


class Pep563RepeatType(DjangoType):
    class Meta:
        model = Branch
        fields = ("id", "name")
        filterset_class = Pep563RepeatFilter


@strawberry.type
class Query:
    @strawberry.field
    def first(self, filter: filter_input_type(Pep563RepeatFilter) | None = None) -> list[str]:
        return []

    @strawberry.field
    def second(self, filter: filter_input_type(Pep563RepeatFilter) | None = None) -> list[str]:
        return []
"""
    with consumer_module("tests_filters_pep563_repeat", program) as namespace:
        finalize_django_types()
        sdl = str(strawberry.Schema(query=consumer_query(namespace)))
    assert "first(filter: Pep563RepeatFilterInputType = null): [String!]!" in sdl
    assert "second(filter: Pep563RepeatFilterInputType = null): [String!]!" in sdl
    assert sdl.count("input Pep563RepeatFilterInputType {") == 1
    assert _helper_referenced_filtersets == {namespace["Pep563RepeatFilter"]}


# ---------------------------------------------------------------------------
# _pascal_case / _camel_case naming helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "_",
        "__",
        "___",
    ],
)
def test_pascal_case_raises_for_no_word_character_input(bad: str) -> None:
    """`_pascal_case` raises rather than silently returning `""`."""
    with pytest.raises(ConfigurationError) as excinfo:
        _pascal_case(bad)
    assert repr(bad) in str(excinfo.value)


def test_pascal_case_converts_separators() -> None:
    assert _pascal_case("galaxy__name") == "GalaxyName"
    assert _pascal_case("email_must_have_at_sign") == "EmailMustHaveAtSign"


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "_",
        "__",
        "___",
    ],
)
def test_type_name_for_raises_for_no_word_character_field_path(bad: str) -> None:
    """``type_name_for`` raises rather than silently collapsing to the root name.

    The guard lives in the shared ``utils.strings.pascal_case_or_raise`` both
    ``_pascal_case`` and ``ClassBasedTypeNameMixin`` wrap, so the bag-class
    naming path in
    ``_build_input_fields`` -- which routes through ``type_name_for`` /
    ``utils.strings.pascal_case`` rather than the inputs-local
    ``_pascal_case`` -- also surfaces the no-word-character collision
    loudly instead of producing a generic ``f"{cls.__name__}InputType"``
    that silently collides with the root input type's own name.
    """

    class _Probe(ClassBasedTypeNameMixin):
        pass

    with pytest.raises(ConfigurationError) as excinfo:
        _Probe.type_name_for(bad)
    assert repr(bad) in str(excinfo.value)


def test_camel_case_returns_input_when_no_word_characters() -> None:
    """`_camel_case` returns the raw string when it has no word tokens."""
    assert _camel_case("") == ""
    assert _camel_case("_") == "_"


def test_camel_case_lowercases_head_and_pascals_rest() -> None:
    assert _camel_case("galaxy_name") == "galaxyName"


# ---------------------------------------------------------------------------
# _scalar_from_form_field - form-field -> Python scalar mapping
# ---------------------------------------------------------------------------


def test_scalar_from_form_field_maps_each_recognized_shape() -> None:
    """Every recognized form-field shape maps to its Python scalar.

    Regression pin for the ``django.forms`` hierarchy trap: ``FloatField``
    and ``DecimalField`` BOTH subclass ``IntegerField``, so they must be
    matched before the ``IntegerField`` catch - otherwise a float/decimal
    filter mis-maps to ``int``.
    """
    assert _scalar_from_form_field(forms.NullBooleanField()) is bool
    assert _scalar_from_form_field(forms.BooleanField()) is bool
    assert _scalar_from_form_field(forms.IntegerField()) is int
    assert _scalar_from_form_field(forms.FloatField()) is float
    assert _scalar_from_form_field(forms.DecimalField()) is decimal.Decimal
    assert _scalar_from_form_field(forms.DateTimeField()) is datetime.datetime
    assert _scalar_from_form_field(forms.DateField()) is datetime.date
    assert _scalar_from_form_field(forms.TimeField()) is datetime.time
    assert _scalar_from_form_field(forms.UUIDField()) is uuid.UUID
    assert _scalar_from_form_field(forms.CharField()) is str
    # Unknown shape falls through to the ``str`` catch-all.
    assert _scalar_from_form_field(forms.Field()) is str


# ---------------------------------------------------------------------------
# _scalar_from_model_field - model-field -> Python scalar mapping
# ---------------------------------------------------------------------------


def test_scalar_from_model_field_none_falls_back_to_str() -> None:
    assert _scalar_from_model_field(None) is str


def test_scalar_from_model_field_maps_each_recognized_shape() -> None:
    assert _scalar_from_model_field(models.BooleanField()) is bool
    assert _scalar_from_model_field(models.IntegerField()) is int
    assert _scalar_from_model_field(models.FloatField()) is float
    assert _scalar_from_model_field(models.DecimalField()) is decimal.Decimal
    assert _scalar_from_model_field(models.DateTimeField()) is datetime.datetime
    assert _scalar_from_model_field(models.DateField()) is datetime.date
    assert _scalar_from_model_field(models.TimeField()) is datetime.time
    assert _scalar_from_model_field(models.UUIDField()) is uuid.UUID
    # Unknown shape falls through to the ``str`` catch-all.
    assert _scalar_from_model_field(models.TextField()) is str


# ---------------------------------------------------------------------------
# convert_filter_to_input_annotation / normalize_input_value edge branches
# ---------------------------------------------------------------------------


def test_convert_filter_to_input_annotation_typed_filter_uses_model_scalar() -> None:
    """A bare ``TypedFilter`` resolves its scalar from the model field."""
    annotation = convert_filter_to_input_annotation(
        TypedFilter(field_name="lifetime_fines_cents"),
        models.IntegerField(),
        None,
    )
    # Optional wrapper around the resolved scalar.
    assert annotation == (int | None)


def test_filter_convert_and_normalize_ride_shared_kind_table() -> None:
    """Convert and normalize walk one most-specific-first filter-class table.

    Two independent ``isinstance`` chains could drift apart (spec-053 C3), so
    both zip ``_FILTER_INPUT_KIND_TYPES`` into ``convert_with_mro`` prechecks;
    ``object`` is last (the catch-all arm).
    """
    for fn in (inputs_mod.convert_filter_to_input_annotation, inputs_mod.normalize_input_value):
        assert "convert_with_mro" in fn.__code__.co_names
        assert "_filter_input_prechecks" in fn.__code__.co_names
    assert _FILTER_INPUT_KIND_TYPES[-1] is object
    assert _FILTER_INPUT_KIND_TYPES[-3] is TypedFilter
    with pytest.raises(ValueError, match="argument"):
        _filter_input_prechecks(lambda _f: None)
    exc = _unexpected_filter_dispatch(object())
    assert isinstance(exc, ConfigurationError)
    assert "internal: filter input dispatch" in str(exc)


def test_convert_raw_pk_relation_filters_type_from_the_target_key_column() -> None:
    """The raw-pk pair types from the target key column, through a one-to-one primary key.

    ``Annotation.profile`` targets ``PatronProfile``, whose key is its ``patron``
    one-to-one: the input is ``Patron.id``'s ``Int`` (a list for the multi-valued class).
    """
    relation = library_models.Annotation._meta.get_field("profile")
    single = RelationPkFilter(field_name="profile", lookup_expr="exact")
    many = RelationPkMultipleFilter(field_name="profile", lookup_expr="in")
    assert convert_filter_to_input_annotation(single, relation) == (int | None)
    assert convert_filter_to_input_annotation(many, relation) == (list[int] | None)
    assert normalize_input_value(many, (3, 4)) == [3, 4]
    with pytest.raises(ConfigurationError, match="primary-key list"):
        normalize_input_value(many, 3)


def test_convert_raw_pk_filter_on_a_non_relation_names_the_leaf_and_related_filter() -> None:
    """A raw-pk filter whose ``field_name`` is not a relation fails at input build.

    The message names the leaf and points at ``RelatedFilter``, never at ``SCALAR_MAP``.
    """
    leaf = RelationPkFilter(field_name="title", lookup_expr="exact")
    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(leaf, library_models.Book._meta.get_field("title"))
    message = str(exc_info.value)
    assert "RelationPkFilter" in message
    assert "'title'" in message
    assert "RelatedFilter" in message
    assert "SCALAR_MAP" not in message


def test_filter_overrides_model_choice_keys_keep_their_class_and_type_from_the_target_key() -> (
    None
):
    """A ``filter_overrides``-selected model-choice key stays the consumer's, typed from its column.

    ``exact`` keeps django-filter's ``ModelChoiceFilter`` and ``in`` its
    ``ConcreteInFilter(BaseInFilter, ModelChoiceFilter)`` wrapper, both still holding
    their ``queryset`` (so the form still validates) and stamped ``override_generated``,
    which keeps them out of the optimizer's candidate rows. The input is the category
    pk: one ``Int`` for ``exact``, a list for ``in``.
    """

    def _category_queryset_extra(_field: object) -> dict[str, object]:
        return {"queryset": Category.objects.all()}

    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"category": ["exact", "in"]}
            filter_overrides = {
                models.ForeignKey: {
                    "filter_class": django_filters.ModelChoiceFilter,
                    "extra": _category_queryset_extra,
                },
            }

    relation = Item._meta.get_field("category")
    exact = ItemFilter.get_filters()["category"]
    in_ = ItemFilter.get_filters()["category__in"]
    assert type(exact) is django_filters.ModelChoiceFilter
    assert isinstance(in_, DjangoBaseInFilter)
    assert isinstance(in_, django_filters.ModelChoiceFilter)
    for leaf in (exact, in_):
        assert leaf.queryset is not None
        assert leaf.queryset.model is Category
        record = filter_generation_provenance(leaf)
        assert record is not None
        assert record.origin == "override_generated"
    snapshot = ItemFilter._expansion_snapshot()
    assert snapshot is not None
    assert not {"category", "category__in"} & set(snapshot.candidates)
    assert convert_filter_to_input_annotation(exact, relation) == (int | None)
    assert convert_filter_to_input_annotation(in_, relation) == (list[int] | None)
    assert normalize_input_value(exact, 3) == 3
    assert normalize_input_value(in_, (3, 4)) == [3, 4]
    with pytest.raises(ConfigurationError, match="model-choice list"):
        normalize_input_value(in_, 3)


def test_declared_model_choice_filter_follows_a_relation_valued_primary_key() -> None:
    """A queryset whose model's key is a one-to-one types from the column that key stores.

    ``PatronProfile``'s primary key is its ``patron`` one-to-one, so the value the form
    cleans is ``Patron.id``: an ``Int``. A declared filter stays ``origin="declared"``.
    """

    class AnnotationFilter(FilterSet):
        profile = django_filters.ModelChoiceFilter(
            queryset=library_models.PatronProfile.objects.all(),
        )

        class Meta:
            model = library_models.Annotation
            fields = ["id"]

    leaf = AnnotationFilter.get_filters()["profile"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "declared"
    relation = library_models.Annotation._meta.get_field("profile")
    assert convert_filter_to_input_annotation(leaf, relation) == (int | None)


def test_model_choice_filter_with_no_column_source_names_the_filterset_and_the_fix() -> None:
    """A callable queryset on a ``method=`` filter naming no relation fails at input build.

    Neither source names a model: the callable queryset has none until a request
    arrives and ``field_name`` (``owner``) is no relation on ``Item``. The message names
    the FilterSet, the filter and both fixes, never ``SCALAR_MAP`` / ``Meta.exclude``.
    """

    def _request_categories(_request: object) -> QuerySet[Category]:
        return Category.objects.all()

    class ItemFilter(FilterSet):
        owner = django_filters.ModelChoiceFilter(
            # basedpyright: types-django-filter types ``queryset`` as a ``QuerySet``;
            # ``QuerySetRequestMixin.get_queryset`` calls a callable one with the request
            queryset=_request_categories,  # pyright: ignore[reportArgumentType]
            method="filter_owner",
        )

        class Meta:
            model = Item
            fields = ["name"]

        def filter_owner(
            self,
            queryset: QuerySet[Item],
            _name: str,
            _value: object,
        ) -> QuerySet[Item]:
            return queryset

    with pytest.raises(ConfigurationError) as exc_info:
        _build_input_fields(ItemFilter)
    message = str(exc_info.value)
    assert message.startswith("ItemFilter: ModelChoiceFilter on 'owner'")
    assert "Pass a model queryset, or point field_name at a relation." in message
    assert "SCALAR_MAP" not in message
    assert "Meta.exclude" not in message


def test_normalize_input_value_typed_filter_unwraps_none_enum_value() -> None:
    """``TypedFilter`` is convert-only; normalize continues and may return ``None``."""

    class Tri(Enum):
        UNKNOWN = None

    assert normalize_input_value(TypedFilter(), Tri.UNKNOWN) is None


def test_normalize_input_value_list_filter_unwraps_each_element() -> None:
    """``ListFilter`` / ``ArrayFilter`` values normalize element-by-element."""
    f = ListFilter(field_name="ids")
    assert normalize_input_value(
        f,
        [1, 2, 3],
        field_name="ids",
    ) == [1, 2, 3]


def test_normalize_input_value_base_csv_filter_unwraps_elements() -> None:
    """``BaseCSVFilter`` normalizes element-by-element unwrapping enum members."""

    class StatusEnum(Enum):
        A = "a"
        B = "b"

    class CSVFilter(BaseInFilter, CharFilter):
        pass

    f = CSVFilter(field_name="status")
    assert normalize_input_value(
        f,
        [StatusEnum.A, StatusEnum.B],
        field_name="status",
    ) == ["a", "b"]


def test_convert_filter_to_input_annotation_derives_enum_for_choice_fields_on_list_and_csv_filters() -> (
    None
):
    """`_element_annotation` resolves choice enum for TypedFilter, ListFilter, and BaseCSVFilter."""
    model_field: ModelField = library_models.Book._meta.get_field("circulation_status")

    # TypedFilter
    tf = TypedFilter(field_name="circulation_status")
    tf_anno = convert_filter_to_input_annotation(tf, model_field)
    tf_cls = _class_arg(tf_anno)
    assert issubclass(tf_cls, Enum)

    # ListFilter
    lf = ListFilter(field_name="circulation_status")
    lf_anno = convert_filter_to_input_annotation(lf, model_field)
    lf_list = next(arg for arg in _args(lf_anno) if arg is not type(None))
    assert get_origin(lf_list) is list
    lf_member = _args(lf_list)[0]
    assert isinstance(lf_member, type)
    assert issubclass(lf_member, Enum)

    # BaseCSVFilter
    class CSVFilter(BaseInFilter, CharFilter):
        pass

    csv_f = CSVFilter(field_name="circulation_status")
    csv_anno = convert_filter_to_input_annotation(csv_f, model_field)
    csv_list = next(arg for arg in _args(csv_anno) if arg is not type(None))
    assert get_origin(csv_list) is list
    csv_member = _args(csv_list)[0]
    assert isinstance(csv_member, type)
    assert issubclass(csv_member, Enum)


def test_element_annotation_fallback_branches_when_model_field_is_none() -> None:
    """`_element_annotation` checks form field when model_field is None, fallback to str."""

    class IntTypedFilter(TypedFilter):
        field_class = forms.IntegerField

    class NoFieldTypedFilter(TypedFilter):
        @property
        @override
        # basedpyright: deliberately a filter with no form field, the input that takes the fallback
        def field(self) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
            return None

    # Form field present -> resolved via `_scalar_from_form_field`
    assert convert_filter_to_input_annotation(IntTypedFilter(), None) == int | None

    # Neither model field nor form field -> fallback to `_scalar_from_model_field(None)` (`str`)
    assert convert_filter_to_input_annotation(NoFieldTypedFilter(), None) == str | None


def test_materialize_input_class_registers_in_module_globals() -> None:
    """`materialize_input_class` registers input classes into the module namespace."""

    class ScratchCustomInput:
        pass

    materialize_input_class("ScratchCustomInput", ScratchCustomInput)
    assert inputs_mod._materialized_names["ScratchCustomInput"] is ScratchCustomInput
    assert getattr(inputs_mod, "ScratchCustomInput", None) is ScratchCustomInput


class _EqRangeFilter(RangeFilter):
    """A ``RangeFilter`` defining ``__eq__`` without ``__hash__``, so instances are unhashable."""

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, _EqRangeFilter) and self.field_name == other.field_name

    # basedpyright: None is the runtime marker for unhashable; typeshed types the slot as a method
    __hash__ = None  # pyright: ignore[reportAssignmentType]


def _range_owner() -> type[FilterSet]:
    class RangeOwnerFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = []

    return RangeOwnerFilter


@pytest.mark.parametrize("owned", [False, True], ids=["unowned", "owned"])
def test_range_input_class_for_a_filter_defining_eq_without_hash(*, owned: bool) -> None:
    """An unhashable ``RangeFilter`` still gets its range input class.

    Owned names over HTTP:
    ``test_scalars_filter_api.py::test_range_input_types_are_scoped_per_filterset``.
    """
    owner = _range_owner() if owned else None
    cls = _build_range_input_class(_EqRangeFilter(field_name="id"), int, owner)
    assert cls.__name__ == ("RangeOwnerFilterIdRangeInputType" if owned else "IdRangeInputType")
    assert cls.__annotations__["start"] == (int | None)


def test_build_range_input_class_name_and_axes_follow_owner_field_and_scalar() -> None:
    """One filter instance gets the name and axes of each owner, field and scalar it is built for."""

    class FirstFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = []

    f = RangeFilter(field_name="price")
    owned = _build_range_input_class(f, int, FirstFilter)
    other_scalar = _build_range_input_class(f, str, FirstFilter)
    f.field_name = "cost"
    other_field = _build_range_input_class(f, int, FirstFilter)

    assert owned.__name__ == "FirstFilterPriceRangeInputType"
    assert other_scalar.__annotations__["start"] == (str | None)
    assert other_field.__name__ == "FirstFilterCostRangeInputType"


def test_finalize_accepts_a_range_filter_defining_eq_without_hash() -> None:
    """A ``Meta.filterset_class`` declaring an unhashable ``RangeFilter`` finalizes."""

    class UnhashableRangeFilter(FilterSet):
        span = _EqRangeFilter(field_name="id")

        class Meta:
            model = library_models.Branch
            fields = []

    class UnhashableRangeBranchType(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            filterset_class = UnhashableRangeFilter

    finalize_django_types()
    assert registry.get(library_models.Branch) is UnhashableRangeBranchType
    assert "UnhashableRangeFilterInputType" in FilterArgumentsFactory.input_object_types


@pytest.mark.parametrize("owned", [False, True], ids=["unowned", "owned"])
def test_range_input_class_retains_neither_filter_nor_filterset(*, owned: bool) -> None:
    """Building a range input class keeps no reference to its filter or owning filterset."""

    def build() -> tuple[weakref.ref[type[FilterSet]], weakref.ref[RangeFilter]]:
        owner = _range_owner()
        f = RangeFilter(field_name="id")
        owner.base_filters["span"] = f
        _build_range_input_class(f, int, owner if owned else None)
        return weakref.ref(owner), weakref.ref(f)

    owner_ref, filter_ref = build()
    gc.collect()
    assert owner_ref() is None
    assert filter_ref() is None


def test_filterset_is_collectable_after_finalize_and_registry_clear() -> None:
    """A finalized filterset with a ``RangeFilter`` is released by ``registry.clear()``."""

    def build() -> weakref.ref[type[FilterSet]]:
        class CollectableRangeFilter(FilterSet):
            span = RangeFilter(field_name="id")

            class Meta:
                model = library_models.Branch
                fields = []

        class CollectableRangeBranchType(DjangoType):
            class Meta:
                model = library_models.Branch
                fields = ("id", "name")
                filterset_class = CollectableRangeFilter

        finalize_django_types()
        assert registry.get(library_models.Branch) is CollectableRangeBranchType
        return weakref.ref(CollectableRangeFilter)

    ref = build()
    registry.clear()
    gc.collect()
    assert ref() is None


def test_build_range_input_class_name_unqualified_without_filterset() -> None:
    """No owning filterset -> the historical ``<Field>RangeInputType`` name is preserved.

    Live scoping of owned names:
    ``examples/fakeshop/test_query/test_scalars_filter_api.py::test_range_input_types_are_scoped_per_filterset``.
    """
    f = RangeFilter(field_name="price")
    assert _build_range_input_class(f, int).__name__ == "PriceRangeInputType"


@pytest.mark.django_db
def test_range_input_type_name_is_scoped_per_filterset() -> None:
    """Two filtersets sharing a ``field_name`` mint DISTINCT range sub-input classes.

    Pin for the spec-027 collision hazard. Shipped filtersets share one axis
    scalar, so the differing-axis claim is package-only. The nested
    ``RangeFilter`` sub-input class name derived from
    ``field_name`` alone, so two filtersets that each declare a ``RangeFilter``
    for a same-named column both stamped one GraphQL name
    (``PriceRangeInputType``), and two ranges of different axis scalars under one
    name cannot share a schema (the type-name claim,
    ``utils/inputs.py::claim_generated_type_name``, refuses the pair in any schema
    serving both). The name is qualified by the owning filterset so the two are
    distinct and both survive in one schema.
    """

    class ScalarPriceFilter(FilterSet):
        price = RangeFilter(field_name="price")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    class TextPriceFilter(FilterSet):
        # Same generated top-level ``price`` field, but a text-backed source:
        # this proves the two scoped nested types retain different axis scalars.
        price = RangeFilter(field_name="price")

        class Meta:
            model = library_models.Branch
            fields = []

    def _range_cls_of(bag: type) -> type:
        for annotation in _annotations(bag).values():
            for arg in _args(annotation):
                if isinstance(arg, type) and arg.__name__.endswith("RangeInputType"):
                    return arg
        raise AssertionError("no RangeInputType found in operator bag")

    def _bag(triples: list[tuple[str, object, dict[str, object]]]) -> type:
        by_attr = {p: a for p, a, _ in triples}
        return _class_arg(by_attr["price"])

    bag1 = _bag(_build_input_fields(ScalarPriceFilter))
    bag2 = _bag(_build_input_fields(TextPriceFilter))
    r1 = _range_cls_of(bag1)
    r2 = _range_cls_of(bag2)

    # Owning-filterset qualifier makes the two names distinct (unqualified, both
    # would be ``PriceRangeInputType``).
    assert r1.__name__ == "ScalarPriceFilterPriceRangeInputType"
    assert r2.__name__ == "TextPriceFilterPriceRangeInputType"
    assert r1.__name__ != r2.__name__
    assert r1.__annotations__["start"] != r2.__annotations__["start"]

    # Both nested range types survive when both operator bags land in one schema;
    # under one name the two could not share it.
    @strawberry.type
    class Query:
        ok: int

    sdl = str(strawberry.Schema(query=Query, types=[bag1, bag2]))
    range_defs = set(re.findall(r"input (\w*RangeInputType)", sdl))
    assert range_defs == {
        "ScalarPriceFilterPriceRangeInputType",
        "TextPriceFilterPriceRangeInputType",
    }


@pytest.mark.django_db
def test_direct_range_conversion_does_not_poison_owned_input_build() -> None:
    """An earlier unowned conversion cannot defeat owner-qualified generation."""

    class OwnedPriceFilter(FilterSet):
        price = RangeFilter(field_name="price")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    declared_filter = OwnedPriceFilter.base_filters["price"]
    model_field = scalar_models.ScalarSpecimen._meta.get_field("price")
    direct = convert_filter_to_input_annotation(declared_filter, model_field)
    direct_cls = _class_arg(direct)
    assert direct_cls.__name__ == "PriceRangeInputType"

    triples = _build_input_fields(OwnedPriceFilter)
    price_annotation = next(
        annotation for python_attr, annotation, _kwargs in triples if python_attr == "price"
    )
    bag = _class_arg(price_annotation)
    owned_cls = next(
        arg
        for annotation in _annotations(bag).values()
        for arg in _args(annotation)
        if isinstance(arg, type) and arg.__name__.endswith("RangeInputType")
    )
    assert owned_cls.__name__ == "OwnedPriceFilterPriceRangeInputType"
    assert owned_cls is not direct_cls


def test_build_input_class_threads_description_into_strawberry_field() -> None:
    """A ``description`` kwarg is forwarded to ``strawberry.field``."""
    cls = build_input_class(
        "DescribedInputType",
        [
            ("note", str | None, {"default": None, "description": "a note"}),
        ],
    )
    # The strawberry field carries the description through decoration.
    field = next(f for f in cls.__strawberry_definition__.fields if f.python_name == "note")
    assert field.description == "a note"


# ---------------------------------------------------------------------------
# _build_input_fields - RelatedFilter with an unresolved (None) target
# ---------------------------------------------------------------------------


def test_build_input_fields_skips_related_filter_with_none_target() -> None:
    """A ``RelatedFilter(None, ...)`` placeholder is skipped, not materialized."""

    class PlaceholderFilter(FilterSet):
        rel = RelatedFilter(None, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    # The None-target branch contributes no input triple but does not raise.
    triples = _build_input_fields(PlaceholderFilter)
    names = {python_attr for python_attr, _annotation, _kwargs in triples}
    assert "rel" not in names
    assert "code" in names


# ---------------------------------------------------------------------------
# Digit-boundary operator-bag / range type names
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_build_input_fields_keeps_digit_boundary_operator_bags_distinct() -> None:
    """``field_2`` / ``field2`` mint DISTINCT operator-bag GraphQL type names.

    ``ClassBasedTypeNameMixin.type_name_for`` routes through ``pascal_case``. A
    non-injective Pascal collapse (``field_2`` / ``field2`` both -> ``Field2``)
    made both bags claim ``<FilterSet>Field2FilterInputType``: two bags of
    different lookups under one name in one set, which the type-name claim
    (``utils/inputs.py::claim_generated_type_name``) refuses at finalize.
    Top-level field attrs stay distinct via ``graphql_camel_name``; the type-name
    stem must preserve the same digit boundary.
    """

    class DigitBoundaryFilter(FilterSet):
        field_2 = CharFilter(field_name="name", lookup_expr="exact")
        field2 = CharFilter(field_name="name", lookup_expr="icontains")

        class Meta:
            model = library_models.Branch
            fields = []

    assert DigitBoundaryFilter.type_name_for("field_2") == (
        "DigitBoundaryFilterField_2FilterInputType"
    )
    assert DigitBoundaryFilter.type_name_for("field2") == (
        "DigitBoundaryFilterField2FilterInputType"
    )

    triples = _build_input_fields(DigitBoundaryFilter)
    by_attr = {python_attr: annotation for python_attr, annotation, _kwargs in triples}

    def _bag(attr: str) -> type:
        return _class_arg(by_attr[attr])

    bag_underscore = _bag("field_2")
    bag_plain = _bag("field2")
    assert bag_underscore.__name__ == "DigitBoundaryFilterField_2FilterInputType"
    assert bag_plain.__name__ == "DigitBoundaryFilterField2FilterInputType"
    assert bag_underscore is not bag_plain
    assert "exact" in bag_underscore.__annotations__
    assert "i_contains" in bag_plain.__annotations__

    @strawberry.type
    class Query:
        ok: int

    # Register the bags directly (same pattern as the scoped-range collision pin);
    # a root input with ``strawberry.lazy`` self-refs needs spec-027 Decision 9 materialization.
    sdl = str(strawberry.Schema(query=Query, types=[bag_underscore, bag_plain]))
    bag_defs = set(re.findall(r"input (DigitBoundaryFilterField_?2FilterInputType)", sdl))
    assert bag_defs == {
        "DigitBoundaryFilterField_2FilterInputType",
        "DigitBoundaryFilterField2FilterInputType",
    }


@pytest.mark.django_db
def test_range_input_type_name_preserves_digit_boundary_in_field_name() -> None:
    """Range sub-input names keep ``price_2`` distinct from ``price2``."""

    class PriceDigitFilter(FilterSet):
        price_2 = RangeFilter(field_name="price_2")
        price2 = RangeFilter(field_name="price2")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    # field_name drives ``_pascal_case`` inside ``_build_range_input_class``.
    underscored = RangeFilter(field_name="price_2")
    plain = RangeFilter(field_name="price2")
    assert (
        _build_range_input_class(underscored, int, PriceDigitFilter).__name__
        == "PriceDigitFilterPrice_2RangeInputType"
    )
    assert (
        _build_range_input_class(plain, int, PriceDigitFilter).__name__
        == "PriceDigitFilterPrice2RangeInputType"
    )


@pytest.mark.django_db
def test_build_input_fields_keeps_underscore_edge_operator_bags_distinct() -> None:
    """``price`` / ``price_`` mint DISTINCT operator-bag GraphQL type names.

    A ``pascal_case`` that dropped leading / trailing underscore runs would
    collapse two members whose names differ only at the edges to one
    type-name stem even though BOTH emission guards pass (the Python attrs and
    the camel GraphQL field names stay distinct for edge variants). A
    ``CharFilter`` bag and a ``RangeFilter`` bag under one name in one set are
    two shapes the type-name claim
    (``utils/inputs.py::claim_generated_type_name``) refuses at finalize, so
    the set could not be served. The stem preserves the edge runs (the Pascal
    dual of ``graphql_camel_name``).
    """

    class UnderscoreEdgeFilter(FilterSet):
        price = CharFilter(field_name="name", lookup_expr="exact")
        price_ = RangeFilter(field_name="city", lookup_expr="exact")

        class Meta:
            model = library_models.Branch
            fields = []

    triples = _build_input_fields(UnderscoreEdgeFilter)
    by_attr = {python_attr: annotation for python_attr, annotation, _kwargs in triples}

    def _bag(attr: str) -> type:
        return _class_arg(by_attr[attr])

    bag_plain = _bag("price")
    bag_under = _bag("price_")
    assert bag_plain.__name__ == "UnderscoreEdgeFilterPriceFilterInputType"
    assert bag_under.__name__ == "UnderscoreEdgeFilterPrice_FilterInputType"
    assert bag_plain is not bag_under
    # The two bags carry DIFFERENT shapes: the CharFilter bag's ``exact`` is a
    # scalar, the RangeFilter bag's ``exact`` embeds the range sub-input.
    assert "RangeInputType" not in str(_annotations(bag_plain)["exact"])
    assert "RangeInputType" in str(_annotations(bag_under)["exact"])

    @strawberry.type
    class Query:
        ok: int

    sdl = str(strawberry.Schema(query=Query, types=[bag_plain, bag_under]))
    bag_defs = set(re.findall(r"input (UnderscoreEdgeFilterPrice_?FilterInputType)", sdl))
    assert bag_defs == {
        "UnderscoreEdgeFilterPriceFilterInputType",
        "UnderscoreEdgeFilterPrice_FilterInputType",
    }
    # The range sub-input of the trailing-underscore member survives too.
    assert "UnderscoreEdgeFilterCityRangeInputType" in sdl


@pytest.mark.django_db
def test_range_input_type_name_preserves_leading_underscore_run_in_field_name() -> None:
    """Range sub-input names keep ``_price`` distinct from ``price``."""

    class LeadingEdgeRangeFilter(FilterSet):
        price = RangeFilter(field_name="name")
        _price = RangeFilter(field_name="city")

        class Meta:
            model = library_models.Branch
            fields = []

    assert (
        _build_range_input_class(
            RangeFilter(field_name="name"),
            int,
            LeadingEdgeRangeFilter,
        ).__name__
        == "LeadingEdgeRangeFilterNameRangeInputType"
    )
    assert (
        _build_range_input_class(
            RangeFilter(field_name="city"),
            int,
            LeadingEdgeRangeFilter,
        ).__name__
        == "LeadingEdgeRangeFilterCityRangeInputType"
    )
    # The naming rule itself: the leading run survives into the stem.
    assert LeadingEdgeRangeFilter.type_name_for("_price") == (
        "LeadingEdgeRangeFilter_PriceFilterInputType"
    )
    assert LeadingEdgeRangeFilter.type_name_for("price") == (
        "LeadingEdgeRangeFilterPriceFilterInputType"
    )


# ---------------------------------------------------------------------------
# clear_filter_input_namespace - cycle-safe import guards
# ---------------------------------------------------------------------------


def test_clear_filter_input_namespace_tolerates_unimportable_submodules() -> None:
    """Both submodule lookups on the clear path are best-effort: skip, never raise.

    The heavy clear reaches ``FilterArgumentsFactory`` and ``FilterSet``
    through ``utils/inputs.py::_safe_import``, so an unimportable module
    yields ``None`` and only its dependent reset is skipped; the reachable
    ledger reset still completes (spec-027 Decision 9).
    """
    factories_name = "django_strawberry_framework.filters.factories"
    sets_name = "django_strawberry_framework.filters.sets"
    # Setting the module entry to ``None`` makes the best-effort lookup of
    # each module raise ImportError internally, exercising both skips.
    with blocked_modules(factories_name, sets_name):
        # Must not raise even though neither submodule can be imported.
        clear_filter_input_namespace()


# ---------------------------------------------------------------------------
# _iter_filterset_subclasses - diamond dedup
# ---------------------------------------------------------------------------


def test_iter_filterset_subclasses_dedupes_diamond_inheritance() -> None:
    """A diamond hierarchy surfaces each subclass once (the dedup `continue`)."""

    class A(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    class B(A):
        pass

    class C(A):
        pass

    class D(B, C):
        pass

    found = _iter_filterset_subclasses(A)
    # ``D`` is reachable through both ``B`` and ``C`` but appears once.
    assert found.count(D) == 1
    assert {B, C, D}.issubset(set(found))
