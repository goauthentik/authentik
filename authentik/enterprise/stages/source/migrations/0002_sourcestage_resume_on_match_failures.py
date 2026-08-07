from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_stages_source", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sourcestage",
            name="resume_on_match_failures",
            field=ArrayField(
                base_field=models.TextField(choices=[("missing_property", "Missing property")]),
                blank=True,
                default=list,
                help_text="Source matching failure reasons for which the flow should resume.",
                size=None,
            ),
        ),
    ]
