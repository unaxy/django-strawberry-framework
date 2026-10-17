"""WS-1C: replace ``TrackedPath.is_current`` with an explicit ``state`` slug.

``state`` disambiguates the three lifecycle meanings the boolean conflated:
``current`` (exists in the working tree), ``historical`` (linked from a done
card; the file once existed), and ``planned`` (linked from a wip/todo card;
does not exist yet). The backfill maps ``is_current=True`` -> ``current`` and
``is_current=False`` -> ``historical`` when any linked card is done, else
``planned``.
"""

from typing import TYPE_CHECKING

from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import ManyRelatedManager

    class _TrackedPath(models.Model):
        """The historical ``kanban.TrackedPath`` columns this migration reads."""

        pk: int
        is_current: bool
        state: str
        cards: ManyRelatedManager[models.Model]


def _backfill_state(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Derive ``state`` from the old ``is_current`` boolean and card links."""
    TrackedPath: type[_TrackedPath] = apps.get_model("kanban", "TrackedPath")
    manager = TrackedPath.objects.using(schema_editor.connection.alias)
    for row in manager.all():
        if row.is_current:
            state = "current"
        elif row.cards.filter(status__key="done").exists():
            state = "historical"
        else:
            state = "planned"
        _ = manager.filter(pk=row.pk).update(state=state)


def _restore_is_current(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Reverse: ``is_current`` = whether ``state`` is ``current``."""
    TrackedPath: type[_TrackedPath] = apps.get_model("kanban", "TrackedPath")
    manager = TrackedPath.objects.using(schema_editor.connection.alias)
    for row in manager.all():
        _ = manager.filter(pk=row.pk).update(is_current=(row.state == "current"))


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0009_specdoc_path"),
    ]

    operations = [
        migrations.AddField(
            model_name="trackedpath",
            name="state",
            field=models.SlugField(
                choices=[
                    ("current", "Current"),
                    ("historical", "Historical"),
                    ("planned", "Planned"),
                ],
                default="current",
            ),
        ),
        migrations.RunPython(_backfill_state, _restore_is_current),
        migrations.RemoveField(
            model_name="trackedpath",
            name="is_current",
        ),
        migrations.AddConstraint(
            model_name="trackedpath",
            constraint=models.CheckConstraint(
                condition=models.Q(state__in=["current", "historical", "planned"]),
                name="tracked_path_state_valid",
            ),
        ),
    ]
