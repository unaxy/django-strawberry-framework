"""Snapshot 1 (opaque): the GOAL.md models verbatim, trimmed to the visibility story."""

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
