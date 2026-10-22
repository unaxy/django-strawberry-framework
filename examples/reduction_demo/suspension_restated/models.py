"""Snapshot ``suspension_restated``: the row rule already has its owner; the actor rule does not."""

from django.db import models
from suspension_restated.rules import Public


class Privatable(models.Model):
    """Owns the ``is_private`` column and the one rule that reads it."""

    is_private = models.BooleanField(default=False)
    visibility = (Public,)

    class Meta:
        abstract = True


class Ticket(Privatable):
    title = models.CharField(max_length=100)

    class Meta:
        ordering = ["title"]


class Reply(Privatable):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="replies")
    body = models.CharField(max_length=100)

    class Meta:
        ordering = ["body"]
