"""Test-local models whose reverse one-to-one spells its query name and accessor apart.

A reverse relation is named twice by Django: ``select_related``, ``only()`` and
filters take its query name (``related_query_name``), while ``prefetch_related``
and the instance attribute take its accessor (``related_name``). Every fakeshop
reverse relation that sets ``related_name`` leaves the two equal, so these
models stand in: ``SpParent.card`` is a reverse one-to-one queried as ``cards``,
with an M2M (``SpCard.genres``) beneath it, and ``SpParent.badge`` is the
control whose two names coincide. ``app_label = "products"`` names an installed
app so Django wires the reverse relations into ``_meta.get_fields()``;
``managed = False`` keeps ``migrate`` from touching their tables, which
``spelling_fixture_tables`` creates, seeds and drops on demand.
"""

from __future__ import annotations

import contextlib
from collections.abc import Generator
from typing import TYPE_CHECKING, TypeAlias

from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

    # Each field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them.
    _Text: TypeAlias = models.TextField[str | Combinable, str]


class SpParent(models.Model):
    """The parent both reverse one-to-ones point at."""

    code: _Text = models.TextField()

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]


class SpGenre(models.Model):
    """The M2M target beneath the split-name one-to-one."""

    name: _Text = models.TextField()

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]


class SpCard(models.Model):
    """A one-to-one child reached as ``parent.card`` and queried as ``cards``."""

    parent: models.OneToOneField[SpParent | Combinable, SpParent] = models.OneToOneField(
        SpParent,
        on_delete=models.CASCADE,
        related_name="card",
        related_query_name="cards",
    )
    name: _Text = models.TextField()
    genres: models.ManyToManyField[SpGenre, models.Model] = models.ManyToManyField(
        SpGenre,
        related_name="cards",
    )

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]


class SpBadge(models.Model):
    """A one-to-one child whose accessor and query name are both ``badge``."""

    parent: models.OneToOneField[SpParent | Combinable, SpParent] = models.OneToOneField(
        SpParent,
        on_delete=models.CASCADE,
        related_name="badge",
    )
    name: _Text = models.TextField()

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]


_MODELS = (
    SpParent,
    SpGenre,
    SpCard,
    SpBadge,
)


@contextlib.contextmanager
def spelling_fixture_tables(connection: BaseDatabaseWrapper) -> Generator[None, None, None]:
    """Create the ``Sp*`` tables and seed three parents; drop the tables on exit.

    Parents ``P-A``, ``P-B`` and ``P-C``: the first two carry a card
    (``CARD-A`` with genres ``g1`` and ``g2``, ``CARD-B`` with ``g1``) and a
    badge (``BADGE-A``, ``BADGE-B``); ``P-C`` carries neither. ``create_model``
    also creates the auto-created ``SpCard.genres`` through table, and
    ``delete_model`` drops it. Callers run under
    ``@pytest.mark.django_db(transaction=True)`` (the SQLite schema editor
    refuses the plain ``django_db`` atomic wrapper).
    """
    created: list[type[models.Model]] = []
    try:
        with connection.schema_editor() as editor:
            for model in _MODELS:
                editor.create_model(model)
                created.append(model)
        genres = {name: SpGenre.objects.create(name=name) for name in ("g1", "g2")}
        for code, genre_names in (("A", ("g1", "g2")), ("B", ("g1",))):
            parent = SpParent.objects.create(code=f"P-{code}")
            card = SpCard.objects.create(parent=parent, name=f"CARD-{code}")
            card.genres.set([genres[name] for name in genre_names])
            _ = SpBadge.objects.create(parent=parent, name=f"BADGE-{code}")
        _ = SpParent.objects.create(code="P-C")
        yield
    finally:
        with connection.schema_editor() as editor:
            for model in reversed(created):
                editor.delete_model(model)
