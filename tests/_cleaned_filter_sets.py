"""Shared consumer filter declarations and rows for scalar range and list form contracts."""

import datetime
import uuid
from decimal import Decimal

import django_filters
from apps.scalars import models as scalar_models

from django_strawberry_framework.filters import FilterSet, ListFilter, RangeFilter


class PackageCleanedScalarSet(FilterSet):
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


class PlainCleanedScalarSet(django_filters.FilterSet):
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


KEPT_EXTERNAL_ID = uuid.UUID("6f1c2a3e-0b4d-4e5f-8a9b-1c2d3e4f5a6b")


def cleaned_specimen(label: str, *, kept: bool) -> scalar_models.ScalarSpecimen:
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
        external_id=KEPT_EXTERNAL_ID if kept else uuid.uuid4(),
        signed_big=7 if kept else 900,
    )
