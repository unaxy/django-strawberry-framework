"""Filter primitive tests for typed, list, range, global-ID, and related filters.

Covers the five parity-floor primitives (`TypedFilter`, `ArrayFilter`,
`RangeFilter`, `ListFilter`, `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter`),
the lazy-resolution mixin, and `RelatedFilter`.

Own-PK empty / malformed GlobalID filter rejection lives in
``test_library_api.py``. This file keeps primitive ``filter()`` methods,
marked non-pk ``to_field`` decode, lazy ``RelatedFilter`` resolution, and
encode-only strategy fail-closed. No fakeshop filterset exposes the one
non-pk ``to_field`` relation (``PatronProfile.favorite_genre``); GraphQL never
delivers a non-list container to ``GlobalIDMultipleChoiceFilter``.
"""

from __future__ import annotations

import copy
import datetime
import uuid
from collections.abc import Callable, Generator, Iterable, Iterator
from decimal import Decimal
from functools import partial
from types import SimpleNamespace
from typing import TYPE_CHECKING, TypeVar

import django_filters
import pytest
import strawberry
from apps.library import models
from apps.scalars import models as scalar_models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import connection as db_connection
from django.db import models as db_models
from django.db.models import Model, QuerySet
from django.db.models.expressions import Combinable
from django.forms import CharField, DecimalField, Field, Form
from django.http import HttpRequest, QueryDict
from django.test import override_settings
from django_filters import BaseInFilter, CharFilter
from django_filters.rest_framework import DjangoFilterBackend
from graphql import GraphQLError
from rest_framework import generics
from rest_framework.test import APIRequestFactory
from strawberry import relay
from typing_extensions import Self, override

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    ArrayFilter,
    ArrayFilterMethod,
    Filter,
    FilterSet,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    LazyRelatedClassMixin,
    ListFilter,
    ListFilterMethod,
    RangeField,
    RangeFilter,
    RelatedFilter,
    TypedFilter,
    validate_range,
)
from django_strawberry_framework.filters.base import (
    _GLOBALID_RELATION_PK_ATTR,
    IntegerInFilter,
    IntegerRangeFilter,
    MembershipInFilter,
    RelationPkFilter,
    RelationPkMultipleFilter,
    _accepted_globalid_type_names,
    _bound_field_name,
    _coerce_int_in_members,
    _column_form_field,
    _decode_and_validate_global_id,
    _ElementField,
    _filter_schema,
    _filterset_model_field,
    _globalid_target,
    _marked_pk_field_name,
    _relation_uses_non_pk_to_field,
    membership_in_filter_class,
    relation_identity_column,
    resolve_globalid_target_definition,
)
from django_strawberry_framework.filters.factories import FilterArgumentsFactory
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types import converters
from django_strawberry_framework.types.definition import DjangoTypeDefinition
from django_strawberry_framework.utils._narrowing import (
    call_method,
    list_of,
    read_attr,
    require_instance,
)
from django_strawberry_framework.utils.typing import object_result
from tests._idioms import ModelSerializerBase, saved_pk
from tests._postgres_fields import FakeArrayField
from tests.filters.fixtures.filtersets import (
    BranchFilter,
    BranchFilterByPath,
    BranchFilterByString,
    ShelfFilter,
)

if TYPE_CHECKING:
    from django_strawberry_framework.utils.typing import ModelField

_FilterT = TypeVar("_FilterT", bound=Filter)


def _widget_value_from_datadict(field: object, *args: object) -> object:
    """``field.widget.value_from_datadict(*args)``, read as ``object`` (the stubs type it ``Any``)."""
    return call_method(read_attr(field, "widget"), "value_from_datadict", *args)


def _widget_decompress(field: object, value: object) -> object:
    """``field.widget.decompress(value)``, read as ``object`` (the stubs type it ``Any``)."""
    return call_method(read_attr(field, "widget"), "decompress", value)


class _RecordingQs(QuerySet[Model]):
    """A real ``QuerySet`` whose query methods record the call instead of building SQL.

    ``filter`` / ``exclude`` keep the keywords they were called with, ``exclude`` and ``distinct``
    count their calls, and ``none`` answers ``nothing``, a second real queryset the test can
    recognise by identity.
    """

    def __init__(self) -> None:
        super().__init__(model=models.Shelf)
        self.captured: dict[str, object] = {}
        self.distinct_calls = 0
        self.exclude_calls = 0
        self.nothing: _RecordingQs | None = None

    @override
    def filter(self, *args: object, **kwargs: object) -> Self:
        self.captured.update(kwargs)
        return self

    @override
    def exclude(self, *args: object, **kwargs: object) -> Self:
        self.exclude_calls += 1
        self.captured.update(kwargs)
        return self

    @override
    def distinct(self, *field_names: str) -> Self:
        self.distinct_calls += 1
        return self

    @override
    def none(self) -> Self:
        self.nothing = type(self)()
        return self.nothing


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# TypedFilter
# ---------------------------------------------------------------------------


def test_typed_filter_drops_input_type_property() -> None:
    """The Graphene-port `input_type` property is intentionally dropped.

    The Strawberry-side annotation derives from the resolved filter
    instance at materialization time via `convert_filter_to_input_annotation`,
    so the Graphene-only property has no role here.
    """
    f = TypedFilter()
    assert not hasattr(f, "input_type")


def test_typed_filter_does_not_carry_graphene_input_type_attribute() -> None:
    """The Graphene-port `_input_type` private slot is also gone."""
    f = TypedFilter()
    assert not hasattr(f, "_input_type")


def test_typed_filter_is_a_django_filter_filter() -> None:
    assert issubclass(TypedFilter, Filter)


# ---------------------------------------------------------------------------
# ArrayFilter
# ---------------------------------------------------------------------------


def test_array_filter_treats_empty_list_as_value() -> None:
    """`[]` is a real value for `ArrayField`; default filter must run."""
    qs = _RecordingQs()

    f = ArrayFilter(field_name="tags", lookup_expr="exact")
    result = f.filter(qs, [])
    assert result is qs
    assert qs.captured == {"tags__exact": []}


def test_array_filter_passes_through_none() -> None:
    """`None` is `EMPTY_VALUES`-ish and short-circuits."""
    sentinel = _RecordingQs()
    f = ArrayFilter(field_name="tags")
    # The cookbook returns the original queryset untouched for `None`.
    assert f.filter(sentinel, None) is sentinel


def test_array_filter_method_setter_swaps_in_array_filter_method() -> None:
    """A consumer-supplied `method=` callable plugs in `ArrayFilterMethod`."""

    def custom(_qs: object, name: str, value: object) -> tuple[str, str, object]:
        return ("custom", name, value)

    f = ArrayFilter(field_name="tags", method=custom)
    assert isinstance(f.filter, ArrayFilterMethod)


# ---------------------------------------------------------------------------
# RangeField / RangeFilter
# ---------------------------------------------------------------------------


def test_validate_range_accepts_two_values() -> None:
    assert validate_range([1, 2]) is None


def test_validate_range_rejects_single_value() -> None:
    with pytest.raises(ValidationError) as excinfo:
        validate_range([1])
    assert excinfo.value.code == "invalid"


def test_validate_range_rejects_three_values() -> None:
    with pytest.raises(ValidationError):
        validate_range(
            [1, 2, 3],
        )


def test_range_filter_uses_range_field_class() -> None:
    assert RangeFilter.field_class is RangeField


def test_range_field_missing_pair_cleans_to_none() -> None:
    """An omitted ``_0``/``_1`` pair is empty, not a range of nulls.

    Live apply of a supplied pair:
    ``test_scalars_filter_api.py::test_scalars_filter_by_price_span_range``.
    """
    field = RangeField(required=False)
    assert _widget_value_from_datadict(field, {}, {}, "price_span") == [None, None]
    assert field.clean([None, None]) is None
    assert _widget_value_from_datadict(
        field,
        {"price_span_0": "10", "price_span_1": "100"},
        {},
        "price_span",
    ) == ["10", "100"]
    assert _widget_decompress(field, ("10", "100")) == ["10", "100"]
    assert _widget_decompress(field, None) == [None, None]


@pytest.mark.parametrize(
    ("bound_field", "value", "cleaned"),
    [
        pytest.param(DecimalField(), ["1.5", None], [Decimal("1.5"), None], id="end-left-open"),
        pytest.param(None, ["NaN", "1.5"], ["NaN", "1.5"], id="no-bound-field-passes-through"),
    ],
)
def test_range_field_cleans_each_bound_with_its_bound_field(
    bound_field: DecimalField | None,
    value: list[str | None],
    cleaned: list[object],
) -> None:
    """A ``None`` bound stays open; without a ``bound_field`` the bounds pass through.

    Live refusal of a bound the column cannot hold:
    ``test_scalars_filter_api.py::test_scalars_filter_price_span_bound_the_column_cannot_hold_is_filter_invalid``.
    """
    assert RangeField(required=False, bound_field=bound_field).clean(value) == cleaned


def test_range_field_leaves_a_pair_of_the_wrong_length_to_validate_range() -> None:
    """A value that is not a pair is never cleaned bound by bound; ``validate_range`` refuses it."""
    with pytest.raises(ValidationError) as excinfo:
        RangeField(bound_field=DecimalField()).clean(["NaN"])
    assert excinfo.value.messages == ["Invalid range specified: it needs to contain 2 values."]


class _ScalarRangeSet(FilterSet):
    price_span = RangeFilter(field_name="price", lookup_expr="range")
    payload_span = RangeFilter(field_name="payload", lookup_expr="range")
    nowhere_span = RangeFilter(field_name="nowhere", lookup_expr="range")
    parent_span = RangeFilter(field_name="parent", lookup_expr="range")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)


class _PlainScalarRangeSet(django_filters.FilterSet):
    price_span = RangeFilter(field_name="price", lookup_expr="range")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)


def _range_field(filter_instance: Filter) -> RangeField:
    return require_instance(filter_instance.field, RangeField)


def test_range_filter_field_cleans_bounds_once_bound_to_a_filterset() -> None:
    """A per-request copy keeps one field whose ``bound_field`` is the column's comparison field.

    A deep copy of the bound filter keeps it. Reading the class-level declaration's field
    builds a fresh one each time and writes nothing to the declaration, which every request
    shares and deep-copies: its ``__dict__`` never gains a ``_field``, so a per-request copy
    made after such reads carries no field and builds its own, cleaning bounds.
    """
    declared = _ScalarRangeSet.base_filters["price_span"]
    before = dict(vars(declared))
    assert _range_field(declared) is not _range_field(declared)
    assert _range_field(declared).bound_field is None
    assert vars(declared) == before
    assert "_field" not in vars(copy.deepcopy(declared))

    filterset = _ScalarRangeSet(data={}, queryset=scalar_models.ScalarSpecimen.objects.none())
    bound = filterset.filters["price_span"]

    assert _range_field(bound) is _range_field(bound)
    assert isinstance(_range_field(bound).bound_field, DecimalField)
    assert isinstance(_range_field(copy.deepcopy(bound)).bound_field, DecimalField)


@pytest.mark.parametrize(("disabled", "help_text"), [(True, ""), (False, "Price span")])
def test_range_filter_class_level_field_is_built_as_django_filter_builds_it(
    disabled: bool,  # noqa: FBT001
    help_text: str,
) -> None:
    """The class-level field is ``Filter.field``'s: label and ``extra``, ``help_text`` per setting."""
    declared = RangeFilter(field_name="price", label="Price", help_text="Price span")

    with override_settings(FILTERS_DISABLE_HELP_TEXT=disabled):
        field = _range_field(declared)

    assert (field.label, field.help_text, field.required) == ("Price", help_text, False)


@pytest.mark.parametrize(
    ("filterset_class", "name"),
    [
        pytest.param(_ScalarRangeSet, "payload_span", id="column-without-a-default-filter"),
        pytest.param(_ScalarRangeSet, "nowhere_span", id="path-naming-no-field"),
        pytest.param(_ScalarRangeSet, "parent_span", id="relation"),
    ],
)
def test_range_filter_without_a_column_form_field_passes_bounds_through(
    filterset_class: type[FilterSet],
    name: str,
) -> None:
    """No column comparison field to read leaves the range field cleaning no bound.

    A relation's would be django-filter's ``ModelChoiceField``, whose lookup of every key
    would tell a key no row holds from one the target's ``get_queryset`` hides.
    """
    filterset = filterset_class(data={}, queryset=scalar_models.ScalarSpecimen.objects.none())

    assert _range_field(filterset.filters[name]).bound_field is None


def test_filter_bound_to_no_filterset_has_no_column_form_field() -> None:
    """A standalone filter, which no ``FilterSet`` stamped as its parent, names no column."""
    assert _column_form_field(RangeFilter(field_name="price", lookup_expr="range")) is None
    assert (
        _column_form_field(ListFilter(field_name="price", lookup_expr="in"), element=True) is None
    )


def test_range_filter_under_a_django_filter_set_gets_the_package_sets_bound_field() -> None:
    """A django-filter ``FilterSet`` parent hands the range field its column's comparison field.

    It is the field class the package ``FilterSet`` hands the same declaration, so a
    ``DjangoFilterBackend`` view cleans each bound as the GraphQL input does.
    """
    queryset = scalar_models.ScalarSpecimen.objects.none()
    plain = _range_field(_PlainScalarRangeSet(data={}, queryset=queryset).filters["price_span"])
    package = _range_field(_ScalarRangeSet(data={}, queryset=queryset).filters["price_span"])

    assert type(plain.bound_field) is type(package.bound_field) is DecimalField


def _decimal_as_text_lookup(
    field: object,
    upstream: tuple[type[Filter] | None, dict[str, object]],
) -> tuple[type[Filter] | None, dict[str, object]]:
    """A project's ``filter_for_lookup`` policy: a decimal column filters as text."""
    if isinstance(field, db_models.DecimalField):
        return CharFilter, {}
    return upstream


class _DecimalAsTextFilterSet(django_filters.FilterSet):
    """A project base whose ``filter_for_lookup`` override filters a decimal column as text."""

    @classmethod
    @override
    def filter_for_lookup(
        cls,
        field: db_models.Field[object, object],
        lookup_type: str,
    ) -> tuple[type[Filter], dict[str, object]]:
        """Answer ``CharFilter`` for a decimal column, django-filter's pair otherwise."""
        if isinstance(field, db_models.DecimalField):
            return CharFilter, {}
        return super().filter_for_lookup(field, lookup_type)


def _package_over_decimal_as_text_set() -> type[FilterSet]:
    """``class _PackageOverDecimalAsTextSet(FilterSet, _DecimalAsTextFilterSet)``.

    A package set with the project base's override behind the package class, declared
    through ``type`` because the stubs type the two bases' classmethods apart.
    """
    meta = type("Meta", (), {"model": scalar_models.ScalarSpecimen, "fields": {"price": ["gte"]}})
    declared = type(
        "_PackageOverDecimalAsTextSet",
        (FilterSet, _DecimalAsTextFilterSet),
        {
            "__module__": __name__,
            "price_span": RangeFilter(field_name="price", lookup_expr="range"),
            "price_in": ListFilter(field_name="price", lookup_expr="in"),
            "Meta": meta,
        },
    )
    assert issubclass(declared, FilterSet)
    return declared


_PackageOverDecimalAsTextSet = _package_over_decimal_as_text_set()


class _PlainDecimalAsTextSet(_DecimalAsTextFilterSet):
    price_span = RangeFilter(field_name="price", lookup_expr="range")
    price_in = ListFilter(field_name="price", lookup_expr="in")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)


class _PackageOwnDecimalAsTextSet(FilterSet):
    """A package set whose own ``filter_for_lookup`` override sits above the package class."""

    price_span = RangeFilter(field_name="price", lookup_expr="range")
    price_in = ListFilter(field_name="price", lookup_expr="in")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)

    @classmethod
    @override
    def filter_for_lookup(
        cls,
        field: ModelField,
        lookup_type: str,
    ) -> tuple[type[Filter] | None, dict[str, object]]:
        """Answer ``CharFilter`` for a decimal column, the package's pair otherwise."""
        return _decimal_as_text_lookup(field, super().filter_for_lookup(field, lookup_type))


@pytest.mark.parametrize(
    ("filterset_class", "form_field_class"),
    [
        pytest.param(
            _PackageOverDecimalAsTextSet,
            CharField,
            id="django-filter-base-behind-package",
        ),
        pytest.param(_PlainDecimalAsTextSet, CharField, id="django-filter-sets-own-override"),
        pytest.param(_PackageOwnDecimalAsTextSet, DecimalField, id="package-subclass-override"),
    ],
)
def test_column_form_field_follows_the_parents_filter_for_lookup_bar_the_package_override(
    filterset_class: type[django_filters.FilterSet | FilterSet],
    form_field_class: type[Field],
) -> None:
    """The comparison field is the parent's ``filter_for_lookup`` without the package override.

    A django-filter base behind the package class, and a django-filter set's own override,
    are configuration and choose the bound and element field; a package subclass's own
    override sits above the package's and is not read, the cleaner reading the class the
    package override replaces.
    """
    filterset = filterset_class(data={}, queryset=scalar_models.ScalarSpecimen.objects.none())
    element = require_instance(filterset.filters["price_in"].field, _ElementField).element_field

    assert type(_range_field(filterset.filters["price_span"]).bound_field) is form_field_class
    assert type(element) is form_field_class


def test_package_set_over_a_django_filter_base_generates_the_bases_filter() -> None:
    """A generated leaf follows a django-filter base's override behind the package class."""
    assert type(_PackageOverDecimalAsTextSet.base_filters["price__gte"]) is CharFilter


class _PackageCleanedScalarSet(FilterSet):
    price_span = RangeFilter(field_name="price", lookup_expr="range")
    occurred_at_span = RangeFilter(field_name="occurred_at", lookup_expr="range")
    external_id_span = RangeFilter(field_name="external_id", lookup_expr="range")
    signed_big_span = RangeFilter(field_name="signed_big", lookup_expr="range")
    price_in = ListFilter(field_name="price", lookup_expr="in")
    occurred_at_in = ListFilter(field_name="occurred_at", lookup_expr="in")
    external_id_in = ListFilter(field_name="external_id", lookup_expr="in")
    signed_big_in = ListFilter(field_name="signed_big", lookup_expr="in")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)


class _PlainCleanedScalarSet(django_filters.FilterSet):
    price_span = RangeFilter(field_name="price", lookup_expr="range")
    occurred_at_span = RangeFilter(field_name="occurred_at", lookup_expr="range")
    external_id_span = RangeFilter(field_name="external_id", lookup_expr="range")
    signed_big_span = RangeFilter(field_name="signed_big", lookup_expr="range")
    price_in = ListFilter(field_name="price", lookup_expr="in")
    occurred_at_in = ListFilter(field_name="occurred_at", lookup_expr="in")
    external_id_in = ListFilter(field_name="external_id", lookup_expr="in")
    signed_big_in = ListFilter(field_name="signed_big", lookup_expr="in")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)


_CLEANED_SCALAR_SETS = [
    pytest.param(_PackageCleanedScalarSet, id="package-filterset"),
    pytest.param(_PlainCleanedScalarSet, id="django-filter-filterset"),
]

_KEPT_EXTERNAL_ID = uuid.UUID("6f1c2a3e-0b4d-4e5f-8a9b-1c2d3e4f5a6b")


def _cleaned_specimen(label: str, *, kept: bool) -> scalar_models.ScalarSpecimen:
    """Create a specimen whose price, timestamp, id and integer each match only when ``kept``."""
    return scalar_models.ScalarSpecimen.objects.create(
        label=label,
        price=Decimal("10.5") if kept else Decimal(99),
        occurred_on=datetime.date(2026, 1, 2),
        occurred_at=datetime.datetime(
            2026 if kept else 2020,
            1,
            2,
            3,
            4,
            5,
            tzinfo=datetime.timezone.utc,
        ),
        occurred_time=datetime.time(3, 4, 5),
        external_id=_KEPT_EXTERNAL_ID if kept else uuid.uuid4(),
        signed_big=7 if kept else 900,
    )


@pytest.mark.parametrize("filterset_class", _CLEANED_SCALAR_SETS)
@pytest.mark.parametrize(
    ("name", "data", "message"),
    [
        pytest.param(
            "price_span",
            {"price_span_0": "NaN", "price_span_1": "1"},
            "Enter a number.",
            id="decimal-range",
        ),
        pytest.param(
            "occurred_at_span",
            {"occurred_at_span_0": "2026-01-01 00:00:00", "occurred_at_span_1": "not-a-date"},
            "Enter a valid date/time.",
            id="datetime-range",
        ),
        pytest.param(
            "external_id_span",
            {"external_id_span_0": "not-a-uuid", "external_id_span_1": str(_KEPT_EXTERNAL_ID)},
            "Enter a valid UUID.",
            id="uuid-range",
        ),
        pytest.param(
            "signed_big_span",
            {"signed_big_span_0": "NaN", "signed_big_span_1": "NaN"},
            "Enter a number.",
            id="integer-range",
        ),
        pytest.param("price_in", {"price_in": ["1", "NaN"]}, "Enter a number.", id="decimal-list"),
        pytest.param(
            "occurred_at_in",
            {"occurred_at_in": ["not-a-date"]},
            "Enter a valid date/time.",
            id="datetime-list",
        ),
        pytest.param(
            "external_id_in",
            {"external_id_in": [str(_KEPT_EXTERNAL_ID), "not-a-uuid"]},
            "Enter a valid UUID.",
            id="uuid-list",
        ),
        pytest.param(
            "signed_big_in",
            {"signed_big_in": ["NaN"]},
            "Enter a number.",
            id="integer-list",
        ),
    ],
)
def test_declared_range_or_list_value_the_column_cannot_hold_is_a_form_error_under_any_filterset(
    filterset_class: type[django_filters.FilterSet | FilterSet],
    name: str,
    data: dict[str, object],
    message: str,
) -> None:
    """A bound or element the column cannot hold is the form's error under either parent.

    A django-filter ``FilterSet`` cleans it as the package ``FilterSet`` does, with the
    column's ``gte`` form field, so it never reaches the ORM (where a ``NaN`` integer bound
    raises ``ValueError`` and a bad UUID or datetime ``ValidationError``). Live refusal under
    the package parent:
    ``test_scalars_filter_api.py::test_scalars_filter_price_span_bound_the_column_cannot_hold_is_filter_invalid``.
    """
    filterset = filterset_class(data=data, queryset=scalar_models.ScalarSpecimen.objects.none())

    assert not filterset.is_valid()
    assert filterset.errors == {name: [message]}


@pytest.mark.django_db
@pytest.mark.parametrize("filterset_class", _CLEANED_SCALAR_SETS)
@pytest.mark.parametrize(
    "data",
    [
        pytest.param({"price_span_0": "10", "price_span_1": "11"}, id="decimal-range"),
        pytest.param(
            {
                "occurred_at_span_0": "2026-01-01 00:00:00",
                "occurred_at_span_1": "2026-12-31 00:00:00",
            },
            id="datetime-range",
        ),
        pytest.param(
            {
                "external_id_span_0": str(_KEPT_EXTERNAL_ID),
                "external_id_span_1": str(_KEPT_EXTERNAL_ID),
            },
            id="uuid-range",
        ),
        pytest.param({"signed_big_span_0": "5", "signed_big_span_1": "8"}, id="integer-range"),
        pytest.param({"price_in": ["10.5"]}, id="decimal-list"),
        pytest.param({"occurred_at_in": ["2026-01-02 03:04:05"]}, id="datetime-list"),
        pytest.param({"external_id_in": [str(_KEPT_EXTERNAL_ID)]}, id="uuid-list"),
        pytest.param({"signed_big_in": ["7"]}, id="integer-list"),
    ],
)
def test_declared_range_or_list_value_the_column_holds_filters_under_any_filterset(
    filterset_class: type[django_filters.FilterSet | FilterSet],
    data: dict[str, object],
) -> None:
    """A well-formed bound or element filters the rows the same under either parent."""
    _ = _cleaned_specimen("kept", kept=True)
    _ = _cleaned_specimen("other", kept=False)
    queryset = scalar_models.ScalarSpecimen.objects.order_by("label")

    filterset = filterset_class(data=data, queryset=queryset)

    assert filterset.is_valid()
    assert list(filterset.qs.values_list("label", flat=True)) == ["kept"]


class _SpecimenLabelSerializer(ModelSerializerBase[scalar_models.ScalarSpecimen]):
    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)


class _CleanedSpecimenListView(generics.ListAPIView[scalar_models.ScalarSpecimen]):
    """A DRF list view filtering through ``DjangoFilterBackend`` with a django-filter set."""

    queryset = scalar_models.ScalarSpecimen.objects.order_by("label")
    serializer_class = _SpecimenLabelSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = _PlainCleanedScalarSet
    authentication_classes = ()
    permission_classes = ()
    pagination_class = None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "status", "body"),
    [
        pytest.param(
            "price_span_0=NaN&price_span_1=NaN",
            400,
            {"price_span": ["Enter a number."]},
            id="decimal-bound-the-column-cannot-hold",
        ),
        pytest.param(
            "signed_big_span_0=NaN&signed_big_span_1=8",
            400,
            {"signed_big_span": ["Enter a number."]},
            id="integer-bound-the-column-cannot-hold",
        ),
        pytest.param(
            "price_span_0=10&price_span_1=11",
            200,
            [{"label": "kept"}],
            id="decimal-span",
        ),
        pytest.param(
            "signed_big_span_0=5&signed_big_span_1=8",
            200,
            [{"label": "kept"}],
            id="integer-span",
        ),
    ],
)
def test_declared_range_filter_under_django_filter_backend_answers_a_bad_bound_with_400(
    query: str,
    status: int,
    body: object,
) -> None:
    """A range bound the column cannot hold is the backend's 400, a valid span its rows.

    ``DjangoFilterBackend`` turns the invalid form into DRF's ``ValidationError``; the bound
    never reaches the ORM, where it would raise and answer 500.
    """
    _ = _cleaned_specimen("kept", kept=True)
    _ = _cleaned_specimen("other", kept=False)
    request = APIRequestFactory().get(f"/specimens/?{query}")

    response = _CleanedSpecimenListView.as_view()(request)

    assert (response.status_code, read_attr(response, "data")) == (status, body)


_ONE_SIDED_RANGES = [
    pytest.param([5, None], {"price_span__gte": 5}, id="start-only"),
    pytest.param([None, 9], {"price_span__lte": 9}, id="end-only"),
]


@pytest.mark.parametrize(("value", "expected"), _ONE_SIDED_RANGES)
def test_range_filter_one_sided_applies_lone_bound(
    value: list[int | None],
    expected: dict[str, object],
) -> None:
    """A range with one bound applies that bound alone, never ``BETWEEN x AND NULL``.

    Live: ``test_scalars_filter_api.py::test_scalars_filter_price_span_one_sided_bounds``.
    """
    qs = _RecordingQs()

    f = RangeFilter(field_name="price_span", lookup_expr="range")
    result = f.filter(qs, value)
    assert result is qs
    assert qs.captured == expected


@pytest.mark.parametrize(
    "value",
    [[5, 9], [0, 9], [5, 0]],
    ids=["both-bounds", "zero-start", "zero-end"],
)
def test_range_filter_two_bounds_keep_declared_lookup(value: list[int]) -> None:
    """Both bounds bind the declared ``range`` lookup unchanged; a ``0`` bound is a bound."""
    qs = _RecordingQs()

    f = RangeFilter(field_name="price_span", lookup_expr="range")
    f.filter(qs, value)
    assert qs.captured == {"price_span__range": value}


@pytest.mark.parametrize(
    "value",
    [[None, None], (None, None), None],
    ids=["both-null-list", "both-null-tuple", "none"],
)
def test_range_filter_without_bounds_is_skipped(
    value: list[None] | tuple[None, None] | None,
) -> None:
    """A range with neither bound constrains nothing: the queryset comes back untouched."""
    qs = _RecordingQs()

    f = RangeFilter(field_name="price_span", lookup_expr="range")
    assert f.filter(qs, value) is qs
    assert qs.captured == {}


@pytest.mark.parametrize(("value", "expected"), _ONE_SIDED_RANGES)
def test_range_filter_one_sided_honours_exclude(
    value: list[int | None],
    expected: dict[str, object],
) -> None:
    """Under ``exclude=True`` the lone bound goes through ``qs.exclude``."""
    qs = _RecordingQs()

    f = RangeFilter(field_name="price_span", lookup_expr="range", exclude=True)
    f.filter(qs, value)
    assert qs.exclude_calls == 1
    assert qs.captured == expected


@pytest.mark.parametrize(("value", "expected"), _ONE_SIDED_RANGES)
def test_range_filter_one_sided_applies_distinct_when_flagged(
    value: list[int | None],
    expected: dict[str, object],
) -> None:
    """``distinct=True`` calls ``.distinct()`` before the lone bound applies."""
    qs = _RecordingQs()

    f = RangeFilter(field_name="price_span", lookup_expr="range", distinct=True)
    f.filter(qs, value)
    assert qs.distinct_calls == 1
    assert qs.captured == expected


# ---------------------------------------------------------------------------
# IntegerRangeFilter
# ---------------------------------------------------------------------------


def test_integer_range_filter_decomposes_range_into_gte_lte() -> None:
    """A two-bound range applies one ``gte`` + ``lte`` predicate, never a raw ``__range`` bind.

    Each bound flows through Django's range-aware integer lookup, so an out-of-range value never
    overflows the backend (a ``BETWEEN`` bind would).
    """
    qs = _RecordingQs()

    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range")
    result = f.filter(qs, [1, 100])
    assert result is qs
    assert qs.captured == {"signed_big__gte": 1, "signed_big__lte": 100}


def test_integer_range_filter_excludes_via_negated_conjunction() -> None:
    """Under ``exclude=True`` the decomposed pair is applied through ``qs.exclude``.

    That is the exact complement of ``NOT (col BETWEEN a AND b)``.
    """
    qs = _RecordingQs()

    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range", exclude=True)
    f.filter(qs, [1, 100])
    assert qs.captured == {"signed_big__gte": 1, "signed_big__lte": 100}


def test_integer_range_filter_passes_through_empty_value() -> None:
    """An empty / ``None`` range keeps django-filter's skip (no bounds supplied)."""
    sentinel = _RecordingQs()
    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range")
    assert f.filter(sentinel, None) is sentinel


def test_integer_range_filter_list_subclass_iteration_error_propagates() -> None:
    """A ``list`` subclass's own ``__iter__`` exception propagates, never an unfiltered skip."""

    class RaisingIter(list[object]):
        @override
        def __iter__(self) -> Iterator[object]:
            raise RuntimeError("list subclass __iter__ raised")

    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range")
    with pytest.raises(RuntimeError, match="list subclass __iter__ raised"):
        f.filter(_RecordingQs(), RaisingIter([1, 2]))


def test_integer_range_filter_applies_distinct_when_flagged() -> None:
    """``IntegerRangeFilter.filter`` calls ``.distinct()`` when ``distinct=True``."""
    qs = _RecordingQs()

    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range", distinct=True)
    result = f.filter(qs, [1, 100])
    assert result is qs
    assert qs.distinct_calls == 1
    assert qs.captured == {"signed_big__gte": 1, "signed_big__lte": 100}


# ---------------------------------------------------------------------------
# ListFilter
# ---------------------------------------------------------------------------


def test_list_filter_returns_qs_none_on_empty_list() -> None:
    qs = _RecordingQs()

    f = ListFilter(field_name="ids")
    assert f.filter(qs, []) is qs.nothing


def test_list_filter_defers_to_super_for_nonempty_lists() -> None:
    qs = _RecordingQs()

    f = ListFilter(field_name="ids", lookup_expr="in")
    f.filter(qs, [1, 2])
    assert qs.captured == {"ids__in": [1, 2]}


def test_list_filter_passes_through_none() -> None:
    """``None`` skips the list-shape gate and falls through to ``Filter.filter``.

    ``Filter.filter`` short-circuits on ``EMPTY_VALUES``, the same omission pass-through the sibling
    ``MembershipInFilter`` documents.
    """
    sentinel = _RecordingQs()
    f = ListFilter(field_name="ids")
    assert f.filter(sentinel, None) is sentinel


class _ValidatedCount(db_models.Model):
    """An integer column whose own validator refuses values below 10."""

    count: db_models.IntegerField[int | Combinable, int] = db_models.IntegerField(
        validators=[MinValueValidator(10)],
    )

    class Meta:
        managed = False
        app_label = "test_list_filter_validators"


class _ValidatedCountSet(FilterSet):
    count_among = ListFilter(field_name="count", lookup_expr="in")
    count_outside = ListFilter(field_name="count", lookup_expr="in", exclude=True)

    class Meta:
        model = _ValidatedCount
        fields = ("count",)


@pytest.fixture
def validated_counts() -> Generator[QuerySet[_ValidatedCount], None, None]:
    """A real ``_ValidatedCount`` table holding 5 (below the validator) and 12."""
    with db_connection.schema_editor() as editor:
        editor.create_model(_ValidatedCount)
    try:
        _ValidatedCount.objects.create(count=5)
        _ValidatedCount.objects.create(count=12)
        yield _ValidatedCount.objects.all()
    finally:
        with db_connection.schema_editor() as editor:
            editor.delete_model(_ValidatedCount)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("name", "members", "counts"),
    [
        pytest.param("count_among", [5], [5], id="validator-refused-member-matches"),
        pytest.param("count_outside", [5], [12], id="validator-refused-member-excluded"),
        pytest.param("count_among", ["abc", 12], [12], id="unconvertible-member-dropped"),
        pytest.param("count_among", ["abc"], [], id="every-member-dropped"),
        pytest.param("count_outside", ["abc"], [5, 12], id="every-member-dropped-excluded"),
    ],
)
def test_list_filter_integer_in_keeps_members_the_backend_stores(
    validated_counts: QuerySet[_ValidatedCount],
    name: str,
    members: list[object],
    counts: list[int],
) -> None:
    """An integer ``in`` drops only members outside the backend's range, never by validator.

    A row holding a value the column's own validators refuse is stored all the same (Django
    validates on ``full_clean``, never on save), so a member equal to it still matches that
    row, and its ``exclude`` twin leaves that row out. A member the column's ``to_python``
    cannot convert identifies no row and is dropped; a list with none left matches nothing,
    or every row when excluding. Package-only: no fakeshop integer column carries a
    validator of its own, and the GraphQL input delivers only integers. Live rows for a
    member past the backend's range:
    ``test_scalars_api.py::test_filter_specimens_by_declared_bigint_list_drops_out_of_range_members``.
    """
    bound = _ValidatedCountSet(data={}, queryset=validated_counts).filters[name]
    result: QuerySet[_ValidatedCount] = bound.filter(validated_counts, members)
    assert sorted(row.count for row in result) == counts


@pytest.mark.parametrize(
    ("element_field", "value", "cleaned"),
    [
        pytest.param(DecimalField(), ["1.5", None], [Decimal("1.5"), None], id="none-kept"),
        pytest.param(DecimalField(), "1.5", "1.5", id="not-a-list-passes-through"),
        pytest.param(None, ["NaN"], ["NaN"], id="no-element-field-passes-through"),
    ],
)
def test_list_filter_field_cleans_each_element_with_its_element_field(
    element_field: DecimalField | None,
    value: object,
    cleaned: object,
) -> None:
    """A ``None`` element stays ``None``; a non-list, or a field with no column, passes through.

    A non-list reaches ``ListFilter.filter``, whose list-shape gate refuses it. Live refusal
    of an element the column cannot hold:
    ``test_scalars_filter_api.py::test_price_among_element_the_column_cannot_hold_is_filter_invalid``.
    """
    assert ListFilter.field_class is ArrayFilter.field_class is _ElementField
    assert _ElementField(required=False, element_field=element_field).clean(value) == cleaned


@pytest.mark.parametrize(
    ("field_name", "lookup_expr"),
    [
        pytest.param("prices", "contains", id="array-column-element-is-its-base-field"),
        pytest.param("price", "in", id="scalar-column"),
    ],
)
def test_array_filter_element_the_column_cannot_hold_is_filter_invalid(
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    lookup_expr: str,
) -> None:
    """Each ``ArrayFilter`` element is cleaned as one value of its column's elements.

    An ``ArrayField`` column's element is a value of its ``base_field``, so a non-finite
    decimal is ``FILTER_INVALID`` before ``django.contrib.postgres``'s array lookup hands it
    to ``base_field.get_prep_value``; under a django-filter ``FilterSet`` it is that form's
    error. Package-only: fakeshop declares no ``ArrayField``.
    """
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", FakeArrayField)

    class PricedShelf(db_models.Model):
        price: db_models.DecimalField[str | float | Decimal | Combinable, Decimal] = (
            db_models.DecimalField(
                max_digits=8,
                decimal_places=2,
            )
        )
        prices = FakeArrayField(db_models.DecimalField(max_digits=8, decimal_places=2))

        class Meta:
            managed = False
            app_label = "test_array_filter_elements"

    class PricedShelfFilter(FilterSet):
        priced = ArrayFilter(field_name=field_name, lookup_expr=lookup_expr)

        class Meta:
            model = PricedShelf
            fields = ("price",)

    class PlainPricedShelfFilter(django_filters.FilterSet):
        priced = ArrayFilter(field_name=field_name, lookup_expr=lookup_expr)

        class Meta:
            model = PricedShelf
            fields = ("price",)

    data = {"priced": ["1.5", "NaN"]}
    filterset = PricedShelfFilter(data=data, queryset=PricedShelf.objects.none())
    with pytest.raises(GraphQLError) as excinfo:
        PricedShelfFilter._validate_form_or_raise(filterset)
    assert excinfo.value.extensions == {
        "code": "FILTER_INVALID",
        "errors": {"priced": [{"message": "Enter a number.", "code": "invalid"}]},
    }
    plain = PlainPricedShelfFilter(data=data, queryset=PricedShelf.objects.none())
    assert not plain.is_valid()
    assert plain.errors == {"priced": ["Enter a number."]}


# ---------------------------------------------------------------------------
# GlobalIDFilter
# ---------------------------------------------------------------------------


def test_global_id_filter_decodes_via_strawberry_relay() -> None:
    """The decoded `node_id` reaches the underlying `Filter.filter` call."""
    qs = _RecordingQs()

    encoded = relay.to_base64("BookType", "42")
    f = GlobalIDFilter(field_name="id", lookup_expr="exact")
    f.filter(qs, encoded)
    assert qs.captured == {"id__exact": "42"}


def test_global_id_filter_passes_through_none() -> None:
    qs = _RecordingQs()

    f = GlobalIDFilter(field_name="id", lookup_expr="exact")
    # `None` falls through to `Filter.filter`, which short-circuits on EMPTY_VALUES.
    result = f.filter(qs, None)
    assert qs.captured == {}
    assert result is qs


def test_global_id_multiple_choice_filter_decodes_every_element(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Decoded `node_id`s reach the underlying `MultipleChoiceFilter.filter`."""
    captured: list[list[str]] = []

    def spy(_self: object, qs: object, value: Iterable[str]) -> object:
        captured.append(list(value))
        return qs

    encoded_one = relay.to_base64("BookType", "1")
    encoded_two = relay.to_base64("BookType", "2")
    # Spy on the upstream ``MultipleChoiceFilter.filter`` via the bound
    # parent class. ``monkeypatch`` auto-restores on teardown (xdist-safe
    # and exception-safe) instead of the prior manual try/finally that
    # wrote through to the upstream class.
    monkeypatch.setattr(GlobalIDMultipleChoiceFilter.__mro__[1], "filter", spy)
    f = GlobalIDMultipleChoiceFilter(field_name="id")
    f.filter(_RecordingQs(), [encoded_one, encoded_two])
    assert captured == [["1", "2"]]


def test_global_id_multiple_choice_filter_passes_through_none() -> None:
    qs = _RecordingQs()

    f = GlobalIDMultipleChoiceFilter(field_name="id")
    result = f.filter(qs, None)
    assert qs.captured == {}
    assert result is qs


@pytest.mark.parametrize("value", [iter(["not-a-global-id"]), object(), "not-a-list"])
def test_global_id_multiple_choice_filter_rejects_malformed_container(value: object) -> None:
    """Malformed direct inputs fail as coded GraphQL errors, not leaked ``TypeError``."""
    f = GlobalIDMultipleChoiceFilter(field_name="id", lookup_expr="in")

    with pytest.raises(GraphQLError, match="expected a list of GlobalIDs") as exc_info:
        f.filter(_RecordingQs(), value)

    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


def test_global_id_multiple_choice_field_distinguishes_absent_from_explicit_empty() -> None:
    """Form cleaning keeps omission as ``None`` and a supplied empty list as ``[]``."""
    field = GlobalIDMultipleChoiceFilter(field_name="id").field

    absent = _widget_value_from_datadict(field, QueryDict(), {}, "id")
    explicit_empty = _widget_value_from_datadict(field, {"id": []}, {}, "id")

    assert field.clean(absent) is None
    assert field.clean(explicit_empty) == []


class _CharInFilter(BaseInFilter, CharFilter):
    """django-filter's ``in`` shape over ``CharFilter`` (what ``filter_for_lookup`` builds)."""


def test_membership_in_field_reads_a_raw_empty_string_as_omission() -> None:
    """``?field__in=`` (django-filter's CSV ``""``) cleans to ``None``; a list stays a list.

    Raw form data keeps django-filter's empty-value rule (no constraint) while the
    GraphQL layer's explicit ``[]`` reaches ``MembershipInFilter.filter`` as the empty set.
    """
    field = membership_in_filter_class(_CharInFilter)(field_name="code", lookup_expr="in").field

    raw_empty = _widget_value_from_datadict(field, QueryDict("code__in="), {}, "code__in")
    explicit_empty = _widget_value_from_datadict(field, {"code__in": []}, {}, "code__in")
    absent = _widget_value_from_datadict(field, QueryDict(), {}, "code__in")
    csv = _widget_value_from_datadict(field, QueryDict("code__in=a,b"), {}, "code__in")

    assert field.clean(raw_empty) is None
    assert field.clean(absent) is None
    assert field.clean(explicit_empty) == []
    assert field.clean(csv) == ["a", "b"]


def test_membership_in_filter_class_wraps_a_new_class_per_call_and_rejects_a_scalar() -> None:
    """A NEW class per call (django-filter's lifecycle) keeping the inner name; a scalar is coded."""
    wrapped = membership_in_filter_class(_CharInFilter)
    assert wrapped is not membership_in_filter_class(_CharInFilter)
    assert wrapped.__name__ == "_CharInFilter"
    assert wrapped.__mro__[1:3] == (MembershipInFilter, _CharInFilter)
    with pytest.raises(GraphQLError) as exc_info:
        wrapped(field_name="code", lookup_expr="in").filter(models.Shelf.objects.all(), "ab")
    assert exc_info.value.extensions == {"code": "FILTER_INVALID"}


def test_global_id_multiple_choice_field_omission_still_enforces_required() -> None:
    """Preserving ``None`` must not bypass Django's required-field validation."""
    field = GlobalIDMultipleChoiceFilter(field_name="id", required=True).field
    absent = _widget_value_from_datadict(field, QueryDict(), {}, "id")

    with pytest.raises(ValidationError, match="required"):
        field.clean(absent)


def test_global_id_multiple_choice_filter_empty_in_matches_nothing_like_list_filter() -> None:
    qs = _RecordingQs()
    global_ids = GlobalIDMultipleChoiceFilter(field_name="id", lookup_expr="in")
    list_filter = ListFilter(field_name="id", lookup_expr="in")

    assert global_ids.filter(qs, []) is qs.nothing
    assert list_filter.filter(qs, []) is qs.nothing


@pytest.mark.django_db
@pytest.mark.parametrize(
    "excluding",
    [
        lambda: ListFilter(field_name="code", exclude=True),
        lambda: GlobalIDMultipleChoiceFilter(field_name="id", lookup_expr="in", exclude=True),
        lambda: GlobalIDMultipleChoiceFilter(field_name="id", lookup_expr="exact", exclude=True),
    ],
    ids=["list-filter", "global-id-in", "global-id-exact"],
)
def test_excluded_empty_membership_matches_every_row_as_a_constraint(
    excluding: Callable[[], Filter],
) -> None:
    """Exclude + empty membership is the complement of match-nothing: every row.

    The rows come back on a new queryset, never the input by identity, which the
    package reads as "applied no constraint".
    """
    branch = models.Branch.objects.create(name="Home", city="Boston")
    models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    models.Shelf.objects.create(code="A-2", topic="general", branch=branch)
    qs = models.Shelf.objects.order_by("code")

    result = object_result(excluding().filter, qs, [])

    assert result is not qs
    assert [require_instance(shelf, models.Shelf).code for shelf in list_of(result)] == [
        "A-1",
        "A-2",
    ]


# ---------------------------------------------------------------------------
# A crafted empty-id GlobalID (well-typed, empty node part) is a REJECTED input,
# not a silent no-op. ``to_base64(type, "")`` decodes to ``node_id == ""``
# and clears decode + strategy + type-name validation, but an empty identifier is
# not a valid resource id: the shared ``_decode_and_validate_global_id`` boundary
# raises ``GLOBALID_INVALID`` (naming the list index when present) so a client can
# never widen a restrictive membership predicate by supplying ``type:``. An
# explicit ``[]`` (match-none) and a ``None`` value (omission) remain non-error
# paths and are asserted separately.
# ---------------------------------------------------------------------------


def test_global_id_multiple_choice_filter_empty_node_id_exact_path_rejects() -> None:
    """The same reject covers the non-``in`` (per-element) path.

    Live ``in`` twins:
    ``test_library_api.py::test_library_genres_filter_empty_id_in_list_raises_globalid_invalid_at_index_0``
    and
    ``::test_library_genres_filter_mixed_empty_id_in_list_rejects_whole_input_at_index_1``.
    """
    f = GlobalIDMultipleChoiceFilter(field_name="genres", lookup_expr="exact")
    with pytest.raises(GraphQLError, match="empty node id") as exc_info:
        f.filter(_RecordingQs(), [relay.to_base64("GenreType", "")])
    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


def test_global_id_multiple_choice_filter_well_formed_list_still_applies_predicate() -> None:
    """Regression: a well-formed non-empty ``in`` list still yields the whole-list predicate.

    Removing the empty-stripping block must not disturb the normal path -- a list
    of real ids compiles the byte-identical ``{field__in: node_ids}`` predicate.
    """
    qs = _RecordingQs()
    f = GlobalIDMultipleChoiceFilter(field_name="genres", lookup_expr="in")
    encoded = [relay.to_base64("GenreType", "5"), relay.to_base64("GenreType", "9")]
    f.filter(qs, encoded)
    assert qs.captured == {"genres__in": ["5", "9"]}


# ---------------------------------------------------------------------------
# A bound filter's ORM path
# ---------------------------------------------------------------------------


def test_bound_field_name_reads_the_path_the_filterset_binds() -> None:
    """A declared filter with no ``field_name`` is bound to its attribute name."""

    class BookFilterSet(FilterSet):
        title = Filter(lookup_expr="icontains")

        class Meta:
            model = models.Book
            fields = ["id"]

    assert _bound_field_name(BookFilterSet.base_filters["title"]) == "title"


def test_bound_field_name_refuses_a_filter_with_no_path() -> None:
    """A ``None`` path is refused by name, never handed to a model-field walk."""
    with pytest.raises(ConfigurationError, match=r"^Filter has no field_name;"):
        _bound_field_name(Filter())


@pytest.mark.parametrize(
    ("filter_instance", "value"),
    [(IntegerInFilter(), [1]), (RelationPkFilter(), 1)],
    ids=["integer-in", "relation-identity"],
)
def test_bound_filters_with_no_field_name_are_refused(
    filter_instance: Filter,
    value: object,
) -> None:
    """A filter bound to a filterset with a model but no ``field_name`` is refused, not skipped."""
    # django-filter stamps ``parent`` on every per-request filter; the stubs omit it.
    setattr(filter_instance, "parent", ShelfFilter())  # noqa: B010
    with pytest.raises(ConfigurationError, match=r"has no field_name;"):
        filter_instance.filter(models.Shelf.objects.none(), value)


def test_filterset_model_field_returns_none_without_model() -> None:
    """A filterset-shaped object with no ``_meta.model`` yields ``None``."""

    class _NoMeta:
        pass

    # basedpyright: the class without _meta is the hostile input under test;
    # _filterset_model_field types the parameter as a FilterSet class or instance
    assert _filterset_model_field(_NoMeta, GlobalIDFilter(field_name="id")) is None  # pyright: ignore[reportArgumentType]


def test_filterset_model_field_returns_none_without_field_name() -> None:
    """An empty ``field_name`` names no field, so it yields ``None`` even on a real model."""
    f = GlobalIDFilter()
    f.field_name = ""
    assert _filterset_model_field(ShelfFilter, f) is None


def test_filterset_model_field_returns_none_for_unknown_field_name() -> None:
    """A typo in ``Filter(field_name=...)`` surfaces as ``None``, not a crash.

    Path resolution is ``django_filters.utils.get_model_field``; an unknown hop
    returns ``None``.
    """
    f = GlobalIDFilter(field_name="nonexistent_field")
    assert _filterset_model_field(ShelfFilter, f) is None


def test_filterset_model_field_walks_related_path() -> None:
    """A ``__``-separated ``field_name`` resolves to the terminal model field."""
    f = GlobalIDFilter(field_name="branch__name")
    assert _filterset_model_field(ShelfFilter, f) is models.Branch._meta.get_field("name")


# ---------------------------------------------------------------------------
# GlobalID relation filtering against a non-pk ``to_field``
# ---------------------------------------------------------------------------


def test_relation_uses_non_pk_to_field_true_for_to_field_fk() -> None:
    """A forward FK on a non-pk ``to_field`` (``favorite_genre`` -> ``name``) is flagged."""
    field = models.PatronProfile._meta.get_field("favorite_genre")
    assert _relation_uses_non_pk_to_field(field) is True


def test_relation_uses_non_pk_to_field_false_for_ordinary_fk_to_pk() -> None:
    """An ordinary FK whose target field IS the related pk is not flagged."""
    field = models.Book._meta.get_field("shelf")
    assert _relation_uses_non_pk_to_field(field) is False


def test_relation_uses_non_pk_to_field_false_for_m2m() -> None:
    """A ``ManyToManyField`` (non-concrete) is not flagged."""
    field = models.Book._meta.get_field("genres")
    assert _relation_uses_non_pk_to_field(field) is False


def test_relation_uses_non_pk_to_field_false_for_reverse_relation() -> None:
    """A reverse relation object (non-concrete) is not flagged."""
    field = models.Book._meta.get_field("loans")
    assert _relation_uses_non_pk_to_field(field) is False


def test_relation_uses_non_pk_to_field_false_for_generic_foreign_key() -> None:
    """A ``GenericForeignKey`` is forward-single but carries no link pairs, so it is not flagged."""
    field = models.TaggedItem._meta.get_field("content_object")
    assert _relation_uses_non_pk_to_field(field) is False


def test_relation_uses_non_pk_to_field_false_for_unreadable_relation_flags() -> None:
    """A descriptor whose relation flags are not booleans is not flagged (no raise)."""
    assert _relation_uses_non_pk_to_field(SimpleNamespace(many_to_many="yes")) is False


def test_relation_uses_non_pk_to_field_false_for_non_relation() -> None:
    """A plain scalar column is not flagged."""
    field = models.Book._meta.get_field("title")
    assert _relation_uses_non_pk_to_field(field) is False


def _seed_favorite_genre_profiles(*genre_names: str) -> list[models.Genre]:
    """Create one genre per name and one patron profile favoring each, in order."""
    genres: list[models.Genre] = []
    for index, genre_name in enumerate(genre_names):
        genre = models.Genre.objects.create(name=genre_name)
        patron = models.Patron.objects.create(name=f"patron-{index}")
        models.PatronProfile.objects.create(
            patron=patron,
            postal_code=f"{genre_name}-zip",
            favorite_genre=genre,
        )
        genres.append(genre)
    return genres


@pytest.mark.django_db
def test_global_id_filter_non_pk_to_field_matches_by_target_pk() -> None:
    """A marked forward-FK GlobalID filter compiles against the target's pk.

    The Relay GlobalID carries the genre's PRIMARY KEY, but
    ``PatronProfile.favorite_genre`` stores / joins on ``name``. The
    pk-qualified predicate (``favorite_genre__pk``) returns exactly the profile
    of the encoded genre, whereas the unqualified predicate
    (``favorite_genre=<pk>``) compares the pk value against the stored ``name``
    column and matches nothing.
    """
    alpha, _beta = _seed_favorite_genre_profiles("ALPHA", "BETA")
    assert str(saved_pk(alpha)) != alpha.name
    encoded = relay.to_base64("GenreType", str(saved_pk(alpha)))

    f = GlobalIDFilter(field_name="favorite_genre", lookup_expr="exact")
    # Boolean flag: ``filter`` derives ``f"{field_name}__pk"``.
    setattr(f, _GLOBALID_RELATION_PK_ATTR, True)
    result = f.filter(models.PatronProfile.objects.all(), encoded)
    assert set(result.values_list("postal_code", flat=True)) == {"ALPHA-zip"}

    # The unqualified predicate compares the pk value against the stored
    # ``name`` column and returns the WRONG (empty) result.
    wrong = models.PatronProfile.objects.filter(favorite_genre__exact=str(saved_pk(alpha)))
    assert wrong.count() == 0


@pytest.mark.django_db
def test_global_id_multiple_choice_filter_non_pk_to_field_union_by_pk() -> None:
    """A marked multi-choice ``in`` filter unions both genres' profiles by pk."""
    alpha, beta, _gamma = _seed_favorite_genre_profiles("ALPHA", "BETA", "GAMMA")
    encoded = [
        relay.to_base64("GenreType", str(saved_pk(alpha))),
        relay.to_base64("GenreType", str(saved_pk(beta))),
    ]
    f = GlobalIDMultipleChoiceFilter(field_name="favorite_genre", lookup_expr="in")
    # Boolean flag: ``filter`` derives ``f"{field_name}__pk"``.
    setattr(f, _GLOBALID_RELATION_PK_ATTR, True)
    result = f.filter(models.PatronProfile.objects.all(), encoded)
    assert set(result.values_list("postal_code", flat=True)) == {"ALPHA-zip", "BETA-zip"}

    # The unqualified ``favorite_genre__in`` compares the pk values against the
    # stored ``name`` column and matches nothing.
    wrong = models.PatronProfile.objects.filter(
        favorite_genre__in=[str(saved_pk(alpha)), str(saved_pk(beta))],
    )
    assert wrong.count() == 0


def test_global_id_filter_fk_to_pk_predicate_is_byte_identical() -> None:
    """Without the marker, the predicate is the unchanged ``{field__lookup: node_id}``."""
    qs = _RecordingQs()

    encoded = relay.to_base64("ShelfType", "7")
    f = GlobalIDFilter(field_name="shelf", lookup_expr="exact")
    assert getattr(f, _GLOBALID_RELATION_PK_ATTR, False) is not True
    f.filter(qs, encoded)
    assert qs.captured == {"shelf__exact": "7"}


def test_global_id_multiple_choice_filter_in_predicate_is_byte_identical() -> None:
    """Without the marker, the ``in`` predicate keeps the raw whole-list form."""
    qs = _RecordingQs()

    encoded = [relay.to_base64("GenreType", "1"), relay.to_base64("GenreType", "2")]
    f = GlobalIDMultipleChoiceFilter(field_name="genres", lookup_expr="in")
    assert getattr(f, _GLOBALID_RELATION_PK_ATTR, False) is not True
    # ``MultipleChoiceFilter`` defaults ``distinct=True``; the stub must accept it.
    f.filter(qs, encoded)
    assert qs.captured == {"genres__in": ["1", "2"]}


def test_global_id_filter_marked_empty_node_id_rejects_before_query() -> None:
    """The marked non-pk-``to_field`` path also rejects an empty id -- never a 500.

    Unmarked own-PK empty-id over HTTP:
    ``test_library_api.py::test_library_genres_filter_empty_id_scalar_global_id_raises_globalid_invalid``.
    No fakeshop filterset exposes the one non-pk ``to_field`` relation
    (``PatronProfile.favorite_genre``), so this marked path stays package-side.

    A MARKED leaf would compile ``<relation>__pk__exact=""`` (a 500
    ``ValueError`` on the integer target pk) if the empty id slipped past the
    scalar no-op. The reject happens inside ``_decode_and_validate_global_id``
    -- before the marked/unmarked branch and before any queryset access -- so
    the marked path raises the same clean ``GLOBALID_INVALID`` and never
    touches the database.
    """
    f = GlobalIDFilter(field_name="favorite_genre", lookup_expr="exact")
    setattr(f, _GLOBALID_RELATION_PK_ATTR, True)
    with pytest.raises(GraphQLError, match="empty node id") as exc_info:
        f.filter(_RecordingQs(), relay.to_base64("GenreType", ""))
    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


# ---------------------------------------------------------------------------
# LazyRelatedClassMixin
# ---------------------------------------------------------------------------


class _SampleClass:
    """Throw-away target for the lazy-resolution callable branch."""


def test_lazy_related_class_mixin_resolves_absolute_path() -> None:
    mixin = LazyRelatedClassMixin()
    resolved = mixin.resolve_lazy_class(
        "tests.filters.fixtures.filtersets.ShelfFilter",
        None,
    )

    assert resolved is ShelfFilter


def test_lazy_related_class_mixin_falls_back_to_bound_module() -> None:
    mixin = LazyRelatedClassMixin()

    resolved = mixin.resolve_lazy_class("ShelfFilter", BranchFilter)
    assert resolved is ShelfFilter


def test_lazy_related_class_mixin_returns_class_as_is() -> None:
    mixin = LazyRelatedClassMixin()
    assert mixin.resolve_lazy_class(_SampleClass, None) is _SampleClass


def test_lazy_related_class_mixin_invokes_callable_factory() -> None:
    mixin = LazyRelatedClassMixin()
    instance = mixin.resolve_lazy_class(
        partial(_SampleClass),
        None,
    )
    assert isinstance(instance, _SampleClass)


def test_lazy_related_class_mixin_raises_when_unresolved_string_has_no_bound_class() -> None:
    mixin = LazyRelatedClassMixin()
    with pytest.raises(ImportError):
        mixin.resolve_lazy_class("definitely.not.a.module.ClassName", None)


# ---------------------------------------------------------------------------
# RelatedFilter
# ---------------------------------------------------------------------------


def test_related_filter_accepts_class_argument() -> None:
    f = RelatedFilter(ShelfFilter)
    assert f._filterset is ShelfFilter


def test_related_filter_accepts_absolute_path_argument() -> None:
    f = RelatedFilter("tests.filters.fixtures.filtersets.ShelfFilter")
    assert f._filterset == "tests.filters.fixtures.filtersets.ShelfFilter"


def test_related_filter_accepts_unqualified_name_argument() -> None:
    f = RelatedFilter("ShelfFilter")
    assert f._filterset == "ShelfFilter"


def test_related_filter_bind_filterset_sets_bound_filterset() -> None:
    f = RelatedFilter("ShelfFilter")

    f.bind_filterset(ShelfFilter)
    assert f.bound_filterset is ShelfFilter
    f.bind_filterset(BranchFilter)
    # Idempotent: a second `bind_filterset` is a no-op.
    assert f.bound_filterset is ShelfFilter


def test_related_filter_filterset_property_resolves_lazy_string() -> None:
    rel = BranchFilterByString.related_filters["shelves"]
    assert rel.filterset is ShelfFilter


def test_related_filter_filterset_property_resolves_absolute_path() -> None:
    rel = BranchFilterByPath.related_filters["shelves"]
    assert rel.filterset is ShelfFilter


def test_related_filter_get_queryset_auto_derives_from_target_model() -> None:
    rel = BranchFilter.related_filters["shelves"]
    qs = rel.get_queryset(request=None)
    assert qs is not None
    assert qs.model is models.Shelf


def test_related_filter_get_queryset_honors_explicit_queryset() -> None:
    explicit_qs = models.Shelf.objects.filter(code="topic-A")
    f = RelatedFilter(ShelfFilter, queryset=explicit_qs)
    # Constructor records the explicit-queryset ledger entry.
    assert f._has_explicit_queryset is True
    assert f.get_queryset(request=None) is explicit_qs


def test_related_filter_explicit_queryset_ledger_defaults_false_when_absent() -> None:
    f = RelatedFilter("ShelfFilter")
    assert f._has_explicit_queryset is False


def test_related_filter_rejects_lookups_kwarg() -> None:
    """The cookbook-port `lookups=` kwarg is dropped; nothing read it.

    Pinning: passing `lookups=` to `RelatedFilter.__init__` must raise
    `TypeError` (unexpected keyword argument). Equivalent shape would be to
    confirm `"lookups"` is absent from `inspect.signature(RelatedFilter)`,
    but the runtime call is the consumer-facing contract.
    """
    with pytest.raises(TypeError):
        RelatedFilter("ShelfFilter", lookups=["exact", "in"])


def test_related_filter_filterset_setter_substitutes_target() -> None:
    """The `filterset` setter swaps the resolved target class in place."""
    rel = RelatedFilter("ShelfFilter")
    # Setter stores the substituted class on `_filterset`.
    rel.filterset = BranchFilter
    assert rel._filterset is BranchFilter
    # Getter resolves the (already-concrete) class as-is and re-stores it.
    assert rel.filterset is BranchFilter
    # A second substitution is honored.
    rel.filterset = ShelfFilter
    assert rel.filterset is ShelfFilter


# ---------------------------------------------------------------------------
# ArrayFilterMethod / ListFilterMethod __call__ dispatch
# ---------------------------------------------------------------------------


def test_array_filter_method_call_passes_through_none() -> None:
    """`ArrayFilterMethod.__call__` returns the queryset untouched for `None`."""

    def custom(_qs: object, name: str, value: object) -> tuple[str, str, object]:
        return ("custom", name, value)

    sentinel = _RecordingQs()
    f = ArrayFilter(field_name="tags", method=custom)
    assert isinstance(f.filter, ArrayFilterMethod)
    assert f.filter(sentinel, None) is sentinel


def test_array_filter_method_call_dispatches_to_custom_method() -> None:
    """A non-`None` value reaches the consumer callable with `(qs, field_name, value)`."""

    def custom(_qs: object, name: str, value: object) -> tuple[str, str, object]:
        return ("custom", name, value)

    f = ArrayFilter(field_name="tags", method=custom)
    assert f.filter(_RecordingQs(), [1, 2]) == ("custom", "tags", [1, 2])


def test_list_filter_method_setter_swaps_in_list_filter_method() -> None:
    """A consumer-supplied `method=` callable plugs in `ListFilterMethod`."""

    def custom(qs: object, _name: str, _value: object) -> object:
        return qs

    f = ListFilter(field_name="ids", method=custom)
    assert isinstance(f.filter, ListFilterMethod)


def test_list_filter_method_call_passes_through_none() -> None:
    """`ListFilterMethod.__call__` returns the queryset untouched for `None`."""

    def custom(_qs: object, name: str, value: object) -> tuple[str, str, object]:
        return ("custom", name, value)

    sentinel = _RecordingQs()
    f = ListFilter(field_name="ids", method=custom)
    assert f.filter(sentinel, None) is sentinel


def test_list_filter_method_call_dispatches_to_custom_method() -> None:
    """A non-`None` value reaches the consumer callable with `(qs, field_name, value)`."""

    def custom(_qs: object, name: str, value: object) -> tuple[str, str, object]:
        return ("custom", name, value)

    f = ListFilter(field_name="ids", method=custom)
    assert f.filter(_RecordingQs(), [1, 2]) == ("custom", "ids", [1, 2])


def test_array_filter_applies_distinct_when_flagged() -> None:
    """`ArrayFilter.filter` calls `.distinct()` when the filter is `distinct=True`."""
    qs = _RecordingQs()

    f = ArrayFilter(field_name="tags", lookup_expr="exact", distinct=True)
    result = f.filter(qs, [1])
    assert result is qs
    assert qs.distinct_calls == 1
    assert qs.captured == {"tags__exact": [1]}


# ---------------------------------------------------------------------------
# Strategy-aware GlobalID validation (spec-031 Decision 13) - owner/target
# definition resolution + per-strategy accepted-type-name set.
# ---------------------------------------------------------------------------


def _definition(
    model: type[Model],
    type_name: str,
    strategy: str | None = "model",
    fields: tuple[str, ...] = ("id",),
) -> DjangoTypeDefinition:
    """Declare a real ``DjangoType`` over ``model`` and record its finalization-time strategy.

    ``effective_globalid_strategy`` is the slot the Relay finalization step writes; setting it
    here stands in for that step, so each test states the strategy it exercises.
    """
    django_model = model
    declared_fields = fields

    class _Type(DjangoType):
        class Meta:
            model = django_model
            fields = declared_fields
            name = type_name

    definition = _Type.__django_strawberry_definition__
    definition.effective_globalid_strategy = strategy
    return definition


def _owner(strategy: str | None = "model") -> DjangoTypeDefinition:
    """The owning ``Book`` definition, emitted as ``OwnerType``."""
    return _definition(models.Book, "OwnerType", strategy)


def _bound(filter_: _FilterT, owner: DjangoTypeDefinition | None) -> _FilterT:
    """Return ``filter_`` as a real ``FilterSet`` instance binds it, its class owned by ``owner``.

    Instantiating the filterset hands each declared filter a copy whose ``parent`` is the
    instance, the slot the GlobalID target resolution reads the owner through; ``None``
    leaves the filterset unbound.
    """

    class OwnerFilter(FilterSet):
        bound = filter_

        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    OwnerFilter._owner_definition = owner
    bound = OwnerFilter().filters["bound"]
    assert isinstance(bound, type(filter_))
    return bound


def _global_id_filter_with_owner(field_name: str, owner: DjangoTypeDefinition) -> GlobalIDFilter:
    return _bound(GlobalIDFilter(field_name=field_name), owner)


def test_globalid_target_returns_none_without_owner() -> None:
    """No bound owner -> no definition (node-id-only fallback in unit contexts)."""
    f = _bound(GlobalIDFilter(field_name="id"), None)
    assert _globalid_target(f) is None


def test_globalid_target_own_pk_branch() -> None:
    """When the field is the owner's PK, the owner definition itself is returned."""
    owner = _owner()
    f = _global_id_filter_with_owner("id", owner)
    target = _globalid_target(f)
    assert target is not None
    assert target.definition is owner


def test_globalid_target_relation_branch() -> None:
    """A relation head resolves through `related_target_for` to the target definition."""
    target_def = _definition(models.Genre, "GenreType")
    owner = _owner()
    f = _global_id_filter_with_owner("genres__id", owner)
    target = _globalid_target(f)
    assert target is not None
    assert target.definition is target_def


def test_globalid_target_relation_branch_unresolved_target() -> None:
    """An unresolvable relation head returns `None` (decode without validation)."""
    owner = _owner()
    f = _global_id_filter_with_owner("genres__id", owner)
    assert _globalid_target(f) is None


def test_accepted_globalid_type_names_none_definition() -> None:
    """No definition -> `None` (node-id-only fallback)."""
    assert _accepted_globalid_type_names(None) is None


def test_accepted_globalid_type_names_per_strategy() -> None:
    """Each framework strategy maps to its accepted `type_name` payload set."""
    model_owner = _owner("model")
    type_owner = _owner("type")
    both_owner = _owner("type+model")
    assert _accepted_globalid_type_names(model_owner) == {"library.book"}
    assert _accepted_globalid_type_names(type_owner) == {"OwnerType"}
    assert _accepted_globalid_type_names(both_owner) == {"library.book", "OwnerType"}


def test_accepted_globalid_type_names_keep_the_default_spelling_for_an_unpublished_target() -> (
    None
):
    """A schema publishing no object type for the target keeps the ``graphql_type_name``.

    Live siblings accept the schema-published name on every GlobalID filter shape
    (``examples/fakeshop/test_query/test_globalid_naming_api.py``); a schema that
    cannot emit an id for the target has only the type's own spelling to accept.
    """

    @strawberry.type
    class Query:
        ping: str = "pong"

    schema = strawberry.Schema(query=Query)
    assert _accepted_globalid_type_names(_owner("type"), schema) == {"OwnerType"}
    assert _accepted_globalid_type_names(_owner("type+model"), schema) == {
        "library.book",
        "OwnerType",
    }


def test_filter_schema_is_none_outside_the_apply_pipeline() -> None:
    """A filterset constructed directly carries no resolver ``info``, so no schema."""
    f = _global_id_filter_with_owner("id", _owner("type"))
    assert _filter_schema(f) is None
    assert _filter_schema(GlobalIDFilter(field_name="id")) is None


@pytest.mark.parametrize("strategy", ["callable", "custom", None])
def test_accepted_globalid_type_names_non_framework_strategies(strategy: str | None) -> None:
    """`callable` / `custom` / absent strategy -> `None` accepted set (defensive belt).

    `_decode_and_validate_global_id` fail-closes on these before reaching this
    helper (see `test_filter_encode_only_strategy_rejects_fail_closed` /
    `test_filter_known_definition_none_strategy_rejects_fail_closed`); the helper
    keeps returning `None` as a defensive belt only.
    """
    owner = _owner(strategy)
    assert _accepted_globalid_type_names(owner) is None


def test_filter_model_strategy_accepts_model_label() -> None:
    """Under `model`, an own-PK filter accepts the model-label payload."""
    owner = _owner("model")
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("library.book", "42")
    assert _decode_and_validate_global_id(encoded, f) == 42


def test_filter_model_strategy_accepts_predecoded_global_id() -> None:
    """The filter accepts Strawberry's already-coerced ``GlobalID`` value unchanged."""
    owner = _owner("model")
    f = _global_id_filter_with_owner("id", owner)

    assert _decode_and_validate_global_id(relay.GlobalID("library.book", "42"), f) == 42


def test_filter_model_strategy_rejects_type_name() -> None:
    """Under `model`, the bare GraphQL type name is rejected."""
    owner = _owner("model")
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("OwnerType", "42")
    with pytest.raises(GraphQLError, match="GlobalID type mismatch"):
        _decode_and_validate_global_id(encoded, f)


def test_filter_type_strategy_accepts_graphql_name() -> None:
    """`type` preserves the pre-0.0.9 `graphql_type_name` acceptance."""
    owner = _owner("type")
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("OwnerType", "7")
    assert _decode_and_validate_global_id(encoded, f) == 7
    # And rejects a model-label payload under `type`.
    with pytest.raises(GraphQLError, match="GlobalID type mismatch"):
        _decode_and_validate_global_id(relay.to_base64("library.book", "7"), f)


def test_filter_type_plus_model_accepts_both() -> None:
    """`type+model` accepts model-label AND type-name inputs."""
    owner = _owner("type+model")
    f = _global_id_filter_with_owner("id", owner)
    assert _decode_and_validate_global_id(relay.to_base64("library.book", "1"), f) == 1
    assert _decode_and_validate_global_id(relay.to_base64("OwnerType", "2"), f) == 2


@pytest.mark.parametrize("strategy", ["callable", "custom"])
def test_filter_encode_only_strategy_rejects_fail_closed(strategy: str) -> None:
    """`callable` / `custom` targets fail closed: the strategy is encode-only.

    These strategies have no decode path, so a typed filter input for the
    target's GlobalID could never validly consume the IDs it emits. The runtime
    backstop (behind the build-time audit) rejects with a coded GraphQLError.
    """
    owner = _owner(strategy)
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("AnythingAtAll", "99")
    with pytest.raises(GraphQLError, match="encode-only") as exc_info:
        _decode_and_validate_global_id(encoded, f)
    assert exc_info.value.extensions == {"code": "GLOBALID_UNVALIDATABLE"}
    assert strategy in str(exc_info.value)


def test_filter_known_definition_none_strategy_rejects_fail_closed() -> None:
    """A known target whose recorded strategy is `None` is a lifecycle defect.

    An unfinalized / non-Relay target should never reach a GlobalID filter; the
    backstop rejects with a coded GraphQLError distinct from the encode-only
    message rather than silently falling back to node-id-only.
    """
    owner = _owner(None)
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("AnythingAtAll", "99")
    with pytest.raises(GraphQLError, match=r"no .*recorded globalid strategy") as exc_info:
        _decode_and_validate_global_id(encoded, f)
    assert exc_info.value.extensions == {"code": "GLOBALID_UNVALIDATABLE"}


def test_multi_value_filter_encode_only_reject_names_index() -> None:
    """`GlobalIDMultipleChoiceFilter` names the offending index on a fail-closed reject."""
    owner = _owner("callable")
    f = _bound(GlobalIDMultipleChoiceFilter(field_name="id"), owner)
    with pytest.raises(GraphQLError, match="at index 0") as exc_info:
        f.filter(_RecordingQs(), [relay.to_base64("AnythingAtAll", "99")])
    assert exc_info.value.extensions == {"code": "GLOBALID_UNVALIDATABLE"}


def test_filter_unbound_owner_node_id_only() -> None:
    """No bound owner -> node-id-only fallback (the existing `None`-definition path)."""
    f = _bound(GlobalIDFilter(field_name="id"), None)
    encoded = relay.to_base64("WhateverType", "5")
    assert _decode_and_validate_global_id(encoded, f) == "5"


def test_filter_wrong_model_rejected() -> None:
    """A wrong-model GlobalID is still rejected for a framework strategy."""
    owner = _owner("model")
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("other.thing", "42")
    with pytest.raises(GraphQLError, match="GlobalID type mismatch"):
        _decode_and_validate_global_id(encoded, f)


def test_filter_non_string_global_id_value_rejected_as_malformed() -> None:
    """A non-string GlobalID value takes the malformed-payload route.

    Only ``str`` (wire form) and ``relay.GlobalID`` objects decode; any
    other value is the same malformed-payload class as bad base64, so the
    caller observes the coded ``GLOBALID_INVALID`` rejection, never a raw
    ``ValueError``.
    """
    f = GlobalIDFilter(field_name="id")
    with pytest.raises(GraphQLError, match="not a valid GlobalID") as exc_info:
        _decode_and_validate_global_id(42, f)
    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


def test_related_filter_relation_branch_strategy_aware() -> None:
    """A relation-branch (target-definition) filter applies the target's strategy."""
    _definition(models.Genre, "GenreType", "model")
    owner = _owner()
    f = _global_id_filter_with_owner("genres__id", owner)
    # The target's model label is accepted; the target's type name is rejected.
    assert _decode_and_validate_global_id(relay.to_base64("library.genre", "3"), f) == 3
    with pytest.raises(GraphQLError, match="GlobalID type mismatch"):
        _decode_and_validate_global_id(relay.to_base64("GenreType", "3"), f)


def test_multi_value_filter_strategy_aware_indexes_rejection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`GlobalIDMultipleChoiceFilter` routes through the strategy-aware check.

    A wrong-shape element names its index in the rejection message; a
    well-shaped batch decodes the model-label payloads through to the upstream
    filter. Spies on the upstream ``MultipleChoiceFilter.filter`` (same pattern
    as ``test_global_id_multiple_choice_filter_decodes_every_element``) so the
    real ``Q``-object filter machinery does not run.
    """
    owner = _owner("model")
    captured: list[list[object]] = []

    def spy(_self: object, qs: object, value: Iterable[object]) -> object:
        captured.append(list(value))
        return qs

    monkeypatch.setattr(GlobalIDMultipleChoiceFilter.__mro__[1], "filter", spy)

    accepted = _bound(GlobalIDMultipleChoiceFilter(field_name="id"), owner)
    accepted.filter(
        _RecordingQs(),
        [relay.to_base64("library.book", "1"), relay.to_base64("library.book", "2")],
    )
    assert captured == [[1, 2]]

    rejected = _bound(GlobalIDMultipleChoiceFilter(field_name="id"), owner)
    with pytest.raises(GraphQLError, match="at index 1"):
        rejected.filter(
            _RecordingQs(),
            [relay.to_base64("library.book", "1"), relay.to_base64("OwnerType", "2")],
        )


# ---------------------------------------------------------------------------
# Multi-hop GlobalID target definition resolution
# ---------------------------------------------------------------------------


def test_resolve_globalid_target_definition_multihop() -> None:
    """`resolve_globalid_target_definition` walks multi-hop relation paths.

    Scope note. The CONSUMER-VISIBLE half of this contract is pinned live at
    ``examples/fakeshop/test_query/test_library_api.py::test_relay_global_id_filter_multihop_leaf_validates_against_the_terminal_model``,
    which drives the shipped ``genresBooksId`` leaf over real HTTP and proves
    the accept/reject polarity (terminal ``library.book`` accepted, head
    ``library.genre`` rejected). That is the row the README's coverage rule
    requires, because the behavior is reachable from a real query.

    What stays here is what a live request cannot construct: the ``pk``/``id``
    suffix equivalences, and the six unresolvable-path rows below (an
    over-long path, unknown segments, an empty string, ``None``, and a
    non-string field name). Every generated leaf resolves by construction and
    a non-str field name cannot come off the wire, so those have no live form.
    """
    branch_def = _definition(models.Branch, "BranchType", "type")
    shelf_def = _definition(models.Shelf, "ShelfType", "type")
    owner = _owner("type")

    # Single-hop own pk
    assert resolve_globalid_target_definition(owner, "id") is owner
    assert resolve_globalid_target_definition(owner, "pk") is owner

    # Single-hop relation
    assert resolve_globalid_target_definition(owner, "shelf") is shelf_def
    assert resolve_globalid_target_definition(owner, "shelf__id") is shelf_def
    assert resolve_globalid_target_definition(owner, "shelf__pk") is shelf_def

    # Multi-hop relation
    assert resolve_globalid_target_definition(owner, "shelf__branch") is branch_def
    assert resolve_globalid_target_definition(owner, "shelf__branch__id") is branch_def
    assert resolve_globalid_target_definition(owner, "shelf__branch__pk") is branch_def

    # Unresolvable paths return None
    assert resolve_globalid_target_definition(owner, "shelf__branch__id__extra") is None
    assert resolve_globalid_target_definition(owner, "shelf__nonexistent") is None
    assert resolve_globalid_target_definition(owner, "nonexistent") is None
    assert resolve_globalid_target_definition(owner, "") is None
    assert resolve_globalid_target_definition(owner, None) is None
    # basedpyright: the non-str field name is the hostile input under test;
    # resolve_globalid_target_definition types the parameter as str | None
    assert resolve_globalid_target_definition(owner, 123) is None  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize(
    ("owner_model", "field_name", "expected_model"),
    [
        # ``PatronProfile.patron`` is the primary key AND a one-to-one relation.
        (models.PatronProfile, "patron", models.Patron),
        (models.PatronProfile, "pk", models.Patron),
        (models.PatronProfile, "patron__id", models.Patron),
        (models.PatronProfile, "pk__pk", models.Patron),
        (models.PatronProfile, "patron__card", models.MembershipCard),
        (models.PatronProfile, "pk__card", models.MembershipCard),
        (models.PatronProfile, "patron__card__id", models.MembershipCard),
        # MTI: the child's primary key is the ``<parent>_ptr`` parent link.
        (models.LendingDesk, "venue_ptr", models.Venue),
        (models.LendingDesk, "pk", models.Venue),
        (models.SelfServeDesk, "pk", models.LendingDesk),
        (models.SelfServeDesk, "pk__pk", models.Venue),
        (models.SelfServeDesk, "lendingdesk_ptr__venue_ptr__id", models.Venue),
    ],
)
def test_resolve_globalid_target_definition_walks_a_relation_primary_key(
    owner_model: type[Model],
    field_name: str,
    expected_model: type[Model],
) -> None:
    """A primary key that is itself a relation is walked as a relation, never the owner's own id.

    The terminal ``pk`` / key name resolves to the model the key points at, and a
    path through it continues from there, so a GlobalID validates against the
    terminal model instead of being accepted node-id-only or checked against the
    owner.
    """
    definitions: dict[type[Model], DjangoTypeDefinition] = {
        models.Patron: _definition(models.Patron, "PatronType"),
        models.MembershipCard: _definition(models.MembershipCard, "MembershipCardType"),
        models.PatronProfile: _definition(
            models.PatronProfile,
            "PatronProfileType",
            fields=("patron",),
        ),
        models.Venue: _definition(models.Venue, "VenueType"),
        models.LendingDesk: _definition(models.LendingDesk, "LendingDeskType"),
        models.SelfServeDesk: _definition(models.SelfServeDesk, "SelfServeDeskType"),
    }

    resolved = resolve_globalid_target_definition(definitions[owner_model], field_name)

    assert resolved is definitions[expected_model]


# ---------------------------------------------------------------------------
# Range validation & Integer/Range filter edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "invalid_value",
    [
        123,
        45.6,
        True,
        False,
        object(),
        {"a": 1, "b": 2},
        [1],
        [1, 2, 3],
        (),
        (1,),
        (1, 2, 3),
        "ab",
    ],
)
def test_validate_range_rejects_non_two_element_sequences(invalid_value: object) -> None:
    """`validate_range` rejects non-sequences, wrong lengths, and mappings with ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        validate_range(invalid_value)
    assert exc_info.value.code == "invalid"


def test_integer_in_filter_unbound_and_missing_model() -> None:
    """`IntegerInFilter.filter` safely filters when unbound or when model field is unresolvable."""
    qs = models.Shelf.objects.all()

    # Standalone / unbound filter instance (parent attribute is absent)
    f = IntegerInFilter(field_name="id", lookup_expr="in")
    assert getattr(f, "parent", None) is None
    res = f.filter(qs, [1, 2])
    assert "IN (1, 2)" in str(res.query)

    # None (omission) passes through without crashing.
    assert f.filter(qs, None) is qs

    # A non-list scalar is a CODED reject at the shape gate: iterated, a
    # string would go char-by-char through the coercion loop ("26"
    # coercing to [2, 6] -- a wrong-result membership) and a bare int
    # would leak ``TypeError: 'int' object is not iterable``.
    with pytest.raises(GraphQLError) as exc_info:
        f.filter(qs, "")
    assert exc_info.value.extensions == {"code": "FILTER_INVALID"}


def test_integer_range_filter_malformed_values_pass_through() -> None:
    """`IntegerRangeFilter.filter` passes through malformed non-range values without crashing."""
    qs = models.Shelf.objects.all()
    f = IntegerRangeFilter(field_name="id")

    assert f.filter(qs, None) is qs
    assert f.filter(qs, "") is qs
    assert f.filter(qs, [1]) is qs
    assert f.filter(qs, [1, 2, 3]) is qs
    assert f.filter(qs, 123) is qs
    assert f.filter(qs, "invalid") is qs


def test_filters_base_edge_cases() -> None:
    """Edge cases for _coerce_int_in_members and the relation-pk marker helpers."""
    # Line 376: model_field is None
    assert _coerce_int_in_members(None, [1, "foo", 3]) == [1, "foo", 3]

    # _relation_uses_non_pk_to_field: non-relation field or None
    assert _relation_uses_non_pk_to_field(None) is False
    assert _relation_uses_non_pk_to_field(object()) is False

    # _marked_pk_field_name: unmarked or missing field_name
    f = GlobalIDFilter()
    assert _marked_pk_field_name(f) is None

    setattr(f, _GLOBALID_RELATION_PK_ATTR, True)
    f.field_name = None
    assert _marked_pk_field_name(f) is None

    f.field_name = "target"
    assert _marked_pk_field_name(f) == "target__pk"


def test_related_filter_get_queryset_mistyped_target_is_typed() -> None:
    """``RelatedFilter.get_queryset`` rejects a mis-typed target with the gate's typed error.

    Ungated, a non-FilterSet target would make the fallback return ``None``
    (its ``_meta`` read comes back empty), leaking a ``None`` queryset into
    django-filter's field build. The gate rejects the mis-typed target at the
    ``.filterset`` read instead.
    """

    class _NoModelFilterSet:
        _meta = None

    # basedpyright: the non-FilterSet target is the hostile input under test; RelatedFilter types
    # the parameter as _FilterSetTarget
    rel = RelatedFilter(_NoModelFilterSet)  # pyright: ignore[reportArgumentType]
    with pytest.raises(ConfigurationError) as exc_info:
        rel.get_queryset(request=None)
    assert "is not a FilterSet subclass" in str(exc_info.value)


# ---------------------------------------------------------------------------
# RelatedFilter target-type gate (the `.filterset` read seam).
# ---------------------------------------------------------------------------


class _PlainClassTarget:
    """A plain class that is not a FilterSet (the mis-typed RelatedFilter target)."""


def test_related_filter_gate_accepts_filterset_class_target() -> None:
    class Target(FilterSet):
        class Meta:
            model = models.Shelf
            fields = ["id"]

    related = RelatedFilter(Target, field_name="shelves")
    assert related.filterset is Target


def test_related_filter_gate_passes_the_none_placeholder() -> None:
    """``RelatedFilter(None)`` is the skip-silently placeholder, and the gate passes it.

    The BFS enqueue and ``_expand_related_filter`` then skip the branch.
    """
    related = RelatedFilter(None, field_name="shelves")
    assert related.filterset is None


def test_related_filter_gate_rejects_plain_class_target() -> None:
    # basedpyright: the non-FilterSet target is the hostile input under test; RelatedFilter types
    # the parameter as _FilterSetTarget
    related = RelatedFilter(_PlainClassTarget, field_name="shelves")  # pyright: ignore[reportArgumentType]
    with pytest.raises(ConfigurationError) as exc_info:
        _ = related.filterset
    msg = str(exc_info.value)
    assert "declares RelatedFilter 'shelves'" in msg
    assert "_PlainClassTarget" in msg
    assert "is not a FilterSet subclass" in msg


def test_related_filter_gate_rejects_cross_family_orderset_target() -> None:
    """The cross-family twin: an ``OrderSet`` cannot filter a relation branch.

    The gate rejects it; otherwise it would be enqueued into the FILTER BFS, walking the order
    family's fields through the filter input builder.
    """

    class AnyOrderset(OrderSet):
        class Meta:
            model = models.Shelf
            fields = ["id"]

    # basedpyright: the OrderSet target is the hostile input under test; RelatedFilter types the
    # parameter as _FilterSetTarget
    related = RelatedFilter(AnyOrderset, field_name="shelves")  # pyright: ignore[reportArgumentType]
    with pytest.raises(ConfigurationError) as exc_info:
        _ = related.filterset
    assert "is not a FilterSet subclass" in str(exc_info.value)


def test_related_filter_gate_rejects_factory_returning_non_class() -> None:
    def factory() -> int:
        return 42

    # basedpyright: the factory returning a non-class is the hostile input under test;
    # RelatedFilter types the parameter as _FilterSetTarget
    related = RelatedFilter(factory, field_name="shelves")  # pyright: ignore[reportArgumentType]
    with pytest.raises(ConfigurationError):
        _ = related.filterset


def test_related_filter_gate_preserves_raw_import_error_for_unresolvable_strings() -> None:
    """The unresolvable-string raw ``ImportError`` stays raw at the property read.

    It is the finalizer's rewrap key.
    """
    related = RelatedFilter("no.such.module.NoSuchFilter", field_name="shelves")
    with pytest.raises(ImportError):
        _ = related.filterset


def test_related_filter_gate_names_the_bound_owner() -> None:
    class Target(FilterSet):
        class Meta:
            model = models.Shelf
            fields = ["id"]

    class Owner(FilterSet):
        shelves = RelatedFilter(Target, field_name="shelves")

        class Meta:
            model = models.Branch
            fields = ["id"]

    # Re-target the bound declaration through the permissive setter, then
    # read: the gate names the OWNING filterset, not just the target.
    # basedpyright: the plain non-FilterSet class is the bad target under test; the setter
    # declares only the FilterSet target shapes
    Owner.related_filters["shelves"].filterset = _PlainClassTarget  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(ConfigurationError) as exc_info:
        _ = Owner.related_filters["shelves"].filterset
    assert "Owner" in str(exc_info.value)


def test_related_filter_expansion_surfaces_the_gate_not_a_raw_attribute_error() -> None:
    """``FilterSet.get_filters()`` expansion surfaces the typed gate error.

    ``_expand_related_filter`` reads ``f.filterset``; a mis-typed target yields the typed error, not a
    raw ``AttributeError: ... has no attribute 'get_filters'``.
    """

    class Parent(FilterSet):
        # basedpyright: the non-FilterSet target is the hostile input under test; RelatedFilter
        # types the parameter as _FilterSetTarget
        shelves = RelatedFilter(_PlainClassTarget, field_name="shelves")  # pyright: ignore[reportArgumentType]

        class Meta:
            model = models.Branch
            fields = ["id"]

    with pytest.raises(ConfigurationError) as exc_info:
        Parent.get_filters()
    assert "is not a FilterSet subclass" in str(exc_info.value)


def test_related_filter_gate_rejects_mistyped_target_at_bfs_enqueue() -> None:
    """The BFS factory's enqueue hits the gate instead of enqueueing a mis-typed target.

    ``getattr(related, 'filterset')`` raises the typed error rather than detonating inside
    ``set_input_type_name``.
    """

    class Parent(FilterSet):
        # basedpyright: the non-FilterSet target is the hostile input under test; RelatedFilter
        # types the parameter as _FilterSetTarget
        shelves = RelatedFilter(_PlainClassTarget, field_name="shelves")  # pyright: ignore[reportArgumentType]

        class Meta:
            model = models.Branch
            fields = ["id"]

    factory = FilterArgumentsFactory(Parent)
    with pytest.raises(ConfigurationError):
        factory._ensure_built()


def test_related_filter_gate_passes_none_placeholder_through_bfs_enqueue() -> None:
    """The ``None`` placeholder is skipped silently by the BFS.

    The build succeeds with the related branch omitted.
    """

    class Parent(FilterSet):
        shelves = RelatedFilter(None, field_name="shelves")

        class Meta:
            model = models.Branch
            fields = ["id"]

    factory = FilterArgumentsFactory(Parent)
    factory._ensure_built()
    assert factory.input_object_types


# ---------------------------------------------------------------------------
# Filter-value shapes outside the form contract, at the filter() seam.
# ---------------------------------------------------------------------------


def test_list_filter_scalar_value_is_a_coded_reject() -> None:
    """A scalar never reaches ``len()``: the shape gate rejects it with the coded error."""
    f = ListFilter(field_name="code")
    with pytest.raises(GraphQLError) as exc_info:
        f.filter(models.Shelf.objects.none(), 42)
    assert exc_info.value.extensions == {"code": "FILTER_INVALID"}


def test_list_filter_one_shot_iterator_is_a_coded_reject() -> None:
    f = ListFilter(field_name="code")
    with pytest.raises(GraphQLError):
        f.filter(models.Shelf.objects.none(), iter(["a", "b"]))


def test_list_filter_string_value_is_rejected_not_iterated_charwise() -> None:
    """A string under an ``in`` lookup is rejected before Django can iterate it char-wise.

    Char-wise iteration would compile ``in: "26"`` to ``IN ('2','6')``.
    """
    f = ListFilter(field_name="code", lookup_expr="in")
    with pytest.raises(GraphQLError):
        f.filter(models.Shelf.objects.none(), "26")


def test_integer_in_filter_scalar_value_is_a_coded_reject() -> None:
    """A scalar that bypasses form coercion never reaches the coercion loop."""
    f = IntegerInFilter(field_name="lifetime_fines_cents")
    with pytest.raises(GraphQLError) as exc_info:
        f.filter(models.Shelf.objects.none(), 42)
    assert exc_info.value.extensions == {"code": "FILTER_INVALID"}


def test_integer_in_filter_string_value_is_rejected_not_iterated_charwise() -> None:
    """A string value is rejected before the coercion loop could iterate it char-by-char.

    ``in: "26"`` would coerce to ``[2, 6]``, a wrong-result membership.
    """

    class PatronFilter(FilterSet):
        fines = IntegerInFilter(field_name="lifetime_fines_cents")

        class Meta:
            model = models.Patron
            fields = {"name": ["exact"]}

    # django-filter binds the declared filter to its set as ``parent`` on instantiation.
    f = PatronFilter().filters["fines"]
    with pytest.raises(GraphQLError):
        f.filter(models.Shelf.objects.none(), "26")


def test_globalid_multiple_choice_list_subclass_iteration_error_propagates() -> None:
    """A ``list`` subclass passes the shape gate; its own ``__iter__`` exception propagates."""

    class RaisingIter(list[object]):
        @override
        def __iter__(self) -> Iterator[object]:
            raise RuntimeError("list subclass __iter__ raised")

    f = GlobalIDMultipleChoiceFilter(field_name="id")
    with pytest.raises(RuntimeError, match="list subclass __iter__ raised"):
        f.filter(models.Shelf.objects.none(), RaisingIter(["ShelfNode:1"]))


def test_array_filter_emptiness_probe_propagates_the_value_eq_error() -> None:
    """``value in EMPTY_VALUES`` compares through the value's own ``__eq__``.

    Whatever that ``__eq__`` raises propagates.
    """

    class RaisingEq:
        @override
        def __eq__(self, other: object) -> bool:
            raise RuntimeError("value __eq__ raised")

        @override
        def __ne__(self, other: object) -> bool:
            raise RuntimeError("value __ne__ raised")

        @override
        def __hash__(self) -> int:
            return 0

    f = ArrayFilter(field_name="tags")
    with pytest.raises(RuntimeError, match="value __eq__ raised"):
        f.filter(models.Shelf.objects.none(), RaisingEq())


def test_integer_range_filter_non_sequence_skips_without_comparing() -> None:
    """The shape check is the only emptiness probe, so a non-sequence skips uncompared.

    The value takes the pass-through skip and its ``__eq__`` never runs.
    """

    class RaisingEq:
        @override
        def __eq__(self, other: object) -> bool:
            raise RuntimeError("value __eq__ raised")

        @override
        def __hash__(self) -> int:
            return 0

    qs = models.Shelf.objects.none()
    f = IntegerRangeFilter(field_name="lifetime_fines_cents")
    assert f.filter(qs, RaisingEq()) is qs


def test_related_filter_gate_rejection_message_is_pinned() -> None:
    """The target-gate rejection names the owner, the declaration and the target kind."""

    class Owner(FilterSet):
        # basedpyright: the non-FilterSet target is the hostile input under test; RelatedFilter
        # types the parameter as _FilterSetTarget
        rel = RelatedFilter(_PlainClassTarget, field_name="shelves")  # pyright: ignore[reportArgumentType]

        class Meta:
            model = models.Branch
            fields = ["id"]

    with pytest.raises(ConfigurationError) as exc_info:
        _ = Owner.related_filters["rel"].filterset
    assert str(exc_info.value) == (
        f"{Owner.__qualname__} declares RelatedFilter 'shelves' targeting "
        "_PlainClassTarget, which is not a FilterSet subclass. "
        "RelatedFilter targets must resolve to a FilterSet subclass (a class, "
        "an import-path string, or a zero-arg factory returning one); "
        "an OrderSet or unrelated class cannot filter a relation branch. "
        "Declare the branch with a FilterSet or remove it."
    )


# ---------------------------------------------------------------------------
# Raw-primary-key relation filters (non-Relay targets)
# ---------------------------------------------------------------------------


def test_relation_identity_column_follows_a_relation_valued_primary_key() -> None:
    """A target whose own key is a one-to-one types by the column that key points at.

    ``Annotation.profile`` targets ``PatronProfile``, whose primary key IS its
    ``patron`` one-to-one, so the raw identity is ``Patron.id``.
    """
    column = relation_identity_column(models.Annotation._meta.get_field("profile"))
    assert column is models.Patron._meta.pk


def test_relation_identity_column_is_none_without_a_resolved_relation() -> None:
    """A plain column, and a relation with no resolved target model, have no identity column."""
    assert relation_identity_column(models.Book._meta.get_field("title")) is None
    assert relation_identity_column(SimpleNamespace(is_relation=True, related_model=None)) is None


@pytest.mark.django_db
def test_relation_pk_filters_generated_for_non_pk_to_field_match_by_target_pk() -> None:
    """A raw-pk ``favorite_genre`` key (FK on ``to_field="name"``) matches the genre's pk.

    No ``DjangoType`` exposes ``Genre`` here, so both leaves are raw-pk filters carrying
    the pk-qualification marker; the value is the target's primary key, never its
    ``name``.
    """
    alpha, beta, _gamma = _seed_favorite_genre_profiles("ALPHA", "BETA", "GAMMA")

    class ProfileFilter(FilterSet):
        class Meta:
            model = models.PatronProfile
            fields = {"favorite_genre": ["exact", "in"]}

    exact_leaf = ProfileFilter.base_filters["favorite_genre"]
    in_leaf = ProfileFilter.base_filters["favorite_genre__in"]
    assert isinstance(exact_leaf, RelationPkFilter)
    assert isinstance(in_leaf, RelationPkMultipleFilter)
    assert getattr(exact_leaf, _GLOBALID_RELATION_PK_ATTR) is True
    assert getattr(in_leaf, _GLOBALID_RELATION_PK_ATTR) is True

    def codes(data: dict[str, object]) -> list[str]:
        filterset = ProfileFilter(
            data=data,
            queryset=models.PatronProfile.objects.order_by("postal_code"),
            request=HttpRequest(),
        )
        return list(filterset.qs.values_list("postal_code", flat=True))

    assert codes({"favorite_genre": saved_pk(alpha)}) == ["ALPHA-zip"]
    assert codes({"favorite_genre__in": [saved_pk(alpha), saved_pk(beta)]}) == [
        "ALPHA-zip",
        "BETA-zip",
    ]


@pytest.mark.django_db
def test_relation_pk_filters_drop_a_value_the_target_column_cannot_hold() -> None:
    """An uncoercible key identifies no row: ``exact`` matches nothing, ``in`` drops it.

    The GraphQL scalar rejects such a value at the wire, so only a direct caller reaches
    this; the verdict is still "no row", never django-filter's empty-value skip.
    """
    branch = models.Branch.objects.create(name="Home", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    models.Book.objects.create(title="Kept", shelf=shelf)

    class BookShelfFilter(FilterSet):
        class Meta:
            model = models.Book
            fields = {"shelf": ["exact", "in"]}

    def titles(data: dict[str, object]) -> list[str]:
        filterset = BookShelfFilter(
            data=data,
            queryset=models.Book.objects.order_by("id"),
            request=HttpRequest(),
        )
        return list(filterset.qs.values_list("title", flat=True))

    assert titles({"shelf": "not-a-pk"}) == []
    assert titles({"shelf__in": ["not-a-pk"]}) == []
    assert titles({"shelf__in": ["not-a-pk", saved_pk(shelf)]}) == ["Kept"]


@pytest.mark.django_db
def test_relation_pk_list_field_skips_existence_checks_and_rejects_a_non_list() -> None:
    """The list form field accepts a pk no row carries, and refuses a scalar with a coded error.

    django-filter's ``ModelMultipleChoiceField`` answered "Select a valid choice" for the
    missing pk, which told it apart from a pk the target's ``get_queryset`` hides.
    """

    class BookGenreFilter(FilterSet):
        class Meta:
            model = models.Book
            fields = {"genres": ["exact"]}

    def form(data: dict[str, object]) -> Form:
        return BookGenreFilter(
            data=data,
            queryset=models.Book.objects.all(),
            request=HttpRequest(),
        ).form

    missing = form({"genres": [987654]})
    assert missing.is_valid(), missing.errors
    assert missing.cleaned_data["genres"] == [987654]
    scalar = form({"genres": "5"})
    assert not scalar.is_valid()
    assert scalar.errors.as_data()["genres"][0].code == "invalid_list"


@pytest.mark.django_db
def test_unbound_relation_pk_filters_apply_the_value_uncoerced() -> None:
    """A filter with no parent filterset has no model to read a column from: value as given."""
    branch = models.Branch.objects.create(name="Home", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    other = models.Shelf.objects.create(code="B-2", topic="general", branch=branch)
    models.Book.objects.create(title="Kept", shelf=shelf)
    models.Book.objects.create(title="Other", shelf=other)
    books = models.Book.objects.order_by("id")

    single = RelationPkFilter(field_name="shelf", lookup_expr="exact")
    many = RelationPkMultipleFilter(field_name="shelf", lookup_expr="in")
    assert list(single.filter(books, saved_pk(shelf)).values_list("title", flat=True)) == ["Kept"]
    assert list(many.filter(books, [saved_pk(other)]).values_list("title", flat=True)) == ["Other"]
    assert single.filter(books, None) is books
    assert many.filter(books, None) is books
