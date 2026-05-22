from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_providers_oauth2", "0032_oauth2provider_grant_types"),
    ]

    operations = [
        migrations.AddField(
            model_name="authorizationcode",
            name="dpop_jkt",
            field=models.CharField(
                default=None,
                max_length=255,
                null=True,
                verbose_name="DPoP JWK Thumbprint",
            ),
        ),
        migrations.AddField(
            model_name="devicetoken",
            name="dpop_jkt",
            field=models.CharField(
                default=None,
                max_length=255,
                null=True,
                verbose_name="DPoP JWK Thumbprint",
            ),
        ),
        migrations.AddField(
            model_name="refreshtoken",
            name="dpop_jkt",
            field=models.CharField(
                default=None,
                max_length=255,
                null=True,
                verbose_name="DPoP JWK Thumbprint",
            ),
        ),
    ]
