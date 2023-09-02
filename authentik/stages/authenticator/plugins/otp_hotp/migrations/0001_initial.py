import django_otp.plugins.otp_hotp.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="HOTPDevice",
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
                        default=django_otp.plugins.otp_hotp.models.default_key,
                        help_text="A hex-encoded secret key of up to 40 bytes.",
                        max_length=80,
                        validators=[django_otp.plugins.otp_hotp.models.key_validator],
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
                        default=5, help_text="The number of missed tokens to tolerate."
                    ),
                ),
                (
                    "counter",
                    models.BigIntegerField(
                        default=0, help_text="The next counter value to expect."
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
                "verbose_name": "HOTP device",
            },
            bases=(models.Model,),
        ),
    ]
