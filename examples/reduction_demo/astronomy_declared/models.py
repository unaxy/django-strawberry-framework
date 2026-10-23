"""Snapshot 2 (declared): same models as snapshot 1; only the schema changes."""

from django.db import models


class Galaxy(models.Model):
    name = models.CharField(max_length=100)
    is_private = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]


class CelestialBody(models.Model):
    name = models.CharField(max_length=100)
    galaxy = models.ForeignKey(Galaxy, on_delete=models.CASCADE, related_name="bodies")
    is_private = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
