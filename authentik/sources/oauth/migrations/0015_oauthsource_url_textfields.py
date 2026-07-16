# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_sources_oauth", "0014_migrate_azuread_to_entraid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="oauthsource",
            name="request_token_url",
            field=models.TextField(
                help_text="URL used to request the initial token. This URL is only required for OAuth 1.",
                null=True,
                verbose_name="Request Token URL",
            ),
        ),
        migrations.AlterField(
            model_name="oauthsource",
            name="authorization_url",
            field=models.TextField(
                help_text="URL the user is redirect to to conest the flow.",
                null=True,
                verbose_name="Authorization URL",
            ),
        ),
        migrations.AlterField(
            model_name="oauthsource",
            name="access_token_url",
            field=models.TextField(
                help_text="URL used by authentik to retrieve tokens.",
                null=True,
                verbose_name="Access Token URL",
            ),
        ),
        migrations.AlterField(
            model_name="oauthsource",
            name="profile_url",
            field=models.TextField(
                help_text="URL used by authentik to get user information.",
                null=True,
                verbose_name="Profile URL",
            ),
        ),
    ]
