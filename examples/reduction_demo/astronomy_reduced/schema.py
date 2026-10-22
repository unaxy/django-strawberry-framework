"""Snapshot 3 (reduced): no visibility code on either node.

The staff bypass lives on the schema (``demo.py`` passes
``visibility=[StaffBypass]``), the public rule lives on the mixin that owns the
column, and the cascade is the framework default. Both hook bodies are gone.
"""

import strawberry
from astronomy_reduced import models

from django_strawberry_framework import DjangoListField, DjangoType


class GalaxyNode(DjangoType):
    class Meta:
        model = models.Galaxy
        fields = ("id", "name", "is_private")


class CelestialBodyNode(DjangoType):
    class Meta:
        model = models.CelestialBody
        fields = (
            "id",
            "name",
            "is_private",
            "galaxy",
        )


@strawberry.type
class Query:
    galaxies: list[GalaxyNode] = DjangoListField(GalaxyNode)
    bodies: list[CelestialBodyNode] = DjangoListField(CelestialBodyNode)
