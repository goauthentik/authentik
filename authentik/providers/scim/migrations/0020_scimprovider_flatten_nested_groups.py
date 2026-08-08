from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_providers_scim", "0019_scimprovider_group_filters_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="scimprovider",
            name="flatten_nested_groups",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "When enabled, members of nested child groups are included as direct "
                    "members of the parent group in the SCIM payload. Useful for SCIM "
                    "endpoints that do not support nested groups (AWS IAM Identity Center, "
                    "Slack, etc.)."
                ),
            ),
        ),
    ]
