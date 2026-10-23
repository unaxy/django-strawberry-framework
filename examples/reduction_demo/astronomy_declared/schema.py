"""Snapshot 2 (declared): the same policy, written in the rule fragment, still per type.

Nothing has moved yet. The hooks are gone, so the cascade is now the framework's
default and no longer an invocation each type must remember. But the rule is
still authored twice, and it is still a composite: an actor clause OR a row
clause. Now the framework can see that, and says so in the audit.
"""

import strawberry
from astronomy_declared import models

from django_strawberry_framework import DjangoListField, DjangoType
from django_strawberry_framework.rules import Actor, Field, Rule

visible = Rule("visible", Actor("is_staff").is_true() | Field("is_private").is_false())


class GalaxyNode(DjangoType):
    class Meta:
        model = models.Galaxy
        fields = ("id", "name", "is_private")
        visibility = (visible,)


class CelestialBodyNode(DjangoType):
    class Meta:
        model = models.CelestialBody
        fields = (
            "id",
            "name",
            "is_private",
            "galaxy",
        )
        visibility = (visible,)


@strawberry.type
class Query:
    galaxies: list[GalaxyNode] = DjangoListField(GalaxyNode)
    bodies: list[CelestialBodyNode] = DjangoListField(CelestialBodyNode)
