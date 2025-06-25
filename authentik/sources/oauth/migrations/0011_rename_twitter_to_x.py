"""Rename Twitter to X"""

from django.db import migrations


class Migration(migrations.Migration):
    """Rename Twitter to X"""

    dependencies = [
        ("authentik_sources_oauth", "0010_oauthsource_authorization_code_auth_method"),
    ]

    operations = [
        migrations.RunSQL(
            "UPDATE authentik_sources_oauth_oauthsource SET provider_type = 'x' WHERE provider_type = 'twitter';"
        ),
    ]
