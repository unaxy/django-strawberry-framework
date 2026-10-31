"""Filter input-generation tests for lookup naming, field construction, normalization, references, and reset.

Covers the lookup-name table, the `_build_logic_fields` /
`_build_input_fields` operator-bag builders, `construct_search`,
`convert_filter_to_input_annotation` / `normalize_input_value` table
cases, `FieldSpec` source-path mapping, and the `filter_input_type`
consumer helper (Decision 11).

``test_filter_declarations_api.py`` owns borrowed flat-filter publication,
scoped ranges with differing axis scalars and published input-name boundaries.
The declaration suite also owns successful postponed helper evaluation over HTTP;
this file retains the missing runtime import construction refusal.
``test_library_api.py`` and ``test_products_api.py`` own ordinary flat-filter
hiding and Relay relation inputs. This file keeps converter dispatch,
construction-time refusal, exact input-class metadata and namespace lifecycle.

The cross-API reuse row exercises django-filter's DRF view after a refused schema
build: that failed GraphQL schema has no endpoint through which to test reuse.
"""

from __future__ import annotations

import copy
import dataclasses
import datetime
import decimal
import gc
import typing
import uuid
import weakref
from collections import OrderedDict
from collections.abc import Callable, Iterator, Mapping
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
    DateFilter,
    DateRangeFilter,
    Filter,
    LookupChoiceFilter,
    NumberFilter,
)
from django_filters import RangeFilter as DjangoRangeFilter
from django_filters.filters import BaseInFilter as DjangoBaseInFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.widgets import RangeWidget, SuffixedMultiWidget
from rest_framework import generics
from rest_framework.test import APIRequestFactory
from strawberry import relay
from strawberry.types.base import get_object_definition
from strawberry.types.field import StrawberryField
from typing_extensions import override

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    ArrayFilter,
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
    _field_specs,
    _filter_input_prechecks,
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
    range_form_keys,
)
from django_strawberry_framework.filters.sets import _widget_keys, filter_generation_provenance
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
from tests._postgres_fields import FakeArrayField, patch_array_field, real_array_of
from tests._soft_dependency import blocked_modules

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable
    from django.http import HttpRequest

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


@pytest.mark.parametrize(
    ("attr", "sequence"),
    [
        pytest.param("and_", True, id="and"),
        pytest.param("or_", True, id="or"),
        pytest.param("not_", False, id="not"),
    ],
)
def test_build_logic_fields_places_the_forward_reference_inside_its_container(
    attr: str,
    *,
    sequence: bool,
) -> None:
    """Each optional logic field has a lazy forward reference, inside a list only for sequences."""
    triples = _build_logic_fields("DemoFilterInputType")
    by_attr = {python_attr: annotation for python_attr, annotation, _kwargs in triples}
    non_none_args = [arg for arg in _args(by_attr[attr]) if arg is not type(None)]
    assert len(non_none_args) == 1
    inner = non_none_args[0]
    if sequence:
        assert get_origin(inner) is list
        inner = _args(inner)[0]
    assert get_origin(inner) is typing.Annotated or hasattr(inner, "__metadata__")
    reference = _args(inner)[0]
    assert reference == "DemoFilterInputType" or (
        read_attr(reference, "__forward_arg__", None) == "DemoFilterInputType"
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
    assert convert_filter_to_input_annotation(f, None, None, FilterSet) == str | None


def test_convert_filter_to_input_annotation_handles_globalid_multiple_choice_filter() -> None:
    f = GlobalIDMultipleChoiceFilter()
    assert convert_filter_to_input_annotation(f, None, None, FilterSet) == list[str] | None


def test_convert_filter_to_input_annotation_handles_range_filter() -> None:
    f = RangeFilter(field_name="value")
    model_field: _Int = models.IntegerField()
    annotation = convert_filter_to_input_annotation(f, model_field, None, FilterSet)
    non_none = [arg for arg in _args(annotation) if arg is not type(None)]
    assert len(non_none) == 1
    range_cls = non_none[0]
    assert hasattr(range_cls, "__strawberry_definition__")
    fields = {field.python_name for field in _definition_fields(range_cls)}
    assert fields == {"start", "end"}


def test_convert_filter_to_input_annotation_handles_list_filter() -> None:
    f = ListFilter(field_name="value")
    model_field: _Int = models.IntegerField()
    annotation = convert_filter_to_input_annotation(f, model_field, None, FilterSet)
    assert annotation == list[int] | None


@pytest.mark.parametrize(
    "make_filter",
    [
        pytest.param(
            lambda: django_filters.MultipleChoiceFilter(
                method="filter_picks",
                choices=[("a", "A")],
            ),
            id="multiple-choice",
        ),
        pytest.param(
            lambda: django_filters.TypedMultipleChoiceFilter(
                method="filter_picks",
                choices=[(1, "One")],
                coerce=int,
            ),
            id="typed-multiple-choice",
        ),
    ],
)
def test_convert_filter_to_input_annotation_types_a_columnless_multiple_choice_method_filter(
    make_filter: Callable[[], Filter],
) -> None:
    """A multiple-choice ``method=`` filter with no column is a list of its form's ``str``.

    Its ``MultipleChoiceField`` cleans a list, so the input is a list; with no model
    column the element comes from the form field, never from
    ``TypedMultipleChoiceFilter.coerce``.
    """
    assert (
        convert_filter_to_input_annotation(make_filter(), None, None, FilterSet)
        == list[str] | None
    )


def test_convert_filter_to_input_annotation_handles_choice_filter_via_converter_pipeline() -> None:
    """`ChoiceFilter` reaches into ``convert_choices_to_enum`` via the model field."""
    # ``Book.circulation_status`` is a TextChoices field on the example model.
    f = ChoiceFilter()
    model_field: ModelField = library_models.Book._meta.get_field("circulation_status")
    annotation = convert_filter_to_input_annotation(f, model_field, None, FilterSet)
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
        convert_filter_to_input_annotation(f, model_field, None, FilterSet)


def test_convert_filter_to_input_annotation_malformed_filter_diagnostics() -> None:
    """Malformed filters raise ConfigurationError naming the method and the filter."""

    class NoFieldFilter(Filter):
        @property
        @override
        def field(self) -> forms.Field:
            raise AttributeError("This consumer field cannot be built.")

    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(
            NoFieldFilter(method="filter_custom"),
            None,
            None,
            FilterSet,
        )
    assert str(exc_info.value).startswith("NoFieldFilter(method='filter_custom') on <")
    assert "exposes no form field" in str(exc_info.value)

    # ``AllValuesMultipleFilter`` reads the per-request ``model`` to build its field, so
    # unbound it builds none; the refusal advises the two spellings that build one.
    unbound = AllValuesMultipleFilter(field_name="city", method="filter_custom")
    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(unbound, None, None, FilterSet)
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
        convert_filter_to_input_annotation(choice_filter, model_field, None, FilterSet)
    assert str(exc_info.value) == (
        f"{type(choice_filter).__name__} on {choice_filter!r} is backed by no model field "
        "declaring `choices` (the filter's own `choices` never feed the enum); declare "
        "`choices` on the column it filters (a `choices=` list of pairs, or a `TextChoices` / "
        "`IntegerChoices` class's `.choices`), or filter that column through a non-choice filter "
        "(`CharFilter`, `NumberFilter`, `DateFromToRangeFilter`, its lookups in Meta.fields, "
        "or `CharFilter(method=...)` for a method filter)."
    )


def test_convert_filter_to_input_annotation_wraps_nullable() -> None:
    """``extra['required']=False`` (the default) wraps the annotation in `T | None`."""
    f = CharFilter()
    annotation = convert_filter_to_input_annotation(f, models.CharField(), None, FilterSet)
    assert annotation == str | None


def test_convert_filter_to_input_annotation_does_not_wrap_required() -> None:
    f = CharFilter(required=True)
    annotation = convert_filter_to_input_annotation(f, models.CharField(), None, FilterSet)
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


# ---------------------------------------------------------------------------
# Refused one-value filters whose widget reads other form-data keys
# ---------------------------------------------------------------------------


class _PairField(forms.MultiValueField):
    """A consumer ``MultiValueField`` over two text parts, read through a two-widget ``MultiWidget``."""

    widget = forms.MultiWidget(widgets=[forms.TextInput(), forms.TextInput()])

    def __init__(self, *, label: str | None = None, required: bool = False) -> None:
        super().__init__(
            fields=[forms.CharField(), forms.CharField()],
            label=label,
            required=required,
        )

    @override
    def compress(self, data_list: list[object]) -> object:
        return data_list


class _PairFilter(Filter):
    """A consumer ``Filter`` whose ``field_class`` is a ``MultiValueField``."""

    field_class = _PairField


_NUMERIC_RANGE_KEYS = "<name>_min, <name>_max"
_NUMERIC_RANGE_NOTE = (
    " A NumericRangeFilter filters a PostgreSQL range column, which the schema does not publish."
)

_OTHER_KEY_WIDGET_DECLARATIONS = [
    pytest.param(
        lambda: django_filters.NumericRangeFilter(field_name="price"),
        _NUMERIC_RANGE_KEYS,
        _NUMERIC_RANGE_NOTE,
        id="numeric-range",
    ),
    pytest.param(
        lambda: django_filters.NumericRangeFilter(field_name="price", lookup_expr="range"),
        _NUMERIC_RANGE_KEYS,
        _NUMERIC_RANGE_NOTE,
        id="numeric-range-range-lookup",
    ),
    pytest.param(
        lambda: django_filters.NumericRangeFilter(field_name="price", lookup_expr="contains"),
        _NUMERIC_RANGE_KEYS,
        _NUMERIC_RANGE_NOTE,
        id="numeric-range-contains-lookup",
    ),
    pytest.param(
        lambda: django_filters.NumericRangeFilter(field_name="price", method="filter_value"),
        _NUMERIC_RANGE_KEYS,
        _NUMERIC_RANGE_NOTE,
        id="numeric-range-method",
    ),
    pytest.param(
        lambda: _PairFilter(field_name="label"),
        "<name>_0, <name>_1",
        "",
        id="multi-value-field",
    ),
    pytest.param(
        lambda: CharFilter(field_name="label", widget=RangeWidget()),
        "<name>_min, <name>_max",
        "",
        id="char-suffixed-multi-widget",
    ),
    pytest.param(
        lambda: CharFilter(
            field_name="label",
            widget=forms.MultiWidget(widgets=[forms.TextInput(), forms.TextInput()]),
        ),
        "<name>_0, <name>_1",
        "",
        id="char-multi-widget",
    ),
    pytest.param(
        lambda: django_filters.ModelChoiceFilter(
            field_name="label",
            # basedpyright: types-django-filter types ``queryset`` as a ``QuerySet``;
            # ``ModelChoiceField`` takes a ``Manager`` as one
            queryset=scalar_models.ScalarSpecimen.objects,  # pyright: ignore[reportArgumentType]
            widget=forms.MultiWidget(widgets=[forms.Select(), forms.Select()]),
        ),
        "<name>_0, <name>_1",
        "",
        id="model-choice-manager-multi-widget",
    ),
]


def _specimen_set(declared: Filter) -> type[FilterSet]:
    """A package ``FilterSet`` over ``ScalarSpecimen`` declaring ``declared`` as ``value``."""

    class SpecimenValueSet(FilterSet):
        value = declared

        def filter_value(
            self,
            queryset: QuerySet[scalar_models.ScalarSpecimen],
            _name: str,
            _value: object,
        ) -> QuerySet[scalar_models.ScalarSpecimen]:
            return queryset

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    return SpecimenValueSet


@pytest.mark.parametrize(("declare", "keys", "note"), _OTHER_KEY_WIDGET_DECLARATIONS)
def test_a_one_value_filter_whose_widget_reads_other_keys_is_refused_when_the_schema_is_built(
    declare: Callable[[], Filter],
    keys: str,
    note: str,
) -> None:
    """A filter published as one value whose widget never reads that value's key refuses.

    The value is written under the filter's own form-data key and the widget reads only its
    own keys, so the filter would answer every request with every row. No fakeshop FilterSet
    can declare one: its schema would refuse to build.
    """
    declared = declare()
    _serve_model(scalar_models.ScalarSpecimen, _specimen_set(declared))

    assert _build_refusal() == (
        f"SpecimenValueSet: {type(declared).__name__} on {declared.field_name!r} publishes one "
        "value under its form-data key <name>, but its form field's widget reads "
        f"{keys}, so the value would never be read. Declare a RangeFilter (the package's or "
        "django-filter's) for a two-bound range, or give the filter a form field whose widget "
        f"reads one key.{note}"
    )


def test_a_model_choice_filter_with_a_request_scoped_queryset_builds_without_calling_it() -> None:
    """The widget check never builds a form field whose ``queryset`` waits for the request.

    The callable raises when called, so the schema building proves nothing called it.
    """

    def _no_request_yet(_request: HttpRequest | None) -> QuerySet[library_models.Shelf]:
        raise AssertionError

    declared = django_filters.ModelChoiceFilter(
        field_name="shelf",
        # basedpyright: types-django-filter types ``queryset`` as a ``QuerySet``;
        # ``QuerySetRequestMixin.get_queryset`` calls a callable one with the request
        queryset=_no_request_yet,  # pyright: ignore[reportArgumentType]
    )

    class BookShelfChoiceSet(FilterSet):
        shelf = declared

        class Meta:
            model = library_models.Book
            fields = []

    _serve_model(library_models.Book, BookShelfChoiceSet)

    finalize_django_types()
    assert "shelf" in filter_lookup_table(BookShelfChoiceSet).by_input_attr


class _CustomizingFilterSet(FilterSet):
    """A filter set overriding ``__init__``, so a ``RelatedFilter`` projects each of its filters."""

    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[models.Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)


@dataclass(frozen=True)
class _LeafRefusalCase:
    """One schema-build refusal a child set's ``leaf`` reaches, expanded or served directly.

    ``expanded`` is the message's subject for a ``RelatedFilter`` copy of ``leaf`` (projected
    or rebound) and ``direct`` for ``leaf`` on the set the schema serves, formatted with the
    sets' names (``child``, ``parent``) and the ``repr`` of the child set's own ``leaf``
    (``declared``); ``rest`` follows either subject.
    """

    declare: Callable[[], Filter]
    expanded: str
    direct: str
    rest: str


_LEAF_REFUSAL_CASES = {
    "lookup-choice": _LeafRefusalCase(
        lambda: LookupChoiceFilter(field_name="code", field_class=forms.CharField),
        "{child}.leaf: LookupChoiceFilter on 'code' (reached through {parent}.shelf)",
        "{child}: LookupChoiceFilter on 'code'",
        " filters by a value and a lookup read from two form-data keys, and no GraphQL input "
        "carries that pair. List the lookups in Meta.fields dict form (one input field per "
        "lookup), or keep the filter on a FilterSet the schema does not serve.",
    ),
    "relation-pk": _LeafRefusalCase(
        lambda: RelationPkFilter(field_name="code", lookup_expr="exact"),
        "{child}.leaf: RelationPkFilter on 'code' (reached through {parent}.shelf)",
        "{child}: RelationPkFilter on 'code'",
        ", which is not a relation to a model on its FilterSet; name a relation key in "
        "Meta.fields, or filter the related row's own fields through a RelatedFilter.",
    ),
    "model-choice": _LeafRefusalCase(
        lambda: django_filters.ModelChoiceFilter(field_name="code"),
        "{child}.leaf: ModelChoiceFilter on 'code' (reached through {parent}.shelf)",
        "{child}: ModelChoiceFilter on 'code'",
        " has no model queryset (its queryset is callable or unset) and its field_name names "
        "no relation on the FilterSet model, so there is no column to type its input from. "
        "Pass a model queryset, or point field_name at a relation.",
    ),
    "choice": _LeafRefusalCase(
        lambda: ChoiceFilter(field_name="topic", choices=[("a", "A")]),
        "ChoiceFilter on {declared} ({child}.leaf, reached through {parent}.shelf)",
        "ChoiceFilter on {declared}",
        " is backed by no model field declaring `choices` (the filter's own `choices` never "
        "feed the enum); declare `choices` on the column it filters (a `choices=` list of "
        "pairs, or a `TextChoices` / `IntegerChoices` class's `.choices`), or filter that "
        "column through a non-choice filter (`CharFilter`, `NumberFilter`, "
        "`DateFromToRangeFilter`, its lookups in Meta.fields, or `CharFilter(method=...)` for "
        "a method filter).",
    ),
    "range-widget": _LeafRefusalCase(
        lambda: DjangoRangeFilter(field_name="tier", widget=forms.TextInput()),
        "RangeFilter consumes a range input for its 'shelf__tier' input ({child}.leaf, "
        "reached through {parent}.shelf)",
        "RangeFilter consumes a range input for its 'tier' input",
        ", but its form field's widget does not read exactly two form-data keys (None); give "
        "it a two-widget MultiWidget.",
    ),
    "other-key-widget": _LeafRefusalCase(
        lambda: django_filters.NumericRangeFilter(field_name="tier"),
        "{child}.leaf: NumericRangeFilter on 'tier' (reached through {parent}.shelf)",
        "{child}: NumericRangeFilter on 'tier'",
        " publishes one value under its form-data key <name>, but its form field's widget "
        "reads <name>_min, <name>_max, so the value would never be read. Declare a "
        "RangeFilter (the package's or django-filter's) for a two-bound range, or give the "
        "filter a form field whose widget reads one key. A NumericRangeFilter filters a "
        "PostgreSQL range column, which the schema does not publish.",
    ),
    "method-without-field": _LeafRefusalCase(
        lambda: AllValuesMultipleFilter(field_name="topic", method="filter_leaf"),
        "AllValuesMultipleFilter(method='filter_leaf') on {declared} ({child}.leaf, reached "
        "through {parent}.shelf)",
        "AllValuesMultipleFilter(method='filter_leaf') on {declared}",
        " exposes no form field; put the method on a typed filter primitive "
        "(`CharFilter(method=...)`, `NumberFilter(method=...)`, `ListFilter(method=...)` for "
        "a list value, ...) or on a `Filter` subclass declaring `field_class` at class level.",
    ),
}


def _shelf_leaf_set(declared: Filter, base: type[FilterSet]) -> type[FilterSet]:
    """A ``Shelf`` set on ``base`` declaring ``declared`` as ``leaf``.

    ``ShelfLeafFilter.filter_leaf`` is the method a ``method=`` leaf names.
    """

    class ShelfLeafFilter(base):
        leaf = declared

        def filter_leaf(
            self,
            queryset: QuerySet[library_models.Shelf],
            _name: str,
            _value: object,
        ) -> QuerySet[library_models.Shelf]:
            return queryset

        class Meta:
            model = library_models.Shelf
            fields = []

    return ShelfLeafFilter


def _book_shelf_set(child: type[FilterSet], base: type[FilterSet]) -> type[FilterSet]:
    """A ``Book`` set on ``base`` expanding ``child`` through ``shelf``."""

    class BookLeafFilter(base):
        shelf = RelatedFilter(child, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = []

    return BookLeafFilter


def _serve_model(model: type[models.Model], served: type[FilterSet] | None) -> None:
    """Declare a ``DjangoType`` for ``model`` whose ``Meta.filterset_class`` is ``served``."""
    meta: dict[str, object] = {"model": model, "fields": ("id",)}
    if served is not None:
        meta["filterset_class"] = served
    _ = type(f"{model.__name__}LeafType", (DjangoType,), {"Meta": type("Meta", (), meta)})


def _build_refusal() -> str:
    """Build the schema and return the ``ConfigurationError`` message it refuses with."""
    with pytest.raises(ConfigurationError) as excinfo:
        finalize_django_types()
    return str(excinfo.value)


@pytest.mark.parametrize(
    "base",
    [FilterSet, _CustomizingFilterSet],
    ids=["plain-child", "child-init"],
)
@pytest.mark.parametrize("site", list(_LEAF_REFUSAL_CASES))
def test_an_expanded_child_leaf_is_refused_under_its_declaration(
    site: str,
    base: type[FilterSet],
) -> None:
    """A refusal reached through a ``RelatedFilter`` copy names the filter the child set declares.

    The copy is rebound onto the parent (``shelf__code``), or projected as a runtime-built
    ``Projected<Class>`` when an owner binds the child leaf (its set overrides ``__init__``,
    or the leaf holds a ``method=``); either way the message names the declared class, its
    attribute on the child set, its own ``field_name`` and the ``RelatedFilter`` it was
    reached through, never the copy.
    """
    case = _LEAF_REFUSAL_CASES[site]
    declared = case.declare()
    child = _shelf_leaf_set(declared, base)
    parent = _book_shelf_set(child, FilterSet)
    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, parent)
    assert child.get_filters()["leaf"] is declared

    subject = case.expanded.format(
        child=child.__name__,
        parent=parent.__name__,
        declared=repr(declared),
    )
    assert _build_refusal() == subject + case.rest


@pytest.mark.parametrize("site", list(_LEAF_REFUSAL_CASES))
def test_a_leaf_on_the_set_it_is_served_from_is_refused_under_its_own_name(site: str) -> None:
    """A leaf declared on the served set itself is named as every root filter is.

    No ``RelatedFilter`` copied it, so the refusal names its own class, its set and its
    own ``field_name``, with no attribute or route.
    """
    case = _LEAF_REFUSAL_CASES[site]
    declared = case.declare()
    child = _shelf_leaf_set(declared, _CustomizingFilterSet)
    _serve_model(library_models.Shelf, child)

    subject = case.direct.format(child=child.__name__, declared=repr(declared))
    assert _build_refusal() == subject + case.rest


@pytest.mark.parametrize(
    ("shelf_base", "book_base"),
    [
        pytest.param(_CustomizingFilterSet, FilterSet, id="projected-then-projected"),
        pytest.param(FilterSet, FilterSet, id="rebound-then-rebound"),
        pytest.param(FilterSet, _CustomizingFilterSet, id="projected-over-a-rebound-copy"),
    ],
)
def test_a_leaf_expanded_across_two_hops_names_every_hop(
    shelf_base: type[FilterSet],
    book_base: type[FilterSet],
) -> None:
    """A copy expanded again names each ``RelatedFilter`` it was reached through.

    ``LoanLeafFilter.book`` expands ``BookLeafFilter``'s copy ``shelf__leaf`` again; each
    hop is projected or rebound by its own set, and a projected copy of a rebound copy walks
    through it. The refusal names ``ShelfLeafFilter.leaf`` and both hops, outermost first.
    """
    child = _shelf_leaf_set(
        LookupChoiceFilter(field_name="code", field_class=forms.CharField),
        shelf_base,
    )
    book_filter = _book_shelf_set(child, book_base)

    class LoanLeafFilter(FilterSet):
        book = RelatedFilter(book_filter, field_name="book")

        class Meta:
            model = library_models.Loan
            fields = []

    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, None)
    _serve_model(library_models.Loan, LoanLeafFilter)

    assert _build_refusal() == (
        f"{child.__name__}.leaf: LookupChoiceFilter on 'code' (reached through "
        f"LoanLeafFilter.book, then {book_filter.__name__}.shelf) filters by a value and a "
        "lookup read from two form-data keys, and no GraphQL input carries that pair. List "
        "the lookups in Meta.fields dict form (one input field per lookup), or keep the "
        "filter on a FilterSet the schema does not serve."
    )


def _deep_copying(parent: type[FilterSet], *, rekey: bool) -> type[FilterSet]:
    """``parent`` under a ``get_filters()`` override returning a deep copy of every filter.

    When ``rekey`` each copy ``shelf__<name>`` is held as ``aliased_<name>`` instead.
    """

    class DeepCopyingFilter(parent):
        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            return OrderedDict(
                (
                    f"aliased_{name.removeprefix('shelf__')}"
                    if rekey and name.startswith("shelf__")
                    else name,
                    copy.deepcopy(filter_instance),
                )
                for name, filter_instance in super().get_filters().items()
            )

    return DeepCopyingFilter


@pytest.mark.parametrize("rekey", [False, True], ids=["deep-copies", "deep-copies-rekeyed"])
@pytest.mark.parametrize(
    "base",
    [FilterSet, _CustomizingFilterSet],
    ids=["plain-child", "child-init"],
)
@pytest.mark.parametrize("site", list(_LEAF_REFUSAL_CASES))
def test_a_get_filters_override_keeps_an_expanded_leaf_refused_under_its_declaration(
    site: str,
    base: type[FilterSet],
    *,
    rekey: bool,
) -> None:
    """A ``get_filters()`` override deep-copying the copies, under its keys or keys of its own.

    Each copy carries the child filter it stands for, so the refusal still names the
    declared class, its attribute on the child set and the ``RelatedFilter`` it was
    reached through, never the parent set and the flat ``field_name``.
    """
    case = _LEAF_REFUSAL_CASES[site]
    declared = case.declare()
    child = _shelf_leaf_set(declared, base)
    parent = _deep_copying(_book_shelf_set(child, FilterSet), rekey=rekey)
    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, parent)
    assert ("aliased_leaf" in parent.get_filters()) is rekey

    subject = case.expanded.format(
        child=child.__name__,
        parent=parent.__name__,
        declared=repr(declared),
    )
    assert _build_refusal() == subject + case.rest


@pytest.mark.parametrize(
    ("shelf_base", "book_base"),
    [
        pytest.param(_CustomizingFilterSet, FilterSet, id="projected-then-projected"),
        pytest.param(FilterSet, FilterSet, id="rebound-then-rebound"),
        pytest.param(FilterSet, _CustomizingFilterSet, id="projected-over-a-rebound-copy"),
    ],
)
def test_a_leaf_expanded_across_a_deep_copying_middle_set_names_every_hop(
    shelf_base: type[FilterSet],
    book_base: type[FilterSet],
) -> None:
    """The middle set's ``get_filters()`` deep-copies its copies; the refusal still names both hops.

    ``LoanLeafFilter.book`` expands the deep copy of ``shelf__leaf`` the middle set
    returns, which carries the child filter it stands for, so the walk reaches
    ``ShelfLeafFilter.leaf`` through both ``RelatedFilter`` hops, outermost first.
    """
    child = _shelf_leaf_set(
        LookupChoiceFilter(field_name="code", field_class=forms.CharField),
        shelf_base,
    )
    book_filter = _deep_copying(_book_shelf_set(child, book_base), rekey=False)

    class LoanLeafFilter(FilterSet):
        book = RelatedFilter(book_filter, field_name="book")

        class Meta:
            model = library_models.Loan
            fields = []

    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, None)
    _serve_model(library_models.Loan, LoanLeafFilter)

    assert _build_refusal() == (
        f"{child.__name__}.leaf: LookupChoiceFilter on 'code' (reached through "
        f"LoanLeafFilter.book, then {book_filter.__name__}.shelf) filters by a value and a "
        "lookup read from two form-data keys, and no GraphQL input carries that pair. List "
        "the lookups in Meta.fields dict form (one input field per lookup), or keep the "
        "filter on a FilterSet the schema does not serve."
    )


def test_a_borrowed_copy_is_refused_as_its_borrowers_own_filter() -> None:
    """A set declaring another set's rebound copy is refused naming itself and the flat ``field_name``.

    ``Borrower.aliased`` is the object ``BookLeafFilter.get_filters()`` holds as
    ``shelf__leaf``; ``Borrower`` expands no ``shelf`` branch, so the copy is its own
    filter there and the refusal names it as every root filter is named.
    """
    child = _shelf_leaf_set(
        LookupChoiceFilter(field_name="code", field_class=forms.CharField),
        FilterSet,
    )
    borrowed = _book_shelf_set(child, FilterSet).get_filters()["shelf__leaf"]

    class Borrower(FilterSet):
        aliased = borrowed

        class Meta:
            model = library_models.Book
            fields = []

    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, Borrower)

    assert _build_refusal() == (
        "Borrower: LookupChoiceFilter on 'shelf__code' filters by a value and a lookup read "
        "from two form-data keys, and no GraphQL input carries that pair. List the lookups in "
        "Meta.fields dict form (one input field per lookup), or keep the filter on a "
        "FilterSet the schema does not serve."
    )


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


def _multiple_choice_in_filter() -> Filter:
    """The ``in`` wrapper ``filter_for_lookup`` builds around a ``MultipleChoiceFilter``.

    django-filter builds it at runtime as ``ConcreteInFilter(BaseInFilter, <filter_class>)``.
    """
    in_class: type[Filter] = type(
        "MultipleChoiceInFilter",
        (BaseInFilter, django_filters.MultipleChoiceFilter),
        {},
    )
    return in_class(field_name="code", lookup_expr="in")


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


@pytest.mark.parametrize(
    "filter_class",
    [CharFilter, NumberFilter, BooleanFilter],
    ids=["char", "number", "boolean"],
)
def test_a_catch_all_leaf_whose_form_field_cannot_be_built_fails_the_schema_build(
    filter_class: type[Filter],
) -> None:
    """The catch-all builds every leaf's form field when the schema is built, method or not.

    ``lookup=`` is no filter keyword, so it rides ``extra`` into the form field class,
    which refuses it: the build raises then, never on each request through the set.
    """

    class BadKwargShelfFilter(FilterSet):
        code_like = filter_class(field_name="code", lookup="icontains")

        class Meta:
            model = library_models.Shelf
            fields = []

    class BadKwargShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            filterset_class = BadKwargShelfFilter

    assert registry.get(library_models.Shelf) is BadKwargShelfType
    with pytest.raises(TypeError, match="lookup"):
        finalize_django_types()


def _bases(*classes: type) -> tuple[type, ...]:
    """The bases of a class built at runtime, as django-filter builds its ``in`` wrapper."""
    return classes


def _input_shape(annotation: object) -> object:
    """``annotation`` with a generated range input class read as its axis names."""
    member = _class_arg(annotation)
    if get_object_definition(member) is None:
        return member
    return sorted(field.python_name for field in _definition_fields(member))


@pytest.mark.parametrize(
    ("parent", "value"),
    [
        pytest.param(RangeFilter, {"start": "a", "end": "h"}, id="range"),
        pytest.param(ChoiceFilter, "good", id="choice"),
        pytest.param(TypedFilter, "good", id="typed"),
    ],
)
def test_a_consumer_class_pairing_multiple_choice_with_another_kind_keeps_that_kinds_arm(
    parent: type[Filter],
    value: object,
) -> None:
    """``MultipleChoiceFilter`` is last before the catch-all, so the other kind's arm wins.

    A consumer class with two bases is typed and normalized as its other base is,
    never as the multiple-choice list.
    """
    paired = type(
        f"{parent.__name__}MultipleChoiceFilter",
        _bases(parent, django_filters.MultipleChoiceFilter),
        {},
    )
    both = paired(field_name="condition")
    assert isinstance(both, Filter)
    assert isinstance(both, django_filters.MultipleChoiceFilter)
    model_field: ModelField = library_models.Shelf._meta.get_field("condition")
    single = parent(field_name="condition")

    assert _input_shape(
        convert_filter_to_input_annotation(both, model_field, None, FilterSet),
    ) == _input_shape(
        convert_filter_to_input_annotation(single, model_field, None, FilterSet),
    )
    assert normalize_input_value(both, value, field_name="condition") == normalize_input_value(
        single,
        value,
        field_name="condition",
    )


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


class _LowHighWidget(SuffixedMultiWidget):
    """A two-box range widget reading ``<name>_low`` / ``<name>_high``."""

    suffixes = ["low", "high"]

    def __init__(self, attrs: dict[str, object] | None = None) -> None:
        super().__init__((forms.TextInput, forms.TextInput), attrs)


class _FieldWidgetRangeFilter(DjangoRangeFilter):
    """django-filter's ``RangeFilter`` whose ``field`` property installs ``_LowHighWidget``."""

    @property
    @override
    def field(self) -> forms.Field:
        field = super().field
        field.widget = _LowHighWidget()
        return field


class _ParentReadingRangeFilter(DjangoRangeFilter):
    """A ``RangeFilter`` whose ``field`` reads the bound ``FilterSet`` it runs in."""

    @property
    @override
    def field(self) -> forms.Field:
        _ = read_attr(self, "parent")
        return super().field


def test_range_and_flat_copy_keys_read_a_field_override_on_a_copy() -> None:
    """Both key readers ask the field the filter's own class builds; the declaration keeps none.

    ``range_form_keys`` (the range input's keys) and ``_widget_keys`` (the flat copy's
    keys) read ``_LowHighWidget`` off the overriding ``field``, and the class-level
    declaration every request deep-copies holds no cached ``_field`` afterwards.
    """
    declared = _FieldWidgetRangeFilter(field_name="price")

    assert range_form_keys(declared, "span") == ("span_low", "span_high")
    assert _widget_keys(declared, "span") == ["span_low", "span_high"]
    assert "_field" not in vars(declared)


def test_range_form_keys_of_a_field_built_only_in_a_bound_set_is_a_configuration_error() -> None:
    """A ``field`` that reads ``self.parent`` builds nothing at schema build: a ``ConfigurationError``."""
    with pytest.raises(ConfigurationError, match="built only inside a bound FilterSet"):
        _ = range_form_keys(_ParentReadingRangeFilter(field_name="price"), "span")


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        pytest.param(5, None, {"lifetime_fines_cents_0": 5}, id="start"),
        pytest.param(None, 10, {"lifetime_fines_cents_1": 10}, id="end"),
        pytest.param(
            5,
            10,
            {"lifetime_fines_cents_0": 5, "lifetime_fines_cents_1": 10},
            id="both",
        ),
        pytest.param(None, None, {}, id="neither"),
    ],
)
def test_normalize_input_value_range_filter_drops_none_axes_partial_range(
    start: int | None,
    end: int | None,
    expected: dict[str, int],
) -> None:
    """A partial-range patch names only supplied axes, retaining both when both are supplied."""
    f = RangeFilter(field_name="lifetime_fines_cents")

    @dataclass
    class _RangeInput:
        start: int | None = None
        end: int | None = None

    assert (
        normalize_input_value(
            f,
            _RangeInput(start=start, end=end),
            field_name="lifetime_fines_cents",
        )
        == expected
    )


@pytest.mark.parametrize("mapping", [False, True], ids=["input-object", "mapping"])
@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        pytest.param(5, UNSET, {"lifetime_fines_cents_0": 5}, id="start"),
        pytest.param(UNSET, 10, {"lifetime_fines_cents_1": 10}, id="end"),
        pytest.param(UNSET, UNSET, {}, id="neither"),
    ],
)
def test_normalize_input_value_range_filter_drops_unset_axes_partial_range(
    start: object,
    end: object,
    expected: dict[str, int],
    *,
    mapping: bool,
) -> None:
    """Mapping and input-object patches omit UNSET axes without adding positional null keys."""
    f = RangeFilter(field_name="lifetime_fines_cents")

    @dataclass
    class _RangeInput:
        start: object = UNSET
        end: object = UNSET

    value = {"start": start, "end": end} if mapping else _RangeInput(start=start, end=end)
    assert (
        normalize_input_value(
            f,
            value,
            field_name="lifetime_fines_cents",
        )
        == expected
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
        pytest.param((1, 5), id="tuple"),
        pytest.param(range(1, 5), id="python-range"),
        pytest.param(object(), id="object"),
        pytest.param(_StartEndAttrs(), id="start-end-attributes"),
    ],
)
def test_range_filters_reject_python_values_without_mapping_or_input_protocol(
    filter_class: type[Filter],
    bad: object,
) -> None:
    """Python-only tuple, range and object protocols cannot masquerade as range mappings.

    This retains the exact rejection of an opaque object and an attribute-only object;
    neither is a JSON value or a generated input. Wire mapping and list refusals live in
    the consumer raw-argument HTTP tests.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        normalize_input_value(filter_class(field_name="price"), bad, field_name="price_span")
    assert str(excinfo.value) == (
        f"{filter_class.__name__} consumes a range input with only 'start' / 'end' axes for "
        f"its 'price_span' input, but received {type(bad).__name__} {bad!r}; send a mapping "
        "or input object with 'start' / 'end' (generated filter inputs reject this "
        "shape during GraphQL validation)."
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
            None,
            FilterSet,
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

    Pre-decoding to a bare ``node_id`` here would strip the type *before*
    the bound filter could validate it, so a wrong-type GlobalID object
    would pass silently. The normalizer
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
        "non-list container (str 'abc') for the list input; send a list (generated "
        "filter inputs deliver a list after GraphQL coercion)."
    )
    with pytest.raises(ConfigurationError, match="non-list container"):
        normalize_input_value(GlobalIDMultipleChoiceFilter(), 42)


@pytest.mark.parametrize(
    ("make_filter", "shape"),
    [
        pytest.param(
            lambda: django_filters.MultipleChoiceFilter(field_name="code"),
            "multiple-choice list",
            id="multiple-choice",
        ),
        pytest.param(
            lambda: django_filters.TypedMultipleChoiceFilter(field_name="code"),
            "multiple-choice list",
            id="typed-multiple-choice",
        ),
        pytest.param(
            lambda: AllValuesMultipleFilter(field_name="code"),
            "multiple-choice list",
            id="all-values-multiple",
        ),
        pytest.param(
            _multiple_choice_in_filter,
            "CSV membership list",
            id="in-wrapper",
        ),
    ],
)
def test_normalize_input_value_rejects_scalar_on_multiple_choice_filter(
    make_filter: Callable[[], Filter],
    shape: str,
) -> None:
    """A multiple-choice filter refuses a non-list; an ``in`` wrapper around one keeps the CSV arm.

    The form field cleans a list, so a ``str`` would iterate its characters; the guard
    refuses it naming the arm that read it.
    """
    made = make_filter()
    with pytest.raises(ConfigurationError) as excinfo:
        normalize_input_value(made, "abc")
    assert str(excinfo.value) == (
        f"{type(made).__name__} consumes a list of values for its 'code' input, but received "
        f"a non-list container (str 'abc') for the {shape}; send a list "
        "(generated filter inputs deliver a list after GraphQL coercion)."
    )


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


@pytest.mark.parametrize(
    "filter_class",
    [GlobalIDFilter, GlobalIDMultipleChoiceFilter],
    ids=["single", "multiple"],
)
def test_normalize_input_value_unset_returns_none(filter_class: type[Filter]) -> None:
    """``strawberry.UNSET`` is treated as "not supplied", same as ``None``.

    Defensive short-circuit at the entry to ``normalize_input_value``:
    every branch below either iterates / indexes / coerces ``raw_value``
    and would either raise ``TypeError`` (list-shaped branches) or
    silently pass the UNSET sentinel into the form-data dict
    (scalar branches). UNSET must be skipped here so every call site
    benefits, including the operator-bag inner loop and the
    ``_q_for_branch`` recursion.
    """
    assert normalize_input_value(filter_class(), UNSET) is None


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


# ---------------------------------------------------------------------------
# _pascal_case / type_name_for naming guards
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


# ---------------------------------------------------------------------------
# _scalar_from_form_field - form-field -> Python scalar mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field_class", "expected"),
    [
        pytest.param(forms.NullBooleanField, bool, id="nullable-boolean"),
        pytest.param(forms.BooleanField, bool, id="boolean"),
        pytest.param(forms.IntegerField, int, id="integer"),
        pytest.param(forms.FloatField, float, id="float"),
        pytest.param(forms.DecimalField, decimal.Decimal, id="decimal"),
        pytest.param(forms.DateTimeField, datetime.datetime, id="datetime"),
        pytest.param(forms.DateField, datetime.date, id="date"),
        pytest.param(forms.TimeField, datetime.time, id="time"),
        pytest.param(forms.UUIDField, uuid.UUID, id="uuid"),
        pytest.param(forms.CharField, str, id="text"),
        pytest.param(forms.Field, str, id="generic-fallback"),
    ],
)
def test_scalar_from_form_field_maps_each_recognized_shape(
    field_class: type[forms.Field],
    expected: type[object],
) -> None:
    """Each form field maps to its scalar, including float and decimal before their integer base."""
    assert _scalar_from_form_field(field_class()) is expected


# ---------------------------------------------------------------------------
# _scalar_from_model_field - model-field -> Python scalar mapping
# ---------------------------------------------------------------------------


def test_scalar_from_model_field_none_falls_back_to_str() -> None:
    assert _scalar_from_model_field(None) is str


@pytest.mark.parametrize(
    ("field_class", "expected"),
    [
        pytest.param(models.BooleanField, bool, id="boolean"),
        pytest.param(models.IntegerField, int, id="integer"),
        pytest.param(models.FloatField, float, id="float"),
        pytest.param(models.DecimalField, decimal.Decimal, id="decimal"),
        pytest.param(models.DateTimeField, datetime.datetime, id="datetime"),
        pytest.param(models.DateField, datetime.date, id="date"),
        pytest.param(models.TimeField, datetime.time, id="time"),
        pytest.param(models.UUIDField, uuid.UUID, id="uuid"),
        pytest.param(models.TextField, str, id="text"),
    ],
)
def test_scalar_from_model_field_maps_each_recognized_shape(
    field_class: type[models.Field[object, object]],
    expected: type[object],
) -> None:
    """Each model field reads its scalar from the shared model-field converter."""
    assert _scalar_from_model_field(field_class()) is expected


# ---------------------------------------------------------------------------
# convert_filter_to_input_annotation / normalize_input_value edge branches
# ---------------------------------------------------------------------------


def test_convert_filter_to_input_annotation_typed_filter_uses_model_scalar() -> None:
    """A bare ``TypedFilter`` resolves its scalar from the model field."""
    annotation = convert_filter_to_input_annotation(
        TypedFilter(field_name="lifetime_fines_cents"),
        models.IntegerField(),
        None,
        FilterSet,
    )
    # Optional wrapper around the resolved scalar.
    assert annotation == (int | None)


@pytest.mark.parametrize(
    "function",
    [inputs_mod.convert_filter_to_input_annotation, inputs_mod.normalize_input_value],
    ids=["convert", "normalize"],
)
def test_filter_convert_and_normalize_ride_shared_kind_table(
    function: Callable[..., object],
) -> None:
    """Convert and normalize walk one most-specific-first filter-class table.

    Two independent ``isinstance`` chains could drift apart (spec-053 C3), so
    both zip ``_FILTER_INPUT_KIND_TYPES`` into ``convert_with_mro`` prechecks;
    ``object`` is last (the catch-all arm).
    """
    names = function.__code__.co_names
    assert "convert_with_mro" in names
    assert "_filter_input_prechecks" in names
    assert _FILTER_INPUT_KIND_TYPES[-1] is object
    assert _FILTER_INPUT_KIND_TYPES[-4] is TypedFilter
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
    assert convert_filter_to_input_annotation(single, relation, None, FilterSet) == (int | None)
    assert convert_filter_to_input_annotation(many, relation, None, FilterSet) == (
        list[int] | None
    )
    assert normalize_input_value(many, (3, 4)) == [3, 4]
    with pytest.raises(ConfigurationError, match="primary-key list"):
        normalize_input_value(many, 3)


def test_convert_raw_pk_filter_on_a_non_relation_names_the_leaf_and_related_filter() -> None:
    """A raw-pk filter whose ``field_name`` is not a relation fails at input build.

    The message names the leaf and points at ``RelatedFilter``, never at ``SCALAR_MAP``.
    """
    leaf = RelationPkFilter(field_name="title", lookup_expr="exact")
    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(
            leaf,
            library_models.Book._meta.get_field("title"),
            None,
            FilterSet,
        )
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
    pk: one ``Int`` for ``exact``, a list for ``in``. The tuple normalization
    below is a Python carrier observation; raw scalar refusal and real form
    acceptance live in
    ``test_filter_normalizer_arguments_api.py::test_a_model_choice_membership_override_keeps_its_json_container_contract``.
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
    assert convert_filter_to_input_annotation(exact, relation, None, ItemFilter) == (int | None)
    assert convert_filter_to_input_annotation(in_, relation, None, ItemFilter) == (
        list[int] | None
    )
    assert normalize_input_value(exact, 3) == 3
    assert normalize_input_value(in_, (3, 4)) == [3, 4]


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
    assert convert_filter_to_input_annotation(leaf, relation, None, AnnotationFilter) == (
        int | None
    )


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
    """A bare ``TypedFilter`` normalizes as a scalar, which may be ``None``."""

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
    tf_anno = convert_filter_to_input_annotation(tf, model_field, None, FilterSet)
    tf_cls = _class_arg(tf_anno)
    assert issubclass(tf_cls, Enum)

    # ListFilter
    lf = ListFilter(field_name="circulation_status")
    lf_anno = convert_filter_to_input_annotation(lf, model_field, None, FilterSet)
    lf_list = next(arg for arg in _args(lf_anno) if arg is not type(None))
    assert get_origin(lf_list) is list
    lf_member = _args(lf_list)[0]
    assert isinstance(lf_member, type)
    assert issubclass(lf_member, Enum)

    # BaseCSVFilter
    class CSVFilter(BaseInFilter, CharFilter):
        pass

    csv_f = CSVFilter(field_name="circulation_status")
    csv_anno = convert_filter_to_input_annotation(csv_f, model_field, None, FilterSet)
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
        def field(self) -> forms.Field:
            raise AttributeError("This consumer field cannot be built.")

    # Form field present -> resolved via `_scalar_from_form_field`
    assert (
        convert_filter_to_input_annotation(IntTypedFilter(), None, None, FilterSet) == int | None
    )

    # Neither model field nor form field -> fallback to `_scalar_from_model_field(None)` (`str`)
    assert (
        convert_filter_to_input_annotation(NoFieldTypedFilter(), None, None, FilterSet)
        == str | None
    )


def test_materialize_input_class_registers_in_module_globals() -> None:
    """`materialize_input_class` registers input classes into the module namespace."""

    class ScratchCustomInput:
        pass

    try:
        materialize_input_class("ScratchCustomInput", ScratchCustomInput)
        assert inputs_mod._materialized_names["ScratchCustomInput"] is ScratchCustomInput
        assert getattr(inputs_mod, "ScratchCustomInput", None) is ScratchCustomInput
    finally:
        inputs_mod._materialized_names.pop("ScratchCustomInput", None)
        if hasattr(inputs_mod, "ScratchCustomInput"):
            delattr(inputs_mod, "ScratchCustomInput")


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


def test_range_input_class_for_a_filter_defining_eq_without_hash() -> None:
    """An unhashable ``RangeFilter`` still gets its range input class.

    Owned names over HTTP:
    ``test_scalars_filter_api.py::test_range_input_types_are_scoped_per_filterset``.
    """
    cls = _build_range_input_class(_EqRangeFilter(field_name="id"), int, _range_owner())
    assert cls.__name__ == "RangeOwnerFilterIdRangeInputType"
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


def test_range_input_class_retains_neither_filter_nor_filterset() -> None:
    """Building a range input class keeps no reference to its filter or owning filterset."""

    def build() -> tuple[weakref.ref[type[FilterSet]], weakref.ref[RangeFilter]]:
        owner = _range_owner()
        f = RangeFilter(field_name="id")
        owner.base_filters["span"] = f
        _build_range_input_class(f, int, owner)
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


def test_build_range_input_class_qualifies_the_field_fallback_stem_by_its_set() -> None:
    """A range with no ``field_name`` takes the ``Field`` stem, still qualified by its set.

    Live scoping of owned names:
    ``examples/fakeshop/test_query/test_scalars_filter_api.py::test_range_input_types_are_scoped_per_filterset``.
    """

    class StemFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = []

    assert _build_range_input_class(RangeFilter(), int, StemFilter).__name__ == (
        "StemFilterFieldRangeInputType"
    )


@pytest.mark.django_db
def test_direct_range_conversion_does_not_poison_owned_input_build() -> None:
    """An earlier conversion under another set cannot defeat owner-qualified generation."""

    class OwnedPriceFilter(FilterSet):
        price = RangeFilter(field_name="price")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    declared_filter = OwnedPriceFilter.base_filters["price"]
    model_field = scalar_models.ScalarSpecimen._meta.get_field("price")
    direct = convert_filter_to_input_annotation(declared_filter, model_field, None, FilterSet)
    direct_cls = _class_arg(direct)
    assert direct_cls.__name__ == "FilterSetPriceRangeInputType"

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
# ArrayFilter / ListFilter over an ArrayField column: typed from its element column
# ---------------------------------------------------------------------------


class _ArraySpecimen(models.Model):
    """One ``ArrayField`` column per element shape an ``ArrayFilter`` / ``ListFilter`` reads.

    Schema-build only (``managed = False``): no row is ever read. ``ints`` holds plain
    integers, ``tiers`` integers with element ``choices``, ``flagged`` carries ``choices`` on
    the array itself, and ``grid`` is an array of arrays.
    """

    ints = FakeArrayField(models.IntegerField())
    tiers = FakeArrayField(models.IntegerField(choices=[(1, "Bronze"), (2, "Silver")]))
    flagged = FakeArrayField(models.IntegerField(), choices=[(1, "one"), (2, "two")])
    grid = FakeArrayField(FakeArrayField(models.IntegerField()))

    class Meta:
        managed = False
        app_label = "test_filter_array_elements"


_ARRAY_FILTER_CLASSES = [
    pytest.param(ArrayFilter, id="array-filter"),
    pytest.param(ListFilter, id="list-filter"),
]
_ARRAY_COLUMN_EXPOSURE = [
    pytest.param(True, id="column-on-the-type"),
    pytest.param(False, id="column-off-the-type"),
]


def _serve_array_filter(declared: Filter, *, exposed: bool) -> type[DjangoType]:
    """Serve a set declaring ``declared`` as ``arr`` and return the serving type.

    ``exposed`` puts the column ``declared`` filters on the serving ``DjangoType``'s
    ``Meta.fields`` beside ``id``.
    """
    column = declared.field_name

    class ArraySpecimenFilter(FilterSet):
        arr = declared

        class Meta:
            model = _ArraySpecimen
            fields = []

    meta: dict[str, object] = {
        "model": _ArraySpecimen,
        "fields": ("id", column) if exposed else ("id",),
        "filterset_class": ArraySpecimenFilter,
    }
    return type("ArraySpecimenType", (DjangoType,), {"Meta": type("Meta", (), meta)})


def _list_member(annotation: object) -> object:
    """The member type of ``list[X]`` / ``list[X] | None``, failing on any other shape."""
    listed = annotation
    if get_origin(annotation) is not list:
        (listed,) = (arg for arg in _args(annotation) if arg is not type(None))
    assert get_origin(listed) is list, annotation
    (member,) = _args(listed)
    return member


def _served_arr_element(served: type[DjangoType]) -> object:
    """Build the schema and return the element type of the served set's ``arr`` input."""
    finalize_django_types()
    assert registry.get(_ArraySpecimen) is served
    input_cls = FilterArgumentsFactory.input_object_types["ArraySpecimenFilterInputType"]
    bag = _class_arg(_annotations(input_cls)["arr"])
    (annotation,) = _annotations(bag).values()
    return _list_member(annotation)


@pytest.mark.parametrize("exposed", _ARRAY_COLUMN_EXPOSURE)
@pytest.mark.parametrize("filter_class", _ARRAY_FILTER_CLASSES)
def test_an_array_column_filter_is_typed_from_its_element_column(
    monkeypatch: pytest.MonkeyPatch,
    filter_class: type[Filter],
    *,
    exposed: bool,
) -> None:
    """A list filter over ``ArrayField(IntegerField())`` takes ``list[int]``.

    Each list member is one element of the array, so the input reads the element column
    (``utils/_array_field.py::array_element_field``), never the array itself, which has no
    ``SCALAR_MAP`` entry; the read side types the same column ``list[int]``.
    """
    patch_array_field(monkeypatch)
    served = _serve_array_filter(filter_class(field_name="ints"), exposed=exposed)

    assert _served_arr_element(served) is int


@pytest.mark.parametrize("exposed", _ARRAY_COLUMN_EXPOSURE)
@pytest.mark.parametrize("filter_class", _ARRAY_FILTER_CLASSES)
def test_an_array_column_filter_shares_the_element_choice_enum(
    monkeypatch: pytest.MonkeyPatch,
    filter_class: type[Filter],
    *,
    exposed: bool,
) -> None:
    """Element ``choices`` type each member as the column's one enum, the read side's included.

    The enum is cached per element column (its model and name), so the filter input and a
    ``DjangoType`` reading ``tiers`` publish the same enum class.
    """
    patch_array_field(monkeypatch)
    served = _serve_array_filter(filter_class(field_name="tiers"), exposed=exposed)

    element = _served_arr_element(served)
    enum_cls = registry.get_enum(_ArraySpecimen, "tiers")
    assert enum_cls is not None
    assert element is enum_cls
    if exposed:
        assert _list_member(_annotations(served)["tiers"]) is enum_cls


@pytest.mark.parametrize("filter_class", _ARRAY_FILTER_CLASSES)
def test_an_array_column_filter_never_reads_the_arrays_own_choices(
    monkeypatch: pytest.MonkeyPatch,
    filter_class: type[Filter],
) -> None:
    """``choices`` on the array column itself feed no enum: each member keeps the element type.

    The read side refuses to publish such a column, so it stays off the type, and the
    filter still filters it by element.
    """
    patch_array_field(monkeypatch)
    served = _serve_array_filter(filter_class(field_name="flagged"), exposed=False)

    assert _served_arr_element(served) is int
    assert registry.get_enum(_ArraySpecimen, "flagged") is None


@pytest.mark.parametrize("filter_class", _ARRAY_FILTER_CLASSES)
def test_an_array_column_filter_refuses_a_nested_array_as_the_read_side_does(
    monkeypatch: pytest.MonkeyPatch,
    filter_class: type[Filter],
) -> None:
    """An array of arrays is refused with the read side's own message, column off the type."""
    patch_array_field(monkeypatch)
    _ = _serve_array_filter(filter_class(field_name="grid"), exposed=False)

    assert _build_refusal() == "Nested ArrayField on _ArraySpecimen.grid is not supported."


@pytest.mark.parametrize(
    ("declare", "lookup"),
    [
        pytest.param(lambda: CharFilter(field_name="ints"), "exact", id="scalar-exact"),
        pytest.param(
            lambda: ListFilter(field_name="ints", lookup_expr="in"),
            "in",
            id="list-in",
        ),
        pytest.param(
            lambda: ArrayFilter(field_name="ints", lookup_expr="gt"),
            "gt",
            id="array-gt",
        ),
        pytest.param(
            lambda: DjangoRangeFilter(field_name="ints"),
            "range",
            id="range",
        ),
    ],
)
def test_an_array_column_filter_whose_lookup_takes_no_element_array_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    declare: Callable[[], Filter],
    lookup: str,
) -> None:
    """Only a list filter whose lookup takes one array of the column's elements builds.

    A scalar filter hands the ORM one element where the column compares a whole array, and
    ``in`` / ``gt`` / ``range`` compare the column with arrays, so an element-typed input
    would build and then fail every value at the database.
    """
    patch_array_field(monkeypatch)
    declared = declare()
    _ = _serve_array_filter(declared, exposed=True)

    assert _build_refusal() == (
        f"{type(declared).__name__} on {declared!r} has no input type for "
        f"lookup '{lookup}' on the ArrayField column _ArraySpecimen.ints: only exact, "
        "contains, contained_by and overlap take one array of the column's elements. Declare "
        "an ArrayFilter with one of those lookup_expr values."
    )


def test_a_choice_filter_over_an_outer_choices_array_column_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``ChoiceFilter`` over an array never builds its enum from the array's own ``choices``.

    The read side refuses those choices as ambiguous, so the filter refuses the column too.
    """
    patch_array_field(monkeypatch)
    declared = ChoiceFilter(field_name="flagged")
    _ = _serve_array_filter(declared, exposed=False)

    assert _build_refusal() == (
        f"ChoiceFilter on {declared!r} has no input type for lookup 'exact' on the ArrayField "
        "column _ArraySpecimen.flagged: only exact, contains, contained_by and overlap take one "
        "array of the column's elements. Declare an ArrayFilter with one of those lookup_expr "
        "values."
    )
    assert registry.get_enum(_ArraySpecimen, "flagged") is None


def _served_arr_annotation(served: type[DjangoType]) -> object:
    """Build the schema and return the served set's ``arr`` leaf annotation, ``None`` stripped."""
    finalize_django_types()
    assert registry.get(_ArraySpecimen) is served
    input_cls = FilterArgumentsFactory.input_object_types["ArraySpecimenFilterInputType"]
    bag = _class_arg(_annotations(input_cls)["arr"])
    (annotation,) = _annotations(bag).values()
    (member,) = (arg for arg in _args(annotation) if arg is not type(None))
    return member


@pytest.mark.parametrize(
    "declare",
    [
        pytest.param(
            lambda: ListFilter(field_name="ints__0", lookup_expr="in"),
            id="index-in",
        ),
        pytest.param(
            lambda: ArrayFilter(field_name="ints__0_2", lookup_expr="exact"),
            id="slice-exact",
        ),
        pytest.param(
            lambda: ArrayFilter(field_name="grid__0", lookup_expr="exact"),
            id="nested-index-exact",
        ),
    ],
)
def test_a_list_filter_through_an_index_or_slice_is_typed_from_the_element_column(
    monkeypatch: pytest.MonkeyPatch,
    declare: Callable[[], Filter],
) -> None:
    """A declared path through an array's index or slice is typed from what it reaches.

    The path names no model field, so each member is typed from the transform's output
    (``filters/base.py::_filterset_value_field``), never the declared form field's
    ``String``: an index of ``ArrayField(IntegerField())`` is one integer, a slice an
    array of them, and an index of an array of arrays an array of integers.
    """
    patch_array_field(monkeypatch)
    served = _serve_array_filter(declare(), exposed=False)

    assert _served_arr_element(served) is int


def test_a_list_filter_through_an_index_shares_the_element_choice_enum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An index of an array whose elements declare ``choices`` takes the column's one enum."""
    patch_array_field(monkeypatch)
    served = _serve_array_filter(
        ListFilter(field_name="tiers__0", lookup_expr="in"),
        exposed=False,
    )

    element = _served_arr_element(served)
    enum_cls = registry.get_enum(_ArraySpecimen, "tiers")
    assert enum_cls is not None
    assert element is enum_cls


def test_a_scalar_filter_through_an_index_is_typed_from_the_element_column(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``NumberFilter`` through an index is the element's ``Int``, never its form's ``Decimal``."""
    patch_array_field(monkeypatch)
    declared = NumberFilter(field_name="ints__0", lookup_expr="gte")
    served = _serve_array_filter(declared, exposed=False)

    assert _served_arr_annotation(served) is int


@pytest.mark.parametrize(
    "declare",
    [
        pytest.param(lambda: NumberFilter(field_name="ints", lookup_expr="len"), id="lookup-len"),
        pytest.param(lambda: NumberFilter(field_name="ints__len"), id="path-len"),
    ],
)
def test_a_filter_through_an_array_len_is_typed_and_compares_the_length(
    monkeypatch: pytest.MonkeyPatch,
    declare: Callable[[], Filter],
) -> None:
    """``len``, in the ``lookup_expr`` or the path, is the transform's ``Int``, never refused.

    The value is compared with the array's element count (``len``'s ``IntegerField``
    output), so the input is typed from it and the predicate compares the length.
    """
    patch_array_field(monkeypatch)
    declared = declare()
    served = _serve_array_filter(declared, exposed=False)

    assert _served_arr_annotation(served) is int
    applied = declared.filter(_ArraySpecimen.objects.all(), 3)
    assert 'LENGTH("test_filter_array_elements__arrayspecimen"."ints") = 3' in str(applied.query)


@pytest.mark.parametrize(
    ("transform", "bound"),
    [pytest.param("year", int, id="year"), pytest.param("date", datetime.date, id="date")],
)
def test_two_ranges_over_one_column_mint_one_range_type_per_value_path(
    transform: str,
    bound: type,
) -> None:
    """A ``range`` and a ``<transform>__range`` over one column are two range types in one set.

    Each is stemmed on the ``field_name`` plus the ``lookup_expr``'s transforms, so the
    column's ``DateTime`` bounds and the transform's output bounds never claim one name.
    """

    class TwoRangeFilter(FilterSet):
        stamps_span = RangeFilter(field_name="occurred_at", lookup_expr="range")
        years_span = RangeFilter(field_name="occurred_at", lookup_expr=f"{transform}__range")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    meta: dict[str, object] = {
        "model": scalar_models.ScalarSpecimen,
        "fields": ("id",),
        "filterset_class": TwoRangeFilter,
    }
    _ = type("TwoRangeType", (DjangoType,), {"Meta": type("Meta", (), meta)})
    finalize_django_types()
    input_cls = FilterArgumentsFactory.input_object_types["TwoRangeFilterInputType"]
    ranges: dict[str, object] = {}
    for name in ("stamps_span", "years_span"):
        (annotation,) = _annotations(_class_arg(_annotations(input_cls)[name])).values()
        range_cls = _class_arg(annotation)
        ranges[range_cls.__name__] = _class_arg(_annotations(range_cls)["start"])

    assert ranges == {
        "TwoRangeFilterOccurredAtRangeInputType": datetime.datetime,
        f"TwoRangeFilterOccurredAt{transform.title()}RangeInputType": bound,
    }


def test_a_range_whose_axes_clean_two_kinds_is_refused_naming_the_filter() -> None:
    """A range form whose two axes clean different scalars has no one type for both bounds.

    A ``date`` axis on ``year`` cannot clean the ``Int`` output, and the range input carries
    one type for both bounds, so the build refuses the filter instead of publishing a bound
    one of the axes cannot clean.
    """

    class MixedAxesFilter(FilterSet):
        # django-filter hands a filter's extra kwargs to its ``RangeField``, ``fields`` included.
        years_span = DjangoRangeFilter(
            field_name="occurred_on__year",
            fields=(forms.DateField(), forms.IntegerField()),
        )

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    meta: dict[str, object] = {
        "model": scalar_models.ScalarSpecimen,
        "fields": ("id",),
        "filterset_class": MixedAxesFilter,
    }
    _ = type("MixedAxesType", (DjangoType,), {"Meta": type("Meta", (), meta)})
    with pytest.raises(ConfigurationError) as excinfo:
        finalize_django_types()

    message = str(excinfo.value)
    assert "MixedAxesFilter" in message, message
    assert "RangeFilter on 'occurred_on__year'" in message, message
    assert "different kinds (date, int)" in message, message


@pytest.mark.parametrize(
    ("declare", "lookup"),
    [
        pytest.param(lambda: NumberFilter(field_name="ints", lookup_expr="0"), "0", id="index"),
        pytest.param(
            lambda: ArrayFilter(field_name="ints", lookup_expr="0_2__exact"),
            "0_2__exact",
            id="slice",
        ),
    ],
)
def test_an_index_or_slice_opening_the_lookup_expr_is_refused_by_name(
    monkeypatch: pytest.MonkeyPatch,
    declare: Callable[[], Filter],
    lookup: str,
) -> None:
    """A lookup that is no GraphQL field name is a ``ConfigurationError``, never a ``SyntaxError``.

    The operator bag publishes each lookup as an input field named by it, which an index or
    slice opening the ``lookup_expr`` cannot be; the refusal names the field_name spelling.
    """
    patch_array_field(monkeypatch)
    declared = declare()
    _ = _serve_array_filter(declared, exposed=False)

    assert _build_refusal() == (
        f"{type(declared).__name__} on {declared!r} publishes lookup '{lookup}', which is no "
        "GraphQL field name. Spell an index or slice in field_name (`<column>__0`, "
        "`<column>__0_2`) and name the lookup in lookup_expr."
    )


def test_a_list_filter_through_a_slice_of_nested_arrays_is_refused_as_the_read_side_does(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A slice of an array of arrays reaches the nested array, refused with the read side's message."""
    patch_array_field(monkeypatch)
    _ = _serve_array_filter(
        ArrayFilter(field_name="grid__0_2", lookup_expr="exact"),
        exposed=False,
    )

    assert _build_refusal() == "Nested ArrayField on _ArraySpecimen.grid is not supported."


def test_a_declared_date_filter_through_a_nested_array_index_keeps_the_array_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An index of an array of arrays reaches an array, which no single date input compares.

    django-filter builds no filter for the inner array, so nothing says the declared
    ``DateField`` cleans a value of it: the leaf keeps the transform's output and the
    array refusal answers, never a ``Date`` input the column cannot compare.
    """
    patch_array_field(monkeypatch)
    declared = DateFilter(field_name="grid__0")
    _ = _serve_array_filter(declared, exposed=False)

    assert _build_refusal() == (
        f"DateFilter on {declared!r} has no input type for lookup 'exact' on the ArrayField "
        "column _ArraySpecimen.grid: only exact, contains, contained_by and overlap take one "
        "array of the column's elements. Declare an ArrayFilter with one of those "
        "lookup_expr values."
    )


def test_a_list_filter_through_a_real_array_index_or_slice_is_typed_from_the_element_column() -> (
    None
):
    """A real ``ArrayField``'s index and slice type each member from ``base_field``.

    Django's own ``IndexTransform`` and ``SliceTransform`` answer the output field: an
    index ``in`` and a slice ``exact`` over ``ArrayField(IntegerField())`` both take
    ``[Int!]``. Runs where ``django.contrib.postgres`` imports (the PostgreSQL tier).
    """
    counts = real_array_of(models.IntegerField())

    class CountedRow(models.Model):
        counts_column = counts

        class Meta:
            managed = False
            app_label = "test_filter_real_array_paths"

    class CountedRowFilter(FilterSet):
        first_among = ListFilter(field_name="counts_column__0", lookup_expr="in")
        first_two = ArrayFilter(field_name="counts_column__0_2", lookup_expr="exact")

        class Meta:
            model = CountedRow
            fields = []

    meta: dict[str, object] = {
        "model": CountedRow,
        "fields": ("id",),
        "filterset_class": CountedRowFilter,
    }
    _ = type("CountedRowType", (DjangoType,), {"Meta": type("Meta", (), meta)})
    finalize_django_types()
    input_cls = FilterArgumentsFactory.input_object_types["CountedRowFilterInputType"]
    for name in ("first_among", "first_two"):
        bag = _class_arg(_annotations(input_cls)[name])
        (annotation,) = _annotations(bag).values()
        assert _list_member(annotation) is int, name
