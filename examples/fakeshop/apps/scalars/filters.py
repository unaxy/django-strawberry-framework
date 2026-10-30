"""FilterSet declarations for the scalars acceptance app.

Where ``apps.scalars.schema`` exercises the converter table on the OUTPUT
side (every scalar field selected in a query), these filtersets exercise
the same converters on the INPUT side: each ``Meta.fields`` lookup flows
through ``convert_filter_to_input_annotation`` /
``_scalar_from_model_field`` to produce a Strawberry filter-input scalar
(``Decimal``, ``UUID``, ``date`` / ``datetime`` / ``time``, ``BigInt``,
``float``, ``bool``). ``JSONField`` (``payload``) is intentionally absent
-- django-filter ships no default filter for it, so it raises at
``get_filters()`` rather than producing an input.

These types are NOT Relay nodes (no ``interfaces`` on the owning
``DjangoType``), so each model's own ``id`` is a plain integer filter --
which makes the ``id`` ``"__all__"`` set (notably its ``in`` lookup)
exercise the django-filter-generated ``BaseInFilter`` -> ``list[int]``
converter path (the non-Relay counterpart to the library app's own-PK
``GlobalIDMultipleChoiceFilter``).

``ScalarSpecimenFilter.tag`` is a ``RelatedFilter`` onto
``ScalarSpecimenTagFilter``, whose owning ``ScalarSpecimenTagType``
declares a custom ``get_queryset`` (``active=True``) -- so the related
branch also exercises the ``get_queryset`` visibility hook through a
relation traversal.

``ScalarSpecimenFilter`` also names the self-referential relation itself: ``parent``
(forward foreign key) takes one specimen primary key for ``exact`` and a list for ``in``,
and ``children`` (its reverse) takes a list. ``ScalarSpecimenType`` is not a Relay node,
so these relation keys filter by the raw ``Int`` primary key rather than a GlobalID. They
are listed lookup by lookup: a per-field ``"__all__"`` would also ask for the ordering
lookups a relation key does not support.

``price_span`` on both specimen filtersets is a declared ``RangeFilter``
over the ``price`` column (the acceptance surface for per-filterset
scoped range input names). ``Meta.fields`` ``price: "__all__"`` still
expands the CSV ``range`` lookup on the ``price`` operator bag; the
declared primitive is a separate ``priceSpan: { range: { start, end } }`` field.

``price_among`` on ``ScalarSpecimenFilter`` is a declared ``ListFilter`` over the same
column with the ``in`` lookup (``priceAmong: { in: [...] }``): the acceptance surface for
a declared list filter, each element cleaned as ``price: { in }`` cleans its members.

Text-pattern lookups (``iexact`` / ``contains`` / ``startswith`` / ``regex`` / ...) are
published by a per-field ``"__all__"`` only on a text column (``label``).
``NullableScalarSpecimenFilter`` declares some explicitly on ``occurred_at`` and
``unsigned_big``: each such leaf is a ``String`` the backend matches against its text
rendering of the column, beside the column-typed ``exact``.

``signed_big_span`` / ``unsigned_big_span`` and ``signed_big_among`` / ``unsigned_big_among``
on ``ScalarSpecimenFilter`` are the same declared ``RangeFilter`` (``range``) and ``ListFilter``
(``in``) over the two ``BigInt`` columns: the acceptance surface for an integer bound or
element past the column's 64-bit range, which answers as the generated ``signedBig: { range }``
/ ``{ in }`` answer it (widening or matching nothing), never a backend overflow.

``price_between``, ``occurred_between`` and ``occurred_in_boxes`` on ``ScalarSpecimenFilter``
are django-filter's own range filters (``RangeFilter`` over ``price``,
``DateFromToRangeFilter`` over ``occurred_on``, and the same date filter over a plain
two-box ``MultiWidget``), each taking ``{ exact: { start, end } }``: the acceptance surface
for a range input sent under the keys the filter's widget reads (``_min`` / ``_max``,
``_after`` / ``_before``, ``_0`` / ``_1``). ``price_in_underscored_boxes`` is django-filter's
``RangeFilter`` over a consumer ``SuffixedMultiWidget`` whose suffixes open with ``_``, so
it reads ``<name>__low`` / ``<name>__high``, past a ``__``: a request names its flat
``partner`` copy by exactly those keys, so the copy applies the bounds sent.
``price_in_field_boxes`` is a consumer ``RangeFilter`` subclass whose ``field`` property
installs its own widget (``FieldBoxRangeWidget``: ``<name>_low`` / ``<name>_high``): the
keys are read off the form field the filter's own class builds, so the range input and
the flat ``partner`` copy are sent under exactly those keys. ``price_span_in_field_boxes``
is the package's ``RangeFilter`` with the same widget installed by ``FieldBoxWidgetMixin``,
a ``field`` override that follows it in the MRO, so it too is sent under ``_low`` / ``_high``.

``occurred_day_of`` on ``ScalarSpecimenFilter`` is a declared ``DateTimeFilter`` through the
``occurred_at`` column's ``date`` transform (``occurredDayOf: { date: <Date> }``): the
acceptance surface for a ``lookup_expr`` transform, typed by the transform's ``DateField``
output, never by the column or the declared form field.

``occurred_year_among`` / ``occurred_year_span`` on ``ScalarSpecimenFilter`` are a declared
``ListFilter`` (``in``) and ``RangeFilter`` (``range``) through the ``occurred_at`` column's
``year`` transform (``occurredYearAmong: { in: [...] }``, ``occurredYearSpan: { range: {
start, end } }``): the acceptance surface for a declared path through a column's transform,
typed by the transform's ``IntegerField`` output (``Int``), never by the declared form field.

``ScalarSpecimenParentStampFilter`` filters through a ``FilteredRelation`` alias rather than
a field: ``parent_day_of`` is a declared ``DateTimeFilter`` whose ``field_name``
(``par__occurred_at``) crosses ``par``, the ``FilteredRelation("parent")`` alias the
``allScalarSpecimensByParentStamp`` resolver adds to its queryset, into the parent's
``occurred_at`` column's ``date`` transform. It is the acceptance surface for a path only
the queryset the filter runs on resolves.
"""

from __future__ import annotations

import django_filters
from django import forms
from django_filters.widgets import SuffixedMultiWidget
from typing_extensions import override

from django_strawberry_framework.filters import FilterSet, ListFilter, RangeFilter, RelatedFilter

from . import models


class UnderscoredRangeWidget(SuffixedMultiWidget):
    """A two-box range widget whose suffixes open with ``_``: it reads ``<name>__low`` / ``<name>__high``."""

    suffixes = ["_low", "_high"]

    def __init__(self, attrs: dict[str, object] | None = None) -> None:
        """Two text boxes, one per suffix."""
        super().__init__((forms.TextInput, forms.TextInput), attrs)


class FieldBoxRangeWidget(SuffixedMultiWidget):
    """A two-box range widget reading ``<name>_low`` / ``<name>_high``."""

    suffixes = ["low", "high"]

    def __init__(self, attrs: dict[str, object] | None = None) -> None:
        """Two text boxes, one per suffix."""
        super().__init__((forms.TextInput, forms.TextInput), attrs)


class FieldBoxWidgetMixin(django_filters.Filter):
    """A filter mixin whose ``field`` property installs a ``FieldBoxRangeWidget``.

    The widget is set on the form field the filter builds, not passed as the filter's
    ``widget`` argument, so only that built field says which keys it reads.
    """

    @property
    @override
    def field(self) -> forms.Field:
        """The filter's form field, given a ``FieldBoxRangeWidget``."""
        field = super().field
        field.widget = FieldBoxRangeWidget()
        return field


class FieldBoxRangeFilter(FieldBoxWidgetMixin, django_filters.RangeFilter):
    """django-filter's ``RangeFilter`` whose ``field`` property installs its own widget."""


class FieldBoxSpanFilter(RangeFilter, FieldBoxWidgetMixin):
    """The package's ``RangeFilter`` with ``FieldBoxWidgetMixin`` after it in the MRO.

    The mixin's ``field`` sits between the package's ``RangeFilter`` and django-filter's
    ``Filter``, so the field it installs its widget on is the one the package's filter
    builds and hands its column's comparison field.
    """


class ScalarSpecimenTagFilter(FilterSet):
    """Filters scalar specimen tags by id, label and active flag."""

    class Meta:
        model = models.ScalarSpecimenTag
        fields = {"id": "__all__", "label": "__all__", "active": "__all__"}


class ScalarSpecimenFilter(FilterSet):
    """Filters scalar specimens by the listed scalar columns (not ``payload``), the tag and price span."""

    tag = RelatedFilter(ScalarSpecimenTagFilter, field_name="tag")
    price_span = RangeFilter(field_name="price", lookup_expr="range")
    price_among = ListFilter(field_name="price", lookup_expr="in")
    signed_big_span = RangeFilter(field_name="signed_big", lookup_expr="range")
    unsigned_big_span = RangeFilter(field_name="unsigned_big", lookup_expr="range")
    signed_big_among = ListFilter(field_name="signed_big", lookup_expr="in")
    unsigned_big_among = ListFilter(field_name="unsigned_big", lookup_expr="in")
    price_between = django_filters.RangeFilter(field_name="price")
    occurred_between = django_filters.DateFromToRangeFilter(field_name="occurred_on")
    occurred_in_boxes = django_filters.DateFromToRangeFilter(
        field_name="occurred_on",
        widget=forms.MultiWidget(widgets=(forms.TextInput, forms.TextInput)),
    )
    price_in_underscored_boxes = django_filters.RangeFilter(
        field_name="price",
        widget=UnderscoredRangeWidget,
    )
    price_in_field_boxes = FieldBoxRangeFilter(field_name="price")
    price_span_in_field_boxes = FieldBoxSpanFilter(field_name="price", lookup_expr="range")
    occurred_day_of = django_filters.DateTimeFilter(field_name="occurred_at", lookup_expr="date")
    occurred_year_among = ListFilter(field_name="occurred_at__year", lookup_expr="in")
    occurred_year_span = RangeFilter(field_name="occurred_at__year", lookup_expr="range")

    class Meta:
        model = models.ScalarSpecimen
        # Every converted scalar except ``payload`` (JSONField has no
        # django-filter default). Each ``"__all__"`` expands to that field's
        # concrete-lookup set, exercising the lookup-expansion path across
        # bool / float / Decimal / date / datetime / time / UUID / BigInt as
        # well as the integer PK. Only the text column ``label`` gets the
        # text-pattern lookups (``iExact`` / ``contains`` / ``startsWith`` /
        # ``regex`` / ...); every other column keeps its comparisons.
        fields = {
            "id": "__all__",
            "label": "__all__",
            "flag": "__all__",
            "score": "__all__",
            "price": "__all__",
            "occurred_on": "__all__",
            "occurred_at": "__all__",
            "occurred_time": "__all__",
            "external_id": "__all__",
            "signed_big": "__all__",
            "unsigned_big": "__all__",
            "parent": ["exact", "in", "isnull"],
            "children": ["exact"],
        }


class NullableScalarSpecimenFilter(FilterSet):
    """Filters nullable scalar specimens, with the partner relation and price span."""

    partner = RelatedFilter(ScalarSpecimenFilter, field_name="partner")
    price_span = RangeFilter(field_name="price", lookup_expr="range")

    class Meta:
        model = models.NullableScalarSpecimen
        fields = {
            "id": "__all__",
            "label": "__all__",
            "flag": "__all__",
            "score": "__all__",
            "price": "__all__",
            "occurred_on": "__all__",
            "external_id": "__all__",
            "signed_big": "__all__",
            # Explicit text-pattern lookups on a datetime and an integer column:
            # each pattern leaf is a ``String`` matched against the column's text
            # rendering, beside the column-typed ``exact``.
            "occurred_at": [
                "exact",
                "iexact",
                "icontains",
                "startswith",
                "regex",
                "iregex",
            ],
            "unsigned_big": ["exact", "contains"],
        }


class ScalarSpecimenParentStampFilter(FilterSet):
    """Filters scalar specimens by the day their parent occurred, through a ``FilteredRelation``."""

    parent_day_of = django_filters.DateTimeFilter(
        field_name="par__occurred_at",
        lookup_expr="date",
    )

    class Meta:
        model = models.ScalarSpecimen
        fields = {"label": ["exact"]}


__all__ = (
    "FieldBoxRangeFilter",
    "FieldBoxRangeWidget",
    "FieldBoxSpanFilter",
    "FieldBoxWidgetMixin",
    "NullableScalarSpecimenFilter",
    "ScalarSpecimenFilter",
    "ScalarSpecimenParentStampFilter",
    "ScalarSpecimenTagFilter",
    "UnderscoredRangeWidget",
)
