"""Per-field ``"__all__"`` lookup expansion: foreign registrations and text-pattern lookups.

``filters/sets.py::_lookups_for_field`` publishes a field's concrete lookups, minus the
lookups ``django.contrib.postgres`` registers onto a field that is not its own: its range
module registers ``contained_by`` onto the core numeric and temporal fields at import, and
its app config registers ``search`` / ``trigram_*`` onto the core text fields. A
``django.contrib.postgres`` field keeps its whole set, and a consumer-registered lookup is
published like a built-in one: a class registration on every field of the class, whenever
it is made, and an instance registration on that field alone. The
``django.contrib.postgres`` rows skip where the module is unimportable (no PostgreSQL
driver installed).

Django's text-pattern lookups (``iexact``, the ``contains`` / ``startswith`` / ``endswith``
families, ``regex`` / ``iregex``) join the set only on a text column, one whose default
filter is ``CharFilter``, when the column's filter is the package's own default; a column
whose filter ``Meta.filter_overrides`` supplies keeps the whole set. Listed explicitly on
a non-text column, the framework's leaf is a ``TextPatternFilter`` typed ``str``; a
``Meta.filter_overrides`` selection or a declared filter keeps its own class and the
column's type.
"""

from typing import TYPE_CHECKING

import django_filters
import pytest
from apps.library import models as library_models
from apps.products.models import Item
from apps.scalars import models as scalar_models
from django.db import models
from django.db.models import lookups as model_lookups
from django.test.utils import register_lookup
from django_filters import CharFilter
from django_filters.filterset import UnknownFieldBehavior

from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.filters.base import EnumChoiceFilter, TextPatternFilter
from django_strawberry_framework.filters.inputs import convert_filter_to_input_annotation
from django_strawberry_framework.filters.sets import (
    _lookups_for_field,
    _non_transform_lookups,
    _without_foreign_postgres_lookups,
    filter_generation_provenance,
)
from django_strawberry_framework.utils import truth

if TYPE_CHECKING:
    from django_strawberry_framework.utils.typing import ModelField

_TEXT_PATTERN_LOOKUPS = frozenset(
    {
        "iexact",
        "contains",
        "icontains",
        "startswith",
        "istartswith",
        "endswith",
        "iendswith",
        "regex",
        "iregex",
    },
)

_CORE_RANGE_OPERAND_FIELDS: tuple[type[models.Field[object, object]], ...] = (
    models.IntegerField,
    models.BigIntegerField,
    models.BigAutoField,
    models.FloatField,
    models.DecimalField,
    models.DateField,
    models.DateTimeField,
)


@pytest.mark.parametrize("field_class", _CORE_RANGE_OPERAND_FIELDS)
def test_core_field_omits_registered_range_contained_by(
    field_class: type[models.Field[object, object]],
) -> None:
    """``contained_by`` is registered on the core field yet absent from its ``"__all__"`` set."""
    pytest.importorskip("django.contrib.postgres.fields")

    field = field_class()
    assert "contained_by" in field.get_lookups()
    lookups = _lookups_for_field(field)
    assert "contained_by" not in lookups
    assert {
        "exact",
        "gt",
        "in",
        "range",
        "isnull",
    } <= set(lookups)


@pytest.mark.parametrize("lookup_name", ["search", "trigram_similar", "trigram_word_similar"])
def test_core_text_field_omits_contrib_postgres_text_lookups(lookup_name: str) -> None:
    """The text lookups ``django.contrib.postgres``'s app config registers stay unpublished."""
    pytest.importorskip("django.contrib.postgres.fields")
    from django.contrib.postgres.lookups import (  # noqa: PLC0415 - after the skip guard
        SearchLookup,
        TrigramSimilar,
        TrigramWordSimilar,
    )

    lookup_class = {
        "search": SearchLookup,
        "trigram_similar": TrigramSimilar,
        "trigram_word_similar": TrigramWordSimilar,
    }[lookup_name]
    field: models.TextField[str, str] = models.TextField()
    with register_lookup(models.TextField, lookup_class):
        assert lookup_name in field.get_lookups()
        lookups = _lookups_for_field(field)
    assert lookup_name not in lookups
    assert {
        "exact",
        "icontains",
        "in",
        "isnull",
    } <= set(lookups)


@pytest.mark.parametrize(
    ("field_kind", "expected"),
    [
        pytest.param(
            "array",
            {
                "contained_by",
                "contains",
                "overlap",
                "exact",
            },
            id="array",
        ),
        pytest.param(
            "subclass",
            {
                "contained_by",
                "contains",
                "overlap",
                "exact",
            },
            id="subclass",
        ),
        pytest.param("hstore", {"has_key", "has_keys", "contained_by"}, id="hstore"),
        pytest.param(
            "range",
            {
                "contained_by",
                "overlap",
                "fully_lt",
                "adjacent_to",
            },
            id="range",
        ),
    ],
)
def test_contrib_postgres_fields_keep_their_own_lookups(
    field_kind: str,
    expected: set[str],
) -> None:
    """Each PostgreSQL container field keeps its native lookup names."""
    pytest.importorskip("django.contrib.postgres.fields")
    from django.contrib.postgres.fields import (  # noqa: PLC0415 - after the skip guard
        ArrayField,
        HStoreField,
        IntegerRangeField,
    )

    class ConsumerArrayField(ArrayField[list[int], list[int]]):
        """A consumer subclass, defined outside ``django.contrib.postgres``."""

    if field_kind == "array":
        array_field: ArrayField[list[int], list[int]] = ArrayField(models.IntegerField())
        field = array_field
    elif field_kind == "subclass":
        field = ConsumerArrayField(models.IntegerField())
    elif field_kind == "hstore":
        field = HStoreField()
    else:
        field = IntegerRangeField()
    assert expected <= set(_lookups_for_field(field))


class _DivisibleBy(models.Lookup[int]):
    """A consumer-registered lookup: ``<column> % <value> = 0``."""

    lookup_name = "divisible_by"


def test_consumer_registered_lookup_is_published() -> None:
    """A lookup the consumer registers on a core field joins its ``"__all__"`` set."""
    with register_lookup(models.IntegerField, _DivisibleBy):
        lookups = _lookups_for_field(models.IntegerField())
    assert "divisible_by" in lookups
    assert "exact" in lookups


def test_class_registration_after_a_first_read_is_published() -> None:
    """A class registration made after the field's set was first read joins the next read."""
    field: models.IntegerField[int, int] = models.IntegerField()
    assert "divisible_by" not in _lookups_for_field(field)
    with register_lookup(models.IntegerField, _DivisibleBy):
        assert "divisible_by" in _lookups_for_field(field)
    assert "divisible_by" not in _lookups_for_field(field)


@pytest.mark.parametrize(
    "read_first",
    ["registered", "other"],
)
def test_instance_registered_lookup_publishes_on_that_field_only(read_first: str) -> None:
    """A lookup registered on one field instance joins that field's set and no sibling's.

    Two fields of one class read their own registries, whichever is read first.
    """
    registered: models.TextField[str, str] = models.TextField()
    other: models.TextField[str, str] = models.TextField()
    _ = registered.register_instance_lookup(model_lookups.IStartsWith, lookup_name="prefix")
    try:
        if read_first == "registered":
            registered_lookups = _lookups_for_field(registered)
            other_lookups = _lookups_for_field(other)
        else:
            other_lookups = _lookups_for_field(other)
            registered_lookups = _lookups_for_field(registered)
    finally:
        registered._unregister_instance_lookup(model_lookups.IStartsWith, lookup_name="prefix")
    assert "prefix" in registered_lookups
    assert "prefix" not in other_lookups


class _ConsumerCharField(models.CharField[str, str]):
    """A consumer subclass of a text column: still text by its MRO."""


_NON_TEXT_FIELDS: tuple[type[models.Field[object, object]], ...] = (
    models.DateField,
    models.DateTimeField,
    models.TimeField,
    models.DurationField,
    models.IntegerField,
    models.BigIntegerField,
    models.PositiveSmallIntegerField,
    models.AutoField,
    models.DecimalField,
    models.FloatField,
    models.BooleanField,
    models.UUIDField,
)

_TEXT_FIELDS: tuple[type[models.Field[object, object]], ...] = (
    models.CharField,
    models.TextField,
    models.SlugField,
    models.EmailField,
    models.URLField,
    models.GenericIPAddressField,
    _ConsumerCharField,
)


@pytest.mark.parametrize(
    "field_class",
    _NON_TEXT_FIELDS,
    ids=[truth.name(field_class) for field_class in _NON_TEXT_FIELDS],
)
def test_non_text_column_withholds_every_text_pattern_lookup(
    field_class: type[models.Field[object, object]],
) -> None:
    """Registered on the column, the nine text-pattern lookups stay out of its ``"__all__"`` set."""
    field = field_class()
    assert set(field.get_lookups()) >= _TEXT_PATTERN_LOOKUPS
    lookups = set(_lookups_for_field(field))
    assert lookups.isdisjoint(_TEXT_PATTERN_LOOKUPS)
    assert {
        "exact",
        "in",
        "isnull",
        "gt",
        "gte",
        "lt",
        "lte",
        "range",
    } <= lookups


@pytest.mark.parametrize(
    "field_class",
    _TEXT_FIELDS,
    ids=[truth.name(field_class) for field_class in _TEXT_FIELDS],
)
def test_text_column_keeps_every_text_pattern_lookup(
    field_class: type[models.Field[object, object]],
) -> None:
    """A column whose default filter is ``CharFilter`` publishes all nine text-pattern lookups."""
    assert set(_lookups_for_field(field_class())) >= _TEXT_PATTERN_LOOKUPS


def test_contrib_postgres_field_keeps_its_own_contains_and_drops_text_patterns() -> None:
    """``ArrayField``'s ``contains`` is array containment, kept; its text patterns are withheld."""
    pytest.importorskip("django.contrib.postgres.fields")
    from django.contrib.postgres.fields import ArrayField  # noqa: PLC0415 - after the skip guard

    array_field: ArrayField[list[int], list[int]] = ArrayField(models.IntegerField())
    lookups = set(_lookups_for_field(array_field))
    assert "contains" in lookups
    assert lookups.isdisjoint(_TEXT_PATTERN_LOOKUPS - {"contains"})


def _leaf(
    filterset: type[FilterSet],
    name: str,
) -> tuple[django_filters.Filter, tuple[str, object]]:
    """The generated leaf ``name`` of ``filterset``, its provenance origin and input annotation."""
    leaf = filterset.get_filters()[name]
    model = filterset._meta.model
    assert model is not None
    assert leaf.field_name is not None
    column = model._meta.get_field(leaf.field_name.split("__")[0])
    record = filter_generation_provenance(leaf)
    assert record is not None
    return leaf, (record.origin, convert_filter_to_input_annotation(leaf, column, None, filterset))


@pytest.mark.parametrize(
    "name",
    [
        "occurred_at__iexact",
        "occurred_at__regex",
        "occurred_at__date__icontains",
        "price__contains",
        "flag__istartswith",
        "external_id__iendswith",
    ],
)
def test_explicit_text_pattern_on_non_text_columns_is_a_string_text_pattern_filter(
    name: str,
) -> None:
    """Listed explicitly, a text-pattern lookup on a non-text column is a ``TextPatternFilter`` of ``str``.

    The column's other lookups keep their column-typed filters, a text column's pattern
    is unchanged, and a pattern after a transform resolves on the transform's output.
    """

    class SpecimenPatternFilter(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {
                "occurred_at": [
                    "exact",
                    "iexact",
                    "regex",
                    "date__icontains",
                ],
                "price": ["gt", "contains"],
                "flag": ["istartswith"],
                "external_id": ["iendswith"],
                "label": ["icontains"],
            }

    leaf, typed = _leaf(SpecimenPatternFilter, name)
    assert type(leaf) is TextPatternFilter
    assert typed == ("framework_default", str | None)
    label, typed = _leaf(SpecimenPatternFilter, "label__icontains")
    assert type(label) is CharFilter
    assert typed == ("framework_default", str | None)
    occurred_at, typed = _leaf(SpecimenPatternFilter, "occurred_at")
    assert type(occurred_at) is django_filters.DateTimeFilter
    assert typed[1] != (str | None)
    price_gt, _ = _leaf(SpecimenPatternFilter, "price__gt")
    assert type(price_gt) is django_filters.NumberFilter


def test_explicit_text_pattern_on_an_integer_choice_column_is_a_string_not_the_enum() -> None:
    """An integer choice column's ``exact`` is its enum; its explicit ``icontains`` is ``str``."""

    class ShelfTierFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"tier": ["exact", "icontains"]}

    exact, _ = _leaf(ShelfTierFilter, "tier")
    pattern, typed = _leaf(ShelfTierFilter, "tier__icontains")
    assert type(exact) is EnumChoiceFilter
    assert type(pattern) is TextPatternFilter
    assert typed == ("framework_default", str | None)


def test_consumer_selected_pattern_filters_keep_their_class_and_column_type() -> None:
    """A ``Meta.filter_overrides`` selection and a declared filter are never rerouted or retyped.

    The override maps ``DateTimeField`` to the consumer's ``DateTimeFilter`` subclass, and the
    declared ``CharFilter`` names the datetime column: both keep their own class, and their
    input keeps the column's ``DateTime`` type.
    """

    class ConsumerDateTimeFilter(django_filters.DateTimeFilter):
        """The consumer's own datetime filter."""

    class OverrideFilter(FilterSet):
        occurred_like = CharFilter(field_name="occurred_at", lookup_expr="icontains")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"occurred_at": ["icontains"]}
            filter_overrides = {
                models.DateTimeField: {"filter_class": ConsumerDateTimeFilter},
            }

    overridden, overridden_typed = _leaf(OverrideFilter, "occurred_at__icontains")
    declared, declared_typed = _leaf(OverrideFilter, "occurred_like")
    plain = convert_filter_to_input_annotation(
        django_filters.DateTimeFilter(field_name="occurred_at"),
        scalar_models.ScalarSpecimen._meta.get_field("occurred_at"),
        None,
        FilterSet,
    )
    assert type(overridden) is ConsumerDateTimeFilter
    assert overridden_typed == ("override_generated", plain)
    assert type(declared) is CharFilter
    assert declared_typed == ("declared", plain)
    assert plain != (str | None)


def test_explicit_text_pattern_on_a_column_with_no_default_filter_stays_unrecognized() -> None:
    """A pattern lookup on a column with no default filter keeps django-filter's contract.

    ``Item.attachment`` (a ``FileField``) and ``ScalarSpecimen.payload`` (a ``JSONField``)
    have no ``FILTER_DEFAULTS`` entry: under ``IGNORE`` their pattern leaves are skipped,
    never generated as a ``TextPatternFilter``.
    """

    class AttachmentPatternProbe(FilterSet):
        class Meta:
            model = Item
            fields = {"name": ["icontains"], "attachment": ["icontains"]}
            unknown_field_behavior = UnknownFieldBehavior.IGNORE

    class PayloadPatternProbe(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"label": ["exact"], "payload": ["icontains"]}
            unknown_field_behavior = UnknownFieldBehavior.IGNORE

    assert set(AttachmentPatternProbe.get_filters()) == {"name__icontains"}
    assert set(PayloadPatternProbe.get_filters()) == {"label"}


def _parent_bag(field: "ModelField") -> set[str]:
    """Every non-transform lookup the field registers, minus foreign ``contrib.postgres`` ones."""
    lookups = _without_foreign_postgres_lookups(type(field), field.get_lookups())
    return set(_non_transform_lookups(lookups))


def _all_bag(filterset: type[FilterSet], name: str) -> set[str]:
    """The lookups ``filterset.get_fields()`` expands ``name``'s ``"__all__"`` to."""
    value = filterset.get_fields()[name]
    assert truth.is_instance(value, list)
    return {str(lookup) for lookup in value}


@pytest.mark.parametrize("name", ["payload", "occurred_at"])
def test_override_selected_columns_keep_the_whole_lookup_catalog(name: str) -> None:
    """Consumer overrides preserve the exact lookup catalog and generated leaf classes."""

    class OverriddenSpecimenFilter(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"payload": "__all__", "occurred_at": "__all__"}
            filter_overrides = {
                models.JSONField: {"filter_class": CharFilter},
                models.DateTimeField: {"filter_class": CharFilter},
            }

    meta = scalar_models.ScalarSpecimen._meta
    bag = _all_bag(OverriddenSpecimenFilter, name)
    assert bag == _parent_bag(meta.get_field(name))
    assert {"iexact", "icontains", "regex"} <= bag
    filters = OverriddenSpecimenFilter.get_filters()
    assert type(filters["occurred_at__icontains"]) is CharFilter
    assert type(filters["payload__icontains"]) is CharFilter


def test_override_selected_file_column_keeps_the_whole_lookup_catalog() -> None:
    """A FileField override preserves the exact lookup catalog and generated leaf class."""

    class MediaFilter(FilterSet):
        class Meta:
            model = scalar_models.MediaSpecimen
            fields = {"attachment": "__all__"}
            filter_overrides = {models.FileField: {"filter_class": CharFilter}}

    bag = _all_bag(MediaFilter, "attachment")
    assert bag == _parent_bag(scalar_models.MediaSpecimen._meta.get_field("attachment"))
    assert {
        "iexact",
        "icontains",
        "startswith",
        "regex",
    } <= bag
    assert type(MediaFilter.get_filters()["attachment__icontains"]) is CharFilter
