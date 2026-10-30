"""Seed the four net-new ``Section`` rows for the ``other`` reclassification.

This data-only migration seeds the four target sections the reclassification
of ``other`` card items needs, at orders 9-12, the slots after ``other``
(order 8, removed by 0016). The item-to-section assignments live in the kanban tables of
``examples/fakeshop/db.sqlite3``.

* ``test_plan`` -> "Test plan" / 9
* ``decision`` -> "Decision" / 10
* ``open_question`` -> "Open question" / 11
* ``note`` -> "Note" / 12

Data migrations run against historical models, so the ``post_save``
``create_uuid_row`` signal does not fire -- the ``UUIDModel`` side-rows are
created explicitly here (mirroring migration 0014's ``_seed``).

The reclassification and subsequent removal of ``other`` are intentionally
irreversible: these section rows now own card items and cannot be deleted under
the ``PROTECT`` foreign key. The migration therefore declares a no-op reverse
instead of exposing a reverse function that can only fail.
"""

from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

NEW_SECTIONS = (
    ("test_plan", "Test plan", 9),
    ("decision", "Decision", 10),
    ("open_question", "Open question", 11),
    ("note", "Note", 12),
)


def _seed(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    alias = schema_editor.connection.alias
    Section: type[models.Model] = apps.get_model("kanban", "Section")
    UUIDModel: type[models.Model] = apps.get_model("kanban", "UUIDModel")

    for key, label, order in NEW_SECTIONS:
        row, created = Section.objects.using(alias).get_or_create(
            key=key,
            defaults={"label": label, "order": order},
        )
        if created:
            _ = UUIDModel.objects.using(alias).create(section=row)


class Migration(migrations.Migration):
    dependencies = [
        ("kanban", "0014_seed_worklog_lookups"),
    ]

    operations = [
        migrations.RunPython(_seed, migrations.RunPython.noop),
    ]
