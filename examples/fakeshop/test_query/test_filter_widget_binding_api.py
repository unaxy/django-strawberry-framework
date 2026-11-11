"""Native filter widgets read supplied values through their bound forms over HTTP.

Ordinary consumer JSON and DateTime arguments enter public FilterSet.apply_sync.
The form's actual widgets, constructor edits and physical data keys own cleaning.
A form rebinding each value as its text keeps a one-key widget's value, while a split
date/time widget cannot split a datetime's text: a masked ``ConfigurationError``. A nested
split range bound whose wall clock in the current time zone leaves years 1..9999 is the
field's ``FILTER_INVALID`` refusal, an empty-permitted form cleaning itself in ``__init__``
included. A consumer form cleaned again over new data is asked about that data alone.
The native holder orders its branch rows by primary key.
"""

from __future__ import annotations

import copy
import datetime
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import wraps

import django_filters
import pytest
import strawberry
from apps.library import models
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Case, DateTimeField, QuerySet, Value, When
from django.http import HttpRequest, HttpResponseBase, QueryDict
from django.test import override_settings
from django.urls import path
from django_filters.fields import DateTimeRangeField
from django_filters.filterset import BaseFilterSet
from graphql_client import JSONObject, RecordCompiledSql, graphql_payload, json_at
from strawberry.scalars import JSON
from strawberry.types import Info
from strawberry.types.base import StrawberryList
from typing_extensions import Self, override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils._narrowing import (
    call_method,
    is_list_or_tuple,
    read_attr,
    require_instance,
)
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_NAMES = ("Alpha", "Beta", "Gamma")
_CHOICES = [(name, name) for name in _NAMES]


@wraps(DjangoGraphQLView.as_view())
def _view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-filter-widgets/", _view)]


def _branches() -> None:
    for name in _NAMES:
        models.Branch.objects.create(name=name, city="Boston")


def _moments() -> QuerySet[models.Branch]:
    return models.Branch.objects.annotate(
        moment=Case(
            When(
                name="Alpha",
                then=Value(datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)),
            ),
            When(
                name="Beta",
                then=Value(datetime.datetime(2024, 1, 2, tzinfo=datetime.timezone.utc)),
            ),
            default=Value(datetime.datetime(2024, 1, 3, tzinfo=datetime.timezone.utc)),
            output_field=DateTimeField(),
        ),
    ).order_by("pk")


def _schema(filters: type[FilterSet], *, ranged: bool = False) -> DjangoSchema:
    class BranchWidgetOutput(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("name",)

    query_type: type[object]
    if ranged:

        @strawberry.type
        class RangeQuery:
            def _rows(
                self,
                info: Info[object, object],
                start: datetime.datetime | None = None,
                end: datetime.datetime | None = None,
            ) -> QuerySet[models.Branch]:
                return filters.apply_sync(
                    {"span": {"range": {"start": start, "end": end}}},
                    _moments(),
                    info,
                )

            rows: QuerySet[models.Branch] = strawberry.field(
                resolver=_rows,
                graphql_type=StrawberryList(BranchWidgetOutput),
            )

        query_type = RangeQuery
    else:

        @strawberry.type
        class PlainQuery:
            def _rows(self, info: Info[object, object], where: JSON) -> QuerySet[models.Branch]:
                return filters.apply_sync(where, models.Branch.objects.order_by("pk"), info)

            rows: QuerySet[models.Branch] = strawberry.field(
                resolver=_rows,
                graphql_type=StrawberryList(BranchWidgetOutput),
            )

        query_type = PlainQuery
    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=query_type,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _post(schema: DjangoSchema, where: object) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                "query($where: JSON!) { rows(where: $where) { name } }",
                variables={"where": where},
                url="/graphql-filter-widgets/",
            )
    finally:
        _CURRENT["schema"] = None


_RANGE_DOCUMENT = (
    "query($start: DateTime, $end: DateTime) { rows(start: $start, end: $end) { name } }"
)


def _range_post(schema: DjangoSchema, start: str | None, end: str | None) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                _RANGE_DOCUMENT,
                variables={"start": start, "end": end},
                url="/graphql-filter-widgets/",
            )
    finally:
        _CURRENT["schema"] = None


def _expected(names: Sequence[str]) -> JSONObject:
    return {"data": {"rows": [{"name": name} for name in names]}}


@dataclass(frozen=True)
class _Selection:
    names: tuple[str, ...]
    allowed: bool = True


class _PairField(forms.MultiValueField):
    def __init__(
        self,
        *,
        required: bool = False,
        label: str | None = None,
        widget: forms.Widget | type[forms.Widget] | None = None,
    ) -> None:
        super().__init__(
            fields=[forms.CharField(required=False), forms.CharField(required=False)],
            require_all_fields=False,
            required=required,
            label=label,
            widget=widget or forms.MultiWidget([forms.TextInput(), forms.TextInput()]),
        )

    @override
    def compress(self, data_list: list[object]) -> _Selection | None:
        if not data_list:
            return None
        return _Selection(tuple(str(value) for value in data_list if value not in (None, "")))


class _PairFilter(django_filters.Filter):
    field_class = _PairField


class _BranchFilter(FilterSet):
    pick: django_filters.Filter = _PairFilter(field_name="name", method="select_names")

    class Meta:
        model = models.Branch
        fields = []

    def select_names(
        self,
        queryset: QuerySet[models.Branch],
        _name: str,
        value: _Selection,
    ) -> QuerySet[models.Branch]:
        return queryset.filter(name__in=value.names) if value.allowed else queryset.none()


def _constructor_filter(style: str) -> type[FilterSet]:
    class ConstructorFilter(_BranchFilter):
        pick: django_filters.Filter = _PairFilter(
            field_name="name",
            method="select_names",
            widget=forms.TextInput()
            if style == "widget-after-super"
            else forms.MultiWidget([forms.TextInput(), forms.TextInput()]),
        )

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[models.Branch] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
            _nested: bool = False,
        ) -> None:
            inherited_widget: forms.Widget | None = None
            if style == "same-class-before-super" and not _nested:
                prototype = type(self)(queryset=queryset, request=request, _nested=True)
                inherited_widget = copy.deepcopy(
                    require_instance(
                        read_attr(prototype.filters["pick"].field, "widget"),
                        forms.Widget,
                    ),
                )
            if style in {"copy-and-edit", "copy-and-remove"}:
                copied = dict(data or {}).copy()
                if style == "copy-and-edit":
                    copied["pick"] = ["Beta", "Gamma"]
                else:
                    copied.pop("pick", None)
                data = copied
            super().__init__(data, queryset, request=request, prefix=prefix)
            self.filters["pick"].field.widget = inherited_widget or forms.MultiWidget(
                [forms.TextInput(), forms.TextInput()],
            )
            if style == "early-clean":
                self.form.is_valid()

        @override
        def get_form_class(self) -> type[forms.Form]:
            if style == "bare-form-class":
                return forms.Form
            return (
                BaseFilterSet.get_form_class(self)
                if style == "upstream-form-class"
                else super().get_form_class()
            )

    if style == "same-class-before-super":

        class DirectAllocationFilter(ConstructorFilter):
            def __new__(
                cls,
                data: Mapping[str, object] | None = None,
                queryset: QuerySet[models.Branch] | None = None,
                *,
                request: HttpRequest | None = None,
                prefix: str | None = None,
                _nested: bool = False,
            ) -> Self:
                del data, queryset, request, prefix
                return object.__new__(cls)

        return DirectAllocationFilter
    return ConstructorFilter


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("style", "expected"),
    [
        ("widget-after-super", ("Alpha", "Beta")),
        ("copy-and-edit", ("Beta", "Gamma")),
        ("copy-and-remove", _NAMES),
        ("same-class-before-super", ("Alpha", "Beta")),
        ("early-clean", ("Alpha", "Beta")),
        ("upstream-form-class", ("Alpha", "Beta")),
        ("bare-form-class", _NAMES),
    ],
    ids=[
        "widget-after-super",
        "copy-and-edit",
        "copy-and-remove",
        "same-class-before-super",
        "early-clean",
        "upstream-form-class",
        "bare-form-class",
    ],
)
def test_constructor_changes_reach_the_actual_bound_widgets(
    style: str,
    expected: tuple[str, ...],
) -> None:
    """Constructor widget changes and current data survive copies and nested construction.

    A ``get_form_class`` returning Django's bare ``Form`` declares no filter field, so
    its bound form cleans nothing and, as upstream's, filters nothing.
    """
    _branches()
    schema = _schema(_constructor_filter(style))
    payload = _post(schema, {"pick": ["Alpha", "Beta"]})
    assert payload == _expected(expected), payload


class _ParentPairFilter(_PairFilter):
    parent: FilterSet

    @property
    @override
    def field(self) -> forms.Field:
        return _PairField(label=self.parent.form_prefix or "Names")


@pytest.mark.django_db
def test_a_parent_dependent_field_is_built_only_after_its_filter_is_bound() -> None:
    """A field deriving its label from its bound parent still applies the supplied names."""
    _branches()

    class ParentFilter(_BranchFilter):
        pick: django_filters.Filter = _ParentPairFilter(field_name="name", method="select_names")

    payload = _post(_schema(ParentFilter), {"pick": ["Alpha", "Beta"]})
    assert payload == _expected(("Alpha", "Beta")), payload


def _data_form(style: str, *, empty_permitted: bool = False) -> type[forms.Form]:
    class DataForm(forms.Form):
        prefix: str | None = "search" if "prefix" in style else None

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(
                data=data,
                prefix=prefix,
                empty_permitted=empty_permitted,
                use_required_attribute=not empty_permitted,
            )
            current: Mapping[str, object] = self.data
            if style == "copy-and-edit":
                self.data = {**current, "pick": ["Beta", "Gamma"]}
            elif style == "copy-and-remove":
                copied = dict(current).copy()
                copied.pop("pick", None)
                self.data = copied
            elif style.startswith("querydict"):
                bound = QueryDict(mutable=True)
                for key, value in current.items():
                    object_result(
                        bound.setlist,
                        key,
                        list(value) if is_list_or_tuple(value) else [value],
                    )
                if style == "querydict":
                    bound.setlist("pick_0_prefix", [])
                if style == "querydict-physical":
                    # One explicit member key owns that part; the canonical input supplies the other.
                    bound.setlist("pick_0", ["Gamma"])
                if style == "querydict-prefix-empty":
                    bound.setlist("pick", [])
                self.data = bound
            elif style == "text":
                # Each value as its text, the mapping an HTML form post binds.
                posted = QueryDict(mutable=True)
                for key, value in current.items():
                    posted[key] = str(value)
                self.data = QueryDict(posted.urlencode())
            elif style == "early-clean":
                self.full_clean()
            elif style == "physical-partial":
                copied = dict(current)
                # One explicit key owns that part; the canonical input still supplies the other.
                copied["pick_0"] = "Gamma"
                self.data = copied

    return DataForm


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("style", "values", "expected"),
    [
        ("copy-and-edit", ["Alpha", "Beta"], ("Beta", "Gamma")),
        ("copy-and-remove", ["Alpha", "Beta"], _NAMES),
        ("early-clean", ["Alpha", "Beta"], ("Alpha", "Beta")),
        ("physical-partial", ["Alpha", "Beta"], ("Beta", "Gamma")),
    ],
    ids=[
        "copy-and-edit",
        "copy-and-remove",
        "early-clean",
        "physical-partial",
    ],
)
def test_form_copies_and_current_physical_edits_own_the_bound_value(
    style: str,
    values: list[str],
    expected: tuple[str, ...],
) -> None:
    """Form edits own explicit parts while untouched canonical parts retain their values."""
    _branches()

    class FormFilter(_BranchFilter):
        class Meta(_BranchFilter.Meta):
            model = models.Branch
            fields = []
            form = _data_form(style)

    payload = _post(_schema(FormFilter), {"pick": values})
    assert payload == _expected(expected), payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("style", "expected"),
    [("querydict-prefix", ("Alpha", "Beta")), ("querydict-prefix-empty", _NAMES)],
    ids=["two-members", "empty-stored-list"],
)
def test_a_prefixed_choice_widget_keeps_its_querydict_members_and_empty_list(
    style: str,
    expected: tuple[str, ...],
) -> None:
    """A prefixed choice reads every current member and treats an empty value list as empty."""
    _branches()

    class ChoiceFilter(FilterSet):
        pick = django_filters.MultipleChoiceFilter(field_name="name", choices=_CHOICES)

        class Meta:
            model = models.Branch
            fields = []
            form = _data_form(style)

    payload = _post(_schema(ChoiceFilter), {"pick": ["Alpha", "Beta"]})
    assert payload == _expected(expected), payload


@pytest.mark.django_db
def test_a_prefixed_text_widget_reads_the_last_repeated_querydict_value() -> None:
    """A one-key alias preserves QueryDict.get semantics rather than stringifying its list."""
    _branches()

    class TextFilter(FilterSet):
        pick = django_filters.CharFilter(field_name="name")

        class Meta:
            model = models.Branch
            fields = []
            form = _data_form("querydict-prefix")

    payload = _post(_schema(TextFilter), {"pick": ["Alpha", "Beta"]})
    assert payload == _expected(("Beta",)), payload


class _MappingReaderInput(forms.TextInput):
    """A consumer reader asking only the Mapping protocol, never ``get`` / ``getlist``."""

    @override
    def value_from_datadict(
        self,
        data: Mapping[str, object],
        files: object,
        name: str,
    ) -> object:
        if not data or name not in data:
            return None
        posted = {key: data[key] for key in data}
        return posted[name]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("style", "values", "expected"),
    [("prefix", "Alpha", ("Alpha",)), ("querydict-prefix", ["Alpha", "Beta"], ("Beta",))],
    ids=["dict-prefix", "querydict-prefix"],
)
def test_a_prefixed_mapping_protocol_reader_sees_the_bound_value(
    style: str,
    values: object,
    expected: tuple[str, ...],
) -> None:
    """Truthiness, membership, iteration and indexing all see the prefixed bound key.

    A plain mapping exposes the derived prefixed entry beside its own keys; a
    ``QueryDict`` re-keys its canonical list, so indexing answers its last value.
    """
    _branches()

    class ReaderFilter(FilterSet):
        pick = django_filters.CharFilter(field_name="name", widget=_MappingReaderInput())

        class Meta:
            model = models.Branch
            fields = []
            form = _data_form(style)

    payload = _post(_schema(ReaderFilter), {"pick": values})
    assert payload == _expected(expected), payload


class _SinglePostedInput(forms.TextInput):
    @override
    def value_from_datadict(
        self,
        data: Mapping[str, object],
        files: object,
        name: str,
    ) -> object:
        posted = call_method(data, "getlist", name)
        if not is_list_or_tuple(posted) or len(posted) > 1:
            raise forms.ValidationError("Supply one posted value.")
        return posted[0] if posted else None


class _PrefixedPostedInput(_SinglePostedInput):
    @override
    def value_from_datadict(
        self,
        data: Mapping[str, object],
        files: object,
        name: str,
    ) -> object:
        value = super().value_from_datadict(data, files, name)
        prefix = data.get(f"{name}_prefix", "")
        return f"{prefix}{value}" if value is not None else None


class _NestedField(forms.MultiValueField):
    def __init__(
        self,
        *,
        reader: str = "multiple",
        required: bool = False,
        label: str | None = None,
    ) -> None:
        if reader == "multiple":
            member_field: forms.Field = forms.MultipleChoiceField(choices=_CHOICES, required=False)
        elif reader in {"json", "opaque-json"}:
            member_field = forms.JSONField(
                widget=_SinglePostedInput() if reader == "opaque-json" else forms.TextInput(),
                required=False,
            )
        else:
            member_field = forms.CharField(widget=_PrefixedPostedInput(), required=False)
        super().__init__(
            fields=[member_field, forms.CharField(required=False)],
            require_all_fields=False,
            required=required,
            label=label,
            widget=forms.MultiWidget(
                [
                    require_instance(read_attr(member_field, "widget"), forms.Widget),
                    forms.TextInput(),
                ],
            ),
        )

    @override
    def compress(self, data_list: list[object]) -> _Selection | None:
        if not data_list:
            return None
        members = data_list[0]
        names = (
            tuple(str(name) for name in members) if is_list_or_tuple(members) else (str(members),)
        )
        return _Selection(names, len(data_list) > 1 and data_list[1] == "go")


class _NestedFilter(django_filters.Filter):
    field_class = _NestedField


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("reader", "members", "expected"),
    [
        ("multiple", ["Alpha", "Beta"], ("Alpha", "Beta")),
        ("multiple", None, ()),
        ("json", ["Alpha", "Beta"], ("Alpha", "Beta")),
        ("single", "Alpha", ("Alpha",)),
    ],
    ids=[
        "multiple-choice-list",
        "multiple-choice-null",
        "json-list-object",
        "single-posted-scalar",
    ],
)
def test_nested_widget_readers_keep_members_objects_and_single_posted_values(
    reader: str,
    members: object,
    expected: tuple[str, ...],
) -> None:
    """Nested readers preserve list membership, opaque values and current getter defaults."""
    _branches()

    class NestedFilter(_BranchFilter):
        pick: django_filters.Filter = _NestedFilter(
            field_name="name",
            method="select_names",
            reader=reader,
        )

        class Meta(_BranchFilter.Meta):
            model = models.Branch
            fields = []
            form = _data_form("querydict")

    schema = _schema(NestedFilter)
    payload = _post(schema, {"pick": [members, "go"]})
    assert payload == _expected(expected), payload
    declined = _post(schema, {"pick": [members, "stop"]})
    assert declined == _expected(()), declined


@pytest.mark.django_db
def test_a_querydict_physical_member_list_wins_over_its_derived_part() -> None:
    """A member list the form posts itself is read whole; the canonical input fills the rest."""
    _branches()

    class PhysicalMemberFilter(_BranchFilter):
        pick: django_filters.Filter = _NestedFilter(field_name="name", method="select_names")

        class Meta(_BranchFilter.Meta):
            model = models.Branch
            fields = []
            form = _data_form("querydict-physical")

    payload = _post(_schema(PhysicalMemberFilter), {"pick": [["Alpha", "Beta"], "go"]})
    assert payload == _expected(("Gamma",)), payload


class _NestedRangeField(DateTimeRangeField):
    def __init__(self, *, required: bool = False, label: str | None = None) -> None:
        super().__init__(required=required, label=label)
        self.require_all_fields = False
        self.fields = [
            forms.SplitDateTimeField(required=False),
            forms.SplitDateTimeField(required=False),
        ]
        self.widget = forms.MultiWidget([forms.SplitDateTimeWidget(), forms.SplitDateTimeWidget()])

    @override
    def compress(self, data_list: list[object] | None) -> slice | None:
        # Empty nested widgets clean to [None, None], still an absent logical range.
        values = data_list if data_list and any(value is not None for value in data_list) else []
        return super().compress(values)


class _NestedDateRangeFilter(django_filters.DateTimeFromToRangeFilter):
    field_class = _NestedRangeField


@pytest.mark.django_db
@pytest.mark.parametrize("mapping", ["dict", "querydict-prefix"], ids=["dict", "querydict-prefix"])
@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        ("2024-01-02T00:00:00+00:00", "2024-01-03T00:00:00+00:00", ("Beta", "Gamma")),
        ("2024-01-02T00:00:00+00:00", None, ("Beta", "Gamma")),
        (None, "2024-01-02T00:00:00+00:00", ("Alpha", "Beta")),
        (None, None, _NAMES),
    ],
    ids=[
        "both",
        "start-only",
        "end-only",
        "neither",
    ],
)
def test_nested_datetime_range_widgets_keep_each_supplied_axis(
    mapping: str,
    start: str | None,
    end: str | None,
    expected: tuple[str, ...],
) -> None:
    """Nested date/time widgets retain each supplied bound without inventing an absent bound."""
    _branches()

    class RangeFilter(FilterSet):
        span = _NestedDateRangeFilter(field_name="moment", lookup_expr="range")

        class Meta:
            model = models.Branch
            fields = []
            form = _data_form(mapping)

    payload = _range_post(_schema(RangeFilter, ranged=True), start, end)
    assert payload == _expected(expected), payload


@pytest.mark.django_db
@pytest.mark.parametrize("mapping", ["dict", "querydict-prefix"], ids=["dict", "querydict-prefix"])
@pytest.mark.parametrize("empty_permitted", [False, True], ids=["ordinary", "empty-permitted"])
@pytest.mark.parametrize("side", ["start", "end"])
@pytest.mark.parametrize(
    ("zone", "bound", "expected"),
    [
        pytest.param("UTC", "0001-01-01T00:30:00+01:00", None, id="utc-before-year-one"),
        pytest.param("UTC", "9999-12-31T23:30:00-01:00", None, id="utc-past-year-9999"),
        pytest.param(
            "America/New_York",
            "0001-01-01T00:30:00+00:00",
            None,
            id="new-york-year-one-in-utc",
        ),
        pytest.param(
            "UTC",
            "0001-01-01T00:30:00+00:00",
            {"start": _NAMES, "end": ()},
            id="utc-year-one-in-utc",
        ),
    ],
)
def test_a_nested_split_range_bound_the_zone_cannot_present_is_filter_invalid(
    mapping: str,
    side: str,
    zone: str,
    bound: str,
    expected: Mapping[str, tuple[str, ...]] | None,
    record_compiled_sql: RecordCompiledSql,
    *,
    empty_permitted: bool,
) -> None:
    """A bound whose wall clock in the current time zone leaves years 1..9999 is refused.

    The nested ``SplitDateTimeWidget`` splits each bound into the current time zone's date
    and time as the form reads it, which it cannot do for a datetime whose wall clock there
    falls in year 0 or 10000: ``FILTER_INVALID`` keyed to ``span``, ``invalid`` ("Enter a
    value the current time zone can represent."), even for ``0001-01-01T00:30:00+00:00``,
    which filters under ``UTC``.
    """
    _branches()

    class RangeFilter(FilterSet):
        span = _NestedDateRangeFilter(field_name="moment", lookup_expr="range")

        class Meta:
            model = models.Branch
            fields = []
            form = _data_form(mapping, empty_permitted=empty_permitted)

    schema = _schema(RangeFilter, ranged=True)
    recorded = record_compiled_sql()
    with override_settings(TIME_ZONE=zone):
        payload = _range_post(schema, *((bound, None) if side == "start" else (None, bound)))

    if expected is not None:
        assert payload == _expected(expected[side]), payload
        return
    refusal = {"message": "Enter a value the current time zone can represent.", "code": "invalid"}
    assert payload == {
        "data": None,
        "errors": [
            {
                "message": "Invalid filter input",
                "locations": [{"line": 1, "column": _RANGE_DOCUMENT.index("rows") + 1}],
                "path": ["rows"],
                "extensions": {"code": "FILTER_INVALID", "errors": {"span": [refusal]}},
            },
        ],
    }, payload
    assert recorded == [], recorded


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["Beta", "\ud800"])
def test_empty_permitted_form_delegates_unchanged_and_propagates_consumer_change_error(
    value: str,
) -> None:
    _branches()
    calls: list[str] = []

    class EmptyForm(forms.Form):
        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(
                data=data,
                prefix=prefix,
                empty_permitted=True,
                use_required_attribute=False,
            )

        @override
        def full_clean(self) -> None:
            calls.append("full_clean")
            super().full_clean()

        @override
        def clean(self) -> dict[str, object]:
            calls.append("clean")
            return super().clean() or {}

    class EmptySet(FilterSet):
        pick = django_filters.CharFilter(field_name="name")

        class Meta:
            model = models.Branch
            fields = []
            form: type[forms.Form] = EmptyForm

    class RefusingChangeForm(EmptyForm):
        @override
        def has_changed(self) -> bool:
            raise ValidationError("consumer change detection", code="consumer")

    class RefusingSet(EmptySet):
        class Meta(EmptySet.Meta):
            form: type[forms.Form] = RefusingChangeForm

    @strawberry.type
    class Query:
        @strawberry.field
        def valid(self, *, refusing: bool) -> bool:
            chosen = RefusingSet if refusing else EmptySet
            return chosen(
                data={"pick": value} if refusing else {},
                queryset=models.Branch.objects.all(),
            ).is_valid()

    schema = DjangoSchema(query=Query, error_policy={"enabled": False})
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            unchanged = graphql_payload(
                "{ valid(refusing: false) }",
                url="/graphql-filter-widgets/",
            )
            assert unchanged == {"data": {"valid": True}}
            assert calls == ["full_clean"]
            calls.clear()
            refused = graphql_payload("{ valid(refusing: true) }", url="/graphql-filter-widgets/")
    finally:
        _CURRENT["schema"] = None
    assert json_at(refused, "errors", 0, "message") == "consumer change detection"
    assert calls == []


@pytest.mark.django_db
def test_an_empty_permitted_form_cleaning_itself_early_keeps_its_widgets_refusal() -> None:
    """An empty-permitted form whose ``__init__`` cleans it answers the widget's own refusal.

    Its change detection reads the nested split range widget, which cannot split a bound whose
    wall clock in the current time zone falls in year 0: that refusal is the form's error,
    and the clean stops there, never asking the widget again.
    """
    _branches()

    class RangeFilter(FilterSet):
        span = _NestedDateRangeFilter(field_name="moment", lookup_expr="range")

        class Meta:
            model = models.Branch
            fields = []
            form = _data_form("early-clean", empty_permitted=True)

    schema = _schema(RangeFilter, ranged=True)
    with override_settings(TIME_ZONE="UTC"):
        payload = _range_post(schema, "0001-01-01T00:30:00+01:00", None)

    refusal = {"message": "Enter a value the current time zone can represent.", "code": "invalid"}
    assert payload == {
        "data": None,
        "errors": [
            {
                "message": "Invalid filter input",
                "locations": [{"line": 1, "column": _RANGE_DOCUMENT.index("rows") + 1}],
                "path": ["rows"],
                "extensions": {"code": "FILTER_INVALID", "errors": {"span": [refusal]}},
            },
        ],
    }, payload


@pytest.mark.django_db
def test_a_form_cleaned_again_over_new_data_asks_that_data() -> None:
    """A consumer form falling back to other data and cleaning again is asked about that data.

    Its ``__init__`` cleans the sent data, finds the text the package refuses, swaps in a
    fallback and calls ``full_clean()`` again: the second clean reads the fallback afresh, so
    the refusal of the first is gone and the fallback filters the rows.
    """
    _branches()

    class FallbackForm(forms.Form):
        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, prefix=prefix)
            if not self.is_valid():
                self.data = {"pick": "Beta"}
                self.full_clean()

    class FallbackSet(FilterSet):
        pick = django_filters.CharFilter(field_name="name")

        class Meta:
            model = models.Branch
            fields = []
            form: type[forms.Form] = FallbackForm

    assert _post(_schema(FallbackSet), {"pick": "\ud800"}) == _expected(("Beta",))


@pytest.mark.django_db
def test_a_form_generated_by_typed_normalization_can_be_reused_as_meta_form() -> None:
    _branches()
    generated: list[type[forms.Form]] = []

    class CapturingForm(forms.Form):
        prefix = "search"

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, prefix=prefix)
            generated.append(type(self))

    class SourceSet(FilterSet):
        pick = django_filters.CharFilter(field_name="name")

        class Meta:
            model = models.Branch
            fields = []
            form: type[forms.Form] = CapturingForm

    assert _post(_schema(SourceSet), {"pick": "Beta"}) == _expected(("Beta",))
    assert len(generated) == 1

    class ReusedSet(SourceSet):
        class Meta(SourceSet.Meta):
            form: type[forms.Form] = generated[0]

    registry.clear()
    assert _post(_schema(ReusedSet), {"pick": "Beta"}) == _expected(("Beta",))


@pytest.mark.django_db
def test_a_one_key_widget_bound_to_its_text_filters_by_it() -> None:
    """A form ``__init__`` rebinding each value as its text keeps a one-key widget's value."""
    _branches()

    class TextFilter(FilterSet):
        pick = django_filters.CharFilter(field_name="name")

        class Meta:
            model = models.Branch
            fields = []
            form = _data_form("text")

    payload = _post(_schema(TextFilter), {"pick": "Beta"})
    assert payload == _expected(("Beta",)), payload


@pytest.mark.django_db
def test_split_datetime_widgets_bound_to_their_text_are_a_masked_configuration_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A nested ``SplitDateTimeWidget`` cannot split the text of a datetime bound.

    The form ``__init__`` rebinds each bound value as its text, so ``span_0`` holds the
    text of the start bound, which ``decompress`` (taking a ``datetime``) cannot split:
    a ``ConfigurationError`` naming ``span_0`` and the widget's ``span_0_0`` /
    ``span_0_1``, never the value's text, before the form cleans. The client gets the
    error policy's masked top-level error and no rows.
    """
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    _branches()

    class RangeFilter(FilterSet):
        span = _NestedDateRangeFilter(field_name="moment", lookup_expr="range")

        class Meta:
            model = models.Branch
            fields = []
            form = _data_form("text")

    payload = _range_post(
        _schema(RangeFilter, ranged=True),
        "2024-01-02T00:00:00+00:00",
        "2024-01-03T00:00:00+00:00",
    )
    correlation_id = json_at(payload, "errors", 0, "extensions", "correlationId")
    assert isinstance(correlation_id, str), payload
    assert payload == {
        "data": None,
        "errors": [
            {
                "message": "An unexpected error occurred.",
                "locations": [{"line": 1, "column": _RANGE_DOCUMENT.index("rows") + 1}],
                "path": ["rows"],
                "extensions": {"correlationId": correlation_id},
            },
        ],
    }
    [logged] = [
        record.exc_info
        for record in caplog.records
        if record.name == "django_strawberry_framework" and record.exc_info is not None
    ]
    assert isinstance(logged[1], ConfigurationError), logged
    message = str(logged[1])
    assert message.startswith(
        "SplitDateTimeWidget.decompress cannot split the str bound under 'span_0' into "
        "the parts the widget reads ('span_0_0', 'span_0_1'): it raised AttributeError",
    ), message
    assert "2024-01-02" not in message, message


@pytest.mark.django_db
@pytest.mark.parametrize("ownership", ["disabled", "physical"], ids=["disabled", "physical"])
def test_a_split_widget_leaves_disabled_and_explicit_physical_values_in_control(
    ownership: str,
) -> None:
    """Disabled and fully physical input never decomposes the ignored canonical list."""
    _branches()
    pytest.importorskip("django.contrib.postgres.forms")
    from django.contrib.postgres.forms import SplitArrayField  # noqa: PLC0415 - optional widget needs a driver

    class DisabledSplitFilter(django_filters.Filter):
        @property
        @override
        def field(self) -> forms.Field:
            return SplitArrayField(
                forms.CharField(),
                size=2,
                required=False,
                disabled=ownership == "disabled",
                initial=["Alpha", "Beta"],
            )

    class DisabledFilter(FilterSet):
        pick = DisabledSplitFilter(field_name="name", method="select_names")

        class Meta:
            model = models.Branch
            fields = []

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[models.Branch] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            if ownership == "physical":
                current: Mapping[str, object] = self.data or {}
                self.data = {**current, "pick_0": "Gamma", "pick_1": "Beta"}
            self.form["pick"].value()

        def select_names(
            self,
            queryset: QuerySet[models.Branch],
            _name: str,
            value: list[str],
        ) -> QuerySet[models.Branch]:
            return queryset.filter(name__in=value)

    payload = _post(_schema(DisabledFilter), {"pick": ["Gamma", "unread", "too-many"]})
    expected = ("Alpha", "Beta") if ownership == "disabled" else ("Beta", "Gamma")
    assert payload == _expected(expected), payload


def _branch_sql(sqls: Sequence[str]) -> list[str]:
    return [
        sql
        for sql in sqls
        if sql.lstrip().upper().startswith("SELECT ")
        and " FROM " in sql
        and sql.split(" FROM ", 1)[1].startswith('"library_branch"')
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "outcome",
    ["accepted", "invalid-choice", "permission-refusal"],
    ids=["accepted", "invalid-choice", "permission-refusal"],
)
def test_all_values_choices_are_read_once_at_validation_and_never_before_permission(
    record_compiled_sql: RecordCompiledSql,
    outcome: str,
) -> None:
    """Choice materialization follows permission and runs once for accepted or invalid values."""
    _branches()

    class ChoicesFilter(FilterSet):
        pick = django_filters.AllValuesFilter(field_name="name")

        class Meta:
            model = models.Branch
            fields = []

        def check_pick_permission(self, _request: object) -> bool:
            return outcome != "permission-refusal"

    schema = _schema(ChoicesFilter)
    sqls = record_compiled_sql()
    payload = _post(schema, {"pick": "Unknown" if outcome == "invalid-choice" else "Alpha"})
    if outcome == "accepted":
        assert payload == _expected(("Alpha",)), payload
        assert len(_branch_sql(sqls)) == 2, sqls
    else:
        assert payload["data"] is None, payload
        assert "errors" in payload, payload
        if outcome == "invalid-choice":
            assert json_at(payload, "errors", 0, "extensions", "code") == "FILTER_INVALID", payload
        else:
            assert json_at(payload, "errors", 0, "message") == (
                "Not authorized to use pick on ChoicesFilter."
            ), payload
            assert json_at(payload, "errors", 0, "path") == ["rows"], payload
        assert len(_branch_sql(sqls)) == (1 if outcome == "invalid-choice" else 0), sqls


@pytest.mark.django_db
def test_a_custom_opaque_json_reader_keeps_its_explicit_physical_grouping() -> None:
    """A custom reader receives the opaque object grouped by the consumer form."""
    _branches()

    class PhysicalForm(forms.Form):
        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, prefix=prefix)
            current: Mapping[str, object] = self.data
            picked = current.get("pick")
            if not is_list_or_tuple(picked) or len(picked) != 2:
                raise forms.ValidationError("Supply names and the selection mode.")
            bound = QueryDict(mutable=True)
            object_result(bound.setlist, "pick_0", [picked[0]])
            object_result(bound.setlist, "pick_1", [picked[1]])
            self.data = bound

    class PhysicalFilter(_BranchFilter):
        pick: django_filters.Filter = _NestedFilter(
            field_name="name",
            method="select_names",
            reader="opaque-json",
        )

        class Meta(_BranchFilter.Meta):
            form = PhysicalForm

    payload = _post(_schema(PhysicalFilter), {"pick": [["Alpha", "Beta"], "go"]})
    assert payload == _expected(("Alpha", "Beta")), payload
