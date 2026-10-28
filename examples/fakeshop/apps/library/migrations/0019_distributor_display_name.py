from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0018_alter_publisher_house_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="distributor",
            name="display_name",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
    ]
