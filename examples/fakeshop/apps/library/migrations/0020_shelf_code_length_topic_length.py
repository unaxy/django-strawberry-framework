import django.db.models.functions.comparison
import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0019_distributor_display_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="shelf",
            name="code_length",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.functions.text.Length("code"),
                output_field=models.BigIntegerField(),
            ),
        ),
        migrations.AddField(
            model_name="shelf",
            name="topic_length",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.functions.text.Length(
                    django.db.models.functions.comparison.NullIf("topic", models.Value("")),
                ),
                output_field=models.IntegerField(null=True),
            ),
        ),
    ]
