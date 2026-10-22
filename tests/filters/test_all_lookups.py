"""Per-field ``"__all__"`` lookup expansion against lookups registered from outside the field.

``filters/sets.py::_lookups_for_field`` publishes a field's concrete lookups, minus the
lookups ``django.contrib.postgres`` registers onto a field that is not its own: its range
module registers ``contained_by`` onto the core numeric and temporal fields at import, and
its app config registers ``search`` / ``trigram_*`` onto the core text fields. A
``django.contrib.postgres`` field keeps its whole set, and a consumer-registered lookup is
published like a built-in one. The ``django.contrib.postgres`` rows skip where the module
is unimportable (no PostgreSQL driver installed).
"""

import pytest
from django.db import models
from django.test.utils import register_lookup

from django_strawberry_framework.filters import sets
from django_strawberry_framework.filters.sets import _lookups_for_field
from django_strawberry_framework.utils import truth

_CORE_RANGE_OPERAND_FIELDS: tuple[type[models.Field[object, object]], ...] = (
    models.IntegerField,
    models.BigIntegerField,
    models.BigAutoField,
    models.FloatField,
    models.DecimalField,
    models.DateField,
    models.DateTimeField,
)


@pytest.fixture(autouse=True)
def _fresh_lookup_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give each test an empty class-keyed memo, so a registration it makes is crawled."""
    cache: truth.IdentityMap[type[models.Field[object, object]], list[str]] = truth.IdentityMap()
    monkeypatch.setattr(sets, "_lookups_for_field_class_cache", cache)


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


def test_contrib_postgres_fields_keep_their_own_lookups() -> None:
    """``ArrayField``, ``HStoreField``, a range field and an ``ArrayField`` subclass keep theirs."""
    pytest.importorskip("django.contrib.postgres.fields")
    from django.contrib.postgres.fields import (  # noqa: PLC0415 - after the skip guard
        ArrayField,
        HStoreField,
        IntegerRangeField,
    )

    class ConsumerArrayField(ArrayField[list[int], list[int]]):
        """A consumer subclass, defined outside ``django.contrib.postgres``."""

    array_field: ArrayField[list[int], list[int]] = ArrayField(models.IntegerField())
    for field in (array_field, ConsumerArrayField(models.IntegerField())):
        assert {
            "contained_by",
            "contains",
            "overlap",
            "exact",
        } <= set(_lookups_for_field(field))
    assert {"has_key", "has_keys", "contained_by"} <= set(_lookups_for_field(HStoreField()))
    assert {
        "contained_by",
        "overlap",
        "fully_lt",
        "adjacent_to",
    } <= set(
        _lookups_for_field(IntegerRangeField()),
    )


class _DivisibleBy(models.Lookup[int]):
    """A consumer-registered lookup: ``<column> % <value> = 0``."""

    lookup_name = "divisible_by"


def test_consumer_registered_lookup_is_published() -> None:
    """A lookup the consumer registers on a core field joins its ``"__all__"`` set."""
    with register_lookup(models.IntegerField, _DivisibleBy):
        lookups = _lookups_for_field(models.IntegerField())
    assert "divisible_by" in lookups
    assert "exact" in lookups
