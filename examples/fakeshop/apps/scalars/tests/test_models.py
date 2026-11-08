"""Scalars model tests for string rendering, relation traversal, and uniqueness rules.

Mirrors the other apps' model tests: __str__ rendering (including the nullable
fallback), self-referential + FK relation traversal, and a uniqueness rule. The
``UniqueScalarSpecimen`` rows pin its conditional ``UniqueConstraint``: a duplicate
``amount`` is refused among active rows and stored beside an inactive one.
"""

import datetime
import uuid
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.scalars.models import (
    NullableScalarSpecimen,
    ScalarSpecimen,
    ScalarSpecimenTag,
    UniqueScalarSpecimen,
)


@pytest.mark.django_db
def test_str_representations_and_relations() -> None:
    tag = ScalarSpecimenTag.objects.create(label="alpha")
    parent = ScalarSpecimen.objects.create(
        label="root",
        occurred_on=datetime.date(2024, 1, 1),
        occurred_at=timezone.now(),
        occurred_time=datetime.time(12, 0),
        external_id=uuid.uuid4(),
        tag=tag,
    )
    child = ScalarSpecimen.objects.create(
        label="leaf",
        occurred_on=datetime.date(2024, 1, 2),
        occurred_at=timezone.now(),
        occurred_time=datetime.time(13, 0),
        external_id=uuid.uuid4(),
        parent=parent,
    )
    labelled = NullableScalarSpecimen.objects.create(label="n1", partner=parent)
    blank = NullableScalarSpecimen.objects.create()

    assert str(tag) == "alpha"
    assert str(parent) == "root"
    assert str(labelled) == "n1"
    assert str(blank) == f"NullableScalarSpecimen#{blank.pk}"

    # Self-referential FK, lookup FK, and the nullable cross-FK all traverse.
    assert list(parent.children.all()) == [child]
    assert list(tag.tagged_specimens.all()) == [parent]
    assert list(parent.nullable_partners.all()) == [labelled]


@pytest.mark.django_db
def test_tag_label_unique() -> None:
    ScalarSpecimenTag.objects.create(label="dup")
    with pytest.raises(IntegrityError), transaction.atomic():
        ScalarSpecimenTag.objects.create(label="dup")


def _unique_specimen(label: str, hour: int, *, active: bool) -> UniqueScalarSpecimen:
    return UniqueScalarSpecimen.objects.create(
        label=label,
        opened_time=datetime.time(hour),
        opened_at=timezone.now(),
        amount=Decimal("12.5"),
        active=active,
    )


@pytest.mark.django_db
def test_unique_specimen_amount_is_unique_among_active_rows() -> None:
    inactive = _unique_specimen("inactive", 1, active=False)
    active = _unique_specimen("active", 2, active=True)

    assert str(inactive) == "inactive"
    assert str(active) == "active"
    with pytest.raises(IntegrityError), transaction.atomic():
        _ = _unique_specimen("duplicate", 3, active=True)
    assert list(
        UniqueScalarSpecimen.objects.order_by("label").values_list("label", flat=True),
    ) == ["active", "inactive"]
