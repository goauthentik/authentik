"""Add refresh token families to access tokens.

This is separate from 0039 so the access token table is only locked for this migration, not for
the refresh token backfill in 0039. Access tokens are short-lived, existing ones are not
backfilled and expire without a family.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_providers_oauth2", "0039_refresh_token_hash_family"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesstoken",
            name="family",
            field=models.UUIDField(default=None, null=True),
        ),
        migrations.AddIndex(
            model_name="accesstoken",
            index=models.Index(
                condition=models.Q(("family__isnull", False)),
                fields=["family"],
                name="authentik_p_at_family_idx",
            ),
        ),
    ]
