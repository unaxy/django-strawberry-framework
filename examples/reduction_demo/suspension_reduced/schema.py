"""Snapshot ``suspension_reduced``: no visibility code on either node.

``ActiveOnly`` lives on the schema's restriction scope (``demo.py`` passes
``restrictions=[ActiveOnly]``), where it is authored once, reaches every type,
and is evaluated above the staff bypass, so a suspended staff user sees nothing.
"""

import strawberry
from suspension_reduced import models

from django_strawberry_framework import DjangoListField, DjangoType


class TicketNode(DjangoType):
    class Meta:
        model = models.Ticket
        fields = ("id", "title", "is_private")


class ReplyNode(DjangoType):
    class Meta:
        model = models.Reply
        fields = (
            "id",
            "body",
            "is_private",
            "ticket",
        )


@strawberry.type
class Query:
    tickets: list[TicketNode] = DjangoListField(TicketNode)
    replies: list[ReplyNode] = DjangoListField(ReplyNode)
