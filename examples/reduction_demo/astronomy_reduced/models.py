"""Snapshot 3 (reduced): the ``is_private`` column and its rule have one owner."""

from astronomy_reduced.rules import Public
from django.db import models


class Privatable(models.Model):
    """Owns the ``is_private`` column and the one rule that reads it."""

    is_private = models.BooleanField(default=False)
    visibility = (Public,)

    class Meta:
        abstract = True


class Galaxy(Privatable):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]


class CelestialBody(Privatable):
    name = models.CharField(max_length=100)
    galaxy = models.ForeignKey(Galaxy, on_delete=models.CASCADE, related_name="bodies")

    class Meta:
        ordering = ["name"]
