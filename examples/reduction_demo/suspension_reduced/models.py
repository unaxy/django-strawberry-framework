"""Snapshot ``suspension_reduced``: both rules at their owners."""

from django.db import models
from suspension_reduced.rules import Public


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
