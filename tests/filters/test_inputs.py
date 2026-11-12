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
import math
import typing
import uuid
import weakref
from collections import OrderedDict
from collections.abc import Callable, Iterable, Iterator, Mapping, Sized
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType, SimpleNamespace
from typing import (
    TYPE_CHECKING,
    NamedTuple,
    Protocol,
    TypeAlias,
    get_args,
    get_origin,
    runtime_checkable,
)

import django_filters
import pytest
import pytest_django
import strawberry
from apps.library import models as library_models
from apps.products.models import Category, Item
from apps.scalars import models as scalar_models
from django import forms
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import QuerySet
from django.db.models.functions import ExtractYear
from django.db.models.lookups import Exact, GreaterThan, GreaterThanOrEqual
from django.http import HttpRequest
from django.test.utils import isolate_apps, register_lookup
from django.utils.choices import CallableChoiceIterator
from django.utils.functional import SimpleLazyObject, lazy
from django_filters import (
    AllValuesFilter,
    AllValuesMultipleFilter,
    BaseInFilter,
    BaseRangeFilter,
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    DateFilter,
    DateFromToRangeFilter,
    DateRangeFilter,
    DateTimeFilter,
    DateTimeFromToRangeFilter,
    DurationFilter,
    Filter,
    LookupChoiceFilter,
    MultipleChoiceFilter,
    NumberFilter,
    TimeFilter,
    TimeRangeFilter,
    TypedChoiceFilter,
    TypedMultipleChoiceFilter,
    UUIDFilter,
)
from django_filters import RangeFilter as DjangoRangeFilter
from django_filters.filters import BaseCSVFilter as DjangoBaseCSVFilter
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
from django_strawberry_framework.filters.base import (
    RelationPkFilter,
    RelationPkMultipleFilter,
    _lookup_operand,
    _model_lookup_operand,
    copied_filter,
    defers_choices,
)
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
    lookup_leaf_names,
    materialize_input_class,
    normalize_input_value,
    range_form_keys,
)
from django_strawberry_framework.filters.sets import (
    _is_filterset_class,
    _widget_keys,
    filter_generation_provenance,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.sets_mixins import ClassBasedTypeNameMixin
from django_strawberry_framework.types import converters as converters_mod
from django_strawberry_framework.types.finalizer import finalize_django_types
from django_strawberry_framework.utils._narrowing import dict_of, read_attr, require
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.utils.typing import object_result
from tests._cleaned_filter_sets import cleaned_specimen
from tests._generated_inputs import keyword_constructor as _keyword_constructor
from tests._idioms import (
    ClaimsClass,
    ClassReadRaises,
    ModelSerializerBase,
    consumer_module,
    consumer_query,
    is_object_list,
)
from tests._info import make_info
from tests._postgres_fields import FakeArrayField, patch_array_field, real_array_of
from tests._relation_fixtures import RpCompositeChild, RpCompositeParent
from tests._soft_dependency import blocked_modules

_M = typing.TypeVar("_M", bound=models.Model)

if TYPE_CHECKING:
    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.models.expressions import Combinable

    from django_strawberry_framework.utils.typing import ModelField

    # Each field's descriptor types as django-stubs declares them (set type, get type),
    # spelled out because the checker runs without the django-stubs mypy plugin.
    _Char: TypeAlias = models.CharField[str | int | Combinable, str]
    _Int: TypeAlias = models.IntegerField[float | int | str | Combinable, int]
    _JSON: TypeAlias = models.JSONField[object, object]
    _FK: TypeAlias = models.ForeignKey[_M | Combinable, _M]
    _O2O: TypeAlias = models.OneToOneField[_M | Combinable, _M]
    _FObj: TypeAlias = models.ForeignObject[_M, _M]
    _M2M: TypeAlias = models.ManyToManyField[_M, models.Model]


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
    """Pin the spec-027 Decision 3 lookup -> python attr table against drift."""
    expected = {
        "exact": "exact",
        "iexact": "i_exact",
        "contains": "contains",
        "icontains": "i_contains",
        "startswith": "starts_with",
        "istartswith": "i_starts_with",
        "endswith": "ends_with",
        "iendswith": "i_ends_with",
        "regex": "regex",
        "iregex": "i_regex",
        "gt": "gt",
        "gte": "gte",
        "lt": "lt",
        "lte": "lte",
        "isnull": "is_null",
        "in": "in_",
        "range": "range",
        "date": "date",
        "year": "year",
        "month": "month",
        "day": "day",
        "week_day": "week_day",
        "quarter": "quarter",
        "hour": "hour",
        "minute": "minute",
        "second": "second",
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
    assert spec.django_source_path == "branch__name"


@pytest.mark.parametrize(
    ("lookup", "names"),
    [
        pytest.param("exact", ("exact", None), id="mapped"),
        pytest.param("icontains", ("i_contains", None), id="mapped-word-boundary"),
        pytest.param("in", ("in_", "in"), id="keyword-escaped"),
        pytest.param("iso_year", ("iso_year", None), id="unmapped"),
        pytest.param("year__gt", ("year_gt", None), id="chain"),
        pytest.param("year__in", ("year_in", None), id="chain-drops-the-keyword-escape"),
        pytest.param("year__isnull", ("year_is_null", None), id="chain-mapped-tail"),
        pytest.param("year__icontains", ("year_i_contains", None), id="chain-uppercase-run"),
        pytest.param("iso_year__gte", ("iso_year_gte", None), id="chain-unmapped-head"),
        pytest.param("from", ("from_", "from"), id="unmapped-keyword-escaped"),
        pytest.param("from__gt", ("from_gt", None), id="chain-drops-an-unmapped-escape"),
    ],
)
def test_lookup_leaf_names_names_a_chain_segment_by_segment(
    lookup: str,
    names: tuple[str, str | None],
) -> None:
    """A bag lookup's ``(python_attr, keyword wire name or None)``, a chain's attr per segment.

    Only a single keyword token carries a wire name; the executing schema's
    ``NameConverter`` names every other field from its attr.
    """
    assert lookup_leaf_names(lookup) == names


def test_two_lookups_of_one_head_named_by_one_attr_are_refused() -> None:
    """A lookup a ``get_filters()`` override adds under a chain's attr would shadow the chain.

    ``year_gt`` (a lookup the project registers) and ``year__gt`` both name the attr
    ``year_gt`` of the ``occurred_at`` head, so one would be unreachable from the generated
    input. The lookup is registered (Django's ``register_lookup``, which unregisters it on
    exit) so the attr-collision guard, not the unresolvable-lookup refusal, is what fires.
    """

    class CollidingFilter(FilterSet):
        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            filters = OrderedDict(super().get_filters())
            filters["occurred_at__year_gt"] = NumberFilter(
                field_name="occurred_at",
                lookup_expr="year_gt",
            )
            return filters

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"occurred_at": ["year__gt"]}

    with (
        register_lookup(models.DateTimeField, GreaterThan, lookup_name="year_gt"),
        pytest.raises(ConfigurationError, match="both generate the lookup attribute 'year_gt'"),
    ):
        filter_lookup_table(CollidingFilter)


@pytest.mark.parametrize("name", ["from", "class", "is"])
def test_a_transform_named_by_a_python_keyword_publishes_under_an_escaped_attr(name: str) -> None:
    """A consumer transform registered under a keyword builds its bag field as ``<name>_``.

    The bare keyword cannot be a dataclass field, so the input class would not build.
    """
    transform = type("KeywordYear", (ExtractYear,), {"lookup_name": name})
    with register_lookup(models.DateTimeField, transform):

        class KeywordFilter(FilterSet):
            class Meta:
                model = scalar_models.ScalarSpecimen
                fields = {"occurred_at": [name]}

        assert _bag_lookup_attrs(KeywordFilter, "occurred_at") == [f"{name}_"]
        assert KeywordFilter._normalize_input({"occurred_at": {f"{name}_": 2020}}) == {
            f"occurred_at__{name}": 2020,
        }


class _YearAtLeast(GreaterThanOrEqual):
    """A consumer comparison whose class names it ``isnull``: ``<value> >= <operand>``."""

    lookup_name = "isnull"

    @override
    def get_rhs_op(self, connection: BaseDatabaseWrapper, rhs: str) -> str:
        # Every supported backend renders ``gte`` so; its operator table is keyed by name.
        del connection
        return f">= {rhs}"


@pytest.mark.django_db
def test_a_consumer_lookup_registered_as_isnull_takes_its_own_operand() -> None:
    """Only Django's ``IsNull`` past a transform publishes ``Boolean``, not any lookup so named.

    ``year__isnull`` here compares the year to a number, which the declared
    ``NumberFilter`` publishes and applies as Django does; ``Boolean`` would refuse every
    value Django accepts.
    """
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("dropped", kept=False)
    _lookup_operand.cache_clear()
    _model_lookup_operand.cache_clear()
    try:
        with register_lookup(models.IntegerField, _YearAtLeast):

            class ShadowedNullFilter(FilterSet):
                since = NumberFilter(field_name="occurred_at", lookup_expr="year__isnull")

                class Meta:
                    model = scalar_models.ScalarSpecimen
                    fields = []

            annotations = {
                attr: ann for attr, ann, _kwargs in _build_input_fields(ShadowedNullFilter)
            }
            (lookup,) = dataclasses.fields(_class_arg(annotations["since"]))
            django_rows = scalar_models.ScalarSpecimen.objects.filter(
                occurred_at__year__isnull=2021,
            )
            expected = list(django_rows.values_list("label", flat=True))
            rows = ShadowedNullFilter.apply_sync(
                {"since": {"year_is_null": 2021}},
                scalar_models.ScalarSpecimen.objects.all(),
                make_info(context=SimpleNamespace(request=HttpRequest())),
            )
            labels = list(rows.values_list("label", flat=True))
    finally:
        _lookup_operand.cache_clear()
        _model_lookup_operand.cache_clear()
    assert lookup.type == "int | None"
    assert labels == expected == ["kept"]


class _ModelBuiltFilter(Filter):
    """A consumer ``Filter`` whose ``field`` reads the bound ``model`` before building it."""

    @property
    @override
    def field(self) -> forms.Field:
        _ = read_attr(self, "model")
        return super().field


@pytest.mark.parametrize("field_name", ["price", "label"], ids=["decimal-column", "text-column"])
@pytest.mark.parametrize(
    ("filter_class", "expected"),
    [
        (NumberFilter, decimal.Decimal | None),
        (Filter, bool | None),
        (_ModelBuiltFilter, bool | None),
    ],
    ids=["form-cleans-a-number", "form-passes-any-value", "form-built-per-request"],
)
def test_a_method_filter_named_isnull_is_typed_by_a_form_cleaning_its_own_kind(
    filter_class: type[Filter],
    expected: object,
    field_name: str,
) -> None:
    """A ``method=`` filter's method applies no ``isnull``, so a form cleaning a number types it.

    The method receives what the form cleans: a ``NumberFilter`` hands it a number, which
    ``Boolean`` would refuse, whatever the column (``label``'s ``String`` would refuse it
    too); a bare ``Filter`` passes any value through and stays ``Boolean``, and so does a
    filter over a column whose form field is built only per request (its ``field`` reads the
    bound ``model``), since no form field names another kind at schema build.
    """

    class MethodNullFilter(FilterSet):
        unset = filter_class(field_name=field_name, lookup_expr="isnull", method="by_value")

        def by_value(
            self,
            queryset: QuerySet[scalar_models.ScalarSpecimen],
            _name: str,
            _value: object,
        ) -> QuerySet[scalar_models.ScalarSpecimen]:
            return queryset

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    annotation = convert_filter_to_input_annotation(
        MethodNullFilter.base_filters["unset"],
        scalar_models.ScalarSpecimen._meta.get_field(field_name),
        None,
        MethodNullFilter,
    )
    assert annotation == expected


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
    f = ChoiceFilter(choices=library_models.Book.CirculationStatus.choices)
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
    assert str(exc_info.value).startswith(
        "FilterSet: NoFieldFilter(method='filter_custom') on None",
    )
    assert "is backed by no model field and exposes no form field" in str(exc_info.value)

    # ``AllValuesMultipleFilter`` reads the per-request ``model`` to build its field, so
    # unbound it builds none; with no column either, the refusal advises the spellings
    # that type it.
    unbound = AllValuesMultipleFilter(field_name="city", method="filter_custom")
    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(unbound, None, None, FilterSet)
    assert str(exc_info.value) == (
        "FilterSet: AllValuesMultipleFilter(method='filter_custom') on 'city' is backed by no "
        "model field and exposes no form field, so nothing types its value; point field_name "
        "at a model field, or put the method on a typed filter primitive "
        "(`CharFilter(method=...)`, `NumberFilter(method=...)`, `ListFilter(method=...)` for "
        "a list value, ...) or on a `Filter` subclass declaring `field_class` at class level."
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
        f"FilterSet: {type(choice_filter).__name__} on {choice_filter.field_name!r} reads "
        f"{model_field.model.__name__}.{model_field.name}, which declares no `choices`, so no "
        "choice enum types its input (the filter's own `choices` never feed the enum); declare "
        "`choices` on the column it filters (a `choices=` list of pairs, or a `TextChoices` / "
        "`IntegerChoices` class's `.choices`), or filter the column through a non-choice filter "
        "(`CharFilter`, `NumberFilter`, `DateFromToRangeFilter`, its lookups in Meta.fields, "
        "or `CharFilter(method=...)` for a method filter)."
    )


def test_a_choice_filter_read_off_no_model_field_names_what_it_reads() -> None:
    """A choice filter typed from no model field is refused saying so.

    Only a column can take ``choices``, so the advice to declare them is left out; the
    transform-output reason runs over HTTP in the live declaration rows.
    """
    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(
            ChoiceFilter(field_name="opened_on", choices=[("a", "A")]),
            None,
            None,
            FilterSet,
        )
    assert str(exc_info.value) == (
        "FilterSet: ChoiceFilter on 'opened_on' reads no model field, so no choice enum types "
        "its input (the filter's own `choices` never feed the enum); filter the column through a "
        "non-choice filter (`CharFilter`, `NumberFilter`, `DateFromToRangeFilter`, its lookups "
        "in Meta.fields, or `CharFilter(method=...)` for a method filter)."
    )


def _date_range_in_filter(field_name: str) -> Filter:
    """A CSV ``in`` wrapper around ``DateRangeFilter``, as django-filter builds one for ``in``."""
    wrapper = type("DateRangeInFilter", (DjangoBaseInFilter, DateRangeFilter), {})
    built = wrapper(field_name=field_name, lookup_expr="in")
    assert isinstance(built, Filter)
    return built


_SHELF = library_models.Shelf


@pytest.mark.parametrize(
    ("make_filter", "column"),
    [
        pytest.param(
            lambda: _date_range_in_filter("condition"),
            _SHELF._meta.get_field("condition"),
            id="date-range-in-wrapper",
        ),
        pytest.param(
            lambda: ChoiceFilter(field_name="tier", choices=[(10, "ten")]),
            _SHELF._meta.get_field("tier"),
            id="choice-disjoint",
        ),
        pytest.param(
            lambda: TypedChoiceFilter(field_name="condition", choices=[("mint", "Mint")]),
            _SHELF._meta.get_field("condition"),
            id="typed-choice-disjoint",
        ),
        pytest.param(
            lambda: ChoiceFilter(field_name="condition", choices=[("", "Unset")]),
            _SHELF._meta.get_field("condition"),
            id="only-the-blank-choice",
        ),
        pytest.param(
            lambda: ChoiceFilter(
                field_name="condition",
                choices=library_models.Book.CirculationStatus,
            ),
            _SHELF._meta.get_field("condition"),
            id="another-columns-choices-class",
        ),
    ],
)
def test_a_choice_filter_accepting_no_member_of_its_column_enum_is_refused(
    make_filter: Callable[[], Filter],
    column: ModelField,
) -> None:
    """A filter whose own form field accepts none of the column enum's members is refused.

    Every value its input publishes would be the form's ``invalid_choice`` (an empty value
    is skipped as no constraint, never accepted), so the build refuses it naming the column.
    """
    declared = make_filter()
    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(declared, column, None, FilterSet)
    assert str(exc_info.value) == (
        f"FilterSet: {type(declared).__name__} on {declared.field_name!r} publishes the choice "
        f"enum of {column.model.__name__}.{column.name}, but its own form field accepts none of "
        "that column's `choices`, so every value of its input would be refused (a "
        "`DateRangeFilter`'s fixed date-range keys are no column's choices); give the filter "
        "`choices` drawn from the column's (`choices=<Model>.<Choices>.choices`, or a subset "
        "of them), or filter that column through a non-choice filter (`CharFilter`, "
        "`NumberFilter`, `DateFromToRangeFilter`, its lookups in Meta.fields, or "
        "`CharFilter(method=...)` for a method filter)."
    )


class _ModelChoiceFieldFilter(Filter):
    """A filter whose form field is a ``ModelChoiceField``, whose choices are rows."""

    field_class: type[forms.ModelChoiceField[models.Model]] = forms.ModelChoiceField


@pytest.mark.parametrize(
    "make_filter",
    [
        pytest.param(lambda: AllValuesFilter(field_name="condition"), id="all-values"),
        pytest.param(
            lambda: ChoiceFilter(field_name="condition", choices=_SHELF.Condition),
            id="the-columns-choices-class",
        ),
        pytest.param(lambda: CharFilter(field_name="condition"), id="char-form-field"),
        pytest.param(
            lambda: _ModelChoiceFieldFilter(
                field_name="condition",
                queryset=library_models.Branch.objects.all(),
            ),
            id="model-choice-form-field",
        ),
    ],
)
def test_a_choice_filter_whose_form_may_accept_a_member_publishes_the_column_enum(
    make_filter: Callable[[], Filter],
) -> None:
    """A form field accepting a member builds; one built per request or from rows is not asked.

    A ``Choices`` class is read as its ``.choices``, so the column's own class accepts every
    member. ``AllValuesFilter`` builds no form field unbound and a model-choice field's choices
    are rows, so neither is read at schema build (no database access is allowed here), and a
    ``CharField`` validates no choices. Callable ``choices`` and a subset run over HTTP in the
    live declaration rows.
    """
    column = _SHELF._meta.get_field("condition")
    annotation = convert_filter_to_input_annotation(make_filter(), column, None, FilterSet)
    (enum_cls,) = (arg for arg in _args(annotation) if arg is not type(None))
    assert isinstance(enum_cls, type)
    assert issubclass(enum_cls, Enum)
    assert [member.name for member in enum_cls] == [
        "BLANK",
        "good",
        "worn",
        "damaged",
    ]


def _conditions_on_record() -> list[tuple[str, str]]:
    """Choices read from the database, which a test without ``django_db`` refuses."""
    return [(shelf.condition, shelf.condition) for shelf in _SHELF.objects.all()]


class _DjangoChoiceFieldFilter(ChoiceFilter):
    """A consumer ``ChoiceFilter`` whose ``field_class`` is Django's own ``ChoiceField``."""

    field_class: type[forms.ChoiceField] = forms.ChoiceField


class _DjangoTypedChoiceFieldFilter(ChoiceFilter):
    """A consumer ``ChoiceFilter`` whose ``field_class`` is Django's own ``TypedChoiceField``."""

    field_class: type[forms.TypedChoiceField] = forms.TypedChoiceField


class _DjangoMultipleChoiceFieldFilter(MultipleChoiceFilter):
    """A consumer ``MultipleChoiceFilter`` whose ``field_class`` is Django's own form field."""

    field_class: type[forms.MultipleChoiceField] = forms.MultipleChoiceField


@pytest.mark.parametrize(
    ("make_filter", "is_list"),
    [
        pytest.param(
            lambda: ChoiceFilter(
                field_name="condition",
                choices=lazy(_conditions_on_record, list)(),
            ),
            False,
            id="choice-lazy-promise",
        ),
        pytest.param(
            lambda: ChoiceFilter(
                field_name="condition",
                choices=SimpleLazyObject(_conditions_on_record),
            ),
            False,
            id="choice-simple-lazy-object",
        ),
        pytest.param(
            lambda: MultipleChoiceFilter(
                field_name="condition",
                choices=lazy(_conditions_on_record, list)(),
            ),
            True,
            id="multiple-choice-lazy-promise",
        ),
        pytest.param(
            lambda: MultipleChoiceFilter(
                field_name="condition",
                choices=SimpleLazyObject(_conditions_on_record),
            ),
            True,
            id="multiple-choice-simple-lazy-object",
        ),
        pytest.param(
            lambda: TypedChoiceFilter(
                field_name="condition",
                choices=SimpleLazyObject(_conditions_on_record),
            ),
            False,
            id="typed-choice-simple-lazy-object",
        ),
        pytest.param(
            lambda: TypedMultipleChoiceFilter(
                field_name="condition",
                choices=SimpleLazyObject(_conditions_on_record),
            ),
            True,
            id="typed-multiple-choice-simple-lazy-object",
        ),
        pytest.param(
            lambda: _DjangoChoiceFieldFilter(
                field_name="condition",
                choices=SimpleLazyObject(_conditions_on_record),
            ),
            False,
            id="django-choice-field-class-simple-lazy-object",
        ),
        pytest.param(
            lambda: _DjangoTypedChoiceFieldFilter(
                field_name="condition",
                choices=SimpleLazyObject(_conditions_on_record),
            ),
            False,
            id="django-typed-choice-field-class-simple-lazy-object",
        ),
        pytest.param(
            lambda: _DjangoMultipleChoiceFieldFilter(
                field_name="condition",
                choices=SimpleLazyObject(_conditions_on_record),
            ),
            True,
            id="django-multiple-choice-field-class-simple-lazy-object",
        ),
    ],
)
def test_lazy_choices_reading_the_database_are_not_evaluated_at_schema_build(
    make_filter: Callable[[], Filter],
    *,
    is_list: bool,
) -> None:
    """Lazy ``choices`` are evaluated per form build, so building the input reads no rows.

    The test holds no database access, so evaluating these choices would raise. Django's own
    choice form fields (``TypedChoiceField``, ``TypedMultipleChoiceField``, a consumer
    ``field_class`` naming Django's ``ChoiceField``, ``TypedChoiceField`` or
    ``MultipleChoiceField``) normalize ``choices`` when they are built, so the build reads
    their form field on a copy handing over the choices unread.
    """
    column = _SHELF._meta.get_field("condition")
    annotation = convert_filter_to_input_annotation(make_filter(), column, None, FilterSet)
    (member,) = (arg for arg in _args(annotation) if arg is not type(None))
    if is_list:
        assert get_origin(member) is list
        (member,) = _args(member)
    assert isinstance(member, type)
    assert issubclass(member, Enum)
    assert [choice.name for choice in member] == [
        "BLANK",
        "good",
        "worn",
        "damaged",
    ]


@isolate_apps("apps.library")
def test_a_choice_filter_over_a_column_whose_only_choice_is_blank_builds() -> None:
    """A column whose only choice is the blank one leaves no member to ask about, so it builds.

    django-filter skips an empty value as no constraint, so the form field is never asked
    about ``BLANK``; with no other member nothing shows the declaration serves no value.
    """

    class BlankOnlyShelf(models.Model):
        state: _Char = models.CharField(max_length=1, choices=[("", "Unset")], blank=True)

        class Meta:
            app_label = "library"
            managed = False

    annotation = convert_filter_to_input_annotation(
        ChoiceFilter(field_name="state"),
        BlankOnlyShelf._meta.get_field("state"),
        None,
        FilterSet,
    )
    enum_cls = _class_arg(annotation)
    assert issubclass(enum_cls, Enum)
    assert [member.name for member in enum_cls] == ["BLANK"]


def _declared_label_annotation(declared: CharFilter) -> object:
    """Type ``declared`` declared as ``label`` on a ``ScalarSpecimen`` set, as the build does.

    django-filter's metaclass binds the declaration's ``field_name`` to its attribute name
    (``label``), and the build types each leaf of the set's lookup table.
    """

    class LabelFilter(FilterSet):
        label = declared

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    return convert_filter_to_input_annotation(
        LabelFilter.base_filters["label"],
        scalar_models.ScalarSpecimen._meta.get_field("label"),
        None,
        LabelFilter,
    )


def test_convert_filter_to_input_annotation_wraps_nullable() -> None:
    """``extra['required']=False`` (the default) wraps the annotation in `T | None`."""
    assert _declared_label_annotation(CharFilter()) == str | None


def test_convert_filter_to_input_annotation_does_not_wrap_required() -> None:
    """``required=True`` returns the scalar without the `| None` wrap."""
    assert _declared_label_annotation(CharFilter(required=True)) is str


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


_ModelChoiceT = typing.TypeVar(
    "_ModelChoiceT",
    bound=django_filters.ModelChoiceFilter | django_filters.ModelMultipleChoiceFilter,
)


def _request_scoped_choice(
    filter_class: type[_ModelChoiceT],
    queryset: Callable[[HttpRequest | None], QuerySet[models.Model]],
    field_name: str | None = None,
    *,
    to_field_name: str | None = None,
    method: str | None = None,
) -> _ModelChoiceT:
    """Declare ``filter_class`` with ``queryset`` uncalled, as django-filter's callable ``queryset``.

    django-filter calls it with the request when it builds the form field, so the schema
    build reads no rows of it.
    """
    # basedpyright: types-django-filter types ``queryset`` as a ``QuerySet``;
    # ``QuerySetRequestMixin.get_queryset`` calls a callable one with the request
    return filter_class(field_name, queryset=queryset, method=method, to_field_name=to_field_name)  # pyright: ignore[reportArgumentType]


def test_a_model_choice_filter_with_a_request_scoped_queryset_builds_without_calling_it() -> None:
    """The widget check never builds a form field whose ``queryset`` waits for the request.

    The callable raises when called, so the schema building proves nothing called it.
    """

    def _no_request_yet(_request: HttpRequest | None) -> QuerySet[library_models.Shelf]:
        raise AssertionError

    declared = _request_scoped_choice(
        django_filters.ModelChoiceFilter,
        _no_request_yet,
        field_name="shelf",
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


class _PerRequestCodeChoice(django_filters.ModelChoiceFilter):
    """A ``ModelChoiceFilter`` with no ``queryset=``: ``get_queryset`` answers each request's rows.

    Its set publishes it (the override can supply the queryset), so a ``field_name`` naming
    no relation is refused when its input builds.
    """

    @override
    def get_queryset(self, request: object) -> QuerySet[library_models.Shelf]:
        return library_models.Shelf._default_manager.all()


@dataclass(frozen=True)
class _LeafRefusalCase:
    """One schema-build refusal a child set's ``leaf`` reaches, expanded or served directly.

    ``expanded`` is the message's subject for a ``RelatedFilter`` copy of ``leaf`` (projected
    or rebound) and ``direct`` for ``leaf`` on the set the schema serves, formatted with the
    sets' names (``child``, ``parent``) and the ``repr`` of the child set's own ``leaf``
    (``declared``) and its class name (``kind``); ``rest`` follows either subject.
    ``plain_child`` declares the leaf instead on a child set overriding nothing, which
    publishes only a filter consumer code can give a queryset.
    """

    declare: Callable[[], Filter]
    expanded: str
    direct: str
    rest: str
    plain_child: Callable[[], Filter] | None = None


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
        "{child}.leaf: {kind} on 'code' (reached through {parent}.shelf)",
        "{child}: {kind} on 'code'",
        " has no queryset and its field_name names no relation on the FilterSet model, so "
        "there is no column to type its input from. Pass a model queryset.",
        plain_child=lambda: _PerRequestCodeChoice(field_name="code"),
    ),
    "choice": _LeafRefusalCase(
        lambda: ChoiceFilter(field_name="topic", choices=[("a", "A")]),
        "{child}.leaf: ChoiceFilter on 'topic' (reached through {parent}.shelf)",
        "{child}: ChoiceFilter on 'topic'",
        " reads Shelf.topic, which declares no `choices`, so no choice enum types its input "
        "(the filter's own `choices` never feed the enum); declare `choices` on the column it "
        "filters (a `choices=` list of pairs, or a `TextChoices` / `IntegerChoices` class's "
        "`.choices`), or filter the column through a non-choice filter (`CharFilter`, "
        "`NumberFilter`, `DateFromToRangeFilter`, its lookups in Meta.fields, or "
        "`CharFilter(method=...)` for a method filter).",
    ),
    "choice-off-column": _LeafRefusalCase(
        lambda: DateRangeFilter(field_name="condition"),
        "{child}.leaf: DateRangeFilter on 'condition' (reached through {parent}.shelf)",
        "{child}: DateRangeFilter on 'condition'",
        " publishes the choice enum of Shelf.condition, but its own form field accepts none of "
        "that column's `choices`, so every value of its input would be refused (a "
        "`DateRangeFilter`'s fixed date-range keys are no column's choices); give the filter "
        "`choices` drawn from the column's (`choices=<Model>.<Choices>.choices`, or a subset "
        "of them), or filter that column through a non-choice filter (`CharFilter`, "
        "`NumberFilter`, `DateFromToRangeFilter`, its lookups in Meta.fields, or "
        "`CharFilter(method=...)` for a method filter).",
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
    "relation": _LeafRefusalCase(
        lambda: CharFilter(field_name="branch"),
        "{child}.leaf: CharFilter on 'branch' (reached through {parent}.shelf)",
        "{child}: CharFilter on 'branch'",
        " reads Shelf.branch, a ForeignKey no SCALAR_MAP entry types, so nothing types its "
        "input; filter by the related row's key through 'branch' in Meta.fields or a "
        "ModelChoiceFilter / ModelMultipleChoiceFilter, name the related column past it "
        "(field_name 'branch__id'), or filter the related row's own fields through a "
        "RelatedFilter.",
    ),
    "method-without-field": _LeafRefusalCase(
        lambda: AllValuesMultipleFilter(method="filter_leaf"),
        "{child}.leaf: AllValuesMultipleFilter(method='filter_leaf') on 'leaf' (reached "
        "through {parent}.shelf)",
        "{child}: AllValuesMultipleFilter(method='filter_leaf') on 'leaf'",
        " is backed by no model field and exposes no form field, so nothing types its value; "
        "point field_name at a model field, or put the method on a typed filter primitive "
        "(`CharFilter(method=...)`, `NumberFilter(method=...)`, `ListFilter(method=...)` for "
        "a list value, ...) or on a `Filter` subclass declaring `field_class` at class level.",
    ),
}


def _declare_leaf(case: _LeafRefusalCase, base: type[FilterSet]) -> Filter:
    """``case``'s leaf as a child set on ``base`` declares it."""
    if base is FilterSet and case.plain_child is not None:
        return case.plain_child()
    return case.declare()


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
    declared = _declare_leaf(case, base)
    child = _shelf_leaf_set(declared, base)
    parent = _book_shelf_set(child, FilterSet)
    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, parent)
    assert child.get_filters()["leaf"] is declared

    subject = case.expanded.format(
        child=child.__name__,
        parent=parent.__name__,
        declared=repr(declared),
        kind=type(declared).__name__,
    )
    assert _build_refusal() == subject + case.rest


@pytest.mark.parametrize("field_name", ["branch", "code"], ids=["relation", "column"])
def test_an_expanded_child_model_choice_with_no_queryset_is_refused_when_its_set_publishes(
    field_name: str,
) -> None:
    """A child set's model-choice filter with no queryset is refused naming the child set.

    The parent's ``RelatedFilter`` publishes the child set first, which refuses the leaf
    before any input builds: nothing on the form-build path could supply the queryset, on
    a relation path or a column one alike.
    """
    child = _shelf_leaf_set(django_filters.ModelChoiceFilter(field_name=field_name), FilterSet)
    parent = _book_shelf_set(child, FilterSet)
    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, parent)

    assert _build_refusal() == (
        f"FilterSet {child.__qualname__}: ModelChoiceFilter 'leaf' has field_name "
        f"{field_name!r} and no queryset, so the model-choice form field it builds has no rows "
        "to look a value up in, and every request building the set's form would fail. Pass "
        "queryset= (a model queryset, or a callable taking the request), override the "
        "filter's get_queryset(request), or give a Meta.filter_overrides entry an `extra` "
        'returning {"queryset": ...}.'
    )


def test_an_expanded_child_set_overriding_init_keeps_its_querysetless_model_choice() -> None:
    """A child set overriding ``__init__`` can supply the queryset per request: it builds."""
    child = _shelf_leaf_set(
        django_filters.ModelChoiceFilter(field_name="branch"),
        _CustomizingFilterSet,
    )
    parent = _book_shelf_set(child, FilterSet)
    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, parent)

    finalize_django_types()
    assert "shelf__leaf" in parent.get_filters()


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

    subject = case.direct.format(
        child=child.__name__,
        declared=repr(declared),
        kind=type(declared).__name__,
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
    declared = _declare_leaf(case, base)
    child = _shelf_leaf_set(declared, base)
    parent = _deep_copying(_book_shelf_set(child, FilterSet), rekey=rekey)
    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, parent)
    assert ("aliased_leaf" in parent.get_filters()) is rekey

    subject = case.expanded.format(
        child=child.__name__,
        parent=parent.__name__,
        declared=repr(declared),
        kind=type(declared).__name__,
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
    # A form field built from the column's choices accepts its enum's members.
    choices = library_models.Shelf.Condition.choices
    both = (
        paired(field_name="condition")
        if parent is RangeFilter
        else paired(field_name="condition", choices=choices)
    )
    assert isinstance(both, Filter)
    assert isinstance(both, django_filters.MultipleChoiceFilter)
    model_field: ModelField = library_models.Shelf._meta.get_field("condition")
    single = (
        parent(field_name="condition", choices=choices)
        if parent is ChoiceFilter
        else parent(field_name="condition")
    )

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


class _OwnKindField(forms.Field):
    """A consumer form field cleaning its own kind, under no ``FORM_FIELD_SCALARS`` row."""

    @override
    def to_python(self, value: object) -> object:
        return value


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
        pytest.param(forms.JSONField, strawberry.scalars.JSON, id="json"),
        pytest.param(forms.CharField, str, id="text"),
        pytest.param(forms.Field, str, id="generic-fallback"),
        pytest.param(_OwnKindField, str, id="unregistered-fallback"),
    ],
)
def test_scalar_from_form_field_maps_each_recognized_shape(
    field_class: type[forms.Field],
    expected: object,
) -> None:
    """Each form field maps to its ``FORM_FIELD_SCALARS`` row, a field no row covers to ``str``.

    Float, decimal and JSON resolve to their own rows before the integer and text classes
    they subclass. A form field no row covers cleans the text of a querystring, so it
    publishes ``String`` where a form mutation refuses it.
    """
    assert _scalar_from_form_field(field_class()) is expected


# ---------------------------------------------------------------------------
# _scalar_from_model_field - model-field -> Python scalar mapping
# ---------------------------------------------------------------------------


def test_scalar_from_model_field_none_falls_back_to_str() -> None:
    assert _scalar_from_model_field(None, CharFilter(), None) is str


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
    assert _scalar_from_model_field(field_class(), CharFilter(), None) is expected


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

    Two independent ``isinstance`` chains could drift apart (spec-055 C3), so
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
    """A callable queryset on a ``method=`` filter naming no field fails at input build.

    Neither source names a model: the callable queryset has none until a request
    arrives and ``field_name`` (``owner``) is no path of fields on ``Item``. The message
    names the FilterSet, the filter and both fixes, never ``SCALAR_MAP`` /
    ``Meta.exclude``.
    """

    def _request_categories(_request: HttpRequest | None) -> QuerySet[Category]:
        return Category.objects.all()

    class ItemFilter(FilterSet):
        owner = _request_scoped_choice(
            django_filters.ModelChoiceFilter,
            _request_categories,
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
    assert message.endswith(
        " has a callable queryset, which names its model only once a request arrives, and its "
        "field_name is no path of fields on the FilterSet model to read that model from, so "
        "there is no column to type its input from. Pass a model queryset, or point field_name "
        "at the field the filter compares (the relation, or the to_field_name column past it).",
    )
    assert "SCALAR_MAP" not in message
    assert "Meta.exclude" not in message


def _requested_branches(_request: HttpRequest | None) -> QuerySet[library_models.Branch]:
    """Every branch: a callable ``queryset``, read only once a request arrives."""
    return library_models.Branch.objects.all()


def _model_choice_annotation(
    model: type[models.Model],
    filter_class: type[
        django_filters.ModelChoiceFilter | django_filters.ModelMultipleChoiceFilter
    ],
    queryset: QuerySet[models.Model] | Callable[[HttpRequest | None], QuerySet[models.Model]],
    field_name: str,
    to_field_name: str | None = None,
) -> object:
    """Type ``filter_class`` over ``field_name``, declared as ``pick`` on a set over ``model``.

    ``queryset`` is a model queryset or a callable one (``_request_scoped_choice``).
    """
    if callable(queryset):
        declared = _request_scoped_choice(
            filter_class,
            queryset,
            field_name,
            to_field_name=to_field_name,
        )
    else:
        declared = filter_class(field_name, queryset=queryset, to_field_name=to_field_name)
    pick_set = type(
        "PickSet",
        (FilterSet,),
        {"pick": declared, "Meta": type("Meta", (), {"model": model, "fields": []})},
    )
    return convert_filter_to_input_annotation(pick_set.base_filters["pick"], None, None, pick_set)


_MODEL_CHOICE_ARMS = {
    "model-queryset": library_models.Branch.objects.all,
    "callable-queryset": lambda: _requested_branches,
}


@pytest.mark.parametrize("arm", list(_MODEL_CHOICE_ARMS))
@pytest.mark.parametrize(
    ("filter_class", "field_name", "expected"),
    [
        (django_filters.ModelChoiceFilter, "branch", int | None),
        (django_filters.ModelMultipleChoiceFilter, "branch__name", list[int] | None),
    ],
    ids=["single-on-the-relation", "multiple-on-its-column"],
)
def test_a_model_choice_to_field_name_of_pk_keys_by_the_primary_key_as_unset_does(
    arm: str,
    filter_class: type[
        django_filters.ModelChoiceFilter | django_filters.ModelMultipleChoiceFilter
    ],
    field_name: str,
    expected: object,
) -> None:
    """``to_field_name="pk"`` types the value as the primary key, as no ``to_field_name`` does.

    Django's ``ModelChoiceField`` looks each value up by ``to_field_name or "pk"``, so
    ``"pk"`` is the primary key whichever model the form field reads: a model queryset's,
    or for a callable queryset the model the ``field_name`` path ends on.
    """
    queryset = _MODEL_CHOICE_ARMS[arm]()
    unset = _model_choice_annotation(
        library_models.Shelf,
        filter_class,
        queryset,
        field_name=field_name,
    )
    pk = _model_choice_annotation(
        library_models.Shelf,
        filter_class,
        queryset,
        field_name=field_name,
        to_field_name="pk",
    )
    assert unset == pk == expected


@pytest.mark.parametrize("arm", list(_MODEL_CHOICE_ARMS))
@pytest.mark.parametrize(
    ("filter_class", "field_name"),
    [
        (django_filters.ModelChoiceFilter, "branch"),
        (django_filters.ModelMultipleChoiceFilter, "branch__name"),
    ],
    ids=["single-on-the-relation", "multiple-on-its-column"],
)
@pytest.mark.parametrize("to_field_name", ["nope", "shelves"], ids=["unknown", "reverse"])
def test_a_model_choice_to_field_name_naming_no_column_is_refused_at_build(
    arm: str,
    filter_class: type[
        django_filters.ModelChoiceFilter | django_filters.ModelMultipleChoiceFilter
    ],
    field_name: str,
    to_field_name: str,
) -> None:
    """A ``to_field_name`` naming nothing, or a reverse relation, of ``Branch`` is refused.

    The form field would look each value up by a name that is no column of the model it
    reads, so no column types the input. The refusal names the set, the filter, the
    ``to_field_name`` and the model: for a model queryset the model its form field looks
    values up in, for a callable one the model its ``field_name`` path ends on, with a
    model queryset among the remedies.
    """
    with pytest.raises(ConfigurationError) as exc_info:
        _model_choice_annotation(
            library_models.Shelf,
            filter_class,
            _MODEL_CHOICE_ARMS[arm](),
            field_name=field_name,
            to_field_name=to_field_name,
        )
    if arm == "callable-queryset":
        source = "the model its field_name path ends on (a callable queryset names none at build)"
        remedy = "Pass a model queryset, name a column of that model,"
    else:
        source = "the model its form field looks each value up in"
        remedy = "Name a column of that model,"
    assert str(exc_info.value) == (
        f"PickSet: {filter_class.__name__} on {field_name!r} has to_field_name "
        f"{to_field_name!r}, which names no column of Branch, {source}, so there is no "
        f"column to type its input from. {remedy} or drop to_field_name to look values up by "
        "primary key."
    )


class _ColumnPathCase(NamedTuple):
    """A model-choice filter over a column path: its set's model, the model queryset's model."""

    model: type[models.Model]
    field_name: str
    target: type[models.Model]
    to_field_name: str | None
    expected: object


_COLUMN_PATH_CASES = {
    "inheritance-child-unset": _ColumnPathCase(
        library_models.KioskFault,
        "kiosk__name",
        library_models.SelfServeDesk,
        None,
        list[int] | None,
    ),
    "inheritance-child-grandparent-column": _ColumnPathCase(
        library_models.KioskFault,
        "kiosk__name",
        library_models.SelfServeDesk,
        "name",
        list[str] | None,
    ),
    "inheritance-child-own-column": _ColumnPathCase(
        library_models.KioskFault,
        "kiosk__name",
        library_models.SelfServeDesk,
        "kiosk_code",
        list[str] | None,
    ),
    "inheritance-child-parent-column": _ColumnPathCase(
        library_models.KioskFault,
        "kiosk__name",
        library_models.SelfServeDesk,
        "window_count",
        list[int] | None,
    ),
    "no-relation-crossed": _ColumnPathCase(
        library_models.Branch,
        "name",
        library_models.Branch,
        "name",
        list[str] | None,
    ),
    "inheritance-child-pk-unset": _ColumnPathCase(
        library_models.KioskFault,
        "kiosk__pk",
        library_models.SelfServeDesk,
        None,
        list[int] | None,
    ),
    "inheritance-child-pk-own-column": _ColumnPathCase(
        library_models.KioskFault,
        "kiosk__pk",
        library_models.SelfServeDesk,
        "kiosk_code",
        list[str] | None,
    ),
    "inheritance-child-own-key": _ColumnPathCase(
        library_models.SelfServeDesk,
        "pk",
        library_models.SelfServeDesk,
        "kiosk_code",
        list[str] | None,
    ),
    "two-hops": _ColumnPathCase(
        library_models.Book,
        "shelf__branch__name",
        library_models.Branch,
        "name",
        list[str] | None,
    ),
    "two-hops-to-the-relation": _ColumnPathCase(
        library_models.Book,
        "shelf__branch",
        library_models.Branch,
        "isil",
        list[str] | None,
    ),
}


@pytest.mark.parametrize("case", list(_COLUMN_PATH_CASES))
def test_a_callable_queryset_types_a_column_path_as_its_model_queryset_does(case: str) -> None:
    """A callable queryset reads the model its ``field_name`` path ends on, as a model one names.

    ``KioskFault.kiosk`` targets the third level of an inheritance chain and ``name`` is
    a column of its first; the model ``kiosk__name`` ends on is the relation's target
    (``SelfServeDesk``), so the target's own ``kiosk_code`` and its parent's
    ``window_count`` are columns of it too. ``kiosk__pk`` ends there as well, though the
    target's key is its parent link, and ``SelfServeDesk``'s own ``pk`` ends on the set's
    model. ``Branch``'s ``name`` crosses no relation, so the
    model is the set's own; ``Book``'s ``shelf__branch__name`` and ``shelf__branch``
    cross two, and the model is the last one's target.
    """
    row = _COLUMN_PATH_CASES[case]

    def _requested_targets(_request: HttpRequest | None) -> QuerySet[models.Model]:
        return row.target._default_manager.all()

    by_model = _model_choice_annotation(
        row.model,
        django_filters.ModelMultipleChoiceFilter,
        row.target._default_manager.all(),
        row.field_name,
        row.to_field_name,
    )
    by_callable = _model_choice_annotation(
        row.model,
        django_filters.ModelMultipleChoiceFilter,
        _requested_targets,
        row.field_name,
        row.to_field_name,
    )
    assert by_callable == by_model == row.expected


@pytest.mark.parametrize(
    ("model", "field_name"),
    [
        (library_models.KioskFault, "kiosk__pk"),
        (library_models.SelfServeDesk, "pk"),
        (library_models.Shelf, "branch__pk"),
    ],
    ids=["inheritance-child-key", "inheritance-child-own-key", "plain-key"],
)
def test_a_model_choice_filter_with_no_queryset_on_a_primary_key_path_is_refused(
    model: type[models.Model],
    field_name: str,
) -> None:
    """An unset ``queryset`` over Django's ``pk`` alias names no model to look values up in.

    The path ends on the column the key stores, not on a relation, even where the key is
    a multi-table-inheritance parent link (``SelfServeDesk``'s ``lendingdesk_ptr``).
    """
    pick_set = type(
        "PickSet",
        (FilterSet,),
        {
            "pick": django_filters.ModelChoiceFilter(field_name=field_name),
            "Meta": type("Meta", (), {"model": model, "fields": []}),
        },
    )
    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(pick_set.base_filters["pick"], None, None, pick_set)
    assert str(exc_info.value) == (
        f"PickSet: ModelChoiceFilter on {field_name!r} has no queryset and its field_name "
        "names no relation on the FilterSet model, so there is no column to type its input "
        "from. Pass a model queryset."
    )


def test_a_model_choice_filter_with_a_callable_queryset_on_a_set_without_a_model_is_refused() -> (
    None
):
    """A set without ``Meta.model`` has no model for a callable queryset's ``field_name`` to walk.

    The callable names its model only once a request arrives, and with no model on the
    set the ``field_name`` path reaches none, so the input is refused with the callable
    queryset's remedy.
    """

    class ModelLessSet(FilterSet):
        names = _request_scoped_choice(
            django_filters.ModelMultipleChoiceFilter,
            _requested_branches,
            field_name="branch__name",
            to_field_name="name",
        )

    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(
            ModelLessSet.base_filters["names"],
            None,
            None,
            ModelLessSet,
        )
    assert str(exc_info.value) == (
        "ModelLessSet: ModelMultipleChoiceFilter on 'branch__name' has a callable queryset, "
        "which names its model only once a request arrives, and its field_name is no path of "
        "fields on the FilterSet model to read that model from, so there is no column to type "
        "its input from. Pass a model queryset, or point field_name at the field the filter "
        "compares (the relation, or the to_field_name column past it)."
    )


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
        f"ArraySpecimenFilter: {type(declared).__name__} on {declared.field_name!r} has no input "
        f"type for lookup '{lookup}' on the ArrayField column _ArraySpecimen.ints: only exact, "
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
        f"ArraySpecimenFilter: ChoiceFilter on {declared.field_name!r} has no input type for "
        "lookup 'exact' on the ArrayField column _ArraySpecimen.flagged: only exact, contains, "
        "contained_by and overlap take one array of the column's elements. Declare an "
        "ArrayFilter with one of those lookup_expr values."
    )
    assert registry.get_enum(_ArraySpecimen, "flagged") is None


@pytest.mark.parametrize(
    "declare",
    [
        pytest.param(
            lambda: ArrayFilter(field_name="ints", lookup_expr="isnull"),
            id="array-filter",
        ),
        pytest.param(
            lambda: ListFilter(field_name="ints", lookup_expr="isnull"),
            id="list-filter",
        ),
        pytest.param(
            lambda: _NumbersInFilter(field_name="ints", lookup_expr="isnull"),
            id="csv-filter",
        ),
        pytest.param(
            lambda: TypedFilter(field_name="ints", lookup_expr="isnull"),
            id="typed-filter",
        ),
        pytest.param(
            lambda: ChoiceFilter(field_name="ints", lookup_expr="isnull", choices=[(1, "one")]),
            id="choice-filter",
        ),
    ],
)
def test_an_array_column_null_test_on_a_filter_publishing_elements_names_a_boolean_filter(
    monkeypatch: pytest.MonkeyPatch,
    declare: Callable[[], Filter],
) -> None:
    """A null test on a list, CSV, typed or choice filter over an array names ``BooleanFilter``.

    Each of them publishes the column's elements where the null test takes one ``Boolean``,
    and its own form cleans no Boolean either; a ``BooleanFilter`` with the same lookup builds.
    """
    patch_array_field(monkeypatch)
    declared = declare()
    _ = _serve_array_filter(declared, exposed=True)

    assert _build_refusal() == (
        f"ArraySpecimenFilter: {type(declared).__name__} on 'ints' has no input type for "
        "lookup 'isnull' on the ArrayField column _ArraySpecimen.ints: a null test takes one "
        "Boolean, which this filter does not publish. Declare a BooleanFilter with lookup_expr "
        "'isnull'."
    )


@pytest.mark.parametrize(
    "range_class",
    [
        pytest.param(DjangoRangeFilter, id="range-filter"),
        pytest.param(DateFromToRangeFilter, id="date-from-to-range-filter"),
    ],
)
def test_a_range_filter_over_an_array_column_is_refused_for_the_range_it_applies(
    monkeypatch: pytest.MonkeyPatch,
    range_class: type[DjangoRangeFilter],
) -> None:
    """A ``RangeFilter`` applies ``range`` whatever its ``lookup_expr``, so its advice is the list one."""
    patch_array_field(monkeypatch)
    _ = _serve_array_filter(range_class(field_name="ints", lookup_expr="isnull"), exposed=True)

    assert _build_refusal() == (
        f"ArraySpecimenFilter: {range_class.__name__} on 'ints' has no input type for lookup "
        "'range' on the ArrayField column _ArraySpecimen.ints: only exact, contains, "
        "contained_by and overlap take one array of the column's elements. Declare an "
        "ArrayFilter with one of those lookup_expr values."
    )


def test_a_boolean_null_test_over_an_array_column_is_boolean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ``BooleanFilter`` the null-test refusal names builds over the array as ``Boolean``."""
    patch_array_field(monkeypatch)
    served = _serve_array_filter(
        BooleanFilter(field_name="ints", lookup_expr="isnull"),
        exposed=True,
    )

    assert _served_arr_annotation(served) is bool


@pytest.mark.parametrize(
    "lookup",
    [
        "exact",
        "contains",
        "contained_by",
        "overlap",
    ],
)
@pytest.mark.parametrize("filter_class", _ARRAY_FILTER_CLASSES)
def test_an_array_column_list_filter_takes_its_elements_for_each_whole_array_lookup(
    monkeypatch: pytest.MonkeyPatch,
    filter_class: type[Filter],
    lookup: str,
) -> None:
    """Each lookup whose operand is one array of the column's elements builds ``list[int]``."""
    patch_array_field(monkeypatch)
    served = _serve_array_filter(filter_class(field_name="ints", lookup_expr=lookup), exposed=True)

    assert _served_arr_element(served) is int


def _serve_array_lookups(
    meta_fields: object,
    filter_class: type[Filter] = ArrayFilter,
) -> type[DjangoType]:
    """Serve a set generating ``meta_fields`` over ``ints`` through a ``filter_class`` override."""

    class ArraySpecimenFilter(FilterSet):
        class Meta:
            model = _ArraySpecimen
            fields = meta_fields
            filter_overrides = {FakeArrayField: {"filter_class": filter_class}}

    meta: dict[str, object] = {
        "model": _ArraySpecimen,
        "fields": ("id",),
        "filterset_class": ArraySpecimenFilter,
    }
    return type("ArraySpecimenType", (DjangoType,), {"Meta": type("Meta", (), meta)})


@pytest.mark.parametrize("filter_class", _ARRAY_FILTER_CLASSES)
def test_an_overridden_array_columns_all_lookups_are_refused_at_the_first_it_cannot_type(
    monkeypatch: pytest.MonkeyPatch,
    filter_class: type[Filter],
) -> None:
    """A served per-field ``"__all__"`` over an array keeps the whole set, so the build refuses it.

    The override's filter class owns the lookups it accepts, and the expansion publishes
    the column's whole catalog; a list filter over an ``ArrayField`` types only the four
    whole-array lookups, so the first other lookup (``iexact``) is refused naming them.
    """
    patch_array_field(monkeypatch)
    _ = _serve_array_lookups({"ints": "__all__"}, filter_class)

    assert _build_refusal() == (
        f"ArraySpecimenFilter: {filter_class.__name__} on 'ints' has no input type for lookup "
        "'iexact' on the ArrayField column _ArraySpecimen.ints: only exact, contains, "
        "contained_by and overlap take one array of the column's elements. Declare an "
        "ArrayFilter with one of those lookup_expr values."
    )


#: A list filter over an array's element count or one element: a transform whose output is no
#: array, compared by one value.
_ARRAY_SCALAR_TRANSFORMS = [
    pytest.param("ints", "len", id="len-lookup"),
    pytest.param("ints__len", "exact", id="len-path"),
    pytest.param("ints", "0", id="index-lookup"),
    pytest.param("ints__0", "exact", id="index-path"),
]


def _array_scalar_refusal(
    set_name: str,
    filter_class: type[Filter],
    field_name: str,
    lookup_expr: str,
) -> str:
    return (
        f"FilterSet {set_name}: {filter_class.__name__} 'arr' has field_name "
        f"{field_name!r} and lookup_expr {lookup_expr!r}, but the lookup it applies, Django's "
        "IntegerFieldExact ('exact'), compares one value, and the filter publishes and applies "
        "a list. Declare lookup_expr 'in' (any member matches) or 'range' (two bounds), or a "
        "transform ending in either ('year__in'); read the list in `method=`; or, for a "
        "Meta.filter_overrides selection, list only those lookups for the column in Meta.fields."
    )


def _declared_array(filter_class: type[Filter], field_name: str, lookup_expr: str) -> Filter:
    if lookup_expr == "exact":
        return filter_class(field_name=field_name)
    return filter_class(field_name=field_name, lookup_expr=lookup_expr)


@pytest.mark.parametrize("filter_class", _ARRAY_FILTER_CLASSES)
@pytest.mark.parametrize(("field_name", "lookup_expr"), _ARRAY_SCALAR_TRANSFORMS)
@pytest.mark.parametrize("served", [True, False], ids=["served", "unserved"])
def test_a_list_filter_over_an_arrays_count_or_element_compared_by_one_value_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    filter_class: type[Filter],
    field_name: str,
    lookup_expr: str,
    *,
    served: bool,
) -> None:
    """``len`` and an index read one integer of the array, so their ``exact`` takes no list.

    The leaf publishes ``[Int!]`` and would hand the whole list to the integer comparison, so
    the set refuses it when it publishes: a served set when the schema builds, an unserved
    one at its first use.
    """
    patch_array_field(monkeypatch)
    declared = _declared_array(filter_class, field_name, lookup_expr)
    if served:
        _ = _serve_array_filter(declared, exposed=False)
        refusal = _build_refusal()
        set_name = "_serve_array_filter.<locals>.ArraySpecimenFilter"
    else:
        meta = type("Meta", (), {"model": _ArraySpecimen, "fields": []})
        unserved = type("ArraySpecimenFilter", (FilterSet,), {"arr": declared, "Meta": meta})
        with pytest.raises(ConfigurationError) as excinfo:
            _ = unserved.get_filters()
        refusal = str(excinfo.value)
        set_name = "ArraySpecimenFilter"

    assert refusal == _array_scalar_refusal(set_name, filter_class, field_name, lookup_expr)


@pytest.mark.parametrize("filter_class", _ARRAY_FILTER_CLASSES)
@pytest.mark.parametrize(
    ("field_name", "lookup_expr", "element"),
    [
        pytest.param("ints", "len__in", int, id="len-in"),
        pytest.param("ints__0", "in", int, id="index-in"),
        pytest.param("ints", "exact", int, id="whole-array-exact"),
    ],
)
def test_a_list_filter_over_an_arrays_count_element_or_whole_array_taking_the_list_builds(
    monkeypatch: pytest.MonkeyPatch,
    filter_class: type[Filter],
    field_name: str,
    lookup_expr: str,
    element: type,
) -> None:
    """A count's or an element's ``in`` takes the list, and the whole array's ``exact`` one array."""
    patch_array_field(monkeypatch)
    declared = _declared_array(filter_class, field_name, lookup_expr)

    assert _served_arr_element(_serve_array_filter(declared, exposed=False)) is element


_WHOLE_ARRAY_LISTED = {
    "exact": (list[int], type(None)),
    "contains": (list[int], type(None)),
    "contained_by": (list[int], type(None)),
    "overlap": (list[int], type(None)),
}


@pytest.mark.parametrize(
    ("listed", "expected"),
    [
        pytest.param([], _WHOLE_ARRAY_LISTED, id="four"),
        pytest.param(
            ["isnull"],
            {**_WHOLE_ARRAY_LISTED, "is_null": (bool, type(None))},
            id="four-and-null-test",
        ),
    ],
)
@pytest.mark.parametrize("filter_class", _ARRAY_FILTER_CLASSES)
def test_an_overridden_array_columns_listed_whole_array_lookups_build(
    monkeypatch: pytest.MonkeyPatch,
    filter_class: type[Filter],
    listed: list[str],
    expected: dict[str, tuple[object, ...]],
) -> None:
    """Listing the four whole-array lookups under the override builds each as ``[Int!]``.

    A listed null test is generated as django-filter's ``BooleanFilter`` and is ``Boolean``.
    """
    patch_array_field(monkeypatch)
    _ = _serve_array_lookups(
        {
            "ints": [
                "exact",
                "contains",
                "contained_by",
                "overlap",
                *listed,
            ],
        },
        filter_class,
    )
    finalize_django_types()

    input_cls = FilterArgumentsFactory.input_object_types["ArraySpecimenFilterInputType"]
    bag = _class_arg(_annotations(input_cls)["ints"])
    published = {name: _args(annotation) for name, annotation in _annotations(bag).items()}
    assert published == expected


def test_an_overridden_array_columns_listed_lookup_its_input_cannot_carry_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Named in ``Meta.fields``, a lookup the expansion leaves out is still refused at build."""
    patch_array_field(monkeypatch)
    _ = _serve_array_lookups({"ints": ["exact", "gt"]})

    assert _build_refusal() == (
        "ArraySpecimenFilter: ArrayFilter on 'ints' has no input type for lookup 'gt' on the "
        "ArrayField column _ArraySpecimen.ints: only exact, contains, contained_by and overlap "
        "take one array of the column's elements. Declare an ArrayFilter with one of those "
        "lookup_expr values."
    )


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
    ("lookup_expr", "transform", "bound"),
    [
        pytest.param("year__range", "year", int, id="year"),
        pytest.param("date__range", "date", datetime.date, id="date"),
        pytest.param("year", "year", int, id="bare-year"),
        pytest.param("date", "date", datetime.date, id="bare-date"),
    ],
)
def test_two_ranges_over_one_column_mint_one_range_type_per_value_path(
    lookup_expr: str,
    transform: str,
    bound: type,
) -> None:
    """A ``range`` and a range through a transform over one column are two range types in one set.

    Each is stemmed on the ``field_name`` plus every transform Django's query applies ahead
    of the lookup, a bare trailing ``year`` / ``date`` (Django's implicit ``exact``)
    included, so the column's ``DateTime`` bounds and the transform's output bounds never
    claim one name.
    """

    class TwoRangeFilter(FilterSet):
        stamps_span = RangeFilter(field_name="occurred_at", lookup_expr="range")
        years_span = RangeFilter(field_name="occurred_at", lookup_expr=lookup_expr)

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


def _model_less_range_owner() -> type[FilterSet]:
    class ModelLessRangeOwnerFilter(FilterSet):
        pass

    return ModelLessRangeOwnerFilter


def _specimen_range_owner() -> type[FilterSet]:
    class SpecimenRangeOwnerFilter(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    return SpecimenRangeOwnerFilter


@pytest.mark.parametrize(
    (
        "owner",
        "field_name",
        "lookup_expr",
        "name",
    ),
    [
        pytest.param(
            _model_less_range_owner,
            "occurred_at",
            "date",
            "ModelLessRangeOwnerFilterOccurredAtRangeInputType",
            id="no-model",
        ),
        pytest.param(
            _specimen_range_owner,
            "par__occurred_at",
            "year__range",
            "SpecimenRangeOwnerFilterParOccurredAtYearRangeInputType",
            id="unresolved-path",
        ),
        pytest.param(
            _specimen_range_owner,
            "occurred_at",
            "bogus__range",
            "SpecimenRangeOwnerFilterOccurredAtBogusRangeInputType",
            id="unwalkable-lookup",
        ),
    ],
)
def test_a_range_no_query_of_the_model_walks_is_stemmed_on_its_spelled_transforms(
    owner: Callable[[], type[FilterSet]],
    field_name: str,
    lookup_expr: str,
    name: str,
) -> None:
    """A range no build-time query of the model walks keeps the ``lookup_expr`` spelled ahead.

    A set with no model, a path only a queryset alias resolves (Django's ``FieldError``) and
    a ``lookup_expr`` no walk from the column accepts (``LookupValidationError``) answer no
    value path, so the stem is the ``field_name`` and the ``lookup_expr`` parts ahead of the
    last. The ``FilteredRelation`` alias is pinned live by ``test_scalars_filter_api.py``'s
    ``parentDaysSpan`` rows; no shipped type serves a set with no model.
    """
    range_filter = RangeFilter(field_name=field_name, lookup_expr=lookup_expr)

    assert _build_range_input_class(range_filter, int, owner()).__name__ == name


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
        f"ArraySpecimenFilter: {type(declared).__name__} on {declared.field_name!r} publishes "
        f"lookup '{lookup}', which is no GraphQL field name. Spell an index or slice in "
        "field_name (`<column>__0`, `<column>__0_2`) and name the lookup in lookup_expr."
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
        f"ArraySpecimenFilter: DateFilter on {declared.field_name!r} has no input type for "
        "lookup 'exact' on the ArrayField column _ArraySpecimen.grid: only exact, contains, "
        "contained_by and overlap take one array of the column's elements. Declare an "
        "ArrayFilter with one of those lookup_expr values."
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


# ---------------------------------------------------------------------------
# A column that converts nothing it is handed is typed by the filter's form
# ---------------------------------------------------------------------------


def _decimal_of(value: object) -> decimal.Decimal:
    """A ``coerce`` callable that is no class, so its kind is unknown to the build."""
    return decimal.Decimal(str(value))


class _FloatFormFilter(Filter):
    """A consumer filter whose form cleans a float, a kind ``json.dumps`` encodes."""

    field_class = forms.FloatField


class _FloatsInFilter(BaseInFilter, _FloatFormFilter):
    """A consumer CSV filter whose members its form cleans as floats."""


class _DurationsInFilter(BaseInFilter, DurationFilter):
    """A consumer CSV filter whose members its form cleans as timedeltas."""


class _OwnKindFilter(Filter):
    """A consumer filter whose form field cleans a kind no row names."""

    field_class = _OwnKindField


class _NumberDatesInFilter(BaseInFilter, DateFilter):
    """A consumer CSV filter whose members its form cleans as dates."""


class _NumbersInFilter(BaseInFilter, NumberFilter):
    """A consumer CSV filter whose members its form cleans as decimals."""


class _DateTimesInFilter(BaseInFilter, DateTimeFilter):
    """A consumer CSV filter whose members its form cleans as datetimes."""


class _TimesInFilter(BaseInFilter, TimeFilter):
    """A consumer CSV filter whose members its form cleans as times."""


class _UUIDsInFilter(BaseInFilter, UUIDFilter):
    """A consumer CSV filter whose members its form cleans as UUIDs."""


class _JSONFormFilter(Filter):
    """A consumer filter whose form cleans any JSON value (``forms.JSONField``)."""

    field_class = forms.JSONField


class _IPAddressFormFilter(Filter):
    """A consumer filter whose form cleans an IP address (``forms.GenericIPAddressField``)."""

    field_class = forms.GenericIPAddressField


class _ModelChoiceFormFilter(Filter):
    """A consumer filter whose form reads a row of its ``queryset`` (``forms.ModelChoiceField``)."""

    field_class = forms.ModelChoiceField


class _URLFormFilter(Filter):
    """A consumer filter whose form cleans a URL (``forms.URLField``)."""

    field_class = forms.URLField


class _MultipleChoiceFormFilter(Filter):
    """A consumer filter whose form cleans a list of its own choices (``MultipleChoiceField``)."""

    field_class = forms.MultipleChoiceField


#: A consumer CSV filter whose members its form validates against its own ``choices``.
_ChoicesInFilter: type[Filter] = type("ChoicesInFilter", (BaseInFilter, ChoiceFilter), {})
#: A consumer CSV ``range`` whose bounds its form coerces after validating its own ``choices``.
_TypedChoicesRangeFilter: type[Filter] = type(
    "TypedChoicesRangeFilter",
    (BaseRangeFilter, TypedChoiceFilter),
    {},
)


class _TypedChoicesInFilter(BaseInFilter, TypedChoiceFilter):
    """A consumer CSV filter whose members its form coerces after validating its own ``choices``."""


class _OwnFilterNumberFilter(NumberFilter):
    """A consumer ``NumberFilter`` whose own ``filter`` decides what its value means."""

    @override
    def filter(self, qs: QuerySet[models.Model], value: object) -> QuerySet[models.Model]:
        return qs


def _payload_set(
    declared: Filter,
    *,
    model: type[models.Model] = scalar_models.ScalarSpecimen,
    overrides: Mapping[type[object], Mapping[str, object]] | None = None,
) -> type[FilterSet]:
    """A package ``FilterSet`` over ``model`` declaring ``declared`` as ``value``."""
    meta: dict[str, object] = {"model": model, "fields": []}
    if overrides is not None:
        meta["filter_overrides"] = dict(overrides)

    def filter_value(
        _self: FilterSet,
        queryset: QuerySet[models.Model],
        _name: str,
        _value: object,
    ) -> QuerySet[models.Model]:
        return queryset

    return type(
        "PayloadValueSet",
        (FilterSet,),
        {"value": declared, "filter_value": filter_value, "Meta": type("Meta", (), meta)},
    )


def _value_leaves(filterset: type[FilterSet]) -> dict[object, object]:
    """The lookup annotations of ``filterset``'s ``value`` operator bag."""
    annotations = {attr: ann for attr, ann, _kwargs in _build_input_fields(filterset)}
    return _annotations(_class_arg(annotations["value"]))


@pytest.mark.parametrize(
    ("declare", "lookup", "expected"),
    [
        pytest.param(
            lambda: CharFilter(field_name="payload"),
            "exact",
            str | None,
            id="text-on-the-column",
        ),
        pytest.param(
            lambda: MultipleChoiceFilter(field_name="payload__n", choices=[("5", "five")]),
            "exact",
            list[str] | None,
            id="multiple-choice-on-a-key",
        ),
        pytest.param(
            lambda: MultipleChoiceFilter(field_name="payload", choices=[("5", "five")]),
            "exact",
            list[str] | None,
            id="multiple-choice-on-the-column",
        ),
        pytest.param(
            lambda: _OwnFilterNumberFilter(field_name="payload__n"),
            "exact",
            decimal.Decimal | None,
            id="decimal-own-filter",
        ),
        pytest.param(
            lambda: _OwnFilterNumberFilter(field_name="payload"),
            "exact",
            decimal.Decimal | None,
            id="decimal-own-filter-on-the-column",
        ),
        pytest.param(
            lambda: _JSONFormFilter(field_name="raw", method="filter_value"),
            "exact",
            strawberry.scalars.JSON | None,
            id="json-form-method",
        ),
        pytest.param(
            lambda: Filter(field_name="payload"),
            "exact",
            strawberry.scalars.JSON | None,
            id="pass-through-on-the-column",
        ),
        pytest.param(
            lambda: TypedMultipleChoiceFilter(
                field_name="payload__n",
                coerce=_decimal_of,
                choices=[("5", "5")],
            ),
            "exact",
            list[str] | None,
            id="unknown-coerce-is-not-refused",
        ),
        pytest.param(
            lambda: _OwnKindFilter(field_name="payload__n"),
            "exact",
            str | None,
            id="unknown-form-kind-is-not-refused",
        ),
        pytest.param(
            lambda: _FloatFormFilter(field_name="payload__n"),
            "exact",
            float | None,
            id="float-form-on-a-key",
        ),
        pytest.param(
            lambda: _FloatsInFilter(field_name="payload__n", lookup_expr="in"),
            "in_",
            list[float] | None,
            id="float-csv-on-a-key",
        ),
        pytest.param(
            lambda: _JSONFormFilter(field_name="payload__n"),
            "exact",
            strawberry.scalars.JSON | None,
            id="json-form-on-a-key",
        ),
        pytest.param(
            lambda: _JSONFormFilter(field_name="payload"),
            "exact",
            strawberry.scalars.JSON | None,
            id="json-form-on-the-column",
        ),
        pytest.param(
            lambda: ListFilter(field_name="payload", lookup_expr="in"),
            "in_",
            list[strawberry.scalars.JSON] | None,
            id="package-list-with-no-column-form",
        ),
        pytest.param(
            lambda: NumberFilter(field_name="payload__n", lookup_expr="isnull"),
            "is_null",
            bool | None,
            id="null-test-on-a-key",
        ),
    ],
)
def test_a_filter_over_a_json_column_is_typed_by_what_its_form_cleans(
    declare: Callable[[], Filter],
    lookup: str,
    expected: object,
) -> None:
    """A ``JSONField`` compares the kind a value is handed, so the filter's form types it.

    The shapes neither fakeshop's ``ScalarSpecimenFilter`` (``test_scalars_filter_api.py``) nor
    the ``test_json_filter_typing_api.py`` holder declares: a text filter on the whole column,
    a ``MultipleChoiceFilter`` (``[String!]``), a consumer
    ``filter`` override cleaning a ``Decimal`` (never refused: it owns what its value means),
    a columnless ``method=`` filter cleaning ``forms.JSONField`` (``JSON``, through the shared
    form table), a ``FloatField`` form (``Float``, a kind ``json.dumps`` encodes, so never
    refused) and a ``coerce`` callable that is no class (its kind unknown, so not refused).
    Deliberate controls, passing before the rule too: a bare ``Filter`` on the
    column keeps ``JSON`` (it passes values through), a ``forms.JSONField`` form on a key
    keeps ``JSON`` (it is exempt from the encoder refusal), a package ``ListFilter`` keeps
    ``[JSON!]`` (django-filter builds no ``gte`` filter for the column, so no comparison form
    cleans its members), and ``isnull`` stays ``Boolean``.
    """
    assert _value_leaves(_payload_set(declare())) == {lookup: expected}


def test_a_filter_override_over_a_json_column_types_values_by_its_text_form() -> None:
    """``filter_overrides={JSONField: CharFilter}`` cleans text, so its values publish ``String``.

    The generated ``exact`` and a declared ``CharFilter`` clean text; a package ``ListFilter``
    and ``RangeFilter`` clean each value with the override's ``CharField`` (django-filter's own
    ``gte`` filter for the column), so ``5`` would reach the column as ``"5"``. The generated
    ``isnull`` stays ``Boolean``.
    """

    class OverriddenPayloadSet(FilterSet):
        text = CharFilter(field_name="payload__n")
        among = ListFilter(field_name="payload", lookup_expr="in")
        span = RangeFilter(field_name="payload__n")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"payload": ["exact", "isnull"]}
            filter_overrides = {models.JSONField: {"filter_class": CharFilter}}

    annotations = {
        attr: _annotations(_class_arg(ann))
        for attr, ann, _kwargs in _build_input_fields(OverriddenPayloadSet)
    }
    span_axes = _annotations(_class_arg(annotations["span"]["exact"]))

    assert annotations["payload"] == {"exact": str | None, "is_null": bool | None}
    assert annotations["text"] == {"exact": str | None}
    assert annotations["among"] == {"in_": list[str] | None}
    assert span_axes == {"start": str | None, "end": str | None}


@pytest.mark.parametrize(
    ("declare", "kind"),
    [
        pytest.param(lambda: NumberFilter(field_name="payload__n"), "Decimal", id="decimal"),
        pytest.param(lambda: DateFilter(field_name="payload__n"), "date", id="date"),
        pytest.param(lambda: DateTimeFilter(field_name="payload__n"), "datetime", id="datetime"),
        pytest.param(lambda: TimeFilter(field_name="payload__n"), "time", id="time"),
        pytest.param(lambda: UUIDFilter(field_name="payload__n"), "UUID", id="uuid"),
        pytest.param(
            lambda: DurationFilter(field_name="payload__n"),
            "timedelta",
            id="timedelta-under-a-string-scalar",
        ),
        pytest.param(
            lambda: TypedMultipleChoiceFilter(
                field_name="payload__n",
                coerce=decimal.Decimal,
                choices=[("5", "5")],
            ),
            "Decimal",
            id="decimal-coerce-class",
        ),
        pytest.param(
            lambda: TypedMultipleChoiceFilter(
                field_name="payload__n",
                coerce=uuid.UUID,
                choices=[("5", "5")],
            ),
            "UUID",
            id="uuid-coerce-class",
        ),
        pytest.param(
            lambda: _DurationsInFilter(field_name="payload__n", lookup_expr="in"),
            "timedelta",
            id="timedelta-csv",
        ),
        pytest.param(
            lambda: NumberFilter(field_name="payload", lookup_expr="gt"),
            "Decimal",
            id="decimal-on-the-column",
        ),
        pytest.param(
            lambda: DateFilter(field_name="payload", lookup_expr="contains"),
            "date",
            id="date-containment",
        ),
        pytest.param(
            lambda: _NumbersInFilter(field_name="payload__n", lookup_expr="in"),
            "Decimal",
            id="decimal-csv",
        ),
        pytest.param(
            lambda: _NumberDatesInFilter(field_name="payload__n", lookup_expr="in"),
            "date",
            id="date-csv",
        ),
        pytest.param(
            lambda: _DateTimesInFilter(field_name="payload__n", lookup_expr="in"),
            "datetime",
            id="datetime-csv",
        ),
        pytest.param(
            lambda: _TimesInFilter(field_name="payload__n", lookup_expr="in"),
            "time",
            id="time-csv",
        ),
        pytest.param(
            lambda: _UUIDsInFilter(field_name="payload__n", lookup_expr="in"),
            "UUID",
            id="uuid-csv",
        ),
        pytest.param(
            lambda: DjangoRangeFilter(field_name="payload__n"),
            "Decimal",
            id="decimal-range",
        ),
        pytest.param(
            lambda: DateFromToRangeFilter(field_name="payload__n"),
            "date",
            id="date-range",
        ),
        pytest.param(
            lambda: DateTimeFromToRangeFilter(field_name="payload__n"),
            "datetime",
            id="datetime-range",
        ),
        pytest.param(
            lambda: TimeRangeFilter(field_name="payload__n"),
            "time",
            id="time-range",
        ),
    ],
)
def test_a_kind_an_encoderless_json_column_cannot_encode_is_refused_at_build(
    declare: Callable[[], Filter],
    kind: str,
) -> None:
    """A lookup preparing its value through a ``JSONField`` with no encoder cannot carry the kind.

    ``JSONField.get_db_prep_value`` encodes through ``json.dumps``, which raises ``TypeError``
    for a ``Decimal``, ``date``, ``datetime``, ``time``, ``timedelta`` or ``UUID``: every request
    sending a value would fail, so the schema build refuses the filter naming the three fixes.
    The kind is the one the form field's class cleans, not the published scalar: a
    ``DurationFilter`` publishes ``String`` and cleans a ``timedelta``, and a
    ``TypedMultipleChoiceFilter`` cleans what a class ``coerce`` builds.
    """
    declared = declare()

    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(_payload_set(declared))

    assert str(excinfo.value) == (
        f"PayloadValueSet: {type(declared).__name__} on {declared.field_name!r} cleans {kind}, "
        "which its JSONField cannot encode with no encoder; give the filter a form field "
        "cleaning text or a number (an IntegerField or FloatField field_class), a bare Filter "
        "or TypedFilter to compare the JSON value as sent, or an encoder on the column."
    )


def test_a_package_list_under_a_number_override_over_json_is_refused_at_build() -> None:
    """A ``ListFilter`` cleaning members with an override's ``DecimalField`` is refused too.

    ``filter_overrides={JSONField: NumberFilter}`` hands each member to a ``DecimalField``, and
    an ``in`` prepares each through the column, which cannot encode a ``Decimal``.
    """
    declared = ListFilter(field_name="payload", lookup_expr="in")
    filterset = _payload_set(
        declared,
        overrides={models.JSONField: {"filter_class": NumberFilter}},
    )

    with pytest.raises(ConfigurationError, match=r"ListFilter on 'payload' cleans Decimal, "):
        _ = _build_input_fields(filterset)


class _CoercingJSONField(models.JSONField[object, object]):
    """A consumer ``JSONField`` that prepares each value as an integer: it converts, so it types."""

    @override
    def get_prep_value(self, value: object) -> object:
        return int(str(value))


@isolate_apps("apps.scalars")
@pytest.mark.parametrize(
    ("declare", "expected"),
    [
        pytest.param(
            lambda: NumberFilter(field_name="encoded__n"),
            decimal.Decimal | None,
            id="decimal-under-a-declared-encoder",
        ),
        pytest.param(
            lambda: DateFilter(field_name="encoded"),
            datetime.date | None,
            id="date-under-a-declared-encoder",
        ),
        pytest.param(
            lambda: NumberFilter(field_name="coerced"),
            strawberry.scalars.JSON | None,
            id="decimal-on-a-converting-subclass",
        ),
        pytest.param(
            lambda: CharFilter(field_name="coerced"),
            strawberry.scalars.JSON | None,
            id="text-on-a-converting-subclass",
        ),
    ],
)
def test_an_encoder_or_a_converting_json_subclass_keeps_its_filter(
    declare: Callable[[], Filter],
    expected: object,
) -> None:
    """A declared encoder is trusted, and a ``JSONField`` that converts is typed by the column.

    ``DjangoJSONEncoder`` encodes a ``Decimal`` and a ``date``, so each filter builds, typed by
    its form, and compares the encoder's text. A subclass overriding ``get_prep_value``
    converts what it is handed, so it types the leaf as any converting column does; those two
    rows are deliberate controls, typed so before the rule too.
    """

    class EncodedSpecimen(models.Model):
        encoded: _JSON = models.JSONField(encoder=DjangoJSONEncoder)
        coerced = _CoercingJSONField()

        class Meta:
            app_label = "scalars"
            managed = False

    assert _value_leaves(_payload_set(declare(), model=EncodedSpecimen)) == {"exact": expected}


class _IntCodeField(models.Field[object, object]):
    """A consumer column converting each value in ``get_db_prep_value``, registered as ``int``."""

    @override
    def get_db_prep_value(
        self,
        value: object,
        connection: BaseDatabaseWrapper,
        prepared: bool = False,
    ) -> object:
        return int(str(value))


@isolate_apps("apps.scalars")
@pytest.mark.parametrize(
    "declare",
    [
        pytest.param(lambda: NumberFilter(field_name="code"), id="number"),
        pytest.param(lambda: CharFilter(field_name="code"), id="text"),
    ],
)
def test_a_registered_non_json_column_keeps_its_scalar_whatever_its_methods(
    declare: Callable[[], Filter],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only a column whose own scalar is ``JSON`` is typed by the form; this one keeps ``Int``.

    The column keeps Django's ``to_python`` / ``get_prep_value`` but converts in
    ``get_db_prep_value``, and ``SCALAR_MAP`` registers it as ``int``: a ``Decimal``-typed
    leaf would silently match ``5`` for ``5.5``, a ``String`` one raise on ``"abc"``.
    Deliberate control: it is typed so before the rule too.
    """
    monkeypatch.setitem(converters_mod.SCALAR_MAP, _IntCodeField, int)

    class CodedSpecimen(models.Model):
        code = _IntCodeField()

        class Meta:
            app_label = "scalars"
            managed = False

    assert _value_leaves(_payload_set(declare(), model=CodedSpecimen)) == {"exact": int | None}


def _relation_remedy(path: str, column: str | None) -> str:
    """The remedy a declared filter over a relation joined on one column is refused with."""
    past = "" if column is None else f", name the related column past it (field_name {column!r})"
    return (
        " no SCALAR_MAP entry types, so nothing types its input; filter by the related row's key "
        f"through {path!r} in Meta.fields or a ModelChoiceFilter / ModelMultipleChoiceFilter"
        f"{past}, or filter the related row's own fields through a RelatedFilter."
    )


_COLUMN_REMEDY = (
    " no SCALAR_MAP entry types, so nothing types its input; register Base36Field (or a class "
    "it subclasses) in SCALAR_MAP."
)


@dataclass(frozen=True)
class _RelationLeaf:
    """A declared filter over a relation joined on one column, and the remedies its refusal names.

    ``declare`` builds the filter for a ``field_name``; ``path`` is the relation's path in
    ``Meta.fields`` and ``column`` the related column named past it (``None`` where the related
    key is itself a relation); ``target`` is the related model a model-choice filter queries.
    """

    model: type[models.Model]
    declare: Callable[[str], Filter]
    field_name: str
    label: str
    path: str
    column: str | None
    target: type[models.Model]


_RELATION_LEAVES = {
    "forward-key": _RelationLeaf(
        library_models.Shelf,
        lambda name: CharFilter(field_name=name),
        "branch",
        "Shelf.branch, a ForeignKey",
        "branch",
        "branch__id",
        library_models.Branch,
    ),
    "key-attname-method": _RelationLeaf(
        library_models.Shelf,
        lambda name: NumberFilter(field_name=name, method="filter_value"),
        "branch_id",
        "Shelf.branch, a ForeignKey",
        "branch",
        "branch__id",
        library_models.Branch,
    ),
    "reverse-key": _RelationLeaf(
        library_models.Branch,
        lambda name: ListFilter(field_name=name, lookup_expr="in"),
        "shelves",
        "Branch.shelves, a ManyToOneRel",
        "shelves",
        "shelves__id",
        library_models.Shelf,
    ),
    "many-to-many": _RelationLeaf(
        library_models.Shelf,
        lambda name: MultipleChoiceFilter(field_name=name, choices=[("1", "one")]),
        "alt_branches",
        "Shelf.alt_branches, a ManyToManyField",
        "alt_branches",
        "alt_branches__id",
        library_models.Branch,
    ),
    "reverse-many-to-many": _RelationLeaf(
        library_models.Branch,
        lambda name: AllValuesMultipleFilter(field_name=name),
        "alt_shelves",
        "Branch.alt_shelves, a ManyToManyRel",
        "alt_shelves",
        "alt_shelves__id",
        library_models.Shelf,
    ),
    "reverse-one-to-one": _RelationLeaf(
        library_models.Patron,
        lambda name: CharFilter(field_name=name),
        "card",
        "Patron.card, a OneToOneRel",
        "card",
        "card__id",
        library_models.MembershipCard,
    ),
    "one-to-one-key-range": _RelationLeaf(
        library_models.PatronProfile,
        lambda name: RangeFilter(field_name=name, lookup_expr="range", method="filter_value"),
        "patron",
        "PatronProfile.patron, a OneToOneField",
        "patron",
        "patron__id",
        library_models.Patron,
    ),
    "parent-link-list": _RelationLeaf(
        library_models.LendingDesk,
        lambda name: ListFilter(field_name=name, lookup_expr="in"),
        "venue_ptr",
        "LendingDesk.venue_ptr, a OneToOneField",
        "venue_ptr",
        "venue_ptr__id",
        library_models.Venue,
    ),
    "key-into-parent-link-range": _RelationLeaf(
        library_models.KioskFault,
        lambda name: RangeFilter(field_name=name, lookup_expr="range", method="filter_value"),
        "kiosk",
        "KioskFault.kiosk, a ForeignKey",
        "kiosk",
        None,
        library_models.LendingDesk,
    ),
    "generic-relation": _RelationLeaf(
        library_models.Branch,
        lambda name: CharFilter(field_name=name),
        "tags",
        "Branch.tags, a GenericRelation",
        "tags",
        "tags__id",
        library_models.TaggedItem,
    ),
    "two-hops": _RelationLeaf(
        library_models.Shelf,
        lambda name: CharFilter(field_name=name),
        "branch__shelves",
        "Branch.shelves, a ManyToOneRel",
        "branch__shelves",
        "branch__shelves__id",
        library_models.Shelf,
    ),
    "reverse-one-to-one-onto-a-parent-link": _RelationLeaf(
        library_models.Venue,
        lambda name: CharFilter(field_name=name),
        "lendingdesk",
        "Venue.lendingdesk, a OneToOneRel",
        "lendingdesk",
        None,
        library_models.LendingDesk,
    ),
    "key-to-field": _RelationLeaf(
        library_models.InterlibraryLoan,
        lambda name: CharFilter(field_name=name),
        "lender",
        "InterlibraryLoan.lender, a ForeignKey",
        "lender",
        "lender__isil",
        library_models.Branch,
    ),
    "key-to-field-attname": _RelationLeaf(
        library_models.InterlibraryLoan,
        lambda name: CharFilter(field_name=name),
        "lender_id",
        "InterlibraryLoan.lender, a ForeignKey",
        "lender",
        "lender__isil",
        library_models.Branch,
    ),
}


@pytest.mark.parametrize("site", list(_RELATION_LEAVES))
def test_a_declared_filter_over_a_relation_is_refused_naming_filter_remedies(site: str) -> None:
    """A declared filter whose ``field_name`` ends on a relation is refused in its set's words.

    A relation's value is a related row's key, which no ``SCALAR_MAP`` entry types, so the
    refusal names the filter and the remedies a ``FilterSet`` has: the relation listed in
    ``Meta.fields``, a model-choice filter, the related column named past it (absent where the
    related key is itself a relation), and a ``RelatedFilter``. A ``method=`` filter is refused
    alike: it keeps its column.
    """
    leaf = _RELATION_LEAVES[site]

    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(_payload_set(leaf.declare(leaf.field_name), model=leaf.model))

    kind = type(leaf.declare(leaf.field_name)).__name__
    assert str(excinfo.value) == (
        f"PayloadValueSet: {kind} on {leaf.field_name!r} reads {leaf.label}"
        + _relation_remedy(leaf.path, leaf.column)
    )


def _serve_on_a_column(model: type[models.Model], served: type[FilterSet]) -> None:
    """Declare a ``DjangoType`` for ``model`` selecting one plain column, serving ``served``.

    ``PatronProfile`` keys its rows by a one-to-one, so it carries no ``id`` to select.
    """
    column = next(field.name for field in model._meta.concrete_fields if not field.is_relation)
    meta = {"model": model, "fields": (column,), "filterset_class": served}
    _ = type(f"{model.__name__}ColumnType", (DjangoType,), {"Meta": type("Meta", (), meta)})


def _meta_fields_set(
    model: type[models.Model],
    fields: Mapping[str, list[str]],
) -> type[FilterSet]:
    """A package ``FilterSet`` over ``model`` generating ``fields``."""
    return type(
        "GeneratedSet",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": model, "fields": dict(fields)})},
    )


@pytest.mark.parametrize(
    "remedy",
    [
        "meta-fields",
        "model-choice",
        "model-multiple-choice",
        "related-column",
    ],
)
@pytest.mark.parametrize("site", list(_RELATION_LEAVES))
def test_every_remedy_a_relation_refusal_names_builds(site: str, remedy: str) -> None:
    """Each remedy the relation refusal names builds the schema for that relation.

    The relation's path listed in ``Meta.fields`` (a raw-key leaf typed by the related key), a
    ``ModelChoiceFilter`` / ``ModelMultipleChoiceFilter`` on it, and the refused filter moved to
    the related column past it.
    """
    leaf = _RELATION_LEAVES[site]
    if remedy == "meta-fields":
        filterset = _meta_fields_set(leaf.model, {leaf.path: ["exact"]})
    elif remedy == "model-choice":
        filterset = _payload_set(
            django_filters.ModelChoiceFilter(
                field_name=leaf.path,
                queryset=leaf.target.objects.all(),
            ),
            model=leaf.model,
        )
    elif remedy == "model-multiple-choice":
        filterset = _payload_set(
            django_filters.ModelMultipleChoiceFilter(
                field_name=leaf.path,
                queryset=leaf.target.objects.all(),
            ),
            model=leaf.model,
        )
    else:
        if leaf.column is None:
            pytest.skip("the related key is itself a relation: no column is named past it")
        filterset = _payload_set(leaf.declare(leaf.column), model=leaf.model)
    _serve_on_a_column(leaf.model, filterset)

    finalize_django_types()

    assert filter_lookup_table(filterset).by_input_attr


@pytest.mark.parametrize(
    ("model", "declare", "message"),
    [
        pytest.param(
            library_models.TaggedItem,
            lambda: CharFilter(field_name="content_object"),
            "PayloadValueSet: CharFilter on 'content_object' reads TaggedItem.content_object, a "
            "GenericForeignKey: Django filters no queryset through it, so no input can carry its "
            "value; filter through the GenericRelation that reverses it on the related model, or "
            "on the content type and object id columns it reads.",
            id="generic-foreign-key",
        ),
        pytest.param(
            library_models.Book,
            lambda: CharFilter(field_name="shelf", lookup_expr="branch"),
            "PayloadValueSet: CharFilter on 'shelf' reads Shelf.branch, a ForeignKey"
            + _relation_remedy("shelf__branch", "shelf__branch__id"),
            id="lookup-crossing-onto-a-relation",
        ),
        pytest.param(
            library_models.Book,
            lambda: CharFilter(field_name="genres"),
            "PayloadValueSet: CharFilter on 'genres' reads Book.genres, a ManyToManyField"
            + _relation_remedy("genres", "genres__id"),
            id="text-on-a-many-to-many",
        ),
        pytest.param(
            RpCompositeChild,
            lambda: CharFilter(field_name="parent"),
            "PayloadValueSet: CharFilter on 'parent' reads RpCompositeChild.parent, a "
            "ForeignObject linked by 2 columns, so no single key value can name a related row; "
            "filter the related row's own fields through a RelatedFilter.",
            id="relation-linked-by-two-columns",
        ),
        pytest.param(
            RpCompositeParent,
            lambda: ListFilter(field_name="pk", lookup_expr="in"),
            "PayloadValueSet: ListFilter on 'pk' reads RpCompositeParent.pk, a "
            "CompositePrimaryKey over 'tenant_id', 'code', which no one value names; filter each "
            "column it composes by name.",
            id="composite-primary-key",
        ),
        pytest.param(
            scalar_models.OverrideSpecimen,
            lambda: CharFilter(field_name="token"),
            "PayloadValueSet: CharFilter on 'token' reads OverrideSpecimen.token, a Base36Field"
            + _COLUMN_REMEDY,
            id="text-on-an-unregistered-column",
        ),
        pytest.param(
            scalar_models.OverrideSpecimen,
            lambda: NumberFilter(field_name="token"),
            "PayloadValueSet: NumberFilter on 'token' reads OverrideSpecimen.token, a Base36Field"
            + _COLUMN_REMEDY,
            id="number-on-an-unregistered-column",
        ),
        pytest.param(
            scalar_models.OverrideSpecimen,
            lambda: NumberFilter(field_name="token", method="filter_value"),
            "PayloadValueSet: NumberFilter on 'token' reads OverrideSpecimen.token, a Base36Field"
            + _COLUMN_REMEDY,
            id="method-number-on-an-unregistered-column",
        ),
    ],
)
def test_a_filter_over_a_field_with_no_scalar_is_refused_naming_its_remedy(
    model: type[models.Model],
    declare: Callable[[], Filter],
    message: str,
) -> None:
    """A field no ``SCALAR_MAP`` entry covers is refused with the remedy its kind takes.

    A ``lookup_expr`` crossing onto a relation names the path Django walks. A
    ``GenericForeignKey`` (no join, so no key column) points at the ``GenericRelation`` and
    the two columns it reads; a relation linked by several columns at a ``RelatedFilter``; a
    ``CompositePrimaryKey`` at its columns; any other column at a ``SCALAR_MAP`` entry, never at
    ``Meta.exclude``, which drops no declared filter.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(_payload_set(declare(), model=model))

    assert str(excinfo.value) == message


@pytest.mark.parametrize(
    ("model", "build"),
    [
        pytest.param(
            library_models.TaggedItem,
            lambda: _meta_fields_set(
                library_models.TaggedItem,
                {"content_type": ["exact"], "object_id": ["exact"]},
            ),
            id="generic-foreign-key-columns",
        ),
        pytest.param(
            library_models.Branch,
            lambda: _meta_fields_set(library_models.Branch, {"tags": ["exact"]}),
            id="generic-relation-reversing-it",
        ),
    ],
)
def test_the_generic_foreign_key_remedies_build(
    model: type[models.Model],
    build: Callable[[], type[FilterSet]],
) -> None:
    """The content type and object id columns, and the ``GenericRelation``, build the schema."""
    filterset = build()
    _serve_model(model, filterset)

    finalize_django_types()

    assert filter_lookup_table(filterset).by_input_attr


def test_a_composite_primary_keys_columns_build_by_name() -> None:
    """Each column a ``CompositePrimaryKey`` composes is typed by its own scalar."""
    annotations = {
        attr: ann
        for attr, ann, _kwargs in _build_input_fields(
            _meta_fields_set(RpCompositeParent, {"tenant_id": ["in"], "code": ["in"]}),
        )
    }

    assert _annotations(_class_arg(annotations["tenant_id"])) == {"in_": list[int] | None}
    assert _annotations(_class_arg(annotations["code"])) == {"in_": list[str] | None}


def _keyed_model_choice(target: type[models.Model]) -> Filter:
    """A ``ModelChoiceFilter`` on ``keyed`` querying ``target``."""
    return django_filters.ModelChoiceFilter(field_name="keyed", queryset=target.objects.all())


@pytest.mark.parametrize(
    ("declare", "kind"),
    [
        pytest.param(None, "RelationPkFilter", id="relation-key-in-meta-fields"),
        pytest.param(_keyed_model_choice, "ModelChoiceFilter", id="model-choice"),
    ],
)
@pytest.mark.parametrize("registered", [False, True], ids=["unregistered", "registered"])
@isolate_apps("apps.scalars")
def test_a_relation_key_onto_an_unregistered_primary_key_is_refused_naming_the_key_column(
    monkeypatch: pytest.MonkeyPatch,
    declare: Callable[[type[models.Model]], Filter] | None,
    kind: str,
    *,
    registered: bool,
) -> None:
    """A key filter typed from a related primary key no ``SCALAR_MAP`` entry covers names it.

    The raw-key leaf ``Meta.fields`` generates and a model-choice filter are typed from the
    column the related key stores, here a ``Base36Field`` primary key: the refusal names that
    column and its ``SCALAR_MAP`` remedy, and an entry for its class builds both.
    """

    class _TokenKeyed(models.Model):
        token: scalar_models.Base36Field = scalar_models.Base36Field(primary_key=True)

        class Meta:
            app_label = "scalars"
            managed = False

    class _TokenRef(models.Model):
        keyed: models.ForeignKey[_TokenKeyed | Combinable, _TokenKeyed] = models.ForeignKey(
            _TokenKeyed,
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    if registered:
        monkeypatch.setitem(converters_mod.SCALAR_MAP, scalar_models.Base36Field, str)
    filterset = (
        _meta_fields_set(_TokenRef, {"keyed": ["exact"]})
        if declare is None
        else _payload_set(declare(_TokenKeyed), model=_TokenRef)
    )
    if registered:
        assert _build_input_fields(filterset)
        return

    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(filterset)

    assert str(excinfo.value) == (
        f"{filterset.__name__}: {kind} on 'keyed' reads _TokenKeyed.token, a Base36Field"
        + _COLUMN_REMEDY
    )


@pytest.mark.parametrize("joined_key_is_unmapped", [False, True])
@isolate_apps("apps.scalars")
def test_relation_remedies_name_their_distinct_scalar_prerequisites(
    *,
    joined_key_is_unmapped: bool,
) -> None:
    """The default choice key is the target pk; the related-column route uses ``to_field``."""

    class _TokenKeyed(models.Model):
        token: models.AutoField[int | Combinable, int] | scalar_models.Base36Field = (
            models.AutoField(primary_key=True)
            if joined_key_is_unmapped
            else scalar_models.Base36Field(primary_key=True)
        )
        code: models.TextField[str | Combinable, str] | scalar_models.Base36Field = (
            scalar_models.Base36Field(unique=True)
            if joined_key_is_unmapped
            else models.TextField(unique=True)
        )
        label: models.TextField[str | Combinable, str] = models.TextField()

        class Meta:
            app_label = "scalars"
            managed = False

    class _TokenRef(models.Model):
        keyed: models.ForeignKey[_TokenKeyed | Combinable, _TokenKeyed] = models.ForeignKey(
            _TokenKeyed,
            to_field="code",
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    filterset = _payload_set(CharFilter(field_name="keyed"), model=_TokenRef)
    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(filterset)

    message = str(excinfo.value)
    assert "_TokenRef.keyed, a ForeignKey" in message
    assert "field_name 'keyed__code'" in message
    pk_prerequisite = "first register Base36Field for _TokenKeyed.token in SCALAR_MAP"
    joined_prerequisite = "first register Base36Field for _TokenKeyed.code in SCALAR_MAP"
    assert (pk_prerequisite in message) is not joined_key_is_unmapped
    assert (joined_prerequisite in message) is joined_key_is_unmapped

    if not joined_key_is_unmapped:
        assert _build_input_fields(
            _payload_set(CharFilter(field_name="keyed__code"), model=_TokenRef),
        )
    else:
        assert _build_input_fields(_meta_fields_set(_TokenRef, {"keyed": ["exact"]}))
        assert _build_input_fields(
            _payload_set(_keyed_model_choice(_TokenKeyed), model=_TokenRef),
        )


@isolate_apps("apps.scalars")
def test_unmapped_relation_key_remedies_build_with_the_stated_prerequisite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The unregistered key's related-row route works alone; key routes need registration."""

    class _TokenKeyed(models.Model):
        token = scalar_models.Base36Field(primary_key=True)
        label: models.TextField[str | Combinable, str] = models.TextField()

        class Meta:
            app_label = "scalars"
            managed = False

    class _TokenRef(models.Model):
        keyed: models.ForeignKey[_TokenKeyed | Combinable, _TokenKeyed] = models.ForeignKey(
            _TokenKeyed,
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(_payload_set(CharFilter(field_name="keyed"), model=_TokenRef))
    message = str(excinfo.value)
    assert "first register Base36Field for _TokenKeyed.token in SCALAR_MAP" in message

    class _KeyedFilter(FilterSet):
        label = CharFilter(field_name="label")

        class Meta:
            model = _TokenKeyed
            fields = []

    class _RefFilter(FilterSet):
        keyed = RelatedFilter(_KeyedFilter, field_name="keyed")

        class Meta:
            model = _TokenRef
            fields = []

    assert _build_input_fields(_RefFilter)
    monkeypatch.setitem(converters_mod.SCALAR_MAP, scalar_models.Base36Field, str)
    assert _build_input_fields(_meta_fields_set(_TokenRef, {"keyed": ["exact"]}))
    assert _build_input_fields(_payload_set(_keyed_model_choice(_TokenKeyed), model=_TokenRef))
    assert _build_input_fields(
        _payload_set(CharFilter(field_name="keyed__token"), model=_TokenRef),
    )


@isolate_apps("apps.scalars")
def test_unmapped_relation_key_public_meta_build_names_required_scalar() -> None:
    """Normal type finalization reaches the declaration's route-specific prerequisite."""

    class _TokenKeyed(models.Model):
        token = scalar_models.Base36Field(primary_key=True)
        label: models.TextField[str | Combinable, str] = models.TextField()

        class Meta:
            app_label = "scalars"
            managed = False

    class _TokenRef(models.Model):
        keyed: models.ForeignKey[_TokenKeyed | Combinable, _TokenKeyed] = models.ForeignKey(
            _TokenKeyed,
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    class _RefFilter(FilterSet):
        leaf = CharFilter(field_name="keyed")

        class Meta:
            model = _TokenRef
            fields = []

    _serve_on_a_column(_TokenRef, _RefFilter)
    message = _build_refusal()
    assert "_RefFilter: CharFilter on 'keyed' reads _TokenRef.keyed" in message
    assert "first register Base36Field for _TokenKeyed.token in SCALAR_MAP" in message


@pytest.mark.parametrize(
    "remedy",
    [
        "meta-fields",
        "model-choice",
        "related-column",
        "related-filter",
    ],
)
@isolate_apps("apps.scalars")
def test_unmapped_relation_key_remedies_finalize_with_their_prerequisite(
    monkeypatch: pytest.MonkeyPatch,
    remedy: str,
) -> None:
    """Each suggested route can build a serving type once its actual prerequisite is met."""

    class _TokenKeyed(models.Model):
        token = scalar_models.Base36Field(primary_key=True)
        label: models.TextField[str | Combinable, str] = models.TextField()

        class Meta:
            app_label = "scalars"
            managed = False

    class _TokenRef(models.Model):
        keyed: models.ForeignKey[_TokenKeyed | Combinable, _TokenKeyed] = models.ForeignKey(
            _TokenKeyed,
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    if remedy == "related-filter":

        class _KeyFilter(FilterSet):
            label = CharFilter(field_name="label")

            class Meta:
                model = _TokenKeyed
                fields = []

        class _RefFilter(FilterSet):
            keyed = RelatedFilter(_KeyFilter, field_name="keyed")

            class Meta:
                model = _TokenRef
                fields = []

        filterset = _RefFilter
    else:
        monkeypatch.setitem(converters_mod.SCALAR_MAP, scalar_models.Base36Field, str)
        if remedy == "meta-fields":
            filterset = _meta_fields_set(_TokenRef, {"keyed": ["exact"]})
        elif remedy == "model-choice":
            filterset = _payload_set(_keyed_model_choice(_TokenKeyed), model=_TokenRef)
        else:
            filterset = _payload_set(CharFilter(field_name="keyed__token"), model=_TokenRef)

    meta = {"model": _TokenKeyed, "fields": ("label",)}
    _ = type("TokenKeyedType", (DjangoType,), {"Meta": type("Meta", (), meta)})
    _serve_on_a_column(_TokenRef, filterset)
    finalize_django_types()

    assert filter_lookup_table(filterset).by_input_attr


@pytest.mark.parametrize("base", [FilterSet, _CustomizingFilterSet])
def test_crossed_relation_refusal_keeps_projected_declaration_namespace(
    base: type[FilterSet],
) -> None:
    """The field and remedy path are both read from the child declaration's namespace."""
    child = _shelf_leaf_set(CharFilter(field_name="branch", lookup_expr="shelves"), base)
    parent = _book_shelf_set(child, FilterSet)
    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, parent)

    message = _build_refusal()
    assert f"{child.__name__}.leaf: CharFilter on 'branch'" in message
    assert f"reached through {parent.__name__}.shelf" in message
    assert "reads Branch.shelves, a ManyToOneRel" in message
    assert "through 'branch__shelves' in Meta.fields" in message
    assert "field_name 'branch__shelves__id'" in message
    assert "branch__branch" not in message


def test_projected_method_lookup_is_not_walked_for_its_remedy() -> None:
    """A child's ``method=`` owns its lookup token even when projection is required."""
    child = _shelf_leaf_set(
        CharFilter(field_name="branch", lookup_expr="shelves", method="filter_leaf"),
        _CustomizingFilterSet,
    )
    parent = _book_shelf_set(child, FilterSet)
    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, parent)

    message = _build_refusal()
    assert "reads Shelf.branch, a ForeignKey" in message
    assert "through 'branch' in Meta.fields" in message
    assert "field_name 'branch__id'" in message
    assert "branch__shelves__id" not in message


@isolate_apps("apps.scalars")
def test_generated_unmapped_filter_refuses_in_filterset_words_before_output_policy() -> None:
    """A selected plain output cannot make a declared generated filter give DjangoType advice."""

    class _Span(models.Model):
        starts_at: models.DateTimeField[
            str | datetime.datetime | datetime.date | Combinable,
            datetime.datetime,
        ] = models.DateTimeField()
        ends_at: models.DateTimeField[
            str | datetime.datetime | datetime.date | Combinable,
            datetime.datetime,
        ] = models.DateTimeField()
        elapsed = models.GeneratedField(
            expression=models.F("ends_at") - models.F("starts_at"),
            output_field=models.DurationField(),
            db_persist=True,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    class _SpanFilter(FilterSet):
        elapsed_text = CharFilter(field_name="elapsed")

        class Meta:
            model = _Span
            fields = []

    _serve_on_a_column(_Span, _SpanFilter)
    message = _build_refusal()
    assert "_SpanFilter: CharFilter on 'elapsed' reads _Span.elapsed, a DurationField" in message
    assert "register DurationField" in message
    assert "Meta.exclude" not in message


@isolate_apps("apps.scalars")
def test_projected_generated_filter_keeps_child_route_in_early_refusal() -> None:
    """A generated output refusal under a flat copy names the original child declaration."""

    class _Span(models.Model):
        starts_at: models.DateTimeField[
            str | datetime.datetime | datetime.date | Combinable,
            datetime.datetime,
        ] = models.DateTimeField()
        ends_at: models.DateTimeField[
            str | datetime.datetime | datetime.date | Combinable,
            datetime.datetime,
        ] = models.DateTimeField()
        elapsed = models.GeneratedField(
            expression=models.F("ends_at") - models.F("starts_at"),
            output_field=models.DurationField(),
            db_persist=True,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    class _SpanHost(models.Model):
        span: models.ForeignKey[_Span | Combinable, _Span] = models.ForeignKey(
            _Span,
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    class _SpanFilter(_CustomizingFilterSet):
        elapsed_text = CharFilter(field_name="elapsed")

        class Meta:
            model = _Span
            fields = []

    class _HostFilter(FilterSet):
        span = RelatedFilter(_SpanFilter, field_name="span")

        class Meta:
            model = _SpanHost
            fields = []

    _serve_model(_Span, None)
    _serve_on_a_column(_SpanHost, _HostFilter)
    message = _build_refusal()
    assert "_SpanFilter.elapsed_text: CharFilter on 'elapsed'" in message
    assert "reached through _HostFilter.span" in message
    assert "reads _Span.elapsed, a DurationField" in message
    assert "Meta.exclude" not in message


@pytest.mark.parametrize(
    "declare",
    [
        lambda: BooleanFilter(field_name="computed", lookup_expr="isnull"),
        lambda: CharFilter(field_name="computed", lookup_expr="icontains"),
    ],
    ids=["null-test", "text-pattern"],
)
@isolate_apps("apps.scalars")
def test_generated_file_policy_precedes_every_filter_input_arm(
    declare: Callable[[], Filter],
) -> None:
    """A Boolean or form-typed leaf cannot publish a generated file output."""

    class _GeneratedFile(models.Model):
        source: models.TextField[str | Combinable, str] = models.TextField()
        computed = models.GeneratedField(
            expression=models.Value("file"),
            output_field=models.FileField(),
            db_persist=True,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    filterset = _payload_set(declare(), model=_GeneratedFile)
    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(filterset)
    message = str(excinfo.value)
    assert "_GeneratedFile.computed, a FileField" in message
    assert "a database expression stores no file" in message
    assert "Meta.exclude" not in message


@isolate_apps("apps.scalars")
def test_generated_meta_fields_uses_filterset_output_policy_at_generation() -> None:
    """An unsupported generated field listed in Meta.fields fails before filter selection."""

    class _GeneratedFile(models.Model):
        computed = models.GeneratedField(
            expression=models.Value("file"),
            output_field=models.FileField(),
            db_persist=True,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    with pytest.raises(ConfigurationError) as excinfo:
        _ = type(
            "_GeneratedFilter",
            (FilterSet,),
            {
                "Meta": type(
                    "Meta",
                    (),
                    {"model": _GeneratedFile, "fields": {"computed": ["exact"]}},
                ),
            },
        )

    message = str(excinfo.value)
    assert "FilterSet _GeneratedFilter: Meta.fields names GeneratedField" in message
    assert "_GeneratedFile.computed" in message
    assert "remove the generated field from Meta.fields" in message
    assert "Meta.exclude" not in message


@isolate_apps("apps.scalars")
def test_generated_array_base_choices_refuse_before_transform_operand_typing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A mapped ``len`` operand cannot hide invalid choices on the generated array source."""
    patch_array_field(monkeypatch)

    class _GeneratedArray(models.Model):
        source: models.IntegerField[float | int | str | Combinable, int] = models.IntegerField()
        computed = models.GeneratedField(
            expression=models.Value(1),
            output_field=FakeArrayField(models.IntegerField(choices=[(1, "One")])),
            db_persist=True,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    filterset = _payload_set(NumberFilter(field_name="computed__len"), model=_GeneratedArray)
    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(filterset)
    message = str(excinfo.value)
    assert "_GeneratedArray.computed, a FakeArrayField" in message
    assert "base_field declares choices Django never validates" in message
    assert "Meta.exclude" not in message


@isolate_apps("apps.scalars")
def test_composite_target_key_is_not_offered_as_one_scalar_relation_remedy() -> None:
    """A single to_field join can coexist with a composite target identity."""

    class _CompositeTarget(models.Model):
        tenant: models.IntegerField[float | int | str | Combinable, int] = models.IntegerField()
        code: models.TextField[str | Combinable, str] = models.TextField()
        pk = models.CompositePrimaryKey("tenant", "code")
        join_code: models.TextField[str | Combinable, str] = models.TextField(unique=True)

        class Meta:
            app_label = "scalars"
            managed = False

    class _CompositeRef(models.Model):
        target: models.ForeignKey[
            _CompositeTarget | Combinable,
            _CompositeTarget,
        ] = models.ForeignKey(
            _CompositeTarget,
            to_field="join_code",
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "scalars"
            managed = False

    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(_payload_set(CharFilter(field_name="target"), model=_CompositeRef))
    message = str(excinfo.value)
    assert "field_name 'target__join_code'" in message
    assert "RelatedFilter" in message
    assert "Meta.fields" not in message
    assert "ModelChoiceFilter" not in message
    assert _build_input_fields(
        _payload_set(CharFilter(field_name="target__join_code"), model=_CompositeRef),
    )


def _relay_unmapped_target(
    *,
    composite: bool,
) -> tuple[type[models.Model], type[models.Model], str]:
    """Return a target with a public mapped NodeID distinct from its unmapped primary key."""
    target_columns: dict[str, object] = {"__module__": __name__, "label": models.TextField()}
    if composite:
        target_columns["tenant"] = models.IntegerField()
        target_columns["code"] = models.TextField()
        target_columns["pk"] = models.CompositePrimaryKey("tenant", "code")
        target_columns["join_code"] = models.TextField(unique=True)
        id_attr = "join_code"
    else:
        target_columns["token"] = scalar_models.Base36Field(primary_key=True)
        target_columns["code"] = models.TextField(unique=True)
        id_attr = "code"
    target_columns["Meta"] = type("Meta", (), {"app_label": "scalars", "managed": False})
    target = type("_RelayKeyed", (models.Model,), target_columns)
    reference = type(
        "_RelayRef",
        (models.Model,),
        {
            "__module__": __name__,
            "keyed": models.ForeignKey(
                target,
                to_field="join_code" if composite else None,
                on_delete=models.CASCADE,
            ),
            "Meta": type("Meta", (), {"app_label": "scalars", "managed": False}),
        },
    )
    return target, reference, id_attr


@pytest.mark.parametrize("composite", [False, True], ids=["unmapped-pk", "composite-pk"])
@pytest.mark.parametrize("replacement", [False, True], ids=["refusal", "generated-gid"])
@isolate_apps("apps.scalars")
def test_relay_public_id_distinguishes_generated_key_from_default_choice(
    *,
    composite: bool,
    replacement: bool,
) -> None:
    """A registered non-pk NodeID makes generated Meta.fields a GID without a pk scalar."""
    target, reference, id_attr = _relay_unmapped_target(composite=composite)
    meta = {
        "model": target,
        "fields": ("label",),
        "interfaces": (relay.Node,),
    }
    node = type(
        "RelayKeyedType",
        (DjangoType,),
        {"__annotations__": {id_attr: relay.NodeID[str]}, "Meta": type("Meta", (), meta)},
    )
    assert issubclass(node, DjangoType)
    filterset = (
        _meta_fields_set(reference, {"keyed": ["exact"]})
        if replacement
        else _payload_set(CharFilter(field_name="keyed"), model=reference)
    )
    _serve_on_a_column(reference, filterset)
    if replacement:
        finalize_django_types()
        assert isinstance(filterset.base_filters["keyed"], GlobalIDFilter)
        return

    message = _build_refusal()
    assert f"public {id_attr!r} GlobalID through 'keyed' in Meta.fields" in message
    assert "first register" not in message.split("ModelChoiceFilter")[0]
    if composite:
        assert "ModelChoiceFilter" not in message
    else:
        assert "ModelChoiceFilter" in message
        assert "first register Base36Field for _RelayKeyed.token in SCALAR_MAP" in message


@isolate_apps("apps.scalars")
@pytest.mark.parametrize("generated", [False, True], ids=["declared", "meta-fields"])
def test_relation_override_disables_generated_globalid_remedy(*, generated: bool) -> None:
    """An own relation override wins before the package's Relay selection."""
    target, reference, id_attr = _relay_unmapped_target(composite=False)
    meta = {"model": target, "fields": ("label",), "interfaces": (relay.Node,)}
    node = type(
        "RelayKeyedType",
        (DjangoType,),
        {"__annotations__": {id_attr: relay.NodeID[str]}, "Meta": type("Meta", (), meta)},
    )
    assert issubclass(node, DjangoType)
    override_meta = type(
        "Meta",
        (),
        {
            "model": reference,
            "fields": {"keyed": ["exact"]} if generated else [],
            "filter_overrides": {models.ForeignKey: {"filter_class": CharFilter}},
        },
    )
    attrs: dict[str, object] = {"Meta": override_meta}
    if not generated:
        attrs["leaf"] = CharFilter(field_name="keyed")
    filterset = type("OverriddenRefFilter", (FilterSet,), attrs)
    _serve_on_a_column(reference, filterset)

    message = _build_refusal()
    assert "ModelChoiceFilter" in message
    assert "first register Base36Field for _RelayKeyed.token in SCALAR_MAP" in message
    assert "Meta.fields" not in message


@pytest.mark.parametrize(
    "hook",
    ["lookup", "field"],
    ids=["filter-for-lookup", "filter-for-field"],
)
@pytest.mark.parametrize("delegating", [False, True], ids=["custom-class", "delegating"])
@pytest.mark.parametrize("replacement", [False, True], ids=["declared", "meta-fields"])
def test_relation_generation_hook_advice_follows_its_actual_selection(
    hook: str,
    *,
    delegating: bool,
    replacement: bool,
) -> None:
    """A public generation hook owns the relation leaf; optional identity advice stays honest."""

    class BranchNode(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("name",)
            interfaces = (relay.Node,)

    assert issubclass(BranchNode, DjangoType)

    class LookupHook(FilterSet):
        @classmethod
        @override
        def filter_for_lookup(
            cls,
            field: ModelField,
            lookup_type: str,
        ) -> tuple[type[Filter] | None, dict[str, object]]:
            if field.is_relation and not delegating:
                return CharFilter, {}
            return super().filter_for_lookup(field, lookup_type)

    class FieldHook(FilterSet):
        @classmethod
        @override
        def filter_for_field(
            cls,
            field: ModelField,
            field_name: str,
            lookup_expr: str | None = None,
        ) -> Filter | None:
            if field.is_relation and not delegating:
                return CharFilter(field_name=field_name, lookup_expr=lookup_expr or "exact")
            return super().filter_for_field(field, field_name, lookup_expr)

    base: type[FilterSet] = LookupHook if hook == "lookup" else FieldHook
    fields: dict[str, list[str]] | list[str] = {"branch": ["exact"]} if replacement else []
    attrs: dict[str, object] = {
        "Meta": type("Meta", (), {"model": library_models.Shelf, "fields": fields}),
    }
    if not replacement:
        attrs["leaf"] = CharFilter(field_name="branch")
    filterset = require(type("ShelfHooked", (base,), attrs), _is_filterset_class)

    _serve_on_a_column(library_models.Shelf, filterset)
    if replacement and delegating:
        finalize_django_types()
        assert isinstance(filterset.base_filters["branch"], GlobalIDFilter)
        return

    if replacement:
        assert isinstance(filterset.base_filters["branch"], CharFilter)
        assert not isinstance(filterset.base_filters["branch"], GlobalIDFilter)
    message = _build_refusal()
    assert "ModelChoiceFilter" in message
    assert "field_name 'branch__id'" in message
    assert "Meta.fields" not in message


def test_a_relation_leaf_whose_set_owns_its_lookup_hook_is_refused_without_the_key_route() -> None:
    """A set overriding ``filter_for_lookup`` is offered no generated key route for a relation.

    The relation's target has no Relay type, so its key is what a generated filter would
    compare; the set's own hook selects that filter, so ``Meta.fields`` is no remedy the
    package can promise: the refusal names the model-choice filters, the related column past
    the relation and a ``RelatedFilter``.
    """

    class LookupHook(FilterSet):
        @classmethod
        @override
        def filter_for_lookup(
            cls,
            field: ModelField,
            lookup_type: str,
        ) -> tuple[type[Filter] | None, dict[str, object]]:
            return super().filter_for_lookup(field, lookup_type)

    class ShelfLookupHook(LookupHook):
        leaf = CharFilter(field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = []

    _serve_on_a_column(library_models.Shelf, ShelfLookupHook)

    assert _build_refusal() == (
        "ShelfLookupHook: CharFilter on 'branch' reads Shelf.branch, a ForeignKey no SCALAR_MAP "
        "entry types, so nothing types its input; use a ModelChoiceFilter / "
        "ModelMultipleChoiceFilter, name the related column past it (field_name 'branch__id'), "
        "or filter the related row's own fields through a RelatedFilter."
    )


@pytest.mark.parametrize(
    ("column", "kind"),
    [
        pytest.param("span", "DurationField", id="duration"),
        pytest.param("blob", "BinaryField", id="binary"),
    ],
)
@isolate_apps("apps.scalars")
def test_a_filter_over_a_django_column_with_no_scalar_is_refused_naming_its_remedy(
    column: str,
    kind: str,
) -> None:
    """A Django column class ``SCALAR_MAP`` leaves out takes the column remedy for its class."""

    class _Unmapped(models.Model):
        span: models.DurationField[object, datetime.timedelta] = models.DurationField()
        blob: models.BinaryField[object, bytes | memoryview] = models.BinaryField()

        class Meta:
            app_label = "scalars"
            managed = False

    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(_payload_set(CharFilter(field_name=column), model=_Unmapped))

    assert str(excinfo.value) == (
        f"PayloadValueSet: CharFilter on {column!r} reads _Unmapped.{column}, a {kind} no "
        f"SCALAR_MAP entry types, so nothing types its input; register {kind} (or a class it "
        "subclasses) in SCALAR_MAP."
    )


def test_a_scalar_map_entry_builds_a_filter_over_an_unregistered_column(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The column remedy: a ``SCALAR_MAP`` entry for the column's class types the filter."""
    monkeypatch.setitem(converters_mod.SCALAR_MAP, scalar_models.Base36Field, str)

    assert _value_leaves(
        _payload_set(CharFilter(field_name="token"), model=scalar_models.OverrideSpecimen),
    ) == {"exact": str | None}


def test_a_relation_registered_as_json_keeps_the_column_scalar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A many-to-many a consumer registers as ``JSON`` is typed by that entry, not the form.

    ``ManyToManyField`` keeps Django's ``to_python`` / ``get_prep_value``, but Django
    prepares a related lookup's value through the target field, so the relation converts.
    Deliberate control: it is typed so before the rule too.
    """
    monkeypatch.setitem(converters_mod.SCALAR_MAP, models.ManyToManyField, strawberry.scalars.JSON)

    leaves = _value_leaves(
        _payload_set(CharFilter(field_name="genres"), model=library_models.Book),
    )
    assert leaves == {"exact": strawberry.scalars.JSON | None}


@pytest.mark.parametrize(
    "declare",
    [
        pytest.param(
            lambda: MultipleChoiceFilter(field_name="occurred_at__month", choices=[("5", "May")]),
            id="month-in-the-field-name",
        ),
        pytest.param(
            lambda: MultipleChoiceFilter(
                field_name="occurred_on",
                lookup_expr="year",
                choices=[("2021", "2021")],
            ),
            id="year-in-the-lookup",
        ),
        pytest.param(
            lambda: TypedMultipleChoiceFilter(
                field_name="occurred_at__year",
                coerce=int,
                choices=[("2021", "2021")],
            ),
            id="typed-year",
        ),
    ],
)
def test_a_multiple_choice_filter_past_a_transform_keeps_the_output_scalar(
    declare: Callable[[], Filter],
) -> None:
    """A converting transform output types each member, never the ``MultipleChoiceField`` text.

    Only a column holding values as given routes a ``MultipleChoiceFilter`` through its form.
    Deliberate control: ``[Int!]`` before the rule too.
    """
    assert list(_value_leaves(_payload_set(declare())).values()) == [list[int] | None]


class _UUIDTypedFilter(TypedFilter):
    """A package ``TypedFilter`` whose form field reads a UUID."""

    field_class: type[forms.UUIDField] = forms.UUIDField


class _OwnFilterTimeFilter(TimeFilter):
    """A consumer ``TimeFilter`` whose own ``filter`` decides what its value means."""

    @override
    def filter(self, qs: QuerySet[models.Model], value: object) -> QuerySet[models.Model]:
        return qs


class _TimeOfDateTimeField(forms.TimeField):
    """A consumer ``TimeField`` that also reads a ``datetime``, as its time of day."""

    @override
    def to_python(self, value: str | datetime.time | None) -> datetime.time | None:
        if isinstance(value, datetime.datetime):
            return value.time()
        return super().to_python(value)


class _TimeOfDateTimeFilter(TimeFilter):
    """A ``TimeFilter`` whose form field is a consumer parser (``_TimeOfDateTimeField``)."""

    field_class: type[forms.TimeField] = _TimeOfDateTimeField


class _EvenField(forms.IntegerField):
    """A consumer form field whose ``validate`` accepts even integers only."""

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if isinstance(value, int) and value % 2:
            raise ValidationError("odd")


class _EvenFilter(Filter):
    """A filter whose form field bounds its integers in ``validate`` (``_EvenField``)."""

    field_class: type[forms.IntegerField] = _EvenField


class _IssuedNumberField(forms.IntegerField):
    """A consumer form field whose ``validate`` accepts only a number some ``Issue`` holds."""

    @override
    def validate(self, value: object) -> None:
        super().validate(value)
        if not library_models.Issue.objects.filter(number=value).exists():
            raise ValidationError("no such issue")


class _IssuedNumberFilter(Filter):
    """A filter whose form field's ``validate`` reads the database (``_IssuedNumberField``)."""

    field_class: type[forms.IntegerField] = _IssuedNumberField


def _overridden_set(filter_class: type[Filter]) -> type[FilterSet]:
    """A ``ScalarSpecimen`` set selecting ``filter_class`` for ``occurred_at`` by override."""
    meta = {
        "model": scalar_models.ScalarSpecimen,
        "fields": {"occurred_at": ["exact"]},
        "filter_overrides": {models.DateTimeField: {"filter_class": filter_class}},
    }
    return type("OverriddenSpecimenSet", (FilterSet,), {"Meta": type("Meta", (), meta)})


def _no_value_refusal(
    subject: str,
    column: str,
    form: str,
    lookup: str,
) -> str:
    """The refusal of a leaf whose own form and lookup answer no value of its column."""
    return (
        f"{subject} is published as {column} values, but its own form field ({form}) and "
        f"lookup {lookup!r} answer no value of that column, so every value of its input would "
        "be refused or would constrain nothing (match every row); filter a transform of the "
        "column whose output its form cleans (a "
        'TimeFilter on `field_name="<column>__time"`), declare a filter class whose form '
        "cleans the column's kind, or read the value in `method=`."
    )


@dataclass(frozen=True)
class _NoValueCase:
    """A set whose one consumer leaf answers no value of its column, and what its refusal names."""

    make_set: Callable[[], type[FilterSet]]
    subject: str
    column: str
    form: str
    lookup: str


_NO_VALUE_CASES: dict[str, _NoValueCase] = {
    "time-on-a-datetime": _NoValueCase(
        lambda: _payload_set(TimeFilter(field_name="occurred_at")),
        "PayloadValueSet: TimeFilter on 'occurred_at'",
        "ScalarSpecimen.occurred_at",
        "TimeField",
        "exact",
    ),
    "uuid-on-an-integer": _NoValueCase(
        lambda: _payload_set(UUIDFilter(field_name="number"), model=library_models.Issue),
        "PayloadValueSet: UUIDFilter on 'number'",
        "Issue.number",
        "UUIDField",
        "exact",
    ),
    "uuid-on-a-big-integer": _NoValueCase(
        lambda: _payload_set(UUIDFilter(field_name="signed_big")),
        "PayloadValueSet: UUIDFilter on 'signed_big'",
        "ScalarSpecimen.signed_big",
        "UUIDField",
        "exact",
    ),
    "duration-on-an-integer": _NoValueCase(
        lambda: _payload_set(DurationFilter(field_name="number"), model=library_models.Issue),
        "PayloadValueSet: DurationFilter on 'number'",
        "Issue.number",
        "DurationField",
        "exact",
    ),
    "duration-on-a-decimal": _NoValueCase(
        lambda: _payload_set(DurationFilter(field_name="price")),
        "PayloadValueSet: DurationFilter on 'price'",
        "ScalarSpecimen.price",
        "DurationField",
        "exact",
    ),
    "typed-uuid-on-an-integer": _NoValueCase(
        lambda: _payload_set(_UUIDTypedFilter(field_name="number"), model=library_models.Issue),
        "PayloadValueSet: _UUIDTypedFilter on 'number'",
        "Issue.number",
        "UUIDField",
        "exact",
    ),
    "boolean-on-a-date": _NoValueCase(
        lambda: _payload_set(BooleanFilter(field_name="occurred_on")),
        "PayloadValueSet: BooleanFilter on 'occurred_on'",
        "ScalarSpecimen.occurred_on",
        "NullBooleanField",
        "exact",
    ),
    "time-icontains-on-a-datetime": _NoValueCase(
        lambda: _payload_set(TimeFilter(field_name="occurred_at", lookup_expr="icontains")),
        "PayloadValueSet: TimeFilter on 'occurred_at'",
        "ScalarSpecimen.occurred_at",
        "TimeField",
        "icontains",
    ),
    "time-gte-on-a-datetime": _NoValueCase(
        lambda: _payload_set(TimeFilter(field_name="occurred_at", lookup_expr="gte")),
        "PayloadValueSet: TimeFilter on 'occurred_at'",
        "ScalarSpecimen.occurred_at",
        "TimeField",
        "gte",
    ),
    "times-in-on-a-datetime": _NoValueCase(
        lambda: _payload_set(_TimesInFilter(field_name="occurred_at", lookup_expr="in")),
        "PayloadValueSet: _TimesInFilter on 'occurred_at'",
        "ScalarSpecimen.occurred_at",
        "TimeInField",
        "in",
    ),
    "date-range-on-an-integer": _NoValueCase(
        lambda: _payload_set(
            DateFromToRangeFilter(field_name="number"),
            model=library_models.Issue,
        ),
        "PayloadValueSet: DateFromToRangeFilter on 'number'",
        "Issue.number",
        "DateField",
        "exact",
    ),
    "override-time-on-a-datetime": _NoValueCase(
        lambda: _overridden_set(TimeFilter),
        "OverriddenSpecimenSet: TimeFilter on 'occurred_at'",
        "ScalarSpecimen.occurred_at",
        "TimeField",
        "exact",
    ),
    "date-on-an-integer-choice-column": _NoValueCase(
        lambda: _payload_set(DateFilter(field_name="tier"), model=_SHELF),
        "PayloadValueSet: DateFilter on 'tier'",
        "Shelf.tier",
        "DateField",
        "exact",
    ),
    "json-form-on-a-date": _NoValueCase(
        lambda: _payload_set(_JSONFormFilter(field_name="occurred_on")),
        "PayloadValueSet: _JSONFormFilter on 'occurred_on'",
        "ScalarSpecimen.occurred_on",
        "JSONField",
        "exact",
    ),
    "bare-in-on-a-big-integer": _NoValueCase(
        lambda: _payload_set(Filter(field_name="signed_big", lookup_expr="in")),
        "PayloadValueSet: Filter on 'signed_big'",
        "ScalarSpecimen.signed_big",
        "Field",
        "in",
    ),
    "ip-address-form-on-a-big-integer": _NoValueCase(
        lambda: _payload_set(_IPAddressFormFilter(field_name="signed_big")),
        "PayloadValueSet: _IPAddressFormFilter on 'signed_big'",
        "ScalarSpecimen.signed_big",
        "GenericIPAddressField",
        "exact",
    ),
    "url-form-on-an-integer": _NoValueCase(
        lambda: _payload_set(
            _URLFormFilter(field_name="number", assume_scheme="https"),
            model=library_models.Issue,
        ),
        "PayloadValueSet: _URLFormFilter on 'number'",
        "Issue.number",
        "URLField",
        "exact",
    ),
    "multiple-choice-form-on-text": _NoValueCase(
        lambda: _payload_set(
            _MultipleChoiceFormFilter(field_name="label", choices=[("alpha", "Alpha")]),
        ),
        "PayloadValueSet: _MultipleChoiceFormFilter on 'label'",
        "ScalarSpecimen.label",
        "MultipleChoiceField",
        "exact",
    ),
    "integer-coerce-on-a-text-choice-column": _NoValueCase(
        lambda: _payload_set(
            _TypedChoicesInFilter(
                field_name="condition",
                lookup_expr="in",
                choices=[("good", "Good"), ("1", "One")],
                coerce=int,
            ),
            model=_SHELF,
        ),
        "PayloadValueSet: _TypedChoicesInFilter on 'condition'",
        "Shelf.condition",
        "TypedChoiceInField",
        "in",
    ),
    "float-coerce-on-a-second-text-choice-column": _NoValueCase(
        lambda: _payload_set(
            _TypedChoicesInFilter(
                field_name="circulation_status",
                lookup_expr="in",
                choices=[("available", "Available"), ("1", "One")],
                coerce=float,
            ),
            model=library_models.Book,
        ),
        "PayloadValueSet: _TypedChoicesInFilter on 'circulation_status'",
        "Book.circulation_status",
        "TypedChoiceInField",
        "in",
    ),
    "decimal-coerce-on-text": _NoValueCase(
        lambda: _payload_set(
            _TypedChoicesInFilter(
                field_name="label",
                lookup_expr="in",
                choices=[("all", "All"), ("alpha", "Alpha")],
                coerce=decimal.Decimal,
            ),
        ),
        "PayloadValueSet: _TypedChoicesInFilter on 'label'",
        "ScalarSpecimen.label",
        "TypedChoiceInField",
        "in",
    ),
    "integer-coerce-range-on-a-text-choice-column": _NoValueCase(
        lambda: _payload_set(
            _TypedChoicesRangeFilter(
                field_name="condition",
                lookup_expr="range",
                choices=[("good", "Good"), ("1", "One")],
                coerce=int,
            ),
            model=_SHELF,
        ),
        "PayloadValueSet: TypedChoicesRangeFilter on 'condition'",
        "Shelf.condition",
        "TypedChoiceRangeField",
        "range",
    ),
}


@pytest.mark.parametrize("case", list(_NO_VALUE_CASES))
def test_a_declared_filter_no_value_of_its_column_answers_is_refused(case: str) -> None:
    """A consumer leaf typed by its column whose own form and lookup answer none of it is refused.

    The leaf compares the column with no transform, so it publishes the column's scalar or
    choice enum, and each value of it is asked of the filter's own form field (validators
    off) and lookup on the declaring set's model: a ``TimeField`` cannot read a ``datetime``
    (nor a ``JSONField`` form decode a ``date``), a ``UUIDField`` reads no integer, a
    ``timedelta`` cannot be prepared for an integer or a decimal, and a ``BooleanFilter``
    cleans every date to no constraint. Every member of a CSV filter and each axis of a
    range filter is asked as that arm hands it, a ``Meta.filter_overrides`` selection as a
    declaration, and a choice column by every member of its enum.
    """
    entry = _NO_VALUE_CASES[case]
    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(entry.make_set())
    assert str(excinfo.value) == _no_value_refusal(
        entry.subject,
        entry.column,
        entry.form,
        entry.lookup,
    )


@pytest.mark.parametrize(
    "base",
    [FilterSet, _CustomizingFilterSet],
    ids=["rebound-child", "projected-child"],
)
def test_a_child_leaf_no_value_of_its_column_answers_is_refused_under_its_declaration(
    base: type[FilterSet],
) -> None:
    """A ``RelatedFilter`` copy is asked as the child set declares it, and named so.

    The copy is rebound onto the parent's path (``shelf__tier``) or projected as a
    runtime-built ``Projected<Class>`` bound to the child set; either way the child's own
    filter is asked on the child set's model, and the refusal names its attribute there
    and the ``RelatedFilter`` it was reached through.
    """
    child = _shelf_leaf_set(DateFilter(field_name="tier"), base)
    parent = _book_shelf_set(child, FilterSet)
    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, parent)

    assert _build_refusal() == _no_value_refusal(
        f"{child.__name__}.leaf: DateFilter on 'tier' (reached through {parent.__name__}.shelf)",
        "Shelf.tier",
        "DateField",
        "exact",
    )


def _generated_specimen_set() -> type[FilterSet]:
    """A ``ScalarSpecimen`` set whose leaves django-filter generates from ``Meta.fields``."""
    meta = {
        "model": scalar_models.ScalarSpecimen,
        "fields": {
            "occurred_at": [
                "exact",
                "lt",
                "in",
                "range",
            ],
            "signed_big": ["exact", "in"],
        },
    }
    return type("GeneratedSpecimenSet", (FilterSet,), {"Meta": type("Meta", (), meta)})


@pytest.mark.parametrize(
    "make_set",
    [
        pytest.param(
            lambda: _payload_set(DateFilter(field_name="occurred_at")),
            id="date-on-a-datetime",
        ),
        pytest.param(
            lambda: _payload_set(CharFilter(field_name="number"), model=library_models.Issue),
            id="text-on-an-integer",
        ),
        pytest.param(
            lambda: _payload_set(NumberFilter(field_name="number"), model=library_models.Issue),
            id="number-on-an-integer",
        ),
        pytest.param(
            lambda: _payload_set(BooleanFilter(field_name="number"), model=library_models.Issue),
            id="boolean-on-an-integer",
        ),
        pytest.param(
            lambda: _payload_set(BooleanFilter(field_name="tier"), model=_SHELF),
            id="boolean-on-an-integer-choice-column",
        ),
        pytest.param(
            lambda: _payload_set(
                NumberFilter(field_name="number", min_value=18),
                model=library_models.Issue,
            ),
            id="number-bounded-by-a-validator",
        ),
        pytest.param(
            lambda: _payload_set(TimeFilter(field_name="occurred_at", method="filter_value")),
            id="time-method",
        ),
        pytest.param(
            lambda: _payload_set(_OwnFilterTimeFilter(field_name="occurred_at")),
            id="time-own-filter",
        ),
        pytest.param(
            lambda: _payload_set(_TimeOfDateTimeFilter(field_name="occurred_at")),
            id="time-consumer-parser",
        ),
        pytest.param(
            lambda: _payload_set(TimeFilter(field_name="occurred_at__time")),
            id="time-of-a-transform",
        ),
        pytest.param(
            lambda: _payload_set(TimeFilter(field_name="occurred_at", lookup_expr="isnull")),
            id="time-null-test",
        ),
        pytest.param(lambda: _overridden_set(DateFilter), id="override-date-on-a-datetime"),
        pytest.param(
            lambda: _payload_set(_EvenFilter(field_name="number"), model=library_models.Issue),
            id="integer-bounded-by-validate",
        ),
        pytest.param(_generated_specimen_set, id="generated-leaves"),
    ],
)
def test_a_declared_filter_some_value_of_its_column_answers_builds(
    make_set: Callable[[], type[FilterSet]],
) -> None:
    """A leaf one value of its column answers builds, and leaves the probe does not ask build.

    A ``DateFilter`` on a ``DateTimeField`` answers a date (lossy: Django warns, the probe
    raises nothing under ``filterwarnings = error``), a text or number form an integer, a
    ``BooleanFilter`` an integer and a member of an integer choice enum, and a validator
    or a ``validate`` bounding the values of a kind never refuses it. A ``method=`` filter,
    a consumer ``filter`` override and a consumer parser own what a value means; a
    transform and a null test type their leaf on other arms; generated leaves are
    django-filter's choice.
    """
    assert _build_input_fields(make_set())


def test_a_declared_lookup_no_field_registers_is_refused_before_its_form_is_asked() -> None:
    """A ``lookup_expr`` no field registers is refused when the set publishes, naming the lookup.

    Django resolves ``unaccent`` only where ``django.contrib.postgres`` registers it, so the
    leaf could answer no request; the set's publication refuses it
    (``filters/base.py::refuse_unresolvable_lookup``) before the input build asks its form.
    """
    payload_set = _payload_set(
        NumberFilter(field_name="number", lookup_expr="unaccent"),
        model=library_models.Issue,
    )
    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(payload_set)
    assert str(excinfo.value).startswith(
        "FilterSet PayloadValueSet: NumberFilter 'value' has field_name 'number' and "
        "lookup_expr 'unaccent', but Django resolves no transform or lookup 'unaccent' on "
        "Issue.number (IntegerField)",
    )


def test_a_projected_child_leaf_some_value_of_its_column_answers_builds() -> None:
    """A projected child leaf is asked on the child set, where its own ``filter`` runs.

    The runtime-built ``Projected<Class>`` reads its owner per request, so the probe asks
    the child set's own ``NumberFilter``, which cleans a member of the tier enum.
    """
    child = _shelf_leaf_set(NumberFilter(field_name="tier"), _CustomizingFilterSet)
    parent = _book_shelf_set(child, FilterSet)
    _serve_model(library_models.Shelf, None)
    _serve_model(library_models.Book, parent)

    finalize_django_types()


@pytest.mark.django_db
def test_a_validate_reading_the_database_is_not_run_at_schema_build(
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """The probe judges the kind only: a form field's ``validate`` never runs, nor its query."""
    with django_assert_num_queries(0):
        assert _build_input_fields(
            _payload_set(_IssuedNumberFilter(field_name="number"), model=library_models.Issue),
        )


@pytest.mark.parametrize(
    ("filter_class", "lookup"),
    [
        pytest.param(_TypedChoicesInFilter, "in", id="in"),
        pytest.param(_TypedChoicesRangeFilter, "range", id="range"),
    ],
)
def test_a_consumer_coerce_is_not_run_at_schema_build(
    filter_class: type[Filter],
    lookup: str,
) -> None:
    """A typed choice form whose ``coerce`` is consumer code is a parser of its own: not asked.

    The keys share no value with the date column, so asked they would refuse the leaf; the
    consumer's ``coerce`` owns what each key means, so the leaf builds and the build never
    calls it.
    """
    calls: list[object] = []

    def coerce(value: object) -> object:
        calls.append(value)
        return value

    assert _build_input_fields(
        _payload_set(
            filter_class(
                field_name="occurred_on",
                lookup_expr=lookup,
                choices=[("x", "X")],
                coerce=coerce,
            ),
        ),
    )
    assert calls == []


@pytest.mark.parametrize(
    ("wrapper", "lookup"),
    [
        pytest.param(BaseInFilter, "in", id="in"),
        pytest.param(BaseRangeFilter, "range", id="range"),
    ],
)
def test_a_consumer_member_form_defining_clean_is_not_run_at_schema_build(
    wrapper: type[DjangoBaseCSVFilter],
    lookup: str,
) -> None:
    """A CSV member form whose own class defines ``clean`` is a parser of its own: not asked.

    django-filter's ``BaseCSVField`` resolves ``clean`` and hands each member to the classes
    after it, so the consumer's ``clean`` is read too; it owns what a member means (a
    ``DateField`` asked an integer column's sample would refuse the leaf), so the leaf builds
    and the build never runs it.
    """
    calls: list[object] = []

    class CountedDateField(forms.DateField):
        @override
        def clean(self, value: object) -> object:
            calls.append(value)
            return object_result(super().clean, value)

    counted: type[Filter] = type(
        "CountedDatesFilter",
        (wrapper, DateFilter),
        {"field_class": CountedDateField},
    )
    assert _build_input_fields(
        _payload_set(
            counted(field_name="number", lookup_expr=lookup),
            model=library_models.Issue,
        ),
    )
    assert calls == []


@pytest.mark.django_db
def test_callable_member_choices_are_not_evaluated_at_schema_build(
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """A CSV choice form's callable ``choices`` stay deferred: no call, no query at build.

    Its keys are evaluated only by the form each request builds, so the leaf is asked the
    column's samples, which a ``ChoiceField`` with ``validate`` off reads, and builds.
    """
    calls: list[None] = []

    def labels() -> list[tuple[str, str]]:
        calls.append(None)
        return [(category.name, category.name) for category in Category.objects.all()]

    with django_assert_num_queries(0):
        assert _build_input_fields(
            _payload_set(
                _ChoicesInFilter(field_name="occurred_on", lookup_expr="in", choices=labels),
            ),
        )
    assert calls == []


@pytest.mark.parametrize(
    "make_set",
    [
        pytest.param(
            lambda: _payload_set(
                _ChoicesInFilter(
                    field_name="label",
                    lookup_expr="in",
                    choices=Category.objects.values_list("name", "name"),
                ),
            ),
            id="csv-member-on-text",
        ),
        pytest.param(
            lambda: _payload_set(
                _ChoicesInFilter(
                    field_name="occurred_on",
                    lookup_expr="in",
                    choices=Category.objects.values_list("name", "name"),
                ),
            ),
            id="csv-member-on-a-date",
        ),
        pytest.param(
            lambda: _payload_set(
                ChoiceFilter(
                    field_name="condition",
                    choices=Category.objects.values_list("name", "name"),
                ),
                model=_SHELF,
            ),
            id="choice-column",
        ),
        pytest.param(
            lambda: _payload_set(
                TypedChoiceFilter(
                    field_name="condition",
                    choices=Category.objects.values_list("name", "name"),
                ),
                model=_SHELF,
            ),
            id="typed-choice-column",
        ),
        pytest.param(
            lambda: _payload_set(
                TypedMultipleChoiceFilter(
                    field_name="condition",
                    choices=Category.objects.values_list("name", "name"),
                ),
                model=_SHELF,
            ),
            id="typed-multiple-choice-column",
        ),
        pytest.param(
            lambda: _payload_set(
                _TypedChoicesInFilter(
                    field_name="condition",
                    lookup_expr="in",
                    choices=Category.objects.values_list("name", "name"),
                ),
                model=_SHELF,
            ),
            id="typed-csv-in-on-a-choice-column",
        ),
        pytest.param(
            lambda: _payload_set(
                _TypedChoicesRangeFilter(
                    field_name="condition",
                    lookup_expr="range",
                    choices=Category.objects.values_list("name", "name"),
                ),
                model=_SHELF,
            ),
            id="typed-csv-range-on-a-choice-column",
        ),
    ],
)
@pytest.mark.django_db
def test_queryset_choices_are_not_evaluated_at_schema_build(
    make_set: Callable[[], type[FilterSet]],
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """A ``QuerySet`` handed as ``choices`` is left to the form each request builds: no query.

    Neither the no-value ask (text and date columns, and each sample of a choice column a
    typed CSV ``in`` or ``range`` is asked) nor the choice-column check reads it, nor building
    a Django ``TypedChoiceField`` or ``TypedMultipleChoiceField``, which normalizes its
    ``choices``, so a table the queryset names need not exist when the schema builds.
    """
    payload_set = make_set()
    with django_assert_num_queries(0):
        assert _build_input_fields(payload_set)


#: A consumer CSV filter whose every member its form reads as a list of choices.
_MultipleChoicesInFilter: type[Filter] = type(
    "MultipleChoicesInFilter",
    (BaseInFilter, MultipleChoiceFilter),
    {},
)


def _counted_categories(calls: list[None]) -> Callable[[], list[tuple[str, str]]]:
    """Choices reading the categories table, recording each evaluation."""

    def labels() -> list[tuple[str, str]]:
        calls.append(None)
        return [(category.name, category.name) for category in Category.objects.all()]

    return labels


@pytest.mark.parametrize(
    "filter_class",
    [
        pytest.param(_ChoicesInFilter, id="choice"),
        pytest.param(_MultipleChoicesInFilter, id="multiple-choice"),
    ],
)
@pytest.mark.django_db
def test_choice_iterator_member_choices_on_a_column_without_choices_build_unevaluated(
    filter_class: type[Filter],
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """Django's ``CallableChoiceIterator`` as a CSV member's ``choices`` stays deferred.

    Django's ``normalize_choices`` leaves the iterator unread, so its keys are evaluated
    only by the form each request builds: the leaf is asked the text column's samples,
    builds, and the build calls nothing and runs no query.
    """
    calls: list[None] = []
    payload_set = _payload_set(
        filter_class(
            field_name="label",
            lookup_expr="in",
            choices=CallableChoiceIterator(_counted_categories(calls)),
        ),
    )
    with django_assert_num_queries(0):
        assert _build_input_fields(payload_set)
    assert calls == []


def test_iterator_member_choices_on_a_text_column_build() -> None:
    """An iterator declared as a CSV choice member's ``choices`` is asked its keys, as a list is.

    Each copy of the filter holds its own copy of the iterator, so the keys the form reads
    are the declared ones, and a key spelling a text value answers.
    """
    assert _build_input_fields(
        _payload_set(
            _ChoicesInFilter(
                field_name="label",
                lookup_expr="in",
                choices=iter([("alpha", "Alpha")]),
            ),
        ),
    )


def test_iterator_member_choices_of_a_multiple_choice_member_are_refused_as_a_list_is() -> None:
    """A CSV ``MultipleChoiceFilter`` reads no single value whatever iterable its ``choices`` are.

    The iterator is asked as a list of pairs would be, so the leaf is refused naming its
    member form.
    """
    payload_set = _payload_set(
        _MultipleChoicesInFilter(
            field_name="label",
            lookup_expr="in",
            choices=iter([("alpha", "Alpha")]),
        ),
    )
    with pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(payload_set)
    assert str(excinfo.value) == _no_value_refusal(
        "PayloadValueSet: MultipleChoicesInFilter on 'label'",
        "ScalarSpecimen.label",
        "MultipleChoiceInField",
        "in",
    )


@pytest.mark.parametrize(
    "base",
    [FilterSet, _CustomizingFilterSet],
    ids=["plain-child", "child-init"],
)
def test_an_expanded_child_leafs_lazy_choices_are_not_evaluated_at_schema_build(
    base: type[FilterSet],
) -> None:
    """A child leaf's lazy ``choices`` stay unread through the child set and its parent's copy.

    The child set publishes the leaf, and its parent's ``RelatedFilter`` copies it (rebound
    onto ``shelf__condition``, or projected when the child set overrides ``__init__``); each
    copy's Django ``TypedChoiceField`` is built at schema build without evaluating the
    ``SimpleLazyObject``, and the test holds no database access.
    """
    calls: list[None] = []

    def conditions() -> list[tuple[str, str]]:
        calls.append(None)
        return _conditions_on_record()

    child = _shelf_leaf_set(
        TypedChoiceFilter(field_name="condition", choices=SimpleLazyObject(conditions)),
        base,
    )
    parent = _book_shelf_set(child, base)
    _serve_model(library_models.Shelf, child)
    _serve_model(library_models.Book, parent)

    finalize_django_types()
    assert "shelf__leaf" in filter_lookup_table(parent).by_input_attr
    assert calls == []


@pytest.mark.django_db
def test_a_filter_overrides_typed_choice_on_a_column_without_choices_is_refused_unevaluated(
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """A ``Meta.filter_overrides`` typed choice leaf on a text column is refused, its queryset unrun.

    The column declares no ``choices``, so no choice enum types the leaf; the refusal reads
    its form field on a copy that hands the ``QuerySet`` over unread, so no query runs.
    """
    payload_set = _overridden_text_set(
        lambda _field: {"choices": Category.objects.values_list("name", "name")},
    )
    with django_assert_num_queries(0), pytest.raises(ConfigurationError) as excinfo:
        _ = _build_input_fields(payload_set)
    assert str(excinfo.value) == _OVERRIDDEN_TEXT_REFUSAL


def _overridden_text_set(
    extra: Callable[[models.Field[object, object]], dict[str, object]],
) -> type[FilterSet]:
    """A ``ScalarSpecimen`` set whose generated ``label`` leaf is a ``TypedChoiceFilter``."""
    meta = {
        "model": scalar_models.ScalarSpecimen,
        "fields": {"label": ["exact"]},
        "filter_overrides": {
            models.TextField: {"filter_class": TypedChoiceFilter, "extra": extra},
        },
    }
    return type("OverriddenTextSet", (FilterSet,), {"Meta": type("Meta", (), meta)})


#: The refusal of the overridden ``label`` leaf: its column declares no ``choices``.
_OVERRIDDEN_TEXT_REFUSAL = (
    "OverriddenTextSet: TypedChoiceFilter on 'label' reads ScalarSpecimen.label, which declares "
    "no `choices`, so no choice enum types its input (the filter's own `choices` never feed the "
    "enum); declare `choices` on the column it filters (a `choices=` list of pairs, or a "
    "`TextChoices` / `IntegerChoices` class's `.choices`), or filter the column through a "
    "non-choice filter (`CharFilter`, `NumberFilter`, `DateFromToRangeFilter`, its lookups in "
    "Meta.fields, or `CharFilter(method=...)` for a method filter)."
)


def _counted_lazy(calls: list[None]) -> object:
    """A ``SimpleLazyObject`` recording each evaluation."""
    return SimpleLazyObject(_counted_callable(calls))


def _counted_callable(calls: list[None]) -> Callable[[], list[tuple[str, str]]]:
    """A callable recording each evaluation."""

    def choices() -> list[tuple[str, str]]:
        calls.append(None)
        return [("good", "Good")]

    return choices


_ChoicesMaker: TypeAlias = Callable[[list[None]], object]

#: Declared ``choices`` by kind, each made over the evaluation record it is handed, and whether
#: only a request's form evaluates them.
_DEFERRED_KIND_CASES: dict[str, tuple[_ChoicesMaker, bool]] = {
    "list": (lambda _calls: [("good", "Good")], False),
    "iterator": (lambda _calls: iter([("good", "Good")]), False),
    "choices-class": (lambda _calls: _SHELF.Condition, False),
    "mapping": (lambda _calls: {"good": "Good"}, False),
    "callable": (_counted_callable, True),
    "lazy-promise": (lambda calls: lazy(_counted_callable(calls), list)(), True),
    "simple-lazy-object": (_counted_lazy, True),
    "choice-iterator": (lambda calls: CallableChoiceIterator(_counted_callable(calls)), True),
    "queryset": (lambda _calls: Category.objects.values_list("name", "name"), True),
}


@pytest.mark.parametrize("kind", list(_DEFERRED_KIND_CASES))
def test_defers_choices_reads_each_lazy_kind_without_evaluating_it(kind: str) -> None:
    """Which declared ``choices`` only a request's form evaluates, asked without evaluating any.

    A callable, a ``lazy()`` promise, a ``SimpleLazyObject``, Django's
    ``CallableChoiceIterator`` and a ``QuerySet`` are deferred; a list, an iterator, a mapping
    and a ``Choices`` class are read at build. The test holds no database access, and no
    deferred value is called.
    """
    make_choices, expected = _DEFERRED_KIND_CASES[kind]
    calls: list[None] = []
    declared = ChoiceFilter(field_name="condition", choices=make_choices(calls))
    assert defers_choices(declared) is expected
    assert calls == []


def test_defers_choices_is_false_for_a_filter_declaring_no_choices() -> None:
    """A choice filter declaring no ``choices`` defers nothing."""
    assert defers_choices(ChoiceFilter(field_name="condition")) is False


@pytest.mark.parametrize("kind", ["simple-lazy-object", "queryset"])
def test_copied_filter_builds_a_django_choice_field_leaving_the_declaration_unread(
    kind: str,
) -> None:
    """The build's copy builds a Django ``TypedChoiceField`` evaluating nothing, the declaration kept.

    The copy hands its form field the choices unread; the declaration keeps the very object
    it declared, unevaluated. The test holds no database access.
    """
    make_choices, _deferred = _DEFERRED_KIND_CASES[kind]
    calls: list[None] = []
    declared_choices = make_choices(calls)
    declared = TypedChoiceFilter(field_name="condition", choices=declared_choices)

    field = copied_filter(declared).field

    assert isinstance(field, forms.TypedChoiceField)
    assert declared.extra["choices"] is declared_choices
    assert calls == []


def test_copied_filter_choices_answer_the_declared_ones_when_read() -> None:
    """A copy's form field answers its declared choices, evaluating that copy's lazy ones only.

    Django's ``valid_value`` reads the choices the copy handed over unread, so it accepts a
    declared key. Each copy holds its own copy of the ``SimpleLazyObject``, so a second copy
    evaluates afresh: the declaration keeps nothing a copy evaluated.
    """
    calls: list[None] = []
    declared = TypedChoiceFilter(field_name="condition", choices=_counted_lazy(calls))

    for evaluated in (1, 2):
        field = copied_filter(declared).field
        assert isinstance(field, forms.TypedChoiceField)
        assert field.valid_value("good")
        assert len(calls) == evaluated


class _CountingChoiceField(forms.TypedChoiceField):
    """A consumer choice form whose ``__init__`` reads ``len()`` of its own ``choices``."""

    choice_count: int

    def __init__(
        self,
        *,
        choices: Iterable[tuple[str, str]],
        coerce: Callable[[str], object] = str,
        required: bool,
        label: str | None,
    ) -> None:
        super().__init__(choices=choices, coerce=coerce, required=required, label=label)
        field_choices: object = self.choices
        assert isinstance(field_choices, Sized)
        self.choice_count = len(field_choices)


class _CountingFieldClassFilter(TypedChoiceFilter):
    """A ``TypedChoiceFilter`` whose ``field_class`` counts its ``choices`` when built."""

    field_class: type[forms.TypedChoiceField] = _CountingChoiceField


class _CountingFieldOverrideFilter(TypedChoiceFilter):
    """A ``TypedChoiceFilter`` whose ``field`` override reads ``len()`` of its ``choices``."""

    @property
    @override
    def field(self) -> forms.Field:
        choices = dict_of(self.extra).get("choices")
        assert isinstance(choices, Sized)
        self.choice_count: int = len(choices)
        return super().field


@pytest.mark.parametrize(
    "filter_class",
    [
        pytest.param(_CountingFieldClassFilter, id="field-class-init"),
        pytest.param(_CountingFieldOverrideFilter, id="field-override"),
    ],
)
def test_consumer_code_counting_lazy_choices_builds_evaluating_them_as_declared(
    filter_class: type[Filter],
) -> None:
    """Consumer code reading ``len()`` of a ``SimpleLazyObject`` ``choices`` builds the input.

    The build's copy hands the choices over in a wrapper answering ``len()`` by iterating
    them, so the consumer evaluates them where it is built, once per form field the build
    reads, as it would on the declared value.
    """
    calls: list[None] = []
    payload_set = _payload_set(
        filter_class(field_name="condition", choices=_counted_lazy(calls)),
        model=_SHELF,
    )
    assert _build_input_fields(payload_set)
    assert len(calls) == _COUNTING_BUILD_EVALUATIONS


@pytest.mark.parametrize(
    "filter_class",
    [
        pytest.param(_CountingFieldClassFilter, id="field-class-init"),
        pytest.param(_CountingFieldOverrideFilter, id="field-override"),
    ],
)
@pytest.mark.django_db
def test_consumer_code_counting_queryset_choices_builds_running_them_as_declared(
    filter_class: type[Filter],
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """Consumer code reading ``len()`` of a ``QuerySet`` ``choices`` builds the input.

    The queryset runs where the consumer counts it, once per form field the build reads (each
    copy's queryset caches its rows), as it would on the declared value.
    """
    payload_set = _payload_set(
        filter_class(field_name="condition", choices=Category.objects.values_list("name", "name")),
        model=_SHELF,
    )
    with django_assert_num_queries(_COUNTING_BUILD_EVALUATIONS):
        assert _build_input_fields(payload_set)


#: The evaluations a consumer counting its deferred ``choices`` runs while the input builds.
_COUNTING_BUILD_EVALUATIONS = 2


def _shelf_conditions_lazily() -> object:
    """A ``SimpleLazyObject`` over the ``Shelf`` conditions on record."""
    return SimpleLazyObject(_conditions_on_record)


def _shelf_codes_queryset() -> object:
    """A ``QuerySet`` of ``Shelf`` code pairs."""
    return _SHELF.objects.values_list("code", "code")


@pytest.mark.parametrize(
    "make_choices",
    [
        pytest.param(_shelf_conditions_lazily, id="simple-lazy-object"),
        pytest.param(_shelf_codes_queryset, id="queryset"),
    ],
)
@pytest.mark.django_db
def test_copied_filter_choices_are_true_without_evaluating(
    make_choices: Callable[[], object],
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """The copy's wrapped ``choices`` answer a truth test without reading the database."""
    copied = copied_filter(TypedChoiceFilter(field_name="condition", choices=make_choices()))
    with django_assert_num_queries(0):
        assert dict_of(copied.extra).get("choices")


@pytest.mark.parametrize(
    "make_choices",
    [
        pytest.param(_shelf_conditions_lazily, id="simple-lazy-object"),
        pytest.param(_shelf_codes_queryset, id="queryset"),
    ],
)
@pytest.mark.django_db
def test_copied_filter_choices_answer_len_by_counting_them_once(
    make_choices: Callable[[], object],
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """The copy's wrapped ``choices`` count what iterating them answers, reading them once.

    Both the ``SimpleLazyObject`` and the ``QuerySet`` cache what they read, so a second
    ``len()`` runs no query.
    """
    branch = library_models.Branch.objects.create(name="Counted")
    _ = _SHELF.objects.create(branch=branch, code="c", condition="good")
    copied = copied_filter(TypedChoiceFilter(field_name="condition", choices=make_choices()))
    choices = dict_of(copied.extra).get("choices")
    assert isinstance(choices, Sized)
    with django_assert_num_queries(1):
        assert len(choices) == 1
        assert len(choices) == 1


class _TableCode:
    """A consumer ``coerce`` class reading each key from its own table: ``KeyError`` off it."""

    TABLE: typing.ClassVar[dict[str, int]] = {"one": 1}

    def __init__(self, value: str) -> None:
        self.code: int = self.TABLE[value]


class _PercentShare:
    """A consumer ``coerce`` class dividing 100 by its key: ``ZeroDivisionError`` for ``"0"``."""

    def __init__(self, value: str) -> None:
        self.share: float = 100 / int(value)


class _Growth:
    """A consumer ``coerce`` class raising ``e`` to its key: ``OverflowError`` past a float's range."""

    def __init__(self, value: str) -> None:
        self.size: float = math.exp(float(value))


@pytest.mark.parametrize(
    ("coerce", "key", "error"),
    [
        pytest.param(_TableCode, "all", KeyError, id="key-error"),
        pytest.param(_PercentShare, "0", ZeroDivisionError, id="zero-division"),
        pytest.param(_Growth, "1000", OverflowError, id="overflow"),
    ],
)
def test_a_coerce_class_raising_its_own_error_at_schema_build_propagates(
    coerce: type[object],
    key: str,
    error: type[Exception],
) -> None:
    """Only the refusals a form raises answer no: a consumer ``coerce`` class's own error propagates.

    Django's ``TypedChoiceField._coerce`` leaves a ``KeyError``, a ``ZeroDivisionError`` or an
    ``OverflowError`` uncaught at every request, and the ask reads only ``ValidationError``, the temporal
    ``AttributeError``, the JSON ``TypeError`` and ``coerce=Decimal``'s
    ``decimal.InvalidOperation`` as no answer, never another ``ArithmeticError``, so the
    consumer's error reaches the schema build as it would each request.
    """
    payload_set = _payload_set(
        _TypedChoicesInFilter(
            field_name="price",
            lookup_expr="in",
            choices=[(key, key)],
            coerce=coerce,
        ),
    )
    with pytest.raises(error):
        _ = _build_input_fields(payload_set)


@pytest.mark.parametrize(
    "column",
    ["signed_big", "occurred_on"],
)
@pytest.mark.django_db
def test_a_model_choice_form_is_not_asked_at_schema_build(
    column: str,
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """A ``ModelChoiceField`` form cleans by reading its queryset, so the ask runs no query.

    Asked, it would look each sample up as a row (``queryset.get``) when the schema builds;
    the leaf builds and its queryset answers each request instead.
    """
    payload_set = _payload_set(
        _ModelChoiceFormFilter(
            field_name=column,
            queryset=scalar_models.ScalarSpecimen.objects.all(),
            to_field_name=column,
        ),
    )
    with django_assert_num_queries(0):
        assert _build_input_fields(payload_set)


class _CodedIntegerField(models.IntegerField[int, int]):
    """A consumer column storing known codes only: ``get_prep_value`` raises ``KeyError`` on others."""

    CODES: typing.ClassVar[dict[int, int]] = {5: 5, 7: 7}

    @override
    def get_prep_value(self, value: object) -> object:
        return None if value is None else self.CODES[int(str(value))]


class _CheckedCodeField(models.IntegerField[int, int]):
    """A consumer column refusing an unknown code with ``ValueError`` in ``get_prep_value``."""

    CODES: typing.ClassVar[frozenset[int]] = frozenset({5, 7})

    @override
    def get_prep_value(self, value: object) -> object:
        if value is None:
            return None
        code = int(str(value))
        if code not in self.CODES:
            raise ValueError(f"unknown code {code}")
        return code


@isolate_apps("apps.scalars")
@pytest.mark.parametrize("column", ["coded", "checked"])
@pytest.mark.parametrize(
    "filter_class",
    [NumberFilter, CharFilter],
    ids=["number", "text"],
)
def test_a_column_converting_in_consumer_code_is_not_asked(
    column: str,
    filter_class: type[Filter],
) -> None:
    """A column whose ``get_prep_value`` is the consumer's own bounds which values pass.

    One sample cannot speak for it (``1`` is no known code, ``5`` and ``7`` filter), so the
    leaf builds as any other does and the column answers each request.
    """

    class CodedSpecimen(models.Model):
        coded = _CodedIntegerField()
        checked = _CheckedCodeField()

        class Meta:
            app_label = "scalars"
            managed = False

    assert _build_input_fields(_payload_set(filter_class(field_name=column), model=CodedSpecimen))


@isolate_apps("apps.scalars")
@pytest.mark.parametrize(
    "field_name",
    [
        "coded_id",
        "coded",
        "coded__pk",
        "keyed_id",
        "joined",
        "tagged",
    ],
)
def test_a_relation_to_a_key_converting_in_consumer_code_is_not_asked(
    field_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A relation converts through the key it points at, so that key's conversion is read.

    Django prepares a relation's value through the fields its last path step targets
    (``RelatedLookupMixin.get_prep_lookup``): a key whose ``get_prep_value`` is the
    consumer's own bounds which values of the relation pass (``1`` is no known code), so a
    leaf on a foreign key, its attname, the target's ``pk``, a one-to-one, a plain
    ``ForeignObject`` and a many-to-many builds under a consumer ``SCALAR_MAP`` entry for
    the relation.
    """
    for relation in (
        models.ForeignKey,
        models.OneToOneField,
        models.ForeignObject,
        models.ManyToManyField,
    ):
        monkeypatch.setitem(converters_mod.SCALAR_MAP, relation, int)

    class CodedTarget(models.Model):
        code = _CodedIntegerField(primary_key=True)

        class Meta:
            app_label = "scalars"
            managed = False

    class CodedHolder(models.Model):
        coded: _FK[CodedTarget] = models.ForeignKey(CodedTarget, on_delete=models.CASCADE)
        keyed: _O2O[CodedTarget] = models.OneToOneField(
            CodedTarget,
            on_delete=models.CASCADE,
            related_name="+",
        )
        joined_code: _Int = models.IntegerField()
        joined: _FObj[CodedTarget] = models.ForeignObject(
            CodedTarget,
            from_fields=["joined_code"],
            to_fields=["code"],
            on_delete=models.CASCADE,
            related_name="+",
        )
        tagged: _M2M[CodedTarget] = models.ManyToManyField(CodedTarget, related_name="+")

        class Meta:
            app_label = "scalars"
            managed = False

    assert _build_input_fields(
        _payload_set(NumberFilter(field_name=field_name), model=CodedHolder),
    )


class _EvenExact(Exact):
    """A consumer lookup preparing even integers only: ``get_prep_lookup`` refuses odd ones."""

    lookup_name = "even"

    @override
    def get_prep_lookup(self) -> object:
        rhs = read_attr(self, "rhs")
        if isinstance(rhs, (int, decimal.Decimal)) and rhs % 2:
            raise ValueError("odd")
        return object_result(super().get_prep_lookup)


def test_a_lookup_preparing_in_consumer_code_is_not_asked() -> None:
    """A lookup whose ``get_prep_lookup`` is the consumer's own bounds which values pass."""
    _lookup_operand.cache_clear()
    _model_lookup_operand.cache_clear()
    try:
        with register_lookup(models.IntegerField, _EvenExact):
            assert _build_input_fields(
                _payload_set(
                    NumberFilter(field_name="number", lookup_expr="even"),
                    model=library_models.Issue,
                ),
            )
    finally:
        _lookup_operand.cache_clear()
        _model_lookup_operand.cache_clear()
