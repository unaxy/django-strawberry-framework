"""OrderSet declarations for the glossary data app.

One ``OrderSet`` per glossary type that publishes an ``orderBy`` argument.
Each uses the ``Meta.fields = "__all__"``
shorthand -- every column-backed field (the orderable scalars plus forward
FK columns such as ``status`` / ``term`` / ``category`` -> ``<field>_id``)
plus any forward ``ForeignObject``, ordered by its carrier columns; reverse
relations, M2M managers and generic relations are excluded. ``GlossaryDocumentOrder``
orders the shared ``kanban.BoardDoc`` model (the glossary namespace's view
of board docs), mirroring ``GlossaryDocumentType``. No per-field permission
gates -- ordering is a straight wiring of the ``Ordering`` surface.
"""

from __future__ import annotations

from apps.kanban import models as kanban_models
from django_strawberry_framework.orders import OrderSet

from . import models


class GlossaryTermOrder(OrderSet):
    """Orders ``GlossaryTerm`` rows by every column-backed field."""

    class Meta:
        model = models.GlossaryTerm
        fields = "__all__"


class GlossaryCategoryMembershipOrder(OrderSet):
    """Orders ``GlossaryCategoryMembership`` rows by every column-backed field."""

    class Meta:
        model = models.GlossaryCategoryMembership
        fields = "__all__"


class GlossarySpecMentionOrder(OrderSet):
    """Orders ``GlossarySpecMention`` rows by every column-backed field."""

    class Meta:
        model = models.GlossarySpecMention
        fields = "__all__"


class GlossaryDocumentOrder(OrderSet):
    """Orders shared ``BoardDoc`` rows by every column-backed field."""

    class Meta:
        model = kanban_models.BoardDoc
        fields = "__all__"


__all__ = (
    "GlossaryCategoryMembershipOrder",
    "GlossaryDocumentOrder",
    "GlossarySpecMentionOrder",
    "GlossaryTermOrder",
)
