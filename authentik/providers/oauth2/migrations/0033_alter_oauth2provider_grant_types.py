import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_providers_oauth2", "0032_oauth2provider_grant_types"),
    ]

    operations = [
        migrations.AlterField(
            model_name="oauth2provider",
            name="grant_types",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.TextField(
                    choices=[
                        ("authorization_code", "Authorization Code"),
                        ("implicit", "Implicit"),
                        ("hybrid", "Hybrid"),
                        ("refresh_token", "Refresh Token"),
                        ("client_credentials", "Client Credentials"),
                        ("password", "Password"),
                        ("urn:ietf:params:oauth:grant-type:device_code", "Device Code"),
                        ("urn:ietf:params:oauth:grant-type:token-exchange", "Token Exchange"),
                    ]
                ),
                default=list,
                size=None,
            ),
        ),
    ]
