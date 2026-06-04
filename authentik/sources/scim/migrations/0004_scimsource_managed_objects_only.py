from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_sources_scim", "0003_alter_scimsourcegroup_unique_together_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="scimsource",
            name="managed_objects_only",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Only manage users and groups created by this SCIM source. "
                    "Disables tenant-wide correlation, restricts group membership, "
                    "and unlinks objects on DELETE instead of deleting them."
                ),
            ),
        ),
    ]
