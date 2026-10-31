"""Filter primitive tests for typed, list, range, global-ID, and related filters.

Covers the five parity-floor primitives (`TypedFilter`, `ArrayFilter`,
`RangeFilter`, `ListFilter`, `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter`),
the lazy-resolution mixin, and `RelatedFilter`.

Own-PK empty / malformed GlobalID filter rejection lives in
``test_library_api.py``. This file keeps primitive form contracts, query-object identity, metadata,
lazy ``RelatedFilter`` resolution, and encode-only strategy refusal. The
``PatronProfile.favorite_genre`` target-key round trips live in
``test_library_api.py``; generated GlobalID list inputs reject non-list containers
before ``GlobalIDMultipleChoiceFilter`` runs. Ordinary JSON consumer arguments are a
separate public form surface.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterable, Iterator
from decimal import Decimal
from functools import partial
from types import SimpleNamespace
from typing import TYPE_CHECKING, ClassVar, TypeVar

import django_filters
import pytest
import strawberry
from apps.library import models
from apps.scalars import models as scalar_models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import DEFAULT_DB_ALIAS
from django.db import connection as db_connection
from django.db import models as db_models
from django.db.models import Model, QuerySet
from django.db.models.expressions import Combinable
from django.forms import CharField, DecimalField, Field, Form, SelectMultiple
from django.http import HttpRequest, QueryDict
from django.test.utils import CaptureQueriesContext, isolate_apps
from django.utils.translation import gettext_lazy
from django_filters import BaseInFilter, CharFilter
from django_filters.filterset import BaseFilterSet
from django_filters.rest_framework import DjangoFilterBackend
from graphql import GraphQLError
from rest_framework import generics
from rest_framework.test import APIRequestFactory
from strawberry import relay
from typing_extensions import Self, override

from django_strawberry_framework import (
    DjangoType,
    finalize_django_types,
)
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
    _coerce_relation_identity,
    _column_form_field,
    _decode_and_validate_global_id,
    _ElementField,
    _filter_schema,
    _filterset_model_field,
    _filterset_value_field,
    _globalid_target,
    _marked_pk_field_name,
    membership_in_filter_class,
    relation_identity_column,
    resolve_globalid_target_definition,
)
from django_strawberry_framework.filters.factories import FilterArgumentsFactory
from django_strawberry_framework.filters.inputs import convert_filter_to_input_annotation
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.types.definition import DjangoTypeDefinition
from django_strawberry_framework.utils._narrowing import (
    call_method,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.relations import is_model_class
from django_strawberry_framework.utils.typing import object_result
from tests._cleaned_filter_sets import (
    KEPT_EXTERNAL_ID as _KEPT_EXTERNAL_ID,
)
from tests._cleaned_filter_sets import (
    PackageCleanedScalarSet as _PackageCleanedScalarSet,
)
from tests._cleaned_filter_sets import (
    PlainCleanedScalarSet as _PlainCleanedScalarSet,
)
from tests._cleaned_filter_sets import (
    cleaned_specimen as _cleaned_specimen,
)
from tests._filter_key_models import (
    _DecimalKeyed,
    _DecimalKeyedHolder,
    _UuidKeyed,
    _UuidKeyedProfile,
)
from tests._idioms import ModelSerializerBase, saved_pk
from tests._postgres_fields import FakeArrayField, patch_array_field
from tests._relation_fixtures import RpCompositeChild
from tests.filters.fixtures.filtersets import (
    BranchFilter,
    BranchFilterByPath,
    BranchFilterByString,
    ShelfFilter,
)
from tests.optimizer._link_models import (
    LnkPairChild,
    LnkParent,
    LnkSlugObjectChild,
    LnkTag,
    link_fixture_tables,
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


def test_array_filter_treats_empty_list_as_value() -> None:
    """The primitive forwards the actual empty list to the exact lookup keyword.

    The recording queryset observes the Python call, not array equality. Real
    empty-array predicates live in
    ``test_postgres_array_filter_bindability_api.py::test_raw_array_forms_keep_upstream_csv_and_explicit_empty_membership``.
    """
    qs = _RecordingQs()

    f = ArrayFilter(field_name="tags", lookup_expr="exact")
    result = f.filter(qs, [])
    assert result is qs
    assert qs.captured == {"tags__exact": []}


def test_array_filter_passes_through_none() -> None:
    """Omission returns the identical queryset without invoking its query methods.

    HTTP omission rows live in
    ``test_postgres_array_filter_bindability_api.py::test_raw_array_forms_keep_upstream_csv_and_explicit_empty_membership``.
    """
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


def test_validate_range_accepts_two_values() -> None:
    assert validate_range([1, 2]) is None


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


@pytest.mark.parametrize(
    "value",
    [["NaN"], ["1", "2", "3"], "not-a-sequence"],
    ids=["short", "long", "scalar"],
)
def test_range_field_leaves_a_pair_of_the_wrong_length_to_validate_range(value: object) -> None:
    """Malformed Python values reach shape validation without per-bound cleaning.

    Generated range inputs and ordinary apply arguments normalize to a fixed pair
    or refuse earlier, so their HTTP verdicts cannot distinguish this form-field
    precedence. Native input-shape refusals live in
    ``examples/fakeshop/test_query/test_filter_apply_arguments_api.py``.
    """
    with pytest.raises(ValidationError) as excinfo:
        RangeField(bound_field=DecimalField()).clean(value)
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


_CLEANED_SCALAR_SETS = [
    pytest.param(_PackageCleanedScalarSet, id="package-filterset"),
    pytest.param(_PlainCleanedScalarSet, id="django-filter-filterset"),
]


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


class _SpecimenLabelSerializer(ModelSerializerBase[scalar_models.ScalarSpecimen]):
    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = ("label",)


class _CleanedSpecimenListView(generics.ListAPIView[scalar_models.ScalarSpecimen]):
    """A DRF list view filtering through ``DjangoFilterBackend`` with a django-filter set."""

    queryset = scalar_models.ScalarSpecimen.objects.order_by("label")
    serializer_class = _SpecimenLabelSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class: ClassVar[type[BaseFilterSet]] = _PlainCleanedScalarSet
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


def _specimen_list_view(
    filterset_class: type[django_filters.FilterSet | FilterSet],
) -> Callable[..., object]:
    """A DRF list view filtering ``ScalarSpecimen`` through ``DjangoFilterBackend``."""

    class SpecimenListView(_CleanedSpecimenListView):
        pass

    SpecimenListView.filterset_class = filterset_class
    return SpecimenListView.as_view()


def _declared_set(
    parent: type[django_filters.FilterSet | FilterSet],
    model: type[Model],
    **filters: Filter,
) -> type[BaseFilterSet]:
    """``class _DeclaredSet(parent)`` over ``model`` declaring ``filters`` and no generated one.

    Declared through ``type`` so one test body runs under either parent.
    """
    meta = type("Meta", (), {"model": model, "fields": ()})
    declared = type("_DeclaredSet", (parent,), {"__module__": __name__, "Meta": meta, **filters})
    assert issubclass(declared, BaseFilterSet)
    return declared


_RAW_FORM_LIST_ROWS = [
    pytest.param("signed_big_in=7,900", ["kept", "other"], id="comma-separated-members"),
    pytest.param("signed_big_in=7", ["kept"], id="one-member"),
    pytest.param("signed_big_in=", ["kept", "other"], id="empty-is-no-constraint"),
    pytest.param("", ["kept", "other"], id="absent-is-no-constraint"),
]


@pytest.mark.django_db
@pytest.mark.parametrize("filterset_class", _CLEANED_SCALAR_SETS)
@pytest.mark.parametrize(("query", "labels"), _RAW_FORM_LIST_ROWS)
def test_declared_list_filter_under_django_filter_backend_reads_raw_form_members(
    filterset_class: type[django_filters.FilterSet | FilterSet],
    query: str,
    labels: list[str],
) -> None:
    """A raw ``?name=`` reads as the generated ``in`` reads it, under either parent.

    ``?name=a,b`` splits on commas and an empty ``?name=`` applies no constraint
    (``_MembershipCSVWidget``), so the backend answers the rows in one query instead of a
    list-shape refusal it cannot map to a response.
    """
    _ = _cleaned_specimen("kept", kept=True)
    _ = _cleaned_specimen("other", kept=False)
    request = APIRequestFactory().get(f"/specimens/?{query}")

    with CaptureQueriesContext(db_connection) as captured:
        response = _specimen_list_view(filterset_class)(request)

    assert read_attr(response, "status_code") == 200
    assert read_attr(response, "data") == [{"label": label} for label in labels]
    assert len(captured) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("filterset_class", _CLEANED_SCALAR_SETS)
def test_declared_list_filter_under_django_filter_backend_answers_a_bad_member_with_400(
    filterset_class: type[django_filters.FilterSet | FilterSet],
) -> None:
    """A raw member the column cannot hold is the form's error, the backend's 400."""
    _ = _cleaned_specimen("kept", kept=True)
    request = APIRequestFactory().get("/specimens/?signed_big_in=7,NaN")

    with CaptureQueriesContext(db_connection) as captured:
        response = _specimen_list_view(filterset_class)(request)

    assert read_attr(response, "status_code") == 400
    assert read_attr(response, "data") == {"signed_big_in": ["Enter a number."]}
    assert len(captured) == 0


@pytest.mark.parametrize("filterset_class", _CLEANED_SCALAR_SETS)
@pytest.mark.parametrize(
    ("data", "cleaned"),
    [
        pytest.param({"signed_big_in": []}, [], id="explicit-empty-list-is-kept"),
        pytest.param({"signed_big_in": ("7",)}, [7], id="tuple-passes-through"),
        pytest.param({"signed_big_in": ["7", "900"]}, [7, 900], id="list-passes-through"),
    ],
)
def test_declared_list_filter_takes_a_list_as_sent(
    filterset_class: type[django_filters.FilterSet | FilterSet],
    data: dict[str, object],
    cleaned: list[int],
) -> None:
    """A list or tuple (the GraphQL input's shape) reaches the field as sent, ``[]`` included."""
    filterset = filterset_class(data=data, queryset=scalar_models.ScalarSpecimen.objects.none())

    assert filterset.is_valid()
    assert filterset.form.cleaned_data["signed_big_in"] == cleaned


class _LazyTextMembersSet(FilterSet):
    label_among = ListFilter(field_name="label", lookup_expr="in")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = {"label": ["in"]}


@pytest.mark.parametrize(
    "name",
    [pytest.param("label__in", id="generated-in"), pytest.param("label_among", id="list-filter")],
)
def test_lazy_translation_string_reads_as_form_text(name: str) -> None:
    """A lazy translation string sent whole splits on commas as form text does."""
    filterset = _LazyTextMembersSet(
        data={name: gettext_lazy("a,b")},
        queryset=scalar_models.ScalarSpecimen.objects.none(),
    )

    assert filterset.is_valid()
    assert filterset.form.cleaned_data[name] == ["a", "b"]


@pytest.mark.parametrize("filterset_class", _CLEANED_SCALAR_SETS)
def test_declared_list_filter_renders_its_raw_form_members_as_text(
    filterset_class: type[django_filters.FilterSet | FilterSet],
) -> None:
    """The filter form renders (DRF's browsable API renders it), members joined by commas."""
    queryset = scalar_models.ScalarSpecimen.objects.none()

    bound = str(filterset_class(data=QueryDict("signed_big_in=7,900"), queryset=queryset).form)
    unbound = str(filterset_class(queryset=queryset).form)

    assert '<input type="text" name="signed_big_in" value="7,900"' in bound
    assert '<input type="text" name="signed_big_in" id="id_signed_big_in">' in unbound


@pytest.mark.parametrize("parent", [FilterSet, django_filters.FilterSet])
def test_a_consumer_list_widget_keeps_its_class_and_cleaned_numeric_members(
    parent: type[django_filters.FilterSet | FilterSet],
) -> None:
    """The consumer's widget class and cleaned numeric members remain form observations.

    Raw repeated-key membership and scalar range/list results are covered through HTTP by
    ``examples/fakeshop/test_query/test_raw_filter_forms_api.py``. The wire cannot show the
    widget's Python class or its intermediate cleaned_data before Django prepares the query.
    """
    declared = _declared_set(
        parent,
        scalar_models.ScalarSpecimen,
        signed_big_in=ListFilter(field_name="signed_big", lookup_expr="in", widget=SelectMultiple),
    )
    filterset = declared(
        data=QueryDict("signed_big_in=7&signed_big_in=900"),
        queryset=scalar_models.ScalarSpecimen.objects.none(),
    )
    assert type(read_attr(filterset.form.fields["signed_big_in"], "widget")) is SelectMultiple
    assert filterset.is_valid()
    assert filterset.form.cleaned_data["signed_big_in"] == [7, 900]


@pytest.mark.parametrize("parent", [FilterSet, django_filters.FilterSet])
@pytest.mark.parametrize(
    ("data", "cleaned"),
    [
        pytest.param(QueryDict("priced=1.5,2"), [Decimal("1.5"), Decimal(2)], id="raw-members"),
        pytest.param(QueryDict("priced="), None, id="raw-empty-is-no-constraint"),
        pytest.param(QueryDict(""), None, id="absent-is-no-constraint"),
        pytest.param({"priced": []}, [], id="explicit-empty-list-is-kept"),
    ],
)
def test_a_driver_free_array_form_cleans_members_to_upstreams_python_values(
    monkeypatch: pytest.MonkeyPatch,
    parent: type[django_filters.FilterSet | FilterSet],
    data: QueryDict | dict[str, object],
    cleaned: list[Decimal] | None,
) -> None:
    """An ``ArrayFilter`` reads raw form data as ``ListFilter`` does: one shared form field.

    Only the cleaned Python Decimal/None values and upstream ErrorDict remain here.
    The optional-contrib classifier is replaced by its driver-free stand-in; real
    array CSV predicates and invalid-form results run over HTTP in
    ``examples/fakeshop/test_query/test_postgres_array_filter_bindability_api.py::test_raw_array_forms_keep_upstream_csv_and_explicit_empty_membership``.
    """
    patch_array_field(monkeypatch)

    class RawPricedShelf(db_models.Model):
        prices = FakeArrayField(db_models.DecimalField(max_digits=8, decimal_places=2))

        class Meta:
            managed = False
            app_label = "test_array_filter_raw_form"

    filterset_class = _declared_set(
        parent,
        RawPricedShelf,
        priced=ArrayFilter(field_name="prices", lookup_expr="contains"),
    )

    filterset = filterset_class(data=data, queryset=RawPricedShelf.objects.none())

    assert filterset.is_valid()
    assert filterset.form.cleaned_data["priced"] == cleaned
    refused = filterset_class(
        data=QueryDict("priced=1.5,NaN"),
        queryset=RawPricedShelf.objects.none(),
    )
    assert not refused.is_valid()
    assert refused.errors == {"priced": ["Enter a number."]}


_ONE_SIDED_RANGES = [
    pytest.param([5, None], {"price_span__gte": 5}, id="start-only"),
    pytest.param([None, 9], {"price_span__lte": 9}, id="end-only"),
]


@pytest.mark.parametrize(("value", "expected"), _ONE_SIDED_RANGES)
def test_range_filter_one_sided_applies_lone_bound(
    value: list[int | None],
    expected: dict[str, object],
) -> None:
    """A lone bound forwards the exact gte/lte keyword to the queryset method.

    This records the Python call. Bound rowsets live in
    ``test_scalars_filter_api.py::test_scalars_filter_price_span_one_sided_bounds``.
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
    """Two bounds retain their supplied Python list under the declared range keyword.

    Real integer and decimal predicates live in
    ``test_raw_filter_forms_api.py::test_declared_scalar_ranges_and_lists_match_the_rows_their_forms_clean``.
    """
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
    """No bound returns the identical queryset without calling filter or exclude.

    A request can show unchanged rows, not query-object identity. HTTP rows live in
    ``test_scalars_filter_api.py::test_scalars_filter_price_span_one_sided_bounds``.
    """
    qs = _RecordingQs()

    f = RangeFilter(field_name="price_span", lookup_expr="range")
    assert f.filter(qs, value) is qs
    assert qs.captured == {}


@pytest.mark.parametrize(("value", "expected"), _ONE_SIDED_RANGES)
def test_range_filter_one_sided_honours_exclude(
    value: list[int | None],
    expected: dict[str, object],
) -> None:
    """A lone bound invokes the queryset's exclude method exactly once.

    The method call is private; its real complement is served in
    ``test_scalars_filter_api.py::test_scalars_filter_not_price_span_start_only_keeps_the_complement``.
    """
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
    """The primitive invokes the queryset's distinct method once before its lone bound.

    This records invocation, not row uniqueness. Bound rowsets live in
    ``test_scalars_filter_api.py::test_scalars_filter_price_span_one_sided_bounds``.
    """
    qs = _RecordingQs()

    f = RangeFilter(field_name="price_span", lookup_expr="range", distinct=True)
    f.filter(qs, value)
    assert qs.distinct_calls == 1
    assert qs.captured == expected


def test_integer_range_filter_decomposes_range_into_gte_lte() -> None:
    """The integer primitive forwards both bounds in one gte/lte keyword mapping.

    Exact Python kwargs stay private. Real overflow-safe integer predicates live in
    ``test_scalars_api.py::test_filter_specimens_by_bigint_range_out_of_range_bound_no_overflow``.
    """
    qs = _RecordingQs()

    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range")
    result = f.filter(qs, [1, 100])
    assert result is qs
    assert qs.captured == {"signed_big__gte": 1, "signed_big__lte": 100}


def test_integer_range_filter_excludes_via_negated_conjunction() -> None:
    """The integer primitive sends both bound keywords through exclude together.

    The recording queryset captures kwargs; the actual complemented rowsets live in
    ``test_scalars_api.py::test_filter_specimens_by_bigint_range_out_of_range_bound_no_overflow``.
    """
    qs = _RecordingQs()

    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range", exclude=True)
    f.filter(qs, [1, 100])
    assert qs.captured == {"signed_big__gte": 1, "signed_big__lte": 100}
    assert qs.exclude_calls == 1


def test_integer_range_filter_passes_through_empty_value() -> None:
    """Omission preserves the exact queryset object.

    HTTP omission and malformed-pair rowsets live in
    ``test_direct_filter_primitives_api.py::test_a_direct_integer_range_primitive_keeps_upstreams_non_pair_skip``.
    """
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
    """The integer primitive invokes distinct exactly once before forwarding both bounds.

    HTTP evaluates SQL, not Python method counts. Integer rowsets live in
    ``test_scalars_api.py::test_filter_specimens_by_bigint_range_out_of_range_bound_no_overflow``.
    """
    qs = _RecordingQs()

    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range", distinct=True)
    result = f.filter(qs, [1, 100])
    assert result is qs
    assert qs.distinct_calls == 1
    assert qs.captured == {"signed_big__gte": 1, "signed_big__lte": 100}


class _TaggedSpecimen(db_models.Model):
    """A table with an array column whose ``len`` transform an integer filter compares.

    Query-build only (``managed = False``): the recording queryset never runs SQL.
    """

    tags = FakeArrayField(db_models.TextField())

    class Meta:
        managed = False
        app_label = "test_integer_transform_filters"


#: Each column an integer transform reads, with its model and the transform's name.
_INTEGER_TRANSFORMS = [
    pytest.param(scalar_models.ScalarSpecimen, "occurred_at", "year", id="datetime-year"),
    pytest.param(scalar_models.ScalarSpecimen, "occurred_at", "iso_year", id="datetime-iso-year"),
    pytest.param(scalar_models.ScalarSpecimen, "occurred_on", "year", id="date-year"),
    pytest.param(scalar_models.ScalarSpecimen, "occurred_on", "month", id="date-month"),
    pytest.param(scalar_models.ScalarSpecimen, "occurred_at", "hour", id="datetime-hour"),
    pytest.param(scalar_models.ScalarSpecimen, "occurred_at", "week_day", id="datetime-week-day"),
    pytest.param(_TaggedSpecimen, "tags", "len", id="array-len"),
]


def _bound_integer_filter(model: type[Model], filter_instance: _FilterT) -> _FilterT:
    """``filter_instance`` as its declared set binds it per request, over ``model``."""
    filterset_class = _declared_set(FilterSet, model, bound=filter_instance)
    return require_instance(filterset_class().filters["bound"], type(filter_instance))


@pytest.mark.django_db
@pytest.mark.parametrize(("model", "column", "transform"), _INTEGER_TRANSFORMS)
def test_integer_in_filter_binds_a_transform_members_uncoerced_by_the_column(
    model: type[Model],
    column: str,
    transform: str,
) -> None:
    """An integer ``in`` through a transform binds every member to the transform's output.

    The members are values of the transform's ``IntegerField`` output, never of the
    column: none is coerced through the column's field (which drops every member of a
    temporal column), and one past every integer range is kept for the filter form's bind
    ask, which refuses it over HTTP in
    ``examples/fakeshop/test_query/test_scalar_predicate_binding_api.py::test_project_integer_transform_members_bind_as_the_transform_output``.
    """
    qs = _RecordingQs()
    f = _bound_integer_filter(
        model,
        IntegerInFilter(field_name=column, lookup_expr=f"{transform}__in"),
    )

    f.filter(qs, [Decimal(3), Decimal(2**70)])
    assert qs.nothing is None
    assert qs.captured == {f"{column}__{transform}__in": [Decimal(3), Decimal(2**70)]}


@pytest.mark.django_db
@pytest.mark.parametrize(("model", "column", "transform"), _INTEGER_TRANSFORMS)
def test_integer_in_filter_drops_a_transform_fractional_member(
    model: type[Model],
    column: str,
    transform: str,
) -> None:
    """A fractional member equals no integer transform output: dropped, never truncated.

    A list whose every member is fractional matches nothing, never the empty-value skip.
    """
    qs = _RecordingQs()
    f = _bound_integer_filter(
        model,
        IntegerInFilter(field_name=column, lookup_expr=f"{transform}__in"),
    )

    f.filter(
        qs,
        [
            Decimal("2020.5"),
            Decimal(3),
            Decimal("3.0"),
            Decimal("-0.5"),
        ],
    )
    assert qs.captured == {f"{column}__{transform}__in": [Decimal(3), Decimal("3.0")]}
    nothing = _RecordingQs()
    assert f.filter(nothing, [Decimal("2020.5"), 0.9]) is nothing.nothing


@pytest.mark.django_db
@pytest.mark.parametrize(("model", "column", "transform"), _INTEGER_TRANSFORMS)
def test_integer_range_filter_applies_its_bounds_through_the_transform(
    model: type[Model],
    column: str,
    transform: str,
) -> None:
    """Both integer bound keywords retain the declared transform path.

    The Python kwargs stay private; actual transform predicates live in
    ``test_scalar_predicate_binding_api.py::test_project_transform_without_a_backend_range_keeps_its_integer_members``.
    """
    qs = _RecordingQs()
    f = _bound_integer_filter(
        model,
        IntegerRangeFilter(field_name=column, lookup_expr=f"{transform}__range"),
    )

    f.filter(qs, [1, 5])
    assert qs.captured == {f"{column}__{transform}__gte": 1, f"{column}__{transform}__lte": 5}


@pytest.mark.django_db
def test_integer_in_filter_coerces_an_integer_column_members() -> None:
    """Forwarded integer members have int type after column coercion and range dropping.

    This inspects Python kwargs. The corresponding real rowsets live in
    ``test_scalars_api.py::test_filter_specimens_by_declared_bigint_list_drops_out_of_range_members``.
    """
    qs = _RecordingQs()
    f = _bound_integer_filter(
        scalar_models.ScalarSpecimen,
        IntegerInFilter(field_name="signed_big", lookup_expr="in"),
    )

    f.filter(qs, [Decimal(3), Decimal(2**70)])
    assert qs.captured == {"signed_big__in": [3]}


@pytest.mark.django_db
def test_integer_in_filter_drops_an_integer_column_fractional_member() -> None:
    """A fractional member names no integer row: dropped, never truncated to one.

    A list whose every member is fractional matches nothing, never the empty-value skip.
    """
    qs = _RecordingQs()
    f = _bound_integer_filter(
        scalar_models.ScalarSpecimen,
        IntegerInFilter(field_name="signed_big", lookup_expr="in"),
    )

    f.filter(
        qs,
        [
            Decimal("1.5"),
            Decimal(2),
            Decimal("0.9"),
            Decimal("-1.5"),
            1.0,
        ],
    )
    assert qs.captured == {"signed_big__in": [2, 1]}
    nothing = _RecordingQs()
    assert f.filter(nothing, [Decimal("1.5"), -1.5]) is nothing.nothing


def test_list_filter_returns_qs_none_on_empty_list() -> None:
    """An empty list returns the specific queryset object created by none().

    HTTP can observe no rows, not that returned object's identity. Native membership
    rowsets live in ``test_library_api.py::test_relay_relation_empty_exact_list_matches_no_rows_over_http``.
    """
    qs = _RecordingQs()

    f = ListFilter(field_name="ids")
    assert f.filter(qs, []) is qs.nothing


def test_list_filter_defers_to_super_for_nonempty_lists() -> None:
    """The supplied Python members reach the upstream in-lookup kwargs unchanged.

    Real list predicates live in
    ``test_raw_filter_forms_api.py::test_declared_scalar_ranges_and_lists_match_the_rows_their_forms_clean``.
    """
    qs = _RecordingQs()

    f = ListFilter(field_name="ids", lookup_expr="in")
    f.filter(qs, [1, 2])
    assert qs.captured == {"ids__in": [1, 2]}


def test_list_filter_passes_through_none() -> None:
    """Omission preserves the identical queryset object through the upstream filter.

    HTTP omission rowsets live in
    ``test_raw_filter_forms_api.py::test_django_query_dict_arguments_keep_csv_emptiness_and_membership``.
    """
    sentinel = _RecordingQs()
    f = ListFilter(field_name="ids")
    assert f.filter(sentinel, None) is sentinel


class _CodedOwner(db_models.Model):
    """A row carrying a unique ``code`` beside its primary key, linked to ``_CodedTarget`` rows.

    ``targets`` runs through ``_TargetCodedLink`` (keyed to the target by its ``code``),
    ``source_coded_targets`` through ``_SourceCodedLink`` (keyed to this owner by its ``code``).
    """

    name: db_models.TextField[str | Combinable, str] = db_models.TextField()
    code: db_models.IntegerField[float | int | str | Combinable, int] = db_models.IntegerField(
        unique=True,
    )
    visible: db_models.BooleanField[bool | Combinable, bool] = db_models.BooleanField()
    targets: db_models.ManyToManyField[_CodedTarget, _TargetCodedLink] = db_models.ManyToManyField(
        "_CodedTarget",
        through="_TargetCodedLink",
        related_name="owners",
    )
    source_coded_targets: db_models.ManyToManyField[_CodedTarget, _SourceCodedLink] = (
        db_models.ManyToManyField(
            "_CodedTarget",
            through="_SourceCodedLink",
            related_name="source_coded_owners",
        )
    )

    class Meta:
        managed = False
        app_label = "library"
        db_table = "filters_coded_owner"


class _CodedTarget(db_models.Model):
    """A row carrying a unique ``code`` beside its primary key, reached by ``_CodedOwner`` rows."""

    name: db_models.TextField[str | Combinable, str] = db_models.TextField()
    code: db_models.IntegerField[float | int | str | Combinable, int] = db_models.IntegerField(
        unique=True,
    )
    visible: db_models.BooleanField[bool | Combinable, bool] = db_models.BooleanField()

    class Meta:
        managed = False
        app_label = "library"
        db_table = "filters_coded_target"


class _TargetCodedLink(db_models.Model):
    """The ``_CodedOwner.targets`` join row, keyed to the target by its ``code``."""

    owner: db_models.ForeignKey[_CodedOwner | Combinable, _CodedOwner] = db_models.ForeignKey(
        _CodedOwner,
        on_delete=db_models.CASCADE,
        related_name="+",
    )
    target: db_models.ForeignKey[_CodedTarget | Combinable, _CodedTarget] = db_models.ForeignKey(
        _CodedTarget,
        on_delete=db_models.CASCADE,
        to_field="code",
        related_name="+",
    )

    class Meta:
        managed = False
        app_label = "library"
        db_table = "filters_target_coded_link"


class _SourceCodedLink(db_models.Model):
    """The ``_CodedOwner.source_coded_targets`` join row, keyed to the owner by its ``code``."""

    owner: db_models.ForeignKey[_CodedOwner | Combinable, _CodedOwner] = db_models.ForeignKey(
        _CodedOwner,
        on_delete=db_models.CASCADE,
        to_field="code",
        related_name="+",
    )
    target: db_models.ForeignKey[_CodedTarget | Combinable, _CodedTarget] = db_models.ForeignKey(
        _CodedTarget,
        on_delete=db_models.CASCADE,
        related_name="+",
    )

    class Meta:
        managed = False
        app_label = "library"
        db_table = "filters_source_coded_link"


@pytest.mark.parametrize("lookup", ["exact", "in"])
@pytest.mark.parametrize(
    ("source", "relation"),
    [
        pytest.param(_CodedOwner, "targets", id="forward"),
        pytest.param(_CodedTarget, "source_coded_owners", id="reverse"),
    ],
)
def test_relay_through_to_field_generation_keeps_its_list_class_and_pk_marker(
    source: type[Model],
    relation: str,
    lookup: str,
) -> None:
    """Generated Relay lists carry a frozen pk marker, which no response can reveal.

    ``examples/fakeshop/test_query/test_relation_identity_columns_api.py`` owns the wire results.
    """
    target = require(source._meta.get_field(relation).related_model, is_model_class)
    source_set = type(
        "CodedSourceSet",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": source, "fields": {relation: ["exact", "in"]}})},
    )
    _ = type(
        "CodedTargetType",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": target, "fields": ("id", "name"), "interfaces": (relay.Node,)},
            ),
        },
    )
    _ = type(
        "CodedSourceType",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": source,
                    "fields": ("id", "name"),
                    "filterset_class": source_set,
                    "interfaces": (relay.Node,),
                },
            ),
        },
    )
    finalize_django_types()
    leaf = source_set.base_filters[relation if lookup == "exact" else f"{relation}__in"]
    assert isinstance(leaf, GlobalIDMultipleChoiceFilter)
    assert getattr(leaf, _GLOBALID_RELATION_PK_ATTR) is True


class _CompositeKeyed(db_models.Model):
    """A row keyed by a composite primary key, which Django names ``pk``."""

    pk = db_models.CompositePrimaryKey("left", "right")
    left: db_models.IntegerField[float | int | str | Combinable, int] = db_models.IntegerField()
    right: db_models.IntegerField[float | int | str | Combinable, int] = db_models.IntegerField()

    class Meta:
        managed = False
        app_label = "test_pk_alias_columns"


def _pk_alias_set(model: type[Model], **filters: django_filters.Filter) -> type[FilterSet]:
    """Build a ``FilterSet`` over ``model`` declaring ``filters`` and generating nothing."""
    meta = type("Meta", (), {"model": model, "fields": ()})
    return type(f"{model.__name__}PkAliasSet", (FilterSet,), {"Meta": meta, **filters})


def _declared_leaf_field(model: type[Model], field_name: str) -> ModelField | None:
    """Resolve a declared ``ListFilter`` over ``field_name`` on a ``FilterSet`` over ``model``."""
    filterset = _pk_alias_set(model, leaf=ListFilter(field_name=field_name, lookup_expr="in"))
    return _filterset_model_field(filterset, filterset.base_filters["leaf"])


@pytest.mark.parametrize(
    (
        "model",
        "field_name",
        "owner",
        "column",
    ),
    [
        pytest.param(models.Shelf, "pk", models.Shelf, "id", id="integer-pk"),
        pytest.param(models.Shelf, "branch__pk", models.Branch, "id", id="relation-pk"),
        pytest.param(models.LendingDesk, "pk", models.Venue, "id", id="mti-child-pk"),
        pytest.param(models.SelfServeDesk, "pk", models.Venue, "id", id="mti-grandchild-pk"),
        pytest.param(models.PatronProfile, "pk", models.Patron, "id", id="one-to-one-pk"),
        pytest.param(models.KioskFault, "kiosk__pk", models.Venue, "id", id="relation-mti-pk"),
        pytest.param(models.Annotation, "profile__pk", models.Patron, "id", id="relation-o2o-pk"),
        pytest.param(models.PatronProfile, "pk__name", models.Patron, "name", id="mid-path-pk"),
        pytest.param(
            models.KioskFault,
            "kiosk__pk__name",
            models.Venue,
            "name",
            id="mid-path-relation-pk",
        ),
        pytest.param(models.Edition, "pk", models.Edition, "isbn_13", id="text-pk"),
        pytest.param(_DecimalKeyed, "pk", _DecimalKeyed, "code", id="decimal-pk"),
        pytest.param(_DecimalKeyedHolder, "owner__pk", _DecimalKeyed, "code", id="decimal-rel-pk"),
        pytest.param(_UuidKeyed, "pk", _UuidKeyed, "code", id="uuid-pk"),
        pytest.param(_UuidKeyedProfile, "pk", _UuidKeyed, "code", id="uuid-one-to-one-pk"),
        pytest.param(_CompositeKeyed, "pk", _CompositeKeyed, "pk", id="composite-pk"),
        pytest.param(models.LendingDesk, "venue_ptr", models.LendingDesk, "venue_ptr", id="link"),
        pytest.param(models.PatronProfile, "patron", models.PatronProfile, "patron", id="key"),
    ],
)
def test_filterset_model_field_reads_pk_as_the_column_its_key_stores(
    model: type[Model],
    field_name: str,
    owner: type[Model],
    column: str,
) -> None:
    """A path ending on ``pk`` answers the column the key stores; a named relation stays itself.

    Django's ``pk`` alias resolves at any segment, and a relation-valued key (a
    multi-table-inheritance parent link, at one or two levels, or a one-to-one primary
    key) is followed to the column it stores, so every consumer types, cleans and
    range-checks ``pk`` as that column. A composite primary key is itself. A relation
    named by its own name (``venue_ptr``, ``patron``) is the relation.
    """
    assert _declared_leaf_field(model, field_name) is owner._meta.get_field(column)


@pytest.mark.parametrize(
    "field_name",
    [
        "pk__nope",
        "nope",
        "branch__nope",
        "code__pk",
    ],
)
def test_filterset_model_field_is_none_for_a_path_naming_no_field(field_name: str) -> None:
    """A path naming no field, ``pk`` alias included, is ``None``."""
    assert _declared_leaf_field(models.Shelf, field_name) is None


def _declared_leaf_value_field(field_name: str, lookup_expr: str = "in") -> ModelField | None:
    """Answer the value field of a declared ``ListFilter`` over a scalar specimen path."""
    filterset = _pk_alias_set(
        scalar_models.ScalarSpecimen,
        leaf=ListFilter(field_name=field_name, lookup_expr=lookup_expr),
    )
    return _filterset_value_field(filterset, filterset.base_filters["leaf"])


@pytest.mark.parametrize(
    ("field_name", "lookup_expr", "output"),
    [
        pytest.param("occurred_on__year", "in", db_models.IntegerField, id="path-year"),
        pytest.param("occurred_at__iso_year", "in", db_models.IntegerField, id="path-iso-year"),
        pytest.param("occurred_at", "year", db_models.IntegerField, id="lookup-year"),
        pytest.param("occurred_at", "year__gt", db_models.IntegerField, id="lookup-year-gt"),
        pytest.param("occurred_at", "date", db_models.DateField, id="lookup-date"),
        pytest.param("occurred_at__date", "gte", db_models.DateField, id="path-date"),
    ],
)
def test_filterset_value_field_reads_the_transforms_ahead_of_the_lookup(
    field_name: str,
    lookup_expr: str,
    output: type[db_models.Field[object, object]],
) -> None:
    """A transform in the path or the ``lookup_expr`` answers its output field, not the column."""
    value_field = _declared_leaf_value_field(field_name, lookup_expr)

    assert type(value_field) is output
    assert value_field is not scalar_models.ScalarSpecimen._meta.get_field("occurred_at")


@pytest.mark.parametrize(
    "lookup_expr",
    [
        "exact",
        "in",
        "isnull",
        "icontains",
        "gte",
    ],
)
def test_filterset_value_field_answers_the_column_for_a_lookup_applied_to_it(
    lookup_expr: str,
) -> None:
    """A lookup applied to the column itself, a text pattern included, answers the column."""
    assert _declared_leaf_value_field("occurred_at", lookup_expr) is (
        scalar_models.ScalarSpecimen._meta.get_field("occurred_at")
    )


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("nope__year", id="no-such-field"),
        pytest.param("par__occurred_at", id="queryset-alias"),
        pytest.param("occurred_on__nope", id="no-such-transform"),
        pytest.param("tag__year", id="relation-end"),
    ],
)
def test_filterset_value_field_is_none_where_django_reads_no_transform(field_name: str) -> None:
    """A path Django refuses, or whose remainder is no transform of its column, answers ``None``.

    A ``FilteredRelation`` alias exists only on the queryset a filter runs on, and a
    relation takes its own lookups, never a column transform.
    """
    assert _declared_leaf_value_field(field_name) is None


def test_filterset_value_field_is_none_without_a_filterset() -> None:
    """No filterset has no model to walk."""
    assert _filterset_value_field(None, ListFilter(field_name="occurred_on__year")) is None


@isolate_apps("apps.library")
def test_filterset_model_field_keeps_django_filters_answer_on_a_path_the_walk_refuses() -> None:
    """A path the package walk refuses keeps django-filter's answer for it.

    A forward ``GenericForeignKey`` is the field itself (the input converter then refuses
    it at build), and a relation still an unresolved lazy string is django-filter's
    ``RuntimeError`` naming the app registry, never ``None``.
    """

    class _Tag(db_models.Model):
        content_type: db_models.ForeignKey[ContentType | Combinable, ContentType] = (
            db_models.ForeignKey(ContentType, on_delete=db_models.CASCADE, related_name="+")
        )
        object_id: db_models.IntegerField[float | int | str | Combinable, int] = (
            db_models.IntegerField()
        )
        content_object: GenericForeignKey = GenericForeignKey("content_type", "object_id")
        unresolved: db_models.ForeignKey[Model | Combinable, Model] = db_models.ForeignKey(
            "unregistered.NoSuchModel",
            on_delete=db_models.CASCADE,
            related_name="+",
        )

        class Meta:
            app_label = "library"

    assert _declared_leaf_field(_Tag, "content_object") is _Tag._meta.get_field("content_object")
    with pytest.raises(RuntimeError, match="apps registry not populated"):
        _ = _declared_leaf_field(_Tag, "unresolved")


def test_declared_pk_leaf_over_a_composite_primary_key_is_refused_at_build() -> None:
    """A declared leaf over a composite primary key named ``pk`` is the unsupported-field error."""
    filterset = _pk_alias_set(_CompositeKeyed, leaf=ListFilter(field_name="pk", lookup_expr="in"))
    bound_leaf = filterset.base_filters["leaf"]
    model_field = _filterset_model_field(filterset, bound_leaf)

    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        _ = convert_filter_to_input_annotation(bound_leaf, model_field, None, filterset)


@pytest.mark.parametrize(
    ("model", "leaf"),
    [
        pytest.param(
            models.PatronProfile,
            RangeFilter(field_name="patron", lookup_expr="range"),
            id="one-to-one-key-range",
        ),
        pytest.param(
            models.LendingDesk,
            ListFilter(field_name="venue_ptr", lookup_expr="in"),
            id="parent-link-list",
        ),
        pytest.param(
            models.KioskFault,
            RangeFilter(field_name="kiosk", lookup_expr="range"),
            id="key-into-parent-link-range",
        ),
    ],
)
def test_declared_range_or_list_naming_a_relation_valued_key_by_name_is_refused_at_build(
    model: type[Model],
    leaf: django_filters.Filter,
) -> None:
    """A declared range or list naming a relation itself stays the build-time refusal.

    Only a path ending on ``pk`` reads the column a key stores; ``patron``, ``venue_ptr``
    and ``kiosk`` name the relation, which no input scalar types.
    """
    filterset = _pk_alias_set(model, leaf=leaf)
    bound_leaf = filterset.base_filters["leaf"]
    model_field = _filterset_model_field(filterset, bound_leaf)

    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        _ = convert_filter_to_input_annotation(bound_leaf, model_field, None, filterset)


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
def test_a_driver_free_array_member_keeps_upstreams_error_dict(
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    lookup_expr: str,
) -> None:
    """The driver-free column classifier retains upstream plain-form errors.

    Optional ArrayField classification and scalar-column fallback can be asked
    without a PostgreSQL driver. The observable typed refusal of a real array
    element is owned by
    ``examples/fakeshop/test_query/test_postgres_array_filter_bindability_api.py::test_numeric_array_members_check_the_real_binding_type_and_keep_non_element_parameters``.
    """
    patch_array_field(monkeypatch)

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

    class PlainPricedShelfFilter(django_filters.FilterSet):
        priced = ArrayFilter(field_name=field_name, lookup_expr=lookup_expr)

        class Meta:
            model = PricedShelf
            fields = ("price",)

    data = {"priced": ["1.5", "NaN"]}
    plain = PlainPricedShelfFilter(data=data, queryset=PricedShelf.objects.none())
    assert not plain.is_valid()
    assert plain.errors == {"priced": ["Enter a number."]}


def test_global_id_filter_decodes_via_strawberry_relay() -> None:
    """An unbound primitive forwards the decoded Python text key to the exact keyword.

    The returned Python type stays private. Native unbound acceptance lives in
    ``test_library_api.py::test_an_unwired_filter_subclass_answers_like_an_unrelated_unwired_set_over_http``.
    """
    qs = _RecordingQs()

    encoded = relay.to_base64("BookType", "42")
    f = GlobalIDFilter(field_name="id", lookup_expr="exact")
    f.filter(qs, encoded)
    assert qs.captured == {"id__exact": "42"}


def test_global_id_filter_passes_through_none() -> None:
    """Omission preserves the exact queryset and invokes no predicate method.

    Actual generated GlobalID predicates live in
    ``test_library_api.py::test_library_books_filter_by_relay_m2m_global_id``.
    """
    qs = _RecordingQs()

    f = GlobalIDFilter(field_name="id", lookup_expr="exact")
    # `None` falls through to `Filter.filter`, which short-circuits on EMPTY_VALUES.
    result = f.filter(qs, None)
    assert qs.captured == {}
    assert result is qs


def test_global_id_multiple_choice_filter_decodes_every_element(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unbound per-element filter passes decoded Python str keys to its upstream method.

    The spy observes the Python list and element types; native accepted list rowsets live in
    ``test_library_api.py::test_library_genres_filter_by_relay_own_pk_global_id_in_list``.
    """
    captured: list[list[str]] = []

    def spy(_self: object, qs: object, value: Iterable[str]) -> object:
        captured.append(list(value))
        return qs

    encoded_one = relay.to_base64("BookType", "1")
    encoded_two = relay.to_base64("BookType", "2")
    # Spy on the upstream ``MultipleChoiceFilter.filter`` via the bound
    # parent class. ``monkeypatch`` auto-restores on teardown (xdist-safe
    # and exception-safe), where a manual try/finally would write through
    # to the upstream class.
    monkeypatch.setattr(GlobalIDMultipleChoiceFilter.__mro__[1], "filter", spy)
    f = GlobalIDMultipleChoiceFilter(field_name="id")
    f.filter(_RecordingQs(), [encoded_one, encoded_two])
    assert captured == [["1", "2"]]


def test_global_id_multiple_choice_filter_passes_through_none() -> None:
    """Omission preserves the exact queryset without forwarding a predicate.

    Real list predicates live in
    ``test_library_api.py::test_library_genres_filter_by_relay_own_pk_global_id_in_list``.
    """
    qs = _RecordingQs()

    f = GlobalIDMultipleChoiceFilter(field_name="id")
    result = f.filter(qs, None)
    assert qs.captured == {}
    assert result is qs


@pytest.mark.parametrize(
    "value",
    [iter(["not-a-global-id"]), object()],
    ids=["iterator", "opaque-object"],
)
def test_globalid_list_primitive_refuses_python_only_containers(value: object) -> None:
    """Python iterators and opaque objects cannot be posted as native JSON containers.

    Native scalar/string refusal belongs to
    ``examples/fakeshop/test_query/test_direct_filter_primitives_api.py::test_direct_public_membership_primitives_refuse_scalar_containers``.
    """
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


def test_membership_wrapper_keeps_the_upstream_name_and_builds_a_fresh_class() -> None:
    """Exact dynamic Python class identity, name and MRO stay construction observations.

    Direct scalar rejection and admitted membership run through native HTTP at
    ``examples/fakeshop/test_query/test_direct_filter_primitives_api.py::test_direct_public_membership_primitives_refuse_scalar_containers``.
    """
    wrapped = membership_in_filter_class(_CharInFilter)
    assert wrapped is not membership_in_filter_class(_CharInFilter)
    assert wrapped.__name__ == "_CharInFilter"
    assert wrapped.__mro__[1:3] == (MembershipInFilter, _CharInFilter)


def test_an_empty_globalid_membership_returns_the_querysets_none_object() -> None:
    """An empty GlobalID list returns the queryset object created by none().

    HTTP observes empty rows, not object identity. Actual empty relation predicates live in
    ``test_library_api.py::test_relay_relation_empty_exact_list_matches_no_rows_over_http``.
    """
    qs = _RecordingQs()
    global_ids = GlobalIDMultipleChoiceFilter(field_name="id", lookup_expr="in")
    assert global_ids.filter(qs, []) is qs.nothing


@pytest.mark.parametrize(
    "excluding",
    [
        lambda: ListFilter(field_name="code", exclude=True),
        lambda: GlobalIDMultipleChoiceFilter(field_name="id", lookup_expr="in", exclude=True),
        lambda: GlobalIDMultipleChoiceFilter(field_name="id", lookup_expr="exact", exclude=True),
    ],
    ids=["list-filter", "global-id-in", "global-id-exact"],
)
def test_excluded_empty_membership_clones_the_exact_input_queryset(
    excluding: Callable[[], Filter],
) -> None:
    """The clone is distinct by Python identity, which the branch applicator uses for activity.

    The match-all rowset and logical complements belong to the real HTTP consumer at
    ``examples/fakeshop/test_query/test_filter_logic_customization_api.py::test_an_authored_excluded_empty_membership_is_a_real_match_all_constraint``.
    """
    queryset = models.Shelf.objects.none()
    assert object_result(excluding().filter, queryset, []) is not queryset


def test_global_id_multiple_choice_filter_well_formed_list_still_applies_predicate() -> None:
    """The whole decoded Python list is forwarded under one in-lookup keyword.

    The precise kwargs stay private. Real accepted memberships live in
    ``test_library_api.py::test_library_genres_filter_by_relay_own_pk_global_id_in_list``.
    """
    qs = _RecordingQs()
    f = GlobalIDMultipleChoiceFilter(field_name="genres", lookup_expr="in")
    encoded = [relay.to_base64("GenreType", "5"), relay.to_base64("GenreType", "9")]
    f.filter(qs, encoded)
    assert qs.captured == {"genres__in": ["5", "9"]}


def test_bound_field_name_reads_the_path_the_filterset_binds() -> None:
    """A declared filter with no ``field_name`` is bound to its attribute name."""

    class BookFilterSet(FilterSet):
        title = Filter(lookup_expr="icontains")

        class Meta:
            model = models.Book
            fields = ["id"]

    assert _bound_field_name(BookFilterSet.base_filters["title"]) == "title"


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

    Path resolution is the package's path classifier, which refuses an unknown hop;
    django-filter's ``get_model_field`` answers that refused path with ``None``.
    """
    f = GlobalIDFilter(field_name="nonexistent_field")
    assert _filterset_model_field(ShelfFilter, f) is None


def test_filterset_model_field_walks_related_path() -> None:
    """A ``__``-separated ``field_name`` resolves to the terminal model field."""
    f = GlobalIDFilter(field_name="branch__name")
    assert _filterset_model_field(ShelfFilter, f) is models.Branch._meta.get_field("name")


def test_global_id_filter_fk_to_pk_predicate_is_byte_identical() -> None:
    """An unmarked primitive forwards its stored text key without adding a pk segment.

    Exact kwargs and marker absence stay private. Real target-key comparisons live in
    ``test_library_api.py::test_global_id_filter_over_a_non_pk_to_field_compares_the_target_key_over_http``.
    """
    qs = _RecordingQs()

    encoded = relay.to_base64("ShelfType", "7")
    f = GlobalIDFilter(field_name="shelf", lookup_expr="exact")
    assert getattr(f, _GLOBALID_RELATION_PK_ATTR, False) is not True
    f.filter(qs, encoded)
    assert qs.captured == {"shelf__exact": "7"}


def test_global_id_multiple_choice_filter_in_predicate_is_byte_identical() -> None:
    """An unmarked primitive forwards its decoded text list under the unchanged in keyword.

    Exact kwargs and marker absence stay private. Actual GlobalID memberships live in
    ``test_library_api.py::test_library_genres_filter_by_relay_own_pk_global_id_in_list``.
    """
    qs = _RecordingQs()

    encoded = [relay.to_base64("GenreType", "1"), relay.to_base64("GenreType", "2")]
    f = GlobalIDMultipleChoiceFilter(field_name="genres", lookup_expr="in")
    assert getattr(f, _GLOBALID_RELATION_PK_ATTR, False) is not True
    # ``MultipleChoiceFilter`` defaults ``distinct=True``; the stub must accept it.
    f.filter(qs, encoded)
    assert qs.captured == {"genres__in": ["1", "2"]}


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
    """The explicit-queryset ledger preserves the consumer's exact queryset object.

    HTTP serializes rows and cannot expose this identity. Native explicit-queryset
    behavior lives in
    ``test_library_api.py::test_library_branches_filter_respects_related_queryset_boundary_on_parent``.
    """
    explicit_qs = models.Shelf.objects.filter(code="topic-A")
    f = RelatedFilter(ShelfFilter, queryset=explicit_qs)
    # Constructor records the explicit-queryset ledger entry.
    assert f._has_explicit_queryset is True
    assert f.get_queryset(request=None) is explicit_qs


def test_related_filter_explicit_queryset_ledger_defaults_false_when_absent() -> None:
    f = RelatedFilter("ShelfFilter")
    assert f._has_explicit_queryset is False


def test_related_filter_rejects_lookups_kwarg() -> None:
    """`lookups=` is refused with `TypeError` naming where lookups are declared.

    A related branch exposes the target filter set's own lookups, so nothing
    reads the kwarg; django-filter would otherwise absorb it into `extra`
    and ignore it.
    """
    with pytest.raises(TypeError) as exc_info:
        RelatedFilter("ShelfFilter", lookups=["exact", "in"])
    assert str(exc_info.value) == (
        "`RelatedFilter` does not accept `lookups=`; declare the lookups on the "
        "target FilterSet's `Meta.fields`."
    )


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


def test_array_filter_method_call_passes_through_none() -> None:
    """Omission preserves the exact queryset without calling the array callback.

    Exact object identity is private. Real array rowsets live in
    ``test_postgres_array_filter_bindability_api.py::test_raw_array_forms_keep_upstream_csv_and_explicit_empty_membership``.
    """

    def custom(_qs: object, name: str, value: object) -> tuple[str, str, object]:
        return ("custom", name, value)

    sentinel = _RecordingQs()
    f = ArrayFilter(field_name="tags", method=custom)
    assert isinstance(f.filter, ArrayFilterMethod)
    assert f.filter(sentinel, None) is sentinel


def test_array_filter_method_call_dispatches_to_custom_method() -> None:
    """The array dispatcher passes the same field name and Python value to its callback.

    This callback returns an argument-recording tuple, not a supported QuerySet
    result. Real array predicates live in
    ``test_postgres_array_filter_bindability_api.py::test_raw_array_forms_keep_upstream_csv_and_explicit_empty_membership``.
    """

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
    """Omission preserves the exact queryset without calling the list callback.

    Exact object identity is private. Native list rowsets live in
    ``test_raw_filter_forms_api.py::test_declared_scalar_ranges_and_lists_match_the_rows_their_forms_clean``.
    """

    def custom(_qs: object, name: str, value: object) -> tuple[str, str, object]:
        return ("custom", name, value)

    sentinel = _RecordingQs()
    f = ListFilter(field_name="ids", method=custom)
    assert f.filter(sentinel, None) is sentinel


def test_list_filter_method_call_dispatches_to_custom_method() -> None:
    """The list dispatcher passes the same field name and Python value to its callback.

    This callback returns an argument-recording tuple, not a supported QuerySet
    result. Native list rowsets live in
    ``test_raw_filter_forms_api.py::test_declared_scalar_ranges_and_lists_match_the_rows_their_forms_clean``.
    """

    def custom(_qs: object, name: str, value: object) -> tuple[str, str, object]:
        return ("custom", name, value)

    f = ListFilter(field_name="ids", method=custom)
    assert f.filter(_RecordingQs(), [1, 2]) == ("custom", "ids", [1, 2])


def test_array_filter_applies_distinct_when_flagged() -> None:
    """The array primitive invokes distinct exactly once before forwarding the value.

    Python method counts stay private; actual array predicates live in
    ``test_postgres_array_filter_bindability_api.py::test_raw_array_forms_keep_upstream_csv_and_explicit_empty_membership``.
    """
    qs = _RecordingQs()

    f = ArrayFilter(field_name="tags", lookup_expr="exact", distinct=True)
    result = f.filter(qs, [1])
    assert result is qs
    assert qs.distinct_calls == 1
    assert qs.captured == {"tags__exact": [1]}


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


def _bound(
    filter_: _FilterT,
    owner: DjangoTypeDefinition | None,
    *,
    model: type[Model] = models.Book,
) -> _FilterT:
    """Return ``filter_`` as a real ``FilterSet`` instance binds it, its class owned by ``owner``.

    Instantiating the filterset hands each declared filter a copy whose ``parent`` is the
    instance, the slot the GlobalID target resolution reads the owner through; ``None``
    leaves the filterset unbound. The filterset filters ``model`` (``Book`` by default).
    """
    filtered_model = model

    class OwnerFilter(FilterSet):
        bound = filter_

        class Meta:
            model = filtered_model
            fields = ()

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

    Runtime decoding rejects these states before consulting this metadata
    helper. The refusal verdicts have separate live and runtime-backstop coverage;
    this test observes only the metadata helper's Python return value.
    """
    owner = _owner(strategy)
    assert _accepted_globalid_type_names(owner) is None


def test_globalid_decoder_returns_the_targets_integer_python_key() -> None:
    """Only the decoded Python type stays private; HTTP cannot distinguish str from int PKs."""

    class BookIdentityFilter(FilterSet):
        chosen = GlobalIDFilter(field_name="id")

        class Meta:
            model = models.Book
            fields = ()

    class BookIdentityNode(DjangoType):
        class Meta:
            model = models.Book
            fields = ("id",)
            interfaces = (relay.Node,)
            globalid_strategy = "model"
            filterset_class = BookIdentityFilter

    finalize_django_types()
    bound = BookIdentityFilter(queryset=models.Book.objects.all())
    filter_ = require_instance(bound.filters["chosen"], GlobalIDFilter)
    key = _decode_and_validate_global_id(
        global_id_for(BookIdentityNode, 42),
        filter_,
        alias=DEFAULT_DB_ALIAS,
    )

    assert type(key) is int


def test_filter_model_strategy_reads_the_model_name_case_insensitively() -> None:
    """The slot names the target as decode reads it: model name any case, app label exact."""
    owner = _owner("model")
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("library.BOOK", "42")
    assert _decode_and_validate_global_id(encoded, f, alias=DEFAULT_DB_ALIAS) == 42
    with pytest.raises(GraphQLError, match="GlobalID type mismatch"):
        _decode_and_validate_global_id(
            relay.to_base64("Library.book", "42"),
            f,
            alias=DEFAULT_DB_ALIAS,
        )


@pytest.mark.parametrize("strategy", ["callable", "custom"])
def test_filter_encode_only_strategy_rejects_fail_closed(strategy: str) -> None:
    """A privately installed encode-only strategy retains its runtime decoder refusal.

    Rungs 1-3 cannot serve this deliberately incomplete lifecycle state: finalization
    rejects bound callable/custom GlobalID tables before constructing any schema.
    ``test_finalizer.py::test_phase_2_5_rejects_globalid_filter_on_callable_strategy_target``
    and its custom-strategy sibling pin that public configuration refusal. The
    known-None non-Relay target is different and has a live runtime owner in
    ``test_globalid_filter_strategies_api.py::test_a_nonrelay_target_refuses_a_globalid_with_a_typed_error``.
    """
    owner = _owner(strategy)
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("AnythingAtAll", "99")
    with pytest.raises(GraphQLError, match="encode-only") as exc_info:
        _decode_and_validate_global_id(encoded, f, alias=DEFAULT_DB_ALIAS)
    assert exc_info.value.extensions == {"code": "GLOBALID_UNVALIDATABLE"}
    assert strategy in str(exc_info.value)


def test_multi_value_filter_encode_only_reject_names_index() -> None:
    """The private encode-only lifecycle backstop retains its offending Python list index.

    Rungs 1-3 cannot publish this manually installed binding: finalization refuses
    bound encode-only GlobalID tables. Ordinary finalized list refusals live in
    ``test_library_api.py::test_library_genres_filter_malformed_own_pk_global_id_in_names_index``.
    """
    owner = _owner("callable")
    f = _bound(GlobalIDMultipleChoiceFilter(field_name="id"), owner)
    with pytest.raises(GraphQLError, match="at index 0") as exc_info:
        f.filter(_RecordingQs(), [relay.to_base64("AnythingAtAll", "99")])
    assert exc_info.value.extensions == {"code": "GLOBALID_UNVALIDATABLE"}


def test_filter_unbound_owner_node_id_only() -> None:
    """No bound owner -> node-id-only fallback (the existing `None`-definition path).

    The ``type_name`` guard is skipped; a filter on a FilterSet model still coerces the
    node id through the column its path names, and a filter no FilterSet holds has no
    column and passes the decoded node id through.
    """
    f = _bound(GlobalIDFilter(field_name="id"), None)
    encoded = relay.to_base64("WhateverType", "5")
    assert _decode_and_validate_global_id(encoded, f, alias=DEFAULT_DB_ALIAS) == 5
    loose = GlobalIDFilter(field_name="id")
    assert _decode_and_validate_global_id(encoded, loose, alias=DEFAULT_DB_ALIAS) == "5"


def _unresolved_relation_owner(kind: str) -> DjangoTypeDefinition | None:
    """The owner of a filterset whose relation target no ``DjangoType`` resolves.

    ``"unbound"`` leaves the filterset with no owner; ``"bound"`` owns it by a ``Book``
    definition, whose ``shelf`` / ``genres`` targets nothing registers.
    """
    return None if kind == "unbound" else _owner()


@pytest.mark.django_db
@pytest.mark.parametrize("owner_kind", ["unbound", "bound"])
@pytest.mark.parametrize(
    (
        "filter_class",
        "relation",
        "lookup",
        "wrap",
    ),
    [
        pytest.param(GlobalIDFilter, "shelf", "exact", False, id="fk-exact"),
        pytest.param(GlobalIDMultipleChoiceFilter, "shelf", "in", True, id="fk-in"),
        pytest.param(GlobalIDFilter, "genres", "exact", False, id="m2m-exact"),
        pytest.param(GlobalIDMultipleChoiceFilter, "genres", "in", True, id="m2m-in"),
    ],
)
def test_unresolved_relation_target_coerces_the_node_id_through_its_primary_key(
    *,
    owner_kind: str,
    filter_class: type[GlobalIDFilter | GlobalIDMultipleChoiceFilter],
    relation: str,
    lookup: str,
    wrap: bool,
) -> None:
    """A relation filter no target type resolves still coerces its node id through the target pk.

    A consumer-declared GlobalID filter on a relation into an unregistered model skips the
    ``type_name`` guard (no type to validate against), but the relation names the target
    primary key the node id is compared on: an id that key cannot hold answers
    ``GLOBALID_INVALID`` rather than Django's raw ``ValueError``, and a coercible one
    filters, matching the row it names and nothing for a key no row holds.
    """
    branch = models.Branch.objects.create(name="UnresolvedBranch", city="Boston")
    shelf = models.Shelf.objects.create(code="UR-1", branch=branch)
    other = models.Shelf.objects.create(code="UR-2", branch=branch)
    genre = models.Genre.objects.create(name="UnresolvedGenre")
    kept = models.Book.objects.create(title="Kept", shelf=shelf)
    _ = models.Book.objects.create(title="Other", shelf=other)
    kept.genres.add(genre)
    target_pk = saved_pk(shelf if relation == "shelf" else genre)
    f = _bound(
        filter_class(field_name=relation, lookup_expr=lookup),
        _unresolved_relation_owner(owner_kind),
    )
    assert _globalid_target(f) is None
    books = models.Book.objects.order_by("pk")

    def apply(*node_ids: str) -> list[str]:
        encoded = [relay.to_base64("Unregistered", node_id) for node_id in node_ids]
        value = encoded if wrap else encoded[0]
        return list(f.filter(books, value).values_list("title", flat=True))

    assert apply(str(target_pk)) == ["Kept"]
    assert apply("987654321") == []
    with pytest.raises(GraphQLError, match=r"not a valid (Shelf|Genre) key value") as exc_info:
        apply("abc")
    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}
    if wrap:
        with pytest.raises(GraphQLError, match="at index 1") as exc_info:
            apply(str(target_pk), "abc")
        assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "owner_kind",
        "filter_class",
        "path",
        "lookup",
        "wrap",
    ),
    [
        pytest.param("unbound", GlobalIDFilter, "id", "exact", False, id="own-id-exact-unbound"),
        pytest.param(
            "unbound",
            GlobalIDMultipleChoiceFilter,
            "id",
            "in",
            True,
            id="own-id-in-unbound",
        ),
        pytest.param(
            "unbound",
            GlobalIDFilter,
            "shelf__id",
            "exact",
            False,
            id="fk-id-exact-unbound",
        ),
        pytest.param("bound", GlobalIDFilter, "shelf__id", "exact", False, id="fk-id-exact-bound"),
        pytest.param(
            "unbound",
            GlobalIDMultipleChoiceFilter,
            "shelf__id",
            "in",
            True,
            id="fk-id-in-unbound",
        ),
        pytest.param(
            "bound",
            GlobalIDMultipleChoiceFilter,
            "shelf__id",
            "in",
            True,
            id="fk-id-in-bound",
        ),
    ],
)
def test_unresolved_target_scalar_column_coerces_the_node_id_through_it(
    *,
    owner_kind: str,
    filter_class: type[GlobalIDFilter | GlobalIDMultipleChoiceFilter],
    path: str,
    lookup: str,
    wrap: bool,
) -> None:
    """A scalar-column filter no target type resolves coerces its node id through that column.

    The own ``id`` under an unbound owner (a bound one resolves its own id), and a
    declared ``shelf__id`` whose target no type registers, skip the ``type_name`` guard
    but still compare the node id on a column: an id it cannot hold answers ``GLOBALID_INVALID`` rather than
    Django's raw ``ValueError``, and a coercible one filters.
    """
    branch = models.Branch.objects.create(name="ScalarBranch", city="Boston")
    shelf = models.Shelf.objects.create(code="SC-1", branch=branch)
    other = models.Shelf.objects.create(code="SC-2", branch=branch)
    kept = models.Book.objects.create(title="Kept", shelf=shelf)
    _ = models.Book.objects.create(title="Other", shelf=other)
    target_pk = saved_pk(kept if path == "id" else shelf)
    f = _bound(
        filter_class(field_name=path, lookup_expr=lookup),
        _unresolved_relation_owner(owner_kind),
    )
    assert _globalid_target(f) is None
    books = models.Book.objects.order_by("pk")

    def apply(*node_ids: str) -> list[str]:
        encoded = [relay.to_base64("Unregistered", node_id) for node_id in node_ids]
        value = encoded if wrap else encoded[0]
        return list(f.filter(books, value).values_list("title", flat=True))

    assert apply(str(target_pk)) == ["Kept"]
    assert apply("987654321") == []
    with pytest.raises(GraphQLError, match=r"not a valid (Book|Shelf) key value") as exc_info:
        apply("abc")
    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}
    if wrap:
        with pytest.raises(GraphQLError, match="at index 1") as exc_info:
            apply(str(target_pk), "abc")
        assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


_MULTI_COLUMN_LINKS = [
    pytest.param(RpCompositeChild, "parent", id="composite-pk"),
    pytest.param(LnkPairChild, "parent", id="two-column-fo"),
    pytest.param(models.ShelfLabel, "shelf", id="fakeshop-two-column-fo"),
]


@pytest.mark.parametrize("owner_kind", ["unbound", "bound"])
@pytest.mark.parametrize(("model", "relation"), _MULTI_COLUMN_LINKS)
@pytest.mark.parametrize(
    ("filter_class", "lookup", "wrap"),
    [
        pytest.param(GlobalIDFilter, "exact", False, id="exact"),
        pytest.param(GlobalIDMultipleChoiceFilter, "in", True, id="in"),
    ],
)
def test_unresolved_multi_column_link_refuses_every_node_id(
    *,
    owner_kind: str,
    model: type[Model],
    relation: str,
    filter_class: type[GlobalIDFilter | GlobalIDMultipleChoiceFilter],
    lookup: str,
    wrap: bool,
) -> None:
    """A relation linked by more than one column, whose target no type resolves, refuses every id.

    Django compares the relation on every column of its last join (a composite primary
    key's members, or a two-column ``ForeignObject``'s targets), so no single node id can
    name a row: the id answers ``GLOBALID_INVALID`` before Django's own refusal of a
    scalar compared with a multi-column link ("must have 2 elements").
    """
    owner = None if owner_kind == "unbound" else _definition(model, "LinkOwnerType")
    f = _bound(filter_class(field_name=relation, lookup_expr=lookup), owner, model=model)
    assert _globalid_target(f) is None
    encoded = relay.to_base64("Unregistered", "1")
    with pytest.raises(GraphQLError, match="is linked by 2 columns") as exc_info:
        _ = f.filter(model._default_manager.all(), [encoded] if wrap else encoded)
    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


@pytest.mark.parametrize(("model", "relation"), _MULTI_COLUMN_LINKS)
def test_raw_key_on_a_multi_column_link_identifies_no_row(
    *,
    model: type[Model],
    relation: str,
) -> None:
    """A declared raw-key leaf on a multi-column link coerces every value to no row.

    No single value can name a row across every link column, so the leaf matches
    nothing (``_coerce_relation_identity``) rather than handing Django a scalar it
    refuses for the multi-column link.
    """
    f = _bound(RelationPkFilter(field_name=relation, lookup_expr="exact"), None, model=model)
    assert _coerce_relation_identity(f, "1", DEFAULT_DB_ALIAS) is None


@pytest.mark.parametrize(("model", "relation"), _MULTI_COLUMN_LINKS)
@pytest.mark.parametrize("filter_class", [RelationPkFilter, RelationPkMultipleFilter])
def test_raw_key_input_on_a_multi_column_link_is_refused_at_build(
    *,
    model: type[Model],
    relation: str,
    filter_class: type[RelationPkFilter | RelationPkMultipleFilter],
) -> None:
    """A declared raw-key leaf on a multi-column link has no scalar to publish.

    Every value identifies no row at request time, and no single column types the
    input, so the build refuses the filter naming its column count.
    """
    filtered_model = model

    class LinkFilter(FilterSet):
        leaf = filter_class(field_name=relation, lookup_expr="exact")

        class Meta:
            model = filtered_model
            fields = ()

    f = LinkFilter().filters["leaf"]
    expected = (
        f"LinkFilter: {filter_class.__name__} on '{relation}' names a relation linked by 2 "
        "columns, so no single key value can name a related row"
    )
    with pytest.raises(ConfigurationError) as exc_info:
        _ = convert_filter_to_input_annotation(
            f,
            model._meta.get_field(relation),
            None,
            LinkFilter,
        )
    assert str(exc_info.value).startswith(expected)


@pytest.mark.parametrize(
    (
        "model",
        "relation",
        "filter_class",
        "annotation",
    ),
    [
        pytest.param(LnkSlugObjectChild, "parent", RelationPkFilter, str | None, id="fo-off-pk"),
        pytest.param(
            LnkSlugObjectChild,
            "parent",
            RelationPkMultipleFilter,
            list[str] | None,
            id="fo-off-pk-list",
        ),
        pytest.param(
            LnkParent,
            "tags",
            RelationPkMultipleFilter,
            list[str] | None,
            id="m2m-to-field",
        ),
        pytest.param(
            LnkTag,
            "parents",
            RelationPkMultipleFilter,
            list[str] | None,
            id="reverse-m2m",
        ),
        pytest.param(models.Book, "shelf", RelationPkFilter, int | None, id="fk-onto-pk"),
        pytest.param(
            models.InterlibraryLoan,
            "lender",
            RelationPkFilter,
            str | None,
            id="fk-text-to-field",
        ),
    ],
)
def test_raw_key_input_is_typed_from_the_column_the_predicate_compares(
    *,
    model: type[Model],
    relation: str,
    filter_class: type[RelationPkFilter | RelationPkMultipleFilter],
    annotation: object,
) -> None:
    """A declared unmarked raw-key leaf publishes the scalar of the column it compares.

    ``LnkSlugObjectChild.parent`` compares ``LnkParent.slug`` and a many-to-many through a
    ``to_field`` compares that ``code`` / ``slug``, and an unmarked ``ForeignKey`` with a
    text ``to_field`` (``InterlibraryLoan.lender`` -> ``Branch.isil``) compares that
    column, so their inputs are strings, never the integer primary key the value is not
    compared with; an ordinary key keeps the target's primary-key scalar.
    """
    f = _bound(filter_class(field_name=relation, lookup_expr="exact"), None, model=model)
    model_field = model._meta.get_field(relation)
    assert convert_filter_to_input_annotation(f, model_field, None, FilterSet) == annotation


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("owner_kind", ["unbound", "bound"])
@pytest.mark.parametrize(
    (
        "model",
        "relation",
        "matching",
        "rows",
        "label",
    ),
    [
        pytest.param(
            LnkSlugObjectChild,
            "parent",
            "s-a",
            ["a1", "a2", "a3"],
            "name",
            id="one-column-fo-off-pk",
        ),
        pytest.param(LnkParent, "tags", "c-t2", ["pa"], "label", id="m2m-through-to-field"),
        pytest.param(
            LnkTag,
            "parents",
            "s-b",
            ["t1"],
            "name",
            id="reverse-m2m-through-to-field",
        ),
    ],
)
@pytest.mark.parametrize(
    ("filter_class", "lookup", "wrap"),
    [
        pytest.param(GlobalIDFilter, "exact", False, id="globalid-exact"),
        pytest.param(GlobalIDMultipleChoiceFilter, "in", True, id="globalid-in"),
        pytest.param(RelationPkFilter, "exact", False, id="raw-exact"),
        pytest.param(RelationPkMultipleFilter, "in", True, id="raw-in"),
    ],
)
def test_unresolved_link_column_compares_the_value_the_link_holds(
    *,
    owner_kind: str,
    model: type[Model],
    relation: str,
    matching: str,
    rows: list[str],
    label: str,
    filter_class: type[Filter],
    lookup: str,
    wrap: bool,
) -> None:
    """An unmarked relation compared on a link column coerces its value through that column.

    A ``ForeignObject`` off the pk, and a many-to-many whose through foreign key onto the
    target has a ``to_field``, compare the link's column (Django's own
    ``<relation>=<value>``), never the target's primary key, so a value that column
    holds matches its rows; a value it cannot hold (an embedded NUL in text) answers
    ``GLOBALID_INVALID`` for a GlobalID and no row for a raw key.
    """
    owner = None if owner_kind == "unbound" else _definition(model, "LinkOwnerType")
    f = _bound(filter_class(field_name=relation, lookup_expr=lookup), owner, model=model)
    globalid = issubclass(filter_class, (GlobalIDFilter, GlobalIDMultipleChoiceFilter))
    if globalid:
        assert _globalid_target(f) is None

    def apply(raw: str) -> list[str]:
        item = relay.to_base64("Unregistered", raw) if globalid else raw
        value = [item] if wrap else item
        qs = f.filter(model._default_manager.order_by("pk"), value)
        return list(qs.values_list(label, flat=True))

    with link_fixture_tables(db_connection):
        assert apply(matching) == rows
        if globalid:
            with pytest.raises(GraphQLError, match="key value") as exc_info:
                _ = apply("a\x00b")
            assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}
        else:
            assert apply("a\x00b") == []


@pytest.mark.django_db
@pytest.mark.parametrize("owner_kind", ["unbound", "bound"])
def test_unresolved_continued_path_lookup_passes_the_node_id_through(*, owner_kind: str) -> None:
    """A ``lookup_expr`` continuing the path past the relation compares another column.

    ``GlobalIDFilter(field_name="shelf", lookup_expr="code")`` compiles
    ``shelf__code=<node id>``: ``code`` is no lookup the relation registers, so the node
    id is not coerced through the shelf's key and reaches the ``code`` column as given.
    """
    branch = models.Branch.objects.create(name="PathBranch", city="Boston")
    shelf = models.Shelf.objects.create(code="CP-1", branch=branch)
    _ = models.Book.objects.create(title="Kept", shelf=shelf)
    f = _bound(
        GlobalIDFilter(field_name="shelf", lookup_expr="code"),
        _unresolved_relation_owner(owner_kind),
    )
    assert _globalid_target(f) is None
    encoded = relay.to_base64("Unregistered", "CP-1")
    books = f.filter(models.Book.objects.all(), encoded)
    assert list(books.values_list("title", flat=True)) == ["Kept"]


def test_related_filter_relation_branch_strategy_aware() -> None:
    """A relation-branch (target-definition) filter applies the target's strategy."""
    _definition(models.Genre, "GenreType", "model")
    owner = _owner()
    f = _global_id_filter_with_owner("genres__id", owner)
    # The target's model label is accepted; the target's type name is rejected.
    assert (
        _decode_and_validate_global_id(
            relay.to_base64("library.genre", "3"),
            f,
            alias=DEFAULT_DB_ALIAS,
        )
        == 3
    )
    with pytest.raises(GraphQLError, match="GlobalID type mismatch"):
        _decode_and_validate_global_id(
            relay.to_base64("GenreType", "3"),
            f,
            alias=DEFAULT_DB_ALIAS,
        )


def test_multi_value_filter_forwards_integer_keys_to_upstream_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A model-owned list filter hands the upstream callback actual Python int keys.

    HTTP rows cannot distinguish an integer key from a database-coercible text key.
    Ordinary list acceptance and wrong-target refusal live in
    ``test_library_api.py::test_library_genres_filter_by_relay_own_pk_global_id_in_list``
    and ``test_library_api.py::test_library_genres_filter_by_relay_own_pk_global_id_in_rejects_wrong_type``.
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
    assert all(type(key) is int for keys in captured for key in keys)


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


def test_a_standalone_integer_primitive_keeps_parent_and_omission_identity() -> None:
    """The absent parent slot and exact queryset identity are Python observations.

    Native direct primitive acceptance and scalar refusal are owned by
    ``examples/fakeshop/test_query/test_direct_filter_primitives_api.py::test_direct_public_membership_primitives_refuse_scalar_containers``.
    """
    queryset = models.Shelf.objects.none()
    primitive = IntegerInFilter(field_name="id", lookup_expr="in")
    assert getattr(primitive, "parent", None) is None
    assert primitive.filter(queryset, None) is queryset


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("", id="empty-string"),
        pytest.param([1], id="short-list"),
        pytest.param([1, 2, 3], id="long-list"),
        pytest.param(123, id="number"),
        pytest.param("invalid", id="string"),
    ],
)
def test_integer_range_filter_malformed_values_pass_through(value: object) -> None:
    """A malformed pair preserves the original Python queryset object.

    A request can show unchanged rows, not queryset identity. Native rowsets live in
    ``test_direct_filter_primitives_api.py::test_a_direct_integer_range_primitive_keeps_upstreams_non_pair_skip``.
    """
    qs = models.Shelf.objects.all()
    f = IntegerRangeFilter(field_name="id")

    assert f.filter(qs, value) is qs


def test_filters_base_edge_cases() -> None:
    """Edge cases for the relation-pk marker helpers."""
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

    ``getattr(related, 'filterset')`` raises the typed error rather than detonating at the
    BFS builder's ``target.type_name_for()``.
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


def test_list_filter_one_shot_iterator_is_a_coded_reject() -> None:
    """A Python-only one-shot iterator is refused without being consumed as a JSON list.

    Native scalar-container refusals live in
    ``test_direct_filter_primitives_api.py::test_direct_public_membership_primitives_refuse_scalar_containers``.
    """
    visited: list[str] = []

    def members() -> Iterator[str]:
        visited.append("iterated")
        yield "a"
        yield "b"

    f = ListFilter(field_name="code")
    with pytest.raises(GraphQLError) as exc_info:
        f.filter(models.Shelf.objects.none(), members())
    assert exc_info.value.extensions == {"code": "FILTER_INVALID"}
    assert visited == []


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
    """``value == []`` compares through the value's own ``__eq__``.

    Whatever that ``__eq__`` raises propagates.
    """

    class RaisingEq:
        @override
        def __eq__(self, other: object) -> bool:
            raise RuntimeError("value __eq__ raised")

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


def test_raw_non_pk_to_field_leaves_are_primary_key_marked_relation_filters() -> None:
    """Only private metadata or callback observations remain here.

    Live sibling: ``examples/fakeshop/test_query/test_raw_relation_key_forms_api.py``.
    """

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


def test_an_unbound_relation_key_primitive_preserves_the_omission_queryset_identity() -> None:
    """Only exact returned QuerySet identity remains a Python-level observation.

    Public unbound single/multiple identity filtering is owned over HTTP by
    ``examples/fakeshop/test_query/test_declared_key_primitives_api.py::test_an_unbound_relation_key_primitive_keeps_its_public_queryset_contract``.
    """
    queryset = models.Book.objects.none()
    single = RelationPkFilter(field_name="shelf", lookup_expr="exact")
    many = RelationPkMultipleFilter(field_name="shelf", lookup_expr="in")
    assert single.filter(queryset, None) is queryset
    assert many.filter(queryset, None) is queryset
