"""Rung 2, snapshot 2 (reduced): each rule authored once, at L0, the rest derived.

The status membership is authored once, on the field's ``choices``;
``ChoicesConstraint`` derives the ``CHECK`` from it. The price floor and the
date order are authored once as ``CheckConstraint``; Django derives the Python
check (``validate_constraints`` inside ``full_clean``). No validator, no
``clean()``, and the database holds every rule.
"""

from django.db import models

from django_strawberry_framework.rules import ChoicesConstraint


class Status(models.TextChoices):
    DRAFT = "draft", "Draft"
    LIVE = "live", "Live"


class Offer(models.Model):
    sku = models.TextField(unique=True)
    status = models.TextField(choices=Status.choices, default=Status.DRAFT)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    starts = models.DateField()
    ends = models.DateField()

    class Meta:
        constraints = [
            ChoicesConstraint("status", name="reduced_offer_status_valid"),
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="reduced_offer_price_nonneg",
            ),
            models.CheckConstraint(
                condition=models.Q(ends__gt=models.F("starts")),
                name="reduced_offer_ends_after_starts",
            ),
        ]
