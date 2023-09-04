from django.conf import settings
from django.db import migrations, models

import authentik.stages.authenticator_totp.models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_stages_authenticator_totp", "0007_authenticatortotpstage_friendly_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TOTPDevice",
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
                    "key",
                    models.CharField(
                        default=authentik.stages.authenticator_totp.models.default_key,
                        help_text="A hex-encoded secret key of up to 40 bytes.",
                        max_length=80,
                        validators=[authentik.stages.authenticator_totp.models.key_validator],
                    ),
                ),
                (
                    "step",
                    models.PositiveSmallIntegerField(
                        default=30, help_text="The time step in seconds."
                    ),
                ),
                (
                    "t0",
                    models.BigIntegerField(
                        default=0, help_text="The Unix time at which to begin counting steps."
                    ),
                ),
                (
                    "digits",
                    models.PositiveSmallIntegerField(
                        default=6,
                        help_text="The number of digits to expect in a token.",
                        choices=[(6, 6), (8, 8)],
                    ),
                ),
                (
                    "tolerance",
                    models.PositiveSmallIntegerField(
                        default=1,
                        help_text="The number of time steps in the past or future to allow.",
                    ),
                ),
                (
                    "drift",
                    models.SmallIntegerField(
                        default=0,
                        help_text="The number of time steps the prover is known to deviate from our clock.",
                    ),
                ),
                (
                    "last_t",
                    models.BigIntegerField(
                        default=-1,
                        help_text="The t value of the latest verified token. The next token must be at a higher time step.",
                    ),
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
                "verbose_name": "TOTP device",
            },
            bases=(models.Model,),
        ),
    ]
