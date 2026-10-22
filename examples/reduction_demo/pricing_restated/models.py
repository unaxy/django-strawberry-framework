"""Rung 2, snapshot 1 (restated): every rule written twice, once for the DB and once for Python.

The common Django shape: a ``CheckConstraint`` for the database and a
validator, ``choices`` or ``clean()`` for the form, each pair saying one thing.
``unique=True`` and a ``UniqueConstraint`` on the same column is the same
restatement at one rung. The date-order rule exists only in ``clean()``, so the
database never hears of it.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Status(models.TextChoices):
    DRAFT = "draft", "Draft"
    LIVE = "live", "Live"


class Offer(models.Model):
    sku = models.TextField(unique=True)
    status = models.TextField(choices=Status.choices, default=Status.DRAFT)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    starts = models.DateField()
    ends = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["sku"], name="restated_offer_sku_unique"),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        "draft",
                        "live",
                    ],
                ),
                name="restated_offer_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="restated_offer_price_nonneg",
            ),
        ]

    def clean(self) -> None:
        if self.ends <= self.starts:
            raise ValidationError({"ends": "must be after starts"})
