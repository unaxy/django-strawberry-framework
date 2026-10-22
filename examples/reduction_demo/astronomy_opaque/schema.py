"""Snapshot 1 (opaque): GOAL.md's two ``get_queryset`` hooks, verbatim.

The visibility policy is correct. It is also stated twice, in Python, where the
framework can neither compare the two copies nor say where each clause belongs.
"""

import strawberry
from astronomy_opaque import models

from django_strawberry_framework import DjangoListField, DjangoType, apply_cascade_permissions


class GalaxyNode(DjangoType):
    class Meta:
        model = models.Galaxy
        fields = ("id", "name", "is_private")

    @classmethod
    def get_queryset(cls, queryset, info):
        user = getattr(getattr(info.context, "request", None), "user", None)
        if user and user.is_staff:
            return queryset
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


class CelestialBodyNode(DjangoType):
    class Meta:
        model = models.CelestialBody
        fields = (
            "id",
            "name",
            "is_private",
            "galaxy",
        )

    @classmethod
    def get_queryset(cls, queryset, info):
        user = getattr(getattr(info.context, "request", None), "user", None)
        if user and user.is_staff:
            return queryset
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)


@strawberry.type
class Query:
    galaxies: list[GalaxyNode] = DjangoListField(GalaxyNode)
    bodies: list[CelestialBodyNode] = DjangoListField(CelestialBodyNode)
