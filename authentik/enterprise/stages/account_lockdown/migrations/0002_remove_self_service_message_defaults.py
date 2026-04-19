from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_stages_account_lockdown", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accountlockdownstage",
            name="self_service_message",
            field=models.TextField(
                help_text=(
                    "HTML message shown to users after self-service lockdown. "
                    "Supports HTML formatting."
                ),
            ),
        ),
        migrations.AlterField(
            model_name="accountlockdownstage",
            name="self_service_message_title",
            field=models.TextField(
                help_text="Title shown to users after self-service lockdown",
            ),
        ),
    ]
