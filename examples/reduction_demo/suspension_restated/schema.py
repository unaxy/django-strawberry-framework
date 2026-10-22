"""Snapshot ``suspension_restated``: "suspended users see nothing", stated once per type.

The inverse of the lead example. ``ActiveOnly`` reads no row field, so no
model owns it, and as a conjunct it cannot be a schema bypass either. Stated
on each type it is authored twice, and it is evaluated after the schema's
bypass, so a suspended staff user still sees everything.
"""

import strawberry
from suspension_restated import models
from suspension_restated.rules import ActiveOnly

from django_strawberry_framework import DjangoListField, DjangoType


class TicketNode(DjangoType):
    class Meta:
        model = models.Ticket
        fields = ("id", "title", "is_private")
        visibility = (ActiveOnly,)


class ReplyNode(DjangoType):
    class Meta:
        model = models.Reply
        fields = (
            "id",
            "body",
            "is_private",
            "ticket",
        )
        visibility = (ActiveOnly,)


@strawberry.type
class Query:
    tickets: list[TicketNode] = DjangoListField(TicketNode)
    replies: list[ReplyNode] = DjangoListField(ReplyNode)
