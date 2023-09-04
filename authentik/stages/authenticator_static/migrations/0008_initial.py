from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "authentik_stages_authenticator_static",
            "0007_authenticatorstaticstage_token_length_and_more",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="StaticDevice",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID", serialize=False, auto_created=True, primary_key=True
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="The human-readable name of this device.", max_length=64
                    ),
                ),
                (
                    "confirmed",
                    models.BooleanField(default=True, help_text="Is this device ready for use?"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="The user that this device belongs to.",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="StaticToken",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID", serialize=False, auto_created=True, primary_key=True
                    ),
                ),
                ("token", models.CharField(max_length=16, db_index=True)),
                (
                    "device",
                    models.ForeignKey(
                        related_name="token_set",
                        to="authentik_stages_authenticator_static.staticdevice",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
