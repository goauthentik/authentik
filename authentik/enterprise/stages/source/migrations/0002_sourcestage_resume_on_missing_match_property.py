from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_stages_source", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sourcestage",
            name="resume_on_missing_match_property",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Resume the flow when source matching fails because a required property "
                    "is missing."
                ),
            ),
        ),
    ]
